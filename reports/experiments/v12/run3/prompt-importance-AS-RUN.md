<!-- sha256: 86f3da7e129cae585a6efce3e32f15afa6c23dd2ee9baf2c4a2642303e37280c · source: docs/standards/tool-input-importance.md -->

# Tool Input Importance

The v12 stage 1 prompt. For one MCP tool, decide which of its inputs are important to the risk of a call and which are not, so that only the important ones are analyzed further. The decision is about meaning: what the input stands for in this tool, and whether choosing a different value would change how risky the call is. The answer for each input is yes or no. This pass does not label inputs and does not rate values.

## What you are given

You are analyzing one MCP tool. You get:

- the tool name and description;
- every declared input, with its description and schema facts (type, format, enum values, minimum, maximum, whether it is required, default);
- optionally, the organization's policy rows for this tool: a short org context, the normal workflow, the assets this tool can reach (with a description of why each matters), special-value rules and baseline rows. Any part may be empty.

Use the whole tool as context. The purpose of the tool and the sibling inputs decide what an input means.

## The question

For each input: **if the caller chose a different value, would the call become more or less risky?**

If yes, the input is important. If the call would be about equally risky whatever value is chosen, the input is not important.

Think about what the input means in this tool, not about its type.

- An input that chooses between black and white, light and dark, or a short list of display options is not important. Either value gives about the same call.
- An input that holds an amount of money is important. A small transfer and a very large one are very different calls.
- An input that names a repository, a folder, an account or a recipient is important, because it decides what the call touches.
- A page number, a sort order or an output format is not important.

An input can be a number and not matter, and a plain string and matter most. Judge the effect, not the type.

## How to decide

- Imagine two very different values, such as the smallest and the largest, or two different targets. If the call would be about equally risky in both, the input is not important.
- The tool matters. On a tool that creates, changes, sends or deletes something, the input that picks the target or the quantity is important. On a read-only tool over public data, few inputs are.
- The policy matters. An input that appears in a special-value rule or a baseline row, or that decides which listed asset is reached, is important.
- A path, a name, an id or an address that picks what the call touches is important.
- A size, a count, a limit or a time window is important when a large value could mean reading or changing a lot at once, or a time could fall outside normal use. It is not important when it only moves the result window, like a page number.
- Free text is not important, even when it is long, unless the description says the text is itself the target (a file path typed as a query, for example).
- An input that only matters together with a sibling is important, and so is the sibling. Say so in `reason`.
- A tool with many similar inputs, such as a list of events each carrying a start, an end and attendees, repeats the same kinds of input. Decide each kind once and give every copy the same answer.
- **When in doubt, answer yes.** An input wrongly kept costs a little later, and an input wrongly dropped is never seen again.

## Rules

1. Describe every declared input exactly once, including nested ones, using a dotted path with `[]` for list items (`files[].path`). Describe none that the tool does not declare.
2. If the length of an array matters, also describe the array itself.
3. `important` is `true` or `false`. There is no other answer.
4. `reason` is one short sentence naming what the input means and why it does or does not change the risk. It is never empty.
5. Never put a quotation mark inside any string value. Paraphrase instead of quoting.

## Examples

These show the reasoning only. Judge the real tool below from its own text.

| Tool and input | Important | Why |
|---|---|---|
| send_money `amount` | yes | the amount of money decides how serious the transfer is |
| send_money `recipient_account` | yes | decides where the money goes |
| send_money `currency` | no | the same transfer in another currency is about as risky |
| send_money `memo`, free text | no | free text for a person to read |
| set_theme `color`, black or white | no | the two options are equivalent, so neither changes the risk |
| export_records `database_id` | yes | decides which data is exported |
| export_records `limit`, 1 to 10000 | yes | a very large export reads a lot at once |
| export_records `format`, csv or json | no | changes the output form only |
| list_items `page`, integer | no | only moves the result window |
| move_file `destination` | yes | decides where the data ends up |
| deploy `environment`, dev, staging or production | yes | the target environment decides the stakes |
| schedule_job `start_hour` | yes | a change at an unusual hour is riskier, and in doubt the answer is yes |

## Output

Output ONLY valid JSON, no prose, no code fences:

```json
{"tool_name": "<name>", "arguments": [
  {"path": "<input path>",
   "important": true,
   "reason": "<one short sentence>"}
]}
```

`important` is `true` or `false`.

Some large tools are given in more than one batch, each batch with only its own inputs but the full tool description. Describe only the inputs present below.

Tool: `{tool_json}`

Inputs: `{inputs_json}`

Policy for this tool (may be empty): `{policy_json}`