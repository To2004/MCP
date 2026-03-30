# Final Report: Datasets, Dimensions, and the MCP-RSS Idea

## 1. The Idea in One Paragraph

MCP-RSS (MCP Risk Scoring System) is a transparent proxy that sits between an AI agent and an
MCP server. Every time the agent calls a tool via `tools/call`, MCP-RSS intercepts the request,
analyzes the tool metadata + request arguments + session history, and produces a **dynamic 1-10
risk score** with a full breakdown explaining why. Unlike every existing MCP defense that outputs
a binary allow/deny, MCP-RSS tells the operator **how dangerous** a specific request is and **why**
— just like CVSS does for software vulnerabilities, but adapted for the unique risks of AI agents
calling tools through the Model Context Protocol.

---

## 2. What Datasets We Have

We reviewed 22 benchmarks and datasets from the MCP security literature. Here is what we have,
what each one contains, and what risk signals we can extract.

### 2.1 MCP-Specific Datasets (10)

These datasets were built specifically for MCP protocol security.


| # | Dataset | Source Paper | Rows | Key Columns Available |
|---|---------|-------------|------|----------------------|
| 01 | **MCIP-Bench** | Jing et al. 2025 | 2,218 | `dialogue_turns` (list), `safety_label` (binary), `risk_category` (11 classes), `function_calls` (JSON with arguments), `source_dataset` |
| 02 | **MCIP Guardian Training** | Jing et al. 2025 | 13,830 | `risk_category` (11 classes with distribution), `transmission_steps` (~8/instance), `class_label`. Largest labeled set for MCP risk classification |
| 03 | **MCP-AttackBench** | — | 70,448 | `text_sample`, `binary_label` (attack/benign), `attack_family` (3: Semantic, Protocol, Injection), `attack_subtype`, `cascade_stage` (I/II/III), `runtime_latency` |
| 04 | **MCPTox** | — | 1,497 | `user_query`, `tool_description_poisoned`, `tool_description_original`, `attack_paradigm` (3 types), `attack_category` (10 types), `mcp_server_source` (45 servers), `asr_per_model` |
| 05 | **MCPSecBench** | — | 765 outcomes | `attack_type` (17), `attack_surface` (4: Client/Protocol/Server/Host), `target_client` (3), `asr_per_trial`, `refusal_rate`, `cost_per_round` ($0.41-$0.76) |
| 06 | **MCP-SafetyBench** | — | multi-turn | `domain` (5: Location/Repo/Financial/Browser/Web), `attack_type` (20), `attack_surface` (3), `target_llm` (13 models), `tsr`, `asr`, `dsr`, `safety_prompt_effective` |
| 07 | **MCP Server Database** | Zhao et al. (Mind Your Server) | 12,230 tools | `server_source` (3 registries), `tool_name`, `eit_flag`, `pat_flag`, `nat_flag`, `exploit_risk_flag`, `exploitable_combo_flag`, `parasitic_chain_member` |
| 08 | **Component Attack PoC** | — | 132 servers | `attack_category` (A1-A12), `server_type` (hand-crafted/generated), `components` (5 types), `scanner_detection` (mcp-scan/AI-Infra-Guard), `host_llm`, `trial_result` |
| 09 | **MCP Server Dataset 67K** | Li & Gao 2025 | 67,057 servers | `registry_source` (6), `server_language`, `tool_source_code`, `confusion_attack_success`, `shadowing_attack_success`, `credential_leakage`, `server_hijacking`, `affix_squatting_group` |
| 10 | **MCP-ITP Implicit Poisoning** | Li et al. | 548 × 12 models | `original_description`, `poisoned_description`, `target_llm` (12), `attack_success` (bool), `detection_by_defense` (bool), `steering_words` |

### 2.2 General Agent/LLM Security Datasets (12)

These datasets measure agent security, prompt injection, and LLM trustworthiness. Not MCP-specific
but transferable to the MCP-agent boundary.

