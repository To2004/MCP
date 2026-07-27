# Scan — github:real

_kind=github · provenance=llm-scan · model_reviewed=True · impact_mode=cia · bands={'low': 30, 'medium': 50, 'high': 71, 'critical': 5}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–150), scaled to this max.

## Inferred domain profile

- **mcp_kind**: GitHub repository management
- **asset_meaning**: GitHub repositories containing source code, documentation, or configuration files
- **blast_radius_meaning**: The extent of changes a tool can make within the repository, from modifying a single file to affecting multiple files and branches
- **dangerous_classes**: holds secrets, handles card flows, core backend service
- **irreversible_actions**: push_files with force option, delete branch, merge pull request without review
- **worked_example**: The tool 'create_or_update_file' on the asset 'infra-config' could lead to severe consequences if it modifies secrets, as this can compromise security.

## Tool impact

| tool | impact |
| --- | --- |
| `create_or_update_file` | 3 |
| `search_repositories` | 2 |
| `create_repository` | 2 |
| `get_file_contents` | 2 |
| `push_files` | 4 |
| `create_issue` | 2 |
| `create_pull_request` | 2 |
| `fork_repository` | 3 |
| `create_branch` | 2 |
| `list_commits` | 2 |
| `list_issues` | 2 |
| `update_issue` | 3 |
| `add_issue_comment` | 3 |
| `search_code` | 2 |
| `search_issues` | 2 |
| `search_users` | 2 |
| `get_issue` | 2 |
| `get_pull_request` | 2 |
| `list_pull_requests` | 1 |
| `create_pull_request_review` | 2 |
| `merge_pull_request` | 4 |
| `get_pull_request_files` | 2 |
| `get_pull_request_status` | 2 |
| `update_pull_request_branch` | 3 |
| `get_pull_request_comments` | 2 |
| `get_pull_request_reviews` | 2 |

## Tool impact — CIA breakdown

_impact = base(1-3) + one point per violated CIA facet. ✓ = the tool violates that objective (C disclose · I modify · A make-unavailable)._

