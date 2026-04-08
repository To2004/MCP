# Python Idioms and uv Workflow

Python language conventions and `uv` package-manager rules for the MCP
Security project. These were previously global rules — they now live here
so they only load on Python projects.

## Python Error Handling

- Use EAFP (`try/except`) over LBYL (`if/else` checks). Ask forgiveness,
  not permission.
- Keep `try` blocks small. Wrap only the single operation that can raise,
  not surrounding logic.
- Use context managers (`with`) for any resource that must be cleaned up:
  files, connections, locks.
- Never write a bare `except:` or `except Exception:` without re-raising.
  Catch only specific, expected exceptions.

## Python Security Hygiene

- Never use `eval()`, `exec()`, or `os.system()`. Use `subprocess.run()`
  with a list of arguments (never `shell=True` with user input).
- Prefer tuples over lists and frozensets over sets when the data should
  not change after creation.

## Type Hints

- Use `X | Y` union syntax, not `Union[X, Y]` or `Optional[X]`.
- Accept abstract types in parameters (`Sequence`, `Mapping`, `Iterable`);
  return concrete types (`list`, `dict`).
- Use `object` instead of `Any`. Reserve `Any` for genuinely untyped
  boundaries (e.g., JSON parsing).
- Use `Self` for methods that return their own class instance.

## String and Data Handling

- Use f-strings for interpolation. Never use `.format()` or `%` formatting.
- Use `pathlib.Path` for all file path operations. Do not use `os.path`.
- Use dataclasses or NamedTuples for structured data. Do not pass raw dicts
  or tuples across function boundaries.

## Pythonic Patterns

- Use properties instead of getter/setter methods.
- Use generator expressions with `all()`, `any()`, and `sum()` instead of
  building intermediate lists.
- Use `enumerate()` instead of manual index tracking.
- Use tuple unpacking: `x, y = get_coordinates()`, not indexed access.
- Every function must return a consistent type. Never return `str` on
  success and `None` on failure from the same function.

## Imports

- No wildcard imports (`from module import *`).
- Prefer absolute imports over relative imports.

## Python File Internal Layout (PEP 8 order)

1. Module docstring.
2. `from __future__ import ...`.
3. Module dunders (`__all__`, `__version__`).
4. Imports: stdlib, third-party, local (blank line between groups,
   alphabetical within each).
5. Module-level constants (`UPPER_SNAKE_CASE`).
6. Type aliases.
7. Classes (parent before child where possible).
8. Functions (public before private, callers before callees).
9. `if __name__ == "__main__":` block.

## uv: Running Code

- Always use `uv run <command>` instead of calling `python` directly. This
  guarantees the virtualenv is synced with the lockfile before execution.
- Never activate the virtualenv manually. Let `uv run` handle it.

## uv: Managing Dependencies

- Add packages with `uv add <pkg>`. Add dev-only packages with
  `uv add --dev <pkg>`.
- Never use `pip install`. All dependency changes must go through uv so
  the lockfile stays consistent.
- After manually editing `pyproject.toml`, run `uv lock` to regenerate
  the lockfile.

## uv: Environment and Lockfile

- Run `uv sync` to sync the local environment with the lockfile.
- Use `uv sync --locked` in CI and deployment to fail if the lockfile is
  out of date.
- Commit both `pyproject.toml` and `uv.lock` to version control.
- Never commit the `.venv/` directory. Add it to `.gitignore`.
- Never manually create or delete the `.venv/`. Let uv manage it entirely.

## uv: Dependency Groups

- Put test and lint tools (pytest, ruff, mypy) in dev dependencies using
  `--dev`.
- Keep runtime dependencies minimal. Do not put dev tools in the main
  dependency list.
