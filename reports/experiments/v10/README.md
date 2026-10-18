# v10 — Static input typing

**Status: deprioritized.** The dynamic layer is currently built on the static
scanner's output directly, not on this input-typing pass. Kept for reference;
not actively being developed.

Every generation up to v9 scored a **(tool, asset)** cell. v10 asks a different
question, one generation below: for each of a tool's **input parameters**, what
kind of value is it, and along which axis can it vary? No risk, no severity, no
bands — a typing pass whose output is what a runtime monitor would otherwise
have to learn by watching traffic.

The motivating case: a call's arguments carry meaning the cell cannot express.
An account id picks one entity out of a population the caller is only partly
entitled to. A meeting length has an ordinary window. An attendee list has a
length. A SQL string without a `LIMIT` reaches every row. A commit message means
nothing at all. Typing these statically is what lets the dynamic layer compare a
value against something, rather than discover the shape of each input from logs.

## The prompt

The prompt changes from run to run, so **each run folder holds the prompt that
produced it** (`runN/prompt-AS-RUN.md`), written by the runner at the start of
the run and stamped with its `sha256`; each result JSON repeats that digest.
There is deliberately no copy at the top level — a single shared copy goes stale
the moment the prompt changes. The live prompt is
`docs/standards/input-typing.md`, sent verbatim with `{tool_json}` replaced by
one tool's definition (the markdown-is-the-prompt convention of
`docs/standards/parameter-scoring.md`).

Two design decisions are load-bearing, both about **not** handing the model the
answer:

- **No taxonomy.** The prompt never lists parameter types to choose from. A
  fixed list would be a taxonomy of the servers we happened to look at, and
  picking from a menu is an easier task than reading the tool. The prompt asks
  for structural facts — what population the value is drawn from, whether it has
  a size or an order, where its meaning changes, whether it is prose — and lets
  the model name the `kind` itself in open vocabulary.
- **No worked examples from the corpus.** Earlier drafts illustrated the fields
  with GitHub and Slack parameters; those are the servers under test, so the
  examples were leakage. They were removed before run 1.

The declared JSON type is deliberately distrusted: across these catalogs 140 of
193 parameters are declared `string` (in `create_or_update_file`, `owner`,
`repo`, `path`, `content`, `message`, `branch` and `sha` all are), only 14
`enum`s are declared, and `pull_number`/`issue_number` are declared `number`
while being identifiers. So the tool JSON carries the **full input schema** —
`enum`, `minimum`, `maximum`, `format` — which `ToolSpec.parameters()` drops.

## Runs

Both: Qwen2.5:32b via local Ollama, greedy (`temperature=0`, `seed=0`), one
rtx_4090, `scripts/derive_input_types.sbatch`. Sources — github and slack from
the live captures in `reports/live_run/*_toollist.json`, calendar from
`static_scoring.registry`.

| | run 1 (20597788) | run 2 (20598630) | run 3 (20622342) |
|---|---|---|---|
| prompt | 128 lines, seven questions | 144 lines | **65 lines, three questions** |
| tools typed | 53 | 53 | 53 |
| JSON failures | 0 | 0 | 0 |
| inputs described vs declared | 221 / 202 — **19 fabricated** | 202 / 202 | 202 / 202 |
| fields per input | up to 19 | up to 19 | at most 8, usually 0–4 |
| wall clock | ~11 min | ~11 min | **~3.5 min** |

### What run 3 changed — the current shape

Runs 1 and 2 answered too much. The question the dynamic layer actually needs is
narrower, so run 3's prompt asks three things and nothing else:

1. **Does the value have a size or a place on a scale** — a count, a length, an
   amount of money, a duration, a time of day, a page size, a row limit? Then
   what it measures, in what unit, and the ranges that count as **low, medium
   and high** for that input.
2. **Does it pick one thing out of many** — an id, an account, a repository, a
   country — where the set is *large* and a caller is entitled to part of it?
   Then `check_policy: true`, the handoff telling the run-time layer to look this
   input up in the organisation's policy. A handful of fixed options is not this.
