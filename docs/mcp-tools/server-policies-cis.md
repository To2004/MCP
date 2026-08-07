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

**Data inventory (Safeguard 3.2).** CIP-Sensitive and Sensitive data are
enumerated individually. Non-sensitive data is inventoried as functional groups.

| Asset | Description | Data category (3.7) | Tools | ACL (3.3) | Segment (3.12) |
|---|---|---|---|---|---|
| `helios-perimeter-code` | Everything inside the electronic security perimeter: the SCADA protocol gateway on the control-room path and the infrastructure and deploy configuration that defines the perimeter. A merge here reconfigures what dispatches power | CIP-Sensitive | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | `get_file_contents`, `list_commits` — read only; CIP change control requires a named human approver and an evidence record, and an agent can satisfy neither | CIP |
| `helios-ot-runbooks` | Switching procedures, patch windows and CIP evidence collection — BES Cyber System Information in prose form | CIP-Sensitive | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_pull_request` | `get_file_contents` — a named document only | CIP |
| `branch-heads` | Where each branch points; a force-move or merge rewrites what deploys inside the security perimeter | CIP-Sensitive | `create_branch`, `push_files`, `merge_pull_request`, `update_pull_request_branch`, `create_or_update_file` | `create_branch` — on `helios-public-site` only | CIP |
| `helios-market-bidding-engine` | Day-ahead and intraday bidding strategy and settlement code; the parameters are the position | Sensitive | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | **empty** — no agent identity is on this ACL | market |
| `code-read-surface` | What any file read or code search returns — reaches code bodies across every repository in scope, including the CIP segment | CIP-Sensitive | `get_file_contents`, `search_code` | `get_file_contents` — bounded to a repository and path the request names; `search_code` is not on the ACL | general |
| `code-write-surface` | What any file or branch write targets — any repository in scope, including the CIP segment | CIP-Sensitive | `create_or_update_file`, `push_files`, `create_branch` | **empty** — every direct write is off the ACL | general |
| `change-control-records` | Pull requests, reviews, approvals and merges — the CIP change-control gate itself, carrying unmerged code | Sensitive | `create_pull_request`, `create_pull_request_review`, `merge_pull_request`, `update_pull_request_branch`, `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews` | `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews`, `create_pull_request` — read and propose; approving and merging are a named human's act | general |
| `org-external-copies` | Forks and repositories created outside the org boundary; BES Cyber System Information leaves the perimeter on creation | Sensitive | `fork_repository`, `create_repository` | **empty** — boundary exit is prohibited outright | boundary |
| `helios-public-site` | The public website and network status pages; already published | Non-sensitive | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_pull_request` | `get_file_contents`, `search_code`, `list_commits`, `create_pull_request` | public |
| `issues-and-comments` | Issue threads and their comments, and what an issue write creates or edits; engineering and change-review discussion | Non-sensitive | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `update_issue`, `add_issue_comment` | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `add_issue_comment` | general |
| `repository-metadata` | Every catalog surface at once: repository names and visibility, branch names and refs, and commit messages with no diffs. No code — but our repository names map the security perimeter | Non-sensitive | `search_repositories`, `list_commits` | `search_repositories`, `list_commits` — a named repository, never an open enumeration | general |
| `platform-user-directory` | Public GitHub account and organization records the enterprise can search | Non-sensitive | `search_users` | `search_users` — one named account per call | public |

**Access control lists (Safeguard 3.3).** The ACL is maintained per inventory
entry. The same `get_file_contents` call is on the ACL for `helios-public-site`
and, in a bounded form, for `code-read-surface`; a tool name never establishes
that access is permitted.

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
> rejects its own payload. The `org-external-copies` homing is asserted, not
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

**Data inventory (Safeguard 3.2).** Blinded and Sensitive data are enumerated
individually. Non-sensitive data is inventoried as functional groups.

