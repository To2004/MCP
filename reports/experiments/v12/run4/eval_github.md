# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 0 | 6 | 230 | 29 | 235 | 0 |
| MISUSE | 0 | 0 | 86 | 0 | 164 | 0 |
| MALICIOUS | 0 | 0 | 8 | 62 | 180 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.585 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.683 | 0.698 |
| RISKY_vs_BENIGN | 0.634 | 0.623 |

No rule applied: 0 calls. With an unresolved input: 665 calls.

Inputs that set the level most often:

- `get_file_contents.owner`: 172
- `create_or_update_file.owner`: 84
- `create_or_update_file.branch`: 84
- `create_branch.owner`: 75
- `create_branch.from_branch`: 75
- `search_code.q`: 66
- `push_files.owner`: 64
- `create_pull_request_review.owner`: 62
- `create_pull_request_review.repo`: 62
- `list_commits.owner`: 57
- `create_branch.repo`: 52
- `search_code.page`: 50
