# Figures — Extracted from Literature Review Papers

This folder contains figures, tables, and diagrams extracted from research papers
for use in Hebrew summary documents.

## Source: MCPShield (Paper #02)

| File | Description | Paper Figure |
|------|-------------|-------------|
| `fig1_mcpshield_architecture.png` | Main framework architecture overview | Figure 1 |
| `fig2_pass_at_k_stability.png` | Pass@K stability analysis across suites | Figure 2 |
| `fig3_runtime_overhead.png` | Runtime overhead per model and benchmark | Figure 3 |
| `fig4_token_usage.png` | Token consumption analysis | Figure 4 |
| `fig5_defense_effectiveness.png` | Defense effectiveness under Drift Attack | Figure 5 |
| `table1_robustness.png` | Robustness results (defense rate w/ and w/o MCPShield) | Table 1 |
| `table2_benign_preservation.png` | False positive rates on benign servers | Table 2 |
| `table3_stage_comparison.png` | Stage-wise ablation (PRE/EXEC/POST contribution) | Table 3 |
| `appendix_stage1_prompts.png` | Stage 1 prompt templates (mock + evaluation) | Appendix A.1 |
| `appendix_stage2_prompts.png` | Stage 2 prompt templates (projection + analysis) | Appendix A.2 |
| `appendix_stage3_prompt.png` | Stage 3 prompt template (periodic reasoning) | Appendix A.3 |

## Usage

These images are referenced from `../02_MCPShield_summary_HE.md` using relative paths:
```markdown
![Description](figures/fig1_mcpshield_architecture.png)
```

## Source Paper

Zhou, Z., Zhang, Y., Cai, H., et al. (2026). *MCPShield: A Security Cognition Layer
for Adaptive Trust Calibration in Model Context Protocol Agents.* arXiv:2602.14281v3.
