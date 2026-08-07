# MCP Server Profile Spec v1

How an organization describes one of its MCP servers so the risk scanner can
score it. A profile is the org's own statement of what the server holds, how
severe each asset is, and what agents are supposed to do with it — the inputs no
amount of reading the tool catalog can supply.

The design rule is **the tool supplies the inventory, the org supplies the
judgement**. Nobody hand-types asset ids or column lists: the scanner enumerates
the store and emits a skeleton, and the author fills in four cells per row. This
keeps profiles authorable by people who know the business rather than the
codebase, and keeps them from drifting away from the real store.

## Authoring loop

```
1. emit     scanner walks the store  →  skeleton with Asset + Contents pre-filled
2. fill     the org supplies Sens. · C · I · A · Why + the prose header
3. check    validator runs coverage + schema + lint
4. scan     the scan reads the profile; sensitivity is never asked of the model
```

Step 1 is what makes this adoptable: an org never has to guess what the scanner
will call an asset. Step 3 is what keeps it honest — a scan **aborts** rather
than guessing at an asset with no row.

## Required structure

One `### <stem>` section per server. Two parts: a prose header and an asset
table. Both are mandatory at conformance level 2 and above (see below).

### Prose header

| Field | Required | What it states |
|---|---|---|
| `**Tier:**` fact line | yes | `**Tier: <XS-XL>** · `<server-id>` · <n> tools · <n> assets` — the parser keys on the backticked server id |
| `**Owner.**` | yes | The team accountable for this server, and a contact. A profile with no owner cannot be challenged. |
| `**Purpose.**` | yes | What the server is for, in the organization's own words. |
| `**Expected agent use.**` | yes | The sanctioned workload, and explicitly what an agent should **never** need. This is what deviation is measured against. |
| `**Content unit.**` | yes (L3) | What "one item" concretely is here — a row, a file, a message, an event. Reach is counted in these units. |
| `**CIA priority.**` | yes | The overall ordering (`C > I > A`), with one sentence of why. |
| `**Provenance.**` | yes | Author, date, and which version of the store was reviewed. |

### Asset table

```
| Asset | Sens. | C | I | A | Contents | Why |
```

| Column | Type | Rules |
|---|---|---|
| `Asset` | backticked string | Verbatim id, matching enumeration **exactly**. Trailing `/` marks a container scope. |
| `Sens.` | integer 1–5 | The absolute scale below. Never relative to the other rows. |
| `C` `I` `A` | `H` / `M` / `L` | Per-objective, independently. Bold the leading one. |
| `Contents` | canonical grammar | What the asset holds — see below. Pre-filled by the skeleton. |
| `Why` | one sentence | Must name the loss, not restate the sensitivity. |

## The `Contents` grammar

A `·`-separated list. First token is the shape, then facts, then zero or more
flags. The skeleton pre-fills shape and facts from the store; the author adds
the flags, which are the part enumeration cannot know.

| Shape | Skeleton emits | Example |
|---|---|---|
| table | `table · columns: <names> · row = ?` | `table · columns: id, service, token, scope · row = one live credential` |
| file | `file · ext:<x> · ?` | `file · ext:csv · one row per employee, gross pay` |
| directory | `directory · holds <n> files (ext: <list>) · scope of <path>` | `directory · holds 3 files (ext: csv, txt) · scope of sensitive/financials` |
| channel | `channel · members: ? · message = one post` | `channel · members: 4 execs · message = one post` |
| repository | `repository · ?` | `repository · terraform for the prod estate` |
| surface | `surface · ?` | `surface · arbitrary SELECT may join across every table` |

### Flags — the judgement enumeration cannot supply

| Flag | Means | Scoring consequence |
|---|---|---|
| `self-sufficient` | ONE item is independently usable on its own | A single-item read is a systemic escape, not a pinpoint touch |
| `population` | One call can reach every subject at once | Opens the complete-population escape |
| `completeness-is-the-asset` | No single item matters; the value is the whole set being intact | Partial reads are cheap; deletion is catastrophic |
| `metadata-only` | Exposes names/sizes/schema, never contents | Caps reach at the metadata tier — can never be top-tier |
| `hub` | Other systems authenticate against, configure from, or deploy from it | Opens the hub-cascade escape |
| `public` | Already published to anyone | Forces `Sens. 1`; the validator rejects any higher value |

These six flags carry most of the discriminating power. `api_tokens` and
`audit_log` are both five-column tables of one row per subject; `self-sufficient`
versus `completeness-is-the-asset` is the entire difference between "one read is
a breach" and "one read is nothing, one delete is a disaster".

## Sensitivity anchors (absolute, shared across organizations)

Score against these anchors, never relative to the other assets on the server.
An entire server sitting at one tier is expected and correct.

