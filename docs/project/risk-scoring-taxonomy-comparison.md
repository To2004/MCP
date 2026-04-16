# Risk Scoring for Tool Invocation: Taxonomy Comparison

A structured comparison of academic approaches to risk scoring, threat taxonomy, and
tool-invocation safety — evaluated against the MCP server risk scoring framework.

---

## Your Project in One Paragraph

The MCP risk scoring framework treats the **MCP server as the protected asset** and
**AI agents as the threat source**. Incoming agent tool-call requests are scored in two
modes: **static** (design-time, based on what a tool can do) and **dynamic** (runtime,
based on the specific call, arguments, and session context). The score gates, throttles,
or denies the call before execution. The core insight is that agentic threats are
structurally different from human-driven threats: they are high-frequency, context-aware,
chained across sessions, and exploit trust boundaries that traditional API gateways were
not designed to handle.

---

## 1. ToolSafe — Step-Level Tool Invocation Safety

**Paper:** Mou et al., arXiv:2601.10156, Jan 2026 (Peking University)

### Taxonomy

ToolSafe identifies **four unsafe patterns** characterising tool invocations:

| Pattern | Code | Description |
|---------|------|-------------|
| Malicious User Request | **MUR** | Agent's upstream user request is inherently harmful |
| Prompt Injection | **PI** | Third-party attack embedded in tool-returned data redirects agent |
| Harmful Tools | **HT** | The tool itself is explicitly dangerous (no benign use) |
| Benign Tools with Risky Arguments | **BTRA** | Legitimate tool called with arguments that make it destructive |

### Scoring Methodology

Each step is classified into three classes: `{safe, controversial, unsafe}`.
The guardrail model decomposes the decision into three sub-tasks inferred jointly:

```
P(y_t, h_t, v_t | a_t, H_t, u) = f_guard(a_t, H_t, u)
```

Where:
- `a_t` = candidate tool invocation action at step t
- `H_t` = full interaction history up to step t
- `u` = original user request
- `h_t` = predicted harmfulness label
- `v_t` = predicted prompt-injection link
- `y_t` = final safety label

The model is trained with multi-task GRPO reward:
`r_t = 1 - w1·𝟙[h_t ≠ ĥ_t] - w2·𝟙[v_t ≠ v̂_t] - w3·𝟙[y_t ≠ ŷ_t]`

### Comparison to Your Idea

| Dimension | ToolSafe | Your Project |
|-----------|----------|--------------|
| Protected asset | Agent (prevent agent from doing harm) | MCP server (protect server from agent) |
| Threat source | Malicious users + injected external data | Agents as the primary threat |
| Scoring granularity | Step-level (pre-execution) | Request-level (per tool call) |
| Static scoring | No — all runtime | Yes — design-time tool risk profiling |
| Dynamic scoring | Yes — per step with history | Yes — per call with session context |
| MCP-specific | No — generic tool agents | Yes |
| Output | 3-class label + feedback to agent | Numeric score → gate/throttle/deny |
| Feedback loop | Yes (TS-Flow feeds back to agent) | Not in scope |

**Key takeaway:** ToolSafe is the closest paper in granularity. Its BTRA pattern is
especially important — your static score alone cannot catch a safe tool being weaponised
by risky arguments; your dynamic scoring must account for this. The MTO
(Motivation–Trigger–Outcome) schema used in TS-Bench for annotation directly maps to
the dimensions you need in your feature space.

---

## 2. MCPShield — Lifecycle Security Cognition for MCP

**Paper:** Zhou et al., arXiv:2602.14281, Feb 2026 (ICML 2026 submission)

### Architecture (3-Stage Lifecycle)

MCPShield is the most architecturally aligned paper to your project. It treats tool
invocation as a three-phase lifecycle and defends each phase:

| Phase | Mechanism | What it does |
|-------|-----------|--------------|
| **Pre-Invocation** | Security Cognitive Probing | Generates mock calls; scores declared vs. actual behaviour |
| **Execution** | Isolated Projection | Constrains side-effects to authorised scope; records kernel traces |
| **Post-Invocation** | Periodic Reasoning | Temporal drift detection over accumulated invocation history |

### Scoring Formula

The Security Cognitive Probing phase produces a **deny score**:

