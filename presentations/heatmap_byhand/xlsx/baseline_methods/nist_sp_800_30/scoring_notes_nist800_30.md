# NIST SP 800-30 Rev. 1 Scoring Notes

MCP server risk matrices scored against the NIST SP 800-30 Rev. 1 qualitative risk
assessment framework. Three servers scored: Filesystem MCP, Slack MCP, SQLite MCP.

## Formula and Scale

**Risk = Threat Likelihood x Adverse Impact**

Both dimensions use the NIST qualitative five-level scale internally (Very Low / Low /
Moderate / High / Very High), collapsed to four output bands for the spreadsheets:

| Qualitative (NIST)    | Output band |
|-----------------------|-------------|
| Very High             | Critical    |
| High                  | High        |
| Moderate              | Medium      |
| Low / Very Low        | Low         |

**Cell score rule**: `max(Likelihood-band, Impact-band)` following NIST SP 800-30
Table I-2 worst-case convention. The more conservative of the two dimensions governs,
so a High-likelihood tool against a Medium-impact asset still resolves to High.

**Threat model**: MCP server is the protected asset; AI agent is the threat source.
All scores are taken from the server's perspective using static upper-bound (worst-case
agent intent) assumptions.


## Threat Likelihood Rationale

Likelihood answers: how probable is it that a malicious or compromised AI agent
successfully invokes this tool against this server?

Baseline is elevated for all MCP tools because: (a) MCP exposes tools as callable
functions with no authentication friction by default, (b) agents can compose tools
programmatically at speed, and (c) MCP protocol does not enforce semantic intent checks.

### Filesystem MCP

| Tool           | Likelihood | Justification                                                         |
|----------------|------------|-----------------------------------------------------------------------|
| read_file      | High       | Direct exfiltration primitive; trivial to invoke; no side effects to hide. |
| write_file     | High       | Immediate integrity damage; call syntax is simple.                    |
| edit_file      | High       | Silent partial corruption; harder to detect than full overwrite.      |
| list_dir       | High       | Pure reconnaissance; zero friction; legitimate use provides cover.    |
| search         | High       | Targeted reconnaissance; low effort; blends with normal agent tasks.  |
| get_file_info  | High       | Metadata leak (size, timestamps); trivial; often overlooked.         |
| move_file      | Medium     | Requires knowing source and destination paths; less trivially abused. |
| create_dir     | Medium     | Structural side-effect only; limited immediate data exposure.         |

### Slack MCP

| Tool                    | Likelihood | Justification                                                        |
|-------------------------|------------|----------------------------------------------------------------------|
| slack_get_channel_history | High     | Mass message pull; single call; very high data-to-effort ratio.     |
| slack_get_thread_replies  | High     | Targeted deep-dive into specific conversations; trivial.            |
| slack_get_user_profile    | High     | Bulk PII retrieval; one call per user; easily automated.            |
| slack_post_message        | High     | Social engineering / phishing primitive; hard to distinguish from legitimate agent actions. |
| slack_reply_to_thread     | High     | Same as post_message; adds context-aware impersonation capability.  |
| slack_get_users           | High     | Full workspace user enumeration in one call; bulk PII.              |
| slack_list_channels       | High     | Channel enumeration; reconnaissance with no visible side-effect.    |
| slack_add_reaction        | Low      | Emoji reaction only; minimal information exposure or integrity risk. |

### SQLite MCP

| Tool           | Likelihood | Justification                                                         |
|----------------|------------|-----------------------------------------------------------------------|
| list_tables    | High       | Reveals full schema surface; first step in any SQL attack chain.      |
| describe_table | High       | Exposes column names and types; enables targeted queries.             |
| read_query     | High       | Arbitrary SELECT; full data extraction in one call.                   |
| write_query    | High       | INSERT / UPDATE / DELETE; immediate, durable integrity damage.        |
| create_table   | Medium     | Requires schema knowledge; primarily a persistence/staging concern.   |
| append_insight | Low        | Appends pre-typed strings to an insight log; narrow blast radius.     |


## Adverse Impact Rationale

Impact uses FIPS 199 CIA triad, taking the high-water mark across Confidentiality (C),
Integrity (I), and Availability (A). Static upper-bound: we assume the worst-case
data in each directory / table / channel category.

### Filesystem MCP

Impact is the max of (directory sensitivity, filetype sensitivity).

**Directory tiers**:

| Directory       | Band     | Reason                                                        |
|-----------------|----------|---------------------------------------------------------------|
| Sensitive Docs  | Critical | Financial records, PII, legal contracts -- direct breach.     |
| Security Evidence | Critical | Audit logs, forensic artifacts -- tampering undermines oversight. |
| Source Code     | High     | IP leakage; write access enables supply-chain attack.         |
| QA Test Plans   | High     | Exposes test coverage gaps; attack surface intelligence.      |
| Shared Proj Dir | High     | Broad exposure across teams; lateral movement vector.         |
| Eval Data       | Medium   | Internal research data; valuable but not immediately breach-grade. |
| Onboarding      | Medium   | Org charts and policies; useful for social engineering.       |
| Public          | Low      | Intended for external consumption; no confidentiality expectation. |

