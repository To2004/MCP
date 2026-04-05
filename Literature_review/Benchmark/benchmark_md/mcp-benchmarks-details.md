# MCP Client→Server Benchmark Details

## 1. MSB — MCP Security Bench (Zhang et al., Oct 2025)

- **arXiv**: 2510.15994
- **Scale**: 2,000 attack cases, 12 attack types, 10 domains, 65 tasks, 400+ tools (304 benign + malicious), 25 MCP servers
- **Models tested**: 9 LLM agents
- **Attack taxonomy** (3 MCP workflow stages):
  - Task Planning: Name Collision, Preference Manipulation, Prompt Injection in tool descriptions
  - Tool Invocation: Out-of-Scope Parameter, Tool Transfer
  - Response Handling: User Impersonation, False Error Escalation, Retrieval Injection
  - 7 mixed/combined variants
- **Client→Server**: HIGH. Out-of-Scope Parameter (74.03% ASR — highest) sends unauthorized params to server tools. User Impersonation (50.72%) causes harmful follow-up requests to servers. False Error (43.42%) forces escalation to privileged server tools.
- **Key metric**: NRP (Net Resilient Performance) = PUA × (1 - ASR)
- **Key finding**: Average ASR 40.71%. Inverse scaling: stronger models more vulnerable.

## 2. MCPSecBench (Yang et al., Aug 2025, v3 Feb 2026)

- **arXiv**: 2508.13220 | **GitHub**: AIS2Lab/MCPSecBench
- **Scale**: 17 attack types across 4 attack surfaces (User, Client, Transport, Server). Tested on Claude Desktop, OpenAI GPT-4.1, Cursor v2.3.29. Each attack tested 15× per model.
- **Client→Server attacks**:
  - Sandbox Escape: client requests exploit server command injection to escape Docker
  - Command Injection: malicious client input exploits server execution methods
  - Confused AI / Tool Misuse: client tricked into invoking server tools harmfully
  - DNS Rebinding: transport-layer unauthorized client access to internal servers
  - CVE-2025-6514: real vuln in mcp-remote enabling arbitrary OS command execution
- **Defenses tested**: MCIP-Guardian, Firewalled-Agentic-Networks (FAN)
- **Key finding**: 85%+ attacks compromised ≥1 platform. Defenses <30% effective.

## 3. MCPTox (Wang et al., Aug 2025)

- **arXiv**: 2508.14925 | **GitHub**: zhiqiangwang4/MCPTox-Benchmark
- **Scale**: 1,312 test cases, 45 live real-world MCP servers, 353 tools, 11 risk categories (Privacy Leakage, Message Hijacking, etc.), 3 attack paradigms. Tested on 20 LLM agents.
- **How it works**: Poisoned tool descriptions (Tool Poisoning Attack / TPA) injected during registration. The poisoned tool itself never executes — all malicious actions performed by legitimate server tools.
- **Client→Server**: MEDIUM. Downstream effect: poisoned client abuses legitimate server tools (e.g., SSH key exfiltration via filesystem tool, email hijacking via email tool).
- **Key finding**: o1-mini 72.8% ASR. Refusal rate <3% even for Claude 3.7 Sonnet. Inverse scaling confirmed.

## 4. MCP-SafetyBench (Zong et al., Dec 2025)

- **arXiv**: 2512.15163
- **Scale**: 20 attack types, 5 domains (browser automation, financial analysis, location nav, repo mgmt, web search). Multi-turn, multi-server. Built on MCP-Universe real servers.
- **Client→Server attacks** (user-side):
  - Malicious Code Execution: reverse shell via .bashrc
  - Credential Theft: API keys, SSH keys, env vars via file-reading tools
  - Remote Access Control: SSH key injection via file-manipulation tools
  - RADE: poisoned retrieval data triggers indirect prompt injection
  - Excessive Privileges Misuse: admin tools used for read-only tasks
  - Replay Injection: replaying valid interactions for unauthorized actions
- **Key finding**: No model immune. ASR 30-50% across models. Host-side attacks >80% success.

## 5. MCP-AttackBench (Xing et al., Aug 2025)

