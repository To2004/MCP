# The static tool-impact rules — as they are now

The rules the scanner uses today, in execution order. Implemented in
`static_impact.classify_by_operation()` and used by mode `five_level_v2_v5r`.

**One question decides the tier: what operation is this — read, write, or
remove?** Not what it touches (blast radius scores that), not what the target is
worth (sensitivity scores that), and not which channel it uses (a runtime fact).

The older tier classifier `classify()` is still in the file, unchanged, because
the v4 and v5 arms were run with it and must stay reproducible. It is not used by
any current mode. What it did differently, and why each of its rules went, is in
[the appendix](#appendix--what-the-previous-rules-did-and-why-they-went).

---

## The ladder

| Tier | Operation | What qualifies |
|---|---|---|
| **1** | none | the server talks about itself, not the data: ping, health, version, clock, whoami |
| **2** | metadata | returns or changes only about-ness — names, ids, counts, sizes, timestamps, permissions, schema, a listing; or consumption state: mark read, star, pin, mute, rename |
| **3** | content read **or** limited write | returns an item's substance (bodies, values, message text), **or** writes a bounded amount and leaves the rest untouched: append a line, add a comment or reply, set one named field, post a short message |
| **4** | write | the ordinary write — the caller supplies what the item says: create a record with its fields, update an event, write a file, overwrite content |
| **5** | removal or execution | delete, wipe, drop, purge, truncate; or it executes code, runs a command, moves money |

Tier 3 holds both a read and a *limited* write on purpose: neither authors the
item. Writing a text file is a 4; writing one sentence into it is a 3.

The 3/4 line is not invented — two published standards draw it in the same place:

| | tier 3 | tier 4 |
|---|---|---|
| **HTTP** | `PATCH` — partial modification, unmentioned fields untouched (RFC 5789) | `PUT` — client sends the complete representation and replaces the resource (RFC 9110) |
| **CVSS v4.0 integrity** | `VI:L` — "modification of data is possible, but … **the amount of modification is limited**" | `VI:H` — "a **total loss of integrity** … able to modify any/all files" |

**Breadth is not on this ladder at all.** How many items a call reaches is
coverage, and blast radius is the primitive that scores it — so the rules read no
breadth vocabulary (`all`, `every`, `bulk`, `batch`, `multiple`), no glob, no
recursion switch and no scope selector, and the impact prompt does not mention
them either. A bulk variant and its singular describe the same *operation*. If the
model, reasoning freely on an abstention, rates a bulk tool higher anyway, that is
its judgement and it stands; nothing instructs it to.

## Vocabulary sizes

| Class | Patterns |
|---|--:|
| none | 16 |
| metadata | 52 |
| read | 46 |
| write | 122 |
| remove | 45 |
| **total** | **281** |

Plus 119 ambiguous single words (name-scoped), 10 generic read verbs, and 9
parameter detectors.

---

## Rule 1 · Which operation?

The most consequential class whose verbs fire wins:

```
remove  >  write  >  read  >  metadata  >  none
```

**Scope sub-rule.** A single word that is an action in a tool *name* but an
ordinary noun in prose is matched **against the name only** — 119 of them
(`branch`, `fork`, `push`, `email`, `notify`, `key`, `index`, `run`…).
Separators are normalised first, so `push_files` → `push files`.

Without it: `usergroups_list` scored *remove* because its prose says groups
"notify all members"; `users_search` scored *remove* because "email" is one of
its search fields; `list_commits` scored *write* because "branch" appears as a
noun.

**A multi-word phrase is not ambiguous.** The ambiguity problem is that one word
can be a noun; a phrase naming the verb *and* its object cannot be misread. So
phrases match across the whole description even when one of their words is on the
ambiguous list — which is how "Mark a channel or DM as read" is recognised at
all.

**No verb matched** ⇒ tier 3, confidence 0.35. That confidence is the abstention
signal: it is what hands the tool to the model under the v5 fallback rule.

## Rule 2 · A generic read verb is not evidence of content

`get`, `fetch`, `search`, `find`, `browse`, `lookup`, `retrieve`, `show`, `view`,
`query` say that *something* comes back — not *what*. When the only read evidence
is generic **and** a metadata verb also fired, the operation is metadata.

Worked: `get-freebusy` reaches 2 because "availability" is a metadata verb while
"get" and "query" are generic. `directory_tree`, `get_pull_request_status` and
`list_commits` resolve the same way. `read_file` still reaches 3, because `read`
is specific.

## Rule 3 · A write is ordinary unless it states a limit

The only question asked of a write is how much of one item this call authors:

| Declaration says | Tier | Confidence |
|---|--:|--:|
| it replaces the content — `overwrite`, `replace`, `rewrite`, `truncate`, `force-push`, "set the entire" | **4** | 0.8 — evidence |
| the amount is bounded — `append`, `add a comment/reply/line`, `patch`, `partial`, `specific fields`, `one field`, `selective` | **3** | 0.8 — evidence |
| **neither** | **4** | **0.35 — abstains to the model** |

The default is **4**, the ordinary write, because that is what a write is when
nothing says otherwise — PUT is the base case and PATCH is the qualified one. But
"bounded or not" is exactly the fact the declaration omitted, so the rules say so
and the model decides. "Create a new calendar event." is this case.

**An array parameter is not a signal either.** An array of attendees on
`create-event` is one event. `is_bulk` is still recorded — the assembly's
bulk-twin pass uses it to stop a batch variant scoring *below* its singular — but
it never promotes a tier.

## Rule 4 · Longest match wins

A match sitting inside a longer match from another class is not independent
evidence, and is dropped before precedence is applied. A class left with no
surviving span is not evidence at all.

"Mark a channel or DM as read" contains the word "read". The phrase describes the
operation; the word inside it does not.

## Rule 5 · A liveness probe is one that is NAMED one

Matched against the tool name only, so "…and their capabilities" in a
description cannot turn a read into a ping. `healthcheck` and
`get_server_version` are tier 1; `get_status` ("Get server health and version")
stays tier 2, because it is named for what it returns.

## Rule 6 · Parameters describe, they do not decide

Nine detectors over parameter *names* — `raw-query`, `raw-command`, `force`,
`glob`, `recursive`, `path`, `outbound`, `unbounded`, `dry-run` — recorded as
`capability_flags`. **None of them touches the tier** — `glob` and `recursive`
used to, but they are breadth signals, and breadth is not an impact question.

The reasoning: a parameter states what a caller **could** pass, and what any given
call **does** pass is a runtime fact. The `outbound` detector (`send_updates`,
`notify`, `webhook`, `to`, `cc`, `bcc`) captures the open-world signal without
letting it change a design-time score.

## Rule 7 · Annotations are evidence, never a bound

`readOnlyHint`, `destructiveHint` and `idempotentHint` are recorded. **None of
them moves the tier.** A hint that contradicts the description is followed by the
description, and the contradiction is written into the evidence trail.

> "annotations are not guaranteed to faithfully describe tool behavior, and
> clients **must** treat them as untrusted unless they come from a trusted
> server" — MCP spec
>
> "An untrusted server can lie. A server can claim `readOnlyHint: true` and
> delete your files anyway." — MCP blog, *Tool Annotations as Risk Vocabulary*

A ceiling would make the server the authority on its own risk score.

## What is deliberately absent

| Absent | Why |
|---|---|
| **Open-world / boundary crossing** | The channel is not the operation. "It is an email" says nothing about read/write/remove; sending *creates a message*, so it is a write. Whether a specific call leaves the organization is a runtime fact the dynamic stage can see. |
| **Any annotation ceiling** | See Rule 7. |
| **Per-tool patterns** | No rule in this file matches a tool name from the corpus. |
| **Behavioral baselines** | Not an impact question at all — it is the runtime primitive, and lives in the dynamic stage. |

## The assembly around these rules

Impact is one of three primitives. Two deterministic passes act on the *blast*
number afterwards, and both changed with this revision:

**Blast floors — three rules, ungated:**

```
asset sensitivity 5  ->  blast >= 4
asset sensitivity 4  ->  blast >= 3
tool impact       5  ->  blast >= 3
```

Reaching a crown-jewel asset at all is never a pinpoint consequence, and neither
is an irreversible call. The previous floors were **gated on impact ≥ 4**, which
is why `create-event` (impact 3) on a sensitivity-5 calendar kept blast 1 and
scored `5 × 1 × 3 = 15`. Ungating removes that hole. The old `impact 4 -> blast 2`
rule went with the gate.

These are now stated in the blast **prompt** as well as enforced in assembly, and
the asset's sensitivity and the tool's impact are handed to the model as decided
facts — so it produces a number that already respects them instead of one that
gets overwritten. `scripts/check_blast_floors.py` audits both after a scan: zero
violations, and a falling count of corrections as the prompt lands.

**Bulk-twin impact** stays: `impact(bulk) >= impact(singular)`. It is a
consistency rule, not a breadth promotion — it stops a batch variant scoring
*below* its own singular, which would be incoherent whatever the ladder says
about coverage.

**Blast roof — removed.** It capped non-escaping reads at 4. A roof can only ever
under-score, it existed to trim over-reads the older prompt produced, and the
floors now state the lower bound outright — so capping on top of them just fights
the rubric.

---

## Measured effect — 55 tools across calendar, github, slack

| Tier | previous rules | current rules |
|---|--:|--:|
| 1 | 1 | 1 |
| 2 | 13 | 14 |
| 3 | 16 | **18** |
| 4 | 19 | **18** |
| 5 | 6 | **4** |

The ladder is balanced again: removing breadth did not collapse it, because the
3/4 line now asks a different and better question. Three writes resolve to tier 3
**by evidence** — `add_issue_comment` ("comment"), `conversations_add_message`
("Add a message"), `usergroups_update` ("one field") — which is exactly the
"write one sentence" case.

**18 of 55 tools abstain** to the model: every write whose declaration does not
state a limit. That is where the rules would otherwise be guessing, and it is
where the LLM now decides — including whether a bulk tool deserves more than its
singular, since nothing in the prompt or the rules tells it either way.

**Three cases worth a decision before this is run:**

| Tool | was | now | The judgement |
|---|--:|--:|---|
| `merge_pull_request` | 5 | 3 | By operation a merge is a write; the code running afterwards is a different tool's operation. But this is the verb GitHub's own policy prohibits outright, and it now scores below a file read. |
| `create_or_update_file` | 5 | 3 | The single-tool regex is gone, which is right. It lands at 3 because its description says "a single file" and never claims replacement — arguably correct, arguably an under-read of "or update". |
| `search_repositories` | 2 | 3 | The one regression. The old container-noun list forced 2; now `search` is generic but no metadata verb fires, so it stays a content read. A repository search returns mostly names, so 2 was probably right. |

---

# Appendix — what the previous rules did, and why they went

The tier classifier grew one special case per tool that scored wrong. Each fixed
its example; none stated a principle.

| Removed | Verdict | Why |
|---|---|---|
| Annotation ceiling (`readOnlyHint: true` ⇒ ≤ 3) | REMOVE | A hint must not bound a risk score — see Rule 7. Also silently inert here: none of the three real vendor catalogs declares annotations, so it would have fired first on an unaudited server. |
| `destructiveHint` corroborates a 5 | REMOVE | Same principle, opposite direction. |
| `create[_ -]?or[_ -]?(update\|overwrite\|replace)` ⇒ 5 | OVERFIT | Matched exactly one tool in the corpus — GitHub's `create_or_update_file`, written into the rules with underscores made optional. |
| Return-shape cap 2: `free.?busy`, `busy blocks`, `colour ids` | OVERFIT | Two calendar tools named inside a rule claiming to be domain-agnostic. Rule 2 now reaches the same answer generally. |
| "The object decides" — 40 lines, three branches | OVERFIT | Its own code comment named the tools it existed for: `directory_tree` and `search_files`. Replaced by Rule 2, one sentence. |
| Container-noun list (14 nouns incl. `colou?rs?`) | NARROW | `colours` was there because the calendar server has `list-colors`. Subsumed by Rule 2. |
| Scoped-edit exception (`line-based`, `partial`, `specific lines`…) | NARROW | A phrase list taken from one filesystem tool's description. It **became the 3/4 boundary itself** — and inverted: breadth must now be claimed, rather than every write being assumed broad with an exception carved out. |

Also **reclassified out of "removal"**, because the old tier described the
*consequence* rather than the operation:

- `merge` · `rebase` · `commit` · `checkout` · `stage` — integrating a change is a
  write; the deploy that may follow is a different tool's operation
- `revert` · `rollback` · `cancel` · `restore` — undoing restores a state rather
  than removing one
- `overwrite` · `replace` · `force-push` — a full replacement is a broad write
  (tier 4), not a removal
- every outbound-send verb — see "What is deliberately absent"

## Sources

- MCP blog, *Tool Annotations as Risk Vocabulary: What Hints Can and Can't Do* —
  <https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/>
- MCP Tool Annotations (spec 2025-03-26) —
  <https://modelcontextprotocol.io/community/interest-groups/tool-annotations>
- MindStudio, *How to Classify AI Agent Actions by Risk: A Four-Tier Framework* —
  <https://www.mindstudio.ai/blog/classify-ai-agent-actions-by-risk>
- CSA, *NIST AI RMF Agentic Profile* (tool risk inventory: consequence scope,
  reversibility, authentication, compositional risk) —
  <https://labs.cloudsecurityalliance.org/agentic/agentic-nist-ai-rmf-profile-v1/>
- CVSS v4.0 Specification (integrity `VI:H` / `VI:L` definitions — the tier 3/4
  line) — <https://www.first.org/cvss/v4.0/specification-document>
- RFC 5789, *PATCH Method for HTTP* (partial modification; unmentioned fields
  untouched) — <https://datatracker.ietf.org/doc/html/rfc5789>
- MDN, *PATCH request method* (PATCH vs PUT semantics) —
  <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PATCH>
