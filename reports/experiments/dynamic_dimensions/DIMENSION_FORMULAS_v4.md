# Dynamic layer: one formula per dimension (v4)

*Updated 2026-10-21. This replaces v3; the changes are listed under
[What changed in v4](#what-changed-in-v4). v4 was checked on the same five simulated GitHub
organisations as v3: see [Simulation](#simulation-v4). The earlier versions are saved:
[v1](DIMENSION_FORMULAS_v1.md), [v2](DIMENSION_FORMULAS_v2.md), [v3](DIMENSION_FORMULAS_v3.md).
The engine runs v4 by default and keeps v1–v3 runnable: see [In the engine](#in-the-engine).
How to write this in the paper: [`paper_v5/DYNAMIC-LAYER-V4-NOTES.md`](../../../paper_v5/DYNAMIC-LAYER-V4-NOTES.md).*

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

---

## The three groups

Each group answers one question about the call.

| Group | Asks | Compared with | Scored as | Dimensions |
|---|---|---|---|---|
| **Typical Cadence** | *when* and *how often*? | his own last 90 days | graded, 0–1 | call rate · write rate · breadth · repetition · session duration · hour of day |
| **Typical Footprint** | *what* does he touch, and *from where*? | his own last 90 days | graded, 0–1 | tool · asset · network · client |
| **Red Flags** | does the call show a *warning sign*? | a line that holds for every agent: set by the organisation, or learned once from all its traffic | yes or no: raised → a set value; not raised → takes no part | burst · sweep · oversized request · unsafe sequence · missing handshake |

"Typical" means learned from his own last 90 days, up to yesterday, and graded: 0.5 is the edge
of his ordinary. A red flag is the same for every agent, and either raised or not.

In one sentence, for the paper: *two groups grade the call against the agent's own typical
behaviour; red flags are yes/no warning signs that hold for every agent.*

### Why "Red Flags", not "Policy" or "Expected Conduct"

- **Readers already know the term.** In fraud detection and anti-money-laundering, a *red flag*
  is a yes/no warning sign: present or not, a reason to look closer, not proof. That is what
  these five checks are.
- **It says a flag raises the score; it does not block.** A raised flag gives 0.9 (×3.6), or
  0.7 (×1.9) for a missing handshake. Names such as "Hard Limits" or "Guardrails" suggest the
  call is stopped, which the dynamic layer never does on its own.
- **"Typical" against "Red Flags" carries the difference between the groups.** Typical is
  relative to him and graded; a red flag is the same for everyone and raised or not. A reader
  learns the scoring from the names.
- **"Policy" was taken twice.** The static side derives asset sensitivity from the
  organisation's *classification policy*, and the gateway loads a route's learned limits from
  its *behaviour policy* file. "Policy rules" made the checks sound as if they came from the
  classification policy. They do not. (The file keeps its name, `behaviour_policy`: it holds the
  red flags' limits.) "Expected Conduct", the name from 2026-10-21 to 2026-10-25, needed a
  sentence of its own to say whose expectation it was.
- **One question per group decides where a dimension goes.** "Is this new for him?" asks
  *what, and from where*, so in v4 every "new for him" check moved to Typical Footprint: new
  network, new client, new tool and the first access to a sensitive asset are no longer flags.

### Names

These are the paper's names, used everywhere in this document. The engine keeps its keys: they
appear in verdicts, gateway logs and snapshots. Renamed on 2026-10-25.

| Group | Name | Measures | Engine key | Earlier name |
|---|---|---|---|---|
| Typical Cadence | Call rate | calls in the last hour | `calls_last_hour` | calls in the last hour |
| | Write rate | writes in the last hour | `writes_last_hour` | writes in the last hour |
| | Breadth | distinct assets in the last hour | `assets_last_hour` | distinct assets in the last hour |
| | Repetition | calls with this tool on this asset in the last 10 minutes | `same_call_10m` | same call in 10 minutes |
| | Session duration | minutes since the session started | `session_length` | session length |
| | Hour of day | how often he calls within an hour of this time | `time_of_day` | time of day |
| Typical Footprint | Tool | the tool | `tool` | |
| | Asset | the asset, with the first-access floor | `asset` | |
| | Network | the caller's /16 range | `network` | v1–v3: the new-network rule |
| | Client | the client program, version dropped | `client` | app; v1–v3: the new-app rule |
| Red Flags | Burst | more calls in one minute than the limit | `burst` | burst |
| | Sweep | more distinct assets in one hour than the limit | `many_assets` | many assets in an hour |
| | Oversized request | a request over this tool's limit | `request_too_big` | request size |
| | Unsafe sequence | a write after reading a different sensitive asset, a blind write, an unreviewed merge | `sequence` | risky order |
| | Missing handshake | a tool call in a session that never sent `initialize` | `protocol_skip` | skipped "hello" |

| Mechanism | Name | Earlier name |
|---|---|---|
| "More than his usual", for counts | excess score | Way 1 |
| "Rarer than his usual", for values | rarity score | Way 2 |
| A flag he raises often counts less | habit discount | rule rarity |
| Something new for him that 3 or more other agents also started this week counts at most 0.5 | org discount | |
| A never-touched sensitive asset scores at least 0.9 (sensitivity 5) or 0.8 (sensitivity 4) | first-access floor | first-look floor |
| His first day: only the checks that need none of his past | warm-up | |
| The strongest score, its dimension, the second-strongest score | top score `s1`, reason `d*`, runner-up `s2` | |

---

## What changed in v4

**Decided on 2026-10-21:**

1. **"Policy" is renamed.** On 2026-10-21 it became Expected Conduct; on 2026-10-25, **Red
   Flags**, and every dimension, flag and mechanism got a short paper name
   ([why](#why-red-flags-not-policy-or-expected-conduct), [names](#names)). The engine's keys
   are unchanged.
2. **New network and new app are no longer rules.** They are Typical Footprint dimensions,
   *network* (/16) and *client* (the client program, version dropped), scored by rarity like
   tool and asset, with a ceiling of 0.9. A never-seen network is ×3.2 for a focused agent
   (×3.6 as v3's rule) and ordinary for one who roams; the org discount still applies.
3. **New tool is no longer a rule.** A tool he has not used in 90 days is scored by tool rarity,
   priced by how often he starts new tools (as in v1), ceiling 0.9, with the org discount.
4. **The first access to a sensitive asset is a floor on the asset's score** (the first-access
   floor), not a rule: a never-touched asset of sensitivity 5 scores at least 0.9, of
   sensitivity 4 at least 0.8. The values are v3's, it is still never org-discounted, and it
   still applies in the warm-up. Under the max this gives v3's `M` on every call; only the name
   of the strongest dimension (`asset`) and the runner-up change. The runner-up matters for the
   review list: in v3 a first access carried the asset's own rarity as its `s2`, in v4 it does
   not ([what v4 costs](#what-v4-costs)).
5. **`s1`, `s2` and the full formula** are written out in one place
   ([Step 2](#step-2-the-calls-multiplier-s1-s2-and-the-full-formula)).
6. **Why the max** is argued as a property of the design, not only a choice
   ([why the strangest wins](#why-the-strangest-wins-max-as-a-design-property)).
7. **Every dimension says why it matters** and what its ordinary look-alike is
   ([The dimensions](#the-dimensions)); **missing handshake** has its own section
   ([Missing handshake](#missing-handshake)).
8. **An ablation study is planned** ([Future work](#future-work-ablation-study)).

Everything else is v3: 15 dimensions and flags instead of 17.

---

## Step 1: a score per dimension

### Excess score: "more than his usual"

Used by **call rate**, **write rate**, **breadth**, **repetition** and **session duration**
(Typical Cadence).

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

A client that polls by design has a high usual, so repetition stays ordinary for it.

### Rarity score: "rarer than his usual"

Used by **tool**, **asset**, **network** and **client** (Typical Footprint), and by **hour of
day** (Typical Cadence).

```
e = (rare calls + 1) / (active days + 1)        "times per day"
s = c / (1 + 2 × e)                             c = 0.9 for tool, network and client; 1 for asset and hour of day
```

| Part | Means | Why |
|---|---|---|
| `e` | how many times a day he does something this rare | per day, not a plain share (see [Why "times per day"](#why-times-per-day-and-not-a-plain-share)) |
| `rare calls` | his past calls on **this thing and everything he used as little or less**, up to yesterday | if he touches rare things all the time, rare is normal for him |
| `active days` | days with at least one call, in the last 90 days, up to yesterday | turns a count into "per day" |
| `+1` (top) | read as "this call" | a never-used thing still gets a small number, not zero |
| `+1` (bottom) | read as "today" | a brand-new agent with 0 days never divides by zero |
| `2` | tolerance | every other day (`e` = 0.5) gives `s` = 0.5, so the multiplier is ×1 |
| `c` | the ceiling | a rare tool, network or client stays near ×3.2–3.6: one of them alone is a signal, not proof |

Network and client count **messages** (`initialize` and `tools/list` too, because they carry
the origin), on every message; tool and asset count tool calls. **Hour of day** uses its own
`e`:
`(his calls within one hour of this time + 1) ÷ (his active days of this kind + 1)`, with weekends
[blended](#weekends).

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

#### Something he never used: a new tool, asset, network or client

Something with count 0 has no count of its own. Its "rare calls" is **how often he started using
something new of that kind** (a new tool, a new asset, a new network, a new client), not
counting
his first 14 days (onboarding).
- If he rarely starts new things, a new one scores near the top.
- If he starts new things every day, a new one is ordinary for him.

| Agent (44 active days) | New things of this kind he started | A never-seen network, client or tool: s | M |
|---|---|---|---|
| Focused: one office network, one client | 0 | 0.86 | **×3.2** |
| Focused, one earlier change | 2 | 0.79 | ×2.6 |
| On a phone: a new /16 most days | about 30 | 0.38 | **×0.9** |

v3 gave all three ×3.6 (its rule). This is the point of v4's change: whether something new is
strange depends on how often *he* starts new things, which only a graded score can say. The
cases v3's rules caught and rarity alone would not are kept by two mechanisms: an explorer's
first access to payroll by the [first-access floor](#the-first-access-floor-a-sensitive-asset),
and an org-wide change by the [org discount](#org-discount).

#### The first-access floor: a sensitive asset

```
asset score = max( rarity score,  0.9 − 0.1 × (5 − asset sensitivity) )      only for an asset of sensitivity 4–5 he has not touched in 90 days
                                   sensitivity 5 → 0.9 (×3.6),  4 → 0.8 (×2.6)
```

- **Why a floor.** Rarity is calm for explorers: an agent who opens a new folder every day would
  score his first access to payroll ×0.8. The floor keeps a first access to a sensitive asset
  at ×3.6 (sensitivity 5) or ×2.6 (sensitivity 4) whoever accesses it.
- **Why it belongs to Footprint.** It asks "is this asset new for him?", the asset dimension's
  question, with the asset's sensitivity as a minimum. It needs none of his past, so it applies
  in the warm-up too: a brand-new identity reading payroll on its first day gets ×3.6.
- **No org discount.** Several agents starting to read secrets in the same week is not
  reassuring. In the large organisation, the discount hid 4 of 31 sensitive peeks in v3's tests.
- **Graded by the asset only.** Grading by the tool as well gained nothing in v3's tests; the
  tool already counts through `R_static`. See [v3](DIMENSION_FORMULAS_v3.md#first-look-at-a-sensitive-asset).
- A first *write* to a sensitive asset is usually also a blind write, so the unsafe-sequence
  flag is raised too.

#### The score as a curve

With `x = 1/e` ("he does it once every x days"), the rarity score is `s = c · x / (x + 2)`.
That's the same curve as the excess score.

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

| Agent | Today | This thing only | This thing + everything rarer |
|---|---|---|---|
| Focused (a few big things + payroll 3× in 30 days) | payroll | ×2.6 | ×2.6 |
| Explorer (the same + 40 small folders, about 2× each) | payroll | ×2.6 | ×0.8 |
| Bot posting to 300 channels in turn (about 9 posts per channel in 90 days) | any channel | ×2.8 on every post | ×1.0 (measured) |
| 26 tools used evenly (about 17 calls per tool in 90 days) | any tool | ×2.0 on every call | ×1.0 (measured) |

"This thing + everything rarer" is calm for bots, rotations and explorers.

#### Learning: once a day

The history updates once a day: every call today is compared with his history up to yesterday.
- A new folder, Q4-plan, stays new all day: each of its 12 calls on its first day scores ×4.4,
  so a new thing cannot be "trained" to look ordinary within the same day.
- The next day, Q4-plan is counted with its whole first day: one call on it scores ×1.6, then
  ×1.5, ×1.45 and ×1.4 on the following days.
- The cost: one busy new day stays red all day.

#### Weekends

A weekend call is compared with his weekend days, plus 4 days' worth of his all-days profile:

```
e_weekend = (his weekend calls within one hour of this time + 4 × e_all) / (his weekend days + 4)
e_all     = (his calls within one hour of this time, any day + 1) / (his active days + 1)
```

With no weekend days yet, a weekend call is judged by his all-days profile; with many, his
weekend profile wins; there is no cliff in between.

### Red flags: a set value

```
raised      → s = the flag's value
not raised  → the flag does not take part
```

| Flag | Raised when | Value |
|---|---|---|
| Burst | more calls in one minute than the learned limit (default 20) | 0.9 (×3.6), less if it is his habit ([habit discount](#habit-discount)) |
| Sweep | more distinct assets in one hour than the learned limit | 0.9, less if it is his habit |
| Oversized request | a request over **this tool's** learned limit | 0.9 |
| Unsafe sequence | a write after reading a different sensitive asset in the session · a write to a sensitive asset not read in 7 days · a merge with no review | 0.9, less if it is his habit |
| Missing handshake | a tool call in a session that never sent `initialize`, only if he sends it in at least half his sessions | 0.7 (×1.9) ([details](#missing-handshake)) |

Why each flag matters is in [The dimensions](#red-flags).

#### Habit discount

For burst, sweep and unsafe sequence, a flag he raises often counts less:

```
value = 0.9 / (1 + 2 × days he raised it / (his active days + 1))        last 90 days, up to yesterday
```

- Raised for the first time: 0.9 (×3.6).
- Raised every other day: 0.45 (it no longer takes part).
- Not used for oversized request (a habit of oversized requests is not reassuring: each one is
  its own paste) or missing handshake (it already switches itself off for a caller who rarely
  sends `initialize`).

#### Org discount

Something new for him (a tool, an asset, a network, a client) that **3 or more other agents also
started in the last 7 days** scores at most 0.5 (×1). That is an org-wide change: a server
release, a VPN change, a repository migration. Other agents only ever lower a score here, never
raise it. It does not lower the [first-access floor](#the-first-access-floor-a-sensitive-asset).

### Missing handshake

**What the handshake is.** An MCP session must start with the `initialize` handshake: the client
names itself (`clientInfo`), states its protocol version and its capabilities, and the server
answers with its own. Only then come `tools/list` and `tools/call`. The gateway marks a session
as started when the server assigns it a session id in its reply to `initialize`.

**When it is raised.** All of these must hold:
1. the message is a `tools/call` with a session id;
2. the gateway never saw that session start, *for this caller* (sessions are kept per caller);
3. he normally sends the handshake: at least 3 of his sessions seen, and at least half of them
   started with `initialize`;
4. he is past his warm-up (his first day).

**Cases**

| Case | Raised? | Why |
|---|---|---|
| An ordinary client: `initialize`, then tool calls | no | the session started properly |
| A script on his token sending `tools/call` with a session id the gateway never saw start (copied from his client, or made up) | **yes**, ×1.9 | not a standard MCP client: no handshake, no client name, no protocol version |
| Another caller using a session his client opened | **yes**, for the other caller | sessions are kept per caller, so for the second caller that session never started |
| A replay of recorded traffic after the gateway dropped the session | **yes** | as above |
| A client that resumes a session after a dropped connection, gateway still running | no | the gateway still remembers the session's start |
| A stateless client that never sends `initialize` (a curl-based bot, some HTTP SDKs) | no | he does not normally send it, so the flag is off for him (v1 edge case: ×0.97) |
| His first 3 sessions, or his first day | no | not enough history to say what is normal for him |
| A message with no session id, or a `tools/list` without `initialize` | no | the flag checks tool calls in a session only |
| **False alarm:** the gateway restarted while his desktop client kept its session open | yes, on every call of that session until the client reconnects | open sessions are not saved in the engine's snapshot ([open decisions](#open-decisions)) |
| **False alarm:** more than 50,000 open sessions (the oldest are dropped), or two gateway replicas that do not share state | yes | the session's start was forgotten, or seen by the other replica |

**Why it matters.** It is the only check on the *protocol* rather than on usage, and it asks a
question no other dimension asks: did this call come from the program he normally uses? A caller
whose client always sends `initialize`, sending a tool call without it, means something else
holds his credentials or his session: a hand-written script, a replay, a second program. In the
simulation, the personal script on someone's token skips `initialize`, and 3% of ordinary
sessions resume without it (the benign case).

**Why 0.7 (×1.9) and not 0.9 (×3.6).**
- It has benign causes: resumed sessions, a gateway restart, replicas, dropped sessions.
- On its own it says "a different program", not "a harmful call". What the call can do is
  priced by `R_static`, and the other dimensions say whether the call itself is strange.
- At ×1.9 it lifts the call above ordinary but stays under the ×3 alert line alone. When
  something else is strange too, it is the call's runner-up `s2` and moves the call up the
  review list (the personal script: a new network, a new client, 2 a.m. *and* no handshake).

### Summary: score → multiplier

| What happened | s | M |
|---|---|---|
| His average, or something he does once a day | 0.33 | 0.89 |
| **Twice his average, or something he does every other day** | **0.50** | **1.00** |
| 4× his average, or once in 4 days | 0.67 | 1.73 |
| 10× his average, or once in 10 days | 0.83 | 2.89 |
| A never-seen network, client or tool, focused agent (44 days) | 0.86 | 3.20 |
| A raised red flag | 0.9 | 3.62 |
| First access to a sensitivity-5 / sensitivity-4 asset (first-access floor) | 0.9 / 0.8 | 3.62 / 2.63 |
| Missing handshake (a red flag) | 0.7 | 1.90 |
| Never (long history) | 0.9–0.98 | 3.6–4.7 |

---

## Step 2: the call's multiplier: s1, s2 and the full formula

### s1 and s2

For one call `c`:

| Symbol | Means |
|---|---|
| `D(c)` | the dimensions that **take part** in `c`: a Cadence or Footprint dimension once he has history for it (after his first day), a red flag only when raised, the first-access floor whenever it applies |
| `s1(c)` | the **top score**: the strongest score in `D(c)`, `max of s_d(c)` |
| `d*(c)` | the dimension that gave `s1`: **the reason** shown with the score |
| `s2(c)` | the **runner-up**: the second-strongest score in `D(c)` (0 when fewer than two take part) |

Only `s1` sets `M`. `s2` never changes `M`, so it never changes a call's risk; it only orders
the daily review list when several agent-days have the same `M`.

### The full formula

```
Step 1, per dimension d in D(c):
  Typical Cadence, counts (excess score):
      s_d = (x + u) / (x + u + 2 × (μ + u))
            x = his number now, μ = his daily average of it, u = 1 unit
  Typical Footprint, and hour of day (rarity score):
      s_d = c_d / (1 + 2 × e_d)
            e_d = (N_d + 1) / (A + 1)
            N_d = his calls on this value and every value he used at most as often;
                  for a value he never used, the new values he started
            A   = his active days;  c_d = 0.9 (tool, network, client), 1 (asset, hour of day)
            org discount:        never used, and 3+ other agents started it in 7 days: s_d ≤ 0.5
            first-access floor:  asset never touched, sensitivity σ ≥ 4: s_asset ≥ 0.9 − 0.1 × (5 − σ)
  Red Flags, flag f, only when raised:
      s_f = v_f / (1 + 2 × k_f / (A + 1))                 (the habit discount)
            v_f = 0.9 (missing handshake: 0.7);  k_f = days he raised f
            (k_f = 0 for oversized request and missing handshake)

Step 2, the call:
  s1 = max of s_d over D(c)           top score;  d* = the dimension that gave it (the reason)
  s2 = second-largest s_d over D(c)   runner-up
  M  = 5   ^ (2 × s1 − 1)     when s1 ≥ 0.5
  M  = 0.7 ^ (1 − 2 × s1)     when s1 < 0.5
  M  = 1                      when D(c) is empty (warm-up, no flag raised)

Step 3, the risk:
  R = R_static × M            R_static 1–5, M 0.7–5  →  R 0.7–25

Review list, per day:
  each agent-day is its call with the largest M;
  rank agent-days by M, then by that call's s2; show the top k with their reason d*
```

| Part | Means | Why |
|---|---|---|
| `0.5` | the edge of normal | 2× usual, or every other day, gives exactly ×1 |
| `5` | the top | static 1–5 × 5 gives 25: both sides use the same 5-step scale |
| `0.7` | the bottom | familiar behaviour lowers the risk a little, by at most 30%, and never erases it |
| `2S − 1` / `1 − 2S` | how far `s1` is from 0.5, from 0 to 1 | a smooth curve: every +0.1 of `s1` above 0.5 multiplies `M` by about 1.38 |

**Example with s1 and s2.** Static 3; his usual is 100 calls an hour.

| Dimension | Situation | s |
|---|---|---|
| Call rate | 400 calls this hour | 0.67 |
| Hour of day | his usual hour | 0.33 |
| Tool | one he uses every other day | 0.50 |
| Asset | a folder he opens once in 10 days | **0.83** = `s1`, `d*` = asset |
| Network | his office network | 0.04 |
| Red Flags | none raised | do not take part |

`s1` = 0.83 (asset), `s2` = 0.67 (call rate). `M` = ×2.9 and `R` ≈ 8.7. The alert reads "asset
0.83, then call rate 0.67".

**Warm-up: his first day.** Until his first day is in his history, `M` = 1, except for the checks
that need none of his past: burst, oversized request, sweep, unsafe sequence and the first-access
floor.

| A brand-new identity on its first day, after 25 calls | M | Reason |
|---|---|---|
| an ordinary call with a tool new today | ×1.0 | warm-up |
| payroll (sensitivity 5), read or write | ×3.6 | asset, first-access floor |
| team deploy repository (sensitivity 4), read | ×2.6 | asset, first-access floor |

### Why the strangest wins: max as a design property

Take one call with four scores: hour of day 0.33, tool 0.33, call rate 0.33, network 0.86.

| Combine by | Result | |
|---|---|---|
| Average | 0.46 → ×0.97 | the strange thing is hidden |
| Sum | 1.85 | not on a 0–1 scale, and grows with every dimension added |
| **Maximum** | 0.86 → ×3.2 | the strange thing shows |

The max is not a shortcut: it is what makes the rest of the design work.

1. **Every score explains itself.** The dimension that set `s1` is the reason; `s2` is the
   runner-up. An operator reads "network 0.86, then hour of day 0.71", not a blend of 15
   numbers. The paper's claim of interpretable risk scores rests on this.
2. **One strange thing is enough.** Ordinary dimensions cannot hide it, however many there are.
   With an average, every dimension added would dilute the others.
3. **Related signals are not counted twice.** A stuck loop raises call rate, repetition and
   burst together. A sum would count one loop three times; the max counts it once. So
   dimensions that overlap can be kept without inflating false alarms.
4. **Bounded whatever the number of dimensions.** `M` stays in [0.7, 5] with 15 dimensions or
   30. A dimension can be added without recalibrating the others or the alert line.
5. **Monotone.** Raising any score never lowers `M`; lowering one never raises it. A stranger
   call never scores safer.
6. **It is well-founded because the scores share one scale.** Every score is built on the same
   curve `x / (x + 2)`, with 0.5 at "twice his usual" or "every other day". Without that common
   scale, a max would compare unlike things; with it, the max asks "how far past his ordinary
   is the furthest thing?".
7. **It makes the ablation exact.** The scores of different dimensions do not depend on each
   other (each reads only its own history), so leaving a dimension out changes `M` only on the
   calls where it was the strongest. Each dimension "owns" a known set of calls: the table of
   [what still causes alerts](#what-still-causes-alerts) is an exact split, and a leave-one-out
   ablation can be computed from one logged run ([Future work](#future-work-ablation-study)).
8. **A known operator in two fields.** In fuzzy logic the max is the standard OR (a call is
   strange if its cadence *or* its footprint is strange, *or* it raises a red flag). In
   outlier-detection ensembles, taking the maximum of the detectors' scores is the known
   alternative to averaging, which keeps an outlier that only one detector sees (Aggarwal &
   Sathe 2015; Zimek et al. 2014).

**Disadvantages, and what the design does about them:**
- **Medium signals don't add up:** an odd hour 0.7 plus an odd asset 0.7 still gives ×1.9. The
  tested alternative, `S = s1 + 0.3 × s2 × (1 − s1)`, caught mass cleanup 56% of the time
  instead of 22%, but raised false alarms from 6.2% to 7.0% of ordinary agent-days (v3 tests).
  v4 keeps `M` = f(`s1`) and lets `s2` act only on the ranking, where it costs no false alarms.
- **Ties at the top:** many agent-days tie at ×3.6. Ranking by `s2` next cut the days with a tie
  at the cut of the list from 29–52% to 3–9% (v3 tests). v4 has fewer exact ties, because a new
  network, client or tool is now graded instead of a fixed ×3.6: the cut falls in a tie on 0–3% of
  days (v3: 2–8%).
- **One noisy dimension is enough on its own:** see [what still causes alerts](#what-still-causes-alerts).

### Why this curve

**Benefits:** normal is exactly ×1; familiar lowers risk by at most 30%, strange raises it up to
×5; smooth, no cliffs; always in range, with no clipping.

**Disadvantages:** 5 and 0.7 are chosen by design, not learned; scores rarely get near 1, so ×5
almost never happens; static and dynamic weigh the same (see the grid in Step 3).

---

## Step 3: the risk

```
R = R_static × M          R_static 1–5,  M 0.7–5   →   R between 0.7 and 25
```

| Static \ s1 | familiar 0.25 | edge 0.5 | 0.67 | 0.83 | red flag 0.9 | 1.0 |
|---|---|---|---|---|---|---|
| 5 | **4.2** | 5.0 | 8.6 | 14.5 | 18.1 | 25.0 |
| 4 | 3.3 | 4.0 | 6.9 | 11.6 | 14.5 | 20.0 |
| 3 | 2.5 | 3.0 | 5.2 | 8.7 | 10.9 | 15.0 |
| 2 | 1.7 | 2.0 | 3.5 | 5.8 | 7.2 | 10.0 |
| 1 | 0.8 | 1.0 | 1.7 | 2.9 | 3.6 | **5.0** |

The two bold cells are about equal: a very strange call on a harmless tool scores about like a
familiar call on a dangerous tool.

The first-access floor makes the asset count twice for a first access: once in `R_static` and
once in `M`. That is on purpose: the alert line is drawn on `M` (×3), and a first access to
payroll should cross it while a first access to a deploy repository should not.

---

## The dimensions

Each dimension: what it catches, why that matters to the server, and what ordinary behaviour
looks like it (and what keeps that calm).

### Typical Cadence

| # | Dimension | Formula | Catches | Why it matters | Ordinary look-alike |
|---|---|---|---|---|---|
| 1 | Call rate: calls in the last hour | excess, u = 1 call | runaway loops, scraping, a bot gone wild | volume is how one call becomes many: the damage of a read or write grows with how often it runs | a release crunch or a busy on-call hour; tolerance 2 keeps up to twice his usual ordinary |
| 2 | Write rate: writes in the last hour | excess, u = 1 call | mass cleanup: many updates in a row | writes change the server's state; many in a row are where mistakes multiply | a planned migration; it shows once, then becomes his usual |
| 3 | Breadth: distinct assets in the last hour | excess, u = 1 asset | a bulk export across many repositories | breadth is the blast radius of misuse: reading one repository is a task, reading forty is an export | a lead reviewing the team's repositories; the count is against his own usual |
| 4 | Repetition: this tool on this asset in the last 10 minutes | excess, u = 1 call | a stuck loop polling one thing, under the burst limit | repeating one call is either a bug or extraction, and a loop on a write repeats its effect | a client that polls by design has a high usual |
| 5 | Session duration: minutes since the session started | excess, u = 1 minute | a stuck or hijacked session that never ends | a session open far longer than his usual keeps credentials and context live for longer than any task needs | desktop clients that keep one session open for hours: compared with *his* usual, not a fixed limit |
| 6 | Hour of day | rarity: his calls within one hour of this time, weekends blended | a 2 a.m. batch by a day worker; a script on his token at night | calls outside his hours are the ones no one is watching, and the ones least likely to be his | on-call nights, travel, a release crunch: these remain the main ordinary cause of alerts, by design |

### Typical Footprint

| # | Dimension | Formula | Catches | Why it matters | Ordinary look-alike |
|---|---|---|---|---|---|
| 7 | Tool | rarity, ceiling 0.9; a tool not used in 90 days is priced by how often he starts new tools | off-role tools (a triager merging), first use of a tool he has no task for | the tool is *what* the agent can do; an unusual tool is an unusual capability being exercised | a role change or a server release with new tools: the org discount covers the release |
| 8 | Asset | rarity; a never-touched sensitive asset (4–5) has the first-access floor, 0.9 / 0.8 | a peek at a sensitive repository; scope creep into other teams' assets | the asset is *what* the call touches; the static side prices its sensitivity, this asks whether *he* touches it | a new project or a repository migration: new assets for him, discounted when 3 others start them too |
| 9 | Network | rarity: the /16 range, ceiling 0.9 | a script on his token from a cloud machine; a stolen token used elsewhere | *where from* is the first sign that a call is not his: the token is the same, the place is not | a home ISP change, travel, a VPN change; a roaming agent who changes networks often stays calm |
| 10 | Client | rarity: the client program, version dropped, ceiling 0.9 | a personal script (`python-requests`) on a token that only ever used Claude Desktop | the client is the program at the keyboard; a new one means a new program acts as him | a client switch: shows once (×3.2 for a focused agent), then becomes his usual; upgrades keep the name and do not count |

### Red Flags

| # | Flag: raised when | Value | Catches | Why it matters | Ordinary look-alike |
|---|---|---|---|---|---|
| 11 | Burst: more calls in one minute than the learned limit | 0.9, habit discount | a runaway loop, a misconfigured bot | a server can be overloaded, or a rate limit exhausted for everyone, within a minute: too fast to wait for call rate's hourly count | pagination, a monthly report bot (the habit discount lowers a habit) |
| 12 | Sweep: more distinct assets in one hour than the learned limit | 0.9, habit discount | a bulk export that would stay ordinary for a broad agent | breadth's backstop (#3): one hour across more assets than anyone in the organisation ordinarily reaches, however broad his own usual | almost none: the limit is set so it is raised on 0.5% of ordinary agent-days |
| 13 | Oversized request: a request over this tool's learned limit | 0.9 | a big paste into an issue, a huge file write | what goes *into* the server: a paste of secrets into a public issue, a payload far beyond the tool's purpose | a legitimate big file write or long comment: the main ordinary cause of alerts (see below) |
| 14 | Unsafe sequence: a write after reading a different sensitive asset; a write to a sensitive asset not read in 7 days; a merge with no review | 0.9, habit discount | copying from a sensitive repository; blind writes; merging unreviewed code | order is how harm is assembled from harmless steps: each call alone is fine, the sequence moves data or skips a check | developers who often copy between repositories: the habit discount lowers it for them |
| 15 | Missing handshake: a tool call in a session that never sent `initialize`, if he normally does | 0.7 | a script, a replay, a second program on his credentials | the only protocol check: did this call come from the program he normally uses? ([details](#missing-handshake)) | resumed sessions, a gateway restart ([cases](#missing-handshake)) |

Two flags back up a Cadence dimension with one line for everyone: burst backs call rate and sweep
backs breadth. The Cadence dimension compares him with his own usual, so a broad or busy agent
can stay ordinary there; the flag still stops at the organisation's line.

### Removed

| Removed | When | Why |
|---|---|---|
| Same tool in 10 minutes | 2026-10-19 | replaced in v3 by "same call in 10 minutes" (tool and asset) |
| The fixed "session longer than 10 minutes" rule | 2026-10-19 | real desktop clients keep one session open for hours |
| Request size, "more than his usual" | 2026-10-20 (v2) | size is checked only by a flag (oversized request) |
| One request limit for all tools (10 KB) | 2026-10-20 (v3) | a limit per tool, learned |
| The 5-call warm-up | 2026-10-20 (v3) | with the history updating once a day, the warm-up is his first day |
| New network rule | 2026-10-21 (v4) | the network dimension in Typical Footprint |
| New app rule | 2026-10-21 (v4) | the client dimension in Typical Footprint |
| New tool rule | 2026-10-21 (v4) | tool rarity, priced by how often he starts new tools |
| First look at a sensitive asset, as a rule | 2026-10-21 (v4) | the first-access floor on the asset dimension, same values |

---

## Limits learned from traffic

Until the organisation writes its own limits, the gateway learns the red flags' limits from its
first 30 days of traffic (`src/mcp_security/behaviour/policy.py`), at the level of an
agent-day: each limit is set so the flag is raised on at most 0.5% of ordinary agent-days.

| Limit | Learned as | In the five simulated organisations |
|---|---|---|
| Burst | the agent-day's busiest minute | more than 48 calls a minute (29 in the large one) |
| Oversized request, per tool | the agent-day's largest request with that tool | issues 9–14 KB, comments 16–26 KB, file writes 83–543 KB; 1 KB for reads |
| Sweep | the agent-day's busiest hour, in distinct assets | more than 15 in all five |
| Required earlier steps (unsafe sequence) | tool B always came after tool A in the same session (99.5% of at least 50 sessions) | none found |

One limit for all tools is set by the tool with the biggest requests (file writes), so it misses a
15–100 KB paste into an issue; per tool, every paste was caught. A limit set on single calls
is raised for a busy agent almost every day; set per agent-day, it was raised on 3.0% instead of
3.7% of
ordinary agent-days. Details: [v3](DIMENSION_FORMULAS_v3.md#limits-learned-from-traffic).

---

## Simulation (v4)

The same five simulated GitHub organisations as v3, with mostly ordinary traffic (the setting is in
[v3](DIMENSION_FORMULAS_v3.md#simulation-v3)): the main one (150 agents), a second seed (150),
heavy file writes (150), a small one (60) and a large one (300); 180 days, the last 90 scored.
v3 is `v3 (decided)`, rescored with the same code as v4. The shipped engine gives the simulation
engine's `M` and strongest dimension on every message, for v3 and for v4 (3,495,900 messages of
the main organisation; 0 differ).

**False alarms and gray episodes**

| Organisation | Agents | Ordinary agent-days at ×3: v3 → **v4** | Gray episodes caught at ×3: v3 → **v4** | Gray episodes on the daily list: v3 → **v4** | Days the list's cut falls in a tie: v3 → **v4** |
|---|---|---|---|---|---|
| Main | 150 | 3.2% → **2.7%** | 63% → **63%** | 59% → **58%** | 7.7% → **2.2%** |
| Second seed | 150 | 3.4% → **2.8%** | 65% → **65%** | 50% → **48%** | 2.2% → **0.0%** |
| Heavy file writes | 150 | 2.3% → **1.8%** | 78% → **78%** | 59% → **54%** | 7.7% → **2.2%** |
| Small | 60 | 3.2% → **2.5%** | 74% → **74%** | 69% → **71%** | 5.5% → **3.3%** |
| Large | 300 | 3.0% → **2.5%** | 72% → **72%** | 57% → **57%** | 6.6% → **1.1%** |
| **Mean** | | **3.01% → 2.46%** | **70.7% → 70.7%** | **59.0% → 57.8%** | |

- **18% fewer false alarms, in every organisation,** all of it on people (3.41% → 2.68% of their
  ordinary days); bots are unchanged (2.32%).
- **The same gray episodes are caught at ×3.** By kind, one mass cleanup is lost and one scope
  creep is gained, out of 460 episodes.
- **Fewer ties at the cut of the daily list,** because a new network, client or tool is now graded
  instead of a fixed ×3.6.
- Main organisation, per day: 2.1 ordinary agent-days at ×3 out of 150 agents (v3: 2.5), plus 3.1
  on days with a labelled life or org change (v3: 3.4). Ordinary *calls* at ×3: 0.1% (v3: 0.2%).

**Where the drop comes from** (ordinary agent-days at ×3, the two changes alone):

| Organisation | v3 | network and client in Footprint only | new tool through tool rarity only | v4 (both) |
|---|---|---|---|---|
| Main | 3.2% | 2.7% | 3.1% | 2.7% |
| Second seed | 3.4% | 2.9% | 3.3% | 2.8% |
| Heavy file writes | 2.3% | 1.9% | 2.1% | 1.8% |
| Small | 3.2% | 2.6% | 3.1% | 2.5% |
| Large | 3.0% | 2.5% | 3.0% | 2.5% |

Almost all of it is the network: the new-network rule caused 17% of v3's false alarms, and the
network dimension causes 1% of v4's.

**Ordinary life and org-wide changes at ×3 or more** (all five organisations, share of their days)

| Change | Days | v3 | **v4** | v4's main cause (main organisation) |
|---|---|---|---|---|
| New hire (onboarding days) | 347 | 28% | **15%** | unsafe sequence |
| Home ISP change | 42 | 38% | **24%** | — (none at ×3 in the main organisation) |
| Role change | 140 | 18% | **14%** | tool |
| Org: server release with new tools | 843 | 17% | **14%** | tool |
| Org: VPN change | 711 | 11% | **9%** | oversized request |
| Back from vacation | 949 | 7.7% | **6.0%** | oversized request |
| Client switch | 119 | 49% | **45%** | client, by design |
| Team transfer | 162 | 2.5% | **1.8%** | oversized request |
| New project | 6,900 | 8.7% | **8.3%** | asset |
| On-call night | 323 | 11% | **11%** | hour of day |
| Org: repository migration | 853 | 15.5% | **15.6%** | asset |
| Release crunch | 1,917 | 32% | **32%** | hour of day |
| Travel | 121 | 39% | **39%** | hour of day, by design |
| Monthly report (a bot) | 75 | 100% | **100%** | burst |

New hires gain the most: their new home networks and their first tools are now graded against
how often they start new things, and a new hire starts new things often.

**Gray episodes by kind** (all five organisations; "calls" is the share of the episode's calls at
×3, for gating call by call)

| Kind | Episodes | v3: caught | **v4: caught** | v4: calls at ×3 |
|---|---|---|---|---|
| Big paste (15–500 KB) | 59 | 100% | **100%** | 100% |
| Misconfigured bot loop | 15 | 100% | **100%** | 96% |
| Personal script on someone's token | 32 | 100% | **100%** | 100% |
| Slow loop on one thing | 35 | 100% | **100%** | 82% |
| Bulk export across repositories | 64 | 100% | **100%** | 79% |
| Peek at a sensitivity-5 repository | 63 | 90% | **90%** | 90% |
| Saturday 2 a.m. batch by a day worker | 29 | 79% | **79%** | 79% |
| Copy from a sensitive repository | 42 | 48% | **48%** | 28% |
| Scope creep (other teams' repos, two weeks) | 40 | 28% | **30%** | 2% |
| Mass cleanup (many updates in a row) | 34 | 26% | **24%** | 8% |
| Over-fetching (large pages) | 47 | 0% | **0%** | 0% |

The personal script is still caught every time without the new-network and new-app rules: it
runs at 1–3 a.m., so hour of day scores it about ×5 (4.96–4.97 in the heavy-file-writes
organisation), above what any of v3's rules gave.

### What still causes alerts

Ordinary agent-days at ×3 are 1.8–2.8%. Their causes (the alerting call's `d*`), averaged over
the five organisations:

| Cause | v3 | **v4** | Why |
|---|---|---|---|
| Oversized request | 58% | **71%** | a legitimate big file write or long comment over the tool's learned limit; the flag is unchanged, its share grew because the others shrank |
| Tool | 10% + new tool 8% | **18%** | a tool he uses once in weeks, or one he has not used in 90 days |
| Asset | 2% + first access 0.4% | **4%** | |
| Unsafe sequence | 3% | **4%** | after the habit discount, only agents who rarely do it |
| Network | new network 17% | **1%** | |
| Session duration, hour of day, sweep, client | 2% | 2% | |

### What v4 costs

**The daily list catches slightly fewer gray episodes:** 59.0% → 57.8% on average (from −5 points
in the heavy-file-writes organisation to +3 in the small one). In the heavy-file-writes
organisation the whole drop is one kind, copies from a sensitive repository (5 of 7 episodes on
the list → 1); every other kind is the same or better. Two mechanisms, both consequences of the
v4 changes:

1. **The first access and the asset's rarity are one score now.** In v3, a first access gave
   two scores: the rule (0.9) and the asset's own rarity (0.41–0.54 in these episodes), so the
   rarity became the call's `s2` and won the tie-break among ×3.6 agent-days. In v4 the floor
   *is* the asset score, so `s2` falls to the next dimension (about 0.22). `M` is the same
   (×3.6).
2. **A first-time tool is graded.** Two copies used a tool new to the agent: ×3.6 as a rule in
   v3, ×3.3 in v4, now below the ordinary ×3.6 oversized-request alerts.

At ×3 (gating call by call), nothing was lost: copies are caught 48% of the time in both. What
to do about the list is an [open decision](#open-decisions).

---

## In the engine

`src/mcp_security/behaviour/engine.py` runs v4 by default. A route picks another design with
`"design": "v1"`, `"v2"` or `"v3"` in its behaviour policy (`BehaviourConfig.design`).

Verdicts, gateway logs and snapshots use the engine keys, not the paper names: the mapping is
in [Names](#names). What v4 changed in them:

| Group | v4 keys | v3 keys |
|---|---|---|
| Typical Cadence | `calls_last_hour`, `writes_last_hour`, `assets_last_hour`, `same_call_10m`, `session_length`, `time_of_day` | the same |
| Typical Footprint | `tool`, `asset` (with the first-access floor), `network`, `client` | `tool`, `asset`; and the rules `new_tool`, `new_network`, `new_client`, `sensitive_first_look` |
| Red Flags | `burst`, `many_assets` (sweep), `request_too_big` (oversized request), `sequence` (unsafe sequence), `protocol_skip` (missing handshake) | the same |

- `Verdict.strongest` is `d*`, `Verdict.score` is `s1`, and `s2` is the second-largest value in
  `Verdict.scores`. `Verdict.above_ordinary` lists the dimensions past 0.5, strongest first (the
  gateway shows them as the reason).
- A snapshot saved by v3 or earlier loads into v4. Its networks and clients have no per-day
  counts, so the network and client dimensions take part only after one day of their own
  history.
- `reports/experiments/dynamic_dimensions/normal_org_sim.py --check-port` checks that the shipped
  engine gives the simulation engine's `M` and strongest dimension on every message, for v3 and
  v4.

---

## Parameters

| Parameter | Value |
|---|---|
| History | his last 90 days, up to yesterday (updated once a day) |
| Warm-up | his first day; the checks that need none of his past still apply |
| Onboarding | first uses in his first 14 days don't count as "starting something new" |
| Tolerance | 2: up to twice his usual, or every other day, is ordinary |
| Units | 1 call, 1 minute, 1 asset |
| Ceilings | 0.9 for tool, network and client; 1 for asset and hour of day |
| Multiplier | 0.7 to 5; exactly 1 at the edge of ordinary |
| Flag values | 0.9 (×3.6); missing handshake 0.7 (×1.9) |
| First-access floor | 0.9 (sensitivity 5) or 0.8 (sensitivity 4), never discounted |
| Habit discount | burst, sweep, unsafe sequence: `0.9 / (1 + 2 × days raised / (active days + 1))` |
| Org discount | 3 or more other agents started the same new tool, asset, network or client in the last 7 days → at most 0.5 |
| Weekends | blended with all days, 4 pseudo-days |
| Limits | learned from the first 30 days, raised on at most 0.5% of agent-days; defaults burst 20 a minute, request 10 KB |
| Sensitive | asset sensitivity 4 or more; a write to one not read in 7 days raises unsafe sequence |

---

## Where the formulas come from

- **One shape for every graded score:** `x / (x + 2)`. The excess score uses `x` = today ÷ his
  usual (with `u`); the rarity score uses `x` = once every `x` days (`x` = 1/`e`). It is the
  saturating curve of BM25 term frequency, `tf / (tf + k)`, and of the Logtalk anomaly
  detector, `Raw / (1 + Raw)`.
- **The `+u` and `+1` are additive (add-one) smoothing,** as in the methodology deck's
  `Likelihood = N(f,v) / (N_total + K_f)` with a bounded history.
- **"This thing + everything rarer"** is an empirical p-value: the share of his past that was at
  least this rare.
- **The max** is the fuzzy-logic OR, and the maximization combination of outlier ensembles
  (Aggarwal & Sathe 2015, who compare it with averaging; Zimek et al. 2014).
- **Design choices checked by simulation,** not taken from a paper: the tolerance 2, the units,
  the ceilings 0.9, per-day counting, the multiplier's 5 and 0.7, the flag values, the floor
  values, the 14 days of onboarding, the 4 weekend pseudo-days and the org discount's 3 agents in
  7 days.

---

## Future work: ablation study

Not done yet; needed for the paper. Planned on the five simulated organisations, reporting first
the false alarms on ordinary agent-days and the ordinary life and org changes at ×3, then the
gray episodes caught and on the review list:

| Arm | Question |
|---|---|
| Leave one dimension out (each of the 15) | does every dimension earn its place? |
| Leave one group out (Typical Cadence, Typical Footprint, Red Flags) | does every group earn its place? |
| The combiner: max (v4) · mean · noisy-OR `1 − ∏(1 − s)` · `s1 + 0.3 × s2 × (1 − s1)` | is the max the right combiner, as argued above? |
| The review list: ties at random · by `s2` · by the number of dimensions past 0.5 | how much does `s2` add? |
| Habit discount off · org discount off · first-access floor off | do the three safety valves pay for themselves? |
| Warm-up: first day · 5 calls · none | |
| Ceilings 0.9 → 1 for tool, network, client | |
| v3's rules back in place of the Footprint dimensions (= v3) | what did v4's move cost or gain? (the partial engines below are its first two rows) |

Because of property 7 of the max, the dimension and group arms need no rerun: log every call's
scores once (`Verdict.scores`), then recompute `M` without the left-out scores. The combiner,
the safety valves and the warm-up change the scores themselves, so they need a rerun of
`normal_org_sim.py`.

---

## Open decisions

1. **The daily list and the first access** ([what v4 costs](#what-v4-costs)): 1.2 points fewer
   gray episodes on the list, mostly copies from a sensitive repository. Options: accept it
   (copies are unsafe sequence's job, and at ×3 nothing changed); or, *in the ranking only*,
   count the first-access floor and the asset's rarity as two scores, as v3 did. The second recovers v3's
   tie-break but counts the asset twice in `s2`. Not tested yet; it belongs in the ablation.
2. **Open sessions are not saved in the snapshot.** After a gateway restart, every call in a
   session that stays open raises missing handshake (×1.9) and restarts its session duration.
   Saving each open session's start time and `initialize` flag would close it.
3. **The sweep limit from a gateway log:** `policy.py` learns it only from calls with resolved
   assets, which a gateway log does not carry, so a policy learned from a log leaves the flag
   off (breadth still runs).
4. **Over-fetching** (a large page size) cannot be seen without reading one argument.
5. **Reasons for the settings:** 90 days, the 0.5% of agent-days for learned limits, the floor
   values and the ceilings come from the simulation, not from data of a real organisation.

---

## References

- C. C. Aggarwal and S. Sathe, "Theoretical Foundations and Algorithms for Outlier Ensembles,"
  *ACM SIGKDD Explorations Newsletter* 17(1), 2015. [doi:10.1145/2830544.2830549](https://doi.org/10.1145/2830544.2830549)
  (the average and maximization combination functions and their trade-offs).
- A. Zimek, R. J. G. B. Campello and J. Sander, "Ensembles for Unsupervised Outlier Detection:
  Challenges and Research Questions," *ACM SIGKDD Explorations Newsletter* 15(1):11–22, 2014.
  [doi:10.1145/2594473.2594476](https://doi.org/10.1145/2594473.2594476).
- The bounded shape `x / (x + c)`: BM25 term-frequency saturation,
  [Stanford IR lecture notes](https://web.stanford.edu/class/cs276/handouts/lecture12-bm25etc.pdf);
  the [Logtalk anomaly detector](https://logtalk.org/handbook/libraries/z_score_anomaly_detector.html).
- The methodology deck: `Likelihood = N(f,v) / (N_total + K_f)`, with a bounded history.
- MCP lifecycle: the `initialize` handshake comes first in every session
  ([specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)).
- Code:
  - `src/mcp_security/behaviour/engine.py` (v4 by default), `policy.py` (the learned limits);
  - `normal_org_world.py`, `normal_org_engines.py` (v4: the switches `origin_rarity`,
    `tool_rarity_first_use`, `sensitive_floor`), `normal_org_sim.py` (the engine `v4`);
  - results: `results/normal_org_sim.md`, `results/normal_org_sim_seed11.md`,
    `results/normal_org_git_heavy_files.md`, `results/normal_org_git_small.md`,
    `results/normal_org_git_large.md`.
- v1's stress test (33 edge cases, 9 organisations) and v3's detailed tables:
  [v3](DIMENSION_FORMULAS_v3.md).
