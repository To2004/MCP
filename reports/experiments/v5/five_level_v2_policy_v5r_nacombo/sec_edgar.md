# Scan — sec-edgar-mcp

_kind=finance · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v5r_nacombo · bands={'low': 24, 'medium': 3, 'high': 0, 'critical': 0, 'na': 99}_

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
| `get_cik_by_ticker` | 3 |
| `get_company_info` | 2 |
| `search_companies` | 2 |
| `get_company_facts` | 3 |
| `get_recent_filings` | 2 |
| `get_filing_content` | 3 |
| `analyze_8k` | 3 |
| `get_filing_sections` | 3 |
| `get_financials` | 3 |
| `get_segment_data` | 3 |
| `get_key_metrics` | 2 |
| `compare_periods` | 3 |
| `discover_company_metrics` | 2 |
| `get_xbrl_concepts` | 3 |
| `discover_xbrl_concepts` | 2 |
| `get_insider_transactions` | 2 |
| `get_insider_summary` | 3 |
| `get_form4_details` | 3 |
| `analyze_form4_transactions` | 3 |
| `analyze_insider_sentiment` | 3 |
| `get_recommended_tools` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `public-filings` | 1 |
| `public-financials` | 1 |
| `public-insider-transactions` | 1 |
| `company-identifiers` | 2 |
| `concept-catalogs` | 3 |
| `research-query-pattern` | 3 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v5r_nacombo, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | get_cik_by_ticker | get_company_info | search_companies | get_company_facts | get_recent_filings | get_filing_content | analyze_8k | get_filing_sections | get_financials | get_segment_data | get_key_metrics | compare_periods | discover_company_metrics | get_xbrl_concepts | discover_xbrl_concepts | get_insider_transactions | get_insider_summary | get_form4_details | analyze_form4_transactions | analyze_insider_sentiment | get_recommended_tools |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-filings` | N/A | N/A | N/A | N/A | 4 (1×2×2) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `public-financials` | N/A | N/A | N/A | 9 (1×3×3) 🟢 | N/A | N/A | N/A | N/A | 9 (1×3×3) 🟢 | 9 (1×3×3) 🟢 | 4 (1×2×2) 🟢 | 6 (1×2×3) 🟢 | N/A | 9 (1×3×3) 🟢 | 4 (1×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `public-insider-transactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×2×2) 🟢 | 9 (1×3×3) 🟢 | 6 (1×2×3) 🟢 | 9 (1×3×3) 🟢 | 6 (1×2×3) 🟢 | N/A |
| `company-identifiers` | 12 (2×2×3) 🟢 | 8 (2×2×2) 🟢 | 8 (2×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `concept-catalogs` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 12 (3×2×2) 🟢 | N/A | 12 (3×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | 27 (3×3×3) 🟢 |
| `research-query-pattern` | N/A | N/A | 12 (3×2×2) 🟢 | N/A | 12 (3×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 12 (3×2×2) 🟢 | 27 (3×3×3) 🟢 | N/A | 27 (3×3×3) 🟢 | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | get_cik_by_ticker | get_company_info | search_companies | get_company_facts | get_recent_filings | get_filing_content | analyze_8k | get_filing_sections | get_financials | get_segment_data | get_key_metrics | compare_periods | discover_company_metrics | get_xbrl_concepts | discover_xbrl_concepts | get_insider_transactions | get_insider_summary | get_form4_details | analyze_form4_transactions | analyze_insider_sentiment | get_recommended_tools |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-filings` | N/A | N/A | N/A | N/A | 2 | 2 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `public-financials` | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A | 3 | 3 | 2 | 2 | N/A | 3 | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `public-insider-transactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 3 | 2 | 3 | 2 | N/A |
| `company-identifiers` | 2 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `concept-catalogs` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | 2 | N/A | N/A | N/A | N/A | N/A | 3 |
| `research-query-pattern` | N/A | N/A | 2 | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 3 | N/A | 3 | N/A | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `get_cik_by_ticker` | **READ** | 2 (Low) | READ | rules |
| `get_company_info` | **METADATA** | 1 (Low) | METADATA | rules |
| `search_companies` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `get_company_facts` | **READ** | 2 (Low) | READ | rules |
| `get_recent_filings` | **READ** | 2 (Low) | READ | rules |
| `get_filing_content` | **READ** | 2 (Low) | READ | rules |
| `analyze_8k` | **READ** | 2 (Low) | READ | verb-fallback |
| `get_filing_sections` | **READ** | 2 (Low) | READ | rules |
| `get_financials` | **READ** | 2 (Low) | READ | rules |
| `get_segment_data` | **READ** | 2 (Low) | READ | rules |
| `get_key_metrics` | **READ** | 2 (Low) | READ | rules |
| `compare_periods` | **READ** | 2 (Low) | READ | verb-fallback |
| `discover_company_metrics` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `get_xbrl_concepts` | **READ** | 2 (Low) | READ | rules |
| `discover_xbrl_concepts` | **READ** | 2 (Low) | READ | verb-fallback |
| `get_insider_transactions` | **READ** | 2 (Low) | READ | rules |
| `get_insider_summary` | **READ** | 2 (Low) | READ | rules |
| `get_form4_details` | **READ** | 2 (Low) | READ | rules |
| `analyze_form4_transactions` | **READ** | 2 (Low) | READ | verb-fallback |
| `analyze_insider_sentiment` | **READ** | 2 (Low) | READ | verb-fallback |
| `get_recommended_tools` | **READ** | 2 (Low) | READ | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `get_cik_by_ticker` | `ticker` | 2 | — | merely names the target |
| `get_company_info` | `identifier` | 2 | — | merely names the target |
| `search_companies` | `query` | 3 | — | can be used for injection attacks |
| `search_companies` | `limit` | 2 | >= 100 | high values can lead to performance degradation |
| `get_company_facts` | `identifier` | 2 | — | merely names the target |
| `get_recent_filings` | `limit` | 5 | unbounded (no LIMIT) | can cause excessive data retrieval and server load |
| `get_recent_filings` | `days` | 4 | >= 365 | increases data volume and processing time |
| `get_recent_filings` | `form_type` | 3 | — | can broaden scope if wildcard or multiple types are allowed |
| `get_recent_filings` | `identifier` | 2 | — | names the target, low risk |
| `get_filing_content` | `identifier` | 2 | — | merely names the target |
| `get_filing_content` | `accession_number` | 2 | — | specific filing identifier, low risk of amplification |
| `analyze_8k` | `identifier` | 2 | — | merely names the target |
| `analyze_8k` | `accession_number` | 2 | — | identifies specific filing, not inherently risky |
| `get_filing_sections` | `accession_number` | 3 | — | potentially used for specific targeting or enumeration |
| `get_filing_sections` | `identifier` | 2 | — | merely names the target |
| `get_filing_sections` | `form_type` | 2 | — | limits the scope to a specific form type, reducing risk |
| `get_financials` | `statement_type` | 3 | — | could potentially request extensive or sensitive data types |
| `get_financials` | `identifier` | 2 | — | merely names the target |
| `get_segment_data` | `segment_type` | 3 | — | could potentially widen scope if not properly validated |
| `get_segment_data` | `identifier` | 2 | — | merely names the target |
| `get_key_metrics` | `metrics` | 4 | >= 10 metrics requested | can broaden scope through bulk fan-out |
| `get_key_metrics` | `identifier` | 2 | — | merely names the target |
| `compare_periods` | `metric` | 3 | — | could be used to request sensitive or extensive data |
| `compare_periods` | `identifier` | 2 | — | merely names the target |
| `compare_periods` | `start_year` | 1 | — | defines the start of a time range, low risk |
| `compare_periods` | `end_year` | 1 | — | defines the end of a time range, low risk |
| `discover_company_metrics` | `search_term` | 3 | — | can potentially widen scope of data retrieval |
| `discover_company_metrics` | `identifier` | 2 | — | merely names the target |
| `get_xbrl_concepts` | `concepts` | 4 | >= 50 concepts | can specify multiple concepts, increasing query complexity a |
| `get_xbrl_concepts` | `identifier` | 2 | — | merely names the target |
| `get_xbrl_concepts` | `form_type` | 2 | — | limits the scope to a specific form type, moderate risk |
| `get_xbrl_concepts` | `accession_number` | 1 | — | identifies a specific filing, low risk |
| `discover_xbrl_concepts` | `namespace_filter` | 4 | — | can be used to filter results broadly, potentially increasin |
| `discover_xbrl_concepts` | `accession_number` | 3 | — | can be used to target specific filings, potentially overwhel |
| `discover_xbrl_concepts` | `identifier` | 2 | — | merely names the target |
| `discover_xbrl_concepts` | `form_type` | 2 | — | limits the scope to a specific form type |
| `get_insider_transactions` | `limit` | 5 | unbounded (no LIMIT) | can cause excessive data retrieval or server load |
| `get_insider_transactions` | `form_types` | 4 | length >= 10 | can broaden scope with many form types |
| `get_insider_transactions` | `days` | 3 | >= 365 | increases data retrieval breadth over time |
| `get_insider_transactions` | `identifier` | 2 | — | merely names the target |
| `get_insider_summary` | `days` | 3 | >= 365 | can widen scope of data retrieval |
| `get_insider_summary` | `identifier` | 2 | — | merely names the target |
| `get_form4_details` | `identifier` | 2 | — | merely names the target |
| `get_form4_details` | `accession_number` | 2 | — | specific filing identifier, low risk of amplification |
| `analyze_form4_transactions` | `limit` | 4 | unbounded (no LIMIT) | controls the breadth of bulk fan-out, potentially overwhelmi |
| `analyze_form4_transactions` | `days` | 3 | >= 365 | can broaden the scope of data retrieval over time |
| `analyze_form4_transactions` | `identifier` | 2 | — | merely names the target |
| `analyze_insider_sentiment` | `months` | 3 | >= 12 | increases data breadth and computational load |
| `analyze_insider_sentiment` | `identifier` | 2 | — | merely names the target |
| `get_recommended_tools` | `form_type` | 2 | — | limited to specific SEC form types |
