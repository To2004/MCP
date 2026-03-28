# Guide: Adding Tests

How to write and organize tests for this project.

## 1. Create the Test File

Place tests in the `tests/` directory, mirroring the source structure:

| Source File | Test File |
|-------------|-----------|
| `src/mcp_security/main.py` | `tests/test_smoke.py` |
| `src/mcp_security/scanner/core.py` | `tests/test_scanner.py` or `tests/test_scanner/test_core.py` |

## 2. Write the Test

```python
from mcp_security.your_module import your_function


def test_your_function_happy_path():
    """Test normal operation."""
    result = your_function("valid_input")
    assert result.status == "success"


def test_your_function_empty_input():
    """Test edge case: empty input."""
    result = your_function("")
    assert result.status == "empty"


def test_your_function_invalid_input():
    """Test error case: invalid input raises."""
    import pytest
    with pytest.raises(ValueError, match="Invalid"):
        your_function("bad_input")
```

## 3. Use Fixtures for Shared Setup

```python
import pytest


@pytest.fixture
def sample_config():
    return {"timeout": 5.0, "retries": 3}


def test_with_config(sample_config):
    result = run_scan(config=sample_config)
    assert result is not None
```

## 4. Run Your Tests

```bash
# Run all tests
uv run pytest

# Run just your new test file
uv run pytest tests/test_your_module.py

# Run with verbose output to see each test
uv run pytest tests/test_your_module.py -v
```

## What to Cover

- **Happy path** — expected inputs, expected outputs
- **Edge cases** — empty strings, zero values, boundary conditions
- **Error cases** — invalid inputs should raise specific exceptions
- **Return types** — verify the structure, not just truthiness

## What to Skip

- Don't test private functions directly
- Don't test third-party library behavior
- Don't test trivial pass-through code
- Don't mock unless you have a compelling reason (prefer real objects)
