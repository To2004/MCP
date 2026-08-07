# Three organizations, provisioned live (2026-07-29)

The assets behind the three live-provisioned sections of
[server-policies.md](../../../docs/mcp-tools/server-policies.md). Every asset in
those registers exists: it was created through the real MCP servers against real
accounts, then read back through the same servers.

Each organization is paired with **one real vendor catalog** — the surface where
its regulatory logic bites hardest:

| Org | Domain | Regulatory anchor | Policy section | Its assets |
|---|---|---|---|---|
| **Helios Grid** | electricity transmission | NERC CIP, BES cyber system information | `github_helios` | 5 repositories |
| **Vireo Bio** | biopharmaceutical R&D | FDA 21 CFR Part 11, ICH-GCP, trial blinding | `slack_vireo` | 7 channels |
| **Aurora Airways** | commercial aviation | EASA/FAA operating certificate, just-culture safety reporting | `calendar_aurora` | 5 calendars |

**Surplus assets.** The provisioning run created all three orgs on all three
surfaces (15 repos, 21 channels, 15 calendars) before the corpus was narrowed to
one catalog per org. The 10 repositories, 14 channels and 10 calendars belonging
to the other pairings still exist in the accounts but no policy section covers
them. They are listed in `github_repos.json`, `slack_channels.json` and
`calendars.json`; nothing reads them.

## What actually ran

| Server | Package | Tools live | Creation calls | Read-back calls |
|---|---|---|---|---|
| GitHub | `@modelcontextprotocol/server-github` | 26 | 57 | 10 |
| Slack | `slack-mcp-server` | 16 (15 without `SLACK_MCP_ADD_MESSAGE_TOOL=true`) | 39 | 5 |
| Google Calendar | `@cocal/google-calendar-mcp` | 13 | 36 | 4 |

Every call returned success. The read-back pass re-read the assets through the
same servers — repository search returns `total_count: 15`, the three seeded
pull requests and issues come back open, calendar events return with their
attendee records, and Slack history returns the posted messages.

## Where the containers came from

Two of the three catalogs cannot create their own containers, which is itself a
register fact:

- **GitHub** — everything is MCP-native: `create_repository`,
  `create_or_update_file`, `create_branch`, `create_pull_request`,
  `create_issue`. Nothing was merged; no pre-existing repository was touched.
- **Slack** — the 16-tool catalog has no channel-create verb, so the 21 channels
  were provisioned through `conversations.create` on the Web API
  ([slack_create_channels.py](slack_create_channels.py)); all 39 messages were
  then written through the MCP's `conversations_add_message`.
- **Google Calendar** — the 13-tool catalog reads the calendar list but cannot
  create a calendar, so the 15 calendars were provisioned through the Calendar
  API ([calendar_create.py](calendar_create.py)); all 36 events were written
  through the MCP's `create-event`.

## Provisioning caveats the policies reflect

- **Slack channels are public.** At provisioning time the user token carried
  `channels:write` but not `groups:write`, so `is_private=true` failed with
  `missing_scope`. `slack_vireo` therefore does **not** use the `private` flag as
  a classification cue — it classifies by the content a channel carries.
  Verified, not assumed. *(The token was later reissued with `groups:write`, so
  private channels are now creatable; the seven Vireo channels remain public and
  the section is written against that.)*
- **GitHub repositories are all private**, including the three `*-public-site`
  repositories, which the policies designate Public by class. Publishing them
  would put content on the open internet under a real account, so the sandbox
  keeps them private; the class in the register is the organization's
  designation, not the current repository visibility bit.
- **One workspace holds all three orgs**, so `conversations_search_messages`
  crosses tenants: a search for `site` returned hits from `helios-field-crews`
  and three Vireo channels in the same result set. Real deployments would be
  separate workspaces, so `slack_vireo` is written as if only the Vireo channels
  existed. The within-tenant finding — that an unscoped search reaches
  `vireo-unblinding` on ordinary vocabulary — is unaffected by this and is what
  the policy relies on.
- **No outbound mail.** Calendar attendees use the reserved `.example` TLD and
  every `create-event` passed `sendUpdates: "none"`.
- Message and event bodies are synthetic. Strings that look credential-shaped are
  explicit placeholders (`PLACEHOLDER-NOT-A-REAL-SECRET`).

## Tool × asset verification

The `Tools` column of each register was checked pair by pair against the live
servers — 194 pairs (the complete claimed set), 179 confirmed, 15 not, each with
a reason. Results and the
findings that came out of it (the usergroup write verbs walled off by Slack's
paid-plan requirement, a second undocumented Slack env flag, and the probe's own
side effects) are in
[TOOL_ASSET_VERIFICATION.md](TOOL_ASSET_VERIFICATION.md).

## Files

| File | What it holds |
|---|---|
| `TOOL_ASSET_MAP.md` | **what tool works on what asset**, per section, unconfirmed pairs in bold |
| `TOOL_ASSET_VERIFICATION.md`, `tool_asset_matrix.json` | the tool × asset probe: report and per-pair matrix |
| `tool_health.json`, `unverified_tools.json` | per-tool working/not status across all 55 tools |
| `probe_tool_asset.py`, `build_verification_report.py` | the probe and its report builder |
| `slack_channels.json` | 21 channels: id, org, purpose |
| `calendars.json` | 15 calendars: id, org, summary, description |
| `github_repos.json` | the 15 repositories created |
| `*_orgs_captured.json` | the creation runs — every call and its response |
| `verify_*.json` | the read-back runs through the same servers |
| `mcp_live.py` | minimal stdio JSON-RPC client: initialize → tools/list → tools/call |
| `make_*_plan.py`, `*_create.py` | the call plans and the two Web-API provisioners |

Credentials are read from `~/.mcp_live_keys/Keys/` at run time and never appear
in these files. The GitHub token in that directory has expired; the runs used
`gh auth token` (account `To2004`, scopes `gist, read:org, repo, workflow`).
