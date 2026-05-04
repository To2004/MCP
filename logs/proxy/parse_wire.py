"""
Reconstruct calls.csv (and tool catalog + session metadata) from a wire.log alone.

Reads one mcp-proxy wire.log, pairs JSON-RPC requests/responses by id (per session),
emits three CSVs into <wire-log-dir>/parsed/.

Usage:
    uv run python logs/proxy/parse_wire.py logs/proxy/wire.log
    uv run python logs/proxy/parse_wire.py logs/proxy/sessions/calendar/wire.log
"""

from __future__ import annotations

import ast
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ── line patterns ────────────────────────────────────────────────────────────
TS_RE = re.compile(r"^\[[DI] (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})")
RECV_RE = re.compile(r"Received JSON: (b'.*'|b\".*\")\s*$")
CHUNK_RE = re.compile(r"chunk: (b'event: message.*'|b\"event: message.*\")\s*$")
NEW_SESSION_RE = re.compile(r"Created new session with ID: ([0-9a-f-]+)")
DISCONNECT_RE = re.compile(r"Client session disconnected ([0-9a-f-]+)")
HTTP_DISCONNECT_RE = re.compile(r"Got event: http\.disconnect")
PREVIEW_LEN = 300

# Two identical (tool, args) calls within this gap are flagged as a probable retry.
RETRY_WINDOW_S = 30.0
# Latency above this is flagged as suspiciously slow.
SLOW_CALL_S = 10.0


def parse_ts(line: str) -> datetime | None:
    m = TS_RE.match(line)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f")


def bytes_literal_to_str(s: str) -> str:
    """Turn a Python bytes-literal repr like b'{"a":1}' into the inner string."""
    return ast.literal_eval(s).decode("utf-8", errors="replace")


def extract_data_payload(chunk_str: str) -> str | None:
    """Pull the JSON body out of an SSE chunk: 'event: message\\r\\ndata: {...}\\r\\n\\r\\n'."""
    marker = "data: "
    idx = chunk_str.find(marker)
    if idx == -1:
        return None
    body = chunk_str[idx + len(marker):]
    return body.rstrip("\r\n")


def args_keys(args: Any) -> list[str]:
    if isinstance(args, dict):
        return list(args.keys())
    return []


def categorize(method: str, is_error: bool, error_msg: str, response_text: str) -> str:
    """Heuristic mapping back to runner labels VALID / BAD_TOOL / BAD_PARAMS / EDGE.

    Errors arrive in two shapes from MCP servers:
      - top-level JSON-RPC `error` (rare here)
      - `result.isError=true` with the error text inside `content[0].text`
    """
    if method != "tools/call":
        return ""
    blob = (error_msg + " " + response_text).lower()
    if is_error or error_msg:
        if "tool" in blob and "not found" in blob:
            return "BAD_TOOL"
        if "input validation" in blob or "invalid arguments" in blob:
            return "BAD_PARAMS"
        if any(m in blob for m in ("access denied", "enoent:", "no such file", "path outside")):
            return "EDGE"
        return "ERROR"
    if any(m in blob for m in ("access denied", "enoent:", "no such file", "path outside")):
        return "EDGE"
    return "VALID"


def response_status(error_code: int | None, is_error: bool) -> str:
    if error_code is not None:
        return "PROTOCOL_ERROR"
    if is_error:
        return "APP_ERROR"
    return "OK"


# ── data classes ─────────────────────────────────────────────────────────────
@dataclass
class PendingReq:
    ts: datetime
    method: str
    params: Any
    session_idx: int


@dataclass
class Session:
    idx: int
    uuid: str
    started_at: datetime
    server_name: str = ""
    server_version: str = ""
    protocol_version: str = ""
    client_name: str = ""
    client_version: str = ""
    n_tool_calls: int = 0
    tools_seen: list[dict] = field(default_factory=list)
    init_count: int = 0
    list_count: int = 0
    disconnect_at: datetime | None = None
    ended_normally: bool = False


