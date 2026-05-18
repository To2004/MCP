# Scoring Notes: MAESTRO / ATFAA Applied to MCP Server Risk Matrices

Applied to three MCP server risk matrices (Filesystem, Slack, SQLite).
Method: Narajala et al. arXiv 2504.19956 (MAESTRO) and 2508.10043 (ATFAA).

## Method Summary

Formula: R = P x I x E

| Factor | Scale | Description |
|--------|-------|-------------|
| P (Probability) | 1-3 | How often does an autonomous agent reach and invoke this tool in normal workflows? 1=unlikely, 2=plausible, 3=routine |
| I (Impact) | 1-3 | Magnitude of harm if the action completes. 1=minor, 2=serious, 3=severe |
| E (Exploitability) | 1-3 | How trivially can an attacker or jailbroken agent exploit this combination? 1=hard, 2=moderate, 3=trivial |

R = P x I x E gives 1-27. Band mapping:

- 18-27 -> Critical
- 9-17  -> High
- 4-8   -> Medium
- 1-3   -> Low

Threat model: MCP server is the protected asset; autonomous AI agent is the attacker.
Static upper-bound assumption: agent operates without human approval gates.


## MAESTRO Key Insight vs. NIST SP 800-30

NIST treats exploitability as a function of attacker skill and motivation. MAESTRO
collapses that: MCP tools are designed to be invoked by callers. An agent calling
read_query or read_file faces zero authentication friction, no GUI, and can execute
at machine speed. This means:

- E = 3 (trivial) for essentially all MCP tools in all three matrices.
- P is elevated compared to human attackers because agents enumerate, search, and
  read as routine pipeline steps -- not as targeted intrusions.
- The P x I x E distribution compresses toward the high end relative to NIST.
  Under NIST, "critical" is reserved for the rarest combination; under MAESTRO,
  any tool x sensitive asset combination with P >= 2 and I >= 3 lands at Critical
  (R = 18) trivially.


## Filesystem MCP: P, I, E Breakdown

E = 3 for all filesystem tools (MCP filesystem server exposes all tools callable
with no additional authentication).

Tool P assignments:

| Tool | P | Rationale |
|------|---|-----------|
| read_file | 3 | Agents routinely read files to answer questions |
| write_file | 2 | Agents write outputs but less frequently than reads |
| edit_file | 2 | Agents patch or update files; plausible in agentic pipelines |
| create_dir | 1 | Rare; agents almost never need to create directories autonomously |
| list_dir | 3 | Enumeration is a standard first step for any file navigation task |
| move_file | 1 | Rare file management action; not a common agentic pattern |
| search | 3 | Searching for relevant files is routine context-gathering |
| get_file_info | 2 | Metadata checks are plausible but not ubiquitous |

Directory I baseline assignments:

| Directory | I | Rationale |
|-----------|---|-----------|
| Sensitive Docs | 3 | Contains PII, financial records, legal contracts |
| Security Evidence | 3 | Audit logs and forensic data; tampering undermines accountability |
| Source Code | 3 | IP, supply-chain risk if modified; enables active exploits |
| QA Test Plans | 2 | Reveals test coverage gaps, may enable QA bypass attacks |
| Shared Proj Dir | 2 | Project data; moderate sensitivity |
| Eval Data | 2 | Research/evaluation datasets; IP exposure |
| Onboarding | 2 | Org structure, HR data, policy documents |
| Public | 1 | Already public; harm from read is negligible |

Filetype modifier: executable and scripting formats (.exe, .sys, .bash, .code, .sql)
raise I by 1 (capped at 3) because exfiltration or modification enables active
exploitation beyond mere data disclosure.

### Notable cells

- Sensitive Docs x any filetype x read_file: P=3, I=3, E=3 -> R=27 (Critical)
- Sensitive Docs x any filetype x create_dir: P=1, I=3, E=3 -> R=9 (High).
  NIST would likely call this Medium because create_dir is low-impact on its own;
  MAESTRO keeps it High because the directory creation supports further exfiltration
  pipelines and P is still non-zero for an autonomous agent.
