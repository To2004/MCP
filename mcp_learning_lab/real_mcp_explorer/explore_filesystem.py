"""Real MCP Explorer --connect to the official filesystem MCP server.

This agent connects to @modelcontextprotocol/server-filesystem (the real,
production-grade server maintained by Anthropic) and walks through every
capability step by step so you can see exactly what an AI agent experiences.

The explorer runs 6 phases:
  1. CONNECT    --spawn the server, perform the MCP handshake
  2. DISCOVER   --list every tool the server exposes + full JSON schemas
  3. READ       --read real files through MCP
  4. WRITE      --create and edit files through MCP
  5. SEARCH     --search file contents and directory trees
  6. BOUNDARIES --test what happens when you go outside allowed directories

Run with:
    uv run python mcp_learning_lab/real_mcp_explorer/explore_filesystem.py
"""

import asyncio
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# The sandbox directory that the MCP server is allowed to access
SANDBOX_DIR = Path(__file__).resolve().parent / "sandbox"

# npx path --needed because new installs may not be in shell PATH yet
NPX_PATH = Path("C:/Program Files/nodejs/npx.cmd")

SEPARATOR = "=" * 60
SUB_SEPARATOR = "-" * 40

# Colors for terminal output (ANSI codes)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def header(title: str) -> None:
    """Print a major section header."""
    print(f"\n{CYAN}{SEPARATOR}{RESET}")
    print(f"  {BOLD}PHASE: {title}{RESET}")
    print(f"{CYAN}{SEPARATOR}{RESET}")


def step(description: str) -> None:
    """Print a step label."""
    print(f"\n  {YELLOW}>>> {description}{RESET}")


def success(message: str) -> None:
    """Print a success message."""
    print(f"  {GREEN}[OK] {message}{RESET}")


def fail(message: str) -> None:
    """Print a failure/denied message."""
    print(f"  {RED}[DENIED] {message}{RESET}")


def info(message: str) -> None:
    """Print an informational message."""
    print(f"  {message}")


def tool_result(result: object) -> None:
    """Print the content blocks from a tool call result."""
    for content in result.content:
        if hasattr(content, "text"):
            for line in content.text.splitlines():
                print(f"    {line}")
        elif hasattr(content, "type") and content.type == "error":
            fail(f"Server error: {content.text}")


# ---------------------------------------------------------------------------
# Phase functions
# ---------------------------------------------------------------------------

async def phase_connect(session: ClientSession) -> object:
    """Phase 1: Perform the MCP handshake and show server info."""
    header("1 --CONNECT (MCP Handshake)")

    step("Sending initialize request to server...")
    info("This is the first message in the MCP protocol.")
    info("The client tells the server its name and what it supports.")
    info("The server responds with its own name, version, and capabilities.")

    init_result = await session.initialize()

    success("Handshake complete!")
    print()
    info(f"  Server name:      {init_result.serverInfo.name}")
    info(f"  Server version:   {init_result.serverInfo.version}")
    info(f"  Protocol version: {init_result.protocolVersion}")
    print()

    capabilities = init_result.capabilities.model_dump(exclude_none=True)
    info("  Server capabilities (what this server can do):")
    for cap_name, cap_value in capabilities.items():
        info(f"    • {cap_name}: {cap_value}")

    print()
    info(f"  Allowed directory: {SANDBOX_DIR}")
    info("  The server can ONLY access files inside this directory.")
    info("  Anything outside will be denied --this is MCP's security model.")

    return init_result


async def phase_discover(session: ClientSession) -> list:
    """Phase 2: List all tools and their schemas."""
    header("2 --DISCOVER (Tool Discovery)")

    step("Calling list_tools() --this is what an agent does first")
    info("The agent asks: 'What tools do you have? What arguments do they take?'")
    info("The server returns a list of tools with JSON Schema for each one.")

    tools_response = await session.list_tools()
    tools = tools_response.tools

    success(f"Server exposes {len(tools)} tools:")
    print()

    for i, t in enumerate(tools, start=1):
        print(f"  {BOLD}[{i}] {t.name}{RESET}")
        if t.description:
            # Show just the first line of description
            first_line = t.description.strip().splitlines()[0]
            print(f"      {first_line}")

        # Show the schema properties
        props = t.inputSchema.get("properties", {})
        required = t.inputSchema.get("required", [])
        if props:
            print("      Parameters:")
            for param_name, param_info in props.items():
                req_marker = " (required)" if param_name in required else " (optional)"
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                desc_part = f" --{param_desc}" if param_desc else ""
                print(f"        • {param_name}: {param_type}{req_marker}{desc_part}")
        print()

    info("This is EXACTLY what Claude, Cursor, or any AI agent sees.")
    info("The agent uses the schema to know what arguments to pass.")

    return tools


