# Gateway Log Example

One real run of the gateway in front of the remote GitHub MCP server, kept so there is a
complete `gateway-log/3` file to look at. Nobody is named in the gateway's config: every
caller signs in at the identity provider, and the log names each caller only from the
signed token. Field meanings are in the
[gateway README](../../../../src/mcp_security/gateway/README.md#log-format-gateway-log3).

## Read it

The `.jsonl` file is the record (append-only, chained, one JSON object per line). Two
views are made from it, and any gateway log renders the same way:

| View | File | Command |
|---|---|---|
| One line per event, like a normal log: time, level, agent id, app, user id, session, request, event, result, duration, size, details | [`github_view.txt`](github_view.txt) | `uv run python -m mcp_security.gateway.log_view <log.jsonl>` |
| Grouped by session, one block per exchange (request, verdict, reply) | [`github_grouped.txt`](github_grouped.txt) | `... log_view <log.jsonl> --grouped` |

In a terminal the first view colours `WARN` and `ERROR` lines. A piece of it:

```text
TIME          LEVEL  AGENT_ID      AGENT        USER_ID                               SESSION   REQUEST   EVENT                             RESULT               DURATION      SIZE  DETAILS
09:00:21.724  INFO   0b995eb352ca  claude-code  a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21  12371305  b8121977  → tools/call get_file_contents    -                           -     183 B  owner=modelcontextprotocol path=README.md repo=python-sdk
09:00:21.724  INFO   0b995eb352ca  claude-code  a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21  12371305  b8121977  ◆ verdict get_file_contents       risk 75.0 high              -         -  cell=75.0 factor=1.00 asset=helios-scada-gateway basis=unresolved input=4(owner,repo) catalog=scanned
09:00:23.041  INFO   0b995eb352ca  claude-code  a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21  12371305  b8121977  ← tools/call get_file_contents    200 ok                 1.32 s    5.0 KB  body=not-kept
09:00:26.145  INFO   2d614e2da252  ci-bot       5d2e8c40-1f6a-4b37-a0e9-c4b81f2d9a73  c1f8c756  aaf1c8f1  → tools/call list_pull_requests   -                           -     177 B  owner=modelcontextprotocol perPage=2 repo=python-sdk
09:00:28.916  WARN   d67a0331eeb4  claude-code  0b7f13aa-2c94-4e0d-8a6f-5e19c3d70f44  12371305  4b64cd60  ! session_agent_mismatch          -                           -         -  owner="claude-code (a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b…" owner_id=0b995eb352ca ended=yes from=127.0.0.1
09:00:28.916  INFO   d67a0331eeb4  claude-code  0b7f13aa-2c94-4e0d-8a6f-5e19c3d70f44  12371305  4b64cd60  → tools/call list_commits         -                           -     172 B  owner=modelcontextprotocol perPage=1 repo=python-sdk
09:00:29.825  WARN   -             -            -                                     -         cb247a2e  ! auth_failed                     token_expired               -         -  from=127.0.0.1
09:00:29.836  WARN   -             -            -                                     -         bb092bc7  ! auth_failed                     wrong_audience              -         -  from=127.0.0.1
```

## Who the callers are, and how the gateway knows

The gateway is an OAuth resource server. It checks each access token's signature against
the identity provider's published keys, its issuer, its audience (this route) and its
expiry, and reads the caller from it. The routes file holds only where the provider is.

| Field | In this log | Comes from |
|---|---|---|
| `user.id` | `a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21` (alice), `0b7f13aa-2c94-4e0d-8a6f-5e19c3d70f44` (bob), `5d2e8c40-1f6a-4b37-a0e9-c4b81f2d9a73` (the ci-bot service account) | The token's `sub`: the person the provider signed in, or the service account |
| `gateway.app`, `gateway.agent` | `claude-code`, `ci-bot` | The token's `client_id`: an application an administrator registered at the provider. There is no self-registration, so the name is vouched for |
| `gateway.agent_id` | `0b995eb352ca` (alice in claude-code) | SHA-256 of issuer, app and user, first 12 characters: one per person per app, the key for baselines and session ownership |
| `gateway.auth`, `gateway.issuer` | `oauth`, `http://127.0.0.1:18800` | How the caller was identified, and who signed the token |
| `gateway.scopes`, `gateway.token_id` | `['mcp:tools']`, `300ccf7ecb84764f` | What the token allows, and its `jti` (for audit and revocation) |
| `gateway.client` | `mcp/0.1.0` | Self-reported by the client in `initialize` — not identity |
| `mcp.session.id` | `12371305…` | The server's session id, logged only as a keyed pseudonym |
| `gateway.exchange_id` | `b8121977…` | One id per HTTP request, on every line it produced |

To put a name to `a4c9e2d1…`, ask the identity provider's directory; the gateway and its
log never hold names. If the token is edited to say someone else, its signature no longer
verifies and the request is refused.

## How it was made

```bash
uv run python reports/experiments/gateway/log_example/make_example.py   # needs `gh` login
```

[`make_example.py`](make_example.py) starts [`identity_provider.py`](identity_provider.py)
(standing in for the organisation's Okta, Entra ID or Keycloak: two applications registered
in advance, `claude-code` for people and the `ci-bot` service) and the real gateway with
[`routes.json`](routes.json), then:

1. **alice** signs in with `claude-code`, the stock `mcp` OAuth client: its first request
   has no token (line 2, `no_bearer_token`), the 401 points it to the provider, it
   signs in (authorization code with PKCE; the browser step is automated) and retries. She
   makes five read-only calls on the public repository `modelcontextprotocol/python-sdk` —
   one reads a file that does not exist (a tool error), one names a tool that does not
   exist (a JSON-RPC error) — and her client ends the session.
2. The **ci-bot** service gets a token with client credentials (no person, no browser) and
   makes one call.
3. **bob** signs in with `claude-code` the same way and makes one call, then sends one on
   alice's ended session. It is flagged, and GitHub still answers it.
4. A token that expired an hour ago, a token minted for another server (`/slack`), and a
   request to a route the gateway does not have (`/gitlab`).

Settings: `log_bodies: "requests"` (reply bodies dropped — GitHub's commit listings carry
commit authors' e-mail addresses, which should not sit in a log or this repository),
`GATEWAY_LOG_KEY` set (pseudonyms are keyed HMACs), the route's scan, breadth spec, input
rules and importance file all loaded. Both files pass the chain check:

```bash
uv run python -m mcp_security.gateway.log_file verify \
    reports/experiments/gateway/log_example/github.jsonl \
    reports/experiments/gateway/log_example/_gateway.jsonl
```

## One of each kind

Raw records from `github.jsonl`; long `message` bodies are shortened here to their size.

### Run starts (line 1)

What this run is: the config, the static artifacts every score below came from, and the identity provider (`gateway.oauth_issuer`).

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141218.9452443,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "gateway",
 "gateway.notice": "gateway_started",
 "gateway.config_sha256": "4c0c8a306dc8",
 "gateway.artifacts": {
  "scan": "ad0f7c85d943",
  "breadth": "1db9c5155f21",
  "rules": "ba341a5d68a1"
 },
 "gateway.effects_sha256": "ff3018bbe203",
 "gateway.log_bodies": "requests",
 "gateway.pseudonyms_keyed": true,
 "gateway.auth": "oauth",
 "gateway.oauth_issuer": "http://127.0.0.1:18800"
}
```

### A client's first request, before it has signed in (line 2)

No token yet: refused with a 401 whose `WWW-Authenticate` header names where to sign in. Every OAuth client starts this way.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141219.167426,
 "log.level": "warn",
 "gateway.route": "github",
 "gateway.direction": "gateway",
 "gateway.exchange_id": "844471a174ba4f859c026dc14d02b434",
 "client.address": "127.0.0.1",
 "client.port": 39322,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "gateway.notice": "auth_failed",
 "gateway.reason": "no_bearer_token",
 "gateway.prev_sha256": "eb3505adf0f8405fcf0b55daff81c553b307a0d8d58031265c1802b2fc56b262"
}
```

### A tool call (line 16)

Who (agent id, app, user id, how identified, issuer, scopes, token id — all from the token), where (address, client, protocol), the call (tool, argument names, argument pseudonym, typed effects) and the request body. `gateway.seq` counts every line in the session; `gateway.request_seq` only alice's own messages.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141221.7245462,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "agent->server",
 "gateway.exchange_id": "b8121977402e430f8962c9dc26c9d918",
 "gateway.agent_id": "0b995eb352ca",
 "gateway.agent": "claude-code",
 "user.id": "a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21",
 "gateway.app": "claude-code",
 "gateway.auth": "oauth",
 "gateway.issuer": "http://127.0.0.1:18800",
 "gateway.scopes": [
  "mcp:tools"
 ],
 "gateway.token_id": "300ccf7ecb84764f",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 13,
 "gateway.request_seq": 4,
 "client.address": "127.0.0.1",
 "client.port": 48754,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "mcp.session.id": "12371305548751cc630361b3da0025f0",
 "mcp.protocol.version": "2025-11-25",
 "mcp.method.name": "tools/call",
 "gen_ai.operation.name": "execute_tool",
 "jsonrpc.request.id": "3",
 "gen_ai.tool.name": "get_file_contents",
 "gateway.message_bytes": 183,
 "gateway.tool_listed": true,
 "gateway.arg_keys": [
  "owner",
  "path",
  "repo"
 ],
 "gateway.args_hash": "50fed1c7a8411661db8f44d858f0f9c0",
 "gateway.effects": {
  "which": {
   "owner": "modelcontextprotocol",
   "path": "README.md",
   "repo": "python-sdk"
  }
 },
 "message": {
  "method": "tools/call",
  "params": {
   "name": "get_file_contents",
   "arguments": {
    "owner": "modelcontextprotocol",
    "repo": "python-sdk",
    "path": "README.md"
   }
  },
  "jsonrpc": "2.0",
  "id": 3
 },
 "gateway.prev_sha256": "c653bc02c2c9336a59de53ea1af4cb4564cddcff0f805698da5b645640221ebf"
}
```

### Its verdict, before forwarding (line 17)

The framework's score. The org policy behind the scan is for a fictional organisation, so nothing in the arguments names one of its assets (`basis: unresolved`) and the call is priced at the worst asset the tool can reach (`helios-scada-gateway`: cell `75.0`, band `high`). `gateway.catalog_match: true` says the session saw the very tool list the scan was run on.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141221.7245462,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "gateway",
 "gateway.exchange_id": "b8121977402e430f8962c9dc26c9d918",
 "gateway.agent_id": "0b995eb352ca",
 "gateway.agent": "claude-code",
 "user.id": "a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21",
 "gateway.app": "claude-code",
 "gateway.auth": "oauth",
 "gateway.issuer": "http://127.0.0.1:18800",
 "gateway.scopes": [
  "mcp:tools"
 ],
 "gateway.token_id": "300ccf7ecb84764f",
 "gateway.seq": 14,
 "mcp.session.id": "12371305548751cc630361b3da0025f0",
 "mcp.method.name": "tools/call",
 "gen_ai.operation.name": "execute_tool",
 "jsonrpc.request.id": "3",
 "gen_ai.tool.name": "get_file_contents",
 "gateway.catalog_match": true,
 "gateway.decision": {
  "asset": "helios-scada-gateway",
  "basis": "unresolved",
  "cell": 75.0,
  "factor": 1.0,
  "risk": 75.001,
  "input_level": 4,
  "input_set_by": "owner,repo",
  "score_us": 474,
  "reasons": "L=1.00(0.97x the median tool, held back to 0% on 1 calls)",
  "band": "high",
  "sensitivity": 5,
  "impact": 3,
  "blast": 5,
  "artifacts": {
   "scan": "ad0f7c85d943",
   "breadth": "1db9c5155f21",
   "rules": "ba341a5d68a1"
  }
 },
 "gateway.prev_sha256": "5f9ebf468bd996d483bc37ae43f7fd93c738b1990722bd6896cae17f62ec666a"
}
```

