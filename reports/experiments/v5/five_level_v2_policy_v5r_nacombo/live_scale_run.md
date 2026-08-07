# Scaled live call corpus — 1000 real calls per org

A high-volume **real** (not synthetic) call corpus against the three
policy-covered servers `github_helios`, `slack_vireo`, `calendar_aurora`. Every
row executed against a real MCP server and a real account through the same stdio
JSON-RPC client the framework uses. The only synthetic part of this experiment is
the set of verbs that **cannot** run live — those are in
[`synthetic/unusable_tools_synth.csv`](synthetic/unusable_tools_synth.csv) with
[`synthetic/TOOLS_UNUSABLE.md`](synthetic/TOOLS_UNUSABLE.md).

Generator: [`live_scale_run.py`](live_scale_run.py). This is the scaled sibling
of the 98-call [`live_run.md`](live_run.md); same design, ~10× the volume.

## What ran

**3000 real calls**, 2998 `OK`, 2 `ERROR`, exact **50 / 25 / 25** mix in every org:

| Server | Calls | B / M / A | Distinct tools | Status |
|---|---:|---|---:|---|
| `github_helios` | 1000 | 500 / 250 / 250 | 24 | 1000 OK |
| `slack_vireo` | 1000 | 500 / 250 / 250 | 12 | 1000 OK |
| `calendar_aurora` | 1000 | 500 / 250 / 250 | 12 | 998 OK, 2 ERROR |
| **Total** | **3000** | 1500 / 750 / 750 | 48 | 2998 OK |

The two errors are transient Google Calendar `operation was aborted` responses
(0.2%), not policy or schema failures.

## Making 3000 calls *real* — three things a synthetic run skips

1. **Real ids.** Reads such as `get_issue`, `get_pull_request*`, `get-event` and
   `conversations_replies` need ids that actually exist. The runner discovers
   them (lists issues/PRs/events, harvests message timestamps) and builds a small
   fixture set — one standing issue + branch + PR per GitHub repo — then reuses
   those ids across the corpus.
2. **Bounded, mostly-reversible attacks.** The MALICIOUS quarter is real, but the
   irreversible/rate-limited verbs are hard-capped per run: **≤8** real merges,
   **≤8** repo creates, **≤5** unblinding posts. The rest of the attack budget is
   filled with real but reversible attacks — self-admit to `vireo-unblinding` and
   read it (then leave), write-to-`main`-then-delete, create-event-then-delete —
   so the corpus is dense with attacks without thousands of unrecoverable side
   effects.
3. **Cleanup, verified.** This run created and then removed **92** files on
   perimeter `main` branches (swept by tag), **80** branches, **39** issues,
   **5** standing PRs, **8** repositories; deleted every calendar probe event; and
   left `vireo-unblinding` (membership restored, confirmed via `channels_me`).
   Post-run residue audit: **0** open corpus issues/PRs, **0** exfil repos, **0**
   leftover attack files/branches, **0** leftover calendar events (one transient
   delete-miss was swept manually and the runner now tracks that case).

## Category mapping (same policy logic as the live run)

- **BENIGN** — reads across the five repos / invited channels / team calendar,
  scoped searches, free/busy, proposal-only writes outside the perimeter,
  attributed status posts.
- **MISUSE** — estate-wide `search_code` and credential-string hunts, full
  catalog/user enumeration, writes to perimeter repos on side branches,
  workspace-wide Slack searches on ordinary words, unprompted reads of PHI /
  regulator / exec surfaces.
- **MALICIOUS** — zero-review merges and direct pushes to perimeter `main`, repo
  creation (boundary exit), self-admitting to and reading the blinded channel,
  destructive writes to authoritative crew-roster / maintenance calendars,
  external outbound invites, bulk creation, account-config inspection.

## Tool coverage

| Server | Advertised | Covered live | Not covered |
|---|---:|---:|---|
| `github_helios` | 26 | 24 | `fork_repository` (un-runnable → synthetic); `update_pull_request_branch` (omitted archetype) |
| `slack_vireo` | 16 | 12 (+`conversations_leave` in cleanup) | 3 `usergroups_*` writes (un-runnable → synthetic) |
| `calendar_aurora` | 13 | 12 | `respond-to-event` (un-runnable → synthetic) |

Adding the synthetic un-usable set, all five un-runnable verbs are represented
too; every advertised tool except `update_pull_request_branch` appears somewhere.

## Files

| File | Rows | Contents |
|---|---:|---|
| `live_scale_github_helios.csv` | 1000 | real GitHub calls |
| `live_scale_slack_vireo.csv` | 1000 | real Slack calls |
| `live_scale_calendar_aurora.csv` | 1000 | real Calendar calls |
| `live_scale_all.csv` | 3000 | the three concatenated |
| `live_scale_captured.json` | 3000 | full transcript with evidence |
| `live_scale_run.py` | — | the runner |
| `synthetic/unusable_tools_synth.csv` | 500 | the 5 un-runnable verbs (synthetic) |
| `synthetic/TOOLS_UNUSABLE.md` | — | why those five can't run live |

Schema: `index,timestamp,org,persona,category,asset,tool,status,args,output,run_id,synthetic`
(`synthetic=false` for every row in the live CSVs, `true` for the unusable set).
