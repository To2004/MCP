"""MCP Agent — connects to the filesystem server and explores it.

This script shows exactly what an AI agent sees when connecting to an MCP server:
1. Spawn the server process (stdio transport)
2. Perform the MCP handshake (initialize)
3. Discover available tools (list_tools) with their JSON schemas
4. Call each tool with real arguments
5. Display results

Run with: uv run python mcp_learning_lab/agent.py
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVER_SCRIPT = Path(__file__).resolve().parent / "filesystem_server.py"

# Sample arguments for each tool — uses real files from this project
TOOL_TEST_ARGS: dict[str, dict[str, str]] = {
    "read_file": {"path": "pyproject.toml"},
    "list_directory": {"path": "src/mcp_security"},
    "get_file_info": {"path": "README.md"},
}

SEPARATOR = "=" * 50


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def print_tool_schema(index: int, name: str, description: str | None, schema: dict) -> None:
    """Print a tool's details in a readable format."""
    print(f"\n  [{index}] {name}")
    if description:
        print(f"      Description: {description}")
    print("      Input Schema:")
    for line in json.dumps(schema, indent=4).splitlines():
        print(f"        {line}")


# ---------------------------------------------------------------------------
# Agent logic
# ---------------------------------------------------------------------------

async def run_agent() -> None:
    """Connect to the MCP filesystem server and explore its capabilities."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT)],
    )

    print_header("MCP CONNECTION")
    print(f"  Spawning server: {SERVER_SCRIPT.name}")
    print("  Transport: stdio (JSON-RPC over stdin/stdout)")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Step 1: Handshake
            init_result = await session.initialize()
            print("\n  Handshake complete!")
            print(f"  Server: {init_result.serverInfo.name}")
            if init_result.serverInfo.version:
                print(f"  Version: {init_result.serverInfo.version}")
            print(f"  Protocol: {init_result.protocolVersion}")
            print(f"  Capabilities: {list(init_result.capabilities.model_dump(exclude_none=True))}")

            # Step 2: Discover tools
            print_header("TOOL DISCOVERY")
            tools_response = await session.list_tools()
            tools = tools_response.tools
            print(f"  Found {len(tools)} tool(s):")

            for i, tool in enumerate(tools, start=1):
                print_tool_schema(
                    index=i,
                    name=tool.name,
                    description=tool.description,
                    schema=tool.inputSchema,
                )

            # Step 3: Call each tool
            print_header("TOOL CALLS")

            for tool in tools:
                args = TOOL_TEST_ARGS.get(tool.name, {})
                args_display = ", ".join(f'{k}="{v}"' for k, v in args.items())

                print(f"\n  Calling {tool.name}({args_display})...")
                print(f"  {'-' * 40}")

                try:
                    result = await session.call_tool(tool.name, arguments=args)
                    for content in result.content:
                        if hasattr(content, "text"):
                            # Indent the result for readability
                            for line in content.text.splitlines():
                                print(f"  {line}")
                except Exception as exc:
                    print(f"  ERROR: {exc}")

            print_header("DONE")
            print("  Agent disconnected. Server process will be cleaned up.\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(run_agent())
