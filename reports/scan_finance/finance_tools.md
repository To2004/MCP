# Static scan — finance-tools-mcp (`finance_tools`)

Source: live MITM capture logs/proxy/sessions/finance_tools/captured.jsonl

Method: deterministic static analysis (atomic-op taxonomy + input-risk rules), no LLM. 17 tools.

## Severity distribution (by primary atomic op)

| Severity | Tools |
| --- | --- |
| Low | 16 |
| Medium | 1 |

## Tools ranked by verb severity

| # | Tool | Primary op | Sev | Top input-risk param | Params |
| --- | --- | --- | --- | --- | --- |
| 1 | `cnbc_news_feed` | CREATE (Medium) | 3 | — | 0 |
| 2 | `get_price_history` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 4 |
| 3 | `get_ticker_data` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 4 | `get_earnings_history` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 5 | `get_ticker_news_tool` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 6 | `super_option_tool` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 7 | `get_top25_holders` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 8 | `get_insider_trades` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 9 | `get_historical_fng_tool` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 1 |
| 10 | `analyze_fng_trend` | READ (Low) | 2 | `days` (r3: magnitude/count — larger value means broader eff) | 1 |
| 11 | `calculate` | READ (Low) | 2 | `expression` (r5: free-form query/command — unbounded reach; the w) | 1 |
| 12 | `get_fred_series` | READ (Low) | 2 | `series_id` (r2: names the target resource — selects what the op ) | 1 |
| 13 | `search_fred_series` | SEARCH (Low) | 2 | `query` (r5: free-form query/command — unbounded reach; the w) | 1 |
| 14 | `get_overall_sentiment_tool` | READ (Low) | 2 | — | 0 |
| 15 | `get_current_time` | READ (Low) | 2 | — | 0 |
| 16 | `get_financial_statements` | METADATA (Low) | 1 | `ticker` (r1: minor / structural parameter) | 3 |
| 17 | `social_media_feed` | METADATA (Low) | 1 | `keywords` (r4: list/array — risk scales with its length (bulk r) | 1 |
