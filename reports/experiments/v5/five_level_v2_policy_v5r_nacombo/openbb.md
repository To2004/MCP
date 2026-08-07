# Scan — openbb-platform

_kind=finance · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v5r_nacombo · bands={'low': 23, 'medium': 12, 'high': 1, 'critical': 0, 'na': 114}_

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

- **mcp_kind**: cloud infra

## Tool impact

| tool | impact |
| --- | --- |
| `install_skill` | 4 |
| `crypto_price_historical` | 3 |
| `derivatives_options_chains` | 3 |
| `derivatives_options_surface` | 2 |
| `derivatives_futures_historical` | 3 |
| `derivatives_futures_curve` | 3 |
| `equity_estimates_consensus` | 3 |
| `equity_discovery_gainers` | 3 |
| `equity_discovery_losers` | 3 |
| `equity_discovery_active` | 3 |
| `equity_discovery_undervalued_large_caps` | 3 |
| `equity_discovery_undervalued_growth` | 3 |
| `equity_discovery_aggressive_small_caps` | 3 |
| `equity_discovery_growth_tech` | 3 |
| `equity_fundamental_balance` | 3 |
| `equity_fundamental_cash` | 3 |
| `equity_fundamental_dividends` | 3 |
| `equity_fundamental_income` | 3 |
| `equity_fundamental_metrics` | 3 |
| `equity_fundamental_management` | 3 |
| `equity_ownership_share_statistics` | 3 |
| `equity_price_quote` | 3 |
| `equity_price_historical` | 3 |
| `equity_screener` | 3 |
| `equity_profile` | 2 |
| `news_company` | 3 |
| `list_prompts` | 2 |
| `get_prompt` | 2 |
| `list_resources` | 2 |
| `read_resource` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `server-capability-install` | 4 |
| `screening-and-fanout` | 4 |
| `public-market-data` | 1 |
| `public-fundamentals-and-ownership` | 1 |
| `platform-catalogs` | 3 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v5r_nacombo, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | install_skill | crypto_price_historical | derivatives_options_chains | derivatives_options_surface | derivatives_futures_historical | derivatives_futures_curve | equity_estimates_consensus | equity_discovery_gainers | equity_discovery_losers | equity_discovery_active | equity_discovery_undervalued_large_caps | equity_discovery_undervalued_growth | equity_discovery_aggressive_small_caps | equity_discovery_growth_tech | equity_fundamental_balance | equity_fundamental_cash | equity_fundamental_dividends | equity_fundamental_income | equity_fundamental_metrics | equity_fundamental_management | equity_ownership_share_statistics | equity_price_quote | equity_price_historical | equity_screener | equity_profile | news_company | list_prompts | get_prompt | list_resources | read_resource |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `server-capability-install` | 64 (4×4×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `screening-and-fanout` | N/A | N/A | N/A | 16 (4×2×2) 🟢 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | N/A | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 48 (4×4×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A |
| `public-market-data` | N/A | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 4 (1×2×2) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | N/A | 4 (1×2×2) 🟢 | N/A | N/A | N/A | N/A | 6 (1×2×3) 🟢 |
| `public-fundamentals-and-ownership` | N/A | N/A | N/A | N/A | N/A | N/A | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | N/A | N/A | N/A | 4 (1×2×2) 🟢 | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A |
| `platform-catalogs` | 48 (3×4×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | 18 (3×2×3) 🟢 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | install_skill | crypto_price_historical | derivatives_options_chains | derivatives_options_surface | derivatives_futures_historical | derivatives_futures_curve | equity_estimates_consensus | equity_discovery_gainers | equity_discovery_losers | equity_discovery_active | equity_discovery_undervalued_large_caps | equity_discovery_undervalued_growth | equity_discovery_aggressive_small_caps | equity_discovery_growth_tech | equity_fundamental_balance | equity_fundamental_cash | equity_fundamental_dividends | equity_fundamental_income | equity_fundamental_metrics | equity_fundamental_management | equity_ownership_share_statistics | equity_price_quote | equity_price_historical | equity_screener | equity_profile | news_company | list_prompts | get_prompt | list_resources | read_resource |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `server-capability-install` | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `screening-and-fanout` | N/A | N/A | N/A | 2 | 3 | 3 | N/A | 3 | 3 | 3 | 3 | 3 | 3 | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | N/A | N/A | N/A | N/A | N/A | N/A |
| `public-market-data` | N/A | 2 | 2 | 2 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 2 | N/A | 2 | N/A | N/A | N/A | N/A | 2 |
| `public-fundamentals-and-ownership` | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 2 | 2 | 2 | 2 | 2 | 2 | N/A | N/A | N/A | 2 | 2 | N/A | N/A | N/A | N/A |
| `platform-catalogs` | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 2 | 2 | 2 |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `install_skill` | **READ** | 2 (Low) | READ | verb-fallback |
| `crypto_price_historical` | **READ** | 2 (Low) | READ | verb-fallback |
| `derivatives_options_chains` | **READ** | 2 (Low) | READ | verb-fallback |
| `derivatives_options_surface` | **READ** | 2 (Low) | READ | verb-fallback |
| `derivatives_futures_historical` | **READ** | 2 (Low) | READ | verb-fallback |
| `derivatives_futures_curve` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_estimates_consensus` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_discovery_gainers` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_discovery_losers` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_discovery_active` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_discovery_undervalued_large_caps` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_discovery_undervalued_growth` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_discovery_aggressive_small_caps` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_discovery_growth_tech` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_fundamental_balance` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_fundamental_cash` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_fundamental_dividends` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_fundamental_income` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_fundamental_metrics` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `equity_fundamental_management` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `equity_ownership_share_statistics` | **BROADCAST** | 4 (High) | BROADCAST | verb-fallback |
| `equity_price_quote` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_price_historical` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_screener` | **READ** | 2 (Low) | READ | verb-fallback |
| `equity_profile` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `news_company` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `list_prompts` | **LIST** | 1 (Low) | LIST | rules |
| `get_prompt` | **READ** | 2 (Low) | READ | rules |
| `list_resources` | **LIST** | 1 (Low) | LIST | rules |
| `read_resource` | **READ** | 2 (Low) | READ | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `install_skill` | `files` | 5 | — | fully controlled payload with arbitrary content |
| `install_skill` | `target` | 3 | — | indicates the provider, could target critical systems |
| `install_skill` | `skill_name` | 2 | — | names the target directory, limited control |
| `crypto_price_historical` | `symbol` | 3 | >= 10 symbols | can fan out to multiple targets |
| `crypto_price_historical` | `provider` | 2 | — | names the target, limited impact |
| `crypto_price_historical` | `start_date` | 2 | — | defines data range, limited impact |
| `crypto_price_historical` | `end_date` | 2 | — | defines data range, limited impact |
| `crypto_price_historical` | `interval` | 1 | — | affects granularity of returned data, low risk |
| `derivatives_options_chains` | `symbol` | 3 | — | can be used to target arbitrary symbols, potentially leading |
| `derivatives_options_chains` | `provider` | 2 | — | likely a fixed enum/structural field |
| `derivatives_options_surface` | `data` | 5 | unbounded (no LIMIT) | payload the caller fully controls, can be large and complex |
| `derivatives_options_surface` | `chart_params` | 4 | — | can influence output scope or complexity |
| `derivatives_options_surface` | `dte_min` | 3 | dte_min <= -1000 | can widen scope to unrealistic values |
| `derivatives_options_surface` | `dte_max` | 3 | dte_max >= 10000 | can widen scope to unrealistic values |
| `derivatives_options_surface` | `strike_min` | 3 | strike_min <= -1000000 | can widen scope to unrealistic values |
| `derivatives_options_surface` | `strike_max` | 3 | strike_max >= 1000000 | can widen scope to unrealistic values |
| `derivatives_options_surface` | `target` | 2 | — | merely names the target |
| `derivatives_options_surface` | `moneyness` | 2 | — | may influence filtering but not directly risky |
| `derivatives_options_surface` | `oi` | 2 | — | boolean flag that may influence filtering but not directly r |
| `derivatives_options_surface` | `volume` | 2 | — | boolean flag that may influence filtering but not directly r |
| `derivatives_options_surface` | `underlying_price` | 1 | — | fixed value, no amplification |
| `derivatives_options_surface` | `option_type` | 1 | — | likely a fixed enum or structural field |
| `derivatives_options_surface` | `theme` | 1 | — | likely a fixed enum or structural field |
| `derivatives_futures_historical` | `symbol` | 3 | >= 10 symbols | can fan out to multiple symbols, increasing load |
| `derivatives_futures_historical` | `interval` | 3 | — | can affect the volume of data returned based on time granula |
| `derivatives_futures_historical` | `provider` | 2 | — | names the data source, low risk |
| `derivatives_futures_historical` | `start_date` | 2 | — | defines the start of data range, low risk |
| `derivatives_futures_historical` | `end_date` | 2 | — | defines the end of data range, low risk |
| `derivatives_futures_historical` | `expiration` | 2 | — | specifies future expiry date, low risk |
| `derivatives_futures_curve` | `date` | 4 | unbounded (no LIMIT) | allows for multiple comma-separated items, potentially leadi |
| `derivatives_futures_curve` | `symbol` | 3 | — | identifies the financial instrument but doesn't control beha |
| `derivatives_futures_curve` | `provider` | 2 | — | names the data provider, low risk |
| `equity_estimates_consensus` | `symbol` | 4 | >= 100 symbols | can cause bulk fan-out with multiple comma-separated items |
| `equity_estimates_consensus` | `provider` | 2 | — | names the data provider, limited impact |
| `equity_discovery_gainers` | `limit` | 4 | >= 500 | controls result set size, high magnitude can overload server |
| `equity_discovery_gainers` | `provider` | 2 | — | names the data source, low risk |
| `equity_discovery_gainers` | `sort` | 1 | — | defines order, no amplification of risk |
| `equity_discovery_losers` | `limit` | 4 | >= 500 | controls result set size, high magnitude can overload server |
| `equity_discovery_losers` | `provider` | 2 | — | names the data source, low risk |
| `equity_discovery_losers` | `sort` | 1 | — | defines order, no amplification of risk |
| `equity_discovery_active` | `limit` | 4 | >= 500 | controls result set size, high magnitude can overload server |
| `equity_discovery_active` | `provider` | 2 | — | names the data source, low risk |
| `equity_discovery_active` | `sort` | 1 | — | defines order, no amplification of risk |
| `equity_discovery_undervalued_large_caps` | `limit` | 4 | >= 500 | controls the number of results, high risk for large values |
| `equity_discovery_undervalued_large_caps` | `provider` | 2 | — | names the data source, low risk |
| `equity_discovery_undervalued_large_caps` | `sort` | 1 | — | defines sort order, minimal impact on server load |
| `equity_discovery_undervalued_growth` | `limit` | 4 | >= 500 | controls result set size, high magnitude can overload server |
| `equity_discovery_undervalued_growth` | `provider` | 2 | — | names the data source, low risk |
| `equity_discovery_undervalued_growth` | `sort` | 1 | — | defines order, no amplification of risk |
| `equity_discovery_aggressive_small_caps` | `limit` | 4 | unbounded (no LIMIT) | controls the number of results and can lead to high server l |
| `equity_discovery_aggressive_small_caps` | `provider` | 2 | — | names the data source, low risk |
| `equity_discovery_aggressive_small_caps` | `sort` | 1 | — | defines sort order, minimal impact on server load |
| `equity_discovery_growth_tech` | `limit` | 4 | >= 500 | controls result set size, high magnitude can overload server |
| `equity_discovery_growth_tech` | `provider` | 2 | — | names the data source, low risk |
| `equity_discovery_growth_tech` | `sort` | 1 | — | defines order, no amplification of risk |
| `equity_fundamental_balance` | `limit` | 4 | >= 10000 | controls the number of data entries returned, high risk for  |
| `equity_fundamental_balance` | `symbol` | 3 | — | identifies the company but doesn't control call volume or sc |
| `equity_fundamental_balance` | `provider` | 2 | — | names the data provider, low risk |
| `equity_fundamental_balance` | `period` | 2 | — | defines time period but doesn't control call volume or scope |
| `equity_fundamental_cash` | `limit` | 5 | >= 10000 | controls the number of data entries returned, high risk for  |
| `equity_fundamental_cash` | `symbol` | 3 | — | identifies the company but doesn't control call volume or sc |
| `equity_fundamental_cash` | `provider` | 2 | — | names the data provider, low risk |
| `equity_fundamental_cash` | `period` | 2 | — | defines time period but doesn't control call volume or scope |
| `equity_fundamental_dividends` | `symbol` | 3 | — | identifies target company, potential for abuse if misused to |
| `equity_fundamental_dividends` | `provider` | 2 | — | names the data provider, limited impact |
| `equity_fundamental_dividends` | `start_date` | 1 | — | defines the start of data range, limited risk |
| `equity_fundamental_dividends` | `end_date` | 1 | — | defines the end of data range, limited risk |
| `equity_fundamental_income` | `limit` | 5 | >= 10000 | controls the number of data entries returned, high risk for  |
| `equity_fundamental_income` | `symbol` | 3 | — | identifies the company but doesn't control output size or be |
| `equity_fundamental_income` | `provider` | 2 | — | names the data provider, low risk |
| `equity_fundamental_income` | `period` | 2 | — | defines time period but doesn't control output size or behav |
| `equity_fundamental_metrics` | `symbol` | 4 | >= 10 symbols | can cause bulk requests, increasing load |
| `equity_fundamental_metrics` | `provider` | 2 | — | names the data source, limited impact |
| `equity_fundamental_management` | `provider` | 2 | — | potentially allows selection of untrusted data sources |
| `equity_fundamental_management` | `symbol` | 1 | — | merely names the target company, low risk |
| `equity_ownership_share_statistics` | `symbol` | 4 | >= 10 symbols | can cause bulk requests, amplifying load |
| `equity_ownership_share_statistics` | `provider` | 2 | — | names the data source, limited impact |
| `equity_price_quote` | `symbol` | 4 | >= 10 symbols | can cause bulk requests, increasing load |
| `equity_price_quote` | `provider` | 2 | — | names the data source, limited impact |
| `equity_price_historical` | `symbol` | 3 | — | can specify multiple symbols, increasing load |
| `equity_price_historical` | `extended_hours` | 3 | — | can increase data volume and processing time |
| `equity_price_historical` | `provider` | 2 | — | names the data source, limited impact |
| `equity_price_historical` | `interval` | 2 | — | affects granularity but not load significantly |
| `equity_price_historical` | `include_actions` | 2 | — | may slightly increase the amount of returned data |
| `equity_price_historical` | `start_date` | 1 | — | defines the start of data range, limited impact |
| `equity_price_historical` | `end_date` | 1 | — | defines the end of data range, limited impact |
| `equity_price_historical` | `adjustment` | 1 | — | affects how data is adjusted, limited impact on load |
| `equity_screener` | `limit` | 4 | == 0 | unbounded result set can overwhelm server |
| `equity_screener` | `mktcap_min` | 3 | >= 50000000000 | can filter out too many companies if set very high |
| `equity_screener` | `mktcap_max` | 3 | <= 1000000 | can filter out too many companies if set very low |
| `equity_screener` | `volume_min` | 3 | >= 50000000 | can filter out too many companies if set very high |
| `equity_screener` | `volume_max` | 3 | <= 1000 | can filter out too many companies if set very low |
| `equity_screener` | `provider` | 2 | — | names the data source |
| `equity_screener` | `price_min` | 2 | >= 5000 | can limit results to a narrow range |
| `equity_screener` | `price_max` | 2 | <= 1 | can limit results to a narrow range |
| `equity_screener` | `beta_min` | 2 | >= 5 | can limit results to a narrow range |
| `equity_screener` | `beta_max` | 2 | <= -1 | can limit results to a narrow range |
| `equity_screener` | `country` | 1 | — | limits to specific countries |
| `equity_screener` | `exchange` | 1 | — | limits to specific exchanges |
| `equity_screener` | `sector` | 1 | — | limits to specific sectors |
| `equity_screener` | `industry` | 1 | — | limits to specific industries |
| `equity_profile` | `symbol` | 4 | >= 10 symbols | can cause bulk requests, increasing load |
| `equity_profile` | `provider` | 2 | — | names the data source, limited impact |
| `news_company` | `limit` | 5 | >= 100 entries | can amplify call's risk by requesting large amounts of data |
| `news_company` | `symbol` | 4 | >= 10 symbols | can cause bulk fan-out with multiple symbols |
| `news_company` | `provider` | 2 | — | names the data source, low risk |
| `news_company` | `start_date` | 2 | — | defines the start of data range, low risk |
| `news_company` | `end_date` | 2 | — | defines the end of data range, low risk |
| `get_prompt` | `arguments` | 5 | — | fully controlled payload by caller |
| `get_prompt` | `name` | 2 | — | merely names the target |
| `read_resource` | `uri` | 4 | — | can point to sensitive resources |
