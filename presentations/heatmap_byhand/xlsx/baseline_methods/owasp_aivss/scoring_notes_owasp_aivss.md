# OWASP AIVSS v0.5 Scoring Notes

OWASP Agentic AI Vulnerability Scoring System v0.5 applied to three MCP server risk matrices.
Reference: Huang, Bargury et al. (2025). Extends CVSS v3.1 with Agentic AI Risk Amplification Factors (AARFs).

## Method Summary

### Base Score

Each cell starts from a CVSS-style base score (0-10) derived from:

- Confidentiality / Integrity / Availability impact of the resource (directory tier, data category, or channel sensitivity)
- Exploitability of the tool (direct data access vs. metadata enumeration)
- A filetype or data-category modifier that reflects parser risk, execution risk, and information density

### Agentic Amplification Factors (AARFs)

Six AARFs are defined in AIVSS v0.5. The four most applicable to MCP are:

| AARF | Multiplier | Applied when |
|------|-----------|-------------|
| Tool Use (TU) | x1.15 | Always; every MCP call is an autonomous tool invocation |
| Data Access (DA) | x1.10 | Tool reads sensitive content (PII, credentials, financial, private messages) |
| Persistent Memory (PM) | x1.10 | Tool writes to persistent state (write_file, edit_file, append_insight, write_query) |
| Multi-Step Reasoning (MSR) | x1.10 | Write following a read is possible; chained tool calls compound risk |
| Prompt Injection Surface (PIS) | x1.10 | External or user-controlled content enters the LLM context (read tools, search, list) |

Formula: `AIVSS_score = min(base * TU * [DA?] * [PM?] * [MSR?] * [PIS?], 10.0)`

Tier thresholds: Critical >= 9.0, High >= 7.0, Medium >= 4.0, Low < 4.0.

### Scoring Context

MCP server = protected asset. AI agent = attacker. All scores are static upper-bound estimates
assuming a fully autonomous agent with no human in the loop (Autonomy Level AARF = implicit).
Prompt Injection Surface applies whenever the tool reads external or user-supplied content that
enters the LLM context.

---

## Filesystem MCP

### AARF Profile by Tool

| Tool | TU | DA | PM | MSR | PIS | Rationale |
|------|----|----|----|----|-----|-----------|
| read_file | yes | yes (sensitive dirs) | no | no | yes | Reads file content into LLM; PIS from any embedded content |
| write_file | yes | no | yes | yes | no | Persists data; MSR because agent writes after reasoning |
| edit_file | yes | no | yes | yes | no | Same as write but partial modification |
| create_dir | yes | no | yes | no | no | Structural change only; PM because it alters the filesystem |
| list_dir | yes | no | no | no | yes | Directory names enter LLM context (PIS) |
| move_file | yes | no | yes | yes | no | Destructive relocation; PM+MSR |
| search | yes | yes (sensitive dirs) | no | no | yes | Scans content; matched snippets enter context |
| get_file_info | yes | no | no | no | no | Metadata only; minimal amplification |

DA is only applied when the directory is in the sensitive set (Sensitive Docs, Security Evidence, Eval Data).

### Base Score by Folder

| Folder | Base Score | Rationale |
|--------|-----------|-----------|
| Sensitive Docs | 9.0 | PII, financials, contracts |
| Security Evidence | 9.0 | Audit logs, forensic data |
| Source Code | 6.5 | Proprietary IP, may contain secrets |
| Eval Data | 6.0 | Research/ML data with business value |
| QA Test Plans | 5.5 | Internal process visibility |
| Shared Proj Dir | 5.0 | Mixed sensitivity |
| Onboarding | 4.0 | Semi-public but contains org structure |
| Public | 2.5 | Intentionally public content |

### Filetype Modifiers

| Filetype | Multiplier | Rationale |
|----------|-----------|-----------|
| .sys | 1.25 | Kernel-level; write = OS compromise |
| .exe | 1.20 | Binary execution; write = malware injection |
| .bash | 1.15 | Shell script; direct code execution risk |
| .code | 1.10 | Source code with potential embedded secrets |
| .sql | 1.10 | Schema and data combined |
| .xlsx | 1.05 | Macro-enabled variants add execution surface |
| .docx | 1.05 | Macro/embedded-link risk |
| .pdf | 1.00 | Baseline; embedded content PIS |
| .csv | 1.00 | Baseline; tabular data |
| .md | 0.90 | Minimal execution model |
| .png | 0.85 | Parser exploits rare |
| .txt | 0.85 | No execution model |

### Key Observations

1. Sensitive Docs and Security Evidence reach Critical on read_file because TU+DA+PIS stack
   on a base of 9.0. Plain CVSS would score these High (7.0-8.0); AIVSS pushes to Critical (9.0+).

2. Source Code / .bash and Source Code / .exe are Critical on write_file because the base (6.5)
   times filetype modifier (1.15/1.20) times tool scale (1.05) times TU+PM+MSR exceeds 9.0.
   Under plain CVSS these would likely be High.

3. create_dir and get_file_info stay Low-Medium across most directories. create_dir gets PM
   amplification but the base tool scale is 0.45, limiting the ceiling.

4. Public directory files rarely exceed Low even with AIVSS because the base score (2.5) is
   insufficient to cross tier thresholds after amplification, except for .exe files where the
   filetype modifier and execution risk push write_file to Low -> Medium -> High.

---

## SQLite MCP

### AARF Profile by Tool