| # | Dataset | Source Paper | Rows | Key Columns Available |
|---|---------|-------------|------|----------------------|
| 11 | **NVD/CVE + CVSS v3.1** | NIST | 31,000+ CVEs | `cve_id`, `description`, `attack_vector` (4), `attack_complexity` (2), `privileges_required` (3), `user_interaction` (2), `scope` (2), `confidentiality_impact` (3), `integrity_impact` (3), `availability_impact` (3), `cvss_base_score` (0-10) |
| 12 | **R-Judge** | — | 569 | `interaction_record`, `risk_scenario` (27), `app_category` (5), `risk_type` (10), `safety_label`, `llm_eval_scores` (11 models) |
| 13 | **AgentDojo** | — | 97 tasks + 629 injections | `task_suite` (4 domains), `user_task`, `injection_task`, `defense_baseline` (6 types), `utility` (%), `asr` (%) |
| 14 | **InjecAgent** | — | 1,054 | `test_case`, `user_tools` (17), `attacker_tools` (62), `harm_category` (direct/exfiltration), `injection_payload` |
| 15 | **Meta Tool-Use PI (LlamaFirewall)** | Meta | 600 | `interaction_trace` (JSON), `label` (benign/malicious), `injection_technique` (7), `threat_category` (8), `domain` (3) |
| 16 | **ASB (Agent Security Bench)** | — | variable | `attack_prompt_type` (6: naive/escape/context_ignoring/fake_completion/average/combined), `utility` (%), `asr` (%), `defense_baseline` (3) |
| 17 | **MiniScope** | — | 10 apps | `application` (10), `api_method` (79-247/app), `permission_scope` (10-84/app), `request_type`, `granted_scopes`, `minimum_scopes`, `mismatch_rate` (%), `latency_overhead` (1-6%) |
| 18 | **Indirect PI Attack** | — | 1,068 | `attack_template` (89), `obfuscation_type` (12), `target_model` (28), `vulnerability_result`, `model_vulnerability_rate` (%) |
| 19 | **DecodingTrust** | — | 30+ sub-datasets | `eval_dimension` (8: toxicity/stereotype/robustness/OOD/privacy/ethics/fairness/demos), `sub_benchmark`, `model_response`, `trustworthiness_score` |
| 20 | **TrustLLM** | — | 30+ datasets | `trust_dimension` (6: truthfulness/safety/fairness/robustness/privacy/ethics), `subcategory` (18), `model_results` (16 LLMs) |
| 21 | **Trust Paradox** | Xu et al. | 19 scenarios | `scenario_id`, `capability_tier` (5), `llm_backend` (4), `tci` (0.72-0.89), `capability_risk_ratio`, `safety_violation_rate`, `inter_agent_trust`, `convergence_iterations` (8-15) |
| 22 | **Synthetic PI** | — | 500 | `attack_category` (10), `injection_prompt`, `pipeline_stage_results`, `isr`, `pof`, `psr`, `ccs`, `tivs` |

### 2.3 Total Data Landscape

| Category | Datasets | Total Rows | Coverage |
|----------|----------|------------|---------|
| MCP-Specific | 10 | ~167,000+ | Tool poisoning, protocol attacks, server ecosystems, attack taxonomies |
| Agent Security | 7 | ~4,500+ | Prompt injection techniques, defense baselines, injection taxonomies |
| LLM Trustworthiness | 3 | 60+ sub-datasets | Model reliability across 6-8 dimensions, 16-28 models profiled |
| Vulnerability Scoring | 1 | 31,000+ CVEs | CVSS methodology — the foundation formula we adapt |
| Permission Analysis | 1 | 10 apps | Ground-truth minimum permission mappings — rare labeled data |
| **Total** | **22** | **~200,000+** | Full coverage of MCP-agent interaction risks |

---

## 3. How The Dimensions Changed

### 3.1 The Problem With v1

The first dimension set (8 dimensions, see `dimension_refinement_analysis.md`) was derived
bottom-up from the benchmarks. It answered: **"What risks exist in the MCP ecosystem?"**

But the thesis builds a proxy between the agent and the MCP server. The dimensions need to answer:
**"Is THIS tool call by THIS agent safe RIGHT NOW?"**

Four of the original 8 dimensions drifted from this question:

| v1 Dimension | What It Measured | Problem |
|-------------|-----------------|---------|
| Attack Category | What type of attack exists | Generic classification, not tied to a specific call |
| Attack Severity | How bad a vulnerability is (CVSS) | Measures vulnerabilities, not agent-tool interactions |
| Attack Surface | Which MCP architecture layer | Infrastructure property, not a call-time decision |
| Trustworthiness | How reliable the LLM/agent is | Measures the agent in isolation, not the interaction |

### 3.2 The v1 → v2 Transformation

