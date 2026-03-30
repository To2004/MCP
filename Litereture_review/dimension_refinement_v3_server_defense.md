# MCP-RSS Dimension Refinement v3: Server-Defense Orientation

## 1. Motivation for v3

### The Reframe

The project description was clarified to:

> **"MCP Security is a defense-oriented risk scoring framework that protects MCP (Model Context Protocol) servers from malicious or risky agent behavior."**

This establishes one clear direction: the **server** is the asset being protected, and the **agent** is the potential threat. Every dimension must answer: **"How does this agent threaten MY server?"**

### What Was Wrong With v2

v2 (see `dimension_refinement_v2_agent_boundary.md`) had 7 dimensions + 1 modifier focused on the "agent-tool boundary." When tested against the server-defense framing, 2 of 7 dimensions pointed the wrong direction:

| v2 Dimension | What It Actually Evaluated | Problem |
|-------------|--------------------------|---------|
| Dim 1: Tool Integrity | Is the **tool** poisoned/malicious? | Protects the **agent** from a bad tool — wrong direction |
| Dim 5: Injection Exposure | Can external content **manipulate the agent**? | Protects the **agent** from injection — wrong direction |
| Agent Trust Modifier | How easily can the **agent be manipulated**? | Measures agent vulnerability, not agent threat |

Dims 2, 3, 4, 6, 7 were correctly oriented (evaluate agent threat to server).

### What v3 Does Differently

v3 goes back to the original 11 benchmark dimensions and re-derives the set with one strict filter: **every dimension must evaluate the risk that the agent's behavior poses to the MCP server.**

Dimensions that previously protected the agent (Tool Toxicity, Injection Resilience, Input Manipulation) are reframed: a compromised agent is the server's problem. The same data is used, but the interpretation flips from "protecting the agent" to "a vulnerable agent is a dangerous agent."

---

## 2. Evaluation of All 11 Original Dimensions

### The Server-Defense Test

For each dimension: **"Does this evaluate how the AGENT threatens the SERVER?"**

| # | Original Dimension | Grade | Protects Server From Agent? | Verdict |
|---|---|---|---|---|
| D1 | Attack Type/Category | A | **Partial** — classifies attacks generically, includes both agent→server and tool→agent attack types | KEEP, filter to agent-originated actions |
| D2 | Attack Surface | B | **Partial** — describes MCP layers, not directional | KEEP, reframe as "which server asset is exposed" |
| D3 | Attack Severity | A | **Yes** — impact on target (server) if attack succeeds | KEEP |
| D4 | Risk Type | B | **Partial** — same data as D1, overlaps | MERGE into D1 |
| D5 | Tool Toxicity | B | **No** — protects agent from poisoned tools | REFRAME: poisoned agent = bigger threat to server |
| D6 | Data Exposure | A | **Yes** — agent stealing/leaking server data | KEEP |
| D7 | Trust Calibration | C | **Partial** — measures agent vulnerability gap, only 19 scenarios | MERGE into modifier |
| D8 | Trustworthiness | A | **Partial** — measures agent reliability, not specific request risk | KEEP as modifier |
| D9 | Protocol Amplification | C | **Partial** — amplifies damage but only ~200 rows | MERGE into severity |
| D10 | Permission Scope | B | **Yes** — agent requesting excess server access | KEEP |
| D11 | Injection Resilience | A | **No** — protects agent from injection, not server from agent | REFRAME: vulnerable agent = weapon pointed at server |
| D12 | Input Manipulation | C | **No** — same direction as D11 | MERGE with D11 reframe |

### The Key Insight

D5, D11, and D12 all point the wrong way individually — they evaluate threats TO the agent. But combined and reframed, they answer a server-defensive question: **"Is this agent compromised (by poisoning or injection), making it a greater threat to my server?"**

A compromised agent is the server's problem. The server operator doesn't care WHY the agent is dangerous — they care THAT it is dangerous. Whether the agent is intentionally malicious, manipulated by prompt injection, or steered by a poisoned tool description, the result is the same: harmful requests hitting the server.

---

## 3. The v3 Dimension Set: 6 Dimensions + 1 Modifier

### Overview

Every dimension answers: **"How does this agent threaten MY server?"**

