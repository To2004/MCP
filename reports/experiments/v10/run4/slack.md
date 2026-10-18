# slack — every tool input, explained

Run `run4`. One table per tool. **Declared** is what the tool's
own schema says — the only evidence the model had. **Class** is what the
model returned and why. **At run time** is what that classification asks
the dynamic layer to do with the value.

Classes: `RANGE` compares by magnitude · `POLICY` resolves which entity
was named against policy · `IGNORE` is not evaluated · `UNKNOWN` is
undecided.

**RANGE** 15 · **POLICY** 21 · **IGNORE** 27 · **UNKNOWN** 0 · 63 declared across 16 tool(s).

Prompt `4fae213c99a4` · job `20629011` · catalog `reports/live_run/slack_real_toollist.json` (slack-mcp-server (korotovsky), captured 2026-07-06).

### `channels_list`

6 argument(s), one model call, 198s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_types` | `string` — Comma-separated channel types. Allowed values: 'mpim', 'im', 'public_channel', 'private_channel'. Example: 'public_channel,private_channel,im' | **POLICY** | The value selects which type of channels to list, changing the context of the call. | Resolve “channel_type” against the organisation's policy: may this caller act on the one it named? |
| `cursor` | `string` — Cursor for pagination. Use the value of the last row and column in the response as next_cursor field returned from the previous request. | **IGNORE** | Cursor is used for pagination and does not affect the policy or represent a meaningful order. | Not evaluated by this component. |
| `limit` | `number` · default=100 — The maximum number of items to return. Must be an integer between 1 and 1000 (maximum 999). | **RANGE** / count | The limit represents the maximum number of items to return, which is a count. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from limits stated in the description. |
| `query` | `string` — Optional keyword to filter channels. Case-insensitive substring match against the fields specified by query_targets. Example: 'marketing' returns channels like #marketing, #marketing-ops. | **IGNORE** | Query is used for filtering channels and does not affect policy or represent a meaningful order. | Not evaluated by this component. |
| `query_targets` | `string` · default="name" — Comma-separated list of fields to match the query against. Allowed values: 'name', 'topic', 'purpose'. Example: 'name,topic,purpose' to search all fields. Default is 'name'. | **POLICY** | The value selects which fields to match the query against, changing the context of the call. | Resolve “field_to_match” against the organisation's policy: may this caller act on the one it named? |
| `sort` | `string` — Type of sorting. Allowed values: 'popularity' - sort by number of members/participants in each channel. | **IGNORE** | Sort changes only how results are presented and does not affect policy or represent a meaningful order. | Not evaluated by this component. |

### `channels_me`

3 argument(s), one model call, 14s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_types` | `string` — Comma-separated channel types. Allowed values: 'mpim', 'im', 'public_channel', 'private_channel'. Default: 'public_channel,private_channel'. | **POLICY** | The value selects which type of channels to list, changing the context of the call. | Resolve “channel_type” against the organisation's policy: may this caller act on the one it named? |
| `cursor` | `string` — Cursor for pagination. | **IGNORE** | Cursor is used for pagination and does not affect the policy or represent a meaningful order. | Not evaluated by this component. |
| `limit` | `number` · default=100 — Maximum number of items to return (1-999). | **RANGE** / count | The limit argument represents a count of items to return, with documented bounds. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from limits stated in the description. |

### `conversations_add_message`

5 argument(s), one model call, 20s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `blocks` | `string` — Raw Slack Block Kit JSON array for rich message formatting (rich_text lists, code blocks, etc.). When provided, this takes precedence over text/content_type for rendering. The text parameter becomes the notification fallback text. | **IGNORE** | The blocks argument is used for rich message formatting and does not represent a quantity or policy concept. | Not evaluated by this component. |
| `channel_id` | `string` — ID of the channel in format Cxxxxxxxxxx or its name starting with #... or @... aka #general or @username_dm. | **POLICY** | The channel_id identifies the specific channel or user to which the message is sent, and this identity must be checked against policy. | Resolve “channel_or_user” against the organisation's policy: may this caller act on the one it named? |
| `content_type` | `string` · default="text/markdown" — Content type of the message. Default is 'text/markdown'. Allowed values: 'text/markdown', 'text/plain'. Ignored when blocks is provided. | **IGNORE** | The content_type argument only changes how the message is rendered and does not represent a quantity or policy concept. | Not evaluated by this component. |
| `text` | `string` — Message text in specified content_type format. Example: 'Hello, world!' for text/plain or '# Hello, world!' for text/markdown. | **IGNORE** | The text argument is free-form message content and does not represent a quantity or policy concept. | Not evaluated by this component. |
| `thread_ts` | `string` — Unique identifier of either a thread's parent message or a message in the thread_ts must be the timestamp in format 1234567890.123456 of an existing message with 0 or more replies. Optional, if not provided the message will be added to the channel itself, otherwise it will be added to the thread. | **IGNORE** | The thread_ts argument is a timestamp used to identify the parent message or thread, but it does not represent a quantity or policy concept. | Not evaluated by this component. |