async def phase_read(session: ClientSession) -> None:
    """Phase 3: Demonstrate read operations."""
    header("3 --READ (What you CAN read)")

    # --- read_file ---
    step("read_file --reading sandbox/hello.txt")
    info("The agent sends: tools/call with name='read_file' and path argument")
    result = await session.call_tool("read_file", {"path": str(SANDBOX_DIR / "hello.txt")})
    success("File contents returned:")
    tool_result(result)

    # --- read_multiple_files ---
    step("read_multiple_files --reading two files at once")
    info("This tool takes a list of paths and returns all contents in one call.")
    info("More efficient than calling read_file multiple times.")
    result = await session.call_tool("read_multiple_files", {
        "paths": [
            str(SANDBOX_DIR / "hello.txt"),
            str(SANDBOX_DIR / "notes.md"),
        ]
    })
    success("Multiple files returned:")
    tool_result(result)

    # --- list_directory ---
    step("list_directory --listing sandbox/")
    result = await session.call_tool("list_directory", {"path": str(SANDBOX_DIR)})
    success("Directory contents:")
    tool_result(result)

    step("list_directory --listing sandbox/data/ (subdirectory)")
    result = await session.call_tool("list_directory", {"path": str(SANDBOX_DIR / "data")})
    success("Subdirectory contents:")
    tool_result(result)

    # --- get_file_info ---
    step("get_file_info --metadata for hello.txt")
    info("Returns size, timestamps, permissions --not file contents.")
    result = await session.call_tool("get_file_info", {"path": str(SANDBOX_DIR / "hello.txt")})
    success("File metadata:")
    tool_result(result)


async def phase_write(session: ClientSession) -> None:
    """Phase 4: Demonstrate write operations."""
    header("4 --WRITE (Creating and editing files)")

    # --- write_file ---
    step("write_file --creating a NEW file through MCP")
    info("The agent can ask the server to create files inside the allowed directory.")
    new_file = str(SANDBOX_DIR / "agent_created.txt")
    result = await session.call_tool("write_file", {
        "path": new_file,
        "content": "This file was created by an MCP agent!\nTimestamp: live demo\n",
    })
    success("File created:")
    tool_result(result)

    step("Verifying --reading back the file we just created")
    result = await session.call_tool("read_file", {"path": new_file})
    success("Contents of agent_created.txt:")
    tool_result(result)

    # --- edit_file ---
    step("edit_file --surgical edit on an existing file")
    info("This doesn't overwrite the whole file --it finds and replaces text.")
    info("Similar to find-and-replace in an editor.")
    result = await session.call_tool("edit_file", {
        "path": str(SANDBOX_DIR / "hello.txt"),
        "edits": [
            {
                "oldText": "This file was here before the agent connected.",
                "newText": "This file was here before the agent connected.\n[EDIT] The agent modified this line via MCP edit_file tool.",
            }
        ],
    })
    success("File edited:")
    tool_result(result)

    step("Verifying the edit --reading hello.txt again")
    result = await session.call_tool("read_file", {"path": str(SANDBOX_DIR / "hello.txt")})
    success("Updated contents:")
    tool_result(result)

    # --- create_directory ---
    step("create_directory --creating a new subdirectory")
    new_dir = str(SANDBOX_DIR / "agent_output")
    result = await session.call_tool("create_directory", {"path": new_dir})
    success("Directory created:")
    tool_result(result)

    # --- move_file ---
    step("move_file --moving a file to the new directory")
    result = await session.call_tool("move_file", {
        "source": new_file,
        "destination": str(SANDBOX_DIR / "agent_output" / "agent_created.txt"),
    })
    success("File moved:")
    tool_result(result)

    step("Verifying --listing agent_output/")
    result = await session.call_tool("list_directory", {
        "path": str(SANDBOX_DIR / "agent_output"),
    })
    success("Directory contents after move:")
    tool_result(result)


async def phase_search(session: ClientSession) -> None:
    """Phase 5: Demonstrate search operations."""
    header("5 --SEARCH (Finding content across files)")

    # --- search_files ---
    step("search_files --searching for 'MCP' across all files")
    info("This does a recursive regex search through the allowed directory.")
    info("Like grep/ripgrep but through the MCP protocol.")
    result = await session.call_tool("search_files", {
        "path": str(SANDBOX_DIR),
        "pattern": "MCP",
    })
    success("Search results for 'MCP':")
    tool_result(result)

    step("search_files --searching for 'critical' in CSV data")
    result = await session.call_tool("search_files", {
        "path": str(SANDBOX_DIR),
        "pattern": "critical",
    })
    success("Search results for 'critical':")
    tool_result(result)

    # --- list_allowed_directories ---
    step("list_allowed_directories --what CAN this server access?")
    info("This is the security boundary. The server declares exactly which")
    info("directories it's allowed to touch. Everything else is off-limits.")
    result = await session.call_tool("list_allowed_directories", {})
    success("Allowed directories:")
    tool_result(result)


