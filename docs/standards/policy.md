# Policy template (abstract, framework-agnostic)

A lighter alternative to [mcp-policy-spec.md](mcp-policy-spec.md) (v1, CIA-columned)
and the [v7 ISO/NIST/CIS arms](policy-authoring-rules.md): no named classification
ladder, no CIA triple, no per-asset owner. An org states its **context** and its
**assets**; the scanner does the classifying. Everything an asset needs to justify
its own weight lives in one prose `Description` cell, reasoned against the org
context above it — not looked up in a table.

Use this when you want the register to stand alone and be legible to a human
reading it top to bottom, at the cost of giving the scanner less explicit
structure to lean on than the ladder-based specs provide. See
[policy-authoring-rules.md](policy-authoring-rules.md)'s framework-comparison
table before choosing this over a ladder-based arm for a real scoring run —
the accuracy tradeoff of dropping the ladder has not been measured for this
shape yet.

## Template

### Block 0 — Org context

Written once per organization, shared across every server section under it.

```
Industry / function:        <what the org does>
Regulatory environment:     <regimes that apply, or "none">
Stakeholders & their stake: <who cares if this leaks/is misused, and specifically why — one line each>
Scope boundary:             <what this policy covers / explicitly excludes>
```

### Block 0.5 — What makes an asset important here

Guidance, not a ranking — reasoning factors a good `Description` cell should
*demonstrate*, in its own words, grounded in Block 0. Not a checklist to score
an asset against; the scanner reads the description's reasoning, not a lookup
against this list.

An asset carries more weight when it involves things like:

- **identifies or is traceable to a specific real person** — e.g. "a named
  employee's home address" vs. "a role title"
- **enables an action with real-world consequence if misused** — e.g. "can
  initiate a payment" vs. "can view a payment's status"
- **is irreversible or hard to undo once acted on** — e.g. "permanently
  deletes" vs. "archives, recoverable for 30 days"; this includes disclosure
  that can't be un-read, and operational commitments (a duty period, a
  maintenance window) whose alteration has consequences independent of
  whether the entry itself was ever secret
- **is visible beyond its intended audience if exposed** — e.g. "shared with
  the whole org" vs. "visible only to the requester"
- **ties to a stakeholder or regulatory concern named in Block 0** — a
  stakeholder in Block 0 explicitly named this data type

An asset carries less weight when it's:

- **the existence or state of something, with no content behind it** — e.g.
  "a container exists" vs. "a container's contents"
- **already public**, or freely visible to anyone with basic access
- **reversible with no lasting effect** if misused

### Table 2 — Asset register *(mandatory, per server)*

| Asset | Description | Tools |
|---|---|---|
| | *names the object, states its boundary, and — using Block 0.5's factors — states in one or two clauses why it matters or doesn't, grounded in Block 0* | *every tool that reads or writes this asset* |

### Table 3 — Tool input rules *(optional, per server — only if a tool has a value-triggered constraint)*

| Tool | Argument | Constraint | Which asset it gates |
|---|---|---|---|
| | | *specific values that override the asset's normal weight — e.g. a sanctioned-country list on a `country` argument, an `admin` value on a `role` argument* | |

Omit this table for a server entirely if none of its tools have an argument
whose *value* — not just its type or presence — changes what the call should
be treated as. Most servers won't have one; don't force an empty table.

### Block 4 — Normal use & baseline *(per server)*

What the org considers an ordinary call on this server, so a call's inputs
can be judged against something. Without it, a scanner can say that a `limit`
or an `amount` is a quantity but never whether a given value is large *here*
(`100` is huge for one input and nothing for another).

```
Normal workflow:   <one or two sentences: who calls what, how often, at what scale>
```

### Table 4 — Input baseline *(optional — a row only where the org wants to say something)*

| Tool | Arguments | Normal | Unusual | Basis |
|---|---|---|---|---|
| | *one input, or several that only mean something together* | *what a typical call passes: a number, a scope, or a named target* | *what would be out of the ordinary; may be left blank* | `stated` · `draft` |

Rules for filling it in:

- **Nothing here is required.** The table is a place to put a baseline, not a
  checklist. Cover only the inputs the org has something to say about; most
  inputs on most tools will have no row, and that is fine.
- **A row can cover several inputs of the same tool.** List them together in
  `Arguments` when the baseline is about the combination (`page` + `per_page`
  is total rows read; `timeMin` + `timeMax` is the window length;
  `owner` + `repo` is which repository). `Normal` then describes the
  combination, not each input on its own.
- **`Basis: stated`**: the number or scope comes from the org. **`draft`**:
  proposed from the rest of this document's wording, waiting for the org to
  confirm. A reader must always be able to tell which is which.
- **Never invent a number.** If the org cannot say what is normal, leave the
  row out. The scanner then falls back to schema bounds and, at run time, to
  observed traffic.
- Rows suit inputs that carry a **quantity or extent** or a **named scope**.
  Do not add rows for free text or formatting options.
- Table 3 says which *values* are special (a sanctioned country); Table 4 says
  how *much* is normal. A row belongs in exactly one of them.

That's the whole document shape: Block 0 → Block 0.5 → Table 2 → Table 3
(conditional) → Block 4 → Table 4 (optional). No named tiers, no CIA, no
owner, and no number unless the org stated it.

