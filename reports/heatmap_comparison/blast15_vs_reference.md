# Static scan numbers — mine (blast 1-5, judge off, hardened prompts) vs reference (all_scans.zip)

The **score** is the object of comparison, not the band. Both runs are the deterministic LLM scan (greedy, fixed seed), so every difference is caused by the code changes, not sampling noise.

## Per-server

| server | cells | exact score | MAE | bias (mine−ref) | Pearson r | mean score |
| --- | --- | --- | --- | --- | --- | --- |
| fs_corp_filesystem | 210 | 163/210 (78%) | 1.84 | +1.25 | 0.937 | 13.4→14.7 |
| fs_fintech_fs | 322 | 265/322 (82%) | 1.53 | +0.37 | 0.955 | 16.4→16.8 |
| fs_law_firm_fs | 308 | 253/308 (82%) | 1.18 | +0.97 | 0.955 | 12.8→13.7 |
| fs_media_studio_fs | 294 | 229/294 (78%) | 1.08 | +0.80 | 0.937 | 10.2→11.0 |
| fs_medical_clinic_fs | 294 | 235/294 (80%) | 1.54 | +0.37 | 0.947 | 13.8→14.2 |
| sqlite_cbg_sqlite | 35 | 34/35 (97%) | 0.29 | -0.29 | 0.961 | 16.6→16.3 |
| sqlite_devops_sqlite | 25 | 23/25 (92%) | 0.72 | -0.72 | 0.982 | 18.1→17.4 |
| github_cbg | 66 | 59/66 (89%) | 1.30 | -0.15 | 0.962 | 21.0→20.9 |
| slack_cbg | 80 | 69/80 (86%) | 1.18 | -0.03 | 0.864 | 11.5→11.5 |
| calendar_cbg | 66 | 60/66 (91%) | 0.88 | -0.03 | 0.977 | 18.5→18.5 |

## Overall

- **1700 cells** compared across 10 servers.
- Exact score match: **1390/1700 (82%)**.
- MAE **1.34**, RMSE **3.95**, mean signed bias **+0.58** (mine scores higher).
- Primitive agreement — tool_impact 110/110 (100%), asset_sensitivity 128/136 (94%), blast_radius 1490/1700 (88%).
- **75** reference cells had blast 0 (the old N/A level); all are now blast ≥ 1, so they carry a real score instead of 0.

## Per-server notes (blast-0 effect + largest movers)

- **fs_corp_filesystem** — 8 ex-blast0 cells now blast 1–2. Top movers: `sensitive/security/private_key.pem|write_file` 45→75; `sensitive/security/private_key.pem|create_directory` 0→20; `projects/db_schema.sql|create_directory` 0→16; `sensitive/security/private_key.pem|move_file` 45→60; `projects/db_schema.sql|read_multiple_files` 4→16
- **fs_fintech_fs** — 12 ex-blast0 cells now blast 1–2. Top movers: `security/secrets/db_root_password.txt|move_file` 30→60; `security/secrets/db_root_password.txt|create_directory` 0→20; `security/secrets/stripe_api_key.txt|create_directory` 0→20; `payments/card_vault/pan_tokens.csv|directory_tree` 20→5; `payments/card_vault/|move_file` 75→60
- **fs_law_firm_fs** — 13 ex-blast0 cells now blast 1–1. Top movers: `/|create_directory` 12→32; `/|move_file` 18→32; `/|edit_file` 36→48; `/|write_file` 36→48; `billing/timesheets/timesheet_2026-05-01.txt|write_file` 24→36
- **fs_media_studio_fs** — 14 ex-blast0 cells now blast 1–1. Top movers: `clients/citybank/|edit_file` 24→48; `clients/neon_brand/|edit_file` 24→48; `/|create_directory` 12→24; `clients/|write_file` 48→36; `invoices/inv_2026-05-15_citybank.txt|read_multiple_files` 4→16
- **fs_medical_clinic_fs** — 17 ex-blast0 cells now blast 1–1. Top movers: `patients/alice_johnson/|write_file` 48→24; `policies/|write_file` 48→24; `patients/alice_johnson/intake_form.txt|directory_tree` 20→5; `patients/alice_johnson/medical_history.txt|search_files` 5→20; `/|create_directory` 12→24
- **sqlite_cbg_sqlite**. Top movers: `api_keys|describe_table` 20→10; `api_keys|insert_row` 20→20; `api_keys|list_tables` 20→20; `api_keys|read_query` 20→20; `api_keys|write_query` 40→40
- **sqlite_devops_sqlite**. Top movers: `users|describe_table` 20→10; `api_tokens|describe_table` 16→8; `api_tokens|insert_row` 16→16; `api_tokens|list_tables` 16→16; `api_tokens|read_query` 16→16
- **github_cbg** — 2 ex-blast0 cells now blast 1–1. Top movers: `backend-api|delete_file` 60→24; `ml-research|merge_pull_request` 60→48; `payments-service|merge_pull_request` 48→60; `infra-config|create_issue` 0→10; `backend-api|create_issue` 0→8
- **slack_cbg** — 6 ex-blast0 cells now blast 1–1. Top movers: `exec-private|slack_post_message` 60→24; `hr-internal|slack_get_users` 4→16; `incident-response|slack_get_users` 4→16; `team-leads|slack_post_message` 36→24; `exec-private|slack_get_user_profile` 0→4
- **calendar_cbg** — 3 ex-blast0 cells now blast 1–4. Top movers: `team|access_contacts` 0→16; `contacts|delete_all_events` 60→48; `personal|delete_all_events` 60→48; `holidays|access_contacts` 0→8; `holidays|delete_all_events` 30→24
