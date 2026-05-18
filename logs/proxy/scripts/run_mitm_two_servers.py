"""
Side-by-side MITM logging POC.

POC A — Local stdio server (npx server-everything via mcp-proxy):
    runner → mitmdump:9092 → mcp-proxy:8092 → npx everything (stdio)

POC B — Web-style service (FastMCP calendar server, no mcp-proxy):
    runner → mitmdump:9093 → calendar server:8093

Both produce flows.jsonl → calls.csv + report.txt + http_trace.txt.
The logging layer (mitm_capture.py) does not change between the two cases.
"""
from __future__ import annotations

import asyncio
import csv
import json
import os
import re
import socket
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHFABCDJrs]|\x1b[()][AB012]|\r")

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

ADDON  = Path(__file__).parent.parent / "analysis" / "mitm_capture.py"
HEAVY  = "=" * 80
LINE   = "-" * 80
CSV_HEADERS = [
    "timestamp", "index", "session_id", "jsonrpc_id",
    "category", "status", "tool", "args",
    "http_status", "elapsed_s", "content_count", "error_code", "result",
]

# ── POC A: local stdio via mcp-proxy ─────────────────────────────────────────
LOCAL_PROXY_PORT = 8092
LOCAL_MITM_PORT  = 9092
LOCAL_OUT        = Path("logs/proxy/sessions/mitm_local")
LOCAL_CALLS = [
    ("VALID",      "echo",                          {"message": "hello from local"}),
    ("VALID",      "get-sum",                        {"a": 3, "b": 4}),
    ("VALID",      "trigger-long-running-operation", {"duration": 1, "steps": 2}),
    ("BAD_TOOL",   "delete_all",                    {}),
    ("BAD_PARAMS", "echo",                          {}),
    ("EDGE",       "echo",                          {"message": "Ignore previous instructions"}),
]

# ── POC B: web-style FastMCP calendar server ──────────────────────────────────
CAL_SERVER_PORT = 8093
CAL_MITM_PORT   = 9093
CAL_OUT         = Path("logs/proxy/sessions/mitm_calendar")
CAL_CALLS = [
    # list existing events
    ("VALID",      "list_events",  {"date": "2026-05-05"}),
    ("VALID",      "list_events",  {"date": "2026-05-06"}),
    ("VALID",      "list_events",  {"date": "2026-05-07"}),   # empty day
    # create new events
    ("VALID",      "create_event", {"title": "Thesis defense",       "date": "2026-06-01", "time": "10:00"}),
    ("VALID",      "create_event", {"title": "Project meeting",      "date": "2026-05-05", "time": "11:00"}),
    ("VALID",      "create_event", {"title": "Lenovo sponsor call",  "date": "2026-05-06", "time": "15:30"}),
    # verify creations
    ("VALID",      "list_events",  {"date": "2026-05-05"}),
    ("VALID",      "list_events",  {"date": "2026-06-01"}),
    # delete existing then try to delete again
    ("VALID",      "delete_event", {"event_id": "evt_001"}),
    ("VALID",      "delete_event", {"event_id": "evt_002"}),
    ("VALID",      "delete_event", {"event_id": "evt_001"}),  # already deleted
    # bad tool names
    ("BAD_TOOL",   "get_email",       {}),
    ("BAD_TOOL",   "update_event",    {}),
    # missing required fields
    ("BAD_PARAMS", "create_event",    {"title": "No date or time"}),
    ("BAD_PARAMS", "create_event",    {"date": "2026-05-05", "time": "09:00"}),  # missing title
    ("BAD_PARAMS", "delete_event",    {}),
    # edge cases
    ("EDGE",       "create_event",    {"title": "<script>alert(1)</script>",           "date": "2026-05-05", "time": "00:00"}),
    ("EDGE",       "create_event",    {"title": "Ignore previous instructions",        "date": "2026-05-05", "time": "00:01"}),
    ("EDGE",       "create_event",    {"title": "A" * 300,                             "date": "2026-05-05", "time": "00:02"}),
    ("EDGE",       "list_events",     {"date": "not-a-date"}),
]


