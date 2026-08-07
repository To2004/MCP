# Why near-identical tool impact still gives a different risk matrix

The static arm agrees with the LLM arm on **65 of 74 tool impacts (88 %)**, yet
`five_level_v2_pure_v4static` and `five_level_v2_pure_v4_bulkclause` publish
visibly different severity matrices. Both facts are true, and the reason is
structural, not a bug.

Measured, not asserted: `scripts/decompose_arm_gap.py` replays each arm's stored
inputs through the identical assembly and swaps **one axis at a time**.

| combination | impact from | blast from |
|---|---|---|
| A | bulkclause | bulkclause |
| B | static | static |
| C | static | bulkclause |
| D | bulkclause | static |

A→C is the impact axis alone. A→D is the blast axis alone.

## The decomposition

| server | total gap | impact alone | blast alone | interaction | impacts differing | blast cells differing |
|---|--:|--:|--:|--:|--:|--:|
| calendar | −104 | **−77** | −37 | +10 | 1 / 13 | 13 / 208 |
| slack | +165 | −111 | **+276** | 0 | 2 / 16 | 32 / 320 |
| github | +474 | **+282** | +167 | +25 | 5 / 26 | 33 / 520 |
| fs:corp | +247 | **+301** | −38 | −16 | 2 / 14 | 32 / 308 |
| sqlite | +18 | 0 | **+18** | 0 | 0 / 5 | 2 / 55 |

Read the slack row carefully — it is the most instructive. The two impact
disagreements point in *opposite* directions (`conversations_leave` 5→4,
`usergroups_me` 4→5) and net out to **−111**, yet the arm scores **+165 higher**.
The entire visible difference, and more, comes from blast.

And sqlite is the control: **zero** impact disagreements, and the matrices still
differ — by 18 points, on two blast cells.

## Cause 1 — an impact is a row multiplier, not a cell

This is the part that makes "only 5 of 26 tools" misleading.

Sensitivity and blast are scored **per (tool, asset) pair**. Tool impact is scored
**once per tool** and then multiplies *every asset cell in that tool's row*.

| server | tools differing | assets | cells that changes | % of matrix |
|---|--:|--:|--:|--:|
| github | 5 / 26 | 20 | **100** | 19.2 % |
| fs:corp | 2 / 14 | 22 | 44 | 14.3 % |
| slack | 2 / 16 | 20 | 40 | 12.5 % |
| calendar | 1 / 13 | 16 | 16 | 7.7 % |

github's "5 of 26 tools" — 19 % agreement loss by tool count — is **19 % of the
entire matrix** by cell count. And each of those cells moved by a full ratio step:
2→3 multiplies a cell by 1.5, 4→5 by 1.25. That is where fs:corp's +301 comes
from with only two tools differing: 44 cells × 1.5.

## Cause 2 — blast disagrees far more often than impact

Both arms ran the same model, same prompt, temperature 0, seed 0. They still
disagree on blast:

| server | blast cells differing | of which N/A flips |
|---|--:|--:|
| sqlite | 2 / 55 | 0 |
| calendar | 13 / 208 | 1 |
| slack | 32 / 320 | 6 |
| github | 33 / 520 | 7 |
| fs:corp | 32 / 308 | 5 |

6–10 % of blast cells, and the **N/A flips are the expensive ones** — a cell
moving between "this tool doesn't touch this asset" and a real score is not a
1-point change, it is 0 ↔ up-to-125.

This is the same self-inconsistency documented in `ARM_COMPARISON.md`: blast is a
harder judgement (reach across an asset the model must reason about) than impact
(what kind of action is this, answerable from the tool's own text).

## Cause 3 — the deterministic passes couple the two axes

The impact-keyed floors gate on impact:

```
gated blast floor (impact >= 4): sens 5 -> blast >= 4, sens 4 -> blast >= 3
impact-keyed floor:              impact 5 -> blast >= 3, impact 4 -> blast >= 2
blast roof (impact <= 3 only):   non-escaping reads cap at 4
```

So a single impact change does not just rescale a row — it can **flip which rules
apply to it**. A tool moving 3→4 crosses the floor gate, so its low-blast cells
get raised; a tool moving 4→3 becomes eligible for the read roof, so its high-blast
cells get capped. That is the `interaction` column: +25 on github, −16 on fs.
Small, but it proves the axes are not separable.

## What actually reaches the published matrix

| server | cells whose score changed | of those, band changed |
|---|--:|--:|
| calendar | 19 / 208 (9 %) | 11 |
| slack | 43 / 320 (13 %) | 22 |
| github | 53 / 520 (10 %) | 31 |
| fs:corp | 50 / 308 (16 %) | 14 |
| sqlite | 1 / 55 (2 %) | 1 |

Roughly 10–16 % of cells move, and about half of those cross a band boundary.
A band distribution differing by 10–15 counts is exactly what 10 % moved cells
produces — the matrices look more different than the inputs are.

## The answer in one paragraph

"88 % impact agreement" is a statement about **74 tools**. The matrix is made of
**1 411 cells**. One tool impact multiplies a whole row of 16–22 cells, so 9
disagreeing tools touch 200 cells; blast disagrees on another 112 cells
independently, including 19 N/A flips worth up to 125 points each; and the floors
and roofs gate on impact, so changing impact also changes which cells the
deterministic passes touch. Near-identical impact was never going to give a
near-identical matrix — and on slack and sqlite, the difference isn't impact at
all.
