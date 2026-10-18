# Scan — calendar:real

_kind=calendar · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v5r_uframe · bands={'low': 20, 'medium': 22, 'high': 18, 'critical': 6, 'na': 142}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = LLM classification against the org POLICY (classify -> map; the org supplies no numbers)
- tool impact = deterministic ladder (static_impact.py); the v4 impact prompt decides only where the ladder abstains (confidence < 0.5)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- blast floor, UNGATED: 
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof: REMOVED in this mode (a cap can only under-score)
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: calendar

## Tool impact

| tool | impact |
| --- | --- |
| `list-calendars` | 2 |
| `list-events` | 2 |
| `search-events` | 3 |
| `get-event` | 3 |
| `list-colors` | 2 |
| `create-event` | 4 |
| `create-events` | 4 |
| `update-event` | 4 |
| `delete-event` | 5 |
| `get-freebusy` | 2 |
| `get-current-time` | 1 |
| `respond-to-event` | 4 |
| `manage-accounts` | 5 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `connected-account-config` | 5 |
| `contacts` | 4 |
| `event-attendee-lists` | 4 |
| `executive` | 4 |
| `recruiting` | 4 |
| `outbound-invite-email` | 4 |
| `account-directory` | 5 |
| `personal` | 3 |
| `team` | 3 |
| `event-records` | 4 |
| `calendar-records` | 2 |
| `free-busy-availability` | 3 |
| `calendar-directory` | 2 |
| `rsvp-state` | 2 |
| `holidays` | 1 |
| `color-catalog` | 1 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v5r_uframe, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `connected-account-config` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 125 (5×5×5) 🔴 |
| `contacts` | N/A | 16 (4×2×2) 🟢 | 48 (4×4×3) 🟡 | 24 (4×2×3) 🟢 | N/A | 64 (4×4×4) 🟡 | 80 (4×5×4) 🟠 | 64 (4×4×4) 🟡 | N/A | N/A | N/A | N/A | N/A |
| `event-attendee-lists` | N/A | 16 (4×2×2) 🟢 | 36 (4×3×3) 🟡 | 24 (4×2×3) 🟢 | N/A | 32 (4×2×4) 🟢 | 64 (4×4×4) 🟡 | 64 (4×4×4) 🟡 | N/A | N/A | N/A | N/A | N/A |
| `executive` | N/A | 16 (4×2×2) 🟢 | 36 (4×3×3) 🟡 | 24 (4×2×3) 🟢 | N/A | 64 (4×4×4) 🟡 | 80 (4×5×4) 🟠 | 64 (4×4×4) 🟡 | 100 (4×5×5) 🔴 | N/A | N/A | N/A | N/A |
| `recruiting` | N/A | 16 (4×2×2) 🟢 | 36 (4×3×3) 🟡 | 24 (4×2×3) 🟢 | N/A | 64 (4×4×4) 🟡 | 80 (4×5×4) 🟠 | 64 (4×4×4) 🟡 | 100 (4×5×5) 🔴 | N/A | N/A | N/A | N/A |
| `outbound-invite-email` | N/A | N/A | N/A | N/A | N/A | 80 (4×5×4) 🟠 | 80 (4×5×4) 🟠 | 64 (4×4×4) 🟡 | 100 (4×5×5) 🔴 | N/A | N/A | N/A | N/A |
| `account-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 125 (5×5×5) 🔴 |
| `personal` | N/A | 12 (3×2×2) 🟢 | 18 (3×2×3) 🟢 | 9 (3×1×3) 🟢 | N/A | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 15 (3×1×5) 🟢 | 12 (3×2×2) 🟢 | N/A | 12 (3×1×4) 🟢 | N/A |
| `team` | N/A | 12 (3×2×2) 🟢 | 18 (3×2×3) 🟢 | 18 (3×2×3) 🟢 | N/A | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 30 (3×2×5) 🟢 | 12 (3×2×2) 🟢 | N/A | 24 (3×2×4) 🟢 | N/A |
| `event-records` | N/A | 16 (4×2×2) 🟢 | 36 (4×3×3) 🟡 | 24 (4×2×3) 🟢 | N/A | 64 (4×4×4) 🟡 | 80 (4×5×4) 🟠 | 64 (4×4×4) 🟡 | 100 (4×5×5) 🔴 | N/A | N/A | 64 (4×4×4) 🟡 | N/A |
| `calendar-records` | 8 (2×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `free-busy-availability` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 12 (3×2×2) 🟢 | N/A | N/A | N/A |
| `calendar-directory` | 8 (2×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `rsvp-state` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×1×4) 🟢 | N/A |
| `holidays` | N/A | 4 (1×2×2) 🟢 | 6 (1×2×3) 🟢 | 3 (1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `color-catalog` | N/A | N/A | N/A | N/A | 2 (1×1×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `connected-account-config` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 |
| `contacts` | N/A | 2 | 4 | 2 | N/A | 4 | 5 | 4 | N/A | N/A | N/A | N/A | N/A |
| `event-attendee-lists` | N/A | 2 | 3 | 2 | N/A | 2 | 4 | 4 | N/A | N/A | N/A | N/A | N/A |
| `executive` | N/A | 2 | 3 | 2 | N/A | 4 | 5 | 4 | 5 | N/A | N/A | N/A | N/A |
| `recruiting` | N/A | 2 | 3 | 2 | N/A | 4 | 5 | 4 | 5 | N/A | N/A | N/A | N/A |
| `outbound-invite-email` | N/A | N/A | N/A | N/A | N/A | 5 | 5 | 4 | 5 | N/A | N/A | N/A | N/A |
| `account-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 |
| `personal` | N/A | 2 | 2 | 1 | N/A | 2 | 3 | 2 | 1 | 2 | N/A | 1 | N/A |
| `team` | N/A | 2 | 2 | 2 | N/A | 2 | 3 | 2 | 2 | 2 | N/A | 2 | N/A |
| `event-records` | N/A | 2 | 3 | 2 | N/A | 4 | 5 | 4 | 5 | N/A | N/A | 4 | N/A |
| `calendar-records` | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `free-busy-availability` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A |
| `calendar-directory` | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `rsvp-state` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A |
| `holidays` | N/A | 2 | 2 | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `color-catalog` | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `list-calendars` | **LIST** | 1 (Low) | LIST | rules |
| `list-events` | **LIST** | 1 (Low) | LIST | rules |
| `search-events` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `get-event` | **READ** | 2 (Low) | READ | rules |
| `list-colors` | **LIST** | 1 (Low) | LIST | rules |
| `create-event` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `create-events` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `update-event` | **MODIFY** | 3 (Medium) | MODIFY | rules |
| `delete-event` | **DELETE** | 5 (Critical) | DELETE | rules |
| `get-freebusy` | **READ** | 2 (Low) | READ | rules |
| `get-current-time` | **READ** | 2 (Low) | READ | rules |
| `respond-to-event` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `manage-accounts` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `list-calendars` | `account` | 3 | — | can query multiple accounts, widening scope |
| `list-events` | `privateExtendedProperty` | 5 | — | allows filtering by potentially sensitive private properties |
| `list-events` | `fields` | 4 | — | can request additional sensitive fields |
| `list-events` | `sharedExtendedProperty` | 4 | — | allows filtering by shared extended properties, possibly rev |
| `list-events` | `account` | 3 | — | can query multiple accounts |
| `list-events` | `calendarId` | 2 | — | names the target calendar |
| `list-events` | `timeMin` | 1 | — | defines start of time range |
| `list-events` | `timeMax` | 1 | — | defines end of time range |
| `list-events` | `timeZone` | 1 | — | sets timezone for the query |
| `search-events` | `query` | 5 | — | fully controllable free text search query |
| `search-events` | `privateExtendedProperty` | 4 | — | filters by private properties, can target specific events |
| `search-events` | `sharedExtendedProperty` | 4 | — | filters by shared properties, can target specific events |
| `search-events` | `fields` | 3 | — | can broaden scope of returned data |
| `search-events` | `account` | 2 | — | names multiple accounts but doesn't control content |
| `search-events` | `calendarId` | 1 | — | identifies target calendar(s) only |
| `search-events` | `timeMin` | 1 | — | defines start of time range only |
| `search-events` | `timeMax` | 1 | — | defines end of time range only |
| `search-events` | `timeZone` | 1 | — | sets timezone for the query, no control over content |
| `get-event` | `fields` | 3 | — | can request additional data, potentially sensitive |
| `get-event` | `account` | 2 | — | names the target account |
| `get-event` | `calendarId` | 1 | — | identifies a specific calendar |
| `get-event` | `eventId` | 1 | — | identifies a specific event |
| `list-colors` | `account` | 2 | — | merely names the target |
| `create-event` | `description` | 5 | — | arbitrary content can be injected |
| `create-event` | `attendees` | 5 | >= 20 recipients | allows bulk fan-out to multiple users |
| `create-event` | `recurrence` | 5 | unbounded (no LIMIT) | allows events to recur indefinitely |
| `create-event` | `guestsCanModify` | 5 | — | allows modification by others |
| `create-event` | `anyoneCanAddSelf` | 5 | — | allows anyone to join the event |
| `create-event` | `extendedProperties` | 5 | total size >= 32K | allows storage of large amounts of data |
| `create-event` | `source` | 5 | — | arbitrary source information can be injected |
| `create-event` | `summary` | 4 | — | can contain arbitrary text for social engineering |
| `create-event` | `guestsCanInviteOthers` | 4 | — | can broaden the scope of attendees |
| `create-event` | `guestsCanSeeOtherGuests` | 4 | — | can expose attendee lists |
| `create-event` | `conferenceData` | 4 | — | can set up conference calls with arbitrary settings |
| `create-event` | `attachments` | 4 | — | can attach files to the event |
| `create-event` | `allowDuplicates` | 4 | — | allows creation of exact duplicates |
| `create-event` | `eventId` | 3 | — | potentially allows event ID manipulation |
| `create-event` | `location` | 3 | — | can contain arbitrary text for social engineering |
| `create-event` | `reminders` | 3 | — | can trigger notifications |
| `create-event` | `visibility` | 3 | — | controls event privacy settings |
| `create-event` | `sendUpdates` | 3 | — | controls notification distribution |
| `create-event` | `calendarsToCheck` | 3 | >= 10 calendars | can check multiple calendars for conflicts |
| `create-event` | `start` | 2 | — | sets event timing |
| `create-event` | `end` | 2 | — | sets event timing |
| `create-event` | `account` | 2 | — | identifies target account |
| `create-event` | `transparency` | 2 | — | affects calendar visibility |
| `create-event` | `duplicateSimilarityThreshold` | 2 | — | affects duplicate detection sensitivity |
| `create-event` | `focusTimeProperties` | 2 | — | specific properties for focus time events |
| `create-event` | `outOfOfficeProperties` | 2 | — | specific properties for out of office events |
| `create-event` | `workingLocationProperties` | 2 | — | specific properties for working location events |
| `create-event` | `calendarId` | 1 | — | specifies calendar target |
| `create-event` | `timeZone` | 1 | — | defines time zone context |
| `create-event` | `colorId` | 1 | — | affects event visibility color |
| `create-event` | `eventType` | 1 | — | defines the type of event |
| `create-events` | `events` | 5 | >= 50 events | bulk creation can overwhelm the server with a large number o |
| `create-events` | `account` | 2 | — | names the target account |
| `create-events` | `sendUpdates` | 2 | — | controls notification settings, could be used to spam |
| `create-events` | `calendarId` | 1 | — | identifies a specific calendar |
| `create-events` | `timeZone` | 1 | — | sets the timezone for events |
| `update-event` | `attendees` | 5 | >= 20 recipients | potentially large list of attendees |
| `update-event` | `recurrence` | 5 | unbounded (no LIMIT) | potentially unbounded recurrence rules |
| `update-event` | `anyoneCanAddSelf` | 5 | — | allows anyone to add themselves |
| `update-event` | `attachments` | 5 | unbounded (no LIMIT) | potentially unbounded list of attachments |
| `update-event` | `description` | 4 | — | potentially large payload of text |
| `update-event` | `modificationScope` | 4 | — | can widen modification scope |
| `update-event` | `calendarsToCheck` | 4 | >= 10 calendars | potentially large list of calendars to check for conflicts |
| `update-event` | `guestsCanModify` | 4 | — | allows attendees to modify event |
| `update-event` | `extendedProperties` | 4 | >= 300 properties or total size >= 32K | can contain large amount of application-specific data |
| `update-event` | `summary` | 3 | — | can contain arbitrary text |
| `update-event` | `location` | 3 | — | can contain arbitrary text |
| `update-event` | `reminders` | 3 | — | can contain arbitrary settings |
| `update-event` | `checkConflicts` | 3 | — | can disable conflict checking |
| `update-event` | `conferenceData` | 3 | — | can contain arbitrary conference properties |
| `update-event` | `guestsCanInviteOthers` | 3 | — | can allow broadening of attendee list |
| `update-event` | `account` | 2 | — | identifies the account |
| `update-event` | `start` | 2 | — | sets event start time |
| `update-event` | `end` | 2 | — | sets event end time |
| `update-event` | `sendUpdates` | 2 | — | controls notification behavior |
| `update-event` | `futureStartDate` | 2 | — | sets future start date for recurring events |
| `update-event` | `transparency` | 2 | — | defines event transparency |
| `update-event` | `visibility` | 2 | — | defines event visibility |
| `update-event` | `guestsCanSeeOtherGuests` | 2 | — | defines attendee visibility |
| `update-event` | `calendarId` | 1 | — | names target calendar |
| `update-event` | `eventId` | 1 | — | names specific event |
| `update-event` | `timeZone` | 1 | — | defines timezone |
| `update-event` | `colorId` | 1 | — | defines color ID |
| `update-event` | `originalStartTime` | 1 | — | defines original start time |
| `delete-event` | `sendUpdates` | 3 | — | can widen scope by sending notifications |
| `delete-event` | `eventId` | 2 | — | specifies the event to delete |
| `delete-event` | `account` | 2 | — | names the target account |
| `delete-event` | `calendarId` | 1 | — | identifies a specific calendar |
| `get-freebusy` | `calendars` | 4 | >= 50 calendars | controls breadth of query |
| `get-freebusy` | `groupExpansionMax` | 3 | >= 100 calendars | controls group expansion breadth |
| `get-freebusy` | `calendarExpansionMax` | 3 | >= 50 calendars | controls calendar expansion breadth |
| `get-freebusy` | `account` | 2 | — | names the target account(s) |
| `get-freebusy` | `timeMin` | 1 | — | sets start time, fixed value |
| `get-freebusy` | `timeMax` | 1 | — | sets end time, fixed value |
| `get-freebusy` | `timeZone` | 1 | — | defines timezone, fixed value |
| `get-current-time` | `account` | 2 | — | only names the target account |
| `get-current-time` | `timeZone` | 1 | — | limits to predefined IANA timezones, no amplification of ris |
| `respond-to-event` | `modificationScope` | 5 | 'all' | can affect all instances of a recurring event |
| `respond-to-event` | `comment` | 4 | — | allows arbitrary text input |
| `respond-to-event` | `sendUpdates` | 4 | 'all' | controls notification fan-out |
| `respond-to-event` | `response` | 3 | — | alters event status |
| `respond-to-event` | `calendarId` | 2 | — | names the target calendar |
| `respond-to-event` | `eventId` | 2 | — | identifies specific event |
| `respond-to-event` | `originalStartTime` | 2 | — | specifies time for specific instance |
| `respond-to-event` | `account` | 1 | — | selects account context |
| `manage-accounts` | `action` | 3 | — | controls the operation but within predefined actions |
| `manage-accounts` | `account_id` | 2 | — | identifies the account, no direct amplification of risk |
