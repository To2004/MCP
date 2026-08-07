# Scan — fs:corp_filesystem

_kind=filesystem · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v4 · bands={'low': 85, 'medium': 54, 'high': 44, 'critical': 14, 'na': 111}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = org profile table (never LLM-scored)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- gated blast floor (impact >= 4): sens 5 -> blast >= 4, sens 4 -> blast >= 3
- impact-keyed floor (one tier lower): impact 5 -> blast >= 3, impact 4 -> blast >= 2
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof (impact <= 3 only, never a mutation): non-escaping read caps at 4, sens-1 caps at 4 — assets flagged hub/population/self-sufficient are exempt
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: files and directories within a corporate file share
- **blast_radius_meaning**: the extent of files or directories that can be accessed or modified by a tool, ranging from individual files to broad directory scopes
- **dangerous_classes**: contains sensitive PII at scale, is executable code, holds secrets
- **irreversible_actions**: write_file, edit_file, move_file
- **worked_example**: read_text_file on sensitive/security/private_key.pem is high severity due to the confidentiality of key material.

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
| `projects/known_defects.csv` | 3 |
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
| `file-contents` | 4 |
| `media-records` | 2 |
| `file-records` | 3 |
| `directory-structure` | 2 |
| `directory-contents` | 2 |
| `file-directory` | 2 |
| `file-metadata` | 2 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v4, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 3 (1×1×3) 🟢 | 3 (1×1×3) 🟢 | N/A | 6 (1×2×3) 🟢 | 15 (1×3×5) 🟢 | 8 (1×2×4) 🟢 | N/A | N/A | N/A | 2 (1×1×2) 🟢 | 8 (1×2×4) 🟢 | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | N/A |
| `onboarding/org_chart.png` | 6 (2×1×3) 🟢 | 6 (2×1×3) 🟢 | 6 (2×1×3) 🟢 | 12 (2×2×3) 🟢 | 30 (2×3×5) 🟢 | N/A | N/A | N/A | N/A | N/A | 16 (2×2×4) 🟢 | 4 (2×1×2) 🟢 | 4 (2×1×2) 🟢 | N/A |
| `projects/db_schema.sql` | 9 (3×1×3) 🟢 | 9 (3×1×3) 🟢 | N/A | 18 (3×2×3) 🟢 | 45 (3×3×5) 🟡 | 24 (3×2×4) 🟢 | N/A | N/A | 6 (3×1×2) 🟢 | N/A | 24 (3×2×4) 🟢 | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | N/A |
| `projects/known_defects.csv` | 9 (3×1×3) 🟢 | 9 (3×1×3) 🟢 | N/A | 18 (3×2×3) 🟢 | 45 (3×3×5) 🟡 | 24 (3×2×4) 🟢 | N/A | N/A | N/A | N/A | 24 (3×2×4) 🟢 | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | N/A |
| `sensitive/financials/payslips_q1.csv` | 60 (4×5×3) 🟡 | 60 (4×5×3) 🟡 | N/A | 60 (4×5×3) 🟡 | 100 (4×5×5) 🔴 | 80 (4×5×4) 🟠 | N/A | N/A | 16 (4×2×2) 🟢 | N/A | 80 (4×5×4) 🟠 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | N/A |
| `sensitive/security/audit_log.txt` | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | N/A | 24 (4×2×3) 🟢 | 60 (4×3×5) 🟡 | 48 (4×3×4) 🟡 | N/A | N/A | N/A | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | N/A |
| `sensitive/security/private_key.pem` | 75 (5×5×3) 🟠 | 75 (5×5×3) 🟠 | N/A | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | 100 (5×5×4) 🔴 | N/A | N/A | N/A | N/A | 100 (5×5×4) 🔴 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | N/A |
| `source_code/core.c` | 60 (4×5×3) 🟡 | 60 (4×5×3) 🟡 | N/A | 60 (4×5×3) 🟡 | 100 (4×5×5) 🔴 | 80 (4×5×4) 🟠 | N/A | N/A | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | N/A |
| `/` | 60 (5×4×3) 🟡 | 60 (5×4×3) 🟡 | N/A | 60 (5×4×3) 🟡 | 100 (5×4×5) 🔴 | 80 (5×4×4) 🟠 | 80 (5×4×4) 🟠 | 40 (5×4×2) 🟡 | 40 (5×4×2) 🟡 | 40 (5×4×2) 🟡 | 80 (5×4×4) 🟠 | 40 (5×4×2) 🟡 | 40 (5×4×2) 🟡 | 40 (5×4×2) 🟡 |
| `sensitive/` | 75 (5×5×3) 🟠 | 75 (5×5×3) 🟠 | N/A | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | 100 (5×5×4) 🔴 | 80 (5×4×4) 🟠 | 30 (5×3×2) 🟢 | 40 (5×4×2) 🟡 | 50 (5×5×2) 🟡 | 100 (5×5×4) 🔴 | 50 (5×5×2) 🟡 | 40 (5×4×2) 🟡 | 40 (5×4×2) 🟡 |
| `projects/` | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | N/A | 36 (3×4×3) 🟡 | 45 (3×3×5) 🟡 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 18 (3×3×2) 🟢 | 18 (3×3×2) 🟢 | 18 (3×3×2) 🟢 | 36 (3×3×4) 🟡 | 18 (3×3×2) 🟢 | 18 (3×3×2) 🟢 | 12 (3×2×2) 🟢 |
| `sensitive/security/` | 75 (5×5×3) 🟠 | 75 (5×5×3) 🟠 | N/A | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | 100 (5×5×4) 🔴 | 80 (5×4×4) 🟠 | 20 (5×2×2) 🟢 | 40 (5×4×2) 🟡 | 50 (5×5×2) 🟡 | 100 (5×5×4) 🔴 | 50 (5×5×2) 🟡 | 30 (5×3×2) 🟢 | 50 (5×5×2) 🟡 |
| `onboarding/` | N/A | N/A | 6 (2×1×3) 🟢 | 6 (2×1×3) 🟢 | 30 (2×3×5) 🟢 | 16 (2×2×4) 🟢 | 16 (2×2×4) 🟢 | 4 (2×1×2) 🟢 | 4 (2×1×2) 🟢 | 4 (2×1×2) 🟢 | 16 (2×2×4) 🟢 | 8 (2×2×2) 🟢 | 8 (2×2×2) 🟢 | 8 (2×2×2) 🟢 |
| `sensitive/financials/` | 60 (4×5×3) 🟡 | 60 (4×5×3) 🟡 | N/A | 60 (4×5×3) 🟡 | 100 (4×5×5) 🔴 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 40 (4×5×2) 🟡 | 80 (4×5×4) 🟠 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 |
| `source_code/` | 60 (4×5×3) 🟡 | 60 (4×5×3) 🟡 | N/A | 60 (4×5×3) 🟡 | 100 (4×5×5) 🔴 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 24 (4×3×2) 🟢 | 8 (4×1×2) 🟢 | 32 (4×4×2) 🟢 | 64 (4×4×4) 🟡 | 40 (4×5×2) 🟡 | 32 (4×4×2) 🟢 | 16 (4×2×2) 🟢 |
| `file-contents` | 48 (4×4×3) 🟡 | 48 (4×4×3) 🟡 | N/A | 48 (4×4×3) 🟡 | 80 (4×4×5) 🟠 | 64 (4×4×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `media-records` | 6 (2×1×3) 🟢 | 6 (2×1×3) 🟢 | 6 (2×1×3) 🟢 | 18 (2×3×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×2×2) 🟢 | 4 (2×1×2) 🟢 | N/A |
| `file-records` | N/A | N/A | N/A | N/A | 45 (3×3×5) 🟡 | 48 (3×4×4) 🟡 | N/A | N/A | N/A | N/A | 24 (3×2×4) 🟢 | N/A | 12 (3×2×2) 🟢 | N/A |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 24 (2×3×4) 🟢 | 8 (2×2×2) 🟢 | 8 (2×2×2) 🟢 | 16 (2×4×2) 🟢 | N/A | 16 (2×4×2) 🟢 | 16 (2×4×2) 🟢 | 16 (2×4×2) 🟢 |
| `directory-contents` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (2×1×2) 🟢 | 4 (2×1×2) 🟢 | 4 (2×1×2) 🟢 | N/A | 8 (2×2×2) 🟢 | 4 (2×1×2) 🟢 | 4 (2×1×2) 🟢 |
| `file-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×2×2) 🟢 | 8 (2×2×2) 🟢 | 8 (2×2×2) 🟢 | N/A | 8 (2×2×2) 🟢 | 8 (2×2×2) 🟢 | 8 (2×2×2) 🟢 |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×2×2) 🟢 | N/A | N/A | 8 (2×2×2) 🟢 | 8 (2×2×2) 🟢 | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 | 1 | N/A | 2 | 3 | 2 | N/A | N/A | N/A | 1 | 2 | 1 | 1 | N/A |
| `onboarding/org_chart.png` | 1 | 1 | 1 | 2 | 3 | N/A | N/A | N/A | N/A | N/A | 2 | 1 | 1 | N/A |
| `projects/db_schema.sql` | 1 | 1 | N/A | 2 | 3 | 2 | N/A | N/A | 1 | N/A | 2 | 1 | 1 | N/A |
| `projects/known_defects.csv` | 1 | 1 | N/A | 2 | 3 | 2 | N/A | N/A | N/A | N/A | 2 | 1 | 1 | N/A |
| `sensitive/financials/payslips_q1.csv` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | N/A | 2 | N/A | 5 | 1 | 1 | N/A |
| `sensitive/security/audit_log.txt` | 1 | 1 | N/A | 2 | 3 | 3 | N/A | N/A | N/A | 1 | 3 | 1 | 1 | N/A |
| `sensitive/security/private_key.pem` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | N/A | N/A | N/A | 5 | 1 | 1 | N/A |
| `source_code/core.c` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | N/A | 1 | 1 | 3 | 1 | 1 | N/A |
| `/` | 4 | 4 | N/A | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| `sensitive/` | 5 | 5 | N/A | 5 | 5 | 5 | 4 | 3 | 4 | 5 | 5 | 5 | 4 | 4 |
| `projects/` | 3 | 3 | N/A | 4 | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 2 |
| `sensitive/security/` | 5 | 5 | N/A | 5 | 5 | 5 | 4 | 2 | 4 | 5 | 5 | 5 | 3 | 5 |
| `onboarding/` | N/A | N/A | 1 | 1 | 3 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 2 |
| `sensitive/financials/` | 5 | 5 | N/A | 5 | 5 | 5 | 3 | 1 | 1 | 5 | 5 | 2 | 2 | 2 |
| `source_code/` | 5 | 5 | N/A | 5 | 5 | 5 | 3 | 3 | 1 | 4 | 4 | 5 | 4 | 2 |
| `file-contents` | 4 | 4 | N/A | 4 | 4 | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `media-records` | 1 | 1 | 1 | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 1 | N/A |
| `file-records` | N/A | N/A | N/A | N/A | 3 | 4 | N/A | N/A | N/A | N/A | 2 | N/A | 2 | N/A |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 2 | 2 | 4 | N/A | 4 | 4 | 4 |
| `directory-contents` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A | 2 | 1 | 1 |
| `file-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 2 | 2 | N/A | 2 | 2 | 2 |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | 2 | 2 | N/A |

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
