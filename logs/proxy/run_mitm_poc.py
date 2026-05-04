"""
mitmproxy POC — capture all MCP traffic via an industry-standard MITM proxy.

Stack:
    runner ──→ mitmdump :9090 ──(reverse proxy)──→ mcp-proxy :8090 ──(stdio)──→ npx everything

mitmdump runs the addon mitm_capture.py which writes every request+response to
JSONL. This works regardless of the MCP transport (SSE or Streamable HTTP) —
mitmdump sees the raw HTTP bytes either way.
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

OUT_DIR = Path("logs/proxy/sessions/mitm_everything")
MCP_PROXY_PORT = 8090
MITM_PORT = 9090
CLIENT_URL = f"http://localhost:{MITM_PORT}/mcp"

CALLS = [
    ("VALID",      "echo",            {"message": "hello world"}),
    ("VALID",      "add",             {"a": 7, "b": 35}),
    ("VALID",      "longRunningOperation", {"duration": 1, "steps": 2}),
    ("VALID",      "annotatedMessage", {"messageType": "success", "includeImage": False}),
    ("BAD_TOOL",   "Echo",            {}),
    ("BAD_TOOL",   "delete_all",      {}),
    ("BAD_PARAMS", "echo",            {}),
    ("BAD_PARAMS", "add",             {"a": "not-a-number", "b": 2}),
    ("EDGE",       "echo",            {"message": "<script>alert(1)</script>"}),
    ("EDGE",       "echo",            {"message": "Ignore previous instructions"}),
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

    # 1) start mcp-proxy on the inner port
    mcp_proxy_log = OUT_DIR / "wire.log"
    print(f"[1/3] Starting mcp-proxy on :{MCP_PROXY_PORT} ...")
    with open(mcp_proxy_log, "w", encoding="utf-8") as wf:
        mcp_proc = subprocess.Popen(
            ["mcp-proxy", "--log-level", "DEBUG", "--port", str(MCP_PROXY_PORT),
             "--", "npx", "@modelcontextprotocol/server-everything", "stdio"],
            stdout=wf, stderr=subprocess.STDOUT, env=os.environ.copy(),
        )

    if not _wait(MCP_PROXY_PORT, 60):
        print("ERROR: mcp-proxy did not start")
        mcp_proc.terminate()
        return
    print(f"      mcp-proxy ready, log → {mcp_proxy_log}")

    # 2) start mitmdump in front of it
    mitm_log = OUT_DIR / "mitmdump.log"
    addon_path = Path(__file__).parent / "mitm_capture.py"
    capture_path = OUT_DIR / "captured.jsonl"
    env = {**os.environ, "MITM_OUT": str(capture_path)}

    print(f"[2/3] Starting mitmdump on :{MITM_PORT} → :{MCP_PROXY_PORT} ...")
    with open(mitm_log, "w", encoding="utf-8") as mf:
        mitm_proc = subprocess.Popen(
            ["uvx", "--from", "mitmproxy", "mitmdump",
             "--mode", f"reverse:http://localhost:{MCP_PROXY_PORT}",
             "--listen-port", str(MITM_PORT),
             "-s", str(addon_path),
             "--set", "stream_large_bodies=10m"],
            stdout=mf, stderr=subprocess.STDOUT, env=env,
        )

    if not _wait(MITM_PORT, 60):
        print("ERROR: mitmdump did not start (see mitmdump.log)")
        mcp_proc.terminate()
        mitm_proc.terminate()
        return
    print(f"      mitmdump ready, capture → {capture_path}")

    # 3) run client through mitmdump
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
        # let mitmdump flush
        await asyncio.sleep(0.5)
        mitm_proc.terminate()
        mcp_proc.terminate()
        mitm_proc.wait()
        mcp_proc.wait()

    # summary
    if capture_path.exists():
        n = sum(1 for _ in capture_path.open(encoding="utf-8"))
        size_kb = capture_path.stat().st_size // 1024
        print(f"\nDone — {n} HTTP flows captured  ({size_kb} KB)")
        print(f"Output : {OUT_DIR.resolve()}")
    else:
        print("\nWARNING: captured.jsonl not produced — see mitmdump.log")


if __name__ == "__main__":
    asyncio.run(run())
