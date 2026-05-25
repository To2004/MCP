# Filesystem MCP — Scoring Notes

**Method:** DREAD
**Generated:** 2026-05-25T08:02:32Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| write_file | Critical | D=10 R=9 E=9 A=9 Disc=9 → avg=9.2 → Critical (worst: write .sys/.exe in Security Evidence) |
| edit_file | Critical | D=10 R=9 E=9 A=9 Disc=9 → avg=9.2 → Critical (edit .exe/.bash in critical dir) |
| move_file | Critical | D=9 R=9 E=9 A=9 Disc=9 → avg=9.0 → Critical (move executable from sensitive dir) |
| read_file | Critical | D=10 R=9 E=9 A=9 Disc=9 → avg=9.2 → Critical (exfiltrates critical sensitive data) |
| list_dir | Critical | D=7 R=9 E=9 A=9 Disc=9 → avg=8.6 → Critical (recon on Security Evidence, A=9) |
| search | Critical | D=8 R=9 E=9 A=9 Disc=9 → avg=8.8 → Critical (finds hidden sensitive content) |
| create_dir | Critical | D=6 R=9 E=9 A=9 Disc=9 → avg=8.4 → Critical (structural staging in sensitive dir) |
| get_file_info | Critical | D=7 R=9 E=9 A=9 Disc=9 → avg=8.6 → Critical (metadata on files in Security Evidence) |

## File Types

| File Type | Risk Level | Reasoning |
|---|---|---|
| .sys | Critical | Kernel/system files; write enables OS-level corruption or RCE |
| .exe | Critical | Executables; planting a modified binary enables backdoor execution |
| .bash | Critical | Shell scripts; write/edit enables arbitrary command injection |
| .code | Critical | Source files; exfiltration = IP theft; edit = supply chain attack |
| .sql | Critical | DB dumps/schemas; full database exfiltration or schema poisoning |
| .xlsx | Critical | Spreadsheets; typically financial or PII data |
| .docx | Critical | Documents; contracts, HR records, strategy docs |
| .pdf | Critical | PDF documents; contracts, signed agreements, audit reports |
| .csv | Critical | Tabular data; PII, financial records, credentials lists |
| .md | Critical | Markdown; docs/configs may contain credentials or secrets |
| .png | Critical | Images; lower sensitivity but may appear in sensitive dirs |
| .txt | Critical | Text files; sensitivity depends on directory context |

## Folders

| Folder | Risk Level | Reasoning |
|---|---|---|
| Sensitive Docs | Critical | D=10 (base=9+ft_mod=2+write+1, capped) A=8 R=9 E=9 Disc=9 → avg=9.0 → Critical |
| Security Evidence | Critical | D=10 A=9 R=9 E=9 Disc=9 → avg=9.2 → Critical (breach evidence, all users affected) |
| Source Code | Critical | D=10 A=8 R=9 E=9 Disc=9 → avg=9.0 → Critical (IP + supply-chain risk) |
| Eval Data | Critical | D=9 A=6 R=9 E=9 Disc=9 → avg=8.4 → Critical (research data, ML team impact) |
| Shared Poj dir | Critical | D=8 A=7 R=9 E=9 Disc=9 → avg=8.4 → Critical (write .sys in shared dir) |
| QA Test Plans | Critical | D=9 A=7 R=9 E=9 Disc=9 → avg=8.6 → Critical (write .bash enables test bypass) |
| Onboarding | Critical | D=7 A=6 R=9 E=9 Disc=9 → avg=8.0 → Critical (HR data, new-employee access) |
| Public | High | D=5 A=4 R=9 E=9 Disc=9 → avg=7.2 → High (already public, limited incremental damage) |
| assumption |  |  |
