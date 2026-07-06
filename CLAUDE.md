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
| Make new simulations | `uv run python scripts/make_simulations.py` |
| Scan (static, LLM-only) | `uv run python -m mcp_security.scanner --kind filesystem --root demo/corp_filesystem` |
| Scan (declarative kind) | `uv run python -m mcp_security.scanner --kind calendar` (also `github`, `slack`) |
| Param rubrics (LLM) | `uv run python -m mcp_security.param_scoring --kind filesystem --server fs:corp_filesystem` |
| Rank calls vs scan | `uv run python -m mcp_security.call_scoring` |
| Highlight most influential inputs | `uv run python scripts/highlight_influential_inputs.py` |
| Score one session (static + dynamic) | `uv run python -m mcp_security.dynamic --session <calls.csv> --server <scan-stem>` |
| Generate dynamic testbed (benign+malicious, big-MCP-weighted) | `uv run python scripts/make_dynamic_testbed.py` |
| Benign-vs-adversarial separation report | `uv run python scripts/evaluate_dynamic.py` |
| Full pipeline (multi-GPU) | `sbatch scripts/scan_and_rank_multigpu.sbatch` |
| Grade scanner (vs LLM tables) | `uv run python scripts/evaluate_scanner.py` |
| Grade scanner (vs oracle panel + inter-rater) | `uv run python scripts/evaluate_vs_human.py` |
| Formula sensitivity (band robustness) | `uv run python scripts/formula_sensitivity.py` |
| Verify pipeline (deterministic) | `uv run python -m mcp_security.review verify` |
| Review (verify + judge + results + advise) | `uv run python -m mcp_security.review all` |
| Export eval tables | `uv run python scripts/export_eval_tables.py` |
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
