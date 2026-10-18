# Parameter classifier — experiment 1: forced checks, code derives the label

**Result: this lost to experiment 2 (`breadth_prompt_categories.md`) and to v3.** Mean
role agree 68.9% (v3: 85.0%, experiment 2: 87.6%), and 2 of 24 tools were dropped
outright on persistent malformed/all-N answers. Forcing five separate yes/no checks per
parameter did not fix the instability — it added five independently-noisy judgments in
place of one categorical pick, and a flip in any one of the five was enough to change
the derived label. `multi_y`, the population this was built to surface, fired once in
the whole run. The three rubric fixes here (creation-call rule, list tie-breaker,
`external_effect` split) are the same ones in experiment 2, which kept them and dropped
the forced-checks machinery — that is the version to use. Full comparison table in
`breadth_prompt_categories.md`. This file is kept for the record, not as a
recommendation.

---

Diagnostics run first, on data already collected from v3 (see the bottom of this file):
they support building this. The `alters_reach -> no_data_effect` flip is 7-to-0 in one
direction, not balanced — that is a ladder that stops reading once it finds a "yes," not
noise. Big flips (|delta| >= 3) really did double in count from v2 to v3 (4/209 to
9/209), not just look bigger because small errors got fixed. And `create-event`'s 12
flips are dominated by permission/notification flags (`sendUpdates`,
`guestsCanInviteOthers`, `anyoneCanAddSelf`, ...), not by content fields — so the
notification-conflation fix matters more for this specific tool than the creation-call
rule does, though both are kept since the creation-call gap is real elsewhere.

## Diff from v3

1. **Model no longer emits `resource_role` directly.** It emits a five-character
   verdict string, `checks` — one Y/N per check, C1..C5, in order. The label is derived
   in code as the LOWEST check that came back Y. This targets the ladder early-exit
   directly: in v3 the model could stop at "yes, this satisfies the no-data-effect
   description" and never separately consider whether it also alters reach. Now it must
   answer all five, every time.
2. **Creation-call rule.** When a call CREATES a new stored thing instead of acting on
   an existing one, nothing yet exists to "narrow" or "select" — so a content field on a
   creation call has nowhere to fall except the reach level. Said explicitly, so the
   model has language for it instead of guessing.
3. **List tie-breaker, both directions.** A list is only "names several stored things"
   when each entry IS one of those things. A list that only fills one field inside a
   single already-chosen record is not that, however long the list is. Both a positive
   and a negative example are given so the model does not overcorrect to "lists are
   never level 5."
4. **`external_effect` is now its own field**, separate from the five checks. A
   notification flag (send an email, ping a channel) does not change what is stored, so
   under the checks alone it is a clean "yes" on check 1 — but it still matters for risk,
   and folding that signal into the same field as "does this touch stored data" was
   making that one field try to answer two different questions at once.
