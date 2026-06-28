# Positioning matrix: McpRisk vs. neighbouring risk-scoring works

Distilled from the cited papers. Axes chosen to separate a per-invocation, server-side, graduated MCP risk scorer from neighbouring approaches.

| Framework | Scores | Timing | Output | Ground truth | Threat direction | Per-call | Arg-aware |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **McpRisk (ours)** | MCP tool invocation risk per (tool, asset) | static (design) + dynamic (request) | graduated band 1–4 / 0–60 score | external MCP attack benchmarks | server is victim (client→server) | yes — per (tool, asset, args) | partial (param magnitude; contextual LLM planned) |
| CVSS v3 | software vulnerability severity | static, once per vuln | 0–10 score | NVD / analyst consensus | n/a (software) | no (per vuln) | no |
| AIVSS (OWASP) | agentic-AI vulnerability severity | static | CVSS base × agentic factors → 0–10 | expert rubric | agent system (generic) | no (per vuln / system) | no |
| AgenTRIM | tool-driven agency risk (least-privilege) | offline + runtime per step | allow/deny + risk | none public (AgentDojo task success) | agent tool misuse / injection | yes — per tool call | partial |
| AURA | agent autonomy risk | design + runtime | gamma-based score | none (framework) | agent autonomy (generic) | per action | no |
| MCP-RiskCue | risk inferred from MCP server logs | runtime (post-hoc on logs) | risk label/severity | synthetic logs + human labels | server-side telemetry | per log event | yes (reads logs) |
| ASTRA | context-/steerability-adjusted risk | design | ordinal risk tiers | none (framework) | application context (generic) | no | no |
| R-Judge | safety-risk awareness from agent traces | runtime / post-hoc | binary safe / unsafe | 569 human-labeled records | agent safety (mixed) | per trajectory step | yes (reads trace) |
| Permission-risk (Entra) | OAuth permission/capability risk | static, at grant time | ordinal risk score | expert consensus (769 perms) | capability grant | no (per permission) | no |
| Description→Score | CVSS severity from CVE text | static, once per vuln | CVSS base metrics | MITRE CVSS labels | n/a (software) | no (per vuln) | no |

## The unoccupied cell

No prior work scores **graduated, per-(tool, asset) MCP invocation risk** in **both** a design-time and a request-time mode under the **server-as-victim** threat model and validates it on **external attack benchmarks**. Capability scorers (CVSS, AIVSS, permission-risk, Description→Score) are per-vulnerability and argument-blind; agent-safety detectors (R-Judge, AgenTRIM, AURA) are binary or allow/deny and mostly evaluated by task success, not graduated risk.
