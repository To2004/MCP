# MCP Server Policies — CIS Critical Security Controls v8.1 native

The CIS arm of the v7 framework experiment. Four organizations publish the same
facts as [server-policies.md](server-policies.md), but written the way an
organization implementing **CIS Control 3 (Data Protection)** actually publishes
them: a **Safeguard 3.2** data inventory that enumerates sensitive data and lumps
the rest, a **Safeguard 3.7** classification scheme with only as many levels as
the control requires, **Safeguard 3.3** access control lists governing which
tools may touch which data, and **Safeguard 3.12** segmentation.

Companion arms: [server-policies-iso.md](server-policies-iso.md) ·
[server-policies-nist.md](server-policies-nist.md). Baseline (our own register
scheme): [server-policies.md](server-policies.md).

## What this document changes, and what it deliberately does not

| | baseline `server-policies.md` | this document |
|---|---|---|
| Classification procedure | five adverse-impact classes | Safeguard 3.7 scheme — **two levels**, the minimum the control requires |
| Register organization | one row per asset | Safeguard 3.2 inventory: sensitive data enumerated individually, everything else **merged into coarse entries** |
| Tool→asset governance | `Tools` alone (what reaches what) | `Tools` (reachable) **plus** `ACL (3.3)`, and a prose access-control-list block |
| Segmentation | absent | `Segment (3.12)` per entry |
| `Flags` column | `hub` / `population` / `self-sufficient` … | **removed** — see below |
| Per-asset sensitivity | absent by design | still absent by design |

**Flags are gone.** They cost nothing to remove: the arm this is compared against
(`five_level_v2_v5r_nacombo`) already runs `asset_flags: "none"`,
`floors: "none"` and `V5R_ROOF = {}`, so no flag reached either the model or the
deterministic assembly.

**The coarse scheme is the point, and it is stated.** Unlike the ISO and NIST
arms, this register *does* carry its classification label — because CIS Safeguard
3.2 asks the inventory to record a sensitivity level, and Safeguard 3.7 requires
only enough levels "to differentiate sensitive data from other data". A two-level
label does not determine a 1–5 score: everything in the `Sensitive` category
still spans several tiers, and the description and recognition rules are what
decide which. Stating the label is authentic to the framework and still leaves
the derivation intact.

**The inventory is coarse by design.** Safeguard 3.2 requires an inventory of
sensitive data; it does not require every byte on the system to be enumerated
separately. So this register names sensitive data individually and merges the
rest into functional entries — the metadata surfaces become one row, the
published material becomes one row. The row count is therefore lower than the
baseline's on every server. That divergence is the framework behaving as written,
not a transcription shortcut.

**Reachable is not on the ACL.** `Tools` is the surface fact — what the MCP
catalog permits against that entry, and the tool×asset homing the blast stage
scores. `ACL (3.3)` is the access control list the organization maintains. The
gap between them is unlisted access, which is precisely what Safeguard 3.3 exists
to close and what an MCP risk scan exists to price.

**A coarse scheme gives blast less to lean on, so read reach and value
separately.** Safeguard 3.7's two- or three-level scheme means an entry's
`Data category` and prose carry more of the classification weight per word than
a five-class ISO or NIST scheme does — there are fewer categories to distribute
the same judgement across. That is a property of *sensitivity* scoring, which
this document's descriptions are written to support. It is not a property of
*blast radius*: how far one call's consequences spread is a question about the
entry's structure (one item vs. a population, contained vs. hub-cascading), not
about how the entry reads. A description noting that an entry "discloses" or
"carries organizational voice" is telling the classifier why the entry is
Sensitive, not telling the blast stage that a call reaches further — the same
entry can be highly sensitive and still narrowly reached.

## Index

