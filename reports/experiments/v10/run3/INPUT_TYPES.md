# Tool Inputs: ranges and policy lookups

Run `run3` — prompt in `prompt-AS-RUN.md` beside this file.
Qwen2.5:32b, greedy, seed 0.
A ✓ marks an input whose legitimate values cannot be known from the tool
definition — the dynamic layer must check it against the organisation's
policy. Blank rows are prose, opaque tokens or small fixed choices.

## github

| tool | input | measures | low / medium / high | absent | policy |
|---|---|---|---|---|---|
| `add_issue_comment` | `owner` | — | — | — | — |
| `add_issue_comment` | `repo` | — | — | — | — |
| `add_issue_comment` | `issue_number` | — | — | — | — |
| `add_issue_comment` | `body` | — | — | — | — |
| `create_branch` | `owner` | — | — | — | — |
| `create_branch` | `repo` | — | — | — | — |
| `create_branch` | `branch` | — | — | — | — |
| `create_branch` | `from_branch` | — | — | — | — |
| `create_issue` | `owner` | — | — | — | ✓ GitHub account |
| `create_issue` | `repo` | — | — | — | ✓ repository in the owner's account |
| `create_issue` | `title` | — | — | — | — |
| `create_issue` | `body` | — | — | — | — |
| `create_issue` | `assignees` | number of items (items) | 1 item / 2-3 items / 4+ items | — | — |
| `create_issue` | `milestone` | — | — | — | — |
| `create_issue` | `labels` | number of items (items) | 1 item / 2-3 items / 4+ items | — | — |
| `create_or_update_file` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `create_or_update_file` | `repo` | — | — | — | ✓ Repository name |
| `create_or_update_file` | `path` | — | — | — | — |
| `create_or_update_file` | `content` | — | — | — | — |
| `create_or_update_file` | `message` | — | — | — | — |
| `create_or_update_file` | `branch` | — | — | — | — |
| `create_or_update_file` | `sha` | — | — | — | — |
| `create_pull_request` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `create_pull_request` | `repo` | — | — | — | ✓ Repository name |
| `create_pull_request` | `title` | — | — | — | — |
| `create_pull_request` | `body` | — | — | — | — |
| `create_pull_request` | `head` | — | — | — | — |
| `create_pull_request` | `base` | — | — | — | — |
| `create_pull_request` | `draft` | — | — | — | — |
| `create_pull_request` | `maintainer_can_modify` | — | — | — | — |
| `create_pull_request_review` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `create_pull_request_review` | `repo` | — | — | — | ✓ Repository name |
| `create_pull_request_review` | `pull_number` | — | — | — | — |
| `create_pull_request_review` | `commit_id` | — | — | — | — |
| `create_pull_request_review` | `body` | — | — | — | — |
| `create_pull_request_review` | `event` | — | — | — | — |
| `create_pull_request_review` | `comments` | — | — | — | — |
| `create_repository` | `name` | — | — | — | — |
| `create_repository` | `description` | — | — | — | — |
| `create_repository` | `private` | — | — | — | — |
| `create_repository` | `autoInit` | — | — | — | — |
| `fork_repository` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `fork_repository` | `repo` | — | — | — | — |
| `fork_repository` | `organization` | — | — | — | ✓ organization to fork to |
| `get_file_contents` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `get_file_contents` | `repo` | — | — | — | ✓ Repository name |
| `get_file_contents` | `path` | — | — | — | ✓ Path to the file or directory |
| `get_file_contents` | `branch` | — | — | — | — |
| `get_issue` | `owner` | — | — | — | — |
| `get_issue` | `repo` | — | — | — | — |
| `get_issue` | `issue_number` | — | — | — | — |
| `get_pull_request` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `get_pull_request` | `repo` | — | — | — | ✓ Repository name |
| `get_pull_request` | `pull_number` | — | — | — | — |
| `get_pull_request_comments` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `get_pull_request_comments` | `repo` | — | — | — | ✓ Repository name |
| `get_pull_request_comments` | `pull_number` | Pull request number | 1-50 / 51-200 / 201+ | — | — |
| `get_pull_request_files` | `owner` | — | — | — | — |
| `get_pull_request_files` | `repo` | — | — | — | — |
| `get_pull_request_files` | `pull_number` | — | — | — | — |
| `get_pull_request_reviews` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `get_pull_request_reviews` | `repo` | — | — | — | ✓ Repository name |
| `get_pull_request_reviews` | `pull_number` | Pull request number | 1-50 / 51-200 / 201+ | — | — |
| `get_pull_request_status` | `owner` | — | — | — | — |
| `get_pull_request_status` | `repo` | — | — | — | — |
| `get_pull_request_status` | `pull_number` | — | — | — | — |
| `list_commits` | `owner` | — | — | — | — |
| `list_commits` | `repo` | — | — | — | — |
| `list_commits` | `sha` | — | — | — | — |
| `list_commits` | `page` | — | — | — | — |
| `list_commits` | `perPage` | number of items per page (items) | 10 items / 30 items / 100 items | removes the bound | — |
| `list_issues` | `owner` | — | — | — | — |
| `list_issues` | `repo` | — | — | — | — |
| `list_issues` | `direction` | — | — | — | — |
| `list_issues` | `labels` | number of items in the list | 0-5 items / 6-10 items / more than 10 items | — | — |
| `list_issues` | `page` | — | — | — | — |
| `list_issues` | `per_page` | number of issues per page | 1-25 issues / 26-50 issues / more than 50 issues | — | — |
| `list_issues` | `since` | — | — | — | — |
| `list_issues` | `sort` | — | — | — | — |
| `list_issues` | `state` | — | — | — | — |
| `list_pull_requests` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `list_pull_requests` | `repo` | — | — | — | ✓ Repository name |
| `list_pull_requests` | `state` | — | — | — | — |
| `list_pull_requests` | `head` | — | — | — | — |
| `list_pull_requests` | `base` | — | — | — | — |
| `list_pull_requests` | `sort` | — | — | — | — |
| `list_pull_requests` | `direction` | — | — | — | — |
| `list_pull_requests` | `per_page` | Results per page | 10 / 50 / 100 | 100 | — |
| `list_pull_requests` | `page` | Page number of the results | 1 / 2 / 5 | 1 | — |
| `merge_pull_request` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `merge_pull_request` | `repo` | — | — | — | ✓ Repository name |
| `merge_pull_request` | `pull_number` | — | — | — | — |
| `merge_pull_request` | `commit_title` | — | — | — | — |
| `merge_pull_request` | `commit_message` | — | — | — | — |
| `merge_pull_request` | `merge_method` | — | — | — | — |
| `push_files` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `push_files` | `repo` | — | — | — | ✓ Repository name |
| `push_files` | `branch` | — | — | — | — |
| `push_files` | `files` | number of items in the array (items) | 1 item / 5 items / 20 items | — | — |
| `push_files` | `message` | — | — | — | — |
| `search_code` | `q` | — | — | — | — |
| `search_code` | `order` | — | — | — | — |
| `search_code` | `page` | number of pages (pages) | 1-5 pages / 6-20 pages / 21+ pages | removes lower bound | — |
| `search_code` | `per_page` | number of items per page (items) | 1-30 items / 31-70 items / 71-100 items | — | — |
| `search_issues` | `q` | — | — | — | — |
| `search_issues` | `order` | — | — | — | — |
| `search_issues` | `page` | number of pages (pages) | 1-5 pages / 6-20 pages / 21+ pages | removes the lower bound | — |
| `search_issues` | `per_page` | number of items per page (items) | 1-30 items / 31-70 items / 71-100 items | — | — |
| `search_issues` | `sort` | — | — | — | — |
| `search_repositories` | `query` | — | — | — | — |
| `search_repositories` | `page` | Page number | 1-5 / 6-20 / 21-max | 1 | — |
| `search_repositories` | `perPage` | Number of results per page | 30 / 50 / 100 | 30 | — |
| `search_users` | `q` | — | — | — | — |
| `search_users` | `order` | — | — | — | — |
| `search_users` | `page` | number of pages (pages) | 1-5 pages / 6-20 pages / 21+ pages | removes the lower bound | — |
| `search_users` | `per_page` | number of items per page (items) | 1-30 items / 31-70 items / 71-100 items | — | — |
| `search_users` | `sort` | — | — | — | — |
| `update_issue` | `owner` | — | — | — | — |
| `update_issue` | `repo` | — | — | — | — |
| `update_issue` | `issue_number` | — | — | — | — |
| `update_issue` | `title` | — | — | — | — |
| `update_issue` | `body` | — | — | — | — |
| `update_issue` | `assignees` | number of items in the list (items) | 1 item / 3 items / 5 items | — | — |
| `update_issue` | `milestone` | — | — | — | — |
| `update_issue` | `labels` | number of items in the list (items) | 1 item / 3 items / 5 items | — | — |
| `update_issue` | `state` | — | — | — | — |
| `update_pull_request_branch` | `owner` | — | — | — | ✓ Repository owner (username or organization) |
| `update_pull_request_branch` | `repo` | — | — | — | ✓ Repository name |
| `update_pull_request_branch` | `pull_number` | — | — | — | — |
| `update_pull_request_branch` | `expected_head_sha` | — | — | — | — |

