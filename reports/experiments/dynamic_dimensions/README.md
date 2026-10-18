# Dynamic dimensions experiment

Which runtime dimensions (time, volume, repetition, reach, breadth, order, size, dormancy) should the dynamic layer use? Should each be compared with the caller itself, its peers, or the whole org? And how does that hold up over one month, one year and two years? Scope is strange usage of the server's own tools by legitimate callers, not attacks. Server responses are not used.

## Start here

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
