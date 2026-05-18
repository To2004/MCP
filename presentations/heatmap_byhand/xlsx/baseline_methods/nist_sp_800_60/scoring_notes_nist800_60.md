# NIST SP 800-60 Scoring Notes

Scoring notes for the three MCP server risk matrices scored under the NIST SP
800-60 / FIPS 199 information-type categorisation framework.

## 1. How Vol 1 Methodology Was Applied

SP 800-60 Vol 1 defines a four-step process for mapping information types to
FIPS 199 security categories. Each step was adapted to the MCP server context
as follows.

### Step 1 -- Identify information types

Each MCP asset surface (directory x file extension for Filesystem, table x
data-category for SQLite, channel persona x asset type for Slack) was mapped
to the closest SP 800-60 Vol 2 catalogue entry. The mapping uses the asset's
primary semantic content, not its location or name, as the anchor.

Example: `sensitive/financials/budget_2026.xlsx` -> Financial Management
(C.3.3) AND Personal Identifying Information (C.3.5.8) because the file sits
in the Sensitive Docs directory and contains financial PII. The higher-risk
type governs.

### Step 2 -- Assign provisional CIA impact from Vol 2

The Vol 2 provisional security category for each information type provides a
baseline CIA triple:

    SC = {(Confidentiality, impact), (Integrity, impact), (Availability, impact)}

where each impact is Low, Moderate, or High. These are read directly from the
Vol 2 table mappings provided in the task specification. No subjective
adjustment was made at this step; adjustments are handled in Step 3.

### Step 3 -- Adjust for mission context

Two context adjusters were applied.

File-extension modifiers (Filesystem MCP only): Certain file types carry
inherent execution or injection risk independent of directory. They were applied
as raise-only overrides (never lowered):

- `.sys`, `.exe` -- set I=High, A=High (executable integrity / availability
  impact)
- `.bash`, `.code` -- set I=High (script injection risk)
- `.sql` -- set I=High when directory has database context (Sensitive Docs,
  Shared Proj Dir, Source Code)

Persona modifier (Slack MCP only): Management and HR channels have elevated
confidentiality sensitivity because they routinely handle PII and compensation
data. Confidentiality was upgraded one band (Low -> Moderate, Moderate -> High,
High stays High) for any asset accessed under a Management or HR persona.

### Step 4 -- Aggregate via high-water mark and apply tool-action lens

FIPS 199 aggregation uses the high-water mark principle: a system's overall
category is the highest impact level across all objectives. For MCP tools, the
high-water mark is applied selectively by tool action rather than globally,
because a read tool cannot cause an integrity failure on its own. The tool-
action lens (see Section 3) picks the active CIA dimension for each tool before
applying the 4-band output mapping.


## 2. Vol 2 Information-Type Mappings Used

### Filesystem MCP

| Directory | Vol 2 Information Type | C | I | A |
|-----------|------------------------|---|---|---|
| Sensitive Docs | PII (C.3.5.8) / Financial Mgmt (C.3.3) | High | Moderate | Low |
| Security Evidence | Information Security (C.3.5.5) | High | High | Moderate |
| Source Code | Information Management (C.3.4) | High | High | Low |
| QA Test Plans | Information Management (C.3.4) | Moderate | Moderate | Low |
| Shared Proj Dir | Administrative Management (C.2.1) | Moderate | Low | Low |
| Eval Data | Research and Development (C.2.8) | Moderate | Moderate | Low |
| Onboarding | Human Resources (C.3.5) | Low | Low | Low |
| Public | Public Affairs (C.3.2) | Low | Low | Low |

File-extension modifiers applied on top of directory base values (raise only):

| Extension | Modifier |
|-----------|----------|
| .sys, .exe | I -> High; A -> High |
| .bash, .code | I -> High |
| .sql (in Sensitive Docs, Shared Proj Dir, Source Code) | I -> High |

