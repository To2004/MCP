# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 7 | 62 | 202 | 0 | 0 | 229 |
| MISUSE | 0 | 0 | 187 | 0 | 0 | 63 |
| MALICIOUS | 0 | 0 | 250 | 0 | 0 | 0 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.655 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.798 | 0.698 |
| RISKY_vs_BENIGN | 0.726 | 0.623 |

No rule applied: 292 calls. With an unresolved input: 427 calls.

Inputs that set the level most often:

- `create_or_update_file.owner`: 84
- `create_or_update_file.path`: 84
- `create_or_update_file.content`: 84
- `create_or_update_file.branch`: 84
- `search_code.q`: 81
- `create_branch.owner`: 75
- `push_files.owner`: 64
- `push_files.files`: 64
- `push_files.files[].path`: 64
- `push_files.files[].content`: 64
- `create_pull_request_review.body`: 62
- `list_commits.owner`: 57
