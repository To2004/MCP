# Server-Side Threat Taxonomy for Model Context Protocol Systems

## Trust Inversion Threat Model

**Premise.** The MCP server is the protected asset. AI agents, their users, upstream data sources, and the transport layer are treated as potentially adversarial.

**Scope.** Only attacks in which the MCP server is the target. Attacks in which a malicious server targets agents or clients are excluded.

**Derivation.** Triangulated from three independent sources, each filtered to server-victim direction:

| Source | Original | After Filter |
|--------|:---:|:---:|
| Author's taxonomy (v2) | 38 | 38 (all server-victim) |
| Shen et al. MCP-38 (Vulcan, 2026) | 38 | 23 retained |
| Gateway Threat Model | 28 + M8 | 20 retained |

Deduplication yielded **57 unique threats** organized into **6 categories** based on attacker objective, plus **observability** as a cross-cutting dimension.

---

## Taxonomy Overview

```
MCP Server-Side Threat Taxonomy
│
├── C1  SERVER COMPROMISE — execute code or corrupt state on my server
│   ├── C1-01  Remote Code Execution via Tool Input
│   ├── C1-02  Command Injection via Unsanitized Input
│   ├── C1-03  Reverse Shell Establishment
│   ├── C1-04  Execution Environment Escape
│   ├── C1-05  Supply Chain Code Execution
│   ├── C1-06  Unauthorized File Write and Modification
│   ├── C1-07  Persistent Backdoor Installation
│   ├── C1-08  Audit Log Tampering and Evidence Destruction
│   ├── C1-09  SQL Injection
│   ├── C1-10  Non-Persistent State Corruption
│   └── C1-11  Cross-Session State Contamination
│
├── C2  DATA EXFILTRATION — extract data, secrets, or credentials from my server
│   ├── C2-01  Path Traversal and Directory Escape
│   ├── C2-02  Credential and API Key Extraction
│   ├── C2-03  Environment Variable Exposure
│   ├── C2-04  Database Credential Extraction
│   ├── C2-05  Server-Side Request Forgery (SSRF)
│   ├── C2-06  DNS Rebinding-Based Access Escalation
│   ├── C2-07  Data Exfiltration via Tool Output Channels
│   ├── C2-08  Systematic Data Overcollection
│   ├── C2-09  Multi-Tenant Data Leakage
│   ├── C2-10  Cross-Repository and Cross-Project Data Theft
│   ├── C2-11  Privacy Inversion via Cross-Tool Aggregation
│   ├── C2-12  Unauthorized Data Propagation
│   └── C2-13  Tool Manifest Reconnaissance
│
├── C3  ACCESS CONTROL SUBVERSION — exceed the access my server authorized
│   ├── C3-01  Excessive Privilege Exploitation
│   ├── C3-02  Out-of-Scope Parameter Injection
│   ├── C3-03  Privilege Escalation via Tool Chaining
│   ├── C3-04  Session Replay Attack
│   ├── C3-05  Temporal Accumulation and Session Drift
│   ├── C3-06  Identity Spoofing and User Impersonation
│   ├── C3-07  False Error Escalation
│   ├── C3-08  Rate Limit and Throttle Bypass
│   ├── C3-09  Unauthenticated Endpoint Access
│   ├── C3-10  Token Audience Misuse and Passthrough
│   ├── C3-11  Confused Deputy Exploitation
│   ├── C3-12  Unauthorized Resource Invocation
│   └── C3-13  Forced Execution Order and Control-Flow Hijack
│
├── C4  RESOURCE EXHAUSTION — crash, exhaust, or financially drain my server
│   ├── C4-01  Computational Resource Exhaustion
│   ├── C4-02  Storage Exhaustion
│   ├── C4-03  Forced Server Crash or Shutdown
│   ├── C4-04  Transport and Protocol-Level Abuse
│   ├── C4-05  Economic Resource Exhaustion (Denial of Wallet)
│   └── C4-06  Recursive and Circular Task Exhaustion
│
├── C5  OPERATIONAL MISUSE — misuse my tools causing legal, financial, or reputational harm
│   ├── C5-01  Retrieval-Augmented Data Exfiltration (RADE)
│   ├── C5-02  Cross-Server Exploitation
│   ├── C5-03  Parasitic Toolchain Composition
│   ├── C5-04  Upstream API Abuse (Provider Ban Induction)
│   ├── C5-05  Regulatory Compliance Violation Induction
│   ├── C5-06  Adversarial Content Generation via Tool Proxy
│   └── C5-07  Lateral Movement via Unrestricted Network Access
│
└── C6  AGENT-MEDIATED VECTORS — the agent is the weapon, my server is the target
    ├── C6-01  Direct Prompt Injection → Server Tool Abuse
    ├── C6-02  Indirect Prompt Injection → Server Tool Abuse
    ├── C6-03  Man-in-the-Middle and Transport Tampering
    └── C6-04  Local Transport Injection via stdio Descriptor Abuse
```

