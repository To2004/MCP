# SQLite MCP — Scoring Notes

**Method:** MAESTRO/ATFAA
**Generated:** 2026-05-25T08:02:33Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| list_tables | Critical | P=3 × I=3(api_keys/employees) × E=3 = 27 → Critical (routine first-step DB exploration) |
| describe_table | Critical | P=3 × I=3 × E=3 = 27 → Critical (routine schema discovery before querying) |
| read_query | Critical | P=3 × I=3 × E=3 = 27 → Critical (agents issue SELECTs constantly; critical tables) |
| write_query | Critical | P=2 × I=3 × E=3 = 18 → Critical (plausible mutation; critical table impact) |
| create_table | High | P=1 × I=3 × E=3 = 9 → High (unlikely DDL; api_keys/employees still I=3) |
| append_insight | Critical | P=2 × I=3 × E=3 = 18 → Critical (plausible agent memo; data-poisoning of notes) |

## Data Types

| Data Type | Risk Level | Reasoning |
|---|---|---|
| PII | Critical | I=3 (GDPR/CCPA risk); P=3(read) × I=3 × E=3 = 27 → Critical |
| Financial | Critical | I=3 (salary, grant amounts); P=3 × I=3 × E=3 = 27 → Critical |
| Credentials / API Keys | Critical | I=3 (immediate compromise); P=3 × I=3 × E=3 = 27 → Critical |
| Restricted Research Data | Critical | I=3 (IP, unpublished results); P=3 × I=3 × E=3 = 27 → Critical |
| Public Research Data | Critical | I=1 (already public); P=3 × I=1 × E=3 = 9 → High worst-case |
| Org / Role Metadata | Critical | I=2; P=3 × I=2 × E=3 = 18 → Critical (org structure enables privilege mapping) |
| Lifecycle / Timestamps | Critical | I=1 (operational metadata); P=3 × I=1 × E=3 = 9 → High worst-case |

## Tables

| Table | Risk Level | Reasoning |
|---|---|---|
| employees | Critical | I=3 (PII + salary + role); P=3 × I=3 × E=3 = 27 → Critical |
| projects | Critical | I=2 (research metadata + timelines); P=3 × I=2 × E=3 = 18 → Critical |
| datasets | Critical | I=2 (public/internal mix); P=3 × I=2 × E=3 = 18 → Critical |
| experiments | Critical | I=2 (research results); P=3 × I=2 × E=3 = 18 → Critical (IP risk) |
| publications | High | I=1 (public academic output); P=3 × I=1 × E=3 = 9 → High |
| grants | Critical | I=3 (financial amounts + identities); P=3 × I=3 × E=3 = 27 → Critical |
| api_keys | Critical | I=3 (credentials); P=3 × I=3 × E=3 = 27 → Critical (most critical table) |