```
S_deny(T) = (1/N) · Σ_{T_i ∈ T} Σ_{k=1}^{M_i} 𝟙[s(d_i, C_k^p) ∈ {deny}]
```

Where `T` is the set of tools, `M_i` is the number of mock probes, and `s()` is an
LLM-based safety verdict. If `S_deny(T)` exceeds a threshold, the server is rejected
before any real calls are made.

### Threat Model (3 Misalignment Types)

| Misalignment | Description |
|-------------|-------------|
| **Semantic** | Declared metadata `d` describes a safe tool but actual behaviour is harmful |
| **Observational** | Visible return `y_t` is benign but execution trajectory `τ_t` has side effects |
| **Temporal** | Agent appears safe in early invocations but drifts malicious over time |

### Comparison to Your Idea

| Dimension | MCPShield | Your Project |
|-----------|-----------|--------------|
| Threat direction | Malicious MCP server attacking agent | Malicious agent attacking MCP server |
| Scoring approach | Mock-probe deny rate (LLM-judged) | Multi-factor numeric score |
| Static component | Security Cognitive Probing (pre-invocation) | Design-time static score |
| Dynamic component | Execution + Periodic Reasoning | Runtime dynamic score |
| Persistence | Security cognition across invocations | Session/context risk accumulation |
| MCP-specific | Yes | Yes |
| Output | Binary trusted/untrusted per server | Numeric risk score per request |

**Key takeaway:** MCPShield defends **agents FROM servers** — the exact inverse of your
threat model. However, its three-phase lifecycle and temporal misalignment detection
are directly applicable to the dynamic scoring mode: a server should track accumulated
request patterns across a session, not just score individual calls in isolation.
The deny-score formula is a concrete design pattern you can adapt.

---

## 3. MCP-Guard — Multi-Stage Detection Pipeline

**Paper:** Xing et al., arXiv:2508.10991, Aug 2025

### 3-Stage Pipeline and 11 Attack Categories

**Stage I — Syntactic Filtering (Static)**
- Rule-based regex for overt patterns
- Filters ~38.9% of threats in ~1.8 ms
- Targets: SQL injection, shell commands, sensitive paths

**Stage II — Semantic Neural Detection (Dynamic)**
- Fine-tuned Multilingual E5 model
- Output: malicious probability P(y|x) ∈ [0, 1]
- Routes cases where 0.45 < P(y|x) < 0.55 to Stage III
- 96.01% accuracy, ~55 ms latency

**Stage III — LLM Arbitration (Dynamic, conditional)**
- Processes ambiguous ~10% of traffic
- Fuses LLM verdict + neural fallback
- Decision: {Safe, Unsafe, Uncertain}

### Attack Taxonomy (MCP-AttackBench, 70,448 samples)

| Macro-Category | Attack Type | Sample Count |
|---------------|-------------|-------------|
| Semantic/Adversarial | Jailbreak Instruction | 68,172 |
| Semantic/Adversarial | Prompt Injection | 326 |
| Protocol-Specific | Cross Origin Attack | 628 |
| Protocol-Specific | Shadow Hijack | 300 |
| Protocol-Specific | Puppet Attack | 100 |
| Protocol-Specific | Tool-name Spoofing | 88 |
| Injection/Execution | Command Injection | 519 |
| Injection/Execution | Data Exfiltration | 147 |
| Injection/Execution | SQL Injection | 128 |
| Injection/Execution | `<IMPORTANT>` Tag Abuse | 40 |

### Comparison to Your Idea

| Dimension | MCP-Guard | Your Project |
|-----------|-----------|--------------|
| Architecture pattern | Cascaded filter pipeline | Static score + dynamic score |
| Static component | Pattern-matching (syntax) | Design-time tool properties |
| Dynamic component | Neural + LLM (semantic) | Runtime call + session analysis |
| Output | Block/pass binary | Numeric score → policy action |
| Attack taxonomy | 11 MCP-specific types | TBD — currently unspecified |
| Scoring persistence | Per-call, stateless | Session-aware (accumulated context) |
| MCP-specific | Yes | Yes |

