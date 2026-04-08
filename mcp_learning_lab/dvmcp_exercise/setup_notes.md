# DVMCP Setup Notes

Append-only log of install and run steps. Fill in as you go so the
exercise is reproducible later.

## DVMCP Source

- Repository: https://github.com/cybersecai-uk/dvmcp
- Commit / version used: v2.0.0 (commit 3d5b461, as of 5 April 2026)
- Date cloned: 5 April 2026

## Prerequisites

- Python version: 3.11+ (used for test client)
- Other runtimes (Node, Docker, etc.): **Node.js v24.14.1** (requires >=18)
- No external npm dependencies

## Install Steps

1. Clone the repository:
   ```
   git clone https://github.com/cybersecai-uk/dvmcp.git dvmcp-test
   cd dvmcp-test
   ```

2. Verify Node.js version:
   ```
   node --version  # Output: v24.14.1 ✓
   ```

3. Install dependencies (minimal - no external packages):
   ```
   npm install  # output: "up to date, audited 1 package"
   ```

4. Start the server:
   ```
   node server.js
   ```
   Server listens on `http://localhost:3001`

## Run Command

```bash
# From dvmcp-test directory
node server.js
# Server starts on port 3001 (configurable via PORT env var)
```

## Transport

- [x] HTTP (default, port 3001)
- [ ] stdio
- [ ] HTTP / SSE extended
- [ ] Other

## How You Connected a Client

- [ ] MCP Inspector
- [ ] Claude Desktop
- [x] Custom Python script (see `client.py`)
- [ ] Other

## Tool List Observed

The server exposes 10 tools without authentication:

```json
{
  "tools": [
    {"name": "run_command", "description": "Execute a system command and return output"},
    {"name": "search_files", "description": "Search for files matching a pattern"},
    {"name": "fetch_url", "description": "Fetch content from a URL"},
    {"name": "read_file", "description": "Read any file from the filesystem"},
    {"name": "write_file", "description": "Write content to any file on the filesystem"},
    {"name": "query_database", "description": "Execute a SQL query against the database"},
    {"name": "list_processes", "description": "List running processes on the system"},
    {"name": "get_env_vars", "description": "Get environment variables including secrets"},
    {"name": "get_weather", "description": "Get current weather for a location"},
    {"name": "admin_panel", "description": "Access the admin control panel"}
  ]
}
```

## Issues and Fixes

**None encountered** — DVMCP installed and ran cleanly on first try with no resolution steps needed.
