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
| [mcp-tool-risk-ratings.csv](mcp-tool-risk-ratings.csv) | Per-tool risk ratings for filesystem, SQLite, GitHub, Slack, Google Drive — scored against MITRE ATT&CK + CVSS |
| [mcp-primitive-operations.csv](mcp-primitive-operations.csv) | 16 generic primitive operations MCP tools perform (read, write, delete…) with risk rankings |
| [mcp-primitive-operations-references.md](mcp-primitive-operations-references.md) | Per-operation justification citing MITRE ATT&CK, CVSS v3.1, OWASP AIVSS, and project papers |
| [mcp-atomic-operations.csv](mcp-atomic-operations.csv) | All 23 MCP protocol-level methods (tools/call, resources/read…) with risk scores |

## Where to Start

- Writing Python code? → [style-and-naming.md](style-and-naming.md)
- Creating a new file or folder? → [project-layout.md](project-layout.md)
- Adding research artifacts? → [data-organization.md](data-organization.md)
