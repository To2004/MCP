# Additional MCP Security Resources

Supplemental resources found during a targeted gap-fill search (April 2026).
Items already present in the known list are excluded.

## Attack Automation Tools

| Tool | Link | Stars (if known) | What it does |
|------|------|-----------------|--------------|
| mcp-server-fuzzer | https://github.com/Agent-Hellboy/mcp-server-fuzzer | — | Generic MCP server fuzzer; supports tool-argument and protocol-type fuzzing, async execution, JSON/CSV/HTML/Markdown reports; installable as `pip install mcp-fuzzer` |
| MCPhound | https://github.com/tayler-id/mcphound | — | Comprehensive MCP security scanner covering cross-server attack paths, tool poisoning, typosquats, CVEs, trust scores, and rug-pull detection |
| mcp-shield | https://github.com/riseandignite/mcp-shield | — | Scans installed MCP servers for tool-poisoning attacks, exfiltration channels, and cross-origin escalations |
| cisco-ai-defense/mcp-scanner | https://github.com/cisco-ai-defense/mcp-scanner | — | Cisco CLI/REST scanner combining their AI Defense inspect API, YARA rules, and LLM-as-judge to flag malicious MCP tools |
| mcpSafetyScanner | https://github.com/johnhalloran321/mcpSafetyScanner | — | Agent-driven automated safety auditing and remediation for arbitrary MCP servers; returns structured vulnerability reports; companion to arXiv:2504.03767 |
| Tencent/AI-Infra-Guard | https://github.com/Tencent/AI-Infra-Guard | — | Full-stack AI red-team platform; includes MCP scan, Agent Scan, and Skills Scan; detects 14 major security risk categories from source or remote URLs |
| ModelContextProtocol-Security/mcpserver-audit | https://github.com/ModelContextProtocol-Security/mcpserver-audit | — | Cloud Security Alliance project; audits MCP servers and publishes findings to shared audit-db and vulnerability-db |
| promptfoo/evil-mcp-server | https://github.com/promptfoo/evil-mcp-server | — | Deliberately malicious MCP server used as a red-team test fixture for adversarial prompt/tool testing |
| securityfortech/secops-mcp | https://github.com/securityfortech/secops-mcp | — | All-in-one security testing toolbox integrating popular OSS security tools through a single MCP interface |
| FuzzingLabs/mcp-security-hub | https://github.com/FuzzingLabs/mcp-security-hub | — | 300+ offensive security tools (Nmap, Ghidra, Nuclei, SQLMap, Hashcat, etc.) accessible via natural language through MCP |
| gleicon/mcp-redteam | https://github.com/gleicon/mcp-redteam | — | Local MCP server grouping infosec tools for red-team and reconnaissance commands usable from Claude and other MCP clients |
| SaravanaGuhan/mcp-guard | https://github.com/SaravanaGuhan/mcp-guard | — | Comprehensive MCP security assessment tool using static analysis, dynamic testing, and intelligent fuzzing |
| AIM-Intelligence/AIM-MCP | https://github.com/AIM-Intelligence/AIM-MCP | — | Guard/protection layer for MCP servers and AI chat sessions |

## Missed Papers

