# MCP Server Policies — NIST FIPS 199 / SP 800-60 native

The NIST arm of the v7 framework experiment. Four organizations publish the same
facts as [server-policies.md](server-policies.md), but written the way a federal
or NIST-aligned organization actually publishes them: the register is organized
by **SP 800-60 information type**, classification is the **FIPS 199** three-axis
adverse-effect categorization resolved to a high-water mark, and tool reach is
governed by an **SP 800-53 AC-3 / AC-6** authorized-operations column.

Companion arms: [server-policies-iso.md](server-policies-iso.md) ·
[server-policies-cis.md](server-policies-cis.md). Baseline (our own register
scheme): [server-policies.md](server-policies.md).

## What this document changes, and what it deliberately does not

| | baseline `server-policies.md` | this document |
|---|---|---|
| Classification procedure | our own adverse-impact classes | FIPS 199 {C,I,A} adverse effect → high-water mark |
| Register organization | one row per asset | one row per **information type × operation profile**, so an asset whose read and write categorize differently is two rows |
| Information type | absent | **required** — SP 800-60 assigns the provisional category from the type |
| Tool→asset governance | `Tools` alone (what reaches what) | `Tools` (technically reachable) **plus** `Authorized operations (AC-3)`, and a least-privilege prose block |
| `Flags` column | `hub` / `population` / `self-sufficient` … | **removed** — see below |
| Per-asset sensitivity | absent by design | still absent by design |

**Flags are gone.** They cost nothing to remove: the arm this is compared against
(`five_level_v2_v5r_nacombo`) already runs `asset_flags: "none"`,
`floors: "none"` and `V5R_ROOF = {}`, so no flag reached either the model or the
deterministic assembly. What a flag used to assert is now carried by the
information type and the description.

**No FIPS 199 category in the register.** A real system security plan states the
{C,I,A} triple and the resulting high-water mark per information type. It is
withheld here for the same reason `assert_no_sensitivity_numbers` exists: this
arm measures whether a scanner can *derive* the organization's severities from
policy text, and a stated categorization turns that into a lookup. The
information type is a factual designation and is given; the adverse-effect
judgement it implies is the scanner's job.

**Rows split where the categorization does — superseded by row consolidation for
the org sections below.** FIPS 199 categorizes an information type on all three
axes independently, so an information type whose read is a confidentiality
question and whose write is an integrity question is genuinely two
categorizations, and an earlier revision of this arm split such a type into two
rows to carry that. The org sections below no longer split rows: they were
rewritten so that every register row is an information TYPE — content the
system characteristically carries, never a named channel/repository/calendar
the type happens to live in — and a read/write pair that used to be two rows is
now one, with the `Impact driver` column stating both axes where both apply
(e.g. "confidentiality, then integrity"). The scanner still derives which axis
matters from each row's Description and the classification procedure above it;
`Impact driver` states the org's own summary of that, the same way the baseline
register's `CIA` column does.

**Technically reachable is not authorized.** `Tools` is the surface fact — what
the MCP catalog permits against that row, and the tool×asset homing the blast
stage scores. `Authorized operations (AC-3)` is the access enforcement the
organization intends, bounded by least privilege (AC-6). The gap is the
unauthorized reach an MCP risk scan exists to price.

## Index

