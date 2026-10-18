# v11 — a stacked-feature ledger for every tool input

Every generation up to v10 gave one argument one label: v1-v9 scored a
**(tool, asset)** cell; v10 sorted each declared input into exactly one of
`RANGE` / `POLICY` / `IGNORE` / `UNKNOWN`. v11 asks the same underlying
question — *how should this input's value be interpreted later?* — but stops
forcing a single label. An argument can be several true things at once: an
`attendees[]` array is a count (its length) stacked on top of a population
(each attendee identifies someone), and today's one-label scheme can only
capture one of those, not both.

The goal, unchanged from v10's own founding rule, is to stay **tool-
independent**: the scanner should never need to know it is looking at
`send_money`, `delete_file`, or `book_flight`. It only asks what properties
of an input's value could make one instance of it more significant than
another — from the schema and description alone, never from the argument's
name.

## Why one label wasn't enough

Reading v10's own run5 output surfaced a concrete bug: `issue_number` came
back `POLICY` in `add_issue_comment` but `RANGE`/count in `get_issue` — the
same parameter, contradictory answers, because each tool is classified in
isolation. Fixing that with a cross-tool consistency pass is one motivation
for v11. The bigger one: some inputs simply don't fit any single class well.
Calendar's `modificationScope: thisEventOnly|all` looks like a small fixed
choice (`IGNORE`-shaped), but its real job is to multiply *another*
argument's blast radius — no existing class says that. `start` and `end`
only mean "how long" when read together; neither argument alone can carry
that fact under a one-argument-at-a-time scheme.

No ready-made taxonomy for this exists in the literature (checked: API-
fuzzing research classifies parameters by structural JSON type plus
regex/format sniffing, not by security-relevant semantics; LLM tool-calling
security surveys describe the risk of bad parameters without offering a
feature list). What follows is a synthesis of JSON Schema's own structural
keywords, general taint-analysis thinking, and UEBA / insider-threat
anomaly-detection feature engineering — not a citation.

## The schema: four layers per tool

### A. Structural facts (computed from the schema, never asked of the model)

- `cardinality` — `scalar` or `array`, with `min_items`/`max_items`/
  `unique_items` when declared. An array's own length is always a magnitude
  fact, independent of what its items are.
- `domain` — `closed` (`enum`/`const`/boolean) or `open` (free string or
  number).
- `declared_bounds` — `minimum`/`maximum`/`minLength`/`maxLength`/`pattern`/
  `format`, when the schema states them. A fact, not a guess — same
  discipline as v10's `bounds_source: "schema"`.
- `required`, `has_default`.

These come free from `input_schema` and are handed to the model as given
context, the same way v10 already passes the full schema instead of the
type-stripped `ToolSpec.parameters()` view.

### B. Reasoned feature flags, one argument at a time

Independent flags instead of one exclusive class:

| flag | question |
|---|---|
| `orderable` | does comparing two values mean more / larger / later? |
| `selects_population` | does the value pick one entity out of a set the caller only partly owns? (today's `POLICY`) |
| `expands_reach` | could this value make the call touch more than one thing, **regardless of whether it's numerically large**? A boolean `include_all: true` expands reach with no magnitude at all — a different axis from `orderable`, not a special case of it. |
| `composes_new_content` / `references_existing` | is the caller inventing this value, or pointing at something that already exists? |
| `provenance` | `caller_composed` \| `caller_copied` \| `system_opaque` — where would a normal caller get this value from? Separates ordinary free text from an opaque cursor/token/hash; both look like `IGNORE` today, for different reasons. |
| `commits_change` | does supplying this value participate in a create/update/delete, versus a pure read? |
| `scope_multiplier` | does this value change how broadly *another* argument's effect applies, without naming a target itself? |

**Deliberately not attempted:** a taint-sink feature ("does this value flow
into a shell/SQL/filesystem/URL sink"). That depends on what the *tool* does
with the value, not on the argument's own schema — the schema alone
under-determines it. Documented as a known limit, not faked.

### C. Dynamic-hook flags — what's worth tracking later, never computed here

Informed by UEBA / insider-threat feature engineering (rarity, entropy /
concentration, temporal pattern are standard behavioral-anomaly features in
that literature), but v11 stays **static**: it only flags which signal would
be *worth* tracking for a given argument. No corpus is read in this pass —
computing the signal itself is runtime work, exactly like v10 already treats
`bounds_source: "none"` as "no bounds yet; traffic should learn them."

- `track_rarity` — worth comparing this value against how often it's been
  seen before. Meaningful mainly when `selects_population` holds over a
  large, open domain; meaningless for a two-value boolean.
- `track_concentration` — worth checking how many *distinct callers*
  normally use this exact value. A value normally shared broadly, suddenly
  used by only one caller, is a different signal than a value only one
  caller has ever used — the insider-threat literature's "high volume, low
  entropy" framing, applied to a single argument.
- `track_temporal_pattern` — worth comparing the call's time-of-day /
  day-of-week against the caller's own baseline. More meaningful for
  `commits_change: true` arguments than for read filters.
- `track_pairing` — this argument's real meaning only emerges jointly with a
  named sibling; lists which one(s) (see the composite pass below).

### D. Cross-argument composites — per tool, not per argument

One extra question per tool: which pairs or groups of its arguments only
mean something *together*? None of v10, `param_scoring`, or `breadth.py`
look at sibling arguments jointly today — every existing scheme scores one
argument at a time. Known real cases already visible in the captured
catalogs: `start` + `end` (github, calendar) → duration; `page` + `per_page`
(github) → total rows touched; an absent filter alongside a high `limit` →
effective reach. Output shape: `composites: [{"args": [...], "meaning": str,
"note": str}]`.

## Cross-tool consistency (folded in, not bolted on)

The same disagreement problem found in v10 (`issue_number`, `milestone`)
will recur for the new flags too, so a reconcile pass is part of v11 from
the start: group arguments by leaf name per server, call the model only
where a flag actually disagrees across tools, retry once on a malformed
reply, and allow an explicit "same name, different concept — don't merge"
answer rather than forcing one. This mirrors two patterns already used
elsewhere in this codebase — `src/mcp_security/scanner/breadth.py`'s
all-or-nothing retry, and `src/mcp_security/review/judge.py`'s
audit-against-cited-evidence shape (not `static_scoring/pipeline.py`'s
blind-proposer-then-blind-judge pattern, which was already pulled from that
module's own live path for causing instability).

## Registry: the full captured surface, not just three servers

v10 covered github (26 tools), calendar (13), slack (16). A fourth real,
live-captured catalog already exists on disk but was never wired into
`scripts/mcp_catalogs.py`: **`finance_tools`**, 17 tools with real declared
`input_schema` (`reports/experiments/static_scanner/inputs/
finance_tools.json` — e.g. `get_ticker_data.ticker: {"type": "string"}`).
v11 covers all four: **72 tools** total. `reports/live_run/
MCP_INVENTORY.md` is missing a `finance_tools` section despite it being
captured — a gap this closes, not a new one it introduces.

## Layout (once runs exist)

```
runN/
├── prompt-AS-RUN.md                    the prompt this run sent, with its sha256
├── {github,slack,calendar,finance_tools}.json   per-tool feature ledger, stamped with that sha
├── {server}.reconciliation.json        cross-tool disagreement resolutions
├── {server}.md                         the readable per-tool table
└── logs/                               slurm + per-server logs
```

## Pilot results (run4, calendar, 2026-08-30)

Ran end-to-end against calendar's real 13-tool catalog. Iterated through
four attempts before landing here — worth recording what each one found,
since the failures were as informative as the successes:

| run | change | result |
|---|---|---|
| run1 | first attempt, 16384 context | 12/13 succeeded; `create-event` (31 args) failed both attempts — reply truncated |
| run2 | context bumped to 32768 | **regression**: `list-calendars`, a 1-argument tool, went from ~49s to 4.5min, then `list-events` hit a full 20-minute timeout. Raising context on a single rtx_4090 pushed the KV cache past VRAM, forcing Ollama into silent CPU offload — cancelled |
| run2 (retry) | reverted to 16384; dropped the redundant raw `input_schema` from the prompt (structural facts already carry every schema-derived fact, including each argument's `description` — added for this) | **13/13 succeeded**, but a manual read found two real quality problems: 92% of arguments (169/184) had a blank `reason`, and `visibility` (a small closed enum) was wrongly tagged `selects_population: true` |
| run3 | added prompt rules distinguishing closed-enum "modes" from `selects_population`, and requiring a non-empty `reason`; made empty-`reason` a hard validation failure | fixed both quality problems everywhere it succeeded (0/106 empty reasons, `visibility` now correctly `false`) — but the longer prompt template plus the stricter gate cost completion: only 11/13, and `create-events`/`update-event` (both with large nested arrays) failed |
| run4 | kept the quality-fixing prompt rules; **reverted the hard reason-gate** to a per-tool recorded warning instead (`empty_reasons: [...]`) — a blank reason is a quality signal, not a shape violation, and gating the whole tool's answer on it discarded otherwise-good answers | 11/13, 0/106 empty reasons. `create-events` and `update-event` still fail — confirmed (by re-running with only the validation logic changed and watching the *same* two tools fail at the *same* point) that this is a genuine prompt-size/context-budget problem reintroduced by the longer prompt rules, not the reason-gate |

**Known limitation, not yet fixed**: the two largest schemas
(`create-events`' `events[]` array of full nested event objects, and
`update-event`'s 28+ top-level arguments) sometimes exceed what fits
reliably in a 16384-token context once the reply must carry a 14-field
vector per argument. Candidate fixes for next iteration: a careful,
incremental context increase with slowdown monitoring (32768 caused VRAM
pressure and CPU offload; something between 16384 and that ceiling may work,
but must be verified, not assumed), or splitting a large tool's arguments
across more than one LLM call rather than widening the window.

**What worked well, confirmed on real output:**
- Cross-argument composites (layer D) correctly found `start`+`end` →
  duration on every tool that has them (`create-event`, `list-events`,
  `get-freebusy`), and one not anticipated in the design:
  `attendees[].email` + `attendees[].optional` → "defines whether an
  attendee is optional or mandatory."
- `visibility`, once the prompt rule was added, correctly resolved to
  `selects_population: false` with a stated reason ("closed domain and
  optional nature imply caller_composed content") instead of the earlier
  wrong `true`.
- Reusing `mcp_security.atomic_ops.toollist_rules.classify_from_toollist`
  for tool context worked once tool names were normalized from calendar's
  `kebab-case` (`create-event`) to the rule set's expected `snake_case`
  (`create_event`) — the rules matched zero calendar tools before this fix,
  confirmed by testing. `respond-to-event` and `manage-accounts` still get
  no atomic-op tag at all — a real, honest gap in the existing rule set's
  verb coverage (no rule for "respond" or "manage"), not something this
  pilot patched.

Reference output: `run4/calendar.json` (11 tools, `empty_reasons` field per
tool for auditability), `run4/prompt-AS-RUN.md`.

## run5 — all five registered servers (2026-09-05)

Extended `scripts/mcp_catalogs.py` with two more real, previously-captured
catalogs (raw `tools/list` with declared `input_schema`, same standard as
github/calendar/slack): **filesystem** (`@modelcontextprotocol/server-
filesystem`, 14 tools, captured 2026-06-08 via mitm proxy against a
synthetic corp filesystem) and **sqlite** (`cbg-sqlite-server`, 5 tools,
same capture method). Ran all five servers in one job (2 GPUs — this
cluster caps public-partition jobs at 2 — round-robin, same fan-out shape as
`derive_input_types.sbatch`).

**Result: 69 of 74 declared-schema tools succeeded** (2 tools have no
declared inputs at all and are correctly excluded, not counted as
failures). The 5 failures are exactly the already-diagnosed pattern, not a
new bug: github's `push_files`, `update_issue`, `create_pull_request_review`
and calendar's `create-events`/`update-event` are this run's largest,
most deeply-nested schemas, hitting the same 16384-token context ceiling
documented above. filesystem and sqlite — both much smaller catalogs — had
zero failures.

**Quality held up on two domains the design was never tuned against**,
confirming the tool-independence goal rather than just working on the three
servers it was iterated on:

- `sqlite`: the *same* `sql` argument, in `read_query` vs. `write_query`,
  correctly got different feature vectors purely from tool context —
  `read_query.sql` is `selects_population: true, commits_change: false`;
  `write_query.sql` is `selects_population: false, commits_change: true,
  track_temporal_pattern: true`. `write_query`'s reused `atomic_ops` tag
  correctly fired the classifier's freeform-SQL worst-case rule:
  `[DELETE, EXECUTE, OVERWRITE, SCHEMA_MODIFY, WRITE]`, severity Critical.
- `filesystem`: `move_file.source` came back `references_existing: true`
  and `move_file.destination` came back `references_existing: false` —
  identical structural facts (both plain string paths), correctly
  distinguished by their semantic role in the tool, not by name or schema
  shape.

Reference output: `run5/{filesystem,sqlite,github,calendar,slack}.json`.

## run6-8 — batching, a separate composites pass, and a quote-escaping fix

Auditing run5's actual output at scale (315 arguments across all 5 servers,
not spot-checks) surfaced two more real quality problems, and the remaining
5 failures needed a proper fix rather than a bigger context window:

- **`scope_multiplier` was overused**: 4 of 7 instances (`per_page`,
  `perPage`, `order`) were ordinary pagination/sort values being tagged as
  if they multiplied a *different* argument's reach, when they were already
  the quantity or presentation choice in question. Tightened the prompt
  rule to require naming the specific sibling argument being multiplied —
  a value that is itself the count/limit is never this.
- **`composites` over-triggered**: 54/67 tools (80%) got at least one, many
  of them vacuous (`write_file`: `{path, content} → "defines the file path
  and content"` — not a new fact, just a restatement that a write tool has
  a target and a payload). Rewrote the rule to require a fact that exists
  *only* because of the pair (a duration, an effective scope) and gave
  explicit negative examples of what doesn't qualify.
- **Large tools now batch instead of needing a bigger context window.**
  Splitting a tool's argument facts into chunks of ≤20 for the classify
  call (each batch gets the full `tool_context` but only its own facts)
  fixed calendar's `create-events`/`update-event` completely, without
  touching `OLLAMA_CONTEXT_LENGTH` again. Composites are now asked in one
  **separate** follow-up call over the whole tool's argument list (its own
  prompt: `docs/standards/tool-input-features-composites.md`) so a composite
  spanning two different batches is never missed, and a composites failure
  degrades to `composites: []` rather than failing the tool.
- **A few small, ordinary tools (`push_files`, `create_issue`,
  `create_pull_request`, `respond-to-event`) kept failing identically across
  repeated runs with unchanged prompts** — not size, not content volume.
  Root cause: the model would quote an example value inside `reason` (e.g.
  "the PR's title, e.g. \"Fix login bug\""), and an unescaped `"` inside a
  JSON string breaks the whole reply — no brace-matching recovery can fix a
  genuinely broken string literal. Added an explicit prompt rule forbidding
  quotation marks inside any string value, paraphrasing instead. Fixed all
  four.

**Final result across runs 6-8: 73 of 74 declared-schema tools succeed**
(only `list_pull_requests` still fails intermittently, with no structural
cause found — treated as residual LLM instruction-following noise at the
~1% level, not a new bug, and not chased further this round). Reference
output: `run8/{filesystem,sqlite,github,calendar,slack}.json`.

**Noted but not folded in**: `reports/scan/{github,slack,calendar}_real.json`
already contain a separately-computed, much more carefully-designed 1-5
`tool_impact` ladder (LLM-judged, with explicit borderline-case rules and
worked examples — see `TOOL_IMPACT_TASK_5LEVEL_V2` in `static_scoring/
prompts.py`) plus a `tool_atomic_ops` block, from the "already fixed"
impact/asset/blast layer. It is a better-designed "how important is this
tool" signal than the rule-based `atomic_ops` severity this experiment
currently reuses for `tool_context` — but it doesn't exist for filesystem's
or sqlite's specific captures here, so folding it in now would make 3
servers richer than the other 2 asymmetrically. Worth revisiting if/when a
matching impact score is computed for all five.

## Explicitly out of scope

- Wiring v11's output into any runtime consumer (`dynamic_v2.py`,
  `BreadthScorer`, or a new scorer). This produces the static ledger only,
  same as v10 always has — v10 itself is "deprioritized" precisely because
  nothing downstream consumes it yet; v11 doesn't change that on its own.
- `src/mcp_security/static_scoring/` (impact / asset / blast-radius) and
  `src/mcp_security/param_scoring/` — untouched.
- Taint-sink-shape as an actual computed feature — documented limitation,
  not attempted.
- Capturing any server beyond the four already on disk.
