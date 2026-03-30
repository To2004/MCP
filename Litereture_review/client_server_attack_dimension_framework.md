# MCP Client→Server Attack Dimension Framework

## 1. Motivation

### Why This Framework

The MCP ecosystem now has **12 dedicated benchmarks** that evaluate attacks where a malicious or compromised MCP client attacks an MCP server. Each benchmark measures different aspects of the attack — some focus on attack types, others on protocol amplification, others on tool poisoning, and others on defense effectiveness.

No single benchmark covers all relevant dimensions. This framework synthesizes the 12 benchmarks into a **unified set of attack-characterization dimensions** — a structured way to describe, classify, and score any client→server attack along multiple axes simultaneously.

### The Core Question

> **"Along which dimensions should we characterize a client→server attack on an MCP server?"**

Each dimension answers a specific sub-question about the attack:

| Sub-Question | What It Captures |
|---|---|
| WHERE in the MCP lifecycle does it strike? | Attack Workflow Stage |
| HOW does the attack reach the server? | Attack Mechanism |
| WHAT damage does a successful attack cause? | Server Impact Category |
| HOW effective is this attack in practice? | Empirical Attack Success |
| CAN existing defenses stop this attack? | Defense Penetration |
| HOW hard is this attack to detect? | Attack Stealth |
| WHICH agent models are most exploitable? | Model Vulnerability Profile |

### How This Differs From Existing Frameworks

| Existing File | Perspective | Data Sources | This File |
|---|---|---|---|
| `dimension_refinement_v3_server_defense.md` | Server operator ("how does this agent threaten MY server?") | 22 benchmarks (attack + non-attack) | Attack analyst ("how do I fully characterize THIS attack?") |
| `benchmark_dimension_set_server_attack.md` | Server defense, benchmark-filtered subset of v3 | 11 benchmarks (filtered from 22) | Attack characterization, built bottom-up from 12 client→server benchmarks |
| `benchmark_refinement_server_attack_columns.md` | Column extraction from 7 core benchmarks | 7 + 2 secondary | Column extraction from all 12 client→server attack benchmarks |

The v3 framework asks: "How dangerous is this agent to my server?" — it scores incoming requests.

This framework asks: "How do I fully describe this attack?" — it characterizes attack patterns across multiple independent axes.

---

## 2. The 12 Source Benchmarks

| # | Benchmark | Scale | Client→Server Relevance | Key Contribution |
|---|---|---|---|---|
| 1 | **MSB** | 2,000 cases, 12 attacks | HIGH | 3-stage MCP workflow taxonomy, NRP metric, inverse scaling discovery |
| 2 | **MCPSecBench** | 17 attacks × 4 surfaces | HIGH | Attack surface severity with empirical ASR per platform |
| 3 | **MCPTox** | 1,312 cases, 45 real servers | MEDIUM | Tool poisoning paradigms, per-model ASR, <3% refusal rate |
| 4 | **MCP-SafetyBench** | 20 attacks × 5 domains | HIGH | Multi-turn multi-server attacks, domain impact weighting |
| 5 | **MCP-AttackBench** | 70,448 samples | MEDIUM | Largest labeled dataset, 3 attack families, cascade stages |
| 6 | **MCIP-Bench** | 11 categories, 10,633 pairs | MEDIUM | Version mismatch, replay injection, function-pair risk |
| 7 | **SafeMCP** | 5 metrics, 3 dimensions | MEDIUM | Passive + active defense evaluation, prompt fusion evasion |
| 8 | **ProtoAmp** | 847 scenarios, 5 servers | HIGH | Protocol amplification (+23-41%), 3 protocol vulnerabilities |
| 9 | **SHADE-Arena** | 17 task pairs, 340+ tools | LOW | Sabotage + evasion, covert side objectives |
| 10 | **MPMA** | Preference manipulation | LOW | Tool preference steering, DPMA technique |
| 11 | **MCP Safety Audit** | 4 PoC attacks | HIGH | First MCP-specific audit, all 4 attacks are client→server |
| 12 | **SAFE-MCP** | 80+ techniques, 14 tactics | MEDIUM | MITRE ATT&CK-mapped MCP threat taxonomy |

---

## 3. The Dimension Set: 6 Dimensions + 1 Modifier

### Overview

| # | Dimension | Core Question | Signal Source | Scale |
|---|---|---|---|---|
| 1 | **Attack Workflow Stage** | WHERE in the MCP lifecycle does the attack strike? | MCP layer / protocol phase | 1-10 |
| 2 | **Attack Mechanism** | HOW does the attack reach the server? | Attack technique taxonomy | 1-10 |
| 3 | **Server Impact Category** | WHAT damage does a successful attack cause? | Impact type + blast radius | 1-10 |
| 4 | **Empirical Attack Success** | HOW effective is this attack in practice? | ASR / NRP across models | 1-10 |
| 5 | **Defense Penetration** | CAN existing defenses stop this attack? | Defense bypass rate | 1-10 |
| 6 | **Attack Stealth** | HOW hard is this attack to detect? | Detection evasion signals | 1-10 |
| Mod | **Model Vulnerability Profile** | WHICH agent models are most exploitable? | Per-model ASR profiles | 0.7-1.4× |

### Attack Characterization Flow

```
Client→Server Attack Instance
        │
        ├─ Dim 1: Attack Workflow Stage      ← which MCP phase/layer is targeted
        ├─ Dim 2: Attack Mechanism            ← what technique delivers the attack
        ├─ Dim 3: Server Impact Category      ← what damage results if successful
        ├─ Dim 4: Empirical Attack Success    ← measured effectiveness (ASR)
        ├─ Dim 5: Defense Penetration         ← how well defenses hold up
        ├─ Dim 6: Attack Stealth              ← how detectable is the attack
        │
        ├─ Modifier: Model Vulnerability      ← which models are most susceptible
        │
        └─► Attack Profile Vector (6 scores + modifier)
```

### Why Each Dimension Is Independent

| Dimension | Independent Because |
|---|---|
| Attack Workflow Stage | An attack can target any MCP phase regardless of mechanism or impact |
| Attack Mechanism | The same mechanism (e.g., poisoning) can target different phases and cause different impacts |
| Server Impact Category | The same impact (e.g., credential theft) can come from different mechanisms at different stages |
| Empirical Attack Success | Effectiveness varies independently — a stealthy attack can fail; an obvious attack can succeed |
| Defense Penetration | Defense bypass is not determined by attack type alone — it depends on what defenses are deployed |
| Attack Stealth | An effective attack is not necessarily stealthy, and a stealthy attack is not necessarily effective |
| Model Vulnerability | Model susceptibility varies across all other dimensions — same attack, different model, different outcome |