### Its reply (line 18)

Status, time taken and size — no body, as `log_bodies` is `requests`.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141223.041792,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "server->agent",
 "gateway.exchange_id": "b8121977402e430f8962c9dc26c9d918",
 "gateway.agent_id": "0b995eb352ca",
 "gateway.agent": "claude-code",
 "user.id": "a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21",
 "gateway.app": "claude-code",
 "gateway.auth": "oauth",
 "gateway.issuer": "http://127.0.0.1:18800",
 "gateway.scopes": [
  "mcp:tools"
 ],
 "gateway.token_id": "300ccf7ecb84764f",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 15,
 "client.address": "127.0.0.1",
 "client.port": 48754,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "http.response.status_code": 200,
 "mcp.session.id": "12371305548751cc630361b3da0025f0",
 "mcp.protocol.version": "2025-11-25",
 "mcp.method.name": "tools/call",
 "gen_ai.operation.name": "execute_tool",
 "jsonrpc.request.id": "3",
 "gen_ai.tool.name": "get_file_contents",
 "gateway.duration_s": 1.3173,
 "gateway.message_bytes": 5086,
 "gateway.prev_sha256": "a0d5890a1dfe69c2eba78b63087e823c048ae6703d77bcc71ef6e403db635286"
}
```

### A call with a time span (line 19)

`since` and `until` are labelled `when` by the scan, so the log holds their span (`when_span_days`) without anyone parsing GitHub's arguments.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141223.0452793,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "agent->server",
 "gateway.exchange_id": "b22d6dcf72a142ff96879fdc80f81144",
 "gateway.agent_id": "0b995eb352ca",
 "gateway.agent": "claude-code",
 "user.id": "a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21",
 "gateway.app": "claude-code",
 "gateway.auth": "oauth",
 "gateway.issuer": "http://127.0.0.1:18800",
 "gateway.scopes": [
  "mcp:tools"
 ],
 "gateway.token_id": "300ccf7ecb84764f",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 16,
 "gateway.request_seq": 5,
 "client.address": "127.0.0.1",
 "client.port": 48762,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "mcp.session.id": "12371305548751cc630361b3da0025f0",
 "mcp.protocol.version": "2025-11-25",
 "mcp.method.name": "tools/call",
 "gen_ai.operation.name": "execute_tool",
 "jsonrpc.request.id": "4",
 "gen_ai.tool.name": "list_commits",
 "gateway.message_bytes": 237,
 "gateway.tool_listed": true,
 "gateway.arg_keys": [
  "owner",
  "perPage",
  "repo",
  "since",
  "until"
 ],
 "gateway.args_hash": "5b2daeeeb8598472a3d1b855153c39fc",
 "gateway.effects": {
  "which": {
   "owner": "modelcontextprotocol",
   "repo": "python-sdk"
  },
  "when_span_days": 30.0
 },
 "message": {
  "method": "tools/call",
  "params": {
   "name": "list_commits",
   "arguments": {
    "owner": "modelcontextprotocol",
    "repo": "python-sdk",
    "perPage": 3,
    "since": "2026-09-01T00:00:00Z",
    "until": "2026-10-01T00:00:00Z"
   }
  },
  "jsonrpc": "2.0",
  "id": 4
 },
 "gateway.prev_sha256": "c44840c46202348ed536f60967ca7c417926453a850a4d56367ee087ee1adca7"
}
```

