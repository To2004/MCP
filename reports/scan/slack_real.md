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
