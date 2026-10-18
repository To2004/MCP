# Dynamic layer dimensions: summary

This is a one-page summary of what the dynamic layer should measure, how well each choice works, and what it needs from the log. Details are in [HIGH_LEVEL.md](HIGH_LEVEL.md) (no call content), [REPORT.md](REPORT.md) (full report, scale and identity) and [DIMENSIONS_GUIDE.md](DIMENSIONS_GUIDE.md) (every dimension with a scenario).

## Scope

- **What is detected:** strange usage of an MCP server's own tools by legitimate agents, not attacks. That covers loops, bursts, over-fetching, fan-out, off-role tools, skipped workflow steps, off-hours use, dormant agents waking, slow scope creep, shared credentials, client switches and protocol misuse.
- **What it may use:** only the agent's requests, the static scan's labels and what the policy states. No server responses.
- **High level:** never look inside a call (no tool inputs, no specific asset). The layer may use:
  - the tool;
  - whether it reads, writes, removes or lists;
  - the asset *type* taken from the tool's name;
  - time, volume and sessions;
  - a general client and network (client family, /16 range).

## How it was tested

- **Data:** 9 simulated organisations on GitHub, Calendar and Slack, running one to two years with 1–4 million messages each. They are built from the repo's real calls (roles, call order, argument values) and the real static scan's labels.
- **Strange usage:** 21 kinds, each at mild, medium and strong intensity. The simulated organisations also contain legitimate changes (new hires, role changes, team transfers, client upgrades, network changes, vacations), so false alarms can be measured.
- **Dimensions:** about 100 candidates, from our own design, published feature catalogues (bot detection, insider threat, fraud, log anomaly detection) and vendor practice (Microsoft Sentinel, Elastic, AWS, Splunk, Exabeam).
- **Scoring:**
  - Each dimension is compared with the agent's own past without labels.
  - Risk is added up per agent per day.
  - Detection is measured at a fixed analyst load: at most 2 or 4 flagged agent-days per day.
- **Generator flaws:** six were found and fixed along the way, for example strange usage at random hours and agents drifting into every tool. Each had been giving some dimension free credit.

## Results

| What the dimensions read | Detection at ≤ 2 / ≤ 4 flagged agent-days per day |
|---|---|
| Exact content: asset names, argument names and values | 57% / 71% |
| **High level + general client and network** | **50% / 60%** |
| High level, tool / time / volume only | 39% / 50% |

Staying at the high level costs 7–11 points. The general client and network fields are worth about 10. The research agrees: leaving content out barely changes average accuracy, but the loss shows at strict alert budgets.

## The recommended high-level set

| # | Dimension | Catches |
|---|---|---|
| 1 | Next-tool rarity for this agent | Off-role tools, skipped steps |
| 2 | Same tool repeated within 10 minutes | Loops, page walks |
| 3 | New network range for this agent | New origin, shared credential |
| 4 | New client family for this agent | Client switch, shared credential |
| 5 | Calls today against its own days | Bursts, storms |
| 6 | Writes today against its own days | Write bursts |
| 7 | First use of a tool few agents use | Off-role tools |
| 8 | Session duration against its own sessions | Stuck or runaway sessions |
| 9 | Network ranges in the last hour | Shared credential |
| 10 | Client families in the last hour | Shared credential, client switch |
| 11 | Asset types today | Reaching beyond usual kinds of object |

Each flags about 0.2% of benign calls or less. The noisiest are next-tool rarity (5.3%) and writes today (3.1%) in the month after a legitimate role change.

**Specialists** to add when there is room for more alerts:

| Dimension | Kind | Caught alone |
|---|---|---|
| Call without `initialize` | Protocol skip | 100% at 0% benign |
| List-to-first-call delay | Cancel storm | 99% |
| Per-tool calls per minute | Page walk | 94% |
| A write as the session's first call | Skipped workflow step | 92% |
| Gap regularity of one tool | Weekly habit | 88% |
| Sessions per hour | Burst | 73% |
| First write from a new client/network combination | Client switch | 64% at 0.01% benign |

## What to remove

- **Weak:** dormancy gap, write share, weekly peer deviation, weekly tool-mix shift, burstiness, CUSUM, gap memory, tool entropy, distinct tools per day.
- **Duplicates:** calls per minute and per 10 minutes, 3-step order, op-type transition, user-agent family (merge with client family).
- **Doesn't fit MCP:** the in-session credential-sharing rule. A second program opens its own session.
- **Never fired:** gap between two specific tools.
- **Research-recommended dimensions that are good alone but redundant here:** session count-vector distance, whole-session pattern rarity, peer next-tool, per-tool rate. Use them as substitutes, not additions.

## What the high level cannot see

| Kind | Caught at high level | Fix, if it matters |
|---|---|---|
| Normal work on another team's sensitive asset | 3–6% | A hash of the asset name (84–86% with exact content) |
| Over-fetching | 8–9% | Request size in bytes or the size input (33–54% with exact content) |
| Content dump | 17–30% | Request size in bytes (76% alone with exact content) |
| Mild fan-out | 6% | A hash of the asset name (90–99% with exact content) |
| Off-hours | 7–10% | Working hours written in the policy |

## Who is calling, the log, and scale

- **Identity matters as much as any dimension.**
  - With one token per person: 75%.
  - With one token shared by 10 people: 71%, and off-role detection drops from 91% to 65%.
  - With only a session id: 12%.
  - The MCP authorization spec already carries both the agent app (`client_id`) and the user (`sub`) in the OAuth token on every request. Log both, hash the user, and keep every baseline per user + agent app.
- **The log.** gateway-log/2 already has everything the high-level set needs. Add the user and agent app from the token. If the light fields above are wanted, add an asset-name hash and the request size as their own fields.
- **Scale is easy.** A Python prototype handled 10,000 agents at about 21,000 calls/s on one core, 40 µs per call (108 µs at p99), with about 72 KB of state per agent and 12 s for the weekly peer computation. State is per agent, so it shards by agent.

## Limits

- **The traffic is synthetic.** It is grounded in real calls and the real static scan, but the strange usage was designed here. Read the numbers as a ranking that held across 9 different organisations, not as production rates.
- **Not yet measured on real traffic:** the general client and network dimensions. The only real gateway log has one agent, one address and one client.
- **Next step:** record real gateway traffic with several agents, users and clients, then rerun the evaluation on it.

## Where things are

| File | Content |
|---|---|
| [HIGH_LEVEL.md](HIGH_LEVEL.md) | High-level set, specialists, removals, research findings |
| [REPORT.md](REPORT.md) | Exact-content results, identity test, log-field test, scale test, architecture |
| [DIMENSIONS_GUIDE.md](DIMENSIONS_GUIDE.md) | Every exact-content dimension with a scenario and its look-alike |
| `results/high_level_v2.md`, `results/dimension_search.md` | Full result tables |
| `results/logging_essence.md` | What logs contain and what analytics use in other fields |
| `results/SUMMARY.md` | Running log of every experiment in this folder |
