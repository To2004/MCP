# Dynamic Layer v2 — Two Independent Factors

v1 multiplied the static cell by one blended number. v2 splits that into two factors that
answer different questions and land in different dimensions of the matrix the scan already
defines, so neither can double-count the other and each can be evaluated on its own.

Run in full on 2026-08-14: breadth classification of all three servers on a GPU, then the
runtime over 3,000 real calls. Everything here is reproducible from the files alongside.

## The formula

```
R(c) = min( 125 , cell(tool, asset) × B(c) × L(c) )
```

| factor | asks | direction | reads |
|---|---|---|---|
| `B` | is this call **narrower** than the worst case blast already priced? | **≤ 1.0** only | argument values against their own Q1 |
| `L` | is this **tool** usual for this deployment? | both ways | tool call counts against the median tool |

### Why `B` can only discount

The scan's blast-radius prompt rates *"the reach of ONE call ... if ONE call runs **or is
misused**"*, with tier 4 being *"one call reaches essentially everything it holds"*, and the
v4 ONE-CALL rule making a tool that takes an array count as sweeping. **`blast_static` is
already the worst case a single call can do.** A call at the wide end is therefore exactly
what was priced; only a demonstrably narrow one earns its way down. Pushing it up would
count reach twice.

This mirrors CVSS, where the Base score is the worst-case reasonable assumption and
Environmental metrics exist to adjust for evidence that the real situation is narrower.

### `B` is gated at Q1: ordinary is 1.0

```
v ≥ Q1                    → B_i = 1.00                     nothing earned
v < Q1  → B_i = 0.70 + 0.30 × (v − min_seen) / (Q1 − min_seen)

w_i = BREADTH_WEIGHT[level_i] / BREADTH_WEIGHT[most central level on this tool]
B   = max over i of ( 1 − w_i × (1 − B_i) )
```

Everything from Q1 up is what the deployment ordinarily does, so it scores exactly what the
scan priced. Only the bottom quartile earns a discount, reaching `B_MIN = 0.70` at the
narrowest value ever observed. **`max` is the conservative choice**: one argument at the
wide end cancels the discount, because a call wide in any dimension is not a narrow call.

**The bottom anchor is `min(seen)`, not Tukey's lower fence.** These quantities are positive
and right-skewed: a page size with Q1 5 and Q3 75 puts the lower fence at **−100**, so the
ramp spreads over 105 unreachable units and a call asking for 1 earns a 1% discount instead
of 30%. The narrowest value actually observed is always reachable and means something
concrete — as narrow as this deployment has ever gone.

### Why `L` moves both ways

The neutral point is **the median tool this deployment actually calls**.

```
share = (calls to this tool + α/V) / (total calls + α)        α = 30, V = tools exposed
ratio = share ÷ median share over the tools with traffic

ratio < 1 →  L = 1 + 0.30 × (1 − ratio)          rare   → up to 1.30
ratio > 1 →  L = 1 − 0.15 × (1 − 1/ratio)        common → down to 0.85
```

An earlier draft anchored on an **even split over the whole exposed catalog**. That is the
wrong reference: a deployment calling 6 of 13 exposed tools has every one of those 6 above
an even split, so all six were "common", every call was discounted, and no call could reach
1.0 no matter how ordinary it was. Anchoring on the median *used* tool puts typical traffic
at 1.0 by construction and leaves both directions live.

The discount side is deliberately **half** the escalation side. Commonness exonerating is
the failure mode with history here: a symmetric likelihood measured net-negative on all
three servers, and per-identity conditioning collapsed misuse AUC 0.53 → 0.30. Rarity is
evidence; commonness is not exoneration.

## Step 1 · The scan

`kind` and `breadth`, judged independently, for **every** parameter — full prompt in
[`breadth_prompt.txt`](breadth_prompt.txt).

| server | tools | inputs | graded | ungraded | model seconds |
|---|---:|---:|---:|---:|---:|
| github | 26 | 130 | 130 | **0** | 136 |
| slack | 16 | 63 | 63 | **0** | 71 |
| calendar | 13 | 110 | 110 | **0** | 103 |

### `breadth` measures centrality to the asset, on a domain-neutral test

The rubric asks **how central a parameter is to the asset the call acts on**, 5 highest. An
earlier version wrote the anchors as lists of nouns — *calendar, repository, channel, table,
file* at 5, *cursor* at 2, *dry-run flag / locale* at 1. Those are the three servers being
measured. A model reading that is pattern-matching the dev set, and the next server, whose
assets are none of those nouns, has nothing to match on.

The levels are now defined by **what changes when you change the value**, holding every
other parameter fixed:

| | changing this value means… |
|---|---|
| 5 | a different stored thing is acted on — or several at once |
| 4 | the same thing, but materially different contents are read or written |
| 3 | the same contents, in a different amount or slice |
| 2 | the same data, presented differently |
| 1 | nothing about the stored data changes |

No product nouns appear anywhere in it, so a server exposing datasets, tickets or devices is
classified by the same question as one exposing repositories. Four rules override intuition
from a parameter's name: a list or pattern selecting stored things is 5 however few entries
it carries; a filter *within* something already selected is 3 however powerful; centrality
is not sensitivity in either direction; and **ties break downward**.

