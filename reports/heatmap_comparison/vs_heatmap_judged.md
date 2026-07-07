# Scanner vs hand-made heatmaps  (scan-dir: reports/scan_judged_backup)

## Filesystem  (by filetype × tool)
- mapped cells: 48 | exact 23/48 (48%) | within-1 44/48 (92%)
  - .png×read_file: human=critical scanner=medium
  - .pdf×read_file: human=critical scanner=medium
  - .pdf×move_file: human=critical scanner=medium
  - .sql×read_file: human=critical scanner=medium

## SQLite  (by table × tool)
- mapped cells: 21 | exact 8/21 (38%) | within-1 19/21 (90%)
  - projects×write_query: human=medium scanner=critical
  - publications×write_query: human=low scanner=high

## Slack  (per-tool worst band — human vs scanner)
| tool | human | scanner |
| --- | --- | --- |
| slack_add_reaction | critical | high |
| slack_get_channel_history | critical | high |
| slack_get_thread_replies | critical | high |
| slack_get_user_profile | high | medium |
| slack_post_message | critical | critical |
| slack_reply_to_thread | critical | high |

- per-tool exact agreement: 1/6 (17%)
