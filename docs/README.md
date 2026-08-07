# MCP Security Documentation

Guides, standards, and references for working with the project.

## How to Navigate

| Section | Path | Audience | Description |
|---------|------|----------|-------------|
| **Project** | [project/](project/) | Everyone | Overview, architecture, roadmap |
| **Development** | [development/](development/) | Contributors | Setup, commands, workflows, contributing |
| **Standards** | [standards/](standards/) | Contributors | Style, layout, testing, security, patterns |
| **Claude** | [claude/](claude/) | Claude Code | AI collaboration conventions |
| **Guides** | [guides/](guides/) | Everyone | Step-by-step how-tos |
| **MCP tools** | [mcp-tools/](mcp-tools/) | Everyone | Server catalog, per-tool references, and [organizational profiles](mcp-tools/server-profiles.md) of the scanned servers |

## Quick Links

- New to the project? Start with [Project Overview](project/overview.md) then [Setup](development/setup.md)
- Visual map of the whole system (static + dynamic dataflow): [Architecture Diagrams](project/architecture-diagrams.md) (Mermaid) / [architecture.svg](project/architecture.svg) (Graphviz)
- Building the dynamic (runtime) scorer? See [Dynamic Scoring Design](project/dynamic-scoring-design.md)
- Resolving *which asset* a runtime call touches (no LLM, no per-server config):
  [`src/mcp_security/binding/README.md`](../src/mcp_security/binding/README.md);
  measured in [v8](../reports/experiments/v8/README.md), explained with diagrams in
  [v8 METHOD.md](../reports/experiments/v8/METHOD.md)
- Which inputs reach which model call? See [LLM Inputs](project/llm-inputs.md)
- Research foundation? See [Annotated Bibliography](project/annotated-bibliography-mcp-security.md) (30 papers, also available as [PDF](project/annotated-bibliography-mcp-security.pdf))
- Adding code? Read [Style and Naming](standards/style-and-naming.md) and [Testing Guide](standards/testing-guide.md)
- Adding a new module? Follow [Adding a Module](guides/adding-a-module.md)

## Conventions

- All docs are Markdown files, one topic per file
- Concise — prefer short sections over long walls of text
- Links are relative
