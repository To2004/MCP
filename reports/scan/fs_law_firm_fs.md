# Scan — fs:law_firm_fs

_kind=filesystem · provenance=llm-scan · model_reviewed=True · bands={'low': 11, 'medium': 146, 'high': 139, 'critical': 12}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the filesystem.
- **blast_radius_meaning**: The extent to which a tool can affect files or directories; from reading a single file (narrow touch) to modifying multiple files across different directories (severe action).
- **worked_example**: The 'write_file' tool paired with the 'billing/timesheets/timesheet_2026-05-15.txt' asset is highly severe as it can overwrite sensitive billing information irreversibly.

## Tool impact

| tool | impact |
| --- | --- |
| `read_file` | 1 |
| `read_text_file` | 1 |
| `read_media_file` | 1 |
| `read_multiple_files` | 1 |
| `write_file` | 3 |
| `edit_file` | 3 |
| `create_directory` | 2 |
| `list_directory` | 1 |
| `list_directory_with_sizes` | 1 |
| `directory_tree` | 1 |
| `move_file` | 2 |
| `search_files` | 1 |
| `get_file_info` | 1 |
| `list_allowed_directories` | 1 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `README.md` | 2 |
| `billing/timesheets/timesheet_2026-05-01.txt` | 4 |
| `billing/timesheets/timesheet_2026-05-15.txt` | 4 |
| `cases/CASE-2026-001/contract.txt` | 4 |
| `cases/CASE-2026-001/correspondence.txt` | 4 |
| `cases/CASE-2026-001/signed_agreement.pdf` | 4 |
| `cases/CASE-2026-002/contract.txt` | 4 |
| `cases/CASE-2026-002/correspondence.txt` | 4 |
| `cases/CASE-2026-002/signed_agreement.pdf` | 4 |
| `clients/acme_corp/intake.txt` | 4 |
| `clients/blue_whale_inc/intake.txt` | 4 |
| `templates/nda_template.txt` | 4 |
| `/` | 4 |
| `cases/` | 4 |
| `cases/CASE-2026-001/` | 4 |
| `cases/CASE-2026-002/` | 4 |
| `billing/` | 4 |
| `billing/timesheets/` | 4 |
| `clients/` | 4 |
| `clients/acme_corp/` | 4 |
| `clients/blue_whale_inc/` | 4 |
| `templates/` | 2 |

