<!-- sha256: 90e5685a67d4923e3299c5350c0c727fbd0b3394dee8fa196eaab12a259559d1 · source: docs/standards/tool-input-features.md -->

# Tool Input Feature Ledger

For each argument an MCP tool declares, decide a small set of **independent
properties** of its value — not one exclusive class. An argument can be
several true things at once: an `attendees[]` array is a count (its length)
stacked on top of a population (each attendee identifies someone). Forcing
one label per argument loses that.

Derived statically, from the tool registry alone. No risk, no severity, no
bands, and no thresholds — this pass never decides that a specific value is
low, medium, or high, and never says a value is dangerous. It only decides
**which property of the value could make one instance more significant than
another, and how that should be evaluated later.**

## What you are given, and what you are asked

You are given two things as **facts**, already decided without you — reason
from them, do not re-derive them:

- **`tool_context`**: the tool's atomic operation tag(s) (e.g. `READ`,
  `DELETE`, `CREATE`) from this project's rule-based operation classifier.
  The same argument name can mean something different depending on this —
  `file_id` in a `READ` tool is not the same stakes as `file_id` in a
  `DELETE` tool, and that difference comes from the tool, not the
  identifier.
- **Per-argument structural facts**: `cardinality` (scalar/array, with
  declared `min_items`/`max_items`), `domain` (closed/open), declared
  `bounds` (minimum/maximum/minLength/maxLength/pattern/format), `required`,
  `default`, and the argument's own `description` text. These come straight
  from the schema. Trust them; do not restate or contradict them. `Tool:`
  below is the tool's name and description only — everything schema-derived
  is already in these structural facts, so the raw `input_schema` is not
  repeated.

You are asked to decide, for each declared argument:

### B. Reasoned feature flags (independent, not exclusive)

```
orderable              comparing two values means more / larger / later
selects_population     picks one entity out of a set the caller only partly owns
expands_reach          could make the call touch more than one thing,
                        REGARDLESS of whether the value is numerically large
                        (a boolean switch can expand reach with no magnitude at all —
                        this is a different question from orderable, not a restatement)
composes_new_content   the caller is inventing this value
references_existing    the caller is pointing at something that already exists
                        (composes_new_content and references_existing are usually,
                        but not always, opposites — a value can do neither, e.g. a
                        pure operational switch)
provenance             caller_composed | caller_copied | system_opaque —
                        where would a normal caller get this value from?
commits_change         participates in a create/update/delete, vs. a pure read
scope_multiplier       changes how broadly ANOTHER argument's effect applies,
                        without naming a target itself
```

Deciding rules:

1. An identifier has no meaningful order: a higher id is not more of
   anything. `selects_population` does not imply `orderable`.
2. `expands_reach` is about scope, not size. A value with no magnitude at
   all (a boolean, a fixed enum) can still expand reach — judge it
   separately from `orderable`.
3. Free text a person reads is normally `composes_new_content: true` and
   everything else `false` — do not invent a policy or magnitude reading for
   prose just because the field is long or consequential.
4. `provenance: system_opaque` is for values a normal caller only ever
   copies verbatim from an earlier response (a cursor, a returned id, a
   sha) — distinct from `caller_copied`, which is a value the caller picked
   from something they already know (an existing username, a known
   channel), and distinct from `caller_composed`, which the caller invents
   fresh.
5. `scope_multiplier` is rare. Ask: does this value, by itself, name
   nothing — yet change how far a sibling argument's effect reaches (e.g. a
   `modificationScope: thisEventOnly|all` on a recurring event)? If the
   value names its own target, it is not this.
6. When ambiguous, read the tool's purpose and its sibling arguments before
   deciding. If it stays ambiguous, set the flag `false`/omit it rather
   than guessing — say so in `reason`.
7. Being categorical does not make something `selects_population`. A small,
   closed set of operational modes (`visibility: default|public|private|
   confidential`, `merge_method: merge|squash|rebase`) is normally not
   `selects_population` — the question is whether choosing a different
   option changes WHICH subject, resource, or account the call acts on, not
   merely how it behaves. It usually takes an open or large `domain`
   (structural fact) for `selects_population` to apply; a small `enum`
   should make you look twice before setting it `true`.
8. **`reason` is never empty.** One clause naming the specific fact that
   drove your decision (a structural fact, the description's wording, or a
   sibling argument) — not a restatement of the flags themselves. A reply
   with a blank `reason` on any argument is rejected and re-asked, so do not
   economize here even on an argument that looks obvious.

### C. Dynamic-hook flags — what would be worth tracking later, never computed here

You are not given any traffic and must not invent frequencies, counts, or
percentiles. You are only judging whether a given runtime signal would be
*meaningful* to track for this argument at all.

```
track_rarity            worth comparing this value against how often it has
                         been seen before (meaningful mainly when
                         selects_population holds over a large, open domain;
                         meaningless for a 2-value boolean)
track_concentration     worth checking how many DISTINCT callers normally
                         use this exact value (a value normally shared
                         broadly, suddenly used by only one caller, is a
                         different signal than a value only one caller ever
                         uses)
track_temporal_pattern  worth comparing the call's time-of-day/day-of-week
                         against the caller's own baseline (more meaningful
                         when commits_change is true than for read filters)
track_pairing           this argument's real meaning only emerges jointly
                         with a named sibling — list the sibling argument
                         name(s), or omit if none
```

## D. Cross-argument composites (once per tool, not per argument)

After describing every argument, answer one more question about the tool as
a whole: which *pairs or groups* of its arguments only become meaningful
together? A `start` and `end` pair only means "how long" read jointly;
neither alone carries that. An absent filter alongside a high `limit` means
something different from the same limit with a narrow filter.

Return `composites: []` if none apply — do not force one.

## What this pass does not attempt

- It never assigns low/medium/high or any numeric threshold to a value.
- It never decides that a specific value (a country, an amount, an id) is
  itself risky.
- It does not attempt a "does this value flow into a shell/SQL/filesystem/
  URL sink" judgment. That depends on what the tool does with the value
  internally, not on the argument's own schema — the schema under-determines
  it, so do not guess.

## Output

Output ONLY valid JSON, no prose, no fences:

```json
{"tool_name": str, "arguments": [{
  "path": str,
  "orderable": bool,
  "selects_population": bool,
  "expands_reach": bool,
  "composes_new_content": bool,
  "references_existing": bool,
  "provenance": "caller_composed" | "caller_copied" | "system_opaque" | null,
  "commits_change": bool,
  "scope_multiplier": bool,
  "track_rarity": bool,
  "track_concentration": bool,
  "track_temporal_pattern": bool,
  "track_pairing": [str],
  "reason": str,
  "confidence": 0.0
}], "composites": [{"args": [str], "meaning": str, "note": str}]}
```

Describe every argument the tool declares, including nested ones, and none
that it does not. Use a dotted path for nesting, with `[]` for a list's
items (`files[].path`).

Tool context: `{tool_context_json}`

Structural facts (per argument, from the schema): `{structural_facts_json}`

Tool: `{tool_json}`