# ── main parser ──────────────────────────────────────────────────────────────
def parse_wire_log(path: Path) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    pending: dict[tuple[int, int | str], PendingReq] = {}
    sessions: dict[int, Session] = {}
    session_idx = 0
    current_session_uuid = ""
    calls_rows: list[dict] = []
    tools_rows: list[dict] = []
    anomalies: list[dict] = []
    last_disconnect_ts: datetime | None = None
    call_index = 0

    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            ts = parse_ts(line)

            m = NEW_SESSION_RE.search(line)
            if m and ts is not None:
                session_idx += 1
                current_session_uuid = m.group(1)
                sessions[session_idx] = Session(idx=session_idx, uuid=current_session_uuid, started_at=ts)
                continue

            m = HTTP_DISCONNECT_RE.search(line)
            if m and ts is not None:
                last_disconnect_ts = ts
                continue

            m = DISCONNECT_RE.search(line)
            if m and ts is not None:
                uid = m.group(1)
                for sess in sessions.values():
                    if sess.uuid == uid:
                        sess.disconnect_at = ts
                        sess.ended_normally = not pending or all(
                            k[0] != sess.idx for k in pending
                        )
                        break
                continue

            m = RECV_RE.search(line)
            if m and ts is not None:
                try:
                    raw = bytes_literal_to_str(m.group(1))
                    payload = json.loads(raw)
                except (ValueError, SyntaxError):
                    continue
                rid = payload.get("id")
                method = payload.get("method", "")
                params = payload.get("params") or {}
                if rid is not None:
                    pending[(session_idx, rid)] = PendingReq(ts, method, params, session_idx)
                continue

            m = CHUNK_RE.search(line)
            if m and ts is not None:
                chunk_str = bytes_literal_to_str(m.group(1))
                body = extract_data_payload(chunk_str)
                if not body:
                    continue
                try:
                    payload = json.loads(body)
                except ValueError:
                    continue
                rid = payload.get("id")
                if rid is None:
                    continue
                key = (session_idx, rid)
                req = pending.pop(key, None)
                if req is None:
                    continue

                # ── handle different methods ───────────────────────────────
                error = payload.get("error")
                result = payload.get("result") or {}
                error_code = error.get("code") if isinstance(error, dict) else None
                error_msg = error.get("message", "") if isinstance(error, dict) else ""
                is_error = bool(result.get("isError")) if isinstance(result, dict) else False

                if req.method == "initialize" and isinstance(result, dict):
                    sess = sessions.get(req.session_idx)
                    if sess:
                        sess.init_count += 1
                        info = result.get("serverInfo") or {}
                        sess.server_name = info.get("name", "")
                        sess.server_version = info.get("version", "")
                        sess.protocol_version = result.get("protocolVersion", "")
                        cinfo = req.params.get("clientInfo") or {}
                        sess.client_name = cinfo.get("name", "")
                        sess.client_version = cinfo.get("version", "")
                        if sess.init_count > 1:
                            anomalies.append({
                                "kind": "REINITIALIZE",
                                "session_idx": req.session_idx,
                                "timestamp": ts.isoformat(timespec="milliseconds"),
                                "call_index": "",
                                "tool": "",
                                "detail": f"initialize called {sess.init_count}x in same session — usually a reconnect/retry",
                            })

                if req.method == "tools/list" and isinstance(result, dict):
                    sess = sessions.get(req.session_idx)
                    if sess:
                        sess.list_count += 1
                    for tool in result.get("tools", []):
                        ann = tool.get("annotations") or {}
                        row = {
                            "session_idx": req.session_idx,
                            "server_name": sess.server_name if sess else "",
                            "tool_name": tool.get("name", ""),
                            "description": (tool.get("description") or "").replace("\n", " "),
                            "input_schema": json.dumps(tool.get("inputSchema") or {}, separators=(",", ":")),
                            "output_schema": json.dumps(tool.get("outputSchema") or {}, separators=(",", ":")),
                            "read_only_hint": ann.get("readOnlyHint", ""),
                            "destructive_hint": ann.get("destructiveHint", ""),
                            "idempotent_hint": ann.get("idempotentHint", ""),
                        }
                        tools_rows.append(row)
                        if sess:
                            sess.tools_seen.append(row)

                if req.method == "tools/call":
                    call_index += 1
                    sess = sessions.get(req.session_idx)
                    if sess:
                        sess.n_tool_calls += 1
                    tool = req.params.get("name", "") if isinstance(req.params, dict) else ""
                    args = req.params.get("arguments", {}) if isinstance(req.params, dict) else {}
                    args_serialized = json.dumps(args, separators=(",", ":"), sort_keys=True)
                    response_text = ""
                    if isinstance(result, dict):
                        content = result.get("content") or []
                        if content and isinstance(content[0], dict):
                            response_text = content[0].get("text", "") or ""
                    if not response_text and error_msg:
                        response_text = error_msg
                    flat = response_text.replace("\n", " ").replace("\r", "")
                    elapsed_s = (ts - req.ts).total_seconds()
                    status = response_status(error_code, is_error)

                    # ── retry detection: same (session, tool, args) within window ───
                    retry_of = ""
                    is_retry = False
                    for prev in reversed(calls_rows):
                        if prev["session_idx"] != req.session_idx:
                            continue
                        if prev["tool"] != tool or prev["args_json_sorted"] != args_serialized:
                            continue
                        prev_ts = datetime.fromisoformat(prev["response_ts"])
                        if (req.ts - prev_ts).total_seconds() <= RETRY_WINDOW_S:
                            retry_of = prev["index"]
                            is_retry = True
                            anomalies.append({
                                "kind": "RETRY",
                                "session_idx": req.session_idx,
                                "timestamp": req.ts.isoformat(timespec="milliseconds"),
                                "call_index": call_index,
                                "tool": tool,
                                "detail": f"identical args repeated within {(req.ts - prev_ts).total_seconds():.1f}s of call #{prev['index']}",
                            })
                        break

                    if elapsed_s > SLOW_CALL_S:
                        anomalies.append({
                            "kind": "SLOW_CALL",
                            "session_idx": req.session_idx,
                            "timestamp": req.ts.isoformat(timespec="milliseconds"),
                            "call_index": call_index,
                            "tool": tool,
                            "detail": f"latency {elapsed_s:.2f}s > {SLOW_CALL_S}s",
                        })

                    calls_rows.append({
                        "index": call_index,
                        "session_idx": req.session_idx,
                        "request_ts": req.ts.isoformat(timespec="milliseconds"),
                        "response_ts": ts.isoformat(timespec="milliseconds"),
                        "elapsed_s": f"{elapsed_s:.3f}",
                        "category": categorize(req.method, is_error or error_code is not None, error_msg, response_text),
                        "status": status,
                        "tool": tool,
                        "args_keys": str(args_keys(args)),
                        "args_json": json.dumps(args, separators=(",", ":")),
                        "args_json_sorted": args_serialized,
                        "error_code": error_code if error_code is not None else "",
                        "error_message": error_msg,
                        "is_retry": is_retry,
                        "retry_of_index": retry_of,
                        "response_preview": flat[:PREVIEW_LEN],
                        "response_text": response_text,
                    })

    # ── post-pass: orphaned requests (request fired, no response ever arrived) ──
    for (sidx, rid), req in pending.items():
        anomalies.append({
            "kind": "ORPHANED_REQUEST",
            "session_idx": sidx,
            "timestamp": req.ts.isoformat(timespec="milliseconds"),
            "call_index": "",
            "tool": req.params.get("name", "") if isinstance(req.params, dict) else "",
            "detail": f"{req.method} id={rid} sent but no response — likely mid-call disconnect or server hang",
        })

    # ── post-pass: session-level oddities ──
    for s in sessions.values():
        if s.init_count == 0:
            anomalies.append({
                "kind": "EMPTY_SESSION",
                "session_idx": s.idx,
                "timestamp": s.started_at.isoformat(timespec="milliseconds"),
                "call_index": "",
                "tool": "",
                "detail": "SSE connected but never sent initialize — probe or aborted handshake",
            })
        elif s.list_count == 0 and s.n_tool_calls == 0:
            anomalies.append({
                "kind": "INIT_ONLY",
                "session_idx": s.idx,
                "timestamp": s.started_at.isoformat(timespec="milliseconds"),
                "call_index": "",
                "tool": "",
                "detail": "initialize done but no tools/list and no tools/call — agent attached then quit",
            })
        elif s.list_count > 0 and s.n_tool_calls == 0:
            anomalies.append({
                "kind": "LISTED_NO_CALLS",
                "session_idx": s.idx,
                "timestamp": s.started_at.isoformat(timespec="milliseconds"),
                "call_index": "",
                "tool": "",
                "detail": "agent listed tools but never called any",
            })

    # strip helper column before emitting calls.csv
    for row in calls_rows:
        row.pop("args_json_sorted", None)

    sessions_rows = [
        {
            "session_idx": s.idx,
            "session_uuid": s.uuid,
            "started_at": s.started_at.isoformat(timespec="milliseconds"),
            "server_name": s.server_name,
            "server_version": s.server_version,
            "protocol_version": s.protocol_version,
            "client_name": s.client_name,
            "client_version": s.client_version,
            "init_count": s.init_count,
            "n_tool_calls": s.n_tool_calls,
            "n_tools_listed": len(s.tools_seen),
            "ended_normally": s.ended_normally,
            "disconnect_at": s.disconnect_at.isoformat(timespec="milliseconds") if s.disconnect_at else "",
        }
        for s in sessions.values()
    ]

    return calls_rows, tools_rows, sessions_rows, anomalies


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(wire_path: str) -> None:
    src = Path(wire_path).resolve()
    out_dir = src.parent / "parsed"
    calls, tools, sessions, anomalies = parse_wire_log(src)

    write_csv(out_dir / "calls.csv", calls, [
        "index", "session_idx", "request_ts", "response_ts", "elapsed_s",
        "category", "status", "tool", "args_keys", "args_json",
        "error_code", "error_message", "is_retry", "retry_of_index",
        "response_preview", "response_text",
    ])
    write_csv(out_dir / "tools_catalog.csv", tools, [
        "session_idx", "server_name", "tool_name", "description",
        "input_schema", "output_schema",
        "read_only_hint", "destructive_hint", "idempotent_hint",
    ])
    write_csv(out_dir / "sessions.csv", sessions, [
        "session_idx", "session_uuid", "started_at",
        "server_name", "server_version", "protocol_version",
        "client_name", "client_version",
        "init_count", "n_tool_calls", "n_tools_listed",
        "ended_normally", "disconnect_at",
    ])
    write_csv(out_dir / "anomalies.csv", anomalies, [
        "kind", "session_idx", "timestamp", "call_index", "tool", "detail",
    ])

    print(f"source : {src}")
    print(f"output : {out_dir}")
    print(f"  sessions       : {len(sessions)}")
    print(f"  tools_catalog  : {len(tools)} rows")
    print(f"  calls          : {len(calls)} rows")
    print(f"  anomalies      : {len(anomalies)} rows")
    if calls:
        from collections import Counter
        cats = Counter(r["category"] or "(non-tool-call)" for r in calls)
        print("  category       :", dict(cats))
        statuses = Counter(r["status"] for r in calls)
        print("  status         :", dict(statuses))
    if anomalies:
        from collections import Counter
        kinds = Counter(a["kind"] for a in anomalies)
        print("  anomaly kinds  :", dict(kinds))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
