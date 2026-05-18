# MCP Slack Server — Tool Reference

The MCP Slack server (`@modelcontextprotocol/server-slack`, reference implementation
in `modelcontextprotocol/servers-archived`) exposes a Slack workspace to AI agents
via JSON-RPC 2.0. Like the GitHub server, this server **stores no data of its own** —
every tool call is a thin wrapper around the Slack Web API at `slack.com/api`.

```
Agent → MCP server (local Node.js process) → slack.com/api → Slack workspace
```

> **Two implementations exist:**
> - **Reference server** (this document) — 8 tools, local process, full source at
>   `modelcontextprotocol/servers-archived/src/slack`. Token = `xoxb-` Bot Token.
> - **Official Slack remote server** (`slackapi/slack-mcp-plugin`, `mcp.slack.com/mcp`) —
>   ~12 tools including search and canvas, hosted by Slack, OAuth-based. No local
>   source to inspect.

## Overview

### Security Boundary

The protected asset is the **Bot User OAuth Token** (`xoxb-`) and its OAuth scopes.
The token is set via the `SLACK_BOT_TOKEN` environment variable at server startup —
the agent never sees it directly, but every tool call uses it.

- **Bot scopes = blast radius** — a bot with `channels:history` + `groups:history`
  can read every conversation in every channel it has been invited to (including
  private). A bot with `chat:write` can post messages as the bot to any channel
  it joined.
- **No local data** — all data lives in Slack. Killing the server leaves the workspace
  untouched.
- **Optional channel restriction** — the `SLACK_CHANNEL_IDS` env var restricts
  `slack_list_channels` to a fixed list. It does **not** restrict `slack_get_channel_history`
  or `slack_post_message` — those take a `channel_id` directly and work on any
  channel the bot has access to.
- **No input parameterization** — `text` arguments to `slack_post_message` and
  `slack_reply_to_thread` are passed directly to the Slack API. An agent can post
  any content, including links, mentions, and phishing-style messages.
- **No destructive paths** — there is no `delete_message`, `archive_channel`, or
  `kick_user` tool. Write risk is limited to posting/reacting.

**Note on response format:** All tools return Slack Web API JSON objects wrapped as
`{ "content": [{ "type": "text", "text": "<JSON string>" }] }`. Examples below
show the inner JSON directly, abbreviated as `{ "text": "..." }`.

### Required Bot Token Scopes

| Scope | Used by |
|-------|---------|
| `channels:read` | `slack_list_channels` (public) |
| `groups:read` | `slack_list_channels` (private, if invited) |
| `channels:history` | `slack_get_channel_history`, `slack_get_thread_replies` |
| `groups:history` | Same, for private channels |
| `chat:write` | `slack_post_message`, `slack_reply_to_thread` |
| `reactions:write` | `slack_add_reaction` |
| `users:read` | `slack_get_users` |
| `users.profile:read` | `slack_get_user_profile` |

### Tool Categories

| Category | Tools |
|----------|-------|
| Channel Discovery | `slack_list_channels` |
| Read Messages | `slack_get_channel_history`, `slack_get_thread_replies` |
| Write Messages | `slack_post_message`, `slack_reply_to_thread` |
| Social Actions | `slack_add_reaction` |
| User Directory | `slack_get_users`, `slack_get_user_profile` |

8 tools total.

---

## Channel Discovery Tool

### `slack_list_channels`

**What it does:** Lists public channels in the workspace (or the fixed list from
`SLACK_CHANNEL_IDS` if that env var is set). Returns channel IDs, names, topics,
member counts, and archive status.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | number | no | Max channels to return (default 100, max 200) |
| `cursor` | string | no | Pagination cursor for next page |

**Output:** `{ "text": "{ \"ok\": true, \"channels\": [...] }" }` — Slack
`conversations.list` response object.

**Good example:**

```json
// Request — orient at session start, find channel IDs for subsequent calls
{
  "method": "tools/call",
  "params": {
    "name": "slack_list_channels",
    "arguments": { "limit": 50 }
  }
}

// Response — array of channel objects
{
  "text": "{\"ok\":true,\"channels\":[{\"id\":\"C012AB3CD\",\"name\":\"general\",\"num_members\":142,\"topic\":{\"value\":\"Company-wide announcements\"}},{\"id\":\"C034EF5GH\",\"name\":\"security-incidents\",\"is_private\":false,\"num_members\":12},...],\"response_metadata\":{\"next_cursor\":\"dGVhbTpDMDY...\"}}"
}
```

