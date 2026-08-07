# Static tool impact — finance MCP servers (no LLM)

196 tools across 5 servers, classified by
`src/mcp_security/static_scoring/static_impact.py` from each tool's own
declaration only — name, description, parameters, annotation hints.
**No model call.** Regenerate with
`uv run python scripts/static_impact_report.py --group finance`.

Ladder: **1** no effect · **2** metadata · **3** content read ·
**4** reversible write · **5** irreversible.

⚠ marks a tier reached with **no verb evidence** — a default, not a finding.

## Summary

| Server | Tools | t1 | t2 | t3 | t4 | t5 | state-changing | no verb evidence |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `finance_tools` | 17 | 1 | 0 | 16 | 0 | 0 | **0** | — |
| `maverick` | 119 | 6 | 11 | 81 | 14 | 7 | **21** | 1 |
| `openbb` | 30 | 0 | 2 | 27 | 1 | 0 | **1** | 2 |
| `sec_edgar` | 21 | 0 | 1 | 20 | 0 | 0 | **0** | — |
| `yahoo_finance` | 9 | 0 | 1 | 8 | 0 | 0 | **0** | — |

Corpus: {1: 7, 2: 15, 3: 152, 4: 15, 5: 7} — 22/196 state-changing (11%).

## Per-server detail

### `finance_tools` — 17 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `analyze_fng_trend` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | — |
| `calculate` | **3** | tier-3 verbs: \bcalculate\b | raw-query |
| `cnbc_news_feed` | **3** | tier-3 verbs: \bget\b | — |
| `get_earnings_history` | **3** | tier-3 verbs: \bget\b, \bhistor(y/ies)\b | — |
| `get_financial_statements` | **3** | tier-3 verbs: \bget\b | — |
| `get_fred_series` | **3** | tier-3 verbs: \bget\b | — |
| `get_historical_fng_tool` | **3** | tier-3 verbs: \bget\b, \bretrieve\b | — |
| `get_insider_trades` | **3** | tier-3 verbs: \bget\b | — |
| `get_overall_sentiment_tool` | **3** | tier-3 verbs: \bget\b | — |
| `get_price_history` | **3** | tier-3 verbs: \bget\b, \bhistor(y/ies)\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `get_ticker_data` | **3** | tier-3 verbs: \bget\b | — |
| `get_ticker_news_tool` | **3** | tier-3 verbs: \bget\b, \bresearch\b | — |
| `get_top25_holders` | **3** | tier-3 verbs: \bget\b | — |
| `search_fred_series` | **3** | tier-3 verbs: \bsearch\b | raw-query |
| `social_media_feed` *(bulk)* | **3** | tier-3 verbs: \bget\b; bulk signal (array param or bulk wording) | — |
| `super_option_tool` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | — |
| `get_current_time` | **1** | tier-3 verbs: \bget\b; return-shape marker -> capped at 1 | — |

Tier counts: {1: 1, 3: 16}

