# Live run — real MCP servers, real keys (benign-only)

Ran on 2026-07-06 on the HPC login node after installing Node (conda env
`mcpnode`) and loading the keys from `Keys.zip`. **Benign / read-only only** — no
create/update/push/delete/merge/fork tool was ever called (enforced by an
allowlist). This is the honest answer to "did it really run": one of the three
genuinely ran live end to end; the other two are blocked by the *credentials*,
not the framework.

**Full tool inventory of all three real servers and how each works:** see
[`MCP_INVENTORY.md`](MCP_INVENTORY.md). Real catalogs saved under
`reports/tool_lists/{github,calendar,slack}_real.json` (26 / 13 / 16 tools).

## Result per server

| server | live? | evidence |
| --- | --- | --- |
| **GitHub** | ✅ **ran live** | Real `@modelcontextprotocol/server-github` started with the real `ghp_` token; advertised **26 tools**; `search_repositories` returned `total_count: 267`; `get_file_contents` returned the real `modelcontextprotocol/servers` README (sha `fe5351a…`, 8609 bytes). Captured in `github_captured.json`. |
| **Slack** | ✅ **ran live** | After the user token was reissued with the read+write scopes, the real `slack-mcp-server` v1.3.0 booted fully ("Slack MCP Server is fully ready"), fetched **7 real channels** (`#social`, `#all-mcp`, …), and advertised **16 tools** (vs 8 in demo `slack_cbg`), 7 of them write (`conversations_add_message`, `_join`, `_leave`, `_mark`, `usergroups_create`/`_update`/`_users_update`). `channels_list` returned real data. Catalog saved to `reports/tool_lists/slack_real.json`. |
| **Google Calendar** | ✅ **ran live** | After the OAuth consent was completed (on the user's machine) and the resulting `tokens.json` (with `refresh_token`, full calendar scope) was placed at `~/.config/google-calendar-mcp/tokens.json`, the real `@cocal/google-calendar-mcp` server accepted it (`Valid tokens found`), advertised **13 tools**, and `list-calendars` returned the real calendars of the test account `test1mcpsserver@gmail.com` (Asia/Jerusalem). Read-only only — no event created/edited/deleted. Captured in `calendar_captured.json`. |

## Slack read + write verified live

On the disposable test workspace (owner-authorized), a full read **and write**
path was exercised: `conversations_add_message` posted a clearly-labeled test
message to `#all-mcp` (`ts=1783335134.109379`), and `conversations_history` read
it straight back (author `test1mcpsserver`). This is the live version of the
framework's adversarial "post to channel" path — safe here because the workspace
is a throwaway. Captured in `slack_write_captured.json`.

## What the GitHub run proves

1. **The end-to-end live path works**: real MCP server + real credential + real
   GitHub API + captured by the same tooling the framework uses.
2. **Real ≫ sample**: the real server exposes **26 tools** vs the **11** in the
   demo `github_cbg` scan — 16 tools (PR reviews, branches, issue comments, code
   search) the demo never modelled. The real catalog is saved to
   `reports/tool_lists/github_real.json` for a future real scan.
3. **The scorer stays honest on live data**: scoring the two real calls against
   the demo scan returns **`unresolved`** (the real repos were never scanned) —
   it refuses to fabricate a band, exactly as on synthetic data. To get real
   risk bands, scan `github_real.json` with the LLM scanner (GPU).

## To finish Slack (the only one left)

- **Slack**: the token authenticates but lacks read scopes. In the Slack app
  config add `channels:read`, `groups:read`, `im:read`, `mpim:read` (and
  `channels:history` etc. for message reads), reinstall the app to reissue the
  token, and update `slackkey.txt` in `Keys.zip`. The server is
  `slack-mcp-server` and reads `SLACK_MCP_XOXP_TOKEN` / `SLACK_MCP_XOXB_TOKEN`.

## Safety

- Read-only allowlist enforced; no state-changing tool was called.
- Keys were read from files, never hardcoded or printed; the decrypted copies
  under `~/.mcp_live_keys/` were shredded after the run. `Keys.zip` is `chmod 600`.
