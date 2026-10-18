# The dynamic layer: which dimensions, how to run them at scale, and what the log must contain

This report summarises the dimension work for the MCP dynamic layer. It covers:
- which runtime dimensions price strange usage of an MCP server's own tools, and how well each works;
- whether this is easy or hard to run for 10,000 agents;
- how the layer knows who sent a call;
- which log fields it needs.

Every claim comes from a test in this folder; the scenarios for each dimension are in [DIMENSIONS_GUIDE.md](DIMENSIONS_GUIDE.md).

## 1. The answer in brief

- **About ten dimensions do most of the work, on every server type tested.**
  - At ≤ 4 flagged agent-days per day, the set catches 71% of strange-usage episodes on average across 9 organisations (60–78% per organisation). At ≤ 2 per day it catches 57%.
  - The strongest single idea is "this agent passed a set of argument names it never passes to this tool". It ranked first in all 9 organisations.
- **It is easy to run at scale.** A plain Python prototype scores a call in about 40 µs (99th percentile 108 µs) and handles about 21,000 calls per second on one core. It needs about 72 KB of state per agent: 10,000 agents ≈ 720 MB. State is per agent, so it shards by agent id.
- **Knowing who sends the call matters as much as any dimension.** See section 5.
- **The log already has almost everything.** gateway-log/2 carries every field the selected dimensions need. Two things are missing:
  - the user behind the agent, from the OAuth token's claims;
  - typed fields for the few inputs the static scan keeps, so the layer does not need to read the full message.

## 2. Scope and rules

These rules shaped every test:

- **Not attacks.** The target is strange usage by legitimate agents: loops, over-fetching, fan-out, off-role tools, skipped steps, bursts, dormant agents waking, slow creep, recipient blasts, shared credentials, client switches and similar.
- **Request side only.** Nothing from the server's answers: no errors, response size or content.
- **No information the policy does not state.** The policy has no roles, teams or working hours, so peers are learned from behaviour and time is judged against the agent's own past.
- **General across MCP servers.** Arguments are read only through the static scan's input effects (`which`, `how_much`, `who`, `when`, `action`, `carried`), so no server-specific parsing is needed.
- **No rules.** Every dimension is learned from the agent's own history, its learned peers, or the whole organisation.

## 3. How it was tested

### Data

- **Worlds:** 9 simulated organisations on 3 servers (GitHub, Calendar, Slack), running one to two years with 1–4 million messages each. The variations were small, medium and large orgs, high churn, mostly bots, and repeat seeds.
- **Grounded in real data:**
  - roles and tool mixes from the repo's real persona corpora;
  - call order from real ordered sessions;
  - argument values from about 14,000 real calls;
  - input effects, tool operations and asset sensitivity from the static scan's reference results.
- **Simulated:**
  - who the agents are, when they work and how the org changes (hires, leavers, vacations, team and role changes, client upgrades, address changes, new assets, holidays, quarter-end);
  - the gateway-log/2 wire fields (address, client name, user agent, protocol handshakes, request bytes);
  - 21 kinds of strange usage at mild, medium and strong intensity.

### Dimensions

60 dimensions: 43 designed here, plus 17 taken from published feature definitions (bot detection, insider-threat datasets, fraud, UEBA). The research notes are in `results/logging_essence.md`.

### Scoring

- Every dimension is ranked against its own last 30 days, without labels.
- A rank above 99.5% is a risk event.
- Events add up per agent-day. An agent-day is flagged when at least two dimensions agree or one is extreme.
- Dimensions were chosen greedily: inside each organisation, and as one set across all nine. Detection is read at a fixed number of flagged agent-days per day.

### Generator mistakes found and fixed before the final numbers

Each of these was found because a result looked too good or too bad.

1. Strange usage was injected at random hours, which gave "hour of week" free credit. It now happens at the agent's normal hours.
2. Agents drifted into using nearly every tool, which made off-role use undetectable. They now keep their role's real tools, with rare legitimate exploration.
3. Some strange calls came as whole sessions of one tool, which gave order dimensions free credit. They now sit inside a normal session.
4. Two protocol dimensions ("call before initialize", "call before the tool list") were listed but never implemented. They are reported as **not measured**.

## 4. Results

### The core set across 9 organisations

