# Slack MCP — Scoring Notes

**Method:** MAESTRO/ATFAA
**Generated:** 2026-05-25T08:02:33Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| slack_get_channel_history | Critical | P=3 × I=3(PII in Mgmt/HR) × E=3 = 27 → Critical (routine bulk read) |
| slack_get_thread_replies | Critical | P=3 × I=3 × E=3 = 27 → Critical (routine thread follow; PII asset I=3) |
| slack_get_user_profile | Critical | P=3 × I=3(PII always I=3) × E=3 = 27 → Critical (routine PII resolution) |
| slack_post_message | Critical | P=2 × I=3 × E=3 = 18 → Critical (plausible social-engineering post) |
| slack_reply_to_thread | Critical | P=2 × I=3 × E=3 = 18 → Critical (plausible in-context phishing reply) |
| slack_get_users | Critical | P=3 × I=3(PII I=3) × E=3 = 27 → Critical (routine bulk PII enumeration) |
| slack_list_channels | Critical | P=3 × I=1(channel names only) × E=3 = 9 → High (routine recon, low impact) |
| slack_add_reaction | High | P=1 × I=1(Team Metadata) × E=3 = 3 → Low (unlikely, minimal impact) |

## Channel Categories

| Channel Categorie | Risk Level | Reasoning |
|---|---|---|
| Management | Critical | I=3 (strategic decisions, exec PII); P=3(read) × I=3 × E=3 = 27 → Critical |
| HR | Critical | I=3 (PII-heavy: payroll, disciplinary); P=3 × I=3 × E=3 = 27 → Critical |
| Public | Critical | I=1 (low sensitivity); exec P=3 × I=1 × E=3 = 9 → High (channel-list recon) |
| Supervisor | Critical | I=2; PII asset overrides I=3; P=3 × I=3 × E=3 = 27 → Critical worst-case |
| Researcher | Critical | I=2; PII asset I=3; P=3 × I=3 × E=3 = 27 → Critical worst-case |
| Techinical | Critical |  |

## Assets

| Asset | Risk Level | Reasoning |
|---|---|---|
| User PII (emails, phones, titles) | Critical | I=3 (PII always); P=3(read) × I=3 × E=3 = 27 → Critical |
| Private Channel Messages | Critical | I follows channel (up to 3 for Mgmt/HR); P=3 × I=3 × E=3 = 27 → Critical |
| Public Channel Messages | High | I=1 (public); P=3 × I=1 × E=3 = 9 → High worst-case |
| Team Metadata | High | I=1 (structural metadata); P=3 × I=1 × E=3 = 9 → High worst-case |
