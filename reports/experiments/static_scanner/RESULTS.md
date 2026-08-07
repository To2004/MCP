# Static scanner — results

Tool impact for every tool in the corpus, computed with **no LLM**.
`LLM` is the v3 scan's model-assigned impact where one exists (comparison only,
not ground truth). Vocabulary and rules: [VOCABULARY.md](VOCABULARY.md).

## Summary

| Server | Tools | t1 | t2 | t3 | t4 | t5 | vs LLM |
|---|--:|--:|--:|--:|--:|--:|--:|
| `calendar:real` | 13 | 1 | 4 | 2 | 1 | 5 | 9/13 = 69% |
| `slack:real` | 16 | 0 | 4 | 5 | 5 | 2 | 15/16 = 94% |
| `github:real` | 26 | 0 | 3 | 11 | 9 | 3 | 22/26 = 85% |
| `fs:corp_filesystem` | 14 | 0 | 4 | 6 | 3 | 1 | 12/14 = 86% |
| `sqlite:cbg_sqlite` | 5 | 0 | 2 | 1 | 1 | 1 | — |
| `finance-tools-mcp` | 17 | 1 | 0 | 16 | 0 | 0 | — |
| `maverick-mcp` | 119 | 6 | 13 | 78 | 11 | 11 | — |
| `openbb-platform` | 30 | 0 | 2 | 27 | 1 | 0 | — |
| `sec-edgar-mcp` | 21 | 0 | 1 | 20 | 0 | 0 | — |
| `yfinance` | 9 | 0 | 1 | 8 | 0 | 0 | — |
| **total** | **270** | 8 | 34 | 174 | 31 | 23 | **58/69 = 84%** |

Within ±1 of the LLM: **69/69 = 100%**. The disagreements are two honest
classes: (a) the model infers unstated side-effects (`respond-to-event` emails
the organiser; `conversations_join` widens what can be read), and (b) whether a
search/list returns names or content genuinely depends on the API, which the
declaration does not settle.

## calendar:real

| Tool | Impact | LLM | Conf | Evidence | Capability flags |
|---|:-:|:-:|:-:|---|---|
| `create-event` | **5** | 4 ✗ | 0.8 | tier-4 verbs: create; parameter evidence raises tier 4 -> 5 | outbound; path |
| `create-events` | **5** | 5 ✓ | 0.8 | tier-4 verbs: create; parameter evidence raises tier 4 -> 5 | outbound |
| `delete-event` | **5** | 5 ✓ | 0.8 | tier-5 verbs: delete | outbound |
| `manage-accounts` | **5** | 5 ✓ | 0.8 | tier-5 verbs: remove | — |
| `update-event` | **5** | 4 ✗ | 0.8 | tier-4 verbs: update; parameter evidence raises tier 4 -> 5 | outbound |
| `respond-to-event` | **4** | 5 ✗ | 0.8 | tier-4 verbs: respond | outbound |
| `get-event` | **3** | 3 ✓ | 0.8 | tier-3 verbs: get, details? | — |
| `search-events` | **3** | 3 ✓ | 0.8 | tier-3 verbs: search, query | raw-query |
| `get-freebusy` | **2** | 2 ✓ | 0.8 | tier-3 verbs: get, query; return-shape marker -> capped at 2 | — |
| `list-calendars` | **2** | 2 ✓ | 0.8 | tier-2 verbs: list | — |
| `list-colors` | **2** | 2 ✓ | 0.8 | tier-2 verbs: list, ids? | — |
| `list-events` | **2** | 3 ✗ | 0.8 | tier-2 verbs: list, names?, ids? | — |
| `get-current-time` | **1** | 1 ✓ | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 1 | — |

## slack:real

