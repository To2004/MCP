# Scan — slack:cbg

_kind=slack · provenance=llm-scan · model_reviewed=True · bands={'low': 22, 'medium': 28, 'high': 30, 'critical': 0}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: communication platform
- **asset_meaning**: channels and user profiles within the communication workspace
- **blast_radius_meaning**: the extent to which a tool can affect users or content across channels; from viewing messages in one channel to posting messages that could reach all members of the workspace
- **worked_example**: slack_post_message on exec-private: Posting a message in an executive private channel can have significant impact due to the sensitivity and importance of communications within this group.

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
| `announcements` | 1 |
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
| `general` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 1 🟢 | 12 🟡 | 4 🟢 | 4 🟢 |
| `announcements` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 1 🟢 | 12 🟡 | 4 🟢 | 4 🟢 |
| `random` | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 1 🟢 | 6 🟡 | 4 🟢 | 4 🟢 |
| `engineering` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 2 🟢 | 18 🟡 | 8 🟡 | 8 🟡 |
| `incident-response` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 4 🟡 | 24 🟠 | 16 🟡 | 16 🟡 |
| `on-call` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 4 🟡 | 24 🟠 | 16 🟡 | 16 🟡 |
| `research-team` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 4 🟡 | 24 🟠 | 16 🟡 | 16 🟡 |
| `exec-private` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 4 🟡 | 24 🟠 | 16 🟡 | 16 🟡 |
| `hr-internal` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 4 🟡 | 24 🟠 | 16 🟡 | 16 🟡 |
| `team-leads` | 16 🟠 | 16 🟠 | 16 🟠 | 16 🟠 | 4 🟡 | 24 🟠 | 16 🟡 | 16 🟡 |

## Tool atomic operations

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `slack_list_channels` | **LIST** | 1 (Low) | LIST | rules |
| `slack_get_channel_history` | **READ** | 2 (Low) | READ | rules |
| `slack_get_thread_replies` | **READ** | 2 (Low) | READ | rules |
| `slack_get_users` | **READ** | 2 (Low) | READ | rules |
| `slack_get_user_profile` | **METADATA** | 1 (Low) | METADATA | rules |
| `slack_post_message` | **BROADCAST** | 4 (High) | BROADCAST, WRITE | rules |
| `slack_reply_to_thread` | **BROADCAST** | 4 (High) | BROADCAST | rules |
| `slack_add_reaction` | **BROADCAST** | 4 (High) | BROADCAST, WRITE | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
