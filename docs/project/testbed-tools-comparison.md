# MCP Security Testbed: Open-Source Tool Comparison

A comparison of open-source platforms and gateways for building an MCP security
testbed. This document helps decide which tools to integrate into our research
framework for testing and scoring agent-to-server MCP traffic.

Last updated: 2026-04-16


## Executive Summary

To build a complete MCP security testbed, we need tools in two categories:

1. **Agent platforms** -- generate realistic LLM-driven tool calls (the attacker side)
2. **MCP gateways** -- proxy, log, and govern traffic between agents and servers (the observer side)

No single tool covers both roles well. The recommended combination for our
research is **Obot** (agent) + **ContextForge** (gateway), with **Lasso** added
if we need real-time threat detection. Each tool is detailed below alongside
alternatives.

---


## Part 1: Agent Platforms

These tools act as the **agent/client** -- the entity that connects to MCP
servers, discovers tools, and decides what to call. In our threat model, this is
the **attacker side**.


### 1.1 Obot (obot-platform/obot)

| Field | Detail |
|-------|--------|
| **Maintainer** | Obot Platform (formerly Acorn Labs) |
| **License** | MIT |
| **Language** | Go (53%) + Svelte (38%) + TypeScript (8%) |
| **Stars** | 710+ |
| **Deployment** | Docker (`docker run -p 8080:8080`), Kubernetes via Helm |
| **LLM Support** | OpenAI, Anthropic, any OpenAI-compatible provider |

**What it is:**
Obot is a full self-hosted AI agent platform. It is not just an agent framework
-- it includes hosting, discovery, security, and a chat UI for MCP servers.

**Core components:**

- **MCP Hosting** -- runs and manages MCP servers directly. Supports Node.js,
  Python, and container-based servers. Handles both single-user STDIO and
  multi-user HTTP transports. Built-in OAuth 2.1 and token management.

- **MCP Registry** -- curated catalog for server discovery. Platform-managed
  credentials, MCP spec compliance checks, and access-based visibility controls.

- **MCP Gateway** -- single access point with user/group access rules, request
  logging, usage analytics, and request filtering.

- **Chat Client** -- standards-compliant chat interface. Built-in RAG for
  domain-specific context, project-wide memory, scheduled tasks, and multi-model
  support.

**Why it matters for our testbed:**
Obot provides a realistic LLM-driven agent that autonomously discovers and calls
MCP tools. Unlike our scripted attack harness (which sends pre-defined payloads),
Obot's agent reasons about which tools to use and how -- producing emergent,
realistic attack patterns. It also has a built-in gateway with basic logging.

**Limitations:**
- Gateway logging is basic (audit logs, not deep observability)
- No OpenTelemetry or distributed tracing
- Written in Go -- harder for us to extend (our codebase is Python)
- Requires an LLM API key to function


### 1.2 Goose (block/goose)

| Field | Detail |
|-------|--------|
| **Maintainer** | Block (formerly Square), now under Linux Foundation (AAIF) |
| **License** | Apache 2.0 |
| **Language** | Rust |
| **Stars** | 15,000+ |
| **Deployment** | CLI tool (`cargo install`, pre-built binaries) |
| **LLM Support** | OpenAI, Anthropic, local models via Ollama |

**What it is:**
Goose is a local-first open-source AI agent that runs in the terminal. It
connects to MCP servers via stdio or HTTP and uses an LLM to accomplish tasks
interactively or autonomously.

**Key features:**
- CLI-native -- runs in terminal, no web UI
- MCP-native from day one (founding contribution to AAIF alongside MCP itself)
- Extensible via MCP servers as "toolkits"
- Session-based interaction with memory

**Why it matters for our testbed:**
Goose is under the same Linux Foundation umbrella as MCP. It represents the
"reference agent" for MCP usage. Being terminal-based makes it easy to script
and automate for batch experiments.

**Limitations:**
- No web UI (terminal only)
- Written in Rust -- harder to modify or integrate with our Python stack
- No built-in gateway or logging proxy
- Single-user, single-session only


### 1.3 mcp-agent (lastmile-ai/mcp-agent)

| Field | Detail |
|-------|--------|
| **Maintainer** | LastMile AI |
| **License** | MIT |
| **Language** | Python |
| **Stars** | 2,000+ |
| **Deployment** | `pip install mcp-agent` |
| **LLM Support** | OpenAI, Anthropic, any LiteLLM-supported provider |

**What it is:**
A lightweight Python framework for building agents that use MCP servers. Unlike
Obot (full platform) or Goose (standalone agent), mcp-agent is a library you
use to build custom agents programmatically.

