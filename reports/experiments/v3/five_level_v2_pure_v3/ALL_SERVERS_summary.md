# Pure v3 — all four MCPs (tools + description only, roofs on)

Every scan's ONLY inputs: the captured tool catalog + the org profile. Score = sensitivity × blast × impact (max 125). Bands: low <17 · medium 17–49 · high 50–99 · critical ≥100. Deterministic rules: bulk-twin dominance, alias twins, sens+impact floors, blast roofs (impact≤3 reads capped, escape-flag assets exempt).

| Server | Tools×Assets | low | medium | high | critical | N/A | floored | roofed | bulk |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `calendar:real` | 13×16 | 19 | 45 | 8 | 2 | 134 | 25 | 3 | 3 |
| `slack:real` | 16×20 | 47 | 52 | 12 | 7 | 202 | 27 | 0 | 0 |
| `github:real` | 26×20 | 58 | 81 | 20 | 21 | 340 | 43 | 0 | 0 |
| `fs:corp_filesystem` | 14×22 | 91 | 61 | 38 | 15 | 103 | 20 | 0 | 8 |

## calendar:real — top cells

| Asset | Tool | Sens | Blast | Impact | Score | Band |
|---|---|:-:|:-:|:-:|-:|---|
| `connected-account-config` | `manage-accounts` | 5 | 5 | 5 | 125 | critical |
| `account-directory` | `manage-accounts` | 4 | 5 | 5 | 100 | critical |
| `recruiting` | `create-events` | 4 | 4 | 5 | 80 | high |
| `executive` | `create-events` | 4 | 4 | 5 | 80 | high |
| `event-attendee-lists` | `create-events` | 4 | 4 | 5 | 80 | high |
| `recruiting` | `respond-to-event` | 4 | 3 | 5 | 60 | high |
| `recruiting` | `delete-event` | 4 | 3 | 5 | 60 | high |
| `executive` | `respond-to-event` | 4 | 3 | 5 | 60 | high |
| `executive` | `delete-event` | 4 | 3 | 5 | 60 | high |
| `event-attendee-lists` | `delete-event` | 4 | 3 | 5 | 60 | high |
| `recruiting` | `update-event` | 4 | 3 | 4 | 48 | medium |
| `recruiting` | `search-events` | 4 | 4 | 3 | 48 | medium |

## slack:real — top cells

| Asset | Tool | Sens | Blast | Impact | Score | Band |
|---|---|:-:|:-:|:-:|-:|---|
| `usergroup-membership` | `usergroups_users_update` | 4 | 5 | 5 | 100 | critical |
| `user-group-membership` | `usergroups_users_update` | 4 | 5 | 5 | 100 | critical |
| `on-call` | `usergroups_users_update` | 4 | 5 | 5 | 100 | critical |
| `incident-response` | `usergroups_users_update` | 4 | 5 | 5 | 100 | critical |
| `hr-internal` | `usergroups_users_update` | 4 | 5 | 5 | 100 | critical |
| `hr-internal` | `conversations_join` | 4 | 5 | 5 | 100 | critical |
| `exec-private` | `usergroups_users_update` | 4 | 5 | 5 | 100 | critical |
| `team-leads` | `usergroups_users_update` | 4 | 4 | 5 | 80 | high |
| `team-leads` | `conversations_join` | 4 | 4 | 5 | 80 | high |
| `on-call` | `conversations_join` | 4 | 4 | 5 | 80 | high |
| `incident-response` | `conversations_join` | 4 | 4 | 5 | 80 | high |
| `exec-private` | `conversations_join` | 4 | 4 | 5 | 80 | high |

## github:real — top cells

| Asset | Tool | Sens | Blast | Impact | Score | Band |
|---|---|:-:|:-:|:-:|-:|---|
| `infra-config` | `push_files` | 5 | 5 | 5 | 125 | critical |
| `infra-config` | `merge_pull_request` | 5 | 5 | 5 | 125 | critical |
| `infra-config` | `fork_repository` | 5 | 5 | 5 | 125 | critical |
| `infra-config` | `create_or_update_file` | 5 | 5 | 5 | 125 | critical |
| `repository-contents` | `merge_pull_request` | 4 | 5 | 5 | 100 | critical |
| `repository-contents` | `fork_repository` | 4 | 5 | 5 | 100 | critical |
| `payments-service` | `push_files` | 4 | 5 | 5 | 100 | critical |
| `payments-service` | `merge_pull_request` | 4 | 5 | 5 | 100 | critical |
| `payments-service` | `fork_repository` | 4 | 5 | 5 | 100 | critical |
| `payments-service` | `create_or_update_file` | 4 | 5 | 5 | 100 | critical |
| `org-external-copies` | `fork_repository` | 4 | 5 | 5 | 100 | critical |
| `ml-research` | `merge_pull_request` | 4 | 5 | 5 | 100 | critical |

## fs:corp_filesystem — top cells

| Asset | Tool | Sens | Blast | Impact | Score | Band |
|---|---|:-:|:-:|:-:|-:|---|
| `sensitive/security/private_key.pem` | `write_file` | 5 | 5 | 5 | 125 | critical |
| `sensitive/security/` | `write_file` | 5 | 5 | 5 | 125 | critical |
| `sensitive/` | `write_file` | 5 | 5 | 5 | 125 | critical |
| `source_code/core.c` | `write_file` | 4 | 5 | 5 | 100 | critical |
| `source_code/` | `write_file` | 4 | 5 | 5 | 100 | critical |
| `sensitive/security/private_key.pem` | `move_file` | 5 | 5 | 4 | 100 | critical |
| `sensitive/security/private_key.pem` | `edit_file` | 5 | 5 | 4 | 100 | critical |
| `sensitive/security/audit_log.txt` | `write_file` | 4 | 5 | 5 | 100 | critical |
| `sensitive/security/` | `move_file` | 5 | 5 | 4 | 100 | critical |
| `sensitive/security/` | `edit_file` | 5 | 5 | 4 | 100 | critical |
| `sensitive/financials/payslips_q1.csv` | `write_file` | 4 | 5 | 5 | 100 | critical |
| `sensitive/financials/` | `write_file` | 4 | 5 | 5 | 100 | critical |

