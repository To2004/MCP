# Filesystem MCP — Scoring Notes

**Method:** CVSS v3.1
**Generated:** 2026-05-25T08:02:32Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| write_file | Critical | AV:N AC:L PR:L UI:N S:C C:H I:H (on .exe/.sys/.bash/.code) → Critical (≥9.0) |
| edit_file | Critical | AV:N AC:L PR:L UI:N S:C C:H I:H (on executables) → Critical; S:U C:H I:H on others → High |
| move_file | High | AV:N AC:L PR:L UI:N S:C I:H A:L (executable move) → High; S:U I:H A:L otherwise → High |
| read_file | Medium | AV:N AC:L PR:L UI:N S:U C:H I:N (critical dir + high-sensitivity filetype) → Medium (6.5) |
| list_dir | Medium | AV:N AC:L PR:L UI:N S:U C:L I:N (metadata disclosure on critical/high dirs) → Medium (5.3) |
| search | Medium | AV:N AC:L PR:L UI:N S:U C:L I:N (reveals content existence in sensitive dirs) → Medium (5.3) |
| create_dir | Medium | AV:N AC:L PR:L UI:N S:U C:N I:L (staging path creation) → Medium (4.3) |
| get_file_info | Medium | AV:N AC:L PR:L UI:N S:U C:L I:N (stat/metadata in critical dirs) → Medium (5.3) |

## File Types

| File Type | Risk Level | Reasoning |
|---|---|---|
| .sys | Critical | System binaries: write/edit yields S:C, C:H, I:H - full Critical |
| .exe | Critical | Executables: same as .sys, scope change on modification |
| .bash | Critical | Shell scripts: execution side-effects on modification, S:C |
| .code | Critical | Source/compiled: S:C on modification in any sensitive dir |
| .sql | High | DB schema+data: C:H, I:H without scope change |
| .xlsx | High | Structured financials: C:H disclosure risk |
| .docx | High | Contracts/docs: C:H disclosure |
| .pdf | High | High-sensitivity docs: C:H read in critical dirs |
| .csv | High | Structured data: C:H in critical dirs (PII, financials) |
| .md | Medium | Markdown metadata: C:L, I:L - medium disclosure |
| .png | Low | Images: C:L at best, typically no sensitive payload |
| .txt | Medium | Plain text: C:L in sensitive dirs; logs/config risk |

## Folders

| Folder | Risk Level | Reasoning |
|---|---|---|
| Sensitive Docs | Critical | Dir tier=critical → C:H I:H read/write; S:C for write_file on executables → Critical worst-case |
| Security Evidence | Critical | Dir tier=critical → C:H I:H; audit-integrity impact elevates to Critical |
| Source Code | High | Dir tier=high → C:H I:L; write/edit .exe/.code S:C → Critical; read C:H → High |
| Eval Data | High | Dir tier=high → C:H I:L; write_file I:H → High worst-case |
| Shared Poj dir | Medium | Dir tier=medium → C:L I:L; write_file I:H → Medium; no executable scope-change uplift |
| QA Test Plans | Medium | Dir tier=medium → C:L I:L; write_file I:H → Medium worst-case |
| Onboarding | Medium | Dir tier=medium → C:L I:L; write_file I:H → Medium worst-case |
| Public | Low | Dir tier=low → C:N/L I:N; list_dir returns N/A; search/read → Low |
| assumption |  |  |
