"""Minimal MCP agent — no demo scaffolding, just real MCP.

This is what a real agent looks like stripped to its core.
Connect → Discover → Call tools → Done.

Run with: uv run python mcp_learning_lab/real_mcp_explorer/minimal_agent.py
"""

import asyncio
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Where the server is allowed to operate
SANDBOX_DIR = Path(__file__).resolve().parent / "sandbox"

# Path to npx
NPX_PATH = Path("C:/Program Files/nodejs/npx.cmd")


async def main() -> None:
    npx_cmd = str(NPX_PATH) if NPX_PATH.exists() else "npx"
    env = os.environ.copy()
    if NPX_PATH.exists():
        env["PATH"] = str(NPX_PATH.parent) + os.pathsep + env.get("PATH", "")

    server_params = StdioServerParameters(
        command=npx_cmd,
        args=["-y", "@modelcontextprotocol/server-filesystem", str(SANDBOX_DIR)],
        env=env,
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:

            # 1. Handshake
            result = await session.initialize()
            print(f"Connected to: {result.serverInfo.name} v{result.serverInfo.version}")
            print(f"Protocol: {result.protocolVersion}\n")

            # 2. Discover tools
            tools = (await session.list_tools()).tools
            print(f"Available tools ({len(tools)}):")
            for t in tools:
                print(f"  - {t.name}")
            print()

            # 3. Use tools — this is ALL an agent needs
            #    Just call_tool(name, args). That's it.

            # Read a file
            r = await session.call_tool("read_file", {"path": str(SANDBOX_DIR / "hello.txt")})
            print("--- read_file('hello.txt') ---")
            print(r.content[0].text)

            # List a directory
            r = await session.call_tool("list_directory", {"path": str(SANDBOX_DIR)})
            print("--- list_directory('sandbox/') ---")
            print(r.content[0].text)

            # Get file info
            r = await session.call_tool("get_file_info", {"path": str(SANDBOX_DIR / "notes.md")})
            print("\n--- get_file_info('notes.md') ---")
            print(r.content[0].text)

            # See the security boundary
            r = await session.call_tool("list_allowed_directories", {})
            print("\n--- list_allowed_directories() ---")
            print(r.content[0].text)

            # Try to escape — this will be denied
            r = await session.call_tool("read_file", {"path": "C:/Windows/System32/drivers/etc/hosts"})
            print("\n--- read_file('C:/Windows/...hosts') ---")
            if r.isError:
                print(f"DENIED: {r.content[0].text}")
            else:
                print(r.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
