# Scan — fs:medical_clinic_fs

_kind=filesystem · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_desc · bands={'low': 95, 'medium': 91, 'high': 46, 'critical': 6, 'na': 154}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–25), scaled to this max.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: files and directories within the medical clinic's patient record system
- **blast_radius_meaning**: the extent to which a tool can affect files or directories; from affecting a single file to enumerating all contents of a directory
- **dangerous_classes**: contains PHI (Protected Health Information), is executable and can alter prescriptions, holds financial PII linking patients to services
- **irreversible_actions**: write_file, edit_file, move_file
- **worked_example**: read_text_file on 'patients/alice_johnson/prescription.txt' is high severity due to the confidentiality of PHI and potential integrity harm if altered

## Tool impact

| tool | impact |
| --- | --- |
| `read_file` | 3 |
| `read_text_file` | 3 |
| `read_media_file` | 3 |
| `read_multiple_files` | 3 |
| `write_file` | 5 |
| `edit_file` | 4 |
| `create_directory` | 4 |
| `list_directory` | 2 |
| `list_directory_with_sizes` | 2 |
| `directory_tree` | 2 |
| `move_file` | 4 |
| `search_files` | 2 |
| `get_file_info` | 2 |
| `list_allowed_directories` | 2 |

## Asset sensitivity

_Not scored in `impact_mode=five_level_v2_desc`: the organization's written description of this server states how severe each asset is, so no separate 1–5 sensitivity primitive is derived. The 28 assets below still form the matrix axis; the score is `blast × impact`._

| asset | sensitivity |
| --- | --- |
| `README.md` | — |
| `billing/invoices/inv_2026-05-20_alice_johnson.txt` | — |
| `billing/invoices/inv_2026-05-21_bob_martinez.txt` | — |
| `patients/alice_johnson/intake_form.txt` | — |
| `patients/alice_johnson/medical_history.txt` | — |
| `patients/alice_johnson/prescription.txt` | — |
| `patients/bob_martinez/intake_form.txt` | — |
| `patients/bob_martinez/medical_history.txt` | — |
| `patients/bob_martinez/prescription.txt` | — |
| `policies/hipaa_notice.txt` | — |
| `scans/alice_johnson_xray.png` | — |
| `scans/bob_martinez_xray.png` | — |
| `staff_directory.txt` | — |
| `/` | — |
| `patients/` | — |
| `patients/alice_johnson/` | — |
| `patients/bob_martinez/` | — |
| `billing/` | — |
| `billing/invoices/` | — |
| `scans/` | — |
| `policies/` | — |
| `file-contents` | — |
| `media-records` | — |
| `file-records` | — |
| `directory-structure` | — |
| `directory-contents` | — |
| `file-directory` | — |
| `file-metadata` | — |

## Risk matrix (score · band)

