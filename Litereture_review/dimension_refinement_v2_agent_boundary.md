# MCP-RSS Dimension Refinement v2: Agent-Boundary Focus

## 1. Motivation for Refocus

### What Changed and Why

The original 8 dimensions (v1, see `dimension_refinement_analysis.md`) were derived bottom-up from
22 benchmark analyses. While data-grounded, many dimensions described properties of the **MCP server**
or the **LLM agent** in isolation — not the **interaction between them**.

**The thesis idea:** MCP-RSS is a proxy that sits between the agent and the MCP server. It intercepts
every `tools/call` request and scores the risk of **that specific call, by that agent, at that moment**.
The dimensions must reflect what the proxy evaluates at the agent-tool boundary.

### The Core Question

> "Given this agent is about to call this MCP tool with these parameters, in this session context,
> what is the risk score?"

Every dimension must be answerable from what the proxy sees mid-session:

| Signal Layer | What The Proxy Has | When Available |
|-------------|-------------------|----------------|
| **Tool metadata** | Name, description, schema from `tools/list` | Before any call (static) |
| **Request arguments** | The actual `params.arguments` the agent is passing | At call time (dynamic) |
| **Session history** | All previous tool calls, data accessed, conversation turns | Accumulated (temporal) |

### What Was Wrong With v1

| Old Dimension | Problem |
|--------------|---------|
| D1 Attack Category | Classifies attack types generically — not tied to a specific tool call |
| D2 Attack Severity | CVSS-based severity is about vulnerabilities, not about agent-tool interactions |
| D3 Attack Surface | Describes MCP architecture layers — that's infrastructure, not the agent's decision |
| D6 Trustworthiness | Measures the LLM/agent itself (DecodingTrust, TrustLLM) — agent in isolation |

### What v2 Does Differently

Every dimension answers a question about **this specific tool call**:

| v1 (ecosystem/generic) | v2 (agent-boundary) | Shift |
|------------------------|---------------------|-------|
| "What type of attack is this?" | "How dangerous is what the agent is asking to do RIGHT NOW?" | From classification → action risk |
| "How bad is this vulnerability?" | "If this call goes wrong, how much damage?" | From static vuln → dynamic impact |
| "Where in the MCP stack?" | Absorbed into Blast Radius | From layer label → impact scope |
| "How reliable is the agent/model?" | Modifier on overall score, not a dimension | From standalone → context signal |

---

## 2. The 7 MCP-Agent Boundary Dimensions

### Overview

| # | Dimension | Proxy Question | Signal Layer | Scale |
|---|-----------|---------------|-------------|-------|
| 1 | **Tool Integrity** | Is this MCP tool itself trustworthy? | Tool metadata (static) | 1-10 |
| 2 | **Request Sensitivity** | How dangerous is what the agent is asking to do? | Request arguments (dynamic) | 1-10 |
| 3 | **Permission Overreach** | Is the agent asking for more access than needed? | Tool metadata + Request (dynamic) | 1-10 |
| 4 | **Data Exposure** | What sensitive data flows through this call? | Request + Session (dynamic) | 1-10 |
| 5 | **Injection Exposure** | Is this call a channel for prompt injection? | All layers (dynamic) | 1-10 |
| 6 | **Blast Radius** | If this call goes wrong, how much damage? | Tool metadata + Request (dynamic) | 1-10 |
| 7 | **Cross-Tool Escalation** | Does this call + session history create a dangerous pattern? | Session history (temporal) | 1-10 |

### Dimension Flow Through the Proxy

```
Agent ──► [tools/call request] ──► MCP-RSS Proxy ──► MCP Server
                                        │
                                        ├─ Dim 1: Tool Integrity       ← tool metadata
                                        ├─ Dim 2: Request Sensitivity  ← arguments
                                        ├─ Dim 3: Permission Overreach ← schema + args
                                        ├─ Dim 4: Data Exposure        ← args + session
                                        ├─ Dim 5: Injection Exposure   ← all signals
                                        ├─ Dim 6: Blast Radius         ← metadata + args
                                        ├─ Dim 7: Cross-Tool Escalation← session history
                                        │
                                        ├─ Modifier: Agent Trust Level ← model identity
                                        │
                                        └─► Risk Score (1-10) + Breakdown + Justification
```

---

## 3. Dimension Specifications

