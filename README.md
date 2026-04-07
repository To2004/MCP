# MCP Security

A defense-oriented risk scoring framework for the Model Context Protocol
(MCP), where the **MCP server is the protected asset** and **AI agents are
the threat source**. The framework scores incoming agent requests so a
server can gate, throttle, or deny dangerous interactions before they
execute.

## Threat Model

All attacks flow **client → server**: a malicious or compromised AI agent
sends harmful requests through MCP tools to damage the server. The inverse
direction (malicious server attacking the agent) is out of scope.

## What the Framework Scores

Risk scores combine factors like tool privilege and side effects, agent
autonomy level, context persistence, trust boundaries, execution frequency,
and downstream blast radius. Scores are produced in two modes:

- **Static** — at design time, based on the tool's general properties
- **Dynamic** — at runtime, based on the specific agent request/input

## Quick Start

```bash
uv sync                            # install dependencies
uv run python -m mcp_security.main # run project
uv run pytest                      # run tests
uv run ruff check .                # lint
```

Full command reference: [docs/development/commands.md](docs/development/commands.md)

## Repository Layout

| Path | Contents |
|------|----------|
| `src/mcp_security/` | Main application code (installed as a package) |
| `tests/` | Automated tests (mirrors src/ structure) |
| `docs/` | Project documentation — [start here](docs/README.md) |
| `Literature_review/` | Thesis research: 62 papers, reviews, benchmarks |
| `mcp_learning_lab/` | Experimental MCP servers and agents |

## Documentation

- [docs/README.md](docs/README.md) — full documentation index
- [docs/project/overview.md](docs/project/overview.md) — detailed project overview
- [CLAUDE.md](CLAUDE.md) — guidance for Claude Code sessions
- [Literature_review/README.md](Literature_review/README.md) — research context

## Status

Early development. Package skeleton and smoke test are in place; scoring
engine and threat model are being built on the research foundation in
`Literature_review/`. See [docs/project/roadmap.md](docs/project/roadmap.md).

## License

License: TBD