**Key takeaway:** MCP-Guard's three-stage cascade is the most operationally mature
architecture. Your dual static/dynamic design is complementary: the static score
maps to Stage I (tool-level risk before any call), and the dynamic score maps to
Stages II–III (request-level semantic risk). MCP-Guard's 11 attack categories should
be the seed taxonomy for your threat classification. The gap: MCP-Guard is stateless
(no session tracking), while your framework includes context reuse and trust boundary
violations across calls.

---

## 4. R-Judge — Risk Taxonomy for Agent Actions

**Paper:** Yuan et al., arXiv:2401.10019, EMNLP 2024 Findings

### Taxonomy: 10 Risk Types × 27 Scenarios × 5 Application Categories

**10 Risk Types:**

| # | Risk Type | Description |
|---|-----------|-------------|
| 1 | Privacy Leakage | Unauthorised disclosure of confidential information |
| 2 | Computer Security | System vulnerabilities and improper access controls |
| 3 | Financial Loss | Unspecified transactions causing monetary damage |
| 4 | Property Damage | Physical destruction or harmful resource allocation |
| 5 | Physical Health | Threats to user wellness or medical safety |
| 6 | Data Loss | Unintended deletion or system corruption |
| 7 | Illegal Activities | Violations of laws or intellectual property rights |
| 8 | Ethics & Morality | Dishonest conduct or inappropriate communications |
| 9 | Bias & Offensiveness | Discriminatory or inappropriate content |
| 10 | Miscellaneous | Residual safety concerns |

**5 Application Categories with 27 Scenarios:**

| Category | Scenario Count | Example Scenarios |
|----------|---------------|-------------------|
| Program | 6 | Terminal, code editing, GitHub, cybersecurity tools |
| Web | 3 | Web browsing, search |
| Software | 7 | Twitter, Gmail, Dropbox, Evernote |
| IoT | 2 | Smart home, traffic management |
| Finance | 4 | Crypto, e-commerce, banking |

**Risk Description Schema — MTO:**
Each risk record uses Motivation → Trigger → Outcome to structure what makes an
agent action risky. This encodes causal chain rather than just outcome severity.

### Comparison to Your Idea

| Dimension | R-Judge | Your Project |
|-----------|---------|--------------|
| Perspective | Agent behaviour safety | MCP server protection from agents |
| Granularity | Trajectory-level judgement | Request/call-level scoring |
| Scoring output | Binary safe/unsafe + F1 | Numeric risk score |
| Taxonomy coverage | 10 risk types, application-domain aware | Currently unspecified threat categories |
| Context use | Full interaction history | Dynamic mode: call + session |
| Formula/dimensions | MTO schema (qualitative) | Needs explicit numeric dimensions |

**Key takeaway:** R-Judge's 10 risk types are the most reusable consequence taxonomy
for your framework. Risks 1 (Privacy), 2 (Computer Security), 3 (Financial), and 6 (Data Loss)
directly map to what an MCP server must protect. The MTO schema provides a structured
way to write your risk feature descriptions: for each tool, document what motivation
enables misuse, what trigger (argument pattern) activates it, and what outcome results.

---

## 5. MAESTRO — Layered Risk Scoring for Agentic AI

**Paper:** Zambare et al., arXiv:2508.10043, Aug 2025

### Seven-Layer Framework

| Layer | Covers |
|-------|--------|
| L1 — Foundation Models | LLM contextual reasoning |
| L2 — Data Operations | Data pipelines, statistics |
| L3 — Agent Frameworks | Planning, execution logic, tool invocation |
| L4 — Deployment & Infrastructure | APIs, containers, microservices |
| L5 — Evaluation & Observability | Logs, dashboards, anomaly metrics |
| L6 — Security & Compliance | Auth, audit, access controls |
| L7 — Agent Ecosystem | Human operators, external agents |

### Risk Scoring Formula

```
R = P × I × E
```

Where:
- **P (Likelihood)**: probability of threat occurrence (Low=1, Med=2, High=3)
- **I (Impact)**: severity if threat succeeds (Low=1, Med=2, High=3)
- **E (Exploitability)**: susceptibility given exposure + attack complexity

Max score = 27. Highest-scoring threat: **Resource Exhaustion** at L4 (score=27).

### 10 Threat Categories with Scores

