# MCP Security Literature Review — Paper Library Guide

This folder contains **81 cataloged papers** organized for the MCP Security thesis project, which builds a **dynamic 1-10 risk scoring system** for evaluating AI agent access to MCP servers.

Papers are sorted into **category folders**, each containing **score subfolders** (Score_10 = most relevant, Score_04 = least). The **Top_20/** folder contains copies of the 20 most important papers in recommended reading order.

---

## Quick Navigation

| Folder | Papers | Description |
|--------|--------|-------------|
| [Top_20/](#top-20-recommended-reading-order) | 19 | The most important papers, ranked by reading order |
| [1_MCP_Security/](#1-mcp-security-31-papers) | 31 | MCP-specific security frameworks, attacks, and defenses |
| [2_MCP_Protocol/](#2-mcp-protocol-9-papers) | 9 | MCP architecture, specifications, and ecosystem studies |
| [3_Multi_Agent_Trust/](#3-multi-agent-trust--access-control-7-papers) | 7 | Trust frameworks, access control, and authorization |
| [4_Prompt_Injection/](#4-prompt-injection--tool-poisoning-14-papers) | 14 | Prompt injection attacks, tool poisoning, and defenses |
| [5_LLM_Guardrails/](#5-llm-guardrails-2-papers) | 2 | LLM guardrail and safety rail systems |
| [6_Risk_Scoring/](#6-risk-scoring--anomaly-detection-8-papers) | 8 | Risk scoring, anomaly detection, and safety benchmarks |
| [7_Not_Academic/](#7-not-academic-4-entries) | 4 | MCP specification web pages (not downloadable PDFs) |
| [8_Unmatched/](#8-unmatched) | 1 | Generated artifact (not a source paper) |
| [Hebrew_Docs/](#hebrew-docs) | 2 | Hebrew-language reference documents (HTML) |

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
| 13 | **Mind Your Server: A Systematic Study of Parasitic Toolchain Attacks on the MCP Ecosystem** | 9 | Security |
| 14 | **TRiSM for Agentic AI: A Review of Trust, Risk, and Security Management** | 8 | Scoring |
| 15 | **Prompt Injection Detection and Mitigation via AI Multi-Agent NLP Frameworks** | 8 | Injection |
| 16 | **Towards Automating Data Access Permissions in AI Agents** | 8 | Trust |
| 17 | **MCP-ITP: An Automated Framework for Implicit Tool Poisoning in MCP** | 8 | Security |
| 18 | **Log-To-Leak: Prompt Injection Attacks on Tool-Using LLM Agents via MCP** *(not downloaded — see below)* | 8 | Security |
| 19 | **ToolSafe: Enhancing Tool Invocation Safety via Proactive Step-level Guardrail and Feedback** | 8 | Scoring |
| 20 | **GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning** | 8 | Scoring |

---

## 1. MCP Security (31 papers)

Direct MCP security research: frameworks, attacks, defenses, benchmarks, and auditing tools.

### Score_10/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **MCPShield: A Security Cognition Layer for Adaptive Trust Calibration in MCP Agents** | Zhou, Z. et al. | 2026 |

### Score_09/ (8 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Breaking the Protocol: Security Analysis of the MCP Specification and Prompt Injection Vulnerabilities** | Maloyan, N.; Namiot, D. | 2026 |
| **MCP-Guard: A Multi-Stage Defense-in-Depth Framework for Securing MCP in Agentic AI** | Xing, W. et al. | 2025 |
| **MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers** | Wang, H. et al. | 2025 |
| **Mind Your Server: A Systematic Study of Parasitic Toolchain Attacks on the MCP Ecosystem** | Zhao, Y. et al. | 2025 |
| **MindGuard: Intrinsic Decision Inspection for Securing LLM Agents Against Metadata Poisoning** | Wang, Z. et al. | 2025 |
| **Securing AI Agent Execution** | Buhler, E. et al. | 2025 |
| **Toward Understanding Security Issues in the Model Context Protocol Ecosystem** | Li, J.; Gao, Y. | 2025 |
| **When MCP Servers Attack: Taxonomy, Feasibility, and Mitigation** | Zhao, C. et al. | 2025 |

### Score_08/ (12 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **A Formal Security Framework for MCP-Based AI Agents: Threat Taxonomy, Verification Models, and Defense Mechanisms** | Acharya, N.; Gupta, G.K. | 2026 |
| **A Systematic Security Analysis of Model Context Protocol: Vulnerabilities, Exploits, and Mitigations** | Siameh, T. et al. | 2026 |
| **Beyond the Protocol: Unveiling Attack Vectors in the MCP Ecosystem** | Song, Q. et al. | 2025 |
| **MCP Safety Audit: LLMs with the MCP Allow Major Security Exploits** | Radosevich, C.; Halloran, J. | 2025 |
| **MCP-DPT: A Defense-Placement Taxonomy and Coverage Analysis for Model Context Protocol Security** | Rostamzadeh, M. et al. | 2026 |
| **MCP-ITP: An Automated Framework for Implicit Tool Poisoning in MCP** | Li, Y. et al. | 2026 |
| **MCPSecBench: A Systematic Security Benchmark and Playground for Testing MCP** | Yang, X. et al. | 2025 |
| **MPMA: Preference Manipulation Attack** | — | — |
| **Securing the MCP: Defending LLMs Against Tool Poisoning and Adversarial Attacks** | Jamshidi, S. et al. | 2025 |
| **Securing the MCP: Risks, Controls, and Governance** | Errico, H. et al. | 2025 |
| **Security Threat Modeling for Emerging AI-Agent Protocols: MCP, A2A, Agora, ANP** | Anbiace, Z. et al. | 2026 |
| **Trivial Trojans: Cross-Tool Exfiltration** | — | — |

### Score_07/ (10 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **A Comprehensive Security Framework for MCP in Multi-Agent AI Systems** | Narayan, O. et al. | 2026 |
| **A Secure Accountability Framework for Multi-Modal Agent Systems via MCP** | Kumar, S.N.P. | 2025 |
| **Enterprise-Grade Security for the MCP: Frameworks and Mitigation Strategies** | Narajala, S.; Habler, E. | 2025 |
| **ETDI: Mitigating Tool Squatting and Rug Pull Attacks in MCP using OAuth-Enhanced Tool Definitions** | Bhatt, D. | 2025 |
| **MCP for Vision Systems: Audit, Security, and Protocol Extensions** | Tiwari, A. et al. | 2025 |
| **MCP Guardian: A Security-First Layer for Safeguarding MCP-Based AI System** | Kumar, S. et al. | 2025 |
| **MCP Safety Training: Preference Alignment** | — | — |
| **MCP Security and Tenancy Boundaries** | Gaddam, R.R. | 2024 |
| **MCP-SafetyBench: A Benchmark for Safety Evaluation of LLMs with Real-World MCP Servers** | Zong, Y. et al. | 2025 |
| **MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol** | Jing, Y. et al. | 2025 |
| **SMCP: Secure Model Context Protocol** | Hou, Y. et al. | 2026 |

---

## 2. MCP Protocol (9 papers)

MCP architecture, specifications, ecosystem measurements, and protocol-level studies.

### Score_10/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **Model Context Protocol (MCP): Landscape, Security Threats, and Future Research Directions** | Hou, Y. et al. | 2025 |

### Score_08/ (2 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Model Context Protocol (MCP) at First Glance: Studying the Security and Maintainability of MCP Servers** | Hasan, M. et al. | 2025 |
| **We Urgently Need Privilege Management in MCP: A Measurement of API Usage in MCP Ecosystems** | Li, Y. et al. | 2025 |

### Score_07/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, and ANP** | Ehtesham, A. et al. | 2025 |

### Score_06/ (3 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **A Measurement Study of Model Context Protocol Ecosystem** | Guo, T. et al. | 2025 |
| **A Survey of the Model Context Protocol: Standardizing Context to Enhance LLMs** | Singh, A. et al. | 2025 |
| **A Survey on MCP: State-of-the-Art, Challenges and Future Directions** | Ray, P.P. | 2025 |

### Score_05/ (2 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Advancing Multi-Agent Systems Through MCP: Architecture, Implementation, and Applications** | Krishnan, N. | 2025 |
| **Systems Security Foundations for Agentic Computing** | Christodorescu, M. et al. | 2025 |

---

## 3. Multi-Agent Trust & Access Control (7 papers)

Trust frameworks, authorization, access control, and trustworthiness benchmarks for LLM agents.

### Score_09/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **Progent: Programmable Privilege Control for LLM Agents** | Shi, Z. et al. | 2025 |

### Score_08/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **Towards Automating Data Access Permissions in AI Agents** | Wu, X. et al. | 2025 |

### Score_07/ (2 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **A Vision for Access Control in LLM-based Agent Systems** | Li, Y. et al. | 2025 |
| **The Trust Paradox in LLM-Based Multi-Agent Systems** | Xu, Y. et al. | 2025 |

### Score_05/ (2 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **DecodingTrust: A Comprehensive Assessment of Trustworthiness in GPT Models** | Wang, B. et al. | 2023 |
| **TrustLLM: Trustworthiness in Large Language Models** | Huang, Y. et al. | 2024 |

### Score_04/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **Towards Trustworthy AI: A Review of Ethical and Robust Large Language Models** | Ferdaus, M. et al. | 2024 |

---

## 4. Prompt Injection & Tool Poisoning (14 papers)

Prompt injection attacks, tool manipulation, indirect injection, and related defenses.

### Score_09/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **From Prompt Injections to Protocol Exploits: Threats in LLM-Powered AI Agents Workflows** | Ferrag, M. et al. | 2025 |

### Score_08/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **Prompt Injection Detection and Mitigation via AI Multi-Agent NLP Frameworks** | Gosmar, D. et al. | 2025 |

### Score_07/ (5 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Imprompter: Tricking LLM Agents into Improper Tool Use** | Fu, Z. et al. | 2024 |
| **InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated LLM Agents** | Zhan, Q. et al. | 2024 |
| **MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents** | Zhu, Y. et al. | 2025 |
| **Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection** | Greshake, K. et al. | 2023 |
| **Prompt Injection Attack to Tool Selection in LLM Agents (ToolHijacker)** | Shi, Z. et al. | 2025 |

### Score_06/ (4 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents** | Debenedetti, E. et al. | 2024 |
| **Exploiting Web Search Tools of AI Agents for Data Exfiltration** | Rall, E. et al. | 2025 |
| **Prompt Injection Attack to Tool Selection in LLM Agents** | Shi, Z. et al. | 2025 |
| **Towards Verifiably Safe Tool Use for LLM Agents** | Doshi, R. et al. | 2026 |

### Score_05/ (3 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents** | Zhan, Q. et al. | 2025 |
| **Defense Against Prompt Injection Attack by Leveraging Attack Techniques** | Chen, Y. et al. | 2025 |
| **The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection** | Jia, Y. et al. | 2025 |

---

## 5. LLM Guardrails (2 papers)

Guardrail systems and safety rails for LLM applications.

### Score_07/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **LlamaFirewall: An Open Source Guardrail System for Building Secure AI Agents** | Meta | 2025 |

### Score_05/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails** | Rebedea, T. et al. | 2023 |

---

## 6. Risk Scoring & Anomaly Detection (8 papers)

Risk scoring methodologies, safety benchmarks, anomaly detection, and agent behavior monitoring.

### Score_08/ (5 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **From Description to Score: Can LLMs Quantify Vulnerabilities?** | Jafarikhah, T. et al. | 2026 |
| **GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning** | Xiang, Z. et al. | 2024 |
| **ToolSafe: Enhancing Tool Invocation Safety via Proactive Step-level Guardrail and Feedback** | Mou, Y. et al. | 2026 |
| **TraceAegis: Securing LLM-Based Agents via Hierarchical and Behavioral Anomaly Detection** | Chen, Y. et al. | 2025 |
| **TRiSM for Agentic AI: A Review of Trust, Risk, and Security Management** | Raza, S. et al. | 2025 |

### Score_07/ (2 papers)

| Paper | Authors | Year |
|-------|---------|------|
| **R-Judge: Benchmarking Safety Risk Awareness for LLM Agents** | Yuan, T. et al. | 2024 |
| **SentinelAgent: Graph-based Anomaly Detection in LLM-based Multi-Agent Systems** | He, R. et al. | 2025 |

### Score_06/ (0 papers — placeholder)

Reserved for: **AI Agents Under Threat: A Survey of Key Security Challenges and Future Pathways** (paywalled — see Manual Downloads).

### Score_04/ (1 paper)

| Paper | Authors | Year |
|-------|---------|------|
| **Adaptive and Explainable AI Agents for Anomaly Detection in Critical IoT Infrastructure** | Sharma, S.; Mehta, V. | 2025 |

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

| Paper | Score | URL |
|-------|-------|-----|
| **Log-To-Leak: Prompt Injection Attacks on Tool-Using LLM Agents via MCP** | 8 | [OpenReview](https://openreview.net/forum?id=UVgbFuXPaO) |
| **Toward Agentic IAM: A Probabilistic Authorization Framework for Least Privilege AI Workflows** | 7 | [ACM DL](https://doi.org/10.1145/3773276.3776564) |
| **AI Agents Under Threat: A Survey of Key Security Challenges and Future Pathways** | 6 | [ACM DL](https://doi.org/10.1145/3716628) |

Once downloaded manually, place them in the correct category/score folder:
- Log-To-Leak → `1_MCP_Security/Score_08/`
- Toward Agentic IAM → `3_Multi_Agent_Trust/Score_07/`
- AI Agents Under Threat → `6_Risk_Scoring/Score_06/`

---

## Hebrew Docs

Hebrew-language reference documents related to the MCP literature review, stored in [Hebrew_Docs/](Hebrew_Docs/).

| File | Description |
|------|-------------|
| `mcp-hebrew.html` | Hebrew summary of MCP concepts and security topics |
| `mcp-hebrew-full.html` | Extended Hebrew document with comprehensive MCP coverage |

---

*Updated 2026-04-15. Added 2 new papers to 1_MCP_Security/Score_08 (MCP-DPT and Formal Security Framework).*
