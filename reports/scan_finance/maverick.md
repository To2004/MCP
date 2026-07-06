# Scan — maverick

_kind=filesystem · provenance=offline-baseline · model_reviewed=False · bands={'low': 291, 'medium': 339, 'high': 84, 'critical': 0}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: a class of file the server can read or write, by type
- **blast_radius_meaning**: from reading one file to overwriting or destroying many
- **worked_example**: write_file on a .pem = critical: clobbers key material irreversibly

## Tool impact

| tool | impact |
| --- | --- |
| `technical_get_rsi_analysis` | 1 |
| `technical_get_macd_analysis` | 1 |
| `technical_get_support_resistance` | 1 |
| `technical_get_full_technical_analysis` | 1 |
| `technical_get_stock_chart_analysis` | 1 |
| `screening_get_maverick_stocks` | 1 |
| `screening_get_maverick_bear_stocks` | 1 |
| `screening_get_supply_demand_breakouts` | 1 |
| `screening_get_all_screening_recommendations` | 1 |
| `screening_get_screening_by_criteria` | 1 |
| `portfolio_add_position` | 2 |
| `portfolio_get_my_portfolio` | 1 |
| `portfolio_remove_position` | 3 |
| `portfolio_clear_portfolio` | 3 |
| `portfolio_risk_adjusted_analysis` | 1 |
| `portfolio_compare_tickers` | 1 |
| `portfolio_portfolio_correlation_analysis` | 1 |
| `data_fetch_stock_data` | 2 |
| `data_fetch_stock_data_batch` | 2 |
| `data_get_stock_info` | 1 |
| `data_get_adanos_market_sentiment` | 1 |
| `data_get_news_sentiment` | 1 |
| `data_get_cached_price_data` | 1 |
| `data_get_chart_links` | 1 |
| `data_clear_cache` | 1 |
| `performance_get_system_performance_health` | 1 |
| `performance_get_redis_health_status` | 1 |
| `performance_get_cache_performance_status` | 1 |
| `performance_get_database_performance_status` | 1 |
| `performance_analyze_database_index_usage` | 1 |
| `performance_optimize_cache_configuration` | 2 |
| `performance_clear_system_caches` | 1 |
| `agents_list_available_agents` | 1 |
| `agents_analyze_market_with_agent` | 1 |
| `agents_get_agent_streaming_analysis` | 2 |
| `agents_compare_personas_analysis` | 1 |
| `agents_orchestrated_analysis` | 1 |
| `agents_deep_research_financial` | 1 |
| `agents_compare_multi_agent_analysis` | 1 |
| `research_comprehensive_research` | 1 |
| `research_company_comprehensive` | 1 |
| `research_analyze_market_sentiment` | 1 |
| `get_system_health` | 1 |
| `get_component_status` | 1 |
| `get_circuit_breaker_status` | 1 |
| `get_resource_usage` | 1 |
| `get_status_dashboard` | 1 |
| `reset_circuit_breaker` | 2 |
| `get_health_history` | 1 |
| `run_health_diagnostics` | 1 |
| `run_backtest` | 1 |
| `optimize_strategy` | 1 |
| `walk_forward_analysis` | 1 |
| `monte_carlo_simulation` | 1 |
| `compare_strategies` | 1 |
| `list_strategies` | 1 |
| `parse_strategy` | 1 |
| `backtest_portfolio` | 1 |
| `generate_backtest_charts` | 1 |
| `generate_optimization_charts` | 1 |
| `run_ml_strategy_backtest` | 1 |
| `train_ml_predictor` | 1 |
| `analyze_market_regimes` | 1 |
| `create_strategy_ensemble` | 2 |
| `discover_capabilities` | 1 |
| `list_all_strategies` | 1 |
| `get_strategy_help` | 1 |
| `get_decision_log` | 1 |
| `get_tool_registry_status` | 1 |
| `create_signal` | 2 |
| `update_signal` | 2 |
| `list_signals` | 1 |
| `delete_signal` | 3 |
| `check_signals_now` | 1 |
| `get_market_regime` | 1 |
| `get_regime_history` | 1 |
| `backtest_signal` | 1 |
| `get_screening_changes` | 1 |
| `get_screening_history` | 1 |
| `schedule_screening` | 3 |
| `get_screening_pipeline_status` | 1 |
| `journal_add_trade` | 2 |
| `journal_close_trade` | 1 |
| `journal_list_trades` | 1 |
| `get_strategy_performance` | 1 |
| `get_strategy_comparison` | 1 |
| `journal_trade_review` | 1 |
| `watchlist_create` | 2 |
| `watchlist_add` | 2 |
| `watchlist_remove` | 3 |
| `watchlist_brief` | 1 |
| `get_upcoming_catalysts` | 1 |
| `get_portfolio_risk_dashboard` | 1 |
| `get_position_risk_check` | 2 |
| `get_regime_adjusted_sizing` | 1 |
| `get_risk_alerts` | 1 |
| `get_user_portfolio_summary` | 1 |
| `get_watchlist` | 1 |
| `get_market_overview` | 1 |
| `get_economic_calendar` | 1 |
| `get_mcp_connection_status` | 1 |
| `get_rsi_analysis` | 1 |
| `get_macd_analysis` | 1 |
| `get_support_resistance` | 1 |
| `get_maverick_stocks` | 2 |
| `get_my_portfolio` | 1 |
| `get_full_technical_analysis` | 1 |
| `get_maverick_bear_stocks` | 2 |
| `get_supply_demand_breakouts` | 1 |
| `get_all_screening_recommendations` | 1 |
| `add_portfolio_position` | 2 |
| `remove_portfolio_position` | 3 |
| `portfolio_correlation_analysis` | 1 |
| `compare_tickers` | 1 |
| `risk_adjusted_analysis` | 1 |
| `fetch_stock_data` | 1 |
| `get_stock_info` | 1 |
| `get_news_sentiment` | 1 |
| `get_adanos_market_sentiment` | 1 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `.txt` | 2 |
| `.csv` | 4 |
| `.json` | 4 |
| `.md` | 2 |
| `.png` | 2 |
| `.py` | 4 |

