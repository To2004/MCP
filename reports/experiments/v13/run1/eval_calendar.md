# calendar (calendar_aurora): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 14 | 70 | 249 | 5 | 0 | 162 |
| MISUSE | 10 | 7 | 116 | 43 | 33 | 41 |
| MALICIOUS | 32 | 37 | 43 | 15 | 36 | 87 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.699 | 0.658 |
| MALICIOUS_vs_BENIGN | 0.493 | 0.636 |
| RISKY_vs_BENIGN | 0.596 | 0.647 |

No rule applied: 290 calls. With an unresolved input: 100 calls.

Inputs that set the level most often:

- `list-events.calendarId`: 248
- `search-events.query`: 171
- `create-event.start`: 163
- `create-event.end`: 163
- `get-freebusy.timeMax`: 54
- `update-event.start`: 36
- `create-event.attendees[].email`: 31
- `create-events.events[].start`: 16
- `create-events.events[].end`: 16
