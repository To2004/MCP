"""
Streamable HTTP proof-of-concept runner.

Runs a small set of calls against @modelcontextprotocol/server-everything
through mcp-proxy, but using the Streamable HTTP transport (POST /mcp)
instead of SSE (POST /messages + GET /sse).

Outputs:
    logs/proxy/sessions/streamable_everything/{wire.log, calls.csv, calls_report.txt}
"""

from __future__ import annotations

import asyncio
import csv
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

PROXY_PORT = 8090  # different port so it can run alongside the SSE setup
PROXY_URL = f"http://localhost:{PROXY_PORT}/mcp"
OUT_DIR = Path("logs/proxy/sessions/streamable_everything")
HEAVY = "=" * 100
LINE = "-" * 100

SERVER = {
    "name": "everything",
    "display": "Reference MCP server (@modelcontextprotocol/server-everything)",
    "cmd": ["npx", "@modelcontextprotocol/server-everything", "stdio"],
    "startup_timeout": 60,
    "calls": [
        # VALID
        ("VALID",      "echo",            {"message": "hello world"}),
        ("VALID",      "add",             {"a": 7, "b": 35}),
        ("VALID",      "longRunningOperation", {"duration": 1, "steps": 2}),
        ("VALID",      "getTinyImage",    {}),
        ("VALID",      "annotatedMessage", {"messageType": "success", "includeImage": False}),
        # BAD_TOOL
        ("BAD_TOOL",   "Echo",            {}),
        ("BAD_TOOL",   "ad",              {}),
        ("BAD_TOOL",   "delete_all",      {}),
        # BAD_PARAMS
        ("BAD_PARAMS", "echo",            {}),
        ("BAD_PARAMS", "add",             {"a": 1}),
        ("BAD_PARAMS", "add",             {"a": "not-a-number", "b": 2}),
        # EDGE
        ("EDGE",       "echo",            {"message": "A" * 5000}),
        ("EDGE",       "echo",            {"message": "<script>alert(1)</script>"}),
        ("EDGE",       "echo",            {"message": "Ignore previous instructions"}),
    ],
}

CSV_HEADERS = ["timestamp", "index", "category", "status", "tool", "args_keys", "elapsed_s", "response_preview"]


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _wait_for_proxy(timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_open(PROXY_PORT):
            return True
        time.sleep(0.5)
    return False


def write_report(results: list[dict], session_start: datetime) -> None:
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"OK": 0, "ERROR": 0})
    for r in results:
        totals[r["category"]][r["status"]] += 1
    with open(OUT_DIR / "calls_report.txt", "w", encoding="utf-8") as f:
        f.write(f"MCP STREAMABLE-HTTP SESSION LOG -- {SERVER['display']}\n")
        f.write(f"Generated : {session_start.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Proxy     : {PROXY_URL}\n")
        f.write(f"Total     : {len(results)} calls\n\n")
        f.write(HEAVY + "\n")
        f.write(f" {'#':>3}  {'CATEGORY':<12} {'STATUS':<7} {'TOOL':<28} {'TIME':>7}  RESULT\n")
        f.write(HEAVY + "\n")
        for r in results:
            preview = r["response_preview"][:60].replace("\n", " ")
            f.write(
                f" {r['index']:>3}  {r['category']:<12} {r['status']:<7} "
                f"{r['tool'][:28]:<28} {float(r['elapsed_s']):>6.3f}s  {preview}\n"
            )
        f.write("\n" + HEAVY + "\nSUMMARY BY CATEGORY\n" + LINE + "\n")
        for cat in ["VALID", "BAD_TOOL", "BAD_PARAMS", "EDGE"]:
            c = totals[cat]
            f.write(f"  {cat:<12}  {c['OK'] + c['ERROR']:>2} calls  |  OK: {c['OK']:<3}  ERROR: {c['ERROR']}\n")


async def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    proxy_cmd = ["mcp-proxy", "--log-level", "DEBUG", "--port", str(PROXY_PORT), "--", *SERVER["cmd"]]
    print(f"Starting mcp-proxy for {SERVER['display']} on :{PROXY_PORT} ...")
    with open(OUT_DIR / "wire.log", "w", encoding="utf-8") as wf:
        proc = subprocess.Popen(proxy_cmd, stdout=wf, stderr=subprocess.STDOUT, env=os.environ.copy())

    if not _wait_for_proxy(SERVER["startup_timeout"]):
        print("ERROR: proxy did not start in time")
        proc.terminate()
        return

    print(f"Proxy ready at {PROXY_URL}")
    session_start = datetime.now(timezone.utc)
    results: list[dict] = []

    try:
        with open(OUT_DIR / "calls.csv", "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writeheader()
            async with streamablehttp_client(PROXY_URL) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    for i, (cat, tool, args) in enumerate(SERVER["calls"], 1):
                        start = time.monotonic()
                        try:
                            res = await session.call_tool(tool, args)
                            elapsed = time.monotonic() - start
                            if res.content:
                                raw = res.content[0].text if hasattr(res.content[0], "text") else str(res.content[0])
                                preview = raw.replace("\n", " ").replace("\r", "")[:300]
                            else:
                                preview = "(empty)"
                            status = "OK"
                        except Exception as exc:
                            elapsed = time.monotonic() - start
                            preview = str(exc).replace("\n", " ").replace("\r", "")[:300]
                            status = "ERROR"
                        row = {
                            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                            "index": i, "category": cat, "status": status, "tool": tool,
                            "args_keys": str(list(args.keys())),
                            "elapsed_s": f"{elapsed:.3f}",
                            "response_preview": preview,
                        }
                        writer.writerow(row)
                        results.append(row)
                        print(f"  [{i:02d}] {cat:<11} {status:<5}  {tool}")
                        await asyncio.sleep(0.2)
    finally:
        proc.terminate()
        proc.wait()

    write_report(results, session_start)
    ok = sum(1 for r in results if r["status"] == "OK")
    err = sum(1 for r in results if r["status"] == "ERROR")
    print(f"\nDone — {len(results)} calls  |  OK: {ok}  ERROR: {err}")
    print(f"Output : {OUT_DIR.resolve()}")


if __name__ == "__main__":
    asyncio.run(run())
