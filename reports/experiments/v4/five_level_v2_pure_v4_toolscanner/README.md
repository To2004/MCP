# Experiment: three independent tool-impact methods

Three ways to answer *"what is this tool's impact tier?"*, run over the same
catalogs. They share no machinery, so where they agree the agreement is
corroboration; where they split, the split localises the problem.

| | method | where it lives | signal it reads |
|---|---|---|---|
| **A** | LLM | `five_level_v2_pure_v4/` | the model reads the tool JSON and answers the 1-5 ladder |
| **B** | static | `static_scoring/static_impact.py` | tiered verb patterns matched over name + description prose |
| **C** | atomic | `atomic_scanner/` *(new)* | the name tokenised to verb+object, mapped to an operation taxonomy; tier = max over the operations |

Regenerate: `uv run python scripts/three_way_impact.py`

## What method C is

`src/mcp_security/atomic_scanner/` parses a tool into the **set of atomic
operations** it performs, then derives the tier as `max(ladder_tier)` over that
set. The set is the useful output — a tool that both `READ`s and `DELETE`s is
worth seeing as such, not just as a 5.

It reads the tool the way a developer names things:

1. **The name is a sentence.** `github_create_pull_request` is
   namespace + verb(`create`) + object(`pull_request`).
2. **The schema is a contract.** A `content` parameter means data flows in; a
   `command` parameter means the caller composes the operation.
3. **The annotations are a declaration.** `readOnlyHint: true` doesn't bound the
   tier, it makes write operations *impossible*, so those hits are dropped.
4. **The description is a fallback only** — consulted for tools whose name says
   nothing. Prose is where method B lives; reading it by default would turn
   corroboration into a shared blind spot.

### The taxonomy

`atomic_scanner/data/atomic_operations_v2.csv`. The **13 base rows are carried
over verbatim** — same rank, same severity, same reasoning — from
`presentations/heatmap_byhand/csv/atomic_operations.csv`. That file and the
`atomic_ops` package it feeds are untouched.

Nine rows were added for operations the base set has no name for:

| added op | tier | why the base set couldn't express it |
|---|:--:|---|
| `TRANSACT` | 5 | money movement is its own irreversibility — not destruction, not disclosure |
| `PUBLISH` | 5 | `BROADCAST` sends *data* to people; deploy/release/merge makes *state* live |
| `ACCESS_CHANGE` | 4 | grant/revoke — recoverable both ways, so not `DELETE` |
| `MEMBERSHIP` | 4 | removing a member is not destroying them |
| `CONFIGURE` | 4 | settings govern later behaviour, not the data |
| `INTERACT` | 4 | browser automation lands its effect in someone else's system |
| `BUILD` | 4 | train/compile a persistent artifact |
| `STATE_TOGGLE` | 2 | mark-read/star/pin: a write that changes no content |
| `NO_EFFECT` | 1 | the base set starts at `LIST`; a ping had nowhere to go |

A new `ladder_tier` column maps operations onto the 1-5 impact ladder, keeping
the two scales explicit rather than silently equal: **severity ranks attacker
value, the ladder ranks what one call does.** They differ — `OVERWRITE` is
severity 4 but ladder 5, because a full overwrite has no in-system undo.

## Results

| corpus | tools | A vs B | A vs C | B vs C |
|---|--:|--:|--:|--:|
| live (5 servers) | 74 | **95%** | **93%** | **96%** |
| finance (5 servers) | 196 | *no LLM arm* | — | **86%** |
| reference (15 servers) | 120 | *no LLM arm* | — | **83%** |

On the live corpus all three land on the same tier for **68 of 74 tools (92%)**,
and there is **not one three-way split** — every disagreement is 2-vs-1.

### The triangulation worked

Bucketing the live disagreements by which method is the odd one out found real
bugs on every side. Before this experiment: A/C 77%, B/C 80%.

**Bugs it found in C (atomic), all now fixed:**
- `get`/`fetch` were treated as operations. They name none — the object does.
  `get_file_info` was READ, is METADATA; `get_current_time` was READ, is NO_EFFECT.
- Late nouns read as verbs: `list_commits` "committed", `list_branches`
  "created", `get_pull_request_comments` "wrote", `list_releases` "published".
- Namespace stripping moved an object to first position: `journal_trade_review`
  became a `TRANSACT` once `journal` was stripped. Positions are now measured
  before stripping.
- `run` was execution unconditionally — `run_backtest` is a computation.
- `news` was lemmatised to `new` → CREATE, costing two finance tools a tier.

**Bugs it found in B (static), all now fixed:**
- `puppeteer_evaluate` — *"Evaluates arbitrary JavaScript"* scored **3**, because
  `evaluate` sits in the analysis family. Evaluating **code** is execution: now 5.
  C had it right from the start, and no amount of staring at B would have
  surfaced it.
- `describe_table` — *"Returns the CREATE TABLE DDL"* scored **4** on the quoted
  keyword `CREATE`. A quoted-statement guard now handles it, per-occurrence, so
  `create_table` (whose *name* carries the verb) still fires.
- `dismiss_notification` — scored **5** because `notification` was in the
  outbound family. Only `notify` acts; `notification` is the object.
- `get_latest_release` — scored **5** on the noun `release`. Only a tool *named*
  `release_*` publishes.

**Where A (the LLM) is the odd one out — 3 tools, and B and C agree against it:**
`conversations_leave` (5 vs 4), `search_users` (2 vs 3),
`get_pull_request_files` (2 vs 3). Two methods agreeing is evidence, not proof —
on `get_pull_request_files` the rules are right for the wrong reason (GitHub
returns the patch, which neither rule set knows).

## Can the three be ground truth?

**Partly, and it is worth being precise about where the limit is.**

Where all three agree — 92% of the live corpus — the tier is about as well
supported as this framework gets without human labelling, because three methods
reading three different signals converged.

But **agreement is not correctness**, and two specific failure modes survive it:

1. **Shared blind spots.** All three read only the declaration. When a tool
   understates itself — `get_pull_request_files` says "list of files" and returns
   diffs — all three can agree and all three be wrong. No amount of method
   diversity fixes a missing fact.
2. **Two rule sets are not two opinions.** B and C were both written by me,
   against the same corpora, in the same week. When they agree against the LLM
   that is weaker evidence than the 2-vs-1 arithmetic suggests. The genuinely
   independent vote is A.

So: use the consensus as a **triage signal**, not a label. The 6 live tools where
the three split are the ones worth a human's attention, and that is the real
product of this experiment — it turns 74 judgement calls into 6.

For finance and reference there is **no LLM arm at all**, so the "three-way"
agreement is really two rule sets agreeing at 86% and 83%. That is not ground
truth, and the remaining gap is where the next round of bugs lives.
