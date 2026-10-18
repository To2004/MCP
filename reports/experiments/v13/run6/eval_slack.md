# slack (slack_vireo): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 284 | 49 | 58 | 28 | 0 | 81 |
| MISUSE | 133 | 53 | 59 | 5 | 0 | 0 |
| MALICIOUS | 158 | 0 | 40 | 0 | 52 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.631 | 0.628 |
| MALICIOUS_vs_BENIGN | 0.632 | 0.678 |
| RISKY_vs_BENIGN | 0.631 | 0.653 |

No rule applied: 81 calls. With an unresolved input: 21 calls.

Inputs that set the level most often:

- `conversations_history.limit`: 494
- `conversations_search_messages.search_query`: 83
- `conversations_search_messages.filter_in_channel`: 57
- `conversations_replies.limit`: 54
- `conversations_search_messages.limit`: 53
- `channels_list.limit`: 49
- `conversations_join.channel_id`: 47
- `users_search.query`: 33
- `usergroups_me.action`: 27
- `conversations_mark.channel_id`: 21
- `conversations_add_message.channel_id`: 18
- `users_search.limit`: 3
