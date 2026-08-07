# v1 — rubric search

Scanner inputs: tool catalog + the demo store (walked for assets) + LLM-generated
homing assets. Asset sensitivity scored by an **LLM stage**. No org profile.

## Rubric candidates

| Folder | Rubric |
|---|---|
| `five_level/` | 5-level action×coverage ladder (impact 1-5) |
| `five_level_v2/` | 5-level action-TYPE ladder (liveness/metadata/read/write/delete) |
| `five_level_v2_fs/` | **the v1 baseline**: five_level_v2 + N/A relevance gate, 5 servers |
| `cia/` | baseline impact + one point per violated C/I/A facet (max 150) |
| `hybrid/`, `hybrid_na/` | action-type impact + reach-of-consequences blast, geometric-mean formula |
| `five_level_v2_finance/` | the finance servers under five_level_v2_na |

## Fixes for the "pinpoint mutation scores low" bug

`delete-event` (impact 5) on a sensitive calendar scored 20/125 because one
event is blast 1. Three independent attempts, judged by a 4-persona panel:

| Folder | Approach | Panel mean |
|---|---|---|
| `five_level_v2_floor/` | deterministic sens-keyed blast floor (`plain` + `gated`) | **gated 7.50 — winner** |
| `five_level_v2_rowfix/` | LLM audits each asset row, repairs ordering violations | 5.88 |
| `five_level_v2_ctx/` | per-tool "understanding" stage injected into blast prompts | 2.75 — last |

**Finding:** context alone cannot fix it — ctx left delete-event at blast 1
because the model correctly said "one call deletes one event". The rubric, not
comprehension, was the constraint. The gated floor won and carried into v2.

Reports: `blast_experiments_comparison.md` (cell-level), `blast_experiments_agent_panel.md`
(the four judges' verdicts).
