<!-- sha256: 851d11fc795cdd7bf2594f549ffc4ba740f8afb5015f24ee818ec9518f2dfe6d · source: docs/standards/tool-input-features-composites.md -->

# Cross-Argument Composites

You are given one tool's full argument list, each with the feature flags
already decided for it (from `docs/standards/tool-input-features.md`'s
per-argument pass). Your only question:

> Which *pairs or groups* of this tool's arguments only reveal something
> when read **together** that neither argument states **alone**?

A `start` and `end` pair reveals a duration — no single argument's flags say
"how long," only the pair does. A `filter` and `limit` pair changes the
effective reach of a call in a way neither argument's own flags capture: the
same `limit` means something different with a narrow filter than with none.

## What is NOT a composite

Most pairs of arguments in a tool are **not** composites. Do not report a
pair just because:

- both arguments are required, or both are used in the same call — every
  multi-argument tool has arguments used together; that alone reveals
  nothing new.
- one argument names a target and another supplies content for it (a path
  and the content to write there, a channel and the message to post) —
  this is an ordinary target/payload pair, not an emergent fact.
- they happen to appear near each other in the schema.

**The test**: can you state a new fact, quantity, or meaning that exists
only because of the pair, and that fact would need its own name if someone
asked you to describe it (a duration, an effective scope, a rate, a
resolved timezone)? If the honest answer is "they're just both inputs to
this tool," it is not a composite — leave it out.

## Output

Output ONLY valid JSON, no prose, no fences:

```json
{"tool_name": str, "composites": [{"args": [str], "meaning": str, "note": str}]}
```

Return `{"tool_name": str, "composites": []}` if none apply — an empty list
is the expected, honest answer for most tools. Do not force one to avoid
returning empty.

Tool: `{tool_summary_json}`

Arguments (with their already-decided flags): `{argument_flags_json}`
