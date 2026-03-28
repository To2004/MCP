# Command Reference

All commands use `uv run` to execute within the project's virtual environment.

## Core Commands

| Command | Description |
|---------|-------------|
| `uv sync` | Install/update all dependencies |
| `uv run python -m mcp_security.main` | Run the project |
| `uv run pytest` | Run all tests |
| `uv run ruff check .` | Lint the codebase |
| `uv run ruff format .` | Auto-format the codebase |

## Testing

```bash
# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_smoke.py

# Run tests matching a name pattern
uv run pytest -k "test_import"

# Run with verbose output
uv run pytest -v

# Run with print output visible
uv run pytest -s
```

## Linting and Formatting

```bash
# Check for lint errors (read-only)
uv run ruff check .

# Auto-fix lint errors where possible
uv run ruff check . --fix

# Format code
uv run ruff format .

# Check formatting without changing files
uv run ruff format . --check
```

## Dependency Management

```bash
# Add a runtime dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Remove a dependency
uv remove <package>

# Update all dependencies
uv sync --upgrade
```