---

## 4. Dimension Specifications

### Dim 1: Attack Workflow Stage

**Core question:** "WHERE in the MCP lifecycle does this attack strike?"

**What this dimension captures:**

The MCP protocol has distinct phases — tool discovery, tool invocation, response handling, and transport. Different attacks target different phases, and the phase determines what server resources are exposed and what defenses can be applied.

**Scale (1-10):**

| Score | Stage | Description | Benchmark Reference |
|---|---|---|---|
| 1-2 | Discovery/Registration | Attack manipulates tool metadata during registration or listing | MSB (Name Collision, Preference Manipulation) |
| 3-4 | Task Planning | Attack influences which tool the agent selects for a task | MSB (Prompt Injection in descriptions), MPMA (DPMA) |
| 5-6 | Tool Invocation | Attack delivers malicious parameters during tool execution | MSB (Out-of-Scope Parameter, Tool Transfer), MCIP-Bench (unauthorized function calls) |
| 7-8 | Response Handling | Attack exploits server response processing or post-execution logic | MSB (User Impersonation, False Error Escalation, Retrieval Injection) |
| 9-10 | Transport/Protocol | Attack exploits MCP protocol itself — DNS rebinding, capability attestation, trust propagation | MCPSecBench (DNS Rebinding), ProtoAmp (3 protocol vulns) |

**Data sources:**

| Benchmark | Rows/Units | What It Provides |
|---|---|---|
| MSB | 2,000 cases across 3 workflow stages | Explicit 3-stage taxonomy: Task Planning → Tool Invocation → Response Handling |
| MCPSecBench | 17 types × 4 surfaces | 4 attack surfaces: User, Client, Transport, Server |
| ProtoAmp | 847 scenarios | 3 protocol-level vulnerabilities with MCP-specific amplification |
| MCIP-Bench | 10,633 function pairs | Version mismatch and replay at invocation stage |
| MCP-SafetyBench | 20 types × 5 domains | Attack surface labels: server-side, host-side, user-side |
| SAFE-MCP | 80+ techniques | 14 MITRE ATT&CK-mapped tactic categories covering full attack lifecycle |
| MPMA | manipulation dataset | Registration-time preference manipulation |

**Key columns extractable from data:**

| Column | Source | Type |
|---|---|---|
| `workflow_stage` (planning / invocation / response) | MSB | categorical |
| `attack_surface` (user / client / transport / server) | MCPSecBench | categorical |
| `attack_surface` (server-side / host-side / user-side) | MCP-SafetyBench | categorical |
| `protocol_vulnerability_type` (attestation / sampling / trust) | ProtoAmp | categorical |
| `risk_category` (11 categories including version mismatch, replay) | MCIP-Bench | categorical |
| `tactic` (14 MITRE-mapped tactics) | SAFE-MCP | categorical |
| `manipulation_type` (DPMA) | MPMA | categorical |

**Derived signals:**

| Signal | Formula / Logic |
|---|---|
| `stage_severity_rank` | Transport/Protocol > Response > Invocation > Planning > Discovery |
| `surface_directness` | `1` if attack_surface ∈ {server-side, protocol-side, transport} else `0` |
| `lifecycle_coverage` | Count of distinct stages attacked in a single benchmark scenario |
| `stage_to_asr_correlation` | Map each stage to empirical ASR from MSB/MCPSecBench |

**Computation:** Classify attack by its primary MCP phase using MSB's 3-stage taxonomy as backbone. Cross-reference with MCPSecBench's 4-surface model and SAFE-MCP's 14-tactic lifecycle. Score = severity rank of the deepest phase reached.

**Grade: A** — 7 benchmarks contribute. MSB provides the clearest taxonomy. MCPSecBench and ProtoAmp add protocol-level granularity. SAFE-MCP provides full lifecycle coverage.

---

### Dim 2: Attack Mechanism

**Core question:** "HOW does the attack reach the server?"

**What this dimension captures:**

The delivery technique — what the attacker actually does to compromise the interaction between client and server. Two attacks can target the same MCP phase and cause the same damage, but use completely different mechanisms (e.g., direct parameter manipulation vs tool description poisoning).

**Scale (1-10):**

| Score | Mechanism | Description | Benchmark Reference |
|---|---|---|---|
| 1-2 | Preference Steering | Manipulates tool selection without altering tool behavior | MPMA (DPMA), MSB (Preference Manipulation) |
| 3-4 | Parameter Abuse | Sends out-of-scope or unauthorized parameters to server tools | MSB (74% ASR), MCIP-Bench (unauthorized calls) |
| 5-6 | Tool Description Poisoning | Injects malicious instructions into tool metadata | MCPTox (3 paradigms), MCP Safety Audit (RADE) |
| 7-8 | Cross-Server Propagation | Attack spreads across multiple MCP servers in a session | ProtoAmp (trust propagation), MCP-SafetyBench (multi-server) |
| 9-10 | Protocol Exploitation | Exploits MCP protocol design flaws — no auth, implicit trust, rebinding | ProtoAmp (3 vulns), MCPSecBench (DNS rebinding, CVE-2025-6514) |

**Data sources:**

| Benchmark | Rows/Units | What It Provides |
|---|---|---|
| MSB | 2,000 cases, 12 attack types | Taxonomy of 12 mechanisms across 3 stages, including Out-of-Scope Parameter (74% ASR) |
| MCPTox | 1,312 cases, 3 paradigms | Tool Poisoning Attack (TPA) with 3 sophistication levels: Explicit FH → Implicit FH → Implicit PT |
| MCP-AttackBench | 70,448 samples, 3 families | 3 attack families: Semantic & Adversarial, Protocol-Specific, Injection & Execution |
| ProtoAmp | 847 scenarios | 3 protocol vulnerabilities: no capability attestation, bidirectional sampling without auth, implicit trust propagation |
| MCPSecBench | 17 types | Command Injection, Sandbox Escape, Confused AI, DNS Rebinding, CVE-2025-6514 |
| MCIP-Bench | 10,633 function pairs | Version mismatch, replay injection, unauthorized function calls |
| MCP-SafetyBench | 20 attack types | Replay Injection, Excessive Privileges Misuse, cross-server patterns |
| MCP Safety Audit | 4 PoC attacks | Malicious Code Execution, RAC, Credential Theft, RADE |
| SAFE-MCP | 80+ techniques | 80+ attack techniques mapped to MITRE ATT&CK framework |
| MPMA | manipulation dataset | Direct Preference Manipulation Attack (DPMA) via tool names/descriptions |

