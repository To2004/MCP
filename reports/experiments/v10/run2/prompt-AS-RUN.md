# Tool Input Typing

Before anything can be said about a call, a monitor has to know what each of a
tool's inputs *is*: what a value picks out, and how one value can differ from
another. This document derives that **statically**, from the
tool registry alone, so the answer exists before the first call is observed.

It is written to be used **two ways**: as a human spec, and verbatim as the
**prompt** the local LLM reads to type one tool's inputs.

This is typing only — no risk, no severity, no bands. Scoring lives in
[parameter-scoring.md](parameter-scoring.md) and consumes this.

## Method

The prompt deliberately does **not** hand the model a list of parameter types to
pick from. A fixed taxonomy would be a taxonomy of the servers we happened to
look at, and choosing from a menu is a much easier task than the one we want
performed — the model would be recognising our categories rather than reading
the tool.

Instead it asks for a small set of **structural facts** that can be stated about
any parameter of any API, and lets the type fall out of them. The model supplies
its own short label for what it found; the facts, not the label, are the contract
downstream code relies on.

Two of those facts carry most of the weight:

- **Population.** The inputs worth describing are the ones that pick one thing
  out of many — an account, a repository, a channel, a country. What matters is
  the size of that set, how much of it a given caller is entitled to reach, and
  which members would be out of the ordinary. A parameter whose legal values are
  three fixed options carries none of that, so the prompt records it as a fixed
  choice and moves on rather than listing the options.
- **Edges.** For anything with a size or an order, the useful output is not the
  range but the specific values at which the meaning changes — including what
  happens when the parameter is left out entirely.

## LLM prompt (derivation)

> You are typing the inputs of one MCP tool, so that a monitor knows before any
> call is seen what each input is and how its value can vary. You are not judging
> risk and not assigning severity.
>
> The declared schema type is often uninformative: most parameters are declared
> as plain strings whatever they hold, and a parameter declared as a number is
> not necessarily one whose size means anything. Decide what the value actually
> is, not what the schema calls it. Work from the name, the description, the
> schema's declared constraints, and how an API like this is called.
>
> Describe only the parameters the tool actually declares. If it declares none,
> return an empty list. Never supply a parameter you expect an API of this sort
> to have but which is not in the definition in front of you — a tool with no
> declared inputs is a fact about the tool, not a gap for you to fill. If the
> tool carries a `type_these` list, describe exactly those parameters: the rest
> are shown only so you can see the call they belong to.
>
> For every parameter the tool declares, in the order declared, return an object
> with `name`, a short lowercase `kind` label you choose yourself for what this
> input is, and **only those of the following that apply**. Name the input, not
> the answer you gave: a `kind` must never be the name of one of the fields
> below. Two parameters of the same shape should get the same label. — omit a field rather
> than filling it with null or an empty list:
>
> ```
> population   when the value picks one thing out of many rather than being
>              content of the call. Say what the members are, roughly how many
>              exist, whether a caller reaches all of them or only the ones it is
>              entitled to, whether the set can be listed at run time and by what
>              means, and which members would stand out as unusual for the
>              organisation running this server. A large population is the point:
>              if the legal values are a handful of fixed options, say
>              "fixed_choice" and nothing more — a small closed set needs no
>              description.
> limits       {"min":…, "max":…} when the value has a natural smallest and
>              largest — an operating window, a documented ceiling, a sensible
>              duration. Give the unit. Only values with an order have limits: a
>              value chosen from a set of named options has no smallest or
>              largest, whatever the options are.
> measures     what is counted or measured, when the value itself is a quantity:
>              a count, a length, an amount, a duration. Give "unit" with it. A
>              date or timestamp marks a position in time and measures nothing —
>              leave it out. When the value is a list, what is measured is the
>              number of items in it.
> edges        [{"at":…, "means":…}] — the values at which this parameter's
>              meaning changes: a default, a ceiling, the point where one item
>              becomes many, the point where a request stops covering a part and
>              starts covering everything. Use "at": "absent" for what leaving the
>              parameter out does, and say so explicitly when omitting it removes
>              a limit instead of applying a default.
> read_with    parameters this one is meaningless without: the other half of a
>              composite name, the other end of an interval.
> stability    "constant", "per-call" or "fresh" — how much the value moves across
>              calls by the same caller. This is what tells a monitor whether an
>              unfamiliar value is worth noticing.
> prose        true when the value is text composed for a person to read. Then
>              give no population, limits, measures or edges: prose has no
>              structure worth recording, and inventing limits for it is worse
>              than saying nothing. An expression the service interprets in order
>              to select or filter data — a search query, a database statement, a
>              filter — is not prose. It has a reach: record in "edges" what
>              bounds that reach and what an absent bound means.
> evidence     "schema", "name", "description" or "domain" — the strongest thing
>              your answer rests on. Do not claim "schema" for anything the schema
>              does not state.
> note         one short line, only where something above needs explaining.
> ```
>
> Return every parameter, including those whose only honest answer is a kind and
> a stability. A parameter with nothing to record is a real result, not an
> omission.
>
> Output ONLY valid JSON, no prose, no fences:
>
> ```json
> {"tool_name": str, "parameters": [{"name": str, "kind": str, "population": {
>   "of": str, "size": str, "caller_reaches": str, "listable_via": str,
>   "unusual": str} | "fixed_choice", "limits": {"min": …, "max": …, "unit": str},
>   "measures": str, "unit": str, "edges": [{"at": …, "means": str}],
>   "read_with": [str], "stability": "constant|per-call|fresh", "prose": bool,
>   "evidence": "schema|name|description|domain", "note": str}]}
> ```
>
> Tool: `{tool_json}`

## Notes for the caller

- `kind` is open vocabulary by design. Treat it as a label to cluster after the
  fact, not a key to match on — the structural fields are the contract. If the
  labels need to be normalised into a fixed set, do it as a separate pass over
  the derived output, where it can be inspected and revised without changing
  what the model was asked.
- The tool JSON handed to the model must carry the schema's declared
  constraints — `enum`, `minimum`, `maximum`, `format`, `default`. They are what
  separates a fixed choice from a real population, and what grounds `limits`;
  `ToolSpec.parameters()` currently drops them.
- Type each **distinct** parameter once per server, not once per tool, and fan
  the answer back out. In the current catalogs 193 parameter occurrences collapse
  to 118 distinct `(name, description, type)` triples — `owner` and `repo` are
  otherwise typed 21 times each, independently and inconsistently.
- Rows are variable-shaped by design: a parser must read an absent field as "does
  not apply", never as a model error.
- Per-tool derivation keeps the prompt small and fans out across GPUs. Nothing
  in it depends on other tools, so a server's tools can be typed independently.
