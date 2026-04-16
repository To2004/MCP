# Agent-SafetyBench

## Source
- **Paper:** Agent-SafetyBench: Evaluating the Safety of LLM Agents (Zhang et al., 2024)
- **Authors:** Zhexin Zhang, Shiyao Cui, Yida Lu, Jingzhuo Zhou, Junxiao Yang, Hongning Wang, Minlie Huang
- **Institution:** Tsinghua University (CoAI Group)
- **Link:** https://github.com/thu-coai/Agent-SafetyBench
- **arXiv:** 2412.14470
- **Year:** 2024 (revised May 2025)

## Format & Size
- **Total samples:** 2,000 test cases
- **Interaction environments:** 349 distinct scenarios
- **Safety risk categories:** 8
- **Failure modes:** 10 common patterns
- **Agents evaluated:** 16 popular LLM agents
- **Availability:** Open-source on GitHub (`thu-coai/Agent-SafetyBench`)
- **Headline result:** none of the 16 evaluated agents scored above 60% safety

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Test case ID | String | ASB-0123 | Yes | Links to scenario |
| Interaction environment | Categorical (349) | finance app, calendar assistant, filesystem host, ... | Yes | Rich scenario coverage |
| Risk category | Categorical (8) | data leakage, harmful execution, unauthorized access, ... | Yes | Supports multi-label scoring |
| Failure mode | Categorical (10) | lack of robustness, risk-awareness gap, ... | Yes | Fine-grained error typology |
| Agent response | Text | Step-by-step trajectory | Yes | Full interaction recorded |
| Safety score | Float (%) | % safe actions per agent | Yes | Primary metric |
| Model identifier | Categorical (16) | GPT-4, Claude, Llama, ... | Yes | Cross-model comparison built in |

## Proposed Risk Dimensions

### Risk-Category Multi-Label Vector
- **Feeding columns:** risk category (8)
- **Proposed scale:** 1-10 per category, summed or max-pooled per request
- **Derivation:** Each of the 8 categories maps to an independent severity score; a single
  request can trigger multiple categories simultaneously. This is the closest published
  analog to a "multi-label risk vector" and maps cleanly into the project's v3
  Agent Action Severity dimension, which already needs to absorb multiple attack types.

### Failure-Mode Behavioral Signature
- **Feeding columns:** failure mode (10)
- **Proposed scale:** 1-10 where signatures of known failure modes raise the score
- **Derivation:** The 10 failure modes (lack of robustness, lack of risk awareness, etc.)
  are behavioral signatures. Train a lightweight classifier to detect each signature in
  live agent requests — presence of a signature elevates the session's risk band. Maps
  into the v3 Agent Compromise Indicator dimension.

### Cross-Model Ceiling Calibration
- **Feeding columns:** safety score across the 16 evaluated models
- **Proposed scale:** 1-10 calibrated so that 60% (the best published result) sits at 5,
  not 10
- **Derivation:** Agent-SafetyBench shows *no current model passes*, which means the
  scorer should be calibrated against this ceiling rather than assuming model-level
  safety. Treating 60% as "average" rather than "good" is the right prior when the
  server has to defend against all 16 model classes.

## Data Quality Notes
- 349 environments is **broader scenario coverage than AgentDojo's 4 task suites** —
  strong signal that a server deployed in a novel domain still needs defense coverage.
- The 60%-ceiling result is the key empirical finding: relying on the LLM's own safety
  alignment as the first line of defense is a 40%-failure-rate strategy. This is
  concrete motivation for the project's server-side framing.
- Scenarios and labels are Tsinghua-curated; English-language benchmark with some
  translated scenarios.
- **Not MCP-specific.** Methodology and failure-mode taxonomy are transferable; raw
  data is not.
- Recent (Dec 2024, revised May 2025), so downstream defense literature on it is still
  sparse compared to AgentHarm and AgentDojo.

## Usefulness Verdict
Agent-SafetyBench is the most directly usable of the three new additions because its
**8 risk categories + 10 failure modes** provide structured signals that can feed a
multi-dimensional scoring system — not just binary "safe/unsafe" labels. The headline
result (no model above 60% safe across 16 evaluated agents) is a concrete, citable
justification for the project's server-side framing: if the agents themselves cannot be
trusted, the server must score. For implementation, treat the 8 risk categories as a
label space that the v3 Agent Action Severity dimension can absorb, and use the 10
failure modes as behavioral signatures for the v3 Agent Compromise Indicator dimension.
Scenarios are broader than AgentDojo but still general-agent, not MCP-specific — run
alongside MCPTox (#4) or MCIP-Bench (#1) rather than as a standalone.
