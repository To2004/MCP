# Risk Scoring Frameworks for Autonomous AI Agent Systems

**No single paper yet proposes the exact "MCP Security" concept—a server-side, continuous risk score combining static tool properties with dynamic request context to gate agent invocations—but more than 40 academic papers and industry frameworks collectively provide the theoretical foundations, scoring methodologies, and architectural patterns to build it.** The field is nascent and fast-moving: the vast majority of relevant work appeared between January 2025 and April 2026, with several papers specifically addressing MCP protocol security emerging in early 2026. The most important gap is directional—most academic work protects the *agent* from malicious servers/tools, not the *server* from risky agent requests—though several industry implementations (Microsoft Agent Governance Toolkit, Traceable AI, Google Apigee) already implement graded scoring on the server/gateway side.

---

## Papers that directly address graded risk scoring for agent tool calls

The closest academic work to the envisioned framework falls into three clusters: vulnerability scoring systems, step-level guardrails, and formal risk estimation.

**OWASP AIVSS (Agentic AI Vulnerability Scoring System, v0.5, 2025)** by Ken Huang, Michael Bargury, et al. is the most mathematically developed scoring framework. It extends CVSS v4.0 with **10 Agentic AI Risk Amplification Factors (AARFs)**—Autonomy of Action, Tool Use, Memory Use, Dynamic Identity, Multi-Agent Interactions, Non-Determinism, Self-Modification, Goal-Driven Planning, Contextual Awareness, and Opacity & Reflexivity—each scored on a 0.0/0.5/1.0 scale. The composite formula is `AIVSS_Score = ((CVSS_Base_Score + AARS) / 2) × ThM`, where AARS is the sum of factor scores (range 0–10) and ThM is a threat multiplier. This produces a continuous 0–10 score. The system ranks "Agentic AI Tool Misuse" at **AIVSS 8.7** and "Agent Access Control Violation" at **8.2**. While designed for vulnerability assessment rather than per-request runtime scoring, AIVSS provides the most rigorous mathematical foundation for graded agentic risk scoring available today.

**ToolSafe** (Mou et al., arXiv 2601.10156, Peking University / Shanghai AI Lab, 2026) introduces TS-Guard, a guardrail using **multi-task reinforcement learning** that evaluates each tool invocation *before* execution by reasoning over the full interaction history. It assesses request harmfulness and action–attack correlations, producing interpretable safety judgments—not binary labels. The companion TS-Flow framework feeds these judgments back to the agent, reducing harmful tool invocations by **65%** while improving benign task completion by ~10%. This is the closest published system to runtime, per-invocation risk scoring with graduated enforcement.

**SafePred** (Chen et al., 2026, referenced in the predictive guardrails literature) directly produces **scalar risk scores** per agent action using a world model bound to real or automatically extracted policies. Only actions where `risk(a) ≤ threshold T` are retained for execution, implementing a clean risk-to-decision gating loop. The threshold is configurable, enabling operators to tune the tradeoff between safety and task completion—precisely the gating/throttling concept described in the MCP Security framework.

**TraceSafe-Bench** (arXiv 2604.07223, 2026) provides critical empirical evidence: across 13 LLMs and 7 specialized guards, **granular risk taxonomies consistently outperform binary safe/unsafe classification** for multi-step tool-calling trajectories. This validates the fundamental premise that continuous/graded scoring is superior to binary detection for agent security.

**R-Judge** (Yuan et al., EMNLP 2024 Findings, arXiv 2401.10019) benchmarks LLMs' ability to judge safety risks from agent interaction records across 569 records, 27 risk scenarios, and 10 risk types. The best model (GPT-4o) achieves only **74.42%** accuracy—well below human level—demonstrating that risk-aware scoring of agent actions remains an unsolved challenge requiring sophisticated reasoning, not simple pattern matching.

---

## MCP-specific security research has exploded since early 2026

Three papers directly address Model Context Protocol security with quantitative risk assessment.

