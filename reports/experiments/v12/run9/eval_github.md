# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 24 | 35 | 405 | 36 | 0 |
| MISUSE | 0 | 0 | 51 | 83 | 81 | 35 |
| MALICIOUS | 0 | 0 | 0 | 144 | 106 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.503 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.710 | 0.698 |
| RISKY_vs_BENIGN | 0.606 | 0.623 |

No rule applied: 35 calls. With an unresolved input: 725 calls.

Inputs that set the level most often:

- `get_file_contents.repo`: 148
- `get_file_contents.owner`: 146
- `create_or_update_file.repo`: 84
- `search_code.q`: 81
- `create_branch.repo`: 75
- `push_files.repo`: 64
- `create_pull_request_review.owner`: 62
- `create_pull_request_review.repo`: 62
- `search_repositories.query`: 49
- `list_commits.repo`: 49
- `list_issues.owner`: 46
- `list_issues.repo`: 46
