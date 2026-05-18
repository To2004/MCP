# CVSS v3.1 Scoring Notes for MCP Risk Matrices

CVSS v3.1 base-score methodology applied to three MCP server risk matrices.
Threat model: the MCP server is the protected asset; the AI agent is the attacker.

## Method Adaptation

### Fixed base metrics

All tool calls travel over the MCP protocol, so two base metrics are constant for every cell.

| Metric | Value | Justification |
|--------|-------|---------------|
| Attack Vector (AV) | Network (N) | Every MCP tool is reached via the network transport layer |
| Attack Complexity (AC) | Low (L) | No specialised conditions required; the agent simply issues a tool call |

### Variable base metrics

| Metric | Default | Override conditions |
|--------|---------|---------------------|
| Privileges Required (PR) | Low (L) | Agent holds a valid MCP session token (low privilege) |
| User Interaction (UI) | None (N) | No human approval gate assumed at call time |
| Scope (S) | Unchanged (U) | Changed (C) when one tool call can affect assets beyond the immediate target |
| Confidentiality Impact (C) | Per asset | High for PII, financial, credentials, exec files; Low for metadata; None for public |
| Integrity Impact (I) | Per tool | High for write/overwrite tools; Low for append or list tools; None for read-only |
| Availability Impact (A) | Rarely High | Low when a move or write can disrupt expected file location or DB schema |

### CVSS v3.1 formula applied

The exact CVSS v3.1 base-score formula is used.

```
ISC_base = 1 - (1 - C_impact)(1 - I_impact)(1 - A_impact)

Scope Unchanged: ISC = 6.42 * ISC_base
Scope Changed:   ISC = 7.52*(ISC_base - 0.029) - 3.25*(ISC_base - 0.02)^15

Exploitability = 8.22 * AV * AC * PR * UI

Scope Unchanged: Base = min(ISC + Exploitability, 10)
Scope Changed:   Base = min(1.08 * (ISC + Exploitability), 10)
```

Results are rounded up to one decimal place per the CVSS rounding rule, then
mapped to bands:

| Score | Band |
|-------|------|
| 9.0-10.0 | Critical |
| 7.0-8.9 | High |
| 4.0-6.9 | Medium |
| 0.1-3.9 | Low |
| 0 | N/A |

### Scope Changed (S:C) decisions

Scope is Changed when a single tool call can affect assets or principals beyond the
directly targeted object.

| Scenario | Rationale |
|----------|-----------|
| write_file or edit_file on .exe/.sys/.bash/.code | Modified binary is executed by downstream users; blast radius extends to all consumers |
| move_file on .exe/.sys/.bash/.code | Same downstream execution risk |
| write_query on the api_keys table | Credential modification enables lateral movement to any system using those keys |
| create_table | Schema change is visible to all DB consumers; alters the DB contract |
| slack_post_message | Message is broadcast to all channel members; fabricated content affects multiple principals |
| slack_reply_to_thread | Same reasoning scoped to thread subscribers |

## Key Scoring Decisions

### Filesystem MCP

**Read-only operations score lower than intuition suggests.**
read_file with C:H (sensitive docs) gives CVSS 6.5 = Medium under PR:L/UI:N/S:U.
This is correct CVSS behavior: no integrity/availability impact and no scope change
keeps the score below 7.0. The risk is real but CVSS reflects absence of write impact.

**Executable file types drive Critical ratings.**
Any write or edit operation on .exe, .sys, .bash, or .code files triggers S:C.
With S:C, PR:L becomes 0.68, and C:H + I:H gives a raw score above 9.0 = Critical.

**Directory sensitivity caps file-type impact.**
A .sql file in the Public directory scores lower than the same file in Sensitive Docs
because the directory sensitivity modifies the effective C and I impact levels.

**move_file scores High (8.5), not Critical.**
S:C applies (exec types) but there is no C:H component (move does not read content),
so the score sits at 8.5 = High rather than Critical.

**list_dir, search, create_dir, get_file_info all score Medium.**
These tools produce C:L or I:L at worst; the CVSS exploitability component
(~2.84 for AV:N/AC:L/PR:L/UI:N) pushes them above 4.0 but not past 7.0.

### Slack MCP

**Post and reply tools score High (8.5) via Scope Changed.**
slack_post_message and slack_reply_to_thread get S:C because posted content
reaches all channel subscribers. With I:H and S:C the score is 8.5 = High.

**Read tools score Medium (6.5), not High.**
Even on private Management or HR channels, reading with C:H, I:N, A:N under
PR:L/UI:N/S:U gives exactly 6.5 = Medium. CVSS does not reach High for
read-only operations without scope change or availability impact at this privilege level.