**Key columns extractable from data:**

| Column | Source | Type |
|---|---|---|
| `attack_type` (12 types) | MSB | categorical |
| `attack_paradigm` (Explicit FH / Implicit FH / Implicit PT) | MCPTox | categorical |
| `attack_family` (Semantic / Protocol / Injection) | MCP-AttackBench | categorical |
| `attack_subtype` | MCP-AttackBench | categorical |
| `protocol_vulnerability` (attestation / sampling / trust) | ProtoAmp | categorical |
| `attack_type` (17 types) | MCPSecBench | categorical |
| `risk_category` (11 categories) | MCIP-Bench | categorical |
| `attack_type` (20 types) | MCP-SafetyBench | categorical |
| `attack_type` (MCE / RAC / CT / RADE) | MCP Safety Audit | categorical |
| `technique_id` (80+ techniques) | SAFE-MCP | categorical |
| `manipulation_type` (DPMA) | MPMA | categorical |

**Derived signals:**

| Signal | Formula / Logic |
|---|---|
| `mechanism_sophistication` | Implicit PT > Protocol exploit > Cross-server > Poisoning > Parameter abuse > Preference steering |
| `mechanism_to_asr_map` | Map each mechanism to empirical ASR from its source benchmark |
| `evasion_potential` | Higher for implicit paradigms (MCPTox), protocol-level (ProtoAmp), lower for direct parameter (MSB) |
| `unified_mechanism_taxonomy` | Merge MSB 12-type + MCPSecBench 17-type + MCP-AttackBench 3-family into unified hierarchy |

**Computation:**
1. Classify attack mechanism using the unified taxonomy (merge MSB, MCPSecBench, MCP-AttackBench type systems)
2. Map to sophistication level using MCPTox paradigm ladder as reference
3. Apply protocol amplification bonus from ProtoAmp when MCP-specific protocol features are exploited
4. Cross-reference with SAFE-MCP's 80+ technique IDs for fine-grained classification
5. Score = sophistication rank × protocol amplification factor

**Grade: A** — 10 of 12 benchmarks contribute mechanism data. This is the most broadly supported dimension. The challenge is taxonomy unification across overlapping type systems.

---

### Dim 3: Server Impact Category

**Core question:** "WHAT damage does a successful attack cause to the server?"

**What this dimension captures:**

The consequence of a successful attack — not how it was delivered (Dim 2) or how often it succeeds (Dim 4), but what happens to the server if the attack works. Two attacks with the same mechanism can cause very different impacts (e.g., poisoned tool descriptions leading to credential theft vs leading to preference steering).

**Scale (1-10):**

| Score | Impact Category | Description | Benchmark Reference |
|---|---|---|---|
| 1-2 | Behavioral Steering | Agent redirected to attacker's server, no direct server damage | MPMA, SHADE-Arena |
| 3-4 | Information Disclosure | Server leaks non-critical data or internal state | MCP-AttackBench (Resource Exfiltration), MCPTox (Privacy Leakage) |
| 5-6 | Credential Theft | Server credentials, API keys, SSH keys, env vars stolen | MCP Safety Audit (CT), MCP-SafetyBench, MCPTox |
| 7-8 | Persistent Access | Attacker gains ongoing access — SSH key injection, backdoor | MCP Safety Audit (RAC), MCP-SafetyBench (SSH key injection) |
| 9-10 | Code Execution / Sandbox Escape | Arbitrary command execution on server, container escape | MCP Safety Audit (MCE), MCPSecBench (Sandbox Escape, Command Injection), MCP-SafetyBench (reverse shell) |

**Data sources:**

| Benchmark | Rows/Units | What It Provides |
|---|---|---|
| MCP Safety Audit | 4 PoC attacks | 4 impact categories with PoC exploits: MCE (code exec), RAC (persistent access), CT (credential theft), RADE (chained impacts) |
| MCPSecBench | 17 types × 4 surfaces | Per-surface impact: Protocol=100% ASR, Server=47%, Client=33%, Host=27% |
| MCP-SafetyBench | 20 types × 5 domains | Domain-weighted impact: Financial (9-10) > Repository (8-9) > Browser (7-8) > Navigation (5-6) > Web Search (3-4). Host-side attacks >80% success |
| MCPTox | 1,312 cases, 11 risk categories | 11 impact categories: Privacy Leakage, Message Hijacking, SSH Key Exfiltration, etc. |
| MCP-AttackBench | 70,448 samples | Shadowing Attacks, Puppet Attacks, Resource Exfiltration via MCP Resources primitive |
| ProtoAmp | 847 scenarios | Cross-server impact amplification: +23-41% ASR over non-MCP baselines |
| SAFE-MCP | 14 tactic categories | MITRE ATT&CK impact categories: Execution, Persistence, Privilege Escalation, Credential Access, Exfiltration, Impact, C2 |
| SHADE-Arena | 17 task pairs | Covert side-objective completion: sabotage + evasion |
| SafeMCP | 5 evaluation metrics | 3 risk dimensions with 5 metrics measuring impact across them |

**Key columns extractable from data:**

| Column | Source | Type |
|---|---|---|
| `attack_type` (MCE / RAC / CT / RADE) | MCP Safety Audit | categorical |
| `attack_surface` + `asr_per_trial` | MCPSecBench | categorical + float |
| `domain` + `attack_type` + `asr` | MCP-SafetyBench | categorical + float |
| `risk_category` (11 categories) | MCPTox | categorical |
| `attack_family` + `binary_label` | MCP-AttackBench | categorical + binary |
| `protocol_amplification` (%) | ProtoAmp | float |
| `tactic` (14 MITRE-mapped) | SAFE-MCP | categorical |
| `sabotage_success_rate` | SHADE-Arena | float |
| `evaluation_metric` (5 metrics) | SafeMCP | float |

**Derived signals:**

| Signal | Formula / Logic |
|---|---|
| `impact_severity_rank` | Code Exec/Escape > Persistent Access > Credential Theft > Info Disclosure > Behavioral Steering |
| `domain_impact_weight` | Financial (×1.5) > Repository (×1.3) > Browser (×1.1) > Navigation (×0.8) > Web Search (×0.6) from MCP-SafetyBench |
| `surface_impact_weight` | Protocol (×2.0) > Server (×1.5) > Client (×1.0) > Host (×0.8) from MCPSecBench ASR |
| `chained_impact_flag` | `1` if RADE or multi-step impact chain detected (MCP Safety Audit, MCP-SafetyBench) |
| `amplified_impact_score` | Base impact × (1 + protocol_amplification/100) from ProtoAmp |

