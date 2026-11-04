# The dynamic score: how unusual is this call for this agent?

This report defines the dynamic part of the risk score: its six dimensions, its single formula and
the reasons behind each choice. It compares eight candidate formulas and states the limits. It ends
with a LaTeX draft written in the same style as the paper's static section. The MCP server is the
protected asset and the calling agent is the threat.

- **Status (2026-10-29):** the formula counts the agent's past **calls**, the author's choice for
  now. Counting days instead is the planned improvement (§4). The design has been checked in a
  prototype but is not yet in the engine.
- **Numbers:** all come from [probes/m_formula_candidates.py](probes/m_formula_candidates.py) on
  synthetic agents. They are design checks, not paper results.

## 1. The idea

The static score says how dangerous a call **can** be: what the tool does, how sensitive the asset
is, how far one call reaches and how risky its parameter values are. It cannot tell whether the
agent making the call is acting like itself. The dynamic score adds exactly that, and nothing else:

```text
Risk(c) = Risk_static(t, a) × M(c)          M ∈ [0.78, 5]
```

- **M = 1** when the call is ordinary for this agent.
- **M rises towards 5** the less often this agent has done anything like it.
- **M falls slightly below 1** for its deepest habits.

M uses only what is known **before** the call runs:
- the agent id (issued by the operator);
- the time;
- the tool;
- the asset the call names, resolved by the same binding layer as the static score.

Argument values belong to the static score (parameter risk), and call outcomes never change the
score of the same call.

## 2. The six dimensions

All six compare the call with **the same agent's own past calls**. They form two groups: what
the agent touches, and how much and when.

### Typical Footprint: what does the agent touch?

| Dimension | Question | Unusual when | Why it matters to the server | Ordinary look-alike |
|---|---|---|---|---|
| **Tool** | Which capability is it using? | a tool this agent rarely or never uses | An agent that reaches for a capability outside its task is either confused or no longer doing its job: a triage bot that starts merging. | A new tool that becomes part of the job settles within about two weeks of daily use. |
| **Asset** | What is it working on? | a repository, channel, calendar, table or folder it rarely touches | Scope creep and data hunting start with assets the agent has no reason to open. The static score prices how sensitive the asset is; here we ask only whether it is new for this agent. | An agent that opens new resources every few days is not surprised by one more. |
| **Tool on asset** | Is it doing something new to something familiar? | this tool is rarely used on this asset, among the past calls on that asset | Misuse often keeps to familiar resources but changes the action: a delete on a calendar it only reads, a write to a table it only queries. | A rarely used asset gives little evidence (few calls), so a first combination there stays mild. |

### Typical Cadence: how much, and when?

| Dimension | Question | Unusual when | Why it matters to the server | Ordinary look-alike |
|---|---|---|---|---|
| **Calls this hour** | How fast? | more calls in the hour than its usual peaks (in doublings) | Volume is how one harmful call becomes thousands: runaway loops, scraping, mass edits. | A busy day is up to about twice its usual peak; only a new doubling counts. |
| **Breadth** | How wide? | more distinct tool-and-asset pairs in the hour than usual (in doublings) | Enumeration and sweeps touch many things quickly: reading forty repositories is an export, not a task. | Periodic jobs, such as a monthly report, become part of the history after their first runs. |
| **Time of day** | When? | an hour it rarely works | Calls outside an agent's hours are the ones no one watches, and the least likely to be its own task. | A night-shift agent works at night, and an always-on bot has no unusual hour. |

**How "at least as unusual" is decided:**
- **Tool, Asset, Time of day:** the value was used in as few past calls, or fewer.
- **Tool on asset:** how often this tool was used, among the past calls on this asset.
- **Calls this hour, Breadth:** the amount reached the same doubling, or a higher one.

### Grounding in user and entity behaviour analytics (UEBA)

Every dimension, and every rule the formula applies to it, follows established UEBA practice. The
sources are the verified entries in [03-ueba-insider-threat-and-datasets.md](03-ueba-insider-threat-and-datasets.md).

