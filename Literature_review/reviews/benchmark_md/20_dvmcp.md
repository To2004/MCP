# Damn Vulnerable MCP Server (DVMCP)

## Source
- **Project:** harishsg993010/damn-vulnerable-MCP-server
- **Link:** https://github.com/harishsg993010/damn-vulnerable-MCP-server
- **Year:** 2025-2026 era community project (public GitHub repository verified 2026-03-30)

## Format & Size
- **Total samples:** **10 challenges** across three difficulty levels
- **Format:** Deliberately vulnerable MCP challenge servers, intended for local execution via Docker, with challenge implementations, docs, solutions, and tests
- **Availability:** Public GitHub repository. The repo exposes challenge folders, tests, Docker files, and setup scripts

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Challenge ID | Integer | 1-10 | Yes | Stable per-challenge identifier |
| Difficulty tier | Categorical | Easy / Medium / Hard | Yes | Direct curriculum-style progression |
| Vulnerability class | Categorical | Prompt Injection, Tool Poisoning, Excessive Permission Scope, Rug Pull, Tool Shadowing, Indirect PI, Token Theft, Malicious Code Execution, Remote Access Control, Multi-Vector Attack | Yes | Very useful attack taxonomy for practical evaluation |
| Challenge implementation | Code / config | Server-specific vulnerable logic | Partially | Requires execution rather than direct tabular ingestion |
| Endpoint / port | Numeric / string | 9001-9010 | Partially | Useful for reproducible testing harnesses |
| Test / solution material | Docs / code | Solutions, tests, setup docs | Yes | Useful for benchmark reproducibility and regression testing |

## Proposed Risk Dimensions

### Direct Server Exploitability
- **Feeding columns:** Vulnerability class, challenge difficulty, exploit path
- **Proposed scale:** 1-10 with prompt-level issues lower and code execution / remote access higher
- **Derivation:** The challenge set explicitly spans direct server abuse, from prompt injection to malicious code execution and remote access control. Hard challenges naturally map to the upper end of a server-risk scale.

### Privilege Escalation Potential
- **Feeding columns:** Challenge class, required permissions, post-exploit capabilities
- **Proposed scale:** 1-10
- **Derivation:** Excessive permission scope, token theft, malicious code execution, and remote access control are all escalation-oriented. These are particularly useful for calibrating your Permission Overreach and Agent Action Severity dimensions.

### Multi-Vector Chain Risk
- **Feeding columns:** Challenge class, whether multiple weaknesses are chained
- **Proposed scale:** 1-10
- **Derivation:** The multi-vector challenge is a practical demonstration that MCP security failures often compose. This makes DVMCP useful for evaluating cross-tool escalation logic even though it is a small lab.

## Data Quality Notes
- This is a **hands-on challenge lab**, not a statistical benchmark with large sample counts.
- It is ideal for demonstrations, regression tests, and attacker playbooks, but weak as a training corpus for ML.
- Because it is intentionally vulnerable, it may overrepresent clean, didactic exploit patterns compared with real-world messy deployments.
- It remains too small for ecosystem calibration, but it is very strong for practical red-team evaluation of server-side attack handling.

## Usefulness Verdict
DVMCP is not a replacement for MCPSecBench or MCP-AttackBench, but it fills a different gap: it gives you a concrete, runnable set of MCP server attack scenarios that can be used for demos, ablations, smoke tests, and defense validation.

For your thesis, it is especially useful if you want to show that your framework can detect or rate not just abstract benchmark rows but real attack workflows such as remote access, malicious code execution, and chained multi-vector compromise. That makes it a strong **practical benchmark supplement**, even though it is too small to anchor the scoring model statistically.
