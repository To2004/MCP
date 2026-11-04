# MCP Risk-Scoring Systems: Industry and Open-Source Catalogue (as of 2026-11-04)

This file lists the real-world systems that give MCP servers, tools, calls or agents a risk score, grade or risk level, with the scoring method each one documents. It is meant for comparison with our framework, which treats the MCP server as the protected asset, the calling agent as the threat, and scores both static (per tool or input) and dynamic (per call, plus a per-agent behaviour multiplier) risk.

## Q1. Which systems exist: name, vendor, URL, licence, first release, status

### Takeaway

I found 35 named products and projects (scanners, gateways, registries, vendor platforms), 6 standards or frameworks, and 14 smaller open-source or niche scoring tools. Invariant Labs (maker of MCP-Scan) was bought by Snyk on 2025-06-24, and MCP-Scan is now "Snyk Agent Scan". agentgateway moved to the Linux Foundation on 2025-08-25. Most products launched between April and October 2025, and several have changed a lot during 2026.

### Cited Findings

#### A. Static scanners and vendor posture platforms

| # | System | Vendor / maintainer | Licence | First release / key dates | Status (Nov 2026) | Source |
|---|---|---|---|---|---|---|
| 1 | Snyk Agent Scan (was Invariant MCP-Scan) | Snyk (bought Invariant Labs AG, announced 2025-06-24, price undisclosed) | Apache-2.0 | MCP-Scan was already scanning all of Smithery by 2025-04-24. v0.6 uses the `2026-07-10` analysis API | Active. v0.5.x is planned for deprecation. The README says CLI output is "experimental" | [SiliconANGLE](https://siliconangle.com/2025/06/24/snyk-acquires-invariant-labs-expand-ai-agent-security-capabilities/); [Invariant/Smithery](https://invariantlabs.ai/blog/smithery-mcp-scan); [README](https://github.com/snyk/agent-scan/); [risks.md](https://github.com/snyk/agent-scan/blob/HEAD/docs/risks.md) |
| 2 | Snyk Evo "Agent Supply Chain Security" | Snyk | Commercial | Not stated | Active (enterprise) | [Snyk docs](https://docs.snyk.io/agent-security/evo-by-snyk/agentic-development-security-ads/agent-supply-chain-security) |
| 3 | Cisco AI Defense MCP Scanner | Cisco AI Defense | Apache-2.0 | Repo created 2025-09-24 | Active, about 1.1k stars. Supports MCP protocol `2026-07-28` | [GitHub](https://github.com/cisco-ai-defense/mcp-scanner/) |
| 4 | Enkrypt AI MCP Scan | Enkrypt AI | Commercial web service (free scan, report sent by email) | Not stated | Active | [Enkrypt](https://enkryptai.com/mcp-scan) |
| 5 | Akto MCP Security (Akto Argus) | Akto | Commercial (paid feature) | Not stated | Active | [Akto docs](https://docs.akto.io/mcp-security); [risk score](https://ai-security-docs.akto.io/akto-argus-agentic-ai-security-for-homegrown-ai/agentic-ai-discovery/concepts/risk-score) |
| 6 | Harness AI Security "MCP Risk Score" | Harness | Commercial | Not stated. Update log entry dated Oct 2026 | Active | [Harness docs](https://developer.harness.io/ai-security/mcp-risk-score) |
| 7 | Wallarm "Endpoint and MCP Primitive Risk Score" | Wallarm | Commercial | Not stated | Active | [Wallarm docs](https://docs.wallarm.com/api-discovery/risk-score/) |
| 8 | MCP-Shield (aaronlab) | Individual (aaronlab) | Open source (licence not checked) | Not stated | Active | [GitHub](https://github.com/aaronlab/mcp-shield) |
| 9 | CSA RiskRubric MCP Scanner | Cloud Security Alliance. The RiskRubric framework was launched by CSA and Noma Security in 2025 | Not stated | Research note dated 2026-03-27 | "Status: draft" | [CSA Labs](https://labs.cloudsecurityalliance.org/agentic/csa-research-note-riskrubric-mcp-scanner-spec-20260327/) |
| 10 | PointGuard AI MCP server grades | PointGuard AI | Commercial | Study published 2026-07-14 (36,527 GitHub servers) | Active | [PointGuard blog](https://www.pointguardai.com/blog/we-tested-36-500-public-mcp-servers-two-thirds-arent-safe-for-enterprise-use) |
| 11 | Noma Security | Noma Security | Commercial | MCP research reported 2026-05-05 | Active. No documented MCP score in the product | [Help Net Security](https://helpnetsecurity.com/2026/05/05/ai-agent-security-skills-blind-spots) |
| 12 | Zenity (MCP use case) | Zenity | Commercial | 2025 MCP Server Security Report | Active. Marketing pages only | [Zenity MCP](https://www.zenity.io/use-cases/risk-type/mcp); [report](https://zenity.io/resources/white-papers/mcp-server-security-report) |
| 13 | Astrix MCP Secret Wrapper and research | Astrix Security | Wrapper is open source. Agent Control Plane is commercial | "State of MCP Server Security 2025" | Active | [Astrix news](https://astrix.security/learn/news/astrix-researchers-uncover-credential-risk-in-the-majority-of-mcp-servers/) |
| 14 | Wiz MCP research | Wiz | Research only (no MCP scoring product found) | Briefing updated 2025-04-21 | Research | [Wiz briefing](https://www.wiz.io/blog/mcp-security-research-briefing) |

#### B. Gateways, proxies and wrappers (runtime)

| # | System | Vendor / maintainer | Licence | First release / key dates | Source |
|---|---|---|---|---|---|
| 15 | Invariant Guardrails and Invariant Gateway | Invariant Labs, now Snyk | Apache-2.0 | Released before the June 2025 acquisition | [GitHub](https://github.com/invariantlabs-ai/invariant) |
| 16 | Lasso MCP Gateway | Lasso Security | MIT | Repo created 2025-04-14. v1.1.0 added the Security Scanner | [GitHub](https://github.com/lasso-security/mcp-gateway); [releases](https://github.com/lasso-security/mcp-gateway/releases) |
| 17 | Enkrypt Secure MCP Gateway | Enkrypt AI | Unclear: PyPI lists Apache-2.0 core plus proprietary terms | PyPI v2.1.8 | [GitHub](https://github.com/EnkryptAI/secure-mcp-gateway); [PyPI](https://pypi.org/project/secure-mcp-gateway/) |
| 18 | mcp-context-protector | Trail of Bits | Open source | Beta announced 2025-07-28 | [ToB blog](https://blog.trailofbits.com/2025/07/28/we-built-the-security-layer-mcp-always-needed/); [GitHub](https://github.com/trailofbits/mcp-context-protector) |
| 19 | Docker MCP Gateway | Docker | Open source | Release date not checked | [security.md](https://github.com/docker/mcp-gateway/blob/main/docs/security.md); [CLI ref](https://docs.docker.com/reference/cli/docker/mcp/gateway/run/) |
| 20 | Microsoft MCP Gateway (Kubernetes) | Microsoft | MIT (per a secondary source) | Not checked | [DeepWiki](https://deepwiki.com/microsoft/mcp-gateway/2.1-overall-architecture); [MintMCP (secondary)](https://www.mintmcp.com/blog/microsoft-mcp-gateway-azure-api-management) |
| 21 | Azure API Management for MCP | Microsoft | Commercial | Not checked | [MS Learn](https://learn.microsoft.com/en-us/azure/api-management/mcp-server-overview) |
| 22 | Pomerium (MCP support) | Pomerium | Open-core | Not checked | [Pomerium MCP](https://www.pomerium.com/docs/capabilities/mcp) |
| 23 | Cloudflare MCP server portals | Cloudflare | Commercial (Zero Trust) | Announced 2025-08-26. GA 2026-09-24 | [blog](https://blog.cloudflare.com/zero-trust-mcp-server-portals/); [GA changelog](https://developers.cloudflare.com/changelog/post/2026-09-24-mcp-portals-ga/) |
| 24 | agentgateway | Created by Solo.io. Linux Foundation project since 2025-08-25 | Open source | 2025-08-25 (LF) | [LF press](https://www.linuxfoundation.org/press/linux-foundation-welcomes-agentgateway-project-to-accelerate-ai-agent-adoption-while-maintaining-security-observability-and-governance) |
| 25 | Kong AI MCP Proxy plugin | Kong | Commercial (AI Gateway Enterprise) | Kong Gateway 3.12+. Claim mapping in 3.14+ | [Kong docs](https://developer.konghq.com/plugins/ai-mcp-proxy/) |
| 26 | Prisma AIRS MCP threat detection, pan-mcp-relay, Prisma AIRS MCP Server | Palo Alto Networks | Commercial. pan-mcp-relay is on GitHub | pan-mcp-relay 2025-07-23. MCP Threats Detection Oct 2025 (updated May 2026). Cortex AES integration 2026-09-25 | [PANW Oct 2025](https://docs.paloaltonetworks.com/ai-runtime-security/new-features/by-date/prisma-airs/october-2025); [pan-mcp-relay](https://github.com/PaloAltoNetworks/pan-mcp-relay); [PANW blog](https://www.paloaltonetworks.com/blog/ai-security/securing-the-ai-coding-frontier-prisma-airs-agentic-endpoint-security/) |
| 27 | ToolHive | Stacklok | Apache-2.0 | Not checked | [docs](https://docs.stacklok.com/toolhive/guides-cli/custom-permissions); [GitHub](https://github.com/stacklok/toolhive) |
| 28 | Golf Firewall | Golf (golf.dev). Also maintains the open-source golfMCP framework | Firewall licence not stated | Not stated | [Golf docs](https://docs.golf.dev/golf-firewall) |
| 29 | Operant AI MCP Gateway (part of AI Gatekeeper) | Operant AI | Commercial | Announced 2025-06-16. AI Gatekeeper trust scores announced 2025-04-16 | [SiliconANGLE](https://siliconangle.com/2025/06/16/operant-ai-expands-gatekeeper-platform-mcp-gateway-ai-runtime-security) |
| 30 | Amazon Bedrock AgentCore Gateway with Policy (Cedar) | AWS | Commercial | Policy GA 2026-03-03 (per a third-party guide) | [AWS docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-getting-started.html); [Konishi guide](https://hidekazu-konishi.com/entry/amazon_bedrock_agentcore_policy_implementation_guide.html) |
| 31 | Google Cloud Agent Gateway and Model Armor for MCP | Google Cloud | Commercial | Agent Gateway announced at Next '26 | [Google MCP overview](https://docs.cloud.google.com/mcp/overview?hl=th); [Next '26 blog](https://cloud.google.com/blog/products/identity-security/next26-redefining-security-for-the-ai-era-with-google-cloud-and-wiz) |

#### C. Registries and directories

| # | System | What it gives | Source |
|---|---|---|---|
| 32 | Smithery | Since 2025-04-24, every listed server is scanned with Invariant MCP-Scan and results show on its page. No numeric grade is described | [Invariant blog](https://invariantlabs.ai/blog/smithery-mcp-scan) |
| 33 | Glama | Quality, security, licence and maintenance grades. Per-tool Tool Definition Quality Score (TDQS) | [Glama score page](https://glama.ai/mcp/servers/mnott/Hook/score) |
| 34 | Official MCP Registry (registry.modelcontextprotocol.io) | Preview. Namespace-ownership verification only | [MCP registry about](https://modelcontextprotocol.io/registry/about) |
| 35 | MCP Market and mcp.so | No security score found. MCP Market's "Official" badge comes from publisher evidence and is explicitly not a security review (per a secondary source) | [Apideck (secondary)](https://www.apideck.com/blog/mcp-server-directories.md) |

#### D. Standards and frameworks

| # | Document | Owner | Date / status | Source |
|---|---|---|---|---|
| 36 | OWASP MCP Top 10 (2025) | OWASP | In "Phase 3 – Beta Release and Pilot Testing" | [OWASP](https://owasp.org/www-project-mcp-top-10/) |
| 37 | OWASP Top 10 for Agentic Applications (ASI01–ASI10) | OWASP GenAI Security Project | Called the "2026" edition. I read only secondary write-ups | [Descope (secondary)](https://www.descope.com/blog/post/owasp-agentic-top-10-identity); [HUMAN (secondary)](https://www.humansecurity.com/learn/blog/owasp-top-10-agentic-applications/) |
| 38 | CoSAI "Model Context Protocol Security" white paper | Coalition for Secure AI (OASIS) | PDF dated 2026-01-08 | [CoSAI PDF](https://www.coalitionforsecureai.org/wp-content/uploads/2026/03/model-context-protocol-security-1.pdf) |
| 39 | CSA MAESTRO threat-modelling framework | Cloud Security Alliance (Ken Huang) | Feb 2025 | [CSA](https://cloudsecurityalliance.org/articles/agentic-ai-threat-modeling-framework-maestro); [GitHub](https://github.com/CloudSecurityAlliance/MAESTRO) |
| 40 | MCP specification "Security Best Practices" | MCP maintainers | Current page references spec `2026-07-28` | [modelcontextprotocol.io](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices) |
| 41 | NIST COSAiS (SP 800-53 overlays for single- and multi-agent AI) and CAISI agent-hijacking evaluations | NIST | In development. May 2026 working session. RFI drew over 500 responses | [NIST NCCoE slides](https://www.nccoe.nist.gov/sites/default/files/2026-05/Cyber-AI-Profile-Working-Session-Extending-Tech-Content-Slides-Slido.pdf) |

#### E. Smaller open-source or niche scorers (14)

| # | Tool | One-line scoring summary | Source |
|---|---|---|---|
| 42 | Canopii CLI and Canopii Trust Index | Deterministic 0–100 score with A–F grade from about 29 controls in 6 domains | [GitHub](https://github.com/canopii-dev/canopii-cli) |
| 43 | mcp-security-audit (LuciferForge) | Starts at 100 and deducts per finding. Grades A–F | [GitHub](https://github.com/LuciferForge/mcp-security-audit) |
| 44 | AgentsID scanner | Starts at 100. Deductions are normalised by tool count and capped | [GitHub](https://github.com/AgentsID-dev/agentsid-scanner) |
| 45 | MCPWatch | 10 checks "derived from OWASP MCP Top 10". A–F grade and public leaderboard | [GitHub](https://github.com/lazymac2x/mcpwatch) |
| 46 | MCTS (Model Context Threat Scanner) | Legacy 0–100 score plus v2 "Absolute Risk" and "Risk Index" | [GitHub](https://github.com/MCP-Audit/MCTS) |
| 47 | mcptrustchecker | "Capability-Flow Trust Model". A–F Trust Score | [site](https://mcptrustchecker.com/scan) |
| 48 | mcpaudit / AxioRank | RISK 0–100 with an ALLOW/DENY verdict. Hosted AxioRank runtime claims a tamper-evident audit log | [GitHub](https://github.com/AxioRank/mcpaudit) |
| 49 | MCP Doctor | Weighted 0–100 quality score | [GitHub](https://github.com/xlyoung/mcp-doctor) |
| 50 | MCPSense | Starts at 100 and subtracts severity weights | [GitHub](https://github.com/fayzkk889/MCPSense) |
| 51 | MCPGuard (PyPI) | OWASP MCP Top 10 configuration checks, runtime middleware, SARIF output | [PyPI](https://pypi.org/project/mcpguard/) |
| 52 | HarrisonCN/mcp-gateway v6.6.0 | Per-client EWMA traffic baseline anomaly detection | [PR #87](https://github.com/HarrisonCN/mcp-gateway/pull/87) |
| 53 | mTrust | Commercial claim: per-agent behaviour baselines and per-call trust score | [mTrust](https://www.modeltrust.io/) |
| 54 | TrueFoundry MCP Gateway | z-score anomaly threshold that quarantines agent access | [TrueFoundry blog](https://www.truefoundry.com/blog/claude-code-enterprise-mcp-gateway) |
| 55 | Boomi MCP Gateway | Search snippet only: an LLM audits tool definitions and "feeds its findings directly into the scoring engine" | [Boomi blog](https://boomi.com/ja/blog/mcp-risk-analysis-attack-vectors-owasp-guidance/) |

### Inferences

- The market splits into three groups. Supply-chain scanners grade servers before install. Identity-aware gateways make allow/deny decisions on each call. Registries attach grades to listings. Only a few systems (Harness, Akto, Wallarm, partly Golf and Operant) score the organisation's own MCP tools as assets.
- Many A–F graders appeared in 2026 (rows 42–50). None appears to be peer-reviewed, and they do not share a common scale.

### Gaps

- First-release dates for Docker MCP Gateway, Microsoft MCP Gateway, Pomerium MCP support, ToolHive, Enkrypt MCP Scan, Akto MCP, Harness and Wallarm MCP scoring were not checked.
- The date MCP-Scan was renamed to Agent Scan is not in the README I read. One secondary source mentions a v0.4.13 release in April 2026 under the new name.
- I could not confirm the GitHub MCP Registry (github.com/mcp) separately from the official registry, so it is not catalogued.
- The well-known "MCP-Shield" by riseandignite (npm `mcp-shield`) was not checked in this pass. Only the aaronlab project of the same name was read.
- I did not check whether Google's acquisition of Wiz has closed, or what Wiz MCP products exist after it. Only Wiz research pages were found.

## Q2. What each system scores, when, and what it outputs

### Takeaway

Static scanners score a **server** (and sometimes a **tool**) once, before install or in CI, and output a severity, a 0–1000 or 0–100 score, or a letter grade. Runtime gateways evaluate each **call** but mostly output **allow/deny** (or redact/quarantine), not a number. Very few systems score the **agent or identity**, and none of the major vendors documents a per-agent score.

### Cited Findings

#### Static: server or tool level

| System | Unit scored | When | Output | Source |
|---|---|---|---|---|
| Snyk Agent Scan v0.6+ | Server (named risk indicators list affected tools) and skills | Scan, CI, or background MDM | Score 0–1000, currently four levels: 100 Low, 300 Medium, 600 High, 1000 Critical. CI exit status set by `--ignore-risks` | [risks.md](https://github.com/snyk/agent-scan/blob/HEAD/docs/risks.md); [scanning.md](https://github.com/snyk/agent-scan/blob/main/docs/scanning.md) |
| Snyk Agent Scan v0.5.x | Server and tool | Scan | Issue codes (for example W015–W020) with severity labels | [issue-codes.md](https://github.com/snyk/agent-scan/blob/main/docs/issue-codes.md) |
| Snyk Evo Agent Supply Chain Security | Each MCP server and skill on a fleet | Continuous. Stdio servers are matched to a Snyk catalog of servers Snyk assesses regularly, without starting them | Risk indexes 0–1,000. Default policy raises an issue at 600 or above (High or Critical) | [Snyk docs](https://docs.snyk.io/agent-security/evo-by-snyk/agentic-development-security-ads/agent-supply-chain-security) |
| Cisco MCP Scanner | Each tool, prompt, resource and server instruction. Also source code, packages and binaries | Scan or REST API | Per tool: `is_safe`, plus a per-analyzer severity of HIGH, MEDIUM, LOW, INFO, SAFE or UNKNOWN, mapped to Cisco AI taxonomy IDs (for example AITech-9.1) | [GitHub](https://github.com/cisco-ai-defense/mcp-scanner/); [API ref](https://github.com/cisco-ai-defense/mcp-scanner/tree/main/docs/api-reference.md); [DeepWiki](https://deepwiki.com/cisco-ai-defense/mcp-scanner/4.1-baseanalyzer-and-securityfinding) |
| Enkrypt MCP Scan | Server (GitHub repo, npm package or remote endpoint) | One-off scan | Emailed report with "severity scores, impact analysis, and fix recommendations" | [Enkrypt](https://enkryptai.com/mcp-scan) |
| Akto | Each MCP endpoint, agent component and collection | Continuous discovery | Risk score capped at 5 | [Akto](https://ai-security-docs.akto.io/akto-argus-agentic-ai-security-for-homegrown-ai/agentic-ai-discovery/concepts/risk-score) |
| Harness | Each discovered MCP **tool** | Discovery | 0–10 score from a likelihood × impact lookup table, which sets a severity | [Harness](https://developer.harness.io/ai-security/mcp-risk-score) |
| Wallarm | Endpoint or "MCP primitive" | API discovery | 1–10. Levels: 1–3 Low, 4–7 Medium, 8–10 High | [Wallarm](https://docs.wallarm.com/api-discovery/risk-score/) |
| Lasso MCP Gateway scanner | Server | Before the server is loaded | Reputation score 0–100. Server marked "blocked" if below 30. Status written into `mcp.json` | [GitHub](https://github.com/lasso-security/mcp-gateway); [releases](https://github.com/lasso-security/mcp-gateway/releases) |
| CSA RiskRubric MCP Scanner (draft) | Server deployment | Client-side scan, including live probing | Score 0–100 mapped to A–F | [CSA](https://labs.cloudsecurityalliance.org/agentic/csa-research-note-riskrubric-mcp-scanner-spec-20260327/) |
| PointGuard AI | Public GitHub server | Bulk scan | A–F | [PointGuard](https://www.pointguardai.com/blog/we-tested-36-500-public-mcp-servers-two-thirds-arent-safe-for-enterprise-use) |
| Glama | Server and each tool | Regular scans | Letter grades for quality, security and licence. TDQS 0–5 per tool and per server. Maintenance tier (archived repo means F) | [Glama](https://glama.ai/mcp/servers/mnott/Hook/score) |
| Smithery | Server | At listing | MCP-Scan results on the server page. No grade described | [Invariant blog](https://invariantlabs.ai/blog/smithery-mcp-scan) |
| Official MCP Registry | Namespace | At publish | Ownership check only. No security score | [MCP registry](https://modelcontextprotocol.io/registry/about) |
| MCP-Shield (aaronlab) | Each locally configured server | Scan | Trust score 0–100 with grades A ≥ 90, B 80–89, C 65–79, D 50–64, F < 50 | [GitHub](https://github.com/aaronlab/mcp-shield) |

#### Runtime: call level

| System | Unit evaluated | Output | Source |
|---|---|---|---|
| Invariant Guardrails / Gateway | Each LLM and MCP request, before and after it runs, plus sequences of calls | Raises an error and blocks. `analyze()` returns a list of errors. No score | [GitHub](https://github.com/invariantlabs-ai/invariant) |
| Trail of Bits mcp-context-protector | Server configuration (pinned trust-on-first-use) and each tool response | Changed tools are blocked, and a changed server instruction blocks the whole server. Flagged responses go to quarantine. No score | [GitHub](https://github.com/trailofbits/mcp-context-protector) |
| Docker MCP Gateway | Each `tools/call` (arguments and responses) | Blocks the call if secrets are found. Interceptors can let a call through or return a custom response. No score | [security.md](https://github.com/docker/mcp-gateway/blob/main/docs/security.md); [interceptors](https://github.com/docker/mcp-gateway/blob/main/examples/interceptors/README.md) |
| Prisma AIRS | Tool definitions, tool inputs and tool outputs | allow/block verdict (`pan_inline_scan` returns `action` = allow or block) | [PANW MCP server](https://docs.paloaltonetworks.com/prisma-airs/ai-agent-identity/understanding-the-prisma-airs-mcp-server); [Oct 2025](https://docs.paloaltonetworks.com/ai-runtime-security/new-features/by-date/prisma-airs/october-2025) |
| Pomerium | Each `tools/call` | Allow/deny with reasons (`mcp-tool-ok`, `mcp-tool-unauthorized`) | [Pomerium](https://www.pomerium.com/docs/capabilities/mcp/limit-mcp-tools) |
| agentgateway | Each MCP method or tool | Allow, Require or Deny via CEL. 403 on deny. Tool lists filtered | [agentgateway authz](https://agentgateway.dev/docs/kubernetes/main/security/authorization/); [tool access](https://agentgateway.dev/docs/kubernetes/latest/documentation/mcp/tool-access/) |
| Kong AI MCP Proxy | Tool discovery and tool invocation | ACL allow/deny | [Kong](https://developer.konghq.com/plugins/ai-mcp-proxy/) |
| AWS AgentCore Policy | Every tool call (ENFORCE mode) | Cedar permit/forbid | [AWS](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-getting-started.html) |
| Azure APIM | Each request to the MCP server | Policy outcomes (rate limit, JWT validation, IP filter) | [MS Learn](https://learn.microsoft.com/en-us/azure/api-management/expose-existing-mcp-server) |
| Cloudflare MCP portals | Each portal request | Access allow/deny. Optional DLP via Gateway | [Cloudflare docs](https://developers.cloudflare.com/cloudflare-one/access-controls/ai-controls/mcp-portals/) |
| Golf Firewall | Each MCP request and response | Monitor mode (log and score) or enforce mode (block or modify). "Severity and confidence scores" on incidents. "Threat scores attached to each event" | [Golf docs](https://docs.golf.dev/golf-firewall) |
| Operant MCP Gateway | MCP servers and data flows | "Trust and risk scores" for servers. Blocking of unverified tools. Redaction | [SiliconANGLE](https://siliconangle.com/2025/06/16/operant-ai-expands-gatekeeper-platform-mcp-gateway-ai-runtime-security) |
| mcpaudit / AxioRank | Server (scan) | "RISK 100/100 DENY" | [GitHub](https://github.com/AxioRank/mcpaudit) |

### Inferences

- Only Harness scores at the level of each **tool** with an explicit likelihood × impact structure. That is the nearest match to our static "cell". Snyk, Cisco, Lasso and the graders score servers, or tools only as evidence for a server finding.
- No major system documents a numeric **per-call** risk score. Runtime products make policy decisions (allow/deny) or run content detectors (prompt injection, DLP, secrets). Golf mentions per-event "threat scores" but does not publish a method.
- No major system documents a score per **agent identity**. Identity is used as a policy input (JWT `sub`, groups, Consumers), not as something that accumulates risk.

### Gaps

- Enkrypt's report format and score scale are not documented publicly.
- Operant's and Golf's scores have no scale or formula in the sources I read.

## Q3. How each score is computed (documented method vs marketing)

### Takeaway

Where a method is published, it is one of four patterns. (a) Deductions from 100 with severity weights, then letter-grade bands (most open-source graders, aaronlab MCP-Shield, RiskRubric). (b) Max-of-factors or additive capped sums (Wallarm, Akto). (c) A likelihood × impact lookup table (Harness). (d) A server-side analysis API whose internals are undocumented (Snyk). Detection inside those scores is rules (regex or YARA), an LLM judge, a vendor content-safety API, SAST/SCA/CVE feeds, or reputation metadata. Commercial runtime platforms (Lasso commercial, Operant, Zenity, Noma, Golf) mostly do not publish their scoring maths.

### Cited Findings

#### Documented formulas

- **Harness:** the score combines Likelihood of Exploit and Impact of Exploit. Likelihood comes from "MCP Tool Access" (Internet Facing or Internal, authentication Weak, Strong or None, and no encryption raises it) and from detected Issues (only High and Critical count, highest one applies). Impact comes from "Sensitivity of Response Data" (Critical, High, Medium, Low) and Labels (defaults Sensitive, Sentry, Critical; highest applies). A Risk Lookup Table maps likelihood and impact to a score from 0 to 10. Each contributor can be turned on or off and edited. Default numeric values are not published — [Harness](https://developer.harness.io/ai-security/mcp-risk-score)
- **Akto:** Risk Score = Security Issue Severity (High 2, Medium 1, Low 0.5) + Recent Discovery (+1 if found in the last 30 days) + Sensitive Data Exposure in responses (+1) + Public Accessibility (+1), capped at 5 — [Akto](https://ai-security-docs.akto.io/akto-argus-agentic-ai-security-for-homegrown-ai/agentic-ai-discovery/concepts/risk-score)
- **Wallarm:** "the highest weight from all factors is used as the endpoint or MCP primitive risk score". Default weights: active vulnerabilities 9, parameters with sensitive data 8, number of query and body parameters 6, accepts XML/JSON objects 6, allows file uploads 6. A score of 1 means no risk factors apply — [Wallarm](https://docs.wallarm.com/api-discovery/risk-score/)
- **CSA RiskRubric MCP Scanner (draft):** five domain weights: Tool Poisoning Detection 30%, Authentication & Authorization 25%, Supply Chain Provenance 20%, Session Management Security 15%, Network Exposure Assessment 10%. Each domain is a 0–100 weighted average of its checks (pass gets full credit, partial gets partial, fail gets zero). Grade bands A 90–100, B 80–89, C 70–79, D 60–69, F 0–59. Any critical finding (direct RCE or unauthenticated credential access) forces F. Inputs are rule-library pattern matching on tool metadata with Unicode normalisation, live probing, and passive configuration analysis. No LLM judge is mentioned — [CSA](https://labs.cloudsecurityalliance.org/agentic/csa-research-note-riskrubric-mcp-scanner-spec-20260327/)
- **PointGuard AI:** Security Maturity 50% (SAST/SCA on code, findings ranked by CVSS, EPSS and CISA KEV, hardcoded secrets, whether a security policy exists), Operational Maturity 30% (publisher verification, licence, issue-resolution speed, peer review), Adoption Maturity 20% (downloads, stars, forks). About 67% of 36,527 servers got D or F, and fewer than 15% got A or B — [PointGuard](https://www.pointguardai.com/blog/we-tested-36-500-public-mcp-servers-two-thirds-arent-safe-for-enterprise-use)
- **Lasso MCP Gateway scanner:** a "multi-factor" reputation score from 0 to 100. Inputs are GitHub owner metrics (followers, repositories, account age, verification, organisation status), repository stars and forks on a logarithmic scale, licence type, repository age and activity, npm downloads, versions and maintainers, and Smithery monthly usage and verification. Tool descriptions are scanned with regex for hidden instructions, sensitive file patterns and malicious actions. Default block threshold is 30. The release notes do not give the weights, which are in the source code (`ProjectAnalyzer`) — [Lasso releases](https://github.com/lasso-security/mcp-gateway/releases)
- **Glama:** overall quality = Tool Definition Quality 70% + Server Coherence 30% (per a Glama page quoted in search results). Server-level tool quality = 60% mean TDQS + 40% minimum TDQS. TDQS scores each tool from 0 to 5 on Behavior, Conciseness, Completeness, Parameters, Purpose and Usage Guidelines. The method behind the security grade is undocumented; Glama says only that scans "confirm that there are no obvious security issues" — [Glama score page](https://glama.ai/mcp/servers/mnott/Hook/score); [Glama search results](https://glama.ai/mcp/servers/sakthivelchan89/scan_your_ai_toolkit/score)
- **MCP-Shield (aaronlab):** more than 15 rules in 8 categories (scope, command, environment, package, network, exfiltration, known risk, privilege), for example EXFIL-001 for combined filesystem and network access. Deductions: High 15, Medium 5, Low 2 — [GitHub](https://github.com/aaronlab/mcp-shield)
- **Canopii:** earned points over the controls it evaluated. The score is hard-capped by the worst failed guard (critical caps at 20, high 49, medium 74, low 89) and by coverage (below 40% coverage caps at 40). Grades A ≥ 90, B ≥ 75, C ≥ 60, D ≥ 40. No LLM in scoring; an optional AI review is advisory only — [GitHub](https://github.com/canopii-dev/canopii-cli)
- **mcp-security-audit:** classifies each tool as SHELL, FILE, DATABASE, NETWORK or SAFE and checks 75 injection patterns. Starts at 100 and deducts CRITICAL 25, HIGH 15, MEDIUM 8, LOW 3, with +1 per documented tool (up to +5) — [GitHub](https://github.com/LuciferForge/mcp-security-audit)
- **AgentsID:** CRITICAL deducts 25 (uncapped), HIGH 15 (capped at 45), MEDIUM 8 and LOW 3 divided by √(tool count) (capped at 25 and 15). Tool names are classified as destructive, execution, financial or credential — [GitHub](https://github.com/AgentsID-dev/agentsid-scanner)
- **MCP Doctor:** Security 35%, Maintenance 25%, Documentation 15%, Testing 15%, Community 10% — [GitHub](https://github.com/xlyoung/mcp-doctor)
- **mcptrustchecker:** "Capable ≠ malicious". A server's blast radius and its signs of malice are kept as two separate axes, so the grade "never punishes a server for what it's built to do". It also builds a cross-tool "toxic-flow graph" looking for untrusted input → sensitive data → exfiltration. No LLM. Calibrated on 30,000+ servers (vendor claim) — [mcptrustchecker](https://mcptrustchecker.com/scan)

#### Documented detection methods (score maths not public)

- **Snyk Agent Scan:** components are "validated with local checks and the Agent Scan API". v0.5.x sends tool names and descriptions to Snyk. v0.6+ sends client information, server configurations and "signatures", and skill files, with secrets redacted first. The API's internal method (LLM, classifier or rules) is undocumented. The README warns that scores "can evolve" and should be read together with the indicator name and evidence — [scanning.md](https://github.com/snyk/agent-scan/blob/main/docs/scanning.md); [risks.md](https://github.com/snyk/agent-scan/blob/HEAD/docs/risks.md)
- **Snyk risk categories:** v0.6+ MCP indicators are `prompt_injection_tool_desc`, `untrusted_content`, private data, and destructive capabilities. Evo also lists "Dangerous words" (manipulative language in descriptions). The v0.5.x "toxic flow" logic (from Invariant Labs and Simon Willison) flags each part of the combination separately: untrusted content W015/W016, sensitive data W017/W018, destructive capabilities W019/W020. Internet egress is not flagged, "as most agents include network access tools (such as curl) by default" — [issue-codes.md](https://github.com/snyk/agent-scan/blob/main/docs/issue-codes.md); [Snyk docs](https://docs.snyk.io/agent-security/evo-by-snyk/agentic-development-security-ads/agent-supply-chain-security)
- **Cisco MCP Scanner:** three engines that can run together or alone: YARA rules (customisable), an LLM-based analyzer ("LLM-as-judge", needs the user's own LLM API key), and the Cisco AI Defense inspect API. Extras: behavioural code scanning of server source, pip-audit CVE checks, VirusTotal hash lookups, PyPI sandbox behavioural analysis, readiness checks. Severity is normalised to the enumerated values. Each finding is tagged with an MCP taxonomy entry. Analyzers report severity separately; the docs do not describe a combined numeric score — [GitHub](https://github.com/cisco-ai-defense/mcp-scanner/); [DeepWiki](https://deepwiki.com/cisco-ai-defense/mcp-scanner/4.1-baseanalyzer-and-securityfinding)
- **Invariant Guardrails:** Python-inspired rules of the form `raise "msg" if: (call: ToolCall) ...`, matched on tool names (`call is tool:get_inbox`). A `->` flow operator matches ordered sequences (for example reading an inbox, then sending email to an unknown address). Built-in detectors include `prompt_injection` with a `threshold` parameter — [GitHub](https://github.com/invariantlabs-ai/invariant)
- **Trail of Bits:** semantic comparison of server instructions, tool descriptions and input schemas against an approved set (ignoring order), re-checked on `notifications/tools/list_changed`. Tool responses are scanned by a guardrail provider (LlamaFirewall ships; others plug in through a `GuardrailProvider` subclass) — [GitHub](https://github.com/trailofbits/mcp-context-protector); [ToB blog](https://blog.trailofbits.com/2025/07/28/we-built-the-security-layer-mcp-always-needed/)
- **Prisma AIRS:** reuses existing AI Runtime Security detectors (DLP, prompt injection, toxic content, URL categorisation) on tool descriptions, inputs and outputs. Targets "context poisoning" and "exposed credentials and identity leakage" — [PANW Oct 2025](https://docs.paloaltonetworks.com/ai-runtime-security/new-features/by-date/prisma-airs/october-2025); [pan-mcp-relay](https://github.com/PaloAltoNetworks/pan-mcp-relay)
- **Docker MCP Gateway:** `secretsscan.ContainsSecrets` runs on the stringified arguments before the call and on the text content after it, and returns an error if a secret is found — [block_secrets.go](https://github.com/docker/mcp-gateway/blob/main/pkg/interceptors/block_secrets.go)
- **Google Model Armor:** "sanitizes MCP requests and responses" against prompt injection, sensitive-data disclosure and tool poisoning on Google-managed MCP servers. IAM deny policies can block tools not marked read-only — [Google MCP overview](https://docs.cloud.google.com/mcp/overview?hl=th); [Google blog](https://cloud.google.com/blog/products/ai-machine-learning/how-to-build-ai-agents-with-google-managed-mcp-servers?e=48754805)

#### Marketing claims with no published method

- Lasso's commercial dashboard: "intelligent risk assessment with MCP risk scoring" — [Lasso GitHub README](https://github.com/lasso-security/mcp-gateway)
- Operant: "assigns trust and risk scores to MCP servers" and "real-time enforcement of trust zones" — [SiliconANGLE](https://siliconangle.com/2025/06/16/operant-ai-expands-gatekeeper-platform-mcp-gateway-ai-runtime-security)
- Zenity: "automatically discovers every MCP server … maps each to its agents, owners, and behavior" and "real-time policy enforcement" — [Zenity](https://www.zenity.io/use-cases/risk-type/mcp)
- Golf: "severity and confidence scores" and "threat scores attached to each event" — [Golf docs](https://docs.golf.dev/golf-firewall)
- mTrust: per-call agent trust scores in under 2 ms and A–F grading. I could not verify these — [mTrust](https://www.modeltrust.io/)
- Several gravitee.io "corpus" pages (for example "MCP Server Runtime Attestation and Trust Scoring") describe per-agent and per-server trust scores. The `/corpus/gen-NNNN/<unrelated-slug>/` URLs suggest generated SEO content, so I do not treat them as product documentation — [Gravitee corpus page](https://gravitee.io/corpus/gen-1099/anything-can-happen/model-context-protocol-mcp-server-runtime-attestation-and-trust-scoring-for-enterprise-ai-toolchains.html)

#### Standards: none define a scoring formula

- OWASP MCP Top 10 (2025): MCP01 Token Mismanagement & Secret Exposure, MCP02 Privilege Escalation via Scope Creep, MCP03 Tool Poisoning, MCP04 Software Supply Chain Attacks & Dependency Tampering, MCP05 Command Injection & Execution, MCP06 Prompt Injection via Contextual Payloads, MCP07 Insufficient Authentication & Authorization, MCP08 Lack of Audit and Telemetry, MCP09 Shadow MCP Servers, MCP10 Context Injection & Over-Sharing. The page gives no scores or severity levels — [OWASP](https://owasp.org/www-project-mcp-top-10/)
- CoSAI: 12 core threat categories and "almost forty threats", split into conventional threats that AI amplifies and MCP-specific new threats (section headings include MCP-T7 session/transport failures and MCP-T8 network binding/isolation). I found no scoring method — [CoSAI PDF](https://www.coalitionforsecureai.org/wp-content/uploads/2026/03/model-context-protocol-security-1.pdf); [Adversa summary](https://adversa.ai/blog/mcp-security-whitepaper-2026-cosai-top-insights/)
- CSA MAESTRO: a seven-layer threat model for agentic AI. Its threat analyzer separates traditional from agentic threats and suggests mitigations. I found no numeric scoring — [CSA](https://cloudsecurityalliance.org/articles/agentic-ai-threat-modeling-framework-maestro); [GitHub](https://github.com/CloudSecurityAlliance/MAESTRO)
- MCP Security Best Practices covers confused deputy, token passthrough, SSRF, state handle hijacking (session hijacking for `2025-11-25` and earlier), local server compromise, OAuth URL validation, stdio-in-proxy escalation, mix-up attacks, localhost redirect impersonation, CIMD trust policies and scope minimisation. It uses MUST/SHOULD rules, not scores. The CIMD section allows "reputation checks for unknown domains" and "restrictions based on domain age" — [MCP spec](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)
- NIST: SP 800-53 control overlays for single- and multi-agent systems are being written (COSAiS), and CAISI is building agent-hijacking evaluations. Nothing is MCP-specific and nothing defines a score — [NIST slides](https://www.nccoe.nist.gov/sites/default/files/2026-05/Cyber-AI-Profile-Working-Session-Extending-Tech-Content-Slides-Slido.pdf)

### Inferences

- Snyk's split into untrusted content, private data and destructive capabilities is the industry's closest match to our impact and sensitivity dimensions. But it is computed per server from the agent's point of view, and it is a set of categorical indicators, not a product of factors.
- Harness's likelihood (exposure, authentication, open issues) × impact (response-data sensitivity, labels) lookup is the closest documented match to our static cell. The difference is that Harness sensitivity comes from data detection and labels set by hand, while ours is derived from the organisation's security policy.
- Caps and floors are common. Canopii caps by the worst guard, RiskRubric forces F on a critical finding, AgentsID caps per severity, and Wallarm takes the maximum factor. This is the same "worst case dominates" idea as our floored dynamic score, but used for static grades.
- Using an LLM judge in scoring is uncommon among the documented systems (Cisco optional, Boomi per snippet). Several open-source graders say they deliberately avoid LLMs so scores are reproducible (Canopii, mcptrustchecker).

### Gaps

- Snyk's analysis API internals and the default lookup table values for Harness are not public.
- I could not open the full CoSAI category list or any CoSAI scoring appendix. I only saw secondary summaries plus the PDF link.
- I did not open the Boomi blog page itself; its claim comes from a search snippet.
- The OWASP "Agentic AI – Threats and Mitigations" guide (separate from the Agentic Top 10) was not checked in this pass.

## Q4. Threat direction: protecting servers from agents, or agents from servers

### Takeaway

Most scanners and several gateways protect the **agent, user or host from malicious or compromised MCP servers** (tool poisoning, rug pulls, shadowing, secret leakage, malicious packages). That is the opposite of our threat model. The systems closest to "defend the server and org data from callers" are identity-aware gateways (Pomerium, agentgateway, Kong, Azure APIM, AWS AgentCore Policy, Cloudflare portals, Golf), which enforce access control but compute no risk score, and API-security platforms (Harness, Akto, Wallarm), which score the organisation's own MCP tools as assets.

### Cited Findings

#### Mainly agent or user protected from server (opposite of ours)

- Cisco MCP Scanner: built "to detect malicious MCP tools". The project blog is titled "Securing the AI agent supply chain" — [GitHub](https://github.com/cisco-ai-defense/mcp-scanner/)
- Snyk Agent Scan v0.5.x: "Compromised MCP Servers … effectively exposes a successful supply chain attack". Covers tool poisoning and tool shadowing — [issue-codes.md](https://github.com/snyk/agent-scan/blob/main/docs/issue-codes.md)
- Trail of Bits: "risks associated with running untrusted MCP servers, including line jumping … rug pulls" — [GitHub](https://github.com/trailofbits/mcp-context-protector)
- Docker MCP Gateway: "designed to reduce what a malicious or compromised MCP server can read, receive, log, or route through the host". Prompt injection and tool-description poisoning are out of scope unless they bypass a gateway boundary — [security.md](https://github.com/docker/mcp-gateway/blob/main/docs/security.md)
- pan-mcp-relay protects "MCP Clients such as IDE's, LLM Chat Clients, and AI Agents from harmful MCP Server Tools". Prisma AIRS says agents "cannot be weaponized against your organization through compromised or malicious tools" — [pan-mcp-relay](https://github.com/PaloAltoNetworks/pan-mcp-relay); [PANW Oct 2025](https://docs.paloaltonetworks.com/ai-runtime-security/new-features/by-date/prisma-airs/october-2025)
- Lasso scanner: "blocks risky MCPs" before they load — [Lasso releases](https://github.com/lasso-security/mcp-gateway/releases)
- Smithery, Glama, PointGuard, Canopii, mcptrustchecker and the other A–F graders answer "is this server safe to install?" — [Smithery](https://invariantlabs.ai/blog/smithery-mcp-scan); [PointGuard](https://www.pointguardai.com/blog/we-tested-36-500-public-mcp-servers-two-thirds-arent-safe-for-enterprise-use)
- Most of the MCP spec's best-practices attacks (SSRF, OAuth URL injection, local server compromise) assume a malicious server attacking the client. Confused deputy, token passthrough, state-handle hijacking and scope minimisation are about protecting the server side — [MCP spec](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)

#### Mixed or two-way

- Snyk "destructive capabilities" asks whether the server exposes tools that could damage shared infrastructure. It frames the agent as possibly "compromised or mistaken" and recommends "human approval for state-changing operations" — [risks.md](https://github.com/snyk/agent-scan/blob/HEAD/docs/risks.md)
- RiskRubric takes "the attacker's vantage point" from the client side and checks the server's authentication, session and network exposure. That is server hardening against outside callers — [CSA](https://labs.cloudsecurityalliance.org/agentic/csa-research-note-riskrubric-mcp-scanner-spec-20260327/)
- Golf Firewall aims to "protect your agents and backend systems". It has rate limits "to protect backends from runaway agents" — [Golf docs](https://docs.golf.dev/golf-firewall)
- Invariant Guardrails flow rules can restrict which tool sequences an agent may perform. That works in either direction — [GitHub](https://github.com/invariantlabs-ai/invariant)

#### Server or org data protected from callers (our direction)

- Pomerium: per-user and per-group `mcp_tool` deny rules, for example blocking `issue_delete` across the organisation. "A model that hallucinates an argument can call those tools just as readily as a useful one" — [Pomerium bridge guide](https://www.pomerium.com/docs/guides/mcp-bridge)
- agentgateway: CEL rules such as `jwt.sub == "alice" && mcp.tool.name == "get_me"`. Justin Cappos calls it "basic role-based access control and visibility" — [agentgateway](https://agentgateway.dev/docs/kubernetes/latest/documentation/mcp/tool-access/); [LF press](https://www.linuxfoundation.org/press/linux-foundation-welcomes-agentgateway-project-to-accelerate-ai-agent-adoption-while-maintaining-security-observability-and-governance)
- Kong per-tool ACLs by Consumer Group; AWS AgentCore Cedar rules on JWT claims and tool arguments (for example an order amount); Azure APIM rate limits and JWT checks — [Kong](https://developer.konghq.com/plugins/ai-mcp-proxy/); [Konishi guide](https://hidekazu-konishi.com/entry/amazon_bedrock_agentcore_policy_implementation_guide.html); [MS Learn](https://learn.microsoft.com/en-us/azure/api-management/mcp-server-overview)
- Harness, Akto and Wallarm score the organisation's own exposed MCP tools and endpoints by exposure, authentication strength and sensitive data in responses — [Harness](https://developer.harness.io/ai-security/mcp-risk-score); [Akto](https://ai-security-docs.akto.io/akto-argus-agentic-ai-security-for-homegrown-ai/agentic-ai-discovery/concepts/risk-score); [Wallarm](https://docs.wallarm.com/api-discovery/risk-score/)
- OWASP Agentic Top 10 ASI02 (Tool Misuse) covers agents misusing tools they are legitimately allowed to use ("no privilege escalation required"), where harm shows up "in sequences of actions rather than in any single API call". ASI03 covers identity and privilege abuse. Both are framed as risks the agent creates, which matches our direction (secondary sources) — [HUMAN](https://www.humansecurity.com/learn/blog/owasp-top-10-agentic-applications/); [Descope](https://www.descope.com/blog/post/owasp-agentic-top-10-identity)

### Inferences

- If we count scoring systems that publish their method, only Harness, Akto and Wallarm score the server's tools as assets. None of them scores the calling agent or the individual call. In this catalogue, our framework is the only one documented to combine a per-tool asset score with per-call, per-agent risk in the server-protection direction.
- Gateways in our direction give binary policy decisions. Our likelihood × escalation × behaviour score would sit between their policy check and the forwarded call, as a graded signal that they currently lack.

### Gaps

- Noma, Zenity and Operant do not state publicly whether their MCP scores are about server-to-agent risk or agent-to-server risk.

## Q5. Use of org context, identity, behaviour baselines, rate limits and audit-log integrity

### Takeaway

**Identity** (JWT, IdP groups, service accounts) and **audit logging** are common in gateways. **Rate limits** appear in Azure APIM, Golf and agentgateway-class gateways. **Org context** appears only as manually set labels or data-sensitivity detection (Harness, Akto, Wallarm), never as sensitivity derived from the organisation's security policy. **Behaviour baselines** over each agent's history are documented only by small open-source projects (EWMA, z-score) and by unverified vendor claims. **Tamper-evident (hash-chained) audit logs** are not documented by any major system. AxioRank claims one in marketing text.

### Cited Findings

#### Org context (data classification or policy)

- Harness: "Sensitivity of Response Data" (four levels) and organisation-defined Labels (Sensitive, Sentry, Critical, plus custom ones) feed impact. Settings need Discovery Settings RBAC permissions — [Harness](https://developer.harness.io/ai-security/mcp-risk-score)
- Akto and Wallarm add risk for sensitive data in responses or parameters — [Akto](https://ai-security-docs.akto.io/akto-argus-agentic-ai-security-for-homegrown-ai/agentic-ai-discovery/concepts/risk-score); [Wallarm](https://docs.wallarm.com/api-discovery/risk-score/)
- Snyk's "private data" indicator is based on the server's "explicit, named purpose" (email, finance, credential vaults). It is a generic category, not the organisation's own classification — [issue-codes.md](https://github.com/snyk/agent-scan/blob/main/docs/issue-codes.md)
- Prisma AIRS uses organisation-configured AI Security Profiles, passed in an `x-pan-profile` header or linked to the app, for DLP and detectors — [PANW configure](https://docs.paloaltonetworks.com/prisma-airs/ai-agent-identity/understanding-the-prisma-airs-mcp-server/configure-mcp-server-security-using-prisma-airs)
- Cloudflare portals can route traffic through Cloudflare Gateway "to detect and block sensitive data from being sent to your upstream MCP servers" — [Cloudflare docs](https://developers.cloudflare.com/cloudflare-one/access-controls/ai-controls/mcp-portals/)

#### Identity (per-agent or per-user)

- Pomerium: every tool call is attributed to the end user's email. Agents act through service accounts that "represent a specific user". Log fields include `mcp-method`, `mcp-tool` and `mcp-tool-parameters` — [Pomerium MCP](https://www.pomerium.com/docs/capabilities/mcp); [bridge guide](https://www.pomerium.com/docs/guides/mcp-bridge)
- agentgateway: CEL rules on `jwt.sub` and claims — [agentgateway](https://agentgateway.dev/docs/kubernetes/latest/documentation/mcp/tool-access/)
- Kong: Consumers and Consumer Groups. 3.14+ maps token claims to Consumers — [Kong cookbook](https://developer.konghq.com/cookbooks/secure-internal-mcp-gateway/)
- AWS AgentCore: Cedar principal comes from JWT claims (for example Cognito groups) — [Konishi guide](https://hidekazu-konishi.com/entry/amazon_bedrock_agentcore_policy_implementation_guide.html)
- Azure APIM: the documented example adds "a custom trace of the agent ID of the caller" — [MS Learn](https://learn.microsoft.com/en-us/azure/api-management/expose-existing-mcp-server)
- Cloudflare: Access service tokens for autonomous agents. MFA, purpose justification and temporary authentication are not enforced for servers authorised through a portal — [Cloudflare docs](https://developers.cloudflare.com/cloudflare-one/access-controls/ai-controls/mcp-portals/)
- Google Agent Gateway: per-agent identity checked during the mTLS handshake, then allow/deny per tool (secondary source only) — [Forkast](https://forkast.news/google-cloud-ships-the-first-protocol-native-agent-gateway-and-it-understands-mcp-and-a2a/)
- Prisma AIRS with Cortex AES: verdicts recorded "in the agent's session timeline, tied to the device, agent and policy" — [PANW blog](https://www.paloaltonetworks.com/blog/ai-security/securing-the-ai-coding-frontier-prisma-airs-agentic-endpoint-security/)
- NIST NCCoE (Feb 2026 concept paper) proposes treating agents as non-human identities using OAuth 2.0, OIDC and SPIFFE/SPIRE (secondary source) — [Codex blog](https://codex.danielvaughan.com/2026/06/24/nist-ai-agent-standards-initiative-codex-cli-compliance-readiness-cosais-identity-authorization/)
- Astrix frames MCP credential risk as a non-human identity problem: 88% of more than 20,000 servers need credentials, 79% keep them in environment variables, and 53% use static keys or PATs (vendor figures) — [Astrix](https://astrix.security/learn/news/astrix-researchers-uncover-credential-risk-in-the-majority-of-mcp-servers/)

#### Behaviour baselines and anomaly detection over time

- HarrisonCN/mcp-gateway v6.6.0: "watches each client for traffic bursts against its EWMA baseline, error spikes and tool enumeration" and can quarantine abusive clients — [PR #87](https://github.com/HarrisonCN/mcp-gateway/pull/87)
- TrueFoundry: the audit stream doubles as a behaviour baseline. "Above a configurable z-score threshold" it quarantines the developer's agentic access. Evaluation runs off the request path on aggregated metrics — [TrueFoundry](https://www.truefoundry.com/blog/claude-code-enterprise-mcp-gateway)
- mTrust: "per-agent behavioral baselines build automatically" (unverified vendor claim) — [mTrust](https://www.modeltrust.io/)
- Akto adds +1 risk for anything "discovered in the last 30 days". This is newness, not behaviour — [Akto](https://ai-security-docs.akto.io/akto-argus-agentic-ai-security-for-homegrown-ai/agentic-ai-discovery/concepts/risk-score)
- Cloudflare's launch blog says portal logs help "detect anomalies before they become breaches". The GA docs list only log fields and export, with no anomaly model — [Cloudflare blog](https://blog.cloudflare.com/zero-trust-mcp-server-portals/); [docs](https://developers.cloudflare.com/cloudflare-one/access-controls/ai-controls/mcp-portals/)
- Zenity says it maps each MCP server to "agents, owners, and behavior". No method is published — [Zenity](https://www.zenity.io/use-cases/risk-type/mcp)
- Trail of Bits and Snyk detect configuration drift (rug pulls) by pinning tool definitions. That is change over time in the server, not in caller behaviour — [ToB GitHub](https://github.com/trailofbits/mcp-context-protector)

#### Rate limits

- Azure APIM: "rate limiting and quota enforcement". The example allows 5 calls per 30 seconds per IP address — [MS Learn](https://learn.microsoft.com/en-us/azure/api-management/expose-existing-mcp-server)
- Golf: per-user, per-tenant and per-server limits — [Golf docs](https://docs.golf.dev/golf-firewall)
- Docker: per-server CPU (default 1) and memory (default 2 GB) limits on containers, which are resource limits rather than call-rate limits — [Docker CLI ref](https://docs.docker.com/reference/cli/docker/mcp/gateway/run/)
- The MCP spec warns that token passthrough lets callers bypass "rate limiting, request validation, or traffic monitoring" — [MCP spec](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)
- MCPWatch counts "Missing rate limits" as check MCP-08 (Medium) — [GitHub](https://github.com/lazymac2x/mcpwatch)

#### Audit logging and integrity

- Docker `--log-calls` is on by default but logs only "tool name and argument shape metadata", and secret blocking runs before logging — [security.md](https://github.com/docker/mcp-gateway/blob/main/docs/security.md); [releases](https://github.com/docker/mcp-gateway/releases/latest)
- Pomerium logs tool parameters and advises redacting them if needed and forwarding to a SIEM — [Pomerium bridge](https://www.pomerium.com/docs/guides/mcp-bridge)
- Cloudflare logs time, status, server, capability and duration. Logpush to SIEM is Enterprise-only — [Cloudflare docs](https://developers.cloudflare.com/cloudflare-one/access-controls/ai-controls/mcp-portals/)
- Golf logs method, tool, parameters (with redaction), identity and policy decision, with SIEM and OpenTelemetry export — [Golf docs](https://docs.golf.dev/golf-firewall)
- Lasso logs requests and responses per guardrail, and keeps a scanner log at `~/.mcp-gateway/scanner.log` — [Lasso releases](https://github.com/lasso-security/mcp-gateway/releases)
- OWASP MCP08:2025 is "Lack of Audit and Telemetry" — [OWASP](https://owasp.org/www-project-mcp-top-10/)
- MCP spec: "Log elevation events (scope requested, granted subset) with correlation IDs" and "Log all `stdio` transport usage for security monitoring" — [MCP spec](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)
- AxioRank (hosted) says it "keeps a tamper-evident audit log". That is a marketing claim with no published mechanism — [mcpaudit README](https://github.com/AxioRank/mcpaudit)

### Inferences

- No documented major system combines all five of: policy-derived asset sensitivity, per-agent identity as the key for risk history, a behaviour multiplier from the agent's own history, a per-call graded score, and a hash-chained log. Each piece exists somewhere. Harness has sensitivity and labels. Pomerium, agentgateway, Kong and AgentCore key on identity. TrueFoundry and HarrisonCN have baselines. APIM and Golf have rate limits. AxioRank claims tamper evidence.
- Gateways log tool calls, but integrity protection of those logs (hash chains, signing) is not part of any documented MCP gateway. Integrity is left to the SIEM.
- Identity in industry gateways is usually the end user that the agent acts for (Pomerium email, JWT `sub`). Our framework keys on an agent id that may stand for a whole organisation, which is a different unit of accountability.

### Gaps

- Whether Operant, Zenity, Noma or Golf build per-agent baselines, and how, is undocumented in public sources.
- I found no independent benchmark of any MCP behaviour-anomaly method. The search turned up none.
- Second pass count: 35 named products and projects (rows 1–35), 6 standards and frameworks (rows 36–41), and 14 smaller tools (rows 42–55), for **55 entries in total**. Of these, 17 publish a numeric or letter-grade formula: Snyk score levels, Akto, Harness (structure only), Wallarm, Lasso reputation threshold, RiskRubric, PointGuard, Glama TDQS, aaronlab MCP-Shield, Canopii, mcp-security-audit, AgentsID, MCPWatch bands, MCTS, MCP Doctor, MCPSense and mcptrustchecker (principles only).