**Bad example:**

```json
// Request — not using SLACK_CHANNEL_IDS restriction and enumerating all channels
// to find sensitive channels by name before reading them
{
  "method": "tools/call",
  "params": {
    "name": "slack_list_channels",
    "arguments": { "limit": 200 }
  }
}

// Response — full channel directory including names like #executive-comms,
// #security-incidents, #hr-confidential (if the bot is in those channels)
// This is reconnaissance: the agent now knows every channel the bot can access.
```

> **Edge cases**
> - `SLACK_CHANNEL_IDS` restricts what this tool returns, but the tool cannot
>   prevent direct `slack_get_channel_history` calls to arbitrary channel IDs.
> - If the bot is not invited to any private channels, those are invisible here.
> - `is_private: true` entries appear only if the bot was invited and the bot
>   token has `groups:read` scope.
> - An empty workspace returns `{ "ok": true, "channels": [] }` — not an error.

---

## Read Message Tools

### `slack_get_channel_history`

**What it does:** Returns the most recent N messages from a channel, including
message text, author user IDs, timestamps, and any reactions. Works on both
public and private channels the bot has been invited to.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | yes | Slack channel ID (e.g. `C012AB3CD`) |
| `limit` | number | no | Messages to return (default 10) |

**Output:** `{ "text": "{ \"ok\": true, \"messages\": [...] }" }` — Slack
`conversations.history` response.

**Good example:**

```json
// Request — read recent messages in #general
{
  "method": "tools/call",
  "params": {
    "name": "slack_get_channel_history",
    "arguments": { "channel_id": "C012AB3CD", "limit": 20 }
  }
}

// Response — messages with user IDs and timestamps
{
  "text": "{\"ok\":true,\"messages\":[{\"type\":\"message\",\"user\":\"U01ABC\",\"text\":\"Sprint review at 3pm today\",\"ts\":\"1705000000.001200\"},{\"type\":\"message\",\"user\":\"U02DEF\",\"text\":\"prod deploy failed — investigating\",\"ts\":\"1705000000.002300\"},...],\"has_more\":true}"
}
```

**Bad example:**

```json
// Request — reading a channel with sensitive operational content
{
  "method": "tools/call",
  "params": {
    "name": "slack_get_channel_history",
    "arguments": { "channel_id": "C_SECOPS_CHANNEL", "limit": 200 }
  }
}

// Response — full incident timeline, internal IP addresses, credentials
// pasted during an incident, on-call rotation details, vulnerability details.
// The bot was invited to this channel "to post alerts" — the agent is now
// reading the full security operations backlog.
{
  "text": "{\"messages\":[...,{\"text\":\"temp creds: AKIA... / key... expires in 1h\"},{\"text\":\"CVE-2024-XXXX affects prod, patching tonight\"}]}"
}
// Anything posted in a channel the bot joined is readable — no per-message ACL.
```

> **Edge cases**
> - `has_more: true` means there are older messages; paginate with the `cursor`
>   field from `response_metadata` (but this tool doesn't expose pagination params —
>   you get only the `limit` most recent messages).
> - Bot messages, system messages (joins/leaves), and deleted-message tombstones
>   all appear in the history.
> - If the bot was removed from the channel, returns `{ "ok": false, "error": "not_in_channel" }`.

---

### `slack_get_thread_replies`

**What it does:** Returns all replies in a message thread, given the parent
message's timestamp (`thread_ts`). Includes the original message as the first item.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | yes | Channel containing the thread |
| `thread_ts` | string | yes | Timestamp of the parent message (format `1234567890.123456`) |

**Output:** `{ "text": "{ \"ok\": true, \"messages\": [...] }" }` — full thread,
parent + all replies, in chronological order.

**Good example:**

```json
// Request — fetch the full context of a thread after seeing the parent in history
{
  "method": "tools/call",
  "params": {
    "name": "slack_get_thread_replies",
    "arguments": { "channel_id": "C012AB3CD", "thread_ts": "1705000000.001200" }
  }
}

// Response — parent message + all replies
```

**Bad example:**

```json
// Timestamp format error — no period in the ts string
{
  "method": "tools/call",
  "params": {
    "name": "slack_get_thread_replies",
    "arguments": { "channel_id": "C012AB3CD", "thread_ts": "1705000000001200" }
  }
}

// Response — Slack API rejects the malformed timestamp
{ "text": "{\"ok\":false,\"error\":\"invalid_ts\"}" }
// Fix: add a period so 6 digits follow it — "1705000000.001200"
```

