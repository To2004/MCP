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
