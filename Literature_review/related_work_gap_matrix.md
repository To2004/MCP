# Related-Work Gap Matrix — Attack Directions × Existing Frameworks

> **Purpose:** defend the thesis claim that MCP-RSS is the **first dynamic,
> ordinal, agent-aware risk scorer for the agent→server direction** of the
> Model Context Protocol. Each qualifier below is load-bearing — dropping any
> one of them surfaces a prior-art contender.
>
> **Threat model reminder:** the MCP **server is the protected asset**. All
> attacks in scope flow **client → server** (agent is the threat source,
> server is the victim). The inverse direction (malicious server attacking
> the agent) is surveyed here only to demonstrate that it is where the
> existing literature and tooling actually concentrate.

---

## Attack-Direction Columns

| Code | Direction | Example |
|------|-----------|---------|
| **A→S** | Agent → Server | Compromised agent sends `read_file("../../etc/passwd")`; SQLi via tool param; DoW through tool abuse. **Thesis focus.** |
| **S→A** | Server → Agent | Malicious tool description poisons agent behavior; rug-pull after approval; metadata poisoning. |
| **S→S** | Server → Server (cross-tool) | Tool shadowing, parasitic toolchain, one server's output hijacks another server's invocation. |
| **U→A (PI)** | User → Agent via direct prompt injection | "Ignore previous instructions and …" injected into agent input. |
| **Ext→A (iPI)** | External → Agent via indirect prompt injection | Hidden instructions in a web page or document the agent retrieves. |
| **CVE** | Traditional software vuln (CWE-78, -22, -89 …) | Classical server-code bug surfaced through an MCP tool (also A→S-adjacent). |

---

## Master Matrix

Cells: **Y** = Covered · **P** = Partial · **—** = Not covered.

### External industry frameworks

| Framework | A→S | S→A | S→S | U→A | Ext→A | CVE |
|-----------|:---:|:---:|:---:|:---:|:-----:|:---:|
| OWASP LLM Top 10 (2023 + 2025) | — | — | — | Y | Y | — |
| OWASP Agentic AI Top 10 (ASI 2026) | P | Y | P | P | Y | P |
| MITRE ATLAS (v5.x, Oct 2025 + Feb 2026 updates) | P | P | P | P | P | P |

### Practitioner MCP tooling

| Tool | A→S | S→A | S→S | U→A | Ext→A | CVE |
|------|:---:|:---:|:---:|:---:|:-----:|:---:|
| DVMCP (target lab, 10 challenges) | P | Y | Y | Y | Y | P |
| Invariant Labs `mcp-scan` / Snyk `agent-scan` | — | Y | Y | P | P | — |
| MCP-Shield (riseandignite) | — | Y | Y | — | — | — |
| MCP Guardian (eqtylab, runtime proxy) | P | P | — | — | — | — |
| MCPSafetyScanner (Halloran et al., 2504.03767) | P | Y | — | — | — | P |
| Cisco AI Defense mcp-scanner | — | Y | P | — | — | P |
| Lasso Security MCP Gateway | P | P | — | P | — | — |
| MCP Guard (General-Analysis) | — | Y | — | — | P | — |

### Academic MCP defense frameworks

| Framework | A→S | S→A | S→S | U→A | Ext→A | CVE |
|-----------|:---:|:---:|:---:|:---:|:-----:|:---:|
| MCP-Guard (Xing et al., 2508.10991) | **Y** | Y | P | Y | P | — |
| MCPShield (Zhou et al., 2602.14281) | — | Y | P | — | — | — |
| MCIP (Jing et al., HKUST 2025) | P | Y | Y | P | — | — |
| MCP Guardian (Kumar et al., 2025) | P | — | — | — | — | P |
| ETDI (Bhatt et al., 2025) | P | Y | — | — | — | — |
| Progent (Shi et al., 2504.11703) | **Y** | P | P | Y | Y | — |
| GuardAgent (Xiang et al., 2406.09187) | P | — | — | P | — | — |
| MiniScope (Zhu et al., 2512.11147) | P | — | — | — | — | — |
| MindGuard (Wang et al., 2508.20412) | — | Y | P | — | — | — |
| ToolSafe (step-level guardrail) | — | — | — | Y | Y | — |
| LlamaFirewall / NeMo Guardrails | — | — | — | Y | Y | — |

