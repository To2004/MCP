# MCP Server Attacks — Cheat Sheet

Quick-reference ordered by the 6 categories from the threat taxonomy.
**Threat model:** agent / user is the attacker — MCP server is the victim.

---

## 1. SERVER COMPROMISE

> Execute code or corrupt state on the server.

| ID | Name | What it does | Det. |
|----|------|-------------|------|
| 1 | **Reverse Shell** | Injects a payload that makes the server open an outbound shell to the attacker — full interactive host access. | High |
| 3 | **SSH Key Injection** | Abuses a file-write tool to append attacker's public key to `~/.ssh/authorized_keys` — persistent remote login, no password needed. | High |
| 4 | **Log Tampering** | Deletes or overwrites audit logs after an attack — destroys forensic evidence, breaks incident response. | Med |
| N3 | **Semantic Data Poisoning** | Writes plausible-but-false data through valid write operations — every record passes validation, but the dataset is quietly wrong. | None |
| M1 | **SQL Injection** *(maybe)* | Injects SQL fragments through a query tool to read, modify, or delete database records. | Med |
| M2 | **State Corruption** *(maybe)* | Repeated tool calls alter config or cache until the server behaves inconsistently or unsafely. | High |

---

## 2. DATA EXFILTRATION

> Extract data, secrets, or credentials from the server.

| ID | Name | What it does | Det. |
|----|------|-------------|------|
| 2 | **Env Var / Token Extraction** | Tricks the server into printing environment variables (`printenv`, `/proc/self/environ`) — leaks API keys, JWTs, cloud credentials. | Med |
| 5 | **Database Credential Exposure** | Reads config files to find DB connection strings (e.g. `postgres://admin:secret@…`) — bypasses all MCP-layer controls. | Med |
| 9 | **SSRF** | Gives a fetch tool an internal URL (`169.254.169.254` cloud metadata, internal APIs) — server makes requests the attacker cannot reach directly. | High |
| 16 | **Scraping / Systematic Extraction** | Repeatedly queries every record/document until the full protected dataset is replicated — each request looks normal, the pattern is the attack. | V.High |
| 17 | **Multi-Tenant Data Leakage** | Broken session/cache/transport isolation causes Tenant A's data to appear in Tenant B's session — cross-tenant breach. | V.High |
| N1 | **Timing Side-Channel Inference** | Measures response latency differences to map which users/files/DB entries exist — no data returned, bypasses all content guardrails. | V.High |
| N7 | **Behavioral Fingerprinting** | Probes error formats, response times, and boundary behaviors to deduce the server's exact tech stack — enables precise targeted attacks. | Med |
| M5 | **Data Exfil via Tool Output** *(maybe)* | Secrets read through one tool are posted through a legitimate outbound channel (GitHub issue, email, chat). | V.High |

---

## 3. ACCESS SUBVERSION

> Exceed the access the server authorized.

| ID | Name | What it does | Det. |
|----|------|-------------|------|
| 6 | **Privilege Escalation via Tool Chaining** | Combines individually-allowed tools in sequence (read config → write policy → trigger exec) to reach a privileged effect no single call could achieve. | V.High |
| 10 | **Replay Attack** | Captures a valid authenticated tool call and re-sends it — server repeats a one-time/expired action (financial, admin, destructive). | High |
| 11 | **Session Abuse / Temporal Accumulation** | Spreads mild requests across many turns (enumerate → read secrets → exfiltrate) — slow-burn pattern evades per-request defenses. | V.High |
| 12 | **False Error Escalation** | Deliberately triggers errors to push the server into a diagnostic/fallback path that has wider permissions than the normal flow. | V.High |
| 18 | **Throttle Bypass** | Spreads requests across sessions, identities, or parameters so rate counters never trigger — enables scraping/exhaustion at scale. | High |
| C1 | **CSRF / DNS Rebinding** | Malicious webpage sends a POST to a locally running MCP server — no Origin check means any website can trigger tool execution (file read, RCE). CVEs: CVE-2026-33252, CVE-2026-34742 | V.High |
| C2 | **SSE Stream Hijacking** | Stolen session ID lets attacker connect to the SSE stream and intercept all real-time tool responses intended for the legitimate agent. CVE: CVE-2026-33946 | V.High |
| C3 | **OAuth Delegation Confused Deputy** | MCP OAuth proxy completes the flow without verifying user consent — attacker silently gets a token under the victim's identity and gains full tool access. CVE: CVE-2026-27124 | V.High |

