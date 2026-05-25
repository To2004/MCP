# SQLite MCP — Scoring Notes

**Method:** NIST SP 800-60
**Generated:** 2026-05-25T08:02:34Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| list_tables | Critical | Role=C; api_keys C=High I=High → band(High,[High,High]) = Critical |
| describe_table | Critical | Role=C; api_keys C=High I=High → Critical; employees C=High I=Mod → High |
| read_query | Critical | Role=C; api_keys C=High, grants C=High I=High → Critical |
| write_query | Critical | Role=I; api_keys I=High C=High → Critical; grants I=High C=High → Critical |
| create_table | Critical | Role=A; api_keys A=High → band(High,[High,High]) = Critical |
| append_insight | Critical | Role=CI (hybrid); api_keys C=I=High → Critical worst-case |

## Data Types

| Data Type | Risk Level | Reasoning |
|---|---|---|
| PII | High | CIA=(High,Mod,Low); read C=High → High; write I=Mod → Medium; api_keys → Critical |
| Financial | Critical | CIA=(High,High,Low); read C=High, I=High → Critical; write I=High → Critical |
| Credentials / API Keys | Critical | CIA=(High,High,High); all dims High → Critical for all tools |
| Restricted Research Data | Medium | CIA=(Mod,Mod,Low); read C=Mod → Medium; write I=Mod → Medium |
| Public Research Data | Low | CIA=(Low,Low,Low); all tools → Low |
| Org / Role Metadata | Medium | CIA=(Mod,Low,Low); read C=Mod → Medium; write I=Low → Low |
| Lifecycle / Timestamps | Medium | CIA=(Low,Mod,Low); write I=Mod → Medium; read C=Low → Low |

## Tables

| Table | Risk Level | Reasoning |
|---|---|---|
| employees | Critical | Max CIA=(High,High,Low) from Financial row; read C=High I=High → Critical |
| projects | Medium | Max CIA=(Mod,Mod,Low); read → Medium; create_table A=Low → Low |
| datasets | Medium | Max CIA=(Mod,Mod,Low); read → Medium; write → Medium |
| experiments | Medium | CIA=(Mod,Mod,Low); read C=Mod → Medium; write I=Mod → Medium; worst=Medium |
| publications | Low | CIA=(Low,Low,Low); all tools → Low |
| grants | Critical | CIA=(High,High,Low); read C=High, I=High → Critical; write I=High → Critical |
| api_keys | Critical | Table CIA=(High,High,High); all dims High → Critical for all tools |
