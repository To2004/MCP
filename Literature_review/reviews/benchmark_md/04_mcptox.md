# MCPTox Dataset

## Source
- **Paper:** MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers (Wang et al., 2025)
- **Link:** https://openreview.net/forum?id=xbs5dVGUQ8
- **Year:** 2025

## Format & Size
- **Total samples:** 1,312-1,497 malicious test cases across 353 authentic tools from 45 live real-world MCP servers
- **Format:** Structured test cases containing user queries paired with poisoned tool descriptions
- **Availability:** OpenReview (https://openreview.net/forum?id=xbs5dVGUQ8); check supplementary materials for dataset release

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| User query | String | Natural language user request | Yes | The benign-looking trigger for the attack |
| Tool description (poisoned) | String | Modified tool description with injected malicious intent | Yes | Core attack vector — the poisoned metadata |
| Tool description (original) | String | Authentic tool description from real MCP server | Yes | Clean baseline for comparison |
| Attack paradigm | Categorical (3 classes) | Explicit Trigger—Function Hijacking, Implicit Trigger—Function Hijacking, Implicit Trigger—Parameter Tampering | Yes | Top-level attack classification |
| Attack category | Categorical (10 classes) | Shadowing, puppet, spoofing, etc. | Yes | Fine-grained attack type |
| MCP server source | String | One of 45 real-world MCP servers | Yes | Provides ecological validity context |
| ASR result | Boolean/float | Success/failure per model | Yes | Ground truth for attack effectiveness |

### Attack Paradigm Breakdown

| Paradigm | Count | % of Total |
|---|---|---|
| Explicit Trigger—Function Hijacking | 224 | ~15-17% |
| Implicit Trigger—Function Hijacking | 548 | ~37-42% |
| Implicit Trigger—Parameter Tampering | 725 | ~48-55% |

## Proposed Risk Dimensions

### Attack Stealth (Detection Difficulty)
- **Feeding columns:** Attack paradigm (3 classes)
- **Proposed scale:** 1-10 based on how hard the attack is to detect
- **Derivation:** The three paradigms directly encode detection difficulty:
  - **Explicit Trigger—Function Hijacking (1-3):** Attack trigger is visible in the query — easiest to catch with keyword/pattern matching
  - **Implicit Trigger—Function Hijacking (4-6):** Trigger is hidden in tool description semantics — requires understanding tool behavior to detect
  - **Implicit Trigger—Parameter Tampering (7-10):** Subtle parameter manipulation with implicit triggers — hardest to detect, requires deep parameter validation

  The distribution (most samples are implicit/parameter tampering) reflects that the harder attacks are more varied and more dangerous.

### Model Vulnerability
- **Feeding columns:** Per-model ASR results
- **Proposed scale:** 1-10 based on how susceptible the target model is
- **Derivation:** Overall ASR is 72.8%, but per-model varies dramatically: GPT-4o (61.8%), Qwen3-32b (58.5%), Claude (34.3%). Map model ASR to risk: a tool/server combination that successfully attacks GPT-4o but fails on Claude has a model-dependent risk profile. For risk scoring, the score should reflect the worst-case model vulnerability (max ASR across models) as the upper bound.

### Reasoning Mode Impact
- **Feeding columns:** ASR with and without reasoning mode enabled
- **Proposed scale:** 1-10 delta score
- **Derivation:** Qwen3-8b shows +27.8% ASR when reasoning is enabled — meaning reasoning mode actually makes the model more susceptible to tool poisoning. This is a critical finding: risk scores should account for whether the agent uses chain-of-thought reasoning. A tool that is safe under default mode but dangerous under reasoning mode needs a conditional risk score.

### Tool Authenticity Risk
- **Feeding columns:** MCP server source (45 servers), tool count (353 tools)
- **Proposed scale:** 1-10 based on how many tools from a server are vulnerable
- **Derivation:** With 45 real servers and 353 tools, compute a per-server vulnerability density: (number of successful attack cases for that server's tools) / (total tools from that server). Servers with high density score 8-10; servers where attacks mostly fail score 1-3.

## Data Quality Notes
- The sample count range (1,312-1,497) suggests some test cases may be conditional or model-dependent. Clarify exact count methodology when using this data.
- This is the only benchmark using real-world MCP servers (45 live servers, 353 authentic tools), giving it ecological validity that synthesized benchmarks lack. However, real-world servers change over time — the tool descriptions captured are snapshots.
- The 10 attack categories (shadowing, puppet, spoofing, etc.) are mentioned but their exact distribution across the 3 paradigms is not fully detailed in the summary — will need to extract this from the paper's appendix.
- The per-model ASR variation is large (Claude at 34.3% vs. GPT-4o at 61.8%), meaning risk scores are inherently model-dependent. A risk scoring system must either (a) score per-model or (b) use the worst-case model as the reference.
- The +27.8% ASR increase with reasoning mode for Qwen3-8b is a single data point — need to check if this pattern holds across models.

## Usefulness Verdict
MCPTox is the most ecologically valid MCP security benchmark because it uses 45 real-world MCP servers and 353 authentic tools rather than synthesized data. For a 1-10 risk scoring system, it provides something no other benchmark does: evidence of how attacks perform against actual production MCP infrastructure. The three attack paradigms (explicit trigger, implicit trigger with function hijacking, implicit trigger with parameter tampering) map cleanly to a "stealth" risk dimension, which is one of the hardest things to quantify.

The per-model ASR variation (34.3% to 72.8%) is both a complication and a feature — it proves that risk is not absolute but depends on the agent model being used. For Lenovo's enterprise deployment, this means the risk score for a given tool should factor in which LLM backend is in use. The reasoning mode finding (+27.8% ASR) is particularly important for practical deployment: enabling chain-of-thought reasoning, which is usually considered beneficial, can actually increase vulnerability to tool poisoning attacks. This is the kind of counterintuitive finding that justifies dynamic (not just static) risk scoring.
