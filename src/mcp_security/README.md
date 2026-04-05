# mcp_security

Main application package for the MCP Security risk scoring framework.

## Purpose

Implements the scoring engine that evaluates AI agent requests to MCP
servers and returns a risk score used to gate, throttle, or deny risky
interactions. See [docs/project/overview.md](../../docs/project/overview.md)
for the framework design.

## Module Layout

| Module | Responsibility |
|--------|----------------|
| `main.py` | CLI entry point (`python -m mcp_security.main`) |

The package is in early development. Subpackages will be added as the
scoring engine, threat model, and integration layers are built. See
[docs/project/architecture.md](../../docs/project/architecture.md) for the
planned structure.

## Installation and Running

From the repo root:

```bash
uv sync                              # install package in editable mode
uv run python -m mcp_security.main   # run entry point
```

## Tests

Tests for this package live in [`tests/`](../../tests/) and mirror the
package structure. See [docs/standards/testing-guide.md](../../docs/standards/testing-guide.md).