| # | Dimension | Server's Question | Signal Layer | Scale |
|---|-----------|------------------|-------------|-------|
| 1 | **Agent Action Severity** | How dangerous is this request to my resources? | Tool metadata + Request args (dynamic) | 1-10 |
| 2 | **Permission Overreach** | Is the agent requesting more access than it needs? | Tool schema + Request (dynamic) | 1-10 |
| 3 | **Data Exfiltration Risk** | How much of my sensitive data is at risk? | Request + Session (dynamic) | 1-10 |
| 4 | **Cross-Tool Escalation** | Is this session showing escalating threat patterns? | Session history (temporal) | 1-10 |
| 5 | **Agent Compromise Indicator** | Is this agent acting under hostile influence? | All layers (dynamic) | 1-10 |
| 6 | **Resource Consumption Risk** | Is this agent abusing my server resources? | Session metrics (temporal) | 1-10 |
| Mod | **Agent Trust Modifier** | How much should I trust this agent overall? | Agent identity (static) | 0.7-1.4× |

### Dimension Flow Through the Proxy

```
Agent ──► [tools/call request] ──► MCP-RSS Proxy ──► MCP Server
                                        │
                                        ├─ Dim 1: Agent Action Severity    ← metadata + args
                                        ├─ Dim 2: Permission Overreach     ← schema + args
                                        ├─ Dim 3: Data Exfiltration Risk   ← args + session
                                        ├─ Dim 4: Cross-Tool Escalation    ← session history
                                        ├─ Dim 5: Agent Compromise Indicator ← all signals
                                        ├─ Dim 6: Resource Consumption Risk ← session metrics
                                        │
                                        ├─ Modifier: Agent Trust Level     ← agent identity
                                        │
                                        └─► Risk Score (1-10) + Breakdown + Justification
```

### Why Each Passes the Server-Defense Test

| Dimension | How the agent threatens the server |
|-----------|-----------------------------------|
| Agent Action Severity | Agent requesting a dangerous operation ON the server's resources |
| Permission Overreach | Agent claiming excess access TO the server beyond task needs |
| Data Exfiltration Risk | Agent stealing or leaking data FROM the server |
| Cross-Tool Escalation | Agent systematically expanding its foothold ON the server over time |
| Agent Compromise Indicator | Compromised agent acting as a proxy attacker AGAINST the server |
| Resource Consumption Risk | Agent exhausting the server's computational resources |
| Agent Trust Modifier | Untrustworthy agent model = bigger overall threat TO the server |

---

## 4. Dimension Specifications

### Dim 1: Agent Action Severity

**Server's question:** "How dangerous is what this agent is trying to do to my resources, RIGHT NOW?"

**What the proxy checks:**
- What operation is being requested? (read vs write vs delete vs execute)
- What server resource is targeted? (public API vs database vs filesystem vs system config)
- Do the argument values match known attack patterns?
- Does the MCP protocol amplify the damage potential?

**Absorbs from original 11:** D1 (Attack Type, filtered to agent-originated), D3 (Attack Severity), D2 (Attack Surface, reframed as server asset), D4 (Risk Type), D9 (Protocol Amplification)

**Scale (1-10):**

| Score | Severity Level | Example Request |
|-------|---------------|----------------|
| 1-2 | Safe | `weather.get(city="London")` — public data, read-only |
| 3-4 | Low | `file.read(path="./config.json")` — local file, read-only |
| 5-6 | Medium | `db.query(sql="SELECT * FROM users")` — data access, broad scope |
| 7-8 | High | `file.write(path="/etc/hosts", content=...)` — system file, write |
| 9-10 | Critical | `shell.execute(cmd="rm -rf /")` — arbitrary execution, destructive |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| MCIP-Bench (01) | 2,218 | 10 risk categories with function call arguments — labeled request-level risk |
| MCIP Guardian (02) | 13,830 | 11-class risk type distribution — primary training set for request classification |
| MCP-AttackBench (03) | 70,448 | Binary attack/benign labels + 3 attack families + cascade stages (I/II/III) |
| MCPSecBench (05) | 17 types × 4 surfaces | ASR per attack type and surface — empirical severity ranking. Surface→impact: Protocol=100%, Server=47%, Client=33%, Host=27% |
| MCP-SafetyBench (06) | 20 types × 5 domains | Domain severity weighting: Financial (9-10) > Repository (8-9) > Browser (7-8) > Navigation (5-6) > Web Search (3-4) |
| NVD/CVSS (11) | 31,000+ CVEs | Description-to-severity methodology — 8 base metrics, proven scoring formula |
| R-Judge (12) | 569 records | 27 risk scenarios across 5 app categories — multi-turn request risk |
| Component PoC (08) | 132 servers | Protocol amplification: +23-41% over non-MCP. Severity modifier when MCP-specific features present |

