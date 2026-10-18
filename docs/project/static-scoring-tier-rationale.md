# Static Scoring Tier Rationale

This explains the (currently uncommitted) changes to `src/mcp_security/
static_scoring/prompts.py`'s three scoring primitives — `tool_impact`,
`asset_sensitivity`, `blast_radius` — what changed in each definition, and
why, grounded in the rules and worked examples the prompts themselves now
state plus this project's own prior experiment history where it applies.
`docs/standards/scoring-prompts.md` is the generated, verbatim dump of the
prompts (do not hand-edit that file); this is the companion document that
explains the reasoning behind it.

## What changed, at a glance

| primitive | change | scope |
|---|---|---|
| `tool_impact` | tiers 3-5 renamed and reworded | the shared `nacombo` ladder |
| `asset_sensitivity` | public-data override added, with worked examples | the shared `_SENS_TIERS` ladder, used by every arm |
| `blast_radius` | rewritten from "fraction of asset reached" to reach-plus-escape-routes | the `nacombo`/`v5r` scope prompt |
| — | new `uframe` arm added | a parallel wording variant of all three primitives |

## Tool impact — generalizing past literal "writes"

Tiers 3-5 were renamed:

- `CONTENT READ or LIMITED WRITE` → `CONTENT ACCESS or LIMITED MODIFICATION`
- `WRITE` → `FULL MODIFICATION` ("the caller supplies what the item says" →
  "the caller controls the item's resulting contents")
- `REMOVAL or EXECUTION` → `DESTRUCTIVE or EXECUTING ACTION`

The pattern across all three: "write" implies literal content (bytes,
rows, message bodies); "modification" is broader and also covers
permission, configuration, and state changes that aren't content writes in
the literal sense but are the same *kind* of consequence (a bounded
permission grant is tier-3-shaped; a config overwrite is tier-4-shaped).
This generalization makes the ladder correctly classify tools whose
"content" is really settings or access grants, which a content-writing
vocabulary undersells.

**Worth flagging**: tier 5 also dropped its explicit `"moves money"`
example, replacing it with the vaguer `"perform an active operation"`. That
is a real scope broadening, not just a rewording — "active operation" is a
much looser trigger than a concrete money-movement example, and is worth
re-running the eval-vs-human-judge comparison on to confirm it isn't
pulling tools into tier 5 that shouldn't be there. The rule directly below
it (`"A write is FULL MODIFICATION (4) unless the declaration says the
amount is bounded (3)"`) still anchors the common case, so the risk is
narrower than it first looks, but it is a genuine widening of the tier-5
net that the old wording didn't have.

## Asset sensitivity — the public-data override

This is the best-evidenced change: it's a direct fix for a bug already on
record in this project's own history — public financial data (market
quotes, filed 10-K/10-Q statements, SEC Form 4 insider-trade filings,
central-bank/FRED series) was being over-scored as sensitive purely because
it concerned money, when it has no confidentiality left to lose at all.

The new rule states it explicitly:

> "PUBLIC-DATA OVERRIDE: data that is ALREADY PUBLIC ... is tier 1
> regardless of its TOPIC. 'Financial' is not 'confidential'."

Two mechanisms enforce this, not just a rule statement:

1. **The domain-inference stage (§0) now excludes public data from
   `dangerous_classes` by name**, with a `NEGATIVE` clause: *"PUBLIC data is
   NOT dangerous ... reserve it for NON-public secrets, PII, money-moving,
   or unpublished records."* This matters because `dangerous_classes` is
   what later escalates a tier — if public data were still allowed into
   that list upstream, the tier-1 override downstream would be fighting an
   escalation signal instead of having none to fight.
2. **A worked example from an unrelated domain** (freight-logistics, not
   finance) teaches the *shape* of the five tiers before the override rule
   is even stated, so the model has a working mental model of "public →
   1" that isn't anchored to the specific domain being scored.

## Blast radius — from "fraction of the asset" to reach-plus-escape

This is the largest change by far (the `blast_radius` task text roughly
tripled). The old model asked one question — *what fraction of this asset
does one call touch?* — and scored 1-5 purely on coverage. The new model
keeps coverage (tiers 1-4) but adds a fifth tier that is a **different kind
of question**: not "how much of the asset," but "does the consequence
*escape* the asset entirely," with three explicit, named escape routes:

- **(a) Total + irreversible** — the old top tier, unchanged in spirit:
  the whole asset destroyed with no path back.
- **(b) Hub cascade** — new. If the asset is a `dependency_hub` (something
  other systems authenticate against, load config from, or build/deploy
  from) and one call discloses, corrupts, or removes it *wholesale*, the
  compromise moves laterally into everything downstream — systemic even if
  the asset itself "looks recoverable." Disclosure is explicitly defined as
  returning the secret's actual contents; listing, enumerating, or reading
  metadata about it stays at tier 1-2, never 5(b).
- **(c) Complete population** — new. If the asset matches a
  `dangerous_class` (PII at scale, money-moving, regulated records) and one
  call reaches its *entire* subject population at once, that tops the
  scale regardless of the physical form the data takes (one file, one row,
  one query — "everyone at once" is what matters, not the container shape).

