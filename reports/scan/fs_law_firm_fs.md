# Scan — fs:law_firm_fs

_kind=filesystem · provenance=llm-scan · model_reviewed=True · bands={'low': 64, 'medium': 112, 'high': 98, 'critical': 34}_

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
| `README.md` | 1 |
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
| `templates/nda_template.txt` | 3 |
| `/` | 4 |
| `cases/` | 5 |
| `cases/CASE-2026-001/` | 4 |
| `cases/CASE-2026-002/` | 4 |
| `billing/` | 4 |
| `billing/timesheets/` | 4 |
| `clients/` | 5 |
| `clients/acme_corp/` | 4 |
| `clients/blue_whale_inc/` | 4 |
| `templates/` | 2 |

## Risk matrix (score · band)

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 6 🟡 | 9 🟠 | 0 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 4 🟡 | 1 🟢 | 1 🟢 | 0 🟢 |
| `billing/timesheets/timesheet_2026-05-01.txt` | 4 🟡 | 4 🟡 | 4 🟢 | 8 🟠 | 48 🔴 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 8 🟠 | 24 🟠 | 4 🟡 | 4 🟢 | 4 🟢 |
| `billing/timesheets/timesheet_2026-05-15.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 48 🔴 | 48 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 12 🟠 | 32 🟠 | 8 🟠 | 4 🟡 | 4 🟡 |
| `cases/CASE-2026-001/contract.txt` | 4 🟡 | 4 🟡 | 4 🟢 | 8 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟢 | 4 🟢 |
| `cases/CASE-2026-001/correspondence.txt` | 4 🟡 | 4 🟡 | 4 🟢 | 8 🟠 | 48 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟠 | 4 🟢 | 4 🟢 |
| `cases/CASE-2026-001/signed_agreement.pdf` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 48 🔴 | 24 🟠 | 0 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 24 🟡 | 4 🟢 | 4 🟢 | 4 🟢 |
| `cases/CASE-2026-002/contract.txt` | 4 🟡 | 4 🟡 | 4 🟢 | 8 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟢 | 4 🟢 |
| `cases/CASE-2026-002/correspondence.txt` | 4 🟡 | 4 🟡 | 4 🟢 | 8 🟠 | 48 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟠 | 4 🟢 | 4 🟢 |
| `cases/CASE-2026-002/signed_agreement.pdf` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 48 🔴 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟡 | 4 🟡 | 4 🟢 | 4 🟢 |
| `clients/acme_corp/intake.txt` | 4 🟡 | 4 🟡 | 4 🟢 | 8 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 4 🟡 | 4 🟢 | 4 🟢 |
| `clients/blue_whale_inc/intake.txt` | 4 🟡 | 4 🟡 | 4 🟢 | 8 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 4 🟡 | 4 🟢 | 4 🟢 |
| `templates/nda_template.txt` | 3 🟡 | 3 🟡 | 3 🟡 | 3 🟠 | 27 🔴 | 27 🔴 | 0 🟢 | 3 🟡 | 3 🟡 | 3 🟡 | 12 🟠 | 3 🟠 | 3 🟡 | 0 🟢 |
| `/` | 12 🟡 | 12 🟡 | 8 🟢 | 12 🟠 | 48 🔴 | 48 🔴 | 8 🟡 | 12 🟠 | 12 🟠 | 12 🟠 | 24 🟠 | 12 🟠 | 12 🟠 | 12 🟠 |
| `cases/` | 15 🟠 | 15 🟠 | 10 🟡 | 15 🟠 | 60 🔴 | 60 🔴 | 10 🟢 | 15 🟠 | 15 🟠 | 15 🟠 | 30 🟡 | 15 🟠 | 15 🟠 | 10 🟡 |
| `cases/CASE-2026-001/` | 4 🟡 | 4 🟡 | 8 🟠 | 12 🟠 | 36 🔴 | 24 🟠 | 8 🟡 | 12 🟠 | 8 🟠 | 12 🟠 | 32 🟠 | 12 🟠 | 12 🟠 | 12 🟠 |
| `cases/CASE-2026-002/` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 36 🔴 | 24 🟠 | 8 🟡 | 12 🟠 | 8 🟠 | 12 🟠 | 24 🟠 | 12 🟠 | 12 🟠 | 12 🟠 |
| `billing/` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟠 | 36 🔴 | 36 🔴 | 8 🟢 | 12 🟠 | 8 🟠 | 8 🟠 | 24 🟡 | 8 🟠 | 12 🟠 | 8 🟠 |
| `billing/timesheets/` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 8 🟠 | 12 🟠 | 8 🟠 | 24 🟠 | 8 🟠 | 12 🟠 | 8 🟡 |
| `clients/` | 10 🟡 | 10 🟡 | 10 🟡 | 15 🟠 | 45 🔴 | 45 🔴 | 20 🟡 | 15 🟠 | 15 🟠 | 15 🟠 | 20 🟡 | 15 🟠 | 15 🟠 | 10 🟡 |
| `clients/acme_corp/` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟠 | 36 🔴 | 24 🟠 | 8 🟢 | 12 🟠 | 12 🟠 | 8 🟡 | 32 🟠 | 12 🟠 | 12 🟠 | 4 🟢 |
| `clients/blue_whale_inc/` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟠 | 24 🔴 | 48 🔴 | 8 🟡 | 12 🟠 | 12 🟠 | 8 🟡 | 24 🟠 | 12 🟠 | 8 🟡 | 12 🟠 |
| `templates/` | 2 🟢 | 4 🟢 | 4 🟢 | 6 🟡 | 12 🟠 | 18 🟠 | 8 🟡 | 2 🟢 | 4 🟢 | 6 🟡 | 12 🟡 | 6 🟡 | 4 🟢 | 4 🟢 |
