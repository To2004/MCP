# v4 — comparing the four severity matrices

Four arms, identical inputs (tool catalog + org profile), identical deterministic
post-processing (bulk twins, alias twins, sens/impact floors, roofs, pure score
bands). They differ in exactly two places: **which impact prompt** and **whether
impact came from the model or from rules**.

| Arm | Tool impact | Blast radius | Impact prompt |
|---|---|---|---|
| `five_level_v2_pure_v4` | LLM | LLM | v4 (current) |
| `five_level_v2_pure_v4_bulkclause` | LLM | LLM | v4 **with** the "bulk drops a safety ⇒ higher tier" clause |
| `five_level_v2_pure_v4static` | **rules** (hardened) | LLM | — (no impact prompt) |
| `five_level_v2_pure_v4static_prehardening` | **rules** (older) | LLM | — |

## Severity matrices

> **The `static` rows below are superseded.** The `openWorldHint` and
> parameter-promotion rules were removed (boundary crossing moved to the dynamic
> stage) and the arm was re-assembled offline. Refreshed numbers, the three-arm
> comparison and the new agreement figures are in
> [STATIC_VS_LLM_AFTER_REMOVAL.md](STATIC_VS_LLM_AFTER_REMOVAL.md) — headline:
> calendar Σ 2 663 → **2 253**, impact agreement 0/13.

| server | arm | low | med | high | crit | Σ score |
|---|---|--:|--:|--:|--:|--:|
| calendar | v4 | 29 | 42 | 8 | 1 | 2 280 |
| | bulkclause | 25 | 45 | 9 | 1 | 2 357 |
| | **static** *(old)* | 30 | 30 | 16 | 3 | **2 663** |
| | static-pre | 29 | 41 | 9 | 1 | 2 282 |
| slack | v4 | 56 | 45 | 18 | 4 | 3 779 |
| | bulkclause | 56 | 45 | 18 | 4 | 3 779 |
| | static | 57 | 49 | 19 | 4 | 3 944 |
| | static-pre | 58 | 50 | 16 | 5 | 3 958 |
| github | v4 | 69 | 59 | 32 | 11 | 6 340 |
| | bulkclause | 69 | 59 | 32 | 11 | 6 340 |
| | static-pre | 54 | 75 | 30 | 14 | 6 756 |
| fs:corp | v4 | 85 | 54 | 44 | 14 | 6 985 |
| | bulkclause | 85 | 54 | 44 | 14 | 6 985 |
| | static | 87 | 52 | 47 | 14 | 7 232 |
| | static-pre | 81 | 55 | 49 | 14 | 7 466 |
| sqlite | v4 | 12 | 19 | 3 | 4 | 1 411 |
| | bulkclause | 12 | 19 | 3 | 4 | 1 411 |
| | static | 11 | 20 | 3 | 4 | 1 429 |
| | static-pre | 12 | 19 | 3 | 4 | 1 411 |

## Why they differ

### 1. v4 vs bulkclause — identical everywhere except calendar

Slack, github, fs and sqlite are **byte-identical**, down to the score sum. That
is not luck: the clause lived only in the IMPACT prompt, the blast prompt was
untouched, and greedy decoding (temperature 0, seed 0) makes the model
reproducible. A prompt sentence about *bulk variants* changes nothing on servers
whose tools have no bulk twin — so nothing moved.

Calendar is the only server with a bulk twin (`create-events`), and it moved by
**one tool**: `list-events` 3 → 2. (Not `create-events` — the deterministic
bulk-twin pass had already been holding it at its singular's tier, so removing
the prompt clause changed a neighbouring judgement rather than the bulk tool
itself.) Σ score fell 2 357 → 2 280.

**Reading:** a single sentence of prompt has a small, local, attributable effect.
This is the cleanest evidence in the whole campaign that the pipeline is
deterministic enough to attribute changes to their cause.

### 2. static vs LLM — impact agrees, blast wanders

| server | impacts differing | blast cells differing |
|---|--:|--:|
| sqlite | **0 / 5** | 1 |
| fs:corp | 2 / 14 | 23 |
| slack | 2 / 16 | 35 |
| calendar | 3 / 13 | 25 |

The headline: **the rules reproduce the model's tool impact almost exactly**, but
the *same LLM* re-scoring the *same blast prompt* disagrees with itself on 23–35
cells per server. The impact stage is the stable one; blast is where the
variance lives.

Why blast moves at all, when decoding is deterministic: the blast prompt carries
the tool's impact-stage context implicitly (the two arms are separate processes
with separately-ordered calls), and blast is a genuinely harder judgement — the
model is deciding reach across an asset it must reason about. Impact asks "what
kind of action is this", which has a right answer in the tool's own text.

The specific impact disagreements are all defensible both ways:
- `create-event`, `update-event`, `create-events` **4 → 5** (static higher):
  the rules read `openWorldHint=true` and applied the ladder's boundary-crossing
  clause — creating an event with `sendUpdates` emails attendees. The model
  judged it a recoverable write. **This single change explains calendar's whole
  gap** (Σ 2 280 → 2 663, high 8 → 16).

  > **Superseded.** The `openWorldHint` rule was since **removed** — boundary
  > crossing depends on the actual request (was `sendUpdates` set?), so it moved
  > to the dynamic stage. These three tools now score **4**, matching the LLM,
  > and calendar's static/LLM impact disagreement drops to **0 / 13**. The
  > matrix rows below for `calendar / static` predate that removal and need a
  > re-assembly to refresh.
- `conversations_leave` **5 → 4** (static lower): the model treated leaving a
  channel as irreversible; the rules call it a recoverable membership change.
- `usergroups_me` **4 → 5** (static higher): its description mentions `remove`.
- `directory_tree`, `search_files` **2 → 3** (static higher): the rules score a
  recursive listing as content, the model as metadata.

### 3. static vs static-prehardening — one annotation, one server

Impacts differ **only on calendar**, and only on the same three tools, for one
reason: `openWorldHint` was previously **dropped at load** (`ToolSpec` had no
such field), so the older classifier never saw it. Slack, fs and sqlite show
**zero** impact differences — their remaining wobble is blast variance.

So the hardening's effect on *this* corpus was one recovered MCP annotation. Its
real value showed on the finance corpus, where the richer vocabulary cut
unclassified tools from 32 to 15 of 270.

## What this says overall

1. **Tool impact is rule-derivable.** 0/5, 2/14, 2/16, 3/13 disagreements — and
   every disagreement is a judgement call, not an error. (Calendar's 3/13 became
   **0/13** once the `openWorldHint` rule moved to the dynamic stage.)
2. **Blast is not.** The same model on the same prompt moves 23–35 cells between
   runs; no rule set would be more arbitrary than that, but it does mean blast
   carries the campaign's residual noise.
3. **Prompt wording has small, local effects**; input and annotation coverage
   have larger ones. The `openWorldHint` fix moved calendar's severity more than
   any prompt edit in this generation did.