---

## Category Summary

| Cat. | Name | Objective | Attacks | T1 | T2 | STRIDE | CIA |
|:----:|------|-----------|:-------:|:--:|:--:|--------|:---:|
| C1 | Server Compromise | Execute code or corrupt state | 11 | 7 | 4 | T, E | I●●● C● A● |
| C2 | Data Exfiltration | Extract data or credentials | 13 | 4 | 9 | I | C●●● |
| C3 | Access Control Subversion | Exceed authorized access | 13 | 1 | 12 | E, S | C●● I●● A● |
| C4 | Resource Exhaustion | Crash or drain resources | 6 | 0 | 6 | D | A●●● |
| C5 | Operational Misuse | Cause legal/financial/reputational harm | 7 | 0 | 7 | R, T | I●● A● C● |
| C6 | Agent-Mediated Vectors | Weaponize agent against server | 4 | 0 | 4 | T, I | C●● I●● A● |
| | **Total** | | **54** | **12** | **42** | | |

> Plus 3 observability properties as cross-cutting dimension (see below).

---

## Observability as Cross-Cutting Dimension

Observability is not an attacker objective — it is the meta-condition that determines whether attacks in C1–C6 can be detected, investigated, and attributed. Rather than treating it as a category, each attack is tagged with an **observability rating**:

| Rating | Meaning |
|--------|---------|
| **High** | Standard server logging captures the attack (HTTP logs, file access logs, DB query logs) |
| **Medium** | Detectable only with MCP-specific instrumentation (tool invocation logs, parameter inspection) |
| **Low** | Requires semantic analysis of agent behavior (intent reconstruction, cross-tool correlation) |
| **None** | No detection mechanism exists without a dedicated MCP proxy or gateway |

Three specific observability failures amplify all C1–C6 attacks:

| ID | Property | Description |
|----|----------|-------------|
| O-1 | Absent tool invocation audit trail | MCP has no built-in logging of tool calls. Without an MCP proxy, attacks leave no trace. |
| O-2 | Decision provenance gap | No record of why the agent selected specific tools or parameters. Attribution is impossible. |
| O-3 | Compliance and forensic audit failure | Server operator cannot demonstrate to regulators that agent activities were appropriate. |

---

## C1 — Server Compromise

**Objective.** The attacker executes arbitrary code on the server host, or corrupts the server's files, database, or runtime state.

**Merge rationale.** Code execution and integrity violation share the same STRIDE category (Tampering), the same defensive surface (input validation, sandboxing, write-access controls), and the same blast radius (host-level compromise). From the server operator's perspective, "they ran their code on my server" and "they modified my files" are both instances of unauthorized modification.

**Defense surface.** Input sanitization, execution sandboxing, filesystem access controls, integrity monitoring.

