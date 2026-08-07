# MCP Tool References

Reference documentation for the MCP servers the thesis project studies and
scores. Two layers:

- **Catalog layer** — broad inventory across the MCP ecosystem
  (~120 servers across 16 asset domains).
- **Deep-doc layer** — per-tool reference for the four servers used as
  the live testbed.

## Catalog

| File | What's in it |
|------|--------------|
| [catalog.md](catalog.md) | Domain-categorized catalog of notable MCP servers. Each row: server, sample tools, link, evidence tag. |
| [domain-graph.md](domain-graph.md) | Two Mermaid views — domain → servers, and domain → operation types (linked to the atomic-op taxonomy). |
| [server-profiles.md](server-profiles.md) | Organizational profile for each of the 18 scanned servers: owning company, expected agent use, peak asset severity, and per-asset CIA emphasis. Profiles are written at five deliberate length tiers (XS–XL) so context length can be A/B'd as scanner input. |
| [server-policies.md](server-policies.md) | Policy-grade descriptions of 19 servers (5 fs tenants + github/slack/calendar real & cbg + 5 finance + 3 live-provisioned) — the realistic-disclosure variant: a data-classification table stating adverse impact per class, an asset register (asset · description · tools · flags · CIA) and recognition rules, with **no sensitivity number anywhere** (real orgs don't release the inventory). The scanner derives the 1–5 itself. Consumed by `scripts/scan_policy_v5.py`, `scripts/scan_policy_sens.py` and `scripts/scan_policy_no_sens.py`; validated by `scripts/check_policies.py`. |
| [server-profile-contents-proposal.md](server-profile-contents-proposal.md) | Worked L3 example (`sqlite:devops_sqlite`) — asset contents and sensitivity merged into one table, per the [profile spec](../standards/mcp-profile-spec.md). Proposal only; nothing reads it yet. |

## Framework-native policies (the v7 arms)

The same four organizations as `server-policies.md`, each publishing its policy
in a **security framework's own shape** rather than in our register shape. Every
other scanner input is held fixed, so a scan difference is attributable to how
the organization wrote its policy.

| File | Framework | Register shape | Authorization column |
|------|-----------|----------------|----------------------|
| [server-policies-iso.md](server-policies-iso.md) | ISO/IEC 27001:2022 | **A.5.9** inventory with a required `Owner`; keeps the baseline's rows | **A.8.3** information access restriction |
| [server-policies-nist.md](server-policies-nist.md) | NIST FIPS 199 / SP 800-60 | One row per **SP 800-60 information type × operation profile** — a type whose read and write categorize differently is two rows, so row counts run above the baseline | **AC-3** access enforcement, bounded by **AC-6** |
| [server-policies-cis.md](server-policies-cis.md) | CIS Controls v8.1 Control 3 | **Safeguard 3.2** inventory — sensitive data enumerated, everything else merged into coarse entries, so row counts run below the baseline | **Safeguard 3.3** data access control lists |

Three properties they share, and one they do not:

- **No `Flags` column.** Removing it costs nothing against the arm they are
  compared to: `five_level_v2_v5r_nacombo` already runs `asset_flags: "none"`,
  `floors: "none"`, and v5r removed the blast roof, so no flag reached either the
  model or the deterministic assembly. What a flag used to assert is now carried
  by the asset's description.
- **Reachable ≠ authorized.** `Tools` stays the reachability fact and the
  tool×asset homing the blast stage scores; the authorization column names the
  subset the organization sanctions. The gap between them is the unsanctioned
  reach an MCP risk scan exists to price.
- **Still no sensitivity number.** `assert_no_sensitivity_numbers` guards these
  documents too — the scanner derives 1–5, as in every policy arm.
- **CIS states its class label; ISO and NIST do not.** Safeguard 3.2 asks the
  inventory to record a sensitivity level and 3.7 requires only two levels, which
  underdetermines a 1–5 anyway. ISO's A.5.13 label and NIST's FIPS 199 triple are
  withheld, because stating them would turn derivation into a lookup.

Scanned by `scripts/scan_v7.sbatch` / `scripts/scan_policy_v5.py --policy-doc`;
compared by `scripts/compare_v7_frameworks.py`; results in
[`reports/experiments/v7/`](../../reports/experiments/v7/README.md). Every
control number and information-type name in these documents was verified against
the published standard — see each document's own References section.

## Real-world policy examples

[`real-policy-examples/`](real-policy-examples/README.md) — three **real, publicly
published** data-classification policies from one organization (The University of Iowa),
collected as the outside-world counterpart to the synthetic registers above. All three cover
the same subject and differ only in how concretely they name assets, so they form a
controlled ladder:

| Rung | Document | Named systems | Register shape |
|---|---|---|---|
| bad | IT-19 Institutional Data Policy | 0 | 4 classes × description × generic data examples |
| medium | Data classification guidelines | 1 (`InfoHawk+`) | CIA derivation matrix + 5 worked examples |
| good | Data Classification Guide to IT Services | 41 | 41 × 4 grid, 164 authorization cells |

They corroborate two design choices (no published sensitivity numbers; reachable ≠
authorized) and challenge two others (our required `Owner` column exceeds what this real org
discloses; no rung reaches per-operation authorization). Refreshed by
`scripts/fetch_real_policy_examples.py`.

## Deep references (per-server tool docs)

These four servers are used as the live testbed for the scoring framework
and have full per-tool documentation:

| Server | Tool reference | Upstream README |
|--------|----------------|-----------------|
| Filesystem | [filesystem.md](filesystem.md) | [filesystem-mcp-readme.md](filesystem-mcp-readme.md) |
| GitHub | [github.md](github.md) | [github-mcp-readme.md](github-mcp-readme.md) |
| Slack | [slack.md](slack.md) | [slack-mcp-readme.md](slack-mcp-readme.md) |
| SQLite | [sqlite.md](sqlite.md) | [sqlite-mcp-readme.md](sqlite-mcp-readme.md) |

## Live-provisioned organizations

The last three policy sections pair one organization with one **real** vendor
catalog — no demo surfaces:

| Section | Organization | Domain | Catalog |
|---|---|---|---|
| `github_helios` | Helios Grid | electricity transmission | real GitHub, 26 tools |
| `slack_vireo` | Vireo Bio | biopharmaceutical R&D | real Slack, 16 tools |
| `calendar_aurora` | Aurora Airways | commercial aviation | real Google Calendar, 13 tools |

Their register ids name assets that exist — created through the real MCP servers
on 2026-07-29 and read back through them. Provenance, the call captures and the
provisioning caveats:
[`reports/live_run/orgs_2026-07-29/`](../../reports/live_run/orgs_2026-07-29/README.md).

## Related

- [`../standards/atomic-op-classification.md`](../standards/atomic-op-classification.md) — operation taxonomy used by `domain-graph.md`.
- [`../standards/mcp-tool-risk-ratings.csv`](../standards/mcp-tool-risk-ratings.csv) — per-tool CVSS-style risk ratings.
- [`../project/annotated-bibliography-mcp-security.md`](../project/annotated-bibliography-mcp-security.md) — papers cited in the `paper-cited` evidence tag of the catalog.
