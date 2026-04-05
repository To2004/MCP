# Standards

Rules and conventions for working in the MCP Security project.
Contributors should read these before making significant changes.

| File | Description |
|------|-------------|
| [style-guide.md](style-guide.md) | Python style: naming, formatting, type hints, docstrings |
| [testing-guide.md](testing-guide.md) | How to write and organize tests |
| [patterns.md](patterns.md) | Recurring design patterns used in this codebase |
| [security-standards.md](security-standards.md) | Security rules for defensive code |
| [folder-layout.md](folder-layout.md) | Top-level folder structure and where files belong |
| [naming-conventions.md](naming-conventions.md) | Naming rules for files, folders, and code identifiers |
| [data-organization.md](data-organization.md) | How research artifacts and data are organized |
| [docs-organization.md](docs-organization.md) | How `docs/` itself is structured |

## How Files Relate

- **style-guide.md** and **naming-conventions.md** overlap on code
  identifiers — `naming-conventions.md` extends the style guide to files
  and folders.
- **folder-layout.md** is the top-level map; **data-organization.md** and
  **docs-organization.md** drill down into specific folder trees.
- **testing-guide.md** builds on naming and folder layout for test files.

## Where to Start

- Writing Python code? → [style-guide.md](style-guide.md)
- Creating a new file or folder? → [folder-layout.md](folder-layout.md)
  then [naming-conventions.md](naming-conventions.md)
- Adding research artifacts? → [data-organization.md](data-organization.md)
- Adding documentation? → [docs-organization.md](docs-organization.md)
