# Dynamic Layer v1 — Breadth Scan and Runtime Scoring, End to End

The whole pipeline for three real MCP servers: the prompt that classifies a tool's inputs
at scan time, what it returned, how the runtime turns that into a number, and what it
produced on 1,500 real calls.

Everything here is reproducible from the files in this directory. Date: 2026-08-14.

## The formula

```
R(c) = min( score_max , cell(tool, asset) × D(c) )
```

### Where `score_max = 125` comes from

It is not chosen. The static score is `asset_sensitivity × blast_radius × tool_impact`,
each rated on the framework's 1–5 ladder, so the product ranges 1…125 and `5 × 5 × 5` is
the arithmetic ceiling. `score_max` exists only so `D` cannot push a call past the top of
the scale the scan already defines — a cell of 125 with `D = 1.30` would otherwise read
162.5, a number the static scale has no meaning for.

The same is true of the band cut-points (17 / 50 / 100): they partition that fixed range.
Nothing in the runtime was tuned to produce them.

`D`'s own bounds, `[0.80, 1.30]`, **are** a choice — bounded ±30% so the runtime can
reorder calls without inventing risk the scan did not price. That one is a judgement, and
it is the only free parameter in the multiplication.

## Step 1 · The scan classifies each input

Asked once per tool, for the inputs the JSON Schema could not settle on its own. The full
text is in [`breadth_prompt.txt`](breadth_prompt.txt); the three deliberate choices in it:

- **the ranking criterion is defined operationally**, not gestured at. An earlier wording
  ("what this call reaches or does") was read as *selectivity*, so a listing tool's page
  size ranked below its filter;
- **it states that a call widens in two ways** — more distinct things reached, *and* more
  returned from each — because only the second is obvious;
- **it asks for an order, not scores.** A 1–5 per input is pointwise ranking, which the
  LLM-ranking literature finds least reliable; the position in the reply is the rank.

No parameter name from any scanned server appears in the prompt.

### What came back

| server | tools | inputs | classified | unclassified | model seconds |
|---|---:|---:|---:|---:|---:|
| github | 26 | 130 | 130 | **0** | 112 |
| slack | 16 | 63 | 63 | **0** | 72 |
| calendar | 13 | 110 | 110 | **0** | 85 |

Full output in `<server>_real_scan.json`. Kinds across the three:

| kind | github | slack | calendar |
|---|---:|---:|---:|
| `none` (not a quantity) | 95 | 43 | 62 |
| `count` | 16 | 7 | 34 |
| `magnitude` | 18 | 6 | 6 |
| `range` | 1 | 7 | 8 |

`none` dominating is the expected shape: most inputs name things rather than size them.

## Step 2 · The runtime learns the numbers

The scan never states a threshold. "How big is too big" is a property of the organization,
so the quartiles are built from the values that deployment actually passes. Learned from
the warm-up half of the real corpus:

```
server   tool                    argument         n    Q1     Q3     upper fence   observed range
calendar get-freebusy            calendars        85   5      13     25            1 … 17
calendar get-freebusy            calendarExpansionMax 85  5   20     42.5          1 … 50
calendar get-freebusy            <span:days>      85   7      180    439.5         1 … 365
calendar list-events             calendarId       81   4      13     26.5          1 … 17
calendar list-events             <span:days>      81   7      90     214.5         1 … 365
calendar search-events           calendarId       92   1      1      1             1 … 1
github   list_commits            perPage          60   10     75     172.5         1 … 100
github   list_pull_requests      per_page         61   5      50     117.5         1 … 100
github   search_code             page             51   1      2      3.5           1 … 3
slack    channels_list           limit            68   10     100    235           1 … 999
slack    channels_me             limit            57   1      10     23.5          1 … 100
slack    conversations_history   limit            72   7      90     214.5         1 … 100
slack    users_search            limit            51   5      50     117.5         1 … 100
```

The same argument name gets a different scale per tool and per deployment — `limit` is
ordinary up to 100 on `channels_list` and unusual past 10 on `channels_me`. That is the
whole point of learning it rather than declaring it.

## Step 3 · How one call becomes a number

