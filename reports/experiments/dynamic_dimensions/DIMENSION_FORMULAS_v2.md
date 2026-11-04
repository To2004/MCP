# Dynamic layer: one formula per dimension (v2)

*Saved copy of v2, kept for reference. The current design is v3: [DIMENSION_FORMULAS.md](DIMENSION_FORMULAS.md). The engine still runs v2 with `"design": "v2"` in a route's behaviour policy.*

*Updated 2026-10-20. This replaces the first version of `DIMENSION_FORMULAS.md`; the changes are
listed under [What changed in v2](#what-changed-in-v2).*

Every call is compared with the **same agent's own last 90 days**, never with other agents. Each
dimension gives a score `s` between 0 (normal) and 1 (very strange), using only fractions and
averages: no bits. The **strangest** dimension sets the call's dynamic multiplier `M`, which always
lies between 0.7 and 5:
- ordinary calls stay at or below ×1, so they do not flare;
- clearly strange calls get close to ×5.

With a static score of 1–5, the risk `R = static × M` stays between 0.7 and 25 by its shape alone,
with no rounding or clipping.

The dimensions fall into three groups:

| Group | Meaning | Dimensions |
|---|---|---|
| **Typical Cadence** | when, how often, and at what intervals operations occur | calls in the last hour · session length · time of day |
| **Typical Footprint** | which tools and assets are typically used | tool · asset |
| **Policy** | fixed yes/no rules; broken → a fixed score | burst · risky order · new network · new app · new tool · request size · skipped "hello" |

"Typical" means learned from his own last 90 days. Policy is a set of fixed checks; a few of them
ask his past one yes/no question ("never seen?", "does he usually say hello?").

---

## What changed in v2

1. **Three named groups:** Typical Cadence, Typical Footprint and Policy replace the old
   Timing / Footprint / Origin / Request headings.
2. **Request size is only a Policy rule** (over 10 KB → 0.9).
   - The "request size, more than his usual" dimension is removed.
   - As a result, a 1 GB request now gives ×3.6, not ×5.0.
3. **New tool is a Policy rule** (a tool he never used → 0.9, ×3.6).
   - Tool rarity stays in Typical Footprint for tools he has used before.
4. **A full explanation of `e`:** how "rare calls" is counted, what the +1s mean, and the
   alternative "this thing only" with its trade-off.
5. **The reasons behind the multiplier:** why the strangest wins and why this curve, with
   benefits and disadvantages.
6. **A fix in the summary table:** the 0.33 row is "once a day", not "twice a day". Twice a day
   gives 0.2.
7. **The stress-test results are from v1.** They were measured before changes 2 and 3; the
   [Stress test](#stress-test) section marks what changes by construction.

---

## Step 1: a score per dimension

### Way 1: "More than his usual"

Used by **calls in the last hour** and **session length** (Typical Cadence).

```
s = (today + u) / (today + u + 2 × (usual + u))
```

| Part | Means | Why |
|---|---|---|
| `today` | his number now: calls in the last 60 minutes, or minutes since the session started | |
| `usual` | his average over the last 90 days | only his own past, never other agents |
| `2` | tolerance: up to 2× his usual is still normal | at exactly 2× usual, `s` = 0.5, so the multiplier is exactly ×1 |
| `u` | a small unit: 1 call, or 1 minute | no 0 ÷ 0, and tiny absolute changes (0 → 1) don't count |
| the shape | `x / (x + 2)` with `x = (today + u) / (usual + u)` | rises fast, then flattens; more always counts, but `s` never passes 1 |

Ignoring `u`, the formula is `today / (today + 2 × usual)`. It compares today with twice his usual.

**Example:** his usual is 100 calls an hour.

| Calls today | s | M |
|---|---|---|
| 100 (his usual) | 0.33 | ×0.9 |
| 200 (2×) | 0.50 | ×1.0 |
| 400 (4×) | 0.67 | ×1.7 |
| 1,000 (10×) | 0.83 | ×2.9 |
| 5,000 (50×) | 0.96 | ×4.4 |

### Way 2: "Rarer than his usual"

Used by **tool** and **asset** (Typical Footprint), and by **time of day** (Typical Cadence).

```
e = (rare calls + 1) / (active days + 1)        "times per day"
s = c / (1 + 2 × e)                             c = 1, or 0.9 for tools
```

| Part | Means | Why |
|---|---|---|
| `e` | how many times a day he does something this rare | per day, not a plain share (see [Why "times per day"](#why-times-per-day-and-not-a-plain-share)) |
| `rare calls` | his past calls on **this thing and everything he used as little or less** | if he touches rare things all the time, rare is normal for him |
| `active days` | days with at least one call, in the last 90 days | turns a count into "per day" |
| `+1` (top) | read as "this call" | a never-used thing still gets a small number, not zero |
| `+1` (bottom) | read as "today" | a brand-new agent with 0 days never divides by zero |
| `2` | tolerance | every other day (`e` = 0.5) gives `s` = 0.5, so the multiplier is ×1 |
| `c` | the ceiling | a rare tool stays near ×3.2–3.6, the same level as a policy rule |

**Time of day** uses its own `e`: `(his calls within one hour of this time + 1) ÷ (his active days
of this kind + 1)`. Weekdays and weekends are counted separately.

#### How "rare calls" is counted: the call picks the cut

Nothing is marked as rare in advance.
1. Sort his history from most used to least used.
2. The thing in **this call** sets the cut: its own count.
3. "Rare calls" is the sum of this thing and everything below the cut.

His history (30 active days), with the cut for two different calls:

```
repo-main     300
docs           60   ← call to docs: cut here    → rare calls = 60+30+3+2+1 = 96
wiki           30
payroll         3   ← call to payroll: cut here → rare calls = 3+2+1 = 6
hr-files        2
old-archive     1
```

| Call to | Rare calls | e | s | M |
|---|---|---|---|---|
| repo-main | 396 | 12.8 | 0.04 | ×0.7 |
| docs | 96 | 3.13 | 0.14 | ×0.8 |
| payroll | 6 | 0.23 | 0.69 | ×1.8 |
| old-archive | 1 | 0.06 | 0.89 | ×3.5 |
| a never-used folder (he started 0 new things) | 0 | 0.03 | 0.94 | ×4.1 |

**Something he never used** (count 0) has no count of its own. Its "rare calls" is **how often he
started using something new**, not counting his warm-up.
- If he rarely starts new things, a new one scores near the top.
- If he explores every day, a new thing is ordinary for him. It can even score a little below
  something he used once.

#### The score as a curve

With `x = 1/e` ("he does it once every x days"), Way 2 is `s = c · x / (x + 2)`. That's the same
curve as Way 1.

| He does it… | e | s (c = 1) | M |
|---|---|---|---|
| once a day | 1 | 0.33 | ×0.9 |
| every other day | 0.5 | 0.50 | ×1.0 |
| once in 4 days | 0.25 | 0.67 | ×1.7 |
| once in 10 days | 0.1 | 0.83 | ×2.9 |
| never (long history) | ~0.01–0.05 | 0.9–0.98 | ×3.6–4.7 |

#### Why "times per day" and not a plain share

An agent making 100 calls a day hits a "1 in 100" thing about once a day by chance.
- **Plain share** (calls to X ÷ all his calls): 6–16% of ordinary agent-days flared to ×3 or more.
- **Times per day:** that halved, to 3–10%.

#### Alternative: "this thing only"

```
e = (calls to X + 1) / (active days + 1)
```

| Agent | Today | This thing only | This thing + everything rarer |
|---|---|---|---|
| Focused (a few big things + payroll 3× in 30 days) | payroll | ×2.6 | ×2.6 |
| Explorer (the same + 40 small folders, about 2× each) | payroll | ×2.6 | ×0.8 |
| Bot posting to 300 channels in turn (about 9 posts per channel in 90 days) | any channel | ×2.8 on every post | ×1.0 (measured) |
| 26 tools used evenly (about 17 calls per tool in 90 days) | any tool | ×2.0 on every call | ×1.0 (measured) |

**This thing only:**
- Easier to explain.
- Catches an explorer touching a rare, important asset.
- But lights up bots, rotations and explorers all day.

**This thing + everything rarer (current):**
- Calm for those agents.
- But can miss an explorer touching something rare and important.

**Untested middle option:** use the whole group in general, and "this thing only" for assets the
static scan rates 4–5.

#### Learning: a new thing becomes ordinary

Take a new folder, Q4-plan, on its first day, with the history above, and assume the history
updates after every call. Each call raises Q4-plan's count, so the cut moves up, more calls sit
below it, `e` grows and the score falls.

| Call on Q4-plan | 1st | 2nd | 3rd | 5th | ~10th |
|---|---|---|---|---|---|
| M | ×4.1 | ×3.0 | ×2.0 | ×1.3 | ×1.0 |

When the history updates (after every call, or once a day) is still an
[open decision](#open-decisions).

### Way 3: Policy rules

```
broken      → s = the rule's value
not broken  → the rule does not take part
```

| Rule | Fires when | Value | Notes |
|---|---|---|---|
| Burst | more than 20 calls in a minute | 0.9 (×3.6) | catches runaway loops; the limit is a setting |
| Risky order | a write after reading a different sensitive asset · a write to a sensitive asset not read in 7 days · a merge with no review | 0.9 (×3.6) | GitHub: 33–46% of its false alarms; consider 0.7 or narrowing |
| New network | a /16 range he has never used | 0.9 (×3.6) | the /16, not the exact IP, which changes all the time on mobile networks, carrier-grade NAT and cloud servers |
| New app | a client name he has never used, version dropped | 0.9 (×3.6) | an upgrade is not a new app |
| **New tool** (v2) | a tool he has never used | 0.9 (×3.6) | the same level as the tool ceiling |
| **Request size** (v2) | a request over 10 KB | 0.9 (×3.6) | size is checked only here; the limit is a setting |
| Skipped "hello" | a tool call in a session that never sent `initialize` | 0.7 (×1.9) | only if he sends `initialize` in at least half his sessions, so stateless clients don't flare; lowered on purpose (a weak signal) |

**Why 0.9:** strong, the same level as a first-time tool through the Footprint ceiling.
**Why 0.7 for "hello":** a weak signal on its own.

### Summary: score → multiplier

| What happened | s | M |
|---|---|---|
| His average, or something he does once a day | 0.33 | 0.89 |
| **Twice his average, or something he does every other day** | **0.50** | **1.00** |
| 4× his average, or once in 4 days | 0.67 | 1.73 |
| 10× his average, or once in 10 days | 0.83 | 2.89 |
| A broken policy rule | 0.9 | 3.62 |
| Skipped "hello" (rule) | 0.7 | 1.90 |
| Never (long history) | 0.9–0.98 | 3.6–4.7 |

---

## Step 2: the call's dynamic multiplier

```
S = the largest s over the call's dimensions
M = 5   ^ (2S − 1)     when S ≥ 0.5     the edge of ordinary → 1,   the strangest possible → towards 5
M = 0.7 ^ (1 − 2S)     when S < 0.5     familiar → below 1,          everything very familiar → towards 0.7
```

| Part | Means | Why |
|---|---|---|
| `S` | the strangest score of the call | one strange thing is enough; it isn't averaged away |
| `0.5` | the edge of normal | 2× usual, or every other day, gives exactly ×1 |
| `5` | the top | static 1–5 × 5 gives 25: both sides use the same 5-step scale |
| `0.7` | the bottom | familiar behaviour lowers the risk a little, by at most 30%, and never erases it |
| `2S − 1` / `1 − 2S` | how far S is from 0.5, from 0 to 1 | a smooth curve: every +0.1 of S above 0.5 multiplies M by about 1.38 |

**Warm-up.** For a user's first 5 calls (or 10, a policy choice), `M` = 1, because there is no
history yet.

### Why the strangest wins (max, not average or sum)

Take one call with four scores: time of day 0.33, tool 0.33, calls this hour 0.33, new network
(rule) 0.9.

| Combine by | Result | |
|---|---|---|
| Average | 0.47 → ×1.0 | the strange thing is hidden |
| Sum | 1.89 | not on a 0–1 scale, and grows with every dimension added |
| **Maximum** | 0.9 → ×3.6 | the strange thing shows |

**Benefits:**
- One strange thing is enough; normal dimensions can't hide it.
- Easy to explain: the dimension that set `S` is the reason for the alert.
- Stable as dimensions are added; related signals aren't counted twice.

**Disadvantages:**
- **Medium signals don't add up:** odd hour 0.7 plus odd asset 0.7 still gives ×1.9.
- **Ties at the top:** every broken rule gives exactly ×3.6.
- **One noisy dimension is enough on its own:** asset rarity, or GitHub "risky order".

### Why this curve

**Benefits:**
- **Normal = exactly ×1:** a normal call keeps its static risk.
- **Small discount, big boost:** familiar lowers risk by at most 30%; strange raises it up to ×5.
- **Smooth, no cliffs:** a small change in behaviour is a small change in risk.
- **Always in range:** 0.7 to 25 with no clipping. Measured range: ×0.79 to ×4.78.

**Disadvantages:**
- **5 and 0.7 are chosen by design**, not learned from data.
- **The top is hard to reach:** scores rarely get near 1, so ×5 almost never happens.
- **Static and dynamic weigh the same:** see the grid in Step 3.

---

## Step 3: the risk

```
R = R_static × M          R_static 1–5,  M 0.7–5   →   R between 0.7 and 25
```

| Static \ S | familiar 0.25 | edge 0.5 | 0.67 | 0.83 | rule 0.9 | 1.0 |
|---|---|---|---|---|---|---|
| 5 | **4.2** | 5.0 | 8.6 | 14.5 | 18.1 | 25.0 |
| 4 | 3.3 | 4.0 | 6.9 | 11.6 | 14.5 | 20.0 |
| 3 | 2.5 | 3.0 | 5.2 | 8.7 | 10.9 | 15.0 |
| 2 | 1.7 | 2.0 | 3.5 | 5.8 | 7.2 | 10.0 |
| 1 | 0.8 | 1.0 | 1.7 | 2.9 | 3.6 | **5.0** |

The two bold cells are about equal: a very strange call on a harmless tool scores about like a
familiar call on a dangerous tool.

**End-to-end example:** static 3, usual 100 calls an hour.

| Dimension | Situation | s |
|---|---|---|
| Calls this hour | 400 | 0.67 |
| Time of day | his usual hour | 0.33 |
| Tool | one he uses every other day | 0.50 |
| Asset | a folder he opens once in 10 days | 0.83 |
| Policy | no rule broken | not used |

S = 0.83, so M = ×2.9 and R ≈ 8.8.

---

## The dimensions

### Typical Cadence

| # | Dimension | Formula |
|---|---|---|
| 1 | Calls in the last hour | more than usual: n = his calls in the last 60 minutes, u = 1 call |
| 2 | Session length | more than usual: minutes since the session started, against his usual, u = 1 minute |
| 3 | Time of day | rarer than usual: e = (his calls within one hour of this time + 1) ÷ (his active days of this kind + 1), weekdays and weekends separately |

### Typical Footprint

| # | Dimension | Formula |
|---|---|---|
| 4 | Tool | rarer than usual, ceiling 0.9 (a tool never used before is the New tool rule) |
| 5 | Asset | rarer than usual: a never-touched asset gives about ×4.4 |

### Policy

| # | Rule | Value |
|---|---|---|
| 6 | Burst: more than 20 calls in a minute | 0.9 |
| 7 | Risky order: a write after reading a different sensitive asset; a write to a sensitive asset not read in 7 days; a merge with no review | 0.9 |
| 8 | New network: a /16 range he has never used | 0.9 |
| 9 | New app: a client name, version dropped, he has never used | 0.9 |
| 10 | New tool: a tool he has never used (v2) | 0.9 |
| 11 | Request size: over 10 KB (v2) | 0.9 |
| 12 | Skipped "hello": a tool call in a session that never sent `initialize`, only if he normally sends it (at least half his sessions) | 0.7 |

### Removed

| Removed | When | Why |
|---|---|---|
| Same tool in 10 minutes | 2026-10-19 | removing it changed overall detection by about 1 point; loops still reach ×2 or more 55% of the time instead of 69% |
| The fixed "session longer than 10 minutes" rule | 2026-10-19 | real desktop clients keep one session open for hours, so it fired all day; replaced by session length against his usual |
| Request size, "more than his usual" | 2026-10-20 | size is now checked only by the Policy rule (over 10 KB) |
| First-time tool through rarity alone | 2026-10-20 | now the New tool rule; tool rarity still covers tools he has used before |

---

## Stress test

> **Measured on the v1 design** (before request size and new tool moved to Policy). The 33
> hand-made cases and the 9-organisation run should be re-run on v2. The "v2" column shows only
> what changes by construction.

### Edge cases (33 hand-made)

**Held: ordinary stays at or below ×1**

| Case | M (v1) | v2 |
|---|---|---|
| Ordinary day | 1.0 | |
| Night-shift worker | 1.0 | |
| Brand-new agent, first 12 calls | 1.0 | |
| Desktop client, one session open all day | 1.0 | |
| New exact IP on every call, same /16 | 1.0 | |
| Requests always 0 bytes, no crash | 1.0 | size is only a rule; the rule doesn't fire |
| 0 bytes, then one request of 50 bytes | 1.0 | size is only a rule; the rule doesn't fire |
| Bot at its usual rate | 1.0 | |
| Bot +20% | 1.0 | |
| Low-volume agent (1 call a day) | 1.0 | |
| Agent back after 120 days away | 1.0 | |
| Agent using 26 tools evenly | 1.0 | |
| Bot posting to 300 channels in rotation | 1.0 | |
| Calls arriving out of order | 1.0 | |
| Stateless client that never sends `initialize` | 0.97 | |

**Held: strong things flare**

| Case | M (v1) | v2 |
|---|---|---|
| A 1 GB request | 5.0, never above | **3.6** (Request size rule) |
| Travel, first day | 4.4, then 1.8 on day 2 and 1.0 by day 5 | |
| A never-touched asset | 4.4 | |
| A write to a sensitive asset never read | 4.4 | |
| A stuck session (usually 5 minutes, open 3 hours) | 4.2 | |
| New /16 network | 3.6 | |
| New client program | 3.6 | |
| A 20 KB request | 3.6 | 3.6 |
| Runaway loop | 3.6 | |
| First-time tool | 3.2 | **3.6** (New tool rule) |
| A tool used once in 60 days | 2.9 | |
| A call without `initialize` | 1.9 | |

**Breaks found and fixed**

| Break | Fix | v2 |
|---|---|---|
| Requests always 0 bytes: division by zero | Unit u = 1 KB | no longer needed: size is only a rule |
| 0 → 50 bytes looked like ×4.4 | Unit u = 1 KB | no longer needed: size is only a rule |
| Fixed 10-minute session rule fired all day on desktop clients | Session length against his usual | |
| Exact IP fired on every call on mobile or NAT | /16 range | |
| Stateless clients looked like protocol skip on every call | Only if he normally sends `initialize` | |
| Rare-but-normal tools, assets and hours flared daily | "Times per day" instead of a plain share | |
| Onboarding made every later first-time tool look ordinary | First uses during the warm-up do not count | |
| A daily user's weekend call flared | Weekend calls compared with weekend days | |

**Still weak**

| Case | M | Why |
|---|---|---|
| Legitimate pagination, 60 pages in a minute | 3.6 | The burst rule cannot tell it from a loop |
| A slow loop, same tool 40 times in 10 minutes | 2.2 | "Same tool in 10 minutes" was removed |
| A bot at 5× its usual rate | 1.95 | Tolerance 2 makes 5× only about ×2 |

### The 9 simulated organisations (v1)

GitHub, Calendar and Slack; about 25 million messages.

| Check | Result |
|---|---|
| Multiplier range | 0.79–4.78 in every organisation; never NaN |
| Ordinary agent-days at ×3 or more | Calendar 2.8%, Slack 3.5–4.8%, GitHub 5.1–9.5% (before the fixes: 6–16%) |
| Ordinary agent-days at ×2 or more | 5–16% (before: 16–28%) |
| Daily review list, ≤ 4 agent-days a day | 52–78% of strange episodes caught, mean 65% (before: 57%) |

**What still causes ordinary flares:**
- **Asset rarity:** about half on Calendar and Slack. Some agents touch long tails of assets.
- **The GitHub risky-order rule:** 33–46% on GitHub. Developers often write to sensitive repos
  they have not read in a week. Lower its value (for example 0.7, ×1.9) or narrow it.

**Legitimate changes that flare at ×3 or more:**

| Change | Share of days | Why |
|---|---|---|
| Night work by a day worker | 54% | Time of day, by design |
| New network | 35% | The new-network rule, by design |
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

**A ranking problem: ties at the top.**
- Every rule gives exactly ×3.6, so many agent-days tie at the top of the daily list.
- At a budget of 2 a day, the list cannot rank them, and detection drops to 17–52% depending on
  the organisation.
- **v2 adds two more ×3.6 rules** (new tool, request size), so ties may become more common.
- Fix: break ties by the second-strongest dimension, or give rules different values.

---

## Parameters

| Parameter | Value |
|---|---|
| History | his last 90 days |
| Warm-up | 5 calls (or 10) |
| Tolerance | 2: up to twice his usual, or every other day, is ordinary |
| Units | 1 call, 1 minute (1 KB no longer needed in v2) |
| Tool ceiling | 0.9 |
| Multiplier | 0.7 to 5; exactly 1 at the edge of ordinary |
| Rule values | 0.9 (×3.6) by default; skipped "hello" 0.7 (×1.9) |
| Limits | burst 20 a minute, request 10 KB |
| History update | open: after every call, or once a day |

---

## Where the formulas come from

- **One shape for both scores:** `x / (x + 2)`.
  - Way 1 uses `x` = today ÷ his usual (with `u`).
  - Way 2 uses `x` = once every `x` days (`x` = 1/`e`).
- **The shape is a known one.** It's the saturating curve used by BM25 term frequency,
  `tf / (tf + k)`, and by the Logtalk anomaly detector, `Raw / (1 + Raw)`.
- **The `+u` and `+1` are additive (add-one) smoothing,** as in the methodology deck's
  `Likelihood = N(f,v) / (N_total + K_f)` with a bounded history.
- **Design choices checked by the stress test,** not taken from a paper:
  - the tolerance 2
  - the units
  - the tool ceiling 0.9
  - per-day counting instead of a plain share
  - the multiplier's 5 and 0.7
  - the rule values 0.9 and 0.7

---

## Open decisions

1. **When the history updates:** after every call or once a day.
   - **After every call:** adapts fast, but a new asset can be "trained" to look ordinary within
     the same day.
   - **Once a day:** simpler and harder to train, but one busy new day stays red all day.
2. **Reasons for the settings:** 90 days, 20 calls a minute, 10 KB and the 5-call warm-up have no
   stated reason yet.
3. **Re-run the stress test and the 9-organisation run on v2.**
4. **Ties at the top:** break them by the second-strongest dimension, or use different rule
   values.
5. **"This thing only" for sensitive assets:** an untested way to catch an explorer touching a
   rare, important asset.

---

## References

- The methodology deck: `Likelihood = N(f,v) / (N_total + K_f)`, with a bounded history.
- The bounded shape `x / (x + c)`:
  - BM25 term-frequency saturation, `tf / (tf + k)`: [Stanford IR lecture notes](https://web.stanford.edu/class/cs276/handouts/lecture12-bm25etc.pdf);
  - [Logtalk anomaly detector](https://logtalk.org/handbook/libraries/z_score_anomaly_detector.html), `Raw / (1 + Raw)`.
- Code (v1):
  - `bounded_stress.py`: the engine, the 33 edge cases and the 9-organisation run;
  - results in `results/bounded_stress_per_day.json` (this design) and
    `results/bounded_stress.json` (before the "times per day" fix);
  - `bounded_examples.py`: the earlier worked examples.
- The deck: `presentations/slides/2026-10-20_dimension-formulas-simple-v5.pptx` and its guide
  `2026-10-20_dimension-formulas-simple-v5.md`.
