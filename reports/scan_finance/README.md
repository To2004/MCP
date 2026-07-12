# Finance MCP scans

Static risk scans of the free finance MCP servers vendored under `external/`,
built **from live traffic** — each server is run for real, driven through the
project's man-in-the-middle proxy, and its own advertised `tools/list` is what
the scanner consumes (never a hand-authored catalog).

## Method (matches the other benchmarks)

```
client → mitmdump:9090 (reverse) → finance FastMCP server:8080
                     │
                     └── mitm_capture.py addon → captured.jsonl
```

1. **Connect + capture** — `logs/proxy/scripts/run_mitm_finance.py` launches each
   no-credential server over Streamable HTTP (via
   `logs/proxy/servers/finance_http_launcher.py`, inside the server's own uv
   env), fronts it with `mitmdump`, and drives one MCP session:
   `initialize` → `tools/list` → benign + attack-shaped calls
   (VALID / BAD_TOOL / BAD_PARAMS / EDGE). Every HTTP flow lands in
   `logs/proxy/sessions/<session>/captured.jsonl`.
2. **Inventory** — `scripts/save_finance_tool_lists.py` extracts the `tools/list`
   response from the capture into `tool_lists/<kind>.json`.
3. **Static scan** — `scripts/scan_finance.py` runs the deterministic
   static-analysis layer (atomic-op taxonomy + input-risk rules,
   `mcp_security.scanner.atomic_flags`) over each tool list. No LLM, no GPU.
   Output: `<kind>.json` (full detail) + `<kind>.md` (operator summary).

## Server coverage (no-credential = connectable right now)

| Server | Key needed to connect? | Captured live | Notes |
| --- | --- | --- | --- |
| **yahoo_finance** | none | ✅ yes | Pure `yfinance` reads; 9 tools, all READ/METADATA (Low). |
| **finance_tools** | none (FRED optional) | ✅ yes | 17 tools (yfinance + CNN Fear&Greed + FRED macro + `calculate`). Source is PyPI-only, so it is installed into a dedicated venv (`.fin-venvs/finance-tools`, `pyrate-limiter==2.10.0` + `requests-ratelimiter==0.4.2` pins) and launched via its `create_mcp_application()` factory (`FIN_FACTORY=1`). 16 Low / 1 Medium. |
| **maverick** | Tiingo key for *data* only | ✅ yes | **119 tools** — the only finance server with real state-changing ops. Standalone fastmcp 3.x; editable-installed into `.fin-venvs/maverick` (heavy native deps: TA-Lib, vectorbt). `tools/list` + registration need no key. **10 Critical** (DELETE/EXECUTE: `run_backtest`, `portfolio_clear_portfolio`, `data_clear_cache`, `delete_signal`, …), 15 Medium, 94 Low. |
| ccxt | none for public tools | ❌ blocked | Node/TypeScript server — `node`/`npm` not installed on this host. |
| alpaca | ALPACA_API_KEY + secret | ❌ needs key | — |
| Financial-Modeling-Prep | FMP_ACCESS_TOKEN | ❌ needs key | — |

Each server is driven by several independent MCP client sessions ("parties") —
a benign analyst, a power/quant user, and an adversary (BAD_TOOL / BAD_PARAMS /
EDGE injection-shaped calls) — so the capture also carries multi-caller runtime
traffic, not just the tool inventory.

## Simulations (for the dynamic layer)

`scripts/make_finance_simulations.py` turns each scanned catalog into a corpus of
benign-vs-attacker call sessions (`logs/proxy/sessions/<kind>_sim/calls.csv`, the
same shape `make_simulations.py` produces). It is **grounded in the scan**: benign
runs sample the low-severity READ tools; ~1/3 attacker runs target the
highest-severity tools the scanner found and inject free-form / path-traversal /
oversized-magnitude / escalating-flag values into exactly the parameters flagged
in each tool's `input_ranking`, plus a non-existent-tool call and a
missing-required-args call. 624 calls across the 5 servers (seeded, reproducible).

```bash
uv run python scripts/make_finance_simulations.py
uv run python -m mcp_security.dynamic --session logs/proxy/sessions/sec_edgar_sim/calls.csv \
    --server sec_edgar --scan-dir reports/scan_finance
```

Note: the dynamic **static-fusion** stage reads `static=invalid` on these because
the finance scans use the deterministic-only schema (`scan_finance.py`), not the
rich LLM cells/bands artifact the fusion consumes. The sessions still flow through
the baseline + sequence stages; full fused scoring requires running these servers
through the LLM scanner (`mcp_security.scanner` + `param_scoring`) to emit the
cells/bands matrices.

## Reproduce

```bash
# finance_tools needs its venv once (Python 3.12; old ratelimiter API):
uv venv --python 3.12 .fin-venvs/finance-tools
uv pip install --python .fin-venvs/finance-tools/bin/python \
    finance-tools-mcp "pyrate-limiter==2.10.0" "requests-ratelimiter==0.4.2"

uv run python logs/proxy/scripts/run_mitm_finance.py            # all no-key servers
uv run python logs/proxy/scripts/run_mitm_finance.py --only yahoo_finance
uv run python scripts/save_finance_tool_lists.py
uv run python scripts/scan_finance.py
```

maverick likewise installs once into its own venv (native deps take a few min):

```bash
uv venv --python 3.12 .fin-venvs/maverick
uv pip install --python .fin-venvs/maverick/bin/python -e external/maverick-mcp
```

## Transport note

The capture proxy records discrete request/response flows, so servers are run
over **Streamable HTTP**, not SSE — a long-lived SSE `GET /sse` stream never
"completes", so the buffering proxy captures nothing from it. yahoo pins only
`mcp>=1.6` (sse-only), so the runner overlays a newer `mcp` (`--with`) to get
streamable-http without editing the vendored source.
