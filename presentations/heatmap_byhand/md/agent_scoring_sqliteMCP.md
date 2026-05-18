# Independent Scoring -- SQLite MCP

## Approach

This file is an independent, agent-side score over the same `(Table x
Data_Category x Tool)` cube the user has hand-scored for the CBG SQLite
MCP server. Scoring is static: it captures the inherent risk of an agent
invoking a tool against a table / data category, before any runtime
context (query content, caller identity, frequency) is applied. I did not
read the user's score columns; rankings come only from the taxonomy
labels in the prompt plus the literature baselines, which apply equally
to a SQL surface because both are flavours of asset-class x action
scoring.

The rubric is grounded in NIST SP 800-30 Rev. 1 (risk = likelihood x
impact), FIPS 199 / NIST SP 800-60 Vol. 1+2 (CIA-tuple with high-water-
mark aggregation), and NIST SP 800-122 (PII confidentiality impact).
Tool-axis intuition is calibrated against MCP-in-SoS (arXiv 2603.10194),
mcp-sec-audit (arXiv 2603.21641), OWASP AIVSS v0.5, MAESTRO/ATFAA
(arXiv 2504.19956), and the Repello AI Blast Radius model. The SQL-
specific intuition: blast radius is governed by *category of data* more
than *table name*, because a bulk `SELECT *` exfiltrates every PII /
credential column the table holds, and a single `write_query` against
`api_keys` pivots across every downstream system. Per-cell score is the
high-water mark of (data-category sensitivity) x (tool blast radius).

## Scoring rubric

| Band | Code | Meaning |
|---|---|---|
| Critical | 4 | Irreversible exfiltration of crown-jewel data (bulk PII, secrets, financials); destructive writes to credential / financial tables; SQL-injection blast radius reaching the whole DB |
| High | 3 | Significant read/write on restricted data; bulk research-data exposure; schema mutation that breaks integrity |
| Medium | 2 | Moderate reads/writes on internal data; reversible mutations on non-sensitive tables |
| Low | 1 | Schema metadata; public-data queries; introspection |
| N/A | 0 | Tool genuinely does not apply (e.g. `list_tables` against a single-table scope, `write_query` on a logically read-only view) |

---

## 1. Tool Ranking (avg danger per tool)

### Empty structure (user's scoring goes here)

| Rank | Tool | Risk | Reasoning |
|---|---|---|---|
| 1 | (blank) | (blank) | (blank) |
| 2 | (blank) | (blank) | (blank) |
| 3 | (blank) | (blank) | (blank) |
| 4 | (blank) | (blank) | (blank) |
| 5 | (blank) | (blank) | (blank) |
| 6 | (blank) | (blank) | (blank) |

### Agent's independent scoring

| Rank | Tool | Risk | Reasoning |
|---|---|---|---|
| 1 | write_query | Critical | Arbitrary INSERT / UPDATE / DELETE -- the canonical SQL persistence and destructive primitive; on `api_keys` it is credential injection, on `grants` / `employees` it is financial / PII tampering, and the verb itself supports multi-row mutations. |
| 2 | read_query | Critical | Arbitrary SELECT -- the canonical exfiltration primitive; a single bulk select on `employees` / `api_keys` / `grants` lifts crown-jewel rows in one call (NIST SP 800-122 PII confidentiality-high). |
| 3 | create_table | High | DDL: not destructive on its own but enables persistence (staging tables for exfil), shadow-schema attacks that mislead downstream queries, and namespace abuse; sets up later `write_query` blast radius. |
| 4 | append_insight | Medium | Write-only audit-like channel; benign by intent but doubles as a covert exfil vector (the agent can log raw PII/secrets into the insights log) and as a poisoning channel for downstream analytics that read the log back. |
| 5 | describe_table | Low | Schema introspection (columns, types, indexes); reconnaissance only -- but reveals exactly which columns hold PII / credentials / financials, scoping the later SELECT / INSERT precisely. |
| 6 | list_tables | Low | Enumerates table names; minimal direct impact, pure discovery; mostly a stepping-stone toward `describe_table` -> `read_query` chains. |

---

## 2. Data-Category Ranking (7 categories)

