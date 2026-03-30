# MCP-RSS Dimension Refinement Analysis

## 1. Purpose

This document reconciles three existing dimension sets for the MCP Risk Scoring System (MCP-RSS)
and arrives at a data-grounded final set using evidence from 22 benchmark analyses.

**Three existing dimension sets:**

| Source | Location | Dimensions | Scale |
|--------|----------|------------|-------|
| Benchmark README | `reviews/benchmark_md/README.md` (lines 71-83) | 11 empirical dimensions | 1-10 |
| Thesis Research Plan | `thesis_research_plan.md` (lines 99-108) | 8 CVSS-inspired metrics | 0-3 |
| Meeting Pitch | `meeting_pitch_practical.md` (lines 53-61) | 7 JSON breakdown fields | 0-3 |

**Problem:** These sets are misaligned. The benchmark dimensions are empirical (what the data
measures) while the research plan dimensions are conceptual (what should be measured). This
analysis bridges the gap.

**Target:** 5-8 final dimensions, each backed by sufficient data to calibrate a 1-10 scale.

---

## 2. Complete Dimension Inventory (Start With Everything)

### 2.1 All 11 Benchmark-Derived Dimensions

| # | Dimension | Type | # Files | Total Rows | Key Sources | Grade |
|---|-----------|------|---------|------------|-------------|-------|
| D1 | Attack Type / Category | Categorical | 10 | 90,338+ | MCIP-Bench (2,218), MCIP Guardian (13,830), MCP-AttackBench (70,448), MCPTox (1,497), MCPSecBench (17×4), MCP-SafetyBench (20×5×13), Component PoC (132), R-Judge (569), Meta Tool-Use PI (600), Synthetic PI (500) | **A** |
| D2 | Attack Surface | Categorical | 2 | ~1,700 | MCPSecBench (4 surfaces × 17 types), MCP-SafetyBench (3 surfaces × 20 types) | **B** |
| D3 | Attack Severity | Numeric | 11 | 31,000+ CVEs + ASR from 8 files | NVD/CVSS (31K+ CVEs, 8 base metrics), ASR data from MCPTox, MCPSecBench, MCP-SafetyBench, AgentDojo, InjecAgent, Indirect PI, Component PoC, Synthetic PI | **A** |
| D4 | Risk Type (MCP-specific) | Categorical | 10 | ~90K (same rows as D1) | MCIP-Bench 10 risk types, R-Judge 10 risk types | **B** (overlap with D1) |
| D5 | Tool Toxicity | Numeric | 2 | 2,045 | MCPTox (1,497 cases, 45 servers, 353 tools), MCP-ITP (548 cases × 12 models) | **B** |
| D6 | Data Exposure | Cat. + Numeric | 2 | 68,417 records | MCP Server Database (1,360 servers, 12,230 tools, EIT/PAT/NAT), MCP Server Dataset 67K (67,057 servers, 44,499 tools) | **A** |
| D7 | Trust Calibration | Numeric | 1 | 19 scenarios | Trust Paradox (TCI 0.72-0.89, 4 LLM backends) | **C** |
| D8 | Trustworthiness | Composite | 5 | multi-benchmark | DecodingTrust (8 dims, 12 sub-benchmarks), TrustLLM (6 dims, 30+ datasets, 16 models), Trust Paradox (19 scenarios), MCP-SafetyBench, MCPTox | **A** |
| D9 | Protocol Amplification | Numeric | 2 | ~200 | MCPSecBench (+23-41% amplification), Component PoC (132 servers, 3.3% detection) | **C** |
| D10 | Permission Scope | Numeric | 2 | 67,000+ | MiniScope (10 apps, 79-247 methods each), MCP Server Dataset 67K (permission metadata) | **B** |
| D11 | Injection Resilience | Numeric | 6 | 4,351+ | AgentDojo (629 injections), Indirect PI (1,068 instances), Synthetic PI (500), Meta Tool-Use PI (600), InjecAgent (1,054), ASB (6 types) | **A** |
| D12 | Input Manipulation | Categorical | 2 | 1,200 | ASB (6 attack prompt types), Meta Tool-Use PI (600 scenarios, 7 techniques) | **C** (overlap with D11) |

