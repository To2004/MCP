# Asset register and policy, grounded in ABAC/RAdAC literature

[`real-policy-examples/`](real-policy-examples/README.md) validates the register's *shape*
against what real organizations publish. This document validates its *name and structure*
against the academic literature that already formalizes the same construct — so the grounding
here is theory, not a second empirical sample, and every worked row below is one of this
project's own **virtual** assets, never a system named in the real-policy corpus (Iowa,
Nevada, Leeds Beckett, Colorado). It covers both halves of the split the literature draws:
the **Attribute Repository** (our asset register) and the **Policy Repository** (our
classification table + recognition rules) — Balogun & Takabi's boxed pairing:

> Attribute Repository + Policy Repository

Skipping the second half would leave the grounding incomplete, since our own
[`mcp-policy-spec.md`](../standards/mcp-policy-spec.md) is explicit that the register alone
never carries the judgement — the policy blocks do.

## The construct already has a name, and it isn't "asset register"

What [`server-policies.md`](server-policies.md) calls an asset register — a per-resource table
of identity, description, and structural properties, kept separate from the rules that act on
it — is the **Attribute Repository** (also **Resource/Object Attribute Repository**, or
**Policy Information Point**, PIP) of ABAC/RAdAC research. Three points from that literature
carry over directly:

- **Attributes are stored separately from policy.** Balogun & Takabi (2022) split an ABAC
  architecture into an attribute repository and a policy repository; a Policy Decision Point
  combines them at evaluation time. That is exactly the split between our register (facts) and
  our recognition rules + classification table (policy) — see
  [`../standards/mcp-policy-spec.md`](../standards/mcp-policy-spec.md).
- **The repository can hold subject, object, and environment attributes together.**
  Yalcinkaya, Maffei & Onori (2017) describe an "enterprise-wide central database of protected
  object and subject attributes," retrieved through a PIP and consumed by a PDP. Their object
  schema — `ASSET_ID`, `DESCRIPTION`, `COMPONENT_TYPE`, `FUNCTION_AREA`, `DEPARTMENT_ID`,
  `CLASSIFICATION` — is a near-literal match for our register's columns.
- **A stored attribute is not itself an access decision.** Jin, Krishnan & Sandhu (2012) treat
  attributes as the input an authorization function consumes, not the output. That is the
  reason our `Tools` column (what is reachable) and the ISO arm's `Authorized operations`
  column (what is sanctioned) are kept as two separate facts rather than collapsed into one —
  the second is a policy decision *over* the first, not another attribute.

## Why the ISO arm is the anchor, not NIST or CIS

The v7 experiment has three framework-native register arms —
[`server-policies-iso.md`](server-policies-iso.md),
[`-nist.md`](server-policies-nist.md), [`-cis.md`](server-policies-cis.md) — and only one of
them is a fair structural match for this literature. NIST's FIPS 199 / SP 800-60 and CIS
Controls v8 are both national artifacts (US federal; a US-centric controls list, narrowed
further to a single state in the CIS example real-policy-examples collects). ISO/IEC 27001's
**A.5.9 "Inventory of information and other associated assets"** is the internationally
adopted standard, and it is the one the cited papers themselves gravitate toward when they
need a real-world register to point at. That makes the ISO arm — not the NIST or CIS arm —
the most universal of the three to anchor the literature mapping against.

## Column mapping — ISO arm to Attribute Repository

| `server-policies-iso.md` column | Attribute-repository role | Literature |
|---|---|---|
| Asset id (register row key) | `ASSET_ID` | Yalcinkaya et al. 2017 |
| Description | `DESCRIPTION` / `COMPONENT_TYPE` | Yalcinkaya et al. 2017 |
| Owner | department/ownership attribute | Balogun & Takabi 2022 (object attributes include department) |
| Tools (reachability) | **not** a classical ABAC attribute — an MCP-specific fact the repository literature has no slot for | — |
| Authorized operations (A.8.3) | PDP output, evaluated *from* attributes, not stored as one | Jin, Krishnan & Sandhu 2012 |
| Loss axis / CIA emphasis | risk/situational factor feeding a RAdAC decision | Kandala, Sandhu & Bhamidipati 2011 |
| "Default: Confidential" for unrecognized material | the unknown-attribute-value case | Bui & Stoller 2020 |

The `Tools` row is the one deliberate mismatch: none of the five papers model "what a caller
can technically reach" as a stored attribute, because none of them describe an MCP-shaped
surface where every tool is reachable against every path by construction. It stays a
register column here because the blast stage scores the tool×asset homing directly — see
[`../project/dynamic-layer-explained.md`](../project/dynamic-layer-explained.md).

## The policy half — Policy Repository

Balogun & Takabi's second register has a direct home in this repo:
[`mcp-policy-spec.md`](../standards/mcp-policy-spec.md) already keeps the judgement in three
blocks separate from the register (Block 3):

