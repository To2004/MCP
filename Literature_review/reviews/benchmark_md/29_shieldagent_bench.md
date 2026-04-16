# ShieldAgent-Bench

## Source
- **Paper:** ShieldAgent: Shielding Agents via Verifiable Safety Policy Reasoning (Chen et al., 2025)
- **Link:** https://shieldagent-aiguard.github.io/
- **arXiv:** 2503.22738
- **Year:** 2025

## Format & Size
- **Total samples:** ~3,000 safety-related pairs of agent instructions and action trajectories
- **Safety-related instructions:** 960
- **Unsafe trajectories:** 3,110 (collected via SOTA attacks)
- **Web environments:** 6 diverse environments
- **Risk categories:** 7
- **Annotation level:** **Step-level**
- **Monitored behavior:** web browsing (specifically, not general tool calls)
- **Pattern coverage (per ToolSafe):** MUR ✓, PI ✓, HT —, BTRA —
- **Availability:** Project page + repository at the URL above

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Instruction ID | String | SA-B-0071 | Yes | Maps to one of 960 safety-related instructions |
| Web environment | Categorical (6) | e-commerce, social, mail, workspace, ... | Yes | Scenario context |
| Risk category | Categorical (7) | privacy, fraud, policy violation, ... | Yes | Target safety policy |
| Action trajectory | Structured | Sequence of browser actions with DOM state | Yes | Full trajectory |
| Step label | Categorical | safe / unsafe | Yes | Per-step annotation |
| Attack method | Categorical | agent-based / environment-based | Yes | Two SOTA attack families |
| Verified policy rule | Structured | Machine-verifiable policy statement | Yes | Enables rule-recall evaluation |
| Guardrail inference cost | Numeric | API queries, inference time per sample | Yes | Efficiency metric |

## Proposed Risk Dimensions

### Policy-Rule Recall Score
- **Feeding columns:** verified policy rule, guardrail decision
- **Proposed scale:** 1-10 where 10 = full rule recall, 1 = no rule grounding
- **Derivation:** ShieldAgent-Bench's distinguishing feature is that every labeled
  unsafe action maps to a **machine-verifiable policy rule** it violates. For the
  project's scorer, this provides a direct test of whether the model's deny decisions
  are grounded in identifiable rules (high score) or in pattern-matching
  generalization (low score). Maps into a "score explainability" dimension, which is
  a practical need for the Lenovo deployment constraint — deny decisions should be
  justifiable.

### Policy-Aware Severity (7 Risk Categories)
- **Feeding columns:** risk category (7)
- **Proposed scale:** 1-10 per category, weighted by the severity of the policy being
  violated
- **Derivation:** 7 categories is narrower than Agent-SafetyBench (8) or ASSEBench (15),
  but each is tied to a concrete policy rule — making it easier to translate into
  actionable server-side policies. Use as a target schema when mapping MCP server
  capabilities to policy-rule checks.

### Efficiency Baseline (API Queries + Latency)
- **Feeding columns:** inference cost per sample
- **Proposed scale:** Not a per-sample risk score — a benchmark comparator
- **Derivation:** ShieldAgent reports ~64.7% reduction in API queries and ~58.2%
  reduction in inference time vs. baselines on this benchmark. These numbers set a
  concrete efficiency target — any server-side scorer the project builds should
  benchmark against ShieldAgent-Bench for both accuracy *and* efficiency to show
  it is viable under Lenovo's practicality constraint.

## Data Quality Notes
- **Policy-rule grounding is the standout feature.** Most benchmarks label outcomes;
  ShieldAgent-Bench labels *why* something is unsafe by linking to a verifiable rule.
  This is the strongest foundation for explainable scoring in the entire benchmark set.
- **HT and BTRA not covered.** ShieldAgent-Bench focuses on MUR and PI only — the
  tool-manifestation axis is absent. Cover the gap with TS-Bench or OS-Safe.
- **Web-browsing only.** The 6 environments are all web-based, which limits transfer
  to MCP servers that expose non-web domains (filesystem, shell, custom APIs).
- 2-attack-family construction (agent-based + environment-based) is narrower than
  AgentDojo's parameterized attack generation, but the attacks are real SOTA methods,
  not synthetic templates.
- ShieldAgent itself achieves 90.1% recall and 11.3% average improvement over prior
  guardrails on this benchmark — these are the reference numbers to beat.

## Usefulness Verdict
ShieldAgent-Bench is the **policy-grounded, explainability-forward** benchmark in the
agent safety landscape. Its unique contribution is that every unsafe label traces to a
machine-verifiable policy rule, which is exactly what the project needs when the MCP
server has to justify a deny decision to the agent or to the Lenovo operator. The
strongest uses are: (1) evaluating whether the scorer's deny decisions are rule-grounded,
(2) borrowing the 7-category policy schema as a starting point for MCP-specific
policy rules, and (3) using ShieldAgent's reported 90.1% recall + efficiency numbers
as the target ceiling to benchmark against. The benchmark's main limitations for the
project are coverage scope (MUR + PI only, no HT or BTRA) and environment (web-only,
not MCP tools) — neither is fatal, but both mean ShieldAgent-Bench must be paired
with TS-Bench (26) for full 2×2 coverage and with an MCP-specific benchmark like
MCPTox or MCIP-Bench for the actual evaluation.
