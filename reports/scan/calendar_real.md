# Scan — calendar:real

_kind=calendar · provenance=llm-scan · model_reviewed=True · bands={'low': 18, 'medium': 16, 'high': 30, 'critical': 14}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: calendar
- **asset_meaning**: calendar instances (personal, team, executive, recruiting, directory, public)
- **blast_radius_meaning**: The extent of impact a tool has on an asset. A narrow touch might involve reading or listing events, while the most severe actions include creating, updating, deleting events, and managing accounts.
- **worked_example**: The 'delete-event' tool paired with the 'executive' asset class is highly severe as it can permanently remove critical executive meeting events.

## Tool impact

| tool | impact |
| --- | --- |
| `list-calendars` | 1 |
| `list-events` | 1 |
| `search-events` | 1 |
| `get-event` | 1 |
| `list-colors` | 1 |
| `create-event` | 2 |
| `create-events` | 3 |
| `update-event` | 3 |
| `delete-event` | 3 |
| `get-freebusy` | 1 |
| `get-current-time` | 1 |
| `respond-to-event` | 2 |
| `manage-accounts` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `personal` | 3 |
| `team` | 3 |
| `executive` | 5 |
| `recruiting` | 4 |
| `contacts` | 4 |
| `holidays` | 1 |

## Risk matrix (score · band)

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 6 🟡 | 9 🟠 | 9 🟠 | 3 🟡 | 3 🟢 | 12 🟡 | 18 🟠 | 18 🟠 | 18 🔴 | 9 🟠 | 3 🟢 | 12 🟡 | 27 🔴 |
| `team` | 9 🟠 | 9 🟠 | 9 🟠 | 3 🟡 | 9 🟠 | 12 🟠 | 36 🔴 | 27 🟠 | 27 🔴 | 9 🟠 | 3 🟢 | 12 🟠 | 27 🔴 |
| `executive` | 15 🟠 | 15 🟠 | 10 🟡 | 10 🟡 | 10 🟢 | 30 🟠 | 60 🔴 | 60 🔴 | 60 🔴 | 10 🟡 | 5 🟢 | 20 🟠 | 60 🔴 |
| `recruiting` | 12 🟠 | 12 🟠 | 12 🟠 | 8 🟡 | 8 🟢 | 16 🟡 | 36 🟠 | 36 🟠 | 48 🔴 | 8 🟢 | 4 🟢 | 16 🟡 | 48 🔴 |
| `contacts` | 8 🟡 | 12 🟠 | 12 🟠 | 4 🟡 | 0 🟢 | 24 🟠 | 48 🔴 | 36 🟠 | 36 🔴 | 8 🟡 | 0 🟢 | 24 🟠 | 24 🟠 |
| `holidays` | 3 🟢 | 3 🟢 | 2 🟢 | 1 🟢 | 3 🟢 | 4 🟡 | 6 🟠 | 9 🟠 | 6 🔴 | 3 🟢 | 1 🟢 | 4 🟡 | 0 🟢 |
