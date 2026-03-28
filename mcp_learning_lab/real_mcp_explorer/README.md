# Real MCP Explorer

Connect to the **official** `@modelcontextprotocol/server-filesystem` maintained
by Anthropic — the same server used by Claude Desktop, Cursor, and other AI tools
in production.

## Prerequisites

- Node.js installed (`node --version` should work)
- `uv sync` has been run

## How to Run

```bash
# From the project root
uv run python mcp_learning_lab/real_mcp_explorer/explore_filesystem.py
```

The agent spawns the official server via `npx` and walks through 6 phases.

## The 6 Phases

| Phase | What Happens | What You Learn |
|-------|-------------|----------------|
| **1. CONNECT** | MCP handshake (initialize) | Server name, version, capabilities, protocol version |
| **2. DISCOVER** | List all tools + JSON schemas | Exactly what an AI agent sees: tool names, descriptions, parameter types |
| **3. READ** | Read files, list dirs, get metadata | How agents consume file data through MCP |
| **4. WRITE** | Create files, edit files, move files | How agents modify the filesystem through MCP |
| **5. SEARCH** | Regex search across files | How agents find information without reading every file |
| **6. BOUNDARIES** | Try to escape the sandbox | What gets DENIED — path traversal, system files, writes outside sandbox |

## The Sandbox

The `sandbox/` directory contains test files for the server to operate on:

```
sandbox/
├── hello.txt          Simple text file
├── notes.md           Markdown file about MCP
└── data/
    └── sample.csv     CSV with risk level data
```

The agent will also create new files and directories during the demo to show
write capabilities.

## Key Insight

The official server exposes **10 tools** — but the agent has ZERO control over
which tools exist or what directories are allowed. The server decides everything.
This is the core of MCP's security model: the server is the gatekeeper, not
the agent.

## After Running

Check the `sandbox/` directory — you'll see files the agent created and edited.
This proves the MCP operations were real, not simulated.
