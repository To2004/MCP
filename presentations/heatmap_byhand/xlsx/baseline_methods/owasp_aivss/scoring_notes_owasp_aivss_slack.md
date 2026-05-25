# Slack MCP — Scoring Notes

**Method:** OWASP AIVSS
**Generated:** 2026-05-25T08:02:34Z

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| slack_get_channel_history | Critical | scale=0.85 TU×DA×MSR×PIS; Management PII: 9.0×1.20×0.85×1.15×1.10×1.10×1.10=17.6→10 → Critical |
| slack_get_thread_replies | Critical | scale=0.80 TU×DA×MSR×PIS; Mgmt PII 9.0×1.20×0.80×1.15×1.10×1.10×1.10=16.6→10 → Critical |
| slack_get_user_profile | High | scale=0.90 TU×DA×PIS; PII 9.0×1.20×0.90×1.15×1.10×1.10=13.7→10 → High |
| slack_post_message | High | scale=0.85 TU×PM×MSR; Mgmt PII 9.0×1.20×0.85×1.15×1.10×1.10=13.3→10 → High |
| slack_reply_to_thread | High | scale=0.85 TU×PM×MSR; same as post_message path → High |
| slack_get_users | Critical | scale=0.90 TU×DA×PIS; bulk PII 9.0×1.20×0.90×1.15×1.10×1.10=13.7→10 → Critical |
| slack_list_channels | Medium | scale=0.40 TU×PIS only; Team Metadata 3.5×1.0×0.40×1.15×1.10=1.8 → Medium |
| slack_add_reaction | Critical | scale=0.50 TU×PM×MSR; Public 3.0×0.70×0.50×1.15×1.10×1.10=1.5 → Critical (high-sensitivity assets amplify) |

## Channel Categories

| Channel Categorie | Risk Level | Reasoning |
|---|---|---|
| Management | Critical | ch_mult=1.20; get_channel_history DA+MSR+PIS → Critical; worst tool=Critical |
| HR | Critical | ch_mult=1.20; same amplifiers as Management; PII base=9.0 → Critical |
| Public | Low | ch_mult=0.70; all assets low base; capped at Low-Medium |
| Supervisor | High | ch_mult=1.05; PII base=9.0×1.05×0.85×TU×DA×MSR×PIS → High worst-case |
| Researcher | High | ch_mult=1.00; PII base=9.0×1.00×0.85×TU×DA×MSR×PIS → High |
| Techinical | High |  |

## Assets

| Asset | Risk Level | Reasoning |
|---|---|---|
| User PII (emails, phones, titles) | Critical | asset_base=9.0; Mgmt ch_mult=1.20; get_channel_history TU×DA×MSR×PIS → Critical |
| Private Channel Messages | Critical | asset_base=7.5; Mgmt 7.5×1.20×0.85×TU×DA×MSR×PIS → Critical |
| Public Channel Messages | Medium | asset_base=3.0; capped; post_message TU×PM×MSR; Mgmt 3.0×1.20×0.85=3.06→amplified → Medium |
| Team Metadata | Medium | asset_base=3.5; add_reaction TU×PM×MSR pushes to Medium; worst=Medium |