---

## 4. EXHAUSTION

> Consume server resources until service degrades or fails.

| ID | Name | What it does | Det. |
|----|------|-------------|------|
| 7 | **Resource Exhaustion** | Floods CPU / memory / disk with huge file generation or expensive processing until service crashes (DoS). | Low |
| 8 | **Recursive / Circular Task Exhaustion** | Causes the agent to loop tool calls indefinitely (output feeds next call forever) — availability lost with no classical exploit payload. | Med |
| 15 | **Denial of Wallet** | Spams thousands of calls through a server wrapper around a paid API — drives up costs until quota exhausted or account suspended. | V.High |
| N2 | **Resource Lock Starvation** | Opens DB connections / file locks / SSE slots and never releases them — pool fills up, all users get timeouts; CPU looks fine, server is deadlocked. | V.High |
| N6 | **Idempotency Abuse (Valid-Data Flooding)** | Calls a create/write tool tens of thousands of times with slightly varied valid data — no crash, but the data store is polluted and search/metrics are destroyed. | High |
| M3 | **Protocol-Level Exhaustion** *(maybe)* | Oversized or malformed JSON-RPC payloads overwhelm the server's protocol/parser layer. | Med |

---

## 5. MISUSE

> Abuse legitimate server capabilities for harmful purposes.

| ID | Name | What it does | Det. |
|----|------|-------------|------|
| 13 | **RADE** | Poisoned retrieved document tells the agent to read `~/.ssh/id_rsa` and send it out — server tools weaponized via external content. | V.High |
| 14 | **Tool Misuse / Confused Deputy** | Uses a legitimate tool (email, publish) for a malicious purpose (phishing, leaking secrets) — tool works correctly, intent is wrong. | V.High |
| 19 | **Toxic Content Generation** | Uses the server's outbound tools (messaging, content gen) to produce abusive/fraudulent content through the operator's account. | High |
| N4 | **Output-Based Downstream Injection** | Stores `=CMD(...)` formulas or log-forging newlines in valid fields — harmless in the server, executes when admin exports CSV or SIEM ingests logs. | High |
| M4 | **Cross-Server Exploitation** *(maybe)* | Access to one MCP server is leveraged to attack a second server through shared context or weak cross-server trust. | V.High |

---

## 6. AGENT-MEDIATED

> Exploits agent behavior to cause or amplify server harm.

| ID | Name | What it does | Det. |
|----|------|-------------|------|
| 20 | **Indirect Prompt Injection → Tool Abuse** | Hidden instructions in a retrieved webpage/doc steer the agent to call dangerous server tools — server sees valid calls, origin is external. | None |
| 21 | **Alignment Failure / Goal Misalignment** | Agent interprets "solve efficiently" as permission to use broad tools, skip safeguards, or over-query — no exploit, just wrong behavior. | Low |
| N5 | **Context Window Manipulation** | Triggers huge server responses to flood the agent's context window, pushing safety instructions out of attention ("lost in the middle") — next tool calls skip forgotten guardrails. | None |

---

## Detection Difficulty Legend

| Level | Meaning |
|-------|---------|
| **None** | Cannot be detected at the server level with current techniques |
| **Low** | Hard to detect; requires heavy instrumentation |
| **Med** | Detectable with moderate monitoring effort |
| **High** | Detectable but requires specific controls not usually in place |
| **V.High** | Detectable only with protocol-layer or cross-request analysis |
