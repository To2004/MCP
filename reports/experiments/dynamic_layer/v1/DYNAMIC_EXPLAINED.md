# The Dynamic Layer, Explained in Full

Every decision in the runtime layer, why it is that way, and what it was measured against.
Companion to [README.md](README.md), which walks the same pipeline end to end with real
numbers; this one explains the *reasoning*.

Implementation: `scripts/dynamic_design/dynamic_v2.py` (runtime) and
`src/mcp_security/scanner/breadth.py` (scan). Tests: `tests/test_dynamic_v2.py`,
`tests/scanner/test_breadth.py`.

## 1 · What the layer is for

The static scan prices a `(tool, asset)` pairing: *how bad would this be if it went
wrong*. It cannot see the call. Two requests to the same tool on the same asset get the
same number whether one reads a week of one calendar and the other reads a year of
seventeen.

The dynamic layer answers the other half: **how much of the system does this particular
call cover, compared to what this organization normally asks for**. It never blocks. Its
output is a number used to order a review queue.

```
R(c) = min( score_max , cell(tool, asset) × D(c) )
```

## 2 · Why the scale is what it is

`score_max = 125` is **not a choice**. The static score is
`asset_sensitivity × blast_radius × tool_impact`, each on the 1–5 ladder, so the product
ranges 1…125. The cap exists only so `D` cannot push a call past the top of a scale the
scan already defines. The band cut-points (17 / 50 / 100) partition that same fixed range.

`D ∈ [0.80, 1.30]` **is** a choice, and the only free parameter in the multiplication.
Bounded at ±30% so the runtime can reorder calls without inventing risk the scan did not
price. Two consequences worth stating plainly:

- within one cell, the widest call can outscore the narrowest by at most **1.63×**;
- across tools the cell spans 2…36 in this corpus (×18), so **severity is decided far more
  by which tool is called than by how broad the call is**. That is the intended shape —
  "only the cell can make a score large" — and it is why a very wide benign read never
  reaches `high`.

## 3 · The division of labour

Three parties, each asked only what it can actually know.

| party | answers | never answers |
|---|---|---|
| **the JSON Schema** | is this an enum, an array, a number? what is its declared `default` and `maximum`? | what a string *means* |
| **the local model** (scan time) | is this argument a quantity, and in what unit? does it select which thing is touched? | how big is too big |
| **the deployment's own traffic** (runtime) | what values does this organization actually pass? | anything about semantics |

The middle row is the one that took several attempts to get right. The scan's older
`critical_trigger` field asks the model for a *threshold* — "at what value does this become
critical" — and the model correctly declines on 86–90% of inputs, because the answer
depends on the organization. Twenty attendees is everyone at a ten-person company and a
small meeting at a large one. Asked instead whether an argument *is* a quantity, the model
settled **270 of 270** structurally-ambiguous inputs across five servers, including two
never used for tuning.

### Why no parameter names are read in Python

An earlier version classified by matching parameter names against hand-written token
lists. It was wrong in ways that only showed up when checked:

| parameter | classified as | because |
|---|---|---|
| `timeMax` | magnitude | contains "max" |
| `calendarId` | range | "calendar" contains "end" |
| `account` | magnitude | contains "count" |

Worse than the errors was the process: each was fixed *after* seeing it fail on the servers
being measured, which fits the rules to the test set. The rules were also unnecessary —
the model resolves the same inputs correctly. Structure now reads no names at all, and
there is a test asserting that identical schemas named `timeMax`, `calendarId`, `account`
and `count` all classify identically.

## 4 · Finding the quantity in a call

Each input carries five fields from the scan: `kind`, `targets`, `rank`, `default`,
`ceiling`, plus `source` recording who decided.

**The label decides only whether to look; the value's shape decides how to read it.** Lists
and objects give their length, numbers their value, numeric strings parse with unit
suffixes (`30d` → 30), a bare value where a collection was expected counts as one. This is
not fastidiousness: the two passes disagree about whether a paged `perPage` is a `count` or
a `magnitude`, and a parser that trusted the label once discarded **100% of one server's
quantities** over that purely taxonomic dispute.

**Spans need the pair.** A `timeMin` alone says nothing about breadth; with `timeMax` it
says how much calendar the call sweeps. One derived quantity, `<span:days>`, comes from the
widest pair of `range` endpoints. Before this existed, 1,380+ endpoint instances were
classified correctly and then dropped, because a per-argument parser cannot see a span by
construction.

