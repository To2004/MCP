# MCP Learning Lab

A hands-on learning exercise to understand how an AI agent connects to an MCP
(Model Context Protocol) server. This is **not** part of the main project — it
exists purely to make the MCP protocol tangible.

## What's Here

| File | Role | Description |
|------|------|-------------|
| `filesystem_server.py` | **MCP Server** | Real server that reads files, lists directories, gets file info |
| `agent.py` | **MCP Agent/Client** | Connects to the server, discovers tools, calls them |

## How to Run

```bash
# From the project root
uv run python mcp_learning_lab/agent.py
```

That's it. The agent spawns the server automatically as a child process.

## What You'll See

The agent walks through the full MCP connection flow:

1. **Connection** — spawns the server via stdio transport
2. **Handshake** — MCP `initialize` exchange (server name, version, capabilities)
3. **Tool Discovery** — `list_tools` returns every tool with its JSON Schema
4. **Tool Calls** — calls each tool with real file paths from this project
5. **Cleanup** — agent disconnects, server process exits

## Key Concepts

### stdio Transport
The server runs as a child process. Communication happens over stdin/stdout
using JSON-RPC 2.0 messages. This is why the server **never uses `print()`** —
stdout is reserved for protocol messages.

### Tool Discovery
When an agent calls `list_tools`, it receives each tool's:
- **Name** — how to call it
- **Description** — what it does (human-readable)
- **Input Schema** — JSON Schema describing required arguments and their types

This schema is auto-generated from Python type hints and docstrings by FastMCP.

### Tool Invocation
The agent sends a `tools/call` request with the tool name and arguments as JSON.
The server executes the function and returns the result as content blocks.

### Security
The filesystem server restricts all paths to the project root directory.
Attempting to access files outside the project raises an error.
