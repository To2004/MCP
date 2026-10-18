# Asset description rules and framework guidance

Concrete authoring rules for the asset register's `Description` cell, and
which of the three v7 framework arms (ISO / NIST / CIS) to write a policy
against when the choice is open. Both come from the same source: the
`five_level_v2_v7_*` experiment, which rewrote `github_helios`, `slack_vireo`
and `calendar_aurora` across all three frameworks, found two real scoring
regressions, fixed them, and measured the effect. Everything below is a rule
*because* a specific mistake produced a specific, measured error — not a style
preference. See `docs/mcp-tools/server-policies-{iso,nist,cis}.md` for the
register shape these rules apply to, and `docs/standards/mcp-policy-spec.md`
for the block structure they slot into (Block 3, Asset register).

## The four-part description

Every asset register row's `Description` cell should contain, in order:

1. **What it is.** One clause naming the information TYPE the row covers —
   content the system characteristically carries, not a container it happens
   to live in (see "Virtual assets" below).
2. **Why it classifies this way**, if it isn't obvious from (1). Adverse-impact
   or disclosure language belongs here — this is legitimate input to the
   *sensitivity* stage, which is supposed to read tone and consequence.
3. **`Reached by:`** one clause per tool in the row's `Tools` column, each as
   `` `tool_name` (mechanism, plain reach fact, ≤10 words) ``. This clause is
   read by the *blast* stage too, and blast prices reach only — see "Reach vs.
   value" below for why this half must stay mechanism-only.
4. **An escalation note**, if any tool in the row grants access without
   returning content itself (a join, an admin/link verb). State explicitly
   that it enables the other tools' reads — see "Escalation tools" below.

## Reach vs. value: keep them in separate clauses

**The mistake:** early versions of the `slack_vireo` CIS register described
`broadcast-information`'s `conversations_add_message` as "posts — the spoofing
risk, since posting here carries organizational voice", and
`workspace-catalog-metadata`'s `channels_list` inherited "the channel list
discloses which studies... are live" from the row's own description. Both
phrases are true and belong in the classification clause (2). Repeating them
inside the `Reached by:` clause (3) — meant to be pure mechanism — measurably
pulled blast scores up on tools that should have scored low: `conversations_unreads`
and `channels_list` moved from blast 2 (`nacombo`) to blast 4 under CIS once
that language was present, compressing them into the same band as actual
content-read verbs and dragging the CIS arm's blast-rank-correlation with
`nacombo` down from 0.76 to 0.66 on `slack_vireo`.

**The rule:** classification language (why an asset is Sensitive/Confidential)
goes in clause (2) only. `Reached by:` clauses (3) state what a tool
*mechanically does* — reads, writes, lists, searches, joins — never why that
matters. Stripping the redundant phrasing back out (`docs/mcp-tools/server-policies-cis.md`,
commit history) recovered roughly half the gap (0.66 → 0.71) without touching
anything else.

