# Thesis Research Plan — Dynamic Risk Scoring for MCP Agent Access

> Personal planning document for a 4th-year Data Science thesis.
> Created: 2026-03-29
> Based on: 62+ papers across 7 categories, 50 datasets, 24 benchmarks

---

## Problem Statement

The Model Context Protocol (MCP) allows AI agents to connect to third-party tool servers, but **there is no graduated, dynamic risk scoring system** for evaluating the severity of agent access requests. Every existing defense is binary:

- MCPShield (Zhou et al., 2026) outputs `trusted` / `untrusted` per server
- MCP-Guard (Xing et al., 2025) produces `attack` / `benign` classifications
- MCIP (Jing et al., 2025) does binary safety awareness + 11-class type ID, but no severity score
- Progent (Shi et al., 2025) enforces static privilege policies — allow or deny
- AgentBound (Buhler et al., 2025) generates permission manifests — binary compliance check

Meanwhile, real MCP interactions exist on a **spectrum of risk**. Reading a public weather API is not the same risk level as accessing a user's filesystem, which is not the same as executing arbitrary SQL. Every existing system treats these identically — either it's safe or it's not. No one produces a **graduated severity score** that helps operators make nuanced decisions.

**Why this matters:** As MCP adoption scales (67,057 servers across 6 registries per Li & Gao, 2025; 8,401 projects per Guo et al., 2025), organizations need a way to triage agent access requests — not just block or allow, but understand *how dangerous* a request is and *why*. The CVSS system does this for software vulnerabilities (0-10 scale). Nothing equivalent exists for MCP agent access.

---

## Key Insight / Novel Angle

**Adapt the CVSS vulnerability scoring methodology to MCP tool access requests, creating an "MCP-RSS" (MCP Risk Scoring System) that produces a dynamic 1-10 score.**

This is novel because:

1. **CVSS-to-MCP transfer has never been attempted.** "From Description to Score" (Jafarikhah et al., 2026) proved LLMs can score CVE descriptions with ~79% accuracy using text alone. MCP tool descriptions are structurally similar to CVE descriptions — they describe what a tool does, what it accesses, and what could go wrong. But nobody has connected these two domains.

2. **Dynamic scoring doesn't exist.** MCPShield introduced "adaptive trust calibration" and "periodic reasoning" — the closest to dynamic scoring — but it still outputs a binary decision. My system would output a numeric score that *changes over time* as the agent's behavior is observed.

3. **Multi-signal aggregation for MCP is unexplored.** Existing defenses use single-signal detection (pattern matching, or neural classification, or LLM judgment). "From Description to Score" showed that meta-classifiers combining multiple LLM outputs marginally improve accuracy. My system would aggregate multiple risk signals (tool metadata, access patterns, behavioral history, ecosystem baselines) into a composite score.

---

## Research Questions

### RQ1: Can LLMs produce accurate graduated risk scores for MCP tool access requests?
Inspired by "From Description to Score" showing LLMs achieve ~79% accuracy scoring CVEs from text. Can this transfer to MCP tool descriptions? What accuracy is achievable? Which LLMs perform best?

### RQ2: What are the right base metrics for an MCP risk scoring system?
CVSS has 8 base metrics (Attack Vector, Complexity, Privileges Required, etc.). What are the equivalent dimensions for MCP risk? This question produces the core contribution — a formal risk taxonomy.

### RQ3: Does multi-signal aggregation improve MCP risk scoring over single-signal approaches?
"From Description to Score" found meta-classifiers only marginally improved CVE scoring (+0.24% to +3.08%). Does the same hold for MCP, or does the richer context (tool metadata + behavioral signals + ecosystem data) enable larger gains?

### RQ4: How does dynamic temporal tracking affect risk scoring accuracy?
MCPShield showed temporal attacks (rug pulls) evade single-window detection. MCP-ITP showed implicit poisoning achieves 84.2% ASR with 0.3% detection. Can a score that evolves over time catch these patterns that static scoring misses?