**Filetype tiers** (standalone worst-case):

| Filetype | Band     | Reason                                                              |
|----------|----------|---------------------------------------------------------------------|
| .sys     | Critical | Kernel/driver code; write enables OS-level compromise.              |
| .exe     | Critical | Executables; write enables arbitrary code injection.                |
| .bash    | Critical | Shell scripts; write enables arbitrary execution at next run.       |
| .code    | Critical | Source files; write plants backdoors silently.                      |
| .sql     | Critical | Database dumps; read discloses all structured data.                 |
| .xlsx    | High     | Spreadsheets routinely hold financials or PII.                      |
| .docx    | High     | Office documents carry contracts, strategy, PII.                    |
| .pdf     | High     | Reports and contracts; high confidentiality value.                  |
| .csv     | High     | Tabular data; frequent PII or financial records.                    |
| .md      | Medium   | Documentation; may expose architecture or credential hints.         |
| .txt     | Medium   | Variable; may hold logs, config, or credentials.                    |
| .png     | Low      | Images; low standalone risk.                                        |

**Notable cells**: Sensitive Docs + any filetype = Critical across all tools because
the directory band (Critical) dominates regardless of filetype. Public + .png = Low
impact, but list_dir and read_file carry High likelihood, so their cell score resolves
to High -- demonstrating the max-convention effect.

### Slack MCP

Impact varies by channel category and asset type.

**Asset impacts**:

| Asset                              | Band     | Reason                                            |
|------------------------------------|----------|---------------------------------------------------|
| User PII (emails, phones, titles)  | Critical | Direct GDPR-grade PII breach.                     |
| Private Channel Messages           | Critical | Confidential business communications.             |
| Public Channel Messages            | Medium   | Semi-public; integrity risk if agent posts bogus content. |
| Team / Workspace Metadata          | Medium   | Org structure; useful for spear-phishing setup.   |

**Category sensitivity** (used to compute worst-case per row in T3):

| Category   | Band     | Reason                                                        |
|------------|----------|---------------------------------------------------------------|
| Management | Critical | Executive strategy, decisions, and confidential discussions.  |
| HR         | Critical | Employee PII, salary data, performance reviews.               |
| Supervisor | High     | Operational decisions, team-level PII.                        |
| Researcher | High     | Research data, IP, unpublished results.                       |
| Technical  | High     | Credential hints, architecture details, deployment info.      |
| Public     | Low      | Intended for external audiences.                              |

**Notable cells**: slack_add_reaction against any asset = Low because both likelihood
(Low) and impact (Low/Medium) are non-threatening; the max resolves to Low or Medium.
slack_get_users against Management PII = Critical (High likelihood x Critical impact).
Public channel messages in the Public category = High rather than Medium because
likelihood (High) overrides the Medium impact via the max-convention.

### SQLite MCP

Impact is assigned per data category within each table.

**Data category impacts**:

| Category                  | Band     | Reason                                               |
|---------------------------|----------|------------------------------------------------------|
| PII                       | Critical | Direct personal data breach.                         |
| Financial                 | Critical | Revenue, salary, or grant data.                      |
| Credentials / API Keys    | Critical | Full account takeover if disclosed.                  |
| Restricted Research Data  | High     | Unpublished results; IP loss.                        |
| Research Metadata         | High     | Project timelines and scope; competitive intelligence. |
| Org / Role Metadata       | High     | Enables targeted social engineering.                 |
| Public Research Data      | Medium   | Intended for dissemination; lower confidentiality.   |
| Public Output             | Medium   | Published work; no confidentiality expectation.      |
| Lifecycle / Timestamps    | Low      | Structural metadata; minimal standalone sensitivity. |
| Timeline                  | Medium   | Project schedules; moderate sensitivity.             |

**Notable cells**: api_keys table + read_query = Critical (High x Critical). Even
list_tables against api_keys = Critical because the mere existence of the table leaks
that API keys are stored in the database. append_insight against PII = High because
Low likelihood is overridden by Critical impact via the max-convention.


## Summary of Ranking Decisions

### Filesystem MCP -- tool ranking

write_file, edit_file, read_file all score Critical (against worst-case assets).
move_file scores Critical despite Medium likelihood because impact (Critical for
sensitive assets) dominates. list_dir and search score High because they are
reconnaissance tools whose worst-case impact is High (exposing structure, not
content directly). get_file_info scores High for similar reasons.

### Slack MCP -- tool ranking

get_channel_history, get_thread_replies, get_user_profile, and get_users score
Critical (bulk data exfiltration, High likelihood x Critical impact). post_message
and reply_to_thread score High (integrity/deception risk). list_channels scores High
(High likelihood x Medium recon impact, max = High). add_reaction scores Low.

### SQLite MCP -- table ranking

employees, grants, and api_keys score Critical (contain PII, Financial, or Credential
data). projects, datasets, and experiments score High (research-grade internal data).
publications scores Medium (public output only).

### SQLite MCP -- data type ranking

PII, Financial, and Credentials / API Keys score Critical. Restricted Research Data,
Research Metadata, and Org / Role Metadata score High. Public data categories score
Medium. Lifecycle / Timestamps score Low.