**MCPShield** (Zhou et al., arXiv 2602.14281, February 2026) is the most directly relevant architecture. It implements a **plug-in security cognition layer** mediating between agents and MCP servers across three lifecycle stages: pre-invocation (metadata-guided probing verifies consistency between declared and actual server capabilities), execution (monitors runtime behaviors to detect out-of-bounds requests), and post-invocation (evaluates long-term behavioral consistency and updates trust scores). The system forms an "adaptive trust calibration" that accumulates lifecycle evidence. While designed to protect the *agent* from untrusted servers, the architecture—lifecycle-wide trust assessment with continuously evolving scores—is directly transferable to server-side risk scoring. An extended formal version (arXiv 2604.05969, April 2026) adds **labeled transition systems with trust-boundary annotations**, defines four verifiable security properties (tool integrity, data confinement, privilege boundedness, context isolation), and constructs a unified threat taxonomy covering **7 categories, 23 attack vectors, and 4 attack surfaces** from analysis of 177,000+ MCP tools. Comparative evaluation shows no existing defense mechanism covers more than **34%** of the threat landscape.

**MCP-in-SoS** (Kumar et al., arXiv 2603.10194, March 2026) takes the exact threat model described in the query—server as protected asset, client as untrusted requester. It implements a four-stage automated pipeline: static code analysis, metadata preparation against MITRE CWE/CAPEC databases, normalization, and **risk scoring** that assigns each observed CWE a Risk Index and derives per-repository severity profiles. This is purely static/design-time scoring of server implementations rather than runtime request-level scoring, but it directly addresses the static risk dimension.

**Security Threat Modeling for AI Agent Protocols** (arXiv 2602.11327, February 2026) provides a lifecycle-aware framework evaluating security posture across creation, operation, and update phases for MCP, A2A, ANP, and Agora protocols, identifying **12 protocol-level risks** with measurement-driven case studies.

---

## Runtime risk estimation approaches span probabilistic, policy-based, and ML-driven methods

The dynamic scoring dimension draws from several distinct methodological traditions.

**AURA (Agent Autonomy Risk Assessment Framework)** (arXiv 2510.15739, 2025) introduces a **gamma-based risk scoring methodology** balancing assessment accuracy with computational efficiency. It is fully modular—dimensions, contexts, weights, scores, memory, human-in-the-loop thresholds, and mitigations can all be adjusted at runtime as workloads or risk appetite shift. AURA supports per-action risk evaluation with configurable escalation thresholds and is engineered for progressive autonomy scaling.

**AgentGuard** (arXiv 2509.23864, 2025) implements **Dynamic Probabilistic Assurance**: an inspection layer that observes agent I/O, abstracts it into formal events corresponding to transitions in a state model, and uses **online learning to dynamically build and update a Markov Decision Process (MDP)** modeling emergent agent behavior. Rather than asking "if" a system will fail, it continuously estimates the probability of failure within given constraints. This is the most theoretically grounded approach to runtime behavioral risk estimation.

**CORTEX** (Muhammad et al., arXiv 2508.19281, 2025) proposes a five-tier hybrid model combining deterministic scoring with probabilistic modeling: utility-adjusted Likelihood × Impact calculations, governance overlays aligned with EU AI Act and NIST RMF, technical surface scores covering drift and adversarial risk, environmental modifiers, and **Bayesian risk aggregation with Monte Carlo simulation**. Its 29-category vulnerability taxonomy derived from 1,200+ incidents in the AIID provides the most empirically grounded risk categorization.

**The MAESTRO/ATFAA scoring model** (arXiv 2504.19956, 2508.10043) uses a clean multiplicative formula: **R = P × I × E** (Likelihood × Impact × Exploitability), with all three dimensions assessed on ordinal scales via qualitative evaluations. This simple model appears across multiple frameworks and provides a practical starting point for combining static and dynamic factors.

**Governance-as-a-Service (GaaS)** (Gaurav et al., arXiv 2508.18765, 2025) implements the exact orchestration-layer pattern: a non-invasive runtime proxy that intercepts agent actions, scores them using a **severity-weighted penalty framework** producing quantitative trust scores per agent output, and makes gate/throttle/deny decisions. Domain-adaptive precision means the system adjusts scoring behavior by application context.

