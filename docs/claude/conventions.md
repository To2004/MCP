# Claude Code Conventions

Rules for how Claude should format output, commits, and PRs in this project.

## Commit Messages

- Use imperative mood: "Add feature" not "Added feature"
- Keep the first line under 72 characters
- Add scope prefix when helpful: `scanner: add timeout config`
- Reference issues when applicable

## Pull Request Descriptions

Use this structure:

```markdown
## Summary
- Brief description of what changed and why

## Test Plan
- [ ] How to verify the changes work
```

## Code Generation Rules

- Match existing patterns in the file being edited
- Use the same import style as surrounding code
- Follow the [Style and Naming](../standards/style-and-naming.md) guide
- Don't introduce new patterns unless the existing ones are insufficient

## When Suggesting Changes

- Explain **why**, not just **what**
- Show the minimal change needed
- If multiple approaches exist, briefly note the trade-offs
- Don't over-engineer — the simplest correct solution wins

## File Organization

When creating new files:
- Source files go in `src/mcp_security/`
- Test files go in `tests/`
- Documentation goes in `docs/`
- Command prompts go in `.claude/commands/`
