### calendar_real

**Tier: M** · `calendar:real` · 13 tools · 16 assets · peak sensitivity **5**

**Owner.** CBG workplace-services team (calendar administration); contact:
`workplace@cbg.example`.

**Company.** CBG on the real Google Calendar MCP surface — 13 tools including
bulk creation (`create-events`) and account administration (`manage-accounts`).

**Expected organizational use.** Scheduling assistance: find a free slot, read
the week, create or move a meeting, RSVP. Bounded, low-volume, and always tied
to a request a human made. An agent should never need `manage-accounts`, bulk
`create-events`, or anything on the `executive` calendar.

**Content unit.** One calendar event (an entry with title, time, attendees);
for `contacts`, one person's record. **The event is the central asset of this
server**: every calendar row below is a container of events, and almost every
tool creates, reads, moves, or deletes events — the per-calendar rows exist
because the same event operation carries different consequences depending on
whose calendar it touches.

**Irreversible actions.** Deleting an event silently removes a commitment (the
loss surfaces only when the meeting does not happen); sending an outbound
invite or update emails people outside the org and cannot be recalled; changes
to `connected-account-config` alter which accounts and scopes every other tool
can reach.

**Provenance.** Authored by the CBG security review, 2026-07-27, against the
13-tool `calendar_real.json` catalog capture.

**Asset severity and CIA.** `executive` and `recruiting` calendars (4) are
confidentiality-first for a non-obvious reason — the *metadata* is the leak. An
executive calendar showing a bank's counsel three times in a week discloses an
acquisition without exposing a single event body, and a recruiting calendar
discloses candidate identities and pending departures. `contacts` (4) is the
directory-scale PII asset. `personal` and `team` (3) are ordinary; `holidays`
(1) is public.

| Asset | Sens. | C | I | A | Contents | Why |
|---|---|---|---|---|---|---|
| `personal` | 3 | M | M | H | calendar · event = one entry; an individual's own schedule | Ordinary schedule; deletion is the sharp edge. |
| `team` | 3 | M | M | H | calendar · event = one entry; ordinary team scheduling | Ordinary team schedule. |
| `executive` | 4 | **H** | M | H | calendar · event = one entry; attendee lists and titles disclose deals and departures without opening a body | Metadata alone discloses deals and departures. |
| `recruiting` | 4 | **H** | M | M | calendar · event = one entry; candidate identities and pending moves | Candidate identities and pending moves. |
| `contacts` | 4 | **H** | L | L | calendar · one record per person; the whole directory in one call · population | Directory-scale PII. |
| `holidays` | 1 | L | M | L | calendar · event = one entry; the published holiday calendar · public | Public calendar. |
| `event-records` | 3 | M | M | H | calendar · what a create/update/delete targets; any event on any calendar in scope | Generic event bodies. |
| `event-attendee-lists` | 4 | **H** | L | L | calendar · who is invited to an event — the people behind the entry · population | Who meets whom — the metadata leak in list form. |
| `outbound-invite-email` | 4 | M | **H** | L | calendar · mail leaving the org under its identity; unrecallable once sent | Crosses the org boundary; unrecallable once sent. |
| `rsvp-state` | 2 | L | L | L | calendar · accept/decline state on one invitation · metadata-only | Attendance state — about-ness. |
| `connected-account-config` | 5 | **H** | **H** | M | calendar · which accounts are linked and with what scope; changing it reaches every calendar · self-sufficient · hub | Account/auth configuration — the access hub for every calendar. |
| `free-busy-availability` | 3 | **H** | L | L | calendar · busy blocks with no titles or attendees · metadata-only | Pattern-of-life metadata across calendars. |
| `calendar-directory` | 2 | L | L | L | calendar · the list of calendars, no events · metadata-only | Calendar names — metadata. |
| `color-catalog` | 1 | L | L | L | calendar · the static colour palette; no organizational state at all · public | Cosmetic color ids. |
| `calendar-records` | 3 | M | M | H | calendar · what a calendar-level write targets | Generic calendar records (generated homing asset). |
| `account-directory` | 4 | **H** | L | L | calendar · the linked-account list · metadata-only | Which accounts exist — organizational PII. |

**In general: C > A > I.** Confidentiality leads on metadata grounds.
Availability ranks second, ahead of integrity, because deletion is the sharp
edge on a calendar: `delete-event` silently removes a commitment, and the loss
only surfaces when the meeting does not happen.

