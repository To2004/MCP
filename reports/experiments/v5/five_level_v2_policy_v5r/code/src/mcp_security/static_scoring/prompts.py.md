# `prompts.py` — every template the scan sends

**1 243 lines, most of it history.** The file accumulates one prompt family per
experiment generation so old arms stay reproducible. v5r uses six constants;
everything else in the file belongs to v1–v5.

| Constant | Stage | What it does |
|---|---|---|
| `DOMAIN_INFERENCE_SYSTEM_V5R` + `_USER_V5R` | 0 | asks three fields — `mcp_kind`, `content_unit`, `contents_definition`. 768 chars, down from 3 369. |
| `TOOL_IMPACT_TASK_V5R` | 1 | the operation ladder. **Sent only where the rules abstain.** Includes its own return schema, so there is no separate user template. |
| `_PROPOSER_BASE_DESC` | 2, 3 | the shared preamble: the org policy (authoritative for importance) plus the inferred domain (authoritative for capability) |
| `ASSET_TASK_POLICY_V5R` + `ASSET_USER_POLICY` | 2 | classify the asset against the policy's classes, then map that class's adverse-impact language onto 1–5 |
| `BLAST_TASK_V5R_FLOORED` | 3 | the propagation rubric, plus the floors stated to the model |
| `BLAST_USER_V5R` | 3 | carries the tool, the asset, the sibling lists, and the already-decided impact and sensitivity |

## What v5r changed, and why

**Domain inference lost seven of ten fields.** `dependency_hubs`,
`dangerous_classes` and `irreversible_actions` asked the model to infer what the
policy now *states* — hubs are the register's `Flags` column, classes are the
classification table, prohibited operations are the operation limits — so keeping
them invited the two to disagree. `asset_meaning`, `blast_radius_meaning` and
`worked_example` were prose no stage consumed while being re-serialized into every
later prompt via the preamble. That is the whole saving: seven fields off ~540
prompts per server, not off one.

**A finance paragraph left both the domain and sensitivity prompts.** "SEC
insider-trade / Form 4 filings, institutional-holding / 13F filings, central-bank
series" was one domain's document types inside a domain-agnostic prompt, written
to stop over-scoring on the finance corpus. The clause that generalizes —
publication, not topic, decides — stayed.

**Open-world left the impact ladder.** A channel is not an operation.

**The blast DISCIPLINE block lost three of four lines**: a "ceiling is 4" cap
written to kill one v3 over-read; a sentence using impact vocabulary ("cannot
exceed the metadata tier") that had no referent among the blast tiers, which is
why it read as unclear; and a consistency instruction the model cannot follow
because each cell is a separate call.

**The floors are now stated, not only enforced.** `BLAST_TASK_V5R_FLOORED` tells
the model the three minimums and `BLAST_USER_V5R` hands it the decided sensitivity
and impact as facts. This accepts a risk: a model that can see the sensitivity may
anchor reach on value, which is the separation the rubric otherwise enforces. The
deterministic pass in `pipeline.py` remains authoritative, and
`scripts/check_blast_floors.py` audits both afterwards.

The rendered text as actually sent is `../../../scoring-prompts-AS-RUN.md`; the
audit of each prompt's role and its overfit lines is `../../../../PROMPT_ROLES.md`.


## Revision: blast counts subjects and systems, not items

`BLAST_TASK_V5R` was rewritten after the numbers showed the old rubric doing the
wrong arithmetic. It counted items — "one item among many", "most of the asset" —
and no published definition of blast radius does. They all measure how far a
consequence propagates across users and dependent systems, and reachability is
what decides. The rubric now opens with:

> COUNT SUBJECTS AND SYSTEMS, NOT ITEMS. Reading ONE password file touches one
> item and compromises every system that password opens — that is a 5, not a 1.

Tier 3 is now the **normal case** ("a group — the people or systems attached to
what the call touched. Start here and move for a reason"), and tier 1 is reserved
for "almost nobody — nothing and nobody depends on it".

## The escape routes were split into four

Route (b) used to read "population — flagged `population` **or**
`self-sufficient`". Those flags mean different things: `population` is coverage,
`self-sufficient` is content-portability. Sharing one route let any tool touching a
`self-sufficient` asset claim tier 5, which is how a single **post** into
`vireo-unblinding` scored blast 5 while `conversations_history` — reading the whole
channel — scored 4.

```
(a) hub                other systems authenticate against it / load config from it
(b) self-sufficient    what the call RETURNS is usable on its own elsewhere
(c) population         one call reaches the asset's ENTIRE set of subjects
(d) irreversible-total the asset is destroyed with nothing left to restore
```

Two invariants are now tested rather than assumed:

- **the routes live in blast only** — `TOOL_IMPACT_TASK_V5R` mentions no flag, no
  register and no escape, because reach is not an impact question;
- **every route is reportable** — `BLAST_USER_V5R`'s `escape` field accepts
  `a|b|c|d|none`. Adding route (d) without widening the schema would have left it
  unusable, and did, until a test caught it.

## A caution about editing this file

It is 1 243 lines of accumulated generations and constants are defined in
append order, not in stage order. A slice-based edit here once deleted
`ASSET_TASK_POLICY_V5R` while rewriting the neighbouring blast constant, and the
suite did not notice because nothing asserted the v5r prompt set was complete.
Two tests now do (`test_every_prompt_the_v5r_path_references_exists`,
`test_v5r_prompt_templates_have_the_placeholders_their_callers_format`). Prefer
targeted edits over computed slices.
