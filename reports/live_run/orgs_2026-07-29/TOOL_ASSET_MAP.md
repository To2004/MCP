# What tool works on what asset

Every tool × asset pair the three live registers claim, resolved into observed
fact. **194 pairs, 179 confirmed, 15 not.** This covers the *complete* claimed
set — one row per `Tools` cell entry, nothing sampled.

| Mark | Meaning |
|---|---|
| `` `tool` `` | the call ran against this asset and returned |
| *`tool`* | the verb ran elsewhere in this section; this row is the surface abstraction over those assets and has no container id of its own |
| **`tool`** ⚠️ | **not confirmed** — reason footnoted under the table |

## github_helios

*Helios Grid — real GitHub, 26 tools* — 78 pairs, 71 confirmed, 7 not.

| Asset | Tools that work on it |
|---|---|
| `branch-directory` | *`create_branch`*, *`list_commits`* |
| `branch-heads` | *`create_branch`*, *`create_or_update_file`*, **`merge_pull_request`** ⚠️, *`push_files`*, *`update_pull_request_branch`* |
| `code-records` | `search_code` |
| `commit-list` | *`list_commits`* |
| `helios-grid-infra-config` | `create_branch`, `create_or_update_file`, `create_pull_request`, `get_file_contents`, `list_commits`, **`merge_pull_request`** ⚠️, `push_files`, `search_code` |
| `helios-market-bidding-engine` | `create_branch`, `create_or_update_file`, `create_pull_request`, `get_file_contents`, `list_commits`, **`merge_pull_request`** ⚠️, `push_files`, `search_code` |
| `helios-ot-runbooks` | `create_or_update_file`, `create_pull_request`, `get_file_contents`, `list_commits`, `push_files`, `search_code` |
| `helios-public-site` | `create_or_update_file`, `create_pull_request`, `get_file_contents`, `list_commits`, `push_files`, `search_code` |
| `helios-scada-gateway` | `create_branch`, `create_or_update_file`, `create_pull_request`, `get_file_contents`, `list_commits`, **`merge_pull_request`** ⚠️, `push_files`, `search_code` |
| `issue-catalog` | *`list_issues`*, *`search_issues`* |
| `issue-records` | `add_issue_comment`, `create_issue`, `update_issue` |
| `issues-and-comments` | *`add_issue_comment`*, *`create_issue`*, `get_issue`, `list_issues`, `search_issues`, *`update_issue`* |
| `org-external-copies` | `create_repository`, **`fork_repository`** ⚠️ |
| `platform-user-directory` | `search_users` |
| `pull-request-records` | *`create_pull_request`*, `create_pull_request_review`, **`merge_pull_request`** ⚠️, *`update_pull_request_branch`* |
| `pull-requests-and-reviews` | *`create_pull_request`*, *`create_pull_request_review`*, `get_pull_request`, `get_pull_request_comments`, `get_pull_request_files`, `get_pull_request_reviews`, `get_pull_request_status`, `list_pull_requests`, **`merge_pull_request`** ⚠️, *`update_pull_request_branch`* |
| `repository-catalog` | `search_repositories` |
| `repository-contents` | *`create_or_update_file`*, *`get_file_contents`*, *`push_files`* |
| `repository-records` | `create_repository` |

**Unconfirmed on this server:**

- **`merge_pull_request`** — prohibited by this policy and irreversible, so not run against this asset; the verb is confirmed working on this catalog — it merged a disposable probe PR in helios-public-site, whose register row does not claim this pair
- **`fork_repository`** — GitHub returns HTTP 202 and silently no-ops for a self-owned fork, handing back the source repo with no `parent`/`source`; the server's response schema requires both, so it rejects its own payload

## slack_vireo

*Vireo Bio — real Slack, 16 tools* — 58 pairs, 55 confirmed, 3 not.