```
v1: 8 ecosystem dimensions              v2: 7 boundary dimensions + 1 modifier
─────────────────────────               ──────────────────────────────────────

D1 Attack Category ──────────┐
                             ├──► Dim 2: REQUEST SENSITIVITY
D2 Attack Severity ──────────┤         "How dangerous is what the agent
                             │          is asking to do RIGHT NOW?"
                             │
                             └──► Dim 6: BLAST RADIUS
D3 Attack Surface  ──────────┘         "If this goes wrong, how much damage?"

D4 Tool Toxicity   ──────────────► Dim 1: TOOL INTEGRITY
                                        "Is this MCP tool trustworthy?"
                                        (expanded: + provenance + registry)

D5 Data Exposure   ──────────────► Dim 4: DATA EXPOSURE
                                        "What data flows through THIS call?"
                                        (expanded: + session-aware exfiltration)

D6 Trustworthiness ──────────────► AGENT TRUST MODIFIER (0.8× to 1.3×)
                                        Demoted: agent properties ≠ call properties
                                        Same data, better role as a multiplier

D7 Permission Scope ─────────────► Dim 3: PERMISSION OVERREACH
                                        "More access than this task needs?"

D8 Injection Resilience ─────────► Dim 5: INJECTION EXPOSURE
                                        "Is this call an injection channel?"
                                        (refocused: from model resilience → call exposure)

                          NEW ───► Dim 7: CROSS-TOOL ESCALATION
                                        "Does this call + session history =
                                         dangerous pattern?"
```

### 3.3 What Changed In Each Dimension

| v1 → v2 | What Changed | Why |
|---------|-------------|-----|
| Attack Category → **Request Sensitivity** | From "what type of attack" to "how dangerous is this specific request with these arguments" | The proxy sees the actual args — use them |
| Attack Severity → **split into Request Sensitivity + Blast Radius** | Severity = likelihood × impact. We split: likelihood goes to request analysis, impact goes to blast radius | Better separation of concerns |
| Attack Surface → **absorbed into Blast Radius** | "Which layer" is only useful for answering "how big is the explosion" | Surface is a property of impact, not a standalone risk axis |
| Tool Toxicity → **Tool Integrity** | Added provenance checking and registry verification on top of poisoning detection | Integrity is broader than toxicity — a non-poisoned tool from a sketchy registry is also risky |
| Data Exposure → **Data Exposure (session-aware)** | Added: "what data was accessed earlier in the session that could leak through this call" | The proxy sees session history — use it for exfiltration detection |
| Trustworthiness → **Agent Trust Modifier** | Demoted from dimension to modifier. Same data (DecodingTrust, TrustLLM, Trust Paradox), different role | A tool call's inherent risk doesn't change by model. But the likelihood of manipulation does. Modifier captures this |
| Permission Scope → **Permission Overreach** | Refocused from "how over-privileged is the tool" to "is the agent asking for more than this task needs" | The proxy can compare request scope to task requirements |
| Injection Resilience → **Injection Exposure** | Flipped perspective: from "how resilient is the model" to "is this call a vector for injection" | Resilience is a model property. Exposure is a call property. The proxy scores calls, not models |
| *(new)* **Cross-Tool Escalation** | Entirely new — tracks session patterns for escalation, exfiltration chains, parasitic toolchains | The proxy sees ALL calls in a session. v1 scored each call independently. v2 uses session context |

### 3.4 Side-by-Side Comparison

| Aspect | v1 (Ecosystem) | v2 (Agent-Boundary) |
|--------|---------------|---------------------|
| **Core question** | "What risks exist?" | "Is THIS call safe RIGHT NOW?" |
| **Perspective** | MCP ecosystem + LLM research | Proxy intercepting agent→tool requests |
| **Dimensions** | 8 standalone | 7 boundary + 1 modifier |
| **Input signals** | Mostly tool metadata | Tool metadata + request args + session history |
| **Session awareness** | None | Dim 7 tracks session-level escalation |
| **Agent trust** | Full dimension (D6) | Modifier (0.8-1.3×) — same data, better role |
| **Data coverage** | 22 benchmarks | 22 benchmarks (same data, refocused mapping) |
| **Data lost** | — | 0 rows. Reorganized, not discarded |

---

## 4. What Columns We Can Extract From Each Dataset

This section maps every dataset to the specific columns that feed each v2 dimension.

### 4.1 Dim 1: Tool Integrity — "Is this tool trustworthy?"

| Dataset | Columns We Use | How |
|---------|---------------|-----|
| MCPTox (04) | `tool_description_poisoned`, `tool_description_original`, `attack_paradigm` | Poisoning detection training: compare poisoned vs clean descriptions. Paradigm = severity ladder |
| MCP-ITP (10) | `poisoned_description`, `steering_words`, `detection_by_defense` | Implicit steering word extraction. The 0.3% detection rate = what other defenses miss |
| MCP Server DB (07) | `eit_flag`, `pat_flag`, `nat_flag`, `server_source` | Tool capability risk classification from real registries |
| 67K Dataset (09) | `registry_source`, `affix_squatting_group`, `credential_leakage` | Provenance verification: is this tool from a trusted registry? Known squatting? |
| Component PoC (08) | `attack_category`, `scanner_detection` | Detection difficulty calibration: 3.3% scanner detection = evasion baseline |

### 4.2 Dim 2: Request Sensitivity — "How dangerous is this request?"

