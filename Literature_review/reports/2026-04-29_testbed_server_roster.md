# Testbed MCP Server Roster — Papers & Benchmarks

**Date:** 2026-04-29
**Purpose:** Practical roster of MCP servers referenced in the project's papers and benchmarks,
organized by auth requirement so the proxy testbed knows what can run immediately vs. what needs credentials.
Full catalog with CVE inventory: [2026-04-24_mcp_servers_catalog.md](2026-04-24_mcp_servers_catalog.md).

---

## 1. No Auth — Use Immediately in Testbed

These run over stdio with no credential gate. Any agent (or the proxy) can invoke them freely.

| Server | Package / Run Command | Version | Used In (Papers) | Notes |
|--------|-----------------------|---------|------------------|-------|
| **Filesystem** | `npx @modelcontextprotocol/server-filesystem <path>` | ≥ 0.6.3 / 2025.7.1 | MCP Safety Audit (2504.03767), MCPSecBench (2508.13220), MCP-SafetyBench (2512.15163) | Patch CVE-2025-53109/53110 — use ≥ 0.6.3 |
| **Git** | `uvx mcp-server-git --repository <path>` | ≥ 2025.12.18 | MCPSecBench (2508.13220), MCPVerse (2508.16260) | Patch 3 CVEs — use ≥ 2025.12.18; local repos only |
| **Memory** | `npx @modelcontextprotocol/server-memory` | — | MCP-SafetyBench (2512.15163) | In-process knowledge graph; no network |
| **Everything** | `npx @modelcontextprotocol/server-everything` | — | MCP Safety Audit (2504.03767), MCPTox (2508.14925) | Reference test server; intentionally open |
| **Fetch** | `npx @modelcontextprotocol/server-fetch` | — | — | ⚠ High risk: no auth + arbitrary outbound HTTP = natural exfiltration vector |
| **Sequential Thinking** | `npx @modelcontextprotocol/server-sequentialthinking` | — | — | Internal reasoning; no network |
| **Time** | `npx @modelcontextprotocol/server-time` | — | MCP-Bench / Accenture (2508.20453) | Local time/timezone; no network |
| **Playwright** | `npx @playwright/mcp@latest` | Latest | MCPSecBench (2508.13220), MCPVerse (2508.16260) | Local browser automation; no MCP-level auth |
| **Puppeteer** *(archived)* | `npx @modelcontextprotocol/server-puppeteer` | 2025.5.12 | — | Archived May 2025; use Playwright instead |
| **DuckDuckGo Search** | `npx @modelcontextprotocol/server-duckduckgo` | — | MCPBench/ModelScope (2504.11094), MCP-Bench (2508.20453) | DDG public API; no key needed |
| **Wikipedia** | *(varies by implementation)* | — | MCP-Bench / Accenture (2508.20453) | Wikipedia API is public |
| **DEX Paprika** | `uvx dexpaprika-mcp` | — | MCP-Bench / Accenture (2508.20453) | DexPaprika public API |
| **Math MCP** | *(varies)* | — | MCP-Bench / Accenture (2508.20453) | Local calculations |
| **DVMCP** | HTTP at `dvmcp.co.uk` (port 3001) | — | DVMCP benchmark, arxiv:2505.24367 | Deliberately vulnerable; never expose outside lab |

**Database servers — no MCP-level auth (but connection string needed for DB itself):**

| Server | Package / Run Command | Version | Used In | Notes |
|--------|-----------------------|---------|---------| ------|
| **SQLite** *(archived)* | `npx @modelcontextprotocol/server-sqlite <db.db>` | — | — | Archived; DB file is local — no remote auth |
| **PostgreSQL** *(archived)* | `npx @modelcontextprotocol/server-postgres <conn>` | — | MCPBench/ModelScope (2504.11094) — 80.08% accuracy | Archived; DB connection string = auth at DB layer, not MCP layer |
| **MySQL** *(archived)* | `npx @modelcontextprotocol/server-mysql <conn>` | — | MCPBench/ModelScope (2504.11094) — 56.06% accuracy | Same; auth is DB-level only |
| **Chroma** (local mode) | `uvx chroma-mcp` | ≤ 0.2.28 | MCP Safety Audit (2504.03767) — RADE attacks | Local/ephemeral mode: fully open; cloud needs key |

> **Why databases have no "real" MCP auth:** The MCP layer itself does not require credentials.
> The database connection string is passed at startup (like a CLI argument), not checked per-call by MCP.
> From the proxy's perspective, every tool call arrives unauthenticated at the MCP boundary.