| Order | Dimension | Log fields it needs |
|---|---|---|
| 1 | New set of argument keys for this agent and tool | tool, argument names |
| 2 | First time this agent touches an asset | `which` value |
| 3 | Client context: address + client + user agent, for this agent | wire fields |
| 4 | Same call repeated within 10 minutes | argument hash |
| 5 | Client addresses per hour | address |
| 6 | Calls today | agent, time |
| 7 | Items requested today | `how_much` values |
| 8 | New user agent | user agent |
| 9 | New recipients | `who` values (hashed) |
| 10 | Peer-rare first touch, new action value, peer-rare new tool | `which`, `action`, tool, learned peers |

**Detection of this set by kind** (mild / medium / strong):

| Caught | Kinds |
|---|---|
| ≥ 85% | shared credential (100%); slow creep (99%); fan-out (90–99%); client switch (92–97%); mode switch (91–93%); off-role tool (88–92%); recipient blast (87–89%); weekly habit (88–96%); sensitivity escalation (84–86%) |
| 60–95%, rising with intensity | page walk (58 / 90 / 93%); loop (59 / 76 / 96%); new origin (64 / 90 / 96%); cancel storm (32 / 80 / 93%); dormant agent waking (63%) |
| Weak | burst (11 / 33 / 82%); content dump (55–63%); long time span (48–60%); skipped workflow step (44–59%); over-fetch (33–54%); protocol skip (not truly measured); off-hours (3–7%) |

### Specialists

These are the best single dimension for one kind, worth adding when the alert budget allows:

| Kind | Dimension | Caught alone |
|---|---|---|
| Cancel storm | list-to-call delay | 99% |
| Cancel storm | retry after cancel | 97% |
| Weekly habit | monotone page/asset run | 97% |
| Loop | identical calls in session | 93% |
| Skipped workflow step | write as the first call | 92% |
| Off-role tool | next-tool rarity | 99% |
| Content dump | request bytes | 76% |
| Burst | sessions per hour | 73% |

Off-hours use is caught 71% by hour of week alone, but is lost once combined. It needs working hours stated in the policy.

### False alarms

Each selected dimension flags about 0.2% of benign messages or fewer. The worst legitimate triggers:

| Dimension | Legitimate trigger | Messages flagged |
|---|---|---|
| Next-tool rarity | role change | 5.3% |
| Addresses per hour | role change | 4.4% |
| Client context | client upgrade | 2.7% |
| Hour of week | night work | 2.7% |

### Which log fields are worth having

The cross-organisation selection was rerun with only the dimensions each field set allows (`ablation.py`):

| What the log keeps | Dimensions available | Detection at ≤ 2 / ≤ 4 per day |
|---|---|---|
| Everything | 60 | 56% / 70% |
| Argument names + request size + argument hash, **no argument values** | 39 | 51% / 64% |
| No wire fields (address, client, user agent) | 53 | 47% / 60% |
| Agent, session, time, method, tool + wire fields | 34 | 45% / 57% |
| Agent, session, time, method, tool only | 27 | 37% / 49% |

- Wire fields are worth about 10 points.
- Argument values are worth about 6 points beyond argument names, size and hash.
- A privacy-preserving log (names, hash and size, no values) keeps 64%.

## 5. Who sent the call?

### What the gateway can and cannot know

- **Always known: what the agent sends.** The tool, its arguments, when, in which session, from which client. That is the whole request.
- **Never known: what the person asked the agent to do.** The prompt and the agent's reasoning never reach the server. The dynamic layer judges the agent's behaviour, not the person's intent.
- **Who:** there are four separate identities, and the gateway needs to keep them apart:

  | Identity | What it is | Where the gateway gets it |
  |---|---|---|
  | **Agent app** | which program is calling (Claude Code, a company assistant, a CI bot) | OAuth `client_id` / `azp`; `gateway.client` from `initialize` |
  | **User** | whose behalf the call is made on | OAuth `sub` |
  | **Delegation chain** | an agent acting for a user, possibly through another service | the `act` claim (RFC 8693) |
  | **Session** | one connection of one agent | `mcp.session.id` |

The MCP authorization spec (2025-11-25) makes the first two available:

> The MCP server is an OAuth 2.1 resource server; the MCP client makes "protected resource requests on behalf of a resource owner".
>
> Every HTTP request carries `Authorization: Bearer <token>` ("even if they are part of the same logical session").
>
> The server "MUST validate that access tokens were issued specifically for them as the intended audience" (RFC 8707).

