<!-- sha256: 3ad3af0ddb0a66e1d7baad1cf11a4ef8ff646655ce7cbbf32a010a247aee4e97 · source: docs/standards/tool-input-levels.md -->

# Tool Input Levels

The v13 prompt, one step per tool. For each input of the tool, first say what the input decides about the asset, then either write a rule that turns the input's value into a level from 1 to 5, using all five levels, or answer `null`. A program applies the rules at run time, with no model involved, and a call's level is the highest level among its inputs. The prompt names no particular product or organization and should work the same on any tool catalog.

## What you are given

- the tool name and description;
- the inputs to answer, with their description and schema facts (type, format, enum values, minimum, maximum, whether it is required, default);
- the tool's other inputs, for context only: switches and short choice lists, which cannot take five levels and are already decided;
- optionally, the organization: a short description, its normal workflow, the assets this tool can reach with a `scanned_level` from 1 to 5, the levels those assets reach (`asset_levels`), and the levels no asset reaches (`name_words_needed_for`). Any part may be empty;
- on a second try, an input may carry `problems_last_time`: the checks your previous rule for it failed. Fix those.

Use the whole tool as context. The purpose of the tool and the sibling inputs decide what an input means.

## The five levels

| Level | Meaning |
|---|---|
| 1 | The safest realistic value. |
| 2 | Safe. |
| 3 | Ordinary. |
| 4 | High: a sensitive target, a lot at once, outside working hours. |
| 5 | Critical: restricted or credential-bearing, bulk, or leaving the organization. |

An ordinary call in the normal workflow gets 1, 2 or 3 from every rule, never 4 or 5.

**Use only what can be known.** Build each level from what the value itself shows, from the tool, or from what you are given. Never make a level that needs facts nobody gave you, such as who a person is behind an opaque user id.

## Step 1: what does the input decide?

Name it in `effect`:

| effect | the input decides | examples |
|---|---|---|
| `which` | which asset is touched, or the account, owner or workspace it lives in | a repository and its owner, a folder, a path, a channel, a calendar, an account, a table, a database |
| `how_much` | how much of it | a limit, a page size, a count, a number of items or recipients |
| `who` | who receives it, is notified, or gains access | a recipient, an attendee, a member, a list of channels to add |
| `action` | what is done to it | a mode with five or more options |
| `when` | when, or over what span | a start, an end, a window, a recurrence, a schedule |
| `carried` | what is written into it, sent out of it, or run against it | a body, a message, a file's content, a description sent to attendees, a query or command that runs, a search text |
| `none` | nothing about the asset | see below |

## Step 2: the rule, or `null`

Write a rule for every input whose effect is not `none`, with three exceptions where the answer is `null`:

1. **It only narrows the call**: an exclude list, or the head or tail of a file that is read anyway. Leaving it out reads the same or more.
2. **It is a label next to the main content**: a title, a commit message or a display name, when the same tool has a separate body or content input that carries the main content.
3. **Its levels would need facts nobody has**: an opaque user id, where the level depends on who the person is.

`effect: none`, and so `null`, is for: how the result is shown, sorted, formatted or translated; a time zone, a color, a reminder or a tag; the result window (a page number, an offset, a cursor); bookkeeping (a request id, an idempotency key, a version token copied from an earlier reply); a record inside an asset another input already picked (an issue or pull request number, an event id, a message timestamp, a comment id, a commit).

**Never `null`**: an input that names the asset or where it lives (a repository, an owner, an organization, a channel, a calendar, an account, a path, a table); the body, content, message, description or query that is written, sent or run; a limit, a page size or a count; a time, a window or a recurrence; a recipient or member list.

Two inputs that name one asset together (an owner and a repository, an account and a calendar) both get a rule.

## Rule kinds

Every rule must reach each level 1, 2, 3, 4 and 5 with at least one entry of its own. `default` is the level for a value that matches nothing; it does not count as an entry. Usually it is 3.

The examples below show the shape only. **Do not copy their words or numbers**: write fragments and cut-offs for this tool's own data and the organization's assets.

### `ranges`: a number, a count, a size, a length or a time

```json
{"kind": "ranges", "measure": "value", "ranges": [
  {"min": null, "max": 5, "level": 1},
  {"min": 5, "max": 20, "level": 2},
  {"min": 20, "max": 200, "level": 3},
  {"min": 200, "max": 2000, "level": 4},
  {"min": 2000, "max": null, "level": 5}], "default": 3}
```

| measure | computed from the value | use it for |
|---|---|---|
| `value` | the number itself | counts, limits, page sizes, amounts |
| `length` | the number of items in a list, or characters in a string | how many files, recipients or attendees |
| `span_hours` | hours between this date-time and the sibling named in `with` | a window given by a start and an end |
| `hour_of_day` | the hour of a date-time, 0 to 24 | when a change or a meeting happens |
| `hours_from_now` | hours from the call to this date-time; negative is the past | how far ahead a change takes effect |

