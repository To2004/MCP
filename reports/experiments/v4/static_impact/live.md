# Static tool impact — live MCP servers (no LLM)

74 tools across 5 servers, classified by
`src/mcp_security/static_scoring/static_impact.py` from each tool's own
declaration only — name, description, parameters, annotation hints.
**No model call.** Regenerate with
`uv run python scripts/static_impact_report.py --group live`.

Ladder: **1** no effect · **2** metadata · **3** content read ·
**4** reversible write · **5** irreversible.

⚠ marks a tier reached with **no verb evidence** — a default, not a finding.

## Summary

| Server | Tools | t1 | t2 | t3 | t4 | t5 | state-changing | no verb evidence |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `calendar_real` | 13 | 1 | 4 | 2 | 4 | 2 | **6** | — |
| `slack_real` | 16 | 0 | 4 | 5 | 5 | 2 | **7** | — |
| `github_real` | 26 | 0 | 5 | 9 | 10 | 2 | **12** | — |
| `fs_corp_filesystem` | 14 | 0 | 6 | 4 | 3 | 1 | **4** | — |
| `sqlite_cbg_sqlite` | 5 | 0 | 2 | 1 | 1 | 1 | **2** | — |

Corpus: {1: 1, 2: 21, 3: 21, 4: 23, 5: 8} — 31/74 state-changing (42%).

## Per-server detail

### `calendar_real` — 13 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `delete-event` | **5** | tier-5 verbs: \bdelete\b | outbound |
| `manage-accounts` | **5** | tier-5 verbs: \bremove\b | — |
| `create-event` *(bulk)* | **4** | tier-4 verbs: \bcreate\b; bulk signal (array param or bulk wording) | outbound, path |
| `create-events` *(bulk)* | **4** | tier-4 verbs: \bcreate\b; bulk signal (array param or bulk wording) | outbound |
| `respond-to-event` | **4** | tier-4 verbs: \brespond\b | outbound |
| `update-event` *(bulk)* | **4** | tier-4 verbs: \bupdate\b; bulk signal (array param or bulk wording) | outbound |
| `get-event` *(bulk)* | **3** | tier-3 verbs: \bget\b, \bdetails?\b; bulk signal (array param or bulk wording) | — |
| `search-events` *(bulk)* | **3** | tier-3 verbs: \bsearch\b, \bquery\b; bulk signal (array param or bulk wording) | raw-query |
| `get-freebusy` *(bulk)* | **2** | tier-3 verbs: \bget\b, \bquery\b; return-shape marker -> capped at 2; bulk signal (array param or bulk wording) | — |
| `list-calendars` | **2** | tier-2 verbs: \blist\b | — |
| `list-colors` | **2** | tier-2 verbs: \blist\b, \bids?\b | — |
| `list-events` *(bulk)* | **2** | tier-2 verbs: \blist\b, \bnames?\b, \bids?\b; bulk signal (array param or bulk wording) | — |
| `get-current-time` | **1** | tier-3 verbs: \bget\b; return-shape marker -> capped at 1 | — |

Tier counts: {1: 1, 2: 4, 3: 2, 4: 4, 5: 2}

### `slack_real` — 16 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `usergroups_me` | **5** | tier-5 verbs: \bremove\b | — |
| `usergroups_users_update` | **5** | tier-5 verbs: \bremove\b | — |
| `conversations_add_message` | **4** | tier-4 verbs: \badd\b | — |
| `conversations_join` | **4** | tier-4 verbs: \bjoin\b | — |
| `conversations_leave` | **4** | tier-4 verbs: \bleave\b | — |
| `usergroups_create` | **4** | tier-4 verbs: \bcreate\b, \bjoin\b | — |
| `usergroups_update` | **4** | tier-4 verbs: \bupdate\b | — |
| `conversations_history` | **3** | tier-3 verbs: \bget\b, \bhistor(y/ies)\b | unbounded |
| `conversations_replies` | **3** | tier-3 verbs: \bget\b, \breplies\b, \bthread\b | unbounded |
| `conversations_search_messages` | **3** | tier-3 verbs: \bsearch\b | unbounded |
| `conversations_unreads` | **3** | tier-3 verbs: \bget\b | — |
| `users_search` | **3** | tier-3 verbs: \bsearch\b, \bdisplay\b, \bdetails?\b | unbounded, raw-query |
| `channels_list` | **2** | tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | unbounded, raw-query |
| `channels_me` | **2** | tier-2 verbs: \blist\b | unbounded |
| `conversations_mark` | **2** | tier-3 verbs: \bread\b; return-shape marker -> capped at 2 | — |
| `usergroups_list` | **2** | tier-2 verbs: \blist\b, \bcounts?\b, \bnames?\b | — |

Tier counts: {2: 4, 3: 5, 4: 5, 5: 2}

