# Filesystem MCP — Scoring Notes

**Method:** NIST SP 800-30
**Generated:** 2026-05-25T08:02:33Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| write_file | Critical | Likelihood=High; Impact=Critical (Sensitive Docs or exec filetype); max → Critical |
| edit_file | Critical | Likelihood=High; Impact=Critical (exec filetype or critical dir); max → Critical |
| move_file | Critical | Likelihood=Medium; Impact=Critical (exec filetype in critical dir); max → Critical |
| read_file | Critical | Likelihood=High; Impact=Critical (Sensitive Docs or .sql/.exe); max → Critical |
| list_dir | High | Likelihood=High; Impact=High (worst dir=High + tool=High); max → High |
| search | High | Likelihood=High; Impact=High (content-exists disclosure in high dirs); max → High |
| create_dir | High | Likelihood=Medium; Impact=High (structural change in High-impact dir); max → High |
| get_file_info | High | Likelihood=High; Impact=Medium (stat metadata only); max → High |

## File Types

| File Type | Risk Level | Reasoning |
|---|---|---|
| .sys | Critical | Kernel/driver files; write or read enables system-level compromise. |
| .exe | Critical | Executable binaries; read reveals functionality; write enables code injection. |
| .bash | Critical | Shell scripts; read exposes automation secrets; write enables arbitrary execution. |
| .code | Critical | Source files; read leaks IP and logic; write plants backdoors silently. |
| .sql | Critical | Database schemas/dumps; read discloses all structured data; write corrupts DB. |
| .xlsx | High | Spreadsheets hold financial or PII data; easily machine-parsed at scale. |
| .docx | High | Office documents often hold contracts, strategies, or sensitive PII. |
| .pdf | High | Reports and contracts carry high confidentiality value. |
| .csv | High | Tabular data; often contains PII or financial records. |
| .md | High | Documentation may expose architecture, credential hints, or internal processes. |
| .png | Medium | Images have low standalone risk; may contain scanned PII documents. |
| .txt | Medium | Plain text is variable; may hold logs, config snippets, or credential hints. |

## Folders

| Folder | Risk Level | Reasoning |
|---|---|---|
| Sensitive Docs | Critical | Dir sensitivity=Critical; read_file Likelihood=High → max(High,Critical) = Critical |
| Security Evidence | Critical | Dir sensitivity=Critical; all read/write tools Likelihood=High → Critical |
| Source Code | Critical | Dir sensitivity=High; exec filetypes raise Impact to Critical; write Likelihood=High → Critical |
| Eval Data | High | Dir sensitivity=Medium; write Likelihood=High; max(High,Medium) = High |
| Shared Poj dir | High | Dir sensitivity=High; write Likelihood=High; max(High,High) = High |
| QA Test Plans | High | Dir sensitivity=High; write Likelihood=High → High; exec ft → Critical |
| Onboarding | Medium | Dir sensitivity=Medium; write Likelihood=High; max(High,Medium) = High |
| Public | Low | Dir sensitivity=Low; write Likelihood=High; max(High,Low) = High |
| assumption | Medium |  |
