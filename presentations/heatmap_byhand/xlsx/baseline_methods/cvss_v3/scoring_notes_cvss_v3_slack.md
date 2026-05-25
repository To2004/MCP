# Slack MCP — Scoring Notes

**Method:** CVSS v3.1
**Generated:** 2026-05-25T08:02:32Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| slack_get_channel_history | Medium | AV:N AC:L PR:L UI:N S:U C:H I:N (bulk private-channel read) → Medium (6.5) |
| slack_get_thread_replies | Medium | AV:N AC:L PR:L UI:N S:U C:H I:N (thread-scoped history read) → Medium (6.5) |
| slack_get_user_profile | Medium | AV:N AC:L PR:L UI:N S:U C:H I:N (direct PII: email, phone, title) → Medium (6.5) |
| slack_post_message | High | AV:N AC:L PR:L UI:N S:C C:L I:H (fabricates messages workspace-wide) → High (8.5) |
| slack_reply_to_thread | High | AV:N AC:L PR:L UI:N S:C C:L I:H (phishing in thread context) → High (8.5) |
| slack_get_users | Medium | AV:N AC:L PR:L UI:N S:U C:H I:N (bulk PII enumeration, workspace-wide) → Medium (6.5) |
| slack_list_channels | Medium | AV:N AC:L PR:L UI:N S:U C:L I:N (channel-name reconnaissance) → Medium (5.3) |
| slack_add_reaction | Medium | AV:N AC:L PR:L UI:N S:U C:N I:L (emoji signalling, minimal) → Medium (4.3) |

## Channel Categories

| Channel Categorie | Risk Level | Reasoning |
|---|---|---|
| Management | High | S:C write tools apply to all channels; post_message I:H → High worst-case |
| HR | High | S:C write tools apply; HR PII C:H amplifies confidentiality risk → High |
| Public | High | S:C write tools still apply to public channels; post_message I:H → High |
| Supervisor | High | S:C post/reply apply; channel tier=high C:H; write tools dominate → High |
| Researcher | High | S:C write tools apply; private channel C:H in Research context → High |
| Techinical | N/A |  |

## Assets

| Asset | Risk Level | Reasoning |
|---|---|---|
| User PII (emails, phones, titles) | High | C:H read via get_user_profile; S:C post_message I:H → High worst-case |
| Private Channel Messages | High | C:H channel history read (6.5); S:C post_message I:H → High worst-case |
| Public Channel Messages | High | S:C post_message I:H applies regardless of channel visibility → High |
| Team Metadata | High | S:C post_message I:H dominates; metadata C:L read → High worst-case |
