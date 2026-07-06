# Scan — github:real

_kind=github · provenance=llm-scan · model_reviewed=True · bands={'low': 32, 'medium': 58, 'high': 58, 'critical': 8}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: GitHub repository management
- **asset_meaning**: A GitHub repository containing code or documentation
- **blast_radius_meaning**: The extent of changes a tool can make within the repository, from modifying a single file to affecting multiple files and branches.
- **worked_example**: The tool 'create_or_update_file' on the asset class 'infra-config' could introduce irreversible changes if used to modify sensitive secrets, escalating severity.

## Tool impact

| tool | impact |
| --- | --- |
| `create_or_update_file` | 3 |
| `search_repositories` | 1 |
| `create_repository` | 2 |
| `get_file_contents` | 1 |
| `push_files` | 3 |
| `create_issue` | 2 |
| `create_pull_request` | 2 |
| `fork_repository` | 2 |
| `create_branch` | 2 |
| `list_commits` | 1 |
| `list_issues` | 1 |
| `update_issue` | 2 |
| `add_issue_comment` | 2 |
| `search_code` | 1 |
| `search_issues` | 1 |
| `search_users` | 1 |
| `get_issue` | 1 |
| `get_pull_request` | 1 |
| `list_pull_requests` | 1 |
| `create_pull_request_review` | 2 |
| `merge_pull_request` | 3 |
| `get_pull_request_files` | 1 |
| `get_pull_request_status` | 1 |
| `update_pull_request_branch` | 2 |
| `get_pull_request_comments` | 1 |
| `get_pull_request_reviews` | 1 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `public-website` | 1 |
| `internal-docs` | 3 |
| `backend-api` | 4 |
| `payments-service` | 4 |
| `infra-config` | 5 |
| `ml-research` | 4 |

## Risk matrix (score · band)

| asset \ tool | create_or_update_file | search_repositories | create_repository | get_file_contents | push_files | create_issue | create_pull_request | fork_repository | create_branch | list_commits | list_issues | update_issue | add_issue_comment | search_code | search_issues | search_users | get_issue | get_pull_request | list_pull_requests | create_pull_request_review | merge_pull_request | get_pull_request_files | get_pull_request_status | update_pull_request_branch | get_pull_request_comments | get_pull_request_reviews |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 6 🟡 | 4 🟢 | 0 🟢 | 4 🟢 | 9 🟡 | 2 🟢 | 4 🟢 | 8 🟡 | 4 🟢 | 4 🟢 | 4 🟢 | 4 🟢 | 2 🟢 | 4 🟢 | 4 🟢 | 1 🟢 | 1 🟢 | 1 🟢 | 4 🟢 | 4 🟢 | 9 🟡 | 4 🟢 | 1 🟢 | 6 🟢 | 1 🟢 | 1 🟢 |
| `internal-docs` | 18 🟠 | 12 🟡 | 0 🟢 | 12 🟡 | 27 🟠 | 6 🟢 | 12 🟡 | 24 🟠 | 12 🟡 | 12 🟡 | 12 🟡 | 12 🟡 | 6 🟢 | 12 🟡 | 12 🟡 | 3 🟢 | 3 🟢 | 3 🟢 | 12 🟡 | 12 🟡 | 27 🟠 | 12 🟡 | 3 🟢 | 18 🟡 | 12 🟡 | 3 🟢 |
| `backend-api` | 24 🟠 | 16 🟠 | 16 🟡 | 16 🟠 | 48 🔴 | 16 🟡 | 16 🟡 | 32 🟠 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟡 | 8 🟡 | 16 🟠 | 16 🟠 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 16 🟡 | 48 🔴 | 16 🟠 | 8 🟡 | 24 🟠 | 16 🟠 | 16 🟠 |
| `payments-service` | 24 🟠 | 16 🟠 | 0 🟢 | 16 🟠 | 48 🔴 | 8 🟡 | 16 🟡 | 32 🟠 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟡 | 8 🟡 | 16 🟠 | 16 🟠 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 16 🟡 | 48 🔴 | 16 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 |
| `infra-config` | 30 🟠 | 20 🟠 | 0 🟠 | 20 🟠 | 75 🔴 | 10 🟠 | 20 🟠 | 40 🟠 | 20 🟠 | 20 🟠 | 20 🟠 | 20 🟠 | 10 🟠 | 20 🟠 | 20 🟠 | 0 🟡 | 5 🟡 | 5 🟡 | 20 🟠 | 20 🟠 | 60 🔴 | 20 🟠 | 5 🟡 | 40 🟠 | 10 🟡 | 20 🟠 |
| `ml-research` | 24 🟠 | 16 🟠 | 0 🟢 | 16 🟠 | 48 🔴 | 16 🟡 | 16 🟡 | 32 🟠 | 16 🟡 | 16 🟠 | 16 🟠 | 16 🟡 | 8 🟡 | 16 🟠 | 16 🟠 | 4 🟡 | 4 🟡 | 4 🟡 | 16 🟠 | 16 🟡 | 48 🔴 | 16 🟠 | 8 🟡 | 24 🟠 | 8 🟡 | 8 🟡 |
