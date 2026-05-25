# SQLite MCP — Scoring Notes

**Variant:** ChatGPT (gpt-4o) — security analyst, NIST SP 800-30 + OWASP LLM Top 10
**Generated:** 2026-05-25 07:24 UTC

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| list_tables | Medium | Reveals database structure which can aid in further attacks. |
| describe_table | Medium | Provides schema details that can be exploited. |
| read_query | Critical | Can access sensitive data stored in the database. |
| write_query | Critical | Can modify or delete critical data. |
| create_table | High | Can be used to introduce unauthorized data structures. |
| append_insight | High | Can add unauthorized data insights, affecting data integrity. |

## Data Types

| Data Type | Risk Level | Reasoning |
|---|---|---|
| PII | Critical | Exposure can lead to identity theft and privacy violations. |
| Financial | Critical | Contains sensitive financial information. |
| Credentials / API Keys | Critical | Exposure can lead to unauthorized access. |
| Restricted Research Data | High | Contains proprietary research information. |
| Public Research Data | Medium | Generally less sensitive but still valuable. |
| Org / Role Metadata | Medium | Contains organizational structure information. |
| Lifecycle / Timestamps | Low | Generally less sensitive, used for tracking. |

## Tables

| Table | Risk Level | Reasoning |
|---|---|---|
| employees | Critical | Contains sensitive employee information. |
| projects | High | Contains project details that may be confidential. |
| datasets | High | Contains data that could be sensitive or proprietary. |
| experiments | High | Contains experimental data that may be proprietary. |
| publications | Medium | Contains information intended for publication. |
| grants | Medium | Contains financial and project information. |
| api_keys | Critical | Contains keys that can be used for unauthorized access. |