| Dataset | Columns We Use | How |
|---------|---------------|-----|
| MCIP-Bench (01) | `risk_category`, `function_calls` (JSON) | Labeled request-level risk: function name + arguments → risk class |
| MCIP Guardian (02) | `risk_category` (11 classes), `class_label` | Primary training set: 13,830 labeled instances for request classification |
| MCP-AttackBench (03) | `binary_label`, `attack_family`, `cascade_stage` | Largest attack/benign pool: 70K samples. Cascade stage = escalation severity |
| MCPSecBench (05) | `attack_type` (17), `asr_per_trial` | Empirical ASR per attack type = ground-truth severity ranking |
| MCP-SafetyBench (06) | `domain`, `attack_type`, `asr` | Domain severity weighting: Financial > Repository > Browser > Navigation > Web |
| NVD/CVSS (11) | `description`, `cvss_base_score` | Description-to-score transfer learning: 31K labeled text→severity pairs |
| R-Judge (12) | `risk_type`, `risk_scenario`, `safety_label` | Multi-turn risk scenarios: 27 scenarios, 10 risk types |

### 4.3 Dim 3: Permission Overreach — "More access than needed?"

| Dataset | Columns We Use | How |
|---------|---------------|-----|
| MiniScope (17) | `api_method`, `granted_scopes`, `minimum_scopes`, `mismatch_rate` | Ground-truth: what scopes a method actually needs vs what's granted |
| 67K Dataset (09) | `permissions_per_server` (avg 17) | Ecosystem baseline for "normal" permission levels |
| MCP Server DB (07) | `tool_capability_flags` | What each tool can actually access |
| CVSS (11) | `privileges_required` (None/Low/High) | Severity weighting for different privilege levels |

### 4.4 Dim 4: Data Exposure — "What sensitive data flows through this call?"

| Dataset | Columns We Use | How |
|---------|---------------|-----|
| MCP Server DB (07) | `eit_flag`, `pat_flag`, `nat_flag`, `exploitable_combo_flag`, `parasitic_chain_member` | Tool-level data risk classification. 27.2% of servers have exploitable combinations |
| 67K Dataset (09) | `credential_leakage`, `server_hijacking` | Real-world credential exposure: 12 leaked credentials, 111+ hijacked servers |
| InjecAgent (14) | `harm_category` (direct/exfiltration), `attacker_tools` | Labeled exfiltration attempts: which tools enable data theft |
| CVSS (11) | `confidentiality_impact` (None/Low/High) | Impact severity weighting for data exposure |

### 4.5 Dim 5: Injection Exposure — "Is this call an injection channel?"

| Dataset | Columns We Use | How |
|---------|---------------|-----|
| AgentDojo (13) | `injection_task`, `defense_baseline`, `asr` | Defense effectiveness: ASR 41.2% → 2.2%. Baseline for "how much defense helps" |
| Indirect PI (18) | `obfuscation_type` (12), `model_vulnerability_rate` | 12 evasion techniques ranked by difficulty. Model-specific vulnerability profiles |
| Synthetic PI (22) | `attack_category` (10), `tivs`, `isr`, `pof`, `psr`, `ccs` | Composite injection scoring template: TIVS = ISR + POF + PSR + CCS |
| Meta Tool-Use PI (15) | `injection_technique` (7), `threat_category` (8) | Technique taxonomy: Direct Override, Authority, Hidden Commands, Role-Play, Logical Traps, Multi-Step, Conflicting |
| InjecAgent (14) | `user_tools`, `attacker_tools`, `injection_payload` | Tool-as-injection-vector: 17 user tools vs 62 attacker tools |
| ASB (16) | `attack_prompt_type` (6) | Input-level attack classification ranked by ASR |
| MCP-ITP (10) | `poisoned_description`, `attack_success` | Injection via tool description (not just via tool input) — 84.2% ASR |

### 4.6 Dim 6: Blast Radius — "How much damage if this goes wrong?"

| Dataset | Columns We Use | How |
|---------|---------------|-----|
| MCPSecBench (05) | `attack_surface`, `asr` | Surface→impact: Protocol=100%, Server=47%, Client=33%, Host=27% |
| Component PoC (08) | `protocol_amplification` (+23-41%) | MCP-specific damage multiplier |
| MCP-SafetyBench (06) | `domain` | Domain severity tiers: Financial=catastrophic, Web Search=contained |
| CVSS (11) | `integrity_impact`, `availability_impact`, `scope` | Proven blast radius formula from 31K labeled vulnerabilities |
| MCP-AttackBench (03) | `cascade_stage` (I/II/III) | Multi-stage damage escalation |

### 4.7 Dim 7: Cross-Tool Escalation — "Dangerous session pattern?"