| Threat | Layer | Score |
|--------|-------|-------|
| Input-Induced Behavior Manipulation | L3 | 12 |
| Goal Manipulation | L3 | 9 |
| Chain-of-Thought Manipulation | L1 | 18 |
| Memory & Context Manipulation | L3 | 12 |
| Critical System Interaction | L4 | 12 |
| Planning & Reasoning Exploitation | L3 | 18 |
| **Resource Exhaustion** | L4 | **27** |
| Knowledge Base Poisoning | L2 | 9 |
| Supply Chain Compromise | L2 | 12 |
| Multi-Agent Exploitation | L3 | 18 |

### Comparison to Your Idea

| Dimension | MAESTRO | Your Project |
|-----------|---------|--------------|
| Formula | R = P × I × E (ordinal, 1–3) | Static + dynamic numeric score (design TBD) |
| Granularity | Per-threat-type, per-layer | Per-tool-call request |
| Static component | Yes (inherent threat properties) | Yes (design-time tool risk) |
| Dynamic component | Yes (real-time anomaly response) | Yes (runtime request scoring) |
| Threat taxonomy | 10 categories across 7 layers | TBD |
| Domain | Network monitoring agentic AI | MCP server tool interactions |

**Key takeaway:** MAESTRO's R = P × I × E formula is the simplest validated risk
scoring approach applicable to your framework. Your dynamic score formula could
be structured as: `Score = Likelihood(call context) × Impact(tool category) × Exploitability(argument pattern)`.
The ordinal 1–3 scale per dimension maps cleanly to configurable thresholds for
gate/throttle/deny decisions.

---

## 6. TRiSM for Agentic AI — Governance Framework

**Paper:** Raza et al., arXiv:2506.04133, Dec 2025 (Vector Institute / Cornell)

### Framework Pillars

| Pillar | What it covers |
|--------|---------------|
| Explainability | Decision provenance, interpretable rationales |
| ModelOps | Lifecycle management, drift monitoring |
| Application Security | Prompt hygiene, sandboxing, access control |
| Model Privacy | Data protection across agents |
| Lifecycle Governance | Regulatory compliance, auditability |

### Risk Taxonomy for AMAS

| Threat | Description |
|--------|-------------|
| Adversarial Attacks | Prompt injection, jailbreaks |
| Data Leakage | Cross-agent information exposure |
| Agent Collusion | Coordinated misbehaviour across agents |
| Emergent Misbehaviour | Unintended goal drift at scale |
| Memory Poisoning | Long-term context contamination |
| Tool-Use Abuse | Malicious or excessive tool invocation |

### Metrics

- **CSS (Component Synergy Score)**: measures inter-agent coordination quality
- **TUE (Tool Utilization Efficacy)**: assesses correctness and efficiency of tool calls

### Comparison to Your Idea

| Dimension | TRiSM | Your Project |
|-----------|-------|--------------|
| Scope | Holistic governance framework | Focused risk scoring at request level |
| Threat taxonomy | 6 AMAS-specific threat types | Subset (tool-use abuse + adversarial) |
| Scoring output | Qualitative governance assessment | Numeric score per request |
| Runtime applicability | Design + governance | Primarily runtime (dynamic mode) |
| Tool-specific scoring | TUE (efficiency metric only) | Risk severity per tool call |

**Key takeaway:** TRiSM is too broad to apply directly, but its **tool-use abuse** category
and **TUE metric** are directly in scope. The memory poisoning threat is important for
your dynamic mode — an agent that contaminates prior context window to manipulate
a later tool call is not captured by single-call scoring.

---

## 7. From Description to Score: Can LLMs Quantify Vulnerabilities?

**Paper:** Jafarikhah et al., arXiv:2512.06781, SAC '26 (Jan 2026, UNC Wilmington)

### What CVSS Measures (and Where it Falls Short)

**CVSS v3.1 Base Metrics:**

| Metric | Type | Values |
|--------|------|--------|
| Attack Vector (AV) | Exploitability | Network, Adjacent, Local, Physical |
| Attack Complexity (AC) | Exploitability | Low, High |
| Privileges Required (PR) | Exploitability | None, Low, High |
| User Interaction (UI) | Exploitability | None, Required |
| Scope (S) | Modifier | Unchanged, Changed |
| Confidentiality Impact (C) | Impact | None, Low, High |
| Integrity Impact (I) | Impact | None, Low, High |
| Availability Impact (A) | Impact | None, Low, High |

