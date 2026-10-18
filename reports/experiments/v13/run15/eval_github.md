# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 33 | 0 | 130 | 245 | 92 | 0 |
| MISUSE | 0 | 0 | 86 | 80 | 84 | 0 |
| MALICIOUS | 0 | 0 | 8 | 119 | 123 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.555 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.725 | 0.698 |
| RISKY_vs_BENIGN | 0.640 | 0.623 |

No rule applied: 0 calls. With an unresolved input: 809 calls.

Inputs that set the level most often:

- `get_file_contents.repo`: 148
- `create_or_update_file.repo`: 84
- `search_code.q`: 81
- `create_branch.repo`: 64
- `push_files.repo`: 64
- `create_pull_request_review.repo`: 62
- `search_repositories.query`: 49
- `list_commits.repo`: 49
- `list_issues.repo`: 39
- `search_users.q`: 35
- `get_pull_request.repo`: 34
- `get_issue.repo`: 28
