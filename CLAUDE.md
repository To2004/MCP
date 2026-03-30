# CLAUDE.md

This file gives guidance to Claude Code when working in this repository.
For detailed documentation, see the [docs/](docs/) folder
([index](docs/README.md)).

## Project Overview

MCP Security is a defense-oriented risk scoring framework that protects
MCP (Model Context Protocol) servers from malicious or risky agent behavior.
Unlike traditional risk frameworks built for static software and human-driven
workflows, this project addresses the unique threats posed by autonomous AI
agents — dynamic tool invocation, context reuse, trust boundary violations,
and downstream blast radius.

The framework evaluates agents accessing MCP servers and produces risk scores
in two modes:
- **Static** — evaluated at design time based on a tool's general properties
- **Dynamic** — evaluated at runtime based on the specific agent request/input

See [docs/project/overview.md](docs/project/overview.md) for full details.

## Quick Reference

| Action | Command |
|--------|---------|
| Install dependencies | `uv sync` |
| Run project | `uv run python -m mcp_security.main` |
| Run tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |

Full command reference: [docs/development/commands.md](docs/development/commands.md)

## Directory Structure

- `src/mcp_security/` — main application code
- `tests/` — automated tests
- `docs/` — project documentation ([index](docs/README.md))
- `.claude/commands/` — reusable Claude Code command prompts

## Coding Rules (MUST follow)

- Use descriptive names; keep functions small and focused
- No hardcoded values — use constants or parameters
- Add docstrings to public functions; use type hints
- Prefer readability over clever code
- Write tests for important logic
- Do not add unnecessary dependencies
- Line length: 100 (enforced by Ruff)

Details: [docs/standards/style-guide.md](docs/standards/style-guide.md)

## Workflow Rules (MUST follow)

- Inspect the codebase and explain the plan before large changes
- For non-trivial work, propose steps before editing many files
- After making changes, run `uv run pytest`
- When adding a feature, also add tests
  ([guide](docs/guides/adding-tests.md))
- Follow security standards:
  [docs/standards/security-standards.md](docs/standards/security-standards.md)

## Documentation Index

| Section | Path | Description |
|---------|------|-------------|
| Project | [docs/project/](docs/project/) | Overview, architecture, roadmap |
| Development | [docs/development/](docs/development/) | Setup, commands, workflows, contributing |
| Standards | [docs/standards/](docs/standards/) | Style, testing, patterns, security |
| Claude | [docs/claude/](docs/claude/) | Claude-specific guidance and commands |
| Guides | [docs/guides/](docs/guides/) | Step-by-step how-tos |
