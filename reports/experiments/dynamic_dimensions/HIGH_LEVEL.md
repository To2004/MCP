# High-level dimensions: what works without looking inside any call

This guide covers the dynamic layer when it may not read call content: no tool inputs, no specific asset, no exact address. It may see only:
- which tool was called;
- whether that tool reads, writes, removes or only lists (from the static scan);
- the type of asset the tool works on, taken from the tool's name (`search_repositories` → repository);
- time, volume and sessions;
- optionally, a general client and network: client software family without version, user-agent family, /16 network range.

## The answer

| What the dimensions read | Detection at ≤ 2 / ≤ 4 flagged agent-days per day |
|---|---|
| Exact content (earlier search: asset names, argument names and values) | 57% / 71% |
| **High level with general client and network (pool A)** | **50% / 60%** |
| High level with tool, time and volume only (pool B) | 39% / 50% |

- Staying at the high level costs 7–11 points. The general client and network fields are worth about 10.
- Same 9 simulated organisations, 21 kinds of strange usage at 3 intensities, and the same label-free scoring as the exact-content search (`results/high_level_v2.md`).
- The research agrees with the size of the gap. Content-free detection barely loses on overall accuracy, but loses at strict alert budgets. Unix masquerade detection, for example, falls from about 60% to under 50% hits at 1% false alarms without command arguments (Maxion, DSN 2003).

## The recommended high-level set (pool A, in order of selection)

| # | Dimension | What it notices | Scenario | Benign alerts |
|---|---|---|---|---|
| 1 | **Next-tool rarity** for this agent | A step this agent never takes after the previous one | A triager agent goes from `list_issues` straight to `merge_pull_request` | 0.20% (5.3% for a month after a role change) |
| 2 | **Same tool repeated within 10 minutes** | Loops, page walks, polling gone wrong | 40 calls of `list_commits` in 4 minutes | 0.14% |
| 3 | **New network range** (/16) for this agent | New origin, shared credential | The token suddenly arrives from a cloud range | 0.00% (0.8% on a legitimate network change) |
| 4 | **New client family** for this agent | Client switch, shared credential | `claude-code` → a `python-requests` script | 0.00% |
| 5 | **Calls today** against its own days | Bursts, storms | 600 calls by noon from an agent that makes 30 a day | 0.20% |
| 6 | **Writes today** against its own days | Write bursts, workflow changes | A read-mostly agent writes 40 times in a day | 0.18% (3.1% after a role change) |
| 7 | **First use of a tool, priced by how many agents use it** | Off-role tools | An agent calls `delete-event`, which almost nobody in the org uses | 0.02% |
| 8 | **Session duration** against its own sessions | Stuck or runaway sessions | A 3-minute agent holds a session open for 2 hours | 0.16% |
| 9 | **Network ranges in the last hour** | Shared credential | One token from 3 networks within an hour | 0.16% |
| 10 | **Client families in the last hour** | Shared credential, client switch | Two different clients on one token at once | 0.03% |
| 11 | **Asset types today** | Reaching beyond its usual kinds of object | A calendar-reading agent also touches accounts and calendars today | 0.21% |

**Without client or network fields (pool B)** the best set is:
next-tool rarity, same tool repeated, calls today, org-rare new tool, impact added up today, writes today, calls per hour, new asset type, cancellations per hour, asset types today, days since this tool was last used, peer-rare new tool. It reaches 50% at ≤ 4 per day.

## Specialists: add when the alert budget allows

| Dimension | Kind | Caught alone | Benign alerts |
|---|---|---|---|
| Call without `initialize` | Protocol skip | 100% | 0.00% |
| Delay from tool list to first call | Cancel storm | 99% | 0.21% |
| Per-tool calls per minute | Page walk | 94% | 0.16% |
| A write as the session's first call | Skipped workflow step | 92% | 0.18% |
| Regularity of the gaps between uses of one tool | Weekly habit, polling | 88% | 0.18% |
| Session count-vector distance (Landauer et al. 2024) | Page walk, loop | 81% / 67% | 0.15% |
| Sessions started per hour | Burst | 73% | 0.19% |
| Hour of week | Off-hours | 71% alone | needs working hours in the policy to be usable |
| First write from a client/network combination seen < 7 days | Client switch | 64% | 0.01% |

