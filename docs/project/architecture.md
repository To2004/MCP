# Architecture

## Package Structure

```
src/mcp_security/
├── __init__.py          Package root
├── main.py              CLI entry point
├── <module>/            One directory per security tool
│   ├── __init__.py      Public API for the module
│   ├── core.py          Core logic
│   └── utils.py         Module-specific helpers (if needed)
```

## Entry Point

The project runs via:

```
python -m mcp_security.main
```

`main.py` is the top-level orchestrator. It imports and delegates to individual
modules. Keep `main.py` thin — it should parse arguments and call module APIs,
not contain business logic.

## Module Design

Each security tool should be its own module (subdirectory) under
`src/mcp_security/`. Modules should:

1. Expose a clear public API via `__init__.py`
2. Keep internal implementation details private (prefix with `_`)
3. Accept configuration as function arguments, not global state
4. Return structured results (dataclasses or typed dicts), not print directly
5. Be independently testable without requiring other modules

## Dependency Flow

```
main.py
  └── module_a/
  └── module_b/
  └── ...
```

Modules should not depend on each other. If shared utilities emerge, they belong
in a `common/` or `shared/` package — but only create this when genuinely needed
by multiple modules.

## Testing Strategy

Tests mirror the source structure:

```
tests/
├── test_smoke.py              Top-level smoke test
├── test_<module>/             One directory per module
│   ├── test_core.py
│   └── test_utils.py
```

See [Testing Guide](../standards/testing-guide.md) for conventions.
