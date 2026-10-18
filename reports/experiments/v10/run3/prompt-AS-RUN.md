<!-- Copied by hand after the run, not snapshotted by the runner: the snapshot
     code landed while job 20622342 was already running. The file was unmodified
     between 12:02:31 (written) and the job window 12:03:03-12:06:44, so this is
     the text run 3 sent. sha256 of the prompt body: f3ffd34680f7a24293dceb6c471858e01118db97e8e483364e72d3d4d0bc70fe -->

# Tool Input Typing

For each input of a tool, one question: is this a value with a **size** — in
which case what counts as low, medium and high — or a value that **picks one out
of many**, in which case the dynamic layer must check it against policy at run
time. Anything else needs no answer.

Derived statically, from the tool registry alone. No risk, no severity.

## LLM prompt (derivation)

> For each input of the MCP tool below, decide which of three things it is, and
> answer briefly. Work from the input's name, its description, the schema's
> declared constraints, and how an API of this sort is called — not from the
> declared JSON type, which is usually just `string` whatever the value holds.
>
> **1. The value has a size or a place on a scale** — a count, a length, an
> amount of money, a duration, a time of day, a date, a page size, a row limit,
> a depth. Say what it measures and in what unit, then give the ranges that
> count as **low**, **medium** and **high** for this input. Use the tool's own
> documented bounds where it states them and ordinary practice where it does
> not. Write the ranges as numbers with a unit, not as words. If the value is a
> list, what has a size is the number of items in it. If leaving the input out
> removes a bound rather than applying a default, say so in `absent`.
>
> **2. The value picks one thing out of many** — an id, an account, a
> repository, a channel, a user, a country, a region. Answer this only when the
> set is **large** and a caller is entitled to part of it rather than all of it:
> say what the set is, and set `check_policy` to true so the run-time layer
> knows to look this input up in the organisation's policy. A value chosen from
> a handful of fixed options is not this — it needs no answer.
>
> **3. Anything else** — text written for a person to read, an opaque token a
> caller copies from an earlier reply, a small fixed choice. Return its name and
> nothing more. Do not invent ranges or sets for these.
>
> Describe only the inputs the tool actually declares, and every one of them. If
> it declares none, return an empty list. Never add an input you would expect an
> API of this sort to have but which is absent from the definition in front of
> you.
>
> Output ONLY valid JSON, no prose, no fences. Give each input only the keys
> that apply to it:
>
> ```json
> {"tool_name": str, "inputs": [{
>   "name": str,
>   "measures": str, "unit": str,
>   "low": str, "medium": str, "high": str, "absent": str,
>   "one_of_many": str, "check_policy": bool
> }]}
> ```
>
> Tool: `{tool_json}`

## Notes for the caller

- The tool JSON must carry the schema's declared constraints (`enum`,
  `minimum`, `maximum`, `format`, `default`); `ToolSpec.parameters()` drops
  them, so the full `input_schema` is passed instead.
- A tool that declares no inputs is never sent to the model — asking about an
  empty schema invites it to invent the inputs it expects.
- `check_policy` is the handoff to the dynamic layer: it marks the inputs whose
  legitimate values cannot be known from the tool definition and must come from
  the organisation's policy.
