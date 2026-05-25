# Filesystem MCP — Scoring Notes

**Method:** OWASP AIVSS
**Generated:** 2026-05-25T08:02:34Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| write_file | Critical | TU(1.15)×PM(1.10)×MSR(1.10): scale=1.05; Sensitive Docs base=9.0×1.05×1.15×1.10×1.10=12.8→10 → Critical |
| edit_file | High | TU(1.15)×PM(1.10)×MSR(1.10): scale=0.95; Sensitive Docs 9.0×0.95×1.15×1.10×1.10=11.5→10 → Critical |
| move_file | High | TU(1.15)×PM(1.10)×MSR(1.10): scale=0.90; Sensitive Docs 9.0×0.90×1.15×1.10×1.10=10.9→10 → Critical |
| read_file | Critical | TU(1.15)×DA(1.10 if sensitive)×PIS(1.10): scale=1.00; Sensitive Docs 9.0×1.00×1.15×1.10×1.10=12.2→10 → Critical |
| list_dir | Medium | TU(1.15)×PIS(1.10): scale=0.65; Sensitive Docs 9.0×0.65×1.15×1.10=7.4 → High |
| search | High | TU(1.15)×DA(1.10)×PIS(1.10): scale=0.70; Sensitive Docs 9.0×0.70×1.15×1.10×1.10=8.9 → High |
| create_dir | Medium | TU(1.15)×PM(1.10): scale=0.45; Sensitive Docs 9.0×0.45×1.15×1.10=5.1 → Medium |
| get_file_info | Low | TU(1.15) only: scale=0.40; Sensitive Docs 9.0×0.40×1.15=4.1 → Medium; Low base dirs → Low |

## File Types

| File Type | Risk Level | Reasoning |
|---|---|---|
| .sys | Critical | Kernel/OS-level files. AIVSS TU+DA+PM amplifiers push Critical. |
| .exe | Critical | Executable binary; write-injection = malware. TU+PM+MSR = Critical. |
| .bash | Critical | Shell script; execution risk. AIVSS lifts High base to Critical. |
| .code | High | Source may embed secrets; read-write chain MSR inflates to High. |
| .sql | High | Schema and data exposure; write_query+MSR amplify to High. |
| .xlsx | High | Financial/structured data; macro-enabled variants add PIS surface. |
| .docx | High | Macro/embedded-link risk; PIS from embedded content applies. |
| .pdf | Medium | PIS from embedded content; read exposes confidential docs. |
| .csv | Medium | Tabular data; DA applies for PII/financial contexts. |
| .md | Low | Minimal execution model; PIS possible via embedded links. |
| .png | Low | Parser exploits rare; limited AARF amplification. |
| .txt | Low | No execution model, no parser complexity. |

## Folders

| Folder | Risk Level | Reasoning |
|---|---|---|
| Sensitive Docs | Critical | folder_base=9.0; write_file TU×PM×MSR → 10 → Critical |
| Security Evidence | Critical | folder_base=9.0; write_file TU×PM×MSR → Critical; read TU×DA×PIS → Critical |
| Source Code | High | folder_base=6.5; write_file 6.5×1.05×TU×PM×MSR=9.6→10 → Critical |
| Eval Data | High | folder_base=6.0; write_file 6.0×1.05×TU×PM×MSR=8.8 → High; read+DA+PIS → High |
| Shared Poj dir | High | folder_base=5.0; write_file 5.0×1.05×TU×PM×MSR=7.3 → High worst-case |
| QA Test Plans | High | folder_base=5.5; write_file 5.5×1.05×TU×PM×MSR=8.0 → High |
| Onboarding | Medium | folder_base=4.0; write_file 4.0×1.05×TU×PM×MSR=5.8 → Medium |
| Public | Medium | folder_base=2.5; write_file 2.5×1.05×TU×PM×MSR=3.7 → Medium |
| assumption | will be given by organization |  |
