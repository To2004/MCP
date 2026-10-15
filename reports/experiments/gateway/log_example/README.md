# Gateway Log Example

One real run of the gateway in front of the remote GitHub MCP server, kept so there is a
complete `gateway-log/3` file to look at: every kind of line the gateway writes, from a
real agent session, with nothing secret in it. Field meanings are in the
[gateway README](../../../../src/mcp_security/gateway/README.md#log-format-gateway-log3).

## Read it

The `.jsonl` file is the record (append-only, chained, one JSON object per line). Two
views are made from it, and any gateway log renders the same way:

| View | File | Command |
|---|---|---|
| One line per event, like a normal log: time, level, agent id, agent, user id, session, request, event, result, duration, size, details | [`github_view.txt`](github_view.txt) | `uv run python -m mcp_security.gateway.log_view <log.jsonl>` |
| Grouped by session, one block per exchange (request, verdict, reply) | [`github_grouped.txt`](github_grouped.txt) | `... log_view <log.jsonl> --grouped` |

In a terminal the first view colours `WARN` and `ERROR` lines. A piece of it:

```text
TIME          LEVEL  AGENT_ID      AGENT  USER_ID  SESSION   REQUEST   EVENT                             RESULT               DURATION      SIZE  DETAILS
11:20:55.460  INFO   agt-0001      alice  u-0001   c36a1a8d  dbdb49f1  → tools/call get_file_contents    -                           -     183 B  owner=modelcontextprotocol path=README.md repo=python-sdk
11:20:55.460  INFO   agt-0001      alice  u-0001   c36a1a8d  dbdb49f1  ◆ verdict get_file_contents       risk 75.0 high              -         -  cell=75.0 factor=1.00 asset=helios-scada-gateway basis=unresolved input=4(owner,repo) catalog=scanned
11:20:55.552  INFO   agt-0001      alice  u-0001   c36a1a8d  f715536e  → GET  (stream)                   -                           -         -
11:20:55.747  INFO   agt-0001      alice  u-0001   c36a1a8d  f715536e  ← GET                             405                    0.19 s      36 B  body=not-kept
11:20:56.682  INFO   agt-0001      alice  u-0001   c36a1a8d  dbdb49f1  ← tools/call get_file_contents    200 ok                 1.22 s    5.0 KB  body=not-kept
…
11:20:59.421  WARN   1b93891181f4  bob    -        c36a1a8d  d6cbcd08  ! session_agent_mismatch          -                           -         -  owner=alice ended=yes from=127.0.0.1
11:20:59.421  INFO   1b93891181f4  bob    -        c36a1a8d  d6cbcd08  → tools/call list_commits         -                           -     172 B  owner=modelcontextprotocol perPage=1 repo=python-sdk
```

## Where the ids come from

None of them is sent by the agent: the gateway hashes the bearer token and looks the hash
up in the `agents` table of [`routes.json`](routes.json).

| Field | Example | Source |
|---|---|---|
| `gateway.agent_id` | `agt-0001`, `1b93891181f4` | The entry's `id` (alice), or — when it has none — the first 12 characters of the token's SHA-256 (bob), as GitHub's audit log records `hashed_token`. Set `id` to keep it across token rotations |
| `gateway.agent` | `alice` | The entry's name: a label for people |
| `user.id` | `u-0001` | The person the agent acts for, as the entry gives it (a pseudonym, not an e-mail) |
| `gateway.app` | `claude-code` | Which agent application holds the token |
| `gateway.client` | `mcp/0.1.0` | Self-reported by the client in `initialize` — not trusted for identity |
| `mcp.session.id` | `c36a1a8d…` | The server's session id, logged only as a keyed pseudonym |
| `gateway.exchange_id` | `dbdb49f1…` | One id per HTTP request, on every line it produced |

With OAuth (not set up here), `user.id` and the app would come from the identity
provider's token (`sub`, `client_id`) instead of the table.

## How it was made

```bash
uv run python reports/experiments/gateway/log_example/make_example.py   # needs `gh` login
```

[`make_example.py`](make_example.py) starts the real gateway process with
[`routes.json`](routes.json) and drives it like an agent would:

- **alice** (id `agt-0001`, user `u-0001`, app `claude-code`) opens a session with the
  real `mcp` client, lists the 49 tools and makes five calls on the public repository
  `modelcontextprotocol/python-sdk`: a search, reading `README.md`, listing a month of
  commits, reading a file that does not exist (a tool error), and calling a tool that does
  not exist (a JSON-RPC error). Her client then ends the session.
- **bob** (no id in the config, so `1b93891181f4`) sends one call on alice's ended session id.
  GitHub still answers it (200).
- A request with a guessed token, and one to a route that does not exist (`/gitlab`).

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

What this run is: which config and which static artifacts every score below came from.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063253.4055371,
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
 "gateway.agents": 2
}
```

### A tool call (line 13)

Who (agent id, name, user id, app — from the config), where (address, client, protocol), the call (tool, argument names, argument pseudonym, typed effects) and the request body. `log.level` is the line's severity. `gateway.seq` counts every line in the session; `gateway.request_seq` only alice's own messages.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063255.4604366,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "agent->server",
 "gateway.exchange_id": "dbdb49f19dcc4479b94c0da739ed504a",
 "gateway.agent_id": "agt-0001",
 "gateway.agent": "alice",
 "user.id": "u-0001",
 "gateway.app": "claude-code",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 11,
 "gateway.request_seq": 4,
 "client.address": "127.0.0.1",
 "client.port": 32870,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "mcp.session.id": "c36a1a8d6714888c187e6af20ff9c961",
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
 "gateway.prev_sha256": "d7fa05f7d2ae5def54d30668c283e24c5957ae2b9ea9f408c832259079c1879c"
}
```