**Computation:**
1. Classify the primary impact category using MCP Safety Audit's 4-type taxonomy as backbone
2. Extend with MCPTox's 11 risk categories for finer granularity
3. Apply domain weighting from MCP-SafetyBench (financial impacts score higher)
4. Apply surface weighting from MCPSecBench (protocol-level impacts score higher)
5. Apply protocol amplification multiplier from ProtoAmp when applicable
6. Flag chained impacts (RADE) — multi-step chains score at the level of their worst individual impact

**Grade: A** — 9 of 12 benchmarks contribute impact data. MCP Safety Audit provides the clearest impact taxonomy. MCP-SafetyBench adds domain weighting. MCPSecBench adds surface weighting. ProtoAmp adds amplification. SAFE-MCP adds MITRE ATT&CK alignment.

---

### Dim 4: Empirical Attack Success

**Core question:** "HOW effective is this attack in practice?"

**What this dimension captures:**

The measured success rate of the attack — not theoretical risk (Dim 3), but actual empirical outcomes from benchmark evaluations. This dimension uses published ASR, NRP, and F1 scores from controlled experiments across multiple models and platforms.

**Scale (1-10):**

| Score | Effectiveness | Description | Benchmark Reference |
|---|---|---|---|
| 1-2 | Rarely succeeds | ASR < 10%, defenses consistently block it | ProtoAmp with AttestMCP (8.7%) |
| 3-4 | Occasionally succeeds | ASR 10-25%, some models/platforms resist | SHADE-Arena (best model 27%) |
| 5-6 | Moderately effective | ASR 25-45%, succeeds on most models with variation | MSB (avg 40.71%), MCP-SafetyBench (30-50%) |
| 7-8 | Highly effective | ASR 45-70%, most models vulnerable | MCPTox (GPT-4o 61.8%), MSB (Out-of-Scope 74%) |
| 9-10 | Near-certain success | ASR > 70%, bypasses safety guardrails, universal vulnerability | MCPTox (o1-mini 72.8%), MCPSecBench (85%+ ≥1 platform), MCP-SafetyBench (host-side >80%) |

**Data sources:**

| Benchmark | Rows/Units | What It Provides |
|---|---|---|
| MSB | 2,000 cases, 9 LLMs | Per-attack-type ASR: Out-of-Scope 74.03%, User Impersonation 50.72%, False Error 43.42%. Average 40.71%. NRP metric |
| MCPTox | 1,312 cases, 20 LLMs | Per-model ASR: o1-mini 72.8%, GPT-4o 61.8%, Claude 34.3%. Refusal rate <3% |
| MCPSecBench | 17 types, 3 platforms | 85%+ attacks compromised ≥1 platform. Per-surface ASR: Protocol=100%, Server=47%, Client=33%, Host=27% |
| MCP-SafetyBench | 20 types, 13 models | ASR 30-50% across models. Host-side attacks >80% success. No model immune |
| ProtoAmp | 847 scenarios | MCP amplifies ASR by +23-41% vs non-MCP baselines. System prompt defense: 61.3% → 47.2% |
| MCP-AttackBench | 70,448 samples | MCP-Guard detection: 96.01% accuracy, 95.4% F1 — provides defense baseline |
| SHADE-Arena | 17 task pairs | Best model (Claude 3.7 Sonnet) at 27% for covert sabotage |
| MCP Safety Audit | 4 PoC attacks, 2 models | Both Claude 3.7 and Llama-3.3-70B susceptible to all 3 direct attacks. RADE works even with guardrails |

**Key columns extractable from data:**

| Column | Source | Type |
|---|---|---|
| `asr` (per attack type) | MSB | float |
| `nrp` (Net Resilient Performance) | MSB | float |
| `asr_per_model` | MCPTox | float |
| `refusal_rate` | MCPTox | float |
| `asr_per_trial` | MCPSecBench | float |
| `asr` + `tsr` + `dsr` | MCP-SafetyBench | float |
| `protocol_amplification` (%) | ProtoAmp | float |
| `accuracy` + `f1` | MCP-AttackBench | float |
| `sabotage_success_rate` | SHADE-Arena | float |
| `attack_success` (per model, per attack type) | MCP Safety Audit | binary |

**Derived signals:**

| Signal | Formula / Logic |
|---|---|
| `normalized_asr` | Map benchmark-specific ASR to unified 0-100% scale |
| `cross_benchmark_asr` | Weighted average of ASR across benchmarks that test the same attack type |
| `inverse_scaling_flag` | `1` if stronger models show higher ASR (MSB, MCPTox confirmed) |
| `universal_vulnerability_flag` | `1` if no tested model is immune (MCP-SafetyBench confirmed) |
| `amplification_delta` | MCP ASR − non-MCP baseline ASR from ProtoAmp (+23-41%) |
| `nrp_score` | PUA × (1 − ASR) from MSB — utility-adjusted attack effectiveness |

**Computation:**
1. Collect ASR values from all benchmarks that tested this attack type
2. Normalize to 0-100% scale (some benchmarks report binary success, others continuous ASR)
3. Compute weighted cross-benchmark ASR (weight by dataset size and methodology rigor)
4. Check for inverse scaling (flag if stronger models are more vulnerable — MSB and MCPTox both confirm)
5. Apply protocol amplification from ProtoAmp when applicable (+23-41%)
6. Score = map normalized cross-benchmark ASR to 1-10 scale

**Key finding across benchmarks:** Average ASR across all 12 benchmarks is approximately **40-50%**. The inverse scaling phenomenon — stronger, more capable models being MORE vulnerable — is independently confirmed by MSB and MCPTox. No model tested across MCP-SafetyBench's 13-model evaluation was immune.

**Grade: A** — 8 of 12 benchmarks provide empirical success rate data. ASR is the most consistently reported metric. Cross-benchmark validation strengthens confidence. The inverse scaling finding is independently replicated.

---

### Dim 5: Defense Penetration

**Core question:** "CAN existing defenses stop this attack?"

**What this dimension captures:**

How well current defensive measures perform against the attack. This is not about the attack's inherent effectiveness (Dim 4), but specifically about whether deployed defenses reduce its success rate. A highly effective attack (Dim 4 = 9) might be easy to defend against (Dim 5 = 2) if the right defense exists, or vice versa.

**Scale (1-10):**

