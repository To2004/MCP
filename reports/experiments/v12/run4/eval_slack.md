# slack (slack_vireo): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 111 | 173 | 114 | 21 | 81 |
| MISUSE | 0 | 0 | 88 | 162 | 0 | 0 |
| MALICIOUS | 0 | 0 | 40 | 0 | 210 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.743 | 0.628 |
| MALICIOUS_vs_BENIGN | 0.911 | 0.678 |
| RISKY_vs_BENIGN | 0.827 | 0.653 |

No rule applied: 81 calls. With an unresolved input: 21 calls.

Inputs that set the level most often:

- `conversations_history.channel_id`: 432
- `conversations_search_messages.search_query`: 148
- `conversations_search_messages.limit`: 74
- `conversations_history.limit`: 62
- `conversations_search_messages.filter_in_channel`: 57
- `channels_list.channel_types`: 49
- `channels_list.limit`: 49
- `conversations_join.channel_id`: 47
- `conversations_replies.channel_id`: 38
- `conversations_replies.thread_ts`: 37
- `users_search.limit`: 33
- `usergroups_me.action`: 27