| ID | Attack | Description | Tier | Src | Obs. | Evidence |
|----|--------|-------------|:----:|:---:|:----:|----------|
| C1-01 | Remote Code Execution via Tool Input | Crafted input to server tool is evaluated as code. | T1 | A,V | High | CVE-2025-5277 |
| C1-02 | Command Injection via Unsanitized Input | Unvalidated input concatenated into shell commands on the server. | T1 | A,V,G | High | CVE-2025-5277; CVE-2025-53967; CVE-2025-69256 |
| C1-03 | Reverse Shell Establishment | Post-exploitation interactive shell from server to attacker endpoint. | T1 | A | Med | DVMCP Ch. 9 |
| C1-04 | Execution Environment Escape | Attacker escapes sandbox, container, or VM to reach host. | T1 | A,V | Med | CVE-2025-53109 |
| C1-05 | Supply Chain Code Execution | Server's dependencies poisoned (npm, PyPI, typosquatting). | T2 | V | None | Smithery registry observations |
| C1-06 | Unauthorized File Write | Write, overwrite, or append to files beyond intended scope. | T1 | A,V | High | 3 CVEs |
| C1-07 | Persistent Backdoor Installation | SSH keys, cron jobs, or profile modifications for persistent access. | T1 | A | Med | CVE-2026-27825 |
| C1-08 | Audit Log Tampering | Modification or deletion of server logs to conceal attack evidence. | T2 | A | Low | CWE-117 |
| C1-09 | SQL Injection | Unvalidated input interpreted as SQL, enabling data modification. | T1 | A | High | Trend Micro |
| C1-10 | Non-Persistent State Corruption | Corruption of in-memory state, caches, or runtime variables. | T2 | A | Low | CWE-471 |
| C1-11 | Cross-Session State Contamination | Shared state from one session poisons subsequent sessions. | T2 | G | Low | Gateway M2.4 |

---

## C2 — Data Exfiltration and Credential Theft

**Objective.** The attacker extracts data, secrets, or credentials from the server.

**Defense surface.** Data access controls, DLP, taint tracking, network egress filtering, credential management.

| ID | Attack | Description | Tier | Src | Obs. | Evidence |
|----|--------|-------------|:----:|:---:|:----:|----------|
| C2-01 | Path Traversal and Directory Escape | Path traversal sequences escape intended sandbox. | T1 | A,V,G | High | 6 CVEs |
| C2-02 | Credential and API Key Extraction | Agent reads and exfiltrates server's stored secrets. | T1 | A,V,G | Med | DVMCP Ch. 7; MCPLIB |
| C2-03 | Environment Variable Exposure | Tools that access env vars expose embedded secrets. | T2 | A,V | Med | CWE-526 |
| C2-04 | Database Credential Extraction | DB connection strings extracted via file-read or env access. | T2 | A | Med | CWE-798 |
| C2-05 | Server-Side Request Forgery (SSRF) | Server makes requests to internal resources. 30% of MCP servers vulnerable. | T1 | A,V,G | Med | 3 CVEs; Merge.dev |
| C2-06 | DNS Rebinding-Based Access Escalation | Domain resolves to an external IP during validation and later rebinds to an internal IP. Verified in the MCP TypeScript SDK for unauthenticated localhost HTTP servers prior to 1.24.0. | T2 | A,V | Low | CVE-2025-66414 |
| C2-07 | Data Exfiltration via Tool Output | Data transmitted via legitimate output channels (email, issues, HTTP). | T2 | A,V,G | Low | GitHub MCP Data Heist |
| C2-08 | Systematic Data Overcollection | Agent queries far more records than task requires. | T2 | A,G | Med | Gateway M5.1 |
| C2-09 | Multi-Tenant Data Leakage | Isolation failure exposes other tenant's data. | T2 | A,V,G | Low | CVE-2026-25536 |
| C2-10 | Cross-Repository Data Theft | Server reads beyond intended repo/project boundary. | T2 | G | Med | Gateway M2.2 |
| C2-11 | Privacy Inversion via Cross-Tool Aggregation | Non-sensitive outputs combined into sensitive composite. | T2 | V | None | Vulcan MCP-25 |
| C2-12 | Unauthorized Data Propagation | Tool output relayed to unrelated destination. | T2 | G | Low | Gateway M5.2 |
| C2-13 | Tool Manifest Reconnaissance | Server capability map exposed to any connecting client. | T2 | V | Med | Vulcan MCP-34 |

