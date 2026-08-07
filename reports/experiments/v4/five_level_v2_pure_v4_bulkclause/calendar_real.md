# Scan — calendar:real

_kind=calendar · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v4 · bands={'low': 25, 'medium': 45, 'high': 9, 'critical': 1, 'na': 128}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = org profile table (never LLM-scored)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- gated blast floor (impact >= 4): sens 5 -> blast >= 4, sens 4 -> blast >= 3
- impact-keyed floor (one tier lower): impact 5 -> blast >= 3, impact 4 -> blast >= 2
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof (impact <= 3 only, never a mutation): non-escaping read caps at 4, sens-1 caps at 4 — assets flagged hub/population/self-sufficient are exempt
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: calendar
- **asset_meaning**: a calendar event or a record of an individual's schedule and availability
- **blast_radius_meaning**: the extent to which a tool can affect events across calendars, from affecting a single event to impacting multiple calendars and their configurations
- **dangerous_classes**: holds PII at scale, metadata alone discloses deals and departures, crosses the org boundary; unrecallable once sent
- **irreversible_actions**: delete-event, create-events, manage-accounts
- **worked_example**: The 'delete-event' tool on an executive calendar can silently remove a commitment, leading to missed meetings without any trace.

## Tool impact

| tool | impact |
| --- | --- |
| `list-calendars` | 2 |
| `list-events` | 3 |
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
| `personal` | 3 |
| `team` | 3 |
| `executive` | 4 |
| `recruiting` | 4 |
| `contacts` | 4 |
| `holidays` | 1 |
| `event-records` | 3 |
| `event-attendee-lists` | 4 |
| `outbound-invite-email` | 4 |
| `rsvp-state` | 2 |
| `connected-account-config` | 5 |
| `free-busy-availability` | 3 |
| `calendar-directory` | 2 |
| `color-catalog` | 1 |
| `calendar-records` | 3 |
| `account-directory` | 4 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v4, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 6 (3×1×2) 🟢 | 18 (3×2×3) 🟢 | 18 (3×2×3) 🟢 | 9 (3×1×3) 🟢 | N/A | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 45 (3×3×5) 🟡 | 6 (3×1×2) 🟢 | N/A | 24 (3×2×4) 🟢 | N/A |
| `team` | 12 (3×2×2) 🟢 | 18 (3×2×3) 🟢 | 18 (3×2×3) 🟢 | 9 (3×1×3) 🟢 | N/A | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 45 (3×3×5) 🟡 | 18 (3×3×2) 🟢 | N/A | 24 (3×2×4) 🟢 | N/A |
| `executive` | 8 (4×1×2) 🟢 | 24 (4×2×3) 🟢 | 24 (4×2×3) 🟢 | 12 (4×1×3) 🟢 | N/A | 48 (4×3×4) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 60 (4×3×5) 🟡 | 16 (4×2×2) 🟢 | N/A | 48 (4×3×4) 🟡 | N/A |
| `recruiting` | 8 (4×1×2) 🟢 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 12 (4×1×3) 🟢 | N/A | 48 (4×3×4) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 60 (4×3×5) 🟡 | 24 (4×3×2) 🟢 | N/A | 48 (4×3×4) 🟡 | N/A |
| `contacts` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `holidays` | 2 (1×1×2) 🟢 | 3 (1×1×3) 🟢 | 3 (1×1×3) 🟢 | 3 (1×1×3) 🟢 | N/A | 8 (1×2×4) 🟢 | N/A | 8 (1×2×4) 🟢 | 15 (1×3×5) 🟢 | 2 (1×1×2) 🟢 | N/A | N/A | N/A |
| `event-records` | N/A | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | 9 (3×1×3) 🟢 | N/A | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 45 (3×3×5) 🟡 | N/A | N/A | 24 (3×2×4) 🟢 | N/A |
| `event-attendee-lists` | N/A | 60 (4×5×3) 🟡 | 36 (4×3×3) 🟡 | 12 (4×1×3) 🟢 | N/A | 80 (4×5×4) 🟠 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 60 (4×3×5) 🟡 | N/A | N/A | N/A | N/A |
| `outbound-invite-email` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `rsvp-state` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (2×2×4) 🟢 | N/A |
| `connected-account-config` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 125 (5×5×5) 🔴 |
| `free-busy-availability` | N/A | 18 (3×2×3) 🟢 | 18 (3×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | 45 (3×3×5) 🟡 | 24 (3×4×2) 🟢 | N/A | N/A | N/A |
| `calendar-directory` | 4 (2×1×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `color-catalog` | N/A | N/A | N/A | N/A | 2 (1×1×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `calendar-records` | 12 (3×2×2) 🟢 | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | N/A | N/A | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 36 (3×3×4) 🟡 | 45 (3×3×5) 🟡 | N/A | N/A | N/A | N/A |
| `account-directory` | 8 (4×1×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 80 (4×4×5) 🟠 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 1 | 2 | 2 | 1 | N/A | 2 | 3 | 2 | 3 | 1 | N/A | 2 | N/A |
| `team` | 2 | 2 | 2 | 1 | N/A | 2 | 3 | 2 | 3 | 3 | N/A | 2 | N/A |
| `executive` | 1 | 2 | 2 | 1 | N/A | 3 | 4 | 3 | 3 | 2 | N/A | 3 | N/A |
| `recruiting` | 1 | 3 | 3 | 1 | N/A | 3 | 4 | 3 | 3 | 3 | N/A | 3 | N/A |
| `contacts` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `holidays` | 1 | 1 | 1 | 1 | N/A | 2 | N/A | 2 | 3 | 1 | N/A | N/A | N/A |
| `event-records` | N/A | 3 | 3 | 1 | N/A | 2 | 3 | 2 | 3 | N/A | N/A | 2 | N/A |
| `event-attendee-lists` | N/A | 5 | 3 | 1 | N/A | 5 | 5 | 3 | 3 | N/A | N/A | N/A | N/A |
| `outbound-invite-email` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `rsvp-state` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A |
| `connected-account-config` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 |
| `free-busy-availability` | N/A | 2 | 2 | N/A | N/A | N/A | N/A | N/A | 3 | 4 | N/A | N/A | N/A |
| `calendar-directory` | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `color-catalog` | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `calendar-records` | 2 | 3 | 3 | N/A | N/A | 2 | 3 | 3 | 3 | N/A | N/A | N/A | N/A |
| `account-directory` | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 |

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
