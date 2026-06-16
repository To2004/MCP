# scanner

MCP asset scanner — enumerate the assets each connected MCP server can reach and
rank them into a `Rank | Name | Risk Level | Reasoning` table.

An MCP server is connected to an *asset store* whose unit depends on the server
kind (files for filesystem, tables for sqlite, channels for slack, resources for
anything else). The scanner connects to each configured server, enumerates the
assets it can reach **read-only**, and ranks them with the shared sensitivity
anchors plus the local LLM (Qwen2.5 via Ollama).

## Pipeline

```
config_reader → enumerate (generic, per kind) → rank → table
                      │
   local store ───────┤ filesystem: os.walk · sqlite: read-only sqlite3
   any MCP server ────┤ generic: list_resources + read-only enumeration tools
   unreachable ───────┘ resolver: web/GitHub lookup → LLM, else theorise
```

Enumeration is **generic by default**: every server is scanned via the MCP
protocol itself (`list_resources` + read-only tools), so an unknown kind still
works with no per-kind code. `filesystem` and `sqlite` add local fast-paths.

**Find through the server's own tools.** A *configured* fs/sqlite server (one
with a launch command) is enumerated by driving its read-only MCP tools —
sqlite via `list_tables` + `describe_table`, filesystem via `directory_tree` /
`list_directory` — all behind the read-only gate. A raw `--root` path (no
server) is still read directly from disk. This per-kind procedure is necessary
because *how* to enumerate (which tool, what argument, how to recurse) differs
per server kind.

**Discovery is deterministic; understanding is the agent.** Finding *where* the
assets are is plain code. Understanding *what* each asset is and how sensitive it
is, is done by a local-LLM ranking agent that reads the server's own
self-description (its tool/resource descriptions, captured as `AssetInventory.context`)
— so a server kind that was never pre-coded is still understood, not guessed.

## Files

| File | Responsibility |
|------|----------------|
| `config_reader.py` | Read connected servers + asset roots from `~/.claude.json` (secrets redacted to key names) |
| `enumerator.py` (filesystem) | Walk roots: emit **directories** (ranked by most sensitive file in their subtree) + files (by type, or per-file with `--by-file`) |
| `introspect.py` | Live, passive MCP connect (stdio/SSE) with timeouts |
| `safety.py` | Read-only gate: only LIST/SEARCH/METADATA tools may be invoked |
| `enumerator.py` | Per-kind + generic asset enumeration → `AssetInventory` |
| `resolver.py` | Web/theorise asset discovery for unreachable servers |
| `ranker.py` | Understanding agent (local LLM, kind-agnostic, reads server context) → ranked table; anchors are hints + offline fallback |
| `__main__.py` | CLI |

## Usage

```bash
# Scan a local store directly (no config needed)
python -m mcp_security.scanner --root demo/corp_filesystem
python -m mcp_security.scanner --root demo/corp_sqlite/corp.db --kind sqlite

# Scan every server configured in ~/.claude.json
python -m mcp_security.scanner

# Flags
--server NAME   only this configured server
--out FILE      also write the markdown report
--no-llm        anchored ranking only (offline)
--no-web        skip the web/theorise fallback
--by-file       (filesystem) list files, not types
```

## Notes

- **Read-only.** Enumeration never invokes write/delete tools; local stores use
  `os.walk` / immutable sqlite connections.
- **Local LLM only.** All model calls go to Ollama (`OLLAMA_HOST`, Qwen2.5:32b)
  via `mcp_security.llm.ollama_client`. No cloud. If Ollama is down, anchored rows
  still print and unanchored ones are flagged `unranked`.
- **No per-kind code is required for a new server.** Enumeration and
  understanding are both generic: an unknown kind is enumerated via the protocol
  and ranked by the agent from the server's context. Adding a marker in
  `config_reader._KIND_MARKERS` + an anchor in `mcp_security.sensitivity` is now
  *optional* — it only adds a deterministic fast-path/hint for a known kind.
