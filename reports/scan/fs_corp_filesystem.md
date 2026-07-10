# Scan — fs:corp_filesystem

_kind=filesystem · provenance=llm-scan · model_reviewed=True · bands={'low': 46, 'medium': 80, 'high': 79, 'critical': 5}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the filesystem.
- **blast_radius_meaning**: The extent of a tool's impact on assets ranges from reading or listing files (narrow touch) to modifying, moving, or deleting files and directories (severe action).
- **worked_example**: The 'write_file' tool paired with the 'sensitive/security/private_key.pem' asset is highly severe because it can overwrite a critical private key file.

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
| `move_file` | 3 |
| `search_files` | 1 |
| `get_file_info` | 1 |
| `list_allowed_directories` | 1 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `README.md` | 1 |
| `onboarding/org_chart.png` | 2 |
| `projects/db_schema.sql` | 3 |
| `projects/known_defects.csv` | 3 |
| `sensitive/financials/payslips_q1.csv` | 4 |
| `sensitive/security/audit_log.txt` | 4 |
| `sensitive/security/private_key.pem` | 5 |
| `source_code/core.c` | 4 |
| `/` | 5 |
| `sensitive/` | 5 |
| `projects/` | 3 |
| `sensitive/security/` | 5 |
| `onboarding/` | 2 |
| `sensitive/financials/` | 4 |
| `source_code/` | 4 |

## Risk matrix (score · band)

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 6 🟡 | 6 🟡 | 2 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 6 🟡 | 1 🟢 | 1 🟢 | 1 🟢 |
| `onboarding/org_chart.png` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 12 🟡 | 4 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 2 🟢 | 2 🟢 | 2 🟢 |
| `projects/db_schema.sql` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 18 🟠 | 18 🟠 | 6 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 18 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
| `projects/known_defects.csv` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 18 🟠 | 18 🟠 | 6 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 18 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
| `sensitive/financials/payslips_q1.csv` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 |
| `sensitive/security/audit_log.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟡 | 4 🟡 |
| `sensitive/security/private_key.pem` | 5 🟡 | 5 🟡 | 5 🟡 | 5 🟡 | 30 🟠 | 30 🟠 | 10 🟠 | 5 🟡 | 5 🟡 | 5 🟡 | 30 🟠 | 10 🟡 | 5 🟡 | 5 🟡 |
| `source_code/core.c` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 8 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟡 | 4 🟡 |
| `/` | 20 🟠 | 20 🟠 | 20 🟠 | 20 🟠 | 30 🟠 | 30 🟠 | 20 🟠 | 20 🟠 | 20 🟠 | 20 🟠 | 60 🔴 | 20 🟠 | 20 🟠 | 20 🟠 |
| `sensitive/` | 20 🟠 | 20 🟠 | 20 🟠 | 25 🟠 | 30 🟠 | 45 🟠 | 20 🟠 | 25 🟠 | 25 🟠 | 25 🟠 | 60 🔴 | 25 🟠 | 20 🟠 | 10 🟡 |
| `projects/` | 12 🟡 | 12 🟡 | 12 🟡 | 12 🟡 | 18 🟠 | 27 🟠 | 12 🟡 | 12 🟡 | 12 🟡 | 12 🟡 | 36 🟠 | 12 🟡 | 6 🟢 | 12 🟡 |
| `sensitive/security/` | 10 🟡 | 20 🟠 | 20 🟠 | 20 🟠 | 45 🟠 | 45 🟠 | 20 🟠 | 25 🟠 | 25 🟠 | 25 🟠 | 60 🔴 | 25 🟠 | 10 🟡 | 10 🟡 |
| `onboarding/` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 12 🟡 | 12 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 4 🟢 | 8 🟡 |
| `sensitive/financials/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 24 🟠 | 24 🟠 | 16 🟡 | 16 🟠 | 16 🟠 | 20 🟠 | 48 🔴 | 16 🟠 | 8 🟡 | 8 🟡 |
| `source_code/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 24 🟠 | 36 🟠 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 16 🟠 | 8 🟡 | 16 🟠 |

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
| `read_text_file` | `tail` | 2 | >= 10000 | limits output to last N lines, but large values can be resou |
| `read_text_file` | `head` | 2 | >= 10000 | limits output to first N lines, but large values can be reso |
| `read_media_file` | `path` | 4 | — | can be used to access sensitive files within allowed directo |
| `read_multiple_files` | `paths` | 5 | >= 100 paths | Allows bulk read of files, potentially overwhelming server r |
| `write_file` | `content` | 5 | — | fully controllable payload can inject malicious code or data |
| `write_file` | `path` | 4 | — | can target critical system files |
| `edit_file` | `edits` | 5 | — | fully controlled payload with potential for bulk changes |
| `edit_file` | `path` | 3 | — | can target sensitive files |
| `edit_file` | `dryRun` | 1 | — | only previews changes, no actual modification |
| `create_directory` | `path` | 3 | — | can be used to create arbitrary directory paths |
| `list_directory` | `path` | 4 | — | can point to sensitive directories |
| `list_directory_with_sizes` | `path` | 4 | — | Can target any directory, potentially exposing sensitive inf |
| `list_directory_with_sizes` | `sortBy` | 1 | — | Limited to predefined sorting options, no amplification of r |
| `directory_tree` | `excludePatterns` | 4 | length >= 100 | can be used to exclude large portions of the directory tree, |
| `directory_tree` | `path` | 3 | — | can target sensitive directories |
| `move_file` | `destination` | 4 | — | can overwrite critical system files or directories |
| `move_file` | `source` | 3 | — | can specify arbitrary file paths |
| `search_files` | `pattern` | 4 | — | allows broad file matching via glob patterns |
| `search_files` | `path` | 3 | — | can target sensitive directories |
| `search_files` | `excludePatterns` | 2 | — | limits the scope of search, potentially reducing risk |
| `get_file_info` | `path` | 4 | — | can target any file or directory, potentially sensitive |