### `conversations_history`

4 argument(s), one model call, 13s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_id` | `string` — - `channel_id` (string): ID of the channel in format Cxxxxxxxxxx or its name starting with #... or @... aka #general or @username_dm. | **POLICY** | The channel_id identifies a specific channel or user, which is subject to policy. | Resolve “channel_or_user” against the organisation's policy: may this caller act on the one it named? |
| `cursor` | `string` — Cursor for pagination. Use the value of the last row and column in the response as next_cursor field returned from the previous request. | **IGNORE** | Cursor is used for pagination and does not have an inherent order or identity that would be relevant to policy. | Not evaluated by this component. |
| `include_activity_messages` | `boolean` · default=false — If true, the response will include activity messages such as 'channel_join' or 'channel_leave'. Default is boolean false. | **IGNORE** | This argument changes the content of the response but does not affect which resource is accessed, so it's operational and not subject to policy. | Not evaluated by this component. |
| `limit` | `string` · default="1d" — Limit of messages to fetch in format of maximum ranges of time (e.g. 1d - 1 day, 1w - 1 week, 30d - 30 days, 90d - 90 days which is a default limit for free tier history) or number of messages (e.g. 50). Must be empty when 'cursor' is provided. | **RANGE** / duration | The limit argument can specify a duration or number of messages, which has an inherent order (e.g., longer time periods or more messages). | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `conversations_join`

1 argument(s), one model call, 17s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_id` | `string` — ID of the channel in format Cxxxxxxxxxx or its name starting with #... (e.g., #general). | **POLICY** | The channel ID or name is used to identify which specific channel the user wants to join, and this selection must be validated against organizational policies. | Resolve “channel” against the organisation's policy: may this caller act on the one it named? |

### `conversations_leave`

1 argument(s), one model call, 16s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_id` | `string` — ID of the channel in format Cxxxxxxxxxx or its name starting with #... or @... (e.g., #general, @username). | **POLICY** | The channel_id is an identifier that determines which specific channel or user the action acts upon, and this requires policy validation. | Resolve “channel_or_user_identifier” against the organisation's policy: may this caller act on the one it named? |

### `conversations_mark`

2 argument(s), one model call, 19s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_id` | `string` — ID of the channel in format Cxxxxxxxxxx or its name starting with #... or @... (e.g., #general, @username). | **POLICY** | The channel or user ID/name is a policy concept as it determines which specific communication context the operation acts on. | Resolve “channel_or_user” against the organisation's policy: may this caller act on the one it named? |
| `ts` | `string` — Timestamp of the message to mark as read up to. If not provided, marks all messages as read. | **RANGE** / temporal | The timestamp is a temporal value that indicates up to which point messages are marked as read. It has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `conversations_replies`

