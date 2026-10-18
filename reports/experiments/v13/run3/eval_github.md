# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 27 | 72 | 82 | 208 | 20 | 91 |
| MISUSE | 0 | 0 | 108 | 65 | 77 | 0 |
| MALICIOUS | 0 | 0 | 24 | 145 | 81 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.697 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.798 | 0.698 |
| RISKY_vs_BENIGN | 0.747 | 0.623 |

No rule applied: 91 calls. With an unresolved input: 662 calls.

Inputs that set the level most often:

- `get_file_contents.repo`: 148
- `create_or_update_file.repo`: 84
- `search_code.q`: 81
- `create_branch.repo`: 75
- `push_files.repo`: 64
- `create_pull_request_review.owner`: 62
- `list_commits.owner`: 57
- `search_repositories.query`: 49
- `create_or_update_file.branch`: 45
- `get_pull_request.owner`: 39
- `get_pull_request.repo`: 39
- `create_pull_request_review.repo`: 36
