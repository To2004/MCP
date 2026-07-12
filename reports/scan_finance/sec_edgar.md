# Static scan — sec-edgar-mcp (`sec_edgar`)

Source: live MITM capture logs/proxy/sessions/finance_sec_edgar/captured.jsonl

Method: deterministic static analysis (atomic-op taxonomy + input-risk rules), no LLM. 21 tools.

## Severity distribution (by primary atomic op)

| Severity | Tools |
| --- | --- |
| Low | 21 |

## Tools ranked by verb severity

| # | Tool | Primary op | Sev | Top input-risk param | Params |
| --- | --- | --- | --- | --- | --- |
| 1 | `get_recent_filings` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 4 |
| 2 | `compare_periods` | READ (Low) | 2 | `identifier` (r2: names the target resource — selects what the op ) | 4 |
| 3 | `get_xbrl_concepts` | READ (Low) | 2 | `concepts` (r4: list/array — risk scales with its length (bulk r) | 4 |
| 4 | `discover_xbrl_concepts` | READ (Low) | 2 | `namespace_filter` (r5: free-form query/command — unbounded reach; the w) | 4 |
| 5 | `get_insider_transactions` | READ (Low) | 2 | `form_types` (r4: list/array — risk scales with its length (bulk r) | 4 |
| 6 | `get_filing_sections` | READ (Low) | 2 | `accession_number` (r3: magnitude/count — larger value means broader eff) | 3 |
| 7 | `analyze_form4_transactions` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 3 |
| 8 | `search_companies` | SEARCH (Low) | 2 | `query` (r5: free-form query/command — unbounded reach; the w) | 2 |
| 9 | `get_filing_content` | READ (Low) | 2 | `accession_number` (r3: magnitude/count — larger value means broader eff) | 2 |
| 10 | `analyze_8k` | READ (Low) | 2 | `accession_number` (r3: magnitude/count — larger value means broader eff) | 2 |
| 11 | `get_financials` | READ (Low) | 2 | `identifier` (r2: names the target resource — selects what the op ) | 2 |
| 12 | `get_segment_data` | READ (Low) | 2 | `identifier` (r2: names the target resource — selects what the op ) | 2 |
| 13 | `get_key_metrics` | READ (Low) | 2 | `metrics` (r4: list/array — risk scales with its length (bulk r) | 2 |
| 14 | `get_insider_summary` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 2 |
| 15 | `get_form4_details` | READ (Low) | 2 | `accession_number` (r3: magnitude/count — larger value means broader eff) | 2 |
| 16 | `analyze_insider_sentiment` | READ (Low) | 2 | `identifier` (r2: names the target resource — selects what the op ) | 2 |
| 17 | `get_cik_by_ticker` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 18 | `get_company_facts` | READ (Low) | 2 | `identifier` (r2: names the target resource — selects what the op ) | 1 |
| 19 | `get_recommended_tools` | READ (Low) | 2 | `form_type` (r1: minor / structural parameter) | 1 |
| 20 | `discover_company_metrics` | METADATA (Low) | 1 | `identifier` (r2: names the target resource — selects what the op ) | 2 |
| 21 | `get_company_info` | METADATA (Low) | 1 | `identifier` (r2: names the target resource — selects what the op ) | 1 |
