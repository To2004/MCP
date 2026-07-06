# Scan — calendar:real

_kind=calendar · provenance=llm-scan · model_reviewed=True · bands={'low': 12, 'medium': 25, 'high': 35, 'critical': 6}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: calendar
- **asset_meaning**: calendar instances (personal, team, executive, recruiting, directory, public)
- **blast_radius_meaning**: The extent of impact a tool has on an asset. A narrow touch might involve reading or listing events, while the most severe action could include deleting calendars or modifying recurring events with wide-reaching effects.
- **worked_example**: The 'delete-event' tool paired with the 'recruiting' asset class is highly severe because it can permanently remove events containing sensitive applicant information.

## Tool impact

| tool | impact |
| --- | --- |
| `list-calendars` | 1 |
| `list-events` | 1 |
| `search-events` | 1 |
| `get-event` | 1 |
| `list-colors` | 1 |
| `create-event` | 3 |
| `create-events` | 3 |
| `update-event` | 3 |
| `delete-event` | 3 |
| `get-freebusy` | 1 |
| `get-current-time` | 1 |
| `respond-to-event` | 2 |
| `manage-accounts` | 2 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `personal` | 3 |
| `team` | 4 |
| `executive` | 4 |
| `recruiting` | 4 |
| `contacts` | 4 |
| `holidays` | 1 |

## Risk matrix (score · band)

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 12 🟡 | 12 🟡 | 12 🟡 | 3 🟢 | 12 🟡 | 18 🟠 | 27 🟠 | 18 🟠 | 18 🟠 | 12 🟡 | 3 🟢 | 12 🟡 | 6 🟢 |
| `team` | 16 🟠 | 16 🟠 | 16 🟠 | 4 🟡 | 16 🟠 | 24 🟠 | 48 🔴 | 36 🟠 | 24 🟠 | 16 🟠 | 4 🟡 | 16 🟡 | 16 🟡 |
| `executive` | 16 🟠 | 16 🟠 | 16 🟠 | 4 🟡 | 16 🟠 | 24 🟠 | 48 🔴 | 36 🟠 | 36 🟠 | 16 🟠 | 4 🟡 | 16 🟡 | 16 🟡 |
| `recruiting` | 16 🟠 | 16 🟠 | 16 🟠 | 8 🟡 | 16 🟠 | 36 🟠 | 48 🔴 | 48 🔴 | 60 🔴 | 16 🟠 | 4 🟡 | 16 🟡 | 16 🟡 |
| `contacts` | 16 🟠 | 16 🟠 | 16 🟠 | 8 🟡 | 16 🟠 | 24 🟠 | 48 🔴 | 36 🟠 | 24 🟠 | 16 🟠 | 4 🟡 | 16 🟡 | 32 🟠 |
| `holidays` | 4 🟢 | 4 🟢 | 4 🟢 | 1 🟢 | 4 🟢 | 6 🟡 | 12 🟡 | 6 🟡 | 6 🟡 | 4 🟢 | 1 🟢 | 4 🟢 | 0 🟢 |
