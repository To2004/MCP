# Simulator and held-out harness tests

Tests for the dynamic-layer simulator in `reports/experiments/dynamic_dimensions/` and the v5
held-out harness built around it. Every world here is synthetic or a development world; no
test number is a paper number.

## Shared setup

| File | What it gives |
|---|---|
| `world_support.py` | `SIM_DIR`, `ensure_sim_on_path()` (appends the simulator folder, never shadows), and `run_python(code, hash_seed)`, which runs code in a fresh interpreter with a chosen `PYTHONHASHSEED` |
| `conftest.py` | puts the simulator on `sys.path`; the session fixture `v5_world` = `build_world(24, 5, world_version="v5")` |

## World tests (`normal_org_world.py`, Batch 1, I9)

| File | Changes | What it checks |
|---|---|---|
| `test_world_determinism.py` | EV-01 | `stable_hash` pinned and equal to Part A's blake2b formula; a v5 world (today's calendar, and a drawn calendar with churn) has the same digest under `PYTHONHASHSEED` 1 and 2, while the salted order does not; the v4 world `build_world(31, 7)` has the digest the pre-v5 code gave under `PYTHONHASHSEED=0`; extended rows leave the other 13 columns alone |
| `test_calendar.py` | EV-06 | `Calendar()` is today's; drawn calendars keep their ranges, the 7-day gaps and the 0.8 presence rate (180 and 365 days); a world built on a moved calendar shows the migration, rollout, crunch, VPN change and gray episodes on that calendar's days only; absent changes leave no trace |
| `test_response_sizes.py` | EV-07 | every tool has a response model; writes echo 1-3 KB; files are capped at 1 MB; over-fetch pages are at least 3x the usual `list_issues` page, by unit and per episode in a world; v5 rows carry `resp`, `exposure` and `owner` |
| `test_roster.py` | EV-08 | the scaled roster equals today's at 150 agents and gives 7 bots, 3 hires and 40 people at 50; shares from 3 to 800 agents; churn averages its yearly rate, leavers and joiners are valid and absent outside their days; bot gray kinds follow the role and do not move a bot's ordinary rows |
| `test_gray_variants.py` | EV-09, EV-09b, EV-08 | plain episodes keep the person's hours, /16, client and session opening (unit and whole world); classic ones keep their giveaways; plain cross-copy writes in a later session; every v5 organisation has public repositories; the toxic flow's classic and plain shapes; the bot kinds' two variants |

The v4 pin was recorded from the pre-v5 `normal_org_world.py` restored from the pre-v5 backup
into a scratch folder. It must never be re-recorded: the v4 world is frozen.

## Other tests in this folder

- `test_heldout_*.py`: the held-out harness (seed derivation, world specs, provenance,
  selection, metrics, combiners, outside baselines).
- `test_gharchive.py`: the GH Archive extractors (request sizes, per-actor cadence).

## Running

```bash
uv run pytest tests/dynamic_dimensions -q
```

The determinism and v4 tests start fresh interpreters and take about 30 seconds together.

## References

- `reports/experiments/dynamic_dimensions/knowledge_base/v5-design-spec.md`, section 4.5
- `reports/experiments/dynamic_dimensions/knowledge_base/v5-implementation-plan.md`, Batch 1