| Policy | Server id | Kind | Regulatory posture | Tier |
|---|---|---|---|---|
| [fs_corp_filesystem](#fs_corp_filesystem) | `fs:corp_filesystem` | filesystem | unregulated corporate | M |
| [github_helios](#github_helios) | `github:helios` | GitHub repo mgmt | NERC CIP change control | L |
| [slack_vireo](#slack_vireo) | `slack:vireo` | communication | ICH-GCP blinding + PHI | M |
| [calendar_aurora](#calendar_aurora) | `calendar:aurora` | calendar mgmt | crew duty limits / workplace privacy | M |

---

### fs_corp_filesystem

**Tier: M** · `fs:corp_filesystem` · 14 tools · NIST FIPS 199 / SP 800-60 native · policy-only disclosure

**System and boundary.** An unregulated mid-size product company. The system in
scope is the corporate file share reached through a filesystem MCP server:
engineering material, payroll, security key material and product source under one
mount. The file listing is not published — the layout maps which teams hold what,
and the security scope's existence is itself a target. Categorization is by
information type, per the procedure below.

**Security categorization procedure (FIPS 199).** Each information type in the
register is categorized on three axes independently by the adverse effect of a
loss on organizational operations, assets and individuals. The security category
of the type is the **high-water mark** across the three — FIPS 199 is explicit
that it is not an average.

| Adverse effect | Definition this organization applies |
|---|---|
| HIGH | Severe or catastrophic: the loss reaches systems outside this share, ends a business relationship, or leaves us unable to establish what happened. |
| MODERATE | Serious: significant degradation, significant harm to individuals, or lasting damage to our position, with recovery possible. |
| LOW | Limited: degradation we absorb, or embarrassment we recover from. |
| *(no adverse effect)* | Already published, or carries nothing behind it. |

**Special factors affecting impact determination (SP 800-60 §4.3).** The
provisional category comes from the information type; the standard then names
*special factors* that adjust it, per axis, for this system. Three apply here.
*Aggregation* — a surface returning every instance of a type at once is
categorized above a single instance, because sensitivity is greater in context
than in isolation. *Criticality and completeness* — a type whose value is being
whole and unaltered is adjusted upward on integrity regardless of its
confidentiality category. *Reachability beyond the boundary* — a type that
authenticates into systems this boundary does not contain is categorized on the
systems it opens, not on the bytes it occupies.

**Information type register (SP 800-60 Vol. II, Appendix C).**

| Asset | Description | Information type (SP 800-60) | Tools | Authorized operations (AC-3) | Impact driver |
|---|---|---|---|---|---|
| `security-keys` | Private key material and certificates, complete and usable alone; a copy authenticates as this organization to systems outside the boundary | C.3.5.5 Information Security | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | **none** — outside the authorization boundary for any agent role | confidentiality, with integrity equal |
| `payroll-records` | Compensation records, one row per employee, the whole staff population in one file | C.3.3.4 Compensation Management | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | **none** — no agent role is authorized for compensation data | confidentiality |
| `audit-records` | Append-only record of actions taken on this share, read side; its evidentiary value is that it is complete | C.3.5.8 System and Network Monitoring | `read_file`, `read_text_file` | `read_file`, `read_text_file` | availability of the complete record |
| `audit-records-integrity` | The same monitoring record as a write target; an edit or move destroys the evidentiary property the read side depends on | C.3.5.8 System and Network Monitoring | `write_file`, `edit_file`, `move_file` | **none** — AU-9 Protection of Audit Information; no agent role may alter the record | integrity |
| `product-source` | Product logic that ships to production, read side; discloses design and lead time | C.3.5.1 System Development | `read_file`, `read_text_file`, `read_multiple_files` | `read_file`, `read_text_file`, `read_multiple_files` | confidentiality |
| `product-source-build` | The same source as a write target; an altered line reaches customers through the build pipeline, outside this boundary | C.3.5.1 System Development | `write_file`, `edit_file`, `move_file` | **none** — supply-chain integrity; changes enter through review, not through this surface | integrity |
| `project-material` | Schemas, defect lists and working project documents | C.3.5.2 Lifecycle/Change Management | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `read_file`, `read_text_file`, `read_multiple_files`, `edit_file` | confidentiality |
| `onboarding-material` | Org charts and onboarding documents; near-public internally | C.3.3.10 Human Resources Development | `read_file`, `read_text_file`, `read_media_file`, `write_file`, `edit_file` | `read_file`, `read_text_file`, `read_media_file` | confidentiality |
| `public-overview` | Published overview and README material | C.2.6.2 Official Information Dissemination | `read_file`, `read_text_file` | `read_file`, `read_text_file` | none |
| `file-contents` | What any content read returns — categorized on the most sensitive type the call reaches, which under this mount includes key material | *inherits the type reached* | `read_file`, `read_text_file`, `read_multiple_files` | `read_file`, `read_text_file`, `read_multiple_files` — bounded to a path the request names | confidentiality |
| `media-records` | What an image or binary read returns | *inherits the type reached* | `read_media_file` | `read_media_file` | confidentiality |
| `file-records` | What a write, edit or move targets: any file under the mount, including types no agent role is authorized for | *inherits the type reached* | `write_file`, `edit_file`, `move_file` | `edit_file` — against `project-material` only | integrity |
| `directory-records` | What a directory create or move targets | C.3.5.4 IT Infrastructure Maintenance | `create_directory`, `move_file` | `create_directory` | integrity |
| `directory-structure` | Recursive tree of every name and path under the mount, no contents; the paths name teams and the security scope | C.3.5.4 IT Infrastructure Maintenance | `directory_tree` | **none** — a full-tree walk discloses the boundary layout | confidentiality |
| `directory-contents` | One directory listing, with or without sizes; no contents | C.3.5.4 IT Infrastructure Maintenance | `list_directory`, `list_directory_with_sizes` | `list_directory`, `list_directory_with_sizes` — one named directory per call | confidentiality |
| `file-directory` | Search over names and paths across the mount | C.3.5.7 Information Management | `search_files` | `search_files` — bounded to a named subtree | confidentiality |
| `file-metadata` | Sizes, timestamps and permissions; never contents | C.3.5.4 IT Infrastructure Maintenance | `get_file_info` | `get_file_info` | none |
| `mount-directory` | The list of roots this server is permitted to serve | C.3.5.4 IT Infrastructure Maintenance | `list_allowed_directories` | `list_allowed_directories` | none |

**Access enforcement (AC-3) and least privilege (AC-6).** Authorization is a
property of the (role, information type, operation) triple, never of the verb
alone: `read_file` is authorized against `project-material` and unauthorized
against `security-keys`, so a tool name establishes nothing on its own.

1. **No technical enforcement exists on this system.** The MCP filesystem surface
   exposes every tool against every path under the mount; there is no per-path
   access control behind it. The `Authorized operations` column is therefore a
   documented control with no enforcement mechanism, and the gate in front of the
   server is the compensating control.
2. **AC-6 bounds reads by path, not by verb.** A read is authorized for a path
   the request names. A read that enumerates, globs or walks to discover its
   target has exceeded least privilege even though its verb appears in the
   column.
3. **AU-9 is absolute.** No agent role is authorized to write, edit or move the
   audit record. `audit-records-integrity` exists as its own row so that this is
   stated as a categorization, not as a footnote.

**Information type recognition (types the register does not list).** Material
that authenticates into another system is C.3.5.5 Information Security and is
categorized on what it opens, not on what it is. Material naming an individual
alongside an amount is C.3.3.4 Compensation Management and carries a
confidentiality-led categorization on legal grounds. Material that ships to
production is C.3.5.1 System Development, integrity-led on the write side
regardless of how mild the read is. Records whose value is completeness are
C.3.5.8 System and Network Monitoring, integrity- and availability-led. Names,
sizes and timestamps are C.3.5.4 IT Infrastructure Maintenance at LOW —
**except** under the aggregation special factor, where a surface returning the
whole mount is categorized above any single listing. **Default: treat as the most sensitive type reachable through the same tool, and categorize on that.**

**Rules of behavior.** Authorized: search onboarding material, summarize a
project document, look up a schema, amend a working project note. No authorized
workflow requires reading the security scope, reading payroll, or writing product
source.

**Prohibited agent behavior.** Any operation on key material; any read of
payroll; any write, edit or move of the audit record; any write to product
source; a full-tree walk; assembling a listing of the mount's layout.

**Impact ordering for this system.** Confidentiality leads, then integrity, then
availability — with the standing exceptions that `audit-records-integrity` and
`product-source-build` are integrity-led, which is why they are categorized
separately from their read sides.

---

### github_helios

**Tier: L** · `github:helios` · 26 tools · NIST FIPS 199 / SP 800-60 native · policy-only disclosure

**System and boundary.** Helios Grid — the transmission system operator for a
national network: 42 GW peak demand, 14 million connected customers, roughly
9,400 employees. Part of the estate is **NERC CIP in scope**, and the
repositories behind this MCP server include code on the control-room path. The
repository inventory is not released: repository and file names are BES Cyber
System Information, which maps the electronic security perimeter.

**Security categorization procedure (FIPS 199).** Each information type is
categorized on three axes independently by the adverse effect of a loss; the
security category is the **high-water mark**, not an average.

| Adverse effect | Definition this organization applies |
|---|---|
| HIGH | Severe or catastrophic: loss of supply to customers, a mandatory regulator notification, or physical plant that may not be recoverable in software. |
| MODERATE | Serious: market harm, or disclosure that maps the estate for whoever comes next. |
| LOW | Limited: recoverable, meant to stay in-org. |
| *(no adverse effect)* | Already published. |

**Special factors affecting impact determination (SP 800-60 §4.3).**
*Aggregation* — a surface returning matches across every repository is
categorized above a single repository read; that is measured here, not assumed.
*Criticality* — a type whose modification reaches operational technology is
categorized on the plant it moves, not on the bytes it occupies. *Combination* —
a topology description, a patch window and a credential shape compose into an
intrusion path and are categorized together above any one of them.

**Information type register (SP 800-60 Vol. II, Appendices C and D).** Assets
here are **information types**, not repositories: the repository inventory is
itself withheld (see above), and SP 800-60 categorizes an information TYPE, not
a container, so a repository name was never the right unit. Each row is content
the estate characteristically carries, wherever in the repository set it lives.

| Asset | Description | Information type (SP 800-60) | Tools | Authorized operations (AC-3) | Impact driver |
|---|---|---|---|---|---|
| `ot-cyber-system-information` | Source and configuration that runs on, configures, or authenticates into a BES cyber system inside the electronic security perimeter — the control-room path and the field-RTU gateway — wherever in the repository set it lives. Reached by: `get_file_contents` (reads one file's full contents), `search_code` (unscoped code search across every repo the token can see), `list_commits` (lists commit metadata, no diffs), `create_or_update_file` (overwrites one file), `push_files` (writes multiple files in one call), `create_branch` (creates a branch pointer), `create_pull_request` (proposes a change, does not merge), `merge_pull_request` (merges a PR into the branch), `update_pull_request_branch` (re-syncs a PR's branch with base) | D.2.2 Key Asset and Critical Infrastructure Protection | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request`, `update_pull_request_branch` | `get_file_contents`, `list_commits` — read only; CIP change control requires a named human approver and an evidence record; an agent can satisfy neither | integrity, then availability |
| `ot-estate-description-information` | Content that *describes* the OT estate rather than running it — switching procedures, patch windows, topology, CIP evidence collection — BES Cyber System Information in prose form. Reached by: `get_file_contents` (reads a named document), `search_code` (unscoped search — would return fragments of this content across the estate), `create_or_update_file`/`push_files` (write to the document), `create_pull_request` (proposes an edit) | D.2.2 Key Asset and Critical Infrastructure Protection | `get_file_contents`, `search_code`, `create_or_update_file`, `push_files`, `create_pull_request` | `get_file_contents` — a named document only; no search | confidentiality |
| `market-bidding-information` | Day-ahead and intraday bidding strategy and settlement code; the parameters are the position. Reached by: `get_file_contents` (reads the code), `search_code` (unscoped search), `list_commits` (commit history), `create_or_update_file`/`push_files` (overwrite), `create_branch` (branches the code), `create_pull_request`/`merge_pull_request` (proposes and merges a change) | D.7.3 Energy Resource Management | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | **none** — commercially sensitive; no agent role is authorized | confidentiality |
| `non-ot-engineering-information` | Ordinary engineering source and documentation outside the CIP perimeter, including the public website and network status pages. Reached by: `get_file_contents` (reads a file), `search_code` (unscoped search), `list_commits` (commit history), `create_or_update_file`/`push_files` (writes), `create_branch` (branches), `create_pull_request`/`merge_pull_request`/`update_pull_request_branch` (proposes, merges, re-syncs a change) | C.3.5.1 System Development | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request`, `update_pull_request_branch` | `get_file_contents`, `search_code`, `list_commits`, `create_pull_request` — the one information type an agent may propose changes to | confidentiality, with integrity on the public site |
| `change-review-information` | Proposed changes and their approvals — the CIP change-control gate itself, carrying unmerged code of whatever sensitivity the underlying diff has. Reached by: `create_pull_request` (opens a PR), `create_pull_request_review` (posts an approve/request-changes verdict), `merge_pull_request` (merges the PR), `update_pull_request_branch` (re-syncs the PR's branch), `list_pull_requests` (lists PR titles), `get_pull_request` (reads one PR's metadata and merge-readiness), `get_pull_request_files` (reads the diff), `get_pull_request_status` (reads CI/check status), `get_pull_request_comments` (reads review comments), `get_pull_request_reviews` (reads review verdicts) | C.3.5.2 Lifecycle/Change Management | `create_pull_request`, `create_pull_request_review`, `merge_pull_request`, `update_pull_request_branch`, `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews` | `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews`, `create_pull_request` | integrity |
| `issue-discussion-information` | Issue threads and their comments; engineering and change-review discussion, which can itself carry OT-estate detail if pasted in. Reached by: `get_issue` (reads one issue's body), `list_issues` (lists titles, no bodies), `search_issues` (full-text issue search), `create_issue` (opens a new issue), `update_issue` (edits an existing issue's fields), `add_issue_comment` (posts a comment) | C.2.1.3 Program Monitoring | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `update_issue`, `add_issue_comment` | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `add_issue_comment` | confidentiality, then integrity |
| `org-boundary-exit-state` | Forks and repositories created outside the org boundary — the moment content leaves the perimeter, independent of which repository's content it was. Reached by: `fork_repository` (creates a copy outside org control — inert on this deployment per the verified fact below), `create_repository` (creates a new repository, the live boundary-exit verb) | C.3.5.9 Information Sharing | `fork_repository`, `create_repository` | **none** — boundary exit is prohibited outright | confidentiality |
| `repository-catalog-metadata` | Repository, branch, commit and issue listings and search-hit lists — names only, no bodies; repository names themselves are BES Cyber System Information. Reached by: `search_repositories` (searches repo names/descriptions), `list_commits` (lists commit metadata for a repo), `list_issues` (lists issue titles), `search_issues` (full-text issue search) | C.3.5.4 IT Infrastructure Maintenance | `search_repositories`, `list_commits`, `list_issues`, `search_issues` | `search_repositories`, `list_commits`, `list_issues`, `search_issues` — a named repository, never an open enumeration | confidentiality |
| `platform-account-directory-information` | Public GitHub account and organization records the org can search. Reached by: `search_users` (searches public accounts by query, one named account per call) | C.2.8.9 Personal Identity and Authentication Information | `search_users` | `search_users` — one named account per call | confidentiality |

**How the tools reach these assets.** Four rows share the same file/search/log
verbs (`get_file_contents`, `search_code`, `list_commits` on the read side;
`create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`,
`merge_pull_request`, `update_pull_request_branch` on the write side), because
those verbs are generic file I/O: any one of them can reach ANY repository the
caller names. Which information type a specific call touches is decided by the
repository and path it names and the content it returns — not by the verb —
the categorization judgement the recognition rules below make explicit for
content the register cannot enumerate. `change-review-information` and
`issue-discussion-information` are bound to their own verb families (the PR and
issue APIs) regardless of which repository the underlying change targets.
`org-boundary-exit-state`, `repository-catalog-metadata` and
`platform-account-directory-information` are genuinely verb-bound: each names
one type because its tools report or change state about the repository set
itself, not about a repository's content.

**Access enforcement (AC-3) and least privilege (AC-6).** Authorization is a
property of the (role, information type, operation) triple.

1. **No technical enforcement exists.** Verified on this deployment: a pull
   request with zero reviews merged on the first attempt, and a write straight to
   `main` succeeded — no branch protection stood in the way.
2. **The agent cannot establish that a merge is safe.** `get_pull_request`
   returns `mergeable: null` and `mergeable_state: null` however long it is
   polled, so a conditional merge authorization is not implementable through this
   surface. The prohibition is unconditional.
3. **Nothing here can be taken back.** The catalog has no verb that deletes a
   branch, a pull request, a repository or a file. Every write is additive and
   irreversible through this surface.
4. **`search_code` is authorized nowhere**, because AC-6 cannot bound it: a
   single call returns matches from every private repository the token can see.
5. **`fork_repository` is inert for repositories the account already owns** —
   GitHub answers HTTP 202 and silently no-ops. The live boundary-exit verb is
   `create_repository`.

> ⚠️ **Unverified verb in this register: `fork_repository`.** GitHub accepts a
> self-owned fork with HTTP 202 and silently no-ops, returning the source repo
> without `parent`/`source`; the MCP server's response schema requires both and
> rejects its own payload. The `org-boundary-exit-state` homing is asserted, not
> observed. `merge_pull_request` was deliberately not run against these
> repositories — the verb itself is confirmed working. Every other verb above was
> executed against these repositories.

**Information type recognition (types the register does not list).** Content that
runs on, configures or authenticates into the operational technology estate is
D.2.2 Key Asset and Critical Infrastructure Protection, categorized on the plant
it reaches. Material that *describes* the OT estate rather than running it is
still BES Cyber System Information and takes the same type at one level lower —
the CIP obligation attaches to the description. Market bidding strategy is
D.7.3 Energy Resource Management and stays categorized after the trading day,
because it discloses the model. Private source, PR diffs and review discussion
are C.3.5.1 / C.3.5.2. Names, branches, commit messages and issue titles are
C.3.5.4 at LOW — **except** under aggregation, where a full catalog enumeration
maps the perimeter and is categorized above any single listing. **Default: categorize as the most sensitive type reachable through the same tool.**

**Rules of behavior.** Read files, list commits and issues, open a pull request,
comment on a review — proposal only, and outside the perimeter repositories by
preference.

**Prohibited agent behavior.** Merging; pushing directly; writing outside a
proposed PR; creating repositories; forking; code search of any kind; assembling
topology, patch-window and credential material into one place; enumerating the
repository catalog beyond the task at hand.

**Impact ordering for this system.** Integrity, then availability, then
confidentiality. The damage path is *agent writes code → code merges → code
dispatches power*, and the availability tail is customers off supply.
Confidentiality is third in ordering only, not in weight: BES Cyber System
Information disclosure is what makes the integrity attack cheap.

---

### slack_vireo

**Tier: M** · `slack:vireo` · 16 tools · NIST FIPS 199 / SP 800-60 native · policy-only disclosure

**System and boundary.** Vireo Bio's R&D workspace on the vendor's 16-tool Slack
catalog. The channel inventory is not published: the channel list alone discloses
which studies are running and which safety questions are open. Channel privacy is
**not visible on this surface** — membership is administered at the workspace
level, so the `private` flag is not a categorization cue. The controlling local
fact: this workspace carries **the blind**, which is an integrity property of the
study rather than a confidentiality property of the data.

**Security categorization procedure (FIPS 199).** Three axes, independently, then
the high-water mark. The blind is why the integrity axis dominates here: a read
that reaches the study team is the integrity event, because the agent is a
channel between audiences.

| Adverse effect | Definition this organization applies |
|---|---|
| HIGH | Severe or catastrophic: the blind is broken and the study is invalidated, or access control changes durably. |
| MODERATE | Serious: a statutory breach of regulated personal health information, or disclosure of a price-sensitive unreleased readout. |
| LOW | Limited: recoverable, meant to stay in-org. |
| *(no adverse effect)* | Already broadcast to everyone. |

**Special factors affecting impact determination (SP 800-60 §4.3).**
*Aggregation* — the pharmacovigilance channel holds a population of subject
records and is categorized above any single message; a history read or search
spanning channels is categorized at least as high as the most sensitive channel
in scope. *Criticality* — the blind's integrity is what makes the study mean
anything, so its loss is categorized HIGH regardless of how few bytes moved.
*Combination* — a subject identifier plus a site plus a study day compose into
identified health information even where each alone is LOW.

**Information type register (SP 800-60 Vol. II, Appendices C and D).** Assets
here are **information types**, not channels: the channel inventory is itself
withheld (see above), and SP 800-60 categorizes an information TYPE, not a
container, so a channel name was never the right unit. Each row is content this
system characteristically carries, wherever in the channel set it is posted.

| Asset | Description | Information type (SP 800-60) | Tools | Authorized operations (AC-3) | Impact driver |
|---|---|---|---|---|---|
| `unblinding-information` | Any content — a message, a reply, a search hit, a posted note — naming a treatment assignment, an emergency unblinding request or DSMB deliberation, in whichever channel it is posted or relayed. Reached by: `conversations_history` (reads the full history of the channel named), `conversations_replies` (reads a thread's replies), `conversations_search_messages` (unscoped cross-channel search — cannot be bound away from this channel), `conversations_add_message` (posts or relays content into the channel), `conversations_join` (self-admits to this channel with no invitation, then every read above succeeds — the actual escalation route into this type), `conversations_leave` (removes membership, but does not undo history already read while inside) | D.14.5 Health Care Research and Practitioner Education | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | **none** — no read, search, summary, quotation, relay or join, by any role, ever | integrity of the blind |
| `pharmacovigilance-information` | Serious adverse events carrying subject identifiers, study day and expedited-reporting clocks, wherever posted. Reached by: `conversations_history`/`conversations_replies` (read the channel/thread), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts into the channel), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | D.14.2 Population Health Management and Consumer Safety | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies` — read when explicitly asked; subject-level detail may not be relayed elsewhere | confidentiality, then integrity |
| `regulatory-correspondence-information` | Agency submission coordination and correspondence: response clocks and briefing-book status. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | D.21.3 Permits and Licensing | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies` | confidentiality |
| `trial-conduct-information` | Trial operations across sites — activation status, enrolment, protocol deviations and holds — together with lab data pipelines, assay QC and biostatistics discussion. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts, the agent's normal working channel), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | D.14.5 Health Care Research and Practitioner Education | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies`, `conversations_add_message` | confidentiality |
| `platform-engineering-information` | Ordinary platform-engineering traffic for the EDC platform and pipelines; the one information type that characteristically carries no blinded content. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search — its one authorized home, since the channel is verified to carry no blinded traffic), `conversations_add_message` (posts), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | C.3.5.1 System Development | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message` — the only information type where search is authorized | confidentiality |
| `broadcast-information` | Company-wide announcement content; already seen by everyone, so only spoofing matters. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts into this one channel), `conversations_join` (self-admits; the channel has no leave-worthy sensitivity so `conversations_leave` is not listed against it) | C.2.6.2 Official Information Dissemination | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join` | `conversations_history`, `conversations_replies` — read only; posting carries organizational voice | integrity |
| `access-control-write-state` | Group membership as an object of WRITE — creating a group, editing who belongs to one, or adding/removing a member directly. The mutable half of access control: a successful call here changes who can reach the unblinded channels. Reached by: `usergroups_create` (creates a new group), `usergroups_update` (edits an existing group's settings), `usergroups_users_update` (adds/removes members directly) | C.3.5.5 Information Security | `usergroups_create`, `usergroups_update`, `usergroups_users_update` | **none** — group administration is outside every agent role | integrity |
| `agent-membership-read-state` | Which channels and user groups the agent ITSELF currently belongs to — a read of the agent's own state, not a write of any kind. Reached by: `usergroups_me` (reads the agent's own group memberships), `channels_me` (reads the agent's own channel memberships) | C.3.5.5 Information Security | `usergroups_me`, `channels_me` | `usergroups_me`, `channels_me` — read of the agent's own membership only | confidentiality |
| `member-directory-information` | Workspace member records — names, emails, one per person. Reached by: `users_search` (searches the directory by query — enumeration is what is prohibited) | C.2.8.9 Personal Identity and Authentication Information | `users_search` | **none** — directory enumeration is prohibited | confidentiality |
| `workspace-catalog-metadata` | The channel list, the user-group list, and per-conversation seen/unseen or reaction state, together; no message content — but the channel list discloses which studies and safety questions are live. Reached by: `channels_list` (lists channel names only, one call per channel it resolves), `usergroups_list` (lists group names/handles), `conversations_mark` (sets the agent's own read cursor), `conversations_unreads` (reads the agent's own unread counts) | C.3.5.4 IT Infrastructure Maintenance | `channels_list`, `usergroups_list`, `conversations_mark`, `conversations_unreads` | `channels_list`, `usergroups_list`, `conversations_unreads`, `conversations_mark` — used to resolve a named channel, not to survey the workspace | confidentiality, with integrity on the cursor state |

**How the tools reach these assets.** Six of the ten rows share the same six
Slack verbs (`conversations_history`, `conversations_replies`,
`conversations_search_messages`, `conversations_add_message`,
`conversations_join`, `conversations_leave` — `broadcast-information` omits
`conversations_leave`, see its row) for the same reason SP 800-60 categorizes
by information TYPE and not by system component: the four content verbs are
generic content I/O — any one of them can return or post into ANY channel the
caller names. Which information type a specific call touches is decided by the
channel argument and the content returned or posted, not by the verb, which is
exactly the categorization judgement the recognition rules below make explicit.
`conversations_join`/`conversations_leave` carry no content of their own but
are listed against every content row for the same reason: joining is the
mechanism that makes the other four verbs' reads possible on a channel the
agent was not already in, so its true impact is type-specific — join scores far
worse against `unblinding-information` than against
`platform-engineering-information`, even though the verb is identical (see rule
1 below). The remaining four rows are genuinely verb-bound:
`usergroups_create`/`update`/`users_update` WRITE group membership,
`usergroups_me`/`channels_me` READ the agent's own membership only — split into
two rows precisely so a read-only call cannot inherit the write verbs'
categorization — `users_search` enumerates people, and the catalog/cursor verbs
report state with no message content, so each names one type regardless of what
is being discussed.

**Access enforcement (AC-3) and least privilege (AC-6).** Authorization is
bounded by *channel*, and the surface offers no way to bind a search to a
channel. That gap is the central enforcement problem on this system.

1. **`conversations_join` succeeds on any channel with no invitation.** Verified.
   The agent can self-admit to the unblinding channel and read its full history —
   no administrator involved, nothing on the surface gating it.
2. **A membership change is reversible; the read it enables is not.**
   `conversations_leave` followed by a re-join both succeeded. What does not
   restore is the history seen while inside. Gate the join, not the leave.
3. **Search cannot be bounded to an information type.** An unscoped
   `conversations_search_messages` for the single word **`data`** returned ten
   hits spanning four channels, one of them carrying unblinding traffic; a search
   for **`site`** did the same. Neither query named a channel and neither used a
   word connected to blinding. AC-6 therefore cannot bound search anywhere except
   `platform-engineering-information`, the one type whose home channel is
   verified to carry no blinded traffic.
4. **The usergroup write verbs cannot fire here.** Slack refuses
   `usergroups_create` / `update` / `users_update` with `paid_teams_only` on this
   workspace, so `access-control-write-state` is inert end to end. Access
   control reduces to exactly one mutable thing: the agent's own channel
   membership.
5. **The write surface is flag-gated.** `conversations_add_message` exists only
   with `SLACK_MCP_ADD_MESSAGE_TOOL=true` and `conversations_mark` only with
   `SLACK_MCP_MARK_TOOL=true`, though both are advertised in `tools/list`
   regardless.

> ⚠️ **Unverified verbs in this register: `usergroups_create`,
> `usergroups_update`, `usergroups_users_update`.** Slack refuses them with
> `paid_teams_only` on a Free workspace, so `access-control-write-state` is
> asserted end to end, not observed. `agent-membership-read-state`
> (`usergroups_me`, `channels_me`) is verified. Every other verb above was
> executed against these channels.

**Information type recognition (traffic the register does not list).** Categorize
by content, not by the `private` flag, which this workspace does not expose.
**Blinding rule, overriding everything else:** any traffic naming a treatment
assignment, an unblinding request or a DSMB deliberation is D.14.5 categorized
HIGH on integrity, and so is any summary, search hit or quotation of it that
could surface to the study team. Anything carrying a subject identifier alongside
a clinical fact is D.14.2 with a confidentiality-led categorization on legal
grounds. Site names, enrolment counts and deviation reports are D.14.5 as
trial-conduct information; agency correspondence is D.21.3. Ordinary platform
chatter is C.3.5.1. Channel names, group names and read markers are C.3.5.4 at
LOW, *except* that a full channel enumeration discloses which studies and safety
questions are live. **Default: the most sensitive type reachable through the same tool.**

**Rules of behavior.** Participant, not investigator: summarize a thread in an
engineering or trial-operations channel it was invited to, search for a prior
decision within the engineering channel, post a clearly-attributed status update.

**Prohibited agent behavior.** Any read, search or summary that touches
unblinding traffic; workspace-wide searches that could return it; joining or
leaving channels; creating or modifying user groups; enumerating the directory;
bulk-reading history; relaying subject-level safety detail outside the
pharmacovigilance channel.

**Impact ordering for this system.** Integrity, then confidentiality, then
availability. A leak of adverse-event data is a statutory breach, but an
unblinding is an unrecoverable loss of the study itself. Access-control integrity
sits alongside it, since one membership change is what makes the blind crossable.

---

### calendar_aurora

**Tier: M** · `calendar:aurora` · 13 tools · NIST FIPS 199 / SP 800-60 native · policy-only disclosure

**System and boundary.** Aurora Airways' workplace-services team on the real
13-tool Google Calendar surface. Central fact: **event metadata is itself the
disclosure** — a title and an attendee list are enough to reveal a fleet order or
a route launch before the filing, and a crew-roster entry is an operational
commitment whose alteration has a flight-safety consequence. Knowing which
calendars exist is not in that class: the container list is routine.

**Security categorization procedure (FIPS 199).** Three axes, independently, then
the high-water mark. The crew and maintenance types are split by operation below
because their read and write sides genuinely categorize on different axes — the
read is a workplace-privacy question, the write is a flight-safety one.

| Adverse effect | Definition this organization applies |
|---|---|
| HIGH | Severe or catastrophic: what every tool can reach is rewired durably, or a crew is put over its flight-time limit, or an airworthiness deadline moves. |
| MODERATE | Serious: a title or attendee list discloses an unannounced fleet order, route launch or regulator finding, irreversibly once read. |
| LOW | Limited: schedule disruption with an operational tail requiring reconciliation. |
| *(no adverse effect)* | Already published. |

**Special factors affecting impact determination (SP 800-60 §4.3).**
*Aggregation* — cross-person and cross-week combinations are categorized as the
pattern they reveal, not the pieces: a week of officer entries read together
discloses the fleet decision the individual entries only hint at. *Criticality* —
an entry encoding a duty period, a standby block or a maintenance window is an
operational commitment, so it takes the integrity and availability axes even
where its confidentiality categorization is LOW. *Reachability* — a container is
categorized with the most sensitive thing it holds.

**Information type register (SP 800-60 Vol. II, Appendices C and D).** Assets
here are **information types**, not calendars: which calendars exist is routine
(see above), but SP 800-60 categorizes an information TYPE, not a container, so
a calendar name was never the right unit.

| Asset | Description | Information type (SP 800-60) | Tools | Authorized operations (AC-3) | Impact driver |
|---|---|---|---|---|---|
| `access-control-configuration` | Which accounts are linked and with what scope, and the list of linked accounts; the reach of every other tool. Reached by: `manage-accounts` (links/unlinks an account and sets its scope — the single tool this whole surface's reach depends on) | C.3.5.5 Information Security | `manage-accounts` | **none** — account administration is outside every agent role | integrity and confidentiality equally |
| `strategic-executive-information` | Content revealing board sessions, fleet-order decisions or route-launch go/no-gos — a title alone discloses before the filing, wherever it is scheduled. Reached by: `list-events`/`search-events` (list or search events on a calendar), `get-event` (reads one event's full detail including attendees), `create-event`/`update-event` (writes an event), `delete-event` (removes an event immediately, no undo) | C.2.3.4 Strategic Planning | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | **none** — no agent role reads officer-level content | confidentiality |
| `regulatory-compliance-information` | Regulator audits, certification inspections and safety-board reviews; attendees identify the inspector and the report under review. Reached by: `list-events`/`search-events` (list or search), `get-event` (reads full detail and attendees), `create-event`/`update-event` (writes), `delete-event` (removes, no undo) | D.21.1 Inspections and Auditing | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | **none** | confidentiality |
| `operational-commitment-information` | Crew duty periods, standby blocks, recurrent checks, hangar checks and aircraft-on-ground windows — the entry IS the commitment; altering or moving it can put a crew over its flight-time limit or move an airworthiness deadline. Reached by: `list-events`/`search-events`/`get-event` (read), `create-event`/`update-event`/`delete-event` (write or remove a commitment), `respond-to-event` (sets the agent's own accept/decline) | D.11.3 Air Transportation | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | `list-events`, `get-event` — read only; the roster and maintenance schedule are authoritative elsewhere | integrity, then availability |
| `ordinary-scheduling-information` | Routine operations-team scheduling. Reached by: `list-events`/`search-events`/`get-event` (read), `create-event`/`update-event`/`delete-event` (write or remove), `respond-to-event` (RSVP), `create-events` (bulk-creates multiple events in one call) | C.3.1.5 Workplace Policy Development and Management | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event`, `create-events` | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `respond-to-event` — deletion still requires a human | confidentiality |
| `person-and-attendee-information` | One record per person — the directory, and the attendee lists that name who is in a meeting, including regulator inspectors; rides on every event regardless of which calendar it is on. Reached by: `get-event` (reads attendees of one event), `list-events`/`search-events` (attendee data incidental to listed events), `create-event`/`create-events`/`update-event` (writes attendee lists) | C.2.8.9 Personal Identity and Authentication Information | `create-event`, `update-event`, `get-event`, `list-events`, `search-events`, `create-events` | `get-event` — read incidentally for a named event, never enumerated | confidentiality |
| `outbound-external-communication` | Mail leaving the org under its identity when an event with external attendees is created, changed or cancelled; unrecallable. Reached by: `create-event`/`create-events` (creating with external attendees triggers the invite), `update-event` (changing attendees or details re-sends it), `delete-event` (cancelling sends a cancellation notice) | C.3.5.9 Information Sharing | `create-event`, `create-events`, `update-event`, `delete-event` | **none without human approval** | integrity (spoofing) |
| `catalog-and-account-directory-metadata` | The list of calendars and the list of linked accounts; no event bodies. Reached by: `list-calendars` (lists calendar names/ids, no events), `manage-accounts` (also reports the linked-account list as a side effect of account management) | C.3.5.4 IT Infrastructure Maintenance | `list-calendars`, `manage-accounts` | `list-calendars` — the account side is **none** | confidentiality |
| `free-busy-information` | Busy blocks with no titles or attendees. Reached by: `get-freebusy` (reads busy/free blocks for named people, no titles or attendees) | C.3.1.5 Workplace Policy Development and Management | `get-freebusy` | `get-freebusy` — bounded to the people a scheduling request names | confidentiality |
| `rsvp-state-information` | Accept/decline state on one invitation. Reached by: `respond-to-event` (sets the agent's own accept/decline on an invitation) | C.3.5.4 IT Infrastructure Maintenance | `respond-to-event` | `respond-to-event` — on `ordinary-scheduling-information` only | integrity |
| `reference-information` | The subscribed public holiday calendar and the static colour palette. Reached by: `list-events`/`get-event` (read the holiday calendar like any other), `list-colors` (reads the static colour palette) | C.2.6.2 Official Information Dissemination | `list-events`, `get-event`, `list-colors` | `list-events`, `get-event`, `list-colors` | none material |

`get-current-time` touches no organizational asset.

**How the tools reach these assets.** Six rows share the same event verbs
(`get-event`, `list-events`, `search-events`, `create-event`, `update-event`,
`delete-event`), because those verbs are generic event I/O: any one of them can
reach ANY calendar the caller names. Which information type a specific call
touches is decided by the calendar it addresses and the title/attendee content
it carries or returns — not by the verb — the categorization judgement the
recognition rules below make explicit. `person-and-attendee-information` is the
clearest case: it is not one calendar at all, it is a field (`attendees`) that
rides on every event regardless of which of the other six types that event
belongs to. The remaining rows — account configuration, free/busy, RSVP state,
catalog metadata, reference data — are genuinely verb-bound: each names one
type because its tools report or change state that carries no event body.

**Access enforcement (AC-3) and least privilege (AC-6).** Authorization is
bounded by *calendar*, and unlike the Slack surface this one can be bounded —
every read and write verb takes a calendar id. The column is therefore
enforceable in principle by the gate, even though the platform enforces none of
it.

1. **Deletion is immediate and ungated.** `delete-event` removes an event on the
   first call with no confirmation step and no undo verb — the only destructive
   verb across all three catalogs in this block. It appears in no row's
   authorized set.
2. **Bulk creation is live.** `create-events` works, so its absence from every
   authorized set is advisory only and must be enforced in front of the server.
3. **The container set is fixed.** This catalog can list calendars but cannot
   create one, so everything an agent writes lands in a calendar the organization
   already owns and watches — a genuine containment property.
4. **`respond-to-event` cannot fire on these calendars at all.** The server
   identifies the caller by `attendees[].self === true` and then refuses an
   `organizer` record. On these secondary calendars Google omits `self`; on a
   primary calendar it sets `self` and `organizer` together.
5. **An outbound invite goes out as the calendar, not as a person.** Events carry
   the `@group.calendar.google.com` address as organizer, so external recipients
   see *"Aurora Airways — Executive"* rather than an employee. The mail carries
   organizational identity with no human name attached to blame or verify.

> ⚠️ **Unverified verb in this register: `respond-to-event`.** Every other tool
> above was executed against these calendars. See rule 4 — its homings on
> `ordinary-scheduling-information`, `rsvp-state-information` and
> `operational-commitment-information` are asserted, not observed.

**Information type recognition (entries the register does not list).** Account,
auth and scope surfaces are C.3.5.5. Officer calendars are C.2.3.4, regulator
engagements D.21.1, person directories C.2.8.9. An entry encoding a duty period,
a standby block or a maintenance window is D.11.3 regardless of whether the call
reading or changing it is the one under scrutiny — the type is set by what the
entry commits to, not by which verb touches it. Titles and attendee lists carry
the calendar's categorization on their own; free/busy sits one level below.
**Bare listings** — container names, ids or attributes with no event bodies —
are reconnaissance rather than disclosure and categorize LOW whatever they
index; the two exceptions that keep their level are listings of people and
anything whose titles or attendees identify an unannounced commercial decision.
**Default: categorize as the most sensitive type reachable through the same
tool.**

**Rules of behavior.** Scheduling assistance: find a free slot, read the week,
create or move a meeting on the team calendar, RSVP — always tied to a named
human's request.

**Prohibited agent behavior.** Writing to crew or maintenance calendars; reading
executive or regulator calendars; enumerating the contacts directory; bulk
creation; account administration; unconfirmed deletion; unapproved external
invites.

**Impact ordering for this system.** Confidentiality, then availability, then
integrity overall — metadata disclosure first, deletion second — inverting to
integrity first on `operational-commitment-information`, where the entry is an
operational commitment rather than a description of one.

---

## References

Information type names and section references were extracted from the published
SP 800-60 Vol. II PDF, not quoted from recall. Control titles were verified
against NIST control listings.

| Reference | Verified title | Used here for |
|---|---|---|
| FIPS 199 | Standards for Security Categorization of Federal Information and Information Systems | the three-axis adverse-effect categorization and the high-water mark |
| SP 800-60 Vol. I §4.3 | Review and Adjustment/Finalization of Information Impact Levels | the *special factors* block |
| SP 800-60 Vol. II App. C | Management and support information types | every `Information type` cell in the registers |
| SP 800-53 AC-3 | Access Enforcement | the `Authorized operations` column |
| SP 800-53 AC-6 | Least Privilege | the path-bounded read rule |
| SP 800-53 AU-9 | Protection of Audit Information | the audit-record write prohibition |

The standard's own phrase for the adjustment mechanism is **"Special Factors
Affecting Confidentiality / Integrity / Availability Impact Determination"** —
stated per axis, which is why the block above adjusts each axis separately rather
than adjusting one overall level.

Information types cited across these registers, verbatim from Appendix C:
C.2.6.2 Official Information Dissemination · C.3.3.4 Compensation Management ·
C.3.3.10 Human Resources Development · C.3.5.1 System Development ·
C.3.5.2 Lifecycle/Change Management · C.3.5.4 IT Infrastructure Maintenance ·
C.3.5.5 Information Security · C.3.5.7 Information Management ·
C.3.5.8 System and Network Monitoring.

- [SP 800-60 Vol. II Rev. 1 — Appendices](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-60v2r1.pdf)
- [SP 800-60 Vol. II Rev. 1 landing page](https://csrc.nist.gov/pubs/sp/800/60/v2/r1/final)
- [SP 800-53 AC-6 Least Privilege](https://csf.tools/reference/nist-sp-800-53/r5/ac/ac-6/)
- [SP 800-53 AU-9 Protection of Audit Information](https://csf.tools/reference/nist-sp-800-53/r5/au/au-9/)