| tool | base | C | I | A | impact |
| --- | --- | --- | --- | --- | --- |
| `create_or_update_file` | 2 | · | ✓ | · | 3 |
| `search_repositories` | 1 | ✓ | · | · | 2 |
| `create_repository` | 2 | · | · | · | 2 |
| `get_file_contents` | 1 | ✓ | · | · | 2 |
| `push_files` | 3 | · | ✓ | · | 4 |
| `create_issue` | 2 | · | · | · | 2 |
| `create_pull_request` | 2 | · | · | · | 2 |
| `fork_repository` | 2 | ✓ | · | · | 3 |
| `create_branch` | 2 | · | · | · | 2 |
| `list_commits` | 1 | ✓ | · | · | 2 |
| `list_issues` | 1 | ✓ | · | · | 2 |
| `update_issue` | 2 | · | ✓ | · | 3 |
| `add_issue_comment` | 2 | · | ✓ | · | 3 |
| `search_code` | 1 | ✓ | · | · | 2 |
| `search_issues` | 1 | ✓ | · | · | 2 |
| `search_users` | 1 | ✓ | · | · | 2 |
| `get_issue` | 1 | ✓ | · | · | 2 |
| `get_pull_request` | 1 | ✓ | · | · | 2 |
| `list_pull_requests` | 1 | · | · | · | 1 |
| `create_pull_request_review` | 2 | · | · | · | 2 |
| `merge_pull_request` | 3 | · | ✓ | · | 4 |
| `get_pull_request_files` | 1 | ✓ | · | · | 2 |
| `get_pull_request_status` | 1 | ✓ | · | · | 2 |
| `update_pull_request_branch` | 2 | · | ✓ | · | 3 |
| `get_pull_request_comments` | 1 | ✓ | · | · | 2 |
| `get_pull_request_reviews` | 1 | ✓ | · | · | 2 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `public-website` | 1 |
| `internal-docs` | 3 |
| `backend-api` | 4 |
| `payments-service` | 5 |
| `infra-config` | 5 |
| `ml-research` | 4 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=cia, score ranges 0–150. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | create_or_update_file | search_repositories | create_repository | get_file_contents | push_files | create_issue | create_pull_request | fork_repository | create_branch | list_commits | list_issues | update_issue | add_issue_comment | search_code | search_issues | search_users | get_issue | get_pull_request | list_pull_requests | create_pull_request_review | merge_pull_request | get_pull_request_files | get_pull_request_status | update_pull_request_branch | get_pull_request_comments | get_pull_request_reviews |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 6 (1×2×3) 🟢 | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 4 (1×2×2) 🟢 | 12 (1×3×4) 🟢 | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 12 (1×4×3) 🟢 | 2 (1×1×2) 🟢 | 4 (1×2×2) 🟢 | 4 (1×2×2) 🟢 | 6 (1×2×3) 🟢 | 3 (1×1×3) 🟢 | 8 (1×4×2) 🟢 | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 3 (1×3×1) 🟢 | 4 (1×2×2) 🟢 | 12 (1×3×4) 🟢 | 4 (1×2×2) 🟢 | 2 (1×1×2) 🟢 | 9 (1×3×3) 🟢 | 4 (1×2×2) 🟢 | 2 (1×1×2) 🟢 |
| `internal-docs` | 18 (3×2×3) 🟢 | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | 36 (3×3×4) 🟢 | 6 (3×1×2) 🟢 | 12 (3×2×2) 🟢 | 36 (3×4×3) 🟢 | 6 (3×1×2) 🟢 | 24 (3×4×2) 🟢 | 6 (3×1×2) 🟢 | 18 (3×2×3) 🟢 | 9 (3×1×3) 🟢 | 18 (3×3×2) 🟢 | 12 (3×2×2) 🟢 | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | 9 (3×3×1) 🟢 | 12 (3×2×2) 🟢 | 36 (3×3×4) 🟢 | 12 (3×2×2) 🟢 | 6 (3×1×2) 🟢 | 27 (3×3×3) 🟢 | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 |
| `backend-api` | 24 (4×2×3) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 16 (4×2×2) 🟢 | 48 (4×3×4) 🟡 | 8 (4×1×2) 🟢 | 24 (4×3×2) 🟢 | 48 (4×4×3) 🟡 | 8 (4×1×2) 🟢 | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 32 (4×4×2) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 4 (4×1×1) 🟢 | 8 (4×1×2) 🟢 | 64 (4×4×4) 🟡 | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 | 48 (4×4×3) 🟡 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 |
| `payments-service` | 30 (5×2×3) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 60 (5×3×4) 🟡 | 10 (5×1×2) 🟢 | 20 (5×2×2) 🟢 | 60 (5×4×3) 🟡 | 10 (5×1×2) 🟢 | 20 (5×2×2) 🟢 | 10 (5×1×2) 🟢 | 15 (5×1×3) 🟢 | 15 (5×1×3) 🟢 | 40 (5×4×2) 🟡 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 5 (5×1×1) 🟢 | 10 (5×1×2) 🟢 | 60 (5×3×4) 🟡 | 20 (5×2×2) 🟢 | 10 (5×1×2) 🟢 | 45 (5×3×3) 🟡 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 |
| `infra-config` | 30 (5×2×3) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 20 (5×2×2) 🟢 | 60 (5×3×4) 🟡 | 10 (5×1×2) 🟢 | 20 (5×2×2) 🟢 | 60 (5×4×3) 🟡 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 15 (5×1×3) 🟢 | 15 (5×1×3) 🟢 | 40 (5×4×2) 🟡 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 5 (5×1×1) 🟢 | 10 (5×1×2) 🟢 | 60 (5×3×4) 🟡 | 20 (5×2×2) 🟢 | 10 (5×1×2) 🟢 | 45 (5×3×3) 🟡 | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 |
| `ml-research` | 24 (4×2×3) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 16 (4×2×2) 🟢 | 48 (4×3×4) 🟡 | 8 (4×1×2) 🟢 | 16 (4×2×2) 🟢 | 48 (4×4×3) 🟡 | 8 (4×1×2) 🟢 | 32 (4×4×2) 🟢 | 8 (4×1×2) 🟢 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 24 (4×3×2) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 8 (4×2×1) 🟢 | 16 (4×2×2) 🟢 | 64 (4×4×4) 🟡 | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 | 36 (4×3×3) 🟢 | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | create_or_update_file | search_repositories | create_repository | get_file_contents | push_files | create_issue | create_pull_request | fork_repository | create_branch | list_commits | list_issues | update_issue | add_issue_comment | search_code | search_issues | search_users | get_issue | get_pull_request | list_pull_requests | create_pull_request_review | merge_pull_request | get_pull_request_files | get_pull_request_status | update_pull_request_branch | get_pull_request_comments | get_pull_request_reviews |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 2 | 1 | 1 | 2 | 3 | 1 | 1 | 4 | 1 | 2 | 2 | 2 | 1 | 4 | 1 | 1 | 1 | 1 | 3 | 2 | 3 | 2 | 1 | 3 | 2 | 1 |
| `internal-docs` | 2 | 1 | 1 | 1 | 3 | 1 | 2 | 4 | 1 | 4 | 1 | 2 | 1 | 3 | 2 | 1 | 1 | 1 | 3 | 2 | 3 | 2 | 1 | 3 | 1 | 1 |
| `backend-api` | 2 | 1 | 1 | 2 | 3 | 1 | 3 | 4 | 1 | 2 | 1 | 1 | 1 | 4 | 1 | 1 | 1 | 1 | 1 | 1 | 4 | 2 | 1 | 4 | 1 | 1 |
| `payments-service` | 2 | 1 | 1 | 1 | 3 | 1 | 2 | 4 | 1 | 2 | 1 | 1 | 1 | 4 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 2 | 1 | 3 | 1 | 1 |
| `infra-config` | 2 | 1 | 1 | 2 | 3 | 1 | 2 | 4 | 1 | 1 | 1 | 1 | 1 | 4 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 2 | 1 | 3 | 1 | 1 |
| `ml-research` | 2 | 1 | 1 | 2 | 3 | 1 | 2 | 4 | 1 | 4 | 1 | 1 | 1 | 3 | 1 | 1 | 1 | 1 | 2 | 2 | 4 | 2 | 1 | 3 | 2 | 1 |

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