Outcome: `.exe` or `.sys` files in Sensitive Docs, Security Evidence, or
Source Code directories can reach CIA = (High, High, High), making any
write-lens tool Critical. Files in Public or Onboarding directories remain Low
or Medium regardless of extension because C stays Low.

### GitHub MCP

| Asset | Vol 2 Information Type | C | I | A |
|-------|------------------------|---|---|---|
| Private Repository Code | Information Management (C.3.4) | High | High | Low |
| Workflow / CI Files | System Maintenance (C.3.5.6) | High | High | Moderate |
| Action Secrets | Identity Mgmt / Credentials | High | High | High |
| Secret Scanning Alerts | Information Security (C.3.5.5) | High | High | Low |
| Code Scanning Alerts | Information Security | High | Moderate | Low |
| Dependabot Alerts | System Maintenance | Moderate | High | Low |
| Issues and Comments | Administrative Management | Moderate | Low | Low |
| Pull Requests | Administrative Management | Moderate | Moderate | Low |
| GitHub Actions Logs | System Maintenance | Moderate | High | Moderate |
| Public Repository Code | Public Affairs | Low | Low | Low |
| User / Org Metadata | Administrative Management | Low | Low | Low |
| Gists | Information Management | Moderate | Low | Low |
| Releases and Tags | Information Management | Low | High | Moderate |

Note: GitHub MCP is documented here for reference. The blank xlsx files
provided did not include a GitHub MCP matrix, so no scored xlsx was generated
for GitHub. Scores follow the same 4-step method and would use the tool-action
lens defined in Section 3 applied to the assets above.

### Slack MCP

| Asset | Vol 2 Information Type | C | I | A |
|-------|------------------------|---|---|---|
| User PII (emails, phones, titles) | PII (C.3.5.8) | High | Moderate | Low |
| Private Channel Messages | Administrative Management / Internal Comms | High | Low | Low |
| Public Channel Messages | Public Affairs (C.3.2) | Low | Low | Low |
| Team / Workspace Metadata | Administrative Management | Low | Low | Low |

Persona modifier: Management and HR channels upgrade C by one level.
Effective CIA after modifier:

| Persona | Asset | C | I | A |
|---------|-------|---|---|---|
| Management, HR | User PII | High (unchanged) | Moderate | Low |
| Management, HR | Private Channel Messages | High (upgraded from High) | Low | Low |
| Management, HR | Public Channel Messages | Moderate (upgraded from Low) | Low | Low |
| Management, HR | Team Metadata | Moderate (upgraded from Low) | Low | Low |
| Other personas | User PII | High | Moderate | Low |
| Other personas | Private Channel Messages | High | Low | Low |
| Other personas | Public Channel Messages | Low | Low | Low |
| Other personas | Team / Workspace Metadata | Low | Low | Low |

### SQLite MCP

| Table | Data Category | Vol 2 Type | C | I | A |
|-------|---------------|-----------|---|---|---|
| employees | PII | PII (C.3.5.8) | High | Moderate | Low |
| employees | Financial | Financial Management (C.3.3) | High | High | Low |
| employees | Role / Org | Human Resources (C.3.5) | Moderate | Low | Low |
| projects | Research Metadata | Research and Development (C.2.8) | Moderate | Moderate | Low |
| projects | Timeline | Administrative Management | Low | Moderate | Low |
| datasets | Public Data | Public Affairs | Low | Low | Low |
| datasets | Internal Data | Research and Development | Moderate | Moderate | Low |
| experiments | Research Results | Research and Development | Moderate | Moderate | Low |
| publications | Public Output | Public Affairs | Low | Low | Low |
| grants | Financial | Financial Management (C.3.3) | High | High | Low |
| api_keys | Credentials | Information Security (credentials) | High | High | High |


## 3. Tool-Action Lens -- Selecting the Active CIA Dimension

Each MCP tool primarily stresses one CIA dimension. The lens selects that
dimension's impact level as the "active" value for the 4-band mapping rule.

