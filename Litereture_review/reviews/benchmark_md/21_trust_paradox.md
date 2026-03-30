# Trust Paradox Evaluation Scenarios

## Source
- **Paper:** The Trust Paradox in LLM-Based Multi-Agent Systems — Xu et al.
- **Link:** https://arxiv.org/abs/2510.18563
- **Year:** 2025

## Format & Size
- **Total samples:** 19 evaluation scenarios across 5 capability tiers
- **Format:** Structured scenarios with quantitative trust and safety metrics; evaluated across 4 LLM backends
- **Availability:** arXiv paper — https://arxiv.org/abs/2510.18563 (scenario descriptions and metrics in paper; check for supplementary materials)

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Scenario ID | categorical | 1-19 | Yes | Each scenario is a distinct evaluation case |
| Capability tier | ordinal | basic, intermediate, advanced, expert, critical | Yes | 5 tiers — directly maps to agent capability risk adjustment |
| LLM backend | categorical | GPT-4o, Claude 3.5 Sonnet, Llama 3.1 70B, Mixtral 8x22B | Yes | 4 backends for cross-model comparison |
| Trust Calibration Index (TCI) | numeric (0-1) | 0.72-0.89 | Yes | Core metric — measures gap between assigned trust and actual trustworthiness |
| Capability-Risk Ratio | numeric | Varies per scenario/model | Yes | Ratio of capability to risk — higher capability does not mean lower risk |
| Safety Violation Rate | numeric (0-1) | Varies per scenario/model | Yes | Direct measure of how often agents violate safety boundaries |
| Inter-agent trust score | numeric (0-1) | 0.73-0.91 | Partially | Stabilizes after 8-15 iterations — initial values are unreliable |
| Convergence iterations | integer | 8-15 | Yes | Number of interactions before trust scores stabilize |

## Proposed Risk Dimensions

### Trust Calibration Risk
- **Feeding columns:** Trust Calibration Index (TCI), inter-agent trust scores
- **Proposed scale:** 1-10 where 1 = trust is well-calibrated (assigned trust matches actual behavior), 10 = severe miscalibration (agent trusted far beyond its actual reliability)
- **Derivation:** TCI ranges from 0.72 to 0.89 in the paper, meaning even the best-calibrated systems have a 11-28% trust gap. Map (1 - TCI) to a 1-10 scale: a TCI of 0.89 maps to ~2 (low risk), a TCI of 0.72 maps to ~4 (moderate risk). For MCP, extend the scale to cover worse cases not in the dataset. This dimension answers: "How much should we trust the trust score itself?"

### Capability-Tier Risk Adjustment
- **Feeding columns:** Capability tier (basic through critical), Capability-Risk Ratio
- **Proposed scale:** 1-10 where 1 = capability tier is low and risk exposure is minimal, 10 = capability tier is critical and risk exposure is maximal
- **Derivation:** The 5 capability tiers map to risk exposure levels. Basic tier tools (read-only, no side effects) start at 1-2. Critical tier tools (system administration, financial transactions, data deletion) start at 8-10. The key insight from the trust paradox: more capable agents are given more trust, but this trust is systematically miscalibrated upward. So the risk adjustment should *increase* with capability tier, not decrease. For MCP, multiply the base capability-tier score by a trust-miscalibration factor derived from the Capability-Risk Ratio.

### Safety Violation Risk
- **Feeding columns:** Safety Violation Rate per scenario and model
- **Proposed scale:** 1-10 where 1 = no safety violations observed, 10 = frequent safety boundary violations
- **Derivation:** Direct mapping of Safety Violation Rate to 1-10. For MCP tools, this is the most actionable dimension — it measures how often an agent actually crosses safety boundaries in practice, not just in theory. Use the per-model violation rates to set model-specific risk adjustments.

### Multi-Agent Trust Stability Risk
- **Feeding columns:** Inter-agent trust scores, convergence iterations (8-15)
- **Proposed scale:** 1-10 where 1 = trust scores are stable and reliable, 10 = trust scores are volatile and unreliable
- **Derivation:** The finding that inter-agent trust requires 8-15 iterations to stabilize means that early interactions are risky — trust scores have not converged yet. For MCP, this maps to a temporal risk dimension: new agent-tool pairings should get higher risk scores that decrease as interaction history accumulates. Score = f(interactions_so_far / convergence_threshold). Below 8 interactions: score 7-10. Above 15 interactions: score 1-3.

## Data Quality Notes
- Only 19 scenarios is a small dataset — statistical power is limited, and the scenarios may not cover all real-world MCP tool use cases.
- The 4 LLM backends provide decent model diversity (2 proprietary, 2 open-source), but results may not generalize to other models or future model versions.
- TCI is a novel metric introduced in this paper — it has not been independently validated or widely adopted yet. Use with appropriate caution.
- Inter-agent trust score stabilization at 8-15 iterations is an empirical finding from these 19 scenarios; the actual convergence point may vary significantly in different deployment contexts.
- The paper is from 2025 and may still be pre-peer-review. The arxiv ID (2510.18563) suggests October 2025 submission. Verify the review status before relying heavily on specific numbers.

## Usefulness Verdict
This is a uniquely valuable benchmark for MCP risk scoring because it directly studies the *trust* problem in multi-agent systems rather than just measuring capability or safety in isolation. The trust paradox finding — that more capable agents receive systematically miscalibrated trust — is the core justification for why a dynamic risk scoring system is needed in the first place. If trust were naturally well-calibrated, a simple capability-based scoring system would suffice. The TCI metric showing 0.72-0.89 calibration proves it does not.

For the MCP 1-10 risk scoring system, the most actionable contributions are: (1) the 5 capability tiers provide a ready-made framework for base risk level assignment, (2) the TCI metric can be directly adopted or adapted as a "trust dimension" score, and (3) the convergence finding (8-15 iterations) provides empirical guidance for how to handle temporal risk — new tool-agent pairings should start with elevated risk scores that decay as interaction history builds. The small dataset size (19 scenarios) means this benchmark is better used for framework design and calibration than for training a scoring model, but the conceptual contributions are high-impact.