### 2.2 Cross-Cutting Columns (Not Standalone Dimensions)

| Column | Type | # Files | Total Rows | Sources | Role |
|--------|------|---------|------------|---------|------|
| Binary Safety Label | Boolean | 2 | 16,048 | MCIP-Bench (2,218), MCIP Guardian (13,830) | Training signal for classifiers |
| ASR / Success Rate | Float (0-100%) | 8 | derived metric | MCPTox (72.8%), MCPSecBench (27-100%), MCP-SafetyBench, AgentDojo, InjecAgent, Indirect PI, Component PoC, Synthetic PI | Calibration metric for severity |
| Model Vulnerability | Float | 5 | 28+ models tested | MCPTox (GPT-4o 61.8%, Claude 34.3%), Indirect PI (28 models), Trust Paradox (4 models), MCP-ITP (12 models), MCP-SafetyBench (13 models) | Feeds Trustworthiness dimension |
| Domain Context | Categorical | 2 | ~1,900 | MCP-SafetyBench (5 domains), Meta Tool-Use PI (Travel, Info-retrieval, Productivity) | Context modifier, not a risk axis |
| CVSS Sub-metrics | Categorical (8) | 1 | 31,000+ | NVD/CVSS (AV, AC, PR, UI, S, C, I, A) | Scoring formula template |
| Server Metadata | Structured | 3 | 68,000+ | MCP Server DB, 67K Dataset, Component PoC | Feeds Data Exposure + Permission Scope |

---

## 3. Data Support Triage

### Grade A — Standalone Candidates (5+ files OR 10K+ labeled rows)

| Dimension | Files | Rows | Why Strong |
|-----------|-------|------|-----------|
| **D1 Attack Type/Category** | 10 | 90K+ | Largest labeled pool; 10+ distinct taxonomies across MCP-specific and general agent benchmarks |
| **D3 Attack Severity** | 11 | 31K+ CVEs + ASR from 8 files | CVSS provides proven scoring formula; ASR data enables MCP-specific calibration |
| **D6 Data Exposure** | 2 | 68K records | Massive ecosystem-scale data; EIT/PAT/NAT classification already operational |
| **D8 Trustworthiness** | 5 | multi-benchmark | Two major trust frameworks (DecodingTrust 8 dims, TrustLLM 6 dims) + 16+ model evaluations |
| **D11 Injection Resilience** | 6 | 4,351+ | Most diverse source coverage; 12 obfuscation types, 7 injection techniques, 6 defense baselines |

### Grade B — Need Merging or Supplementation (2-4 files, 1K-10K rows)

| Dimension | Files | Rows | Issue |
|-----------|-------|------|-------|
| **D4 Risk Type** | 10 | ~90K | Same 10 files as D1 — MCIP's 10 risk types ARE attack categories. Redundant. |
| **D5 Tool Toxicity** | 2 | 2,045 | MCP-specific and novel, but only 2 sources. Worth keeping for thesis differentiation. |
| **D2 Attack Surface** | 2 | ~1,700 | Only 2 files but empirically grounded (MCPSecBench ASR per surface is hard evidence). |
| **D10 Permission Scope** | 2 | 67K+ | Large volume but mostly metadata-level. Directly maps to CVSS Privileges Required. |

### Grade C — Must Merge (1 file OR <1K rows OR high overlap)

| Dimension | Files | Rows | Problem |
|-----------|-------|------|---------|
| **D7 Trust Calibration** | 1 | 19 scenarios | Single paper (Trust Paradox). Too small for standalone dimension. TCI is a sub-signal of D8 Trustworthiness. |
| **D9 Protocol Amplification** | 2 | ~200 | Only ~200 data points. The +23-41% amplification factor is better used as a modifier inside D2 Attack Surface. |
| **D12 Input Manipulation** | 2 | 1,200 | ASB's 6 attack types and Meta Tool-Use PI's 7 techniques directly overlap with D11 Injection Resilience. Two sides of the same coin. |

---

## 4. Merge Proposals (11 → 7)

