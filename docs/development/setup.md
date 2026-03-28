# Development Setup

## Prerequisites

- **Python 3.12+** — check with `python --version`
- **uv** — install from [docs.astral.sh/uv](https://docs.astral.sh/uv/)

> Note: `.python-version` specifies Python 3.14 for the project. If you don't
> have 3.14, uv will use any compatible version (>=3.12 per pyproject.toml).

## Getting Started

```bash
# Clone the repository
git clone <repo-url>
cd MCP

# Install dependencies (creates .venv automatically)
uv sync

# Verify the install
uv run python -m mcp_security.main
# Expected output: "MCP Security project is running."

# Run tests
uv run pytest
# Expected: 1 passed

# Run linter
uv run ruff check .
# Expected: All checks passed
```

## IDE Setup

### VS Code

Recommended extensions:
- **Python** (ms-python.python)
- **Ruff** (charliermarsh.ruff)

Settings (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": ".venv/Scripts/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "editor.rulers": [100]
}
```

### PyCharm

- Set the project interpreter to `.venv/`
- Enable Ruff as an external tool or plugin
- Set right margin to 100

## Troubleshooting

See [Debugging Guide](../guides/debugging.md) for common issues.