**Why this matters more on a coarse scheme.** A 2-3 level scheme (CIS
Safeguard 3.7's minimum, "enough to differentiate sensitive from other data")
gives the classifying model less procedural structure per word than a 4-5
level scheme with an explicit multi-criteria test (ISO A.5.12's four criteria;
FIPS 199's {C,I,A} triple). With less structure to lean on, evaluative
language in the wrong clause is more likely to bleed into an unrelated
judgement. Apply this rule everywhere, but audit CIS-shaped policies hardest.

## Virtual assets, not named containers — unless the container list is itself routine

Default every asset to an information TYPE (`unblinding-information`,
`ot-cyber-system-information`), not a named channel, repository, or calendar.
Two reasons, both evidence-backed:

- **The org's own container inventory is usually the sensitive fact.** Every
  real policy this project examined (`docs/mcp-tools/real-policy-examples/`)
  classifies information by type, never by naming the systems that hold it —
  Leeds Beckett, UC Denver, Connecticut, Brunel all publish a classification
  *procedure* applied to data, not a directory of named systems. A synthetic
  register that names channels/repos is disclosing more than any real
  organization in this survey actually does.
- **A tool's `Tools` cell duplicates across virtual rows anyway.** Slack's
  `conversations_history`/`replies`/`search_messages`/`add_message` are
  generic content I/O — the same four verbs appear against every content-type
  row because any one of them can reach whatever channel the caller names.
  The register was never really binding a verb to one container; it was
  always the recognition rules (asset→class from content) doing the work.
  Naming the container was cosmetic.

**Exception:** when the container list itself is routine to publish (Aurora's
calendar list — "the container list is routine" — vs. Vireo's channel list,
which is explicitly withheld because it discloses which studies are running),
container-level rows for pure catalog/metadata state are fine. Content rows
still classify by type.

## Escalation tools must be listed on every asset they enable

**The mistake:** `conversations_join`/`conversations_leave` return no content,
so an early rewrite moved them off every content-type row onto a dedicated
access-state row. That broke the register's most important fact:
`conversations_join` succeeds on any channel with no invitation (verified —
see the Access restriction rules in each Slack section), so it is the actual
mechanism that reaches `unblinding-information`. With it removed from that
row, `nacombo`'s blast=5 for `conversations_join` against the equivalent asset
fell to blast=2 under the rewritten arms — the single biggest error in the
whole experiment (rank correlation 0.40-0.49 on `slack_vireo`, vs. 0.76-0.98
on the other two servers that had no such tool).

**The rule:** a tool that grants access without itself carrying content
(join, leave, link, admin) must appear in the `Tools` column of *every*
content-type row it can expose — not just an access-state row — with a
`Reached by:` note stating explicitly that it enables the other tools' reads.
Restoring this (all three arms) brought `slack_vireo`'s blast correlation to
0.71-0.76 and its cross-arm agreement (ISO vs. NIST vs. CIS on each other) to
100% within one tier, 0 two-tier splits — the best of any server measured.

## Split read-only state from mutable state, even when they look related

**The mistake:** one row (`access-control-state`) originally carried both the
mutable group-membership verbs (`usergroups_create`/`update`/`users_update` —
unauthorized, Sensitive) and the agent's own read-only membership lookup
(`usergroups_me`, `channels_me`). The row's blast score, driven by the write
verbs' description, applied to the read-only tools too: `usergroups_me` scored
blast=5, though it can only ever return the caller's own membership — one
item, no mutation, structurally incapable of reaching further.

**The rule:** when a set of tools sharing an apparent theme differ in kind
(read-only vs. mutable, own-state vs. others'-state), give them separate rows
even if it doubles the row count for that theme. Splitting `access-control-state`
into `access-control-write-state` and `agent-membership-read-state` dropped
`usergroups_me` to blast=1 — the correct floor — without any other row moving.

## Framework guidance: which to write against

Ranked by how reliably a scanner can *derive* correct severities from the
resulting document — not by real-world popularity or ease of certification.
Full numbers in `reports/experiments/v7/FRAMEWORK_RESULTS.md`.

| | **NIST** (FIPS 199 / SP 800-60) | **ISO** (A.5.9 / A.5.12 / A.8.3) | **CIS** (Safeguard 3.2 / 3.3 / 3.7) |
|---|---|---|---|
| Blast-rank correlation with `nacombo`, across all three servers | 0.76-0.98 (best or tied-best on every server) | 0.72-0.91 | 0.71-0.93 (weakest on 2 of 3) |
| Why | {C,I,A} scored on three axes independently, then high-water-marked — forces per-axis reasoning before a single number is produced | A.5.12's four criteria (legal, value, criticality, disclosure-or-modification) is the second-most explicit procedure; richest real-world citation depth found (Leeds Beckett, Brunel) | Safeguard 3.7 requires only "enough levels to differentiate sensitive from other data" — by design, the least procedural scaffolding of the three |
| Real-world grounding | Real disclosures found (UC Denver, Connecticut) are consistently strong, sole-framework, often ship worked examples | Real disclosures vary widely in depth (Leeds Beckett: deep; Brunel: middle; Warwick: standard-name only) — pick a strong reference, don't assume "ISO-certified" implies control-level detail | **A pure CIS-primary disclosure essentially does not exist publicly** — three independent searches found only joint-framework mentions (Nevada, San Joaquin County, NYC all cite CIS alongside NIST/ISO, never alone) |
| Use when | Default choice for scanner-facing policy | Org is genuinely ISO-certified and you want the richest accountability columns (`Owner`) | Org is a genuine CIS-Controls-primary shop; compensate with the reach-vs-value rule above, since the framework's own minimalism is what causes the fragility |

**Default recommendation: write against NIST unless the target org is
demonstrably ISO- or CIS-primary.** If CIS is the only honest choice, expect
to do more manual work holding reach language out of classification-flavored
clauses than the other two frameworks require.

## References

- `docs/standards/mcp-policy-spec.md` — the block structure (register shape,
  conformance levels) these rules apply within.
- `docs/standards/policy-scheme-alignment.md` — which register fields each
  framework already requires vs. what has no standards home (the `Tools`
  column and the flags).
- `docs/mcp-tools/real-policy-examples/README.md` — the real-world policy
  corpus (ladder + framework set) these rules are grounded in.
- `reports/experiments/v7/FRAMEWORK_RESULTS.md` — the full comparison numbers
  behind the framework guidance table above.
- `scripts/check_policies.py` — mechanical conformance checks (register
  parses, no leaked sensitivity numbers, total tool coverage). Does not yet
  check the rules on this page; they are currently enforced by review, not by
  the checker.
