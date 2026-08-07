# Scan — yfinance

_kind=finance · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v5r_nacombo · bands={'low': 9, 'medium': 3, 'high': 0, 'critical': 0, 'na': 33}_

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

- **mcp_kind**: financial data service

## Tool impact

| tool | impact |
| --- | --- |
| `get_historical_stock_prices` | 3 |
| `get_stock_info` | 3 |
| `get_yahoo_finance_news` | 3 |
| `get_stock_actions` | 3 |
| `get_financial_statement` | 3 |
| `get_holder_info` | 3 |
| `get_option_expiration_dates` | 3 |
| `get_option_chain` | 3 |
| `get_recommendations` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `public-market-data` | 1 |
| `public-fundamentals` | 1 |
| `public-news` | 1 |
| `option-expiry-catalog` | 2 |
| `research-query-pattern` | 3 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v5r_nacombo, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | get_historical_stock_prices | get_stock_info | get_yahoo_finance_news | get_stock_actions | get_financial_statement | get_holder_info | get_option_expiration_dates | get_option_chain | get_recommendations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-market-data` | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | N/A | 6 (1×2×3) 🟢 | N/A | N/A | N/A | 6 (1×2×3) 🟢 | N/A |
| `public-fundamentals` | N/A | N/A | N/A | N/A | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | N/A | N/A | 6 (1×2×3) 🟢 |
| `public-news` | N/A | N/A | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `option-expiry-catalog` | N/A | N/A | N/A | N/A | N/A | N/A | 12 (2×2×3) 🟢 | N/A | N/A |
| `research-query-pattern` | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | N/A | N/A | 27 (3×3×3) 🟢 | N/A | N/A | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | get_historical_stock_prices | get_stock_info | get_yahoo_finance_news | get_stock_actions | get_financial_statement | get_holder_info | get_option_expiration_dates | get_option_chain | get_recommendations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-market-data` | 2 | 2 | N/A | 2 | N/A | N/A | N/A | 2 | N/A |
| `public-fundamentals` | N/A | N/A | N/A | N/A | 2 | 2 | N/A | N/A | 2 |
| `public-news` | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `option-expiry-catalog` | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A |
| `research-query-pattern` | 3 | 3 | N/A | N/A | 3 | N/A | N/A | N/A | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `get_historical_stock_prices` | **READ** | 2 (Low) | READ | rules |
| `get_stock_info` | **METADATA** | 1 (Low) | METADATA | rules |
| `get_yahoo_finance_news` | **READ** | 2 (Low) | READ | rules |
| `get_stock_actions` | **READ** | 2 (Low) | READ | rules |
| `get_financial_statement` | **METADATA** | 1 (Low) | METADATA | rules |
| `get_holder_info` | **METADATA** | 1 (Low) | METADATA | rules |
| `get_option_expiration_dates` | **READ** | 2 (Low) | READ | rules |
| `get_option_chain` | **READ** | 2 (Low) | READ | rules |
| `get_recommendations` | **READ** | 2 (Low) | READ | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `get_historical_stock_prices` | `period` | 4 | unbounded (no LIMIT) | can amplify risk by specifying a very long period, increasin |
| `get_historical_stock_prices` | `interval` | 3 | — | can affect the granularity and thus the volume of data reque |
| `get_historical_stock_prices` | `ticker` | 2 | — | merely names the target |
| `get_stock_info` | `ticker` | 2 | — | merely names the target |
| `get_yahoo_finance_news` | `ticker` | 2 | — | merely names the target |
| `get_stock_actions` | `ticker` | 2 | — | merely names the target |
| `get_financial_statement` | `financial_type` | 3 | — | could potentially affect data volume and type requested |
| `get_financial_statement` | `ticker` | 2 | — | merely names the target |
| `get_holder_info` | `holder_type` | 3 | — | can potentially widen scope depending on type selected |
| `get_holder_info` | `ticker` | 2 | — | merely names the target |
| `get_option_expiration_dates` | `ticker` | 2 | — | merely names the target |
| `get_option_chain` | `ticker` | 2 | — | merely names the target |
| `get_option_chain` | `expiration_date` | 1 | — | limits data scope to a specific date |
| `get_option_chain` | `option_type` | 1 | — | narrows the type of options returned |
| `get_recommendations` | `months_back` | 4 | >= 60 | increases the breadth of data retrieval, potentially overloa |
| `get_recommendations` | `recommendation_type` | 3 | — | could be used to filter or manipulate data scope |
| `get_recommendations` | `ticker` | 2 | — | merely names the target |