**Key columns extractable from data:**
- `risk_category` (11 classes) — MCIP-Bench, MCIP Guardian
- `binary_label` (attack/benign) — MCP-AttackBench
- `attack_type` (17 types) + `attack_surface` (4 types) — MCPSecBench
- `domain` + `attack_type` (5 × 20) + `asr` — MCP-SafetyBench
- `cvss_base_score` + `description` + 8 sub-metrics — NVD/CVSS
- `function_call` + `arguments` (JSON) — MCIP-Bench
- `protocol_amplification` (%) — Component PoC
- `cascade_stage` (I/II/III) — MCP-AttackBench

**Computation:** Classify the request from tool name + arguments using the unified taxonomy
(MCIP 10 types → MCPSecBench 17 types → MCP-SafetyBench domain weighting). Use MCIP Guardian's
13,830 labeled samples as primary training set. Adapt CVSS base score formula with MCP-specific
sub-metrics. Apply domain severity modifier from MCP-SafetyBench. Apply protocol amplification
(+23-41% from Component PoC) when MCP-specific features (tool_list_changed, auto-approve, SSE)
are present. Use cascade stage from MCP-AttackBench as escalation indicator (Stage III = max severity).

**Grade: A** — 8 data sources, 118K+ rows. Strongest data coverage of any dimension.

---

### Dim 2: Permission Overreach

**Server's question:** "Is this agent requesting more access to my resources than this task actually requires?"

**What the proxy checks:**
- What permissions does this tool grant vs what the request actually needs?
- Over-privilege ratio: granted scopes vs minimum required
- Sensitivity of excess permissions (read < write < delete < admin)

**Absorbs from original 11:** D10 (Permission Scope)

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

**Why this dimension matters for enterprise:** Most actionable dimension. Reducing permissions is
the simplest, cheapest risk mitigation a server operator can deploy immediately. No ML needed —
just scope comparison.

**Grade: B+** — 4 data sources, 67K+ records. MiniScope provides rare ground-truth labels.

---

### Dim 3: Data Exfiltration Risk

**Server's question:** "How much of my sensitive data is this agent trying to access, and could it leak that data?"

**What the proxy checks:**
- What data can this tool access? (EIT/PAT/NAT classification)
- What is the agent sending as arguments? (credentials, PII, internal data?)
- What did the agent access earlier in the session that could leak through this call?
- Is this a data exfiltration pattern? (read PII → send to network tool)

**Absorbs from original 11:** D6 (Data Exposure) + session-aware exfiltration detection

**Scale (1-10):**

| Score | Exfiltration Risk | What The Proxy Sees |
|-------|------------------|-------------------|
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

### Dim 4: Cross-Tool Escalation

**Server's question:** "Does this agent's request, combined with its earlier requests in this session, create a dangerous pattern of escalating access to my resources?"

**What the proxy checks:**
- Tool sequence: did the agent read credentials → now calling a network tool? (exfiltration chain)
- Parasitic toolchain: is this the EIT → PAT → NAT pattern? (90% success rate)
- Privilege escalation: is each successive call gaining more server access?
- Behavioral drift: has the agent's behavior changed since the session started?
- Multi-turn manipulation: has the conversation been steered toward dangerous calls?

**Absorbs from original 11:** v2 Cross-Tool Escalation concept + D7 (Trust Calibration temporal data)

**Scale (1-10):**