3. **Anything else** — prose, an opaque token, a small fixed choice — gets its
   name and nothing more.

Result on the three servers: **41 inputs with a scale, 45 needing a policy
lookup, 116 needing nothing.** `INPUT_TYPES.md` renders it as one table per
server, with ✓ in the policy column.

### What run 2 changed

Prompt (see [`prompts/`](prompts/) for run 1's text, reconstructed):

1. *"Describe only the parameters the tool actually declares… a tool with no
   declared inputs is a fact about the tool, not a gap for you to fill."*
2. *"Name the input, not the answer you gave: a `kind` must never be the name of
   one of the fields below."*
3. An expression the service interprets to select or filter data is **not**
   prose — it has a reach, so record what bounds it.
4. `limits` only for values with an order; named options have no min or max.
5. A timestamp marks a position and `measures` nothing; a list measures its
   length.

Runner:

- Tools declaring no properties are **never sent to the model** (recorded as
  `no_declared_schema`). This closes the fabrication path structurally rather
  than by instruction — run 1's calendar invented `calendar_id`, `start_date`,
  `end_date` and `event_type` for `list_events`, which declares nothing.
- Per-server dedupe on `(name, description, type)`: a parameter is typed once,
  in the first tool that declares it, and reused elsewhere with `reused: true`.
  The tool still ships its whole schema plus a `type_these` list, so `read_with`
  can still see partner parameters.

## What the output looks like

```
repo     of: repositories owned by the specified owner
         size: varies widely from one to thousands per user/organization
         caller_reaches: only the ones it is entitled to
         listable_via: GET /repos/{owner}
per_page limits {1, 100} · edges [30 → default, 100 → maximum allowed]
q        kind: query · edges [absent → no bound]
content  prose: true — and nothing else
sort     fixed_choice — options not listed
```

`listable_via` was not asked for by name and is the most useful field the model
volunteered: it names the call a monitor can make to check membership at run
time.

## Known defects (runs 1-2, on the older prompt)

- **Reuse leaks context.** `per_page` was typed inside `list_issues`, so its
  unit reads `"issues per page"` — and that answer is reused verbatim in
  `search_code`, `search_issues` and `search_users`, where it counts code
  results and users. Consistency bought a small wrongness.
- **`fixed_choice` became a `kind` 25 times** (25 of the 29 field-name labels).
  The prompt sanctions the word for the `population` field, and the "never use a
  field name as a kind" rule does not cover it.
- **18 same-name parameters still disagree**, all with differing descriptions
  across tools, so dedupe cannot merge them: `owner` is `account` in one tool and
  `repository_owner` in another; `slack.limit` has four labels. Only a
  normalisation pass over the finished output resolves these, which is what the
  prompt's note on `kind` being open vocabulary anticipates.
- **Calendar is thin, and that is the registry's fault.** 9 of its 11 tools
  declare no input schema at all, so only 9 parameters exist to type against
  github's 130 and slack's 63.

## Layout

```
runN/
├── prompt-AS-RUN.md               the prompt this run sent, with its sha256
├── {github,slack,calendar}.json   per-tool results, each stamped with that sha
├── INPUT_TYPES.md                 the readable table
└── logs/                          slurm + per-server logs
scripts-AS-RUN/                    runner, sbatch and summariser as first run
```

Run 1's `prompt-AS-RUN.md` is **reconstructed** (its text was not captured at the
time, so the run-2 file has its edits inverted); run 3's was copied by hand after
the fact. From run 4 on the runner writes it itself, before the first tool.

## Reproducing

```
sbatch scripts/derive_input_types.sbatch     # ~3.5 min on one rtx_4090
```

The job picks the next free `runN` folder, pins it for all three servers, and
summarises into it. To re-render an existing run:
`.venv/bin/python scripts/summarize_input_types.py reports/experiments/v10/run3`.
