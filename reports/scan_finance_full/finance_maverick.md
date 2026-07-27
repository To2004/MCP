# Scan — finance:maverick

_kind=finance · provenance=llm-scan · model_reviewed=True · bands={'low': 165, 'medium': 353, 'high': 194, 'critical': 2}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–75): 🟢 <20 · 🟡 20–40 · 🟠 40–60 · 🔴 60–75.

## Inferred domain profile

- **mcp_kind**: financial_trading_system
- **asset_meaning**: Financial data and user-specific trading information.
- **blast_radius_meaning**: The extent to which a tool can impact financial assets or sensitive user data. Narrow touch involves minimal changes, while severe actions could lead to irreversible financial transactions or exposure of critical credentials.
- **dangerous_classes**: restricted, financial, pii, money, crown_jewel, secret, credentials
- **irreversible_actions**: portfolio_clear_portfolio, create_signal, update_signal, delete_signal, journal_close_trade, remove_portfolio_position, portfolio_remove_position, portfolio_clear_portfolio, data_clear_cache, performance_clear_system_caches
- **worked_example**: The tool 'portfolio_clear_portfolio' on the asset class 'portfolio_positions' is highly severe as it removes all positions from a portfolio, which cannot be undone and impacts financial holdings.

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
| `data_fetch_stock_data` | 1 |
| `data_fetch_stock_data_batch` | 1 |
| `data_get_stock_info` | 1 |
| `data_get_adanos_market_sentiment` | 1 |
| `data_get_news_sentiment` | 1 |
| `data_get_cached_price_data` | 1 |
| `data_get_chart_links` | 1 |
| `data_clear_cache` | 2 |
| `performance_get_system_performance_health` | 1 |
| `performance_get_redis_health_status` | 1 |
| `performance_get_cache_performance_status` | 1 |
| `performance_get_database_performance_status` | 1 |
| `performance_analyze_database_index_usage` | 1 |
| `performance_optimize_cache_configuration` | 1 |
| `performance_clear_system_caches` | 3 |
| `agents_list_available_agents` | 1 |
| `agents_analyze_market_with_agent` | 1 |
| `agents_get_agent_streaming_analysis` | 1 |
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
| `train_ml_predictor` | 2 |
| `analyze_market_regimes` | 1 |
| `create_strategy_ensemble` | 2 |
| `discover_capabilities` | 1 |
| `list_all_strategies` | 1 |
| `get_strategy_help` | 1 |
| `get_decision_log` | 1 |
| `get_tool_registry_status` | 1 |
| `create_signal` | 3 |
| `update_signal` | 3 |
| `list_signals` | 1 |
| `delete_signal` | 3 |
| `check_signals_now` | 1 |
| `get_market_regime` | 1 |
| `get_regime_history` | 1 |
| `backtest_signal` | 1 |
| `get_screening_changes` | 1 |
| `get_screening_history` | 1 |
| `schedule_screening` | 2 |
| `get_screening_pipeline_status` | 1 |
| `journal_add_trade` | 2 |
| `journal_close_trade` | 3 |
| `journal_list_trades` | 1 |
| `get_strategy_performance` | 1 |
| `get_strategy_comparison` | 1 |
| `journal_trade_review` | 1 |
| `watchlist_create` | 2 |
| `watchlist_add` | 2 |
| `watchlist_remove` | 2 |
| `watchlist_brief` | 1 |
| `get_upcoming_catalysts` | 1 |
| `get_portfolio_risk_dashboard` | 1 |
| `get_position_risk_check` | 1 |
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
| `get_maverick_stocks` | 1 |
| `get_my_portfolio` | 1 |
| `get_full_technical_analysis` | 1 |
| `get_maverick_bear_stocks` | 1 |
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
| `market_data` | 1 |
| `watchlists` | 4 |
| `screening_results` | 3 |
| `portfolio_positions` | 4 |
| `account_and_orders` | 5 |
| `server_api_credentials` | 5 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; score ranges 0–75. Colour is by raw score for visualization: 🟢 <20 · 🟡 20–40 · 🟠 40–60 · 🔴 60–75. Likelihood is pinned to 1.0 and omitted._

