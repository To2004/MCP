# Static scan — yfinance (`yahoo_finance`)

Source: live MITM capture logs/proxy/sessions/finance_yahoo/captured.jsonl

Method: deterministic static analysis (atomic-op taxonomy + input-risk rules), no LLM. 9 tools.

## Severity distribution (by primary atomic op)

| Severity | Tools |
| --- | --- |
| Low | 9 |

## Tools ranked by verb severity

| # | Tool | Primary op | Sev | Top input-risk param | Params |
| --- | --- | --- | --- | --- | --- |
| 1 | `get_historical_stock_prices` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 3 |
| 2 | `get_option_chain` | READ (Low) | 2 | `expiration_date` (r3: magnitude/count — larger value means broader eff) | 3 |
| 3 | `get_recommendations` | READ (Low) | 2 | `recommendation_type` (r3: magnitude/count — larger value means broader eff) | 3 |
| 4 | `get_yahoo_finance_news` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 5 | `get_stock_actions` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 6 | `get_option_expiration_dates` | READ (Low) | 2 | `ticker` (r1: minor / structural parameter) | 1 |
| 7 | `get_financial_statement` | METADATA (Low) | 1 | `ticker` (r1: minor / structural parameter) | 2 |
| 8 | `get_holder_info` | METADATA (Low) | 1 | `ticker` (r1: minor / structural parameter) | 2 |
| 9 | `get_stock_info` | METADATA (Low) | 1 | `ticker` (r1: minor / structural parameter) | 1 |
