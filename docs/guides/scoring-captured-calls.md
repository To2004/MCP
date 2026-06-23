# Scoring Captured Tool Calls

The call-scoring module applies the design-time static risk tables to *real
captured calls* — the normal/benign and misconfiguration traffic recorded under
`logs/proxy/` — so every call gets a risk score and band by lookup, with no LLM
at scoring time. Ranking normal traffic surfaces the inherently risky and
misconfigured calls a server should gate, even when nothing malicious is
happening.

## Running it

```bash
uv run python -m mcp_security.call_scoring            # writes reports/ranked_calls.csv
uv run python -m mcp_security.call_scoring -v         # with info logging
uv run python -m mcp_security.call_scoring --output /tmp/ranked.csv
```

The command prints a band/server summary and the ten riskiest calls, then writes
the full ranked corpus to `reports/ranked_calls.csv` (highest risk first).

## How a call is scored

Each captured session is scored against its server's static table
(`reports/samples/all_static_tables.json`). For one call:

1. **Unknown tool** — the tool is absent from the table's registry (a typo or a
   non-existent tool, e.g. `drop_table`). Unscorable; flagged `invalid`, which
   is itself a misconfiguration signal.
2. **Resolved asset** — the argument names an asset the table knows (a file
   extension, a SQL table, a channel). Scored directly from the precomputed
   `cells` matrix: `asset_sensitivity x blast_radius x tool_impact`.
3. **Unresolved asset** — known tool, unknown asset. Scored as a worst-case
   floor: minimum sensitivity at the tool's highest blast radius.

Bands are `low < medium < high < critical`, plus `invalid` for unscorable calls.

## Sources and tables

| Session (under `logs/proxy/`) | Static table |
|-------------------------------|--------------|
| `parsed/calls.csv` | `corp_filesystem` |
| `sessions/medical_clinic_sim/calls.csv` | `medical_clinic_fs` |
| `sessions/law_firm_sim/calls.csv` | `law_firm_fs` |
| `sessions/media_studio_sim/calls.csv` | `media_studio_fs` |
| `sessions/cbg_sqlite_sim/calls.csv` | `cbg_sqlite` |

Add a session by appending a `(relative_path, table_name)` entry to `SOURCES` in
`src/mcp_security/call_scoring/corpus.py`.

## Module layout

- `loader.py` — read either captured CSV schema into a common `Call`.
- `resolve.py` — map a call's arguments to its server's asset class.
- `tables.py` — load and index the static risk tables.
- `score.py` — score one call against one table.
- `corpus.py` — map sessions to tables, score, rank, and summarize.
