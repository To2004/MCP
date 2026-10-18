# run5 — run log

What the job did, line by line. The log text is verbatim; the notes
beside it explain what each kind of line means.

## `calendar-20673505.log`

Runner log for `calendar` — one line per tool

```
2026-08-28 14:12:21,262 prompt b14d66ebf28b… (7368 chars)
2026-08-28 14:12:21,265 calendar: typing 13 tool(s) [shard 0/1]
2026-08-28 14:12:21,266   -> list-calendars (1 argument(s))
2026-08-28 14:12:33,248   -> list-events (8 argument(s))
2026-08-28 14:12:50,488   -> search-events (9 argument(s))
2026-08-28 14:13:13,476   -> get-event (4 argument(s))
2026-08-28 14:13:23,175   -> list-colors (1 argument(s))
2026-08-28 14:13:25,713   -> create-event (31 argument(s))
2026-08-28 14:14:52,605   -> create-events (5 argument(s))
2026-08-28 14:15:41,085   -> update-event (28 argument(s))
2026-08-28 14:16:44,276   -> delete-event (4 argument(s))
2026-08-28 14:16:51,080   -> get-freebusy (7 argument(s))
2026-08-28 14:17:09,146   -> get-current-time (2 argument(s))
2026-08-28 14:17:13,330   -> respond-to-event (8 argument(s))
2026-08-28 14:17:26,777   -> manage-accounts (2 argument(s))
2026-08-28 14:17:31,058 wrote /home/ovadyat/MCP/reports/experiments/v10/run5/calendar.json (13 tool(s), 0 failed, 0 schemaless)
```

**What those lines mean**

- `2026-08-28 14:12:21,262 prompt b14d66ebf28b… (7368 chars)`  
  The sha256 of the prompt text, read once at the start of the run and snapshotted as `prompt-AS-RUN.md`. Every result file repeats this digest, so results can never be read against the wrong prompt.
- `2026-08-28 14:12:21,265 calendar: typing 13 tool(s) [shard 0/1]`  
  How many tools the server contributed.
- `2026-08-28 14:12:21,266   -> list-calendars (1 argument(s))`  
  One model call. The gap to the next timestamp is how long it took; the first call of a run also pays for loading the model.

**Time per model call**

| tool | seconds |
|---|---|
| `list-calendars` | 12 |
| `list-events` | 17 |
| `search-events` | 23 |
| `get-event` | 10 |
| `list-colors` | 2 |
| `create-event` | 87 |
| `create-events` | 49 |
| `update-event` | 63 |
| `delete-event` | 7 |
| `get-freebusy` | 18 |
| `get-current-time` | 4 |
| `respond-to-event` | 13 |
| `manage-accounts` | 5 |

## `github-20673504.log`

Runner log for `github` — one line per tool

```
2026-08-28 14:12:28,154 prompt b14d66ebf28b… (7368 chars)
2026-08-28 14:12:28,155 github: typing 26 tool(s) [shard 0/1]
2026-08-28 14:12:28,156   -> create_or_update_file (7 argument(s))
2026-08-28 14:13:22,677   -> search_repositories (3 argument(s))
2026-08-28 14:13:33,018   -> create_repository (4 argument(s))
2026-08-28 14:13:39,083   -> get_file_contents (4 argument(s))
2026-08-28 14:13:46,401   -> push_files (5 argument(s))
2026-08-28 14:13:59,790   -> create_issue (7 argument(s))
2026-08-28 14:14:13,205   -> create_pull_request (8 argument(s))
2026-08-28 14:14:27,675   -> fork_repository (3 argument(s))
2026-08-28 14:14:33,678   -> create_branch (4 argument(s))
2026-08-28 14:14:41,195   -> list_commits (5 argument(s))
2026-08-28 14:14:51,576   -> list_issues (9 argument(s))
2026-08-28 14:15:09,348   -> update_issue (9 argument(s))
2026-08-28 14:15:27,661   -> add_issue_comment (4 argument(s))
2026-08-28 14:15:34,987   -> search_code (4 argument(s))
2026-08-28 14:15:48,376   -> search_issues (5 argument(s))
2026-08-28 14:16:04,543   -> search_users (5 argument(s))
2026-08-28 14:16:20,762   -> get_issue (3 argument(s))
2026-08-28 14:16:27,549   -> get_pull_request (3 argument(s))
2026-08-28 14:16:34,360   -> list_pull_requests (9 argument(s))
2026-08-28 14:16:51,268   -> create_pull_request_review (7 argument(s))
2026-08-28 14:17:13,347   -> merge_pull_request (6 argument(s))
2026-08-28 14:17:23,549   -> get_pull_request_files (3 argument(s))
2026-08-28 14:17:30,148   -> get_pull_request_status (3 argument(s))
2026-08-28 14:17:37,045   -> update_pull_request_branch (4 argument(s))
2026-08-28 14:17:44,912   -> get_pull_request_comments (3 argument(s))
2026-08-28 14:17:51,711   -> get_pull_request_reviews (3 argument(s))
2026-08-28 14:17:58,787 wrote /home/ovadyat/MCP/reports/experiments/v10/run5/github.json (26 tool(s), 0 failed, 0 schemaless)
```

