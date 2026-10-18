# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 194 | 4 | 15 | 58 | 67 | 162 |
| MISUSE | 89 | 3 | 9 | 2 | 106 | 41 |
| MALICIOUS | 45 | 3 | 56 | 17 | 42 | 87 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.648 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.535 | 0.636 |
| RISKY_vs_BENIGN | 0.591 | 0.647 |

No rule applied: 290 calls. With an unresolved input: 54 calls.

Inputs that set the level most often:

- `list-events.timeMin`: 248
- `list-events.timeMax`: 248
- `search-events.timeMin`: 171
- `search-events.timeMax`: 171
- `create-event.start`: 164
- `create-event.end`: 80
- `get-freebusy.timeMin`: 54
- `update-event.end`: 36
- `create-event.attendees`: 28
- `create-event.attendees[].email`: 28
- `create-events.calendarId`: 16
- `create-events.events[].summary`: 16