**Key features:**
- Python-native -- integrates directly with our codebase
- Simple workflow patterns (sequential, parallel, router)
- Connects to multiple MCP servers simultaneously
- Programmatic control over agent behavior

**Why it matters for our testbed:**
Most scriptable option. We can write Python agents that programmatically connect
to MCP servers and execute attack scenarios -- giving us full control over what
the agent does while still using real LLM reasoning.

**Limitations:**
- No UI, no registry, no gateway
- No built-in logging or observability
- Requires writing agent code ourselves
- Smaller community than Obot or Goose


### Agent Platform Comparison

| Feature | Obot | Goose | mcp-agent |
|---------|------|-------|-----------|
| Full platform (UI, registry) | Yes | No | No |
| MCP-native | Yes | Yes | Yes |
| Built-in gateway | Yes (basic) | No | No |
| Built-in logging | Audit logs | No | No |
| LLM-driven agent | Yes | Yes | Yes |
| Python integration | Hard (Go) | Hard (Rust) | Native |
| Self-hosted | Yes | Yes (local) | Yes |
| Scriptable/automatable | Via API | Via CLI | Via code |
| Multi-server support | Yes | Yes | Yes |
| Web UI | Yes | No | No |
| License | MIT | Apache 2.0 | MIT |

---


## Part 2: MCP Gateways

These tools sit **between** the agent and the MCP server. They proxy requests,
log traffic, enforce policies, and provide observability. In our testbed, this
is the **observer/scorer layer**.


### 2.1 IBM ContextForge (IBM/mcp-context-forge)

| Field | Detail |
|-------|--------|
| **Maintainer** | IBM |
| **License** | Apache 2.0 |
| **Language** | Python (FastAPI) + optional Rust runtime |
| **Stars** | 3,500+ |
| **Deployment** | PyPI, Docker, Docker Compose, Kubernetes (Helm) |
| **DB** | PostgreSQL (production), SQLite (dev), Redis (cache) |

**What it is:**
ContextForge is an AI gateway, registry, and proxy that federates MCP servers,
A2A (Agent-to-Agent) protocols, and REST/gRPC APIs into a single unified
endpoint. It provides centralized governance, discovery, and observability.

**Core components:**

- **Tools Gateway** -- federates multiple MCP servers behind one endpoint.
  Translates REST and gRPC APIs into MCP tools automatically via schema
  extraction and gRPC reflection.

- **Agent Gateway** -- routes requests from OpenAI, Anthropic, and custom
  agents using A2A protocols and OpenAI-compatible APIs.

- **API Gateway** -- rate limiting, authentication (JWT, Basic, OAuth), retry
  logic, and reverse proxy for REST services.

- **Admin UI** -- web-based management with real-time log viewer, filtering,
  search, and export. Also shows server health and tool registry.

- **Observability** -- full OpenTelemetry integration supporting Phoenix,
  Jaeger, Zipkin, and OTLP backends. Distributed tracing across federated
  gateways. LLM-specific metrics (token usage, costs).

- **Plugin system** -- 40+ plugins for additional transports and integrations.

**Key capability: mcpgateway.translate**
Wraps stdio-based MCP servers as HTTP/SSE endpoints, making any local MCP
server accessible through the gateway:
```
python -m mcpgateway.translate --stdio "npx -y @modelcontextprotocol/server-filesystem /tmp" --expose-sse --port 8003
```

**Why it matters for our testbed:**
ContextForge is the most feature-complete open-source gateway. It gives us deep
logging, real-time traffic inspection, and OpenTelemetry tracing -- exactly what
we need to capture and analyze every tool call for scoring. Written in Python,
so it integrates naturally with our codebase.

**Limitations:**
- Heavier infrastructure (PostgreSQL, Redis for production)
- No built-in agent/LLM (pure infrastructure)
- More complex setup than lighter alternatives
- Roadmap items (input validation, DDoS protection) not yet shipped


### 2.2 Lasso MCP Security Gateway (lasso-security/mcp-gateway)

| Field | Detail |
|-------|--------|
| **Maintainer** | Lasso Security |
| **License** | MIT |
| **Language** | Python |
| **Stars** | 500+ |
| **Deployment** | PyPI, Docker |
| **Focus** | Security-first |

**What it is:**
A security-focused MCP gateway with a plugin-based architecture that inspects
traffic in real time to detect and mitigate threats.

**Core security features:**

