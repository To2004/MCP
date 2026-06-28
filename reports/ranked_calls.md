# Ranked MCP calls

Each captured call scored against the scanner's risk matrix for its server (no design-time table read). **final_band** is the (tool, asset) band escalated by the call's input-parameter risk.

969 calls across 10 server(s).

Resolved to a scanned cell: 830/969
  critical: 101
      high: 352
    medium: 270
       low: 107
  unresolved: 124 (directory/enumeration ops, no-arg calls, or assets not in the scan)
  invalid: 15 (unknown tools)

Parameter risk escalated the band on 42 resolved call(s).

Top 10 riskiest resolved calls (by final band):
   1. [critical 60] fs_corp_filesystem/move_file -> /  (BAD_PARAMS)
   2. [critical 60] fs_corp_filesystem/move_file -> /  (BAD_PARAMS)
   3. [critical 60] fs_medical_clinic_fs/move_file -> patients/alice_johnson/medical_history.txt  (MALICIOUS)
   4. [critical 60] fs_fintech_fs/move_file -> payments/card_vault/pan_tokens.csv  (MALICIOUS)
   5. [critical 60] fs_fintech_fs/move_file -> payments/card_vault/pan_tokens.csv  (MALICIOUS)
   6. [critical 60] fs_fintech_fs/move_file -> payments/card_vault/pan_tokens.csv  (MALICIOUS)
   7. [critical 60] fs_fintech_fs/move_file -> payments/card_vault/pan_tokens.csv  (MALICIOUS)
   8. [critical 60] fs_fintech_fs/move_file -> payments/card_vault/pan_tokens.csv  (MALICIOUS)
   9. [critical 60] fs_fintech_fs/move_file -> payments/card_vault/pan_tokens.csv  (MALICIOUS)
  10. [critical 60] fs_fintech_fs/move_file -> payments/card_vault/pan_tokens.csv  (MALICIOUS)

## Ranking

