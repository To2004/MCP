# Parameter classifier — split experiment, call 1 of 2: kind only

Same `kind` rubric as `window` (v7), asked ALONE — no `resource_role` or
`external_effect` in the same reply. Tests whether decoupling the two questions into
separate calls reduces cross-contamination versus asking both in one JSON per
parameter (`window`'s design).

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

<examples>
Tool: query_records
Parameters: dataset_id, filter_text, limit, sort_by, trace_id
{"inputs":[
{"name":"dataset_id","kind":"not_size"},
{"name":"filter_text","kind":"not_size"},
{"name":"limit","kind":"magnitude"},
{"name":"sort_by","kind":"not_size"},
{"name":"trace_id","kind":"not_size"}]}

Tool: create_ticket
Parameters: project_id, title, watchers, window_start, window_end, notify_watchers, layout_version
{"inputs":[
{"name":"project_id","kind":"not_size"},
{"name":"title","kind":"not_size"},
{"name":"watchers","kind":"count"},
{"name":"window_start","kind":"range"},
{"name":"window_end","kind":"range"},
{"name":"notify_watchers","kind":"not_size"},
{"name":"layout_version","kind":"not_size"}]}
</examples>

<tool>
Name: {tool}
Description: {desc}
Parameters:
{params}
</tool>

For each parameter, give kind.

Reply with ONLY this JSON. Every parameter exactly once, names copied exactly as
written, in the order given.

{"inputs":[{"name":"<name>","kind":"count|magnitude|range|not_size"}]}
```