| Tool | Impact | LLM | Conf | Evidence | Capability flags |
|---|:-:|:-:|:-:|---|---|
| `usergroups_me` | **5** | 5 ✓ | 0.8 | tier-5 verbs: remove | — |
| `usergroups_users_update` | **5** | 5 ✓ | 0.8 | tier-5 verbs: remove | — |
| `conversations_add_message` | **4** | 4 ✓ | 0.8 | tier-4 verbs: add | — |
| `conversations_join` | **4** | 5 ✗ | 0.8 | tier-4 verbs: join | — |
| `conversations_leave` | **4** | 4 ✓ | 0.8 | tier-4 verbs: leave | — |
| `usergroups_create` | **4** | 4 ✓ | 0.8 | tier-4 verbs: create, join | — |
| `usergroups_update` | **4** | 4 ✓ | 0.8 | tier-4 verbs: update | — |
| `conversations_history` | **3** | 3 ✓ | 0.8 | tier-3 verbs: get, histor(y|ies) | unbounded |
| `conversations_replies` | **3** | 3 ✓ | 0.8 | tier-3 verbs: get, replies, thread | unbounded |
| `conversations_search_messages` | **3** | 3 ✓ | 0.8 | tier-3 verbs: search | unbounded |
| `conversations_unreads` | **3** | 3 ✓ | 0.8 | tier-3 verbs: get | — |
| `users_search` | **3** | 3 ✓ | 0.8 | tier-3 verbs: search, display, details? | unbounded; raw-query |
| `channels_list` | **2** | 2 ✓ | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 2 | unbounded; raw-query |
| `channels_me` | **2** | 2 ✓ | 0.8 | tier-2 verbs: list | unbounded |
| `conversations_mark` | **2** | 2 ✓ | 0.8 | tier-3 verbs: read; return-shape marker -> capped at 2 | — |
| `usergroups_list` | **2** | 2 ✓ | 0.8 | tier-2 verbs: list, counts?, names? | — |

## github:real

| Tool | Impact | LLM | Conf | Evidence | Capability flags |
|---|:-:|:-:|:-:|---|---|
| `create_or_update_file` | **5** | 5 ✓ | 0.8 | tier-4 verbs: create, update; create-or-overwrite in one tool -> | path |
| `merge_pull_request` | **5** | 5 ✓ | 0.8 | tier-5 verbs: merge | — |
| `push_files` | **5** | 5 ✓ | 0.8 | tier-5 verbs: push | — |
| `add_issue_comment` | **4** | 4 ✓ | 0.8 | tier-4 verbs: add, comment | — |
| `create_branch` | **4** | 4 ✓ | 0.8 | tier-4 verbs: create, branch | — |
| `create_issue` | **4** | 4 ✓ | 0.8 | tier-4 verbs: create | — |
| `create_pull_request` | **4** | 4 ✓ | 0.8 | tier-4 verbs: create | — |
| `create_pull_request_review` | **4** | 4 ✓ | 0.8 | tier-4 verbs: create | — |
| `create_repository` | **4** | 4 ✓ | 0.8 | tier-4 verbs: create | — |
| `fork_repository` | **4** | 5 ✗ | 0.8 | tier-4 verbs: fork | — |
| `update_issue` | **4** | 4 ✓ | 0.8 | tier-4 verbs: update | — |
| `update_pull_request_branch` | **4** | 4 ✓ | 0.8 | tier-4 verbs: branch, update | — |
| `get_file_contents` | **3** | 3 ✓ | 0.8 | tier-3 verbs: get, contents? | path |
| `get_issue` | **3** | 3 ✓ | 0.8 | tier-3 verbs: get, details? | — |
| `get_pull_request` | **3** | 3 ✓ | 0.8 | tier-3 verbs: get, details? | — |
| `get_pull_request_comments` | **3** | 3 ✓ | 0.8 | tier-3 verbs: get | — |
| `get_pull_request_files` | **3** | 3 ✓ | 0.8 | tier-3 verbs: get | — |
| `get_pull_request_reviews` | **3** | 3 ✓ | 0.8 | tier-3 verbs: get | — |
| `list_commits` | **3** | 2 ✗ | 0.8 | tier-3 verbs: get | — |
| `search_code` | **3** | 3 ✓ | 0.8 | tier-3 verbs: search | raw-query |
| `search_issues` | **3** | 3 ✓ | 0.8 | tier-3 verbs: search | raw-query |
| `search_repositories` | **3** | 2 ✗ | 0.8 | tier-3 verbs: search | raw-query |
| `search_users` | **3** | 2 ✗ | 0.8 | tier-3 verbs: search | raw-query |
| `get_pull_request_status` | **2** | 2 ✓ | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 2 | — |
| `list_issues` | **2** | 2 ✓ | 0.8 | tier-2 verbs: list | — |
| `list_pull_requests` | **2** | 2 ✓ | 0.8 | tier-2 verbs: list | — |

