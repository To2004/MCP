# v4 — all five servers (short standards-grounded prompts, tools+description only)

Scanner inputs: the captured tool catalog + the org profile, nothing else.
Prompts: impact 2 322 chars (tool JSON alone, no profile/domain), blast 2 781 chars
(CVSS vulnerable-vs-subsequent framing + sibling tool/asset lists; a tier-5 escape
requires a flag in the org table). Score = sensitivity × blast × impact, max 125.
Bands are pure score thresholds: low <17 · medium 17–49 · high 50–99 · critical ≥100.

| Server | Tools×Assets | low | medium | high | critical | N/A | floored | bulk |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| `calendar:real` | 13×16 | 25 | 45 | 9 | 1 | 128 | 29 | 2 |
| `slack:real` | 16×20 | 56 | 45 | 18 | 4 | 197 | 31 | 0 |
| `github:real` | 26×20 | 69 | 59 | 32 | 11 | 349 | 39 | 0 |
| `fs:corp_filesystem` | 14×22 | 85 | 54 | 44 | 14 | 111 | 25 | 8 |
| `sqlite:cbg_sqlite` | 5×11 | 12 | 19 | 3 | 4 | 17 | 7 | 0 |

## calendar:real — top cells

| Asset | Tool | Sens | Blast | Impact | Score | Band |
|---|---|:-:|:-:|:-:|-:|---|
| `connected-account-config` | `manage-accounts` | 5 | 5 | 5 | 125 | critical |
| `event-attendee-lists` | `create-events` | 4 | 5 | 4 | 80 | high |
| `event-attendee-lists` | `create-event` | 4 | 5 | 4 | 80 | high |
| `account-directory` | `manage-accounts` | 4 | 4 | 5 | 80 | high |
| `recruiting` | `create-events` | 4 | 4 | 4 | 64 | high |
| `executive` | `create-events` | 4 | 4 | 4 | 64 | high |
| `recruiting` | `delete-event` | 4 | 3 | 5 | 60 | high |
| `executive` | `delete-event` | 4 | 3 | 5 | 60 | high |
| `event-attendee-lists` | `list-events` | 4 | 5 | 3 | 60 | high |
| `event-attendee-lists` | `delete-event` | 4 | 3 | 5 | 60 | high |

## slack:real — top cells

| Asset | Tool | Sens | Blast | Impact | Score | Band |
|---|---|:-:|:-:|:-:|-:|---|
| `usergroup-membership` | `usergroups_users_update` | 4 | 5 | 5 | 100 | critical |
| `user-group-membership` | `usergroups_users_update` | 4 | 5 | 5 | 100 | critical |
| `incident-response` | `usergroups_users_update` | 4 | 5 | 5 | 100 | critical |
| `channel-messages` | `usergroups_users_update` | 4 | 5 | 5 | 100 | critical |
| `exec-private` | `usergroups_users_update` | 4 | 4 | 5 | 80 | high |
| `channel-messages` | `conversations_join` | 4 | 5 | 4 | 80 | high |
| `incident-response` | `conversations_join` | 4 | 4 | 4 | 64 | high |
| `exec-private` | `conversations_join` | 4 | 4 | 4 | 64 | high |
| `channel-messages` | `conversations_add_message` | 4 | 4 | 4 | 64 | high |
| `agent-channel-membership` | `conversations_join` | 4 | 4 | 4 | 64 | high |

## github:real — top cells

| Asset | Tool | Sens | Blast | Impact | Score | Band |
|---|---|:-:|:-:|:-:|-:|---|
| `infra-config` | `merge_pull_request` | 5 | 5 | 5 | 125 | critical |
| `infra-config` | `create_or_update_file` | 5 | 5 | 5 | 125 | critical |
| `payments-service` | `merge_pull_request` | 4 | 5 | 5 | 100 | critical |
| `payments-service` | `create_or_update_file` | 4 | 5 | 5 | 100 | critical |
| `infra-config` | `update_pull_request_branch` | 5 | 5 | 4 | 100 | critical |
| `infra-config` | `push_files` | 5 | 5 | 4 | 100 | critical |
| `infra-config` | `fork_repository` | 5 | 5 | 4 | 100 | critical |
| `branch-heads` | `merge_pull_request` | 4 | 5 | 5 | 100 | critical |
| `branch-heads` | `create_or_update_file` | 4 | 5 | 5 | 100 | critical |
| `backend-api` | `merge_pull_request` | 4 | 5 | 5 | 100 | critical |

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
| `sensitive/security/` | `move_file` | 5 | 5 | 4 | 100 | critical |
| `sensitive/security/` | `edit_file` | 5 | 5 | 4 | 100 | critical |
| `sensitive/financials/payslips_q1.csv` | `write_file` | 4 | 5 | 5 | 100 | critical |

## sqlite:cbg_sqlite — top cells

| Asset | Tool | Sens | Blast | Impact | Score | Band |
|---|---|:-:|:-:|:-:|-:|---|
| `api_keys` | `write_query` | 5 | 5 | 5 | 125 | critical |
| `employees` | `write_query` | 4 | 5 | 5 | 100 | critical |
| `database-records` | `write_query` | 4 | 5 | 5 | 100 | critical |
| `api_keys` | `insert_row` | 5 | 5 | 4 | 100 | critical |
| `grants` | `write_query` | 4 | 4 | 5 | 80 | high |
| `database-records` | `insert_row` | 4 | 5 | 4 | 80 | high |
| `database-records` | `read_query` | 4 | 5 | 3 | 60 | high |
| `grants` | `insert_row` | 4 | 3 | 4 | 48 | medium |
| `employees` | `read_query` | 4 | 4 | 3 | 48 | medium |
| `employees` | `insert_row` | 4 | 3 | 4 | 48 | medium |