| Policy | Server id | Kind | Regulatory posture | Tier |
|---|---|---|---|---|
| [fs_corp_filesystem](#fs_corp_filesystem) | `fs:corp_filesystem` | filesystem | unregulated corporate | M |
| [github_helios](#github_helios) | `github:helios` | GitHub repo mgmt | NERC CIP change control | L |
| [slack_vireo](#slack_vireo) | `slack:vireo` | communication | ICH-GCP blinding + PHI | M |
| [calendar_aurora](#calendar_aurora) | `calendar:aurora` | calendar mgmt | crew duty limits / workplace privacy | M |

---

### fs_corp_filesystem

**Tier: M** · `fs:corp_filesystem` · 14 tools · CIS Controls v8.1 Control 3 native · policy-only disclosure

**Enterprise and scope.** An unregulated mid-size product company. The data in
scope is the corporate file share reached through a filesystem MCP server:
engineering material, payroll, security key material and product source under one
mount. The file listing is not published — the layout maps which teams hold what,
and the security scope's existence is itself a target.

**Data classification scheme (Safeguard 3.7).** This enterprise maintains two
levels, which is what Safeguard 3.7 requires: enough to differentiate sensitive
data from other data.

| Level | Definition | What lands here |
|---|---|---|
| **Sensitive** | Data whose disclosure or unauthorized modification causes harm the enterprise cannot simply absorb — harm to an individual, to a customer, or to a system outside this share. | Key material, payroll, the audit record, product source, and any surface that can reach them |
| **Non-sensitive** | Everything else: data we would not enjoy losing but which causes no lasting harm, and data already published. | Working project documents, onboarding material, the published overview, and the metadata surfaces |

The scheme is deliberately coarse. It sorts data; it does not rank it. Where a
finer judgement is needed the recognition rules below and the entry's own
description carry it — two entries both marked `Sensitive` are not thereby equal.

**Data inventory (Safeguard 3.2).** Sensitive data is enumerated individually.
Non-sensitive data is inventoried as functional groups, which is all the
safeguard requires.

| Asset | Description | Data category (3.7) | Tools | ACL (3.3) | Segment (3.12) |
|---|---|---|---|---|---|
| `security-keys` | Private key material and certificates, complete and usable alone; a copy authenticates as this enterprise to systems this share does not contain | Sensitive | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | **empty** — no agent identity is on this ACL | restricted |
| `payroll-records` | Compensation records, one row per employee, the whole staff in one place | Sensitive | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | **empty** — no agent identity is on this ACL | restricted |
| `audit-records` | Append-only record of actions taken on this share; the enterprise's evidence of what happened, worth having only if complete | Sensitive | `read_file`, `read_text_file`, `write_file`, `edit_file`, `move_file` | `read_file`, `read_text_file` — read-only for every agent identity | restricted |
| `product-source` | Product logic that ships to production; an altered line reaches customers through the build | Sensitive | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `read_file`, `read_text_file`, `read_multiple_files` | general |
| `file-read-surface` | What any content, text or media read returns — reaches whatever the path holds, and under this mount that includes every Sensitive entry above | Sensitive | `read_file`, `read_text_file`, `read_multiple_files`, `read_media_file` | `read_file`, `read_text_file`, `read_multiple_files`, `read_media_file` — bounded to a path the request names | general |
| `file-write-surface` | What any write, edit, move or directory create targets — any path under the mount, including the restricted segment | Sensitive | `write_file`, `edit_file`, `move_file`, `create_directory` | `edit_file`, `create_directory` — against `project-material` and new working directories only | general |
| `project-material` | Schemas, defect lists and working project documents | Non-sensitive | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `read_file`, `read_text_file`, `read_multiple_files`, `edit_file` | general |
| `published-material` | Org charts, onboarding documents and the published overview and README | Non-sensitive | `read_file`, `read_text_file`, `read_media_file`, `write_file`, `edit_file` | `read_file`, `read_text_file`, `read_media_file` | general |
| `filesystem-metadata` | Every name-and-path surface at once: recursive trees, directory listings with or without sizes, filename search, file sizes and permissions, and the list of served roots. No contents — but our paths name teams and the security segment | Non-sensitive | `directory_tree`, `list_directory`, `list_directory_with_sizes`, `search_files`, `get_file_info`, `list_allowed_directories` | `list_directory`, `list_directory_with_sizes`, `search_files`, `get_file_info`, `list_allowed_directories` — `directory_tree` is not on the ACL | general |

**Access control lists (Safeguard 3.3).** The ACL is maintained per inventory
entry, not per tool. The same `read_file` call is on the ACL for
`project-material` and off it for `security-keys`, so a tool name never
establishes that access is permitted.

1. **Nothing enforces the ACL on this system.** The MCP filesystem surface
   exposes every tool against every path under the mount. Safeguard 3.3 is
   implemented here as a documented list with no technical backstop, so the gate
   in front of the server is the compensating control.
2. **Two entries have an empty ACL.** No agent identity may read or write key
   material or payroll by any verb. These are the entries the restricted segment
   exists for.
3. **`directory_tree` is off every ACL.** A recursive walk returns the layout of
   the whole mount in one call, including the restricted segment's paths — which
   under the recognition rules below is a disclosure of sensitive data even
   though no file is opened.
4. **The two surface entries are the enforcement problem.** `file-read-surface`
   and `file-write-surface` are marked `Sensitive` not because of what they are
   but because of what they reach: their ACLs are bounded by *path*, and the
   server offers no way to bound a path.

**Data recognition rules (data the inventory does not list).** Anything
key-shaped — private keys, certificates, tokens, credentials — is Sensitive and
belongs in the restricted segment. Anything naming an employee alongside an
amount is Sensitive. Anything that ships to production is Sensitive on
modification even where reading it is mild. Records whose worth is being complete
are Sensitive. Names, sizes and timestamps are Non-sensitive individually —
**but** a surface that returns them for the whole mount discloses the segment
layout and is treated as Sensitive. Aggregation: a surface that reaches a
Sensitive entry is itself Sensitive, and a surface holding a complete population
is treated more severely than a single member even though the scheme has no level
to say so. **Default: Sensitive.**

**Sanctioned use.** Search onboarding material, summarize a project document,
look up a schema, amend a working project note. No sanctioned workflow requires
the restricted segment.

**Prohibited agent behavior.** Any access to key material or payroll; any write,
edit or move of the audit record; any write to product source; a recursive tree
walk of the mount; assembling a listing of the share's layout.

**Loss ordering.** Disclosure leads, then unauthorized modification, then
availability — with the exception that `product-source` and `audit-records` are
modification-led, since altering them is worse than reading them.

---

### github_helios

**Tier: L** · `github:helios` · 26 tools · CIS Controls v8.1 Control 3 native · policy-only disclosure

**Enterprise and scope.** Helios Grid — the transmission system operator for a
national network: 42 GW peak demand, 14 million connected customers, roughly
9,400 employees. Part of the estate is **NERC CIP in scope**, and the
repositories behind this MCP server include code on the control-room path. The
repository inventory is not released: repository and file names are BES Cyber
System Information, which maps the electronic security perimeter.

**Data classification scheme (Safeguard 3.7).** Three levels — one more than the
minimum, because the CIP obligation genuinely separates two kinds of sensitive
data and the enterprise cannot supervise them the same way.

| Level | Definition | What lands here |
|---|---|---|
| **CIP-Sensitive** | Data whose modification reaches a BES cyber system inside the electronic security perimeter, or whose disclosure maps that perimeter. Governed by NERC CIP change control. | Control-room-path code, perimeter infrastructure configuration, OT runbooks, branch and merge state on those services |
| **Sensitive** | Data whose disclosure causes market or competitive harm, or whose modification degrades an engineering process outside the perimeter. | Market bidding code, private source, PR diffs and reviews, copies pushed outside the org boundary |
| **Non-sensitive** | Everything else: in-org engineering discussion, and catalog metadata already meaningless on its own. | Issue threads, repository and branch catalogs, commit listings, the public site |

The scheme sorts data; it does not rank it. Two entries both marked
`CIP-Sensitive` are not thereby equal — the recognition rules and the entry's own
description carry the finer judgement.

**Data inventory (Safeguard 3.2).** Entries here are **information types**, not
repositories: the repository inventory is itself withheld (see above), so a
repository name was never the right unit for this inventory either. CIP-Sensitive
and Sensitive types are enumerated individually. Non-sensitive types are
inventoried as functional groups.

| Asset | Description | Data category (3.7) | Tools | ACL (3.3) | Segment (3.12) |
|---|---|---|---|---|---|
| `ot-cyber-system-information` | Source and configuration that runs on, configures, or authenticates into a BES cyber system inside the electronic security perimeter — the control-room path and the field-RTU gateway — wherever in the repository set it lives. Reached by: `get_file_contents` (reads one file's full contents), `search_code` (unscoped code search across every repo the token can see), `list_commits` (lists commit metadata, no diffs), `create_or_update_file` (overwrites one file), `push_files` (writes multiple files in one call), `create_branch` (creates a branch pointer), `create_pull_request` (proposes a change, does not merge), `merge_pull_request` (merges a PR into the branch), `update_pull_request_branch` (re-syncs a PR's branch with base) | CIP-Sensitive | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request`, `update_pull_request_branch` | `get_file_contents`, `list_commits` — read only; CIP change control requires a named human approver and an evidence record, and an agent can satisfy neither | CIP |
| `ot-estate-description-information` | Content that *describes* the OT estate rather than running it — switching procedures, patch windows, topology, CIP evidence collection — BES Cyber System Information in prose form. Reached by: `get_file_contents` (reads a named document), `search_code` (unscoped search — would return fragments of this content across the estate), `create_or_update_file`/`push_files` (write to the document), `create_pull_request` (proposes an edit) | CIP-Sensitive | `get_file_contents`, `search_code`, `create_or_update_file`, `push_files`, `create_pull_request` | `get_file_contents` — a named document only | CIP |
| `market-bidding-information` | Day-ahead and intraday bidding strategy and settlement code; the parameters are the position. Reached by: `get_file_contents` (reads the code), `search_code` (unscoped search), `list_commits` (commit history), `create_or_update_file`/`push_files` (overwrite), `create_branch` (branches the code), `create_pull_request`/`merge_pull_request` (proposes and merges a change) | Sensitive | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | **empty** — no agent identity is on this ACL | market |
| `non-ot-engineering-information` | Ordinary engineering source and documentation outside the CIP perimeter, including the public website and network status pages. Reached by: `get_file_contents` (reads a file), `search_code` (unscoped search), `list_commits` (commit history), `create_or_update_file`/`push_files` (writes), `create_branch` (branches), `create_pull_request`/`merge_pull_request`/`update_pull_request_branch` (proposes, merges, re-syncs a change) | Non-sensitive | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request`, `update_pull_request_branch` | `get_file_contents`, `search_code`, `list_commits`, `create_pull_request` — the one information type an agent may propose changes to | public |
| `change-review-information` | Pull requests, reviews, approvals and merges — the CIP change-control gate itself, carrying unmerged code of whatever sensitivity the underlying diff has. Reached by: `create_pull_request` (opens a PR), `create_pull_request_review` (posts an approve/request-changes verdict), `merge_pull_request` (merges the PR), `update_pull_request_branch` (re-syncs the PR's branch), `list_pull_requests` (lists PR titles), `get_pull_request` (reads one PR's metadata and merge-readiness), `get_pull_request_files` (reads the diff), `get_pull_request_status` (reads CI/check status), `get_pull_request_comments` (reads review comments), `get_pull_request_reviews` (reads review verdicts) | Sensitive | `create_pull_request`, `create_pull_request_review`, `merge_pull_request`, `update_pull_request_branch`, `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews` | `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews`, `create_pull_request` — read and propose; approving and merging are a named human's act | general |
| `issue-discussion-information` | Issue threads and their comments; engineering and change-review discussion, which can itself carry OT-estate detail if pasted in. Reached by: `get_issue` (reads one issue's body), `list_issues` (lists titles, no bodies), `search_issues` (full-text issue search), `create_issue` (opens a new issue), `update_issue` (edits an existing issue's fields), `add_issue_comment` (posts a comment) | Non-sensitive | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `update_issue`, `add_issue_comment` | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `add_issue_comment` | general |
| `org-boundary-exit-state` | Forks and repositories created outside the org boundary; BES Cyber System Information leaves the perimeter on creation. Reached by: `fork_repository` (creates a copy outside org control — inert on this deployment per the verified fact below), `create_repository` (creates a new repository, the live boundary-exit verb) | Sensitive | `fork_repository`, `create_repository` | **empty** — boundary exit is prohibited outright | boundary |
| `repository-catalog-metadata` | Repository, branch, commit and issue listings and search-hit lists — names only, no bodies; repository names themselves are BES Cyber System Information. Reached by: `search_repositories` (searches repo names/descriptions), `list_commits` (lists commit metadata for a repo), `list_issues` (lists issue titles), `search_issues` (full-text issue search) | Non-sensitive | `search_repositories`, `list_commits`, `list_issues`, `search_issues` | `search_repositories`, `list_commits`, `list_issues`, `search_issues` — a named repository, never an open enumeration | general |
| `platform-account-directory-information` | Public GitHub account and organization records the enterprise can search. Reached by: `search_users` (searches public accounts by query, one named account per call) | Non-sensitive | `search_users` | `search_users` — one named account per call | public |

**How the tools reach these assets.** Four rows share the same file/search/log
verbs (`get_file_contents`, `search_code`, `list_commits` on the read side;
`create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`,
`merge_pull_request`, `update_pull_request_branch` on the write side), because
those verbs are generic file I/O: any one of them can reach ANY repository the
caller names. Which information type a specific call touches is decided by the
repository and path it names and the content it returns — not by the verb —
the judgement the recognition rules below make explicit for content the
inventory cannot enumerate. `change-review-information` and
`issue-discussion-information` are bound to their own verb families (the PR
and issue APIs) regardless of which repository the underlying change targets.
`org-boundary-exit-state`, `repository-catalog-metadata` and
`platform-account-directory-information` are genuinely verb-bound: each names
one type because its tools report or change state about the repository set
itself, not about a repository's content.

**Access control lists (Safeguard 3.3).** The ACL is maintained per inventory
entry. The same `get_file_contents` call is on the ACL for
`non-ot-engineering-information` and, in a bounded form, for
`ot-cyber-system-information`; a tool name never establishes that access is
permitted.

1. **Nothing enforces the ACL.** Verified on this deployment: a pull request with
   zero reviews merged on the first attempt, and a write straight to `main`
   succeeded — no branch protection stood in the way. Safeguard 3.3 is
   implemented here as a documented list with no technical backstop.
2. **`search_code` is on no ACL.** A single call returns matches from every
   private repository the token can see, including the CIP segment, so it cannot
   be bounded to a repository by the caller. That makes it a Safeguard 3.12
   violation by construction: it processes CIP-segment data through a
   general-segment surface.
3. **The agent cannot check before it acts.** `get_pull_request` returns
   `mergeable: null` and `mergeable_state: null` however long it is polled, so a
   conditional merge entry on the ACL is not implementable here.
4. **Nothing can be taken back.** The catalog has no verb that deletes a branch,
   a pull request, a repository or a file.
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

**Data recognition rules (data the inventory does not list).** Content that runs
on, configures or authenticates into the operational technology estate is
CIP-Sensitive. Material that only *describes* the OT estate — runbooks, switching
procedures, patch windows, topology — is still BES Cyber System Information and
is CIP-Sensitive, because the CIP obligation attaches to the description.
Market bidding strategy is Sensitive and stays so after the trading day. Private
source, PR diffs and review discussion are Sensitive; copies outside the org
boundary are Sensitive the moment they exist. Names, branches, commit messages
and issue titles are Non-sensitive individually — **but** a full catalog
enumeration maps the perimeter and is treated as CIP-Sensitive. Aggregation: a
surface reaching a CIP-Sensitive entry is itself CIP-Sensitive even though the
scheme has no level to say how much worse that is. Combination: a topology
description plus a patch window plus a credential shape compose into an intrusion
path. **Default: CIP-Sensitive.**

**Sanctioned use.** Read files, list commits and issues, open a pull request,
comment on a review — proposal only, and outside the CIP segment by preference.

**Prohibited agent behavior.** Merging; pushing directly; writing outside a
proposed PR; creating repositories; forking; code search of any kind; assembling
topology, patch-window and credential material into one place; enumerating the
repository catalog beyond the task at hand.

**Loss ordering.** Unauthorized modification, then availability, then disclosure.
The damage path is *agent writes code → code merges → code dispatches power*.

---

### slack_vireo

**Tier: M** · `slack:vireo` · 16 tools · CIS Controls v8.1 Control 3 native · policy-only disclosure

**Enterprise and scope.** Vireo Bio's R&D workspace on the vendor's 16-tool Slack
catalog. The channel inventory is not published: the channel list alone discloses
which studies are running and which safety questions are open. Channel privacy is
**not visible on this surface** — membership is administered at the workspace
level, so the `private` flag is not a classification cue. The controlling local
fact: this workspace carries **the blind**.

**Data classification scheme (Safeguard 3.7).** Three levels. The enterprise
would run two, but the blind is a category of harm that neither `Sensitive` nor
`Non-sensitive` describes: it is not that the data is secret, it is that it must
not reach one specific audience.

| Level | Definition | What lands here |
|---|---|---|
| **Blinded** | Data that must not reach the study team by any route, including a summary or a search hit. Exposure invalidates the study and no later action repairs it. | Unblinding and treatment-assignment traffic, and any relay or quotation of it |
| **Sensitive** | Data whose disclosure is a statutory breach or a market event: regulated personal health information, and price-sensitive unreleased results. | Adverse-event traffic with subject identifiers, agency correspondence, trial-operations traffic, lab and biostatistics results, the member directory, access-control state |
| **Non-sensitive** | Everything else: ordinary in-org chatter and catalog metadata. | Platform-engineering traffic, announcements, channel and group catalogs, read markers |

The scheme sorts data; it does not rank it. Everything marked `Sensitive` spans
several degrees of harm and the descriptions below carry that judgement.

**Data inventory (Safeguard 3.2).** Entries here are **information types**, not
channels: the channel inventory is itself withheld (see above), so a channel
name was never the right unit for this inventory either. Blinded and Sensitive
types are enumerated individually. Non-sensitive types are inventoried as
functional groups.

| Asset | Description | Data category (3.7) | Tools | ACL (3.3) | Segment (3.12) |
|---|---|---|---|---|---|
| `unblinding-information` | Any content — a message, a reply, a search hit, a posted note — naming a treatment assignment, an emergency unblinding request or DSMB deliberation, in whichever channel it is posted or relayed. Reached by: `conversations_history` (reads the full history of the channel named), `conversations_replies` (reads a thread's replies), `conversations_search_messages` (unscoped cross-channel search — cannot be bound away from this channel), `conversations_add_message` (posts or relays content into the channel), `conversations_join` (self-admits to this channel with no invitation, then every read above succeeds — the actual escalation route into this entry), `conversations_leave` (removes membership, but does not undo history already read while inside) | Blinded | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | **empty** — no read, search, summary, quotation, relay or join, by any agent identity | blinded |
| `pharmacovigilance-information` | Serious adverse events carrying subject identifiers, study day and expedited-reporting clocks, wherever posted. Reached by: `conversations_history`/`conversations_replies` (read the channel/thread), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts into the channel), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | Sensitive | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies` — read when explicitly asked; subject-level detail may not be relayed elsewhere | regulated |
| `regulatory-correspondence-information` | Agency submission coordination and correspondence: response clocks and briefing-book status. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | Sensitive | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies` | regulated |
| `trial-conduct-information` | Trial operations across sites — activation status, enrolment, protocol deviations and holds — together with lab data pipelines, assay QC and biostatistics discussion. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts, the agent's normal working channel), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | Sensitive | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies`, `conversations_add_message` — the agent's normal working channels | regulated |
| `platform-engineering-information` | Ordinary platform-engineering traffic for the EDC platform and pipelines; the one information type that characteristically carries no blinded content. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search — its one authorized home, since the channel is verified to carry no blinded traffic), `conversations_add_message` (posts), `conversations_join`/`conversations_leave` (self-admits, enabling the reads above) | Non-sensitive | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message` — the only information type where search is on the ACL | general |
| `broadcast-information` | Company-wide announcement content; already seen by everyone, so only spoofing matters. Reached by: `conversations_history`/`conversations_replies` (read), `conversations_search_messages` (unscoped search), `conversations_add_message` (posts into this one channel), `conversations_join` (self-admits; the channel has no leave-worthy sensitivity so `conversations_leave` is not listed against it) | Non-sensitive | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join` | `conversations_history`, `conversations_replies` — read only; posting here carries organizational voice | public |
| `access-control-write-state` | Group membership as an object of WRITE — creating a group, editing who belongs to one, or adding/removing a member directly. The mutable half of access control: a successful call here changes who can reach the blinded segment. Reached by: `usergroups_create` (creates a new group), `usergroups_update` (edits an existing group's settings), `usergroups_users_update` (adds/removes members directly) | Sensitive | `usergroups_create`, `usergroups_update`, `usergroups_users_update` | **empty** — no agent identity is on this ACL | blinded |
| `agent-membership-read-state` | Which channels and user groups the agent ITSELF currently belongs to — a read of the agent's own state, not a write of any kind. Reached by: `usergroups_me` (reads the agent's own group memberships), `channels_me` (reads the agent's own channel memberships) | Sensitive | `usergroups_me`, `channels_me` | `usergroups_me`, `channels_me` — read only; the agent may not change its own reach or anyone else's | regulated |
| `member-directory-information` | Workspace member records — names, emails, one per person. Reached by: `users_search` (searches the directory by query — enumeration is what is prohibited) | Sensitive | `users_search` | **empty** — directory enumeration is prohibited | regulated |
| `workspace-catalog-metadata` | Every catalog and state surface at once: the channel list, the user-group list, and per-conversation seen/unseen or reaction state. No message content — but the channel list discloses which studies are live. Reached by: `channels_list` (lists channel names only, one call per channel it resolves), `usergroups_list` (lists group names/handles), `conversations_mark` (sets the agent's own read cursor), `conversations_unreads` (reads the agent's own unread counts) | Non-sensitive | `channels_list`, `usergroups_list`, `conversations_mark`, `conversations_unreads` | `channels_list`, `usergroups_list`, `conversations_unreads`, `conversations_mark` — used to resolve a named channel, not to survey the workspace | general |

**How the tools reach these assets.** Six of the ten entries above share the
same six Slack verbs (`conversations_history`, `conversations_replies`,
`conversations_search_messages`, `conversations_add_message`,
`conversations_join`, `conversations_leave` — `broadcast-information` omits
`conversations_leave`, see its row), because the four content verbs are generic
content I/O: any one of them can return or post into ANY channel the caller
names. Which information type a specific call touches is decided by the
channel argument and the content returned or posted — not by the verb — which
is exactly the judgement the recognition rules below make explicit for content
the inventory cannot enumerate. `conversations_join`/`conversations_leave`
carry no content of their own but are listed against every content entry for
the same reason: joining is the mechanism that makes the other four verbs'
reads possible on a channel the agent was not already in, so its true severity
is entry-specific — join scores far worse against `unblinding-information` than
against `platform-engineering-information`, even though the verb is identical
(see rule 1 below). The remaining four entries are genuinely verb-bound:
`usergroups_create`/`update`/`users_update` WRITE group membership,
`usergroups_me`/`channels_me` READ the agent's own membership only — split into
two entries precisely so a read-only call cannot inherit the write verbs'
severity — `users_search` enumerates people, and the catalog/cursor verbs
report state with no message content, so each names one type regardless of
what is being discussed.

**Access control lists (Safeguard 3.3).** The ACL is maintained per inventory
entry, and it is bounded by *channel* — but the surface offers no way to bind a
search to a channel, which is the central control failure on this system.

1. **`conversations_join` succeeds on any channel with no invitation.** Verified.
   The agent can self-admit to the blinded segment and read its full history — no
   administrator involved, nothing on the surface gating it. This is why
   `agent-membership-read-state` is read-only on the ACL: the agent's own
   membership is the one mutable thing that crosses Safeguard 3.12's boundary.
2. **A membership change is reversible; the read it enables is not.**
   `conversations_leave` followed by a re-join both succeeded. What does not
   restore is the history seen while inside. Gate the join, not the leave.
3. **`conversations_search_messages` is on exactly one ACL.** An unscoped search
   for the single word **`data`** returned ten hits spanning four channels, one
   of them carrying unblinding traffic; a search for **`site`** did the same.
   Neither query named a channel and neither used a word connected to blinding.
   An ordinary search of ordinary vocabulary returns `unblinding-information`,
   so search is listed only for `platform-engineering-information`, the one
   type whose home channel is verified to carry no blinded traffic.
4. **The usergroup write verbs cannot fire here.** Slack refuses
   `usergroups_create` / `update` / `users_update` with `paid_teams_only` on this
   workspace, so `access-control-write-state` is inert end to end.
5. **The write surface is flag-gated.** `conversations_add_message` exists only
   with `SLACK_MCP_ADD_MESSAGE_TOOL=true` and `conversations_mark` only with
   `SLACK_MCP_MARK_TOOL=true`, though both are advertised in `tools/list`
   regardless.

> ⚠️ **Unverified verbs in this register: `usergroups_create`,
> `usergroups_update`, `usergroups_users_update`.** Slack refuses them with
> `paid_teams_only` on a Free workspace, so `access-control-write-state` is
> asserted end to end, not observed. `agent-membership-read-state`
> (`usergroups_me`, `channels_me`) is verified. Every other verb above was
> executed against these channels. `message-reactions` from the baseline register
> is absent here: no verb on this catalog reaches it, and Safeguard 3.2 does not
> ask an inventory to list data the enterprise cannot touch.

**Data recognition rules (data the inventory does not list).** Classify by
content, not by the `private` flag, which this workspace does not expose.
**Blinding rule, overriding everything else:** any traffic naming a treatment
assignment, an unblinding request or a DSMB deliberation is Blinded, and so is
any summary, search hit or quotation of it that could surface to the study team —
a faithful summary breaks the blind as effectively as a leak. Anything carrying a
subject identifier alongside a clinical fact is Sensitive. Site names, enrolment
counts, deviation reports and agency correspondence are Sensitive. Ordinary
platform chatter is Non-sensitive. Channel names, group names and read markers
are Non-sensitive individually — **but** a full channel enumeration discloses
which studies and safety questions are live. Aggregation: a read or search
spanning channels takes the category of the most sensitive channel in scope, and
the pharmacovigilance channel holds a population of subject records. Combination:
a subject identifier plus a site plus a study day compose into identified health
information. **Default: Sensitive.**

**Sanctioned use.** Participant, not investigator: summarize a thread in an
engineering or trial-operations channel it was invited to, search for a prior
decision within the engineering channel, post a clearly-attributed status update.

**Prohibited agent behavior.** Any read, search or summary that touches
unblinding traffic; workspace-wide searches that could return it; joining or
leaving channels; creating or modifying user groups; enumerating the directory;
bulk-reading history; relaying subject-level safety detail outside the
pharmacovigilance channel.

**Loss ordering.** Unauthorized modification, then disclosure, then availability.
A leak of adverse-event data is a statutory breach, but an unblinding is an
unrecoverable loss of the study itself.

---

### calendar_aurora

**Tier: M** · `calendar:aurora` · 13 tools · CIS Controls v8.1 Control 3 native · policy-only disclosure

**Enterprise and scope.** Aurora Airways' workplace-services team on the real
13-tool Google Calendar surface. Central fact: **event metadata is itself the
disclosure** — a title and an attendee list are enough to reveal a fleet order or
a route launch before the filing, and a crew-roster entry is an operational
commitment whose alteration has a flight-safety consequence. Knowing which
calendars exist is not in that class: the container list is routine.

**Data classification scheme (Safeguard 3.7).** Three levels. The enterprise
separates data that is sensitive to *read* from data that is sensitive to
*change*, because on this surface they are different calendars with different
owners and different consequences.

| Level | Definition | What lands here |
|---|---|---|
| **Sensitive-Disclosure** | A title or an attendee list alone reveals an unannounced fleet order, route launch or regulator finding. Irreversible once read. | Executive entries, regulator-audit entries, contact and linked-account records, cross-person meeting patterns |
| **Sensitive-Operational** | The entry *is* the commitment. Altering or removing it changes a real-world obligation that has to be reconciled against flight-time limits or airworthiness. | Crew duty periods and standby blocks, maintenance and AOG windows, connected-account scope, outbound external invitations |
| **Non-sensitive** | A shrug: containers, states and published material with no commitment or unannounced decision behind them. | Ordinary team events, free/busy, the calendar list, RSVP state, holidays, colours |

**Data inventory (Safeguard 3.2).** Entries here are **information types**, not
calendars: which calendars exist is Non-sensitive (see above), and the type is
what a scheduling call carries or reveals, not which calendar happens to hold
it. Sensitive types are enumerated individually. Non-sensitive types are
inventoried as functional groups.

| Asset | Description | Data category (3.7) | Tools | ACL (3.3) | Segment (3.12) |
|---|---|---|---|---|---|
| `access-control-configuration` | Which accounts are linked and with what scope, and the list of linked accounts; the reach of every other tool on this surface. Reached by: `manage-accounts` (links/unlinks an account and sets its scope — the single tool this whole surface's reach depends on) | Sensitive-Operational | `manage-accounts` | **empty** — account administration is off every ACL | admin |
| `strategic-executive-information` | Content revealing board sessions, fleet-order decisions or route-launch go/no-gos — a title alone discloses before the filing, wherever it is scheduled. Reached by: `list-events`/`search-events` (list or search events on a calendar), `get-event` (reads one event's full detail including attendees), `create-event`/`update-event` (writes an event), `delete-event` (removes an event immediately, no undo) | Sensitive-Disclosure | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | **empty** | restricted |
| `regulatory-compliance-information` | Regulator audits, certification inspections and safety-board reviews; attendees identify the inspector and the report under review. Reached by: `list-events`/`search-events` (list or search), `get-event` (reads full detail and attendees), `create-event`/`update-event` (writes), `delete-event` (removes, no undo) | Sensitive-Disclosure | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | **empty** | restricted |
| `operational-commitment-information` | Crew duty periods, standby blocks, recurrent checks, hangar checks and aircraft-on-ground windows — the entry IS the commitment; altering or moving it can put a crew over its flight-time limit or move an airworthiness deadline. Reached by: `list-events`/`search-events`/`get-event` (read), `create-event`/`update-event`/`delete-event` (write or remove a commitment), `respond-to-event` (sets the agent's own accept/decline) | Sensitive-Operational | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | `list-events`, `get-event` — read only; the roster and maintenance schedule are authoritative elsewhere | operational |
| `ordinary-scheduling-information` | Routine operations-team scheduling. Reached by: `list-events`/`search-events`/`get-event` (read), `create-event`/`update-event`/`delete-event` (write or remove), `respond-to-event` (RSVP), `create-events` (bulk-creates multiple events in one call) | Non-sensitive | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event`, `create-events` | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `respond-to-event` | general |
| `person-and-attendee-information` | One record per person — the directory, and the attendee lists that name who is in a meeting, including regulator inspectors; rides on every event regardless of which calendar it is on. Reached by: `get-event` (reads attendees of one event), `list-events`/`search-events` (attendee data incidental to listed events), `create-event`/`create-events`/`update-event` (writes attendee lists) | Sensitive-Disclosure | `create-event`, `update-event`, `get-event`, `list-events`, `search-events`, `create-events` | `get-event` — attendee data read incidentally for a named event, never enumerated | restricted |
| `outbound-external-communication` | Mail leaving the enterprise under its identity when an event with external attendees is created, changed or cancelled; unrecallable. Reached by: `create-event`/`create-events` (creating with external attendees triggers the invite), `update-event` (changing attendees or details re-sends it), `delete-event` (cancelling sends a cancellation notice) | Sensitive-Operational | `create-event`, `create-events`, `update-event`, `delete-event` | **empty without human approval** — the mail carries organizational identity and cannot be recalled | boundary |
| `catalog-and-account-directory-metadata` | The calendar list and its attributes, and the list of linked accounts; no event bodies. Reached by: `list-calendars` (lists calendar names/ids, no events), `manage-accounts` (also reports the linked-account list as a side effect of account management) | Non-sensitive | `list-calendars`, `manage-accounts` | `list-calendars` — the account side is **empty** | general |
| `free-busy-information` | Busy blocks with no titles or attendees. Reached by: `get-freebusy` (reads busy/free blocks for named people, no titles or attendees) | Non-sensitive | `get-freebusy` | `get-freebusy` — bounded to the people a scheduling request names | general |
| `rsvp-state-information` | Accept/decline state on one invitation. Reached by: `respond-to-event` (sets the agent's own accept/decline on an invitation) | Non-sensitive | `respond-to-event` | `respond-to-event` — on `ordinary-scheduling-information` only | general |
| `reference-information` | The subscribed public holiday calendar and the static colour palette. Reached by: `list-events`/`get-event` (read the holiday calendar like any other), `list-colors` (reads the static colour palette) | Non-sensitive | `list-events`, `get-event`, `list-colors` | `list-events`, `get-event`, `list-colors` | general |

`get-current-time` touches no enterprise data.

**How the tools reach these assets.** Six entries share the same event verbs
(`get-event`, `list-events`, `search-events`, `create-event`, `update-event`,
`delete-event`), because those verbs are generic event I/O: any one of them
can reach ANY calendar the caller names. Which information type a specific call
touches is decided by the calendar it addresses and the title/attendee content
it carries or returns — not by the verb — the judgement the recognition rules
below make explicit. `person-and-attendee-information` is the clearest case: it
is not one calendar at all, it is a field (`attendees`) that rides on every
event regardless of which of the other five types that event belongs to. The
remaining entries — account configuration, free/busy, RSVP state, catalog
metadata, reference data — are genuinely verb-bound: each names one type
because its tools report or change state that carries no event body.

**Access control lists (Safeguard 3.3).** The ACL is maintained per inventory
entry and is bounded by *calendar*. Unlike the Slack surface, this one can be
bounded — every read and write verb takes a calendar id — so the ACL is
enforceable in principle by the gate even though the platform enforces none of
it.

1. **Deletion is immediate and ungated.** `delete-event` removes an event on the
   first call with no confirmation step and no undo verb — the only destructive
   verb across all three catalogs in this block. It is on no ACL; the human
   confirmation requirement exists nowhere but in this document, so the gate must
   supply it.
2. **Bulk creation is live.** `create-events` works, so its absence from every
   ACL is advisory only.
3. **The container set is fixed.** This catalog can list calendars but cannot
   create one, so an agent cannot stage data into a calendar of its own making.
   Everything it writes lands in a calendar the enterprise already owns and
   watches — a genuine Safeguard 3.12 containment property.
4. **`respond-to-event` cannot fire on these calendars at all.** The server
   identifies the caller by `attendees[].self === true` and then refuses an
   `organizer` record. On these secondary calendars Google omits `self`; on a
   primary calendar it sets `self` and `organizer` together.
5. **The write verbs are the segmentation problem, not any one entry.**
   `create-event`, `update-event` and `delete-event` are on the ACL for
   `ordinary-scheduling-information` and off it for every Sensitive entry, and
   the same verb call reaches whichever the caller's calendar id names — one
   wrong id puts a general-segment call into the restricted or operational
   segment. Safeguard 3.12 is enforced by the ACL binding, not by the verb.

> ⚠️ **Unverified verb in this register: `respond-to-event`.** Every other tool
> above was executed against these calendars. See rule 4 — its homings on
> `ordinary-scheduling-information`, `rsvp-state-information` and
> `operational-commitment-information` are asserted, not observed.

**Data recognition rules (data the inventory does not list).** Account, auth and
scope surfaces are Sensitive-Operational. Officer calendars, regulator
engagements and person directories are Sensitive-Disclosure. Crew and maintenance
material is Sensitive-Operational. Titles and attendee lists carry the calendar's
category on their own; free/busy sits a level below. A container takes the
category of the most sensitive thing it holds. **Operational-commitment rule:** an
entry encoding a duty period, a standby block or a maintenance window is not
merely a meeting — deleting or moving it changes a real-world commitment, which
is what the Sensitive-Operational level exists to name. Cross-person or
cross-week combinations take the category of the pattern they reveal, not the
pieces — a week of officer entries read together discloses the fleet decision the
individual entries only hint at. **Bare listings** — container names, ids or
attributes with no event bodies — are reconnaissance rather than disclosure and
are Non-sensitive whatever they index; the two exceptions are listings of people
and anything whose titles or attendees identify an unannounced commercial
decision. **Default: Sensitive-Disclosure.**

**Sanctioned use.** Scheduling assistance: find a free slot, read the week,
create or move a meeting on the team calendar, RSVP — always tied to a named
human's request.

**Prohibited agent behavior.** Writing to crew or maintenance calendars; reading
executive or regulator calendars; enumerating the contacts directory; bulk
creation; account administration; unconfirmed deletion; unapproved external
invites.

**Loss ordering.** Disclosure, then availability, then unauthorized modification
overall — metadata disclosure first, deletion second — inverting to modification
first on `operational-commitment-information`, where the entry is a commitment
rather than a description of one.

---

## References

Safeguard numbers and titles were verified against the CIS Controls Assessment
Specification for Controls v8.1, not quoted from recall.

| Safeguard | Verified title | Used here for |
|---|---|---|
| 3.1 | Establish and Maintain a Data Management Process | the scope statement |
| 3.2 | Establish and Maintain a Data Inventory | the coarse register, sensitive data enumerated and the rest merged |
| 3.3 | Configure Data Access Control Lists | the `ACL` column and the access-control-list block |
| 3.7 | Establish and Maintain a Data Classification Scheme | the two-level `Data category` scheme |
| 3.12 | Segment Data Processing and Storage Based on Sensitivity | the `Segment` column |

Control 3 carries 14 safeguards in total (3.1–3.14). The five above are the ones
this document implements; the remainder — retention, disposal, encryption at
rest / in transit / on media, data-flow documentation, DLP, and logging of
sensitive data access — govern controls outside an MCP tool surface and are not
represented in these registers.

Safeguard 3.7 requires only enough levels "to differentiate sensitive data from
other data", which is the textual basis for the two-level scheme used here.

- [CIS Critical Security Control 3: Data Protection](https://www.cisecurity.org/controls/data-protection)
- [CIS Controls Assessment Specification v8.1 — Control 3](https://cas.docs.cisecurity.org/en/latest/source/Controls3/)
