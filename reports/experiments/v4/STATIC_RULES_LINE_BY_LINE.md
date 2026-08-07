# `static_impact.py` — the whole file, in words

A walkthrough of every construct in
`src/mcp_security/static_scoring/static_impact.py` (≈870 lines), top to bottom.
The file has five parts: **the tier vocabulary**, **the scoping machinery**,
**the caps and exceptions**, **the parameter signals**, and **`classify()`**,
which runs everything in a fixed order.

---

# Part 1 — The tier vocabulary (`_TIER_PATTERNS`, lines 41–340)

A dictionary: tier number → tuple of regex strings. 260 patterns total. Every
pattern is word-boundary anchored (`\bdelete\b`), so "delete" matches but
"deleted_at" does not become a delete verb by accident.

The comment above it states the contract: **the score is the MAX tier whose
evidence fires** — the ladder's own "a tool spanning tiers takes the highest it
reaches". Order inside a tier is irrelevant; it only affects which pattern gets
reported as evidence.

### Tier 1 — "the server talks about itself, not the data" (16 patterns)
`ping`, `health(check)`, `heartbeat`, `liveness`, `readiness`, `echo`, `whoami`,
`current-time`, `server time`, `now`, `version`, `capabilities`, `uptime`,
`diagnostics`, `noop`, `nop`.

The unifying idea: the answer is a *fact about the service*, not about any data
it holds. Misusing such a call yields nothing you didn't already have by being
connected.

### Tier 2 — "about-ness" (50 patterns, three families)
1. **Listing / enumerating**: `list`, `ls`, `enumerate`, `index`, `catalog(ue)`,
   `browse`, `directory`, `dir`, `glob`, `walk`, `discover`, `inventory`,
   `registry`.
2. **Shape and attributes**: `metadata`, `schema`, `describe`, `stat`, `sizes`,
   `counts`, `names`, `ids`, `timestamps`, `permissions`, `attributes`,
   `exists`, `columns`, `fields`, `keys`, `headers`, `status`, `free-busy`,
   `availability`, `quotas`, `usage`.
3. **Consumption state and labels** — writes, but writes that only touch
   about-ness: `mark as read/unread/seen`, `acknowledge`, `star`/`unstar`,
   `pin`/`unpin`, `mute`/`unmute`, `flag`, `follow`/`unfollow`,
   `watch`/`unwatch`, `rename`, `react`, `emoji`.

That third family is the subtle one: marking a message read *is* a state change,
but nothing about the content changes, so it sits with metadata rather than with
writes.

### Tier 3 — "the substance is disclosed" (46 patterns)
`read`, `cat`, `tail`, `get`, `fetch`, `download`, `export`, `dump`, `extract`,
`search`, `query`, `find`, `lookup`, `select`, `grep`, `scan`, `view`, `show`,
`display`, `retrieve`, `open`, `preview`, `inspect`, `contents`, `body`, `text`,
`payload`, `history`, `transcripts`, `replies`, `thread`, `details`, `diff`,
`blame`, plus the **analysis family**: `summar(y|ise|ize)`, `analyse/analyze`,
`report`, `compare`, `calculate`, `compute`, `simulate`, `backtest`, `forecast`,
`research`, `evaluate`, `screen(er)`.

The analysis family was added late, after the confidence field showed that
finance tools like `monte_carlo_simulation` and `analyze_fng_trend` were matching
nothing at all and silently defaulting. Computation over data is a content read:
it must see the substance to compute on it.

### Tier 4 — "state changes and the system can undo it" (85 patterns, five families)
1. **Bring into existence**: `create`, `add`, `new`, `make`, `mkdir`, `insert`,
   `append`, `upload`, `import`, `register`, `provision`, `allocate`, `draft`,
   `generate`, `build`, `clone`, `duplicate`, `copy`, `fork`, `branch`,
   `snapshot`, `stage`.
2. **Change in place**: `update`, `edit`, `modify`, `patch`, `put`, `set`,
   `upsert`, `save`, `store`, `write`, `amend`, `revise`, `adjust`, `configure`,
   `relabel`, `tag`, `label`, `annotate`.
3. **Relocate**: `move`, `mv`, `relocate`, `transfer to`, `sync`, `mirror`.
4. **Membership and access** — recoverable in both directions: `join`, `leave`,
   `grant`, `revoke`, `assign`, `unassign`, `membership`, `subscribe`,
   `unsubscribe`, `share`, `permit`, `authorise/authorize`.