---

## C3 — Access Control Subversion

**Objective.** The attacker obtains more access than the server intended to grant.

**Defense surface.** Authentication, authorization, session management, policy enforcement, consent mechanisms.

| ID | Attack | Description | Tier | Src | Obs. | Evidence |
|----|--------|-------------|:----:|:---:|:----:|----------|
| C3-01 | Excessive Privilege Exploitation | Over-broad tool permissions exploited beyond intended scope. | T1 | A,V,G | Med | DVMCP Ch. 3; MSB |
| C3-02 | Out-of-Scope Parameter Injection | Parameters outside intended input domain exploit weak validation. | T2 | A,V | Med | MSB; CWE-20 |
| C3-03 | Privilege Escalation via Tool Chaining | Cumulative effect of chained calls exceeds individual authorization. | T2 | A,V | Low | Vulcan MCP-04 |
| C3-04 | Session Replay Attack | Captured tokens/codes replayed; MCP lacks nonce/freshness. | T2 | A,V,G | Med | Vulcan MCP-03 |
| C3-05 | Temporal Accumulation and Session Drift | Permissions accumulate across long sessions without re-auth. | T2 | A | None | CWE-269 |
| C3-06 | Identity Spoofing and User Impersonation | Weak identity verification in MCP session layer. | T2 | A,G | Med | Gateway M1.1 |
| C3-07 | False Error Escalation | Fabricated errors trigger fallback paths granting elevated access. | T2 | A | Low | CWE-755 |
| C3-08 | Rate Limit and Throttle Bypass | Rate-counting logic circumvented. | T2 | A,V | Med | CWE-770 |
| C3-09 | Unauthenticated Endpoint Access | Server exposes tools without requiring authentication. | T2 | G | High | Gateway M1.4 |
| C3-10 | Token Audience Misuse and Passthrough | Server forwards tokens downstream without audience validation. | T2 | G,V | Low | MCP Security Best Practices |
| C3-11 | Confused Deputy Exploitation | Server's own elevated privileges exploited on attacker's behalf. | T2 | A,V,G | Low | Vulcan MCP-04; MCP spec |
| C3-12 | Unauthorized Resource Invocation | Agent invokes capability outside user's actual intent. | T2 | G | Low | Gateway M6.1 |
| C3-13 | Forced Execution Order and Control-Flow Hijack | Poisoned context forces attacker-determined tool execution order. | T2 | G | None | Gateway M6.2 |

---

## C4 — Resource Exhaustion and Service Degradation

**Objective.** The attacker crashes the server, exhausts its computational resources, or drains its financial budget.

**Defense surface.** Rate limiting, quotas, circuit breakers, timeouts, budget controls.

| ID | Attack | Description | Tier | Src | Obs. | Evidence |
|----|--------|-------------|:----:|:---:|:----:|----------|
| C4-01 | Computational Resource Exhaustion | Unbounded CPU or memory consumption renders server unresponsive. | T2 | A,V,G | High | CWE-400 |
| C4-02 | Storage Exhaustion | Disk filled through writes, log inflation, or cache abuse. | T2 | A | High | CWE-400 |
| C4-03 | Forced Server Crash or Shutdown | Unhandled exception or shutdown-triggering tool invocation. | T2 | A | High | CWE-248 |
| C4-04 | Transport and Protocol-Level Abuse | Malformed JSON-RPC, connection flooding, SSE abuse. | T2 | A,V | Med | Vulcan MCP-29 |
| C4-05 | Economic Resource Exhaustion (Denial of Wallet) | Unbounded consumption of metered APIs causing financial damage. | T2 | A,V,G | Med | Enkrypt AI; Gateway M7.2 |
| C4-06 | Recursive and Circular Task Exhaustion | Agent trapped in infinite tool invocation loops. | T2 | G,V | Med | Gateway M7.3 |

