# Ranked MCP calls

Each captured call scored against the scanner's risk matrix for its server (no design-time table read). Ranking is by **final_score** — the cell score amplified by the call's input-parameter risk (`score x param_multiplier`). Bands are shown for visualization only.

969 calls across 10 server(s).

Resolved to a scanned cell: 830/969
  critical: 46
      high: 345
    medium: 315
       low: 124
  unresolved: 124 (directory/enumeration ops, no-arg calls, or assets not in the scan)
  invalid: 15 (unknown tools)

Parameter risk amplified the score on 166 resolved call(s).

Top 10 riskiest resolved calls (by final score):
   1. [120] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 60 x2 via sql)  [critical]
   2. [120] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 60 x2 via sql)  [critical]
   3. [120] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 60 x2 via sql)  [critical]
   4. [120] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 60 x2 via sql)  [critical]
   5. [120] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 60 x2 via sql)  [critical]
   6. [120] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 60 x2 via sql)  [critical]
   7. [120] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 60 x2 via sql)  [critical]
   8. [120] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 60 x2 via sql)  [critical]
   9. [120] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 60 x2 via sql)  [critical]
  10. [72] fs_corp_filesystem/edit_file -> source_code/  (VALID) (cell 48 x1.5 via edits)  [critical]

## Ranking

