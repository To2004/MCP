# MCP Security Literature Review — Paper Library Guide

This folder contains **62 cataloged papers** (+ 14 unmatched extras) organized for the MCP Security thesis project, which builds a **dynamic 1-10 risk scoring system** for evaluating AI agent access to MCP servers.

Papers are sorted into **category folders**, each containing **score subfolders** (Score_10 = most relevant, Score_04 = least). The **Top_20/** folder contains copies of the 20 most important papers in recommended reading order.

---

## Quick Navigation

| Folder | Papers | Description |
|--------|--------|-------------|
| [Top_20/](#top-20-recommended-reading-order) | 19 | The most important papers, ranked by reading order |
| [1_MCP_Security/](#1-mcp-security-19-papers) | 19 | MCP-specific security frameworks, attacks, and defenses |
| [2_MCP_Protocol/](#2-mcp-protocol-5-papers) | 5 | MCP architecture, specifications, and ecosystem studies |
| [3_Multi_Agent_Trust/](#3-multi-agent-trust--access-control-7-papers) | 7 | Trust frameworks, access control, and authorization |
| [4_Prompt_Injection/](#4-prompt-injection--tool-poisoning-14-papers) | 14 | Prompt injection attacks, tool poisoning, and defenses |
| [5_LLM_Guardrails/](#5-llm-guardrails-2-papers) | 2 | LLM guardrail and safety rail systems |
| [6_Risk_Scoring/](#6-risk-scoring--anomaly-detection-8-papers) | 8 | Risk scoring, anomaly detection, and safety benchmarks |
| [7_Not_Academic/](#7-not-academic-4-entries) | 4 | MCP specification web pages (not downloadable PDFs) |
| [7_Unmatched/](#7-unmatched-14-extras) | 22 | Pre-existing PDFs not yet matched to the catalog |
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

## 1. MCP Security (19 papers)

Direct MCP security research: frameworks, attacks, defenses, benchmarks, and auditing tools.

### Score_10/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 49 | **MCPShield: A Security Cognition Layer for Adaptive Trust Calibration in MCP Agents** | Zhou, Z. et al. | 2026 |

### Score_09/ (8 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 51 | **Breaking the Protocol: Security Analysis of the MCP Specification and Prompt Injection Vulnerabilities** | Maloyan, N.; Namiot, D. | 2026 |
| 46 | **MCP-Guard: A Multi-Stage Defense-in-Depth Framework for Securing MCP in Agentic AI** | Xing, W. et al. | 2025 |
| 22 | **MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers** | Wang, H. et al. | 2025 |
| 26 | **Mind Your Server: A Systematic Study of Parasitic Toolchain Attacks on the MCP Ecosystem** | Zhao, Y. et al. | 2025 |
| 47 | **MindGuard: Intrinsic Decision Inspection for Securing LLM Agents Against Metadata Poisoning** | Wang, Z. et al. | 2025 |
| 28 | **Securing AI Agent Execution** | Buhler, E. et al. | 2025 |
| 20 | **Toward Understanding Security Issues in the Model Context Protocol Ecosystem** | Li, J.; Gao, Y. | 2025 |
| 25 | **When MCP Servers Attack: Taxonomy, Feasibility, and Mitigation** | Zhao, C. et al. | 2025 |

### Score_08/ (4 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 45 | **Beyond the Protocol: Unveiling Attack Vectors in the MCP Ecosystem** | Song, Q. et al. | 2025 |
| 41 | **MCP Safety Audit: LLMs with the MCP Allow Major Security Exploits** | Radosevich, C.; Halloran, J. | 2025 |
| 50 | **MCP-ITP: An Automated Framework for Implicit Tool Poisoning in MCP** | Li, Y. et al. | 2026 |
| 21 | **MCPSecBench: A Systematic Security Benchmark and Playground for Testing MCP** | Yang, X. et al. | 2025 |

### Score_07/ (6 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 42 | **Enterprise-Grade Security for the MCP: Frameworks and Mitigation Strategies** | Narajala, S.; Habler, E. | 2025 |
| 23 | **ETDI: Mitigating Tool Squatting and Rug Pull Attacks in MCP using OAuth-Enhanced Tool Definitions** | Bhatt, D. | 2025 |
| 44 | **MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol** | Jing, Y. et al. | 2025 |
| 43 | **MCP Guardian: A Security-First Layer for Safeguarding MCP-Based AI System** | Kumar, S. et al. | 2025 |
| 48 | **MCP-SafetyBench: A Benchmark for Safety Evaluation of LLMs with Real-World MCP Servers** | Zong, Y. et al. | 2025 |
| 24 | **SMCP: Secure Model Context Protocol** | Hou, Y. et al. | 2026 |

---

## 2. MCP Protocol (5 papers)

MCP architecture, specifications, ecosystem measurements, and protocol-level studies.

### Score_10/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 16 | **Model Context Protocol (MCP): Landscape, Security Threats, and Future Research Directions** | Hou, Y. et al. | 2025 |

### Score_08/ (2 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 17 | **Model Context Protocol (MCP) at First Glance: Studying the Security and Maintainability of MCP Servers** | Hasan, M. et al. | 2025 |
| 19 | **We Urgently Need Privilege Management in MCP: A Measurement of API Usage in MCP Ecosystems** | Li, Y. et al. | 2025 |

### Score_06/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 18 | **A Measurement Study of Model Context Protocol Ecosystem** | Guo, T. et al. | 2025 |

### Score_05/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 52 | **Systems Security Foundations for Agentic Computing** | Christodorescu, M. et al. | 2025 |

---

## 3. Multi-Agent Trust & Access Control (7 papers)

Trust frameworks, authorization, access control, and trustworthiness benchmarks for LLM agents.

### Score_09/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 13 | **Progent: Programmable Privilege Control for LLM Agents** | Shi, Z. et al. | 2025 |

### Score_08/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 14 | **Towards Automating Data Access Permissions in AI Agents** | Wu, X. et al. | 2025 |

### Score_07/ (2 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 54 | **A Vision for Access Control in LLM-based Agent Systems** | Li, Y. et al. | 2025 |
| 55 | **The Trust Paradox in LLM-Based Multi-Agent Systems** | Xu, Y. et al. | 2025 |

### Score_05/ (2 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 9 | **DecodingTrust: A Comprehensive Assessment of Trustworthiness in GPT Models** | Wang, B. et al. | 2023 |
| 8 | **TrustLLM: Trustworthiness in Large Language Models** | Huang, Y. et al. | 2024 |

### Score_04/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 10 | **Towards Trustworthy AI: A Review of Ethical and Robust Large Language Models** | Ferdaus, M. et al. | 2024 |

---

## 4. Prompt Injection & Tool Poisoning (14 papers)

Prompt injection attacks, tool manipulation, indirect injection, and related defenses.

### Score_09/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 6 | **From Prompt Injections to Protocol Exploits: Threats in LLM-Powered AI Agents Workflows** | Ferrag, M. et al. | 2025 |

### Score_08/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 5 | **Prompt Injection Detection and Mitigation via AI Multi-Agent NLP Frameworks** | Gosmar, D. et al. | 2025 |

### Score_07/ (5 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 31 | **Imprompter: Tricking LLM Agents into Improper Tool Use** | Fu, Z. et al. | 2024 |
| 30 | **InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated LLM Agents** | Zhan, Q. et al. | 2024 |
| 32 | **MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents** | Zhu, Y. et al. | 2025 |
| 56 | **Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection** | Greshake, K. et al. | 2023 |
| 57 | **Prompt Injection Attack to Tool Selection in LLM Agents (ToolHijacker)** | Shi, Z. et al. | 2025 |

### Score_06/ (4 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 29 | **AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents** | Debenedetti, E. et al. | 2024 |
| 37 | **Exploiting Web Search Tools of AI Agents for Data Exfiltration** | Rall, E. et al. | 2025 |
| 35 | **Prompt Injection Attack to Tool Selection in LLM Agents** | Shi, Z. et al. | 2025 |
| 33 | **Towards Verifiably Safe Tool Use for LLM Agents** | Doshi, R. et al. | 2026 |

### Score_05/ (3 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 36 | **Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents** | Zhan, Q. et al. | 2025 |
| 7 | **Defense Against Prompt Injection Attack by Leveraging Attack Techniques** | Chen, Y. et al. | 2025 |
| 34 | **The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection** | Jia, Y. et al. | 2025 |

---

## 5. LLM Guardrails (2 papers)

Guardrail systems and safety rails for LLM applications.

### Score_07/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 59 | **LlamaFirewall: An Open Source Guardrail System for Building Secure AI Agents** | Meta | 2025 |

### Score_05/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 58 | **NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails** | Rebedea, T. et al. | 2023 |

---

## 6. Risk Scoring & Anomaly Detection (8 papers)

Risk scoring methodologies, safety benchmarks, anomaly detection, and agent behavior monitoring.

### Score_08/ (5 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 3 | **From Description to Score: Can LLMs Quantify Vulnerabilities?** | Jafarikhah, T. et al. | 2026 |
| 60 | **GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning** | Xiang, Z. et al. | 2024 |
| 62 | **ToolSafe: Enhancing Tool Invocation Safety via Proactive Step-level Guardrail and Feedback** | Mou, Y. et al. | 2026 |
| 61 | **TraceAegis: Securing LLM-Based Agents via Hierarchical and Behavioral Anomaly Detection** | Chen, Y. et al. | 2025 |
| 1 | **TRiSM for Agentic AI: A Review of Trust, Risk, and Security Management in LLM-based Agentic Multi-Agent Systems** | Raza, S. et al. | 2025 |

### Score_07/ (2 papers)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 2 | **R-Judge: Benchmarking Safety Risk Awareness for LLM Agents** | Yuan, T. et al. | 2024 |
| 11 | **SentinelAgent: Graph-based Anomaly Detection in LLM-based Multi-Agent Systems** | He, R. et al. | 2025 |

### Score_04/ (1 paper)

| ID | Paper | Authors | Year |
|----|-------|---------|------|
| 12 | **Adaptive and Explainable AI Agents for Anomaly Detection in Critical IoT Infrastructure** | Sharma, S.; Mehta, V. | 2025 |

---

## 7. Not Academic (4 entries)

These are MCP specification web pages, not downloadable academic papers. Saved as `.txt` placeholders with URLs.

| ID | Entry | URL |
|----|-------|-----|
| 38 | Model Context Protocol Specification | https://modelcontextprotocol.io/specification/2025-11-25 |
| 39 | MCP Authorization Specification | https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization |
| 40 | Security Best Practices | https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices |
| 53 | Model Context Protocol Specification (v2025-11-25) | https://modelcontextprotocol.io/specification/2025-11-25 |

---

## 7. Unmatched (14 extras)

These pre-existing PDFs were not matched to any of the 62 cataloged papers. They have been added to the Excel as IDs 63-76 with placeholder data. **You should review these and fill in proper titles, categories, and relevance scores.**

| New ID | Filename | arXiv ID |
|--------|----------|----------|
| 63 | 1286748.pdf | — |
| 64 | 2025.emnlp-main.62.pdf | — |
| 65 | 2504.21030v1.pdf | 2504.21030 |
| 66 | 2505.02279v2.pdf | 2505.02279 |
| 67 | 2509.22814v1.pdf | 2509.22814 |
| 68 | 2511.20920v1.pdf | 2511.20920 |
| 69 | 2512.06556v1.pdf | 2512.06556 |
| 70 | 2602.11327v1.pdf | 2602.11327 |
| 71 | 3796519.pdf | — |
| 72 | A_Comprehensive_Security_Framework_for_the_Model_Context_Protocol_MCP_in_Multi-Agent_AI_Systems.pdf | — |
| 73 | A_Systematic_Security_Analysis_of_Model_Context_Protocol_Vulnerabilities_Exploits_and_Mitigations.pdf | — |
| 74 | IJAIBDCMS-V5I1P118.pdf | — |
| 75 | Paper_1_(2025.7.12)_A_Secure_Accountability_Framework_for_Multi-Modal_Agent..._JCSTS.pdf | — |
| 76 | preprints202504.0245.v1.pdf | — |

---

## Papers Requiring Manual Download

These 3 papers returned HTTP 403 (access denied / paywall). You may need institutional access or to find them through Google Scholar.

| ID | Paper | Score | URL |
|----|-------|-------|-----|
| 27 | **Log-To-Leak: Prompt Injection Attacks on Tool-Using LLM Agents via MCP** | 8 | [OpenReview](https://openreview.net/forum?id=UVgbFuXPaO) |
| 15 | **Toward Agentic IAM: A Probabilistic Authorization Framework for Least Privilege AI Workflows** | 7 | [ACM DL](https://doi.org/10.1145/3773276.3776564) |
| 4 | **AI Agents Under Threat: A Survey of Key Security Challenges and Future Pathways** | 6 | [ACM DL](https://doi.org/10.1145/3716628) |

Once downloaded manually, place them in the correct category/score folder:
- ID 27 -> `1_MCP_Security/Score_08/`
- ID 15 -> `3_Multi_Agent_Trust/Score_07/`
- ID 4 -> `6_Risk_Scoring/Score_06/`

---

## Hebrew Docs

Hebrew-language reference documents related to the MCP literature review, stored in [Hebrew_Docs/](Hebrew_Docs/).

| File | Description |
|------|-------------|
| `mcp-hebrew.html` | Hebrew summary of MCP concepts and security topics |
| `mcp-hebrew-full.html` | Extended Hebrew document with comprehensive MCP coverage |

---

*Generated on 2026-03-27 by `organize_papers.py`. Updated 2026-03-29.*
