# Filesystem MCP — Scoring Notes

**Method:** NIST SP 800-60
**Generated:** 2026-05-25T08:02:34Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| write_file | Critical | Role=I; Security Evidence I=High, C=High → band(High,[High,Mod]) = Critical |
| edit_file | Critical | Role=I; Source Code I=High (post .bash/.exe modifier); C=High → Critical |
| move_file | Critical | Role=A; Security Evidence A=Moderate; Source Code A=Low; worst → Medium |
| read_file | Critical | Role=C; Sensitive Docs C=High, I=Mod → band(High,[Mod,Low]) = High |
| list_dir | Critical | Role=C; Sensitive Docs C=High → High; Security Evidence C=High → High |
| search | Critical | Role=CI (hybrid); C=High wins; I=High in Security Evidence → Critical |
| create_dir | Critical | Role=A; A=Moderate in Security Evidence → Medium |
| get_file_info | Critical | Role=C; Sensitive Docs C=High → High; lower dirs → Medium or Low |

## File Types

| File Type | Risk Level | Reasoning |
|---|---|---|
| .sys | Critical | Executable modifier raises I+A to High; present in high-C dirs -> Critical |
| .exe | Critical | Executable modifier raises I+A to High; Source Code dir C=High -> Critical |
| .bash | Critical | Script-injection modifier raises I to High; Source Code dir C=High -> Critical |
| .code | Critical | Script-injection modifier raises I to High; Source Code dir C=High -> Critical |
| .sql | Critical | DB-context modifier raises I to High in Sensitive/Source dirs; C=High -> Critical |
| .xlsx | Critical | Sensitive Docs: C=High, I=Mod; write/edit tool on I=Mod -> Medium; read C=High -> High |
| .docx | Critical | Sensitive Docs: C=High, I=Mod; read -> High; write -> Medium |
| .pdf | Critical | Security Evidence: C=High, I=High; read -> High; write -> Critical |
| .csv | Critical | Sensitive Docs: C=High; read -> High; write -> Medium |
| .md | Critical | Source Code dir: C=High, I=High; read -> High; write -> Critical |
| .png | Critical | All dirs have Low I; Security Evidence C=High -> High on read; otherwise Medium or Low |
| .txt | Critical | Security Evidence: C=High I=High -> Critical write; Sensitive Docs C=High -> High read |

## Folders

| Folder | Risk Level | Reasoning |
|---|---|---|
| Sensitive Docs | High | CIA=(High,Mod,Low); write(I=Mod→High via filetype): Critical; read C=High → High |
| Security Evidence | Critical | CIA=(High,High,Mod); write I=High + C=High → Critical; read C=High → Critical |
| Source Code | Critical | CIA=(High,High,Low); write I=High, C=High → Critical; read C=High → Critical |
| Eval Data | Medium | CIA=(Mod,Mod,Low); write I=Mod → Medium; read C=Mod → Medium |
| Shared Poj dir | Medium | CIA=(Mod,Low,Low); write I=Low → Low; read C=Mod → Medium |
| QA Test Plans | Medium | CIA=(Mod,Mod,Low); write I=Mod → Medium; read C=Mod → Medium |
| Onboarding | Low | CIA=(Low,Low,Low); write I=Low → Low; read C=Low → Low |
| Public | Low | CIA=(Low,Low,Low); all tools → Low |
| assumption | Low |  |
