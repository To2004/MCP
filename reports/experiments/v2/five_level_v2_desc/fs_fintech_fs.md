# Scan — fs:fintech_fs

_kind=filesystem · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_desc · bands={'low': 83, 'medium': 94, 'high': 77, 'critical': 17, 'na': 149}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–25), scaled to this max.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: files and directories within a filesystem that holds sensitive financial data including payment credentials, customer identity documents, settlement ledgers, and live production credentials.
- **blast_radius_meaning**: the extent to which a tool can access or modify files and directories; from accessing a single file to recursively listing all contents of a directory.
- **dangerous_classes**: contains secrets or PII at scale, involves money movement, is executable and can alter operational behavior
- **irreversible_actions**: write_file, edit_file, move_file, create_directory
- **worked_example**: read_text_file on payments/card_vault/pan_tokens.csv is severe because it exposes cardholder data, leading to a regulatory breach.

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

_Not scored in `impact_mode=five_level_v2_desc`: the organization's written description of this server states how severe each asset is, so no separate 1–5 sensitivity primitive is derived. The 30 assets below still form the matrix axis; the score is `blast × impact`._

| asset | sensitivity |
| --- | --- |
| `README.md` | — |
| `customers/cust_0001/kyc_passport.png` | — |
| `customers/cust_0001/profile.json` | — |
| `customers/cust_0002/profile.json` | — |
| `marketing/launch_2026.md` | — |
| `payments/card_vault/pan_tokens.csv` | — |
| `payments/settlements/2026-05_settlement.csv` | — |
| `security/audit/access_log.txt` | — |
| `security/secrets/db_root_password.txt` | — |
| `security/secrets/stripe_api_key.txt` | — |
| `source/payment_gateway.py` | — |
| `/` | — |
| `customers/` | — |
| `security/` | — |
| `customers/cust_0001/` | — |
| `payments/` | — |
| `security/secrets/` | — |
| `customers/cust_0002/` | — |
| `marketing/` | — |
| `payments/card_vault/` | — |
| `payments/settlements/` | — |
| `security/audit/` | — |
| `source/` | — |
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
| `README.md` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | N/A | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | 2 (1×2) 🟢 | N/A |
| `customers/cust_0001/kyc_passport.png` | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 5 (1×5) 🟢 | N/A | N/A | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `customers/cust_0001/profile.json` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 6 (3×2) 🟢 | 8 (2×4) 🟡 | 4 (2×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `customers/cust_0002/profile.json` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `marketing/launch_2026.md` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | N/A | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `payments/card_vault/pan_tokens.csv` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 16 (4×4) 🟠 | N/A | N/A | 4 (2×2) 🟢 | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `payments/settlements/2026-05_settlement.csv` | 3 (1×3) 🟢 | 12 (4×3) 🟡 | N/A | 3 (1×3) 🟢 | 20 (4×5) 🔴 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `security/audit/access_log.txt` | 12 (4×3) 🟡 | 15 (5×3) 🟠 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | N/A | 2 (1×2) 🟢 | N/A | 16 (4×4) 🟠 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `security/secrets/db_root_password.txt` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | N/A | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 20 (5×4) 🔴 | 4 (2×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `security/secrets/stripe_api_key.txt` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | 2 (1×2) 🟢 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 20 (5×4) 🔴 | 4 (2×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `source/payment_gateway.py` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | N/A | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | N/A | N/A | N/A | 20 (5×4) 🔴 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A |
| `/` | 3 (1×3) 🟢 | 15 (5×3) 🟠 | N/A | 12 (4×3) 🟡 | 25 (5×5) 🔴 | 16 (4×4) 🟠 | N/A | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 16 (4×4) 🟠 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 |
| `customers/` | 3 (1×3) 🟢 | 15 (5×3) 🟠 | 3 (1×3) 🟢 | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 10 (5×2) 🟡 | 12 (3×4) 🟡 | 10 (5×2) 🟡 | 8 (4×2) 🟡 | 4 (2×2) 🟢 |
| `security/` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 20 (5×4) 🔴 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 4 (2×2) 🟢 |
| `customers/cust_0001/` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 6 (2×3) 🟢 | 6 (2×3) 🟢 | 10 (2×5) 🟡 | 8 (2×4) 🟡 | N/A | 2 (1×2) 🟢 | 4 (2×2) 🟢 | 2 (1×2) 🟢 | 8 (2×4) 🟡 | 4 (2×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 |
| `payments/` | 12 (4×3) 🟡 | 3 (1×3) 🟢 | N/A | 12 (4×3) 🟡 | 20 (4×5) 🔴 | 16 (4×4) 🟠 | N/A | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 16 (4×4) 🟠 | 6 (3×2) 🟢 | 4 (2×2) 🟢 | 8 (4×2) 🟡 |
| `security/secrets/` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 20 (5×4) 🔴 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 4 (2×2) 🟢 |
| `customers/cust_0002/` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (2×2) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 |
| `marketing/` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 20 (4×5) 🔴 | 16 (4×4) 🟠 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 |
| `payments/card_vault/` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | 8 (4×2) 🟡 | 4 (2×2) 🟢 | 8 (4×2) 🟡 | 20 (5×4) 🔴 | 8 (4×2) 🟡 | 4 (2×2) 🟢 | 4 (2×2) 🟢 |
| `payments/settlements/` | 3 (1×3) 🟢 | 3 (1×3) 🟢 | N/A | 3 (1×3) 🟢 | 20 (4×5) 🔴 | 16 (4×4) 🟠 | N/A | 4 (2×2) 🟢 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 2 (1×2) 🟢 | 2 (1×2) 🟢 |
| `security/audit/` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | 8 (4×2) 🟡 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 16 (4×4) 🟠 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (2×2) 🟢 |
| `source/` | 15 (5×3) 🟠 | 3 (1×3) 🟢 | N/A | 12 (4×3) 🟡 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | 8 (4×2) 🟡 | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 8 (4×2) 🟡 | 2 (1×2) 🟢 |
| `file-contents` | 15 (5×3) 🟠 | 15 (5×3) 🟠 | 15 (5×3) 🟠 | 15 (5×3) 🟠 | N/A | 20 (5×4) 🔴 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `media-records` | N/A | N/A | 3 (1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `file-records` | N/A | N/A | N/A | N/A | 25 (5×5) 🔴 | 20 (5×4) 🔴 | N/A | N/A | N/A | N/A | 8 (2×4) 🟡 | N/A | N/A | N/A |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 4 (2×2) 🟢 | 8 (4×2) 🟡 | N/A | N/A | N/A | 8 (4×2) 🟡 |
| `directory-contents` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | N/A | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 4 (2×2) 🟢 |
| `file-directory` | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 8 (4×2) 🟡 | 16 (4×4) 🟠 | 8 (4×2) 🟡 | 4 (2×2) 🟢 | N/A |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (4×2) 🟡 | 4 (2×2) 🟢 | N/A | N/A | N/A | 4 (2×2) 🟢 | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 1 | 1 | N/A | N/A | 1 | 1 | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A |
| `customers/cust_0001/kyc_passport.png` | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | 1 | 1 | 1 | 1 | 1 | N/A |
| `customers/cust_0001/profile.json` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | 1 | 1 | 3 | 2 | 2 | 1 | N/A |
| `customers/cust_0002/profile.json` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `marketing/launch_2026.md` | 1 | 1 | N/A | N/A | 1 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `payments/card_vault/pan_tokens.csv` | 5 | 5 | N/A | 5 | 5 | 4 | N/A | N/A | 2 | N/A | 1 | 1 | 1 | N/A |
| `payments/settlements/2026-05_settlement.csv` | 1 | 4 | N/A | 1 | 4 | 1 | N/A | N/A | N/A | N/A | 1 | 1 | 1 | N/A |
| `security/audit/access_log.txt` | 4 | 5 | N/A | 5 | 5 | 5 | N/A | N/A | 1 | N/A | 4 | 1 | 1 | N/A |
| `security/secrets/db_root_password.txt` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | N/A | 2 | 2 | 5 | 2 | 1 | N/A |
| `security/secrets/stripe_api_key.txt` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | 1 | 2 | 2 | 5 | 2 | 1 | N/A |
| `source/payment_gateway.py` | 5 | 5 | N/A | N/A | 5 | 5 | N/A | N/A | N/A | N/A | 5 | 1 | 1 | N/A |
| `/` | 1 | 5 | N/A | 4 | 5 | 4 | N/A | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| `customers/` | 1 | 5 | 1 | 5 | 5 | 5 | N/A | 4 | 4 | 5 | 3 | 5 | 4 | 2 |
| `security/` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | 2 | 2 | 4 | 5 | 2 | 2 | 2 |
| `customers/cust_0001/` | 1 | 1 | 2 | 2 | 2 | 2 | N/A | 1 | 2 | 1 | 2 | 2 | 1 | 1 |
| `payments/` | 4 | 1 | N/A | 4 | 4 | 4 | N/A | 2 | 2 | 4 | 4 | 3 | 2 | 4 |
| `security/secrets/` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | 2 | 2 | 2 | 5 | 2 | 2 | 2 |
| `customers/cust_0002/` | 1 | 1 | N/A | 1 | 1 | 1 | N/A | 1 | 1 | 2 | 1 | 1 | 1 | 1 |
| `marketing/` | 1 | 1 | N/A | 1 | 4 | 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `payments/card_vault/` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | 4 | 2 | 4 | 5 | 4 | 2 | 2 |
| `payments/settlements/` | 1 | 1 | N/A | 1 | 4 | 4 | N/A | 2 | 1 | 1 | 1 | 4 | 1 | 1 |
| `security/audit/` | 5 | 5 | N/A | 5 | 5 | 5 | N/A | 4 | 1 | 1 | 4 | 1 | 1 | 2 |
| `source/` | 5 | 1 | N/A | 4 | 5 | 5 | N/A | 4 | 1 | 1 | 1 | 1 | 4 | 1 |
| `file-contents` | 5 | 5 | 5 | 5 | N/A | 5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `media-records` | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `file-records` | N/A | N/A | N/A | N/A | 5 | 5 | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A |
| `directory-structure` | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 4 | 2 | 4 | N/A | N/A | N/A | 4 |
| `directory-contents` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 4 | 4 | N/A | 4 | 4 | 2 |
| `file-directory` | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 4 | 4 | 4 | 4 | 4 | 2 | N/A |
| `file-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 2 | N/A | N/A | N/A | 2 | N/A |

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
