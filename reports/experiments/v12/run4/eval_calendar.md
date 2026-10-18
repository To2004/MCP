# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 0 | 0 | 47 | 408 | 45 |
| MISUSE | 0 | 0 | 0 | 0 | 250 | 0 |
| MALICIOUS | 0 | 0 | 87 | 73 | 90 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.592 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.284 | 0.636 |
| RISKY_vs_BENIGN | 0.438 | 0.647 |

No rule applied: 45 calls. With an unresolved input: 305 calls.

Inputs that set the level most often:

- `list-events.timeMin`: 248
- `list-events.timeMax`: 248
- `search-events.timeMin`: 171
- `search-events.timeMax`: 171
- `search-events.privateExtendedProperty`: 171
- `search-events.sharedExtendedProperty`: 171
- `create-event.timeZone`: 120
- `get-event.eventId`: 99
- `list-events.calendarId`: 95
- `search-events.calendarId`: 75
- `delete-event.calendarId`: 72
- `delete-event.eventId`: 72