5. **In-system posting and lifecycle**: `post`, `comment`, `reply`, `respond`,
   `rsvp`, `accept`, `decline`, `vote`, `submit`; `open`, `close`, `reopen`,
   `archive`, `unarchive`, `restore`, `enable`, `disable`, `activate`,
   `deactivate`, `pause`, `resume`, `schedule`, `reschedule`, `manage`, `apply`,
   `commit`, `checkout`.

Note `grant` **and** `revoke` are both tier 4. Revoking access sounds
destructive, but it is re-grantable — the test is undo-ability, not how alarming
the verb sounds.

### Tier 5 — "no path back **from inside the system**" (63 patterns, four families)
1. **Destroy**: `delete`, `remove`, `rm`, `unlink`, `destroy`, `drop`, `purge`,
   `wipe`, `erase`, `truncate`, `clear`, `flush`, `evict`, `reset`, `empty`,
   `prune`, `discard`, `expire`, `invalidate`, `terminate`, `kill`, `shutdown`,
   `deprovision`, `decommission`, `uninstall`, `cancel`, `void`, `revert`,
   `rollback`, `force-push`.
2. **Replace wholesale**: `overwrite`, `replace the entire/whole/complete`,
   `completely overwrite`.
3. **Execute**: `execute`, `eval-code/script/expression`,
   `run a command/script/code/query/job`, `invoke`, `deploy`, `release`,
   `publish`, `merge`, `push`, `rebase`.
4. **Money**: `transfer funds`, `payments`, `charge`, `refund`, `payout`,
   `withdraw`, `settle`, `place an order`, `trade`, `buy`, `sell`.
5. **Leaves the system boundary**: `send`, `email`, `sms`, `notify`, `webhook`,
   `invite`, `broadcast`, `forward`, `announce`.

That last family is the conceptual core of tier 5: an email already delivered is
as unrecallable as a dropped table. "Irreversible" means *the system's own
controls cannot restore the prior world* — which covers both destruction inside
and escape outside. Note this fires on the declared **action** (`send_message`
sends on every call), not on an `openWorldHint` annotation or a `notify`
parameter — those are possibilities, and possibilities are dynamic-stage work.

### Line 341 — `_COMPILED`
Every pattern is compiled once with `re.I` into `{tier: (compiled, …)}`. Purely a
performance concern: `classify()` runs 260 regexes per tool, and the corpus is
270 tools.

---

# Part 2 — The scoping machinery (lines 343–498)

This part exists because of one discovery: **matching verbs across a whole
description is the dominant source of false positives.**

### `_AMBIGUOUS` (lines 350–471) — 101 tokens
Words that are a strong action verb in a tool *name* but an ordinary noun in
prose. Grouped by domain in the source: VCS (`branch`, `fork`, `merge`, `push`,
`rebase`, `commit`, `tag`, `release`, `deploy`, `publish`…), messaging (`email`,
`notif`, `invite`, `comment`, `reply`, `announce`, `post`, `share`, `follow`,
`watch`, `flag`, `vote`, `accept`, `decline`), lifecycle/admin (`manage`,
`configure`, `provision`, `register`, `submit`, `apply`, `enable`, `disable`,
`open`, `close`, `archive`, `restore`, `schedule`, `cancel`, `kill`, `reset`,
`clear`, `run`, `invoke`, `make`, `build`, `new`, `generate`), data movement
(`copy`, `sync`, `mirror`, `import`, `export`, `snapshot`, `save`, `store`,
`set`, `put`, `add`, `draft`), money (`payment`, `trade`, `buy`, `sell`,
`charge`, `order`), and payload nouns (`index`, `catalog`, `directory`,
`history`, `status`, `mark`, `scan`, `key`, `field`, `column`, `header`, `text`,
`body`, `payload`, `report`, `compare`, `evaluate`, `screen`, `usage`).

Three real failures motivated it, all in the source comment:
- `usergroups_list` → tier 5, because its prose says groups *"notify all members"*
- `users_search` → tier 5, because "email" is one of its *search fields*
- `list_commits` → tier 4, because "branch" appears as a *noun*

### `_NEGATOR` and `_negated()` (lines 479–489)
A regex of negators — `never, not, n't, don't, do not, does not, cannot, can't,
avoid, without, no need to, refrain from, must not, should not` — followed by
`[^.]{0,40}$`. That tail is the clever part: it requires the negator to be within
40 characters *and* with no full stop in between, i.e. **the same clause**.

`_negated(text, position)` slices the 60 characters before a match and asks
whether the negator regex fits at the end of that window. If yes, the verb is a
prohibition, not a capability.