| Rank | Final score | Cell score | Param x | Final band | Cell band | Param | Param risk | Server | Tool | Asset | Persona | Category | Reason |
| ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 120 | 60 | 2x | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 2 | 120 | 60 | 2x | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 3 | 120 | 60 | 2x | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 4 | 120 | 60 | 2x | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 5 | 120 | 60 | 2x | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 6 | 120 | 60 | 2x | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 7 | 120 | 60 | 2x | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 8 | 120 | 60 | 2x | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 9 | 120 | 60 | 2x | critical | critical | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 10 | 72 | 48 | 1.5x | critical | critical | edits | medium | fs_corp_filesystem | `edit_file` | `source_code/` | Bob (Dev) | VALID | scanned cell: edit_file x source_code/ (scope source_code/ (ancestor of notes.txt)) |
| 11 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 12 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 13 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 14 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 15 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 16 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 17 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 18 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 19 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 20 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 21 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 22 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 23 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 24 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 25 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 26 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 27 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 28 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 29 | 60 | 60 | 1x | critical | critical | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 30 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 31 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 32 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 33 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 34 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 35 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 36 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 37 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 38 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 39 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 40 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 41 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 42 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 43 | 60 | 60 | 1x | critical | critical | — | — | github_cbg | `merge_pull_request` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 44 | 48 | 48 | 1x | critical | critical | — | — | fs_corp_filesystem | `move_file` | `source_code/` | Bob (Dev) | VALID | scanned cell: move_file x source_code/ (scope source_code/ (ancestor of notes.txt)) |
| 45 | 48 | 48 | 1x | critical | critical | — | — | fs_corp_filesystem | `write_file` | `projects/` | Dave (Manager) | BAD_PARAMS | scanned cell: write_file x projects/ (scope projects/ (ancestor of update.txt)) |
| 46 | 48 | 48 | 1x | critical | critical | — | — | fs_corp_filesystem | `move_file` | `/` | Mallory (Attacker) | BAD_PARAMS | scanned cell: move_file x / (store-root scope) |
| 47 | 48 | 48 | 1x | critical | critical | — | — | fs_corp_filesystem | `write_file` | `/` | Mallory (Attacker) | EDGE | scanned cell: write_file x / (store-root scope) |
| 48 | 48 | 48 | 1x | critical | critical | — | — | fs_corp_filesystem | `write_file` | `/` | — | BAD_PARAMS | scanned cell: write_file x / (store-root scope) |
| 49 | 48 | 48 | 1x | critical | critical | — | — | fs_corp_filesystem | `move_file` | `/` | — | BAD_PARAMS | scanned cell: move_file x / (store-root scope) |
| 50 | 48 | 48 | 1x | critical | critical | — | — | fs_corp_filesystem | `edit_file` | `/` | — | BAD_PARAMS | scanned cell: edit_file x / (store-root scope) |
| 51 | 48 | 48 | 1x | critical | critical | — | — | fs_medical_clinic_fs | `write_file` | `billing/invoices/` | Billing Staff | MISUSE | scanned cell: write_file x billing/invoices/ (scope billing/invoices/ (ancestor of combined_dump.txt)) |
| 52 | 48 | 48 | 1x | critical | critical | — | — | fs_medical_clinic_fs | `write_file` | `billing/` | Attacker (Eve) | MALICIOUS | scanned cell: write_file x billing/ (scope billing/ (ancestor of exfil.txt)) |
| 53 | 48 | 48 | 1x | critical | critical | — | — | fs_law_firm_fs | `write_file` | `billing/timesheets/` | Billing Clerk | MISUSE | scanned cell: write_file x billing/timesheets/ (scope billing/timesheets/ (ancestor of all_hours_dump.txt)) |
| 54 | 48 | 48 | 1x | critical | critical | — | — | fs_law_firm_fs | `write_file` | `billing/` | Attacker (Mallory) | MALICIOUS | scanned cell: write_file x billing/ (scope billing/ (ancestor of exfil.txt)) |
| 55 | 48 | 24 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `write_query` | `employees` | Mallory (Attacker) | BAD_PARAMS | scanned cell: write_query x employees (table employees) |
| 56 | 48 | 24 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `write_query` | `employees` | Mallory (Attacker) | EDGE | scanned cell: write_query x employees (table employees) |
| 57 | 40 | 20 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `api_keys` | Mallory (Attacker) | BAD_PARAMS | scanned cell: read_query x api_keys (table api_keys) |
| 58 | 40 | 20 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `api_keys` | Mallory (Attacker) | EDGE | scanned cell: read_query x api_keys (table api_keys) |
| 59 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: read_query x users (table users) |
| 60 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x users (table users) |
| 61 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: read_query x users (table users) |
| 62 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x users (table users) |
| 63 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x users (table users) |
| 64 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: read_query x users (table users) |
| 65 | 36 | 36 | 1x | high | high | — | — | fs_law_firm_fs | `write_file` | `cases/CASE-2026-001/` | Admin Overbroad | MISUSE | scanned cell: write_file x cases/CASE-2026-001/ (scope cases/CASE-2026-001/ (ancestor of admin_note.txt)) |
| 66 | 36 | 36 | 1x | high | high | — | — | fs_media_studio_fs | `write_file` | `invoices/` | Billing Overbroad | MISUSE | scanned cell: write_file x invoices/ (scope invoices/ (ancestor of draft_invoice.txt)) |
| 67 | 36 | 36 | 1x | high | high | — | — | fs_media_studio_fs | `write_file` | `invoices/` | Attacker (Oscar) | MALICIOUS | scanned cell: write_file x invoices/ (scope invoices/ (ancestor of exfil.txt)) |
| 68 | 36 | 36 | 1x | high | high | — | — | github_cbg | `push_files` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: push_files x payments-service (repo payments-service) |
| 69 | 36 | 36 | 1x | high | high | — | — | github_cbg | `push_files` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: push_files x payments-service (repo payments-service) |
| 70 | 36 | 36 | 1x | high | high | — | — | github_cbg | `push_files` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: push_files x payments-service (repo payments-service) |
| 71 | 36 | 24 | 1.5x | high | high | edits | medium | fs_medical_clinic_fs | `edit_file` | `policies/hipaa_notice.txt` | Attacker (Eve) | MALICIOUS | scanned cell: edit_file x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 72 | 36 | 24 | 1.5x | high | high | edits | medium | fs_law_firm_fs | `edit_file` | `templates/nda_template.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: edit_file x templates/nda_template.txt (file templates/nda_template.txt) |
| 73 | 36 | 18 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `write_query` | `experiments` | Jonas Lindberg | VALID | scanned cell: write_query x experiments (table experiments) |
| 74 | 32 | 16 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | New User | DISCOVERY | scanned cell: search_files x / (store-root scope) |
| 75 | 32 | 16 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | New User | DISCOVERY | scanned cell: search_files x / (store-root scope) |
| 76 | 32 | 16 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | Dave (Manager) | VALID | scanned cell: search_files x / (store-root scope) |
| 77 | 32 | 16 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 78 | 32 | 16 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 79 | 32 | 16 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 80 | 32 | 16 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 81 | 32 | 16 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 82 | 32 | 16 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 83 | 32 | 16 | 2x | high | high | pattern | high | fs_law_firm_fs | `search_files` | `/` | Billing Roberts | BENIGN | scanned cell: search_files x / (store-root scope) |
| 84 | 32 | 16 | 2x | high | high | pattern | high | fs_law_firm_fs | `search_files` | `/` | Paralegal Overbroad | MISUSE | scanned cell: search_files x / (store-root scope) |
| 85 | 32 | 16 | 2x | high | high | pattern | high | fs_law_firm_fs | `search_files` | `/` | Attacker (Mallory) | MALICIOUS | scanned cell: search_files x / (store-root scope) |
| 86 | 32 | 16 | 2x | high | high | pattern | high | fs_law_firm_fs | `search_files` | `clients/` | Attacker (Mallory) | MALICIOUS | scanned cell: search_files x clients/ (directory scope clients/) |
| 87 | 32 | 16 | 2x | high | high | pattern | high | fs_media_studio_fs | `search_files` | `invoices/` | Billing Jordan | BENIGN | scanned cell: search_files x invoices/ (directory scope invoices/) |
| 88 | 32 | 16 | 2x | high | high | pattern | high | fs_media_studio_fs | `search_files` | `clients/` | Attacker (Oscar) | MALICIOUS | scanned cell: search_files x clients/ (directory scope clients/) |
| 89 | 32 | 16 | 2x | high | high | pattern | high | fs_media_studio_fs | `search_files` | `clients/` | Attacker (Oscar) | MALICIOUS | scanned cell: search_files x clients/ (directory scope clients/) |
| 90 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `projects` | Dr. Alice Chen | VALID | scanned cell: read_query x projects (table projects) |
| 91 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `datasets` | Dr. Bob Martinez | VALID | scanned cell: read_query x datasets (table datasets) |
| 92 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `employees` | Grace Park | VALID | scanned cell: read_query x employees (table employees) |
| 93 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `datasets` | Kira Volkov | VALID | scanned cell: read_query x datasets (table datasets) |
| 94 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `grants` | Maya Rao | VALID | scanned cell: read_query x grants (table grants) |
| 95 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `grants` | Maya Rao | VALID | scanned cell: read_query x grants (table grants) |
| 96 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `employees` | Dr. Olivia Tanaka | VALID | scanned cell: read_query x employees (table employees) |
| 97 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `projects` | Nico Schmidt | VALID | scanned cell: read_query x projects (table projects) |
| 98 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `employees` | Mallory (Attacker) | EDGE | scanned cell: read_query x employees (table employees) |
| 99 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 100 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 101 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 102 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 103 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 104 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 105 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 106 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 107 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 108 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 109 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 110 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 111 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 112 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 113 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 114 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 115 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 116 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 117 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 118 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 119 | 30 | 30 | 1x | high | high | — | — | fs_medical_clinic_fs | `move_file` | `patients/alice_johnson/medical_history.txt` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x patients/alice_johnson/medical_history.txt (file patients/alice_johnson/medical_history.txt) |
| 120 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 121 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 122 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 123 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 124 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 125 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 126 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 127 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 128 | 30 | 20 | 1.5x | high | high | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `patients/alice_johnson/medical_history.txt` | Nurse Adams | BENIGN | scanned cell: read_multiple_files x patients/alice_johnson/medical_history.txt (file patients/alice_johnson/medical_history.txt) |
| 129 | 30 | 20 | 1.5x | high | high | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `patients/alice_johnson/intake_form.txt` | Intern Carter | MISUSE | scanned cell: read_multiple_files x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 130 | 30 | 20 | 1.5x | high | high | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `patients/alice_johnson/intake_form.txt` | Clumsy Admin | MISUSE | scanned cell: read_multiple_files x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 131 | 27 | 18 | 1.5x | high | high | edits | medium | fs_media_studio_fs | `edit_file` | `project_pipeline.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: edit_file x project_pipeline.txt (file project_pipeline.txt) |
| 132 | 25 | 25 | 1x | high | high | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Attacker (Eve) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 133 | 25 | 25 | 1x | high | high | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 134 | 25 | 25 | 1x | high | high | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 135 | 25 | 25 | 1x | high | high | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 136 | 25 | 25 | 1x | high | high | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 137 | 24 | 24 | 1x | high | high | — | — | fs_corp_filesystem | `write_file` | `source_code/` | Bob (Dev) | VALID | scanned cell: write_file x source_code/ (scope source_code/ (ancestor of notes.txt)) |
| 138 | 24 | 24 | 1x | high | high | — | — | fs_medical_clinic_fs | `write_file` | `patients/alice_johnson/` | Clumsy Admin | MISUSE | scanned cell: write_file x patients/alice_johnson/ (scope patients/alice_johnson/ (ancestor of admin_notes.txt)) |
| 139 | 24 | 24 | 1x | high | high | — | — | fs_medical_clinic_fs | `move_file` | `scans/alice_johnson_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x scans/alice_johnson_xray.png (file scans/alice_johnson_xray.png) |
| 140 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 141 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 142 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 143 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 144 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 145 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 146 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 147 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 148 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 149 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 150 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 151 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 152 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 153 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 154 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 155 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 156 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 157 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 158 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 159 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 160 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 161 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Compromised CI | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 162 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 163 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 164 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 165 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 166 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 167 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Compromised CI | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 168 | 24 | 24 | 1x | high | high | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Attacker (Eve) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 169 | 24 | 24 | 1x | high | high | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Insider (Mallory) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 170 | 24 | 24 | 1x | high | high | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Insider (Mallory) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 171 | 24 | 24 | 1x | high | high | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Insider (Mallory) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 172 | 24 | 24 | 1x | high | high | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Attacker (Eve) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 173 | 24 | 16 | 1.5x | high | high | paths | medium | fs_corp_filesystem | `read_multiple_files` | `sensitive/financials/` | Carol (Finance) | VALID | scanned cell: read_multiple_files x sensitive/financials/ (scope sensitive/financials/ (ancestor of budget_2026.xlsx)) |
| 174 | 24 | 16 | 1.5x | high | high | paths | medium | fs_corp_filesystem | `read_multiple_files` | `/` | — | VALID | scanned cell: read_multiple_files x / (store-root scope) |
| 175 | 24 | 16 | 1.5x | high | high | paths | medium | fs_law_firm_fs | `read_multiple_files` | `cases/CASE-2026-001/contract.txt` | Junior Associate | MISUSE | scanned cell: read_multiple_files x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 176 | 24 | 16 | 1.5x | high | high | paths | medium | fs_law_firm_fs | `read_multiple_files` | `cases/CASE-2026-001/contract.txt` | Admin Overbroad | MISUSE | scanned cell: read_multiple_files x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 177 | 24 | 16 | 1.5x | high | high | paths | medium | fs_media_studio_fs | `read_multiple_files` | `clients/citybank/contract.txt` | PM Casey | BENIGN | scanned cell: read_multiple_files x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 178 | 24 | 16 | 1.5x | high | high | paths | medium | fs_media_studio_fs | `read_multiple_files` | `clients/citybank/contract.txt` | Admin Overbroad | MISUSE | scanned cell: read_multiple_files x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 179 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 180 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 181 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 182 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 183 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 184 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 185 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 186 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 187 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 188 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 189 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 190 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 191 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 192 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 193 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 194 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 195 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 196 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 197 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 198 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 199 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 200 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 201 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 202 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 203 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 204 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 205 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 206 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 207 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 208 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 209 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 210 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 211 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 212 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 213 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 214 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 215 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 216 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 217 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 218 | 24 | 16 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 219 | 24 | 12 | 2x | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `/` | Dr. Patel | BENIGN | scanned cell: search_files x / (store-root scope) |
| 220 | 24 | 12 | 2x | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `/` | Nurse Overbroad | MISUSE | scanned cell: search_files x / (store-root scope) |
| 221 | 24 | 12 | 2x | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x / (store-root scope) |
| 222 | 24 | 12 | 2x | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `scans/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x scans/ (directory scope scans/) |
| 223 | 24 | 12 | 2x | high | medium | pattern | high | fs_media_studio_fs | `search_files` | `/` | PM Overbroad | MISUSE | scanned cell: search_files x / (store-root scope) |
| 224 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Dr. Alice Chen | VALID | scanned cell: read_query x experiments (table experiments) |
| 225 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Dr. Carla Singh | VALID | scanned cell: read_query x experiments (table experiments) |
| 226 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Hugo Berger | VALID | scanned cell: read_query x experiments (table experiments) |
| 227 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Jonas Lindberg | VALID | scanned cell: read_query x experiments (table experiments) |
| 228 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `directory_tree` | `/` | New User | DISCOVERY | scanned cell: directory_tree x / (store-root scope) |
| 229 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory_with_sizes` | `/` | New User | DISCOVERY | scanned cell: list_directory_with_sizes x / (store-root scope) |
| 230 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | New User | DISCOVERY | scanned cell: get_file_info x / (store-root scope) |
| 231 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `directory_tree` | `source_code/` | Bob (Dev) | VALID | scanned cell: directory_tree x source_code/ (directory scope source_code/) |
| 232 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory_with_sizes` | `sensitive/financials/` | Carol (Finance) | VALID | scanned cell: list_directory_with_sizes x sensitive/financials/ (directory scope sensitive/financials/) |
| 233 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | Dave (Manager) | VALID | scanned cell: get_file_info x / (store-root scope) |
| 234 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `sensitive/security/` | Eve (Security) | VALID | scanned cell: list_directory x sensitive/security/ (directory scope sensitive/security/) |
| 235 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | Frank (New hire) | VALID | scanned cell: list_directory x / (store-root scope) |
| 236 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_media_file` | `/` | Frank (New hire) | VALID | scanned cell: read_media_file x / (store-root scope) |
| 237 | 16 | 16 | 1x | medium | medium | — | — | fs_corp_filesystem | `create_directory` | `source_code/` | Bob (Dev) | VALID | scanned cell: create_directory x source_code/ (scope source_code/ (ancestor of feature_branch)) |
| 238 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_text_file` | `/` | Mallory (Attacker) | EDGE | scanned cell: read_text_file x / (store-root scope) |
| 239 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_text_file` | `/` | Mallory (Attacker) | EDGE | scanned cell: read_text_file x / (store-root scope) |
| 240 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | VALID | scanned cell: list_directory x / (store-root scope) |
| 241 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | VALID | scanned cell: list_directory x / (store-root scope) |
| 242 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory_with_sizes` | `/` | — | VALID | scanned cell: list_directory_with_sizes x / (store-root scope) |
| 243 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `directory_tree` | `/` | — | VALID | scanned cell: directory_tree x / (store-root scope) |
| 244 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | VALID | scanned cell: get_file_info x / (store-root scope) |
| 245 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | VALID | scanned cell: get_file_info x / (store-root scope) |
| 246 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | VALID | scanned cell: read_file x / (store-root scope) |
| 247 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_text_file` | `/` | — | VALID | scanned cell: read_text_file x / (store-root scope) |
| 248 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | VALID | scanned cell: read_file x / (store-root scope) |
| 249 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | VALID | scanned cell: list_directory x / (store-root scope) |
| 250 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `search_files` | `/` | — | BAD_PARAMS | scanned cell: search_files x / (store-root scope) |
| 251 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 252 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 253 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | EDGE | scanned cell: list_directory x / (store-root scope) |
| 254 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 255 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 256 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | EDGE | scanned cell: get_file_info x / (store-root scope) |
| 257 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | EDGE | scanned cell: list_directory x / (store-root scope) |
| 258 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 259 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 260 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | EDGE | scanned cell: list_directory x / (store-root scope) |
| 261 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | EDGE | scanned cell: get_file_info x / (store-root scope) |
| 262 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 263 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/` | Dr. Smith | BENIGN | scanned cell: list_directory x patients/ (directory scope patients/) |
| 264 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory_with_sizes` | `patients/alice_johnson/` | Nurse Adams | BENIGN | scanned cell: list_directory_with_sizes x patients/alice_johnson/ (directory scope patients/alice_johnson/) |
| 265 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `directory_tree` | `billing/` | Receptionist Torres | BENIGN | scanned cell: directory_tree x billing/ (directory scope billing/) |
| 266 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `billing/invoices/` | Receptionist Torres | BENIGN | scanned cell: list_directory x billing/invoices/ (directory scope billing/invoices/) |
| 267 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory_with_sizes` | `billing/` | Billing Staff | MISUSE | scanned cell: list_directory_with_sizes x billing/ (directory scope billing/) |
| 268 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/` | New Resident | MISUSE | scanned cell: list_directory x patients/ (directory scope patients/) |
| 269 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `billing/` | New Resident | MISUSE | scanned cell: list_directory x billing/ (directory scope billing/) |
| 270 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/alice_johnson/` | Clumsy Admin | MISUSE | scanned cell: list_directory x patients/alice_johnson/ (directory scope patients/alice_johnson/) |
| 271 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/` | Attacker (Eve) | MALICIOUS | scanned cell: list_directory x patients/ (directory scope patients/) |
| 272 | 16 | 16 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `create_directory` | `billing/` | Attacker (Eve) | MALICIOUS | scanned cell: create_directory x billing/ (scope billing/ (ancestor of staging)) |
| 273 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `directory_tree` | `cases/CASE-2026-001/` | Atty Thompson | BENIGN | scanned cell: directory_tree x cases/CASE-2026-001/ (directory scope cases/CASE-2026-001/) |
| 274 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory_with_sizes` | `clients/` | Paralegal Kim | BENIGN | scanned cell: list_directory_with_sizes x clients/ (directory scope clients/) |
| 275 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory` | `cases/CASE-2026-002/` | Associate Chen | BENIGN | scanned cell: list_directory x cases/CASE-2026-002/ (directory scope cases/CASE-2026-002/) |
| 276 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `directory_tree` | `/` | Junior Associate | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 277 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory_with_sizes` | `billing/timesheets/` | Billing Clerk | MISUSE | scanned cell: list_directory_with_sizes x billing/timesheets/ (directory scope billing/timesheets/) |
| 278 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `directory_tree` | `/` | New Intern | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 279 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory` | `cases/` | New Intern | MISUSE | scanned cell: list_directory x cases/ (directory scope cases/) |
| 280 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory` | `clients/` | New Intern | MISUSE | scanned cell: list_directory x clients/ (directory scope clients/) |
| 281 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory` | `billing/` | New Intern | MISUSE | scanned cell: list_directory x billing/ (directory scope billing/) |
| 282 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `directory_tree` | `/` | Admin Overbroad | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 283 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory` | `clients/` | Attacker (Mallory) | MALICIOUS | scanned cell: list_directory x clients/ (directory scope clients/) |
| 284 | 16 | 16 | 1x | medium | medium | — | — | fs_law_firm_fs | `move_file` | `clients/acme_corp/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: move_file x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 285 | 16 | 16 | 1x | medium | medium | — | — | fs_law_firm_fs | `create_directory` | `billing/` | Attacker (Mallory) | MALICIOUS | scanned cell: create_directory x billing/ (scope billing/ (ancestor of staging)) |
| 286 | 16 | 16 | 1x | medium | medium | — | — | fs_law_firm_fs | `move_file` | `cases/CASE-2026-001/signed_agreement.pdf` | Attacker (Mallory) | MALICIOUS | scanned cell: move_file x cases/CASE-2026-001/signed_agreement.pdf (file cases/CASE-2026-001/signed_agreement.pdf) |
| 287 | 16 | 16 | 1x | high | high | — | — | fs_media_studio_fs | `directory_tree` | `clients/` | Account Manager Taylor | BENIGN | scanned cell: directory_tree x clients/ (directory scope clients/) |
| 288 | 16 | 16 | 1x | high | high | — | — | fs_media_studio_fs | `list_directory` | `clients/` | New Hire | MISUSE | scanned cell: list_directory x clients/ (directory scope clients/) |
| 289 | 16 | 16 | 1x | high | high | — | — | fs_media_studio_fs | `list_directory` | `invoices/` | New Hire | MISUSE | scanned cell: list_directory x invoices/ (directory scope invoices/) |
| 290 | 16 | 16 | 1x | high | high | — | — | fs_media_studio_fs | `list_directory_with_sizes` | `invoices/` | Billing Overbroad | MISUSE | scanned cell: list_directory_with_sizes x invoices/ (directory scope invoices/) |
| 291 | 16 | 16 | 1x | high | high | — | — | fs_media_studio_fs | `list_directory` | `clients/` | Admin Overbroad | MISUSE | scanned cell: list_directory x clients/ (directory scope clients/) |
| 292 | 16 | 16 | 1x | medium | medium | — | — | fs_media_studio_fs | `create_directory` | `invoices/` | Attacker (Oscar) | MALICIOUS | scanned cell: create_directory x invoices/ (scope invoices/ (ancestor of staging)) |
| 293 | 16 | 16 | 1x | high | high | — | — | sqlite_cbg_sqlite | `describe_table` | `employees` | New User | DISCOVERY | scanned cell: describe_table x employees (table employees) |
| 294 | 16 | 16 | 1x | high | high | — | — | sqlite_cbg_sqlite | `describe_table` | `projects` | New User | DISCOVERY | scanned cell: describe_table x projects (table projects) |
| 295 | 16 | 16 | 1x | high | high | — | — | sqlite_cbg_sqlite | `describe_table` | `datasets` | New User | DISCOVERY | scanned cell: describe_table x datasets (table datasets) |
| 296 | 16 | 16 | 1x | high | high | — | — | sqlite_cbg_sqlite | `describe_table` | `grants` | New User | DISCOVERY | scanned cell: describe_table x grants (table grants) |
| 297 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 298 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 299 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 300 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 301 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 302 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 303 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 304 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 305 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 306 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 307 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 308 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 309 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Attacker (Mallory) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 310 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 311 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 312 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 313 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 314 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 315 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 316 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 317 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 318 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 319 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 320 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 321 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 322 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 323 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 324 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 325 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 326 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 327 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 328 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 329 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 330 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 331 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 332 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 333 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 334 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 335 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 336 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 337 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 338 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 339 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 340 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 341 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 342 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 343 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 344 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 345 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 346 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 347 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 348 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 349 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 350 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 351 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 352 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 353 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 354 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 355 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 356 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 357 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 358 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 359 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 360 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 361 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 362 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 363 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 364 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 365 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 366 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 367 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 368 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 369 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 370 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 371 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 372 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 373 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 374 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 375 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 376 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 377 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 378 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 379 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 380 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 381 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 382 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 383 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 384 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 385 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 386 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 387 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Attacker (Mallory) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 388 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 389 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 390 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 391 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 392 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 393 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 394 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 395 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 396 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 397 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 398 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 399 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 400 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 401 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 402 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 403 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 404 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 405 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 406 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 407 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 408 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 409 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 410 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 411 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 412 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 413 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 414 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 415 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Attacker (Mallory) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 416 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 417 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 418 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 419 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 420 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 421 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 422 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 423 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 424 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 425 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 426 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 427 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 428 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 429 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 430 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 431 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 432 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 433 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 434 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 435 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 436 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 437 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 438 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 439 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 440 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 441 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 442 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 443 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 444 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 445 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 446 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 447 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 448 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 449 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 450 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 451 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 452 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 453 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 454 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 455 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 456 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 457 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 458 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 459 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 460 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 461 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 462 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 463 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 464 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 465 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 466 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 467 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 468 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 469 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 470 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 471 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 472 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 473 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 474 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 475 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 476 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 477 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 478 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 479 | 16 | 16 | 1x | medium | medium | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 480 | 16 | 16 | 1x | medium | medium | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 481 | 16 | 16 | 1x | medium | medium | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 482 | 16 | 16 | 1x | medium | medium | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 483 | 16 | 16 | 1x | medium | medium | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 484 | 16 | 16 | 1x | medium | medium | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 485 | 16 | 16 | 1x | medium | medium | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 486 | 16 | 16 | 1x | medium | medium | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 487 | 16 | 8 | 2x | high | medium | pattern | high | fs_media_studio_fs | `search_files` | `shoots/` | Freelancer Overbroad | MISUSE | scanned cell: search_files x shoots/ (directory scope shoots/) |
| 488 | 16 | 8 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `publications` | Farid Hassan | VALID | scanned cell: read_query x publications (table publications) |
| 489 | 15 | 10 | 1.5x | medium | medium | paths | medium | fs_corp_filesystem | `read_multiple_files` | `sensitive/security/private_key.pem` | Mallory (Attacker) | EDGE | scanned cell: read_multiple_files x sensitive/security/private_key.pem (file sensitive/security/private_key.pem) |
| 490 | 12 | 12 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `directory_tree` | `/` | Intern Carter | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 491 | 12 | 12 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `directory_tree` | `/` | New Resident | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 492 | 12 | 12 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `list_directory` | `/` | New Resident | MISUSE | scanned cell: list_directory x / (store-root scope) |
| 493 | 12 | 12 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `list_directory` | `scans/` | New Resident | MISUSE | scanned cell: list_directory x scans/ (directory scope scans/) |
| 494 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `list_directory` | `shoots/SHOOT-2026-A/` | Photographer Alex | BENIGN | scanned cell: list_directory x shoots/SHOOT-2026-A/ (directory scope shoots/SHOOT-2026-A/) |
| 495 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `list_directory_with_sizes` | `shoots/SHOOT-2026-A/` | Art Director Sam | BENIGN | scanned cell: list_directory_with_sizes x shoots/SHOOT-2026-A/ (directory scope shoots/SHOOT-2026-A/) |
| 496 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `list_directory` | `/` | PM Casey | BENIGN | scanned cell: list_directory x / (store-root scope) |
| 497 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `directory_tree` | `/` | New Hire | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 498 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `list_directory` | `shoots/SHOOT-2026-A/` | Attacker (Oscar) | MALICIOUS | scanned cell: list_directory x shoots/SHOOT-2026-A/ (directory scope shoots/SHOOT-2026-A/) |
| 499 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `move_file` | `shoots/SHOOT-2026-A/photo_002.jpg` | Attacker (Oscar) | MALICIOUS | scanned cell: move_file x shoots/SHOOT-2026-A/photo_002.jpg (file shoots/SHOOT-2026-A/photo_002.jpg) |
| 500 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `move_file` | `shoots/SHOOT-2026-B/photo_001.jpg` | Attacker (Oscar) | MALICIOUS | scanned cell: move_file x shoots/SHOOT-2026-B/photo_001.jpg (file shoots/SHOOT-2026-B/photo_001.jpg) |
| 501 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 502 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 503 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 504 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 505 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 506 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 507 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 508 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 509 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 510 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 511 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 512 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 513 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 514 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 515 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 516 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 517 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 518 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 519 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 520 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 521 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 522 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 523 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 524 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 525 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 526 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 527 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 528 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 529 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 530 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 531 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 532 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 533 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 534 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 535 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 536 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 537 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 538 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 539 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 540 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 541 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 542 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 543 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 544 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 545 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 546 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 547 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 548 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 549 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 550 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 551 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 552 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 553 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 554 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 555 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 556 | 12 | 12 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 557 | 12 | 8 | 1.5x | medium | medium | paths | medium | fs_law_firm_fs | `read_multiple_files` | `clients/acme_corp/intake.txt` | Paralegal Kim | BENIGN | scanned cell: read_multiple_files x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 558 | 12 | 8 | 1.5x | medium | medium | paths | medium | fs_law_firm_fs | `read_multiple_files` | `clients/acme_corp/intake.txt` | Paralegal Overbroad | MISUSE | scanned cell: read_multiple_files x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 559 | 10 | 10 | 1x | medium | medium | — | — | fs_corp_filesystem | `get_file_info` | `sensitive/security/private_key.pem` | Eve (Security) | VALID | scanned cell: get_file_info x sensitive/security/private_key.pem (file sensitive/security/private_key.pem) |
| 560 | 10 | 10 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/intake_form.txt` | Dr. Smith | BENIGN | scanned cell: read_text_file x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 561 | 10 | 10 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/intake_form.txt` | New Resident | MISUSE | scanned cell: read_text_file x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 562 | 10 | 10 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/medical_history.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/alice_johnson/medical_history.txt (file patients/alice_johnson/medical_history.txt) |
| 563 | 10 | 10 | 1x | medium | medium | — | — | sqlite_cbg_sqlite | `describe_table` | `api_keys` | New User | DISCOVERY | scanned cell: describe_table x api_keys (table api_keys) |
| 564 | 10 | 10 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 565 | 10 | 10 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 566 | 10 | 10 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 567 | 10 | 10 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 568 | 10 | 10 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 569 | 10 | 10 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 570 | 10 | 10 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 571 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 572 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 573 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Insider (Mallory) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 574 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 575 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 576 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 577 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 578 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Insider (Mallory) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 579 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 580 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 581 | 10 | 10 | 1x | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Insider (Mallory) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 582 | 8 | 8 | 1x | medium | medium | — | — | fs_corp_filesystem | `list_directory` | `onboarding/` | Alice (HR) | VALID | scanned cell: list_directory x onboarding/ (directory scope onboarding/) |
| 583 | 8 | 8 | 1x | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `onboarding/` | Alice (HR) | VALID | scanned cell: read_text_file x onboarding/ (scope onboarding/ (ancestor of policies.pdf)) |
| 584 | 8 | 8 | 1x | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `sensitive/financials/payslips_q1.csv` | Carol (Finance) | VALID | scanned cell: read_text_file x sensitive/financials/payslips_q1.csv (file sensitive/financials/payslips_q1.csv) |
| 585 | 8 | 8 | 1x | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `sensitive/security/audit_log.txt` | Eve (Security) | VALID | scanned cell: read_text_file x sensitive/security/audit_log.txt (file sensitive/security/audit_log.txt) |
| 586 | 8 | 8 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `policies/hipaa_notice.txt` | Admin Nguyen | BENIGN | scanned cell: read_text_file x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 587 | 8 | 8 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `policies/hipaa_notice.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 588 | 8 | 8 | 1x | medium | medium | — | — | fs_law_firm_fs | `list_directory` | `templates/` | Partner Davis | BENIGN | scanned cell: list_directory x templates/ (directory scope templates/) |
| 589 | 8 | 8 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-01.txt` | Billing Roberts | BENIGN | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-01.txt (file billing/timesheets/timesheet_2026-05-01.txt) |
| 590 | 8 | 8 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-01.txt` | Billing Clerk | MISUSE | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-01.txt (file billing/timesheets/timesheet_2026-05-01.txt) |
| 591 | 8 | 8 | 1x | medium | medium | — | — | fs_law_firm_fs | `list_directory` | `templates/` | New Intern | MISUSE | scanned cell: list_directory x templates/ (directory scope templates/) |
| 592 | 8 | 8 | 1x | medium | medium | — | — | fs_media_studio_fs | `list_directory` | `shoots/` | New Hire | MISUSE | scanned cell: list_directory x shoots/ (directory scope shoots/) |
| 593 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 594 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 595 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 596 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 597 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 598 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 599 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 600 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 601 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 602 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 603 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 604 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 605 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 606 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 607 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 608 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 609 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 610 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 611 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 612 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 613 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 614 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 615 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 616 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 617 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 618 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 619 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 620 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 621 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 622 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 623 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 624 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 625 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 626 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 627 | 6 | 4 | 1.5x | medium | medium | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `staff_directory.txt` | Nurse Overbroad | MISUSE | scanned cell: read_multiple_files x staff_directory.txt (file staff_directory.txt) |
| 628 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 629 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 630 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 631 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 632 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 633 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 634 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 635 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 636 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 637 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 638 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 639 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 640 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 641 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 642 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 643 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 644 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 645 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 646 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 647 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 648 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 649 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 650 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 651 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 652 | 5 | 5 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/intake_form.txt` | Dr. Smith | BENIGN | scanned cell: read_text_file x patients/bob_martinez/intake_form.txt (file patients/bob_martinez/intake_form.txt) |
| 653 | 4.5 | 3 | 1.5x | medium | low | paths | medium | fs_media_studio_fs | `read_multiple_files` | `project_pipeline.txt` | PM Overbroad | MISUSE | scanned cell: read_multiple_files x project_pipeline.txt (file project_pipeline.txt) |
| 654 | 4 | 4 | 1x | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `source_code/core.c` | Bob (Dev) | VALID | scanned cell: read_text_file x source_code/core.c (file source_code/core.c) |
| 655 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `staff_directory.txt` | Receptionist Torres | BENIGN | scanned cell: read_text_file x staff_directory.txt (file staff_directory.txt) |
| 656 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/prescription.txt` | Dr. Patel | BENIGN | scanned cell: read_text_file x patients/alice_johnson/prescription.txt (file patients/alice_johnson/prescription.txt) |
| 657 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/prescription.txt` | Dr. Patel | BENIGN | scanned cell: read_text_file x patients/bob_martinez/prescription.txt (file patients/bob_martinez/prescription.txt) |
| 658 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `get_file_info` | `policies/hipaa_notice.txt` | Admin Nguyen | BENIGN | scanned cell: get_file_info x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 659 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `billing/invoices/inv_2026-05-20_alice_johnson.txt` | Admin Nguyen | BENIGN | scanned cell: read_text_file x billing/invoices/inv_2026-05-20_alice_johnson.txt (file billing/invoices/inv_2026-05-20_alice_johnson.txt) |
| 660 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `billing/invoices/inv_2026-05-20_alice_johnson.txt` | Billing Staff | MISUSE | scanned cell: read_text_file x billing/invoices/inv_2026-05-20_alice_johnson.txt (file billing/invoices/inv_2026-05-20_alice_johnson.txt) |
| 661 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `billing/invoices/inv_2026-05-21_bob_martinez.txt` | Billing Staff | MISUSE | scanned cell: read_text_file x billing/invoices/inv_2026-05-21_bob_martinez.txt (file billing/invoices/inv_2026-05-21_bob_martinez.txt) |
| 662 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/prescription.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/alice_johnson/prescription.txt (file patients/alice_johnson/prescription.txt) |
| 663 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/prescription.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/bob_martinez/prescription.txt (file patients/bob_martinez/prescription.txt) |
| 664 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_media_file` | `scans/alice_johnson_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x scans/alice_johnson_xray.png (file scans/alice_johnson_xray.png) |
| 665 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_media_file` | `scans/bob_martinez_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x scans/bob_martinez_xray.png (file scans/bob_martinez_xray.png) |
| 666 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `get_file_info` | `scans/bob_martinez_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_info x scans/bob_martinez_xray.png (file scans/bob_martinez_xray.png) |
| 667 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/prescription.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/bob_martinez/prescription.txt (file patients/bob_martinez/prescription.txt) |
| 668 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-001/contract.txt` | Atty Thompson | BENIGN | scanned cell: read_text_file x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 669 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-001/correspondence.txt` | Atty Thompson | BENIGN | scanned cell: read_text_file x cases/CASE-2026-001/correspondence.txt (file cases/CASE-2026-001/correspondence.txt) |
| 670 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `get_file_info` | `templates/nda_template.txt` | Partner Davis | BENIGN | scanned cell: get_file_info x templates/nda_template.txt (file templates/nda_template.txt) |
| 671 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `templates/nda_template.txt` | Partner Davis | BENIGN | scanned cell: read_text_file x templates/nda_template.txt (file templates/nda_template.txt) |
| 672 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-15.txt` | Billing Roberts | BENIGN | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-15.txt (file billing/timesheets/timesheet_2026-05-15.txt) |
| 673 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_media_file` | `cases/CASE-2026-002/signed_agreement.pdf` | Associate Chen | BENIGN | scanned cell: read_media_file x cases/CASE-2026-002/signed_agreement.pdf (file cases/CASE-2026-002/signed_agreement.pdf) |
| 674 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-002/correspondence.txt` | Associate Chen | BENIGN | scanned cell: read_text_file x cases/CASE-2026-002/correspondence.txt (file cases/CASE-2026-002/correspondence.txt) |
| 675 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-15.txt` | Billing Clerk | MISUSE | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-15.txt (file billing/timesheets/timesheet_2026-05-15.txt) |
| 676 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-001/contract.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 677 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-002/contract.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x cases/CASE-2026-002/contract.txt (file cases/CASE-2026-002/contract.txt) |
| 678 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `templates/nda_template.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x templates/nda_template.txt (file templates/nda_template.txt) |
| 679 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `clients/acme_corp/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 680 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_media_file` | `cases/CASE-2026-001/signed_agreement.pdf` | Attacker (Mallory) | MALICIOUS | scanned cell: read_media_file x cases/CASE-2026-001/signed_agreement.pdf (file cases/CASE-2026-001/signed_agreement.pdf) |
| 681 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `get_file_info` | `clients/blue_whale_inc/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: get_file_info x clients/blue_whale_inc/intake.txt (file clients/blue_whale_inc/intake.txt) |
| 682 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `clients/blue_whale_inc/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x clients/blue_whale_inc/intake.txt (file clients/blue_whale_inc/intake.txt) |
| 683 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-002/contract.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x cases/CASE-2026-002/contract.txt (file cases/CASE-2026-002/contract.txt) |
| 684 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `shoots/SHOOT-2026-A/brief.txt` | Photographer Alex | BENIGN | scanned cell: read_text_file x shoots/SHOOT-2026-A/brief.txt (file shoots/SHOOT-2026-A/brief.txt) |
| 685 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `get_file_info` | `clients/citybank/contract.txt` | Account Manager Taylor | BENIGN | scanned cell: get_file_info x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 686 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/citybank/contract.txt` | Account Manager Taylor | BENIGN | scanned cell: read_text_file x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 687 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `invoices/inv_2026-05-15_citybank.txt` | Billing Jordan | BENIGN | scanned cell: read_text_file x invoices/inv_2026-05-15_citybank.txt (file invoices/inv_2026-05-15_citybank.txt) |
| 688 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `invoices/inv_2026-05-21_neon_brand.txt` | Billing Jordan | BENIGN | scanned cell: read_text_file x invoices/inv_2026-05-21_neon_brand.txt (file invoices/inv_2026-05-21_neon_brand.txt) |
| 689 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `invoices/inv_2026-05-15_citybank.txt` | Billing Overbroad | MISUSE | scanned cell: read_text_file x invoices/inv_2026-05-15_citybank.txt (file invoices/inv_2026-05-15_citybank.txt) |
| 690 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/citybank/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 691 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/neon_brand/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x clients/neon_brand/contract.txt (file clients/neon_brand/contract.txt) |
| 692 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `get_file_info` | `clients/neon_brand/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: get_file_info x clients/neon_brand/contract.txt (file clients/neon_brand/contract.txt) |
| 693 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/neon_brand/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x clients/neon_brand/contract.txt (file clients/neon_brand/contract.txt) |
| 694 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 695 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 696 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 697 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 698 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 699 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 700 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 701 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 702 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 703 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 704 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 705 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 706 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 707 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 708 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 709 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 710 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 711 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 712 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 713 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 714 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 715 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 716 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 717 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 718 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 719 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 720 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 721 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 722 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 723 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 724 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 725 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 726 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 727 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 728 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 729 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 730 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 731 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 732 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 733 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 734 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 735 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 736 | 4 | 4 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 737 | 4 | 4 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 738 | 4 | 4 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 739 | 4 | 4 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 740 | 4 | 4 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 741 | 4 | 4 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 742 | 4 | 4 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 743 | 4 | 4 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 744 | 4 | 4 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 745 | 4 | 4 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 746 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 747 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 748 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 749 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 750 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 751 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 752 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 753 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 754 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 755 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 756 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 757 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 758 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 759 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 760 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 761 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 762 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 763 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 764 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 765 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 766 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 767 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 768 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 769 | 4 | 4 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 770 | 3 | 3 | 1x | low | low | — | — | fs_corp_filesystem | `read_text_file` | `projects/known_defects.csv` | Dave (Manager) | VALID | scanned cell: read_text_file x projects/known_defects.csv (file projects/known_defects.csv) |
| 771 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_text_file` | `shoots/SHOOT-2026-A/notes.txt` | Photographer Alex | BENIGN | scanned cell: read_text_file x shoots/SHOOT-2026-A/notes.txt (file shoots/SHOOT-2026-A/notes.txt) |
| 772 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_001.jpg` | Art Director Sam | BENIGN | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_001.jpg (file shoots/SHOOT-2026-A/photo_001.jpg) |
| 773 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_002.jpg` | Art Director Sam | BENIGN | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_002.jpg (file shoots/SHOOT-2026-A/photo_002.jpg) |
| 774 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_text_file` | `project_pipeline.txt` | PM Casey | BENIGN | scanned cell: read_text_file x project_pipeline.txt (file project_pipeline.txt) |
| 775 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_001.jpg` | Freelancer Overbroad | MISUSE | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_001.jpg (file shoots/SHOOT-2026-A/photo_001.jpg) |
| 776 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_002.jpg` | Freelancer Overbroad | MISUSE | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_002.jpg (file shoots/SHOOT-2026-A/photo_002.jpg) |
| 777 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-B/photo_001.jpg` | Freelancer Overbroad | MISUSE | scanned cell: read_media_file x shoots/SHOOT-2026-B/photo_001.jpg (file shoots/SHOOT-2026-B/photo_001.jpg) |
| 778 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_text_file` | `project_pipeline.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x project_pipeline.txt (file project_pipeline.txt) |
| 779 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-B/photo_001.jpg` | Attacker (Oscar) | MALICIOUS | scanned cell: read_media_file x shoots/SHOOT-2026-B/photo_001.jpg (file shoots/SHOOT-2026-B/photo_001.jpg) |
| 780 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_text_file` | `shoots/SHOOT-2026-B/notes.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x shoots/SHOOT-2026-B/notes.txt (file shoots/SHOOT-2026-B/notes.txt) |
| 781 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 782 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 783 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 784 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 785 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 786 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 787 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 788 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 789 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 790 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 791 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 792 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 793 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 794 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 795 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 796 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 797 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 798 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 799 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 800 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 801 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 802 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 803 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 804 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 805 | 2 | 2 | 1x | low | low | — | — | fs_corp_filesystem | `read_media_file` | `onboarding/org_chart.png` | Alice (HR) | VALID | scanned cell: read_media_file x onboarding/org_chart.png (file onboarding/org_chart.png) |
| 806 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 807 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 808 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 809 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 810 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 811 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 812 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 813 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 814 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 815 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 816 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 817 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 818 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 819 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 820 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 821 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 822 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 823 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 824 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 825 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 826 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 827 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 828 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 829 | 2 | 2 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 830 | 1 | 1 | 1x | low | low | — | — | fs_corp_filesystem | `read_text_file` | `README.md` | Frank (New hire) | VALID | scanned cell: read_text_file x README.md (file README.md) |
| 831 | — | — | 1x | unresolved | unresolved | — | — | fs_corp_filesystem | `list_allowed_directories` | `—` | New User | DISCOVERY | no path argument |
| 832 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `delete_file` | `—` | Mallory (Attacker) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 833 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `execute_shell` | `—` | Mallory (Attacker) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 834 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `copy_file` | `—` | Frank (New hire) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 835 | — | — | 1x | unresolved | unresolved | — | — | fs_corp_filesystem | `read_text_file` | `—` | Frank (New hire) | BAD_PARAMS | no path argument |
| 836 | — | — | 1x | unresolved | unresolved | — | — | fs_corp_filesystem | `list_allowed_directories` | `—` | — | VALID | no path argument |
| 837 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `non-existent-tool` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 838 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `readFile` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 839 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `read_File` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 840 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `listDirectory` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 841 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `list-directory` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 842 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `delete_file` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 843 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `execute_command` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 844 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `admin-override` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 845 | — | — | 1x | invalid | invalid | — | — | fs_corp_filesystem | `write-file` | `—` | — | BAD_TOOL | unknown tool (likely misconfiguration) |
| 846 | — | — | 1x | unresolved | unresolved | — | — | fs_corp_filesystem | `read_file` | `—` | — | BAD_PARAMS | no path argument |
| 847 | — | — | 1x | unresolved | unresolved | — | — | fs_corp_filesystem | `list_directory` | `—` | — | BAD_PARAMS | no path argument |
| 848 | — | — | 1x | unresolved | unresolved | — | — | fs_corp_filesystem | `get_file_info` | `—` | — | BAD_PARAMS | no path argument |
| 849 | — | — | 1x | unresolved | unresolved | — | — | fs_corp_filesystem | `read_multiple_files` | `—` | — | BAD_PARAMS | no path argument |
| 850 | — | — | 1x | unresolved | unresolved | — | — | fs_corp_filesystem | `read_file` | `—` | — | BAD_PARAMS | no path argument |
| 851 | — | — | 1x | unresolved | unresolved | — | — | fs_corp_filesystem | `directory_tree` | `—` | — | BAD_PARAMS | no path argument |
| 852 | — | — | 1x | unresolved | unresolved | — | — | fs_medical_clinic_fs | `list_allowed_directories` | `—` | Dr. Smith | BENIGN | no path argument |
| 853 | — | — | 1x | unresolved | unresolved | — | — | fs_medical_clinic_fs | `list_allowed_directories` | `—` | New Resident | MISUSE | no path argument |
| 854 | — | — | 1x | unresolved | unresolved | — | — | fs_law_firm_fs | `list_allowed_directories` | `—` | Atty Thompson | BENIGN | no path argument |
| 855 | — | — | 1x | unresolved | unresolved | — | — | fs_law_firm_fs | `list_allowed_directories` | `—` | New Intern | MISUSE | no path argument |
| 856 | — | — | 1x | unresolved | unresolved | — | — | fs_media_studio_fs | `list_allowed_directories` | `—` | Photographer Alex | BENIGN | no path argument |
| 857 | — | — | 1x | unresolved | unresolved | — | — | fs_media_studio_fs | `list_allowed_directories` | `—` | New Hire | MISUSE | no path argument |
| 858 | — | — | 1x | unresolved | unresolved | — | — | sqlite_cbg_sqlite | `list_tables` | `—` | New User | DISCOVERY | no table/query argument |
| 859 | — | — | 1x | unresolved | unresolved | values | low | sqlite_cbg_sqlite | `insert_row` | `—` | Dr. Alice Chen | VALID | table insights not in table |
| 860 | — | — | 1x | invalid | invalid | — | — | sqlite_cbg_sqlite | `drop_table` | `—` | Mallory (Attacker) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 861 | — | — | 1x | invalid | invalid | — | — | sqlite_cbg_sqlite | `execute_shell` | `—` | Mallory (Attacker) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 862 | — | — | 1x | invalid | invalid | — | — | sqlite_cbg_sqlite | `export_csv` | `—` | Frank (New hire) | BAD_TOOL | unknown tool (likely misconfiguration) |
| 863 | — | — | 1x | unresolved | unresolved | — | — | sqlite_cbg_sqlite | `describe_table` | `—` | Frank (New hire) | BAD_PARAMS | table nonexistent_table not in table |
| 864 | — | — | 1x | unresolved | unresolved | values | low | sqlite_cbg_sqlite | `insert_row` | `—` | Mallory (Attacker) | EDGE | table insights not in table |
| 865 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 866 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 867 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 868 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 869 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 870 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 871 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 872 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 873 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 874 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 875 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 876 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 877 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 878 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 879 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 880 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 881 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 882 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 883 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 884 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 885 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 886 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 887 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 888 | — | — | 1x | unresolved | unresolved | — | — | github_cbg | `search_repositories` | `—` | CI Bot | BENIGN | no repository argument |
| 889 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 890 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 891 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 892 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 893 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 894 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 895 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 896 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 897 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 898 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 899 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 900 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 901 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 902 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 903 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 904 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 905 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 906 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 907 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 908 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 909 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 910 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 911 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 912 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 913 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 914 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 915 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 916 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 917 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 918 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 919 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 920 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_list_channels` | `—` | Support Agent | BENIGN | no channel argument |
| 921 | — | — | 1x | unresolved | unresolved | — | — | slack_cbg | `slack_get_user_profile` | `—` | Attacker (Trudy) | MALICIOUS | no channel argument |
| 922 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 923 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 924 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 925 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 926 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 927 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 928 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 929 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 930 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 931 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 932 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 933 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 934 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 935 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 936 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 937 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 938 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 939 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 940 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 941 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 942 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 943 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 944 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 945 | — | — | 1x | unresolved | unresolved | — | — | fs_fintech_fs | `list_allowed_directories` | `—` | Finance Analyst | BENIGN | no path argument |
| 946 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 947 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 948 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 949 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 950 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 951 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 952 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 953 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 954 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 955 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 956 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 957 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 958 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 959 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 960 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 961 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 962 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 963 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 964 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 965 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 966 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 967 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 968 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
| 969 | — | — | 1x | unresolved | unresolved | — | — | sqlite_devops_sqlite | `list_tables` | `—` | Analytics Bot | BENIGN | no table/query argument |
