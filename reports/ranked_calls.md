# Ranked MCP calls

Each captured call scored against the scanner's risk matrix for its server (no design-time table read). Ranking is by **final_score** — the cell score amplified by the call's input-parameter risk (`score x param_multiplier`). Bands are shown for visualization only.

969 calls across 10 server(s).

Resolved to a scanned cell: 830/969
  critical: 5
      high: 315
    medium: 383
       low: 127
  unresolved: 124 (directory/enumeration ops, no-arg calls, or assets not in the scan)
  invalid: 15 (unknown tools)

Parameter risk amplified the score on 166 resolved call(s).

Top 10 riskiest resolved calls (by final score):
   1. [72] fs_corp_filesystem/edit_file -> source_code/  (VALID) (cell 48 x1.5 via edits)  [critical]
   2. [72] sqlite_devops_sqlite/write_query -> audit_log  (MALICIOUS) (cell 36 x2 via sql)  [high]
   3. [72] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 36 x2 via sql)  [high]
   4. [72] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 36 x2 via sql)  [high]
   5. [72] sqlite_devops_sqlite/write_query -> audit_log  (MALICIOUS) (cell 36 x2 via sql)  [high]
   6. [72] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 36 x2 via sql)  [high]
   7. [72] sqlite_devops_sqlite/write_query -> audit_log  (MALICIOUS) (cell 36 x2 via sql)  [high]
   8. [72] sqlite_devops_sqlite/write_query -> audit_log  (MALICIOUS) (cell 36 x2 via sql)  [high]
   9. [72] sqlite_devops_sqlite/write_query -> users  (MALICIOUS) (cell 36 x2 via sql)  [high]
  10. [72] sqlite_devops_sqlite/write_query -> audit_log  (MALICIOUS) (cell 36 x2 via sql)  [high]

## Ranking

