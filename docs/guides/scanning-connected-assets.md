# Scanning Connected MCP Assets

The asset scanner answers one question: *what data can each connected MCP server
reach, and how sensitive is it?* It enumerates the assets a server exposes and
ranks them into a `Rank | Name | Risk Level | Reasoning` table.

This fits the project's threat model — the MCP server is the protected asset, the
agent is the threat — by making the server's reachable data, and its sensitivity,
explicit.

## What counts as an asset

The asset unit depends on the server kind:

| Server kind | Assets | Anchor |
|-------------|--------|--------|
| filesystem  | file-types (`.sql`, `.pem`, …) | `FILETYPE_SENSITIVITY` |
| sqlite      | tables (+ PII column tags) | `DB_COLUMN_ANCHOR` |
| slack       | channels / DMs | `SLACK_CHANNEL_ANCHOR` |
| any other   | `list_resources` + read-only tool output | generic filetype fallback, else LLM |

Enumeration is generic: unknown server kinds are still scanned through the MCP
protocol (`list_resources` plus read-only enumeration tools), with no per-kind
code required.

## Running it

```bash
# A local store directly — no config lookup
uv run python -m mcp_security.scanner --root demo/corp_filesystem
uv run python -m mcp_security.scanner --root demo/corp_sqlite/corp.db --kind sqlite

# Every server configured in ~/.claude.json (global + all projects)
uv run python -m mcp_security.scanner

# Offline / deterministic — anchored ranking only
uv run python -m mcp_security.scanner --root demo/corp_filesystem --no-llm --no-web
```

| Flag | Effect |
|------|--------|
| `--root PATH` | scan a local path directly |
| `--kind KIND` | asset kind for `--root` (default `filesystem`) |
| `--server NAME` | only the configured server with this name |
| `--out FILE` | also write the markdown report |
| `--no-llm` | anchored rows only; unanchored flagged `unranked` |
| `--no-web` | skip the GitHub/npm fallback for unreachable servers |
| `--by-file` | (filesystem) list files instead of types |

## Ranking

1. **Anchor** — the security team's fixed sensitivity (shared in
   `mcp_security.sensitivity`) resolves known rows deterministically. These are
   never silently downgraded.
2. **Local LLM** — every remaining asset is ranked and explained by Qwen2.5:32b
   via Ollama. The LLM may *raise* an anchored row but not lower it.

## Safety

- **Read-only.** Local stores use `os.walk` / immutable sqlite connections; live
  servers are only ever asked to run tools classified `LIST`/`SEARCH`/`METADATA`.
  Write/delete/unclassified tools are never invoked.
- **Secrets.** Only env-var *key names* are read from config — never values.
- **Local LLM only.** No cloud model is used. If Ollama is unreachable the scan
  still completes with anchored ranking.
- **Spawning stdio servers.** Live introspection of a stdio server starts its
  process to call `initialize`/`list_*`. Configs are user-authored and trusted;
  the scan stays passive (no mutating calls) and bounds each connect with a
  timeout.

## Extending

Add a server kind by:

1. a marker in `scanner/config_reader.py` `_KIND_MARKERS`,
2. (optional) an anchor dict in `mcp_security/sensitivity.py`,
3. (optional) an `ANCHOR_RESOLVERS` entry in `scanner/ranker.py`.

Enumeration already works generically, so a new kind is scannable even before any
anchor is added.
