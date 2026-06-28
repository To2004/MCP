# Scan — fs:corp_filesystem

_kind=filesystem · provenance=llm-scan · model_reviewed=True · bands={'low': 52, 'medium': 56, 'high': 71, 'critical': 31}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the filesystem.
- **blast_radius_meaning**: The extent to which a tool can affect files or directories; from reading a single file (narrow touch) to modifying multiple files across different directories (severe action).
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
| `projects/db_schema.sql` | 4 |
| `projects/known_defects.csv` | 3 |
| `sensitive/financials/payslips_q1.csv` | 4 |
| `sensitive/security/audit_log.txt` | 4 |
| `sensitive/security/private_key.pem` | 5 |
| `source_code/core.c` | 3 |
| `/` | 5 |
| `sensitive/` | 5 |
| `projects/` | 4 |
| `sensitive/security/` | 5 |
| `onboarding/` | 2 |
| `sensitive/financials/` | 4 |
| `source_code/` | 3 |

## Risk matrix (score · band)

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 6 🟡 | 6 🟡 | 0 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 6 🟡 | 1 🟢 | 1 🟢 | 0 🟢 |
| `onboarding/org_chart.png` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟡 | 12 🟠 | 6 🟠 | 0 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 18 🟠 | 2 🟢 | 2 🟢 | 2 🟢 |
| `projects/db_schema.sql` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟠 | 24 🔴 | 24 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 36 🔴 | 4 🟠 | 4 🟢 | 4 🟢 |
| `projects/known_defects.csv` | 3 🟡 | 3 🟡 | 3 🟡 | 3 🟠 | 18 🟠 | 18 🟠 | 0 🟢 | 3 🟡 | 3 🟡 | 3 🟡 | 18 🟠 | 3 🟡 | 3 🟡 | 3 🟡 |
| `sensitive/financials/payslips_q1.csv` | 8 🟠 | 8 🟠 | 4 🟡 | 12 🔴 | 36 🔴 | 24 🔴 | 8 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🔴 | 8 🟠 | 4 🟢 | 4 🟢 |
| `sensitive/security/audit_log.txt` | 8 🟡 | 8 🟡 | 4 🟢 | 8 🟠 | 36 🔴 | 36 🔴 | 8 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🔴 | 4 🟢 | 4 🟢 | 4 🟢 |
| `sensitive/security/private_key.pem` | 10 🟠 | 10 🟠 | 10 🟠 | 10 🟠 | 45 🔴 | 60 🔴 | 20 🟡 | 5 🟢 | 5 🟢 | 10 🟡 | 45 🔴 | 5 🟢 | 10 🟡 | 5 🟢 |
| `source_code/core.c` | 3 🟡 | 3 🟡 | 3 🟡 | 3 🟠 | 18 🟠 | 18 🟠 | 0 🟢 | 3 🟡 | 3 🟡 | 3 🟡 | 27 🟠 | 3 🟡 | 3 🟢 | 3 🟢 |
| `/` | 20 🟠 | 10 🟡 | 10 🟡 | 15 🟠 | 45 🔴 | 45 🔴 | 20 🟡 | 15 🟠 | 15 🟠 | 15 🟠 | 60 🔴 | 15 🟠 | 15 🟠 | 10 🟡 |
| `sensitive/` | 5 🟡 | 15 🟠 | 10 🟠 | 15 🟠 | 45 🔴 | 45 🔴 | 10 🟢 | 10 🟠 | 15 🟠 | 15 🟠 | 60 🔴 | 10 🟡 | 15 🟠 | 10 🟡 |
| `projects/` | 12 🟡 | 8 🟡 | 12 🟡 | 12 🟠 | 48 🔴 | 36 🔴 | 16 🟡 | 12 🟠 | 12 🟠 | 12 🟠 | 36 🔴 | 12 🟠 | 12 🟡 | 12 🟠 |
| `sensitive/security/` | 15 🟠 | 10 🟠 | 10 🟠 | 10 🟠 | 45 🔴 | 45 🔴 | 20 🟡 | 10 🟠 | 10 🟠 | 10 🟠 | 60 🔴 | 15 🟠 | 10 🟠 | 10 🟠 |
| `onboarding/` | 4 🟢 | 4 🟢 | 4 🟢 | 6 🟡 | 12 🟠 | 12 🟠 | 8 🟡 | 6 🟡 | 2 🟢 | 6 🟡 | 24 🟠 | 6 🟡 | 6 🟡 | 4 🟢 |
| `sensitive/financials/` | 8 🟠 | 8 🟠 | 8 🟠 | 8 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 8 🟠 | 12 🟠 | 12 🟠 | 48 🔴 | 12 🟠 | 12 🟠 | 12 🟠 |
| `source_code/` | 9 🟡 | 6 🟡 | 6 🟡 | 9 🟠 | 27 🔴 | 27 🔴 | 12 🟡 | 9 🟠 | 9 🟠 | 9 🟠 | 36 🔴 | 9 🟠 | 9 🟠 | 9 🟠 |
