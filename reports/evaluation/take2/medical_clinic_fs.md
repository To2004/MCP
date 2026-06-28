# Evaluation ground truth — medical_clinic_fs

> Design-time reviewed risk table. **Used only to grade the scanner's output; the scanner never reads this file.**

## Server

| Field | Value |
| --- | --- |
| name | medical_clinic_fs |
| server | medical-clinic-fs |
| mcp_kind | filesystem |
| version | static-take2-2026-06-23 |
| model_reviewed | True |
| formula | `asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact` |
| band_distribution | {'low': 111, 'medium': 39, 'high': 23, 'critical': 9} |
| judge_ran | True |
| judge_overrides | 37 |

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the server's allowed directories.
- **blast_radius_meaning**: The extent to which a tool can affect files or directories; from reading a single file (narrow touch) to overwriting multiple files or creating/deleting directories (severe action).
- **worked_example**: The 'write_file' tool paired with the 'patients/alice_johnson/medical_history.txt' asset is highly severe because it can overwrite sensitive medical information.
- **dangerous_classes**: holds PII at scale, is executable
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
| `README.md` | 1 |
| `billing/invoices/inv_2026-05-20_alice_johnson.txt` | 5 |
| `billing/invoices/inv_2026-05-21_bob_martinez.txt` | 3 |
| `patients/alice_johnson/intake_form.txt` | 4 |
| `patients/alice_johnson/medical_history.txt` | 5 |
| `patients/alice_johnson/prescription.txt` | 4 |
| `patients/bob_martinez/intake_form.txt` | 4 |
| `patients/bob_martinez/medical_history.txt` | 5 |
| `patients/bob_martinez/prescription.txt` | 4 |
| `policies/hipaa_notice.txt` | 2 |
| `scans/alice_johnson_xray.png` | 4 |
| `scans/bob_martinez_xray.png` | 3 |
| `staff_directory.txt` | 3 |

## Risk matrix (score · band)

Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 9 🟡 | 6 🟢 | 2 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 6 🟢 | 1 🟢 | 1 🟢 | 1 🟢 |
| `billing/invoices/inv_2026-05-20_alice_johnson.txt` | 5 🟡 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 60 🔴 | 0 🟢 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 5 🟡 | 5 🟡 | 5 🟡 |
| `billing/invoices/inv_2026-05-21_bob_martinez.txt` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 36 🟠 | 6 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
| `patients/alice_johnson/intake_form.txt` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 48 🟠 | 8 🟡 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 4 🟢 | 4 🟢 | 4 🟢 |
| `patients/alice_johnson/medical_history.txt` | 5 🟡 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 60 🔴 | 10 🟡 | 5 🟡 | 5 🟡 | 5 🟡 | 45 🔴 | 5 🟡 | 5 🟡 | 5 🟡 |
| `patients/alice_johnson/prescription.txt` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 48 🟠 | 8 🟡 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 4 🟢 | 4 🟢 | 4 🟢 |
| `patients/bob_martinez/intake_form.txt` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 48 🟠 | 0 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 4 🟢 | 4 🟢 | 4 🟢 |
| `patients/bob_martinez/medical_history.txt` | 5 🟡 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 45 🔴 | 10 🟡 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 5 🟡 | 5 🟡 | 5 🟡 |
| `patients/bob_martinez/prescription.txt` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 24 🟠 | 8 🟡 | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 4 🟢 | 4 🟢 | 4 🟢 |
| `policies/hipaa_notice.txt` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 18 🟡 | 18 🟡 | 4 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 24 🟠 | 2 🟢 | 2 🟢 | 2 🟢 |
| `scans/alice_johnson_xray.png` | 4 🟢 | 0 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 0 🟠 | 0 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 36 🟠 | 4 🟢 | 4 🟢 | 0 🟢 |
| `scans/bob_martinez_xray.png` | 3 🟢 | 0 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 0 🟢 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 3 🟢 | 3 🟢 | 0 🟢 |
| `staff_directory.txt` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 18 🟡 | 6 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 3 🟢 | 3 🟢 | 3 🟢 |
