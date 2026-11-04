# Dynamic dimensions experiment

Which runtime dimensions (time, volume, repetition, reach, breadth, order, size, dormancy) should the dynamic layer use? Should each be compared with the caller itself, its peers, or the whole org? And how does that hold up over one month, one year and two years? Scope is strange usage of the server's own tools by legitimate callers, not attacks. Server responses are not used.

## Start here

- [DIMENSION_FORMULAS.md](DIMENSION_FORMULAS.md): **the current design (v4),** run by default by `src/mcp_security/behaviour/engine.py`. The earlier versions are saved as [DIMENSION_FORMULAS_v1.md](DIMENSION_FORMULAS_v1.md), [DIMENSION_FORMULAS_v2.md](DIMENSION_FORMULAS_v2.md) and [DIMENSION_FORMULAS_v3.md](DIMENSION_FORMULAS_v3.md); the engine still runs them with `"design": "v1"`, `"v2"` or `"v3"`. The exact formula for each of the 15 dimensions and flags in three groups: Typical Cadence, Typical Footprint and Red Flags (v3's "Policy", briefly "Expected Conduct"; v4 moved every "new for him" check into Typical Footprint), with a short paper name for each and its engine key. Also: why each one matters, the missing handshake case by case, `s1`/`s2` and the full formula, why the max, and the planned ablation study. How to write it in the paper: [`paper_v5/DYNAMIC-LAYER-V4-NOTES.md`](../../../paper_v5/DYNAMIC-LAYER-V4-NOTES.md). Each gives a score from 0 to 1 using only fractions and averages, with no bits. The strangest dimension sets a multiplier from 0.7 to 5: ordinary calls stay at or below 1. Static × dynamic stays between 0.7 and 25. Checked on five simulated organisations of mostly ordinary traffic (`normal_org_sim.py`).
- [FORMULA.md](FORMULA.md): the short version for reviewers and clients: three questions (Pace, Path, Place), the `e` formula that joins them, and what a deployment needs.
- [SCENARIOS.md](SCENARIOS.md): the formula run on 15 concrete scenarios by a reference engine, where it breaks, and two new ideas that fix the breaks (crowd: one agent or everyone; settling: changed or misbehaving).
- [SUMMARY.md](SUMMARY.md): one-page summary of everything: results, the recommended set, what to add or remove, what the high level cannot see, identity, log and scale.
- [REPORT.md](REPORT.md): the big summary. Which dimensions, how well they work, how to run them for 10,000 agents, who sent the call, and what the log needs.
- [HIGH_LEVEL.md](HIGH_LEVEL.md): the dimensions that work **without looking inside any call** (tool, operation, asset type, time, volume, general client/network): the recommended set, specialists, what to remove and what the high level cannot see.
- [DIMENSIONS_GUIDE.md](DIMENSIONS_GUIDE.md): every dimension with a concrete scenario, its legitimate look-alike, its log fields and its cost.

## Files

| File | What it does |
|---|---|
| `world.py` | Builds a two-year synthetic GitHub-MCP organisation grounded in the repo's real live calls: roles, tool mixes, argument templates, static impact and sensitivity. It injects 12 kinds of labelled strange usage and 7 kinds of labelled legitimate change. |
| `detectors.py` | Scores every call on 13 dimensions × references (self, peer, org, self→peer hierarchy, anchored) × window (30 d, 90 d, lifetime). Each call is scored first and only then added to history. |
| `evaluate.py` | Sets alert thresholds without labels, from the previous 30 days at a fixed alert budget with a daily cap. It reports episode detection per kind and false alarms per kind of legitimate change, for month 1, year 1 and year 2. It also compares the three candidate plans. |
| `plans.py` | Compares the three candidate plans at **equal analyst load** (alerted caller-days per day). Covers month 1 and month 2 of a new deployment, year 1 and year 2. |
| `drift.py` | Slow drift: each caller's weekly out-of-team share, measured against a frozen, a re-anchored or a rolling baseline. |
| `focus.py` | Which topic to focus on: volume over short time, what is touched vs peers, or order and time. Each topic alone and in pairs, at equal analyst load, with no policy rules. |
| `learned.py` | Option 3 test: one learned model over generic call tokens (tool, opaque asset handle, size bucket, tool-to-tool step), scored per caller-day. |
| `hybrid.py` | Static-guided dimensions plus the learned model, sharing one analyst load. |
| `new_dims.py` | Tests four dimensions taken from the Dynamic Context Catalog deck: assets per session vs the policy's "one at a time", consequence added up over a day, weekly write share, and the share of calls on unregistered assets. |
| `focus_select.py` | Greedy forward selection of the dimension pool at a fixed analyst load: pick on one world, check on the other. |
| `wire_dims.py` | Dimensions the gateway-log/2 wire log makes possible (argument keys, session length, sessions per hour), added to the five focus dimensions. |
| `world2.py` | Multi-server worlds (GitHub, Calendar, Slack) grounded in real calls and the static scan's input effects. Agents carry gateway-log/2 wire fields. 21 kinds of strange usage at 3 intensities. |
| `dims2.py`, `dims3.py` | The 60-dimension pool: 43 designed + 17 from the published feature catalog. All are request-side and use static effect labels. Peers are learned, not taken from roles. |
| `eval2.py`, `report2.py` | Per-scenario prep, each dimension alone, greedy selection inside each scenario and across all nine. Writes `results/dimension_search.md`. |
| `w2/run_all.sh` | Runs the whole pipeline (worlds → both feature batches → prep → selection). |
| `ablation.py` | Which log fields matter: reruns the cross-scenario selection with only the dimensions each field set allows. |
| `identity_variants.py`, `identity_eval.py`, `w2/run_identity.sh` | Identity test: the same traffic seen as one token per person, one token shared by 10 people, or session-only identity. |
| `engine_scale.py` | Cost test: a lean engine for the core set run with 10,000 agents (throughput, latency, memory, weekly peers). |
| `dims4.py`, `dims5.py`, `dims6.py`, `high_level_eval.py`, `w2/run_high_level.sh` | High-level dimensions (no call content) and their evaluation; see HIGH_LEVEL.md. |
| `dynamic_engine.py`, `scenarios.py`, `idea_eval.py` | A reference engine for the formula with the two new ideas; 15 scripted scenarios on a simulated GitHub organisation; both ideas on the 9 organisations. See SCENARIOS.md. |
| `self_only_dims.py`, `self_only_eval.py` | Self-only dimensions (no user id, no comparison with other users) and identity variants. |
| `vkp_extra_dims.py`, `vkp_eval.py`, `vkp_greedy.py`, `vkp_engine.py`, `vkp_scenarios.py` | The Velocity / Knowledge / Place baseline: every proposed dimension alone and drop-one, the smallest set, average vs max inside a family, and the scenarios. |
| `family_formula.py` | The three families (Pace, Path, Place) and the `e` formula: four ways to turn surprise into a signal × four ways to join the families; see FORMULA.md. |
| `formula_compare.py`, `formula_test.py`, `formula_test2.py` | Earlier tests of how to combine the dimensions into one score: strongest signal vs adding vs multiplying, at equal analyst load. |
| `normal_org_world.py`, `normal_org_engines.py`, `normal_org_sim.py` | A **mostly-ordinary** GitHub organisation (real tools and static levels; 150 agents, 180 days; ordinary life changes, three org-wide changes, rare gray episodes, no attacks). It is run through the shipped engine (`src/mcp_security/behaviour/engine.py`), the documented v2, and v2 with each proposed fix, with the doc's limits and with limits learned by `policy.py`. The switch-free variant is first checked to give the shipped engine's multiplier on every message. It also tests the detectors the misses called for: assets, writes and repeated calls per hour; a first look at a sensitive asset; a weekend fallback; per-tool size limits. Results: `results/normal_org_sim.md`, plus `results/normal_org_sim_seed11.md` (a second organisation, key engines). The **v3 candidate** (same call in 10 minutes and writes per hour in Typical Cadence, distinct assets per hour as a count or a rule, a first look at a sensitive asset as a Policy rule, per-tool size limits, daily updates, 14-day onboarding, weekends blended with all days) is in the same files. The "more git" organisations (`--profile heavy_files` / `more_pastes`, 60 and 300 agents) check the per-tool size limits: `results/normal_org_git_*.md`. The second round (`v3 final, …` engines) tests distinct assets per hour as a count with the rule as a backstop, the first-look rule graded by asset sensitivity and by the tool's level, a warm-up of one day (with the rules that need no history still on), and size limits learned per agent-day; **`v3 (decided)`** is the engine written into DIMENSION_FORMULAS_v3.md; **`v4`** is DIMENSION_FORMULAS.md (v4), with its two partial switches (`v3 (decided), network and app in Footprint`, `v3 (decided), new tool through tool rarity`); `--check-port` checks the shipped v3 and v4 against the simulation on every message. Run: `uv run python normal_org_sim.py` (about 10 minutes on 8 cores); `--only "<engine>|<engine>"` scores some engines and merges them into the saved results. |
| `human_study/` | **Bot Day Check**, the human evaluation of the dynamic layer: a 30-minute web survey for 10-20 people (many non-technical). They judge 16 v4-scored agent-days from the main organisation against each agent's own usual days, never seeing the score, plus 8 pairs from the same day. Includes the item builder, the private key, the web page, the answer collector, the analysis and 5 Claude runs. See [human_study/README.md](human_study/README.md). |
| `results/` | `results_seed{1,2}.md` (per-dimension experiments), `plans.md`, `drift.txt`, `focus.md` (combined by strongest signal), `focus_accumulated.md` (combined by adding risk per caller-day), `visibility.md` (reading nothing vs static-kept inputs), `learned.md`, `hybrid.md`, `new_dims.md`, `select_pick*_v2.md`, `logging_essence.md` (what logs contain and what analytics use, across non-MCP domains). |

## Reproduce

```bash
python world.py --days 730 --seed 1 --out world_seed1.csv.gz
for w in 30 90 life; do
  python detectors.py --world world_seed1.csv.gz --window $w \
    --out ../../../runs/dynamic_dimensions/scores_s1_w$w.npz
done
python evaluate.py --scores-dir ../../../runs/dynamic_dimensions --seed 1
# dense 75-day worlds for the first-month (cold start) test
python world.py --days 75 --seed 11 --per-kind 8 --out world_month_seed11.csv.gz
python detectors.py --world world_month_seed11.csv.gz --window 90 \
  --out ../../../runs/dynamic_dimensions/scores_s11_w90.npz
python plans.py --scores-dir ../../../runs/dynamic_dimensions --seeds 1 2 --month-seeds 11 12
python drift.py world_seed1.csv.gz world_seed2.csv.gz
```

The score files (`runs/`, gitignored) are large. The world CSVs are kept here because they double as a synthetic call corpus.

## Honest limits

- The traffic is synthetic. Benign behaviour is grounded in real calls, but timing, org change and strange usage are our own design. A dimension that matches how we wrote a kind of strange usage will look good by construction. Read the results as which dimension can see which kind, at what false-alarm cost, not as production detection rates.
- Roles, teams and caller ids come from the generator. On the wire they need caller identity, which the gateway does not capture yet.
