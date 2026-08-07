# Scan — github:real

_kind=github · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_desc · bands={'low': 29, 'medium': 120, 'high': 31, 'critical': 16, 'na': 324}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–25), scaled to this max.

## Inferred domain profile

- **mcp_kind**: source control system
- **asset_meaning**: GitHub repositories and mutable states within them (e.g., branches, issues, pull requests)
- **blast_radius_meaning**: The extent to which a tool can modify or access files, code changes, issues, comments, and other repository contents. A narrow touch might be updating a single file, while the most severe action could involve merging a pull request that affects production behavior.
- **dangerous_classes**: handles financial transactions, contains unpublished research or model weights, manages infrastructure secrets
- **irreversible_actions**: merge_pull_request, push_files, create_or_update_file
- **worked_example**: The tool 'merge_pull_request' on the asset 'infra-config' is highly severe because it can merge changes directly into production, potentially causing widespread operational impact.

## Tool impact

| tool | impact |
| --- | --- |
| `create_or_update_file` | 5 |
| `search_repositories` | 2 |
| `create_repository` | 4 |
| `get_file_contents` | 3 |
| `push_files` | 5 |
| `create_issue` | 4 |
| `create_pull_request` | 4 |
| `fork_repository` | 4 |
| `create_branch` | 4 |
| `list_commits` | 2 |
| `list_issues` | 2 |
| `update_issue` | 4 |
| `add_issue_comment` | 4 |
| `search_code` | 3 |
| `search_issues` | 2 |
| `search_users` | 2 |
| `get_issue` | 3 |
| `get_pull_request` | 3 |
| `list_pull_requests` | 2 |
| `create_pull_request_review` | 4 |
| `merge_pull_request` | 5 |
| `get_pull_request_files` | 2 |
| `get_pull_request_status` | 3 |
| `update_pull_request_branch` | 4 |
| `get_pull_request_comments` | 3 |
| `get_pull_request_reviews` | 3 |

## Asset sensitivity

_Not scored in `impact_mode=five_level_v2_desc`: the organization's written description of this server states how severe each asset is, so no separate 1–5 sensitivity primitive is derived. The 20 assets below still form the matrix axis; the score is `blast × impact`._

| asset | sensitivity |
| --- | --- |
| `public-website` | — |
| `internal-docs` | — |
| `backend-api` | — |
| `payments-service` | — |
| `infra-config` | — |
| `ml-research` | — |
| `branch-heads` | — |
| `issues-and-comments` | — |
| `pull-requests-and-reviews` | — |
| `org-external-copies` | — |
| `platform-user-directory` | — |
| `repository-catalog` | — |
| `repository-contents` | — |
| `issue-records` | — |
| `pull-request-records` | — |
| `branch-directory` | — |
| `commit-list` | — |
| `issue-catalog` | — |
| `code-records` | — |
| `repository-records` | — |

## Risk matrix (score · band)

