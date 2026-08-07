# v3 — deterministic rules + how much description is needed

Inputs everywhere: the tool catalog + the org profile, nothing else (the `pure`
shape adopted in v2). What changed is the deterministic layer and the amount of
profile the model sees.

## The current best result

| Folder | What |
|---|---|
| **`five_level_v2_pure_v3/`** | **all four MCP servers** — calendar, slack, github, filesystem. Start with `ALL_SERVERS_summary.md`; per server there is a `_matrix.csv`, a `.md` report and the full `.json`. `inputs/` holds the exact catalog + profile each run consumed, `scoring-prompts.md` every prompt sent. |

Rules added in v3 (all score-side; bands stay a pure function of the score):
- **bulk-twin dominance** — a bulk variant always outscores its singular twin
  (prompt guidance + deterministic backstop). Fixed `create-events` ≤ `create-event`
  and the `read_multiple_files` < `read_file` inversion.
- **impact-keyed floors** — impact 5 → blast ≥ 3, impact 4 → blast ≥ 2, regardless
  of sensitivity (the mirror of the sens-keyed floors, one tier lower).
- **blast roofs** — cap reads that cannot legitimately escape. Safety invariant:
  only impact ≤ 3 cells are ever capped, so no mutation can be under-scored;
  assets flagged hub/population/self-sufficient are exempt.
- **bands recalibrated to the 125 scale** as pure thresholds: low <17 ·
  medium 17-49 · high 50-99 · critical ≥100 (no categorical overrides).

## Scheme / context arms (roof-free, calendar)

| Folder | Profile the model saw | Result |
|---|---|---|
| `five_level_v2_pure_noflags/` | flags stripped from Contents | ≈ baseline — prose already carried the hub meaning |
| `five_level_v2_pure_terse/` | fact line + Asset/Sens/shape table, NO prose | fixed the recruiting blast over-read (5→4) but broke relevance: 22 more cells scored, `create-events` impact fell 5→4 |
| `five_level_v2_pure_rich/` | full profile + whole tool registry in every prompt | ≈ baseline, also fixed recruiting |
| `roof_experiment/` | offline comparison of 3 roof rule-sets | conservative roof adopted (3 cells on calendar, 0 elsewhere) |

**Finding** (`scheme_context_comparison.md`): "less is better" holds for blast
only. Less prose *hurts* tool impact and N/A relevance. Keep the full profile;
correct prose-driven blast over-reads with the roof instead.

## Not run

`five_level_v2_pure_imponly/` and `five_level_v2_pure_nodom/` are empty — those
arms (impact stage without the asset table; no inferred-domain stage) failed on
an unregistered-mode error, were fixed in code, but have not been re-run.
