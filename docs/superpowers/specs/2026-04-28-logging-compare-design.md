# Logging Compare Demo — Design Spec

MCP protocol logging vs MCP proxy logging, side-by-side in one runner.

## Goal

Show concretely that `notifications/message` (protocol logging) and proxy wire logs
capture different things at different layers. One script, two phases, real output.

## Files

```
mcp_learning_lab/logging_compare/
    server.py       — FastMCP server with 3 tools emitting notifications/message
    run_demo.py     — Two-phase runner: direct then proxy
```

## Server (`server.py`)

Uses FastMCP with `Context` to emit real `notifications/message` packets.

**Tools:**

| Tool | Args | Protocol logs emitted |
|------|------|-----------------------|
| `add` | `a: float, b: float` | debug: inputs; info: result |
| `divide` | `a: float, b: float` | debug: inputs; warning if b==0; info: result |
| `echo` | `message: str` | debug: received; info: echoing back |

Logging levels used: `debug`, `info`, `warning` — gives visible contrast in output.

`divide(10, 0)` raises `ValueError` after emitting the warning, so we see a log
notification followed by a JSON-RPC error response in the wire log.

## Runner (`run_demo.py`)

### Phase 1 — Direct (protocol logging)

1. Spawn `server.py` as subprocess over STDIO (`mcp.client.stdio.stdio_client`)
2. Open `ClientSession`, pass `logging_callback=` to capture `notifications/message`
3. Call: `add(3,5)`, `divide(10,2)`, `divide(10,0)`, `echo("hello MCP")`
4. Print captured log notifications, labelled clearly

Output shows only what the server chose to emit — nothing about the JSON-RPC envelope.

### Phase 2 — Proxy (wire logging)

1. Write a temp wire log path: `logs/proxy/logging_compare_wire.log`
2. Spawn `mcp-proxy --log-level DEBUG --port 8765 -- python server.py` as subprocess
3. Wait for port 8765 to open
4. Connect via SSE (`mcp.client.sse.sse_client`)
5. Call same 4 tool calls in same order
6. Terminate proxy, read and print wire log

Output shows every JSON-RPC packet: initialize handshake, tools/list, all tool
requests + responses, notifications, and the error response from divide(10,0).

### Output format

```
══════════════════════════════════════════════
 PHASE 1 — DIRECT CONNECTION (protocol logs)
══════════════════════════════════════════════
[LOG debug]   add called: a=3.0, b=5.0
[LOG info]    result=8.0
...

══════════════════════════════════════════════
 PHASE 2 — THROUGH MCP PROXY (wire log)
══════════════════════════════════════════════
[raw wire output from mcp-proxy]

══════════════════════════════════════════════
 WHAT'S THE DIFFERENCE?
══════════════════════════════════════════════
Phase 1 captured N log notifications (what server chose to say)
Phase 2 captured M wire lines (everything on the wire)
```

## Constraints

- No mocking — real subprocess server, real MCP client, real mcp-proxy
- Proxy port: 8765 (avoids collision with existing 8080 usage)
- Wire log: `logs/proxy/logging_compare_wire.log` (fits existing logs/proxy/ layout)
- Python only — no new dependencies beyond `mcp` (already installed)
- Run with: `uv run python mcp_learning_lab/logging_compare/run_demo.py`
