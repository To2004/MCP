# SQLite MCP — Scoring Notes

**Method:** OWASP Risk Rating
**Generated:** 2026-05-25T08:02:35Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| list_tables | Critical | L=(7+6+8+9)/4=7.5(High); I=(9-3+9-2)/2=(6,7) High; matrix(H,H) → Critical |
| describe_table | Critical | L=(7+7+8+9)/4=7.75(High); I=(9-2+9-1)/2=(7,8) High; matrix(H,H) → Critical |
| read_query | Critical | L=(7+8+8+9)/4=8.0(High); I=(9+9)/2=9.0 High; matrix(H,H) → Critical |
| write_query | Critical | L=(7+9+7+9)/4=8.0(High); I=(9+1+9+1)/2=9.0 High; matrix(H,H) → Critical |
| create_table | Critical | L=(7+7+7+9)/4=7.5(High); I=(9-1+9)/2=(8,9) High; matrix(H,H) → Critical |
| append_insight | Critical | L=(7+6+7+9)/4=7.25(High); I=(9-1+9)/2=(8,9) High; matrix(H,H) → Critical |

## Data Types

| Data Type | Risk Level | Reasoning |
|---|---|---|
| PII | Critical | SQLITE_IMPACT (9,9) for employees/PII; read_query I=9.0 High; L=8.0 High → Critical |
| Financial | Critical | SQLITE_IMPACT max (9,9) grants/Financial; write_query I cap=9; L=8.0 High → Critical |
| Credentials / API Keys | Critical | SQLITE_IMPACT (9,9) api_keys; write_query I=(9+1)cap=9; L=8.0 High → Critical |
| Restricted Research Data | Critical | experiments (8,8); write_query I=(8+1,8+1)=9 High; L=8.0 High → Critical |
| Public Research Data | High | publications (3,3); write_query I=(3+1,3+1)=(4,4) Med; L=8.0 High → High |
| Org / Role Metadata | Critical | employees Role/Org (7,6); write I=(7+1,6+1)=High; L=7.75 High → Critical |
| Lifecycle / Timestamps | Critical | projects Timeline (5,5); write_query I=(5+1,5+1)=(6,6) High; L=7.25 High → Critical |

## Tables

| Table | Risk Level | Reasoning |
|---|---|---|
| employees | Critical | employees PII (9,9); write I=cap 9; L=8.0 High → Critical |
| projects | Critical | projects max (7,7) ResMetadata; write I=(8,8) High; L=7.75 High → Critical |
| datasets | Critical | datasets max (7,6) InternalData; write I=(8,7) High; L=7.75 High → Critical |
| experiments | Critical | experiments ResResults (8,8); write I=(9,9); L=7.75 High → Critical |
| publications | High | publications PublicOutput (3,3); write I=(4,4) Med; L=7.25 High → High |
| grants | Critical | grants Financial (8,8); write I=(9,9) High; L=8.0 High → Critical |
| api_keys | Critical | api_keys Credentials (9,9); write I=cap 9; L=8.0 High; matrix(H,H) → Critical |