Real case: `sec-edgar-mcp` scored six read-only tools as tier-4 writes because
their descriptions instruct the model — *"ONLY use data returned from SEC
records. **NEVER add** external information."*

### `_is_ambiguous(pattern)` (line 492)
Checks whether any ambiguous token is a substring of the *pattern string* — so
`r"\bpush\b"` contains "push" → ambiguous. Simple, and it means adding a word to
`_AMBIGUOUS` automatically narrows every pattern containing it.

### `_first_sentence(text)` (line 496)
Splits on `(?<=[.!?])\s` and takes the first piece — the sentence that states
what the tool does, before the caveats and LLM instructions. Used only by the
tier-2 cap scope.

---

# Part 3 — Caps and exceptions (lines 501–560)

### `_SCOPED_EDIT` (line 503)
Matches `line-based`, `partial`, `specific lines/fields/parts`, `diff`,
`appends to`, `leaves the rest`, `selective`. Evidence that an edit is
reconstructable, which pulls a would-be 5 back to 4.

### `_BULK_WORDS` (line 509)
`bulk`, `batch`, `multiple`, `several`, `many`, `in one call`. Sets the
`is_bulk` flag. The comment directly below records that **the "+1 tier for
dropping a safety" rule was removed on request** — bulk no longer changes the
score here; dominance is enforced by the pipeline's separate bulk-twin pass.

### `_CREATE_OR_OVERWRITE` (line 517)
`create_or_update|overwrite|replace`, tolerant of `_`, `-` or space. One call
that can either create new or replace wholesale takes 5.

### `_CONTAINER_NOUN` (line 526)
`calendars, directories, folders, repositories, channels, tables, accounts,
buckets, databases, schemas, colours, groups, workspaces`. Listing one of these
is a catalog; listing anything else hands back items.

### `_CAP_MARKERS` (lines 532–560)
Pairs of (tier ceiling, regex) describing **what a read returns**:
- **cap 1**: `current date/time`, `server time`, `ping`, `health`, `heartbeat`,
  `version`, `capabilities`, `whoami`.
- **cap 2**: `free-busy`, `availability`, `busy blocks`, `schema`, "list/names/ids
  of \<containers\>", "available \<plural\>", `colour ids/palette`, "mark … as
  read", "marks all messages as read", "metadata about", "detailed metadata",
  `status`, `dashboard`, `connection state`, "listing of all files and
  directories", "distinguish between files and directories".

---

# Part 4 — Parameter signals

The premise, cited in the source: **the dangerous property is often in the
INPUTS, not the verb.** As of the openWorld/parameter removal these are recorded
and never scored — the inputs describe the tool, the dynamic stage prices them.

### `_PARAM_SIGNALS`
Nine tuples of `(key, regex, explanation)`. Every regex is `\A…\Z` **full-name
anchored**, with a warning comment: an unanchored alternation made `cc` match
inside `a(cc)ount`, turning every calendar read into an outbound-messaging tool
(corpus tier-5 count 51 → 20 once fixed).

**None of them raises the tier.** They are capability flags only — a parameter
says what the caller *could* pass, and the value actually passed is a runtime
fact the dynamic stage prices.

| key | matches |
|---|---|
| `raw-query` | `sql`, `statement`, `query`, `q`, `expression`, `*_sql` |
| `raw-command` | `cmd`, `command`, `script`, `code`, `exec`, `shell`, `program` |
| `outbound` | `send_updates`, `notify`, `webhook`, `recipients`, `to`, `cc`, `bcc` |
| `path` | `path`, `file`, `dir`, `destination`, `source`, `src`, `dst`, `*_path` |
| `recursive` | `recursive`, `recurse`, `deep`, `all_files`, `include_subdir` |
| `glob` | `glob`, `pattern`, `wildcard`, `regex`, `match`, `filter` |
| `force` | `force`, `hard`, `permanent`, `skip_confirm`, `overwrite`, `replace` |
| `unbounded` | `limit`, `max_results`, `count`, `page_size` |
| `dry-run` | `dry_run`, `preview`, `simulate` |

### `_tool_params(tool)`
Pulls `input_schema` or `parameters`, returns its `properties` dict, tolerating
either attribute name and a missing/odd schema.

### `_param_signals(tool)`
For each parameter, for each signal whose regex matches the parameter name:
1. Build a note: `` `key: `pname` explanation` ``.
2. If the key is `path`, `raw-command` or `raw-query` **and** the schema has no
   `enum`, `pattern` or `format`, append *"(unconstrained: no enum/pattern/format)"*
   — this is the over-privilege case.