| Our dimension | UEBA counterpart | How UEBA scores it | How we score it |
|---|---|---|---|
| Tool | Sentinel's "first time" and "uncommonly by user" insights per action [V1, V2]; GuardDuty flags the API call that is unusual for the identity [V19] | yes or no: first time in 30-180 days, uncommon in 10 days | the share of the agent's past calls whose tool was at least as rare |
| Asset | Sentinel's per-resource insights [V1]; Exabeam's first access to a system [V11]; Elastic's `rare` [V15] | first time or uncommon; Exabeam weights it by how critical the system is | the same share, for assets. How critical the asset is stays in the static score, which M multiplies |
| Tool on asset | GuardDuty's "which factors of the API request are unusual for the user identity" [V19]; Exabeam's per-user histograms per activity [V10] | per action on a resource | the share of past calls on this asset that used this tool |
| Calls this hour | Sentinel's burst-of-operations insight [V1]; Exabeam's numerical models [V10]; Elastic's counts per time bucket [V15] | a count per time bucket, against the user's own history | the hour's count, in doublings, against the agent's past calls |
| Breadth | Entra's "mass access to sensitive files", only when uncommon for the user [V18]; Elastic's distinct counts per bucket [V15] | distinct objects per bucket, against the user's history | distinct tool-and-asset pairs per hour, in doublings |
| Time of day | Exabeam's time-of-week model [V10]; Elastic's `time_of_day` [V15]; the time-of-day feature in risk-based authentication [D23] | the position in the day or week, against the user's history | the share of past calls at an hour at least as rare |

**What we keep from UEBA:**
- **A baseline per entity,** never one global rule. Every product above does this.
- **"First time" is the strongest signal, but discounted when the entity often does first-time
  things.** Sentinel gives a user's first Azure operation a high priority but a low anomaly score
  "because occasional first-time actions are common" [V2]. Exabeam's anomaly factor depends on how
  often a rule triggers [V12], and GuardDuty learns repeated behaviour as expected [V19]. In our
  formula this discount is automatic: k counts the agent's own past first-time calls.
- **A history of weeks to months, and a warm-up.** Sentinel uses 10-180 days and Exabeam 60-90
  days. Exabeam waits for its models to converge, Entra waits at least 5 days, and Elastic needs 20
  buckets [V2, V9, V15, V18]. Ours keeps a history and ramps up over the first 1,000 calls.
