# Folder Layout

This document defines the top-level folder structure of the MCP Security
project, what each folder holds, and how to decide where new files belong.

## Top-Level Structure

```
MCP/
├── src/mcp_security/      # Main application code (src layout)
├── tests/                 # Automated tests (mirrors src structure)
├── docs/                  # Project documentation
├── Litereture_review/     # Research artifacts (PDFs, summaries, benchmarks)
├── mcp_learning_lab/      # Hands-on experiments and learning notes
├── .claude/               # Claude Code commands and local settings
├── pyproject.toml         # Package config and dependencies
├── uv.lock                # Locked dependency versions
├── CLAUDE.md              # Top-level Claude instructions
└── README.md              # Entry point for humans
```

## What Goes Where

| Folder | Purpose | Do put here | Do NOT put here |
|--------|---------|-------------|-----------------|
| `src/mcp_security/` | Shipping Python code | Modules, subpackages, `__init__.py` | Tests, scratch scripts, data files |
| `tests/` | Automated tests | `test_*.py` files mirroring `src/` | Fixtures >1MB (use external storage) |
| `docs/` | Human documentation | Markdown files organized by category | Generated artifacts, data |
| `Litereture_review/` | Research inputs | PDFs, paper summaries, benchmark reviews | Runnable code for the package |
| `mcp_learning_lab/` | Experiments | Prototypes, exploration, learning notes | Production code |
| `.claude/` | Claude tooling | Reusable command prompts, local settings | Secrets (use `.env`) |

## `src/mcp_security/` Subpackage Rules

- Each subpackage reflects a **logical domain** (scanner, scoring, reporting)
- A subpackage is only warranted when it contains ≥3 related modules
- Keep subpackage trees flat — prefer `src/mcp_security/scoring/static.py`
  over `src/mcp_security/scoring/static/engine.py`

## `docs/` Subcategories

See [docs-organization.md](docs-organization.md) for the full breakdown.
Quick summary: `project/`, `development/`, `standards/`, `claude/`, `guides/`.

## `Litereture_review/` Subcategories

| Subfolder | Contents |
|-----------|----------|
| `PDF/` | Source papers, grouped by topic then score (e.g., `1_MCP_Security/Score_10/`) |
| `reviews/` | Paper summaries, figures, reading notes |
| `Benchmark/` | Benchmark dataset reviews |
| `Excels/` | Spreadsheets tracking papers |
| `Latex/` | Thesis LaTeX sources |
| `scripts/` | Helper scripts for processing the review |

See [data-organization.md](data-organization.md) for naming and grouping rules.

## Depth Limits

- **Max 3 levels deep** for code (`src/mcp_security/scoring/static.py`)
- **Max 4 levels deep** for research artifacts
  (`Litereture_review/PDF/1_MCP_Security/Score_10/`)
- If you need more depth, the structure is probably wrong — flatten or
  regroup

## When to Create a New Top-Level Folder

Only create a new top-level folder when:

1. The content doesn't fit any existing category
2. You have ≥3 files that belong together
3. The content has a distinct purpose from existing folders

Default answer is **no** — find an existing home first.

## README in Every Folder

Every folder (except `__pycache__`, `.venv`, `.git`, etc.) MUST have a
`README.md` explaining:

- What the folder contains
- How files in it relate to each other
- How to navigate its contents

See [docs-organization.md](docs-organization.md) for the README template.

## Ignored Folders

These are managed by tools and MUST be in `.gitignore`:

- `.venv/` — managed by `uv`, never commit
- `__pycache__/`, `.pytest_cache/`, `.ruff_cache/` — tool caches
- `*.egg-info/`, `dist/`, `build/` — build artifacts

## References

- Python Packaging Guide: src layout is preferred for packaged libraries
- Harvard RDM: separate raw data from generated artifacts
- One-project-per-repo unless projects share substantial data
