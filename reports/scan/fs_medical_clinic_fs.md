# Scan — fs:medical_clinic_fs

_kind=filesystem · provenance=llm-scan · model_reviewed=True · bands={'low': 56, 'medium': 87, 'high': 95, 'critical': 56}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the filesystem.
- **blast_radius_meaning**: The extent of a tool's impact on assets ranges from reading or listing files (narrow touch) to modifying, moving, or deleting files and directories (severe action).
- **worked_example**: The 'write_file' tool paired with the 'patients/alice_johnson/prescription.txt' asset is highly severe because it can overwrite sensitive patient data.

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
| `billing/invoices/inv_2026-05-21_bob_martinez.txt` | 3 |
| `patients/alice_johnson/intake_form.txt` | 4 |
| `patients/alice_johnson/medical_history.txt` | 5 |
| `patients/alice_johnson/prescription.txt` | 5 |
| `patients/bob_martinez/intake_form.txt` | 4 |
| `patients/bob_martinez/medical_history.txt` | 4 |
| `patients/bob_martinez/prescription.txt` | 5 |
| `policies/hipaa_notice.txt` | 3 |
| `scans/alice_johnson_xray.png` | 4 |
| `scans/bob_martinez_xray.png` | 4 |
| `staff_directory.txt` | 4 |
| `/` | 4 |
| `patients/` | 4 |
| `patients/alice_johnson/` | 4 |
| `patients/bob_martinez/` | 4 |
| `billing/` | 4 |
| `billing/invoices/` | 4 |
| `scans/` | 4 |
| `policies/` | 4 |

## Risk matrix (score · band)

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 12 🟡 | 0 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 18 🟠 | 2 🟢 | 2 🟢 | 0 🟢 |
| `billing/invoices/inv_2026-05-20_alice_johnson.txt` | 4 🟡 | 4 🟡 | 4 🟢 | 8 🟠 | 48 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 48 🔴 | 4 🟠 | 4 🟢 | 4 🟢 |
| `billing/invoices/inv_2026-05-21_bob_martinez.txt` | 3 🟡 | 3 🟡 | 3 🟢 | 6 🟠 | 36 🔴 | 27 🟠 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 36 🔴 | 3 🟡 | 3 🟢 | 3 🟢 |
| `patients/alice_johnson/intake_form.txt` | 4 🟡 | 8 🟡 | 8 🟡 | 8 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 48 🔴 | 4 🟠 | 4 🟢 | 4 🟢 |
| `patients/alice_johnson/medical_history.txt` | 5 🟡 | 5 🟡 | 15 🟠 | 10 🟠 | 45 🔴 | 30 🟠 | 0 🟢 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 15 🟠 | 5 🟢 | 5 🟢 |
| `patients/alice_johnson/prescription.txt` | 5 🟡 | 10 🟡 | 10 🟡 | 10 🟠 | 45 🔴 | 45 🔴 | 0 🟢 | 5 🟢 | 5 🟢 | 10 🟠 | 60 🔴 | 15 🟠 | 5 🟢 | 5 🟢 |
| `patients/bob_martinez/intake_form.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟠 | 48 🔴 | 4 🟠 | 4 🟢 | 4 🟢 |
| `patients/bob_martinez/medical_history.txt` | 4 🟡 | 4 🟡 | 8 🟡 | 8 🟠 | 36 🔴 | 24 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 48 🔴 | 4 🟡 | 4 🟢 | 4 🟢 |
| `patients/bob_martinez/prescription.txt` | 10 🟡 | 5 🟡 | 10 🟡 | 10 🟠 | 60 🔴 | 60 🔴 | 0 🟢 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 5 🟠 | 5 🟢 | 5 🟢 |
| `policies/hipaa_notice.txt` | 3 🟡 | 3 🟡 | 6 🟡 | 3 🟠 | 27 🔴 | 27 🔴 | 0 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 27 🔴 | 3 🟡 | 3 🟢 | 3 🟢 |
| `scans/alice_johnson_xray.png` | 4 🟡 | 0 🟡 | 4 🟡 | 4 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟠 | 36 🔴 | 4 🟠 | 4 🟡 | 0 🟢 |
| `scans/bob_martinez_xray.png` | 4 🟡 | 0 🟡 | 4 🟡 | 4 🟠 | 36 🔴 | 12 🟠 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟠 | 48 🔴 | 4 🟠 | 4 🟡 | 0 🟢 |
| `staff_directory.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 4 🟠 | 24 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 36 🔴 | 4 🟠 | 4 🟢 | 4 🟢 |
| `/` | 12 🟠 | 12 🟠 | 8 🟡 | 12 🟠 | 36 🔴 | 48 🔴 | 16 🟡 | 12 🟠 | 12 🟠 | 12 🟠 | 36 🔴 | 8 🟡 | 12 🟠 | 4 🟢 |
| `patients/` | 8 🟡 | 8 🟡 | 8 🟡 | 12 🟠 | 36 🔴 | 48 🔴 | 16 🟠 | 12 🟠 | 12 🟠 | 12 🟠 | 48 🔴 | 12 🟠 | 12 🟠 | 8 🟡 |
| `patients/alice_johnson/` | 12 🟠 | 8 🟠 | 12 🟠 | 12 🟠 | 36 🔴 | 36 🔴 | 16 🟡 | 8 🟠 | 12 🟠 | 12 🟠 | 36 🔴 | 12 🟠 | 12 🟠 | 8 🟠 |
| `patients/bob_martinez/` | 12 🟠 | 12 🟠 | 12 🟠 | 8 🟠 | 36 🔴 | 36 🔴 | 16 🟡 | 12 🟠 | 12 🟠 | 12 🟠 | 48 🔴 | 12 🟠 | 12 🟠 | 12 🟠 |
| `billing/` | 12 🟠 | 12 🟠 | 12 🟠 | 12 🟠 | 36 🔴 | 36 🔴 | 16 🟡 | 12 🟠 | 12 🟠 | 12 🟠 | 48 🔴 | 12 🟠 | 12 🟠 | 8 🟡 |
| `billing/invoices/` | 8 🟠 | 12 🟠 | 12 🟠 | 12 🟠 | 36 🔴 | 48 🔴 | 16 🟡 | 12 🟠 | 12 🟠 | 8 🟡 | 48 🔴 | 12 🟠 | 12 🟠 | 8 🟡 |
| `scans/` | 12 🟡 | 8 🟡 | 8 🟡 | 12 🟠 | 36 🔴 | 48 🔴 | 16 🟡 | 12 🟠 | 12 🟠 | 12 🟠 | 48 🔴 | 12 🟠 | 12 🟠 | 8 🟡 |
| `policies/` | 4 🟡 | 8 🟡 | 8 🟡 | 12 🟠 | 48 🔴 | 36 🔴 | 16 🟠 | 12 🟠 | 8 🟡 | 12 🟠 | 48 🔴 | 12 🟠 | 12 🟠 | 12 🟠 |
