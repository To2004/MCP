# Scan — finance:finance_tools

_kind=finance · provenance=llm-scan · model_reviewed=True · bands={'low': 45, 'medium': 34, 'high': 6, 'critical': 0}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: financial_data_service
- **asset_meaning**: Financial data assets such as equity prices, financial statements, macroeconomic series, news feeds, and API credentials.
- **blast_radius_meaning**: The extent to which a tool can access or modify an asset. A narrow touch might involve reading a single ticker's price history, while the most severe action could involve leaking sensitive API credentials or altering critical market data.
- **worked_example**: The tool 'get_ticker_news_tool' accessing the asset class 'news_and_sentiment' is considered low severity as it only retrieves public news data.

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
| `social_media_feed` | 1 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `equity_market_data` | 4 |
| `macro_economic_data` | 2 |
| `news_and_sentiment` | 1 |
| `options_data` | 1 |
| `server_api_credentials` | 5 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)` and its band. Likelihood is pinned to 1.0 and omitted._

| asset \ tool | get_ticker_data | get_price_history | get_financial_statements | get_earnings_history | get_ticker_news_tool | super_option_tool | get_top25_holders | get_insider_trades | get_overall_sentiment_tool | get_historical_fng_tool | analyze_fng_trend | calculate | get_current_time | get_fred_series | search_fred_series | cnbc_news_feed | social_media_feed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `equity_market_data` | 16 (4×4×1) 🟠 | 4 (4×1×1) 🟡 | 4 (4×1×1) 🟡 | 4 (4×1×1) 🟡 | 4 (4×1×1) 🟡 | 4 (4×1×1) 🟡 | 4 (4×1×1) 🟡 | 4 (4×1×1) 🟡 | 4 (4×1×1) 🟡 | 16 (4×4×1) 🟠 | 16 (4×4×1) 🟠 | 4 (4×1×1) 🟡 | 4 (4×1×1) 🟡 | 4 (4×1×1) 🟡 | 16 (4×4×1) 🟠 | 16 (4×4×1) 🟠 | 16 (4×4×1) 🟠 |
| `macro_economic_data` | 2 (2×1×1) 🟢 | 2 (2×1×1) 🟢 | 2 (2×1×1) 🟢 | 2 (2×1×1) 🟢 | 2 (2×1×1) 🟢 | 2 (2×1×1) 🟢 | 2 (2×1×1) 🟢 | 2 (2×1×1) 🟢 | 8 (2×4×1) 🟡 | 8 (2×4×1) 🟡 | 8 (2×4×1) 🟡 | 2 (2×1×1) 🟢 | 2 (2×1×1) 🟢 | 2 (2×1×1) 🟢 | 8 (2×4×1) 🟡 | 8 (2×4×1) 🟡 | 8 (2×4×1) 🟡 |
| `news_and_sentiment` | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 |
| `options_data` | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 2 (1×2×1) 🟢 | 4 (1×4×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 |
| `server_api_credentials` | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 | 10 (5×2×1) 🟡 | 5 (5×1×1) 🟡 | 5 (5×1×1) 🟡 |

## Blast radius (tool reach · 1–5)

_How many items ONE call of the tool touches on that asset — a count of reach, not severity. Constant down a column is expected for same-structure assets; `⚠` marks a tool the consistency check found drifting._

| asset \ tool | get_ticker_data ⚠ | get_price_history | get_financial_statements | get_earnings_history | get_ticker_news_tool | super_option_tool | get_top25_holders | get_insider_trades | get_overall_sentiment_tool ⚠ | get_historical_fng_tool | analyze_fng_trend | calculate | get_current_time | get_fred_series | search_fred_series | cnbc_news_feed ⚠ | social_media_feed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `equity_market_data` | 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 4 | 4 | 1 | 1 | 1 | 4 | 4 | 4 |
| `macro_economic_data` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 4 | 4 | 4 | 1 | 1 | 1 | 4 | 4 | 4 |
| `news_and_sentiment` | 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 4 | 4 | 1 | 1 | 1 | 4 | 4 | 4 |
| `options_data` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 4 | 4 | 1 | 1 | 1 | 4 | 1 | 4 |
| `server_api_credentials` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 |

### Blast-radius drift (flagged for review)

| tool | asset_structure | values | by asset |
| --- | --- | --- | --- |
| `cnbc_news_feed` | container | 1/4 | equity_market_data:4, macro_economic_data:4, news_and_sentiment:4, options_data:1 |
| `get_overall_sentiment_tool` | container | 1/2/4 | equity_market_data:1, macro_economic_data:4, news_and_sentiment:1, options_data:2 |
| `get_ticker_data` | container | 1/4 | equity_market_data:4, macro_economic_data:1, news_and_sentiment:4 |

## Tool atomic operations

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `get_ticker_data` | **READ** | 2 (Low) | READ | rules |
| `get_price_history` | **READ** | 2 (Low) | READ | rules |
| `get_financial_statements` | **METADATA** | 1 (Low) | METADATA | rules |
| `get_earnings_history` | **READ** | 2 (Low) | READ | rules |
| `get_ticker_news_tool` | **READ** | 2 (Low) | READ | rules |
| `super_option_tool` | **READ** | 2 (Low) | READ | verb-fallback |
| `get_top25_holders` | **READ** | 2 (Low) | READ | rules |
| `get_insider_trades` | **READ** | 2 (Low) | READ | rules |
| `get_overall_sentiment_tool` | **READ** | 2 (Low) | READ | rules |
| `get_historical_fng_tool` | **READ** | 2 (Low) | READ | rules |
| `analyze_fng_trend` | **READ** | 2 (Low) | READ | verb-fallback |
| `calculate` | **READ** | 2 (Low) | READ | verb-fallback |
| `get_current_time` | **READ** | 2 (Low) | READ | rules |
| `get_fred_series` | **READ** | 2 (Low) | READ | rules |
| `search_fred_series` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `cnbc_news_feed` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `social_media_feed` | **METADATA** | 1 (Low) | METADATA | verb-fallback |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `get_ticker_data` | `ticker` | 2 | — | merely names the target |
| `get_price_history` | `start_date` | 4 | — | can extend the time range, increasing load |
| `get_price_history` | `end_date` | 4 | — | can extend the time range, increasing load |
| `get_price_history` | `period` | 3 | — | can widen scope of data retrieval |
| `get_price_history` | `ticker` | 2 | — | merely names the target |
| `get_financial_statements` | `ticker` | 2 | — | merely names the target |
| `get_financial_statements` | `statement_type` | 1 | — | fixed enum/structural field |
| `get_financial_statements` | `frequency` | 1 | — | fixed enum/structural field |
| `get_earnings_history` | `ticker` | 2 | — | merely names the target |
| `get_ticker_news_tool` | `ticker` | 2 | — | merely names the target |
| `super_option_tool` | `ticker` | 2 | — | merely names the target |
| `get_top25_holders` | `ticker` | 2 | — | merely names the target |
| `get_insider_trades` | `ticker` | 2 | — | merely names the target |
| `get_historical_fng_tool` | `days` | 3 | >= 1000 | potentially large data retrieval |
| `analyze_fng_trend` | `days` | 3 | >= 1000 | potentially large data request |
| `calculate` | `expression` | 4 | — | arbitrary code execution through mathematical expressions |
| `get_fred_series` | `series_id` | 2 | — | merely names the target |
| `search_fred_series` | `query` | 2 | — | limited to keyword search, no direct execution risk |
| `social_media_feed` | `keywords` | 3 | — | can broaden the scope of data retrieval |