| Dataset | Columns We Use | How |
|---------|---------------|-----|
| MCP Server DB (07) | `eit_flag`+`pat_flag`+`nat_flag` per tool, `parasitic_chain_member` | Toolchain combination risk: 90% success across 10 tested chains |
| MCPTox (04) | `attack_paradigm` (escalation ladder) | Multi-step attack progression: Explicit → Implicit-FH → Implicit-PT |
| R-Judge (12) | `risk_scenario`, `risk_type` (sequential) | Multi-turn interaction risk patterns |
| Trust Paradox (21) | `convergence_iterations`, `tci`, `safety_violation_rate` | Temporal drift over 8-15 turns |
| MCP-SafetyBench (06) | `dialogue_turn`, `attack_success` | Multi-turn sustained attack success rates |
| Component PoC (08) | `components` (5 modular types) | Compositional attack building blocks |

### 4.8 Agent Trust Modifier — "How susceptible is this agent model?"

| Dataset | Columns We Use | How |
|---------|---------------|-----|
| MCPTox (04) | `asr_per_model` | GPT-4o: 61.8%, Claude: 34.3% — model-specific vulnerability |
| MCP-ITP (10) | `target_llm`, `attack_success` | 12 models tested against implicit poisoning |
| Indirect PI (18) | `target_model`, `model_vulnerability_rate` | 28 models: grok-4 72.4%, GPT/Google ~0% |
| DecodingTrust (19) | `eval_dimension` (8), `trustworthiness_score` | Multi-dimensional trust profile: GPT-4/3.5 baselines |
| TrustLLM (20) | `trust_dimension` (6), `model_results` | 16 LLMs across 6 trust dimensions |
| Trust Paradox (21) | `capability_tier`, `tci`, `llm_backend` | Capability-trust miscalibration: TCI 0.72-0.89 |

---

## 5. The Scoring Pipeline

### 5.1 How It Works At Runtime

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Agent sends tools/call                           │
│    {"method": "tools/call", "params": {"name": "X", "arguments": {…}}} │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          MCP-RSS PROXY                                  │
│                                                                         │
│  ┌─────────────────────┐                                                │
│  │ STATIC LAYER        │  Dim 1: Tool Integrity (tool metadata)         │
│  │ (pre-computed)       │  Dim 3: Permission Overreach (schema)          │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│  ┌──────────▼──────────┐                                                │
│  │ DYNAMIC LAYER       │  Dim 2: Request Sensitivity (arguments)        │
│  │ (per-request)        │  Dim 4: Data Exposure (args + session)         │
│  │                      │  Dim 5: Injection Exposure (all signals)       │
│  │                      │  Dim 6: Blast Radius (metadata + args)         │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│  ┌──────────▼──────────┐                                                │
│  │ TEMPORAL LAYER      │  Dim 7: Cross-Tool Escalation (session hist.)  │
│  │ (session-aware)      │  Agent Trust Modifier (model identity)         │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│  ┌──────────▼──────────┐                                                │
│  │ SCORE COMPUTATION   │  Weighted combination → Base Score (1-10)      │
│  │                      │  × Agent Trust Modifier (0.8-1.3)             │
│  │                      │  = Final Risk Score                            │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│  ┌──────────▼──────────┐                                                │
│  │ DECISION            │  1-3: AUTO-ALLOW                               │
│  │                      │  4-6: ALLOW WITH LOGGING                      │
│  │                      │  7-8: REQUIRE HUMAN APPROVAL                  │
│  │                      │  9-10: AUTO-DENY                              │
│  └─────────────────────┘                                                │
└──────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Static vs Dynamic Dimensions

| Layer | Dimensions | When Computed | Cost |
|-------|-----------|--------------|------|
| **Static** | Dim 1 (Tool Integrity), Dim 3 (Permission Overreach) | Once per tool, cached | Very low — lookup + regex |
| **Dynamic** | Dim 2 (Request Sensitivity), Dim 4 (Data Exposure), Dim 5 (Injection Exposure), Dim 6 (Blast Radius) | Every request | Low-medium — classifier + pattern matching |
| **Temporal** | Dim 7 (Cross-Tool Escalation), Agent Trust Modifier | Accumulated per session | Low — sequence analysis |

---

## 6. Why This Is Novel

### 6.1 What Exists Today (All Binary)

| System | Output | Problem |
|--------|--------|---------|
| MCPShield (Zhou et al.) | `trusted` / `untrusted` | Binary — no severity gradation |
| MCP-Guard (Xing et al.) | `attack` / `benign` | Binary — no severity gradation |
| MCIP (Jing et al.) | Binary safety + 11-class type | Classification — still no risk score |
| Progent (Shi et al.) | Allow / Deny | Static policies — no dynamic context |
| AgentBound (Buhler et al.) | Permission manifest | Compliance check — binary |
| mcp-scan | Alert / No alert | Scanner — 3.3% detection rate |