| # | Absorbed | Into | Rationale | Data Impact |
|---|----------|------|-----------|-------------|
| M1 | **D4 Risk Type** | **D1 Attack Category** | MCIP's 10 risk types (Identity Injection, Function Overlapping, etc.) are attack categories. Both draw from the same 10 files and ~90K rows. Merging eliminates double-counting. The union taxonomy becomes: MCIP 10 types + AttackBench 3 families + MCPSecBench 17 types + MCPTox 3 paradigms. | 0 rows lost |
| M2 | **D7 Trust Calibration** | **D8 Trustworthiness** | Trust Calibration has only 19 scenarios from one paper. The TCI metric (0.72-0.89) becomes a sub-score: capability-tier modifier within the trustworthiness composite. DecodingTrust + TrustLLM already cover the broader picture. | +19 rows added to D8 |
| M3 | **D12 Input Manipulation** | **D11 Injection Resilience** | ASB's 6 attack prompt types and Meta Tool-Use PI's 7 injection techniques describe how PI payloads are constructed. D11 already measures resistance to those payloads. Merged dimension covers both attack sophistication and system resilience. | +1,200 rows added to D11 |
| M4 | **D9 Protocol Amplification** | **D2 Attack Surface** | ~200 instances is too thin for standalone. Protocol amplification (+23-41%) explains why the protocol surface scores 9-10 in D2. The data becomes the calibration evidence for the protocol layer's severity weight. | +200 rows added to D2 |

---

## 5. Dimension Progression

### Stage 1: All 11 Empirical Dimensions

```
D1  Attack Type/Category         ──┐
D2  Attack Surface               ──┤
D3  Attack Severity              ──┤
D4  Risk Type (MCP-specific)     ──┤  ← 11 dimensions
D5  Tool Toxicity                ──┤
D6  Data Exposure                ──┤
D7  Trust Calibration            ──┤
D8  Trustworthiness              ──┤
D9  Protocol Amplification       ──┤
D10 Permission Scope             ──┤
D11 Injection Resilience         ──┤
D12 Input Manipulation           ──┘
```

### Stage 2: After 4 Merges → 8 Dimensions

```
D1+D4  Attack Category           ──┐  (Risk Type absorbed)
D2+D9  Attack Surface            ──┤  (Protocol Amplification absorbed)
D3     Attack Severity           ──┤
D5     Tool Toxicity             ──┤  ← 8 dimensions
D6     Data Exposure             ──┤
D8+D7  Trustworthiness           ──┤  (Trust Calibration absorbed)
D10    Permission Scope          ──┤
D11+D12 Injection Resilience     ──┘  (Input Manipulation absorbed)
```

### Stage 3: Evaluate Further Reduction

**Keep Tool Toxicity (D5) separate?**
- YES — It is the most MCP-specific dimension (thesis novelty). MCPTox + MCP-ITP are purpose-built
  MCP datasets. Tool description integrity is a pre-invocation static signal that no other dimension
  captures. This is the core differentiator from CVSS.

**Keep Permission Scope (D10) separate?**
- YES — Maps directly to CVSS "Privileges Required". Backed by 67K+ server records from the 67K
  Dataset. Most actionable dimension for Lenovo: reducing permissions is the simplest risk
  mitigation an enterprise can deploy.

**Final: 8 dimensions.** No further reduction needed. Each has clear data support and distinct
risk coverage.

### Final 8 Dimensions — Summary

| # | Dimension | Files | Rows | Grade | Unique Risk Coverage |
|---|-----------|-------|------|-------|---------------------|
| 1 | Attack Category | 10 | 90K+ | A | What type of attack is this? |
| 2 | Attack Severity | 11 | 31K+ CVEs + ASR | A | How bad if it succeeds? |
| 3 | Attack Surface | 2+2 | ~1,900 | B+ | Where in the MCP stack? |
| 4 | Tool Toxicity / Description Integrity | 2 | 2,045 | B | Is the tool description poisoned? |
| 5 | Data Exposure | 2 | 68K records | A | What sensitive data is at risk? |
| 6 | Trustworthiness | 5+1 | multi-benchmark | A | How reliable is the agent/model? |
| 7 | Permission Scope | 2 | 67K+ | B | How over-privileged is the request? |
| 8 | Injection Resilience | 6+2 | 5,551+ | A | How resistant to prompt injection? |

