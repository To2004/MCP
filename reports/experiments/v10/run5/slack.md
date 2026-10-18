# slack — every tool input, explained

Run `run5`. One table per tool. **Declared** is what the tool's
own schema says — the only evidence the model had. **Class** is what the
model returned and why. **At run time** is what that classification asks
the dynamic layer to do with the value.

Classes: `RANGE` compares by magnitude · `POLICY` resolves which entity
was named against policy · `IGNORE` is not evaluated · `UNKNOWN` is
undecided.

**RANGE** 14 · **POLICY** 23 · **IGNORE** 26 · **UNKNOWN** 0 · 63 declared across 16 tool(s).

Prompt `b14d66ebf28b` · job `20673506` · catalog `reports/live_run/slack_real_toollist.json` (slack-mcp-server (korotovsky), captured 2026-07-06).

### `channels_list`

6 argument(s), one model call, 38s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_types` | `string` — Comma-separated channel types. Allowed values: 'mpim', 'im', 'public_channel', 'private_channel'. Example: 'public_channel,private_channel,im' | **POLICY** | The value selects which type of channels to list, changing the context of the call. | Resolve “channel_type” against the organisation's policy: may this caller act on the one it named? |
| `cursor` | `string` — Cursor for pagination. Use the value of the last row and column in the response as next_cursor field returned from the previous request. | **IGNORE** | Cursor is used for pagination and does not have a meaningful order or policy implication. | Not evaluated by this component. |
| `limit` | `number` · default=100 — The maximum number of items to return. Must be an integer between 1 and 1000 (maximum 999). | **RANGE** / count | The limit defines the maximum number of items to return, which is a count. | Band the value: **low** < 50 · **medium** 50-200 · **high** > 200. Boundaries come from the schema's declared minimum/maximum. |
| `query` | `string` — Optional keyword to filter channels. Case-insensitive substring match against the fields specified by query_targets. Example: 'marketing' returns channels like #marketing, #marketing-ops. | **IGNORE** | Query is free text used for filtering and does not have a meaningful order or policy implication. | Not evaluated by this component. |
| `query_targets` | `string` · default="name" — Comma-separated list of fields to match the query against. Allowed values: 'name', 'topic', 'purpose'. Example: 'name,topic,purpose' to search all fields. Default is 'name'. | **POLICY** | The value selects which fields to match the query against, changing the context of the call. | Resolve “field_to_match” against the organisation's policy: may this caller act on the one it named? |
| `sort` | `string` — Type of sorting. Allowed values: 'popularity' - sort by number of members/participants in each channel. | **IGNORE** | Sort changes only how results are presented and does not have a meaningful order or policy implication. | Not evaluated by this component. |

### `channels_me`

3 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_types` | `string` — Comma-separated channel types. Allowed values: 'mpim', 'im', 'public_channel', 'private_channel'. Default: 'public_channel,private_channel'. | **POLICY** | The value selects which type of channels to list, changing the context of the call. | Resolve “channel_type” against the organisation's policy: may this caller act on the one it named? |
| `cursor` | `string` — Cursor for pagination. | **IGNORE** | Cursor is used for pagination and does not have a meaningful order or policy implication. | Not evaluated by this component. |
| `limit` | `number` · default=100 — Maximum number of items to return (1-999). | **RANGE** / count | The limit argument specifies the maximum number of items to return, which has a meaningful order. | Band the value: **low** <50 · **medium** 50-200 · **high** >200. Boundaries come from the schema's declared minimum/maximum. |

### `conversations_add_message`

