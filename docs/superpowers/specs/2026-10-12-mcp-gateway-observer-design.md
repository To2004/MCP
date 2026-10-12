# MCP Gateway Observer — Design (demo)

An observe-only MCP gateway: a web agent is pointed at the gateway URL instead of an
external MCP server's URL, every JSON-RPC message is recorded, and a separate offline step
scores the recorded tool calls with the existing static + dynamic layers.

## Goal

- Sit in front of an **external** MCP server (Streamable HTTP / JSON-RPC) so every message
  reaches us before the server sees it.
- Be **invisible to the agent**: identical bodies, no added headers, SSE passed through as it
  arrives. The model sees exactly what the upstream sends.
- **Observe only** — never block. Research instrument first; enforcement is out of scope.
- Demo-sized: about 300 lines, easy to change.

## Decisions

| Question | Decision |
|---|---|
| Where it sits | MCP gateway the agent is configured to use (the real-world pattern; we control neither side otherwise) |
| Transport | Streamable HTTP: `POST` / `GET` / `DELETE` on `/{route}[/...]` |
| Credentials | The gateway holds the upstream key (env var named in config); agents authenticate to the gateway with their own bearer token, stored only as a SHA-256 hash |
| What is recorded | MCP wire only — one JSON line per JSON-RPC message, both directions |
| Scoring | Offline and re-runnable, only for routes with a scan configured; others are recorded raw |

## Files

| File | Job |
|---|---|
| `src/mcp_security/gateway/proxy.py` | Forwards to the upstream, streams the reply back unchanged, logs each message |
| `src/mcp_security/gateway/score.py` | Pairs `tools/call` with its result; `R = min(score_max, cell × B × L)` |
| `src/mcp_security/gateway/routes.example.json` | Route → upstream URL, key env-var name, optional scan + breadth kind; agent token hashes |
| `tests/gateway/test_gateway.py` | Fake upstream: pass-through identical, key injected, nothing secret logged, scoring pairs and scores |

## Log line

```json
{"ts": 1760256000.12, "route": "github", "agent": "alice", "session": "abc",
 "direction": "agent->server", "http": "POST", "status": null, "message": {"jsonrpc": "2.0", ...}}
```

## Scoring

- `cell`: `binding.MatrixScorer` over the route's scan artifact (`cells` / `bands`).
- `B × L`: `GateScorer` from `scripts/dynamic_design/gate_runtime.py`, one `Connection` per
  route, replayed in log order, so re-running gives identical numbers.
- Output: `<log>_scored.csv` with tool, args, outcome, cell, asset, factor, R, reasons.

## Deliberately left out (demo)

Raw-byte replay, catalog hashing, queue/gap markers, driver labels, secret-path tokens,
OAuth pass-through, public hosting, enforcement. Each can be added later without changing
the log format.