Returns the flag list. Nothing else: there is no floor, no conditional
promotion, no corroboration regex. `write_query` is tier 5 from the verbs in
"INSERT, UPDATE, or DELETE"; `read_query` with the identical `query` parameter
stays 3. The parameter is reported on both.

---

# Part 5 — `StaticImpact` and `classify()`

### `StaticImpact`
The result record: `tool_name`, `tool_impact` (the tier), `reasoning` (evidence
joined into a sentence), `evidence` (the list), `annotation_bound` (the ceiling
if `readOnlyHint` applied), `is_bulk`, `capability_flags`, `confidence`.

Its docstring states the two things that are deliberately **not** folded into the
tier: capability flags are a separate axis, and the threat model is **misuse in
normal operation** — the declaration is taken at face value.

### `_matches(name, description)`
Builds two scopes:
- `full` = name (separators → spaces) + description
- `narrow` = name only, separators → spaces

The separator normalisation matters: `\bpush\b` cannot match `push_files`,
because `_` is a word character. `push_files` → `push files` fixes it.

Then for each tier, for each pattern: choose the scope by `_is_ambiguous`, and
count the pattern as fired only if **at least one occurrence is not negated**
(`any(not _negated(...) for m in pat.finditer(scope))`). So one negated mention
doesn't suppress a genuine second mention.

### `_array_param(tool)`
True when any parameter has `"type": "array"` — a bulk signal independent of
wording.

### `classify(tool)` — the fixed order

**Setup.** Reads `name`, `description`, builds `text`, computes `hits` via
`_matches`, and reads all four annotation hints.

**Rule 1 — annotation ceiling.** `ceiling = 3 if readOnlyHint else 5`.
Records `readOnlyHint`/`destructiveHint` as evidence.

**Rule 2 — highest firing tier within the ceiling.** `max(t for t in
hits if t <= ceiling)`. If nothing fired: tier 3 if read-only, 5 if destructive,
else **3** — a tool that declares nothing is assumed to read content, not assumed
harmless. Evidence records either the firing verbs or `"no verb evidence"`.

**Rule 2b — container listings.** If tier is 2, a listing verb fired,
no container noun appears, and no tier-3 verb fired → **3**. Ambiguity resolves
upward because under-scoring is the costlier error.

**Rule 3 — return-shape caps.** Only when tier ≤ 3. Two different
scopes: cap 1 is checked against the **name only** (a liveness tool is *named*
one — `get_user_portfolio_summary` scored 1 because its prose ended "…and stock
analysis **capabilities**"); cap 2 against name + first sentence. Breaks at the
first cap that applies and is lower than the current tier.

**Rule 3b — create-or-overwrite.** Tier 4 + `_CREATE_OR_OVERWRITE` → 5.

**Rule 4 — scoped-edit exception.** Tier 5 + scoped-edit language, and
no genuine delete/remove/purge among the tier-5 hits → back to 4.

**Rule 5 — destructiveHint corroboration.** Tier 4 + `destructiveHint`
+ a tier-5 verb among the hits → 5. Note the guard: it needs a tier-5 verb, so
the hint never decides alone.

**Bulk flag.** Sets `is_bulk`; does not change the tier.

**Rule 6 — parameter signals.** Computes capability flags. The tier is not
touched.

**openWorldHint — removed.** The module does not read it. Boundary crossing
(did this call actually leave the system?) is a per-request fact and belongs to
the dynamic stage; the hint is still parsed onto `ToolSpec` for that stage to
use. What remains here: `idempotentHint=false` on a tier ≥ 4 adds a "retry
repeats the effect" flag.

**Confidence.** 0.5 base; 0.8 if an explicit tier verb fired; +0.15 if any
annotation was present; **0.35** if nothing fired (the tier is a default, not a
finding).

**Return.** The full record, with `annotation_bound` set only when the
read-only ceiling actually applied.

### `classify_all(tools)`
`{name: classify(tool)}` for a whole registry.

---

# Two structural observations

**Only two things can now raise a tier**: a verb in the tool's own text, and a
`destructiveHint` that corroborates one. Annotations bound from above (Rule 1),
caps bound reads from above (Rule 3), and everything else is descriptive. That
makes the tier a statement about the **declared action** and nothing else —
which is the property the ladder claims to measure.

**Everything is additive and logged.** No rule silently replaces another; each
appends to `evidence`, so the `reasoning` string reconstructs the full derivation.
That is what makes a static score auditable in the same way a logged LLM answer
is — you can always ask *why* a tool got its tier and get a specific answer.
