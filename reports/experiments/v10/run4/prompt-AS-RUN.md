<!-- sha256: 4fae213c99a45f49c0d3be4acfea54ebfc08aab4a959b1b6046064eed6daec6b · source: docs/standards/input-typing.md -->

# Tool Input Typing

For each argument an MCP tool declares, decide **how its value should be
interpreted later, during dynamic analysis** — not how risky it is. Four
classes: `RANGE` (values that compare), `POLICY` (values that name something a
policy must speak to), `IGNORE` (values this component should not evaluate),
`UNKNOWN` (not enough evidence).

Derived statically, from the tool registry alone. No risk, no severity, no
bands — banding a RANGE and resolving a POLICY value both happen at run time.

## Why four classes

A fixed label set is what makes the static pass **measurable**: arguments can be
hand-labelled once and the prompt scored by accuracy and per-class F1. Open
vocabulary cannot be scored. The set is deliberately about *mechanism* — which
dynamic check applies — rather than about the shape of the value, because the
shape is not the thing the next stage needs to know.

Two disciplines the prompt keeps:

- **No invented numbers.** Whether 100 is large depends entirely on the
  argument. Bounds are copied from the schema or reported absent, and thresholds
  are decided later from declared bounds or observed traffic.
- **Rules before examples.** Illustrations use argument names that appear in no
  server under test; a long list of names invites matching by resemblance
  instead of reasoning, and names drawn from the evaluation corpus would be
  answers to the test.

## LLM prompt (derivation)

> You are analysing the input schema of one MCP tool. Your task is not to
> estimate the risk of an argument. It is to decide, for each argument, HOW its
> value should be interpreted later, during dynamic analysis.
>
> Use the whole tool as context: its name and description, the argument's name
> and description, its JSON Schema type, format, bounds and enum, and the sibling
> arguments it is called alongside. Do not classify from the primitive JSON type
> — most arguments are declared as strings whatever they hold, and a numeric
> argument is not necessarily a quantity.
>
> Classify every leaf argument into exactly one class.
>
> ```
> RANGE    The values have a meaningful order: one value is more, larger, longer,
>          later or deeper than another, so comparing two values tells you
>          something. Return a subtype from:
>          count | amount | size | percentage | duration | temporal | limit | other
>
> POLICY   The value selects which entity, resource, subject, location,
>          organisational unit or category the call acts on. What matters is not
>          how large the value is but which one it is, and whether this caller
>          should have that one. That cannot be settled from the tool definition;
>          it has to be looked up in the organisation's policy. Return
>          policy_concept: what a policy would have to say something about.
>
> IGNORE   The value has neither a meaningful order nor an identity that a policy
>          would speak to: free text a person reads, an option that only changes
>          how a result is rendered, an ordinary operational switch, or a value
>          the caller copies from an earlier response rather than composes.
>
> UNKNOWN  The definition does not say enough to choose. Prefer this to guessing.
> ```
>
> Deciding rules — these are rules, not names to match:
>
> 1. An identifier has no meaningful order: a higher id is not more of anything.
>    An identifier is POLICY even when it is a number.
> 2. A quantity keeps its order even when written as a string: a date, a duration
>    or an amount in a string field is still RANGE.
> 3. Being categorical does not make something POLICY, and having few options
>    does not make it IGNORE. The question is whether choosing a different value
>    changes WHICH subject, resource or context the call acts on. If it changes
>    only presentation, it is IGNORE.
> 4. Free text is normally IGNORE, however long or however consequential the
>    text.
> 5. If the argument is a list, classify the list itself by its length — RANGE,
>    subtype count — and classify what a single item would be under `items`,
>    using these same classes. A list of identifiers is a RANGE whose items are
>    POLICY.
> 6. When a name is ambiguous, read the tool's purpose and its sibling arguments
>    before choosing. If it stays ambiguous, return UNKNOWN.
>
> Bounds: return `minimum`, `maximum` and `unit` only where the schema states
> them or the argument's own documentation does. Do not invent numbers — whether
> 100 is large depends entirely on the argument, and the thresholds are decided
> later from declared bounds or from observed traffic. Set `bounds_source` to
> `"schema"` when you copied declared bounds, `"documented"` when the description
> states them in words, and `"none"` when there are none; `"none"` tells the later
> stage it must learn them.
>
> Do not assign low, medium or high, and do not assess risk. This classification
> only decides which mechanism examines the value later.
>
> The following illustrate the rules. They are not a table to match names
> against; an argument you have not seen is classified by the rules, not by
> resemblance.
>
> ```
> user_id: integer                     -> POLICY   (an id has no order)
> max_results: integer                 -> RANGE / count
> retention_days: integer              -> RANGE / duration
> country: string                      -> POLICY   (which jurisdiction, not how much)
> environment: enum[dev,staging,prod]  -> POLICY   (changes which system is acted on)
> output_format: enum[a,b]             -> IGNORE   (changes only presentation)
> ```
>
> Describe every argument the tool declares, including nested ones, and none that
> it does not. Use a dotted path for nesting, with `[]` for a list's items
> (`files[].path`). If the tool declares no arguments, return an empty list.
>
> Output ONLY valid JSON, no prose, no fences:
>
> ```json
> {"tool_name": str, "arguments": [{
>   "path": str,
>   "classification": "RANGE|POLICY|IGNORE|UNKNOWN",
>   "subtype": "count|amount|size|percentage|duration|temporal|limit|other" | null,
>   "items": {"classification": str, "policy_concept": str} | null,
>   "minimum": number|null, "maximum": number|null, "unit": str|null,
>   "bounds_source": "schema|documented|none",
>   "policy_concept": str|null,
>   "reason": str,
>   "confidence": 0.0
> }]}
> ```
>
> Tool: `{tool_json}`