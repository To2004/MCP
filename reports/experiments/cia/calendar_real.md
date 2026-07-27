# Scan — calendar:real

_kind=calendar · provenance=llm-scan · model_reviewed=True · impact_mode=cia · bands={'low': 16, 'medium': 37, 'high': 25, 'critical': 0}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–150), scaled to this max.

## Inferred domain profile

- **mcp_kind**: calendar system
- **asset_meaning**: a calendar containing events and possibly personal information (PII)
- **blast_radius_meaning**: the extent of impact a tool has on the calendar's events or metadata, from affecting a single event to impacting all events across multiple calendars
- **dangerous_classes**: holds PII at scale, is a shared calendar
- **irreversible_actions**: delete-event when applied to critical calendars (e.g., executive or recruiting) without backups, create-events in bulk without conflict detection on critical calendars
- **worked_example**: The 'delete-event' tool paired with the 'recruiting' asset class is highly severe because it can remove PII of applicants, which could lead to data loss and privacy issues.

## Tool impact

| tool | impact |
| --- | --- |
| `list-calendars` | 2 |
| `list-events` | 2 |
| `search-events` | 2 |
| `get-event` | 2 |
| `list-colors` | 2 |
| `create-event` | 4 |
| `create-events` | 4 |
| `update-event` | 3 |
| `delete-event` | 5 |
| `get-freebusy` | 2 |
| `get-current-time` | 1 |
| `respond-to-event` | 3 |
| `manage-accounts` | 6 |

## Tool impact — CIA breakdown

_impact = base(1-3) + one point per violated CIA facet. ✓ = the tool violates that objective (C disclose · I modify · A make-unavailable)._

