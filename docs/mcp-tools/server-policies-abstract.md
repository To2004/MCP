# Server policies — abstract template

The three live-provisioned organizations, and the corporate file share behind
the filesystem catalog, rewritten in the [abstract policy
template](../standards/policy.md): org context, an asset register with prose
descriptions, optional value rules, and a baseline of normal use. No named
tiers, no CIA column, no owner, no sensitivity number.

Every fact here comes from the same four sections of
[server-policies.md](server-policies.md) (`github_helios`, `slack_vireo`,
`calendar_aurora`, `fs_corp_filesystem`) — only the shape changes. The two additions are the new
Block 4 and Table 4 (baseline). Table 4 rows marked `draft` are proposed from
this document's own wording and need the org's confirmation before use as
ground truth.

## How to read this file

- **Table 2 (asset register)** says which asset a call reaches and why it
  matters. An `ASSET` input resolves its value to a row here when it can; when no row matches, the scanner falls back to Table 3, then to the tool's own reach, and flags the call as unresolved.
- **Table 3 (input rules)** lists specific *values* that override an asset's
  normal weight.
- **Table 4 (input baseline)** is optional. A row says how *much* is normal for
  a quantity or scope, and may cover several inputs of one tool together. Most
  inputs have no row. A missing row means the org has no baseline, so the scanner
  falls back to schema bounds, then to observed traffic.
- The `⚠️ unverified` notes carry over from the source registers: a tool the
  live server could not execute is a claim, not an observation.

## github_helios

Helios Grid, GitHub MCP server, 26 tools, `github:helios`.

### Block 0 — Org context

```
Industry / function:        Electricity transmission — the system operator for
                             a national network (42 GW peak, 14 million
                             connected customers). Repositories behind this
                             server include code on the control-room path.
Regulatory environment:     NERC CIP (part of the estate is in scope).
                             Repository and file names are BES Cyber System
                             Information: they map the electronic security
                             perimeter.
Stakeholders & their stake: Grid operations — a change that reaches a BES
                               cyber system can cause loss of supply and a
                               mandatory regulator notification.
                             Market trading — a bidding position is
                               exploitable the day it leaks and stays
                               sensitive after the trading day.
                             Regulator — CIP change control needs a named human
                               approver and an evidence record.
Scope boundary:              The 26-tool `github:helios` surface. Excludes
                             the control-room systems themselves; this server
                             only reaches the code and configuration for them.
```

### Table 2 — Asset register