### 6.2 What MCP-RSS Does Differently

1. **Graduated scoring (1-10)** — Operators set their own threshold. A security-conscious org
   blocks at 6. A research lab blocks at 9. Both use the same system.

2. **Dynamic, not static** — The score changes based on the specific request arguments, the
   session history, and the agent's behavior. Reading `/etc/passwd` scores differently than
   reading `weather.json`, even from the same tool.

3. **Session-aware** — Dim 7 (Cross-Tool Escalation) tracks patterns across calls. Reading
   credentials then calling a network tool triggers escalation. No existing system does this.

4. **Agent-boundary focused** — Every dimension evaluates the interaction between agent and
   tool, not the server or the model in isolation. The proxy sits at the exact point where
   risk materializes.

5. **Explainable** — Every score comes with a breakdown and justification. The operator knows
   WHY the score is 9.2, not just that it's high.

6. **Adapted from CVSS** — The cybersecurity industry trusts CVSS for vulnerability scoring.
   MCP-RSS adapts the same philosophy (multi-dimensional base metrics → composite score)
   to a new domain. This is a known methodology applied to a novel problem.

### 6.3 Research Questions Addressed

| RQ | Question | Which Dimensions Answer It |
|----|---------|---------------------------|
| RQ1 | Can LLMs produce accurate risk scores for MCP requests? | Dim 2 (trained on 118K+ labeled samples) |
| RQ2 | What are the right base metrics for MCP risk? | **All 7 dimensions + modifier = the formal answer** |
| RQ3 | Does multi-signal aggregation help? | 7 dims + modifier vs single-dim ablation |
| RQ4 | Does temporal tracking improve accuracy? | Dim 7 (Cross-Tool Escalation) vs static-only |
| RQ5 | Does graduated scoring preserve more utility? | 1-10 scale vs binary threshold comparison |

---

## 7. Data Support Summary

### 7.1 Dimension Data Grades

| Dimension | Datasets | Total Rows | Grade | Limiting Factor |
|-----------|----------|------------|-------|----------------|
| Dim 1: Tool Integrity | 5 | 80K+ | **A** | None — strongest MCP-specific coverage |
| Dim 2: Request Sensitivity | 7 | 118K+ | **A** | None — largest data pool |
| Dim 3: Permission Overreach | 4 | 67K+ | **B+** | MiniScope has only 10 apps (but ground-truth) |
| Dim 4: Data Exposure | 4 | 80K+ | **A** | Parasitic toolchain data is uniquely powerful |
| Dim 5: Injection Exposure | 7 | 4,400+ | **A** | Rows smaller but 7 diverse sources |
| Dim 6: Blast Radius | 5 | 100K+ | **A** | CVSS provides formula, MCP benchmarks calibrate |
| Dim 7: Cross-Tool Escalation | 6 | varied | **B+** | Temporal drift data thin (19 scenarios), rest strong |
| Agent Trust Modifier | 6 | 60+ sub-datasets | **A** | Well-profiled: 28 models across multiple benchmarks |

### 7.2 Total Coverage

- **22/22 benchmarks mapped** — no orphan datasets
- **0 rows discarded** — same data as v1, reorganized around the agent-tool boundary
- **Every dimension backed by 4+ datasets** — no single-source dependencies
- **All 5 research questions addressable** from the dimension structure

---

## 8. Example Scoring Walkthrough

### High-Risk Call: Agent writes to /etc/passwd

```
Request: filesystem_write(path="/etc/passwd", content="root:x:0:0:...")
Session: Agent previously called db.query("SELECT password FROM users")
Agent: GPT-4o
```

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| Dim 1: Tool Integrity | 3 | Tool from official registry, description matches behavior |
| Dim 2: Request Sensitivity | 9 | Writing to critical system file — top severity |
| Dim 3: Permission Overreach | 8 | filesystem_write has unrestricted path access, task only needs config read |
| Dim 4: Data Exposure | 9 | Previous call accessed passwords, now writing to auth file — exfiltration chain |
| Dim 5: Injection Exposure | 4 | No injection detected in arguments, but tool accepts arbitrary paths |
| Dim 6: Blast Radius | 9 | /etc/passwd write = system-wide, irreversible |
| Dim 7: Cross-Tool Escalation | 8 | db.query(passwords) → filesystem_write(/etc/passwd) = privilege escalation chain |
| **Base Score** | **7.1** | Weighted combination |
| Agent Trust Modifier | ×1.2 | GPT-4o: 61.8% ASR in MCPTox |
| **Final Score** | **8.5** | REQUIRE HUMAN APPROVAL |