| tool | base | C | I | A | impact |
| --- | --- | --- | --- | --- | --- |
| `list-calendars` | 1 | ✓ | · | · | 2 |
| `list-events` | 1 | ✓ | · | · | 2 |
| `search-events` | 1 | ✓ | · | · | 2 |
| `get-event` | 1 | ✓ | · | · | 2 |
| `list-colors` | 1 | ✓ | · | · | 2 |
| `create-event` | 3 | · | ✓ | · | 4 |
| `create-events` | 3 | · | ✓ | · | 4 |
| `update-event` | 2 | · | ✓ | · | 3 |
| `delete-event` | 3 | · | ✓ | ✓ | 5 |
| `get-freebusy` | 1 | ✓ | · | · | 2 |
| `get-current-time` | 1 | · | · | · | 1 |
| `respond-to-event` | 2 | · | ✓ | · | 3 |
| `manage-accounts` | 3 | ✓ | ✓ | ✓ | 6 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `personal` | 3 |
| `team` | 3 |
| `executive` | 4 |
| `recruiting` | 4 |
| `contacts` | 4 |
| `holidays` | 1 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=cia, score ranges 0–150. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 6 (3×1×2) 🟢 | 24 (3×4×2) 🟢 | 18 (3×3×2) 🟢 | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | 12 (3×1×4) 🟢 | 24 (3×2×4) 🟢 | 9 (3×1×3) 🟢 | 15 (3×1×5) 🟢 | 12 (3×2×2) 🟢 | 3 (3×1×1) 🟢 | 9 (3×1×3) 🟢 | 18 (3×1×6) 🟢 |
| `team` | 6 (3×1×2) 🟢 | 24 (3×4×2) 🟢 | 18 (3×3×2) 🟢 | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | 12 (3×1×4) 🟢 | 36 (3×3×4) 🟢 | 9 (3×1×3) 🟢 | 15 (3×1×5) 🟢 | 12 (3×2×2) 🟢 | 3 (3×1×1) 🟢 | 9 (3×1×3) 🟢 | 18 (3×1×6) 🟢 |
| `executive` | 8 (4×1×2) 🟢 | 32 (4×4×2) 🟢 | 24 (4×3×2) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 16 (4×1×4) 🟢 | 48 (4×3×4) 🟡 | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 32 (4×4×2) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 24 (4×1×6) 🟢 |
| `recruiting` | 8 (4×1×2) 🟢 | 32 (4×4×2) 🟢 | 24 (4×3×2) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 16 (4×1×4) 🟢 | 48 (4×3×4) 🟡 | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 24 (4×3×2) 🟢 | 4 (4×1×1) 🟢 | 24 (4×2×3) 🟢 | 24 (4×1×6) 🟢 |
| `contacts` | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 16 (4×1×4) 🟢 | 16 (4×1×4) 🟢 | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 8 (4×1×2) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 24 (4×1×6) 🟢 |
| `holidays` | 2 (1×1×2) 🟢 | 8 (1×4×2) 🟢 | 8 (1×4×2) 🟢 | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 4 (1×1×4) 🟢 | 12 (1×3×4) 🟢 | 3 (1×1×3) 🟢 | 5 (1×1×5) 🟢 | 6 (1×3×2) 🟢 | 1 (1×1×1) 🟢 | 3 (1×1×3) 🟢 | 6 (1×1×6) 🟢 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 1 | 4 | 3 | 1 | 1 | 1 | 2 | 1 | 1 | 2 | 1 | 1 | 1 |
| `team` | 1 | 4 | 3 | 1 | 1 | 1 | 3 | 1 | 1 | 2 | 1 | 1 | 1 |
| `executive` | 1 | 4 | 3 | 1 | 1 | 1 | 3 | 1 | 1 | 4 | 1 | 1 | 1 |
| `recruiting` | 1 | 4 | 3 | 1 | 1 | 1 | 3 | 1 | 1 | 3 | 1 | 2 | 1 |
| `contacts` | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `holidays` | 1 | 4 | 4 | 1 | 1 | 1 | 3 | 1 | 1 | 3 | 1 | 1 | 1 |

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
| `list-events` | `privateExtendedProperty` | 4 | — | allows filtering by potentially sensitive private properties |
| `list-events` | `fields` | 3 | — | can request additional sensitive fields |
| `list-events` | `sharedExtendedProperty` | 3 | — | allows filtering by shared extended properties, which may be |
| `list-events` | `account` | 2 | — | names the target account(s) |
| `list-events` | `timeMin` | 2 | — | defines start of time range |
| `list-events` | `timeMax` | 2 | — | defines end of time range |
| `list-events` | `calendarId` | 1 | — | identifies specific calendar |
| `list-events` | `timeZone` | 1 | — | sets timezone for the query |
| `search-events` | `query` | 5 | — | fully controllable free text search query |
| `search-events` | `privateExtendedProperty` | 4 | — | filters by private properties, potentially revealing sensiti |
| `search-events` | `fields` | 3 | — | can broaden scope of returned data |
| `search-events` | `sharedExtendedProperty` | 3 | — | filters by shared properties, could reveal some details |
| `search-events` | `account` | 2 | — | names multiple accounts but doesn't control content |
| `search-events` | `calendarId` | 1 | — | identifies target calendar(s) only |
| `search-events` | `timeMin` | 1 | — | defines start of time range only |
| `search-events` | `timeMax` | 1 | — | defines end of time range only |
| `search-events` | `timeZone` | 1 | — | sets timezone for the query |
| `get-event` | `fields` | 3 | length >= 20 | can potentially request many fields, increasing data exposur |
| `get-event` | `account` | 2 | — | merely names the target |
| `get-event` | `calendarId` | 1 | — | names a specific calendar, low risk |
| `get-event` | `eventId` | 1 | — | identifies a single event, low risk |
| `list-colors` | `account` | 2 | — | merely names the target |
| `create-event` | `attendees` | 5 | >= 20 recipients | bulk fan-out for invitations |
| `create-event` | `recurrence` | 5 | unbounded (no LIMIT) | can create infinite events |
| `create-event` | `anyoneCanAddSelf` | 5 | — | allows anyone to join the event |
| `create-event` | `extendedProperties` | 5 | >= 300 properties or total size >= 32K | large storage and potential for abuse |
| `create-event` | `summary` | 4 | — | fully controlled payload |
| `create-event` | `description` | 4 | — | fully controlled payload |
| `create-event` | `guestsCanInviteOthers` | 4 | — | can widen scope of invitations |
| `create-event` | `guestsCanModify` | 4 | — | allows attendees to modify event details |
| `create-event` | `sendUpdates` | 4 | — | controls notification spamming |
| `create-event` | `attachments` | 4 | — | can attach malicious files |
| `create-event` | `eventId` | 3 | — | can be used to overwrite events |
| `create-event` | `location` | 3 | — | can be used to mislead or spam |
| `create-event` | `reminders` | 3 | — | can be used to spam reminders |
| `create-event` | `visibility` | 3 | — | controls who can see the event |
| `create-event` | `guestsCanSeeOtherGuests` | 3 | — | can expose attendee list |
| `create-event` | `conferenceData` | 3 | — | can be used for conference manipulation |
| `create-event` | `source` | 3 | — | defines event source |
| `create-event` | `allowDuplicates` | 3 | — | can allow creation of exact duplicates |
| `create-event` | `start` | 2 | — | sets event start time |
| `create-event` | `end` | 2 | — | sets event end time |
| `create-event` | `account` | 2 | — | names the target account |
| `create-event` | `transparency` | 2 | — | affects event visibility |
| `create-event` | `calendarsToCheck` | 2 | — | checks for conflicts in multiple calendars |
| `create-event` | `eventType` | 2 | — | defines event type |
| `create-event` | `calendarId` | 1 | — | identifies the calendar |
| `create-event` | `timeZone` | 1 | — | defines timezone |
| `create-event` | `colorId` | 1 | — | affects event color |
| `create-event` | `duplicateSimilarityThreshold` | 1 | — | threshold for duplicate detection |
| `create-event` | `focusTimeProperties` | 1 | — | specific properties for focus time events |
| `create-event` | `outOfOfficeProperties` | 1 | — | specific properties for out of office events |
| `create-event` | `workingLocationProperties` | 1 | — | specific properties for working location events |
| `create-events` | `events` | 5 | >= 50 events | bulk creation can overwhelm server |
| `create-events` | `account` | 2 | — | names the target account |
| `create-events` | `sendUpdates` | 2 | — | controls notification settings |
| `create-events` | `calendarId` | 1 | — | identifies a specific calendar |
| `create-events` | `timeZone` | 1 | — | sets the timezone for events |
| `update-event` | `attendees` | 5 | >= 20 recipients | can add a large number of attendees |
| `update-event` | `recurrence` | 5 | unbounded (no LIMIT) | can create unending recurring events |
| `update-event` | `guestsCanModify` | 5 | — | allows attendees to modify the event |
| `update-event` | `anyoneCanAddSelf` | 5 | — | allows anyone to join the event |
| `update-event` | `attachments` | 5 | unbounded (no LIMIT) | can attach a large number of files |
| `update-event` | `description` | 4 | — | can contain large amounts of data or malicious content |
| `update-event` | `modificationScope` | 4 | — | defines the scope of modifications which can be wide-ranging |
| `update-event` | `conferenceData` | 4 | — | can add or update conference links which can be abused |
| `update-event` | `guestsCanInviteOthers` | 4 | — | can allow unauthorized invitations |
| `update-event` | `extendedProperties` | 4 | >= 300 properties or total size >= 32K | can store large amounts of data |
| `update-event` | `summary` | 3 | — | can contain arbitrary text |
| `update-event` | `location` | 3 | — | can contain arbitrary text |
| `update-event` | `reminders` | 3 | — | configures reminders which can be abused for spamming |
| `update-event` | `sendUpdates` | 3 | — | controls notification spamming |
| `update-event` | `calendarsToCheck` | 3 | >= 5 calendars | can specify multiple calendars for conflicts |
| `update-event` | `visibility` | 3 | — | controls who sees the event |
| `update-event` | `guestsCanSeeOtherGuests` | 3 | — | controls privacy of attendee list |
| `update-event` | `account` | 2 | — | identifies the account |
| `update-event` | `start` | 2 | — | sets the start time |
| `update-event` | `end` | 2 | — | sets the end time |
| `update-event` | `originalStartTime` | 2 | — | sets original start time for recurring events |
| `update-event` | `futureStartDate` | 2 | — | defines the future start date for modifications |
| `update-event` | `transparency` | 2 | — | defines event visibility status |
| `update-event` | `calendarId` | 1 | — | names the target calendar |
| `update-event` | `eventId` | 1 | — | names the event to update |
| `update-event` | `timeZone` | 1 | — | defines timezone |
| `update-event` | `colorId` | 1 | — | defines color ID |
| `update-event` | `checkConflicts` | 1 | — | controls conflict checking |
| `delete-event` | `sendUpdates` | 3 | — | can widen scope by sending notifications |
| `delete-event` | `account` | 2 | — | names the target account |
| `delete-event` | `calendarId` | 1 | — | identifies a specific calendar |
| `delete-event` | `eventId` | 1 | — | specifies the event to delete |
| `get-freebusy` | `groupExpansionMax` | 5 | >= 100 calendars | controls maximum expansion of groups into calendars |
| `get-freebusy` | `calendarExpansionMax` | 5 | >= 50 calendars | controls maximum number of calendars to expand |
| `get-freebusy` | `calendars` | 4 | >= 50 calendars | controls breadth of query |
| `get-freebusy` | `account` | 2 | — | names the target, but does not control scope |
| `get-freebusy` | `timeMin` | 1 | — | sets start time, no control over scope or magnitude |
| `get-freebusy` | `timeMax` | 1 | — | sets end time, no control over scope or magnitude |
| `get-freebusy` | `timeZone` | 1 | — | defines timezone context, not a risk factor |
| `get-current-time` | `account` | 2 | — | only names the target account |
| `get-current-time` | `timeZone` | 1 | — | limits to predefined IANA timezones, no amplification of ris |
| `respond-to-event` | `modificationScope` | 5 | 'all' | can affect all instances of a recurring event, broadens impa |
| `respond-to-event` | `comment` | 4 | — | potentially carries arbitrary text, could be used for inject |
| `respond-to-event` | `sendUpdates` | 4 | 'all' | can send notifications to all guests, potentially amplifying |
| `respond-to-event` | `response` | 3 | — | can influence event status but not directly harmful |
| `respond-to-event` | `calendarId` | 2 | — | merely names the target |
| `respond-to-event` | `eventId` | 2 | — | identifies specific event, not inherently risky |
| `respond-to-event` | `originalStartTime` | 2 | — | required for specific instance modification, not inherently  |
| `respond-to-event` | `account` | 1 | — | optional context for operation, low risk |
| `manage-accounts` | `action` | 3 | — | controls the operation but within predefined actions |
| `manage-accounts` | `account_id` | 2 | — | identifies the account, no direct amplification of risk |
