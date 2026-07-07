# Scoring Captured Tool Calls

The call-scoring module ranks *real captured calls* — the normal/benign and
misconfiguration traffic recorded under `logs/proxy/` — against the **scanner's**
risk matrices, so every call gets a risk score and band by lookup, with no LLM at
scoring time. Ranking normal traffic surfaces the inherently risky and
misconfigured calls a server should gate, even when nothing malicious is
happening.

The matrices come from the static scanner (`mcp_security.scanner`), which derives
them with the LLM from each server's tools and assets **before the server runs**.
Run the scanner first — it writes `reports/scan/<server>.json`; the ranker scores
calls against those artifacts and never reads the committed design-time tables.

## Running it

```bash
# 1. scan (LLM-only — run on a GPU node; see scripts/scan_and_rank_on_gpu.sbatch)
uv run python -m mcp_security.scanner --kind filesystem --root demo/corp_filesystem \
    --server fs:corp_filesystem

# 2. rank captured calls against the scans
uv run python -m mcp_security.call_scoring            # writes reports/ranked_calls.{csv,md}
uv run python -m mcp_security.call_scoring -v         # with info logging
```

The command prints a band/server summary and the ten riskiest calls, then writes
the full ranked corpus to `reports/ranked_calls.csv` and `reports/ranked_calls.md`
(highest risk first). If no scan artifact exists yet it tells you to run the
scanner first.

## How a call is scored

Each captured session is scored against its server's scan artifact
(`reports/scan/<server>.json`). A call is scored only when it resolves to a
scanned cell; the module never fabricates a score or band for calls it cannot
resolve. For one call:

1. **Resolved** — the argument names an asset the scan knows (a file extension, a
   SQL table, a channel) and the `(tool, asset)` cell exists. The score and band
   come **verbatim** from the scan's `cells` and `bands` matrices. The bands were
   assigned at scan time by the deterministic `band_label` and are read as-is here,
   never recomputed.
2. **`unresolved`** — a known tool whose target is not a cell: a
   directory/enumeration op with no single file asset, a no-argument call, or an
   extension/table the scan never enumerated. No score; the `reason` records which.
3. **`invalid`** — the tool is absent from the scan's tool set (a typo or a
   non-existent tool, e.g. `drop_table`). A misconfiguration signal.

Risk bands are `low < medium < high < critical` (resolved calls only).
`unresolved` and `invalid` are statuses, not bands. Calls rank by numeric score
descending; unscored statuses sink below all scored calls.

## Sources and scans

| Session (under `logs/proxy/`) | Scan artifact (`reports/scan/<stem>.json`) |
|-------------------------------|--------------------------------------------|
| `sessions/filesystem_sim/calls.csv` | `fs_corp_filesystem` |
| `parsed/calls.csv` | `fs_corp_filesystem` |
| `sessions/medical_clinic_sim/calls.csv` | `fs_medical_clinic_fs` |
| `sessions/law_firm_sim/calls.csv` | `fs_law_firm_fs` |
| `sessions/media_studio_sim/calls.csv` | `fs_media_studio_fs` |
| `sessions/cbg_sqlite_sim/calls.csv` | `sqlite_cbg_sqlite` |

Only sessions whose scan artifact is present are scored; the rest are skipped with
a warning. Add a session by appending a `(relative_path, scan_stem)` entry to
`SOURCES` in `src/mcp_security/call_scoring/corpus.py`.

## Module layout

- `loader.py` — read either captured CSV schema into a common `Call`.
- `resolve.py` — map a call's arguments to its server's asset class.
- `tables.py` — load and index the scanner's risk matrices (scan artifacts).
- `score.py` — score one call against one matrix.
- `corpus.py` — map sessions to scans, score, rank, and summarize.

## Input-parameter escalation

On top of the (tool, asset) band, each call's **input-parameter values** are scored
and can escalate its risk. The LLM derives a per-tool rubric — which parameters
carry magnitude (a list length, a content size, a SQL `LIMIT`, …), each with a
`base_rank` and numeric `cutoffs` — written to `reports/scan/<server>_params.json`
(`python -m mcp_security.param_scoring`). For a call: `value_band` comes from the
cutoffs, the **parameter risk** is `average(base_rank, value_band)` rounded half-up,
and `final_band = max(tool_asset_band, parameter_risk)`. So an unbounded
`read_query` (no `LIMIT`) on a low-sensitivity table escalates to `high`, and a
bulk `read_multiple_files` escalates by its path count. The rules live in
`docs/standards/parameter-scoring.md` (which doubles as the LLM prompt); the ranker
shows `final_band`, the cell band, and the escalating parameter. With no rubric
present, `final_band` equals the cell band.

## Grading the scanner

The committed design-time tables are kept only as **evaluation ground truth**
under `reports/evaluation/` (rendered by `scripts/export_eval_tables.py`).
`scripts/evaluate_scanner.py` compares the scanner's matrices to that ground truth
and reports band / tool-impact / asset-sensitivity agreement — the tables grade
the scanner, they never feed it.
