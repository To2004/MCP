<!-- sha256: cced1025dfb3e8ca1d2f4c003085a9596c20925bebe0f751146607ad8576b310 · source: docs/standards/tool-input-importance-check.md -->

# Tool Input Importance Check

The v12 stage 1 second look. The inputs listed below did not get a clear majority in the earlier passes: most passes judged them not important, and they are about to be dropped. Stage 2 will write no rule for them, and at run time their values will never be checked. Your job is to keep the few that really drive the risk of a call, and to confirm the drop for the rest.

## What you are given

- the tool name and description;
- the inputs about to be dropped, each with its description, schema facts, and what the earlier passes said;
- the tool's other inputs, name and description only, for context;
- optionally, the organization's policy rows for this tool. Any part may be empty.

## The question

For each input, name the **riskiest realistic value** and the **safest realistic value**, and compare two calls of this tool that differ only in this input. Keep the input only if the riskiest call is clearly riskier: at least two steps on a five-step scale from safe (1) to critical (5), where an ordinary call is 3.

Clearly riskier means one of these, concretely:

- it reaches a more sensitive target named in the policy, or a target outside the organization;
- it reaches many more records or people at once;
- it sends something out, or opens something to more people;
- it makes a change much larger or harder to undo.

Two kinds of evidence settle the question in favor of keeping:

- the input is a target, a quantity that can reach bulk, the start or end of a window, a switch that opens something to more people, a send or notify switch, or the main content written or sent, and you cannot rule out that its riskiest value matters;
- the same input was kept in another tool of this server (shown as `kept_in_other_tools`, with that tool's reason): keep it here too, unless this tool's purpose makes it irrelevant (an account selector on a tool that only returns a fixed color palette).

These are not enough, and mean the answer is no:

- the value *can indicate*, *may affect* or *could reveal* something, without saying what it would reach;
- it only changes how the result is shown, ordered, paged, labeled or reminded;
- it picks a record inside a target another input already chose;
- it is secondary text next to the main content, unless the policy says this text is sensitive.

## Rules

1. Answer every input listed below exactly once, using the same path. Answer none that is not listed.
2. `important` is `true` or `false`.
3. `example` names the riskiest value and what it would reach, when `important` is `true`; null otherwise.
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

Inputs about to be dropped, with what the earlier passes said: `{inputs_json}`

Other inputs of this tool, for context only: `{context_inputs_json}`

Policy for this tool (may be empty): `{policy_json}`