---

## 6. Final Dimension Specifications

### Dim 1: Attack Category

**Definition:** Classifies the type of attack being attempted against the MCP tool invocation.

**Scale (1-10):**

| Score | Category Tier | Example Attack Types |
|-------|--------------|---------------------|
| 1-2 | Low | Wrong Parameter Intent, Causal Dependency |
| 3-4 | Medium | Data Injection, Replay Injection, Function Dependency |
| 5-6 | High | Function Injection, Function Overlapping, Excessive Privileges |
| 7-8 | Critical | Identity Injection, Explicit Trigger Function Hijacking |
| 9-10 | Catastrophic | Implicit Trigger Parameter Tampering, multi-step chained attacks |

**Data sources:**
- MCIP-Bench: 2,218 instances, 11 risk categories (10 attack + 1 safe)
- MCIP Guardian: 13,830 instances, same 11 categories with class distribution
- MCP-AttackBench: 70,448 samples, 3 attack families (Semantic/Adversarial, Protocol-Specific, Injection/Execution)
- MCPTox: 1,497 cases, 3 paradigms (Explicit Trigger 224, Implicit Trigger FH 548, Implicit Trigger PT 725)
- MCPSecBench: 17 attack types across 4 surfaces
- MCP-SafetyBench: 20 attack types across 5 domains and 13 models
- Component PoC: 132 servers across 12 categories (A1-A12)
- R-Judge: 569 records, 10 risk types
- Meta Tool-Use PI: 600 scenarios, 8 threat categories
- Synthetic PI: 500 prompts, 10 attack categories

**Computation:** Classify the attack type from tool invocation context using the unified taxonomy
(MCIP 10 types → AttackBench 3 families → MCPTox 3 paradigms). Map to severity tier via a
lookup table trained on labeled data. MCIP Guardian's 13,830 samples serve as the primary
training set for the classifier.

---

### Dim 2: Attack Severity

**Definition:** How dangerous the attack is if it succeeds — the potential impact on
confidentiality, integrity, and availability.

**Scale (1-10):**

| Score | Severity | CVSS Equivalent | Empirical ASR Mapping |
|-------|----------|----------------|----------------------|
| 1-2 | Informational | 0.1-1.9 | — |
| 3-4 | Low | 2.0-3.9 | ASR 0-10% across benchmarks |
| 5-6 | Medium | 4.0-6.9 | ASR 10-40% |
| 7-8 | High | 7.0-8.9 | ASR 40-70% |
| 9-10 | Critical | 9.0-10.0 | ASR 70-100% |

**Data sources:**
- NVD/CVSS: 31,000+ CVEs with CVSS v3.1 base scores (0.0-10.0) and 8 sub-metrics (AV, AC, PR, UI, S, C, I, A)
- ASR data: MCPTox (72.8% avg), MCPSecBench (protocol 100%, server 47%, client 33%, host 27%), MCP-ITP (84.2% ASR, 0.3% detection), AgentDojo (41.2% baseline → 2.2% with defense), Indirect PI (34.3%-72.4% per model)

**Computation:** Adapt CVSS v3.1 base score formula with MCP-specific sub-metrics. Pre-train on
NVD data for description-to-severity mapping. Calibrate using empirical ASR from MCP benchmarks
as validation signal. The CVSS 8-metric structure maps naturally:
- Attack Vector → Attack Surface (Dim 3)
- Confidentiality Impact → Data Exposure (Dim 5)
- Privileges Required → Permission Scope (Dim 7)
- Remaining metrics → MCP-specific adaptations

---

### Dim 3: Attack Surface

**Definition:** Which layer of the MCP architecture is targeted, including protocol amplification
effects.

**Scale (1-10):**

