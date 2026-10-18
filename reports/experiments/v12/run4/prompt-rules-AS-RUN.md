<!-- sha256: a36bd145cbdcdf8551caeca373581fe2e6a2910271de5de126903d6f41f9685f · source: docs/standards/tool-input-rules.md -->

# Tool Input Rules

The v12 stage 2 prompt. Stage 1 ([tool-input-importance.md](tool-input-importance.md)) kept only the inputs of this tool that can change how risky a call is. For each of them, write one rule that a program can apply at run time, with no model involved, to turn the input's actual value into a level from 1 to 5. At run time the call's input level is the highest level among its inputs.

## What you are given

- the tool name and description;
- the inputs to write rules for, with their description and schema facts (type, format, enum values, minimum, maximum, whether it is required, default), and the reason stage 1 kept each one (`why_important`);
- the tool's other inputs, name and description only, for context. Stage 1 judged them not important. Write no rules for them;
- optionally, the organization's policy rows for this tool: a short org context, the normal workflow, the assets this tool can reach with a description and a `scanned_level` from 1 to 5, special-value rules and baseline rows. Any part may be empty.

## The five levels

Level 3 is the neutral point: the value a normal call passes. Lower levels are safer than normal, higher levels are riskier than normal.

| Level | Meaning |
|---|---|
| 1 | No concern. Smaller or safer than a normal call: a tiny count, a public or already published target. |
| 2 | Low. An ordinary value on the safe side. |
| 3 | Normal. What an ordinary call in the tool's normal workflow passes. |
| 4 | High. Notable: a sensitive target, a lot at once, outside normal hours, outside the usual audience, a value the policy calls unusual. |
| 5 | Critical. Serious or hard to undo: a restricted or credential-bearing target, a destination outside the organization, a bulk change, a value the policy prohibits. |

The same scale is used for the organization's assets (`scanned_level`), so a rule on a path or a query should agree with the levels of the assets it can reach.

## Kinds of input

Give each input one `classification`:

- `RANGE`: a quantity, a size, a count, a date, a time, or a window.
- `ASSET`: picks what the call touches (a repository, a path, a channel, an account, a recipient, an environment).
- `CONTENT`: what is written, sent or executed (a file body, a message, a query).
- `MODE`: a switch or an action that changes what the call does or who can see it.

## Rule kinds

Each input gets exactly one rule. A rule always ends in a level from 1 to 5.

### `ranges`: a number, a length, or a time

```json
{"kind": "ranges", "measure": "value", "ranges": [
  {"min": null, "max": 50, "level": 2},
  {"min": 50, "max": 500, "level": 3},
  {"min": 500, "max": 5000, "level": 4},
  {"min": 5000, "max": null, "level": 5}], "default": 3}
```

`measure` says what is computed from the value before the ranges are applied:

| measure | computed from the value |
|---|---|
| `value` | the number itself |
| `length` | the number of items in a list, or of characters in a string |
| `hour_of_day` | the hour of a date-time, 0 to 24, in the time zone written in the value |
| `weekday` | the day of a date-time, 0 for Monday to 6 for Sunday |
| `span_hours` | the hours between this date-time and the sibling input named in `with` |
| `hours_from_now` | hours from the moment of the call to this date-time; negative is the past |

A range matches when `min <= x < max`; `null` means open. The first matching range wins; if none matches, `default` applies. For `span_hours`, add `"with": "<sibling input path>"`.

### `register`: a value that names one of the organization's assets

```json
{"kind": "register", "default": 5}
```

At run time the value is matched against the assets this tool can reach, and the level is that asset's `scanned_level`. Write no levels of your own for listed assets. `default` applies when the value names no listed asset: an unknown target is not known to be safe, so use the highest `scanned_level` among the assets this tool can reach, unless the policy says how unlisted targets are treated. Use this kind only when the policy lists assets for this tool.

### `keywords`: a path, a name, a query or a text, judged by what it contains

```json
{"kind": "keywords", "groups": [
  {"contains": ["secret", "password", "credential", "id_rsa", ".env", "token"], "level": 5},
  {"contains": ["payroll", "salary", "medical", "contract"], "level": 4},
  {"contains": ["tmp", "scratch", "public", "readme"], "level": 2}], "default": 3}
```

At run time the value is lowercased and checked for each fragment. The highest level among the matching groups wins; if none matches, `default` applies. Write fragments in lower case, as plain text. Never use regular expressions or escape characters. Use names from the policy (asset names, project names) as fragments where they appear in values.

