# External-benchmark detection: risk scorers as attack detectors

Ground truth: 150 labeled calls from the third-party benchmarks MCPSecBench, MCP-SafetyBench, and MSB (same threat model: the MCP server is the protected asset; calls flow client→server). Each scorer's per-call risk is graded as a detector of ATTACK. We report **AUC** (threshold-free ranking quality) and **recall@10%FPR** (attacks caught at a tight false-positive budget) — the two metrics that discriminate here; single-threshold F1 collapses to the no-skill ‘flag everything’ point for scorers that do not separate, so it is kept only in the JSON. Capability-only frameworks (CVSS, AIVSS) score the *tool* and cannot see the argument where the attack lives; content/context-aware scorers can.

### ATTACK vs VALID  (55 positive / 59 VALID)

| scorer | AUC | recall@10%FPR |
| --- | --- | --- |
| llm_judge | 0.68 | 42% |
| keyword | 0.67 | 38% |
| cvss | 0.52 | 0% |
| aivss | 0.52 | 0% |
| majority | 0.50 | 0% |
| random | 0.48 | 11% |

### flag-worthy vs VALID  (79 positive / 59 VALID)

| scorer | AUC | recall@10%FPR |
| --- | --- | --- |
| llm_judge | 0.64 | 34% |
| keyword | 0.61 | 28% |
| cvss | 0.51 | 0% |
| aivss | 0.51 | 0% |
| majority | 0.50 | 0% |
| random | 0.47 | 9% |

### Per-benchmark AUC (ATTACK vs VALID)

| scorer | mcp_safetybench | mcpsecbench | msb |
| --- | --- | --- | --- |
| cvss | 0.50 | 0.57 | 0.52 |
| aivss | 0.50 | 0.57 | 0.52 |
| keyword | 0.62 | 0.69 | 0.62 |
| majority | 0.50 | 0.50 | 0.50 |
| random | 0.46 | 0.47 | 0.51 |
| llm_judge | 0.65 | 0.64 | 0.74 |