| Score | Surface Layer | Empirical ASR | Protocol Amplification |
|-------|-------------|---------------|----------------------|
| 3-4 | Host-side | 27% ASR (MCPSecBench) | — |
| 5-6 | Client-side / User-side | 33% ASR (MCPSecBench) | — |
| 6-7 | Server-side | 47% ASR (MCPSecBench) | +23% from MCP features |
| 9-10 | Protocol-side | 100% ASR (MCPSecBench) | +41% from MCP features |

**Data sources:**
- MCPSecBench: 4 attack surfaces × 17 attack types, 3 test clients (Claude Desktop, GPT-4.1, Cursor), 15 trials per attack
- MCP-SafetyBench: 3 surfaces (server-side, host-side, user-side) × 20 attack types × 13 models
- Component PoC: 132 servers, 12 categories, 5 component types (launch commands, initialization, tools, resources, prompts). Protocol amplification: +23-41%. Detection rate: 3.3% (4/120)

**Computation:** Classify the target surface from tool metadata and invocation context. Assign
the base score from MCPSecBench's empirical ASR mapping. Apply protocol amplification modifier
when MCP-specific features (tool_list_changed, auto-approve, SSE transport) are present.

---

### Dim 4: Tool Toxicity / Description Integrity

**Definition:** Whether the tool's description or metadata has been poisoned or manipulated to
steer agent behavior.

**Scale (1-10):**

| Score | Toxicity Level | Characteristics |
|-------|---------------|-----------------|
| 1-2 | Clean / Verified | Tool from official registry, description matches behavior |
| 3-4 | Minor Anomaly | Unusual phrasing or scope claims, no steering detected |
| 5-6 | Suspicious | Matches known poisoning patterns, implicit steering words |
| 7-8 | Likely Poisoned | Implicit Trigger—Function Hijacking paradigm detected |
| 9-10 | Confirmed Toxic | Implicit Trigger—Parameter Tampering, explicit malicious intent |

**Data sources:**
- MCPTox: 1,312-1,497 malicious test cases, 45 real MCP servers, 353 authentic tools, 3 attack paradigms:
  - Explicit Trigger—Function Hijacking: 224 cases (stealth 1-3)
  - Implicit Trigger—Function Hijacking: 548 cases (stealth 4-6)
  - Implicit Trigger—Parameter Tampering: 725 cases (stealth 7-10)
- MCP-ITP: 548 implicit poisoning test cases × 12 models = 6,576 evaluation data points. Overall ASR: 84.2%. Detection by existing defenses: 0.3%

**Computation:** Analyze tool description for implicit steering words and poisoning signatures
(MCP-ITP methodology). Compare against known-good description distributions from the 67K server
ecosystem. Apply the MCPTox paradigm classification (explicit → implicit-FH → implicit-PT) as
the severity ladder. The 0.3% detection baseline means this dimension specifically captures what
other security layers miss — making it critical for the thesis contribution.

**Why standalone:** This is the most MCP-specific dimension. Tool description poisoning is unique
to the MCP ecosystem where agents read tool descriptions to decide behavior. No equivalent exists
in CVSS or traditional security frameworks.

---

### Dim 5: Data Exposure

**Definition:** The risk of sensitive data leakage through tool access patterns and capability
combinations.

**Scale (1-10):**

| Score | Exposure Level | Tool Classification |
|-------|---------------|-------------------|
| 1-2 | Public data only | No EIT/PAT/NAT flags |
| 3-4 | Internal data | EIT only (external ingestion, no privacy access) |
| 5-6 | PII accessible | PAT flagged (privacy access tools) |
| 7-8 | Credentials at risk | NAT flagged (network access) or PAT+EIT combo |
| 9-10 | Full exposure | EIT+PAT+NAT combination (parasitic toolchain capable) |

**Data sources:**
- MCP Server Database: 1,360 servers, 12,230 tools
  - EIT (External Ingestion Tools): 472 tools across 128 servers
  - PAT (Privacy Access Tools): 391 tools across 155 servers
  - NAT (Network Access Tools): 180 tools across 89 servers
  - Exploitable tools: 1,062 (8.7% of all tools)
  - Exploitable tool combinations: 27.2% of servers
  - Parasitic toolchain success rate: 90%