### `values`: a fixed choice or an on and off switch

```json
{"kind": "values", "values": [
  {"value": "production", "level": 5},
  {"value": "staging", "level": 3},
  {"value": "dev", "level": 2}], "default": 3}
```

At run time the value is compared with each listed value, ignoring case. A boolean is written as `true` or `false`. If none matches, `default` applies. List every enum value the schema declares.

### `domain`: an email address, a user handle or a URL

```json
{"kind": "domain", "internal": 3, "external": 5}
```

At run time the value's domain is compared with the organization's own domains. A value whose domain is not the organization's own gets `external`.

## Absent inputs

Every rule also has `when_absent`: the level when the caller leaves the input out, or `null` when leaving it out adds nothing. Leaving an input out can be the risky case: a search with no channel filter searches every channel, and a list with no limit may return everything. Give `when_absent` a level in exactly those cases.

## Where the levels come from, in this order

1. **The policy**, when it speaks to the input: a baseline row (its normal values are level 3, its unusual values level 4 or 5), a special-value rule (level 5 unless it says otherwise), or the listed assets the value reaches. `source: policy`, or `source: register` for a `register` rule.
2. **The schema**, when it states bounds: anchor the ranges to them. `source: schema`.
3. **Your own judgment** about the tool and common practice, when neither of the above covers the input. Approximate numbers are fine: the direction and rough size matter more than the exact cut. Prefer a wide level 3 range over a false cutoff. `source: inferred`.

The riskiest values are not always the largest. A time of day is the clearest case: ordinary working hours are level 3, early morning and evening level 4, late night level 5. If the policy states the organization's working hours, use them.

## Rules

1. Write exactly one rule for every input listed under Inputs to write rules for, using the same path, and none for any other input.
2. Every level and every `default` is a whole number from 1 to 5.
3. Keep rules short: three to five ranges, groups or values is usually enough.
4. For a list item (a path ending in `[]`, or with `[]` inside it), the rule is applied to every item and the highest level counts. To judge how many items there are, put a `length` rule on the list itself.
5. `reason` is one short sentence naming what decided the levels. It is never empty.
6. Never put a quotation mark inside any string value, and never put a backslash anywhere. Paraphrase instead of quoting.

## Examples

These show the shape only. Judge the real tool below from its own text.

| Input | Rule |
|---|---|
| export_records `limit`, 1 to 10000 | `ranges` on `value`: below 50 is 2, 50 to 500 is 3, 500 to 5000 is 4, above is 5. `schema` |
| export_records `database_id`, policy lists assets | `register`, default the highest scanned level among its assets. `register` |
| move_file `destination` | `keywords`: secret, password, credential, ssh, id_rsa is 5; payroll, hr, legal is 4; tmp, scratch is 2; default 3. `inferred` |
| schedule_job `start`, date-time | `ranges` on `hour_of_day`: 0 to 6 is 5, 6 to 8 is 4, 8 to 18 is 3, 18 to 22 is 4, 22 to 24 is 5. `inferred` |
| list_events `time_min` with `time_max` | `ranges` on `span_hours` with time_max: below 48 is 2, 48 to 336 is 3, 336 to 2160 is 4, above is 5. `inferred` |
| create_repo `private`, boolean | `values`: true is 3, false is 5 when the policy treats public copies as serious. `policy` |
| send_invite `attendees[].email` | `domain`: internal 3, external 5. `policy` |
| search `channel_filter`, optional | `register`, default 5, `when_absent` 5: no filter searches everything. `policy` |
| post_message `text` | `keywords`: password, token, secret is 5; default 3. `inferred` |

## Output

Output ONLY valid JSON, no prose, no code fences:

```json
{"tool_name": "<name>", "arguments": [
  {"path": "<input path>",
   "classification": "RANGE | ASSET | CONTENT | MODE",
   "rule": {"kind": "ranges | register | keywords | values | domain", "...": "fields of that kind"},
   "when_absent": null,
   "source": "policy | register | schema | inferred",
   "reason": "<one short sentence>",
   "confidence": 0.0}
]}
```

Some tools are given in more than one batch. Write rules only for the inputs present under Inputs to write rules for below.

Tool: `{tool_json}`

Inputs to write rules for: `{inputs_json}`

Other inputs of this tool, for context only: `{context_inputs_json}`

Policy for this tool (may be empty): `{policy_json}`