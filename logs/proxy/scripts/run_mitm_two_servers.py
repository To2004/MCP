"""
Side-by-side MITM logging POC.

POC A — Local stdio server (npx server-everything via mcp-proxy):
    runner → mitmdump:9092 → mcp-proxy:8092 → npx everything (stdio)

POC B — Web-style service (FastMCP calendar server, no mcp-proxy):
    runner → mitmdump:9093 → calendar server:8093

Both produce captured.jsonl → calls.csv + calls_report.txt.
The logging layer (mitm_capture.py) does not change between the two cases.
"""
from __future__ import annotations

import asyncio
import csv
import json
import os
import socket
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

ADDON  = Path(__file__).parent / "mitm_capture.py"
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
    ("VALID",      "list_events",  {"date": "2026-05-05"}),
    ("VALID",      "create_event", {"title": "Thesis defense", "date": "2026-06-01", "time": "10:00"}),
    ("VALID",      "list_events",  {"date": "2026-06-01"}),
    ("VALID",      "delete_event", {"event_id": "evt_001"}),
    ("BAD_TOOL",   "get_email",    {}),
    ("BAD_PARAMS", "create_event", {"title": "Missing fields"}),
    ("EDGE",       "create_event", {"title": "<script>alert(1)</script>", "date": "2026-05-05", "time": "00:00"}),
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


def _start_mitmdump(upstream_port: int, listen_port: int, capture_path: Path, log_path: Path) -> subprocess.Popen:
    env = {**os.environ, "MITM_OUT": str(capture_path.resolve())}
    lf = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        ["uvx", "--from", "mitmproxy", "mitmdump",
         "--mode", f"reverse:http://localhost:{upstream_port}",
         "--listen-port", str(listen_port),
         "-s", str(ADDON),
         "--set", "stream_large_bodies=10m"],
        stdout=lf, stderr=subprocess.STDOUT, env=env,
    )
    lf.close()
    return proc


def _parse_result(resp: dict) -> tuple[str, int, str]:
    """Return (result_text, content_count, error_code)."""
    error_code = ""
    # top-level JSON-RPC error
    if "error" in resp:
        return str(resp["error"].get("message", resp["error"])), 0, str(resp["error"].get("code", ""))
    result = resp.get("result", {})
    if not isinstance(result, dict):
        return str(result), 0, ""
    # MCP isError flag inside result
    if result.get("isError"):
        content = result.get("content", [])
        text = " | ".join(c.get("text", "") for c in content if c.get("type") == "text")
        return text, len(content), ""
    content = result.get("content", [])
    text = " | ".join(c.get("text", "") for c in content if c.get("type") == "text")
    return text, len(content), error_code


def write_report(out_dir: Path, calls: list[tuple], capture_path: Path, label: str) -> None:
    flows = [json.loads(l) for l in capture_path.read_text(encoding="utf-8").splitlines()]

    # extract only tools/call flows in order, also grab session_id from headers
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
        session_id  = flow["req_headers"].get("mcp-session-id", "")
        jsonrpc_id  = str(req.get("id", ""))
        is_error    = bool(error_code) or any(
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
            "result":        result_str[:200],
        })

    # calls.csv
    csv_path = out_dir / "calls.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    # calls_report.txt
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"OK": 0, "ERROR": 0})
    for r in rows:
        totals[r["category"]][r["status"]] += 1

    report_path = out_dir / "calls_report.txt"
    session_ids = sorted({r["session_id"] for r in rows if r["session_id"]})
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"MCP MITM SESSION LOG -- {label}\n")
        f.write(f"Generated  : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Total      : {len(rows)} tool calls\n")
        f.write(f"Session IDs: {', '.join(session_ids) if session_ids else 'n/a'}\n\n")
        f.write(HEAVY + "\n")
        f.write(f" {'#':>3}  {'RPC':>4}  {'CATEGORY':<12} {'STATUS':<7} {'HTTP':>4}  "
                f"{'TOOL':<32} {'TIME':>7}  {'CNT':>3}  RESULT\n")
        f.write(HEAVY + "\n")
        for r in rows:
            preview = r["result"][:40].replace("\n", " ")
            ec = f"[{r['error_code']}]" if r["error_code"] else ""
            f.write(
                f" {r['index']:>3}  {r['jsonrpc_id']:>4}  {r['category']:<12} {r['status']:<7} "
                f"{r['http_status']:>4}  {r['tool'][:32]:<32} {float(r['elapsed_s']):>6.3f}s  "
                f"{r['content_count']:>3}  {preview} {ec}\n"
            )
        f.write("\n" + HEAVY + "\nSUMMARY BY CATEGORY\n" + LINE + "\n")
        for cat in ["VALID", "BAD_TOOL", "BAD_PARAMS", "EDGE"]:
            c = totals[cat]
            total = c["OK"] + c["ERROR"]
            if total:
                f.write(f"  {cat:<12}  {total:>2} calls  |  OK: {c['OK']:<3}  ERROR: {c['ERROR']}\n")

    print(f"\n  calls.csv      → {csv_path}")
    print(f"  calls_report   → {report_path}")


