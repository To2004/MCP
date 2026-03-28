# Guide: Adding a New Module

Step-by-step process for creating a new security module.

## 1. Create the Module Directory

```
src/mcp_security/
└── your_module/
    ├── __init__.py
    └── core.py
```

## 2. Write the Public API

In `__init__.py`, export the module's public interface:

```python
from mcp_security.your_module.core import scan, YourResult

__all__ = ["scan", "YourResult"]
```

## 3. Implement Core Logic

In `core.py`:

```python
from dataclasses import dataclass


@dataclass
class YourResult:
    """Result of the scan."""
    target: str
    finding: str
    severity: str


def scan(target: str, timeout: float = 5.0) -> list[YourResult]:
    """Scan a target for issues.

    Args:
        target: The target to scan.
        timeout: Maximum time in seconds per check.

    Returns:
        List of findings.
    """
    results = []
    # Implementation here
    return results
```

## 4. Create Tests

```
tests/
└── test_your_module.py
```

```python
from mcp_security.your_module import scan, YourResult


def test_scan_returns_results():
    results = scan("example.com")
    assert isinstance(results, list)


def test_scan_result_structure():
    results = scan("example.com")
    for result in results:
        assert isinstance(result, YourResult)
        assert result.target == "example.com"
```

## 5. Wire It Up (Optional)

If the module should be callable from the CLI, add it to `main.py`:

```python
from mcp_security.your_module import scan

def main() -> None:
    results = scan("target")
    for r in results:
        print(f"{r.severity}: {r.finding}")
```

## 6. Verify

```bash
uv run pytest
uv run ruff check .
```

Both must pass before committing.

## Checklist

- [ ] Module directory with `__init__.py` and `core.py`
- [ ] Public API exported in `__init__.py`
- [ ] Type hints on all public functions
- [ ] Docstrings on public functions and classes
- [ ] Test file with happy path and edge case tests
- [ ] Linter and tests pass