5 argument(s), one model call, 16s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `blocks` | `string` — Raw Slack Block Kit JSON array for rich message formatting (rich_text lists, code blocks, etc.). When provided, this takes precedence over text/content_type for rendering. The text parameter becomes the notification fallback text. | **IGNORE** | The blocks argument is a string that holds JSON for rich message formatting. It does not have an inherent order or policy context. | Not evaluated by this component. |
| `channel_id` | `string` — ID of the channel in format Cxxxxxxxxxx or its name starting with #... or @... aka #general or @username_dm. | **POLICY** | The channel_id is an identifier that determines which channel the message will be added to. It does not have a meaningful order but selects a specific resource. | Resolve “channel_id” against the organisation's policy: may this caller act on the one it named? |
| `content_type` | `string` · default="text/markdown" — Content type of the message. Default is 'text/markdown'. Allowed values: 'text/markdown', 'text/plain'. Ignored when blocks is provided. | **IGNORE** | The content_type is an enum that changes only the presentation of the message and does not affect which resource or context the call acts on. | Not evaluated by this component. |
| `text` | `string` — Message text in specified content_type format. Example: 'Hello, world!' for text/plain or '# Hello, world!' for text/markdown. | **IGNORE** | The text argument is free-form message content. It does not have a meaningful order or policy context. | Not evaluated by this component. |
| `thread_ts` | `string` — Unique identifier of either a thread's parent message or a message in the thread_ts must be the timestamp in format 1234567890.123456 of an existing message with 0 or more replies. Optional, if not provided the message will be added to the channel itself, otherwise it will be added to the thread. | **POLICY** | The thread_ts is an identifier that determines which thread the message will be added to. It does not have a meaningful order but selects a specific context. | Resolve “thread_ts” against the organisation's policy: may this caller act on the one it named? |

### `conversations_history`

4 argument(s), one model call, 8s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_id` | `string` — - `channel_id` (string): ID of the channel in format Cxxxxxxxxxx or its name starting with #... or @... aka #general or @username_dm. | **POLICY** | The channel ID or name identifies a specific communication context, which is subject to policy. | Resolve “channel_or_user” against the organisation's policy: may this caller act on the one it named? |
| `cursor` | `string` — Cursor for pagination. Use the value of the last row and column in the response as next_cursor field returned from the previous request. | **IGNORE** | Cursor values are used for pagination and do not have inherent meaning beyond their use in the API call. | Not evaluated by this component. |
| `include_activity_messages` | `boolean` · default=false — If true, the response will include activity messages such as 'channel_join' or 'channel_leave'. Default is boolean false. | **IGNORE** | This is a boolean flag that changes how results are returned, but does not affect which resources or subjects are acted upon. | Not evaluated by this component. |
| `limit` | `string` · default="1d" — Limit of messages to fetch in format of maximum ranges of time (e.g. 1d - 1 day, 1w - 1 week, 30d - 30 days, 90d - 90 days which is a default limit for free tier history) or number of messages (e.g. 50). Must be empty when 'cursor' is provided. | **RANGE** / duration | The limit argument specifies a duration or number of messages to fetch, which has a meaningful order. | Band the value: **low** < 1d · **medium** 1d - 30d · **high** > 30d. Boundaries come from limits stated in the description. |

### `conversations_join`

1 argument(s), one model call, 3s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_id` | `string` — ID of the channel in format Cxxxxxxxxxx or its name starting with #... (e.g., #general). | **POLICY** | The channel ID or name is used to identify which specific channel the user wants to join, and this selection must be evaluated against policy. | Resolve “channel” against the organisation's policy: may this caller act on the one it named? |

### `conversations_leave`

1 argument(s), one model call, 3s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_id` | `string` — ID of the channel in format Cxxxxxxxxxx or its name starting with #... or @... (e.g., #general, @username). | **POLICY** | The channel_id identifies a specific channel or user, which is relevant to policy decisions. | Resolve “channel_or_user” against the organisation's policy: may this caller act on the one it named? |

### `conversations_mark`

2 argument(s), one model call, 5s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_id` | `string` — ID of the channel in format Cxxxxxxxxxx or its name starting with #... or @... (e.g., #general, @username). | **POLICY** | The channel ID or name identifies a specific communication context, which is subject to policy. | Resolve “channel_or_user” against the organisation's policy: may this caller act on the one it named? |
| `ts` | `string` — Timestamp of the message to mark as read up to. If not provided, marks all messages as read. | **RANGE** / temporal | The timestamp represents a point in time, and its value can be compared to determine how far back the read mark is set. | Band the value: **low** < 3600 seconds ago · **medium** 3600-86400 seconds ago · **high** > 86400 seconds ago. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `conversations_replies`

