# Docs Organization

This document defines how the `docs/` folder itself is structured: what
each subcategory holds, how to format new doc files, and when to add a
new category.

## Subcategory Structure

```
docs/
├── README.md              # Index / navigation entry point
├── project/               # High-level project info
│   ├── overview.md
│   ├── architecture.md
│   └── roadmap.md
├── development/           # How to work on the project
│   ├── setup.md
│   ├── commands.md
│   ├── workflows.md
│   └── contributing.md
├── standards/             # Rules and conventions
│   ├── style-guide.md
│   ├── testing-guide.md
│   ├── patterns.md
│   ├── security-standards.md
│   ├── folder-layout.md
│   ├── naming-conventions.md
│   ├── data-organization.md
│   └── docs-organization.md
├── claude/                # Claude Code guidance
│   ├── working-with-claude.md
│   ├── commands-reference.md
│   └── conventions.md
└── guides/                # Step-by-step how-tos
    ├── adding-a-module.md
    ├── adding-tests.md
    └── debugging.md
```

## What Each Subcategory Holds

| Subcategory | Audience | Purpose | Example topics |
|-------------|----------|---------|----------------|
| `project/` | Everyone | What this project is | Overview, architecture, roadmap |
| `development/` | Contributors | How to work on it | Setup, commands, workflows |
| `standards/` | Contributors | Rules to follow | Style, testing, security, layout |
| `claude/` | Claude Code | AI collaboration guide | Conventions, commands |
| `guides/` | Everyone | Do X, step-by-step | Adding a module, debugging |

## File Structure Rules

Each doc file must:

1. Have exactly **one H1** (the title) at the top
2. Start with a **1–3 sentence intro** explaining what the doc covers
3. Use **H2** for major sections, **H3** for subsections
4. Use **H4 sparingly** — if you need H5, your structure is wrong
5. Leave **blank lines around every heading**
6. Use **unique, descriptive heading names** (link anchors come from these)

## Doc File Template

```markdown
# <Doc Title>

<1–3 sentence intro explaining what this doc covers and who it's for.>

## <First Major Section>

<Content.>

### <Subsection>

<Content.>

## <Second Major Section>

<Content.>

## References

<Links to related docs, external sources.>
```

## Table of Contents

- For docs **under 200 lines**: no TOC needed
- For docs **200–500 lines**: optional TOC after intro
- For docs **over 500 lines**: consider splitting into multiple docs

## Length Guidelines

| Doc type | Target length |
|----------|---------------|
| Standards (this folder) | 100–300 lines |
| Project overview | 50–150 lines |
| Guides | 100–400 lines |
| Architecture | 200–600 lines |

If a doc exceeds 600 lines, split it. Concise is kinder to the reader.

## Cross-Linking Rules

- **Use relative links** so they work on GitHub and locally:
  `[style-guide.md](style-guide.md)` not absolute URLs
- **Link to specific headings** with `#heading-slug`:
  `[naming rules](naming-conventions.md#python-identifiers-pep-8)`
- **Update `docs/README.md`** whenever you add a new doc
- **Update `CLAUDE.md`** if the new doc belongs in its Documentation Index

## Code Examples in Docs

- Use **fenced code blocks** with language tags: ` ```python `
- Keep examples **short and runnable**
- Use **this project's actual conventions**, not generic examples
- **Never** include real secrets, API keys, or passwords

## Tables vs Lists

- Use **tables** for comparison (2+ dimensions): rules, conventions, options
- Use **bullet lists** for sequential/unordered items (1 dimension)
- Use **numbered lists** only when order matters

## When to Add a New Doc

Add a new doc when:

1. The topic is distinct from existing docs
2. You have ≥100 lines of content to write
3. Contributors would search for it by name

Do **not** add a new doc when:

- You have 3 paragraphs — add them to an existing doc instead
- The content belongs in a code comment or docstring
- It duplicates or mostly overlaps an existing doc

## When to Add a New Subcategory

Default answer: **no**. The five existing subcategories
(`project/`, `development/`, `standards/`, `claude/`, `guides/`) cover
most needs.

Only add a new subcategory when:

1. You have ≥3 docs that share an audience and purpose
2. None of the existing subcategories fit
3. You update `docs/README.md` and `CLAUDE.md` Documentation Index

## README.md in Each Subfolder

Per the global `readme-folders` rule, every subfolder must have a
README.md linking to its docs:

```markdown
# <Subcategory Name>

<One-sentence description of this subcategory's purpose.>

| File | Description |
|------|-------------|
| [doc-1.md](doc-1.md) | <One-line summary> |
| [doc-2.md](doc-2.md) | <One-line summary> |
```

## References

- Google Markdown Style Guide: one H1, descriptive headings
- MkDocs writing guide: intro + TOC + sections structure
- See [folder-layout.md](folder-layout.md) for top-level project layout
