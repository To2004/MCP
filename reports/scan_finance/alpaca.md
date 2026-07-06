# Scan — alpaca

_kind=filesystem · provenance=offline-baseline · model_reviewed=False · bands={'low': 138, 'medium': 189, 'high': 87, 'critical': 0}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: a class of file the server can read or write, by type
- **blast_radius_meaning**: from reading one file to overwriting or destroying many
- **worked_example**: write_file on a .pem = critical: clobbers key material irreversibly

## Tool impact

| tool | impact |
| --- | --- |
| `place_stock_order` | 3 |
| `place_crypto_order` | 2 |
| `place_option_order` | 2 |
| `get_stock_bars` | 1 |
| `get_stock_quotes` | 1 |
| `get_stock_trades` | 1 |
| `get_crypto_bars` | 1 |
| `get_crypto_quotes` | 1 |
| `get_crypto_trades` | 1 |
| `get_locates` | 1 |
| `create_locate` | 2 |
| `get_locate` | 1 |
| `get_locate_quotes` | 1 |
| `get_account_info` | 1 |
| `get_account_activities` | 1 |
| `get_account_activities_by_type` | 1 |
| `get_account_config` | 2 |
| `update_account_config` | 2 |
| `get_portfolio_history` | 1 |
| `get_all_assets` | 2 |
| `get_asset` | 2 |
| `get_calendar` | 1 |
| `get_clock` | 1 |
| `get_corporate_action_announcements` | 1 |
| `get_corporate_action_announcement` | 1 |
| `get_option_contracts` | 1 |
| `get_option_contract` | 1 |
| `get_orders` | 1 |
| `cancel_all_orders` | 1 |
| `get_order_by_id` | 1 |
| `cancel_order_by_id` | 1 |
| `replace_order_by_id` | 2 |
| `get_order_by_client_id` | 1 |
| `get_all_positions` | 1 |
| `close_all_positions` | 3 |
| `get_open_position` | 1 |
| `close_position` | 3 |
| `do_not_exercise_options_position` | 1 |
| `exercise_options_position` | 2 |
| `get_watchlists` | 1 |
| `create_watchlist` | 2 |
| `get_watchlist_by_id` | 1 |
| `update_watchlist_by_id` | 3 |
| `add_asset_to_watchlist_by_id` | 2 |
| `delete_watchlist_by_id` | 3 |
| `remove_asset_from_watchlist_by_id` | 3 |
| `get_fixed_income_latest_quotes` | 1 |
| `get_index_latest_values` | 1 |
| `get_index_values` | 1 |
| `get_news` | 1 |
| `get_option_bars` | 1 |
| `get_option_exchange_codes` | 1 |
| `get_option_latest_quote` | 1 |
| `get_option_snapshot` | 1 |
| `get_option_chain` | 1 |
| `get_option_trades` | 1 |
| `get_option_latest_trade` | 1 |
| `get_market_movers` | 2 |
| `get_most_active_stocks` | 1 |
| `get_crypto_latest_bar` | 2 |
| `get_crypto_latest_orderbook` | 2 |
| `get_crypto_latest_quote` | 2 |
| `get_crypto_latest_trade` | 2 |
| `get_crypto_snapshot` | 2 |
| `get_corporate_actions` | 1 |
| `get_stock_latest_bar` | 1 |
| `get_stock_latest_quote` | 1 |
| `get_stock_snapshot` | 1 |
| `get_stock_latest_trade` | 1 |

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

| asset \ tool | place_stock_order | place_crypto_order | place_option_order | get_stock_bars | get_stock_quotes | get_stock_trades | get_crypto_bars | get_crypto_quotes | get_crypto_trades | get_locates | create_locate | get_locate | get_locate_quotes | get_account_info | get_account_activities | get_account_activities_by_type | get_account_config | update_account_config | get_portfolio_history | get_all_assets | get_asset | get_calendar | get_clock | get_corporate_action_announcements | get_corporate_action_announcement | get_option_contracts | get_option_contract | get_orders | cancel_all_orders | get_order_by_id | cancel_order_by_id | replace_order_by_id | get_order_by_client_id | get_all_positions | close_all_positions | get_open_position | close_position | do_not_exercise_options_position | exercise_options_position | get_watchlists | create_watchlist | get_watchlist_by_id | update_watchlist_by_id | add_asset_to_watchlist_by_id | delete_watchlist_by_id | remove_asset_from_watchlist_by_id | get_fixed_income_latest_quotes | get_index_latest_values | get_index_values | get_news | get_option_bars | get_option_exchange_codes | get_option_latest_quote | get_option_snapshot | get_option_chain | get_option_trades | get_option_latest_trade | get_market_movers | get_most_active_stocks | get_crypto_latest_bar | get_crypto_latest_orderbook | get_crypto_latest_quote | get_crypto_latest_trade | get_crypto_snapshot | get_corporate_actions | get_stock_latest_bar | get_stock_latest_quote | get_stock_snapshot | get_stock_latest_trade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `.txt` | 24 🟠 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 24 🟠 | 2 🟢 | 24 🟠 | 2 🟢 | 8 🟡 | 2 🟢 | 8 🟡 | 2 🟢 | 24 🟠 | 8 🟡 | 24 🟠 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.csv` | 48 🟠 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 48 🟠 | 8 🟡 | 48 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 48 🟠 | 24 🟠 | 48 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 24 🟠 | 24 🟠 | 24 🟠 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 |
| `.json` | 48 🟠 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 48 🟠 | 8 🟡 | 48 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 48 🟠 | 24 🟠 | 48 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 24 🟠 | 24 🟠 | 24 🟠 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 |
| `.md` | 24 🟠 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 24 🟠 | 2 🟢 | 24 🟠 | 2 🟢 | 8 🟡 | 2 🟢 | 8 🟡 | 2 🟢 | 24 🟠 | 8 🟡 | 24 🟠 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.png` | 24 🟠 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 24 🟠 | 2 🟢 | 24 🟠 | 2 🟢 | 8 🟡 | 2 🟢 | 8 🟡 | 2 🟢 | 24 🟠 | 8 🟡 | 24 🟠 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.py` | 48 🟠 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 48 🟠 | 8 🟡 | 48 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 48 🟠 | 24 🟠 | 48 🟠 | 48 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 24 🟠 | 24 🟠 | 24 🟠 | 24 🟠 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 |
