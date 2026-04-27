# MCP Servers Catalog — Papers, Benchmarks & Real-World Deployments

**Date:** 2026-04-24
**Purpose:** Thesis on MCP server security risk-scoring framework. Covers official, community, benchmark/research, and security-notable servers with version data and authentication classification.

---

## 0. Authentication Classification

For the thesis threat model — AI agents calling MCP servers — authentication is a first-order security signal. A server with no auth can be invoked by **any** agent that has local access; no credential gate exists at the MCP layer.

### 0.1 Auth Required (server non-functional without credentials)

| Server | Auth Type | Credential |
|--------|-----------|------------|
| GitHub MCP Server (`github/github-mcp-server`) | PAT or OAuth 2.0 | `GITHUB_PERSONAL_ACCESS_TOKEN` or browser OAuth |
| AWS MCP Servers (`awslabs/mcp`) | AWS IAM / SigV4 | `AWS_ACCESS_KEY_ID` / named profiles / IAM roles |
| Azure MCP (`@azure/mcp`) | Azure Entra ID (MSAL) | Azure CLI / Managed Identity / service principal |
| Stripe MCP (`@stripe/mcp`) | API key | `STRIPE_SECRET_KEY` env var; remote uses OAuth |
| Atlassian Remote MCP | OAuth 2.1 (primary) or API token | OAuth 2.1 with PKCE; API token if org admin enables |
| Sentry MCP (`getsentry/sentry-mcp`) | OAuth (cloud) / access token (self-hosted) | Device-code OAuth or personal access token |
| Supabase MCP (`@supabase/mcp-server-supabase`) | OAuth or PAT | Browser OAuth or `SUPABASE_ACCESS_TOKEN` |
| Google Calendar MCP (`@cocal/google-calendar-mcp`) | OAuth 2.0 (Google) | `gcp-oauth.keys.json` + Google account consent |
| Brave Search MCP | API key | `BRAVE_API_KEY` → `X-Subscription-Token` header |
| Tavily MCP | API key | `TAVILY_API_KEY` env var |
| Exa Search MCP | API key | `EXA_API_KEY` env var |
| Bing Web Search MCP | Azure subscription key | `BING_API_KEY` (API retiring August 2026) |
| Hugging Face MCP | Bearer token or OAuth | `HF_TOKEN` env var |
| OKX Exchange MCP | API key + secret + passphrase | `~/.okx/config.toml` (three-part credential) |
| Google Maps MCP (archived) | API key | `GOOGLE_MAPS_API_KEY` env var |
| Reddit MCP | OAuth 2.0 client credentials | `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` |
| WhatsApp MCP (`lharries/whatsapp-mcp`) | WhatsApp QR / session (implicit) | QR scan on first run; session persists ~20 days |
| Slack MCP (archived) | OAuth token | `SLACK_BOT_USER_OAUTH_TOKEN` + `SLACK_TEAM_ID` |
| GitHub MCP (archived reference) | PAT | `GITHUB_PERSONAL_ACCESS_TOKEN` |

### 0.2 Auth Optional (works without credentials; auth raises rate limits or unlocks features)

| Server | Auth Type | Without Auth |
|--------|-----------|--------------|
| Chroma MCP (`chroma-mcp-server`) | API key (cloud only) | Local/ephemeral mode: fully open; cloud deployment: key required |
| PostgreSQL MCP (Anthropic reference) | DB connection string | MCP layer has no auth gate; target DB enforces credentials |
| MySQL MCP (Anthropic reference) | DB connection string | Same as PostgreSQL |
| BioMCP | Multiple optional API keys (NCBI, Semantic Scholar, OncoKB…) | Fully functional; keys unlock higher rate limits |
| Paper Search MCP (`openags/paper-search-mcp`) | Optional API keys | Works against arXiv, PubMed, bioRxiv without keys |
| NASA Data MCP | API key | Public `DEMO_KEY` = 30 req/hr; key = 1,000 req/hr |
| Context7 MCP | API key | 60 req/hr shared pool without key; key gives dedicated quota |

### 0.3 No Auth (fully open — any agent can invoke without credentials)

