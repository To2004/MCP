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
| `proxy.py` | Forwards `POST`/`GET`/`DELETE`, injects the upstream key, logs each message, refusals and session takeovers |
| `config.py` | The routes file: upstreams, identity provider (OAuth), trusted proxies, pseudonym key |
| `oauth.py` | OAuth 2.1 resource server: checks the provider's JWT access tokens, reads the caller from them, serves RFC 9728 metadata |
| `wire_log.py` | The log format (`gateway-log/3`): one JSON line per message, built from the wire alone |
| `log_file.py` | Append-only JSONL with a per-file hash chain; `read_log`; `verify` command |
| `log_view.py` | A log rendered for people, one line per event like a normal log (`--grouped`: by session, one block per exchange) |
| `log_grouped.py`, `log_text.py` | The grouped view, and the formatting both views share |
| `effects.py` | Typed effect fields (`which`, `how_much`, `who`, `when`, `action`, `carried`) read through the scan's importance labels |
| `pseudonym.py` | Keyed HMAC pseudonyms for session ids, arguments and recipients |
| `http_wire.py` | Client address behind trusted proxies, `Mcp-Name` decoding, JSON-RPC from bodies and SSE |
| `framework.py` | The connection: a route's static artifacts loaded once, one call scored at a time |
| `catalog.py` | Pulls the server's tool list out of the log, in the shape `static-scan` reads |
| `static_cells.py` | Combines `static-scan`'s three levels into cells: the repo's v5 formula, max 125 |
| `score.py` | Re-scores a saved log offline with the same `framework.py`: gives the logged numbers, or what a new scan changes |
| `github_remote.py` | Remote GitHub MCP vs the npx server: tool and argument renames, policy rewrite |
| `routes.example.json` | Route → upstream URL, key env var, optional scan, breadth spec, importance and kind |
| `../../../scripts/gateway_replay_corpus.py` | Replays a recorded corpus through the gateway, one session per persona |
| `../../../scripts/gateway_static_scan.sbatch` | The static side on one GPU: `static-scan`, breadth pass, cells |

## Config

- `upstreams.<route>.url` — the external server. `key_env` names the env var holding its key
  (never the key itself); `key_header` / `key_prefix` default to `Authorization: Bearer `.
- `scan` + `kind` — set them to score the route; leave them out to record only. `scan` is
  any file with `cells` and `bands` (a v5 scan, or `static_cells.py` output).
- `breadth` — the breadth spec for this route's catalog; without it, the `kind`'s default.
- `scoring` — `inline` (default: scored before forwarding), `background` (just after, same
  process) or `off`. `history` — `route` (default: one runtime history for everyone) or
  `caller` (one per signed-in caller: issuer, app and user).
- `state_file` — where the runtime history is saved at shutdown and loaded at start, so a
  restart continues where it stopped; `state_every` also saves after every N scored calls.
- `importance` (per route) — the static scan's `<server>.importance.json`; adds typed effect
  fields (`gateway.effects`) to every `tools/call` line.
- `log_bodies` (per route) — `all` (default), `requests` (no reply bodies) or `none` (no
  bodies). `tools/list` replies are always kept. Argument names, the argument pseudonym and
  the typed effects are written in every mode; offline re-scoring needs `all` or `requests`.
- `hash_key_env` — env var holding the pseudonym key (default `GATEWAY_LOG_KEY`). Without it
  pseudonyms are plain SHA-256, guessable for low-entropy values; set it whenever
  `log_bodies` is not `all`.
- `trusted_proxies` — addresses/CIDRs whose `X-Forwarded-For` is believed; empty (default)
  means `client.address` is the TCP peer. Only this setting decides: the server's own
  forwarded-header handling is off.
- `oauth` — `{"issuer", "jwks_uri", "public_url", "scopes_supported"?, "algorithms"?, "leeway_s"?}`:
  the organisation's identity provider, and the only source of who a caller is — nobody is
  named in the routes file. People sign in there (authorization code with PKCE); services
  use client credentials; the agent application is registered there by an administrator.
  A token must be a JWT signed with a key from `jwks_uri`, with `iss` = `issuer`,
  `aud` = the route's URL (`public_url` + `/route`: a token for another server is refused)
  and a future `exp`; the caller is read from it — `sub` → `user.id`, `client_id` →
  `gateway.app`, plus `scope`, `jti` and `act`. `gateway.agent_id` is one per issuer, app and
  user. Each route publishes `/.well-known/oauth-protected-resource/<route>` and every 401
  carries `WWW-Authenticate: Bearer resource_metadata=...`, so a stock MCP client signs in on
  its own. The token is never sent upstream. Without `oauth` every caller is `anonymous`
  (local testing only; the gateway says so at start). A routes file with the old `agents`
  table is refused.

## Log format (`gateway-log/3`)

A deployment has no labels and no roles, only the wire, so each line holds only what the
wire says (plus who the token was issued to, from the config). Names follow the
OpenTelemetry MCP semantic conventions where one exists; the gateway's own fields are
`gateway.*`; a field that does not apply is left out.