5 argument(s), one model call, 14s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_id` | `string` — ID of the channel in format Cxxxxxxxxxx or its name starting with #... or @... aka #general or @username_dm. | **POLICY** | The channel ID or name is used to identify which specific channel the call acts on. | Resolve “channel” against the organisation's policy: may this caller act on the one it named? |
| `cursor` | `string` — Cursor for pagination. Use the value of the last row and column in the response as next_cursor field returned from the previous request. | **IGNORE** | Cursor values are typically opaque tokens used for pagination and do not have a meaningful order or policy context. | Not evaluated by this component. |
| `include_activity_messages` | `boolean` · default=false — If true, the response will include activity messages such as 'channel_join' or 'channel_leave'. Default is boolean false. | **IGNORE** | This is an operational switch that changes how the result is rendered, but does not affect which resources are acted upon. | Not evaluated by this component. |
| `limit` | `string` · default="1d" — Limit of messages to fetch in format of maximum ranges of time (e.g. 1d - 1 day, 30d - 30 days, 90d - 90 days which is a default limit for free tier history) or number of messages (e.g. 50). Must be empty when 'cursor' is provided. | **RANGE** / duration | The limit can be specified as a duration or number of messages, indicating a quantity that has an order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `thread_ts` | `string` — Unique identifier of either a thread's parent message or a message in the thread. ts must be the timestamp in format 1234567890.123456 of an existing message with 0 or more replies. | **RANGE** / temporal | The timestamp is a temporal value that has an order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `conversations_search_messages`

12 argument(s), one model call, 39s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `cursor` | `string` · default="" — Cursor for pagination. Use the value of the last row and column in the response as next_cursor field returned from the previous request. | **IGNORE** | The cursor is used for pagination and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `filter_date_after` | `string` — Filter messages sent after a specific date in format 'YYYY-MM-DD'. Example: '2023-10-01', 'July', 'Yesterday' or 'Today'. If not provided, all dates will be searched. | **RANGE** / temporal | The date after which messages are filtered has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `filter_date_before` | `string` — Filter messages sent before a specific date in format 'YYYY-MM-DD'. Example: '2023-10-01', 'July', 'Yesterday' or 'Today'. If not provided, all dates will be searched. | **RANGE** / temporal | The date before which messages are filtered has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `filter_date_during` | `string` — Filter messages sent during a specific period in format 'YYYY-MM-DD'. Example: 'July', 'Yesterday' or 'Today'. If not provided, all dates will be searched. | **RANGE** / temporal | The period during which messages are filtered has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `filter_date_on` | `string` — Filter messages sent on a specific date in format 'YYYY-MM-DD'. Example: '2023-10-01', 'July', 'Yesterday' or 'Today'. If not provided, all dates will be searched. | **RANGE** / temporal | The date on which messages are filtered has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `filter_in_channel` | `string` — Filter messages in a specific public/private channel by its ID or name. Example: 'C1234567890', 'G1234567890', or '#general'. If not provided, all channels will be searched. | **POLICY** | The channel ID or name is a policy concept as it identifies the specific channel. | Resolve “channel_id_or_name” against the organisation's policy: may this caller act on the one it named? |
| `filter_in_im_or_mpim` | `string` — Filter messages in a direct message (DM) or multi-person direct message (MPIM) conversation by its ID or name. Example: 'D1234567890' or '@username_dm'. If not provided, all DMs and MPIMs will be searched. | **POLICY** | The DM or MPIM ID or name is a policy concept as it identifies the specific conversation. | Resolve “dm_or_mpim_id_or_name” against the organisation's policy: may this caller act on the one it named? |
| `filter_threads_only` | `boolean` — If true, the response will include only messages from threads. Default is boolean false. | **IGNORE** | This is a boolean flag that changes the result set but does not have an order or policy context. | Not evaluated by this component. |
| `filter_users_from` | `string` — Filter messages from a specific user by their ID or display name. Example: 'U1234567890' or '@username'. If not provided, all users will be searched. | **POLICY** | The user ID or display name is a policy concept as it identifies the specific user. | Resolve “user_id_or_display_name” against the organisation's policy: may this caller act on the one it named? |
| `filter_users_with` | `string` — Filter messages with a specific user by their ID or display name in threads and DMs. Example: 'U1234567890' or '@username'. If not provided, all threads and DMs will be searched. | **POLICY** | The user ID or display name is a policy concept as it identifies the specific user. | Resolve “user_id_or_display_name” against the organisation's policy: may this caller act on the one it named? |
| `limit` | `number` · default=20 — The maximum number of items to return. Must be an integer between 1 and 100. | **RANGE** / count | The limit has a meaningful order and is bounded by the schema. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from the schema's declared minimum/maximum. |
| `search_query` | `string` — Search query to filter messages. Example: 'marketing report' or full URL of Slack message e.g. 'https://slack.com/archives/C1234567890/p1234567890123456', then the tool will return a single message matching given URL, herewith all other parameters will be ignored. | **IGNORE** | The search query is free text and does not have a meaningful order or policy context. | Not evaluated by this component. |

### `conversations_unreads`

6 argument(s), one model call, 21s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channel_types` | `string` · default="all" — Filter by channel type: 'all' (default), 'dm' (direct messages), 'group_dm' (group DMs), 'partner' (ext-* channels), 'internal' (other channels). | **POLICY** | The value selects which type of channels to act on, changing the context of the call. | Resolve “channel_type” against the organisation's policy: may this caller act on the one it named? |
| `include_messages` | `boolean` · default=true — If true (default), returns the actual unread messages. If false, returns only a summary of channels with unreads. | **IGNORE** | This argument changes only how the result is rendered (whether it includes messages or not). | Not evaluated by this component. |
| `include_muted` | `boolean` · default=false — If true, includes muted channels in results. Default is false (muted channels are excluded, matching Slack app behavior). | **IGNORE** | This argument changes only whether muted channels are included in results, which does not change the identity of the resources acted upon. | Not evaluated by this component. |
| `max_channels` | `number` · default=50 — Maximum number of channels to fetch unreads from. Default is 50. | **RANGE** / count | The value represents a count of channels, which has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `max_messages_per_channel` | `number` · default=10 — Maximum messages to fetch per channel. Default is 10. | **RANGE** / count | The value represents a count of messages, which has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `mentions_only` | `boolean` · default=false — If true, only returns channels where you have @mentions. Default is false. | **IGNORE** | This argument changes only whether to return channels with mentions or not, which does not change the identity of the resources acted upon. | Not evaluated by this component. |

### `usergroups_create`

