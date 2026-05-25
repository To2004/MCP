# Slack MCP — Scoring Notes

**Method:** NIST SP 800-30
**Generated:** 2026-05-25T08:02:33Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| slack_get_channel_history | Critical | Likelihood=High; Impact=Critical (private channel PII); max → Critical |
| slack_get_thread_replies | Critical | Likelihood=High; Impact=Critical (private thread content); max → Critical |
| slack_get_user_profile | Critical | Likelihood=High; Impact=Critical (direct PII asset); max → Critical |
| slack_post_message | High | Likelihood=High; Impact=High (social engineering; post_message overrides to High); max → High |
| slack_reply_to_thread | High | Likelihood=High; Impact=High (phishing reply; Impact adjusted to High); max → High |
| slack_get_users | Critical | Likelihood=High; Impact=Critical (bulk PII enumeration); max → Critical |
| slack_list_channels | High | Likelihood=High; Impact=Medium (channel-name recon only); max → High |
| slack_add_reaction | Low | Likelihood=Low; Impact=Low (emoji reaction, minimal); max → Low |

## Channel Categories

| Channel Categorie | Risk Level | Reasoning |
|---|---|---|
| Management | Critical | Channel sensitivity=Critical; read tools Likelihood=High → Critical |
| HR | Critical | Channel sensitivity=Critical; PII-heavy; read Likelihood=High → Critical |
| Public | Low | Channel sensitivity=Low; write Likelihood=High; max(High,Low) = Low |
| Supervisor | High | Channel sensitivity=High; read Likelihood=High → High |
| Researcher | High | Channel sensitivity=High; read Likelihood=High → High |
| Techinical | High |  |

## Assets

| Asset | Risk Level | Reasoning |
|---|---|---|
| User PII (emails, phones, titles) | Critical | Asset Impact=Critical; read Likelihood=High → Critical |
| Private Channel Messages | Critical | Asset Impact=Critical; read Likelihood=High → Critical |
| Public Channel Messages | Medium | Asset Impact=Medium; read Likelihood=High → High |
| Team Metadata | Medium | Asset Impact=Medium; read Likelihood=High → High |
