# Claude Code Commands Reference

Custom commands are stored in `.claude/commands/` and invoked with `/` in the
Claude Code prompt.

## Available Commands

### /plan

**File:** `.claude/commands/plan.md`

Creates an implementation plan for a requested change. Use this before starting
non-trivial work to align on approach.

**When to use:** Before making large or multi-file changes.

### /implement

**File:** `.claude/commands/implement.md`

Implements a requested change following project conventions. Keeps code modular,
testable, and suggests where tests should go.

**When to use:** When you're ready to write code after planning.

### /review

**File:** `.claude/commands/review.md`

Reviews the current codebase and suggests improvements in priority order.

**When to use:** For code review, quality checks, or finding improvements.

## Creating New Commands

1. Create a markdown file in `.claude/commands/`
2. Write the prompt template as the file content
3. The filename (without `.md`) becomes the command name
4. Invoke with `/<filename>` in Claude Code

### Tips for Good Commands

- Keep prompts focused on one task
- Reference project conventions (link to docs/ if needed)
- Include constraints (e.g., "run tests after changes")
- Be explicit about expected output format