| Score | Escalation Level | Session Pattern |
|-------|-----------------|----------------|
| 1-2 | No escalation | First call in session, or calls are independent/unrelated |
| 3-4 | Minor sequence | Related calls but no privilege gain or data flow between them |
| 5-6 | Moderate chain | 2-3 calls with increasing scope, data flows between tools |
| 7-8 | Dangerous chain | Active privilege escalation or data exfiltration sequence detected |
| 9-10 | Parasitic toolchain | Full EIT→PAT→NAT chain, or rug-pull pattern, or multi-step attack chain |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| MCP Server DB (07) | 1,360 servers | Parasitic toolchain: 10 tested chains, 90% success rate. EIT+PAT+NAT combination risk: 27.2% of servers |
| MCPTox (04) | 1,497 cases | Multi-step attack paradigms: Explicit → Implicit-FH → Implicit-PT escalation ladder |
| R-Judge (12) | 569 records | 27 risk scenarios in multi-turn agent interactions — sequential risk patterns |
| Trust Paradox (21) | 19 scenarios | Temporal convergence (8-15 iterations), trust drift over time, TCI 0.72-0.89 |
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
2. Compute privilege delta: is each call requesting higher server permissions?
3. Track data flow: did a previous tool output become this tool's input? (exfiltration indicator)
4. Apply temporal drift check from Trust Paradox: has the agent's behavior changed over 8-15 turns?
5. Score = max(combination_risk, escalation_pattern, exfiltration_indicator)

**Grade: B+** — 6 data sources, varied row counts. Parasitic toolchain data is unique and powerful.
Temporal drift data is thin (19 scenarios) but the methodology is sound.

---

### Dim 5: Agent Compromise Indicator

**Server's question:** "Is this agent likely acting under external influence (poisoned tools, prompt injection, manipulation) that makes it a greater threat to my server?"

**What the proxy checks:**
- Has the agent been exposed to poisoned tool descriptions in this session?
- Does the agent's model backend have high injection vulnerability?
- Do the current request arguments contain injection patterns?
- Has the agent's behavior shifted compared to earlier in the session?
- Does the request pattern match known injection-driven behavior?

**Why this is server-defensive:** A compromised agent is the server's problem. Even though
the agent is the "victim" of the injection or poisoning, the SERVER bears the consequences
when the compromised agent sends harmful requests. The server operator needs to know:
"Is this agent likely acting under hostile influence? If so, treat all its requests with
heightened suspicion."

**Absorbs from original 11:** D5 (Tool Toxicity — reframed), D11 (Injection Resilience — reframed), D12 (Input Manipulation — reframed)

**Scale (1-10):**

| Score | Compromise Level | What The Proxy Sees |
|-------|-----------------|-------------------|
| 1-2 | No indicators | Agent model has low injection vulnerability (ASR <10%), no suspicious patterns |
| 3-4 | Low risk | Agent model has moderate vulnerability (ASR 10-30%), no active indicators |
| 5-6 | Elevated | Agent exposed to suspicious tool descriptions in session, or model has high vulnerability (ASR 30-50%) |
| 7-8 | High | Request pattern matches known injection-driven behavior, or confirmed poisoned tool in session |
| 9-10 | Confirmed compromise | Active injection payload detected in arguments, or agent behavior drastically shifted mid-session |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| MCPTox (04) | 1,497 cases | 3 attack paradigms across 353 real tools, per-model ASR: GPT-4o 61.8%, Claude 34.3% |
| MCP-ITP (10) | 548 × 12 models | Implicit poisoning ASR: 84.2%. Detection by existing tools: 0.3%. Tool description poisoning |
| AgentDojo (13) | 629 injections | 4 domains, 6 defense baselines. ASR 41.2% → 2.2% with best defense |
| Indirect PI (18) | 1,068 instances | 89 templates × 12 obfuscation types, 28 models. Vulnerability range: 34.3%-72.4% |
| Synthetic PI (22) | 500 prompts | 10 injection categories, TIVS composite metric, 45.7% mitigation |
| Meta Tool-Use PI (15) | 600 scenarios | 7 injection techniques, 8 threat categories, 3 domains |
| InjecAgent (14) | 1,054 cases | 17 user tools × 62 attacker tools — tool as injection vector |
| ASB (16) | 6 types | 6 attack prompt types ranked by ASR |
| Component PoC (08) | 132 servers | Scanner detection: 3.3% — evasion baseline for compromised agents |

**Key columns extractable from data:**
- `tool_description_poisoned` + `attack_paradigm` — MCPTox
- `poisoned_description` + `steering_words` + `detection_by_defense` — MCP-ITP
- `injection_task` + `defense_baseline` + `asr` — AgentDojo
- `obfuscation_type` (12 types) + `model_vulnerability_rate` — Indirect PI
- `attack_category` (10 types) + `tivs` score — Synthetic PI
- `injection_technique` (7 types) + `threat_category` (8 types) — Meta Tool-Use PI
- `attacker_tools` (62) + `harm_type` — InjecAgent
- `attack_prompt_type` (6 types) — ASB
- `asr_per_model` — MCPTox, MCP-ITP, Indirect PI

