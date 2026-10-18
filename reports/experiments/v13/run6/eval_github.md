# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 15 | 46 | 308 | 99 | 32 | 0 |
| MISUSE | 0 | 0 | 219 | 4 | 27 | 0 |
| MALICIOUS | 0 | 0 | 202 | 24 | 24 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.495 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.521 | 0.698 |
| RISKY_vs_BENIGN | 0.508 | 0.623 |

No rule applied: 0 calls. With an unresolved input: 481 calls.

Inputs that set the level most often:

- `get_file_contents.path`: 172
- `create_or_update_file.path`: 84
- `create_or_update_file.content`: 84
- `create_or_update_file.branch`: 84
- `search_code.q`: 81
- `create_branch.repo`: 75
- `push_files.files`: 64
- `push_files.files[].path`: 64
- `push_files.files[].content`: 64
- `create_pull_request_review.owner`: 62
- `create_pull_request_review.repo`: 62
- `search_repositories.query`: 49
