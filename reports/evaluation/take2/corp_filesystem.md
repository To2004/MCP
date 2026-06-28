# Evaluation ground truth — corp_filesystem

> Design-time reviewed risk table. **Used only to grade the scanner's output; the scanner never reads this file.**

## Server

| Field | Value |
| --- | --- |
| name | corp_filesystem |
| server | secure-filesystem-server |
| mcp_kind | filesystem |
| version | static-take2-2026-06-23 |
| model_reviewed | True |
| formula | `asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact` |
| band_distribution | {'low': 78, 'medium': 21, 'high': 11, 'critical': 2} |
| judge_ran | True |
| judge_overrides | 16 |

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the server's allowed directories.
- **blast_radius_meaning**: The extent to which a tool can affect files or directories; from reading a single file (narrow touch) to modifying multiple files across different directories (severe action).
- **worked_example**: The 'write_file' tool paired with the 'sensitive/security/private_key.pem' asset is highly severe because it can overwrite a critical private key file.
- **dangerous_classes**: holds secrets, is executable
- **irreversible_actions**: deletes, overwrites existing files, executes code

### Tool impact (1 read · 2 recoverable · 3 destructive)

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

### Asset sensitivity (1 low – 5 crown-jewel)

| asset | sensitivity |
| --- | --- |
| `README.md` | 1 |
| `onboarding/org_chart.png` | 2 |
| `projects/db_schema.sql` | 4 |
| `projects/known_defects.csv` | 3 |
| `sensitive/financials/payslips_q1.csv` | 4 |
| `sensitive/security/audit_log.txt` | 4 |
| `sensitive/security/private_key.pem` | 5 |
| `source_code/core.c` | 3 |

## Risk matrix (score · band)

Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 6 🟢 | 6 🟢 | 0 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 4 🟢 | 1 🟢 | 1 🟢 | 1 🟢 |
| `onboarding/org_chart.png` | 2 🟢 | 0 🟢 | 2 🟢 | 2 🟢 | 18 🟡 | 0 🟢 | 0 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 |
| `projects/db_schema.sql` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 36 🟠 | 8 🟡 | 4 🟢 | 4 🟢 | 4 🟢 | 16 🟡 | 4 🟢 | 4 🟢 | 4 🟢 |
| `projects/known_defects.csv` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 18 🟡 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 12 🟡 | 3 🟢 | 3 🟢 | 3 🟢 |
| `sensitive/financials/payslips_q1.csv` | 4 🟢 | 4 🟢 | 8 🟡 | 4 🟢 | 48 🟠 | 48 🟠 | 0 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 24 🟠 | 4 🟢 | 4 🟢 | 4 🟢 |
| `sensitive/security/audit_log.txt` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 48 🟠 | 8 🟡 | 4 🟢 | 4 🟢 | 4 🟢 | 16 🟡 | 4 🟢 | 4 🟢 | 4 🟢 |
| `sensitive/security/private_key.pem` | 5 🟡 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 45 🔴 | 10 🟡 | 5 🟡 | 5 🟡 | 5 🟡 | 30 🟠 | 5 🟡 | 5 🟡 | 5 🟡 |
| `source_code/core.c` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 27 🟠 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 12 🟡 | 3 🟢 | 3 🟢 | 3 🟢 |
