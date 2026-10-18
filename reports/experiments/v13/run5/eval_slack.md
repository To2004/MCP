# slack (slack_vireo): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 86 | 209 | 79 | 45 | 0 | 81 |
| MISUSE | 38 | 148 | 59 | 5 | 0 | 0 |
| MALICIOUS | 72 | 86 | 40 | 0 | 52 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.574 | 0.628 |
| MALICIOUS_vs_BENIGN | 0.599 | 0.678 |
| RISKY_vs_BENIGN | 0.587 | 0.653 |

No rule applied: 81 calls. With an unresolved input: 21 calls.

Inputs that set the level most often:

- `conversations_history.limit`: 494
- `conversations_search_messages.search_query`: 83
- `conversations_search_messages.filter_in_channel`: 57
- `conversations_replies.channel_id`: 54
- `conversations_search_messages.limit`: 53
- `channels_list.limit`: 49
- `conversations_join.channel_id`: 47
- `users_search.query`: 33
- `usergroups_me.action`: 27
- `conversations_mark.channel_id`: 21
- `conversations_mark.ts`: 21
- `conversations_add_message.channel_id`: 18
