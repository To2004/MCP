# MCP Filesystem Tools — Docs + Teaching Deck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce `docs/mcp-tools/filesystem.md` (student reference) and `presentations/mcp-filesystem-tools.pptx` (18-slide teaching deck) explaining every MCP filesystem tool with input/output tables, good/bad examples, and edge cases.

**Architecture:** The markdown doc is written directly; the PPTX is generated programmatically by `scripts/generate_filesystem_deck.py` using python-pptx. The script is self-contained — no external images, all diagrams drawn with shapes. A pytest smoke test verifies slide count and key title text.

**Tech Stack:** Python 3.12, python-pptx 1.0.2 (already in pyproject.toml), pytest, uv

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `docs/mcp-tools/filesystem.md` | Full tool reference for students |
| Create | `scripts/generate_filesystem_deck.py` | Generates the PPTX file |
| Create | `presentations/mcp-filesystem-tools.pptx` | Generated output (committed) |
| Create | `tests/test_filesystem_deck.py` | Smoke test: slide count + title text |

---

## Task 1: Write `docs/mcp-tools/filesystem.md`

**Files:**
- Create: `docs/mcp-tools/filesystem.md`

This is the full reference doc. No code — pure markdown. Write it in one pass.

- [ ] **Step 1: Create the file**

Write `docs/mcp-tools/filesystem.md` with the following exact content:

````markdown
# MCP Filesystem Server — Tool Reference

The MCP filesystem server (`@modelcontextprotocol/server-filesystem`) exposes a sandboxed
directory to AI agents via JSON-RPC 2.0. Agents call named tools; the server executes them
and returns results. Every operation is confined to the **allowed root** passed at server
startup — no escaping it.

## Overview

### Security Boundary

The server enforces one rule: every path must live inside the allowed root.

- `../` traversal → `Error: Path outside allowed directory`
- Absolute path outside root → same error
- Empty path → `Error: Access denied`

No path gymnastics can break out. The server resolves symlinks and checks the real path.

### Tool Categories

| Category | Tools |
|----------|-------|
| Read | `read_text_file`, `read_media_file`, `read_multiple_files` |
| Write | `write_file`, `edit_file` |
| Navigate | `list_directory`, `list_directory_with_sizes`, `directory_tree`, `search_files` |
| Info / Admin | `get_file_info`, `create_directory`, `move_file`, `list_allowed_directories` |

---

## Read Tools

### `read_text_file`

**What it does:** Returns the full text content of a file as a UTF-8 string.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | yes | Absolute or root-relative path to the file |
| `head` | number | no | Return only the first N lines |
| `tail` | number | no | Return only the last N lines |

**Output:** `{ "content": "<file text as string>" }`

**File types that work well:** `.txt`, `.md`, `.csv`, `.sql`, `.c`, `.py`, `.sh`, `.pem`, `.json`, `.yaml`

**File types that behave oddly:** `.png`, `.pdf`, `.docx`, `.xlsx`, `.exe`, `.sys` — these are binary.
The server will attempt to decode them as UTF-8 and will either return garbled output or an
encoding error. Use `read_media_file` for binaries.

**Good example:**

```json
// Request
{
  "method": "tools/call",
  "params": {
    "name": "read_text_file",
    "arguments": { "path": "sensitive/security/audit_log.txt" }
  }
}

// Response
{
  "content": "2026-01-15 09:00 | LOGIN  | eve@corp.com | success\n2026-01-15 09:04 | READ   | audit_log.txt | success\n"
}
```

**Bad example:**

```json
// Request — wrong tool for a binary file
{
  "method": "tools/call",
  "params": {
    "name": "read_text_file",
    "arguments": { "path": "onboarding/org_chart.png" }
  }
}

// Response — garbled or error
{
  "content": "Error: Could not decode file as UTF-8. Use read_media_file for binary files."
}
```

> **Edge cases**
> - `head: 5` returns lines 1–5; `tail: 3` returns the last 3 lines. You cannot combine them.
> - A file with Windows line endings (`\r\n`) is returned as-is — the agent sees the raw bytes.
> - Reading a 0-byte file returns `{ "content": "" }` — not an error.

---

### `read_media_file`

**What it does:** Returns a binary file's content as a base64-encoded blob with its MIME type.
Use this for images, PDFs, Office documents, and executables.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | yes | Path to the binary file |

**Output:**

```json
{
  "content": [
    {
      "type": "image",
      "data": "<base64-encoded bytes>",
      "mimeType": "image/png"
    }
  ]
}
```

The `type` field is `"image"` for images, `"audio"` for audio, `"blob"` for everything else
(PDF, DOCX, XLSX, EXE, SYS).

**File types and their `type`/`mimeType`:**

| Extension | `type` | `mimeType` |
|-----------|--------|------------|
| `.png` | `image` | `image/png` |
| `.jpg` | `image` | `image/jpeg` |
| `.pdf` | `blob` | `application/pdf` |
| `.docx` | `blob` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `.xlsx` | `blob` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `.exe` | `blob` | `application/octet-stream` |
| `.sys` | `blob` | `application/octet-stream` |

**Good example:**

```json
// Request
{
  "method": "tools/call",
  "params": {
    "name": "read_media_file",
    "arguments": { "path": "public/logo.png" }
  }
}

// Response
{
  "content": [
    {
      "type": "image",
      "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk...",
      "mimeType": "image/png"
    }
  ]
}
```

**Bad example:**

```json
// Request — using read_media_file on a text file wastes tokens
{
  "method": "tools/call",
  "params": {
    "name": "read_media_file",
    "arguments": { "path": "sensitive/security/audit_log.txt" }
  }
}

// Response — works, but you get base64 of plain text instead of the string directly
{
  "content": [
    { "type": "blob", "data": "MjAyNi0wMS0xNSA...", "mimeType": "text/plain" }
  ]
}
// Use read_text_file instead — you get a readable string at lower cost.
```

> **Edge cases**
> - `.exe` and `.sys` files decode successfully but the base64 is opaque — an LLM cannot
>   meaningfully interpret machine code. Metadata from `get_file_info` is more useful.
> - Very large files (>10 MB) may hit context limits when base64-encoded.

---

### `read_multiple_files`

**What it does:** Reads several files in one call and returns their contents in a single
response. A failure on one path does not abort the rest — the error is inlined.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `paths` | string[] | yes | Array of paths, minimum 1 |

**Output:** A single string block with each file's content separated by headers, or inline
errors for paths that failed.

**File types:** Same rules as `read_text_file` — works for text files. Binary paths will
return inline decode errors.

**Good example:**

```json
// Request
{
  "method": "tools/call",
  "params": {
    "name": "read_multiple_files",
    "arguments": {
      "paths": [
        "sensitive/financials/payslips_q1.csv",
        "projects/known_defects.csv"
      ]
    }
  }
}

// Response
{
  "content": "=== sensitive/financials/payslips_q1.csv ===\nemployee_id,name,salary\n101,Alice,72000\n...\n\n=== projects/known_defects.csv ===\nid,title,severity\n1,Memory leak in auth,high\n..."
}
```

**Bad example:**

```json
// Request — one valid path, one bad path
{
  "method": "tools/call",
  "params": {
    "name": "read_multiple_files",
    "arguments": {
      "paths": [
        "sensitive/financials/payslips_q1.csv",
        "sensitive/security/private_key.pem",
        "does_not_exist.txt"
      ]
    }
  }
}

// Response — partial success, error inlined (does NOT fail the whole call)
{
  "content": "=== sensitive/financials/payslips_q1.csv ===\nemployee_id,...\n\n=== sensitive/security/private_key.pem ===\n-----BEGIN PRIVATE KEY-----\n...\n\n=== does_not_exist.txt ===\nError: ENOENT: no such file or directory"
}
```

> **Edge cases**
> - The response is one big string — you must parse it yourself to separate files.
> - There is no atomicity: some files may succeed while others fail.
> - Passing a single-element array is valid but slower than `read_text_file` for one file.

---

## Write Tools

### `write_file`

