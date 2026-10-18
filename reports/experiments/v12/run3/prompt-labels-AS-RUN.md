<!-- sha256: 98147418715f0ef344f1f253a6691798d523228cb99af49677f39a6b6638db5f · source: docs/standards/tool-input-labels.md -->

# Tool Input Labels

The v12 stage 2 prompt. It runs only on the inputs that stage 1 ([tool-input-importance.md](tool-input-importance.md)) judged to matter; the unimportant ones were dropped there. For each of them, decide how its value should be interpreted, then say which values make a call more or less risky, as low, medium and high bands. The tool itself is the main evidence. The organization's policy, when one is given, comes first for the bands.

## What you are given

You are analyzing one MCP tool. You get:

- the tool name and description;
- the inputs to analyze, with their description and schema facts (type, format, enum values, minimum, maximum, whether it is required, default). Stage 1 judged each of them important and gave a reason, shown as `why_important`. Take that as given;
- the tool's other inputs, name and description only, for context. Stage 1 judged them not important. Do not describe them;
- optionally, the organization's policy rows for this tool: a short org context, the normal workflow, the assets this tool can reach (with a description of why each matters), special-value rules (Table 3) and baseline rows (Table 4). Any part may be empty.

Use the whole tool as context. The purpose of the tool and the sibling inputs decide what an ambiguous input means.

## Part 1: the label

Give every leaf input exactly one label.

### RANGE

The value has a meaningful order, magnitude or extent, so a larger, smaller or later value means more or less of something: counts, limits, amounts, sizes, durations, time windows, percentages, depths, dates and times of day.

A number that only names something is NOT a range. An account id, an issue number and a page cursor are not ranges.

Subtype, one of: `count | amount | size | percentage | duration | temporal | limit | other`.

### ASSET

The value selects, names or locates something, so which value was passed decides how much the call matters.

The type does not matter. A string, an integer, an enum, a path and a UUID can all be ASSET.

Subtype, one of:

- `container`: a handle for a bounded thing that holds other things (a repository, a channel, a calendar, a database, a project, a bucket).
- `content_locator`: a value that points at content by its location or name (a file path, a folder, a document title, a table name, a URL, a search scope).
- `principal`: a person or account (a user, an owner, an attendee, an email address, a tenant).
- `category`: a named class that changes the context of the call (an environment such as production, a country, a role, a data classification).

Also return `asset_concept`: a short phrase for what the value stands for.

### IGNORE

The value neither has a meaningful magnitude nor selects something whose identity matters: free text meant for a person or a search, descriptions, comments, titles, output formats, sort order, ordinary on/off switches, and small sets of operating modes that change how the call behaves but not which thing it acts on.

### UNKNOWN

The schema and descriptions do not give enough evidence to choose. Prefer UNKNOWN over a guess.

## Part 2: the risk bands (RANGE and ASSET only)

For every RANGE and ASSET input, say which values make the call more or less risky. Write one to three bands. Each band has a level (`low`, `medium` or `high`), a short description of the values that fall in it, and, for RANGE, optional numeric limits in a stated unit.

A band describes how much THIS VALUE adds to the risk of the call, not how risky the tool is overall. A delete tool's id input is not high just because the tool deletes. The same tool can be low risk with one value and high risk with another, and that difference is what you are describing.

### Where the bands come from, in this order

1. **The policy, when it speaks to this input.**
   - A baseline row for the input: the normal values are `low`, the unusual values are `high`, and the space between is `medium`.
   - A special-value rule: the values it names are `high`.
   - The assets this tool can reach: place each kind of value on the asset it would reach, and use that asset's description to say how much it matters. An asset the policy calls public or already published is `low`. One that identifies real people, cannot be undone, or controls other systems is `high`.
   - Set `bands_source` to `policy`.
2. **The schema, when it states bounds.** Anchor the bands to them (for example, the top part of a declared maximum is higher). Set `bands_source` to `schema` when the schema alone decided it.
3. **Your own judgment about the tool.** When neither of the above covers the input, use the tool's purpose, the sibling inputs and common practice to give the general direction. It is fine if it is not exactly right. Set `bands_source` to `inferred`.

Rules for the inferred case:

- Give the direction and a rough size. Approximate numbers are allowed, but never imply precision: prefer a wide `medium` band to a false cutoff.
- Say what normal use looks like for this kind of tool, then place the unusual values at the risky end.
- The risky region does not have to be the largest values. Some inputs are risky when too small, or risky when outside a normal window. A time of day is the clearest case: ordinary working hours are `low`, early morning and evening edges are `medium`, and late night, weekends and holidays are `high`. If the policy gives the organization's hours, use them instead of the general assumption.
- For an unbounded count or size, think about what one ordinary call would pass, and what would mean someone is reading or changing a lot at once.

