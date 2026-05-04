"""
Manual inspection of mcp-proxy wire.log — one subcommand per question.

Each subcommand answers ONE focused question and prints a small report.
Nothing here writes CSVs; this is for reading the log by hand.

Usage:
    uv run python logs/proxy/inspect_wire.py retries     <wire.log>
    uv run python logs/proxy/inspect_wire.py orphans     <wire.log>
    uv run python logs/proxy/inspect_wire.py disconnects <wire.log>
    uv run python logs/proxy/inspect_wire.py slow        <wire.log> [seconds=10]
    uv run python logs/proxy/inspect_wire.py sessions    <wire.log>
    uv run python logs/proxy/inspect_wire.py calls       <wire.log>
    uv run python logs/proxy/inspect_wire.py tools       <wire.log>
    uv run python logs/proxy/inspect_wire.py raw         <wire.log> [N=50]
"""

from __future__ import annotations

import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ── line patterns ────────────────────────────────────────────────────────────
TS_RE = re.compile(r"^\[[DI] (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})")
RECV_RE = re.compile(r"Received JSON: (b'.*'|b\".*\")\s*$")
CHUNK_RE = re.compile(r"chunk: (b'event: message.*'|b\"event: message.*\")\s*$")
NEW_SESSION_RE = re.compile(r"Created new session with ID: ([0-9a-f-]+)")
DISCONNECT_RE = re.compile(r"Client session disconnected ([0-9a-f-]+)")
HTTP_DC_RE = re.compile(r"Got event: http\.disconnect")


# ── tiny helpers ─────────────────────────────────────────────────────────────
def parse_ts(line: str) -> datetime | None:
    m = TS_RE.match(line)
    return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f") if m else None


def bytes_lit(s: str) -> str:
    return ast.literal_eval(s).decode("utf-8", errors="replace")


def chunk_payload(s: str) -> str | None:
    """Pull the JSON body out of an SSE chunk."""
    i = s.find("data: ")
    return s[i + 6:].rstrip("\r\n") if i != -1 else None


def iter_events(path: Path):
    """
    Walk a wire.log line by line and yield (kind, ts, **fields) tuples.

    Kinds:
        new_session(uuid)
        request(session_idx, ts, id, method, params)
        response(session_idx, ts, id, error_code, error_msg, is_error, content_text, raw)
        http_disconnect(ts)
        session_disconnect(ts, uuid)
    """
    session_idx = 0
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            ts = parse_ts(line)

            m = NEW_SESSION_RE.search(line)
            if m and ts is not None:
                session_idx += 1
                yield ("new_session", ts, {"session_idx": session_idx, "uuid": m.group(1)})
                continue

            if HTTP_DC_RE.search(line) and ts is not None:
                yield ("http_disconnect", ts, {})
                continue

            m = DISCONNECT_RE.search(line)
            if m and ts is not None:
                yield ("session_disconnect", ts, {"uuid": m.group(1)})
                continue

            m = RECV_RE.search(line)
            if m and ts is not None:
                try:
                    payload = json.loads(bytes_lit(m.group(1)))
                except (ValueError, SyntaxError):
                    continue
                yield ("request", ts, {
                    "session_idx": session_idx,
                    "id": payload.get("id"),
                    "method": payload.get("method", ""),
                    "params": payload.get("params") or {},
                })
                continue

            m = CHUNK_RE.search(line)
            if m and ts is not None:
                body = chunk_payload(bytes_lit(m.group(1)))
                if not body:
                    continue
                try:
                    payload = json.loads(body)
                except ValueError:
                    continue
                err = payload.get("error") or {}
                result = payload.get("result") or {}
                content_text = ""
                if isinstance(result, dict):
                    c = result.get("content") or []
                    if c and isinstance(c[0], dict):
                        content_text = c[0].get("text", "") or ""
                yield ("response", ts, {
                    "session_idx": session_idx,
                    "id": payload.get("id"),
                    "error_code": err.get("code") if isinstance(err, dict) else None,
                    "error_msg": err.get("message", "") if isinstance(err, dict) else "",
                    "is_error": bool(result.get("isError")) if isinstance(result, dict) else False,
                    "content_text": content_text,
                    "raw_result": result,
                })