### The tool reports an error (line 24)

The call ran and failed: `error.type: tool_error` (OpenTelemetry's value for `isError`).

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141225.106361,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "server->agent",
 "gateway.exchange_id": "3306848de2794a0faba54b0b9d6ceaf5",
 "gateway.agent_id": "0b995eb352ca",
 "gateway.agent": "claude-code",
 "user.id": "a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21",
 "gateway.app": "claude-code",
 "gateway.auth": "oauth",
 "gateway.issuer": "http://127.0.0.1:18800",
 "gateway.scopes": [
  "mcp:tools"
 ],
 "gateway.token_id": "300ccf7ecb84764f",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 21,
 "client.address": "127.0.0.1",
 "client.port": 48766,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "http.response.status_code": 200,
 "mcp.session.id": "12371305548751cc630361b3da0025f0",
 "mcp.protocol.version": "2025-11-25",
 "mcp.method.name": "tools/call",
 "gen_ai.operation.name": "execute_tool",
 "jsonrpc.request.id": "5",
 "gen_ai.tool.name": "get_file_contents",
 "error.type": "tool_error",
 "gateway.duration_s": 1.489,
 "gateway.message_bytes": 221,
 "gateway.prev_sha256": "beccce598e5d31835dd5d5a0226a0c6fbb85ef2dabd2a9ff87725008798a7ee6"
}
```

### A JSON-RPC error (line 27)

An unknown tool: the code is in `rpc.response.status_code`, and there is no `error.type`, since OpenTelemetry counts -32602 as the caller's mistake, not an error.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141225.3131106,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "server->agent",
 "gateway.exchange_id": "3f52915a6cc043659b2f48ed2055dd88",
 "gateway.agent_id": "0b995eb352ca",
 "gateway.agent": "claude-code",
 "user.id": "a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21",
 "gateway.app": "claude-code",
 "gateway.auth": "oauth",
 "gateway.issuer": "http://127.0.0.1:18800",
 "gateway.scopes": [
  "mcp:tools"
 ],
 "gateway.token_id": "300ccf7ecb84764f",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 24,
 "client.address": "127.0.0.1",
 "client.port": 48768,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "http.response.status_code": 200,
 "mcp.session.id": "12371305548751cc630361b3da0025f0",
 "mcp.protocol.version": "2025-11-25",
 "mcp.method.name": "tools/call",
 "gen_ai.operation.name": "execute_tool",
 "jsonrpc.request.id": "6",
 "gen_ai.tool.name": "no_such_tool",
 "rpc.response.status_code": "-32602",
 "gateway.duration_s": 0.2024,
 "gateway.message_bytes": 98,
 "gateway.prev_sha256": "a8e1534e204ad6b4c92abc5f701dbcd04c1d3d7d20b8bae672845e0294d2e31a"
}
```

