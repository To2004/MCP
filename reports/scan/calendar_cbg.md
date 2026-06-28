# Scan — calendar:cbg

_kind=calendar · provenance=llm-scan · model_reviewed=True · bands={'low': 6, 'medium': 28, 'high': 21, 'critical': 11}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: calendar management system
- **asset_meaning**: calendars and contact directories used for scheduling and managing events
- **blast_radius_meaning**: the extent of impact a tool has on the calendar or directory; from viewing a single event to deleting all events in a calendar or modifying multiple attendees' schedules
- **worked_example**: delete_event on executive: Deleting an important board meeting from the executive calendar could severely impact decision-making processes and planning.

## Tool impact

| tool | impact |
| --- | --- |
| `list_calendars` | 1 |
| `list_events` | 1 |
| `list_week` | 1 |
| `get_event` | 1 |
| `find_free_slot` | 1 |
| `access_contacts` | 2 |
| `create_event` | 2 |
| `update_event` | 2 |
| `send_email_invite` | 3 |
| `delete_event` | 3 |
| `delete_all_events` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `personal` | 4 |
| `team` | 4 |
| `executive` | 4 |
| `recruiting` | 4 |
| `contacts` | 4 |
| `holidays` | 2 |

## Risk matrix (score · band)

| asset \ tool | list_calendars | list_events | list_week | get_event | find_free_slot | access_contacts | create_event | update_event | send_email_invite | delete_event | delete_all_events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 12 🟠 | 12 🟠 | 12 🟠 | 4 🟡 | 8 🟡 | 8 🟡 | 16 🟡 | 16 🟡 | 36 🔴 | 24 🟠 | 48 🔴 |
| `team` | 12 🟠 | 12 🟠 | 12 🟠 | 4 🟡 | 8 🟡 | 8 🟡 | 16 🟡 | 16 🟡 | 36 🔴 | 24 🟠 | 48 🔴 |
| `executive` | 12 🟠 | 12 🟠 | 12 🟠 | 4 🟡 | 8 🟡 | 16 🟡 | 16 🟡 | 16 🟡 | 48 🔴 | 36 🟠 | 48 🔴 |
| `recruiting` | 8 🟡 | 8 🟡 | 12 🟠 | 8 🟡 | 8 🟢 | 24 🟠 | 24 🟡 | 24 🟡 | 36 🟠 | 36 🟠 | 48 🔴 |
| `contacts` | 8 🟡 | 8 🟡 | 8 🟡 | 8 🟡 | 12 🟠 | 24 🟠 | 24 🟡 | 24 🟡 | 48 🔴 | 36 🟠 | 48 🔴 |
| `holidays` | 6 🟢 | 4 🟢 | 6 🟢 | 2 🟢 | 6 🟢 | 0 🟡 | 8 🟡 | 12 🟠 | 18 🔴 | 12 🟠 | 24 🔴 |