---

## C5 — Operational Misuse and Policy Violation

**Objective.** The attacker misuses the server's legitimate tools in ways that cause legal, financial, or reputational harm to the server operator — without necessarily exploiting a technical vulnerability.

**Defense surface.** Policy enforcement, content filtering, usage monitoring, data-flow governance.

| ID | Attack | Description | Tier | Src | Obs. | Evidence |
|----|--------|-------------|:----:|:---:|:----:|----------|
| C5-01 | Retrieval-Augmented Data Exfiltration (RADE) | Server's retrieval tools locate data; output/communication tools exfiltrate it. | T2 | A | Low | GitHub MCP Data Heist analog |
| C5-02 | Cross-Server Exploitation | Access to one server facilitates attacks on another through shared agent context. | T2 | A | None | ProtoAmp (arXiv:2601.17549); OWASP Agentic ASI07 as framework cross-walk |
| C5-03 | Parasitic Toolchain Composition | Individually benign tools chained into malicious composite workflow. | T2 | A,V | None | Vulcan MCP-17; Docker MCP; MSB |
| C5-04 | Upstream API Abuse (Provider Ban Induction) | Excessive/malicious requests get server banned from upstream APIs. | T2 | A | Med | OWASP LLM10 |
| C5-05 | Regulatory Compliance Violation Induction | Regulated data fed through server tools creates liability. | T2 | A | Low | CoSAI WS4 |
| C5-06 | Adversarial Content Generation via Tool Proxy | Toxic/illegal content generated through server's tools. | T2 | A | Med | OWASP LLM09 |
| C5-07 | Lateral Movement via Unrestricted Network Access | Compromised server pivots into internal systems. 33% of MCP tools allow unrestricted network. | T2 | V | Low | Docker MCP Security |

---

## C6 — Agent-Mediated Attack Vectors

**Objective.** The attacker compromises the communication channel or manipulates the agent into becoming an unwitting weapon against the server.

**Rationale for separate category.** These attacks are not on the agent — they are *through* the agent. The server is the ultimate target. Prompt injection does not harm the agent; it causes the agent to harm the server by abusing its tools. From the server's perspective, these arrive as formally valid requests that are substantively unauthorized. No existing MCP benchmark measures these from the server-defender perspective. This constitutes the primary research gap.

**Defense surface.** Prompt injection detection, transport security, context isolation, taint propagation.

| ID | Attack | Description | Tier | Src | Obs. | Evidence |
|----|--------|-------------|:----:|:---:|:----:|----------|
| C6-01 | Direct Prompt Injection → Server Tool Abuse | Adversarial user instructions override agent behavior, causing it to invoke server tools maliciously. MSB reports high ASR. | T2 | V | None | Vulcan MCP-19; MSB; OWASP LLM01 |
| C6-02 | Indirect Prompt Injection → Server Tool Abuse | Instructions embedded in external data (documents, web pages, DB records) consumed via server's own retrieval tools cause agent to abuse server's actuation tools. Confirmed in production. | T2 | V | None | Vulcan MCP-20; GitHub MCP Data Heist |
| C6-03 | Man-in-the-Middle and Transport Tampering | JSON-RPC messages intercepted and modified; MCP does not mandate TLS validation. | T2 | V | Low | Vulcan MCP-28 |
| C6-04 | Local Transport Injection via stdio | Co-located process injects into server's stdin/stdout channel. | T2 | V | Low | Vulcan MCP-30 |

---

## Classification Bands

The six categories form three conceptual bands that structure the paper's argument:

| Band | Categories | Character | Benchmark Coverage |
|------|-----------|-----------|-------------------|
| **Classical server security** | C1, C2 | Same threats as any web server. 11 attack classes have direct server-victim CVE evidence in production MCP implementations; additional Tier-1 entries rely on DVMCP challenge evidence. | Well-covered by traditional security tools |
| **Agent-amplified threats** | C3, C4, C5 | Classical access control + MCP-specific: tool chaining, confused deputy, compliance induction, RADE. Requests look legitimate individually. | Partially covered; policy enforcement gaps |
| **MCP-specific (research gap)** | C6 + O-1/O-2/O-3 | Prompt injection as server-side weapon, transport manipulation, observability void. | **No existing benchmark measures these from the server's perspective** |

