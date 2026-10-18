# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 0 | 153 | 174 | 69 | 104 |
| MISUSE | 0 | 0 | 25 | 43 | 182 | 0 |
| MALICIOUS | 0 | 0 | 132 | 34 | 69 | 15 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.832 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.547 | 0.636 |
| RISKY_vs_BENIGN | 0.690 | 0.647 |

No rule applied: 119 calls. With an unresolved input: 170 calls.

Inputs that set the level most often:

- `list-events.timeMin`: 215
- `list-events.timeMax`: 215
- `search-events.timeMin`: 171
- `search-events.timeMax`: 171
- `create-event.summary`: 126
- `get-event.calendarId`: 99
- `list-events.calendarId`: 76
- `search-events.calendarId`: 75
- `delete-event.calendarId`: 72
- `create-event.start`: 67
- `create-event.end`: 67
- `get-freebusy.calendars`: 54
