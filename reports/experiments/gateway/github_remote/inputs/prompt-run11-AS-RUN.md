<!-- sha256: 41802e7dd2614c723504bf62d3ff3436018048beb8663f7efdad32b6b052e196 -->

# Tool Input Importance

The v12 stage 1 prompt. For each input of one tool, answer two questions: does the input affect an asset, and how much can its value change the risk of the call, from 1 to 5. The program keeps an input only when both answers say it matters; every other input gets no run-time rule. The prompt names no particular product or organization and should work the same on any tool catalog.

## What you are given

You are analyzing one tool. You get:

- the tool name and description;
- every declared input, with its description and schema facts (type, format, enum values, minimum, maximum, whether it is required, default);
- optionally, the organization's policy rows for this tool: a short org context, the assets this tool can reach with a description of why each matters, special-value rules and baseline rows. Any part may be empty.

Use the whole tool as context. The purpose of the tool and the sibling inputs decide what an input means.

## Question 1: does the input affect an asset?

An asset is anything the organization would lose if it were misused: data, money, access rights, a running system, or the people it is responsible for. When the policy lists assets for this tool, those are the assets.

Answer **yes** if the value of the input decides or changes what the call does to an asset, in one of these ways, and name the way in `effect`:

| effect | the input decides | examples of such inputs |
|---|---|---|
| `which` | which asset is touched: the asset itself, not one record inside it | a file or folder, a record store, an account, a project, a container, a zone |
| `how_much` | how much of it | an amount, a count, a limit, a page size, a size, the number of items or recipients |
| `who` | who receives it, is notified, or gains access to it | a recipient, an audience, a member to add, a sharing or visibility setting, a switch that sends updates or notifications to people |
| `action` | what is done to it | a mode or switch that turns a read into a write, one item into all, a preview into a real change, private into public |
| `when` | when, or over what span | a start, an end, a window, a schedule, a recurrence, both for what is read and for when a change takes effect |
| `carried` | what is written into it, sent out of it, or run against it | a body, a message, a query or command that runs, a URL the server fetches |

Answer **no**, with `effect` set to `none`, if the input only changes how the result is shown, ordered, tagged or reminded; if it only moves the result window (a page number, an offset, a cursor), while a page size or a limit is `how_much`; if it is bookkeeping (a request id, an idempotency key, a version token copied from an earlier reply); or if it names a record inside an asset another input already picked (an issue number, a pull request number, an event id, a message timestamp), so the asset is already decided.

## Question 2: rank its influence from 1 to 5

Imagine two calls of this tool that are identical except for this input: one with the safest realistic value, one with the riskiest. How far apart are they?

| rank | meaning |
|---|---|
| 1 | No realistic value changes the risk of the call. |
| 2 | A small change: the riskiest value is only a little riskier. |
| 3 | A clear change: the riskiest value makes an ordinary call clearly riskier. |
| 4 | A large change: the riskiest value makes an ordinary call serious. |
| 5 | Decisive: the value alone can turn an ordinary call into a critical one. |

- For an input that names a target, the extremes are the most and the least sensitive target the call could name.
- For a quantity, the extremes are the smallest and the largest realistic value, not an impossible one.
- Rank the input, not the tool: on a tool that deletes, the sort order of its results is still 1.
- Text next to the main content (a title or subject next to a body, a change message next to the change, a display name) rarely ranks above 2, unless the policy says that text is sensitive.

## How the answers are used

Answer both questions on their own; you do not decide whether the input is kept. The program keeps an input when question 1 is yes **and** question 2 is 3 or more. An input the policy names in a special-value rule or a baseline row is kept regardless.

## Rules

1. Describe every declared input exactly once, including nested ones, using a dotted path with `[]` for list items (`files[].path`). Describe none that the tool does not declare.
2. If an input is a list whose length counts targets or recipients, describe the list itself too, with `how_much`.
3. A tool with many similar inputs, such as a list of items each with the same fields, repeats the same kinds of input. Give every copy of the same kind the same answers.
4. Two inputs that only name one asset together (an owner and a name, a bucket and a key) get the same answers.
5. `affects_asset` is `true` or `false`; `effect` is one of the words above; `rank` is a whole number from 1 to 5.
6. `reason` is one short sentence naming the safest and the riskiest value, or why no value matters.
7. Never put a quotation mark inside any string value, and never put a backslash anywhere.

## Examples

These come from products unlike the one you are judging; they show the reasoning only.

| Tool and input | Affects an asset | Rank | Kept |
|---|---|---|---|
| transfer_funds `amount` | yes, how_much | 5: a very large transfer against a small one | yes |
| transfer_funds `to_account` | yes, who | 5: an outside account against one's own | yes |
| transfer_funds `currency` | yes, how_much | 2: the same transfer in another currency | no |
| transfer_funds `idempotency_key` | no | 1: bookkeeping | no |
| put_object `bucket` and `key` | yes, which | 4: a bucket of customer records against a scratch bucket | yes |
| put_object `acl` | yes, who | 5: public read against private | yes |
| put_object `cache_control` | no | 1: how the object is served | no |
| send_email `to`, `cc`, `bcc` | yes, who | 5: outside recipients against a colleague | yes |
| send_email `subject` | yes, carried | 2: text next to the body | no |
| send_email `body` | yes, carried | 3: a body carrying confidential data | yes |
| run_sql `query` | yes, carried | 5: a statement that deletes or exports a table | yes |
| run_sql `output_format` | no | 1: presentation | no |
| list_employees `fields` | yes, which | 4: salary or national id columns against names | yes |
| list_employees `page` | no | 1: pagination | no |
| list_employees `page_size` | yes, how_much | 4: ten thousand rows against ten | yes |
| schedule_job `start_time` | yes, when | 3: three at night on a weekend against a weekday afternoon | yes |
| get_ticket `ticket_id`, project chosen by another input | no | 2: a record inside the chosen project | no |
| restore_backup `dry_run` | yes, action | 4: a real restore against a preview | yes |

## Output

Output ONLY valid JSON, no prose, no code fences:

```json
{"tool_name": "<name>", "arguments": [
  {"path": "<input path>",
   "affects_asset": true,
   "effect": "which | how_much | who | action | when | carried | none",
   "rank": 3,
   "reason": "<one short sentence>"}
]}
```

Some large tools are given in more than one batch, each batch with only its own inputs but the full tool description. Describe only the inputs present below.

Tool: `{tool_json}`

Inputs: `{inputs_json}`

Policy for this tool (may be empty): `{policy_json}`
