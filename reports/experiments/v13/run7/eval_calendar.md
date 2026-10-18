# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 0 | 153 | 2 | 241 | 104 |
| MISUSE | 0 | 0 | 25 | 0 | 225 | 0 |
| MALICIOUS | 0 | 0 | 176 | 6 | 53 | 15 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.719 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.434 | 0.636 |
| RISKY_vs_BENIGN | 0.576 | 0.647 |

No rule applied: 119 calls. With an unresolved input: 170 calls.

Inputs that set the level most often:

- `list-events.timeMin`: 248
- `list-events.timeMax`: 248
- `search-events.timeMin`: 171
- `search-events.timeMax`: 171
- `create-event.summary`: 154
- `get-event.calendarId`: 99
- `search-events.calendarId`: 75
- `create-event.start`: 74
- `create-event.end`: 74
- `delete-event.calendarId`: 72
- `get-freebusy.calendars`: 54
- `get-freebusy.calendars[].id`: 54
