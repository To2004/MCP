# Testing Guide

## Framework

We use **pytest** with the following configuration (from `pyproject.toml`):

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

## File Structure

Tests mirror the source tree:

```
tests/
├── test_smoke.py              Top-level smoke test
├── test_<module_name>.py      Simple module tests
├── test_<module_name>/        Complex module test suites
│   ├── test_core.py
│   └── test_utils.py
```

## Naming

- Test files: `test_<name>.py`
- Test functions: `test_<what_it_tests>()`
- Be descriptive: `test_scan_returns_open_for_listening_port()`

## Writing Tests

### Basic Pattern

```python
from mcp_security.scanner import scan_port

def test_scan_detects_open_port():
    result = scan_port("localhost", 80)
    assert result.is_open is True

def test_scan_detects_closed_port():
    result = scan_port("localhost", 99999)
    assert result.is_open is False
```

### What to Test

- **Happy path** — correct inputs produce correct outputs
- **Edge cases** — empty inputs, boundary values, None
- **Error cases** — invalid inputs raise appropriate exceptions
- **Return values** — verify type, structure, and content

### What NOT to Test

- Implementation details (private functions, internal state)
- Third-party library behavior
- Trivial code (simple property access, pass-through functions)

## Fixtures

Use pytest fixtures for shared setup:

```python
import pytest

@pytest.fixture
def sample_hosts():
    return ["192.168.1.1", "192.168.1.2"]

def test_batch_scan(sample_hosts):
    results = batch_scan(sample_hosts, port=80)
    assert len(results) == 2
```

## Running Tests

```bash
uv run pytest              # All tests
uv run pytest -v           # Verbose
uv run pytest -k "scan"    # Pattern match
uv run pytest -x           # Stop on first failure
```

## Coverage

When coverage tooling is added, aim for meaningful coverage — test logic and
branching, not line count.