**Computation:** Multi-signal assessment:
1. Check if the agent's model backend has high injection vulnerability (MCPTox per-model ASR, Indirect PI per-model rates)
2. Check if tools in the current session have suspicious descriptions (MCP-ITP methodology — analyze for implicit steering words)
3. Check if the agent's current request arguments contain injection patterns (12-obfuscation coverage from Indirect PI, 7-technique taxonomy from Meta Tool-Use PI)
4. Check if the agent's behavior has shifted compared to earlier in the session (Trust Paradox temporal drift)
5. Combine sub-signals using Synthetic PI's TIVS template (ISR + POF + PSR + CCS → single score)

**The critical reframe:** The same data that v2 used for "protecting the agent" is now used to assess
"how dangerous is this agent to the server BECAUSE it may be compromised." The 84.2% implicit
poisoning ASR (MCP-ITP) means most agents CAN be weaponized. The 0.3% detection rate means most
other defenses won't catch it. This dimension specifically catches the gap.

**Grade: A** — 9 data sources, 6K+ direct rows plus model vulnerability profiles across 28+ models.

---

### Dim 6: Resource Consumption Risk

**Server's question:** "Is this agent consuming or requesting excessive server resources?"

**What the proxy checks:**
- Rate of tool calls from this agent/session (calls per unit time)
- Computational cost of the requested operation
- Cumulative session resource consumption
- Pattern: is the agent systematically probing or flooding?

**Absorbs from original 11:** NEW — no original equivalent. This is a gap the original 11 did not
capture because the benchmarks focused on qualitative attack types, not quantitative resource abuse.

**Scale (1-10):**

| Score | Consumption Level | What The Proxy Sees |
|-------|------------------|-------------------|
| 1-2 | Normal | Request rate and cost within expected baseline |
| 3-4 | Above average | Slightly elevated rate or moderately expensive operation |
| 5-6 | Elevated | Sustained high-volume requests or computationally expensive operations |
| 7-8 | Excessive | Systematic high-volume pattern, or very expensive operations repeated |
| 9-10 | Abusive | Obvious DoS behavior, resource exhaustion, or rapid-fire probing |

**Data sources:**

| Dataset | Rows | What It Provides |
|---------|------|-----------------|
| MCPSecBench (05) | cost data | Cost per round: $0.41-$0.76 — baseline for cost-per-request |
| MiniScope (17) | latency data | Latency overhead: 1-6% — runtime cost baseline |
| 67K Dataset (09) | ecosystem stats | Normal request patterns from 67,057 servers — baseline rates |

**Computation:** Rule-based (no ML needed):
1. Track calls per minute from this agent/session
2. Estimate computational cost per request (based on operation type)
3. Track cumulative session resource consumption
4. Compare to baseline rates from ecosystem data
5. Flag patterns: rapid sequential calls, repeated expensive operations, systematic capability probing

**Data gap acknowledged:** No benchmark explicitly measures agent-to-server resource abuse. This
dimension is implemented purely with rules (rate counters, cost thresholds). This is a future
data collection opportunity — creating a labeled dataset of normal vs abusive agent request
patterns would strengthen this dimension.

**Grade: D** — Conceptually important for server defense, but data-poor. Rule-based implementation
is practical and does not require ML training data.

---

## 5. Agent Trust Modifier (Not a Dimension)

**Server's question:** "Based on what I know about this agent's model and track record, should I adjust my overall threat assessment up or down?"

**Why it's a modifier, not a dimension:**
The agent's intrinsic properties (which model, how reliable, what biases) affect the
*likelihood* of dangerous behavior but don't describe a specific risk of a specific request.
The same `file.write("/etc/passwd")` request is equally dangerous regardless of which model
sends it. But the probability of an agent being manipulated into sending that request differs
by model.

**Absorbs from original 11:** D8 (Trustworthiness) + D7 (Trust Calibration)

**How it works:**

```
Final Score = Base Score (from 6 dims) × Agent Trust Modifier
```

