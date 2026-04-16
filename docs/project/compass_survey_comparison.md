# Compass Risk-Scoring Survey vs. MCP-RSS: Comparison Report

A structured comparison between the "Risk scoring frameworks for autonomous AI agent systems" survey
(the Compass artifact, April 2026) and the MCP-RSS thesis framework.

---

## 1. What Each Document Is

### The Compass Survey

A synthesis of 40+ academic papers and industry frameworks covering the theoretical foundations,
scoring methodologies, and architectural patterns relevant to building a continuous, server-side
risk score for MCP tool invocations. It explicitly concludes that no single published paper
implements the exact server-side perspective and identifies three open research gaps. Source file:
[`Literature_review/risk_scoring_frameworks_survey.md`](../../Literature_review/risk_scoring_frameworks_survey.md).

### MCP-RSS (This Thesis)

A **dynamic, ordinal, agent-aware risk scorer for the agent→server direction of the Model Context
Protocol**. The MCP server is the protected asset; AI agents are the threat source. The framework
scores incoming agent tool-call requests in two modes — static (design-time tool properties) and
dynamic (runtime call context and session state) — outputting an ordinal 1–10 score that drives
gate/throttle/deny decisions. Core novelty claim:

> *MCP-RSS is the first dynamic, ordinal, agent-aware risk scorer for the agent→server direction
> of the Model Context Protocol.*

Reference documents: [`risk-scoring-taxonomy-comparison.md`](risk-scoring-taxonomy-comparison.md),
[`related_work_gap_matrix.md`](../../Literature_review/related_work_gap_matrix.md).

---

## 2. Coverage Overlap: Already Known vs. Net-New

### Papers already in MCP-RSS literature review

| Paper | ArXiv ID | Already covered in |
|-------|----------|--------------------|
| ToolSafe | 2601.10156 | risk-scoring-taxonomy-comparison.md §1 |
| MCPShield | 2602.14281 | risk-scoring-taxonomy-comparison.md §2, gap-matrix.md |
| MCP-Guard | 2508.10991 | related_work_gap_matrix.md (nearest A→S prior art) |
| R-Judge | 2401.10019 | risk-scoring-taxonomy-comparison.md §4, gap-matrix.md |
| MAESTRO/ATFAA | 2508.10043 | risk-scoring-taxonomy-comparison.md §5 |
| TRiSM for Agentic AI | 2506.04133 | risk-scoring-taxonomy-comparison.md §6 |
| OWASP AIVSS | — | risk-scoring-taxonomy-comparison.md §9 |
| Threat Model for Agent Protocols | 2602.11327 | gap-matrix.md |
| ToolEmu | 2309.15817 | mentioned in taxonomy docs |

### Net-new papers introduced by the Compass survey

| Paper / Framework | ArXiv ID | Key Contribution | Priority |
|-------------------|----------|-----------------|----------|
| MCPShield Formal | 2604.05969 | 7-category/23-vector taxonomy from 177k tools; ≤34% coverage by any existing defense | **High** |
| MCP-in-SoS | 2603.10194 | Exact A→S threat model; CWE Risk Index → per-repo severity | **High** |
| TraceSafe-Bench | 2604.07223 | Empirical proof: granular > binary, across 13 LLMs and 7 guards | **High** |
| SafePred | — | Scalar risk score + configurable threshold gating (world-model based) | **High** |
| CORTEX | 2508.19281 | 5-tier Bayesian + Monte Carlo; 29-category taxonomy from 1,200+ incidents | High |
| AgentGuard | 2509.23864 | Online MDP for probabilistic failure estimation | High |
| AURA | 2510.15739 | Gamma-based modular runtime scoring; adjustable at runtime | Medium |
| GaaS | 2508.18765 | Severity-weighted penalty proxy; gate/throttle/deny output | Medium |
| Guardrails as Infrastructure | 2603.18059 | Quantifies safety-capability tradeoff: P0→P4 = 68% fewer violations, 81% fewer task completions | **High** |
| TOP-R | 2512.16310 | Mosaic effect — individually low-risk calls compose into high-risk chains | **High** |
| Trinity Defense | 2602.09947 | (p)^n degradation model for multi-agent chain scoring | High |
| SEAgent | 2601.11893 | MAC/ABAC + information flow graph; 0% ASR on all benchmarked vectors | High |
| FINOS AIR-OP-028 | — | 5 trust-boundary violation types; 4 propagation patterns | Medium |
| Repello AI Blast Radius | — | 4-factor blast radius model; persistence as the least-understood factor | Medium |
| KRI Framework | 2603.12450 | Expected-loss KRI with ROC-AUC 0.927 | Medium |
| Microsoft AGT | — | 0–1000 dynamic trust score, 5 tiers, behavioral decay; <0.1 ms p99 | **High** |
| Traceable AI | — | 0–10 Likelihood × Impact; "spatial impact" = blast radius for APIs | High |
| CSA Agentic Trust Framework | — | 4 maturity levels; circuit breakers for cascading failure | Medium |
| AgentSpec | 2503.18666 | DSL triggers + graduated enforcement (ICSE 2026) | Medium |
| AgentSentinel | 2509.07764 | Rule + AI dual auditor, pre-execution gating | Low |
| AgenTRIM | 2601.12449 | Per-step adaptive filtering | Low |
| NVIDIA ARP Framework | 2511.21990 | Graph-based risk decomposition | Low |
| Quantitative Security Benchmarking MAS | 2507.21146 | Formal trust relations T ⊆ A×A | Low |
| TrustBench | 2603.09157 | Real-time inline trust verification | Low |
| ConfusedPilot | 2408.04870 | Confused deputy in RAG systems | Low |
| Zero Trust Identity | 2505.19301 | DIDs + VCs + ZKPs for agent identity | Low |
| Permission Risk Scoring | 2512.15781 | LLM-based API permission tiering | Low |
| Databricks DASF v3.0 | — | 97 risks, 73 controls | Low |
| Adversa AI MCP Top 25 | — | Impact 40%/Exploit 30%/Prevalence 20%/Remediation 10% weighting | Low |
| ASTRA | 2511.18114 | Application-context risk assessment | Low |

