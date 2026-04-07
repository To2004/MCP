# MCP-SafetyBench

## Source
- **Paper:** MCP-SafetyBench: A Benchmark for Safety Evaluation of Large Language Models with Real-World MCP Servers (Zong et al., 2025)
- **Link:** https://arxiv.org/abs/2512.15163
- **Year:** 2025

## Format & Size
- **Total samples:** Multi-turn interaction test cases across 5 domains and 20 attack types
- **Format:** Multi-turn interaction format with domain-specific MCP server configurations
- **Availability:** arXiv (https://arxiv.org/abs/2512.15163); check for associated repository

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Domain | Categorical (5 classes) | Location Navigation, Repository Management, Financial Analysis, Browser Automation, Web Search | Yes | Primary domain classification |
| Attack type | Categorical (20 types) | Stealth attacks, disruption attacks across server/host/user-side | Yes | Fine-grained attack taxonomy |
| Attack surface | Categorical (3 classes) | Server-side, host-side, user-side | Yes | Where the attack targets |
| Multi-turn dialogue | List of dicts | Sequential user-agent-tool interactions | Yes | Captures sustained attack patterns |
| Target LLM | Categorical (13 models) | GPT-5, Claude-4.0-Sonnet, Gemini-2.5-Pro, Grok-4, etc. | Yes | Broad model coverage |
| TSR (Task Success Rate) | Float | Per-model task completion rate | Yes | Measures functional impact of attacks |
| ASR (Attack Success Rate) | Float | Per-model attack success rate | Yes | Primary security metric |
| DSR (Defense Success Rate) | Float | Per-model defense effectiveness | Yes | Measures resilience |
| Safety prompt effectiveness | Float/Boolean | Impact of safety prompts on ASR/DSR | Yes | Tests a specific defense mechanism |

### Domain Coverage

| Domain | Description | Risk Context |
|---|---|---|
| Location Navigation | Map/GPS MCP tools | Privacy, physical safety |
| Repository Management | GitHub/code MCP tools | Code injection, supply chain |
| Financial Analysis | Finance/trading MCP tools | Financial loss, fraud |
| Browser Automation | Web browsing MCP tools | Data exfiltration, phishing |
| Web Search | Search engine MCP tools | Information manipulation |

### Model Coverage (13 LLMs)
GPT-5, GPT-4.1, GPT-4o, o4-mini, Claude-3.7-Sonnet, Claude-4.0-Sonnet, Gemini-2.5-Pro, Gemini-2.5-Flash, Grok-4, GLM-4.5, Kimi-K2, Qwen3-235B, DeepSeek-V3.1

## Proposed Risk Dimensions

### Domain-Specific Risk Weighting
- **Feeding columns:** Domain (5 classes), ASR per domain
- **Proposed scale:** 1-10 based on domain sensitivity and attack impact
- **Derivation:** Not all domains carry equal risk. Proposed weighting:
  - **Financial Analysis (9-10):** Direct monetary loss potential; regulatory implications
  - **Repository Management (8-9):** Code injection can propagate through supply chains; persistent impact
  - **Browser Automation (7-8):** Data exfiltration, credential theft, phishing execution
  - **Location Navigation (5-6):** Privacy exposure, potential physical safety concerns
  - **Web Search (3-4):** Information manipulation; lower direct impact but enables social engineering

  Refine these weights using the actual per-domain ASR and TSR data from the benchmark.

### Attack Taxonomy Depth
- **Feeding columns:** Attack type (20 types), stealth vs. disruption classification
- **Proposed scale:** 1-10 per attack type
- **Derivation:** The stealth/disruption split provides a natural two-tier classification:
  - **Stealth attacks (6-10):** Designed to avoid detection while achieving malicious goals. Higher risk because they may succeed without triggering alerts.
  - **Disruption attacks (3-6):** Designed to break functionality. Lower risk ceiling because they are more noticeable, but still dangerous for availability.

  Within each tier, rank the specific attack types by their cross-model average ASR.

### Model Resilience Profile
- **Feeding columns:** Per-model TSR, ASR, DSR across all 13 models
- **Proposed scale:** 1-10 vulnerability score per model
- **Derivation:** For each of the 13 models, compute a composite vulnerability score: `vulnerability = (ASR * 0.5) + ((1 - DSR) * 0.3) + ((1 - TSR_under_attack / TSR_baseline) * 0.2)`. This captures three aspects: how often attacks succeed (ASR), how weak the defenses are (1 - DSR), and how much task performance degrades under attack. The 13-model coverage means we can build a vulnerability ranking that covers most production LLMs.

### Multi-Turn Sustained Risk
- **Feeding columns:** Multi-turn dialogue data, turn-by-turn attack progression
- **Proposed scale:** 1-10 based on how risk accumulates over turns
- **Derivation:** Multi-turn format allows tracking whether risk increases, decreases, or stays constant across turns. Compute a "risk trajectory" per interaction: if the attack becomes more effective in later turns (agent becomes more compliant), score 8-10. If the agent recovers and resists in later turns, score 3-5. If risk is constant, score 5-6. This captures a dimension that single-turn benchmarks completely miss.

### Safety Prompt Effectiveness
- **Feeding columns:** ASR/DSR with and without safety prompts
- **Proposed scale:** 1-10 delta representing how much safety prompts reduce risk
- **Derivation:** Compare ASR with safety prompts enabled vs. disabled. If safety prompts reduce ASR by >50%, the baseline risk (without prompts) scores 8-10 but the mitigated risk drops to 3-4. If safety prompts have <10% impact, the risk score stays high regardless. This dimension tells us which attack types are "promptable" (can be defended with instructions) vs. "structural" (require architectural fixes).

## Data Quality Notes
- The exact total sample count is not specified as a single number — it is distributed across 5 domains x 20 attack types x 13 models, with multi-turn interactions. The effective sample count depends on how many test cases per domain-attack-model combination are included.
- The 13-model coverage is the broadest of any MCP benchmark and includes cutting-edge models (GPT-5, Claude-4.0-Sonnet, Grok-4). This makes cross-model comparison highly valuable but also means results will quickly become dated as models are updated.
- The stealth vs. disruption categorization of attacks is useful but coarse — some attacks may have elements of both. Check the paper for how edge cases are classified.
- Multi-turn format is a major strength for realism but makes the data harder to use for simple classifiers. Each interaction is a sequence, not a single-sample classification problem.
- The 3 attack surfaces (server-side, host-side, user-side) overlap with but are not identical to MCPSecBench's 4 surfaces (which adds protocol-side). Mapping between the two benchmarks will require alignment.

## Usefulness Verdict
MCP-SafetyBench is the most comprehensive MCP security benchmark in terms of breadth: 5 real-world domains, 20 attack types, 13 state-of-the-art LLMs, and multi-turn evaluation. For a 1-10 risk scoring system, its main contribution is the domain-specific risk dimension — the insight that a "risky" tool in financial analysis is fundamentally different from a "risky" tool in web search. No other benchmark provides this domain grounding.

The 13-model coverage is extremely valuable for building a model-aware risk scorer. Instead of assuming one risk score fits all agents, this benchmark's data allows computing model-specific vulnerability profiles. Combined with MCPTox's finding that reasoning mode changes attack susceptibility, MCP-SafetyBench's cross-model data enables a risk scoring system that adjusts its output based on which LLM is acting as the agent. The multi-turn format also supports sustained risk assessment — critical for enterprise deployments where agent sessions can be long-running. The triple-metric approach (TSR + ASR + DSR) gives a more complete picture than benchmarks that only measure attack success.
