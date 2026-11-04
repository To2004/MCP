"""
Minimal MCPServer (mcp SDK 2.x) — runs natively over Streamable HTTP on :8080.
No mcp-proxy needed. Exposes the same tools used in the MITM POC runs.
"""
from __future__ import annotations

import time

from mcp.server.mcpserver import MCPServer

PORT = 8080

mcp = MCPServer("test-server")


@mcp.tool()
def echo(message: str) -> str:
    """Echo the message back."""
    return message


@mcp.tool()
def add(a: int, b: int) -> int:
    """Return a + b."""
    return a + b


@mcp.tool()
def slow_op(duration: int = 2) -> str:
    """Sleep for duration seconds then return done."""
    time.sleep(duration)
    return f"done after {duration}s"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=PORT)
