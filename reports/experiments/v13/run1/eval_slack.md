# slack (slack_vireo): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 257 | 49 | 29 | 28 | 0 | 137 |
| MISUSE | 133 | 12 | 21 | 0 | 79 | 5 |
| MALICIOUS | 158 | 0 | 0 | 0 | 40 | 52 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.718 | 0.628 |
| MALICIOUS_vs_BENIGN | 0.524 | 0.678 |
| RISKY_vs_BENIGN | 0.621 | 0.653 |

No rule applied: 194 calls. With an unresolved input: 0 calls.

Inputs that set the level most often:

- `conversations_history.limit`: 494
- `conversations_search_messages.filter_in_channel`: 176
- `conversations_replies.limit`: 54
- `channels_list.limit`: 49
- `users_search.query`: 33
- `conversations_search_messages.search_query`: 29
- `users_search.limit`: 8