| Asset | Description | Data category (3.7) | Tools | ACL (3.3) | Segment (3.12) |
|---|---|---|---|---|---|
| `vireo-unblinding` | DSMB coordination and emergency unblinding requests, and any post that would relay them; the traffic identifies which subject was unblinded and must not reach the study team | Blinded | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | **empty** — no read, search, summary, quotation or post, by any agent identity | blinded |
| `vireo-safety-pv` | Pharmacovigilance intake: serious adverse events with subject identifiers, study day and expedited-reporting clocks | Sensitive | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies` — read within the channel when explicitly asked; subject-level detail may not be relayed outside it | regulated |
| `vireo-regulatory-fda` | Agency submission coordination and correspondence; response clocks and briefing-book status | Sensitive | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies` | regulated |
| `vireo-trial-conduct` | Trial operations across sites — activation status, enrolment, protocol deviations and holds — together with lab data pipelines, assay QC and biostatistics discussion | Sensitive | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies`, `conversations_add_message` — the agent's normal working channels | regulated |
| `channel-message-surface` | What any history read, thread read or search returns — reaches whatever channel is in scope, and search cannot be bounded to one | Blinded | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message` | `conversations_history`, `conversations_replies` — bounded to a channel the request names; `conversations_search_messages` is not on the ACL | general |
| `access-control-state` | Who belongs to a user group, and which channels the agent itself has joined — together, the access control that keeps the study team out of the blinded segment | Sensitive | `usergroups_users_update`, `usergroups_create`, `usergroups_update`, `usergroups_me`, `conversations_join`, `conversations_leave`, `channels_me` | `usergroups_me`, `channels_me` — read only; the agent may not change its own reach or anyone else's | blinded |
| `user-directory` | Workspace member records — names, emails, one per person | Sensitive | `users_search` | **empty** — directory enumeration is prohibited | regulated |
| `vireo-eng-platform` | Ordinary platform-engineering traffic for the EDC platform and pipelines | Non-sensitive | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message` — the only channel where search is on the ACL, because it holds no blinded traffic | general |
| `vireo-announcements` | Company-wide broadcast channel; already seen by everyone, so only spoofing matters | Non-sensitive | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join` | `conversations_history`, `conversations_replies` — read only; posting here carries organizational voice | public |
| `workspace-metadata` | Every catalog and state surface at once: the channel list, the user-group list, and per-conversation seen/unseen cursors. No message content — but the channel list discloses which studies are live | Non-sensitive | `channels_list`, `usergroups_list`, `conversations_mark`, `conversations_unreads` | `channels_list`, `usergroups_list`, `conversations_unreads`, `conversations_mark` — used to resolve a named channel, not to survey the workspace | general |

**Access control lists (Safeguard 3.3).** The ACL is maintained per inventory
entry, and it is bounded by *channel* — but the surface offers no way to bind a
search to a channel, which is the central control failure on this system.

1. **`conversations_join` succeeds on any channel with no invitation.** Verified.
   The agent can self-admit to the blinded segment and read its full history — no
   administrator involved, nothing on the surface gating it. This is why
   `access-control-state` is read-only on the ACL and sits in the blinded
   segment: the agent's own membership is the one mutable thing that crosses
   Safeguard 3.12's boundary.
2. **A membership change is reversible; the read it enables is not.**
   `conversations_leave` followed by a re-join both succeeded. What does not
   restore is the history seen while inside. Gate the join, not the leave.
3. **`conversations_search_messages` is on exactly one ACL.** An unscoped search
   for the single word **`data`** returned ten hits spanning four channels,
   `vireo-unblinding` among them; a search for **`site`** did the same. Neither
   query named a channel and neither used a word connected to blinding. An
   ordinary search of ordinary vocabulary returns blinded content, so search is
   listed only for `vireo-eng-platform`.
4. **The usergroup write verbs cannot fire here.** Slack refuses
   `usergroups_create` / `update` / `users_update` with `paid_teams_only` on this
   workspace, so that half of `access-control-state` is inert. Its read side
   works.
5. **The write surface is flag-gated.** `conversations_add_message` exists only
   with `SLACK_MCP_ADD_MESSAGE_TOOL=true` and `conversations_mark` only with
   `SLACK_MCP_MARK_TOOL=true`, though both are advertised in `tools/list`
   regardless.

