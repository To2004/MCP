# Scan — fs:medical_clinic_fs

_kind=filesystem · provenance=llm-scan · model_reviewed=True · bands={'low': 19, 'medium': 143, 'high': 117, 'critical': 15}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the filesystem.
- **blast_radius_meaning**: The extent of a tool's impact on assets ranges from reading or listing files (narrow touch) to modifying, moving, or deleting files and directories (severe action).
- **worked_example**: The 'write_file' tool paired with the 'patients/alice_johnson/intake_form.txt' asset is highly severe because it can overwrite sensitive patient information.

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
| `README.md` | 2 |
| `billing/invoices/inv_2026-05-20_alice_johnson.txt` | 4 |
| `billing/invoices/inv_2026-05-21_bob_martinez.txt` | 4 |
| `patients/alice_johnson/intake_form.txt` | 5 |
| `patients/alice_johnson/medical_history.txt` | 5 |
| `patients/alice_johnson/prescription.txt` | 5 |
| `patients/bob_martinez/intake_form.txt` | 5 |
| `patients/bob_martinez/medical_history.txt` | 4 |
| `patients/bob_martinez/prescription.txt` | 4 |
| `policies/hipaa_notice.txt` | 4 |
| `scans/alice_johnson_xray.png` | 4 |
| `scans/bob_martinez_xray.png` | 4 |
| `staff_directory.txt` | 4 |
| `/` | 3 |
| `patients/` | 4 |
| `patients/alice_johnson/` | 4 |
| `patients/bob_martinez/` | 4 |
| `billing/` | 4 |
| `billing/invoices/` | 4 |
| `scans/` | 3 |
| `policies/` | 4 |

## Risk matrix (score · band)

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 12 🟡 | 0 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 2 🟢 | 2 🟢 | 0 🟢 |
| `billing/invoices/inv_2026-05-20_alice_johnson.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 36 🟠 | 4 🟡 | 4 🟡 | 4 🟡 |
| `billing/invoices/inv_2026-05-21_bob_martinez.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 24 🟠 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟡 | 4 🟡 |
| `patients/alice_johnson/intake_form.txt` | 5 🟡 | 5 🟡 | 10 🟡 | 20 🟠 | 30 🟠 | 30 🟠 | 0 🟠 | 5 🟡 | 5 🟡 | 20 🟠 | 30 🟠 | 5 🟡 | 5 🟡 | 5 🟡 |
| `patients/alice_johnson/medical_history.txt` | 5 🟡 | 5 🟡 | 10 🟡 | 20 🟠 | 30 🟠 | 30 🟠 | 0 🟠 | 5 🟡 | 5 🟡 | 5 🟡 | 30 🟠 | 5 🟡 | 5 🟡 | 5 🟡 |
| `patients/alice_johnson/prescription.txt` | 5 🟡 | 5 🟡 | 10 🟡 | 20 🟠 | 30 🟠 | 30 🟠 | 0 🟠 | 5 🟡 | 5 🟡 | 5 🟡 | 30 🟠 | 5 🟡 | 5 🟡 | 5 🟡 |
| `patients/bob_martinez/intake_form.txt` | 5 🟡 | 5 🟡 | 5 🟡 | 20 🟠 | 30 🟠 | 30 🟠 | 0 🟠 | 5 🟡 | 5 🟡 | 5 🟡 | 30 🟠 | 5 🟡 | 5 🟡 | 5 🟡 |
| `patients/bob_martinez/medical_history.txt` | 4 🟡 | 4 🟡 | 8 🟡 | 16 🟠 | 24 🟠 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟡 | 4 🟡 |
| `patients/bob_martinez/prescription.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 24 🟠 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟡 | 4 🟡 |
| `policies/hipaa_notice.txt` | 4 🟡 | 4 🟡 | 8 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟡 | 4 🟡 |
| `scans/alice_johnson_xray.png` | 4 🟡 | 0 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟡 | 0 🟡 |
| `scans/bob_martinez_xray.png` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟡 | 0 🟡 |
| `staff_directory.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟡 | 4 🟡 |
| `/` | 12 🟡 | 12 🟡 | 12 🟡 | 12 🟡 | 36 🟠 | 36 🟠 | 12 🟡 | 12 🟡 | 12 🟡 | 12 🟡 | 45 🟠 | 12 🟡 | 12 🟡 | 12 🟡 |
| `patients/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 60 🔴 | 16 🟠 | 16 🟠 | 16 🟠 |
| `patients/alice_johnson/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 60 🔴 | 16 🟠 | 16 🟠 | 16 🟠 |
| `patients/bob_martinez/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 60 🔴 | 16 🟠 | 16 🟠 | 16 🟠 |
| `billing/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 60 🔴 | 16 🟠 | 16 🟠 | 16 🟠 |
| `billing/invoices/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 36 🟠 | 16 🟠 | 16 🟠 | 16 🟠 |
| `scans/` | 12 🟡 | 12 🟡 | 12 🟡 | 12 🟡 | 36 🟠 | 36 🟠 | 12 🟡 | 12 🟡 | 12 🟡 | 12 🟡 | 27 🟠 | 12 🟡 | 12 🟡 | 12 🟡 |
| `policies/` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 36 🟠 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 36 🟠 | 16 🟠 | 16 🟠 | 16 🟠 |

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
