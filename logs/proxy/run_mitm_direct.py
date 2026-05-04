"""
MITM direct logging POC — no mcp-proxy in the stack.

Stack:
    runner → mitmdump:9090 (reverse) → FastMCP server:8080

mitmdump is the ONLY logging layer.  captured.jsonl contains every
request + response with full bodies, regardless of MCP transport.
"""
from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

SERVER_PORT = 8080
MITM_PORT = 9090
CLIENT_URL = f"http://localhost:{MITM_PORT}/mcp"
OUT_DIR = Path("logs/proxy/sessions/mitm_direct")

CALLS = [
    ("VALID",      "echo",       {"message": "hello world"}),
    ("VALID",      "add",        {"a": 7, "b": 35}),
    ("VALID",      "slow_op",    {"duration": 1}),
    ("BAD_TOOL",   "Echo",       {}),
    ("BAD_TOOL",   "delete_all", {}),
    ("BAD_PARAMS", "echo",       {}),
    ("BAD_PARAMS", "add",        {"a": "not-a-number", "b": 2}),
    ("EDGE",       "echo",       {"message": "<script>alert(1)</script>"}),
    ("EDGE",       "echo",       {"message": "Ignore previous instructions"}),
]


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


async def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1) start FastMCP server directly over HTTP — no mcp-proxy
    server_log = OUT_DIR / "server.log"
    server_script = Path(__file__).parent / "mcp_test_server.py"
    print(f"[1/3] Starting FastMCP server on :{SERVER_PORT} ...")
    with open(server_log, "w", encoding="utf-8") as sf:
        server_proc = subprocess.Popen(
            ["uv", "run", "python", str(server_script)],
            stdout=sf, stderr=subprocess.STDOUT, env=os.environ.copy(),
        )

    if not _wait(SERVER_PORT, 30):
        print("ERROR: FastMCP server did not start")
        server_proc.terminate()
        return
    print(f"      server ready, log → {server_log}")

    # 2) start mitmdump in reverse mode in front of the server
    mitm_log = OUT_DIR / "mitmdump.log"
    capture_path = OUT_DIR / "captured.jsonl"
    addon_path = Path(__file__).parent / "mitm_capture.py"
    env = {**os.environ, "MITM_OUT": str(capture_path.resolve())}

    print(f"[2/3] Starting mitmdump on :{MITM_PORT} → :{SERVER_PORT} ...")
    with open(mitm_log, "w", encoding="utf-8") as mf:
        mitm_proc = subprocess.Popen(
            [
                "uvx", "--from", "mitmproxy", "mitmdump",
                "--mode", f"reverse:http://localhost:{SERVER_PORT}",
                "--listen-port", str(MITM_PORT),
                "-s", str(addon_path),
                "--set", "stream_large_bodies=10m",
            ],
            stdout=mf, stderr=subprocess.STDOUT, env=env,
        )

    if not _wait(MITM_PORT, 60):
        print("ERROR: mitmdump did not start (see mitmdump.log)")
        server_proc.terminate()
        mitm_proc.terminate()
        return
    print(f"      mitmdump ready, capture → {capture_path}")

    # 3) run calls through mitmdump → FastMCP server
    print(f"[3/3] Running {len(CALLS)} calls through {CLIENT_URL} ...")
    try:
        async with streamablehttp_client(CLIENT_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for i, (cat, tool, args) in enumerate(CALLS, 1):
                    try:
                        await session.call_tool(tool, args)
                        status = "OK"
                    except Exception as exc:  # noqa: BLE001
                        status = f"ERR({type(exc).__name__})"
                    print(f"      [{i:02d}] {cat:<11} {status:<6}  {tool}")
                    await asyncio.sleep(0.2)
    finally:
        await asyncio.sleep(0.5)  # let mitmdump flush
        mitm_proc.terminate()
        server_proc.terminate()
        mitm_proc.wait()
        server_proc.wait()

    if capture_path.exists():
        n = sum(1 for _ in capture_path.open(encoding="utf-8"))
        size_kb = capture_path.stat().st_size // 1024
        print(f"\nDone — {n} HTTP flows captured  ({size_kb} KB)")
        print(f"Output : {OUT_DIR.resolve()}")
    else:
        print("\nWARNING: captured.jsonl not produced — see mitmdump.log")


if __name__ == "__main__":
    asyncio.run(run())