## 5 · The omission rule

An omitted argument is not missing data. The call happened, and something was in force.
Three cases, decided by what is actually known:

| case | what is done | why |
|---|---|---|
| the schema declares a **default** | substitute it | fact, not inference — that value applied, so the call really did request it |
| **no default**, and this argument has ≥ `MIN_HISTORY` observed uses | impute **Q3** | the caller bounded nothing, and this is an argument the organization does use; the honest reading is the high end of normal |
| **no default**, and nobody ever passes it | **ignore it entirely** | there is no Q3 to impute, and charging every call for an argument this deployment never uses would be inventing a signal |

This closed a real inversion. Before it, an **unbounded** request scored *lower* than a
large bounded one:

```
conversations_history  limit=999    ->  D 1.30
conversations_history  OMITS limit  ->  D 1.00     the widest possible call, read as silence
```

Two safeguards keep it honest. **Imputed values are scored but never remembered** — else
the reference learns from its own assumptions and drifts. **Applied defaults are
remembered**, since a call that omits `limit` genuinely did request the default.

One surprising consequence, deliberate and tested: because Q3 sits above the median,
**omitting an argument costs more than passing a typical value for it**. A caller who
declines to bound anything is treated as asking for the high end of normal, which is
strictly more than most callers ask for.

## 6 · Turning a value into a factor

```
Q1, Q3 = 25th and 75th percentile of the values this deployment passed for this argument
upper  = Q3 + 1.5 × (Q3 − Q1)                     Tukey's outlier fence

ramp   = clamp( (value − Q1) / (upper − Q1), 0, 1 )
D      = 0.80 + 0.50 × ( 1 − Π (1 − ramp) )       noisy-OR across the call's quantities
```

**Quartiles, not a single cut-point.** A threshold can say *whether* a call crossed a line;
it cannot order the calls on either side of it, and ordering is the entire output. Measured
on the same 1,500 real calls, a three-bin `D` produced **3 distinct scores** — `limit=1`,
`10`, `50` and `100` were indistinguishable — where the ramp produces 22–81 per server.

**Rank-based, not mean and standard deviation.** Quartiles cannot be dragged by the very
outliers they exist to find.

**Noisy-OR, not a maximum.** Breadth composes multiplicatively: seventeen calendars over a
year covers seventeen times more than one calendar over a year, and a maximum cannot
express "wide in two dimensions at once". Noisy-OR stays bounded, stays monotone, and still
saturates on any single argument that reaches its fence. On this corpus **694 of 1,026**
scored calls carry more than one judgeable quantity, so it is the common case rather than
an edge one.

**Abstain rather than guess.** Below `MIN_HISTORY = 20` observations there are no
meaningful quartiles, and `D` contributes 1.0.

**A flat sample takes the floor.** If every observed value is identical, `Q1 = Q3` and both
fences collapse onto that point, so *any* other value would read as an outlier. That is an
artefact of the estimator, not evidence about the call. On calendar this guard fired 77
times in 500 calls.

### The rolling window, and a bug worth remembering

History is capped at `MAX_HISTORY = 4000` per argument, evicted **by arrival order**. An
earlier version evicted from the *sorted* list, which deletes the smallest value every
time. On a stationary stream of `{1,5,10,25,50,100}` with a 200-value window:

```
calls     Q1    Q3   smallest kept
  400     25   100      25
  800     50   100      50
 1200    100   100      50
 2000    100   100     100
```

Within ~1,200 calls the window held nothing but the largest value, `Q1 = Q3`, and every
call scored the floor forever — silently, with no error. No published number was affected
(no window ever filled), but it would have failed invisibly in production.

## 7 · What the layer deliberately does not do

Each of these is a stated boundary, not an unfinished feature.

- **It does not resolve identifiers.** An unknown event id is not riskier than a known one;
  treating novelty as risk would alert on every first-time access. A wrong id and a right
  id score identically. This also means **BOLA is out of scope by construction** — detecting
  whether a caller owns an object needs ownership context and multiple identities, which a
  server-side scorer without roles does not have. In OWASP terms this is an
  **API4 (Unrestricted Resource Consumption)** signal, not an API1 (BOLA) control.
- **It does not read response status.** The reference answers *what breadth does this
  organization ask for*, not *what succeeded*. Checked against 543 real failures, every one
  was incidental — a quota, an empty result set, a bad test id — never the organization
  declining to work that way. Filtering on status discarded 543 ordinary observations and
  left the fences worse informed.
