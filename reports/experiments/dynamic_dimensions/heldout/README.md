# Held-out evaluation harness (dynamic layer v5)

This folder holds the analysis harness for the v5 held-out evaluation: world pools and seeds,
provenance, the development selection rule, the metrics and statistics, the combiner family and
the outside baselines. It implements spec section 6 of
[v5-design-spec.md](../knowledge_base/v5-design-spec.md) (Batch 1, implementer I10 of
[v5-implementation-plan.md](../knowledge_base/v5-implementation-plan.md)).

## Files

| File | Change | What it does |
|---|---|---|
| `heldout_world_spec.py` | EV-15, EV-17 | The range file: pools (`dev`, `calibration`, `test`), families W1-W8 and their ranges, burnt seeds, `derive_seed` with the public beacon (the full commit sha and the beacon in one canonical spelling), `seed_plan`, `world_spec`, `family_size` |
| `heldout_provenance.py` | EV-02, EV-15 | File and config digests, git state, imported files, the provenance block with config and policy digests per engine, `check_mergeable` and `merged_provenance`, the freeze file set and manifest |
| `select_v5.py` | EV-16 | Spec 6.2's rule: matched-cost pAUC objective, admissibility constraints, argued-switch admission, margins of 1.64 x the world-level SE fixed in the hashed rule, the cumulative x3 cap, ties to fewer constants |
| `heldout_metrics.py` | EV-18, EV-19, EV-24, EV-31 | Local-day keys in deployment days, agent-days, credited pAUC over [0, 3%], threshold fits, the credited review list, per-dimension spend with Holm, the caller's active days A and the tenure bands, 30-day periods, transfer ratio, PPV, harm before the first alert, the gate curve of R |
| `heldout_stats.py` | R2-8 | Wilson, the binomial tail, Holm, the world-only bootstrap (B = 10,000, percentile or BCa), the world-level sign-flip test, the Wilcoxon signed-rank test over worlds (Hyp6) |
| `combiner_family.py` | EV-20 | Matched-budget combiners on scores and on ranks (Footprint enters as a rank under D3 (a) and (b)), leave-one-out ablations, Hyp4's simultaneous non-inferiority bounds |
| `outside_baselines.py` | EV-22 | Static only, Red Flags only, per-agent max \|z\|, a numpy Isolation Forest and its grid choice, role peer group, Guardian-, AegisMCP- and Praetor-style baselines, simplified personal-day and org calibrations |

`gharchive_request_sizes.py` and `gharchive_actor_cadence.py` belong to the GH Archive
implementer (I11, EV-26 and X2), who placed them here; see their docstrings.

## Use

The modules take numpy arrays from a score log; they never run an engine. Import them as a
package from the repository root:

```python
import normal_org_world as W  # reports/experiments/dynamic_dimensions on sys.path

from reports.experiments.dynamic_dimensions.heldout import heldout_metrics as hm
from reports.experiments.dynamic_dimensions.heldout import heldout_world_spec as ws

days = hm.group_agent_days(agent, hm.local_day_keys(ts, zones, base_day=W.BASE_DAY))
dm = hm.day_max(days, s1, s2)
pauc = hm.credited_pauc(days, dm, episode, window=ws.SELECT_WINDOW)
```

Conventions:

- **Agents.** The agent label is the baseline key the engine kept history under: the signed-in
  agent, or the reported client and address without sign-in (spec 2.1, decision D5). Results
  can be split by identity strength with `rate_by_group`.
- **Deployment days.** Every window counts days from deployment day 0: the route warm-up
  stratum is days 0-89, thresholds are fitted on days 90-134, selection metrics use days 135-180,
  and the 30-day periods start at day 90. Pass `base_day` to `local_day_keys`: the simulator's
  `normal_org_world.BASE_DAY`, or `clock.local_day` of a route's first call. Day keys counted
  from 1970 are refused with a `ValueError`.
- **Margins.** The selection rule's margins are numbers fixed in the hashed rule. Batch 5 runs
  `select_v5.derive_margins` on the L2 v5-engine development runs and writes the result into the
  rule before hashing it.
- **Combiners.** Every combiner arm, the `v5` arm included, is compared without floors: the
  `v5` arm is the statistic alone, not the shipped s1.

Every module uses numpy and the standard library only (plus `mcp_security.behaviour` for the
clock and the dimension layout). Tests: `uv run pytest tests/dynamic_dimensions/test_heldout_*.py`.

## Numbers

Every number these modules produce on a simulator world is a **development-world or synthetic
number**. Paper numbers come only from the frozen shipped engine on held-out worlds (spec 6.3).

## References

- [v5-design-spec.md](../knowledge_base/v5-design-spec.md), sections 2.1, 2.4-2.8 and 6.
- [probes/calib_eval.py](../knowledge_base/probes/calib_eval.py): the threshold fit, the
  list's exact tie expectation and the Wilson interval were copied from it.
