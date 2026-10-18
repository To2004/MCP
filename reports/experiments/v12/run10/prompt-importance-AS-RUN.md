<!-- sha256: 0b1209147e6521a007c5f97f73234b0c3f729e59d6a364aa2c7295fff396d48a · source: docs/standards/tool-input-importance.md -->

# Tool Input Importance

The v12 stage 1 prompt. For each input of one tool, answer two questions. First: can this input's value be ranked on a risk scale from 1 to 5, and if so, in which way? Second: how risky is the call at the input's safest realistic value, and how risky at its riskiest? The program keeps an input only when it can be ranked and the riskiest value is at least two steps above the safest; every other input gets no run-time rule. The prompt names no particular product or organization and should work the same on any tool catalog.

## What you are given

You are analyzing one tool. You get:

- the tool name and description;
- every declared input, with its description and schema facts (type, format, enum values, minimum, maximum, whether it is required, default);
- optionally, the organization's policy rows for this tool: a short org context, the assets this tool can reach with a description of why each matters, special-value rules and baseline rows. Any part may be empty.

Use the whole tool as context. The purpose of the tool and the sibling inputs decide what an input means.

## Question 1: can the value be ranked from 1 to 5, and how?

Look only at the value a caller would pass. Can you tell, from the value alone, whether this call is safer or riskier? Say which `kind` of input it is. The kind decides how its risk is ranked later.

| kind | the input is | how its value is ranked | example values, low to high |
|---|---|---|---|
| `number` | an amount, a count, a limit, a size, a page size, a duration | by size | 10 rows, 1 000 rows, 1 000 000 rows |
| `asset_id` | the name or id of an asset the organization keeps: a repository, a channel, a calendar, a database, a bucket, an account | by which asset it is, looked up in the organization's policy | a public site, an internal project, a restricted system |
| `time` | a date, a time, a start, an end, a window, a schedule | by time of day, day of week, or length of window | a weekday afternoon, an evening, three at night |
| `choice` | a fixed set of options or a switch: visibility, environment, action, scope, on or off | each option gets its own level | private, internal, public |
| `recipient` | an email address, a user, a domain, a URL something is sent to | inside or outside the organization | a colleague, a partner, an unknown outside address |
| `name_or_path` | a file path, a folder, a table name, a key, a pattern of names | by what the name contains | a temporary file, a project file, a file of keys or passwords |
| `content` | a message, a file body, a query or a command that runs, text that is stored or sent | by what the text contains | a status note, personal data, a destructive or exporting statement |
| `record_id` | an id or token that only points at one record or position: an issue number, an event id, a request id, a cursor, a version token | cannot be ranked: the value itself says nothing about risk | none |
| `none` | anything whose values all lead to the same call: a color, a sort order, an output format, a reminder setting | cannot be ranked: no value is riskier than another | none |

`rankable` is `true` for the first seven kinds and `false` for `record_id` and `none`.

Two inputs that look alike can differ. The name of a repository is an `asset_id` (the policy can say how sensitive it is); the number of an issue inside that repository is a `record_id` (no rule can tell a risky issue number from a safe one). A page size is a `number` (it sets how much is read); a page number only moves the window and is `none`.

## Question 2: the safest and the riskiest value

Imagine two calls of this tool that are identical except for this input: one with the **safest** realistic value, one with the **riskiest** realistic value. Give each call a level on this scale:

| level | meaning |
|---|---|
| 1 | No concern: safer than an ordinary call. |
| 2 | Low. |
| 3 | An ordinary call of this tool. |
| 4 | High: a sensitive target, a lot at once, an unusual time, an unusual audience. |
| 5 | Critical: a restricted target, outside the organization, a bulk or irreversible change. |

- For a target, the extremes are the most and the least sensitive target the call could name. For a quantity, the smallest and the largest realistic value, not an impossible one.
- If the policy describes the assets or says what is normal, use it.
- Rank this input, not the tool: on a tool that deletes, the sort order of its results changes nothing.
- An input that cannot be ranked still gets both levels; they will usually be equal.

## How the answers are used

You do not decide whether the input is kept. The program keeps an input when `rankable` is true **and** `riskiest_level - safest_level` is 2 or more. An input the policy names in a special-value rule or a baseline row is kept regardless. For every kept input, the next stage writes a run-time rule from its `kind`.

## Rules

1. Describe every declared input exactly once, including nested ones, using a dotted path with `[]` for list items (`files[].path`). Describe none that the tool does not declare.
2. If an input is a list whose length counts targets or recipients, also describe the list itself, as a `number`.
3. A tool with many similar inputs, such as a list of items each with the same fields, repeats the same kinds of input. Give every copy of the same kind the same answers.
4. Two inputs that only name one asset together (an owner and a name, a bucket and a key) get the same answers.
5. `safest` and `riskiest` name the two values briefly; the levels are whole numbers from 1 to 5.
6. `reason` is one short sentence.
7. Never put a quotation mark inside any string value, and never put a backslash anywhere.

## Examples

These come from products unlike the one you are judging; they show the reasoning only.

| Tool and input | kind | safest, level | riskiest, level | kept |
|---|---|---|---|---|
| transfer_funds `amount` | number | a small payment, 2 | a very large transfer, 5 | yes |
| transfer_funds `to_account` | recipient | one's own account, 2 | an unknown outside account, 5 | yes |
| transfer_funds `currency` | choice | the home currency, 3 | another currency, 3 | no |
| transfer_funds `idempotency_key` | record_id | any, 3 | any, 3 | no |
| put_object `bucket` | asset_id | a scratch bucket, 2 | a bucket of customer records, 5 | yes |
| put_object `acl` | choice | private, 2 | public read, 5 | yes |
| put_object `cache_control` | none | any, 3 | any, 3 | no |
| send_email `subject` | content | a routine subject, 3 | a subject naming a confidential deal, 4 | no |
| send_email `attachments[].name` | name_or_path | a meeting agenda, 3 | a payroll export, 5 | yes |
| run_sql `query` | content | a small select, 3 | a statement that deletes or exports a table, 5 | yes |
| list_employees `page_size` | number | 10 rows, 2 | 10 000 rows, 5 | yes |
| list_employees `page` | none | page 1, 3 | page 400, 3 | no |
| get_ticket `ticket_id` | record_id | any, 3 | any, 3 | no |
| schedule_job `start_time` | time | a weekday afternoon, 3 | three at night on a weekend, 5 | yes |

## Output

Output ONLY valid JSON, no prose, no code fences:

```json
{"tool_name": "<name>", "arguments": [
  {"path": "<input path>",
   "kind": "number | asset_id | time | choice | recipient | name_or_path | content | record_id | none",
   "rankable": true,
   "safest": "<the safest realistic value, briefly>",
   "safest_level": 2,
   "riskiest": "<the riskiest realistic value, briefly>",
   "riskiest_level": 5,
   "reason": "<one short sentence>"}
]}
```

Some large tools are given in more than one batch, each batch with only its own inputs but the full tool description. Describe only the inputs present below.

Tool: `{tool_json}`

Inputs: `{inputs_json}`

Policy for this tool (may be empty): `{policy_json}`