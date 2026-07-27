# Scan — fs:corp

_kind=filesystem · provenance=llm-scan · model_reviewed=True · impact_mode=hybrid_na · bands={'low': 29, 'medium': 21, 'high': 22, 'critical': 0, 'na': 26}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: file types or extensions representing different kinds of files stored in the filesystem.
- **blast_radius_meaning**: the extent to which a tool can affect multiple files or directories; from affecting a single file to potentially altering all files within allowed directories.
- **dangerous_classes**: executable files, files containing secrets (e.g., .pem), database schema (.sql)
- **irreversible_actions**: write_file, edit_file when it overwrites critical content, move_file that results in file loss or corruption
- **worked_example**: The 'write_file' tool paired with a '.sql' asset class could overwrite the entire contents of a database schema, which is highly irreversible and dangerous.

## Tool impact

| tool | impact |
| --- | --- |
| `read_file` | 2 |
| `read_text_file` | 2 |
| `read_media_file` | 2 |
| `read_multiple_files` | 2 |
| `write_file` | 4 |
| `edit_file` | 4 |
| `create_directory` | 3 |
| `list_directory` | 1 |
| `list_directory_with_sizes` | 1 |
| `directory_tree` | 1 |
| `move_file` | 4 |
| `search_files` | 2 |
| `get_file_info` | 1 |
| `list_allowed_directories` | 1 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `.csv` | 3 |
| `.c` | 3 |
| `.md` | 3 |
| `.pem` | 5 |
| `.png` | 2 |
| `.sql` | 4 |
| `.txt` | 3 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=hybrid_na, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `.csv` | 21.21 (3×1×2) 🟢 | 21.21 (3×1×2) 🟢 | N/A | 36.74 (3×3×2) 🟡 | 60 (3×4×4) 🟡 | 51.96 (3×3×4) 🟡 | N/A | 15 (3×1×1) 🟢 | 15 (3×1×1) 🟢 | 25.98 (3×3×1) 🟢 | 30 (3×1×4) 🟢 | 42.43 (3×4×2) 🟡 | 15 (3×1×1) 🟢 | N/A |
| `.c` | 21.21 (3×1×2) 🟢 | 21.21 (3×1×2) 🟢 | N/A | 36.74 (3×3×2) 🟡 | 60 (3×4×4) 🟡 | 51.96 (3×3×4) 🟡 | N/A | 15 (3×1×1) 🟢 | 15 (3×1×1) 🟢 | 15 (3×1×1) 🟢 | 30 (3×1×4) 🟢 | 21.21 (3×1×2) 🟢 | 15 (3×1×1) 🟢 | N/A |
| `.md` | 21.21 (3×1×2) 🟢 | 21.21 (3×1×2) 🟢 | N/A | 36.74 (3×3×2) 🟡 | 30 (3×1×4) 🟢 | 42.43 (3×2×4) 🟡 | N/A | 15 (3×1×1) 🟢 | 15 (3×1×1) 🟢 | 15 (3×1×1) 🟢 | 30 (3×1×4) 🟢 | 36.74 (3×3×2) 🟡 | 15 (3×1×1) 🟢 | N/A |
| `.pem` | 79.06 (5×5×2) 🟠 | 70.71 (5×4×2) 🟠 | N/A | 50 (5×2×2) 🟡 | 111.8 (5×5×4) 🔴 | 111.8 (5×5×4) 🔴 | N/A | N/A | 25 (5×1×1) 🟢 | N/A | 111.8 (5×5×4) 🔴 | 35.36 (5×1×2) 🟡 | 25 (5×1×1) 🟢 | N/A |
| `.png` | N/A | N/A | 14.14 (2×1×2) 🟢 | 14.14 (2×1×2) 🟢 | 40 (2×4×4) 🟡 | N/A | N/A | 10 (2×1×1) 🟢 | 10 (2×1×1) 🟢 | N/A | 20 (2×1×4) 🟢 | 24.49 (2×3×2) 🟢 | 10 (2×1×1) 🟢 | N/A |
| `.sql` | 56.57 (4×4×2) 🟡 | 56.57 (4×4×2) 🟡 | N/A | 48.99 (4×3×2) 🟡 | 89.44 (4×5×4) 🟠 | 80 (4×4×4) 🟠 | N/A | 20 (4×1×1) 🟢 | 20 (4×1×1) 🟢 | 20 (4×1×1) 🟢 | 40 (4×1×4) 🟡 | 48.99 (4×3×2) 🟡 | 20 (4×1×1) 🟢 | N/A |
| `.txt` | 21.21 (3×1×2) 🟢 | 21.21 (3×1×2) 🟢 | N/A | 36.74 (3×3×2) 🟡 | 60 (3×4×4) 🟡 | 42.43 (3×2×4) 🟡 | N/A | 15 (3×1×1) 🟢 | 15 (3×1×1) 🟢 | 15 (3×1×1) 🟢 | 30 (3×1×4) 🟢 | 36.74 (3×3×2) 🟡 | 15 (3×1×1) 🟢 | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `.csv` | 1 | 1 | N/A | 3 | 4 | 3 | N/A | 1 | 1 | 3 | 1 | 4 | 1 | N/A |
| `.c` | 1 | 1 | N/A | 3 | 4 | 3 | N/A | 1 | 1 | 1 | 1 | 1 | 1 | N/A |
| `.md` | 1 | 1 | N/A | 3 | 1 | 2 | N/A | 1 | 1 | 1 | 1 | 3 | 1 | N/A |
| `.pem` | 5 | 4 | N/A | 2 | 5 | 5 | N/A | N/A | 1 | N/A | 5 | 1 | 1 | N/A |
| `.png` | N/A | N/A | 1 | 1 | 4 | N/A | N/A | 1 | 1 | N/A | 1 | 3 | 1 | N/A |
| `.sql` | 4 | 4 | N/A | 3 | 5 | 4 | N/A | 1 | 1 | 1 | 1 | 3 | 1 | N/A |
| `.txt` | 1 | 1 | N/A | 3 | 4 | 2 | N/A | 1 | 1 | 1 | 1 | 3 | 1 | N/A |

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