- Public x .txt x write_file: P=2, I=1, E=3 -> R=6 (Medium).
  NIST would score this Low. MAESTRO inflates it: an agent writing to public files
  could poison shared outputs or exfiltrate encoded data via steganography.
- Public x .exe x read_file: P=3, I=2, E=3 -> R=18 (Critical).
  Executable files in a public directory still have I=2 after the filetype modifier
  (Public base I=1, raised to 2 for .exe). MAESTRO calls this Critical because
  reading executables could enable binary analysis for supply-chain attacks.
- move_file / create_dir are the only tools that drop below High across all
  directories, because P is suppressed (1-2). This is the primary discriminator.


## Slack MCP: P, I, E Breakdown

E = 3 for all Slack tools. Slack MCP exposes all channels visible to the bot token;
no per-call authentication.

Tool P assignments:

| Tool | P | Rationale |
|------|---|-----------|
| slack_get_channel_history | 3 | Agents fetch channel context as a first step |
| slack_get_thread_replies | 3 | Following threads is routine in conversation agents |
| slack_get_user_profile | 3 | Resolving user identities is routine for any people-related task |
| slack_post_message | 2 | Autonomous posting is plausible but less frequent than reads |
| slack_reply_to_thread | 2 | Thread replies are plausible; agents comment on findings |
| slack_get_users | 3 | Bulk user listing is a standard enumeration / PII harvest step |
| slack_list_channels | 3 | Channel enumeration is a discovery step, routine in any Slack agent |
| slack_add_reaction | 1 | Low utility for autonomous agents; rarely invoked |

Channel category I:

| Category | I | Rationale |
|----------|---|-----------|
| Management | 3 | Strategic decisions, compensation, org power; severe if disclosed |
| HR | 3 | PII-dense (performance reviews, salaries, hiring); GDPR/CCPA exposure |
| Technical | 2 | System info, architecture; occasional credential leakage in messages |
| Supervisor | 2 | Team operations, moderate sensitivity |
| Researcher | 2 | IP, research methodology, unpublished results |
| Public | 1 | Low sensitivity; already broadly accessible |

Asset I overrides (applied before channel modifier):

- User PII (emails, phones, titles): I=3 regardless of channel.
  Any tool that surfaces PII at scale is severe under GDPR/CCPA threat models.
- Private Channel Messages: I follows channel category.
- Public Channel Messages: I=1.
- Team / Workspace Metadata: I=1 (structural, low harm).

### Notable cells

- Management x User PII x slack_get_user_profile: P=3, I=3, E=3 -> R=27 (Critical).
- Public x Public Channel Messages x slack_post_message: P=2, I=1, E=3 -> R=6 (Medium).
  NIST would score this Low (public data, low impact). MAESTRO raises to Medium:
  an agent autonomously posting to public channels creates reputational and
  misinformation risk that NIST does not model for agentic actors.
- slack_add_reaction across all assets: P=1, max I=3 -> R=9 (High for PII) down to
  R=3 (Low for public/metadata). Only tool that can drop to Low under MAESTRO.
- MAESTRO inflation vs. NIST: slack_get_users against Management/HR PII scores
  Critical under MAESTRO (P=3, I=3, E=3). Under a NIST likelihood model, this
  would be High at best because NIST assumes a human attacker who must discover and
  target the API. An autonomous agent calls slack_get_users as a standard step with
  zero friction.
- All seven non-reaction tools score Critical at maximum (against high-sensitivity
  channels with PII assets). The only sub-Critical maximum is slack_add_reaction
  (max High). This near-total Critical saturation is the MAESTRO signature: agentic
  E=3 collapses the upper tail.


## SQLite MCP: P, I, E Breakdown

E = 3 for all SQLite tools. The MCP SQLite server accepts arbitrary SQL strings; no
query whitelisting or parameterization layer is assumed at the server level.

Tool P assignments:

| Tool | P | Rationale |
|------|---|-----------|
| list_tables | 3 | First step in any DB-facing agentic workflow |
| describe_table | 3 | Schema discovery before querying; routine |
| read_query | 3 | Agents issue SELECT queries constantly for data retrieval |
| write_query | 2 | Mutation is plausible; agent updates records or inserts findings |
| create_table | 1 | DDL is rare in normal agentic operation |
| append_insight | 2 | Agents record conclusions; plausible in research-assistant scenarios |