def pair_calls(path: Path):
    """
    Walk events and yield one row per matched (request, response).

    Each row: {tool, args, request_ts, response_ts, elapsed_s, session_idx,
               error_code, error_msg, is_error, content_text}
    """
    pending: dict[tuple, dict] = {}
    for kind, ts, ev in iter_events(path):
        if kind == "request":
            if ev["id"] is not None:
                pending[(ev["session_idx"], ev["id"])] = {**ev, "ts": ts}
        elif kind == "response":
            req = pending.pop((ev["session_idx"], ev["id"]), None)
            if req is None:
                continue
            params = req["params"] if isinstance(req["params"], dict) else {}
            yield {
                "session_idx": req["session_idx"],
                "method": req["method"],
                "tool": params.get("name", "") if req["method"] == "tools/call" else "",
                "args": params.get("arguments", {}) if req["method"] == "tools/call" else {},
                "params_json": json.dumps(params, separators=(",", ":"), sort_keys=True),
                "request_ts": req["ts"],
                "response_ts": ts,
                "elapsed_s": (ts - req["ts"]).total_seconds(),
                "error_code": ev["error_code"],
                "error_msg": ev["error_msg"],
                "is_error": ev["is_error"],
                "content_text": ev["content_text"],
                "raw_result": ev["raw_result"],
            }
    # whatever is left is orphaned — handled by the orphan subcommand


# ── subcommands (one focused question each) ──────────────────────────────────
def cmd_retries(path: Path, window_s: float = 30.0) -> None:
    """Find tool calls repeated with identical args within window_s seconds."""
    print(f"-- retries (same tool + same args within {window_s:.0f}s) --\n")
    seen: list[dict] = []
    hits = 0
    for row in pair_calls(path):
        if row["method"] != "tools/call":
            continue
        args_key = json.dumps(row["args"], sort_keys=True)
        for prev in reversed(seen):
            if prev["session_idx"] != row["session_idx"]:
                continue
            if prev["tool"] != row["tool"] or prev["args_key"] != args_key:
                continue
            gap = (row["request_ts"] - prev["response_ts"]).total_seconds()
            if 0 <= gap <= window_s:
                hits += 1
                print(f"  s#{row['session_idx']} {row['tool']:<22} "
                      f"first @ {prev['request_ts']:%H:%M:%S.%f}  "
                      f"retry @ {row['request_ts']:%H:%M:%S.%f}  gap={gap:.2f}s")
                print(f"     args: {args_key}")
            break
        seen.append({"tool": row["tool"], "args_key": args_key,
                     "request_ts": row["request_ts"], "response_ts": row["response_ts"],
                     "session_idx": row["session_idx"]})
    print(f"\n  total retries: {hits}")


def cmd_orphans(path: Path) -> None:
    """Find requests that never got a response (likely mid-call disconnect or hang)."""
    print("-- orphaned requests (sent, never answered) --\n")
    pending: dict[tuple, dict] = {}
    for kind, ts, ev in iter_events(path):
        if kind == "request" and ev["id"] is not None:
            pending[(ev["session_idx"], ev["id"])] = {**ev, "ts": ts}
        elif kind == "response":
            pending.pop((ev["session_idx"], ev["id"]), None)
    if not pending:
        print("  (none — every request was answered)")
        return
    for (sidx, rid), req in pending.items():
        params = req["params"] if isinstance(req["params"], dict) else {}
        tool = params.get("name", "") if req["method"] == "tools/call" else ""
        print(f"  s#{sidx} id={rid:<3} {req['method']:<14} tool={tool:<20} sent @ {req['ts']:%H:%M:%S.%f}")
    print(f"\n  total orphans: {len(pending)}")


