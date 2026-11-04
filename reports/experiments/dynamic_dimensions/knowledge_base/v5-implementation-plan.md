# Dynamic layer v5: implementation plan

This plan builds the changes in [v5-design-spec.md](v5-design-spec.md) (revision 2) in dependency
order. Each batch lists its implementers and the files each one owns. No file appears twice in
one batch, so implementers can work in parallel. Change ids and switch names are the spec's
(section 4). An external-evidence track (X1-X3) runs beside the batches from the start.

## Core scope (decided 2026-10-26)

The author chose D1 = (a), D2 = (a), D3 = (a) and D4 = (a), and a **paper core first** build
(spec §8). Read volume is therefore the 16th dimension. Cadence shares are 1/21 each, Footprint
and Red Flags 1/12 each, and M is in [1, 5].

The rows below are **deferred** until after submission. Every other row in this plan is in scope.

| Batch | Deferred | What stays in scope instead |
|---|---|---|
| 0 | `scorer_tier` and `state_store` config fields | the existing `state_path` / `state_every` |
| 1 | I12's SQLite `StateStore`; DEP-4 log rotation; RF4's versioned re-learn (I3) | I12: a JSON snapshot at the route rollover plus log-tail replay through `RouteScorer`, which gives live = offline after a restart |
| 1 | AI-13's token index and memo (I8) | the exact-id dict and the unique-match rule for floors |
| 2 | J8 scorer tier (DEP-1, DEP-2) | none; inline single-instance scoring (T9) |
| 3 | K2's 2- and 4-shard arms; K4's replica, 10^5-register and migration rows | K2 single instance; K4 save/restore at 10^3 and 10^4, kill -9, flood, sessions, latency |
| 4 | L1's shard checks | everything else in L1 |

## Identity per agent and SDK 2.x (decided 2026-10-27, spec §8 D5)

The author's deployments have no user ids, at most an agent id. History is therefore kept per
agent.

- **Done 2026-10-27 (before the Batch 1 fixers):**
  - The v5 default `baseline_key` is `"agent"`. It keys a signed-in caller by `Identity.id`, and
    a caller without sign-in by `oauth.reported_key(clientInfo, address)`, the client family
    plus the IP address (IPv6 /64).
  - `"user"` stays an opt-in.
  - `allow_anonymous_v5` and the DEP-8 refusal are removed.
  - `with_v5_facts` folds logical calls under `Exchange.baseline_key` when it is set.