### A service, not a person (line 37)

The ci-bot's token came from client credentials: `user.id` is its service account, `gateway.app` the registered service.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141226.1450827,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "agent->server",
 "gateway.exchange_id": "aaf1c8f13a9441ff8f9f3222cb592d2b",
 "gateway.agent_id": "2d614e2da252",
 "gateway.agent": "ci-bot",
 "user.id": "5d2e8c40-1f6a-4b37-a0e9-c4b81f2d9a73",
 "gateway.app": "ci-bot",
 "gateway.auth": "oauth",
 "gateway.issuer": "http://127.0.0.1:18800",
 "gateway.scopes": [
  "mcp:tools"
 ],
 "gateway.token_id": "02d7cbfb9eaaf766",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 7,
 "gateway.request_seq": 3,
 "client.address": "127.0.0.1",
 "client.port": 48840,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "mcp.session.id": "c1f8c756d760d5c19f529122b5abaa4f",
 "mcp.protocol.version": "2025-11-25",
 "mcp.method.name": "tools/call",
 "gen_ai.operation.name": "execute_tool",
 "jsonrpc.request.id": "2",
 "gen_ai.tool.name": "list_pull_requests",
 "gateway.message_bytes": 177,
 "gateway.tool_listed": true,
 "gateway.arg_keys": [
  "owner",
  "perPage",
  "repo"
 ],
 "gateway.args_hash": "44e21a30f807997bcdbab5deb0509092",
 "gateway.effects": {
  "how_much": {
   "perPage": 2
  }
 },
 "message": {
  "method": "tools/call",
  "params": {
   "name": "list_pull_requests",
   "arguments": {
    "owner": "modelcontextprotocol",
    "repo": "python-sdk",
    "perPage": 2
   }
  },
  "jsonrpc": "2.0",
  "id": 2
 },
 "gateway.prev_sha256": "be2533c95ef490f48d9e11948ae743cc74de6a86b8680536ba9d2cabe08d2041"
}
```

### Another user on the session (line 59)

bob, signed in and with a valid token of his own, sends a call on alice's session id after she ended it. The gateway remembers the session's owner (`gateway.session_owner_id`, her agent id), so this is a `warn` — and forwarded, since the gateway never blocks. GitHub answered it (line 62): a closed session id still works upstream, which is why session ids are logged only as pseudonyms.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141228.916276,
 "log.level": "warn",
 "gateway.route": "github",
 "gateway.direction": "gateway",
 "gateway.exchange_id": "4b64cd604f794018831ec228a749aee7",
 "gateway.agent_id": "d67a0331eeb4",
 "gateway.agent": "claude-code",
 "user.id": "0b7f13aa-2c94-4e0d-8a6f-5e19c3d70f44",
 "gateway.app": "claude-code",
 "gateway.auth": "oauth",
 "gateway.issuer": "http://127.0.0.1:18800",
 "gateway.scopes": [
  "mcp:tools"
 ],
 "gateway.token_id": "55c4badc653a8631",
 "client.address": "127.0.0.1",
 "client.port": 48928,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "mcp.session.id": "12371305548751cc630361b3da0025f0",
 "gateway.notice": "session_agent_mismatch",
 "gateway.session_owner": "claude-code (a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21)",
 "gateway.session_owner_id": "0b995eb352ca",
 "gateway.session_ended": true,
 "gateway.prev_sha256": "77d06298e359bbb7efc36966a8a0cc11c6d90150e16f839dbd4a4770259834ac"
}
```