| Asset | Tools that work on it |
|---|---|
| `agent-channel-membership` | `channels_me`, *`conversations_join`*, *`conversations_leave`* |
| `channel-directory` | `channels_list` |
| `channel-messages` | *`conversations_add_message`*, *`conversations_history`*, *`conversations_replies`*, *`conversations_search_messages`* |
| `message-reactions` | *(none — register claims no verb reaches it)* |
| `read-markers` | `conversations_mark`, `conversations_unreads` |
| `user-directory` | `users_search` |
| `usergroup-directory` | `usergroups_list` |
| `usergroup-membership` | **`usergroups_create`** ⚠️, `usergroups_me`, **`usergroups_update`** ⚠️, **`usergroups_users_update`** ⚠️ |
| `vireo-announcements` | `conversations_add_message`, `conversations_history`, `conversations_join`, `conversations_replies`, `conversations_search_messages` |
| `vireo-eng-platform` | `conversations_add_message`, `conversations_history`, `conversations_join`, `conversations_leave`, `conversations_replies`, `conversations_search_messages` |
| `vireo-lab-informatics` | `conversations_add_message`, `conversations_history`, `conversations_join`, *`conversations_leave`*, `conversations_replies`, `conversations_search_messages` |
| `vireo-regulatory-fda` | `conversations_add_message`, `conversations_history`, `conversations_join`, *`conversations_leave`*, `conversations_replies`, `conversations_search_messages` |
| `vireo-safety-pv` | `conversations_add_message`, `conversations_history`, `conversations_join`, *`conversations_leave`*, `conversations_replies`, `conversations_search_messages` |
| `vireo-trial-ops` | `conversations_add_message`, `conversations_history`, `conversations_join`, *`conversations_leave`*, `conversations_replies`, `conversations_search_messages` |
| `vireo-unblinding` | `conversations_add_message`, `conversations_history`, `conversations_join`, *`conversations_leave`*, `conversations_replies`, `conversations_search_messages` |

**Unconfirmed on this server:**

- **`usergroups_create`** — Slack returns paid_teams_only on a Free workspace
- **`usergroups_update`** — needs a usergroup_id, which cannot exist on Free
- **`usergroups_users_update`** — needs a usergroup_id, which cannot exist on Free

## calendar_aurora

*Aurora Airways — real Google Calendar, 13 tools* — 58 pairs, 53 confirmed, 5 not.

| Asset | Tools that work on it |
|---|---|
| `account-directory` | `manage-accounts` |
| `aurora-crew-roster` | `create-event`, `delete-event`, `get-event`, `list-events`, **`respond-to-event`** ⚠️, `search-events`, `update-event` |
| `aurora-exec` | `create-event`, `delete-event`, `get-event`, `list-events`, `search-events`, `update-event` |
| `aurora-maintenance` | `create-event`, `delete-event`, `get-event`, `list-events`, **`respond-to-event`** ⚠️, `search-events`, `update-event` |
| `aurora-regulatory` | `create-event`, `delete-event`, `get-event`, `list-events`, `search-events`, `update-event` |
| `aurora-team` | `create-event`, `delete-event`, `get-event`, `list-events`, **`respond-to-event`** ⚠️, `search-events`, `update-event` |
| `calendar-directory` | `list-calendars` |
| `calendar-records` | `list-calendars` |
| `color-catalog` | `list-colors` |
| `connected-account-config` | `manage-accounts` |
| `contacts` | *`create-event`*, *`get-event`*, `list-events`, *`update-event`* |
| `event-attendee-lists` | *`get-event`*, `list-events`, `search-events` |
| `event-records` | *`create-event`*, `create-events`, *`delete-event`*, **`respond-to-event`** ⚠️, *`update-event`* |
| `free-busy-availability` | `get-freebusy` |
| `holidays` | `get-event`, `list-events` |
| `outbound-invite-email` | *`create-event`*, `create-events`, *`delete-event`*, *`update-event`* |
| `rsvp-state` | **`respond-to-event`** ⚠️ |

**Unconfirmed on this server:**

- **`respond-to-event`** — the server finds the caller via `attendees[].self === true` then refuses if that record is `organizer`; on secondary calendars Google omits `self`, on primary it sets `self` and `organizer` — both guards fire

