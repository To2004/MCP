<!-- sha256: 8e58bb649af60e7d778da49227e5a50e0653fc5d0e19ac10af581aaf18c8e804 · source: docs/standards/tool-input-levels.md -->

# Tool Input Levels

The v13 prompt, one step per tool. For each input of the tool, either write a rule that turns the input's value into a level from 1 to 5, using all five levels, or answer `null` when the input cannot be rated that way. A program applies the rules at run time, with no model involved, and a call's level is the highest level among its inputs. The prompt names no particular product or organization and should work the same on any tool catalog.

## What you are given

- the tool name and description;
- every declared input, with its description and schema facts (type, format, enum values, minimum, maximum, whether it is required, default);
- optionally, a short description of the organization, its normal workflow, and the assets this tool can reach, each with a `scanned_level` from 1 to 5. Any part may be empty;
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

**Use only what can be known.** Build each level from what the value itself shows, from the tool, or from what you are given. Never make a level that needs facts nobody gave you, such as who a person is, which team they are on, or whether a name belongs to a partner.

## Answer `null` when

1. **The input does not touch an asset.** It changes how the result is shown, sorted, formatted or translated; it sets a time zone, a color, a reminder or a tag; it moves the result window (a page number, an offset, a cursor); or it is bookkeeping (a request id, an idempotency key, a version token copied from an earlier reply). A page size or a limit is not bookkeeping: it decides how much is read.
2. **It names a record inside an asset that another input already picked**: an issue or ticket number, an event id, a message timestamp, a comment id, a commit. The asset is already decided.
3. **It cannot take five different levels**: a true or false switch, or a choice of two to four options.
4. **It is text next to the main content**: a title or subject next to a body, a change message next to the change, a display name.
5. **Its levels would need facts you do not have**, as above.

## Rule kinds

Every rule must reach each level 1, 2, 3, 4 and 5 with at least one entry of its own. `default` is the level for a value that matches nothing; it does not count as an entry. Usually it is 3.

### `ranges`: a number, a count, a size, a length or a time

```json
{"kind": "ranges", "measure": "value", "ranges": [
  {"min": null, "max": 10, "level": 1},
  {"min": 10, "max": 100, "level": 2},
  {"min": 100, "max": 1000, "level": 3},
  {"min": 1000, "max": 10000, "level": 4},
  {"min": 10000, "max": null, "level": 5}], "default": 3}
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

### `register`: the value names one of the listed assets

```json
{"kind": "register", "groups": [
  {"contains": ["test", "sandbox"], "level": 2},
  {"contains": ["finance", "payroll"], "level": 4}], "default": 3}
```

At run time a value that names a listed asset gets that asset's `scanned_level`. Those levels count as entries. For the levels no listed asset reaches, write `groups` of name fragments, so that a name not on the list can still be rated. A name that matches neither gets `default`.

Use `register` only for an input whose values are the listed assets themselves. Not for an owner, an account, a user or a record id.

### `keywords`: a path, a query, a body, a command

```json
{"kind": "keywords", "groups": [
  {"contains": ["public", "readme"], "level": 1},
  {"contains": ["tmp", "cache", "test"], "level": 2},
  {"contains": ["report", "notes"], "level": 3},
  {"contains": ["customer", "payroll", "contract"], "level": 4},
  {"contains": ["secret", "password", "token", ".env", "id_rsa"], "level": 5}], "default": 3}
```

The value is lowercased and checked for each fragment; the highest matching group wins. Write fragments in lower case, as plain text, never as regular expressions.

### `values`: a choice of five or more options

```json
{"kind": "values", "values": [
  {"value": "name", "level": 1}, {"value": "team", "level": 2},
  {"value": "email", "level": 3}, {"value": "salary", "level": 4},
  {"value": "national_id", "level": 5}], "default": 3}
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

| Tool and input | Answer |
|---|---|
| export_records `limit` | `ranges` on `value`: below 10 is 1, 10 to 100 is 2, 100 to 1000 is 3, 1000 to 10000 is 4, 10000 and up is 5 |
| list_invoices `from` and `to` | on both, `ranges` on `span_hours` with the other: below 24 is 1, 24 to 168 is 2, 168 to 720 is 3, 720 to 2160 is 4, 2160 and up is 5 |
| schedule_job `start` | `ranges` on `hour_of_day`: 10 to 16 is 1; 8 to 10 and 16 to 18 are 2; 7 to 8 and 18 to 20 are 3; 6 to 7 and 20 to 22 are 4; 0 to 6 and 22 to 24 are 5 |
| query_db `database`, assets listed at 1, 3 and 5 | `register`: groups test, sandbox at 2 and finance, payroll at 4 fill the missing levels; default 3 |
| read_object `key` | `keywords`, as in the example above |
| run_sql `query` | `keywords`: explain, show at 1; count at 2; select at 3; update, insert, alter at 4; drop, delete, truncate, grant at 5 |
| send_mail `to[]` | `email` |
| list_employees `fields[]`, twelve column names | `values`: name at 1, team at 2, email at 3, salary at 4, national_id at 5 |
| search_files, no `folder` given searches every folder | `register` on `folder` with `when_absent` 5 |
| transfer_funds `approved`, true or false | `null`: two values only |
| send_mail `subject` | `null`: text next to the body |
| get_ticket `ticket_id`, project chosen by another input | `null`: a record inside the chosen project |
| list_files `order_by` | `null`: presentation |
| add_member `user_id` | `null`: who the user is cannot be known from the id |

## Before you answer, check

1. Does every rule reach each level 1 to 5 with an entry of its own?
2. Does an ordinary call get 1, 2 or 3 from every rule?
3. Is every `null` one of the five cases above, with the case named in `reason`?

## Rules

1. Answer every input listed under Inputs exactly once, using the same path, including nested ones (`files[].path`). Answer none that the tool does not declare.
2. Every level and `default` is a whole number from 1 to 5.
3. `reason` is one short sentence: what decided the levels, or which case makes the answer `null`.
4. Never put a quotation mark inside any string value, and never put a backslash anywhere.

## Output

Output ONLY valid JSON, no prose, no code fences:

```json
{"tool_name": "<name>", "inputs": [
  {"path": "<input path>",
   "rule": {"kind": "ranges | register | keywords | values | email", "...": "fields of that kind"},
   "when_absent": null,
   "reason": "<one short sentence>"},
  {"path": "<input path>", "rule": null, "reason": "<which case>"}
]}
```

Some large tools are given in more than one batch, each with only its own inputs but the full tool description. Answer only the inputs present below.

Tool: `{tool_json}`

Inputs: `{inputs_json}`

Organization (may be empty): `{policy_json}`