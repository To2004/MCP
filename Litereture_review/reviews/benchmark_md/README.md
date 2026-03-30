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
| `07_mcp_server_database.md` | MCP Server Database | Zhao et al., 2025 | 1,360 servers / 12,230 tools |
| `08_component_attack_poc.md` | Component-based Attack PoC Dataset | Zhao et al., 2025 | 132 servers (up to 1M+ configs) |
| `09_mcp_server_dataset_67k.md` | MCP Server Dataset (67K) | Li & Gao, 2025 | 67,057 servers / 44,499 tools |
| `10_mcp_itp_implicit_poisoning.md` | MCP-ITP Implicit Poisoning Data | Li et al., 2026 | 548 test cases x 12 models |
| `11_nvd_cvss.md` | NVD/CVE Database + CVSS v3.1 | Jafarikhah et al., 2026 | 31,000+ CVEs |
| `12_r_judge.md` | R-Judge Records | Yuan et al., 2024 | 569 multi-turn records |

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
