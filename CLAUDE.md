# CLAUDE.md

This file gives guidance to Claude Code when working in this repository.

## Project Overview
MCP Security is a Python project managed with uv.

The goal of this repository is to build security-related tooling in a clean,
modular, and testable way.

## Tech Stack
- Python
- uv for dependency management
- pytest for tests
- Ruff for linting

## Directory Structure
- `src/mcp_security/` → main application code
- `tests/` → automated tests
- `.claude/commands/` → reusable Claude Code command prompts

## Commands
Install dependencies:
`uv sync`

Run the project:
`uv run python -m mcp_security.main`

Run tests:
`uv run pytest`

Lint:
`uv run ruff check .`

## Coding Rules
- Use descriptive names
- Keep functions small and focused
- Avoid hardcoded values
- Add docstrings to important functions
- Prefer readability over clever code
- Write tests for important logic
- Do not add unnecessary dependencies

## Workflow Rules
- First inspect the codebase and explain the plan before large changes
- For non-trivial work, propose steps before editing many files
- After making changes, run tests
- When adding a new feature, also suggest where tests should go