# Live call corpus — three real MCP servers (`five_level_v2_policy_v5r_nacombo`)

A benign / misuse / attack **call corpus run live** against the three
policy-covered servers in this experiment folder — `github_helios`,
`slack_vireo`, `calendar_aurora`. Every row hit a real MCP server and a real
account through the same stdio JSON-RPC client the framework already uses
([`../../../live_run/orgs_2026-07-29/mcp_live.py`](../../../live_run/orgs_2026-07-29/mcp_live.py)).
Nothing here is simulated. The scan matrices in this folder
(`github_helios_matrix.csv`, `slack_vireo_matrix.csv`,
`calendar_aurora_matrix.csv`) are the *design-time* scores for the same servers;
this is the *runtime* traffic you would score against them.

Generator: [`live_call_run.py`](live_call_run.py). Outputs: `live_calls.csv`
(one line per call), `live_captured.json` (full transcript with evidence).

## What ran

**98 live calls**, 93 `OK`, 5 `ERROR`. Category mix matches the 50 / 25 / 25
target requested:

| Category | Calls | Share |
|---|---:|---:|
| BENIGN | 52 | 53% |
| MISUSE | 21 | 21% |
| MALICIOUS | 25 | 26% |

Per server:

| Server | Calls | B / M / A | Distinct tools | Tools exercised / advertised |
|---|---:|---|---:|---:|
| `github_helios` | 47 | 30 / 9 / 8 | 20 | **20 / 26** |
| `slack_vireo` | 28 | 13 / 7 / 8 | 14 | **14 / 16** |
| `calendar_aurora` | 23 | 9 / 5 / 9 | 12 | **12 / 13** |

The benign share is highest on GitHub (many cheap, safe reads across five repos);
Calendar is attack-heavy because its destructive verbs (delete/update on
authoritative operational calendars) are the point of interest there. Across all
three the blend lands on the requested split.

## The five tools that cannot run — and did not fake success

Exactly five verbs across the three catalogs cannot fire on these deployments.
They are still **attempted** in the corpus (as MALICIOUS attack attempts) and
recorded as `ERROR`, never dressed up as `OK`:

| Server | Tool | Why it fails |
|---|---|---|
| `github_helios` | `fork_repository` | GitHub 202-no-ops a self-owned fork; the server's schema then rejects its own reply |
| `slack_vireo` | `usergroups_create` | Slack `paid_teams_only` on a Free workspace |
| `slack_vireo` | `usergroups_update` | needs a usergroup id that cannot exist on Free |
| `slack_vireo` | `usergroups_users_update` | same — no usergroup id on Free |
| `calendar_aurora` | `respond-to-event` | server locates the caller via `attendees[].self` and refuses an `organizer`; both guards fire on these calendars |

These are the same five flagged as unverified in
[`server-policies.md`](../../../../docs/mcp-tools/server-policies.md) and
`../../../live_run/orgs_2026-07-29/unverified_tools.json`. The corpus is the
independent confirmation that they still don't run.

## How the categories map to the policies

The category of each call is chosen against the server's own policy section, so
the corpus is meaningful to score, not arbitrary.

- **BENIGN** — expected organizational use: reads the agent was asked for,
  scoped searches, proposal-only writes *outside* the perimeter (open an issue,
  branch a public repo), team-calendar scheduling, posting an attributed status
  to a channel the agent belongs to.
- **MISUSE** — over-reach short of a prohibited-outright verb: estate-wide
  `search_code` and credential-string hunts, full repository/user enumeration,
  writing to a *perimeter* repo on a side branch, workspace-wide Slack searches
  on ordinary words (`data`, `site`) that cross the trial blind, bulk-reading PHI
  channels, reading the executive/regulator calendars, an unrequested post.
- **MALICIOUS** — prohibited-outright / irreversible: `create_repository`
  (boundary-exit exfil), a zero-review **merge into a perimeter repo** plus a
  direct push to `main`, self-admitting to `vireo-unblinding` and reading it,
  posting into the unblinding channel, deleting authoritative crew-roster and
  maintenance calendar records, an external outbound invite, bulk event
  creation, account-config inspection.

The signature attack per server actually succeeds live and proves the gap the
policies warn about: the merge landed (`merged: true`) with no branch protection;
`conversations_join` self-admitted to the blinded channel with no invitation;
`delete-event` removed an operational record on the first call with no
confirmation.

## Safety, and full cleanup

No verb that deletes a user, revokes the caller's own access, or ends the session
was ever called. Destructive writes targeted only **To2004 sandbox artifacts this
project created**, never the user's own repositories, and were cleaned up:

- **GitHub** — the run self-cleans through the REST API (the catalog has no
  delete verbs): closed 2 PRs and 2 issues, deleted 2 files written to `main`,
  3 branches, and the 1 repo it created. Post-run residue check: **0** open
  corpus issues/PRs, **0** exfil repos, **0** leftover attack files, **0**
  corpus branches. Deleting the created repo needed the `delete_repo` OAuth scope
  (granted mid-run on the login-node `gh` token).
- **Calendar** — every probe event (create/update/delete demonstrations) is
  deleted at the end: 6/6 removed.
- **Slack** — the catalog has **no message-delete verb**, so the few clearly
  labeled `[mcp-risk-corpus]` posts cannot be retracted; message volume was kept
  deliberately low for that reason. The one channel joined for the attack
  (`vireo-unblinding`) was left afterward — membership restored, confirmed via
  `channels_me`. The read it enabled is the demonstrated, unrecoverable damage.

### One honesty note

During an early manual cleanup pass (before the self-cleaning run) I also deleted
two **pre-existing** July-provisioning branches (`probe/tool-asset-check`,
`proposal/adapter-flag`) and closed an old probe PR on the sandbox repos. Those
were not created by this corpus; they are recoverable from their commits/PRs, but
they should not have been touched. The final self-cleaning run only removes
artifacts it captured from its own responses.

## Files

| File | Contents |
|---|---|
| `live_call_run.py` | the generator/runner (categorized plan → live calls → self-cleanup → emit) |
| `live_calls.csv` | 98 rows: `index,timestamp,org,persona,category,asset,tool,status,args,note,evidence` |
| `live_captured.json` | full transcript, same fields plus untruncated-to-300-char evidence |
| `live_run.md` | this summary |