### Its verdict, before forwarding (line 14)

The framework's score. The org policy behind the scan is for a fictional organisation, so nothing in the arguments names one of its assets (`basis: unresolved`) and the call is priced at the worst asset the tool can reach (`helios-scada-gateway`: cell `75.0`, band `high`). `gateway.catalog_match: true` says the session saw the very tool list the scan was run on.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063255.4604366,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "gateway",
 "gateway.exchange_id": "dbdb49f19dcc4479b94c0da739ed504a",
 "gateway.agent_id": "agt-0001",
 "gateway.agent": "alice",
 "user.id": "u-0001",
 "gateway.app": "claude-code",
 "gateway.seq": 12,
 "mcp.session.id": "c36a1a8d6714888c187e6af20ff9c961",
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
  "score_us": 780,
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
 "gateway.prev_sha256": "2ee5b2e12572e1b9441c55189a9818f6ab4b4d0b7dbd04354073b6eeb294e395"
}
```

### Its reply (line 17)

Status, time taken and size — no body, as `log_bodies` is `requests`.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063256.6821816,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "server->agent",
 "gateway.exchange_id": "dbdb49f19dcc4479b94c0da739ed504a",
 "gateway.agent_id": "agt-0001",
 "gateway.agent": "alice",
 "user.id": "u-0001",
 "gateway.app": "claude-code",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 15,
 "client.address": "127.0.0.1",
 "client.port": 32870,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "http.response.status_code": 200,
 "mcp.session.id": "c36a1a8d6714888c187e6af20ff9c961",
 "mcp.protocol.version": "2025-11-25",
 "mcp.method.name": "tools/call",
 "gen_ai.operation.name": "execute_tool",
 "jsonrpc.request.id": "3",
 "gen_ai.tool.name": "get_file_contents",
 "gateway.duration_s": 1.2218,
 "gateway.message_bytes": 5086,
 "gateway.prev_sha256": "37210e69b9d6266745ec15f9bc89f3e1427f033c295add26de635926abebdfd1"
}
```

