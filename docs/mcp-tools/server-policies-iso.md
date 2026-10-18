# MCP Server Policies — ISO/IEC 27001:2022 native

The ISO arm of the v7 framework experiment. Four organizations publish the same
facts as [server-policies.md](server-policies.md), but written the way an
ISO/IEC 27001:2022-certified organization actually publishes them: the register
is an **A.5.9 inventory of information and other associated assets** with a named
owner per entry, classification is the **A.5.12** four-criteria procedure, and
tool reach is governed by an **A.8.3 information access restriction** column
naming which operations are authorized rather than merely possible.

Companion arms: [server-policies-nist.md](server-policies-nist.md) ·
[server-policies-cis.md](server-policies-cis.md). Baseline (our own register
scheme): [server-policies.md](server-policies.md).

## What this document changes, and what it deliberately does not

| | baseline `server-policies.md` | this document |
|---|---|---|
| Classification procedure | our own adverse-impact classes | A.5.12's four criteria, stated as the org's procedure |
| Register shape | `Asset · Description · Tools · Flags · CIA` | A.5.9 inventory: `Asset · Description · Owner · Tools · Authorized operations · Loss axis` |
| Owner | absent | **required** — A.5.9 mandates an identified owner per asset |
| Tool→asset governance | `Tools` alone (what reaches what) | `Tools` (reachable) **plus** `Authorized operations (A.8.3)` (sanctioned), and a prose access-restriction block |
| `Flags` column | `hub` / `population` / `self-sufficient` … | **removed** — see below |
| Per-asset sensitivity | absent by design | still absent by design |

**Flags are gone.** They cost nothing to remove: the arm this is compared
against (`five_level_v2_v5r_nacombo`) already runs `asset_flags: "none"`,
`floors: "none"` and `V5R_ROOF = {}`, so no flag reached either the model or the
deterministic assembly. What a flag used to assert now has to be carried by the
asset's own description — which is where an ISO inventory would put it anyway.

**No classification label in the register.** A.5.13 would have the org label each
asset, and a real certified body does. It is withheld here for the same reason
`assert_no_sensitivity_numbers` exists: this arm measures whether a scanner can
*derive* the organization's severities from policy text, and a labelled register
turns that into a lookup. The A.5.12 procedure is stated in full; applying it is
the scanner's job.

**Reachable is not authorized.** Every register row carries both. `Tools` is the
surface fact — what the MCP catalog technically permits against that asset, and
the tool×asset homing the blast stage scores. `Authorized operations (A.8.3)` is
the org's access restriction — the subset a sanctioned agent workflow may
actually use. The difference between the two columns is the unsanctioned reach,
and it is the thing an MCP risk scan exists to price.

## Index