> **Edge cases**
> - Timestamps from `slack_get_channel_history` may appear without the period in
>   some UI contexts — always normalize to `xxxxxxxxxx.xxxxxx` format.
> - A thread with no replies returns only the parent message in `messages`.
> - Thread replies in private channels require `groups:history` scope.

---

## Write Message Tools

### `slack_post_message`

**What it does:** Posts a new message as the bot to any Slack channel the bot
has been added to. Supports Slack markdown (mrkdwn): `*bold*`, `_italic_`,
`>quote`, `` `code` ``, `<@USER_ID>` mentions.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | yes | Target channel ID |
| `text` | string | yes | Message text (mrkdwn supported) |

**Output:** `{ "text": "{ \"ok\": true, \"ts\": \"...\", \"channel\": \"...\" }" }`

**Good example:**

```json
// Request — post a daily standup summary
{
  "method": "tools/call",
  "params": {
    "name": "slack_post_message",
    "arguments": {
      "channel_id": "C012AB3CD",
      "text": "*Daily Standup — 2026-05-12*\n- ✅ Auth fix shipped\n- 🔄 DB migration in progress\n- ⚠️ Blocked on design review"
    }
  }
}

// Response
{ "text": "{\"ok\":true,\"channel\":\"C012AB3CD\",\"ts\":\"1705001234.000100\",\"message\":{\"text\":\"*Daily Standup...\"}}" }
```

**Bad example:**

```json
// Request — agent sends a phishing-style message impersonating an exec
{
  "method": "tools/call",
  "params": {
    "name": "slack_post_message",
    "arguments": {
      "channel_id": "C_GENERAL",
      "text": "*Important security notice from IT* — your account requires reverification. Click here: <http://attacker.example/steal-creds|Verify account>"
    }
  }
}

// Response — message delivered as the bot to the entire #general channel
{ "text": "{\"ok\":true,\"ts\":\"1705001234.000200\"}" }
// The bot's display name and icon make it look authoritative.
// No confirmation step — the message is already sent.
```

> **Edge cases**
> - The message is sent **immediately** — there is no draft mode (the slackapi remote
>   server adds `slack_send_message_draft`, but the reference server does not).
> - The `text` field is passed verbatim to the Slack API — **no sanitization**. Any
>   mrkdwn, link, or mention the agent includes will render as intended.
> - Sending to a channel the bot has not joined returns
>   `{ "ok": false, "error": "not_in_channel" }`.
> - Rate limit: Slack's `chat.postMessage` is limited to ~1 request/second per token.
>   Rapid posting hits `ratelimited` errors.

---

### `slack_reply_to_thread`

**What it does:** Posts a reply to an existing message thread. Identical to
`slack_post_message` in risk profile — the only difference is the message
appears inside a thread rather than in the main channel.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | yes | Channel containing the thread |
| `thread_ts` | string | yes | Parent message timestamp |
| `text` | string | yes | Reply text (mrkdwn supported) |

**Output:** `{ "text": "{ \"ok\": true, \"ts\": \"...\", \"message\": {...} }" }`

**Good example:**

```json
// Request — reply to an incident thread with a status update
{
  "method": "tools/call",
  "params": {
    "name": "slack_reply_to_thread",
    "arguments": {
      "channel_id": "C_INCIDENTS",
      "thread_ts": "1705000000.002300",
      "text": "Root cause identified: misconfigured load balancer. Rollback complete. Monitoring for 30 min before all-clear."
    }
  }
}
```

**Bad example:**

```json
// Request — agent injects misinformation into an ongoing incident thread
{
  "method": "tools/call",
  "params": {
    "name": "slack_reply_to_thread",
    "arguments": {
      "channel_id": "C_INCIDENTS",
      "thread_ts": "1705000000.002300",
      "text": "False alarm — escalation cancelled. No further action needed."
    }
  }
}
// Thread participants receive the reply as if it came from the trusted bot.
// Incident responders may stand down prematurely.
```

> **Edge cases**
> - No `reply_broadcast` parameter — the reference server always replies in-thread
>   only (unlike the Slack API which supports broadcasting to channel).
> - Same timestamp format constraint as `slack_get_thread_replies`.

---

## Social Action Tool

### `slack_add_reaction`

**What it does:** Adds an emoji reaction to a specific message. Reactions appear
under the message and are visible to all members in the channel.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | yes | Channel containing the message |
| `timestamp` | string | yes | Message timestamp |
| `reaction` | string | yes | Emoji name without colons (e.g. `thumbsup`) |