- **arXiv**: 2508.10991 | **GitHub**: GenTelLab/MCP-Guard
- **Scale**: 70,448 samples augmented by GPT-4. Largest MCP security dataset.
- **Attack types**: Shadowing Attacks, Puppet Attacks, Resource Exfiltration via MCP Resources primitive (passive env var access).
- **3-stage filtration**: Protocol-Compliant Embedding → JSON Schema Validation → Semantic Deduplication.
- **Client→Server**: MEDIUM. Payloads embedded in MCP fields (description, inputSchema, JSON-RPC). Resource exfiltration from server.
- **Defense**: MCP-Guard achieves 96.01% accuracy, 95.4% F1.

## 6. MCIP-Bench (Jing et al., May 2025)

- **arXiv**: 2505.14590
- **Scale**: 11 categories (10 risk + 1 gold), 200 real conversations from glaiveai/glaive-function-calling-v2, 10,633 function call pairs, DeepSeek-R1 assisted labeling.
- **Client→Server**: MEDIUM. Version Mismatch (security logic fails), Replay Injection, unauthorized function calls outside permitted scope.
- **Defense**: MCIP-Guardian trained model.

## 7. SafeMCP (Fang et al., Jun 2025)

- **arXiv**: 2506.13666
- **Framework**: Controlled testing of third-party MCP service risks. APIs for GPT-4o, o1, Qwen3, DeepSeek-R1, Doubao. Passive defense (whitelisting, post-hoc detection) + active defense (content filtering). 5 evaluation metrics across 3 dimensions. Prompt fusion technique hides injected attacks.
- **Client→Server**: MEDIUM. Agent interaction with malicious 3rd-party servers results in exploitation of legitimate server tools/resources.

## 8. ProtoAmp (Jan 2026)

- **arXiv**: 2601.17549
- **Scale**: 847 attack scenarios across 5 MCP server implementations. Bridges InjecAgent/AgentDojo to MCP infrastructure.
- **3 protocol-level vulnerabilities**:
  1. No capability attestation → servers claim arbitrary permissions
  2. Bidirectional sampling without origin auth → server-side prompt injection
  3. Implicit trust propagation in multi-server configs → cross-server attacks
- **Client→Server**: HIGH. MCP amplifies ASR by 23-41% vs non-MCP baselines. System prompt defense: 61.3% → 47.2%. AttestMCP protocol extension: 8.7%.

## 9. SHADE-Arena (Kutasov et al., Jun 2025)

- **arXiv**: 2506.15740
- **Scale**: 17 task pairs, 340+ tools, 100k+ tokens environment. Evaluates sabotage + evasion.
- **Client→Server**: LOW (indirect). Agents misuse server tools for covert side objectives. Best model: Claude 3.7 Sonnet at 27%.

## 10. MPMA (Wang et al., May 2025)

- **arXiv**: 2505.11154
- **Attack**: MCP Preference Manipulation Attack. Attacker deploys customized MCP server, manipulates LLMs to prioritize it. Direct Preference Manipulation Attack (DPMA) uses manipulative words in tool names/descriptions.
- **Client→Server**: LOW (indirect). Steers client away from legitimate servers toward attacker's.

## 11. MCP Safety Audit (Radosevich & Halloran, Apr 2025)

- **arXiv**: 2504.03767 | **GitHub**: johnhalloran321/mcpSafetyScanner
- **Scale**: 4 attack types, tested on Claude 3.7 + Llama-3.3-70B. PoC exploits on standard MCP servers.
- **All 4 attacks are client→server** (HIGH):
  1. Malicious Code Execution — client uses server code execution tools for harmful commands
  2. Remote Access Control (RAC) — client uses server file tools to inject SSH keys
  3. Credential Theft (CT) — client uses server tools to exfiltrate credentials
  4. RADE — multi-server: poisoned retrieval triggers CT/RAC via another server's tools
- **Key finding**: Both Claude and Llama susceptible to all 3 direct attacks. RADE works even with safety guardrails.

## 12. SAFE-MCP Framework (safemcp.org)

- **Source**: Astha.ai, Linux Foundation, OpenID Foundation
- **Scale**: 80+ techniques, 14 tactic categories mapped to MITRE ATT&CK.
- **Tactics**: Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Exfiltration, Impact, C2, Resource Dev, Recon.
- **Client→Server**: MEDIUM. Comprehensive taxonomy of client-initiated techniques against MCP servers. Useful for threat modeling.
