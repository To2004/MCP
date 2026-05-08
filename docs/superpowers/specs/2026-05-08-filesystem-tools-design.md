---
title: MCP Filesystem Tools — Reference Docs + Teaching Deck
date: 2026-05-08
status: approved
---

# MCP Filesystem Tools — Reference Docs + Teaching Deck

## Goal

Produce two artifacts explaining how each MCP filesystem tool works, targeting **students** who will work on this codebase:

1. `docs/mcp-tools/filesystem.md` — complete tool reference (the thing students look up)
2. `presentations/mcp-filesystem-tools.pptx` — teaching deck (the thing you teach from)

## Audience

Students new to MCP. Assume Python familiarity but no prior JSON-RPC or MCP protocol knowledge.

## Source Material

- MCP server: `@modelcontextprotocol/server-filesystem` v1.27.0
- Demo filesystem: `demo/corp_filesystem/` (14 file types across 4 sensitivity tiers)
- Real call examples: `logs/proxy/sessions/filesystem_sim/`
- Protocol: JSON-RPC 2.0, transport HTTP+SSE via mcp-proxy

---

## Artifact 1: `docs/mcp-tools/filesystem.md`

### Structure

```
# MCP Filesystem Server — Tool Reference

## Overview
  - What the filesystem MCP server is (1 paragraph)
  - The security boundary: allowed root, path traversal blocking
  - Tool categories table (read / write / navigate / info)

## Read Tools
  ### read_text_file
  ### read_media_file
  ### read_multiple_files

## Write Tools
  ### write_file
  ### edit_file

## Navigation Tools
  ### list_directory
  ### list_directory_with_sizes
  ### directory_tree
  ### search_files

## Info & Admin Tools
  ### get_file_info
  ### create_directory
  ### move_file
  ### list_allowed_directories

## Edge Cases & Gotchas
  - Glob patterns (* vs **/* vs *.csv)
  - Path: absolute vs relative, trailing slash, empty string
  - write_file silently overwrites — no confirmation
  - read_multiple_files: partial failure doesn't stop the batch
  - Tools that don't exist (delete_file, execute_shell, copy_file)

## File Type Behavior Matrix
  - Table: file type × tool → what you get
```

### Per-Tool Template

Every tool section uses this exact structure:

| Field | Content |
|-------|---------|
| **What it does** | 1-sentence plain-English description |
| **Input** | Parameter table: name / type / required / description |
| **Output** | Format and encoding of the response |
| **File types** | Which types work well, which behave oddly |
| **Good example** | Real call + response from corp_filesystem demo |
| **Bad example** | Call that fails or gives unexpected result + explanation |
| **Edge cases** | Callout box for that tool's specific gotchas |

### File Types Covered

| Extension | Category | Notes |
|-----------|----------|-------|
| `.txt` | Plain text | Always works with read_text_file |
| `.md` | Markdown | Same as .txt — returned as raw string |
| `.csv` | Delimited text | Same as .txt — agent must parse |
| `.sql` | Code/text | Same as .txt |
| `.c` / code files | Source code | Same as .txt |
| `.sh` / bash | Script | Same as .txt |
| `.png` | Binary image | Use read_media_file → base64 blob |
| `.pdf` | Binary document | Use read_media_file → base64 blob |
| `.docx` | Binary Office | Use read_media_file → base64 blob |
| `.xlsx` | Binary Office | Use read_media_file → base64 blob |
| `.exe` | Binary executable | Use read_media_file → base64 blob (opaque) |
| `.sys` | System binary | Use read_media_file → base64 blob (opaque) |
| `.pem` | Text cert/key | Works with read_text_file |

### Edge Cases to Cover

1. **Glob `*`** — matches files in specified dir only, NOT recursive
2. **Glob `**/*`** — recursive, matches everything
3. **Glob `**/*.csv`** — recursive, filter by extension
4. **Empty path** — returns "Access denied" or validation error
5. **`../` traversal** — blocked: "outside allowed directory"
6. **Absolute path outside root** — blocked: same error
7. **write_file on existing file** — silently overwrites, no warning
8. **read_multiple_files with one bad path** — partial result returned, bad path logged as error inline
9. **Missing required param** — `-32602` validation error
10. **Calling delete_file / execute_shell / copy_file** — `-32602` tool-not-found error; explain WHY (security design)

---

## Artifact 2: `presentations/mcp-filesystem-tools.pptx`

### Approach

Teaching deck: heavier on visuals and diagrams, lighter on text. Not a mirror of the docs — it's what you present from. Uses python-pptx to generate programmatically.

### Slide Plan (~18 slides)

#### Act 1 — What Is MCP Filesystem? (4 slides)

| # | Slide | Visual |
|---|-------|--------|
| 1 | Title: "MCP Filesystem Server — How It Works" | Logo / title card |
| 2 | What is MCP? | Protocol diagram: Agent → JSON-RPC → MCP Server → Filesystem |
| 3 | Request→Response flow | Annotated boxes: request (method, params) → server → response (content / error) |
| 4 | The security boundary | Diagram: allowed root box, red ✗ on `../` traversal, red ✗ on absolute outside root |

#### Act 2 — Tools in Action (9 slides)

| # | Slide | Visual |
|---|-------|--------|
| 5 | Read Tools overview | read_text_file / read_media_file / read_multiple_files — icon + 1-liner each |
| 6 | read_text_file | Flow: path → text block; file type icons that work (.txt .csv .md .sql .c .sh .pem) |
| 7 | read_media_file | Flow: path → base64 blob; file type icons (.png .pdf .docx .xlsx .exe .sys) |
| 8 | read_multiple_files | Flow: [path array] → multiple responses; partial-fail highlight |
| 9 | Write Tools | write_file + edit_file; destructive badge; diff output example for edit_file |
| 10 | Navigation: list tools | list_directory vs list_directory_with_sizes vs directory_tree — side-by-side output |
| 11 | search_files | Glob cheatsheet visual: `*` / `**/*` / `**/*.csv` with example results |
| 12 | Info & Admin | get_file_info / create_directory / move_file — quick visual each |
| 13 | File type matrix | Grid: rows = file type, columns = tool, cells = ✅ / ⚠️ / ❌ |

#### Act 3 — Edge Cases & Gotchas (5 slides)

| # | Slide | Visual |
|---|-------|--------|
| 14 | Glob patterns | `*` vs `**/*` result comparison side by side |
| 15 | Path pitfalls | Empty string / `../` / absolute outside root → all with error outputs |
| 16 | Silent overwrite | write_file before/after — file content replaced, no warning |
| 17 | Partial batch failure | read_multiple_files: one bad path inline error, rest succeed |
| 18 | Tools that don't exist | delete_file / execute_shell / copy_file → -32602; explain security design choice |

### Generation Method

Use **python-pptx** to generate the PPTX programmatically from a Python script.

- Script: `scripts/generate_filesystem_deck.py`
- Output: `presentations/mcp-filesystem-tools.pptx`
- Diagrams: drawn with python-pptx shapes (rectangles, arrows, connectors) — no external image dependencies
- Consistent theme: dark background, monospace font for code blocks, color-coded boxes (green = good, red = bad/error, yellow = warning)

---

## File Outputs

| File | Purpose |
|------|---------|
| `docs/mcp-tools/filesystem.md` | Student reference doc |
| `scripts/generate_filesystem_deck.py` | PPTX generator script |
| `presentations/mcp-filesystem-tools.pptx` | Generated teaching deck |

## Out of Scope

- Other MCP servers (calendar, SQLite) — separate docs if needed later
- Animated slides or embedded video
- Interactive notebooks (too much student setup friction)
