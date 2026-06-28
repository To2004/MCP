# Evaluation ground truth — medical_clinic_fs

> Design-time reviewed risk table. **Used only to grade the scanner's output; the scanner never reads this file.**

## Server

| Field | Value |
| --- | --- |
| name | medical_clinic_fs |
| server | medical-clinic-fs |
| mcp_kind | filesystem |
| version | static-2026-06-23 |
| model_reviewed | True |
| formula | `asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact` |
| band_distribution | {'low': 43, 'medium': 9, 'high': 4, 'critical': 0} |
| judge_ran | True |
| judge_overrides | 5 |

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: File types or extensions representing different kinds of files stored in the filesystem.
- **blast_radius_meaning**: The extent to which a tool can affect assets; from reading a single file (narrow touch) to overwriting multiple files or directories (severe action).
- **worked_example**: The 'write_file' tool paired with a '.txt' asset class is highly severe because it can overwrite an existing text file, potentially losing its contents irreversibly.
- **dangerous_classes**: holds sensitive data, is executable
- **irreversible_actions**: overwrites existing files without warning, deletes files permanently, executes code on the system

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
| `.txt` | 2 |
| `.png` | 2 |
| `.md` | 3 |
| `(no extension)` | 3 |

## Risk matrix (score · band)

Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `.txt` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 18 🟡 | 12 🟡 | 0 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.png` | 2 🟢 | 0 🟢 | 2 🟢 | 2 🟢 | 18 🟡 | 12 🟡 | 0 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 8 🟡 | 2 🟢 | 2 🟢 | 0 🟢 |
| `.md` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 27 🟠 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 12 🟡 | 3 🟢 | 3 🟢 | 3 🟢 |
| `(no extension)` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 36 🟠 | 12 🟡 | 3 🟢 | 3 🟢 | 3 🟢 | 12 🟡 | 3 🟢 | 3 🟢 | 3 🟢 |
