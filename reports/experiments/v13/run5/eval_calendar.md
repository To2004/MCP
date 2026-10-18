# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 0 | 164 | 2 | 230 | 104 |
| MISUSE | 0 | 0 | 0 | 31 | 219 | 0 |
| MALICIOUS | 0 | 0 | 132 | 20 | 83 | 15 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.741 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.501 | 0.636 |
| RISKY_vs_BENIGN | 0.621 | 0.647 |

No rule applied: 119 calls. With an unresolved input: 170 calls.

Inputs that set the level most often:

- `list-events.timeMin`: 248
- `search-events.calendarId`: 171
- `create-event.calendarId`: 166
- `create-event.summary`: 101
- `get-event.calendarId`: 99
- `delete-event.calendarId`: 72
- `search-events.query`: 65
- `create-event.start`: 56
- `create-event.end`: 56
- `get-freebusy.timeMin`: 54
- `update-event.start`: 36
- `list-events.calendarId`: 33
