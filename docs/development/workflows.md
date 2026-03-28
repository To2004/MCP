# Development Workflows

## Branch Strategy

- `main` is the default branch — keep it stable
- Create feature branches for new work: `feature/<short-description>`
- Create fix branches for bugs: `fix/<short-description>`
- Keep branches short-lived — merge or close within a few days

## Development Cycle

1. **Create a branch** from `main`
2. **Make changes** — small, focused commits
3. **Run tests** — `uv run pytest` before every commit
4. **Run linter** — `uv run ruff check .`
5. **Push and open a PR** against `main`
6. **Review** — address feedback, keep the PR focused
7. **Merge** — squash or rebase preferred

## Commit Messages

Use clear, imperative-mood messages:

```
Add port scanner module
Fix false positive in header check
Update pytest to 8.1.0
```

Prefix with scope when helpful:

```
scanner: add timeout configuration
tests: add integration tests for scanner
docs: update setup instructions
```

## Before Pushing

Always run this checklist:

```bash
uv run ruff check .
uv run ruff format . --check
uv run pytest
```

All three must pass before pushing.

## Pull Requests

- Keep PRs focused on one change
- Write a clear title and description
- Link to related issues if applicable
- Ensure tests pass in CI before merging
