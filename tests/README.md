# tests

Automated tests for the `mcp_security` package, using pytest.

## Layout

Tests mirror the structure of `src/mcp_security/`:

```
tests/
├── test_smoke.py              # Top-level smoke test
└── test_<module_name>.py      # Per-module tests added as code grows
```

For complex modules with many tests, use a subfolder:

```
tests/
└── test_<module_name>/
    ├── test_core.py
    └── test_utils.py
```

## Running Tests

From the repo root:

```bash
uv run pytest              # all tests
uv run pytest -v           # verbose
uv run pytest -k "scan"    # pattern match
uv run pytest -x           # stop on first failure
```

## Writing Tests

See [docs/standards/testing-guide.md](../docs/standards/testing-guide.md)
for naming conventions, what to test, and fixture patterns.