### `maverick` — 119 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `data_clear_cache` | **5** | tier-5 verbs: \bclear\b | — |
| `delete_signal` | **5** | tier-5 verbs: \bdelete\b | — |
| `portfolio_clear_portfolio` | **5** | tier-5 verbs: \bclear\b | — |
| `portfolio_remove_position` | **5** | tier-5 verbs: \bremove\b | — |
| `remove_portfolio_position` | **5** | tier-5 verbs: \bremove\b | — |
| `reset_circuit_breaker` | **5** | tier-5 verbs: \breset\b | — |
| `watchlist_remove` | **5** | tier-5 verbs: \bremove\b | — |
| `add_portfolio_position` | **4** | tier-4 verbs: \badd\b | — |
| `create_signal` | **4** | tier-4 verbs: \bcreate\b | — |
| `create_strategy_ensemble` *(bulk)* | **4** | tier-4 verbs: \bcreate\b; bulk signal (array param or bulk wording) | — |
| `generate_backtest_charts` | **4** | tier-4 verbs: \bgenerate\b | — |
| `generate_optimization_charts` | **4** | tier-4 verbs: \bgenerate\b | — |
| `journal_add_trade` | **4** | tier-4 verbs: \badd\b | — |
| `journal_close_trade` | **4** | tier-4 verbs: \bclose\b | — |
| `performance_clear_system_caches` | **4** | tier-5 verbs: \bclear\b; scoped/partial edit language -> capped at 4 | — |
| `portfolio_add_position` | **4** | tier-4 verbs: \badd\b | — |
| `schedule_screening` | **4** | tier-4 verbs: \bschedule\b | — |
| `train_ml_predictor` | **4** | tier-4 verbs: \btrain\b | — |
| `update_signal` | **4** | tier-4 verbs: \bupdate\b | — |
| `watchlist_add` | **4** | tier-4 verbs: \badd\b | — |
| `watchlist_create` | **4** | tier-4 verbs: \bcreate\b | — |
| `agents_analyze_market_with_agent` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | raw-query, unbounded |
| `agents_compare_multi_agent_analysis` *(bulk)* | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b, \bcompare\b; bulk signal (array param or bulk wording) | raw-query |
| `agents_compare_personas_analysis` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b, \bcompare\b | raw-query |
| `agents_deep_research_financial` | **3** | tier-3 verbs: \bresearch\b | — |
| `agents_get_agent_streaming_analysis` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | raw-query |
| `agents_orchestrated_analysis` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | raw-query |
| `analyze_market_regimes` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | — |
| `backtest_portfolio` *(bulk)* | **3** | tier-3 verbs: \bbacktest\b; bulk signal (array param or bulk wording) | — |
| `backtest_signal` | **3** | tier-3 verbs: \bsummar(y/ise/ize)\b, \bbacktest\b | — |
| `check_signals_now` | **3** | tier-2 verbs: \blist\b; lists non-container items -> content read (3) | — |
| `compare_strategies` *(bulk)* | **3** | tier-3 verbs: \bcompare\b; bulk signal (array param or bulk wording) | — |
| `compare_tickers` | **3** | tier-3 verbs: \bcompare\b | — |
| `data_fetch_stock_data` | **3** | tier-3 verbs: \bfetch\b | — |
| `data_fetch_stock_data_batch` *(bulk)* | **3** | tier-3 verbs: \bfetch\b; bulk signal (array param or bulk wording) | — |
| `data_get_adanos_market_sentiment` | **3** | tier-3 verbs: \bget\b | — |
| `data_get_cached_price_data` | **3** | tier-3 verbs: \bget\b | — |
| `data_get_chart_links` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `data_get_news_sentiment` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b, \bresearch\b | unbounded |
| `data_get_stock_info` | **3** | tier-3 verbs: \bget\b | — |
| `fetch_stock_data` | **3** | tier-3 verbs: \bfetch\b | — |
| `get_adanos_market_sentiment` | **3** | tier-3 verbs: \bget\b | — |
| `get_all_screening_recommendations` | **3** | tier-3 verbs: \bget\b, \bscreen(er/ing)?\b | — |
| `get_decision_log` | **3** | tier-3 verbs: \bget\b, \bquery\b | unbounded |
| `get_economic_calendar` | **3** | tier-3 verbs: \bget\b | — |
| `get_full_technical_analysis` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `get_macd_analysis` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `get_market_overview` | **3** | tier-3 verbs: \bget\b | — |
| `get_market_regime` | **3** | tier-3 verbs: \bget\b | — |
| `get_maverick_bear_stocks` | **3** | tier-3 verbs: \bget\b | unbounded |
| `get_maverick_stocks` | **3** | tier-3 verbs: \bget\b | unbounded |
| `get_my_portfolio` | **3** | tier-3 verbs: \bget\b | — |
| `get_news_sentiment` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | unbounded |
| `get_position_risk_check` | **3** | tier-3 verbs: \bget\b | — |
| `get_regime_adjusted_sizing` | **3** | tier-3 verbs: \bget\b, \bcalculate\b | — |
| `get_regime_history` | **3** | tier-3 verbs: \bget\b, \bretrieve\b, \bhistor(y/ies)\b | — |
| `get_resource_usage` | **3** | tier-3 verbs: \bget\b | — |
| `get_risk_alerts` | **3** | tier-3 verbs: \bget\b | — |
| `get_rsi_analysis` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `get_screening_changes` | **3** | tier-3 verbs: \bget\b, \bscreen(er/ing)?\b | unbounded |
| `get_screening_history` | **3** | tier-3 verbs: \bget\b, \bhistor(y/ies)\b, \bscreen(er/ing)?\b | — |
| `get_stock_info` | **3** | tier-3 verbs: \bget\b | — |
| `get_strategy_comparison` | **3** | tier-3 verbs: \bget\b | — |
| `get_strategy_help` | **3** | tier-3 verbs: \bget\b | — |
| `get_strategy_performance` | **3** | tier-3 verbs: \bget\b | — |
| `get_supply_demand_breakouts` | **3** | tier-3 verbs: \bget\b | unbounded |
| `get_support_resistance` | **3** | tier-3 verbs: \bget\b | — |
| `get_upcoming_catalysts` | **3** | tier-3 verbs: \bget\b | — |
| `get_user_portfolio_summary` | **3** | tier-3 verbs: \bget\b, \bsummar(y/ise/ize)\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `get_watchlist` | **3** | tier-3 verbs: \bget\b | unbounded |
| `journal_list_trades` | **3** | tier-2 verbs: \blist\b; lists non-container items -> content read (3) | unbounded |
| `journal_trade_review` | **3** | tier-3 verbs: \bdetails?\b | — |
| `list_all_strategies` | **3** | tier-2 verbs: \blist\b, \bnames?\b; lists non-container items -> content read (3) | — |
| `list_signals` | **3** | tier-2 verbs: \blist\b; lists non-container items -> content read (3) | — |
| `list_strategies` | **3** | tier-2 verbs: \blist\b; lists non-container items -> content read (3) | — |
| `monte_carlo_simulation` | **3** | tier-3 verbs: \bsimulat(e/ion)\b, \bbacktest\b | — |
| `optimize_strategy` | **3** | tier-3 verbs: \bsearch\b | — |
| `parse_strategy` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `performance_analyze_database_index_usage` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | — |
| `performance_optimize_cache_configuration` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | — |
| `portfolio_compare_tickers` *(bulk)* | **3** | tier-3 verbs: \bcompare\b; bulk signal (array param or bulk wording) | — |
| `portfolio_correlation_analysis` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | — |
| `portfolio_get_my_portfolio` | **3** | tier-3 verbs: \bget\b | — |
| `portfolio_portfolio_correlation_analysis` *(bulk)* | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b; bulk signal (array param or bulk wording) | — |
| `portfolio_risk_adjusted_analysis` | **3** | tier-3 verbs: \bdetails?\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `research_analyze_market_sentiment` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b, \bresearch\b | — |
| `research_company_comprehensive` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b, \bresearch\b | — |
| `research_comprehensive_research` | **3** | tier-3 verbs: \bsearch\b, \banaly[sz](e/es/ed/ing/is)\b, \bresearch\b | raw-query |
| `risk_adjusted_analysis` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | — |
| `run_backtest` | **3** | tier-3 verbs: \bbacktest\b | — |
| `run_ml_strategy_backtest` | **3** | tier-3 verbs: \bbacktest\b | — |
| `screening_get_all_screening_recommendations` | **3** | tier-3 verbs: \bget\b, \bscreen(er/ing)?\b | — |
| `screening_get_maverick_bear_stocks` | **3** | tier-3 verbs: \bget\b, \bscreen(er/ing)?\b | unbounded |
| `screening_get_maverick_stocks` | **3** | tier-3 verbs: \bget\b, \bresearch\b, \bscreen(er/ing)?\b | unbounded |
| `screening_get_screening_by_criteria` | **3** | tier-3 verbs: \bget\b, \bscreen(er/ing)?\b | unbounded |
| `screening_get_supply_demand_breakouts` | **3** | tier-3 verbs: \bget\b, \bscreen(er/ing)?\b | unbounded |
| `technical_get_full_technical_analysis` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `technical_get_macd_analysis` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `technical_get_rsi_analysis` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `technical_get_stock_chart_analysis` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `technical_get_support_resistance` | **3** | tier-3 verbs: \bget\b | — |
| `walk_forward_analysis` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | — |
| `agents_list_available_agents` | **2** | tier-2 verbs: \blist\b; lists non-container items -> content read (3); return-shape marker -> capped at 2 | — |
| `get_circuit_breaker_status` | **2** | tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | — |
| `get_component_status` | **2** | tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | — |
| `get_mcp_connection_status` | **2** | tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | — |
| `get_portfolio_risk_dashboard` | **2** | tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | — |
| `get_screening_pipeline_status` | **2** | tier-3 verbs: \bget\b, \bscreen(er/ing)?\b; return-shape marker -> capped at 2 | — |
| `get_status_dashboard` | **2** | tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | — |
| `get_tool_registry_status` | **2** | tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | — |
| `performance_get_cache_performance_status` | **2** | tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | — |
| `performance_get_database_performance_status` | **2** | tier-3 verbs: \bget\b, \bquery\b; return-shape marker -> capped at 2 | — |
| `watchlist_brief` | **2** | tier-2 verbs: \bcounts?\b | — |
| `discover_capabilities` | **1** | tier-2 verbs: \bdiscover\b; return-shape marker -> capped at 1 | — |
| `get_health_history` | **1** | tier-3 verbs: \bget\b, \bhistor(y/ies)\b, \banaly[sz](e/es/ed/ing/is)\b; return-shape marker -> capped at 1 | — |
| `get_system_health` | **1** | tier-3 verbs: \bget\b; return-shape marker -> capped at 1 | — |
| `performance_get_redis_health_status` | **1** | tier-3 verbs: \bget\b; return-shape marker -> capped at 1 | — |
| `performance_get_system_performance_health` | **1** | tier-3 verbs: \bget\b, \bquery\b, \banaly[sz](e/es/ed/ing/is)\b; return-shape marker -> capped at 1 | — |
| `run_health_diagnostics` | **1** | tier-1 verbs: \bhealth(check)?\b, \bdiagnostics?\b | — |

