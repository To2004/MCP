# Scan — slack:real

_kind=slack · provenance=llm-scan · model_reviewed=True · bands={'low': 30, 'medium': 86, 'high': 38, 'critical': 6}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: communication
- **asset_meaning**: Slack channels (public or private) used for communication within an organization.
- **blast_radius_meaning**: The extent to which a tool can affect the content and membership of a channel, ranging from read-only operations like listing members or messages to actions that modify the channel's state such as adding messages or changing memberships.
- **worked_example**: The tool 'conversations_add_message' paired with the asset 'incident-response' could be severe if it adds critical incident details to a private technical channel, potentially exposing sensitive information.

## Tool impact

| tool | impact |
| --- | --- |
| `channels_list` | 1 |
| `channels_me` | 1 |
| `conversations_add_message` | 2 |
| `conversations_history` | 1 |
| `conversations_join` | 2 |
| `conversations_leave` | 2 |
| `conversations_mark` | 2 |
| `conversations_replies` | 1 |
| `conversations_search_messages` | 1 |
| `conversations_unreads` | 1 |
| `usergroups_create` | 2 |
| `usergroups_list` | 1 |
| `usergroups_me` | 2 |
| `usergroups_update` | 2 |
| `usergroups_users_update` | 3 |
| `users_search` | 1 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `general` | 1 |
| `announcements` | 2 |
| `random` | 1 |
| `engineering` | 2 |
| `incident-response` | 4 |
| `on-call` | 4 |
| `research-team` | 4 |
| `exec-private` | 4 |
| `hr-internal` | 4 |
| `team-leads` | 4 |

## Risk matrix (score · band)

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 8 🟡 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 2 🟢 | 4 🟢 | 9 🟡 | 4 🟢 |
| `announcements` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 4 🟢 | 8 🟡 | 18 🟡 | 8 🟡 |
| `random` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 2 🟢 | 4 🟢 | 9 🟡 | 4 🟢 |
| `engineering` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 18 🟡 | 8 🟡 |
| `incident-response` | 16 🟠 | 16 🟠 | 16 🟡 | 16 🟠 | 16 🟡 | 16 🟡 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟡 | 4 🟡 | 16 🟡 | 16 🟡 | 48 🔴 | 8 🟡 |
| `on-call` | 16 🟠 | 16 🟠 | 16 🟡 | 16 🟠 | 16 🟡 | 16 🟡 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟡 | 8 🟡 | 16 🟡 | 16 🟡 | 48 🔴 | 8 🟡 |
| `research-team` | 16 🟠 | 16 🟠 | 16 🟡 | 16 🟠 | 16 🟡 | 16 🟡 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟡 | 8 🟡 | 16 🟡 | 16 🟡 | 48 🔴 | 8 🟡 |
| `exec-private` | 16 🟠 | 16 🟠 | 24 🟠 | 16 🟠 | 16 🟡 | 16 🟡 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟡 | 8 🟡 | 16 🟡 | 16 🟡 | 48 🔴 | 8 🟡 |
| `hr-internal` | 16 🟠 | 16 🟠 | 16 🟡 | 16 🟠 | 16 🟡 | 16 🟡 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟡 | 4 🟡 | 16 🟡 | 16 🟡 | 48 🔴 | 16 🟠 |
| `team-leads` | 16 🟠 | 16 🟠 | 16 🟡 | 16 🟠 | 16 🟡 | 16 🟡 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟡 | 8 🟡 | 16 🟡 | 16 🟡 | 48 🔴 | 8 🟡 |