---

## 3. Where the Compass Survey Strengthens MCP-RSS

### 3.1 Empirical validation of ordinal over binary scoring

**TraceSafe-Bench** (arXiv 2604.07223) provides direct empirical evidence across 13 LLMs and 7 guards
that granular risk taxonomies consistently outperform binary safe/unsafe classifiers for multi-step
tool-calling trajectories. This is the strongest published empirical argument for MCP-RSS's
ordinal 1–10 output over MCP-Guard's binary block/pass.

> **Thesis use:** cite in §2 (Motivation) when justifying why a numeric score is preferable to
> a threshold classifier.

### 3.2 The survey explicitly identifies MCP-RSS's exact gap

The Compass survey closes with:

> *"No published work implements the exact server-side perspective — computing a continuous risk
> score for each incoming agent tool call from the server's vantage point; most work takes the
> agent's perspective."*

This is an independent third-party source confirming the novelty claim. It is more credible in a
thesis than self-assertion.

> **Thesis use:** quote directly in §3 (Related Work gap summary) as external corroboration.

### 3.3 Microsoft AGT validates the product direction

Microsoft's production quote:
> *"A binary trusted/untrusted model doesn't capture reality. Trust scoring with behavioral decay
> and dynamic privilege assignment turned out to be a much better model."*

This is a production system (open-sourced April 2026) operated at scale, arriving at the same
design conclusion as MCP-RSS independently. The AGT's gate/throttle/deny enforcement at <0.1 ms
p99 also validates that runtime scoring is operationally feasible.

> **Thesis use:** cite in §2 (Motivation) as industry validation. Position MCP-RSS as the
> academic counterpart: AGT is a proprietary, closed scoring model; MCP-RSS provides an
> open, MCP-native, reproducible framework.

### 3.4 MCP-in-SoS validates the static scoring direction

MCP-in-SoS (arXiv 2603.10194, March 2026) uses the exact same threat model — server as protected
asset, agent/client as untrusted requester — and implements static risk scoring via CWE Risk
Indices derived from server code analysis. It validates that static scoring of server endpoints
is tractable. The gap is that MCP-in-SoS is design-time only (code analysis, not request-level)
and does not produce a per-call dynamic score.

> **Thesis use:** position as the static-mode precedent that MCP-RSS extends to runtime.

### 3.5 TOP-R validates session chain risk as a research necessity

TOP-R (arXiv 2512.16310) proves the "mosaic effect" empirically: individually low-risk tool calls
compose into high-risk information synthesis when sequenced. This directly validates MCP-RSS's
session-context accumulation dimension and shows that per-call scoring alone is insufficient.

> **Thesis use:** cite in the dynamic scoring design section when motivating session-level
> context tracking across calls within a single agent session.

### 3.6 Guardrails as Infrastructure quantifies the threshold calibration problem

225 controlled experiments show that moving from policy P0 (no guardrails) to P4 (strictest)
reduces violations from 0% to 68.1% but also drops task success from 35.6% to 6.7%. This is the
most precise published measurement of the safety-capability tradeoff — directly relevant to
choosing the MCP-RSS gate/throttle/deny threshold.