**Key empirical finding:** GPT-5 achieves 78.99% weighted F1 on automated CVSS
prediction from CVE descriptions. Hardest metrics: Privileges Required (71.61%), 
Availability Impact (67.95%). Easiest: User Interaction (88.95%), Attack Vector (87.96%).

**Critical limitation:** CVSS was designed for static software vulnerabilities.
It lacks metrics for: agent autonomy, context chain exploitation, temporal persistence,
or tool-invocation blast radius.

### Comparison to Your Idea

| Dimension | CVSS/LLM Auto-Scoring | Your Project |
|-----------|----------------------|--------------|
| Scoring target | Static CVE vulnerabilities | Dynamic agent tool-call requests |
| Dimensions | 8 fixed base metrics | Needs: autonomy, context, blast radius |
| Runtime applicability | No (design-time only) | Both static (maps to base metrics) and dynamic |
| Agent-specific | No | Yes (core design principle) |
| Contextual | No | Yes (session history, call sequence) |

**Key takeaway:** CVSS Attack Vector, Privileges Required, and Scope directly map
to your **static scoring** dimensions. A tool that requires `AV=Network, PR=None, S=Changed`
is inherently high-risk before any agent touches it. Your dynamic score needs
**additional dimensions** that CVSS lacks: argument sensitivity, call-chain position,
session anomaly, and tool blast radius.

---

## 8. Graph of Effort — AI-Assisted Attack Effort Scoring

**Paper:** Mehra et al., arXiv:2503.16392, Cloud Computing 2025

### Scoring Methodology

Each kill chain step is scored 0–3 based on three binary criteria:

```
score(step_i) = AT + TAI + G
```

Where:
- **AT** (Automation Tools): ready-to-use AI models exist? (1 if yes)
- **TAI** (Trainability of AI): datasets available to train custom models? (1 if yes)
- **G** (Generability): automated data generation possible? (1 if yes)

**Overall GOE = min(score across all 4 kill chain steps)**
The minimum function captures that a chain is only as hard as its easiest step.

**4 Kill Chain Steps:** Reconnaissance → Weaponization → Delivery → Exploitation

**Integration with CVSS:** GOE maps to the CVSS v4.0 Supplemental Metric "Automatable"
(N/H), enabling enrichment of existing CVSS scores without replacing them.

### Comparison to Your Idea

| Dimension | Graph of Effort | Your Project |
|-----------|----------------|--------------|
| Scoring target | Effort to use AI for exploiting a CVE | Risk of an agent's tool-call to a server |
| Formula | min(AT + TAI + G) per kill chain step | Multi-factor: likelihood × impact × context |
| Static vs dynamic | Static (design-time analysis) | Both modes |
| MCP/agent specific | No — general AI-assisted attacks | Yes |
| Automation dimension | Core dimension (AT) | Should be captured in agent autonomy |

**Key takeaway:** The **minimum function** design principle is important: the overall
risk of an agent's tool chain is bounded by the easiest-to-exploit step, not the
hardest. In a multi-tool session, a single low-friction tool (e.g., `read_file`) may
be the entry point that enables a high-risk tool chain. Your static score should
use a similar bottom-up aggregation when tools are combined.

---

## 9. OWASP AIVSS — Industry Standard for AI Vulnerability Scoring

**Source:** OWASP Foundation, aivss.owasp.org, v0.8 (2025)

### AI-Specific Scoring Dimensions (0.0–1.0 each)

| Metric | Description |
|--------|-------------|
| Model Robustness | Resistance to adversarial perturbations |
| Data Sensitivity | Sensitivity of data the model accesses |
| Exploitation Impact | Severity of a successful exploit |
| Decision Criticality | Criticality of decisions the model makes |
| Adversarial Difficulty | Difficulty of crafting a working attack |
| **Agent Autonomy** | Degree of autonomous action the agent can take |
| **Lateral Leverage** | Ability to pivot to adjacent systems/tools |
| Goal Vulnerability | Susceptibility of agent goals to manipulation |
| Context Sensitivity | Sensitivity of context available to the model |

Combined with a **ModelComplexityMultiplier**.

