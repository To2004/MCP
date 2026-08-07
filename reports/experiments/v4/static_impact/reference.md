# Static tool impact — reference MCP servers (no LLM)

120 tools across 15 servers, classified by
`src/mcp_security/static_scoring/static_impact.py` from each tool's own
declaration only — name, description, parameters, annotation hints.
**No model call.** Regenerate with
`uv run python scripts/static_impact_report.py --group reference`.

Ladder: **1** no effect · **2** metadata · **3** content read ·
**4** reversible write · **5** irreversible.

⚠ marks a tier reached with **no verb evidence** — a default, not a finding.

## Summary

| Server | Tools | t1 | t2 | t3 | t4 | t5 | state-changing | no verb evidence |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `brave-search` | 2 | 0 | 0 | 2 | 0 | 0 | **0** | — |
| `everything` | 8 | 2 | 0 | 5 | 1 | 0 | **1** | 5 |
| `fetch` | 1 | 0 | 0 | 1 | 0 | 0 | **0** | — |
| `filesystem` | 13 | 0 | 3 | 6 | 4 | 0 | **4** | — |
| `gdrive` | 2 | 0 | 0 | 2 | 0 | 0 | **0** | — |
| `git` | 12 | 0 | 1 | 5 | 5 | 1 | **6** | — |
| `github` | 44 | 0 | 13 | 16 | 11 | 4 | **15** | — |
| `memory` | 9 | 0 | 0 | 2 | 4 | 3 | **7** | — |
| `postgres` | 1 | 0 | 0 | 1 | 0 | 0 | **0** | — |
| `puppeteer` | 7 | 0 | 0 | 4 | 2 | 1 | **3** | 3 |
| `redis` | 4 | 0 | 0 | 2 | 1 | 1 | **2** | — |
| `sequentialthinking` | 1 | 0 | 0 | 1 | 0 | 0 | **0** | 1 |
| `slack` | 8 | 0 | 2 | 3 | 3 | 0 | **3** | — |
| `sqlite` | 6 | 0 | 1 | 2 | 2 | 1 | **3** | 1 |
| `time` | 2 | 2 | 0 | 0 | 0 | 0 | **0** | 1 |

Corpus: {1: 4, 2: 20, 3: 52, 4: 33, 5: 11} — 44/120 state-changing (37%).

## Per-server detail

### `brave-search` — 2 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `brave_local_search` | **3** | tier-3 verbs: \bsearch\b | raw-query, unbounded |
| `brave_web_search` | **3** | tier-3 verbs: \bsearch\b | raw-query, unbounded |

Tier counts: {3: 2}

### `everything` — 8 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `add` | **4** | tier-4 verbs: \badd\b | — |
| `annotatedMessage` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `getResourceReference` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `getTinyImage` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `longRunningOperation` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `printEnv` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `echo` | **1** | tier-1 verbs: \becho\b | — |
| `sampleLLM` | **1** | tier-1 verbs: \bcapabilit(y/ies)\b | — |

Tier counts: {1: 2, 3: 5, 4: 1}

### `fetch` — 1 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `fetch` | **3** | tier-3 verbs: \bfetch\b, \bcontents?\b | — |

Tier counts: {3: 1}

### `filesystem` — 13 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `create_directory` | **4** | tier-4 verbs: \bcreate\b | path |
| `edit_file` *(bulk)* | **4** | tier-4 verbs: \bedit\b; bulk signal (array param or bulk wording) | path, dry-run |
| `move_file` | **4** | tier-4 verbs: \bmove\b | path, path |
| `write_file` | **4** | tier-4 verbs: \bwrite\b | path |
| `list_directory` | **3** | tier-3 verbs: \bcontents?\b | path |
| `list_directory_with_sizes` | **3** | tier-3 verbs: \bcontents?\b | path |
| `read_media_file` | **3** | tier-3 verbs: \bread\b, \bcontents?\b | path |
| `read_multiple_files` *(bulk)* | **3** | tier-3 verbs: \bread\b, \bcontents?\b; bulk signal (array param or bulk wording) | — |
| `read_text_file` | **3** | tier-3 verbs: \bread\b, \bcontents?\b, \btext\b | path |
| `search_files` *(bulk)* | **3** | tier-3 verbs: \bsearch\b; bulk signal (array param or bulk wording) | path, glob |
| `directory_tree` *(bulk)* | **2** | tier-2 verbs: \bdirectory\b; bulk signal (array param or bulk wording) | path |
| `get_file_info` | **2** | tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | path |
| `list_allowed_directories` | **2** | tier-2 verbs: \blist\b | — |

Tier counts: {2: 3, 3: 6, 4: 4}

### `gdrive` — 2 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `gdrive_read_file` | **3** | tier-3 verbs: \bread\b, \bcontents?\b | — |
| `gdrive_search` | **3** | tier-3 verbs: \bsearch\b, \bquery\b | raw-query |

Tier counts: {3: 2}