### RQ5: What is the utility cost of graduated risk scoring?
Every defense paper reports a security-utility tradeoff (Progent: ASR 41.2%→2.2% but utility drops; MCIP: safety gains vs BFCL-v3 utility). Does a graduated 1-10 score preserve more utility than binary allow/deny, since operators can set their own thresholds?

---

## Methodology

### What to Build: MCP-RSS (MCP Risk Scoring System)

A Python system that takes an MCP tool invocation request and produces:
- A **risk score** from 1 (minimal risk) to 10 (critical risk)
- A **risk breakdown** showing sub-scores per dimension (like CVSS base metrics)
- A **confidence level** indicating how certain the score is
- A **justification** explaining why the score was assigned (explainability)

### Architecture (3-Stage Pipeline)

Inspired by MCP-Guard's cascaded approach (pattern→neural→LLM) and MCPShield's lifecycle model (pre→exec→post):

**Stage 1 — Static Risk Assessment (pre-invocation)**
- Analyze tool metadata: name, description, schema, required permissions
- Check against known attack patterns (MCLIB's 31-attack catalog)
- Compute base risk score from tool properties alone
- Fast, cheap, filters obvious high/low risk cases

**Stage 2 — Contextual Risk Enrichment (pre-invocation)**
- Factor in: which agent is requesting, what other tools are in the session, what data has been accessed
- Apply ecosystem baselines: is this tool's access pattern normal? (calibrated from 67K server dataset)
- Check for parasitic toolchain patterns (EIT/PAT/NAT combinations from "Mind Your Server")
- Adjust score based on agent capability level (Trust Paradox findings)

**Stage 3 — LLM-based Risk Judgment (pre-invocation, expensive path)**
- Only triggered when Stages 1-2 produce ambiguous scores (e.g., 4-7 range)
- LLM analyzes the full context: tool description + request parameters + session history
- Produces graduated score with justification
- Inspired by "From Description to Score" two-shot prompting approach

**Post-invocation Update (temporal tracking)**
- After tool execution, observe results and update the score
- Track score drift over multiple invocations (MCPShield's periodic reasoning, but numeric)
- Flag rug-pull patterns where score should increase over time

### Proposed MCP Risk Base Metrics (answering RQ2)

Adapted from CVSS v3.1 base metrics, informed by the literature. Refined through three iterations
(v1→v2→v3) to align with the server-defense framing: every dimension must answer **"How does this
agent threaten the server?"** See `dimension_refinement_v3_server_defense.md` for full specification.

#### Original 8 CVSS-Inspired Metrics (initial proposal)

| MCP Metric | Inspired By | What It Measures |
|---|---|---|
| **Access Scope** | CVSS Attack Vector | What resources can the tool reach? (network, filesystem, database, OS) |
| **Data Sensitivity** | CVSS Confidentiality Impact | How sensitive is the data the tool can access? (public, internal, PII, credentials) |
| **Action Reversibility** | CVSS Integrity Impact | Can the tool's actions be undone? (read-only, write, delete, execute) |
| **Privilege Level** | CVSS Privileges Required | What permissions does the tool need? (none, user-level, admin, root) |
| **Agent Trust** | Trust Paradox (Xu et al.) | How trusted is the requesting agent? (new, established, verified) |
| **Tool Provenance** | MCP ecosystem studies | Is the tool from a known/verified source? (official, community, unknown) |
| **Combination Risk** | Mind Your Server (Zhao et al.) | Does this tool + other session tools create dangerous combinations? |
| **Description Integrity** | MCP-ITP (Li et al.) | Does the tool description show signs of implicit poisoning? |

#### Current v3 Server-Defense Dimensions (6 + 1 modifier)

The 8 metrics above were refined into 6 server-defense dimensions + 1 modifier. Key changes:
- Access Scope + Action Reversibility + Data Sensitivity → absorbed into **Agent Action Severity**
- Tool Provenance + Description Integrity → absorbed into **Agent Compromise Indicator** (reframed: compromised agent = threat to server)
- Agent Trust → **Agent Trust Modifier** (demoted: agent properties ≠ request risk)
- NEW: **Resource Consumption Risk** (DoS/resource abuse — not in original proposal)

| # | v3 Dimension | Maps to Original Metric | Server's Question | Scale |
|---|---|---|---|---|
| 1 | **Agent Action Severity** | Access Scope + Action Reversibility + Data Sensitivity | How dangerous is this request to my resources? | 1-10 |
| 2 | **Permission Overreach** | Privilege Level | Is the agent requesting more access than needed? | 1-10 |
| 3 | **Data Exfiltration Risk** | Data Sensitivity (refocused on theft) | How much of my sensitive data is at risk? | 1-10 |
| 4 | **Cross-Tool Escalation** | Combination Risk | Is this session showing escalating threat patterns? | 1-10 |
| 5 | **Agent Compromise Indicator** | Tool Provenance + Description Integrity (reframed) | Is this agent acting under hostile influence? | 1-10 |
| 6 | **Resource Consumption Risk** | *(new — no original equivalent)* | Is this agent abusing my server resources? | 1-10 |
| Mod | **Agent Trust Modifier** | Agent Trust | How much should I trust this agent? | 0.7-1.4× |

Each dimension scored 1-10, weighted and combined into the composite score. The modifier adjusts the base score to produce the final risk score using a formula inspired by CVSS base score calculation.

### What Data to Use

**For training/calibration:**
- MCP-AttackBench: 70,448 labeled samples (attack/benign) — train the Stage 2 neural classifier
- MCIP Guardian Training Dataset: 13,830 instances across 10 risk types — train risk type classification
- NVD/CVE Database: 31,000+ entries with CVSS scores — pre-train the description-to-score approach
- glaive-function-calling-v2: 112,960 function calling instances — learn "normal" tool access patterns
- MCP Server Dataset (67,057 servers): calibrate ecosystem baselines for what's typical

**For evaluation:**
- MCPSecBench: 17 attack types across 4 surfaces — primary security benchmark
- MCPTox: 45 real-world servers, 353 tools, 3 attack paradigms — tool poisoning evaluation
- MCP-SafetyBench: 5 domains, 20 attack types, 13 LLMs — cross-domain generalization
- AgentDojo: 4 task suites, 97 user tasks, 629 injection tasks — standard agent security benchmark
- R-Judge: 569 records, 27 risk scenarios — risk awareness benchmark
- BFCL-v3: function calling accuracy — utility cost measurement
- Damn Vulnerable MCP Server: 10 intentionally vulnerable servers — controlled validation

**For testing implicit attacks specifically:**
- MCP-ITP Implicit Poisoning Data: the 0.3% detection baseline to beat
- Component-based Attack PoC Dataset: 132 servers, 12 categories

### How to Evaluate

1. **Scoring Accuracy:** Compare MCP-RSS scores against human expert ratings on a labeled dataset of MCP tool invocations (create this dataset as part of the thesis — ~500 tool invocations manually scored 1-10 by 2-3 annotators). Measure MAE, weighted F1, and rank correlation (Spearman's ρ).

2. **Detection Performance:** Run MCP-RSS against MCPSecBench, MCPTox, and MCP-SafetyBench attack scenarios. For each attack, check if MCP-RSS assigns a score ≥ threshold (e.g., ≥7). Compare detection rate against MCPShield (95.30%), MCP-Guard (95.4% F1), and mcp-scan (4/120 detection) baselines.

3. **Graduated Value:** Compare decision quality of:
   - Binary allow/deny (existing approach)
   - 3-tier (low/medium/high)
   - Full 1-10 scale (MCP-RSS)

   Does the 1-10 scale enable better operator decisions than binary? Measure using a simulated decision scenario with varied risk tolerance levels.

4. **Utility Preservation:** Run BFCL-v3 function calling benchmark with and without MCP-RSS. Measure how much accuracy degrades. Compare against Progent and MCIP's utility costs.

5. **Temporal Detection:** Test rug-pull and temporal drift attacks (from MCPShield's Rug Pull suite). Can MCP-RSS's temporal tracking detect score drift that static scoring misses?

6. **Implicit Attack Detection:** Test against MCP-ITP's implicit poisoning dataset. Can semantic analysis in Stage 3 beat the current 0.3% detection baseline?

---

## Phases & Milestones

### Phase 1: Foundation (Weeks 1-3)
- Define the formal MCP risk base metrics (the 8 dimensions above)
- Design the scoring formula (weighted combination → 1-10 score)
- Create the human-labeled evaluation dataset (~500 MCP tool invocations, manually scored)
- Set up the project infrastructure (Python, uv, testing framework)
- **Deliverable:** Formal risk taxonomy document + labeled dataset

### Phase 2: Static Scorer (Weeks 4-6)
- Implement Stage 1: pattern-based risk assessment from tool metadata
- Implement the base score calculation from the 8 metrics
- Test on the labeled dataset — establish baseline accuracy
- Compare against random baseline and majority-class baseline
- **Deliverable:** Working Stage 1 scorer with baseline metrics

### Phase 3: LLM-based Scorer (Weeks 7-9)
- Implement Stage 3: LLM-based risk judgment with few-shot prompting
- Replicate the "From Description to Score" approach but for MCP tool descriptions
- Test zero-shot, two-shot, five-shot prompting (Jafarikhah et al. found two-shot optimal)
- Evaluate with multiple LLMs (at minimum GPT-4o and one open model)
- **Deliverable:** LLM scoring pipeline with accuracy measurements

### Phase 4: Multi-signal Aggregation (Weeks 10-12)
- Implement Stage 2: contextual enrichment with ecosystem baselines
- Build the meta-classifier combining Stage 1 + Stage 2 + Stage 3 signals
- Train on MCP-AttackBench and MCIP training data
- Implement tool combination risk detection (parasitic toolchain patterns)
- **Deliverable:** Full 3-stage pipeline with multi-signal aggregation

### Phase 5: Temporal Tracking (Weeks 13-14)
- Add post-invocation score updates
- Implement temporal drift detection
- Test against rug-pull and temporal decoupling attacks
- **Deliverable:** Dynamic scoring with temporal evolution

### Phase 6: Evaluation & Writing (Weeks 15-18)
- Run full evaluation against all benchmarks (MCPSecBench, MCPTox, AgentDojo, etc.)
- Conduct the graduated-value comparison (binary vs 3-tier vs 1-10)
- Measure utility cost with BFCL-v3
- Write the thesis document
- **Deliverable:** Complete thesis

---

## Expected Contributions

### Primary Contribution
**MCP-RSS: The first graduated risk scoring system for MCP agent access.** A formal framework that produces a 1-10 severity score (not binary) for MCP tool invocation requests, with sub-scores per risk dimension, confidence levels, and justifications.

### Secondary Contributions
1. **MCP Risk Taxonomy:** A formal set of base metrics for MCP risk assessment (the 8 dimensions), analogous to CVSS base metrics for vulnerability scoring. This taxonomy can be reused by other researchers.

2. **CVSS-to-MCP Transfer Study:** Empirical evidence on whether the "description to score" approach from vulnerability scoring transfers to MCP tool descriptions. This validates (or refutes) a cross-domain transfer that nobody has tested.

3. **Multi-signal Aggregation Results:** Empirical data on whether combining tool metadata + behavioral signals + LLM judgment + ecosystem baselines produces meaningfully better risk scoring than single-signal approaches.

4. **Graduated vs Binary Comparison:** The first empirical comparison of graduated (1-10) vs binary (allow/deny) risk assessment for MCP, measuring whether the additional granularity actually helps operator decision-making.

5. **Human-labeled MCP Risk Dataset:** A publicly available dataset of ~500 MCP tool invocations with human-assigned risk scores (1-10), which doesn't currently exist and would be useful for future research.

---

## Literature References

### Core inspirations (what this thesis builds on directly):

- **"From Description to Score" (Jafarikhah et al., 2026)** — Proved LLMs can score CVE severity from text descriptions at ~79% accuracy with two-shot prompting. GPT-5 was best. Meta-classifiers combining 6 LLMs gave only marginal improvement (+0.24% to +3.08%), suggesting the bottleneck is description quality, not classifier architecture. **My thesis adapts this exact methodology from CVEs to MCP tool descriptions — nobody has tried this transfer.**

- **MCPShield (Zhou et al., 2026)** — The closest existing work to what I'm building. Introduces lifecycle-wide defense (pre-invocation probing, execution isolation, post-invocation periodic reasoning) and "adaptive trust calibration." Achieves 95.30% defense rate vs 10.05% baseline across 76 malicious servers. **But it outputs binary trusted/untrusted, not a graduated score. My thesis turns this into a 1-10 numeric system.**

- **CVSS v3.1 (FIRST.org)** — The gold standard for vulnerability severity scoring. 8 base metrics, weighted formula, 0-10 scale. Universally adopted. **My thesis creates the MCP equivalent — same idea, different domain.**

### Attack landscape (what the scorer must detect):

- **"When MCP Servers Attack" (Zhao et al., 2025)** — Taxonomy of 12 attack categories (A1-A12), tested with 132 servers across 5 LLMs. Found mcp-scan detects only 4/120 poisoned servers. **Their 12-category taxonomy directly informs my risk type classification.**

- **MCPTox (Wang et al., 2025)** — 3 attack paradigms on real-world MCP servers. Overall 72.8% ASR. Implicit attacks are hardest to detect. **Essential evaluation benchmark for testing whether my scorer catches tool poisoning.**

- **MCP-ITP (Li et al., 2026)** — Showed implicit tool poisoning achieves 84.2% ASR with only 0.3% detection rate by existing tools. Individual words in descriptions can steer agent behavior. **This is the hardest challenge for my scorer — can semantic analysis beat 0.3%?**

- **"Breaking the Protocol" (Maloyan & Namiot, 2026)** — Quantified that MCP amplifies prompt injection by +23-41% vs non-MCP baselines. Three injection layers (resource content, tool response, sampling). AttestMCP defense reduces ASR from 52.8% to 12.4%. **The amplification factor should increase risk scores for protocol-level vectors.**

- **"Mind Your Server" (Zhao et al., 2025)** — Identified parasitic toolchain attacks. 27.2% of servers expose exploitable tool combinations. EIT/PAT/NAT tool classification. 90% attack success across 10 real toolchains. **Directly informs the "Combination Risk" metric in my scoring system.**

- **"Log-To-Leak" (Hu et al., 2026)** — Showed benign infrastructure tools (logging, monitoring) can be weaponized for covert data exfiltration while preserving task quality. **Proves the scorer can't rely on output quality as a safety signal, and must evaluate tool combinations.**

### Trust and access control (informing the scoring dimensions):

- **Progent (Shi et al., 2025)** — Programmable privilege control for LLM agents. Reduced ASR from 41.2% to 2.2% on AgentDojo. **Shows that fine-grained access control works, but Progent uses static policies. My system adds graduated scoring on top.**

- **"Trust Paradox" (Xu et al., 2025)** — Empirically validated that more capable agents are more vulnerable (TCI 0.72-0.89). Trust stabilizes after 8-15 iterations. **Directly informs the "Agent Trust" metric — capability ≠ trustworthiness.**

- **GuardAgent (Xiang et al., 2024)** — Guard agent with role-based access control. >98% accuracy on healthcare scenarios. **Shows attribute-based risk assessment works. My system uses this for context-dependent scoring.**

- **"Towards Automating Data Access Permissions" (Wu et al., 2025)** — Automated permission generation for AI agents. **Informs how my system evaluates privilege escalation risk.**

### Risk scoring and anomaly detection (methodological inspiration):

- **TRiSM for Agentic AI (Raza et al., 2025)** — Survey of Trust, Risk, and Security Management for agentic multi-agent systems. Identifies Gartner's TRiSM framework as applicable to AI agents. **Provides the theoretical framework for my risk scoring approach.**

- **R-Judge (Yuan et al., 2024)** — Benchmark for safety risk awareness. 569 records, 27 scenarios, 10 risk types. Best model (GPT-4o) only achieves 74.42%, most near random. **Shows how hard risk assessment is — my system needs to beat 74.42% on risk-type identification.**

- **TraceAegis (Chen et al., 2025)** — Hierarchical and behavioral anomaly detection for LLM agents. **Informs the temporal tracking component of my scorer.**

- **SentinelAgent (He et al., 2025)** — Graph-based anomaly detection in multi-agent systems. **Informs how to model tool interaction patterns for the combination risk metric.**

- **ToolSafe (Mou et al., 2026)** — Step-level proactive guardrails with feedback. **Shows value of per-step risk assessment rather than once-per-session.**

### Defense frameworks (architectural inspiration):

- **MCP-Guard (Xing et al., 2025)** — Three-stage cascade: pattern matching (38.9% filter, <2ms) → neural detection (96.01% F1) → LLM arbitration. 95.4% F1 overall. **My 3-stage architecture is directly inspired by this, but outputs a score instead of binary.**

- **LlamaFirewall (Meta, 2025)** — Open-source guardrail system. PromptGuard + AlignmentCheck pipeline. 600-scenario benchmark. **Provides a deployment model for how risk scoring integrates into agent systems.**

- **NeMo Guardrails (Rebedea et al., 2023)** — Programmable safety rails. **Background on how guardrail systems work in practice.**

### Ecosystem data (calibration and baselines):

- **"Toward Understanding Security Issues in MCP" (Li & Gao, 2025)** — 67,057 servers, 44,499 Python tools. Tool confusion 20-100% success, tool shadowing 40-100%, credential leakage in multiple registries. **Provides ecosystem baseline data for calibrating what "normal" looks like.**

- **"MCP at First Glance" (Hasan et al., 2025)** — 1,899 repos analyzed with SonarQube. Vulnerability patterns and code quality metrics. **Server quality metrics as proxy signals for tool provenance scoring.**

- **"Privilege Management in MCP" (Li et al., 2025)** — 2,117 repos showing widespread over-privilege. **Justifies the "Privilege Level" metric and default-deny bias in scoring.**

- **MCP Landscape (Hou et al., 2025)** — First comprehensive MCP landscape survey. 1,899 repos across 6 registries. **The foundational reference for understanding the MCP ecosystem.**

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Human labeling of 500 tool invocations is too slow | Start with 200 high-confidence cases, expand if time allows. Use inter-annotator agreement to validate quality over quantity. |
| LLM API costs for Stage 3 evaluation | Use GPT-4o-mini for development, full models only for final evaluation. Budget ~$50-100 for API calls. |
| "From Description to Score" approach may not transfer to MCP | This is itself a finding worth reporting (negative results are valuable). Fall back to training a dedicated classifier on MCP-specific data. |
| Graduated scoring may not outperform binary | Again, a valid finding. Report the comparison honestly. |
| Implicit poisoning detection may remain near-zero | Focus on showing improvement over 0.3% baseline, even if absolute detection is still low. Frame as "the hard problem" for future work. |

---

## What This Plan Does NOT Cover

- **Deployment/production system:** This is research, not a product. The scorer is a prototype.
- **Multi-agent scenarios:** Focus is on single agent ↔ single server interactions. Multi-agent chains are future work.
- **Training custom LLMs:** Using existing LLMs via API, not fine-tuning. Fine-tuning is future work.
- **Formal verification:** The scoring system is empirical, not provably correct.
- **Real-time performance optimization:** Correctness first, speed second.