def cmd_disconnects(path: Path) -> None:
    """List every disconnect with what was in flight at the time."""
    print("-- disconnects (session_disconnect / http.disconnect events) --\n")
    pending: dict[tuple, dict] = {}
    last_http_dc: datetime | None = None
    for kind, ts, ev in iter_events(path):
        if kind == "request" and ev["id"] is not None:
            pending[(ev["session_idx"], ev["id"])] = {**ev, "ts": ts}
        elif kind == "response":
            pending.pop((ev["session_idx"], ev["id"]), None)
        elif kind == "http_disconnect":
            last_http_dc = ts
        elif kind == "session_disconnect":
            in_flight = [k for k in pending if pending[k].get("ts")]
            normal = " (clean)" if not in_flight else f"  ⚠ {len(in_flight)} in-flight"
            http_marker = ""
            if last_http_dc and (ts - last_http_dc).total_seconds() < 0.1:
                http_marker = "  [paired http.disconnect]"
            print(f"  {ts:%H:%M:%S.%f}  uuid={ev['uuid']}{normal}{http_marker}")


def cmd_slow(path: Path, threshold_s: float = 10.0) -> None:
    """List tool calls slower than threshold (default 10s)."""
    print(f"-- slow calls (latency > {threshold_s:.0f}s) --\n")
    hits = 0
    for row in pair_calls(path):
        if row["method"] != "tools/call":
            continue
        if row["elapsed_s"] > threshold_s:
            hits += 1
            print(f"  s#{row['session_idx']} {row['tool']:<22} {row['elapsed_s']:>7.2f}s  "
                  f"args={json.dumps(row['args'])[:60]}")
    print(f"\n  total slow calls: {hits}")


def cmd_sessions(path: Path) -> None:
    """Per-session summary: init / list / calls / clean disconnect or not."""
    print("-- sessions --\n")
    sessions: dict[int, dict] = {}
    pending: dict[tuple, dict] = {}
    uuid_to_idx: dict[str, int] = {}
    for kind, ts, ev in iter_events(path):
        if kind == "new_session":
            sessions[ev["session_idx"]] = {
                "uuid": ev["uuid"], "started": ts,
                "init": 0, "list": 0, "calls": 0, "ended": None,
            }
            uuid_to_idx[ev["uuid"]] = ev["session_idx"]
        elif kind == "request":
            if ev["method"] == "initialize":
                if ev["session_idx"] in sessions:
                    sessions[ev["session_idx"]]["init"] += 1
            elif ev["method"] == "tools/list":
                if ev["session_idx"] in sessions:
                    sessions[ev["session_idx"]]["list"] += 1
            elif ev["method"] == "tools/call":
                if ev["session_idx"] in sessions:
                    sessions[ev["session_idx"]]["calls"] += 1
            if ev["id"] is not None:
                pending[(ev["session_idx"], ev["id"])] = ts
        elif kind == "response":
            pending.pop((ev["session_idx"], ev["id"]), None)
        elif kind == "session_disconnect":
            sidx = uuid_to_idx.get(ev["uuid"])
            if sidx in sessions:
                sessions[sidx]["ended"] = ts
                sessions[sidx]["clean"] = not any(k[0] == sidx for k in pending)
    print(f"  {'#':<3} {'started':<23} {'init':>4} {'list':>4} {'calls':>5}  status   uuid")
    for idx, s in sessions.items():
        ended = "(open)" if s["ended"] is None else (
            "clean" if s.get("clean", True) else "DROPPED"
        )
        print(f"  {idx:<3} {s['started']:%Y-%m-%d %H:%M:%S}  "
              f"{s['init']:>4} {s['list']:>4} {s['calls']:>5}  {ended:<8} {s['uuid']}")


