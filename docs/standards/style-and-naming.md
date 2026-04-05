# Style and Naming

Python style, file naming, folder naming, and identifier conventions for
the MCP Security project.

## General Principles

- Readability over cleverness
- Explicit over implicit
- Descriptive names over comments
- Small functions that do one thing
- Consistency beats personal preference — match what exists

## Python Identifiers (PEP 8)

| Element | Convention | Example |
|---------|-----------|---------|
| Modules / packages | `snake_case` | `port_scanner`, `scoring` |
| Classes | `PascalCase` | `ScanResult`, `RiskScore` |
| Functions / variables | `snake_case` | `scan_port()`, `timeout_seconds` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT` |
| Private | leading underscore | `_parse_response()` |
| Type vars | `PascalCase`, short | `T`, `ResultT` |

Enforced by Ruff — see `pyproject.toml`.

## Descriptive Naming Rules

- Prefer full words over abbreviations: `response` not `resp`
- Exceptions: `url`, `http`, `id`, `api`, `ip`
- Booleans start with `is_`, `has_`, `should_`: `is_open`, `has_timeout`
- Collections are plural: `ports`, `scan_results`
- Functions are verbs; classes are nouns
- Avoid: single-letter names (except loop indices), type suffixes
  (`port_list` → `ports`), negated booleans, Hungarian notation

## File Naming

| Kind | Convention | Example |
|------|-----------|---------|
| Python modules | `snake_case.py` | `port_scanner.py` |
| Python tests | `test_<module>.py` | `test_port_scanner.py` |
| Markdown docs | `kebab-case.md` or `snake_case.md` | `project-layout.md` |
| Config files | lowercase, tool-defined | `pyproject.toml` |
| Scripts | `snake_case.py` / `.sh` | `download_papers.py` |

**Rule:** snake_case for anything the OS treats as a unit; pick one doc
style per folder and stay consistent.

## Folder Naming

| Kind | Convention | Example |
|------|-----------|---------|
| Code folders | `snake_case` | `src/mcp_security/scoring/` |
| Doc folders | `snake_case` | `docs/development/` |
| Numbered research folders | `N_TopicName` | `1_MCP_Security/` |
| Score buckets | `Score_NN` | `Score_10/` |

## File Path Rules

- No spaces; only `-`, `_`, `.` as separators
- No mixed case folders on the same level
- Keep paths under 100 characters (Windows limit)

## Formatting

Enforced by Ruff:

- Line length: 100
- Indentation: 4 spaces
- Quotes: double

Run `uv run ruff format .`.

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

## Type Hints and Docstrings

Add type hints to function signatures. Add Google-style docstrings to
public functions and classes:

```python
def scan_ports(host: str, ports: list[int]) -> list[ScanResult]:
    """Scan multiple ports on a host.

    Args:
        host: Target hostname or IP address.
        ports: Ports to scan.

    Returns:
        One result per port.

    Raises:
        ConnectionError: If the host is unreachable.
    """
```

Skip docstrings for obvious internal helpers and tests.

## Error Handling

- Raise specific exceptions, not bare `Exception`
- Catch only what you can handle meaningfully
- Let unexpected errors propagate
- Use custom exceptions for domain errors

## Constants

No hardcoded values in function bodies. Define at module level:

```python
DEFAULT_TIMEOUT = 5.0
MAX_RETRIES = 3
```

## Test Naming

- File: `test_<module_name>.py`
- Function: `test_<behavior>()` e.g., `test_scan_port_returns_true_when_open()`
- Class: `Test<Subject>` e.g., `TestPortScanner`
- Fixtures: `conftest.py` at the appropriate level

## Git Branch Names

- `feat/<description>`, `fix/<description>`, `docs/<description>`
- Use kebab-case within the description part

## References

- See [project-layout.md](project-layout.md) for where files belong
- See [data-organization.md](data-organization.md) for research artifact naming
