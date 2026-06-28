# Evaluation ground truth — corp_filesystem

> Design-time reviewed risk table. **Used only to grade the scanner's output; the scanner never reads this file.**

## Server

| Field | Value |
| --- | --- |
| name | corp_filesystem |
| server | secure-filesystem-server |
| mcp_kind | filesystem |
| version | static-2026-06-23 |
| model_reviewed | True |
| formula | `asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact` |
| band_distribution | {'low': 67, 'medium': 23, 'high': 5, 'critical': 3} |
| judge_ran | True |
| judge_overrides | 10 |

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: file types or extensions representing different kinds of files stored in the filesystem.
- **blast_radius_meaning**: the extent to which a tool can affect assets; from reading a single file (narrow touch) to overwriting multiple files or creating/deleting directories (severe action).
- **worked_example**: write_file on .pem: Overwriting a PEM file, which likely contains sensitive cryptographic keys, is highly severe due to the potential for irreversible data loss and security breaches.
- **dangerous_classes**: holds secrets, is executable
- **irreversible_actions**: overwrites existing files without warning, deletes or moves files and directories

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
| `.csv` | 3 |
| `.c` | 3 |
| `.md` | 2 |
| `.pem` | 5 |
| `.png` | 2 |
| `.sql` | 4 |
| `.txt` | 2 |

## Risk matrix (score · band)

Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `.csv` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 18 🟡 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 18 🟡 | 3 🟢 | 3 🟢 | 3 🟢 |
| `.c` | 3 🟢 | 3 🟢 | 0 🟢 | 3 🟢 | 27 🟠 | 18 🟡 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 18 🟡 | 3 🟢 | 3 🟢 | 3 🟢 |
| `.md` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 18 🟡 | 12 🟡 | 0 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.pem` | 5 🟡 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 60 🔴 | 0 🟢 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 5 🟡 | 5 🟡 | 5 🟡 |
| `.png` | 2 🟢 | 0 🟢 | 2 🟢 | 2 🟢 | 18 🟡 | 12 🟡 | 0 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 2 🟢 | 2 🟢 | 2 🟢 |
| `.sql` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 36 🟠 | 0 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 36 🟠 | 4 🟢 | 4 🟢 | 4 🟢 |
| `.txt` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 18 🟡 | 12 🟡 | 0 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 2 🟢 | 2 🟢 | 2 🟢 |
