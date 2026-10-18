# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 27 | 0 | 313 | 98 | 51 | 11 |
| MISUSE | 0 | 0 | 132 | 68 | 26 | 24 |
| MALICIOUS | 0 | 0 | 34 | 69 | 99 | 48 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.523 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.652 | 0.698 |
| RISKY_vs_BENIGN | 0.587 | 0.623 |

No rule applied: 83 calls. With an unresolved input: 726 calls.

Inputs that set the level most often:

- `get_file_contents.repo`: 148
- `create_or_update_file.repo`: 84
- `search_code.q`: 81
- `push_files.repo`: 64
- `create_pull_request_review.repo`: 62
- `search_repositories.query`: 49
- `list_commits.repo`: 49
- `list_issues.repo`: 46
- `get_pull_request.owner`: 39
- `search_users.q`: 35
- `get_pull_request.repo`: 34
- `create_issue.repo`: 34
