# github (github_helios): 1000 real calls

| category | 1 | 2 | 3 | 4 | 5 | no rule |
|---|---|---|---|---|---|---|
| BENIGN | 139 | 0 | 70 | 0 | 0 | 291 |
| MISUSE | 63 | 0 | 97 | 0 | 31 | 59 |
| MALICIOUS | 0 | 0 | 124 | 0 | 0 | 126 |

| separation (AUC, 0.5 = none) | input rules | tool only |
|---|---|---|
| MISUSE_vs_BENIGN | 0.735 | 0.548 |
| MALICIOUS_vs_BENIGN | 0.608 | 0.698 |
| RISKY_vs_BENIGN | 0.672 | 0.623 |

No rule applied: 476 calls. With an unresolved input: 0 calls.

Inputs that set the level most often:

- `get_file_contents.path`: 172
- `create_or_update_file.path`: 84
- `search_code.q`: 81
- `push_files.files[].path`: 64
- `search_repositories.query`: 49
- `create_issue.body`: 34
- `search_issues.q`: 26
- `add_issue_comment.body`: 14