### What each level means

| Level | Meaning |
|---|---|
| `low` | An ordinary value for this kind of call. Nothing about it needs a second look. |
| `medium` | Unusual enough to note, or the value is ambiguous. A wide band when you cannot tell. |
| `high` | A value that would justify a second look before the call runs: a large reach, an out-of-pattern time, a sensitive asset, a value outside the org, or an irreversible target. |

## Rules

1. Decide from meaning, not from the JSON type. A numeric identifier is ASSET. A numeric limit is RANGE. A string holding a date window is RANGE. A string holding a country is ASSET.
2. Use the tool as context. The same input name can mean different things in different tools.
3. A path is ASSET with subtype `content_locator`, never IGNORE, because which file was named decides what the call touches. Bands for a path describe kinds of location: a folder that holds credentials, personal data or other systems' configuration is `high`; a public or generated file is `low`.
4. Free text that a person reads or a search engine matches (a query, a message body, a title, a description) is IGNORE and gets no bands.
5. Being categorical does not make an input ASSET. A format, a sort order or a merge method is IGNORE. An environment, a country or a role is ASSET, because choosing a different value changes the context the call acts in.
6. A small enum is not automatically IGNORE. Ask whether choosing another option changes WHICH thing or WHICH context the call acts on (ASSET) or only HOW it behaves (IGNORE).
7. A pagination cursor that the caller copies from an earlier reply is IGNORE. A page size is RANGE with subtype `limit`; a page number is RANGE with subtype `count`.
8. An input that only means something together with a sibling is still labeled on its own, but its bands may use the sibling. If a baseline row covers several inputs together, say so in `reason` and give the same bands to each of them.
9. Do not classify an array itself. Label each leaf, using a dotted path with `[]` for list items (`files[].path`). If the length of an array matters, also label the array as RANGE with subtype `count`.
10. If you hesitate between two labels, choose UNKNOWN, and say in `reason` which two.
11. Return `range` (stated bounds) only from the schema or the description. Bands may be approximate; bounds may not be invented.
12. `reason` is one short sentence naming the fact that decided the label and the bands. It is never empty.
13. Never put a quotation mark inside any string value. Paraphrase instead of quoting.

## Examples

These show the reasoning only. Judge the real tool below from its own text.

| Input | Label | Bands |
|---|---|---|
| export_records `limit`, integer, 1 to 10000 (no policy) | RANGE, limit | low: up to about 100; medium: 100 to about 1000; high: above about 1000, since it moves a lot of records at once. `schema`, `inferred` numbers. |
| export_records `database_id` (policy lists a payroll database as a restricted asset and a test database as public) | ASSET, container | high: the payroll database; low: the test database; medium: any database the policy does not list. `policy`. |
| schedule_job `start_hour`, integer 0 to 23 (no policy) | RANGE, temporal | low: 9 to 18, usual working hours; medium: 7 to 9 and 18 to 22; high: 22 to 7, when nobody expects activity. `inferred` |
| move_file `destination` (no policy) | ASSET, content_locator | high: folders holding credentials, keys, personal or financial records, or another system's configuration; medium: shared folders with many readers; low: a personal scratch or temporary folder. `inferred` |
| deploy `environment`, enum dev, staging, production | ASSET, category | low: dev; medium: staging; high: production. `inferred` |
| export_records `format`, enum csv or json | IGNORE | none |
| export_records `query`, string | IGNORE | none |

## Output

Output ONLY valid JSON, no prose, no code fences:

```json
{"tool_name": "<name>", "arguments": [
  {"path": "<input path>",
   "classification": "RANGE | ASSET | IGNORE | UNKNOWN",
   "subtype": "<subtype or null>",
   "range": {"minimum": null, "maximum": null, "unit": null},
   "asset_concept": "<what the value stands for, or null>",
   "bands": [
     {"level": "low | medium | high",
      "when": "<which values fall here, in one short phrase>",
      "min": null,
      "max": null}
   ],
   "bands_source": "policy | schema | inferred | null",
   "reason": "<one short sentence>",
   "confidence": 0.0}
]}
```

- `range` holds stated bounds only, and only for RANGE.
- `bands` is empty for IGNORE and UNKNOWN. For RANGE, `min` and `max` are in the unit of the input and may be null when the band is described in words. For ASSET they are always null.
- `asset_concept` is filled only for ASSET.

Describe every input listed under Inputs to analyze below, including nested ones, and none that is not listed.

Some tools are given in more than one batch. Describe only the inputs present under Inputs to analyze below.

Tool: `{tool_json}`

Inputs to analyze: `{inputs_json}`

Other inputs of this tool, for context only: `{context_inputs_json}`

Policy for this tool (may be empty): `{policy_json}`