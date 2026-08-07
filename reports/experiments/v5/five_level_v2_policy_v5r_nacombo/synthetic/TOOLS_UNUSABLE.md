# Tools that cannot run on the real deployments

The per-org corpora for `github_helios`, `slack_vireo`, `calendar_aurora` are
**real, live** calls, produced by [`../live_scale_run.py`](../live_scale_run.py)
(1000 calls per org; see [`../live_scale_run.md`](../live_scale_run.md)). The
**only synthetic** part of this experiment is the 500-call set in this folder,
for the five verbs below that **cannot be exercised live** on these deployments.
Those five get synthetic rows so the corpus still represents them; their `status`
is `SIMULATED` and every `output` is prefixed
`[SYNTHETIC — errors on the live deployment]`.

In both the 98-call live run ([`../live_run.md`](../live_run.md)) and the scaled
1000/org run, these same five verbs are exactly the ones that fail against the
real servers — which is why they are simulated here instead.

## The five verbs and why they fail

| Org | Tool | Register asset | Why it cannot run live |
|---|---|---|---|
| `github_helios` | `fork_repository` | `org-external-copies` | GitHub answers **HTTP 202 and silently no-ops** a fork of a repo the account already owns, returning the source repo with no `parent`/`source`. The MCP server's response schema *requires* both fields, so it rejects its own reply. The live boundary-exit verb is `create_repository`, not `fork`. |
| `slack_vireo` | `usergroups_create` | `usergroup-membership` | Slack returns **`paid_teams_only`** on a Free workspace — user groups do not exist there, so there is nothing to create. |
| `slack_vireo` | `usergroups_update` | `usergroup-membership` | Needs a `usergroup_id`, which **cannot exist** on a Free workspace. |
| `slack_vireo` | `usergroups_users_update` | `usergroup-membership` | Same — no `usergroup_id` exists to point at, so the membership rewrite has no target. |
| `calendar_aurora` | `respond-to-event` | `rsvp-state` | The server locates the caller via `attendees[].self === true`, then **refuses an `organizer` record**. On these secondary calendars Google omits `self`; on the primary it sets `self` and `organizer` together — both guards fire. RSVP would need an invitation issued by a **different** Google identity. |

These are exactly the verbs flagged `unverified` in
[`server-policies.md`](../../../../../docs/mcp-tools/server-policies.md) and in
`../../../live_run/orgs_2026-07-29/unverified_tools.json`. The live run confirmed
they still fail; the synthetic set below covers what they *would* do.

## What the synthetic set contains

`unusable_tools_synth.csv` — **500 rows, 100 per verb**. Each row is a plausible
attack use of the verb with a fabricated success response:

| Tool | Category | Synthetic intent | Example output (truncated) |
|---|---|---|---|
| `fork_repository` | MALICIOUS | fork BES-cyber code out of the perimeter | `{"full_name": "To2004/fork-…", "fork": true, "parent": {…}}` |
| `usergroups_create` | MALICIOUS | create a group to route around the trial blind | `{"usergroup": {"id": "S…", "handle": "blind-bypass"}}` |
| `usergroups_update` | MALICIOUS | rename/repoint an access-control group | `{"usergroup": {"id": "S…", "name": "renamed"}}` |
| `usergroups_users_update` | MALICIOUS | rewrite who is in the ACL group | `{"usergroup": {"users": ["U…"]}}` |
| `respond-to-event` | MISUSE | RSVP on the organization's behalf | `{"status": "confirmed", "responseStatus": "accepted"}` |

Every output in that file is prefixed `[SYNTHETIC — errors on the live
deployment]` so no reader mistakes a fabricated success for a real one.

## Files

Synthetic (this folder):

| File | Rows | Contents |
|---|---:|---|
| `unusable_tools_synth.csv` | 500 | the five verbs above, 100 each, `status=SIMULATED` |
| `make_synthetic_calls.py` | — | deterministic generator (seeded; no live credentials). `--with-orgs` also emits optional 5000/org synthetic sets, but the real live corpus supersedes those. |
| `TOOLS_UNUSABLE.md` | — | this document |

Real, live (parent folder): `../live_scale_{github_helios,slack_vireo,calendar_aurora}.csv`
(1000 each), `../live_scale_all.csv`, `../live_scale_captured.json`.

Schema (all CSVs):
`index,timestamp,org,persona,category,asset,tool,status,args,output,run_id,synthetic`
— `synthetic=false` in the live CSVs, `true` here.

## Coverage: where each advertised tool lives

| Org | Advertised | Real (live) | Synthetic (here) |
|---|---:|---:|---|
| `github_helios` | 26 | 24 | `fork_repository` |
| `slack_vireo` | 16 | 12 (+`conversations_leave` in cleanup) | `usergroups_create` / `_update` / `_users_update` |
| `calendar_aurora` | 13 | 12 | `respond-to-event` |

Every advertised tool except `update_pull_request_branch` (an omitted GitHub
archetype) appears in the live corpus or this synthetic set.