async def _run_calls(url: str, calls: list[tuple]) -> None:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
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

    print(f"[1/3] Starting mcp-proxy on :{LOCAL_PROXY_PORT} ...")
    with open(LOCAL_OUT / "wire.log", "w", encoding="utf-8") as wf:
        proxy_proc = subprocess.Popen(
            ["mcp-proxy", "--log-level", "DEBUG", "--port", str(LOCAL_PROXY_PORT),
             "--", "npx", "@modelcontextprotocol/server-everything", "stdio"],
            stdout=wf, stderr=subprocess.STDOUT, env=os.environ.copy(),
        )
    if not _wait(LOCAL_PROXY_PORT, 60):
        print("ERROR: mcp-proxy did not start"); proxy_proc.terminate(); return

    print(f"[2/3] Starting mitmdump on :{LOCAL_MITM_PORT} → :{LOCAL_PROXY_PORT} ...")
    capture = LOCAL_OUT / "captured.jsonl"
    mitm_proc = _start_mitmdump(LOCAL_PROXY_PORT, LOCAL_MITM_PORT, capture, LOCAL_OUT / "mitmdump.log")
    if not _wait(LOCAL_MITM_PORT, 60):
        print("ERROR: mitmdump did not start"); proxy_proc.terminate(); mitm_proc.terminate(); return

    print(f"[3/3] Running {len(LOCAL_CALLS)} calls through http://localhost:{LOCAL_MITM_PORT}/mcp ...")
    try:
        await _run_calls(f"http://localhost:{LOCAL_MITM_PORT}/mcp", LOCAL_CALLS)
    finally:
        await asyncio.sleep(0.5)
        mitm_proc.terminate(); proxy_proc.terminate()
        mitm_proc.wait();      proxy_proc.wait()

    write_report(LOCAL_OUT, LOCAL_CALLS, capture, "Local stdio (npx server-everything)")


# ── POC B ─────────────────────────────────────────────────────────────────────
async def poc_b_calendar() -> None:
    print("\n" + HEAVY)
    print("POC B — Web-style service  (FastMCP calendar, no mcp-proxy)")
    print(HEAVY)
    CAL_OUT.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] Starting calendar server on :{CAL_SERVER_PORT} ...")
    cal_script = Path(__file__).parent / "mcp_calendar_server.py"
    with open(CAL_OUT / "server.log", "w", encoding="utf-8") as sf:
        cal_proc = subprocess.Popen(
            ["uv", "run", "python", str(cal_script)],
            stdout=sf, stderr=subprocess.STDOUT, env=os.environ.copy(),
        )
    if not _wait(CAL_SERVER_PORT, 30):
        print("ERROR: calendar server did not start"); cal_proc.terminate(); return

    print(f"[2/3] Starting mitmdump on :{CAL_MITM_PORT} → :{CAL_SERVER_PORT} ...")
    capture = CAL_OUT / "captured.jsonl"
    mitm_proc = _start_mitmdump(CAL_SERVER_PORT, CAL_MITM_PORT, capture, CAL_OUT / "mitmdump.log")
    if not _wait(CAL_MITM_PORT, 60):
        print("ERROR: mitmdump did not start"); cal_proc.terminate(); mitm_proc.terminate(); return

    print(f"[3/3] Running {len(CAL_CALLS)} calls through http://localhost:{CAL_MITM_PORT}/mcp ...")
    try:
        await _run_calls(f"http://localhost:{CAL_MITM_PORT}/mcp", CAL_CALLS)
    finally:
        await asyncio.sleep(0.5)
        mitm_proc.terminate(); cal_proc.terminate()
        mitm_proc.wait();      cal_proc.wait()

    write_report(CAL_OUT, CAL_CALLS, capture, "Web-style calendar (FastMCP)")


# ── main ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    await poc_a_local_stdio()
    await poc_b_calendar()
    print("\n" + HEAVY)
    print("Output folders:")
    print(f"  Local    : {LOCAL_OUT.resolve()}")
    print(f"  Calendar : {CAL_OUT.resolve()}")
    print(HEAVY)


if __name__ == "__main__":
    asyncio.run(main())
