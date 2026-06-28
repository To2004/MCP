# Scan — fs:media_studio_fs

_kind=filesystem · provenance=llm-scan · model_reviewed=True · bands={'low': 49, 'medium': 125, 'high': 86, 'critical': 34}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the filesystem.
- **blast_radius_meaning**: The extent to which a tool can affect files or directories; from reading a single file (narrow touch) to modifying multiple files across different directories (severe action).
- **worked_example**: The 'write_file' tool paired with the 'clients/citybank/contract.txt' asset is highly severe because it can overwrite sensitive client contract information irreversibly.

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
| `move_file` | 2 |
| `search_files` | 1 |
| `get_file_info` | 1 |
| `list_allowed_directories` | 1 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `README.md` | 1 |
| `clients/citybank/contract.txt` | 4 |
| `clients/neon_brand/contract.txt` | 4 |
| `invoices/inv_2026-05-15_citybank.txt` | 4 |
| `invoices/inv_2026-05-21_neon_brand.txt` | 4 |
| `project_pipeline.txt` | 3 |
| `shoots/SHOOT-2026-A/brief.txt` | 4 |
| `shoots/SHOOT-2026-A/notes.txt` | 3 |
| `shoots/SHOOT-2026-A/photo_001.jpg` | 3 |
| `shoots/SHOOT-2026-A/photo_002.jpg` | 3 |
| `shoots/SHOOT-2026-B/brief.txt` | 4 |
| `shoots/SHOOT-2026-B/notes.txt` | 3 |
| `shoots/SHOOT-2026-B/photo_001.jpg` | 3 |
| `/` | 4 |
| `shoots/` | 2 |
| `shoots/SHOOT-2026-A/` | 3 |
| `shoots/SHOOT-2026-B/` | 3 |
| `clients/` | 4 |
| `invoices/` | 3 |
| `clients/citybank/` | 4 |
| `clients/neon_brand/` | 4 |

## Risk matrix (score · band)

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 6 🟡 | 6 🟡 | 0 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 4 🟡 | 1 🟢 | 1 🟢 | 0 🟢 |
| `clients/citybank/contract.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 24 🔴 | 24 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟡 | 0 🟢 |
| `clients/neon_brand/contract.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 24 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 4 🟡 | 4 🟡 | 0 🟢 |
| `invoices/inv_2026-05-15_citybank.txt` | 4 🟡 | 4 🟡 | 4 🟢 | 8 🟠 | 48 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 4 🟡 | 4 🟢 | 4 🟢 |
| `invoices/inv_2026-05-21_neon_brand.txt` | 4 🟡 | 4 🟡 | 4 🟢 | 8 🟠 | 48 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 4 🟡 | 4 🟢 | 4 🟢 |
| `project_pipeline.txt` | 3 🟡 | 3 🟡 | 3 🟡 | 3 🟠 | 27 🔴 | 18 🟠 | 0 🟢 | 3 🟡 | 3 🟡 | 3 🟡 | 12 🟡 | 3 🟡 | 3 🟢 | 0 🟢 |
| `shoots/SHOOT-2026-A/brief.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 4 🟡 | 4 🟡 | 4 🟡 |
| `shoots/SHOOT-2026-A/notes.txt` | 3 🟡 | 3 🟡 | 3 🟢 | 6 🟠 | 27 🔴 | 27 🔴 | 0 🟢 | 3 🟡 | 3 🟡 | 3 🟡 | 12 🟠 | 3 🟡 | 3 🟢 | 3 🟢 |
| `shoots/SHOOT-2026-A/photo_001.jpg` | 3 🟡 | 3 🟡 | 3 🟡 | 6 🟠 | 27 🔴 | 9 🟠 | 0 🟢 | 3 🟡 | 3 🟡 | 3 🟡 | 18 🟠 | 3 🟡 | 3 🟡 | 0 🟢 |
| `shoots/SHOOT-2026-A/photo_002.jpg` | 3 🟡 | 3 🟡 | 3 🟡 | 3 🟠 | 27 🔴 | 9 🟠 | 0 🟢 | 3 🟡 | 3 🟡 | 3 🟠 | 12 🟡 | 3 🟠 | 3 🟢 | 0 🟢 |
| `shoots/SHOOT-2026-B/brief.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 4 🟡 | 4 🟡 | 0 🟢 |
| `shoots/SHOOT-2026-B/notes.txt` | 3 🟡 | 3 🟡 | 3 🟢 | 6 🟠 | 27 🔴 | 27 🔴 | 0 🟢 | 3 🟡 | 3 🟡 | 3 🟡 | 12 🟠 | 3 🟡 | 3 🟢 | 3 🟢 |
| `shoots/SHOOT-2026-B/photo_001.jpg` | 3 🟡 | 3 🟢 | 3 🟡 | 3 🟠 | 36 🔴 | 18 🟠 | 0 🟢 | 3 🟡 | 3 🟡 | 3 🟠 | 18 🟠 | 3 🟡 | 3 🟢 | 0 🟢 |
| `/` | 12 🟡 | 12 🟡 | 12 🟡 | 12 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 12 🟠 | 12 🟠 | 12 🟠 | 24 🟡 | 12 🟠 | 12 🟡 | 12 🟡 |
| `shoots/` | 6 🟡 | 6 🟡 | 4 🟡 | 4 🟡 | 24 🟠 | 24 🟠 | 4 🟢 | 6 🟡 | 6 🟡 | 6 🟡 | 12 🟡 | 6 🟡 | 6 🟡 | 6 🟡 |
| `shoots/SHOOT-2026-A/` | 6 🟡 | 6 🟡 | 6 🟡 | 9 🟠 | 36 🔴 | 36 🔴 | 12 🟠 | 9 🟠 | 3 🟢 | 9 🟠 | 18 🟠 | 9 🟠 | 9 🟠 | 9 🟠 |
| `shoots/SHOOT-2026-B/` | 3 🟡 | 3 🟡 | 3 🟡 | 9 🟠 | 27 🔴 | 27 🔴 | 18 🟠 | 9 🟠 | 9 🟠 | 9 🟠 | 18 🟠 | 9 🟠 | 9 🟠 | 9 🟠 |
| `clients/` | 12 🟠 | 4 🟡 | 8 🟠 | 12 🟠 | 36 🔴 | 36 🔴 | 16 🟠 | 12 🟠 | 12 🟠 | 12 🟠 | 24 🟠 | 12 🟠 | 12 🟠 | 4 🟡 |
| `invoices/` | 6 🟡 | 6 🟡 | 6 🟡 | 9 🟠 | 27 🔴 | 27 🔴 | 12 🟠 | 9 🟠 | 9 🟠 | 9 🟠 | 18 🟠 | 9 🟠 | 9 🟠 | 9 🟠 |
| `clients/citybank/` | 8 🟡 | 8 🟡 | 8 🟡 | 12 🟠 | 48 🔴 | 48 🔴 | 8 🟢 | 12 🟠 | 8 🟡 | 12 🟠 | 32 🟠 | 12 🟠 | 12 🟠 | 8 🟡 |
| `clients/neon_brand/` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟠 | 24 🔴 | 48 🔴 | 8 🟡 | 12 🟠 | 8 🟠 | 12 🟠 | 24 🟠 | 12 🟠 | 12 🟠 | 12 🟠 |
