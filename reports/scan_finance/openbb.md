# Static scan — openbb-platform (`openbb`)

Source: live MITM capture logs/proxy/sessions/finance_openbb/captured.jsonl

Method: deterministic static analysis (atomic-op taxonomy + input-risk rules), no LLM. 30 tools.

## Severity distribution (by primary atomic op)

| Severity | Tools |
| --- | --- |
| Low | 27 |
| Medium | 2 |
| High | 1 |

## Tools ranked by verb severity

| # | Tool | Primary op | Sev | Top input-risk param | Params |
| --- | --- | --- | --- | --- | --- |
| 1 | `equity_ownership_share_statistics` | BROADCAST (High) | 4 | `provider` (r2: names the target resource — selects what the op ) | 2 |
| 2 | `news_company` | CREATE (Medium) | 3 | `limit` (r3: magnitude/count — larger value means broader eff) | 5 |
| 3 | `equity_fundamental_management` | MODIFY (Medium) | 3 | `provider` (r2: names the target resource — selects what the op ) | 2 |
| 4 | `equity_screener` | READ (Low) | 2 | `country` (r3: magnitude/count — larger value means broader eff) | 14 |
| 5 | `derivatives_options_surface` | READ (Low) | 2 | `data` (r4: payload content — injection / exfiltration / poi) | 13 |
| 6 | `equity_price_historical` | READ (Low) | 2 | `provider` (r2: names the target resource — selects what the op ) | 8 |
| 7 | `derivatives_futures_historical` | READ (Low) | 2 | `provider` (r2: names the target resource — selects what the op ) | 6 |
| 8 | `crypto_price_historical` | READ (Low) | 2 | `provider` (r2: names the target resource — selects what the op ) | 5 |
| 9 | `equity_fundamental_balance` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 4 |
| 10 | `equity_fundamental_cash` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 4 |
| 11 | `equity_fundamental_dividends` | READ (Low) | 2 | `provider` (r2: names the target resource — selects what the op ) | 4 |
| 12 | `equity_fundamental_income` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 4 |
| 13 | `install_skill` | READ (Low) | 2 | `skill_name` (r2: names the target resource — selects what the op ) | 3 |
| 14 | `derivatives_futures_curve` | READ (Low) | 2 | `provider` (r2: names the target resource — selects what the op ) | 3 |
| 15 | `equity_discovery_gainers` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 3 |
| 16 | `equity_discovery_losers` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 3 |
| 17 | `equity_discovery_active` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 3 |
| 18 | `equity_discovery_undervalued_large_caps` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 3 |
| 19 | `equity_discovery_undervalued_growth` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 3 |
| 20 | `equity_discovery_aggressive_small_caps` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 3 |
| 21 | `equity_discovery_growth_tech` | READ (Low) | 2 | `limit` (r3: magnitude/count — larger value means broader eff) | 3 |
| 22 | `derivatives_options_chains` | READ (Low) | 2 | `provider` (r2: names the target resource — selects what the op ) | 2 |
| 23 | `equity_estimates_consensus` | READ (Low) | 2 | `provider` (r2: names the target resource — selects what the op ) | 2 |
| 24 | `equity_price_quote` | READ (Low) | 2 | `provider` (r2: names the target resource — selects what the op ) | 2 |
| 25 | `get_prompt` | READ (Low) | 2 | `name` (r2: names the target resource — selects what the op ) | 2 |
| 26 | `read_resource` | READ (Low) | 2 | `uri` (r1: minor / structural parameter) | 1 |
| 27 | `equity_fundamental_metrics` | METADATA (Low) | 1 | `provider` (r2: names the target resource — selects what the op ) | 2 |
| 28 | `equity_profile` | METADATA (Low) | 1 | `provider` (r2: names the target resource — selects what the op ) | 2 |
| 29 | `list_prompts` | LIST (Low) | 1 | — | 0 |
| 30 | `list_resources` | LIST (Low) | 1 | — | 0 |
