# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 33 | 0 | 150 | 231 | 86 | 0 |
| MISUSE | 0 | 0 | 86 | 76 | 88 | 0 |
| MALICIOUS | 0 | 0 | 8 | 100 | 142 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.578 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.765 | 0.698 |
| RISKY_vs_BENIGN | 0.671 | 0.623 |

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