### A token that expired (line 63)

Correctly signed by the provider, but past its `exp`: refused (`token_expired`). Nothing about the caller is logged beyond the request's address.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141229.8251364,
 "log.level": "warn",
 "gateway.route": "github",
 "gateway.direction": "gateway",
 "gateway.exchange_id": "cb247a2e978b4fc58cb0cd5f0e49fd92",
 "client.address": "127.0.0.1",
 "client.port": 50908,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "gateway.notice": "auth_failed",
 "gateway.reason": "token_expired",
 "gateway.prev_sha256": "1c703cb64b922bd6376654552a59b9d1f43abc447820c0d30c65fe1a197b59b4"
}
```

### A token minted for another server (line 64)

Signed by the provider for `/slack`, sent to `/github`: refused (`wrong_audience`, RFC 8707). A token one server receives cannot be replayed at another.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141229.8364356,
 "log.level": "warn",
 "gateway.route": "github",
 "gateway.direction": "gateway",
 "gateway.exchange_id": "bb092bc7212b4bc8b83b60f9536df4e8",
 "client.address": "127.0.0.1",
 "client.port": 50910,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "gateway.notice": "auth_failed",
 "gateway.reason": "wrong_audience",
 "gateway.prev_sha256": "57f1f0bf967b6ecd489f6471fa8d5f05f5cbb601a7b719badbd5c156aef6ab69"
}
```

