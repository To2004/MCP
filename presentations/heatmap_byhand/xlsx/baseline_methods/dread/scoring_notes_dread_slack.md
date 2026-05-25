# Slack MCP — Scoring Notes

**Method:** DREAD
**Generated:** 2026-05-25T08:02:33Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| slack_get_channel_history | Critical | D=7 R=9 E=9 A=9 Disc=9 → avg=8.6 → Critical (bulk private message harvest) |
| slack_get_thread_replies | Critical | D=7 R=9 E=9 A=9 Disc=9 → avg=8.6 → Critical (sensitive thread content read) |
| slack_get_user_profile | Critical | D=8 R=9 E=9 A=9 Disc=9 → avg=8.8 → Critical (direct PII: email, phone, title) |
| slack_post_message | Critical | D=8 R=9 E=9 A=9(HR worst) Disc=9 → avg=8.8 → Critical (impersonation/social engineering) |
| slack_reply_to_thread | Critical | D=8 R=9 E=9 A=9 Disc=9 → avg=8.8 → Critical (in-context phishing/manipulation) |
| slack_get_users | Critical | D=7 R=9 E=9 A=9 Disc=9 → avg=8.6 → Critical (bulk PII enumeration workspace-wide) |
| slack_list_channels | Critical | D=4 R=9 E=9 A=9 Disc=9 → avg=8.0 → Critical (recon; reveals channel names) |
| slack_add_reaction | High | D=3 R=9 E=9 A=9 Disc=9 → avg=7.8 → High (minimal; emoji signalling only) |

## Channel Categories

| Channel Categorie | Risk Level | Reasoning |
|---|---|---|
| Management | Critical | D=9 A=8 R=9 E=9 Disc=9 → avg=8.8 → Critical (strategic decisions, exec PII) |
| HR | Critical | D=9 A=9 R=9 E=9 Disc=9 → avg=9.0 → Critical (PII-heavy: performance, salary, hiring) |
| Public | High | D=min(public_asset_d,5) A=3 R=9 E=9 Disc=9 → avg≤7.0 → High (already visible, capped damage) |
| Supervisor | Critical | D=8 A=7 R=9 E=9 Disc=9 → avg=8.4 → Critical (team operations, moderate sensitivity) |
| Researcher | High | D=6 A=6 R=9 E=9 Disc=9 → avg=7.8 → High (IP, research methodology) |
| Techinical | Critical |  |

## Assets

| Asset | Risk Level | Reasoning |
|---|---|---|
| User PII (emails, phones, titles) | Critical | D=9 A=9(HR worst) R=9 E=9 Disc=9 → avg=9.0 → Critical (direct PII exfiltration) |
| Private Channel Messages | Critical | D=8 A=9 R=9 E=9 Disc=9 → avg=8.8 → Critical (confidential comms bulk-read) |
| Public Channel Messages | Critical | D=4 capped A=3(public) → but worst-case HR A=9 D=4 → avg=8.0 → Critical |
| Team Metadata | Critical | D=4 capped A=9(HR worst) R=9 E=9 Disc=9 → avg=8.0 → Critical |