- **Real-time threat detection** -- plugin inspects all tool calls for prompt
  injection, command injection, and sensitive data exposure. Blocks malicious
  payloads before they reach the server.

- **PII masking and redaction** -- automatically detects and masks personally
  identifiable information and secrets in request/response payloads.

- **Tool reputation scoring** -- scans MCP servers before loading and calculates
  a reputation score based on tool descriptions and capabilities. This is
  conceptually similar to our static scoring.

- **Plugin architecture** -- extensible via custom plugins for additional
  security checks.

**Why it matters for our testbed:**
Lasso's threat detection and tool reputation scoring directly overlap with our
research goals. We could compare Lasso's built-in detection against our own
scorer to benchmark accuracy. The PII masking is also relevant to our C2
(data exfiltration) attack category.

**Limitations:**
- Security scanning adds 100--250 ms latency per request
- No general observability (no OpenTelemetry, no distributed tracing)
- Focused narrowly on security -- lacks LLM routing, caching, or federation
- Smaller community and less mature than ContextForge


### 2.3 MCPX by Lunar.dev

| Field | Detail |
|-------|--------|
| **Maintainer** | Lunar.dev |
| **License** | Open source (custom) |
| **Language** | Go |
| **Stars** | 1,000+ |
| **Deployment** | Docker, Kubernetes |
| **Focus** | Enterprise governance + control plane |

**What it is:**
MCPX is a full AI control plane (not just a proxy) that provides a single
governed entry point for all agent-to-tool interactions.

**Key features:**
- Tool-level RBAC (global, service, and individual tool granularity)
- Identity-aligned attribution (who called what, when)
- Immutable audit trails spanning prompt > LLM decision > tool call > response
- Credential isolation per tool/server
- ~4 ms p99 latency overhead

**Why it matters for our testbed:**
MCPX's immutable audit trail captures the complete chain: prompt in, LLM
decision, tool call, API response. This is the most complete logging available
and would give us full context for dynamic scoring (session history, call
chains).

**Limitations:**
- Written in Go -- harder to integrate with our Python stack
- Enterprise-focused -- may be overengineered for research use
- Less documentation than ContextForge
- Governance features we do not need (multi-team RBAC, SSO)


### 2.4 Docker MCP Gateway

| Field | Detail |
|-------|--------|
| **Maintainer** | Docker Inc. |
| **License** | Open source |
| **Language** | Go |
| **Deployment** | Docker Compose (native) |
| **Focus** | Container-native simplicity |

**What it is:**
An MCP gateway tightly integrated with Docker. If your MCP servers already run
in containers, this gateway discovers and manages them automatically.

**Key features:**
- Compose-first workflow -- define MCP servers in docker-compose.yml
- Container-based security isolation (network sandboxing)
- CLI-driven, minimal configuration
- Automatic service discovery for Docker containers

**Why it matters for our testbed:**
Simplest option if we containerize all test servers. Zero configuration overhead.

**Limitations:**
- Very basic logging (container stdout only)
- No web UI, no admin panel
- No OpenTelemetry or structured observability
- Docker-only -- does not support bare-metal MCP servers
- Minimal security features


### 2.5 Envoy AI Gateway

| Field | Detail |
|-------|--------|
| **Maintainer** | Envoy Proxy / Tetrate |
| **License** | Apache 2.0 |
| **Language** | Go / C++ |
| **Deployment** | Kubernetes (Envoy sidecar) |
| **Focus** | Infrastructure-grade routing |

**What it is:**
An extension of the battle-tested Envoy proxy that adds MCP routing via a
custom MCPRoute resource. If you already run Envoy, adding MCP support is a
configuration change.

**Key features:**
- Production-grade proxy (used by major companies worldwide)
- MCP routing via Kubernetes custom resources
- Full Envoy ecosystem (rate limiting, circuit breaking, mTLS)
- Extremely low latency

**Why it matters for our testbed:**
Only relevant if we deploy on Kubernetes with Envoy already in place.

**Limitations:**
- Very heavy infrastructure requirement (Kubernetes + Envoy)
- Overkill for research -- built for production traffic at scale
- Complex configuration
- No MCP-specific logging or admin UI


### MCP Gateway Comparison

