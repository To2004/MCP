# Risk matrix — final scores

Independent Claude baseline, scored from tool/asset semantics only (no scan prompts). Rows are **container/scope assets** first, then **mutable-state assets** (tagged `·state` — the state each write tool can change), then **read-surface assets** (tagged `·read` — state no tool mutates but read tools expose, including the per-kind catalogs). Each cell is the final risk score (0-100); `na` = the tool does not act on that asset. Bands are absolute: 🔴 >=80 . 🟠 >=60 . 🟡 >=35 . 🟢 else.

Updated 2026-07-22: added the catalog assets (`repository-catalog`, `channel-directory`, `calendar-directory`) so every discovery tool is homed; only the two true utility tools (`list-colors`, `get-current-time`) remain all-`na`.

## github

| asset \ tool | create_or_update_file | search_repositories | create_repository | get_file_contents | push_files | create_issue | create_pull_request | fork_repository | create_branch | list_commits | list_issues | update_issue | add_issue_comment | search_code | search_issues | search_users | get_issue | get_pull_request | list_pull_requests | create_pull_request_review | merge_pull_request | get_pull_request_files | get_pull_request_status | update_pull_request_branch | get_pull_request_comments | get_pull_request_reviews |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 6 🟢 | na | na | 4 🟢 | 12 🟢 | 2 🟢 | 4 🟢 | 12 🟢 | 2 🟢 | 4 🟢 | 4 🟢 | 3 🟢 | 3 🟢 | 8 🟢 | 4 🟢 | na | 2 🟢 | 2 🟢 | 4 🟢 | 3 🟢 | 12 🟢 | 4 🟢 | 2 🟢 | 6 🟢 | 2 🟢 | 2 🟢 |
| `internal-docs` | 18 🟢 | na | na | 12 🟢 | 36 🟡 | 6 🟢 | 12 🟢 | 36 🟡 | 6 🟢 | 12 🟢 | 12 🟢 | 9 🟢 | 9 🟢 | 24 🟢 | 12 🟢 | na | 6 🟢 | 6 🟢 | 12 🟢 | 9 🟢 | 36 🟡 | 12 🟢 | 6 🟢 | 18 🟢 | 6 🟢 | 6 🟢 |
| `backend-api` | 24 🟢 | na | na | 16 🟢 | 48 🟡 | 8 🟢 | 16 🟢 | 48 🟡 | 8 🟢 | 16 🟢 | 16 🟢 | 12 🟢 | 12 🟢 | 32 🟢 | 16 🟢 | na | 8 🟢 | 8 🟢 | 16 🟢 | 12 🟢 | 48 🟡 | 16 🟢 | 8 🟢 | 24 🟢 | 8 🟢 | 8 🟢 |
| `payments-service` | 30 🟢 | na | na | 20 🟢 | 60 🟠 | 10 🟢 | 20 🟢 | 60 🟠 | 10 🟢 | 20 🟢 | 20 🟢 | 15 🟢 | 15 🟢 | 40 🟡 | 20 🟢 | na | 10 🟢 | 10 🟢 | 20 🟢 | 15 🟢 | 60 🟠 | 20 🟢 | 10 🟢 | 30 🟢 | 10 🟢 | 10 🟢 |
| `infra-config` | 30 🟢 | na | na | 20 🟢 | 60 🟠 | 10 🟢 | 20 🟢 | 60 🟠 | 10 🟢 | 20 🟢 | 20 🟢 | 15 🟢 | 15 🟢 | 40 🟡 | 20 🟢 | na | 10 🟢 | 10 🟢 | 20 🟢 | 15 🟢 | 60 🟠 | 20 🟢 | 10 🟢 | 30 🟢 | 10 🟢 | 10 🟢 |
| `ml-research` | 24 🟢 | na | na | 16 🟢 | 48 🟡 | 8 🟢 | 16 🟢 | 48 🟡 | 8 🟢 | 16 🟢 | 16 🟢 | 12 🟢 | 12 🟢 | 32 🟢 | 16 🟢 | na | 8 🟢 | 8 🟢 | 16 🟢 | 12 🟢 | 48 🟡 | 16 🟢 | 8 🟢 | 24 🟢 | 8 🟢 | 8 🟢 |
| `branch-heads` ·state | 24 🟢 | na | na | 16 🟢 | 48 🟡 | na | na | na | 8 🟢 | 16 🟢 | na | na | na | 32 🟢 | na | na | na | na | na | na | 48 🟡 | na | na | 24 🟢 | na | na |
| `issues-and-comments` ·state | na | na | na | na | na | 4 🟢 | na | na | na | na | 8 🟢 | 6 🟢 | 6 🟢 | na | 8 🟢 | na | 4 🟢 | na | na | na | na | na | na | na | 4 🟢 | na |
| `pull-requests-and-reviews` ·state | na | na | na | na | na | na | 12 🟢 | na | na | na | na | na | na | na | na | na | na | 6 🟢 | 12 🟢 | 9 🟢 | 36 🟡 | 12 🟢 | 6 🟢 | 18 🟢 | 6 🟢 | 6 🟢 |
| `org-external-copies` ·state | na | na | 8 🟢 | na | na | na | na | 48 🟡 | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na |
| `platform-user-directory` ·read | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | 4 🟢 | na | na | na | na | na | na | na | na | na | na |
| `repository-catalog` ·read | na | 4 🟢 | 2 🟢 | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na |