- MCP Server Dataset 67K: 67,057 servers, 44,499 tools
  - Credential leakage: 9 PATs + 3 API keys found
  - Server hijacking instances: 111+
  - Affix-squatting groups: 408
  - Invalid link rate: 6.75%
- InjecAgent: 1,054 test cases with data exfiltration category

**Computation:** Classify each tool by EIT/PAT/NAT flags. Score individual tools by their
highest flag. For tool combinations in a session, check for parasitic toolchain potential
(EIT+PAT+NAT). The 27.2% exploitable-combination rate is the base rate for combination scoring.
Credential leakage instances from the 67K dataset calibrate the upper severity band.

---

### Dim 6: Trustworthiness

**Definition:** Multi-dimensional assessment of the agent/model's reliability, incorporating
safety, robustness, privacy, ethics, and trust calibration.

**Scale (1-10):**

| Score | Trust Level | Characteristics |
|-------|------------|-----------------|
| 1-2 | Highly Trusted | Top-tier across all sub-dimensions, verified capability tier |
| 3-4 | Generally Trusted | Strong on most sub-dimensions, minor weaknesses |
| 5-6 | Mixed Trust | Significant gaps in 1-2 sub-dimensions |
| 7-8 | Low Trust | Fails multiple sub-dimensions, high capability-trust gap |
| 9-10 | Untrusted | Unverified model, no trust data available, or known unsafe |

**Sub-dimensions (from DecodingTrust + TrustLLM):**
1. Toxicity (RealToxicityPrompts, BOLD)
2. Stereotype Bias (BBQ, CrowS-Pair)
3. Adversarial Robustness (AdvGLUE, ANLI)
4. OOD Robustness (RealtimeQA, MMLU)
5. Privacy (Enron Email extraction)
6. Machine Ethics (ETHICS, Jiminy Cricket)
7. Fairness (Adult UCI)
8. Safety (jailbreak susceptibility)

**Trust Calibration modifier (from Trust Paradox):**
- TCI metric (0.72-0.89) inverted: higher capability models get higher scrutiny
- 5 capability tiers: basic → intermediate → advanced → expert → critical
- More capable models that show trust gaps score higher (worse) on this dimension

**Data sources:**
- DecodingTrust: 8 dimensions, 12 sub-benchmarks, GPT-4/3.5 baselines
- TrustLLM: 6 dimensions, 30+ datasets, 16 LLMs, 18 subcategories
- Trust Paradox: 19 scenarios, TCI 0.72-0.89, 4 LLM backends, 5 capability tiers
- Model vulnerability data: MCPTox (GPT-4o 61.8%, Claude 34.3%), MCP-ITP (12 models), Indirect PI (28 models across 9 providers)

**Computation:** For a known LLM backend, look up its trustworthiness profile across sub-dimensions.
Compute composite score as weighted average. Apply Trust Paradox modifier: capability tier ×
(1 - TCI) amplifies the score for capable-but-untrustworthy models. For unknown models, default
to score 8-9 (untrusted until proven).

---

### Dim 7: Permission Scope

**Definition:** How over-privileged the requested tool permissions are relative to the minimum
required.

**Scale (1-10):**

| Score | Privilege Level | Over-Privilege Ratio |
|-------|----------------|---------------------|
| 1-2 | Least privilege | Requested ≤ minimum required scopes |
| 3-4 | Minor excess | 1-2 unnecessary scopes granted |
| 5-6 | Moderate excess | 3-5 unnecessary scopes, some sensitive |
| 7-8 | Severe excess | 6+ unnecessary scopes, includes write/delete access |
| 9-10 | Full privilege | Admin/root level, unrestricted path or API access |

**Data sources:**
- MiniScope: 10 real-world applications with ground-truth minimum permission mappings
  - Gmail: 79 methods, 10 scopes
  - Google Calendar: 37 methods, 17 scopes
  - Slack: 247 methods, 84 scopes
  - Dropbox: 120 methods, 13 scopes
  - Multi-app suites: 171 methods (Suite 1), 465 methods (Suite 2)
- MCP Server Dataset 67K: 67,057 servers with permission metadata, 17 avg permissions/server baseline
- MCP Server Database: 1,360 servers, tool capability flags