So a gateway that validates or introspects the token can log `client_id` (the agent app) and `sub` (the user, hashed). Today gateway-log/2 logs only `gateway.agent`, a name looked up from the token's hash. That is one identity, and it is only right if each person has their own token.

### Test: the same traffic, three kinds of identity

`identity_variants.py` rewrites the caller identity of the Calendar, Slack and GitHub organisations three ways. Everything is then rescored from scratch (`w2/run_identity.sh`, `identity_eval.py`). The detection set is the cross-organisation core set.

| Identity the gateway sees | Detection at ≤ 2 / ≤ 4 flagged identities per day |
|---|---|
| One token per person | 60% / 75% |
| One token shared by 10 people (a company assistant acting for many users; only the token is logged) | 61% / 71% |
| No stable identity: every session looks like a new caller | 12% / 12% (Slack + GitHub; the Calendar run exceeded the 32 GB memory limit) |

**What a shared token costs, by kind** (≤ 4 per day):

| Kind | Per person | Shared by 10 |
|---|---|---|
| Off-role tool | 91% | 65% |
| Sensitivity escalation | 90% | 71% |
| Client switch | 98% | 83% |
| Fan-out | 100% | 89% |
| Mode switch | 95% | 86% |
| New origin | 90% | 82% |

These are exactly the dimensions that ask "is this normal for this caller?": the token's "normal" becomes the union of ten people's normals. Kinds judged inside one session (loops, page walks, weekly habits) are unchanged.

A shared token also loses attribution: a flagged item now covers ten people, and the analyst has to work out which one.

**Without stable identity, almost everything is lost.** Only checks inside one session survive: loops 62%, page walks 55%, cancel storms 51%. Every first-time, per-day or client dimension needs a caller that persists across sessions.

### What to do

1. **Key every baseline by user + agent app**, from the token's `sub` and `client_id` (hash the user id).
   - Fall back to the agent app alone, then to the organisation.
   - Never use the session as the identity.
2. **If an agent platform calls with one service credential for many users** (OAuth client-credentials, so no `sub`), the gateway cannot know the user. The platform must pass it, for example as a signed header or a token-exchange `act` chain. Add this as an integration requirement and record it in the policy.
3. **Bots with no user:** the agent app itself is the identity.
4. **Cost at 10,000 users:** state is per (user, agent app) key. 10,000 users with 1–2 agent apps each is 10,000–20,000 keys × about 72 KB, so 0.7–1.4 GB in the Python prototype. That fits on one machine, and it shards by key.

## 6. Running it for 10,000 agents

### Measured

`engine_scale.py` runs a lean engine for the core set on a synthetic stream of 10,000 agents over 30 days (12 million calls), on one CPU core in plain Python, while other jobs shared the machine:

| Measure | Result | What it means |
|---|---|---|
| Throughput | about 21,000 calls/s | 10,000 agents × 500 calls/day is about 58 calls/s on average, so one core has more than 300× headroom |
| Latency per call | p50 40 µs, p99 108 µs (rare pauses up to 23 ms during pruning) | Fast enough to score inline, before the call is forwarded |
| Memory | about 72 KB per agent, about 720 MB for 10,000 | A compiled implementation would be several times smaller |
| Weekly peer computation | 12 s for 10,000 agents | Sparse matrix, top-5 cosine, in blocks |

### Why it scales

- **Per-call work is O(1).** Every dimension in the core set keeps small, bounded per-agent state:

  | State | Used for |
  |---|---|
  | Decayed fixed-size histograms | "how unusual is this number" |
  | Value → last-seen maps pruned after 90 days | "first time" checks |
  | Short deques | 10-minute and 1-hour windows |
  | A bounded recently-used set | recipients |

- **State is per agent,** so it shards by agent id across workers with no coordination.
- **Shared state is small and refreshed in batch:** learned peers (weekly) and "which agents touch which asset" (hourly is enough).

### Easy, medium and hard parts

| Part | Difficulty | Why |
|---|---|---|
| Per-agent counters, windows, novelty sets | Easy | O(1) per call, bounded memory, shards by agent |
| Label-free calibration (rank against the last 30 days) | Easy–medium | One streaming quantile sketch (t-digest or KLL) per dimension instead of storing 30 days of scores |
| Agent-day accumulation and the alert queue | Medium | A daily roll-up job; one item per agent-day for analysts |
| Learned peers | Medium | A weekly batch job. 10,000 agents take 12 s; at 100,000+ use blockwise or approximate nearest neighbours (LSH) |
| Identity (who is the user behind the agent) | Medium–hard | Needs the token's claims at the gateway; see section 5 |
| Static coverage of every MCP server | Medium–hard, operational | Each server needs a scan for input effects. New tools need a re-scan, triggered when the catalog hash changes. |
| Cold start, drift, re-anchoring | Medium | New agents lean on peers; baselines reset on known changes (team or role change) and at a periodic review |
| Tuning the alert budget per deployment | Medium | Detection depends on how many agent-days analysts can review |

