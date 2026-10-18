# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 0 | 157 | 239 | 0 | 104 |
| MISUSE | 0 | 0 | 0 | 0 | 250 | 0 |
| MALICIOUS | 0 | 0 | 16 | 0 | 219 | 15 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 1.000 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.906 | 0.636 |
| RISKY_vs_BENIGN | 0.953 | 0.647 |

No rule applied: 119 calls. With an unresolved input: 154 calls.

Inputs that set the level most often:

- `create-event.calendarId`: 183
- `list-events.timeMin`: 172
- `list-events.timeMax`: 172
- `search-events.calendarId`: 106
- `get-event.calendarId`: 99
- `list-events.calendarId`: 76
- `delete-event.calendarId`: 72
- `search-events.timeMin`: 65
- `search-events.timeMax`: 65
- `get-freebusy.calendars`: 54
- `get-freebusy.calendars[].id`: 54
- `create-event.summary`: 45