- A range matches when `min <= x < max`; `null` is open. For `value`, `length` and `span_hours`, the last range is open at the top.
- **A window**: put a `span_hours` rule on both the start and the end, each naming the other in `with`. The length of the window is what matters, not how far away it is.
- **Time of day**: peak working hours are the safest, levels 1 and 2; late night is 5.

### `register`: the value names one of the listed assets, or the account or owner they live in

```json
{"kind": "register", "groups": [
  {"contains": ["sandbox"], "level": 2},
  {"contains": ["billing"], "level": 3}], "default": 3}
```

At run time a value that names a listed asset gets that asset's `scanned_level`; those levels count as entries. Write `groups` of name fragments for **every level in `name_words_needed_for`**, so that a name not on the list can still be rated. A name that matches neither gets `default`. With no asset list, the groups must reach all five levels.

### `keywords`: a path, a query, a body, a command, a search text

```json
{"kind": "keywords", "groups": [
  {"contains": ["changelog"], "level": 1},
  {"contains": ["draft"], "level": 2},
  {"contains": ["invoice"], "level": 3},
  {"contains": ["salary"], "level": 4},
  {"contains": ["private_key"], "level": 5}], "default": 3}
```

The value is lowercased and checked for each fragment; the highest matching group wins. Write fragments in lower case, as plain text, never as regular expressions. Rate what the text touches or reveals, not its grammar: for a query, the data it names and the operation it performs.

### `values`: a choice of five or more options

```json
{"kind": "values", "values": [
  {"value": "a", "level": 1}, {"value": "b", "level": 2}, {"value": "c", "level": 3},
  {"value": "d", "level": 4}, {"value": "e", "level": 5}], "default": 3}
```

Compared with each listed value, ignoring case.

### `email`: an email address

```json
{"kind": "email"}
```

The levels are fixed and come from the organization's policy: its own domain 1, a partner domain it lists 2, another organization 3, a domain it flags 4, a personal mailbox such as a free webmail account 5. Write nothing else in this rule.

## Absent inputs and lists

- `when_absent` is the level when the call leaves the input out. It is `null` unless leaving it out widens the call to everything in scope: a search with no channel filter that searches every channel, a list with no limit that returns everything.
- For a list item (a path with `[]`), the rule is applied to every item and the highest level counts. To rate how many items there are, put a `length` rule on the list itself.

## Examples

These come from products unlike the one you are judging; they show the reasoning only.

| Tool and input | effect | Answer |
|---|---|---|
| export_records `limit` | `how_much` | `ranges` on `value`, five ranges from a handful to the whole table |
| list_invoices `from` and `to` | `when` | on both, `ranges` on `span_hours` with the other: a day, a week, a month, a quarter, longer |
| schedule_job `start` | `when` | `ranges` on `hour_of_day`: midday at 1, the edges of the working day at 2, early morning and evening at 3, late evening at 4, night at 5 |
| query_db `database`, assets listed at 1, 3 and 5 | `which` | `register`, name words for 2 and 4 |
| query_db `workspace`, the account the databases live in | `which` | `register`, name words for all levels the assets miss |
| run_sql `query` | `carried` | `keywords`: read-only words low, writes high, destructive or permission changes at 5, sensitive table names raising it |
| send_mail `to[]` | `who` | `email` |
| send_mail `body` | `carried` | `keywords` on what the body reveals |
| send_mail `subject`, with a body input | `carried` | `null`: a label next to the main content |
| export_file `exclude[]` | `how_much` | `null`: it only narrows the call |
| add_member `user_id`, opaque | `who` | `null`: who the user is cannot be known from the id |
| get_ticket `ticket_id`, project chosen by another input | `none` | `null`: a record inside the chosen project |
| list_files `order_by` | `none` | `null`: presentation |

## Before you answer, check

1. Does every rule reach each level 1 to 5 with an entry of its own? For `register`, do your name words cover every level in `name_words_needed_for`?
2. Does an ordinary call get 1, 2 or 3 from every rule?
3. Is every `null` either `effect: none` or one of the three exceptions, named in `reason`?
4. Did you write this tool's own words, not the examples'?

## Rules

1. Answer every input listed under Inputs exactly once, using the same path, including nested ones (`files[].path`). Answer none that is not listed there.
2. Every level and `default` is a whole number from 1 to 5.
3. `reason` is one short sentence: what decided the levels, or why the answer is `null`.
4. Never put a quotation mark inside any string value, and never put a backslash anywhere.

## Output

Output ONLY valid JSON, no prose, no code fences:

```json
{"tool_name": "<name>", "inputs": [
  {"path": "<input path>",
   "effect": "which | how_much | who | action | when | carried | none",
   "rule": {"kind": "ranges | register | keywords | values | email", "...": "fields of that kind"},
   "when_absent": null,
   "reason": "<one short sentence>"},
  {"path": "<input path>", "effect": "none", "rule": null, "reason": "<why>"}
]}
```

Some large tools are given in more than one batch, each with only its own inputs but the full tool description. Answer only the inputs present below.

Tool: `{tool_json}`

Inputs: `{inputs_json}`

Other inputs of this tool, already decided, for context only: `{context_inputs_json}`

Organization (may be empty): `{policy_json}`