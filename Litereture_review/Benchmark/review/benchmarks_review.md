# Benchmarks Review — MCP Security Literature

> Comprehensive review of **24 benchmarks** extracted from 82 papers
> across the MCP Security literature review.  
> Generated: 2026-03-29

---

## Table of Contents

1. [MCPSecBench](#1-mcpsecbench)
2. [MCPTox](#2-mcptox)
3. [MCP-SafetyBench](#3-mcp-safetybench)
4. [MCP-AttackBench](#4-mcp-attackbench)
5. [MCIP-Bench](#5-mcip-bench)
6. [ProtoAMP (Protocol Amplification Benchmark)](#6-protoamp-protocol-amplification-benchmark)
7. [AttestMCP](#7-attestmcp)
8. [MCLIB (MCP Attack Library)](#8-mclib-mcp-attack-library)
9. [MCPSafetyScanner](#9-mcpsafetyscanner)
10. [AgentDojo](#10-agentdojo)
11. [InjecAgent](#11-injecagent)
12. [R-Judge](#12-r-judge)
13. [DecodingTrust](#13-decodingtrust)
14. [TrustLLM](#14-trustllm)
15. [CVSS v3.1 / NVD](#15-cvss-v3.1--nvd)
16. [ASB (Agent Security Bench)](#16-asb-agent-security-bench)
17. [AgentHarm](#17-agentharm)
18. [HarmBench](#18-harmbench)
19. [JailbreakBench](#19-jailbreakbench)
20. [BIPIA (Benchmark for Indirect Prompt Injection Attacks)](#20-bipia-benchmark-for-indirect-prompt-injection-attacks)
21. [HELM (Holistic Evaluation of Language Models)](#21-helm-holistic-evaluation-of-language-models)
22. [BFCL-v3 (Berkeley Function Calling Leaderboard)](#22-bfcl-v3-berkeley-function-calling-leaderboard)
23. [WebArena](#23-webarena)
24. [AgentBench](#24-agentbench)

---

## 1. MCPSecBench

**Paper:** MCPSecBench: A Systematic Security Benchmark and Playground for Testing Model Context Protocols (Yang et al., 2025)

| Field | Details |
|-------|---------|
| **Link** | https://arxiv.org/abs/2508.13220 |
| **Description** | The first systematic MCP security benchmark providing taxonomy-driven test cases, GUI test harness, prompt datasets, attack scripts, and server/client implementations for reproducible evaluation across 17 attack types and 4 attack surfaces. |
| **Metrics Used** | Attack Success Rate (ASR), Refusal Rate (RR), cost per testing round ($0.41-$0.76). Evaluated per attack type per platform. |
| **Common Baselines** | Claude Desktop, OpenAI GPT-4.1, Cursor v2.3.29. Protocol-side: 100% universal ASR. Client-side: ~33% average. Server-side: ~47%. Host-side: ~27%. |
| **How to Use It** | Clone the benchmark repository. Configure MCP client/server test environments. Run attack scripts against target platforms. Use the GUI test harness for automated benchmarking. Requires access to target LLM APIs and MCP client installations. 15 trials per attack for statistical robustness. |
| **How It Can Help My Project** | The definitive benchmark for evaluating MCP security solutions. The 4-surface taxonomy (client/protocol/server/host) maps directly to the risk scoring system's evaluation dimensions. Essential for comparing the MCP risk scorer against published baselines. |

---

## 2. MCPTox

**Paper:** MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers (Wang et al., 2025)

| Field | Details |
|-------|---------|
| **Link** | https://openreview.net/forum?id=xbs5dVGUQ8 |
| **Description** | First benchmark for systematic evaluation of tool poisoning attacks on real-world MCP servers. Tests three attack paradigms (Explicit Trigger, Implicit Trigger — Function Hijacking, Implicit Trigger — Parameter Tampering) across 10 attack categories using authentic MCP server tools. |
| **Metrics Used** | Attack Success Rate (ASR), Refusal Rate (RR). Per-paradigm and per-model breakdowns. Overall 72.8% ASR measured. |
| **Common Baselines** | GPT-4o (61.8% ASR), Qwen3-32b (58.5%), Claude (34.3%). Reasoning mode impact: Qwen3-8b shows +27.8% ASR with reasoning enabled. |
| **How to Use It** | Access the benchmark dataset with 45 real-world MCP servers and 353 tools. Generate malicious test cases using the three attack templates. Run against target LLM agents. Measure ASR and RR per model. Requires API access to target LLMs and MCP server configurations. |
| **How It Can Help My Project** | Essential for testing the risk scorer's ability to detect tool poisoning — the most direct MCP attack vector. The three paradigms test different detection difficulty levels. Real-world server data ensures practical relevance of evaluation results. |

---

## 3. MCP-SafetyBench

**Paper:** MCP-SafetyBench: A Benchmark for Safety Evaluation of Large Language Models with Real-World MCP Servers (Zong et al., 2025)

| Field | Details |
|-------|---------|
| **Link** | https://arxiv.org/abs/2512.15163 |
| **Description** | Multi-domain MCP safety benchmark evaluating 13 LLMs across 5 real-world domains (Location Navigation, Repository Management, Financial Analysis, Browser Automation, Web Search) with 20 attack types in multi-turn interactions. |
| **Metrics Used** | Task Success Rate (TSR), Attack Success Rate (ASR), Defense Success Rate (DSR), safety prompt effectiveness. |
| **Common Baselines** | 13 LLMs: GPT-5, GPT-4.1, GPT-4o, o4-mini, Claude-3.7-Sonnet, Claude-4.0-Sonnet, Gemini-2.5-Pro, Gemini-2.5-Flash, Grok-4, GLM-4.5, Kimi-K2, Qwen3-235B, DeepSeek-V3.1. |
| **How to Use It** | Configure real-world MCP servers for 5 domains. Apply adversarial tool description modifications. Run multi-turn evaluation sessions with target LLMs. Measure TSR and ASR per domain-attack combination. Requires API access to all 13 models and domain-specific MCP server setups. |
| **How It Can Help My Project** | The broadest MCP safety benchmark by domain coverage. The 5-domain evaluation ensures the risk scorer generalizes across MCP use cases. Multi-turn interaction testing evaluates sustained risk assessment accuracy over extended sessions. |

---

## 4. MCP-AttackBench

**Paper:** MCP-Guard: A Multi-Stage Defense-in-Depth Framework for Securing MCP in Agentic AI (Xing et al., 2025)

| Field | Details |
|-------|---------|
| **Link** | https://arxiv.org/abs/2508.10991 |
| **Description** | Large-scale attack benchmark with hierarchical taxonomy of MCP threats organized into Semantic & Adversarial, Protocol-Specific, and Injection & Execution families. Designed for training and evaluating cascaded defense systems. |
| **Metrics Used** | F1-score (95.4% achieved), Attack Success Rate, Detection Success Rate, runtime latency (455.9ms avg, 50.9ms optimized), speedup ratio (2.04x vs standalone LLM). |
| **Common Baselines** | Standalone LLM defenses. Three-stage cascade: Stage I pattern matching (38.9% filter rate, <2ms), Stage II neural detection (96.01% F1), Stage III LLM arbitration. |
| **How to Use It** | Use the 70,448-sample dataset for training detection models. Implement the three-stage cascade pipeline. Fine-tune E5 embedding model on training corpus (5,258 samples). Evaluate with binary cross-entropy loss. Requires GPU for neural model training and LLM API access for Stage III. |
| **How It Can Help My Project** | Provides both training data and a defense architecture blueprint for the MCP risk scoring system. The cascaded approach (fast pattern → neural → LLM) directly maps to a multi-stage risk scoring pipeline. The 95.4% F1 sets the accuracy target. |

---

## 5. MCIP-Bench

**Paper:** MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol (Jing et al., 2025)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/HKUST-KnowComp/MCIP |
| **Description** | MCP contextual integrity benchmark evaluating LLMs' ability to detect 10 risk types in MCP function-calling interactions. Tests both Safety Awareness (binary safe/unsafe) and Risk Resistance (11-class identification). |
| **Metrics Used** | Safety Awareness Accuracy, Safety Awareness Macro-F1, Risk Resistance Accuracy, Risk Resistance Macro-F1, BFCL Utility (overall accuracy %). |
| **Common Baselines** | xLAM-2-70b-fc-r, xLAM-2-32b-fc-r, xLAM-2-8B-fc-r, ToolACE-2-8B, Qwen2.5-72B-Instruct, Qwen2.5-32B-Instruct, DeepSeek-R1. |
| **How to Use It** | Clone the MCIP GitHub repository. Load the 2,218-instance benchmark. Run target LLMs on both Safety Awareness and Risk Resistance tasks. Compare against published baseline results. Requires API access to evaluation models and local compute for open-source models. |
| **How It Can Help My Project** | The 10 risk types provide a granular classification scheme for MCP risk scoring. The dual evaluation (binary + 11-class) tests both coarse and fine-grained risk detection. Available on GitHub for immediate use. |

---

## 6. ProtoAMP (Protocol Amplification Benchmark)

**Paper:** Breaking the Protocol: Security Analysis of the MCP Specification and Prompt Injection Vulnerabilities (Maloyan & Namiot, 2026)

| Field | Details |
|-------|---------|
| **Link** | https://arxiv.org/abs/2601.17549 |
| **Description** | Benchmark quantifying how MCP architecture amplifies prompt injection attack success rates compared to non-MCP baselines. Tests attacks at three protocol layers (resource content, tool response payloads, sampling request prompts) with the proposed AttestMCP defense. |
| **Metrics Used** | Attack Success Rate (ASR), amplification factor (% increase vs baseline), defense reduction (ASR before/after AttestMCP), latency overhead (8.3ms cold, 2.4ms warm). |
| **Common Baselines** | Non-MCP baseline ASR. Three MCP server implementations: filesystem, git, sqlite. Four LLM backends: Claude-3.5-Sonnet, GPT-4o, Llama-3.1-70B. AttestMCP defense reduces ASR from 52.8% to 12.4% (76.5% reduction). |
| **How to Use It** | Set up 3 MCP server implementations. Configure 4 LLM backends. Run 847 test scenarios measuring ASR at each protocol layer. Compare MCP vs non-MCP baselines. Implement AttestMCP extension for defense evaluation. Requires MCP server infrastructure and LLM API access. |
| **How It Can Help My Project** | Quantifies the MCP-specific risk amplification that the risk scorer must account for. The +23-41% amplification factor demonstrates that protocol context should increase risk scores. AttestMCP's 76.5% ASR reduction shows the value of protocol-level defenses. |

---

## 7. AttestMCP

**Paper:** Breaking the Protocol: Security Analysis of the MCP Specification and Prompt Injection Vulnerabilities (Maloyan & Namiot, 2026)

| Field | Details |
|-------|---------|
| **Link** | https://arxiv.org/abs/2601.17549 |
| **Description** | Backward-compatible attestation extension for MCP providing 5 security enhancements: Capability Attestation (cryptographic proof), Message Authentication (HMAC-SHA256), Origin Tagging (server identification), Isolation Enforcement (cross-server data flow restrictions), and Replay Protection (nonce-based time windows). |
| **Metrics Used** | ASR reduction (52.8% → 12.4%, 76.5% reduction), performance overhead (8.3ms cold start, 2.4ms warm cache per message). |
| **Common Baselines** | Unprotected MCP protocol baseline. Compared against: indirect injection (47.8% → reduced), cross-server propagation (61.3% → reduced), sampling vulnerability (67.2% → reduced). |
| **How to Use It** | Implement the 5 AttestMCP extensions on MCP servers. Add HMAC-SHA256 message signing. Configure nonce-based replay protection. Deploy origin tags on all server responses. Requires cryptographic key management infrastructure and protocol-level modifications. |
| **How It Can Help My Project** | AttestMCP's 5 security features inform what the risk scorer should verify: capability attestation, message integrity, origin tracking, isolation, and replay protection. Each missing feature could increase risk scores. |

---

## 8. MCLIB (MCP Attack Library)

**Paper:** Referenced by When MCP Servers Attack (Zhao et al., 2025); Guo et al., 2025

| Field | Details |
|-------|---------|
| **Link** | https://arxiv.org/abs/2508.12538 |
| **Description** | Unified plugin-based framework for simulating and evaluating MCP attacks. Catalogs 31 attacks across four families: direct tool injection, indirect tool injection, malicious-user attacks, and LLM-inherent attacks. |
| **Metrics Used** | Attack success rates per family and per attack type. Plugin-based evaluation metrics. |
| **Common Baselines** | 31 attacks across 4 families provide comprehensive coverage of the MCP threat landscape. |
| **How to Use It** | Install the MCLIB framework. Configure attack plugins for target MCP environments. Run systematic evaluation across all 4 attack families. Requires MCP server/client setup and LLM access. |
| **How It Can Help My Project** | The 31-attack catalog across 4 families provides the most comprehensive threat enumeration for the risk scoring taxonomy. The plugin architecture enables systematic testing of risk scorer coverage against all known attack types. |

---

## 9. MCPSafetyScanner

**Paper:** MCP Safety Audit: LLMs with the MCP Allow Major Security Exploits (Radosevich & Halloran, 2025)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/johnhalloran321/mcpSafetyScanner |
| **Description** | First automated MCP security auditing tool. Scans MCP deployments for vulnerability patterns and executes proof-of-concept exploits including credential theft, malicious code execution, and retrieval-agent deception attacks. |
| **Metrics Used** | Qualitative exploit validation (credential theft success, code execution success). Tested on Claude 3.7 and Llama-3.3-70B-Instruct. |
| **Common Baselines** | Tested against standard MCP servers: filesystem, Slack, Everything, Chroma. Attack types: MCE, RAC, CT, RADE. |
| **How to Use It** | Install MCPSafetyScanner from GitHub. Point it at target MCP server deployments. Run automated vulnerability scanning. Review exploit reports. Requires Node.js and access to target MCP servers. |
| **How It Can Help My Project** | A ready-made validation tool for the risk scoring system — run MCPSafetyScanner against test deployments and verify the risk scorer flags the same vulnerabilities. The documented attack types define critical severity categories. |

---

## 10. AgentDojo

**Paper:** AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents (Debenedetti et al., 2024)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/ethz-spylab/agentdojo |
| **Description** | The most widely adopted dynamic evaluation environment for prompt injection attacks and defenses in tool-using LLM agents. Provides 4 realistic task suites with parameterized attacks, defense baselines, and reproducible benchmarking. Used by Progent, LlamaFirewall, TraceAegis, ToolSafe, and The Task Shield. |
| **Metrics Used** | Utility (task completion %), Utility under attack, Attack Success Rate (ASR), AUC, Recall@1%FPR, TPR, FPR, Balanced Accuracy, F1. |
| **Common Baselines** | Multiple defenses compared: repeat_user_prompt, spotlighting_with_delimiting, tool_filter, transformers_pi_detector, DataSentinel, Llama Prompt Guard 2. Progent achieved ASR reduction from 41.2% to 2.2%. |
| **How to Use It** | pip install agentdojo. Implement agent within the framework. Run against 4 task suites (Workspace, Travel, Banking, Slack) with 97 user tasks and 629 injection tasks. Compare utility vs ASR tradeoff. Requires Python 3.10+ and LLM API access. |
| **How It Can Help My Project** | The standard benchmark for agent security evaluation — must be included for credibility. The 4-domain coverage tests generalization. The extensive defense baseline comparisons enable positioning the MCP risk scorer against state-of-the-art. |

---

## 11. InjecAgent

**Paper:** InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated LLM Agents (Zhan et al., 2024)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/uiuc-kang-lab/InjecAgent |
| **Description** | First indirect injection benchmark specifically for tool-integrated agents. Evaluates private-data exfiltration risk with explicit user-tool vs attacker-tool distinction across direct harm and data stealing categories. |
| **Metrics Used** | Attack Success Rate (ASR) across tools, agents, harm categories, and exfiltration scenarios. |
| **Common Baselines** | Multiple agent configurations evaluated. Used as evaluation benchmark by MindGuard (attack payload adaptation), Adaptive Attacks (100-case subset), and referenced by TraceAegis. |
| **How to Use It** | Clone the InjecAgent repository. Configure 17 user tools and 62 attacker tools. Run 1,054 test cases against target agents. Measure ASR per harm category. Requires Python and LLM API access. |
| **How It Can Help My Project** | The explicit exfiltration category is directly relevant to MCP data leakage risk assessment. The user-tool vs attacker-tool framework maps to the risk scorer's need to evaluate tool trustworthiness. |

---

## 12. R-Judge

**Paper:** R-Judge: Benchmarking Safety Risk Awareness for LLM Agents (Yuan et al., 2024)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/Lordog/R-Judge |
| **Description** | Benchmark for evaluating risk awareness in LLM agent behaviors. Contains 569 curated multi-turn interaction records across 27 risk scenarios and 10 risk types sourced from WebArena, ToolEmu, InterCode-Bash/SQL, and MINT environments. |
| **Metrics Used** | Safety judgment accuracy (binary safe/unsafe classification). Best: GPT-4o at 74.42%, most models near random. |
| **Common Baselines** | 11 LLMs evaluated with both prompting and fine-tuning approaches. Fine-tuning on safety judgment significantly improves performance. |
| **How to Use It** | Clone the R-Judge repository. Load the 569 interaction records. Evaluate target LLMs on safety judgment task. Compare against published baselines. Fine-tuning variant requires labeled training data and GPU resources. |
| **How It Can Help My Project** | The 10 risk types and 27 scenarios provide a template for MCP-specific risk categories. The finding that most models perform near random on risk judgment highlights the challenge the MCP risk scorer must overcome. |

---

## 13. DecodingTrust

**Paper:** DecodingTrust: A Comprehensive Assessment of Trustworthiness in GPT Models (Wang et al., 2023)

| Field | Details |
|-------|---------|
| **Link** | https://huggingface.co/datasets/AI-Secure/DecodingTrust |
| **Description** | Eight-dimensional trustworthiness benchmark (NeurIPS 2023 Outstanding Paper) evaluating toxicity, stereotype bias, adversarial robustness, OOD robustness, adversarial demonstrations, privacy, machine ethics, and fairness. |
| **Metrics Used** | Dimension-specific metrics across 8 trustworthiness dimensions. Uses sub-benchmarks: RealToxicityPrompts, BBQ, AdvGLUE, MMLU, ETHICS, and more. |
| **Common Baselines** | GPT-4, GPT-3.5. Key finding: GPT-4 more vulnerable to jailbreaking than GPT-3.5 despite better baselines. |
| **How to Use It** | Access dataset from HuggingFace (AI-Secure/DecodingTrust). Run evaluations using the 8-dimension framework. Each dimension has specific evaluation protocols and metrics. Requires LLM API access and the DecodingTrust evaluation codebase. |
| **How It Can Help My Project** | The 8-dimension framework provides a scoring rubric adaptable for MCP agent trustworthiness evaluation. Finding that capability ≠ trustworthiness is critical for MCP risk assessment design. |

---

## 14. TrustLLM

**Paper:** TrustLLM: Trustworthiness in Large Language Models (Huang et al., 2024)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/HowieHwong/TrustLLM |
| **Description** | Largest-scale LLM trustworthiness benchmark (ICML 2024) evaluating 16 LLMs across 6 dimensions (truthfulness, safety, fairness, robustness, privacy, machine ethics) using 30+ datasets and 18 subcategories. |
| **Metrics Used** | Dimension-specific scores across 6 dimensions, 18 subcategories. Uses 30+ public datasets for evaluation. |
| **Common Baselines** | 16 mainstream LLMs. Finding: proprietary LLMs generally more trustworthy; some over-optimize safety at cost of utility. |
| **How to Use It** | Clone the TrustLLM GitHub repository. Set up evaluation environment. Run target LLMs against 30+ datasets across 6 dimensions. Compare against 16-model baseline. Requires significant compute and API access for full evaluation. |
| **How It Can Help My Project** | The 6 trustworthiness dimensions can be adapted as risk scoring dimensions for MCP agents. The safety-utility tradeoff finding directly informs risk threshold calibration. |

---

## 15. CVSS v3.1 / NVD

**Paper:** From Description to Score: Can LLMs Quantify Vulnerabilities? (Jafarikhah et al., 2026)

| Field | Details |
|-------|---------|
| **Link** | https://nvd.nist.gov/ |
| **Description** | The Common Vulnerability Scoring System (CVSS v3.1) with the National Vulnerability Database (NVD), used to evaluate whether LLMs can automatically score vulnerabilities from textual descriptions. Tests automated severity quantification across 31,000+ CVE entries. |
| **Metrics Used** | Accuracy, Precision, Recall, F1, MAE across 8 CVSS base metrics. Severity scale: None/Low/Medium/High/Critical. |
| **Common Baselines** | 6 LLMs: GPT-4o, GPT-5, Llama-3.3-70B, Gemini-2.5-Flash, DeepSeek-R1, Grok-3. GPT-5 highest precision. Two-shot prompting optimal. |
| **How to Use It** | Access NVD data via API (https://nvd.nist.gov/). Extract CVE descriptions and CVSS scores. Implement LLM-based scoring with zero-shot to ten-shot prompting. Train meta-classifier combining LLM outputs. Requires LLM API access. |
| **How It Can Help My Project** | CVSS scoring methodology is directly transferable to MCP risk scoring. The text-to-severity-score approach mirrors how MCP Security could score tool descriptions. The meta-classifier ensemble approach applies to combining multiple risk signals. |

---

## 16. ASB (Agent Security Bench)

**Paper:** Agent Security Bench (Zhang et al., 2025)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/agiresearch/ASB |
| **Description** | Benchmark for formalizing attacks and defenses in LLM-based agents with 6 attack prompt types. Used by both Progent and ToolSafe for standardized evaluation. |
| **Metrics Used** | Utility (%), Attack Success Rate (ASR %) per attack type. |
| **Common Baselines** | 6 attack types: combined_attack, context_ignoring, escape_characters, fake_completion, naive, average. Defense baselines: delimiters, sandwich, instructional prevention. |
| **How to Use It** | Clone the ASB repository. Configure agent environments. Run all 6 attack types against target defenses. Measure utility-ASR tradeoff. Requires Python and LLM API access. |
| **How It Can Help My Project** | The 6 attack types provide input-level risk classification categories for the MCP risk scorer. Standardized evaluation enables comparison with Progent and ToolSafe results. |

---

## 17. AgentHarm

**Paper:** AgentHarm: Harmful Agent Behavior Benchmark (Gray Swan / UK AISI, 2025)

| Field | Details |
|-------|---------|
| **Link** | https://huggingface.co/datasets/ai-safety-institute/AgentHarm |
| **Description** | Benchmark for evaluating harmful agent behaviors including deepfakes, misinformation generation, and other dangerous capabilities. Published by UK AI Safety Institute and Gray Swan. |
| **Metrics Used** | Attack Success Rate (ASR), Safety Rate, Helpfulness. |
| **Common Baselines** | Multiple LLM agents evaluated on harmful behavior compliance rates. |
| **How to Use It** | Access dataset from HuggingFace (ai-safety-institute/AgentHarm). Evaluate target agents on harmful behavior requests. Measure compliance rates. Requires LLM API access. |
| **How It Can Help My Project** | Defines the highest severity tier for risk scoring — requests that should always be denied. Essential for calibrating the 'critical risk' threshold of the MCP risk scorer. |

---

## 18. HarmBench

**Paper:** Referenced by TRiSM for Agentic AI (Raza et al., 2025) and multiple survey papers

| Field | Details |
|-------|---------|
| **Link** | https://github.com/centerforaisafety/HarmBench |
| **Description** | Standardized benchmark for prompt injection and jailbreak evaluation from the Center for AI Safety. Widely referenced across MCP security literature for measuring attack robustness. |
| **Metrics Used** | Attack Success Rate (ASR), Robustness scores. |
| **Common Baselines** | Multiple jailbreak techniques and defense mechanisms evaluated. |
| **How to Use It** | Clone from GitHub. Run jailbreak attacks against target models. Measure ASR and robustness. Requires Python and LLM API access. |
| **How It Can Help My Project** | Standard jailbreak evaluation relevant to MCP scenarios where agents attempt to bypass tool restrictions through prompt manipulation. |

---

## 19. JailbreakBench

**Paper:** Referenced by TRiSM for Agentic AI (Raza et al., 2025)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/JailbreakBench/jailbreakbench |
| **Description** | Benchmark focused specifically on jailbreak scenarios for LLMs. Referenced alongside HarmBench for comprehensive jailbreak evaluation. |
| **Metrics Used** | Attack Success Rate (ASR), Robustness under jailbreak scenarios. |
| **Common Baselines** | Multiple jailbreak techniques cataloged and evaluated. |
| **How to Use It** | Clone from GitHub. Configure jailbreak evaluation. Run against target LLMs. Requires Python and LLM API access. |
| **How It Can Help My Project** | Complements HarmBench for jailbreak-specific evaluation. Relevant to testing whether the MCP risk scorer can detect jailbreak attempts targeting tool access permissions. |

---

## 20. BIPIA (Benchmark for Indirect Prompt Injection Attacks)

**Paper:** Referenced by Beyond the Protocol (Song et al., 2025) and multiple papers

| Field | Details |
|-------|---------|
| **Link** | https://github.com/microsoft/BIPIA |
| **Description** | The first indirect prompt injection attack benchmark, developed by Microsoft. Referenced across MCP security literature as a foundational PI evaluation framework. |
| **Metrics Used** | Attack success rates for indirect prompt injection. Detection accuracy. |
| **Common Baselines** | Multiple LLM models and defense mechanisms evaluated. |
| **How to Use It** | Clone from GitHub (Microsoft). Run indirect PI attacks against target systems. Measure detection rates. Requires Python and LLM access. |
| **How It Can Help My Project** | Foundational PI benchmark applicable to MCP scenarios where external content injections reach the agent through tool responses. Tests the risk scorer's ability to detect indirect attacks. |

---

## 21. HELM (Holistic Evaluation of Language Models)

**Paper:** Referenced by TRiSM for Agentic AI (Raza et al., 2025)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/stanford-crfm/helm |
| **Description** | Comprehensive LLM evaluation framework from Stanford CRFM covering robustness, fairness, and bias. Referenced in MCP security literature as a comprehensive model evaluation standard. |
| **Metrics Used** | Comprehensive metrics across multiple dimensions: robustness, fairness, bias, accuracy. |
| **Common Baselines** | Multiple mainstream LLMs evaluated across all dimensions. |
| **How to Use It** | Install HELM framework. Configure evaluation scenarios. Run comprehensive model evaluation. Requires significant compute resources. |
| **How It Can Help My Project** | Provides the broadest LLM evaluation methodology that can inform how to holistically assess MCP agent capabilities and risks across multiple dimensions. |

---

## 22. BFCL-v3 (Berkeley Function Calling Leaderboard)

**Paper:** Used by MCIP (Jing et al., 2025) for utility evaluation

| Field | Details |
|-------|---------|
| **Link** | https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard |
| **Description** | The standard benchmark for evaluating LLM function calling capabilities. Used to measure whether security-focused MCP designs degrade practical function calling utility. |
| **Metrics Used** | Overall function calling accuracy (%). Measures correct tool selection, parameter extraction, and execution. |
| **Common Baselines** | Broad LLM comparison available on the public leaderboard (gorilla.cs.berkeley.edu). |
| **How to Use It** | Access via GitHub or HuggingFace. Run target LLMs on function calling tasks. Compare against leaderboard. Requires LLM API access. |
| **How It Can Help My Project** | Essential for measuring the utility cost of MCP risk scoring. A risk scorer that significantly degrades function calling accuracy is impractical. BFCL-v3 provides the accepted measurement standard. |

---

## 23. WebArena

**Paper:** Referenced by R-Judge (Yuan et al., 2024) and TRiSM (Raza et al., 2025)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/web-arena-x/webarena |
| **Description** | Web navigation benchmark used as a source environment for R-Judge safety evaluation scenarios. Tests agent interactions in realistic web environments with potential security implications. |
| **Metrics Used** | Task success rate, safety compliance in web navigation tasks. |
| **Common Baselines** | Multiple LLM-based web agents evaluated. |
| **How to Use It** | Set up WebArena environment with web applications. Deploy agent in navigation tasks. Evaluate task success and safety. Requires Docker and compute resources. |
| **How It Can Help My Project** | Web navigation is a common MCP tool category. WebArena scenarios test whether the risk scorer correctly assesses web-interaction risks including content injection and data exposure. |

---

## 24. AgentBench

**Paper:** Referenced by TRiSM (Raza et al., 2025) and SentinelAgent (He et al., 2025)

| Field | Details |
|-------|---------|
| **Link** | https://github.com/THUDM/AgentBench |
| **Description** | Multi-task agent benchmark for evaluating LLM agents across diverse environments. Referenced in MCP security literature for comprehensive agent capability assessment. |
| **Metrics Used** | Task success rate, compliance metrics, multi-step attack resilience. |
| **Common Baselines** | Multiple LLM agents across diverse task categories. |
| **How to Use It** | Clone from GitHub. Set up multi-task evaluation environments. Run agent evaluations. Requires Python and LLM API access. |
| **How It Can Help My Project** | Provides multi-task evaluation methodology applicable to testing the MCP risk scorer across diverse tool-use scenarios. Multi-step evaluation tests sustained risk assessment accuracy. |

---