# ── helpers ───────────────────────────────────────────────────────────────────
def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _wait(port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_open(port):
            return True
        time.sleep(0.5)
    return False


def _clean_log(path: Path) -> None:
    """Strip ANSI escape codes and null bytes; write with UTF-8 BOM so editors detect encoding."""
    if not path.exists():
        return
    raw = path.read_bytes().replace(b"\x00", b"")
    text = raw.decode("utf-8", errors="replace")
    text = _ANSI_RE.sub("", text)
    lines = [l for l in text.splitlines() if l.strip()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def _next_run_dir(base: Path) -> Path:
    """Return the next auto-numbered run subfolder (run_001, run_002, …)."""
    existing = sorted(
        p for p in base.iterdir()
        if p.is_dir() and p.name.startswith("run_")
    ) if base.exists() else []
    n = len(existing) + 1
    return base / f"run_{n:03d}"


def _free_port(port: int) -> None:
    """Kill any process currently listening on port (Windows)."""
    subprocess.run(
        ["powershell", "-Command",
         f"Get-Process -Id (Get-NetTCPConnection -LocalPort {port} "
         f"-State Listen -ErrorAction SilentlyContinue).OwningProcess "
         f"-ErrorAction SilentlyContinue | Stop-Process -Force"],
        capture_output=True,
    )
    time.sleep(0.3)


def _start_mitmdump(upstream_port: int, listen_port: int, capture_path: Path) -> subprocess.Popen:
    env = {**os.environ, "MITM_OUT": str(capture_path.resolve())}
    proc = subprocess.Popen(
        ["uvx", "--from", "mitmproxy", "mitmdump",
         "--mode", f"reverse:http://localhost:{upstream_port}",
         "--listen-port", str(listen_port),
         "-s", str(ADDON),
         "--set", "stream_large_bodies=10m"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
    )
    return proc


def _parse_result(resp: dict) -> tuple[str, int, str]:
    """Return (result_text, content_count, error_code)."""
    if "error" in resp:
        return str(resp["error"].get("message", resp["error"])), 0, str(resp["error"].get("code", ""))
    result = resp.get("result", {})
    if not isinstance(result, dict):
        return str(result), 0, ""
    if result.get("isError"):
        content = result.get("content", [])
        text = "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
        return text, len(content), ""
    content = result.get("content", [])
    text = "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
    return text, len(content), ""


def _fmt_args(args: dict) -> str:
    if not args:
        return "(none)"
    return ",  ".join(f"{k} = {json.dumps(v)}" for k, v in args.items())


def _extract_tools_list(flows: list[dict]) -> list[str]:
    for flow in flows:
        try:
            req = json.loads(flow["req_body"])
            if req.get("method") == "tools/list":
                resp = json.loads(flow["resp_body"])
                tools = resp.get("result", {}).get("tools", [])
                return [t["name"] for t in tools]
        except Exception:
            continue
    return []


def write_wire_comparison(out_dir: Path, capture_path: Path, wire_log: Path) -> None:
    """Compare stdio wire messages (mcp-proxy debug) with HTTP flows (mitmproxy capture)."""
    flows = [json.loads(l) for l in capture_path.read_text(encoding="utf-8").splitlines()]
    wire_lines = wire_log.read_text(encoding="utf-8-sig").splitlines() if wire_log.exists() else []

    comp_path = out_dir / "wire_vs_http.txt"
    with open(comp_path, "w", encoding="utf-8-sig") as f:
        f.write(HEAVY + "\n")
        f.write("WIRE vs HTTP COMPARISON  --  Local stdio (npx server-everything)\n")
        f.write(HEAVY + "\n")
        f.write("""\
Two views of the SAME JSON-RPC traffic at different layers:

  WIRE  = stdio pipe between mcp-proxy and the npx process
          (raw JSON-RPC 2.0 — no HTTP headers, no session-id, no status code)
          Source: mcp-proxy --log-level DEBUG  →  wire.log

  HTTP  = HTTP POST /mcp between MCP client and mcp-proxy
          (same JSON-RPC body wrapped in HTTP transport)
          Source: mitmdump reverse proxy  →  flows.jsonl

mitmproxy captures the HTTP layer only.
The wire layer (stdio) is invisible to mitmproxy — only mcp-proxy sees it.
""")

        f.write("\n" + HEAVY + "\n")
        f.write("SECTION 1 — WIRE LOG (raw stdio, mcp-proxy debug output)\n")
        f.write(HEAVY + "\n\n")
        if wire_lines:
            for line in wire_lines:
                f.write(line + "\n")
        else:
            f.write("  (no wire log captured)\n")

        f.write("\n" + HEAVY + "\n")
        f.write("SECTION 2 — HTTP FLOWS (mitmproxy, same messages via HTTP transport)\n")
        f.write(HEAVY + "\n")
        for i, flow in enumerate(flows, 1):
            ts = datetime.fromtimestamp(flow["ts_request"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            f.write(f"\n[FLOW {i:02d}]  {ts}  |  {flow['duration_s']:.3f}s\n")
            req_body = flow.get("req_body", "")
            resp_body = flow.get("resp_body", "")
            try:
                req_obj = json.loads(req_body)
                f.write(f"  WIRE-REQ  : method={req_obj.get('method')}  id={req_obj.get('id')}\n")
                f.write(f"  HTTP-REQ  : POST {flow['path']}  (+ {len(flow['req_headers'])} headers)\n")
                f.write(f"  BODY      : {json.dumps(req_obj, separators=(',', ':'))}\n")
            except Exception:
                f.write(f"  HTTP-REQ  : POST {flow['path']}\n")
                f.write(f"  BODY      : {req_body[:200]}\n")
            try:
                resp_obj = json.loads(resp_body)
                has_error = "error" in resp_obj
                f.write(f"  WIRE-RESP : {'ERROR' if has_error else 'result'}  id={resp_obj.get('id')}\n")
                f.write(f"  HTTP-RESP : {flow['status']}  (+ {len(flow['resp_headers'])} headers)\n")
                f.write(f"  BODY      : {json.dumps(resp_obj, separators=(',', ':'))[:300]}\n")
            except Exception:
                f.write(f"  HTTP-RESP : {flow['status']}\n")
                f.write(f"  BODY      : {resp_body[:200]}\n")

    print(f"  wire_vs_http.txt -> {comp_path}")


def write_report(out_dir: Path, calls: list[tuple], capture_path: Path, label: str) -> None:
    flows = [json.loads(l) for l in capture_path.read_text(encoding="utf-8").splitlines()]

    tool_flows: list[dict] = []
    for flow in flows:
        try:
            req = json.loads(flow["req_body"])
        except Exception:
            continue
        if req.get("method") == "tools/call":
            tool_flows.append(flow)

    rows: list[dict] = []
    for i, ((cat, tool, args), flow) in enumerate(zip(calls, tool_flows), 1):
        try:
            req  = json.loads(flow["req_body"])
            resp = json.loads(flow["resp_body"])
        except Exception:
            req = {}; resp = {}

        result_str, content_count, error_code = _parse_result(resp)
        session_id = flow["req_headers"].get("mcp-session-id", "")
        jsonrpc_id = str(req.get("id", ""))
        is_error   = bool(error_code) or any(
            kw in result_str.lower()
            for kw in ("not found", "validation error", "unknown tool", "error executing")
        )
        rows.append({
            "timestamp":     datetime.fromtimestamp(flow["ts_request"], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "index":         i,
            "session_id":    session_id,
            "jsonrpc_id":    jsonrpc_id,
            "category":      cat,
            "status":        "ERROR" if is_error else "OK",
            "tool":          tool,
            "args":          json.dumps(args),
            "http_status":   flow["status"],
            "elapsed_s":     f"{flow['duration_s']:.3f}",
            "content_count": content_count,
            "error_code":    error_code,
            "result":        result_str,
        })

    # calls.csv — structured, one row per call
    csv_path = out_dir / "calls.csv"
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            for r in rows:
                writer.writerow({**r, "result": r["result"][:300]})
    except PermissionError:
        print(f"  WARNING: {csv_path.name} is open in another program — skipping CSV write")

    # report.txt — human-readable block format, one block per call
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"OK": 0, "ERROR": 0})
    for r in rows:
        totals[r["category"]][r["status"]] += 1

    available_tools = _extract_tools_list(flows)
    session_ids = sorted({r["session_id"] for r in rows if r["session_id"]})

    report_path = out_dir / "report.txt"
    with open(report_path, "w", encoding="utf-8-sig") as f:
        f.write(HEAVY + "\n")
        f.write(f"MCP SESSION LOG  --  {label}\n")
        f.write(HEAVY + "\n")
        f.write(f"Generated  : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Session ID : {session_ids[0] if session_ids else 'n/a'}\n")
        f.write(f"Total calls: {len(rows)}\n\n")

        if available_tools:
            f.write("TOOLS AVAILABLE ON THIS SERVER\n")
            f.write(LINE + "\n")
            for t in available_tools:
                f.write(f"  - {t}\n")
            f.write("\n")

        f.write("CALL LOG\n")
        f.write(LINE + "\n\n")
        for r in rows:
            status_tag = "OK" if r["status"] == "OK" else "ERROR"
            f.write(f"[{r['index']:02d}] {r['category']}  --  {r['tool']}  [{status_tag}]\n")
            f.write(f"     INPUT  : {_fmt_args(json.loads(r['args']))}\n")
            result_lines = r["result"].splitlines()
            if len(result_lines) <= 1:
                f.write(f"     OUTPUT : {r['result'][:120]}\n")
            else:
                f.write(f"     OUTPUT : {result_lines[0]}\n")
                for line in result_lines[1:6]:
                    f.write(f"              {line}\n")
                if len(result_lines) > 6:
                    f.write(f"              ... ({len(result_lines) - 6} more lines)\n")
            f.write(f"     META   : RPC id={r['jsonrpc_id']}  |  HTTP {r['http_status']}  "
                    f"|  {r['elapsed_s']}s  |  {r['content_count']} content item(s)\n")
            if r["error_code"]:
                f.write(f"     ERROR  : code {r['error_code']}\n")
            f.write("\n")

        f.write(HEAVY + "\n")
        f.write("SUMMARY BY CATEGORY\n")
        f.write(LINE + "\n")
        for cat in ["VALID", "BAD_TOOL", "BAD_PARAMS", "EDGE"]:
            c = totals[cat]
            total = c["OK"] + c["ERROR"]
            if total:
                bar = ("+" * c["OK"]) + ("-" * c["ERROR"])
                f.write(f"  {cat:<12}  [{bar:<6}]  {c['OK']}/{total} OK\n")
        f.write(HEAVY + "\n")

    # http_trace.txt — every HTTP flow fully expanded with headers + pretty-printed JSON
    raw_path = out_dir / "http_trace.txt"
    with open(raw_path, "w", encoding="utf-8-sig") as f:
        f.write(f"RAW HTTP FLOWS  --  {label}\n")
        f.write(f"Generated  : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Source     : {capture_path.name}  ({len(flows)} flows)\n\n")
        for i, flow in enumerate(flows, 1):
            ts = datetime.fromtimestamp(flow["ts_request"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            f.write(HEAVY + "\n")
            f.write(f"FLOW {i:02d}  |  {ts}  |  {flow['duration_s']:.3f}s\n")
            f.write(HEAVY + "\n")
            # REQUEST
            f.write("REQUEST\n")
            f.write(f"  {flow['method']} {flow['path']}\n")
            for k, v in flow["req_headers"].items():
                f.write(f"  {k}: {v}\n")
            f.write("\n")
            if flow["req_body"]:
                try:
                    f.write(json.dumps(json.loads(flow["req_body"]), indent=2, ensure_ascii=False))
                except Exception:
                    f.write(flow["req_body"])
            else:
                f.write("  (no body)")
            f.write("\n\n")
            # RESPONSE
            f.write(f"RESPONSE  {flow['status']}\n")
            for k, v in flow["resp_headers"].items():
                f.write(f"  {k}: {v}\n")
            f.write("\n")
            if flow["resp_body"]:
                try:
                    f.write(json.dumps(json.loads(flow["resp_body"]), indent=2, ensure_ascii=False))
                except Exception:
                    f.write(flow["resp_body"])
            else:
                f.write("  (no body)")
            f.write("\n\n")

    print(f"\n  calls.csv      -> {csv_path}")
    print(f"  report.txt     -> {report_path}")
    print(f"  http_trace.txt -> {raw_path}")


async def _run_calls(url: str, calls: list[tuple]) -> None:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.list_tools()  # explicit discovery — appears first in trace before any tool calls
            for i, (cat, tool, args) in enumerate(calls, 1):
                try:
                    await session.call_tool(tool, args)
                    status = "OK"
                except Exception as exc:  # noqa: BLE001
                    status = f"ERR({type(exc).__name__})"
                print(f"      [{i:02d}] {cat:<11} {status:<6}  {tool}")
                await asyncio.sleep(0.2)


# ── POC A ─────────────────────────────────────────────────────────────────────
async def poc_a_local_stdio() -> None:
    print(HEAVY)
    print("POC A — Local stdio server  (npx server-everything via mcp-proxy)")
    print(HEAVY)
    LOCAL_OUT.mkdir(parents=True, exist_ok=True)
    run_dir = _next_run_dir(LOCAL_OUT)
    run_dir.mkdir(parents=True, exist_ok=True)
    _free_port(LOCAL_PROXY_PORT)
    _free_port(LOCAL_MITM_PORT)

    wire_log = run_dir / "wire.log"
    print(f"[1/3] Starting mcp-proxy on :{LOCAL_PROXY_PORT} (DEBUG → wire.log) ...")
    wire_fh = open(wire_log, "w", encoding="utf-8", errors="replace")
    proxy_proc = subprocess.Popen(
        ["mcp-proxy", "--log-level", "DEBUG", "--port", str(LOCAL_PROXY_PORT),
         "--", "npx", "@modelcontextprotocol/server-everything", "stdio"],
        stdout=subprocess.DEVNULL, stderr=wire_fh, env=os.environ.copy(),
    )
    if not _wait(LOCAL_PROXY_PORT, 60):
        print("ERROR: mcp-proxy did not start"); wire_fh.close(); proxy_proc.terminate(); return

    print(f"[2/3] Starting mitmdump on :{LOCAL_MITM_PORT} → :{LOCAL_PROXY_PORT} ...")
    capture = run_dir / "flows.jsonl"
    mitm_proc = _start_mitmdump(LOCAL_PROXY_PORT, LOCAL_MITM_PORT, capture)
    if not _wait(LOCAL_MITM_PORT, 60):
        print("ERROR: mitmdump did not start"); wire_fh.close(); proxy_proc.terminate(); mitm_proc.terminate(); return

    print(f"[3/3] Running {len(LOCAL_CALLS)} calls through http://localhost:{LOCAL_MITM_PORT}/mcp ...")
    try:
        await _run_calls(f"http://localhost:{LOCAL_MITM_PORT}/mcp", LOCAL_CALLS)
    finally:
        await asyncio.sleep(0.5)
        mitm_proc.terminate(); proxy_proc.terminate()
        mitm_proc.wait();      proxy_proc.wait()
        wire_fh.close()

    _clean_log(wire_log)
    write_report(run_dir, LOCAL_CALLS, capture, "Local stdio (npx server-everything)")
    write_wire_comparison(run_dir, capture, wire_log)


# ── POC B ─────────────────────────────────────────────────────────────────────
async def poc_b_calendar() -> None:
    print("\n" + HEAVY)
    print("POC B — Web-style service  (FastMCP calendar, no mcp-proxy)")
    print(HEAVY)
    CAL_OUT.mkdir(parents=True, exist_ok=True)
    run_dir = _next_run_dir(CAL_OUT)
    run_dir.mkdir(parents=True, exist_ok=True)
    _free_port(CAL_SERVER_PORT)
    _free_port(CAL_MITM_PORT)

    print(f"[1/3] Starting calendar server on :{CAL_SERVER_PORT} ...")
    cal_script = Path(__file__).parent.parent / "servers" / "mcp_calendar_server.py"
    cal_proc = subprocess.Popen(
        ["uv", "run", "python", str(cal_script)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(),
    )
    if not _wait(CAL_SERVER_PORT, 30):
        print("ERROR: calendar server did not start"); cal_proc.terminate(); return

    print(f"[2/3] Starting mitmdump on :{CAL_MITM_PORT} → :{CAL_SERVER_PORT} ...")
    capture = run_dir / "flows.jsonl"
    mitm_proc = _start_mitmdump(CAL_SERVER_PORT, CAL_MITM_PORT, capture)
    if not _wait(CAL_MITM_PORT, 60):
        print("ERROR: mitmdump did not start"); cal_proc.terminate(); mitm_proc.terminate(); return

    print(f"[3/3] Running {len(CAL_CALLS)} calls through http://localhost:{CAL_MITM_PORT}/mcp ...")
    try:
        await _run_calls(f"http://localhost:{CAL_MITM_PORT}/mcp", CAL_CALLS)
    finally:
        await asyncio.sleep(0.5)
        mitm_proc.terminate(); cal_proc.terminate()
        mitm_proc.wait();      cal_proc.wait()

    write_report(run_dir, CAL_CALLS, capture, "Web-style calendar (FastMCP)")


# ── main ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    await poc_a_local_stdio()
    await poc_b_calendar()
    print("\n" + HEAVY)
    print("Output folders:")
    print(f"  Local    : {LOCAL_OUT.resolve()}  (run subfolders)")
    print(f"  Calendar : {CAL_OUT.resolve()}  (run subfolders)")
    print(HEAVY)


if __name__ == "__main__":
    asyncio.run(main())