- **Raise, don't block.** Behaviour only steps risk up, as Okta's behaviour detection does [V17].
- **The score as a likelihood ratio.** Risk-based authentication scores a login by how much less
  likely its features are for this user than for a reference (Freeman et al., NDSS 2016) [D23].
  Our M = (typical share / this call's share)^γ is that ratio, with the agent's own typical call
  as the reference.

**Where we differ, and why:**

| UEBA practice | Ours | Why |
|---|---|---|
| Yes/no insights and expert-set risk points (Exabeam: points per rule, "notable" at 90; Splunk: alert above 100 per 24 hours) [V9, V11] | a graded share from the agent's own history | There are no labels or expert weights to justify. Graded rarity needs no tuning, and its false-alarm rate is bounded |
| Peer groups built from directory or HR data (Sentinel, Splunk UBA, Exabeam) [V2] | the agent's own history only | An MCP gateway sees only an agent id and has no directory |
| A sum over a session or 24 hours (Exabeam, Splunk) [V9] | one score per call, before it runs | The score must exist before the call executes. A daily sum can still order the review list (future work) |
| Sessions or time buckets as the unit of counting [V10, V15] | calls, for now | The author's choice for now. Buckets are the planned improvement (§4) |

**Paper sentence:** *the dynamic score follows UEBA practice: per-entity baselines, first-time and
uncommon behaviour per attribute, uncommon volume per time bucket and a habit discount. It replaces
yes/no insights and expert risk points with each agent's own empirical rarity, so it needs no
labels or tuned weights and its false-alarm rate is bounded.*

## 3. The formula, explained simply

**The one question:** *how many of this agent's past calls were at least this unusual?*

1. **Each dimension:** count the agent's past calls that were at least as unusual on that
   dimension.
2. **The whole call:** take the call's most unusual dimension and compare it with each past call's
   most unusual dimension. Ties are broken by the next most unusual one. Let **k** be the number
   of past calls that were at least as unusual.
3. **The multiplier:**

```text
M = ( (n + 1) / (2k + 1) )^γ ,        γ = ln 5 / ln( max(n, 1000) + 1 )
n = the agent's past calls in its history,   k = past calls at least as unusual (0 … n)
```

What M looks like for an agent with 4,000 past calls:

| Share of its past calls that were at least this unusual | M |
|---|---|
| none (never seen) | ×5.00 |
| 1 in 1,000 | ×3.26 |
| 1 in 100 | ×2.13 |
| 1 in 10 | ×1.37 |
| half | ×1.00 |
| all | ×0.87 |

Each halving of the share raises M by the same step, ×1.14 at this history size.

**Worked examples** (illustrative k; the static score uses the paper's weighted sum):

| Call | n | k | (n+1)/(2k+1) | M | Static | Risk |
|---|---|---|---|---|---|---|
| Routine read of its usual channel | 4,000 | 2,000 | 1.0 | ×1.00 | 1.8 | 1.8 |
| Monthly report over many tables (1 in 100 past calls as unusual) | 4,000 | 40 | 49 | ×2.13 | 2.7 | 5.8 |
| A delete on a calendar it only ever reads | 4,000 | 3 | 572 | ×3.43 | 3.0 | 10.3 |
| A 3 am sweep of 25 repositories (nothing like it before) | 4,000 | 0 | 4,001 | ×5.00 | 2.1 | 10.5 |
| Its deepest habit | 4,000 | 4,000 | 0.5 | ×0.87 | 2.7 | 2.4 |
| A new agent's first unusual call | 10 | 0 | 11 | ×1.75 | 3.0 | 5.2 |

**Where the numbers come from:**

| Number | Origin |
|---|---|
| ½ | A behaviour seen in half the agent's calls gives exactly ×1 (the mid-p correction, Lancaster 1961). It also gives a new agent ×1. |
| 5 | M spans the same factor of 5 as the static 1-5 scale, so neither layer outweighs the other. |
| γ | It makes "never in the agent's history" land exactly on ×5. |
| 1,000 | The number of past calls an agent needs before a never-seen behaviour reaches ×5. Below it, M ramps up instead of jumping. |
| 0.87 | It is not chosen; it follows from the ½. |

**New agents.** A new id starts at ×1. Something never seen before gives ×1.18 after 1 past call,
×1.75 after 10, ×2.93 after 100 and ×5 from 1,000 calls on.

**Guarantee.** If an agent's ordinary calls are exchangeable, a given call reaches ×5 with
probability at most 1/(n + 1) (a conformal p-value; Bates et al., Annals of Statistics 2023). The
guarantee is per call, so an agent that makes more calls a day has more chances in a day.

**Known costs of counting calls, to improve later.** Calls from one busy hour are not independent
evidence (NIDES, SRI 1994). In the comparison (§4) this showed up three ways:
- ordinary days rise to about ×1.4-1.9;
- a new tool used daily for two weeks still scores about ×2.5;
- one huge burst day teaches the agent that bursts are normal.

Insider-threat and enterprise log analysis count per user-day instead (Le et al., IEEE TNSM 2020;
Beehive, ACSAC 2013). Counting days (F) passed about 30 more of the 125 checks.

### Every variable: why it is there, how it scales, how it moves the score

```text
M = ((n + 1) / (2k + 1))^γ ,   γ = ln 5 / ln(max(n, n0) + 1),   n0 = 1,000,   Risk = Risk_static × M
```

| Variable | What it is | Why it is there | How it scales across MCP servers |
|---|---|---|---|
| **n** | the agent's past calls in its history (the last 90 days, as in the deck) | The amount of evidence. UEBA always scores against the entity's own baseline (Sentinel 10-180 days, Exabeam 60-90 days). | A plain count of calls, so it works for any server. It is large for busy agents (a CI bot on GitHub: tens of thousands) and small for quiet ones (a calendar assistant: hundreds). |
| **k** | of those n calls, how many were at least as unusual as this one | UEBA's "first time or uncommon for this user", made a number. It gives the habit discount automatically: an agent that often does new things has a large k for new things. | "At least as unusual" uses only what every MCP call has: the tool name, the asset the binding layer names, and the time. |
| **½** (it appears as n + 1 and 2k + 1) | this call counts as half an observation | Nothing divides by zero, a new agent gets ×1, and behaviour seen in half the calls gives exactly ×1 (mid-p, Lancaster 1961). | The same everywhere. |
| **5** | the top of M | It is the same span as the static 1-5 scale, so behaviour can move a call across the whole static range and no further. | The same everywhere. |
| **γ** | the exponent | It makes "never seen in the agent's history" exactly ×5, and makes every halving of k the same step. | It is computed from n, so each agent gets its own scale with no tuning per server: 0.233 at 1,000 calls, 0.194 at 4,000, 0.140 at 100,000. |
| **n0 = 1,000** | the warm-up | Below 1,000 past calls, "never seen" ramps up instead of jumping to ×5, like UEBA's warm-ups (Exabeam waits for its models to converge, Entra waits 5 days, Elastic needs 20 buckets). | One number for all servers, but a low-volume agent reaches it late (corner case 2). |
| **Doublings** (Calls this hour, Breadth) | amounts are compared in bins: 1, 2-3, 4-7, 8-15, … | Each is relative to the agent's own level: a 10% busier hour is not a record, twice the peak is. | Scale-free: going from 20 to 40 calls an hour is the same step as going from 2,000 to 4,000. |
| **Most unusual dimension first** | how the six dimensions become one k | Without it, every call looks a little unusual somewhere and M inflates (a median of ×1.9 in our tests). | The same everywhere. |

**How each variable moves M:**

| k, with n = 4,000 | 0 | 1 | 3 | 10 | 40 | 100 | 400 | 2,000 | 4,000 |
|---|---|---|---|---|---|---|---|---|---|
| M | ×5.00 | ×4.04 | ×3.43 | ×2.77 | ×2.13 | ×1.79 | ×1.37 | ×1.00 | ×0.87 |

| n, for something never seen (k = 0) | 0 | 10 | 100 | 180 | 900 | 1,000 or more |
|---|---|---|---|---|---|---|
| M | ×1.00 | ×1.75 | ×2.93 | ×3.36 | ×4.88 | ×5.00 |

| n, for a behaviour in 1% of past calls | 1,000 | 4,000 | 100,000 |
|---|---|---|---|
| M | ×2.46 | ×2.13 | ×1.73 |

For doublings, take an agent whose usual peak is 20 calls an hour (the 16-31 bin). An hour with 30
calls stays in the same bin, so nothing changes. An hour with 40 calls is in the next bin (32-63),
which is a record, so M rises.

**Examples per dimension:**

| Dimension | M goes up | M stays at about ×1 or below |
|---|---|---|
| Tool | GitHub: a comment bot calls `merge_pull_request` for the first time | its daily `add_issue_comment` |
| Asset | SQLite: a reporting agent queries `salaries` for the first time | its daily queries on `orders`; a Slack bot that joins new channels every week opens one more |
| Tool on asset | Calendar: `delete-event` on a calendar it only ever reads | `list-events` on the same calendar |
| Calls this hour | Filesystem: 300 reads in an hour from an agent whose peak is 20 | a busy hour of 30 (the same doubling) |
| Breadth | GitHub: 25 repositories in one hour, against a usual 3 | a monthly report that does this every month (it is in the history) |
| Time of day | Slack: posting at 3 am from a 9-to-5 agent | a night-shift or always-on agent at night |

**Why it holds across different MCP servers:**
- It uses only what every call carries: the agent id, the time, the tool name, and the asset that
  the binding layer resolves against the policy register (a repository, channel, calendar, table
  or folder). The binding layer has no per-server code.
- Everything is relative to the agent's own history, so no threshold in calls per hour or bytes
  has to change from one server to another.
- The few global numbers (½, 5, n0) are set by reasons that do not depend on the server.

**Corner cases:**

| # | Case | What happens | Note or mitigation |
|---|---|---|---|
| 1 | A brand-new agent id | n = 0 gives ×1, and M ramps up with its history | A fresh id is the cheapest evasion. The rate of new ids is a separate signal |
| 2 | A low-volume agent | 2 calls a day gives n ≈ 180 in 90 days, so "never seen" reaches only ×3.36 (×4.88 at 10 calls a day) | Counting days or buckets (planned), or a lower n0 |
| 3 | A very busy agent | the same 1% behaviour gives ×1.73 at 100,000 calls against ×2.46 at 1,000; more calls a day mean more chances of a false ×5 (at most 1/(n+1) per call) | Counting buckets fixes both |
| 4 | One huge burst | its thousands of calls enter the history, so later bursts look normal (×1.2 in our tests) | Buckets, or a cap on the calls counted per hour |
| 5 | Very few calls in an hour | going from 1 to 2 calls is already a doubling | Ignore doublings below about 4 calls (open) |
| 6 | A call with no asset (search, list) | Asset and Tool on asset do not apply and count as ordinary; the other four still apply | — |
| 7 | An asset that is not in the policy | the static score takes the worst case; the dynamic score tracks the inferred name like any asset | — |
| 8 | A server with one asset or few tools (one table, one calendar) | Asset and Tool carry little information; Cadence still works | — |
| 9 | An always-on agent | Time of day is never unusual | The other dimensions still apply |
| 10 | An agent that often explores | a new asset is ordinary for it | Sensitivity still counts, through the static score |
| 11 | Ties (many past calls equally unusual) | they count as "at least as unusual", which lowers M | Conservative by design |
| 12 | The server ships a new tool | every agent's first use is "never seen", so many calls hit ×5 at once | A cross-agent discount (future) |
| 13 | A deep habit on a dangerous tool | M = 0.87 lowers the risk | Gate with max(1, M) (open) |
| 14 | One id for a whole organisation | weak misuse is diluted in the totals, but strong misuse still shows | — |

## 4. Candidate formulas compared

We compared the candidates on 20 general scenarios and 7 kinds of synthetic agent:
- five shaped like GitHub, Slack, Calendar, SQLite and Filesystem agents, using their real tool
  names;
- one always-on agent and one with very uneven volume.

That is 132 checks per seed, with expectations fixed before running. The table shows the mean and
the 95% Student-t interval over **10 development seeds (101-110)**. These seeds are now burnt and
will never produce paper numbers.

| | Formula | Ordinary days stay quiet (53) | One unusual thing caught (51) | Several at once reach ×5 (14) | Total (132) |
|---|---|---|---|---|---|
| A | The deck's dimension slides (v4 scores, strangest wins) | 42.0 ± 1.3 | 31.9 ± 1.1 | 0 | 87.9 ± 1.9 |
| B | The deck's model, Baseline / Likelihood, counted on calls | 15.3 ± 1.0 | 43.8 ± 0.7 | 14 | 86.9 ± 1.1 |
| C | Product of the ratios (as in risk-based login checks) | 10.0 ± 0.0 | 34.0 ± 1.0 | 14 | 71.8 ± 0.9 |
| D | Rank on calls | 20.9 ± 1.2 | 43.5 ± 0.6 | 14 | 92.2 ± 1.8 |
| E | Rank on days | 47.9 ± 1.2 | 46.6 ± 1.0 | 14 | 122.4 ± 1.6 |
| F | Rank on days, Tool on asset per asset | 49.8 ± 0.8 | 50.5 ± 0.9 | 14 | 128.1 ± 1.3 |
| G | Strangest dimension (each dimension's own M; the highest wins) | 40.2 ± 1.5 | 50.8 ± 0.5 | 14 | 118.8 ± 1.6 |
| H | Total surprise (add up the dimensions' surprise, then rank) | 52.1 ± 0.2 | 34.1 ± 1.2 | 12.8 ± 0.7 | 112.9 ± 1.3 |
| I | Rank on calls, Tool on asset per asset | 22.2 ± 1.3 | 43.6 ± 0.5 | 14 | 93.6 ± 1.6 |
| **J** | **I with the settled design rules (§5b): the current choice** | **21.9 ± 1.3** | **43.6 ± 0.5** | **14** | **93.3 ± 1.7** |
| K | F with the same rules: the planned improvement | 49.8 ± 0.8 | 50.5 ± 0.9 | 14 | 128.1 ± 1.3 |

**What matters, in order:**
1. **Count days, not calls** (D → E: +30; J → K: +35). With calls, ordinary days look unusual, a
   new tool is still flagged after two weeks, and one huge burst teaches the agent that bursts are
   normal.
2. **How the dimensions are combined sets the balance** between false alarms and detection:
   - **Strangest dimension (G)** catches the most single signals but flags ordinary days. With six
     dimensions, something is a little unusual on most days.
   - **Total surprise (H)** is the quietest but misses single signals, because one unusual dimension
     is diluted by five ordinary ones.
   - **The rarest-dimension rank (F, K)** keeps ordinary days quiet, catches single signals and
     reaches ×5 when several things are unusual.
3. **Tool on asset per asset** (E → F: +6). It turns "a familiar asset with a new action" from about
   ×1.5 into ×5.
4. **The deck's exp(Baseline − Likelihood)** can only move between ×0.37 and ×2.7, and stays near ×1
   on real data. Whatever is chosen, it must become a ratio.

## 5. Design checks for the current choice (J, counting calls)

| Scenario group | Result (10 seeds) |
|---|---|
| Stay quiet | 21.9 ± 1.3 of 53. Ordinary days have a median of about ×1.35-1.87, a new tool used daily for 2 weeks scores ×2.3-2.6, and an explorer's new resource ×2.6-3.4 |
| One unusual thing | 43.6 ± 0.5 of 51. Single signals reach ×2.5-5, except a burst after one huge burst day (×1.2: the burst taught the habit) and the very uneven agent |
| Several at once | 14 of 14 at ×5 |
| Expected to get through | as expected, except the low-volume agent. Three extra calls doubled its busiest hour, which is a real record for it |

Counting days (K) fixes most of the quiet misses: 49.8 ± 0.8 of 53, with ordinary days at about
×0.9-1.05.

**The reason shown with each score** (seed 101, the GitHub-shaped agent):

| Call | M | Reason shown |
|---|---|---|
| a routine read | ×0.96 | Tool on asset: as unusual in 23% of past calls |
| a write on a repository it only reads | ×3.41 | Tool on asset: as unusual in 0.09% of past calls |
| a tool it never used | ×5.00 | Tool: as unusual in 0.01% of past calls |
| a read at 3 am | ×5.00 | Time of day: as unusual in 0.01% of past calls |
| 30 calls in one hour | ×5.00 | Calls this hour: as unusual in 0.01% of past calls |

## 5b. Design rules settled (the reviewers' minor points)

| Point | Rule | Why | Checked |
|---|---|---|---|
| **What enters the history** | Only calls that ran. A call the gateway denied, or that failed, is scored but never learned. A retried call (the same logical call, such as an MCP input-required retry) counts once. | Otherwise an attacker builds history by probing: 20 denied attempts would make the real call look familiar. | Probe then strike: the real call scores ×5 after 20 denied probes; if the probes were learned, it would score ×0.7-2.1. |
| **Time of day** | Hours are read in the route's own time zone (set by the operator). A past call counts if it was within one hour of this time, so 22:00 is not new for an agent that works until 21:00. There is no weekday or weekend split. | It matches the deck's rule, "calls within 1 hour of this time". The author decided that "day" is not part of the context; weekly rhythm is a stated limit. | Little measurable change on the synthetic agents; kept so the definition matches the deck. |
| **Very small amounts** | Amounts of 1-3 share one bin, so a third call in an hour is not a record. | Going from 1 to 2 calls would otherwise count as a doubling. | Little measurable change. The low-volume agent's remaining miss is a real doubling (8 → 11 calls in an hour). |
| **The discount below ×1** | M below 1 reorders the daily review list only. **For blocking, the gateway uses max(1, M).** | UEBA down-weights what an entity does all the time (GuardDuty "expected behavior", Exabeam's anomaly factor, Sentinel's anomaly score), so habit should rank below novelty. But habit must never lower a block decision, or mimicry earns a discount. | — |
| **Explainability** | Every score comes with its reason: the most unusual dimension and the share of past calls that were as unusual (table above). | Analysts and reviewers need to see why M is high. UEBA products show the triggering insight. | Shown above. |
| **Statistics** | Mean and 95% Student-t interval over 10 seeds. Development seeds (101-110, 202, 303, and the simulator's 1, 2, 7, 11, 12, 21, 31, 41) are burnt. Paper seeds are fixed when the evaluation is frozen. | So no number is tuned on the data it is reported on. | §4, §5. |
| **One formula everywhere** | This report is the reference. The earlier notes are marked as superseded or as background, and the deck's slides 28-30 get the replacement text below. | The deck, the report and the paper must show the same formula. | — |

## 6. Limits a reviewer will raise

| Limit | What happens |
|---|---|
| Mimicry | Misuse inside the agent's habit gets M ≤ 1; only the static score sees it. |
| Pacing and habit building | Staying under its own peaks, or repeating a behaviour often first, keeps M low. |
| Fresh ids | A new id starts at ×1 and ramps slowly. |
| Weekly cycles and drift | They weaken the exchangeability the guarantee rests on, and must be measured. |
| A coarse top | At n = 90 the top values are ×5, ×3.38, ×2.82. |
| Dilution | Each added dimension lowers the score of a single unusual thing a little. |
| Partial days | Today's peaks are known only up to the current call. |
| Counting calls | Busy hours weigh more than quiet ones; ordinary days look mildly unusual; one burst can poison the habit (§3). |

## Defending the claims

### "Isn't this just UEBA on MCP logs?"

It uses UEBA's signals on purpose (§2), because they are what reviewers and operators already
trust. What is new is everything around them that an MCP gateway needs and that UEBA products do
not provide:

| # | Claim | What UEBA does instead | What we must show |
|---|---|---|---|
| 1 | **Scored before the call runs**, per call, at the protocol boundary | Exabeam sums rule points per session, Splunk per 24 hours, and Sentinel ranks events for an analyst afterwards | latency per call, and that only pre-execution information is used |
| 2 | **One risk from two layers**: a policy-derived static score (tool impact, asset sensitivity, blast radius, parameter risk) scaled by behaviour with a fixed span (×5 = the static scale) | Exabeam multiplies a rule's anchor score by an anomaly factor, but its anchors are expert-set per rule, not a model of tool, asset and scope | that the combination ranks risky calls better than either layer alone |
| 3 | **Assets resolved from free-form tool arguments** against the organisation's policy register, deterministically, with no per-server code, and shared by both layers | UEBA consumes logs whose resources are already structured (hosts, files, mailboxes) | resolution accuracy across servers (the binding experiments) |
| 4 | **Identity-minimal**: only an operator-issued agent id | Sentinel, Splunk UBA and Exabeam build peer groups from directory or HR data | that it works without peers |
| 5 | **Label-free and calibrated**: one formula for all six dimensions, with graded rarity instead of expert points, and a stated per-call false-alarm bound | yes/no insights with expert risk points and thresholds | the false-alarm rate on ordinary traffic (real data, in the pipeline) |
| 6 | **Agent-specific signals**: Tool on asset (a new action on a familiar resource, the signature of a hijacked agent that keeps its targets but changes what it does), and Breadth over tool-and-asset pairs | per-attribute novelty; action-on-resource only as a GuardDuty factor | detection of injected-agent misuse (real data, in the pipeline) |

**Claims we do not make:**
- that per-entity rarity is new;
- that rank-based p-values are new;
- that M stops an adaptive attacker who mimics the agent (§6).

### Why this formula

| Part | Justification |
|---|---|
| Risk = static × behaviour | Risk is a function of impact and likelihood (NIST SP 800-30). The static score carries impact, and M adjusts how likely this call is to be misuse given the agent's own past. |
| k / n, the agent's own empirical rarity | UEBA's "first time / uncommon for this user" (Sentinel, Exabeam, Elastic), as a number. |
| (½ / share) | The likelihood ratio of risk-based authentication (Freeman et al., NDSS 2016), with the agent's own typical call as the reference. |
| ½ | Mid-p (Lancaster 1961): no division by zero, a new agent gets ×1, and a typical behaviour gets exactly ×1. |
| The power γ and the top of 5 | Every halving of rarity is the same step, and "never seen" equals the span of the static scale. |
| 1,000-call warm-up | UEBA warm-ups: Exabeam's convergence, Entra's 5 days, Elastic's 20 buckets. |
| Doublings | UEBA compares counts per time bucket against the user's own history. Doublings make that scale-free across servers. |
| Most unusual dimension first | It keeps six dimensions from inflating ordinary calls (§4, G against F). Unlike a maximum, it stays calibrated. |

### Questions a reviewer will ask

- **"Why not a learned model (autoencoder, isolation forest)?"** There are no labels, histories are
  per agent, and every score needs a reason and a fixed scale tied to the static score. Learned
  detectors will be baselines in the evaluation.
- **"Why calls and not days?"** Calls are the unit the gateway decides on. Our own comparison
  shows that days are better (§4: +35 checks), so the paper should report both and keep days as the
  improvement.
- **"An attacker can mimic the agent."** Yes. M targets out-of-character behaviour, such as a
  hijacked or confused agent. Mimicry is left to the static score and is stated as a limit.
- **"Why 5, 1,000 and 90 days?"** See the table above. The evaluation will sweep them.

## Replacement text for the deck (slides 28-30)

| Slide | Replace | With |
|---|---|---|
| 28 Formal Dynamic Model | Risk_dynamic = e^(Baseline(f,v) − Likelihood(f,v)) | Risk(c) = Risk_static(t, a) × M(c), with M(c) = ((n + 1)/(2k + 1))^γ. "How many of this agent's past calls were at least this unusual?" |
| 29 Likelihood | Likelihood(f,v) = N(f,v) / (N_total + K(f)) | share(c) = (k + ½)/(n + 1): the share of the agent's past calls at least as unusual as this one, with this call counted as half. Rarer is more unusual: values used less often, amounts in a higher doubling. |
| 30 The Neutral value | N_neutral = Baseline·(H + K)/(1 − Baseline) | Neutral: share = ½ gives M = 1. Never seen gives M = 5 (once the agent has 1,000 calls); every call gives about ×0.87. Each halving of the share is the same step up. |

## 7. LaTeX draft for the paper

This is in the style of the static section, with the current choice of counting calls. It uses n
and k instead of A and D, so it does not clash with the static weight w_A.

```latex
\subsection{Dynamic Risk Assessment}
\label{sec:dynamic}

The static score captures how much damage a tool can do to an asset, but not whether the agent
issuing a call is acting like itself. The \textit{Dynamic Scanner} adds this context. It scores
each call against the issuing agent's own history and turns the result into a behaviour
multiplier $M(c)$ that scales the static score:
\begin{equation}
Risk(c) = Risk_{\mathrm{static}}(t_i, a_j) \times M(c), \qquad M(c) \in [0.78, 5].
\label{eq:dynamic-risk}
\end{equation}
An ordinary call keeps its static score ($M = 1$); a call unlike anything in the agent's recent
history raises it up to five-fold. Only information available before the call executes is used:
the agent identifier, the invocation time, the invoked tool, and the asset the call names,
resolved against the same asset register as the static score. Argument values are priced by the
static parameter risk (\S\ref{sec:static}), and the outcome of a call never changes its own score.

\subsubsection{Dimensions}
Each dimension compares the call with the same agent's own past calls. We group them
into what the agent touches (\emph{Typical Footprint}) and how much and when it acts
(\emph{Typical Cadence}), as summarised in Table~\ref{tab:dynamic_dimensions}.

\begin{table}[t]
\centering
\caption{Dynamic dimensions. Each is compared with the agent's own past calls.}
\label{tab:dynamic_dimensions}
\small
\renewcommand{\arraystretch}{1.08}
\begin{tabular}{@{}p{0.2\columnwidth} p{0.3\columnwidth} p{0.42\columnwidth}@{}}
\toprule
\textbf{Dimension} & \textbf{Unusual when} & \textbf{Why it matters} \\
\midrule
\multicolumn{3}{@{}l}{\textit{Typical Footprint: what the agent touches}} \\
Tool & a tool the agent rarely uses & an unusual capability is being exercised \\
Asset & an asset it rarely touches & scope creep and data hunting start here \\
Tool on asset & a tool rarely used on this asset & a new action on a familiar resource \\
\midrule
\multicolumn{3}{@{}l}{\textit{Typical Cadence: how much and when}} \\
Calls this hour & more calls than its usual peaks & loops, scraping, mass edits \\
Breadth & more distinct tool--asset pairs per hour & enumeration and sweeps \\
Time of day & an hour it rarely works & activity no one is watching \\
\bottomrule
\end{tabular}
\end{table}

Each dimension mirrors a signal of user and entity behaviour analytics (UEBA): first-time and
uncommon actions and resources, uncommon activity volume, and unusual time of activity are each
scored per entity against its own baseline in commercial UEBA \cite{sentinel_ueba,exabeam_models}
and in risk-based authentication \cite{freeman2016whoareyou}. Unlike those systems, we replace
yes/no insights and expert-assigned risk points with each agent's own empirical rarity, so no
labels or tuned weights are needed. Amounts are compared in doublings, so a slightly busier hour is
not a record while twice the usual peak is. For Tool on asset we use the share of the agent's past calls on this asset that used this tool,
so a first combination on a rarely used asset carries little evidence.

\subsubsection{Behaviour multiplier}
For each call we ask a single question: \emph{how many of this agent's past calls were at least
this unusual?} For each dimension, a past call counts if its value on that dimension was at least
as rare (or its amount at least as high). For the call as a whole, we compare its most unusual
dimension with each past call's most unusual dimension, breaking ties by the next one, and let
$k(c)$ be the number of past calls that were at least as unusual. With $n$ the agent's past calls,
\begin{equation}
M(c) = \left( \frac{n + 1}{2\,k(c) + 1} \right)^{\gamma}, \qquad
\gamma = \frac{\ln 5}{\ln (\max(n, n_0) + 1)},
\label{eq:behaviour-multiplier}
\end{equation}
with $n_0 = 1000$. A behaviour seen in half of the agent's calls gives $M = 1$; each halving of
$k$ raises $M$ by the same factor; a behaviour never seen in the agent's history gives $M = 5$,
the span of the static scale, so behaviour alone can move a call across the whole static range
but no further. Below $n_0$ past calls, $M$ ramps up with the history instead of jumping to the
top. Because $(k + 1)/(n + 1)$ is a conformal p-value of the call \cite{bates2023conformal},
a given call of an agent whose calls are exchangeable reaches $M = 5$ with probability at most
$1/(n + 1)$, regardless of the number of dimensions. Only calls that executed enter an agent's history: denied or failed
calls are scored but never learned, so probing cannot make a later call look familiar, and a
retried call counts once. Every score is reported with its reason, the most unusual dimension and
the share of past calls that were as unusual. When the score is used to block, $M$ is floored at 1,
so habit can reorder the review list but never lowers a block decision.
```

## References

- NIST. *Guide for Conducting Risk Assessments*. SP 800-30 Rev. 1, 2012.

- S. Bates, E. Candès, L. Lei, Y. Romano, M. Sesia. Testing for outliers with conformal p-values.
  *Annals of Statistics* 51(1):149-178, 2023.
- H. S. Javitz, A. Valdes. The NIDES statistical component: description and justification. SRI
  International, 1994.
- H. O. Lancaster. Significance tests in discrete distributions. *JASA* 56(294):223-234, 1961.
- D. C. Le, N. Zincir-Heywood, M. I. Heywood. Analyzing data granularity levels for insider threat
  detection using machine learning. *IEEE TNSM* 17(1), 2020.
- T.-F. Yen et al. Beehive: large-scale log analysis for detecting suspicious activity in
  enterprise networks. ACSAC 2013.
- Comparison details and the other sources: [behaviour-formula-candidates.md](behaviour-formula-candidates.md).
