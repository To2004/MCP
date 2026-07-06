# Finance MCP scans — offline baseline

Static scans of five **free, key-free-to-enumerate** finance MCP servers, produced
with the project scanner. Each server's own advertised `tools/list` was captured
live over stdio, then scanned tool-by-asset against the `demo/fintech_fs` asset
store.

## Important: this is the deterministic baseline, not the LLM scan

This machine has no `qwen2.5:32b` / Ollama, so scans were run with `--no-llm`
(`provenance=offline-baseline`, `model_reviewed=False`). The deterministic baseline
ranks tool impact and blast-radius bands by heuristic. For thesis-grade numbers,
re-run the same tool lists on the GPU node with the LLM
(`sbatch scripts/scan_and_rank_multigpu.sbatch`) — the captured tool lists in
`tool_lists/` are the exact input it needs.

## Servers scanned

| Server | Tools | Assets | Cells | 🟢 low | 🟡 med | 🟠 high | 🔴 crit | Key needed? |
|--------|------:|-------:|------:|------:|------:|-------:|-------:|-------------|
| maverick | 119 | 6 | 6 | 291 | 339 | 84 | 0 | none |
| alpaca | 69 | 6 | 6 | 138 | 189 | 87 | 0 | dummy (enumerates without live key) |
| ccxt | 24 | 6 | 6 | 57 | 72 | 15 | 0 | none for data |
| finance_tools | 17 | 6 | 6 | 48 | 51 | 3 | 0 | none |
| yahoo_finance | 9 | 6 | 6 | 27 | 27 | 0 | 0 | none |

(low/med/high/crit are per-cell band counts across the tool×asset matrix.)

## What's inside

- `tool_lists/<server>.json` — the exact `tools/list` captured from each server
  (name, description, self-declared annotations, full input schema). This is the
  scanner's canonical input.
- `<server>.json` — the scan artifact (tool impact, asset sensitivity, blast
  radius, per-cell bands, band distribution, provenance).
- `<server>.md` — human-readable view of the same scan.

## Reproduce

```bash
# 1. capture a server's tools/list over stdio
python scripts/capture_external_tool_list.py --kind <name> --cwd external/<repo> -- <launch cmd>
# 2. scan it (offline baseline)
python -m mcp_security.scanner --kind filesystem --tool-list reports/tool_lists/<name>.json \
    --root demo/fintech_fs --server <name> --no-llm --scan-dir reports/scan_finance
```

## Highest-impact tools found (baseline)

- **alpaca** `place_stock_order` (impact 3) — real order placement; the flagship
  high-severity write action.
- **ccxt / maverick** — trade/execution and portfolio tools cluster in the 🟠 high band.
- **yahoo_finance** — entirely read-only; no cell exceeds 🟡 medium, the intended
  low-severity contrast case.