5. **Examples are deliberately generic.** v3's worked examples leaned on tool shapes
   (`create_event`, `channels_list`) that sit close to the real servers this prompt is
   actually scored against (`create-event`, `channels_list` are real tool names in this
   project's own calendar and slack catalogs) — close enough that a worked example could
   function as an answer key instead of a teaching example. This version uses tool and
   field names that do not match anything in the scanned catalogs.

`kind` is unchanged from v3.

---

## The prompt

Filled with `.replace()`, not `.format()` — the reply schema and examples use single
braces, which `str.format` cannot pass through unescaped.

```text
You label the input parameters of one MCP tool.

Judge what the value MEANS in a real call. The declared type is a hint only. It is
often wider or narrower than the value it actually carries.

<label name="kind">
If a caller passed a BIGGER value here, what makes it bigger?

count      The value holds several things and what matters is how many.
           This includes several things packed into one string with a separator.
           e.g. ["a.txt","b.txt"] ; "id1,id2,id3"

magnitude  The value is one number, and a bigger number means more work done or more
           data returned. This includes a number written as text, with or without a
           unit suffix.
           e.g. limit=500 ; page_size ; "30d" meaning thirty days

range      The value is one end of an interval, and what matters is how wide the
           interval is between it and its partner parameter.
           e.g. start_date, whose partner is end_date ; from_line, whose partner is to_line

not_size   None of the above. The value picks one particular thing, switches a mode on
           or off, or is free text being written.
           e.g. file_id ; sort="asc" ; the body of a message

Rule: a value that identifies something is not_size even when it is a number.
One id is not bigger than another id.
</label>

<label name="checks">
Answer FIVE separate yes/no questions about this parameter. Answer every one of them.
Do not stop early. Do not skip a question because an earlier one was yes.

The test for all five: keep every other parameter the same, change only this value, and
ask what is different about the stored data afterwards.

First, work out which parameter of this tool names the stored unit the call acts on —
the record, file, table, folder, mailbox, channel, calendar, repository. Call that the
NAMING PARAMETER. Some tools have one. Some have none. You need this to answer C3 and C4.

If the call CREATES a new stored unit rather than acting on an existing one, then the
naming parameter is the one saying WHERE the new unit lands (a parent folder, a
workspace, a project, a calendar). The fields filling in the new unit's own contents are
not naming parameters — they are C4, because nothing existing is there yet for them to
narrow.

C1  Is the stored data identical whatever this value is?
    The value concerns running the call, logging it, timing it, or sending a
    notification to someone. Nothing stored changes.
    yes: a request id used only for tracing ; a retry count ; a timeout ; a flag that
    only decides who gets notified about a change someone else already made

C2  Does the same information arrive either way, only in a different order, format, or
    instalment?
    yes: an output format switch ; a sort order ; a pagination cursor or token ; a
    "pretty-print this reply" flag

C3  Does a naming parameter exist, with this value only capping, bounding or narrowing
    what comes out of the unit that parameter named?
    Delete this parameter and the call still does basically the same thing to basically
    the same data.
    yes: a row limit ; a page size ; a free-text filter that searches inside an already
    chosen container ; a flag that hides some already-chosen rows

C4  Does this value stay inside the unit the naming parameter chose, but change WHAT
    content is read or written there?
    yes: the body of a record being written ; a list of names filling one field of a
    single record ; a flag deciding whether an existing value gets overwritten ; a flag
    switching how much of one record's content is returned

C5  Does this value itself name or match the stored unit the call acts on — or several
    such units at once?
    yes: an id naming one record, file, or container ; a list of several such ids or
    paths ; a pattern matching an open-ended set of them

Tie-breakers. These beat any feeling you get from the parameter's name.

- A list is C5 only when EACH ENTRY is another stored unit the call reads or writes on
  its own. A list whose entries only fill one field inside a SINGLE unit is C4, not C5.
  C5 example: a parameter that lists several item ids, each one written or read
  separately.
  C4 example: a parameter that lists several names into ONE field of a single record
  (e.g. who should be told about it) — one record, one field, however many names.

- A parameter offering a fixed menu of categories that narrows a listing is C3 even
  when it accepts several values at once. It selects nothing new; it filters.

- Free text written into a place another parameter already chose is C4, however
  confidential that text is.

- A flag deciding whether the write really lands, or how much of it lands, is C4.
  A flag changing only speed, logging, retries, or notifications is C1.

- If a tool has no naming parameter at all and one value alone decides which stored
  things come back, that value is C5, not C3.
</label>

<label name="external_effect">
Does this value cause data to leave the system or reach a third party — an email, an
invite, a notification, a webhook, a share link, an outbound request?
Answer yes or no. This is independent of the five checks. A value can be C1 and still
be yes.
</label>

<examples>
Tool: query_records
Parameters: dataset_id, filter_text, limit, sort_by, trace_id
{"inputs":[
{"name":"dataset_id","effect":"a different dataset is read","kind":"not_size","checks":"NNNNY","external_effect":"no"},
{"name":"filter_text","effect":"same dataset, narrows which rows come back","kind":"not_size","checks":"NNYNN","external_effect":"no"},
{"name":"limit","effect":"same rows, fewer or more of them","kind":"magnitude","checks":"NNYNN","external_effect":"no"},
{"name":"sort_by","effect":"same rows, different order","kind":"not_size","checks":"NYNNN","external_effect":"no"},
{"name":"trace_id","effect":"stored data untouched","kind":"not_size","checks":"YNNNN","external_effect":"no"}]}

Tool: create_ticket
Parameters: project_id, title, watchers, window_start, window_end, notify_watchers, layout_version
Naming parameter: project_id — it says where the new ticket lands.
{"inputs":[
{"name":"project_id","effect":"the ticket is created in a different project","kind":"not_size","checks":"NNNNY","external_effect":"no"},
{"name":"title","effect":"same project, different content in the new ticket","kind":"not_size","checks":"NNNYN","external_effect":"no"},
{"name":"watchers","effect":"one ticket, more names in one field of it","kind":"count","checks":"NNNYN","external_effect":"yes"},
{"name":"window_start","effect":"one ticket, widens or narrows its window with window_end","kind":"range","checks":"NNNYN","external_effect":"no"},
{"name":"window_end","effect":"one ticket, widens or narrows its window with window_start","kind":"range","checks":"NNNYN","external_effect":"no"},
{"name":"notify_watchers","effect":"ticket stored identically, decides who gets emailed about it","kind":"not_size","checks":"YNNNN","external_effect":"yes"},
{"name":"layout_version","effect":"decides which display template is attached to the new ticket","kind":"not_size","checks":"NNNYN","external_effect":"no"}]}

Tool: list_containers
Parameters: space_id, kinds, exclude_hidden, page_size, cursor
{"inputs":[
{"name":"space_id","effect":"a different workspace is listed","kind":"not_size","checks":"NNNNY","external_effect":"no"},
{"name":"kinds","effect":"same workspace, narrows which container kinds are listed","kind":"count","checks":"NNYNN","external_effect":"no"},
{"name":"exclude_hidden","effect":"same workspace, narrows the listing","kind":"not_size","checks":"NNYNN","external_effect":"no"},
{"name":"page_size","effect":"same containers, fewer or more of them","kind":"magnitude","checks":"NNYNN","external_effect":"no"},
{"name":"cursor","effect":"same containers, a later instalment","kind":"not_size","checks":"NYNNN","external_effect":"no"}]}

Tool: save_items
Parameters: keys, content, overwrite, dry_run
{"inputs":[
{"name":"keys","effect":"each entry is another item written","kind":"count","checks":"NNNNY","external_effect":"no"},
{"name":"content","effect":"same items, different bytes written into them","kind":"not_size","checks":"NNNYN","external_effect":"no"},
{"name":"overwrite","effect":"same items, decides whether existing bytes are destroyed","kind":"not_size","checks":"NNNYN","external_effect":"no"},
{"name":"dry_run","effect":"same items, decides whether the write lands at all","kind":"not_size","checks":"NNNYN","external_effect":"no"}]}
</examples>

<tool>
Name: {tool}
Description: {desc}
Parameters:
{params}
</tool>

For each parameter: state in one short clause what changes about the stored data when
only that value changes, then give kind, then the five checks as a five-character string
of Y and N in order C1 C2 C3 C4 C5, then external_effect.

Answer all five checks for every parameter. More than one may be Y.

Reply with ONLY this JSON. Every parameter exactly once, names copied exactly as
written, in the order given.

{"inputs":[{"name":"<name>","effect":"<one short clause>","kind":"count|magnitude|range|not_size","checks":"<5 chars of Y/N>","external_effect":"yes|no"}]}
```

**Correction, after the first run:** this was designed to prefill the assistant turn
with `{"inputs": [` by appending the prefix to the prompt and reconstructing the JSON
from `prefix + response`. That does not work against Ollama's `/api/generate` — without
`raw: true`, Ollama wraps the prompt in the model's chat template and generates a FRESH
reply regardless of what trails the prompt text, so the appended prefix just became
extra user-turn text, and the model's real reply (a complete, self-contained JSON object
of its own) came back doubled up with the manually-added prefix when concatenated. Every
one of the first 24 tools failed to parse — 0/24, not a stability finding, a bug. Fixed
by dropping the prefill entirely and using the same plain `query_ollama` call v2/v3/v4
already use successfully; there is no prefill in the version actually run.