**Computation:** Compare requested permissions to minimum necessary (MiniScope ground-truth as
reference). Over-privilege ratio = (granted - minimum) / total available scopes. Weight by
scope sensitivity (read < write < delete < execute < admin). Use 17 permissions/server as the
ecosystem baseline from the 67K dataset.

**Why standalone:** Most actionable dimension for Lenovo. Reducing permissions is the simplest,
cheapest risk mitigation an enterprise can deploy immediately.

---

### Dim 8: Injection Resilience

**Definition:** The system's resistance to prompt injection attacks across techniques, obfuscation
methods, and attack sophistication levels.

**Scale (1-10, inverted: 1 = highly resilient, 10 = trivially injectable):**

| Score | Resilience Level | ASR Range | Characteristics |
|-------|-----------------|-----------|-----------------|
| 1-2 | Highly Resilient | ASR 0-5% | Resists all 12 obfuscation types and 7 injection techniques |
| 3-4 | Resilient | ASR 5-15% | Fails on 1-2 advanced techniques only |
| 5-6 | Moderate | ASR 15-40% | Vulnerable to indirect and multi-step injections |
| 7-8 | Weak | ASR 40-70% | Fails on direct overrides and authority assertions |
| 9-10 | No Resilience | ASR 70-100% | Trivially injectable across all techniques |

**Data sources:**
- AgentDojo: 97 user tasks + 629 injection tasks, 6 defense baselines (repeat_user_prompt, spotlighting, tool_filter, transformers_pi_detector, DataSentinel, Llama Prompt Guard 2). Baseline ASR 41.2% → 2.2% with best defense.
- Indirect PI Attack: 1,068 instances (89 templates × 12 obfuscation types), 28 models across 9 providers. Vulnerability range: 34.3%-72.4% per model.
- Synthetic PI: 500 engineered prompts (50 per category × 10 categories). Metrics: ISR, POF, PSR, CCS, TIVS composite. 45.7% reduction through mitigation.
- Meta Tool-Use PI: 600 scenarios (300 benign, 300 malicious), 8 threat categories, 7 injection techniques (Direct Override, Authority Assertions, Hidden Commands, Role-Play, Logical Traps, Multi-Step, Conflicting).
- InjecAgent: 1,054 test cases, 17 user tools, 62 attacker tools.
- ASB: 6 attack prompt types (combined_attack, context_ignoring, escape_characters, fake_completion, naive, average).

**Computation:** Measure/estimate ASR across injection technique categories. Apply the 12-obfuscation
coverage check from Indirect PI. Tools in environments where AgentDojo's defense baselines fail
score higher. Use Synthetic PI's TIVS composite as a template for combining sub-metrics
(ISR + POF + PSR + CCS → single score).

---

## 7. Reconciliation with Existing Thesis Metrics

### 7.1 Mapping: Data-Grounded → CVSS-Inspired

| Research Plan Metric (0-3) | Maps To Final Dimension (1-10) | Relationship |
|---------------------------|-------------------------------|-------------|
| **Access Scope** (CVSS Attack Vector) | **Dim 3: Attack Surface** | Direct — "what can the tool reach" defines the surface |
| **Data Sensitivity** (CVSS Confidentiality) | **Dim 5: Data Exposure** | Direct — both measure what data is at risk |
| **Action Reversibility** (CVSS Integrity) | **Dim 2: Attack Severity** | Embedded — reversibility is a severity sub-metric (integrity impact) |
| **Privilege Level** (CVSS Privileges Required) | **Dim 7: Permission Scope** | Direct — both measure over-privilege |
| **Agent Trust** (Trust Paradox) | **Dim 6: Trustworthiness** | Embedded — agent trust is one facet of the trustworthiness composite |
| **Tool Provenance** (ecosystem studies) | **Dim 4: Tool Toxicity** | Related — provenance (source registry, verification status) feeds toxicity assessment |
| **Combination Risk** (Mind Your Server) | **Dim 5: Data Exposure** | Embedded — EIT+PAT+NAT parasitic toolchain risk is the data-grounded version of combination risk |
| **Description Integrity** (MCP-ITP) | **Dim 4: Tool Toxicity** | Direct — description integrity IS tool toxicity |