| asset \ tool | technical_get_rsi_analysis | technical_get_macd_analysis | technical_get_support_resistance | technical_get_full_technical_analysis | technical_get_stock_chart_analysis | screening_get_maverick_stocks | screening_get_maverick_bear_stocks | screening_get_supply_demand_breakouts | screening_get_all_screening_recommendations | screening_get_screening_by_criteria | portfolio_add_position | portfolio_get_my_portfolio | portfolio_remove_position | portfolio_clear_portfolio | portfolio_risk_adjusted_analysis | portfolio_compare_tickers | portfolio_portfolio_correlation_analysis | data_fetch_stock_data | data_fetch_stock_data_batch | data_get_stock_info | data_get_adanos_market_sentiment | data_get_news_sentiment | data_get_cached_price_data | data_get_chart_links | data_clear_cache | performance_get_system_performance_health | performance_get_redis_health_status | performance_get_cache_performance_status | performance_get_database_performance_status | performance_analyze_database_index_usage | performance_optimize_cache_configuration | performance_clear_system_caches | agents_list_available_agents | agents_analyze_market_with_agent | agents_get_agent_streaming_analysis | agents_compare_personas_analysis | agents_orchestrated_analysis | agents_deep_research_financial | agents_compare_multi_agent_analysis | research_comprehensive_research | research_company_comprehensive | research_analyze_market_sentiment | get_system_health | get_component_status | get_circuit_breaker_status | get_resource_usage | get_status_dashboard | reset_circuit_breaker | get_health_history | run_health_diagnostics | run_backtest | optimize_strategy | walk_forward_analysis | monte_carlo_simulation | compare_strategies | list_strategies | parse_strategy | backtest_portfolio | generate_backtest_charts | generate_optimization_charts | run_ml_strategy_backtest | train_ml_predictor | analyze_market_regimes | create_strategy_ensemble | discover_capabilities | list_all_strategies | get_strategy_help | get_decision_log | get_tool_registry_status | create_signal | update_signal | list_signals | delete_signal | check_signals_now | get_market_regime | get_regime_history | backtest_signal | get_screening_changes | get_screening_history | schedule_screening | get_screening_pipeline_status | journal_add_trade | journal_close_trade | journal_list_trades | get_strategy_performance | get_strategy_comparison | journal_trade_review | watchlist_create | watchlist_add | watchlist_remove | watchlist_brief | get_upcoming_catalysts | get_portfolio_risk_dashboard | get_position_risk_check | get_regime_adjusted_sizing | get_risk_alerts | get_user_portfolio_summary | get_watchlist | get_market_overview | get_economic_calendar | get_mcp_connection_status | get_rsi_analysis | get_macd_analysis | get_support_resistance | get_maverick_stocks | get_my_portfolio | get_full_technical_analysis | get_maverick_bear_stocks | get_supply_demand_breakouts | get_all_screening_recommendations | add_portfolio_position | remove_portfolio_position | portfolio_correlation_analysis | compare_tickers | risk_adjusted_analysis | fetch_stock_data | get_stock_info | get_news_sentiment | get_adanos_market_sentiment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `market_data` | 1 (1×1×1) 🟢 | 2 (1×2×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 2 (1×1×2) 🟢 | 4 (1×4×1) 🟢 | 6 (1×2×3) 🟢 | 3 (1×1×3) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 2 (1×2×1) 🟢 | 8 (1×4×2) 🟢 | 4 (1×4×1) 🟢 | 2 (1×2×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 2 (1×2×1) 🟢 | 12 (1×4×3) 🟢 | 2 (1×2×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×2×2) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×2×2) 🟢 | 4 (1×4×1) 🟢 | 8 (1×4×2) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 2 (1×2×1) 🟢 | 4 (1×4×1) 🟢 | 2 (1×2×1) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 4 (1×4×1) 🟢 | 6 (1×2×3) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×2×2) 🟢 | 2 (1×2×1) 🟢 | 2 (1×1×2) 🟢 | 3 (1×1×3) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 2 (1×2×1) 🟢 | 4 (1×2×2) 🟢 | 4 (1×2×2) 🟢 | 2 (1×1×2) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 2 (1×2×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 2 (1×2×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 2 (1×1×2) 🟢 | 3 (1×1×3) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 |
| `watchlists` | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 4 (4×1×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×2×2) 🟢 | 4 (4×1×1) 🟢 | 24 (4×2×3) 🟡 | 12 (4×1×3) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 32 (4×4×2) 🟡 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 24 (4×2×3) 🟡 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×2×2) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×2×2) 🟢 | 8 (4×2×1) 🟢 | 16 (4×2×2) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 24 (4×2×3) 🟡 | 24 (4×2×3) 🟡 | 16 (4×4×1) 🟢 | 24 (4×2×3) 🟡 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×2×2) 🟢 | 8 (4×2×1) 🟢 | 16 (4×2×2) 🟢 | 24 (4×2×3) 🟡 | 16 (4×4×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 4 (4×1×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×1×2) 🟢 | 24 (4×2×3) 🟡 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 4 (4×1×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 |
| `screening_results` | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 6 (3×2×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×2×2) 🟢 | 3 (3×1×1) 🟢 | 18 (3×2×3) 🟢 | 18 (3×2×3) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 24 (3×4×2) 🟡 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 36 (3×4×3) 🟡 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 6 (3×2×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 6 (3×1×2) 🟢 | 3 (3×1×1) 🟢 | 6 (3×2×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 6 (3×1×2) 🟢 | 3 (3×1×1) 🟢 | 24 (3×4×2) 🟡 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 9 (3×1×3) 🟢 | 18 (3×2×3) 🟢 | 12 (3×4×1) 🟢 | 18 (3×2×3) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×2×2) 🟢 | 6 (3×2×1) 🟢 | 6 (3×1×2) 🟢 | 9 (3×1×3) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 6 (3×1×2) 🟢 | 12 (3×2×2) 🟢 | 6 (3×1×2) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 6 (3×2×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×2×2) 🟢 | 9 (3×1×3) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 12 (3×4×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 |
| `portfolio_positions` | 8 (4×2×1) 🟢 | 4 (4×1×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 20 (4×5×1) 🟡 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×2×2) 🟢 | 16 (4×4×1) 🟢 | 24 (4×2×3) 🟡 | 60 (4×5×3) 🔴 | 16 (4×4×1) 🟢 | 20 (4×5×1) 🟡 | 20 (4×5×1) 🟡 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 8 (4×2×1) 🟢 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 32 (4×4×2) 🟡 | 8 (4×2×1) 🟢 | 4 (4×1×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 12 (4×1×3) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 20 (4×5×1) 🟡 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 20 (4×5×1) 🟡 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×2×2) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×1×2) 🟢 | 8 (4×2×1) 🟢 | 40 (4×5×2) 🟠 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 20 (4×5×1) 🟡 | 8 (4×2×1) 🟢 | 24 (4×2×3) 🟡 | 24 (4×2×3) 🟡 | 20 (4×5×1) 🟡 | 24 (4×2×3) 🟡 | 16 (4×4×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×1×2) 🟢 | 8 (4×2×1) 🟢 | 16 (4×2×2) 🟢 | 24 (4×2×3) 🟡 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 4 (4×1×1) 🟢 | 8 (4×1×2) 🟢 | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 | 20 (4×5×1) 🟡 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 4 (4×1×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 20 (4×5×1) 🟡 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 4 (4×1×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 4 (4×1×1) 🟢 | 20 (4×5×1) 🟡 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 16 (4×2×2) 🟢 | 24 (4×2×3) 🟡 | 16 (4×4×1) 🟢 | 16 (4×4×1) 🟢 | 8 (4×2×1) 🟢 | 4 (4×1×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 | 8 (4×2×1) 🟢 |
| `account_and_orders` | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 25 (5×5×1) 🟡 | 20 (5×2×2) 🟡 | 25 (5×5×1) 🟡 | 30 (5×2×3) 🟡 | 75 (5×5×3) 🔴 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 40 (5×4×2) 🟠 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 15 (5×3×1) 🟢 | 10 (5×2×1) 🟢 | 30 (5×2×3) 🟡 | 10 (5×2×1) 🟢 | 20 (5×4×1) 🟡 | 20 (5×4×1) 🟡 | 25 (5×5×1) 🟡 | 25 (5×5×1) 🟡 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 25 (5×5×1) 🟡 | 20 (5×4×1) 🟡 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 20 (5×2×2) 🟡 | 25 (5×5×1) 🟡 | 20 (5×4×1) 🟡 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 20 (5×2×2) 🟡 | 5 (5×1×1) 🟢 | 30 (5×3×2) 🟡 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 5 (5×1×1) 🟢 | 30 (5×2×3) 🟡 | 30 (5×2×3) 🟡 | 25 (5×5×1) 🟡 | 30 (5×2×3) 🟡 | 20 (5×4×1) 🟡 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 25 (5×5×1) 🟡 | 25 (5×5×1) 🟡 | 10 (5×2×1) 🟢 | 20 (5×2×2) 🟡 | 10 (5×2×1) 🟢 | 20 (5×2×2) 🟡 | 30 (5×2×3) 🟡 | 25 (5×5×1) 🟡 | 20 (5×4×1) 🟡 | 25 (5×5×1) 🟡 | 5 (5×1×1) 🟢 | 20 (5×2×2) 🟡 | 20 (5×2×2) 🟡 | 20 (5×2×2) 🟡 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 25 (5×5×1) 🟡 | 20 (5×2×2) 🟡 | 30 (5×2×3) 🟡 | 25 (5×5×1) 🟡 | 25 (5×5×1) 🟡 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 |
| `server_api_credentials` | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×1×2) 🟢 | 5 (5×1×1) 🟢 | 15 (5×1×3) 🟢 | 15 (5×1×3) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 20 (5×2×2) 🟡 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 30 (5×2×3) 🟡 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 25 (5×5×1) 🟡 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×1×2) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×1×2) 🟢 | 5 (5×1×1) 🟢 | 10 (5×1×2) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 15 (5×1×3) 🟢 | 30 (5×2×3) 🟡 | 25 (5×5×1) 🟡 | 30 (5×2×3) 🟡 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×1×2) 🟢 | 5 (5×1×1) 🟢 | 10 (5×1×2) 🟢 | 15 (5×1×3) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 10 (5×1×2) 🟢 | 15 (5×1×3) 🟢 | 10 (5×2×1) 🟢 | 10 (5×2×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 | 5 (5×1×1) 🟢 |

## Blast radius (tool reach · 1–5)

_How many items ONE call of the tool touches on that asset — a count of reach, not severity. Constant down a column is expected for same-structure assets; `⚠` marks a tool the consistency check found drifting._

| asset \ tool | technical_get_rsi_analysis ⚠ | technical_get_macd_analysis ⚠ | technical_get_support_resistance ⚠ | technical_get_full_technical_analysis ⚠ | technical_get_stock_chart_analysis ⚠ | screening_get_maverick_stocks ⚠ | screening_get_maverick_bear_stocks ⚠ | screening_get_supply_demand_breakouts ⚠ | screening_get_all_screening_recommendations ⚠ | screening_get_screening_by_criteria ⚠ | portfolio_add_position ⚠ | portfolio_get_my_portfolio ⚠ | portfolio_remove_position ⚠ | portfolio_clear_portfolio ⚠ | portfolio_risk_adjusted_analysis ⚠ | portfolio_compare_tickers ⚠ | portfolio_portfolio_correlation_analysis ⚠ | data_fetch_stock_data ⚠ | data_fetch_stock_data_batch ⚠ | data_get_stock_info ⚠ | data_get_adanos_market_sentiment ⚠ | data_get_news_sentiment ⚠ | data_get_cached_price_data ⚠ | data_get_chart_links ⚠ | data_clear_cache | performance_get_system_performance_health ⚠ | performance_get_redis_health_status ⚠ | performance_get_cache_performance_status ⚠ | performance_get_database_performance_status ⚠ | performance_analyze_database_index_usage ⚠ | performance_optimize_cache_configuration | performance_clear_system_caches ⚠ | agents_list_available_agents | agents_analyze_market_with_agent | agents_get_agent_streaming_analysis | agents_compare_personas_analysis ⚠ | agents_orchestrated_analysis ⚠ | agents_deep_research_financial ⚠ | agents_compare_multi_agent_analysis ⚠ | research_comprehensive_research ⚠ | research_company_comprehensive ⚠ | research_analyze_market_sentiment ⚠ | get_system_health ⚠ | get_component_status ⚠ | get_circuit_breaker_status ⚠ | get_resource_usage ⚠ | get_status_dashboard ⚠ | reset_circuit_breaker | get_health_history ⚠ | run_health_diagnostics ⚠ | run_backtest ⚠ | optimize_strategy ⚠ | walk_forward_analysis ⚠ | monte_carlo_simulation ⚠ | compare_strategies ⚠ | list_strategies ⚠ | parse_strategy ⚠ | backtest_portfolio ⚠ | generate_backtest_charts ⚠ | generate_optimization_charts ⚠ | run_ml_strategy_backtest ⚠ | train_ml_predictor ⚠ | analyze_market_regimes ⚠ | create_strategy_ensemble ⚠ | discover_capabilities ⚠ | list_all_strategies ⚠ | get_strategy_help | get_decision_log ⚠ | get_tool_registry_status | create_signal | update_signal | list_signals ⚠ | delete_signal | check_signals_now | get_market_regime ⚠ | get_regime_history ⚠ | backtest_signal ⚠ | get_screening_changes ⚠ | get_screening_history ⚠ | schedule_screening ⚠ | get_screening_pipeline_status | journal_add_trade ⚠ | journal_close_trade ⚠ | journal_list_trades ⚠ | get_strategy_performance ⚠ | get_strategy_comparison ⚠ | journal_trade_review ⚠ | watchlist_create ⚠ | watchlist_add ⚠ | watchlist_remove ⚠ | watchlist_brief ⚠ | get_upcoming_catalysts ⚠ | get_portfolio_risk_dashboard ⚠ | get_position_risk_check ⚠ | get_regime_adjusted_sizing ⚠ | get_risk_alerts ⚠ | get_user_portfolio_summary ⚠ | get_watchlist ⚠ | get_market_overview ⚠ | get_economic_calendar ⚠ | get_mcp_connection_status | get_rsi_analysis ⚠ | get_macd_analysis ⚠ | get_support_resistance ⚠ | get_maverick_stocks ⚠ | get_my_portfolio ⚠ | get_full_technical_analysis ⚠ | get_maverick_bear_stocks ⚠ | get_supply_demand_breakouts ⚠ | get_all_screening_recommendations ⚠ | add_portfolio_position ⚠ | remove_portfolio_position ⚠ | portfolio_correlation_analysis ⚠ | compare_tickers ⚠ | risk_adjusted_analysis ⚠ | fetch_stock_data ⚠ | get_stock_info ⚠ | get_news_sentiment ⚠ | get_adanos_market_sentiment ⚠ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `market_data` | 1 | 2 | 4 | 1 | 4 | 4 | 4 | 4 | 4 | 4 | 1 | 4 | 2 | 1 | 4 | 4 | 4 | 1 | 4 | 1 | 4 | 4 | 4 | 2 | 4 | 4 | 2 | 4 | 4 | 4 | 2 | 4 | 2 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 1 | 4 | 2 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 1 | 4 | 4 | 4 | 4 | 2 | 4 | 4 | 4 | 4 | 2 | 4 | 2 | 2 | 2 | 4 | 2 | 4 | 1 | 4 | 4 | 4 | 4 | 2 | 2 | 1 | 1 | 4 | 4 | 4 | 2 | 2 | 2 | 1 | 4 | 4 | 4 | 1 | 2 | 4 | 4 | 4 | 4 | 4 | 2 | 1 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 1 | 1 | 4 | 4 | 1 | 4 | 1 | 4 | 4 |
| `watchlists` | 2 | 2 | 1 | 2 | 2 | 4 | 4 | 4 | 4 | 4 | 2 | 1 | 2 | 1 | 2 | 4 | 4 | 1 | 4 | 2 | 2 | 2 | 2 | 2 | 4 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 4 | 4 | 4 | 4 | 4 | 4 | 2 | 2 | 2 | 4 | 4 | 4 | 1 | 4 | 2 | 1 | 4 | 2 | 2 | 4 | 2 | 4 | 4 | 2 | 4 | 2 | 2 | 2 | 2 | 2 | 2 | 4 | 4 | 2 | 4 | 2 | 2 | 2 | 4 | 2 | 4 | 2 | 4 | 2 | 4 | 4 | 2 | 2 | 2 | 2 | 4 | 1 | 4 | 1 | 2 | 2 | 2 | 4 | 4 | 2 | 2 | 2 | 2 | 4 | 4 | 4 | 4 | 2 | 2 | 1 | 2 | 4 | 4 | 2 | 4 | 4 | 4 | 1 | 2 | 4 | 4 | 2 | 1 | 2 | 2 | 4 |
| `screening_results` | 1 | 1 | 2 | 1 | 1 | 4 | 4 | 4 | 4 | 4 | 2 | 1 | 2 | 2 | 1 | 4 | 4 | 1 | 4 | 1 | 1 | 1 | 1 | 1 | 4 | 4 | 1 | 1 | 1 | 1 | 1 | 4 | 1 | 4 | 1 | 4 | 4 | 1 | 4 | 4 | 1 | 1 | 4 | 4 | 2 | 1 | 4 | 1 | 1 | 2 | 1 | 4 | 4 | 1 | 4 | 4 | 1 | 4 | 1 | 1 | 1 | 1 | 1 | 4 | 4 | 4 | 1 | 4 | 1 | 1 | 2 | 4 | 2 | 4 | 1 | 4 | 4 | 4 | 4 | 2 | 2 | 1 | 1 | 4 | 4 | 4 | 1 | 1 | 2 | 1 | 4 | 4 | 1 | 1 | 2 | 1 | 4 | 4 | 4 | 4 | 1 | 1 | 1 | 1 | 4 | 4 | 1 | 4 | 4 | 4 | 2 | 1 | 4 | 4 | 4 | 1 | 1 | 1 | 4 |
| `portfolio_positions` | 2 | 1 | 2 | 2 | 1 | 4 | 4 | 5 | 4 | 4 | 2 | 4 | 2 | 5 | 4 | 5 | 5 | 1 | 4 | 1 | 1 | 2 | 1 | 1 | 4 | 2 | 1 | 2 | 2 | 2 | 2 | 1 | 2 | 4 | 4 | 4 | 5 | 4 | 4 | 2 | 2 | 2 | 5 | 4 | 4 | 1 | 4 | 2 | 4 | 4 | 2 | 2 | 4 | 2 | 4 | 4 | 1 | 4 | 2 | 2 | 2 | 1 | 2 | 5 | 2 | 2 | 2 | 5 | 2 | 2 | 2 | 5 | 2 | 4 | 1 | 4 | 4 | 4 | 4 | 1 | 2 | 2 | 2 | 4 | 4 | 4 | 1 | 1 | 2 | 1 | 5 | 2 | 4 | 2 | 1 | 2 | 2 | 4 | 5 | 2 | 2 | 1 | 2 | 2 | 4 | 4 | 1 | 5 | 4 | 4 | 2 | 2 | 4 | 4 | 2 | 1 | 2 | 2 | 2 |
| `account_and_orders` | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 5 | 5 | 2 | 5 | 2 | 5 | 2 | 2 | 5 | 2 | 5 | 2 | 2 | 2 | 2 | 1 | 4 | 2 | 2 | 2 | 2 | 3 | 2 | 2 | 2 | 4 | 4 | 5 | 5 | 2 | 5 | 1 | 2 | 2 | 5 | 5 | 4 | 2 | 5 | 2 | 5 | 4 | 2 | 2 | 2 | 2 | 5 | 2 | 2 | 5 | 2 | 2 | 2 | 2 | 1 | 3 | 1 | 2 | 2 | 5 | 1 | 2 | 2 | 5 | 2 | 4 | 2 | 5 | 5 | 5 | 2 | 2 | 2 | 2 | 2 | 5 | 4 | 5 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 5 | 2 | 2 | 2 | 2 | 2 | 2 | 5 | 2 | 2 | 5 | 5 | 2 | 2 | 5 | 5 | 2 | 2 | 2 | 2 | 1 |
| `server_api_credentials` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 2 | 5 | 2 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 2 | 5 | 2 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 1 |

### Model-vs-derived blast mismatches

_Authoritative blast is derived in code from the reach classification, so the matrix above is consistent by construction. These are cells where the model's OWN number disagreed with the derived one — usually sensitivity leaking into its reach call, a classification-quality signal._

| tool | asset | model | derived |
| --- | --- | --- | --- |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `technical_get_rsi_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `technical_get_macd_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `technical_get_support_resistance` | **READ** | 2 (Low) | READ | verb-fallback |
| `technical_get_full_technical_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `technical_get_stock_chart_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `screening_get_maverick_stocks` | **READ** | 2 (Low) | READ | verb-fallback |
| `screening_get_maverick_bear_stocks` | **READ** | 2 (Low) | READ | verb-fallback |
| `screening_get_supply_demand_breakouts` | **READ** | 2 (Low) | READ | verb-fallback |
| `screening_get_all_screening_recommendations` | **READ** | 2 (Low) | READ | verb-fallback |
| `screening_get_screening_by_criteria` | **READ** | 2 (Low) | READ | verb-fallback |
| `portfolio_add_position` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `portfolio_get_my_portfolio` | **READ** | 2 (Low) | READ | verb-fallback |
| `portfolio_remove_position` | **DELETE** | 5 (Critical) | DELETE | verb-fallback |
| `portfolio_clear_portfolio` | **DELETE** | 5 (Critical) | DELETE | verb-fallback |
| `portfolio_risk_adjusted_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `portfolio_compare_tickers` | **READ** | 2 (Low) | READ | verb-fallback |
| `portfolio_portfolio_correlation_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `data_fetch_stock_data` | **READ** | 2 (Low) | READ | verb-fallback |
| `data_fetch_stock_data_batch` | **READ** | 2 (Low) | READ | verb-fallback |
| `data_get_stock_info` | **METADATA** | 1 (Low) | METADATA | rules |
| `data_get_adanos_market_sentiment` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `data_get_news_sentiment` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `data_get_cached_price_data` | **READ** | 2 (Low) | READ | verb-fallback |
| `data_get_chart_links` | **READ** | 2 (Low) | READ | verb-fallback |
| `data_clear_cache` | **DELETE** | 5 (Critical) | DELETE | verb-fallback |
| `performance_get_system_performance_health` | **READ** | 2 (Low) | READ | verb-fallback |
| `performance_get_redis_health_status` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `performance_get_cache_performance_status` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `performance_get_database_performance_status` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `performance_analyze_database_index_usage` | **READ** | 2 (Low) | READ | verb-fallback |
| `performance_optimize_cache_configuration` | **READ** | 2 (Low) | READ | verb-fallback |
| `performance_clear_system_caches` | **DELETE** | 5 (Critical) | DELETE | verb-fallback |
| `agents_list_available_agents` | **LIST** | 1 (Low) | LIST | verb-fallback |
| `agents_analyze_market_with_agent` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `agents_get_agent_streaming_analysis` | **MODIFY** | 3 (Medium) | MODIFY | rules |
| `agents_compare_personas_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `agents_orchestrated_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `agents_deep_research_financial` | **SEARCH** | 2 (Low) | SEARCH | verb-fallback |
| `agents_compare_multi_agent_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `research_comprehensive_research` | **SEARCH** | 2 (Low) | SEARCH | verb-fallback |
| `research_company_comprehensive` | **SEARCH** | 2 (Low) | SEARCH | verb-fallback |
| `research_analyze_market_sentiment` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `get_system_health` | **READ** | 2 (Low) | READ | rules |
| `get_component_status` | **METADATA** | 1 (Low) | METADATA | rules |
| `get_circuit_breaker_status` | **METADATA** | 1 (Low) | METADATA | rules |
| `get_resource_usage` | **READ** | 2 (Low) | READ | rules |
| `get_status_dashboard` | **METADATA** | 1 (Low) | METADATA | rules |
| `reset_circuit_breaker` | **MODIFY** | 3 (Medium) | MODIFY | rules |
| `get_health_history` | **READ** | 2 (Low) | READ | rules |
| `run_health_diagnostics` | **EXECUTE** | 5 (Critical) | EXECUTE | rules |
| `run_backtest` | **EXECUTE** | 5 (Critical) | EXECUTE | rules |
| `optimize_strategy` | **READ** | 2 (Low) | READ | verb-fallback |
| `walk_forward_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `monte_carlo_simulation` | **READ** | 2 (Low) | READ | verb-fallback |
| `compare_strategies` | **READ** | 2 (Low) | READ | verb-fallback |
| `list_strategies` | **LIST** | 1 (Low) | LIST | rules |
| `parse_strategy` | **READ** | 2 (Low) | READ | verb-fallback |
| `backtest_portfolio` | **READ** | 2 (Low) | READ | verb-fallback |
| `generate_backtest_charts` | **READ** | 2 (Low) | READ | verb-fallback |
| `generate_optimization_charts` | **READ** | 2 (Low) | READ | verb-fallback |
| `run_ml_strategy_backtest` | **EXECUTE** | 5 (Critical) | EXECUTE | rules |
| `train_ml_predictor` | **READ** | 2 (Low) | READ | verb-fallback |
| `analyze_market_regimes` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `create_strategy_ensemble` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `discover_capabilities` | **READ** | 2 (Low) | READ | verb-fallback |
| `list_all_strategies` | **LIST** | 1 (Low) | LIST | rules |
| `get_strategy_help` | **READ** | 2 (Low) | READ | rules |
| `get_decision_log` | **READ** | 2 (Low) | READ | rules |
| `get_tool_registry_status` | **METADATA** | 1 (Low) | METADATA | rules |
| `create_signal` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `update_signal` | **MODIFY** | 3 (Medium) | MODIFY | rules |
| `list_signals` | **LIST** | 1 (Low) | LIST | rules |
| `delete_signal` | **DELETE** | 5 (Critical) | DELETE | rules |
| `check_signals_now` | **READ** | 2 (Low) | READ | verb-fallback |
| `get_market_regime` | **READ** | 2 (Low) | READ | rules |
| `get_regime_history` | **READ** | 2 (Low) | READ | rules |
| `backtest_signal` | **READ** | 2 (Low) | READ | verb-fallback |
| `get_screening_changes` | **READ** | 2 (Low) | READ | rules |
| `get_screening_history` | **READ** | 2 (Low) | READ | rules |
| `schedule_screening` | **READ** | 2 (Low) | READ | verb-fallback |
| `get_screening_pipeline_status` | **METADATA** | 1 (Low) | METADATA | rules |
| `journal_add_trade` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `journal_close_trade` | **READ** | 2 (Low) | READ | verb-fallback |
| `journal_list_trades` | **LIST** | 1 (Low) | LIST | verb-fallback |
| `get_strategy_performance` | **READ** | 2 (Low) | READ | rules |
| `get_strategy_comparison` | **READ** | 2 (Low) | READ | rules |
| `journal_trade_review` | **READ** | 2 (Low) | READ | verb-fallback |
| `watchlist_create` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `watchlist_add` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `watchlist_remove` | **DELETE** | 5 (Critical) | DELETE | verb-fallback |
| `watchlist_brief` | **LIST** | 1 (Low) | LIST | verb-fallback |
| `get_upcoming_catalysts` | **READ** | 2 (Low) | READ | rules |
| `get_portfolio_risk_dashboard` | **READ** | 2 (Low) | READ | rules |
| `get_position_risk_check` | **READ** | 2 (Low) | READ | rules |
| `get_regime_adjusted_sizing` | **READ** | 2 (Low) | READ | rules |
| `get_risk_alerts` | **READ** | 2 (Low) | READ | rules |
| `get_user_portfolio_summary` | **READ** | 2 (Low) | READ | rules |
| `get_watchlist` | **READ** | 2 (Low) | READ | rules |
| `get_market_overview` | **READ** | 2 (Low) | READ | rules |
| `get_economic_calendar` | **READ** | 2 (Low) | READ | rules |
| `get_mcp_connection_status` | **METADATA** | 1 (Low) | METADATA | rules |
| `get_rsi_analysis` | **READ** | 2 (Low) | READ | rules |
| `get_macd_analysis` | **READ** | 2 (Low) | READ | rules |
| `get_support_resistance` | **READ** | 2 (Low) | READ | rules |
| `get_maverick_stocks` | **READ** | 2 (Low) | READ | rules |
| `get_my_portfolio` | **READ** | 2 (Low) | READ | rules |
| `get_full_technical_analysis` | **READ** | 2 (Low) | READ | rules |
| `get_maverick_bear_stocks` | **READ** | 2 (Low) | READ | rules |
| `get_supply_demand_breakouts` | **READ** | 2 (Low) | READ | rules |
| `get_all_screening_recommendations` | **READ** | 2 (Low) | READ | rules |
| `add_portfolio_position` | **WRITE** | 3 (Medium) | WRITE | rules |
| `remove_portfolio_position` | **DELETE** | 5 (Critical) | DELETE | rules |
| `portfolio_correlation_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `compare_tickers` | **READ** | 2 (Low) | READ | verb-fallback |
| `risk_adjusted_analysis` | **READ** | 2 (Low) | READ | verb-fallback |
| `fetch_stock_data` | **READ** | 2 (Low) | READ | rules |
| `get_stock_info` | **METADATA** | 1 (Low) | METADATA | rules |
| `get_news_sentiment` | **READ** | 2 (Low) | READ | rules |
| `get_adanos_market_sentiment` | **READ** | 2 (Low) | READ | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `technical_get_rsi_analysis` | `days` | 4 | >= 10000 | high values can significantly increase data retrieval and pr |
| `technical_get_rsi_analysis` | `period` | 3 | >= 1000 | can amplify computational load if set very high |
| `technical_get_rsi_analysis` | `ticker` | 2 | — | merely names the target |
| `technical_get_macd_analysis` | `days` | 4 | >= 10000 | large magnitude can lead to significant resource consumption |
| `technical_get_macd_analysis` | `fast_period` | 3 | >= 1000 | can cause excessive data processing if set too high |
| `technical_get_macd_analysis` | `slow_period` | 3 | >= 1000 | can cause excessive data processing if set too high |
| `technical_get_macd_analysis` | `signal_period` | 3 | >= 1000 | can cause excessive data processing if set too high |
| `technical_get_macd_analysis` | `ticker` | 2 | — | merely names the target |
| `technical_get_support_resistance` | `days` | 4 | >= 1095 | can amplify data retrieval and processing load |
| `technical_get_support_resistance` | `ticker` | 2 | — | merely names the target |
| `technical_get_full_technical_analysis` | `days` | 4 | >= 1095 | can amplify server load by requesting extensive historical d |
| `technical_get_full_technical_analysis` | `ticker` | 2 | — | merely names the target |
| `technical_get_stock_chart_analysis` | `ticker` | 2 | — | merely names the target |
| `screening_get_maverick_stocks` | `limit` | 3 | >= 1000 | Can cause excessive data retrieval |
| `screening_get_maverick_bear_stocks` | `limit` | 3 | >= 100 | Potentially large data retrieval |
| `screening_get_supply_demand_breakouts` | `limit` | 4 | >= 1000 | Can cause excessive data retrieval |
| `screening_get_supply_demand_breakouts` | `filter_moving_averages` | 2 | — | Boolean flag with limited impact on server load |
| `screening_get_screening_by_criteria` | `limit` | 4 | >= 500 | can significantly increase the number of results returned, p |
| `screening_get_screening_by_criteria` | `min_volume` | 3 | — | can filter out low-volume stocks but doesn't inherently ampl |
| `screening_get_screening_by_criteria` | `min_momentum_score` | 2 | — | limits the scope to a specific score range |
| `screening_get_screening_by_criteria` | `max_price` | 2 | — | limits the scope to a specific price range |
| `screening_get_screening_by_criteria` | `sector` | 1 | — | narrowly defines the sector, reducing potential risk |
| `portfolio_add_position` | `shares` | 4 | shares >= 1000000 | large magnitude can overwhelm server resources or skew portf |
| `portfolio_add_position` | `purchase_price` | 3 | purchase_price >= 1000000 | high price per share could lead to unrealistic financial cal |
| `portfolio_add_position` | `notes` | 3 | — | potentially large text input could be used for injection att |
| `portfolio_add_position` | `ticker` | 2 | — | merely identifies the stock |
| `portfolio_add_position` | `purchase_date` | 1 | — | only affects date context, not server load or data integrity |
| `portfolio_add_position` | `user_id` | 1 | — | identifies the user, no direct risk amplification |
| `portfolio_add_position` | `portfolio_name` | 1 | — | merely names the portfolio, no direct risk amplification |
| `portfolio_get_my_portfolio` | `include_current_prices` | 3 | — | can increase server load by fetching live prices |
| `portfolio_get_my_portfolio` | `user_id` | 2 | — | merely names the target |
| `portfolio_get_my_portfolio` | `portfolio_name` | 1 | — | names a specific portfolio, low risk |
| `portfolio_remove_position` | `shares` | 4 | shares >= 100000 | controls the magnitude of shares to remove, potentially lead |
| `portfolio_remove_position` | `ticker` | 2 | — | merely names the target |
| `portfolio_remove_position` | `user_id` | 2 | — | merely identifies the user |
| `portfolio_remove_position` | `portfolio_name` | 2 | — | merely names the portfolio |
| `portfolio_clear_portfolio` | `confirm` | 5 | True | enables destructive action |
| `portfolio_clear_portfolio` | `user_id` | 2 | — | merely names the target |
| `portfolio_clear_portfolio` | `portfolio_name` | 2 | — | merely names the target |
| `portfolio_risk_adjusted_analysis` | `risk_level` | 3 | risk_level >= 90 | can influence aggressive investment behavior |
| `portfolio_risk_adjusted_analysis` | `ticker` | 2 | — | merely names the target |
| `portfolio_risk_adjusted_analysis` | `user_id` | 1 | — | identifies the user, low risk |
| `portfolio_risk_adjusted_analysis` | `portfolio_name` | 1 | — | names the portfolio, no direct impact on server risk |
| `portfolio_compare_tickers` | `tickers` | 4 | >= 100 tickers | large breadth can overwhelm server resources |
| `portfolio_compare_tickers` | `days` | 3 | >= 365 days | longer historical data requests increase load |
| `portfolio_compare_tickers` | `user_id` | 1 | — | merely identifies the user, no amplifying effect |
| `portfolio_compare_tickers` | `portfolio_name` | 1 | — | names the portfolio, no amplifying effect |
| `portfolio_portfolio_correlation_analysis` | `tickers` | 4 | >= 100 tickers | large list can cause excessive data retrieval and processing |
| `portfolio_portfolio_correlation_analysis` | `days` | 2 | >= 3650 days (10 years) | longer periods may lead to performance degradation due to la |
| `portfolio_portfolio_correlation_analysis` | `user_id` | 1 | — | merely identifies the user, no amplifying effect on risk |
| `portfolio_portfolio_correlation_analysis` | `portfolio_name` | 1 | — | only names the portfolio, does not affect server load or sec |
| `data_fetch_stock_data` | `start_date` | 3 | start_date <= 1900-01-01 | can potentially request a large amount of historical data |
| `data_fetch_stock_data` | `end_date` | 3 | end_date >= 2100-01-01 | can potentially request future or very long-term data range |
| `data_fetch_stock_data` | `ticker` | 2 | — | merely names the target |
| `data_fetch_stock_data_batch` | `tickers` | 4 | >= 100 tickers | large breadth can overwhelm server resources |
| `data_fetch_stock_data_batch` | `start_date` | 2 | — | defines historical data range, but not inherently risky |
| `data_fetch_stock_data_batch` | `end_date` | 2 | — | defines historical data range, but not inherently risky |
| `data_get_stock_info` | `ticker` | 2 | — | merely names the target |
| `data_get_adanos_market_sentiment` | `sources` | 5 | length >= 10 | list length can cause bulk fan-out, increasing server load |
| `data_get_adanos_market_sentiment` | `days` | 4 | >= 365 | can amplify data retrieval scope and load |
| `data_get_adanos_market_sentiment` | `ticker` | 2 | — | merely names the target |
| `data_get_news_sentiment` | `limit` | 4 | >= 100 | controls the breadth (bulk fan-out) of news articles to anal |
| `data_get_news_sentiment` | `timeframe` | 3 | — | can widen scope of data retrieval |
| `data_get_news_sentiment` | `ticker` | 2 | — | merely names the target |
| `data_get_cached_price_data` | `end_date` | 4 | — | potentially unbounded, can request large date ranges |
| `data_get_cached_price_data` | `start_date` | 3 | — | can widen data scope over time |
| `data_get_cached_price_data` | `ticker` | 2 | — | merely names the target |
| `data_get_chart_links` | `ticker` | 2 | — | merely names the target |
| `data_clear_cache` | `ticker` | 4 | — | Can clear all cached data if set to None, affecting server p |
| `performance_get_system_performance_health` | `request` | 4 | — | potentially contains arbitrary data that could be misused |
| `performance_clear_system_caches` | `request` | 4 | — | Controls the types of caches to clear, potentially affecting |
| `agents_analyze_market_with_agent` | `query` | 5 | — | Free-form input can be abused for injection attacks |
| `agents_analyze_market_with_agent` | `screening_strategy` | 4 | — | May alter how data is processed or filtered, possibly exposi |
| `agents_analyze_market_with_agent` | `persona` | 3 | — | Can influence the AI's behavior, potentially leading to unin |
| `agents_analyze_market_with_agent` | `max_results` | 2 | >= 1000 | Limits the number of results returned; high values can lead  |
| `agents_analyze_market_with_agent` | `session_id` | 1 | — | Identifies a session, typically low risk unless used for ses |
| `agents_get_agent_streaming_analysis` | `query` | 5 | — | Free-form input can be exploited for injection attacks |
| `agents_get_agent_streaming_analysis` | `persona` | 3 | — | Potentially used to impersonate or mislead the AI agent |
| `agents_get_agent_streaming_analysis` | `stream_mode` | 2 | — | May affect how data is processed but not inherently risky |
| `agents_get_agent_streaming_analysis` | `session_id` | 1 | — | Identifies the session, no direct risk amplification |
| `agents_compare_personas_analysis` | `query` | 4 | — | potentially complex and unvalidated input |
| `agents_compare_personas_analysis` | `session_id` | 1 | — | likely a simple identifier |
| `agents_orchestrated_analysis` | `query` | 5 | — | Free-form input can be exploited for injection attacks |
| `agents_orchestrated_analysis` | `max_agents` | 4 | >= 100 | High count can lead to resource exhaustion or excessive load |
| `agents_orchestrated_analysis` | `persona` | 3 | — | Potentially used to impersonate roles, leading to unauthoriz |
| `agents_orchestrated_analysis` | `parallel_execution` | 3 | — | Enables concurrent operations which could overwhelm resource |
| `agents_orchestrated_analysis` | `routing_strategy` | 2 | — | Could influence how tasks are distributed but is less likely |
| `agents_orchestrated_analysis` | `session_id` | 1 | — | Identifies a session, less likely to be exploitable on its o |
| `agents_deep_research_financial` | `focus_areas` | 5 | >= 10 focus areas | can broaden the scope of research and potentially overwhelm  |
| `agents_deep_research_financial` | `research_depth` | 4 | — | can significantly increase computational load if set to a hi |
| `agents_deep_research_financial` | `research_topic` | 3 | — | can be used to target sensitive financial information |
| `agents_deep_research_financial` | `persona` | 2 | — | may influence the perspective and depth of research, but lim |
| `agents_deep_research_financial` | `timeframe` | 2 | — | defines temporal scope but is unlikely to cause significant  |
| `agents_deep_research_financial` | `session_id` | 1 | — | identifies the session and does not directly influence serve |
| `agents_compare_multi_agent_analysis` | `query` | 5 | — | Free-form input can be abused for injection attacks |
| `agents_compare_multi_agent_analysis` | `agent_types` | 4 | >= 10 types | Bulk fan-out increases the scope of potential abuse |
| `agents_compare_multi_agent_analysis` | `persona` | 2 | — | Names a target or role, limited impact without further conte |
| `agents_compare_multi_agent_analysis` | `session_id` | 1 | — | Identifies session, typically low risk unless used for sessi |
| `research_comprehensive_research` | `research_scope` | 5 | exhaustive | Can significantly increase server load with exhaustive scope |
| `research_comprehensive_research` | `query` | 4 | — | Free-form input can be abused for malicious web searches |
| `research_comprehensive_research` | `max_sources` | 3 | >= 20 | Higher number of sources increases processing load |
| `research_comprehensive_research` | `persona` | 2 | — | Limited to predefined investor personas, low risk |
| `research_comprehensive_research` | `timeframe` | 1 | — | Limited to predefined time frames, low risk |
| `research_company_comprehensive` | `persona` | 5 | — | potentially free-form input with undefined behavior |
| `research_company_comprehensive` | `include_competitive_analysis` | 3 | — | can widen scope of analysis |
| `research_company_comprehensive` | `symbol` | 2 | — | merely names the target |
| `research_analyze_market_sentiment` | `persona` | 4 | — | potentially allows for broad, undefined scope of analysis |
| `research_analyze_market_sentiment` | `timeframe` | 3 | — | could be used to request an unbounded or excessively long ti |
| `research_analyze_market_sentiment` | `topic` | 2 | — | merely names the target |
| `get_component_status` | `component_name` | 2 | — | merely names the target |
| `reset_circuit_breaker` | `breaker_name` | 2 | — | merely names the target |
| `run_backtest` | `initial_capital` | 4 | >= 1000000 | large magnitude can amplify resource usage |
| `run_backtest` | `start_date` | 3 | — | can extend backtest duration |
| `run_backtest` | `end_date` | 3 | — | can extend backtest duration |
| `run_backtest` | `period` | 3 | — | can widen the scope of data considered |
| `run_backtest` | `signal_period` | 3 | — | can widen the scope of data considered |
| `run_backtest` | `lookback` | 3 | — | can widen the scope of data considered |
| `run_backtest` | `breakout_factor` | 3 | — | can widen the scope of data considered |
| `run_backtest` | `symbol` | 2 | — | merely names the target |
| `run_backtest` | `fast_period` | 2 | — | can affect backtest performance but limited in scope |
| `run_backtest` | `slow_period` | 2 | — | can affect backtest performance but limited in scope |
| `run_backtest` | `oversold` | 2 | — | affects backtest logic but limited in scope |
| `run_backtest` | `overbought` | 2 | — | affects backtest logic but limited in scope |
| `run_backtest` | `std_dev` | 2 | — | affects backtest logic but limited in scope |
| `run_backtest` | `threshold` | 2 | — | affects backtest logic but limited in scope |
| `run_backtest` | `z_score_threshold` | 2 | — | affects backtest logic but limited in scope |
| `run_backtest` | `strategy` | 1 | — | fixed enum/structural field |
| `optimize_strategy` | `top_n` | 5 | >= 1000 | controls the number of results, potentially leading to high  |
| `optimize_strategy` | `optimization_level` | 4 | — | can significantly increase computational load and time |
| `optimize_strategy` | `strategy` | 3 | — | could potentially execute arbitrary or complex strategies |
| `optimize_strategy` | `symbol` | 2 | — | merely names the target |
| `optimize_strategy` | `optimization_metric` | 2 | — | selects the metric to optimize but does not control executio |
| `optimize_strategy` | `start_date` | 1 | — | defines a start point, not inherently risky |
| `optimize_strategy` | `end_date` | 1 | — | defines an end point, not inherently risky |
| `walk_forward_analysis` | `window_size` | 4 | >= 3650 | can significantly increase computational load |
| `walk_forward_analysis` | `step_size` | 4 | <= 1 | small step size can lead to excessive computation |
| `walk_forward_analysis` | `strategy` | 3 | — | could introduce unknown or malicious logic |
| `walk_forward_analysis` | `symbol` | 2 | — | merely names the target |
| `walk_forward_analysis` | `start_date` | 2 | — | defines the analysis period start, limited impact |
| `walk_forward_analysis` | `end_date` | 2 | — | defines the analysis period end, limited impact |
| `monte_carlo_simulation` | `num_simulations` | 5 | >= 10000 | large magnitude can overwhelm server resources |
| `monte_carlo_simulation` | `strategy` | 3 | — | could imply complex or resource-intensive operations |
| `monte_carlo_simulation` | `symbol` | 2 | — | merely names the target |
| `monte_carlo_simulation` | `fast_period` | 2 | — | could affect simulation scope but not directly risky |
| `monte_carlo_simulation` | `slow_period` | 2 | — | could affect simulation scope but not directly risky |
| `monte_carlo_simulation` | `period` | 2 | — | could affect simulation scope but not directly risky |
| `monte_carlo_simulation` | `start_date` | 1 | — | defines a start point without amplifying risk |
| `monte_carlo_simulation` | `end_date` | 1 | — | defines an end point without amplifying risk |
| `compare_strategies` | `strategies` | 4 | >= 10 strategies | can cause bulk fan-out |
| `compare_strategies` | `symbol` | 2 | — | merely names the target |
| `compare_strategies` | `start_date` | 2 | — | defines a start point, not inherently risky |
| `compare_strategies` | `end_date` | 2 | — | defines an end point, not inherently risky |
| `parse_strategy` | `description` | 3 | — | potentially complex and unbounded input |
| `backtest_portfolio` | `symbols` | 4 | >= 100 symbols | large breadth can overwhelm server |
| `backtest_portfolio` | `initial_capital` | 3 | >= 1000000 | large capital can amplify computational load |
| `backtest_portfolio` | `strategy` | 2 | — | names a strategy type |
| `backtest_portfolio` | `position_size` | 2 | — | defines position size per symbol |
| `backtest_portfolio` | `start_date` | 1 | — | defines start date for backtesting |
| `backtest_portfolio` | `end_date` | 1 | — | defines end date for backtesting |
| `backtest_portfolio` | `fast_period` | 1 | — | likely a technical indicator parameter |
| `backtest_portfolio` | `slow_period` | 1 | — | likely a technical indicator parameter |
| `backtest_portfolio` | `period` | 1 | — | likely a technical indicator parameter |
| `generate_backtest_charts` | `strategy` | 3 | — | could potentially execute complex or resource-intensive stra |
| `generate_backtest_charts` | `symbol` | 2 | — | merely names the target |
| `generate_backtest_charts` | `start_date` | 2 | — | defines the start of data range, but not inherently risky |
| `generate_backtest_charts` | `end_date` | 2 | — | defines the end of data range, but not inherently risky |
| `generate_backtest_charts` | `theme` | 1 | — | affects only visual appearance and is limited to two options |
| `generate_optimization_charts` | `strategy` | 3 | — | could imply complex or resource-intensive computations |
| `generate_optimization_charts` | `symbol` | 2 | — | merely names the target |
| `generate_optimization_charts` | `start_date` | 2 | — | defines the start of data range, but not inherently risky |
| `generate_optimization_charts` | `end_date` | 2 | — | defines the end of data range, but not inherently risky |
| `generate_optimization_charts` | `theme` | 1 | — | affects only visual appearance and is limited to two options |
| `run_ml_strategy_backtest` | `initial_capital` | 4 | >= 100000 | large magnitude can amplify financial risk |
| `run_ml_strategy_backtest` | `n_estimators` | 4 | >= 500 | large count can lead to resource exhaustion |
| `run_ml_strategy_backtest` | `max_depth` | 4 | unbounded (no LIMIT) | can lead to deep recursion or excessive computation |
| `run_ml_strategy_backtest` | `start_date` | 3 | — | can widen data scope if set too far back |
| `run_ml_strategy_backtest` | `end_date` | 3 | — | can widen data scope if set too far forward |
| `run_ml_strategy_backtest` | `symbol` | 2 | — | merely names the target |
| `run_ml_strategy_backtest` | `train_ratio` | 2 | — | can affect data usage but not directly risky |
| `run_ml_strategy_backtest` | `learning_rate` | 2 | — | affects model training but not directly risky |
| `run_ml_strategy_backtest` | `strategy_type` | 1 | — | fixed enum/structural field |
| `run_ml_strategy_backtest` | `model_type` | 1 | — | fixed enum/structural field |
| `run_ml_strategy_backtest` | `adaptation_method` | 1 | — | fixed enum/structural field |
| `train_ml_predictor` | `n_estimators` | 5 | >= 1000 | high count can lead to resource exhaustion |
| `train_ml_predictor` | `target_periods` | 4 | >= 50 | can amplify the scope of prediction |
| `train_ml_predictor` | `max_depth` | 4 | — | can influence model complexity and resource usage |
| `train_ml_predictor` | `start_date` | 3 | — | can be used to manipulate data range |
| `train_ml_predictor` | `end_date` | 3 | — | can be used to manipulate data range |
| `train_ml_predictor` | `return_threshold` | 3 | — | can influence signal classification |
| `train_ml_predictor` | `min_samples_split` | 3 | — | can affect the granularity of splits |
| `train_ml_predictor` | `symbol` | 2 | — | merely names the target |
| `train_ml_predictor` | `model_type` | 1 | — | fixed enum/structural field |
| `analyze_market_regimes` | `lookback_period` | 5 | unbounded (no LIMIT) | can significantly widen the scope and increase computational |
| `analyze_market_regimes` | `n_regimes` | 4 | >= 100 | large magnitude can amplify computational load |
| `analyze_market_regimes` | `start_date` | 3 | — | can potentially widen analysis scope |
| `analyze_market_regimes` | `end_date` | 3 | — | can potentially widen analysis scope |
| `analyze_market_regimes` | `symbol` | 2 | — | merely names the target |
| `analyze_market_regimes` | `method` | 2 | — | fixed enum/structural field |
| `create_strategy_ensemble` | `symbols` | 4 | >= 100 symbols | large breadth can overwhelm server resources |
| `create_strategy_ensemble` | `base_strategies` | 3 | — | potentially large list, but impact depends on strategy imple |
| `create_strategy_ensemble` | `initial_capital` | 3 | >= 1000000 | large magnitude can lead to resource-intensive computations |
| `create_strategy_ensemble` | `start_date` | 2 | — | can affect data volume, but not directly a risk factor |
| `create_strategy_ensemble` | `end_date` | 2 | — | can affect data volume, but not directly a risk factor |
| `create_strategy_ensemble` | `weighting_method` | 1 | — | fixed enum/structural field with limited options |
| `get_strategy_help` | `strategy_type` | 2 | — | merely names the target |
| `get_decision_log` | `limit` | 4 | >= 100 | controls breadth of data retrieval |
| `get_decision_log` | `session_id` | 2 | — | names the target, limited scope |
| `create_signal` | `condition` | 5 | — | can specify complex and potentially abusive conditions |
| `create_signal` | `interval_seconds` | 3 | >= 604800 | large magnitude can lead to excessive resource usage over ti |
| `create_signal` | `label` | 2 | — | merely names the target |
| `create_signal` | `ticker` | 1 | — | names the financial instrument, low risk |
| `update_signal` | `condition` | 5 | — | potentially complex and arbitrary, can lead to unintended be |
| `update_signal` | `interval_seconds` | 4 | >= 10 | can cause excessive resource usage if set too low |
| `update_signal` | `label` | 3 | — | can be used to mislead or obfuscate |
| `update_signal` | `active` | 3 | — | enables or disables the signal, potentially affecting system |
| `update_signal` | `signal_id` | 2 | — | merely identifies the target |
| `list_signals` | `active_only` | 2 | — | limits output to active signals, reducing potential informat |
| `delete_signal` | `signal_id` | 2 | — | merely names the target |
| `get_regime_history` | `days` | 3 | >= 1000 | potentially large data retrieval |
| `backtest_signal` | `initial_capital` | 4 | >= 100000 | large magnitude can amplify computational load and financial |
| `backtest_signal` | `signal_id` | 2 | — | merely names the target |
| `backtest_signal` | `start_date` | 1 | — | defines a fixed point in time, low risk |
| `backtest_signal` | `end_date` | 1 | — | defines a fixed point in time, low risk |
| `get_screening_changes` | `limit` | 4 | >= 1000 | controls the breadth of data retrieved |
| `get_screening_changes` | `screen_name` | 2 | — | merely names the target |
| `get_screening_history` | `screen_name` | 3 | — | can potentially filter a large set of data, widening scope |
| `get_screening_history` | `symbol` | 2 | — | merely names the target |
| `schedule_screening` | `interval_minutes` | 4 | >= 1 | can cause frequent execution, amplifying resource usage |
| `schedule_screening` | `screen_name` | 2 | — | merely names the target |
| `journal_add_trade` | `rationale` | 5 | — | free-form query/command that caller fully controls |
| `journal_add_trade` | `notes` | 5 | — | free-form query/command that caller fully controls |
| `journal_add_trade` | `shares` | 4 | >= 100000 | large magnitude can overwhelm system resources or indicate f |
| `journal_add_trade` | `entry_price` | 3 | — | can be manipulated to misrepresent trade value |
| `journal_add_trade` | `tags` | 3 | unbounded (no LIMIT) | can be used to bulk fan-out or inject malicious data |
| `journal_add_trade` | `symbol` | 2 | — | merely names the target |
| `journal_add_trade` | `side` | 1 | — | fixed enum/structural field |
| `journal_close_trade` | `exit_price` | 4 | abs(exit_price) >= 100000 | can manipulate PnL calculation significantly |
| `journal_close_trade` | `notes` | 3 | — | potentially carries arbitrary data, could be abused for inje |
| `journal_close_trade` | `entry_id` | 2 | — | merely identifies the trade |
| `journal_list_trades` | `limit` | 4 | >= 1000 | controls the breadth of data retrieval |
| `journal_list_trades` | `symbol` | 2 | — | merely names the target |
| `journal_list_trades` | `strategy_tag` | 2 | — | merely names the target |
| `journal_list_trades` | `status` | 1 | — | likely a fixed enum/structural field |
| `get_strategy_performance` | `strategy_tag` | 2 | — | merely names the target |
| `journal_trade_review` | `entry_id` | 2 | — | merely names the target |
| `watchlist_create` | `description` | 3 | — | potentially carries arbitrary data that could be misused if  |
| `watchlist_create` | `name` | 2 | — | merely names the target |
| `watchlist_add` | `notes` | 4 | — | fully controlled payload with potential for abuse in content |
| `watchlist_add` | `symbol` | 3 | — | can be used to target specific financial instruments |
| `watchlist_add` | `watchlist_id` | 2 | — | merely names the target |
| `watchlist_remove` | `symbol` | 3 | — | could be used to target specific, potentially critical symbo |
| `watchlist_remove` | `watchlist_id` | 2 | — | merely names the target |
| `watchlist_brief` | `watchlist_id` | 2 | — | merely names the target |
| `get_upcoming_catalysts` | `symbols` | 4 | >= 100 symbols | bulk fan-out |
| `get_upcoming_catalysts` | `days_ahead` | 2 | — | limited scope widening |
| `get_portfolio_risk_dashboard` | `portfolio_name` | 2 | — | merely names the target |
| `get_position_risk_check` | `shares` | 4 | shares >= 1000000 | large magnitude can amplify risk through bulk transactions |
| `get_position_risk_check` | `entry_price` | 3 | — | can influence the projected metrics but is bounded by market |
| `get_position_risk_check` | `ticker` | 2 | — | merely names the target |
| `get_position_risk_check` | `portfolio_name` | 1 | — | merely names the target portfolio |
| `get_regime_adjusted_sizing` | `risk_pct` | 5 | >= 100 | high percentage directly amplifies risk exposure |
| `get_regime_adjusted_sizing` | `account_size` | 4 | >= 100000 | large magnitude can amplify financial risk |
| `get_regime_adjusted_sizing` | `stop_loss` | 3 | <= 0.1 * account_size | low stop loss can lead to significant financial losses |
| `get_regime_adjusted_sizing` | `entry_price` | 2 | — | controls the entry point but not directly amplifying risk |
| `get_risk_alerts` | `portfolio_name` | 2 | — | merely names the target |
| `get_watchlist` | `limit` | 3 | >= 1000 | can cause excessive data retrieval |
| `get_economic_calendar` | `days_ahead` | 3 | >= 100 | potentially large data request |
| `get_rsi_analysis` | `days` | 4 | >= 10000 | high values can significantly increase data retrieval and pr |
| `get_rsi_analysis` | `period` | 3 | >= 1000 | can amplify computational load if set very high |
| `get_rsi_analysis` | `ticker` | 2 | — | merely names the target |
| `get_macd_analysis` | `days` | 4 | >= 10000 | large magnitude can lead to significant resource consumption |
| `get_macd_analysis` | `fast_period` | 3 | >= 1000 | can cause excessive data processing if too large |
| `get_macd_analysis` | `slow_period` | 3 | >= 1000 | can cause excessive data processing if too large |
| `get_macd_analysis` | `signal_period` | 3 | >= 1000 | can cause excessive data processing if too large |
| `get_macd_analysis` | `ticker` | 2 | — | merely names the target |
| `get_support_resistance` | `days` | 4 | >= 1095 | can amplify data retrieval and processing load |
| `get_support_resistance` | `ticker` | 2 | — | merely names the target |
| `get_maverick_stocks` | `limit` | 3 | >= 100 | can increase server load by requesting a large number of sto |
| `get_my_portfolio` | `include_current_prices` | 2 | — | Boolean flag with limited impact |
| `get_full_technical_analysis` | `days` | 4 | >= 1095 | can amplify data retrieval and processing load |
| `get_full_technical_analysis` | `ticker` | 2 | — | merely names the target |
| `get_maverick_bear_stocks` | `limit` | 3 | >= 100 | Can increase server load by requesting a large number of sto |
| `get_supply_demand_breakouts` | `limit` | 4 | >= 1000 | Can cause excessive data retrieval |
| `get_supply_demand_breakouts` | `filter_moving_averages` | 2 | — | Boolean flag with limited impact on server load |
| `add_portfolio_position` | `notes` | 5 | — | potentially free-form input that could be abused for injecti |
| `add_portfolio_position` | `shares` | 4 | shares >= 100000 | large number of shares can amplify financial impact |
| `add_portfolio_position` | `purchase_price` | 3 | purchase_price >= 100000 | high purchase price can lead to large monetary transactions |
| `add_portfolio_position` | `ticker` | 2 | — | merely identifies the stock |
| `add_portfolio_position` | `purchase_date` | 1 | — | optional date field, no direct risk amplification |
| `remove_portfolio_position` | `shares` | 4 | shares >= 100000 | can amplify risk through large magnitude |
| `remove_portfolio_position` | `ticker` | 2 | — | merely names the target |
| `portfolio_correlation_analysis` | `days` | 3 | >= 1000 | large magnitude can overwhelm server with data processing |
| `compare_tickers` | `tickers` | 4 | >= 100 tickers | can cause excessive data retrieval and processing |
| `compare_tickers` | `days` | 2 | >= 365 days | increases the amount of historical data processed |
| `risk_adjusted_analysis` | `risk_level` | 4 | risk_level >= 90.0 | can amplify risk tolerance to very aggressive levels |
| `risk_adjusted_analysis` | `ticker` | 2 | — | merely names the target |
| `fetch_stock_data` | `start_date` | 3 | — | can potentially request a large time range if end_date is fa |
| `fetch_stock_data` | `end_date` | 3 | — | can potentially request a large time range if start_date is  |
| `fetch_stock_data` | `ticker` | 2 | — | merely names the target |
| `get_stock_info` | `ticker` | 2 | — | merely names the target |
| `get_news_sentiment` | `limit` | 4 | >= 100 | controls the breadth (bulk fan-out) of articles to analyze |
| `get_news_sentiment` | `timeframe` | 3 | — | can widen scope of data retrieval |
| `get_news_sentiment` | `ticker` | 2 | — | merely names the target |
| `get_adanos_market_sentiment` | `sources` | 5 | — | can broaden the scope of data sources, increasing risk |
| `get_adanos_market_sentiment` | `days` | 4 | >= 365 | increases data retrieval and processing load over time |
| `get_adanos_market_sentiment` | `ticker` | 2 | — | names the target, limited scope |
