# Debugging Guide

Common issues and how to resolve them.

## Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'mcp_security'`

**Cause:** The virtual environment doesn't have the package installed, or
pytest can't find the source.

**Fix:**
```bash
uv sync
```

Verify `pyproject.toml` has the correct pytest configuration:
```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
```

## uv sync Fails

**Symptom:** `uv sync` fails with resolution errors.

**Fix:**
- Check your Python version: `python --version` (need 3.12+)
- Delete `.venv/` and retry: `rm -rf .venv && uv sync`
- Check `pyproject.toml` for dependency conflicts

## Tests Not Discovered

**Symptom:** `uv run pytest` runs 0 tests.

**Cause:** Test files or functions don't follow naming conventions.

**Fix:**
- Test files must start with `test_`
- Test functions must start with `test_`
- Test files must be in `tests/` directory

## Ruff Errors

**Symptom:** `uv run ruff check .` reports errors.

**Fix:**
```bash
# Auto-fix what Ruff can fix
uv run ruff check . --fix

# Auto-format
uv run ruff format .
```

For errors that can't be auto-fixed, read the error code and fix manually.
Ruff error codes are documented at [docs.astral.sh/ruff/rules](https://docs.astral.sh/ruff/rules/).

## Line Length Violations

**Symptom:** Ruff reports line-too-long errors.

**Fix:** The project uses 100-character lines (configured in `pyproject.toml`).
Break long lines using:
- Parenthesized line continuation
- Multi-line function arguments
- Intermediate variables for complex expressions

## Python Version Mismatch

**Note:** `.python-version` specifies 3.14, but `pyproject.toml` requires
>=3.12. If you don't have Python 3.14 installed, uv will use whatever
compatible version is available. This is expected and fine for development.
