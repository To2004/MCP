# Static tool impact — deterministic ladder, no LLM

Tool impact for every server in `v3/five_level_v2_pure_v3`, computed by
`src/mcp_security/static_scoring/static_impact.py` from each tool's own
declaration (name, description, parameters, MCP annotation hints) — **no model
call**. The `LLM` column is the v3 scan's model-assigned impact, shown for
comparison only; it is not ground truth.

Ladder: **1** no effect · **2** metadata · **3** content read · **4** reversible
write · **5** irreversible or open-world.

Rules: annotation ceiling (`readOnlyHint` ⇒ ≤3) · ambiguous noun/verb words
counted in the tool NAME only · negation guard (a verb after never/do-not is a
prohibition, not a capability) · return-shape caps (liveness markers in the name,
return markers in the opening sentence; never lowers a mutation) · scoped-edit
exception · create-or-overwrite ⇒ 5. The "bulk drops a safety ⇒ +1" rule was
**removed** in v4.

## calendar:real

| Tool | Static | LLM | Match | Evidence |
|---|:-:|:-:|:-:|---|
| `delete-event` | **5** | 5 | ✓ | tier-5 verbs: delete |
| `manage-accounts` | **5** | 5 | ✓ | tier-5 verbs: remove |
| `create-event` | **4** | 4 | ✓ | tier-4 verbs: create |
| `create-events` | **4** | 5 | ✗ | tier-4 verbs: create |
| `respond-to-event` | **4** | 5 | ✗ | tier-4 verbs: respond |
| `update-event` | **4** | 4 | ✓ | tier-4 verbs: update |
| `get-event` | **3** | 3 | ✓ | tier-3 verbs: get, details? |
| `search-events` | **3** | 3 | ✓ | tier-3 verbs: search, query |
| `get-freebusy` | **2** | 2 | ✓ | tier-3 verbs: get, query; return-shape marker -> capped at 2 |
| `list-calendars` | **2** | 2 | ✓ | tier-2 verbs: list |
| `list-colors` | **2** | 2 | ✓ | tier-2 verbs: list |
| `list-events` | **2** | 3 | ✗ | tier-2 verbs: list, names? |
| `get-current-time` | **1** | 1 | ✓ | tier-3 verbs: get; return-shape marker -> capped at 1 |

Agreement with the LLM: **10/13 = 77%**

## slack:real

| Tool | Static | LLM | Match | Evidence |
|---|:-:|:-:|:-:|---|
| `usergroups_me` | **5** | 5 | ✓ | tier-5 verbs: remove |
| `usergroups_users_update` | **5** | 5 | ✓ | tier-5 verbs: remove |
| `conversations_add_message` | **4** | 4 | ✓ | tier-4 verbs: add |
| `conversations_join` | **4** | 5 | ✗ | tier-4 verbs: join |
| `conversations_leave` | **4** | 4 | ✓ | tier-4 verbs: leave |
| `usergroups_create` | **4** | 4 | ✓ | tier-4 verbs: create, add, join |
| `usergroups_update` | **4** | 4 | ✓ | tier-4 verbs: update |
| `conversations_history` | **3** | 3 | ✓ | tier-3 verbs: get, histor(y|ies) |
| `conversations_replies` | **3** | 3 | ✓ | tier-3 verbs: get, replies |
| `conversations_search_messages` | **3** | 3 | ✓ | tier-3 verbs: search |
| `conversations_unreads` | **3** | 3 | ✓ | tier-3 verbs: get |
| `users_search` | **3** | 3 | ✓ | tier-3 verbs: search, details? |
| `channels_list` | **2** | 2 | ✓ | tier-3 verbs: get; return-shape marker -> capped at 2 |
| `channels_me` | **2** | 2 | ✓ | tier-2 verbs: list |
| `conversations_mark` | **2** | 2 | ✓ | tier-3 verbs: read; return-shape marker -> capped at 2 |
| `usergroups_list` | **2** | 2 | ✓ | tier-2 verbs: list, counts?, names? |

Agreement with the LLM: **15/16 = 94%**

## github:real

