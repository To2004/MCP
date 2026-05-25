# Slack MCP — Scoring Notes

**Method:** NIST SP 800-60
**Generated:** 2026-05-25T08:02:34Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| slack_get_channel_history | High | Role=C; User PII C=High (Mgmt upgrade) → band(High,[Mod,Low]) = High |
| slack_get_thread_replies | High | Role=C; User PII in Mgmt channel C upgrades to High → High |
| slack_get_user_profile | High | Role=C; PII C=High → band(High,[Mod,Low]) = High |
| slack_post_message | Medium | Role=I; PII I=Mod; Private Msg I=Low; band(Mod,[High,Low]) → Medium |
| slack_reply_to_thread | Medium | Role=I; PII I=Mod → Medium; no other High dims → Medium |
| slack_get_users | High | Role=C; PII C=High (Mgmt upgrade); band(High,[Mod,Low]) = High |
| slack_list_channels | High | Role=C; Team Metadata C=Low → Low; PII C=High → High worst-case |
| slack_add_reaction | Medium | Role=I; all assets I=Low or Mod → Low or Medium |

## Channel Categories

| Channel Categorie | Risk Level | Reasoning |
|---|---|---|
| Management | High | Persona upgrade: PII C Low→Moderate, Private Msg C Low→Moderate; worst=High |
| HR | High | Persona upgrade same as Management; PII C→Moderate; write I=Mod → Medium/High |
| Public | High | No persona upgrade; all assets low CIA; tools → Low or Medium |
| Supervisor | High | No persona upgrade; PII C=High; read C=High → High |
| Researcher | High | No persona upgrade; PII C=High; read → High |
| Techinical | High |  |

## Assets

| Asset | Risk Level | Reasoning |
|---|---|---|
| User PII (emails, phones, titles) | High | CIA=(High,Mod,Low); read C=High → High; write I=Mod → Medium |
| Private Channel Messages | High | CIA=(High,Low,Low); read C=High → High; write I=Low → Low |
| Public Channel Messages | Low | CIA=(Low,Low,Low); all tools → Low |
| Team Metadata | Low | CIA=(Low,Low,Low); all tools → Low |