### `git` — 12 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `git_reset` | **5** | tier-5 verbs: \breset\b | path |
| `git_add` *(bulk)* | **4** | tier-4 verbs: \badd\b; bulk signal (array param or bulk wording) | path |
| `git_checkout` | **4** | tier-4 verbs: \bcheckout\b | path |
| `git_commit` | **4** | tier-4 verbs: \bcommit\b | path |
| `git_create_branch` | **4** | tier-4 verbs: \bcreate\b, \bbranch\b | path |
| `git_init` | **4** | tier-4 verbs: \binit\b | path |
| `git_diff` | **3** | tier-3 verbs: \bdiff\b | path |
| `git_diff_staged` | **3** | tier-3 verbs: \bdiff\b | path |
| `git_diff_unstaged` | **3** | tier-3 verbs: \bdiff\b | path |
| `git_log` | **3** | tier-3 verbs: \bhistor(y/ies)\b | path |
| `git_show` | **3** | tier-3 verbs: \bshow\b, \bcontents?\b | path |
| `git_status` | **2** | tier-2 verbs: \bstatus\b | path |

Tier counts: {2: 1, 3: 5, 4: 5, 5: 1}

### `github` — 44 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `actions_run_trigger` | **5** | tier-5 verbs: \btrigger\b | — |
| `create_or_update_file` | **5** | tier-4 verbs: \bcreate\b, \bupdate\b; create-or-overwrite in one tool -> 5 | path |
| `delete_file` | **5** | tier-5 verbs: \bdelete\b | path |
| `merge_pull_request` | **5** | tier-5 verbs: \bmerge\b | — |
| `add_issue_comment` | **4** | tier-4 verbs: \badd\b, \bcomment\b | — |
| `create_branch` | **4** | tier-4 verbs: \bcreate\b, \bbranch\b | — |
| `create_gist` | **4** | tier-4 verbs: \bcreate\b | — |
| `create_issue` | **4** | tier-4 verbs: \bcreate\b | — |
| `create_pull_request` | **4** | tier-4 verbs: \bcreate\b | — |
| `create_repository` | **4** | tier-4 verbs: \bcreate\b | — |
| `fork_repository` | **4** | tier-4 verbs: \bfork\b | — |
| `get_commit` | **4** | tier-4 verbs: \bcommit\b | — |
| `push_files` *(bulk)* | **4** | tier-4 verbs: \bpush\b; bulk signal (array param or bulk wording) | — |
| `update_issue_body` | **4** | tier-4 verbs: \bupdate\b | — |
| `update_pull_request` | **4** | tier-4 verbs: \bupdate\b | — |
| `actions_get` | **3** | tier-3 verbs: \bget\b, \bdetails?\b | — |
| `dismiss_notification` | **3** | tier-3 verbs: \bread\b | — |
| `get_file_contents` | **3** | tier-3 verbs: \bget\b, \bcontents?\b | path |
| `get_job_logs` | **3** | tier-3 verbs: \bget\b | — |
| `get_latest_release` | **3** | tier-3 verbs: \bget\b | — |
| `get_team_members` | **3** | tier-3 verbs: \bget\b | — |
| `get_teams` | **3** | tier-3 verbs: \bget\b | — |
| `issue_read` | **3** | tier-3 verbs: \bread\b, \bdetails?\b | — |
| `list_commits` | **3** | tier-2 verbs: \blist\b; lists non-container items -> content read (3) | — |
| `list_dependabot_alerts` | **3** | tier-2 verbs: \blist\b; lists non-container items -> content read (3) | — |
| `list_notifications` | **3** | tier-2 verbs: \blist\b; lists non-container items -> content read (3) | — |
| `pull_request_read` | **3** | tier-3 verbs: \bread\b, \bdetails?\b | — |
| `search_code` | **3** | tier-3 verbs: \bread\b, \bsearch\b | raw-query |
| `search_issues` | **3** | tier-3 verbs: \bsearch\b | raw-query |
| `search_pull_requests` | **3** | tier-3 verbs: \bsearch\b | raw-query |
| `search_users` | **3** | tier-3 verbs: \bsearch\b | raw-query |
| `actions_list` | **2** | tier-2 verbs: \blist\b | — |
| `get_me` | **2** | tier-3 verbs: \bget\b; generic verb; stated return is metadata ("the authenticated user's GitHub profile ") -> 2 | — |
| `get_repository_tree` | **2** | tier-3 verbs: \bget\b; generic verb; stated return is metadata ("the recursive tree of a repository at a ") -> 2 | — |
| `list_branches` | **2** | tier-2 verbs: \blist\b | — |
| `list_code_scanning_alerts` | **2** | tier-2 verbs: \blist\b | — |
| `list_discussions` | **2** | tier-2 verbs: \blist\b | — |
| `list_issues` | **2** | tier-2 verbs: \blist\b | — |
| `list_pull_requests` | **2** | tier-2 verbs: \blist\b | — |
| `list_releases` | **2** | tier-2 verbs: \blist\b | — |
| `list_secret_scanning_alerts` | **2** | tier-2 verbs: \blist\b | — |
| `list_tags` | **2** | tier-2 verbs: \blist\b | — |
| `search_repositories` | **2** | tier-3 verbs: \bsearch\b; generic verb over a CONTAINER -> catalog of names (2) | raw-query |
| `star_repository` | **2** | tier-2 verbs: \bstar\b | — |

