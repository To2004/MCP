# Scan — calendar:cbg

_kind=calendar · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_desc · bands={'low': 9, 'medium': 40, 'high': 11, 'critical': 10, 'na': 73}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–25), scaled to this max.

## Inferred domain profile

- **mcp_kind**: calendar system
- **asset_meaning**: calendars and related mutable state (events, attendee lists, emails)
- **blast_radius_meaning**: the extent of calendar events or contacts affected by a tool's action -- from affecting one event to deleting all events on a calendar
- **dangerous_classes**: holds PII at scale (contacts), executive meetings with sensitive content, recruiting interviews involving candidate details
- **irreversible_actions**: delete_all_events
- **worked_example**: The 'send_email_invite' tool paired with the 'event-attendee-lists' asset can send unauthorized emails to external contacts, potentially leaking internal information.

## Tool impact

| tool | impact |
| --- | --- |
| `list_calendars` | 2 |
| `list_events` | 2 |
| `list_week` | 3 |
| `get_event` | 3 |
| `find_free_slot` | 2 |
| `access_contacts` | 3 |
| `create_event` | 4 |
| `update_event` | 4 |
| `send_email_invite` | 5 |
| `delete_event` | 5 |
| `delete_all_events` | 5 |

## Asset sensitivity

_Not scored in `impact_mode=five_level_v2_desc`: the organization's written description of this server states how severe each asset is, so no separate 1–5 sensitivity primitive is derived. The 13 assets below still form the matrix axis; the score is `blast × impact`._

| asset | sensitivity |
| --- | --- |
| `personal` | — |
| `team` | — |
| `executive` | — |
| `recruiting` | — |
| `contacts` | — |
| `holidays` | — |
| `event-records` | — |
| `event-attendee-lists` | — |
| `outbound-invite-email` | — |
| `rsvp-state` | — |
| `connected-account-config` | — |
| `free-busy-availability` | — |
| `calendar-directory` | — |

## Risk matrix (score · band)

_Each cell shows `score (blast×impact)` — sensitivity is not scored in this mode; impact_mode=five_level_v2_desc, score ranges 0–25. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list_calendars | list_events | list_week | get_event | find_free_slot | access_contacts | create_event | update_event | send_email_invite | delete_event | delete_all_events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 2 (1×2) 🟢 | 4 (2×2) 🟢 | 6 (2×3) 🟢 | 3 (1×3) 🟢 | 2 (1×2) 🟢 | N/A | 4 (1×4) 🟢 | 4 (1×4) 🟢 | N/A | 5 (1×5) 🟢 | 20 (4×5) 🔴 |
| `team` | 2 (1×2) 🟢 | 4 (2×2) 🟢 | 6 (2×3) 🟢 | 3 (1×3) 🟢 | 4 (2×2) 🟢 | N/A | 4 (1×4) 🟢 | 4 (1×4) 🟢 | 15 (3×5) 🟠 | 5 (1×5) 🟢 | 20 (4×5) 🔴 |
| `executive` | 4 (2×2) 🟢 | 6 (3×2) 🟢 | 6 (2×3) 🟢 | 6 (2×3) 🟢 | 4 (2×2) 🟢 | N/A | 4 (1×4) 🟢 | 4 (1×4) 🟢 | 25 (5×5) 🔴 | 5 (1×5) 🟢 | 25 (5×5) 🔴 |
| `recruiting` | 4 (2×2) 🟢 | 10 (5×2) 🟡 | 6 (2×3) 🟢 | 3 (1×3) 🟢 | 4 (2×2) 🟢 | N/A | 4 (1×4) 🟢 | 8 (2×4) 🟡 | 25 (5×5) 🔴 | 5 (1×5) 🟢 | 25 (5×5) 🔴 |
| `contacts` | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | 15 (5×3) 🟠 | 8 (2×4) 🟡 | N/A | 25 (5×5) 🔴 | N/A | N/A |
| `holidays` | 2 (1×2) 🟢 | 6 (3×2) 🟢 | 6 (2×3) 🟢 | 3 (1×3) 🟢 | N/A | N/A | N/A | 4 (1×4) 🟢 | N/A | 5 (1×5) 🟢 | 20 (4×5) 🔴 |
| `event-records` | N/A | 4 (2×2) 🟢 | 6 (2×3) 🟢 | 3 (1×3) 🟢 | 4 (2×2) 🟢 | N/A | 4 (1×4) 🟢 | 4 (1×4) 🟢 | N/A | 5 (1×5) 🟢 | 25 (5×5) 🔴 |
| `event-attendee-lists` | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | N/A | 8 (2×4) 🟡 | 4 (1×4) 🟢 | 10 (2×5) 🟡 | N/A | 25 (5×5) 🔴 |
| `outbound-invite-email` | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×4) 🟡 | N/A | 15 (3×5) 🟠 | N/A | N/A |
| `rsvp-state` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `connected-account-config` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `free-busy-availability` | N/A | 6 (3×2) 🟢 | 9 (3×3) 🟡 | N/A | 6 (3×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `calendar-directory` | 4 (2×2) 🟢 | N/A | N/A | N/A | 4 (2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list_calendars | list_events | list_week | get_event | find_free_slot | access_contacts | create_event | update_event | send_email_invite | delete_event | delete_all_events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 1 | 2 | 2 | 1 | 1 | N/A | 1 | 1 | N/A | 1 | 4 |
| `team` | 1 | 2 | 2 | 1 | 2 | N/A | 1 | 1 | 3 | 1 | 4 |
| `executive` | 2 | 3 | 2 | 2 | 2 | N/A | 1 | 1 | 5 | 1 | 5 |
| `recruiting` | 2 | 5 | 2 | 1 | 2 | N/A | 1 | 2 | 5 | 1 | 5 |
| `contacts` | N/A | N/A | N/A | N/A | 2 | 5 | 2 | N/A | 5 | N/A | N/A |
| `holidays` | 1 | 3 | 2 | 1 | N/A | N/A | N/A | 1 | N/A | 1 | 4 |
| `event-records` | N/A | 2 | 2 | 1 | 2 | N/A | 1 | 1 | N/A | 1 | 5 |
| `event-attendee-lists` | N/A | N/A | N/A | N/A | 2 | N/A | 2 | 1 | 2 | N/A | 5 |
| `outbound-invite-email` | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | 3 | N/A | N/A |
| `rsvp-state` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `connected-account-config` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `free-busy-availability` | N/A | 3 | 3 | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A |
| `calendar-directory` | 2 | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

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
| `update_event` | `attendees` | 4 | >= 20 recipients | can invite a large number of attendees, increasing fan-out |
| `update_event` | `duration_min` | 3 | >= 1440 (24 hours) | long durations can monopolize resources for extended periods |
| `update_event` | `event_id` | 2 | — | merely names the target |
| `update_event` | `calendar` | 1 | — | names the calendar, limited scope |
