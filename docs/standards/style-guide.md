# Python Style Guide

## General Principles

- Readability over cleverness
- Explicit over implicit
- Descriptive names over comments
- Small functions that do one thing

## Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | `snake_case` | `port_scanner.py` |
| Functions | `snake_case` | `scan_ports()` |
| Classes | `PascalCase` | `ScanResult` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT` |
| Private | Leading underscore | `_parse_response()` |

Use descriptive names. Avoid abbreviations unless universally understood
(e.g., `url`, `http`, `id`).

## Formatting

Enforced by Ruff. Key settings from `pyproject.toml`:

- **Line length**: 100 characters
- **Indentation**: 4 spaces
- **Quotes**: double quotes (Ruff default)

Run `uv run ruff format .` to auto-format.

## Type Hints

Use type hints for function signatures:

```python
def scan_port(host: str, port: int, timeout: float = 5.0) -> bool:
    """Check if a port is open on the given host."""
    ...
```

Use `from __future__ import annotations` for forward references when needed.

## Docstrings

Add docstrings to public functions and classes. Use Google style:

```python
def scan_ports(host: str, ports: list[int]) -> list[ScanResult]:
    """Scan multiple ports on a host.

    Args:
        host: Target hostname or IP address.
        ports: List of port numbers to scan.

    Returns:
        List of scan results, one per port.

    Raises:
        ConnectionError: If the host is unreachable.
    """
```

Skip docstrings for obvious internal helpers and tests.

## Imports

Order (enforced by Ruff):

1. Standard library
2. Third-party packages
3. Local imports

```python
import os
from pathlib import Path

import pytest

from mcp_security.scanner import scan_ports
```

## Error Handling

- Raise specific exceptions, not bare `Exception`
- Only catch exceptions you can handle meaningfully
- Let unexpected errors propagate — don't silence them
- Use custom exceptions for domain-specific errors

## Constants

No hardcoded values in function bodies. Define constants at module level:

```python
DEFAULT_TIMEOUT = 5.0
MAX_RETRIES = 3

def connect(host: str, timeout: float = DEFAULT_TIMEOUT) -> Connection:
    ...
```
