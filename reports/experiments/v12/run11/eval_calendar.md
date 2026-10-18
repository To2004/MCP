# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 0 | 198 | 79 | 178 | 45 |
| MISUSE | 0 | 0 | 0 | 0 | 250 | 0 |
| MALICIOUS | 0 | 0 | 140 | 36 | 74 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.822 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.486 | 0.636 |
| RISKY_vs_BENIGN | 0.654 | 0.647 |

No rule applied: 45 calls. With an unresolved input: 170 calls.

Inputs that set the level most often:

- `list-events.calendarId`: 248
- `search-events.timeMin`: 171
- `search-events.timeMax`: 171
- `create-event.calendarId`: 148
- `create-event.start`: 120
- `create-event.end`: 120
- `list-events.timeMin`: 110
- `list-events.timeMax`: 110
- `search-events.calendarId`: 106
- `get-event.calendarId`: 99
- `create-event.summary`: 83
- `create-event.sendUpdates`: 83
