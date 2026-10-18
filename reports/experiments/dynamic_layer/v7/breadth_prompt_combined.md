# Parameter classifier — experiment D: all three v7 rules combined

Base: exp2 (87.6% role agree), plus all three rules from context/fields/window in one
prompt. Each rule alone beat exp2:

```
              exp2    context  fields  window
role agree    87.6%   90.0%    89.3%   91.7%   (window: median 95.9%, best single result)
```

Each rule's spillover onto the OTHER two rules' target tools was partial, not full
(see `v7/README.md` cross-table) — worth checking whether combining them stacks the
gains or the added rule text starts colliding / adding noise of its own.

---

## The prompt

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

<label name="resource_role">
How much does this parameter decide WHICH STORED DATA the call touches?

First work out which parameter of this tool NAMES the stored unit the call acts on —
the record, file, table, folder, mailbox, channel, calendar, repository the call is
about. Call that the naming parameter. Some tools have one; some have none.

If the call CREATES a new stored unit rather than acting on an existing one, the naming
parameter is the one saying WHERE the new unit lands (which folder, which workspace,
which project) — not the fields filling in the new unit's own contents. Those content
fields are level 4 below, even on a creation call, because nothing existing is there yet
for them to narrow.

Read all five levels before you answer, then pick the ONE that fits best.

5  names_resource
   This value itself names or matches the stored unit the call acts on, or several such
   units at once. Change it and the call points somewhere else entirely.

4  alters_reach
   The value stays inside the unit the naming parameter chose (or, on a creation call,
   inside the new unit being created), but changes WHAT content is read or written
   there.

3  sizes_amount
   A naming parameter exists, and this value only caps, bounds, or narrows what comes
   out of the unit it named. Delete this parameter and the call still does basically the
   same thing to basically the same data.

2  shapes_output
   The same information arrives either way — this value only changes its order, format,
   or which instalment of it arrives.

1  no_data_effect
   The stored data is identical whatever this value is. It concerns running the call,
   logging it, timing it, or sending a notification to someone — nothing stored changes.

Tie-breakers. These beat any feeling you get from the parameter's name.

- A list is level 5 only when EACH ENTRY is another stored unit the call reads or writes
  on its own. A list whose entries only fill one field inside a SINGLE unit is level 4,
  not 5.
  Level 5 example: a parameter listing several item ids, each one written or read
  separately.
  Level 4 example: a parameter listing several names into ONE field of a single record
  (e.g. who should be told about it) — one record, one field, however many names.

- A parameter offering a fixed menu of categories that narrows a listing is level 3 even
  when it accepts several values at once. It selects nothing new; it filters.

- Free text written into a place another parameter already chose is level 4, however
  confidential that text is.

- A flag deciding whether the write really lands, or how much of it lands, is level 4.
  A flag changing only speed, logging, retries, or notifications is level 1.

- If a tool has no naming parameter at all and one value alone decides which stored
  things come back, that value is level 5, not level 3.

- If two levels seem to fit, re-read the naming-parameter test above before choosing —
  do not drop to the lower level without checking it against the test.
- A tool can have MORE THAN ONE parameter that helps select the stored unit —
  for example, an account or workspace context alongside a specific record,
  channel, or calendar within it. Do not force a single "the" naming parameter
  when a tool genuinely has both: the broader context parameter (which account,
  which workspace) is level 5 in its own right, same as the specific-item
  parameter within it. Changing either one points the call at a different stored
  universe, even though only one of them is the MOST specific.
- A parameter that selects WHICH FIELDS of an already-chosen record come back
  (a projection: fields=, select=, include=) is level 2, not level 3 or 4 — it
  trims which attributes of the SAME content are shown; the underlying record
  read or written does not change. Raise it to level 3 only if it can exclude an
  entire attached sub-resource that would otherwise be fetched separately (e.g.
  skip a large embedded attachment). Default to level 2 for a plain field list.
- A parameter that is one end of a time or numeric WINDOW (kind: range) bounding
  which records fall inside an already-chosen container is level 3, not level 4 —
  it narrows which of the container's contents are returned, the same as a limit
  or a filter. This holds whether the window is on a listing call or bounds one
  field inside a single record: the test is still whether it narrows an existing
  selection (level 3) or changes WHAT is read or written there (level 4), and a
  date or number range being the shape of the value does not by itself move it.
