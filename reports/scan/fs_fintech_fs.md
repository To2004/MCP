# Scan — fs:fintech_fs

_kind=filesystem · provenance=llm-scan · model_reviewed=True · bands={'low': 54, 'medium': 95, 'high': 104, 'critical': 69}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: filesystem
- **asset_meaning**: Files and directories within the filesystem.
- **blast_radius_meaning**: The extent to which a tool can affect files or directories; from reading a single file (narrow touch) to modifying multiple files across different directories (severe action).
- **worked_example**: The 'write_file' tool paired with the 'payments/card_vault/pan_tokens.csv' asset is highly severe because it can overwrite sensitive payment information irreversibly.

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
| `customers/cust_0001/kyc_passport.png` | 4 |
| `customers/cust_0001/profile.json` | 4 |
| `customers/cust_0002/profile.json` | 4 |
| `marketing/launch_2026.md` | 3 |
| `payments/card_vault/pan_tokens.csv` | 5 |
| `payments/settlements/2026-05_settlement.csv` | 4 |
| `security/audit/access_log.txt` | 4 |
| `security/secrets/db_root_password.txt` | 5 |
| `security/secrets/stripe_api_key.txt` | 5 |
| `source/payment_gateway.py` | 4 |
| `/` | 4 |
| `customers/` | 5 |
| `security/` | 3 |
| `customers/cust_0001/` | 4 |
| `payments/` | 4 |
| `security/secrets/` | 5 |
| `customers/cust_0002/` | 4 |
| `marketing/` | 2 |
| `payments/card_vault/` | 5 |
| `payments/settlements/` | 4 |
| `security/audit/` | 3 |
| `source/` | 3 |

## Risk matrix (score · band)

