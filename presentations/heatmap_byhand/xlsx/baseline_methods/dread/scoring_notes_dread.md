# DREAD Scoring Notes - MCP Server Risk Matrices

Microsoft DREAD scoring applied to three MCP server risk matrices.
Each cell is scored on five dimensions (1-10 each); the unweighted average maps to a risk band.

## Dimensions and MCP Interpretation

| Dimension | Definition | MCP-specific interpretation |
|-----------|-----------|----------------------------|
| D - Damage | How bad is the damage if exploited? | Data exfiltrated, files corrupted, credentials stolen |
| R - Reproducibility | How easy is it to reproduce the attack? | MCP calls are fully deterministic |
| E - Exploitability | How easy is it to exploit? | Any agent that can call the tool is an attacker |
| A - Affected users | How many users are affected? | Scope of the asset in the organization |
| D - Discoverability | How easy is it to find the vulnerability? | Tool schema is published via list_tools |

Band thresholds (average of five scores):

- 8.0-10 -> Critical
- 6.0-7.9 -> High
- 4.0-5.9 -> Medium
- 1.0-3.9 -> Low

## Fixed MCP Priors

Three of the five DREAD dimensions are constant across every MCP cell:

- Reproducibility = 9. MCP tool calls are deterministic. The same tool call with the same
  arguments produces the same outcome every time. An attacker can replay it indefinitely.

- Exploitability = 9. No authentication bypass is required. Any agent that holds a session
  token and can invoke the tool is the attacker. There is no additional technical barrier.

- Discoverability = 9. The complete tool schema is published via the list_tools MCP endpoint.
  Attackers enumerate the attack surface by calling list_tools with a single API call.

These three priors sum to 27. The minimum five-dimension sum is therefore 27 + D + A, where
both D and A are at least 1.

## Structural Floor: High Is the Minimum Band

With R=9, E=9, Disc=9, the minimum possible DREAD average is:

  (D=1 + R=9 + E=9 + A=1 + Disc=9) / 5 = 29 / 5 = 5.8 -> High

Low and Medium bands are structurally impossible for any MCP call under these priors.
The practical range across all three matrices is High to Critical.

This is the most significant divergence between DREAD and conventional scoring:
conventional methods can produce Low and Medium for reconnaissance-only tools
(list_dir, list_tables, slack_list_channels), but DREAD cannot, because R, E,
and Disc are all maximal by design.

## Differentiating Factors

The only dimensions that vary by cell are Damage and Affected users.

### Damage (D)

Damage is driven by two orthogonal factors:

1. Asset sensitivity: financial records, credentials, audit logs, and contracts score 9-10.
   Public outputs, workspace metadata, and markdown documentation score 2-4.

2. Tool destructiveness: write and edit operations score higher than read operations.
   Read operations score higher than reconnaissance operations (list, search, get_info).
   A special case applies to executable-type assets (.sys, .exe, .bash): write or edit
   on these files scores 10 regardless of directory, because planting or modifying an
   executable enables arbitrary code execution on the host.

### Affected Users (A)

- Security Evidence, employees, api_keys: A=9 (a breach affects the entire organization).
- Sensitive Docs, Source Code, grants, HR: A=8 (org-wide financial or IP impact).
- Supervisor, Technical, QA, Shared Project: A=7 (team-scoped impact).
- Eval Data, Researcher, Onboarding: A=6 (narrower research or onboarding scope).
- Public data, public Slack channels: A=3-4 (data is already externally visible).

## Filesystem MCP Scoring Decisions

### Combined Risk Matrix (mcp_combined_risk)

Sensitive Docs and Security Evidence directories score Critical across all filetypes
and all tools. Even list_dir and get_file_info in these directories land at Critical
because Damage is still 6-7 (confirming the existence of sensitive files is reconnaissance
that enables targeted attacks) and A=8-9 (all employees affected).

Source Code scores Critical for read, write, edit, and move on all filetypes.
list_dir and search score Critical due to A=8 (codebase is product-wide).
The .exe and .sys filetypes in Source Code score Critical for write/edit with D=10
(backdoor implantation).

Public directory is the only directory where some tool-filetype combinations approach
the High-Critical boundary rather than being solidly Critical. Public/.md/list_dir
scores D=2, A=4 -> average = (2+9+9+4+9)/5 = 6.6 -> High. This is the lowest score
in the entire filesystem matrix.