### Dim 1: Tool Integrity

**Proxy question:** "Is the MCP tool I'm about to let the agent use trustworthy?"

**What the proxy checks:**
- Is the tool description poisoned or manipulated?
- Does the tool come from a verified registry?
- Does the description match what the tool actually does?
- Are there known poisoning signatures (implicit steering words)?

**Scale (1-10):**

| Score | Integrity Level | What The Proxy Sees |
|-------|----------------|-------------------|
| 1-2 | Verified clean | Official registry, description matches behavior, no anomalies |
| 3-4 | Minor anomaly | Unusual phrasing or scope claims, unverified source |
| 5-6 | Suspicious | Matches known poisoning patterns, implicit steering words detected |
| 7-8 | Likely poisoned | Implicit Trigger — Function Hijacking paradigm detected |
| 9-10 | Confirmed toxic | Implicit Trigger — Parameter Tampering, explicit malicious intent |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| MCPTox (04) | 1,497 cases | 3 attack paradigms across 353 real tools from 45 servers. Stealth ladder: Explicit (224) → Implicit FH (548) → Implicit PT (725) |
| MCP-ITP (10) | 548 × 12 models | Implicit poisoning ASR: 84.2%. Detection by existing tools: 0.3%. The gap this dimension fills |
| MCP Server DB (07) | 12,230 tools | EIT/PAT/NAT flags — tool capability classification from 1,360 real servers |
| 67K Dataset (09) | 67,057 servers | Provenance data: affix-squatting (408 groups), credential leaks (12), server hijacking (111+) |
| Component PoC (08) | 132 servers | 12 attack categories (A1-A12), 5 modular components. Scanner detection: 3.3% |

**Key columns extractable from data:**
- `tool_description` (original vs poisoned) — MCPTox, MCP-ITP
- `attack_paradigm` (Explicit/Implicit-FH/Implicit-PT) — MCPTox
- `detection_result` (detected/missed) — MCP-ITP, Component PoC
- `registry_source` — 67K Dataset, MCP Server DB
- `eit_flag`, `pat_flag`, `nat_flag` — MCP Server DB
- `affix_squatting_group` — 67K Dataset

**Computation:** Analyze tool description for implicit steering words (MCP-ITP methodology).
Compare against known-good description distributions from the 67K ecosystem. Check registry
provenance. Apply MCPTox paradigm classification as the severity ladder. The 0.3% detection
baseline is what this dimension specifically catches — what all other security layers miss.

**Grade: A** — 5 data sources, 80K+ records, most MCP-specific dimension.

---

### Dim 2: Request Sensitivity

**Proxy question:** "How dangerous is what the agent is asking to do RIGHT NOW with these arguments?"

**What the proxy checks:**
- What resource is being targeted? (public API vs /etc/passwd vs database)
- What operation type? (read vs write vs delete vs execute)
- Do the argument values match known attack patterns?
- How dangerous is this category of request?

**Scale (1-10):**

| Score | Sensitivity Level | Example Request |
|-------|------------------|----------------|
| 1-2 | Safe | `weather.get(city="London")` — public data, read-only |
| 3-4 | Low | `file.read(path="./config.json")` — local file, read-only |
| 5-6 | Medium | `db.query(sql="SELECT * FROM users")` — data access, broad scope |
| 7-8 | High | `file.write(path="/etc/hosts", content=...)` — system file, write |
| 9-10 | Critical | `shell.execute(cmd="rm -rf /")` — arbitrary execution, destructive |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| MCIP-Bench (01) | 2,218 | 10 risk categories with function call arguments — labeled request-level risk |
| MCIP Guardian (02) | 13,830 | 11-class risk type distribution — training data for request classification |
| MCP-AttackBench (03) | 70,448 | Binary attack/benign labels — largest labeled pool for request classification |
| MCPSecBench (05) | 17 types × 3 clients | ASR per attack type — empirical success rates for request categories |
| MCP-SafetyBench (06) | 20 types × 5 domains | Domain-specific risk: Financial (9-10), Repository (8-9), Browser (7-8), Navigation (5-6), Web Search (3-4) |
| NVD/CVSS (11) | 31,000+ CVEs | Description-to-severity methodology — transferable to tool request descriptions |
| R-Judge (12) | 569 records | 27 risk scenarios across 5 app categories — multi-turn request risk |