20 input(s) with a scale · 27 needing a policy lookup · 83 needing nothing · 0 tool(s) declare no inputs.
Failed: none.

## slack

| tool | input | measures | low / medium / high | absent | policy |
|---|---|---|---|---|---|
| `channels_list` | `channel_types` | — | — | — | ✓ channel types |
| `channels_list` | `cursor` | position in pagination (string) | — / — / — | removes pagination | — |
| `channels_list` | `limit` | number of items (items) | 1-300 items / 301-700 items / 701-999 items | — | — |
| `channels_list` | `query` | — | — | — | — |
| `channels_list` | `query_targets` | — | — | — | — |
| `channels_list` | `sort` | — | — | — | — |
| `channels_me` | `channel_types` | — | — | — | ✓ channel types |
| `channels_me` | `cursor` | position in pagination sequence (string) | — / — / — | no pagination | — |
| `channels_me` | `limit` | number of items (items) | 1-30 items / 31-90 items / 91-999 items | 100 items | — |
| `conversations_add_message` | `blocks` | — | — | — | — |
| `conversations_add_message` | `channel_id` | — | — | — | ✓ ID of the channel or user |
| `conversations_add_message` | `content_type` | — | — | — | — |
| `conversations_add_message` | `text` | — | — | — | — |
| `conversations_add_message` | `thread_ts` | timestamp (seconds.milliseconds) | — / — / — | message will be added to the channel itself | — |
| `conversations_history` | `channel_id` | — | — | — | ✓ channels or direct messages |
| `conversations_history` | `cursor` | pagination position | — / — / — | no pagination | — |
| `conversations_history` | `include_activity_messages` | — | — | — | — |
| `conversations_history` | `limit` | time or message count | 1d / 7d / 90d | default limit for free tier history (90d) | — |
| `conversations_join` | `channel_id` | — | — | — | ✓ channels |
| `conversations_leave` | `channel_id` | — | — | — | ✓ channels or users |
| `conversations_mark` | `channel_id` | — | — | — | ✓ channels or users |
| `conversations_mark` | `ts` | time (seconds) | 0s / 3600s / 86400s | — | — |
| `conversations_replies` | `channel_id` | — | — | — | — |
| `conversations_replies` | `cursor` | — | — | — | — |
| `conversations_replies` | `include_activity_messages` | — | — | — | — |
| `conversations_replies` | `limit` | time or number of messages (days or count) | 1d or 50 / 30d or 100 / 90d or 200 | — | — |
| `conversations_replies` | `thread_ts` | — | — | — | — |
| `conversations_search_messages` | `cursor` | — | — | — | — |
| `conversations_search_messages` | `filter_date_after` | date (days) | 1 day / 7 days / 30 days | — | — |
| `conversations_search_messages` | `filter_date_before` | date (days) | 1 day / 7 days / 30 days | — | — |
| `conversations_search_messages` | `filter_date_during` | duration (days) | 1 day / 7 days / 30 days | — | — |
| `conversations_search_messages` | `filter_date_on` | date (day) | — / — / — | — | — |
| `conversations_search_messages` | `filter_in_channel` | — | — | — | ✓ channel ID or name |
| `conversations_search_messages` | `filter_in_im_or_mpim` | — | — | — | ✓ DM/MPIM conversation ID or name |
| `conversations_search_messages` | `filter_threads_only` | — | — | — | — |
| `conversations_search_messages` | `filter_users_from` | — | — | — | ✓ user ID or display name |
| `conversations_search_messages` | `filter_users_with` | — | — | — | ✓ user ID or display name in threads and DMs |
| `conversations_search_messages` | `limit` | count | 10 items / 20 items / 50 items | — | — |
| `conversations_search_messages` | `search_query` | — | — | — | — |
| `conversations_unreads` | `channel_types` | — | — | — | — |
| `conversations_unreads` | `include_messages` | — | — | — | — |
| `conversations_unreads` | `include_muted` | — | — | — | — |
| `conversations_unreads` | `max_channels` | number of channels (channels) | 10 channels / 50 channels / 100 channels | unlimited | — |
| `conversations_unreads` | `max_messages_per_channel` | number of messages per channel (messages) | 5 messages / 10 messages / 20 messages | unlimited | — |
| `conversations_unreads` | `mentions_only` | — | — | — | — |
| `usergroups_create` | `channels` | — | — | — | ✓ channel IDs |
| `usergroups_create` | `description` | — | — | — | — |
| `usergroups_create` | `handle` | — | — | — | — |
| `usergroups_create` | `name` | — | — | — | — |
| `usergroups_list` | `include_count` | — | — | — | — |
| `usergroups_list` | `include_disabled` | — | — | — | — |
| `usergroups_list` | `include_users` | — | — | — | — |
| `usergroups_me` | `action` | — | — | — | — |
| `usergroups_me` | `usergroup_id` | — | — | — | ✓ user group IDs |
| `usergroups_update` | `channels` | — | — | — | ✓ channel IDs |
| `usergroups_update` | `description` | — | — | — | — |
| `usergroups_update` | `handle` | — | — | — | — |
| `usergroups_update` | `name` | — | — | — | — |
| `usergroups_update` | `usergroup_id` | — | — | — | ✓ user group IDs |
| `usergroups_users_update` | `usergroup_id` | — | — | — | ✓ ID of the user group |
| `usergroups_users_update` | `users` | number of items in list (items) | 1-5 items / 6-20 items / 21+ items | — | — |
| `users_search` | `limit` | number of results (results) | 1-20 results / 21-50 results / 51-100 results | — | — |
| `users_search` | `query` | — | — | — | — |

18 input(s) with a scale · 16 needing a policy lookup · 29 needing nothing · 0 tool(s) declare no inputs.
Failed: none.

## calendar

| tool | input | measures | low / medium / high | absent | policy |
|---|---|---|---|---|---|
| `create_event` | `title` | — | — | — | — |
| `create_event` | `date` | — | — | — | — |
| `create_event` | `calendar` | — | — | — | ✓ target calendar id |
| `create_event` | `attendees` | — | — | — | — |
| `create_event` | `duration_min` | meeting length (minutes) | 30 minutes / 60 minutes / 120 minutes | no duration limit | — |
| `update_event` | `event_id` | — | — | — | — |
| `update_event` | `calendar` | — | — | — | ✓ calendar id |
| `update_event` | `attendees` | number of attendees (count) | 1-5 count / 6-20 count / 21+ count | — | — |
| `update_event` | `duration_min` | meeting length (minutes) | 30 minutes / 60 minutes / 90+ minutes | no limit | — |

3 input(s) with a scale · 2 needing a policy lookup · 4 needing nothing · 9 tool(s) declare no inputs.
Failed: none.
