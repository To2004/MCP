# Ult ablation arms — comparison and verdict

Four scans of the same 4 servers, each moving ONE prompt-context lever over the
identical `five_level_v2_ult` machinery, plus the `pure` (tools+description-only)
registry experiment on calendar. Agreement = same band on shared scored cells
vs the base arm.

## Aggregate agreement vs base

| arm | lever | agreement | drift direction | verdict |
|---|---|---|---|---|
| leanimp | description withheld from impact stage | 492/534 (92%) | ±small, symmetric | Lever unnecessary — the description does NOT bias impact. Keep base (simpler: one preamble everywhere). |
| tools | full tool registry in every impact/blast prompt | 451/518 (87%) | mixed | **Rejected** — it DEMOTED the one cell that must be critical: `manage-accounts` on the `hub`-flagged `connected-account-config` fell 125 critical → 100 high. The registry context distracts the blast judgement. |
| struct | structured-only profile (table + CIA, no prose) | 421/507 (83%) | systematically UP (55 higher vs 31 lower; calendar high 6 → 17) | **Rejected** as sole scheme — prose moderates; table-only over-escalates. The prose is doing real calibration work. |
| pure | registry built from catalog + profile only | 64/67 (95.5%, calendar) | ±tiny | **Adopted** — reproduces the full scan without any store access; all key cells identical. |

Key-cell check (calendar): `delete-event` = high on personal/exec in every arm;
`manage-accounts|connected-account-config` = 125 critical in every arm EXCEPT
tools (100 high).

## Conclusion (the "v2")

No prompt-context lever improves on the base configuration — each either
changes nothing (leanimp), distracts (tools), or over-escalates (struct). The
supported improvement is not a prompt change but an input change: **pure mode**
(tool catalog + spec-v1 org profile as the only inputs) matches the full scan
at 95.5% band agreement and is the realistic deployment shape. v2 therefore =
base ult scoring machinery + pure registry construction, with a rerun-stability
measurement (two identical pure scans compared cell-by-cell) as the final
validation — the panel's standing demand from every prior round.

Caveat (standing): part of each arm's drift is LLM re-scan variance, not the
lever; the rerun-stability measurement bounds exactly that.
