# Naming Conventions

This document defines naming rules for files, folders, and code identifiers
in the MCP Security project. Consistency beats personal preference — if in
doubt, match what already exists.

## Files

| Kind | Convention | Example |
|------|-----------|---------|
| Python modules | `snake_case.py` | `port_scanner.py` |
| Python tests | `test_<module>.py` | `test_port_scanner.py` |
| Markdown docs | `snake_case.md` or `kebab-case.md` | `folder-layout.md` |
| Config files | lowercase, tool-defined | `pyproject.toml`, `.gitignore` |
| LaTeX sources | `snake_case.tex` | `introduction.tex` |
| Scripts | `snake_case.py` or `snake_case.sh` | `download_papers.py` |

**Rule of thumb:** snake_case for anything the OS treats as a unit.
kebab-case is acceptable for docs since many projects use it — just pick
one style per folder and stay consistent.

## Folders

| Kind | Convention | Example |
|------|-----------|---------|
| Code folders | `snake_case` | `src/mcp_security/scoring/` |
| Doc folders | `snake_case` | `docs/development/` |
| Numbered research folders | `N_TopicName` | `1_MCP_Security/`, `2_MCP_Protocol/` |
| Score buckets | `Score_NN` | `Score_10/`, `Score_07/` |

The numbered prefix on research folders enforces reading order and groups
related scores together when listed alphabetically.

## Python Identifiers (PEP 8)

| Element | Convention | Example |
|---------|-----------|---------|
| Modules / packages | `snake_case` | `scoring`, `port_scanner` |
| Classes | `PascalCase` | `ScanResult`, `RiskScore` |
| Functions | `snake_case` | `scan_port()`, `compute_risk()` |
| Variables | `snake_case` | `timeout_seconds`, `result_list` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT`, `MAX_RETRIES` |
| Private (module-internal) | leading underscore | `_parse_response()`, `_cache` |
| Type vars | `PascalCase`, short | `T`, `ResultT` |

Aligns with [style-guide.md](style-guide.md). Full PEP 8 rules apply.

## Descriptive Naming Rules

- **Prefer full words** over abbreviations: `response` not `resp`, `config`
  not `cfg`
- **Exception**: universally-understood abbreviations are fine: `url`,
  `http`, `id`, `api`, `ip`
- **Boolean names** start with `is_`, `has_`, `should_`: `is_open`,
  `has_timeout`
- **Collection names** are plural: `ports`, `scan_results` (not `port_list`)
- **Function names are verbs**: `scan_ports()`, not `port_scanner()` for a
  function
- **Class names are nouns**: `ScanResult`, not `ScanResultData`

## Avoid

- Single-letter names (except loop indices `i`, `j`, `k` or math contexts)
- Type-suffixed names: `port_list`, `config_dict` → use `ports`, `config`
- Negated booleans: `is_not_ready` → use `is_ready`
- Hungarian notation: `strName`, `intCount`

## File Path Rules

- **No spaces in paths** — use underscores or hyphens
- **No special characters** except `-`, `_`, `.`
- **No mixed case folders on the same level** — pick one convention
- **Keep paths under 100 characters** where possible (Windows path limits)

## Test File Naming

- Test file: `test_<module_name>.py` (pytest discovery convention)
- Test function: `test_<behavior_described>()` e.g.,
  `test_scan_port_returns_true_when_port_open()`
- Test class (if used): `Test<Subject>` e.g., `TestPortScanner`
- Fixtures: `conftest.py` at the appropriate test directory level

## Data File Naming

For research artifacts (see
[data-organization.md](data-organization.md)):

- PDFs: keep original titles where reasonable, but remove spaces and
  special chars
- Summaries: `NN_paper_name_summary_LANG.md` e.g.,
  `02_MCPShield_summary_HE.md`
- Benchmark files: `NN_benchmark_name.md` e.g., `01_mcip_bench.md`

## Git Branch Names

- Feature: `feat/<short-description>` e.g., `feat/static-scoring`
- Fix: `fix/<short-description>` e.g., `fix/import-error`
- Docs: `docs/<short-description>` e.g., `docs/folder-layout`
- Use kebab-case within the description part

## Enforcement

- Python identifiers: enforced by Ruff (see `pyproject.toml`)
- File paths: enforced by code review and this document
- Git branches: convention, not enforced