> **Thesis use:** cite in §6 (Evaluation / Limitations) when discussing threshold selection as
> an open problem. The tradeoff curve also frames Lenovo's operational concern about false positives.

---

## 4. Where the Compass Survey Contextualizes or Challenges MCP-RSS

### 4.1 Microsoft AGT as industrial prior art — requires explicit positioning

The AGT implements dynamic trust scoring with gate/throttle/deny actions at production scale.
While it is not MCP-specific and is a closed proprietary system, it does implement the core
pattern. MCP-RSS cannot claim "first dynamic trust scoring system for agentic AI" — that claim
would be false.

**How to position:** MCP-RSS's novelty is specifically the combination of MCP-native dimensions
(blast radius, permission overreach, chain risk), ordinal academic output, and agent-aware
open framework design. AGT is the existence proof that the pattern works; MCP-RSS is the
principled, reproducible, protocol-specific instantiation.

### 4.2 MCPShield Formal (arXiv 2604.05969) — taxonomy overlap risk

The April 2026 extended MCPShield paper analyzes 177,000+ MCP tools and constructs a taxonomy
covering **7 categories, 23 attack vectors, and 4 attack surfaces**. It also concludes that no
existing defense covers more than 34% of its threat landscape — which implies MCP-RSS's attack
taxonomy will need to be compared against this taxonomy.

**Action required:** read arXiv 2604.05969 in full. Map the 7 categories against the current
MCP-RSS attack taxonomy ([`mcp_server_attack_taxonomy_v2_agent_boundary.md`](../../Literature_review/mcp_server_attack_taxonomy_v2_agent_boundary.md)).
If MCPShield Formal's A→S subcategories overlap, cite it as a taxonomy precedent; if not,
differentiate explicitly.

### 4.3 CORTEX and AgentGuard as more sophisticated formula alternatives

CORTEX uses Bayesian aggregation with Monte Carlo simulation (5-tier model). AgentGuard uses
an online MDP with continuous failure probability estimation. Both are more theoretically
grounded than R = P × I × E but also significantly more complex to implement and calibrate.

**How to position:** MCP-RSS's R = P × I × E formula trades theoretical completeness for
implementability — justified by the Lenovo deployment constraint (cost, speed, practicality).
CORTEX and AgentGuard represent research-track extensions; MCP-RSS is the deployable baseline.

### 4.4 Traceable AI's "spatial impact" overlaps with blast radius scoring

Traceable AI's commercial implementation already scores API endpoints using a "spatial impact"
factor (number of downstream API dependencies) — essentially blast radius for API calls. This
means the blast radius dimension in MCP-RSS has commercial precedent, not just academic theory.

**How to position:** validates the dimension. Position MCP-RSS as bringing the same signal to
the MCP protocol layer with an open, reproducible methodology.

---

## 5. Scoring Formula Landscape

How published formulas compare to MCP-RSS's planned approach:

| Framework | Formula | Output Scale | Static | Dynamic | Agent-Aware |
|-----------|---------|-------------|--------|---------|-------------|
| **MCP-RSS** | TBD (target: P × I × E variant) | 1–10 ordinal | Yes | Yes | Yes |
| MAESTRO | R = P × I × E (1–3 per factor) | 1–27 | Yes | Yes | No |
| OWASP AIVSS | ((CVSS + AARS) / 2) × ThM | 0–10 | Yes | No | Partial |
| CORTEX | Bayesian (Likelihood × Impact + overlays) | 0–10 | Yes | Yes | No |
| AgentGuard | P(failure \| constraints) via online MDP | 0–1 probability | No | Yes | No |
| GaaS | Σ severity-weighted penalties | Trust score | No | Yes | No |
| Microsoft AGT | Behavioral decay on 0–1000 scale | 0–1000 | No | Yes | Yes |
| Traceable AI | Likelihood × Impact (with spatial factor) | 0–10 | Yes | Yes | No |
| SafePred | risk(a) ≤ T (world-model bound) | Scalar | No | Yes | No |
| R = P × I × E (ATFAA) | same as MAESTRO | 1–27 | Yes | Yes | No |
| Trinity Defense | 1 − (p)^n for chain degradation | 0–1 probability | Yes | No | No |
| KRI Framework | Expected-loss KRI | 0–1 (ROC) | Yes | Yes | Partial |