The **Guardrails as Infrastructure** paper (arXiv 2603.18059, 2026) presents "Policy-First Tooling" with a compact **policy DSL** supporting tool-level, group-level, and capability-level gating; argument constraints (regex, range, enum, path containment); cross-field invariants; rate limits; and approval requirements for high-risk actions. In 225 controlled runs, stricter policy packs improved violation prevention from 0.000 (P0) to **0.681 (P4)**, though task success dropped from 0.356 to 0.067—quantifying the fundamental safety-capability tradeoff.

---

## Trust boundaries, blast radius, and the confused deputy problem in agent systems

Several papers provide the conceptual foundations for static risk scoring based on trust boundary crossing and potential blast radius.

**SEAgent** (Ji et al., arXiv 2601.11893, HKUST/ETH Zurich, 2025) proposes a **mandatory access control (MAC) framework** built on attribute-based access control for LLM agents. It identifies five distinct privilege escalation vectors—direct prompt injection, indirect prompt injection, RAG poisoning, untrusted agent insertion, and the **confused deputy attack** in multi-agent systems. SEAgent monitors agent-tool interactions via an **information flow graph** and achieves a 0% attack success rate across all benchmarked vectors. The information flow graph approach directly supports blast radius estimation.

**"Trustworthy Agentic AI Requires Deterministic Architectural Boundaries"** (arXiv 2602.09947, 2025) proposes the **Trinity Defense** (Action Governance, Information-Flow Control, Privilege Separation) and formalizes blast radius propagation: if each agent in a chain is 94.3% accurate, the chain's accuracy degrades as **(0.943)^n**, meaning a 5-agent chain drops to ~74% accuracy. This cascading degradation model provides a mathematical basis for scoring multi-step action chains.

The **FINOS AI Governance Framework (AIR-OP-028)** from the financial services sector catalogs five trust boundary violation mechanisms (agent-to-agent communication compromise, shared resource contamination, authority impersonation, cross-agent privilege inheritance, cascade failure propagation) and four attack propagation patterns (horizontal, vertical escalation, hub-and-spoke, chain reaction). This is the most detailed taxonomy of trust boundary violations and propagation patterns directly applicable to blast radius modeling.

**Repello AI's blast radius model** identifies four measurable dimensions: what data the model can access, what actions it can execute, what downstream systems receive its outputs, and what persistence mechanisms exist. Their key insight: **persistence mechanisms are the least-understood blast radius factor**—they determine whether blast radius is session-scoped or open-ended.

**TOP-R (Tool Orchestration Privacy Risk)** (arXiv 2512.16310, 2025) identifies a critical compositional risk: individually authorized, low-risk tool calls can compose into high-risk information synthesis through the **"mosaic effect."** This demonstrates that per-invocation risk scoring alone is insufficient—sequential/compositional risk across tool call chains must also be scored.

---

## Industry implementations already deploy graded runtime scoring

The **Microsoft Agent Governance Toolkit** (open-sourced April 2026) is the most mature production implementation. Its Agent Mesh component implements **dynamic trust scoring on a 0–1000 scale with five behavioral tiers** and behavioral decay—trust degrades over time without positive signals. The Agent OS provides a stateless policy engine intercepting every action at **<0.1ms p99** latency, supporting YAML rules, OPA Rego, and Cedar policies. The developers explicitly stated: *"A binary trusted/untrusted model doesn't capture reality. Trust scoring with behavioral decay and dynamic privilege assignment turned out to be a much better model."*

**Traceable AI** implements a continuous **0–10 risk score** per API endpoint as a function of Likelihood (API access type, vulnerabilities, ease of discovery) and Impact (data sensitivity, spatial impact/API dependencies, custom labels). The "spatial impact" factor—measuring the number of downstream API dependencies—is essentially blast radius analysis for API calls.

**Google Cloud Apigee** uses three-dimensional scoring: source assessment (detected abuse traffic), proxy assessment (security policy implementation), and target assessment (backend security configuration), continuously updated over time windows.

**Microsoft Defender for Copilot Studio** (January 2026) implements runtime risk-based gating at the tool invocation layer, treating every tool invocation as a "high-value, high-risk event" with security checks before execution. **AWS AI Risk Intelligence (AIRI)** automates security and governance control assessments across the entire agentic lifecycle. **Anthropic's Trustworthy Agents Framework** (updated April 2026) deploys graduated permissions (always allow / needs approval / block) per tool action.