### Suggested architecture

1. **Gateway:** already built. It writes gateway-log/2 and should add the identity claims and typed effect fields (section 7).
2. **Scorer:** in-process or a sidecar, keyed by agent identity, holding the per-agent state in memory with periodic snapshots.
   - Start observe-only: read the log stream, score and write risk events. It cannot break traffic and can be replayed.
   - Move inline only for dimensions that should gate calls.
3. **Daily roll-up:** risk events → agent-day items, ordered by the static layer's impact × sensitivity.
4. **Weekly batch:** learned peers and re-anchoring.

## 7. What the log needs

| Field | In gateway-log/2? | Used by | Note |
|---|---|---|---|
| Agent identity (`gateway.agent` from the token) | yes | everything | self-reported today unless tokens are configured |
| **User behind the agent** (token `sub`) and **agent app** (`client_id` / `azp`), delegation chain (`act`) | **no** | per-user baselines | see section 5; hash the user id |
| Session id, position in session, timestamp | yes | windows, order, sessions per hour | |
| MCP method, tool name, protocol version | yes | order, novelty, protocol checks | |
| Client address, client name/version, user agent | yes | client context, new origin, shared credentials | worth about 10 points of detection |
| Request size in bytes | yes | content dump | |
| **Argument names** (the key set) | inside `message` | the #1 dimension | log as its own field |
| **Argument hash** | no | repeated calls, loops | equality only, no content |
| **Typed static-kept values**: `which`, `how_much`, recipient count + hashes, time span, `action` | inside `message` | first touch, items today, recipients, mode | log as typed fields so the full message can be dropped or kept separately |
| Server responses (status, error, duration, response size) | yes | **not used** (out of scope) | keep for audit; the dynamic layer ignores them |

This is the pattern of other audit logs:
- CloudTrail logs structured request parameters.
- Kubernetes audit separates metadata from bodies.
- OWASP says to hash identifiers.

## 8. Limits

- **The traffic is synthetic.** Benign behaviour is grounded in real calls and the real static scan, but the strange usage was designed here. Dimension 1 partly benefits from that: when a strange call adds an argument the agent never passes, key novelty is exactly what notices it. Read the numbers as a ranking that held across nine different organisations, not as production rates.
- **The wire fields and the multi-agent setting are simulated.** The only real gateway-log/2 file has one agent, one address and one client.
- **Not measured:** the two protocol-order checks (not implemented here), and off-hours against stated working hours (the policy has none).
- **The scale test** is a Python prototype on a synthetic stream. It measures cost, not detection.

## 9. Next steps

1. Add the identity claims and typed effect fields to gateway-log/2.
2. Record real multi-agent traffic through the gateway (several tokens, users, clients) and rerun `eval2.py` on it.
3. Implement the two protocol-order checks.
4. Add working hours to the policy if off-hours use matters.
5. Build the scorer as an observe-only consumer of the log, with the core set first and specialists second.

## Files

| File | What it is |
|---|---|
| [DIMENSIONS_GUIDE.md](DIMENSIONS_GUIDE.md) | Every dimension with a scenario, its legitimate look-alike, its log fields and its cost |
| `world2.py`, `dims2.py`, `dims3.py`, `eval2.py`, `report2.py`, `w2/run_all.sh` | The 9-organisation dimension search |
| `results/dimension_search.md`, `results/eval2.json` | Full result tables |
| `ablation.py`, `results/ablation.json` | Log-field test |
| `identity_variants.py`, `identity_eval.py`, `w2/run_identity.sh`, `results/identity.json` | Identity test |
| `engine_scale.py`, `results/scale_10k.txt` | 10,000-agent cost test |
| `results/logging_essence.md` | What logs contain and what analytics use in other fields (CloudTrail, Kubernetes, SaaS, EHR, payments) |
| `results/SUMMARY.md` | The running summary of every experiment in this folder |