**Output:** `{ "text": "{ \"ok\": true }" }`

**Good example:**

```json
// Request — acknowledge a message with a thumbs-up
{
  "method": "tools/call",
  "params": {
    "name": "slack_add_reaction",
    "arguments": { "channel_id": "C012AB3CD", "timestamp": "1705000000.001200", "reaction": "white_check_mark" }
  }
}
```

**Bad example:**

```json
// Request — voting with negative/inflammatory emoji to manipulate sentiment
{
  "method": "tools/call",
  "params": {
    "name": "slack_add_reaction",
    "arguments": { "channel_id": "C_PROPOSALS", "timestamp": "1705000000.001200", "reaction": "thumbsdown" }
  }
}
// Lowest-severity write tool, but still visible to the entire channel.
// The bot cannot remove its own reactions — no remove_reaction tool exists.
```

> **Edge cases**
> - Adding the same reaction twice returns `{ "ok": false, "error": "already_reacted" }`.
> - Invalid emoji names return `{ "ok": false, "error": "invalid_name" }`.
> - There is no `slack_remove_reaction` tool — reactions added by the agent are permanent
>   until manually removed by a human.
> - Requires `reactions:write` scope.

---

## User Directory Tools

### `slack_get_users`

**What it does:** Returns a paginated list of all workspace users. Each entry
includes the user's ID, display name, real name, email (if the bot has
`users:read.email` scope), time zone, and status.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | number | no | Max users (default 100, max 200) |
| `cursor` | string | no | Pagination cursor |

**Output:** `{ "text": "{ \"ok\": true, \"members\": [...] }" }` — Slack
`users.list` response.

**Good example:**

```json
// Request — discover user IDs for mention construction
{
  "method": "tools/call",
  "params": {
    "name": "slack_get_users",
    "arguments": { "limit": 200 }
  }
}

// Response — workspace member list
{ "text": "{\"ok\":true,\"members\":[{\"id\":\"U01ABC\",\"name\":\"alice\",\"real_name\":\"Alice Chen\",\"profile\":{\"email\":\"alice@corp.com\",\"display_name\":\"alice\"}},...],\"response_metadata\":{\"next_cursor\":\"\"}}" }
```

**Bad example:**

```json
// Request — single call dumps every employee's name, email, and timezone
{
  "method": "tools/call",
  "params": {
    "name": "slack_get_users",
    "arguments": { "limit": 200 }
  }
}

// Response — full PII directory: names, emails, job titles, phone numbers
// (if users have filled in profiles), timezone, active/away status.
// This is a complete employee directory dump with one tool call.
```

> **Edge cases**
> - Bot users and Slack App entries are included in the response — filter by
>   `"is_bot": false` to get only humans.
> - `email` is only present if the bot has `users:read.email` scope (requires admin approval).
> - Deactivated users appear with `"deleted": true`.
> - Large workspaces (1000+ users) require multiple paginated calls using `cursor`.

---

### `slack_get_user_profile`

**What it does:** Returns the detailed Slack profile for a single user — display
name, real name, email, phone, title, status text/emoji, timezone, and any custom
profile fields the workspace has defined.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | string | yes | Slack user ID (e.g. `U01ABC`) |

**Output:** `{ "text": "{ \"ok\": true, \"profile\": {...} }" }` — Slack
`users.profile.get` response.

**Good example:**

```json
// Request — look up someone's title before addressing them
{
  "method": "tools/call",
  "params": {
    "name": "slack_get_user_profile",
    "arguments": { "user_id": "U01ABC" }
  }
}

// Response
{ "text": "{\"ok\":true,\"profile\":{\"display_name\":\"alice\",\"real_name\":\"Alice Chen\",\"title\":\"Senior Engineer\",\"email\":\"alice@corp.com\",\"status_text\":\"on vacation until 5/20\",\"tz\":\"America/New_York\"}}" }
```

**Bad example:**

```json
// Request — harvesting executive contact details for social engineering
{
  "method": "tools/call",
  "params": {
    "name": "slack_get_user_profile",
    "arguments": { "user_id": "U_CEO_ID" }
  }
}

// Response — real name, personal email (if set), phone, custom fields
// such as "Manager", "Department", "GitHub handle", "Location" if
// the workspace has defined them. High-value recon target.
```

