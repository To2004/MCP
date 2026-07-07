# Scanner vs hand-made heatmaps  (scan-dir: reports/scan)

## Filesystem  (by filetype × tool)
- mapped cells: 48 | exact 17/48 (35%) | within-1 42/48 (88%)
  - .png×read_file: human=critical scanner=medium
  - .pdf×read_file: human=critical scanner=medium
  - .pdf×move_file: human=critical scanner=medium
  - .sql×read_file: human=critical scanner=medium
  - .csv×read_file: human=critical scanner=medium
  - .txt×read_file: human=critical scanner=medium

## SQLite  (by table × tool)
- mapped cells: 21 | exact 2/21 (10%) | within-1 15/21 (71%)
  - employees×describe_table: human=low scanner=high
  - projects×describe_table: human=low scanner=high
  - projects×read_query: human=low scanner=high
  - datasets×describe_table: human=low scanner=high
  - grants×describe_table: human=low scanner=high
  - api_keys×describe_table: human=low scanner=high

## Slack  (per-tool worst band — human vs scanner)
| tool | human | scanner |
| --- | --- | --- |
| slack_add_reaction | critical | medium |
| slack_get_channel_history | critical | high |
| slack_get_thread_replies | critical | high |
| slack_get_user_profile | high | medium |
| slack_post_message | critical | critical |
| slack_reply_to_thread | critical | medium |

- per-tool exact agreement: 1/6 (17%)