**get_users scores Medium despite bulk PII.**
The bulk-PII concern is real operationally, but CVSS v3.1 base score mechanics
(C:H, I:N, A:N, S:U, PR:L) still yield 6.5. This reflects a known CVSS limitation
for mass-exfiltration scenarios; the Medium label is formula-accurate.

**All channel categories and asset types score High as worst-case.**
Because post_message (High) applies to every channel/asset combination, the
worst-case row in every ranking sheet is High.

### SQLite MCP

**write_query on api_keys is the only Critical cell.**
S:C (credential theft enables lateral movement) combined with C:H (key exposure)
and I:H (key overwrite) produces a score above 9.0.

**read_query scores Medium (6.5) on PII tables.**
Same CVSS mechanics as Slack reads: C:H, I:N, A:N, S:U, PR:L = 6.5.

**create_table scores Medium despite S:C.**
S:C applies (schema change affects all consumers) but C:N, I:L, A:L limits the
impact side. With S:C the PR weight rises to 0.68 and 1.08 multiplier applies,
but the low impact values keep the score around 6.5 = Medium.

**Ranking_DataTypes all show Critical.**
The worst-case per data category is computed across all tools and all tables.
Because write_query on api_keys is Critical, and the api_keys table is present
for every data-category worst-case sweep, all data categories inherit Critical.
This is correct: even a Public-Output row combined with api_keys/write_query
results in a Critical cell.

**Ranking_Tables: api_keys = Critical; all others = High.**
write_query on non-api_keys tables (S:U, I:H, A:L) scores 7.1 = High.
api_keys additionally triggers S:C for a Critical result.

## Notable Cells

| File | Sheet | Location | Score | Note |
|------|-------|----------|-------|------|
| filesystemMCP | mcp_combined_risk | Sensitive Docs / .sys / write_file | Critical | S:C + C:H + I:H |
| filesystemMCP | mcp_combined_risk | Public / .txt / read_file | N/A | No meaningful impact |
| filesystemMCP | Ranking_Tools | write_file | Critical | Worst tool across all assets |
| filesystemMCP | Ranking_Filetypes | .sys, .exe, .bash, .code | Critical | Scope change on modification |
| filesystemMCP | Ranking_Assets | sensitive/financials/budget_2026.xlsx | Critical | Financial PII in critical dir |
| slackMCP | T3_All_Together | Management / Private Messages / post_message | High | S:C, I:H |
| slackMCP | T3_All_Together | Public / Public Messages / get_channel_history | Medium | C:L only; public content |
| slackMCP | T3_All_Together | any / any / add_reaction | Medium | I:L, no C; CVSS 4.3 |
| sqliteMCP | mcp_combined_risk_sqlite | api_keys / Credentials / write_query | Critical | S:C + C:H + I:H |
| sqliteMCP | mcp_combined_risk_sqlite | publications / Public Output / list_tables | Medium | C:L only |
| sqliteMCP | mcp_combined_risk_sqlite | employees / PII / read_query | Medium | C:H I:N S:U = CVSS 6.5 |

## Score Distribution Summary

### Filesystem MCP (mcp_combined_risk sheet, 608 scored cells)

| Band | Count | Pct |
|------|-------|-----|
| Critical | 14 | 2% |
| High | 105 | 17% |
| Medium | 400 | 66% |
| N/A | 89 | 15% |
| Low | 0 | 0% |

Critical cells: write_file and edit_file on executable types (.exe/.sys/.bash/.code)
in high-sensitivity directories. N/A cells: list_dir and get_file_info on Public and
Onboarding directories where all impact dimensions are zero.

### Slack MCP (T3_All_Together sheet, 176 scored cells)

| Band | Count | Pct |
|------|-------|-----|
| High | 42 | 24% |
| Medium | 132 | 75% |
| N/A | 2 | 1% |

High cells: slack_post_message and slack_reply_to_thread in all channel/asset combos.
N/A cells: get_channel_history and get_thread_replies on Public/Public-Channel-Messages
(no C or I impact reading already-public content).

### SQLite MCP (mcp_combined_risk_sqlite, 66 scored cells)

| Band | Count | Pct |
|------|-------|-----|
| Critical | 1 | 2% |
| High | 6 | 9% |
| Medium | 53 | 80% |
| N/A | 6 | 9% |

Critical: write_query on api_keys (S:C + C:H + I:H). High: write_query on other tables.
N/A cells: list_tables on medium-tier data categories (projects/Timeline,
projects/Research Metadata, datasets/Public Data), and list_tables, describe_table,
read_query on publications/Public-Output. All have C:N, I:N, A:N.

## References

- CVSS v3.1 Specification: https://www.first.org/cvss/v3.1/specification-document
- CVSS v3.1 User Guide: https://www.first.org/cvss/user-guide
- NVD CVSS Calculator: https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator
