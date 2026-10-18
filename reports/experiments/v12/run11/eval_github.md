# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 24 | 35 | 326 | 115 | 0 |
| MISUSE | 0 | 0 | 51 | 83 | 81 | 35 |
| MALICIOUS | 0 | 0 | 8 | 86 | 156 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.451 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.708 | 0.698 |
| RISKY_vs_BENIGN | 0.579 | 0.623 |

No rule applied: 35 calls. With an unresolved input: 653 calls.

Inputs that set the level most often:

- `get_file_contents.repo`: 148
- `get_file_contents.owner`: 146
- `create_or_update_file.branch`: 84
- `search_code.q`: 81
- `create_branch.repo`: 75
- `push_files.repo`: 64
- `create_pull_request_review.owner`: 62
- `create_pull_request_review.repo`: 62
- `search_repositories.query`: 49
- `list_commits.repo`: 49
- `list_issues.state`: 46
- `get_pull_request.owner`: 39