**Key columns extractable from data:**
- `risk_category` (11 classes) — MCIP-Bench, MCIP Guardian
- `binary_label` (attack/benign) — MCP-AttackBench
- `attack_type` (17 types) — MCPSecBench
- `domain` + `attack_type` (5 × 20) — MCP-SafetyBench
- `cvss_base_score` + `description` — NVD/CVSS
- `function_call` + `arguments` (JSON) — MCIP-Bench
- `asr_per_type` (%) — MCPSecBench, MCP-SafetyBench

**Computation:** Classify the request from tool name + arguments using the unified taxonomy
(MCIP 10 types → MCPSecBench 17 types → MCP-SafetyBench domain weighting). Use MCIP Guardian's
13,830 labeled samples as primary training set. Apply domain severity modifier from
MCP-SafetyBench (Financial > Repository > Browser). Use NVD's description-to-score approach
as the text analysis backbone.

**Grade: A** — 7 data sources, 118K+ records, strongest data coverage.

---

### Dim 3: Permission Overreach

**Proxy question:** "Is the agent requesting more access than this specific task actually needs?"

**What the proxy checks:**
- What permissions does this tool grant vs what the request needs?
- Over-privilege ratio: granted scopes vs minimum required
- Sensitivity of excess permissions (read < write < delete < admin)

**Scale (1-10):**

| Score | Overreach Level | What The Proxy Sees |
|-------|----------------|-------------------|
| 1-2 | Least privilege | Requested permissions ≤ minimum required for this operation |
| 3-4 | Minor excess | 1-2 unnecessary scopes granted, all low-sensitivity |
| 5-6 | Moderate excess | 3-5 unnecessary scopes, some include write access |
| 7-8 | Severe excess | 6+ unnecessary scopes, includes delete/execute access |
| 9-10 | Full privilege | Admin/root level, unrestricted path or API access |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| MiniScope (17) | 10 apps | Ground-truth minimum permission mappings: Gmail (79 methods, 10 scopes), Slack (247 methods, 84 scopes), Dropbox (120 methods, 13 scopes). The reference standard for "minimum required" |
| 67K Dataset (09) | 67,057 servers | Permission metadata, 17 avg permissions/server baseline — ecosystem norm |
| MCP Server DB (07) | 1,360 servers | Tool capability flags — what each tool can actually access |
| CVSS (11) | 31,000+ CVEs | Privileges Required metric (None/Low/High) — severity weighting template |

**Key columns extractable from data:**
- `api_method` → `required_scopes` (ground truth) — MiniScope
- `granted_scopes` vs `minimum_scopes` — MiniScope
- `mismatch_rate` (%) — MiniScope
- `permissions_per_server` — 67K Dataset
- `tool_capability_flags` — MCP Server DB
- `privileges_required` (None/Low/High) — CVSS

**Computation:** Compare requested permissions against minimum necessary (MiniScope ground-truth
as reference). Over-privilege ratio = (granted − minimum) / total available scopes. Weight by
scope sensitivity (read=1, write=2, delete=3, execute=4, admin=5). Use 17 permissions/server
as ecosystem baseline from 67K Dataset.

**Why this dimension matters for Lenovo:** Most actionable dimension. Reducing permissions is the
simplest, cheapest risk mitigation an enterprise can deploy immediately. No ML needed — just
scope comparison.

**Grade: B+** — 4 data sources, 67K+ records. MiniScope provides rare ground-truth labels.

---

### Dim 4: Data Exposure

**Proxy question:** "What sensitive data could flow through this specific tool call?"

**What the proxy checks:**
- What data can this tool access? (EIT/PAT/NAT classification)
- What is the agent sending as arguments? (credentials, PII, internal data?)
- What did the agent access earlier in the session that could leak through this call?
- Is this a data exfiltration pattern? (read PII → send to network tool)

**Scale (1-10):**

