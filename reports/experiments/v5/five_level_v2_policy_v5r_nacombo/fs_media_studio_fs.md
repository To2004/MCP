# Scan — fs:media_studio_fs

_kind=filesystem · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v5r_nacombo · bands={'low': 63, 'medium': 36, 'high': 12, 'critical': 0, 'na': 113}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = LLM classification against the org POLICY (classify -> map; the org supplies no numbers)
- tool impact = deterministic ladder (static_impact.py); the v4 impact prompt decides only where the ladder abstains (confidence < 0.5)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- blast floor, UNGATED: 
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof: REMOVED in this mode (a cap can only under-score)
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: filesystem

## Tool impact

| tool | impact |
| --- | --- |
| `read_file` | 3 |
| `read_text_file` | 3 |
| `read_media_file` | 3 |
| `read_multiple_files` | 3 |
| `write_file` | 4 |
| `edit_file` | 4 |
| `create_directory` | 4 |
| `list_directory` | 2 |
| `list_directory_with_sizes` | 2 |
| `directory_tree` | 2 |
| `move_file` | 2 |
| `search_files` | 2 |
| `get_file_info` | 2 |
| `list_allowed_directories` | 2 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `unreleased-imagery` | 4 |
| `campaign-briefs` | 4 |
| `client-contracts` | 4 |
| `invoices` | 4 |
| `shoot-notes` | 3 |
| `project-pipeline` | 4 |
| `public-overview` | 1 |
| `file-contents` | 4 |
| `media-records` | 4 |
| `file-records` | 3 |
| `directory-records` | 3 |
| `directory-structure` | 4 |
| `directory-contents` | 4 |
| `file-directory` | 4 |
| `file-metadata` | 2 |
| `mount-directory` | 2 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v5r_nacombo, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `unreleased-imagery` | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | N/A | N/A | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | N/A |
| `campaign-briefs` | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | N/A | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 64 (4×4×4) 🟡 | N/A | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | N/A |
| `client-contracts` | 48 (4×4×3) 🟡 | 48 (4×4×3) 🟡 | N/A | 60 (4×5×3) 🟡 | 64 (4×4×4) 🟡 | 64 (4×4×4) 🟡 | N/A | 24 (4×3×2) 🟢 | 32 (4×4×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 24 (4×3×2) 🟢 | 16 (4×2×2) 🟢 | N/A |
| `invoices` | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | N/A | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 64 (4×4×4) 🟡 | N/A | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | N/A | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | N/A |
| `shoot-notes` | 18 (3×2×3) 🟢 | 18 (3×2×3) 🟢 | N/A | 27 (3×3×3) 🟢 | 24 (3×2×4) 🟢 | 24 (3×2×4) 🟢 | N/A | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | N/A | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | N/A |
| `project-pipeline` | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | N/A | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 64 (4×4×4) 🟡 | N/A | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | N/A | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | N/A |
| `public-overview` | 6 (1×2×3) 🟢 | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | 4 (1×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `file-contents` | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 64 (4×4×4) 🟡 | N/A | N/A | 16 (4×2×2) 🟢 | N/A | 16 (4×2×2) 🟢 | 24 (4×3×2) 🟢 | N/A | N/A |
| `media-records` | N/A | N/A | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | 16 (4×2×2) 🟢 | N/A | 16 (4×2×2) 🟢 | N/A |
| `file-records` | N/A | N/A | N/A | 27 (3×3×3) 🟢 | 48 (3×4×4) 🟡 | 48 (3×4×4) 🟡 | N/A | N/A | N/A | N/A | 12 (3×2×2) 🟢 | N/A | 12 (3×2×2) 🟢 | N/A |
| `directory-records` | N/A | N/A | N/A | N/A | N/A | N/A | 48 (3×4×4) 🟡 | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | 18 (3×3×2) 🟢 | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 32 (4×2×4) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | N/A | 16 (4×2×2) 🟢 | N/A | 16 (4×2×2) 🟢 |
| `directory-contents` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | N/A | 16 (4×2×2) 🟢 | N/A | N/A |
| `file-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | N/A | 16 (4×2×2) 🟢 | N/A | 16 (4×2×2) 🟢 |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×2×2) 🟢 | 8 (2×2×2) 🟢 | N/A | N/A | N/A | 8 (2×2×2) 🟢 | N/A |
| `mount-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×2×2) 🟢 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `unreleased-imagery` | 3 | 3 | 3 | 4 | 4 | N/A | N/A | 2 | 2 | 2 | 2 | 2 | 2 | N/A |
| `campaign-briefs` | 3 | 3 | N/A | 4 | 4 | 4 | N/A | 2 | 2 | 2 | 2 | 2 | 2 | N/A |
| `client-contracts` | 4 | 4 | N/A | 5 | 4 | 4 | N/A | 3 | 4 | 2 | 2 | 3 | 2 | N/A |
| `invoices` | 3 | 3 | N/A | 4 | 4 | 4 | N/A | 2 | 2 | N/A | 2 | 2 | 2 | N/A |
| `shoot-notes` | 2 | 2 | N/A | 3 | 2 | 2 | N/A | 2 | 2 | N/A | 2 | 2 | 2 | N/A |
| `project-pipeline` | 3 | 3 | N/A | 4 | 4 | 4 | N/A | 2 | 2 | N/A | 2 | 2 | 2 | N/A |
| `public-overview` | 2 | 2 | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `file-contents` | 3 | 3 | 3 | 4 | 4 | 4 | N/A | N/A | 2 | N/A | 2 | 3 | N/A | N/A |
| `media-records` | N/A | N/A | 3 | 3 | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | 2 | N/A |
| `file-records` | N/A | N/A | N/A | 3 | 4 | 4 | N/A | N/A | N/A | N/A | 2 | N/A | 2 | N/A |
| `directory-records` | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 2 | 2 | 2 | 2 | 3 | 2 | 2 |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 2 | 2 | 2 | N/A | 2 | N/A | 2 |
| `directory-contents` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 2 | 2 | N/A | 2 | N/A | N/A |
| `file-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 2 | 2 | N/A | 2 | N/A | 2 |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 2 | N/A | N/A | N/A | 2 | N/A |
| `mount-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 |

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