5 argument(s), one model call, 9s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_id` | `string` — ID of the channel in format Cxxxxxxxxxx or its name starting with #... or @... aka #general or @username_dm. | **POLICY** | The channel ID or name identifies a specific communication channel, which is subject to policy. | Resolve “channel” against the organisation's policy: may this caller act on the one it named? |
| `cursor` | `string` — Cursor for pagination. Use the value of the last row and column in the response as next_cursor field returned from the previous request. | **IGNORE** | Cursor values are used for pagination and do not have inherent meaning beyond their use in fetching the next set of results. | Not evaluated by this component. |
| `include_activity_messages` | `boolean` · default=false — If true, the response will include activity messages such as 'channel_join' or 'channel_leave'. Default is boolean false. | **IGNORE** | This is a boolean flag that changes how messages are included, but does not change the subject or resource acted upon. | Not evaluated by this component. |
| `limit` | `string` · default="1d" — Limit of messages to fetch in format of maximum ranges of time (e.g. 1d - 1 day, 30d - 30 days, 90d - 90 days which is a default limit for free tier history) or number of messages (e.g. 50). Must be empty when 'cursor' is provided. | **RANGE** / duration | The limit argument specifies a duration or number of messages to fetch, which has a meaningful order. | Band the value: **low** < 1d · **medium** 1d - 30d · **high** > 30d. Boundaries come from limits stated in the description. |
| `thread_ts` | `string` — Unique identifier of either a thread's parent message or a message in the thread. ts must be the timestamp in format 1234567890.123456 of an existing message with 0 or more replies. | **POLICY** | This timestamp identifies a specific thread or message within a conversation, which is subject to policy. | Resolve “message_thread” against the organisation's policy: may this caller act on the one it named? |

### `conversations_search_messages`

12 argument(s), one model call, 38s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `cursor` | `string` · default="" — Cursor for pagination. Use the value of the last row and column in the response as next_cursor field returned from the previous request. | **IGNORE** | The cursor is used for pagination and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `filter_date_after` | `string` — Filter messages sent after a specific date in format 'YYYY-MM-DD'. Example: '2023-10-01', 'July', 'Yesterday' or 'Today'. If not provided, all dates will be searched. | **RANGE** / temporal | The date after which messages are filtered has a meaningful order. | Band the value: **low** < 7 days ago · **medium** 7-30 days ago · **high** > 30 days ago. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `filter_date_before` | `string` — Filter messages sent before a specific date in format 'YYYY-MM-DD'. Example: '2023-10-01', 'July', 'Yesterday' or 'Today'. If not provided, all dates will be searched. | **RANGE** / temporal | The date before which messages are filtered has a meaningful order. | Band the value: **low** < 7 days ago · **medium** 7-30 days ago · **high** > 30 days ago. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `filter_date_during` | `string` — Filter messages sent during a specific period in format 'YYYY-MM-DD'. Example: 'July', 'Yesterday' or 'Today'. If not provided, all dates will be searched. | **RANGE** / temporal | The date during which messages are filtered has a meaningful order. | Band the value: **low** < 7 days ago · **medium** 7-30 days ago · **high** > 30 days ago. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `filter_date_on` | `string` — Filter messages sent on a specific date in format 'YYYY-MM-DD'. Example: '2023-10-01', 'July', 'Yesterday' or 'Today'. If not provided, all dates will be searched. | **RANGE** / temporal | The date on which messages are filtered has a meaningful order. | Band the value: **low** < 7 days ago · **medium** 7-30 days ago · **high** > 30 days ago. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `filter_in_channel` | `string` — Filter messages in a specific public/private channel by its ID or name. Example: 'C1234567890', 'G1234567890', or '#general'. If not provided, all channels will be searched. | **POLICY** | The channel ID or name is a policy concept as it identifies the specific channel. | Resolve “channel” against the organisation's policy: may this caller act on the one it named? |
| `filter_in_im_or_mpim` | `string` — Filter messages in a direct message (DM) or multi-person direct message (MPIM) conversation by its ID or name. Example: 'D1234567890' or '@username_dm'. If not provided, all DMs and MPIMs will be searched. | **POLICY** | The DM or MPIM conversation ID or name is a policy concept as it identifies the specific conversation. | Resolve “conversation” against the organisation's policy: may this caller act on the one it named? |
| `filter_threads_only` | `boolean` — If true, the response will include only messages from threads. Default is boolean false. | **IGNORE** | This is a boolean flag that changes the presentation of results, not a policy concept or meaningful order. | Not evaluated by this component. |
| `filter_users_from` | `string` — Filter messages from a specific user by their ID or display name. Example: 'U1234567890' or '@username'. If not provided, all users will be searched. | **POLICY** | The user ID or display name is a policy concept as it identifies the specific user. | Resolve “user” against the organisation's policy: may this caller act on the one it named? |
| `filter_users_with` | `string` — Filter messages with a specific user by their ID or display name in threads and DMs. Example: 'U1234567890' or '@username'. If not provided, all threads and DMs will be searched. | **POLICY** | The user ID or display name is a policy concept as it identifies the specific user. | Resolve “user” against the organisation's policy: may this caller act on the one it named? |
| `limit` | `number` · default=20 — The maximum number of items to return. Must be an integer between 1 and 100. | **RANGE** / count | The limit has a meaningful order and is bounded by the schema. | Band the value: **low** < 20 items · **medium** 20-50 items · **high** > 50 items. Boundaries come from the schema's declared minimum/maximum. |
| `search_query` | `string` — Search query to filter messages. Example: 'marketing report' or full URL of Slack message e.g. 'https://slack.com/archives/C1234567890/p1234567890123456', then the tool will return a single message matching given URL, herewith all other parameters will be ignored. | **IGNORE** | The search query is free text and does not have a meaningful order or policy context. | Not evaluated by this component. |

### `conversations_unreads`

6 argument(s), one model call, 12s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_types` | `string` · default="all" — Filter by channel type: 'all' (default), 'dm' (direct messages), 'group_dm' (group DMs), 'partner' (ext-* channels), 'internal' (other channels). | **POLICY** | The value selects which type of channel the call acts on. | Resolve “channel_type” against the organisation's policy: may this caller act on the one it named? |
| `include_messages` | `boolean` · default=true — If true (default), returns the actual unread messages. If false, returns only a summary of channels with unreads. | **IGNORE** | This argument only changes how the result is rendered, not the subject or context of the call. | Not evaluated by this component. |
| `include_muted` | `boolean` · default=false — If true, includes muted channels in results. Default is false (muted channels are excluded, matching Slack app behavior). | **IGNORE** | This argument only changes how the result is rendered, not the subject or context of the call. | Not evaluated by this component. |
| `max_channels` | `number` · default=50 — Maximum number of channels to fetch unreads from. Default is 50. | **RANGE** / count | The value represents a count of channels, and the meaning changes at different thresholds. | Band the value: **low** < 25 · **medium** 25-75 · **high** > 75 channels. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `max_messages_per_channel` | `number` · default=10 — Maximum messages to fetch per channel. Default is 10. | **RANGE** / count | The value represents a count of messages, and the meaning changes at different thresholds. | Band the value: **low** < 5 · **medium** 5-20 · **high** > 20 messages. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `mentions_only` | `boolean` · default=false — If true, only returns channels where you have @mentions. Default is false. | **IGNORE** | This argument only changes how the result is rendered, not the subject or context of the call. | Not evaluated by this component. |