| Agent Trust Level | Modifier | Basis |
|------------------|----------|-------|
| Verified / High Trust | 0.7× | DecodingTrust top-tier, MCPTox ASR < 30%, verified agent identity |
| Established Trust | 0.85× | Known model with moderate safety scores |
| Standard / Unknown | 1.0× | Default — no data to adjust |
| Low Trust | 1.2× | MCPTox ASR > 50%, poor safety benchmarks |
| Untrusted / Flagged | 1.4× | No benchmark data, or known unsafe model, or previously flagged |

**Data sources:**
- DecodingTrust (19): 8 dimensions, GPT-4/3.5 baselines
- TrustLLM (20): 6 dimensions, 16 LLMs, 30+ datasets
- Trust Paradox (21): TCI 0.72-0.89, 4 backends, 5 capability tiers
- MCPTox (04): Model-specific ASR — GPT-4o 61.8%, Claude 34.3%
- MCP-ITP (10): 12 models tested, vulnerability range
- Indirect PI (18): 28 models, vulnerability 34.3%-72.4%

**Grade: A** — 6 data sources, 28+ models profiled.

---

## 6. Dimension Evolution: v1 → v2 → v3

### What Changed At Each Stage

| Stage | Dimensions | Core Question | Perspective |
|-------|-----------|--------------|-------------|
| v1 (11→8) | 8 standalone | "What risks exist in the MCP ecosystem?" | Ecosystem-wide |
| v2 (8→7+1) | 7 boundary + 1 modifier | "Is THIS call by THIS agent safe RIGHT NOW?" | Agent-tool boundary |
| **v3 (11→6+1)** | **6 server-defense + 1 modifier** | **"How does this agent threaten MY server?"** | **Server operator** |

### v2 → v3 Dimension Mapping

| v2 Dimension | v3 Fate | Why |
|-------------|---------|-----|
| Dim 1: Tool Integrity | → **Dim 5: Agent Compromise Indicator** (absorbed) | Tool integrity protects the agent, not the server. Reframed: if the tool is poisoned, the agent is compromised, making it dangerous to the server |
| Dim 2: Request Sensitivity | → **Dim 1: Agent Action Severity** (expanded) | Kept and expanded: merged with attack surface, severity, and protocol amplification into one comprehensive "how dangerous is this request" dimension |
| Dim 3: Permission Overreach | → **Dim 2: Permission Overreach** (kept) | Already server-defensive. Unchanged |
| Dim 4: Data Exposure | → **Dim 3: Data Exfiltration Risk** (refocused) | Refocused from general "data flows through this call" to explicitly "agent stealing server data" |
| Dim 5: Injection Exposure | → **Dim 5: Agent Compromise Indicator** (absorbed) | Injection protects the agent, not the server. Reframed: injection vulnerability = agent is a loaded weapon pointed at server |
| Dim 6: Blast Radius | → **Dim 1: Agent Action Severity** (absorbed) | Blast radius is the impact component of severity. Merged into the comprehensive severity dimension |
| Dim 7: Cross-Tool Escalation | → **Dim 4: Cross-Tool Escalation** (kept) | Already server-defensive. Kept with enhanced temporal tracking |
| Agent Trust Modifier | → **Agent Trust Modifier** (kept) | Reframed from "how vulnerable is the agent" to "how much of a threat is this agent's profile to the server" |
| *(none)* | → **Dim 6: Resource Consumption Risk** (NEW) | New dimension capturing volumetric/DoS threats that the original 11 and v2 missed entirely |

### What's New in v3

| New Element | Why It Didn't Exist Before |
|------------|--------------------------|
| **Dim 5: Agent Compromise Indicator** | v1/v2 treated tool poisoning and injection as separate concerns protecting the agent. v3 combines them into a single server-defensive question: "Is this agent compromised?" |
| **Dim 6: Resource Consumption Risk** | Original benchmarks focused on qualitative attack types. No benchmark measured quantitative resource abuse. v3 adds this as a rule-based dimension |
| **Server-defense framing for all dims** | v1 was ecosystem-wide, v2 was boundary-focused. v3 is the first version where every single dimension passes the test "this protects the server from the agent" |

---

## 7. Benchmark Coverage Matrix (v3)

