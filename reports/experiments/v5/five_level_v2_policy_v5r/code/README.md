# The code that produced this run

Every module the v5r scan path executes, copied here as it was when the run
started, with a `.md` beside each one explaining what it does. `manifest.json`
records a sha256 per file, so a result in the parent folder can be tied to the
exact source that produced it.

This is a **snapshot, not the live source** — the repo moves, the run does not.
The originals live at the same relative paths under the repo root.

Regenerate with `uv run python scripts/snapshot_v5r_code.py`.

## The path, in execution order

| # | File | What it does | Lines |
|---|---|---|--:|
| 1 | [`scripts/scan_v5.sbatch`](scripts/scan_v5.sbatch.md) | SLURM wrapper — reserves a GPU, starts the local model, calls the driver | 81 |
| 2 | [`scripts/scan_policy_v5.py`](scripts/scan_policy_v5.py.md) | the driver — builds a registry from two documents, writes the artifacts | 247 |
| 3 | [`scanner/tool_list.py`](src/mcp_security/scanner/tool_list.py.md) | loads the captured `tools/list` catalog into `ToolSpec` objects | 71 |
| 4 | [`static_scoring/server_profiles.py`](src/mcp_security/static_scoring/server_profiles.py.md) | splits the policy document into per-server sections | 395 |
| 5 | [`static_scoring/server_policies.py`](src/mcp_security/static_scoring/server_policies.py.md) | parses the asset register; refuses a policy that leaked numbers | 211 |
| 6 | [`static_scoring/registry.py`](src/mcp_security/static_scoring/registry.py.md) | the data model — `ToolSpec`, `AssetSpec`, `ServerRegistry` | 834 |
| 7 | [`static_scoring/static_impact.py`](src/mcp_security/static_scoring/static_impact.py.md) | **the deterministic tool-impact rules** (stage 1) | 1333 |
| 8 | [`static_scoring/prompts.py`](src/mcp_security/static_scoring/prompts.py.md) | every prompt template the scan sends | 1243 |
| 9 | [`llm/ollama_client.py`](src/mcp_security/llm/ollama_client.py.md) | the model transport — one request per scoring decision | 112 |
| 10 | [`static_scoring/pipeline.py`](src/mcp_security/static_scoring/pipeline.py.md) | **orchestration, the four stages, the deterministic assembly** | 1633 |
| 11 | [`static_scoring/fallback.py`](src/mcp_security/static_scoring/fallback.py.md) | offline heuristics — never reached in a strict scan | 256 |
| 12 | [`scanner/atomic_flags.py`](src/mcp_security/scanner/atomic_flags.py.md) | post-scan enrichment — atomic ops, input ranking | 402 |
| 13 | [`scanner/render.py`](src/mcp_security/scanner/render.py.md) | renders the artifact as markdown and the matrix CSV | 292 |

7 110 lines total. The two that carry the scoring decisions are **7** (rules) and
**10** (stages + assembly); the rest is loading, prompting, transport and output.

## How a scan flows through them

```
scan_v5.sbatch
  └─ scan_policy_v5.py                     one target at a time
       ├─ tool_list.py                      catalog  -> [ToolSpec]
       ├─ server_profiles.py                policy doc -> this server's section
       ├─ server_policies.py                section  -> [PolicyAssetRow]
       ├─ registry.py                        both     -> ServerRegistry
       └─ pipeline.build_static_table()
            ├─ stage 0  domain inference     prompts.py + ollama_client.py
            ├─ stage 1  tool impact          static_impact.py, model only on abstention
            ├─ stage 2  asset sensitivity    prompts.py + ollama_client.py
            ├─ stage 3  blast radius         prompts.py + ollama_client.py
            ├─ assembly bulk / alias / floors
            └─ cells, bands, band_distribution
       ├─ atomic_flags.enrich_scan()
       └─ render.py                          -> <stem>.md, <stem>_matrix.csv
```

`fallback.py` sits behind every model call but is unreachable here: the driver
passes `strict=True`, so a model failure raises `LLMUnavailableError` instead of
substituting a heuristic.

## What is NOT in this folder

The two **inputs** (the tool catalogs and the policy sections) are in
`../inputs/` when exported, and the policy document itself is
`docs/mcp-tools/server-policies.md`. The prompts **as sent** are rendered in
`../scoring-prompts-AS-RUN.md`. The rules are explained for review in
`../../STATIC_RULES.md`, and what is standards-grounded versus ours is audited in
`../../GROUNDING.md`.