**What those lines mean**

- `2026-08-28 14:12:28,154 prompt b14d66ebf28b… (7368 chars)`  
  The sha256 of the prompt text, read once at the start of the run and snapshotted as `prompt-AS-RUN.md`. Every result file repeats this digest, so results can never be read against the wrong prompt.
- `2026-08-28 14:12:28,155 github: typing 26 tool(s) [shard 0/1]`  
  How many tools the server contributed.
- `2026-08-28 14:12:28,156   -> create_or_update_file (7 argument(s))`  
  One model call. The gap to the next timestamp is how long it took; the first call of a run also pays for loading the model.

**Time per model call**

| tool | seconds |
|---|---|
| `create_or_update_file` | 54 |
| `search_repositories` | 11 |
| `create_repository` | 6 |
| `get_file_contents` | 7 |
| `push_files` | 13 |
| `create_issue` | 14 |
| `create_pull_request` | 14 |
| `fork_repository` | 6 |
| `create_branch` | 8 |
| `list_commits` | 10 |
| `list_issues` | 18 |
| `update_issue` | 18 |
| `add_issue_comment` | 7 |
| `search_code` | 14 |
| `search_issues` | 16 |
| `search_users` | 16 |
| `get_issue` | 7 |
| `get_pull_request` | 7 |
| `list_pull_requests` | 17 |
| `create_pull_request_review` | 22 |
| `merge_pull_request` | 10 |
| `get_pull_request_files` | 7 |
| `get_pull_request_status` | 7 |
| `update_pull_request_branch` | 7 |
| `get_pull_request_comments` | 7 |
| `get_pull_request_reviews` | 7 |

## `input-types-20673504.out`

SLURM job log — allocation and the shell script's own echoes

```
------------------------------------
Fri 28 Aug 2026 14:12:15 IDT
SLURM_JOBID:		20673504
SLURM_JOB_NODELIST:	cs-4090-10
SLURM_SCRATCH_DIR:	/scratch/ovadyat/20673504
Allocated Resouces:	cpu - 8 / mem - 49152 MB / gpu - 1
SLURM_GPU_INDEX:	2
Running as ovadyat from shabtaia account with normal QOS
------------------------------------
=== run folder: /home/ovadyat/MCP/reports/experiments/v10/run5 ===
=== cs-4090-10.auth.ad.bgu.ac.il: 1 GPU(s) ===
=== servers: github ===
  -> github on gpu0 (port 11600)
wrote /home/ovadyat/MCP/reports/experiments/v10/run5/INPUT_TYPES.md
```

**What those lines mean**

- `=== run folder: /home/ovadyat/MCP/reports/experiments/v10/run5 ===`  
  The folder this run writes to, chosen once by the job so all servers agree.
- `=== cs-4090-10.auth.ad.bgu.ac.il: 1 GPU(s) ===`  
  The node and how many GPUs it got; one Ollama is served per GPU.
- `=== servers: github ===`  
  Which servers were typed. `TYPE_SERVERS` overrides the default.
- `wrote /home/ovadyat/MCP/reports/experiments/v10/run5/INPUT_TYPES.md`  
  The result file, written once at the end of the server's pass.

## `input-types-20673505.out`

SLURM job log — allocation and the shell script's own echoes

```
------------------------------------
Fri 28 Aug 2026 14:12:16 IDT
SLURM_JOBID:		20673505
SLURM_JOB_NODELIST:	ise-4090-02
SLURM_SCRATCH_DIR:	/scratch/ovadyat/20673505
Allocated Resouces:	cpu - 8 / mem - 49152 MB / gpu - 1
SLURM_GPU_INDEX:	0
Running as ovadyat from shabtaia account with normal QOS
------------------------------------
=== run folder: /home/ovadyat/MCP/reports/experiments/v10/run5 ===
=== ise-4090-02.auth.ad.bgu.ac.il: 1 GPU(s) ===
=== servers: calendar ===
  -> calendar on gpu0 (port 11600)
wrote /home/ovadyat/MCP/reports/experiments/v10/run5/INPUT_TYPES.md
```

**What those lines mean**

- `=== run folder: /home/ovadyat/MCP/reports/experiments/v10/run5 ===`  
  The folder this run writes to, chosen once by the job so all servers agree.
- `=== ise-4090-02.auth.ad.bgu.ac.il: 1 GPU(s) ===`  
  The node and how many GPUs it got; one Ollama is served per GPU.
- `=== servers: calendar ===`  
  Which servers were typed. `TYPE_SERVERS` overrides the default.
- `wrote /home/ovadyat/MCP/reports/experiments/v10/run5/INPUT_TYPES.md`  
  The result file, written once at the end of the server's pass.

