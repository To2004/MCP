# Benchmark Analysis Files

Individual benchmark analysis files for MCP security datasets and evaluation frameworks. Each file follows a standardized structure covering source, format, data structure, proposed risk dimensions (for 1-10 scoring), data quality notes, and a usefulness verdict.

## Files

| File | Benchmark | Paper | Samples |
|------|-----------|-------|---------|
| `01_mcip_bench.md` | MCIP-Bench | Jing et al., 2025 | 2,218 instances |
| `02_mcip_guardian_training.md` | MCIP Guardian Training Dataset | Jing et al., 2025 | 13,830 instances |
| `03_mcp_attackbench.md` | MCP-AttackBench | Xing et al., 2025 | 70,448 samples |
| `04_mcptox.md` | MCPTox Dataset | Wang et al., 2025 | 1,312-1,497 test cases |
| `05_mcpsecbench.md` | MCPSecBench Playground | Yang et al., 2025 | 17 attack types x 15 trials |
| `06_mcp_safetybench.md` | MCP-SafetyBench | Zong et al., 2025 | 5 domains x 20 types x 13 models |

## Structure of Each File

Each benchmark analysis follows this template:

1. **Source** — paper title, authors, link, year
2. **Format & Size** — sample count, data format, availability
3. **Data Structure** — table of fields/columns with types, examples, and usability notes
4. **Proposed Risk Dimensions** — how each benchmark's data maps to 1-10 risk scoring dimensions
5. **Data Quality Notes** — limitations, missing values, inconsistencies
6. **Usefulness Verdict** — practical assessment for multi-label risk scoring

## Related

- [../benchmarks_review.md](../benchmarks_review.md) — Consolidated benchmarks review
- [../paper_summaries/](../paper_summaries/) — Detailed paper summaries