Data category I:

| Category | I | Rationale |
|----------|---|-----------|
| PII | 3 | Personal identifiers; regulatory exposure (GDPR, CCPA) |
| Financial | 3 | Salary, grants, budgets; severe if disclosed or tampered |
| Credentials / API Keys | 3 | Immediate lateral movement and system compromise if exfiltrated |
| Restricted Research Data | 3 | Unpublished IP; severe competitive and reputational harm |
| Internal Data | 2 | Non-public but not individually identifiable; serious |
| Research Metadata | 2 | Project info, timelines; serious if leaked |
| Research Results | 2 | Experimental outcomes; potentially restricted |
| Org / Role Metadata | 2 | Org structure; serious for social engineering |
| Public Research Data | 1 | Already published; minor harm |
| Public Output | 1 | Published work; already public |
| Lifecycle / Timestamps | 1 | Operational metadata; low sensitivity |

Table I is the maximum I across all data categories the table contains. Used as a
floor when the specific data category I is lower (e.g., projects contains both
Research Metadata (I=2) and Timeline (I=1); table floor is I=2).

### Notable cells

- api_keys x Credentials x read_query: P=3, I=3, E=3 -> R=27 (Critical).
  Most severe cell in the matrix. NIST would also rate this high, but only after a
  skilled attacker discovers the table. An agent discovers it in one list_tables call.
- api_keys x Credentials x create_table: P=1, I=3, E=3 -> R=9 (High).
  NIST would likely score this Medium or Low (create_table does not directly expose
  credentials). MAESTRO keeps it High because P=1 is still non-zero, and a
  jailbroken agent could create a shadow table to redirect API key writes.
- publications x Public Output x create_table: P=1, I=1, E=3 -> R=3 (Low).
  Only Low cell in the entire SQLite matrix. Confirms MAESTRO does not uniformly
  inflate: genuinely low-P, low-I combinations still land at Low.
- publications x Public Output x read_query: P=3, I=1, E=3 -> R=9 (High).
  NIST would score this Low or Medium (public data). MAESTRO scores High: the
  exfiltration of large volumes of public records at machine speed creates bulk
  data aggregation risk that NIST's per-request model misses.
- Ranking_DataTypes: all seven categories score Critical at maximum except
  Public Research Data and Lifecycle/Timestamps, which score Critical due to
  list_tables and describe_table (P=3, I=2, E=3 -> R=18). Every data type reaches
  Critical under MAESTRO because the discovery tools (list_tables, describe_table,
  read_query) all have P=3.


## Cross-Matrix MAESTRO vs. NIST Comparison

| Observation | NIST SP 800-30 | MAESTRO / ATFAA |
|-------------|---------------|-----------------|
| Exploitability default | Varies by attacker skill | Fixed E=3 for MCP tools (callable by design) |
| Likelihood for read-only tools | Often Low-Medium (attacker must find and target) | Often High-Critical (agent reads as standard pipeline step) |
| Discovery tools (list, search, enumerate) | Low impact assumed | P=3; raises many cells to Critical even before exploitation |
| Low-impact public assets | Low | Medium-High (bulk aggregation risk at machine speed) |
| Critical saturation rate | ~10-20% of cells (reserved for worst combinations) | ~50-70% of cells (P+I compression under agentic threat model) |

The MAESTRO inflation is methodologically justified, not arbitrary: the framework
explicitly models that agents do not require human motivation, opportunity windows,
or skill acquisition to reach and invoke tools. Every tool call is zero-friction.
P and I remain the primary discriminators; E is a fixed agentic constant.


## Files Written

- risk_ranking_filesystemMCP_maestro.xlsx
- risk_ranking_slackMCP_maestro.xlsx
- mcp_sqlite_risk_rankings_maestro.xlsx
- scoring_notes_maestro_atfaa.md (this file)

All scoring performed with openpyxl. No new rows or columns added.
Band labels used: Critical, High, Medium, Low only.