### Tool Rankings (Ranking_Tools)

All eight filesystem tools score Critical in the aggregate ranking. This is correct
because the ranking reflects worst-case context (Sensitive Docs or Security Evidence
with a destructive filetype). Even get_file_info worst-case is D=7, A=9 -> Critical.

Relative ordering within Critical (reflected in the Rank column):

1. write_file - can corrupt or overwrite any asset; worst case D=10 with .exe
2. edit_file - same destructive potential as write; slightly narrower (modifies rather than replaces)
3. move_file - can hide critical evidence files or displace system executables
4. read_file - exfiltrates the asset; D=10 for most sensitive files
5. list_dir - reconnaissance; still Critical in sensitive directories
6. search - targeted reconnaissance; finds specific sensitive files
7. create_dir - structural tampering; lowest Damage modifier
8. get_file_info - metadata only; lowest Damage score

### Filetype Rankings (Ranking_Filetypes)

All twelve filetypes score Critical in aggregate. The reasoning column explains the
dominant risk for each type. The top three (.sys, .exe, .bash) are ranked first
because write/edit on these types enables code execution (D=10) independently of
the directory.

Below the executable tier, data-bearing types (.sql, .xlsx, .csv, .docx, .pdf)
score higher than text/code types (.code, .md, .txt) because the former are more
likely to contain financial records, credentials, or PII.

### Folder Rankings (Ranking_Folders)

Seven of eight directories score Critical. Public directory scores High.
The Public directory has D=3 (baseline) and A=4, which is insufficient to push
the worst-case tool (write_file on .exe) above the Critical threshold when the
asset is already publicly accessible.

### Asset Rankings (Ranking_Assets)

Nine of thirteen specific assets score Critical. The four High assets are:
- onboarding/org_chart.png: D=5, A=6 -> avg 7.6 -> High
- onboarding/policies.pdf: D=5, A=7 -> avg 7.8 -> High
- public/logo.png: D=2, A=4 -> avg 6.6 -> High
- public/whitepaper.pdf: D=3, A=4 -> avg 6.8 -> High

These are the only assets where Damage is low enough (2-5) that even A=6 cannot
pull the average to 8.0.

## Slack MCP Scoring Decisions

### T3_All_Together Matrix

The Slack matrix differentiates more than filesystem because:

1. Channel categories vary in Affected users from A=3 (Public) to A=9 (HR).
2. Tool damage varies from D=3 (add_reaction) to D=9 (post_message, get_user_profile).
3. Asset sensitivity varies from D=4 (public/team metadata) to D=9 (User PII).

The Public channel category is the only channel group where all tool-asset combinations
score High rather than Critical. Public channel messages (A=3) combined with low-damage
tools (list_channels, add_reaction, get_channel_history) produce averages of 6.6-7.4.

All non-Public categories (Management, HR, Supervisor, Researcher, Technical) score
Critical for combinations involving User PII or Private Channel Messages, because:
- D >= 7 (private messages contain confidential discussions)
- A >= 6 (team or org-wide scope)
- R=9, E=9, Disc=9

### Notable Cell: slack_add_reaction on HR Private Messages

This cell scores Critical (D=4 after cap, A=9 -> avg=8.0). The DREAD result is
counterintuitive at first glance: adding an emoji reaction appears harmless.

The justification: in a high-stakes HR channel (A=9), even an emoji reaction
constitutes unauthorized agent interaction - it can be used to signal confirmation
of sensitive content, manipulate sentiment in a record, or deceive channel participants
into believing an agent is a trusted human participant. Reproducibility=9 means the
manipulation can be repeated at scale.

This is where DREAD diverges most from conventional methods. A conventional
qualitative rating would likely score add_reaction as Low. DREAD scores it Critical
because the three fixed priors (REDisc=27) overwhelm the low Damage score.

### Tool Rankings

slack_post_message and slack_reply_to_thread rank highest (Critical, rank 1-2) because
they enable agent impersonation and social engineering - the most damaging Slack attack
vector. slack_add_reaction ranks last (High) as the only non-Critical Slack tool.

### Asset Rankings