**What it does:** Creates a new file or **completely overwrites** an existing one with the
given content string. There is no confirmation, no backup, no diff — the old content is gone.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | yes | Destination path (created if it doesn't exist) |
| `content` | string | yes | Full text content to write |

**Output:** `{ "content": "Successfully wrote to <path>" }`

**File types:** Always writes the `content` string as UTF-8 text. Not suitable for binary
files (you cannot write a PNG or EXE this way).

**Good example:**

```json
// Request — creating a new notes file
{
  "method": "tools/call",
  "params": {
    "name": "write_file",
    "arguments": {
      "path": "source_code/sprint_notes.txt",
      "content": "Sprint 12 goals:\n- Fix memory leak\n- Add unit tests\n"
    }
  }
}

// Response
{ "content": "Successfully wrote to source_code/sprint_notes.txt" }
```

**Bad example:**

```json
// Request — accidentally overwriting an existing important file
{
  "method": "tools/call",
  "params": {
    "name": "write_file",
    "arguments": {
      "path": "sensitive/security/audit_log.txt",
      "content": "log cleared"
    }
  }
}

// Response — succeeds silently, original audit log is GONE
{ "content": "Successfully wrote to sensitive/security/audit_log.txt" }

// The server does not warn you. Always check get_file_info first
// if you are unsure whether the file already exists.
```

> **Edge cases**
> - Parent directories must exist — writing to `a/b/c.txt` when `a/b/` doesn't exist fails.
> - Annotations: `destructiveHint: true`, `idempotentHint: true`.
> - Missing `content` parameter → `-32602` validation error.

---

### `edit_file`

**What it does:** Applies one or more find-and-replace operations to an existing file and
returns a git-style diff of the changes.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | yes | Path to an existing file |
| `edits` | array | yes | List of `{ "oldText": "...", "newText": "..." }` objects |
| `dryRun` | boolean | no | If `true`, returns the diff without saving (default: `false`) |

**Output:** A git-style unified diff string showing what changed.

**File types:** Text files only. Works on `.txt`, `.md`, `.csv`, `.c`, `.py`, `.sql`, etc.

**Good example:**

```json
// Request — fix a typo in sprint notes
{
  "method": "tools/call",
  "params": {
    "name": "edit_file",
    "arguments": {
      "path": "source_code/sprint_notes.txt",
      "edits": [
        { "oldText": "Fix memory leak", "newText": "Fix memory leak in auth module" }
      ],
      "dryRun": false
    }
  }
}

// Response — git-style diff
{
  "content": "--- source_code/sprint_notes.txt\n+++ source_code/sprint_notes.txt\n@@ -1,3 +1,3 @@\n Sprint 12 goals:\n-Fix memory leak\n+Fix memory leak in auth module\n Add unit tests\n"
}
```

**Bad example:**

```json
// Request — oldText doesn't exactly match the file content
{
  "method": "tools/call",
  "params": {
    "name": "edit_file",
    "arguments": {
      "path": "source_code/sprint_notes.txt",
      "edits": [
        { "oldText": "fix memory leak", "newText": "done" }
      ]
    }
  }
}

// Response — fails because match is case-sensitive
{
  "content": "Error: Could not find text to replace: 'fix memory leak'"
}
```

> **Edge cases**
> - Match is **exact and case-sensitive** — whitespace counts.
> - `edits` is applied in order; if edit 2 depends on edit 1's result, that works.
> - `dryRun: true` is useful to preview before committing changes.
> - Annotations: `destructiveHint: true`, `idempotentHint: false`.

---

## Navigation Tools

### `list_directory`

**What it does:** Lists the immediate contents of a directory. Each entry is prefixed with
`[FILE]` or `[DIR]`.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | yes | Path to a directory |

**Output:** A newline-separated string like:
```
[DIR] contracts
[DIR] financials
[DIR] security
```

**Good example:**

```json
// Request
{
  "method": "tools/call",
  "params": {
    "name": "list_directory",
    "arguments": { "path": "sensitive" }
  }
}

// Response
{ "content": "[DIR] contracts\n[DIR] financials\n[DIR] security\n" }
```

**Bad example:**

```json
// Request — passing a file path instead of a directory
{
  "method": "tools/call",
  "params": {
    "name": "list_directory",
    "arguments": { "path": "sensitive/security/audit_log.txt" }
  }
}

// Response
{ "content": "Error: Not a directory: sensitive/security/audit_log.txt" }
```

> **Edge cases**
> - Lists only one level deep — not recursive. Use `directory_tree` for recursive views.
> - An empty directory returns `{ "content": "" }` — not an error.

---

### `list_directory_with_sizes`

**What it does:** Same as `list_directory` but includes file sizes in bytes. Supports sorting.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | yes | Path to a directory |
| `sortBy` | string | no | `"name"` (default) or `"size"` |

**Output:**
```
[FILE] audit_log.txt    134 B
[FILE] private_key.pem  110 B
```

**Good example:**

```json
{
  "method": "tools/call",
  "params": {
    "name": "list_directory_with_sizes",
    "arguments": { "path": "sensitive/financials", "sortBy": "size" }
  }
}
// Response: files sorted largest first
{ "content": "[FILE] payslips_q1.csv    74 B\n[FILE] budget_2026.xlsx   15 B\n" }
```

**Bad example:**

```json
// Invalid sortBy value
{
  "method": "tools/call",
  "params": {
    "name": "list_directory_with_sizes",
    "arguments": { "path": "sensitive/financials", "sortBy": "date" }
  }
}
// Response
{ "content": "Error: Invalid sortBy value: 'date'. Must be 'name' or 'size'." }
```

> **Edge cases**
> - Directory sizes are not shown — only files have size values.
> - `sortBy: "size"` sorts descending (largest first).

---

### `directory_tree`

**What it does:** Returns the full recursive tree of a directory as a JSON structure with
`name`, `type` (`"file"` or `"directory"`), and `children` fields.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | yes | Root of the tree |
| `excludePatterns` | string[] | no | Glob patterns to skip (e.g., `["*.log", "node_modules"]`) |

**Output:**

```json
{
  "name": "sensitive",
  "type": "directory",
  "children": [
    { "name": "contracts", "type": "directory", "children": [
        { "name": "master_agreement.pdf", "type": "file" },
        { "name": "nda_template.docx", "type": "file" }
    ]},
    ...
  ]
}
```

**Good example:**

```json
// Request — get tree of source_code, skip build artifacts
{
  "method": "tools/call",
  "params": {
    "name": "directory_tree",
    "arguments": {
      "path": "source_code",
      "excludePatterns": ["*.exe", "*.obj"]
    }
  }
}
// Response — JSON tree with .exe excluded
```

**Bad example:**

```json
// Request — running directory_tree on the entire root with no excludes
{
  "method": "tools/call",
  "params": {
    "name": "directory_tree",
    "arguments": { "path": "." }
  }
}
// This works but returns a huge JSON blob for large filesystems.
// Use list_directory or search_files when you only need a subset.
```

> **Edge cases**
> - The output is a JSON string, not a pre-parsed object — you must parse it.
> - `excludePatterns` uses glob syntax: `*.log` matches in any directory, `logs/*` only in `logs/`.

---

### `search_files`

**What it does:** Finds files matching a glob pattern within a directory. Returns a list of
full matching paths.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | yes | Directory to search within |
| `pattern` | string | yes | Glob pattern |
| `excludePatterns` | string[] | no | Patterns to skip |

**Output:** Newline-separated list of matching paths.

**Glob pattern cheatsheet:**

| Pattern | Matches |
|---------|---------|
| `*` | Any file in the `path` directory only (not recursive) |
| `**/*` | Every file recursively under `path` |
| `**/*.csv` | Every `.csv` file recursively under `path` |
| `sensitive/**/*.pdf` | Every `.pdf` inside `sensitive/` |
| `*.txt` | `.txt` files in `path` only |

**Good example:**

```json
// Find all CSVs anywhere under the root
{
  "method": "tools/call",
  "params": {
    "name": "search_files",
    "arguments": { "path": ".", "pattern": "**/*.csv" }
  }
}
// Response
{
  "content": "sensitive/financials/payslips_q1.csv\nprojects/known_defects.csv\n"
}
```

**Bad example:**

```json
// Common mistake: using * thinking it's recursive
{
  "method": "tools/call",
  "params": {
    "name": "search_files",
    "arguments": { "path": ".", "pattern": "*.csv" }
  }
}
// Response — EMPTY (no CSVs directly in the root; they're in subdirectories)
{ "content": "" }
// Fix: use **/*.csv
```

> **Edge cases**
> - `*` is NOT recursive. This is the #1 beginner mistake.
> - An empty result is not an error — it just means no files matched.
> - Patterns are case-sensitive on Linux/Mac, case-insensitive on Windows.

---

## Info & Admin Tools

### `get_file_info`

**What it does:** Returns metadata about a file or directory: size, timestamps, type, and
permissions. Does not read the file content.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | yes | File or directory path |

**Output:**
```
size: 134
created: 2026-01-10T08:00:00.000Z
modified: 2026-01-15T09:04:00.000Z
accessed: 2026-01-15T09:04:00.000Z
isDirectory: false
isFile: true
permissions: 644
```

**Good example:**

```json
// Check metadata before deciding whether to read a file
{
  "method": "tools/call",
  "params": {
    "name": "get_file_info",
    "arguments": { "path": "source_code/build.exe" }
  }
}
// Response — you see it's 2.3 MB; decide not to base64-encode it
```

**Bad example:**

```json
// Passing a path that doesn't exist
{
  "method": "tools/call",
  "params": {
    "name": "get_file_info",
    "arguments": { "path": "sensitive/secret.txt" }
  }
}
// Response
{ "content": "Error: ENOENT: no such file or directory, stat 'sensitive/secret.txt'" }
```

> **Edge cases**
> - Works on both files and directories.
> - Use this before `write_file` to check if a file already exists.

---

### `create_directory`

**What it does:** Creates a directory (and any missing parent directories). Safe to call if
the directory already exists — it does nothing and returns success.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | yes | Directory path to create |

**Output:** `{ "content": "Successfully created directory <path>" }`

**Good example:**

```json
{
  "method": "tools/call",
  "params": {
    "name": "create_directory",
    "arguments": { "path": "source_code/feature_branch/utils" }
  }
}
// Creates source_code/feature_branch/ and source_code/feature_branch/utils/ in one call
```

**Bad example:**

```json
// Trying to create a directory where a file already exists with that name
{
  "method": "tools/call",
  "params": {
    "name": "create_directory",
    "arguments": { "path": "sensitive/security/audit_log.txt" }
  }
}
// Response
{ "content": "Error: EEXIST: file exists, mkdir '...audit_log.txt'" }
```

> **Edge cases**
> - Annotations: `destructiveHint: false`, `idempotentHint: true` — safe to retry.
> - Creates nested paths in one call (`a/b/c` creates all three levels).

---

### `move_file`

**What it does:** Moves or renames a file or directory. Fails if the destination already exists.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `source` | string | yes | Existing file/directory path |
| `destination` | string | yes | Target path |

**Output:** `{ "content": "Successfully moved <source> to <destination>" }`

**Good example:**

```json
{
  "method": "tools/call",
  "params": {
    "name": "move_file",
    "arguments": {
      "source": "source_code/sprint_notes.txt",
      "destination": "source_code/feature_branch/sprint_notes.txt"
    }
  }
}
```

**Bad example:**

```json
// Destination already exists — move fails
{
  "method": "tools/call",
  "params": {
    "name": "move_file",
    "arguments": {
      "source": "source_code/core.c",
      "destination": "source_code/build.exe"
    }
  }
}
// Response
{ "content": "Error: Destination already exists: source_code/build.exe" }
```

> **Edge cases**
> - Annotations: `destructiveHint: false`, `idempotentHint: false` — not safe to retry blindly.
> - There is no `copy_file` — if you need a copy, read + write.

---

### `list_allowed_directories`

**What it does:** Returns the list of root directories the server was started with. No parameters.

**Input:** *(none)*

**Output:** `{ "content": "Allowed directories:\n/path/to/corp_filesystem_sim\n" }`

**Good example:**

```json
// First call in any session — orient yourself
{
  "method": "tools/call",
  "params": { "name": "list_allowed_directories", "arguments": {} }
}
// Response tells you what root the server has access to
```

**Bad example:**

```json
// There is no bad example — this tool always succeeds.
// The only mistake is not calling it first and then guessing paths.
```

> **Edge cases**
> - Call this as your very first tool when exploring an unknown server.
> - The server may have multiple allowed directories if started with multiple roots.

---

## Edge Cases & Gotchas

### Glob Patterns

The most common mistake is using `*` when you need `**/*`.

| Pattern | Searches | Recursive? | Example result |
|---------|----------|------------|----------------|
| `*` | `path/` only | No | `README.md` (only if in root) |
| `**/*` | `path/` and all subdirs | Yes | Every file everywhere |
| `**/*.csv` | All subdirs | Yes | Only `.csv` files |
| `sensitive/**/*.pdf` | `sensitive/` subtree | Yes | PDFs inside sensitive/ |

```
search_files(path=".", pattern="*.csv")   → []  (WRONG — CSVs are in subdirs)
search_files(path=".", pattern="**/*.csv") → ["sensitive/financials/payslips_q1.csv", ...]
```

### Path Pitfalls

| Input | Result |
|-------|--------|
| `""` (empty string) | `Error: Access denied` |
| `../etc/passwd` | `Error: Path outside allowed directory` |
| `C:/Windows/win.ini` | `Error: Path outside allowed directory` |
| `./sensitive/` (trailing slash) | Works — trailing slash is stripped |
| `sensitive` vs `./sensitive` | Both work — same path |

### `write_file` Silently Overwrites

```json
// File exists with 500 lines of audit data
write_file("audit_log.txt", "cleared")
// → Success. 500 lines gone. No warning.

// Safe pattern: check first
get_file_info("audit_log.txt")   // confirm it exists / check size
// Then decide whether to write
```

### `read_multiple_files` Partial Failure

```json
// One bad path does NOT abort the batch
read_multiple_files(["payslips.csv", "MISSING.txt", "audit_log.txt"])
// → payslips.csv: OK content
// → MISSING.txt:  Error: ENOENT
// → audit_log.txt: OK content
// All in one response string — check for "Error:" inline
```

### Tools That Don't Exist

These tools are intentionally absent — calling them returns error code `-32602`:

| Tool you tried | Why it's missing |
|----------------|-----------------|
| `delete_file` | Irreversible — agents can't destroy data |
| `execute_shell` | Arbitrary code execution is out of scope |
| `copy_file` | Not needed — read + write achieves the same |
| `chmod` / `chown` | Permission changes not exposed to agents |

---

## File Type Behavior Matrix

| File type | `read_text_file` | `read_media_file` | `write_file` | `search_files` |
|-----------|-----------------|-------------------|--------------|----------------|
| `.txt` | ✅ Plain string | ⚠️ base64 (wasteful) | ✅ | ✅ |
| `.md` | ✅ Plain string | ⚠️ base64 (wasteful) | ✅ | ✅ |
| `.csv` | ✅ Plain string | ⚠️ base64 (wasteful) | ✅ | ✅ |
| `.sql` | ✅ Plain string | ⚠️ base64 (wasteful) | ✅ | ✅ |
| `.c` / code | ✅ Plain string | ⚠️ base64 (wasteful) | ✅ | ✅ |
| `.sh` / `.bash` | ✅ Plain string | ⚠️ base64 (wasteful) | ✅ | ✅ |
| `.pem` | ✅ Plain string | ⚠️ base64 (wasteful) | ✅ | ✅ |
| `.png` | ❌ Decode error | ✅ base64 image blob | ❌ binary | ✅ |
| `.pdf` | ❌ Decode error | ✅ base64 blob | ❌ binary | ✅ |
| `.docx` | ❌ Decode error | ✅ base64 blob | ❌ binary | ✅ |
| `.xlsx` | ❌ Decode error | ✅ base64 blob | ❌ binary | ✅ |
| `.exe` | ❌ Decode error | ✅ base64 blob (opaque) | ❌ binary | ✅ |
| `.sys` | ❌ Decode error | ✅ base64 blob (opaque) | ❌ binary | ✅ |

Legend: ✅ = correct tool · ⚠️ = works but suboptimal · ❌ = wrong tool / fails
````

- [ ] **Step 2: Verify the file renders cleanly**

Open `docs/mcp-tools/filesystem.md` in any markdown viewer and confirm:
- All 14 tools have sections
- Every tool has Input table, Good example, Bad example, Edge cases
- File type matrix table at the bottom

- [ ] **Step 3: Commit**

```bash
git add docs/mcp-tools/filesystem.md
git commit -m "docs: add MCP filesystem server tool reference"
```

---

## Task 2: Scaffold `scripts/generate_filesystem_deck.py`

**Files:**
- Create: `scripts/generate_filesystem_deck.py`

Build the theme constants and helper functions. No slides yet — just the skeleton.

- [ ] **Step 1: Write the file**

Create `scripts/generate_filesystem_deck.py`:

```python
"""Generate the MCP Filesystem Tools teaching deck (18 slides)."""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
BG = RGBColor(0x1E, 0x1E, 0x2E)       # dark navy background
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0x89, 0xB4, 0xFA)   # blue accent
GREEN = RGBColor(0xA6, 0xE3, 0xA1)    # good example
RED = RGBColor(0xF3, 0x8B, 0xA8)      # bad example / error
YELLOW = RGBColor(0xF9, 0xE2, 0xAF)   # warning / edge case
GRAY = RGBColor(0x45, 0x47, 0x5A)     # subtle box fill
MONO_FONT = "Courier New"
BODY_FONT = "Calibri"

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

OUTPUT = Path(__file__).parent.parent / "presentations" / "mcp-filesystem-tools.pptx"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def new_presentation() -> Presentation:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def add_slide(prs: Presentation):
    """Add a blank slide and paint the background."""
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = BG
    return slide


def text_box(slide, left, top, width, height, text, size=Pt(18), bold=False,
             color=WHITE, font=BODY_FONT, align=PP_ALIGN.LEFT, wrap=True):
    """Add a text box and return the shape."""
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = size
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    return txb


def code_box(slide, left, top, width, height, code, fill=GRAY, text_color=WHITE):
    """A monospace code block with a filled background rectangle."""
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height,
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = fill

    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = code
    run.font.size = Pt(12)
    run.font.name = MONO_FONT
    run.font.color.rgb = text_color
    return shape


def label_box(slide, left, top, width, height, text, fill=ACCENT, text_color=BG, size=Pt(14)):
    """Colored label / badge box."""
    shape = slide.shapes.add_shape(1, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = fill
    tf = shape.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.size = size
    run.font.bold = True
    run.font.name = BODY_FONT
    run.font.color.rgb = text_color
    return shape


def arrow(slide, x1, y1, x2, y2, color=ACCENT):
    """Draw a horizontal right-pointing connector arrow."""
    from pptx.util import Emu
    connector = slide.shapes.add_connector(
        1,  # MSO_CONNECTOR_TYPE.STRAIGHT
        x1, y1, x2, y2,
    )
    connector.line.color.rgb = color
    connector.line.width = Pt(2)
    return connector


def slide_title(slide, title, subtitle=None):
    """Add a slide title (large) and optional subtitle."""
    text_box(slide, Inches(0.5), Inches(0.2), Inches(12.3), Inches(0.9),
             title, size=Pt(32), bold=True, color=ACCENT)
    if subtitle:
        text_box(slide, Inches(0.5), Inches(1.0), Inches(12.3), Inches(0.5),
                 subtitle, size=Pt(18), color=WHITE)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_deck() -> Presentation:
    prs = new_presentation()
    _slide_01_title(prs)
    _slide_02_what_is_mcp(prs)
    _slide_03_request_response(prs)
    _slide_04_security_boundary(prs)
    _slide_05_read_overview(prs)
    _slide_06_read_text_file(prs)
    _slide_07_read_media_file(prs)
    _slide_08_read_multiple_files(prs)
    _slide_09_write_tools(prs)
    _slide_10_list_tools(prs)
    _slide_11_search_files(prs)
    _slide_12_info_admin(prs)
    _slide_13_file_type_matrix(prs)
    _slide_14_glob_patterns(prs)
    _slide_15_path_pitfalls(prs)
    _slide_16_silent_overwrite(prs)
    _slide_17_partial_batch(prs)
    _slide_18_missing_tools(prs)
    return prs


if __name__ == "__main__":
    prs = generate_deck()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUTPUT)
    print(f"Saved: {OUTPUT}")
```

Note: each `_slide_NN_*` function will be added in subsequent tasks. Add them as stubs for now so the script runs:

```python
def _slide_01_title(prs): add_slide(prs)
def _slide_02_what_is_mcp(prs): add_slide(prs)
def _slide_03_request_response(prs): add_slide(prs)
def _slide_04_security_boundary(prs): add_slide(prs)
def _slide_05_read_overview(prs): add_slide(prs)
def _slide_06_read_text_file(prs): add_slide(prs)
def _slide_07_read_media_file(prs): add_slide(prs)
def _slide_08_read_multiple_files(prs): add_slide(prs)
def _slide_09_write_tools(prs): add_slide(prs)
def _slide_10_list_tools(prs): add_slide(prs)
def _slide_11_search_files(prs): add_slide(prs)
def _slide_12_info_admin(prs): add_slide(prs)
def _slide_13_file_type_matrix(prs): add_slide(prs)
def _slide_14_glob_patterns(prs): add_slide(prs)
def _slide_15_path_pitfalls(prs): add_slide(prs)
def _slide_16_silent_overwrite(prs): add_slide(prs)
def _slide_17_partial_batch(prs): add_slide(prs)
def _slide_18_missing_tools(prs): add_slide(prs)
```

Place the stubs **before** `generate_deck()` in the file.

- [ ] **Step 2: Verify it runs**

```bash
uv run python scripts/generate_filesystem_deck.py
```

Expected: `Saved: .../presentations/mcp-filesystem-tools.pptx` and a valid (18 blank dark slides) PPTX file.

- [ ] **Step 3: Write the failing test**

Create `tests/test_filesystem_deck.py`:

```python
"""Smoke tests for the filesystem teaching deck generator."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_filesystem_deck import generate_deck


def test_deck_has_18_slides():
    prs = generate_deck()
    assert len(prs.slides) == 18


def test_slide_backgrounds_are_dark():
    from pptx.dml.color import RGBColor
    prs = generate_deck()
    for i, slide in enumerate(prs.slides):
        fill = slide.background.fill
        # solid fill should be the dark BG color
        assert fill.fore_color.rgb == RGBColor(0x1E, 0x1E, 0x2E), f"Slide {i+1} wrong bg"
```

- [ ] **Step 4: Run the test — expect PASS (stubs produce 18 blank dark slides)**

```bash
uv run pytest tests/test_filesystem_deck.py -v
```

Expected:
```
PASSED tests/test_filesystem_deck.py::test_deck_has_18_slides
PASSED tests/test_filesystem_deck.py::test_slide_backgrounds_are_dark
```

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_filesystem_deck.py tests/test_filesystem_deck.py
git commit -m "feat: scaffold PPTX generator with stubs and smoke tests"
```

---

## Task 3: Implement Act 1 — Protocol Overview Slides (slides 1–4)

**Files:**
- Modify: `scripts/generate_filesystem_deck.py` — replace stubs for slides 1–4

Replace each stub function one at a time with the real implementation below.

- [ ] **Step 1: Implement `_slide_01_title`**

```python
def _slide_01_title(prs: Presentation):
    slide = add_slide(prs)
    # Main title
    text_box(slide, Inches(1), Inches(2.2), Inches(11.3), Inches(1.5),
             "MCP Filesystem Server", size=Pt(48), bold=True, color=ACCENT,
             align=PP_ALIGN.CENTER)
    text_box(slide, Inches(1), Inches(3.7), Inches(11.3), Inches(0.8),
             "How It Works — Tool Reference & Teaching Guide",
             size=Pt(24), color=WHITE, align=PP_ALIGN.CENTER)
    text_box(slide, Inches(1), Inches(5.2), Inches(11.3), Inches(0.5),
             "@modelcontextprotocol/server-filesystem  v1.27.0",
             size=Pt(16), color=GRAY, align=PP_ALIGN.CENTER)
```

- [ ] **Step 2: Implement `_slide_02_what_is_mcp`**

```python
def _slide_02_what_is_mcp(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "What is MCP?",
                "Model Context Protocol — lets AI agents call tools on external servers")

    # Draw: Agent → JSON-RPC → MCP Server → Filesystem
    boxes = [
        (Inches(0.5),  "AI Agent",       ACCENT),
        (Inches(3.5),  "JSON-RPC 2.0",   YELLOW),
        (Inches(6.5),  "MCP Server",      GREEN),
        (Inches(9.5),  "Filesystem",      GRAY),
    ]
    for left, label, color in boxes:
        label_box(slide, left, Inches(3.2), Inches(2.5), Inches(1.0),
                  label, fill=color, text_color=BG, size=Pt(16))

    # Arrows between boxes
    for i in range(3):
        x1 = Inches(0.5 + i * 3 + 2.5)
        x2 = Inches(0.5 + (i + 1) * 3)
        arrow(slide, x1, Inches(3.7), x2, Inches(3.7))

    text_box(slide, Inches(0.5), Inches(4.5), Inches(12.3), Inches(1.2),
             "An agent sends a JSON-RPC request naming a tool (e.g. read_text_file) with "
             "parameters. The MCP server executes it and returns a result. "
             "The filesystem server exposes 14 tools — all sandboxed to an allowed root.",
             size=Pt(16), color=WHITE)
```

- [ ] **Step 3: Implement `_slide_03_request_response`**

```python
def _slide_03_request_response(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "Request → Response Flow")

    request_json = (
        '{\n'
        '  "jsonrpc": "2.0",\n'
        '  "id": 1,\n'
        '  "method": "tools/call",\n'
        '  "params": {\n'
        '    "name": "read_text_file",\n'
        '    "arguments": {\n'
        '      "path": "sensitive/security/audit_log.txt"\n'
        '    }\n'
        '  }\n'
        '}'
    )
    response_json = (
        '{\n'
        '  "jsonrpc": "2.0",\n'
        '  "id": 1,\n'
        '  "result": {\n'
        '    "content": [\n'
        '      {\n'
        '        "type": "text",\n'
        '        "text": "2026-01-15 09:00 | LOGIN..."\n'
        '      }\n'
        '    ]\n'
        '  }\n'
        '}'
    )

    text_box(slide, Inches(0.5), Inches(1.5), Inches(5.5), Inches(0.4),
             "REQUEST", size=Pt(14), bold=True, color=GREEN)
    code_box(slide, Inches(0.5), Inches(1.9), Inches(5.5), Inches(4.8), request_json)

    arrow(slide, Inches(6.2), Inches(4.2), Inches(7.0), Inches(4.2))

    text_box(slide, Inches(7.2), Inches(1.5), Inches(5.5), Inches(0.4),
             "RESPONSE", size=Pt(14), bold=True, color=ACCENT)
    code_box(slide, Inches(7.2), Inches(1.9), Inches(5.5), Inches(4.8), response_json)
```

- [ ] **Step 4: Implement `_slide_04_security_boundary`**

```python
def _slide_04_security_boundary(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "The Security Boundary",
                "Every path must live inside the allowed root — no exceptions")

    # Allowed root box (green border)
    root_box = slide.shapes.add_shape(1, Inches(0.5), Inches(1.8), Inches(6.0), Inches(4.5))
    root_box.fill.solid()
    root_box.fill.fore_color.rgb = RGBColor(0x1A, 0x2A, 0x1A)
    root_box.line.color.rgb = GREEN
    root_box.line.width = Pt(2)
    text_box(slide, Inches(0.7), Inches(1.9), Inches(5.5), Inches(0.4),
             "✓  Allowed root: /corp_filesystem/", size=Pt(14), bold=True, color=GREEN)
    for path in ["sensitive/security/audit_log.txt",
                 "projects/known_defects.csv",
                 "source_code/core.c"]:
        text_box(slide, Inches(0.9), Inches(2.0 + 0.5 * ["sensitive/security/audit_log.txt",
                 "projects/known_defects.csv", "source_code/core.c"].index(path)),
                 Inches(5.5), Inches(0.45),
                 f"  {path}", size=Pt(13), color=WHITE)

    # Blocked attempts (red)
    blocked = [
        ("../etc/passwd", "Path outside allowed directory"),
        ("C:/Windows/win.ini", "Path outside allowed directory"),
        ("(empty string)", "Access denied"),
    ]
    for i, (attempt, error) in enumerate(blocked):
        y = Inches(2.1 + i * 1.1)
        label_box(slide, Inches(7.0), y, Inches(3.5), Inches(0.45),
                  f"✗  {attempt}", fill=RED, text_color=WHITE, size=Pt(12))
        text_box(slide, Inches(7.0), Inches(y + Inches(0.5)), Inches(5.5), Inches(0.4),
                 f"→ Error: {error}", size=Pt(11), color=RED)
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/test_filesystem_deck.py -v
```

Expected: both tests still PASS (slide count = 18, all backgrounds dark).

- [ ] **Step 6: Commit**

```bash
git add scripts/generate_filesystem_deck.py
git commit -m "feat: implement Act 1 slides (protocol overview)"
```

---

## Task 4: Implement Act 2 — Tools in Action (slides 5–13)

**Files:**
- Modify: `scripts/generate_filesystem_deck.py` — replace stubs for slides 5–13

- [ ] **Step 1: Implement `_slide_05_read_overview`**

```python
def _slide_05_read_overview(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "Read Tools")

    tools = [
        ("read_text_file",     "Returns file content as a UTF-8 string.\nBest for: .txt .md .csv .sql .c .sh .pem"),
        ("read_media_file",    "Returns binary as base64 blob + MIME type.\nBest for: .png .pdf .docx .xlsx .exe .sys"),
        ("read_multiple_files","Reads an array of files in one call.\nPartial failure doesn't abort the batch."),
    ]
    for i, (name, desc) in enumerate(tools):
        x = Inches(0.5 + i * 4.2)
        label_box(slide, x, Inches(2.0), Inches(3.9), Inches(0.55),
                  name, fill=ACCENT, text_color=BG, size=Pt(14))
        text_box(slide, x, Inches(2.7), Inches(3.9), Inches(1.5),
                 desc, size=Pt(14), color=WHITE)
```

- [ ] **Step 2: Implement `_slide_06_read_text_file`**

```python
def _slide_06_read_text_file(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "read_text_file",
                'Input: path (str), optional head/tail (int) → Output: plain UTF-8 string')

    # File types that work
    text_box(slide, Inches(0.5), Inches(1.8), Inches(6.0), Inches(0.4),
             "Works with:", size=Pt(14), bold=True, color=GREEN)
    text_box(slide, Inches(0.5), Inches(2.2), Inches(6.0), Inches(0.5),
             ".txt   .md   .csv   .sql   .c   .py   .sh   .bash   .pem",
             size=Pt(14), color=GREEN, font=MONO_FONT)

    text_box(slide, Inches(0.5), Inches(2.9), Inches(6.0), Inches(0.4),
             "Do NOT use with (binary — use read_media_file):", size=Pt(14), bold=True, color=RED)
    text_box(slide, Inches(0.5), Inches(3.3), Inches(6.0), Inches(0.5),
             ".png   .pdf   .docx   .xlsx   .exe   .sys",
             size=Pt(14), color=RED, font=MONO_FONT)

    # Good example
    text_box(slide, Inches(7.0), Inches(1.8), Inches(5.8), Inches(0.4),
             "✓ Good", size=Pt(13), bold=True, color=GREEN)
    code_box(slide, Inches(7.0), Inches(2.2), Inches(5.8), Inches(1.6),
             'read_text_file(\n  path="sensitive/security/audit_log.txt"\n)\n→ "2026-01-15 09:00 | LOGIN | ..."',
             fill=RGBColor(0x1A, 0x2A, 0x1A), text_color=GREEN)

    # Bad example
    text_box(slide, Inches(7.0), Inches(4.0), Inches(5.8), Inches(0.4),
             "✗ Bad — binary file", size=Pt(13), bold=True, color=RED)
    code_box(slide, Inches(7.0), Inches(4.4), Inches(5.8), Inches(1.6),
             'read_text_file(\n  path="onboarding/org_chart.png"\n)\n→ Error: Cannot decode as UTF-8',
             fill=RGBColor(0x2A, 0x1A, 0x1A), text_color=RED)

    text_box(slide, Inches(0.5), Inches(6.2), Inches(12.3), Inches(0.6),
             "Edge case: head=5 → first 5 lines only. tail=3 → last 3 lines. Cannot combine.",
             size=Pt(13), color=YELLOW)
```

- [ ] **Step 3: Implement `_slide_07_read_media_file`**

```python
def _slide_07_read_media_file(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "read_media_file",
                "Input: path (str) → Output: base64 blob + mimeType")

    text_box(slide, Inches(0.5), Inches(1.8), Inches(6.0), Inches(0.4),
             "Use for binary files:", size=Pt(14), bold=True, color=ACCENT)
    rows = [
        (".png / .jpg", "image", "image/png"),
        (".pdf",        "blob",  "application/pdf"),
        (".docx",       "blob",  "application/vnd.openxmlformats..."),
        (".xlsx",       "blob",  "application/vnd.openxmlformats..."),
        (".exe / .sys", "blob",  "application/octet-stream"),
    ]
    for i, (ext, typ, mime) in enumerate(rows):
        y = Inches(2.3 + i * 0.55)
        text_box(slide, Inches(0.5), y, Inches(2.0), Inches(0.5),
                 ext, size=Pt(13), color=WHITE, font=MONO_FONT)
        text_box(slide, Inches(2.6), y, Inches(1.2), Inches(0.5),
                 typ, size=Pt(13), color=ACCENT, font=MONO_FONT)
        text_box(slide, Inches(4.0), y, Inches(3.0), Inches(0.5),
                 mime, size=Pt(11), color=GRAY, font=MONO_FONT)

    text_box(slide, Inches(7.0), Inches(1.8), Inches(5.8), Inches(0.4),
             "✓ Good", size=Pt(13), bold=True, color=GREEN)
    code_box(slide, Inches(7.0), Inches(2.2), Inches(5.8), Inches(2.2),
             'read_media_file(path="public/logo.png")\n\n→ {\n    "type": "image",\n    "data": "iVBORw0KGgo...",\n    "mimeType": "image/png"\n  }',
             fill=RGBColor(0x1A, 0x2A, 0x1A), text_color=GREEN)

    text_box(slide, Inches(7.0), Inches(4.6), Inches(5.8), Inches(0.4),
             "✗ Bad — text file wastes tokens", size=Pt(13), bold=True, color=YELLOW)
    code_box(slide, Inches(7.0), Inches(5.0), Inches(5.8), Inches(1.5),
             'read_media_file(path="audit_log.txt")\n# works but returns base64 of plain text\n# use read_text_file instead',
             fill=RGBColor(0x2A, 0x28, 0x1A), text_color=YELLOW)
```

- [ ] **Step 4: Implement `_slide_08_read_multiple_files`**

```python
def _slide_08_read_multiple_files(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "read_multiple_files",
                "Input: paths[] → Output: all contents in one string (partial failure OK)")

    code_box(slide, Inches(0.5), Inches(1.8), Inches(6.0), Inches(2.5),
             'read_multiple_files(paths=[\n  "sensitive/financials/payslips_q1.csv",\n  "does_not_exist.txt",\n  "projects/known_defects.csv"\n])',
             fill=GRAY)

    arrow(slide, Inches(6.7), Inches(3.0), Inches(7.3), Inches(3.0))

    code_box(slide, Inches(7.5), Inches(1.8), Inches(5.3), Inches(2.5),
             '=== payslips_q1.csv ===\nemployee_id,name,salary\n101,Alice,72000\n\n=== does_not_exist.txt ===\nError: ENOENT: no such file\n\n=== known_defects.csv ===\nid,title,severity\n1,Memory leak,high',
             fill=GRAY)

    label_box(slide, Inches(7.5), Inches(3.6), Inches(5.3), Inches(0.45),
              "Bad path → inline error, rest succeed", fill=YELLOW, text_color=BG, size=Pt(13))

    text_box(slide, Inches(0.5), Inches(4.6), Inches(12.3), Inches(1.4),
             "Key points:\n"
             "• Response is one string — you must parse it yourself to separate files\n"
             "• There is no atomicity — some succeed, some fail\n"
             "• Check for 'Error:' lines inline to detect partial failure",
             size=Pt(14), color=WHITE)
```

- [ ] **Step 5: Implement `_slide_09_write_tools`**

```python
def _slide_09_write_tools(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "Write Tools")

    # write_file
    label_box(slide, Inches(0.5), Inches(1.8), Inches(5.5), Inches(0.55),
              "write_file", fill=RED, text_color=WHITE)
    text_box(slide, Inches(0.5), Inches(2.5), Inches(5.5), Inches(0.4),
             "Creates or OVERWRITES a file — no confirmation", size=Pt(13), color=WHITE)
    code_box(slide, Inches(0.5), Inches(3.0), Inches(5.5), Inches(1.3),
             'write_file(\n  path="source_code/notes.txt",\n  content="Sprint 12 goals:\\n- Fix auth"\n)\n→ "Successfully wrote to notes.txt"',
             fill=GRAY)
    label_box(slide, Inches(0.5), Inches(4.5), Inches(5.5), Inches(0.4),
              "⚠ destructive=true  idempotent=true", fill=YELLOW, text_color=BG, size=Pt(12))

    # edit_file
    label_box(slide, Inches(7.0), Inches(1.8), Inches(5.8), Inches(0.55),
              "edit_file", fill=ACCENT, text_color=BG)
    text_box(slide, Inches(7.0), Inches(2.5), Inches(5.8), Inches(0.4),
             "Find-and-replace edits → returns git diff", size=Pt(13), color=WHITE)
    code_box(slide, Inches(7.0), Inches(3.0), Inches(5.8), Inches(2.5),
             'edit_file(\n  path="notes.txt",\n  edits=[{\n    "oldText": "Fix auth",\n    "newText": "Fix auth module"\n  }]\n)\n→ "@@ -1 +1 @@\\n-Fix auth\\n+Fix auth module"',
             fill=GRAY)
    label_box(slide, Inches(7.0), Inches(5.6), Inches(5.8), Inches(0.4),
              "⚠ destructive=true  idempotent=false", fill=YELLOW, text_color=BG, size=Pt(12))

    text_box(slide, Inches(0.5), Inches(6.3), Inches(12.3), Inches(0.45),
             "Tip: use dryRun=true to preview the diff before committing changes",
             size=Pt(13), color=YELLOW)
```

- [ ] **Step 6: Implement `_slide_10_list_tools`**

```python
def _slide_10_list_tools(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "Navigation — List & Tree Tools")

    cols = [
        ("list_directory", ACCENT,
         "sensitive/\n[DIR] contracts\n[DIR] financials\n[DIR] security"),
        ("list_directory_with_sizes", GREEN,
         "sensitive/financials/\n[FILE] payslips_q1.csv  74 B\n[FILE] budget_2026.xlsx  15 B"),
        ("directory_tree", YELLOW,
         '{\n  "name": "sensitive",\n  "type": "directory",\n  "children": [\n    {"name": "contracts",\n     "type": "directory", ...}\n  ]\n}'),
    ]
    for i, (name, color, output) in enumerate(cols):
        x = Inches(0.3 + i * 4.35)
        label_box(slide, x, Inches(1.8), Inches(4.0), Inches(0.5),
                  name, fill=color, text_color=BG, size=Pt(13))
        code_box(slide, x, Inches(2.4), Inches(4.0), Inches(3.8),
                 output, fill=GRAY)

    text_box(slide, Inches(0.5), Inches(6.4), Inches(12.3), Inches(0.45),
             "directory_tree output is JSON string — parse it. Use excludePatterns=[\"*.log\"] to skip noisy files.",
             size=Pt(13), color=YELLOW)
```

- [ ] **Step 7: Implement `_slide_11_search_files`**

```python
def _slide_11_search_files(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "search_files — Glob Pattern Cheatsheet")

    rows = [
        ("*",            "Current dir only",   "NO",  "README.md  (only if in root)"),
        ("**/*",         "All files recursive","YES", "sensitive/financials/payslips_q1.csv\nprojects/known_defects.csv\n..."),
        ("**/*.csv",     "CSV files only",     "YES", "sensitive/financials/payslips_q1.csv\nprojects/known_defects.csv"),
        ("sensitive/**","Inside sensitive/",   "YES", "sensitive/contracts/...\nsensitive/financials/..."),
    ]
    headers = ["Pattern", "Meaning", "Recursive?", "Example result"]
    col_x = [Inches(0.3), Inches(2.8), Inches(5.5), Inches(7.2)]
    col_w = [Inches(2.3), Inches(2.5), Inches(1.5), Inches(5.7)]

    for j, h in enumerate(headers):
        text_box(slide, col_x[j], Inches(1.8), col_w[j], Inches(0.45),
                 h, size=Pt(13), bold=True, color=ACCENT)

    for i, (pat, meaning, rec, example) in enumerate(rows):
        y = Inches(2.4 + i * 1.1)
        bg = RGBColor(0x1A, 0x1A, 0x3A) if i % 2 == 0 else GRAY
        for j, val in enumerate([pat, meaning, rec, example]):
            color = RED if (j == 0 and pat == "*") else (GREEN if rec == "YES" else YELLOW)
            code_box(slide, col_x[j], y, col_w[j], Inches(1.0),
                     val, fill=bg, text_color=color if j == 0 else WHITE)

    text_box(slide, Inches(0.3), Inches(6.8), Inches(12.5), Inches(0.45),
             "⚠  * is NOT recursive — the #1 beginner mistake. Always use **/* for recursive search.",
             size=Pt(14), bold=True, color=RED)
```

- [ ] **Step 8: Implement `_slide_12_info_admin`**

```python
def _slide_12_info_admin(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "Info & Admin Tools")

    tools = [
        ("get_file_info",
         "path → metadata\n(size, timestamps,\ntype, permissions)",
         "size: 134\nmodified: 2026-01-15\nisFile: true\npermissions: 644"),
        ("create_directory",
         "path → creates dir\n(and parents).\nSafe to retry.",
         'create_directory(\n  "source_code/feature/utils"\n)\n→ "Successfully created..."'),
        ("move_file",
         "source, destination\n→ moves or renames.\nFails if dest exists.",
         'move_file(\n  source="notes.txt",\n  destination="archive/notes.txt"\n)\n→ "Successfully moved..."'),
        ("list_allowed_directories",
         "No params → lists\nserver root dirs.\nCall this first.",
         '→ "Allowed directories:\n/corp_filesystem_sim"'),
    ]
    for i, (name, desc, example) in enumerate(tools):
        x = Inches(0.2 + i * 3.3)
        label_box(slide, x, Inches(1.8), Inches(3.0), Inches(0.5),
                  name, fill=ACCENT, text_color=BG, size=Pt(12))
        text_box(slide, x, Inches(2.4), Inches(3.0), Inches(1.3),
                 desc, size=Pt(12), color=WHITE)
        code_box(slide, x, Inches(3.8), Inches(3.0), Inches(2.5),
                 example, fill=GRAY)
```

- [ ] **Step 9: Implement `_slide_13_file_type_matrix`**

```python
def _slide_13_file_type_matrix(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "File Type × Tool Matrix")

    rows = [
        (".txt / .md / .csv", "✅", "⚠️ wasteful", "✅", "✅"),
        (".sql / .c / .sh",   "✅", "⚠️ wasteful", "✅", "✅"),
        (".pem",              "✅", "⚠️ wasteful", "✅", "✅"),
        (".png",              "❌",  "✅",          "❌",  "✅"),
        (".pdf",              "❌",  "✅",          "❌",  "✅"),
        (".docx / .xlsx",     "❌",  "✅",          "❌",  "✅"),
        (".exe / .sys",       "❌",  "✅ (opaque)",  "❌",  "✅"),
    ]
    cols = ["File type", "read_text_file", "read_media_file", "write_file", "search_files"]
    col_x = [Inches(0.2), Inches(2.8), Inches(5.1), Inches(8.2), Inches(10.5)]
    col_w = [Inches(2.4), Inches(2.1), Inches(2.9), Inches(2.1), Inches(2.5)]

    for j, h in enumerate(cols):
        label_box(slide, col_x[j], Inches(1.8), col_w[j], Inches(0.45),
                  h, fill=GRAY, text_color=ACCENT, size=Pt(12))

    for i, (ftype, *cells) in enumerate(rows):
        y = Inches(2.4 + i * 0.6)
        bg = RGBColor(0x25, 0x27, 0x38) if i % 2 == 0 else GRAY
        text_box(slide, col_x[0], y, col_w[0], Inches(0.55),
                 ftype, size=Pt(12), color=WHITE, font=MONO_FONT)
        for j, cell in enumerate(cells):
            color = GREEN if "✅" in cell else (RED if "❌" in cell else YELLOW)
            text_box(slide, col_x[j + 1], y, col_w[j + 1], Inches(0.55),
                     cell, size=Pt(13), color=color, align=PP_ALIGN.CENTER)

    text_box(slide, Inches(0.2), Inches(6.8), Inches(12.5), Inches(0.45),
             "✅ correct tool  ·  ⚠️ works but suboptimal  ·  ❌ wrong tool / fails",
             size=Pt(13), color=GRAY, align=PP_ALIGN.CENTER)
```

- [ ] **Step 10: Run tests**

```bash
uv run pytest tests/test_filesystem_deck.py -v
```

Expected: both PASS.

- [ ] **Step 11: Commit**

```bash
git add scripts/generate_filesystem_deck.py
git commit -m "feat: implement Act 2 slides (tools in action)"
```

---

## Task 5: Implement Act 3 — Edge Cases & Gotchas (slides 14–18)

**Files:**
- Modify: `scripts/generate_filesystem_deck.py` — replace stubs for slides 14–18

- [ ] **Step 1: Implement `_slide_14_glob_patterns`**

```python
def _slide_14_glob_patterns(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "Edge Case: Glob Patterns",
                "* is NOT recursive — the #1 beginner mistake")

    left_code = (
        'search_files(\n'
        '  path=".",\n'
        '  pattern="*.csv"\n'
        ')\n\n'
        '→ (empty — no CSVs\n'
        '   directly in root)'
    )
    right_code = (
        'search_files(\n'
        '  path=".",\n'
        '  pattern="**/*.csv"\n'
        ')\n\n'
        '→ sensitive/financials/payslips_q1.csv\n'
        '   projects/known_defects.csv'
    )

    label_box(slide, Inches(0.5), Inches(1.8), Inches(5.5), Inches(0.5),
              "✗  pattern='*.csv'  (WRONG)", fill=RED, text_color=WHITE)
    code_box(slide, Inches(0.5), Inches(2.4), Inches(5.5), Inches(3.5),
             left_code, fill=RGBColor(0x2A, 0x1A, 0x1A), text_color=RED)

    arrow(slide, Inches(6.2), Inches(4.0), Inches(7.0), Inches(4.0))

    label_box(slide, Inches(7.2), Inches(1.8), Inches(5.7), Inches(0.5),
              "✓  pattern='**/*.csv'  (CORRECT)", fill=GREEN, text_color=BG)
    code_box(slide, Inches(7.2), Inches(2.4), Inches(5.7), Inches(3.5),
             right_code, fill=RGBColor(0x1A, 0x2A, 0x1A), text_color=GREEN)

    text_box(slide, Inches(0.5), Inches(6.2), Inches(12.3), Inches(0.6),
             "Rule: * = current directory only · **/* = recursive · **/*.ext = recursive + filter by extension",
             size=Pt(14), color=YELLOW)
```

- [ ] **Step 2: Implement `_slide_15_path_pitfalls`**

```python
def _slide_15_path_pitfalls(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "Edge Case: Path Pitfalls")

    cases = [
        ('""  (empty string)',      "Error: Access denied",                       RED),
        ('"../etc/passwd"',         "Error: Path outside allowed directory",       RED),
        ('"C:/Windows/win.ini"',    "Error: Path outside allowed directory",       RED),
        ('"./sensitive/"  (./  and trailing /)', "Works — both stripped automatically", GREEN),
        ('"sensitive"  vs  "./sensitive"', "Both work — same resolved path",        GREEN),
    ]
    for i, (path, result, color) in enumerate(cases):
        y = Inches(1.8 + i * 0.95)
        code_box(slide, Inches(0.5), y, Inches(5.5), Inches(0.75),
                 f"path = {path}", fill=GRAY)
        arrow(slide, Inches(6.2), Inches(y + Inches(0.37)), Inches(7.0), Inches(y + Inches(0.37)))
        code_box(slide, Inches(7.2), y, Inches(5.7), Inches(0.75),
                 result,
                 fill=RGBColor(0x2A, 0x1A, 0x1A) if color == RED else RGBColor(0x1A, 0x2A, 0x1A),
                 text_color=color)
```

- [ ] **Step 3: Implement `_slide_16_silent_overwrite`**

```python
def _slide_16_silent_overwrite(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "Edge Case: write_file Silently Overwrites",
                "No warning. No backup. Old content is gone.")

    code_box(slide, Inches(0.5), Inches(1.9), Inches(5.5), Inches(1.8),
             "BEFORE\n\naudit_log.txt:\n2026-01-15 09:00 | LOGIN | eve | success\n2026-01-15 09:04 | READ  | audit_log | success\n... (500 lines)",
             fill=RGBColor(0x1A, 0x2A, 0x1A), text_color=GREEN)

    code_box(slide, Inches(0.5), Inches(4.0), Inches(5.5), Inches(1.5),
             'write_file(\n  path="sensitive/security/audit_log.txt",\n  content="log cleared"\n)\n→ "Successfully wrote to audit_log.txt"',
             fill=GRAY)

    arrow(slide, Inches(6.2), Inches(4.0), Inches(7.0), Inches(4.0))

    code_box(slide, Inches(7.2), Inches(1.9), Inches(5.7), Inches(1.8),
             "AFTER\n\naudit_log.txt:\nlog cleared\n\n\n(500 lines gone)",
             fill=RGBColor(0x2A, 0x1A, 0x1A), text_color=RED)

    label_box(slide, Inches(7.2), Inches(4.0), Inches(5.7), Inches(0.5),
              "No error. No diff. No confirmation.", fill=RED, text_color=WHITE)

    text_box(slide, Inches(0.5), Inches(6.2), Inches(12.3), Inches(0.55),
             "Safe pattern: call get_file_info first to check if the file exists before writing.",
             size=Pt(14), color=YELLOW)
```

- [ ] **Step 4: Implement `_slide_17_partial_batch`**

```python
def _slide_17_partial_batch(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "Edge Case: read_multiple_files Partial Failure",
                "One bad path does NOT abort the batch — error is inlined")

    code_box(slide, Inches(0.5), Inches(1.8), Inches(5.5), Inches(2.0),
             'read_multiple_files(paths=[\n  "sensitive/financials/payslips_q1.csv",\n  "does_not_exist.txt",\n  "projects/known_defects.csv"\n])',
             fill=GRAY)

    arrow(slide, Inches(6.2), Inches(2.7), Inches(7.0), Inches(2.7))

    code_box(slide, Inches(7.2), Inches(1.8), Inches(5.7), Inches(4.0),
             "=== payslips_q1.csv ===\nemployee_id,name,salary\n101,Alice,72000\n\n"
             "=== does_not_exist.txt ===\nError: ENOENT: no such file\n\n"
             "=== known_defects.csv ===\nid,title,severity\n1,Memory leak,high",
             fill=GRAY)

    label_box(slide, Inches(7.2), Inches(6.0), Inches(5.7), Inches(0.45),
              "Scan for 'Error:' lines to detect partial failure", fill=YELLOW, text_color=BG, size=Pt(13))

    text_box(slide, Inches(0.5), Inches(4.1), Inches(6.0), Inches(0.9),
             "• Response is one big string\n• Parse it yourself to split files\n• No atomicity — some succeed, some fail",
             size=Pt(14), color=WHITE)
```

- [ ] **Step 5: Implement `_slide_18_missing_tools`**

```python
def _slide_18_missing_tools(prs: Presentation):
    slide = add_slide(prs)
    slide_title(slide, "Tools That Don't Exist (By Design)",
                "Calling these returns error -32602. They are intentionally absent.")

    tools = [
        ("delete_file",    "Irreversible — agents cannot destroy data"),
        ("execute_shell",  "Arbitrary code execution is out of scope"),
        ("copy_file",      "Not needed — read_text_file + write_file achieves the same"),
        ("chmod / chown",  "Permission changes not exposed to agents"),
    ]
    for i, (name, reason) in enumerate(tools):
        y = Inches(2.0 + i * 1.1)
        label_box(slide, Inches(0.5), y, Inches(3.5), Inches(0.55),
                  name, fill=RED, text_color=WHITE, size=Pt(14))
        text_box(slide, Inches(4.2), y, Inches(8.7), Inches(0.55),
                 reason, size=Pt(14), color=WHITE)

    code_box(slide, Inches(0.5), Inches(6.0), Inches(12.0), Inches(0.7),
             'tools/call { "name": "delete_file", ... }  →  Error -32602: Tool not found: delete_file',
             fill=GRAY, text_color=RED)
```

- [ ] **Step 6: Run tests**

```bash
uv run pytest tests/test_filesystem_deck.py -v
```

Expected: both PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/generate_filesystem_deck.py
git commit -m "feat: implement Act 3 slides (edge cases and gotchas)"
```

---

## Task 6: Add title text tests, generate final PPTX, and commit

**Files:**
- Modify: `tests/test_filesystem_deck.py` — add title text assertions
- Modify: `scripts/generate_filesystem_deck.py` — run and save final output

- [ ] **Step 1: Add title-text tests to `tests/test_filesystem_deck.py`**

Add these functions after the existing tests:

```python
def _first_text(slide) -> str:
    """Return the text of the first text-containing shape on a slide."""
    for shape in slide.shapes:
        if shape.has_text_frame:
            t = shape.text_frame.text.strip()
            if t:
                return t
    return ""


def test_slide_titles():
    prs = generate_deck()
    slides = prs.slides
    assert "MCP Filesystem Server" in _first_text(slides[0])
    assert "What is MCP" in _first_text(slides[1])
    assert "Request" in _first_text(slides[2])
    assert "Security Boundary" in _first_text(slides[3])
    assert "Read Tools" in _first_text(slides[4])
    assert "read_text_file" in _first_text(slides[5])
    assert "read_media_file" in _first_text(slides[6])
    assert "read_multiple_files" in _first_text(slides[7])
    assert "Write Tools" in _first_text(slides[8])
    assert "Navigation" in _first_text(slides[9])
    assert "search_files" in _first_text(slides[10])
    assert "Info" in _first_text(slides[11])
    assert "Matrix" in _first_text(slides[12])
    assert "Glob" in _first_text(slides[13])
    assert "Path" in _first_text(slides[14])
    assert "Overwrite" in _first_text(slides[15])
    assert "Partial" in _first_text(slides[16])
    assert "Don't Exist" in _first_text(slides[17])
```

- [ ] **Step 2: Run all tests**

```bash
uv run pytest tests/test_filesystem_deck.py -v
```

Expected:
```
PASSED tests/test_filesystem_deck.py::test_deck_has_18_slides
PASSED tests/test_filesystem_deck.py::test_slide_backgrounds_are_dark
PASSED tests/test_filesystem_deck.py::test_slide_titles
```

- [ ] **Step 3: Generate the final PPTX**

```bash
uv run python scripts/generate_filesystem_deck.py
```

Expected: `Saved: .../presentations/mcp-filesystem-tools.pptx`

Open the file in PowerPoint or LibreOffice Impress and verify:
- 18 slides, dark background throughout
- Act 1 (slides 1–4): title card, protocol diagram, request/response, security boundary
- Act 2 (slides 5–13): all read/write/nav/matrix slides have colored boxes and code examples
- Act 3 (slides 14–18): edge case slides with red/green comparisons

- [ ] **Step 4: Run full test suite to check for regressions**

```bash
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit everything**

```bash
git add tests/test_filesystem_deck.py presentations/mcp-filesystem-tools.pptx
git commit -m "feat: finalize filesystem teaching deck — 18 slides, all tests pass"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task that covers it |
|-----------------|---------------------|
| `docs/mcp-tools/filesystem.md` with 14 tools, input/output tables, good/bad examples | Task 1 |
| File type behavior (txt/md/csv/sql/c/sh/pem/png/pdf/docx/xlsx/exe/sys) | Task 1 (per-tool sections + matrix) |
| Edge cases: glob patterns, path pitfalls, silent overwrite, partial batch, missing tools | Task 1 (Edge Cases section) + Task 5 (slides 14–18) |
| PPTX Act 1 — 4 protocol overview slides | Task 3 |
| PPTX Act 2 — 9 tools-in-action slides | Task 4 |
| PPTX Act 3 — 5 edge case slides | Task 5 |
| Tests: slide count, dark backgrounds, slide titles | Task 2 (count + bg) + Task 6 (titles) |
| Generated PPTX committed to `presentations/` | Task 6 |

**Placeholder scan:** No TBDs. All code blocks are complete. All paths are exact.

**Type consistency:** `generate_deck()` returns `Presentation`. All `_slide_NN_*` functions take `prs: Presentation`. Helper functions (`add_slide`, `text_box`, `code_box`, `label_box`, `arrow`, `slide_title`) are defined in Task 2 scaffold and reused consistently in Tasks 3–5.
