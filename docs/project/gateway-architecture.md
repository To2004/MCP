# Gateway Architecture: Connecting Policy, Static, Dynamic, Storage and Remote Access

How the framework becomes one connected system in front of remote MCP servers: what
exists today, what the standards and comparable systems do, and the build order. Research
done 2026-10-14; every source below was opened, not taken from a search snippet.

## The shape: NIST's policy roles, filled with our parts

NIST SP 800-207 (Zero Trust, §3.1–3.3) and SP 800-162 (ABAC) split access control into an
enforcement point, a decision point, information sources and an administration point. The
"trust algorithm" they describe is our framework: 800-207 §3.3.1 recommends a *contextual*
algorithm that "takes the subject… recent history into consideration", and a *score-based*
one that compares a weighted score with a configured threshold. Risk-adaptive access
control (Kandala, Sandhu, Bhamidipati, ARES 2011) is the same idea: risk computed in real
time from trustworthiness, threat and access history.

| Role | What it does | Ours today | Gap |
|---|---|---|---|
| PEP — enforcement point | Sees every call; carries out the decision | `gateway/proxy.py`, observe-only | No modes (observe / shadow / enforce) |
| PDP — decision point | Turns inputs into a decision | `gateway/framework.py` computes the risk; nothing turns it into an outcome | Decision rules: thresholds, hard "never" rules, outcome per band |
| PIP — static information | Facts known before the call | Scan cells, levels, breadth spec, input rules as JSON files named in the route config | Not indexed by the tool list they were made for; no store |
| PIP — dynamic information | What the caller did before | `gate_runtime.GateScorer` state, in memory, one history per route | Lost on restart; shared by all callers |
| PAP — administration point | Writes and versions policy | Org policy markdown (`~/mcp-static-scan/policies`, the remote copy); thresholds are code constants | No versioned policy bundle |
| Audit | Every message, decision and refusal | `wire_log.py` JSONL (gateway-log/3), decision lines with artifact digests, per-file hash chain (`log_file.py`) | No database; chain not anchored off the host |

## What comparable systems do

None of the gateways combines a design-time tool × asset matrix with learned per-caller
behaviour; that is this framework's contribution. They show the plumbing:

