# Dynamic Layer v2 — Extended To 5 More Real MCP Servers

[`dynamic_layer/v2`](../v2/README.md) ran the `B × L` runtime layer against 3,000 real
calls to github/slack/calendar. This extends the same method — unmodified — to the five
no-credential finance servers already live-captured under
[`reports/scan_finance/`](../../../scan_finance/README.md): **yahoo_finance**,
**finance_tools**, **sec_edgar**, **maverick**, **openbb**. None of github, slack or
calendar are touched here; this is coverage on servers the runtime layer has never seen.

Run in full on 2026-08-14: breadth classification of all five servers on a GPU
(`scripts/scan_breadth_finance.sbatch`), then 3,000 real calls (600/server) driven
directly against each live server (`scripts/dynamic_design/make_finance_real_warmup.py`)
and scored with the unmodified `scripts/dynamic_design/dynamic_v2.py`.

## Method

**Breadth classification** is the exact same pass as v2's Step 1 — same prompt
(`dynamic_layer/v2/breadth_prompt.txt`), same model (`qwen2.5:32b`), same GPU/Ollama
harness (`scripts/scan_breadth.sbatch`'s pattern, pointed at the finance catalogs) — just
run over five catalogs it had not been run over yet. The artifacts on disk under
`reports/experiments/breadth_spec/<server>_scan.json` predated a working Ollama
connection and were 100% `unclassified`; this replaces them with a real run.

**Real calls** differ in one respect from v2's `make_real_warmup.py`: that script drives
github/slack/calendar over `npx`/stdio and hand-authors one call plan per tool, because
three servers with ~10-25 tools each is tractable by hand. The five finance servers
expose 9+17+21+119+30 = 196 tools with five different schemas, so
`make_finance_real_warmup.py` instead:

1. reuses each server's own **deterministic static scan**
   (`reports/scan_finance/<server>.json`, `primary_op` per tool — no LLM) to restrict
   itself to tools classified READ / METADATA / SEARCH / LIST. No write ever runs against
   live financial state (no portfolio mutation, no cache clear, no signal delete) —
   the same read-only discipline v2's warm-up applies by hand.
2. fills each surviving tool's declared JSON Schema **generically**: parameter names
   that carry real-world meaning (`ticker`, `period`, `days`, `limit`, `series_id`,
   `form_type`, ...) draw from a pool of real, liquid instruments and real series/form
   codes; anything else falls back to the schema's own type/enum. Values seen in real
   responses (accession numbers, option expiration dates, CIKs) are harvested
   opportunistically and reused, so the small number of parameters that need a real
   discovered identifier are not invented either.
3. launches each server exactly the way `run_mitm_finance.py` already does (same launch
   config, reused directly — `server_dir`/`module`/`attr`/`run_cmd`/`env`/`transport`) but
   without the mitmdump capture layer, since this run needs volume, not an HTTP capture.

Every call hits the real upstream: Yahoo Finance, FRED (via finance_tools), SEC EDGAR,
OpenBB's yfinance-backed routes, and maverick's local technical-analysis/screening
engine over live yfinance data. Corpora: `reports/experiments/real_benign_finance/`.

## Step 1 · The scan

| server | tools | inputs | resolved | unresolved | model seconds |
|---|---:|---:|---:|---:|---:|
| yahoo_finance | 9 | 17 | 17 | **0** | 66 |
| finance_tools | 17 | 19 | 19 | **0** | 27 |
| sec_edgar | 21 | 50 | 50 | **0** | 62 |
| openbb | 30 | 111 | 111 | **0** | 119 |
| maverick | 119 | 306 | 306 | **0** | 342 |

Every input on every tool got a model answer — same as v2's three servers, and the same
`kind`/`breadth`/`default`/`ceiling`/`source`/`why` schema, written to
`reports/experiments/breadth_spec/<server>_scan.json`.

## Step 2 · 600 real calls per server, `D = B × L`

Warm on the first 300 of each corpus, score the last 300 (v2 used a 500/500 split on a
1,000-call corpus; these corpora are 600, so the split is 300/300).

| server | real calls | ok | failed | n scored | min | p25 | median | p75 | max | <1.0 | >1.0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| yahoo_finance | 600 | 600 | 0 | 300 | 0.85 | 0.98 | **1.00** | 1.02 | 1.09 | 44% | 44% |
| finance_tools | 600 | 416 | 184 | 300 | 0.69 | 0.98 | **1.00** | 1.03 | 1.09 | 42% | 46% |
| sec_edgar | 600 | 582 | 18 | 300 | 0.77 | 0.98 | **1.00** | 1.05 | 1.13 | 47% | 43% |
| maverick | 600 | 519 | 81 | 300 | 0.90 | 0.96 | **1.00** | 1.09 | 1.28 | 42% | 39% |
| openbb | 600 | 359 | 241 | 300 | 0.81 | 0.97 | **0.99** | 1.07 | 1.16 | 51% | 40% |

**The median call scores ~1.00 on all five servers**, same shape v2 found on
github/slack/calendar: an ordinary call is worth what the scan priced, and traffic lands
on both sides of it.

The `failed` counts are real, not a driver defect: yahoo_finance's own read tools hit
Yahoo's stable JSON endpoints and never failed (600/600); finance_tools and openbb lean
heavily on scraped/free endpoints (CNBC news, sentiment feeds, holder-info pages, FRED
without a key) that throttle hard under sustained real traffic, and maverick occasionally
hits a tool that needs a paid data key it doesn't have. `BreadthScorer.observe` ignores
call status entirely (v2 already does this for github/slack/calendar) — a failed real
call still tells the runtime layer a real deployment really asked for that argument
shape, so these failures are not discarded, just never mistaken for a security signal.

### Where each quantity's verdict came from

| | yahoo_finance | finance_tools | sec_edgar | maverick | openbb |
|---|---:|---:|---:|---:|---:|
| `ordinary` (≥ Q1, no discount) | 27 | 22 | 46 | 0 | 28 |
| `no history` (< 20 observations) | 9 | 24 | 114 | 235 | 283 |
| `no floor` (no room below Q1 to be narrow) | 25 | 0 | 4 | 0 | 34 |
| `narrow` (< Q1, discounted) | 9 | 4 | 10 | 0 | 6 |

maverick's `no history` dominance (all 235 tracked quantities) is a direct consequence of
its size: 306 breadth-carrying inputs spread thin over a 300-call warm-up, so almost
nothing individually reached `MIN_HISTORY = 20` observations — the honest abstention,
not a guess, exactly as designed. yahoo_finance and openbb instead show real `no floor`
mass: several of their quantities (e.g. a `period`/`interval` argument with only a
handful of distinct real values) have no room below Q1 to demonstrate narrowness, so the
argument is excluded from `B` rather than silently pinning every call to "ordinary".

## What this does not establish

Same limits v2 already states for its own three servers, unchanged here. Every call is
benign by construction — read-only tools chosen by the deterministic scan, no
adversarial argument shaping — so nothing here shows the layer separates misuse from
ordinary use on these servers either.

`cell` is blank in every emitted row here (`cell resolved: 0` on all five runs), and this
is not a gap specific to finance: v2's own README notes the same is true of its real
github/slack/calendar corpora — `cell` needs a resolved asset and an LLM-scanned
cells/bands matrix (`mcp_security.scanner` + `param_scoring`), and none of the eight
servers now covered (three original + five finance) has both. `B` and `L` are the
runtime's whole contribution here, same as v2, and are complete.

Rubric label stability and generality claims are exactly as unmeasured as v2 already
states they are — this extension adds coverage (5 more real servers, a much larger and
more varied tool surface, three different transports/launch mechanisms), not a new
validation axis.

## Files

| file | contents |
|---|---|
| `../../breadth_spec/<server>_scan.json` | per-input `kind`, `breadth`, `default`, `ceiling`, `source`, `why` (shared location with v2's own three servers) |
| `../../real_benign_finance/<org>_real.csv` | the raw real-call corpus, one row per call |
| `scored_<server>.csv` | one row per scored call: `D` = `B × L`, and each quantity's own discount, weight and source |

## Reproduce

```bash
sbatch scripts/scan_breadth_finance.sbatch          # classify all 5 catalogs (GPU, ~17 min)

uv run python scripts/dynamic_design/make_finance_real_warmup.py \
    --server all --n 600 --pace 0.15                # ~3,000 real calls, ~80 min total
                                                      # (yahoo_finance/sec_edgar/maverick are
                                                      # fast; finance_tools/openbb are slower —
                                                      # real upstream throttling)

uv run python scripts/dynamic_design/dynamic_v2.py \
    --corpus reports/experiments/real_benign_finance/yahoo_finance_kestrel_real.csv \
    --split 0.5 --emit reports/experiments/dynamic_layer/v2_finance/scored_yahoo_finance.csv
# ... and once more per server (org codenames: finance_tools_orbit, sec_edgar_ledger,
# maverick_talon, openbb_atlas)
```