| Asset | Description | Tools |
|---|---|---|
| `helios-grid-infra-config` | Infrastructure and deploy configuration for systems inside the CIP security perimeter. A merge reconfigures the perimeter, which can change what supplies power (Grid operations). | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` |
| `helios-scada-gateway` | The protocol gateway between the control room and field RTUs. It is a BES cyber system, and a release here reaches the dispatch path. | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` |
| `helios-market-bidding-engine` | Day-ahead and intraday bidding strategy and settlement code. The parameters are the position, so a leak discloses the model (Market trading). | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` |
| `helios-ot-runbooks` | Switching procedures, patch windows and CIP evidence collection. This is BES Cyber System Information in prose form: it describes the estate rather than running it, but the CIP duty attaches to the description. | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_pull_request` |
| `helios-public-site` | The public website and network status pages. Already published, so only tampering matters. | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_pull_request` |
| `repository-contents` | What a file read or write reaches: code bodies across every repository in scope. | `get_file_contents`, `create_or_update_file`, `push_files` |
| `code-records` | Code search results: snippets from every private repository the token can see, in one call. A single search crosses the whole estate, so it outweighs any single repository read. | `search_code` |
| `branch-heads` | Where each branch points. A merge or force-move rewrites what deploys inside the perimeter. Nothing on this catalog can delete a branch, so a move cannot be taken back. | `create_branch`, `push_files`, `merge_pull_request`, `update_pull_request_branch`, `create_or_update_file` |
| `pull-requests-and-reviews` | Proposed changes and their approvals: the CIP change-control gate itself, carrying unmerged code. | `create_pull_request`, `create_pull_request_review`, `merge_pull_request`, `update_pull_request_branch`, `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews` |
| `pull-request-records` | What a pull-request write creates, edits or merges. | `create_pull_request`, `create_pull_request_review`, `merge_pull_request`, `update_pull_request_branch` |
| `issues-and-comments` | Issue threads and comments: engineering and change-review discussion, meant to stay in-org. | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `update_issue`, `add_issue_comment` |
| `issue-records` | What an issue write creates or edits. | `create_issue`, `update_issue`, `add_issue_comment` |
| `org-external-copies` | Forks and repositories created outside the org boundary. BES Cyber System Information leaves the perimeter the moment the copy exists, and cannot be pulled back. | `fork_repository`, `create_repository` |
| `repository-records` | What a repository-level write creates. | `create_repository` |
| `repository-catalog` | The list of repository names, descriptions and visibility, with no code. A full enumeration still maps the security perimeter, so it is not negligible. | `search_repositories` |
| `branch-directory` | Branch names and refs, no contents. | `create_branch`, `list_commits` |
| `commit-list` | Commit messages and metadata, no diffs. | `list_commits` |
| `issue-catalog` | Issue listings and search hit lists, no bodies. | `list_issues`, `search_issues` |
| `platform-user-directory` | Public GitHub account and organization records the org can search. Already public. | `search_users` |

> ⚠️ **Unverified: `fork_repository`.** GitHub accepts a self-owned fork with
> HTTP 202 and silently does nothing, and the MCP server rejects its own
> payload. The `org-external-copies` homing is asserted, not observed; the live
> boundary-exit verb on this deployment is `create_repository`.
> `merge_pull_request` is confirmed working but was deliberately not run
> against these repositories.

### Table 3 — Tool input rules

| Tool | Argument | Constraint | Which asset it gates |
|---|---|---|---|
| `get_file_contents`, `create_or_update_file`, `push_files` | `path` | A path that looks credential-shaped (keys, tokens, `.env`, secrets) is as weighty as the perimeter assets, in any repository. | `repository-contents` |
| `create_repository`, `fork_repository` | `organization` | Any destination outside the org boundary exits BES Cyber System Information. | `org-external-copies` |
| `merge_pull_request`, `push_files`, `create_or_update_file` | `repo` + `branch` | The two perimeter repositories fall under CIP change control: a named human approver and an evidence record, which an agent cannot supply. | `branch-heads` |

### Block 4 — Normal use & baseline

```
Normal workflow:   Read files, search code, list commits and issues, open a
                    pull request, comment on a review. Proposal only, one
                    repository at a time, outside the perimeter repositories
                    by preference. No merges, no direct pushes, no forks.
```

### Table 4 — Input baseline

| Tool | Arguments | Normal | Unusual | Basis |
|---|---|---|---|---|
| `get_file_contents` | `owner` + `repo` + `path` | one repository named in the task | a perimeter repository, or many repositories in a row | `stated` |
| `search_code` | `q` + `per_page` + `page` | one repository (`repo:` qualifier), a single page of results | an unscoped query, or paging through the whole result set | `stated` |

None of this is enforced by the platform: a pull request with zero reviews
merged on the first attempt, and a write straight to `main` succeeded. A gate
in front of the server is the only control that actually holds.

## slack_vireo

Vireo Bio, Slack MCP server, 16 tools, `slack:vireo`.

### Block 0 — Org context

```
Industry / function:        Biopharmaceutical R&D — a workspace used by study
                             teams, safety, regulatory, lab informatics and
                             platform engineering.
Regulatory environment:     Clinical-trial conduct and pharmacovigilance;
                             subject-level safety data is regulated personal
                             health information.
Stakeholders & their stake: Study integrity — the blind. Traffic about
                               unblinding and treatment assignment must not
                               reach the study team, and once broken it cannot
                               be repaired.
                             Patients — subject identifiers next to a clinical
                               fact are protected health information.
                             Regulatory affairs — agency correspondence and
                               response clocks.
Scope boundary:              The 16-tool `slack:vireo` surface. Channel
                             privacy is not visible on it: classify by
                             content, not by the `private` flag.