| Score | Penetration Level | Description | Benchmark Reference |
|---|---|---|---|
| 1-2 | Fully blocked | Defense reduces ASR to <10% | ProtoAmp AttestMCP (8.7%), MCP-AttackBench MCP-Guard (96% detection) |
| 3-4 | Mostly blocked | Defense reduces ASR by 60-80% | SafeMCP active defense (content filtering) |
| 5-6 | Partially blocked | Defense reduces ASR by 30-60%, significant residual risk | ProtoAmp system prompt (61.3% → 47.2%) |
| 7-8 | Weakly blocked | Defense reduces ASR by <30% | MCPSecBench (defenses <30% effective overall) |
| 9-10 | Bypasses all defenses | No tested defense materially reduces ASR | MCPTox (<3% refusal), MCP Safety Audit (RADE works with guardrails) |

**Data sources:**

| Benchmark | Rows/Units | What It Provides |
|---|---|---|
| MCPSecBench | 17 types, defenses tested | MCIP-Guardian and Firewalled-Agentic-Networks (FAN) tested — both <30% effective |
| MCP-AttackBench | 70,448 samples | MCP-Guard achieves 96.01% accuracy, 95.4% F1 — strongest defense result |
| ProtoAmp | 847 scenarios | System prompt defense: 61.3% → 47.2% ASR. AttestMCP protocol extension: 8.7% |
| SafeMCP | 5 metrics | Passive defense (whitelisting, post-hoc detection) + active defense (content filtering). Prompt fusion technique tested |
| MCP Safety Audit | 4 PoC attacks | RADE works even with safety guardrails — defense bypass confirmed |
| MCPTox | 1,312 cases | Refusal rate <3% even for Claude 3.7 Sonnet — model-level defense almost nonexistent |
| MCIP-Bench | 10,633 pairs | MCIP-Guardian trained model as defensive baseline |

**Key columns extractable from data:**

| Column | Source | Type |
|---|---|---|
| `defense_type` (MCIP-Guardian / FAN) | MCPSecBench | categorical |
| `defense_effectiveness` (%) | MCPSecBench | float |
| `accuracy` + `f1` + `precision` + `recall` | MCP-AttackBench | float |
| `asr_with_defense` + `asr_without_defense` | ProtoAmp | float |
| `defense_type` (passive / active) | SafeMCP | categorical |
| `safety_prompt_effective` | MCP-SafetyBench | binary |
| `refusal_rate` | MCPTox | float |
| `guardrail_bypass` (boolean) | MCP Safety Audit | binary |
| `dsr` (Defense Success Rate) | MCP-SafetyBench | float |

**Derived signals:**

| Signal | Formula / Logic |
|---|---|
| `defense_reduction_ratio` | (ASR_without − ASR_with) / ASR_without |
| `residual_asr` | ASR after best available defense |
| `defense_type_effectiveness_map` | Map each defense type to its empirical effectiveness across benchmarks |
| `promptable_flag` | `1` if safety prompts materially reduce ASR (MCP-SafetyBench) |
| `defense_ceiling` | Max effectiveness achieved across all tested defenses for this attack type |

**Computation:**
1. Collect defense effectiveness data from all benchmarks that tested defenses against this attack type
2. Compute defense reduction ratio = (pre-defense ASR − post-defense ASR) / pre-defense ASR
3. Identify best available defense and its residual ASR
4. Score = inverse of defense ceiling (high penetration = low defense effectiveness)
5. Special cases: if no defense tested → score 8 (unknown = assume high penetration); if refusal rate <5% → score 9-10

**Key finding across benchmarks:** The defense landscape is heavily polarized. MCP-Guard (MCP-AttackBench) achieves 96% detection for its specific attack types. AttestMCP (ProtoAmp) drops protocol-level attacks to 8.7%. But general-purpose defenses (MCPSecBench: <30%, MCPTox: <3% refusal) fail badly. This means defense effectiveness is **highly attack-type-specific** — there is no universal defense.

**Grade: B+** — 7 of 12 benchmarks provide defense data. The data is strong but heterogeneous (different defense types, different evaluation methods). The key insight about attack-type-specific defense effectiveness is well-supported.

---

### Dim 6: Attack Stealth

**Core question:** "HOW hard is this attack to detect before or during execution?"

**What this dimension captures:**

The difficulty of identifying the attack — whether the attack is designed to evade detection, whether it triggers safety guardrails, and whether existing scanners catch it. An attack can be highly effective (Dim 4) but also highly detectable (low stealth), or moderately effective but nearly invisible (high stealth).

**Scale (1-10):**

| Score | Stealth Level | Description | Benchmark Reference |
|---|---|---|---|
| 1-2 | Obvious | Direct malicious parameters, easily flagged by pattern matching | MSB (Out-of-Scope Parameter — obvious but 74% ASR) |
| 3-4 | Low stealth | Attack visible in request or tool call arguments with basic inspection | MCP Safety Audit (direct MCE, RAC, CT are identifiable) |
| 5-6 | Moderate stealth | Attack embedded in normal-looking requests, requires deeper analysis | MCP-AttackBench (Stage II cascade), MCIP-Bench (replay) |
| 7-8 | High stealth | Attack uses implicit techniques, prompt fusion, or covert channels | MCPTox (Implicit PT paradigm), SafeMCP (prompt fusion), SHADE-Arena |
| 9-10 | Near-invisible | Attack exploits protocol design, no payload to inspect, indistinguishable from legitimate use | ProtoAmp (protocol-level trust exploitation), MCPTox (<3% refusal, 0.3% MCP-ITP detection) |

**Data sources:**

| Benchmark | Rows/Units | What It Provides |
|---|---|---|
| MCPTox | 1,312 cases, 3 paradigms | 3-level stealth ladder: Explicit FH (low stealth) → Implicit FH (medium) → Implicit PT (high). Refusal rate <3% — models do not detect the attack |
| MCP-AttackBench | 70,448 samples, 3 stages | 3-stage cascade: Stage I (surface-level) → Stage II (schema-embedded) → Stage III (semantic-level evasion) |
| SafeMCP | 5 metrics | Prompt fusion technique specifically designed to hide injected attacks |
| SHADE-Arena | 17 task pairs | Evaluates both sabotage success AND evasion — agent must accomplish covert goals without being caught |
| ProtoAmp | 847 scenarios | Protocol-level attacks have no inspectable payload — they exploit trust architecture, not request content |
| MCP Safety Audit | 4 PoC attacks | RADE is stealthier than direct attacks (multi-server indirection) |
| MPMA | manipulation dataset | Manipulative words in tool names/descriptions — subtle semantic attacks |

**Key columns extractable from data:**