| Lens | Tools | Rationale |
|------|-------|-----------|
| C (Confidentiality) | read_file, list_dir, get_file_info, list_tables, describe_table, read_query, slack_get_*, slack_list_channels | Data exposure risk; no write side-effect |
| I (Integrity) | write_file, edit_file, write_query, slack_post_message, slack_reply_to_thread, slack_add_reaction | Writes or modifies persistent state |
| A (Availability) | move_file, create_dir, create_table | Structural changes; disrupts access or schema |
| CI hybrid (max C, I) | search, append_insight | Both exposes and modifies; take whichever is higher |

4-band mapping rule applied after the active dimension is selected:

    Active dimension = High AND at least one other dimension = High -> Critical
    Active dimension = High, others below High                    -> High
    Active dimension = Moderate                                   -> Medium
    Active dimension = Low                                        -> Low

The "at least one other High" test captures the FIPS 199 high-water mark
principle: if two or more objectives are simultaneously High, the system-level
risk is elevated above a single-dimension High.

Selected score examples:

    Sensitive Docs / .sql / read_file:
        base CIA = (High, Moderate, Low); .sql modifier -> (High, High, Low)
        C-lens: active=High, others=[High, Low] -> one other High -> Critical

    Security Evidence / .png / write_file:
        base CIA = (High, High, Moderate)
        I-lens: active=High, others=[High, Moderate] -> one other High -> Critical

    Security Evidence / .png / move_file:
        A-lens: active=Moderate, others=[High, High] -> Medium

    Sensitive Docs / .png / write_file:
        base CIA = (High, Moderate, Low)
        I-lens: active=Moderate -> Medium

    employees / PII / read_query:
        CIA = (High, Moderate, Low)
        C-lens: active=High, others=[Moderate, Low] -> no other High -> High

    api_keys / Credentials / create_table:
        CIA = (High, High, High)
        A-lens: active=High, others=[High, High] -> Critical

    Public Channel Messages / slack_post_message (no persona upgrade):
        CIA = (Low, Low, Low)
        I-lens: active=Low -> Low


## 4. Key Cells Where 800-60 Diverges from 800-30

SP 800-30 combines threat likelihood with impact to produce risk. SP 800-60
produces only an impact category -- likelihood is not modelled. Divergence
appears most clearly in the following situations.

### High-frequency low-severity tools

Under 800-30, `list_dir` and `get_file_info` on a Public directory would score
Low partly because there is no realistic threat event that yields significant
harm. Under 800-60 they also score Low because C=Low, I=Low, A=Low for the
Public information type. Agreement here is coincidental: the method is the
same but the route is different.

### Low-frequency high-severity exposures

`move_file` on Security Evidence / .exe (CIA after modifier = High, High, High)
scores Critical under 800-60 because A=High + others=High. Under 800-30, a
defender would likely reduce the score by applying a Low-likelihood factor
(most agents do not move executables). 800-60 makes no such adjustment.

### create_dir / create_table scored by availability alone

The availability dimension for most information types is Low or Moderate. Under
800-60, `create_dir` on a Sensitive Docs directory returns Low (A=Low from
base CIA, not modified by file extension at directory level) while `read_file`
on the same directory returns High. Under 800-30, `create_dir` on a sensitive
directory would likely receive a Moderate or High risk score due to the
privilege-escalation threat event (creating directories enables subsequent
writes). The information-type method has no mechanism to capture this.

### Hybrid tool `append_insight`

800-30 would assess this as a single compound tool call with a likelihood-
adjusted risk. 800-60 requires choosing a CIA dimension. The CI-hybrid lens
takes max(C, I), which produces the same result as if the higher-risk dimension
were the only active one. This loses the compounding effect that 800-30 would
capture when both C and I are simultaneously stressed.

### Scoring flat across identical directory contents

Under 800-60, every file in the Security Evidence directory scores the same
base CIA tuple regardless of the file's actual content. A benign screenshot and
a cryptographic key log in the same folder receive the same score. 800-30 would
permit the analyst to assign different threat-event likelihoods to each file.