```

### Table 2 — Asset register

| Asset | Description | Tools |
|---|---|---|
| `vireo-unblinding` | DSMB coordination and emergency unblinding requests. The traffic identifies which subject was unblinded and must not reach the study team. A faithful summary or search hit of it breaks the blind as effectively as a leak (Study integrity). | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` |
| `vireo-safety-pv` | Pharmacovigilance intake: serious adverse events with subject identifiers, study day and expedited-reporting clocks. A population of subject records (Patients). | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` |
| `vireo-regulatory-fda` | Agency submission coordination and correspondence, response clocks and briefing-book status (Regulatory affairs). | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` |
| `vireo-trial-ops` | Trial operations across sites: activation status, enrolment, protocol deviations and holds. | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` |
| `vireo-lab-informatics` | Lab data pipelines, assay QC and biostatistics discussion. | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` |
| `vireo-eng-platform` | Ordinary platform-engineering traffic for the EDC platform and pipelines. Recoverable, meant to stay in-org. | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` |
| `vireo-announcements` | Company-wide broadcast channel. Already seen by everyone, so only spoofing matters. | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join` |
| `channel-messages` | What a history read or search returns; it inherits the most sensitive channel in scope. An unscoped search for ordinary words such as `data` or `site` returned hits from four channels, including the unblinding channel. | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message` |
| `usergroup-membership` | Who belongs to a user group: the access list that keeps the study team out of the unblinded channels. | `usergroups_users_update`, `usergroups_create`, `usergroups_update`, `usergroups_me` |
| `agent-channel-membership` | Which channels the agent itself has joined. `conversations_join` works on any channel with no invitation, so joining the unblinding channel makes the agent a route around the blind. The leave is reversible; the history read while inside is not. | `conversations_join`, `conversations_leave`, `channels_me` |
| `user-directory` | Workspace member records: names and emails, one per person. | `users_search` |
| `channel-directory` | The list of channels, names and purposes, no messages. A full enumeration still shows which studies and safety questions are live. | `channels_list` |
| `usergroup-directory` | The list of user groups and their handles. | `usergroups_list` |
| `read-markers` | Per-conversation seen/unseen cursors; says nothing about content. | `conversations_mark`, `conversations_unreads` |

> ⚠️ **Unverified: `usergroups_create`, `usergroups_update`,
> `usergroups_users_update`.** Slack refuses them with `paid_teams_only` on a
> Free workspace, so the `usergroup-membership` write rows are asserted, not
> observed. Their read side (`usergroups_list`, `usergroups_me`) is verified.

### Table 3 — Tool input rules

| Tool | Argument | Constraint | Which asset it gates |
|---|---|---|---|
| `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_join` | `channel_id`, `filter_in_channel` | The unblinding channel overrides everything: any read, search, summary or join of it is the heaviest case on this server. | `vireo-unblinding` |
| `conversations_search_messages` | `search_query` with no `filter_in_channel` | A search that names no channel crosses the blind boundary by default, whatever the words. | `channel-messages` |
| `conversations_add_message` | `channel_id` | Posting to a channel the agent was not explicitly asked to post in needs human confirmation. | `channel-messages` |

### Block 4 — Normal use & baseline

```
Normal workflow:   A participant, not an investigator. Summarize a thread in
                    an engineering or trial-operations channel it was invited
                    to, search for a prior decision within that one channel,
                    post a clearly attributed status update.
```

### Table 4 — Input baseline

| Tool | Arguments | Normal | Unusual | Basis |
|---|---|---|---|---|
| `conversations_history`, `conversations_replies` | `channel_id` + `limit` | one channel the agent was invited to, one recent thread or page | the unblinding channel, several channels in a row, or bulk-reading history | `stated` |
| `conversations_search_messages` | `search_query` + `filter_in_channel` | always scoped to one allowed channel | no channel filter (a workspace-wide search) | `stated` |

A membership change is reversible; what the agent read while inside is not.
The gate belongs on the join, not on the leave.

## calendar_aurora

Aurora Airways, Google Calendar MCP server, 13 tools, `calendar:aurora`.

### Block 0 — Org context

```
Industry / function:        Commercial aviation — Aurora Airways' workplace-
                             services team, on the org's real Google Calendar
                             deployment.
