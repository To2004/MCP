# Dynamic Layer v2 — The Calculation

How one call's score is computed under the current design, factor by factor, with a
worked example carried through. Specification only: no results, no evaluation.

This supersedes [Dynamic Layer — The Calculation](dynamic-layer-formula.md) for the
implemented runtime (`scripts/dynamic_design/dynamic_v2.py`). That document is kept
as-is; it records the three-factor design and the reasoning behind it. What changed and
why is in [the last section](#what-changed-from-v1-and-why).

## The formula

```
R(c) = min( score_max , cell(tool, asset) × D(c) )
```

Two ingredients. That is the whole runtime.

| factor | the question it answers | range | who decides it |
|---|---|---|---|
| `cell(tool, asset)` | how bad would this be, if it went wrong? | 1 … 125 | the scan, at design time |
| `D(c)` | how broad is this call for this organization? | 0.80 … 1.30 | this call's arguments, against observed history |

The shape matters: **only the cell can make a score large.** `D` nudges it by at most
±30%, so nothing in the runtime can invent risk the scan did not already price, and
nothing can discount a call by more than a fifth.

## 1 · `cell` — the base

A table lookup. The scan has already computed, for every (tool, resource) pairing the
server exposes:

```
cell = asset_sensitivity × blast_radius × tool_impact        1 … 125
```

The runtime never recomputes this. It reads the number and moves on. Bands (`low 0–16`,
`medium 17–49`, `high 50–99`, `critical 100–125`) are a **label over the number, not a
decision** — they exist so a human can skim, and nothing in the arithmetic depends on
them.

## 2 · `D` — is this call unusually broad here?

**The idea.** The same tool is a pinprick or a demolition depending on how much it
covers. Fifty calendars is not the same request as one, even though both are
`list-events`. But what counts as "a lot" is a property of the deployment, not of the
tool, so the deployment's own history sets the cut points.

```
D = 0.80   at or below the quarter-point of what this organization asks for
D → 1.30   climbing continuously toward the outlier fence
D = 1.00   nothing could be judged — no quantity argument, or no history yet
```

**D is continuous, not three bins.** That matters more than it sounds. With a single
threshold, every call on the ordinary side scores identically: `limit=1`, `limit=10`,
`limit=50` and `limit=100` all collapse to one number and cannot be ordered. Measured on
real traffic, a three-bin D produced **3 distinct scores across 1500 calls**; the ramp
produces **58**, and small routine calls still sit on the floor:

```
get-freebusy.calendars   1->0.80  5->0.80  10->0.93  13->1.00  17->1.10
list_commits.perPage     1->0.80  25->0.88  50->1.00  75->1.12  100->1.25
channels_list.limit      1->0.80  50->0.89  100->1.00  999->1.30
```

One call, one D. If several quantities are present the **widest wins**: a request that is
ordinary in one dimension and enormous in another is a wide request.

### 2a · Finding the quantity

Not every argument carries breadth. The **breadth spec** classifies each of a tool's
inputs once, at scan time, and ships inside the scan artifact as `tool_breadth` alongside
`tool_atomic_ops` and `tool_input_ranking` (`src/mcp_security/scanner/breadth.py`).

Each input carries five fields. Three are answers, two are facts:

| field | meaning |
|---|---|
| `kind` | `count` (a collection; its length is the quantity), `magnitude` (a number whose value is the quantity), `range` (one endpoint of an interval; the *span* is the quantity), or `none` (names or selects one thing, switches a mode, or is content being written) |
| `targets` | does this value decide *which* stored thing the call acts on, rather than how much of it? |
| `rank` | the model's ordering of this tool's inputs by how much of the system the call can be made to touch, most first |
| `default` | the value the server applies when the caller omits the argument — declared in the schema, so fact rather than inference |
| `ceiling` | `maxItems`/`maximum`, likewise declared |

**The label decides only whether to look. The value's own shape decides how to read it.**
Lists and objects give their length, numbers give their value, numeric strings parse with
unit suffixes (`30d` → 30), and a bare value where a collection was expected counts as
one. This split is deliberate: the two passes disagree about whether a paged `perPage` is
a count or a magnitude, and a parser that trusted the label once discarded every quantity
on an entire server over that purely taxonomic dispute.

**Spans need the pair.** A `timeMin` alone says nothing; `timeMin` with `timeMax` says how
much calendar the call sweeps. One extra quantity, `<span:days>`, is derived per call from
the widest pair of `range` endpoints.

#### Two passes, and why neither is asked the other's question

**Structure** is what the JSON Schema states outright — an `enum` is a fixed choice, an
`array`'s length is its breadth, `maxItems`/`maximum` are ceilings, `default` is what
applies on omission. It reads **no parameter name**. Name rules are guesses at semantics,
and each one fixed after seeing a misclassification is a guess fitted to the servers under
test: substring matching had made `timeMax` a magnitude (it contains "max"), `calendarId`
a range ("calendar" contains "end") and `account` a count.

**Semantics** is everything structure leaves open, handed to the local model. Measured
over five servers it settled **270 of 270** structurally-ambiguous inputs, including on
two never used for tuning.

That makes the model pass a **required scan step, not an optional enrichment**. Slack
declares every one of its 63 inputs as a plain string, so structure alone resolves none of
them; without the model's answers that server has no quantities and every call scores
1.00.

**An input nobody classified reads `kind: "none"`** — not a quantity — because that is
what the runtime must do with it anyway, and most inputs genuinely are not quantities. The
gap moves to `source`, which is `unclassified` rather than `schema` or `llm`. Counting
those is how you tell a finished scan from one whose model died halfway; the scan exits
non-zero when any remain.

#### The prompt

Asked once per tool, for the inputs structure could not settle. No parameter name from any
scanned server appears in it — concrete examples are the main channel through which a
prompt memorises the set it will be measured on.

```text
You are analysing the input parameters of one API tool.

Answer three questions about each parameter. Judge what the parameter MEANS, not how it is declared — a declared type is often wider or narrower than what the value carries.

(1) "kind" — if a caller supplied a LARGER value, how is "larger" expressed?

    count      the value is a collection, and what matters is how many items it holds (including a collection encoded inside one string with a separator)
    magnitude  the value is a single number, and a bigger number means more work done or more data returned (including a number written as text, with or without a unit suffix)
    range      the value is one endpoint of an interval, and the SIZE of the interval between it and its partner parameter is what matters
    none       the value names or selects one particular thing, switches a mode on or off, or is free-form content being written

    A value that identifies something is "none" even when it is numeric: one identifier is not larger than another.

(2) "targets" — true if the value decides WHICH stored thing the call reads or changes: it names, selects, or filters the container, record or path acted on. False if it only shapes the request — how many results, how they are ordered, what format they come back in, or content being written. A parameter can be both: one that names a set of containers targets, and its length is also a count.

(3) the ORDER of your reply — rank the parameters by HOW MUCH OF THE SYSTEM this call can be made to touch by changing that one parameter, largest first.

    A call touches more of the system in two ways, and BOTH count:
      - more distinct stored things are reached — more containers, records or paths
      - more is returned or changed within each thing that is reached

    A parameter that raises the NUMBER of things reached therefore ranks above one that only raises how much comes back from a single thing, and both rank above a parameter that changes neither.
    A parameter that names exactly one thing does not widen the call, however important that thing is: importance is not breadth.
    A parameter that narrows or filters results does not widen the call either.
    If two parameters would widen the call equally, put the one whose values can grow larger first.

Tool: <tool name>
Description: <tool description>

Parameters:
<one line per parameter: name, declared type, description>

Reply with ONLY a JSON object. Include every parameter listed above exactly once, using its name exactly as written, ordered by question (3):
{"inputs": [{"name": <parameter name>, "kind": "none|count|magnitude|range", "targets": true|false, "why": "<one short clause>"}]}
```

Three things about its construction are deliberate.

**It defines the ranking criterion operationally rather than gesturing at it.** An earlier
wording — *"what this call reaches or does"* — was read as selectivity, so a listing tool's
page size ranked below its filter. The annotation literature is consistent that a prompt
needs concept *definitions* and explicit edge cases, written as one would write them for a
human annotator, not a single clause.

**It states that a call widens in two ways**, because only one of them is obvious: more can
come back from a single thing, *and* more distinct things can be reached. A page size on a
listing tool multiplies the containers reached, not the rows within one.

**It asks for an order, not scores.** Requesting a 1–5 per input would be pointwise
ranking, which the LLM-ranking literature finds least reliable — scores produced in
isolation need heavy calibration, whereas one ordered list judges the candidates against
each other. The position in the reply *is* the rank; no score is requested and none is
accepted.

#### Known limits of the ranking

Two, both measured rather than assumed.

**Position bias is architectural** in autoregressive models, so the order inputs are
presented in leaks into the ordering that comes back. Inputs are always presented in one
deterministic order, which makes the ranking reproducible but not unbiased. Repetition over
shuffled presentations is the published mitigation and costs a model call per repeat;
`scripts/check_rank_stability.py` measures the size of the bias so that cost can be
decided rather than guessed.

**The ordering does not always put the volume argument first.** On a channel-listing tool
the model still ranks the argument naming *which kinds* of channel above the one bounding
*how many*, even under the volume-worded criterion. Labels also moved between runs on the
same input. This is why `rank` is **not** used to weight `D` by default — see
[Blind Spots](dynamic-layer-blind-spots.md).

### 2b · Deciding how broad it is

**The reference is built at runtime, from this deployment's own traffic. Nothing at
design time supplies a number.** That division is the core of the design: the schema and
the model are asked only *which argument is a quantity*, because "how big is too big"
depends on the organization — twenty attendees is everyone at a ten-person company and a
small meeting at a large one. A model cannot know which one you are, and when asked it
correctly declines: a stated threshold was present on only 10–14% of inputs.

Once an argument has `MIN_HISTORY` observations:

```
Q1, Q3 = the 25th and 75th percentile of values seen for this (server, tool, argument)
upper  = Q3 + 1.5 × (Q3 − Q1)                     Tukey's outlier fence

D = 0.80 + 0.50 × clamp( (value − Q1) / (upper − Q1), 0, 1 )
```

So a value at or below Q1 takes the full discount, one at the fence takes the full
escalation, and everything between is ordered. **Quartiles rather than one cut-point** is
what makes that ordering possible; quartiles rather than mean and standard deviation
because they are rank-based, so one enormous call cannot drag the reference it is being
judged against.

**A flat sample takes the floor.** If every observed value is identical, `Q1 = upper` and
there is nothing to grade against, so the call is treated as routine rather than as an
outlier-by-construction.

**Too little history → 1.0.** Not a guess in either direction. This is the honest cold
start: the layer has no opinion about an argument it has never seen.

## 3 · What `D` deliberately does not do

Worth stating, because each is a question people will ask.

- **It does not resolve identifiers.** An unknown event id is not riskier than a known
  one; treating novelty as risk would alert on every first-time access. A wrong id and a
  right id score identically, by design.
- **It does not read response status.** The reference answers *what breadth does this
  organization ask for*, not *what succeeded*. Measured on real traffic, failures were
  quotas, empty result sets, and bad test ids — never the organization declining to work
  that way — so filtering on status only discarded ordinary observations.
- **It has no memory across calls.** No rate, no burst, no session. A call scored twice
  scores the same both times. The consequence: a hundred small calls look like a hundred
  small calls. The threat model is a legitimate agent doing too much in one request, not
  an adversary spreading work to stay under a threshold.
- **It never blocks.** The output is a number and a label. Nothing is denied.
- **It does not weight quantities by `rank`.** The scan's ordering answers "how much of
  the system could this parameter reach", which is close to what `D` measures but not the
  same, and weighting by it suppressed genuinely wide calls: a request for the largest
  page a listing API allows fell from 1.30 to 0.88 under a top-heavy curve, because the
  page size ranked third. Rank weighting exists behind a flag and is off.
- **It does not use `targets`.** An argument that selects *which* asset is a reach signal,
  and reach is the cell's job; folding it into a volume factor would double-count.

## Worked example

A scheduling agent at **aurora** calls `list-events` over seven calendars for a
fourteen-day window. The organization has previously called it with one to three
calendars.

**Step 1 — the cell.**

```
cell(list-events, calendar-records) = 60          → high band (50–99)
```

**Step 2 — the quantities.**

```
calendarId   is a `count`, value is a list of 7        → 7
timeMin/timeMax are `range`  → <span:days>            → 14
```

**Step 3 — how broad, per quantity.**

```
calendarId history (46 observations): Q1 = 1, Q3 = 3
             upper = 3 + 1.5 × (3 − 1) = 6
             D = 0.80 + 0.50 × (7 − 1)/(6 − 1) = 0.80 + 0.50 × 1.0   → 1.30  (clamped)

<span:days> history (46 observations): Q1 = 7, Q3 = 30
             upper = 30 + 1.5 × 23 = 64.5
             D = 0.80 + 0.50 × (14 − 7)/(64.5 − 7) = 0.80 + 0.06     → 0.86
```

**Step 4 — combine, and score.**

```
the widest wins                                        → D = 1.30

R = min(125, 60 × 1.30) = 78.0                         → high
```

Reported as **78, high**, with the reason `calendarId=7->1.30(observed)`. The band did
not change; the call simply sorts above the ordinary `list-events` calls around it, which
is the entire job.

Had the same call used three calendars instead of seven, `D` would be
`0.80 + 0.50 × 2/5 = 1.00` and `R = 60` — and with one calendar, `D = 0.80` and `R = 48`.
Three requests to the same tool, three different scores, ordered by how much they cover.

## Constants

| constant | value | why |
|---|---|---|
| `score_max` | 125 | 5 × 5 × 5, the ceiling of the static formula |
| band labels | 17 / 50 / 100 | from the scan's `band_thresholds`; presentation only |
| `D` range | 0.80 … 1.30 | bounded both ways; ±30% is the most the runtime may move a score |
| ramp floor / top | Q1 / upper fence | the discount is full at the quarter-point, the escalation full at the outlier fence |
| Tukey multiplier | 1.5 | ~0.7% of well-behaved values fall outside |
| `MIN_HISTORY` | 20 | below this there are no meaningful quartiles |
| `MAX_HISTORY` | 4000 | rolling window of the most recent values; eviction is by **arrival order**, never from the sorted list — dropping the smallest value each time walks Q1 and Q3 upward until the window holds one value and everything scores the floor |
| `RANK_DECAY` | 0.5 | how much less a lower-ranked quantity would count, **if** rank weighting were enabled. It is not. |

## Order of operations

```
1. resolve the call to a (tool, resource) cell             → base score
2. find this tool's quantity arguments from tool_breadth
3. for each: read the value; if omitted, substitute the declared default;
   if omitted with no default, impute Q3; if present but unreadable, impute Q3
4. add the derived <span:days> if range endpoints pair up, or impute it
   when the tool takes a window and the caller gave none
5. ramp each quantity from Q1 to the upper fence  → ramp in [0, 1]
6. combine by noisy-OR: 1 - Π(1 - ramp)           → D in [0.80, 1.30]
7. multiply by the cell, clamp above by score_max
8. report the score, its band, and the per-quantity reasons. Nothing is blocked.
```

Step 6 is a noisy-OR rather than a maximum because breadth composes multiplicatively:
fifty calendars over a year covers fifty times more than one calendar over a year, so a
call wide in two dimensions is wider than one wide in a single dimension, which a maximum
cannot express. Noisy-OR stays bounded, stays monotone, and still saturates on any single
argument that reaches its fence. Measured on real traffic, 694 of 1026 scored calls carry
more than one judgeable quantity, so this is the common case rather than an edge one.

Step 3 matters more than it looks. An omitted argument is not absent data — the call still
happened and something was still in force. Where the schema declares a default, that value
applied, so substituting it is fact. Where it declares none, the caller bounded nothing,
and the honest reading is at least the usual upper end. Imputed values are **scored but
never remembered**, or the reference would learn from its own assumptions; applied defaults
*are* remembered, since a call that omits a limit really did request the default.

Cost is a few dict lookups and one sorted insert per quantity — measured at roughly
20 microseconds per call, no model and no network.

## What changed from v1, and why

| v1 | v2 | reason |
|---|---|---|
| `cell × likelihood × escalation` | `cell × D` | `likelihood` was keyed on `(company, tool)`, so it was **constant across every call to one tool by one company** and could not order calls within a tool at all. It also measured net-negative on all three servers. |
| `likelihood ∈ [0.10, 1.00]` | discount capped at 0.8 | a 90% discount is a far stronger claim than the evidence supports; ±30% matches the bounded-modifier precedent |
| band floor protecting the discount | no floor | with a maximum 20% discount there is little to protect, and the band is a label rather than a decision. Fewer interacting parts. |
| escalation from magnitude args only | every argument the breadth spec marks as a quantity | escalation never fired once, partly because its input was `critical_trigger`, present on only 10–14% of inputs |
| three bins `0.9 / 1.0 / 1.3` | a continuous ramp over `[0.80, 1.30]` | three bins produced **3 distinct scores across 1500 real calls**: `limit=1`, `10`, `50` and `100` were indistinguishable. A cut-point says *whether* a call crossed a line; it cannot order the calls on either side, and ordering is the whole output |
| widest quantity wins | noisy-OR over all quantities | breadth composes multiplicatively; a maximum cannot express "wide in two dimensions at once" |
| omitted argument ignored | default substituted, else Q3 imputed | an unbounded request scored *lower* than a large bounded one — the widest possible call read as silence |
| thresholds from `critical_trigger` | thresholds from observed history, ceiling for cold start | "at what value is this critical" depends on the organization; the model correctly declines to answer it, so ask it only for the *type* and take the cut-point from the data |
