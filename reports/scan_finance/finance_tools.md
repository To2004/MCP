# Scan — finance_tools

_kind=filesystem · provenance=offline-baseline · model_reviewed=False · bands={'low': 48, 'medium': 51, 'high': 3, 'critical': 0}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: a class of file the server can read or write, by type
- **blast_radius_meaning**: from reading one file to overwriting or destroying many
- **worked_example**: write_file on a .pem = critical: clobbers key material irreversibly

## Tool impact

| tool | impact |
| --- | --- |
| `get_ticker_data` | 1 |
| `get_price_history` | 1 |
| `get_financial_statements` | 1 |
| `get_earnings_history` | 1 |
| `get_ticker_news_tool` | 1 |
| `super_option_tool` | 1 |
| `get_top25_holders` | 1 |
| `get_insider_trades` | 1 |
| `get_overall_sentiment_tool` | 1 |
| `get_historical_fng_tool` | 1 |
| `analyze_fng_trend` | 1 |
| `calculate` | 1 |
| `get_current_time` | 1 |
| `get_fred_series` | 1 |
| `search_fred_series` | 1 |
| `cnbc_news_feed` | 1 |
| `social_media_feed` | 2 |

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

| asset \ tool | get_ticker_data | get_price_history | get_financial_statements | get_earnings_history | get_ticker_news_tool | super_option_tool | get_top25_holders | get_insider_trades | get_overall_sentiment_tool | get_historical_fng_tool | analyze_fng_trend | calculate | get_current_time | get_fred_series | search_fred_series | cnbc_news_feed | social_media_feed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `.txt` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 |
| `.csv` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 |
| `.json` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 |
| `.md` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 |
| `.png` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 |
| `.py` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 |
