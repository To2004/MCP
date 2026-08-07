# Scan — calendar:real

_kind=calendar · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v4_static · bands={'low': 30, 'medium': 39, 'high': 9, 'critical': 1, 'na': 129}_

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

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v4_static, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | 18 (3×2×3) 🟢 | 9 (3×1×3) 🟢 | N/A | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 45 (3×3×5) 🟡 | 6 (3×1×2) 🟢 | N/A | 24 (3×2×4) 🟢 | N/A |
| `team` | 6 (3×1×2) 🟢 | 12 (3×2×2) 🟢 | 18 (3×2×3) 🟢 | 9 (3×1×3) 🟢 | N/A | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 45 (3×3×5) 🟡 | 18 (3×3×2) 🟢 | N/A | 24 (3×2×4) 🟢 | N/A |
| `executive` | 8 (4×1×2) 🟢 | 16 (4×2×2) 🟢 | 36 (4×3×3) 🟡 | 12 (4×1×3) 🟢 | N/A | 48 (4×3×4) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 60 (4×3×5) 🟡 | 24 (4×3×2) 🟢 | N/A | 48 (4×3×4) 🟡 | N/A |
| `recruiting` | 8 (4×1×2) 🟢 | 16 (4×2×2) 🟢 | 24 (4×2×3) 🟢 | 12 (4×1×3) 🟢 | N/A | 48 (4×3×4) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 60 (4×3×5) 🟡 | 16 (4×2×2) 🟢 | N/A | 48 (4×3×4) 🟡 | N/A |
| `contacts` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `holidays` | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 3 (1×1×3) 🟢 | 3 (1×1×3) 🟢 | N/A | 8 (1×2×4) 🟢 | N/A | 8 (1×2×4) 🟢 | 15 (1×3×5) 🟢 | 2 (1×1×2) 🟢 | N/A | N/A | N/A |
| `event-records` | N/A | 18 (3×3×2) 🟢 | 27 (3×3×3) 🟢 | 9 (3×1×3) 🟢 | N/A | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 45 (3×3×5) 🟡 | N/A | N/A | 24 (3×2×4) 🟢 | N/A |
| `event-attendee-lists` | N/A | 40 (4×5×2) 🟡 | 60 (4×5×3) 🟡 | 12 (4×1×3) 🟢 | N/A | 80 (4×5×4) 🟠 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 60 (4×3×5) 🟡 | N/A | N/A | N/A | N/A |
| `outbound-invite-email` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `rsvp-state` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (2×2×4) 🟢 | N/A |
| `connected-account-config` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 125 (5×5×5) 🔴 |
| `free-busy-availability` | N/A | 12 (3×2×2) 🟢 | 18 (3×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | 45 (3×3×5) 🟡 | 24 (3×4×2) 🟢 | N/A | N/A | N/A |
| `calendar-directory` | 4 (2×1×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `color-catalog` | N/A | N/A | N/A | N/A | 2 (1×1×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `calendar-records` | N/A | 12 (3×2×2) 🟢 | 18 (3×2×3) 🟢 | N/A | N/A | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 45 (3×3×5) 🟡 | N/A | N/A | N/A | N/A |
| `account-directory` | 16 (4×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 80 (4×4×5) 🟠 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal` | 1 | 1 | 2 | 1 | N/A | 2 | 3 | 2 | 3 | 1 | N/A | 2 | N/A |
| `team` | 1 | 2 | 2 | 1 | N/A | 2 | 3 | 2 | 3 | 3 | N/A | 2 | N/A |
| `executive` | 1 | 2 | 3 | 1 | N/A | 3 | 4 | 3 | 3 | 3 | N/A | 3 | N/A |
| `recruiting` | 1 | 2 | 2 | 1 | N/A | 3 | 4 | 3 | 3 | 2 | N/A | 3 | N/A |
| `contacts` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `holidays` | 1 | 1 | 1 | 1 | N/A | 2 | N/A | 2 | 3 | 1 | N/A | N/A | N/A |
| `event-records` | N/A | 3 | 3 | 1 | N/A | 2 | 3 | 2 | 3 | N/A | N/A | 2 | N/A |
| `event-attendee-lists` | N/A | 5 | 5 | 1 | N/A | 5 | 5 | 3 | 3 | N/A | N/A | N/A | N/A |
| `outbound-invite-email` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `rsvp-state` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A |
| `connected-account-config` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 |
| `free-busy-availability` | N/A | 2 | 2 | N/A | N/A | N/A | N/A | N/A | 3 | 4 | N/A | N/A | N/A |
| `calendar-directory` | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `color-catalog` | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `calendar-records` | N/A | 2 | 2 | N/A | N/A | 2 | 3 | 2 | 3 | N/A | N/A | N/A | N/A |
| `account-directory` | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 |

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
| `list-calendars` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `list-events` | `fields` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `list-events` | `privateExtendedProperty` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `list-events` | `sharedExtendedProperty` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `list-events` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `list-events` | `timeMax` | 3 | large value | magnitude/count — larger value means broader effect |
| `list-events` | `calendarId` | 2 | — | names the target resource — selects what the op touches |
| `list-events` | `timeMin` | 1 | — | minor / structural parameter |
| `list-events` | `timeZone` | 1 | — | minor / structural parameter |
| `search-events` | `query` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `search-events` | `fields` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `search-events` | `privateExtendedProperty` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `search-events` | `sharedExtendedProperty` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `search-events` | `timeMax` | 3 | large value | magnitude/count — larger value means broader effect |
| `search-events` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `search-events` | `calendarId` | 2 | — | names the target resource — selects what the op touches |
| `search-events` | `timeMin` | 1 | — | minor / structural parameter |
| `search-events` | `timeZone` | 1 | — | minor / structural parameter |
| `get-event` | `fields` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `get-event` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `get-event` | `calendarId` | 2 | — | names the target resource — selects what the op touches |
| `get-event` | `eventId` | 2 | — | names the target resource — selects what the op touches |
| `list-colors` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `create-event` | `description` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `create-event` | `attendees` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `create-event` | `recurrence` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `create-event` | `conferenceData` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `create-event` | `attachments` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `create-event` | `calendarsToCheck` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `create-event` | `allowDuplicates` | 4 | flag set true | escalating flag — flips the call to a wider/irreversible mod |
| `create-event` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `create-event` | `calendarId` | 2 | — | names the target resource — selects what the op touches |
| `create-event` | `eventId` | 2 | — | names the target resource — selects what the op touches |
| `create-event` | `colorId` | 2 | — | names the target resource — selects what the op touches |
| `create-event` | `eventType` | 2 | — | names the target resource — selects what the op touches |
| `create-event` | `summary` | 1 | — | minor / structural parameter |
| `create-event` | `start` | 1 | — | minor / structural parameter |
| `create-event` | `end` | 1 | — | minor / structural parameter |
| `create-event` | `timeZone` | 1 | — | minor / structural parameter |
| `create-event` | `location` | 1 | — | minor / structural parameter |
| `create-event` | `reminders` | 1 | — | minor / structural parameter |
| `create-event` | `transparency` | 1 | — | minor / structural parameter |
| `create-event` | `visibility` | 1 | — | minor / structural parameter |
| `create-event` | `guestsCanInviteOthers` | 1 | — | minor / structural parameter |
| `create-event` | `guestsCanModify` | 1 | — | minor / structural parameter |
| `create-event` | `guestsCanSeeOtherGuests` | 1 | — | minor / structural parameter |
| `create-event` | `anyoneCanAddSelf` | 1 | — | minor / structural parameter |
| `create-event` | `sendUpdates` | 1 | — | minor / structural parameter |
| `create-event` | `extendedProperties` | 1 | — | minor / structural parameter |
| `create-event` | `source` | 1 | — | minor / structural parameter |
| `create-event` | `duplicateSimilarityThreshold` | 1 | — | minor / structural parameter |
| `create-event` | `focusTimeProperties` | 1 | — | minor / structural parameter |
| `create-event` | `outOfOfficeProperties` | 1 | — | minor / structural parameter |
| `create-event` | `workingLocationProperties` | 1 | — | minor / structural parameter |
| `create-events` | `events` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `create-events` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `create-events` | `calendarId` | 2 | — | names the target resource — selects what the op touches |
| `create-events` | `timeZone` | 1 | — | minor / structural parameter |
| `create-events` | `sendUpdates` | 1 | — | minor / structural parameter |
| `update-event` | `description` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `update-event` | `attendees` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `update-event` | `recurrence` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `update-event` | `calendarsToCheck` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `update-event` | `conferenceData` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `update-event` | `attachments` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `update-event` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `update-event` | `calendarId` | 2 | — | names the target resource — selects what the op touches |
| `update-event` | `eventId` | 2 | — | names the target resource — selects what the op touches |
| `update-event` | `colorId` | 2 | — | names the target resource — selects what the op touches |
| `update-event` | `summary` | 1 | — | minor / structural parameter |
| `update-event` | `start` | 1 | — | minor / structural parameter |
| `update-event` | `end` | 1 | — | minor / structural parameter |
| `update-event` | `timeZone` | 1 | — | minor / structural parameter |
| `update-event` | `location` | 1 | — | minor / structural parameter |
| `update-event` | `reminders` | 1 | — | minor / structural parameter |
| `update-event` | `sendUpdates` | 1 | — | minor / structural parameter |
| `update-event` | `modificationScope` | 1 | — | minor / structural parameter |
| `update-event` | `originalStartTime` | 1 | — | minor / structural parameter |
| `update-event` | `futureStartDate` | 1 | — | minor / structural parameter |
| `update-event` | `checkConflicts` | 1 | — | minor / structural parameter |
| `update-event` | `transparency` | 1 | — | minor / structural parameter |
| `update-event` | `visibility` | 1 | — | minor / structural parameter |
| `update-event` | `guestsCanInviteOthers` | 1 | — | minor / structural parameter |
| `update-event` | `guestsCanModify` | 1 | — | minor / structural parameter |
| `update-event` | `guestsCanSeeOtherGuests` | 1 | — | minor / structural parameter |
| `update-event` | `anyoneCanAddSelf` | 1 | — | minor / structural parameter |
| `update-event` | `extendedProperties` | 1 | — | minor / structural parameter |
| `delete-event` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `delete-event` | `calendarId` | 2 | — | names the target resource — selects what the op touches |
| `delete-event` | `eventId` | 2 | — | names the target resource — selects what the op touches |
| `delete-event` | `sendUpdates` | 1 | — | minor / structural parameter |
| `get-freebusy` | `calendars` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `get-freebusy` | `timeMax` | 3 | large value | magnitude/count — larger value means broader effect |
| `get-freebusy` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `get-freebusy` | `groupExpansionMax` | 3 | large value | magnitude/count — larger value means broader effect |
| `get-freebusy` | `calendarExpansionMax` | 3 | large value | magnitude/count — larger value means broader effect |
| `get-freebusy` | `timeMin` | 1 | — | minor / structural parameter |
| `get-freebusy` | `timeZone` | 1 | — | minor / structural parameter |
| `get-current-time` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `get-current-time` | `timeZone` | 1 | — | minor / structural parameter |
| `respond-to-event` | `account` | 3 | large value | magnitude/count — larger value means broader effect |
| `respond-to-event` | `calendarId` | 2 | — | names the target resource — selects what the op touches |
| `respond-to-event` | `eventId` | 2 | — | names the target resource — selects what the op touches |
| `respond-to-event` | `response` | 1 | — | minor / structural parameter |
| `respond-to-event` | `comment` | 1 | — | minor / structural parameter |
| `respond-to-event` | `modificationScope` | 1 | — | minor / structural parameter |
| `respond-to-event` | `originalStartTime` | 1 | — | minor / structural parameter |
| `respond-to-event` | `sendUpdates` | 1 | — | minor / structural parameter |
| `manage-accounts` | `account_id` | 3 | large value | magnitude/count — larger value means broader effect |
| `manage-accounts` | `action` | 1 | — | minor / structural parameter |