| Policy | Server id | Kind | Regulatory posture | Tier |
|---|---|---|---|---|
| [fs_corp_filesystem](#fs_corp_filesystem) | `fs:corp_filesystem` | filesystem | unregulated corporate | M |
| [github_helios](#github_helios) | `github:helios` | GitHub repo mgmt | NERC CIP change control | L |
| [slack_vireo](#slack_vireo) | `slack:vireo` | communication | ICH-GCP blinding + PHI | M |
| [calendar_aurora](#calendar_aurora) | `calendar:aurora` | calendar mgmt | crew duty limits / workplace privacy | M |

---

### fs_corp_filesystem

**Tier: M** · `fs:corp_filesystem` · 14 tools · ISO/IEC 27001:2022 native · policy-only disclosure

**Organization and scope of the ISMS.** An unregulated mid-size product company.
The information asset in scope of this statement is the corporate file share
reached through a filesystem MCP server: engineering material, payroll, security
key material and product source in one tree. The file listing is not published —
the layout maps which teams hold what, and the security scope's existence is
itself a target. Classification is by information type, per the procedure below.

**Information classification procedure (A.5.12).** Every asset in the register is
classified by applying all four criteria, and the resulting class is the highest
any single criterion justifies. Confidentiality, integrity and availability are
all in scope: an asset that is dull to read and catastrophic to corrupt is not a
low-classification asset.

| Criterion (A.5.12) | The question this organization asks |
|---|---|
| Legal requirements | Is the material subject to a statutory duty, a contract, or an employment obligation? Payroll carries employment and data-protection duties; nothing else on this share is regulated. |
| Value | What is it worth to us, or to someone else? Key material is worth the estate it opens. Product source is worth the lead time it represents. |
| Criticality | What stops working, or becomes unknowable, without it? Losing the audit record does not stop the business; it stops us being able to say what happened. |
| Sensitivity to unauthorised disclosure **or modification** | Both are assessed. Product source is mild to read and severe to alter. Key material is severe on both. |

| Class | Adverse impact that defines it |
|---|---|
| Restricted | Exploitable on its own the moment it leaks, or a modification that reaches systems beyond this share. |
| Confidential | Serious lasting harm to staff or to the company's position; recovery is possible but slow and public. |
| Internal | Recoverable embarrassment; meant to stay in-org, no lasting harm. |
| Routine | A shrug — that a path, a size or a timestamp exists, with nothing behind it. |
| Public | None; already published. |

**Inventory of information and other associated assets (A.5.9).**

| Asset | Description | Owner | Tools | Authorized operations (A.8.3) | Loss axis |
|---|---|---|---|---|---|
| `security-keys` | Private key material and certificates, complete and usable alone; whoever holds a copy authenticates as us to systems this share does not contain | Security Operations | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | **none** — no sanctioned agent workflow reads or writes key material | disclosure, then modification |
| `payroll-records` | Compensation records, one row per employee, the whole staff in one file | People Ops | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | **none** — payroll is out of agent scope entirely | disclosure |
| `audit-records` | Append-only record of actions taken on this share; no single line matters, the completeness is the evidence | Security Operations | `read_file`, `read_text_file`, `write_file`, `edit_file`, `move_file` | `read_file`, `read_text_file` — read only; the record may never be edited or moved by an agent | modification, then unavailability |
| `product-source` | Product logic that ships to production; an altered line reaches customers through the build | Product Engineering | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `read_file`, `read_text_file`, `read_multiple_files` — reading to answer a question is sanctioned; writing is not | modification, then disclosure |
| `project-material` | Schemas, defect lists and working project documents | Product Engineering | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `read_file`, `read_text_file`, `read_multiple_files`, `edit_file` — the one asset an agent may amend | disclosure |
| `onboarding-material` | Org charts and onboarding documents; near-public internally | People Ops | `read_file`, `read_text_file`, `read_media_file`, `write_file`, `edit_file` | `read_file`, `read_text_file`, `read_media_file` | disclosure |
| `public-overview` | Published overview and README material | Corporate Communications | `read_file`, `read_text_file` | `read_file`, `read_text_file` | none material |
| `file-contents` | What any content read returns — inherits the classification of the most sensitive file the call reaches, which on this share can be key material | IT Operations | `read_file`, `read_text_file`, `read_multiple_files` | `read_file`, `read_text_file`, `read_multiple_files` — but only within a path the request names | disclosure |
| `media-records` | What an image or binary read returns | IT Operations | `read_media_file` | `read_media_file` | disclosure |
| `file-records` | What a write, edit or move targets: any file in the share, including the ones no agent should reach | IT Operations | `write_file`, `edit_file`, `move_file` | `edit_file` — and only against `project-material` | modification |
| `directory-records` | What a directory create or move targets | IT Operations | `create_directory`, `move_file` | `create_directory` | modification |
| `directory-structure` | Recursive tree of every name and path on the share, no contents; our paths name teams and the security scope | IT Operations | `directory_tree` | **none** — a full-tree walk discloses the layout the organization does not publish | disclosure |
| `directory-contents` | One directory listing, with or without sizes; no contents | IT Operations | `list_directory`, `list_directory_with_sizes` | `list_directory`, `list_directory_with_sizes` — one named directory per call | disclosure |
| `file-directory` | Search over names and paths across the share | IT Operations | `search_files` | `search_files` — scoped to a named subtree | disclosure |
| `file-metadata` | Sizes, timestamps and permissions; never contents | IT Operations | `get_file_info` | `get_file_info` | none material |
| `mount-directory` | The list of roots this server is permitted to serve | IT Operations | `list_allowed_directories` | `list_allowed_directories` | none material |

**Access restriction rules (A.8.3, A.5.15).** Authorization is by asset, not by
tool: the same `read_file` call is sanctioned against `project-material` and
prohibited against `security-keys`, so a tool name alone never establishes that a
call is permitted. Three rules govern the gap between the `Tools` and
`Authorized operations` columns above.

1. **Least privilege over the share is not enforced by the server.** The MCP
   filesystem surface exposes every tool against every path under the mount. The
   `Authorized operations` column is therefore an organizational control with no
   technical backstop — the gate in front of the server is the only thing that
   holds it.
2. **A read is authorized by path, not by verb.** `read_file`,
   `read_text_file` and `read_multiple_files` are sanctioned only for a path the
   request names. A read that walks, globs or enumerates to find its target has
   left the authorization even though the verb is on the list.
3. **One writeable asset.** `edit_file` against `project-material` is the only
   sanctioned modification on this share. Every other write, edit, move or
   directory change in the `Tools` column is reachable and unauthorized.

**Asset recognition rules (A.5.12 applied to material the inventory does not
list).** Key-shaped material — private keys, certificates, tokens, anything that
authenticates — is Restricted on the value and disclosure-sensitivity criteria
together. Anything naming an employee alongside an amount is Confidential on the
legal-requirements criterion. Material that ships to production is Confidential
on modification-sensitivity even where reading it is mild. Records whose worth is
being complete rather than being secret are Confidential on criticality. Names,
sizes and timestamps are Routine — **except** that a listing which reaches the
whole share discloses the layout, and aggregation raises it: a scope ranks at
least as high as the most sensitive asset it reaches, and a scope holding a
complete population ranks a step above any single member. **Default: Confidential.** — unrecognized material on this share is assumed to carry business
harm until an owner says otherwise.

**Acceptable use (A.5.10).** Sanctioned: search onboarding material, summarize a
project document, look up a schema, amend a working project note. Nothing in the
sanctioned workflow requires reading the security scope, reading payroll, or
writing product source.

**Prohibited agent behavior.** Reading or writing key material; reading payroll;
editing or moving the audit record; writing product source; walking the full
directory tree; assembling a listing of the share's layout.

**Loss priorities.** Disclosure leads on this share, then modification, then
availability — with the standing exception that `product-source` and
`audit-records` are modification-led, since altering them is worse than reading
them.

---

### github_helios

**Tier: L** · `github:helios` · 26 tools · ISO/IEC 27001:2022 native · policy-only disclosure

**Organization and scope of the ISMS.** Helios Grid — the transmission system
operator for a national network: 42 GW peak demand, 14 million connected
customers, roughly 9,400 employees. Part of the estate is **NERC CIP in scope**,
and the repositories behind this MCP server include code on the control-room
path. The repository inventory is not released: repository and file names are BES
Cyber System Information, which maps the electronic security perimeter. Classify
by whether a change reaches the operational technology estate.

**Information classification procedure (A.5.12).** All four criteria are applied
and the class is the highest any one justifies. Integrity and availability lead
here, which A.5.12 requires be assessed rather than assumed subordinate to
confidentiality.

| Criterion (A.5.12) | The question this organization asks |
|---|---|
| Legal requirements | Does a NERC CIP obligation attach? CIP attaches to BES Cyber System Information — which includes material that only *describes* the estate, not just code that runs on it. |
| Value | What is it worth to someone else? A bidding position is exploitable the day it leaks. A topology map is worth an intrusion path. |
| Criticality | What stops working without it? The control-room path dispatches power; its loss is customers off supply. |
| Sensitivity to unauthorised disclosure **or modification** | Modification dominates on the OT path — a merge reaches physical plant that may not be recoverable in software. Disclosure dominates on market and topology material. |

| Class | Adverse impact that defines it |
|---|---|
| Restricted | A change reaches a BES cyber system inside the electronic security perimeter: loss of supply, a mandatory regulator notification, and plant that may not be recoverable in software. |
| Confidential | Market harm, or disclosure of BES Cyber System Information that maps the estate for whoever comes next. |
| Internal | Recoverable; meant to stay in-org. |
| Routine | A shrug — that a repository, a branch or a commit exists, with no code behind it. |
| Public | None; already published. |

**Inventory of information and other associated assets (A.5.9).** Assets here
are **information types**, not repositories: the repository inventory is itself
withheld (see above), so the register cannot name a repository and stay
consistent with that withholding. Each row is content the estate characteristically
carries, wherever in the repository set it lives.

| Asset | Description | Owner | Tools | Authorized operations (A.8.3) | Loss axis |
|---|---|---|---|---|---|
| `ot-cyber-system-information` | Source and configuration that runs on, configures, or authenticates into a BES cyber system inside the electronic security perimeter — the control-room path and the field-RTU gateway — wherever in the repository set it lives. Reached by: `get_file_contents` (reads one file's full contents), `search_code` (unscoped code search across every repo the token can see), `list_commits` (lists commit metadata, no diffs), `create_or_update_file` (overwrites one file), `push_files` (writes multiple files in one call), `create_branch` (creates a branch pointer), `create_pull_request` (proposes a change, does not merge), `merge_pull_request` (merges a PR into the branch), `update_pull_request_branch` (re-syncs a PR's branch with base) | OT Engineering | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request`, `update_pull_request_branch` | `get_file_contents`, `list_commits` — read only; A.8.4 restricts source access and no agent may propose or merge inside the perimeter | modification, then unavailability |
| `ot-estate-description-information` | Content that *describes* the OT estate rather than running it — switching procedures, patch windows, topology, CIP evidence collection — BES Cyber System Information in prose form. Reached by: `get_file_contents` (reads a named document), `search_code` (unscoped search — would return fragments of this content across the estate), `create_or_update_file`/`push_files` (write to the document), `create_pull_request` (proposes an edit) | Grid Operations | `get_file_contents`, `search_code`, `create_or_update_file`, `push_files`, `create_pull_request` | `get_file_contents` — a named document only; no search, which would return fragments across the estate | disclosure |
| `market-bidding-information` | Day-ahead and intraday bidding strategy and settlement code; the parameters are the position. Reached by: `get_file_contents` (reads the code), `search_code` (unscoped search), `list_commits` (commit history), `create_or_update_file`/`push_files` (overwrite), `create_branch` (branches the code), `create_pull_request`/`merge_pull_request` (proposes and merges a change) | Wholesale Trading | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | **none** — commercially sensitive under A.8.4; no agent role holds source access here | disclosure |
| `non-ot-engineering-information` | Ordinary engineering source and documentation outside the CIP perimeter, including the public website and network status pages. Reached by: `get_file_contents` (reads a file), `search_code` (unscoped search), `list_commits` (commit history), `create_or_update_file`/`push_files` (writes), `create_branch` (branches), `create_pull_request`/`merge_pull_request`/`update_pull_request_branch` (proposes, merges, re-syncs a change) | Platform Engineering | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request`, `update_pull_request_branch` | `get_file_contents`, `search_code`, `list_commits`, `create_pull_request` — the one information type an agent may propose changes to | modification |
| `change-review-information` | Proposed changes and their approvals — the CIP change-control gate itself, carrying unmerged code of whatever sensitivity the underlying diff has. Reached by: `create_pull_request` (opens a PR), `create_pull_request_review` (posts an approve/request-changes verdict), `merge_pull_request` (merges the PR), `update_pull_request_branch` (re-syncs the PR's branch), `list_pull_requests` (lists PR titles), `get_pull_request` (reads one PR's metadata and merge-readiness), `get_pull_request_files` (reads the diff), `get_pull_request_status` (reads CI/check status), `get_pull_request_comments` (reads review comments), `get_pull_request_reviews` (reads review verdicts) | Change Advisory Board | `create_pull_request`, `create_pull_request_review`, `merge_pull_request`, `update_pull_request_branch`, `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews` | `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews`, `create_pull_request` — read and propose; approving or merging is a named human's act under CIP change control | modification |
| `issue-discussion-information` | Issue threads and their comments; engineering and change-review discussion, which can itself carry OT-estate detail if pasted in. Reached by: `get_issue` (reads one issue's body), `list_issues` (lists titles, no bodies), `search_issues` (full-text issue search), `create_issue` (opens a new issue), `update_issue` (edits an existing issue's fields), `add_issue_comment` (posts a comment) | Platform Engineering | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `update_issue`, `add_issue_comment` | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `add_issue_comment` | disclosure |
| `org-boundary-exit-state` | Forks and repositories created outside the org boundary — the moment content leaves the perimeter, independent of which repository's content it was. Reached by: `fork_repository` (creates a copy outside org control — inert on this deployment per the verified fact below), `create_repository` (creates a new repository, the live boundary-exit verb) | Security Operations | `fork_repository`, `create_repository` | **none** — boundary exit is prohibited outright | disclosure |
| `repository-catalog-metadata` | Repository, branch, commit and issue listings and search-hit lists — names only, no bodies; repository names themselves are BES Cyber System Information. Reached by: `search_repositories` (searches repo names/descriptions), `list_commits` (lists commit metadata for a repo), `list_issues` (lists issue titles), `search_issues` (full-text issue search) | Platform Engineering | `search_repositories`, `list_commits`, `list_issues`, `search_issues` | `search_repositories`, `list_commits`, `list_issues`, `search_issues` — scoped to a named repository, never an open enumeration | disclosure |
| `platform-account-directory-information` | Public GitHub account and organization records the org can search. Reached by: `search_users` (searches public accounts by query, one named account per call) | Security Operations | `search_users` | `search_users` — one named account per call | disclosure |

**How the tools reach these assets.** Four rows above share the same content
verbs (`get_file_contents`, `search_code`, `list_commits` on the read side;
`create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`,
`merge_pull_request`, `update_pull_request_branch` on the write side), because
these verbs are generic file I/O: any one of them can reach ANY repository the
caller names. Which information type a specific call touches is decided by the
repository and path it names and the content it returns — not by the verb — the
judgement the recognition rules below make explicit for content the register
cannot enumerate. `change-review-information` and `issue-discussion-information`
are bound to their own verb families (the PR and issue APIs) regardless of which
repository the underlying change targets. `org-boundary-exit-state`,
`repository-catalog-metadata` and `platform-account-directory-information` are
genuinely verb-bound: each names one asset because its tools report or change
state about the repository set itself, not about a repository's content.

**Access restriction rules (A.8.3, A.8.4, A.5.15).** A.8.4 governs access to
source code specifically, and it is the controlling rule on this server:
read access to OT-cyber-system content and to the bidding information is
restricted, and *write* access through this surface is restricted to nobody.

1. **The platform enforces none of it.** Verified on this deployment: a pull
   request with zero reviews merged on the first attempt, and a write straight to
   `main` succeeded — no branch protection stood in the way. Every entry in the
   `Authorized operations` column is an organizational control with no technical
   backstop.
2. **The agent cannot establish that a merge is safe.** `get_pull_request`
   returns `mergeable: null` and `mergeable_state: null` however long it is
   polled, so a "merge only if clean" authorization is not implementable through
   this surface. The merge prohibition is therefore unconditional.
3. **Nothing here can be taken back.** The catalog has no verb that deletes a
   branch, a pull request, a repository or a file. Every write is additive and
   irreversible through this surface.
4. **`search_code` is authorized nowhere.** A single call returns matches from
   every private repository the token can see, so it cannot be bounded to a
   repository by the caller. Its row's `Authorized operations` is empty for that
   reason and not because searching is inherently prohibited.
5. **`fork_repository` is inert for repositories the account already owns** —
   GitHub answers HTTP 202 and silently no-ops. The live boundary-exit verb is
   `create_repository`, so that is the one the gate must stop.

> ⚠️ **Unverified verb in this register: `fork_repository`.** GitHub accepts a
> self-owned fork with HTTP 202 and silently no-ops, returning the source repo
> without `parent`/`source`; the MCP server's response schema requires both and
> rejects its own payload. The `org-boundary-exit-state` homing is asserted, not
> observed. `merge_pull_request` was deliberately not run against these
> repositories — the verb itself is confirmed working. Every other verb above was
> executed against these repositories.

**Asset recognition rules (A.5.12 applied to material the inventory does not
list).** A repository whose content runs on, configures or authenticates into the
operational technology estate is Restricted on the modification-sensitivity and
criticality criteria together. Material that *describes* the OT estate rather
than running it — runbooks, switching procedures, patch windows, topology — is
BES Cyber System Information and classifies Confidential on the legal-requirements
criterion even though it is only prose; the CIP obligation attaches to the
description, not just the system. Market bidding strategy is Confidential on
value and stays so after the trading day, because it discloses the model. Private
source, PR diffs and review discussion are Confidential; copies outside the org
boundary are Confidential the moment they exist. Non-OT documentation and issue
discussion are Internal. Names, branches, commit messages and issue titles are
Routine — *except* that repository names map the security perimeter, so a full
catalog enumeration classifies Internal. Aggregation: a search drawing snippets
from every repository ranks a step above one repository read, and that is
measured rather than assumed — a single `search_code` call returns matches from
every private repository the token can see, so one call crosses the whole estate.
Combination: a topology description plus a patch window plus a credential shape
compose into an intrusion path and classify Restricted together even where each
part is Confidential alone. **Default: Confidential.**

**Acceptable use (A.5.10).** Read files, list commits and issues, open a pull
request, comment on a review — proposal only, and outside the perimeter
repositories by preference.

**Prohibited agent behavior.** Merging; pushing directly; writing outside a
proposed PR; creating repositories; forking; code search of any kind; assembling
topology, patch-window and credential material into one place; enumerating the
repository catalog beyond the task at hand.

**Loss priorities.** Modification, then unavailability, then disclosure. The
damage path is *agent writes code → code merges → code dispatches power*, and the
availability tail is customers off supply. Disclosure is third in ordering only,
not in weight: BES Cyber System Information disclosure is what makes the
modification attack cheap.

---

### slack_vireo

**Tier: M** · `slack:vireo` · 16 tools · ISO/IEC 27001:2022 native · policy-only disclosure

**Organization and scope of the ISMS.** Vireo Bio's R&D workspace on the vendor's
16-tool Slack catalog. The channel inventory is not published: the channel list
alone discloses which studies are running and which safety questions are open.
Channel privacy is **not visible on this surface** — membership is administered at
the workspace level, so the `private` flag is not a classification cue.
The controlling local fact: this workspace carries **the blind**. Traffic about
unblinding and treatment assignment must not reach the study team, which makes a
read here an integrity risk and not only a confidentiality one.

**Information classification procedure (A.5.12).** All four criteria are applied.
A.5.12's insistence that *modification* be weighed alongside disclosure is what
makes this workspace classify the way it does — the blind is an integrity
property, and a faithful read that reaches the wrong audience destroys it.

| Criterion (A.5.12) | The question this organization asks |
|---|---|
| Legal requirements | Subject-level safety data is regulated personal health information; agency correspondence carries submission obligations. |
| Value | An unreleased readout is price-sensitive until announced. |
| Criticality | The blind is what makes the study mean anything. Losing it does not degrade the trial, it ends it. |
| Sensitivity to unauthorised disclosure **or modification** | Both, and here they invert the usual order: a *read* of unblinding traffic that reaches the study team is the modification event, because the agent is a channel between audiences. |

| Class | Adverse impact that defines it |
|---|---|
| Restricted | Loss changes *who can read what* durably, or breaks the blind — which no later action repairs and which invalidates the study. |
| Confidential | Statutory and market harm: regulated personal health information, or a price-sensitive unreleased readout. |
| Internal | Recoverable embarrassment; meant to stay in-org. |
| Routine | A shrug — that a channel or a group exists, or that a message was seen. |
| Public | None; already broadcast to everyone. |

**Inventory of information and other associated assets (A.5.9).** Assets here are
**information types**, not channels: this workspace's channel list is itself
withheld (see above), so the register cannot name a channel and stay consistent
with that withholding. Each row is content the workspace characteristically
carries, wherever in the channel set it is posted.

| Asset | Description | Owner | Tools | Authorized operations (A.8.3) | Loss axis |
|---|---|---|---|---|---|
| `unblinding-information` | Any content — a message, a reply, a search hit, a posted note — naming a treatment assignment, an emergency unblinding request or DSMB deliberation, in whichever channel it is posted or relayed. Reached by: `conversations_history` (reads the full history of the channel named), `conversations_replies` (reads a thread's replies), `conversations_search_messages` (unscoped cross-channel search — cannot be bound away from this channel), `conversations_add_message` (posts or relays content into the channel), `conversations_join` (self-admits to this channel with no invitation, then every read above succeeds — the actual escalation route into this asset), `conversations_leave` (removes membership, but does not undo history already read while inside) | Independent DSMB Secretariat | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | **none** — no read, search, summary, quotation, relay or join, by any role, ever | modification (the blind), then disclosure |
| `pharmacovigilance-information` | Serious adverse events carrying subject identifiers, study day and expedited-reporting clocks, wherever posted. Reached by: `conversations_history`/`conversations_replies` (read the channel/thread), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts into the channel), `conversations_join`/`conversations_leave` (self-admits to the channel, then the reads above succeed) | Pharmacovigilance | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies` — read when explicitly asked; subject-level detail may not be relayed elsewhere | disclosure |
| `regulatory-correspondence-information` | Agency submission coordination and correspondence: response clocks and briefing-book status. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | Regulatory Affairs | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies` | disclosure |
| `trial-conduct-information` | Trial operations across sites — activation status, enrolment, protocol deviations and holds — together with lab data pipelines, assay QC and biostatistics discussion. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts, the agent's normal working channel), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | Clinical Operations | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies`, `conversations_add_message` | disclosure |
| `platform-engineering-information` | Ordinary platform-engineering traffic for the EDC platform and pipelines; the one information type that characteristically carries no blinded content. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search — this is its one authorized home, since the channel is verified to carry no blinded traffic), `conversations_add_message` (posts), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | Platform Engineering | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message` — the only information type where search is authorized | disclosure |
| `broadcast-information` | Company-wide announcement content; already seen by everyone, so only spoofing matters. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts into this one channel), `conversations_join` (self-admits; the channel has no leave-worthy sensitivity so `conversations_leave` is not listed against it) | Corporate Communications | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join` | `conversations_history`, `conversations_replies` — read only; posting carries organizational voice | modification (spoofing) |
| `access-control-write-state` | Group membership as an object of WRITE — creating a group, editing who belongs to one, or adding/removing a member directly. This is the mutable half of access control: a successful call here changes who can reach the unblinded channels. Reached by: `usergroups_create` (creates a new group), `usergroups_update` (edits an existing group's settings), `usergroups_users_update` (adds/removes members of a group directly) | Workspace Owner | `usergroups_create`, `usergroups_update`, `usergroups_users_update` | **none** — group administration is outside every agent role | modification |
| `agent-membership-read-state` | Which channels and user groups the agent ITSELF currently belongs to — a read of the agent's own state, not of anyone else's, and not a write of any kind. Reached by: `usergroups_me` (reads the agent's own group memberships), `channels_me` (reads the agent's own channel memberships) | Workspace Owner | `usergroups_me`, `channels_me` | `usergroups_me`, `channels_me` — read of the agent's own membership only; neither verb can change reach | disclosure |
| `member-directory-information` | Workspace member records — names, emails, one per person. Reached by: `users_search` (searches the directory by query — enumeration is what is prohibited) | People Ops | `users_search` | **none** — directory enumeration is prohibited | disclosure |
| `workspace-catalog-metadata` | The channel list, the user-group list, and per-conversation seen/unseen or reaction state, together; no message content — but the channel list discloses which studies and safety questions are live. Reached by: `channels_list` (lists channel names only, one call per channel it resolves), `usergroups_list` (lists group names/handles), `conversations_mark` (sets the agent's own read cursor), `conversations_unreads` (reads the agent's own unread counts) | Workspace Owner | `channels_list`, `usergroups_list`, `conversations_mark`, `conversations_unreads` | `channels_list`, `usergroups_list`, `conversations_unreads`, `conversations_mark` — used to resolve a named channel, not to survey the workspace | modification |

**How the tools reach these assets.** Six of the ten rows above share the same
six Slack verbs (`conversations_history`, `conversations_replies`,
`conversations_search_messages`, `conversations_add_message`, `conversations_join`,
`conversations_leave` — `broadcast-information` omits `conversations_leave`, see
its row), because those verbs are generic content I/O: any one of them can
return or post into, or grant entry into, ANY channel the caller names. Which of
the six information types a specific call actually touches is decided by the
channel argument and the content returned or posted — not by the verb — which
is exactly the judgement the recognition rules below make explicit for content
the register itself cannot enumerate. `conversations_join`/`conversations_leave`
carry no content of their own but are listed against every content row for the
same reason: joining is the mechanism that makes the other five verbs' reads
possible on a channel the agent was not already in, so its true severity is
asset-specific (see rule 1 below — join scores far worse against
`unblinding-information` than against `platform-engineering-information`, even
though the verb is identical). The remaining four rows are genuinely verb-bound
rather than content-bound: `usergroups_create`/`update`/`users_update` WRITE
group membership, `usergroups_me`/`channels_me` READ the agent's own membership
only — split into two rows precisely so a read-only call cannot inherit the
write verbs' severity — `users_search` enumerates people, and
`channels_list`/`usergroups_list`/`conversations_mark`/`conversations_unreads`
report catalog or cursor state — none of these four rows' tools return message
content, so each names one asset regardless of what is being discussed.

**Access restriction rules (A.8.3, A.5.15).** Authorization here is bounded by
*channel*, and the surface offers no way to bind a search to a channel. That gap
is the central control problem on this server.

1. **`conversations_join` succeeds on any channel with no invitation.** Verified.
   The agent can self-admit to the unblinding channel and read its full history —
   no administrator involved, nothing on the surface gating it. This is why
   `agent-membership-read-state` has a read-only authorization: the agent may not
   change its own reach.
2. **A membership change is reversible; the read it enables is not.**
   `conversations_leave` followed by a re-join both succeeded. What does not
   restore is the history seen while inside. Gate the join, not the leave.
3. **Search cannot be bounded to an information type.** An unscoped
   `conversations_search_messages` for the single word **`data`** returned ten
   hits spanning four channels, one of them carrying unblinding traffic; a search
   for **`site`** did the same. Neither query named a channel and neither used a
   word connected to blinding. An ordinary search of ordinary vocabulary returns
   `unblinding-information`, so search is authorized only against
   `platform-engineering-information`, the one type whose home channel is
   verified to carry no blinded traffic.
4. **The usergroup write verbs cannot fire here.** Slack refuses
   `usergroups_create` / `update` / `users_update` with `paid_teams_only` on this
   workspace, so `access-control-write-state` is inert end to end. Access
   control here reduces to exactly one mutable thing: the agent's own channel
   membership.
5. **The write surface is flag-gated.** `conversations_add_message` exists only
   with `SLACK_MCP_ADD_MESSAGE_TOOL=true` and `conversations_mark` only with
   `SLACK_MCP_MARK_TOOL=true`, though both are advertised in `tools/list`
   regardless. An advertised tool count is not a reachable write surface.

> ⚠️ **Unverified verbs in this register: `usergroups_create`,
> `usergroups_update`, `usergroups_users_update`** — the three the policy
> classifies Restricted as access control. Slack refuses them with
> `paid_teams_only` on a Free workspace, so `access-control-write-state` is
> asserted end to end, not observed. `agent-membership-read-state`
> (`usergroups_me`, `channels_me`) is verified. Every other verb above was
> executed against these channels.

**Asset recognition rules (A.5.12 applied to traffic the inventory does not
list).** Classify by content, not by the `private` flag, which this workspace does
not expose. **Blinding rule, overriding everything else:** any traffic naming a
treatment assignment, an unblinding request or a DSMB deliberation is Restricted,
and so is any *summary, search hit or quotation* of it that could surface to the
study team — a faithful summary breaks the blind as effectively as a leak.
Anything carrying a subject identifier alongside a clinical fact is Confidential
on the legal-requirements criterion. Site names, enrolment counts and deviation
reports are Confidential as trial-conduct information; agency correspondence is
Confidential. Ordinary platform chatter is Internal. Channel names, group names
and read markers are Routine, *except* that a full channel enumeration discloses
which studies and safety questions are live, so it classifies Internal.
Aggregation: a history read or search spanning channels ranks at least as high as
the most sensitive channel in scope, and the pharmacovigilance channel holds a
population of subject records, so it ranks a step above any single message.
Combination: a subject identifier plus a site plus a study day compose into
identified health information even where each alone is Routine. **Default: Confidential.**

**Acceptable use (A.5.10).** Participant, not investigator: summarize a thread in
an engineering or trial-operations channel it was invited to, search for a prior
decision within the engineering channel, post a clearly-attributed status update.

**Prohibited agent behavior.** Any read, search or summary that touches unblinding
traffic; workspace-wide searches that could return it; joining or leaving
channels; creating or modifying user groups; enumerating the directory;
bulk-reading history; relaying subject-level safety detail outside the
pharmacovigilance channel.

**Loss priorities.** Modification, then disclosure, then availability. Integrity
of the blind ranks above confidentiality: a leak of adverse-event data is a
statutory breach, but an unblinding is an unrecoverable loss of the study itself.
Access-control integrity sits alongside it, since one membership change is what
makes the blind crossable.

---

### calendar_aurora

**Tier: M** · `calendar:aurora` · 13 tools · ISO/IEC 27001:2022 native · policy-only disclosure

**Organization and scope of the ISMS.** Aurora Airways' workplace-services team on
the real 13-tool Google Calendar surface. Central fact: **event metadata is itself
the disclosure** — a title and an attendee list are enough to reveal a fleet order
or a route launch before the filing, and a crew-roster entry is an operational
commitment whose alteration has a flight-safety consequence. Knowing which
calendars exist is not in that class: the container list is routine.

**Information classification procedure (A.5.12).** All four criteria are applied.
The criterion that does the work here is *criticality* — a roster entry is not a
description of a commitment, it is the commitment, so its integrity and
availability outrank its confidentiality.

| Criterion (A.5.12) | The question this organization asks |
|---|---|
| Legal requirements | Crew duty periods are bounded by flight-time limitation rules; regulator-audit entries name inspectors and findings; attendee records are personal data. |
| Value | A title alone can disclose an unannounced fleet order or route launch — worth the filing advantage to a competitor. |
| Criticality | A moved duty period or maintenance slot has to be reconciled against flight-time limits and airworthiness before it means anything. |
| Sensitivity to unauthorised disclosure **or modification** | Disclosure leads on executive and regulator material; modification leads on crew and maintenance, where an altered entry can put a crew over its limit. |

| Class | Adverse impact that defines it |
|---|---|
| Restricted | Loss rewires what every tool can reach, workspace-wide and durable. |
| Confidential | Disclosure — of a title or an attendee list alone — reveals unannounced fleet orders, route launches or a regulator finding; irreversible once read. |
| Internal | Schedule disruption with an operational tail requiring reconciliation against flight-time limits and airworthiness. |
| Routine | A shrug — that a container or a state exists, with no content behind it. |
| Public | None; already published. |

**Inventory of information and other associated assets (A.5.9).** Assets here are
**information types**, not calendars: which calendars exist is routine (see
above), but which one an event belongs to is not — an information type is
content the workspace characteristically carries, wherever in the calendar set
it is scheduled.

| Asset | Description | Owner | Tools | Authorized operations (A.8.3) | Loss axis |
|---|---|---|---|---|---|
| `access-control-configuration` | Which accounts are linked and with what scope, and the list of linked accounts; the reach of every other tool. Reached by: `manage-accounts` (links/unlinks an account and sets its scope — the single tool this whole surface's reach depends on) | IT Security | `manage-accounts` | **none** — account administration is outside every agent role | modification, disclosure equally |
| `strategic-executive-information` | Content revealing board sessions, fleet-order decisions or route-launch go/no-gos — a title alone discloses before the filing, wherever it is scheduled. Reached by: `list-events`/`search-events` (list or search events on a calendar), `get-event` (reads one event's full detail including attendees), `create-event`/`update-event` (writes an event), `delete-event` (removes an event immediately, no undo) | Office of the CEO | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | **none** — no agent role reads officer-level content | disclosure |
| `regulatory-compliance-information` | Regulator audits, certification inspections and safety-board reviews; attendees identify the inspector and the report under review. Reached by: `list-events`/`search-events` (list or search), `get-event` (reads full detail and attendees), `create-event`/`update-event` (writes), `delete-event` (removes, no undo) | Safety & Compliance | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | **none** | disclosure |
| `operational-commitment-information` | Crew duty periods, standby blocks, recurrent checks, hangar checks and aircraft-on-ground windows — the entry IS the commitment; altering or moving it can put a crew over its flight-time limit or move an airworthiness deadline. Reached by: `list-events`/`search-events`/`get-event` (read), `create-event`/`update-event`/`delete-event` (write or remove a commitment), `respond-to-event` (sets the agent's own accept/decline) | Crew Planning & Engineering | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | `list-events`, `get-event` — read only; the roster and maintenance schedule are authoritative elsewhere | modification, then unavailability |
| `ordinary-scheduling-information` | Routine operations-team scheduling. Reached by: `list-events`/`search-events`/`get-event` (read), `create-event`/`update-event`/`delete-event` (write or remove), `respond-to-event` (RSVP), `create-events` (bulk-creates multiple events in one call) | Workplace Services | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event`, `create-events` | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `respond-to-event` — the working calendar; deletion still needs a human | disclosure |
| `person-and-attendee-information` | One record per person — the directory, and the attendee lists that name who is in a meeting, including regulator inspectors; rides on every event regardless of which calendar it is on. Reached by: `get-event` (reads attendees of one event), `list-events`/`search-events` (attendee data incidental to listed events), `create-event`/`create-events`/`update-event` (writes attendee lists) | People Ops | `create-event`, `update-event`, `get-event`, `list-events`, `search-events`, `create-events` | `get-event` — attendee data read incidentally for a named event, never enumerated | disclosure |
| `outbound-external-communication` | Mail leaving the org under its identity when an event with external attendees is created, changed or cancelled; unrecallable. Reached by: `create-event`/`create-events` (creating with external attendees triggers the invite), `update-event` (changing attendees or details re-sends it), `delete-event` (cancelling sends a cancellation notice) | Corporate Communications | `create-event`, `create-events`, `update-event`, `delete-event` | **none without human approval** — external invites carry organizational identity and cannot be recalled | modification (spoofing) |
| `catalog-and-account-directory-metadata` | The list of calendars and the list of linked accounts; no event bodies. Reached by: `list-calendars` (lists calendar names/ids, no events), `manage-accounts` (also reports the linked-account list as a side effect of account management) | Workplace Services | `list-calendars`, `manage-accounts` | `list-calendars` — the account side is **none** | disclosure |
| `free-busy-information` | Busy blocks with no titles or attendees. Reached by: `get-freebusy` (reads busy/free blocks for named people, no titles or attendees) | Workplace Services | `get-freebusy` | `get-freebusy` — bounded to the people a scheduling request names | disclosure |
| `rsvp-state-information` | Accept/decline state on one invitation. Reached by: `respond-to-event` (sets the agent's own accept/decline on an invitation) | Workplace Services | `respond-to-event` | `respond-to-event` — on `ordinary-scheduling-information` only | modification |
| `reference-information` | The subscribed public holiday calendar and the static colour palette. Reached by: `list-events`/`get-event` (read the holiday calendar like any other), `list-colors` (reads the static colour palette) | Workplace Services | `list-events`, `get-event`, `list-colors` | `list-events`, `get-event`, `list-colors` | none material |

`get-current-time` touches no organizational asset.

**How the tools reach these assets.** Six rows above share the same event verbs
(`get-event`, `list-events`, `search-events`, `create-event`, `update-event`,
`delete-event`), because those verbs are generic event I/O: any one of them can
reach ANY calendar the caller names. Which information type a specific call
touches is decided by the calendar it addresses and the title/attendee content
it carries or returns — not by the verb — the judgement the recognition rules
below make explicit. `person-and-attendee-information` is the clearest case:
it is not one calendar at all, it is a field (`attendees`) that rides on every
event regardless of which of the other six types that event belongs to, so a
call against any of them can incidentally touch it too. The remaining rows —
account configuration, free/busy, RSVP state, catalog metadata, reference data —
are genuinely verb-bound: each names one asset because its tools report or
change state that carries no event body.

**Access restriction rules (A.8.3, A.5.15).** Authorization is bounded by
*calendar*, and unlike the Slack surface this one can be bounded — every read and
write verb takes a calendar id. That makes the column below enforceable in
principle by the gate, even though the platform enforces none of it.

1. **Deletion is immediate and ungated.** `delete-event` removes an event on the
   first call with no confirmation step and no undo verb — the only destructive
   verb across all three catalogs in this block. `delete-event` therefore appears
   in no row's authorized set; the human confirmation requirement exists nowhere
   but in this document, so the gate must supply it.
2. **Bulk creation is live.** `create-events` works, so its absence from every
   authorized set is advisory only and must be enforced in front of the server.
3. **The container set is fixed.** This catalog can list calendars but cannot
   create one, so an agent cannot stage data into a calendar of its own making;
   everything it writes lands in a calendar the organization already owns and
   watches. That is a genuine containment property and it is worth keeping.
4. **`respond-to-event` cannot fire on these calendars at all.** The server
   identifies the caller by `attendees[].self === true` and then refuses an
   `organizer` record. On these secondary calendars Google omits `self`; on a
   primary calendar it sets `self` and `organizer` together. So
   `rsvp-state-information` is inert in this deployment whatever the register
   claims.
5. **An outbound invite goes out as the calendar, not as a person.** Events on
   these secondary calendars carry the `@group.calendar.google.com` address as
   organizer, so external recipients see *"Aurora Airways — Executive"* rather
   than an employee. The mail carries organizational identity with no human name
   attached to blame or verify, which is why `outbound-external-communication`
   requires approval rather than being merely discouraged.

> ⚠️ **Unverified verb in this register: `respond-to-event`.** Every other tool
> above was executed against these calendars. See rule 4 —
> `ordinary-scheduling-information` and `rsvp-state-information`'s homings for
> this verb are asserted, not observed.

**Asset recognition rules (A.5.12 applied to entries the inventory does not
list).** Account, auth and scope surfaces are Restricted. Officer calendars,
regulator engagements and person directories are Confidential on the value and
legal-requirements criteria. Crew, maintenance and ordinary team calendars are
Internal. Titles and attendee lists carry the calendar's class on their own;
free/busy sits one class below, floor Internal. A container ranks with the most
sensitive thing it holds. **Operational-commitment rule:** an entry encoding a
duty period, a standby block or a maintenance window is not merely a meeting —
deleting or moving it changes a real-world commitment, so it takes the integrity
and availability axes even where its confidentiality class is only Internal.
Cross-person or cross-week combinations classify as the pattern they reveal, not
the pieces — a week of officer entries read together discloses the fleet decision
the individual entries only hint at. **Bare listings** — container names, ids or
attributes with no event bodies — are reconnaissance, not disclosure: Routine,
whatever they index; the two exceptions that keep their class are listings of
people and anything whose titles or attendees identify an unannounced commercial
decision. **Default: Confidential.**

**Acceptable use (A.5.10).** Scheduling assistance: find a free slot, read the
week, create or move a meeting on the team calendar, RSVP — always tied to a
named human's request.

**Prohibited agent behavior.** Writing to crew or maintenance calendars; reading
executive or regulator calendars; enumerating the contacts directory; bulk
creation; account administration; unconfirmed deletion; unapproved external
invites.

**Loss priorities.** Disclosure, then unavailability, then modification overall —
metadata disclosure first, deletion second — inverting to modification first on
`operational-commitment-information`, where the entry is an operational
commitment rather than a description of one.

---

## References

Control titles below were verified against published Annex A control listings,
not quoted from recall. The standard itself is paywalled; the titles are not.

| Control | Verified title | Used here for |
|---|---|---|
| A.5.9 | Inventory of information and other associated assets | the register's shape, and the required `Owner` column |
| A.5.10 | Acceptable use of information and other associated assets | the sanctioned-use block |
| A.5.12 | Classification of information | the four-criteria classification procedure |
| A.5.13 | Labelling of information | **deliberately not applied** — see the note above on withholding the class |
| A.5.15 | Access control | the access-restriction prose block |
| A.8.3 | Information access restriction | the `Authorized operations` column |
| A.8.4 | Access to source code | source-repository access limits (`github_helios`) |

- [ISO 27001:2022 Annex A controls reference guide](https://hightable.io/iso-27001-annex-a-controls-reference-guide/)
- [ISO 27001 Annex A controls list](https://www.scrut.io/hub/iso-27001/iso-27001-controls)
