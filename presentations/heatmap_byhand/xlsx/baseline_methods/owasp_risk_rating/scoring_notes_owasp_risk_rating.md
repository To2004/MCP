# OWASP Risk Rating Methodology -- MCP Scoring Notes

Adaptation of the OWASP Risk Rating Methodology to score three MCP server risk
matrices: Filesystem MCP, Slack MCP, and SQLite MCP.

## Method Overview

OWASP Risk Rating uses two aggregate scores, each on a 0--9 numeric scale, which
are then classified into tiers and combined via a fixed 3x3 matrix.

**Likelihood** = average of four threat-agent factors (each 0--9):

| Factor | Description | Low end | High end |
|--------|-------------|---------|---------|
| Skill level | Technical skill required | 1 = expert | 9 = no skill |
| Motive | Reward or incentive | 1 = low reward | 9 = high reward |
| Opportunity | Access needed to exploit | 1 = full access | 9 = no access |
| Population size | Who could perform the attack | 1 = individual | 9 = all users |

**Impact** = average of two impact dimensions:

- Technical impact: data disclosure, integrity loss, non-repudiation failure, availability loss.
- Business impact: financial damage, reputation damage, compliance violations, privacy violations.

**Banding matrix** (L and I each classified as Low < 3, Medium 3--5, High >= 6):

|           | Low I   | Medium I | High I   |
|-----------|---------|----------|----------|
| Low L     | Low     | Low      | Medium   |
| Medium L  | Low     | Medium   | High     |
| High L    | Medium  | High     | Critical |

Valid output bands: Critical, High, Medium, Low.

## MCP Context Adaptations

### Attacker model

The attacker is an AI agent with MCP protocol access. The MCP server is the
protected asset. The agent can invoke any registered tool in a single protocol
call with no additional lateral movement required.

### Likelihood factors

- **Skill level = 7** (no human skill required; the agent calls a tool by name).
- **Opportunity = 7--8** (7 for write/destructive tools that may require a payload;
  8 for read and enumeration tools that accept no user-supplied parameters).
- **Population = 9** (any agent instance that has been granted MCP access can
  invoke any tool).
- **Motive** varies by tool: write tools that enable social engineering or data
  exfiltration score 8--9; passive enumeration tools score 5--6; low-value tools
  such as add-reaction score 3.

These parameters guarantee a minimum Likelihood score of 6.5, which places every
tool in the High likelihood tier. Under the OWASP matrix, High L combined with
Low I yields Medium. Therefore **no combination in this model can produce a Low
band**. This is a correct upper-bound finding: MCP direct-call access means no
interaction is truly low risk.

### Impact factors

Impact is computed in two layers:

1. **Asset sensitivity baseline** -- directory (Filesystem), channel category
   (Slack), or table+data-category (SQLite) sets a base (technical, business)
   pair. Sensitive personal data and credentials anchor at (9, 9); public
   content anchors at (2--3, 2--4).
2. **Tool modifier** -- applied additively. Read tools carry a 0 delta.
   Destructive write tools add +1 to both dimensions. Enumeration and metadata
   tools subtract 1--3 from technical impact and 0--2 from business impact.
   All values are clamped to [1, 9].

For **business impact**, compliance exposure (GDPR, HIPAA) and reputation damage
are weighted heavily. Any table or channel containing employee PII or health-
adjacent data receives a business impact of 9 regardless of directory sensitivity.
Financial records and credentials similarly anchor at 9.

### Static upper-bound scoring

All scores represent the worst-case attacker intent. A tool is scored as if an
adversarial agent will maximize the harm achievable with that call. This is
appropriate for a server-side gate decision: the server cannot know the agent's
intent in advance.

## Key Scoring Decisions by MCP Server

### Filesystem MCP

- **Sensitive Docs and Security Evidence** directories start at tech=9, biz=9.
  All non-trivial tools on any filetype in these directories score Critical.
- **Source Code** starts at tech=8, biz=7. Write and edit operations score
  Critical; get_file_info and create_dir score High due to lower impact.
- **Public** directory starts at tech=3, biz=4. Write tools score High (attacker
  can plant malicious files in public-facing space). Read and enumerate tools
  score Medium (high likelihood, minimal data impact).
- **.png and .txt** filetypes apply a -2/-1 and -1/0 impact modifier respectively;
  .sys, .exe, .bash, .sql, .code apply no negative modifier (maximum sensitivity).
- **get_file_info** applies the largest negative tool modifier (-3 tech, -2 biz)
  because it returns metadata only, not file content.
- **create_dir** is also heavily discounted (-4 tech, -3 biz) because creating an
  empty directory has no direct data disclosure effect.

### Slack MCP

- **Management and HR channels** receive the highest base impact (9, 9) for
  Private Channel Messages and User PII, reflecting GDPR, HIPAA, and strategic
  information sensitivity.
- **slack_post_message and slack_reply_to_thread** receive +1 tech / +2 biz tool
  modifiers because write access enables social engineering and targeted phishing
  within trusted conversation threads, amplifying business damage.
- **slack_add_reaction** receives a -4/-4 modifier and a motive of only 3; it
  scores Medium on all meaningful assets because it cannot exfiltrate data.
- **slack_list_channels** receives -2 tech / -1 biz (enumeration only, no content
  access).
- The T3_All_Together sheet ranks each channel group by its worst-case band; the
  rank value is written to the top (master) cell of each merged group range.
- **No Low bands appear** because the minimum Likelihood = 6.5 (High tier) drives
  even low-impact cells to Medium.

### SQLite MCP

- **api_keys / Credentials** is the highest-risk table: base impact (9, 9) and
  write_query adds +1 to both dimensions, yielding Critical across all read and
  write tools.
- **employees / Financial** and **employees / PII** anchor at (9, 9) for GDPR /
  payroll compliance reasons.
- **experiments / Research Results** anchors at (8, 8) for unpublished IP
  protection.
- **publications / Public Output** and **datasets / Public Data** anchor at (3, 3);
  list_tables and describe_table produce Medium (not Low) because of high
  Likelihood tier.
- **list_tables** applies a -3/-2 tool modifier (schema enumeration only);
  **describe_table** applies -2/-1. Despite these reductions, both tools score
  Critical on high-sensitivity tables because High L + High I = Critical.
- **create_table** applies -1/0 modifier; append_insight applies -1/0. These
  score Critical on credential and PII tables because the underlying data impact
  remains in the High tier.

## Score Distribution Summary

| File | Critical | High | Medium | Low |
|------|----------|------|--------|-----|
| Filesystem (combined matrix) | 350 | 206 | 52 | 0 |
| Slack (T3 combined) | 83 | 67 | 26 | 0 |
| SQLite (combined matrix) | 41 | 16 | 9 | 0 |

The absence of Low-band scores across all three servers is not an artifact of
over-inflation; it reflects the structural property of MCP: opportunity and
population are maximally high for any tool that has been registered with the
server. A server operator who wishes to accept Low-risk tool calls must either
restrict tool registration or introduce per-call authentication that reduces the
population and opportunity factors.
