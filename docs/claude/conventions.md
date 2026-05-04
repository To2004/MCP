# Claude Code Conventions

Formatting, commit, and PR conventions for Claude Code in this repo.

## INSTRUCTIONS

### Code generation

- Match existing patterns in the file being edited
- Use the same import style as surrounding code
- Follow the [Style and Naming](../standards/style-and-naming.md) guide
- Don't introduce new patterns unless existing ones are insufficient

### When suggesting changes

- Explain **why**, not just **what**
- Show the minimal change needed
- If multiple approaches exist, briefly note the trade-offs
- Don't over-engineer — simplest correct solution wins

### File placement

- Source files → `src/mcp_security/`
- Test files → `tests/`
- Documentation → `docs/`
- Command prompts → `.claude/commands/`

## OUTPUT FORMAT

### Commit messages

- Imperative mood: "Add feature" not "Added feature"
- First line under 72 characters
- Scope prefix when helpful: `scanner: add timeout config`
- Reference issues when applicable

### Pull requests

```markdown
## Summary
- Brief description of what changed and why

## Test Plan
- [ ] How to verify the changes work
```