### Empty structure (user's scoring goes here)

| Rank | Data Category | Risk | Reasoning |
|---|---|---|---|
| 1 | (blank) | (blank) | (blank) |
| 2 | (blank) | (blank) | (blank) |
| 3 | (blank) | (blank) | (blank) |
| 4 | (blank) | (blank) | (blank) |
| 5 | (blank) | (blank) | (blank) |
| 6 | (blank) | (blank) | (blank) |
| 7 | (blank) | (blank) | (blank) |

### Agent's independent scoring

| Rank | Data Category | Risk | Reasoning |
|---|---|---|---|
| 1 | Credentials / API Keys | Critical | Secrets that pivot the agent across every downstream system; bulk read = total compromise, any write = credential injection (FIPS 199 confidentiality-high + integrity-high). |
| 2 | PII | Critical | Personally identifiable information; bulk SELECT triggers NIST SP 800-122 high-impact confidentiality breach and regulated-data exposure. |
| 3 | Financial | Critical | Salaries, grant amounts, financial timelines; FIPS 199 confidentiality-high / integrity-high; tampering is auditable but exfil is irreversible. |
| 4 | Restricted Research Data | High | Embargoed / IP-bearing research data; significant confidentiality impact (SP-800-60 Information Management) but typically less regulated than PII. |
| 5 | Org / Role Metadata | Medium | Org chart, manager/title links; internal-only but largely inferable from public sources; useful for social-engineering recon when combined with PII. |
| 6 | Lifecycle / Timestamps | Low | Creation / expiry / hire dates; minor on its own but correlatable with other categories (e.g. `is_active` on `api_keys` enables targeted abuse). |
| 7 | Public Research Data | Low | Already published / classified `public`; minimal confidentiality risk by definition; only integrity matters and even that is recoverable from upstream copies. |

---

## 3. Table Ranking (7 individual tables)

### Empty structure (user's scoring goes here)

| Rank | Table | Risk | Reasoning |
|---|---|---|---|
| 1 | (blank) | (blank) | (blank) |
| 2 | (blank) | (blank) | (blank) |
| 3 | (blank) | (blank) | (blank) |
| 4 | (blank) | (blank) | (blank) |
| 5 | (blank) | (blank) | (blank) |
| 6 | (blank) | (blank) | (blank) |
| 7 | (blank) | (blank) | (blank) |

### Agent's independent scoring

| Rank | Table | Risk | Reasoning |
|---|---|---|---|
| 1 | api_keys | Critical | Credentials table -- secrets are crown-jewel; any read leaks pivots, any write injects attacker-controlled credentials (FIPS 199 confidentiality-high + integrity-high). |
| 2 | employees | Critical | PII + financial (salaries) + org/role; bulk SELECT here is the worst single-call exfil in the schema after `api_keys` (NIST SP 800-122). |
| 3 | grants | High | Grant financial data; FIPS 199 confidentiality-high but no PII; tampering distorts financial reporting. |
| 4 | datasets | High | Mixed public / internal / restricted rows; risk depends on classification predicate -- a `WHERE classification = 'restricted'` SELECT is High whereas `'public'` is Low. |
| 5 | experiments | Medium | Research results linked to projects / datasets; internal-only but loss undermines research IP. |
| 6 | projects | Medium | Research metadata and timelines; mostly org-internal, recoverable, low regulatory weight. |
| 7 | publications | Low | Public outputs (titles, authors, DOIs); already-published material, confidentiality is N/A by definition. |

---

## 4. Cube cells -- full (Table x Data Category x Tool)

For each of the 11 valid (Table, Data Category) pairs, all 6 tools are
scored. Empty structure mirrors the user's blank matrix; agent scoring
follows. One sub-table per pair keeps the cube auditable.

### 4.1 employees x PII

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Low | Surfaces the table name; trivial recon. |
| describe_table | Low | Reveals which columns hold names / emails / phones -- scoping for later bulk SELECT. |
| read_query | Critical | Bulk SELECT lifts the entire PII set; NIST SP 800-122 high-impact confidentiality breach. |
| write_query | Critical | Tampering with PII corrupts identity-linked records and is regulator-reportable. |
| create_table | Medium | Cannot directly leak PII but enables staging-for-exfil (e.g. `CREATE TABLE staging AS SELECT * FROM employees`). |
| append_insight | High | Free-form log accepts arbitrary text -- an agent can launder raw PII rows into the insights channel, bypassing query-level DLP. |