| Score | Exposure Level | What The Proxy Sees |
|-------|---------------|-------------------|
| 1-2 | Public data only | No EIT/PAT/NAT flags, args contain no sensitive values |
| 3-4 | Internal data | EIT only, or args reference internal paths/endpoints |
| 5-6 | PII accessible | PAT flagged, or previous call accessed PII and this call sends outbound |
| 7-8 | Credentials at risk | NAT flagged, or args contain tokens/keys, or PAT+EIT combo |
| 9-10 | Full exposure | EIT+PAT+NAT combination (parasitic toolchain capable), active exfiltration |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| MCP Server DB (07) | 12,230 tools | EIT (472 tools/128 servers), PAT (391/155), NAT (180/89). Exploitable: 8.7%. Combo risk: 27.2% of servers. Parasitic toolchain success: 90% |
| 67K Dataset (09) | 67,057 servers | Credential leakage: 9 PATs + 3 API keys found. Server hijacking: 111+. Invalid links: 6.75% |
| InjecAgent (14) | 1,054 cases | Data exfiltration category — labeled exfiltration attempts vs direct harm |
| CVSS (11) | 31,000+ CVEs | Confidentiality Impact metric (None/Low/High) — severity weighting |

**Key columns extractable from data:**
- `eit_flag`, `pat_flag`, `nat_flag` — MCP Server DB
- `exploitable_combo` (boolean) — MCP Server DB
- `parasitic_toolchain_member` — MCP Server DB
- `credential_leakage` — 67K Dataset
- `harm_category` (direct/exfiltration) — InjecAgent
- `confidentiality_impact` (None/Low/High) — CVSS

**Computation:** Classify tool by EIT/PAT/NAT flags. Check arguments for sensitive values
(regex patterns for tokens, paths, PII). Cross-reference with session history: if previous
call accessed PAT-flagged tool and current call targets NAT-flagged tool → parasitic toolchain
alert (score 9-10). The 27.2% exploitable-combination rate calibrates the session-level scoring.

**Grade: A** — 4 data sources, 80K+ records. Parasitic toolchain data is unique.

---

### Dim 5: Injection Exposure

**Proxy question:** "Is this tool call a channel for prompt injection — either inbound (attacker → agent) or outbound (tool output → agent)?"

**What the proxy checks:**
- Do the tool's inputs come from untrusted sources? (user-provided URLs, web content, emails)
- Does the tool return content that the agent will interpret as instructions?
- Do the current arguments contain injection patterns?
- Does the tool description itself contain injection payloads?

**Scale (1-10):**

| Score | Injection Risk | What The Proxy Sees |
|-------|---------------|-------------------|
| 1-2 | Minimal | Tool has no external input, returns structured data only |
| 3-4 | Low | Tool reads external content but agent doesn't act on output |
| 5-6 | Medium | Tool ingests untrusted input OR returns free-text the agent interprets |
| 7-8 | High | Tool reads attacker-controlled content (web pages, emails) that agent acts on |
| 9-10 | Critical | Active injection detected in arguments or tool description, multi-step chain |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| AgentDojo (13) | 629 injections | 4 domains, 6 defense baselines. ASR 41.2% → 2.2% with best defense |
| Indirect PI (18) | 1,068 instances | 89 templates × 12 obfuscation types, 28 models. Range: 34.3%-72.4% |
| Synthetic PI (22) | 500 prompts | 10 injection categories, TIVS composite metric, 45.7% mitigation |
| Meta Tool-Use PI (15) | 600 scenarios | 7 injection techniques, 8 threat categories, 3 domains |
| InjecAgent (14) | 1,054 cases | 17 user tools × 62 attacker tools — tool as injection vector |
| ASB (16) | 6 types | 6 attack prompt types ranked by ASR |
| MCP-ITP (10) | 548 cases | Injection via tool description (not just via tool input) — 84.2% ASR |

**Key columns extractable from data:**
- `injection_task` + `user_task` — AgentDojo
- `attack_template` + `obfuscation_type` (12 types) — Indirect PI
- `injection_category` (10 types) + `TIVS` score — Synthetic PI
- `injection_technique` (7 types) + `threat_category` (8 types) — Meta Tool-Use PI
- `harm_type` + `attacker_tool` — InjecAgent
- `attack_prompt_type` (6 types) — ASB
- `poisoned_description` + `asr` — MCP-ITP
- `defense_baseline` + `asr_after_defense` — AgentDojo

**Computation:** Analyze tool inputs for injection patterns using the 12-obfuscation coverage
check from Indirect PI. Classify injection technique from Meta Tool-Use PI's 7-type taxonomy.
Check tool description for poisoning (MCP-ITP methodology — overlaps with Dim 1 but here
focused on injection payload, not integrity). Use AgentDojo's defense baselines to estimate
post-defense residual risk. Combine sub-metrics using Synthetic PI's TIVS template
(ISR + POF + PSR + CCS → single score).

