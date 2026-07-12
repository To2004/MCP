# Static scan — maverick-mcp (`maverick`)

Source: live MITM capture logs/proxy/sessions/finance_maverick/captured.jsonl

Method: deterministic static analysis (atomic-op taxonomy + input-risk rules), no LLM. 119 tools.

## Severity distribution (by primary atomic op)

| Severity | Tools |
| --- | --- |
| Low | 94 |
| Medium | 15 |
| Critical | 10 |

## Tools ranked by verb severity

| # | Tool | Primary op | Sev | Top input-risk param | Params |
| --- | --- | --- | --- | --- | --- |
| 1 | `run_backtest` | EXECUTE (Critical) | 5 | `symbol` (r1: minor / structural parameter) | 16 |
| 2 | `run_ml_strategy_backtest` | EXECUTE (Critical) | 5 | `train_ratio` (r3: magnitude/count — larger value means broader eff) | 11 |
| 3 | `portfolio_remove_position` | DELETE (Critical) | 5 | `user_id` (r2: names the target resource — selects what the op ) | 4 |
| 4 | `portfolio_clear_portfolio` | DELETE (Critical) | 5 | `confirm` (r4: escalating flag — flips the call to a wider/irre) | 3 |
| 5 | `watchlist_remove` | DELETE (Critical) | 5 | `watchlist_id` (r2: names the target resource — selects what the op ) | 2 |
| 6 | `remove_portfolio_position` | DELETE (Critical) | 5 | `ticker` (r1: minor / structural parameter) | 2 |
| 7 | `data_clear_cache` | DELETE (Critical) | 5 | `ticker` (r1: minor / structural parameter) | 1 |
| 8 | `performance_clear_system_caches` | DELETE (Critical) | 5 | `request` (r1: minor / structural parameter) | 1 |
| 9 | `delete_signal` | DELETE (Critical) | 5 | `signal_id` (r2: names the target resource — selects what the op ) | 1 |
| 10 | `run_health_diagnostics` | EXECUTE (Critical) | 5 | — | 0 |
| 11 | `portfolio_add_position` | CREATE (Medium) | 3 | `user_id` (r2: names the target resource — selects what the op ) | 7 |
| 12 | `journal_add_trade` | CREATE (Medium) | 3 | `side` (r2: names the target resource — selects what the op ) | 7 |
| 13 | `analyze_market_regimes` | MODIFY (Medium) | 3 | `n_regimes` (r3: magnitude/count — larger value means broader eff) | 6 |
| 14 | `create_strategy_ensemble` | WRITE (Medium) | 3 | `symbols` (r4: list/array — risk scales with its length (bulk r) | 6 |
| 15 | `agents_analyze_market_with_agent` | MODIFY (Medium) | 3 | `query` (r5: free-form query/command — unbounded reach; the w) | 5 |
| 16 | `update_signal` | MODIFY (Medium) | 3 | `signal_id` (r2: names the target resource — selects what the op ) | 5 |
| 17 | `add_portfolio_position` | WRITE (Medium) | 3 | `ticker` (r1: minor / structural parameter) | 5 |
| 18 | `agents_get_agent_streaming_analysis` | MODIFY (Medium) | 3 | `query` (r5: free-form query/command — unbounded reach; the w) | 4 |
| 19 | `create_signal` | WRITE (Medium) | 3 | `label` (r1: minor / structural parameter) | 4 |
| 20 | `data_get_adanos_market_sentiment` | MODIFY (Medium) | 3 | `days` (r3: magnitude/count — larger value means broader eff) | 3 |
| 21 | `data_get_news_sentiment` | CREATE (Medium) | 3 | `limit` (r3: magnitude/count — larger value means broader eff) | 3 |
| 22 | `research_analyze_market_sentiment` | MODIFY (Medium) | 3 | `topic` (r1: minor / structural parameter) | 3 |
| 23 | `watchlist_add` | CREATE (Medium) | 3 | `watchlist_id` (r2: names the target resource — selects what the op ) | 3 |
| 24 | `watchlist_create` | CREATE (Medium) | 3 | `description` (r5: free-form query/command — unbounded reach; the w) | 2 |
| 25 | `reset_circuit_breaker` | MODIFY (Medium) | 3 | `breaker_name` (r2: names the target resource — selects what the op ) | 1 |
| 26 | `backtest_portfolio` | READ (Low) | 2 | `symbols` (r4: list/array — risk scales with its length (bulk r) | 9 |
| 27 | `train_ml_predictor` | READ (Low) | 2 | `return_threshold` (r3: magnitude/count — larger value means broader eff) | 9 |
| 28 | `monte_carlo_simulation` | READ (Low) | 2 | `symbol` (r1: minor / structural parameter) | 8 |
| 29 | `optimize_strategy` | READ (Low) | 2 | `optimization_metric` (r3: magnitude/count — larger value means broader eff) | 7 |
| 30 | `agents_orchestrated_analysis` | READ (Low) | 2 | `query` (r5: free-form query/command — unbounded reach; the w) | 6 |
| 31 | `agents_deep_research_financial` | SEARCH (Low) | 2 | `research_depth` (r3: magnitude/count — larger value means broader eff) | 6 |
| 32 | `walk_forward_analysis` | READ (Low) | 2 | `window_size` (r3: magnitude/count — larger value means broader eff) | 6 |
| 33 | `technical_get_macd_analysis` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 5 |
| 34 | `screening_get_screening_by_criteria` | READ (Low) | 2 | `min_momentum_score` (r3: magnitude/count — larger value means broader eff) | 5 |
| 35 | `research_comprehensive_research` | SEARCH (Low) | 2 | `query` (r5: free-form query/command — unbounded reach; the w) | 5 |
| 36 | `generate_backtest_charts` | READ (Low) | 2 | `symbol` (r1: minor / structural parameter) | 5 |
| 37 | `generate_optimization_charts` | READ (Low) | 2 | `symbol` (r1: minor / structural parameter) | 5 |
| 38 | `get_macd_analysis` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 5 |
| 39 | `portfolio_risk_adjusted_analysis` | READ (Low) | 2 | `user_id` (r2: names the target resource — selects what the op ) | 4 |
| 40 | `portfolio_compare_tickers` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 4 |
| 41 | `portfolio_portfolio_correlation_analysis` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 4 |
| 42 | `agents_compare_multi_agent_analysis` | READ (Low) | 2 | `query` (r5: free-form query/command — unbounded reach; the w) | 4 |
| 43 | `compare_strategies` | READ (Low) | 2 | `symbol` (r1: minor / structural parameter) | 4 |
| 44 | `backtest_signal` | READ (Low) | 2 | `signal_id` (r2: names the target resource — selects what the op ) | 4 |
| 45 | `get_position_risk_check` | READ (Low) | 2 | `portfolio_name` (r2: names the target resource — selects what the op ) | 4 |
| 46 | `get_regime_adjusted_sizing` | READ (Low) | 2 | `account_size` (r3: magnitude/count — larger value means broader eff) | 4 |
| 47 | `technical_get_rsi_analysis` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 3 |
| 48 | `portfolio_get_my_portfolio` | READ (Low) | 2 | `user_id` (r2: names the target resource — selects what the op ) | 3 |
| 49 | `data_fetch_stock_data` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 3 |
| 50 | `data_fetch_stock_data_batch` | READ (Low) | 2 | `tickers` (r4: list/array — risk scales with its length (bulk r) | 3 |
| 51 | `data_get_cached_price_data` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 3 |
| 52 | `research_company_comprehensive` | SEARCH (Low) | 2 | `symbol` (r1: minor / structural parameter) | 3 |
| 53 | `journal_close_trade` | READ (Low) | 2 | `entry_id` (r2: names the target resource — selects what the op ) | 3 |
| 54 | `get_rsi_analysis` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 3 |
| 55 | `fetch_stock_data` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 3 |
| 56 | `get_news_sentiment` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 3 |
| 57 | `get_adanos_market_sentiment` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 3 |
| 58 | `technical_get_support_resistance` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 2 |
| 59 | `technical_get_full_technical_analysis` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 2 |
| 60 | `screening_get_supply_demand_breakouts` | READ (Low) | 2 | `filter_moving_averages` (r5: free-form query/command — unbounded reach; the w) | 2 |
| 61 | `agents_compare_personas_analysis` | READ (Low) | 2 | `query` (r5: free-form query/command — unbounded reach; the w) | 2 |
| 62 | `get_decision_log` | READ (Low) | 2 | `session_id` (r3: magnitude/count — larger value means broader eff) | 2 |
| 63 | `get_screening_changes` | READ (Low) | 2 | `screen_name` (r3: magnitude/count — larger value means broader eff) | 2 |
| 64 | `get_screening_history` | READ (Low) | 2 | `screen_name` (r3: magnitude/count — larger value means broader eff) | 2 |
| 65 | `schedule_screening` | READ (Low) | 2 | `screen_name` (r3: magnitude/count — larger value means broader eff) | 2 |
| 66 | `get_upcoming_catalysts` | READ (Low) | 2 | `days_ahead` (r3: magnitude/count — larger value means broader eff) | 2 |
| 67 | `get_support_resistance` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 2 |
| 68 | `get_full_technical_analysis` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 2 |
| 69 | `get_supply_demand_breakouts` | READ (Low) | 2 | `filter_moving_averages` (r5: free-form query/command — unbounded reach; the w) | 2 |
| 70 | `compare_tickers` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 2 |
| 71 | `risk_adjusted_analysis` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 2 |
| 72 | `technical_get_stock_chart_analysis` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 73 | `screening_get_maverick_stocks` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 1 |
| 74 | `screening_get_maverick_bear_stocks` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 1 |
| 75 | `data_get_chart_links` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 76 | `performance_get_system_performance_health` | READ (Low) | 2 | `request` (r1: minor / structural parameter) | 1 |
| 77 | `parse_strategy` | READ (Low) | 2 | `description` (r5: free-form query/command — unbounded reach; the w) | 1 |
| 78 | `get_strategy_help` | READ (Low) | 2 | `strategy_type` (r1: minor / structural parameter) | 1 |
| 79 | `get_regime_history` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 1 |
| 80 | `get_strategy_performance` | READ (Low) | 2 | `strategy_tag` (r1: minor / structural parameter) | 1 |
| 81 | `journal_trade_review` | READ (Low) | 2 | `entry_id` (r2: names the target resource — selects what the op ) | 1 |
| 82 | `get_portfolio_risk_dashboard` | READ (Low) | 2 | `portfolio_name` (r2: names the target resource — selects what the op ) | 1 |
| 83 | `get_risk_alerts` | READ (Low) | 2 | `portfolio_name` (r2: names the target resource — selects what the op ) | 1 |
| 84 | `get_watchlist` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 1 |
| 85 | `get_economic_calendar` | READ (Low) | 2 | `days_ahead` (r3: magnitude/count — larger value means broader eff) | 1 |
| 86 | `get_maverick_stocks` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 1 |
| 87 | `get_my_portfolio` | READ (Low) | 2 | `include_current_prices` (r1: minor / structural parameter) | 1 |
| 88 | `get_maverick_bear_stocks` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 1 |
| 89 | `portfolio_correlation_analysis` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 1 |
| 90 | `screening_get_all_screening_recommendations` | READ (Low) | 2 | — | 0 |
| 91 | `performance_analyze_database_index_usage` | READ (Low) | 2 | — | 0 |
| 92 | `performance_optimize_cache_configuration` | READ (Low) | 2 | — | 0 |
| 93 | `get_system_health` | READ (Low) | 2 | — | 0 |
| 94 | `get_resource_usage` | READ (Low) | 2 | — | 0 |
| 95 | `get_health_history` | READ (Low) | 2 | — | 0 |
| 96 | `discover_capabilities` | READ (Low) | 2 | — | 0 |
| 97 | `check_signals_now` | READ (Low) | 2 | — | 0 |
| 98 | `get_market_regime` | READ (Low) | 2 | — | 0 |
| 99 | `get_strategy_comparison` | READ (Low) | 2 | — | 0 |
| 100 | `get_user_portfolio_summary` | READ (Low) | 2 | — | 0 |
| 101 | `get_market_overview` | READ (Low) | 2 | — | 0 |
| 102 | `get_all_screening_recommendations` | READ (Low) | 2 | — | 0 |
| 103 | `journal_list_trades` | LIST (Low) | 1 | `limit` (r3: magnitude/count — larger value means broader eff) | 4 |
| 104 | `data_get_stock_info` | METADATA (Low) | 1 | `ticker` (r1: minor / structural parameter) | 1 |
| 105 | `get_component_status` | METADATA (Low) | 1 | `component_name` (r2: names the target resource — selects what the op ) | 1 |
| 106 | `list_signals` | LIST (Low) | 1 | `active_only` (r1: minor / structural parameter) | 1 |
| 107 | `watchlist_brief` | LIST (Low) | 1 | `watchlist_id` (r2: names the target resource — selects what the op ) | 1 |
| 108 | `get_stock_info` | METADATA (Low) | 1 | `ticker` (r1: minor / structural parameter) | 1 |
| 109 | `performance_get_redis_health_status` | METADATA (Low) | 1 | — | 0 |
| 110 | `performance_get_cache_performance_status` | METADATA (Low) | 1 | — | 0 |
| 111 | `performance_get_database_performance_status` | METADATA (Low) | 1 | — | 0 |
| 112 | `agents_list_available_agents` | LIST (Low) | 1 | — | 0 |
| 113 | `get_circuit_breaker_status` | METADATA (Low) | 1 | — | 0 |
| 114 | `get_status_dashboard` | METADATA (Low) | 1 | — | 0 |
| 115 | `list_strategies` | LIST (Low) | 1 | — | 0 |
| 116 | `list_all_strategies` | LIST (Low) | 1 | — | 0 |
| 117 | `get_tool_registry_status` | METADATA (Low) | 1 | — | 0 |
| 118 | `get_screening_pipeline_status` | METADATA (Low) | 1 | — | 0 |
| 119 | `get_mcp_connection_status` | METADATA (Low) | 1 | — | 0 |