| Column | Source | Type |
|---|---|---|
| `attack_paradigm` (Explicit / Implicit FH / Implicit PT) | MCPTox | categorical (stealth ladder) |
| `cascade_stage` (I / II / III) | MCP-AttackBench | categorical (evasion depth) |
| `refusal_rate` | MCPTox | float (low = stealthy) |
| `prompt_fusion_technique` | SafeMCP | binary |
| `evasion_success_rate` | SHADE-Arena | float |
| `scanner_detection` | ProtoAmp (referenced from Component PoC: 3.3%) | float (low = stealthy) |
| `attack_type` (direct vs RADE) | MCP Safety Audit | categorical (indirection level) |
| `runtime_latency` | MCP-AttackBench | float (detection window) |

**Derived signals:**

| Signal | Formula / Logic |
|---|---|
| `stealth_paradigm_score` | Implicit PT (9) > Implicit FH (7) > Explicit FH (4) from MCPTox |
| `cascade_evasion_score` | Stage III (9) > Stage II (6) > Stage I (3) from MCP-AttackBench |
| `refusal_inverse` | 10 × (1 − refusal_rate) — lower refusal = higher stealth |
| `detection_gap` | 1 − scanner_detection_rate — Component PoC scanner: 3.3% detection → 96.7% gap |
| `evasion_composite` | Weighted combination of paradigm + cascade + refusal + scanner signals |

**Computation:**
1. Classify attack stealth using MCPTox's 3-paradigm ladder as primary reference
2. Cross-reference with MCP-AttackBench's cascade stage for evasion depth
3. Apply refusal rate data — attacks with <5% refusal rate score 8+
4. Apply scanner detection data — attacks with <10% detection rate score 9+
5. Check for prompt fusion (SafeMCP) or protocol-level exploitation (ProtoAmp) — both add stealth bonus
6. Score = max(paradigm_score, cascade_score, refusal_inverse, detection_gap)

**Grade: B+** — 7 of 12 benchmarks contribute stealth signals. MCPTox and MCP-AttackBench provide the strongest structured stealth ladders. The refusal rate data (<3%) is a powerful signal. Protocol-level stealth (ProtoAmp) is conceptually strong but harder to quantify on a 1-10 scale.

---

## 5. Model Vulnerability Profile (Modifier)

**Core question:** "WHICH agent models are most exploitable as attack vectors against the server?"

**Why it is a modifier, not a dimension:**

The model sending the request affects the *probability* of an attack succeeding but does not change the attack's inherent characteristics. The same Out-of-Scope Parameter attack (Dim 1: Invocation, Dim 2: Parameter Abuse, Dim 3: varies, Dim 6: low stealth) gets the same base scores regardless of model. But the probability that the model executes the attack varies dramatically: o1-mini 72.8% vs Claude 34.3% (MCPTox).

**How it works:**

```
Attack Profile Score = Base Score (from 6 dims) × Model Vulnerability Modifier
```

| Vulnerability Tier | Modifier | Basis |
|---|---|---|
| Low vulnerability | 0.7× | MCPTox ASR <30%, strong refusal rates, top defense benchmarks |
| Moderate vulnerability | 0.85× | MCPTox ASR 30-45%, moderate refusal rates |
| Standard / Unknown | 1.0× | No per-model data available — default assumption |
| High vulnerability | 1.2× | MCPTox ASR 45-65%, low refusal, inverse scaling confirmed |
| Very high vulnerability | 1.4× | MCPTox ASR >65%, near-zero refusal, consistently vulnerable across benchmarks |

**Data sources:**

| Benchmark | Models Tested | What It Provides |
|---|---|---|
| MSB | 9 LLMs | Per-model ASR across 12 attack types. Inverse scaling: stronger models more vulnerable |
| MCPTox | 20 LLMs | Per-model ASR: o1-mini 72.8%, GPT-4o 61.8%, Claude 3.7 Sonnet 34.3%. Refusal rate <3% across all |
| MCP-SafetyBench | 13 models | ASR 30-50% range. No model immune. Per-domain per-model breakdown |
| MCPSecBench | 3 platforms | Claude Desktop, GPT-4.1, Cursor v2.3.29 — platform-specific vulnerability |
| ProtoAmp | multiple models | MCP amplifies model-specific vulnerability by +23-41% |
| SHADE-Arena | multiple models | Best model (Claude 3.7 Sonnet) 27% for covert sabotage |

**Key columns extractable from data:**

| Column | Source | Type |
|---|---|---|
| `asr_per_model` (per attack type) | MSB | float |
| `asr_per_model` (per paradigm) | MCPTox | float |
| `refusal_rate` (per model) | MCPTox | float |
| `target_llm` + `asr` + `tsr` + `dsr` | MCP-SafetyBench | categorical + float |
| `target_client` + `asr_per_trial` | MCPSecBench | categorical + float |
| `sabotage_success_rate` (per model) | SHADE-Arena | float |

**Derived signals:**

| Signal | Formula / Logic |
|---|---|
| `model_mean_asr` | Average ASR across all tested attack types for a given model |
| `model_refusal_rate` | Inverse indicator — lower refusal = higher vulnerability |
| `inverse_scaling_coefficient` | Correlation between model capability ranking and ASR (positive = inverse scaling) |
| `cross_benchmark_vulnerability` | Weighted average of model ASR across MSB + MCPTox + MCP-SafetyBench |
| `model_vulnerability_tier` | Classify into 5 tiers based on cross-benchmark vulnerability |

**Key finding across benchmarks:** The **inverse scaling effect** — stronger, more capable models being MORE susceptible to MCP client→server attacks — is independently confirmed by MSB (9 LLMs) and MCPTox (20 LLMs). This means the most capable agent models deployed in production are likely the most exploitable.

**Grade: A** — 6 of 12 benchmarks provide per-model data. MCPTox (20 LLMs) and MCP-SafetyBench (13 models) provide the broadest coverage. The inverse scaling finding is independently replicated and has major practical implications.

---

## 6. Benchmark Coverage Matrix

| Benchmark | D1 Stage | D2 Mechanism | D3 Impact | D4 Success | D5 Defense | D6 Stealth | Modifier |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| MSB | x | x | | x | | x | x |
| MCPSecBench | x | x | x | x | x | | x |
| MCPTox | | x | x | x | x | x | x |
| MCP-SafetyBench | x | x | x | x | x | | x |
| MCP-AttackBench | | x | x | x | x | x | |
| MCIP-Bench | x | x | | | x | x | |
| SafeMCP | | | x | | x | x | |
| ProtoAmp | x | x | x | x | x | x | x |
| SHADE-Arena | | | x | x | | x | |
| MPMA | x | x | x | | | x | |
| MCP Safety Audit | | x | x | x | x | x | |
| SAFE-MCP | x | x | x | | | | |

