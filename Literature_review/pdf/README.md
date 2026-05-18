# MCP Security Literature Review — Paper Library Guide

This folder contains **107 source papers** organized for the MCP Security thesis project, which builds a defense-oriented risk-scoring framework for evaluating AI agent access to MCP servers.

Papers are sorted into **category folders**, each containing **type subfolders** that describe what a paper contributes (attacks, defenses, benchmarks, surveys, measurements, frameworks, scoring, detection). The **Top_20/** folder contains copies of the 20 most important papers in recommended reading order.

---

## Quick Navigation

| Folder | Papers | Type subfolders | Description |
|--------|--------|-----------------|-------------|
| [Top_20/](#top-20-recommended-reading-order) | 19 | — | The most important papers, ranked by reading order |
| [1_MCP_Security/](#1-mcp-security-55-papers) | 55 | attacks, defenses, benchmarks, surveys | MCP-specific security frameworks, attacks, and defenses |
| [2_MCP_Protocol/](#2-mcp-protocol-10-papers) | 10 | surveys, measurements | MCP architecture, specifications, and ecosystem studies |
| [3_Multi_Agent_Trust/](#3-multi-agent-trust--access-control-9-papers) | 9 | frameworks, benchmarks | Trust frameworks, access control, and authorization |
| [4_Prompt_Injection/](#4-prompt-injection--tool-poisoning-17-papers) | 17 | attacks, defenses, benchmarks, surveys | Prompt injection attacks, tool poisoning, and defenses |
| [5_LLM_Guardrails/](#5-llm-guardrails-4-papers) | 4 | — (flat) | LLM guardrail and safety rail systems |
| [6_Risk_Scoring/](#6-risk-scoring--anomaly-detection-14-papers) | 14 | scoring, detection | Risk scoring, anomaly detection, and safety benchmarks |
| [7_Not_Academic/](#7-not-academic-4-entries) | 4 | — | MCP specification web pages (not downloadable PDFs) |
| [8_Unmatched/](#8-unmatched) | 1 | — | Generated artifact (not a source paper) |
| [Hebrew_Docs/](#hebrew-docs) | 2 | — | Hebrew-language reference documents (HTML) |

**3 papers could not be downloaded** (paywall/access denied) — see [Manual Downloads](#papers-requiring-manual-download).

---

## Top 20 — Recommended Reading Order

These are the most relevant papers for the thesis. Read them in this order — each builds on the previous. They are **duplicated** from their category folders for convenience.

| # | Paper | Score | Category |
|---|-------|-------|----------|
| 01 | **Model Context Protocol (MCP): Landscape, Security Threats, and Future Research Directions** | 10 | Protocol |
| 02 | **MCPShield: A Security Cognition Layer for Adaptive Trust Calibration in MCP Agents** | 10 | Security |
| 03 | **From Prompt Injections to Protocol Exploits: Threats in LLM-Powered AI Agents Workflows** | 9 | Injection |
| 04 | **Progent: Programmable Privilege Control for LLM Agents** | 9 | Trust |
| 05 | **When MCP Servers Attack: Taxonomy, Feasibility, and Mitigation** | 9 | Security |
| 06 | **MCP-Guard: A Multi-Stage Defense-in-Depth Framework for Securing MCP in Agentic AI** | 9 | Security |
| 07 | **From Description to Score: Can LLMs Quantify Vulnerabilities?** | 8 | Scoring |
| 08 | **MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers** | 9 | Security |
| 09 | **Breaking the Protocol: Security Analysis of the MCP Specification and Prompt Injection Vulnerabilities** | 9 | Security |
| 10 | **MindGuard: Intrinsic Decision Inspection for Securing LLM Agents Against Metadata Poisoning** | 9 | Security |
| 11 | **Securing AI Agent Execution** | 9 | Security |
| 12 | **Toward Understanding Security Issues in the Model Context Protocol Ecosystem** | 9 | Security |
| 13 | **Parasites in the Toolchain: A Large-Scale Analysis of Attacks on the MCP Ecosystem** | 9 | Security |
| 14 | **TRiSM for Agentic AI: A Review of Trust, Risk, and Security Management** | 8 | Scoring |
| 15 | **Prompt Injection Detection and Mitigation via AI Multi-Agent NLP Frameworks** | 8 | Injection |
| 16 | **Towards Automating Data Access Permissions in AI Agents** | 8 | Trust |
| 17 | **MCP-ITP: An Automated Framework for Implicit Tool Poisoning in MCP** | 8 | Security |
| 18 | **Log-To-Leak: Prompt Injection Attacks on Tool-Using LLM Agents via MCP** *(not downloaded — see below)* | 8 | Security |
| 19 | **ToolSafe: Enhancing Tool Invocation Safety via Proactive Step-level Guardrail and Feedback** | 8 | Scoring |
| 20 | **GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning** | 8 | Scoring |

---

## 1. MCP Security (55 papers)

Direct MCP security research: frameworks, attacks, defenses, benchmarks, and auditing tools.

### attacks/ (12 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Beyond the Protocol: Unveiling Attack Vectors in the MCP Ecosystem** | Song, Q. et al. | 2025 |
| **Compatibility at a Cost: Systematic Discovery and Exploitation of MCP Clause-Compliance Vulnerabilities** | Yang, N. et al. | 2026 |
| **Breaking the Protocol: Security Analysis of the MCP Specification and Prompt Injection Vulnerabilities** | Maloyan, N.; Namiot, D. | 2026 |
| **MCP Safety Audit: LLMs with the MCP Allow Major Security Exploits** | Radosevich, C.; Halloran, J. | 2025 |
| **MCP Threat Modeling and Analyzing Vulnerabilities to Prompt Injection with Tool Poisoning** | Huang, C. et al. | 2026 |
| **MCP-ITP: An Automated Framework for Implicit Tool Poisoning in MCP** | Li, Y. et al. | 2026 |
| **MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers** | Wang, H. et al. | 2025 |
| **MPMA: Preference Manipulation Attack** | — | — |
| **Parasites in the Toolchain: A Large-Scale Analysis of Attacks on the MCP Ecosystem** | Zhao, S. et al. | 2026 |
| **Supply-Chain Poisoning Attacks Against LLM Coding Agent Skill Ecosystems** | Qu, Y. et al. | 2026 |
| **Trivial Trojans: Cross-Tool Exfiltration** | — | — |
| **When MCP Servers Attack: Taxonomy, Feasibility, and Mitigation** | Zhao, C. et al. | 2025 |

### defenses/ (22 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **AgentGuardian: Learning Access Control Policies to Govern AI Agent Behavior** | Abaev, N. et al. | 2026 |
| **AgenticCyOps: Securing Multi-Agentic AI Integration in Enterprise Cyber Operations** | Mitra, S. et al. | 2026 |
| **AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents** | Wang, H. et al. | 2025 |
| **ClawGuard: A Runtime Security Framework for Tool-Augmented LLM Agents Against Indirect Prompt Injection** | Zhao, W. et al. | 2026 |
| **CSAgent: Secure and Efficient Access Control for Computer-Use Agents via Context Space** | Gong, H. et al. | 2026 |
| **Enterprise-Grade Security for the MCP: Frameworks and Mitigation Strategies** | Narajala, S.; Habler, E. | 2025 |
| **ETDI: Mitigating Tool Squatting and Rug Pull Attacks in MCP using OAuth-Enhanced Tool Definitions** | Bhatt, D. | 2025 |
| **MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol** | Jing, Y. et al. | 2025 |
| **MCP for Vision Systems: Audit, Security, and Protocol Extensions** | Tiwari, A. et al. | 2025 |
| **MCP Guardian: A Security-First Layer for Safeguarding MCP-Based AI System** | Kumar, S. et al. | 2025 |
| **MCPGuard: Automatically Detecting Vulnerabilities in MCP Servers** | Wang, B. et al. | 2025 |
| **MCP Safety Training: Preference Alignment** | — | — |
| **MCP Security and Tenancy Boundaries** | Gaddam, R.R. | 2024 |
| **MCP-Guard: A Multi-Stage Defense-in-Depth Framework for Securing MCP in Agentic AI** | Xing, W. et al. | 2025 |
| **MCPShield: A Security Cognition Layer for Adaptive Trust Calibration in MCP Agents** | Zhou, Z. et al. | 2026 |
| **MindGuard: Intrinsic Decision Inspection for Securing LLM Agents Against Metadata Poisoning** | Wang, Z. et al. | 2025 |
| **Policy Compiler for Secure Agentic Systems** | Palumbo, N. et al. | 2026 |
| **SEAgent: Taming Privilege Escalation in LLM-Based Agent Systems via Mandatory Access Control** | Ji, Z. et al. | 2026 |
| **Securing AI Agent Execution** | Buhler, E. et al. | 2025 |
| **SMCP: Secure Model Context Protocol** | Hou, Y. et al. | 2026 |
| **Symbolic Guardrails for Domain-Specific Agents: Safety and Security Without Sacrificing Utility** | Hong, Y. et al. | 2026 |
| **TRUSTDESC: Preventing Tool Poisoning in LLM Applications via Trusted Description Generation** | Ye, H. et al. | 2026 |

### benchmarks/ (8 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Are AI-assisted Development Tools Immune to Prompt Injection?** | Huang, C. et al. | 2026 |
| **ATBench: A Diverse and Realistic Agent Trajectory Benchmark for Safety Evaluation and Diagnosis** | Li, Y. et al. | 2026 |
| **AutoMalTool: Automatic Red Teaming LLM-based Agents with Model Context Protocol Tools** | He, P. et al. | 2025 |
| **MCP Security Bench: Benchmarking Attacks Against Model Context Protocol in LLM Agents** | Zhang, D. et al. | 2026 |
| **MCP-SafetyBench: A Benchmark for Safety Evaluation of LLMs with Real-World MCP Servers** | Zong, Y. et al. | 2025 |
| **MCPSecBench: A Systematic Security Benchmark and Playground for Testing MCP** | Yang, X. et al. | 2025 |
| **OpenAgentSafety: A Comprehensive Framework for Evaluating Real-World AI Agent Safety** | Vijayvargiya, S. et al. | 2025 |
| **Toward Understanding Security Issues in the Model Context Protocol Ecosystem** | Li, J.; Gao, Y. | 2025 |

### surveys/ (11 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **A Comprehensive Security Framework for MCP in Multi-Agent AI Systems** | Narayan, O. et al. | 2026 |
| **A Secure Accountability Framework for Multi-Modal Agent Systems via MCP** | Kumar, S.N.P. | 2025 |
| **A Systematic Security Analysis of Model Context Protocol: Vulnerabilities, Exploits, and Mitigations** | Siameh, T. et al. | 2026 |
| **A Formal Security Framework for MCP-Based AI Agents: Threat Taxonomy, Verification Models, and Defense Mechanisms** | Acharya, N.; Gupta, G.K. | 2026 |
| **MCP-38: A Comprehensive Threat Taxonomy for Model Context Protocol Systems** | Shen, Y.T. et al. | 2026 |
| **MCP-DPT: A Defense-Placement Taxonomy and Coverage Analysis for Model Context Protocol Security** | Rostamzadeh, M. et al. | 2026 |
| **Securing the MCP: Defending LLMs Against Tool Poisoning and Adversarial Attacks** | Jamshidi, S. et al. | 2025 |
| **Securing the MCP: Risks, Controls, and Governance** | Errico, H. et al. | 2025 |
| **Security Threat Modeling for Emerging AI-Agent Protocols: MCP, A2A, Agora, ANP** | Anbiace, Z. et al. | 2026 |
| **SoK: Security and Safety in the Model Context Protocol Ecosystem** | Gaire, S. et al. | 2025 |
| **The Attack and Defense Landscape of Agentic AI: A Comprehensive Survey** | Kim, J. et al. | 2026 |

---

## 2. MCP Protocol (10 papers)

MCP architecture, specifications, ecosystem measurements, and protocol-level studies.

### surveys/ (6 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, and ANP** | Ehtesham, A. et al. | 2025 |
| **A Survey of the Model Context Protocol: Standardizing Context to Enhance LLMs** | Singh, A. et al. | 2025 |
| **A Survey on MCP: State-of-the-Art, Challenges and Future Directions** | Ray, P.P. | 2025 |
| **Advancing Multi-Agent Systems Through MCP: Architecture, Implementation, and Applications** | Krishnan, N. | 2025 |
| **Model Context Protocol (MCP): Landscape, Security Threats, and Future Research Directions** | Hou, Y. et al. | 2025 |
| **Systems Security Foundations for Agentic Computing** | Christodorescu, M. et al. | 2025 |

### measurements/ (4 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **A Measurement Study of Model Context Protocol Ecosystem** | Guo, T. et al. | 2025 |
| **MCP Does Not Stand for Misuse Cryptography Protocol: Uncovering Cryptographic Misuse in MCP at Scale** | Yan, B. et al. | 2025 |
| **Model Context Protocol (MCP) at First Glance: Studying the Security and Maintainability of MCP Servers** | Hasan, M. et al. | 2025 |
| **We Urgently Need Privilege Management in MCP: A Measurement of API Usage in MCP Ecosystems** | Li, Y. et al. | 2025 |

---

## 3. Multi-Agent Trust & Access Control (9 papers)

Trust frameworks, authorization, access control, and trustworthiness benchmarks for LLM agents.

### frameworks/ (6 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **A Novel Zero-Trust Identity Framework for Agentic AI: Decentralized Authentication and Fine-Grained Access Control** | Huang, K. et al. | 2025 |
| **A Vision for Access Control in LLM-based Agent Systems** | Li, Y. et al. | 2025 |
| **Caging the Agents: A Zero Trust Security Architecture for Autonomous AI in Healthcare** | Maiti, S. | 2026 |
| **Progent: Programmable Privilege Control for LLM Agents** | Shi, Z. et al. | 2025 |
| **The Trust Paradox in LLM-Based Multi-Agent Systems** | Xu, Y. et al. | 2025 |
| **Towards Automating Data Access Permissions in AI Agents** | Wu, X. et al. | 2025 |

### benchmarks/ (3 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **DecodingTrust: A Comprehensive Assessment of Trustworthiness in GPT Models** | Wang, B. et al. | 2023 |
| **Towards Trustworthy AI: A Review of Ethical and Robust Large Language Models** | Ferdaus, M. et al. | 2024 |
| **TrustLLM: Trustworthiness in Large Language Models** | Huang, Y. et al. | 2024 |

---

## 4. Prompt Injection & Tool Poisoning (17 papers)

Prompt injection attacks, tool manipulation, indirect injection, and related defenses.

### attacks/ (8 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents** | Zhan, Q. et al. | 2025 |
| **Exploiting Web Search Tools of AI Agents for Data Exfiltration** | Rall, E. et al. | 2025 |
| **From Prompt Injections to Protocol Exploits: Threats in LLM-Powered AI Agents Workflows** | Ferrag, M. et al. | 2025 |
| **Imprompter: Tricking LLM Agents into Improper Tool Use** | Fu, Z. et al. | 2024 |
| **InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated LLM Agents** | Zhan, Q. et al. | 2024 |
| **Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection** | Greshake, K. et al. | 2023 |
| **Prompt Injection Attack to Tool Selection in LLM Agents (ToolHijacker)** | Shi, Z. et al. | 2025 |
| **Red-Teaming LLM Multi-Agent Systems via Communication Attacks** | He, P. et al. | 2025 |

### defenses/ (5 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Defense Against Prompt Injection Attack by Leveraging Attack Techniques** | Chen, Y. et al. | 2025 |
| **MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents** | Zhu, Y. et al. | 2025 |
| **Prompt Injection Detection and Mitigation via AI Multi-Agent NLP Frameworks** | Gosmar, D. et al. | 2025 |
| **The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection** | Jia, Y. et al. | 2025 |
| **Towards Verifiably Safe Tool Use for LLM Agents** | Doshi, R. et al. | 2026 |

### benchmarks/ (2 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents** | Debenedetti, E. et al. | 2024 |
| **SIRAJ: Diverse and Efficient Red-Teaming for LLM Agents via Distilled Structured Reasoning** | Zhou, K. et al. | 2025 |

### surveys/ (2 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Agentic AI Security: Threats, Defenses, Evaluation, and Open Challenges** | Chhabra, A. et al. | 2025 |
| **Prompt Injection SoK: Attacks on Agentic Coding Assistants — Vulnerabilities in Skills, Tools, and Protocols** | Maloyan, N.; Namiot, D. | 2026 |

---

## 5. LLM Guardrails (4 papers)

Guardrail systems and safety rails for LLM applications. Papers are stored directly in this folder (no type subfolders).

| Paper | Authors | Year |
|-------|---------|------|
| **LlamaFirewall: An Open Source Guardrail System for Building Secure AI Agents** | Meta | 2025 |
| **LLM Agents Should Employ Security Principles** | Zhang, K. et al. | 2025 |
| **MI9: An Integrated Runtime Governance Framework for Agentic AI** | Wang, C.L. et al. | 2025 |
| **NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails** | Rebedea, T. et al. | 2023 |

---

## 6. Risk Scoring & Anomaly Detection (14 papers)

Risk scoring methodologies, safety benchmarks, anomaly detection, and agent behavior monitoring.

### scoring/ (7 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **ASTRA: Agentic Steerability and Risk Assessment Framework** | Hazan, I. et al. | 2025 |
| **From Description to Score: Can LLMs Quantify Vulnerabilities?** | Jafarikhah, T. et al. | 2026 |
| **ProbGuard: Proactive Runtime Enforcement of LLM Agent Safety via Probabilistic Model Checking** | Wang, H. et al. | 2025 |
| **PropensityBench: Evaluating Latent Safety Risks in Large Language Models via an Agentic Approach** | Sehwag, U.M. et al. | 2025 |
| **R-Judge: Benchmarking Safety Risk Awareness for LLM Agents** | Yuan, T. et al. | 2024 |
| **Risk Analysis Techniques for Governed LLM-based Multi-Agent Systems** | Reid, A. et al. | 2025 |
| **TRiSM for Agentic AI: A Review of Trust, Risk, and Security Management** | Raza, S. et al. | 2025 |

### detection/ (7 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Adaptive and Explainable AI Agents for Anomaly Detection in Critical IoT Infrastructure** | Sharma, S.; Mehta, V. | 2025 |
| **GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning** | Xiang, Z. et al. | 2024 |
| **Mind the GAP: Text Safety Does Not Transfer to Tool-Call Safety in LLM Agents** | Cartagena, A.; Teixeira, A. | 2026 |
| **SentinelAgent: Graph-based Anomaly Detection in LLM-based Multi-Agent Systems** | He, R. et al. | 2025 |
| **ToolSafe: Enhancing Tool Invocation Safety via Proactive Step-level Guardrail and Feedback** | Mou, Y. et al. | 2026 |
| **TraceAegis: Securing LLM-Based Agents via Hierarchical and Behavioral Anomaly Detection** | Chen, Y. et al. | 2025 |
| **Unsafer in Many Turns: Benchmarking and Defending Multi-Turn Safety Risks in Tool-Using Agents** | Li, X. et al. | 2026 |

---

## 7. Not Academic (4 entries)

These are MCP specification web pages, not downloadable academic papers. Saved as `.txt` placeholders with URLs.

| Entry | URL |
|-------|-----|
| Model Context Protocol Specification | https://modelcontextprotocol.io/specification/2025-11-25 |
| MCP Authorization Specification | https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization |
| Security Best Practices | https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices |
| Model Context Protocol Specification (v2025-11-25) | https://modelcontextprotocol.io/specification/2025-11-25 |

---

## 8. Unmatched

Contains one generated project artifact (not a source paper):

| File | Notes |
|------|-------|
| `mcp_security_literature_review.pdf` | **Project output** — generated literature review document summarizing 62 papers. Not a source paper. |

---

## Papers Requiring Manual Download

These 3 papers returned HTTP 403 (access denied / paywall). You may need institutional access or to find them through Google Scholar.

| Paper | URL |
|-------|-----|
| **Log-To-Leak: Prompt Injection Attacks on Tool-Using LLM Agents via MCP** | [OpenReview](https://openreview.net/forum?id=UVgbFuXPaO) |
| **Toward Agentic IAM: A Probabilistic Authorization Framework for Least Privilege AI Workflows** | [ACM DL](https://doi.org/10.1145/3773276.3776564) |
| **AI Agents Under Threat: A Survey of Key Security Challenges and Future Pathways** | [ACM DL](https://doi.org/10.1145/3716628) |

Once downloaded manually, place them in the correct category/type folder:
- Log-To-Leak → `1_MCP_Security/attacks/`
- Toward Agentic IAM → `3_Multi_Agent_Trust/frameworks/`
- AI Agents Under Threat → `6_Risk_Scoring/scoring/`

---

## Hebrew Docs

Hebrew-language reference documents related to the MCP literature review, stored in [Hebrew_Docs/](Hebrew_Docs/).

| File | Description |
|------|-------------|
| `mcp-hebrew.html` | Hebrew summary of MCP concepts and security topics |
| `mcp-hebrew-full.html` | Extended Hebrew document with comprehensive MCP coverage |

---

## Recently Added — 2026-05-05

### Scoring_curated/ (19 PDFs + README)

Curated set of papers that **strictly produce or study a numeric/graded risk score** — directly relevant to the thesis's MCP risk-scoring framework. Organized into 7 categories with per-category explanations in [Scoring_curated/README.md](Scoring_curated/README.md):

1. MCP-specific risk scoring (3 papers)
2. Vulnerability scoring — CVSS automation (2)
3. Permission and tool-invocation risk scoring (3)
4. Anomaly severity scoring (2)
5. Agent action harm and safety scoring (3)
6. Trust scoring — zero-trust access (1 + 1 manual)
7. Asset / data importance scoring (5)

### Context-only PDFs at this folder root (non-scoring, kept for reference)

These were downloaded earlier in the same batch but describe threat taxonomies, benchmarks, or architectures rather than scoring mechanisms. Useful as background but not in `Scoring_curated/`.

| File | Why kept |
|---|---|
| `2025_Hou_mcp-landscape-security-threats.pdf` | MCP threat taxonomy (arXiv 2503.23278) |
| `2025_Narajala_mcp-enterprise-grade-security.pdf` | MCP enterprise mitigation framework (arXiv 2504.08623) |
| `2025_MCPSecBench-systematic-security-benchmark.pdf` | Attack benchmark, not scoring (arXiv 2508.13220) |
| `2025_first-look-mcp-ecosystem-security.pdf` | MCP ecosystem audit (arXiv 2510.16558) |
| `2025_mcp-at-first-glance-security-maintainability.pdf` | Health metrics study (arXiv 2506.13538) |
| `2025_securing-ai-agent-execution.pdf` | AgentBound access control (arXiv 2510.21236) |
| `2025_lm-agents-fail-act-risk-knowledge.pdf` | Diagnostic study (arXiv 2508.13465) |
| `2023_dlp-classification-igbca.pdf` | DLP classification, not scoring (arXiv 2312.13711) |
| `2025_contextual-sensitive-data-detection.pdf` | Sensitive-data detection (arXiv 2512.04120) |
| `2020_NIST_SP_800-207_zero-trust-architecture.pdf` | Zero-trust reference architecture |
