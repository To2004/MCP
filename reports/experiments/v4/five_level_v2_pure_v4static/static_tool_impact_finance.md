# Static tool impact — finance MCP servers (no LLM)

Tool impact for the five finance servers, computed by
`src/mcp_security/static_scoring/static_impact.py` from each tool's own
declaration only — name, description, parameters, MCP annotation hints.
**No model call.** Catalogs: `reports/scan_finance/tool_lists/`.

Ladder: **1** no effect · **2** metadata · **3** content read · **4** reversible
write · **5** irreversible / open-world.

## Summary

| Server | Tools | t1 | t2 | t3 | t4 | t5 | state-changing |
|---|--:|--:|--:|--:|--:|--:|--:|
| `finance-tools-mcp` | 17 | 1 | 0 | 16 | 0 | 0 | **0** |
| `maverick-mcp` | 119 | 6 | 14 | 87 | 8 | 4 | **12** |
| `openbb-platform` | 30 | 0 | 2 | 28 | 0 | 0 | **0** |
| `sec-edgar-mcp` | 21 | 0 | 0 | 21 | 0 | 0 | **0** |
| `yfinance` | 9 | 0 | 1 | 8 | 0 | 0 | **0** |
| **total** | **196** | 7 | 17 | 160 | 8 | 4 | **12** |

**Headline:** four of the five finance servers are entirely read-only data
surfaces — not one tool above tier 3. Every state-changing capability in the
corpus (8 writes, 4 irreversible) sits in **maverick-mcp**, and each one
touches a portfolio, watchlist, trade journal or signal.

## finance-tools-mcp

17 tools · tier 1: 1 · tier 3: 16

Non-content tools (tier 1–2):

| Tool | Impact | Evidence |
|---|:-:|---|
| `get_current_time` | 1 | tier-3 verbs: get; return-shape marker -> capped at 1 |

## maverick-mcp

119 tools · tier 1: 6 · tier 2: 14 · tier 3: 87 · tier 4: 8 · tier 5: 4

State-changing tools:

| Tool | Impact | Evidence |
|---|:-:|---|
| `watchlist_remove` | **5** | tier-5 verbs: remove |
| `remove_portfolio_position` | **5** | tier-5 verbs: remove |
| `portfolio_remove_position` | **5** | tier-5 verbs: remove |
| `delete_signal` | **5** | tier-5 verbs: delete |
| `watchlist_create` | **4** | tier-4 verbs: create |
| `watchlist_add` | **4** | tier-4 verbs: add |
| `update_signal` | **4** | tier-4 verbs: update |
| `portfolio_add_position` | **4** | tier-4 verbs: add |
| `journal_add_trade` | **4** | tier-4 verbs: add |
| `create_strategy_ensemble` | **4** | tier-4 verbs: create |
| `create_signal` | **4** | tier-4 verbs: create |
| `add_portfolio_position` | **4** | tier-4 verbs: add |

Non-content tools (tier 1–2):

| Tool | Impact | Evidence |
|---|:-:|---|
| `discover_capabilities` | 1 | tier-1 verbs: capabilit(y|ies) |
| `get_health_history` | 1 | tier-3 verbs: get, histor(y|ies); return-shape marker -> capped at 1 |
| `get_system_health` | 1 | tier-3 verbs: get; return-shape marker -> capped at 1 |
| `performance_get_redis_health_status` | 1 | tier-3 verbs: get; return-shape marker -> capped at 1 |
| `performance_get_system_performance_health` | 1 | tier-3 verbs: get, query; return-shape marker -> capped at 1 |
| `run_health_diagnostics` | 1 | tier-1 verbs: health |
| `agents_list_available_agents` | 2 | tier-2 verbs: list; lists non-container items -> content read (3); ret |
| `get_circuit_breaker_status` | 2 | tier-3 verbs: get; return-shape marker -> capped at 2 |
| `get_component_status` | 2 | tier-3 verbs: get; return-shape marker -> capped at 2 |
| `get_mcp_connection_status` | 2 | tier-3 verbs: get; return-shape marker -> capped at 2 |
| `get_portfolio_risk_dashboard` | 2 | tier-3 verbs: get; return-shape marker -> capped at 2 |
| `get_screening_pipeline_status` | 2 | tier-3 verbs: get; return-shape marker -> capped at 2 |
| `get_status_dashboard` | 2 | tier-3 verbs: get; return-shape marker -> capped at 2 |
| `get_tool_registry_status` | 2 | tier-3 verbs: get; return-shape marker -> capped at 2 |
| `performance_analyze_database_index_usage` | 2 | tier-2 verbs: index |
| `performance_get_cache_performance_status` | 2 | tier-3 verbs: get; return-shape marker -> capped at 2 |
| `performance_get_database_performance_status` | 2 | tier-3 verbs: get, query; return-shape marker -> capped at 2 |
| `performance_optimize_cache_configuration` | 2 | tier-2 verbs: sizes? |
| `schedule_screening` | 2 | tier-2 verbs: names? |
| `watchlist_brief` | 2 | tier-2 verbs: counts? |

## openbb-platform

30 tools · tier 2: 2 · tier 3: 28

Non-content tools (tier 1–2):

| Tool | Impact | Evidence |
|---|:-:|---|
| `list_prompts` | 2 | tier-2 verbs: list, metadata, names?; lists non-container items -> con |
| `list_resources` | 2 | tier-2 verbs: list, metadata, names?; lists non-container items -> con |

## sec-edgar-mcp

21 tools · tier 3: 21

Every tool is a tier-3 content read — a pure market/filings data surface.

## yfinance

9 tools · tier 2: 1 · tier 3: 8

Non-content tools (tier 1–2):

| Tool | Impact | Evidence |
|---|:-:|---|
| `get_option_expiration_dates` | 2 | tier-3 verbs: get, fetch; return-shape marker -> capped at 2 |

## Two false positives this corpus exposed (both fixed)

**1. Negated verbs.** `sec-edgar-mcp` scored six read-only tools as tier-4
writes because their descriptions instruct the MODEL — *"ONLY use data returned
from SEC records. **NEVER add** external information"* — and a bare verb match
read "add" as a capability. A **negation guard** now discounts a verb preceded
by never / do not / without / cannot in the same clause. All 21 sec-edgar tools
now score tier 3.

**2. Incidental liveness words.** `get_user_portfolio_summary` scored tier 1
because its description ends *"…and stock analysis **capabilities**"*. Liveness
markers (health, version, capabilities, ping) are now matched **in the tool name
only**; return-shape markers match the name and opening sentence. A tool is a
ping when it is named one, not when it mentions the word.

Both are the same underlying hazard: MCP descriptions are increasingly written
as prompts to an agent rather than as API documentation, so verb matching must
be scoped, not global.

