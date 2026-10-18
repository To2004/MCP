# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 15 | 31 | 304 | 121 | 18 | 11 |
| MISUSE | 0 | 0 | 195 | 11 | 20 | 24 |
| MALICIOUS | 0 | 0 | 100 | 86 | 24 | 40 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.443 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.553 | 0.698 |
| RISKY_vs_BENIGN | 0.498 | 0.623 |

No rule applied: 75 calls. With an unresolved input: 470 calls.

Inputs that set the level most often:

- `get_file_contents.path`: 172
- `create_or_update_file.path`: 84
- `create_or_update_file.content`: 84
- `create_or_update_file.branch`: 84
- `search_code.q`: 81
- `push_files.repo`: 64
- `create_pull_request_review.owner`: 62
- `create_pull_request_review.repo`: 62
- `search_repositories.query`: 49
- `list_commits.repo`: 49
- `list_issues.repo`: 46
- `get_pull_request.owner`: 39
