# Parameter Label Prompt — v4 idea (chunked calls, same labels as v3)

v3 (`reports/experiments/dynamic_layer/v4/breadth_prompt.md`) was tested this week.
It worked, and worked better than expected:

| | v2 (old) | v3 (tested) |
|---|---|---|
| `kind` agree | 94.7% | 97.3% |
| `breadth`/`resource_role` agree | 62.5% | 85.0% |

**Result, tested (`scripts/check_breadth_v4_stability.py`,
`reports/experiments/breadth_spec/breadth_v4_stability.json`): chunking did not help.**
It is a wash at best, and it broke one thing outright:

| | v3 | v4 (chunked) |
|---|---|---|
| `kind` agree | 97.3% | 96.8% |
| `resource_role` agree | 85.0% | 85.4% (looks better, but see below) |
| mean role agree, same 23 tools (dropping the one v4 lost) | 86.1% | 85.4% |
| `create-event` (31 params, v3's weakest tool) | 61% | **no data — every retry on one of its 6 chunks came back malformed, so the whole tool was dropped** |

Once the comparison is put on the same footing (v4 lost `create-event` entirely, so
comparing v3's mean *with* it against v4's mean *without* it flatters v4), chunking is
not an improvement — it is very slightly worse. Some tools got better
(`conversations_unreads` 50%→100%), some got clearly worse (`update-event` 93%→68%,
`create_pull_request` 88%→75%, `usergroups_create` 75%→50%), and the one tool this was
most meant to fix produced no usable answer at all, because splitting it into 6 chunks
gave 12 separate model calls (2 directions × 6 chunks) instead of 2, and one chunk
failing invalidates the whole tool.

**Why, concretely — a real example from `update-event`:** `start` and `end` are a
declared range pair (the rubric's own `range` `kind` needs a value's "partner
parameter" to recognize it as one). In the forward run, both landed in the same chunk
and were correctly read as one range. In the reversed run, they landed in **different**
chunks — `end`'s chunk still had it right (`kind: range`), but `start`'s chunk, on its
own, read it as `not_size`. Cutting a tool into chunks introduced a NEW way for
presentation order to change the answer: which chunk a parameter's partner ends up in.
The "other parameters, for context only" line gives names, not enough to keep a
declared pair legible when they are split apart.

**Conclusion: v3 stays the adopted candidate.** Chunking, as designed here, trades one
order-sensitivity channel (batch size / context bleeding) for another (which chunk a
parameter's partner lands in) at roughly double the call cost, and adds a new failure
mode (partial-tool data loss) on exactly the tools it most needed to help. If chunking
is revisited, chunk boundaries would need to keep declared partner pairs (schema
properties that reference each other, or share an obvious name prefix/suffix) in the
same chunk, rather than cutting by raw schema position — that was not done here and is
the concrete next thing to try, not a re-run of this version.

---

v3's own numbers still pointed at one thing left to fix: the biggest tools were still
the weakest (`create-event`, 31 parameters, only 61% agree), and when v3 *did* flip an
answer, the flip got bigger, not smaller (old average jump 1.2 steps, v3's jump 1.85
steps). Small tools were mostly fine; big tools were not. That is the signature of a
**batching** problem, not a wording problem — this file does not change any label or
any rubric text from v3. It changes how many parameters get asked about **in one model
reply**.

---

## The idea: keep the context, shrink the batch

Research on "batch prompting" (asking about several items in one reply to save calls)
finds the same shape we found: small batches are fine, but past a certain size, answers
start blurring into each other — one paper calls this "context bleeding," where a
strong keyword in one item leaks into the model's read of the item next to it. Several
papers put the safe line somewhere around 8-16 items for simple tasks, and lower (under
8) for tasks that need real reasoning per item — which labelling a parameter is closer
to than, say, sorting a sentence into "positive" or "negative."

So the plan is: **do not ask about more than a handful of parameters in one reply.**
Split a tool's parameter list into small groups and label each group in its own model
call.

There is one thing this cannot simply drop, though. Read the v3 rubric closely and one
line matters a lot:

> A filter or search string is `sizes_amount` when ANOTHER parameter already names the
> unit it runs inside. It is `names_resource` when no other parameter names the unit.

To answer that correctly, the model has to know **whether a sibling parameter exists**
— even if it is not being asked to label that sibling right now. Cut a tool's
parameters into groups and hand each group to the model with no idea the other groups
exist, and a `query` parameter that should be `sizes_amount` (because `collection_id`
elsewhere already names the resource) could wrongly become `names_resource` — the model
would have no way to know `collection_id` is even on this tool.

So this version keeps the group small for **labelling**, but still tells the model the
**full list of every other parameter's name** on the tool, marked clearly as
context only — not something to answer for in this call. That keeps the one piece of
cross-parameter knowledge the rubric actually needs, while removing the rest of what
made big tools unstable: many full verdicts, with full reasoning text, piling up in one
reply.

---

## What actually changed

1. **Same two labels, same rubric, same five-step checklist, same examples as v3.**
   Nothing about what "sizes_amount" or "alters_reach" means has changed.
2. **One new line added to the prompt**, right before the list of parameters to label:
   > Other parameters on this tool, for context only — do not answer for these, they
   > are scored in a separate call: {other_params}
3. **A tool's parameters are split into groups of at most 6** (chosen from the batch-
   prompting research's "stays safe under ~8" line, with some headroom) before calling
   the model. Each group gets its own reply. A tool with 6 or fewer parameters is
   unaffected — it was already effectively "one small batch."
4. Group boundaries are cut from the same order the parameters were given in — so the
   forward/reversed stability test still applies cleanly: reverse the whole list first,
   then cut it into groups of 6, exactly as a real scan would.

---

## What this should and should not fix

**Should fix:** the part of the instability that comes from many parameters being
labelled in the same reply — the mechanism the batch-prompting research describes, and
the one our own numbers pointed at (big tools worst, bigger jumps when wrong).

**Should not fix:** anything that was already a genuine judgment call about one
parameter's meaning, independent of batching. If a single parameter is just ambiguous
on its own merits, cutting the batch size does not resolve that — a real test of this
is whether `resource_role` agreement on the *small* tools (which were already
effectively unbatched) changes at all. If it does not move much, that confirms batching
was the mechanism; if the small tools also move, something else was going on too.

---

## How this is tested

Same forward/reversed test as v2 and v3: ask about a tool's parameters in normal order,
then ask again with the whole schema reversed, and check how often `kind` and
`resource_role` come back the same. The only difference from the v3 test is that "ask
about a tool" is now several grouped calls instead of one, on both sides of the test.

`scripts/check_breadth_v4_stability.py` runs this.

---

## The prompt template

Same as v3, with the one line added (`{other_params}`) and the closing instruction
narrowed to "every parameter listed above" instead of implying the tool's full input
set:

```text
You label the input parameters of one MCP tool. Give each parameter two labels.

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

Answer this on its own. Ignore the kind label. Ignore how secret or valuable the data
feels — that is a separate question and it is not this one.

The test: keep every other parameter the same, change only this value, and ask what is
different about the stored data afterwards.

Work through these five checks IN ORDER. Stop at the first one that clearly fits. Only
move to the next check when the current one clearly does not apply.

1. no_data_effect
   The stored data is exactly the same whatever this value is. The value concerns
   running the call, logging it, or timing it.
   e.g. request_id ; timeout ; retries ; a label used only for tracing

2. shapes_output
   The same information is read or written either way. This value only changes the
   order, the format, or which instalment of it arrives.
   e.g. format="json" ; sort="desc" ; a paging cursor ; include_metadata

3. sizes_amount
   Another parameter already names the stored unit, and this value only caps, bounds
   or narrows what comes out of it. Delete the parameter and the call still does
   basically the same thing to basically the same data.
   e.g. limit ; offset ; max_results ; a filter or search string that runs inside a
   unit another parameter already named

4. alters_reach
   It stays inside the unit another parameter named, but this value changes WHAT
   content is read or written there.
   e.g. the text being written into a chosen file ; fields="*" ; recursive=true ;
   overwrite=true

5. names_resource
   Nothing above fits, so this value itself names or matches the stored unit: a
   record, file, table, folder, mailbox, repository, account, endpoint. Change it and
   the call points somewhere else entirely. Also use this when one value picks SEVERAL
   such units at once — a list of them, or a pattern matching an open set of them.

Tie-breakers. These beat any feeling you get from the parameter's name:

- A list or a pattern that picks stored things is names_resource even if it holds one
  entry. What matters is that each extra entry would be another stored thing.
- A filter or search string is sizes_amount when ANOTHER parameter already names the
  unit it runs inside. It is names_resource when no other parameter names the unit and
  this value alone decides which stored things come back.
- Free text written into a place another parameter already chose is alters_reach,
  however confidential that text is.
- A flag deciding whether the write really lands, or how much of it lands, is
  alters_reach. e.g. dry_run, force, confirm, cascade. A flag that only changes speed,
  logging or retries is no_data_effect.
</label>

<examples>
Tool: search_documents
Parameters: collection_id, query, limit, sort, trace_id
{"inputs":[
{"name":"collection_id","effect":"the call reads a different collection","kind":"not_size","resource_role":"names_resource"},
{"name":"query","effect":"same collection, narrows which rows come back","kind":"not_size","resource_role":"sizes_amount"},
{"name":"limit","effect":"same rows, fewer or more of them","kind":"magnitude","resource_role":"sizes_amount"},
{"name":"sort","effect":"same rows, different order","kind":"not_size","resource_role":"shapes_output"},
{"name":"trace_id","effect":"stored data untouched","kind":"not_size","resource_role":"no_data_effect"}]}

Tool: export_logs
Parameters: service, from_time, to_time, max_rows, compress
{"inputs":[
{"name":"service","effect":"a different log store is read","kind":"not_size","resource_role":"names_resource"},
{"name":"from_time","effect":"same store, widens or narrows the window with to_time","kind":"range","resource_role":"sizes_amount"},
{"name":"to_time","effect":"same store, widens or narrows the window with from_time","kind":"range","resource_role":"sizes_amount"},
{"name":"max_rows","effect":"same rows, capped count","kind":"magnitude","resource_role":"sizes_amount"},
{"name":"compress","effect":"same rows, different encoding","kind":"not_size","resource_role":"shapes_output"}]}

Tool: write_files
Parameters: paths, content, overwrite, dry_run
{"inputs":[
{"name":"paths","effect":"each entry is another file written","kind":"count","resource_role":"names_resource"},
{"name":"content","effect":"same files, different bytes written into them","kind":"not_size","resource_role":"alters_reach"},
{"name":"overwrite","effect":"same files, decides whether existing bytes are destroyed","kind":"not_size","resource_role":"alters_reach"},
{"name":"dry_run","effect":"same files, decides whether the write lands at all","kind":"not_size","resource_role":"alters_reach"}]}
</examples>

<tool>
Name: {tool}
Description: {desc}
Other parameters on this tool, for context only — do not answer for these, they are
scored in a separate call: {other_params}
Parameters to label in THIS call:
{params}
</tool>

For each parameter listed above under "Parameters to label in THIS call", first state
in one short clause what changes about the stored data when only that value changes,
then give the two labels. Do not answer for any parameter listed only under "Other
parameters."

Reply with ONLY this JSON. Every parameter listed above exactly once, names copied
exactly as written, in the order given.

{"inputs":[{"name":"<name>","effect":"<one short clause>","kind":"count|magnitude|range|not_size","resource_role":"no_data_effect|shapes_output|sizes_amount|alters_reach|names_resource"}]}
```

---

## Sources

- Batch prompting degrades past a size threshold ("context bleeding" between items in
  one reply): arxiv.org/pdf/2605.28268, arxiv.org/html/2607.20528,
  ar5iv.labs.arxiv.org/html/2301.08721.
- Permutation self-consistency (shuffle + aggregate) as the alternative published fix
  for order bias, not used here but the reason chunking was chosen as the cheaper
  first thing to try: "Found in the Middle," aclanthology.org/2024.naacl-long.129/.
- This project's own numbers: `reports/experiments/breadth_spec/breadth_v3_stability.json`.
