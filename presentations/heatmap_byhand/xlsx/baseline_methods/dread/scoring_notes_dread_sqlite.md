# SQLite MCP — Scoring Notes

**Method:** DREAD
**Generated:** 2026-05-25T08:02:33Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| list_tables | Critical | D=10-4=6 A=9 R=9 E=9 Disc=9 → avg=8.4 → Critical (table enumeration, api_keys visible) |
| describe_table | Critical | D=10-3=7 A=9 R=9 E=9 Disc=9 → avg=8.6 → Critical (schema recon on api_keys) |
| read_query | Critical | D=10+0=10 A=9 R=9 E=9 Disc=9 → avg=9.2 → Critical (api_keys read=catastrophic) |
| write_query | Critical | D=min(10+1,10)=10 A=9(api_keys) R=9 E=9 Disc=9 → avg=9.2 → Critical |
| create_table | Critical | D=10+0=10 A=9 R=9 E=9 Disc=9 → avg=9.2 → Critical (api_keys create_table path) |
| append_insight | Critical | D=min(10,5)=5 A=9 R=9 E=9 Disc=9 → avg=8.2 → Critical (capped by append_insight rule) |

## Data Types

| Data Type | Risk Level | Reasoning |
|---|---|---|
| PII | Critical | D=9 A=8(conservative org-wide) R=9 E=9 Disc=9 → avg=8.8 → Critical |
| Financial | Critical | D=9 A=8 R=9 E=9 Disc=9 → avg=8.8 → Critical (salary, grant amounts, compliance) |
| Credentials / API Keys | Critical | D=10 A=8 R=9 E=9 Disc=9 → avg=9.0 → Critical (immediate full-system compromise) |
| Restricted Research Data | Critical | D=7 A=8 R=9 E=9 Disc=9 → avg=8.4 → Critical (IP, unpublished results) |
| Public Research Data | High | D=3 A=8 R=9 E=9 Disc=9 → avg=7.6 → High (public output, limited incremental harm) |
| Org / Role Metadata | Critical | D=5 A=8 R=9 E=9 Disc=9 → avg=8.0 → Critical (org structure reconnaissance) |
| Lifecycle / Timestamps | High | D=4 A=8 R=9 E=9 Disc=9 → avg=7.8 → High (operational metadata, limited harm) |

## Tables

| Table | Risk Level | Reasoning |
|---|---|---|
| employees | Critical | D=9 A=9 R=9 E=9 Disc=9 → avg=9.0 → Critical (PII + salary for all employees) |
| projects | Critical | D=6 A=7 R=9 E=9 Disc=9 → avg=8.0 → Critical (project metadata + timelines) |
| datasets | Critical | D=6 A=7 R=9 E=9 Disc=9 → avg=8.0 → Critical (mixed public/internal; research team) |
| experiments | High | D=6 A=6 R=9 E=9 Disc=9 → avg=7.8 → High (research results; IP exposure) |
| publications | High | D=3 A=5 R=9 E=9 Disc=9 → avg=7.0 → High (public academic output, minimal extra harm) |
| grants | Critical | D=8 A=8 R=9 E=9 Disc=9 → avg=8.8 → Critical (financial data; fiduciary/compliance impact) |
| api_keys | Critical | D=10 A=9 R=9 E=9 Disc=9 → avg=9.2 → Critical (credential exfiltration = maximum damage) |