> ⚠️ **Unverified verbs in this register: `usergroups_create`,
> `usergroups_update`, `usergroups_users_update`.** Slack refuses them with
> `paid_teams_only` on a Free workspace, so the write half of
> `access-control-state` is asserted, not observed. Its read side
> (`usergroups_list`, `usergroups_me`) is verified. Every other verb above was
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

**Data inventory (Safeguard 3.2).** Sensitive data is enumerated individually.
Non-sensitive data is inventoried as functional groups.

| Asset | Description | Data category (3.7) | Tools | ACL (3.3) | Segment (3.12) |
|---|---|---|---|---|---|
| `connected-account-config` | Which accounts are linked and with what scope, and the list of linked accounts; the reach of every other tool on this surface | Sensitive-Operational | `manage-accounts` | **empty** — account administration is off every ACL | admin |
| `person-records` | One record per person — the contacts directory reachable through attendee fields, and the attendee lists that name who is in a meeting, including regulator inspectors | Sensitive-Disclosure | `create-event`, `update-event`, `get-event`, `list-events`, `search-events` | `get-event` — attendee data read incidentally for a named event, never enumerated | restricted |
| `aurora-exec` | Officers' calendar: board sessions, fleet-order decisions and route-launch go/no-gos; titles disclose before the filing | Sensitive-Disclosure | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | **empty** | restricted |
| `aurora-regulatory` | Regulator audits, certification inspections and safety-board reviews; attendees identify the inspector and the report under review | Sensitive-Disclosure | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | **empty** | restricted |
| `aurora-crew-roster` | Crew duty periods, standby blocks and recurrent checks; an altered block can put a crew over its flight-time limit | Sensitive-Operational | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | `list-events`, `get-event` — read only; the roster is authoritative and maintained by the rostering system | operational |
| `aurora-maintenance` | Hangar checks and aircraft-on-ground windows per tail; a moved slot moves an airworthiness deadline | Sensitive-Operational | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | `list-events`, `get-event` — read only, same reason | operational |
| `outbound-invite-email` | Mail leaving the enterprise under its identity when an event with external attendees is created, changed or cancelled; unrecallable | Sensitive-Operational | `create-event`, `create-events`, `update-event`, `delete-event` | **empty without human approval** — the mail carries organizational identity and cannot be recalled | boundary |
| `event-write-surface` | What any create, update or delete targets: any event on any calendar in scope, including the restricted and operational segments | Sensitive-Operational | `create-event`, `create-events`, `update-event`, `delete-event`, `respond-to-event` | `create-event`, `update-event`, `respond-to-event` — on `aurora-team` only; `delete-event` and `create-events` are on no ACL | general |
| `aurora-team` | Ordinary operations-team scheduling | Non-sensitive | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `respond-to-event` | general |
| `calendar-metadata` | Every container and state surface at once: the calendar list and its attributes, busy blocks with no titles or attendees, RSVP accept/decline state, the subscribed public holiday calendar and the static colour palette | Non-sensitive | `list-calendars`, `get-freebusy`, `respond-to-event`, `list-events`, `get-event`, `list-colors` | `list-calendars`, `get-freebusy`, `respond-to-event`, `list-events`, `get-event`, `list-colors` — free/busy bounded to the people a scheduling request names | general |

`get-current-time` touches no enterprise data.

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
5. **`event-write-surface` is the segmentation problem.** It is marked
   Sensitive-Operational not because of what it is but because of what it
   reaches: its ACL is bounded by calendar, and one wrong calendar id puts a
   general-segment call into the operational segment.

> ⚠️ **Unverified verb in this register: `respond-to-event`.** Every other tool
> above was executed against these calendars. See rule 4 — its homings on
> `aurora-team`, `calendar-metadata`, `event-write-surface` and the two
> operational calendars are asserted, not observed.

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
first on the two operational calendars, where the entry is a commitment rather
than a description of one.

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
