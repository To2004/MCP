# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 76 | 4 | 15 | 67 | 176 | 162 |
| MISUSE | 13 | 3 | 9 | 106 | 78 | 41 |
| MALICIOUS | 45 | 3 | 128 | 6 | 53 | 15 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.575 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.532 | 0.636 |
| RISKY_vs_BENIGN | 0.553 | 0.647 |

No rule applied: 218 calls. With an unresolved input: 100 calls.

Inputs that set the level most often:

- `list-events.timeMin`: 248
- `search-events.timeMin`: 171
- `create-event.start`: 164
- `create-event.end`: 164
- `delete-event.calendarId`: 72
- `get-freebusy.timeMin`: 54
- `get-freebusy.timeMax`: 54
- `update-event.start`: 36
- `list-events.calendarId`: 33
- `create-event.attendees`: 28
- `create-event.attendees[].email`: 28
- `create-events.events[].summary`: 16