_Each cell shows `score (blast×impact)` — sensitivity is not scored in this mode; impact_mode=five_level_v2_desc, score ranges 0–25. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | N/A | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `billing/invoices/inv_2026-05-20_alice_johnson.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | 2 (1×2) 🟢 | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `billing/invoices/inv_2026-05-21_bob_martinez.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | 4 (2×2) 🟢 | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `patients/alice_johnson/intake_form.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `patients/alice_johnson/medical_history.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `patients/alice_johnson/prescription.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `patients/bob_martinez/intake_form.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `patients/bob_martinez/medical_history.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `patients/bob_martinez/prescription.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `policies/hipaa_notice.txt` | 3 (1×3) 🟢 | 15 (5×3) 🟠 | N/A | N/A | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `scans/alice_johnson_xray.png` | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 5 (1×5) 🟢 | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `scans/bob_martinez_xray.png` | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 5 (1×5) 🟢 | N/A | N/A | N/A | 2 (1×2) 🟢 | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `staff_directory.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | N/A | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `/` | 12 (4×3) 🟡 | 15 (5×3) 🟠 | 3 (1×3) 🟢 | 12 (4×3) 🟡 | 25 (5×5) 🔴 | 16 (4×4) 🟠 | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 16 (4×4) 🟠 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 |
| `patients/` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 15 (5×3) 🟠 | 20 (4×5) 🔴 | 16 (4×4) 🟠 | N/A | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 6 (3×2) 🟢 | 4 (2×2) 🟢 |
| `patients/alice_johnson/` | 6 (2×3) 🟢 | 6 (2×3) 🟢 | N/A | 6 (2×3) 🟢 | 15 (3×5) 🟠 | 8 (2×4) 🟡 | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 12 (3×4) 🟡 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 |
| `patients/bob_martinez/` | 6 (2×3) 🟢 | 3 (1×3) 🟢 | N/A | 6 (2×3) 🟢 | 10 (2×5) 🟡 | 8 (2×4) 🟡 | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 12 (3×4) 🟡 | 2 (1×2) 🟢 | 4 (2×2) 🟢 | 2 (1×2) 🟢 |
| `billing/` | 3 (1×3) 🟢 | 12 (4×3) 🟡 | N/A | 12 (4×3) 🟡 | 20 (4×5) 🔴 | 16 (4×4) 🟠 | N/A | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 12 (3×4) 🟡 | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 4 (2×2) 🟢 |
| `billing/invoices/` | 15 (5×3) 🟠 | 6 (2×3) 🟢 | N/A | 12 (4×3) 🟡 | 15 (3×5) 🟠 | 16 (4×4) 🟠 | N/A | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 12 (3×4) 🟡 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 4 (2×2) 🟢 |
| `scans/` | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 12 (4×3) 🟡 | 20 (4×5) 🔴 | N/A | N/A | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 16 (4×4) 🟠 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 4 (2×2) 🟢 |
| `policies/` | 15 (5×3) 🟠 | 3 (1×3) 🟢 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (2×2) 🟢 | 16 (4×4) 🟠 | 2 (1×2) 🟢 | 8 (4×2) 🟡 | 4 (2×2) 🟢 |
| `file-contents` | 15 (5×3) 🟠 | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 15 (5×3) 🟠 | N/A | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `media-records` | N/A | N/A | 3 (1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `file-records` | 15 (5×3) 🟠 | 3 (1×3) 🟢 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 16 (4×4) 🟠 | 8 (4×2) 🟡 | N/A | N/A |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 8 (4×2) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A |
| `directory-contents` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 6 (3×2) 🟢 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | N/A | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 |
| `file-directory` | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 16 (4×4) 🟠 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | N/A |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | N/A | N/A | 4 (2×2) 🟢 | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 | 1 | N/A | N/A | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `billing/invoices/inv_2026-05-20_alice_johnson.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | 1 | N/A | 1 | 1 | 1 | N/A |
| `billing/invoices/inv_2026-05-21_bob_martinez.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | 2 | N/A | 1 | 1 | 1 | N/A |
| `patients/alice_johnson/intake_form.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | 1 | 1 | 1 | 1 | 1 | N/A |
| `patients/alice_johnson/medical_history.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | 1 | 1 | 1 | 1 | 1 | N/A |
| `patients/alice_johnson/prescription.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | 1 | 1 | 1 | 1 | N/A |
| `patients/bob_martinez/intake_form.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `patients/bob_martinez/medical_history.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `patients/bob_martinez/prescription.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `policies/hipaa_notice.txt` | 1 | 5 | N/A | N/A | 1 | 1 | N/A | N/A | N/A | 1 | 1 | 1 | 1 | N/A |
| `scans/alice_johnson_xray.png` | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `scans/bob_martinez_xray.png` | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | 1 | N/A | 1 | 1 | 1 | N/A |
| `staff_directory.txt` | 1 | 1 | N/A | N/A | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `/` | 4 | 5 | 1 | 4 | 5 | 4 | 1 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| `patients/` | 1 | 1 | N/A | 5 | 4 | 4 | N/A | 4 | 4 | 4 | 1 | 4 | 3 | 2 |
| `patients/alice_johnson/` | 2 | 2 | N/A | 2 | 3 | 2 | N/A | 1 | 1 | 1 | 3 | 1 | 1 | 1 |
| `patients/bob_martinez/` | 2 | 1 | N/A | 2 | 2 | 2 | N/A | 1 | 1 | 1 | 3 | 1 | 2 | 1 |
| `billing/` | 1 | 4 | N/A | 4 | 4 | 4 | N/A | 4 | 4 | 4 | 3 | 2 | 4 | 2 |
| `billing/invoices/` | 5 | 2 | N/A | 4 | 3 | 4 | N/A | 2 | 2 | 2 | 3 | 2 | 2 | 2 |
| `scans/` | 1 | N/A | 1 | 4 | 4 | N/A | N/A | 2 | 4 | 4 | 4 | 4 | 4 | 2 |
| `policies/` | 5 | 1 | N/A | 5 | 5 | 5 | 1 | 1 | 1 | 2 | 4 | 1 | 4 | 2 |
| `file-contents` | 5 | 1 | 1 | 5 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `media-records` | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `file-records` | 5 | 1 | N/A | 5 | 5 | 1 | N/A | N/A | N/A | N/A | 4 | 4 | N/A | N/A |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 4 | N/A | N/A | N/A | N/A | N/A | N/A |
| `directory-contents` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 4 | 4 | N/A | 4 | 4 | 4 |
| `file-directory` | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 4 | 4 | 4 | 4 | 4 | 4 | N/A |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 4 | 4 | N/A | N/A | 2 | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

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
