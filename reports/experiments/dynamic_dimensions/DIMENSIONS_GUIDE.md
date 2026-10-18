# Dynamic-layer dimensions: what each one measures, with a scenario

This guide explains every dimension the dynamic layer should compute. For each one it gives a concrete scenario of the strange usage it catches, the legitimate behaviour that can look like it, the log fields it reads and what it costs at scale.

Scope is strange usage of an MCP server's own tools by legitimate agents (not attacks). Every dimension reads only:
- what the agent's request shows;
- the static scan's labels (tool operation, input effects);
- what the organisation's policy states.

Nothing comes from server responses.

Numbers come from the dimension search: 9 simulated organisations (GitHub, Calendar, Slack), 21 kinds of strange usage, 60 candidate dimensions (`results/dimension_search.md`). "Caught alone" is the share of episodes in which this dimension, by itself, rose into its own top 0.2% of scores. The full method and the honest limits are in [REPORT.md](REPORT.md).

## How every dimension works

Each dimension turns one request into a number, then asks how unusual that number is for this agent, compared with its own past.

- **Novelty dimensions** ("first time…") are priced by how often this agent produces anything new at all. A brand-new asset is a strong signal for an agent that touches the same five repos every day, and a weak one for an agent that browses widely.
- **Count and size dimensions** ("…per hour", "…today") use the share of the agent's past values at least as large as this one.

Scores never decide alone. They become risk events, the events add up per agent per day, and an agent-day is flagged when at least two dimensions agree or one is extreme. Analysts then see one item per agent-day instead of many per-call alerts.

## Part 1: the core set (works across every organisation tested)

### 1. New set of argument keys for this agent and tool

- **What it measures:** the names of the arguments a call passes, never their values, as a set, keyed by tool. It fires when this agent has never passed this combination to this tool.
- **Scenario:** a Calendar scheduling agent has called `create-event` thousands of times with `calendarId`, `summary`, `start` and `end`. One afternoon it calls `create-event` with `attendees` and `sendUpdates` as well. It has never sent those keys, and the call invites 40 people and emails all of them.
- **Also catches:**
  - page walks: a `page` argument appears for the first time;
  - off-role calls: a tool never used means a key set never used;
  - mode switches.
- **Legitimate look-alike:** a role change, or a new feature in the agent. False alarms are 0.8% of messages in the 30 days after a role change, and 0.02% of benign messages overall.
- **Evidence:**
  - Ranked first in all 9 organisations.
  - Caught alone: off-role tools 90%, recipient blasts 89%, mode switches 88%, page walks 86%.
  - This is the "attribute presence" model from web-request anomaly detection (Kruegel & Vigna, CCS 2003).
- **Log fields:** tool name and argument key names.
- **Cost:** a small set of key-set hashes per agent and tool.

### 2. First time this agent touches an asset

- **What it measures:** the value of the input the static scan marks as `which` (repository, channel, calendar), as an opaque name. It does not matter whether the asset is in the policy register.
- **Scenario:** a Slack assistant that has served the `#vireo-trial-ops` channel for eight months reads `#vireo-unblinding` for the first time. Its peers never read it either; the peer-rare version (dimension 10) prices that in.
- **Also catches:**
  - fan-out: twelve repos the agent never used, in one session;
  - slow creep: one new out-of-team repo a week.
- **Legitimate look-alike:** a team transfer (0.7%) and new hires. A new asset that the whole team starts using shows up as "first touch" for everyone at once; the peer-rare version damps it.
- **Evidence:** caught alone: fan-out 96%, slow creep 91%, sensitivity escalation 87%. Benign alerts 0.03%.
- **Log fields:** the `which` value, from the static scan's input effects.
- **Cost:** asset → last-seen day per agent, pruned after 90 days.

### 3. Client context: address + client name + user agent, for this agent

- **What it measures:** how surprising this combination of client address, client software name/version and user agent is for this agent. It uses a smoothed probability per field, so a value seen often scores near 0 and a never-seen value scores high (Freeman et al., NDSS 2016).
- **Scenario:** the token of the `pv-assistant` agent normally arrives from `10.2.x.x` with `claude-code/1.4` and `python-httpx`. At 14:02 the same token arrives from `203.0.x.x` with `langchain-mcp-adapters/0.9` and `node-fetch`, while the original is still working. Two programs are now holding one credential.
- **Also catches:**
  - a client switch: an agent suddenly driven by a raw `python-requests` script;
  - a new origin.
- **Legitimate look-alike:** a client upgrade (2.7% in the 3 days after one) and a redeploy to a new host (1.8%). Version bumps are the main false-alarm source, so compare the client name without the minor version.
- **Evidence:** caught alone: shared credential 100%, client switch 82%, new origin 74%.
- **Log fields:** `client.address`, `gateway.client` (from `initialize`) and `user_agent.original`, all already in gateway-log/2.
- **Cost:** three small counters per agent.