The **Cloud Security Alliance's Agentic Trust Framework (ATF)** (February 2026) applies Zero Trust principles (NIST 800-207) with **four maturity levels** requiring progressively demonstrated trustworthiness before greater autonomy is granted, circuit breakers for cascading failure prevention, and policy-as-code enforcement.

---

## Synthesis and the path forward for MCP Security scoring

The literature converges on a composite scoring architecture that the MCP Security framework should integrate:

- **Static risk factors** (design-time): tool permission scope (SEAgent ABAC labels), API exposure level (Traceable AI), data sensitivity classification (OWASP AIVSS Tool Use factor), CWE risk indices from code analysis (MCP-in-SoS), downstream dependency count as blast radius proxy (Traceable spatial impact), and reversibility of effects (Repello AI persistence dimension)
- **Dynamic risk factors** (runtime): behavioral anomaly signals (Microsoft AGT behavioral decay), request sequence analysis and cascading risk estimation using (0.943)^n degradation models (Trinity Defense), compositional mosaic risk across tool call chains (TOP-R), MDP-based probability-of-failure estimation from online learning (AgentGuard), and step-level safety judgments from multi-task RL (ToolSafe)
- **Scoring formula candidates**: The MAESTRO `R = P × I × E` provides the simplest viable formula; OWASP AIVSS provides the most comprehensive `((CVSS + AARS) / 2) × ThM`; CORTEX offers the most statistically rigorous Bayesian aggregation with Monte Carlo simulation; and Microsoft AGT's 0–1000 scale with behavioral decay provides the most production-tested continuous scoring approach

Three critical research gaps remain. First, **no published work implements the exact server-side perspective**—computing a continuous risk score for each incoming agent tool call from the server's vantage point; most work takes the agent's perspective. Second, **compositional/sequential risk scoring** across multi-step tool call chains remains largely theoretical despite being identified as essential by multiple papers. Third, **the fundamental tradeoff between safety and capability** is poorly characterized: the Guardrails as Infrastructure paper's finding that stricter policies reduce violations from 0% to 68% but also reduce task success from 36% to 7% underscores that calibrating the scoring threshold is itself an open research problem.

---

## Consolidated reference table

