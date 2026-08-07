# `registry.py` — the data model

**834 lines, of which v5r uses about 120.** Three dataclasses plus a large set of
loaders for demo servers that this arm does not use.

## What v5r uses

| Class | Role |
|---|---|
| `ToolSpec` | one tool: `name`, `description`, the four MCP annotation hints, and `input_schema`. `parameters()` flattens the schema; `to_prompt_json()` is the shape every per-tool prompt receives. |
| `AssetSpec` | one asset: `asset_id`, `description`, and free-form `tags`. v5r fills the tags with `flag:<name>` and `tool:<name>` from the policy register. |
| `ServerRegistry` | the whole input: `server`, `kind`, `tools`, `assets`, `apps`, and `description` (here, the policy section verbatim). |

`tools_json_compact()` drops the input schemas — it is what the domain-inference
stage receives, because recognising a domain does not need every parameter and the
full `tools_json()` would overflow the context on a large server.

**`open_world_hint` is parsed but never read by v5r.** It stays on `ToolSpec` so
the dynamic scorer can consume it, which is where boundary-crossing belongs: the
hint describes a possibility only a specific request realises.

## What v5r does NOT use

`load_github_registry()`, `load_slack_registry()`, `load_calendar_registry()`,
the filesystem and sqlite loaders — these build registries from the project's demo
data (a captured `tools_catalog.csv`, a live `cbg.db` schema, a demo file tree).
v5r builds its registry from the captured vendor catalog plus the policy register
instead, which is the point of the arm: nothing comes from walking a store.

The declarative loaders are still reachable from `scripts/check_policies.py`,
which needs a `cbg` server's advertised tool list to validate its register.
