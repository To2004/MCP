<!-- sha256: 5733f6c6aabeb0a8c33c2aa5298af58963cd718918729513409aa5e3abc7d02d · source: docs/standards/tool-input-importance.md -->

# Tool Input Importance

The v12 stage 1 prompt. For one MCP tool, decide which of its inputs are important to the risk of a call and which are not, so that only the important ones get run-time rules in stage 2. The decision is about meaning: what the input stands for in this tool, and whether choosing a different value could change how risky the call is. The answer for each input is yes or no.

Dropping an input is the one mistake that cannot be fixed later: stage 2 never sees it, and at run time its value is never checked. Keeping an input that turns out not to matter costs almost nothing. So this pass answers yes for every input except a short list of inputs that clearly cannot matter.

## What you are given

You are analyzing one MCP tool. You get:

- the tool name and description;
- every declared input, with its description and schema facts (type, format, enum values, minimum, maximum, whether it is required, default);
- optionally, the organization's policy rows for this tool: a short org context, the normal workflow, the assets this tool can reach (with a description of why each matters), special-value rules and baseline rows. Any part may be empty.

Use the whole tool as context. The purpose of the tool and the sibling inputs decide what an input means.

## The question

For each input: **is there any realistic value of this input that would make this call riskier than an ordinary call?**

If yes, the input is important. Answer no only when every allowed value gives an equally risky call.

Think about what the input means in this tool, not about its type.

- An input that chooses between black and white, or light and dark, is not important. Either value gives the same call.
- An input that holds an amount of money is important. A small transfer and a very large one are very different calls.
- An input that names a repository, a folder, an account or a recipient is important, because it decides what the call touches.

An input can be a number and not matter, and a plain string and matter most. Judge the effect, not the type.

## Always important

Answer yes for any input that does one of these, whatever its type:

1. **Picks what the call touches**: a repository, owner, file path, folder, branch, channel, calendar, event, issue, database, table, account, tenant, user, recipient, attendee, URL, or any id that names one of these.
2. **Sets how much**: an amount, a size, a count, a limit, a page size, a number of items, a batch, the length of a list. A large value can mean reading or changing a lot at once.
3. **Sets when or for how long**: a date, a time, a start, an end, a time window, a duration, a recurrence. A time outside normal hours, or a long window, can be notable.
4. **Widens who can see, join or change something**: public or private, visibility, sharing, guests can invite or modify, anyone can join, include members or users, include disabled or hidden items.
5. **Sends something out or notifies people**: send updates, notify, email, post, invite, publish.
6. **Changes what the operation does**: an action or mode that turns one operation into another (join or leave, approve or reject or comment, merge or squash, one item or all items, delete or archive, read or write).
7. **Carries the content written or sent**: a file body, a message text, a commit content, a query that is executed. What is written can carry secrets or personal data.
8. **Scopes or filters the call, when leaving it out widens the call**: a channel filter on a search, a repository qualifier, a folder filter. Its absence can mean the whole workspace.
9. **Appears anywhere in the policy given below**: in a special-value rule, a baseline row, or as the input that decides which listed asset is reached.

## May be not important

Only these may be answered no, and only when the tool's description gives no sign that the value does more than its plain job:

- a page number, an offset, or a cursor or page token copied from an earlier reply: it moves the window, the same data is reachable either way;
- the output format or encoding (csv or json, markdown or plain text);
- the sort order or sort direction;
- purely visual choices: a color, a theme, a display time zone that only changes how a time is shown;
- a human-readable label that is only displayed and is not the content of what is written or sent, such as an optional short display name, when the tool also carries the real content in another input.

If an input is not on this list, the answer is yes. If you are unsure whether it is on this list, the answer is yes.

## Rules

1. Describe every declared input exactly once, including nested ones, using a dotted path with `[]` for list items (`files[].path`). Describe none that the tool does not declare.
2. If an input is an array, also describe the array itself when its length could matter (rule 2 above); its length is a count.
3. A tool with many similar inputs, such as a list of events each carrying a start, an end and attendees, repeats the same kinds of input. Give every copy of the same kind the same answer.
4. The same input name in the same tool family gets the same answer unless the tool's purpose clearly differs (an account selector is important in every tool that reads or changes data).
5. `important` is `true` or `false`.
6. `reason` is one short sentence. For `true`, name the kind of risk the input carries. For `false`, name the item on the not-important list it belongs to.
7. Never put a quotation mark inside any string value. Paraphrase instead of quoting.

## Examples

These show the reasoning only. Judge the real tool below from its own text.

| Tool and input | Important | Why |
|---|---|---|
| send_money `amount` | yes | sets how much money moves |
| send_money `recipient_account` | yes | picks where the money goes |
| send_money `currency` | yes | changes what is moved; not on the not-important list |
| send_money `memo`, free text | yes | content sent to another party |
| set_theme `color`, black or white | no | purely visual choice |
| export_records `database_id` | yes | picks which data is exported |
| export_records `limit`, 1 to 10000 | yes | sets how much is read |
| export_records `format`, csv or json | no | output format |
| list_items `page`, integer | no | page number |
| list_items `cursor`, copied from a reply | no | cursor |
| list_items `sort`, asc or desc | no | sort order |
| move_file `destination` | yes | picks where the data ends up |
| deploy `environment`, dev, staging or production | yes | picks what the call touches |
| create_repo `private`, boolean | yes | widens who can see it |
| search `channel_filter`, optional | yes | leaving it out searches everything |
| update_event `scope`, this event or all events | yes | changes what the operation does |

## Output

Output ONLY valid JSON, no prose, no code fences:

```json
{"tool_name": "<name>", "arguments": [
  {"path": "<input path>",
   "important": true,
   "reason": "<one short sentence>"}
]}
```

Some large tools are given in more than one batch, each batch with only its own inputs but the full tool description. Describe only the inputs present below.

Tool: `{tool_json}`

Inputs: `{inputs_json}`

Policy for this tool (may be empty): `{policy_json}`