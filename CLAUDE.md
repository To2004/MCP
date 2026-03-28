# CLAUDE.md

This file gives guidance to Claude Code when working in this repository.
For detailed documentation, see the [docs/](docs/) folder
([index](docs/README.md)).

## Project Overview

MCP Security is a Python project focused on evaluating and ranking the severity
of AI agents that request access to Model Context Protocol (MCP) servers.
The goal is to build a risk scoring system that analyzes agent access requests
and classifies them by severity level, helping determine whether an agent
should be allowed, restricted, or denied access to MCP resources.

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