| Server | Transport | Note |
|--------|-----------|------|
| Filesystem MCP (`@modelcontextprotocol/server-filesystem`) | stdio | Path-scoping only; no identity-based auth |
| Git MCP (`mcp-server-git`) | stdio | Local repos; no auth layer at all |
| **Fetch MCP** (`@modelcontextprotocol/server-fetch`) | stdio | **High risk**: no auth + arbitrary outbound HTTP = natural exfiltration vector |
| Memory MCP (`@modelcontextprotocol/server-memory`) | stdio | Local in-process knowledge graph |
| Time MCP | stdio | Local only; no network |
| Sequential Thinking MCP | stdio | Internal reasoning; no network |
| Everything MCP (`@modelcontextprotocol/server-everything`) | stdio | Intentionally open test/reference server |
| Puppeteer MCP (archived) | stdio | Local Chromium; no MCP-level auth |
| Playwright MCP (`@playwright/mcp`) | stdio | Local browser automation; session auth via browser cookies |
| DuckDuckGo Search MCP | stdio | DDG has no API key; fully open |
| DEX Paprika MCP (`coinpaprika/dexpaprika-mcp`) | stdio / HTTP | DexPaprika API is public; no credentials |
| Wikipedia MCP | stdio | Wikipedia API is public and unauthenticated |
| **DVMCP** (dvmcp.co.uk) | HTTP | Open by design — deliberately vulnerable; never expose in production |
| mcp-remote (transport proxy) | stdio→HTTP | The proxy itself has no auth; brokers upstream OAuth flow |
| MCP Inspector | HTTP (localhost) | Auto-generated session token, localhost only; no external auth |

### 0.4 Security Implications for Risk Scoring

| Auth Class | Attack Surface | Risk Signal |
|------------|---------------|-------------|
| **None** | Any agent with process access can invoke freely | Highest: no credential gate; exfiltration and abuse possible without any stolen secret |
| **Optional** | Unauthenticated path exists; auth adds rate-limiting only | Medium: degraded but functional without credentials |
| **Required** | Agent must hold a valid credential | Lower baseline risk; but auth-bypass CVEs (confused deputy, token validation bugs) become the attack surface |

> **Key finding:** All official Anthropic reference servers (stdio) have **no auth by design** — the security model assumes the invoking process is trusted. This assumption breaks down when an AI agent is the invoker.

---

## 1. Official Anthropic / MCP Steering Group Servers

All live at [github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) (84k+ stars, 904 contributors). All use **stdio** transport. TypeScript servers run via `npx`; Python via `uvx` or `pip`.

### 1.1 Active Reference Servers (April 2026)

| Server | npm / PyPI Package | Transport | Notes |
|--------|--------------------|-----------|-------|
| **Everything** | *(no separate package)* | stdio | Reference test server with prompts, resources, and tools; target in MCP Safety Audit (arxiv:2504.03767) |
| **Fetch** | `@modelcontextprotocol/server-fetch` | stdio | Web content fetching and HTML→Markdown conversion |
| **Filesystem** | `@modelcontextprotocol/server-filesystem` | stdio | Patched in `2025.7.1` / `0.6.3` (CVE-2025-53109, CVE-2025-53110) |
| **Git** | `mcp-server-git` (PyPI) | stdio | Three CVEs patched in `2025.12.18` (CVE-2025-68143/44/45); `git_init` tool removed |
| **Memory** | `@modelcontextprotocol/server-memory` | stdio | Knowledge graph persistent memory |
| **Sequential Thinking** | *(no separate package)* | stdio | Dynamic reflective problem-solving |
| **Time** | *(no separate package)* | stdio | Time and timezone conversion; used in MCP-Bench benchmark |

**Protocol versions:** `2024-11-05` (initial GA, stdio + SSE), `2025-03-26` (Streamable HTTP added, SSE deprecated for remote).

### 1.2 Archived / Retired Official Reference Servers