## Risk matrix (score · band)

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 12 🟡 | 4 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 |
| `billing/timesheets/timesheet_2026-05-01.txt` | 8 🟡 | 8 🟡 | 4 🟡 | 16 🟠 | 36 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 16 🟡 | 16 🟠 | 4 🟡 | 4 🟡 |
| `billing/timesheets/timesheet_2026-05-15.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 36 🟠 | 24 🟠 | 8 🟡 | 16 🟠 | 4 🟡 | 16 🟠 | 16 🟡 | 16 🟠 | 4 🟡 | 4 🟡 |
| `cases/CASE-2026-001/contract.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟡 | 4 🟡 | 4 🟡 |
| `cases/CASE-2026-001/correspondence.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟡 | 4 🟡 | 4 🟡 |
| `cases/CASE-2026-001/signed_agreement.pdf` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟡 | 4 🟡 | 4 🟡 |
| `cases/CASE-2026-002/contract.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟡 | 4 🟡 | 4 🟡 |
| `cases/CASE-2026-002/correspondence.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟡 | 4 🟡 | 4 🟡 |
| `cases/CASE-2026-002/signed_agreement.pdf` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟡 | 4 🟡 | 4 🟡 |
| `clients/acme_corp/intake.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟡 | 4 🟡 | 4 🟡 |
| `clients/blue_whale_inc/intake.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟡 | 4 🟡 | 4 🟡 |
| `templates/nda_template.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟡 | 4 🟡 | 4 🟡 |
| `/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 48 🔴 | 32 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 32 🟠 | 16 🟠 | 16 🟠 | 16 🟠 |
| `cases/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 32 🟠 | 16 🟠 | 16 🟠 | 16 🟠 |
| `cases/CASE-2026-001/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 36 🟠 | 36 🟠 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 24 🟠 | 16 🟠 | 16 🟠 | 16 🟠 |
| `cases/CASE-2026-002/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 36 🟠 | 36 🟠 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 24 🟠 | 16 🟠 | 16 🟠 | 16 🟠 |
| `billing/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 32 🟠 | 16 🟠 | 16 🟠 | 16 🟠 |
| `billing/timesheets/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 32 🟠 | 16 🟠 | 16 🟠 | 16 🟠 |
| `clients/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 32 🟠 | 16 🟠 | 16 🟠 | 16 🟠 |
| `clients/acme_corp/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 24 🟠 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 |
| `clients/blue_whale_inc/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 36 🟠 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 24 🟠 | 16 🟠 | 16 🟠 | 16 🟠 |
| `templates/` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 18 🟡 | 24 🟠 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 12 🟡 | 8 🟡 | 8 🟡 | 8 🟡 |

## Tool atomic operations

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `read_file` | **READ** | 2 (Low) | READ | rules |
| `read_text_file` | **READ** | 2 (Low) | READ | rules |
| `read_media_file` | **READ** | 2 (Low) | READ | rules |
| `read_multiple_files` | **READ** | 2 (Low) | READ | rules |
| `write_file` | **OVERWRITE** | 4 (High) | OVERWRITE, WRITE | rules |
| `edit_file` | **MODIFY** | 3 (Medium) | MODIFY | rules |
| `create_directory` | **CREATE** | 3 (Medium) | CREATE | rules |
| `list_directory` | **LIST** | 1 (Low) | LIST | rules |
| `list_directory_with_sizes` | **LIST** | 1 (Low) | LIST | rules |
| `directory_tree` | **LIST** | 1 (Low) | LIST | rules |
| `move_file` | **MOVE** | 3 (Medium) | MOVE | rules |
| `search_files` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `get_file_info` | **METADATA** | 1 (Low) | METADATA | rules |
| `list_allowed_directories` | **LIST** | 1 (Low) | LIST | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `read_file` | `path` | 4 | — | can target any file on the server |
| `read_file` | `tail` | 2 | >= 10000 | limits output to last N lines, but large values can still be |
| `read_file` | `head` | 2 | >= 10000 | limits output to first N lines, but large values can still b |
| `read_text_file` | `path` | 4 | — | can target any file on the server |
| `read_text_file` | `tail` | 2 | >= 10000 | limits output to last N lines, but large values can still be |
| `read_text_file` | `head` | 2 | >= 10000 | limits output to first N lines, but large values can still b |
| `read_media_file` | `path` | 4 | — | can be used to access sensitive files within allowed directo |
| `read_multiple_files` | `paths` | 5 | >= 100 paths | Allows bulk read of files, potentially overwhelming server r |
| `write_file` | `content` | 5 | — | fully controllable payload can inject malicious code or data |
| `write_file` | `path` | 4 | — | can target critical system files |
| `edit_file` | `edits` | 5 | — | fully controlled payload with potential for bulk changes |
| `edit_file` | `path` | 3 | — | can target sensitive files |
| `edit_file` | `dryRun` | 1 | — | only previews changes, no actual modification |
| `create_directory` | `path` | 3 | — | can be used to create directories in sensitive locations |
| `list_directory` | `path` | 4 | — | can point to sensitive directories |
| `list_directory_with_sizes` | `path` | 4 | — | can point to sensitive directories |
| `list_directory_with_sizes` | `sortBy` | 1 | — | only affects sorting, not scope or action |
| `directory_tree` | `excludePatterns` | 4 | length >= 100 | can be used to exclude large portions of the directory tree, |
| `directory_tree` | `path` | 3 | — | can target sensitive directories |
| `move_file` | `destination` | 4 | — | can overwrite critical system files or directories |
| `move_file` | `source` | 3 | — | can specify arbitrary file paths |
| `search_files` | `pattern` | 4 | — | allows broad file matching via glob patterns |
| `search_files` | `path` | 3 | — | can target sensitive directories |
| `search_files` | `excludePatterns` | 2 | — | limits the scope of search, potentially reducing risk |
| `get_file_info` | `path` | 4 | — | can target any file or directory, potentially sensitive |