| `mcp-policy-spec.md` block | Policy-repository role | Literature |
|---|---|---|
| Block 2 — data classification table (Class · adverse-impact definition · Examples) | the stored policy rule set a PDP evaluates *against* attributes, not another attribute itself | Balogun & Takabi 2022 |
| Block 4 — asset recognition rules (cues, metadata rule, aggregation, default class) | the matching function that maps a stored attribute (an asset's Description) onto a policy class — Jin, Krishnan & Sandhu's "authorization function," concretely | Jin, Krishnan & Sandhu 2012 |
| Block 4's fail-closed default class | the unknown-attribute-value case, resolved by policy rather than left undefined | Bui & Stoller 2020 |
| Blocks 5–7 — operation limits, expected use, loss priorities | operational-need and risk/situational factors that adjust a decision beyond static classification | Kandala, Sandhu & Bhamidipati 2011 |

The same asymmetry the register mapping surfaced repeats here: nothing in the five papers
models an *organization-supplied* classification procedure that a scanner must *derive*
severities from rather than look up — Block 2's "no numbers, ever" rule and Block 4's
recognition rules are this project's own addition on top of the literature's PDP, not
something the literature already specifies. What the literature does confirm is the
*shape*: rules stored and evaluated separately from the facts they act on, exactly Balogun
& Takabi's PDP combining an attribute repository with a policy repository.

### Worked example — policy repository, same virtual org

The classification table and recognition-rule paragraph already published for
`fs_corp_filesystem` in [`server-policies-iso.md`](server-policies-iso.md#fs_corp_filesystem) —
the same fictional company as the register example below, never a real organization:

| Class | Adverse impact that defines it |
|---|---|
| Restricted | Exploitable on its own the moment it leaks, or a modification that reaches systems beyond this share. |
| Confidential | Serious lasting harm to staff or to the company's position; recovery is possible but slow and public. |
| Internal | Recoverable embarrassment; meant to stay in-org, no lasting harm. |
| Routine | A shrug — that a path, a size or a timestamp exists, with nothing behind it. |
| Public | None; already published. |

**Default: Confidential** — unrecognized material on this share is assumed to carry business
harm until an owner says otherwise. That single rule is the fail-closed policy decision Bui &
Stoller's unknown-value case calls for: rather than leaving an unlisted asset's classification
undefined, the policy repository states what happens when the attribute repository has no row
for it.

## Worked example — virtual assets only

Recast two rows already in [`server-policies-iso.md`](server-policies-iso.md#fs_corp_filesystem)
— `fs_corp_filesystem`, an entirely fictional "unregulated mid-size product company" — in
Yalcinkaya-style attribute-repository notation. Nothing below names a real system; that is the
same virtual-asset convention every register in this repo already follows.

```text
ASSET_ID       = security-keys
DESCRIPTION    = Private key material and certificates, complete and usable alone
COMPONENT_TYPE = credential material
FUNCTION_AREA  = Security Operations
DEPARTMENT_ID  = SecOps
CLASSIFICATION = Restricted (disclosure, then modification)

ASSET_ID       = payroll-records
DESCRIPTION    = Compensation records, one row per employee, the whole staff in one file
COMPONENT_TYPE = personnel data
FUNCTION_AREA  = People Ops
DEPARTMENT_ID  = PeopleOps
CLASSIFICATION = Confidential (disclosure)
```

The organization that "owns" `A-1832`-style real assets never appears; the repository holds
only what that organization would be willing to disclose about a resource it does not name —
Bui & Stoller's point about attribute values the org may withhold entirely.

## What we keep calling it

The codebase, the policy spec, and every arm's Markdown keep the names **asset register** and
**classification table / recognition rules** — renaming them to "Attribute Repository" and
"Policy Repository" everywhere would touch the parser in
[`server_policies.py`](../../src/mcp_security/static_scoring/server_policies.py), every test
that greps for the register header or the policy blocks, and five Markdown documents, for a
name change with no behavioral effect. Use **Attribute Repository / Policy Repository (PIP /
PDP)** when situating the design against related work in the thesis or paper; **asset
register** and **policy** stay this project's own names for its concrete instantiation of that
pair, the same way `real-policy-examples/README.md` treats "asset register" as our working
name while comparing it to what real organizations actually publish.

## References

| Paper | Venue | Contributes |
|---|---|---|
| Yalcinkaya, Maffei & Onori (2017) | *Int. J. Computer Network and Information Security*, 9(2) | The closest structural match — a central attribute repository with an object/asset schema (`ASSET_ID`, `DESCRIPTION`, `CLASSIFICATION`, …) retrieved through a PIP |
| Balogun & Takabi (2022) | WRIT, ACSAC 2022 | Attribute repository kept separate from a policy repository, combined by the PDP at decision time |
| Jin, Krishnan & Sandhu (2012) | DBSec 2012, LNCS 7371 | Foundational unified ABAC model — attributes as authorization-function input, not output |
| Kandala, Sandhu & Bhamidipati (2011) | ARES 2011 | RAdAC built on an attribute-based framework — risk/situational factors feeding the access decision |
| Bui & Stoller (2020) | ICISS 2020, LNCS 12553 | ABAC/ReBAC policy mining where some entity attribute values are unknown |

- E. Yalcinkaya, A. Maffei, and M. Onori, "Application of Attribute Based Access Control Model
  for Industrial Control Systems," *International Journal of Computer Network and Information
  Security*, vol. 9, no. 2, pp. 12–21, 2017, doi: 10.5815/ijcnis.2017.02.02.
- O. Balogun and D. Takabi, "An Insider Threat Mitigation Framework Using Attribute Based
  Access Control," in *7th Workshop on Research for Insider Threats (WRIT), ACSAC*, 2022.
- X. Jin, R. Krishnan, and R. Sandhu, "A Unified Attribute-Based Access Control Model Covering
  DAC, MAC and RBAC," in *Data and Applications Security and Privacy XXVI (DBSec 2012)*, LNCS
  7371, pp. 41–55, Springer, 2012, doi: 10.1007/978-3-642-31540-4_4.
- S. Kandala, R. Sandhu, and V. Bhamidipati, "An Attribute Based Framework for Risk-Adaptive
  Access Control Models," in *2011 Sixth International Conference on Availability, Reliability
  and Security (ARES)*, pp. 236–241, 2011, doi: 10.1109/ARES.2011.41.
- T. Bui and S. D. Stoller, "Learning Attribute-Based and Relationship-Based Access Control
  Policies with Unknown Values," in *Information Systems Security, 16th International
  Conference (ICISS 2020)*, LNCS 12553, pp. 23–44, Springer, 2020.
