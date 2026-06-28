# Scan — github:cbg

_kind=github · provenance=llm-scan · model_reviewed=True · bands={'low': 14, 'medium': 13, 'high': 23, 'critical': 16}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: code repository management
- **asset_meaning**: repositories containing source code, documentation, or sensitive configuration files
- **blast_radius_meaning**: the extent of changes a tool can make to the repository, from reading files (narrow touch) to modifying or deleting files and creating pull requests (severe action)
- **worked_example**: The tool 'delete_file' used on the asset 'infra-config' is highly severe because it can permanently remove sensitive configuration files.

## Tool impact

| tool | impact |
| --- | --- |
| `search_repositories` | 1 |
| `get_file_contents` | 1 |
| `list_commits` | 1 |
| `get_issue` | 1 |
| `create_issue` | 2 |
| `create_or_update_file` | 3 |
| `push_files` | 3 |
| `delete_file` | 3 |
| `create_pull_request` | 3 |
| `merge_pull_request` | 3 |
| `fork_repository` | 2 |

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

| asset \ tool | search_repositories | get_file_contents | list_commits | get_issue | create_issue | create_or_update_file | push_files | delete_file | create_pull_request | merge_pull_request | fork_repository |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 3 🟢 | 1 🟢 | 3 🟢 | 1 🟢 | 2 🟡 | 9 🟠 | 9 🟠 | 9 🟠 | 9 🟠 | 12 🔴 | 6 🟡 |
| `internal-docs` | 9 🟠 | 3 🟡 | 9 🟠 | 3 🟢 | 6 🟢 | 27 🟠 | 36 🔴 | 36 🔴 | 27 🟠 | 36 🔴 | 18 🟡 |
| `backend-api` | 12 🟠 | 4 🟡 | 12 🟠 | 4 🟢 | 0 🟢 | 36 🟠 | 36 🟠 | 48 🔴 | 36 🟠 | 48 🔴 | 16 🟡 |
| `payments-service` | 12 🟠 | 4 🟡 | 12 🟠 | 4 🟢 | 8 🟢 | 36 🟠 | 36 🟠 | 48 🔴 | 36 🟠 | 48 🔴 | 24 🟡 |
| `infra-config` | 10 🟠 | 10 🟠 | 5 🟡 | 5 🟢 | 0 🟢 | 45 🔴 | 60 🔴 | 60 🔴 | 60 🟠 | 60 🔴 | 30 🟡 |
| `ml-research` | 4 🟡 | 4 🟡 | 12 🟠 | 4 🟢 | 8 🟢 | 48 🔴 | 36 🔴 | 48 🔴 | 36 🟠 | 48 🔴 | 24 🟡 |