### A call with a time span (line 18)

`since` and `until` are labelled `when` by the scan, so the log holds their span (`when_span_days`) without anyone parsing GitHub's arguments.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063256.6895053,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "agent->server",
 "gateway.exchange_id": "707e873e1a1846a19353a4df90d3edbf",
 "gateway.agent_id": "agt-0001",
 "gateway.agent": "alice",
 "user.id": "u-0001",
 "gateway.app": "claude-code",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 16,
 "gateway.request_seq": 5,
 "client.address": "127.0.0.1",
 "client.port": 32884,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "mcp.session.id": "c36a1a8d6714888c187e6af20ff9c961",
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
 "gateway.prev_sha256": "04964327eabbe512d4383c093014a0b7387697e686d3a80a327732f020083625"
}
```

### The tool reports an error (line 23)

The call ran and failed: `error.type: tool_error` (OpenTelemetry's value for `isError`).

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063258.9714115,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "server->agent",
 "gateway.exchange_id": "48e78f5408014579af34d2f6b0f60188",
 "gateway.agent_id": "agt-0001",
 "gateway.agent": "alice",
 "user.id": "u-0001",
 "gateway.app": "claude-code",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 21,
 "client.address": "127.0.0.1",
 "client.port": 32888,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "http.response.status_code": 200,
 "mcp.session.id": "c36a1a8d6714888c187e6af20ff9c961",
 "mcp.protocol.version": "2025-11-25",
 "mcp.method.name": "tools/call",
 "gen_ai.operation.name": "execute_tool",
 "jsonrpc.request.id": "5",
 "gen_ai.tool.name": "get_file_contents",
 "error.type": "tool_error",
 "gateway.duration_s": 1.4499,
 "gateway.message_bytes": 221,
 "gateway.prev_sha256": "3c2513f327b9e3c92d9a9f4015911b6c5595e7968a87e39e2b47e97347987b8e"
}
```

### A JSON-RPC error (line 26)

An unknown tool: the code is in `rpc.response.status_code`, and there is no `error.type`, since OpenTelemetry counts -32602 as the caller's mistake, not an error.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063259.1952965,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "server->agent",
 "gateway.exchange_id": "3c3eb445ad4b48b3833aabc5faee14d8",
 "gateway.agent_id": "agt-0001",
 "gateway.agent": "alice",
 "user.id": "u-0001",
 "gateway.app": "claude-code",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 24,
 "client.address": "127.0.0.1",
 "client.port": 32898,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "http.response.status_code": 200,
 "mcp.session.id": "c36a1a8d6714888c187e6af20ff9c961",
 "mcp.protocol.version": "2025-11-25",
 "mcp.method.name": "tools/call",
 "gen_ai.operation.name": "execute_tool",
 "jsonrpc.request.id": "6",
 "gen_ai.tool.name": "no_such_tool",
 "rpc.response.status_code": "-32602",
 "gateway.duration_s": 0.2195,
 "gateway.message_bytes": 98,
 "gateway.prev_sha256": "69e012d13aeaa0170edcbc9203f3f7970dd6f043052918ff0b40c7bfb98dd369"
}
```

### A reply without a body (line 28)

GitHub's answer to the session's end: no JSON-RPC message, but the status is still logged.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063259.407389,
 "log.level": "info",
 "gateway.route": "github",
 "gateway.direction": "server->agent",
 "gateway.exchange_id": "67eaab160c414c73b50283dc9e462167",
 "gateway.agent_id": "agt-0001",
 "gateway.agent": "alice",
 "user.id": "u-0001",
 "gateway.app": "claude-code",
 "gateway.client": "mcp/0.1.0",
 "gateway.seq": 26,
 "client.address": "127.0.0.1",
 "client.port": 32906,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "DELETE",
 "http.response.status_code": 204,
 "mcp.session.id": "c36a1a8d6714888c187e6af20ff9c961",
 "mcp.protocol.version": "2025-11-25",
 "gateway.duration_s": 0.208,
 "gateway.message_bytes": 0,
 "gateway.prev_sha256": "7b835507fe281ac9addd09600819a7fa5f76d8a2e50228805da36842fe33d88f"
}
```

