# Design Patterns

## Preferred Patterns

### Early Returns

Reduce nesting by returning early for guard clauses:

```python
# Good
def process(data: str) -> Result:
    if not data:
        return Result.empty()
    if not is_valid(data):
        raise ValueError(f"Invalid data: {data}")
    return _do_processing(data)

# Avoid
def process(data: str) -> Result:
    if data:
        if is_valid(data):
            return _do_processing(data)
        else:
            raise ValueError(f"Invalid data: {data}")
    else:
        return Result.empty()
```

### Dataclasses for Structured Results

Return structured data instead of raw dicts or tuples:

```python
from dataclasses import dataclass

@dataclass
class ScanResult:
    host: str
    port: int
    is_open: bool
    banner: str | None = None
```

### Composition Over Inheritance

Prefer composing small, focused functions over class hierarchies:

```python
# Good
def scan_and_report(host: str, ports: list[int]) -> Report:
    results = scan_ports(host, ports)
    return build_report(results)

# Avoid
class BaseScanner:
    def scan(self): ...
    def report(self): ...

class PortScanner(BaseScanner): ...
```

### Explicit Configuration

Pass configuration as arguments, don't rely on global state:

```python
# Good
def scan(host: str, timeout: float = 5.0) -> ScanResult:
    ...

# Avoid
GLOBAL_TIMEOUT = 5.0
def scan(host: str) -> ScanResult:
    # uses GLOBAL_TIMEOUT implicitly
    ...
```

## Anti-Patterns to Avoid

- **God functions** — if a function does more than one thing, split it
- **Premature abstraction** — don't create base classes or factories until you have 3+ concrete cases
- **Silent failures** — don't catch and ignore exceptions
- **Mutable default arguments** — use `None` and assign inside the function
- **String typing** — use enums or constants instead of magic strings
