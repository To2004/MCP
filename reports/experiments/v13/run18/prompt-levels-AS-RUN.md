<!-- sha256: 7bb96aa41bfa057710ddcbb01523222f5ea8c226a83462621e50a1cdd29d80d2 · source: docs/standards/tool-input-levels.md -->

# Rate the Inputs of One Tool

<tool>
{tool_json}
</tool>

<inputs>
{inputs_json}
</inputs>

<other_inputs>
{context_inputs_json}
</other_inputs>

<policy>
{policy_json}
</policy>

## The task

A gateway stands in front of the server that offers this tool. Every time an AI agent calls the tool, the gateway gives each argument a risk level from 1 to 5 and blocks or flags the riskiest calls. You write the rules it uses: for each input in `<inputs>`, a rule that turns the value an agent sends into a level, or no rule. A program applies the rules call by call, long after you wrote them, so a rule can only use what a value shows, the tool, and `<policy>`.

`<other_inputs>` are the tool's other inputs: read them to understand the tool, and answer only the inputs in `<inputs>`. `<policy>` is what the organization says about this tool and its assets, each asset with a level from 1 to 5 (`scanned_level`); it may be empty.

## The levels

| Level | Meaning |
|---|---|
| 1 | the safest realistic value |
| 2 | safe |
| 3 | ordinary |
| 4 | high: a sensitive target, a lot at once, outside working hours, or what the policy calls unusual |
| 5 | critical: what the policy prohibits or calls the heaviest case, credentials, bulk, or data leaving the organization |

A value typical of the normal workflow gets 1 to 3, unless it names data the policy rates higher. Where the policy speaks about an input, follow it; numbers and cut-offs it does not give are yours.

## For each input

1. **Say what it decides** (`effect`):
   - `which`: which asset is touched, or the account or owner it belongs to
   - `how_much`: how many items the call returns or changes: messages, rows, files, recipients
   - `who`: who receives something, is notified or gains access
   - `action`: what is done, chosen from five or more options
   - `when`: when it happens, or over what span of time
   - `carried`: what is written, sent or run: a body, a message, file content, a query, a search text
   - `none`: none of these, such as display, custom metadata, or a record inside an asset another input chose (an event id, an issue number)
2. **Say why** (`reason`), in one sentence: what decides the levels and where it comes from (the policy, the schema, or common knowledge), or why there is no rule.
3. **Write the rule, or `null`.** The answer is `null` when:
   - the effect is `none`;
   - the input sets a size inside one item that is read anyway (the first lines of a file), or excludes things. The number of items a call returns does get a rule;
   - it is a short label next to the main content (a title or a commit message, when the tool also has a body);
   - its level would need facts nobody has (who is behind an opaque user id);
   - it can take fewer than five values, counting the values its description lists.

   Every other input gets a rule. Each level 1, 2, 3, 4 and 5 must be reached by some realistic value; levels the program adds (below) count. Start with the safest values, the harmless ones (public, read-only, small, in working hours) at 1 and 2, so that no level is left empty. `default` is the level of a value that matches nothing. Such a value is ordinary, so `default` is 1, 2 or 3.
4. **Set `when_absent`** only when the policy or the normal workflow says that leaving the input out is unusual or risky, for example a search the policy wants scoped to one channel: then 4, or 5 for the heaviest case. Otherwise it is `null`, and an input with a default is rated at its default.

## Kinds of rule

### `ranges`: numbers, counts, lengths, times

A range matches when `min <= x < max`, and `null` is open. Write the ranges from the smallest number up, one range for each level 1 to 5, the first open at the bottom and the last open at the top. Keep them inside the input's `minimum` and `maximum`: a range no value can reach does not count. Four shapes, with the usual cut-offs; yours may differ:

```json
{"kind": "ranges", "measure": "value", "ranges": [
  {"min": null, "max": 10, "level": 1}, {"min": 10, "max": 50, "level": 2},
  {"min": 50, "max": 200, "level": 3}, {"min": 200, "max": 1000, "level": 4},
  {"min": 1000, "max": null, "level": 5}], "default": 3}

{"kind": "ranges", "measure": "span_hours", "with": "timeMax", "ranges": [
  {"min": null, "max": 24, "level": 1}, {"min": 24, "max": 168, "level": 2},
  {"min": 168, "max": 720, "level": 3}, {"min": 720, "max": 8760, "level": 4},
  {"min": 8760, "max": null, "level": 5}], "default": 3}

{"kind": "ranges", "measure": "hours_from_now", "ranges": [
  {"min": null, "max": -8760, "level": 5}, {"min": -8760, "max": -720, "level": 4},
  {"min": -720, "max": -168, "level": 3}, {"min": -168, "max": -24, "level": 2},
  {"min": -24, "max": null, "level": 1}], "default": 3}

{"kind": "ranges", "measure": "hour_of_day", "ranges": [
  {"min": null, "max": 7, "level": 5}, {"min": 7, "max": 9, "level": 3},
  {"min": 9, "max": 17, "level": 1}, {"min": 17, "max": 19, "level": 2},
  {"min": 19, "max": 22, "level": 4}, {"min": 22, "max": null, "level": 5}], "default": 3}
```