**Coverage statistics:**

| Metric | Value |
|---|---|
| Benchmarks per dimension (avg) | 7.5 |
| Benchmarks per dimension (min) | 6 (Dim 1, Dim 6) |
| Benchmarks per dimension (max) | 10 (Dim 2) |
| Dimensions per benchmark (avg) | 4.4 |
| Dimensions per benchmark (min) | 3 (SHADE-Arena, SafeMCP) |
| Dimensions per benchmark (max) | 7 (ProtoAmp) |
| Orphan benchmarks | **0** — every benchmark feeds at least 3 dimensions |

---

## 7. Data Support Summary

| Dimension | Benchmarks Contributing | Total Rows/Units | Grade | Strongest Sources |
|---|---|---|---|---|
| Dim 1: Attack Workflow Stage | 7 | 85K+ (MSB 2K + MCPSecBench 765 + ProtoAmp 847 + MCIP-Bench 10.6K + MCP-SafetyBench multi + SAFE-MCP 80+ + MPMA) | **A** | MSB (explicit 3-stage), MCPSecBench (4-surface), SAFE-MCP (lifecycle) |
| Dim 2: Attack Mechanism | 10 | 88K+ (MSB 2K + MCPTox 1.3K + MCP-AttackBench 70.4K + ProtoAmp 847 + MCPSecBench 765 + MCIP-Bench 10.6K + MCP-SafetyBench multi + MCP Safety Audit 4 + SAFE-MCP 80+ + MPMA) | **A** | MCP-AttackBench (largest), MSB (12-type taxonomy), SAFE-MCP (80+ techniques) |
| Dim 3: Server Impact Category | 9 | 76K+ (MCP Safety Audit 4 + MCPSecBench 765 + MCP-SafetyBench multi + MCPTox 1.3K + MCP-AttackBench 70.4K + ProtoAmp 847 + SAFE-MCP 80+ + SHADE-Arena 17 + SafeMCP 5) | **A** | MCP Safety Audit (clearest taxonomy), MCP-SafetyBench (domain weighting) |
| Dim 4: Empirical Attack Success | 8 | 77K+ (MSB 2K + MCPTox 1.3K + MCPSecBench 765 + MCP-SafetyBench multi + ProtoAmp 847 + MCP-AttackBench 70.4K + SHADE-Arena 17 + MCP Safety Audit 4) | **A** | MSB (NRP metric), MCPTox (20 LLMs), MCP-SafetyBench (13 models) |
| Dim 5: Defense Penetration | 7 | 83K+ (MCPSecBench 765 + MCP-AttackBench 70.4K + ProtoAmp 847 + SafeMCP 5 + MCP Safety Audit 4 + MCPTox 1.3K + MCIP-Bench 10.6K) | **B+** | MCP-AttackBench (96% MCP-Guard), ProtoAmp (AttestMCP 8.7%) |
| Dim 6: Attack Stealth | 7 | 73K+ (MCPTox 1.3K + MCP-AttackBench 70.4K + SafeMCP 5 + SHADE-Arena 17 + ProtoAmp 847 + MCP Safety Audit 4 + MPMA) | **B+** | MCPTox (3-paradigm ladder), MCP-AttackBench (cascade stages) |
| Model Vulnerability Profile | 6 | 5K+ (MSB 2K + MCPTox 1.3K + MCP-SafetyBench multi + MCPSecBench 765 + ProtoAmp 847 + SHADE-Arena 17) | **A** | MCPTox (20 LLMs), MCP-SafetyBench (13 models) |

---

## 8. Unified Column Map

These are the highest-value column groups across all 12 benchmarks for attack characterization:

| Column Group | Best Benchmarks | Dimension(s) Served |
|---|---|---|
| `workflow_stage` / `attack_surface` | MSB, MCPSecBench, MCP-SafetyBench | Dim 1 (Stage) |
| `attack_type` / `attack_family` / `technique_id` | MSB, MCP-AttackBench, MCPSecBench, MCP-SafetyBench, SAFE-MCP | Dim 2 (Mechanism) |
| `risk_category` / `tactic` / `impact_type` | MCPTox, MCP Safety Audit, SAFE-MCP, MCP-AttackBench | Dim 3 (Impact) |
| `asr` / `nrp` / `attack_success` | MSB, MCPTox, MCPSecBench, MCP-SafetyBench, ProtoAmp | Dim 4 (Success) |
| `defense_type` / `defense_effectiveness` / `dsr` | MCPSecBench, MCP-AttackBench, ProtoAmp, SafeMCP, MCP-SafetyBench | Dim 5 (Defense) |
| `attack_paradigm` / `cascade_stage` / `refusal_rate` | MCPTox, MCP-AttackBench, SHADE-Arena | Dim 6 (Stealth) |
| `asr_per_model` / `target_llm` / `refusal_rate` | MCPTox, MSB, MCP-SafetyBench, MCPSecBench | Modifier (Model) |
| `domain` / `attack_surface` severity weights | MCP-SafetyBench, MCPSecBench | Cross-dimensional weighting |
| `protocol_amplification` (%) | ProtoAmp | Cross-dimensional amplification |

---

## 9. Example Attack Profile

### Example: Out-of-Scope Parameter Attack (MSB)

```
Attack: Agent sends unauthorized parameters to server tool
Source: MSB benchmark, 74.03% ASR
```

| Dimension | Score | Reasoning |
|---|---|---|
| Dim 1: Attack Workflow Stage | 5 | Tool Invocation stage — parameters sent during tool execution |
| Dim 2: Attack Mechanism | 4 | Parameter Abuse — direct unauthorized parameter injection |
| Dim 3: Server Impact Category | 6 | Varies: can lead to credential access or data disclosure depending on tool |
| Dim 4: Empirical Attack Success | 8 | 74.03% ASR — highest in MSB benchmark |
| Dim 5: Defense Penetration | 8 | No defense specifically tested against this in MSB |
| Dim 6: Attack Stealth | 2 | Obvious — out-of-scope parameters detectable by schema validation |
| **Base Profile** | **(5, 4, 6, 8, 8, 2)** | High success, low stealth, invocation-stage parameter abuse |
| Model Modifier | ×1.2 | Inverse scaling — stronger models more susceptible |
| **Adjusted Profile** | **(6, 4.8, 7.2, 9.6, 9.6, 2.4)** | |

### Example: Implicit Tool Poisoning (MCPTox Implicit PT)