def cmd_calls(path: Path) -> None:
    """Chronological list of every tool call (one line each)."""
    print("-- tool calls (chronological) --\n")
    print(f"  {'#':<3} {'time':<12} {'s':<3} {'tool':<24} {'elapsed':>8}  result")
    i = 0
    for row in pair_calls(path):
        if row["method"] != "tools/call":
            continue
        i += 1
        text = (row["error_msg"] or row["content_text"]).replace("\n", " ").replace("\r", "")
        verdict = "ERR" if (row["is_error"] or row["error_code"]) else "OK "
        time_str = row["request_ts"].strftime("%H:%M:%S.%f")[:12]
        print(f"  {i:<3} {time_str:<12} s{row['session_idx']:<2} "
              f"{row['tool']:<24} {row['elapsed_s']:>7.2f}s  {verdict} {text[:55]}")


def cmd_tools(path: Path) -> None:
    """List the tool catalog from every tools/list response."""
    print("-- tools (from tools/list responses) --\n")
    seen = set()
    for row in pair_calls(path):
        if row["method"] != "tools/list":
            continue
        for tool in row["raw_result"].get("tools", []):
            key = (row["session_idx"], tool.get("name"))
            if key in seen:
                continue
            seen.add(key)
            ann = tool.get("annotations") or {}
            flags = []
            if ann.get("readOnlyHint"):
                flags.append("read-only")
            if ann.get("destructiveHint"):
                flags.append("destructive")
            if ann.get("idempotentHint"):
                flags.append("idempotent")
            flag_str = ",".join(flags) if flags else "-"
            desc = (tool.get("description") or "").split(".")[0][:80]
            print(f"  s#{row['session_idx']}  {tool.get('name', ''):<28} [{flag_str}]")
            print(f"      {desc}")


def cmd_raw(path: Path, n: float = 50) -> None:
    """Pretty-print the first N parsed JSON-RPC frames in order."""
    n = int(n)
    print(f"-- raw frames (first {n}) --\n")
    count = 0
    for kind, ts, ev in iter_events(path):
        if kind not in ("request", "response", "session_disconnect", "new_session"):
            continue
        count += 1
        if count > n:
            break
        if kind == "new_session":
            print(f"  {ts:%H:%M:%S.%f} NEW   session #{ev['session_idx']} ({ev['uuid']})")
        elif kind == "request":
            params = ev["params"] if isinstance(ev["params"], dict) else {}
            tool = params.get("name", "")
            extra = f" tool={tool}" if tool else ""
            print(f"  {ts:%H:%M:%S.%f} REQ   s{ev['session_idx']} id={ev['id']} {ev['method']}{extra}")
        elif kind == "response":
            tag = "ERR" if (ev["is_error"] or ev["error_code"]) else "OK "
            text = (ev["error_msg"] or ev["content_text"]).replace("\n", " ")[:50]
            print(f"  {ts:%H:%M:%S.%f} RESP  s{ev['session_idx']} id={ev['id']} {tag} {text}")
        elif kind == "session_disconnect":
            print(f"  {ts:%H:%M:%S.%f} DC    {ev['uuid']}")


# ── dispatcher ───────────────────────────────────────────────────────────────
COMMANDS = {
    "retries": cmd_retries,
    "orphans": cmd_orphans,
    "disconnects": cmd_disconnects,
    "slow": cmd_slow,
    "sessions": cmd_sessions,
    "calls": cmd_calls,
    "tools": cmd_tools,
    "raw": cmd_raw,
}


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in COMMANDS:
        print(__doc__)
        return 1
    cmd = argv[1]
    path = Path(argv[2]).resolve()
    if not path.exists():
        print(f"error: file not found: {path}")
        return 2
    fn = COMMANDS[cmd]
    extra: list[float] = []
    if cmd in ("slow", "retries", "raw") and len(argv) >= 4:
        try:
            extra.append(float(argv[3]))
        except ValueError:
            print(f"error: third argument must be a number for `{cmd}`")
            return 2
    try:
        if extra:
            fn(path, extra[0])  # type: ignore[arg-type]
        else:
            fn(path)
    except UnicodeEncodeError:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        if extra:
            fn(path, extra[0])  # type: ignore[arg-type]
        else:
            fn(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
