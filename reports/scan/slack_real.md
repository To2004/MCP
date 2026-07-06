# Scan — slack:real

_kind=slack · provenance=llm-scan · model_reviewed=True · bands={'low': 56, 'medium': 66, 'high': 31, 'critical': 7}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: communication
- **asset_meaning**: Slack channels (public or private) used for communication within an organization.
- **blast_radius_meaning**: The extent to which a tool can affect the content and membership of a channel, ranging from read-only operations like listing members or messages to actions that modify the channel's state such as adding messages or changing user group memberships.
- **worked_example**: The tool 'conversations_add_message' paired with the asset 'incident-response' could be severe if it adds critical incident details to a private technical channel, potentially exposing sensitive information.

## Tool impact

| tool | impact |
| --- | --- |
| `channels_list` | 1 |
| `channels_me` | 1 |
| `conversations_add_message` | 3 |
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
| `general` | 3 🟢 | 3 🟢 | 6 🟡 | 3 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 3 🟢 | 2 🟢 | 3 🟢 | 4 🟢 | 3 🟢 | 2 🟢 | 4 🟢 | 12 🟡 | 2 🟢 |
| `announcements` | 6 🟢 | 6 🟢 | 18 🟡 | 4 🟢 | 4 🟢 | 8 🟢 | 8 🟢 | 6 🟢 | 6 🟢 | 6 🟢 | 8 🟢 | 6 🟢 | 4 🟢 | 12 🟡 | 24 🟠 | 4 🟢 |
| `random` | 3 🟢 | 2 🟢 | 6 🟡 | 3 🟢 | 2 🟢 | 4 🟢 | 4 🟢 | 3 🟢 | 2 🟢 | 3 🟢 | 4 🟢 | 3 🟢 | 2 🟢 | 4 🟢 | 12 🟡 | 1 🟢 |
| `engineering` | 6 🟢 | 6 🟢 | 12 🟡 | 6 🟢 | 4 🟢 | 8 🟢 | 8 🟢 | 6 🟢 | 6 🟢 | 6 🟢 | 8 🟡 | 4 🟢 | 8 🟡 | 12 🟠 | 24 🔴 | 4 🟢 |
| `incident-response` | 12 🟠 | 8 🟡 | 36 🟠 | 8 🟡 | 16 🟡 | 16 🟡 | 16 🟡 | 12 🟠 | 8 🟡 | 8 🟡 | 16 🟡 | 8 🟡 | 24 🟠 | 16 🟡 | 48 🔴 | 8 🟡 |
| `on-call` | 12 🟠 | 8 🟡 | 36 🟠 | 8 🟡 | 24 🟠 | 16 🟡 | 16 🟡 | 12 🟠 | 8 🟡 | 12 🟠 | 16 🟡 | 8 🟡 | 16 🟡 | 16 🟡 | 48 🔴 | 8 🟡 |
| `research-team` | 12 🟠 | 8 🟡 | 36 🟠 | 12 🟠 | 16 🟡 | 16 🟡 | 16 🟡 | 12 🟠 | 8 🟡 | 8 🟡 | 16 🟡 | 8 🟡 | 16 🟡 | 16 🟡 | 48 🔴 | 8 🟡 |
| `exec-private` | 8 🟡 | 8 🟡 | 36 🟠 | 8 🟡 | 24 🟠 | 8 🟢 | 8 🟢 | 8 🟡 | 8 🟡 | 8 🟡 | 24 🟠 | 8 🟡 | 24 🟠 | 24 🟠 | 48 🔴 | 8 🟡 |
| `hr-internal` | 8 🟡 | 8 🟡 | 36 🟠 | 12 🟠 | 16 🟡 | 16 🟡 | 16 🟡 | 12 🟠 | 8 🟡 | 8 🟡 | 16 🟡 | 4 🟢 | 16 🟡 | 16 🟡 | 36 🟠 | 8 🟡 |
| `team-leads` | 12 🟠 | 8 🟡 | 36 🔴 | 8 🟠 | 16 🟠 | 16 🟡 | 16 🟡 | 12 🟠 | 8 🟠 | 8 🟡 | 24 🟠 | 4 🟢 | 16 🟡 | 24 🟠 | 48 🔴 | 8 🟡 |
