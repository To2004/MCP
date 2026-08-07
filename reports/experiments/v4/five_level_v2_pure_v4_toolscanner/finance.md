# Three-way tool impact — finance (196 tools)

Three independent methods over the same catalogs:

| | method | signal it reads |
|---|---|---|
| **A** | LLM | the model reads the tool JSON and answers the ladder |
| **B** | static | tiered verb patterns over name + description prose |
| **C** | atomic | name tokenised to verb+object, mapped to an operation taxonomy, tier = max |

They share no pattern table, so agreement is corroboration rather than a shared blind spot.

## Pairwise agreement

| pair | exact | of | % | within ±1 |
|---|--:|--:|--:|--:|
| static vs atomic | 168 | 196 | 86% | 98% |

## Consensus

{'agreed': 168, 'split (2 methods)': 28}

## Where the methods disagree

| server | tool | LLM | static | atomic | max op | atomic ops |
|---|---|:--:|:--:|:--:|---|---|
| maverick | `check_signals_now` | — | 3 | 5 | `EXECUTE` | EXECUTE |
| maverick | `data_get_stock_info` | — | 3 | 2 | `METADATA` | METADATA |
| maverick | `discover_capabilities` | — | 1 | 2 | `LIST` | LIST |
| maverick | `generate_backtest_charts` | — | 4 | 3 | `READ` | READ |
| maverick | `generate_optimization_charts` | — | 4 | 3 | `READ` | READ |
| maverick | `get_health_history` | — | 1 | 3 | `READ` | NO_EFFECT, READ |
| maverick | `get_portfolio_risk_dashboard` | — | 2 | 3 | `READ` | READ |
| maverick | `get_regime_adjusted_sizing` | — | 3 | 4 | `MODIFY` | MODIFY |
| maverick | `get_stock_info` | — | 3 | 2 | `METADATA` | METADATA |
| maverick | `journal_list_trades` | — | 3 | 2 | `LIST` | LIST |
| maverick | `list_all_strategies` | — | 3 | 2 | `LIST` | LIST |
| maverick | `list_signals` | — | 3 | 2 | `LIST` | LIST |
| maverick | `list_strategies` | — | 3 | 2 | `LIST` | LIST |
| maverick | `optimize_strategy` | — | 3 | 4 | `CONFIGURE` | CONFIGURE |
| maverick | `performance_clear_system_caches` | — | 4 | 5 | `DELETE` | DELETE |
| maverick | `performance_get_redis_health_status` | — | 1 | 2 | `METADATA` | METADATA, NO_EFFECT |
| maverick | `performance_optimize_cache_configuration` | — | 3 | 4 | `CONFIGURE` | CONFIGURE |
| maverick | `portfolio_risk_adjusted_analysis` | — | 3 | 4 | `MODIFY` | MODIFY, READ |
| maverick | `risk_adjusted_analysis` | — | 3 | 4 | `MODIFY` | MODIFY, READ |
| maverick | `run_health_diagnostics` | — | 1 | 3 | `READ` | NO_EFFECT, READ |
| maverick | `watchlist_brief` | — | 2 | 3 | `READ` | READ |
| openbb | `derivatives_options_surface` | — | 3 | 4 | `WRITE` | SEARCH, WRITE |
| openbb | `equity_profile` | — | 3 | 2 | `METADATA` | METADATA |
| sec_edgar | `discover_company_metrics` | — | 3 | 2 | `LIST` | LIST |
| sec_edgar | `get_company_info` | — | 3 | 2 | `METADATA` | METADATA |
| yahoo_finance | `get_holder_info` | — | 3 | 2 | `METADATA` | METADATA |
| yahoo_finance | `get_option_expiration_dates` | — | 2 | 3 | `READ` | READ |
| yahoo_finance | `get_stock_info` | — | 3 | 2 | `METADATA` | METADATA |

28 of 196 tools have a disagreement (14%).

## Atomic operation census

| operation | tools | tier |
|---|--:|--:|
| `READ` | 141 | 3 |
| `METADATA` | 15 | 2 |
| `LIST` | 11 | 2 |
| `CREATE` | 8 | 4 |
| `DELETE` | 8 | 5 |
| `NO_EFFECT` | 6 | 1 |
| `MODIFY` | 6 | 4 |
| `SEARCH` | 4 | 3 |
| `CONFIGURE` | 2 | 4 |
| `BUILD` | 1 | 4 |
| `EXECUTE` | 1 | 5 |
| `WRITE` | 1 | 4 |