### Sensitive Docs .sql vs .xlsx

Both sit in the same directory (base C=High, I=Moderate). The .sql extension
modifier raises I to High, producing Critical on read (C=High, I=High -> two
Highs -> Critical). The .xlsx file stays at I=Moderate (no modifier applies),
so read scores High. Under 800-30, the difference would be expressed via a
higher likelihood of data-exfiltration events for .sql files (direct database
access) rather than via the impact tuple.


## 5. Limitations: Adapting an Federal-System Framework to MCP Agents

NIST SP 800-60 was designed for categorising U.S. federal information systems
prior to implementing FISMA-mandated controls. Several structural assumptions
do not translate cleanly to the MCP server threat model.

### Assumption: the information type is known and bounded

Vol 2 assumes a human analyst inspects the system and identifies all
information types in advance. In an MCP server, the set of information types a
tool can reach at runtime depends on which paths or tables the calling agent
supplies. A `read_file` call to `source_code/core.c` and one to
`public/whitepaper.pdf` use the same tool but access different information
types. The static scoring approach adopted here assigns the score based on the
asset at design time; it cannot account for novel paths an agent discovers at
runtime.

### Assumption: system scope is an organisational information system

SP 800-60 categories (e.g., C.3.5.5 Information Security) were designed around
mission-area information systems -- payroll systems, case management systems --
not fine-grained tool APIs. Mapping a single MCP tool to a single Vol 2
category produces a category mismatch when the tool's surface spans multiple
mission areas. The `read_query` tool on a SQLite database containing employees,
grants, and api_keys simultaneously touches PII, Financial Management, and
Information Security categories. The approach taken here resolves this by
scoring each table x data-category row independently and recording the
per-combination score, which the ranking sheets then aggregate by high-water
mark.

### Assumption: impact values are stable

Vol 2 provisional values were established for standard federal business
functions. They do not reflect the amplification that AI agents introduce:
- An agent can issue tool calls at machine speed, multiplying exposure.
- An agent's context window can cache and re-use confidential output, creating
  a secondary exfiltration channel that FIPS 199 does not model.
- Prompt injection can redirect an agent's tool calls to unintended targets
  within the same information-type class.

None of these factors affect the FIPS 199 impact tuple, so 800-60 will
systematically under-rate dynamic risk.

### Assumption: the defender controls the information system

FISMA and SP 800-60 assume the organisation owns and operates the system it is
categorising. In the MCP model, the MCP server is the protected asset but the
agent is an external (potentially third-party) caller. The framework treats the
caller as an insider threat actor, which SP 800-60 does not model at all.

### Adaptation made: tool-action CIA lens

The primary adaptation introduced in this scoring is the tool-action lens
(Section 3). SP 800-60 does not define it; it was derived from the FIPS 199
security objective definitions and the MCP tool taxonomy. Without this lens,
all tools on a given asset would receive the same score (the information-type
high-water mark), which would eliminate any differentiation between read-only
and write/delete tools -- the most practically important distinction for a
server-side access-control policy.

### Adaptation made: file-extension modifiers

SP 800-60 operates at the information-type level, not the file-format level.
Executable and script extensions (.exe, .sys, .bash, .code) were treated as
modifiers that raise the provisional CIA values because their inherent
execution capability changes the impact of an integrity compromise. This
adaptation is necessary for a filesystem MCP server but has no Vol 2 precedent.

### Recommendation

NIST SP 800-60 is useful as a structural anchor for the static scoring layer:
it provides a defensible, standards-traceable method for assigning baseline CIA
impact tuples to each asset class. However, it should be supplemented with
SP 800-30 threat-likelihood factors (dynamic scoring layer) and MCP-specific
amplifiers (call frequency, context reuse, injection risk) to produce a full
risk score. Treating the 800-60 output as the final score over-rates
availability-lens tools and under-rates compound or high-frequency threat
scenarios.