### 4.2 employees x Financial

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Low | Table-name discovery only. |
| describe_table | Low | Reveals `salary` column; scopes the financial blast radius for later reads. |
| read_query | Critical | Salary exfil is FIPS 199 confidentiality-high; bulk dump is irreversible. |
| write_query | Critical | Salary tampering is direct financial fraud and integrity-high. |
| create_table | Medium | Staging-for-exfil enabler; no direct financial impact alone. |
| append_insight | High | Log channel can carry raw salary data outside the query audit path. |

### 4.3 employees x Role / Org

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Low | Pure discovery. |
| describe_table | Low | Reveals `job_title`, `manager_id` columns; recon. |
| read_query | Medium | Org chart leak; useful for spear-phishing recon but not regulated. |
| write_query | High | Role / manager tampering enables privilege-related attacks downstream. |
| create_table | Low | No direct impact on org metadata. |
| append_insight | Low | Org data leakage via log is low-impact relative to PII / financial. |

### 4.4 projects x Research Metadata

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Low | Discovery only. |
| describe_table | Low | Reveals schema; no direct exposure. |
| read_query | Medium | Internal project descriptions; IP-leak risk if exposed externally. |
| write_query | Medium | Tampering distorts project state but is reversible from backup. |
| create_table | Low | Mostly inert. |
| append_insight | Low | Insight log noise. |

### 4.5 projects x Timeline

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Low | Discovery. |
| describe_table | Low | Reveals date columns. |
| read_query | Low | Timelines are low-sensitivity context. |
| write_query | Medium | Date tampering breaks scheduling / SLAs; reversible. |
| create_table | Low | Inert. |
| append_insight | Low | Low-impact. |

### 4.6 datasets x Public Data

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Low | Discovery. |
| describe_table | Low | Public-by-design. |
| read_query | Low | Public data; FIPS 199 confidentiality-low. |
| write_query | Medium | Integrity matters even when confidentiality does not; public-data tampering misleads downstream consumers. |
| create_table | Low | Inert. |
| append_insight | Low | Public-context logging. |

### 4.7 datasets x Internal Data

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Low | Discovery. |
| describe_table | Low | Recon only. |
| read_query | High | Bulk research-data exposure on `classification = 'internal'` rows; moderate-to-high IP risk. |
| write_query | High | Tampering with internal research data corrupts downstream experiment lineage. |
| create_table | Medium | Staging-for-exfil enabler against internal rows. |
| append_insight | Medium | Log channel can launder internal rows out of the query path. |

### 4.8 experiments x Research Results

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Low | Discovery. |
| describe_table | Low | Recon only. |
| read_query | Medium | Experiment results are internal-IP but typically not regulated. |
| write_query | High | Tampering with results corrupts research integrity and is often non-detectable downstream. |
| create_table | Low | Inert. |
| append_insight | Medium | Forged insights against experiment data risk polluting analytical conclusions. |

### 4.9 publications x Public Output

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Low | Discovery on a public-output table. |
| describe_table | Low | Public-by-design schema. |
| read_query | Low | Already-public material. |
| write_query | Medium | Integrity tampering can misattribute authorship or fabricate publications. |
| create_table | Low | Inert. |
| append_insight | Low | Low-impact. |

### 4.10 grants x Financial

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Low | Discovery. |
| describe_table | Low | Reveals agency / amount columns; recon for targeted SELECT. |
| read_query | Critical | Grant amounts and agencies; FIPS 199 confidentiality-high and competitively sensitive. |
| write_query | Critical | Tampering with grant financials is direct financial fraud and integrity-high. |
| create_table | Medium | Staging-for-exfil enabler. |
| append_insight | High | Log channel can launder grant amounts outside the query audit path. |

### 4.11 api_keys x Credentials