```
Attack: Poisoned tool description steers agent to exfiltrate credentials via legitimate tools
Source: MCPTox, o1-mini 72.8% ASR, <3% refusal
```

| Dimension | Score | Reasoning |
|---|---|---|
| Dim 1: Attack Workflow Stage | 3 | Task Planning stage — poisoned description influences tool selection |
| Dim 2: Attack Mechanism | 6 | Tool Description Poisoning — Implicit PT paradigm (highest sophistication) |
| Dim 3: Server Impact Category | 6 | Credential Theft — SSH key exfiltration via legitimate filesystem tool |
| Dim 4: Empirical Attack Success | 8 | o1-mini 72.8% ASR; GPT-4o 61.8% |
| Dim 5: Defense Penetration | 9 | <3% refusal rate — model-level defense almost nonexistent |
| Dim 6: Attack Stealth | 9 | Implicit PT paradigm + <3% refusal + poisoned tool never executes |
| **Base Profile** | **(3, 6, 6, 8, 9, 9)** | Early-stage, highly stealthy, defense-bypassing poisoning attack |
| Model Modifier | ×1.4 | o1-mini: very high vulnerability (72.8% ASR) |
| **Adjusted Profile** | **(4.2, 8.4, 8.4, 11.2→10, 12.6→10, 12.6→10)** | Cap at 10 |

### Example: Protocol Trust Propagation (ProtoAmp)

```
Attack: Implicit trust propagation in multi-server config enables cross-server attack
Source: ProtoAmp, +23-41% amplification vs non-MCP
```

| Dimension | Score | Reasoning |
|---|---|---|
| Dim 1: Attack Workflow Stage | 10 | Transport/Protocol layer — exploits MCP protocol trust architecture |
| Dim 2: Attack Mechanism | 9 | Protocol Exploitation — implicit trust propagation, no auth verification |
| Dim 3: Server Impact Category | 8 | Cross-server persistent access — attacker moves laterally |
| Dim 4: Empirical Attack Success | 7 | +23-41% amplification; system prompt drops to 47.2% but AttestMCP drops to 8.7% |
| Dim 5: Defense Penetration | 5 | AttestMCP works (8.7%) but not widely deployed; system prompt partially effective |
| Dim 6: Attack Stealth | 9 | Protocol-level — no inspectable payload, exploits trust architecture |
| **Base Profile** | **(10, 9, 8, 7, 5, 9)** | Protocol-level, high stealth, high impact, but effective defense exists |
| Model Modifier | ×1.0 | Protocol-level attack — model less relevant |
| **Adjusted Profile** | **(10, 9, 8, 7, 5, 9)** | Unchanged |

---

## 10. Cross-Benchmark Insights

### Insight 1: Inverse Scaling Is Universal

| Benchmark | Finding |
|---|---|
| MSB | Stronger models more vulnerable across 12 attack types |
| MCPTox | o1-mini (72.8%) > GPT-4o (61.8%) > Claude (34.3%) |
| MCP-SafetyBench | No model immune; ASR 30-50% across 13 models |

**Implication:** The most capable agent models deployed in enterprise MCP environments are the most exploitable. This means model capability cannot be used as a proxy for safety.

### Insight 2: Defense Effectiveness Is Attack-Type-Specific

| Defense | What It Blocks | What It Misses |
|---|---|---|
| MCP-Guard (MCP-AttackBench) | 96% of request-level attacks | Protocol-level, multi-turn, poisoning |
| AttestMCP (ProtoAmp) | 91.3% of protocol-level attacks | Request-level, poisoning |
| System prompts (ProtoAmp) | Reduces ASR from 61.3% to 47.2% | Still 47.2% residual |
| MCIP-Guardian / FAN (MCPSecBench) | <30% overall | Most attack types |
| Model refusal (MCPTox) | <3% of poisoning attacks | Almost everything |

**Implication:** No single defense layer is sufficient. The 12 benchmarks collectively demonstrate that effective MCP server defense requires attack-type-specific countermeasures — a scoring framework must assess which defense layer is appropriate for each attack type.

### Insight 3: Protocol Amplification Is the MCP-Specific Threat Multiplier

ProtoAmp demonstrates that MCP's protocol design amplifies attack success by 23-41% compared to non-MCP baselines. The three protocol vulnerabilities — no capability attestation, bidirectional sampling without origin auth, and implicit trust propagation — are structural, not behavioral. They cannot be fixed by improving model safety alone.

### Insight 4: Stealth and Effectiveness Are Not Correlated

| Attack | Stealth | Effectiveness | Pattern |
|---|---|---|---|
| Out-of-Scope Parameter (MSB) | Low (2) | High (74% ASR) | Obvious but effective |
| Implicit PT Poisoning (MCPTox) | High (9) | High (72.8% ASR) | Stealthy and effective |
| Covert Sabotage (SHADE-Arena) | High (8) | Low (27% best) | Stealthy but weak |
| Protocol Trust (ProtoAmp) | High (9) | Medium-High (amplified) | Stealthy and amplified |

**Implication:** Stealth and effectiveness are independent axes — a scoring framework must measure both separately, not assume one implies the other.

---

## 11. Summary

| Aspect | This Framework |
|---|---|
| **Core question** | "How do I fully characterize this client→server attack?" |
| **Perspective** | Attack analyst / security researcher |
| **Dimensions** | 6 attack-characterization + 1 model modifier |
| **Source data** | 12 client→server attack benchmarks only |
| **Total rows/units across sources** | ~90K+ (dominated by MCP-AttackBench's 70.4K) |
| **Coverage** | 12/12 benchmarks mapped, 0 orphans |
| **Grades** | 4× A, 2× B+, 1× A (modifier) |
| **Key finding** | Inverse scaling, defense specificity, protocol amplification, stealth-effectiveness independence |

### Comparison With Existing Frameworks

| Aspect | v3 Server Defense | Benchmark-Backed Server Attack | **This File** |
|---|---|---|---|
| **Question** | How does this agent threaten my server? | Same, benchmark-filtered | How do I characterize this attack? |
| **Perspective** | Server operator | Server operator | Attack analyst |
| **Dimensions** | 6 + modifier | 5 + modifier | 6 + modifier |
| **Data sources** | 22 benchmarks | 11 benchmarks | 12 client→server attack benchmarks |
| **Use case** | Runtime risk scoring of incoming requests | Training risk scorer | Attack taxonomy and benchmark synthesis |
| **Output** | Risk score (1-10) | Risk score (1-10) | Attack profile vector (6 scores + modifier) |
