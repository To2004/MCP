# slack (slack_vireo): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 69 | 96 | 130 | 97 | 0 | 108 |
| MISUSE | 0 | 11 | 101 | 138 | 0 | 0 |
| MALICIOUS | 0 | 0 | 40 | 0 | 163 | 47 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.791 | 0.628 |
| MALICIOUS_vs_BENIGN | 0.780 | 0.678 |
| RISKY_vs_BENIGN | 0.786 | 0.653 |

No rule applied: 155 calls. With an unresolved input: 21 calls.

Inputs that set the level most often:

- `conversations_history.channel_id`: 447
- `conversations_search_messages.search_query`: 148
- `conversations_history.limit`: 62
- `conversations_search_messages.filter_in_channel`: 57
- `conversations_replies.limit`: 54
- `channels_list.limit`: 49
- `users_search.query`: 21
- `conversations_mark.channel_id`: 21
- `conversations_mark.ts`: 21
- `conversations_add_message.channel_id`: 18
- `users_search.limit`: 14