| Tool | TU | DA | PM | MSR | PIS | Rationale |
|------|----|----|----|----|-----|-----------|
| list_tables | yes | no | no | no | yes | Table names enter LLM context (schema enumeration) |
| describe_table | yes | no | no | no | yes | Column names and types enter context |
| read_query | yes | yes (sensitive cats) | no | yes | yes | Reads actual data; enables read-then-write chain |
| write_query | yes | no | yes | yes | no | Modifies persistent database state |
| create_table | yes | no | yes | no | no | Structural schema change |
| append_insight | yes | no | yes | yes | no | Writes notes to a persistent insight store |

### Base Score by Data Category

| Data Category | Base Score | Rationale |
|--------------|-----------|-----------|
| Credentials / API Keys | 9.5 | Direct system access; highest CIA impact |
| PII | 9.0 | Regulatory exposure; confidentiality critical |
| Financial | 8.5 | Privacy + business impact |
| Research Results / Restricted Research Data | 5.5 | IP value; confidentiality impact |
| Internal Data | 5.0 | Non-public but not regulated |
| Research Metadata | 4.0 | Structural information |
| Org / Role Metadata | 4.5 | Organizational reconnaissance value |
| Public Data / Output | 2.0-2.5 | Intentionally public |
| Lifecycle / Timestamps | 3.0 | Temporal metadata |

### Key Observations

1. read_query on PII, Financial, and Credentials reaches Critical because the high base (8.5-9.5)
   times read_query scale (0.95) times TU+DA+MSR+PIS exceeds 9.0. Under plain CVSS read access to
   PII typically scores High; AIVSS elevates it to Critical due to the autonomous chain risk.

2. list_tables is scored N/A in the combined-risk sheet because it returns table names regardless
   of which specific table is queried. In the Table_DataType and Assets sheets it is scored as
   a cross-cutting metadata operation (Medium overall due to TU+PIS on schema enumeration).

3. append_insight reaches High for sensitive categories (PII, Financial, Credentials) because
   writing agent notes to a persistent store (PM+MSR) creates an exfiltration-via-memory risk.
   Plain CVSS would treat this as a low-impact write; AIVSS specifically captures the
   Persistent Memory amplifier.

4. create_table on the api_keys table scores High (not Critical) because the base tool scale
   for schema operations (0.60) limits the ceiling even with TU+PM amplification. The actual
   data exposure requires read_query or write_query.

---

## Slack MCP

### AARF Profile by Tool

| Tool | TU | DA | PM | MSR | PIS | Rationale |
|------|----|----|----|----|-----|-----------|
| slack_get_channel_history | yes | yes (PII/private) | no | yes | yes | Reads messages; history enters context; enables chain |
| slack_get_thread_replies | yes | yes (PII/private) | no | yes | yes | Same as above for thread scope |
| slack_get_user_profile | yes | yes (PII) | no | no | yes | Directly reads PII (email, phone, title) |
| slack_post_message | yes | no | yes | yes | no | Writes to channel; PM+MSR (follows read) |
| slack_reply_to_thread | yes | no | yes | yes | no | Same as post but scoped to thread |
| slack_get_users | yes | yes (PII) | no | no | yes | Bulk PII enumeration |
| slack_list_channels | yes | no | no | no | yes | Channel names enter context (org recon) |
| slack_add_reaction | yes | no | yes | yes | no | Covert signaling channel; PM+MSR amplifiers |

### Channel Multipliers

| Channel | Multiplier | Rationale |
|---------|-----------|-----------|
| Management | 1.20 | Executive communications; highest business impact |
| HR | 1.20 | Personnel data; regulatory exposure |
| Supervisor | 1.05 | Operational visibility; moderate elevation |
| Researcher | 1.00 | Baseline |
| Technical | 1.00 | Baseline |
| Public | 0.70 | Intentionally visible workspace |

### Key Observations

1. slack_add_reaction scores Critical for Management/HR PII because this tool can act as a
   covert exfiltration confirmation signal (agent reads data, then reacts to signal receipt).
   Plain CVSS would score an emoji reaction as negligible; AIVSS captures this through the
   MSR and PM amplifiers.

2. slack_get_channel_history and slack_get_thread_replies on private messages in Management
   and HR reach Critical (TU+DA+MSR+PIS stacking). In plain CVSS these would be High (7.0-8.0)
   because the confidentiality impact is High but there is no integrity or availability impact.
   AIVSS adds MSR because the agent can chain this read into a subsequent post.

3. slack_list_channels is scored N/A for PII, Private, and Public Message assets because
   the tool returns channel metadata only, not message content or user profiles. It scores
   Low-Medium for Team Metadata assets via TU+PIS.

4. Public channel reads (get_channel_history on Public messages) score Low in Public workspace
   and Low-Medium in other workspaces, reflecting that the content is already visible to
   workspace members. AIVSS amplification does not elevate Low base scores past Medium
   without sensitive content.

---

## AIVSS vs Plain CVSS: Tier Inflation Summary

| Scenario | CVSS tier (estimate) | AIVSS tier | AARFs responsible |
|----------|---------------------|------------|-------------------|
| read_file on Sensitive Docs | High | Critical | TU + DA + PIS |
| write_file on Source Code/.bash | High | Critical | TU + PM + MSR |
| read_query on PII table | High | Critical | TU + DA + MSR + PIS |
| append_insight on Financial data | Medium | High | TU + PM + MSR |
| slack_add_reaction in Management | Low | High-Critical | TU + PM + MSR |
| list_tables (schema enumeration) | Low | Medium | TU + PIS |
| get_file_info on Public file | Low | Low | TU only; base too low |

AIVSS consistently inflates by one tier when two or more non-TU amplifiers apply. It inflates by
two tiers when three or more amplifiers stack on a medium-sensitivity base (e.g., a tool that reads
then enables a write on restricted data). The Tool Use amplifier alone (x1.15) is insufficient to
cross a tier boundary from a low base score, which preserves meaningful differentiation at the
Low end of the scale.