| Paper/Framework | Authors/Org | Year | Venue | Scoring Method | Static/Dynamic | ArXiv ID |
|---|---|---|---|---|---|---|
| OWASP AIVSS v0.5 | Huang, Bargury et al. | 2025 | OWASP | CVSS + 10 AARFs → 0–10 score | Static | — |
| MCPShield | Zhou et al. | 2026 | arXiv | Adaptive trust calibration, lifecycle-wide | Both | 2602.14281 |
| MCP-in-SoS | Kumar et al. | 2026 | arXiv | CWE Risk Index + frequency scoring | Static | 2603.10194 |
| MCPShield (Formal) | Extended team | 2026 | arXiv | Labeled transition systems, trust annotations | Static | 2604.05969 |
| ToolSafe | Mou et al. | 2026 | arXiv | Multi-task RL step-level safety scores | Dynamic | 2601.10156 |
| SafePred | Chen et al. | 2026 | arXiv | World-model scalar risk, threshold gating | Dynamic | — |
| TraceSafe-Bench | — | 2026 | arXiv | Granular risk taxonomies > binary | Dynamic | 2604.07223 |
| R-Judge | Yuan et al. | 2024 | EMNLP | Benchmark: multi-turn risk awareness | Dynamic | 2401.10019 |
| AURA | — | 2025 | arXiv | Gamma-based continuous scoring | Both | 2510.15739 |
| AgentGuard | — | 2025 | arXiv | Online MDP, probabilistic assurance | Dynamic | 2509.23864 |
| CORTEX | Muhammad et al. | 2025 | arXiv | 5-tier Bayesian + Monte Carlo | Both | 2508.19281 |
| MAESTRO/ATFAA | Narajala et al. | 2025 | arXiv | R = P × I × E | Static | 2504.19956, 2508.10043 |
| GaaS | Gaurav et al. | 2025 | arXiv | Severity-weighted penalty, trust scores | Dynamic | 2508.18765 |
| Guardrails as Infrastructure | — | 2026 | arXiv | Policy DSL, risk-aware gating | Both | 2603.18059 |
| AgenTRIM | — | 2026 | arXiv | Per-step adaptive filtering | Dynamic | 2601.12449 |
| AgentSpec | Wang et al. | 2026 | ICSE 2026 | DSL triggers + graduated enforcement | Dynamic | 2503.18666 |
| TRiSM for Agentic AI | Raza et al. | 2025 | arXiv/NeurIPS | CSS + TUE metrics, trust score decay | Both | 2506.04133 |
| ASTRA | — | 2025 | arXiv | Application-context risk assessment | Both | 2511.18114 |
| SEAgent | Ji et al. | 2025 | arXiv | MAC/ABAC + info flow graph | Static | 2601.11893 |
| Policy Compiler | — | 2026 | arXiv | Formal policy verification | Static | 2602.16708 |
| Permission Risk Scoring | Mahara | 2025 | arXiv | LLM-based API permission tiering | Static | 2512.15781 |
| Formalizing LLM Agent Security | — | 2026 | arXiv | Oracle functions for security properties | Both | 2603.19469 |
| AgentSentinel | — | 2025 | arXiv | Rule + AI dual auditor, pre-exec gating | Dynamic | 2509.07764 |
| TrustBench | — | 2026 | arXiv | Real-time inline trust verification | Dynamic | 2603.09157 |
| TOP-R | — | 2025 | arXiv | Mosaic/compositional tool orchestration risk | Dynamic | 2512.16310 |
| ToolEmu | Ruan et al. | 2023 | arXiv | LM-emulated sandbox risk quantification | Static | 2309.15817 |
| Trinity Defense | — | 2025 | arXiv | Cascading (p)^n degradation model | Static | 2602.09947 |
| Threat Model for Agent Protocols | — | 2026 | arXiv | 12 protocol-level risks, lifecycle-aware | Static | 2602.11327 |
| NVIDIA ARP Framework | NVIDIA | 2025 | arXiv | Graph-based ARP risk decomposition | Both | 2511.21990 |
| Risk Analysis Multi-Agent | — | 2025 | arXiv | Cascading error propagation | Dynamic | 2508.05687 |
| Quantitative Security Benchmarking MAS | — | 2025 | arXiv | Formal trust relations T ⊆ A×A | Both | 2507.21146 |
| ConfusedPilot | RoyChowdhury et al. | 2024 | arXiv | Confused deputy in RAG systems | — | 2408.04870 |
| KRI Framework | Sherif et al. | 2026 | arXiv | Expected-loss KRI, ROC-AUC 0.927 | Both | 2603.12450 |
| Zero Trust Identity for Agents | Huang et al. | 2025 | arXiv | DIDs + VCs + ZKPs | Dynamic | 2505.19301 |
| MS Agent Governance Toolkit | Microsoft | 2026 | GitHub | 0–1000 trust score, 5 tiers, behavioral decay | Dynamic | — |
| CSA Agentic Trust Framework | CSA/Woodruff | 2026 | CSA | 4 maturity levels, circuit breakers | Both | — |
| Traceable AI | Traceable | 2025 | Commercial | Likelihood × Impact → 0–10 per endpoint | Both | — |
| Google Apigee | Google | 2025 | Commercial | 3-axis scoring (source/proxy/target) | Both | — |
| Anthropic Trustworthy Agents | Anthropic | 2025–26 | Whitepaper | Graduated permissions per tool action | Static | — |
| OWASP Cheat Sheet | OWASP | 2026 | OWASP | LOW/MEDIUM/HIGH/CRITICAL risk levels | Static | — |
| FINOS AIR-OP-028 | FINOS | 2025 | FINOS | 5 violation types, 4 propagation patterns | Static | — |
| Repello AI Blast Radius | Repello AI | 2025 | Industry | 4-factor blast radius model | Static | — |
| Adversa AI MCP Top 25 | Adversa AI | 2025 | Industry | Impact 40%/Exploit 30%/Prevalence 20%/Remediation 10% | Static | — |
| Databricks DASF v3.0 | Databricks | 2025 | Industry | 97 risks, 73 controls | Both | — |