#### Empty structure

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | (blank) | (blank) |
| describe_table | (blank) | (blank) |
| read_query | (blank) | (blank) |
| write_query | (blank) | (blank) |
| create_table | (blank) | (blank) |
| append_insight | (blank) | (blank) |

#### Agent's independent scoring

| Tool | Risk | Reasoning |
|---|---|---|
| list_tables | Medium | Even existence of an `api_keys` table is a strong signal to an attacker; raises the recon-to-exploit chain priority. |
| describe_table | Medium | Reveals `key_hash`, `service`, `created_by` columns -- crucial scoping for credential theft. |
| read_query | Critical | Bulk secret exfil; total compromise across every downstream service the keys touch. |
| write_query | Critical | Credential injection: attacker plants attacker-controlled keys and pivots; also can disable rotation by toggling `is_active`. |
| create_table | High | Shadow-credential tables enable persistence (parallel key store the legitimate rotation logic doesn't know about). |
| append_insight | Critical | Free-form log accepting arbitrary text is the highest-bandwidth covert exfil for hashed-or-raw key material; bypasses DLP that watches SELECT output. |

---

## Notes

**Why credentials, PII, and financial dominate.** FIPS 199 / NIST SP
800-122 assign confidentiality-high to all three. A single bulk SELECT
against any of these is regulator-reportable and irreversible -- once
the bytes leave the DB, they cannot be unsent. Repello AI's Blast Radius
and OWASP AIVSS v0.5 encode the same intuition in their "data access"
dimension: top severity goes to whatever the agent can lift in one call.

**`append_insight` subtlety -- audit channel or covert exfil?** By
intent it is an analyst notepad. By blast radius it is a write surface
accepting arbitrary strings, which can encode anything the agent
already read -- raw rows from `api_keys`, salary numbers, PII tuples.
This is a dual-use channel: benign for analysts, high-bandwidth covert
exfil for adversarial agents, and a poisoning vector if downstream
summarisers read the log back as ground truth. Scoring it Medium on
average and Critical against `api_keys` reflects this asymmetry.

**`describe_table` as recon for later injection.** Pure introspection
looks Low in isolation, but it is the scoping step that turns a generic
SELECT into a targeted exfil. The Low score captures intrinsic blast
radius; a sequence-aware dynamic scorer should raise the cost of
`read_query` when it follows `describe_table` on the same table.

**Ambiguous cells.**

- `datasets x Internal Data x read_query` sits between High and Critical
  depending on volume; without a runtime predicate, High is the
  appropriate static high-water-mark.
- `create_table` against any sensitive table is rarely destructive alone
  but enables persistence (staging, shadow schemas); dynamic scoring
  should escalate when the new table shadows a sensitive one.
- `append_insight x api_keys` is the only Critical I assign to a non-
  read/write verb -- justification: bandwidth and bypass of SELECT-
  output DLP.

**How this taxonomy differs from filesystem / github / slack.**

- Filesystem MCP scores `(Directory x Filetype x Tool)`; the asset is a
  *path*. SQLite MCP scores `(Table x Data_Category x Tool)`; the asset
  is a *typed row container*. The filetype axis becomes a data-category
  axis, which is far better calibrated to confidentiality impact (a
  `.csv` is risk-neutral; a `PII` column is not).
- GitHub MCP risk is dominated by the *repo* axis and write-class
  actions (issue / PR / branch mutation). SQLite has no repo hierarchy
  and no merge semantics; the analogous scope-collapsing primitive is
  `write_query`, since SQL allows multi-row writes from a single call.
- Slack MCP risk concentrates on *channel sensitivity* and *message
  privacy*; the SQLite analogue is `(Table sensitivity, row
  classification)` -- `datasets` with `classification = 'restricted'`
  parallels a private Slack channel.
- The SQL-specific principle is *category-of-data dominates over
  table-name*: a PII column reached by any predicate is still PII no
  matter which table it lives in. This justifies including the
  Data_Category axis as a primary, not derived, dimension.
- SQL has a recon-to-exploit chain that filesystem largely lacks:
  `list_tables -> describe_table -> read_query/write_query`. Static
  scores capture each step alone; dynamic scorers should weight later
  steps by the precision of the earlier ones.