## `input-types-20673506.out`

SLURM job log — allocation and the shell script's own echoes

```
------------------------------------
Fri 28 Aug 2026 14:12:16 IDT
SLURM_JOBID:		20673506
SLURM_JOB_NODELIST:	ise-4090-17
SLURM_SCRATCH_DIR:	/scratch/ovadyat/20673506
Allocated Resouces:	cpu - 8 / mem - 49152 MB / gpu - 1
SLURM_GPU_INDEX:	2
Running as ovadyat from shabtaia account with normal QOS
------------------------------------
=== run folder: /home/ovadyat/MCP/reports/experiments/v10/run5 ===
=== ise-4090-17.auth.ad.bgu.ac.il: 1 GPU(s) ===
=== servers: slack ===
  -> slack on gpu0 (port 11600)
wrote /home/ovadyat/MCP/reports/experiments/v10/run5/INPUT_TYPES.md
```

**What those lines mean**

- `=== run folder: /home/ovadyat/MCP/reports/experiments/v10/run5 ===`  
  The folder this run writes to, chosen once by the job so all servers agree.
- `=== ise-4090-17.auth.ad.bgu.ac.il: 1 GPU(s) ===`  
  The node and how many GPUs it got; one Ollama is served per GPU.
- `=== servers: slack ===`  
  Which servers were typed. `TYPE_SERVERS` overrides the default.
- `wrote /home/ovadyat/MCP/reports/experiments/v10/run5/INPUT_TYPES.md`  
  The result file, written once at the end of the server's pass.

## `slack-20673506.log`

Runner log for `slack` — one line per tool

```
2026-08-28 14:12:23,121 prompt b14d66ebf28b… (7368 chars)
2026-08-28 14:12:23,123 slack: typing 16 tool(s) [shard 0/1]
2026-08-28 14:12:23,123   -> channels_list (6 argument(s))
2026-08-28 14:13:01,626   -> channels_me (3 argument(s))
2026-08-28 14:13:08,298   -> conversations_add_message (5 argument(s))
2026-08-28 14:13:24,799   -> conversations_history (4 argument(s))
2026-08-28 14:13:32,743   -> conversations_join (1 argument(s))
2026-08-28 14:13:35,483   -> conversations_leave (1 argument(s))
2026-08-28 14:13:38,022   -> conversations_mark (2 argument(s))
2026-08-28 14:13:43,582   -> conversations_replies (5 argument(s))
2026-08-28 14:13:52,044   -> conversations_search_messages (12 argument(s))
2026-08-28 14:14:30,279   -> conversations_unreads (6 argument(s))
2026-08-28 14:14:42,675   -> usergroups_create (4 argument(s))
2026-08-28 14:14:49,129   -> usergroups_list (3 argument(s))
2026-08-28 14:14:54,073   -> usergroups_me (2 argument(s))
2026-08-28 14:15:01,023   -> usergroups_update (5 argument(s))
2026-08-28 14:15:09,235   -> usergroups_users_update (2 argument(s))
2026-08-28 14:15:14,745   -> users_search (2 argument(s))
2026-08-28 14:15:21,963 wrote /home/ovadyat/MCP/reports/experiments/v10/run5/slack.json (16 tool(s), 0 failed, 0 schemaless)
```

**What those lines mean**

- `2026-08-28 14:12:23,121 prompt b14d66ebf28b… (7368 chars)`  
  The sha256 of the prompt text, read once at the start of the run and snapshotted as `prompt-AS-RUN.md`. Every result file repeats this digest, so results can never be read against the wrong prompt.
- `2026-08-28 14:12:23,123 slack: typing 16 tool(s) [shard 0/1]`  
  How many tools the server contributed.
- `2026-08-28 14:12:23,123   -> channels_list (6 argument(s))`  
  One model call. The gap to the next timestamp is how long it took; the first call of a run also pays for loading the model.

**Time per model call**

| tool | seconds |
|---|---|
| `channels_list` | 38 |
| `channels_me` | 7 |
| `conversations_add_message` | 16 |
| `conversations_history` | 8 |
| `conversations_join` | 3 |
| `conversations_leave` | 3 |
| `conversations_mark` | 5 |
| `conversations_replies` | 9 |
| `conversations_search_messages` | 38 |
| `conversations_unreads` | 12 |
| `usergroups_create` | 7 |
| `usergroups_list` | 5 |
| `usergroups_me` | 7 |
| `usergroups_update` | 8 |
| `usergroups_users_update` | 5 |
| `users_search` | 7 |

## What the run produced

| file | tools | arguments described | declared | failed | no schema |
|---|---|---|---|---|---|
| `calendar.json` | 13 | 155 | 110 | 0 | 0 |
| `github.json` | 26 | 136 | 130 | 0 | 0 |
| `slack.json` | 16 | 63 | 63 | 0 | 0 |
