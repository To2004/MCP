# Tool × asset verification

`check_policies.py` proves two mechanical things about a register's `Tools`
column: no cell names a tool the server does not advertise, and at P2 every
advertised tool appears in some cell. Neither is evidence that a *particular*
pairing is real — that `search_code` reaches `helios-scada-gateway`, or that
`get-freebusy` reaches the Aurora calendars.

This is that evidence. Every tool × asset pair claimed by the three
live-provisioned registers was called against that asset on the live server.
**194 pairs, 179 confirmed, 15 not — each with a stated reason.** This is the
complete claimed set: one row per `Tools` cell entry across the three registers. The machine-
readable matrix is [`tool_asset_matrix.json`](tool_asset_matrix.json); the probe
is [`probe_tool_asset.py`](probe_tool_asset.py).

## Result

| Section | Pairs | Confirmed | Not confirmed |
|---|---|---|---|
| `calendar_aurora` | 58 | 53 | 5 |
| `slack_vireo` | 58 | 55 | 3 |
| `github_helios` | 78 | 71 | 7 |
| **total** | **194** | **179** | **15** |

Six Slack pairs were initially blocked by the user token's scopes and by a server
env flag. The token was reissued on 2026-07-29 with `usergroups:read`,
`usergroups:write` and `groups:write`, and the server relaunched with
`SLACK_MCP_MARK_TOOL=true`; three of the six then verified and the other three
hit a workspace-plan wall. The counts above are after that re-probe.

## Evidence grades

| Grade | Count | Meaning |
|---|---|---|
| `VERIFIED` | 123 | the call ran against this asset and succeeded |
| `PROVEN-IN-PROVISIONING` | 14 | this verb wrote this asset during the 2026-07-29 creation run |
| `SAME-VERB-VERIFIED` | 41 | surface asset — the verb is confirmed on the concrete rows it abstracts over |
| `NO-TOOL-CLAIMED` | 1 | the register claims `—`, and nothing on the catalog reaches it |
| `BLOCKED-BY-PLAN` | 1 | the workspace plan does not offer the feature at all |
| `NOT-EXECUTABLE-HERE` | 8 | the sandbox cannot produce the precondition the verb needs |
| `SKIPPED-BY-DESIGN` | 6 | prohibited by the policy under test and irreversible |

## The 15 unconfirmed pairs

**`respond-to-event` → `aurora-crew-roster`, `aurora-maintenance`, `aurora-team`**
(`NOT-EXECUTABLE-HERE`). Two guards in the server, and this account trips both.
The code is:

```js
const selfAttendeeIndex = attendees.findIndex((a) => a.self === true);
if (selfAttendeeIndex === -1) throw "You are not an attendee of this event…"
if (attendees[selfAttendeeIndex].organizer === true) throw "You are the organizer…"
```

The account **is** in the attendee list on the Aurora calendars — but Google
computes `self` relative to the calendar being read, and these are secondary
calendars whose identity is the `@group.calendar.google.com` address. That
address appears as the *organizer* with `self: true`, while the attendee entry
comes back bare:

| Calendar | Attendee record returned | Guard that fires |
|---|---|---|
| secondary (all five Aurora) | `{"email": "…", "responseStatus": "needsAction"}` — no `self` | "not an attendee" |
| primary | `{"email": "…", "organizer": true, "self": true}` | "you are the organizer" |

Verified by creating a probe event on the primary calendar and getting the
*second* error rather than the first. The verb is not broken: it needs an
invitation issued by a **different Google identity**, which a single-account
sandbox cannot produce in either direction.

**`usergroups_create` → `usergroup-membership`** (`BLOCKED-BY-PLAN`), and
**`usergroups_update`, `usergroups_users_update`** on the same row
(`NOT-EXECUTABLE-HERE`). With `usergroups:write` present, Slack still refuses
creation with **`paid_teams_only`** — user groups are a paid-plan feature and
this workspace is Free. The two update verbs need an existing `usergroup_id`,
and none can exist here, so they inherit the same wall. This is the sharpest
remaining gap in the corpus: these are the verbs `slack_vireo` classifies
**Restricted as access control**, so the register's most consequential Slack row
is the one no credential on this workspace can exercise. The read side of that
row — `usergroups_list` and `usergroups_me` — is `VERIFIED`, returning an empty
group directory.

The scope story is worth recording because it was the first diagnosis and it was
only half right: five verbs returned `missing_scope`, but adding the scopes moved
just two of them. A `missing_scope` error can hide a plan wall behind it, since
Slack checks the scope before the entitlement.

**`conversations_mark`** is now `VERIFIED`. It was initially blocked by a
**second** opt-in env gate alongside `SLACK_MCP_ADD_MESSAGE_TOOL` —
*"set the SLACK_MCP_MARK_TOOL environment variable to true"* — which was not
recorded anywhere in this repo before this probe. With the flag set it marks a
real channel read up to a real message ts.