**Why this matters, concretely**: under the old fraction-of-asset model, a
single credential file is *physically* one small item — reading it looks
like reaching a small fraction of "the filesystem" as an asset, or at best
"the whole of a single-item asset" (old tier 4). But the actual
consequence of reading a complete, usable credential in full is systemic —
it unlocks whatever it protects, independent of how many bytes it
occupies. The new model separates these two questions on purpose: coverage
of the container (still tiers 1-4) versus escape beyond it (tier 5, route
b), so a physically tiny but functionally load-bearing secret can now score
5 without needing to also be "the whole asset" in a naive size sense. This
directly targets what this project's own blast-radius tuning history
already identified as **pinpoint-mutation under-scoring** — a small,
high-consequence change that the old coverage-only model had no way to
price correctly.

A second explicit correction in the same rewrite: **disclosure now
explicitly counts as reach, not just modification.** *"A read can therefore
reach as far as a write: a call that discloses a complete, self-sufficient
secret must NOT score below a call that overwrites or deletes that same
secret."* The reasoning given is that theft is silent and enables lateral
reuse, while destruction is at least detectable and recoverable — so a
model that only escalated blast for writes/deletes was systematically
under-pricing exfiltration relative to destruction.

The return schema grew an `escape` field (`"a"|"b"|"c"|"none"`) recording
*which* route fired, which makes a tier-5 score auditable rather than
opaque — a reviewer can check whether the asset genuinely matches a
`dependency_hub`/`dangerous_class` rather than trusting the number alone.

## The new `uframe` arm — isolating wording from the scale

`uframe` restates all three primitives — `ACTION IMPACT`, `ASSET
CONFIDENTIALITY`, `CONSEQUENCE SCOPE` — in different tier names, but with
the *same* five-level structure and (per the file's own header comment)
the same underlying scale at every tier as `nacombo`. The stated purpose:

> "a score difference from nacombo isolates wording alone, not the
> underlying scale."

This is a controlled ablation, not a new scoring philosophy: if scores
diverge between `nacombo` and `uframe` on the same tools/assets, the cause
is vocabulary alignment with an organization's own framework language, not
a real change in what's being measured. This is the same instinct already
behind this project's ISO/NIST/CIS scheme-alignment work
(`docs/standards/policy-scheme-alignment.md`) — `uframe` extends "does the
vocabulary we use change the number" to a fourth variant: the
organization's *own* words, rather than a named external standard's.

One real (not just cosmetic) change rides along in `uframe`'s blast-radius
relevance handling: when the organization's own asset register *lists* a
tool as reaching an asset, relevance is treated as settled — score the
reach, never return `null`. When it's *not* listed, the guidance is the
same "N/A is the more expensive mistake" principle `nacombo` already uses
elsewhere (a wrong low score is visible and arguable later; a wrong `null`
silently deletes the cell) — so this isn't a new philosophy, just the same
one applied to a register-driven relevance signal that `nacombo`'s version
of this prompt doesn't have access to in the same form.

## A consistent methodology: worked examples from an unrelated domain

Every new worked-example block added in this update — freight-logistics
for asset sensitivity, a security-operations/SIEM example for blast
radius, a support-ticket triage example for the behavioral baseline —
deliberately uses a domain the prompt is *not* scoring, so the model learns
the shape of the reasoning rather than pattern-matching on nouns from the
actual evaluation corpus. This is the same discipline already documented
elsewhere in this repo for a different pipeline (`docs/standards/
input-typing.md`: *"Illustrations use argument names that appear in no
server under test... names drawn from the evaluation corpus would be
answers to the test"*) — worth naming explicitly here because it means this
update is following an established, previously-validated project
convention rather than introducing a new one.

## Open questions worth verifying before committing

- Tier 5's broadened `"perform an active operation"` wording (see above) —
  re-run against the existing human-judge comparison
  (`scripts/evaluate_vs_human.py`) to confirm it doesn't pull tools into
  tier 5 that the old, narrower wording correctly left at tier 4.
- The blast-radius rewrite is large enough that it should be re-scored
  against the same held-out set used for the prior blast-radius tuning
  rounds (`ctx` / `floor` / `rowfix`) before treating the pinpoint-mutation
  fix as confirmed rather than theoretically sound.
- `uframe` is only useful once it's actually run against the same
  tools/assets as `nacombo` and diffed — right now it's a hypothesis
  (wording-only divergence) that hasn't been tested against real scores
  yet.

## References

- `src/mcp_security/static_scoring/prompts.py` — the source of truth; this
  document explains it, `docs/standards/scoring-prompts.md` dumps it
  verbatim (regenerate via `scripts/dump_scoring_prompts.py`).
- `src/mcp_security/static_scoring/pipeline.py`, `tests/static_scoring/
  test_policy_frameworks_v7.py` — also touched by the same uncommitted
  change; not covered in depth here.
- `docs/standards/policy-scheme-alignment.md` — the prior ISO/NIST/CIS
  wording-sensitivity experiments `uframe` extends.
- `docs/standards/input-typing.md` — the source of the "worked examples
  from an unrelated domain" convention this update reapplies.