Several research-recommended dimensions were implemented and tested. They are strong alone but **redundant** with the set above: added on top of it, each was neutral or cost up to 3 points at a fixed alert budget. They are valid substitutes, not additions:
- session count-vector distance;
- per-tool rate per minute;
- next tool judged against peers (t-STIDE+ style);
- whole-session pattern rarity;
- the new-combination-on-write rule.

## Remove

These were never chosen and are weak, redundant or noisy:

| Remove | Why |
|---|---|
| Dormancy gap, write share today, weekly peer deviation, distinct tools today, non-call share, removes today | Weak alone (≤ 31% for any kind except slow creep) |
| Burstiness, CUSUM on calls, gap memory, tool entropy, weekly tool-mix shift, session tool diversity | Weak; slow creep is inflated for every dimension because its episodes last 12+ weeks |
| Calls per minute, calls per 10 minutes, next-tool trigram, op-type transition, org-rare new asset type | Duplicate a stronger dimension (calls per hour, next-tool rarity, new tool) |
| User-agent family new | Duplicates client family new (both 83% on client switch); fold them into one "client" field |
| Gap between two specific tools | Never fired usefully (0%) |
| In-session credential-sharing rule (> 1 network and > 1 client in one session) | Doesn't fit MCP: a second program opens its own session instead of reusing one |
| Networks inside one session | Simulation artifact (simulated laptops switch networks mid-session); retest on real traffic |

## What the high level cannot see

| Kind | High-level detection at ≤ 4 per day | Why |
|---|---|---|
| Sensitivity escalation (normal work on another team's sensitive asset) | 3–6% | Nothing changes except **which** asset. No published work recovers this without asset identity. |
| Over-fetch | 8–9% | The size lives in the inputs |
| Content dump | 17–30% | The size lives in the inputs |
| Mild fan-out | 6% (strong 71%) | Several assets of the same type look like one |
| Off-hours | 7–10% | Needs working hours stated in the policy |

If any of these matter, two light fields would bring most of it back without reading content:
- a **hash** of the asset name. This is enough for "first time this agent touches this asset"; the exact-content search caught fan-out at 90–99% and escalation at 84–86% with it.
- the **request size in bytes**. Content dumps were caught 76% with it.

## What the research says

| Finding | Evidence |
|---|---|
| Counts per session or window are the most robust content-free family | Landauer et al. 2024: event-count-vector distance F1 93–96 on standard log benchmarks; "event position in sequences is less relevant than event occurrence frequencies". Maxion & Townsend 2002: order-free command frequencies beat sequence methods. |
| Order works with short context and when conditioned on who | DeepLog's n-gram baseline was best at N = 1. Long n-grams collapse (Landauer: 2-gram F1 85 vs 10-gram 34). Nolle et al. 2018: conditioning on the actor added about 0.2 F1. |
| Rarity against self, peers and the tenant is what vendors use | Microsoft Sentinel UEBA, Elastic ML jobs, GuardDuty, Exabeam, Datadog new-value rules |
| Content-free detection loses at strict budgets, not on average | Maxion 2003; Zhang et al., AAAI 2020: recall at 0.1% false positives 1.6% vs 67% |
| Avoid | Off-hours baselined on the agent itself (machines run around the clock; daylight-saving noise), ungated first-time flags, long n-grams and full HMMs, organisational attributes as features (use them to form peers instead), random train/test splits |

The full research notes, with sources, are in the session's research report. The vendor and paper links are in `results/logging_essence.md` and `REPORT.md`.

## Files

| File | What it is |
|---|---|
| `dims4.py`, `dims5.py`, `dims6.py` | The high-level dimensions: tool / time / volume / asset type, more session and protocol dimensions, and the research-recommended ones |
| `high_level_eval.py` | Pools A and B: selection, detection by kind and intensity, best single dimension per kind, false alarms |
| `results/high_level_v2.md`, `results/high_level_v2.json` | Full result tables |
| `w2/run_high_level.sh` | Reruns the high-level pipeline |