---

## 2. API Key Required — Need One Free/Paid Key

Servers that require an environment variable token but no OAuth browser flow.

| Server | Package / Run Command | Version | Auth Env Var | Used In | Notes |
|--------|-----------------------|---------|--------------|---------|-------|
| **Brave Search** | `npx @modelcontextprotocol/server-brave-search` | 0.6.2 *(archived)* | `BRAVE_API_KEY` | MCPBench/ModelScope (2504.11094) — 46.6%, MCP-Bench (2508.20453) | Free tier available |
| **Tavily** | `npx tavily-mcp` | — | `TAVILY_API_KEY` | MCPBench/ModelScope (2504.11094) — 47.99% accuracy | Free tier available |
| **Exa Search** | `npx exa-mcp-server` | — | `EXA_API_KEY` | MCPBench/ModelScope (2504.11094) — 15.02% accuracy | Free tier |
| **Bing Web Search** | *(varies)* | — | `BING_API_KEY` | MCPBench/ModelScope (2504.11094) — 64.33% (best search accuracy) | ⚠ Retiring August 2026 |
| **Fire Crawl Search** | `npx firecrawl-mcp` | — | `FIRECRAWL_API_KEY` | MCPBench/ModelScope (2504.11094) — 58.33% | Free tier |
| **Google Maps** *(archived)* | `npx @modelcontextprotocol/server-google-maps` | — | `GOOGLE_MAPS_API_KEY` | MCP-Bench / Accenture (2508.20453) | Archived; key still required |
| **NASA Data** | *(varies)* | — | Optional `NASA_API_KEY` | MCP-Bench / Accenture (2508.20453) | `DEMO_KEY` = 30 req/hr; own key = 1,000/hr |
| **Context7** | *(varies)* | — | Optional | MCP-Bench / Accenture (2508.20453) | 60 req/hr without key |
| **OKX Exchange** | *(varies)* | — | 3-part credential | MCP-Bench / Accenture (2508.20453) | Complex auth setup |
| **GitHub MCP** | `docker run ghcr.io/github/github-mcp-server` | v1.0.2 (Apr 2026) | `GITHUB_PERSONAL_ACCESS_TOKEN` | MCP Safety Audit (2504.03767) | PAT = simple; also supports OAuth |
| **Stripe** | `npx @stripe/mcp` | 0.2.4 | `STRIPE_SECRET_KEY` | arxiv:2506.13538 | Test key available in Stripe dashboard |
| **Sentry** | `npx @getsentry/mcp-server-sentry` | — | `SENTRY_AUTH_TOKEN` | — | Free plan exists |

---

## 3. Full OAuth Required — Browser Flow Needed

These require an OAuth browser consent flow before the server is usable.

| Server | Package | Auth Type | Used In | Notes |
|--------|---------|-----------|---------|-------|
| **Google Calendar** | `npx @cocal/google-calendar-mcp` | OAuth 2.0 (Google) | *(prior proxy work)* | Needs GCP project + `gcp-oauth.keys.json` |
| **Google Drive** *(archived)* | `npx @modelcontextprotocol/server-gdrive` | OAuth 2.0 (Google) | — | Same Google Cloud setup as Calendar |
| **Slack** *(archived)* | `npx @modelcontextprotocol/server-slack` | OAuth token | MCP Safety Audit (2504.03767) | `SLACK_BOT_USER_OAUTH_TOKEN` + `SLACK_TEAM_ID` |
| **Atlassian Remote** | `https://mcp.atlassian.com/v1/mcp` | OAuth 2.1 + PKCE | — | Remote HTTP endpoint; SSE deprecated June 30 2026 |
| **Supabase** | `npx @supabase/mcp-server-supabase` | OAuth or PAT | — | v0.5.10 |
| **Reddit** | *(varies)* | OAuth 2.0 client creds | MCP-Bench / Accenture (2508.20453) | App registration needed |
| **WhatsApp** | `github.com/lharries/whatsapp-mcp` | QR scan (session) | Security research (Invariant Labs) | Session persists ~20 days; rug-pull demo target |

---

## 4. Paper ↔ Server Cross-Reference

Which papers tested which servers.

