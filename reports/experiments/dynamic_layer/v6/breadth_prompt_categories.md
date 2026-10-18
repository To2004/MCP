# Parameter classifier — experiment 2: explained levels, one direct pick

Same three substantive fixes as experiment 1 (creation-call rule, sharpened list
tie-breaker, `external_effect` split out), and the same de-fitted examples — but without
forcing five separate yes/no answers per parameter. Here the five levels are explained
as plain descriptions (what v3 already did), the model reads all five before answering,
and it picks ONE label directly. No derivation step; the model's own answer is the
label.

This is the control for experiment 1's actual new mechanism. Both experiments carry the
same rubric fixes; only experiment 1 also forces the model to answer every check instead
of stopping at the first one that fits. If experiment 1 clearly beats this one,
forcing-all-checks was the part doing the work. If they land close together, the
rubric fixes (creation-call rule, list tie-breaker, external_effect split) were doing
the work and the forced-checks machinery was not needed.

**Result: this one won outright, and by a clear margin.**

```
                  v2 (old)   v3        exp 1 (checks)   exp 2 (this file)
kind agree        94.7%      97.3%     94.2%            95.4%
role agree        62.5%      85.0%     68.9%            87.6%   (median 88.2%)
identical tools    3/24       7/24     6/22 (2 dropped)  11/24
```

Experiment 1 (forced five-check verdict, label derived in code) was WORSE than v3, not
better, and dropped 2 of 24 tools outright (persistent malformed/all-N checks strings
after retry). `multi_y` — the thing it was built to surface, a parameter the model
marks "yes" on more than one check — fired exactly ONCE across every tool tested. The
"ladder early-exit" theory (the model stops at the first satisfied check and never
weighs C4) does not hold up: the model was not conflating checks, it was answering five
separate, independently-noisy binary questions instead of one categorical pick, and a
flip in any single one of those five is enough to change the derived label. Forcing the
checks did not reduce the model's uncertainty, it multiplied the number of places that
uncertainty could enter.

Experiment 2 — same three rubric fixes, same de-fitted examples, but the model still
picks ONE label directly, same as v3 — beat v3 on the SAME 24 tools, with no dropped
data:

```
channels_list             0.67 -> 1.00   (+0.33)
conversations_unreads     0.50 -> 1.00   (+0.50)
create-event               0.61 -> 0.87   (+0.26)   <- v3's weakest tool, biggest tool
create_pull_request        0.88 -> 1.00   (+0.12)
merge_pull_request         0.83 -> 1.00   (+0.17)
```
against a handful of small-tool regressions (`get-freebusy` 1.00->0.57, `get-event`
1.00->0.75, `list-events` 1.00->0.75 — all tools with 3-4 parameters, where one flipped
answer swings the percentage a lot). Net: mean role agree rose from 85.0% to 87.6%
(median 85.7% -> 88.2%), and the fix landed exactly where it was needed most —
`create-event`, the tool this whole investigation kept coming back to.

**Conclusion: adopt this prompt (experiment 2), not experiment 1.** The rubric content
(what "creates a new thing" means, the list tie-breaker's positive/negative pair,
splitting `external_effect` out) was the fix. Forcing five yes/no answers and deriving
the label in code was not just unnecessary, it actively hurt. This is now the
best-performing version across the whole investigation (v2 62.5% -> v3 85.0% ->
this 87.6%), on the full tool set, with nothing dropped.

`kind` is unchanged from v3.

---

## The prompt

Filled with `.replace()`, not `.format()`.

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

**Correction, after the first run:** this was meant to prefill the assistant turn the
same way experiment 1 was, and hit the same bug — see the correction note in
`breadth_prompt_checks.md`. Both experiments run with the plain, non-prefilled
`query_ollama` call, so the comparison between them still isolates the forced-checks
mechanism cleanly; neither one has a prefill effect to control for.

---

## How this is tested

Same forward/reversed test as the others. `resource_role` is read directly from the
model's own answer here — no derivation step, unlike experiment 1.

`scripts/check_breadth_categories_stability.py` runs this.