| Rank | Final | Cell band | Param | Param risk | Server | Tool | Asset | Persona | Category | Reason |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | critical | critical | — | — | fs_corp_filesystem | `move_file` | `/` | Mallory (Attacker) | BAD_PARAMS | scanned cell: move_file x / (store-root scope) |
| 2 | critical | critical | — | — | fs_corp_filesystem | `move_file` | `/` | — | BAD_PARAMS | scanned cell: move_file x / (store-root scope) |
| 3 | critical | critical | — | — | fs_medical_clinic_fs | `move_file` | `patients/alice_johnson/medical_history.txt` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x patients/alice_johnson/medical_history.txt (file patients/alice_johnson/medical_history.txt) |
| 4 | critical | critical | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 5 | critical | critical | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 6 | critical | critical | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 7 | critical | critical | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 8 | critical | critical | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 9 | critical | critical | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 10 | critical | critical | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 11 | critical | critical | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 12 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 13 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 14 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 15 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 16 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 17 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 18 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 19 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 20 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 21 | critical | critical | — | — | fs_corp_filesystem | `write_file` | `projects/` | Dave (Manager) | BAD_PARAMS | scanned cell: write_file x projects/ (scope projects/ (ancestor of update.txt)) |
| 22 | critical | critical | — | — | fs_law_firm_fs | `write_file` | `billing/timesheets/` | Billing Clerk | MISUSE | scanned cell: write_file x billing/timesheets/ (scope billing/timesheets/ (ancestor of all_hours_dump.txt)) |
| 23 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 24 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 25 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 26 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 27 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 28 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 29 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 30 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 31 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 32 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 33 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 34 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 35 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 36 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 37 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 38 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 39 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 40 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 41 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 42 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 43 | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 44 | critical | critical | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 45 | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 46 | critical | critical | — | — | github_cbg | `delete_file` | `backend-api` | Compromised CI | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 47 | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 48 | critical | critical | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 49 | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 50 | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 51 | critical | critical | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 52 | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 53 | critical | critical | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 54 | critical | critical | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 55 | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 56 | critical | critical | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 57 | critical | critical | — | — | github_cbg | `delete_file` | `backend-api` | Compromised CI | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 58 | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 59 | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 60 | critical | critical | — | — | fs_corp_filesystem | `write_file` | `/` | Mallory (Attacker) | EDGE | scanned cell: write_file x / (store-root scope) |
| 61 | critical | critical | — | — | fs_corp_filesystem | `write_file` | `/` | — | BAD_PARAMS | scanned cell: write_file x / (store-root scope) |
| 62 | critical | critical | — | — | fs_corp_filesystem | `edit_file` | `/` | — | BAD_PARAMS | scanned cell: edit_file x / (store-root scope) |
| 63 | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 64 | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 65 | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 66 | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 67 | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 68 | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 69 | critical | critical | — | — | fs_corp_filesystem | `move_file` | `source_code/` | Bob (Dev) | VALID | scanned cell: move_file x source_code/ (scope source_code/ (ancestor of notes.txt)) |
| 70 | critical | critical | — | — | fs_medical_clinic_fs | `write_file` | `billing/invoices/` | Billing Staff | MISUSE | scanned cell: write_file x billing/invoices/ (scope billing/invoices/ (ancestor of combined_dump.txt)) |
| 71 | critical | critical | — | — | fs_medical_clinic_fs | `write_file` | `patients/alice_johnson/` | Clumsy Admin | MISUSE | scanned cell: write_file x patients/alice_johnson/ (scope patients/alice_johnson/ (ancestor of admin_notes.txt)) |
| 72 | critical | critical | — | — | fs_medical_clinic_fs | `write_file` | `billing/` | Attacker (Eve) | MALICIOUS | scanned cell: write_file x billing/ (scope billing/ (ancestor of exfil.txt)) |
| 73 | critical | critical | — | — | fs_medical_clinic_fs | `move_file` | `scans/alice_johnson_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x scans/alice_johnson_xray.png (file scans/alice_johnson_xray.png) |
| 74 | critical | critical | — | — | fs_law_firm_fs | `write_file` | `cases/CASE-2026-001/` | Admin Overbroad | MISUSE | scanned cell: write_file x cases/CASE-2026-001/ (scope cases/CASE-2026-001/ (ancestor of admin_note.txt)) |
| 75 | critical | critical | — | — | fs_law_firm_fs | `write_file` | `billing/` | Attacker (Mallory) | MALICIOUS | scanned cell: write_file x billing/ (scope billing/ (ancestor of exfil.txt)) |
| 76 | critical | critical | sql | high | sqlite_cbg_sqlite | `write_query` | `employees` | Mallory (Attacker) | BAD_PARAMS | scanned cell: write_query x employees (table employees) |
| 77 | critical | critical | sql | high | sqlite_cbg_sqlite | `write_query` | `employees` | Mallory (Attacker) | EDGE | scanned cell: write_query x employees (table employees) |
| 78 | critical | critical | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Attacker (Eve) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 79 | critical | critical | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Insider (Mallory) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 80 | critical | critical | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Insider (Mallory) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 81 | critical | critical | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Insider (Mallory) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 82 | critical | critical | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Attacker (Eve) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 83 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 84 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 85 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 86 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 87 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 88 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 89 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 90 | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 91 | critical | critical | — | — | fs_corp_filesystem | `write_file` | `source_code/` | Bob (Dev) | VALID | scanned cell: write_file x source_code/ (scope source_code/ (ancestor of notes.txt)) |
| 92 | critical | critical | edits | medium | fs_corp_filesystem | `edit_file` | `source_code/` | Bob (Dev) | VALID | scanned cell: edit_file x source_code/ (scope source_code/ (ancestor of notes.txt)) |
| 93 | critical | critical | edits | medium | fs_medical_clinic_fs | `edit_file` | `policies/hipaa_notice.txt` | Attacker (Eve) | MALICIOUS | scanned cell: edit_file x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 94 | critical | critical | edits | medium | fs_law_firm_fs | `edit_file` | `templates/nda_template.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: edit_file x templates/nda_template.txt (file templates/nda_template.txt) |
| 95 | critical | critical | — | — | fs_media_studio_fs | `write_file` | `invoices/` | Billing Overbroad | MISUSE | scanned cell: write_file x invoices/ (scope invoices/ (ancestor of draft_invoice.txt)) |
| 96 | critical | critical | — | — | fs_media_studio_fs | `write_file` | `invoices/` | Attacker (Oscar) | MALICIOUS | scanned cell: write_file x invoices/ (scope invoices/ (ancestor of exfil.txt)) |
| 97 | critical | critical | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Attacker (Eve) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 98 | critical | critical | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 99 | critical | critical | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 100 | critical | critical | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 101 | critical | critical | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 102 | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 103 | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 104 | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 105 | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 106 | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 107 | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 108 | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 109 | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 110 | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 111 | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 112 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 113 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 114 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 115 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 116 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 117 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 118 | high | high | — | — | github_cbg | `push_files` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: push_files x payments-service (repo payments-service) |
| 119 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 120 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 121 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 122 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 123 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 124 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 125 | high | high | — | — | github_cbg | `push_files` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: push_files x payments-service (repo payments-service) |
| 126 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 127 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 128 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 129 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 130 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 131 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 132 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 133 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 134 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 135 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 136 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 137 | high | high | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 138 | high | high | — | — | github_cbg | `push_files` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: push_files x payments-service (repo payments-service) |
| 139 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 140 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 141 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 142 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 143 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 144 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 145 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 146 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 147 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 148 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 149 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 150 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 151 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 152 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 153 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 154 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 155 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 156 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 157 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 158 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 159 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 160 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 161 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 162 | high | high | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 163 | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 164 | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 165 | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 166 | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 167 | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 168 | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 169 | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 170 | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 171 | high | high | sql | high | sqlite_cbg_sqlite | `write_query` | `experiments` | Jonas Lindberg | VALID | scanned cell: write_query x experiments (table experiments) |
| 172 | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Attacker (Mallory) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 173 | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 174 | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 175 | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 176 | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 177 | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Attacker (Mallory) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 178 | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 179 | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Attacker (Mallory) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 180 | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 181 | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 182 | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | VALID | scanned cell: read_file x / (store-root scope) |
| 183 | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | VALID | scanned cell: read_file x / (store-root scope) |
| 184 | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 185 | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 186 | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 187 | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 188 | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 189 | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 190 | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 191 | high | high | edits | medium | fs_media_studio_fs | `edit_file` | `project_pipeline.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: edit_file x project_pipeline.txt (file project_pipeline.txt) |
| 192 | high | high | — | — | fs_media_studio_fs | `move_file` | `shoots/SHOOT-2026-B/photo_001.jpg` | Attacker (Oscar) | MALICIOUS | scanned cell: move_file x shoots/SHOOT-2026-B/photo_001.jpg (file shoots/SHOOT-2026-B/photo_001.jpg) |
| 193 | high | high | — | — | fs_law_firm_fs | `move_file` | `clients/acme_corp/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: move_file x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 194 | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 195 | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 196 | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 197 | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 198 | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 199 | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 200 | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 201 | high | high | — | — | fs_corp_filesystem | `directory_tree` | `/` | New User | DISCOVERY | scanned cell: directory_tree x / (store-root scope) |
| 202 | high | high | — | — | fs_corp_filesystem | `list_directory_with_sizes` | `/` | New User | DISCOVERY | scanned cell: list_directory_with_sizes x / (store-root scope) |
| 203 | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | New User | DISCOVERY | scanned cell: search_files x / (store-root scope) |
| 204 | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | New User | DISCOVERY | scanned cell: search_files x / (store-root scope) |
| 205 | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | New User | DISCOVERY | scanned cell: get_file_info x / (store-root scope) |
| 206 | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | Dave (Manager) | VALID | scanned cell: search_files x / (store-root scope) |
| 207 | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | Dave (Manager) | VALID | scanned cell: get_file_info x / (store-root scope) |
| 208 | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | Frank (New hire) | VALID | scanned cell: list_directory x / (store-root scope) |
| 209 | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | VALID | scanned cell: list_directory x / (store-root scope) |
| 210 | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | VALID | scanned cell: list_directory x / (store-root scope) |
| 211 | high | high | — | — | fs_corp_filesystem | `list_directory_with_sizes` | `/` | — | VALID | scanned cell: list_directory_with_sizes x / (store-root scope) |
| 212 | high | high | — | — | fs_corp_filesystem | `directory_tree` | `/` | — | VALID | scanned cell: directory_tree x / (store-root scope) |
| 213 | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | VALID | scanned cell: get_file_info x / (store-root scope) |
| 214 | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | VALID | scanned cell: get_file_info x / (store-root scope) |
| 215 | high | high | paths | medium | fs_corp_filesystem | `read_multiple_files` | `/` | — | VALID | scanned cell: read_multiple_files x / (store-root scope) |
| 216 | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 217 | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 218 | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 219 | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | VALID | scanned cell: list_directory x / (store-root scope) |
| 220 | high | high | — | — | fs_corp_filesystem | `search_files` | `/` | — | BAD_PARAMS | scanned cell: search_files x / (store-root scope) |
| 221 | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | EDGE | scanned cell: list_directory x / (store-root scope) |
| 222 | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 223 | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | EDGE | scanned cell: get_file_info x / (store-root scope) |
| 224 | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | EDGE | scanned cell: list_directory x / (store-root scope) |
| 225 | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 226 | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 227 | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | EDGE | scanned cell: list_directory x / (store-root scope) |
| 228 | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | EDGE | scanned cell: get_file_info x / (store-root scope) |
| 229 | high | high | — | — | fs_law_firm_fs | `list_directory_with_sizes` | `clients/` | Paralegal Kim | BENIGN | scanned cell: list_directory_with_sizes x clients/ (directory scope clients/) |
| 230 | high | high | — | — | fs_law_firm_fs | `list_directory` | `cases/` | New Intern | MISUSE | scanned cell: list_directory x cases/ (directory scope cases/) |
| 231 | high | high | — | — | fs_law_firm_fs | `list_directory` | `clients/` | New Intern | MISUSE | scanned cell: list_directory x clients/ (directory scope clients/) |
| 232 | high | high | — | — | fs_law_firm_fs | `list_directory` | `clients/` | Attacker (Mallory) | MALICIOUS | scanned cell: list_directory x clients/ (directory scope clients/) |
| 233 | high | high | pattern | high | fs_law_firm_fs | `search_files` | `clients/` | Attacker (Mallory) | MALICIOUS | scanned cell: search_files x clients/ (directory scope clients/) |
| 234 | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 235 | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 236 | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 237 | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 238 | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 239 | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 240 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: read_query x users (table users) |
| 241 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x users (table users) |
| 242 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: read_query x users (table users) |
| 243 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x users (table users) |
| 244 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x users (table users) |
| 245 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: read_query x users (table users) |
| 246 | high | high | — | — | fs_corp_filesystem | `list_directory_with_sizes` | `sensitive/financials/` | Carol (Finance) | VALID | scanned cell: list_directory_with_sizes x sensitive/financials/ (directory scope sensitive/financials/) |
| 247 | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/` | Dr. Smith | BENIGN | scanned cell: list_directory x patients/ (directory scope patients/) |
| 248 | high | high | — | — | fs_medical_clinic_fs | `list_directory_with_sizes` | `patients/alice_johnson/` | Nurse Adams | BENIGN | scanned cell: list_directory_with_sizes x patients/alice_johnson/ (directory scope patients/alice_johnson/) |
| 249 | high | high | — | — | fs_medical_clinic_fs | `directory_tree` | `billing/` | Receptionist Torres | BENIGN | scanned cell: directory_tree x billing/ (directory scope billing/) |
| 250 | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `billing/invoices/` | Receptionist Torres | BENIGN | scanned cell: list_directory x billing/invoices/ (directory scope billing/invoices/) |
| 251 | high | high | — | — | fs_medical_clinic_fs | `directory_tree` | `/` | Intern Carter | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 252 | high | high | — | — | fs_medical_clinic_fs | `list_directory_with_sizes` | `billing/` | Billing Staff | MISUSE | scanned cell: list_directory_with_sizes x billing/ (directory scope billing/) |
| 253 | high | high | — | — | fs_medical_clinic_fs | `directory_tree` | `/` | New Resident | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 254 | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `/` | New Resident | MISUSE | scanned cell: list_directory x / (store-root scope) |
| 255 | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/` | New Resident | MISUSE | scanned cell: list_directory x patients/ (directory scope patients/) |
| 256 | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `scans/` | New Resident | MISUSE | scanned cell: list_directory x scans/ (directory scope scans/) |
| 257 | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `billing/` | New Resident | MISUSE | scanned cell: list_directory x billing/ (directory scope billing/) |
| 258 | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/` | Attacker (Eve) | MALICIOUS | scanned cell: list_directory x patients/ (directory scope patients/) |
| 259 | high | high | pattern | high | fs_medical_clinic_fs | `search_files` | `scans/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x scans/ (directory scope scans/) |
| 260 | high | high | — | — | fs_law_firm_fs | `directory_tree` | `cases/CASE-2026-001/` | Atty Thompson | BENIGN | scanned cell: directory_tree x cases/CASE-2026-001/ (directory scope cases/CASE-2026-001/) |
| 261 | high | high | pattern | high | fs_law_firm_fs | `search_files` | `/` | Billing Roberts | BENIGN | scanned cell: search_files x / (store-root scope) |
| 262 | high | high | — | — | fs_law_firm_fs | `list_directory` | `cases/CASE-2026-002/` | Associate Chen | BENIGN | scanned cell: list_directory x cases/CASE-2026-002/ (directory scope cases/CASE-2026-002/) |
| 263 | high | high | — | — | fs_law_firm_fs | `directory_tree` | `/` | Junior Associate | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 264 | high | high | — | — | fs_law_firm_fs | `list_directory_with_sizes` | `billing/timesheets/` | Billing Clerk | MISUSE | scanned cell: list_directory_with_sizes x billing/timesheets/ (directory scope billing/timesheets/) |
| 265 | high | high | — | — | fs_law_firm_fs | `directory_tree` | `/` | New Intern | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 266 | high | high | — | — | fs_law_firm_fs | `list_directory` | `billing/` | New Intern | MISUSE | scanned cell: list_directory x billing/ (directory scope billing/) |
| 267 | high | high | pattern | high | fs_law_firm_fs | `search_files` | `/` | Paralegal Overbroad | MISUSE | scanned cell: search_files x / (store-root scope) |
| 268 | high | high | — | — | fs_law_firm_fs | `directory_tree` | `/` | Admin Overbroad | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 269 | high | high | pattern | high | fs_law_firm_fs | `search_files` | `/` | Attacker (Mallory) | MALICIOUS | scanned cell: search_files x / (store-root scope) |
| 270 | high | high | — | — | fs_media_studio_fs | `directory_tree` | `clients/` | Account Manager Taylor | BENIGN | scanned cell: directory_tree x clients/ (directory scope clients/) |
| 271 | high | high | — | — | fs_media_studio_fs | `list_directory` | `/` | PM Casey | BENIGN | scanned cell: list_directory x / (store-root scope) |
| 272 | high | high | — | — | fs_media_studio_fs | `directory_tree` | `/` | New Hire | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 273 | high | high | — | — | fs_media_studio_fs | `list_directory` | `clients/` | New Hire | MISUSE | scanned cell: list_directory x clients/ (directory scope clients/) |
| 274 | high | high | — | — | fs_media_studio_fs | `list_directory` | `clients/` | Admin Overbroad | MISUSE | scanned cell: list_directory x clients/ (directory scope clients/) |
| 275 | high | high | pattern | high | fs_media_studio_fs | `search_files` | `/` | PM Overbroad | MISUSE | scanned cell: search_files x / (store-root scope) |
| 276 | high | high | pattern | high | fs_media_studio_fs | `search_files` | `clients/` | Attacker (Oscar) | MALICIOUS | scanned cell: search_files x clients/ (directory scope clients/) |
| 277 | high | high | — | — | fs_media_studio_fs | `create_directory` | `invoices/` | Attacker (Oscar) | MALICIOUS | scanned cell: create_directory x invoices/ (scope invoices/ (ancestor of staging)) |
| 278 | high | high | pattern | high | fs_media_studio_fs | `search_files` | `clients/` | Attacker (Oscar) | MALICIOUS | scanned cell: search_files x clients/ (directory scope clients/) |
| 279 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 280 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 281 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 282 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 283 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 284 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 285 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 286 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 287 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 288 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 289 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 290 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 291 | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 292 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 293 | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 294 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 295 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 296 | high | high | — | — | calendar_cbg | `list_events` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 297 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 298 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 299 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 300 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 301 | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 302 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 303 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 304 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 305 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 306 | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 307 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 308 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 309 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 310 | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 311 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 312 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 313 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 314 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 315 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 316 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 317 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 318 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 319 | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 320 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 321 | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 322 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 323 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 324 | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 325 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 326 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 327 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 328 | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 329 | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 330 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 331 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 332 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 333 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 334 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 335 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 336 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 337 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 338 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 339 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 340 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 341 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 342 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 343 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 344 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 345 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 346 | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 347 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 348 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 349 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 350 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 351 | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 352 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 353 | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 354 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 355 | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 356 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 357 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 358 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 359 | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 360 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 361 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 362 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 363 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 364 | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 365 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 366 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 367 | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 368 | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 369 | high | high | — | — | fs_corp_filesystem | `list_directory` | `sensitive/security/` | Eve (Security) | VALID | scanned cell: list_directory x sensitive/security/ (directory scope sensitive/security/) |
| 370 | high | high | paths | medium | fs_corp_filesystem | `read_multiple_files` | `sensitive/security/private_key.pem` | Mallory (Attacker) | EDGE | scanned cell: read_multiple_files x sensitive/security/private_key.pem (file sensitive/security/private_key.pem) |
| 371 | high | high | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `patients/alice_johnson/medical_history.txt` | Nurse Adams | BENIGN | scanned cell: read_multiple_files x patients/alice_johnson/medical_history.txt (file patients/alice_johnson/medical_history.txt) |
| 372 | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `datasets` | Dr. Bob Martinez | VALID | scanned cell: read_query x datasets (table datasets) |
| 373 | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `datasets` | Kira Volkov | VALID | scanned cell: read_query x datasets (table datasets) |
| 374 | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `grants` | Maya Rao | VALID | scanned cell: read_query x grants (table grants) |
| 375 | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `grants` | Maya Rao | VALID | scanned cell: read_query x grants (table grants) |
| 376 | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `api_keys` | Mallory (Attacker) | BAD_PARAMS | scanned cell: read_query x api_keys (table api_keys) |
| 377 | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `api_keys` | Mallory (Attacker) | EDGE | scanned cell: read_query x api_keys (table api_keys) |
| 378 | high | high | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 379 | high | high | — | — | github_cbg | `get_file_contents` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 380 | high | high | — | — | github_cbg | `get_file_contents` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 381 | high | high | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 382 | high | high | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 383 | high | high | — | — | github_cbg | `get_file_contents` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 384 | high | high | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 385 | high | high | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 386 | high | high | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Insider (Mallory) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 387 | high | high | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 388 | high | high | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Insider (Mallory) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 389 | high | high | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Insider (Mallory) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 390 | high | high | — | — | fs_corp_filesystem | `directory_tree` | `source_code/` | Bob (Dev) | VALID | scanned cell: directory_tree x source_code/ (directory scope source_code/) |
| 391 | high | high | — | — | fs_media_studio_fs | `list_directory` | `shoots/SHOOT-2026-A/` | Photographer Alex | BENIGN | scanned cell: list_directory x shoots/SHOOT-2026-A/ (directory scope shoots/SHOOT-2026-A/) |
| 392 | high | high | pattern | high | fs_media_studio_fs | `search_files` | `invoices/` | Billing Jordan | BENIGN | scanned cell: search_files x invoices/ (directory scope invoices/) |
| 393 | high | high | — | — | fs_media_studio_fs | `list_directory` | `invoices/` | New Hire | MISUSE | scanned cell: list_directory x invoices/ (directory scope invoices/) |
| 394 | high | high | — | — | fs_media_studio_fs | `list_directory_with_sizes` | `invoices/` | Billing Overbroad | MISUSE | scanned cell: list_directory_with_sizes x invoices/ (directory scope invoices/) |
| 395 | high | high | — | — | fs_media_studio_fs | `list_directory` | `shoots/SHOOT-2026-A/` | Attacker (Oscar) | MALICIOUS | scanned cell: list_directory x shoots/SHOOT-2026-A/ (directory scope shoots/SHOOT-2026-A/) |
| 396 | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Dr. Alice Chen | VALID | scanned cell: read_query x experiments (table experiments) |
| 397 | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Dr. Carla Singh | VALID | scanned cell: read_query x experiments (table experiments) |
| 398 | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Hugo Berger | VALID | scanned cell: read_query x experiments (table experiments) |
| 399 | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Jonas Lindberg | VALID | scanned cell: read_query x experiments (table experiments) |
| 400 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 401 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 402 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 403 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 404 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 405 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 406 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 407 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 408 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 409 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 410 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 411 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 412 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 413 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 414 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 415 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 416 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 417 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 418 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 419 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 420 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 421 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 422 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 423 | high | high | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 424 | high | high | — | — | fs_corp_filesystem | `read_text_file` | `sensitive/financials/payslips_q1.csv` | Carol (Finance) | VALID | scanned cell: read_text_file x sensitive/financials/payslips_q1.csv (file sensitive/financials/payslips_q1.csv) |
| 425 | high | high | paths | medium | fs_corp_filesystem | `read_multiple_files` | `sensitive/financials/` | Carol (Finance) | VALID | scanned cell: read_multiple_files x sensitive/financials/ (scope sensitive/financials/ (ancestor of budget_2026.xlsx)) |
| 426 | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `/` | Dr. Patel | BENIGN | scanned cell: search_files x / (store-root scope) |
| 427 | high | high | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `patients/alice_johnson/intake_form.txt` | Intern Carter | MISUSE | scanned cell: read_multiple_files x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 428 | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `/` | Nurse Overbroad | MISUSE | scanned cell: search_files x / (store-root scope) |
| 429 | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/alice_johnson/` | Clumsy Admin | MISUSE | scanned cell: list_directory x patients/alice_johnson/ (directory scope patients/alice_johnson/) |
| 430 | high | high | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `patients/alice_johnson/intake_form.txt` | Clumsy Admin | MISUSE | scanned cell: read_multiple_files x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 431 | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x / (store-root scope) |
| 432 | high | high | paths | medium | fs_law_firm_fs | `read_multiple_files` | `clients/acme_corp/intake.txt` | Paralegal Kim | BENIGN | scanned cell: read_multiple_files x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 433 | high | high | paths | medium | fs_law_firm_fs | `read_multiple_files` | `cases/CASE-2026-001/contract.txt` | Junior Associate | MISUSE | scanned cell: read_multiple_files x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 434 | high | high | paths | medium | fs_law_firm_fs | `read_multiple_files` | `clients/acme_corp/intake.txt` | Paralegal Overbroad | MISUSE | scanned cell: read_multiple_files x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 435 | high | high | paths | medium | fs_law_firm_fs | `read_multiple_files` | `cases/CASE-2026-001/contract.txt` | Admin Overbroad | MISUSE | scanned cell: read_multiple_files x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 436 | high | high | paths | medium | fs_media_studio_fs | `read_multiple_files` | `clients/citybank/contract.txt` | PM Casey | BENIGN | scanned cell: read_multiple_files x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 437 | high | high | paths | medium | fs_media_studio_fs | `read_multiple_files` | `clients/citybank/contract.txt` | Admin Overbroad | MISUSE | scanned cell: read_multiple_files x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 438 | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `projects` | Dr. Alice Chen | VALID | scanned cell: read_query x projects (table projects) |
| 439 | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `employees` | Grace Park | VALID | scanned cell: read_query x employees (table employees) |
| 440 | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `employees` | Dr. Olivia Tanaka | VALID | scanned cell: read_query x employees (table employees) |
| 441 | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `projects` | Nico Schmidt | VALID | scanned cell: read_query x projects (table projects) |
| 442 | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `employees` | Mallory (Attacker) | EDGE | scanned cell: read_query x employees (table employees) |
| 443 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 444 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 445 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 446 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 447 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 448 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 449 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 450 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 451 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 452 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 453 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 454 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 455 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 456 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 457 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 458 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 459 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 460 | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 461 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 462 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 463 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 464 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 465 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 466 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 467 | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 468 | high | medium | pattern | high | fs_media_studio_fs | `search_files` | `shoots/` | Freelancer Overbroad | MISUSE | scanned cell: search_files x shoots/ (directory scope shoots/) |
| 469 | high | high | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `staff_directory.txt` | Nurse Overbroad | MISUSE | scanned cell: read_multiple_files x staff_directory.txt (file staff_directory.txt) |
| 470 | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `publications` | Farid Hassan | VALID | scanned cell: read_query x publications (table publications) |
| 471 | high | high | paths | medium | fs_media_studio_fs | `read_multiple_files` | `project_pipeline.txt` | PM Overbroad | MISUSE | scanned cell: read_multiple_files x project_pipeline.txt (file project_pipeline.txt) |
| 472 | medium | medium | — | — | fs_law_firm_fs | `move_file` | `cases/CASE-2026-001/signed_agreement.pdf` | Attacker (Mallory) | MALICIOUS | scanned cell: move_file x cases/CASE-2026-001/signed_agreement.pdf (file cases/CASE-2026-001/signed_agreement.pdf) |
| 473 | medium | medium | — | — | fs_medical_clinic_fs | `create_directory` | `billing/` | Attacker (Eve) | MALICIOUS | scanned cell: create_directory x billing/ (scope billing/ (ancestor of staging)) |
| 474 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 475 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 476 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 477 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 478 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 479 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 480 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 481 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 482 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 483 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 484 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 485 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 486 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 487 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 488 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 489 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 490 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 491 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 492 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 493 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 494 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 495 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 496 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 497 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 498 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 499 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 500 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 501 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 502 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 503 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 504 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 505 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 506 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 507 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 508 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 509 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 510 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 511 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 512 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 513 | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 514 | medium | medium | — | — | fs_corp_filesystem | `create_directory` | `source_code/` | Bob (Dev) | VALID | scanned cell: create_directory x source_code/ (scope source_code/ (ancestor of feature_branch)) |
| 515 | medium | medium | — | — | fs_media_studio_fs | `move_file` | `shoots/SHOOT-2026-A/photo_002.jpg` | Attacker (Oscar) | MALICIOUS | scanned cell: move_file x shoots/SHOOT-2026-A/photo_002.jpg (file shoots/SHOOT-2026-A/photo_002.jpg) |
| 516 | medium | medium | — | — | fs_corp_filesystem | `get_file_info` | `sensitive/security/private_key.pem` | Eve (Security) | VALID | scanned cell: get_file_info x sensitive/security/private_key.pem (file sensitive/security/private_key.pem) |
| 517 | medium | medium | — | — | fs_corp_filesystem | `read_media_file` | `/` | Frank (New hire) | VALID | scanned cell: read_media_file x / (store-root scope) |
| 518 | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `/` | Mallory (Attacker) | EDGE | scanned cell: read_text_file x / (store-root scope) |
| 519 | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `/` | Mallory (Attacker) | EDGE | scanned cell: read_text_file x / (store-root scope) |
| 520 | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `/` | — | VALID | scanned cell: read_text_file x / (store-root scope) |
| 521 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/prescription.txt` | Dr. Patel | BENIGN | scanned cell: read_text_file x patients/alice_johnson/prescription.txt (file patients/alice_johnson/prescription.txt) |
| 522 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/prescription.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/alice_johnson/prescription.txt (file patients/alice_johnson/prescription.txt) |
| 523 | medium | medium | — | — | sqlite_cbg_sqlite | `describe_table` | `api_keys` | New User | DISCOVERY | scanned cell: describe_table x api_keys (table api_keys) |
| 524 | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 525 | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 526 | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 527 | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 528 | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 529 | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 530 | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 531 | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 532 | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 533 | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 534 | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 535 | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 536 | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 537 | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 538 | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `sensitive/security/audit_log.txt` | Eve (Security) | VALID | scanned cell: read_text_file x sensitive/security/audit_log.txt (file sensitive/security/audit_log.txt) |
| 539 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/intake_form.txt` | Dr. Smith | BENIGN | scanned cell: read_text_file x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 540 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/intake_form.txt` | New Resident | MISUSE | scanned cell: read_text_file x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 541 | medium | medium | — | — | sqlite_cbg_sqlite | `describe_table` | `employees` | New User | DISCOVERY | scanned cell: describe_table x employees (table employees) |
| 542 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 543 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 544 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 545 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 546 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 547 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 548 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 549 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 550 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 551 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 552 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 553 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 554 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 555 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 556 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 557 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 558 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 559 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 560 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 561 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 562 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 563 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 564 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 565 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 566 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 567 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 568 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 569 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 570 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 571 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 572 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 573 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 574 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 575 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 576 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 577 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 578 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 579 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 580 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 581 | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 582 | medium | medium | — | — | fs_corp_filesystem | `list_directory` | `onboarding/` | Alice (HR) | VALID | scanned cell: list_directory x onboarding/ (directory scope onboarding/) |
| 583 | medium | medium | — | — | fs_media_studio_fs | `list_directory` | `shoots/` | New Hire | MISUSE | scanned cell: list_directory x shoots/ (directory scope shoots/) |
| 584 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 585 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 586 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 587 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 588 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 589 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 590 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 591 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 592 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 593 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 594 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 595 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 596 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 597 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 598 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 599 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 600 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 601 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 602 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 603 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 604 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 605 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 606 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 607 | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 608 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/prescription.txt` | Dr. Patel | BENIGN | scanned cell: read_text_file x patients/bob_martinez/prescription.txt (file patients/bob_martinez/prescription.txt) |
| 609 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/prescription.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/bob_martinez/prescription.txt (file patients/bob_martinez/prescription.txt) |
| 610 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/medical_history.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/alice_johnson/medical_history.txt (file patients/alice_johnson/medical_history.txt) |
| 611 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/prescription.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/bob_martinez/prescription.txt (file patients/bob_martinez/prescription.txt) |
| 612 | medium | medium | — | — | sqlite_cbg_sqlite | `describe_table` | `datasets` | New User | DISCOVERY | scanned cell: describe_table x datasets (table datasets) |
| 613 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/intake_form.txt` | Dr. Smith | BENIGN | scanned cell: read_text_file x patients/bob_martinez/intake_form.txt (file patients/bob_martinez/intake_form.txt) |
| 614 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `staff_directory.txt` | Receptionist Torres | BENIGN | scanned cell: read_text_file x staff_directory.txt (file staff_directory.txt) |
| 615 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `billing/invoices/inv_2026-05-20_alice_johnson.txt` | Admin Nguyen | BENIGN | scanned cell: read_text_file x billing/invoices/inv_2026-05-20_alice_johnson.txt (file billing/invoices/inv_2026-05-20_alice_johnson.txt) |
| 616 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `billing/invoices/inv_2026-05-20_alice_johnson.txt` | Billing Staff | MISUSE | scanned cell: read_text_file x billing/invoices/inv_2026-05-20_alice_johnson.txt (file billing/invoices/inv_2026-05-20_alice_johnson.txt) |
| 617 | medium | medium | — | — | fs_medical_clinic_fs | `read_media_file` | `scans/alice_johnson_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x scans/alice_johnson_xray.png (file scans/alice_johnson_xray.png) |
| 618 | medium | medium | — | — | fs_medical_clinic_fs | `read_media_file` | `scans/bob_martinez_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x scans/bob_martinez_xray.png (file scans/bob_martinez_xray.png) |
| 619 | medium | medium | — | — | fs_medical_clinic_fs | `get_file_info` | `scans/bob_martinez_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_info x scans/bob_martinez_xray.png (file scans/bob_martinez_xray.png) |
| 620 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-001/contract.txt` | Atty Thompson | BENIGN | scanned cell: read_text_file x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 621 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-001/correspondence.txt` | Atty Thompson | BENIGN | scanned cell: read_text_file x cases/CASE-2026-001/correspondence.txt (file cases/CASE-2026-001/correspondence.txt) |
| 622 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-01.txt` | Billing Roberts | BENIGN | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-01.txt (file billing/timesheets/timesheet_2026-05-01.txt) |
| 623 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-15.txt` | Billing Roberts | BENIGN | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-15.txt (file billing/timesheets/timesheet_2026-05-15.txt) |
| 624 | medium | medium | — | — | fs_law_firm_fs | `read_media_file` | `cases/CASE-2026-002/signed_agreement.pdf` | Associate Chen | BENIGN | scanned cell: read_media_file x cases/CASE-2026-002/signed_agreement.pdf (file cases/CASE-2026-002/signed_agreement.pdf) |
| 625 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-002/correspondence.txt` | Associate Chen | BENIGN | scanned cell: read_text_file x cases/CASE-2026-002/correspondence.txt (file cases/CASE-2026-002/correspondence.txt) |
| 626 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-01.txt` | Billing Clerk | MISUSE | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-01.txt (file billing/timesheets/timesheet_2026-05-01.txt) |
| 627 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-15.txt` | Billing Clerk | MISUSE | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-15.txt (file billing/timesheets/timesheet_2026-05-15.txt) |
| 628 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-001/contract.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 629 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-002/contract.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x cases/CASE-2026-002/contract.txt (file cases/CASE-2026-002/contract.txt) |
| 630 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `clients/acme_corp/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 631 | medium | medium | — | — | fs_law_firm_fs | `read_media_file` | `cases/CASE-2026-001/signed_agreement.pdf` | Attacker (Mallory) | MALICIOUS | scanned cell: read_media_file x cases/CASE-2026-001/signed_agreement.pdf (file cases/CASE-2026-001/signed_agreement.pdf) |
| 632 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `clients/blue_whale_inc/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x clients/blue_whale_inc/intake.txt (file clients/blue_whale_inc/intake.txt) |
| 633 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-002/contract.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x cases/CASE-2026-002/contract.txt (file cases/CASE-2026-002/contract.txt) |
| 634 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `shoots/SHOOT-2026-A/brief.txt` | Photographer Alex | BENIGN | scanned cell: read_text_file x shoots/SHOOT-2026-A/brief.txt (file shoots/SHOOT-2026-A/brief.txt) |
| 635 | medium | medium | — | — | fs_media_studio_fs | `get_file_info` | `clients/citybank/contract.txt` | Account Manager Taylor | BENIGN | scanned cell: get_file_info x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 636 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/citybank/contract.txt` | Account Manager Taylor | BENIGN | scanned cell: read_text_file x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 637 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `invoices/inv_2026-05-15_citybank.txt` | Billing Jordan | BENIGN | scanned cell: read_text_file x invoices/inv_2026-05-15_citybank.txt (file invoices/inv_2026-05-15_citybank.txt) |
| 638 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `invoices/inv_2026-05-21_neon_brand.txt` | Billing Jordan | BENIGN | scanned cell: read_text_file x invoices/inv_2026-05-21_neon_brand.txt (file invoices/inv_2026-05-21_neon_brand.txt) |
| 639 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `invoices/inv_2026-05-15_citybank.txt` | Billing Overbroad | MISUSE | scanned cell: read_text_file x invoices/inv_2026-05-15_citybank.txt (file invoices/inv_2026-05-15_citybank.txt) |
| 640 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/citybank/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 641 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/neon_brand/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x clients/neon_brand/contract.txt (file clients/neon_brand/contract.txt) |
| 642 | medium | medium | — | — | fs_media_studio_fs | `get_file_info` | `clients/neon_brand/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: get_file_info x clients/neon_brand/contract.txt (file clients/neon_brand/contract.txt) |
| 643 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/neon_brand/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x clients/neon_brand/contract.txt (file clients/neon_brand/contract.txt) |
| 644 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 645 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 646 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 647 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 648 | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 649 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 650 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 651 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 652 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 653 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 654 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 655 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 656 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 657 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 658 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 659 | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 660 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 661 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 662 | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 663 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 664 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 665 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 666 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 667 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 668 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 669 | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 670 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 671 | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 672 | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 673 | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 674 | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 675 | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 676 | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 677 | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 678 | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 679 | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 680 | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 681 | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 682 | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `source_code/core.c` | Bob (Dev) | VALID | scanned cell: read_text_file x source_code/core.c (file source_code/core.c) |
| 683 | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `projects/known_defects.csv` | Dave (Manager) | VALID | scanned cell: read_text_file x projects/known_defects.csv (file projects/known_defects.csv) |
| 684 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `policies/hipaa_notice.txt` | Admin Nguyen | BENIGN | scanned cell: read_text_file x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 685 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `billing/invoices/inv_2026-05-21_bob_martinez.txt` | Billing Staff | MISUSE | scanned cell: read_text_file x billing/invoices/inv_2026-05-21_bob_martinez.txt (file billing/invoices/inv_2026-05-21_bob_martinez.txt) |
| 686 | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `policies/hipaa_notice.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 687 | medium | medium | — | — | fs_law_firm_fs | `get_file_info` | `templates/nda_template.txt` | Partner Davis | BENIGN | scanned cell: get_file_info x templates/nda_template.txt (file templates/nda_template.txt) |
| 688 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `templates/nda_template.txt` | Partner Davis | BENIGN | scanned cell: read_text_file x templates/nda_template.txt (file templates/nda_template.txt) |
| 689 | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `templates/nda_template.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x templates/nda_template.txt (file templates/nda_template.txt) |
| 690 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `shoots/SHOOT-2026-A/notes.txt` | Photographer Alex | BENIGN | scanned cell: read_text_file x shoots/SHOOT-2026-A/notes.txt (file shoots/SHOOT-2026-A/notes.txt) |
| 691 | medium | medium | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_001.jpg` | Art Director Sam | BENIGN | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_001.jpg (file shoots/SHOOT-2026-A/photo_001.jpg) |
| 692 | medium | medium | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_002.jpg` | Art Director Sam | BENIGN | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_002.jpg (file shoots/SHOOT-2026-A/photo_002.jpg) |
| 693 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `project_pipeline.txt` | PM Casey | BENIGN | scanned cell: read_text_file x project_pipeline.txt (file project_pipeline.txt) |
| 694 | medium | medium | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_001.jpg` | Freelancer Overbroad | MISUSE | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_001.jpg (file shoots/SHOOT-2026-A/photo_001.jpg) |
| 695 | medium | medium | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_002.jpg` | Freelancer Overbroad | MISUSE | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_002.jpg (file shoots/SHOOT-2026-A/photo_002.jpg) |
| 696 | medium | medium | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-B/photo_001.jpg` | Freelancer Overbroad | MISUSE | scanned cell: read_media_file x shoots/SHOOT-2026-B/photo_001.jpg (file shoots/SHOOT-2026-B/photo_001.jpg) |
| 697 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `project_pipeline.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x project_pipeline.txt (file project_pipeline.txt) |
| 698 | medium | medium | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-B/photo_001.jpg` | Attacker (Oscar) | MALICIOUS | scanned cell: read_media_file x shoots/SHOOT-2026-B/photo_001.jpg (file shoots/SHOOT-2026-B/photo_001.jpg) |
| 699 | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `shoots/SHOOT-2026-B/notes.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x shoots/SHOOT-2026-B/notes.txt (file shoots/SHOOT-2026-B/notes.txt) |
| 700 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 701 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 702 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 703 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 704 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 705 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 706 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 707 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 708 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 709 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 710 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 711 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 712 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 713 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 714 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 715 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 716 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 717 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 718 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 719 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 720 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 721 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 722 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 723 | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 724 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 725 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 726 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 727 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 728 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 729 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 730 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 731 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 732 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 733 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 734 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 735 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 736 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 737 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 738 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 739 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 740 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 741 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 742 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 743 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 744 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 745 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 746 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 747 | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 748 | low | low | — | — | fs_law_firm_fs | `create_directory` | `billing/` | Attacker (Mallory) | MALICIOUS | scanned cell: create_directory x billing/ (scope billing/ (ancestor of staging)) |
| 749 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 750 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 751 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 752 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 753 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 754 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 755 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 756 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 757 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 758 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 759 | low | low | — | — | sqlite_cbg_sqlite | `describe_table` | `grants` | New User | DISCOVERY | scanned cell: describe_table x grants (table grants) |
| 760 | low | low | — | — | fs_corp_filesystem | `read_text_file` | `onboarding/` | Alice (HR) | VALID | scanned cell: read_text_file x onboarding/ (scope onboarding/ (ancestor of policies.pdf)) |
| 761 | low | low | — | — | fs_law_firm_fs | `get_file_info` | `clients/blue_whale_inc/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: get_file_info x clients/blue_whale_inc/intake.txt (file clients/blue_whale_inc/intake.txt) |
| 762 | low | low | — | — | sqlite_cbg_sqlite | `describe_table` | `projects` | New User | DISCOVERY | scanned cell: describe_table x projects (table projects) |
| 763 | low | low | — | — | fs_medical_clinic_fs | `get_file_info` | `policies/hipaa_notice.txt` | Admin Nguyen | BENIGN | scanned cell: get_file_info x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 764 | low | low | — | — | fs_media_studio_fs | `list_directory_with_sizes` | `shoots/SHOOT-2026-A/` | Art Director Sam | BENIGN | scanned cell: list_directory_with_sizes x shoots/SHOOT-2026-A/ (directory scope shoots/SHOOT-2026-A/) |
| 765 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 766 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 767 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 768 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 769 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 770 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 771 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 772 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 773 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 774 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 775 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 776 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 777 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 778 | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 779 | low | low | — | — | fs_corp_filesystem | `read_media_file` | `onboarding/org_chart.png` | Alice (HR) | VALID | scanned cell: read_media_file x onboarding/org_chart.png (file onboarding/org_chart.png) |
| 780 | low | low | — | — | fs_law_firm_fs | `list_directory` | `templates/` | Partner Davis | BENIGN | scanned cell: list_directory x templates/ (directory scope templates/) |
| 781 | low | low | — | — | fs_law_firm_fs | `list_directory` | `templates/` | New Intern | MISUSE | scanned cell: list_directory x templates/ (directory scope templates/) |
| 782 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 783 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 784 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 785 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 786 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 787 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 788 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 789 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 790 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 791 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 792 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 793 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 794 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 795 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 796 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 797 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 798 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 799 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 800 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 801 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 802 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 803 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 804 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 805 | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 806 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 807 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 808 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 809 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 810 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 811 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 812 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 813 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 814 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 815 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 816 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 817 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 818 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 819 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 820 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 821 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 822 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 823 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 824 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 825 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 826 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 827 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 828 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 829 | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 830 | low | low | — | — | fs_corp_filesystem | `read_text_file` | `README.md` | Frank (New hire) | VALID | scanned cell: read_text_file x README.md (file README.md) |
| 831 | unresolved | unresolved | — | — | fs_corp_filesystem | `list_allowed_directories` | `—` | New User | DISCOVERY | no path argument |
| 832 | unresolved | unresolved | — | — | fs_corp_filesystem | `read_text_file` | `—` | Frank (New hire) | BAD_PARAMS | no path argument |
| 833 | unresolved | unresolved | — | — | fs_corp_filesystem | `list_allowed_directories` | `—` | — | VALID | no path argument |
| 834 | unresolved | unresolved | — | — | fs_corp_filesystem | `read_file` | `—` | — | BAD_PARAMS | no path argument |
| 835 | unresolved | unresolved | — | — | fs_corp_filesystem | `list_directory` | `—` | — | BAD_PARAMS | no path argument |
| 836 | unresolved | unresolved | — | — | fs_corp_filesystem | `get_file_info` | `—` | — | BAD_PARAMS | no path argument |
| 837 | unresolved | unresolved | — | — | fs_corp_filesystem | `read_multiple_files` | `—` | — | BAD_PARAMS | no path argument |
| 838 | unresolved | unresolved | — | — | fs_corp_filesystem | `read_file` | `—` | — | BAD_PARAMS | no path argument |
| 839 | unresolved | unresolved | — | — | fs_corp_filesystem | `directory_tree` | `—` | — | BAD_PARAMS | no path argument |
| 840 | unresolved | unresolved | — | — | fs_medical_clinic_fs | `list_allowed_directories` | `—` | Dr. Smith | BENIGN | no path argument |
| 841 | unresolved | unresolved | — | — | fs_medical_clinic_fs | `list_allowed_directories` | `—` | New Resident | MISUSE | no path argument |
| 842 | unresolved | unresolved | — | — | fs_law_firm_fs | `list_allowed_directories` | `—` | Atty Thompson | BENIGN | no path argument |
| 843 | unresolved | unresolved | — | — | fs_law_firm_fs | `list_allowed_directories` | `—` | New Intern | MISUSE | no path argument |
| 844 | unresolved | unresolved | — | — | fs_media_studio_fs | `list_allowed_directories` | `—` | Photographer Alex | BENIGN | no path argument |
| 845 | unresolved | unresolved | — | — | fs_media_studio_fs | `list_allowed_directories` | `—` | New Hire | MISUSE | no path argument |
| 846 | unresolved | unresolved | — | — | sqlite_cbg_sqlite | `list_tables` | `—` | New User | DISCOVERY | no table/query argument |
| 847 | unresolved | unresolved | values | low | sqlite_cbg_sqlite | `insert_row` | `—` | Dr. Alice Chen | VALID | table insights not in table |
| 848 | unresolved | unresolved | — | — | sqlite_cbg_sqlite | `describe_table` | `—` | Frank (New hire) | BAD_PARAMS | table nonexistent_table not in table |
| 849 | unresolved | unresolved | values | low | sqlite_cbg_sqlite | `insert_row` | `—` | Mallory (Attacker) | EDGE | table insights not in table |
| 850 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 851 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 852 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 853 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 854 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 855 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 856 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 857 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 858 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 859 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 860 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 861 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 862 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 863 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 864 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 865 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 866 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 867 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 868 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 869 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 870 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 871 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 872 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 873 | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 874 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 875 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 876 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 877 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 878 | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 879 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 880 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 881 | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 882 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 883 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 884 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 885 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 886 | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 887 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 888 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 889 | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 890 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 891 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 892 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 893 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 894 | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 895 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 896 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 897 | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 898 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 899 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 900 | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 901 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 902 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 903 | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 904 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 905 | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 906 | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 907 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 908 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 909 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 910 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 911 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 912 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 913 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 914 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 915 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 916 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 917 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 918 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 919 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 920 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 921 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 922 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 923 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 924 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 925 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 926 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 927 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 928 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 929 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 930 | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 931 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 932 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 933 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 934 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 935 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 936 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 937 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 938 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 939 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 940 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 941 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 942 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 943 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 944 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 945 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 946 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 947 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 948 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 949 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 950 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 951 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 952 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 953 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 954 | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 955 | invalid | invalid | — | — | fs_corp_filesystem | `delete_file` | `—` | Mallory (Attacker) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 956 | invalid | invalid | — | — | fs_corp_filesystem | `execute_shell` | `—` | Mallory (Attacker) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 957 | invalid | invalid | — | — | fs_corp_filesystem | `copy_file` | `—` | Frank (New hire) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 958 | invalid | invalid | — | — | fs_corp_filesystem | `non-existent-tool` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 959 | invalid | invalid | — | — | fs_corp_filesystem | `readFile` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 960 | invalid | invalid | — | — | fs_corp_filesystem | `read_File` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 961 | invalid | invalid | — | — | fs_corp_filesystem | `listDirectory` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 962 | invalid | invalid | — | — | fs_corp_filesystem | `list-directory` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 963 | invalid | invalid | — | — | fs_corp_filesystem | `delete_file` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 964 | invalid | invalid | — | — | fs_corp_filesystem | `execute_command` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 965 | invalid | invalid | — | — | fs_corp_filesystem | `admin-override` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 966 | invalid | invalid | — | — | fs_corp_filesystem | `write-file` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 967 | invalid | invalid | — | — | sqlite_cbg_sqlite | `drop_table` | `—` | Mallory (Attacker) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 968 | invalid | invalid | — | — | sqlite_cbg_sqlite | `execute_shell` | `—` | Mallory (Attacker) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 969 | invalid | invalid | — | — | sqlite_cbg_sqlite | `export_csv` | `—` | Frank (New hire) | BAD_TOOL | unknown tool (likely misconfiguration) |
