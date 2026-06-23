# CLAUDE.md

Guidance for Claude Code in this repo. Detailed docs: [docs/](docs/README.md).

## INSTRUCTIONS

### Non-negotiable rules

- **Threat model direction**: MCP servers are the PROTECTED asset; agents are the THREAT. Never reverse. Frame as "defending servers FROM agents".
- **MCP scope**: For MCP-related items (benchmarks, attacks, papers), return ONLY MCP-specific results. No "bonus" non-MCP tiers unless explicitly asked.
- **Questions ≠ actions**: Answer questions directly. Don't install, explore, or execute unless asked. If unsure, ask.
- **Verify before "done"**: For catalogs/scans (CVEs, papers, files), do a second pass and state the count before finalizing.

### Coding rules

- Descriptive names; small, focused functions
- No hardcoded values — use constants or parameters
- Docstrings on public functions; type hints everywhere
- Tests for important logic
- Line length 100 (Ruff-enforced)
- Details: [docs/standards/style-and-naming.md](docs/standards/style-and-naming.md)

### Workflow rules

- Explain the plan before large multi-file changes
- Run `uv run pytest` after edits
- New features ship with tests — [guide](docs/guides/adding-tests.md)
- Follow [security standards](docs/standards/security-standards.md)

## CONTEXT

Defense-oriented risk-scoring framework. The **MCP server is the protected asset**; **AI agents are the threat source**. The framework scores incoming agent requests — **static** at design time (tool properties), **dynamic** at runtime (specific request/input) — so servers can gate, throttle, or deny risky calls before execution. Inverse direction (malicious server → agent) is out of scope.

Full details: [docs/project/overview.md](docs/project/overview.md).

### Layout

- `src/mcp_security/` — application code
- `tests/` — automated tests
- `docs/` — documentation ([index](docs/README.md))
- `demo/` — demo assets (e.g., fake corp filesystem for the MCP server target)
- `.claude/commands/` — reusable Claude command prompts

## REFERENCE

| Action | Command |
|--------|---------|
| Install | `uv sync` |
| Run | `uv run python -m mcp_security.main` |
| Scan assets | `uv run python -m mcp_security.scanner` |
| Static score | `uv run python -m mcp_security.static_scoring --kind filesystem` |
| Score calls | `uv run python -m mcp_security.call_scoring` |
| Test | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |

Full command reference: [docs/development/commands.md](docs/development/commands.md).

| Section | Path |
|---------|------|
| Project | [docs/project/](docs/project/) |
| Development | [docs/development/](docs/development/) |
| Standards | [docs/standards/](docs/standards/) |
| Claude | [docs/claude/](docs/claude/) |
| Guides | [docs/guides/](docs/guides/) |