async def phase_boundaries(session: ClientSession) -> None:
    """Phase 6: Test security boundaries --what gets DENIED."""
    header("6 --BOUNDARIES (What you CANNOT do)")

    info("The server was started with access to ONLY the sandbox/ directory.")
    info("Let's see what happens when we try to escape that boundary.\n")

    # --- Try to read outside sandbox ---
    step("Trying to read C:/Windows/System32/drivers/etc/hosts")
    info("This is outside the allowed directory --should be DENIED.")
    try:
        result = await session.call_tool("read_file", {
            "path": "C:/Windows/System32/drivers/etc/hosts",
        })
        if result.isError:
            fail("DENIED --server refused to read outside allowed directory")
            tool_result(result)
        else:
            fail("Unexpectedly succeeded --this should have been denied!")
            tool_result(result)
    except Exception as exc:
        fail(f"DENIED --{exc}")

    # --- Try to read parent directory ---
    step("Trying to read ../../pyproject.toml (path traversal)")
    info("Even relative paths that escape the sandbox should be blocked.")
    try:
        result = await session.call_tool("read_file", {
            "path": str(SANDBOX_DIR / ".." / ".." / "pyproject.toml"),
        })
        if result.isError:
            fail("DENIED --path traversal blocked")
            tool_result(result)
        else:
            info("Server resolved the path --check if it was actually allowed:")
            tool_result(result)
    except Exception as exc:
        fail(f"DENIED --{exc}")

    # --- Try to write outside sandbox ---
    step("Trying to write to C:/temp_mcp_test.txt")
    info("Write access outside the sandbox should be denied.")
    try:
        result = await session.call_tool("write_file", {
            "path": "C:/temp_mcp_test.txt",
            "content": "This should not be created",
        })
        if result.isError:
            fail("DENIED --cannot write outside allowed directory")
            tool_result(result)
        else:
            fail("Unexpectedly succeeded --this should have been denied!")
    except Exception as exc:
        fail(f"DENIED --{exc}")

    # --- Try to list root directory ---
    step("Trying to list C:/ (root directory)")
    try:
        result = await session.call_tool("list_directory", {"path": "C:/"})
        if result.isError:
            fail("DENIED --cannot list directories outside sandbox")
            tool_result(result)
        else:
            fail("Unexpectedly succeeded!")
    except Exception as exc:
        fail(f"DENIED --{exc}")

    print()
    info(f"{BOLD}TAKEAWAY:{RESET} The MCP server enforces a strict security boundary.")
    info("An agent can only touch files in directories the server was configured for.")
    info("This is how MCP prevents agents from accessing sensitive system files.")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary() -> None:
    """Print a final summary of what was demonstrated."""
    header("SUMMARY --What You Learned")

    print(f"""
  {BOLD}What an agent CAN do (inside allowed directory):{RESET}
    {GREEN}[+]{RESET} read_file          -- Read any file's contents
    {GREEN}[+]{RESET} read_multiple_files -- Read several files in one call
    {GREEN}[+]{RESET} write_file         -- Create new files or overwrite existing
    {GREEN}[+]{RESET} edit_file          -- Find-and-replace edits (surgical changes)
    {GREEN}[+]{RESET} create_directory   -- Create new directories
    {GREEN}[+]{RESET} list_directory     -- List directory contents
    {GREEN}[+]{RESET} move_file          -- Move or rename files
    {GREEN}[+]{RESET} search_files       -- Regex search across files
    {GREEN}[+]{RESET} get_file_info      -- Get file metadata (size, timestamps)
    {GREEN}[+]{RESET} list_allowed_dirs  -- See what directories are allowed

  {BOLD}What an agent CANNOT do:{RESET}
    {RED}[-]{RESET} Read files outside the allowed directory
    {RED}[-]{RESET} Write files outside the allowed directory
    {RED}[-]{RESET} Use path traversal (../../) to escape the sandbox
    {RED}[-]{RESET} List directories outside the allowed area
    {RED}[-]{RESET} Execute shell commands (no tool for that)
    {RED}[-]{RESET} Access network resources (no tool for that)
    {RED}[-]{RESET} Install packages or modify system state

  {BOLD}The MCP security model:{RESET}
    The server decides what tools exist and what directories are allowed.
    The agent has ZERO control over this -- it can only use what's offered.
    This is why MCP is safer than giving an agent raw shell access.
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run_explorer() -> None:
    """Run the full MCP exploration sequence."""
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"  {BOLD}REAL MCP EXPLORER{RESET}")
    print("  Connecting to: @modelcontextprotocol/server-filesystem")
    print(f"  Sandbox: {SANDBOX_DIR}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    # Determine npx command and ensure Node.js is in PATH for the subprocess
    npx_cmd = str(NPX_PATH) if NPX_PATH.exists() else "npx"
    nodejs_dir = str(NPX_PATH.parent) if NPX_PATH.exists() else ""

    env = os.environ.copy()
    if nodejs_dir:
        env["PATH"] = nodejs_dir + os.pathsep + env.get("PATH", "")

    server_params = StdioServerParameters(
        command=npx_cmd,
        args=["-y", "@modelcontextprotocol/server-filesystem", str(SANDBOX_DIR)],
        env=env,
    )

    step("Spawning official MCP filesystem server via npx...")
    info(f"Command: npx -y @modelcontextprotocol/server-filesystem {SANDBOX_DIR}")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await phase_connect(session)
            await phase_discover(session)
            await phase_read(session)
            await phase_write(session)
            await phase_search(session)
            await phase_boundaries(session)

    print_summary()


if __name__ == "__main__":
    asyncio.run(run_explorer())
