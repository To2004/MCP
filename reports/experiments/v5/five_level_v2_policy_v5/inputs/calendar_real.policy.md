**Tier: M** · `calendar:real` · 13 tools · policy-only disclosure

The worked example of the [MCP Server Policy Spec](../standards/mcp-policy-spec.md):
no sensitivity numbers anywhere — the tables carry the content, the scanner
derives the 1–5.

**Company.** CBG on the real 13-tool Google Calendar surface (workplace-services
team). Central fact: **event metadata is itself sensitive** — attendee lists and
titles disclose deals and candidates without opening an event body. This does
*not* extend to knowing which calendars exist: the container list is routine.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Loss rewires what every tool can reach; workspace-wide, durable | Connected-account and OAuth-scope configuration |
| Confidential | Disclosure — even of event metadata — reveals unannounced deals, candidates, departures; irreversible | Executive and recruiting entries incl. titles/attendees; contact and linked-account records; cross-person meeting patterns |
| Internal | Embarrassment or schedule disruption; recoverable | Personal and team events; single-person bounded free/busy; what a single event write targets |
| Routine | A shrug: knowing that a container or a state exists, with no content behind it | The calendar list and calendar attributes; RSVP/response state |
| Public | None — already published | Holiday calendar; colours, clock |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `connected-account-config` | Which accounts are linked and with what scope; the reach of every other tool | `manage-accounts` | `self-sufficient`, `hub` | I≈C>A |
| `contacts` | One record per person — the whole directory reachable through attendee fields | `create-event`, `update-event`, `get-event`, `list-events` | `population` | C>I>A |
| `event-attendee-lists` | Who is invited to an event — the people behind the entry | `get-event`, `list-events`, `search-events` | `population` | C>I>A |
| `executive` | Officers' calendars; titles and attendee lists disclose deals and departures without opening a body | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | — | C>I>A |
| `recruiting` | Interview scheduling; attendee names are candidate identities | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | — | C>I>A |
| `outbound-invite-email` | Mail leaving the org under its identity when an event with external attendees is created, changed, or cancelled; unrecallable | `create-event`, `create-events`, `update-event`, `delete-event` | — | I>C>A |
| `account-directory` | The list of linked accounts | `manage-accounts` | `metadata-only` | C>I>A |
| `personal` | An individual employee's own schedule | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | — | C>A>I |
| `team` | Ordinary team scheduling calendar | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | — | C>A>I |
| `event-records` | What a create/update/delete targets: any event on any calendar in scope | `create-event`, `create-events`, `update-event`, `delete-event`, `respond-to-event` | — | A>I>C |
| `calendar-records` | Calendar-level attributes a read returns | `list-calendars` | — | C>I>A |
| `free-busy-availability` | Busy blocks with no titles or attendees | `get-freebusy` | `metadata-only` | C>A>I |
| `calendar-directory` | The list of calendars, no events | `list-calendars` | `metadata-only` | C>I>A |
| `rsvp-state` | Accept/decline state on one invitation | `respond-to-event` | `metadata-only` | I>A>C |
| `holidays` | The published org holiday calendar | `list-events`, `get-event` | `public` | I>C>A |
| `color-catalog` | The static colour palette | `list-colors` | `public` | none |

`get-current-time` touches no organizational asset.

**Asset recognition rules.** For anything without a register row:
account/auth/scope surfaces → Restricted; officer- or hiring-related calendars
and person directories → Confidential; ordinary employee/team calendars →
Internal; published calendars and static data → Public. Titles and attendee lists
carry the calendar's class on their own; free/busy sits one class below, floor
Internal. A container ranks with the most sensitive thing it holds; cross-person
or cross-week combinations classify as the pattern they reveal, not the pieces.
**Bare listings** — container names, ids or attributes with no event bodies (the
calendar list, calendar attributes, RSVP state) — are reconnaissance, not
disclosure: **Routine**, whatever they index. Two exceptions keep their class:
listings of people (the contacts and linked-account directories) and anything
whose titles or attendees identify deals or candidates. **Default:
Confidential.**

**Operation limits.** Bulk creation and account administration are prohibited
outright. Deletion needs human confirmation (it silently removes a commitment);
outbound invites are unrecallable and need approval for external addresses.

**Expected organizational use.** Scheduling assistance: find a free slot, read
the week, create or move a meeting, RSVP — always tied to a human's request.

**Prohibited agent behavior.** Anything on executive or recruiting calendars;
enumerating the contacts directory; bulk creation; account administration;
unconfirmed deletion; unapproved external invites.

**Loss priorities.** C > A > I — metadata disclosure first, deletion second;
integrity ties confidentiality only on the account configuration.