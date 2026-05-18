# MCP Primitive Operations — Ranking References

This document explains what each risk rank in `mcp-primitive-operations.csv` is grounded in.
The ranking uses three independent frameworks so no single subjective judgment drives it.

## Caveats up-front

The **sensitivity, blast-radius, and irreversibility numbers** in the CSV are
heuristic best-fits to the project's scoring model (see `scoring-reference.md`).
The **relative ordering** of operations — execute > delete > send > write … — is
grounded in the sources below. If you need the numbers to be defensible,
map each operation to the relevant CVSS v3.1 or AIVSS metric and use those
values directly.

---

## Three frameworks used

### 1. MITRE ATT&CK (empirical — most objective)

MITRE ATT&CK ranks techniques by prevalence in real-world intrusions and by
the tactic they serve. Operations that appear in late-stage tactics
(Execution, Exfiltration, Impact) are ranked higher than early-stage ones
(Discovery, Collection). This is observation-based, not opinion-based.

**Source:** MITRE ATT&CK Enterprise Matrix v15 — https://attack.mitre.org/

### 2. CVSS v3.1 impact subscores (standardised)

The CVSS Impact Score covers Confidentiality, Integrity, and Availability,
each rated None / Low / High. Operations that score High on multiple
dimensions sit in higher risk tiers. Scope=Changed (affects components
beyond the vulnerable one) escalates the score further.

**Source:** NIST NVD / FIRST CVSS v3.1 specification —
https://www.first.org/cvss/v3.1/specification-document

### 3. OWASP AIVSS v0.5 (AI-specific extension, newer)

Extends CVSS with Agent Autonomy, Lateral Leverage, and Decision Criticality
scores. Operations that an agent can perform autonomously (no human in the
loop) with high lateral reach score higher here.

**Source:** OWASP AI Vulnerability Scoring System v0.5 (Paper 18 in the
annotated bibliography) — https://aivss.owasp.org/

---

## Operation-by-operation justification

### Rank 1 — execute (score 75)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | **T1059** Command and Scripting Interpreter — appears in every major intrusion study; sits in the Execution tactic which directly precedes Persistence, Privilege Escalation, and Impact |
| CVSS v3.1 | Scope=**Changed**, C=High, I=High, A=High → CVSS base ≈ 10.0 (critical ceiling) |
| OWASP AIVSS | Agent Autonomy=High, Lateral Leverage=High, Decision Criticality=Critical |
| Project lit. | Paper 1 (Radosevich 2025): malicious code execution is the primary demonstrated MCP exploit; Paper 12 (ToolEmu): even the safest agent fails with severe outcomes 23.9% of the time via tool execution |

---

### Rank 2 — delete (score 45)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | **T1485** Data Destruction, **T1490** Inhibit System Recovery — both sit in the Impact tactic, the last stage of an intrusion kill chain |
| CVSS v3.1 | Scope=Unchanged, C=None, I=High, A=High → typically scores 7.1–8.4 (High) |
| OWASP AIVSS | Irreversibility is the dominant factor; no AI-specific amplification but Decision Criticality=High |
| NIST FIPS 199 | Availability=High (system unavailable); Integrity=High (data destroyed); high-water mark = High categorisation |

---

### Rank 3 — send (score 32)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | **T1048** Exfiltration Over Alternative Protocol, **T1567** Exfiltration Over Web Service — Exfiltration tactic; agent-controlled destination enables data theft without leaving the MCP scope |
| CVSS v3.1 | Scope=**Changed** (data leaves the system boundary), C=High → elevates to High/Critical range |
| OWASP API Top 10 | API3:2023 Broken Object Property Level Authorization covers excessive data exposure via outbound calls |
| Project lit. | Paper 13 (InjecAgent): data exfiltration is one of the two primary attack intentions in indirect prompt injection; Paper 14 (AgentDojo): Slack/email tools used as exfil channels in 97 real task benchmarks |

---

### Rank 4 — write / edit (score 16)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | **T1565** Data Manipulation (write to stored data), **T1105** Ingress Tool Transfer (write attacker payload) |
| CVSS v3.1 | Scope=Unchanged, C=None, I=High, A=None → typically 6.5–7.5 (High) |
| OWASP AIVSS | Lateral Leverage moderate; irreversibility escalates for log/audit targets |
| Project lit. | Paper 25 (Caging the Agents): filesystem write and database write are two of the six threat domains in the production healthcare deployment |

---