## Tool atomic operations

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `channels_list` | **LIST** | 1 (Low) | LIST | rules |
| `channels_me` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `conversations_add_message` | **BROADCAST** | 4 (High) | BROADCAST | verb-fallback |
| `conversations_history` | **READ** | 2 (Low) | READ | verb-fallback |
| `conversations_join` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `conversations_leave` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `conversations_mark` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `conversations_replies` | **READ** | 2 (Low) | READ | verb-fallback |
| `conversations_search_messages` | **BROADCAST** | 4 (High) | BROADCAST | verb-fallback |
| `conversations_unreads` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `usergroups_create` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `usergroups_list` | **LIST** | 1 (Low) | LIST | rules |
| `usergroups_me` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `usergroups_update` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `usergroups_users_update` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `users_search` | **SEARCH** | 2 (Low) | SEARCH | verb-fallback |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `channels_list` | `limit` | 4 | >= 999 | can amplify data retrieval volume |
| `channels_list` | `query` | 3 | — | allows for broad or specific channel filtering |
| `channels_list` | `channel_types` | 2 | — | limits scope to predefined types |
| `channels_list` | `query_targets` | 2 | — | limits query scope to predefined fields |
| `channels_list` | `cursor` | 1 | — | pagination control, no amplification risk |
| `channels_list` | `sort` | 1 | — | only affects order, not volume or content |
| `channels_me` | `limit` | 4 | >= 999 | can amplify the volume of data retrieved |
| `channels_me` | `channel_types` | 3 | — | controls the scope of channels queried |
| `channels_me` | `cursor` | 1 | — | used for pagination, low risk |
| `conversations_add_message` | `text` | 5 | — | Fully controlled payload for the message content |
| `conversations_add_message` | `blocks` | 4 | — | Can contain arbitrary JSON for rich message formatting |
| `conversations_add_message` | `thread_ts` | 3 | — | Can target specific threads, potentially amplifying scope |
| `conversations_add_message` | `channel_id` | 2 | — | Identifies the target channel but does not control content |
| `conversations_add_message` | `content_type` | 1 | — | Limits message format, no direct amplification of risk |
| `conversations_history` | `limit` | 5 | unbounded (no LIMIT) | controls the magnitude of data fetched, potentially overwhel |
| `conversations_history` | `include_activity_messages` | 3 | — | can widen the scope of data retrieved |
| `conversations_history` | `channel_id` | 2 | — | merely names the target |
| `conversations_history` | `cursor` | 1 | — | used for pagination, no amplification of risk |
| `conversations_join` | `channel_id` | 2 | — | merely names the target |
| `conversations_leave` | `channel_id` | 2 | — | merely names the target |
| `conversations_mark` | `ts` | 3 | — | can be used to mark all messages as read if not provided, po |
| `conversations_mark` | `channel_id` | 2 | — | merely names the target |
| `conversations_replies` | `limit` | 4 | unbounded (no LIMIT) | controls the magnitude of data fetched, unbounded can overwh |
| `conversations_replies` | `include_activity_messages` | 3 | — | can widen the scope of messages fetched |
| `conversations_replies` | `channel_id` | 2 | — | merely names the target |
| `conversations_replies` | `thread_ts` | 2 | — | identifies a specific thread or message, not inherently risk |
| `conversations_replies` | `cursor` | 1 | — | used for pagination, not inherently risky |
| `conversations_search_messages` | `limit` | 5 | >= 100 | high fan-out control, can amplify call's impact significantl |
| `conversations_search_messages` | `search_query` | 5 | — | free-form query with full caller control, high risk of abuse |
| `conversations_search_messages` | `filter_users_with` | 4 | — | DM/MPIM user filtering, high risk due to sensitive content |
| `conversations_search_messages` | `filter_in_im_or_mpim` | 3 | — | DM/MPIM targeting, higher risk due to sensitive content |
| `conversations_search_messages` | `filter_users_from` | 3 | — | user targeting, higher risk due to potential sensitive data  |
| `conversations_search_messages` | `cursor` | 2 | — | pagination control, low risk |
| `conversations_search_messages` | `filter_date_during` | 2 | — | potentially broad date range filter |
| `conversations_search_messages` | `filter_in_channel` | 2 | — | channel targeting, moderate risk |
| `conversations_search_messages` | `filter_date_after` | 1 | — | narrow date range filter |
| `conversations_search_messages` | `filter_date_before` | 1 | — | narrow date range filter |
| `conversations_search_messages` | `filter_date_on` | 1 | — | specific date filter, low risk |
| `conversations_search_messages` | `filter_threads_only` | 1 | — | thread filtering, low risk |
| `conversations_unreads` | `max_channels` | 5 | >= 100 | controls the breadth of channel fan-out, increasing load and |
| `conversations_unreads` | `include_muted` | 4 | — | widens scope to include muted channels, potentially exposing |
| `conversations_unreads` | `max_messages_per_channel` | 4 | >= 50 | increases data volume per channel, potentially overwhelming  |
| `conversations_unreads` | `include_messages` | 3 | — | controls whether actual messages are returned, increasing da |
| `conversations_unreads` | `channel_types` | 2 | — | limits scope to specific channel types |
| `conversations_unreads` | `mentions_only` | 1 | — | narrows scope to only channels with mentions, reducing risk |
| `usergroups_create` | `handle` | 4 | — | can be used for impersonation or phishing attempts |
| `usergroups_create` | `channels` | 3 | >= 10 channels | can broaden access to multiple sensitive channels |
| `usergroups_create` | `name` | 2 | — | potentially misleading group name |
| `usergroups_create` | `description` | 2 | — | potentially misleading or confusing text |
| `usergroups_list` | `include_users` | 5 | — | Potentially exposes a large list of user IDs, increasing ris |
| `usergroups_list` | `include_disabled` | 3 | — | May expose sensitive information about archived groups |
| `usergroups_list` | `include_count` | 2 | — | Does not significantly affect security |
| `usergroups_me` | `usergroup_id` | 4 | — | can target any group, potentially leading to unauthorized ac |
| `usergroups_me` | `action` | 3 | — | controls the operation but is limited to predefined actions |
| `usergroups_update` | `channels` | 4 | >= 10 channels | Bulk fan-out to multiple channels |
| `usergroups_update` | `handle` | 3 | — | Changes how users interact with the group |
| `usergroups_update` | `description` | 2 | — | Potentially misleading text content |
| `usergroups_update` | `name` | 2 | — | Potentially misleading display name |
| `usergroups_update` | `usergroup_id` | 1 | — | Identifies the target group, no amplification |
| `usergroups_users_update` | `users` | 5 | >= 100 users | completely replaces member list, allowing bulk manipulation |
| `usergroups_users_update` | `usergroup_id` | 2 | — | merely identifies the target |
| `users_search` | `query` | 5 | — | Fully controllable input that can be used for enumeration or |
| `users_search` | `limit` | 3 | >= 100 | Can return a large number of results |