### Low-Risk Call: Agent reads weather

```
Request: weather.get(city="London")
Session: First call in session
Agent: Claude
```

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| Dim 1: Tool Integrity | 2 | Official API, verified description |
| Dim 2: Request Sensitivity | 1 | Public data, read-only |
| Dim 3: Permission Overreach | 1 | Minimal scope, matches task |
| Dim 4: Data Exposure | 1 | Public weather data, no PII |
| Dim 5: Injection Exposure | 2 | Structured input, structured output |
| Dim 6: Blast Radius | 1 | Read-only, no system impact |
| Dim 7: Cross-Tool Escalation | 1 | First call, no session history |
| **Base Score** | **1.3** | |
| Agent Trust Modifier | ×0.8 | Claude: 34.3% ASR, high trust |
| **Final Score** | **1.0** | AUTO-ALLOW |

---

## 9. Dimension Evolution: v2 → v3 (Server-Defense Reframe)

### 9.1 Why v2 Needed Revision

The project description was clarified to: **"protects MCP servers from malicious or risky agent
behavior."** When v2's 7 dimensions were tested against this framing, 2 pointed the wrong direction:

| v2 Dimension | Problem |
|-------------|---------|
| Dim 1: Tool Integrity | Protects the **agent** from poisoned tools — not the server from the agent |
| Dim 5: Injection Exposure | Protects the **agent** from injection — not the server from the agent |

### 9.2 The v3 Dimension Set (6 + 1 Modifier)

Every dimension now answers: **"How does this agent threaten MY server?"**

| # | Dimension | Server's Question | Absorbs from v2 | Grade |
|---|-----------|------------------|-----------------|-------|
| 1 | **Agent Action Severity** | How dangerous is this request to my resources? | v2 Dim 2 (Request Sensitivity) + v2 Dim 6 (Blast Radius) | A (118K+) |
| 2 | **Permission Overreach** | Is the agent requesting more access than needed? | v2 Dim 3 (unchanged) | B+ (67K+) |
| 3 | **Data Exfiltration Risk** | How much of my sensitive data is at risk? | v2 Dim 4 (Data Exposure, refocused) | A (80K+) |
| 4 | **Cross-Tool Escalation** | Is this session showing escalating threats? | v2 Dim 7 (kept) | B+ (6 sources) |
| 5 | **Agent Compromise Indicator** | Is this agent acting under hostile influence? | v2 Dim 1 (Tool Integrity) + v2 Dim 5 (Injection Exposure) — **reframed** | A (9 sources) |
| 6 | **Resource Consumption Risk** | Is this agent abusing my server resources? | **NEW** — no v2 equivalent | D (rule-based) |
| Mod | **Agent Trust Modifier** | How much should I trust this agent? | v2 Modifier (reframed) | A (28+ models) |

### 9.3 The Key Reframe: Agent Compromise Indicator

v2 had Tool Integrity (protecting agent from poisoned tools) and Injection Exposure (protecting
agent from injection) as separate dimensions. v3 combines and inverts them:

> **A compromised agent is the server's problem.** Whether the agent was poisoned by a tool
> description, manipulated by prompt injection, or steered by adversarial input — the SERVER
> bears the consequences when it sends harmful requests.

The same data (MCPTox, MCP-ITP, AgentDojo, Indirect PI, etc.) is used, but the interpretation
flips from "protecting the agent" to "a vulnerable agent is a dangerous agent."

### 9.4 Updated Column Mappings (v3)

#### Dim 1: Agent Action Severity
| Dataset | Columns | How |
|---------|---------|-----|
| MCIP-Bench (01) | `risk_category`, `function_calls` (JSON) | Labeled request-level risk |
| MCIP Guardian (02) | `risk_category` (11 classes), `class_label` | Primary training set |
| MCP-AttackBench (03) | `binary_label`, `attack_family`, `cascade_stage` | Largest attack/benign pool |
| MCPSecBench (05) | `attack_type` (17), `attack_surface` (4), `asr_per_trial` | Severity + surface mapping |
| MCP-SafetyBench (06) | `domain`, `attack_type`, `asr` | Domain severity weighting |
| NVD/CVSS (11) | `description`, `cvss_base_score`, 8 sub-metrics | Scoring formula template |
| R-Judge (12) | `risk_type`, `risk_scenario`, `safety_label` | Multi-turn risk scenarios |
| Component PoC (08) | `protocol_amplification` (%) | MCP-specific damage multiplier |