## fs:corp_filesystem

| Tool | Impact | LLM | Conf | Evidence | Capability flags |
|---|:-:|:-:|:-:|---|---|
| `write_file` | **5** | 5 ✓ | 0.95 | readOnlyHint=false; destructiveHint=true; tier-5 verbs: overwrit | path |
| `create_directory` | **4** | 4 ✓ | 0.95 | readOnlyHint=false; tier-4 verbs: create | path |
| `edit_file` | **4** | 4 ✓ | 0.95 | readOnlyHint=false; destructiveHint=true; tier-4 verbs: edit | path; dry-run; non-idempotent writ |
| `move_file` | **4** | 4 ✓ | 0.95 | readOnlyHint=false; tier-4 verbs: move | path; path; non-idempotent write |
| `directory_tree` | **3** | 2 ✗ | 0.95 | readOnlyHint=true -> ceiling 3; tier-3 verbs: get | path |
| `read_file` | **3** | 3 ✓ | 0.95 | readOnlyHint=true -> ceiling 3; tier-3 verbs: read, contents? | path |
| `read_media_file` | **3** | 3 ✓ | 0.95 | readOnlyHint=true -> ceiling 3; tier-3 verbs: read | path |
| `read_multiple_files` | **3** | 3 ✓ | 0.95 | readOnlyHint=true -> ceiling 3; tier-3 verbs: read, contents? | — |
| `read_text_file` | **3** | 3 ✓ | 0.95 | readOnlyHint=true -> ceiling 3; tier-3 verbs: read, tail, conten | path |
| `search_files` | **3** | 2 ✗ | 0.95 | readOnlyHint=true -> ceiling 3; tier-3 verbs: search | path; glob |
| `get_file_info` | **2** | 2 ✓ | 0.95 | readOnlyHint=true -> ceiling 3; tier-3 verbs: get, retrieve; ret | path |
| `list_allowed_directories` | **2** | 2 ✓ | 0.95 | readOnlyHint=true -> ceiling 3; tier-2 verbs: list | — |
| `list_directory` | **2** | 2 ✓ | 0.95 | readOnlyHint=true -> ceiling 3; tier-3 verbs: get; return-shape  | path |
| `list_directory_with_sizes` | **2** | 2 ✓ | 0.95 | readOnlyHint=true -> ceiling 3; tier-3 verbs: get; return-shape  | path |

## sqlite:cbg_sqlite

| Tool | Impact | LLM | Conf | Evidence | Capability flags |
|---|:-:|:-:|:-:|---|---|
| `write_query` | **5** | — | 0.8 | tier-5 verbs: delete, drop | raw-query |
| `insert_row` | **4** | — | 0.8 | tier-4 verbs: insert | — |
| `read_query` | **3** | — | 0.8 | tier-3 verbs: read, query | raw-query |
| `describe_table` | **2** | — | 0.8 | tier-2 verbs: describe, names? | — |
| `list_tables` | **2** | — | 0.8 | tier-2 verbs: list | — |

## finance-tools-mcp