### `github_real` — 26 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `create_or_update_file` | **5** | tier-4 verbs: \bcreate\b, \bupdate\b; create-or-overwrite in one tool -> 5 | path |
| `merge_pull_request` | **5** | tier-5 verbs: \bmerge\b | — |
| `add_issue_comment` | **4** | tier-4 verbs: \badd\b, \bcomment\b | — |
| `create_branch` | **4** | tier-4 verbs: \bcreate\b, \bbranch\b | — |
| `create_issue` *(bulk)* | **4** | tier-4 verbs: \bcreate\b; bulk signal (array param or bulk wording) | — |
| `create_pull_request` | **4** | tier-4 verbs: \bcreate\b | — |
| `create_pull_request_review` *(bulk)* | **4** | tier-4 verbs: \bcreate\b; bulk signal (array param or bulk wording) | — |
| `create_repository` | **4** | tier-4 verbs: \bcreate\b | — |
| `fork_repository` | **4** | tier-4 verbs: \bfork\b | — |
| `push_files` *(bulk)* | **4** | tier-4 verbs: \bpush\b; bulk signal (array param or bulk wording) | — |
| `update_issue` *(bulk)* | **4** | tier-4 verbs: \bupdate\b; bulk signal (array param or bulk wording) | — |
| `update_pull_request_branch` | **4** | tier-4 verbs: \bbranch\b, \bupdate\b | — |
| `get_file_contents` | **3** | tier-3 verbs: \bget\b, \bcontents?\b | path |
| `get_issue` | **3** | tier-3 verbs: \bget\b, \bdetails?\b | — |
| `get_pull_request` | **3** | tier-3 verbs: \bget\b, \bdetails?\b | — |
| `get_pull_request_comments` | **3** | tier-3 verbs: \bget\b | — |
| `get_pull_request_files` | **3** | tier-3 verbs: \bget\b | — |
| `get_pull_request_reviews` | **3** | tier-3 verbs: \bget\b | — |
| `search_code` | **3** | tier-3 verbs: \bsearch\b | raw-query |
| `search_issues` | **3** | tier-3 verbs: \bsearch\b | raw-query |
| `search_users` | **3** | tier-3 verbs: \bsearch\b | raw-query |
| `get_pull_request_status` | **2** | tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | — |
| `list_commits` | **2** | tier-3 verbs: \bget\b; named a listing; only a generic read verb above it -> 2 | — |
| `list_issues` *(bulk)* | **2** | tier-2 verbs: \blist\b; bulk signal (array param or bulk wording) | — |
| `list_pull_requests` | **2** | tier-2 verbs: \blist\b | — |
| `search_repositories` | **2** | tier-3 verbs: \bsearch\b; generic verb over a CONTAINER -> catalog of names (2) | raw-query |

Tier counts: {2: 5, 3: 9, 4: 10, 5: 2}

### `fs_corp_filesystem` — 14 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `write_file` | **5** | readOnlyHint=false; destructiveHint=true; tier-5 verbs: \boverwrit(e/ing)\b, \bcompletely overwrite\b | path |
| `create_directory` *(bulk)* | **4** | readOnlyHint=false; tier-4 verbs: \bcreate\b; bulk signal (array param or bulk wording) | path |
| `edit_file` *(bulk)* | **4** | readOnlyHint=false; destructiveHint=true; tier-4 verbs: \bedit\b; bulk signal (array param or bulk wording) | path, dry-run, non-idempotent write |
| `move_file` | **4** | readOnlyHint=false; tier-4 verbs: \bmove\b | path, path, non-idempotent write |
| `read_file` | **3** | readOnlyHint=true -> ceiling 3; tier-3 verbs: \bread\b, \bcontents?\b | path |
| `read_media_file` | **3** | readOnlyHint=true -> ceiling 3; tier-3 verbs: \bread\b | path |
| `read_multiple_files` *(bulk)* | **3** | readOnlyHint=true -> ceiling 3; tier-3 verbs: \bread\b, \bcontents?\b, \banaly[sz](e/es/ed/ing/is)\b; bulk signal (array param or bulk wording) | — |
| `read_text_file` | **3** | readOnlyHint=true -> ceiling 3; tier-3 verbs: \bread\b, \btail\b, \bcontents?\b | path |
| `directory_tree` *(bulk)* | **2** | readOnlyHint=true -> ceiling 3; tier-3 verbs: \bget\b; generic verb; stated return is metadata ("'name', 'type' (file/directory), and 'ch") -> 2; bulk signal (array param or bulk wording) | path |
| `get_file_info` | **2** | readOnlyHint=true -> ceiling 3; tier-3 verbs: \bget\b, \bretrieve\b; return-shape marker -> capped at 2 | path |
| `list_allowed_directories` | **2** | readOnlyHint=true -> ceiling 3; tier-2 verbs: \blist\b | — |
| `list_directory` | **2** | readOnlyHint=true -> ceiling 3; tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | path |
| `list_directory_with_sizes` | **2** | readOnlyHint=true -> ceiling 3; tier-3 verbs: \bget\b; return-shape marker -> capped at 2 | path |
| `search_files` *(bulk)* | **2** | readOnlyHint=true -> ceiling 3; tier-3 verbs: \bsearch\b; generic verb; stated return is metadata ("full paths to all matching items") -> 2; bulk signal (array param or bulk wording) | path, glob |

Tier counts: {2: 6, 3: 4, 4: 3, 5: 1}

### `sqlite_cbg_sqlite` — 5 tools

| Tool | Impact | Why | Flags |
|---|:--:|---|---|
| `write_query` | **5** | tier-5 verbs: \bdelete\b, \bdrop\b | raw-query |
| `insert_row` | **4** | tier-4 verbs: \binsert\b | — |
| `read_query` | **3** | tier-3 verbs: \bread\b, \bquery\b | raw-query |
| `describe_table` | **2** | tier-2 verbs: \bdescribe\b, \bnames?\b | — |
| `list_tables` | **2** | tier-2 verbs: \blist\b | — |

Tier counts: {2: 2, 3: 1, 4: 1, 5: 1}
