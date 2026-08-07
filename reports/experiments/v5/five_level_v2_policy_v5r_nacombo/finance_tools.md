# Scan — finance-tools-mcp

_kind=finance · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v5r_nacombo · bands={'low': 18, 'medium': 9, 'high': 0, 'critical': 0, 'na': 75}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = LLM classification against the org POLICY (classify -> map; the org supplies no numbers)
- tool impact = deterministic ladder (static_impact.py); the v4 impact prompt decides only where the ladder abstains (confidence < 0.5)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- blast floor, UNGATED: 
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof: REMOVED in this mode (a cap can only under-score)
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: financial data

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
| `calculate` | 3 |
| `get_current_time` | 1 |
| `get_fred_series` | 2 |
| `search_fred_series` | 2 |
| `cnbc_news_feed` | 3 |
| `social_media_feed` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `expression-evaluator` | 4 |
| `research-query-pattern` | 3 |
| `public-market-data` | 1 |
| `public-macro-series` | 1 |
| `public-news-and-sentiment` | 1 |
| `server-clock` | 2 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v5r_nacombo, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | get_ticker_data | get_price_history | get_financial_statements | get_earnings_history | get_ticker_news_tool | super_option_tool | get_top25_holders | get_insider_trades | get_overall_sentiment_tool | get_historical_fng_tool | analyze_fng_trend | calculate | get_current_time | get_fred_series | search_fred_series | cnbc_news_feed | social_media_feed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `expression-evaluator` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 36 (4×3×3) 🟡 | N/A | N/A | N/A | N/A | N/A |
| `research-query-pattern` | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | N/A | N/A | N/A | N/A | N/A | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | N/A | N/A |
| `public-market-data` | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | N/A | 6 (1×2×3) 🟢 | 9 (1×3×3) 🟢 | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `public-macro-series` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×2×2) 🟢 | 4 (1×2×2) 🟢 | N/A | N/A |
| `public-news-and-sentiment` | N/A | N/A | N/A | N/A | 6 (1×2×3) 🟢 | N/A | N/A | N/A | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 |
| `server-clock` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 (2×1×1) 🟢 | N/A | N/A | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | get_ticker_data | get_price_history | get_financial_statements | get_earnings_history | get_ticker_news_tool | super_option_tool | get_top25_holders | get_insider_trades | get_overall_sentiment_tool | get_historical_fng_tool | analyze_fng_trend | calculate | get_current_time | get_fred_series | search_fred_series | cnbc_news_feed | social_media_feed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `expression-evaluator` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A |
| `research-query-pattern` | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | N/A | N/A | N/A | N/A | N/A | 2 | 2 | N/A | N/A |
| `public-market-data` | 2 | 2 | 2 | 2 | N/A | 2 | 3 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `public-macro-series` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 2 | N/A | N/A |
| `public-news-and-sentiment` | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | 2 | 2 | 2 | N/A | N/A | N/A | N/A | 2 | 2 |
| `server-clock` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A |

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
