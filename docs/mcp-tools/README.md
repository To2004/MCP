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

## Deep references (per-server tool docs)

These four servers are used as the live testbed for the scoring framework
and have full per-tool documentation:

| Server | Tool reference | Upstream README |
|--------|----------------|-----------------|
| Filesystem | [filesystem.md](filesystem.md) | [filesystem-mcp-readme.md](filesystem-mcp-readme.md) |
| GitHub | [github.md](github.md) | [github-mcp-readme.md](github-mcp-readme.md) |
| Slack | [slack.md](slack.md) | [slack-mcp-readme.md](slack-mcp-readme.md) |
| SQLite | [sqlite.md](sqlite.md) | [sqlite-mcp-readme.md](sqlite-mcp-readme.md) |

## Related

- [`../standards/atomic-op-classification.md`](../standards/atomic-op-classification.md) — operation taxonomy used by `domain-graph.md`.
- [`../standards/mcp-tool-risk-ratings.csv`](../standards/mcp-tool-risk-ratings.csv) — per-tool CVSS-style risk ratings.
- [`../project/annotated-bibliography-mcp-security.md`](../project/annotated-bibliography-mcp-security.md) — papers cited in the `paper-cited` evidence tag of the catalog.