---

## Framework Cross-Walk

### OWASP Top 10 for LLM Applications (2025)

| OWASP LLM | Name | Mapped Attacks |
|-----------|------|----------------|
| LLM01 | Prompt Injection | C6-01, C6-02 |
| LLM02 | Sensitive Information Disclosure | C2-02, C2-03, C2-05, C2-11, C2-13 |
| LLM03 | Supply Chain Vulnerabilities | C1-05 |
| LLM05 | Improper Output Handling | C1-02, C1-04, C1-09, C6-03 |
| LLM06 | Excessive Agency | C3-01, C3-03, C3-11, C3-12, C5-03 |
| LLM09 | Misinformation | C5-06 |
| LLM10 | Unbounded Consumption | C4-01, C4-05, C4-06 |

### OWASP Top 10 for Agentic Applications (2026)

| OWASP Agentic | Name | Mapped Attacks |
|---------------|------|----------------|
| ASI01 | Agent Goal Hijack | C6-01, C6-02 |
| ASI02 | Tool Misuse and Exploitation | C3-01, C3-03, C5-03 |
| ASI03 | Identity and Privilege Abuse | C3-06, C3-10, C3-11 |
| ASI05 | Unexpected Code Execution | C1-01, C1-02, C1-04 |
| ASI07 | Insecure Inter-Agent Communication | C5-02, C6-03, C6-04 |
| ASI08 | Cascading Failures | C2-09, C4-01, C4-06, C5-07 |
| ASI09 | Human-Agent Trust Exploitation | C3-05 |
| ASI10 | Rogue Agents | O-1, O-2 |

---

## Source Contribution Analysis

| Source | Sole contributor | Shared (2 sources) | Shared (all 3) | Total |
|--------|:---:|:---:|:---:|:---:|
| Author [A] | 12 | 16 | 10 | 38 |
| Vulcan [V] | 4 | 12 | 7 | 23 |
| Gateway [G] | 5 | 10 | 5 | 20 |

### Unique to each source (server-victim only)

**Author [A] — 12 exclusive attacks:**
C1-03 Reverse shell, C1-07 Backdoor install, C1-08 Log tampering, C1-10 State corruption, C2-04 DB cred extraction, C3-05 Temporal accumulation, C3-07 False error escalation, C4-02 Storage exhaustion, C4-03 Forced crash, C5-04 Upstream API abuse, C5-05 Compliance violation, C5-06 Toxic content generation.

**Vulcan [V] — 4 exclusive attacks:**
C1-05 Supply chain, C2-11 Privacy inversion, C2-13 Manifest reconnaissance, C5-07 Lateral movement.

**Gateway [G] — 5 exclusive attacks:**
C1-11 Cross-session contamination, C2-10 Cross-repo theft, C3-09 Unauthenticated access, C3-12 Unauthorized invocation, C3-13 Control-flow hijack.

---

## Observability Distribution

| Rating | Count | % | Description |
|--------|:-----:|:-:|-------------|
| High | 10 | 19% | Standard server logging detects |
| Medium | 19 | 35% | MCP-specific instrumentation needed |
| Low | 16 | 30% | Semantic analysis of agent behavior required |
| None | 9 | 17% | No detection without dedicated MCP proxy |

**Key finding:** 46% of attacks (Low + None) require capabilities that no existing MCP security tool provides. The observability gap is not a single missing feature — it is a structural property of the current MCP ecosystem that compounds every other threat category.


---

## Editorial Review Addendum (April 2026)

This addendum captures source-verification and taxonomy-structure corrections identified during a cross-check of this file against the attack catalog and public sources.

### Source corrections

