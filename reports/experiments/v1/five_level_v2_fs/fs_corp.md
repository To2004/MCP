# Scan — fs:corp

_kind=filesystem · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_na · bands={'low': 14, 'medium': 70, 'high': 81, 'critical': 22, 'na': 121}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: files and directories within the filesystem
- **blast_radius_meaning**: the extent of files or directories affected by a tool's action, from affecting a single file to impacting multiple files or entire directory structures
- **dangerous_classes**: holds sensitive or personal identifiable information, is executable, contains cryptographic keys
- **irreversible_actions**: overwriting an existing file with new content, deleting a directory and its contents, executing code from files
- **worked_example**: The 'write_file' tool paired with the 'sensitive/security/private_key.pem' asset is highly severe because it can overwrite critical cryptographic keys, leading to potential security breaches.

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

| asset | sensitivity |
| --- | --- |
| `README.md` | 1 |
| `onboarding/org_chart.png` | 2 |
| `projects/db_schema.sql` | 3 |
| `projects/known_defects.csv` | 4 |
| `sensitive/financials/payslips_q1.csv` | 4 |
| `sensitive/security/audit_log.txt` | 4 |
| `sensitive/security/private_key.pem` | 5 |
| `source_code/core.c` | 4 |
| `/` | 5 |
| `sensitive/` | 5 |
| `projects/` | 3 |
| `sensitive/security/` | 5 |
| `onboarding/` | 2 |
| `sensitive/financials/` | 4 |
| `source_code/` | 4 |
| `file-contents` | 5 |
| `media-records` | 2 |
| `file-records` | 3 |
| `directory-structure` | 1 |
| `directory-contents` | 2 |
| `file-directory` | 4 |
| `file-metadata` | 2 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_na, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 3 (1×1×3) 🟢 | 3 (1×1×3) 🟢 | N/A | N/A | 5 (1×1×5) 🟢 | 4 (1×1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (1×1×4) 🟢 | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | N/A |
| `onboarding/org_chart.png` | N/A | N/A | 6 (2×1×3) 🟢 | N/A | 10 (2×1×5) 🟢 | N/A | N/A | N/A | N/A | N/A | 8 (2×1×4) 🟢 | 4 (2×1×2) 🟢 | 4 (2×1×2) 🟢 | N/A |
| `projects/db_schema.sql` | 36 (3×4×3) 🟡 | 9 (3×1×3) 🟢 | N/A | 9 (3×1×3) 🟢 | 15 (3×1×5) 🟢 | 12 (3×1×4) 🟢 | N/A | N/A | N/A | N/A | 12 (3×1×4) 🟢 | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | N/A |
| `projects/known_defects.csv` | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | N/A | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 64 (4×4×4) 🟡 | N/A | N/A | N/A | N/A | 16 (4×1×4) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | N/A |
| `sensitive/financials/payslips_q1.csv` | 60 (4×5×3) 🟡 | 60 (4×5×3) 🟡 | N/A | 60 (4×5×3) 🟡 | 60 (4×3×5) 🟡 | 80 (4×5×4) 🟠 | N/A | N/A | N/A | N/A | 16 (4×1×4) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | N/A |
| `sensitive/security/audit_log.txt` | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | N/A | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 16 (4×1×4) 🟢 | N/A | N/A | N/A | N/A | 16 (4×1×4) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | N/A |
| `sensitive/security/private_key.pem` | 75 (5×5×3) 🟠 | 75 (5×5×3) 🟠 | N/A | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | 100 (5×5×4) 🔴 | N/A | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | N/A | 20 (5×1×4) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | N/A |
| `source_code/core.c` | 12 (4×1×3) 🟢 | 48 (4×4×3) 🟡 | N/A | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 16 (4×1×4) 🟢 | N/A | N/A | N/A | N/A | 32 (4×2×4) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | N/A |
| `/` | 75 (5×5×3) 🟠 | 15 (5×1×3) 🟢 | 15 (5×1×3) 🟢 | 75 (5×5×3) 🟠 | 100 (5×4×5) 🔴 | 60 (5×3×4) 🟡 | 40 (5×2×4) 🟡 | 40 (5×4×2) 🟡 | 20 (5×2×2) 🟢 | 40 (5×4×2) 🟡 | 40 (5×2×4) 🟡 | 40 (5×4×2) 🟡 | 40 (5×4×2) 🟡 | 40 (5×4×2) 🟡 |
| `sensitive/` | 75 (5×5×3) 🟠 | 75 (5×5×3) 🟠 | N/A | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | 100 (5×5×4) 🔴 | N/A | 20 (5×2×2) 🟢 | 20 (5×2×2) 🟢 | 30 (5×3×2) 🟢 | 60 (5×3×4) 🟡 | 20 (5×2×2) 🟢 | 20 (5×2×2) 🟢 | 20 (5×2×2) 🟢 |
| `projects/` | N/A | 36 (3×4×3) 🟡 | N/A | 36 (3×4×3) 🟡 | 45 (3×3×5) 🟡 | 36 (3×3×4) 🟡 | 12 (3×1×4) 🟢 | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | 36 (3×3×4) 🟡 | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 |
| `sensitive/security/` | 75 (5×5×3) 🟠 | 75 (5×5×3) 🟠 | N/A | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | 100 (5×5×4) 🔴 | N/A | 50 (5×5×2) 🟡 | 20 (5×2×2) 🟢 | 20 (5×2×2) 🟢 | 40 (5×2×4) 🟡 | 20 (5×2×2) 🟢 | 20 (5×2×2) 🟢 | 20 (5×2×2) 🟢 |
| `onboarding/` | N/A | N/A | 6 (2×1×3) 🟢 | 6 (2×1×3) 🟢 | 10 (2×1×5) 🟢 | N/A | 8 (2×1×4) 🟢 | 16 (2×4×2) 🟢 | 4 (2×1×2) 🟢 | 4 (2×1×2) 🟢 | 8 (2×1×4) 🟢 | 4 (2×1×2) 🟢 | 4 (2×1×2) 🟢 | 4 (2×1×2) 🟢 |
| `sensitive/financials/` | 12 (4×1×3) 🟢 | 60 (4×5×3) 🟡 | N/A | 48 (4×4×3) 🟡 | 80 (4×4×5) 🟠 | 64 (4×4×4) 🟡 | N/A | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 16 (4×2×2) 🟢 | 48 (4×3×4) 🟡 | 8 (4×1×2) 🟢 | 32 (4×4×2) 🟢 | 16 (4×2×2) 🟢 |
| `source_code/` | N/A | 48 (4×4×3) 🟡 | N/A | 60 (4×5×3) 🟡 | 80 (4×4×5) 🟠 | 64 (4×4×4) 🟡 | N/A | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 32 (4×4×2) 🟢 | 16 (4×1×4) 🟢 | 8 (4×1×2) 🟢 | 32 (4×4×2) 🟢 | 8 (4×1×2) 🟢 |
| `file-contents` | 75 (5×5×3) 🟠 | 75 (5×5×3) 🟠 | 15 (5×1×3) 🟢 | 75 (5×5×3) 🟠 | N/A | 20 (5×1×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `media-records` | N/A | N/A | 6 (2×1×3) 🟢 | 24 (2×4×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×2×2) 🟢 | N/A | N/A |
| `file-records` | 9 (3×1×3) 🟢 | 9 (3×1×3) 🟢 | N/A | 27 (3×3×3) 🟢 | 15 (3×1×5) 🟢 | 36 (3×3×4) 🟡 | N/A | N/A | N/A | N/A | 24 (3×2×4) 🟢 | N/A | N/A | N/A |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 12 (1×3×4) 🟢 | 8 (1×4×2) 🟢 | 8 (1×4×2) 🟢 | 8 (1×4×2) 🟢 | 12 (1×3×4) 🟢 | 8 (1×4×2) 🟢 | N/A | 8 (1×4×2) 🟢 |
| `directory-contents` | N/A | N/A | N/A | 24 (2×4×3) 🟢 | N/A | N/A | N/A | 16 (2×4×2) 🟢 | 16 (2×4×2) 🟢 | 16 (2×4×2) 🟢 | N/A | 16 (2×4×2) 🟢 | 12 (2×3×2) 🟢 | 8 (2×2×2) 🟢 |
| `file-directory` | N/A | N/A | N/A | N/A | 60 (4×3×5) 🟡 | 48 (4×3×4) 🟡 | 48 (4×3×4) 🟡 | 32 (4×4×2) 🟢 | 32 (4×4×2) 🟢 | 32 (4×4×2) 🟢 | 48 (4×3×4) 🟡 | 24 (4×3×2) 🟢 | 8 (4×1×2) 🟢 | 16 (4×2×2) 🟢 |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (2×4×2) 🟢 | 16 (2×4×2) 🟢 | N/A | N/A | N/A | 8 (2×2×2) 🟢 | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 | 1 | N/A | N/A | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `onboarding/org_chart.png` | N/A | N/A | 1 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `projects/db_schema.sql` | 4 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `projects/known_defects.csv` | 1 | 1 | N/A | 1 | 1 | 4 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `sensitive/financials/payslips_q1.csv` | 5 | 5 | N/A | 5 | 3 | 5 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `sensitive/security/audit_log.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `sensitive/security/private_key.pem` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | 1 | 1 | N/A | 1 | 1 | 1 | N/A |
| `source_code/core.c` | 1 | 4 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | N/A | 2 | 1 | 1 | N/A |
| `/` | 5 | 1 | 1 | 5 | 4 | 3 | 2 | 4 | 2 | 4 | 2 | 4 | 4 | 4 |
| `sensitive/` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | 2 | 2 | 3 | 3 | 2 | 2 | 2 |
| `projects/` | N/A | 4 | N/A | 4 | 3 | 3 | 1 | 2 | 2 | 2 | 3 | 2 | 2 | 2 |
| `sensitive/security/` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | 5 | 2 | 2 | 2 | 2 | 2 | 2 |
| `onboarding/` | N/A | N/A | 1 | 1 | 1 | N/A | 1 | 4 | 1 | 1 | 1 | 1 | 1 | 1 |
| `sensitive/financials/` | 1 | 5 | N/A | 4 | 4 | 4 | N/A | 1 | 1 | 2 | 3 | 1 | 4 | 2 |
| `source_code/` | N/A | 4 | N/A | 5 | 4 | 4 | N/A | 1 | 1 | 4 | 1 | 1 | 4 | 1 |
| `file-contents` | 5 | 5 | 1 | 5 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `media-records` | N/A | N/A | 1 | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A |
| `file-records` | 1 | 1 | N/A | 3 | 1 | 3 | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 4 | 4 | 4 | 3 | 4 | N/A | 4 |
| `directory-contents` | N/A | N/A | N/A | 4 | N/A | N/A | N/A | 4 | 4 | 4 | N/A | 4 | 3 | 2 |
| `file-directory` | N/A | N/A | N/A | N/A | 3 | 3 | 3 | 4 | 4 | 4 | 3 | 3 | 1 | 2 |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 4 | N/A | N/A | N/A | 2 | N/A |

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
| `read_text_file` | `tail` | 2 | >= 10000 | limits output to last N lines, but large values can be resou |
| `read_text_file` | `head` | 2 | >= 10000 | limits output to first N lines, but large values can be reso |
| `read_media_file` | `path` | 4 | — | can be used to access sensitive files within allowed directo |
| `read_multiple_files` | `paths` | 5 | >= 100 paths | Allows bulk read of files, potentially overwhelming server r |
| `write_file` | `content` | 5 | — | fully controllable payload can inject malicious code or data |
| `write_file` | `path` | 4 | — | can target critical system files |
| `edit_file` | `edits` | 5 | — | fully controlled payload with potential for bulk changes |
| `edit_file` | `path` | 3 | — | can target sensitive files |
| `edit_file` | `dryRun` | 1 | — | only previews changes, no actual modification |
| `create_directory` | `path` | 3 | — | can be used to create arbitrary directory paths |
| `list_directory` | `path` | 4 | — | can point to sensitive directories |
| `list_directory_with_sizes` | `path` | 4 | — | Can target any directory, potentially exposing sensitive inf |
| `list_directory_with_sizes` | `sortBy` | 1 | — | Limited to predefined sorting options, no amplification of r |
| `directory_tree` | `excludePatterns` | 4 | length >= 100 | can be used to exclude large portions of the directory tree, |
| `directory_tree` | `path` | 3 | — | can target sensitive directories |
| `move_file` | `destination` | 4 | — | can overwrite critical system files or directories |
| `move_file` | `source` | 3 | — | can specify arbitrary file paths |
| `search_files` | `pattern` | 4 | — | allows broad file matching via glob patterns |
| `search_files` | `path` | 3 | — | can target sensitive directories |
| `search_files` | `excludePatterns` | 2 | — | limits the scope of search, potentially reducing risk |
| `get_file_info` | `path` | 4 | — | can target any file or directory, potentially sensitive |