| Benchmark | D1 Sev | D2 Perm | D3 Data | D4 Escal | D5 Comp | D6 Res | Modifier |
|-----------|:------:|:-------:|:-------:|:--------:|:-------:|:------:|:--------:|
| 01 MCIP-Bench | x | | | | | | |
| 02 MCIP Guardian | x | | | | | | |
| 03 MCP-AttackBench | x | | | | | | |
| 04 MCPTox | x | | | x | x | | x |
| 05 MCPSecBench | x | | | | | x | |
| 06 MCP-SafetyBench | x | | | x | | | |
| 07 MCP Server DB | | x | x | x | | | |
| 08 Component PoC | x | | | x | x | | |
| 09 67K Dataset | | x | x | | | x | |
| 10 MCP-ITP | | | | | x | | x |
| 11 NVD/CVSS | x | x | x | | | | |
| 12 R-Judge | x | | | x | | | |
| 13 AgentDojo | | | | | x | | |
| 14 InjecAgent | | | x | | x | | |
| 15 Meta Tool-Use PI | | | | | x | | |
| 16 ASB | | | | | x | | |
| 17 MiniScope | | x | | | | x | |
| 18 Indirect PI | | | | | x | | x |
| 19 DecodingTrust | | | | | | | x |
| 20 TrustLLM | | | | | | | x |
| 21 Trust Paradox | | | | x | | | x |
| 22 Synthetic PI | | | | | x | | |

**Coverage:** All 22 benchmarks mapped. No orphan files. Every benchmark feeds at least one
dimension or the modifier.

---

## 8. Updated JSON Output Structure

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
  "justification": "Agent is requesting filesystem_write to /etc/passwd — critical system file (action_severity=9). Tool permissions grant unrestricted path access beyond task needs (permission_overreach=7). Previous call accessed user database, creating data exfiltration vector (data_exfiltration=8). Session shows escalating privilege pattern: db_read → file_write to system path (escalation=6). Agent model (GPT-4o) has 61.8% ASR in MCPTox — elevated compromise risk (compromise=5, modifier=1.2).",
  "recommendation": "REQUIRE HUMAN APPROVAL",
  "confidence": 0.92
}
```

---

## 9. Scoring Pipeline (v3)

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
│  │ STATIC LAYER        │  Dim 2: Permission Overreach (schema)          │
│  │ (pre-computed)       │                                                │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│  ┌──────────▼──────────┐                                                │
│  │ DYNAMIC LAYER       │  Dim 1: Agent Action Severity (metadata+args)  │
│  │ (per-request)        │  Dim 3: Data Exfiltration Risk (args+session)  │
│  │                      │  Dim 5: Agent Compromise Indicator (all)       │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│  ┌──────────▼──────────┐                                                │
│  │ TEMPORAL LAYER      │  Dim 4: Cross-Tool Escalation (session hist.)  │
│  │ (session-aware)      │  Dim 6: Resource Consumption Risk (metrics)    │
│  │                      │  Agent Trust Modifier (agent identity)         │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│  ┌──────────▼──────────┐                                                │
│  │ SCORE COMPUTATION   │  Weighted combination → Base Score (1-10)      │
│  │                      │  × Agent Trust Modifier (0.7-1.4)             │
│  │                      │  = Final Risk Score                            │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│  ┌──────────▼──────────┐                                                │
│  │ SERVER DECISION     │  1-3: AUTO-ALLOW                               │
│  │                      │  4-6: ALLOW WITH LOGGING                      │
│  │                      │  7-8: REQUIRE HUMAN APPROVAL                  │
│  │                      │  9-10: AUTO-DENY                              │
│  └─────────────────────┘                                                │
└──────────────────────────────────────────────────────────────────────────┘
```

### Static vs Dynamic vs Temporal Dimensions

| Layer | Dimensions | When Computed | Cost |
|-------|-----------|--------------|------|
| **Static** | Dim 2 (Permission Overreach) | Once per tool, cached | Very low — scope comparison |
| **Dynamic** | Dim 1 (Action Severity), Dim 3 (Data Exfiltration), Dim 5 (Compromise Indicator) | Every request | Low-medium — classifier + pattern matching |
| **Temporal** | Dim 4 (Cross-Tool Escalation), Dim 6 (Resource Consumption), Agent Trust Modifier | Accumulated per session | Low — sequence analysis + counters |

---

## 10. Example Scoring Walkthroughs

### High-Risk Call: Agent writes to /etc/passwd

