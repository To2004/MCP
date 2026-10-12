# Gateway (observe-only)

An MCP gateway that sits between an agent and an **external** MCP server, records every
JSON-RPC message, and leaves scoring to a separate offline step. It never blocks.

## How it sits in the path

```
web agent ──HTTP JSON-RPC──► gateway /{route} ──► external MCP server
                                 │  one JSON line per message, both directions
                                 ▼
                       runs/gateway/<route>.jsonl
                                 │  score.py (re-run any time)
                                 ▼
                       runs/gateway/<route>_scored.csv
```

The agent is given the gateway's URL instead of the server's. The upstream reply is streamed
back byte for byte with no added headers, so the model sees exactly what the server sent
(the demo checks the `tools/list` catalog is identical via the gateway and direct).

## Files

| File | What it does |
|---|---|
| `proxy.py` | Forwards `POST`/`GET`/`DELETE`, injects the upstream key, logs each message |
| `score.py` | Pairs each `tools/call` with its result; `risk = min(score_max, cell × B × L)` |
| `routes.example.json` | Route → upstream URL, key env var, optional scan + breadth kind; agents |

## Config

- `upstreams.<route>.url` — the external server. `key_env` names the env var holding its key
  (never the key itself); `key_header` / `key_prefix` default to `Authorization: Bearer `.
- `scan` + `kind` — set them to score the route; leave them out to record only.
- `agents` — `{sha256(token): name}`. Empty means no agent auth (local demo only). Make a
  hash with `python -c "import hashlib,sys;print(hashlib.sha256(sys.argv[1].encode()).hexdigest())" TOKEN`.

## Run

```bash
GITHUB_TOKEN=$(gh auth token) uv run python -m mcp_security.gateway.proxy \
    --config src/mcp_security/gateway/routes.example.json          # listens on 127.0.0.1:8765

uv run python scripts/gateway_demo_agent.py --route deepwiki --direct https://mcp.deepwiki.com/mcp
uv run python -m mcp_security.gateway.score --config src/mcp_security/gateway/routes.example.json \
    --route github
```

## Limits (demo)

- Only `tools/call` is scored; every other method is recorded.
- A route's scan is matched by config, not by checking the live catalog against it.
- `B × L` needs warm-up: below ~20 calls per tool it stays near 1.0.
- Public hosting (HTTPS for a web agent) is not set up here — put a tunnel or reverse host
  in front, and configure `agents` before exposing a route that holds a real key.

Design: [docs/superpowers/specs/2026-10-12-mcp-gateway-observer-design.md](../../../docs/superpowers/specs/2026-10-12-mcp-gateway-observer-design.md)