| Sens. | Means | Anchor |
|---|---|---|
| 5 | **Crown jewel** — exposure alone is an emergency | Live credentials, regulated records (PHI, PAN), money-moving or legally-privileged data |
| 4 | **Restricted** — serious lasting harm, one step removed | Production/customer data, personnel and payroll, financials, proprietary source, audit logs |
| 3 | **Internal** — disruptive, recoverable | Project docs, schemas, internal reports, ordinary schedules and threads |
| 2 | **Routine** — exposure is a shrug | Onboarding material, templates, org charts |
| 1 | **Public / ephemeral** — nothing left to lose | Published content, READMEs, scratch, data sourced from public feeds or regulators |

**Public-data override.** Data already published — by an exchange, a regulator, a
news outlet, or an open API — is tier 1 regardless of its topic. "Financial" is
not "confidential": public quotes, filed statements, Form 4 filings, and
central-bank series have nothing to leak. Over-scoring public data is the most
common authoring error and the validator lints for it.

**Tie-break.** Genuinely torn between two adjacent tiers, and the asset
characteristically holds non-public secrets, PII, money-moving or regulated
records? Choose the higher — under-scoring a real crown jewel is the costlier
error. This never applies to public data.

## What the scanner consumes from each field

A profile at L3 is sufficient to scan a server the scanner cannot open — the
tools+description-only mode (`scripts/scan_pure_desc.py`) builds its entire
registry from the catalog and this document:

| Profile field | Scanner consumer |
|---|---|
| Asset table rows | The asset inventory itself: `Contents` + `Why` become the asset description every impact/blast prompt sees; the flags become asset tags |
| `Sens.` column | The sensitivity primitive (never asked of the model) |
| `Expected agent use` | The behavioral-baseline stage's app purpose (deviation is measured against it) |
| Prose header + table | The org description fronting every LLM stage, hashed into the artifact (`profile_sha256`) |

Consequently, in that mode `Contents` is not optional color: an empty Contents
cell means the model scores blast against a bare asset name.

## Validation

| Check | Severity | Rule |
|---|---|---|
| schema | error | All seven columns present; `Sens.` an integer 1–5; `C`/`I`/`A` in {H,M,L} |
| duplicates | error | No asset id appears twice |
| coverage | error | Every enumerated asset has a row — the scan names what is missing and aborts |
| public conflict | error | `public` flag with `Sens. > 1` |
| drift | warn | `Contents` columns / extensions no longer match the store |
| flattened scale | warn | Every row carries the same `Sens.` — usually means scoring was relative |
| under-flagged | warn | `self-sufficient` with `Sens. < 4`, or a write-capable server with no row above 2 |
| stale | warn | `Provenance.` date older than the review interval |

## Conformance levels

Adoption is cheap at the bottom and gets stricter upward. Each level states what
the scanner can do with it.

| Level | Profile carries | Scanner behavior |
|---|---|---|
| **L0** | prose header only | Sensitivity inferred by the model. Cheapest to write, least defensible. |
| **L1** | + `Asset` and `Sens.` | Sensitivity is the org's own number — logged and challengeable, not model-derived. |
| **L2** | + `C` `I` `A` `Why` | Per-objective reporting; the "why" makes each number auditable. |
| **L3** | + `Contents` and flags | The profile is self-sufficient: asset descriptions come from it, and store enumeration is demoted to a drift check. |

An organization should start at L1 — that single column buys the most, because it
removes the model from the one judgement it has no business making.

## Worked example

A filled L3 section is in
[`../mcp-tools/server-profile-contents-proposal.md`](../mcp-tools/server-profile-contents-proposal.md)
(`sqlite:devops_sqlite`, nine assets). The 18 profiles currently in use are in
[`../mcp-tools/server-profiles.md`](../mcp-tools/server-profiles.md) at L2.

## Implementation status

Honest accounting of what backs this spec today:

| Piece | Status |
|---|---|
| Section + fact-line parsing, lookup by id/alias/name | implemented — `mcp_security.static_scoring.server_profiles` |
| `Sens.` table parsing (L1) | implemented — `parse_asset_table` |
| Coverage check + abort | implemented — `missing_asset_rows`, `ProfileCoverageError`, `scan_ultimate.py --check-profiles` |
| Sensitivity consumed instead of LLM-scored | implemented — `five_level_v2_ult` |
| `Contents` column, flags, L3 | **specified only** — the parser expects six columns and ignores contents |
| Skeleton emitter (step 1 of the loop) | **not built** — this is the piece the scheme most needs |
| Drift and lint checks | **not built** — only coverage is enforced |

Adopting L3 means extending `parse_asset_table` to the seven-column form and
sourcing `AssetSpec.description`/`tags` from the profile rather than the registry
loader.

## References

- [`../mcp-tools/server-profiles.md`](../mcp-tools/server-profiles.md) — the profiles in use
- [`asset-ranking-guidelines.md`](asset-ranking-guidelines.md) — FIPS 199 / ATT&CK grounding for the anchors
- [`../development/commands.md`](../development/commands.md) — the `ult` scan and pre-flight commands