- **J3/J4 (Batch 2) wire it:**
  - Compute `baseline_caller(baseline_mode(route, design), identity.key, identity.baseline_key,
    reported)`. `reported` is given only when the request carries no sign-in, from the request's
    clientInfo (`_meta` on 2026-07-28, the session's `initialize` before) and the client address
    after the trusted-proxy rule.
  - Set `Exchange.baseline_key`, and log it with the identity strength.
  - Offline, `score.py` rebuilds the same key from `gateway.client` and `client.address`.
- **SDK:** the repo moves to `mcp>=2.3,<3`. The demo and replay scripts get
  `--protocol legacy|modern`.

## Rules for every batch

- **Decide D1-D4 first.** Done on 2026-10-26; see the core scope above. The spec's §8 decisions set the dimension count, the shares, Table 1
  and the schedule. D1 in particular must be settled before Batch 0 (R4-12).
- **Two golden pins.**
  - INF-1 records the v1-v4 engine verdict streams on a seeded fixture, before any edit. The
    fixture includes sessionless calls and duplicate first uses.
  - INF-3 records a v4 gateway log re-scored through `score.py` as a pinned CSV.
  - A batch is done only when both pins hold, `uv run pytest` passes and `uv run ruff check .` is
    clean. Re-baselining INF-3 needs a changelog entry naming E9, AI-3 or PS7.
- **v1-v4 stay bit-identical.**
  - E1, E2 and RF9 run only under `legacy_fixes`, which defaults to False for v1-v4.
  - `config_to_json` emits only the fields for `config.design` (INF-4), so v4 policy JSON and its
    digests do not move.
- **Interfaces before bodies** (R3-15). Batch 0 adds every new interface, with inert defaults:
  - every `BehaviourConfig`, `Message` and `Verdict` field;
  - every gateway `Upstream` and `OAuthConfig` field, the `Exchange` fields and the log field
    names;
  - the `RouteScorer` constructor (pseudonymizer, ledger) with `reply`, `score_read` and `commit`
    stubs;
  - the engine's `score` / `commit` split. In v1-v4, `observe` stays exactly score plus commit.
- **Exclusive files.** An implementer edits only the files in its row and codes against the
  Batch 0 interfaces of the others.
- **New folders** get a `README.md`: `tests/binding/`, `tests/dynamic_dimensions/`,
  `reports/experiments/dynamic_dimensions/heldout/` and `catalogs/`.
- **Design-phase files stay read-only until Batch 4:** `DIMENSION_FORMULAS*.md`, `paper_v5/` and
  `docs/`. The exception is Batch 0's copy of `DIMENSION_FORMULAS.md` to `DIMENSION_FORMULAS_v4.md`.
- **No v5 mirror.** `normal_org_engines.py` stays v4-only (spec, conflict 18).

## Batch overview

| Batch | Goal | Implementers | Depends on | Exit check |
|---|---|---|---|---|
| 0 | Interfaces, golden pins, legacy fixes | 1 (serial) | D1-D4 | INF-1, INF-3 green; `design="v5"` runs and equals v4 with every v5 switch off |
| 1 | New modules and leaf files | 12 in parallel | 0 | unit tests of every new module; `calibration.py` equals the O3 probe arm on a fixed array |
| 2 | Engine inputs; gateway wiring; scorer tier; simulator harness | 7 in parallel | 1 | v5 gets every input; the gateway passes them; 1-, 2- and 4-shard scores are equal |
| 3 | Calibration, floors and red flags in the engine; replay; adaptive kinds | 5 in parallel | 2 | v5 verdicts carry rates, floors, records and surge notices |
| 4 | Verification, the probe re-run on the v5 engine, docs | 3 in parallel | 3 | property tests; live = offline including restart; docs synced |
| 5 | Development selection, freeze, preregistration | 1 (serial) | 4 | `dyn-v5-frozen` tag; preregistration deposited before any calibration world |
| 6 | Held-out runs, X1-X3 scoring, analysis | 2 | 5 | every table, side by side across pools |
| 7 | Paper | 1-2 | 6 | §3, §4.3, §5 drafted within the spec's §7 budget |

## Batch 0: interfaces and pins (serial)

One implementer, `core`. Commits go in this order.

| Step | Change | Files: functions |
|---|---|---|
| 0.1 | INF-1 engine golden, with sessionless and duplicate-first-use fixtures | tests/behaviour/test_golden_designs.py (new), tests/behaviour/golden/ (new, with README) |
| 0.2 | INF-3 gateway golden | tests/gateway/test_golden_gateway.py (new), tests/gateway/golden/ (new, with README) |
| 0.3 | V5 design flags | `engine.py`: `V5` in `DESIGNS` (81); `BehaviourEngine.__init__` (270-279) |
| 0.4 | Every v5 config field, including `legacy_fixes`; design defaults resolved in `__post_init__` | `engine.py:BehaviourConfig` (111-147) |
| 0.5 | Message fields: `era`, `app`, `client_family`, `zone`, `more_assets`, `exposure`, `static`, `arg_bytes`, `logical_call`, `outcome`. No `role`: B4 is deferred. Verdict fields: `alert`, `runner_up`, `runner_up_dimension`, `floors`, `rate`, `rates`, `runner_up_rate`, `records`, `notes`. | `engine.py:Message` (151-164), `Verdict` (168-181) |
| 0.6 | Engine `score` / `commit` split (v1-v4: `observe` = score + commit, unchanged); PS6; EV-21; EV-03 trace hook | `engine.py:observe` (281-299), `multiplier` (184-188) |
| 0.7 | E1, E2, RF9 behind `legacy_fixes` | `engine.py:_problematic_sequence` (574), `_call` (379-380); `memory.py:FirstUses.others` (231-238) |
| 0.8 | INF-4 design-scoped policy JSON | `policy.py:config_to_json`, `config_from_json` (137-150) |
| 0.9 | Gateway interfaces: `Upstream` / `OAuthConfig` fields (`baseline_key`, `user_claim`, `zone_claim`, `zone_map`, `route_zone`, `shared_egress`, `fail_closed_unparsed`, `upstream_audit_header`, `allow_anonymous_v5`, `state_store`, `scorer_tier`); `Exchange` fields; LOG-1 field and line names; the `RouteScorer` constructor and stubs | `gateway/config.py` (66-104), `gateway/wire_log.py` (Exchange), `gateway/framework.py` (`RouteScorer.__init__`) |
| 0.10 | B9 clock module (pure functions) | behaviour/clock.py (new), tests/behaviour/test_clock.py (new) |
| 0.11 | Keep the v4 doc | copy `DIMENSION_FORMULAS.md` to `DIMENSION_FORMULAS_v4.md` |

## Batch 1: new modules and leaf files (parallel)

| Implementer | Changes | Files owned (exclusive) | Tests |
|---|---|---|---|
| I1 calibration | CAL-1 `DayRings`; CAL-2 `RecordReference` (rank among all route agent-days, cap condition, path activity); CAL-3 `combine` with the watch-only cap; CAL-4 `apply_floors` with floor budgets and route warm-up; CAL-6 `SurgeGuard`; CAL-7 `RouteClock` with the open-day buffer and fold sweep; `alert_line(alpha)`; HOLD, TOP, EST, GWR variants; FP-1 | behaviour/calibration.py (new) | tests/behaviour/test_calibration.py: equals `probes/org_record_rank_probe.py` arm O3 on a fixed array; a dormant caller's last day enters the reference; the min and the surge guard never lower q |
| I2 memory | B5; B7 `SlotQuantile`; value-day counts as count-of-counts with the value cap and overflow (DEP-7); AI-8 `SlidingTotal`; RF7 `OrgFirstSeen` and the established flag | behaviour/memory.py | tests/behaviour/test_memory.py: a never-used value is strangest; a 10^5-value flood stays bounded |
| I3 policy | RF1 on argument bytes; RF2; RF4 offline re-learn to a versioned file; E5 window learner; AI-6; CLI `--design v5`; agent-days by baseline key and local day; reads daily extracts | behaviour/policy.py | test_policy.py: v4 golden JSON; binomial band; one inflated identity |
| I4 sequence and protocol | E4 `own_session`; E5, SEQ-1, SEQ-2 and the E14 hook in `unsafe_sequence`; E6 (legacy, watch-only) and E8 in `handshake` | behaviour/own_session.py, unsafe_sequence.py, handshake.py (all new) | test_own_session.py, test_unsafe_sequence.py (pair keys; a new pair is a record; repeats are habit), test_handshake.py |
| I5 rates | RF5 `FlagRates`: `nominal_rate`, Wilson bounds, floor demotion counting only established callers, path-activity report, per-era base rates, `flag_surge` | behaviour/flag_rates.py (new) | test_flag_rates.py: Sybils cannot force a demotion |
| I6 gateway wire | E3, E7; E9 and DEP-5 SessionBook (TTL, cap); B3; ARG-1 era-free sizes, logical-call key and outcome; GW-1; RPL-1 | gateway/protocol_era.py (new), gateway/wire_log.py, gateway/http_wire.py | test_protocol_era.py, test_wire_log.py (10^6 sessions bounded), test_http_wire.py (50 MB reply linear) |
| I7 gateway identity and config | B1; B2 client pair; B9d zone map; B10 per-platform egress table; PS7 `legacy_gate`; PS9, PS10; DEP-8 | gateway/oauth.py, gateway/config.py, gateway/routes.example.json | test_oauth.py: two client_ids give one user |
| I8 binding | AI-1, AI-2, AI-13 (exact dict, token index, memo, unique match for floors), EXP-1, AI-7, AI-12, AI-3 | binding/touched_asset.py (new), binding/scoring.py, binding/__init__.py | tests/binding/: a 10^5-id register for time and ambiguity; decoy path |
| I9 world, part 1 | EV-01, EV-06, EV-07, EV-08 with churn, EV-09 and EV-09b (public repositories, toxic-flow kind) | normal_org_world.py | tests/dynamic_dimensions/: determinism, calendar, sizes, roster, churn |
| I10 harness | EV-15 `derive_seed` with a beacon; EV-02; EV-16 `select_v5` (spec §6.2); `heldout_metrics.py` (pAUC, local-day key, per-dimension spend with Holm, tenure bands, 30-day periods, transfer ratio, PPV); EV-20 with Footprint as a rank; EV-22; world-only bootstrap | heldout_world_spec.py, heldout_provenance.py, select_v5.py, heldout_metrics.py, combiner_family.py, outside_baselines.py (all new) | their tests |
| I11 GH Archive | EV-26 sizes; X2 per-actor cadence extraction (pseudonymised, aggregates only) | gharchive_request_sizes.py, gharchive_actor_cadence.py, scripts/dynamic_design/gharchive_array.sbatch (all new, CPU-only) | their tests |
| I12 state and logs | DEP-3 `StateStore` (SQLite, incremental, off-loop) and snapshot plus log-tail replay; DEP-4 daily log rotation with the chain carried across files, and a streaming reader | behaviour/state_store.py (new), gateway/state_replay.py (new), gateway/log_file.py | kill -9 replay equals a clean run; the chain verifies across files |

## Batch 2: engine inputs, wiring, scorer tier (parallel)

| Implementer | Changes | Files owned (exclusive) | Tests |
|---|---|---|---|
| J1 engine inputs | E4, E11/B2, E12, B5, B7, B9, the RF7 branch (551-556), AI-7, AI-8 `reply`, AI-10, AI-12; DEP-7 Burst ring and scoring budget (`unscored`); v5 score / commit; snapshot and restore of the new state; v5 refuses non-v5 snapshots (DEP-6) | behaviour/engine.py | test_engine_designs.py: each switch at its off value equals core minus that part |
| J3 gateway scorer | INF-2 with every engine input; AI-2p; AI-7 labels; B1/B2; E3 era; E14 ledger argument; PS7; `RouteScorer.reply`, `score_read`, `commit`; DEP-8; replay of `behaviour_fold` and `policy_switched`; the migration bootstrap `score.py --design v5 --save-state`; the review list | gateway/framework.py, gateway/score.py | test_framework.py, test_score.py: a `log_bodies = none` route replays equal |
| J4 gateway proxy and viewers | ARG-1: score before forward, commit after the reply; AI-8 `_answered`; AI-10; E14 ledger creation; DEP-3 store wiring and replay on start; DEP-4 policy switch at rollover; PS7 viewers | gateway/proxy.py, gateway/log_text.py, gateway/log_view.py, gateway/log_grouped.py | test_gateway.py: a 400 response is scored but not committed |
| J8 scorer tier | DEP-1 background consumer sharded by baseline key; DEP-2 daily extracts and digest-pinned references | gateway/scorer_tier.py (new) | test_scorer_tier.py: 1, 2 and 4 shards give equal verdicts |
| J5 simulator harness | EV-02; EV-04 gateway-inputs mode; EV-03 score-log runner; EV-31 route warm-up stratum | normal_org_sim.py, heldout_run_world.py (new) | test_gateway_inputs.py, test_provenance.py, test_trace.py |
| J6 world, part 2 | EV-10 eras, with MRTR continuations and fallback probes rendered for replay; EV-11; EV-12 Slack catalog and the W7 two-route world (must); EV-13; EV-14 hook | normal_org_world.py, catalogs/ (new) | test_era_worlds.py, test_two_route.py |
| J7 GH Archive analysis | Hyp5 statistic; X2 checks (record rate against 1/(A+1), per-dimension spend by weekday class) | gharchive_request_sizes.py, gharchive_actor_cadence.py | their tests |

## Batch 3: calibration, floors and red flags; replay; adaptive kinds (parallel)

| Implementer | Changes | Files owned (exclusive) | Tests |
|---|---|---|---|
| K1 engine verdict | Calibration stage after the scores dict (CAL-1..CAL-7) with the route reference folded on the route clock; `_first_look` (489-502) moved out of the Asset score (429-431) into floors; SEQ-1/SEQ-2 and handshake hookups; RF1/RF2 lookups returning rho; PS8; FP-1; RF5 feed; v5 Verdict fields | behaviour/engine.py | test_engine_designs.py: the spec's §2.5 table; watch-only terms never reach the 1% line; the cap condition |
| K2 gateway replay | EV-05: 5 worlds per family through `RouteScorer`, including MRTR, fallback and mixed-era wire; scorer tier at 2 and 4 shards | gateway_replay_world.py (new) | replay equals the oracle on registered repositories |
| K3 adaptive kinds | EV-25 (must): the nine kinds plus ramps for each record dimension, a distinct-value flood, floor demotion by Sybils, surge cover and a two-hop toxic flow; free-envelope overlay | adaptive_gray_kinds.py (new) | test_adaptive_gray_kinds.py |
| K4 SLURM and overhead | EV-17 array (CPU-only, 3 CPUs, 16 GB, 1 h, `%200`); EV-27 required rows (save and restore at 10^3 and 10^4, kill -9, 10^5 register, flood, replicas, migration, sessions, latency) | scripts/dynamic_design/heldout_array.sbatch (new), scripts/dynamic_design/measure_gateway_overhead.py (new) | dry run on 1 world |
| K5 era swap | E13 on rendered wire messages | era_swap.py (new) | test_era_swap.py |

## Batch 4: verification, probe re-run, docs (parallel)

| Implementer | Changes | Files owned (exclusive) |
|---|---|---|
| L1 tests | E13 era invariance through `RouteScorer`; INF-1 and INF-3 re-run; live = offline, including restart replay and kill -9; the guarantee unit test on synthetic exchangeable streams (realised ≤ α + β); the dormant-caller fold; 10^6 sessions | tests/behaviour/test_era_invariance.py, tests/behaviour/test_guarantee.py, tests/gateway/test_live_offline.py (all new) |
| L2 probe re-run | Re-run `org_record_rank_probe.py` and the evaluator on score logs from the **v5 engine** for the development worlds, before selection. Report per-dimension spend, path activity and the surge-day count. Label every output "development world". | probes/org_record_rank_probe.py (inputs only), probes/README.md |
| L3 docs | `DIMENSION_FORMULAS_v5.md` (new, from the code): the one rule, Verdict field semantics (`strongest` / `score` carry d* / s1, and `scores` holds the raw s_d) and the Red Flags sentence. Also: `DIMENSION_FORMULAS.md` points to v4 and v5; docs/project/dynamic-layer-explained.md; docs/development/commands.md; the CLAUDE.md commands table; README.md; paper_v5/DYNAMIC-LAYER-V5-NOTES.md (names table and claims ledger, first line per R4-7) | those files |

## Batch 5: development selection and freeze (serial)

1. Write `heldout/v5_candidates.json` (cfg0-cfg9) and the selection rule (spec §6.2), with δ
   computed from the development world-level SE. Record their SHA-256 before any run.
2. Hash the simulator files (R2-6).
3. Generate 5 `dev` worlds per family W2-W8 from a public salt. They are burnt from then on.
4. Run the candidates: thresholds fitted on days 90-134 (unlabelled), selection metrics on days
   135-180 of the new development worlds.
5. Freeze per spec §6.3: tag `dyn-v5-frozen`, and put the X1 scenario hashes and the X3 log
   digests into the preregistration. Deposit it **before** generating any calibration world, mix
   in the beacon, then derive the seeds. `design = "v5"` becomes the default only in that tag's
   policy files.

## Batch 6: held-out runs and analysis

- **R1 runs:**
  - the calibration pool, then the test pool, through `heldout_array.sbatch` (CPU only);
  - the gateway replay and the adaptive overlay;
  - X1's scenarios, scored once;
  - X3's sealed logs, scored once from deployment day 0;
  - X2's real-data checks.
- **R2 analysis:** score logs go to `heldout_metrics.py`, `combiner_family.py`,
  `outside_baselines.py` and the EV-21 sensitivity runs. Every table appears side by side:
  development, calibration, each family, X1, X2, X3.

## Batch 7: paper

Follow spec §7. The method must fit 1.5 columns, using the 5 new body names. Write §3, §4.3, §4.4
and §5, the threats-to-validity paragraph, and the Ethics and Open Science appendices, including
the appendix list of every configuration scored on a development world.

## External-evidence track (starts now; author actions)

| Line | Owner | Steps | Deadline if D4 = (a) |
|---|---|---|---|
| X1 independent scenarios | author | Recruit at least 2 people outside the design. Give them the episode schema and catalog, never v5 numbers. They deliver at least 30 gray and 30 benign look-alike scenarios. These are compiled and hashed before scoring. | recruited by 8 Nov; delivered by the freeze |
| X2 GH Archive per-actor cadence | I11, J7 | Extract actor-hour streams (people, `[bot]` and agent actors), pseudonymised; aggregates only | Batches 1-2 |
| X3 sealed lab shadow logs | author | Consent and ethics; run the observe-only gateway with `log_bodies = all` for 30-45 days from deployment day 0; deposit the log digests at the freeze; nobody scores them before then | consent by 8 Nov; logging from about 8 Nov |

## Schedule (if D4 = USENIX Security '27 cycle 2)

| Dates (2026-2027) | Work |
|---|---|
| 26-29 Oct | D1-D4 decided; Batch 0 |
| 30 Oct - 8 Nov | Batch 1; X1 and X3 recruited; X3 logging starts |
| 9-17 Nov | Batch 2 |
| 18-25 Nov | Batch 3 |
| 26-30 Nov | Batch 4 |
| 1-8 Dec | Batch 5 (freeze on 8 Dec) |
| 9-28 Dec | Batch 6 (X3 reaches 30 days on about 8 Dec, 45 days on about 23 Dec) |
| 29 Dec - 26 Jan | Batch 7 (registration 19 Jan, paper 26 Jan) |

Switch to D4 = (b) in either case:
- X1 or X3 is not confirmed by 8 Nov;
- the freeze slips past about 15 Dec.

The CCS 2027 and USENIX '28 dates are UNVERIFIED.

## References

- [v5-design-spec.md](v5-design-spec.md): change ids, switches, the evaluation plan and the
  Review log.
- [v5-calibration.md](v5-calibration.md): the S5 record and the engine state of revision 1.
- [probes/README.md](probes/README.md): every probe script.
- Part A JSON (`v5_part_a.json` in this session's scratchpad): files and tests for each change.
- Code line numbers as cited in the spec's references.