| Paper (arXiv) | Servers Used |
|---------------|-------------|
| **2504.03767** — MCP Safety Audit | Filesystem, Slack, Everything, Chroma |
| **2504.11094** — MCPBench (ModelScope) | Brave Search, DuckDuckGo, Tavily, Exa, Fire Crawl, Bing, MySQL, PostgreSQL |
| **2505.24367** — DVMCP | DVMCP (10 intentional flaws) |
| **2506.13538** — Ecosystem Security Study | 583 community servers scanned (SonarQube + mcp-scan) |
| **2508.13220** — MCPSecBench | Filesystem, Git, Playwright, Azure MCP; CVE-2025-6514 demo |
| **2508.14925** — MCPTox | 45 live servers, 353 tools (mcp.so + mcpservers.cn) |
| **2508.16260** — MCPVerse | 65 servers: filesystem, Git, Yahoo Finance, GeekNews, Amap, Variflight, Excel, code sandbox |
| **2508.20453** — MCP-Bench (Accenture) | BioMCP, Paper Search, Hugging Face, NASA, DEX Paprika, OKX, Math, Time, Wikipedia, Reddit, Google Maps, Context7, NixOS, OSINT |
| **2512.15163** — MCP-SafetyBench | Memory, Filesystem; built on MCP-Universe real servers (245 test cases) |

---

## 5. Additional Servers Found in PDF Papers (Not in Markdown Reviews)

These servers were found by reading the actual PDFs — they did not appear in the markdown benchmark review files.

| Server | Used In (PDF) | Auth | Notes |
|--------|--------------|------|-------|
| **weather_forecast** | Beyond the Protocol (attack demo) | None | Custom demo server; used to show Tool Poisoning Attack on Chengdu weather queries |
| **desktop-commander** | Beyond the Protocol (attack demo) | None | Exposes `read_file_tool`; used in Privacy Steal Task demo |
| **transfer-mcp** | Beyond the Protocol (attack demo) | None | ⚠ Crypto transfer tool (`transfer_tool`); used in Ethereum theft demo — do NOT expose outside lab |
| **Alpaca MCP Server** | AutoMalTool / Compatibility at a Cost | Unknown | 27 tools; tested in red-teaming framework |
| **Weather** (generic) | MPMA (8-server test set) | None | One of 8 servers used in Preference Manipulation Attack evaluation |
| **Markdown** (converter) | MPMA (8-server test set) | None | Markdown conversion; one of 8 servers in MPMA |
| **Installer** | MPMA (8-server test set) | None | Package installation tools; one of 8 servers in MPMA |
| **Hotnews** | MPMA (8-server test set) | None | News retrieval; one of 8 servers in MPMA |
| **Crypto** (data) | MPMA (8-server test set) | None | Cryptocurrency price/data (not transfers); one of 8 MPMA servers |

**MCP clients tested in papers (not servers, but useful for testbed setup):**

| Client | Papers | Version |
|--------|--------|---------|
| Claude Desktop | MCP Safety Audit, MCPSecBench, Beyond the Protocol | 0.8.1 (Safety Audit), 0.12.28 (MCPSecBench) |
| Cursor | MCPSecBench, Beyond the Protocol | v1.2.2 → v2.3.29 |
| Cline | Beyond the Protocol | — |
| Copilot MCP | Beyond the Protocol | — |
| Cherry Studio | Beyond the Protocol | — |

**Papers whose PDFs could not be fully read** (measurement studies — may contain additional server lists):
- `A_Measurement_Study_of_Model_Context_Protocol_Ecosystem.pdf`
- `MCP_Does_Not_Stand_for_Misuse_Cryptography_Protocol_Uncovering_Cryptographic_Misuse_in_MCP_at_Scale.pdf`
- `We_Urgently_Need_Privilege_Management_in_MCP_A_Measurement_of_API_Usage_in_MCP_Ecosystems.pdf`

---

## 7. Recommended Proxy Testbed Stack

Servers you can run **right now** without any credential setup, covering the main attack surfaces
studied in the papers.

| Priority | Server | Why |
|----------|--------|-----|
| 1 | **Filesystem** (≥ 0.6.3) | Most-tested in papers; file read/write/exfiltration scenarios |
| 2 | **Git** (≥ 2025.12.18) | Local repo ops; credential theft scenarios |
| 3 | **Everything** | Reference server for prompt injection and tool poisoning |
| 4 | **Fetch** | Exfiltration vector; high-risk no-auth outbound HTTP |
| 5 | **Memory** | RADE multi-server attack scenarios |
| 6 | **SQLite** | DB query scenarios; no auth at MCP layer |
| 7 | **DVMCP** | All 10 OWASP MCP Top 10 flaws; pre-built attack surface |
| 8 | **Playwright** | Browser automation; lateral movement scenarios |

Add **Brave Search** or **Tavily** (free API key) to cover search-based exfiltration scenarios
from MCPBench paper.
