# Slack MCP — Scoring Notes

**Variant:** ChatGPT (gpt-4o) — security analyst, NIST SP 800-30 + OWASP LLM Top 10
**Generated:** 2026-05-25 07:24 UTC

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| slack_get_channel_history | High | Access to channel history can reveal sensitive discussions. |
| slack_get_thread_replies | High | Thread replies can contain sensitive follow-up information. |
| slack_get_user_profile | Medium | User profiles can contain personal information. |
| slack_post_message | Medium | Posting messages can disrupt communication channels. |
| slack_reply_to_thread | Medium | Replying to threads can spread misinformation. |
| slack_get_users | Medium | Access to user lists can reveal organizational structure. |
| slack_list_channels | Low | Listing channels generally poses low risk. |
| slack_add_reaction | Low | Adding reactions is generally harmless. |

## Channel Categories

| Category | Risk Level | Reasoning |
|---|---|---|
| Management | Critical | Contains strategic and sensitive management discussions. |
| HR | Critical | Contains sensitive employee information and discussions. |
| Supervisor | High | Contains supervisory communications that may be sensitive. |
| Researcher | High | Contains research discussions that may be proprietary. |
| Technical | Medium | Contains technical discussions that may reveal system details. |
| Public | Low | Contains information intended for public access. |

## Assets

| Asset | Risk Level | Reasoning |
|---|---|---|
| User PII (emails, phones, titles) | Critical | Exposure of PII can lead to identity theft. |
| Private Channel Messages | High | Contains confidential communications. |
| Public Channel Messages | Medium | Generally intended for wider audience, less sensitive. |
| Team Metadata | Medium | Contains organizational information that could be sensitive. |
