# MCP Security Literature Scan — 2026-04-20

**Search window:** 2026-02-19 to 2026-04-20
**Run type:** catch-up (2 months)
**Papers found:** 12

---

## Papers

### 1. MCP-DPT: A Defense-Placement Taxonomy and Coverage Analysis for Model Context Protocol Security
- **Authors:** Mehrdad Rostamzadeh, Sidhant Narula, Nahom Birhan, Mohammad Ghasemigol, Daniel Takabi
- **Publication date:** 2026-04-08
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2604.07551
- **PDF:** not downloaded — network restricted (sandbox cannot reach arxiv.org)
- **Summary:** Introduces a defense-placement-oriented security analysis of MCP with a layer-aligned taxonomy that organizes attacks by the architectural component responsible for enforcement. Maps threats across six MCP layers and identifies primary and secondary defense points for defense-in-depth reasoning. Reveals that existing defenses are predominantly tool-centric, with persistent gaps at host orchestration, transport, and supply-chain layers.
- **Relevance to defending MCP servers from malicious agents:** Directly maps where defenses should be placed within MCP server architecture to counter agent-driven attacks, identifying critical unprotected layers that servers must address.
- **Relevance score:** 5

### 2. A Formal Security Framework for MCP-Based AI Agents: Threat Taxonomy, Verification Models, and Defense Mechanisms (MCPShield)
- **Authors:** Nirajan Acharya, Gaurav Kumar Gupta
- **Publication date:** 2026-04-07
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2604.05969
- **PDF:** not downloaded — network restricted
- **Summary:** Presents MCPShield, a comprehensive formal security framework addressing the absence of unified formal security analysis for MCP-based agent ecosystems with 97M+ monthly SDK downloads and 177K+ registered tools. Provides threat taxonomy, formal verification models, and defense mechanisms for systematically characterizing and mitigating threats. Conducted a large-scale empirical study monitoring 177,436 tools across public MCP server repositories between November 2024 and February 2026.
- **Relevance to defending MCP servers from malicious agents:** Provides the first formal verification framework that MCP servers can use to systematically analyze and prove defense properties against agent-driven threats.
- **Relevance score:** 5