```
for each quantity argument of the tool:
    value    = the argument, or the schema's declared default if omitted,
               or Q3 if omitted with no default, or Q3 if present but unreadable
    ramp     = clamp( (value − Q1) / (upper_fence − Q1), 0, 1 )

D           = 0.80 + 0.50 × ( 1 − Π (1 − ramp) )        noisy-OR over the quantities
R           = min( 125, cell × D )
```

Noisy-OR rather than a maximum because breadth composes multiplicatively — seventeen
calendars over a year covers seventeen times more than one calendar over a year, and a
maximum cannot express "wide in two dimensions at once". It stays bounded, stays monotone,
and still saturates on any single argument that reaches its fence. On this corpus 694 of
1,026 scored calls carry more than one judgeable quantity, so it is the common case.

### Worked, with real rows from `scored_calendar_aurora.csv`

**A wide call.** `get-freebusy`, 17 calendars, a full year, expansion at the maximum:

```
calendarExpansionMax = 50   Q1=5  fence=42.5   ramp = (50−5)/(42.5−5)  = 1.00 (clamped)
calendars            = 17   Q1=5  fence=25     ramp = (17−5)/(25−5)    = 0.60
<span:days>          = 365  Q1=7  fence=439.5  ramp = (365−7)/(439.5−7)= 0.83

noisy-OR = 1 − (1−1.00)(1−0.60)(1−0.83) = 1.00
D        = 0.80 + 0.50 × 1.00 = 1.30
```

Any one argument at its fence saturates the call, which is intended: a request at the
widest the contract allows is a wide request regardless of what else it carries.

**A middling call.** `list-events`, 12 calendars, a fortnight:

```
calendarId  = 12   Q1=4  fence=26.5   ramp = (12−4)/(26.5−4) = 0.36
<span:days> = 14   Q1=7  fence=214.5  ramp = (14−7)/(214.5−7)= 0.03

noisy-OR = 1 − (1−0.36)(1−0.03) = 0.38
D        = 0.80 + 0.50 × 0.38 = 0.99
```

**A narrow call.** `search-events`, one calendar, one week:

```
calendarId  = 1    Q1=Q3=1 → flat sample, nothing to grade against → ramp 0
<span:days> = 7    Q1=7  fence=439.5  ramp = 0

D = 0.80
```

The flat-sample rule matters here: every observed `search-events.calendarId` was 1, so the
fences collapse onto that value and *any* other value would read as an outlier. Treating
it as routine is the honest reading, not an escalation.

## Step 4 · Results on 1,500 real benign calls

Warm on the first 500 calls of each server's corpus, score the last 500 — same
distribution both sides, so a cold-start artefact cannot masquerade as an outlier. Every
call is benign by construction.

| server | scored | min | p25 | median | p75 | max | distinct D | above 1.0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| github | 500 | 0.80 | 0.86 | 1.00 | 1.11 | 1.29 | 53 | 35.8% |
| slack | 500 | 0.80 | 0.80 | 0.87 | 1.00 | 1.30 | 22 | 11.2% |
| calendar | 500 | 0.80 | 1.00 | 1.00 | 1.00 | 1.30 | 81 | 19.8% |

Per-call rows, with every quantity's own ramp and where the reference came from, are in
`scored_<server>.csv`. Throughput is 24,000–27,000 calls/sec — 37–43 µs per call, no model
and no network at runtime.

### Why a continuous ramp instead of bins

The same 1,500 calls under a three-bin `D` produced **3 distinct scores**: `limit=1`, `10`,
`50` and `100` were indistinguishable and only the extreme stood out. The ramp produces
22–81 per server while routine calls still sit on the floor:

```
get-freebusy.calendars    1→0.80   5→0.80   10→0.93   13→1.00   17→1.10
list_commits.perPage      1→0.80  25→0.88   50→1.00   75→1.12  100→1.25
channels_list.limit       1→0.80  50→0.89  100→1.00  999→1.30
```

A cut-point can say *whether* a call crossed a line. It cannot order the calls on either
side of it, and ordering is the entire output of this layer.

### Reading the three servers

**Calendar** clusters hard at 1.00 — its p25, median and p75 are all 1.00. 840 of its
judgements abstained for want of history: only 7 of its quantities reached the 20-value
minimum within 500 warm-up calls, because its traffic spreads across 13 tools. That is the
honest cold start, not a tuning failure.