### `usergroups_create`

4 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channels` | `string` — Comma-separated channel IDs where this group is commonly mentioned. Members get suggestions to join these channels. | **POLICY** | The value selects specific channels, which is a policy concern. | Resolve “channel_ids” against the organisation's policy: may this caller act on the one it named? |
| `description` | `string` — Purpose or description shown in group details (e.g., 'Backend and frontend engineers'). | **IGNORE** | This is free text that does not have an inherent order or policy significance. | Not evaluated by this component. |
| `handle` | `string` — The @mention handle without the @ symbol (e.g., 'engineering' for @engineering). Keep it short and lowercase. If omitted, Slack auto-generates one from the name. | **POLICY** | The handle uniquely identifies the user group and is a policy concern. | Resolve “user_group_handle” against the organisation's policy: may this caller act on the one it named? |
| `name` | `string` — Display name of the user group (e.g., 'Engineering Team', 'Design Squad'). | **IGNORE** | This is free text that does not have an inherent order or policy significance, though it's required for display purposes. | Not evaluated by this component. |

### `usergroups_list`

3 argument(s), one model call, 5s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `include_count` | `boolean` · default=true — Include user count for each group. Default is true. | **IGNORE** | This argument only changes the content of the response, not the subject or scale of the operation. | Not evaluated by this component. |
| `include_disabled` | `boolean` · default=false — Include disabled/archived groups. Default is false. | **IGNORE** | This argument only changes the content of the response, not the subject or scale of the operation. | Not evaluated by this component. |
| `include_users` | `boolean` · default=false — Include list of user IDs in each group. Default is false. | **IGNORE** | This argument only changes the content of the response, not the subject or scale of the operation. | Not evaluated by this component. |

### `usergroups_me`

2 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `action` | `string` — Action to perform: 'list' returns CSV of groups you're a member of, 'join' adds you to a group, 'leave' removes you from a group. | **IGNORE** | The action argument changes only the operation performed and does not represent a quantity or identity that requires policy evaluation. | Not evaluated by this component. |
| `usergroup_id` | `string` — ID of the user group (starts with 'S', e.g., 'S0123456789'). Required for 'join' and 'leave' actions. Get IDs from usergroups_list. | **POLICY** | The usergroup_id is an identifier that determines which specific group the action applies to, and this requires policy evaluation. | Resolve “usergroup_id” against the organisation's policy: may this caller act on the one it named? |

### `usergroups_update`

5 argument(s), one model call, 8s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channels` | `string` — New default channel IDs (comma-separated). Replaces existing default channels. | **POLICY** | The value represents specific channel IDs, which are policy-relevant identifiers. | Resolve “channel_ids” against the organisation's policy: may this caller act on the one it named? |
| `description` | `string` — New description for the group. | **IGNORE** | This is free text that does not have a meaningful order or identity relevant to policy. | Not evaluated by this component. |
| `handle` | `string` — New @mention handle (without @). Changing this changes how users mention the group. | **POLICY** | The handle changes how the group is mentioned, which can be subject to organizational policies. | Resolve “mention_handle” against the organisation's policy: may this caller act on the one it named? |
| `name` | `string` — New display name for the group. | **IGNORE** | This is free text that does not have a meaningful order or identity relevant to policy. | Not evaluated by this component. |
| `usergroup_id` | `string` — ID of the user group to update (starts with 'S', e.g., 'S0123456789'). Get IDs from usergroups_list. | **POLICY** | The user group ID is an identifier that determines which specific group the operation acts on, making it policy-relevant. | Resolve “user_group_ids” against the organisation's policy: may this caller act on the one it named? |

