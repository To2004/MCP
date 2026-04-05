# MCP Server Threat Taxonomy

> **Perspective:** You built a legitimate MCP server. What can people (or agents) do to hurt you?
>
> 6 categories · 38 attacks · organized by attacker goal

---

```
MCP Server Threat Taxonomy
│
├── 1  COMPROMISE — run unauthorized code on my server
│   ├── 1.1  Arbitrary Code Execution              [T1] CVE-2025-5277
│   ├── 1.2  Reverse Shell                          [T1] DVMCP Ch9
│   ├── 1.3  Command Injection                      [T1] 3 CVEs
│   └── 7.1  Sandbox / Container Escape             [T1] CVE-2025-53109
│
├── 2  STEAL — extract my data, secrets, or credentials
│   ├── 2.1  Path Traversal (file read)             [T1] 6 CVEs
│   ├── 3.1  API Key / Token Extraction             [T1] DVMCP Ch7
│   ├── 3.2  Environment Variable Exposure          [T2]
│   ├── 3.3  Database Credential Extraction         [T2]
│   ├── 4.2  Data Exfiltration via Query            [T2]
│   ├── 8.1  SSRF (reach internal network)          [T1] 3 CVEs
│   ├── 8.2  DNS Rebinding                          [T2]
│   ├── 16.1 Systematic Data Extraction (scraping)  [T2]
│   └── 16.2 Multi-Tenant Data Leakage             [T2] CVE-2026-25536
│
├── 3  TAMPER — modify my files, database, or state
│   ├── 2.2  Unauthorized File Write                [T1] 3 CVEs
│   ├── 2.3  SSH Key Injection (persistent backdoor)[T1] CVE-2026-27825
│   ├── 2.4  Log Tampering / Evidence Destruction   [T2]
│   ├── 4.1  SQL Injection                          [T1] Trend Micro
│   └── 4.3  State Corruption                       [T2]
│
├── 4  BYPASS — get more access than I authorized
│   ├── 5.1  Excessive Privilege Exploitation       [T1] DVMCP Ch3
│   ├── 5.2  Out-of-Scope Parameter Injection       [T2]
│   ├── 5.3  Privilege Escalation via Tool Chaining [T2]
│   ├── 10.1 Replay Attack                          [T2]
│   ├── 10.2 Session Abuse / Temporal Accumulation  [T2]
│   ├── 11.1 User Impersonation                     [T2]
│   ├── 11.2 False Error Escalation                 [T2]
│   └── 17.1 Rate Limit / Throttle Bypass           [T2]
│
├── 5  DISRUPT — crash, exhaust, or financially drain my server
│   ├── 6.1  CPU / Memory Exhaustion                [T2]
│   ├── 6.2  Disk Exhaustion                        [T2]
│   ├── 6.3  Forced Server Shutdown                 [T2]
│   ├── 8.3  Protocol-Level Exploitation            [T2]
│   └── 15.1 Denial of Wallet (API cost drain)      [T2]
│
└── 6  ABUSE — misuse my tools causing legal, financial, or reputational harm
    ├── 12.1 RADE (retrieval → weaponize my tools)  [T2]
    ├── 13.1 Cross-Server Exploitation              [T2]
    ├── 13.2 Confused Deputy / Tool Misuse          [T2]
    ├── 13.3 Parasitic Toolchain (3-stage chain)    [T2]
    ├── 15.2 Upstream API Abuse (get me banned)      [T2]
    ├── 16.3 Compliance Violation (send me bad data) [T2]
    └── 17.2 Toxic Content via My Tools             [T2]
```

---

### Category Summary

| # | Category | What it means | Attacks | Tier 1 | Tier 2 |
|---|----------|--------------|:-------:|:------:|:------:|
| **1** | **Compromise** | They run their code on my server | 4 | 4 | 0 |
| **2** | **Steal** | They take my data or secrets | 9 | 4 | 5 |
| **3** | **Tamper** | They change my files, DB, or state | 5 | 3 | 2 |
| **4** | **Bypass** | They get access I didn't authorize | 8 | 1 | 7 |
| **5** | **Disrupt** | They crash me or drain my wallet | 5 | 0 | 5 |
| **6** | **Abuse** | They misuse my tools to harm me or others | 7 | 0 | 7 |
| | **Total** | | **38** | **12** | **26** |

---

### Category → CIA Mapping

| Category | Confidentiality | Integrity | Availability |
|----------|:-:|:-:|:-:|
| 1 — Compromise | | **●●●** | ● |
| 2 — Steal | **●●●** | | |
| 3 — Tamper | | **●●●** | |
| 4 — Bypass | ●● | ●● | ● |
| 5 — Disrupt | | | **●●●** |
| 6 — Abuse | ● | ●● | ● |

> ●●● = primary pillar · ●● = secondary · ● = sometimes affected

---

### Key Observation

Categories 1–3 are **classic server security** — the same vulnerabilities you'd find in any web server (command injection, path traversal, SQL injection). The MCP ecosystem has **16 real CVEs** proving these exist in production MCP servers.

Categories 4–6 are **MCP-specific or agent-specific** — these emerge because an AI agent is the client. Replay attacks, tool chaining, confused deputy, denial of wallet, and compliance violations are harder to defend against because the requests look legitimate individually. **No existing MCP benchmark measures these.** This is the research gap.

---

### Tier 3 — Adjacent Ecosystem Threats (not in main taxonomy)

| # | Attack | Why excluded |
|---|--------|-------------|
| 9.2 | Supply-Chain Poisoning | Build-time, not runtime |
| 14.1 | Autonomy Abuse | Not an attack; alignment failure |
| 14.2 | Communication Channel Weaponization | Server is indirect victim; overlaps with 13.2 |