| asset \ tool | read_file | read_text_file | read_media_file | read_multiple_files | write_file | edit_file | create_directory | list_directory | list_directory_with_sizes | directory_tree | move_file | search_files | get_file_info | list_allowed_directories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 12 🟡 | 0 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 18 🟠 | 2 🟢 | 2 🟢 | 0 🟢 |
| `customers/cust_0001/kyc_passport.png` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 24 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 36 🔴 | 4 🟠 | 4 🟢 | 0 🟢 |
| `customers/cust_0001/profile.json` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 36 🔴 | 4 🟠 | 4 🟢 | 4 🟢 |
| `customers/cust_0002/profile.json` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 48 🔴 | 4 🟠 | 4 🟢 | 4 🟢 |
| `marketing/launch_2026.md` | 3 🟡 | 3 🟡 | 3 🟢 | 3 🟠 | 18 🟠 | 18 🟠 | 0 🟢 | 3 🟡 | 3 🟡 | 3 🟠 | 27 🔴 | 3 🟡 | 3 🟢 | 3 🟢 |
| `payments/card_vault/pan_tokens.csv` | 10 🟡 | 10 🟡 | 5 🟢 | 10 🟠 | 60 🔴 | 45 🔴 | 0 🟢 | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 5 🟠 | 5 🟢 | 5 🟢 |
| `payments/settlements/2026-05_settlement.csv` | 4 🟡 | 4 🟡 | 4 🟢 | 12 🟠 | 48 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 48 🔴 | 4 🟠 | 4 🟢 | 4 🟢 |
| `security/audit/access_log.txt` | 4 🟡 | 4 🟡 | 4 🟡 | 8 🟠 | 24 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 36 🔴 | 4 🟠 | 4 🟢 | 4 🟢 |
| `security/secrets/db_root_password.txt` | 10 🔴 | 10 🔴 | 15 🔴 | 15 🔴 | 60 🔴 | 45 🔴 | 20 🟡 | 5 🟢 | 5 🟢 | 10 🟢 | 60 🔴 | 10 🔴 | 5 🟢 | 0 🟢 |
| `security/secrets/stripe_api_key.txt` | 10 🟠 | 10 🟠 | 15 🟠 | 15 🔴 | 60 🔴 | 45 🔴 | 20 🟡 | 15 🟠 | 5 🟡 | 10 🟠 | 60 🔴 | 10 🟠 | 5 🟢 | 10 🟠 |
| `source/payment_gateway.py` | 4 🟡 | 4 🟡 | 0 🟢 | 4 🟠 | 36 🔴 | 36 🔴 | 0 🟢 | 4 🟡 | 4 🟡 | 4 🟡 | 36 🔴 | 4 🟠 | 4 🟡 | 0 🟢 |
| `/` | 12 🟡 | 12 🟡 | 12 🟡 | 12 🟠 | 48 🔴 | 48 🔴 | 16 🟢 | 12 🟠 | 12 🟠 | 12 🟠 | 48 🔴 | 12 🟡 | 12 🟡 | 12 🟡 |
| `customers/` | 15 🟠 | 15 🟠 | 15 🟠 | 15 🟠 | 60 🔴 | 30 🟠 | 20 🟡 | 15 🟠 | 15 🟠 | 15 🟠 | 60 🔴 | 15 🟠 | 15 🟠 | 5 🟢 |
| `security/` | 9 🟡 | 9 🟡 | 9 🟡 | 9 🟠 | 27 🔴 | 27 🔴 | 12 🟡 | 9 🟠 | 9 🟠 | 9 🟠 | 36 🔴 | 9 🟠 | 9 🟠 | 3 🟢 |
| `customers/cust_0001/` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟠 | 48 🔴 | 48 🔴 | 16 🟡 | 12 🟠 | 12 🟠 | 12 🟠 | 48 🔴 | 12 🟠 | 12 🟠 | 12 🟠 |
| `payments/` | 8 🟡 | 12 🟠 | 8 🟡 | 8 🟠 | 36 🔴 | 36 🔴 | 8 🟢 | 12 🟠 | 8 🟡 | 12 🟠 | 48 🔴 | 8 🟡 | 12 🟠 | 8 🟡 |
| `security/secrets/` | 10 🟠 | 10 🟠 | 10 🟠 | 15 🔴 | 60 🔴 | 60 🔴 | 10 🟡 | 10 🟠 | 10 🟠 | 15 🔴 | 60 🔴 | 20 🔴 | 10 🟠 | 10 🟠 |
| `customers/cust_0002/` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟠 | 36 🔴 | 48 🔴 | 16 🟡 | 12 🟠 | 12 🟠 | 8 🟡 | 36 🔴 | 12 🟠 | 12 🟠 | 8 🟡 |
| `marketing/` | 6 🟢 | 4 🟢 | 4 🟢 | 6 🟡 | 18 🟠 | 12 🟠 | 8 🟡 | 6 🟡 | 6 🟡 | 6 🟡 | 18 🟠 | 6 🟡 | 6 🟢 | 6 🟢 |
| `payments/card_vault/` | 10 🟠 | 10 🟠 | 10 🟠 | 15 🟠 | 60 🔴 | 60 🔴 | 10 🟡 | 10 🟠 | 10 🟠 | 10 🟠 | 60 🔴 | 15 🟠 | 10 🟠 | 10 🟠 |
| `payments/settlements/` | 8 🟠 | 8 🟠 | 8 🟠 | 8 🟠 | 36 🔴 | 48 🔴 | 16 🟡 | 8 🟠 | 8 🟠 | 8 🟠 | 36 🔴 | 12 🟠 | 8 🟡 | 8 🟡 |
| `security/audit/` | 6 🟡 | 6 🟡 | 9 🟡 | 6 🟠 | 18 🔴 | 18 🔴 | 6 🟢 | 9 🟠 | 6 🟠 | 9 🟠 | 27 🔴 | 9 🟠 | 9 🟠 | 9 🟠 |
| `source/` | 6 🟡 | 6 🟡 | 6 🟡 | 9 🟠 | 27 🔴 | 36 🔴 | 12 🟡 | 9 🟠 | 9 🟠 | 9 🟠 | 36 🔴 | 9 🟠 | 9 🟠 | 6 🟡 |
