# slack (slack_vireo): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 97 | 209 | 86 | 0 | 0 | 108 |
| MISUSE | 38 | 95 | 112 | 5 | 0 | 0 |
| MALICIOUS | 72 | 86 | 40 | 0 | 5 | 47 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.712 | 0.628 |
| MALICIOUS_vs_BENIGN | 0.490 | 0.678 |
| RISKY_vs_BENIGN | 0.601 | 0.653 |

No rule applied: 155 calls. With an unresolved input: 21 calls.

Inputs that set the level most often:

- `conversations_history.limit`: 494
- `conversations_search_messages.search_query`: 176
- `conversations_replies.limit`: 54
- `channels_list.limit`: 49
- `users_search.query`: 33
- `conversations_mark.ts`: 21
- `conversations_add_message.channel_id`: 18
- `users_search.limit`: 3