</label>

<label name="external_effect">
Does this value cause data to leave the system or reach a third party — an email, an
invite, a notification, a webhook, a share link, an outbound request?
Answer yes or no. This is independent of resource_role. A value can be level 1 and
still be yes.
</label>

<examples>
Tool: query_records
Parameters: dataset_id, filter_text, limit, sort_by, trace_id
{"inputs":[
{"name":"dataset_id","effect":"a different dataset is read","kind":"not_size","resource_role":"names_resource","external_effect":"no"},
{"name":"filter_text","effect":"same dataset, narrows which rows come back","kind":"not_size","resource_role":"sizes_amount","external_effect":"no"},
{"name":"limit","effect":"same rows, fewer or more of them","kind":"magnitude","resource_role":"sizes_amount","external_effect":"no"},
{"name":"sort_by","effect":"same rows, different order","kind":"not_size","resource_role":"shapes_output","external_effect":"no"},
{"name":"trace_id","effect":"stored data untouched","kind":"not_size","resource_role":"no_data_effect","external_effect":"no"}]}

Tool: create_ticket
Parameters: project_id, title, watchers, window_start, window_end, notify_watchers, layout_version
Naming parameter: project_id — it says where the new ticket lands.
{"inputs":[
{"name":"project_id","effect":"the ticket is created in a different project","kind":"not_size","resource_role":"names_resource","external_effect":"no"},
{"name":"title","effect":"same project, different content in the new ticket","kind":"not_size","resource_role":"alters_reach","external_effect":"no"},
{"name":"watchers","effect":"one ticket, more names in one field of it","kind":"count","resource_role":"alters_reach","external_effect":"yes"},
{"name":"window_start","effect":"one ticket, widens or narrows its window with window_end","kind":"range","resource_role":"alters_reach","external_effect":"no"},
{"name":"window_end","effect":"one ticket, widens or narrows its window with window_start","kind":"range","resource_role":"alters_reach","external_effect":"no"},
{"name":"notify_watchers","effect":"ticket stored identically, decides who gets emailed about it","kind":"not_size","resource_role":"no_data_effect","external_effect":"yes"},
{"name":"layout_version","effect":"decides which display template is attached to the new ticket","kind":"not_size","resource_role":"alters_reach","external_effect":"no"}]}

Tool: list_containers
Parameters: space_id, kinds, exclude_hidden, page_size, cursor
{"inputs":[
{"name":"space_id","effect":"a different workspace is listed","kind":"not_size","resource_role":"names_resource","external_effect":"no"},
{"name":"kinds","effect":"same workspace, narrows which container kinds are listed","kind":"count","resource_role":"sizes_amount","external_effect":"no"},
{"name":"exclude_hidden","effect":"same workspace, narrows the listing","kind":"not_size","resource_role":"sizes_amount","external_effect":"no"},
{"name":"page_size","effect":"same containers, fewer or more of them","kind":"magnitude","resource_role":"sizes_amount","external_effect":"no"},
{"name":"cursor","effect":"same containers, a later instalment","kind":"not_size","resource_role":"shapes_output","external_effect":"no"}]}

Tool: save_items
Parameters: keys, content, overwrite, dry_run
{"inputs":[
{"name":"keys","effect":"each entry is another item written","kind":"count","resource_role":"names_resource","external_effect":"no"},
{"name":"content","effect":"same items, different bytes written into them","kind":"not_size","resource_role":"alters_reach","external_effect":"no"},
{"name":"overwrite","effect":"same items, decides whether existing bytes are destroyed","kind":"not_size","resource_role":"alters_reach","external_effect":"no"},
{"name":"dry_run","effect":"same items, decides whether the write lands at all","kind":"not_size","resource_role":"alters_reach","external_effect":"no"}]}
</examples>

<tool>
Name: {tool}
Description: {desc}
Parameters:
{params}
</tool>

For each parameter, first state in one short clause what changes about the stored data
when only that value changes, then give kind, then resource_role, then external_effect.

Reply with ONLY this JSON. Every parameter exactly once, names copied exactly as
written, in the order given.

{"inputs":[{"name":"<name>","effect":"<one short clause>","kind":"count|magnitude|range|not_size","resource_role":"no_data_effect|shapes_output|sizes_amount|alters_reach|names_resource","external_effect":"yes|no"}]}
```
