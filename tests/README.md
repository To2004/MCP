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

## Attack Testbed

The `testbed/` subdirectory is an attack harness for empirical security evaluation.
It is independent of the regular unit tests and runs against real MCP servers.

See [testbed/README.md](testbed/README.md) for full documentation.

Quick run:

```bash
uv run python -m tests.testbed.harness.attack_runner --server filesystem --mode attack
uv run python -m tests.testbed.harness.attack_runner --all --scenarios --mode eval
```