## Worked example — `calendar_aurora` (Google Calendar, Aurora Airways)

Rebuilt under this template from the existing `calendar_aurora` register in
[server-policies.md](../mcp-tools/server-policies.md#calendar_aurora) — real
13-tool Google Calendar surface, verified against the live server. Only the
shape changes here (no ladder, no CIA/Flags columns, reasoning folded into
`Description`); the underlying facts are the same ones already verified there.

### Block 0 — Org context

```
Industry / function:        Commercial aviation — Aurora Airways' workplace-
                             services team, on the org's real Google Calendar
                             deployment.
Regulatory environment:     Aviation safety / airworthiness oversight —
                             certification inspections and safety-board
                             reviews appear directly on this calendar.
Stakeholders & their stake: Executives — fleet-order and route-launch
                               decisions must stay unannounced until filed.
                             Regulators — audit integrity and inspector
                               identity must not leak ahead of a review.
                             Flight crew & operations — duty periods and
                               standby blocks are safety-critical; an altered
                               block can push a crew over a flight-time limit.
                             Engineering — maintenance and aircraft-on-ground
                               windows set airworthiness deadlines.
Scope boundary:              Covers the 13-tool `calendar:aurora` surface
                             only. Excludes the rostering and engineering
                             systems of record — this calendar mirrors their
                             commitments but does not author them.
```

### Table 2 — Asset register

| Asset | Description | Tools |
|---|---|---|
| `connected-account-config` | Which Google accounts are linked and under what OAuth scope — this is the reach of every other tool in the catalog, so it matters independent of any single event's content. | `manage-accounts` |
| `contacts` | One record per person, reachable through attendee fields on any event — identifies real individuals across the whole directory. | `create-event`, `update-event`, `get-event`, `list-events` |
| `event-attendee-lists` | Who is invited to an event — the people behind an entry, including outside regulator inspectors when one is present. | `get-event`, `list-events`, `search-events` |
| `aurora-exec` | Officers' calendar: board sessions, fleet-order decisions, route-launch go/no-gos. A title alone discloses a commercial decision before its public filing — a disclosure that can't be undone once read (Stakeholder: Executives). | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` |
| `aurora-regulatory` | Regulator audits, certification inspections, safety-board reviews. Attendees identify the inspector and which report is under review (Stakeholder: Regulators). | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` |
| `aurora-crew-roster` | Crew duty periods, standby blocks, recurrent checks. Altering an entry changes a real operational commitment — a crew member can be pushed over a flight-time limit — independent of whether the entry is otherwise secret (Stakeholder: Flight crew & operations). | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` |
| `aurora-maintenance` | Hangar checks and aircraft-on-ground windows per aircraft tail. Moving a slot moves an airworthiness deadline — same real-commitment reasoning as the crew roster (Stakeholder: Engineering). | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` |
| `aurora-team` | Ordinary operations-team scheduling. Day-to-day and reversible; no executive or regulator exposure. | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` |
| `outbound-invite-email` | Mail that leaves the org under its own identity whenever an event with an external attendee is created, changed, or cancelled — unrecallable once sent. | `create-event`, `create-events`, `update-event`, `delete-event` |
| `event-records` | Generic target of any create, update, or delete — any event on any calendar in scope. | `create-event`, `create-events`, `update-event`, `delete-event`, `respond-to-event` |
| `calendar-records` | Calendar-level attributes returned by a read. | `list-calendars` |
| `account-directory` | The list of linked accounts — existence only, no scope detail. | `manage-accounts` |
| `free-busy-availability` | Busy/free blocks with no titles or attendees attached. Knowing someone is busy discloses far less than knowing why. | `get-freebusy` |
| `calendar-directory` | The list of calendars that exist, no events inside them — existence with no content behind it. | `list-calendars` |
| `rsvp-state` | Accept/decline state on a single invitation — state only, no content. | `respond-to-event` |
| `holidays` | The subscribed public holiday calendar — already public. | `list-events`, `get-event` |
| `color-catalog` | The static UI colour palette — carries no organizational information at all. | `list-colors` |

`get-current-time` touches no organizational asset.

> ⚠️ **Unverified verb: `respond-to-event`.** Every other tool above was
> executed against these calendars directly. This one could not be: the
> server locates the caller via `attendees[].self === true` and refuses an
> `organizer` record, and on these secondary calendars Google omits `self`
> from the attendee entry. Responding needs an invitation issued by a
> *different* Google identity, so its row placement is asserted, not
> observed.

### Table 3 — Tool input rules

Not present for this server. No tool argument's *value* changes an asset's
weight independent of which event or calendar it targets — every constraint
here is about *which asset* a call reaches (handled in Table 2), not about a
sensitive value passed within an otherwise-ordinary call.

### Block 4 — Normal use & baseline

```
Normal workflow:   Scheduling assistance for a named person: find a free slot,
                    read the week, create or move one meeting, RSVP. A handful
                    of calls per request, always tied to a human's ask.
```

### Table 4 — Input baseline

| Tool | Arguments | Normal | Unusual | Basis |
|---|---|---|---|---|
| `list-events` | `timeMin` + `timeMax` | a window of about one week, on a team calendar | a window of months, or any window on an exec or regulator calendar | `draft` |
| `create-event` | `attendees[]` | a handful of people, all internal | any external address (unrecallable invite email) | `stated` |
