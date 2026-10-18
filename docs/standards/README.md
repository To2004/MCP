# Standards

Rules and conventions for working in the MCP Security project.

| File | Description |
|------|-------------|
| [style-and-naming.md](style-and-naming.md) | Python style + naming (files, folders, identifiers) |
| [project-layout.md](project-layout.md) | Top-level structure + `docs/` organization |
| [testing-guide.md](testing-guide.md) | How to write and organize tests |
| [patterns.md](patterns.md) | Recurring design patterns |
| [security-standards.md](security-standards.md) | Security rules for defensive code |
| [data-organization.md](data-organization.md) | Research artifact and data organization |
| [nist-guidelines.md](nist-guidelines.md) | NIST publications (FIPS 199, SP 800-60/30/83) underpinning the risk model |
| [scoring-reference.md](scoring-reference.md) | Risk scoring model: Sensitivity × Blast Radius × Likelihood × Irreversibility |
| [mcp-profile-spec.md](mcp-profile-spec.md) | **MCP Server Profile Spec v1** — how any organization writes the profile the scanner reads: authoring loop, required schema, `Contents` grammar + flags, absolute sensitivity anchors, validation rules, four conformance levels |
| [mcp-policy-spec.md](mcp-policy-spec.md) | **MCP Server Policy Spec v1** — the realistic-disclosure counterpart: how an org that withholds its per-asset judgement supplies it as rules instead (classification table by adverse impact, asset register with tool homing and structural flags, recognition rules with a fail-closed default) so the scanner derives sensitivity and blast radius itself. Enforced by `scripts/check_policies.py` |
| [policy.md](policy.md) | **Abstract policy template (no ladder, no CIA)** — org context + a reasoning guide for asset weight + an asset register (`Asset \| Description \| Tools`) + an optional tool-input-rules table + a **normal-use baseline** (Block 4, optional Table 4; `stated` vs `draft` rows, never an invented number). Lighter than v1/v7; accuracy tradeoff of dropping the ladder not yet measured. Includes a `calendar_aurora` worked example |
| [tool-input-importance.md](tool-input-importance.md) | **v12 stage 1 prompt**, product-neutral, two questions per tool input. (1) Does it affect an asset: which asset, how much (including page size and limits), who receives or is notified, what is done, when (including when a change takes effect), or what is carried? (2) Rank its influence 1 to 5 by comparing the safest and riskiest value. The program keeps an input when (1) is yes and (2) is 3 or more; policy-named inputs are always kept. See [v12](../../reports/experiments/v12/README.md). |
| [tool-input-levels.md](tool-input-levels.md) | **v13 prompt, one step** (replaces the two v12 prompts below): per tool input, a run-time rule that reaches every level 1 to 5 (`ranges`, `register` with name words, `keywords`, `values` with five or more choices, `email`), or `null` when the input does not touch an asset, names a record, has fewer than five values, is text next to the main content, or would need facts nobody has. The model gets everything the policy says about the tool (asset levels, special-value rules, baseline) and follows it where it speaks; the program writes in the policy's whole asset register and the credential words. See [v13](../../reports/experiments/v13/README.md). |
| [tool-input-rules.md](tool-input-rules.md) | **v12 stage 2 prompt**: one run-time rule per important input (`ranges`, `register`, `keywords`, `values`, `domain`), turning a value into a level 1 to 5 where 3 is a normal call. Applied by [`mcp_security.input_rules`](../../src/mcp_security/input_rules/README.md); a call's level is the max over its inputs. |
| [policy-authoring-rules.md](policy-authoring-rules.md) | Asset description rules (the four-part `Description` cell, reach-vs-value separation, virtual assets, escalation tools, read/write row splits) and which of ISO/NIST/CIS to write against — each rule traced to a specific measured regression from the v7 framework experiment |
| [policy-scheme-alignment.md](policy-scheme-alignment.md) | What each of ISO/NIST/CIS already requires an org to have vs. what has no standards home (the `Tools` column, the flags) — the minimum ask when requesting a real org's policy |
| [mcp-tool-risk-ratings.csv](mcp-tool-risk-ratings.csv) | Per-tool risk ratings for filesystem, SQLite, GitHub, Slack, Google Drive — scored against MITRE ATT&CK + CVSS |
| [mcp-primitive-operations.csv](mcp-primitive-operations.csv) | 16 generic primitive operations MCP tools perform (read, write, delete…) with risk rankings |
| [mcp-primitive-operations-references.md](mcp-primitive-operations-references.md) | Per-operation justification citing MITRE ATT&CK, CVSS v3.1, OWASP AIVSS, and project papers |
| [mcp-atomic-operations.csv](mcp-atomic-operations.csv) | All 23 MCP protocol-level methods (tools/call, resources/read…) with risk scores |
| [atomic-op-classification.md](atomic-op-classification.md) | How the rules-based classifier maps MCP tools to the 13 atomic operations (two-path: README + ToolList) |

## Where to Start

- Writing Python code? → [style-and-naming.md](style-and-naming.md)
- Creating a new file or folder? → [project-layout.md](project-layout.md)
- Adding research artifacts? → [data-organization.md](data-organization.md)