| `measure` | What is measured |
|---|---|
| `value` | the number itself |
| `length` | the number of items in a list, or of characters in a text |
| `span_hours` | hours between this date-time and the input named in `"with"`. Use it on both ends of a read window (an input with `window_with` names its other end); always give `"with"`. A day is 24 hours, a week 168, a month 720, a year 8760. When a call gives only one end, the program measures to now |
| `hour_of_day` | the hour, 0 to 24, as written in the value. Working hours get 1 and 2, night gets 5 |
| `hours_from_now` | hours from the call to the date-time, negative in the past. Use it for a single date that starts a read (since, after) when there is no end input: further back is higher |

**A read window**: an input with `window_with` is one end of a window. Rate the window's length: `span_hours`, with `"with"` naming the other end. Never `hours_from_now` for it.

### `register`: the value is an asset's own name or id

```json
{"kind": "register", "groups": [], "default": 3}
```

Use it when the values are names from the policy's asset lists: a repository, a channel, a calendar. The program looks the value up among all the organization's assets and gives that asset's `scanned_level`. `asset_levels` in `<policy>` lists the levels those assets reach and `name_words_needed_for` the levels none reaches: add groups of name words (`{"contains": [...], "level": 2}`) for those levels only. When a policy rule says this tool may not do something to an asset, or calls it the heaviest case, raise that asset: `"overrides": [{"asset": "...", "level": 5}]`.

When the assets are kinds of data (key material, payroll) and the value is a path or a text, use `keywords` instead: such values never contain the asset names.

### `keywords`: paths, queries, bodies, commands

```json
{"kind": "keywords", "groups": [
  {"contains": ["...", "..."], "level": 1}, {"contains": ["...", "..."], "level": 2},
  {"contains": ["...", "..."], "level": 3}, {"contains": ["...", "..."], "level": 4},
  {"contains": ["...", "..."], "level": 5}], "default": 3}
```

A group matches when the lowercased value contains one of its words at the start of a word, so `unblind` also matches `unblinding`. The highest matching group wins. Use words that appear in such values: folder and file names, terms in a query or a message. An asset's name (`customer-exports`) does not appear in a path; the words of its description do (`export`, `customer`). Rate what the text reaches and does: the data it names, and its operation (a read, a change, a deletion). Words the policy uses for an asset's data get that asset's level. Write one group for each level 1 to 5. The program also adds the credential words (password, token, secret, private key, `.env`, `id_rsa` and the like) at level 5, so your level-5 group is for what else is critical: what the policy prohibits, or the data of a level-5 asset.

### `values`: one of five or more options

```json
{"kind": "values", "values": [
  {"value": "...", "level": 1}, {"value": "...", "level": 2}, {"value": "...", "level": 3},
  {"value": "...", "level": 4}, {"value": "...", "level": 5}], "default": 3}
```

List only values the input can take, from its `enum` or its description. With fewer than five, the answer is `null`.

### `email`: an email address

`{"kind": "email"}`. The program fixes the levels: the organization's own domain 1, a partner domain 2, no readable domain 3, another organization 4, a personal mailbox or a domain the policy flags 5.

## Examples from other products

<examples>
<example>
HR system, `export_records.department`. The policy lists `finance-payroll` at 5, `engineering` at 3 and `canteen` at 1, and `name_words_needed_for` is `[2, 4]`. Effect `which`. Reason: the policy's departments. Rule: `register` with two groups, `handbook` at 2 and `legal` at 4.
</example>
<example>
Object storage, `get_object.key`, a file path. The policy's assets are `customer-exports` (4) and `signing-keys` (5): kinds of data, not file names. Effect `which`. Reason: the policy describes the data, so a path is rated by its words. Rule: `keywords`: `public` 1, `docs` 2, `reports` 3, `exports` and `customer` 4, `keys/` and `.p12` 5.
</example>
<example>
Video calls, `schedule_call.start`. Effect `when`. Reason: the hour of the call. Rule: `ranges` on `hour_of_day`: 10 to 16 is 1, 8 to 10 and 16 to 18 are 2, 18 to 21 is 3, 21 to 23 is 4, before 8 and after 23 are 5.
</example>
<example>
Analytics, `run_report.sql`. Effect `carried`. Reason: the operation and the tables it names. Rule: `keywords`: `select` 1, `join` 2, `insert` 3, `update` and `salary` 4, `delete`, `drop` and `grant` 5.
</example>
<example>
Forum, `create_post.title`, and the tool also has `body`. Effect `carried`. Reason: a label next to the body, which carries the content. Rule: `null`.
</example>
<example>
Ticketing, `get_ticket.ticket_id`, the project chosen by another input. Effect `none`. Reason: a record inside the chosen project. Rule: `null`.
</example>
</examples>

## Answer

Before you answer, check that:

- every rule has an entry for each level 1, 2, 3, 4 and 5, the safe levels included;
- each end of a read window uses `span_hours` with its other end;
- `keywords` hold words that appear in the values, not asset names.

Reply with one JSON object, `{"inputs": [...]}`, with one entry for each input in `<inputs>` under the same `path`, nested ones included (`files[].path`). Each entry has, in this order: `path`, `effect`, `reason`, `rule` (an object, or `null`), and `when_absent` (a level, or `null`). Every level and `default` is a whole number from 1 to 5.

An input that carries `your_last_rule` and `problems_last_time` was answered before and failed the program's checks: fix each problem listed and keep the rest of that rule.