<!-- sha256: d05e444a4cfa2f2138d40555ccef259a7d6c968f243ac5a60cf9871b87eaa63c · source: docs/standards/tool-input-importance-check.md -->

# Tool Input Importance Check

The v12 stage 1 second look. An earlier pass judged the inputs listed below not important to the risk of a call, and they are about to be dropped: stage 2 will never write a rule for them, and at run time their values will never be checked. A wrongly dropped input is the one mistake that cannot be fixed later. Your job is to catch those mistakes.

## What you are given

- the tool name and description;
- the inputs about to be dropped, each with its description, schema facts, and the reason the earlier pass gave;
- the tool's other inputs, name and description only, for context;
- optionally, the organization's policy rows for this tool. Any part may be empty.

## The question

For each input about to be dropped: **can you name one realistic value of this input, and the situation in which it is passed, that would make this call riskier than an ordinary call of the same tool?**

- If you can, the input is important. Write the value and the situation in `example`.
- If every allowed value gives an equally risky call, the input is not important. Leave `example` null.

Realistic means a value a caller of this tool could plausibly send, not a malformed or impossible one. Riskier means the call touches something more sensitive, reaches more people or more data, sends something out, changes more, or happens at a less expected time.

Inputs that are genuinely not important are things like a page number, a cursor copied from an earlier reply, an output format, a sort order, or a purely visual choice such as a color. Do not keep those just to be safe: if no realistic value makes the call riskier, say so.

## Rules

1. Answer every input listed below exactly once, using the same path. Answer none that is not listed.
2. `important` is `true` or `false`.
3. `example` is a short phrase naming the value and the situation when `important` is `true`, and null otherwise.
4. `reason` is one short sentence.
5. Never put a quotation mark inside any string value. Paraphrase instead of quoting.

## Output

Output ONLY valid JSON, no prose, no code fences:

```json
{"tool_name": "<name>", "arguments": [
  {"path": "<input path>",
   "important": false,
   "example": null,
   "reason": "<one short sentence>"}
]}
```

Tool: `{tool_json}`

Inputs about to be dropped, with the earlier reason: `{inputs_json}`

Other inputs of this tool, for context only: `{context_inputs_json}`

Policy for this tool (may be empty): `{policy_json}`