---

## Derivation and validation (runs in the test script, not the model)

```python
CHECK_ORDER = ["no_data_effect", "shapes_output", "sizes_amount",
               "alters_reach", "names_resource"]
ROLE_SCORE = {"names_resource": 5, "alters_reach": 4, "sizes_amount": 3,
              "shapes_output": 2, "no_data_effect": 1}

def derive(item: dict) -> dict | None:
    checks = item.get("checks", "")
    if not (len(checks) == 5 and set(checks) <= {"Y", "N"}):
        return None
    ys = [i for i, c in enumerate(checks) if c == "Y"]
    if not ys:
        return None                              # all-N: retry once, then drop the tool
    item["resource_role"] = CHECK_ORDER[ys[0]]    # lowest Y wins
    item["multi_y"] = len(ys) > 1                 # logged, not rejected
    return item
```

A parameter answering Y to both C1 and C4 is exactly the population that was silently
collapsing under v3's single-shot label — `multi_y` makes it visible instead of hidden.
All-N gets one retry, then the whole tool is dropped from the comparison rather than
defaulted to a level — a silent default here would just reintroduce v3's fall-through
in a new place.

---

## Diagnostics run before building this (on `breadth_v3_stability.json`, no model calls)

```
alters_reach -> no_data_effect:  7
no_data_effect -> alters_reach:  0
```
One-directional, 7 to 0 — a ladder that stops early, not context noise. Point 1 above is
aimed straight at this.

```
big flips (|delta| >= 3), over ALL 209 inputs, not just disagreements:
v2: 4/209 (1.9%)
v3: 9/209 (4.3%)
```
The count itself more than doubled — not just a bigger average among a smaller set of
errors. The "v3's mistakes got worse, not just rarer" read from last round holds up.

```
create-event's 12 flipped parameters (v3):
account, allowDuplicates, anyoneCanAddSelf, calendarsToCheck, colorId, eventId,
eventType, guestsCanInviteOthers, guestsCanModify, guestsCanSeeOtherGuests,
sendUpdates, timeZone
```
None of the content fields (`summary`, `description`, `location`) flipped at all. The
list is dominated by permission/notification-adjacent flags
(`guestsCan*`, `anyoneCanAddSelf`, `sendUpdates`) and identifiers/bookkeeping fields
(`account`, `eventId`, `timeZone`, `colorId`). That points at point 4
(`external_effect` split) mattering more for this specific tool than point 2 (the
creation-call rule) — point 2 is kept anyway because the gap it targets is real on
other tools, just not the dominant one here.

---

## How this is tested

Same forward/reversed test as v2/v3/v4: ask about a tool's parameters in schema order,
then again with the schema reversed, and compare. `kind_agree` is unchanged. `resource_role`
here is the DERIVED label, not something the model wrote directly — the comparison is on
the derived value.

`scripts/check_breadth_checks_stability.py` runs this.
