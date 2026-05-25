# SQLite MCP — Scoring Notes

**Method:** CVSS v3.1
**Generated:** 2026-05-25T08:02:32Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| list_tables | Medium | AV:N AC:L PR:L UI:N S:U C:L I:N (table-name reconnaissance, limited disclosure) → Medium (5.3) |
| describe_table | Medium | AV:N AC:L PR:L UI:N S:U C:L I:N (schema column-name disclosure) → Medium (5.3) |
| read_query | Medium | AV:N AC:L PR:L UI:N S:U C:H I:N (SELECT on critical tables: PII, credentials, financial) → Medium (6.5) |
| write_query | Critical | AV:N AC:L PR:L UI:N S:C C:H I:H A:L (api_keys table: credential theft + lateral movement) → Critical |
| create_table | Medium | AV:N AC:L PR:L UI:N S:C C:N I:L A:L (schema change visible to all DB consumers) → Medium (6.5) |
| append_insight | Medium | AV:N AC:L PR:L UI:N S:U C:N I:L (append-only note, data-poisoning risk) → Medium (4.3) |

## Data Types

| Data Type | Risk Level | Reasoning |
|---|---|---|
| PII | Critical | PII tier=critical: read_query C:H → Medium (6.5); write_query I:H A:L → High; write on api_keys S:C → Critical |
| Financial | Critical | Financial tier=critical: read_query C:H → Medium; write_query I:H → High; api_keys path → Critical |
| Credentials / API Keys | Critical | Credentials tier=critical + api_keys table S:C on write_query: C:H I:H A:L → Critical |
| Restricted Research Data | Critical | Tier=high: read_query C:H → Medium (6.5); write_query I:H → High; api_keys write dominates → Critical |
| Public Research Data | Critical | Tier=low; write_query on api_keys S:C C:H I:H still applies → Critical worst-case |
| Org / Role Metadata | Critical | Tier=medium/high; worst-case write on api_keys S:C → Critical regardless of data cat row |
| Lifecycle / Timestamps | Critical | Tier=low; api_keys write_query S:C dominates → Critical worst-case across all rows |

## Tables

| Table | Risk Level | Reasoning |
|---|---|---|
| employees | High | PII table tier=critical: write_query S:U I:H A:L → High (7.1); read_query C:H → Medium |
| projects | High | Metadata tier=medium: write_query I:L A:L → Medium; read_query C:L → Medium |
| datasets | High | Mixed tier=medium: write_query I:L → Medium; read_query C:L → Medium |
| experiments | High | Research tier=high: write_query I:H A:L → High; read_query C:H → Medium |
| publications | High | Public tier=low: write_query I:N→L → Medium; read_query C:N → Low/Medium |
| grants | High | Financial tier=high: write_query I:H A:L → High; read_query C:H → Medium (6.5) |
| api_keys | Critical | write_query: S:C C:H I:H A:L (credential modification enables lateral movement) → Critical |