Moved to [github.com/modelcontextprotocol/servers-archived](https://github.com/modelcontextprotocol/servers-archived). No security guarantees.

| Server | Last npm Version | Transport | Status |
|--------|-----------------|-----------|--------|
| Brave Search | 0.6.2 | stdio | Archived |
| GitHub | *(superseded by github/github-mcp-server)* | stdio | Archived April 2025 |
| GitLab | *(archived)* | stdio | Archived |
| Google Drive | *(archived)* | stdio | Archived |
| Google Maps | *(archived)* | stdio | Archived |
| PostgreSQL | *(archived)* | stdio | Archived |
| Puppeteer | `@modelcontextprotocol/server-puppeteer` v2025.5.12 | stdio | Archived May 2025 |
| Redis | *(archived)* | stdio | Archived |
| Sentry | *(superseded by getsentry/sentry-mcp)* | stdio | Archived |
| Slack | `@modelcontextprotocol/server-slack` v2025.4.25 | stdio | Archived April 2025 |
| SQLite | *(deprecated in favor of db-mcp)* | stdio | Archived |
| AWS KB Retrieval | *(replaced by awslabs/mcp)* | stdio | Archived |
| EverArt | *(archived)* | stdio | Archived |

---

## 2. Official Company / Platform MCP Servers

### 2.1 GitHub MCP Server

| Attribute | Value |
|-----------|-------|
| **Repo** | [github.com/github/github-mcp-server](https://github.com/github/github-mcp-server) |
| **Version** | v1.0.2 (April 22, 2026; ~60 releases) |
| **Transport** | stdio (Docker) + remote HTTP (`https://api.githubcopilot.com/mcp/`) |
| **Tools** | 80+ tools across 20+ toolsets (repos, issues, PRs, Actions, code scanning, Dependabot) |
| **Used in** | Production (GitHub Copilot); MCP Safety Audit paper (prompt injection demos) |

### 2.2 AWS MCP Servers (`awslabs/mcp`)

Repo: [github.com/awslabs/mcp](https://github.com/awslabs/mcp). All stdio; SSE removed May 2025. All PyPI packages under `awslabs.*` namespace.

| Server | Package |
|--------|---------|
| AWS Documentation MCP | `awslabs.aws-documentation-mcp-server` |
| AWS IaC MCP | `awslabs.aws-iac-mcp-server` |
| Amazon EKS MCP | `awslabs.eks-mcp-server` |
| Amazon ECS MCP | `awslabs-ecs-mcp-server` |
| AWS Serverless MCP | `awslabs.aws-serverless-mcp-server` |
| Amazon Bedrock KB | `awslabs.bedrock-kb-retrieval-mcp-server` |
| Amazon DynamoDB MCP | `awslabs.dynamodb-mcp-server` |
| Amazon Aurora PostgreSQL MCP | `awslabs.postgres-mcp-server` |
| Amazon Aurora MySQL MCP | `awslabs.mysql-mcp-server` |
| Amazon Neptune MCP | `awslabs.amazon-neptune-mcp-server` |
| Amazon Redshift MCP | `awslabs.redshift-mcp-server` |
| Amazon Kendra MCP | `awslabs.amazon-kendra-index-mcp-server` |
| AWS IAM MCP | `awslabs.iam-mcp-server` |
| Amazon SageMaker MCP | `awslabs.sagemaker-ai-mcp-server` |
| OpenAPI MCP | `awslabs.openapi-mcp-server` |

**CVE note:** community `aws-mcp-server` — CVE-2025-5277 (CVSS 9.6), command injection via unsanitized shell metacharacters.

### 2.3 Microsoft / Azure MCP Server

| Attribute | Value |
|-----------|-------|
| **Repo** | [github.com/microsoft/mcp](https://github.com/microsoft/mcp) (azure-mcp archived August 2025) |
| **npm** | `@azure/mcp` v2.0.0-beta.33; GA "1.0" announced |
| **Transport** | stdio |
| **CVEs** | CVE-2026-26118 (SSRF → privilege elevation, CVSS 8.8); CVE-2026-32211 (missing auth → credential disclosure, CVSS 9.1) |
| **Used in** | MCPSecBench benchmark |

### 2.4 Stripe MCP Server

| Attribute | Value |
|-----------|-------|
| **Repo** | [github.com/stripe/agent-toolkit](https://github.com/stripe/agent-toolkit) |
| **npm** | `@stripe/mcp` v0.2.4; toolkit: `@stripe/agent-toolkit` |
| **Transport** | stdio (local `npx`) + remote HTTP (`https://mcp.stripe.com`, OAuth) |
| **Used in** | arxiv:2506.13538 (landscape study) |

### 2.5 Atlassian Remote MCP Server

| Attribute | Value |
|-----------|-------|
| **Repo** | [github.com/atlassian/atlassian-mcp-server](https://github.com/atlassian/atlassian-mcp-server) |
| **Remote endpoint** | `https://mcp.atlassian.com/v1/mcp` (Streamable HTTP) |
| **Deprecated endpoint** | `https://mcp.atlassian.com/v1/sse` (deprecated; supported until June 30, 2026) |
| **CVEs** | CVE-2026-27825 (path traversal → arbitrary file write → RCE, CVSS 9.1); CVE-2026-27826 (SSRF, CVSS 8.2) |

### 2.6 Sentry MCP Server

| Attribute | Value |
|-----------|-------|
| **Repo** | [github.com/getsentry/sentry-mcp](https://github.com/getsentry/sentry-mcp) |
| **Transport** | stdio |
| **Tools** | Query errors, issues, projects; create projects |

### 2.7 Microsoft Playwright MCP Server

| Attribute | Value |
|-----------|-------|
| **Repo** | [github.com/microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) |
| **npm** | `@playwright/mcp` (via `npx @playwright/mcp@latest`) |
| **Transport** | stdio |
| **Also** | Cloudflare fork: `@cloudflare/playwright-mcp` |

### 2.8 Supabase MCP Server

| Attribute | Value |
|-----------|-------|
| **Repo** | [github.com/supabase-community/supabase-mcp](https://github.com/supabase-community/supabase-mcp) |
| **npm** | `@supabase/mcp-server-supabase` v0.5.10 (October 17, 2025) |
| **Transport** | stdio |

### 2.9 Chroma MCP Server (Vector Database)

| Attribute | Value |
|-----------|-------|
| **Repo** | [github.com/chroma-core/chroma-mcp](https://github.com/chroma-core/chroma-mcp) |
| **PyPI** | `chroma-mcp-server` (through v0.2.28, May 2025) |
| **Transport** | stdio (via `uvx chroma-mcp`) |
| **Used in** | MCP Safety Audit (arxiv:2504.03767) — RADE attacks against Claude Desktop v0.8.1 |

---

## 3. Research and Benchmark Contexts

### 3.1 MCP Safety Audit — arxiv:2504.03767

**Platform:** Claude Desktop v0.8.1 on macOS Sequoia 15.3.2

| Server | Command | Attacks Tested |
|--------|---------|----------------|
| Filesystem (Anthropic) | `npx @modelcontextprotocol/server-filesystem` | MCE, RAC, credential theft |
| Slack (Anthropic, archived) | `npx @modelcontextprotocol/server-slack` | Credential exfiltration via messaging |
| Everything (Anthropic) | `npx @modelcontextprotocol/server-everything` | Credential theft via `printEnv` |
| Chroma | `uvx chroma-mcp` | RADE attacks (corrupted vector retrieval) |

**Also introduced:** MCPSafetyScanner — first multi-agent auditing tool; pilot ASR ~41%; Out-of-Scope Parameter attacks >74%.

### 3.2 MCPBench / ModelScope — arxiv:2504.11094

**Mode:** All servers in SSE mode, 30-second timeout, Singapore server.

| Server | Accuracy | Avg Time |
|--------|----------|----------|
| Brave Search | 46.6% | 13.98 s |
| DuckDuckGo Search | 13.62% | 64.17 s |
| Tavily MCP | 47.99% | 95.52 s |
| Exa Search | 15.02% | 231.24 s |
| Fire Crawl Search | 58.33% | 15.44 s |
| Bing Web Search | **64.33%** | 12.4 s |
| MySQL MCP | 56.06% (declarative) | — |
| PostgreSQL MCP | **80.08%** (declarative) | — |

### 3.3 MCP-SafetyBench — arxiv:2512.15163 (ICLR 2026)

245 test cases across 5 domains (Financial Analysis, Location Navigation, Repository Management, Browser Automation, Web Search). Real MCP servers, built on MCP-Universe.
**Key finding:** Overall ASRs 30–50% across 13 LLMs; 20 attack types across server-side (74.69%), host-side (12.24%), and user-side (13.06%) attack surfaces.

### 3.4 MCPSecBench — arxiv:2508.13220

Repo: [github.com/AIS2Lab/MCPSecBench](https://github.com/AIS2Lab/MCPSecBench)

| Platform | Version |
|----------|---------|
| Claude Desktop (claude-opus-4.5) | v0.12.28 |
| GPT-4.1 | — |
| Cursor | v1.2.2 → v2.3.29 |

17 attack types across 4 surfaces; transport: stdio, HTTP Streaming, SSE. Real-world demo via CVE-2025-6514 (mcp-remote).

### 3.5 MCPTox — arxiv:2508.14925

45 live real-world MCP servers, 353 authentic tools (from mcp.so and mcpservers.cn), 8 application domains, 1,312 malicious test cases, 11 risk categories. ASR up to **72.8%** across 20 LLM agents.

### 3.6 MCPVerse — arxiv:2508.16260

65 MCP servers, 552 unique tools, 250 human-curated tasks (L1–L3 complexity).
Domains: file system, Git, Yahoo Finance, GeekNews, Amap, Variflight, Excel, code sandbox.
Modes: Oracle, Standard (32 MCPs / 218 tools / 64k token budget), Max-Scale (all 65).

### 3.7 MCP-Bench (Accenture) — arxiv:2508.20453 (NeurIPS 2025 Workshop)

Repo: [github.com/Accenture/mcp-bench](https://github.com/Accenture/mcp-bench). 28 live servers, 250 tools across finance, travel, scientific computing, academic search. Judge: o4-mini.

Named servers:

| Server | Domain |
|--------|--------|
| BioMCP | Clinical trials / health |
| Paper Search | Academic databases |
| Hugging Face | ML models and datasets |
| NASA Data | Space missions |
| DEX Paprika | Cryptocurrency/DeFi |
| OKX Exchange | Trading data |
| Math MCP | Calculations |
| Time MCP | Date/timezone |
| Wikipedia | Encyclopedia |
| Reddit | Social content |
| Google Maps | Location services |
| Context7 | Documentation lookup |
| OSINT Intelligence | Research gathering |
| NixOS | Package management |

### 3.8 Ecosystem Security Study — arxiv:2506.13538

1,899 MCP servers total; 583 with ≥10 GitHub stars. Language split: TypeScript (227), Python (196), JavaScript (115).
- 7.2% had general vulnerabilities (credential exposure most common: 3.6%)
- 5.5% had MCP-specific tool poisoning
- 66% had code smells; 14.4% had critical/blocker-level bugs
- Scanned with SonarQube + mcp-scan (83-server sample)

### 3.9 WhatsApp MCP — Invariant Labs (April 2025)

| Server | Repo | Vulnerability |
|--------|------|---------------|
| whatsapp-mcp | [github.com/lharries/whatsapp-mcp](https://github.com/lharries/whatsapp-mcp) | Tool poisoning + rug pull → full message-history exfiltration |

---

## 4. CVE Inventory

### 4.1 Anthropic Official Server CVEs

| Server | CVE | Affected | Fixed | CVSS | Type |
|--------|-----|----------|-------|------|------|
| mcp-server-git | CVE-2025-68145 | < 2025.12.18 | 2025.12.18 | 6.4 | Path validation bypass |
| mcp-server-git | CVE-2025-68143 | < 2025.9.25 | 2025.9.25 | 6.5 | Unrestricted `git_init` |
| mcp-server-git | CVE-2025-68144 | < 2025.12.18 | 2025.12.18 | 6.3 | Argument injection in `git_diff`/`git_checkout` |
| Filesystem MCP | CVE-2025-53109 | < 0.6.3 / < 2025.7.1 | 0.6.3 | 8.4 | Symlink bypass → RCE ("EscapeRoute") |
| Filesystem MCP | CVE-2025-53110 | < 0.6.3 / < 2025.7.1 | 0.6.3 | 7.3 | Directory-containment bypass |
| MCP Inspector | CVE-2025-49596 | < 0.14.1 | 0.14.1 | 9.4 | Unauthenticated RCE via browser CSRF |

### 4.2 SDK-Level CVEs

| SDK | CVE | Affected | Fixed | CVSS | Type |
|-----|-----|----------|-------|------|------|
| TypeScript SDK | CVE-2026-25536 | 1.10.0–1.25.3 | 1.26.0 | 7.1 | Cross-client data leak via shared instance reuse |
| TypeScript SDK | CVE-2025-66414 | < 1.24.0 | 1.24.0 | 8.0 | DNS rebinding on localhost SSE/StreamableHTTP |
| Python SDK (`mcp`) | CVE-2025-66416 | < 1.23.0 | 1.23.0 | 8.0 | DNS rebinding on localhost SSE/StreamableHTTP |
| Go SDK | CVE-2026-34742 | < 1.4.0 | 1.4.0 | — | DNS rebinding protection disabled by default |
| Go SDK | CVE-2026-33252 | < 1.4.1 | 1.4.1 | — | CSRF (missing Origin header on Streamable HTTP) |
| Ruby SDK | CVE-2026-33946 | < 0.9.2 | 0.9.2 | — | SSE stream hijacking via session ID replay |

### 4.3 Community Server CVEs (Server as Victim — In-Scope for Thesis)

| Server | CVE | CVSS | Type | Transport |
|--------|-----|------|------|-----------|
| mcp-server-kubernetes | CVE-2025-53355 | 7.5 | Command injection in `kubectl_scale`/`patch`/`explain` via `execSync` | stdio |
| node-code-sandbox-mcp | CVE-2025-53372 | 7.5 | Docker sandbox escape — `container_id` unsanitized in `execSync` | stdio |
| figma-developer-mcp (Framelink) | CVE-2025-53967 | 7.5–8.0 | Command injection in `get_figma_data` → `child_process.exec` | stdio |
| mcp-fetch-server | CVE-2025-65513 | 9.3 | SSRF — `is_ip_private()` receives full URL, always returns false | stdio |
| Zen MCP Server | CVE-2025-66689 | 6.5–9.8 | Path traversal via blacklist bypass in `is_dangerous_path()` | stdio |
| filesystem-mcp | CVE-2025-67366 | 7.0 | Path traversal | stdio |
| create-mcp-server-stdio | CVE-2025-54994 | 10.0 | Command injection in scaffolding CLI | stdio |
| Serverless Framework MCP | CVE-2025-69256 | — | Command injection in `list-projects` tool | stdio |
| Vet MCP Server | CVE-2025-59163 | 7.0 | DNS rebinding | SSE |
| gemini-mcp-tool | CVE-2026-0755 | 9.8 | Command injection | Network |
| GitHub Kanban MCP | CVE-2026-0756 | Critical | RCE via tool interface | stdio |
| MCPJam Inspector | CVE-2026-23744 | 9.8 | Binds 0.0.0.0 with no auth → install malicious MCP server | HTTP |
| mcp-atlassian (community) | CVE-2026-27825 | 9.1 | Path traversal → arbitrary file write → RCE | HTTP |
| mcp-atlassian (community) | CVE-2026-27826 | 8.2 | SSRF via Atlassian URL headers | HTTP |
| FastMCP | CVE-2026-27124 | 8.2 | OAuth Confused Deputy (OAuthProxy skips consent validation) | HTTP |
| FastMCP OpenAPI Provider | CVE-2026-32871 | 10.0 | SSRF + path traversal via `urljoin()` with `../` in path params | HTTP |
| adx-mcp-server (Azure Data Explorer) | CVE-2026-33980 | 8.3 | KQL injection in schema/sample/details tools | stdio |
| mcp-data-vis | CVE-2026-5322 | 7.3 | SQL injection in `create_table` via `db.exec()` | stdio |
| godot-mcp | CVE-2026-25546 | — | Command injection in `executeOperation` (`projectPath` → `exec()`) | stdio |
| WeKnora | CVE-2026-30861 | — | Command injection in stdio config validation | stdio |
| PraisonAI | CVE-2026-34953 | 9.1 | OAuth token validation broken — any Bearer token grants full access | HTTP |
| PraisonAI | CVE-2026-34935 | — | OS command injection in `MCPHandler.parse_mcp_command()` | stdio |
| nginx-ui (MCP endpoint) | CVE-2026-33032 | Critical | Unauthenticated `/mcp_message` → nginx takeover | HTTP |
| mcp-framework (QuantGeekDev) | CVE-2026-39313 | 8.7 | DoS via unbounded POST body | HTTP |
| @mobilenext/mobile-mcp | CVE-2026-33989 | 8.1 | Path traversal in screen-capture parameters | stdio |
| @mobilenext/mobile-mcp | CVE-2026-35394 | — | Arbitrary Android Intent via `mobile_open_url` | stdio |
| mcp-bridge | GHSA-wvr4-3wq4-gpc5 | — | Unauthenticated RCE via `/bridge` endpoint | HTTP |
| mcp-handler (npm) | GHSA-w2fm-25vw-vh7f | — | Race condition — tool responses leak across concurrent sessions | HTTP |
| Apache Doris MCP | CVE-2025-66335 | 5.3 | SQL injection via query context bypass | stdio |
| markdownify-mcp | CVE-2025-5273 | — | Arbitrary file read via path validation failure | stdio |
| markdownify-mcp | CVE-2025-5276 | — | SSRF via unrestricted URL fetching | stdio |
| aws-mcp-server (community) | CVE-2025-5277 | 9.6 | Command injection via shell metacharacters | stdio |
| Flowise | CVE-2025-59528 | 10.0 | Unauthenticated RCE — `mcpServerConfig` passed to `Function()` constructor | HTTP |
| Microsoft Azure MCP | CVE-2026-26118 | 8.8 | SSRF → privilege elevation | stdio |
| Microsoft Azure MCP | CVE-2026-32211 | 9.1 | Missing auth → credential disclosure | stdio |

### 4.4 Client-Side / Inverse-Direction CVEs (Out of Thesis Scope)

| Server/Client | CVE | CVSS | Type |
|--------------|-----|------|------|
| mcp-remote (npm) | CVE-2025-6514 | 9.6 | OS command injection via OAuth `authorization_endpoint`; fixed in 0.1.16 |
| Windsurf IDE | CVE-2026-30615 | 8.0 | Zero-click: malicious MCP config in project → local RCE |
| LiteLLM | CVE-2026-30623 | Critical | Authenticated RCE via JSON MCP STDIO config |
| GPT Researcher | CVE-2025-65720 | Critical | Unauthenticated UI → malicious MCP STDIO config → reverse shell |

---

## 5. Security Research and Testing Infrastructure

### 5.1 DVMCP (Damn Vulnerable MCP)

Site: [dvmcp.co.uk](https://dvmcp.co.uk/). Deliberately insecure MCP server for security education. Transport: HTTP (default port 3001). 10 intentional flaws mapped to OWASP MCP Top 10.

| Challenge | Vulnerability | OWASP MCP |
|-----------|--------------|-----------|
| MCP-001 | No authentication | MCP-07 |
| MCP-002 | Tool definition tampering (rug pull) | MCP-01 |
| MCP-003 | Command injection via tool arguments | MCP-04 |
| MCP-004 | No input validation | MCP-04 |
| MCP-005 | SSRF via `resources/read` | MCP-06 |
| MCP-006 | Data exfiltration (no response limits) | MCP-06 |
| MCP-007 | Replay attacks (no nonce/timestamp) | MCP-08 |
| MCP-008 | No rate limiting | MCP-09 |
| MCP-009 | Privilege escalation via sampling | MCP-03 |
| MCP-010 | Sensitive tools exposed | MCP-09 |

### 5.2 mcp-scan / Snyk Agent Scan

[github.com/invariantlabs-ai/mcp-scan](https://github.com/invariantlabs-ai/mcp-scan) — rebranded to Snyk Agent Scan (v0.4.13, April 2026). Static tool-description analysis + runtime proxy mode. Used in arxiv:2506.13538 to scan 83 servers.

### 5.3 MCPSafetyScanner

Introduced in arxiv:2504.03767. Multi-agent auditing tool; automatically generates adversarial samples and produces security reports.

### 5.4 mcpscan.ai

[mcpscan.ai](https://mcpscan.ai/) — cloud-based scanner. Scan of 50+ public MCP servers: 23% contained command injection vulnerabilities.

---

## 6. Protocol and Ecosystem Version Anchors

| Component | Version | Date | Notes |
|-----------|---------|------|-------|
| MCP Specification (GA) | 2024-11-05 | Nov 2024 | stdio + SSE transports |
| MCP Specification (Streamable HTTP) | 2025-03-26 | Mar 2025 | StreamableHTTP added; SSE deprecated for remote |
| MCP Python SDK (`mcp`) | 1.23.0 → 1.27.0+ | 2025 | 1.23.0 fixed CVE-2025-66416 |
| MCP TypeScript SDK | 1.24.0 → 1.26.0+ | 2025 | 1.24.0 fixed CVE-2025-66414; 1.26.0 fixed CVE-2026-25536 |
| MCP Go SDK | 1.4.0, 1.4.1 | 2026 | Fixed CVE-2026-34742 and CVE-2026-33252 |
| MCP Ruby SDK | 0.9.2 | 2026 | Fixed CVE-2026-33946 |
| MCP Inspector | 0.14.1 | 2025 | Fixed CVE-2025-49596 |
| Claude Desktop | 0.8.1 (Safety Audit), 0.12.28 (MCPSecBench) | 2025 | Primary MCP client in research |
| Cursor | v1.2.2, v2.3.29 | 2025–2026 | Tested in MCPSecBench |
| Total registered servers | ~18,000 (MCP Market, Jan 2026) | Jan 2026 | 12,000+ across GitHub/npm/PyPI |

---

## Summary Counts

| Category | Count |
|----------|-------|
| Official Anthropic servers (active) | 7 |
| Official Anthropic servers (archived) | 13 |
| Official company integration servers | 40+ (AWS suite: 15, GitHub, Azure, Stripe, Atlassian…) |
| Named servers in research benchmarks | ~60+ (MCPVerse: 65, MCPTox: 45, MCP-Bench: 28) |
| CVEs — server as victim (in-scope) | 35+ CVEs + 2 GHSAs |
| CVEs — SDK-level | 6 (TS, Python, Go, Ruby) |
| CVEs — client/host as victim (out-of-scope) | 4+ |

---

## Sources

- arxiv:2506.13538 — MCP at First Glance (Security & Maintainability)
- arxiv:2504.03767 — MCP Safety Audit (MCPSafetyScanner)
- arxiv:2512.15163 — MCP-SafetyBench (ICLR 2026)
- arxiv:2508.13220 — MCPSecBench
- arxiv:2508.14925 — MCPTox Tool Poisoning Benchmark
- arxiv:2508.16260 — MCPVerse
- arxiv:2508.20453 — MCP-Bench (Accenture/NeurIPS 2025)
- arxiv:2504.11094 — MCPBench Evaluation Report (ModelScope)
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
- [github/github-mcp-server](https://github.com/github/github-mcp-server)
- [awslabs/mcp](https://github.com/awslabs/mcp)
- [The Vulnerable MCP Project CVE database](https://vulnerablemcp.info/)
- [Timeline of MCP Security Breaches — authzed](https://authzed.com/blog/timeline-mcp-breaches)
- [WhatsApp MCP exfiltration — Invariant Labs](https://invariantlabs.ai/blog/whatsapp-mcp-exploited)
- [DVMCP](https://dvmcp.co.uk/)
- [CVE-2025-6514 — mcp-remote RCE (JFrog)](https://jfrog.com/blog/2025-6514-critical-mcp-remote-rce-vulnerability/)
- [CVE-2025-49596 — MCP Inspector RCE (Oligo)](https://www.oligo.security/blog/critical-rce-vulnerability-in-anthropic-mcp-inspector-cve-2025-49596)
- [CVE-2025-53109/53110 — EscapeRoute (Cymulate)](https://cymulate.com/blog/cve-2025-53109-53110-escaperoute-anthropic/)
- [CVE-2025-53967 — Figma MCP (Endor Labs)](https://www.endorlabs.com/learn/cve-2025-53967-remote-code-execution-in-framelink-figma-mcp-server)
