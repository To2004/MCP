# Dynamic layer: one formula per dimension (v3)

*Saved copy of v3, kept for reference. The current design is v4: [DIMENSION_FORMULAS.md](DIMENSION_FORMULAS.md). The engine still runs v3 with `"design": "v3"` in a route's behaviour policy.*

*Updated 2026-10-20. This replaces v2; the changes are listed under
[What changed in v3](#what-changed-in-v3). v3 was checked on five simulated GitHub organisations
of mostly ordinary traffic: see [Simulation](#simulation-v3). The earlier versions are saved:
[v1](DIMENSION_FORMULAS_v1.md), [v2](DIMENSION_FORMULAS_v2.md). The engine ran v3 by default and
kept v1 and v2 runnable: see [In the engine](DIMENSION_FORMULAS.md#in-the-engine).*

Every call is compared with the **same agent's own last 90 days**. Each dimension gives a score
`s` between 0 (normal) and 1 (very strange), using only fractions and averages: no bits. The
**strangest** dimension sets the call's dynamic multiplier `M`, which always lies between 0.7
and 5:
- ordinary calls stay at or below ×1, so they do not flare;
- clearly strange calls get close to ×5.

With a static score of 1–5, the risk `R = static × M` stays between 0.7 and 25 by its shape alone,
with no rounding or clipping.

Other agents never raise a score. They can only lower one: something new for him that several
other agents also started this week is an org-wide change, not his own
([org discount](#org-discount)).

The dimensions fall into three groups:

| Group | Meaning | Dimensions |
|---|---|---|
| **Typical Cadence** | when, how often, and at what intervals operations occur | calls in the last hour · session length · time of day · same call in 10 minutes · writes in the last hour · distinct assets in the last hour |
| **Typical Footprint** | which tools and assets are typically used | tool · asset |
| **Policy** | yes/no rules; broken → a set score | burst · risky order · new network · new app · new tool · request size · skipped "hello" · first look at a sensitive asset · many assets in an hour |

"Typical" means learned from his own last 90 days, up to yesterday. Policy is a set of checks with
limits; a few of them ask his past one yes/no question ("never seen?", "does he usually say
hello?").

---

## What changed in v3

**Decided on 2026-10-20:**

1. **Same call in 10 minutes** (Typical Cadence): the same tool on the same asset, more than his
   usual. It catches a stuck agent loop that stays under the burst limit.
2. **First look at a sensitive asset** (Policy): an asset of sensitivity 4 or 5 he has not touched
   in 90 days. The decision was to grade it by the asset and the tool. Grading by the asset halves
   the false alarms; grading by the tool as well gained nothing in the simulation. So v3 grades by
   the asset only, 0.9 (×3.6) for sensitivity 5 and 0.8 (×2.6) for sensitivity 4, and the tool
   counts through `R_static`. See [First look at a sensitive asset](#first-look-at-a-sensitive-asset).
3. **Distinct assets in the last hour:** a count in Typical Cadence (more than his usual), with a
   Policy rule as a backstop (more assets in one hour than the organisation's learned limit).
4. **Request size: one limit per tool**, learned from traffic, instead of one 10 KB limit for all.
   Each limit is learned per agent-day, as `policy.py` already learns its one limit.
5. **The history updates once a day.** A call is compared with his history up to yesterday.
6. **Onboarding: 14 days.** What he starts using in his first 14 days does not count as "starting
   something new".
7. **Weekends are blended with all days:** a weekend call is compared with his weekend days plus
   4 days' worth of his all-days profile. See [Weekends](#weekends).
8. **M stays the maximum.** Ties are broken only when ranking the daily review list, by the
   second-strongest score; `M` itself does not change.

**From the simulation** (proposed by the simulation; not yet decided explicitly):

9. **The warm-up is his first day**, not his first 5 calls. Because of change 5, nothing is in his
   history until his first day ends, so every tool would be "new" (×3.6) all that day. During the
   warm-up, the rules that need none of his past still fire: burst, request size, many assets,
   first look at a sensitive asset and risky order.
10. **Writes in the last hour** (Typical Cadence, more than his usual). Without it, mass cleanup
    is caught half as often (main organisation: 22% → 11%), with the same false alarms.
11. **Rule rarity** for burst, risky order and many assets: a rule he breaks often counts less.
    See [Rule rarity](#rule-rarity).
12. **Org discount** for new tools, assets, networks and apps, but not for a first look at a
    sensitive asset. See [Org discount](#org-discount).
13. **Limits learned from traffic** (`policy.py`, first 30 days): burst, request size per tool,
    many assets per hour. See [Limits learned from traffic](#limits-learned-from-traffic).

**Tested and not adopted:**
- the tie-break formula `S = s1 + 0.3 × s2 × (1 − s1)` (M stays the max);
- distinct assets per hour as the rule only (one org-wide limit can be pushed up by a few heavy
  users, as happened to request size);
- weekends split, fallback, or a separate weekend flag;
- counting days instead of calls for tool, asset and time of day.

---

## Step 1: a score per dimension

### Way 1: "More than his usual"

Used by **calls in the last hour**, **session length**, **same call in 10 minutes**, **writes in
the last hour** and **distinct assets in the last hour** (Typical Cadence).

```
s = (today + u) / (today + u + 2 × (usual + u))
```

| Part | Means | Why |
|---|---|---|
| `today` | his number now: calls in the last 60 minutes, minutes since the session started, calls with this tool on this asset in the last 10 minutes, writes in the last 60 minutes, or distinct assets in the last 60 minutes | |
| `usual` | his average of that number over the last 90 days, up to yesterday | only his own past, never other agents |
| `2` | tolerance: up to 2× his usual is still normal | at exactly 2× usual, `s` = 0.5, so the multiplier is exactly ×1 |
| `u` | a small unit: 1 call, 1 minute or 1 asset | no 0 ÷ 0, and tiny absolute changes (0 → 1) don't count |
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

**The three new counts** (v3):

| Dimension | Catches | In the simulation (main organisation) |
|---|---|---|
| Same call in 10 minutes | a stuck agent loop polling one thing | slow loops caught 100% (v2: 0%) |
| Writes in the last hour | mass cleanup: many updates in a row | mass cleanup 22% (11% without it) |
| Distinct assets in the last hour | a bulk export across many repositories | bulk exports 100% with the rule backstop, 82% with the count alone (v2: 0%) |

A client that polls by design has a high usual, so "same call in 10 minutes" stays ordinary for
it.

### Way 2: "Rarer than his usual"

Used by **tool** and **asset** (Typical Footprint), and by **time of day** (Typical Cadence).

```
e = (rare calls + 1) / (active days + 1)        "times per day"
s = c / (1 + 2 × e)                             c = 1, or 0.9 for tools
```

| Part | Means | Why |
|---|---|---|
| `e` | how many times a day he does something this rare | per day, not a plain share (see [Why "times per day"](#why-times-per-day-and-not-a-plain-share)) |
| `rare calls` | his past calls on **this thing and everything he used as little or less**, up to yesterday | if he touches rare things all the time, rare is normal for him |
| `active days` | days with at least one call, in the last 90 days, up to yesterday | turns a count into "per day" |
| `+1` (top) | read as "this call" | a never-used thing still gets a small number, not zero |
| `+1` (bottom) | read as "today" | a brand-new agent with 0 days never divides by zero |
| `2` | tolerance | every other day (`e` = 0.5) gives `s` = 0.5, so the multiplier is ×1 |
| `c` | the ceiling | a rare tool stays near ×3.2–3.6, the same level as a policy rule |

**Time of day** uses its own `e`: `(his calls within one hour of this time + 1) ÷ (his active days
of this kind + 1)`, with weekends [blended](#weekends).

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
started using something new**, not counting his first 14 days (onboarding).
- If he rarely starts new things, a new one scores near the top.
- If he explores every day, a new thing is ordinary for him. It can even score a little below
  something he used once.
- An explorer's first look at payroll is caught by the Policy rule
  [first look at a sensitive asset](#first-look-at-a-sensitive-asset), not here.

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

#### "This thing only" or "this thing + everything rarer"

```
e = (calls to X + 1) / (active days + 1)        this thing only
```

| Agent | Today | This thing only | This thing + everything rarer |
|---|---|---|---|
| Focused (a few big things + payroll 3× in 30 days) | payroll | ×2.6 | ×2.6 |
| Explorer (the same + 40 small folders, about 2× each) | payroll | ×2.6 | ×0.8 |
| Bot posting to 300 channels in turn (about 9 posts per channel in 90 days) | any channel | ×2.8 on every post | ×1.0 (measured) |
| 26 tools used evenly (about 17 calls per tool in 90 days) | any tool | ×2.0 on every call | ×1.0 (measured) |

v3 keeps "this thing + everything rarer", which is calm for bots, rotations and explorers. The gap
it leaves (an explorer's first look at a rare, important asset) is closed by the Policy rule
[first look at a sensitive asset](#first-look-at-a-sensitive-asset).

#### Learning: once a day

The history updates once a day: every call today is compared with his history up to yesterday.
- A new folder, Q4-plan, stays new all day: each of its 12 calls on its first day scores ×4.4.
  When the history updated after every call, the score fell call by call (×4.4, 3.9, 3.4 … 1.7),
  so a new thing could be "trained" to look ordinary within the same day.
- The next day, Q4-plan is counted with its whole first day: one call on it scores ×1.6, then
  ×1.5, ×1.45 and ×1.4 on the following days.
- A personal script on someone's token (a new client from a new network, 50–150 calls at night):
  100% of its calls reach ×3 (5% when the history updated after every call, because its first
  calls taught the engine the new network, client and hour).
- The cost: one busy new day stays red all day.

#### Weekends

A weekend call is compared with his weekend days, plus 4 days' worth of his all-days profile:

```
e_weekend = (his weekend calls within one hour of this time + 4 × e_all) / (his weekend days + 4)
e_all     = (his calls within one hour of this time, any day + 1) / (his active days + 1)
```

- With no weekend days yet, a weekend call is judged by his all-days profile.
- With many weekend days, his weekend profile wins.
- There is no cliff in between.

| Case | Weekends split (v2) | **Blended (v3)** |
|---|---|---|
| Day worker, first Saturday ever, 2 a.m. | ×0.96 (missed) | **×4.4** |
| Day worker, first Saturday ever, 10 a.m. | ×0.96 | **×0.96** |
| Works every Saturday 10–14; Saturday 2 a.m. | ×2.9 | **×4.8** |
| Works every Saturday 10–14; Saturday 10 a.m. | ×0.96 | **×0.96** |
| Saturday 2 a.m. batches caught at ×3 (main organisation) | 20% | **80%** |

### Way 3: Policy rules

```
broken      → s = the rule's value
not broken  → the rule does not take part
```

| Rule | Fires when | Value |
|---|---|---|
| Burst | more calls in one minute than the learned limit (default 20) | 0.9 (×3.6), less if it is his habit ([rule rarity](#rule-rarity)) |
| Risky order | a write after reading a different sensitive asset in the session · a write to a sensitive asset not read in 7 days · a merge with no review | 0.9, less if it is his habit |
| Many assets in an hour | more distinct assets in one hour than the learned limit | 0.9, less if it is his habit |
| New network | a /16 range he has not used in 90 days | 0.9, at most 0.5 in an org-wide change ([org discount](#org-discount)) |
| New app | a client name, version dropped, he has not used in 90 days | 0.9, org discount |
| New tool | a tool he has not used in 90 days | 0.9, org discount |
| Request size | a request over **this tool's** learned limit | 0.9 |
| First look at a sensitive asset | an asset of sensitivity 4–5 he has not touched in 90 days | 0.9 for sensitivity 5, 0.8 for 4 ([details](#first-look-at-a-sensitive-asset)); no org discount |
| Skipped "hello" | a tool call in a session that never sent `initialize`, only if he sends it in at least half his sessions | 0.7 (×1.9) |

#### First look at a sensitive asset

```
value = 0.9 − 0.1 × (5 − asset sensitivity)          sensitivity 5 → 0.9 (×3.6),  4 → 0.8 (×2.6)
```

- A first look at payroll alerts (×3.6); a new hire's first look at the team's deploy repository
  does not (×2.6).
- A first write to a sensitive asset is usually also a blind write, so risky order fires too.
- It fires during the warm-up too, so a brand-new identity reading payroll on its first day gets
  ×3.6 (×1.0 in v2).

**Grading by the tool too.** The idea was to let the tool's static level (5 remove, 4 write,
3 read, 2 metadata) move the value as well, 0.05 a level. Four versions on the five organisations
(mean, and the range across organisations; the list is the top 4 agent-days a day, the top 8 in
the large organisation):

| First-look value | sensitivity 5: read / write / list | sensitivity 4: read / write / list | ordinary days at ×3 | gray episodes in the top-4 list |
|---|---|---|---|---|
| flat 0.9 | ×3.6 / ×3.6 / ×3.6 | ×3.6 / ×3.6 / ×3.6 | 6.1% (4.5–7.8%) | 49% (31–60%) |
| **by asset (v3)** | **×3.6 / ×3.6 / ×3.6** | **×2.6 / ×2.6 / ×2.6** | **3.7% (2.7–5.2%)** | **58% (48–66%)** |
| by asset and tool, a write is 0.9 | ×3.1 / ×3.6 / ×2.6 | ×2.2 / ×2.6 / ×1.9 | 3.7% (2.7–5.2%) | 52% (42–60%) |
| by asset and tool, a read is 0.9 | ×3.6 / ×4.3 / ×3.1 | ×2.6 / ×3.1 / ×2.2 | 4.3% (3.6–5.8%) | 58% (48–66%) |

- **The asset carries all the gain:** moving sensitivity-4 first looks below ×3 cuts the false
  alarms from 6.1% to 3.7% and new hires' alerts from 27–51% to 22–36% of their days. The cost is
  scope creep (reading other teams' deploy repositories for two weeks): caught 19–67% instead of
  38–100%.
- **The tool adds nothing measurable.** Anchored at a write, it lowers a first read of payroll to
  ×3.1, so peeks rank below the other ×3.6 alerts. Anchored at a read, it lifts a first write to a
  sensitivity-4 repository to ×3.1, above the alert line.
- The tool already counts in `R = R_static × M`, through the static level.

#### Rule rarity

For burst, risky order and many assets, a rule he breaks often counts less:

```
value = 0.9 / (1 + 2 × days he broke it / (his active days + 1))        last 90 days, up to yesterday
```

- Broken for the first time: 0.9 (×3.6).
- Broken every other day: 0.45 (it no longer takes part).
- Not used for request size, first look or the "new" rules: those are rare by nature.

#### Org discount

Something new for him (a tool, an asset, a network, an app) that **3 or more other agents also
started in the last 7 days** scores at most 0.5 (×1). That is an org-wide change: a server
release, a VPN change, a repository migration. Other agents only ever lower a score here, never
raise it.

**Not for a first look at a sensitive asset.** Several agents starting to read secrets in the
same week is not reassuring. In the large organisation (300 agents), the discount hid 4 of its 31
sensitive peeks (all at the secrets repository), because 3–4 other agents, mostly other peekers,
had first read it that week. Without the discount on this rule, peeks were caught 90% of the time
instead of 83% across the five organisations, and ordinary false alarms rose by at most 0.2
points.

### Summary: score → multiplier

| What happened | s | M |
|---|---|---|
| His average, or something he does once a day | 0.33 | 0.89 |
| **Twice his average, or something he does every other day** | **0.50** | **1.00** |
| 4× his average, or once in 4 days | 0.67 | 1.73 |
| 10× his average, or once in 10 days | 0.83 | 2.89 |
| A broken policy rule | 0.9 | 3.62 |
| First look at a sensitivity-4 asset (rule) | 0.8 | 2.63 |
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

**Warm-up: his first day.** Until his first day is in his history, `M` = 1, except for the rules
that need none of his past: burst, request size, many assets, first look at a sensitive asset and
risky order. (v2: his first 5 calls. With the history updating once a day, every tool would be
"new" for the rest of his first day.)

| A brand-new identity on its first day, after 25 calls | 5-call warm-up | first day | **first day, rules on (v3)** |
|---|---|---|---|
| an ordinary call with a tool new today | ×3.6 (new tool) | ×1.0 | **×1.0** |
| payroll, read file | ×3.6 (new tool) | ×1.0 | **×3.6** (first look) |
| payroll, write file | ×3.6 (new tool) | ×1.0 | **×3.6** (first look) |
| team deploy repo (4), read file | ×3.6 (new tool) | ×1.0 | **×2.6** (first look) |

In the five organisations, the first-day warm-up lowered new hires' alerts from 24–42% to 22–36%
of their onboarding days and changed nothing else. Keeping the history-free rules on during the
warm-up cost about one point of new-hire days (main organisation: 34.7% without them, 36.1% with
them) and nothing else.

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
  The tested alternative, `S = s1 + 0.3 × s2 × (1 − s1)`, catches mass cleanup 56% of the time
  instead of 22%, but raises false alarms from 6.2% to 7.0% of ordinary agent-days (main
  organisation, first v3 candidate). Not adopted: `M` stays the max.
- **Ties at the top:** every broken rule gives ×3.6, so many agent-days tie at the cut of the
  daily review list. The list breaks the ties by the second-strongest score; `M` stays the max.
  In the five organisations, that cut the days with a tie at the cut from 29–52% to 3–9% and
  raised the gray episodes on the list from 43–67% to 49–69%.
- **One noisy dimension is enough on its own:** see [what still causes alerts](#what-still-causes-alerts).

### Why this curve

**Benefits:**
- **Normal = exactly ×1:** a normal call keeps its static risk.
- **Small discount, big boost:** familiar lowers risk by at most 30%; strange raises it up to ×5.
- **Smooth, no cliffs:** a small change in behaviour is a small change in risk.
- **Always in range:** 0.7 to 25 with no clipping.

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

The graded first-look rule makes the asset count twice for a first look: once in `R_static` and
once in `M`. That is on purpose: the alert line is drawn on `M` (×3), and a first look at payroll
should cross it while a first look at a deploy repository should not.

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
| 1 | Calls in the last hour | more than usual: his calls in the last 60 minutes, u = 1 call |
| 2 | Session length | more than usual: minutes since the session started, u = 1 minute |
| 3 | Time of day | rarer than usual: e = (his calls within one hour of this time + 1) ÷ (his active days + 1), weekends blended with all days |
| 4 | Same call in 10 minutes (v3) | more than usual: his calls with this tool on this asset in the last 10 minutes, u = 1 call |
| 5 | Writes in the last hour (v3) | more than usual: his writes in the last 60 minutes, u = 1 call |
| 6 | Distinct assets in the last hour (v3) | more than usual: distinct assets he touched in the last 60 minutes, u = 1 asset |

### Typical Footprint

| # | Dimension | Formula |
|---|---|---|
| 7 | Tool | rarer than usual, ceiling 0.9 (a tool not used in 90 days is the New tool rule) |
| 8 | Asset | rarer than usual: a never-touched asset gives about ×4.4 for a focused agent |

### Policy

| # | Rule | Value |
|---|---|---|
| 9 | Burst: more calls in a minute than the learned limit | 0.9, rule rarity |
| 10 | Risky order: a write after reading a different sensitive asset; a write to a sensitive asset not read in 7 days; a merge with no review | 0.9, rule rarity |
| 11 | Many assets in an hour (v3): more distinct assets in one hour than the learned limit | 0.9, rule rarity |
| 12 | New network: a /16 range he has not used in 90 days | 0.9, org discount |
| 13 | New app: a client name, version dropped, he has not used in 90 days | 0.9, org discount |
| 14 | New tool: a tool he has not used in 90 days | 0.9, org discount |
| 15 | Request size: over this tool's learned limit (v3: per tool) | 0.9 |
| 16 | First look at a sensitive asset (v3): sensitivity 4–5, not touched in 90 days | 0.9 for sensitivity 5, 0.8 for 4; no org discount |
| 17 | Skipped "hello": a tool call in a session that never sent `initialize`, only if he normally sends it (at least half his sessions) | 0.7 |

### Removed

| Removed | When | Why |
|---|---|---|
| Same tool in 10 minutes | 2026-10-19 | replaced in v3 by "same call in 10 minutes" (tool and asset), which catches loops without flaring on busy tools |
| The fixed "session longer than 10 minutes" rule | 2026-10-19 | real desktop clients keep one session open for hours; replaced by session length against his usual |
| Request size, "more than his usual" | 2026-10-20 (v2) | size is checked only by the Policy rule |
| First-time tool through rarity alone | 2026-10-20 (v2) | now the New tool rule; tool rarity still covers tools he has used before |
| One request limit for all tools (10 KB) | 2026-10-20 (v3) | a limit per tool, learned: one limit is set by the biggest tool (file writes) and misses pastes into issues |
| The 5-call warm-up | 2026-10-20 (v3) | with the history updating once a day, the warm-up is his first day |

---

## Limits learned from traffic

Until the organisation writes its own limits, the gateway learns them from its first 30 days of
traffic (`src/mcp_security/behaviour/policy.py`), at the level of an agent-day: each limit is set so
the rule fires on at most 0.5% of ordinary agent-days.

| Limit | Learned as | In the five simulated organisations |
|---|---|---|
| Burst | the agent-day's busiest minute | more than 48 calls a minute (29 in the large one) |
| Request size, per tool | the agent-day's largest request with that tool | issues 9–14 KB, comments 16–26 KB, file writes 83–543 KB; 1 KB for reads |
| Many assets in an hour | the agent-day's busiest hour, in distinct assets | more than 15 in all five |
| Required earlier steps | tool B always came after tool A in the same session (99.5% of at least 50 sessions) | none found |

**Why per tool:**

One limit for all tools is set by the tool with the biggest requests (file writes), so it misses a
15–100 KB paste into an issue. Big pastes caught at ×3:

| Organisation | One limit for all tools | Pastes caught | Limit per tool (issue / file write) | Pastes caught |
|---|---|---|---|---|
| Heavy file writes (15 pastes) | 618 KB | 0% | 14 KB / 543 KB | 100% |
| Small (6 pastes) | 68 KB | 17% | 14 KB / 83 KB | 100% |
| Large (28 pastes) | 101 KB | 11% | 12 KB / 118 KB | 100% |

**Why per agent-day:** a limit set on single calls (0.1% of calls over it) fires for a busy agent
almost every day. Learning each tool's limit from agent-days, as `policy.py` already does for its
one limit, lowered false alarms in four organisations and kept them in the fifth (mean 3.7% →
3.0% of ordinary agent-days; small organisation 5.2% → 3.2%; bots most of all), and still caught
every paste.

---

## Simulation (v3)

**The setting.** A GitHub organisation using the 26 real GitHub MCP tools with their static
levels, about 100 repositories of sensitivity 2–5, and agents in seven roles (developers, leads,
SREs, PMs and three kinds of bots). It runs for 180 days: the first 90 are history and days 90–179
are scored.
- **Ordinary life:** vacations, new projects, role changes, new hires, client switches, on-call
  nights.
- **Org-wide changes:** a VPN change, a server release with 4 new tools, a repository migration
  and a release crunch.
- **Gray episodes, not attacks:** risky but legitimate-looking use, such as a bulk export, a look
  at a sensitive repository, a stuck loop, mass cleanup, a Saturday 2 a.m. batch, a big paste, a personal
  script on someone's token, scope creep, over-fetching and a misconfigured bot.

Five organisations: the main one (150 agents), a second seed (150), one with heavy file writes
(150), a small one (60) and a large one (300). The engine was first checked to give the shipped
engine's multiplier on every message when all the v3 switches are off.

**False alarms and gray episodes**

| Organisation | Agents | Ordinary agent-days at ×3: v2 → v2 with learned limits → **v3** | Gray episodes caught at ×3: v2 → **v3** | Gray episodes in the daily list: v2 → **v3** |
|---|---|---|---|---|
| Main | 150 | 52.2% → 22.1% → **3.2%** | 28% → **65%** | 14% → **62%** |
| Second seed | 150 | 51.9% → 22.8% → **3.4%** | 32% → **66%** | 14% → **49%** |
| Heavy file writes | 150 | 64.2% → 20.0% → **2.3%** | 38% → **79%** | 9% → **60%** |
| Small | 60 | 43.0% → 18.0% → **3.2%** | 51% → **74%** | 18% → **69%** |
| Large | 300 | 54.4% → 25.1% → **3.2%** | 36% → **72%** | 11% → **57%** |

- The daily list is the top 4 agent-days a day (top 8 in the large organisation). v2's ties are
  broken at random; v3's by the second-strongest score.
- v3 at ×2 or more: 12–17% of ordinary agent-days. Ordinary *calls* at ×3: 0.1–0.2%.
- Main organisation, per day: about 2.5 ordinary agent-days at ×3 out of 150 agents, plus 3.5 on
  days with a labelled life or org change.

**Gray episodes by kind**

All five organisations together. "Calls" is the share of the episode's calls at ×3 (for gating
call by call).

| Kind | Episodes | v2: caught | **v3: caught** | v3: calls at ×3 |
|---|---|---|---|---|
| Big paste (15–500 KB) | 59 | 100% | **100%** | 100% |
| Misconfigured bot loop | 15 | 100% | **100%** | 96% |
| Personal script on someone's token | 32 | 100% | **100%** | 100% (v2: 4%) |
| Slow loop on one thing | 35 | 9% | **100%** | 83% |
| Bulk export across repositories | 64 | 2% | **100%** | 79% |
| Peek at a sensitivity-5 repository | 63 | 8% | **90%** | 90% |
| Saturday 2 a.m. batch by a day worker | 29 | 21% | **79%** | 79% |
| Copy from a sensitive repository | 42 | 100% | **48%** | 28% |
| Scope creep (other teams' repos, two weeks) | 40 | 0% | **30%** | 2% |
| Mass cleanup (many updates in a row) | 34 | 0% | **26%** | 11% |
| Over-fetching (large pages) | 47 | 0% | **0%** | 0% |

**Ordinary life and org-wide changes at ×3 or more** (main organisation)

| Change | v2 | **v3** | v3's main cause |
|---|---|---|---|
| Back from vacation | 64% | **7%** | request size |
| New project | 64% | **8%** | asset |
| Org: VPN change | 100% | **8%** | new network |
| Team transfer | 67% | **6%** | request size |
| On-call night | 100% | **13%** | time of day |
| Role change | 87% | **13%** | new tool |
| Org: repository migration | 68% | **16%** | asset |
| Org: server release with new tools | 86% | **16%** | new tool |
| Release crunch | 84% | **34%** | time of day |
| New hire (onboarding days) | 86% | **38%** | new network |
| Travel | 80% | **40%** | time of day, by design |
| Home ISP change | 100% | **50%** | new network, by design |
| Client switch | 88% | **56%** | new app, by design |
| Monthly report | 100% | **100%** | burst |

### What still causes alerts

Ordinary agent-days at ×3 are 2.3–3.4%. Their causes, averaged over the five organisations:

| Cause | Share | Why |
|---|---|---|
| Request size | 57% | a legitimate big file write or long comment over the tool's learned limit |
| New network | 17% | a new home or mobile network: the rule, by design |
| Tool rarity | 10% | a tool he uses once in weeks |
| New tool | 8% | a tool he has not used in 90 days |
| Risky order | 4% | after rule rarity, only agents who rarely do it |
| Asset, session length | 3% | |

### Still weak

| Kind | v3 | Why |
|---|---|---|
| Over-fetching | 0% | the page size is an argument; the layer reads no arguments |
| Mass cleanup | 26% | updates to his own issues: writes per hour and calls per hour both rise, but rarely past ×3 alone, and medium signals don't add up under max |
| Scope creep | 30% | first looks at other teams' sensitivity-4 repositories are ×2.6 on purpose |
| Copy from a sensitive repository | 48% (v2: 100%) | risky order catches it, but rule rarity lowers risky order for developers who do it often; in v2 with learned limits, risky order was 91% of the false alarms |
| Monthly report (a bot) | 100% of its days | a burst over the limit once a month; 3 bursts in 90 days is still rare, so rule rarity keeps it at about ×3.1 |

**Honest limits.** The traffic is synthetic. Its ordinary behaviour is grounded in real GitHub
tools and their static levels, but the habits, the life changes and the gray episodes are our
design. v3's new detectors were designed after seeing what v2 missed, so their catch rates are
optimistic. The drop in false alarms is the more trustworthy number.

---

## Earlier stress test (v1 design)

> Measured on the v1 design, before v2 and v3. Not rerun on v3: the simulation above replaces
> the organisation run, and the 33 edge cases become unit tests when v3 is ported into the
> engine.

### Edge cases (33 hand-made, v1)

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
| History | his last 90 days, up to yesterday (updated once a day) |
| Warm-up | his first day; rules that need none of his past still fire |
| Onboarding | first uses in his first 14 days don't count as "starting something new" |
| Tolerance | 2: up to twice his usual, or every other day, is ordinary |
| Units | 1 call, 1 minute, 1 asset |
| Tool ceiling | 0.9 |
| Multiplier | 0.7 to 5; exactly 1 at the edge of ordinary |
| Rule values | 0.9 (×3.6); skipped "hello" 0.7 (×1.9); first look 0.9 (sensitivity 5) or 0.8 (sensitivity 4) |
| Rule rarity | burst, risky order, many assets: `0.9 / (1 + 2 × days broken / (active days + 1))` |
| Org discount | 3 or more other agents started the same new thing in the last 7 days → at most 0.5; not for a first look at a sensitive asset |
| Weekends | blended with all days, 4 pseudo-days |
| Limits | learned from the first 30 days, fired on at most 0.5% of agent-days; defaults burst 20 a minute, request 10 KB |
| Sensitive | asset sensitivity 4 or more; a write to one not read in 7 days is a risky order |

---

## Where the formulas come from

- **One shape for both scores:** `x / (x + 2)`.
  - Way 1 uses `x` = today ÷ his usual (with `u`).
  - Way 2 uses `x` = once every `x` days (`x` = 1/`e`).
- **The shape is a known one.** It's the saturating curve used by BM25 term frequency,
  `tf / (tf + k)`, and by the Logtalk anomaly detector, `Raw / (1 + Raw)`.
- **The `+u` and `+1` are additive (add-one) smoothing,** as in the methodology deck's
  `Likelihood = N(f,v) / (N_total + K_f)` with a bounded history.
- **"This thing + everything rarer"** is an empirical p-value: the share of his past that was at
  least this rare.
- **Design choices checked by simulation,** not taken from a paper: the tolerance 2, the units,
  the tool ceiling 0.9, per-day counting, the multiplier's 5 and 0.7, the rule values, the
  first-look values, the 14 days of onboarding, the 4 weekend pseudo-days and the org discount's
  3 agents in 7 days.

---

## Open decisions

1. **The warm-up** (change 9): his first day, with the history-free rules on. Proposed by the
   simulation, not decided yet.
2. **Rule rarity and the org discount** (changes 11 and 12): carried over from the first
   simulation round, not decided explicitly. Keeping the first-look rule out of the org discount
   is new in this round.
3. **Over-fetching** (a large page size) cannot be seen without reading one argument.
4. **Grading the first look by the tool as well:** proposed, tested in two versions, no gain (see
   [the table](#first-look-at-a-sensitive-asset)); it would be one more term in the formula if a
   real organisation shows otherwise.
5. **The many-assets limit from a gateway log:** `policy.py` learns it only from calls with
   resolved assets, which a gateway log does not carry, so a policy learned from a log leaves
   the rule off (the count still runs).
6. **Reasons for the settings:** 90 days, the 0.5% of agent-days for learned limits and the
   first-look values come from the simulation, not from data of a real organisation.

---

## References

- The methodology deck: `Likelihood = N(f,v) / (N_total + K_f)`, with a bounded history.
- The bounded shape `x / (x + c)`:
  - BM25 term-frequency saturation, `tf / (tf + k)`: [Stanford IR lecture notes](https://web.stanford.edu/class/cs276/handouts/lecture12-bm25etc.pdf);
  - [Logtalk anomaly detector](https://logtalk.org/handbook/libraries/z_score_anomaly_detector.html), `Raw / (1 + Raw)`.
- Code (v3):
  - `normal_org_world.py`: the mostly-ordinary GitHub organisations;
  - `normal_org_engines.py`: the engine with each v2 and v3 change as a switch;
  - `normal_org_sim.py`: the runs, the review list and the hand-made scenarios; v3 as written
    here is the engine `v3 (decided)` in the results;
  - results: `results/normal_org_sim.md` (main), `results/normal_org_sim_seed11.md`,
    `results/normal_org_git_heavy_files.md`, `results/normal_org_git_small.md`,
    `results/normal_org_git_large.md`.
- Code (v1): `bounded_stress.py`, with results in `results/bounded_stress_per_day.json`;
  `bounded_examples.py`.
- The deck: `presentations/slides/2026-10-20_dimension-formulas-simple-v5.pptx` and its guide
  `2026-10-20_dimension-formulas-simple-v5.md` (v2).
