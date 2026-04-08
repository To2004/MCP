# MCP Server CVE Catalog — Agent→Server Attacks

Comprehensive catalog of publicly disclosed CVEs where **the MCP server is the victim** and the attack vector flows **client → server** (agent, malicious prompt, or network client as the threat source). This matches the thesis threat model: MCP server = protected asset, AI agent / MCP client = threat source. CVEs where a malicious server attacks the client/agent (the inverse direction) are explicitly excluded — see [§ Exclusions](#exclusions) for the list.

This catalog complements [`mcp_server_attack_taxonomy_v2_agent_boundary.md`](mcp_server_attack_taxonomy_v2_agent_boundary.md) — the taxonomy maps attacks to risk-scoring dimensions, while this file is the raw CVE evidence inventory. Cutoff date: 2026-04-05.

## Summary Table

| # | CVE ID | Affected Server | Attack Type | CWE | CVSS | Year |
|---|--------|-----------------|-------------|-----|------|------|
| 1 | CVE-2025-5273 | markdownify-mcp | Arbitrary file read | CWE-22 | — | 2025 |
| 2 | CVE-2025-5276 | markdownify-mcp | SSRF | CWE-918 | — | 2025 |
| 3 | CVE-2025-5277 | aws-mcp-server | Command injection (shell metachars) | CWE-78 | 9.6 | 2025 |
| 4 | CVE-2025-49596 | Anthropic MCP Inspector | Unauthenticated RCE (inspector-proxy) | CWE-306 | — | 2025 |
| 5 | CVE-2025-53109 | Anthropic Filesystem MCP | Symlink bypass → arbitrary R/W → RCE | CWE-59 | 8.4 | 2025 |
| 6 | CVE-2025-53110 | Anthropic Filesystem MCP | Directory-containment / sandbox escape | CWE-22 | 7.3 | 2025 |
| 7 | CVE-2025-53355 | Kubernetes MCP Server | Command injection | CWE-77/78 | — | 2025 |
| 8 | CVE-2025-53372 | node-code-sandbox-mcp | Docker sandbox escape | CWE-269 | — | 2025 |
| 9 | CVE-2025-53967 | Framelink Figma MCP | Command injection (child_process.exec) | CWE-78 | — | 2025 |
| 10 | CVE-2025-54994 | create-mcp-server-stdio | Command injection | CWE-78 | — | 2025 |
| 11 | CVE-2025-59163 | Vet MCP Server | DNS rebinding | CWE-350 | — | 2025 |
| 12 | CVE-2025-65513 | mcp-fetch-server | SSRF (private-IP check bypass) | CWE-918 | 9.3 | 2025 |
| 13 | CVE-2025-66689 | Zen MCP Server | Path traversal | CWE-22 | — | 2025 |
| 14 | CVE-2025-67366 | filesystem-mcp | Path traversal | CWE-22 | — | 2025 |
| 15 | CVE-2025-68143 | Anthropic mcp-server-git | Unrestricted git_init (arbitrary repo path) | CWE-22 | 6.5 | 2025 |
| 16 | CVE-2025-68144 | Anthropic mcp-server-git | Argument injection in git_diff → file overwrite | CWE-88 | 6.3 | 2025 |
| 17 | CVE-2025-68145 | Anthropic mcp-server-git | Path validation bypass | CWE-22 | 6.4 | 2025 |
| 18 | CVE-2025-69256 | Serverless Framework MCP | Command injection (list-projects) | CWE-78 | — | 2025 |
| 19 | CVE-2026-0755 | gemini-mcp-tool | Command injection | CWE-78 | — | 2026 |
| 20 | CVE-2026-0756 | GitHub Kanban MCP Server | RCE via tool interface | CWE-78 | — | 2026 |
| 21 | CVE-2026-23744 | MCPJam Inspector | Unauth RCE (binds 0.0.0.0, no auth) | CWE-306 | 9.8 | 2026 |
| 22 | CVE-2026-25536 | MCP TypeScript SDK | Cross-client data leak (shared transport) | CWE-362/200 | 7.1 | 2026 |
| 23 | CVE-2026-25546 | godot-mcp | Command injection (exec, projectPath) | CWE-78 | — | 2026 |
| 24 | CVE-2026-26118 | Azure MCP Server | SSRF → privilege elevation | CWE-918 | 8.8 | 2026 |
| 25 | CVE-2026-27124 | FastMCP | OAuth proxy confused-deputy | CWE-441 | 8.2 | 2026 |
| 26 | CVE-2026-27825 | mcp-atlassian | Path traversal → arbitrary file write → RCE | CWE-22 | 9.1 | 2026 |
| 27 | CVE-2026-27826 | mcp-atlassian | SSRF (Atlassian URL headers) | CWE-918 | 8.2 | 2026 |
| 28 | CVE-2026-30861 | WeKnora | Command injection (stdio config validation) | CWE-78 | — | 2026 |
| 29 | CVE-2026-32871 | FastMCP OpenAPI Provider | SSRF + path traversal (urljoin) | CWE-918 | 10.0 | 2026 |
| 30 | CVE-2026-33989 | @mobilenext/mobile-mcp | Path traversal (screen-capture saveTo/output) | CWE-22 | 8.1 | 2026 |
| 31 | CVE-2026-34953 | PraisonAI | OAuth token validation bypass | CWE-287 | 9.1 | 2026 |
| 32 | CVE-2026-5322 | mcp-data-vis | SQL injection (create_table tool) | CWE-89 | 7.3 | 2026 |
| 33 | CVE-2026-32211 | Azure MCP Server | Missing auth → information disclosure | CWE-306 | 9.1 | 2026 |
| 34 | CVE-2026-33032 | nginx-ui (MCP endpoint) | Unauthenticated MCP endpoint → nginx takeover | CWE-306 | — | 2026 |
| 35 | CVE-2026-33252 | MCP Go SDK | Cross-site tool execution (CSRF, missing Origin check) | CWE-352 | — | 2026 |
| 36 | CVE-2026-33946 | MCP Ruby SDK | SSE stream hijacking via session ID replay | CWE-384 | — | 2026 |
| 37 | CVE-2026-33980 | adx-mcp-server (Azure Data Explorer) | KQL injection in 3 tools | CWE-89 | 8.3 | 2026 |
| 38 | CVE-2026-34742 | MCP Go SDK | DNS rebinding protection disabled by default | CWE-350 | — | 2026 |
| 39 | CVE-2026-34935 | PraisonAI | OS command injection in MCPHandler.parse_mcp_command() | CWE-78 | — | 2026 |
| 40 | CVE-2026-35394 | @mobilenext/mobile-mcp | Arbitrary Android Intent execution (mobile_open_url) | CWE-74 | — | 2026 |
| 41 | GHSA-wvr4-3wq4-gpc5 | mcp-bridge | Unauthenticated RCE via /bridge endpoint | CWE-78/306 | — | 2026 |
| 42 | GHSA-w2fm-25vw-vh7f | mcp-handler | Tool response leak across concurrent sessions (race) | CWE-362 | — | 2026 |

**Totals:** 42 advisories (40 CVEs + 2 GHSAs without assigned CVE). By type: 12 Command Injection/RCE, 8 Path Traversal, 6 SSRF, 6 Auth/Authz Bypass, 2 SQL/KQL Injection, 2 Sandbox/Network Escape, 2 Data Leak/Session, 2 Protocol (CSRF/DNS-rebind), 1 Intent injection, 1 Session hijack. By year: 18 in 2025, 24 in 2026 (YTD through April 5).

## Detailed Entries

### Command Injection / RCE

**CVE-2025-5277 — aws-mcp-server (CVSS 9.6)**
Fails to sanitize shell metacharacters in CLI commands passed via tool arguments, enabling arbitrary command execution on the server host. The AI agent supplies input → server executes unsanitized shell → host compromise.

**CVE-2025-53355 — Kubernetes MCP Server**
Command injection in tool handlers that construct `kubectl` invocations from agent-controlled parameters without sanitization.

**CVE-2025-53967 — Framelink Figma MCP Server**
The `fetchWithRetry` function builds `curl` commands using unsanitized user input through the `fileKey` parameter, allowing RCE via design-tool interactions.

**CVE-2025-54994 — create-mcp-server-stdio**
Command injection in the MCP server scaffolding CLI; malicious project names reach shell execution during server generation.

**CVE-2025-69256 — Serverless Framework MCP (@serverless/mcp)**
Command injection in the `list-projects` tool — parameter values passed directly to shell without escaping.

**CVE-2026-0755 — gemini-mcp-tool**
Input validation failure reaching command execution.

**CVE-2026-0756 — GitHub Kanban MCP Server**
Remote code execution allowing arbitrary command execution through the MCP tool interface.

**CVE-2026-25546 — godot-mcp**
The `executeOperation` function accepts `projectPath` as user input and passes it directly to `exec()`, enabling arbitrary command execution.

**CVE-2026-30861 — WeKnora**
Unauthenticated command injection flaw within WeKnora's MCP stdio configuration validation.

**CVE-2026-34935 — PraisonAI**
OS command injection in `MCPHandler.parse_mcp_command()` — agent-controlled MCP command strings reach shell execution without sanitization.

**GHSA-wvr4-3wq4-gpc5 — mcp-bridge**
Unauthenticated remote OS command execution via the `/bridge` endpoint; any network client can trigger arbitrary command execution on the host.

### SQL / Query-Language Injection

**CVE-2026-5322 — mcp-data-vis (CVSS 7.3)**
The `create_table` tool in `src/servers/database/server.js` embeds attacker-controlled schema values directly into CREATE TABLE statements via `db.exec()` without parameterization, enabling arbitrary SQL against the SQLite database.

**CVE-2026-33980 — adx-mcp-server / Azure Data Explorer MCP (CVSS 8.3)**
KQL injection in `get_table_schema`, `sample_table_data`, and `get_table_details` tools; `table_name` is interpolated via f-strings into KQL queries, letting a prompt-injected agent execute arbitrary Kusto queries against the cluster.

### Path Traversal / Unauthorized File Access

**CVE-2025-5273 — markdownify-mcp**
Arbitrary file read via insufficient path validation — agent can supply any absolute path and extract file contents.

**CVE-2025-53109 — Anthropic Filesystem MCP Server (CVSS 8.4, "EscapeRoute")**
Symlink following allows reading/writing files outside the allowed directories, enabling arbitrary file access → code execution. Patched in npm package `2025.7.1` / `0.6.3`.

**CVE-2025-53110 — Anthropic Filesystem MCP Server (CVSS 7.3, "EscapeRoute")**
Directory containment bypass — `--repository` boundary not enforced, enabling sandbox escape. Same patch as 53109.

**CVE-2025-66689 — Zen MCP Server**
Path traversal via unsanitized path arguments passed to file operations.

**CVE-2025-67366 — filesystem-mcp**
Input validation failure allowing path traversal on filesystem operations.

**CVE-2025-68143 — Anthropic mcp-server-git (CVSS 6.5)**
`git_init` fails to validate repository boundary, allowing repo creation at arbitrary filesystem locations (e.g. turning `~/.ssh` into a git repo).

**CVE-2025-68145 — Anthropic mcp-server-git (CVSS 6.4)**
Path validation bypass — `--repository` boundary not enforced on tool arguments.

**CVE-2026-27825 — mcp-atlassian (CVSS 9.1, 4M+ downloads)**
Missing directory confinement in `download_attachment` / `download_content_attachments` tools; attacker-controlled target path writes arbitrary files. When HTTP transport is bound to 0.0.0.0 without auth, unauthenticated attackers can overwrite `~/.bashrc` or `~/.ssh/authorized_keys` → persistent RCE.

**CVE-2026-33989 — @mobilenext/mobile-mcp (CVSS 8.1)**
`saveTo` and `output` parameters in screen-capture / recording tools passed directly to filesystem operations without validation — write outside workspace.

### Server-Side Request Forgery (SSRF)

**CVE-2025-5276 — markdownify-mcp**
SSRF via URL fetching without destination validation — server makes arbitrary outbound requests on behalf of the agent.

**CVE-2025-65513 — mcp-fetch-server (CVSS 9.3)**
`is_ip_private()` fails to properly validate private IP addresses, enabling SSRF to internal services (cloud metadata, LAN).

**CVE-2026-26118 — Azure MCP Server (CVSS 8.8)**
SSRF enabling privilege elevation on Azure; patched in March 2026 security update.

**CVE-2026-27826 — mcp-atlassian (CVSS 8.2)**
SSRF via Atlassian URL headers. Chained with CVE-2026-27825 for unauthenticated RCE from the LAN.

**CVE-2026-32871 — FastMCP OpenAPI Provider (CVSS 10.0 CRITICAL)**
`_build_url()` substitutes path parameters into URL templates without URL-encoding; `urljoin()` interprets `../` as traversal, enabling authenticated SSRF that inherits the provider's credentials.

### Authentication & Authorization

**CVE-2025-49596 — Anthropic MCP Inspector**
Unauthenticated RCE via the inspector-proxy architecture; arbitrary commands on developer machines running the inspector.

**CVE-2026-23744 — MCPJam Inspector (CVSS 9.8)**
HTTP server binds 0.0.0.0 by default with no authentication on server-management endpoint; crafted HTTP request installs malicious MCP server → RCE. Affects ≤ 1.4.2, fixed in 1.4.3.

**CVE-2026-27124 — FastMCP (CVSS 8.2)**
OAuthProxy does not validate user consent on the authorization code callback; combined with GitHub's skip-consent behavior, enables a Confused Deputy (CWE-441) attack.

**CVE-2026-34953 — PraisonAI (CVSS 9.1)**
OAuth token validation is fundamentally broken — any attacker providing an arbitrary Bearer token gains full authenticated access to all registered tools and agent capabilities. Fixed in 4.5.97.

**CVE-2026-32211 — Azure MCP Server (CVSS 9.1)**
Missing authentication for a critical function — attackers without valid credentials can read configuration details, API keys, authentication tokens, and project data. Disclosed April 3, 2026; mitigation guidance published by Microsoft, patch pending.

**CVE-2026-33032 — nginx-ui MCP endpoint (Critical)**
Two HTTP endpoints (`/mcp` and `/mcp_message`) exposed. The `/mcp_message` endpoint applies only IP-whitelisting; the default whitelist is empty, which the middleware treats as "allow all". Any network attacker can invoke all MCP tools including nginx restart/reload and configuration file create/modify/delete → full nginx takeover. Affects versions ≤ 2.3.5.

### Sandbox / Containment Escape

**CVE-2025-53372 — node-code-sandbox-mcp**
Docker sandbox escape — allows the sandboxed code execution to break out to the host.

**CVE-2025-59163 — Vet MCP Server**
DNS rebinding attack against the MCP server's network boundary.

**CVE-2026-34742 — MCP Go SDK**
DNS rebinding protection disabled by default on localhost-bound HTTP servers (all versions before 1.4.0). Attackers on the same LAN as a developer can use DNS rebinding to reach the MCP server through a browser. Fixed in 1.4.0.

**CVE-2026-35394 — @mobilenext/mobile-mcp**
`mobile_open_url` tool allows arbitrary Android Intent execution; agent-controlled URL parameter is passed to `Intent.parseUri()`, enabling launch of arbitrary activities/services with attacker-chosen extras.

### Session / Data Isolation / Protocol

**CVE-2026-25536 — MCP TypeScript SDK (CVSS 7.1)**
Shared `McpServer`/transport instance reuse across multiple client connections in stateless `StreamableHTTPServerTransport` deployments causes cross-client response leakage. Affects versions 1.10.0 through 1.25.3. The most-cited protocol-SDK-level CVE for multi-tenant data-leakage risk scoring.

**CVE-2026-33252 — MCP Go SDK (CSRF)**
Streamable HTTP transport accepted browser-generated cross-site POST requests without validating the `Origin` header or requiring `Content-Type: application/json`. In stateless/sessionless deployments without Authorization, any website could trigger tool execution on a local MCP server. Fixed in 1.4.1.

**CVE-2026-33946 — MCP Ruby SDK**
`streamable_http_transport.rb` insufficient session binding: an attacker obtaining a valid session ID can hijack the victim's SSE stream and intercept all real-time data. Fixed in 0.9.2.

**GHSA-w2fm-25vw-vh7f — mcp-handler (npm)**
Race condition in concurrent client session handling — tool responses can leak across concurrent sessions, same class of bug as CVE-2026-25536 but in the `mcp-handler` npm package.

## Mapping to Risk-Scoring Dimensions

The CVEs map to the v2 agent-boundary taxonomy dimensions ([reference](mcp_server_attack_taxonomy_v2_agent_boundary.md)) as follows:

| Dimension | Matching CVEs |
|-----------|---------------|
| 1.1 Arbitrary Code Execution | 5277, 49596, 23744, 27825 (chained), 33032 |
| 1.3 Command Injection | 5277, 53355, 53967, 54994, 69256, 0755, 0756, 25546, 30861, 34935, mcp-bridge |
| 2.1 Unauthorized File Read | 5273, 53109, 53110, 68143, 68145, 66689, 67366 |
| 2.2 Unauthorized File Write | 68144, 53109, 27825, 33989 |
| 2.3 SSH Key / Credential Injection | 27825 (~/.ssh/authorized_keys demo), 32211 (Azure creds) |
| 7.1 Sandbox Escape | 53109, 53110, 53372 |
| 8.1 SSRF | 5276, 65513, 26118, 27826, 32871 |
| 8.3 Protocol-Level Exploitation | 25536, 33252, 33946, 34742, mcp-handler |
| 10.2 Session Abuse | 25536, 33946, mcp-handler |
| 16.2 Multi-Tenant Data Leakage | 25536, 32211, mcp-handler |
| **New — SQL/Query-Language Injection** | 5322, 33980 |
| **New — Auth Bypass** | 49596, 23744, 27124, 34953, 32211, 33032 |
| **New — CSRF / Browser-Reachable Tools** | 33252, 34742, 59163 |
| **New — Intent / Mobile-URI Injection** | 35394 |

The 6 authentication-bypass CVEs and 5 protocol-level CVEs confirm two taxonomy gaps — v2 currently underweights **"Dimension 17 — Authentication / Authorization Failure"** and lacks a dedicated **protocol/SDK-layer** dimension (currently subsumed under 8.3). Two SQL/KQL-injection CVEs and an Android Intent-injection CVE are entirely unrepresented in the existing v2 dimensions and warrant a new Injection family.

## Exclusions — CVEs Where the Server is the Attacker

These CVEs exist in the MCP ecosystem but flow **server → client** (malicious server attacks the agent/client) and are therefore **out of scope** for this thesis:

| CVE ID | Component | Why Excluded |
|--------|-----------|--------------|
| CVE-2025-6514 | mcp-remote (client proxy, CVSS 9.6) | Malicious remote server sends booby-trapped `authorization_endpoint` → RCE on client machine. Direction: server → client. |
| CVE-2025-59944 | Cursor IDE | Cursor is the MCP client; file-protection bypass affects the client. |
| CVE-2025-59536 | Claude Code | Client-side RCE via project-file parsing. |
| CVE-2026-21518 | VS Code `mcp.json` handling | VS Code is the MCP client; command injection on client. |
| CVE-2026-21852 | Claude Code | MCP-server-approval bypass on client. |
| CVE-2026-22785 | Orval MCP Client | Client-side code injection via OpenAPI `summary` fields. |
| CVE-2026-23947 | Orval MCP Client | Client-side code injection via `x-enumDescriptions` fields. |

Reason for exclusion: the thesis models the agent as the threat source and the server as the protected asset. Protecting clients from malicious servers is the inverse problem and is handled by a different threat model (e.g. tool-description sanitization, client-side sandboxing).

## Coverage Notes

- **Database snapshot:** The Vulnerable MCP Project database currently lists 13 Critical, 30 High, 6 Medium, and 1 Informational severity entries as of early 2026; this catalog covers the CVE-assigned subset.
- **Pattern concentration:** 43% of documented MCP-server CVEs involve command injection; 82% of surveyed MCP implementations use file operations vulnerable to path traversal.
- **Ecosystem scale:** BlueRock's analysis of 7,000+ MCP servers found latent SSRF exposure in ~36.7%.
- **Auth gap:** A survey of 554 network-exposed MCP servers found 37% had no authentication.
- **Source of truth for updates:** https://vulnerablemcp.info/ — live database, re-check before thesis submission.

## Sources

- [The Vulnerable MCP Project — Database](https://vulnerablemcp.info/)
- [The Vulnerable MCP Project — Taxonomy](https://vulnerablemcp.info/taxonomy.html)
- [MCPJam Inspector RCE (CVE-2026-23744) entry](https://vulnerablemcp.info/vuln/cve-2026-23744-mcpjam-inspector-rce.html)
- [MCP Security 2026: 30 CVEs in 60 Days — heyuan110](https://www.heyuan110.com/posts/ai/2026-03-10-mcp-security-2026/)
- [A Timeline of MCP Security Breaches — authzed](https://authzed.com/blog/timeline-mcp-breaches)
- [Classic Vulnerabilities Meet AI Infrastructure — Endor Labs](https://www.endorlabs.com/learn/classic-vulnerabilities-meet-ai-infrastructure-why-mcp-needs-appsec)
- [EscapeRoute: CVE-2025-53109 & 53110 — Cymulate](https://cymulate.com/blog/cve-2025-53109-53110-escaperoute-anthropic/)
- [Three Flaws in Anthropic MCP Git Server — The Hacker News](https://thehackernews.com/2026/01/three-flaws-in-anthropic-mcp-git-server.html)
- [CVE-2026-27825 mcp-atlassian RCE & SSRF — Arctic Wolf](https://arcticwolf.com/resources/blog-uk/cve-2026-27825-critical-unauthenticated-rce-and-ssrf-in-mcp-atlassian/)
- [MCP fURI: SSRF in Microsoft MarkItDown MCP — BlueRock](https://www.bluerock.io/post/mcp-furi-microsoft-markitdown-vulnerabilities)
- [CVE-2026-26118 Azure MCP SSRF — TheHackerWire](https://www.thehackerwire.com/azure-mcp-server-ssrf-for-privilege-elevation-cve-2026-26118/)
- [CVE-2026-34953 PraisonAI Auth Bypass — TheHackerWire](https://www.thehackerwire.com/praisonai-authentication-bypass-grants-full-access-cve-2026-34953/)
- [CVE-2026-32871 FastMCP OpenAPI SSRF — GitLab Advisories](https://advisories.gitlab.com/pkg/pypi/fastmcp/CVE-2026-32871/)
- [CVE-2026-27124 FastMCP OAuth Proxy — GitLab Advisories](https://advisories.gitlab.com/pkg/pypi/fastmcp/CVE-2026-27124/)
- [CVE-2026-33989 @mobilenext/mobile-mcp — GitLab Advisories](https://advisories.gitlab.com/pkg/npm/@mobilenext/mobile-mcp/CVE-2026-33989/)
- [CVE-2025-6514 mcp-remote RCE — JFrog](https://jfrog.com/blog/2025-6514-critical-mcp-remote-rce-vulnerability/)
- [Microsoft & Anthropic MCP Servers at Risk — Dark Reading](https://www.darkreading.com/application-security/microsoft-anthropic-mcp-servers-risk-takeovers)
- [Seven MCP CVEs in One Month — dev.to/kai_security_ai](https://dev.to/kai_security_ai/seven-mcp-cves-in-one-month-the-complete-map-1am5)
- [CVE-2026-25536 MCP TypeScript SDK — cvefeed.io](https://cvefeed.io/vuln/detail/CVE-2026-25536)
- [CVE-2026-32211 Azure MCP Missing Auth — cvefeed.io](https://cvefeed.io/vuln/detail/CVE-2026-32211)
- [CVE-2026-34742 MCP Go SDK DNS Rebinding — GitLab Advisories](https://advisories.gitlab.com/pkg/golang/github.com/modelcontextprotocol/go-sdk/CVE-2026-34742/)
- [CVE-2026-33032 nginx-ui MCP Takeover — GitLab Advisories](https://advisories.gitlab.com/pkg/golang/github.com/0xjacky/nginx-ui/CVE-2026-33032/)
- [CVE-2026-33980 adx-mcp-server KQL Injection — GitLab Advisories](https://advisories.gitlab.com/pkg/pypi/adx-mcp-server/CVE-2026-33980/)
- [CVE-2026-33946 MCP Ruby SDK Session Hijack — GitLab Advisories](https://advisories.gitlab.com/pkg/gem/mcp/CVE-2026-33946/)
- [CVE-2026-33252 MCP Go SDK CSRF — CIRCL Vulnerability Lookup](https://vulnerability.circl.lu/vuln/cve-2026-33252)
- [CVE-2026-5322 mcp-data-vis SQL Injection — ThreatInt](https://cve.threatint.eu/CVE/CVE-2026-5322)
- [GitHub Advisory Database (MCP filter)](https://github.com/advisories?query=mcp+server&type=reviewed)
