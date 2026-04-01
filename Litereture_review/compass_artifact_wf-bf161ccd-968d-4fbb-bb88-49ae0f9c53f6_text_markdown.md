# Research Papers on Attacks Against MCP Servers and the MCP Ecosystem

**The security of Anthropic's Model Context Protocol has become a fast-growing research area, with over 25 academic papers published since March 2025.** MCP — the open standard for connecting AI agents to external tools and data sources — introduces novel attack surfaces that researchers have systematically catalogued and exploited. The papers below represent the 15 most relevant works that specifically analyze attacks on MCP servers, tool misuse, prompt injection through MCP tool calls, privilege escalation, trust boundary violations, and threat modeling within the MCP architecture. Most are arXiv preprints given the protocol's recency, though several have been accepted at peer-reviewed venues including ACM TOSEM, EMNLP, and ACM MobiCom.

---

## 1. Model Context Protocol (MCP): Landscape, security threats, and future research directions

- **Authors:** Xinyi Hou, Yanjie Zhao, Shenao Wang, Haoyu Wang
- **Venue:** ACM Transactions on Software Engineering and Methodology (TOSEM), 2026; arXiv preprint March 2025
- **Year:** 2025 (arXiv), accepted December 2025
- **URL:** https://arxiv.org/abs/2503.23278 | https://doi.org/10.1145/3796519
- **Summary:** The foundational academic study of MCP security. Defines the full MCP server lifecycle across **4 phases and 16 activities**, then constructs a comprehensive threat taxonomy covering 16 distinct threat scenarios organized by four attacker types: malicious developers, external attackers, malicious users, and inherent security flaws. Includes real-world case studies of namespace typosquatting, tool impersonation, and preference manipulation attacks. This is the most cited MCP security paper and the only one published in a top-tier software engineering journal.

---

## 2. MCP Safety Audit: LLMs with the Model Context Protocol allow major security exploits

- **Authors:** Brandon Radosevich, John Halloran
- **Venue:** arXiv preprint (cs.CR)
- **Year:** 2025 (submitted April 2, 2025)
- **URL:** https://arxiv.org/abs/2504.03767
- **Summary:** One of the earliest empirical security audits of MCP. Demonstrates that Claude 3.7 Sonnet and Llama-3.3-70B can be coerced into using MCP tools for **malicious code execution, remote access control, and credential theft**. Introduces the RADE (Retrieval-Agent DEception) attack, a novel multi-MCP-server attack where corrupted public data in vector databases triggers agent exploitation chains. Also releases McpSafetyScanner, the first automated tool for auditing MCP server security.

---

## 3. Beyond the Protocol: Unveiling attack vectors in the Model Context Protocol ecosystem

- **Authors:** Hao Song, Yiming Shen, Wenxuan Luo, Leixin Guo, Ting Chen, Jiashui Wang, Beibei Li, Xiaosong Zhang, Jiachi Chen
- **Venue:** arXiv preprint (cs.CR, cs.SE)
- **Year:** 2025 (submitted May 31, 2025)
- **URL:** https://arxiv.org/abs/2506.02040
- **Summary:** The first end-to-end empirical evaluation of the MCP attack lifecycle. Identifies four attack categories — **Tool Poisoning, Puppet Attacks, Rug Pull Attacks, and Exploitation via Malicious External Resources** — and demonstrates the full upload→download→attack pipeline. Successfully uploads malicious servers to three major MCP aggregation platforms (Smithery.ai, MCP.so, Glama) without detection. A user study with 20 participants confirms that users struggle to distinguish malicious servers from legitimate ones. Attacks trigger harmful local actions including private file access and digital asset transfers across five leading LLMs.

---

## 4. When MCP servers attack: Taxonomy, feasibility, and mitigation

