# Filesystem MCP — Scoring Notes

**Method:** MAESTRO/ATFAA
**Generated:** 2026-05-25T08:02:33Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| write_file | Critical | P=2 × I=3(max,critical dir+exec ft) × E=3 = 18 → Critical |
| edit_file | Critical | P=2 × I=3 × E=3 = 18 → Critical (critical dir or exec filetype) |
| move_file | High | P=1 × I=3 × E=3 = 9 → High (unlikely invocation, but high impact) |
| read_file | Critical | P=3 × I=3 × E=3 = 27 → Critical (routine; reads critical-dir sensitive data) |
| list_dir | Critical | P=3 × I=3 × E=3 = 27 → Critical (routine enumeration of sensitive directories) |
| search | Critical | P=3 × I=3 × E=3 = 27 → Critical (routine content search in critical dirs) |
| create_dir | High | P=1 × I=3 × E=3 = 9 → High (unlikely but critical-dir staging risk) |
| get_file_info | Critical | P=2 × I=3 × E=3 = 18 → Critical (plausible metadata check on critical files) |

## File Types

| File Type | Risk Level | Reasoning |
|---|---|---|
| .sys | Critical | Exec filetype: raises I by +1 (cap 3); P=3(read) × I=3 × E=3 = 27 → Critical |
| .exe | Critical | Exec filetype: I+1 → I=3 in high/critical dirs; P=3 × I=3 × E=3 = 27 → Critical |
| .bash | Critical | Exec filetype: I+1 → I=3; read/write/search in any sensitive dir → Critical |
| .code | Critical | Exec filetype: I+1 → I=3; IP theft + supply-chain attack surface → Critical |
| .sql | Critical | Exec filetype: I+1; DB schema/data exfiltration → Critical worst-case |
| .xlsx | Critical | I unchanged (non-exec); Sensitive Docs I=3; read P=3 × I=3 × E=3 = 27 → Critical |
| .docx | Critical | I unchanged; Sensitive Docs I=3; read P=3 × I=3 × E=3 = 27 → Critical |
| .pdf | Critical | I unchanged; Sensitive Docs I=3; read P=3 × I=3 = 27 → Critical |
| .csv | Critical | I unchanged; Sensitive Docs I=3; read P=3 × I=3 = 27 → Critical |
| .md | Critical | I unchanged; Source Code I=3; read P=3 × I=3 = 27 → Critical |
| .png | Critical | I unchanged; all dirs: max I=3 (Sensitive Docs); read P=3 × I=3 = 27 → Critical |
| .txt | Critical | I unchanged; Security Evidence I=3; read P=3 × I=3 = 27 → Critical |

## Folders

| Folder | Risk Level | Reasoning |
|---|---|---|
| Sensitive Docs | Critical | I=3 (PII/contracts/financials); write P=2 → R=18 Critical; read P=3 → R=27 Critical |
| Security Evidence | Critical | I=3 (audit integrity); read P=3 → R=27 Critical; write P=2 → R=18 Critical |
| Source Code | Critical | I=3 (IP/supply-chain); exec filetypes raise I to 3; read P=3 → R=27 Critical |
| Eval Data | Critical | I=2 (research data); exec ft raises I to 3; read P=3 × I=3 × E=3 = 27 → Critical |
| Shared Poj dir | Critical | I=2; exec ft raises I to 3; read P=3 × I=3 = 27 → Critical worst-case |
| QA Test Plans | Critical | I=2; exec ft raises I to 3; read P=3 × I=3 = 27 → Critical worst-case |
| Onboarding | Critical | I=2; exec ft raises I to 3; read P=3 × I=3 = 27 → Critical worst-case |
| Public | Critical | I=1; exec ft raises I to min(1+1,3)=2; write P=2 × I=2 × E=3 = 12 → High |
| assumption |  |  |