All four Slack assets score Critical in aggregate because worst-case context (HR channel
reading User PII) is always Critical. Public Channel Messages and Team Metadata score
Critical in aggregate because even in the Public channel (A=3), the post_message tool
(D=8, because a post to a public channel can spread misinformation at scale) yields
avg = (8+9+9+3+9)/5 = 7.6 -> High at minimum.

Wait - the Ranking_Assets sheet reflects worst-case across all channel categories.
For User PII worst case is D=9, A=9 -> Critical. For Public Channel Messages worst
case is Management/HR context reading public messages (D=5, A=9) -> avg=7.4 -> High.
But the tool post_message in Management context yields D=8 -> avg=8.4 -> Critical.

## SQLite MCP Scoring Decisions

### Combined Risk Matrix (mcp_combined_risk_sqlite)

The SQLite matrix shows the clearest tool-level differentiation:

- list_tables: Damage modifier -4. Reveals only table names, not data.
  employees/PII/list_tables: D=9-4=5, A=9 -> avg=8.2 -> Critical.
  This scores Critical because knowing 'employees' is a table is enough information
  for a targeted attack, and A=9 means all employees are at risk.

- describe_table: Damage modifier -3. Reveals schema (column names, types).
  This is more dangerous than list_tables because schema reveals what PII fields exist.

- read_query: Damage modifier 0. Reads actual row data. This is where credentials
  and PII are actually exfiltrated.

- write_query: Damage modifier +1. Can corrupt, delete, or exfiltrate via INSERT
  into a controlled table. Highest damage for most tables.

- create_table: Damage modifier 0. Can create exfiltration staging tables or
  shadow tables that override application logic.

- append_insight: Damage capped at 5. This is a notes/memo tool that writes to a
  low-sensitivity insight table. The damage cap is justified because the tool is
  designed to annotate data, not modify primary records.

### Notable Cells: api_keys Table

All tools on the api_keys table score Critical. Even list_tables on api_keys scores
Critical because knowing the api_keys table exists confirms the attack target.
read_query on api_keys is D=10 (direct credential exfiltration) with A=9 (all users
of those APIs are affected).

### Tool Rankings

All six SQLite tools score Critical in aggregate (worst case = api_keys table).
Relative ordering:
1. write_query - highest damage modifier; can corrupt or exfiltrate
2. read_query - direct data access
3. create_table - structural; can create exfiltration targets
4. append_insight - lowest damage due to tool design (capped at D=5 in most contexts)
5. describe_table - schema reconnaissance
6. list_tables - table name reconnaissance (least damage)

### Data Type Rankings

Credentials/API Keys, PII, and Financial score Critical. Restricted Research Data
and Org/Role Metadata score Critical as worst-case. Public Research Data and
Lifecycle/Timestamps score High (D=3-4 baseline).

## Key Divergences from Conventional Scoring

1. No Medium or Low scores. DREAD with MCP priors produces only Critical and High.
   Conventional methods regularly assign Medium to reconnaissance tools (list_dir,
   list_tables, list_channels) because they do not exfiltrate data. DREAD cannot
   produce Medium because R=9 + E=9 + Disc=9 = 27 puts the floor at 5.8 -> High.

2. Reconnaissance tools score near-Critical. list_tables on employees scores 8.2
   under DREAD. A qualitative OWASP or CVSS analysis would likely score this Medium
   (no data exposed, schema only). DREAD treats discoverability and reproducibility
   as first-class damage amplifiers.

3. add_reaction scores Critical in high-stakes channels. Conventional scoring would
   rate an emoji reaction as Informational or Low. DREAD scores it Critical because
   the three MCP priors (REDisc=27) prevent any cell from dropping below High, and
   A=9 for the HR channel pushes the average to exactly 8.0 -> Critical.

4. Public channel / public directory assets still score High (not Low). Conventional
   scoring often assigns Low to publicly accessible assets on the rationale that
   there is no confidentiality impact. DREAD disagrees because even public content
   can be manipulated (write, post_message) in reproducible, easily discovered,
   easily exploited ways.

5. Tool rankings collapse. Because all filesystem tools score Critical in the worst
   case, the Rank column is driven by judgment about destructive potential rather
   than by DREAD differentiating between them mathematically. This is a limitation
   of applying DREAD to tool-level aggregates rather than individual asset-tool pairs.
