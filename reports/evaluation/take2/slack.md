# Evaluation ground truth — slack

> Design-time reviewed risk table. **Used only to grade the scanner's output; the scanner never reads this file.**

## Server

| Field | Value |
| --- | --- |
| name | slack |
| server | slack-mcp-server |
| mcp_kind | communication platform |
| version | static-take2-2026-06-23 |
| model_reviewed | True |
| formula | `asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact` |
| band_distribution | {'low': 43, 'medium': 26, 'high': 11, 'critical': 0} |
| judge_ran | True |
| judge_overrides | 15 |

## Inferred domain profile

- **mcp_kind**: communication platform
- **asset_meaning**: channels within a workspace
- **blast_radius_meaning**: the scope of impact from an action; from viewing messages to posting new ones that could reach all members in the channel
- **worked_example**: Using 'slack_post_message' on 'exec-private': Posting a message to an executive-level, private channel could lead to significant internal impact.
- **dangerous_classes**: holds sensitive information, is private
- **irreversible_actions**: posts external messages, sends notifications

### Tool impact (1 read · 2 recoverable · 3 destructive)

| tool | impact |
| --- | --- |
| `slack_list_channels` | 1 |
| `slack_get_channel_history` | 1 |
| `slack_get_thread_replies` | 1 |
| `slack_get_users` | 1 |
| `slack_get_user_profile` | 1 |
| `slack_post_message` | 3 |
| `slack_reply_to_thread` | 2 |
| `slack_add_reaction` | 2 |

### Asset sensitivity (1 low – 5 crown-jewel)

| asset | sensitivity |
| --- | --- |
| `general` | 1 |
| `announcements` | 1 |
| `random` | 1 |
| `engineering` | 2 |
| `incident-response` | 4 |
| `on-call` | 4 |
| `research-team` | 4 |
| `exec-private` | 4 |
| `hr-internal` | 4 |
| `team-leads` | 4 |

## Risk matrix (score · band)

Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical

| asset \ tool | slack_list_channels | slack_get_channel_history | slack_get_thread_replies | slack_get_users | slack_get_user_profile | slack_post_message | slack_reply_to_thread | slack_add_reaction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 1 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 0 🟢 | 6 🟢 | 4 🟢 | 4 🟢 |
| `announcements` | 1 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 0 🟢 | 9 🟡 | 4 🟢 | 4 🟢 |
| `random` | 1 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 0 🟢 | 6 🟢 | 4 🟢 | 4 🟢 |
| `engineering` | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 2 🟢 | 12 🟡 | 8 🟡 | 8 🟡 |
| `incident-response` | 4 🟢 | 4 🟢 | 12 🟠 | 4 🟢 | 4 🟢 | 48 🟠 | 16 🟡 | 16 🟡 |
| `on-call` | 8 🟡 | 8 🟡 | 8 🟡 | 4 🟢 | 4 🟢 | 48 🟠 | 16 🟡 | 16 🟡 |
| `research-team` | 4 🟢 | 4 🟢 | 12 🟠 | 8 🟡 | 4 🟢 | 48 🟠 | 16 🟡 | 16 🟡 |
| `exec-private` | 4 🟢 | 12 🟠 | 8 🟡 | 8 🟡 | 4 🟢 | 36 🟠 | 16 🟡 | 16 🟡 |
| `hr-internal` | 4 🟢 | 12 🟠 | 12 🟠 | 8 🟡 | 4 🟢 | 48 🟠 | 16 🟡 | 16 🟡 |
| `team-leads` | 4 🟢 | 8 🟡 | 8 🟡 | 8 🟡 | 4 🟢 | 36 🟠 | 16 🟡 | 16 🟡 |