| Title | Link | Date | One-line relevance |
|-------|------|------|-------------------|
| Enterprise-Grade Security for the Model Context Protocol (MCP): Frameworks and Mitigation Strategies | https://arxiv.org/abs/2504.08623 | Apr 2025 | Systematic threat modeling of MCP attack vectors with enterprise mitigation frameworks including tool-poisoning defenses |
| Model Context Protocol (MCP) at First Glance: Studying the Security and Maintainability of MCP Servers | https://arxiv.org/abs/2506.13538 | Jun 2025 | First large-scale empirical study of 1,899 open-source MCP servers assessing health, security, and maintainability |
| Toward Understanding Security Issues in the Model Context Protocol Ecosystem | https://arxiv.org/abs/2510.16558 | Oct 2025 | First comprehensive decomposition of the MCP ecosystem (hosts, registries, servers) and its security issues |
| MPMA: Preference Manipulation Attack Against Model Context Protocol | https://arxiv.org/abs/2505.11154 | May 2025 | Introduces MCP Preference Manipulation Attack where attacker server hijacks LLM priority over competing servers |
| Trivial Trojans: How Minimal MCP Servers Enable Cross-Tool Exfiltration of Sensitive Data | https://arxiv.org/abs/2507.19880 | Jul 2025 | PoC attack: minimal malicious weather MCP server leverages legitimate banking tools to steal account balances |
| MCP Safety Training: Learning to Refuse Falsely Benign MCP Exploits using Improved Preference Alignment | https://arxiv.org/abs/2505.23634 | May 2025 | Defense approach using preference alignment to train LLMs to refuse retrieval-based falsely benign MCP attacks |
| Security Threat Modeling for Emerging AI-Agent Protocols: A Comparative Analysis of MCP, A2A, Agora, and ANP | https://arxiv.org/abs/2602.11327 | Feb 2026 | Identifies 12 protocol-level risks across MCP and three competing agent protocols using structured threat modeling |

## Missed GitHub Repos

| Repo | Link | Stars | What it does |
|------|------|-------|--------------|
| slowmist/MCP-Security-Checklist | https://github.com/slowmist/MCP-Security-Checklist | — | Comprehensive security checklist for MCP-based AI tools, built by SlowMist blockchain security firm; distinct from their MasterMCP repo |
| google/mcp-security | https://github.com/google/mcp-security | — | Google-maintained MCP servers exposing Google SecOps, Chronicle, SOAR, and Security Command Center through MCP |
| nisalgunawardhana/MCP-Security-101 | https://github.com/nisalgunawardhana/MCP-Security-101 | — | Educational guide covering MCP vulnerability classes, detection, and prevention patterns |
| msaleme/red-team-blue-team-agent-fabric | https://github.com/msaleme/red-team-blue-team-agent-fabric | — | 342-test security harness for autonomous AI agents aligned with NIST AI 800-2; supports MCP, A2A, and x402 protocols |
| cyproxio/mcp-for-security | https://github.com/cyproxio/mcp-for-security | — | Collection of MCP servers wrapping SQLMap, FFUF, Nmap, and Masscan for AI-driven penetration testing workflows |
| leidosinc/McpSafetyScanner | https://github.com/leidosinc/McpSafetyScanner | — | Leidos fork/mirror of mcpSafetyScanner; companion to arXiv:2504.03767 |
| DMontgomery40/mcp-security-scanner | https://github.com/DMontgomery40/mcp-security-scanner | — | Security vulnerability scanner built with MCP plugins |

## Notes

- **Two distinct scanner categories are emerging:** (1) static/configuration scanners (mcp-scan, mcp-shield, mcphound, cisco mcp-scanner) that analyze tool descriptions offline, and (2) active fuzzing/agent-driven harnesses (mcp-server-fuzzer, mcpSafetyScanner, AI-Infra-Guard) that send live payloads. Most prior literature focused only on the first category.
- **arXiv 2506.13538** is the only large-scale empirical study of real MCP server health (1,899 servers), making it the closest analogue to a dataset paper for this domain.
- **arXiv 2602.11327** is notable for extending the threat model beyond MCP to compare against A2A, Agora, and ANP protocols — useful for situating MCP risk within the broader agent-protocol landscape.
- **arXiv 2504.08623** (Enterprise-Grade Security) was the most-cited practical framework paper in blog posts and industry write-ups but was absent from the known-list — likely a significant gap.
- **The Vulnerable MCP Project** (https://vulnerablemcp.info/) maintains a community-sourced database of MCP CVEs and vulnerability classes; not a GitHub repo but a useful reference resource.
- **NVIDIA/garak** (https://github.com/NVIDIA/garak/issues/1639) has an open issue tracking OWASP MCP Top 10 coverage, indicating the LLM red-team community is converging on MCP-specific attack taxonomy — worth watching for future scanner integration.
- Supply-chain attacks (npm package backdoors, tool poisoning seeded in registries) appear as a distinct and underserved threat vector in the literature, with only MCPTox and the Postmark breach case study addressing it empirically.
