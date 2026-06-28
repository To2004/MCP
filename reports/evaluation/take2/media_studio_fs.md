# Evaluation ground truth — media_studio_fs

> Design-time reviewed risk table. **Used only to grade the scanner's output; the scanner never reads this file.**

## Server

| Field | Value |
| --- | --- |
| name | media_studio_fs |
| server | media-studio-fs |
| mcp_kind | filesystem |
| version | static-take2-2026-06-23 |
| model_reviewed | True |
| formula | `asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact` |
| band_distribution | {'low': 141, 'medium': 7, 'high': 34, 'critical': 0} |
| judge_ran | True |
| judge_overrides | 39 |

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the filesystem.
- **blast_radius_meaning**: The extent to which a tool can affect files or directories; from reading a single file (narrow touch) to modifying multiple files across different directories (severe action).
- **worked_example**: The 'write_file' tool paired with the 'clients/citybank/contract.txt' asset is highly severe as it can overwrite a contract file, potentially leading to data loss or corruption.
- **dangerous_classes**: holds sensitive information, is executable
- **irreversible_actions**: write_file, edit_file, move_file

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
| `move_file` | 3 |
| `search_files` | 1 |
| `get_file_info` | 1 |
| `list_allowed_directories` | 1 |

### Asset sensitivity (1 low – 5 crown-jewel)

| asset | sensitivity |
| --- | --- |
| `README.md` | 1 |
| `clients/citybank/contract.txt` | 4 |
| `clients/neon_brand/contract.txt` | 4 |
| `invoices/inv_2026-05-15_citybank.txt` | 4 |
| `invoices/inv_2026-05-21_neon_brand.txt` | 4 |
| `project_pipeline.txt` | 3 |
| `shoots/SHOOT-2026-A/brief.txt` | 3 |
| `shoots/SHOOT-2026-A/notes.txt` | 3 |
| `shoots/SHOOT-2026-A/photo_001.jpg` | 3 |
| `shoots/SHOOT-2026-A/photo_002.jpg` | 3 |
| `shoots/SHOOT-2026-B/brief.txt` | 3 |
| `shoots/SHOOT-2026-B/notes.txt` | 3 |
| `shoots/SHOOT-2026-B/photo_001.jpg` | 3 |

## Risk matrix (score · band)

Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 9 🟡 | 6 🟢 | 2 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 9 🟡 | 1 🟢 | 1 🟢 | 1 🟢 |
| `clients/citybank/contract.txt` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 36 🟠 | 8 🟡 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 4 🟢 | 4 🟢 | 4 🟢 |
| `clients/neon_brand/contract.txt` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 48 🟠 | 0 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 4 🟢 | 4 🟢 | 4 🟢 |
| `invoices/inv_2026-05-15_citybank.txt` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 48 🟠 | 8 🟡 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 4 🟢 | 4 🟢 | 4 🟢 |
| `invoices/inv_2026-05-21_neon_brand.txt` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 48 🟠 | 8 🟡 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 4 🟢 | 4 🟢 | 4 🟢 |
| `project_pipeline.txt` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 27 🟠 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
| `shoots/SHOOT-2026-A/brief.txt` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 36 🟠 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
| `shoots/SHOOT-2026-A/notes.txt` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 36 🟠 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
| `shoots/SHOOT-2026-A/photo_001.jpg` | 3 🟢 | 0 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 36 🟠 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
| `shoots/SHOOT-2026-A/photo_002.jpg` | 3 🟢 | 0 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 18 🟡 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
| `shoots/SHOOT-2026-B/brief.txt` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 36 🟠 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
| `shoots/SHOOT-2026-B/notes.txt` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 36 🟠 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
| `shoots/SHOOT-2026-B/photo_001.jpg` | 3 🟢 | 0 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 18 🟡 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
