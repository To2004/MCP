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

## Tool atomic operations

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