- **Authors:** Weibo Zhao, Jiahao Liu, Bonan Ruan, Shaofei Li, Zhenkai Liang
- **Venue:** arXiv preprint (cs.CR)
- **Year:** 2025 (submitted September 29, 2025)
- **URL:** https://arxiv.org/abs/2509.24272
- **Summary:** First systematic study treating MCP servers themselves as active threat actors. Decomposes MCP servers into six core components and proposes a taxonomy of **12 attack categories** with proof-of-concept implementations for each. Tests against Claude Desktop, Cursor, and fast-agent with multiple backbone LLMs (GPT-4o, o3, Claude Sonnet 4, Gemini-2.5-pro). Six attack categories achieved **100% success rate** across all configurations. Demonstrates that state-of-the-art scanners (mcp-scan, AI-Infra-Guard) detect only a fraction of generated malicious servers, and that attackers can produce large volumes of malicious servers at virtually zero cost.

---

## 5. MPMA: Preference Manipulation Attack against Model Context Protocol

- **Authors:** Zihan Wang, Hongwei Li, Rui Zhang, Yu Liu, Wenbo Jiang, Wenshu Fan, Qingchuan Zhao, Guowen Xu
- **Venue:** arXiv preprint (cs.CR, cs.CL)
- **Year:** 2025 (submitted May 16, 2025)
- **URL:** https://arxiv.org/abs/2505.11154
- **Summary:** Introduces the MCP Preference Manipulation Attack (MPMA), where an attacker deploys a customized MCP server that manipulates LLMs into preferentially selecting it over competing servers. Proposes two variants: Direct Preference Manipulation Attack (DPMA), which achieves **100% attack success rate** using manipulative language, and Genetically Adapted Preference Manipulation Attack (GAPMA), a stealthier approach using genetic algorithms to evolve adversarial descriptions. Evaluated across 8 MCP servers and 5 mainstream LLMs including DeepSeek-V3, Claude-3.7-Sonnet, and GPT-4o.

---

## 6. Systematic Analysis of MCP Security

- **Authors:** Yongjian Guo, Puzhuo Liu, Wanlun Ma, Zehang Deng, Xiaogang Zhu, Peng Di, Xi Xiao, Sheng Wen
- **Venue:** arXiv preprint (cs.CR)
- **Year:** 2025 (submitted August 18, 2025)
- **URL:** https://arxiv.org/abs/2508.12538
- **Summary:** Presents MCPLIB, the first unified attack simulation framework for MCP, cataloguing **31 distinct attack methods** under four classifications: direct tool injection, indirect tool injection, malicious user attacks, and LLM-inherent vulnerability exploitation. Provides the first quantitative analysis of MCP attack efficacy with root cause analysis. Key findings include that agents blindly trust tool descriptions, chain attacks exploit shared context windows, and LLMs fundamentally cannot distinguish external data from executable instructions — making tool return attacks the most effective vector.

---

## 7. MCPTox: A benchmark for Tool Poisoning Attack on real-world MCP servers

- **Authors:** Zhiqiang Wang, Yichao Gao, Yanting Wang, Suyuan Liu, Haifeng Sun, Haoran Cheng, Guanquan Shi, Haohua Du, Xiangyang Li
- **Venue:** arXiv preprint
- **Year:** 2025 (submitted August 19, 2025)
- **URL:** https://arxiv.org/abs/2508.14925
- **Summary:** The first benchmark to systematically evaluate agent robustness against Tool Poisoning in realistic MCP settings. Built on **45 live, real-world MCP servers with 353 authentic tools**, it generates 1,312 malicious test cases via three attack templates covering 10 risk categories. Evaluation across 20 LLM agents reveals alarming vulnerability: o1-mini reaches **72.8% attack success rate**, and even the most defensive model (Claude-3.7-Sonnet) exhibits a refusal rate below 3%. More capable models are paradoxically more susceptible to tool poisoning.

---

## 8. MCP-ITP: An automated framework for Implicit Tool Poisoning in MCP

- **Authors:** Ruiqi Li, Zhiqiang Wang, Yunhao Yao, Xiang-Yang Li
- **Venue:** arXiv preprint
- **Year:** 2026 (submitted January 12, 2026)
- **URL:** https://arxiv.org/abs/2601.07395
- **Summary:** Introduces a stealthy attack variant called implicit tool poisoning, where the poisoned tool is **never directly invoked** — instead, its metadata induces the agent to call legitimate high-privilege tools for malicious purposes. Formulates poisoned tool generation as a black-box optimization problem with iterative feedback from evaluation and detection LLMs. Achieves up to **84.2% attack success rate** while suppressing the Malicious Tool Detection Rate to as low as 0.3% across 12 LLM agents, making it nearly invisible to existing defenses.

