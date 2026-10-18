# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 0 | 105 | 65 | 285 | 45 |
| MISUSE | 0 | 0 | 0 | 0 | 250 | 0 |
| MALICIOUS | 0 | 0 | 160 | 16 | 74 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.715 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.360 | 0.636 |
| RISKY_vs_BENIGN | 0.537 | 0.647 |

No rule applied: 45 calls. With an unresolved input: 170 calls.

Inputs that set the level most often:

- `list-events.timeMin`: 248
- `list-events.timeMax`: 248
- `create-event.calendarId`: 185
- `create-event.summary`: 120
- `create-event.sendUpdates`: 120
- `search-events.calendarId`: 106
- `get-event.calendarId`: 99
- `list-events.calendarId`: 76
- `delete-event.calendarId`: 72
- `delete-event.eventId`: 72
- `search-events.timeMin`: 65
- `search-events.timeMax`: 65
