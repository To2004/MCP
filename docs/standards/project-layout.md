# Project Layout

Top-level structure of the MCP Security project, what each folder holds,
and how the `docs/` folder is organized.

## Top-Level Structure

```
MCP/
├── src/mcp_security/      # Application code (src layout)
├── tests/                 # Tests (mirrors src/ structure)
├── docs/                  # Project documentation
├── Litereture_review/     # Research: PDFs, summaries, benchmarks
├── mcp_learning_lab/      # Experiments and learning notes
├── .claude/               # Claude Code commands and settings
├── pyproject.toml         # Package config
├── uv.lock                # Locked dependencies
├── CLAUDE.md              # Top-level Claude instructions
└── README.md              # Entry point for humans
```

## What Goes Where

| Folder | Purpose | Do NOT put here |
|--------|---------|-----------------|
| `src/mcp_security/` | Shipping code | Tests, scratch scripts, data |
| `tests/` | `test_*.py` mirroring src/ | Fixtures >1MB |
| `docs/` | Markdown by category | Generated artifacts, data |
| `Litereture_review/` | Research inputs | Runnable package code |
| `mcp_learning_lab/` | Experiments | Production code |
| `.claude/` | Commands, local settings | Secrets (use `.env`) |

## Subpackage Rules

- Each subpackage = one logical domain (scanner, scoring, reporting)
- Create only when it contains ≥3 related modules
- Keep trees flat: `scoring/static.py` over `scoring/static/engine.py`

## Depth Limits

- Max 3 levels deep for code
- Max 4 levels deep for research artifacts
- If you need more, restructure

## When to Add a Top-Level Folder

Default: **no**. Only add when content fits no existing category, you
have ≥3 related files, and it has a distinct purpose.

## `docs/` Organization

```
docs/
├── README.md              # Navigation entry point
├── project/               # Overview, architecture, roadmap
├── development/           # Setup, commands, workflows, contributing
├── standards/             # Style, patterns, security, layout
├── claude/                # Claude Code guidance
└── guides/                # Step-by-step how-tos
```

## Doc File Structure

Each doc file must:

1. One H1 (title) at top
2. 1–3 sentence intro
3. H2 for major sections, H3 for subsections (avoid H4+)
4. Blank lines around every heading
5. Descriptive, unique heading names

## Doc Length Guidelines

| Doc type | Target |
|----------|--------|
| Standards | 100–300 lines |
| Project overview | 50–150 lines |
| Guides | 100–400 lines |

If >600 lines, split.

## Cross-Linking

- Relative links: `[file.md](file.md)` not absolute URLs
- Update `docs/README.md` when adding a doc
- Update `CLAUDE.md` if the doc belongs in its Documentation Index

## When to Add a New Doc

Add when the topic is distinct, you have ≥100 lines of content, and
contributors would search for it by name. Don't add when you have 3
paragraphs (add to an existing doc) or it duplicates existing content.

## Ignored Folders

Must be in `.gitignore`:

- `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`
- `*.egg-info/`, `dist/`, `build/`
- `.env`, `.env.local`

## READMEs

Every subfolder (except tool-managed ones) has a `README.md` linking to
its contents.
