# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 0 | 153 | 67 | 176 | 104 |
| MISUSE | 0 | 0 | 0 | 18 | 232 | 0 |
| MALICIOUS | 0 | 0 | 76 | 4 | 83 | 87 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.807 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.429 | 0.636 |
| RISKY_vs_BENIGN | 0.618 | 0.647 |

No rule applied: 191 calls. With an unresolved input: 170 calls.

Inputs that set the level most often:

- `list-events.timeMin`: 248
- `list-events.timeMax`: 248
- `create-event.calendarId`: 166
- `create-event.summary`: 101
- `get-event.calendarId`: 99
- `search-events.calendarId`: 93
- `search-events.timeMin`: 83
- `search-events.timeMax`: 83
- `create-event.start`: 56
- `create-event.end`: 56
- `get-freebusy.calendars`: 54
- `get-freebusy.calendars[].id`: 54
