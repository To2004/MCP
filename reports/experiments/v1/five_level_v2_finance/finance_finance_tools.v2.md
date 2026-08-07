# Scan — finance:finance_tools

_kind=finance_tools · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_na · bands={'low': 1, 'medium': 15, 'high': 11, 'critical': 0, 'na': 177}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Inferred domain profile

- **mcp_kind**: financial data retrieval system
- **asset_meaning**: collections of financial and market-related information such as stock prices, financial statements, news, sentiment indicators, insider trading records, and more.
- **blast_radius_meaning**: the extent to which a tool can access or affect different types of financial assets; from accessing a single record to aggregating data across multiple asset classes.
- **dangerous_classes**: holds sensitive market information, includes insider trading records, aggregates financial statements at scale
- **worked_example**: get_ticker_data tool paired with ticker-records asset class, where the severity rationale is that accessing comprehensive data for a single stock can reveal significant insights into its performance and market sentiment.

## Tool impact

| tool | impact |
| --- | --- |
| `get_ticker_data` | 3 |
| `get_price_history` | 3 |
| `get_financial_statements` | 3 |
| `get_earnings_history` | 3 |
| `get_ticker_news_tool` | 3 |
| `super_option_tool` | 3 |
| `get_top25_holders` | 3 |
| `get_insider_trades` | 3 |
| `get_overall_sentiment_tool` | 3 |
| `get_historical_fng_tool` | 3 |
| `analyze_fng_trend` | 3 |
| `calculate` | 5 |
| `get_current_time` | 1 |
| `get_fred_series` | 3 |
| `search_fred_series` | 2 |
| `cnbc_news_feed` | 3 |
| `social_media_feed` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `ticker-records` | 4 |
| `price-history-records` | 1 |
| `financial-statements` | 4 |
| `option-data` | 3 |
| `institutional-holder-records` | 4 |
| `insider-trading-records` | 5 |
| `market-sentiment-indicators` | 1 |
| `historical-fng-data` | 1 |
| `fng-index-records` | 1 |
| `fred-series-records` | 1 |
| `news-feed` | 1 |
| `social-media-posts` | 1 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_na, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | get_ticker_data | get_price_history | get_financial_statements | get_earnings_history | get_ticker_news_tool | super_option_tool | get_top25_holders | get_insider_trades | get_overall_sentiment_tool | get_historical_fng_tool | analyze_fng_trend | calculate | get_current_time | get_fred_series | search_fred_series | cnbc_news_feed | social_media_feed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ticker-records` | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | N/A | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 24 (4×2×3) 🟢 | 36 (4×3×3) 🟡 | 24 (4×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `price-history-records` | 3 (1×1×3) 🟢 | 9 (1×3×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 (1×1×3) 🟢 | N/A | N/A | N/A |
| `financial-statements` | N/A | N/A | 36 (4×3×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `option-data` | N/A | N/A | N/A | N/A | N/A | 9 (3×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `institutional-holder-records` | N/A | N/A | N/A | N/A | N/A | N/A | 24 (4×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `insider-trading-records` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 45 (5×3×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `market-sentiment-indicators` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 9 (1×3×3) 🟢 | 9 (1×3×3) 🟢 | 9 (1×3×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `historical-fng-data` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 9 (1×3×3) 🟢 | 9 (1×3×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `fng-index-records` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 (1×1×3) 🟢 | 9 (1×3×3) 🟢 | 9 (1×3×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `fred-series-records` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 (1×1×3) 🟢 | 4 (1×2×2) 🟢 | N/A | N/A |
| `news-feed` | N/A | N/A | N/A | N/A | 3 (1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 6 (1×2×3) 🟢 | N/A |
| `social-media-posts` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 9 (1×3×3) 🟢 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | get_ticker_data | get_price_history | get_financial_statements | get_earnings_history | get_ticker_news_tool | super_option_tool | get_top25_holders | get_insider_trades | get_overall_sentiment_tool | get_historical_fng_tool | analyze_fng_trend | calculate | get_current_time | get_fred_series | search_fred_series | cnbc_news_feed | social_media_feed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ticker-records` | 1 | 1 | N/A | 1 | 1 | 2 | 3 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `price-history-records` | 1 | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A |
| `financial-statements` | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `option-data` | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `institutional-holder-records` | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `insider-trading-records` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `market-sentiment-indicators` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 3 | 3 | N/A | N/A | N/A | N/A | N/A | N/A |
| `historical-fng-data` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 3 | N/A | N/A | N/A | N/A | N/A | N/A |
| `fng-index-records` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 3 | 3 | N/A | N/A | N/A | N/A | N/A | N/A |
| `fred-series-records` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 2 | N/A | N/A |
| `news-feed` | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A |
| `social-media-posts` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

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