## slack

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | na | na | 3 🟢 | 8 🟢 | 2 🟢 | 3 🟢 | 8 🟢 | 4 🟢 | 8 🟢 | 6 🟢 | na | na | na | na | na | na |
| `announcements` | na | na | 3 🟢 | 8 🟢 | 2 🟢 | 3 🟢 | 8 🟢 | 4 🟢 | 8 🟢 | 6 🟢 | na | na | na | na | na | na |
| `random` | na | na | 3 🟢 | 8 🟢 | 2 🟢 | 3 🟢 | 8 🟢 | 4 🟢 | 8 🟢 | 6 🟢 | na | na | na | na | na | na |
| `engineering` | na | na | 6 🟢 | 16 🟢 | 4 🟢 | 6 🟢 | 16 🟢 | 8 🟢 | 16 🟢 | 12 🟢 | na | na | na | na | na | na |
| `incident-response` | na | na | 12 🟢 | 32 🟢 | 8 🟢 | 12 🟢 | 32 🟢 | 16 🟢 | 32 🟢 | 24 🟢 | na | na | na | na | na | na |
| `on-call` | na | na | 12 🟢 | 32 🟢 | 8 🟢 | 12 🟢 | 32 🟢 | 16 🟢 | 32 🟢 | 24 🟢 | na | na | na | na | na | na |
| `research-team` | na | na | 9 🟢 | 24 🟢 | 6 🟢 | 9 🟢 | 24 🟢 | 12 🟢 | 24 🟢 | 18 🟢 | na | na | na | na | na | na |
| `exec-private` | na | na | 15 🟢 | 40 🟡 | 10 🟢 | 15 🟢 | 40 🟡 | 20 🟢 | 40 🟡 | 30 🟢 | na | na | na | na | na | na |
| `hr-internal` | na | na | 15 🟢 | 40 🟡 | 10 🟢 | 15 🟢 | 40 🟡 | 20 🟢 | 40 🟡 | 30 🟢 | na | na | na | na | na | na |
| `team-leads` | na | na | 12 🟢 | 32 🟢 | 8 🟢 | 12 🟢 | 32 🟢 | 16 🟢 | 32 🟢 | 24 🟢 | na | na | na | na | na | na |
| `channel-messages` ·state | na | na | 9 🟢 | 24 🟢 | na | na | na | 12 🟢 | 24 🟢 | 18 🟢 | na | na | na | na | na | na |
| `message-reactions` ·state | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na |
| `read-markers` ·state | na | na | na | na | na | na | 16 🟢 | na | na | 12 🟢 | na | na | na | na | na | na |
| `usergroup-membership` ·state | na | na | na | na | na | na | na | na | na | na | 8 🟢 | 16 🟢 | 12 🟢 | 24 🟢 | 60 🟠 | na |
| `agent-channel-membership` ·state | na | 6 🟢 | na | na | 6 🟢 | 9 🟢 | na | na | na | na | na | na | na | na | na | na |
| `user-directory` ·read | na | na | na | na | na | na | na | na | na | na | na | na | na | na | na | 16 🟢 |
| `channel-directory` ·read | 8 🟢 | 4 🟢 | na | na | na | na | na | na | na | na | na | na | na | na | na | na |

## calendar

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | na | 24 🟢 | 18 🟢 | 6 🟢 | na | 12 🟢 | 36 🟡 | 9 🟢 | 15 🟢 | 12 🟢 | na | 9 🟢 | na |
| `team` | na | 24 🟢 | 18 🟢 | 6 🟢 | na | 12 🟢 | 36 🟡 | 9 🟢 | 15 🟢 | 12 🟢 | na | 9 🟢 | na |
| `executive` | na | 40 🟡 | 30 🟢 | 10 🟢 | na | 20 🟢 | 60 🟠 | 15 🟢 | 25 🟢 | 20 🟢 | na | 15 🟢 | na |
| `recruiting` | na | 32 🟢 | 24 🟢 | 8 🟢 | na | 16 🟢 | 48 🟡 | 12 🟢 | 20 🟢 | 16 🟢 | na | 12 🟢 | na |
| `contacts` | na | 32 🟢 | 24 🟢 | 8 🟢 | na | 16 🟢 | 48 🟡 | 12 🟢 | 20 🟢 | 16 🟢 | na | 12 🟢 | na |
| `holidays` | na | 8 🟢 | 6 🟢 | 2 🟢 | na | 4 🟢 | 12 🟢 | 3 🟢 | 5 🟢 | 4 🟢 | na | 3 🟢 | na |
| `event-records` ·state | na | 24 🟢 | 18 🟢 | 6 🟢 | na | 12 🟢 | 36 🟡 | 9 🟢 | 15 🟢 | na | na | na | na |
| `event-attendee-lists` ·state | na | na | na | 8 🟢 | na | 16 🟢 | 48 🟡 | 12 🟢 | na | na | na | na | na |
| `outbound-invite-email` ·state | na | na | na | na | na | 12 🟢 | 36 🟡 | 9 🟢 | na | na | na | 9 🟢 | na |
| `rsvp-state` ·state | na | na | na | na | na | na | na | na | na | na | na | 6 🟢 | na |
| `connected-account-config` ·state | na | na | na | na | na | na | na | na | na | na | na | na | 30 🟢 |
| `free-busy-availability` ·read | na | na | na | na | na | na | na | na | na | 12 🟢 | na | na | na |
| `calendar-directory` ·read | 4 🟢 | na | na | na | na | na | na | na | na | na | na | na | na |
