# Scan — slack:cbg

_kind=slack · provenance=llm-scan · model_reviewed=True · bands={'low': 27, 'medium': 28, 'high': 19, 'critical': 6}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: communication platform
- **asset_meaning**: channels and user profiles within the communication workspace
- **blast_radius_meaning**: the extent to which a tool can affect messages or users across channels; from viewing limited information in one channel to posting messages that could reach all members of multiple channels
- **worked_example**: Using 'slack_post_message' on the 'exec-private' channel is high severity because it can disseminate information to a group of executives, potentially causing immediate impact.

## Tool impact

| tool | impact |
| --- | --- |
| `slack_list_channels` | 1 |
| `slack_get_channel_history` | 1 |
| `slack_get_thread_replies` | 1 |
| `slack_get_users` | 1 |
| `slack_get_user_profile` | 1 |
| `slack_post_message` | 3 |
| `slack_reply_to_thread` | 2 |
| `slack_add_reaction` | 2 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `general` | 1 |
| `announcements` | 3 |
| `random` | 1 |
| `engineering` | 2 |
| `incident-response` | 4 |
| `on-call` | 4 |
| `research-team` | 4 |
| `exec-private` | 4 |
| `hr-internal` | 4 |
| `team-leads` | 4 |

## Risk matrix (score · band)

| asset \ tool | slack_list_channels | slack_get_channel_history | slack_get_thread_replies | slack_get_users | slack_get_user_profile | slack_post_message | slack_reply_to_thread | slack_add_reaction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 3 🟢 | 3 🟢 | 3 🟢 | 3 🟢 | 0 🟢 | 9 🟡 | 6 🟡 | 4 🟡 |
| `announcements` | 9 🟢 | 6 🟢 | 6 🟢 | 6 🟡 | 0 🟢 | 36 🟠 | 18 🟡 | 12 🟡 |
| `random` | 3 🟢 | 2 🟢 | 3 🟢 | 3 🟢 | 0 🟢 | 9 🟡 | 4 🟡 | 4 🟡 |
| `engineering` | 6 🟢 | 6 🟢 | 6 🟢 | 4 🟡 | 0 🟡 | 18 🟠 | 8 🟡 | 8 🟡 |
| `incident-response` | 8 🟡 | 8 🟠 | 8 🟡 | 4 🟢 | 0 🟢 | 36 🔴 | 16 🟠 | 16 🟠 |
| `on-call` | 8 🟡 | 8 🟠 | 8 🟡 | 0 🟢 | 0 🟢 | 36 🔴 | 16 🟠 | 16 🟠 |
| `research-team` | 8 🟡 | 8 🟠 | 8 🟡 | 4 🟢 | 0 🟢 | 36 🔴 | 16 🟠 | 16 🟠 |
| `exec-private` | 8 🟡 | 8 🟠 | 8 🟡 | 8 🟡 | 0 🟢 | 48 🔴 | 24 🟠 | 16 🟡 |
| `hr-internal` | 8 🟡 | 8 🟠 | 8 🟡 | 4 🟢 | 0 🟢 | 48 🔴 | 16 🟠 | 16 🟠 |
| `team-leads` | 8 🟡 | 8 🟠 | 8 🟠 | 8 🟡 | 4 🟢 | 48 🔴 | 24 🟠 | 16 🟡 |