| server | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| github | 7 (5%) | 14 (11%) | 27 (21%) | 20 (15%) | 62 (48%) |
| slack | 0 | 8 (13%) | 22 (35%) | 16 (25%) | 17 (27%) |
| calendar | 16 (15%) | 11 (10%) | 34 (31%) | 23 (21%) | 26 (24%) |

GitHub's mass at 5 is structural rather than inflation: 26 tools take `owner` and `repo`,
which is 52 of its 130 inputs, and both genuinely select which stored thing is acted on.

Spot-checked on `calendar`: `calendarId` and `account` are 5, `query` 4, `timeMin`/`timeMax`
3 — they size a window inside an already-chosen calendar — and `timeZone` 2.

**`breadth` is graded independently of `kind`.** An identifier has no larger or smaller
value — `kind: none` — but it may be the very thing that names the asset. In v1 the two were
tied together and 66% of inputs were pushed into the bucket that weighs nothing purely
because no number could be read from them.

**Every parameter goes to the model, including ones the schema settles.** `source` records
which pass decided: `llm` where structure was silent, `schema+llm` where the schema owned
`kind` (an array's length is a count regardless) and the model graded reach. An earlier
attempt asked only about schema-ambiguous inputs and left **58 arrays with no reach grade at
all** — the inputs whose length *is* the fan-out.

## Step 2 · The result on 3,000 real benign calls

Warm on the first 500 of each corpus, score the last 500.

| server | n | min | p25 | median | p75 | max | distinct | below 1.0 | at 1.0 | above 1.0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| github | 500 | 0.97 | 0.99 | **1.00** | 1.01 | 1.06 | 284 | 40% | 13% | 47% |
| slack | 500 | 0.84 | 0.93 | **1.00** | 1.02 | 1.07 | 304 | 51% | 15% | 34% |
| calendar | 500 | 0.88 | 1.00 | **1.00** | 1.03 | 1.07 | 278 | 29% | 23% | 48% |

**The median call scores exactly 1.00 on all three servers**, and traffic lands on both
sides of it. That is the intended shape: an ordinary call is worth what the scan priced,
narrower calls earn their way down, and calls to tools this deployment rarely touches rise.

19,000–24,000 calls/sec, 41–53 µs per call, no model and no network at runtime.

### Where each quantity's verdict came from

| | github | slack | calendar |
|---|---:|---:|---:|
| `ordinary` (≥ Q1, no discount) | 783 | 447 | 379 |
| `no history` (< 20 observations) | 132 | 255 | 840 |
| `flat` (every observed value identical) | — | 134 | 77 |
| `narrow` (< Q1, discounted) | 91 | 61 | 64 |

Calendar's dominance of `no history` is why its p25 is already 1.00: most of its quantities
never reached the 20-observation minimum in 500 warm-up calls, so `B` stays at 1.0 and `L`
alone moves the score.

### The escalation side, checked directly

The corpora are benign and call a fixed set of tools, so nothing in them is rare. Probing
the warmed model with tools the deployment never called:

| server | tool | calls seen | L |
|---|---|---:|---:|
| calendar | `list-events` | 81 | 1.01 |
| calendar | **`delete-event`** | **0** | **1.28** |
| github | `list_commits` | 60 | 1.02 |
| github | **`create_or_update_file`** | **0** | **1.28** |
| slack | `conversations_history` | 72 | 0.99 |
| slack | **`conversations_add_message`** | **0** | **1.28** |

A tool the deployment actually uses sits at ~1.0; one it has never used escalates by 28%.
The path works and never fires here, which is what a benign corpus should look like.

## What this does not establish

Every call is benign by construction, so nothing here shows the layer separates misuse from
ordinary use. It shows the shape of the score on real traffic and that both factors behave
as specified. The other half needs calls that are broad *and* wrong, or that use tools this
deployment does not — and those have to come from real usage, not a script that picks
unusual values, or the evaluation only rediscovers its own generator.

The rubric's **label stability is still unmeasured**. Kendall τ 0.538 describes v1's
listwise *ordering* and says nothing about a pointwise 1–5 score; the equivalent check is
the flip rate over repeated runs at temperature 0. Generality is likewise argued from the
rubric's wording, not yet demonstrated — the test is two servers held out of development.

`cell` is blank in the per-call CSVs: the real corpora carry no resolved asset, and mapping
a live call to a register asset is the binding layer's job. `B` and `L` are the runtime's
whole contribution and are complete.

## Files

| file | contents |
|---|---|
| `breadth_prompt.txt` | the exact prompt, as sent |
| `<server>_real_scan.json` | per-input `kind`, `breadth`, `default`, `ceiling`, `source`, `why` |
| `scored_<server>.csv` | one row per scored call: `D` = `B × L`, and each quantity's own discount, weight and source |

## Reproduce

```bash
sbatch scripts/scan_breadth.sbatch            # classify every input (GPU, ~6 min)

python3 scripts/dynamic_design/dynamic_v2.py \
    --corpus reports/experiments/real_benign/calendar_aurora_real.csv \
    --split 0.5 --emit scored_calendar_aurora.csv
```