- **C1-02 command injection:** `CVE-2025-6514` should **not** be used as primary evidence for a server-victim MCP server command-injection entry. It is an **mcp-remote** issue triggered when a client/host connects to an untrusted server, so the victim is the client/host rather than the MCP server. Use the server-victim CVEs already present in the attack catalog instead.
- **C2-06 DNS rebinding:** `CVE-2025-66414` is real, but it is narrower than the original row implied. It applies to **HTTP-based localhost MCP servers without authentication** in the TypeScript SDK prior to `1.24.0`.
- **C5-02 cross-server exploitation:** `ProtoAmp` is the stronger direct source because it discusses MCP architectural trust propagation and capability-attestation gaps. `OWASP Agentic ASI07` is better treated as a framework-level mapping, not the primary evidence line.

### Coverage and count check

- The detailed attack catalog contains **55 Tier 1+2 attacks**, while this taxonomy presents **54**. The missing item is **4.2 Data Exfiltration via Query Abuse**, which is implicitly merged into **C1-09 SQL Injection** but that merge is not documented.
- Because the two files use different numbering schemes (`1.x–19.x` versus `C1-xx–C6-xx`), a reader cannot cross-reference them reliably without a mapping table.
- If the paper keeps both files, add a **legacy-ID ↔ taxonomy-ID mapping table**. If only one document survives into the paper, prefer the taxonomy numbering.

### Scope correction

- **C2-11 Privacy Inversion via Cross-Tool Aggregation** is the weakest server-victim fit. In the strict threat model, the server is not breached and each tool may behave correctly within scope; the privacy harm emerges from the **agent's aggregation/inference**.
- Recommended handling: **demote C2-11 to Tier 3** or reframe it as a **server design flaw that enables privacy-violating aggregation**, not a core runtime attack on the server.

### Merge recommendations

The following merges are recommended for the paper version because they reduce redundancy without losing analytical coverage:

| Priority | Merge | Recommendation |
|---|---|---|
| Strong | Reverse Shell into RCE / code-execution family | Treat reverse shell as a payload or post-exploitation outcome, not a separate top-level attack |
| Strong | CPU/Memory Exhaustion + Storage Exhaustion | Merge into a single `Resource Exhaustion` family with resource-specific subtypes |
| Strong | RADE + Parasitic Toolchain | Keep one canonical `multi-stage exfiltration via tool chaining` entry, with RADE as the retrieval-triggered subtype |
| Strong | Data Exfiltration via Tool Output + Unauthorized Data Propagation | Merge into one output-channel / cross-tool exfiltration entry |
| Strong | Query-abuse exfiltration into SQL Injection | Explicitly document that the exfiltration variant is merged into SQL injection |
| Moderate | Confused Deputy + Adversarial/Toxic Content via Tool Proxy | Treat toxic content generation as a misuse/confused-deputy subtype |
| Moderate | Direct + Indirect Prompt Injection | Keep one canonical prompt-injection-to-server-abuse entry with two delivery variants |
| Debatable | Excessive Privilege Exploitation + Out-of-Scope Parameter Injection | Keep separate unless you want a more compact paper taxonomy; they reflect different defense failures |

### Tier-2 evidence quality

Tier 2 is currently too broad. A reviewer can reasonably ask whether some entries are:
1. supported by **indirect MCP evidence** (for example Vulcan/Gateway/protocol studies), or
2. mostly **classical CWE projection** into the MCP setting.

Recommended split:
- **Tier 2a — indirect MCP evidence**
- **Tier 2b — projected server-side pattern without MCP-specific measurement yet**

### C5 versus C6 clarification

The current document says the taxonomy is organized by **attacker objective**, but **C6** is actually a **delivery / mediation mechanism** category rather than an objective. That creates conceptual overlap with C5.

Recommended fix:
- Either redefine **C6** explicitly as **delivery vectors / mediation vectors** orthogonal to C1–C5, or
- move the agent-mediated C5 entries into C6 and keep C5 only for non-injection operational misuse.

