# scanner

Static, **pre-runtime** MCP scanner. It understands a server's tools and assets
*before the server runs* and **never connects to a live MCP**. It derives every
risk primitive with the local LLM (strict, LLM-only) — nothing is hardcoded and
no design-time table is read.

## Why static

A gateway needs the risk picture *before* it lets an agent talk to a server, and
a live connection is neither always available nor safe to make at design time. So
the scanner reads the server description from committed, static sources:

- **tools** — from the Excel tool catalog `docs/mcp-tools/xlsx/<kind>_tools.xlsx`
  (`tool_catalog.py`). Only the inventory is used (name, description, annotation
  hints, params); the catalog's hand-authored `risk_tier` columns are *evaluation
  ground truth*, never an input.
- **assets** — from the on-disk store the server fronts: a filesystem tree
  (`os.walk`), a sqlite schema (read-only), or the seeded slack channels.

## Pipeline

```
Excel tool catalog ─┐
on-disk asset store ─┴─► ServerRegistry ─► StaticScorer(strict, LLM-only) ─► scan artifact
                          (scan.py)          (static_scoring.pipeline)        reports/scan/<server>.json
```

The understanding stage is `mcp_security.static_scoring.pipeline.StaticScorer` in
**strict mode**: each primitive (domain, tool impact, asset sensitivity, blast
radius) is decided by the model via the `prompts.txt` suite, and if the model is
unreachable the scan raises `LLMUnavailableError` instead of falling back to a
heuristic or a checked-in number.

## Files

| File | Responsibility |
|------|----------------|
| `tool_catalog.py` | Load the tool inventory from the Excel catalog → `ToolSpec` list |
| `scan.py` | Assemble the registry (Excel tools + disk assets), run the LLM understanding, write the scan artifact |
| `asset_gen.py` | Generate an affected asset per tool from name+description alone (own prompt, never part of the normal scan prompts) |
| `render.py` | Render a scan artifact as markdown |
| `__main__.py` | CLI |

## Usage

```bash
# Real scan (needs Ollama/Qwen — run on a GPU node)
python -m mcp_security.scanner --kind filesystem --root demo/corp_filesystem \
    --server fs:corp_filesystem --out reports/scan/fs_corp_filesystem.md
python -m mcp_security.scanner --kind sqlite --root demo/cbg_sqlite/cbg.db

# Whole pipeline (scan every demo server, rank calls, grade vs ground truth)
sbatch scripts/scan_and_rank_on_gpu.sbatch

# Offline smoke check only (deterministic baseline, NOT a real scan)
python -m mcp_security.scanner --kind filesystem --no-llm

# Home every tool on an asset, generating generic ones where the registry
# has none (channels_list -> channel-directory). Separate prompt from the
# normal scan prompts; the model sees ONLY the tool name + description, no
# org context, and pure utility tools (clock, colors) generate nothing.
python -m mcp_security.scanner --kind slack --gen-assets

# Check the generator against the held-out curated tool->asset list
python -m mcp_security.scanner.asset_gen --eval            # LLM (GPU node)
python -m mcp_security.scanner.asset_gen --eval --no-llm   # heuristic smoke
```

The scan artifact (`reports/scan/<server>.json`) has the same shape as a static
table — tool impact, asset sensitivity, per-pair blast radius, the `cells` matrix
and its `bands`. The call ranker (`mcp_security.call_scoring`) scores observed
calls against it.

## Notes

- **No live MCP.** There is no protocol connection, no port, no running server.
- **LLM-only.** A real scan needs the model; `--no-llm` is a deterministic smoke
  path for tests, never shipped as a scan.
- **Graded, not fed, by the tables.** The committed design-time tables become
  evaluation ground truth (`reports/evaluation/`); `scripts/evaluate_scanner.py`
  scores the scanner against them. The scanner never reads them.
