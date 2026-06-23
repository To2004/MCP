# reports/samples

Sample/reference outputs of the scoring pipelines — generated artifacts, kept in
the repo as worked examples, not hand-authored.

| File | Produced by | Notes |
|------|-------------|-------|
| `all_static_tables.json` | `python -m mcp_security.static_scoring --all` | **Combined** — every demo server in one file, with a cross-server `index` + `totals` |
| `payment_static_table.json` | static-scoring pipeline (mock payment MCP) | The original reference table; `mcp_kind` is a mock |
| `filesystem_static_table.json` | `... --kind filesystem` | From the simulated `secure-filesystem-server` registry |
| `sqlite_static_table.json` | `... --kind cbg_sqlite` | From the live `demo/cbg_sqlite/cbg.db` schema |

`all_static_tables.json` is the headline deliverable: each server's full table
under `tables.<name>`, plus an `index` (worst band, critical cells, judge
overrides per server) and `totals` for a quick read.

### take1 vs take2

- `all_static_tables.json` — **take1**: filesystem assets are file *types*
  (`.txt`, `.pem`). Misses content-sensitivity that lives in the path.
- `all_static_tables_take2.json` — **take2** (`--take2`): filesystem assets are
  individual files by **full path** (`patients/alice/medical_history.txt`), so
  medical/legal records score correctly. The `version` field carries the tag.

Compare the two for `medical_clinic_fs`/`law_firm_fs`: take1 finds 0 critical
cells; take2 surfaces the patient/client records as critical.

The `filesystem_*` and `sqlite_*` tables here were generated offline
(`--no-llm`), so they carry `model_reviewed: false` and
`inferred_profile.needs_human_review: true`. Regenerate them model-reviewed with
`sbatch scripts/static_score_on_gpu.sbatch` on a GPU node.

See `src/mcp_security/static_scoring/README.md` for the table schema.
