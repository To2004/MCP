# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 15 | 42 | 260 | 113 | 36 | 34 |
| MISUSE | 0 | 24 | 101 | 68 | 57 | 0 |
| MALICIOUS | 0 | 40 | 8 | 50 | 144 | 8 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.633 | 0.572 |
| MALICIOUS_vs_BENIGN | 0.756 | 0.708 |
| RISKY_vs_BENIGN | 0.695 | 0.640 |

No rule applied: 42 calls. With an unresolved input: 767 calls.

Inputs that set the level most often:

- `get_file_contents.repo`: 148
- `create_or_update_file.branch`: 84
- `search_code.q`: 81
- `create_branch.owner`: 75
- `push_files.repo`: 64
- `search_repositories.query`: 49
- `list_commits.repo`: 49
- `list_issues.repo`: 46
- `get_pull_request.owner`: 39
- `get_pull_request.repo`: 39
- `create_or_update_file.repo`: 39
- `create_pull_request_review.repo`: 36
