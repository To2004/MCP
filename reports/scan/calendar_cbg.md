# Scan — calendar:cbg

_kind=calendar · provenance=llm-scan · model_reviewed=True · bands={'low': 10, 'medium': 22, 'high': 30, 'critical': 4}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: calendar management system
- **asset_meaning**: a calendar or contact directory containing events and personal information
- **blast_radius_meaning**: the extent of impact a tool has on the calendar or contact data; from viewing specific event details to modifying or deleting multiple events across various calendars
- **worked_example**: delete_event tool on executive asset: Deleting an important board meeting from the executive calendar could severely impact decision-making and planning processes.

## Tool impact

| tool | impact |
| --- | --- |
| `list_calendars` | 1 |
| `list_events` | 1 |
| `list_week` | 1 |
| `get_event` | 1 |
| `find_free_slot` | 1 |
| `access_contacts` | 1 |
| `create_event` | 2 |
| `update_event` | 2 |
| `send_email_invite` | 3 |
| `delete_event` | 3 |
| `delete_all_events` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `personal` | 4 |
| `team` | 3 |
| `executive` | 4 |
| `recruiting` | 4 |
| `contacts` | 5 |
| `holidays` | 1 |

## Risk matrix (score · band)

| asset \ tool | list_calendars | list_events | list_week | get_event | find_free_slot | access_contacts | create_event | update_event | send_email_invite | delete_event | delete_all_events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 8 🟡 | 16 🟠 | 16 🟠 | 4 🟡 | 16 🟠 | 4 🟡 | 16 🟡 | 16 🟡 | 24 🟠 | 24 🟠 | 48 🔴 |
| `team` | 12 🟡 | 12 🟡 | 12 🟡 | 3 🟢 | 12 🟡 | 3 🟢 | 12 🟡 | 12 🟡 | 18 🟠 | 18 🟠 | 36 🟠 |
| `executive` | 16 🟠 | 16 🟠 | 16 🟠 | 4 🟡 | 16 🟠 | 4 🟡 | 16 🟡 | 16 🟡 | 24 🟠 | 24 🟠 | 60 🔴 |
| `recruiting` | 16 🟠 | 16 🟠 | 16 🟠 | 8 🟡 | 16 🟠 | 16 🟠 | 16 🟡 | 16 🟡 | 24 🟠 | 24 🟠 | 48 🔴 |
| `contacts` | 20 🟠 | 20 🟠 | 20 🟠 | 5 🟡 | 20 🟠 | 20 🟠 | 20 🟠 | 20 🟠 | 30 🟠 | 30 🟠 | 60 🔴 |
| `holidays` | 4 🟢 | 4 🟢 | 4 🟢 | 1 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 6 🟡 | 6 🟡 | 12 🟡 |

## Tool atomic operations

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `list_calendars` | **LIST** | 1 (Low) | LIST | rules |
| `list_events` | **LIST** | 1 (Low) | LIST | rules |
| `list_week` | **LIST** | 1 (Low) | LIST | rules |
| `get_event` | **READ** | 2 (Low) | READ | rules |
| `find_free_slot` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `access_contacts` | **READ** | 2 (Low) | READ | verb-fallback |
| `create_event` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `update_event` | **MODIFY** | 3 (Medium) | MODIFY | rules |
| `send_email_invite` | **BROADCAST** | 4 (High) | BROADCAST | rules |
| `delete_event` | **DELETE** | 5 (Critical) | DELETE | rules |
| `delete_all_events` | **DELETE** | 5 (Critical) | DELETE | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `create_event` | `attendees` | 4 | >= 10 recipients | can bulk invite, widening scope |
| `create_event` | `duration_min` | 3 | >= 24*60 (1 day) | can set large meeting lengths |
| `create_event` | `title` | 2 | — | merely names the target |
| `create_event` | `calendar` | 2 | — | names the target calendar id |
| `create_event` | `date` | 1 | — | sets a fixed time, no amplification |
| `update_event` | `attendees` | 4 | >= 20 recipients | can invite a large number of attendees |
| `update_event` | `duration_min` | 3 | >= 1440 (24 hours) | can set an unreasonably long meeting duration |
| `update_event` | `event_id` | 2 | — | merely names the target |
| `update_event` | `calendar` | 1 | — | names the calendar, low risk |