Tier counts: {2: 13, 3: 16, 4: 11, 5: 4}

### `memory` — 9 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `delete_entities` *(bulk)* | **5** | tier-5 verbs: \bdelete\b; bulk signal (array param or bulk wording) | — |
| `delete_observations` *(bulk)* | **5** | tier-5 verbs: \bdelete\b; bulk signal (array param or bulk wording) | — |
| `delete_relations` *(bulk)* | **5** | tier-5 verbs: \bdelete\b; bulk signal (array param or bulk wording) | — |
| `add_observations` *(bulk)* | **4** | tier-4 verbs: \badd\b; bulk signal (array param or bulk wording) | — |
| `create_entities` *(bulk)* | **4** | tier-4 verbs: \bcreate\b; bulk signal (array param or bulk wording) | — |
| `create_relations` *(bulk)* | **4** | tier-4 verbs: \bcreate\b; bulk signal (array param or bulk wording) | — |
| `open_nodes` *(bulk)* | **4** | tier-4 verbs: \bopen\b; bulk signal (array param or bulk wording) | — |
| `read_graph` | **3** | tier-3 verbs: \bread\b | — |
| `search_nodes` | **3** | tier-3 verbs: \bsearch\b, \bquery\b | raw-query |

Tier counts: {3: 2, 4: 4, 5: 3}

### `postgres` — 1 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `query` | **3** | tier-3 verbs: \bread\b, \bquery\b | raw-query |

Tier counts: {3: 1}

### `puppeteer` — 7 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `puppeteer_evaluate` | **5** | tier-5 verbs: \beval(uate)?s?\b[^.]{0,20}\b(javascript/js/code/script/expression)\b | raw-command |
| `puppeteer_click` | **4** | tier-4 verbs: \bclick\b | — |
| `puppeteer_fill` | **4** | tier-4 verbs: \bfill\b | — |
| `puppeteer_hover` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `puppeteer_navigate` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `puppeteer_screenshot` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `puppeteer_select` | **3** | tier-3 verbs: \bselect\b | — |

Tier counts: {3: 4, 4: 2, 5: 1}

### `redis` — 4 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `delete` | **5** | tier-5 verbs: \bdelete\b | — |
| `set` | **4** | tier-4 verbs: \bset\b | — |
| `get` | **3** | tier-3 verbs: \bget\b | — |
| `list` | **3** | tier-2 verbs: \blist\b, \bglob\b; lists non-container items -> content read (3) | glob |

Tier counts: {3: 2, 4: 1, 5: 1}

### `sequentialthinking` — 1 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `sequentialthinking` | **3** ⚠ | no verb evidence -> annotation/default | — |

Tier counts: {3: 1}

### `slack` — 8 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `slack_add_reaction` | **4** | tier-4 verbs: \badd\b | — |
| `slack_post_message` | **4** | tier-4 verbs: \bpost\b | — |
| `slack_reply_to_thread` | **4** | tier-4 verbs: \breply\b | — |
| `slack_get_channel_history` | **3** | tier-3 verbs: \bget\b, \bhistor(y/ies)\b | unbounded |
| `slack_get_thread_replies` | **3** | tier-3 verbs: \bget\b, \breplies\b, \bthread\b | — |
| `slack_get_user_profile` | **3** | tier-3 verbs: \bget\b | — |
| `slack_get_users` | **2** | tier-3 verbs: \bget\b; generic verb; stated return is metadata ("a paginated list of all workspace users") -> 2 | unbounded |
| `slack_list_channels` | **2** | tier-2 verbs: \blist\b | unbounded |

Tier counts: {2: 2, 3: 3, 4: 3}

### `sqlite` — 6 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `write_query` | **5** | tier-5 verbs: \bdelete\b, \bdrop\b | raw-query |
| `append_insight` | **4** | tier-4 verbs: \bappend\b | — |
| `create_table` | **4** | tier-4 verbs: \bcreate\b | raw-query |
| `describe_table` | **3** ⚠ | no verb evidence -> annotation/default | — |
| `read_query` | **3** | tier-3 verbs: \bread\b, \bquery\b | raw-query |
| `list_tables` | **2** | tier-2 verbs: \blist\b, \bnames?\b | — |

Tier counts: {2: 1, 3: 2, 4: 2, 5: 1}

### `time` — 2 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `convert_time` | **1** ⚠ | no verb evidence -> annotation/default; return-shape marker -> capped at 1 | — |
| `get_current_time` | **1** | tier-3 verbs: \bget\b; return-shape marker -> capped at 1 | — |

Tier counts: {1: 2}