_Each cell shows `score (blast×impact)` — sensitivity is not scored in this mode; impact_mode=five_level_v2_desc, score ranges 0–25. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | create_or_update_file | search_repositories | create_repository | get_file_contents | push_files | create_issue | create_pull_request | fork_repository | create_branch | list_commits | list_issues | update_issue | add_issue_comment | search_code | search_issues | search_users | get_issue | get_pull_request | list_pull_requests | create_pull_request_review | merge_pull_request | get_pull_request_files | get_pull_request_status | update_pull_request_branch | get_pull_request_comments | get_pull_request_reviews |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 5 (1×5) 🟢 | 4 (2×2) 🟢 | N/A | 3 (1×3) 🟢 | 20 (4×5) 🔴 | 4 (1×4) 🟢 | 8 (2×4) 🟡 | 16 (4×4) 🟠 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 4 (2×2) 🟢 | 8 (2×4) 🟡 | 4 (1×4) 🟢 | 6 (2×3) 🟢 | 4 (2×2) 🟢 | N/A | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 4 (2×2) 🟢 | 8 (2×4) 🟡 | 20 (4×5) 🔴 | 4 (2×2) 🟢 | 3 (1×3) 🟢 | 8 (2×4) 🟡 | 6 (2×3) 🟢 | 3 (1×3) 🟢 |
| `internal-docs` | 5 (1×5) 🟢 | 4 (2×2) 🟢 | N/A | 3 (1×3) 🟢 | 15 (3×5) 🟠 | 4 (1×4) 🟢 | 8 (2×4) 🟡 | 16 (4×4) 🟠 | 8 (2×4) 🟡 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 8 (2×4) 🟡 | 4 (1×4) 🟢 | 9 (3×3) 🟡 | 4 (2×2) 🟢 | N/A | N/A | N/A | 4 (2×2) 🟢 | 4 (1×4) 🟢 | 15 (3×5) 🟠 | 4 (2×2) 🟢 | N/A | 12 (3×4) 🟡 | N/A | N/A |
| `backend-api` | 5 (1×5) 🟢 | 4 (2×2) 🟢 | N/A | 12 (4×3) 🟡 | 25 (5×5) 🔴 | 4 (1×4) 🟢 | 8 (2×4) 🟡 | 16 (4×4) 🟠 | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 4 (2×2) 🟢 | 8 (2×4) 🟡 | 4 (1×4) 🟢 | 9 (3×3) 🟡 | 4 (2×2) 🟢 | N/A | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 4 (2×2) 🟢 | 4 (1×4) 🟢 | 15 (3×5) 🟠 | 4 (2×2) 🟢 | 3 (1×3) 🟢 | 12 (3×4) 🟡 | 6 (2×3) 🟢 | 3 (1×3) 🟢 |
| `payments-service` | 10 (2×5) 🟡 | 4 (2×2) 🟢 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 4 (1×4) 🟢 | 8 (2×4) 🟡 | 16 (4×4) 🟠 | 4 (1×4) 🟢 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 8 (2×4) 🟡 | 4 (1×4) 🟢 | 9 (3×3) 🟡 | 6 (3×2) 🟢 | N/A | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 4 (2×2) 🟢 | 4 (1×4) 🟢 | 25 (5×5) 🔴 | 4 (2×2) 🟢 | 3 (1×3) 🟢 | 12 (3×4) 🟡 | 6 (2×3) 🟢 | 3 (1×3) 🟢 |
| `infra-config` | 25 (5×5) 🔴 | 4 (2×2) 🟢 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | N/A | 4 (1×4) 🟢 | 20 (5×4) 🔴 | 4 (1×4) 🟢 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | N/A | N/A | 6 (2×3) 🟢 | N/A | N/A | N/A | 15 (5×3) 🟠 | 4 (2×2) 🟢 | N/A | 25 (5×5) 🔴 | 4 (2×2) 🟢 | N/A | 12 (3×4) 🟡 | N/A | 15 (5×3) 🟠 |
| `ml-research` | 10 (2×5) 🟡 | 4 (2×2) 🟢 | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 4 (1×4) 🟢 | 8 (2×4) 🟡 | 20 (5×4) 🔴 | 4 (1×4) 🟢 | 4 (2×2) 🟢 | 4 (2×2) 🟢 | 8 (2×4) 🟡 | 4 (1×4) 🟢 | 6 (2×3) 🟢 | 4 (2×2) 🟢 | N/A | 3 (1×3) 🟢 | 3 (1×3) 🟢 | 4 (2×2) 🟢 | 4 (1×4) 🟢 | 20 (4×5) 🔴 | 4 (2×2) 🟢 | 3 (1×3) 🟢 | 12 (3×4) 🟡 | 6 (2×3) 🟢 | 3 (1×3) 🟢 |
| `branch-heads` | 15 (3×5) 🟠 | N/A | N/A | N/A | 20 (4×5) 🔴 | N/A | 8 (2×4) 🟡 | N/A | 8 (2×4) 🟡 | 4 (2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 20 (4×5) 🔴 | N/A | N/A | 12 (3×4) 🟡 | N/A | N/A |
| `issues-and-comments` | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | 4 (1×4) 🟢 | 4 (1×4) 🟢 | N/A | 4 (2×2) 🟢 | N/A | 3 (1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 6 (2×3) 🟢 | N/A |
| `pull-requests-and-reviews` | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | N/A | N/A | 3 (1×3) 🟢 | 6 (3×2) 🟢 | 8 (2×4) 🟡 | 20 (4×5) 🔴 | 4 (2×2) 🟢 | 3 (1×3) 🟢 | 8 (2×4) 🟡 | 3 (1×3) 🟢 | 6 (2×3) 🟢 |
| `org-external-copies` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 20 (5×4) 🔴 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `platform-user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-catalog` | N/A | 4 (2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-contents` | 5 (1×5) 🟢 | N/A | N/A | 15 (5×3) 🟠 | 20 (4×5) 🔴 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 25 (5×5) 🔴 | 4 (2×2) 🟢 | N/A | 12 (3×4) 🟡 | N/A | N/A |
| `issue-records` | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | 4 (1×4) 🟢 | 4 (1×4) 🟢 | N/A | 6 (3×2) 🟢 | N/A | 3 (1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `pull-request-records` | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 (1×3) 🟢 | 4 (2×2) 🟢 | 4 (1×4) 🟢 | N/A | 4 (2×2) 🟢 | 3 (1×3) 🟢 | 4 (1×4) 🟢 | 6 (2×3) 🟢 | 3 (1×3) 🟢 |
| `branch-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×4) 🟡 | N/A | N/A |
| `commit-list` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `issue-catalog` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | 4 (1×4) 🟢 | N/A | N/A | 4 (2×2) 🟢 | N/A | 3 (1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `code-records` | N/A | 4 (2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | N/A | N/A | N/A | N/A |
| `repository-records` | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 (1×3) 🟢 | N/A | 4 (1×4) 🟢 | 25 (5×5) 🔴 | N/A | N/A | 4 (1×4) 🟢 | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | create_or_update_file | search_repositories | create_repository | get_file_contents | push_files | create_issue | create_pull_request | fork_repository | create_branch | list_commits | list_issues | update_issue | add_issue_comment | search_code | search_issues | search_users | get_issue | get_pull_request | list_pull_requests | create_pull_request_review | merge_pull_request | get_pull_request_files | get_pull_request_status | update_pull_request_branch | get_pull_request_comments | get_pull_request_reviews |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 1 | 2 | N/A | 1 | 4 | 1 | 2 | 4 | 1 | 1 | 2 | 2 | 1 | 2 | 2 | N/A | 1 | 1 | 2 | 2 | 4 | 2 | 1 | 2 | 2 | 1 |
| `internal-docs` | 1 | 2 | N/A | 1 | 3 | 1 | 2 | 4 | 2 | 2 | 2 | 2 | 1 | 3 | 2 | N/A | N/A | N/A | 2 | 1 | 3 | 2 | N/A | 3 | N/A | N/A |
| `backend-api` | 1 | 2 | N/A | 4 | 5 | 1 | 2 | 4 | 1 | 4 | 2 | 2 | 1 | 3 | 2 | N/A | 1 | 1 | 2 | 1 | 3 | 2 | 1 | 3 | 2 | 1 |
| `payments-service` | 2 | 2 | N/A | 5 | 5 | 1 | 2 | 4 | 1 | 2 | 2 | 2 | 1 | 3 | 3 | N/A | 1 | 1 | 2 | 1 | 5 | 2 | 1 | 3 | 2 | 1 |
| `infra-config` | 5 | 2 | N/A | 5 | 5 | N/A | 1 | 5 | 1 | 2 | 2 | N/A | N/A | 2 | N/A | N/A | N/A | 5 | 2 | N/A | 5 | 2 | N/A | 3 | N/A | 5 |
| `ml-research` | 2 | 2 | N/A | 5 | 5 | 1 | 2 | 5 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | N/A | 1 | 1 | 2 | 1 | 4 | 2 | 1 | 3 | 2 | 1 |
| `branch-heads` | 3 | N/A | N/A | N/A | 4 | N/A | 2 | N/A | 2 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | N/A | N/A | 3 | N/A | N/A |
| `issues-and-comments` | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | 2 | 1 | 1 | N/A | 2 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A |
| `pull-requests-and-reviews` | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | 1 | 3 | 2 | 4 | 2 | 1 | 2 | 1 | 2 |
| `org-external-copies` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `platform-user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-catalog` | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-contents` | 1 | N/A | N/A | 5 | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | 2 | N/A | 3 | N/A | N/A |
| `issue-records` | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | 2 | 1 | 1 | N/A | 3 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `pull-request-records` | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 2 | 1 | N/A | 2 | 1 | 1 | 2 | 1 |
| `branch-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A |
| `commit-list` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `issue-catalog` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 1 | N/A | N/A | 2 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `code-records` | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A |
| `repository-records` | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | 1 | 5 | N/A | N/A | 1 | N/A | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `create_or_update_file` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `search_repositories` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `create_repository` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `get_file_contents` | **READ** | 2 (Low) | READ | rules |
| `push_files` | **WRITE** | 3 (Medium) | WRITE | rules |
| `create_issue` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `create_pull_request` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `fork_repository` | **CREATE** | 3 (Medium) | CREATE | rules |
| `create_branch` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `list_commits` | **LIST** | 1 (Low) | LIST | rules |
| `list_issues` | **LIST** | 1 (Low) | LIST | rules |
| `update_issue` | **MODIFY** | 3 (Medium) | MODIFY | rules |
| `add_issue_comment` | **WRITE** | 3 (Medium) | WRITE | rules |
| `search_code` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `search_issues` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `search_users` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `get_issue` | **READ** | 2 (Low) | READ | rules |
| `get_pull_request` | **READ** | 2 (Low) | READ | rules |
| `list_pull_requests` | **LIST** | 1 (Low) | LIST | rules |
| `create_pull_request_review` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `merge_pull_request` | **WRITE** | 3 (Medium) | WRITE | rules |
| `get_pull_request_files` | **READ** | 2 (Low) | READ | rules |
| `get_pull_request_status` | **METADATA** | 1 (Low) | METADATA | rules |
| `update_pull_request_branch` | **MODIFY** | 3 (Medium) | MODIFY | rules |
| `get_pull_request_comments` | **READ** | 2 (Low) | READ | rules |
| `get_pull_request_reviews` | **READ** | 2 (Low) | READ | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `create_or_update_file` | `content` | 5 | — | fully controlled payload that can contain malicious code or  |
| `create_or_update_file` | `path` | 4 | — | can be used to specify sensitive file paths for modification |
| `create_or_update_file` | `sha` | 3 | — | can be used to specify a specific file version, potentially  |
| `create_or_update_file` | `owner` | 2 | — | merely names the target repository owner |
| `create_or_update_file` | `repo` | 2 | — | merely names the target repository |
| `create_or_update_file` | `branch` | 2 | — | names the target branch for modification |
| `create_or_update_file` | `message` | 1 | — | commit message, low risk as it's just text |
| `search_repositories` | `query` | 5 | — | Fully controllable input can be used for malicious searches |
| `search_repositories` | `perPage` | 3 | >= 100 | Can increase the volume of data retrieved per call |
| `search_repositories` | `page` | 2 | — | Controls pagination but not inherently risky |
| `create_repository` | `private` | 3 | — | can widen access scope if set to false |
| `create_repository` | `name` | 2 | — | merely names the target |
| `create_repository` | `autoInit` | 2 | — | initializes with a file, but limited impact |
| `create_repository` | `description` | 1 | — | descriptive text, no action |
| `get_file_contents` | `path` | 4 | — | can be used to access sensitive files or directories |
| `get_file_contents` | `owner` | 2 | — | merely names the target repository owner |
| `get_file_contents` | `repo` | 2 | — | merely names the target repository |
| `get_file_contents` | `branch` | 1 | — | limits the scope to a specific branch, reducing risk |
| `push_files` | `files` | 4 | >= 10 files | can be used to upload a large number of potentially maliciou |
| `push_files` | `message` | 3 | — | potentially contains arbitrary text that could mislead or ob |
| `push_files` | `owner` | 2 | — | merely names the target repository owner |
| `push_files` | `repo` | 2 | — | merely names the target repository |
| `push_files` | `branch` | 2 | — | merely specifies the branch to push to |
| `create_issue` | `body` | 5 | — | fully controllable content, can contain malicious scripts or |
| `create_issue` | `assignees` | 4 | >= 20 recipients | can be used to spam multiple users with issues |
| `create_issue` | `title` | 3 | — | can be used to mislead or confuse with arbitrary text |
| `create_issue` | `labels` | 3 | >= 20 labels | can be used to overwhelm with tags or mislead categorization |
| `create_issue` | `owner` | 2 | — | merely names the target repository owner |
| `create_issue` | `repo` | 2 | — | merely names the target repository |
| `create_issue` | `milestone` | 1 | — | affects issue tracking, not directly harmful |
| `create_pull_request` | `body` | 4 | — | fully controlled content that can contain malicious instruct |
| `create_pull_request` | `title` | 3 | — | can be used to mislead or confuse maintainers |
| `create_pull_request` | `head` | 3 | — | can point to a branch with unknown changes, potentially harm |
| `create_pull_request` | `owner` | 2 | — | merely names the target repository owner |
| `create_pull_request` | `repo` | 2 | — | merely names the target repository |
| `create_pull_request` | `base` | 2 | — | names the target branch for merging, but does not control co |
| `create_pull_request` | `maintainer_can_modify` | 2 | — | allows maintainers to modify the PR but does not inherently  |
| `create_pull_request` | `draft` | 1 | — | affects visibility and workflow, not security directly |
| `fork_repository` | `organization` | 3 | — | can widen scope to an organization, potentially amplifying a |
| `fork_repository` | `owner` | 2 | — | merely names the target repository owner |
| `fork_repository` | `repo` | 2 | — | merely names the target repository |
| `create_branch` | `from_branch` | 4 | — | allows specifying an arbitrary source branch, which could le |
| `create_branch` | `branch` | 3 | — | can be used to create arbitrary branch names, potentially fo |
| `create_branch` | `owner` | 2 | — | merely names the target repository owner |
| `create_branch` | `repo` | 2 | — | merely names the target repository |
| `list_commits` | `perPage` | 5 | >= 100 | large values can cause significant data retrieval, leading t |
| `list_commits` | `page` | 4 | >= 1000 | high page numbers can lead to excessive API calls and resour |
| `list_commits` | `sha` | 3 | — | can potentially specify a wide range of commits, affecting d |
| `list_commits` | `owner` | 2 | — | merely names the target repository owner |
| `list_commits` | `repo` | 2 | — | merely names the target repository |
| `list_issues` | `per_page` | 4 | >= 100 issues per page | can increase data volume returned |
| `list_issues` | `labels` | 3 | >= 20 labels | can broaden scope with many filters |
| `list_issues` | `owner` | 2 | — | names the target repository owner |
| `list_issues` | `repo` | 2 | — | names the target repository |
| `list_issues` | `since` | 2 | — | limits time scope of results |
| `list_issues` | `direction` | 1 | — | limits to ascending or descending order |
| `list_issues` | `page` | 1 | — | pagination control, limited impact |
| `list_issues` | `sort` | 1 | — | defines sorting criteria, limited impact |
| `list_issues` | `state` | 1 | — | filters by issue state (open/closed), limited impact |
| `update_issue` | `body` | 5 | — | can contain large amounts of arbitrary content or malicious  |
| `update_issue` | `assignees` | 4 | >= 20 recipients | can bulk assign to many users |
| `update_issue` | `title` | 3 | — | can contain arbitrary text |
| `update_issue` | `labels` | 3 | >= 50 labels | can add numerous labels to an issue |
| `update_issue` | `owner` | 2 | — | names the target repository owner |
| `update_issue` | `repo` | 2 | — | names the target repository |
| `update_issue` | `state` | 2 | — | changes the state of the issue |
| `update_issue` | `issue_number` | 1 | — | identifies a specific issue |
| `update_issue` | `milestone` | 1 | — | references a specific milestone |
| `add_issue_comment` | `body` | 5 | — | fully controlled payload with potential for abuse (e.g., XSS |
| `add_issue_comment` | `owner` | 2 | — | merely names the target repository owner |
| `add_issue_comment` | `repo` | 2 | — | merely names the target repository |
| `add_issue_comment` | `issue_number` | 1 | — | identifies a specific issue, no amplification potential |
| `search_code` | `q` | 5 | — | Free-form query can be abused for wide-ranging searches or m |
| `search_code` | `per_page` | 4 | >= 100 | Controls the number of results per page, high values can ove |
| `search_code` | `page` | 3 | >= 100 | Can be used for excessive pagination requests |
| `search_code` | `order` | 2 | — | Limited to predefined values, minimal risk |
| `search_issues` | `q` | 5 | — | Free-form query can be abused for wide-ranging searches or m |
| `search_issues` | `per_page` | 4 | >= 100 | Controls the number of results per page, high values can ove |
| `search_issues` | `page` | 3 | >= 100 | Can be used for excessive pagination requests |
| `search_issues` | `order` | 2 | — | Limited to predefined values, minimal risk |
| `search_issues` | `sort` | 2 | — | Limited to predefined sorting options, minimal risk |
| `search_users` | `q` | 5 | — | Free-form query can be abused for complex, wide-ranging sear |
| `search_users` | `per_page` | 4 | >= 100 | Controls the number of results per page, high risk if set to |
| `search_users` | `page` | 3 | >= 100 | Can be used for excessive pagination requests |
| `search_users` | `order` | 2 | — | Limited to predefined values, low risk of abuse |
| `search_users` | `sort` | 2 | — | Limited to predefined values, low risk of abuse |
| `get_issue` | `issue_number` | 3 | — | can be used to fan out requests across many issues, but is a |
| `get_issue` | `owner` | 2 | — | merely names the target repository owner |
| `get_issue` | `repo` | 2 | — | merely names the target repository |
| `get_pull_request` | `pull_number` | 3 | — | can be used to fan out across multiple pull requests if auto |
| `get_pull_request` | `owner` | 2 | — | merely names the target |
| `get_pull_request` | `repo` | 2 | — | merely names the target |
| `list_pull_requests` | `per_page` | 4 | >= 100 | controls result breadth (bulk fan-out) |
| `list_pull_requests` | `head` | 3 | — | can be a free-form query/command |
| `list_pull_requests` | `page` | 3 | — | can be used to exhaustively retrieve data |
| `list_pull_requests` | `owner` | 2 | — | merely names the target |
| `list_pull_requests` | `repo` | 2 | — | merely names the target |
| `list_pull_requests` | `base` | 2 | — | can influence scope but limited |
| `list_pull_requests` | `state` | 1 | — | fixed enum/structural field |
| `list_pull_requests` | `sort` | 1 | — | fixed enum/structural field |
| `list_pull_requests` | `direction` | 1 | — | fixed enum/structural field |
| `create_pull_request_review` | `body` | 4 | — | fully controlled text that could contain malicious content o |
| `create_pull_request_review` | `comments` | 4 | >= 20 comments | array that can be used to fan out malicious content or instr |
| `create_pull_request_review` | `event` | 3 | — | defines the action of the review, potentially destructive if |
| `create_pull_request_review` | `owner` | 2 | — | merely names the target |
| `create_pull_request_review` | `repo` | 2 | — | merely names the target |
| `create_pull_request_review` | `commit_id` | 2 | — | specifies commit for review, limited scope |
| `create_pull_request_review` | `pull_number` | 1 | — | identifies specific pull request, not inherently risky |
| `merge_pull_request` | `commit_message` | 5 | — | fully controlled string input with potential for arbitrary c |
| `merge_pull_request` | `commit_title` | 4 | — | fully controlled string input that could contain malicious c |
| `merge_pull_request` | `pull_number` | 3 | — | identifies specific pull request, but not inherently risky |
| `merge_pull_request` | `merge_method` | 3 | — | could influence the merge process, but limited to predefined |
| `merge_pull_request` | `owner` | 2 | — | merely names the target repository owner |
| `merge_pull_request` | `repo` | 2 | — | merely names the target repository |
| `get_pull_request_files` | `pull_number` | 3 | — | can be used to target specific or numerous pull requests |
| `get_pull_request_files` | `owner` | 2 | — | merely names the target |
| `get_pull_request_files` | `repo` | 2 | — | merely names the target |
| `get_pull_request_status` | `pull_number` | 3 | — | can be used to fan out across multiple pull requests if auto |
| `get_pull_request_status` | `owner` | 2 | — | merely names the target |
| `get_pull_request_status` | `repo` | 2 | — | merely names the target |
| `update_pull_request_branch` | `expected_head_sha` | 4 | — | can be used to manipulate the update process by specifying a |
| `update_pull_request_branch` | `pull_number` | 3 | — | identifies a specific pull request, but does not control con |
| `update_pull_request_branch` | `owner` | 2 | — | merely names the target repository owner |
| `update_pull_request_branch` | `repo` | 2 | — | merely names the target repository |
| `get_pull_request_comments` | `pull_number` | 3 | — | can be used to target specific or non-existent pull requests |
| `get_pull_request_comments` | `owner` | 2 | — | merely names the target |
| `get_pull_request_comments` | `repo` | 2 | — | merely names the target |
| `get_pull_request_reviews` | `pull_number` | 3 | — | can be used to fan out across multiple pull requests if auto |
| `get_pull_request_reviews` | `owner` | 2 | — | merely names the target |
| `get_pull_request_reviews` | `repo` | 2 | — | merely names the target |
