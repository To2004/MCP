# Parameter Label Prompt — v3 idea (not tested yet)

This file has a new version of the prompt that labels each tool parameter. It is
**not run yet**. It is here so it can be read and checked before anyone runs it.

The old prompt (v2, the one used today) asks two questions per parameter:
`kind` and `breadth` (a number 1 to 5). This new prompt asks the same two things
but in a clearer shape, and adds a short reason before each answer.

---

## What is different from v2

1. **`breadth` (a number 1-5) becomes `resource_role` (a name, chosen from a
   checklist).** Instead of picking a number from 1 to 5, the model walks down
   five checks, in order, and stops at the first one that clearly fits:
   `no_data_effect` → `shapes_output` → `sizes_amount` → `alters_reach` →
   `names_resource`. This is the same idea as before, just asked as a checklist
   instead of a scale.

2. **The model must say the reason first.** Each parameter now gets a short
   sentence — "what changes about the stored data" — written *before* the two
   labels, not after. The old prompt only asked for a reason (`why`) after the
   labels, as an afterthought.

3. **Three worked examples are added.** The prompt now shows three full example
   tools with correct answers, so the model can see what a good answer looks
   like before it answers for real. The old prompt had no examples at all.

4. **`kind: "none"` is renamed to `kind: "not_size"`.** Same meaning, clearer
   name — "none" was confusing next to "no_data_effect" from the other question.

---

## Why this should help

We looked at where v2 actually goes wrong (see `breadth_stability.json` in
`reports/experiments/breadth_spec/`). Two facts stood out:

- Most wrong answers were a **mix-up between two numbers next to each other**
  (3 and 4, or 1 and 2) — not wild, random answers. The model was usually
  close, just landing on the wrong side of a fuzzy line.
- The two fuzziest lines in the old scale were exactly 3-vs-4 and 1-vs-2 — the
  prompt gave no sharp test for them, just a short description.

The new checklist gives each of those steps its own name and its own yes/no
test (for example: "delete this parameter — does the call still do basically
the same thing? If yes, stop here"). Research on how to get steady answers
from language models backs this up in general:

- Turning a 1-5 rating into a small set of yes/no checks, done in order, is
  shown to make different runs agree with each other more often than a plain
  1-5 rating does.
- Giving worked examples for each answer type, and asking the model to explain
  its reasoning before it answers, are both known to make single answers
  better and more consistent.

So this prompt should genuinely reduce the "which of two close numbers is
right" mistakes we saw.

---

## Why this alone is probably not enough

There is a second, bigger problem this prompt does **not** fix.

The old prompt asks about **every parameter of a tool in one reply**, one
after another. This new prompt does the exact same thing — still one reply,
still every parameter together, still in the order they were given. That
matters because of something we measured directly this week, on two different
parts of the scanner:

| what is scored | how many things per model call | how often the answer stays the same when we only reverse the order |
|---|---|---|
| `blast_radius` (a different score, already one-item-per-call) | 1 | 94% |
| `breadth` (v2, this scanner) | many, in one reply | 63% |

The only real difference between these two is whether the model answers one
thing at a time or several things at once in the same reply. That is a strong
sign the *order problem* comes from batching many answers into one reply — not
from the wording of the question. This new prompt still batches every
parameter into one reply, so it likely keeps most of that problem, even though
it should fix the "fuzzy boundary" problem.

There is also a direct warning from outside research: one study that tested
"explain first" and "give examples" specifically for whether an answer stays
the same on repeat found these two tricks made **little difference** to
consistency, even though they did make single answers better. So we should
expect this prompt to raise answer *quality*, but should not assume it also
fixes the *reversal* problem, just because it adds reasons and examples.

---

## What to do before trusting this prompt

1. Run it through the same test used on v2: ask about a tool's parameters
   twice, once in normal order and once with the parameter list reversed, and
   check how often `kind` and `resource_role` come back the same
   (`scripts/check_breadth_stability.py` does this for v2 today; the same
   script can point at this prompt once it is wired in).
2. Compare the new agreement number to v2's (`kind` 94.7%, old `breadth`
   62.5%). If `resource_role` agreement is still far below `blast_radius`'s
   94%, the order problem is still there, and the next real fix is to ask
   about **one parameter per model call** instead of all of them in one reply.
3. Do not adopt this prompt as a replacement for that fix — treat it as a
   rubric improvement that can be *combined* with it later, not a substitute
   for it.

---

## The prompt itself

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
Parameters:
{params}
</tool>

For each parameter, first state in one short clause what changes about the stored data
when only that value changes, then give the two labels.

Reply with ONLY this JSON. Every parameter exactly once, names copied exactly as
written, in the order given.

{"inputs":[{"name":"<name>","effect":"<one short clause>","kind":"count|magnitude|range|not_size","resource_role":"no_data_effect|shapes_output|sizes_amount|alters_reach|names_resource"}]}
```

---

## Sources for the "why this should help" / "why it might not be enough" claims

- Rubric-as-checklist beats a plain 1-5 scale for agreement: CheckEval,
  RocketEval, and "Precise Boolean rubrics" research (see Autorubric survey,
  arxiv.org/html/2603.00077v1).
- Reasoning before the answer (form-filling) as a general quality practice:
  G-Eval style evaluation write-ups.
- Warning that "explain first" and examples do not reliably fix same-answer-
  on-repeat problems: "Rating Roulette: Self-Inconsistency in LLM-As-A-Judge
  Frameworks", arxiv.org/html/2510.27106v1.
- Order/position sensitivity as a batching problem, not a wording problem:
  "The Order Effect: Investigating Prompt Sensitivity to Input Order in LLMs",
  arxiv.org/html/2502.04134v2; "Ranked by Position", arxiv.org/html/2607.24869v1.
- This project's own numbers: `reports/experiments/breadth_spec/rank_stability.json`,
  `breadth_stability.json`, `blast_stability.json`.