| Feature | ContextForge | Lasso | MCPX | Docker GW | Envoy AI |
|---------|-------------|-------|------|-----------|----------|
| OpenTelemetry | Yes | No | No | No | Via Envoy |
| Admin web UI | Yes | No | Yes | No | No |
| Real-time log viewer | Yes | No | Yes | No | No |
| Threat detection | Roadmap | Yes | No | No | No |
| PII masking | No | Yes | No | No | No |
| Tool reputation score | No | Yes | No | No | No |
| Tool-level RBAC | Basic | No | Yes | No | Via Envoy |
| Protocol translation | MCP+REST+gRPC | MCP only | MCP only | MCP only | MCP only |
| Python-native | Yes | Yes | No (Go) | No (Go) | No (C++) |
| Latency overhead | ~10ms | 100-250ms | ~4ms | <5ms | <1ms |
| Complexity | Medium | Low | Medium | Low | High |
| License | Apache 2.0 | MIT | Open | Open | Apache 2.0 |

---


## Part 3: Security Scanning Tools

These tools do not proxy traffic -- they scan MCP servers for vulnerabilities.
Useful for validating our attack templates and comparing detection approaches.


### 3.1 Proximity (AISafely)

- Scans MCP servers and identifies tools, prompts, and resources
- NOVA engine writes pattern-based rules to detect suspicious content
- Evaluates how tool descriptions might introduce security risks
- Useful for validating our static scoring approach

### 3.2 Cisco MCP Scanner

- Contextual and semantic analysis of MCP tool definitions
- Identifies hidden risks from how tools are described, invoked, and composed
- Focuses on supply-chain risk in MCP server integrations
- Complements our dynamic scoring by catching description-level risks

---


## Part 4: Recommendation for Our Research

### Minimum Viable Testbed (Quickest to Deploy)

| Role | Tool | Why |
|------|------|-----|
| Agent | **Obot** | Realistic LLM agent, web UI, built-in MCP |
| Gateway | **ContextForge** | Deep logging, admin UI, Python-native |
| Servers | **FastMCP** (existing) | Already built in our repo |
| Scripted attacks | **attack_runner.py** (existing) | Already built, 25 templates |

**Effort:** 1--2 days to set up Obot + ContextForge and connect to our test servers.

### Extended Testbed (Deeper Research)

Add to the above:

| Role | Tool | Why |
|------|------|-----|
| Threat detection benchmark | **Lasso** | Compare its detection vs. our scorer |
| Programmatic agents | **mcp-agent** | Python-native scripted LLM agents |
| Static scanning | **Proximity** | Validate our static scoring approach |

**Effort:** additional 2--3 days.

### Why ContextForge Over Alternatives

1. **Python-native** -- integrates directly with our `scorer_bridge.py`
2. **OpenTelemetry** -- structured tracing we can export and analyze
3. **mcpgateway.translate** -- wraps our existing stdio servers without changes
4. **Most feature-complete** -- federation, admin UI, real-time logs
5. **Active community** -- 3,500+ stars, IBM-backed, 7,000+ tests

### Why Obot Over Alternatives

1. **Full platform** -- agent + registry + gateway in one install
2. **Web UI** -- easy to demonstrate to stakeholders
3. **MCP-native** -- connects to MCP servers without adapters
4. **Realistic agent** -- LLM-driven tool selection, not scripted
5. **MIT license** -- no restrictions for academic use

---


## Sources

- [Obot GitHub](https://github.com/obot-platform/obot) | [Docs](https://docs.obot.ai)
- [IBM ContextForge GitHub](https://github.com/IBM/mcp-context-forge) | [Docs](https://ibm.github.io/mcp-context-forge/)
- [Goose GitHub](https://github.com/block/goose)
- [mcp-agent GitHub](https://github.com/lastmile-ai/mcp-agent)
- [Lasso MCP Gateway](https://www.lasso.security/resources/lasso-releases-first-open-source-security-gateway-for-mcp)
- [MCPX Lunar.dev](https://www.lunar.dev/product/mcp)
- [Proximity Scanner](https://www.helpnetsecurity.com/2025/10/29/proximity-open-source-mcp-security-scanner/)
- [Cisco MCP Scanner](https://blogs.cisco.com/ai/securing-the-ai-agent-supply-chain-with-ciscos-open-source-mcp-scanner)
- [Best Open Source MCP Gateways 2026 (Lunar.dev)](https://www.lunar.dev/post/the-best-open-source-mcp-gateways-in-2026)
- [MCP Gateway Comparison (Composio)](https://composio.dev/content/best-mcp-gateway-for-developers)
- [Top 10 Open Source AI Projects (GitHub Blog)](https://github.blog/open-source/maintainers/from-mcp-to-multi-agents-the-top-10-open-source-ai-projects-on-github-right-now-and-why-they-matter/)
- [Linux Foundation AAIF Announcement](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)