### Another agent on the session (line 29)

bob uses alice's session id after she ended it. The gateway remembers the owner, so this is a `warn` — and forwarded, since the gateway never blocks. GitHub answered it (line 32, status 200): a closed session id still works upstream, which is why the session id is only ever logged as a pseudonym.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063259.4214203,
 "log.level": "warn",
 "gateway.route": "github",
 "gateway.direction": "gateway",
 "gateway.exchange_id": "d6cbcd08bbed44e6a662f612153ca292",
 "gateway.agent_id": "1b93891181f4",
 "gateway.agent": "bob",
 "client.address": "127.0.0.1",
 "client.port": 52652,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "mcp.session.id": "c36a1a8d6714888c187e6af20ff9c961",
 "gateway.notice": "session_agent_mismatch",
 "gateway.session_owner": "alice",
 "gateway.session_ended": true,
 "gateway.prev_sha256": "8b53deaba3f1ca5cd7607ccbafb733a6210525aa5b1aa14522590e9c17a97464"
}
```

### A refused login (line 33)

No agent id: the token matched none. The token itself is not logged.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063259.8984752,
 "log.level": "warn",
 "gateway.route": "github",
 "gateway.direction": "gateway",
 "gateway.exchange_id": "8203dd3542c8465da72bc15ee51f0c23",
 "client.address": "127.0.0.1",
 "client.port": 52652,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "gateway.notice": "auth_failed",
 "gateway.reason": "unknown_token",
 "gateway.prev_sha256": "e605d5e593f37d21544e63f8338311ad91547a28e4ff838358bafb025dbe3a26"
}
```

### A request to an unknown route (`_gateway.jsonl`, line 1)

Written to `_gateway.jsonl`, as there is no route file for it.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063259.900303,
 "log.level": "warn",
 "gateway.route": "gitlab",
 "gateway.direction": "gateway",
 "gateway.exchange_id": "64adc18d799a48efbf52a1585bd7b0d7",
 "client.address": "127.0.0.1",
 "client.port": 52652,
 "user_agent.original": "python-httpx/0.28.1",
 "http.request.method": "POST",
 "gateway.notice": "unknown_route"
}
```

### Run stops (line 34)

Written on a clean shutdown. Every line after the first carries `gateway.prev_sha256`, the digest of the line before it.

```json
{
 "schema": "gateway-log/3",
 "ts": 1792063260.036962,
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
 "gateway.agents": 2,
 "gateway.prev_sha256": "c8a1f56f57ca3f192920fe8888565c457be30fc47476c73609fcfede8893dc05"
}
```

## What is not in it

Checked on both files: no GitHub token, no agent token, no raw session id, no e-mail
address, no reply content. What is there and could be sensitive in another deployment:
the request arguments (`message` on request lines, and `which` / `action` values in
`gateway.effects`); set `log_bodies: "none"` to keep only the typed fields.

## Use it

```bash
# re-score it offline with the same framework (writes github_scored.csv next to the log)
uv run python -m mcp_security.gateway.score \
    --config reports/experiments/gateway/log_example/routes.json --route github
```

## Files

| File | What it is |
|---|---|
| `github.jsonl` | The route's log: 34 lines |
| `_gateway.jsonl` | Requests that matched no route: 1 line |
| `github_view.txt` | The same log, one line per event (`log_view.py`) |
| `github_grouped.txt` | The same log, grouped by session (`log_view.py --grouped`) |
| `routes.json` | The gateway config of the run; `agents` holds the SHA-256 of two throwaway example tokens |
| `make_example.py` | Re-makes both log files and both views (replaces them) |
