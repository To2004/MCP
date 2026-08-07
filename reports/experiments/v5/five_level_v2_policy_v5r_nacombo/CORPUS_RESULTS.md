# The filesystem / SQL / finance corpus — `nacombo` arm

The final v5r configuration (`five_level_v2_v5r_nacombo`) run over eleven servers outside the three `_real` servers the arm was developed on. Sensitivity is derived from `docs/mcp-tools/server-policies.md` alone; no org supplies a number. Prompts as run are in `scoring-prompts-AS-RUN.md` in this folder.

## Per-server results

| Group | Server | Tools | Assets | Cells | Scored | N/A | Static ladder | Mean sens | Mean blast | Mean impact | low/med/high/crit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Filesystem | `fs_fintech_fs` | 14 | 18 | 252 | 103 | 149 | 86% | 3.39 | 3.18 | 2.71 | 39/36/24/4 |
| Filesystem | `fs_medical_clinic_fs` | 14 | 16 | 224 | 86 | 138 | 86% | 3.88 | 3.14 | 2.71 | 27/37/22/0 |
| Filesystem | `fs_corp_filesystem` | 14 | 16 | 224 | 87 | 137 | 86% | 3.06 | 3.25 | 2.71 | 36/26/21/4 |
| Filesystem | `fs_law_firm_fs` | 14 | 15 | 210 | 89 | 121 | 86% | 3.40 | 2.83 | 2.71 | 33/43/13/0 |
| Filesystem | `fs_media_studio_fs` | 14 | 16 | 224 | 111 | 113 | 86% | 3.38 | 2.60 | 2.71 | 63/36/12/0 |
| SQL | `sqlite_cbg_sqlite` | 5 | 11 | 55 | 37 | 18 | 80% | 3.27 | 2.97 | 3.20 | 13/13/7/4 |
| Finance | `finance_tools` | 17 | 6 | 102 | 27 | 75 | 100% | 2.00 | 2.33 | 2.76 | 18/9/0/0 |
| Finance | `openbb` | 30 | 5 | 150 | 36 | 114 | 90% | 2.60 | 2.42 | 2.87 | 23/12/1/0 |
| Finance | `sec_edgar` | 21 | 6 | 126 | 27 | 99 | 100% | 1.83 | 2.33 | 2.67 | 24/3/0/0 |
| Finance | `yahoo_finance` | 9 | 5 | 45 | 12 | 33 | 100% | 1.60 | 2.25 | 3.00 | 9/3/0/0 |
| Finance | `maverick` | — | — | — | — | — | — | — | — | — | **not scored (see below)** |

**Totals** — 10 servers, 152 tools, 114 assets, 1612 tool x asset cells. 615 scored (38%), 997 N/A (62%). 12 critical and 100 high — 18% of scored cells.

## The finance servers behave as the over-scoring control

`sec_edgar` and `yahoo_finance` read public filings and public market data. Nothing they return is confidential, so the correct answer is that nothing reaches high or critical — and nothing does:

| Server | What it is | high | critical | Top cell |
|---|---|---:|---:|---|
| `finance_tools` | technical indicators over public quotes | 0 | 0 | 36 — `calculate` x `expression-evaluator` |
| `openbb` | public market data, plus a skill installer | 1 | 0 | 64 — `install_skill` x `server-capability-install` |
| `sec_edgar` | public SEC filings | 0 | 0 | 27 — `get_recommended_tools` x `concept-catalogs` |
| `yahoo_finance` | public market quotes | 0 | 0 | 27 — `get_historical_stock_prices` x `research-query-pattern` |

The single high cell in the whole finance group is `openbb`'s `install_skill` writing to `server-capability-install` (64). That is the right outlier to surface: a market-data server that also lets a caller install new skills is a code-introduction surface, not a data read. The static ladder abstained on it (confidence 0.35) and the LLM fallback called it an ordinary write (4) — the hand-off doing exactly what it exists for.

## Where the impact number comes from

| Source | Tools | Share |
|---|---:|---:|
| `static_ladder` | 138 | 91% |
| `llm_fallback` | 14 | 9% |

The static ladder answers 91% of the 152 tools with no model call. The LLM is consulted only where the ladder's confidence falls below `STATIC_IMPACT_MIN_CONFIDENCE` — typically a verb the ladder does not recognise (`install_skill`, `calculate`). That is the design-time cost claim for v5: most of the corpus is priced deterministically and reproducibly.

## Highest-scoring cell per server

| Server | Score | Tool x Asset | sens | blast | impact |
|---|---:|---|---:|---:|---:|
| `fs_fintech_fs` | 100 | `write_file` x `card-vault` | 5 | 5 | 4 |
| `fs_medical_clinic_fs` | 80 | `write_file` x `patient-charts` | 5 | 4 | 4 |
| `fs_corp_filesystem` | 100 | `write_file` x `security-keys` | 5 | 5 | 4 |
| `fs_law_firm_fs` | 80 | `write_file` x `matter-files` | 5 | 4 | 4 |
| `fs_media_studio_fs` | 64 | `write_file` x `unreleased-imagery` | 4 | 4 | 4 |
| `sqlite_cbg_sqlite` | 125 | `write_query` x `api_keys` | 5 | 5 | 5 |
| `finance_tools` | 36 | `calculate` x `expression-evaluator` | 4 | 3 | 3 |
| `openbb` | 64 | `install_skill` x `server-capability-install` | 4 | 4 | 4 |
| `sec_edgar` | 27 | `get_recommended_tools` x `concept-catalogs` | 3 | 3 | 3 |
| `yahoo_finance` | 27 | `get_historical_stock_prices` x `research-query-pattern` | 3 | 3 | 3 |

Every filesystem top cell is `write_file`, and every one lands on that org's most sensitive asset — card vaults, patient charts, security keys, matter files. `sqlite_cbg_sqlite` is the only 125 in the corpus: `write_query` against `api_keys` is a free-form write (impact 5) on a self-sufficient credential store (sensitivity 5) whose reach is the whole database (blast 5).

## The one failure

`maverick` (119 tools) crashed the model server on its first call. The abort is in the CUDA flash-attention kernel (`launch_fattn` -> `ggml_abort`, `llama-server terminated, signal: aborted`), not in the scanner: the kernel aborts on this prompt length with a quantised KV cache. It is being re-run by `scripts/scan_v5_bigserver.sbatch`, which is identical to `scripts/scan_v5.sbatch` except that flash attention is off and the KV cache is f16. Model, prompts and decoding parameters are unchanged, so the result stays comparable with the ten servers above.