| Tool | Static | LLM | Match | Evidence |
|---|:-:|:-:|:-:|---|
| `create_or_update_file` | **5** | 5 | ✓ | tier-4 verbs: create, update; create-or-overwrite in one tool -> 5 |
| `merge_pull_request` | **5** | 5 | ✓ | tier-5 verbs: merge |
| `push_files` | **5** | 5 | ✓ | tier-5 verbs: push |
| `add_issue_comment` | **4** | 4 | ✓ | tier-4 verbs: add, comment |
| `create_branch` | **4** | 4 | ✓ | tier-4 verbs: create, branch |
| `create_issue` | **4** | 4 | ✓ | tier-4 verbs: create |
| `create_pull_request` | **4** | 4 | ✓ | tier-4 verbs: create |
| `create_pull_request_review` | **4** | 4 | ✓ | tier-4 verbs: create |
| `create_repository` | **4** | 4 | ✓ | tier-4 verbs: create |
| `fork_repository` | **4** | 5 | ✗ | tier-4 verbs: fork |
| `update_issue` | **4** | 4 | ✓ | tier-4 verbs: update |
| `update_pull_request_branch` | **4** | 4 | ✓ | tier-4 verbs: update, branch |
| `get_file_contents` | **3** | 3 | ✓ | tier-3 verbs: get, contents? |
| `get_issue` | **3** | 3 | ✓ | tier-3 verbs: get, details? |
| `get_pull_request` | **3** | 3 | ✓ | tier-3 verbs: get, details? |
| `get_pull_request_comments` | **3** | 3 | ✓ | tier-3 verbs: get |
| `get_pull_request_files` | **3** | 3 | ✓ | tier-3 verbs: get |
| `get_pull_request_reviews` | **3** | 3 | ✓ | tier-3 verbs: get |
| `list_commits` | **3** | 2 | ✗ | tier-3 verbs: get |
| `search_code` | **3** | 3 | ✓ | tier-3 verbs: search |
| `search_issues` | **3** | 3 | ✓ | tier-3 verbs: search |
| `search_repositories` | **3** | 2 | ✗ | tier-3 verbs: search |
| `search_users` | **3** | 2 | ✗ | tier-3 verbs: search |
| `get_pull_request_status` | **2** | 2 | ✓ | tier-3 verbs: get; return-shape marker -> capped at 2 |
| `list_issues` | **2** | 2 | ✓ | tier-2 verbs: list |
| `list_pull_requests` | **2** | 2 | ✓ | tier-2 verbs: list |

Agreement with the LLM: **22/26 = 85%**

## fs:corp_filesystem

| Tool | Static | LLM | Match | Evidence |
|---|:-:|:-:|:-:|---|
| `write_file` | **5** | 5 | ✓ | readOnlyHint=false; destructiveHint=true; tier-5 verbs: overwrit(e|ing), compl |
| `create_directory` | **4** | 4 | ✓ | readOnlyHint=false; tier-4 verbs: create |
| `edit_file` | **4** | 4 | ✓ | readOnlyHint=false; destructiveHint=true; tier-4 verbs: edit |
| `move_file` | **4** | 4 | ✓ | readOnlyHint=false; tier-4 verbs: move |
| `directory_tree` | **3** | 2 | ✗ | readOnlyHint=true -> ceiling 3; tier-3 verbs: get, view |
| `read_file` | **3** | 3 | ✓ | readOnlyHint=true -> ceiling 3; tier-3 verbs: read, contents? |
| `read_media_file` | **3** | 3 | ✓ | readOnlyHint=true -> ceiling 3; tier-3 verbs: read |
| `read_multiple_files` | **3** | 3 | ✓ | readOnlyHint=true -> ceiling 3; tier-3 verbs: read, contents? |
| `read_text_file` | **3** | 3 | ✓ | readOnlyHint=true -> ceiling 3; tier-3 verbs: read, contents? |
| `search_files` | **3** | 2 | ✗ | readOnlyHint=true -> ceiling 3; tier-3 verbs: search |
| `get_file_info` | **2** | 2 | ✓ | readOnlyHint=true -> ceiling 3; tier-3 verbs: get, retrieve; return-shape mark |
| `list_allowed_directories` | **2** | 2 | ✓ | readOnlyHint=true -> ceiling 3; tier-2 verbs: list |
| `list_directory` | **2** | 2 | ✓ | readOnlyHint=true -> ceiling 3; tier-3 verbs: get; return-shape marker -> capp |
| `list_directory_with_sizes` | **2** | 2 | ✓ | readOnlyHint=true -> ceiling 3; tier-3 verbs: get; return-shape marker -> capp |

Agreement with the LLM: **12/14 = 86%**

## Summary

| Server | Tools | Static == LLM |
|---|--:|--:|
| `calendar:real` | 13 | 10/13 = 77% |
| `slack:real` | 16 | 15/16 = 94% |
| `github:real` | 26 | 22/26 = 85% |
| `fs:corp_filesystem` | 14 | 12/14 = 86% |
| **total** | **69** | **59/69 = 86%** |