### `usergroups_users_update`

2 argument(s), one model call, 5s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `usergroup_id` | `string` — ID of the user group (starts with 'S', e.g., 'S0123456789'). Get IDs from usergroups_list. | **POLICY** | The usergroup_id is an identifier for a specific user group, which determines the scope of the operation. | Resolve “user group” against the organisation's policy: may this caller act on the one it named? |
| `users` | `string` — Comma-separated user IDs that will become the COMPLETE member list (e.g., 'U0123456789,U9876543210'). All current members not in this list will be removed. | **RANGE** / count | The 'users' argument represents a list of user IDs, and the number of users can be considered as a count. The ranges are based on typical group sizes. | Band the value: **low** < 5 users · **medium** 5-20 users · **high** > 20 users. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `users_search`

2 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `limit` | `number` · default=10 — Maximum number of results to return (1-100). Default is 10. | **RANGE** / count | The limit argument is a numeric value that represents the maximum number of results to return, which has a meaningful order. | Band the value: **low** <10 · **medium** 10-50 · **high** >50. Boundaries come from the schema's declared minimum/maximum. |
| `query` | `string` — Search query - matches against real name, display name, username, email, or a Slack user ID (e.g. U07VCEPP4N5). | **IGNORE** | The query argument is a search string that does not have an inherent order or policy context. | Not evaluated by this component. |