---

## 9. Trivial Trojans: How minimal MCP servers enable cross-tool exfiltration of sensitive data

- **Authors:** Nicola Croce, Tobin South
- **Venue:** arXiv preprint
- **Year:** 2025 (submitted July 26, 2025)
- **URL:** https://arxiv.org/abs/2507.19880
- **Summary:** Demonstrates that even unsophisticated threat actors can exploit MCP's trust model for cross-server data exfiltration using only **basic Python scripting and free webhook services**. A malicious weather MCP server — built by trivially modifying Anthropic's official example server code — successfully steals financial data from a legitimate banking server connected to the same agent. Undergraduate-level programming suffices for high-impact data theft across MCP trust boundaries, highlighting the protocol's fundamental lack of inter-server isolation.

---

## 10. IntentMiner: Intent Inversion Attack via tool call analysis in the Model Context Protocol

- **Authors:** Yunhao Yao, Zhiqiang Wang, Haoran Cheng, Yihang Cheng, Haohua Du, Xiang-Yang Li
- **Venue:** arXiv preprint
- **Year:** 2025 (submitted December 16, 2025)
- **URL:** https://arxiv.org/abs/2512.14166
- **Summary:** Uncovers a novel privacy attack vector: the Intent Inversion Attack. Semi-honest third-party MCP servers can **accurately reconstruct users' underlying intents** by analyzing only authorized metadata — function signatures, arguments, and receipts — without direct access to raw user queries. Introduces IntentMiner, a framework using hierarchical semantic parsing that achieves over 85% semantic alignment with original queries on the ToolACE benchmark. Demonstrates that even properly functioning MCP servers can compromise user privacy through metadata analysis alone.

---

## 11. Breaking the Protocol: Security analysis of the Model Context Protocol specification and prompt injection vulnerabilities

- **Authors:** Narek Maloyan, Dmitry Namiot
- **Venue:** arXiv preprint
- **Year:** 2026 (submitted January 24, 2026)
- **URL:** https://arxiv.org/abs/2601.17549
- **Summary:** The first formal security analysis targeting MCP's specification itself rather than its implementations. Identifies three protocol-level vulnerabilities: absence of capability attestation, bidirectional sampling without origin authentication, and implicit trust propagation in multi-server configurations. The ProtoAmp/MCPBench framework tests **847 attack scenarios** and demonstrates that MCP amplifies attack success rates by **23–41%** compared to non-MCP tool integrations. Proposes AttestMCP, a backward-compatible extension with cryptographic capability attestation that reduces attack success from 52.8% to 12.4%.

---

## 12. MCIP: Protecting MCP safety via Model Contextual Integrity Protocol

- **Authors:** Huihao Jing, Haoran Li, Wenbin Hu, Qi Hu, Heli Xu, Tianshu Chu, Peizhao Hu, Yangqiu Song
- **Venue:** EMNLP 2025 (Empirical Methods in Natural Language Processing); arXiv preprint
- **Year:** 2025 (November 2025)
- **URL:** https://arxiv.org/abs/2505.14590 | https://aclanthology.org/2025.emnlp-main.62.pdf
- **Summary:** Proposes the Model Contextual Integrity Protocol (MCIP), developing a fine-grained taxonomy of unsafe MCP behaviors across **5 dimensions** (Stage, Source, Scope, Type, MAESTRO alignment). Introduces MCIP-Bench, a benchmark for evaluating LLMs' ability to identify safety risks within MCP interactions, and a "Guardian" safety-aware model. Published at EMNLP 2025, making it one of the few peer-reviewed MCP security papers at a top-tier NLP venue. Finds that existing LLMs have weak safety awareness in MCP scenarios.

---

## 13. Model Context Protocol at First Glance: Studying the security and maintainability of MCP servers

