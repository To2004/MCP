# Attack Payload Library — MCP Server Attacks

Threat model: **MCP servers are the victim. Agents and clients are the attacker.**
All payloads in this library represent attacks sent from a client/agent to a server — never the reverse.

Sources: MCPSecBench (arXiv:2508.13220), MCPTox (openreview:xbs5dVGUQ8), ProtoAMP (arXiv:2601.17549), MCP-SafetyBench (arXiv:2512.15163), MCIP-Bench, MCP Safety Audit (MCPSafetyScanner), MCP-AttackBench (arXiv:2508.10991), InjecAgent, AgentDojo, and the project's own testbed run results (2026-04-08).

---

## Table of Contents

| Server | File | Primary Attack Categories | CVEs |
|--------|------|--------------------------|------|
| [filesystem](#filesystem) | [filesystem.md](filesystem.md) | Path traversal, SSH key injection, credential theft, log tampering | CVE-2025-53109, CVE-2025-53110 |
| [git](#git) | [git.md](git.md) | Argument injection, RCE, SSRF, indirect prompt injection | CVE-2025-68143, CVE-2025-68144, CVE-2025-68145 |
| [sqlite](#sqlite) | [sqlite.md](sqlite.md) | SQL injection, schema enumeration, state corruption, replay attack | CVE-2026-5322 (analog) |
| [fetch](#fetch) | [fetch.md](fetch.md) | SSRF, RADE, indirect prompt injection | CVE-2025-65513 |
| [everything](#everything) | [everything.md](everything.md) | Environment variable exfiltration, behavioral fingerprinting, auth bypass | — |
| [sequential-thinking](#sequential-thinking) | [sequential-thinking.md](sequential-thinking.md) | Implicit trigger injection, causal dependency injection, denial of wallet | — |
| [slack](#slack) | [slack.md](slack.md) | Tool misuse, indirect prompt injection, credential theft | — |
| [brave-search](#brave-search) | [brave-search.md](brave-search.md) | RADE, API quota exhaustion, denial of wallet | — |
| [puppeteer](#puppeteer) | [puppeteer.md](puppeteer.md) | Browser SSRF, screenshot exfiltration, JS execution, file:// read | — |
| [playwright](#playwright) | [playwright.md](playwright.md) | Browser SSRF, snapshot exfiltration, indirect prompt injection, file:// read | — |
| [github](#github) | [github.md](github.md) | Token exfiltration, supply chain attack, indirect prompt injection, history mining | — |
| [google-maps](#google-maps) | [google-maps.md](google-maps.md) | API key exposure, surveillance, denial of wallet, SSRF | — |
| [notion](#notion) | [notion.md](notion.md) | Database dump, indirect prompt injection, content injection, state corruption | — |
| [tavily](#tavily) | [tavily.md](tavily.md) | RADE, denial of wallet, bulk content extraction | — |
| [exa](#exa) | [exa.md](exa.md) | RADE, content extraction, denial of wallet | — |
| [firecrawl](#firecrawl) | [firecrawl.md](firecrawl.md) | RADE, SSRF, bulk crawl, denial of wallet | — |
| [desktop-commander](#desktop-commander) | [desktop-commander.md](desktop-commander.md) | Command injection, reverse shell, config bypass, disk exhaustion | — |
| [gmail](#gmail) | [gmail.md](gmail.md) | Phishing, indirect prompt injection, credential theft, mass exfiltration | — |
| [ms-365](#ms-365) | [ms-365.md](ms-365.md) | Phishing, indirect prompt injection, SharePoint exfiltration, calendar injection | — |
| [gitmcp](#gitmcp) | [gitmcp.md](gitmcp.md) | Indirect prompt injection, credential theft, supply chain, privilege escalation | — |
| [bright-data](#bright-data) | [bright-data.md](bright-data.md) | SSRF via proxy, RADE, bulk scraping, denial of wallet | — |
| [excel-mcp](#excel-mcp) | [excel-mcp.md](excel-mcp.md) | CSV formula injection, DDE injection, log forgery, financial data exfil | CVE-2025-13133 |
| [mcp-alchemy](#mcp-alchemy) | [mcp-alchemy.md](mcp-alchemy.md) | SQL injection, schema enumeration, credential theft, OS command via DB | — |
| [feishu](#feishu) | [feishu.md](feishu.md) | Tool misuse, data exfiltration, indirect prompt injection, credential theft | — |
| [mcp-bridge](#mcp-bridge) | [mcp-bridge.md](mcp-bridge.md) | Unauthenticated RCE, network-wide exposure, replay attack, cross-server chaining | GHSA-wvr4-3wq4-gpc5 |
| [fastmcp](#fastmcp) | [fastmcp.md](fastmcp.md) | SSRF (0.0.0.0 bypass), path traversal, protocol exhaustion | CVE-2026-32871 |
| [markdownify-mcp](#markdownify-mcp) | [markdownify-mcp.md](markdownify-mcp.md) | SSRF via URL conversion, path traversal, indirect prompt injection | CVE-2025-5273, CVE-2025-5276 |
| [mcp-data-vis](#mcp-data-vis) | [mcp-data-vis.md](mcp-data-vis.md) | SQL injection, schema enumeration, data destruction, path traversal | CVE-2026-5322 |
| [mcp-run-python](#mcp-run-python) | [mcp-run-python.md](mcp-run-python.md) | Sandbox escape, reverse shell, environment dump, container escape, CPU DoS | — |
| [serverless-mcp](#serverless-mcp) | [serverless-mcp.md](serverless-mcp.md) | Command injection via list-projects, reverse shell, credential theft | CVE-2025-69256 |
| [godot-mcp](#godot-mcp) | [godot-mcp.md](godot-mcp.md) | Command injection via projectPath, path traversal, behavioral fingerprinting | CVE-2026-25546 |
| [adx-mcp](#adx-mcp) | [adx-mcp.md](adx-mcp.md) | KQL injection, schema exfiltration, cross-database escalation, DROP TABLE | CVE-2026-33980 |
| [aws-mcp](#aws-mcp) | [aws-mcp.md](aws-mcp.md) | Command injection, SSRF, path traversal, credential theft, denial of wallet | CVE-2025-5277 |
| [chroma](#chroma) | [chroma.md](chroma.md) | Full collection dump, vector store poisoning (RADE), collection deletion | — |
| [damn-vulnerable-mcp](#damn-vulnerable-mcp) | [damn-vulnerable-mcp.md](damn-vulnerable-mcp.md) | Path traversal, excessive permissions, rug pull, RCE, SSH key injection, SQL injection | — |
| [blog-publisher](#blog-publisher) | [blog-publisher.md](blog-publisher.md) | Content injection, credential theft, indirect prompt injection, XSS, mass deletion | — |
| [twitter-mcp](#twitter-mcp) | [twitter-mcp.md](twitter-mcp.md) | Disinformation posting, OAuth token theft, mass DM phishing, follower exfil | — |
| [web-research-mcp](#web-research-mcp) | [web-research-mcp.md](web-research-mcp.md) | RADE, SSRF, denial of wallet, competitive intelligence scraping | — |
| [MCPSecBench custom servers](#mcpsecbench-custom-servers) | [mcpsecbench-custom-servers.md](mcpsecbench-custom-servers.md) | Tool schema injection, sampling injection, initialization injection, DNS rebinding, container escape | — |

---

## Attack Category Legend

| Category | Description |
|----------|-------------|
| **Path traversal** | Reading files outside the server's intended directory |
| **Command injection** | Injecting OS commands via tool parameters (CWE-78, CWE-88) |
| **SQL injection** | Injecting SQL into database query tools (CWE-89) |
| **KQL injection** | Injecting KQL into Azure Data Explorer tools |
| **SSRF** | Server-Side Request Forgery — server fetches internal endpoints (CWE-918) |
| **RADE** | Retrieval-Augmented Data Exfiltration — poisoned retrieved content hijacks agent |
| **Indirect prompt injection** | Hidden instructions in external content hijack the agent (CWE-20) |
| **Tool misuse** | Using legitimate tools for malicious purposes (CWE-441) |
| **Credential theft** | Extracting API keys, tokens, database passwords (CWE-522) |
| **Denial of wallet** | Exhausting API quotas or compute budgets (CWE-400) |
| **State corruption** | Corrupting server internal state (CWE-666) |
| **Auth bypass** | Accessing privileged tools without authentication (CWE-306) |
| **Output injection** | Injecting malicious content into server-written output (CWE-1236) |
| **Container escape** | Breaking out of sandbox/container isolation (CWE-269) |
| **Replay attack** | Replaying captured tool calls without idempotency guards (CWE-294) |
| **Behavioral fingerprinting** | Probing error messages to reveal technology stack (CWE-209) |

---

## ASR Reference (from papers)

| Attack Type | ASR | Source |
|-------------|-----|--------|
| Protocol-side attacks (any) | 100% | MCPSecBench (arXiv:2508.13220) |
| Tool poisoning (overall) | 72.8% | MCPTox (openreview:xbs5dVGUQ8) |
| Out-of-scope parameter injection | 74.03% | MSB (Zhang et al.) |
| Sampling vulnerability | 67.2% | ProtoAMP (arXiv:2601.17549) |
| Cross-server propagation | 61.3% | ProtoAMP (arXiv:2601.17549) |
| Server-side attacks (overall) | ~47% | MCPSecBench (arXiv:2508.13220) |
| Indirect injection | 47.8% | ProtoAMP (arXiv:2601.17549) |
| Parasitic toolchain attacks | 90% | MCP Server Database (arXiv:2509.06572) |
| Tool poisoning GPT-4o | 61.8% | MCPTox (openreview:xbs5dVGUQ8) |
| Tool poisoning Claude | 34.3% | MCPTox (openreview:xbs5dVGUQ8) |
| Client-side attacks (overall) | ~33% | MCPSecBench (arXiv:2508.13220) |
| Host-side attacks (overall) | ~27% | MCPSecBench (arXiv:2508.13220) |
| Replay injection | 9.9% | MCIP-Bench |
| Initialization injection (undetected) | 96.7% undetected | Component-based Attack PoC |

---

## How to Use These Payloads

Each payload is a complete JSON-RPC 2.0 message ready to send to an MCP server's stdio transport or HTTP endpoint. To replay a payload against a running server:

**Via stdio (Python MCP client):**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async with stdio_client(StdioServerParameters(command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp/sandbox"])) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("read_file", {"path": "../../etc/passwd"})
        print(result)
```

**Via HTTP (for bridge/HTTP servers):**
```bash
curl -X POST http://localhost:3001/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"read_file","arguments":{"path":"../../etc/passwd"}}}'
```

The testbed harness (`tests/testbed/harness/attack_runner.py`) can also run these payloads systematically against any server profile.