### Rank 5 — move / configure (score 12)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | move → **T1074** Data Staged; configure → **T1562** Impair Defenses (specifically T1562.001 Disable or Modify Tools — lowering a log level is the textbook example) |
| CVSS v3.1 | configure: Scope=Unchanged, I=Low, A=Low, but Integrity of security controls affected → escalates under CVSS Environmental metrics |
| Project scoring | Irreversibility ×2 applied because both operations break audit references or forensic visibility |

---

### Rank 6 — authenticate (score 10)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | **T1078** Valid Accounts, **T1528** Steal Application Access Token, **T1539** Steal Web Session Cookie — all in Credential Access tactic |
| CVSS v3.1 | The vulnerability is in the *obtained* credential, not the act; once obtained, subsequent calls inherit its permissions — Scope=Changed potential |
| OWASP API Top 10 | API2:2023 Broken Authentication |
| Project lit. | Paper 26 (Zero-Trust Identity): agent credential management is identified as the primary gap in current MCP trust architectures |

---

### Rank 7 — query / search (score 9)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | **T1213** Data from Information Repositories, **T1530** Data from Cloud Storage — Collection tactic; bulk reads are categorised separately from single reads because of volume |
| CVSS v3.1 | C=High (bulk disclosure), I=None, A=None → typically 7.5 (High) when bulk |
| Project lit. | Paper 13 (InjecAgent): 62 attacker tools in the benchmark; bulk query is the primary data collection step before exfiltration |

---

### Rank 8 — read (score 8)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | **T1005** Data from Local System, **T1083** File and Directory Discovery |
| CVSS v3.1 | C=High (if sensitive file), I=None, A=None → 6.5–7.5 when file is sensitive; lower for public data |
| NIST SP 800-60 | Sensitivity rating varies by information type — this is where SP 800-60 Vol 2 catalog should be consulted for the specific file/record type |

---

### Rank 9 — list / copy / post (score 6)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | list → **T1083** File and Directory Discovery, **T1087** Account Discovery (Discovery tactic — early-stage, lower severity); copy → **T1020** Automated Exfiltration; post → **T1048** |
| CVSS v3.1 | list: C=Low (metadata only, not content), I=None → 3–5 (Medium); copy/post: treated like read + send but compounded |
| Project lit. | Paper 4 (MCP at First Glance): enumeration of tool names is the first step in 7.2% of vulnerable server exploitation paths |

---

### Rank 10 — subscribe / fetch (score 4)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | subscribe → **T1557** Adversary-in-the-Middle (persistent channel); fetch → no direct ATT&CK technique, but SSRF maps to CWE-918 |
| OWASP | fetch: **OWASP A10:2021 Server-Side Request Forgery** — specifically listed as an emerging risk when URL is agent-controlled |
| CVSS v3.1 | fetch (SSRF): C=Low–High depending on internal target reachability |

---

### Rank 11 — ping (score 1)

| Framework | Evidence |
|-----------|----------|
| MITRE ATT&CK | **T1016** System Network Configuration Discovery — lowest-impact Discovery sub-technique |
| CVSS v3.1 | No standard CVE is assigned to a ping by itself; nearest analog scores 0–2 (Informational) |

---

## What to do if you need fully reproducible numbers

1. For each operation, look up the MITRE ATT&CK technique ID in the table above.
2. Find a representative CVE for that technique in the NVD and read its CVSS vector.
3. Map CVSS C/I/A to Sensitivity (C) and Blast Radius (I+A) and Irreversibility from `scoring-reference.md`.
4. That gives you numbers derived from published CVE data, not judgment.

Alternatively, apply OWASP AIVSS directly if you want AI-agent-specific scoring
(Agent Autonomy and Lateral Leverage dimensions are more appropriate than raw CVSS
for MCP tool-call contexts).

---

## References

- MITRE ATT&CK Enterprise v15 — https://attack.mitre.org/
- CVSS v3.1 Specification — https://www.first.org/cvss/v3.1/specification-document
- OWASP AIVSS v0.5 — https://aivss.owasp.org/
- OWASP API Security Top 10 2023 — https://owasp.org/API-Security/
- OWASP Top 10 2021 (A10 SSRF) — https://owasp.org/Top10/
- NIST FIPS 199 / SP 800-30 / SP 800-60 — see `nist-guidelines.md`
- Papers 1, 4, 10, 12, 13, 14, 18, 25, 26 — see annotated bibliography
