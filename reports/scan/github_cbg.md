# Scan — github:cbg

_kind=github · provenance=llm-scan · model_reviewed=True · bands={'low': 10, 'medium': 21, 'high': 26, 'critical': 9}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: code repository management
- **asset_meaning**: repositories containing source code, documentation, or sensitive configuration files
- **blast_radius_meaning**: the extent of changes a tool can make to the repositories; from reading files (narrow touch) to modifying or deleting files and merging pull requests (severe action)
- **worked_example**: The tool 'delete_file' used on the asset 'infra-config' is highly severe because it can permanently remove sensitive configuration and secret files.

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
| `create_pull_request` | 2 |
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
| `public-website` | 4 🟢 | 1 🟢 | 4 🟢 | 1 🟢 | 2 🟢 | 6 🟡 | 9 🟡 | 6 🟡 | 4 🟢 | 12 🟡 | 8 🟡 |
| `internal-docs` | 12 🟡 | 3 🟢 | 12 🟡 | 3 🟢 | 6 🟢 | 18 🟠 | 27 🟠 | 18 🟠 | 12 🟡 | 36 🟠 | 24 🟠 |
| `backend-api` | 16 🟠 | 4 🟡 | 16 🟠 | 4 🟡 | 0 🟢 | 24 🟠 | 36 🟠 | 60 🔴 | 16 🟡 | 48 🔴 | 32 🟠 |
| `payments-service` | 16 🟠 | 4 🟡 | 16 🟠 | 4 🟡 | 8 🟡 | 24 🟠 | 36 🟠 | 24 🟠 | 16 🟡 | 48 🔴 | 32 🟠 |
| `infra-config` | 20 🟠 | 10 🟡 | 20 🟠 | 10 🟡 | 0 🟠 | 60 🔴 | 60 🔴 | 75 🔴 | 30 🟠 | 75 🔴 | 40 🟠 |
| `ml-research` | 16 🟠 | 4 🟡 | 16 🟠 | 4 🟡 | 8 🟡 | 24 🟠 | 36 🟠 | 60 🔴 | 16 🟡 | 60 🔴 | 32 🟠 |

## Tool atomic operations

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `search_repositories` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `get_file_contents` | **READ** | 2 (Low) | READ | rules |
| `list_commits` | **LIST** | 1 (Low) | LIST | rules |
| `get_issue` | **READ** | 2 (Low) | READ | rules |
| `create_issue` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `create_or_update_file` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `push_files` | **WRITE** | 3 (Medium) | WRITE | rules |
| `delete_file` | **DELETE** | 5 (Critical) | DELETE | rules |
| `create_pull_request` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `merge_pull_request` | **WRITE** | 3 (Medium) | WRITE | rules |
| `fork_repository` | **CREATE** | 3 (Medium) | CREATE | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