### A request to an unknown route (`_gateway.jsonl`, line 1)

Written to `_gateway.jsonl`, as there is no route file for it.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141229.8458664,
 "log.level": "warn",
 "gateway.route": "gitlab",
 "gateway.direction": "gateway",
 "gateway.exchange_id": "bfa13ca940064000a387257439446303",
 "client.address": "127.0.0.1",
 "client.port": 50916,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "gateway.notice": "unknown_route"
}
```

### Run stops (line 65)

Written on a clean shutdown. Every line after the first carries `gateway.prev_sha256`, the digest of the line before it.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792141230.0401864,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "gateway",
 "gateway.notice": "gateway_stopped",
 "gateway.config_sha256": "4c0c8a306dc8",
 "gateway.artifacts": {
  "scan": "ad0f7c85d943",
  "breadth": "1db9c5155f21",
  "rules": "ba341a5d68a1"
 },
 "gateway.effects_sha256": "ff3018bbe203",
 "gateway.log_bodies": "requests",
 "gateway.pseudonyms_keyed": true,
 "gateway.auth": "oauth",
 "gateway.oauth_issuer": "http://127.0.0.1:18800",
 "gateway.prev_sha256": "49699b2e205eaa95fd5e82c304b5276c07e477b6041f74e6ea79419b4e086f72"
}
```

## What is not in it

Checked on both files: no access token, no GitHub token, no client secret, no raw session
id, no e-mail address, no reply content, no person's name. What is there and could be
sensitive in another deployment: the request arguments (`message` on request lines, and
`which` / `action` values in `gateway.effects`); set `log_bodies: "none"` to keep only the
typed fields.

## Use it

```bash
# re-score it offline with the same framework (writes github_scored.csv next to the log)
uv run python -m mcp_security.gateway.score \
    --config reports/experiments/gateway/log_example/routes.json --route github
```

## Files

| File | What it is |
|---|---|
| `github.jsonl` | The route's log: 65 lines |
| `_gateway.jsonl` | Requests that matched no route: 1 line |
| `github_view.txt` | The same log, one line per event (`log_view.py`) |
| `github_grouped.txt` | The same log, grouped by session (`log_view.py --grouped`) |
| `routes.json` | The gateway config of the run: the route and where the identity provider is — no callers |
| `identity_provider.py` | The identity provider of the run: registered applications, a directory of people and one service account |
| `make_example.py` | Re-makes both log files and both views (replaces them) |