### 4. Same call repeated within 10 minutes

- **What it measures:** how many identical calls (same tool, same arguments) this agent sent in the last 10 minutes. Comparing calls needs only a hash of the arguments, not the arguments themselves.
- **Scenario:** a GitHub CI agent stuck in a retry loop calls `get_pull_request_status` for PR 412 forty times in four minutes.
- **Also catches:** cancel storms, where the same call is re-sent after each cancellation.
- **Legitimate look-alike:** polling bots and client retries. Real benign callers repeat an identical call 8–16% of the time within their last 10 calls (measured on the live corpora), which is why the threshold is per agent, not fixed.
- **Evidence:** caught alone: loops 93%, cancel storms 88%.
- **Log fields:** a hash of the arguments.
- **Cost:** a 10-minute deque per agent.

### 5. Client addresses per hour

- **What it measures:** how many different client addresses this agent's token used in the last hour.
- **Scenario:** a calendar agent's token is used from the office network, then a cloud host, then a home network within 40 minutes. It is being used in three places.
- **Legitimate look-alike:** laptops moving between networks, and night work. Role changes showed 4.4% in the simulation; this is the noisiest core dimension and needs the peer/self comparison.
- **Evidence:** caught alone: shared credential 74%, new origin 71%.
- **Log fields:** `client.address`.
- **Cost:** a 1-hour deque per agent.

### 6. Calls today

- **What it measures:** the agent's call count so far today, against its own past days.
- **Scenario:** a release-manager agent that makes about 30 calls a day makes 600 by noon, because a misconfigured scheduler starts it every minute.
- **Evidence:**
  - Caught alone it is moderate (bursts 35%), because one burst is diluted over a day.
  - It earns its place by corroborating other signals in the agent-day sum.
- **Log fields:** agent id and timestamp.
- **Cost:** one counter plus one fixed-size histogram per agent.

### 7. Items requested today

- **What it measures:** the sum of the agent's `how_much` input values today (page size, limit, count), against its own past days.
- **Scenario:** a developer agent normally reads about 150 issues a day. Today it pages `list_issues` with `per_page=100` through 40 pages, which is 4,000 issues. No single call is unusual (GitHub caps a page at 100), but the day is.
- **Evidence:**
  - Caught alone: over-fetch 41%, page walks 35%.
  - Over-fetch is still one of the weakest kinds overall (33–54%), because one call cannot ask for much more than normal when the server caps page size.
- **Log fields:** the `how_much` values.
- **Cost:** one counter plus one histogram per agent.

### 8. New user agent

- **What it measures:** a user-agent string this agent has never used.
- **Scenario:** an agent that has only ever sent `python-httpx/0.28` starts sending `python-requests/2.32`. Someone is running a script with its token.
- **Evidence:**
  - Caught alone: shared credential 92%, client switch 83%.
  - Picked in 8 of 9 organisations.
  - Zero false alarms on benign traffic in the simulation. In a real deployment a client upgrade changes the version, so compare the product name.
- **Log fields:** `user_agent.original`.
- **Cost:** a small set per agent.

### 9. New recipients

- **What it measures:** recipients (the input the static scan marks as `who`) that this agent has never addressed.
- **Scenario:** a calendar agent that books meetings for one team invites 30 external addresses it has never invited.
- **Evidence:**
  - Caught alone it is weak (9%), because a blast often re-uses some known addresses.
  - In combination it lifts recipient blasts to 87–94%, together with the argument-key set and the recipient count.
- **Log fields:** the `who` values, hashed.
- **Cost:** a bounded recently-used set per agent (2,000 entries).

### 10. Peer-rare first touch, new action value, peer-rare new tool

Three refinements that use learned peers. Peers are the 5 agents whose tool and asset usage is most similar, recomputed weekly. They are learned rather than declared, because the policy has no roles.

- **Peer-rare first touch:** a first touch of an asset that none of the agent's peers use either. For example, a web-team agent opens the grid-ops configuration repo. Caught alone: fan-out 96%, slow creep 90%, sensitivity escalation 86%.
- **New action value:** a value of an `action` input never used by this agent. For example, `sendUpdates=all` from an agent that always sent `none`, or `visibility=public`. Weak alone (19%), useful in combination.
- **Peer-rare new tool:** a tool neither the agent nor its peers use. For example, a triager agent calls `merge_pull_request`. Caught alone: off-role tools 89%.

## Part 2: specialists (best for one kind, worth adding when the alert budget allows)