- **Policy as data, versioned.** OPA bundles carry a revision (git hash) and can be signed;
  every decision log records the bundle revision, the input and the result
  ([OPA bundles](https://www.openpolicyagent.org/docs/management-bundles),
  [decision logs](https://www.openpolicyagent.org/docs/management-decision-logs)).
  Cerbos loads policy from git or a database and expresses argument thresholds with
  step-up remediation ([Cerbos](https://docs.cerbos.dev/cerbos/latest/configuration/storage)).
- **Scores in policy.** AWS AgentCore Policy (Cedar) thresholds guardrail confidence scores
  and counts calls over time windows, but keys them to a caller-supplied session ID, which
  resets with every new session
  ([AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-temporal.html)).
- **Shadow before enforce.** AgentCore logs "decision flips" in log-only mode; IBM
  ContextForge has enforce / permissive / disabled plugin modes
  ([ContextForge plugins](https://ibm.github.io/mcp-context-forge/using/plugins/)).
- **Storage.** Small deployments keep everything in SQLite or Postgres (ContextForge,
  Phoenix, agentgateway); analytics move to ClickHouse only when aggregations get slow
  (Langfuse, Helicone) ([Langfuse](https://langfuse.com/self-hosting),
  [agentgateway DB](https://agentgateway.dev/docs/standalone/latest/documentation/setup/database.md)).
- **State that survives restarts.** Event sourcing: the append-only log is the record,
  state is rebuilt by replay, snapshots are an optimisation
  ([Azure pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)).
  `gate_runtime` already has `snapshot` / `rehydrate` per scope; replaying our log costs
  ~0.24 ms per call (measured).

## What the current MCP spec changes (2026-07-28)

Checked on the specification pages:

- **No protocol sessions, no GET stream, no DELETE.** `Mcp-Session-Id` is gone; each
  request is its own POST ([Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)).
  A caller's calls must be grouped by the authenticated principal, not a session.
- **Client name and protocol version travel in every request's `_meta`**; `Mcp-Method` and
  `Mcp-Name` headers must match the body. `clientInfo` is self-reported and must not be
  used for security decisions.
- **Servers must validate `Origin`** (403 if invalid) and authenticate every connection.
- **Authorization** ([2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)):
  the gateway is an OAuth 2.1 resource server, publishes RFC 9728 protected-resource
  metadata, accepts only tokens issued for itself (RFC 8707 audience) and never passes an
  agent's token upstream. Holding its own upstream credential is allowed, but one shared
  GitHub token makes every agent the same GitHub user.

The traffic logged so far (Python MCP client, remote GitHub MCP) used `2025-11-25`, so it
still had sessions; the gateway must handle both eras.

## Target design

```
remote agents ──HTTPS──► tunnel/TLS ──► PEP: gateway (validates JWT + Origin)
                                          │  principal = (iss, sub, client_id) from the token
                                          ▼
                      PDP: framework.py + decision rules (policy bundle @ revision)
                         ├─ static PIP: artifacts by sha256(tools/list) + policy digest
                         └─ dynamic PIP: GateScorer state per principal
                                 (snapshot every N calls; rebuilt by replay on restart)
                                          │ outcome: allow / alert / review / deny
                                          │ mode: observe | shadow | enforce
                                          ▼
                      store: messages, decisions, catalogs, artifacts, policies, snapshots
                                          │
                       new tools/list? ──► saved, strict default, static re-scan queued (GPU)
```

Decision rules have two kinds, as 800-207 and Cedar's forbid-overrides do: hard rules from
the policy (input-rule level 5, unscanned tool) that always win, and score thresholds on
`cell × B × L` for the rest. The thresholds are the organization's, kept in the policy
bundle; until it sets them, the scan's own bands stand in.

## Measured capacity (2026-10-15)

From [reports/experiments/gateway/scale](../../reports/experiments/gateway/scale/README.md):
scoring a call costs ~40 µs median and does not grow with callers (to 100k) or history; one
gateway process carries ~600 calls/s with httpx and collapses above ~64 requests in flight
(httpcore's connection pool), ~1,500 with aiohttp; processes scale linearly when each
caller is routed to the same one (8 aiohttp processes: ~9,000 calls/s with inline
scoring). With a 400 ms server, 4 aiohttp processes serve 1,024 agents with no added
latency. Scoring inline (before forwarding) is affordable; a separate scorer reading the
log decides within ~3 ms and keeps up with ~14,000 calls/s, but cannot block a call.

## Build order

**Stage 1 — research tier, one machine, no new services.**
1. SQLite store (standard library) plus a `blobs/sha256/` directory: `agents`, `catalogs`,
   `artifacts`, `scans`, `policies`, `calls`, `messages`, `decisions`, `snapshots`; the
   JSONL log stays as the raw record and is loaded into the store.
2. Dynamic state per caller (the principal as `gate_runtime`'s scope), snapshotted every N
   calls and restored on start-up, with the log tail replayed.
3. Decision rules as data and a `mode`; decision lines gain the outcome they *would* have
   had, still observe-only.
4. Protocol 2026-07-28 support in the log: `clientInfo` from `_meta`, callers grouped by
   principal when there is no session, `Origin` checked.

**Stage 2 — reachable by remote agents.** OAuth 2.1 resource server (JWT validation,
RFC 9728 metadata, audience check) against an identity provider (Keycloak, Auth0 or
Cloudflare Access) — the gateway side is built (`gateway/oauth.py`, checked end to end with
a stock MCP client against a test provider); the provider itself is still to choose; TLS through Cloudflare Tunnel or Caddy with the gateway still bound to
127.0.0.1; per-agent identities; least-privilege upstream credentials per route. Needs the
owner's choice of identity provider and hosting, and approval before a route holding a
real credential is exposed.

**Stage 3 — deployable.** Postgres instead of SQLite, OpenTelemetry export, ClickHouse only
if analytics get slow; shadow, then enforce, failing closed on high cells only; tools that
are denied for a caller removed from its `tools/list`.

## Sources

- NIST SP 800-207, Zero Trust Architecture, §3.1–3.3.1; NIST SP 800-162, ABAC.
- Kandala, Sandhu, Bhamidipati, "An Attribute Based Framework for Risk-Adaptive Access
  Control Models", ARES 2011.
- MCP specification 2026-07-28: versioning, Streamable HTTP, authorization.
- OPA, Cerbos, AWS AgentCore Policy, IBM ContextForge, agentgateway, Langfuse, Helicone,
  Arize Phoenix, Azure event-sourcing pattern — links inline above.
- MCP architecture papers: SMCP (arXiv 2602.01129), Securing MCP (2511.20920), ETDI
  (2506.01333), MCP Guardian (2504.12757), AgentBound (2510.21236), ScopeGate (2606.28679).