- **It has no memory across calls.** No rate, no burst, no session. A call scored twice
  scores the same both times. The cost: a hundred small calls look like a hundred small
  calls, so ID enumeration is invisible. The threat model is a legitimate agent doing too
  much in one request, not an adversary spreading work to evade a threshold.
- **It does not weight quantities by `rank`.** See below.
- **It does not use `targets`.** An argument that selects *which* asset is a reach signal,
  and reach is the cell's job; folding it into a volume factor would double-count.
- **It never blocks.**

## 8 · The ranking, and why it is not in the arithmetic

The scan returns a `rank` per input — the model's ordering of a tool's inputs by how much
of the system the call can be made to touch. Ranking **within one tool is correct**: all of
a tool's inputs compete for the same call, so they are the right comparison set.

It is asked listwise — the position in the reply *is* the rank — because a 1–5 score per
input is pointwise ranking, which the LLM-ranking literature finds least reliable: scores
produced in isolation need heavy calibration, whereas one ordered list judges the
candidates against each other.

It is nonetheless **not used to weight `D`**, for two measured reasons.

**It is not stable.** Asked twice with the inputs presented in opposite order — identical
content, only the presentation reversed:

```
24 tools    mean Kendall tau 0.538    median 0.60    identical orderings 3 / 24
```

Against thresholds fixed before the measurement (≥0.8 usable, 0.4–0.8 explanation only,
<0.4 unusable), that is the middle band. The pattern matters more than the mean:

| inputs per tool | tau |
|---|---|
| 3–5 | 0.33 … 1.00, several perfect |
| 6–8 | 0.40 … 0.79 |
| **20–23** | **−0.37, −0.47** |

Negative tau on the largest tools is the signature of the model echoing back the order it
was given. On a 23-input tool the "ranking" is largely the schema's declaration order, and
weighting a risk score by that would make it depend on how a server author wrote their JSON.

**And weighting suppressed the calls it should raise.** A request for the largest page a
listing API allows fell from **1.30 to 0.88** under a top-heavy curve, because that page
size ranked third among its tool's inputs. Steeper curves made it worse, not better:

| case | equal | linear ×0.5 | steep 1/2ⁱ | top-only |
|---|---:|---:|---:|---:|
| `channels_list` limit=999 | **1.300** | 1.050 | 0.925 | **0.875** |
| `list-events` 17 cals × 365d | **1.300** | 1.194 | 1.194 | 1.121 |

`rank` is therefore kept for **explanation** — which input to look at first — where a wobble
costs nothing. `--rank-weight` enables the weighting for experiment; it is off.

**The known fix, not yet done:** ask for the ranking as a *second pass* over the JSON the
first pass returns. Classification would stop depending on presentation order entirely, the
ranking pass could be repeated over shuffled orders and aggregated (the published
mitigation for position bias), and single-input tools would be skipped rather than handed a
rank of 1 that carries no information. Cost is a second model call per tool.

## 9 · What was measured, and on what

| claim | evidence |
|---|---|
| the classifier generalises | 270 tools / 836 inputs across 10 catalogs, 7 never used for tuning |
| the model resolves what structure cannot | 270 of 270 ambiguous inputs, incl. 2 held-out servers |
| the score orders benign traffic by breadth | 1,500 real calls, 22–81 distinct `D` per server |
| ranking is unstable at scale | Kendall tau 0.538 over 24 tools, forward vs reversed |
| runtime cost is negligible | 24,000–27,000 calls/sec, 37–43 µs per call |

**All corpora are real** — 3,000 read-only calls against live GitHub, Slack and Google
Calendar MCP servers, with breadth values drawn from real account state (12 repositories,
24 channels, 17 calendars) rather than a distribution anyone chose.

## 10 · What none of this establishes

Every call in every corpus is **benign by construction**. Nothing here shows that `D`
separates misuse from ordinary use — only that routine calls sit on the floor, wide calls
climb, and what the false-alarm side costs. The other half needs calls that are broad *and*
wrong, and those have to come from real usage that happens to be wide. A script that picks
large numbers would only rediscover its own generator.

The layer also inherits the static side's open problem: **`cell` requires resolving which
asset a call touches**, and the real corpora carry no resolved asset, so `R` is blank in the
per-call CSVs. `D` is the runtime's whole contribution and is complete.
