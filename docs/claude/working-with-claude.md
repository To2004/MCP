# Working with Claude Code

## How Claude Should Approach This Project

These rules govern how Claude Code operates in this repository.

### Before Making Changes

1. **Read before editing** — always inspect relevant files before modifying them
2. **Plan before acting** — for non-trivial work, explain the approach before
   editing multiple files
3. **Understand context** — check existing patterns, imports, and conventions
   before writing new code

### While Making Changes

- Follow the [Style Guide](../standards/style-guide.md) exactly
- Keep functions small and focused
- Use descriptive names — no abbreviations unless standard
- Add docstrings to public functions
- Add type hints to function signatures
- No hardcoded values — use constants or parameters
- Prefer readability over cleverness

### After Making Changes

1. **Run tests** — `uv run pytest` after every change
2. **Run linter** — `uv run ruff check .`
3. **Suggest tests** — when adding a feature, propose where tests should go

### What to Avoid

- Don't add dependencies unless absolutely necessary
- Don't refactor code beyond what was asked
- Don't add comments to code you didn't change
- Don't create abstractions for one-time operations
- Don't guess at requirements — ask the user

## When to Read Docs

Claude loads `CLAUDE.md` automatically. For deeper context, read the relevant
docs/ file:

| Task | Read |
|------|------|
| Adding a new module | [Adding a Module](../guides/adding-a-module.md) |
| Writing tests | [Testing Guide](../standards/testing-guide.md) |
| Style questions | [Style Guide](../standards/style-guide.md) |
| Security concerns | [Security Standards](../standards/security-standards.md) |
| Understanding architecture | [Architecture](../project/architecture.md) |