**Grade: A** — 7 data sources, 4,400+ labeled injection instances. Strongest cross-benchmark coverage.

---

### Dim 6: Blast Radius

**Proxy question:** "If this tool call goes wrong — is exploited, misused, or fails — how much damage results?"

**What the proxy checks:**
- Can the action be reversed? (read-only vs write vs delete vs execute)
- What's the scope of impact? (single file vs entire system vs external services)
- Does the MCP protocol amplify the damage? (+23-41% from protocol features)
- Which architecture layer is affected? (host=contained, protocol=everything)

**Scale (1-10):**

| Score | Blast Radius | Impact Scope | Reversibility |
|-------|-------------|-------------|---------------|
| 1-2 | Contained | Single resource, read-only | Fully reversible / no change |
| 3-4 | Limited | Single service, write access | Reversible with effort |
| 5-6 | Moderate | Multiple resources, data modification | Partially reversible |
| 7-8 | Wide | Cross-service, credential exposure, host-level | Difficult to reverse |
| 9-10 | Catastrophic | System-wide, arbitrary execution, external cascade | Irreversible |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| MCPSecBench (05) | 17 types × 4 surfaces | Surface-level ASR: Protocol=100%, Server=47%, Client=33%, Host=27%. Directly maps surface → blast radius |
| Component PoC (08) | 132 servers | Protocol amplification: +23-41% over non-MCP. Detection: 3.3%. Shows MCP makes damage worse |
| MCP-SafetyBench (06) | 5 domains × 20 types | Domain severity tiers: Financial (catastrophic) > Repository (wide) > Browser (moderate) > Navigation (limited) > Web Search (contained) |
| CVSS (11) | 31,000+ CVEs | Integrity Impact + Availability Impact + Scope metric — proven formula for blast radius |
| MCP-AttackBench (03) | 70,448 samples | 3 attack families with cascade stages (I/II/III) — multi-stage damage escalation |

**Key columns extractable from data:**
- `attack_surface` + `asr` — MCPSecBench
- `protocol_amplification` (%) — Component PoC
- `domain` + `severity_tier` — MCP-SafetyBench
- `integrity_impact`, `availability_impact`, `scope` — CVSS
- `cascade_stage` (I/II/III) — MCP-AttackBench

**Computation:** Start from CVSS Integrity + Availability + Scope sub-metrics (proven formula).
Apply MCP-specific modifiers:
- Surface multiplier from MCPSecBench (protocol surface = 3.7× host surface in ASR)
- Protocol amplification from Component PoC (+23-41%)
- Domain severity from MCP-SafetyBench (Financial=1.0×, Web Search=0.3×)
- Cascade stage from MCP-AttackBench (Stage III = full blast)

**Grade: A** — 5 data sources, 100K+ records. CVSS provides the formula, MCP benchmarks calibrate it.

---

### Dim 7: Cross-Tool Escalation

**Proxy question:** "Does this tool call, combined with what happened earlier in the session, create a dangerous escalation pattern?"

**What the proxy checks:**
- Tool sequence: did the agent read credentials → now calling network tool? (exfiltration chain)
- Parasitic toolchain: is this the EIT → PAT → NAT pattern? (90% success rate)
- Privilege escalation: is each successive call gaining more access?
- Behavioral drift: has the agent's behavior changed since the session started?
- Multi-turn manipulation: has the conversation been steered toward dangerous calls?

**Scale (1-10):**

| Score | Escalation Level | Session Pattern |
|-------|-----------------|----------------|
| 1-2 | No escalation | First call in session, or calls are independent/unrelated |
| 3-4 | Minor sequence | Related calls but no privilege gain or data flow between them |
| 5-6 | Moderate chain | 2-3 calls with increasing scope, data flows between tools |
| 7-8 | Dangerous chain | Active privilege escalation or data exfiltration sequence detected |
| 9-10 | Parasitic toolchain | Full EIT→PAT→NAT chain, or rug-pull pattern, or multi-step injection chain |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| MCP Server DB (07) | 1,360 servers | Parasitic toolchain: 10 tested chains, 90% success rate. EIT+PAT+NAT combination risk: 27.2% of servers |
| MCPTox (04) | 1,497 cases | Multi-step attack paradigms: Explicit → Implicit-FH → Implicit-PT escalation |
| R-Judge (12) | 569 records | 27 risk scenarios in multi-turn agent interactions — sequential risk patterns |
| Trust Paradox (21) | 19 scenarios | Temporal convergence (8-15 iterations), trust drift over time |
| MCP-SafetyBench (06) | multi-turn | Multi-turn sustained attacks across 5 domains and 13 models |
| Component PoC (08) | 132 servers | 5 modular components — compositional attack building blocks |

