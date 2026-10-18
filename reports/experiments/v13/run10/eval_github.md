# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 15 | 8 | 396 | 48 | 22 | 11 |
| MISUSE | 0 | 0 | 164 | 4 | 58 | 24 |
| MALICIOUS | 0 | 0 | 34 | 74 | 102 | 40 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.547 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.733 | 0.698 |
| RISKY_vs_BENIGN | 0.640 | 0.623 |

No rule applied: 75 calls. With an unresolved input: 734 calls.

Inputs that set the level most often:

- `get_file_contents.owner`: 172
- `get_file_contents.path`: 172
- `create_or_update_file.repo`: 84
- `search_code.q`: 81
- `push_files.repo`: 64
- `create_pull_request_review.repo`: 62
- `search_repositories.query`: 49
- `list_commits.repo`: 49
- `list_issues.repo`: 42
- `get_pull_request.owner`: 39
- `get_pull_request.repo`: 39
- `search_users.q`: 35
