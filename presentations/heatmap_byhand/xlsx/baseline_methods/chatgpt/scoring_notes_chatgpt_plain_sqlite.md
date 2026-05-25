# SQLite MCP — Scoring Notes

**Variant:** ChatGPT (gpt-4o) — plain, no system prompt
**Generated:** 2026-05-25 07:24 UTC

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| list_tables | Medium | Listing tables can reveal database structure. |
| describe_table | Medium | Describing tables can expose schema details. |
| read_query | High | Reading queries can access sensitive data. |
| write_query | Critical | Writing queries can alter or delete critical data. |
| create_table | Medium | Creating tables can lead to unauthorized data storage. |
| append_insight | High | Appending insights can introduce incorrect data. |

## Data Types

| Data Type | Risk Level | Reasoning |
|---|---|---|
| PII | Critical | PII exposure can lead to identity theft and privacy issues. |
| Financial | Critical | Financial data is highly sensitive and valuable. |
| Credentials / API Keys | Critical | Credentials can be used to gain unauthorized access. |
| Restricted Research Data | High | Restricted data may contain proprietary research. |
| Public Research Data | Medium | Public data is less sensitive but still valuable. |
| Org / Role Metadata | Medium | Metadata can reveal organizational insights. |
| Lifecycle / Timestamps | Low | Timestamps generally have low sensitivity. |

## Tables

| Table | Risk Level | Reasoning |
|---|---|---|
| employees | Critical | Employee table contains sensitive personal information. |
| projects | High | Project data may include proprietary information. |
| datasets | High | Datasets can contain sensitive research data. |
| experiments | High | Experiment data may include confidential research results. |
| publications | Medium | Publications are generally less sensitive but valuable. |
| grants | Medium | Grant information can reveal funding sources and amounts. |
| api_keys | Critical | API keys can be used to access systems without authorization. |
