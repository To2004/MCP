# Pipeline correctness verification (deterministic)

Independent re-derivation of every published artifact — no LLM, fully reproducible. A ❌ means an on-disk artifact contradicts the code that produced it.

**8/8 checks pass.**

| Check | Result | Detail |
| --- | --- | --- |
| `no_leakage_paths` | ✅ | no live scoring source reads reports/samples or reports/evaluation |
| `scan_formula` | ✅ | 1700 cells satisfy score=sensitivity*blast*impact |
| `band_distribution` | ✅ | 10 scans: band_distribution matches cells |
| `cell_coverage` | ✅ | every cell's tool & asset is declared |
| `tools_match_tool_list` | ✅ | scan tools equal the advertised tool set for every server |
| `param_rubrics` | ✅ | 71 parameters: valid base_rank & monotonic cutoffs |
| `ranked_calls` | ✅ | 969 rows (830 scored) faithful to scans & ordered |
| `determinism_config` | ✅ | ollama client uses temperature 0 + fixed seed |