### 3. Model Context Protocol Threat Modeling and Analyzing Vulnerabilities to Prompt Injection with Tool Poisoning
- **Authors:** Charoes Huang, Xin Huang, Amin Milani Fard (also authors of paper #6)
- **Publication date:** 2026-03-23
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2603.22489
- **PDF:** not downloaded — network restricted
- **Summary:** Reveals tool poisoning — where malicious instructions are embedded in tool metadata — as the most prevalent and impactful client-side vulnerability against MCP servers. Provides a systematic comparison of how seven major MCP clients validate and defend against tool poisoning attacks. Identifies significant security issues due to insufficient static validation and parameter visibility across all tested clients.
- **Relevance to defending MCP servers from malicious agents:** Directly characterizes how agents can exploit tool metadata to poison MCP servers, and benchmarks existing client-side defenses, informing server-side mitigations.
- **Relevance score:** 5

### 4. ShieldNet: Network-Level Guardrails against Emerging Supply-Chain Injections in Agentic Systems
- **Authors:** Zhuowen Yuan and 7 co-authors
- **Publication date:** 2026-04-06
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2604.04426
- **PDF:** not downloaded — network restricted
- **Summary:** Introduces SC-Inject-Bench, a large-scale benchmark of 10,000+ malicious MCP tools grounded in 25+ attack types derived from MITRE ATT&CK, targeting supply-chain threats in agentic systems. Proposes ShieldNet, a network-level guardrail framework that detects supply-chain attacks by observing real network interactions via MITM proxy. Achieves 0.995 F1 with only 0.8% false positives while substantially outperforming existing MCP scanners and LLM-based guardrails.
- **Relevance to defending MCP servers from malicious agents:** Provides a practical detection framework that MCP server operators can deploy at the network layer to identify malicious tool invocations from compromised agents before they execute.
- **Relevance score:** 5

### 5. ClawGuard: A Runtime Security Framework for Tool-Augmented LLM Agents Against Indirect Prompt Injection
- **Authors:** Wei Zhao and 3 co-authors
- **Publication date:** 2026-04-13
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2604.11790
- **PDF:** not downloaded — network restricted
- **Summary:** Proposes ClawGuard, which automatically derives task-specific access constraints from the user's stated objective prior to any external tool invocation, blocking all three injection pathways without model modification. Evaluated across five state-of-the-art LLMs on AgentDojo, SkillInject, and MCPSafeBench benchmarks. Establishes deterministic tool-call boundary enforcement as an effective defense requiring neither safety-specific fine-tuning nor architectural modification.
- **Relevance to defending MCP servers from malicious agents:** Demonstrates a runtime enforcement approach that can be adapted server-side to validate that incoming agent tool calls align with declared task objectives, blocking injected malicious invocations.
- **Relevance score:** 4

### 6. Are AI-assisted Development Tools Immune to Prompt Injection?
- **Authors:** Charoes Huang, Xin Huang, Amin Milani Fard
- **Publication date:** 2026-03-23
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2603.21642
- **PDF:** not downloaded — network restricted
- **Summary:** First empirical analysis of prompt injection vulnerabilities in real-world MCP client implementations, testing seven widely used MCP clients (Claude Desktop, Claude Code, Cursor, Cline, Continue, Gemini CLI, Langflow). Investigates whether major MCP clients are vulnerable to prompt-injection attacks delivered via tool-poisoning vectors. Fills a gap in security research that had previously focused on LLM prompt injection rather than MCP client behavior.
- **Relevance to defending MCP servers from malicious agents:** Reveals how compromised or vulnerable MCP clients can be weaponized to attack servers via tool-poisoning vectors, informing server-side input validation requirements.
- **Relevance score:** 4

### 7. OpenClaw PRISM: A Zero-Fork, Defense-in-Depth Runtime Security Layer for Tool-Augmented LLM Agents
- **Authors:** Frank Li
- **Publication date:** 2026-03-12
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2603.11853
- **PDF:** not downloaded — network restricted
- **Summary:** Addresses security risks of tool-augmented LLM agents including indirect prompt injection through fetched content, unsafe tool execution, credential leakage, and control file tampering. Distributes enforcement across ten lifecycle hooks spanning message ingress, prompt construction, tool execution, tool-result persistence, outbound messaging, sub-agent spawning, and gateway startup. Uses a hybrid scanning pipeline with fast heuristic scoring escalating to LLM-assisted classification, with session-level risk accumulation and graduated response thresholds.
- **Relevance to defending MCP servers from malicious agents:** The ten-hook lifecycle enforcement model is directly applicable to MCP server-side defense, providing a blueprint for intercepting malicious agent interactions at multiple processing stages.
- **Relevance score:** 4

### 8. ClawWorm: Self-Propagating Attacks Across LLM Agent Ecosystems
- **Authors:** Yihao Zhang, Zeming Wei, Xiaokun Luan, Chengcan Wu, Zhixin Zhang, Jiangrong Wu, Haolin Wu, Huanran Chen, Jun Sun, Meng Sun
- **Publication date:** 2026-03-16
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2603.15727
- **PDF:** not downloaded — network restricted
- **Summary:** Demonstrates the first self-replicating worm attack against a production-scale agent framework (OpenClaw, 40K+ active instances), achieving fully autonomous infection from a single message. The worm hijacks core configuration for persistent presence across session restarts, executes arbitrary payloads on reboot, and propagates to every newly encountered peer without further attacker intervention. Argues the vulnerabilities are structural consequences of architectural patterns shared by a growing class of autonomous agent ecosystems.
- **Relevance to defending MCP servers from malicious agents:** Demonstrates how agent-to-agent worm propagation can compromise MCP-like tool-serving infrastructure; servers must defend against infected agents carrying worm payloads.
- **Relevance score:** 4

### 9. AttriGuard: Defeating Indirect Prompt Injection in LLM Agents via Causal Attribution of Tool Invocations
- **Authors:** Yu He, Haozhe Zhu, Yiming Li, Shuo Shao, Hongwei Yao, Zhihao Liu, Zhan Qin
- **Publication date:** 2026-03-11
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2603.10749
- **PDF:** not downloaded — network restricted
- **Summary:** Introduces action-level causal attribution to distinguish tool calls driven by user intent from those causally driven by untrusted observations (indirect prompt injection). Proposes AttriGuard, a runtime defense using parallel counterfactual tests that verify the necessity of each proposed tool call by re-executing the agent under a control-attenuated view. Achieves 0% attack success rate under static attacks with negligible utility loss across four LLMs and two benchmarks.
- **Relevance to defending MCP servers from malicious agents:** The causal attribution approach could be deployed server-side to verify whether incoming tool calls originate from legitimate user intent vs. injected instructions, enabling servers to reject suspicious invocations.
- **Relevance score:** 4

### 10. AgentSentry: Mitigating Indirect Prompt Injection in LLM Agents via Temporal Causal Diagnostics and Context Purification
- **Authors:** Tian Zhang, Yiwei Xu, Juan Wang, Keyan Guo, Xiaoyang Xu, Bowen Xiao, Quanlong Guan, Jinlin Fan, Jiawei Liu, Zhiquan Liu, Hongxin Hu
- **Publication date:** 2026-02-26
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2602.22724
- **PDF:** not downloaded — network restricted
- **Summary:** Proposes the first inference-time defense to model multi-turn indirect prompt injection as a temporal causal takeover of tool-augmented LLM agents. Localizes takeover points via controlled counterfactual re-executions at tool-return boundaries, then enables safe continuation through causally guided context purification. Removes attack-induced deviations while preserving task-relevant evidence for legitimate tool-use workflows.
- **Relevance to defending MCP servers from malicious agents:** Provides a detection mechanism for identifying when agent requests have been hijacked by injected instructions, allowing servers to gate suspicious multi-turn tool-call sequences.
- **Relevance score:** 3

### 11. Memory Poisoning and Secure Multi-Agent Systems
- **Authors:** Vicenç Torra, Maria Bras-Amorós
- **Publication date:** 2026-03-20
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2603.20357
- **PDF:** not downloaded — network restricted
- **Summary:** Addresses memory poisoning attacks targeting semantic, episodic, and short-term memory in agentic AI and multi-agent systems. Reviews existing security solutions and proposes adapted solutions based on cryptography and local inference with private knowledge retrieval. Emphasizes risks from inter-agent interactions that can cause memory poisoning — risks that are not well studied and difficult to formalize.
- **Relevance to defending MCP servers from malicious agents:** Memory poisoning through agent interactions could be used to corrupt MCP server-side state or cached context, enabling persistent manipulation of server behavior across sessions.
- **Relevance score:** 3

### 12. From Component Manipulation to System Compromise: Understanding and Detecting Malicious MCP Servers
- **Authors:** Yiheng Huang, Zhijia Zhao, Bihuan Chen, Susheng Wu, Zhuotong Zhou, Yiheng Cao, Xin Hu, Xin Peng
- **Publication date:** 2026-04-02
- **Source / venue:** arXiv (cs.CR)
- **Link:** https://arxiv.org/abs/2604.01905
- **PDF:** not downloaded — network restricted
- **Summary:** Takes a component-centric perspective on MCP security and builds the first component-centric PoC dataset of 114 malicious MCP servers where attacks are achieved as manipulation over MCP components and their compositions. Addresses limitations of effect-based attack classification that obscure multi-component attack chains. Proposes detection methods for previously unknown malicious behaviors in MCP servers.
- **Relevance to defending MCP servers from malicious agents:** **Note: This paper is about the INVERSE direction** (malicious servers attacking agents, not agents attacking servers). However, the component-centric attack taxonomy and PoC dataset provide useful understanding of MCP attack surfaces that also apply to server defense.
- **Relevance score:** 2

---

## Key Takeaways

- **MCP defense taxonomy gaps identified:** MCP-DPT (paper #1) reveals that existing defenses are heavily concentrated at the tool layer, with critical gaps at host orchestration, transport, and supply-chain layers. Server operators should prioritize multi-layer defense-in-depth strategies rather than tool-only validation.

- **Tool poisoning confirmed as top threat:** Multiple papers (#3, #6) converge on tool poisoning — malicious instructions embedded in tool metadata — as the most prevalent and impactful attack vector against MCP servers. All seven tested MCP clients showed insufficient static validation.

- **Formal verification now available:** MCPShield (#2) provides the first formal security framework with verification models, moving MCP security from ad hoc mitigations toward provable defense properties — a significant maturation of the field.

- **Network-level detection proves highly effective:** ShieldNet (#4) demonstrates that monitoring real network interactions via MITM proxy achieves 0.995 F1 for detecting supply-chain attacks, substantially outperforming static MCP scanners. This suggests MCP servers should deploy network-level guardrails alongside application-level defenses.

- **Causal attribution emerges as a defense paradigm:** Both AttriGuard (#9) and AgentSentry (#10) use counterfactual re-execution to distinguish legitimate tool calls from injection-induced ones. AttriGuard achieves 0% attack success rate, suggesting this approach could be adapted for server-side request validation.

- **Self-propagating worm attacks demonstrated at scale:** ClawWorm (#8) achieves fully autonomous infection across 40K+ agent instances from a single message, showing that MCP servers face not just individual malicious agents but potentially entire networks of compromised agents carrying worm payloads.

- **Runtime enforcement without model changes is viable:** ClawGuard (#5) and PRISM (#7) both demonstrate effective defense through deterministic runtime enforcement hooks, with no need for model fine-tuning — making them practical for immediate deployment in MCP server environments.

- **Research volume surge:** The 12 directly relevant papers in just 2 months represents a significant acceleration in MCP security research, reflecting both the rapid growth of MCP adoption (97M+ monthly SDK downloads) and the urgency of the threat landscape.
