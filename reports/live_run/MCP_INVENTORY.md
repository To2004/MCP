# Real MCP Inventory — GitHub · Google Calendar · Slack

The actual tool surface of the three big MCP servers, captured **live** on
2026-07-06 (not the small demo samples). Each server was launched for real with
its real credentials; this is its own advertised `tools/list`. Full catalogs
(names + descriptions + input schemas) are saved under `reports/tool_lists/`:
`github_real.json`, `calendar_real.json`, `slack_real.json`.

Why this matters: the framework's scans (`reports/scan/*.json`) were built from
**hand-modelled demo** servers with far fewer tools. The real servers expose
2–3× more tools — including many write/destructive ones the demo omits — so a
real risk assessment must scan these real catalogs, not the samples.

| MCP | server package | real tools | demo tools | live status |
| --- | --- | --- | --- | --- |
| GitHub | `@modelcontextprotocol/server-github` | **26** | 11 | ✅ read verified |
| Google Calendar | `@cocal/google-calendar-mcp` | **13** | 11 | ✅ read verified |
| Slack | `slack-mcp-server` (korotovsky) | **16** | 8 | ✅ read + write verified |

---

## How each server works

All three are **Node** packages launched via `npx` over **stdio**, driven here
by the Python `mcp` client. Node is provided by the conda env `mcpnode`
(the cluster has no system Node). Credentials come from `Keys.zip`; nothing is
hardcoded.

- **GitHub** — env `GITHUB_PERSONAL_ACCESS_TOKEN` = a `ghp_` PAT. Stateless auth,
  boots immediately. Read tools hit the GitHub REST API directly.
- **Google Calendar** — env `GOOGLE_OAUTH_CREDENTIALS` = the OAuth *installed-app*
  client JSON, **plus** a `tokens.json` (with `refresh_token`) at
  `~/.config/google-calendar-mcp/tokens.json`. The consent must be done once in a
  browser (on a machine that has one) to mint that token; it then refreshes headless.
- **Slack** — env `SLACK_MCP_XOXP_TOKEN` (user token, preferred) and/or
  `SLACK_MCP_XOXB_TOKEN` (bot token, ignored when the user token is present). The
  user token needs read scopes (`channels:read`+`groups/im/mpim:read`, `*:history`,
  `search:read`, `users:read`) or the server **crashes on boot** fetching channels;
  write tools need `chat:write`, `reactions:write`, `channels:write`, and the post
  tool only appears when `SLACK_MCP_ADD_MESSAGE_TOOL=true`. Caches channels/users
  under `~/.cache/slack-mcp-server/`.

---

## GitHub — 26 tools

**Read (7):** `search_repositories`, `get_file_contents`, `list_commits`,
`get_issue`, `list_issues`, `search_code`, `search_users`, `search_issues`,
`get_pull_request`, `list_pull_requests`, `get_pull_request_files`,
`get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews`

**Write / state-changing:** `create_or_update_file`, `push_files`, `create_issue`,
`update_issue`, `add_issue_comment`, `create_repository`, `create_branch`,
`create_pull_request`, `create_pull_request_review`, `merge_pull_request`,
`update_pull_request_branch`, `fork_repository`

Demo `github_cbg` modelled only 11 (and no `create_repository`, `create_branch`,
PR-review, or issue-comment tools).

## Google Calendar — 13 tools

**Read:** `list-calendars`, `list-events`, `search-events`, `get-event`,
`list-colors`, `get-freebusy`, `get-current-time`

**Write / state-changing:** `create-event`, `create-events` (bulk),
`update-event`, `delete-event`, `respond-to-event`

**Account:** `manage-accounts` (auth management)

## Slack — 16 tools

**Read (9):** `channels_list`, `channels_me`, `conversations_history`,
`conversations_replies`, `conversations_search_messages`, `conversations_unreads`,
`usergroups_list`, `usergroups_me`, `users_search`

**Write / state-changing (7):** `conversations_add_message` (post),
`conversations_join`, `conversations_leave`, `conversations_mark`,
`usergroups_create`, `usergroups_update`, `usergroups_users_update`

Demo `slack_cbg` modelled 8 (different names, no usergroup or join/leave tools).
Live read + write both verified: posted a labeled test message to `#all-mcp` and
read it back (see `slack_write_captured.json`).

---

## Next step to use these in the framework

These real catalogs are ready to be scanned into real risk matrices — feed each
`reports/tool_lists/<mcp>_real.json` to the LLM scanner
(`python -m mcp_security.scanner --tool-list ...`, GPU) to replace the demo scans,
then regenerate the simulations against the real tool surface.