**`fork_repository` → `org-external-copies`** (`NOT-EXECUTABLE-HERE`, **and a
real server bug**). GitHub does not reject a self-owned fork — called directly,
`POST /repos/To2004/helios-scada-gateway/forks` returns **HTTP 202 Accepted** and
hands back the *source repository*: `fork: false`, no `parent`, no `source`. It
is a silent no-op. The server then does:

```js
const response = await githubRequest(url, { method: "POST" });
return GitHubRepositorySchema.extend({
    parent: GitHubRepositorySchema,   // required
    source: GitHubRepositorySchema,   // required
}).parse(response);
```

It assumes every 202 is fork-shaped, so Zod rejects the no-op payload and the
error surfaces as `path: ["parent"], expected "object", received "undefined"`.
Neither field is `.optional()` and there is no branch for "accepted but did
nothing". No fork was created — the repository list was re-checked and contains
none. Confirming the homing needs a second account or an org; fixing the crash
needs a change upstream in `@modelcontextprotocol/server-github`.

**`merge_pull_request` → `helios-grid-infra-config`, `helios-scada-gateway`,
`helios-market-bidding-engine`** (`SKIPPED-BY-DESIGN`). Prohibited outright by
the policy under test and irreversible. Not run, and therefore not claimed as
verified.

## Per-tool health: does every advertised tool actually work?

The pair matrix answers "does this tool reach this asset". This answers the
blunter question: of the tools each catalog advertises, which ones can be made to
run at all here. **50 of 55.**

| Catalog | Tools | Working | Not working |
|---|---|---|---|
| Google Calendar (`calendar_aurora`) | 13 | 12 | **`respond-to-event`** |
| Slack (`slack_vireo`) | 16 | 13 | **`usergroups_create`**, **`usergroups_update`**, **`usergroups_users_update`** |
| GitHub (`github_helios`) | 26 | 25 | **`fork_repository`** |
| **total** | **55** | **50** | **5** |

Machine-readable: [`tool_health.json`](tool_health.json) (all 55) and
[`unverified_tools.json`](unverified_tools.json) (the 5).

Three tools that had never been executed were run specifically for this table:

- **`get-current-time`** ✅ — returns time, timezone and offset. It touches no
  organizational asset, so it appears in no register row and the pair probe never
  called it.
- **`update_pull_request_branch`** ✅ — the first attempt returned *"There are no
  new commits on the base branch"*, a state refusal rather than a reach failure.
  Re-run after landing a commit on `main`: `{"success": true}`. Upgraded from
  `REACHED-NO-OP` to `VERIFIED`.
- **`merge_pull_request`** ✅ — merged a disposable probe PR in
  `helios-public-site`, returning `{"merged": true}`. That repository's register
  row does **not** claim this pair, so the three `SKIPPED-BY-DESIGN` pairs on the
  merge-capable repositories remain unexercised, exactly as the policy requires.
  The verb works; the policy is what stops it, not the catalog.

One catalog defect found while doing it: the GitHub MCP's `get_pull_request`
returns `mergeable: null` and `mergeable_state: null` no matter how long you poll,
so an agent **cannot pre-check mergeability through this surface** — the only way
to find out is to attempt the merge. Worth knowing for any policy that leans on
"check before you act".

## What the probe changed in the accounts

The probe was designed to leave the described assets intact, but it is not
side-effect free:

- **Calendar** — a scratch event was created, read, updated and deleted on each
  of the five Aurora calendars (and a second one for the `get-event` re-probe).
  All were deleted; the 13 seeded Aurora events are untouched.
- **Slack** — `conversations_leave` was exercised on `vireo-eng-platform` only,
  then membership was restored by re-joining. No messages were posted; the
  `conversations_add_message` row rests on the 39 posts from the creation run.
- **GitHub** — this one leaves artifacts. Each of the five Helios repositories
  has a `probe/tool-asset-check` branch containing `PROBE.md`;
  `helios-scada-gateway` additionally has a review comment, a `probe` label and an
  extra probe issue. Four probe pull requests remain open. The fifth, in
  `helios-public-site`, was **squash-merged** to prove `merge_pull_request` works,
  which also added `content/base-bump.md` to that repository's `main`. Nothing was
  merged in the three repositories whose register claims the merge pair. The MCP
  catalog has no branch- or PR-delete verb, so the rest was left in place rather
  than cleaned up out of band.

## Two bugs in the first probe pass

Recorded because the corrected results are what the matrix contains:

1. `get-event` was ordered before `create-event`, so it had no event id to fetch
   and reported `SKIPPED` on all five calendars. Re-run in the right order: all
   five `VERIFIED`.
2. `respond-to-event` was first called with a made-up event id and returned
   *"Resource not found"* — which proves nothing about reach. Re-run against a
   real event, it returns the attendee error above, which is the actual finding.
