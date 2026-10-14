# Gateway (observe-only)

An MCP gateway that sits between agents and an **external** MCP server, records every
JSON-RPC message, and runs the whole framework on each call — the static scan's cell, the
dynamic layer's runtime factor and the input rules — *before* forwarding it. It never blocks.

## How it sits in the path

```
agents ──HTTP JSON-RPC──► gateway /{route} ─────────────────► external MCP server
                              │
          tools/call ─────────┼─► framework.py (before forwarding, ~0.2 ms)
                              │     static:  arguments → asset → cell  (scan cells)
                              │     dynamic: B × L, learned from earlier calls
                              │     input rules: input level 1–5
                              │     → decision line in the log
                              │
          tools/list reply ───┼─► tool list the scan was not run on?
                              │     → saved to <log_dir>/catalogs/, notice in the log
                              ▼
                    <log_dir>/<route>.jsonl   (messages + decisions + notices)

STATIC, once per tool list (GPU), feeds the route's config:
  static-scan: sensitivity, impact, blast   →  static_cells.py: S × blast × impact = cell
  static-scan: input importance             →  stage-2 input rules
  scan_breadth.py: which inputs are amounts →  breadth spec for B
```

The agent is given the gateway's URL instead of the server's. The upstream reply is streamed
back byte for byte with no added headers, so the model sees exactly what the server sent
(the demo checks the `tools/list` catalog is identical via the gateway and direct).

## Files

| File | What it does |
|---|---|
| `proxy.py` | Forwards `POST`/`GET`/`DELETE`, injects the upstream key, logs each message |
| `wire_log.py` | The log format: one JSON line per message, built from the wire alone |
| `framework.py` | The connection: a route's static artifacts loaded once, one call scored at a time |
| `catalog.py` | Pulls the server's tool list out of the log, in the shape `static-scan` reads |
| `static_cells.py` | Combines `static-scan`'s three levels into cells: the repo's v5 formula, max 125 |
| `score.py` | Re-scores a saved log offline with the same `framework.py`: gives the logged numbers, or what a new scan changes |
| `github_remote.py` | Remote GitHub MCP vs the npx server: tool and argument renames, policy rewrite |
| `routes.example.json` | Route → upstream URL, key env var, optional scan, breadth spec and kind; agents |
| `../../../scripts/gateway_replay_corpus.py` | Replays a recorded corpus through the gateway, one session per persona |
| `../../../scripts/gateway_static_scan.sbatch` | The static side on one GPU: `static-scan`, breadth pass, cells |

## Config

- `upstreams.<route>.url` — the external server. `key_env` names the env var holding its key
  (never the key itself); `key_header` / `key_prefix` default to `Authorization: Bearer `.
- `scan` + `kind` — set them to score the route; leave them out to record only. `scan` is
  any file with `cells` and `bands` (a v5 scan, or `static_cells.py` output).
- `breadth` — the breadth spec for this route's catalog; without it, the `kind`'s default.
- `agents` — `{sha256(token): name}`. Empty means no agent auth (local demo only). Make a
  hash with `python -c "import hashlib,sys;print(hashlib.sha256(sys.argv[1].encode()).hexdigest())" TOKEN`.

## Log format (`gateway-log/2`)

A deployment has no labels and no roles, only the wire, so each line holds only what the
wire says. Names follow the OpenTelemetry MCP semantic conventions where one exists; the
gateway's own fields are `gateway.*`; a field that does not apply is left out.

| Question | Fields |
|---|---|
| Who | `gateway.agent` (the agent's token, as its configured name), `gateway.client` (name/version from `initialize`), `client.address`, `client.port`, `user_agent.original` |
| When, in what order | `ts`, `mcp.session.id`, `gateway.seq` (position in the session) |
| What | `mcp.method.name`, `gen_ai.tool.name`, `jsonrpc.request.id`, `mcp.protocol.version`, `message` (the full JSON-RPC message) |
| What came back | `http.response.status_code`, `error.type` (JSON-RPC code, or `tool_error`), `gateway.duration_s`, `gateway.message_bytes` |
| Protocol | `gateway.catalog_sha256` (the tool list a session saw), `gateway.tool_listed` (was the called tool in it) |
| Decision (one per `tools/call`, before forwarding) | `gateway.decision`: `asset`, `basis`, `sensitivity`, `impact`, `blast`, `band`, `cell`, `factor`, `risk`, `input_level`, `input_set_by`, `score_us`, `reasons`, `artifacts` (digests of the scan, breadth and rules files); `gateway.catalog_match` (is the session's tool list the scanned one) |
| Notice | `gateway.notice` = `catalog_not_scanned`, with `gateway.catalog_file` |

Never logged: the `Authorization` header, the upstream key, any other header. Logs from
before this format (no `schema` key) are read with their old keys renamed.

## Run the whole thing

```bash
# 1. the gateway (listens on 127.0.0.1:8765)
GITHUB_TOKEN=$(gh auth token) uv run python -m mcp_security.gateway.proxy --config routes.json

# 2. agents: the 1,000-call org corpus, replayed through the gateway (reads only by default)
uv run python scripts/gateway_replay_corpus.py

# 3. static, once per catalog: capture the tool list, then scan it on a GPU
uv run python -m mcp_security.gateway.catalog --config routes.json --route github
sbatch --export=ALL,NAME=github_remote scripts/gateway_static_scan.sbatch

# 4. dynamic: score every call (re-run any time, e.g. after a new scan)
uv run python -m mcp_security.gateway.score --config routes.json --route github
```

The worked example, with every input and result, is in
[reports/experiments/gateway/github_remote/](../../../reports/experiments/gateway/github_remote/README.md).

## Limits (demo)

- Only `tools/call` is scored; every other method is recorded.
- A merged tool (`pull_request_read` with a `method` argument) has one cell per asset,
  shared by all its methods: `get_diff` and `get_status` score the same.
- Live and offline scores are identical (checked on 148 real calls), except the reported
  `asset` name when several assets tie on the same cell: `binding.scoring` breaks the tie
  in hash order, which changes between processes. The risk itself does not change.
- Each decision says whether the session's tool list is the one the route's scan was run on
  (`gateway.catalog_match`); a mismatch is logged and the new list saved, never blocked.
  A scan made without a recorded catalog digest (the v5 scans) gives `catalog_match` none.
- `B × L` needs warm-up: below ~20 calls per tool it stays near 1.0.
- Public hosting (HTTPS for a web agent) is not set up here — put a tunnel or reverse host
  in front, and configure `agents` before exposing a route that holds a real key.

Design: [docs/superpowers/specs/2026-10-12-mcp-gateway-observer-design.md](../../../docs/superpowers/specs/2026-10-12-mcp-gateway-observer-design.md)