> **Edge cases**
> - `include_labels: true` is always passed by the server — custom field labels
>   are returned alongside values.
> - If the user does not exist or is from another workspace: `{ "ok": false, "error": "user_not_found" }`.
> - Status text/emoji reflects the user's current availability (valuable for timing social engineering).

---

## Edge Cases & Gotchas

### Token Scope = Blast Radius

| Scope | What the agent can do |
|-------|-----------------------|
| `channels:read` | Enumerate all public channels by name |
| `channels:history` | Read full message history of every public channel the bot joined |
| `groups:history` | Same for private channels |
| `chat:write` | Post as the bot to any joined channel — no confirmation |
| `reactions:write` | Add emoji to any visible message — no confirmation, no undo via API |
| `users:read` | Dump the entire workspace member directory |
| `users.profile:read` | Read detailed profiles including custom fields |

Minimum scope for basic read-only use: `channels:read` + `channels:history`.
Adding `chat:write` introduces the write-risk surface.

### `SLACK_CHANNEL_IDS` Restriction is Porous

```
SLACK_CHANNEL_IDS=C012AB3CD,C034EF5GH
```

This restricts `slack_list_channels` to those two channels. But:

```json
// This still works on ANY channel the bot has access to:
{ "name": "slack_get_channel_history", "arguments": { "channel_id": "C_SENSITIVE_CHANNEL" } }
{ "name": "slack_post_message",        "arguments": { "channel_id": "C_SENSITIVE_CHANNEL", "text": "..." } }
```

`SLACK_CHANNEL_IDS` provides **discovery restriction only**, not access restriction.
The only way to restrict `slack_get_channel_history` is to not invite the bot to sensitive channels.

### No Input Sanitization

`slack_post_message` and `slack_reply_to_thread` pass `text` directly to
`chat.postMessage`. There is no stripping of links, mentions, or mrkdwn.

```json
// Agent-controlled text posted verbatim to the workspace:
"text": "<http://attacker.example|Click here to verify your Slack account>"
// Renders as a clickable link: "Click here to verify your Slack account"

"text": "<!channel> Emergency — everyone evacuate the office immediately"
// <!channel> notifies every member of the channel — real Slack feature.
```

### No Delete / Undo

| Action | Reversible via MCP? |
|--------|---------------------|
| `slack_post_message` | ❌ no `delete_message` tool |
| `slack_reply_to_thread` | ❌ no `delete_message` tool |
| `slack_add_reaction` | ❌ no `remove_reaction` tool |

All write actions are permanent at the MCP level. A human must go into Slack
to delete the message or remove the reaction manually.

### PII Dump in One Call

```
slack_get_users(limit=200) → full workspace directory
```

One tool call returns every employee's name, email, timezone, and status —
a complete PII snapshot of the organisation. The same data from a corporate
HR system would require multiple database queries with access controls.

### Tools That Don't Exist

These are intentionally absent from the reference server:

| Tool you might expect | Why it's missing |
|-----------------------|------------------|
| `slack_delete_message` | Irreversible — too destructive |
| `slack_archive_channel` | Admin-level — out of scope |
| `slack_kick_user` | Admin-level — out of scope |
| `slack_upload_file` | Binary upload — out of scope |
| `slack_search` | Added in the remote slackapi server, not reference |
| `slack_create_canvas` | Remote server only |
| `slack_direct_message` | Use `slack_post_message` with a user's DM channel ID |

---

## Tool Capability Matrix

| Tool | Reads messages | Reads user PII | Posts messages | Reactions | Destructive |
|------|---------------|----------------|----------------|-----------|-------------|
| `slack_list_channels` | ❌ | ❌ | ❌ | ❌ | ❌ |
| `slack_get_channel_history` | ✅ | ⚠️ user IDs in messages | ❌ | ❌ | ❌ |
| `slack_get_thread_replies` | ✅ | ⚠️ user IDs in messages | ❌ | ❌ | ❌ |
| `slack_post_message` | ❌ | ❌ | ✅ | ❌ | ⚠️ no undo |
| `slack_reply_to_thread` | ❌ | ❌ | ✅ (in thread) | ❌ | ⚠️ no undo |
| `slack_add_reaction` | ❌ | ❌ | ❌ | ✅ | ⚠️ no undo |
| `slack_get_users` | ❌ | ✅ full directory | ❌ | ❌ | ❌ |
| `slack_get_user_profile` | ❌ | ✅ detailed | ❌ | ❌ | ❌ |

Legend: ✅ = yes · ⚠️ = conditional / limited · ❌ = no / not applicable
