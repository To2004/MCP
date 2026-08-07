# v2 — the organization's own description

The question: can the org's written profile (`docs/mcp-tools/server-profiles.md`)
replace what the scanner infers? Two answers, one rejected and one adopted.

## The rejected step

| Folder | What it did | Verdict |
|---|---|---|
| `five_level_v2_desc/` | org prose in front of every stage AND the sensitivity primitive **deleted** (score = blast × impact, max 25); 13 servers | Panel 5.13 — rejected. Value leaked into blast, per-patient PHI reads priced as low as a README, no challengeable number left. |

## The adopted step — `ult`

Sensitivity comes back, but as the **org's own per-asset table** (never LLM-scored;
the scan aborts naming any asset missing a row). Plus the v1 gated floor folded
into assembly, an alias-twin pass, and `band_label_v5`.

| Folder | Arm |
|---|---|
| `five_level_v2_ult/` | the base ult scan, 4 servers (with store access) |
| `five_level_v2_ult_grid/` | offline grid: floor gate ≥3/≥4 × sens-4 floor 2/3 |
| `five_level_v2_ult_tools/` | ablation: full tool registry in every prompt |
| `five_level_v2_ult_leanimp/` | ablation: description withheld from the impact stage |
| `five_level_v2_ult_struct/` | ablation: structured-only profile (no prose) |

**Ablation findings** (`ult_ablation_comparison.md`): none beat the base —
`tools` demoted the hub-critical cell (rejected), `struct` over-escalated
(rejected), `leanimp` changed nothing (unnecessary). Grid finding: all four
floor variants gave identical band distributions.

## The production shape — `pure`

| Folder | What |
|---|---|
| `five_level_v2_pure/` | registry built from the tool catalog + profile ONLY — no store, no generated assets |
| `five_level_v2_pure_rerun/`, `_rerun2/` | two independent repeats: **all three runs bit-identical**, 208/208 cells |

**Finding:** pure matched the full-input scan on 64/67 shared cells (95.5%;
91.8% counting N/A migrations) with every key cell identical — the profile spec
is sufficient scanner input. Panel: **8.38, unanimous first** (`ultimate_agent_panel.md`).

Reports: `desc_experiment_agent_panel.md`, `ult_ablation_comparison.md`,
`ultimate_agent_panel.md`.