Tier counts: {1: 6, 2: 11, 3: 81, 4: 14, 5: 7}

### `openbb` — 30 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `install_skill` | **4** | tier-4 verbs: \binstall\b | — |
| `crypto_price_historical` | **3** | tier-3 verbs: \bget\b | — |
| `derivatives_futures_curve` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `derivatives_futures_historical` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `derivatives_options_chains` | **3** | tier-3 verbs: \bget\b | — |
| `derivatives_options_surface` | **3** | tier-2 verbs: \blist\b; lists non-container items -> content read (3) | — |
| `equity_discovery_active` | **3** | tier-3 verbs: \bget\b | unbounded |
| `equity_discovery_aggressive_small_caps` | **3** | tier-3 verbs: \bget\b | unbounded |
| `equity_discovery_gainers` | **3** | tier-3 verbs: \bget\b | unbounded |
| `equity_discovery_growth_tech` | **3** | tier-3 verbs: \bget\b | unbounded |
| `equity_discovery_losers` | **3** | tier-3 verbs: \bget\b | unbounded |
| `equity_discovery_undervalued_growth` | **3** | tier-3 verbs: \bget\b | unbounded |
| `equity_discovery_undervalued_large_caps` | **3** | tier-3 verbs: \bget\b | unbounded |
| `equity_estimates_consensus` | **3** | tier-3 verbs: \bget\b | — |
| `equity_fundamental_balance` | **3** | tier-3 verbs: \bget\b | unbounded |
| `equity_fundamental_cash` | **3** | tier-3 verbs: \bget\b | unbounded |
| `equity_fundamental_dividends` | **3** | tier-3 verbs: \bget\b | — |
| `equity_fundamental_income` | **3** | tier-3 verbs: \bget\b | unbounded |
| `equity_fundamental_management` | **3** | tier-3 verbs: \bget\b | — |
| `equity_fundamental_metrics` | **3** | tier-3 verbs: \bget\b | — |
| `equity_ownership_share_statistics` | **3** | tier-3 verbs: \bget\b | — |
| `equity_price_historical` | **3** | tier-3 verbs: \bget\b | — |
| `equity_price_quote` | **3** | tier-3 verbs: \bget\b | — |
| `equity_profile` | **3** | tier-3 verbs: \bget\b | — |
| `equity_screener` | **3** | tier-3 verbs: \bscreen(er/ing)?\b | unbounded |
| `get_prompt` | **3** | tier-3 verbs: \bget\b | — |
| `news_company` | **3** | tier-3 verbs: \bget\b | unbounded |
| `read_resource` | **3** | readOnlyHint=true -> ceiling 3; tier-3 verbs: \bread\b, \bcontents?\b | — |
| `list_prompts` | **2** | tier-2 verbs: \blist\b, \bmetadata\b, \bnames?\b; lists non-container items -> content read (3); return-shape marker -> capped at 2 | — |
| `list_resources` | **2** | readOnlyHint=true -> ceiling 3; tier-2 verbs: \blist\b, \bmetadata\b, \bnames?\b; lists non-container items -> content read (3); return-shape marker -> capped at 2 | — |

