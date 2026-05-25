# SQLite MCP — Scoring Notes

**Method:** NIST SP 800-30
**Generated:** 2026-05-25T08:02:33Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| list_tables | Critical | Likelihood=High; Impact=Critical (api_keys/employees worst-case); max → Critical |
| describe_table | Critical | Likelihood=High; Impact=Critical (schema reveals sensitive structure); max → Critical |
| read_query | Critical | Likelihood=High; Impact=Critical (SELECT from PII/credentials/financial); max → Critical |
| write_query | Critical | Likelihood=High; Impact=Critical (INSERT/UPDATE/DELETE on critical tables); max → Critical |
| create_table | High | Likelihood=Medium; Impact=High (schema change in High-impact DB); max → High |
| append_insight | High | Likelihood=Low; Impact=High (append to notes; data-poisoning risk); max → High |

## Data Types

| Data Type | Risk Level | Reasoning |
|---|---|---|
| PII | Critical | Data Impact=Critical; read_query Likelihood=High → Critical |
| Financial | Critical | Data Impact=Critical; write_query Likelihood=High → Critical |
| Credentials / API Keys | Critical | Data Impact=Critical; any High-likelihood tool → Critical |
| Restricted Research Data | High | Data Impact=High; read_query Likelihood=High → High |
| Public Research Data | Medium | Data Impact=Medium; Likelihood=High → High (max rule) |
| Org / Role Metadata | High | Data Impact=High; Likelihood=High → High |
| Lifecycle / Timestamps | Low | Data Impact=Low; Likelihood=Low(append_insight) → Low worst-case |

## Tables

| Table | Risk Level | Reasoning |
|---|---|---|
| employees | Critical | Table Impact=Critical (PII+salary); read/write Likelihood=High → Critical |
| projects | High | Table Impact=High (research metadata+timelines); Likelihood=High → High |
| datasets | High | Table Impact=High (internal data); Likelihood=High → High |
| experiments | High | Table Impact=High (research results); Likelihood=High → High |
| publications | Medium | Table Impact=Medium (public output); read Likelihood=High → High (max rule) |
| grants | Critical | Table Impact=Critical (financial); read/write Likelihood=High → Critical |
| api_keys | Critical | Table Impact=Critical (credentials); read/write Likelihood=High → Critical |