| Tool | Impact | LLM | Conf | Evidence | Capability flags |
|---|:-:|:-:|:-:|---|---|
| `analyze_fng_trend` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `calculate` | **3** | — | 0.8 | tier-3 verbs: calculate | raw-query |
| `cnbc_news_feed` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_earnings_history` | **3** | — | 0.8 | tier-3 verbs: get, histor(y|ies) | — |
| `get_financial_statements` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_fred_series` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_historical_fng_tool` | **3** | — | 0.8 | tier-3 verbs: get, retrieve | — |
| `get_insider_trades` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_overall_sentiment_tool` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_price_history` | **3** | — | 0.8 | tier-3 verbs: get, histor(y|ies) | — |
| `get_ticker_data` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_ticker_news_tool` | **3** | — | 0.8 | tier-3 verbs: get, research | — |
| `get_top25_holders` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `search_fred_series` | **3** | — | 0.8 | tier-3 verbs: search | raw-query |
| `social_media_feed` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `super_option_tool` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `get_current_time` | **1** | — | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 1 | — |

## maverick-mcp

| Tool | Impact | LLM | Conf | Evidence | Capability flags |
|---|:-:|:-:|:-:|---|---|
| `data_clear_cache` | **5** | — | 0.8 | tier-5 verbs: clear | — |
| `delete_signal` | **5** | — | 0.8 | tier-5 verbs: delete | — |
| `journal_add_trade` | **5** | — | 0.8 | tier-5 verbs: trade | — |
| `journal_close_trade` | **5** | — | 0.8 | tier-5 verbs: trade | — |
| `journal_trade_review` | **5** | — | 0.8 | tier-5 verbs: trade | — |
| `portfolio_clear_portfolio` | **5** | — | 0.8 | tier-5 verbs: clear | — |
| `portfolio_remove_position` | **5** | — | 0.8 | tier-5 verbs: remove | — |
| `remove_portfolio_position` | **5** | — | 0.8 | tier-5 verbs: remove | — |
| `reset_circuit_breaker` | **5** | — | 0.8 | tier-5 verbs: reset | — |
| `walk_forward_analysis` | **5** | — | 0.8 | tier-5 verbs: forward | — |
| `watchlist_remove` | **5** | — | 0.8 | tier-5 verbs: remove | — |
| `add_portfolio_position` | **4** | — | 0.8 | tier-4 verbs: add | — |
| `create_signal` | **4** | — | 0.8 | tier-4 verbs: create | — |
| `create_strategy_ensemble` | **4** | — | 0.8 | tier-4 verbs: create | — |
| `generate_backtest_charts` | **4** | — | 0.8 | tier-4 verbs: generate | — |
| `generate_optimization_charts` | **4** | — | 0.8 | tier-4 verbs: generate | — |
| `performance_clear_system_caches` | **4** | — | 0.8 | tier-5 verbs: clear; scoped/partial edit language -> capped at 4 | — |
| `portfolio_add_position` | **4** | — | 0.8 | tier-4 verbs: add | — |
| `schedule_screening` | **4** | — | 0.8 | tier-4 verbs: schedule | — |
| `update_signal` | **4** | — | 0.8 | tier-4 verbs: update | — |
| `watchlist_add` | **4** | — | 0.8 | tier-4 verbs: add | — |
| `watchlist_create` | **4** | — | 0.8 | tier-4 verbs: create | — |
| `agents_analyze_market_with_agent` | **3** | — | 0.35 | no verb evidence -> annotation/default | raw-query; unbounded |
| `agents_compare_multi_agent_analysis` | **3** | — | 0.8 | tier-3 verbs: compare | raw-query |
| `agents_compare_personas_analysis` | **3** | — | 0.8 | tier-3 verbs: compare | raw-query |
| `agents_deep_research_financial` | **3** | — | 0.8 | tier-3 verbs: research | — |
| `agents_get_agent_streaming_analysis` | **3** | — | 0.8 | tier-3 verbs: get | raw-query |
| `agents_orchestrated_analysis` | **3** | — | 0.35 | no verb evidence -> annotation/default | raw-query |
| `analyze_market_regimes` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `backtest_portfolio` | **3** | — | 0.8 | tier-3 verbs: backtest | — |
| `backtest_signal` | **3** | — | 0.8 | tier-3 verbs: summar(y|ise|ize), backtest | — |
| `check_signals_now` | **3** | — | 0.8 | tier-2 verbs: list; lists non-container items -> content read (3 | — |
| `compare_strategies` | **3** | — | 0.8 | tier-3 verbs: compare | — |
| `compare_tickers` | **3** | — | 0.8 | tier-3 verbs: compare | — |
| `data_fetch_stock_data` | **3** | — | 0.8 | tier-3 verbs: fetch | — |
| `data_fetch_stock_data_batch` | **3** | — | 0.8 | tier-3 verbs: fetch | — |
| `data_get_adanos_market_sentiment` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `data_get_cached_price_data` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `data_get_chart_links` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `data_get_news_sentiment` | **3** | — | 0.8 | tier-3 verbs: get, research | unbounded |
| `data_get_stock_info` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `fetch_stock_data` | **3** | — | 0.8 | tier-3 verbs: fetch | — |
| `get_adanos_market_sentiment` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_all_screening_recommendations` | **3** | — | 0.8 | tier-3 verbs: get, screen(er|ing)? | — |
| `get_decision_log` | **3** | — | 0.8 | tier-3 verbs: get, query | unbounded |
| `get_economic_calendar` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_full_technical_analysis` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_macd_analysis` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_market_overview` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_market_regime` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_maverick_bear_stocks` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `get_maverick_stocks` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `get_my_portfolio` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_news_sentiment` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `get_position_risk_check` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_regime_adjusted_sizing` | **3** | — | 0.8 | tier-3 verbs: get, calculate | — |
| `get_regime_history` | **3** | — | 0.8 | tier-3 verbs: get, retrieve, histor(y|ies) | — |
| `get_resource_usage` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_risk_alerts` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_rsi_analysis` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_screening_changes` | **3** | — | 0.8 | tier-3 verbs: get, screen(er|ing)? | unbounded |
| `get_screening_history` | **3** | — | 0.8 | tier-3 verbs: get, histor(y|ies), screen(er|ing)? | — |
| `get_stock_info` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_strategy_comparison` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_strategy_help` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_strategy_performance` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_supply_demand_breakouts` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `get_support_resistance` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_upcoming_catalysts` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_user_portfolio_summary` | **3** | — | 0.8 | tier-3 verbs: get, summar(y|ise|ize) | — |
| `get_watchlist` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `journal_list_trades` | **3** | — | 0.8 | tier-2 verbs: list; lists non-container items -> content read (3 | unbounded |
| `list_all_strategies` | **3** | — | 0.8 | tier-2 verbs: list, names?; lists non-container items -> content | — |
| `list_signals` | **3** | — | 0.8 | tier-2 verbs: list; lists non-container items -> content read (3 | — |
| `list_strategies` | **3** | — | 0.8 | tier-2 verbs: list; lists non-container items -> content read (3 | — |
| `monte_carlo_simulation` | **3** | — | 0.8 | tier-3 verbs: simulat(e|ion), backtest | — |
| `optimize_strategy` | **3** | — | 0.8 | tier-3 verbs: search | — |
| `parse_strategy` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `portfolio_compare_tickers` | **3** | — | 0.8 | tier-3 verbs: compare | — |
| `portfolio_correlation_analysis` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `portfolio_get_my_portfolio` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `portfolio_portfolio_correlation_analysis` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `portfolio_risk_adjusted_analysis` | **3** | — | 0.8 | tier-3 verbs: details? | — |
| `research_analyze_market_sentiment` | **3** | — | 0.8 | tier-3 verbs: research | — |
| `research_company_comprehensive` | **3** | — | 0.8 | tier-3 verbs: research | — |
| `research_comprehensive_research` | **3** | — | 0.8 | tier-3 verbs: search, research | raw-query |
| `risk_adjusted_analysis` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `run_backtest` | **3** | — | 0.8 | tier-3 verbs: backtest | — |
| `run_ml_strategy_backtest` | **3** | — | 0.8 | tier-3 verbs: backtest | — |
| `screening_get_all_screening_recommendations` | **3** | — | 0.8 | tier-3 verbs: get, screen(er|ing)? | — |
| `screening_get_maverick_bear_stocks` | **3** | — | 0.8 | tier-3 verbs: get, screen(er|ing)? | unbounded |
| `screening_get_maverick_stocks` | **3** | — | 0.8 | tier-3 verbs: get, research, screen(er|ing)? | unbounded |
| `screening_get_screening_by_criteria` | **3** | — | 0.8 | tier-3 verbs: get, screen(er|ing)? | unbounded |
| `screening_get_supply_demand_breakouts` | **3** | — | 0.8 | tier-3 verbs: get, screen(er|ing)? | unbounded |
| `technical_get_full_technical_analysis` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `technical_get_macd_analysis` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `technical_get_rsi_analysis` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `technical_get_stock_chart_analysis` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `technical_get_support_resistance` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `train_ml_predictor` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `agents_list_available_agents` | **2** | — | 0.8 | tier-2 verbs: list; lists non-container items -> content read (3 | — |
| `get_circuit_breaker_status` | **2** | — | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 2 | — |
| `get_component_status` | **2** | — | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 2 | — |
| `get_mcp_connection_status` | **2** | — | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 2 | — |
| `get_portfolio_risk_dashboard` | **2** | — | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 2 | — |
| `get_screening_pipeline_status` | **2** | — | 0.8 | tier-3 verbs: get, screen(er|ing)?; return-shape marker -> cappe | — |
| `get_status_dashboard` | **2** | — | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 2 | — |
| `get_tool_registry_status` | **2** | — | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 2 | — |
| `performance_analyze_database_index_usage` | **2** | — | 0.8 | tier-2 verbs: index, usage | — |
| `performance_get_cache_performance_status` | **2** | — | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 2 | — |
| `performance_get_database_performance_status` | **2** | — | 0.8 | tier-3 verbs: get, query; return-shape marker -> capped at 2 | — |
| `performance_optimize_cache_configuration` | **2** | — | 0.8 | tier-2 verbs: sizes? | — |
| `watchlist_brief` | **2** | — | 0.8 | tier-2 verbs: counts? | — |
| `discover_capabilities` | **1** | — | 0.8 | tier-2 verbs: discover; return-shape marker -> capped at 1 | — |
| `get_health_history` | **1** | — | 0.8 | tier-3 verbs: get, histor(y|ies); return-shape marker -> capped  | — |
| `get_system_health` | **1** | — | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 1 | — |
| `performance_get_redis_health_status` | **1** | — | 0.8 | tier-3 verbs: get; return-shape marker -> capped at 1 | — |
| `performance_get_system_performance_health` | **1** | — | 0.8 | tier-3 verbs: get, query; return-shape marker -> capped at 1 | — |
| `run_health_diagnostics` | **1** | — | 0.8 | tier-1 verbs: health(check)?, diagnostics? | — |

## openbb-platform

| Tool | Impact | LLM | Conf | Evidence | Capability flags |
|---|:-:|:-:|:-:|---|---|
| `equity_ownership_share_statistics` | **4** | — | 0.8 | tier-4 verbs: share | — |
| `crypto_price_historical` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `derivatives_futures_curve` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `derivatives_futures_historical` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `derivatives_options_chains` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `derivatives_options_surface` | **3** | — | 0.8 | tier-2 verbs: list; lists non-container items -> content read (3 | — |
| `equity_discovery_active` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `equity_discovery_aggressive_small_caps` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `equity_discovery_gainers` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `equity_discovery_growth_tech` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `equity_discovery_losers` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `equity_discovery_undervalued_growth` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `equity_discovery_undervalued_large_caps` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `equity_estimates_consensus` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `equity_fundamental_balance` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `equity_fundamental_cash` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `equity_fundamental_dividends` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `equity_fundamental_income` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `equity_fundamental_management` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `equity_fundamental_metrics` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `equity_price_historical` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `equity_price_quote` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `equity_profile` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `equity_screener` | **3** | — | 0.8 | tier-3 verbs: screen(er|ing)? | unbounded |
| `get_prompt` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `install_skill` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `news_company` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `read_resource` | **3** | — | 0.95 | readOnlyHint=true -> ceiling 3; tier-3 verbs: read, contents? | — |
| `list_prompts` | **2** | — | 0.8 | tier-2 verbs: list, metadata, names?; lists non-container items  | — |
| `list_resources` | **2** | — | 0.95 | readOnlyHint=true -> ceiling 3; tier-2 verbs: list, metadata, na | — |

## sec-edgar-mcp

| Tool | Impact | LLM | Conf | Evidence | Capability flags |
|---|:-:|:-:|:-:|---|---|
| `analyze_8k` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `analyze_form4_transactions` | **3** | — | 0.8 | tier-3 verbs: extract, query, details? | unbounded |
| `analyze_insider_sentiment` | **3** | — | 0.35 | no verb evidence -> annotation/default | — |
| `compare_periods` | **3** | — | 0.8 | tier-3 verbs: compare | — |
| `discover_company_metrics` | **3** | — | 0.8 | tier-3 verbs: search | — |
| `get_cik_by_ticker` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_company_facts` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_company_info` | **3** | — | 0.8 | tier-3 verbs: get, query | — |
| `get_filing_content` | **3** | — | 0.8 | tier-3 verbs: get, contents? | — |
| `get_filing_sections` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_financials` | **3** | — | 0.8 | tier-3 verbs: get, query | — |
| `get_form4_details` | **3** | — | 0.8 | tier-3 verbs: get, details? | — |
| `get_insider_summary` | **3** | — | 0.8 | tier-3 verbs: get, query, summar(y|ise|ize) | — |
| `get_insider_transactions` | **3** | — | 0.8 | tier-3 verbs: get, query | unbounded |
| `get_key_metrics` | **3** | — | 0.8 | tier-3 verbs: get, retrieve | — |
| `get_recent_filings` | **3** | — | 0.8 | tier-3 verbs: get | unbounded |
| `get_recommended_tools` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_segment_data` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_xbrl_concepts` | **3** | — | 0.8 | tier-3 verbs: get, extract | — |
| `search_companies` | **3** | — | 0.8 | tier-3 verbs: search, query | raw-query; unbounded |
| `discover_xbrl_concepts` | **2** | — | 0.8 | tier-2 verbs: discover | — |

## yfinance

| Tool | Impact | LLM | Conf | Evidence | Capability flags |
|---|:-:|:-:|:-:|---|---|
| `get_financial_statement` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_historical_stock_prices` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_holder_info` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_option_chain` | **3** | — | 0.8 | tier-3 verbs: get, fetch | — |
| `get_recommendations` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_stock_actions` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_stock_info` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_yahoo_finance_news` | **3** | — | 0.8 | tier-3 verbs: get | — |
| `get_option_expiration_dates` | **2** | — | 0.8 | tier-3 verbs: get, fetch; return-shape marker -> capped at 2 | — |

## Unclassified — no verb matched (default tier 3)

15 of 270 tools. These are analysis/compute tools whose names are not
CRUD verbs; tier 3 is a defensible default (they read data and compute) but it
is a default, not a finding — which is what `confidence: 0.35` records.

- `finance-tools-mcp` · `super_option_tool`
- `finance-tools-mcp` · `analyze_fng_trend`
- `maverick-mcp` · `portfolio_portfolio_correlation_analysis`
- `maverick-mcp` · `agents_analyze_market_with_agent`
- `maverick-mcp` · `agents_orchestrated_analysis`
- `maverick-mcp` · `parse_strategy`
- `maverick-mcp` · `train_ml_predictor`
- `maverick-mcp` · `analyze_market_regimes`
- `maverick-mcp` · `portfolio_correlation_analysis`
- `maverick-mcp` · `risk_adjusted_analysis`
- `openbb-platform` · `install_skill`
- `openbb-platform` · `derivatives_futures_historical`
- `openbb-platform` · `derivatives_futures_curve`
- `sec-edgar-mcp` · `analyze_8k`
- `sec-edgar-mcp` · `analyze_insider_sentiment`
