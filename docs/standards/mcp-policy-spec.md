# MCP Server Policy Spec v1 (scheme)

How an organization describes one of its MCP servers **when it will not release
per-asset sensitivity judgements**. The profile spec's design rule is "the tool
supplies the inventory, the org supplies the judgement" — one filled table row
per asset, including the 1–5 number. This spec is its realistic-disclosure
counterpart: the org **does** list its assets (an asset register: id, small
description, which tools operate on it, optionally CIA emphasis) but supplies
**no sensitivity numbers** — the judgement comes as policy rules, and the
scanner derives per-asset sensitivity and per-tool×asset blast radius by
applying the rules to the register and to whatever else it enumerates.

This document defines the scheme only. Content for each organization is written
against it in [`docs/mcp-tools/server-policies.md`](../mcp-tools/server-policies.md).

## What the scanner must derive, and what that requires

Two scoring primitives have to come out of policy text alone:

**1. Asset sensitivity** (per enumerated asset, 1–5) decomposes into:

| Sub-problem | Who can supply it | Policy block that carries it |
|---|---|---|
| What the assets ARE | The org — the list itself is shareable; only the judgement is withheld | **Asset register**: id, small description, tools, optional CIA |
| Calibration: class → severity | Split: the org states each class's **consequence of loss** in its own words (statutory breach, patient injury, embarrassment); the **scanner** maps that language onto its 1–5 rubric | Classification table — no numbers in it |
| Classification: asset → class | The scanner, using each register row's description plus the org's recognition knowledge | **Asset recognition rules** applied to the register |
| Composition: scopes, populations, metadata | The org (structural judgement enumeration can't make) | **Aggregation rules** inside the recognition block |

**2. Blast radius** (per tool × asset) decomposes into:

| Sub-problem | Policy block that carries it |
|---|---|
| Which tool works on which asset | **Tools column of the asset register** (exact mapping) |
| Which operations touch which classes (generalizes to unlisted assets) | **Tool operation matrix** |
| Reach of one call (record / scope / store) | Reach column of the matrix |
| Escalation beyond nominal reach | **Blast escalators** |

The bridge insight: an org cannot enumerate its assets for you (the inventory is
sensitive and goes stale), but it **can** state the rules by which its own staff
recognize and handle each class — and rules generalize to assets that did not
exist when the policy was written. That is strictly more durable than a labeled
inventory.

## Required structure

One `### <stem>` section per server. The parser
(`mcp_security.static_scoring.server_profiles`) keys on the heading and the
``**Tier: X** · `server-id` `` fact line, same as profiles. A policy section
must NOT contain an `| Asset | Sens. |` table — the per-asset sensitivity
number is the judgement the org declines to give, and its absence is what makes
profile-sensitivity modes fail loudly if misdirected here. The asset register's
header (`| Asset | Description | Tools | CIA |`) deliberately has no `Sens.`
second column, so the profile parser cannot mistake it for an inventory.

### Block 1 — Organization & disclosure posture (`**Company.**`)

Who runs the server, the regulatory regime that prices a loss (PCI-DSS, HIPAA,
privilege — or "unregulated"), and **why the inventory is withheld** (it maps
the cardholder environment; filenames are themselves PHI; repo names map the
estate). The withholding reason is load-bearing: it tells the scorer which
*metadata* is already sensitive.

### Block 2 — Data classification policy (table)

The Stanford/Berkeley shape — one row per class, three cells. **Cover the whole
range.** A four-class ladder (Restricted / Confidential / Internal / Public)
leaves the scanner no class between "recoverable embarrassment" and "already
published", so metadata surfaces — container listings, read/RSVP state, schema —
have nowhere to land and get pulled up into Internal. If the server exposes any,
give them their own class (a *Routine* row: "a shrug: knowing a container or a
state exists, with no content behind it"). This is the single most common cause
of a policy scan over-scoring listings.

| Column | What it states |
|---|---|
| Class | The org's own class names (Restricted / Confidential / Internal / Public, or local equivalents) |
| Definition (adverse impact) | What actually happens when this class leaks / is altered / is lost, in the org's words — statutory breach, patient injury, privilege waiver, embarrassment. This is the severity signal. |
| Examples | What belongs in the class on THIS server, by type, never by path |

**No numbers.** The org never writes a 1–5 — not per asset and not per class.
The scanner derives sensitivity itself: it classifies each asset (Blocks 3 + 4),
then maps the class's *adverse-impact language* onto the scoring rubric's own
1–5 scale. The org supplies consequences in its vocabulary; the rubric owns the
scale. Per-asset CIA lives in the register, not here.

### Block 3 — Asset register (table)

The asset list the org CAN share — everything except the judgement number.
One row per asset:

| Column | What it states |
|---|---|
| Asset | The asset id (calendar, table, directory, channel, repo, surface) |
| Description | One line: what this asset is and what it holds — the raw material the recognition rules classify |
| Tools | Which of the server's tools operate on this asset ("what tool works on what asset") — the exact tool×asset homing the blast stage scores. `—` is a legitimate value: nothing on this server reaches the asset, and the scan marks its whole row N/A |
| Flags | *(optional)* structural properties from a closed vocabulary: `hub`, `population`, `self-sufficient`, `completeness-is-the-asset`, `metadata-only`, `public` |
| CIA | *(optional)* which axis carries the loss for this asset, e.g. `C>I>A` or `C:H I:M A:L` |

**Why `Flags` is still policy-grade.** A flag states what an asset *is* — other
systems authenticate against it, it holds a whole population of subjects, it is
already published — not what it is worth. It is the same kind of structural
judgement as the `Tools` column: enumeration cannot make it, the org can state
it, and it generalizes. Two scoring mechanisms consume it: the v4/v5 blast rubric
requires a tier-5 award to cite one of `hub` / `population` / `self-sufficient`
(so a tier-5 "escape" is sanctioned by the organization rather than inferred from
prose adjectives), and the deterministic blast roof exempts flagged assets from
its read cap. A register with no `Flags` column parses; every asset is then
unflagged and its reads cap at blast 4.

What the register must NOT contain: a `Sens.` column. The org states facts
(what exists, what touches it, where the loss axis lies); the scanner derives
the 1–5 by applying Blocks 2 + 4 to the Description cell. The register also
does not exempt the scanner from enumeration: assets it finds that have no row
fall to the recognition rules and the fail-closed default.

### Block 4 — Asset recognition rules (`**Asset recognition rules.**`)

The asset→class bridge; without it the classes never attach to anything real.
Applied to
each register row's Description, and to anything enumerated that has no row.
Bulleted rules in four groups, each phrased so it applies to assets that don't
exist yet:

1. **Recognition cues** — naming and location conventions (`secrets/`,
   `*_vault`), structural markers (a channel's `private` flag, column names like
   `ssn`/`token`, repo topic labels), content-type cues (key material, PAN
   formats, chart/prescription text).
2. **Metadata rule** — whether names, titles, or attendee lists alone already
   carry the class (patient filenames = PHI; executive calendar titles disclose
   deals). Decides how to score enumeration/list/search surfaces.
3. **Aggregation rules** — a container ranks at least as high as the most
   sensitive thing it reaches (the FIPS 199 high-water mark); a scope holding a
   whole population of Class-X records ranks a step above one record; a
   **combination rule** for the mosaic effect — individually innocuous types
   that classify higher when joined (account number + identity, name + diagnosis
   date), which SP 800-60 lists as the most common reason a provisional impact
   is adjusted upward; append-only records whose value is completeness;
   credentials that are complete and usable alone.
4. **Default class** — what an unrecognized asset is treated as. Must be
   fail-closed (state the class explicitly).

These are the per-org, prose equivalent of the security team's global anchor
tables in `mcp_security/sensitivity.py` (`DIR_SENSITIVITY`,
`DB_COLUMN_ANCHOR`, …) — same idea, but published by the org that owns the data.

### Block 5 — Operation limits (`**Operation limits.**`, brief)

Blast radius is the *scanner's* job, not the policy's — the register's Tools
column already gives it the exact tool×asset homing, and reach/escalation are
scored from the tool catalog. The policy contributes only what the org alone
knows, in a few lines: operations prohibited outright (bulk verbs, account
administration), operations needing human confirmation, and effects that
cannot be undone (deletes, outbound sends). No matrix, no escalator taxonomy.

### Block 6 — Expected use & prohibitions

`**Expected organizational use.**` — the sanctioned workload (baseline stage
reads this), always scoped ("one record at a time, addressed by id").
`**Prohibited agent behavior.**` — violations by kind, not degree.

### Block 7 — Loss priorities

One line: C/I/A ordering for the server and where each axis concentrates.

## Length

Real classification standards (Stanford's risk classifications, Berkeley's
P1–P4) are a single table of class · adverse-impact definition · examples,
plus short usage guidance. Match that: **the two tables carry the content;
every prose block is a few lines**. A section that outgrows a page is doing
the scanner's job for it.

## How the blocks map to scoring stages

| Scoring stage | Reads |
|---|---|
| Domain/profile inference | Block 1 |
| Asset sensitivity | Blocks 2 + 3 + 4 — the core: classify each register row (and anything unlisted) via the recognition rules, map the class's adverse-impact language onto the rubric's 1–5, adjust by aggregation |
| Tool impact | Blocks 2 (CIA) + 5 + 7 |
| Blast radius | Block 3's Tools column (exact homing) + the tool catalog; Block 5 only adds the org-known limits |
| Behavioral baseline | Block 6 |

Consequence for scoring modes: with Blocks 2–4 present, sensitivity is
derivable **by the scanner** — no org-supplied number anywhere — so the policy
scan can keep the sensitivity primitive (`sens × blast × impact`, max 125)
instead of the desc-mode's `blast × impact` (max 25). Which mode the policy
experiment runs is an open decision recorded in the experiment notes — this
spec only guarantees the inputs for both.

## Section skeleton

```markdown
### <stem>

**Tier: M** · `<server-id>` · <n> tools · policy-only disclosure

**Company.** <org, regime, why per-asset judgements are withheld>

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | <what actually happens: statutory breach, injury, …> | <types> |
| Confidential | ... | <types> |
| Internal | ... | <types> |
| Routine | <a shrug — include this row if the server exposes metadata surfaces> | <listings, schema, read/RSVP state> |
| Public | ... | <types> |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `<asset-id>` | <one line: what it is, what it holds> | `<tool-a>`, `<tool-b>` | `hub` | C>I>A |

**Asset recognition rules.** <one compact paragraph: cues per class ·
metadata rule · aggregation rule · **Default: <class>**>

**Operation limits.** <a few lines: prohibited outright · needs confirmation ·
cannot be undone>

**Expected organizational use.** <sanctioned workload, scoped, 1–2 lines>

**Prohibited agent behavior.** <violations by kind, 1–2 lines>

**Loss priorities.** <one line: C/I/A ordering>
```

## Conformance

- **P0** — prose-only policy (classes described; no register).
- **P1** — Blocks 1, 2, 3 present: classification table (no numbers) plus the
  asset register with Description and Tools cells filled.
- **P2** — all seven blocks present; recognition rules state a fail-closed
  default; every tool of the server appears in at least one register row's
  Tools cell (or is explicitly noted as touching no asset).

`scripts/check_policies.py` enforces this: the fact line parses; there is NO
`| Asset | Sens. |` table anywhere; the register parses with unique ids and only
known `Flags` values; at P1+ the register's Tools cells reference only tools the
server actually advertises; at P2 tool coverage is total (a tool touching no
asset must say so in prose) and a `**Default: <class>**` recognition rule exists.

```
uv run python scripts/check_policies.py [--server calendar_real]
```

## Grounding in established practice

The scheme is not invented — each block mirrors how real organizations already
publish this information without releasing inventories:

- **Block 2 (class → consequence)** is SP 800-60's *provisional impact per
  information type* with the numbers left to the assessor — the org describes
  the consequence, the categorizer (here: the scanner's rubric) assigns the
  level. Every corporate Restricted/Confidential/Internal/Public ladder with
  handling levels has this shape.
- **Block 4 (recognition rules)** is how DLP/auto-labeling actually works:
  Microsoft Purview applies sensitivity labels via *conditions* — sensitive
  information types (pattern + keyword detectors) and classifier matches,
  including multi-condition combinations — never via a hand-labeled file list.
  Orgs demonstrably can and do author recognition rules.
- **Block 4 aggregation** is SP 800-60's *adjustment* step (aggregation raises
  impact; "sensitivity is greater in context than in isolation") plus the
  FIPS 199 high-water mark; the mosaic/combination rule matches TOP-R's finding
  that individually authorized low-risk calls compose into high-risk synthesis.
- **Block 5 operation limits** align with published blast-radius models: data
  reachable, actions executable, downstream/outbound recipients, and
  **persistence mechanisms** (session-scoped vs open-ended effects) — the
  last being the least-understood factor and the reason hub/config changes
  outrank their nominal byte-count.

See [`nist-guidelines.md`](nist-guidelines.md) and
[`Literature_review/risk_scoring_frameworks_survey.md`](../../Literature_review/risk_scoring_frameworks_survey.md).

## References

Internal:

- Inventory-grade counterpart: [mcp-profile-spec.md](mcp-profile-spec.md)
- Policy content: [`../mcp-tools/server-policies.md`](../mcp-tools/server-policies.md)
- Global anchor tables this scheme localizes per-org:
  `src/mcp_security/sensitivity.py`
- Atomic-op taxonomy: [atomic-op-classification.md](atomic-op-classification.md)
- NIST summaries: [nist-guidelines.md](nist-guidelines.md);
  blast-radius literature:
  [`Literature_review/risk_scoring_frameworks_survey.md`](../../Literature_review/risk_scoring_frameworks_survey.md)

External sources this scheme is modeled on:

- Stanford University, *Risk Classifications* —
  <https://uit.stanford.edu/guide/riskclassifications> (class · definition ·
  examples table; the Block 2 shape)
- UC Berkeley ISO, *Data and IT Resource Classification Standard* (P1–P4) —
  <https://security.berkeley.edu/data-classification-standard> (adverse-impact
  definitions per level; the Block 2 severity language)
- NIST FIPS 199 — CIA × impact levels and the high-water mark (Block 4
  container rule)
- NIST SP 800-60 (Vol I/II) — information type → provisional impact +
  adjustment factors, aggregation chief among them (Blocks 2 + 4) —
  <https://csrc.nist.gov/pubs/sp/800/60/r2/iwd>
- Microsoft Purview, *Apply a sensitivity label automatically* —
  <https://learn.microsoft.com/en-us/purview/apply-sensitivity-label-automatically>
  (label-by-condition; the Block 4 recognition-rule shape)
