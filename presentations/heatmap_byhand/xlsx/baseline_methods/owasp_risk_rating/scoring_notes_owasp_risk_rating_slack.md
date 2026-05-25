# Slack MCP — Scoring Notes

**Method:** OWASP Risk Rating
**Generated:** 2026-05-25T08:02:34Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| slack_get_channel_history | Critical | L=(7+8+8+9)/4=8.0(High); I=(9+1+9+1)/2=9.0 High; matrix(H,H) → Critical |
| slack_get_thread_replies | Critical | L=(7+7+8+9)/4=7.75(High); I=(9+9)/2=9.0; matrix(H,H) → Critical |
| slack_get_user_profile | Critical | L=(7+8+8+9)/4=8.0(High); I=(9+9)/2=9.0; matrix(H,H) → Critical |
| slack_post_message | Critical | L=(7+9+7+9)/4=8.0(High); I=(9+1+9+2)/2=9.0+cap; matrix(H,H) → Critical |
| slack_reply_to_thread | Critical | L=(7+9+7+9)/4=8.0(High); I=(9+1+9+2)/2=9.0; matrix(H,H) → Critical |
| slack_get_users | Critical | L=(7+8+8+9)/4=8.0(High); I=(9+9)/2=9.0; matrix(H,H) → Critical |
| slack_list_channels | Critical | L=(7+6+8+9)/4=7.5(High); I=(9-2+9-1)/2=(7,8) High; matrix(H,H) → Critical |
| slack_add_reaction | High | L=(7+3+8+9)/4=6.75(High); I=(9-4+9-4)/2=(5,5) Med; matrix(H,M) → High |

## Channel Categories

| Channel Categorie | Risk Level | Reasoning |
|---|---|---|
| Management | Critical | SLACK_IMPACT max (9,9); post_message I=(9+1,9+2)=cap 9; L=8.0 High → Critical |
| HR | Critical | SLACK_IMPACT (9,9) for PII; post_message adds (1,2)→cap; matrix(H,H) → Critical |
| Public | Critical | SLACK_IMPACT (2,2) for public msgs; write I=(2+1,2+2)=(3,4) Med; L=8.0 High → High |
| Supervisor | Critical | SLACK_IMPACT (7,8) for PII; post_message I→(8,9) High; L=8.0 High → Critical |
| Researcher | Critical | SLACK_IMPACT (8,8) private msgs; post_message I→cap 9; L=8.0 High → Critical |
| Techinical | Critical |  |

## Assets

| Asset | Risk Level | Reasoning |
|---|---|---|
| User PII (emails, phones, titles) | Critical | Worst (9,9) in HR channel; post_message adds (1,2)→cap 9; L=8.0 High → Critical |
| Private Channel Messages | Critical | Worst (9,9) in Mgmt/HR; post_message→cap 9; L=8.0 High → Critical |
| Public Channel Messages | Critical | Max impact (5,5) Technical/Mgmt; post_message (6,7) High; L=8.0 High → Critical |
| Team Metadata | Critical | Max impact (5,6) HR; post_message→(6,8) High; L=8.0 High → Critical |