4 argument(s), one model call, 21s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channels` | `string` — Comma-separated channel IDs where this group is commonly mentioned. Members get suggestions to join these channels. | **POLICY** | The value selects specific channels, which is a policy concern. | Resolve “channel_ids” against the organisation's policy: may this caller act on the one it named? |
| `description` | `string` — Purpose or description shown in group details (e.g., 'Backend and frontend engineers'). | **IGNORE** | This is free text that does not affect the scope or identity of the operation. | Not evaluated by this component. |
| `handle` | `string` — The @mention handle without the @ symbol (e.g., 'engineering' for @engineering). Keep it short and lowercase. If omitted, Slack auto-generates one from the name. | **POLICY** | The handle uniquely identifies a user group and is used for mentions, which can be subject to policy. | Resolve “user_group_handle” against the organisation's policy: may this caller act on the one it named? |
| `name` | `string` — Display name of the user group (e.g., 'Engineering Team', 'Design Squad'). | **IGNORE** | This is the display name of the user group, which does not affect the scope or identity of the operation in a way that would require policy evaluation. | Not evaluated by this component. |

### `usergroups_list`

3 argument(s), one model call, 20s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `include_count` | `boolean` · default=true — Include user count for each group. Default is true. | **IGNORE** | This is a boolean flag that only changes how the result is rendered, not which resources are acted upon. | Not evaluated by this component. |
| `include_disabled` | `boolean` · default=false — Include disabled/archived groups. Default is false. | **IGNORE** | This is a boolean flag that only changes how the result is rendered, not which resources are acted upon. | Not evaluated by this component. |
| `include_users` | `boolean` · default=false — Include list of user IDs in each group. Default is false. | **IGNORE** | This is a boolean flag that only changes how the result is rendered, not which resources are acted upon. | Not evaluated by this component. |

### `usergroups_me`

2 argument(s), one model call, 12s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `action` | `string` — Action to perform: 'list' returns CSV of groups you're a member of, 'join' adds you to a group, 'leave' removes you from a group. | **IGNORE** | The action argument changes only the operation performed, not a quantity or policy entity. | Not evaluated by this component. |
| `usergroup_id` | `string` — ID of the user group (starts with 'S', e.g., 'S0123456789'). Required for 'join' and 'leave' actions. Get IDs from usergroups_list. | **POLICY** | The usergroup_id identifies a specific user group, which is a policy entity. | Resolve “user group” against the organisation's policy: may this caller act on the one it named? |

### `usergroups_update`

5 argument(s), one model call, 19s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `channels` | `string` — New default channel IDs (comma-separated). Replaces existing default channels. | **POLICY** | The value represents specific channel IDs, which are policy-relevant identifiers. | Resolve “channel_ids” against the organisation's policy: may this caller act on the one it named? |
| `description` | `string` — New description for the group. | **IGNORE** | This is free text that does not have a meaningful order or identity relevant to policy. | Not evaluated by this component. |
| `handle` | `string` — New @mention handle (without @). Changing this changes how users mention the group. | **POLICY** | The handle changes how users mention the group, which is a specific identifier that matters for policy. | Resolve “mention_handle” against the organisation's policy: may this caller act on the one it named? |
| `name` | `string` — New display name for the group. | **IGNORE** | This is free text that does not have a meaningful order or identity relevant to policy. | Not evaluated by this component. |
| `usergroup_id` | `string` — ID of the user group to update (starts with 'S', e.g., 'S0123456789'). Get IDs from usergroups_list. | **POLICY** | The user group ID is an identifier that matters for policy, as it specifies which specific group the operation acts on. | Resolve “user_group_ids” against the organisation's policy: may this caller act on the one it named? |

### `usergroups_users_update`

2 argument(s), one model call, 18s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `usergroup_id` | `string` — ID of the user group (starts with 'S', e.g., 'S0123456789'). Get IDs from usergroups_list. | **POLICY** | The user group ID is an identifier that selects which specific user group the operation acts on. | Resolve “user_group” against the organisation's policy: may this caller act on the one it named? |
| `users` | `string` — Comma-separated user IDs that will become the COMPLETE member list (e.g., 'U0123456789,U9876543210'). All current members not in this list will be removed. | **RANGE** / count | The 'users' argument is a list of user IDs, which can be interpreted as the count of users to replace in the group. Each item within this list represents an individual user ID, making each item a policy concept. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. Each item is **POLICY** — user, so the members are checked as well as the count. |

### `users_search`

2 argument(s), one model call, 18s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `limit` | `number` · default=10 — Maximum number of results to return (1-100). Default is 10. | **RANGE** / count | The limit argument specifies a maximum number of results, which is a count. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from limits stated in the description. |
| `query` | `string` — Search query - matches against real name, display name, username, email, or a Slack user ID (e.g. U07VCEPP4N5). | **IGNORE** | The query argument is a search term that does not have an inherent order or policy context. | Not evaluated by this component. |