Covers agentic-specific risks: tool squatting, memory poisoning, agent identity impersonation.

### Comparison to Your Idea

| Dimension | OWASP AIVSS | Your Project |
|-----------|-------------|--------------|
| Scoring target | AI system vulnerability severity | Risk of agent tool-call to MCP server |
| Agent-specific dimensions | Agent Autonomy, Lateral Leverage | These should be core dimensions |
| Runtime use | Primarily static assessment | Both static and dynamic |
| MCP-specific | No | Yes |
| Formula published | Yes (with calculator) | Under development |

**Key takeaway:** AIVSS's **Agent Autonomy** and **Lateral Leverage** dimensions are
the most critical adoptable metrics for your framework. A tool that enables high
lateral leverage (e.g., `shell_exec` that can pivot to filesystem + network) should
score much higher than a read-only query tool even if their CVSS base scores are
similar. These two dimensions are your primary differentiation from traditional scoring.

---

## 10. Dynamic Risk Assessment — Systematic Review

**Paper:** Cheimonidis & Rantos, Future Internet 15(10):324, 2023

### DRA Method Taxonomy (50 models reviewed)

| Method Class | Approach | Strength |
|-------------|----------|---------|
| Bayesian Networks | Probabilistic inference over threat states | Uncertainty quantification |
| Attack Graphs | Causal chain modelling | Multi-step attack path scoring |
| Machine Learning | Pattern detection from traffic/logs | Scalable anomaly detection |
| Event-driven | State machine triggers on security events | Low latency response |

**Definition of DRA:** "The continuous process of identifying and assessing risks to
organisational operations in near real-time."

**Key gaps found:**
- Limited real-world deployment
- Rarely handles cascaded/chained threats
- No cross-session persistence in most models
- Threshold calibration is domain-specific and hard to generalise

### Comparison to Your Idea

| Dimension | DRA Literature | Your Project |
|-----------|---------------|--------------|
| Real-time scoring | Yes (core requirement) | Yes (dynamic mode) |
| Chained threats | Gap in literature | Your session-context is meant to address this |
| Bayesian approaches | Recommended | Compatible with P × I × E formula |
| Agent-specific | Absent from all 50 models | Core design |
| MCP-specific | Absent | Core design |

**Key takeaway:** The DRA literature confirms that your dynamic scoring mode is
**research-novel**: none of the 50 reviewed models handle autonomous agent chains,
MCP-specific protocol behaviour, or cross-session context accumulation. This is
your clearest gap claim.

---

## Synthesis: Full Comparison Table

| Approach | Threat Direction | Scoring Mode | Formula | Agent-Aware | MCP-Specific | Output |
|----------|-----------------|-------------|---------|------------|-------------|--------|
| **Your Project** | Agent → Server | Static + Dynamic | TBD | Yes | Yes | Numeric score → gate/throttle/deny |
| ToolSafe | User/Injector → Agent | Dynamic (step-level) | 3-task GRPO | Yes | No | 3-class label + feedback |
| MCPShield | Malicious server → Agent | Static + Dynamic + Post | Deny-rate score | Yes | Yes | Binary trusted/untrusted |
| MCP-Guard | Attacker → MCP | Static + Dynamic | Cascade pipeline | Yes | Yes | Binary block/pass |
| R-Judge | Agent actions → World | Dynamic (trajectory) | Binary/F1 | Yes | No | Safe/unsafe label |
| MAESTRO | Agent threats → System | Static + Dynamic | R = P × I × E | Yes | No | Per-threat risk score |
| TRiSM | Various → AMAS | Design-time | Qualitative | Yes | No | Governance assessment |
| CVSS (LLM-scored) | Attacker → Software | Static | 8-metric base score | No | No | 0–10 severity |
| Graph of Effort | AI → Vulnerability | Static | min(AT+TAI+G) | Yes (AI effort) | No | 0–3 per step |
| OWASP AIVSS | Various → AI System | Static | 0–1 per metric × multiplier | Yes | No | Composite AI risk score |
| DRA Literature | Various → Infrastructure | Dynamic | Bayesian/ML | No | No | Real-time risk state |

---

## What Makes Your Idea Novel: Gap Analysis

### 1. The Server-Side Framing Is Unique

