# MCP Client→Server Attack Benchmarks

> Reference document for all known benchmarks evaluating attacks where a **malicious MCP client attacks an MCP server (tool provider)**.
> Last updated: March 2026.

## Quick Reference Table

| # | Benchmark | arXiv | Scale | Client→Server | GitHub |
|---|-----------|-------|-------|----------------|--------|
| 1 | **MSB** | 2510.15994 | 2,000 cases, 12 attacks, 400+ tools | HIGH | — |
| 2 | **MCPSecBench** | 2508.13220 | 17 attacks, 4 surfaces | HIGH | AIS2Lab/MCPSecBench |
| 3 | **MCPTox** | 2508.14925 | 1,312 cases, 45 servers, 353 tools | MEDIUM | zhiqiangwang4/MCPTox-Benchmark |
| 4 | **MCP-SafetyBench** | 2512.15163 | 20 attacks, 5 domains, multi-turn | HIGH | — |
| 5 | **MCP-AttackBench** | 2508.10991 | 70,448 samples | MEDIUM | GenTelLab/MCP-Guard |
| 6 | **MCIP-Bench** | 2505.14590 | 11 categories, 10,633 function pairs | MEDIUM | — |
| 7 | **SafeMCP** | 2506.13666 | Framework + 5 metrics | MEDIUM | — |
| 8 | **ProtoAmp** | 2601.17549 | 847 scenarios, 5 servers | HIGH | — |
| 9 | **SHADE-Arena** | 2506.15740 | 17 task pairs, 340+ tools | LOW | — |
| 10 | **MPMA** | 2505.11154 | Preference manipulation dataset | LOW | — |
| 11 | **MCP Safety Audit** | 2504.03767 | 4 attacks, PoC exploits | HIGH | johnhalloran321/mcpSafetyScanner |
| 12 | **SAFE-MCP** | safemcp.org | 80+ techniques, 14 tactics | MEDIUM | safemcp.org (open-source) |

## Attack Types → Benchmarks Map

| Attack Type | Benchmarks |
|---|---|
| Malicious Code Execution | MCP Safety Audit, MCP-SafetyBench, MCPSecBench |
| Credential Theft | MCP Safety Audit, MCP-SafetyBench, MCPTox, MCPSecBench |
| Remote Access Control | MCP Safety Audit, MCP-SafetyBench |
| Sandbox Escape | MCPSecBench |
| Out-of-Scope Parameters | MSB (74% ASR) |
| RADE (Retrieval-Agent Deception) | MCP Safety Audit, MCP-SafetyBench, MSB |
| Confused Deputy / Misuse | MCPSecBench, MCP Spec |
| Replay Injection | MCP-SafetyBench, MCIP-Bench |
| DNS Rebinding | MCPSecBench |
| Cross-Server Attack | ProtoAmp, MCPTox, MCP-SafetyBench |
| Excessive Privileges Misuse | MCP-SafetyBench |
| Resource Exfiltration | MCP-AttackBench |

For detailed descriptions of each benchmark, see `@docs/mcp-benchmarks-details.md`.
