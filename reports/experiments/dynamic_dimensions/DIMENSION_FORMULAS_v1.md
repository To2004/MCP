# Dynamic layer: one formula per dimension (v1)

*Saved copy of v1, kept for reference. The current design is v3: [DIMENSION_FORMULAS.md](DIMENSION_FORMULAS.md). The engine still runs v1 with `"design": "v1"` in a route's behaviour policy.*

Each dimension gives a score `s` between 0 and 1, using only fractions and averages: no bits. The strangest dimension sets the call's dynamic multiplier, which always lies between 0.7 and 5. Ordinary calls stay at or below 1, so they do not flare, while clearly strange calls get close to 5. With a static score of 1–5, the risk stays between 0.7 and 25 by its shape alone, with no rounding or clipping. Every formula compares the agent only with his own last 90 days.

The design was stress-tested on all 9 simulated organisations (GitHub, Calendar, Slack; about 25 million messages) and on 33 hand-made edge cases. The results are under [Stress test](#stress-test).

## Step 1: a score per dimension

**1. "More than his usual"**, for counts, durations and sizes:

```
s = (value + u) / (value + u + 2 × (his average + u))
```

The unit `u` is 1 call, 1 minute or 1 KB. It stops tiny absolute changes from counting (0 → 50 bytes stays ordinary) and makes 0 / 0 impossible.

**2. "Rarer than his usual"**, for which tool, which asset and what time. It asks **how many times a day he normally does something this rare**:

```
e = (his calls on things at most this common + 1) / (his active days + 1)       "times per day"
s = c / (1 + 2 × e)                                                              c = 0.9 for tools, 1 otherwise
```

- For something he has never used, the count is how often he started using something new (not counting his warm-up).
- The ceiling `c` = 0.9 keeps a first-time tool near ×3.2–3.6.
- A once-every-two-days thing is ordinary (s = 0.5, ×1). Once in 10 days gives about ×2.9. Never gives the top.

**3. Policy rule:** broken → `s` = the rule's value. The default is 0.9 (×3.6); protocol skip is 0.7 (×1.9). Not broken → the rule does not take part.

**Why "times per day" and not a plain share.** An agent making 100 calls a day hits a "1 in 100" thing about once a day by chance. With a plain share, 6–16% of ordinary agent-days flared to ×3 or more. Counting "how many times a day he does something this rare" halved that, to 3–10%.

| What happened | s | M |
|---|---|---|
| His average, or something he does twice a day | 0.33 | 0.89 |
| **Twice his average, or something he does every other day** | **0.50** | **1.00** |
| 4× his average, or once in 4 days | 0.67 | 1.73 |
| 10× his average, or once in 10 days | 0.83 | 2.89 |
| Never (long history) | 0.9–0.98 | 3.6–4.7 |

## Step 2: the call's dynamic multiplier

The strangest dimension decides:

```
S = the largest s over the call's dimensions
M = 5   ^ (2S − 1)     when S ≥ 0.5        the edge of ordinary → 1,   the strangest possible → towards 5
M = 0.7 ^ (1 − 2S)     when S < 0.5        familiar → below 1,          everything very familiar → towards 0.7
```

**Warm-up.** For a user's first 5 calls (or 10, a policy choice), `M` = 1 because there is no history yet.

## Step 3: the risk

```
R = R_static × M          R_static 1–5,  M 0.7–5   →   R between 0.7 and 25
```

## The dimensions

### Timing

| # | Dimension | Formula |
|---|---|---|
| 1 | Calls in the last hour | more than usual: n = his calls in the last 60 minutes, u = 1 call |
| 2 | Session length | more than usual: minutes since the session started, against his usual, u = 1 minute |
| 3 | Time of day | rarer than usual: e = (his calls within one hour of this time + 1) ÷ (his active days of this kind + 1), counting weekdays and weekends separately |
| 4 | Burst | rule: more than 20 calls in a minute → 0.9 |
| 5 | Problematic sequence | rule → 0.9: a write after reading a different sensitive asset; a write to a sensitive asset not read in 7 days; a merge with no review |

Removed, on 2026-10-19:
- **Same tool in 10 minutes.** Removing it changed overall detection by about 1 point. Loops still reach ×2 or more 55% of the time instead of 69%.
- **The fixed "session longer than 10 minutes" rule.** Real desktop clients keep one session open for hours, so it fired all day. It was replaced by session length against his usual.

### Footprint

| # | Dimension | Formula |
|---|---|---|
| 6 | Tool | rarer than usual, ceiling 0.9: a first-time tool gives about ×3.2–3.6 |
| 7 | Asset | rarer than usual: a never-touched asset gives about ×4.4 |

### Origin

| # | Dimension | Formula |
|---|---|---|
| 8 | First-time network | rule: a /16 range he has never used → 0.9. It uses the broader range because the exact IP changes all the time on mobile networks, carrier-grade NAT and cloud servers. |
| 9 | First-time client family | rule: a client name, version dropped, he has never used → 0.9 |

### Request

| # | Dimension | Formula |
|---|---|---|
| 10 | Request size | more than usual, per tool: u = 1 KB |
| 11 | Request too big | rule: over 10 KB → 0.9 |
| 12 | Protocol skip | rule: a tool call in a session that never sent `initialize` → 0.7 (×1.9). It applies only if he normally sends `initialize` (at least half of his sessions), so stateless clients do not flare on every call. |

## Stress test

### Edge cases (33 hand-made)

**Held: ordinary stays at or below ×1**

| Case | M |
|---|---|
| Ordinary day | 1.0 |
| Night-shift worker | 1.0 |
| Brand-new agent, first 12 calls | 1.0 |
| Desktop client, one session open all day | 1.0 |
| New exact IP on every call, same /16 | 1.0 |
| Requests always 0 bytes, no crash | 1.0 |
| 0 bytes, then one request of 50 bytes | 1.0 |
| Bot at its usual rate | 1.0 |
| Bot +20% | 1.0 |
| Low-volume agent (1 call a day) | 1.0 |
| Agent back after 120 days away | 1.0 |
| Agent using 26 tools evenly | 1.0 |
| Bot posting to 300 channels in rotation | 1.0 |
| Calls arriving out of order | 1.0 |
| Stateless client that never sends `initialize` | 0.97 |

**Held: strong things flare**

| Case | M |
|---|---|
| A 1 GB request | 5.0, never above |
| Travel, first day | 4.4, then 1.8 on day 2 and 1.0 by day 5 |
| A never-touched asset | 4.4 |
| A write to a sensitive asset never read | 4.4 |
| A stuck session (usually 5 minutes, open 3 hours) | 4.2 |
| New /16 network | 3.6 |
| New client program | 3.6 |
| A 20 KB request | 3.6 |
| Runaway loop | 3.6 |
| First-time tool | 3.2 |
| A tool used once in 60 days | 2.9 |
| A call without `initialize` | 1.9 |

**Breaks found and fixed**

| Break | Fix |
|---|---|
| Requests always 0 bytes: division by zero | Unit u = 1 KB |
| 0 → 50 bytes looked like ×4.4 | Unit u = 1 KB |
| Fixed 10-minute session rule fired all day on desktop clients | Session length against his usual |
| Exact IP fired on every call on mobile or NAT | /16 range |
| Stateless clients looked like protocol skip on every call | Only if he normally sends `initialize` |
| Rare-but-normal tools, assets and hours flared daily | "Times per day" instead of a plain share |
| Onboarding made every later first-time tool look ordinary | First uses during the warm-up do not count |
| A daily user's weekend call flared | Weekend calls compared with weekend days |

**Still weak**

| Case | M | Why |
|---|---|---|
| Legitimate pagination, 60 pages in a minute | 3.6 | The burst rule cannot tell it from a loop |
| A slow loop, same tool 40 times in 10 minutes | 2.2 | "Same tool in 10 minutes" was removed |
| A bot at 5× its usual rate | 1.95 | Tolerance 2 makes 5× only about ×2 |

### The 9 simulated organisations

| Check | Result |
|---|---|
| Multiplier range | 0.79–4.78 in every organisation; never NaN |
| Ordinary agent-days at ×3 or more | Calendar 2.8%, Slack 3.5–4.8%, GitHub 5.1–9.5% (before the fixes: 6–16%) |
| Ordinary agent-days at ×2 or more | 5–16% (before: 16–28%) |
| Daily review list, ≤ 4 agent-days a day | 52–78% of strange episodes caught, mean 65% (before: 57%) |

**What still causes ordinary flares:**

- **Asset rarity:** about half on Calendar and Slack. Some agents touch long tails of assets.
- **The GitHub problematic-sequence rule:** 33–46% on GitHub. Developers often write to sensitive repos they have not read in a week. Lower its value (for example 0.7, ×1.9) or narrow it.

**Legitimate changes that flare at ×3 or more:**

| Change | Share of days | Why |
|---|---|---|
| Night work by a day worker | 54% | Time of day, by design |
| New network | 35% | The first-time network rule, by design |
| Role change | 22% | — |
| Team transfer | 20% | — |
| Back from vacation | 14% | — |
| Client upgrade, new hire, redeploy | 4–6% | — |

**Caught at ×3 or more:**

| How well | Kinds |
|---|---|
| Very well | New origin 100%, shared credential 95%, slow creep 90%, sensitive asset 80%, fan-out 78% |
| In between | Client switch 71%, repeated habit 65%, off-role tool 64%, page walk 63%, loop 52%, content dump 50% |
| Weak | Cancel storm 23%, protocol skip 6% (lowered on purpose), over-fetch 5% (cannot be seen without the page size) |

**A ranking problem: ties at the top.** Every rule gives exactly ×3.6, so many agent-days tie at the top of the daily list. At a budget of 2 a day, the list cannot rank them, and detection drops to 17–52% depending on the organisation. Break ties by the second-strongest dimension, or give rules different values.

## Policy learned from the data, simulated with the production engine

Until the organisation writes a policy, the gateway can learn one from a route's own traffic: `src/mcp_security/behaviour/policy.py`. Each limit is set from agent-days, not single calls, so a rule fires on at most 0.5% of ordinary agent-days. A tool requires an earlier one when that tool came first in 99.5% of its sessions.

**Ties are not broken.** An agent-day scores its highest multiplier, and everything tied at the review list's cut-off is flagged.

The production engine (`src/mcp_security/behaviour`) was run on the 9 organisations (`behaviour_policy_sim.py`), with the policy learned from each organisation's first 30 days:

- burst over 15–20 calls a minute (the default is 20);
- requests over 1 KB (the default is 10 KB; simulated requests are small);
- no required earlier steps, because no tool always followed another in the simulated sessions.

| | Default policy | Learned policy |
|---|---|---|
| Multiplier range | 0.79–4.78 | 0.79–4.78 |
| Ordinary agent-days at ×3 or more | 2.8–8.1%, mean 3.9% | 3.0–8.1%, mean 4.2% |
| Review list, ≤ 2 a day (ties included; real load 2.0–3.0) | 48% | **50%** |
| Review list, ≤ 4 a day | 68% | **70%** |

**Where the learned policy changed things:**

- **The learned 1 KB request limit** catches content dumps at 100% (from 49%).
- **The tighter burst limit** lifts loops to 65% (from 52%) and recipient blasts to 65% (from 45%). It also adds a little burst noise on ordinary days.

## Parameters

| Parameter | Value |
|---|---|
| History | his last 90 days |
| Warm-up | 5 calls (or 10) |
| Tolerance | 2: up to twice his usual, or every other day, is ordinary |
| Units | 1 call, 1 minute, 1 KB |
| Tool ceiling | 0.9 (first-time tool ≈ ×3.2–3.6) |
| Multiplier | 0.7 to 5; exactly 1 at the edge of ordinary |
| Rule values | 0.9 (×3.6) by default; protocol skip 0.7 (×1.9) |
| Limits | burst 20 a minute, request 10 KB |

## References

- The methodology deck: `Likelihood = N(f,v) / (N_total + K_f)`, with a bounded history.
- The bounded shape `x / (x + c)`:
  - BM25 term-frequency saturation, `tf / (tf + k)`: [Stanford IR lecture notes](https://web.stanford.edu/class/cs276/handouts/lecture12-bm25etc.pdf);
  - [Logtalk anomaly detector](https://logtalk.org/handbook/libraries/z_score_anomaly_detector.html), `Raw / (1 + Raw)`.
- Code:
  - `bounded_stress.py`: the engine, the 33 edge cases and the 9-organisation run;
  - results in `results/bounded_stress_per_day.json` (this design) and `results/bounded_stress.json` (before the "times per day" fix);
  - `bounded_examples.py`: the earlier worked examples.