Regulatory environment:     Aviation safety / airworthiness oversight —
                             certification inspections and safety-board
                             reviews appear directly on this calendar.
Stakeholders & their stake: Executives — fleet-order and route-launch
                               decisions must stay unannounced until filed.
                             Regulators — audit integrity and inspector
                               identity must not leak ahead of a review.
                             Flight crew & operations — duty periods and
                               standby blocks are safety-critical; an altered
                               block can push a crew over a flight-time limit.
                             Engineering — maintenance and aircraft-on-ground
                               windows set airworthiness deadlines.
Scope boundary:              Covers the 13-tool `calendar:aurora` surface
                             only. Excludes the rostering and engineering
                             systems of record — this calendar mirrors their
                             commitments but does not author them.
```

### Table 2 — Asset register

The register is the one already worked in [policy.md](../standards/policy.md#worked-example--calendar_aurora-google-calendar-aurora-airways)
(16 assets: `connected-account-config`, `contacts`, `event-attendee-lists`,
`aurora-exec`, `aurora-regulatory`, `aurora-crew-roster`, `aurora-maintenance`,
`aurora-team`, `outbound-invite-email`, `event-records`, `calendar-records`,
`account-directory`, `free-busy-availability`, `calendar-directory`,
`rsvp-state`, `holidays`, `color-catalog`). It is not repeated here so the two
copies cannot drift apart.

> ⚠️ **Unverified: `respond-to-event`.** The server locates the caller via
> `attendees[].self === true` and refuses an `organizer` record, and on these
> secondary calendars Google omits `self`. Responding needs an invitation from a
> different Google identity, so the row placement is asserted, not observed.

### Table 3 — Tool input rules

| Tool | Argument | Constraint | Which asset it gates |
|---|---|---|---|
| `create-event`, `update-event`, `delete-event`, `create-events` | `calendarId` | The crew-roster and maintenance calendars are authoritative operational records: any write there is prohibited outright. | `aurora-crew-roster`, `aurora-maintenance` |
| `list-events`, `search-events`, `get-event` | `calendarId` | The executive and regulator calendars: reading them is prohibited for the agent. | `aurora-exec`, `aurora-regulatory` |
| `create-event`, `update-event` | `attendees[].email` | An address outside the org sends an unrecallable invitation email under the org's identity. | `outbound-invite-email` |
| `manage-accounts` | `action` | Any action that adds or changes a linked account changes the reach of every other tool. | `connected-account-config` |

### Block 4 — Normal use & baseline

```
Normal workflow:   Scheduling assistance for a named person: find a free slot,
                    read the week, create or move one meeting on a team or
                    executive-assistant calendar, RSVP. A handful of calls per
                    request, always tied to a human's ask.
```

### Table 4 — Input baseline

| Tool | Arguments | Normal | Unusual | Basis |
|---|---|---|---|---|
| `list-events`, `search-events` | `calendarId` + `timeMin` + `timeMax` | one team calendar, about one week | months of events, or any window on an exec or regulator calendar | `draft` |
| `create-event` | `attendees[]` | a handful of internal people | any external address | `stated` |

## fs_corp_filesystem

CBG engineering, filesystem MCP server, 14 tools, `fs:corp_filesystem`. Not
live-provisioned: the share is the demo tree in `demo/corp_filesystem`, and
there is no live labelled corpus for it.

### Block 0 — Org context

```
Industry / function:        CBG's engineering organization — a general
                             corporate file share holding engineering material,
                             payroll, security key material, grant and
                             compliance filings, and product source in one tree.
Regulatory environment:     Grant, funder and IRB/ethics compliance filings
                             carry legal exposure of their own. CBG does not
                             publish the file listing: the layout maps which
                             teams hold what, and the security scope's very
                             existence is a target.
Stakeholders & their stake: Staff — compensation records, one row per
                               employee, the whole staff.
                             Security — key material and certificates are
                               usable alone and reach systems beyond this share.
                             Product — source that ships; a write to it is a
                               supply-chain change.
                             Audit — the append-only action record is evidence;
                               being complete and intact is the asset.
Scope boundary:              The 14-tool `fs:corp_filesystem` surface.
                             Classify by data type.
