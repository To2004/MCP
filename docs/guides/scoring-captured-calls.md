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
(`reports/samples/all_static_tables.json`). A call is scored only when it
resolves to a precomputed cell; the module never fabricates a score or band for
calls it cannot resolve. For one call:

1. **Resolved** — the argument names an asset the table knows (a file extension,
   a SQL table, a channel) and the `(tool, asset)` cell exists. The score and
   band come **verbatim** from the table's `cells` and `bands` matrices. The
   bands carry design-time judgement and are never recomputed from the score.
2. **`unresolved`** — a known tool whose target is not a cell: a
   directory/enumeration op with no single file asset, a no-argument call, or an
   extension/table the design-time table never enumerated. No score; the
   `reason` records which, so the table can be extended where it matters.
3. **`invalid`** — the tool is absent from the table's registry (a typo or a
   non-existent tool, e.g. `drop_table`). A misconfiguration signal.

Risk bands are `low < medium < high < critical` (resolved calls only).
`unresolved` and `invalid` are statuses, not bands. Calls rank by numeric score
descending; unscored statuses sink below all scored calls.

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
