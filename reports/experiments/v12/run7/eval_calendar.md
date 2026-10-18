# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 0 | 153 | 17 | 285 | 45 |
| MISUSE | 0 | 0 | 0 | 31 | 219 | 0 |
| MALICIOUS | 0 | 0 | 87 | 16 | 147 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.678 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.531 | 0.636 |
| RISKY_vs_BENIGN | 0.604 | 0.647 |

No rule applied: 45 calls. With an unresolved input: 116 calls.

Inputs that set the level most often:

- `list-events.account`: 248
- `list-events.timeMin`: 248
- `list-events.timeMax`: 248
- `search-events.calendarId`: 171
- `create-event.calendarId`: 168
- `get-event.calendarId`: 99
- `list-events.calendarId`: 76
- `delete-event.calendarId`: 72
- `delete-event.eventId`: 72
- `delete-event.sendUpdates`: 72
- `search-events.query`: 65
- `search-events.timeMin`: 65
