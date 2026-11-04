# Probes

The design-phase scripts behind the measured numbers in the v5 knowledge base. Every number they
print is from a **development world** (burnt seeds and organisations) or from synthetic traffic,
never a test result. None of them edits `src/`, the simulator or any design file.

## How to run

- Most probes read the per-call vectors that `dump_vectors.py` writes: one `.npz` per world, with
  a JSON sidecar. Dump them first, then point a probe at the `.npz` files.
- Use numpy and one process. Most probes take about 40-80 s per world.
- Set `PYTHONHASHSEED=0`, because the simulator uses Python's salted `hash` (EV-01).
- The usage line is at the top of each script's docstring.
- Outputs go to the session scratchpad, not the repository.

## Scripts

| Script | What it measures | Inputs | Used by |
|---|---|---|---|
| [dump_vectors.py](dump_vectors.py) | Runs the shipped v4 engine (the simulator's `Variant` with the V4 switches) over a world. It saves every tool call's per-dimension scores, the first-access floor, raw red-flag values and org-discount events. | a simulator world | every `calib_*` probe, `lower_bound_probe.py`, `spell_probe.py`, `org_record_rank_probe.py` |
| [calib_eval.py](calib_eval.py) | The shared evaluator: agent-day scores, fitted and fixed lines, gray recall, credited review list, strata. It is the only source of headline numbers for the calibration arms. | vectors plus one arm's per-call score | all calibration arms |
| [calib_per_dim_conformal.py](calib_per_dim_conformal.py) | Part B arm "daily rates with budget shares": per-dimension rates, the record rank, weighted Bonferroni (9 ArmSpecs, lines 98-110) | vectors | `calib_v5_synthesis.py`, `org_record_rank_probe.py`; v5-calibration §1-§2 |
| [calib_personal_day.py](calib_personal_day.py) | Part B arm "personal day calibration": one day rank per caller, a newcomer pool, the RF1 pooled-line re-implementation `rf1_raised` | vectors | `calib_v5_synthesis.py`; v5-calibration §7 |
| [calib_org_normalised.py](calib_org_normalised.py) | Part B arm "org calibration": each score replaced by its org rate, then weighted Bonferroni | vectors | v5-calibration §6-§7 |
| [calib_group_calibrated.py](calib_group_calibrated.py) | Part B arm "three-group calibration": one calibrated p-value per paper group | vectors | v5-calibration §6-§7 |
| [calib_v5_synthesis.py](calib_v5_synthesis.py) | Revision 1 synthesis arms S0-S7: floor pricing, RF1 line, day units, tenure-band and established references; arm S5 was chosen | vectors | v5-calibration §2, §6 |
| [org_record_rank_probe.py](org_record_rank_probe.py) | **Revision 2.** Arms S5, O1 (record rank among all route agent-days), O2 (Unsafe-sequence records, watch-only Missing handshake, Red Flags at 1/12), O3 (surge guard). Reports per-dimension spend, realised rates on all benign days, gray recall, oracle ROC points and path activity. | vectors | v5-design-spec §2.3, §2.6, Review log R1-4, R2-1, R3-4 |
| [hour_surge_check.py](hour_surge_check.py) | **Revision 2.** Which benign agent-days drive Hour-of-day spend under O1: the release-crunch day | vectors | v5-design-spec §2.6, R3-4 |
| [lower_bound_probe.py](lower_bound_probe.py) | M's bottom of x0.7 against M ≥ 1 on consequential calls, or on every call (PS8, decision D2) | vectors | v5-design-spec D2 |
| [spell_probe.py](spell_probe.py) | Session duration replaced by a per-caller run of calls ended by an idle gap (E4), and the merge-with-no-review step scoped to a run or a fixed window (E5) | vectors (seed 7) | Part A E4, E5 |
| [m_formula_numbers.py](m_formula_numbers.py) | **2026-10-28.** Every number in the one-formula proposal for M: the constants, the guideline table, the H sweep and the conformal false-alarm bound. It also compares two combiners (most unusual dimension vs. the formula applied twice) by Monte Carlo on ordinary days | none (synthetic) | behaviour-multiplier-formula.md |
| [m_formula_scenarios.py](m_formula_scenarios.py) | **2026-10-28, superseded by m_formula_servers.py.** A small prototype of the one-formula M with the 11 proposed dimensions, and a "fixed" design (Step tells a never-touched asset from a blind write, Tool on asset is a frequency among the days the asset was touched, Area adds the asset's folder). One synthetic agent with 90 active days; 18 scenario checks with expectations fixed before running (routine calibration, quiet habits, single and combined anomalies). About 10 s | none (synthetic) | chat report of 2026-10-28; behaviour-multiplier-formula.md |
| [m_formula_servers.py](m_formula_servers.py) | **2026-10-28, supersedes the 12-dimension prototype.** The one-formula M with 8 general dimensions (call rate, tool rate, breadth, read volume, request size, resource, action = this tool on this resource, hour). Resources are binding containers: policy-register id, inferred pseudonym, or none. 24 general scenarios (A stay quiet, B one unusual thing, C several at once, D expected to get through), written once and run on 7 kinds of agent: five shaped like GitHub, Slack, Calendar, SQLite and Filesystem (real tool names), one always-on and one with very uneven volume. Expectations fixed before running. About 1 min | none (synthetic) | chat report of 2026-10-28 |
| [m_formula_pinecrest.py](m_formula_pinecrest.py) | **2026-11-01.** The author's Pinecrest scenarios ("Dynamic score scenario report"; scenario 8, the long session, removed by the author) against the deck's expected curves. Variants: J4 (four dimensions on calls, plain k), J4s (smooth k: near past calls count partly; Sidak for four dimensions) and J4s with Time of day split into weekday and weekend (the other kind of day counts 1/10 or 1/16). `--plot <png>` draws pinecrest_smooth_k.png (conda `python3 -I`, needs matplotlib). pinecrest_vs_deck.png is the earlier figure (J, K, J+, K+) | none (synthetic) | chat reports of 2026-11-01 |
| [m_formula_candidates.py](m_formula_candidates.py) | **2026-10-29.** Candidate formulas A-K for M on the 6 agreed dimensions (Tool, Asset, Tool on asset; Calls this hour, Breadth, Time of day). They include the deck's v4 scores, the deck's model fixed, the product of ratios, ranks on calls and on days, the strangest dimension, the total surprise, J (the current choice: calls with the settled design rules) and K (days with the same rules). 20 scenarios on 7 agents (132 checks), including probe-then-strike for the denied-call rule. `--seeds 101,...,110` prints means with 95% intervals; `--explain` prints the reason shown with M. About 18 s per seed | none (synthetic) | dynamic-score-report.md §4-§5b |
| [red_flag_arms.py](red_flag_arms.py) | Red-flag mechanics arms from one v4 engine pass: habit keys, org-discount variants, oversized limits by the agent-day procedure | a simulator world | Part A RF1, RF6, RF7, RF11 |
| [red_flag_arms_table.py](red_flag_arms_table.py) | Prints several `red_flag_arms.py` outputs side by side | `red_flag_arms.py` JSON | Part A RF |
| [pooled_line_rates.py](pooled_line_rates.py) | Realised raise rate of the oversized line learned as one pooled agent-day budget, with and without leaving out the top identity | a simulator world (imports `red_flag_arms.py`) | Part A RF1 |
| [baselines_identity_probe.py](baselines_identity_probe.py) | Raw-traffic facts behind the baseline choices: novelty inversions and monotone novelty rules (N7), per-day caps and the bucketed usual (N5), UTC days (N27), absence gaps (N10) | a simulator world | Part A B1-B10 |
| [binding_identity_probe.py](binding_identity_probe.py) | The measured binding failures (C5, N1) against the real remote GitHub scan, and the target-input / container-handle prototype | the remote GitHub scan cells | Part A AI-1-AI-5 |
| [gha_body_sizes.py](gha_body_sizes.py) | Feasibility of the real-data step: request-body sizes in one GH Archive hourly file. It prints counts and quantiles only, never actor logins. | GH Archive JSON lines on stdin | Part A EV-26; Hyp5 |
| [gateway_scale_probe.py](gateway_scale_probe.py) | Snapshot size, save time and per-call cost of the shipped v4 engine on **synthetic** traffic, extrapolated to 10^4 identities and 10^5 assets (systems reviewer) | synthetic | v5-design-spec §2.9, §6.10, R3-1, R3-7 |

## Notes

- `calib_eval.py`, `calib_per_dim_conformal.py`, `calib_personal_day.py` and
  `calib_v5_synthesis.py` are also imported as modules by later probes. Change their interfaces
  only together with every importer.
- The revision 2 probes run on v4 score vectors, so their numbers are "calibration stage on v4
  scores", not v5 numbers. Plan Batch 4 (L2) re-runs them on score logs from the v5 engine.
- `__pycache__/` is a local artefact and is not part of the probes.

## References

- [v5-design-spec.md](../v5-design-spec.md), [v5-calibration.md](../v5-calibration.md),
  [v5-implementation-plan.md](../v5-implementation-plan.md).
- The engine and simulator files the probes import are cited in each script's docstring.