```
Request: filesystem_write(path="/etc/passwd", content="root:x:0:0:...")
Session: Agent previously called db.query("SELECT password FROM users")
Agent: GPT-4o
```

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| Dim 1: Agent Action Severity | 9 | Writing to critical system file — top severity. Protocol surface amplifies |
| Dim 2: Permission Overreach | 8 | filesystem_write has unrestricted path access, task only needs config read |
| Dim 3: Data Exfiltration Risk | 9 | Previous call accessed passwords, now writing to auth file — parasitic chain |
| Dim 4: Cross-Tool Escalation | 8 | db.query(passwords) → filesystem_write(/etc/passwd) = privilege escalation chain |
| Dim 5: Agent Compromise Indicator | 5 | GPT-4o has 61.8% ASR in MCPTox — elevated compromise probability |
| Dim 6: Resource Consumption Risk | 2 | Normal request rate, single operation |
| **Base Score** | **6.8** | Weighted combination |
| Agent Trust Modifier | ×1.2 | GPT-4o: high vulnerability profile |
| **Final Score** | **8.2** | **REQUIRE HUMAN APPROVAL** |

### Low-Risk Call: Agent reads weather

```
Request: weather.get(city="London")
Session: First call in session
Agent: Claude
```

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| Dim 1: Agent Action Severity | 1 | Public data, read-only, no server resource at risk |
| Dim 2: Permission Overreach | 1 | Minimal scope, matches task exactly |
| Dim 3: Data Exfiltration Risk | 1 | Public weather data, no PII, no server secrets |
| Dim 4: Cross-Tool Escalation | 1 | First call, no session history to escalate from |
| Dim 5: Agent Compromise Indicator | 2 | Claude has 34.3% ASR — moderate but no active indicators |
| Dim 6: Resource Consumption Risk | 1 | Single request, normal rate |
| **Base Score** | **1.2** | |
| Agent Trust Modifier | ×0.85 | Claude: established trust, lower vulnerability |
| **Final Score** | **1.0** | **AUTO-ALLOW** |

---

## 11. Data Support Summary

### Dimension Data Grades

| Dimension | Datasets | Total Rows | Grade | Limiting Factor |
|-----------|----------|------------|-------|----------------|
| Dim 1: Agent Action Severity | 8 | 118K+ | **A** | None — strongest data coverage |
| Dim 2: Permission Overreach | 4 | 67K+ | **B+** | MiniScope has only 10 apps (but ground-truth) |
| Dim 3: Data Exfiltration Risk | 4 | 80K+ | **A** | Parasitic toolchain data is unique |
| Dim 4: Cross-Tool Escalation | 6 | varied | **B+** | Temporal drift data thin (19 scenarios), rest strong |
| Dim 5: Agent Compromise Indicator | 9 | 6K+ | **A** | Strongest cross-benchmark injection/poisoning coverage |
| Dim 6: Resource Consumption Risk | 3 | metadata | **D** | No labeled dataset — rule-based implementation |
| Agent Trust Modifier | 6 | 60+ sub-datasets | **A** | 28+ models profiled across multiple benchmarks |

### Total Coverage

- **22/22 benchmarks mapped** — no orphan datasets
- **0 rows discarded** — same data as v1/v2, reorganized around server defense
- **Every dimension backed by 3+ datasets** (except Dim 6 which is rule-based)
- **Every dimension passes the server-defense test**

---

## 12. Summary

| Aspect | v1 | v2 | **v3** |
|--------|----|----|--------|
| **Core question** | "What risks exist?" | "Is THIS call safe?" | **"How does this agent threaten MY server?"** |
| **Perspective** | MCP ecosystem | Agent-tool boundary | **Server operator** |
| **Dimensions** | 8 standalone | 7 boundary + 1 modifier | **6 server-defense + 1 modifier** |
| **Direction test** | Mixed | 5/7 pass | **6/6 pass** |
| **Agent-as-threat dims** | None explicitly | 5 of 7 | **All 6** |
| **Agent-as-victim dims** | D5, D8 | D1 (Tool Integrity), D5 (Injection) | **0 — reframed into Dim 5 (Compromise Indicator)** |
| **New in this version** | — | Cross-Tool Escalation | **Agent Compromise Indicator, Resource Consumption Risk** |
| **Benchmarks used** | 22 | 22 | **22 (same data, server-defense focused)** |
| **Data lost** | — | 0 rows | **0 rows** |