| Rank | Final score | Cell score | Param x | Final band | Cell band | Param | Param risk | Server | Tool | Asset | Persona | Category | Reason |
| ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 72 | 48 | 1.5x | critical | critical | edits | medium | fs_corp_filesystem | `edit_file` | `source_code/` | Bob (Dev) | VALID | scanned cell: edit_file x source_code/ (scope source_code/ (ancestor of notes.txt)) |
| 2 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 3 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 4 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 5 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 6 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 7 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 8 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 9 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 10 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 11 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 12 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 13 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 14 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 15 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 16 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: write_query x users (table users) |
| 17 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `audit_log` | Insider (Dave) | MALICIOUS | scanned cell: write_query x audit_log (table audit_log) |
| 18 | 72 | 36 | 2x | high | high | sql | high | sqlite_devops_sqlite | `write_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: write_query x users (table users) |
| 19 | 60 | 60 | 1x | critical | critical | — | — | fs_corp_filesystem | `move_file` | `/` | Mallory (Attacker) | BAD_PARAMS | scanned cell: move_file x / (store-root scope) |
| 20 | 60 | 60 | 1x | critical | critical | — | — | fs_corp_filesystem | `move_file` | `/` | — | BAD_PARAMS | scanned cell: move_file x / (store-root scope) |
| 21 | 60 | 60 | 1x | critical | critical | — | — | fs_corp_filesystem | `edit_file` | `/` | — | BAD_PARAMS | scanned cell: edit_file x / (store-root scope) |
| 22 | 48 | 48 | 1x | critical | critical | — | — | fs_corp_filesystem | `move_file` | `source_code/` | Bob (Dev) | VALID | scanned cell: move_file x source_code/ (scope source_code/ (ancestor of notes.txt)) |
| 23 | 48 | 24 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `write_query` | `employees` | Mallory (Attacker) | BAD_PARAMS | scanned cell: write_query x employees (table employees) |
| 24 | 48 | 24 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `write_query` | `employees` | Mallory (Attacker) | EDGE | scanned cell: write_query x employees (table employees) |
| 25 | 45 | 45 | 1x | high | high | — | — | github_cbg | `push_files` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: push_files x payments-service (repo payments-service) |
| 26 | 45 | 45 | 1x | high | high | — | — | github_cbg | `push_files` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: push_files x payments-service (repo payments-service) |
| 27 | 45 | 45 | 1x | high | high | — | — | github_cbg | `push_files` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: push_files x payments-service (repo payments-service) |
| 28 | 40 | 20 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | New User | DISCOVERY | scanned cell: search_files x / (store-root scope) |
| 29 | 40 | 20 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | New User | DISCOVERY | scanned cell: search_files x / (store-root scope) |
| 30 | 40 | 20 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | Dave (Manager) | VALID | scanned cell: search_files x / (store-root scope) |
| 31 | 40 | 20 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 32 | 40 | 20 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 33 | 40 | 20 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 34 | 40 | 20 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 35 | 40 | 20 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 36 | 40 | 20 | 2x | high | high | pattern | high | fs_corp_filesystem | `search_files` | `/` | — | VALID | scanned cell: search_files x / (store-root scope) |
| 37 | 40 | 20 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `api_keys` | Mallory (Attacker) | BAD_PARAMS | scanned cell: read_query x api_keys (table api_keys) |
| 38 | 40 | 20 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `api_keys` | Mallory (Attacker) | EDGE | scanned cell: read_query x api_keys (table api_keys) |
| 39 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 40 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 41 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 42 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 43 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 44 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 45 | 40 | 20 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: read_query x api_tokens (table api_tokens) |
| 46 | 36 | 36 | 1x | high | high | — | — | fs_law_firm_fs | `write_file` | `billing/timesheets/` | Billing Clerk | MISUSE | scanned cell: write_file x billing/timesheets/ (scope billing/timesheets/ (ancestor of all_hours_dump.txt)) |
| 47 | 36 | 36 | 1x | high | high | — | — | fs_law_firm_fs | `write_file` | `cases/CASE-2026-001/` | Admin Overbroad | MISUSE | scanned cell: write_file x cases/CASE-2026-001/ (scope cases/CASE-2026-001/ (ancestor of admin_note.txt)) |
| 48 | 36 | 36 | 1x | high | high | — | — | fs_law_firm_fs | `write_file` | `billing/` | Attacker (Mallory) | MALICIOUS | scanned cell: write_file x billing/ (scope billing/ (ancestor of exfil.txt)) |
| 49 | 36 | 36 | 1x | high | high | — | — | fs_media_studio_fs | `write_file` | `invoices/` | Billing Overbroad | MISUSE | scanned cell: write_file x invoices/ (scope invoices/ (ancestor of draft_invoice.txt)) |
| 50 | 36 | 36 | 1x | high | high | — | — | fs_media_studio_fs | `write_file` | `invoices/` | Attacker (Oscar) | MALICIOUS | scanned cell: write_file x invoices/ (scope invoices/ (ancestor of exfil.txt)) |
| 51 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 52 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 53 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 54 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 55 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 56 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 57 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 58 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 59 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 60 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 61 | 36 | 36 | 1x | high | high | — | — | calendar_cbg | `delete_all_events` | `team` | Insider (Dave) | MALICIOUS | scanned cell: delete_all_events x team (calendar team) |
| 62 | 36 | 24 | 1.5x | high | high | edits | medium | fs_medical_clinic_fs | `edit_file` | `policies/hipaa_notice.txt` | Attacker (Eve) | MALICIOUS | scanned cell: edit_file x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 63 | 36 | 24 | 1.5x | high | high | edits | medium | fs_law_firm_fs | `edit_file` | `templates/nda_template.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: edit_file x templates/nda_template.txt (file templates/nda_template.txt) |
| 64 | 36 | 18 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `write_query` | `experiments` | Jonas Lindberg | VALID | scanned cell: write_query x experiments (table experiments) |
| 65 | 32 | 16 | 2x | high | high | pattern | high | fs_law_firm_fs | `search_files` | `clients/` | Attacker (Mallory) | MALICIOUS | scanned cell: search_files x clients/ (directory scope clients/) |
| 66 | 32 | 16 | 2x | high | high | pattern | high | fs_media_studio_fs | `search_files` | `invoices/` | Billing Jordan | BENIGN | scanned cell: search_files x invoices/ (directory scope invoices/) |
| 67 | 32 | 16 | 2x | high | high | pattern | high | fs_media_studio_fs | `search_files` | `clients/` | Attacker (Oscar) | MALICIOUS | scanned cell: search_files x clients/ (directory scope clients/) |
| 68 | 32 | 16 | 2x | high | high | pattern | high | fs_media_studio_fs | `search_files` | `clients/` | Attacker (Oscar) | MALICIOUS | scanned cell: search_files x clients/ (directory scope clients/) |
| 69 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `employees` | Grace Park | VALID | scanned cell: read_query x employees (table employees) |
| 70 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `grants` | Maya Rao | VALID | scanned cell: read_query x grants (table grants) |
| 71 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `grants` | Maya Rao | VALID | scanned cell: read_query x grants (table grants) |
| 72 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `employees` | Dr. Olivia Tanaka | VALID | scanned cell: read_query x employees (table employees) |
| 73 | 32 | 16 | 2x | high | high | sql | high | sqlite_cbg_sqlite | `read_query` | `employees` | Mallory (Attacker) | EDGE | scanned cell: read_query x employees (table employees) |
| 74 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 75 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 76 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 77 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 78 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 79 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 80 | 32 | 16 | 2x | high | medium | attendees | high | calendar_cbg | `create_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: create_event x executive (calendar executive) |
| 81 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 82 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 83 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 84 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 85 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 86 | 32 | 16 | 2x | high | high | pattern | high | fs_fintech_fs | `search_files` | `customers/` | Insider (Mallory) | MALICIOUS | scanned cell: search_files x customers/ (directory scope customers/) |
| 87 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: read_query x users (table users) |
| 88 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x users (table users) |
| 89 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: read_query x users (table users) |
| 90 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x users (table users) |
| 91 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Attacker (Eve) | MALICIOUS | scanned cell: read_query x users (table users) |
| 92 | 32 | 16 | 2x | high | high | sql | high | sqlite_devops_sqlite | `read_query` | `users` | Insider (Dave) | MALICIOUS | scanned cell: read_query x users (table users) |
| 93 | 30 | 30 | 1x | high | high | — | — | fs_corp_filesystem | `write_file` | `/` | Mallory (Attacker) | EDGE | scanned cell: write_file x / (store-root scope) |
| 94 | 30 | 30 | 1x | high | high | — | — | fs_corp_filesystem | `write_file` | `/` | — | BAD_PARAMS | scanned cell: write_file x / (store-root scope) |
| 95 | 30 | 30 | 1x | high | high | — | — | fs_medical_clinic_fs | `write_file` | `patients/alice_johnson/` | Clumsy Admin | MISUSE | scanned cell: write_file x patients/alice_johnson/ (scope patients/alice_johnson/ (ancestor of admin_notes.txt)) |
| 96 | 30 | 30 | 1x | high | high | — | — | fs_medical_clinic_fs | `move_file` | `patients/alice_johnson/medical_history.txt` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x patients/alice_johnson/medical_history.txt (file patients/alice_johnson/medical_history.txt) |
| 97 | 30 | 30 | 1x | high | high | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 98 | 30 | 30 | 1x | high | high | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 99 | 30 | 30 | 1x | high | high | — | — | github_cbg | `create_or_update_file` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 100 | 30 | 30 | 1x | high | high | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 101 | 30 | 30 | 1x | high | high | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 102 | 30 | 30 | 1x | high | high | — | — | github_cbg | `merge_pull_request` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 103 | 30 | 30 | 1x | high | high | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 104 | 30 | 30 | 1x | high | high | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 105 | 30 | 30 | 1x | high | high | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 106 | 30 | 30 | 1x | high | high | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 107 | 30 | 30 | 1x | high | high | — | — | github_cbg | `merge_pull_request` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 108 | 30 | 30 | 1x | high | high | — | — | github_cbg | `create_or_update_file` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: create_or_update_file x infra-config (repo infra-config) |
| 109 | 30 | 30 | 1x | high | high | — | — | github_cbg | `merge_pull_request` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 110 | 30 | 30 | 1x | high | high | — | — | github_cbg | `merge_pull_request` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: merge_pull_request x payments-service (repo payments-service) |
| 111 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 112 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 113 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 114 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 115 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 116 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 117 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 118 | 30 | 30 | 1x | high | high | — | — | fs_fintech_fs | `move_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: move_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 119 | 30 | 20 | 1.5x | high | high | paths | medium | fs_corp_filesystem | `read_multiple_files` | `/` | — | VALID | scanned cell: read_multiple_files x / (store-root scope) |
| 120 | 27 | 18 | 1.5x | high | high | edits | medium | fs_media_studio_fs | `edit_file` | `project_pipeline.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: edit_file x project_pipeline.txt (file project_pipeline.txt) |
| 121 | 24 | 24 | 1x | high | high | — | — | fs_corp_filesystem | `write_file` | `source_code/` | Bob (Dev) | VALID | scanned cell: write_file x source_code/ (scope source_code/ (ancestor of notes.txt)) |
| 122 | 24 | 24 | 1x | high | high | — | — | fs_medical_clinic_fs | `write_file` | `billing/invoices/` | Billing Staff | MISUSE | scanned cell: write_file x billing/invoices/ (scope billing/invoices/ (ancestor of combined_dump.txt)) |
| 123 | 24 | 24 | 1x | high | high | — | — | fs_medical_clinic_fs | `write_file` | `billing/` | Attacker (Eve) | MALICIOUS | scanned cell: write_file x billing/ (scope billing/ (ancestor of exfil.txt)) |
| 124 | 24 | 24 | 1x | high | high | — | — | fs_medical_clinic_fs | `move_file` | `scans/alice_johnson_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: move_file x scans/alice_johnson_xray.png (file scans/alice_johnson_xray.png) |
| 125 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 126 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 127 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 128 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 129 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 130 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 131 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 132 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 133 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 134 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 135 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 136 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 137 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 138 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 139 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 140 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 141 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 142 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 143 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 144 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `delete_event` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: delete_event x executive (calendar executive) |
| 145 | 24 | 24 | 1x | high | high | — | — | calendar_cbg | `send_email_invite` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: send_email_invite x executive (calendar executive) |
| 146 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Compromised CI | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 147 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 148 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 149 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 150 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 151 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Attacker (Eve) | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 152 | 24 | 24 | 1x | high | high | — | — | github_cbg | `delete_file` | `backend-api` | Compromised CI | MALICIOUS | scanned cell: delete_file x backend-api (repo backend-api) |
| 153 | 24 | 24 | 1x | high | high | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Attacker (Eve) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 154 | 24 | 24 | 1x | high | high | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Insider (Mallory) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 155 | 24 | 24 | 1x | high | high | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Insider (Mallory) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 156 | 24 | 24 | 1x | high | high | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Insider (Mallory) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 157 | 24 | 24 | 1x | high | high | — | — | fs_fintech_fs | `edit_file` | `security/audit/access_log.txt` | Attacker (Eve) | MALICIOUS | scanned cell: edit_file x security/audit/access_log.txt (file security/audit/access_log.txt) |
| 158 | 24 | 16 | 1.5x | high | high | paths | medium | fs_corp_filesystem | `read_multiple_files` | `sensitive/financials/` | Carol (Finance) | VALID | scanned cell: read_multiple_files x sensitive/financials/ (scope sensitive/financials/ (ancestor of budget_2026.xlsx)) |
| 159 | 24 | 12 | 2x | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `/` | Dr. Patel | BENIGN | scanned cell: search_files x / (store-root scope) |
| 160 | 24 | 12 | 2x | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `/` | Nurse Overbroad | MISUSE | scanned cell: search_files x / (store-root scope) |
| 161 | 24 | 12 | 2x | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x / (store-root scope) |
| 162 | 24 | 12 | 2x | high | medium | pattern | high | fs_medical_clinic_fs | `search_files` | `scans/` | Attacker (Eve) | MALICIOUS | scanned cell: search_files x scans/ (directory scope scans/) |
| 163 | 24 | 12 | 2x | high | medium | pattern | high | fs_law_firm_fs | `search_files` | `/` | Billing Roberts | BENIGN | scanned cell: search_files x / (store-root scope) |
| 164 | 24 | 12 | 2x | high | medium | pattern | high | fs_law_firm_fs | `search_files` | `/` | Paralegal Overbroad | MISUSE | scanned cell: search_files x / (store-root scope) |
| 165 | 24 | 12 | 2x | high | medium | pattern | high | fs_law_firm_fs | `search_files` | `/` | Attacker (Mallory) | MALICIOUS | scanned cell: search_files x / (store-root scope) |
| 166 | 24 | 12 | 2x | high | medium | pattern | high | fs_media_studio_fs | `search_files` | `shoots/` | Freelancer Overbroad | MISUSE | scanned cell: search_files x shoots/ (directory scope shoots/) |
| 167 | 24 | 12 | 2x | high | medium | pattern | high | fs_media_studio_fs | `search_files` | `/` | PM Overbroad | MISUSE | scanned cell: search_files x / (store-root scope) |
| 168 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `projects` | Dr. Alice Chen | VALID | scanned cell: read_query x projects (table projects) |
| 169 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Dr. Alice Chen | VALID | scanned cell: read_query x experiments (table experiments) |
| 170 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `datasets` | Dr. Bob Martinez | VALID | scanned cell: read_query x datasets (table datasets) |
| 171 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Dr. Carla Singh | VALID | scanned cell: read_query x experiments (table experiments) |
| 172 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `datasets` | Kira Volkov | VALID | scanned cell: read_query x datasets (table datasets) |
| 173 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Hugo Berger | VALID | scanned cell: read_query x experiments (table experiments) |
| 174 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `experiments` | Jonas Lindberg | VALID | scanned cell: read_query x experiments (table experiments) |
| 175 | 24 | 12 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `projects` | Nico Schmidt | VALID | scanned cell: read_query x projects (table projects) |
| 176 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `directory_tree` | `/` | New User | DISCOVERY | scanned cell: directory_tree x / (store-root scope) |
| 177 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory_with_sizes` | `/` | New User | DISCOVERY | scanned cell: list_directory_with_sizes x / (store-root scope) |
| 178 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | New User | DISCOVERY | scanned cell: get_file_info x / (store-root scope) |
| 179 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | Dave (Manager) | VALID | scanned cell: get_file_info x / (store-root scope) |
| 180 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `sensitive/security/` | Eve (Security) | VALID | scanned cell: list_directory x sensitive/security/ (directory scope sensitive/security/) |
| 181 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | Frank (New hire) | VALID | scanned cell: list_directory x / (store-root scope) |
| 182 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_media_file` | `/` | Frank (New hire) | VALID | scanned cell: read_media_file x / (store-root scope) |
| 183 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_text_file` | `/` | Mallory (Attacker) | EDGE | scanned cell: read_text_file x / (store-root scope) |
| 184 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_text_file` | `/` | Mallory (Attacker) | EDGE | scanned cell: read_text_file x / (store-root scope) |
| 185 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | VALID | scanned cell: list_directory x / (store-root scope) |
| 186 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | VALID | scanned cell: list_directory x / (store-root scope) |
| 187 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory_with_sizes` | `/` | — | VALID | scanned cell: list_directory_with_sizes x / (store-root scope) |
| 188 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `directory_tree` | `/` | — | VALID | scanned cell: directory_tree x / (store-root scope) |
| 189 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | VALID | scanned cell: get_file_info x / (store-root scope) |
| 190 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | VALID | scanned cell: get_file_info x / (store-root scope) |
| 191 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | VALID | scanned cell: read_file x / (store-root scope) |
| 192 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_text_file` | `/` | — | VALID | scanned cell: read_text_file x / (store-root scope) |
| 193 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | VALID | scanned cell: read_file x / (store-root scope) |
| 194 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | VALID | scanned cell: list_directory x / (store-root scope) |
| 195 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `search_files` | `/` | — | BAD_PARAMS | scanned cell: search_files x / (store-root scope) |
| 196 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 197 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 198 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | EDGE | scanned cell: list_directory x / (store-root scope) |
| 199 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 200 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 201 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | EDGE | scanned cell: get_file_info x / (store-root scope) |
| 202 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | EDGE | scanned cell: list_directory x / (store-root scope) |
| 203 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 204 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 205 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory` | `/` | — | EDGE | scanned cell: list_directory x / (store-root scope) |
| 206 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `get_file_info` | `/` | — | EDGE | scanned cell: get_file_info x / (store-root scope) |
| 207 | 20 | 20 | 1x | high | high | — | — | fs_corp_filesystem | `read_file` | `/` | — | EDGE | scanned cell: read_file x / (store-root scope) |
| 208 | 20 | 20 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/` | Dr. Smith | BENIGN | scanned cell: list_directory x patients/ (directory scope patients/) |
| 209 | 20 | 20 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory_with_sizes` | `patients/alice_johnson/` | Nurse Adams | BENIGN | scanned cell: list_directory_with_sizes x patients/alice_johnson/ (directory scope patients/alice_johnson/) |
| 210 | 20 | 20 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/` | New Resident | MISUSE | scanned cell: list_directory x patients/ (directory scope patients/) |
| 211 | 20 | 20 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/alice_johnson/` | Clumsy Admin | MISUSE | scanned cell: list_directory x patients/alice_johnson/ (directory scope patients/alice_johnson/) |
| 212 | 20 | 20 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `patients/` | Attacker (Eve) | MALICIOUS | scanned cell: list_directory x patients/ (directory scope patients/) |
| 213 | 20 | 20 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Attacker (Mallory) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 214 | 20 | 20 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 215 | 20 | 20 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 216 | 20 | 20 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 217 | 20 | 20 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 218 | 20 | 20 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Attacker (Mallory) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 219 | 20 | 20 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 220 | 20 | 20 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Attacker (Mallory) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 221 | 20 | 20 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 222 | 20 | 20 | 1x | high | high | — | — | calendar_cbg | `access_contacts` | `contacts` | Insider (Dave) | MALICIOUS | scanned cell: access_contacts x contacts (calendar contacts) |
| 223 | 20 | 20 | 1x | high | high | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Attacker (Eve) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 224 | 20 | 20 | 1x | high | high | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 225 | 20 | 20 | 1x | high | high | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 226 | 20 | 20 | 1x | high | high | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 227 | 20 | 20 | 1x | high | high | — | — | fs_fintech_fs | `directory_tree` | `security/secrets/` | Insider (Mallory) | MALICIOUS | scanned cell: directory_tree x security/secrets/ (directory scope security/secrets/) |
| 228 | 20 | 20 | 1x | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 229 | 20 | 20 | 1x | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 230 | 20 | 20 | 1x | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 231 | 20 | 20 | 1x | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 232 | 20 | 20 | 1x | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 233 | 20 | 20 | 1x | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 234 | 20 | 20 | 1x | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Attacker (Eve) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 235 | 20 | 20 | 1x | high | high | — | — | sqlite_devops_sqlite | `insert_row` | `api_tokens` | Insider (Dave) | MALICIOUS | scanned cell: insert_row x api_tokens (table api_tokens) |
| 236 | 18 | 18 | 1x | high | high | — | — | fs_corp_filesystem | `write_file` | `projects/` | Dave (Manager) | BAD_PARAMS | scanned cell: write_file x projects/ (scope projects/ (ancestor of update.txt)) |
| 237 | 18 | 18 | 1x | medium | medium | — | — | fs_media_studio_fs | `move_file` | `shoots/SHOOT-2026-A/photo_002.jpg` | Attacker (Oscar) | MALICIOUS | scanned cell: move_file x shoots/SHOOT-2026-A/photo_002.jpg (file shoots/SHOOT-2026-A/photo_002.jpg) |
| 238 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 239 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 240 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 241 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 242 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 243 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 244 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 245 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 246 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 247 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 248 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 249 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 250 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 251 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 252 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 253 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 254 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 255 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 256 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 257 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 258 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 259 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 260 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 261 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 262 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 263 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 264 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 265 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 266 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 267 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 268 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 269 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 270 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 271 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 272 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 273 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 274 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 275 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 276 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Scheduler Bot | BENIGN | scanned cell: create_event x team (calendar team) |
| 277 | 18 | 12 | 1.5x | medium | medium | attendees | medium | calendar_cbg | `create_event` | `team` | Exec Assistant | BENIGN | scanned cell: create_event x team (calendar team) |
| 278 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `directory_tree` | `source_code/` | Bob (Dev) | VALID | scanned cell: directory_tree x source_code/ (directory scope source_code/) |
| 279 | 16 | 16 | 1x | high | high | — | — | fs_corp_filesystem | `list_directory_with_sizes` | `sensitive/financials/` | Carol (Finance) | VALID | scanned cell: list_directory_with_sizes x sensitive/financials/ (directory scope sensitive/financials/) |
| 280 | 16 | 16 | 1x | medium | medium | — | — | fs_corp_filesystem | `create_directory` | `source_code/` | Bob (Dev) | VALID | scanned cell: create_directory x source_code/ (scope source_code/ (ancestor of feature_branch)) |
| 281 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `directory_tree` | `billing/` | Receptionist Torres | BENIGN | scanned cell: directory_tree x billing/ (directory scope billing/) |
| 282 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `billing/invoices/` | Receptionist Torres | BENIGN | scanned cell: list_directory x billing/invoices/ (directory scope billing/invoices/) |
| 283 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory_with_sizes` | `billing/` | Billing Staff | MISUSE | scanned cell: list_directory_with_sizes x billing/ (directory scope billing/) |
| 284 | 16 | 16 | 1x | high | high | — | — | fs_medical_clinic_fs | `list_directory` | `billing/` | New Resident | MISUSE | scanned cell: list_directory x billing/ (directory scope billing/) |
| 285 | 16 | 16 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `create_directory` | `billing/` | Attacker (Eve) | MALICIOUS | scanned cell: create_directory x billing/ (scope billing/ (ancestor of staging)) |
| 286 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `directory_tree` | `cases/CASE-2026-001/` | Atty Thompson | BENIGN | scanned cell: directory_tree x cases/CASE-2026-001/ (directory scope cases/CASE-2026-001/) |
| 287 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory_with_sizes` | `clients/` | Paralegal Kim | BENIGN | scanned cell: list_directory_with_sizes x clients/ (directory scope clients/) |
| 288 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory` | `cases/CASE-2026-002/` | Associate Chen | BENIGN | scanned cell: list_directory x cases/CASE-2026-002/ (directory scope cases/CASE-2026-002/) |
| 289 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory_with_sizes` | `billing/timesheets/` | Billing Clerk | MISUSE | scanned cell: list_directory_with_sizes x billing/timesheets/ (directory scope billing/timesheets/) |
| 290 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory` | `cases/` | New Intern | MISUSE | scanned cell: list_directory x cases/ (directory scope cases/) |
| 291 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory` | `clients/` | New Intern | MISUSE | scanned cell: list_directory x clients/ (directory scope clients/) |
| 292 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory` | `billing/` | New Intern | MISUSE | scanned cell: list_directory x billing/ (directory scope billing/) |
| 293 | 16 | 16 | 1x | high | high | — | — | fs_law_firm_fs | `list_directory` | `clients/` | Attacker (Mallory) | MALICIOUS | scanned cell: list_directory x clients/ (directory scope clients/) |
| 294 | 16 | 16 | 1x | medium | medium | — | — | fs_law_firm_fs | `move_file` | `clients/acme_corp/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: move_file x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 295 | 16 | 16 | 1x | medium | medium | — | — | fs_law_firm_fs | `create_directory` | `billing/` | Attacker (Mallory) | MALICIOUS | scanned cell: create_directory x billing/ (scope billing/ (ancestor of staging)) |
| 296 | 16 | 16 | 1x | medium | medium | — | — | fs_law_firm_fs | `move_file` | `cases/CASE-2026-001/signed_agreement.pdf` | Attacker (Mallory) | MALICIOUS | scanned cell: move_file x cases/CASE-2026-001/signed_agreement.pdf (file cases/CASE-2026-001/signed_agreement.pdf) |
| 297 | 16 | 16 | 1x | high | high | — | — | fs_media_studio_fs | `directory_tree` | `clients/` | Account Manager Taylor | BENIGN | scanned cell: directory_tree x clients/ (directory scope clients/) |
| 298 | 16 | 16 | 1x | high | high | — | — | fs_media_studio_fs | `list_directory` | `clients/` | New Hire | MISUSE | scanned cell: list_directory x clients/ (directory scope clients/) |
| 299 | 16 | 16 | 1x | high | high | — | — | fs_media_studio_fs | `list_directory` | `invoices/` | New Hire | MISUSE | scanned cell: list_directory x invoices/ (directory scope invoices/) |
| 300 | 16 | 16 | 1x | high | high | — | — | fs_media_studio_fs | `list_directory_with_sizes` | `invoices/` | Billing Overbroad | MISUSE | scanned cell: list_directory_with_sizes x invoices/ (directory scope invoices/) |
| 301 | 16 | 16 | 1x | high | high | — | — | fs_media_studio_fs | `list_directory` | `clients/` | Admin Overbroad | MISUSE | scanned cell: list_directory x clients/ (directory scope clients/) |
| 302 | 16 | 16 | 1x | medium | medium | — | — | fs_media_studio_fs | `create_directory` | `invoices/` | Attacker (Oscar) | MALICIOUS | scanned cell: create_directory x invoices/ (scope invoices/ (ancestor of staging)) |
| 303 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 304 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 305 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 306 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 307 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 308 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 309 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 310 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 311 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 312 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 313 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 314 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 315 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 316 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Attacker (Mallory) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 317 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 318 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 319 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 320 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 321 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 322 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 323 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 324 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 325 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 326 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 327 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 328 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 329 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 330 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 331 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 332 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 333 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 334 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 335 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 336 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 337 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 338 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 339 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 340 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 341 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 342 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 343 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 344 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 345 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 346 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 347 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 348 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 349 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 350 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 351 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 352 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 353 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 354 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 355 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 356 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 357 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 358 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 359 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 360 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 361 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 362 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 363 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 364 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 365 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 366 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 367 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 368 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 369 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 370 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `executive` | Insider (Dave) | MALICIOUS | scanned cell: list_events x executive (calendar executive) |
| 371 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 372 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Scheduler Bot | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 373 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_calendars` | `personal` | Exec Assistant | BENIGN | scanned cell: list_calendars x personal (calendar personal (default scope)) |
| 374 | 16 | 16 | 1x | high | high | — | — | calendar_cbg | `list_events` | `personal` | Exec Assistant | BENIGN | scanned cell: list_events x personal (calendar personal) |
| 375 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 376 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 377 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 378 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 379 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 380 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 381 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 382 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 383 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 384 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 385 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 386 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 387 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 388 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 389 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 390 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 391 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 392 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 393 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 394 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 395 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 396 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 397 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 398 | 16 | 16 | 1x | medium | medium | — | — | github_cbg | `create_pull_request` | `backend-api` | CI Bot | BENIGN | scanned cell: create_pull_request x backend-api (repo backend-api) |
| 399 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 400 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 401 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 402 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 403 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 404 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 405 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 406 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 407 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 408 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 409 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 410 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 411 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 412 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 413 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 414 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 415 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `exec-private` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x exec-private (channel exec-private) |
| 416 | 16 | 16 | 1x | high | high | — | — | slack_cbg | `slack_get_channel_history` | `hr-internal` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_get_channel_history x hr-internal (channel hr-internal) |
| 417 | 16 | 8 | 2x | high | medium | sql | high | sqlite_cbg_sqlite | `read_query` | `publications` | Farid Hassan | VALID | scanned cell: read_query x publications (table publications) |
| 418 | 12 | 12 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `directory_tree` | `/` | Intern Carter | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 419 | 12 | 12 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `directory_tree` | `/` | New Resident | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 420 | 12 | 12 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `list_directory` | `/` | New Resident | MISUSE | scanned cell: list_directory x / (store-root scope) |
| 421 | 12 | 12 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `list_directory` | `scans/` | New Resident | MISUSE | scanned cell: list_directory x scans/ (directory scope scans/) |
| 422 | 12 | 12 | 1x | medium | medium | — | — | fs_law_firm_fs | `directory_tree` | `/` | Junior Associate | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 423 | 12 | 12 | 1x | medium | medium | — | — | fs_law_firm_fs | `directory_tree` | `/` | New Intern | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 424 | 12 | 12 | 1x | medium | medium | — | — | fs_law_firm_fs | `directory_tree` | `/` | Admin Overbroad | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 425 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `list_directory` | `shoots/SHOOT-2026-A/` | Photographer Alex | BENIGN | scanned cell: list_directory x shoots/SHOOT-2026-A/ (directory scope shoots/SHOOT-2026-A/) |
| 426 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `list_directory_with_sizes` | `shoots/SHOOT-2026-A/` | Art Director Sam | BENIGN | scanned cell: list_directory_with_sizes x shoots/SHOOT-2026-A/ (directory scope shoots/SHOOT-2026-A/) |
| 427 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `list_directory` | `/` | PM Casey | BENIGN | scanned cell: list_directory x / (store-root scope) |
| 428 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `directory_tree` | `/` | New Hire | MISUSE | scanned cell: directory_tree x / (store-root scope) |
| 429 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `list_directory` | `shoots/` | New Hire | MISUSE | scanned cell: list_directory x shoots/ (directory scope shoots/) |
| 430 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `list_directory` | `shoots/SHOOT-2026-A/` | Attacker (Oscar) | MALICIOUS | scanned cell: list_directory x shoots/SHOOT-2026-A/ (directory scope shoots/SHOOT-2026-A/) |
| 431 | 12 | 12 | 1x | medium | medium | — | — | fs_media_studio_fs | `move_file` | `shoots/SHOOT-2026-B/photo_001.jpg` | Attacker (Oscar) | MALICIOUS | scanned cell: move_file x shoots/SHOOT-2026-B/photo_001.jpg (file shoots/SHOOT-2026-B/photo_001.jpg) |
| 432 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 433 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 434 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 435 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 436 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 437 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 438 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 439 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 440 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 441 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 442 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 443 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 444 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 445 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 446 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 447 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 448 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 449 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 450 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 451 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 452 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 453 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 454 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 455 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 456 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 457 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 458 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 459 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 460 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 461 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 462 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 463 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 464 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 465 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 466 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 467 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 468 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 469 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 470 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 471 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 472 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 473 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 474 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 475 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 476 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 477 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 478 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 479 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 480 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 481 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Exec Assistant | BENIGN | scanned cell: list_events x team (calendar team) |
| 482 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 483 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 484 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `list_events` | `team` | Scheduler Bot | BENIGN | scanned cell: list_events x team (calendar team) |
| 485 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 486 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 487 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 488 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Scheduler Bot | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 489 | 12 | 12 | 1x | medium | medium | — | — | calendar_cbg | `find_free_slot` | `team` | Exec Assistant | BENIGN | scanned cell: find_free_slot x team (calendar team) |
| 490 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 491 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 492 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 493 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 494 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 495 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 496 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 497 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 498 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 499 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
| 500 | 12 | 12 | 1x | medium | medium | — | — | github_cbg | `list_commits` | `internal-docs` | CI Bot | BENIGN | scanned cell: list_commits x internal-docs (repo internal-docs) |
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
| 514 | 12 | 8 | 1.5x | medium | medium | paths | medium | fs_media_studio_fs | `read_multiple_files` | `clients/citybank/contract.txt` | PM Casey | BENIGN | scanned cell: read_multiple_files x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 515 | 12 | 8 | 1.5x | medium | medium | paths | medium | fs_media_studio_fs | `read_multiple_files` | `clients/citybank/contract.txt` | Admin Overbroad | MISUSE | scanned cell: read_multiple_files x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 516 | 10 | 10 | 1x | medium | medium | — | — | sqlite_cbg_sqlite | `describe_table` | `api_keys` | New User | DISCOVERY | scanned cell: describe_table x api_keys (table api_keys) |
| 517 | 8 | 8 | 1x | medium | medium | — | — | fs_corp_filesystem | `list_directory` | `onboarding/` | Alice (HR) | VALID | scanned cell: list_directory x onboarding/ (directory scope onboarding/) |
| 518 | 8 | 8 | 1x | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `onboarding/` | Alice (HR) | VALID | scanned cell: read_text_file x onboarding/ (scope onboarding/ (ancestor of policies.pdf)) |
| 519 | 8 | 8 | 1x | medium | medium | — | — | fs_law_firm_fs | `list_directory` | `templates/` | Partner Davis | BENIGN | scanned cell: list_directory x templates/ (directory scope templates/) |
| 520 | 8 | 8 | 1x | medium | medium | — | — | fs_law_firm_fs | `list_directory` | `templates/` | New Intern | MISUSE | scanned cell: list_directory x templates/ (directory scope templates/) |
| 521 | 8 | 8 | 1x | medium | medium | — | — | sqlite_cbg_sqlite | `describe_table` | `employees` | New User | DISCOVERY | scanned cell: describe_table x employees (table employees) |
| 522 | 8 | 8 | 1x | medium | medium | — | — | sqlite_cbg_sqlite | `describe_table` | `grants` | New User | DISCOVERY | scanned cell: describe_table x grants (table grants) |
| 523 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 524 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 525 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 526 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 527 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 528 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 529 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 530 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 531 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 532 | 8 | 8 | 1x | medium | medium | — | — | slack_cbg | `slack_get_channel_history` | `engineering` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x engineering (channel engineering) |
| 533 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 534 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 535 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 536 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 537 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 538 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 539 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 540 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 541 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 542 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 543 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 544 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 545 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 546 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 547 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 548 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 549 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 550 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 551 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 552 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 553 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 554 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 555 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 556 | 8 | 8 | 1x | medium | medium | — | — | fs_fintech_fs | `directory_tree` | `marketing/` | Finance Analyst | BENIGN | scanned cell: directory_tree x marketing/ (directory scope marketing/) |
| 557 | 7.5 | 5 | 1.5x | medium | medium | paths | medium | fs_corp_filesystem | `read_multiple_files` | `sensitive/security/private_key.pem` | Mallory (Attacker) | EDGE | scanned cell: read_multiple_files x sensitive/security/private_key.pem (file sensitive/security/private_key.pem) |
| 558 | 7.5 | 5 | 1.5x | medium | medium | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `patients/alice_johnson/medical_history.txt` | Nurse Adams | BENIGN | scanned cell: read_multiple_files x patients/alice_johnson/medical_history.txt (file patients/alice_johnson/medical_history.txt) |
| 559 | 7.5 | 5 | 1.5x | medium | medium | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `patients/alice_johnson/intake_form.txt` | Intern Carter | MISUSE | scanned cell: read_multiple_files x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 560 | 7.5 | 5 | 1.5x | medium | medium | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `patients/alice_johnson/intake_form.txt` | Clumsy Admin | MISUSE | scanned cell: read_multiple_files x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 561 | 6 | 6 | 1x | low | low | — | — | sqlite_cbg_sqlite | `describe_table` | `projects` | New User | DISCOVERY | scanned cell: describe_table x projects (table projects) |
| 562 | 6 | 6 | 1x | low | low | — | — | sqlite_cbg_sqlite | `describe_table` | `datasets` | New User | DISCOVERY | scanned cell: describe_table x datasets (table datasets) |
| 563 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 564 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 565 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 566 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 567 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 568 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 569 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 570 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 571 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 572 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 573 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 574 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 575 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 576 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 577 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 578 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 579 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 580 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 581 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 582 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 583 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 584 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 585 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 586 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 587 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 588 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 589 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 590 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 591 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 592 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `general` | Attacker (Trudy) | MALICIOUS | scanned cell: slack_post_message x general (channel general) |
| 593 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 594 | 6 | 6 | 1x | medium | medium | — | — | slack_cbg | `slack_post_message` | `announcements` | Support Agent | BENIGN | scanned cell: slack_post_message x announcements (channel announcements) |
| 595 | 6 | 4 | 1.5x | medium | medium | paths | medium | fs_medical_clinic_fs | `read_multiple_files` | `staff_directory.txt` | Nurse Overbroad | MISUSE | scanned cell: read_multiple_files x staff_directory.txt (file staff_directory.txt) |
| 596 | 6 | 4 | 1.5x | medium | medium | paths | medium | fs_law_firm_fs | `read_multiple_files` | `clients/acme_corp/intake.txt` | Paralegal Kim | BENIGN | scanned cell: read_multiple_files x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 597 | 6 | 4 | 1.5x | medium | medium | paths | medium | fs_law_firm_fs | `read_multiple_files` | `cases/CASE-2026-001/contract.txt` | Junior Associate | MISUSE | scanned cell: read_multiple_files x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 598 | 6 | 4 | 1.5x | medium | medium | paths | medium | fs_law_firm_fs | `read_multiple_files` | `clients/acme_corp/intake.txt` | Paralegal Overbroad | MISUSE | scanned cell: read_multiple_files x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 599 | 6 | 4 | 1.5x | medium | medium | paths | medium | fs_law_firm_fs | `read_multiple_files` | `cases/CASE-2026-001/contract.txt` | Admin Overbroad | MISUSE | scanned cell: read_multiple_files x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 600 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 601 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 602 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 603 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 604 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 605 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 606 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 607 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 608 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 609 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 610 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 611 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 612 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 613 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 614 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 615 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 616 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 617 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 618 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 619 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 620 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 621 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 622 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 623 | 6 | 4 | 1.5x | medium | low | sql | medium | sqlite_devops_sqlite | `read_query` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: read_query x public_metrics (table public_metrics) |
| 624 | 5 | 5 | 1x | medium | medium | — | — | fs_corp_filesystem | `get_file_info` | `sensitive/security/private_key.pem` | Eve (Security) | VALID | scanned cell: get_file_info x sensitive/security/private_key.pem (file sensitive/security/private_key.pem) |
| 625 | 5 | 5 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/intake_form.txt` | Dr. Smith | BENIGN | scanned cell: read_text_file x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 626 | 5 | 5 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/intake_form.txt` | Dr. Smith | BENIGN | scanned cell: read_text_file x patients/bob_martinez/intake_form.txt (file patients/bob_martinez/intake_form.txt) |
| 627 | 5 | 5 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/prescription.txt` | Dr. Patel | BENIGN | scanned cell: read_text_file x patients/alice_johnson/prescription.txt (file patients/alice_johnson/prescription.txt) |
| 628 | 5 | 5 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/prescription.txt` | Dr. Patel | BENIGN | scanned cell: read_text_file x patients/bob_martinez/prescription.txt (file patients/bob_martinez/prescription.txt) |
| 629 | 5 | 5 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/intake_form.txt` | New Resident | MISUSE | scanned cell: read_text_file x patients/alice_johnson/intake_form.txt (file patients/alice_johnson/intake_form.txt) |
| 630 | 5 | 5 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/prescription.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/alice_johnson/prescription.txt (file patients/alice_johnson/prescription.txt) |
| 631 | 5 | 5 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/prescription.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/bob_martinez/prescription.txt (file patients/bob_martinez/prescription.txt) |
| 632 | 5 | 5 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/alice_johnson/medical_history.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/alice_johnson/medical_history.txt (file patients/alice_johnson/medical_history.txt) |
| 633 | 5 | 5 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `patients/bob_martinez/prescription.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x patients/bob_martinez/prescription.txt (file patients/bob_martinez/prescription.txt) |
| 634 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 635 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 636 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 637 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 638 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 639 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 640 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 641 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 642 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 643 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `payments-service` | Compromised CI | MALICIOUS | scanned cell: get_file_contents x payments-service (repo payments-service) |
| 644 | 5 | 5 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `infra-config` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_contents x infra-config (repo infra-config) |
| 645 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 646 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 647 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 648 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 649 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 650 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Insider (Mallory) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 651 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 652 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 653 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 654 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 655 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 656 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 657 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 658 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 659 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 660 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Insider (Mallory) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 661 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Insider (Mallory) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 662 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Insider (Mallory) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 663 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_file` | `payments/card_vault/pan_tokens.csv` | Attacker (Eve) | MALICIOUS | scanned cell: read_file x payments/card_vault/pan_tokens.csv (file payments/card_vault/pan_tokens.csv) |
| 664 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_media_file` | `customers/cust_0001/kyc_passport.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x customers/cust_0001/kyc_passport.png (file customers/cust_0001/kyc_passport.png) |
| 665 | 5 | 5 | 1x | medium | medium | — | — | fs_fintech_fs | `read_text_file` | `security/secrets/stripe_api_key.txt` | Insider (Mallory) | MALICIOUS | scanned cell: read_text_file x security/secrets/stripe_api_key.txt (file security/secrets/stripe_api_key.txt) |
| 666 | 4.5 | 3 | 1.5x | medium | low | paths | medium | fs_media_studio_fs | `read_multiple_files` | `project_pipeline.txt` | PM Overbroad | MISUSE | scanned cell: read_multiple_files x project_pipeline.txt (file project_pipeline.txt) |
| 667 | 4 | 4 | 1x | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `source_code/core.c` | Bob (Dev) | VALID | scanned cell: read_text_file x source_code/core.c (file source_code/core.c) |
| 668 | 4 | 4 | 1x | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `sensitive/financials/payslips_q1.csv` | Carol (Finance) | VALID | scanned cell: read_text_file x sensitive/financials/payslips_q1.csv (file sensitive/financials/payslips_q1.csv) |
| 669 | 4 | 4 | 1x | medium | medium | — | — | fs_corp_filesystem | `read_text_file` | `sensitive/security/audit_log.txt` | Eve (Security) | VALID | scanned cell: read_text_file x sensitive/security/audit_log.txt (file sensitive/security/audit_log.txt) |
| 670 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `staff_directory.txt` | Receptionist Torres | BENIGN | scanned cell: read_text_file x staff_directory.txt (file staff_directory.txt) |
| 671 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `get_file_info` | `policies/hipaa_notice.txt` | Admin Nguyen | BENIGN | scanned cell: get_file_info x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 672 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `policies/hipaa_notice.txt` | Admin Nguyen | BENIGN | scanned cell: read_text_file x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 673 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `billing/invoices/inv_2026-05-20_alice_johnson.txt` | Admin Nguyen | BENIGN | scanned cell: read_text_file x billing/invoices/inv_2026-05-20_alice_johnson.txt (file billing/invoices/inv_2026-05-20_alice_johnson.txt) |
| 674 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `billing/invoices/inv_2026-05-20_alice_johnson.txt` | Billing Staff | MISUSE | scanned cell: read_text_file x billing/invoices/inv_2026-05-20_alice_johnson.txt (file billing/invoices/inv_2026-05-20_alice_johnson.txt) |
| 675 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `billing/invoices/inv_2026-05-21_bob_martinez.txt` | Billing Staff | MISUSE | scanned cell: read_text_file x billing/invoices/inv_2026-05-21_bob_martinez.txt (file billing/invoices/inv_2026-05-21_bob_martinez.txt) |
| 676 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_text_file` | `policies/hipaa_notice.txt` | Attacker (Eve) | MALICIOUS | scanned cell: read_text_file x policies/hipaa_notice.txt (file policies/hipaa_notice.txt) |
| 677 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_media_file` | `scans/alice_johnson_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x scans/alice_johnson_xray.png (file scans/alice_johnson_xray.png) |
| 678 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `read_media_file` | `scans/bob_martinez_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: read_media_file x scans/bob_martinez_xray.png (file scans/bob_martinez_xray.png) |
| 679 | 4 | 4 | 1x | medium | medium | — | — | fs_medical_clinic_fs | `get_file_info` | `scans/bob_martinez_xray.png` | Attacker (Eve) | MALICIOUS | scanned cell: get_file_info x scans/bob_martinez_xray.png (file scans/bob_martinez_xray.png) |
| 680 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-001/contract.txt` | Atty Thompson | BENIGN | scanned cell: read_text_file x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 681 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-001/correspondence.txt` | Atty Thompson | BENIGN | scanned cell: read_text_file x cases/CASE-2026-001/correspondence.txt (file cases/CASE-2026-001/correspondence.txt) |
| 682 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `get_file_info` | `templates/nda_template.txt` | Partner Davis | BENIGN | scanned cell: get_file_info x templates/nda_template.txt (file templates/nda_template.txt) |
| 683 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `templates/nda_template.txt` | Partner Davis | BENIGN | scanned cell: read_text_file x templates/nda_template.txt (file templates/nda_template.txt) |
| 684 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-01.txt` | Billing Roberts | BENIGN | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-01.txt (file billing/timesheets/timesheet_2026-05-01.txt) |
| 685 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-15.txt` | Billing Roberts | BENIGN | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-15.txt (file billing/timesheets/timesheet_2026-05-15.txt) |
| 686 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_media_file` | `cases/CASE-2026-002/signed_agreement.pdf` | Associate Chen | BENIGN | scanned cell: read_media_file x cases/CASE-2026-002/signed_agreement.pdf (file cases/CASE-2026-002/signed_agreement.pdf) |
| 687 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-002/correspondence.txt` | Associate Chen | BENIGN | scanned cell: read_text_file x cases/CASE-2026-002/correspondence.txt (file cases/CASE-2026-002/correspondence.txt) |
| 688 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-01.txt` | Billing Clerk | MISUSE | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-01.txt (file billing/timesheets/timesheet_2026-05-01.txt) |
| 689 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `billing/timesheets/timesheet_2026-05-15.txt` | Billing Clerk | MISUSE | scanned cell: read_text_file x billing/timesheets/timesheet_2026-05-15.txt (file billing/timesheets/timesheet_2026-05-15.txt) |
| 690 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-001/contract.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x cases/CASE-2026-001/contract.txt (file cases/CASE-2026-001/contract.txt) |
| 691 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-002/contract.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x cases/CASE-2026-002/contract.txt (file cases/CASE-2026-002/contract.txt) |
| 692 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `templates/nda_template.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x templates/nda_template.txt (file templates/nda_template.txt) |
| 693 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `clients/acme_corp/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x clients/acme_corp/intake.txt (file clients/acme_corp/intake.txt) |
| 694 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_media_file` | `cases/CASE-2026-001/signed_agreement.pdf` | Attacker (Mallory) | MALICIOUS | scanned cell: read_media_file x cases/CASE-2026-001/signed_agreement.pdf (file cases/CASE-2026-001/signed_agreement.pdf) |
| 695 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `get_file_info` | `clients/blue_whale_inc/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: get_file_info x clients/blue_whale_inc/intake.txt (file clients/blue_whale_inc/intake.txt) |
| 696 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `clients/blue_whale_inc/intake.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x clients/blue_whale_inc/intake.txt (file clients/blue_whale_inc/intake.txt) |
| 697 | 4 | 4 | 1x | medium | medium | — | — | fs_law_firm_fs | `read_text_file` | `cases/CASE-2026-002/contract.txt` | Attacker (Mallory) | MALICIOUS | scanned cell: read_text_file x cases/CASE-2026-002/contract.txt (file cases/CASE-2026-002/contract.txt) |
| 698 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `get_file_info` | `clients/citybank/contract.txt` | Account Manager Taylor | BENIGN | scanned cell: get_file_info x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 699 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/citybank/contract.txt` | Account Manager Taylor | BENIGN | scanned cell: read_text_file x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 700 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `invoices/inv_2026-05-15_citybank.txt` | Billing Jordan | BENIGN | scanned cell: read_text_file x invoices/inv_2026-05-15_citybank.txt (file invoices/inv_2026-05-15_citybank.txt) |
| 701 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `invoices/inv_2026-05-21_neon_brand.txt` | Billing Jordan | BENIGN | scanned cell: read_text_file x invoices/inv_2026-05-21_neon_brand.txt (file invoices/inv_2026-05-21_neon_brand.txt) |
| 702 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `invoices/inv_2026-05-15_citybank.txt` | Billing Overbroad | MISUSE | scanned cell: read_text_file x invoices/inv_2026-05-15_citybank.txt (file invoices/inv_2026-05-15_citybank.txt) |
| 703 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/citybank/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x clients/citybank/contract.txt (file clients/citybank/contract.txt) |
| 704 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/neon_brand/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x clients/neon_brand/contract.txt (file clients/neon_brand/contract.txt) |
| 705 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `get_file_info` | `clients/neon_brand/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: get_file_info x clients/neon_brand/contract.txt (file clients/neon_brand/contract.txt) |
| 706 | 4 | 4 | 1x | medium | medium | — | — | fs_media_studio_fs | `read_text_file` | `clients/neon_brand/contract.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x clients/neon_brand/contract.txt (file clients/neon_brand/contract.txt) |
| 707 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 708 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 709 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 710 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 711 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 712 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 713 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 714 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 715 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 716 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 717 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 718 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 719 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 720 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 721 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 722 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 723 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 724 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 725 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 726 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 727 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 728 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 729 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 730 | 4 | 4 | 1x | medium | medium | — | — | github_cbg | `get_file_contents` | `backend-api` | CI Bot | BENIGN | scanned cell: get_file_contents x backend-api (repo backend-api) |
| 731 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 732 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 733 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 734 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 735 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 736 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 737 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 738 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 739 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 740 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 741 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 742 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 743 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 744 | 4 | 4 | 1x | low | low | — | — | slack_cbg | `slack_get_channel_history` | `general` | Support Agent | BENIGN | scanned cell: slack_get_channel_history x general (channel general) |
| 745 | 3 | 3 | 1x | low | low | — | — | fs_corp_filesystem | `read_text_file` | `projects/known_defects.csv` | Dave (Manager) | VALID | scanned cell: read_text_file x projects/known_defects.csv (file projects/known_defects.csv) |
| 746 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_text_file` | `shoots/SHOOT-2026-A/brief.txt` | Photographer Alex | BENIGN | scanned cell: read_text_file x shoots/SHOOT-2026-A/brief.txt (file shoots/SHOOT-2026-A/brief.txt) |
| 747 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_text_file` | `shoots/SHOOT-2026-A/notes.txt` | Photographer Alex | BENIGN | scanned cell: read_text_file x shoots/SHOOT-2026-A/notes.txt (file shoots/SHOOT-2026-A/notes.txt) |
| 748 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_001.jpg` | Art Director Sam | BENIGN | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_001.jpg (file shoots/SHOOT-2026-A/photo_001.jpg) |
| 749 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_002.jpg` | Art Director Sam | BENIGN | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_002.jpg (file shoots/SHOOT-2026-A/photo_002.jpg) |
| 750 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_text_file` | `project_pipeline.txt` | PM Casey | BENIGN | scanned cell: read_text_file x project_pipeline.txt (file project_pipeline.txt) |
| 751 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_001.jpg` | Freelancer Overbroad | MISUSE | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_001.jpg (file shoots/SHOOT-2026-A/photo_001.jpg) |
| 752 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-A/photo_002.jpg` | Freelancer Overbroad | MISUSE | scanned cell: read_media_file x shoots/SHOOT-2026-A/photo_002.jpg (file shoots/SHOOT-2026-A/photo_002.jpg) |
| 753 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-B/photo_001.jpg` | Freelancer Overbroad | MISUSE | scanned cell: read_media_file x shoots/SHOOT-2026-B/photo_001.jpg (file shoots/SHOOT-2026-B/photo_001.jpg) |
| 754 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_text_file` | `project_pipeline.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x project_pipeline.txt (file project_pipeline.txt) |
| 755 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_media_file` | `shoots/SHOOT-2026-B/photo_001.jpg` | Attacker (Oscar) | MALICIOUS | scanned cell: read_media_file x shoots/SHOOT-2026-B/photo_001.jpg (file shoots/SHOOT-2026-B/photo_001.jpg) |
| 756 | 3 | 3 | 1x | low | low | — | — | fs_media_studio_fs | `read_text_file` | `shoots/SHOOT-2026-B/notes.txt` | Attacker (Oscar) | MALICIOUS | scanned cell: read_text_file x shoots/SHOOT-2026-B/notes.txt (file shoots/SHOOT-2026-B/notes.txt) |
| 757 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 758 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 759 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 760 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 761 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 762 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 763 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 764 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 765 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 766 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 767 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 768 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 769 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 770 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 771 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 772 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 773 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 774 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 775 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 776 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 777 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 778 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 779 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 780 | 3 | 3 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `marketing/launch_2026.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x marketing/launch_2026.md (file marketing/launch_2026.md) |
| 781 | 2 | 2 | 1x | low | low | — | — | fs_corp_filesystem | `read_media_file` | `onboarding/org_chart.png` | Alice (HR) | VALID | scanned cell: read_media_file x onboarding/org_chart.png (file onboarding/org_chart.png) |
| 782 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 783 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 784 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 785 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 786 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 787 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 788 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 789 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 790 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 791 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 792 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 793 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 794 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 795 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 796 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 797 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 798 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 799 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 800 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 801 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 802 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 803 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 804 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 805 | 2 | 2 | 1x | low | low | — | — | sqlite_devops_sqlite | `describe_table` | `public_metrics` | Analytics Bot | BENIGN | scanned cell: describe_table x public_metrics (table public_metrics) |
| 806 | 1 | 1 | 1x | low | low | — | — | fs_corp_filesystem | `read_text_file` | `README.md` | Frank (New hire) | VALID | scanned cell: read_text_file x README.md (file README.md) |
| 807 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 808 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 809 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 810 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 811 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 812 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 813 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 814 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 815 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 816 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 817 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 818 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 819 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 820 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 821 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 822 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 823 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 824 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 825 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 826 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 827 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 828 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 829 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
| 830 | 1 | 1 | 1x | low | low | — | — | fs_fintech_fs | `read_text_file` | `README.md` | Finance Analyst | BENIGN | scanned cell: read_text_file x README.md (file README.md) |
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