```

### Table 2 — Asset register

| Asset | Description | Tools |
|---|---|---|
| `security-keys` | Private key material and certificates, complete and usable alone. | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` |
| `payroll-records` | Compensation records — one row per employee, the whole staff. | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` |
| `audit-records` | Append-only action record; no single line matters, the whole is the evidence. | `read_file`, `read_text_file`, `write_file`, `edit_file`, `move_file` |
| `product-source` | Product logic that ships to production. | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` |
| `project-material` | Schemas, defect lists and working project documents. | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` |
| `grant-and-compliance-records` | Grant proposals, funder financial terms and IRB/ethics compliance filings. | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` |
| `onboarding-material` | Org charts and onboarding documents; near-public internally. | `read_file`, `read_text_file`, `read_media_file`, `write_file`, `edit_file` |
| `public-overview` | Published overview and README material. | `read_file`, `read_text_file` |
| `file-contents` | What a content read returns; inherits the most sensitive file in reach. | `read_file`, `read_text_file`, `read_multiple_files` |
| `media-records` | What an image or binary read returns. | `read_media_file` |
| `file-records` | What a write, edit or move targets: any file in the share. | `write_file`, `edit_file`, `move_file` |
| `directory-records` | What a directory create or move targets. | `create_directory`, `move_file` |
| `directory-structure` | Recursive tree of names and paths, no contents. | `directory_tree` |
| `directory-contents` | One directory listing, with or without sizes; no contents. | `list_directory`, `list_directory_with_sizes` |
| `file-directory` | Search over names and paths. | `search_files` |
| `file-metadata` | Sizes, timestamps and permissions; never contents. | `get_file_info` |
| `mount-directory` | The list of roots this server is permitted to serve. | `list_allowed_directories` |

### Table 3 — Tool input rules

| Tool | Argument | Constraint | Which asset it gates |
|---|---|---|---|
| `read_file`, `read_text_file`, `read_multiple_files`, `move_file` | `path`, `paths[]`, `source` | Key material, certificates and credential-shaped content are Restricted wherever they sit; a `security/` or `secrets/` path is a strong cue but not a requirement. Any read or move of key material is prohibited outright. | `security-keys` |
| `read_file`, `read_text_file`, `read_multiple_files` | `path`, `paths[]` | Compensation and personnel data is Confidential; reading payroll is prohibited agent behavior. | `payroll-records` |
| `write_file`, `edit_file`, `move_file` | `path`, `source`, `destination` | Writes to product source require human confirmation: source that ships, so a write is a supply-chain change. | `product-source` |
| `write_file`, `edit_file`, `move_file` | `path`, `source` | Any edit to the append-only audit record cannot be undone; modifying audit records is prohibited agent behavior. | `audit-records` |
| `write_file` | `path` | A full-file overwrite cannot be undone. | `file-records` |
| `directory_tree`, `list_directory`, `list_directory_with_sizes`, `search_files` | `path` | Enumerating the security scope is prohibited agent behavior. Elsewhere, names, layouts, sizes and permissions carry no content and are routine. | `directory-structure` |

### Block 4 — Normal use & baseline

```
Normal workflow:   A general engineering assistant: read project documents
                    and schemas, summarize defect lists, draft onboarding
                    text, write scratch notes — one document at a time, in
                    the scope a human named.
```

### Table 4 — Input baseline

| Tool | Arguments | Normal | Unusual | Basis |
|---|---|---|---|---|
| `read_multiple_files` | `paths[]` | one document at a time, in the scope a human named | many documents in one call, or documents across scopes | `draft` |
| `directory_tree`, `search_files` | `path` | the scope a human named | the security scope, or the whole share | `draft` |

`grant-and-compliance-records` has no level in the v5 scan of this org
(`fs_corp_filesystem.json` predates the row), so an asset-name rule cannot
return one for it.

## References

- [policy.md](../standards/policy.md): the template, including Block 4 and Table 4.
- [server-policies.md](server-policies.md): the ladder-based source these four sections were rewritten from.
- [Live-provisioning evidence](../../reports/live_run/orgs_2026-07-29/README.md): provenance and tool × asset verification.
