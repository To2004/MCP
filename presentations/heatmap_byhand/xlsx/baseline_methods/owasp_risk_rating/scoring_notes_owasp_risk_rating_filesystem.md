# Filesystem MCP — Scoring Notes

**Method:** OWASP Risk Rating
**Generated:** 2026-05-25T08:02:34Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| write_file | Critical | L=(7+8+7+9)/4=7.75(High); I=(9+1+9+1)/2=max(9,9)=9.0(High); matrix(H,H) → Critical |
| edit_file | Critical | L=(7+8+7+9)/4=7.75(High); I tech=9+1=9(capped) biz=9+1=9; matrix(H,H) → Critical |
| move_file | Critical | L=(7+7+7+9)/4=7.5(High); I tech=9 biz=9; matrix(H,H) → Critical |
| read_file | Critical | L=(7+7+8+9)/4=7.75(High); I tech=9+0=9 biz=9+0=9; matrix(H,H) → Critical |
| list_dir | Critical | L=(7+6+8+9)/4=7.5(High); I tech=9-1=8 biz=9-0=9; matrix(H,H) → Critical |
| search | Critical | L=(7+7+8+9)/4=7.75(High); I tech=9-2=7 biz=9-0=9; matrix(H,H) → Critical |
| create_dir | High | L=(7+5+8+9)/4=7.25(High); I tech=9-4=5(Med) biz=9-3=6(High); matrix(H,H) → Critical |
| get_file_info | Critical | L=(7+5+8+9)/4=7.25(High); I tech=9-3=6(High) biz=9-2=7(High); matrix(H,H) → Critical |

## File Types

| File Type | Risk Level | Reasoning |
|---|---|---|
| .sys | Critical | System files can expose OS internals; write grants kernel-level impact |
| .exe | Critical | Executables enable code injection; high integrity and availability risk |
| .bash | Critical | Shell scripts enable command injection and privilege escalation |
| .code | Critical | Source code exposes logic, secrets, and attack surface |
| .sql | Critical | SQL files expose schema and data; writes directly corrupt DB |
| .xlsx | Critical | Spreadsheets often hold financial/PII data; GDPR/compliance trigger |
| .docx | Critical | Documents hold contracts and PII; confidentiality risk |
| .pdf | Critical | PDFs include contracts, reports; moderate exfiltration risk |
| .csv | Critical | CSVs hold bulk PII and financial records; mass exfiltration risk |
| .md | Critical | Markdown docs expose process and limited internal info |
| .png | Critical | Images have low inherent sensitivity; metadata may leak context |
| .txt | Critical | Text files vary widely; audit logs in sensitive dirs are high risk |

## Folders

| Folder | Risk Level | Reasoning |
|---|---|---|
| Sensitive Docs | Critical | dir base (tech=9,biz=9); write I=(9+1)cap=9, L=7.75 High → Critical |
| Security Evidence | Critical | dir base (9,9); all tools L≥7.25 High; I≥6.0 High → Critical |
| Source Code | Critical | dir base (8,7); write I=(8+1,7+1) High; L=High → Critical |
| Eval Data | Critical | dir base (7,6); write I=(7+1,6+1) High; L=High → Critical |
| Shared Poj dir | Critical | dir base (7,7); write I=High; L=High → Critical |
| QA Test Plans | Critical | dir base (7,6); write I=High; L=High → Critical |
| Onboarding | Critical | dir base (6,6); write I=(6+1,6+1)=(7,7) High; L=High → Critical |
| Public | High | dir base (3,4); write I=(3+1,4+1)=(4,5) Med; L=High → High |
| assumption |  |  |
