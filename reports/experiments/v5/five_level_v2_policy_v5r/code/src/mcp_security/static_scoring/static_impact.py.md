# `static_impact.py` — the deterministic tool-impact rules

**1 333 lines. This is where stage 1 is decided without a model.**

The module holds two classifiers. Only one of them runs in v5r.

| Function | Used by | Status |
|---|---|---|
| `classify()` | v4, v4-static, v5 | the older *tier* classifier. Kept unchanged so those arms stay byte-reproducible. **Not called in v5r.** |
| `classify_by_operation()` | **v5r** | the current *operation* classifier |
| `classify_all_by_operation()` | convenience | maps it over a tool list |

Both return a `StaticImpact`: the tier, the evidence that set it, a confidence,
`is_bulk`, and `capability_flags`. The evidence list is the audit trail — a static
score is as inspectable as a logged model answer.

## What `classify_by_operation()` asks

One question: **is this a read, a write, or a removal?** Then five rules.

1. **Which operation.** The most consequential class whose verbs fire —
   `remove > write > read > metadata > none` — over 281 patterns
   (16 none / 52 metadata / 46 read / 122 write / 45 remove). 119 *ambiguous*
   single words are matched against the tool **name only**, because a word can be
   a verb in a name and a noun in prose. Multi-word phrases are exempt from that
   narrowing: a phrase naming the verb and its object cannot be misread.
2. **A generic read verb is not evidence of content.** `get` / `fetch` / `search`
   / `find` / `show` / `query` say something comes back, not what. If that is all
   the read evidence there is and a metadata verb also fired, the answer is
   metadata.
3. **A write is ordinary (4) unless it states a limit (3).** `overwrite` /
   `replace` → 4 with evidence. `append` / `add a comment` / `one field` → 3 with
   evidence. **Neither → 4 as a default, confidence 0.35, which abstains.**
4. **Longest match wins.** A match inside a longer match from another class is
   dropped before precedence is applied — "Mark a channel as read" contains
   "read", but the phrase describes the operation.
5. **A liveness probe is one that is NAMED one.** Name-only, so prose about
   "capabilities" cannot turn a read into a ping.

Then: annotations are appended as **evidence only** and never move the tier; a
hint contradicting the description is recorded as a contradiction.

## The confidence field is the hand-off signal

`0.8` when a rule had evidence. `0.35` on the two branches that are *defaults*
rather than findings — no verb matched at all, or a write that never said whether
the amount is bounded. `pipeline.STATIC_IMPACT_MIN_CONFIDENCE` (0.5) turns that
into the decision to call the model.

## Read this alongside

- `../../../../STATIC_RULES.md` — every rule with worked examples and the
  measured tier distribution
- `../../../../GROUNDING.md` — which of these rules has a published source (the
  3/4 line does; the 281-pattern lexicon and the name-only scoping do not)

## Deliberately absent

**Breadth** — how many items a call reaches is coverage, scored by blast radius,
so no breadth vocabulary is read here and an array parameter never promotes a
tier. **Open-world** — a channel is not an operation; sending creates a message,
so it is a write. **Any annotation ceiling** — a server must not be the authority
on its own risk score.
