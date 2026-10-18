# slack (slack_vireo): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 58 | 96 | 151 | 114 | 0 | 81 |
| MISUSE | 0 | 0 | 33 | 217 | 0 | 0 |
| MALICIOUS | 0 | 0 | 0 | 30 | 220 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.851 | 0.628 |
| MALICIOUS_vs_BENIGN | 0.986 | 0.678 |
| RISKY_vs_BENIGN | 0.919 | 0.653 |

No rule applied: 81 calls. With an unresolved input: 21 calls.

Inputs that set the level most often:

- `conversations_history.channel_id`: 447
- `conversations_search_messages.filter_in_channel`: 166
- `conversations_history.limit`: 62
- `conversations_replies.channel_id`: 54
- `channels_list.limit`: 49
- `conversations_join.channel_id`: 47
- `users_search.query`: 33
- `usergroups_me.action`: 27
- `conversations_search_messages.search_query`: 27
- `conversations_mark.channel_id`: 21
- `conversations_mark.ts`: 21
- `conversations_add_message.channel_id`: 18