## Risk matrix (score · band)

| asset \ tool | technical_get_rsi_analysis | technical_get_macd_analysis | technical_get_support_resistance | technical_get_full_technical_analysis | technical_get_stock_chart_analysis | screening_get_maverick_stocks | screening_get_maverick_bear_stocks | screening_get_supply_demand_breakouts | screening_get_all_screening_recommendations | screening_get_screening_by_criteria | portfolio_add_position | portfolio_get_my_portfolio | portfolio_remove_position | portfolio_clear_portfolio | portfolio_risk_adjusted_analysis | portfolio_compare_tickers | portfolio_portfolio_correlation_analysis | data_fetch_stock_data | data_fetch_stock_data_batch | data_get_stock_info | data_get_adanos_market_sentiment | data_get_news_sentiment | data_get_cached_price_data | data_get_chart_links | data_clear_cache | performance_get_system_performance_health | performance_get_redis_health_status | performance_get_cache_performance_status | performance_get_database_performance_status | performance_analyze_database_index_usage | performance_optimize_cache_configuration | performance_clear_system_caches | agents_list_available_agents | agents_analyze_market_with_agent | agents_get_agent_streaming_analysis | agents_compare_personas_analysis | agents_orchestrated_analysis | agents_deep_research_financial | agents_compare_multi_agent_analysis | research_comprehensive_research | research_company_comprehensive | research_analyze_market_sentiment | get_system_health | get_component_status | get_circuit_breaker_status | get_resource_usage | get_status_dashboard | reset_circuit_breaker | get_health_history | run_health_diagnostics | run_backtest | optimize_strategy | walk_forward_analysis | monte_carlo_simulation | compare_strategies | list_strategies | parse_strategy | backtest_portfolio | generate_backtest_charts | generate_optimization_charts | run_ml_strategy_backtest | train_ml_predictor | analyze_market_regimes | create_strategy_ensemble | discover_capabilities | list_all_strategies | get_strategy_help | get_decision_log | get_tool_registry_status | create_signal | update_signal | list_signals | delete_signal | check_signals_now | get_market_regime | get_regime_history | backtest_signal | get_screening_changes | get_screening_history | schedule_screening | get_screening_pipeline_status | journal_add_trade | journal_close_trade | journal_list_trades | get_strategy_performance | get_strategy_comparison | journal_trade_review | watchlist_create | watchlist_add | watchlist_remove | watchlist_brief | get_upcoming_catalysts | get_portfolio_risk_dashboard | get_position_risk_check | get_regime_adjusted_sizing | get_risk_alerts | get_user_portfolio_summary | get_watchlist | get_market_overview | get_economic_calendar | get_mcp_connection_status | get_rsi_analysis | get_macd_analysis | get_support_resistance | get_maverick_stocks | get_my_portfolio | get_full_technical_analysis | get_maverick_bear_stocks | get_supply_demand_breakouts | get_all_screening_recommendations | add_portfolio_position | remove_portfolio_position | portfolio_correlation_analysis | compare_tickers | risk_adjusted_analysis | fetch_stock_data | get_stock_info | get_news_sentiment | get_adanos_market_sentiment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `.txt` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 24 🟠 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 24 🟠 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.csv` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 48 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 48 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 |
| `.json` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 48 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 48 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 |
| `.md` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 24 🟠 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 24 🟠 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.png` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 24 🟠 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 24 🟠 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 8 🟡 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.py` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 48 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 48 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 24 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 |