**Slack** is the narrowest (median 0.87, only 11.2% above 1.0) because its learned fences
are wide — `channels_list.limit` runs to 999 in ordinary use, so most calls sit low on the
ramp.

**GitHub** is the most spread (35.8% above 1.0, p75 1.11) because its paging arguments are
exercised across their whole legal range, so the quartiles are tight and ordinary variation
registers.

## The ranking, and why it is not used in the arithmetic

The scan also returns a `rank` per input — the model's ordering of a tool's inputs by how
much of the system the call can be made to touch. It is **not** used to weight `D`.

**Ranking within one tool is the right scope** — all of a tool's inputs compete for the
same call, so they are the correct comparison set. The only degenerate case is a tool with
a single input, where a rank of 1 carries no information; that is 4 of 55 tools here
(github 0/26, slack 2/16, calendar 2/13).

**But the ordering is not stable enough to multiply by.** Asked twice with the inputs
presented in opposite order — identical content, only the presentation reversed:

```
24 tools    mean Kendall tau 0.538    median 0.60    identical orderings 3 / 24
```

Against thresholds fixed before the measurement (≥0.8 usable, 0.4–0.8 explanation only,
<0.4 unusable), 0.54 lands in the middle band. The pattern is sharper than the mean:

| inputs per tool | tau |
|---|---|
| 3–5 | 0.33 … 1.00, several perfect |
| 6–8 | 0.40 … 0.79 |
| **20–23** | **−0.37, −0.47** |

Negative tau on the two largest tools is the signature of the model echoing back the order
it was given, so on a 23-input tool the "ranking" is largely the schema's declaration
order. Weighting `D` by that would make the score depend on how a server author happened
to write their JSON.

Measured directly, weighting also suppressed the calls it should raise: a request for the
largest page a listing API allows fell from **1.30 to 0.88** under a top-heavy curve,
because that page size ranked third among its tool's inputs.

`rank` is therefore kept for explanation — *which input to look at first* — where a wobble
costs nothing. `--rank-weight` enables the weighting for anyone who wants to experiment;
it is off.

### The obvious fix, not yet done

Ranking could be a **second pass over the JSON the first pass returns**, rather than
riding along with the classification. That would decouple them: classification would no
longer depend on presentation order at all, the ranking prompt could be repeated over
shuffled orders and aggregated (the published mitigation for position bias), and
single-input tools would simply be skipped instead of receiving a meaningless rank. It
costs a second model call per tool.

## Full reasoning

[DYNAMIC_EXPLAINED.md](DYNAMIC_EXPLAINED.md) covers every decision in the layer and what
each was measured against — the division of labour between schema, model and traffic, the
omission rule, why quartiles rather than a threshold, why noisy-OR rather than a maximum,
the six things the layer deliberately does not do, and the two bugs (sorted-list eviction,
label-driven parsing) that failed silently before they were found.

## Files

| file | contents |
|---|---|
| `breadth_prompt.txt` | the exact prompt, as sent |
| `<server>_real_scan.json` | per-input `kind`, `targets`, `rank`, `default`, `ceiling`, `source`, `why` |
| `scored_<server>.csv` | one row per scored call: tool, `D`, quantity count, and each quantity's ramp and source |
| `DYNAMIC_EXPLAINED.md` | every design decision and the evidence for it |

## Reproduce

```bash
sbatch scripts/scan_breadth.sbatch                       # classify inputs (GPU, ~5 min)
sbatch scripts/check_rank_stability.sbatch               # position-bias measurement

python3 scripts/dynamic_design/dynamic_v2.py \
    --corpus reports/experiments/real_benign/calendar_aurora_real.csv \
    --split 0.5 --emit scored_calendar_aurora.csv
```

## What this does not show

Every call in the corpus is benign, so nothing here demonstrates that `D` separates misuse
from ordinary use. It shows the shape of the score on real traffic, that routine calls sit
on the floor and wide ones climb, and what the false-alarm side costs. The other side needs
calls that are broad *and* wrong — and those have to come from real usage that happens to
be wide, not from a script that picks large numbers, or the evaluation only rediscovers its
own generator.
