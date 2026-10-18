# v7 Prompts

The three v7 arms (`iso`, `nist`, `cis`) each classify asset sensitivity with a
dedicated task prompt, defined in
[`src/mcp_security/static_scoring/prompts.py`](../../../src/mcp_security/static_scoring/prompts.py)
as `ASSET_TASK_POLICY_V7_ISO` / `_NIST` / `_CIS` (lines 1834, 1876, 1927) and
selected per arm in
[`pipeline.py:1247-1256`](../../../src/mcp_security/static_scoring/pipeline.py#L1247-L1256)
via `sens_scheme: "v7_iso" | "v7_nist" | "v7_cis"`. This file shows how each is
assembled and reproduces the full text sent to the model.

## Assembly

Every sensitivity call in `Pipeline.score_assets()` builds one string:

```
preamble + "\n" + task + "\n\n" + user
```

- **preamble** — `_PROPOSER_BASE_DESC` (org description + inferred domain
  profile; none of the v7 modes set `no_domain`, so this is the one used).
- **task** — the arm's `ASSET_TASK_POLICY_V7_*` constant, itself built from a
  per-arm opening, the shared `_SENS_TIERS` rubric, the shared `_AUTHZ_EVIDENCE`
  block (parameterized with the arm's control citation), and a per-arm closing.
- **user** — `ASSET_USER_POLICY`, filled with the one asset's JSON.

### Preamble — `_PROPOSER_BASE_DESC`

```
You are a security classifier for an MCP gateway. Two
descriptions of this server are given below. The ORGANIZATION'S DESCRIPTION is
written by the people who deploy it and is authoritative for CONTEXT: who runs the
server, what agents are supposed to do with it, how severe each asset is, and which
of confidentiality / integrity / availability carries the loss. The INFERRED DOMAIN
PROFILE is derived from the tool registry and is authoritative for MECHANICS: what
the tools can actually do. Use both. Where they disagree about CAPABILITY trust the
inferred profile; where they disagree about IMPORTANCE trust the organization.

ORGANIZATION'S DESCRIPTION OF THIS MCP SERVER:
{org_description}

INFERRED DOMAIN PROFILE:
{domain_profile}

Output ONLY valid JSON, no prose, no fences.
```

`{org_description}` is the framework-native policy document for the arm
(`server-policies-iso.md` / `-nist.md` / `-cis.md`); `{domain_profile}` is the
Stage 0 inferred profile for that server.

### Shared rubric — `_SENS_TIERS`

Spliced into all three task prompts after their classification steps:

```
  5 CROWN JEWEL  exposure alone is an emergency — exploitable or legally
                 reportable the moment it leaks; OR a control plane, where losing
                 it rewires what every other tool can reach.
  4 RESTRICTED   serious lasting harm one step removed: damages customers, staff
                 or the organization's position, but is not instantly weaponizable.
  3 INTERNAL     disruptive and embarrassing but recoverable; meant to stay in-org.
  2 ROUTINE      low-value internal material; exposure is a shrug.
  1 PUBLIC       already published or disposable — no confidentiality left to lose.

RULES
- ABSOLUTE scale, never relative to the other assets here. A whole server sitting
  at one tier is expected; do NOT spread scores to manufacture contrast.
- CONTAINER: takes the tier of the most sensitive thing it CHARACTERISTICALLY
  holds — its typical payload, not a conceivable one.
- AGGREGATION: if one asset holds the WHOLE population of a class, or the policy
  names a combination that reveals more than its parts, raise one tier.
- PUBLISHED, NOT TOPIC: data the organization has already published has no
  confidentiality left to lose and is 1, however sensitive its subject sounds.
```

### Shared authorization block — `_AUTHZ_EVIDENCE`

Spliced in right after `_SENS_TIERS`, with `{control}` filled per arm (ISO
`A.8.3 information access restriction`, NIST `AC-3 access enforcement, bounded
by AC-6`, CIS `Safeguard 3.3 data access control lists`):

```
- SANCTIONED VS REACHABLE ({control}). The register states, per asset, which of
  the tools that can reach it the organization actually authorizes. Read the gap
  as EVIDENCE, not as an answer:
    * An asset the organization authorizes NO operation against is one it has
      decided no agent should touch. That usually means it is precious — but it
      can also mean another system is authoritative for it, or that the operation
      cannot be undone. Prefer the reading the asset's own description supports.
    * An asset that is broadly authorized is rarely a crown jewel, because an
      organization does not hand out routine access to one.
    * NEVER score sensitivity from the authorization column alone. It records an
      access decision; you are classifying the information.
```

### User message — `ASSET_USER_POLICY`

```
Asset class entry:
{asset_json}

Return JSON (classify BEFORE you score -- emit these keys in this exact order):
{"asset_id": str, "policy_class": str, "reasoning": str,
  "sensitivity": 1-5, "confidence": 0.0-1.0}
```

## Full assembled task prompts

### `v7_iso`

```
TASK: Assign ASSET SENSITIVITY (1-5) by applying the ISO/IEC 27001:2022
classification procedure THIS ORGANIZATION PUBLISHED, then mapping its class onto
the scale below.

The policy states its A.5.12 procedure as a table of four criteria, each phrased
as a question this organization asks. Work through them in that form.

  1 CLASSIFY against the published procedure, taking each criterion in turn:
      * LEGAL REQUIREMENTS — statutory duty, contract, or employment obligation.
      * VALUE — worth to the organization, or to someone else.
      * CRITICALITY — what stops working, or becomes unknowable, without it.
      * SENSITIVITY to unauthorised disclosure OR MODIFICATION — both; the policy
        names both and so must you.
    The class is the HIGHEST any single criterion justifies, never an average.
    Use the organization's own class names, taken from its classification table.
    Where the register does not settle it, apply the section's recognition rules
    and then its stated fail-closed default.

  2 MAP that class onto the scale below.

<< _SENS_TIERS >>

<< _AUTHZ_EVIDENCE, control="A.8.3 information access restriction" >>

- THE OWNER IS A CUE, NOT A SCORE. A.5.9 requires an identified owner. An asset
  owned by a security or compliance function is more often Restricted or above
  than one owned by a workplace-services function — but the owner names
  accountability, not value. It breaks ties; it does not decide them.
- INTEGRITY AND AVAILABILITY COUNT. A.5.12 requires all three axes. The register
  states a loss axis per asset; an asset whose loss axis is modification is not
  low merely because reading it is harmless.
- THE REGISTER HAS NO FLAGS. Whether an asset is a control plane, holds a whole
  population, or is usable on its own is stated in its description. Read it
  there.
```

### `v7_nist`

```
TASK: Assign ASSET SENSITIVITY (1-5) by categorizing this register row the way
FIPS 199 requires and THIS ORGANIZATION PUBLISHED, then mapping the result onto
the scale below.

The register states an SP 800-60 information type per row, and the section states
the adverse-effect definitions this organization applies. Use both.

  1 START FROM THE TYPE. SP 800-60 assigns a provisional category from what the
    information IS. The row names its information type — use it. Rows reading
    "inherits the type reached" take the type of the most sensitive row the same
    tool can reach.

  2 CATEGORIZE AS A TRIPLE. Rate the adverse effect of a loss on each of
    confidentiality, integrity and availability, against the organization's own
    definitions of HIGH / MODERATE / LOW. Judge the effect, not the topic.

  3 APPLY THE SPECIAL FACTORS the section lists — aggregation, criticality and
    completeness, reachability beyond the boundary. They adjust PER AXIS and only
    upward.

  4 TAKE THE HIGH-WATER MARK. The security category is the HIGHEST of the three,
    never an average. Then map:
      HIGH     -> 5 if a loss is legally reportable, immediately exploitable, or
                  rewires what other systems can reach; otherwise 4.
      MODERATE -> 3
      LOW      -> 2
      no adverse effect / already published -> 1

<< _SENS_TIERS >>

<< _AUTHZ_EVIDENCE, control="AC-3 access enforcement, bounded by AC-6" >>

- THE ROW IS AN OPERATION PROFILE, NOT A FILE. This register splits a type whose
  read and write categorize differently into two rows. Categorize the row in front
  of you on the axis its own description and impact driver name — do not average
  it with its twin, and do not import the twin's category.
- THE THREE-LEVEL FIPS SCALE IS COARSER THAN THIS FIVE-LEVEL ONE. Step 4 is where
  that is resolved, and the HIGH split is the only judgement it asks of you.
- THE REGISTER HAS NO FLAGS. Whether a row is a control plane, holds a whole
  population, or is usable on its own is stated in its description and reached
  through the aggregation and reachability special factors.
```

### `v7_cis`

```
TASK: Assign ASSET SENSITIVITY (1-5) starting from the data classification scheme
THIS ORGANIZATION PUBLISHED under CIS Safeguard 3.7, then refining it to a tier.

The register STATES this organization's category for each entry. That category is
a starting point and nothing more: the scheme has two or three levels where this
scale has five, so most of the work is still ahead of you.

  1 READ THE STATED CATEGORY off the register row and look up its definition in
    the organization's scheme. The definition — the harm it describes — is what
    matters, not the label.

  2 REFINE TO A TIER using the entry's own description, the recognition rules,
    and the 3.12 segment. Ask what this data IS, who it is about, what depends on
    it, and how much of it one call reaches. A coarse scheme delegates exactly
    this judgement to the description; make it.

  3 MAP onto the scale below.

<< _SENS_TIERS >>

<< _AUTHZ_EVIDENCE, control="Safeguard 3.3 data access control lists" >>

- A COARSE SCHEME IS NOT A LOW SCORE, AND IT IS NOT A HIGH ONE EITHER. The
  organization's top category spans 3-5 on this scale and its bottom category
  spans 1-3. Do NOT collapse a category to a single tier, in either direction:
  two entries carrying the same label are routinely two tiers apart, and the
  description is what separates them.
- SAFEGUARD 3.2 MERGES. This inventory enumerates sensitive data individually and
  lumps the rest into functional groups, so a single row can stand for several
  distinct surfaces. Score a merged row on the most sensitive thing it
  CHARACTERISTICALLY holds, exactly as the container rule says — a merge is not a
  reason to average.
- THE SEGMENT IS A CUE, NOT A SCORE. Safeguard 3.12 separates processing by
  sensitivity, so an entry in a restricted segment is rarely a 1 or a 2. But the
  segment records where data lives, not what it is worth.
- THE REGISTER HAS NO FLAGS. Whether an entry is a control plane, holds a whole
  population, or is usable on its own is stated in its description.
```

## What v7 does *not* change

Tool impact and blast radius use the same prompts as every other five-level
arm — `TOOL_IMPACT_TASK` and the blast task for `five_level_v2` mode — since
`FIVE_LEVEL_LADDERS` maps all three `five_level_v2_v7_*` modes to the same
deterministic operation-type impact ladder (`prompts.py` line 80-82) and the
v7 register carries no flags or sensitivity numbers for those stages to read.
Only the asset-sensitivity task prompt differs per arm.

## Reference

- [`README.md`](README.md) — what v7 measures and how to reproduce a scan
- [`src/mcp_security/static_scoring/prompts.py`](../../../src/mcp_security/static_scoring/prompts.py)
  — `_SENS_TIERS` (L1665), `_AUTHZ_EVIDENCE` (L1817), `ASSET_TASK_POLICY_V7_ISO`
  (L1834), `_NIST` (L1876), `_CIS` (L1927)
- [`src/mcp_security/static_scoring/pipeline.py`](../../../src/mcp_security/static_scoring/pipeline.py)
  — arm selection (L1247-L1256), preamble assembly (`_proposer_prompt`, L976)