**Key columns extractable from data:**
- `eit_flag` + `pat_flag` + `nat_flag` (per tool in session) — MCP Server DB
- `parasitic_chain_success` (boolean) — MCP Server DB
- `attack_paradigm` (escalation ladder) — MCPTox
- `scenario_id` + `risk_type` (sequential) — R-Judge
- `convergence_iterations` + `tci_drift` — Trust Paradox
- `dialogue_turn` + `attack_success` — MCP-SafetyBench

**Computation:** Track tool call sequence in session. For each new call:
1. Check if current tool + any previous tool forms a known dangerous combination (EIT+PAT, PAT+NAT, EIT+PAT+NAT)
2. Compute privilege delta: is each call requesting higher permissions?
3. Track data flow: did a previous tool output become this tool's input? (exfiltration indicator)
4. Apply temporal drift check from Trust Paradox: has the agent's behavior changed over 8-15 turns?
5. Score = max(combination_risk, escalation_pattern, exfiltration_indicator)

**Grade: B+** — 6 data sources, varied row counts. Parasitic toolchain data is unique and powerful.
Temporal drift data is thin (19 scenarios) but the methodology is sound.

---

## 4. Agent Trust as a Modifier (Not a Dimension)

**Why it's a modifier, not a dimension:**
The agent's trustworthiness (which LLM backend, how reliable, what biases) is a property of the
**agent**, not of the **tool call**. The same tool call has the same inherent risk whether GPT-4o
or Claude makes it. But the *likelihood* of the agent being manipulated into making a dangerous
call differs by model.

**How it works:**

```
Final Score = Base Score (from 7 dims) × Agent Trust Modifier
```

| Agent Trust Level | Modifier | Basis |
|------------------|----------|-------|
| Verified/High Trust | 0.8× | DecodingTrust top-tier, MCPTox ASR < 40% for this model |
| Standard Trust | 1.0× | Average performer across benchmarks |
| Low Trust | 1.2× | MCPTox ASR > 60%, or unverified model |
| Unknown/Untested | 1.3× | No benchmark data available |

**Data sources:**
- DecodingTrust (19): 8 dimensions, GPT-4/3.5 baselines
- TrustLLM (20): 6 dimensions, 16 LLMs, 30+ datasets
- Trust Paradox (21): TCI 0.72-0.89, 4 backends, 5 capability tiers
- MCPTox (04): Model-specific ASR — GPT-4o 61.8%, Claude 34.3%
- MCP-ITP (10): 12 models tested, vulnerability range
- Indirect PI (18): 28 models, vulnerability 34.3%-72.4%

This keeps the trustworthiness data in the system without making it a standalone risk dimension
of the tool call.

---

## 5. Dimension Mapping: v1 → v2

### What Got Absorbed, What's New

| v1 Dimension | v2 Fate | Rationale |
|-------------|---------|-----------|
| D1 Attack Category | → **Dim 2 Request Sensitivity** | Attack type is identified from the request arguments, not independently |
| D2 Attack Severity | → **Dim 2 Request Sensitivity** + **Dim 6 Blast Radius** | Split: likelihood goes to request, impact goes to blast radius |
| D3 Attack Surface | → **Dim 6 Blast Radius** | Which layer = how big the explosion |
| D4 Tool Toxicity | → **Dim 1 Tool Integrity** | Expanded: poisoning + provenance + registry verification |
| D5 Data Exposure | → **Dim 4 Data Exposure** | Kept, refocused on the specific call + session flow |
| D6 Trustworthiness | → **Agent Trust Modifier** | Model properties ≠ tool call properties |
| D7 Permission Scope | → **Dim 3 Permission Overreach** | Kept, refocused on "more than this task needs" |
| D8 Injection Resilience | → **Dim 5 Injection Exposure** | Refocused: resilience is model-side, exposure is call-side |