#### Dim 5: Agent Compromise Indicator
| Dataset | Columns | How |
|---------|---------|-----|
| MCPTox (04) | `tool_description_poisoned`, `attack_paradigm`, `asr_per_model` | Poisoning exposure + model vulnerability |
| MCP-ITP (10) | `poisoned_description`, `steering_words`, `detection_by_defense` | Implicit poisoning detection (84.2% ASR) |
| AgentDojo (13) | `injection_task`, `defense_baseline`, `asr` | Defense effectiveness baseline |
| Indirect PI (18) | `obfuscation_type` (12), `model_vulnerability_rate` | 12 evasion techniques, 28 models |
| Synthetic PI (22) | `attack_category` (10), `tivs` | Composite injection scoring |
| Meta Tool-Use PI (15) | `injection_technique` (7), `threat_category` (8) | Technique taxonomy |
| InjecAgent (14) | `attacker_tools` (62), `harm_type` | Tool as injection vector |
| ASB (16) | `attack_prompt_type` (6) | Input-level attack classification |
| Component PoC (08) | `scanner_detection` (3.3%) | Evasion baseline |

### 9.5 Updated Scoring Pipeline (v3)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Agent sends tools/call                           │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          MCP-RSS PROXY                                  │
│                                                                         │
│  STATIC:    Dim 2: Permission Overreach (schema, cached per tool)       │
│  DYNAMIC:   Dim 1: Agent Action Severity (metadata + args)             │
│             Dim 3: Data Exfiltration Risk (args + session)             │
│             Dim 5: Agent Compromise Indicator (all signals)            │
│  TEMPORAL:  Dim 4: Cross-Tool Escalation (session history)             │
│             Dim 6: Resource Consumption Risk (session metrics)          │
│             Agent Trust Modifier (agent identity)                      │
│                                                                         │
│  → Base Score (1-10) × Modifier (0.7-1.4) = Final Score               │
│  → 1-3: AUTO-ALLOW | 4-6: LOG | 7-8: HUMAN APPROVAL | 9-10: DENY     │
└──────────────────────────────────────────────────────────────────────────┘
```

### 9.6 Updated JSON Output (v3)

```json
{
  "risk_score": 8.5,
  "risk_level": "HIGH",
  "dimensions": {
    "agent_action_severity": 9,
    "permission_overreach": 7,
    "data_exfiltration_risk": 8,
    "cross_tool_escalation": 6,
    "agent_compromise_indicator": 5,
    "resource_consumption_risk": 2
  },
  "agent_trust_modifier": 1.2,
  "base_score_before_modifier": 7.1,
  "justification": "Agent requesting filesystem_write to /etc/passwd (action_severity=9). Unrestricted path access beyond task needs (permission_overreach=7). Previous db.query accessed passwords — exfiltration vector (data_exfiltration=8). Escalating pattern: db_read → system file_write (escalation=6). GPT-4o has 61.8% MCPTox ASR (compromise=5, modifier=1.2).",
  "recommendation": "REQUIRE HUMAN APPROVAL",
  "confidence": 0.92
}
```

### 9.7 Updated Data Grades (v3)

| Dimension | Datasets | Total Rows | Grade |
|-----------|----------|------------|-------|
| Dim 1: Agent Action Severity | 8 | 118K+ | **A** |
| Dim 2: Permission Overreach | 4 | 67K+ | **B+** |
| Dim 3: Data Exfiltration Risk | 4 | 80K+ | **A** |
| Dim 4: Cross-Tool Escalation | 6 | varied | **B+** |
| Dim 5: Agent Compromise Indicator | 9 | 6K+ | **A** |
| Dim 6: Resource Consumption Risk | 3 | metadata | **D** |
| Agent Trust Modifier | 6 | 60+ sub-datasets | **A** |

---

## 10. What Comes Next

1. **Formalize the scoring formula** — Define weights for each dimension and the combination
   function (weighted average, geometric mean, or CVSS-style nonlinear formula).

2. **Build the static scorer** — Implement Dim 2 (Permission Overreach) using rule-based scope
   comparison. This can be cached per tool.

3. **Train the request classifier** — Use MCIP Guardian (13,830 samples) + MCP-AttackBench
   (70,448 samples) to train Dim 1 (Agent Action Severity).

4. **Implement session tracking** — Build the session history store for Dim 4
   (Cross-Tool Escalation) and Dim 6 (Resource Consumption Risk).

5. **Build the compromise detector** — Implement Dim 5 (Agent Compromise Indicator) using
   MCP-ITP steering word detection + injection pattern matching from Indirect PI/Meta Tool-Use PI.

6. **Create evaluation dataset** — ~500 MCP tool invocations manually scored 1-10 by annotators
   for ground-truth validation.

7. **Benchmark against existing systems** — Compare MCP-RSS detection rate vs MCPShield (95.3%),
   MCP-Guard (95.4% F1), and mcp-scan (3.3%).

Full v3 specification: see `dimension_refinement_v3_server_defense.md`.
