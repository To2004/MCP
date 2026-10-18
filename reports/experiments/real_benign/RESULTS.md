# All-Benign Real Traffic — Warm on Half, Score the Other Half

A second batch of **1000 real read-only calls per server**, independent of the first
(seed 909090), every one benign by construction. Each corpus is split down the middle:
the first 500 calls set the fences, the last 500 are scored against them. Warm-up and
test therefore come from the same distribution, which is the only arrangement that can
tell a cold-start artefact from a real outlier.

Date: 2026-08-13. Corpora: `*_real.csv`. Per-call output: `scored_*.csv`, combined in
`scored_all.csv`. Runtime: [Dynamic Layer v2 — The Calculation](../../../docs/project/dynamic-layer-formula-v2.md).

## The corpora

| server | calls | ok | failed | why the failures |
|---|---:|---:|---:|---|
| github | 1000 | 788 | 212 | search rate limits, empty result sets |
| calendar | 1000 | 958 | 42 | Google per-minute quota (0.7 s pacing, versus 0.1 s last run) |
| slack | 1000 | 1000 | 0 | — |

The call plans were widened to reach every read-only tool that carries a quantity. The
effect on GitHub, comparing the two batches:

| batch | tracked quantities | detail |
|---|---:|---|
| first run | 2 | `list_commits.perPage`, `search_repositories.perPage` |
| **this run** | **14** | `page` + `per_page` across all seven read tools, 104–145 observations each |

That was the point. The previous batch's failure was not that 1000 calls were too few —
it was that they warmed arguments the test corpus never used.

## Result

`D` is continuous over `[0.80, 1.30]`, built from each deployment's own quartiles.

```
server           scored    min    p25  median    p75    p90    max   >1.0
github              500   0.80   0.86    1.00   1.08   1.20   1.25  28.2%
slack               500   0.80   0.80    0.90   1.00   1.00   1.30   8.0%
calendar            500   0.80   0.91    1.00   1.00   1.00   1.30   9.0%

58 distinct scores across 1500 calls        27–32 us per call
```

### Common calls sink, wide calls climb

This is the property the run was for. Within a single tool, the score now tracks how much
the call actually covers:

```
get-freebusy.calendars    1->0.80  5->0.80  10->0.93  13->1.00  17->1.10
list_commits.perPage      1->0.80  25->0.88  50->1.00  75->1.12  100->1.25
channels_list.limit       1->0.80  50->0.89  100->1.00  999->1.30
conversations_history.limit  1->0.80  25->0.84  50->0.90  100->1.02
```

The earlier three-bin version produced **3 distinct scores across the same 1500 calls**:
`limit=1`, `10`, `50` and `100` were indistinguishable, and only `999` stood out. A single
cut-point can say *whether* a call crossed a line; it cannot order the calls on either
side of it, and ordering is the entire output of this layer.

### Where the numbers come from

Design time answers only **which argument is a quantity** — the schema where its types
are honest, a local model where they are not. **No threshold is taken from either.** The
quartiles are built at runtime from the values this deployment has actually passed, which
is why the same `limit=100` reads as routine on GitHub (`perPage` spans 1–100 constantly)
and as wide on Slack (`channels_list` usually asks for far fewer).

Calendar leans on `1.00` at p75 and above because only 4 of its quantities reached
`MIN_HISTORY` within 500 warm-up calls, so many of its calls have no reference yet and
abstain. That is the honest cold start, not a tuning failure.

## What this run establishes

1. **The warm-then-score protocol works end to end** on real traffic, at 25–31 µs per call.
2. **Widening the call plan fixed the transfer problem** — 2 tracked quantities to 14 on
   GitHub, all judgeable.
3. **The score orders benign traffic by breadth** — 58 distinct values, floor at the
   quarter-point, top only at the outlier fence.
4. **The flat-sample guard is load-bearing** — 77 of calendar's judgements would
   otherwise have been outliers-by-construction.
5. **Nothing at design time supplies a number.** The model points at the input; the
   deployment's traffic sets the scale.

## What it does not establish

Nothing here shows the layer separates misuse from ordinary use, because **there is no
misuse in this corpus**. What it shows is the false-alarm side of the ledger, on real
traffic, with a real warm-up. The other side needs calls that are broad *and* wrong —
and those must come from real usage that happens to be wide, not from a script that
picks large numbers, or the evaluation only rediscovers the generator.

`cell` and the final `R` are blank in the per-call CSVs: the real corpora carry no
resolved asset, and mapping a live call to a register asset is the binding layer's job,
not the runtime's. The `D` column is the runtime's whole contribution and is complete.

## Files

| file | contents |
|---|---|
| `github_helios_real.csv`, `slack_vireo_real.csv`, `calendar_aurora_real.csv` | 1000 real calls each |
| `scored_<server>.csv` | one row per scored call: tool, D, quantity count, and the reason |
| `scored_all.csv` | all 1500 scored calls combined |

## Reproduce

```bash
python3 scripts/dynamic_design/make_real_warmup.py --server github --n 1000 \
    --seed 909090 --out reports/experiments/real_benign

python3 scripts/dynamic_design/dynamic_v2.py \
    --corpus reports/experiments/real_benign/github_helios_real.csv \
    --split 0.5 --emit reports/experiments/real_benign/scored_github_helios.csv
```