- **Authors:** Mohammed Mehedi Hasan, Hao Li, Emad Fallahzadeh, Gopi Krishnan Rajbahadur, Bram Adams, Ahmed E. Hassan
- **Venue:** arXiv preprint (submitted to ACM TOSEM)
- **Year:** 2025 (submitted June 16, 2025)
- **URL:** https://arxiv.org/abs/2506.13538
- **Summary:** The first large-scale empirical study of real-world MCP server security, analyzing **1,899 open-source MCP servers** using a hybrid analysis pipeline combining SonarQube static analysis with MCP-specific scanning tools. Identifies 8 distinct vulnerability types, finding that 7.2% of servers contain general vulnerabilities, **5.5% exhibit MCP-specific tool poisoning**, and credential exposure affects 3.6% of servers. Also reports that 66% of servers have code smells and 14.4% contain bug patterns, painting a concerning picture of ecosystem-wide code quality.

---

## 14. MCP Threat Modeling and analyzing vulnerabilities to prompt injection with Tool Poisoning

- **Authors:** (Multiple authors)
- **Venue:** arXiv preprint
- **Year:** 2026 (March 2026)
- **URL:** https://arxiv.org/abs/2603.22489
- **Summary:** The most comprehensive client-side security analysis, applying **STRIDE and DREAD** threat modeling across 5 MCP components to identify 57 distinct threats. Empirically tests 7 major MCP clients — Claude Desktop, Claude Code, Cursor, Cline, Continue, Gemini CLI, and Langflow — against 4 tool poisoning attack vectors. Results reveal dramatic variance: attack success rates range from **0% (Claude Desktop) to 100% (Cursor)**. Tool poisoning scores Critical at 46.5/50 on the DREAD scale. Proposes a multi-layered defense strategy encompassing static metadata analysis, decision path tracking, and behavioral anomaly detection.

---

## 15. Secure Model Context Protocol for large language models with dual signatures

- **Authors:** Shiqiang Li, Xinghai Wei, Jie Yuan, Xingwu Wang, Keji Miao
- **Venue:** ACM MobiCom '25 (31st Annual International Conference on Mobile Computing and Networking)
- **Year:** 2025 (published November 4, 2025)
- **URL:** https://doi.org/10.1145/3737897.3767287
- **Summary:** Proposes a dual-signature verification framework to protect against MCP server tampering and tool-based prompt injection attacks. A tool can only be invoked after verifying cryptographic signatures from both a trusted third-party platform and the original developer, preventing unauthorized tool modifications (rug pulls) and supply chain attacks. Published at ACM MobiCom, making it one of the rare peer-reviewed MCP security papers at a premier systems conference. Introduces minimal overhead while maintaining backward compatibility with existing MCP servers.

---

## The emerging landscape of MCP attack research

Several patterns emerge from this body of work. **Tool poisoning is the dominant attack vector**, appearing in nearly every paper — the ability to embed adversarial instructions in tool descriptions exploits a fundamental design tension between rich tool metadata and LLM trust in that metadata. Cross-server attacks represent the second major theme: MCP's architecture allows multiple servers to share an agent's context window, enabling malicious servers to access data from or manipulate actions of trusted servers (papers #3, #4, #9). A third research thread focuses on the gap between protocol specification and security guarantees — MCP lacks built-in capability attestation, mutual authentication, and inter-server isolation (paper #11).

The field is evolving rapidly, with benchmarks (#7, #12, #14) enabling standardized evaluation, defense frameworks emerging (#8, #15), and attack sophistication increasing from overt tool poisoning to implicit attacks where the malicious tool is never even invoked (#8). Notably, the research consistently finds that **more capable LLMs are often more vulnerable** to MCP attacks, as their stronger instruction-following abilities make them more susceptible to adversarial tool descriptions. Three additional papers worth monitoring include MCPSecBench (arXiv:2508.13220), which formalizes 17 distinct attack types with over 85% success across platforms; MCP Safety Training (arXiv:2505.23634), which proposes preference alignment to teach LLMs to refuse MCP exploits; and MindGuard (arXiv:2508.20412), which achieves 94–99% precision in detecting poisoned tool invocations using attention-based decision graphs.