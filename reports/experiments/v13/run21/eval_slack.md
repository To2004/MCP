# slack (slack_vireo): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 80 | 47 | 205 | 114 | 0 | 54 |
| MISUSE | 0 | 0 | 33 | 217 | 0 | 0 |
| MALICIOUS | 0 | 0 | 0 | 40 | 210 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.844 | 0.628 |
| MALICIOUS_vs_BENIGN | 0.982 | 0.678 |
| RISKY_vs_BENIGN | 0.913 | 0.653 |

No rule applied: 54 calls. With an unresolved input: 21 calls.

Inputs that set the level most often:

- `conversations_history.channel_id`: 447
- `conversations_search_messages.filter_in_channel`: 176
- `conversations_history.limit`: 62
- `conversations_replies.channel_id`: 54
- `channels_list.limit`: 49
- `conversations_join.channel_id`: 47
- `users_search.query`: 33
- `channels_me.limit`: 30
- `conversations_unreads.channel_types`: 24
- `conversations_unreads.max_channels`: 24
- `conversations_unreads.max_messages_per_channel`: 24
- `conversations_mark.channel_id`: 21