| Question | Fields |
|---|---|
| Who | `user.id` (the token's `sub`), `gateway.app` and `gateway.agent` (its `client_id`), `gateway.agent_id` (one per issuer, app and user), `gateway.auth` (`oauth`, or `none` without a provider), `gateway.issuer`, `gateway.scopes`, `gateway.token_id`, `gateway.act` — all from the identity provider's signed token, `gateway.client` (self-reported name/version from `initialize` or `_meta`), `client.address` (behind trusted proxies), `client.port`, `network.peer.address` (the proxy, when there is one), `user_agent.original`, `http.request.header.origin` |
| Severity | `log.level`: `info`; `warn` for a refused login, an unknown route, a session used by another agent, an unscanned tool list or headers naming another call; `error` for an unreachable upstream or a failed score |
| When, in what order | `ts`, `mcp.session.id` (a pseudonym), `gateway.seq` (every line in the session), `gateway.request_seq` (the agent's own messages only), `gateway.exchange_id` (all lines of one HTTP request), `trace_id` / `span_id` (from `params._meta.traceparent`) |
| What | `mcp.method.name`, `gen_ai.operation.name` (`execute_tool`), `gen_ai.tool.name`, `jsonrpc.request.id` (string), `mcp.protocol.version`, `gateway.arg_keys`, `gateway.args_hash` (pseudonym of the canonical arguments), `gateway.effects`, `gateway.message_bytes` (UTF-8), `gateway.header_mismatch` (`Mcp-Method` / `Mcp-Name` naming another call than the body), `message` (per `log_bodies`) |
| What came back | `http.response.status_code`, `rpc.response.status_code` (JSON-RPC code), `error.type` (a real error: the code, `tool_error`, or an exception class; not -32700/-32600/-32601/-32602/-32002), `gateway.duration_s` |
| Protocol | `gateway.catalog_sha256` (the tool list a session saw), `gateway.tool_listed` (was the called tool in it) |
| Decision (one per `tools/call`, before forwarding) | `gateway.decision`: `asset`, `basis`, `sensitivity`, `impact`, `blast`, `band`, `cell`, `factor`, `risk`, `input_level`, `input_set_by`, `score_us`, `reasons`, `artifacts` (digests of the scan, breadth and rules files); `gateway.catalog_match` (is the session's tool list the scanned one) |
| Notice (`gateway.notice`) | `catalog_not_scanned` (+ `gateway.catalog_file`); `auth_failed` (+ `gateway.reason`: `no_bearer_token`, `token_expired`, `wrong_audience`, `wrong_issuer`, `bad_signature`, `unknown_signing_key`, `missing_claim` or `invalid_token`); `unknown_route` (in `_gateway.jsonl`); `session_agent_mismatch` (+ `gateway.session_owner`, `gateway.session_owner_id`, `gateway.session_ended`); `upstream_unreachable` (+ `error.type`, `gateway.error`); `gateway_started` / `gateway_stopped` (+ `gateway.config_sha256`, `gateway.artifacts`, `gateway.effects_sha256`, `gateway.log_bodies`, `gateway.pseudonyms_keyed`, `gateway.auth`, `gateway.oauth_issuer`) |
| Integrity | `gateway.prev_sha256`: SHA-256 of the previous line in the file. `uv run python -m mcp_security.gateway.log_file verify <log.jsonl>` reports where the chain breaks |

To read a log: `uv run python -m mcp_security.gateway.log_view <log.jsonl>` (one line per
event; `--grouped` for one block per exchange; `--out view.txt` to save it).
A complete example from one real run on GitHub, every line explained:
[reports/experiments/gateway/log_example/](../../../reports/experiments/gateway/log_example/README.md).

Never logged: the `Authorization` header, the upstream key, any refused token, the raw
session id, any other header. Logs from before this format are still read: v1 lines (no
`schema` key) with their old keys renamed, v2 lines as they are.

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
- One process carries ~600 calls/s and collapses above ~64 requests in flight (httpx's
  connection pool); run several processes, each caller always to the same one — never
  uvicorn `--workers`. Measured: [scale experiments](../../../reports/experiments/gateway/scale/README.md).
- The hash chain shows an edited, inserted or deleted line, not lines cut from the start
  or end of a file or a file rewritten whole: copy the logs (or their last digest) where
  the gateway cannot write. One process per `log_dir`: two writers on a file break it.
- A session used by an agent other than the one that opened it is logged
  (`session_agent_mismatch`) and still forwarded; refusing it is a decision rule to add.
- `Origin` is logged, not validated (MCP requires a server to answer 403 to a bad one).
- Public hosting (HTTPS for a web agent) is not set up here — put a tunnel or reverse host
  in front, and configure `oauth` before exposing a route that holds a real key.

Design: [docs/superpowers/specs/2026-10-12-mcp-gateway-observer-design.md](../../../docs/superpowers/specs/2026-10-12-mcp-gateway-observer-design.md).
Where it goes next (policy, storage, remote access): [docs/project/gateway-architecture.md](../../../docs/project/gateway-architecture.md).