### Risk-scoring / evaluation work (scoring-method neighbours)

| Work | A→S | S→A | S→S | U→A | Ext→A | CVE |
|------|:---:|:---:|:---:|:---:|:-----:|:---:|
| From Description to Score (Jafarikhah, SAC'26) | — | — | — | — | — | **Y** |
| TRiSM for Agentic AI (survey, 2506.04133) | survey | survey | survey | survey | survey | survey |
| R-Judge (benchmark, 569 traces) | P | P | P | P | P | — |
| TraceAegis (behavioural anomaly) | — | — | — | P | P | — |

---

## Methodological Axes (the second gap dimension)

Attack-direction coverage alone does not isolate MCP-RSS's contribution. Four
methodological axes separate it from the nearest competitors:

| Framework (nearest A→S contenders) | Timing | Output type | Agent-aware | Policy-free |
|---|---|---|---|---|
| **MCP-Guard** | Dynamic (inline proxy) | **Binary** (block/pass) | No — payload-only | Yes (learned) |
| **Progent** | Dynamic (per-call) | **Binary** (allow/deny) | Yes | No — hand-authored JSON |
| **MCIP Guardian** | Dynamic (multi-turn) | Multi-class label (10-way) | No | Yes |
| **From Description to Score** | **Static** (text-only) | **Ordinal 0–10 (CVSS)** | No | Yes |
| **MCP Guardian (Kumar)** | Dynamic (WAF gateway) | Binary (allow/deny/throttle) | Partial (auth identity) | No — rules |
| **MCP-RSS (this thesis)** | **Static + Dynamic** | **Ordinal 1–10** | **Yes** | **Yes (learned)** |

No single row above matches MCP-RSS on all four axes, sir.

---

## Per-Cluster Rationale

### External industry frameworks — framing mismatch, not a drop-in competitor

**OWASP LLM Top 10 (2023 + 2025).** The LLM/model is the victim throughout.
LLM05 (Improper Output Handling) and LLM06 (Excessive Agency) share the
*shape* of A→S — tool call with harmful parameters causes downstream damage —
but neither scores the request to an MCP server or treats the server as the
protected asset. LLM10 (Unbounded Consumption) targets LLM infrastructure,
not MCP servers.
Source: <https://genai.owasp.org/llm-top-10/>

**OWASP Agentic AI Top 10 (ASI 2026).** Closest of the three industry lists.
ASI02 (Tool Misuse & Exploitation), ASI03 (Identity & Privilege Abuse), ASI05
(Unexpected Code Execution), and ASI10 (Rogue Agents) acknowledge that agents
can cause server-side harm. But ASI framing is agent-ecosystem-centric —
"protect the agent's integrity and its workflow outcomes" — not server-
centric per-request scoring. No ASI category defines a quantitative risk
score for an incoming request to an MCP server.
Source: <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/>

**MITRE ATLAS.** Core scope is attacks on ML models (evasion, poisoning,
extraction). The post-Oct-2025 additions — AML.T0061 AI Agent Tools,
AML.T0062 Exfiltration via AI Agent Tool Invocation, and MCP Server
Compromise case studies — explicitly cover A→S and S→A **techniques**, but
ATLAS is a **TTP knowledge base, not a risk-scoring framework**. It catalogs
*what* adversaries do, not *how risky a specific request is*.
Source: <https://atlas.mitre.org/>

### Practitioner MCP tooling — almost entirely protects the agent, not the server

Eight publicly available MCP security tools were audited. They split into
three groups:

1. **Static server/description scanners** (`mcp-scan`, MCP-Shield,
   MCPSafetyScanner, Cisco mcp-scanner) — overwhelmingly defend the *agent*
   against a malicious *server*: tool poisoning, shadowing, description
   injection. Opposite direction from MCP-RSS.
2. **Runtime proxies/gateways** (MCP Guardian/eqtylab, Lasso MCP Gateway,
   MCP Guard/General-Analysis) — intercept live traffic but enforce
   **binary** approve/deny or content-moderation policies (PII, PI strings,
   secrets). None produce an ordinal MCP-native score; none are agent-aware.
3. **Labs / benchmarks** (DVMCP) — targets for evaluation, not scorers.

Lasso MCP Gateway is the sole tool that combines runtime interception with
policy-like enforcement, but its model is generic DLP / content moderation,
not MCP-specific dimensions (permission overreach, blast radius, chain risk,
tool severity).

**Qualitative verdict:** zero of the surveyed practitioner tools deliver
dynamic, agent-aware, multi-dimensional risk scoring of agent→server MCP
requests.

### Academic MCP defense frameworks — three near-misses

Three published academic frameworks are close enough to MCP-RSS's territory
to require explicit differentiation:

**MCP-Guard (closest prior art).** Three-stage cascaded proxy — regex, then
fine-tuned E5 neural detector, then LLM arbiter — inspects MCP request
payloads in-flight. F1=95.4%, ~506 ms. **It is the only published work that
does A→S semantic payload inspection dynamically at the server boundary.**
What it does NOT do: it outputs a **binary** block/pass verdict (Stage II
emits a continuous P(y|x) internally but binarises at threshold), it is not
agent-aware (decision depends on payload content, not caller history), and
it carries no ordinal severity. The MCP-Guard authors' own roadmap lists
"graded risk scoring" as future work — MCP-RSS fills exactly that slot.

**Progent (strongest deterministic A→S gate).** Programmable JSON-policy
proxy that intercepts every tool call; supports dynamic policy updates
driven by agent state. Drops prompt-injection ASR from 41.2 % → 2.2 % on
AgentDojo. **But it is a policy enforcer, not a risk scorer** — it requires
hand-authored policies per agent and outputs deterministic allow/deny. It
cannot rate previously unseen call patterns without a matching rule.

**MCIP Guardian.** Dynamic multi-turn classifier labels MCP dialogues into
10 attack types + safe. **Categorical** output, not ordinal severity;
taxonomy oriented to contextual-integrity violations rather than
server-impact magnitude.

All other academic frameworks (MCPShield, MindGuard, GuardAgent, MiniScope,
ETDI, ToolSafe, LlamaFirewall, NeMo Guardrails) either point in the opposite
direction (protecting the agent), constrain a different axis (permission
scoping, identity, LLM-internal drift), or operate at different layers
(session guardrails, memory integrity). They are complementary, not
competing.

### Risk-scoring neighbours — the ordinal-score question is unsolved

**From Description to Score (Jafarikhah et al., SAC'26)** is the only work
here that actually outputs an ordinal risk score. It predicts the eight CVSS
base metrics from CVE *text* — static, text-only, CVE-centric. It proves that
LLM-based ordinal scoring is feasible, but it does not touch MCP, agents,
runtime requests, or agent-awareness.

**TRiSM for Agentic AI** is a 180-paper survey. Its own mapping confirms that
no reviewed work combines runtime evaluation + agent-awareness + ordinal
scoring + server-as-victim framing.

**R-Judge** demonstrates how hard even *binary* safety judgement is for
state-of-the-art LLMs (GPT-4o: 74.42 % on 569 traces). Ordinal scoring is
strictly harder.

**TraceAegis** scores trace anomalies, not request severity — a different
quantity.

---

## Synthesis — the Defensible "First" Claim

**Defensible claim (use this exact framing in the thesis):**

> MCP-RSS is the **first dynamic, ordinal, agent-aware risk scorer for the
> agent→server direction of the Model Context Protocol**.

Each qualifier is load-bearing:

| Qualifier | Dropping it surfaces | Why the contender fails to cover the full claim |
|-----------|---------------------|--------------------------------------------------|
| **dynamic** | From Description to Score | It's ordinal and policy-free, but static + text-only + non-MCP |
| **ordinal** | MCP-Guard | Dynamic + A→S + policy-free, but **binary** block/pass |
| **agent-aware** | MCP-Guard (again) | Payload-only, no per-caller reputation or history |
| **agent→server** | MCPShield | Dynamic and lifecycle-aware, but protects the *agent* from the server |
| **MCP-scoped** | General LLM guardrails (Lasso, Llama-Firewall, NeMo) | Content-moderation / DLP primitives, not MCP-native risk dimensions |

**Positioning statement (recommended):**

> MCP-Guard (Xing et al., 2026) demonstrated that semantic inspection of
> agent→server MCP payloads is feasible at ~506 ms with F1=95.4 %. Progent
> (Shi et al., 2025) demonstrated that per-call policy enforcement sharply
> reduces agent-driven attack success. MCP-RSS extends this trajectory
> beyond binary block/pass and hand-authored policies to an **ordinal 1–10
> risk score** that incorporates caller identity, request semantics, and
> tool blast-radius — filling the exact roadmap slot acknowledged in
> MCP-Guard §11.

**What honest differentiation requires:**

- Cite MCP-Guard as the closest prior art, not as an unrelated work.
- Do not claim "first to defend servers" — Progent, MCP-Guard, and
  several gateways already do that at policy-level granularity.
- The novelty is **the ordinal + agent-aware combination on the A→S axis**,
  not the direction itself.

---

## References

- OWASP LLM Top 10 2025: <https://genai.owasp.org/llm-top-10/>
- OWASP Top 10 for Agentic Applications 2026: <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/>
- MITRE ATLAS: <https://atlas.mitre.org/>
- DVMCP: <https://github.com/harishsg993010/damn-vulnerable-MCP-server>
- Invariant Labs `mcp-scan` / Snyk `agent-scan`: <https://github.com/snyk/agent-scan>
- MCP-Shield: <https://github.com/riseandignite/mcp-shield>
- MCP Guardian (eqtylab): <https://github.com/eqtylab/mcp-guardian>
- MCPSafetyScanner: <https://arxiv.org/abs/2504.03767>
- Cisco mcp-scanner: <https://github.com/cisco-ai-defense/mcp-scanner>
- Lasso MCP Gateway: <https://github.com/lasso-security/mcp-gateway>
- MCP Guard (General-Analysis): <https://github.com/General-Analysis/mcp-guard>
- MCP-Guard (Xing et al.): <https://arxiv.org/abs/2508.10991>
- MCPShield (Zhou et al.): <https://arxiv.org/abs/2602.14281>
- Progent (Shi et al.): <https://arxiv.org/abs/2504.11703>
- GuardAgent (Xiang et al.): <https://arxiv.org/abs/2406.09187>
- MiniScope (Zhu et al.): <https://arxiv.org/abs/2512.11147>
- MindGuard (Wang et al.): <https://arxiv.org/abs/2508.20412>
- From Description to Score (Jafarikhah et al.): SAC '26
- TRiSM for Agentic AI (Raza et al.): <https://arxiv.org/abs/2506.04133>
- Repo-local attack taxonomy: [mcp_server_attack_taxonomy_v2_agent_boundary.md](mcp_server_attack_taxonomy_v2_agent_boundary.md)
- Repo-local DVMCP benchmark card: [reviews/benchmark_md/20_dvmcp.md](reviews/benchmark_md/20_dvmcp.md)
