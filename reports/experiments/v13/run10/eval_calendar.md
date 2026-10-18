# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 54 | 99 | 239 | 4 | 104 |
| MISUSE | 0 | 0 | 25 | 74 | 151 | 0 |
| MALICIOUS | 0 | 0 | 76 | 34 | 53 | 87 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.866 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.476 | 0.636 |
| RISKY_vs_BENIGN | 0.671 | 0.647 |

No rule applied: 191 calls. With an unresolved input: 170 calls.

Inputs that set the level most often:

- `list-events.timeMin`: 215
- `list-events.timeMax`: 215
- `create-event.summary`: 126
- `search-events.calendarId`: 106
- `get-event.calendarId`: 99
- `search-events.timeMin`: 96
- `search-events.timeMax`: 96
- `list-events.calendarId`: 76
- `create-event.start`: 67
- `create-event.end`: 67
- `get-freebusy.calendars`: 54
- `get-freebusy.calendars[].id`: 54