Tier counts: {2: 2, 3: 27, 4: 1}

### `sec_edgar` — 21 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `analyze_8k` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | — |
| `analyze_form4_transactions` | **3** | tier-3 verbs: \bextract\b, \bquery\b, \bdetails?\b | unbounded |
| `analyze_insider_sentiment` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b | — |
| `compare_periods` | **3** | tier-3 verbs: \banaly[sz](e/es/ed/ing/is)\b, \bcompare\b | — |
| `discover_company_metrics` | **3** | tier-3 verbs: \bsearch\b | — |
| `get_cik_by_ticker` | **3** | tier-3 verbs: \bget\b | — |
| `get_company_facts` | **3** | tier-3 verbs: \bget\b | — |
| `get_company_info` | **3** | tier-3 verbs: \bget\b, \bquery\b | — |
| `get_filing_content` | **3** | tier-3 verbs: \bget\b, \bcontents?\b | — |
| `get_filing_sections` | **3** | tier-3 verbs: \bget\b | — |
| `get_financials` | **3** | tier-3 verbs: \bget\b, \bquery\b | — |
| `get_form4_details` | **3** | tier-3 verbs: \bget\b, \bdetails?\b | — |
| `get_insider_summary` | **3** | tier-3 verbs: \bget\b, \bquery\b, \bsummar(y/ise/ize)\b | — |
| `get_insider_transactions` *(bulk)* | **3** | tier-3 verbs: \bget\b, \bquery\b; bulk signal (array param or bulk wording) | unbounded |
| `get_key_metrics` *(bulk)* | **3** | tier-3 verbs: \bget\b, \bretrieve\b; bulk signal (array param or bulk wording) | — |
| `get_recent_filings` | **3** | tier-3 verbs: \bget\b | unbounded |
| `get_recommended_tools` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `get_segment_data` | **3** | tier-3 verbs: \bget\b, \banaly[sz](e/es/ed/ing/is)\b | — |
| `get_xbrl_concepts` *(bulk)* | **3** | tier-3 verbs: \bget\b, \bextract\b; bulk signal (array param or bulk wording) | — |
| `search_companies` | **3** | tier-3 verbs: \bsearch\b, \bquery\b | raw-query, unbounded |
| `discover_xbrl_concepts` | **2** | tier-2 verbs: \bdiscover\b | — |

Tier counts: {2: 1, 3: 20}

### `yahoo_finance` — 9 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `get_financial_statement` | **3** | tier-3 verbs: \bget\b | — |
| `get_historical_stock_prices` | **3** | tier-3 verbs: \bget\b | — |
| `get_holder_info` | **3** | tier-3 verbs: \bget\b | — |
| `get_option_chain` | **3** | tier-3 verbs: \bget\b, \bfetch\b | — |
| `get_recommendations` | **3** | tier-3 verbs: \bget\b | — |
| `get_stock_actions` | **3** | tier-3 verbs: \bget\b | — |
| `get_stock_info` | **3** | tier-3 verbs: \bget\b | — |
| `get_yahoo_finance_news` | **3** | tier-3 verbs: \bget\b | — |
| `get_option_expiration_dates` | **2** | tier-3 verbs: \bget\b, \bfetch\b; return-shape marker -> capped at 2 | — |

Tier counts: {2: 1, 3: 8}