| Dimension | Kind | Scenario | Caught alone | Legitimate look-alike |
|---|---|---|---|---|
| Identical calls in session | Loops | The same `search-events` query 100 times in one session | 93% | client retries (1.1% after a role change) |
| Sessions started per hour | Bursts | 30 sessions in an hour from an agent that opens 2 | 73% | night incident work (0.9%) |
| Monotone page/asset run | Weekly habit, enumeration | Every Monday at 10:00, pages 1→20 of `list_commits` across repos in order | 97% | — (0.03% benign) |
| List-to-call delay | Cancel storm | The first call follows the tool list in 5 ms instead of the agent's usual 2–8 s | 99% | — |
| Retry after cancel | Cancel storm | The same call re-sent right after the client cancelled it | 97% | — |
| Write as the first call | Skipped workflow step | `merge_pull_request` or `delete-event` with no read before it in the session | 92% | role changes (1.2%) |
| Next-tool rarity | Off-role tool, skipped step | A step that never follows the previous one for this agent | off-role 99% | role changes (5.3%), the noisiest specialist |
| Request bytes | Content dump | A message body 40× the agent's usual size | 76% | team transfer (1.2%) |
| First address | New origin | The token appears from a cloud address range never seen | 100% | new network (0.8%) |
| First client name | Dormant agent waking | An agent idle for 3 months returns with a different client version | 66% | client upgrade (0.4%) |
| Hour of week | Off-hours | A daytime agent working at 03:00 on a Sunday | 71% alone, 3–7% in combination | night work (2.7%). Becomes useful only if the policy states working hours. |

## Part 3: tested and not selected

These were tested across all 9 organisations and never earned a place in the cross-organisation set:

- Entropy of assets and tools per hour.
- CUSUM on daily calls and on new edges.
- Gap memory coefficient, Fano factor.
- Weekly tool-mix shift, weekly scope shift.
- Sensitivity above the agent's usual maximum. Sensitivity belongs in "how bad", not "how strange".
- Share of unpopular targets, revisit ratio, distinct recipients per day.
- Peer next-tool model, trigram order.
- Dormancy gap. The return of a dormant agent was better caught by its changed client.
- Session length, parallel sessions, initialisations per hour.

**Not measured:** "call before the tool list" and "call before initialize" were listed but not implemented in this run. In the simulation they would be trivially perfect, because benign sessions always initialise, so nothing could be learned. On real traffic they are cheap and worth adding.

## Scenarios for each kind of strange usage

All numbers are for the cross-organisation set at ≤ 4 flagged agent-days per day.

| Kind | Scenario | Caught by | Detected (mild / medium / strong) |
|---|---|---|---|
| Shared credential | One token used by two programs at once, from two addresses | client context, new user agent, addresses per hour | 100 / 100 / 100% |
| Client switch | The agent's token driven by a raw script for a day | new user agent, client context | 94 / 92 / 97% |
| New origin | Calls from a never-seen cloud address | client context, addresses per hour | 64 / 90 / 96% |
| Fan-out | One session touches 5 / 12 / 30 assets | first touch (self and peers) | 90 / 93 / 99% |
| Slow creep | One new out-of-team asset a week for 6 weeks, kept up for 12 weeks | first touch, peer-rare first touch | 99% |
| Sensitivity escalation | Normal work on another team's sensitive asset | peer-rare first touch | 84 / 86 / 85% |
| Off-role tool | A tool outside the role, inside a normal session | new key set, peer-rare new tool | 88 / 92 / 92% |
| Mode switch | An `action` input set to a value the agent never uses | new key set, new action value | 93 / 91 / 93% |
| Recipient blast | 6 / 30 / 150 recipients on one call | new key set, new recipients | 87 / 89 / 87% |
| Weekly habit | A 15-call enumeration every week for 4–16 weeks | items today, first touch | 89 / 88 / 96% |
| Page walk | Pages 1→10 / 30 / 100 of one list | new key set, items today | 58 / 90 / 93% |
| Loop | The same call 5 / 20 / 100 times | identical calls | 59 / 76 / 96% |
| Cancel storm | 4 / 12 / 40 call-cancel-retry cycles | identical calls, calls today | 32 / 80 / 93% |
| Burst | 3 / 10 / 30 sessions in one hour | calls today, addresses per hour | 11 / 33 / 82% |
| Dormant agent waking | First calls after 2–4 months of silence | client context, new user agent | 63% |
| Content dump | A message body 5× / 40× / 300× its usual size | request bytes (specialist), new key set | 55 / 63 / 62% |
| Long time span | A query over 60 / 400 / 3,000 days | new key set | 55 / 60 / 48% (weak) |
| Skipped workflow step | Writes with no read first | specialist: write-first 92% alone | 44 / 59 / 53% (weak in the general set) |
| Over-fetch | Page size or limit 3× / 10× / 50× normal | items today | 33 / 41 / 54% (weak) |
| Protocol skip | Calls with no initialize or tool list | sessions per hour (the direct check was not implemented) | 6 / 12 / 59% (not truly measured) |
| Off-hours | A normal session at 01:00–05:00 local time | hour of week only alone | 5 / 7 / 3% (needs policy working hours) |