### What's New in v2

| New Element | Why It Didn't Exist in v1 |
|------------|--------------------------|
| **Dim 7 Cross-Tool Escalation** | v1 treated each tool call independently. v2 uses session history because the proxy sees everything |
| **Agent Trust Modifier** | v1 had Trustworthiness as a scored dimension. v2 uses it as a multiplier — same data, better role |
| **Request arguments analysis** | v1 focused on tool metadata. v2 also analyzes what the agent is actually passing as arguments |
| **Session-aware Data Exposure** | v1 scored data exposure from tool capabilities. v2 also checks "what data was accessed earlier that could leak through this call" |

---

## 6. Benchmark Coverage Matrix (v2)

| Benchmark | D1 Integ | D2 Req | D3 Perm | D4 Data | D5 Inj | D6 Blast | D7 Escal | Modifier |
|-----------|:--------:|:------:|:-------:|:-------:|:------:|:--------:|:--------:|:--------:|
| 01 MCIP-Bench | | x | | | | | | |
| 02 MCIP Guardian | | x | | | | | | |
| 03 MCP-AttackBench | | x | | | | x | | |
| 04 MCPTox | x | | | | | | x | x |
| 05 MCPSecBench | | x | | | | x | | |
| 06 MCP-SafetyBench | | x | | | | x | x | |
| 07 MCP Server DB | x | | x | x | | | x | |
| 08 Component PoC | x | | | | | x | x | |
| 09 67K Dataset | x | | x | x | | | | |
| 10 MCP-ITP | x | | | | x | | | x |
| 11 NVD/CVSS | | x | x | x | | x | | |
| 12 R-Judge | | x | | | | | x | |
| 13 AgentDojo | | | | | x | | | |
| 14 InjecAgent | | | | x | x | | | |
| 15 Meta Tool-Use PI | | | | | x | | | |
| 16 ASB | | | | | x | | | |
| 17 MiniScope | | | x | | | | | |
| 18 Indirect PI | | | | | x | | | x |
| 19 DecodingTrust | | | | | | | | x |
| 20 TrustLLM | | | | | | | | x |
| 21 Trust Paradox | | | | | | | x | x |
| 22 Synthetic PI | | | | | x | | | |

**Coverage:** All 22 benchmarks mapped. No orphan files. Every benchmark feeds at least one
dimension or the modifier.

---

## 7. Updated JSON Output Structure

```json
{
  "risk_score": 9.2,
  "risk_level": "CRITICAL",
  "dimensions": {
    "tool_integrity": 3,
    "request_sensitivity": 9,
    "permission_overreach": 7,
    "data_exposure": 8,
    "injection_exposure": 4,
    "blast_radius": 9,
    "cross_tool_escalation": 6
  },
  "agent_trust_modifier": 1.2,
  "base_score_before_modifier": 7.7,
  "justification": "Agent is requesting filesystem_write to /etc/passwd — critical system file (request_sensitivity=9). Write operation is irreversible with system-wide impact (blast_radius=9). Tool permissions grant unrestricted path access beyond what this task requires (permission_overreach=7). Previous call accessed user database, creating a potential data flow to this write (data_exposure=8). Agent backend (GPT-4o) has 61.8% attack susceptibility in MCPTox benchmarks (modifier=1.2).",
  "recommendation": "DENY — request manual approval",
  "confidence": 0.94
}
```

---

## 8. Summary

| Aspect | v1 | v2 |
|--------|----|----|
| **Perspective** | MCP ecosystem + LLM properties | Agent-tool boundary interaction |
| **Core question** | "What are the risks?" (general) | "Is THIS call by THIS agent safe RIGHT NOW?" (specific) |
| **Dimensions** | 8 standalone | 7 boundary + 1 modifier |
| **Signal scope** | Mostly tool metadata | Tool metadata + request args + session history |
| **Session awareness** | None | Dim 7 Cross-Tool Escalation tracks session patterns |
| **Agent trust** | Standalone dimension (D6) | Modifier that adjusts overall score |
| **Benchmarks used** | 22 | 22 (same data, better-focused dimensions) |
| **Data lost** | — | 0 rows lost. Same data, reorganized around the boundary |
