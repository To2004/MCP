# SQLite MCP — Scoring Notes

**Method:** OWASP AIVSS
**Generated:** 2026-05-25T08:02:34Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| list_tables | Medium | scale=0.30 TU×PIS; Credentials 9.5×0.30×1.15×1.10=3.6 → Medium |
| describe_table | Medium | scale=0.40 TU×PIS; Credentials 9.5×0.40×1.15×1.10=4.8 → Medium |
| read_query | Critical | scale=0.95 TU×DA×MSR×PIS; Credentials 9.5×0.95×1.15×1.10×1.10×1.10=14.4→10 → Critical |
| write_query | Critical | scale=1.00 TU×PM×MSR; Credentials 9.5×1.00×1.15×1.10×1.10=13.3→10 → Critical |
| create_table | High | scale=0.60 TU×PM; Credentials 9.5×0.60×1.15×1.10=7.2 → High |
| append_insight | High | scale=0.65 TU×PM×MSR; PII 9.0×0.65×1.15×1.10×1.10=8.1 → High |

## Data Types

| Data Type | Risk Level | Reasoning |
|---|---|---|
| PII | Critical | data_base=9.0; read_query TU×DA×MSR×PIS → Critical |
| Financial | Critical | data_base=8.5; read_query TU×DA×MSR×PIS → Critical |
| Credentials / API Keys | Critical | data_base=9.5; highest base; all amplified tools → Critical |
| Restricted Research Data | High | data_base=5.5; read_query TU×DA×MSR×PIS → High |
| Public Research Data | Medium | data_base=2.5; all tools stay Low-Medium after amplification |
| Org / Role Metadata | Medium | data_base=4.5; write_query TU×PM×MSR=4.5×1.00×1.15×1.10×1.10=6.3 → Medium |
| Lifecycle / Timestamps | Low | data_base=3.0; write_query 3.0×1.00×1.15×1.10×1.10=4.2 → Medium; read 3.0×0.95×…=Low-Med |

## Tables

| Table | Risk Level | Reasoning |
|---|---|---|
| employees | Critical | PII+Financial rows: read_query TU×DA×MSR×PIS on base=9.0/8.5 → Critical |
| projects | Medium | Research Metadata base=4.0; write_query TU×PM×MSR=4.0×1.15×1.10×1.10=5.6 → Medium |
| datasets | High | Internal Data base=5.0; read_query TU×DA×MSR×PIS → High |
| experiments | High | Research Results base=5.5; read_query amplified → High |
| publications | Low | Public Output base=2.0; all tools amplified stay Low after TU → Low |
| grants | Critical | Financial base=8.5; read_query amplified → Critical |
| api_keys | Critical | Credentials base=9.5; highest base; all amplified tools → Critical |