Every paper above either:
- Defends the **agent** from external manipulation (ToolSafe, MCPShield, R-Judge, GuardAgent), or
- Scores the **vulnerability of a system** in isolation (CVSS, EPSS, AIVSS, GOE)

None treats the **MCP server as a first-class protected asset** that scores whether
an agent request should be executed. This framing is architecturally distinct.

### 2. Static + Dynamic as Complementary Modes

| Existing approach | What it scores |
|------------------|----------------|
| Static-only (CVSS, AIVSS) | What the tool *can* do — no request context |
| Dynamic-only (ToolSafe, MCP-Guard) | What the specific call *is doing* — no inherent risk baseline |
| **Your project** | Both: inherent tool risk + contextual request risk → combined score |

The combination enables a decision rule such as:
"Block if static_score > 8 OR dynamic_score > 6 OR (static_score > 5 AND dynamic_score > 4)"

No existing paper operationalises this duality.

### 3. Session-Level Context Accumulation

Most papers score individual calls or individual trajectories. Your framework's
"context reuse and trust boundary violations across calls" addresses the **temporal
misalignment** problem that MCPShield identifies but only partially solves. A scoring
system that tracks call chains (e.g., `read_file` → `write_file` → `send_email`
within one session, each individually low-risk but collectively high-risk) is novel
across all surveyed literature.

### 4. Dimensions to Add That Literature Confirms Are Missing

Drawing from OWASP AIVSS, MAESTRO, and the DRA gap analysis, your scoring framework
should include these dimensions that no single existing framework captures together:

| Dimension | Source | Applies to |
|-----------|--------|-----------|
| Tool blast radius (Lateral Leverage) | OWASP AIVSS | Static score |
| Agent autonomy level | OWASP AIVSS | Static score |
| Argument sensitivity | ToolSafe BTRA | Dynamic score |
| Call-chain position | Graph of Effort (min step) | Dynamic score |
| Session anomaly delta | DRA / MCPShield temporal | Dynamic score |
| Request harmfulness (upstream intent) | ToolSafe h_t | Dynamic score |
| Prompt injection link | ToolSafe v_t | Dynamic score |
| Impact class (R-Judge risk types 1–6) | R-Judge | Both |

---

## Recommended Taxonomy for Your Framework

Based on all papers surveyed, a practical threat taxonomy for the MCP server
risk scoring framework:

### Static Threat Categories (tool properties)

| Category | Derived from |
|----------|-------------|
| Execution scope (local/adjacent/network/cloud) | CVSS Attack Vector |
| Privilege level required | CVSS Privileges Required |
| Scope change potential (can affect other servers) | CVSS Scope |
| Data sensitivity class (read/write/delete/exfiltrate) | R-Judge risk types 1, 3, 6 |
| Lateral leverage (can chain to other tools/systems) | OWASP AIVSS |
| Reversibility (idempotent vs. destructive) | R-Judge Property Damage |

### Dynamic Threat Categories (per-call context)

| Category | Derived from |
|----------|-------------|
| Malicious user request (upstream intent) | ToolSafe MUR |
| Prompt injection in arguments | ToolSafe PI / MCP-Guard |
| Protocol-level attack (spoofing, shadow hijack) | MCP-Guard |
| Risky argument pattern on benign tool | ToolSafe BTRA |
| Session chain risk (sequence anomaly) | MCPShield temporal + DRA |
| Identity/trust boundary violation | OWASP AIVSS, Paper 26 (ZT-IAM) |

---

## References

Papers discussed in this document are catalogued in
[annotated-bibliography-mcp-security.md](annotated-bibliography-mcp-security.md).

Additional papers read directly:
- ToolSafe — arXiv:2601.10156
- MCPShield — arXiv:2602.14281
- From Description to Score — arXiv:2512.06781
- TRiSM for Agentic AI — arXiv:2506.04133
- MCP-Guard — arXiv:2508.10991
- R-Judge — arXiv:2401.10019
- MAESTRO (Securing Agentic AI) — arXiv:2508.10043
- Graph of Effort — arXiv:2503.16392
- OWASP AIVSS — aivss.owasp.org
- Dynamic Risk Assessment (Cheimonidis) — doi:10.3390/fi15100324
