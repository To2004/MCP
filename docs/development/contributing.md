# Contributing

## Getting Started

1. Read the [Project Overview](../project/overview.md)
2. Follow the [Setup Guide](setup.md)
3. Review the [Style Guide](../standards/style-guide.md)

## Making Changes

1. Check for existing issues or discussions before starting
2. Create a feature branch from `main`
3. Write code following the [Style Guide](../standards/style-guide.md)
4. Add tests for new functionality (see [Adding Tests](../guides/adding-tests.md))
5. Run the full test suite and linter
6. Open a PR with a clear description

## Code Review Checklist

When reviewing (or self-reviewing) a PR:

- [ ] Code follows the style guide
- [ ] Functions are small and focused
- [ ] No hardcoded values
- [ ] Public functions have docstrings
- [ ] Tests cover the new/changed logic
- [ ] No unnecessary dependencies added
- [ ] Linter and tests pass

## What Makes a Good Contribution

- **Focused** — one concern per PR
- **Tested** — new logic has tests
- **Documented** — public APIs have docstrings; complex logic has comments
- **Minimal** — no unrelated changes, no premature abstractions

## Reporting Issues

Open a GitHub issue with:
- What you expected
- What happened instead
- Steps to reproduce
- Environment details (Python version, OS)
