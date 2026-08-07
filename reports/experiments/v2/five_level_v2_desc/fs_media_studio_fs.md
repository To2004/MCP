# Scan — fs:media_studio_fs

_kind=filesystem · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_desc · bands={'low': 97, 'medium': 82, 'high': 74, 'critical': 11, 'na': 128}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–25), scaled to this max.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the commercial photography studio's file system.
- **blast_radius_meaning**: The extent to which a tool can affect files or directories; from affecting a single file to impacting multiple files or entire directory structures.
- **dangerous_classes**: Contracts with clients (confidential terms), Invoices (financial details)
- **irreversible_actions**: write_file, edit_file, move_file
- **worked_example**: The 'write_file' tool on the 'clients/citybank/contract.txt' asset could overwrite the contract, altering its integrity and causing financial or legal issues.

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
| `move_file` | 5 |
| `search_files` | 2 |
| `get_file_info` | 2 |
| `list_allowed_directories` | 2 |

## Asset sensitivity

_Not scored in `impact_mode=five_level_v2_desc`: the organization's written description of this server states how severe each asset is, so no separate 1–5 sensitivity primitive is derived. The 28 assets below still form the matrix axis; the score is `blast × impact`._

| asset | sensitivity |
| --- | --- |
| `README.md` | — |
| `clients/citybank/contract.txt` | — |
| `clients/neon_brand/contract.txt` | — |
| `invoices/inv_2026-05-15_citybank.txt` | — |
| `invoices/inv_2026-05-21_neon_brand.txt` | — |
| `project_pipeline.txt` | — |
| `shoots/SHOOT-2026-A/brief.txt` | — |
| `shoots/SHOOT-2026-A/notes.txt` | — |
| `shoots/SHOOT-2026-A/photo_001.jpg` | — |
| `shoots/SHOOT-2026-A/photo_002.jpg` | — |
| `shoots/SHOOT-2026-B/brief.txt` | — |
| `shoots/SHOOT-2026-B/notes.txt` | — |
| `shoots/SHOOT-2026-B/photo_001.jpg` | — |
| `/` | — |
| `shoots/` | — |
| `shoots/SHOOT-2026-A/` | — |
| `shoots/SHOOT-2026-B/` | — |
| `clients/` | — |
| `invoices/` | — |
| `clients/citybank/` | — |
| `clients/neon_brand/` | — |
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
| `README.md` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | N/A | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `clients/citybank/contract.txt` | 3 (1×3) 🟢 | 15 (5×3) 🟠 | N/A | 6 (2×3) 🟢 | 5 (1×5) 🟢 | 20 (5×4) 🔴 | N/A | N/A | N/A | N/A | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `clients/neon_brand/contract.txt` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 20 (5×4) 🔴 | N/A | N/A | N/A | N/A | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `invoices/inv_2026-05-15_citybank.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 12 (4×3) 🟡 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (2×2) 🟢 | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `invoices/inv_2026-05-21_neon_brand.txt` | 3 (1×3) 🟢 | 15 (5×3) 🟠 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `project_pipeline.txt` | 12 (4×3) 🟡 | 15 (5×3) 🟠 | N/A | 6 (2×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `shoots/SHOOT-2026-A/brief.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `shoots/SHOOT-2026-A/notes.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `shoots/SHOOT-2026-A/photo_001.jpg` | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 5 (1×5) 🟢 | N/A | N/A | N/A | 2 (1×2) 🟢 | N/A | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `shoots/SHOOT-2026-A/photo_002.jpg` | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 5 (1×5) 🟢 | N/A | N/A | N/A | 2 (1×2) 🟢 | N/A | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `shoots/SHOOT-2026-B/brief.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `shoots/SHOOT-2026-B/notes.txt` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `shoots/SHOOT-2026-B/photo_001.jpg` | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 5 (1×5) 🟢 | N/A | N/A | N/A | N/A | N/A | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `/` | 6 (2×3) 🟢 | 12 (4×3) 🟡 | 12 (4×3) 🟡 | 12 (4×3) 🟡 | 20 (4×5) 🔴 | 12 (3×4) 🟡 | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 20 (4×5) 🔴 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 |
| `shoots/` | 9 (3×3) 🟡 | 12 (4×3) 🟡 | 12 (4×3) 🟡 | 12 (4×3) 🟡 | 15 (3×5) 🟠 | 12 (3×4) 🟡 | N/A | 8 (4×2) 🟡 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 5 (1×5) 🟢 | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 8 (4×2) 🟡 |
| `shoots/SHOOT-2026-A/` | 3 (1×3) 🟢 | 6 (2×3) 🟢 | 9 (3×3) 🟡 | 9 (3×3) 🟡 | 15 (3×5) 🟠 | 12 (3×4) 🟡 | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 15 (3×5) 🟠 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 2 (1×2) 🟢 |
| `shoots/SHOOT-2026-B/` | 3 (1×3) 🟢 | 9 (3×3) 🟡 | 9 (3×3) 🟡 | 12 (4×3) 🟡 | 15 (3×5) 🟠 | 8 (2×4) 🟡 | N/A | 2 (1×2) 🟢 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 20 (4×5) 🔴 | 2 (1×2) 🟢 | 8 (4×2) 🟡 | 2 (1×2) 🟢 |
| `clients/` | 12 (4×3) 🟡 | 15 (5×3) 🟠 | N/A | 15 (5×3) 🟠 | 5 (1×5) 🟢 | 8 (2×4) 🟡 | N/A | 8 (4×2) 🟡 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 20 (4×5) 🔴 | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 2 (1×2) 🟢 |
| `invoices/` | 12 (4×3) 🟡 | 9 (3×3) 🟡 | N/A | 15 (5×3) 🟠 | 20 (4×5) 🔴 | 8 (2×4) 🟡 | N/A | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 4 (2×2) 🟢 | 15 (3×5) 🟠 | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 4 (2×2) 🟢 |
| `clients/citybank/` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 4 (1×4) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (2×2) 🟢 | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (2×2) 🟢 |
| `clients/neon_brand/` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 20 (4×5) 🔴 | 4 (1×4) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 5 (1×5) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (2×2) 🟢 |
| `file-contents` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | 3 (1×3) 🟢 | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `media-records` | N/A | N/A | 9 (3×3) 🟡 | 9 (3×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | N/A | N/A |
| `file-records` | 15 (5×3) 🟠 | 6 (2×3) 🟢 | N/A | 15 (5×3) 🟠 | 20 (4×5) 🔴 | 16 (4×4) 🟠 | N/A | N/A | N/A | N/A | 20 (4×5) 🔴 | 8 (4×2) 🟡 | N/A | N/A |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 12 (3×4) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | N/A | 4 (2×2) 🟢 | N/A | 4 (2×2) 🟢 |
| `directory-contents` | N/A | N/A | N/A | 12 (4×3) 🟡 | N/A | N/A | N/A | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | N/A | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 4 (2×2) 🟢 |
| `file-directory` | N/A | N/A | N/A | 12 (4×3) 🟡 | 20 (4×5) 🔴 | 16 (4×4) 🟠 | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 15 (3×5) 🟠 | 8 (4×2) 🟡 | 2 (1×2) 🟢 | 4 (2×2) 🟢 |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (4×2) 🟡 | 4 (2×2) 🟢 | 8 (4×2) 🟡 | N/A | 4 (2×2) 🟢 | 2 (1×2) 🟢 | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 | 1 | N/A | N/A | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `clients/citybank/contract.txt` | 1 | 5 | N/A | 2 | 1 | 5 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `clients/neon_brand/contract.txt` | 5 | 5 | N/A | 1 | 1 | 5 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `invoices/inv_2026-05-15_citybank.txt` | 1 | 1 | N/A | 4 | 1 | 1 | N/A | 1 | 1 | 2 | 1 | 1 | 1 | N/A |
| `invoices/inv_2026-05-21_neon_brand.txt` | 1 | 5 | N/A | 1 | 1 | 1 | N/A | 1 | 1 | 1 | 1 | 1 | 1 | N/A |
| `project_pipeline.txt` | 4 | 5 | N/A | 2 | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `shoots/SHOOT-2026-A/brief.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | 1 | 1 | 1 | 1 | 1 | N/A |
| `shoots/SHOOT-2026-A/notes.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | 1 | 1 | 1 | 1 | 1 | N/A |
| `shoots/SHOOT-2026-A/photo_001.jpg` | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | 1 | N/A | 1 | 1 | 1 | N/A |
| `shoots/SHOOT-2026-A/photo_002.jpg` | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | 1 | N/A | 1 | 1 | 1 | N/A |
| `shoots/SHOOT-2026-B/brief.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | 1 | 1 | 1 | 1 | 1 | N/A |
| `shoots/SHOOT-2026-B/notes.txt` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | 1 | 1 | 1 | 1 | 1 | N/A |
| `shoots/SHOOT-2026-B/photo_001.jpg` | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `/` | 2 | 4 | 4 | 4 | 4 | 3 | 1 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| `shoots/` | 3 | 4 | 4 | 4 | 3 | 3 | N/A | 4 | 2 | 2 | 1 | 2 | 4 | 4 |
| `shoots/SHOOT-2026-A/` | 1 | 2 | 3 | 3 | 3 | 3 | N/A | 1 | 1 | 1 | 3 | 4 | 4 | 1 |
| `shoots/SHOOT-2026-B/` | 1 | 3 | 3 | 4 | 3 | 2 | N/A | 1 | 4 | 4 | 4 | 1 | 4 | 1 |
| `clients/` | 4 | 5 | N/A | 5 | 1 | 2 | N/A | 4 | 1 | 1 | 4 | 2 | 4 | 1 |
| `invoices/` | 4 | 3 | N/A | 5 | 4 | 2 | N/A | 2 | 4 | 2 | 3 | 2 | 4 | 2 |
| `clients/citybank/` | 5 | 5 | N/A | 5 | 5 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 2 |
| `clients/neon_brand/` | 1 | 1 | N/A | 1 | 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| `file-contents` | 5 | 5 | 1 | 5 | 5 | 5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `media-records` | N/A | N/A | 3 | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A |
| `file-records` | 5 | 2 | N/A | 5 | 4 | 4 | N/A | N/A | N/A | N/A | 4 | 4 | N/A | N/A |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 4 | 4 | 4 | N/A | 2 | N/A | 2 |
| `directory-contents` | N/A | N/A | N/A | 4 | N/A | N/A | N/A | 4 | 4 | 4 | N/A | 4 | 4 | 2 |
| `file-directory` | N/A | N/A | N/A | 4 | 4 | 4 | 1 | 4 | 2 | 4 | 3 | 4 | 1 | 2 |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 2 | 4 | N/A | 2 | 1 | N/A |

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