**Key observation:** MCP-RSS's target output range (1–10 ordinal) matches the most widely deployed
commercial systems (Traceable AI, OWASP AIVSS) and is the most interpretable for operators
making gate/throttle/deny policy decisions. The 1–27 range of R = P × I × E is less intuitive
but maps cleanly onto three tiers (low: 1–9, medium: 10–18, high: 19–27).

**Recommended formula path:** Start with R = P × I × E (1–27 raw), normalize to 1–10, then add
an agent-awareness modifier for session state. This integrates the three best-validated
approaches without the calibration overhead of Bayesian models.

---

## 6. Thesis Novelty Claim: Impact Assessment

The Compass survey does not weaken the defensible claim. It strengthens it on three axes:

| Qualifier in the novelty claim | Compass survey verdict |
|-------------------------------|------------------------|
| **dynamic** | Confirmed gap: all MCP-specific academic work is static or lifecycle-oriented, not per-request runtime |
| **ordinal** | Confirmed gap: MCP-Guard (nearest A→S contender) outputs binary; TraceSafe-Bench proves ordinal is superior |
| **agent-aware** | Confirmed gap: Microsoft AGT is agent-aware but not MCP-specific; academic systems are payload-only |
| **agent→server** | Confirmed gap: survey explicitly states no paper takes the server's vantage point |
| **MCP-scoped** | Partially challenged: MCP-in-SoS uses A→S threat model but static only; MCPShield Formal has MCP-native taxonomy |

**Net verdict:** the novelty claim holds. The new papers (MCP-in-SoS, MCPShield Formal, Microsoft
AGT) enrich the related-work section but each fails to satisfy the full four-qualifier combination
that MCP-RSS uniquely satisfies.

---

## 7. Net-New Papers to Prioritize for Full Review

Listed by expected thesis impact:

1. **MCPShield Formal** (arXiv 2604.05969) — must read; taxonomy overlap risk, covers 177k tools
2. **MCP-in-SoS** (arXiv 2603.10194) — must read; closest A→S static predecessor
3. **TraceSafe-Bench** (arXiv 2604.07223) — must read; empirical validation of ordinal scoring
4. **Guardrails as Infrastructure** (arXiv 2603.18059) — must read; quantifies threshold tradeoff
5. **CORTEX** (arXiv 2508.19281) — should read; 29-category empirical taxonomy is useful
6. **TOP-R** (arXiv 2512.16310) — should read; mosaic/chain risk empirical evidence
7. **Trinity Defense** (arXiv 2602.09947) — should read; (p)^n chain degradation model
8. **SEAgent** (arXiv 2601.11893) — should read; MAC + info flow graph for blast radius
9. **AgentGuard** (arXiv 2509.23864) — skim; MDP formula alternative
10. **KRI Framework** (arXiv 2603.12450) — skim; expected-loss framing for Lenovo audience

---

## 8. Recommended Actions

| Action | Priority | Where |
|--------|----------|-------|
| Add MCPShield Formal (2604.05969) to taxonomy comparison doc | High | risk-scoring-taxonomy-comparison.md |
| Add MCP-in-SoS (2603.10194) as static-mode precedent in related work | High | related_work_gap_matrix.md |
| Cite TraceSafe-Bench in motivation for ordinal scoring | High | thesis §2 |
| Quote Microsoft AGT and Compass survey gap statement as external validation | High | thesis §2–3 |
| Map project taxonomy against MCPShield Formal's 7-category/23-vector taxonomy | High | new doc or update mcp_server_attack_taxonomy_v2_agent_boundary.md |
| Use Guardrails as Infrastructure tradeoff data to frame threshold discussion | High | thesis §6 |
| Add TOP-R mosaic-effect evidence to session chain risk motivation | Medium | thesis §4 (dynamic scoring design) |
| Use Trinity Defense (p)^n model as chain-risk scoring formula component | Medium | thesis §4 |
| Update gap matrix with MCP-in-SoS (A→S column, static-only marker) | Medium | related_work_gap_matrix.md |
| Add CORTEX 29-category taxonomy to literature review for threat classification reference | Medium | Literature_review/ |

---

## References

- Compass survey source file: [`Literature_review/risk_scoring_frameworks_survey.md`](../../Literature_review/risk_scoring_frameworks_survey.md)
- Project gap matrix: [`Literature_review/related_work_gap_matrix.md`](../../Literature_review/related_work_gap_matrix.md)
- Risk scoring taxonomy comparison: [`docs/project/risk-scoring-taxonomy-comparison.md`](risk-scoring-taxonomy-comparison.md)
- Attack taxonomy v2: [`Literature_review/mcp_server_attack_taxonomy_v2_agent_boundary.md`](../../Literature_review/mcp_server_attack_taxonomy_v2_agent_boundary.md)
