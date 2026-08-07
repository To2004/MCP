# Scan — github:real

_kind=github · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v4_static · bands={'low': 64, 'medium': 70, 'high': 31, 'critical': 11, 'na': 344}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = org profile table (never LLM-scored)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- gated blast floor (impact >= 4): sens 5 -> blast >= 4, sens 4 -> blast >= 3
- impact-keyed floor (one tier lower): impact 5 -> blast >= 3, impact 4 -> blast >= 2
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof (impact <= 3 only, never a mutation): non-escaping read caps at 4, sens-1 caps at 4 — assets flagged hub/population/self-sufficient are exempt
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: code repository
- **asset_meaning**: GitHub repositories and their contents (files, issues, pull requests)
- **blast_radius_meaning**: The extent of the impact a tool can have on assets, from modifying a single file to affecting entire codebases or production systems through merges and deployments.
- **dangerous_classes**: holds unpublished research, models and datasets, affects live payment processing, reconfigures production systems
- **irreversible_actions**: merge_pull_request, push_files, create_or_update_file
- **worked_example**: The tool 'merge_pull_request' on the asset 'backend-api' can lead to immediate changes in production behavior, making it highly impactful.

## Tool impact

| tool | impact |
| --- | --- |
| `create_or_update_file` | 5 |
| `search_repositories` | 2 |
| `create_repository` | 4 |
| `get_file_contents` | 3 |
| `push_files` | 4 |
| `create_issue` | 4 |
| `create_pull_request` | 4 |
| `fork_repository` | 4 |
| `create_branch` | 4 |
| `list_commits` | 2 |
| `list_issues` | 2 |
| `update_issue` | 4 |
| `add_issue_comment` | 4 |
| `search_code` | 3 |
| `search_issues` | 3 |
| `search_users` | 3 |
| `get_issue` | 3 |
| `get_pull_request` | 3 |
| `list_pull_requests` | 2 |
| `create_pull_request_review` | 4 |
| `merge_pull_request` | 5 |
| `get_pull_request_files` | 3 |
| `get_pull_request_status` | 2 |
| `update_pull_request_branch` | 4 |
| `get_pull_request_comments` | 3 |
| `get_pull_request_reviews` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `public-website` | 1 |
| `internal-docs` | 3 |
| `backend-api` | 4 |
| `payments-service` | 4 |
| `infra-config` | 5 |
| `ml-research` | 4 |
| `branch-heads` | 4 |
| `issues-and-comments` | 3 |
| `pull-requests-and-reviews` | 4 |
| `org-external-copies` | 4 |
| `platform-user-directory` | 1 |
| `repository-catalog` | 2 |
| `repository-contents` | 4 |
| `issue-records` | 3 |
| `pull-request-records` | 4 |
| `branch-directory` | 2 |
| `commit-list` | 2 |
| `issue-catalog` | 2 |
| `code-records` | 4 |
| `repository-records` | 3 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v4_static, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | create_or_update_file | search_repositories | create_repository | get_file_contents | push_files | create_issue | create_pull_request | fork_repository | create_branch | list_commits | list_issues | update_issue | add_issue_comment | search_code | search_issues | search_users | get_issue | get_pull_request | list_pull_requests | create_pull_request_review | merge_pull_request | get_pull_request_files | get_pull_request_status | update_pull_request_branch | get_pull_request_comments | get_pull_request_reviews |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 15 (1×3×5) 🟢 | N/A | N/A | 3 (1×1×3) 🟢 | 16 (1×4×4) 🟢 | 8 (1×2×4) 🟢 | 8 (1×2×4) 🟢 | 20 (1×5×4) 🟢 | 8 (1×2×4) 🟢 | 4 (1×2×2) 🟢 | N/A | N/A | N/A | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | 20 (1×4×5) 🟢 | 3 (1×1×3) 🟢 | N/A | 16 (1×4×4) 🟢 | N/A | N/A |
| `internal-docs` | 45 (3×3×5) 🟡 | N/A | N/A | 9 (3×1×3) 🟢 | 36 (3×3×4) 🟡 | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 60 (3×5×4) 🟡 | 24 (3×2×4) 🟢 | 12 (3×2×2) 🟢 | N/A | 24 (3×2×4) 🟢 | N/A | 18 (3×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | 60 (3×4×5) 🟡 | 18 (3×2×3) 🟢 | N/A | 36 (3×3×4) 🟡 | N/A | N/A |
| `backend-api` | 60 (4×3×5) 🟡 | N/A | N/A | 12 (4×1×3) 🟢 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 48 (4×3×4) 🟡 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 48 (4×3×4) 🟡 | 48 (4×3×4) 🟡 | 24 (4×2×3) 🟢 | 24 (4×2×3) 🟢 | N/A | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 16 (4×2×2) 🟢 | 48 (4×3×4) 🟡 | 100 (4×5×5) 🔴 | 36 (4×3×3) 🟡 | 8 (4×1×2) 🟢 | 80 (4×5×4) 🟠 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 |
| `payments-service` | 100 (4×5×5) 🔴 | N/A | N/A | 12 (4×1×3) 🟢 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 48 (4×3×4) 🟡 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 48 (4×3×4) 🟡 | 48 (4×3×4) 🟡 | 36 (4×3×3) 🟡 | 24 (4×2×3) 🟢 | N/A | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 16 (4×2×2) 🟢 | 48 (4×3×4) 🟡 | 100 (4×5×5) 🔴 | 24 (4×2×3) 🟢 | 16 (4×2×2) 🟢 | 80 (4×5×4) 🟠 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 |
| `infra-config` | 125 (5×5×5) 🔴 | N/A | N/A | 15 (5×1×3) 🟢 | 100 (5×5×4) 🔴 | 80 (5×4×4) 🟠 | 80 (5×4×4) 🟠 | 100 (5×5×4) 🔴 | 80 (5×4×4) 🟠 | 20 (5×2×2) 🟢 | 20 (5×2×2) 🟢 | N/A | N/A | 30 (5×2×3) 🟢 | N/A | N/A | N/A | N/A | 20 (5×2×2) 🟢 | 80 (5×4×4) 🟠 | 125 (5×5×5) 🔴 | 30 (5×2×3) 🟢 | N/A | 100 (5×5×4) 🔴 | N/A | N/A |
| `ml-research` | 60 (4×3×5) 🟡 | 16 (4×2×2) 🟢 | N/A | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 48 (4×3×4) 🟡 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 16 (4×2×2) 🟢 | 16 (4×2×2) 🟢 | 48 (4×3×4) 🟡 | 48 (4×3×4) 🟡 | 24 (4×2×3) 🟢 | N/A | N/A | 12 (4×1×3) 🟢 | N/A | 16 (4×2×2) 🟢 | N/A | 80 (4×4×5) 🟠 | 24 (4×2×3) 🟢 | N/A | 48 (4×3×4) 🟡 | N/A | N/A |
| `branch-heads` | 100 (4×5×5) 🔴 | N/A | N/A | N/A | 80 (4×5×4) 🟠 | N/A | 48 (4×3×4) 🟡 | N/A | 48 (4×3×4) 🟡 | 16 (4×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 100 (4×5×5) 🔴 | N/A | N/A | 80 (4×5×4) 🟠 | N/A | N/A |
| `issues-and-comments` | N/A | N/A | N/A | N/A | N/A | 24 (3×2×4) 🟢 | N/A | N/A | N/A | N/A | 12 (3×2×2) 🟢 | 24 (3×2×4) 🟢 | 24 (3×2×4) 🟢 | N/A | 27 (3×3×3) 🟢 | N/A | 9 (3×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 9 (3×1×3) 🟢 | N/A |
| `pull-requests-and-reviews` | N/A | N/A | N/A | N/A | N/A | N/A | 48 (4×3×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | 36 (4×3×3) 🟡 | 24 (4×2×3) 🟢 | N/A | N/A | 12 (4×1×3) 🟢 | 16 (4×2×2) 🟢 | 64 (4×4×4) 🟡 | 80 (4×4×5) 🟠 | 24 (4×2×3) 🟢 | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 |
| `org-external-copies` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 80 (4×5×4) 🟠 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `platform-user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 (1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-catalog` | N/A | 8 (2×2×2) 🟢 | 16 (2×2×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-contents` | 60 (4×3×5) 🟡 | N/A | N/A | 12 (4×1×3) 🟢 | 64 (4×4×4) 🟡 | N/A | 48 (4×3×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | 24 (4×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | 80 (4×4×5) 🟠 | 24 (4×2×3) 🟢 | N/A | 48 (4×3×4) 🟡 | N/A | N/A |
| `issue-records` | N/A | N/A | N/A | N/A | N/A | 24 (3×2×4) 🟢 | N/A | N/A | N/A | N/A | 12 (3×2×2) 🟢 | 24 (3×2×4) 🟢 | 24 (3×2×4) 🟢 | N/A | 18 (3×2×3) 🟢 | N/A | 9 (3×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `pull-request-records` | N/A | N/A | N/A | N/A | N/A | N/A | 48 (4×3×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 24 (4×2×3) 🟢 | N/A | N/A | 12 (4×1×3) 🟢 | 16 (4×2×2) 🟢 | 48 (4×3×4) 🟡 | 100 (4×5×5) 🔴 | 12 (4×1×3) 🟢 | 8 (4×1×2) 🟢 | 64 (4×4×4) 🟡 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 |
| `branch-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (2×2×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `commit-list` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (2×1×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `issue-catalog` | N/A | N/A | N/A | N/A | N/A | 16 (2×2×4) 🟢 | N/A | N/A | N/A | N/A | 8 (2×2×2) 🟢 | N/A | N/A | N/A | 12 (2×2×3) 🟢 | N/A | 6 (2×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `code-records` | N/A | 40 (4×5×2) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 60 (4×5×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 36 (4×3×3) 🟡 | N/A | N/A | N/A | N/A |
| `repository-records` | 75 (3×5×5) 🟠 | N/A | N/A | N/A | 60 (3×5×4) 🟡 | 24 (3×2×4) 🟢 | 36 (3×3×4) 🟡 | 60 (3×5×4) 🟡 | 24 (3×2×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 12 (3×2×2) 🟢 | N/A | 75 (3×5×5) 🟠 | N/A | N/A | N/A | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | create_or_update_file | search_repositories | create_repository | get_file_contents | push_files | create_issue | create_pull_request | fork_repository | create_branch | list_commits | list_issues | update_issue | add_issue_comment | search_code | search_issues | search_users | get_issue | get_pull_request | list_pull_requests | create_pull_request_review | merge_pull_request | get_pull_request_files | get_pull_request_status | update_pull_request_branch | get_pull_request_comments | get_pull_request_reviews |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 3 | N/A | N/A | 1 | 4 | 2 | 2 | 5 | 2 | 2 | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 1 | N/A | 4 | N/A | N/A |
| `internal-docs` | 3 | N/A | N/A | 1 | 3 | 2 | 3 | 5 | 2 | 2 | N/A | 2 | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 2 | N/A | 3 | N/A | N/A |
| `backend-api` | 3 | N/A | N/A | 1 | 5 | 3 | 3 | 5 | 3 | 2 | 2 | 3 | 3 | 2 | 2 | N/A | 1 | 1 | 2 | 3 | 5 | 3 | 1 | 5 | 1 | 1 |
| `payments-service` | 5 | N/A | N/A | 1 | 5 | 3 | 3 | 5 | 3 | 2 | 2 | 3 | 3 | 3 | 2 | N/A | 1 | 1 | 2 | 3 | 5 | 2 | 2 | 5 | 1 | 1 |
| `infra-config` | 5 | N/A | N/A | 1 | 5 | 4 | 4 | 5 | 4 | 2 | 2 | N/A | N/A | 2 | N/A | N/A | N/A | N/A | 2 | 4 | 5 | 2 | N/A | 5 | N/A | N/A |
| `ml-research` | 3 | 2 | N/A | 4 | 4 | 3 | 3 | 5 | 3 | 2 | 2 | 3 | 3 | 2 | N/A | N/A | 1 | N/A | 2 | N/A | 4 | 2 | N/A | 3 | N/A | N/A |
| `branch-heads` | 5 | N/A | N/A | N/A | 5 | N/A | 3 | N/A | 3 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | N/A | N/A | 5 | N/A | N/A |
| `issues-and-comments` | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | 2 | 2 | 2 | N/A | 3 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A |
| `pull-requests-and-reviews` | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 2 | N/A | N/A | 1 | 2 | 4 | 4 | 2 | 1 | 3 | 1 | 1 |
| `org-external-copies` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `platform-user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-catalog` | N/A | 2 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-contents` | 3 | N/A | N/A | 1 | 4 | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 2 | N/A | 3 | N/A | N/A |
| `issue-records` | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | 2 | 2 | 2 | N/A | 2 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `pull-request-records` | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | 1 | 2 | 3 | 5 | 1 | 1 | 4 | 1 | 1 |
| `branch-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `commit-list` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `issue-catalog` | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | 2 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `code-records` | N/A | 5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A |
| `repository-records` | 5 | N/A | N/A | N/A | 5 | 2 | 3 | 5 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | 5 | N/A | N/A | N/A | N/A | N/A |

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
| `create_or_update_file` | `content` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `create_or_update_file` | `message` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `create_or_update_file` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `create_or_update_file` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `create_or_update_file` | `path` | 2 | — | names the target resource — selects what the op touches |
| `create_or_update_file` | `branch` | 2 | — | names the target resource — selects what the op touches |
| `create_or_update_file` | `sha` | 1 | — | minor / structural parameter |
| `search_repositories` | `query` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `search_repositories` | `page` | 1 | — | minor / structural parameter |
| `search_repositories` | `perPage` | 1 | — | minor / structural parameter |
| `create_repository` | `description` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `create_repository` | `name` | 2 | — | names the target resource — selects what the op touches |
| `create_repository` | `private` | 1 | — | minor / structural parameter |
| `create_repository` | `autoInit` | 1 | — | minor / structural parameter |
| `get_file_contents` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `get_file_contents` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `get_file_contents` | `path` | 2 | — | names the target resource — selects what the op touches |
| `get_file_contents` | `branch` | 2 | — | names the target resource — selects what the op touches |
| `push_files` | `files` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `push_files` | `message` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `push_files` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `push_files` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `push_files` | `branch` | 2 | — | names the target resource — selects what the op touches |
| `create_issue` | `body` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `create_issue` | `assignees` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `create_issue` | `labels` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `create_issue` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `create_issue` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `create_issue` | `title` | 1 | — | minor / structural parameter |
| `create_issue` | `milestone` | 1 | — | minor / structural parameter |
| `create_pull_request` | `body` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `create_pull_request` | `maintainer_can_modify` | 3 | large value | magnitude/count — larger value means broader effect |
| `create_pull_request` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `create_pull_request` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `create_pull_request` | `title` | 1 | — | minor / structural parameter |
| `create_pull_request` | `head` | 1 | — | minor / structural parameter |
| `create_pull_request` | `base` | 1 | — | minor / structural parameter |
| `create_pull_request` | `draft` | 1 | — | minor / structural parameter |
| `fork_repository` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `fork_repository` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `fork_repository` | `organization` | 1 | — | minor / structural parameter |
| `create_branch` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `create_branch` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `create_branch` | `branch` | 2 | — | names the target resource — selects what the op touches |
| `create_branch` | `from_branch` | 2 | — | names the target resource — selects what the op touches |
| `list_commits` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `list_commits` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `list_commits` | `sha` | 1 | — | minor / structural parameter |
| `list_commits` | `page` | 1 | — | minor / structural parameter |
| `list_commits` | `perPage` | 1 | — | minor / structural parameter |
| `list_issues` | `labels` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `list_issues` | `per_page` | 3 | large value | magnitude/count — larger value means broader effect |
| `list_issues` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `list_issues` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `list_issues` | `direction` | 1 | — | minor / structural parameter |
| `list_issues` | `page` | 1 | — | minor / structural parameter |
| `list_issues` | `since` | 1 | — | minor / structural parameter |
| `list_issues` | `sort` | 1 | — | minor / structural parameter |
| `list_issues` | `state` | 1 | — | minor / structural parameter |
| `update_issue` | `body` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `update_issue` | `assignees` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `update_issue` | `labels` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `update_issue` | `issue_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `update_issue` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `update_issue` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `update_issue` | `title` | 1 | — | minor / structural parameter |
| `update_issue` | `milestone` | 1 | — | minor / structural parameter |
| `update_issue` | `state` | 1 | — | minor / structural parameter |
| `add_issue_comment` | `body` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `add_issue_comment` | `issue_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `add_issue_comment` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `add_issue_comment` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `search_code` | `per_page` | 3 | large value | magnitude/count — larger value means broader effect |
| `search_code` | `q` | 1 | — | minor / structural parameter |
| `search_code` | `order` | 1 | — | minor / structural parameter |
| `search_code` | `page` | 1 | — | minor / structural parameter |
| `search_issues` | `per_page` | 3 | large value | magnitude/count — larger value means broader effect |
| `search_issues` | `q` | 1 | — | minor / structural parameter |
| `search_issues` | `order` | 1 | — | minor / structural parameter |
| `search_issues` | `page` | 1 | — | minor / structural parameter |
| `search_issues` | `sort` | 1 | — | minor / structural parameter |
| `search_users` | `per_page` | 3 | large value | magnitude/count — larger value means broader effect |
| `search_users` | `q` | 1 | — | minor / structural parameter |
| `search_users` | `order` | 1 | — | minor / structural parameter |
| `search_users` | `page` | 1 | — | minor / structural parameter |
| `search_users` | `sort` | 1 | — | minor / structural parameter |
| `get_issue` | `issue_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `get_issue` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `get_issue` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `get_pull_request` | `pull_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `get_pull_request` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `get_pull_request` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `list_pull_requests` | `per_page` | 3 | large value | magnitude/count — larger value means broader effect |
| `list_pull_requests` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `list_pull_requests` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `list_pull_requests` | `state` | 1 | — | minor / structural parameter |
| `list_pull_requests` | `head` | 1 | — | minor / structural parameter |
| `list_pull_requests` | `base` | 1 | — | minor / structural parameter |
| `list_pull_requests` | `sort` | 1 | — | minor / structural parameter |
| `list_pull_requests` | `direction` | 1 | — | minor / structural parameter |
| `list_pull_requests` | `page` | 1 | — | minor / structural parameter |
| `create_pull_request_review` | `body` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `create_pull_request_review` | `comments` | 4 | large list (bulk fan-out) | list/array — risk scales with its length (bulk reach, mass f |
| `create_pull_request_review` | `pull_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `create_pull_request_review` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `create_pull_request_review` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `create_pull_request_review` | `event` | 2 | — | names the target resource — selects what the op touches |
| `create_pull_request_review` | `commit_id` | 2 | — | names the target resource — selects what the op touches |
| `merge_pull_request` | `commit_message` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `merge_pull_request` | `pull_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `merge_pull_request` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `merge_pull_request` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `merge_pull_request` | `commit_title` | 1 | — | minor / structural parameter |
| `merge_pull_request` | `merge_method` | 1 | — | minor / structural parameter |
| `get_pull_request_files` | `pull_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `get_pull_request_files` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `get_pull_request_files` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `get_pull_request_status` | `pull_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `get_pull_request_status` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `get_pull_request_status` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `update_pull_request_branch` | `pull_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `update_pull_request_branch` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `update_pull_request_branch` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `update_pull_request_branch` | `expected_head_sha` | 1 | — | minor / structural parameter |
| `get_pull_request_comments` | `pull_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `get_pull_request_comments` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `get_pull_request_comments` | `repo` | 2 | — | names the target resource — selects what the op touches |
| `get_pull_request_reviews` | `pull_number` | 3 | large value | magnitude/count — larger value means broader effect |
| `get_pull_request_reviews` | `owner` | 2 | — | names the target resource — selects what the op touches |
| `get_pull_request_reviews` | `repo` | 2 | — | names the target resource — selects what the op touches |