### 7.2 Coverage Check

All 8 research plan metrics are covered by the final 8 dimensions:
- 4 direct mappings (Access Scope, Data Sensitivity, Privilege Level, Description Integrity)
- 3 embedded as sub-scores (Action Reversibility, Agent Trust, Combination Risk)
- 1 related/feeding relationship (Tool Provenance)

### 7.3 Updated JSON Output Structure

The `meeting_pitch_practical.md` JSON output should be updated from 7 fields to 8:

```json
{
  "risk_score": 9.2,
  "risk_level": "CRITICAL",
  "breakdown": {
    "attack_category": 8,
    "attack_severity": 9,
    "attack_surface": 8,
    "tool_toxicity": 3,
    "data_exposure": 9,
    "trustworthiness": 6,
    "permission_scope": 7,
    "injection_resilience": 8
  },
  "justification": "Writing to /etc/passwd requires root privileges and can compromise system integrity...",
  "recommendation": "DENY -- request manual approval",
  "confidence": 0.94
}
```

---

## 8. Benchmark Coverage Matrix

Every benchmark file (01-22) is referenced by at least one final dimension:

| Benchmark | D1 Cat | D2 Sev | D3 Surf | D4 Tox | D5 Exp | D6 Trust | D7 Perm | D8 Inj |
|-----------|:------:|:------:|:-------:|:------:|:------:|:--------:|:-------:|:------:|
| 01 MCIP-Bench | x | | | | | | | |
| 02 MCIP Guardian | x | | | | | | | |
| 03 MCP-AttackBench | x | x | | | | | | |
| 04 MCPTox | x | x | | x | | | | |
| 05 MCPSecBench | x | x | x | | | | | |
| 06 MCP-SafetyBench | x | x | x | | | | | |
| 07 MCP Server DB | | | | | x | | x | |
| 08 Component PoC | x | | x | | | | | |
| 09 67K Dataset | | | | | x | | x | |
| 10 MCP-ITP | | | | x | | | | |
| 11 NVD/CVSS | | x | | | | | | |
| 12 R-Judge | x | | | | | | | |
| 13 AgentDojo | | x | | | | | | x |
| 14 InjecAgent | | | | | x | | | x |
| 15 Meta Tool-Use PI | x | | | | | | | x |
| 16 ASB | | | | | | | | x |
| 17 MiniScope | | | | | | | x | |
| 18 Indirect PI | | x | | | | | | x |
| 19 DecodingTrust | | | | | | x | | |
| 20 TrustLLM | | | | | | x | | |
| 21 Trust Paradox | | | | | | x | | |
| 22 Synthetic PI | x | | | | | | | x |

**Coverage:** All 22 benchmarks mapped. No orphan files.

---

## 9. Summary

| Step | Dimensions | Change |
|------|-----------|--------|
| Start | 11 + 6 cross-cutting = 17 columns | Everything from benchmarks |
| Triage | 5A + 4B + 3C | Graded by data support |
| Merge | 11 → 8 | 4 merges (Risk Type, Trust Calibration, Input Manipulation, Protocol Amplification) |
| Evaluate | 8 → 8 | Tool Toxicity and Permission Scope kept for thesis novelty and Lenovo practicality |
| **Final** | **8 dimensions** | Each with 1-10 scale, data sources, and computation method |

**Final 8 dimensions for MCP-RSS:**

1. **Attack Category** — what type of attack (10 files, 90K+ rows)
2. **Attack Severity** — how bad if it succeeds (11 files, 31K+ CVEs)
3. **Attack Surface** — where in the MCP stack (4 files, ~1,900 rows + amplification)
4. **Tool Toxicity** — is the tool description poisoned (2 files, 2,045 rows, MCP-specific)
5. **Data Exposure** — what sensitive data is at risk (2 files, 68K records)
6. **Trustworthiness** — how reliable is the agent (6 files, multi-benchmark)
7. **Permission Scope** — how over-privileged is the request (2 files, 67K+ records)
8. **Injection Resilience** — how resistant to prompt injection (8 files, 5,551+ rows)
