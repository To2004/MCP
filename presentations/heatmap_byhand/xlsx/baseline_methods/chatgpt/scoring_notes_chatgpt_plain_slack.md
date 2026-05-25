# Slack MCP — Scoring Notes

**Variant:** ChatGPT (gpt-4o) — plain, no system prompt
**Generated:** 2026-05-25 07:24 UTC

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| slack_get_channel_history | High | Accessing channel history can expose sensitive discussions. |
| slack_get_thread_replies | High | Thread replies may contain sensitive follow-up information. |
| slack_get_user_profile | Medium | User profiles can reveal personal information. |
| slack_post_message | Medium | Posting messages can lead to misinformation or spam. |
| slack_reply_to_thread | Medium | Replying to threads can disrupt ongoing discussions. |
| slack_get_users | Medium | Listing users can reveal organizational structure. |
| slack_list_channels | Low | Listing channels generally reveals non-sensitive information. |
| slack_add_reaction | Low | Adding reactions is a low-risk activity. |

## Channel Categories

| Category | Risk Level | Reasoning |
|---|---|---|
| Management | Critical | Management channels contain strategic discussions. |
| HR | Critical | HR channels contain sensitive employee information. |
| Supervisor | High | Supervisor channels may include sensitive operational details. |
| Researcher | High | Research channels can contain proprietary research data. |
| Technical | Medium | Technical channels may include sensitive technical discussions. |
| Public | Low | Public channels are intended for non-sensitive information. |

## Assets

| Asset | Risk Level | Reasoning |
|---|---|---|
| User PII (emails, phones, titles) | Critical | PII exposure can lead to privacy violations. |
| Private Channel Messages | Critical | Private messages often contain sensitive information. |
| Public Channel Messages | Medium | Public messages are generally less sensitive. |
| Team Metadata | Medium | Metadata can reveal organizational structure and roles. |
