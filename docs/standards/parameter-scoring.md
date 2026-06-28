# Input-Parameter Scoring

A call's risk is not only *which tool touches which asset* — it is also *how much*
the call's **input parameters** ask for. Sending a calendar invite to 3 people and
to 200 people use the same tool and asset; the parameter magnitude is what differs.
This rubric scores the input parameters of a call and combines that with the
(tool, asset) judgment from the scan.

It is written to be used **two ways**: as a human spec, and verbatim as the
**prompt** the local LLM (Ollama/Qwen) reads to derive a per-tool parameter rubric.
The numbers below are *examples* — the model derives the actual cutoffs per tool
from the tool's own parameters and domain; nothing is hardcoded per server.

## What the LLM produces (per tool)

For each tool, identify the input parameters that carry **risk magnitude** (a count,
a size, a breadth, a recipient list, a row limit, a recursion depth, …) and for each
give:

1. **base_rank** — how sensitive the parameter is *intrinsically*, ignoring its
   value: `low | medium | high | critical`. (e.g. "attendees" on a calendar invite
   is `medium`; "delete recursively" flag is `high`.)
2. **cutoffs** — ascending numeric thresholds that map the parameter's *value* to a
   band. A value is banded by the highest threshold it meets or exceeds.
3. **extract** — how to read the value from the call arguments: a number directly,
   the **length of a list**, a parsed `LIMIT`, a boolean (true ⇒ its `when_true`
   band), etc.

**Free-text parameters carry magnitude too.** If a parameter is a query or command
string (e.g. a SQL statement), the breadth it touches is magnitude. Use
`extract: parsed_limit` on that parameter: an explicit `LIMIT n` bounds it to `n`
rows, and its **absence means unbounded** — a `SELECT`/`UPDATE`/`DELETE` with no
`LIMIT` touches every row, the widest possible reach, so unbounded must land in the
top cutoff. Always give a query/command parameter a `parsed_limit` rubric.

### Worked example — sqlite `read_query`, parameter `query`

```
parameter: query
base_rank: medium
extract:   parsed_limit       # LIMIT n -> n; no LIMIT -> unbounded (worst)
cutoffs:   >= 100   -> low
           >= 1000  -> medium
           >= 5000  -> high
           # unbounded (no LIMIT) lands above the top cutoff -> critical reach
```

### Worked example — calendar `create_event`, parameter `attendees`

```
parameter: attendees
base_rank: medium
extract:   length of the attendees list
cutoffs:   < 3        -> low
           3 .. 6     -> medium
           7 .. 10    -> high
           11 .. 20   -> high
           > 20       -> critical
```

So 2 attendees → low, 5 → medium, 20 → high, 50 → critical (the *value band*).

## Combining the bands

Bands are ranked `low=1 · medium=2 · high=3 · critical=4`.

1. **value_band** comes from the cutoffs above for the call's actual value.
2. **parameter risk** = average of the parameter's `base_rank` and the `value_band`,
   rounded half-up. This is the user's rule: a `medium` parameter (base) with a
   value that lands `critical` ⇒ average(2, 4) = 3 ⇒ **high**.
3. **final band** = the parameter risk **escalates** the (tool, asset) band from the
   scan — the higher of the two wins (a dangerous parameter can raise inherent
   risk, never lower it):

   ```
   final = max( tool_asset_band , parameter_risk )
   ```

   When a call has several risky parameters, take the most severe parameter risk.

### Example end to end

`create_event` on a shared team calendar (tool×asset band = `medium`), `attendees`
base_rank `medium`, 20 people → value_band `high`(11-20):
- parameter risk = average(medium=2, high=3) = 2.5 → round half-up → 3 = **high**
- final = max(medium, high) = **high**

(If 50 people: value_band `critical`, parameter risk = average(2,4)=3 = high,
final = max(medium, high) = high. A `high` base parameter at 50 → average(3,4)=3.5
→ critical.)

## LLM prompt (derivation)

> You are a security analyst. For the MCP tool below, list only the input
> parameters that carry **risk magnitude** — a count, size, breadth, recipient
> list, row limit, recursion depth, or an escalating flag. For each, return its
> `base_rank` (low/medium/high/critical), how to `extract` its value from a call
> (number | list_length | parsed_limit | boolean), and ascending `cutoffs` mapping
> the value to bands, following the worked example above. If the tool has no
> magnitude-bearing parameter, return an empty list. Output ONLY valid JSON.
>
> Tool: `{tool_json}`
>
> Return: `{"tool_name": str, "parameters": [{"name": str, "base_rank":
> "low|medium|high|critical", "extract": "number|list_length|parsed_limit|boolean",
> "cutoffs": [{"min": number, "band": "low|medium|high|critical"}],
> "when_true": "low|medium|high|critical"|null, "reasoning": str}]}`

The application of the derived rubric to a concrete call (reading the value,
banding it, combining) is deterministic and lives in
`mcp_security.param_scoring`.
