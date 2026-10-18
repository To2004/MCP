# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 0 | 159 | 237 | 0 | 104 |
| MISUSE | 0 | 0 | 0 | 31 | 219 | 0 |
| MALICIOUS | 0 | 0 | 89 | 0 | 146 | 15 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.971 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.721 | 0.636 |
| RISKY_vs_BENIGN | 0.846 | 0.647 |

No rule applied: 119 calls. With an unresolved input: 154 calls.

Inputs that set the level most often:

- `create-event.calendarId`: 185
- `list-events.timeMin`: 172
- `list-events.timeMax`: 172
- `create-event.summary`: 120
- `search-events.calendarId`: 106
- `get-event.calendarId`: 99
- `search-events.timeMin`: 96
- `search-events.timeMax`: 96
- `list-events.calendarId`: 76
- `delete-event.calendarId`: 72
- `get-event.eventId`: 58
- `get-freebusy.calendars`: 54
