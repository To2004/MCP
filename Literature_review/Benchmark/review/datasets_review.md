# Datasets Review — MCP Security Literature

> Comprehensive review of **50 datasets** extracted from 82 papers
> across the MCP Security literature review.  
> Generated: 2026-03-29

---

## Table of Contents

1. [MCP-AttackBench](#1-mcp-attackbench)
2. [MCPTox Dataset](#2-mcptox-dataset)
3. [MCPSecBench Playground](#3-mcpsecbench-playground)
4. [MCP-SafetyBench Dataset](#4-mcp-safetybench-dataset)
5. [MCIP-Bench](#5-mcip-bench)
6. [MCIP Guardian Training Dataset](#6-mcip-guardian-training-dataset)
7. [ProtoAMP Attack Data](#7-protoamp-attack-data)
8. [MCP Server Dataset (67,057 servers)](#8-mcp-server-dataset-67057-servers)
9. [MCP Server Database (1,360 servers / 12,230 tools)](#9-mcp-server-database-1360-servers--12230-tools)
10. [MCP Server Registry Dataset (1,899 repos)](#10-mcp-server-registry-dataset-1899-repos)
11. [MCP Server Empirical Dataset (1,899 repos)](#11-mcp-server-empirical-dataset-1899-repos)
12. [MCP API Usage Dataset (2,117 repos)](#12-mcp-api-usage-dataset-2117-repos)
13. [MCP Ecosystem Dataset (8,401 projects)](#13-mcp-ecosystem-dataset-8401-projects)
14. [Top-296 MCP Server Dataset](#14-top-296-mcp-server-dataset)
15. [Malicious MCP Server Dataset (Song et al.)](#15-malicious-mcp-server-dataset-song-et-al.)
16. [Damn Vulnerable MCP Server](#16-damn-vulnerable-mcp-server)
17. [Component-based Attack PoC Dataset (132 servers)](#17-component-based-attack-poc-dataset-132-servers)
18. [MCP Attack Benchmark (Beyond the Protocol)](#18-mcp-attack-benchmark-beyond-the-protocol)
19. [MCPShield Evaluation Suite (6 test suites)](#19-mcpshield-evaluation-suite-6-test-suites)
20. [MCP-ITP Implicit Poisoning Data](#20-mcp-itp-implicit-poisoning-data)
21. [Log-To-Leak Attack Scenarios](#21-log-to-leak-attack-scenarios)
22. [MCPSafetyScanner Test Scenarios](#22-mcpsafetyscanner-test-scenarios)
23. [InjecAgent Dataset](#23-injecagent-dataset)
24. [AgentDojo Task Suites](#24-agentdojo-task-suites)
25. [R-Judge Records](#25-r-judge-records)
26. [ASB (Agent Safety Benchmark)](#26-asb-agent-safety-benchmark)
27. [AgentHarm Dataset](#27-agentharm-dataset)
28. [RAS-Eval](#28-ras-eval)
29. [EICU-AC (Healthcare Access Control)](#29-eicu-ac-healthcare-access-control)
30. [Mind2Web-SC (Web Navigation Safety Control)](#30-mind2web-sc-web-navigation-safety-control)
31. [MiniScope Synthetic Permission Dataset](#31-miniscope-synthetic-permission-dataset)
32. [Trust Paradox Evaluation Scenarios (19 scenarios)](#32-trust-paradox-evaluation-scenarios-19-scenarios)
33. [Indirect PI Attack Dataset (1,068 instances)](#33-indirect-pi-attack-dataset-1068-instances)
34. [Synthetic PI Dataset (500 prompts)](#34-synthetic-pi-dataset-500-prompts)
35. [ShareGPT Conversation Dataset](#35-sharegpt-conversation-dataset)
36. [WildChat Dataset (1M interactions)](#36-wildchat-dataset-1m-interactions)
37. [DecodingTrust Dataset](#37-decodingtrust-dataset)
38. [TrustLLM Benchmark Datasets (30+)](#38-trustllm-benchmark-datasets-30+)
39. [NVD/CVE Database (31,000+ entries)](#39-nvdcve-database-31000+-entries)
40. [glaive-function-calling-v2](#40-glaive-function-calling-v2)
41. [ToolACE Dataset](#41-toolace-dataset)
42. [ToolBench Dataset](#42-toolbench-dataset)
43. [MetaTool Benchmark Dataset](#43-metatool-benchmark-dataset)
44. [Meta Tool-Use Agentic PI Benchmark (600 scenarios)](#44-meta-tool-use-agentic-pi-benchmark-600-scenarios)
45. [CyberSecEval3](#45-cyberseceval3)
46. [Anthropic Red-Teaming Dataset](#46-anthropic-red-teaming-dataset)
47. [CIAQA (Compositional Instruction Attack QA)](#47-ciaqa-compositional-instruction-attack-qa)
48. [CrAIBench (Web3 AI Agent Benchmark)](#48-craibench-web3-ai-agent-benchmark)
49. [AlpacaFarm Dataset (208 samples)](#49-alpacafarm-dataset-208-samples)
50. [BFCL-v3 (Berkeley Function Calling Leaderboard)](#50-bfcl-v3-berkeley-function-calling-leaderboard)

---

## 1. MCP-AttackBench

**Paper:** MCP-Guard: A Multi-Stage Defense-in-Depth Framework for Securing Model Context Protocol in Agentic AI (Xing et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2508.10991 |
| **Description** | A large-scale synthetic security dataset covering unique threat vectors for MCP environments. It uses a hierarchical taxonomy organized into three families: Semantic & Adversarial attacks, Protocol-Specific attacks, and Injection & Execution attacks. Designed to train and evaluate cascaded defense pipelines for MCP security. |
| **Structure Details** | 70,448 samples total. Training corpus of 5,258 samples (2,153 adversarial, 3,105 benign) used for fine-tuning E5 embedding model. Covers three attack families with hierarchical sub-categories. Format: structured text samples with attack/benign labels. |
| **How the Paper Used It** | Used as the primary training and evaluation dataset for the MCP-Guard three-stage cascaded defense pipeline. The training corpus fine-tuned the Multilingual-E5-large embedding model (Stage II neural detection), achieving 96.01% F1 score with a 95.06% improvement over baseline. |
| **How It Can Help My Project** | Directly applicable for training the risk_scorer module of an MCP security system. The hierarchical attack taxonomy can inform severity tier definitions. The 70K+ labeled samples provide substantial training data for ML-based risk classification of MCP tool invocations. |

---

## 2. MCPTox Dataset

**Paper:** MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers (Wang et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://openreview.net/forum?id=xbs5dVGUQ8 |
| **Description** | The first benchmark built from real-world MCP servers for evaluating tool poisoning attacks. Contains malicious test cases across three attack paradigms: Explicit Trigger Function Hijacking, Implicit Trigger Function Hijacking, and Implicit Trigger Parameter Tampering. Covers 10 attack categories including shadowing, puppet, and spoofing attacks. |
| **Structure Details** | 45 live real-world MCP servers, 353 authentic tools, 1,312-1,497 malicious test cases. Breakdown: Explicit Trigger—Function Hijacking (224 cases), Implicit Trigger—Function Hijacking (548 cases), Implicit Trigger—Parameter Tampering (725 cases). Format: structured test cases with user queries + poisoned tool descriptions. |
| **How the Paper Used It** | Primary evaluation benchmark for measuring tool poisoning attack success rates across multiple LLM agents (GPT-4o, Qwen3-32b, Claude, etc.). Found overall 72.8% attack success rate with significant model vulnerability variation. |
| **How It Can Help My Project** | Essential for evaluating an MCP risk scoring system's ability to detect tool poisoning attacks. The three attack paradigms map to different severity tiers. Real-world server data ensures the risk scorer is tested against realistic threats rather than synthetic patterns only. |

---

## 3. MCPSecBench Playground

**Paper:** MCPSecBench: A Systematic Security Benchmark and Playground for Testing Model Context Protocols (Yang et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2508.13220 |
| **Description** | A comprehensive MCP security testing framework providing taxonomy-driven test cases, a GUI test harness, prompt datasets, attack scripts, and server/client implementations. Covers 17 distinct attack types across 4 attack surfaces: client-side, protocol-side, server-side, and host-side. |
| **Structure Details** | 17 attack types across 4 attack surfaces. Prompt dataset with LLM-based prompt variation. Multi-layer evaluation covering Claude Desktop, OpenAI GPT-4.1, and Cursor v2.3.29. 15 trials per attack for statistical robustness. Cost: $0.41-$0.76 per testing round. |
| **How the Paper Used It** | Used as both a benchmark and playground for evaluating MCP security across multiple platforms and providers. Found 100% ASR on protocol-side attacks (universal), ~33% on client-side, ~47% on server-side, and ~27% on host-side. |
| **How It Can Help My Project** | The 4-surface attack taxonomy directly maps to the risk scoring system's evaluation dimensions. The playground environment enables reproducible testing of risk classification accuracy. Protocol-side attacks (100% ASR) highlight critical areas where the risk scorer must flag maximum severity. |

---

## 4. MCP-SafetyBench Dataset

**Paper:** MCP-SafetyBench: A Benchmark for Safety Evaluation of Large Language Models with Real-World MCP Servers (Zong et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2512.15163 |
| **Description** | A benchmark evaluating LLM safety across five real-world MCP domains with 20 attack types using multi-turn interaction evaluation. Covers both stealth and disruption attacks across server-side, host-side, and user-side categories using real-world MCP servers with adversarially modified tool descriptions. |
| **Structure Details** | 5 domains (Location Navigation, Repository Management, Financial Analysis, Browser Automation, Web Search). 20 attack types. Evaluated on 13 LLMs (9 proprietary including GPT-5, Claude-4.0-Sonnet, Grok-4; 4 open-source). Multi-turn interaction format. |
| **How the Paper Used It** | Primary benchmark evaluating 13 LLMs on safety compliance across all domain-attack combinations. Measured Task Success Rate (TSR), Attack Success Rate (ASR), and safety prompt effectiveness. |
| **How It Can Help My Project** | The 5-domain coverage ensures the risk scoring system generalizes across MCP use cases. The 20 attack types provide a comprehensive threat catalog for severity classification. Multi-turn evaluation tests whether risk scoring remains accurate across extended agent sessions. |

---

## 5. MCIP-Bench

**Paper:** MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol (Jing et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/HKUST-KnowComp/MCIP |
| **Description** | A benchmark suite for evaluating LLMs' safety capabilities in MCP interactions. Covers 11 categories: 10 risk types (Identity Injection, Function Overlapping, Function Injection, Data Injection, Excessive Privileges Overlapping, Function Dependency Injection, Replay Injection, Wrong Parameter Intent Injection, Ignore Purpose Intent Injection, Causal Dependency Injection) plus 1 safe/gold class. |
| **Structure Details** | 2,218 synthesized instances total (1,192 from Glaive AI + 1,026 from ToolACE). Each instance averages ~6 dialogue turns. 11 categories. Format: multi-turn function-calling dialogues with safety labels. |
| **How the Paper Used It** | Used to evaluate MCIP Guardian and baseline models (xLAM, ToolACE, Qwen2.5, DeepSeek-R1) on Safety Awareness (binary classification) and Risk Resistance (11-class identification). Measured by Accuracy and Macro-F1. |
| **How It Can Help My Project** | The 10 risk types provide a ready-made taxonomy for the risk scoring system's severity classification. The structured dialogue format tests multi-turn risk assessment. Can directly evaluate whether the MCP risk scorer correctly identifies each of the 10 risk categories. |

---

## 6. MCIP Guardian Training Dataset

**Paper:** MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol (Jing et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/HKUST-KnowComp/MCIP |
| **Description** | A training dataset in Model Contextual Integrity (MCI) format for training safety-aware MCP models. Covers all 11 MCIP categories with structured information transmission steps. |
| **Structure Details** | 13,830 instances across 11 categories. Distribution: True (1,791), Identity Injection (1,749), Function Overlapping (1,395), Function Injection (1,382), Data Injection (1,361), Excessive Privileges (1,401), Function Dependency Injection (1,372), Replay Injection (1,371), Wrong Parameter (664), Ignore Purpose (718), Causal Dependency (626). ~8 transmission steps per instance. |
| **How the Paper Used It** | Used to fine-tune Salesforce/Llama-xLAM-2-8b-fc-r as the MCIP Guardian safety model. The fine-tuned model significantly outperformed baseline LLMs on safety awareness tasks. |
| **How It Can Help My Project** | Directly usable for training the risk_scorer module to classify MCP interactions into 10 risk categories. The imbalanced class distribution reflects real-world threat frequency patterns. The MCI format (information transmission steps) aligns with how MCP tool invocations flow through the protocol. |

---

## 7. ProtoAMP Attack Data

**Paper:** Breaking the Protocol: Security Analysis of the MCP Specification and Prompt Injection Vulnerabilities (Maloyan & Namiot, 2026)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2601.17549 |
| **Description** | Protocol Amplification benchmark dataset containing controlled test scenarios measuring how MCP architecture amplifies prompt injection attack success rates compared to non-MCP baselines. Attacks injected at three protocol layers: resource content, tool response payloads, and sampling request prompts. |
| **Structure Details** | 847 controlled test scenarios. Tested on 3 MCP server implementations (filesystem, git, sqlite) and 4 LLM backends (Claude-3.5-Sonnet, GPT-4o, Llama-3.1-70B). Three injection layers measured independently. |
| **How the Paper Used It** | Quantified that MCP architecture amplifies attack success by +23-41% versus non-MCP baselines. Indirect injection: 47.8% ASR vs 31.2% baseline (+16.6%). Cross-server propagation: 61.3% vs 19.7% (+41.6%). Sampling vulnerability: 67.2% ASR. |
| **How It Can Help My Project** | Demonstrates that MCP-specific protocol features create amplified risk — critical evidence for the risk scorer to assign higher severity to protocol-level attack vectors. The three injection layers map to distinct risk dimensions the scoring system must evaluate. |

---

## 8. MCP Server Dataset (67,057 servers)

**Paper:** Toward Understanding Security Issues in the Model Context Protocol Ecosystem (Li & Gao, 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2510.16558 |
| **Description** | Large-scale dataset of MCP servers collected across 6 registries for ecosystem-wide security analysis. Covers server metadata, tool definitions, and security posture indicators including invalid links, empty content, missing documentation, and credential leakage. |
| **Structure Details** | 67,057 servers across 6 registries: mcp.so (15,000+), MCP Market (10,000+), MCP Store (5,000+), Pulse MCP (7,000+), Smithery (7,682), npm (52,102). 44,499 Python-based tools extracted via AST analysis. 52.1% Python, 22.5% JavaScript, 11.6% TypeScript. |
| **How the Paper Used It** | Used for ecosystem-wide trust analysis identifying: tool confusion attacks (20-100% success), tool shadowing (40-100% success), credential leakage (9 PATs, 3 API keys), server hijacking (111+ instances), and affix-squatting (408 groups). |
| **How It Can Help My Project** | Provides the scale data needed to understand MCP ecosystem risk distribution. The vulnerability prevalence statistics (e.g., 6.75% invalid links, credential leakage rates) can calibrate the risk scorer's base rates. The 44K+ tool database enables training a tool-level risk classifier. |

---

## 9. MCP Server Database (1,360 servers / 12,230 tools)

**Paper:** Mind Your Server: A Systematic Study of Parasitic Toolchain Attacks on the MCP Ecosystem (Zhao et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2509.06572 |
| **Description** | Database of MCP servers and tools analyzed for parasitic toolchain attack (MCP-UPD) vulnerability. Categorizes tools into External Ingestion Tools (EIT), Privacy Access Tools (PAT), and Network Access Tools (NAT) based on their exploit-enabling capabilities. |
| **Structure Details** | 1,360 servers from 3 sources: Pulse MCP (784), MCP Market (310), Awesome MCP Servers (266). 12,230 tools total. Risk categories: EIT (472 tools, 128 servers), PAT (391 tools, 155 servers), NAT (180 tools, 89 servers). 1,062 tools (8.7%) identified with exploit risk. |
| **How the Paper Used It** | Used for ecosystem census revealing 27.2% of servers expose exploitable tool combinations. Demonstrated 90% success rate in constructing real-world parasitic toolchain attacks across 10 toolchains. |
| **How It Can Help My Project** | The EIT/PAT/NAT risk taxonomy provides a tool-level classification scheme for the risk scorer. The finding that 8.7% of tools carry exploit risk gives a baseline detection target. Parasitic toolchain patterns inform multi-tool risk aggregation logic. |

---

## 10. MCP Server Registry Dataset (1,899 repos)

**Paper:** Model Context Protocol (MCP): Landscape, Security Threats, and Future Research Directions (Hou et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2503.23278 |
| **Description** | Collection of open-source MCP server repositories from 6 registries used to map the MCP ecosystem landscape, server lifecycle, and security posture. Provides the first comprehensive census of the MCP server ecosystem. |
| **Structure Details** | 1,899 repositories from: official GitHub repo, Glama, PulseMCP, Smithery, MCP.so, OpenSumi. Includes server metadata, tool schemas, transport configurations, and lifecycle states. |
| **How the Paper Used It** | Used for the first comprehensive MCP landscape analysis, mapping protocol architecture, threat surfaces, and research gaps. Identified key security threats across protocol layers. |
| **How It Can Help My Project** | Provides ecosystem context for the risk scoring system — understanding server population distribution, common tool patterns, and typical configurations helps calibrate risk baselines and identify outlier behaviors worth flagging. |

---

## 11. MCP Server Empirical Dataset (1,899 repos)

**Paper:** Model Context Protocol (MCP) at First Glance: Studying the Security and Maintainability of MCP Servers (Hasan et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/SAILResearch/replication-25-mcp-server-empirical-study |
| **Description** | Large-scale empirical study dataset of open-source MCP servers examining security vulnerabilities, code quality, and maintainability. Analyzed using SonarQube for vulnerability detection and CHAOSS metrics for ecosystem health. |
| **Structure Details** | 1,899 repositories from official, community, and mined (GitHub SDK import search) sources. Analyzed with SonarQube (vulnerability/code smell/bug detection), mcp-scan (tool poisoning), and 14 CHAOSS OSS health metrics. |
| **How the Paper Used It** | First large-scale empirical study identifying common vulnerability patterns across MCP server implementations, dependency auditing results, and ecosystem quality metrics for nearly 1,900 servers. |
| **How It Can Help My Project** | The vulnerability pattern data from 1,900 servers can train the risk scorer to recognize common security anti-patterns. SonarQube findings provide ground truth for code-level risk indicators. Maintainability metrics could serve as proxy signals for server trustworthiness. |

---

## 12. MCP API Usage Dataset (2,117 repos)

**Paper:** We Urgently Need Privilege Management in MCP: A Measurement of API Usage in MCP Ecosystems (Li et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2507.06250 |
| **Description** | Measurement dataset of API usage across real MCP applications, documenting privilege-sensitive API exposure and over-privilege patterns. Collected from 3 registries to demonstrate the urgent need for least-privilege enforcement. |
| **Structure Details** | 2,117 unique GitHub repositories from mcp.so, Glama, and Smithery. Contains tool/API definitions, over-privilege rate measurements, and sensitive API exposure classification. |
| **How the Paper Used It** | Demonstrated that MCP tools routinely access privilege-sensitive APIs without proper authorization controls. Provided evidence-based argument for least-privilege enforcement in MCP ecosystems. |
| **How It Can Help My Project** | The over-privilege measurements directly inform how the risk scorer should weight API access patterns. Privilege-sensitivity classifications can be used as features in the risk scoring model. Evidence of widespread over-privilege justifies strict default-deny policies. |

---

## 13. MCP Ecosystem Dataset (8,401 projects)

**Paper:** A Measurement Study of Model Context Protocol Ecosystem (Guo et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2509.25292 |
| **Description** | Characterization dataset of the MCP ecosystem covering servers, tools, and registries across 6 major marketplaces. Analyzes growth patterns, distribution, and observable risk indicators. |
| **Structure Details** | 8,401 valid MCP projects across 6 marketplaces. Covers server types, tool categories, transport protocols, language distributions, and value classifications. |
| **How the Paper Used It** | Used for ecosystem-scale characterization analyzing distribution of server types, tool categories, growth patterns, and observable risk indicators across the MCP landscape. |
| **How It Can Help My Project** | The ecosystem distribution data helps set risk scoring priors — understanding what 'normal' looks like enables anomaly-based risk detection. Growth pattern data can inform how quickly the risk scorer's training data becomes stale. |

---

## 14. Top-296 MCP Server Dataset

**Paper:** Securing AI Agent Execution — AgentBound (Bühler et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/MCP-Security/MCP-Artifact |
| **Description** | Dataset of the 296 most popular MCP servers by GitHub stars (59-63,215 stars) from PulseMCP. Used to evaluate automated security policy generation accuracy for the AgentBound access control framework. |
| **Structure Details** | 296 MCP servers (top 300 by stars, 296 successfully downloaded). 48 servers manually evaluated (~8 hours each by 2 authors). 816 total permissions across 48 servers (17 avg per server). AgentManifestGen matched 787 permissions (96.5% accuracy). |
| **How the Paper Used It** | Primary evaluation dataset for AgentBound's policy generation. Demonstrated 80.9% accuracy and 100% recall in automated manifest creation. 96 servers evaluated via GitHub Issues. |
| **How It Can Help My Project** | The permission profiles of 296 popular servers provide reference data for what 'normal' access patterns look like. The 17-permissions-per-server average establishes a baseline for the risk scorer to flag abnormal permission requests. |

---

## 15. Malicious MCP Server Dataset (Song et al.)

**Paper:** Beyond the Protocol: Unveiling Attack Vectors in the MCP Ecosystem (Song et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/MCP-Security/MCP-Artifact |
| **Description** | Public dataset of 4 MCP servers with known categories of malicious behaviors: Google Maps Server (malicious external resource), mcp_server_time (puppet attack), mcp-weather-server (dynamic API host rewriting), and wechat-mcp (SQL injection). |
| **Structure Details** | 4 malicious MCP servers, each targeting a different attack vector. Ready-to-use package format for security testing. |
| **How the Paper Used It** | Used to test AgentBox's security enforcement (RQ2). AgentBound successfully blocked all 4 attack types through its policy-based access control. |
| **How It Can Help My Project** | Provides labeled ground truth for the risk scorer — 4 known-malicious servers with documented attack vectors for testing detection accuracy. Useful as a quick validation set for the risk scoring pipeline. |

---

## 16. Damn Vulnerable MCP Server

**Paper:** Securing AI Agent Execution — AgentBound (Bühler et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/harishsg993010/damn-vulnerable-MCP-server |
| **Description** | A public security challenge dataset containing 10 intentionally vulnerable MCP servers designed for security testing, similar to DVWA for web applications. Each server contains one or multiple attack vectors. |
| **Structure Details** | 10 vulnerable MCP servers (C.1-C.10). Includes: 2 tool poisoning attacks, 1 rug pull attack, 2 malicious external resource attacks, 2 prompt injection attacks, and additional mixed vectors. |
| **How the Paper Used It** | Used to evaluate AgentBox against a diverse set of security challenges. AgentBox prevented 9 out of 10 attacks (all environment-targeting attacks blocked). |
| **How It Can Help My Project** | An excellent test bed for the risk scoring system — 10 servers with known vulnerabilities at varying severity levels. Can validate that the risk scorer assigns appropriate severity tiers to different attack types. The 'capture the flag' format enables iterative risk scorer improvement. |

---

## 17. Component-based Attack PoC Dataset (132 servers)

**Paper:** When MCP Servers Attack: Taxonomy, Feasibility, and Mitigation (Zhao et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | Paper under review — contact: Weibo Zhao et al. via https://arxiv.org/abs/2509.24272 |
| **Description** | A set of 12 Proof-of-Concept malicious MCP servers (one per attack category A1-A12) plus 120 generated malicious servers from modular component seeds. The generator can theoretically produce up to 1,046,529 unique malicious server configurations. |
| **Structure Details** | 12 hand-crafted PoC servers + 120 generated servers (10 per category). Generator seeds: 5 malicious launch commands, 7 initialization snippets, 10 malicious/30 benign tools, 10 malicious/10 benign resources, 5 malicious/5 benign prompts. Evaluated across 3 hosts and 5 LLMs, 15 trials each. |
| **How the Paper Used It** | Primary evaluation for taxonomy study. Also tested scanner effectiveness: mcp-scan detected only 4/120 poisoned servers; AI-Infra-Guard performed better but still insufficient. |
| **How It Can Help My Project** | The component-based server generation approach can produce large-scale training data for the risk scorer. The 12-category taxonomy provides a comprehensive attack classification scheme. Scanner evaluation results establish baselines to improve upon. |

---

## 18. MCP Attack Benchmark (Beyond the Protocol)

**Paper:** Beyond the Protocol: Unveiling Attack Vectors in the Model Context Protocol Ecosystem (Song et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/MCP-Security/MCP-Artifact |
| **Description** | End-to-end evaluation framework testing malicious MCP server attacks across LLMs and MCP clients. Tests three attack tasks (Privacy Steal, Result Manipulation, Cryptocurrency Theft) against three attack vectors (Tool Poisoning, Puppet Attack, Malicious External Resources). |
| **Structure Details** | Two benchmarks: (1) 3 tasks x 3 vectors x 5 LLMs x 20 tests = 900 tests; (2) 3 tasks x 3 vectors x 5 MCP clients x 20 tests = 900 tests. LLMs: Claude 3.7, GPT-4o, DeepSeek-V3, LLaMA-3.1-70B, Gemini 2.5 Pro. Clients: Cherry Studio, Claude Desktop, Cline, Copilot-MCP, Cursor. |
| **How the Paper Used It** | Found average 53% ASR with <5% refusal rate. Exploitation via Malicious External Resources achieved highest ASR (93.33%). Also included a 20-participant user study on a simulated aggregator platform. |
| **How It Can Help My Project** | The cross-LLM and cross-client evaluation reveals which combinations are most vulnerable — informing how the risk scorer should weight model/client context. The 93% ASR for external resource attacks highlights a critical severity tier. |

---

## 19. MCPShield Evaluation Suite (6 test suites)

**Paper:** MCPShield: A Security Cognition Layer for Adaptive Trust Calibration in MCP Agents (Zhou et al., 2026)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2602.14281 |
| **Description** | Multi-suite security evaluation framework containing 6 distinct malicious MCP server test suites: MCPSafetyBench (tool poisoning + command injection), MCPSecBench (tool substitution + workflow poisoning), DemonAgent (encoded payloads + persistence), MCP-Artifact (result manipulation), Adaptive Monitor (monitor hijacking), and Rug Pull Attack (temporal drift). |
| **Structure Details** | 6 test suites, each containing multiple malicious servers with different attack patterns. Evaluated using Tool Safety Rate (TSR), Detection Success Rate (DSR), Attack Success Rate (ASR), time overhead, and token overhead metrics. |
| **How the Paper Used It** | Comprehensive evaluation of MCPShield's three-phase lifecycle defense: pre-invocation probing, execution isolation, and post-invocation reasoning. Achieved 95.30% defense rate versus 10.05% baseline. |
| **How It Can Help My Project** | The 6 diverse test suites cover the full spectrum of MCP attack patterns. The lifecycle-based evaluation (pre/during/post invocation) directly maps to when the risk scorer should assess threats. The 95.30% defense rate sets a target benchmark for the risk scoring system. |

---

## 20. MCP-ITP Implicit Poisoning Data

**Paper:** MCP-ITP: An Automated Framework for Implicit Tool Poisoning in MCP (Li et al., 2026)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2601.07395 |
| **Description** | Automated framework-generated dataset of implicitly poisoned tool descriptions that achieve high attack success through innocuous-appearing text optimized via black-box techniques. The poisoned descriptions evade existing detection with only 0.3% detection rate. |
| **Structure Details** | Based on MCPTox's 548 implicit poisoning test cases. Evaluated across 12 LLM agents (o1-mini, GPT-4o-mini, GPT-3.5-turbo, DeepSeek-R1/V3, Gemini-2.5-flash, Qwen3 variants). Detection tested against AI-Infra-Guard and Oracle detectors. |
| **How the Paper Used It** | Demonstrated 84.2% attack success rate with only 0.3% detection by existing defenses. Showed that individual words in tool descriptions can steer agent behavior without explicit malicious instructions. |
| **How It Can Help My Project** | Reveals a critical blind spot for risk scoring: implicit poisoning that evades pattern-based detection. The risk scorer must incorporate semantic analysis beyond keyword matching. The 0.3% detection rate establishes the difficulty baseline for implicit attack detection. |

---

## 21. Log-To-Leak Attack Scenarios

**Paper:** Log-To-Leak: Prompt Injection Attacks on Tool-Using LLM Agents via Model Context Protocol (Hu et al., 2026)

| Field | Details |
|-------|---------|
| **Direct Link** | https://openreview.net/forum?id=UVgbFuXPaO |
| **Description** | Prompt injection attack framework exploiting MCP logging tools for data exfiltration. Demonstrates that benign infrastructure tools (logging, monitoring) can be weaponized to silently capture and transmit sensitive data while preserving task quality. |
| **Structure Details** | Attack scenarios targeting MCP logging and monitoring tools. Evaluation of leakage success rate, task quality preservation, and detection evasion across MCP configurations. |
| **How the Paper Used It** | Demonstrated successful covert data exfiltration through benign MCP infrastructure tools while maintaining normal task completion quality, making the attack difficult to detect through output monitoring. |
| **How It Can Help My Project** | Highlights that the risk scorer must evaluate seemingly benign tools (logging, monitoring) for covert channel potential. Risk scoring should account for tool combinations, not just individual tools. Task quality preservation during attacks means the risk scorer cannot rely solely on output quality as a safety signal. |

---

## 22. MCPSafetyScanner Test Scenarios

**Paper:** MCP Safety Audit: LLMs with the Model Context Protocol Allow Major Security Exploits (Radosevich & Halloran, 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/johnhalloran321/mcpSafetyScanner |
| **Description** | The first automated MCP security auditing tool with test scenarios for credential theft, malicious code execution, and coercion attacks. Tested against real MCP deployments using standard MCP servers (filesystem, Slack, Everything, Chroma). |
| **Structure Details** | Qualitative attack demonstrations on 4 real MCP servers. Tested with Claude 3.7 and Llama-3.3-70B-Instruct. Attack types: MCE (Malicious Code Execution), RAC (Remote Access Control), CT (Credential Theft), RADE (Retrieval-Agent Deception). |
| **How the Paper Used It** | Demonstrated coercion attacks enabling credential theft and malicious code execution against real MCP deployments through systematic vulnerability scanning with MCPSafetyScanner. |
| **How It Can Help My Project** | MCPSafetyScanner provides a ready-made tool for validating the risk scorer's detection capabilities. The documented attack types (MCE, RAC, CT, RADE) define critical severity categories. The real-world MCP server test environment ensures practical relevance. |

---

## 23. InjecAgent Dataset

**Paper:** InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents (Zhan et al., 2024)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/uiuc-kang-lab/InjecAgent |
| **Description** | Benchmark for indirect prompt injections in tool-integrated LLM agents with explicit study of private-data exfiltration. Provides user tools, attacker tools, and multiple agent configurations across direct harm and data stealing categories. |
| **Structure Details** | 1,054 test cases total. 17 user tools and 62 attacker tools. Two harm categories: direct harm and data stealing/exfiltration. Multiple agent configurations for vulnerability assessment. |
| **How the Paper Used It** | First indirect injection benchmark for tool-integrated agents. Systematically evaluated attack success rates across tools, agents, harm categories, and exfiltration scenarios. |
| **How It Can Help My Project** | The user-tool vs attacker-tool distinction maps directly to the risk scorer's need to differentiate legitimate and adversarial tool access. The exfiltration category is directly relevant to MCP data leakage risk assessment. Provides labeled test data for binary risk classification. |

---

## 24. AgentDojo Task Suites

**Paper:** AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents (Debenedetti et al., 2024)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/ethz-spylab/agentdojo |
| **Description** | Dynamic evaluation environment for prompt injection attacks and defenses in tool-using LLM agents. Provides realistic tasks with parameterized attacks, defense baselines, and reproducible benchmarking across 4 agent environments. |
| **Structure Details** | 4 task suites: Workspace, Travel, Banking, Slack. 97 user tasks and 629 injection tasks. Supports multiple attack implementations and defense baselines. Dynamic environment with parameterized attack generation. |
| **How the Paper Used It** | Used as the primary evaluation platform by Progent (41.2% -> 2.2% ASR reduction), LlamaFirewall, TraceAegis, ToolSafe, and The Task Shield. The most widely adopted agent security benchmark. |
| **How It Can Help My Project** | The most established evaluation platform for agent security — essential for benchmarking the MCP risk scoring system against existing defenses. The 4 realistic domains ensure broad coverage. Widely adopted, enabling direct comparison with published results. |

---

## 25. R-Judge Records

**Paper:** R-Judge: Benchmarking Safety Risk Awareness for LLM Agents (Yuan et al., 2024)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/Lordog/R-Judge |
| **Description** | Benchmark for evaluating risk awareness in LLM agent behaviors across diverse environments. Contains curated multi-turn agent interaction records with annotated safety labels and risk descriptions spanning 27 key risk scenarios. |
| **Structure Details** | 569 multi-turn agent interaction records. 27 risk scenarios across 5 application categories. 10 risk types with annotated safety labels. Sources: WebArena, ToolEmu, InterCode-Bash, InterCode-SQL, MINT environments. |
| **How the Paper Used It** | Evaluated 11 LLMs showing GPT-4o achieves 74.42% while others near random. Fine-tuning on safety judgment significantly improves performance. |
| **How It Can Help My Project** | The 10 risk types and 27 scenarios provide a template for defining MCP-specific risk categories. The scoring approach (judging agent interactions) directly mirrors the MCP risk scorer's goal. The 74.42% best accuracy shows the current difficulty level for risk assessment. |

---

## 26. ASB (Agent Safety Benchmark)

**Paper:** Agent Security Bench (Zhang et al., 2025) / Used by ToolSafe (Mou et al., 2026) and Progent (Shi et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/agiresearch/ASB |
| **Description** | Benchmark for formalizing and evaluating attacks and defenses in LLM-based agents. Contains multiple attack prompt types for systematic agent security evaluation. |
| **Structure Details** | 6 attack prompt types: combined_attack, context_ignoring, escape_characters, fake_completion, naive, plus average. Measures Utility (%) and ASR (%). Used by both Progent and ToolSafe for evaluation. |
| **How the Paper Used It** | Used as secondary benchmark by Progent (evaluated against 3 defenses) and as primary benchmark by ToolSafe for evaluating TS-Guard's step-level proactive guardrail. |
| **How It Can Help My Project** | The 6 attack prompt types provide a classification scheme for input-level risk assessment in the MCP security system. The utility vs ASR tradeoff measurements help calibrate how much task degradation is acceptable for security enforcement. |

---

## 27. AgentHarm Dataset

**Paper:** AgentHarm: Harmful Agent Behavior Benchmark (Gray Swan / UK AISI, 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://huggingface.co/datasets/ai-safety-institute/AgentHarm |
| **Description** | Benchmark for evaluating harmful agent behaviors including deepfakes, misinformation, and other dangerous capabilities. Contains ReAct trajectories with harmful agent requests. |
| **Structure Details** | ReAct-format trajectories with harmful behavior requests. Covers multiple harm categories. Used by ToolSafe and TraceAegis for evaluation. |
| **How the Paper Used It** | Used as evaluation benchmark by ToolSafe (measuring ASR, Safety Rate, and Helpfulness) and referenced by TraceAegis as a related benchmark for harmful behavior detection. |
| **How It Can Help My Project** | Provides ground truth for the most severe risk tier — requests that should always be denied. The harm categories inform the risk scorer's highest-severity classification criteria. |

---

## 28. RAS-Eval

**Paper:** RAS-Eval: Comprehensive Benchmark for LLM Agent Security (Fu et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/lanzer-tree/RAS-Eval |
| **Description** | Comprehensive benchmark for security evaluation of LLM agents in real-world environments. Contains CFI (Control-Flow Integrity) violation attacks adapted for metadata poisoning evaluation. |
| **Structure Details** | Multi-category security evaluation. Per-model distributions vary (e.g., Qwen3-8b: 919 Normal, 6 Poisoned). Format adapted for metadata poisoning by MindGuard evaluation. |
| **How the Paper Used It** | Used by MindGuard as a third evaluation dataset with attack payloads transformed into metadata poisoning format. Also referenced by MCP-Guard as an evaluation corpus. |
| **How It Can Help My Project** | The control-flow integrity violation focus is relevant to detecting tool invocation sequence manipulation in MCP. Provides additional evaluation data for the risk scorer's ability to detect metadata-level attacks. |

---

## 29. EICU-AC (Healthcare Access Control)

**Paper:** GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning (Xiang et al., 2024)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/guardagent/code |
| **Description** | Access control benchmark for healthcare LLM agents built on the eICU Collaborative Research Database. Defines three roles (physician, nursing, general admin) with different database permissions for role-based access evaluation. |
| **Structure Details** | 100 test samples across 10 databases. Three roles with distinct permission levels. Based on the eICU clinical database. |
| **How the Paper Used It** | Primary benchmark for evaluating GuardAgent's access control enforcement in the EHRAgent healthcare scenario. GuardAgent achieved >98% accuracy in safety assessment. |
| **How It Can Help My Project** | Demonstrates role-based access control evaluation methodology directly applicable to MCP agent access control. The three-role permission model provides a template for MCP agent role classification. Healthcare domain demonstrates high-stakes access control requirements. |

---

## 30. Mind2Web-SC (Web Navigation Safety Control)

**Paper:** GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning (Xiang et al., 2024)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/guardagent/code |
| **Description** | Safety control benchmark for web navigation agents built on Mind2Web. Defines safety rules based on user attributes (age, license) and action categories (shopping, rentals, etc.) for web interaction safety evaluation. |
| **Structure Details** | 100 test samples across 7 action categories. Safety rules based on user attributes and action types. Built on the Mind2Web web navigation dataset. |
| **How the Paper Used It** | Primary benchmark for evaluating GuardAgent's safety control in the SeeAct web navigation scenario. Tests whether the guard agent correctly enforces attribute-based safety constraints. |
| **How It Can Help My Project** | The attribute-based safety rules provide a model for context-dependent risk scoring in MCP — where the same tool invocation may be safe or risky depending on the requesting agent's attributes and context. |

---

## 31. MiniScope Synthetic Permission Dataset

**Paper:** MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents (Zhu et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2512.11147 |
| **Description** | Synthetic dataset of realistic user-agent interactions derived from 10 popular real-world applications. Contains single-method and multi-method requests for evaluating permission minimality, runtime overhead, and user effort. |
| **Structure Details** | 10 applications (Gmail: 79 methods/10 scopes, Google Calendar: 37/17, Slack: 247/84, Dropbox: 120/13, etc.). Single-method requests per API method. 200 multi-method requests per app. 2 multi-app suites (171 and 465 methods). 1-6% latency overhead measured. |
| **How the Paper Used It** | Evaluated MiniScope against 3 baselines (Vanilla, PerMethod, LLMScope) on permission minimality, runtime overhead, and user confirmation rates. MiniScope achieved lowest mismatch rates. |
| **How It Can Help My Project** | The permission hierarchy data from 10 real applications provides reference architectures for MCP tool permission modeling. The scope-based access control approach directly maps to MCP capability-level risk assessment. |

---

## 32. Trust Paradox Evaluation Scenarios (19 scenarios)

**Paper:** The Trust Paradox in LLM-Based Multi-Agent Systems (Xu et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2510.18563 |
| **Description** | Carefully constructed evaluation scenarios validating the trust paradox — that granting agents more capability inherently increases their vulnerability surface. Spans 5 capability levels tested across 4 model backends. |
| **Structure Details** | 19 scenarios across 5 capability tiers (basic, intermediate, advanced, expert, critical). 4 LLM backends: GPT-4o, Claude 3.5 Sonnet, Llama 3.1 70B, Mixtral 8x22B. Metrics: Trust Calibration Index, Capability-Risk Ratio, Safety Violation Rate. |
| **How the Paper Used It** | Empirically validated the trust paradox with TCI ranging 0.72-0.89, confirming systematic trust miscalibration. Inter-agent trust scores stabilize at 0.73-0.91 but require 8-15 iterations. |
| **How It Can Help My Project** | Demonstrates that the risk scorer must account for the trust-capability paradox — more capable agents may need higher scrutiny, not less. The 5-tier capability model informs how the risk scorer should adjust severity based on agent capability level. |

---

## 33. Indirect PI Attack Dataset (1,068 instances)

**Paper:** Exploiting Web Search Tools of AI Agents for Data Exfiltration (Rall et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://anonymous.4open.science/r/web-search-exploit-paper-FFC6 |
| **Description** | Systematic evaluation dataset for indirect prompt injection via web search tools in AI agents. Generated from 89 attack templates with 12 variations each using PyRIT converters (LLM fuzzing, encoding, Unicode obfuscation, etc.). |
| **Structure Details** | 1,068 unique attack instances from 89 templates x 12 variations. Tested on 28 models across providers (X-AI, Inception, Qwen, Meta, Anthropic, OpenAI, Google, DeepSeek, Mistral). Variations: LLM-based fuzzing, Base64 encoding, Unicode obfuscation, random capitalization, translation. |
| **How the Paper Used It** | Systematically evaluated LLM vulnerability to data exfiltration via web search tools. Found X-AI grok-4 most vulnerable (72.4%), OpenAI/Google/Amazon most resilient (near 0%). |
| **How It Can Help My Project** | The 12 attack variation types provide obfuscation categories the risk scorer must handle. The per-model vulnerability data informs model-specific risk adjustment. The PyRIT-based generation approach can be adapted to generate MCP-specific attack variants for training data. |

---

## 34. Synthetic PI Dataset (500 prompts)

**Paper:** Prompt Injection Detection and Mitigation via AI Multi-Agent NLP Frameworks (Gosmar et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2503.11517 |
| **Description** | 500 engineered injection prompts across 10 attack categories generated by OpenAI o3-mini. Categories include Direct Override, Authority Assertions, Hidden Commands, Role-Play, Logical Traps, Multi-Step, Conflicting Instructions, HTML/Markdown Embeds, Hybrid, and Social Engineering. |
| **Structure Details** | 500 prompts total (50 per category). 10 attack categories. Processed through a 3-agent pipeline (Generator, Sanitizer, Enforcer). Novel metrics: ISR, POF, PSR, CCS, TIVS. |
| **How the Paper Used It** | Evaluated the multi-agent NLP defense framework achieving 45.7% reduction in vulnerability score through layered mitigation. TIVS composite score measured across all categories. |
| **How It Can Help My Project** | The 10 attack categories provide a prompt-level risk classification taxonomy. The TIVS composite scoring methodology is directly transferable to MCP risk scoring design. The 4 novel metrics (ISR, POF, PSR, CCS) can be adapted as sub-scores in the MCP risk model. |

---

## 35. ShareGPT Conversation Dataset

**Paper:** Imprompter: Tricking LLM Agents into Improper Tool Use (Fu et al., 2024)

| Field | Details |
|-------|---------|
| **Direct Link** | https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered |
| **Description** | Real human-ChatGPT 3.5 conversations from late 2022 to early 2023. Used as training data for information exfiltration attacks that trick agents into improper tool use. |
| **Structure Details** | ~53,000 conversations. First 100 sampled for training, last 100 for validation. Format: multi-turn conversation transcripts. |
| **How the Paper Used It** | Used to train D_text for information exfiltration attacks. Evaluated using Syntax Correctness, PPL, Word Extraction Precision, and Word Extraction GPT Score. |
| **How It Can Help My Project** | Provides realistic conversation patterns for testing whether the risk scorer can detect exfiltration attempts embedded in natural-looking conversations. The adversarial attack methodology demonstrates attacks the risk scorer must handle. |

---

## 36. WildChat Dataset (1M interactions)

**Paper:** Imprompter: Tricking LLM Agents into Improper Tool Use (Fu et al., 2024)

| Field | Details |
|-------|---------|
| **Direct Link** | https://huggingface.co/datasets/allenai/WildChat-1M |
| **Description** | 1 million real human-LLM interaction logs from 2024 with PII annotations. Used for training and validating PII exfiltration attacks. Full version with toxic data requires gated access. |
| **Structure Details** | 1M interaction logs. 49 conversations with PII found (24 train, 25 validation). PII annotations included. Gated access for toxic content subset. |
| **How the Paper Used It** | Used for training/validation of PII exfiltration attacks. Evaluated with Syntax Correctness, PII Precision, PII Recall, and Context GPT Score. |
| **How It Can Help My Project** | The PII-annotated data is useful for testing whether the risk scorer can detect privacy leakage risks in MCP tool invocations. The large scale (1M interactions) provides diverse patterns for robust evaluation. |

---

## 37. DecodingTrust Dataset

**Paper:** DecodingTrust: A Comprehensive Assessment of Trustworthiness in GPT Models (Wang et al., 2023)

| Field | Details |
|-------|---------|
| **Direct Link** | https://huggingface.co/datasets/AI-Secure/DecodingTrust |
| **Description** | Eight-dimensional trustworthiness evaluation dataset for GPT models covering toxicity, stereotype bias, adversarial robustness, OOD robustness, adversarial demonstrations, privacy, machine ethics, and fairness. NeurIPS 2023 Outstanding Paper. |
| **Structure Details** | 8 evaluation dimensions, each with multiple sub-datasets. Includes: RealToxicityPrompts, BOLD, BBQ, SST-2, AdvGLUE, ANLI, RealtimeQA, MMLU, Enron Email, ETHICS, Jiminy Cricket, Adult (UCI), and more. Available on HuggingFace. |
| **How the Paper Used It** | Evaluated GPT-4 and GPT-3.5 across all 8 dimensions. Discovered GPT-4 is more vulnerable to jailbreaking than GPT-3.5 despite better baseline performance. |
| **How It Can Help My Project** | The 8-dimension framework provides a ready-made scoring rubric adaptable for MCP agent trustworthiness. The finding that capability does not equal trustworthiness is critical for risk assessment — the risk scorer should not assume more capable models are safer. |

---

## 38. TrustLLM Benchmark Datasets (30+)

**Paper:** TrustLLM: Trustworthiness in Large Language Models (Huang et al., 2024)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/HowieHwong/TrustLLM |
| **Description** | Comprehensive trustworthiness benchmark evaluating 16 LLMs across six dimensions (truthfulness, safety, fairness, robustness, privacy, machine ethics) using over 30 datasets. Published at ICML 2024. |
| **Structure Details** | 30+ datasets across 6 dimensions and 18 subcategories. Includes: SQuAD2.0, TruthfulQA, HaluEval, CrowS-Pair, StereoSet, AdvGLUE, Enron Email, ETHICS, ConfAIde, MoralChoice, Social Chemistry 101, and many more. 16 LLMs evaluated. |
| **How the Paper Used It** | Largest-scale LLM trustworthiness study. Found proprietary LLMs generally more trustworthy but some over-optimize safety at the cost of utility. |
| **How It Can Help My Project** | The 6 trustworthiness dimensions map to MCP risk scoring dimensions. The 30+ datasets provide extensive evaluation data. The safety-utility tradeoff finding is directly relevant to calibrating MCP risk scoring thresholds. |

---

## 39. NVD/CVE Database (31,000+ entries)

**Paper:** From Description to Score: Can LLMs Quantify Vulnerabilities? (Jafarikhah et al., 2026)

| Field | Details |
|-------|---------|
| **Direct Link** | https://nvd.nist.gov/ |
| **Description** | National Vulnerability Database containing CVE entries with CVSS v3.1 base metrics. Used to evaluate whether LLMs can automatically score vulnerabilities from textual descriptions. |
| **Structure Details** | 31,000+ CVEs from 2019-2024 with CVSS v3.1 base metrics (8 sub-metrics). Tested with 6 LLMs: GPT-4o, GPT-5, Llama-3.3-70B, Gemini-2.5-Flash, DeepSeek-R1, Grok-3. Format: CVE description text paired with CVSS scores. |
| **How the Paper Used It** | Evaluated 6 LLMs for automated CVSS scoring. Found two-shot prompting optimal. GPT-5 achieved highest precision. Meta-classifier combining LLM outputs provided marginal improvement. |
| **How It Can Help My Project** | CVSS scoring methodology is directly transferable to MCP risk scoring. The approach of using LLMs to quantify severity from textual descriptions mirrors how MCP Security could score agent requests from tool descriptions. The ensemble meta-classifier approach applies to combining multiple risk signals. |

---

## 40. glaive-function-calling-v2

**Paper:** MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol (Jing et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://huggingface.co/datasets/glaiveai/glaive-function-calling-v2 |
| **Description** | Widely used open-source dataset for training models on function calling. Contains real function calling conversations released by Glaive AI. |
| **Structure Details** | 112,960 instances total. Multi-turn function calling conversations. Used as source for both MCIP-Bench construction (200 gold instances) and MCIP Guardian training (2,000 sampled rows). Function pool of 10,633 function call pairs. |
| **How the Paper Used It** | Primary source for constructing MCIP-Bench gold instances and MCIP Guardian training data. Provided realistic function calling patterns for safety evaluation. |
| **How It Can Help My Project** | Large-scale function calling data directly relevant to training an MCP tool invocation risk classifier. The 112K+ instances provide diverse calling patterns for learning normal behavior baselines. The function pool enables training risk models on realistic tool interaction sequences. |

---

## 41. ToolACE Dataset

**Paper:** Used by MCIP (Jing et al., 2025) and MindGuard (Wang et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://huggingface.co/datasets/Team-ACE/ToolACE |
| **Description** | Function calling dataset used as a complementary data source for MCP security evaluation. Provides tool call samples for generalization validation and clean baseline comparison. |
| **Structure Details** | 11,300 rows. Used by MCIP-Bench for supplementary evaluation (1,026 instances). Also used by MindGuard as part of a 12,000+ heterogeneous clean tool call validation set. |
| **How the Paper Used It** | Used by MCIP for generalization validation on unseen risks. Used by MindGuard for TAE (Total Attention Energy) signal validation, confirming the signal can distinguish decision sources from non-sources. |
| **How It Can Help My Project** | Provides clean/benign tool call baselines essential for training a risk scorer to distinguish normal from anomalous MCP tool invocations. The generalization validation demonstrates how to test risk scoring robustness across different data sources. |

---

## 42. ToolBench Dataset

**Paper:** ToolHijacker: Prompt Injection Attack to Tool Selection in LLM Agents (Shi et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/OpenBMB/ToolBench |
| **Description** | Large-scale benchmark for enhancing tool-use capabilities of LLMs with instruction-tuning samples. Contains tools from RapidAPI used for evaluating tool selection attacks and defenses. |
| **Structure Details** | 126,486 instruction-tuning samples leveraging 16,464 tool documents from RapidAPI. After deduplication: 9,650 benign tool documents. Used with 10 target tasks and 1,000 task descriptions for attack evaluation. |
| **How the Paper Used It** | Secondary evaluation dataset for ToolHijacker. Gradient-free attack achieved 88.2% ASR with GPT-4o. Larger tool library (9,650 docs) made defense evaluation more realistic. Also used by MindGuard for TAE validation. |
| **How It Can Help My Project** | The 16K+ tool documents provide a large-scale tool registry for testing MCP tool-level risk classification. The ToolHijacker results (88.2% ASR) quantify the risk of tool selection manipulation that the MCP risk scorer must detect. |

---

## 43. MetaTool Benchmark Dataset

**Paper:** ToolHijacker: Prompt Injection Attack to Tool Selection in LLM Agents (Shi et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/HowieHwong/MetaTool |
| **Description** | Benchmark focusing on LLMs' capabilities in tool usage with scenario-driven evaluations. Contains tool documents sourced from OpenAI Plugins for evaluating tool selection accuracy and attack vulnerability. |
| **Structure Details** | 21,127 instances involving 199 benign tool documents from OpenAI Plugins. 10 high-quality target tasks designed for real-world needs. 100 target task descriptions per task (1,000 total). Metrics: Accuracy, ASR, Hit Rate, Attack Hit Rate. |
| **How the Paper Used It** | Primary evaluation dataset for ToolHijacker. Gradient-free attack achieved 96.7% ASR with GPT-4o on MetaTool. Human study with 6 participants showed >=71% failure to detect malicious tool documents. |
| **How It Can Help My Project** | The 199 tool document library from OpenAI Plugins provides realistic tool metadata for training the MCP risk scorer. The 96.7% ASR demonstrates that tool selection attacks are highly effective — the risk scorer must prioritize tool integrity verification. |

---

## 44. Meta Tool-Use Agentic PI Benchmark (600 scenarios)

**Paper:** LlamaFirewall: An Open Source Guardrail System for Building Secure AI Agents (Chennabasappa et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://huggingface.co/datasets/facebook/llamafirewall-alignmentcheck-evals |
| **Description** | Novel benchmark for evaluating prompt injection resilience in agentic environments across travel, information retrieval, and productivity domains. Simulates smartphone apps with realistic tool-use scenarios. |
| **Structure Details** | 600 scenarios (300 benign, 300 malicious). 7 injection techniques. 8 threat categories. Three domains: travel, info-retrieval, productivity. Format: tool-use agentic interaction traces. |
| **How the Paper Used It** | Used to evaluate LlamaFirewall's combined PromptGuard + AlignmentCheck pipeline for PI resilience. Measured ASR per attack type and threat category. |
| **How It Can Help My Project** | The 600-scenario benchmark with balanced benign/malicious split provides well-structured evaluation data for the MCP risk scorer. The 7 injection techniques and 8 threat categories inform the risk scoring taxonomy. Available on HuggingFace for direct use. |

---

## 45. CyberSecEval3

**Paper:** LlamaFirewall: An Open Source Guardrail System for Building Secure AI Agents (Chennabasappa et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/meta-llama/PurpleLlama/tree/main/CybersecurityBenchmarks |
| **Description** | Cybersecurity evaluation benchmark for LLM-generated code from Meta's PurpleLlama project. Tests code completion safety across multiple programming languages. |
| **Structure Details** | 50 code completions per language across 7+ programming languages. Evaluates whether LLM-generated code contains vulnerabilities. Metrics: Precision (96%), Recall (79%). |
| **How the Paper Used It** | Used to evaluate CodeShield component of LlamaFirewall for detecting insecure code patterns in LLM-generated code. |
| **How It Can Help My Project** | Code security evaluation is relevant when MCP agents generate or modify code through tool invocations. The risk scorer could integrate similar static analysis to assess code-generating tool calls. |

---

## 46. Anthropic Red-Teaming Dataset

**Paper:** NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications (Rebedea et al., 2023)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/anthropics/hh-rlhf |
| **Description** | Human-annotated prompts rated 0-4 for alignment bypass attempts, used to evaluate moderation rails. Paired with the Anthropic Helpful Dataset for balanced safety evaluation. |
| **Structure Details** | Highest-harm prompts sampled from the full red-teaming set. Balanced with ~200 total samples (harmful + helpful). Format: text prompts with harm severity ratings. |
| **How the Paper Used It** | Used to evaluate NeMo Guardrails' moderation capability — measuring percentage of harmful content blocked versus helpful content correctly allowed. |
| **How It Can Help My Project** | Provides adversarial prompts for testing the MCP risk scorer's ability to detect harmful requests. The harm severity ratings (0-4) provide labeled data for training graduated risk classification. |

---

## 47. CIAQA (Compositional Instruction Attack QA)

**Paper:** From Prompt Injections to Protocol Exploits: Threats in LLM-Powered AI Agents Workflows (Ferrag et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2506.23260 |
| **Description** | Dataset for evaluating Compositional Instruction Attacks (CIA) on LLMs, containing multiple-choice questions based on successful jailbreaks. Demonstrates >95% ASR on major models. |
| **Structure Details** | 2,700 multiple-choice questions based on 900 successful jailbreaks. Format: QA pairs testing compositional attack effectiveness. |
| **How the Paper Used It** | Cited to demonstrate that CIA achieves >95% ASR on GPT-4, GPT-3.5, and Llama2-70b-chat, quantifying the severity of compositional instruction attacks. |
| **How It Can Help My Project** | Compositional attacks that achieve >95% ASR represent a critical threat vector for MCP security. The risk scorer must detect when multiple innocent-looking instructions combine into an attack pattern. |

---

## 48. CrAIBench (Web3 AI Agent Benchmark)

**Paper:** From Prompt Injections to Protocol Exploits: Threats in LLM-Powered AI Agents Workflows (Ferrag et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://arxiv.org/abs/2506.23260 |
| **Description** | Web3 domain-specific benchmark for assessing AI agent robustness against context manipulation attacks across realistic blockchain tasks including token transfers, trading, and cross-chain interactions. |
| **Structure Details** | 150+ realistic blockchain tasks. 500+ attack test cases. Covers token transfers, trading, cross-chain interactions. Tests both prompt-based and fine-tuning-based defenses. |
| **How the Paper Used It** | Cited to demonstrate context manipulation attack effectiveness in Web3 ecosystems. Found prompt-based defenses ineffective while fine-tuning-based defenses showed more robustness. |
| **How It Can Help My Project** | Relevant to MCP risk scoring in financial/blockchain tool contexts. Demonstrates that domain-specific attack testing is necessary — the risk scorer may need specialized assessment for high-value MCP tool categories. |

---

## 49. AlpacaFarm Dataset (208 samples)

**Paper:** Defense Against Prompt Injection Attack by Leveraging Attack Techniques (Chen et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://github.com/tatsu-lab/stanford_alpaca |
| **Description** | Instruction-following dataset subset used for evaluating direct prompt injection defense. The defense approach inverts attack techniques for defensive purposes without requiring model fine-tuning. |
| **Structure Details** | 208 samples used for direct prompt injection evaluation. Part of the larger Stanford Alpaca dataset. Paired with 2,000-sample Filtered QA Dataset for indirect PI evaluation. |
| **How the Paper Used It** | Used to evaluate training-free defense achieving state-of-the-art results by inverting prompt injection attack techniques for defensive purposes. |
| **How It Can Help My Project** | The training-free defense approach is highly relevant for MCP Security since it requires no model modification. The inverted-attack methodology could be adapted for real-time MCP request screening. |

---

## 50. BFCL-v3 (Berkeley Function Calling Leaderboard)

**Paper:** MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol (Jing et al., 2025)

| Field | Details |
|-------|---------|
| **Direct Link** | https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard |
| **Description** | Benchmark for evaluating function calling capabilities of LLMs. Used to assess whether safety-oriented MCP designs affect practical function calling utility. |
| **Structure Details** | Comprehensive function calling evaluation across multiple LLM models. Measures overall accuracy percentage. Available on both GitHub and HuggingFace. |
| **How the Paper Used It** | Used as utility metric to evaluate the safety-utility tradeoff of MCIP Guardian — ensuring safety improvements don't degrade function calling capability. |
| **How It Can Help My Project** | Essential for measuring whether MCP risk scoring introduces unacceptable utility degradation. A risk scorer that blocks too many legitimate calls is impractical. BFCL-v3 provides the utility measurement standard. |

---
