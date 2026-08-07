# Scan — github:cbg

_kind=github · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_desc · bands={'low': 9, 'medium': 26, 'high': 33, 'critical': 16, 'na': 103}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–25), scaled to this max.

## Inferred domain profile

- **mcp_kind**: GitHub repository management
- **asset_meaning**: repositories and mutable states within the GitHub organization
- **blast_radius_meaning**: the extent of changes a tool can make to repositories or their contents, from modifying single files to affecting entire branches or infrastructure configurations
- **dangerous_classes**: handles card flows, proprietary ML research, infra/CI config: deploy keys, tokens, .env templates
- **irreversible_actions**: merge_pull_request, delete_file, push_files
- **worked_example**: The 'merge_pull_request' tool on the 'payments-service' asset could lead to unreviewed code changes affecting live payment processing.

## Tool impact

| tool | impact |
| --- | --- |
| `search_repositories` | 3 |
| `get_file_contents` | 3 |
| `list_commits` | 2 |
| `get_issue` | 3 |
| `create_issue` | 4 |
| `create_or_update_file` | 5 |
| `push_files` | 4 |
| `delete_file` | 5 |
| `create_pull_request` | 4 |
| `merge_pull_request` | 5 |
| `fork_repository` | 4 |

## Asset sensitivity

_Not scored in `impact_mode=five_level_v2_desc`: the organization's written description of this server states how severe each asset is, so no separate 1–5 sensitivity primitive is derived. The 17 assets below still form the matrix axis; the score is `blast × impact`._

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
| `repository-records` | — |
| `commit-history` | — |
| `issue-records` | — |
| `repository-contents` | — |
| `pull-request-records` | — |

## Risk matrix (score · band)

_Each cell shows `score (blast×impact)` — sensitivity is not scored in this mode; impact_mode=five_level_v2_desc, score ranges 0–25. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | search_repositories | get_file_contents | list_commits | get_issue | create_issue | create_or_update_file | push_files | delete_file | create_pull_request | merge_pull_request | fork_repository |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 6 (2×3) 🟢 | 3 (1×3) 🟢 | 2 (1×2) 🟢 | 3 (1×3) 🟢 | 4 (1×4) 🟢 | 20 (4×5) 🔴 | 12 (3×4) 🟡 | 20 (4×5) 🔴 | 8 (2×4) 🟡 | 20 (4×5) 🔴 | 16 (4×4) 🟠 |
| `internal-docs` | 6 (2×3) 🟢 | 6 (2×3) 🟢 | 4 (2×2) 🟢 | N/A | N/A | 15 (3×5) 🟠 | 12 (3×4) 🟡 | 5 (1×5) 🟢 | 8 (2×4) 🟡 | 20 (4×5) 🔴 | 20 (5×4) 🔴 |
| `backend-api` | 6 (2×3) 🟢 | 3 (1×3) 🟢 | 4 (2×2) 🟢 | N/A | N/A | 15 (3×5) 🟠 | 12 (3×4) 🟡 | 15 (3×5) 🟠 | 12 (3×4) 🟡 | 20 (4×5) 🔴 | 20 (5×4) 🔴 |
| `payments-service` | 6 (2×3) 🟢 | 15 (5×3) 🟠 | 4 (2×2) 🟢 | 3 (1×3) 🟢 | 8 (2×4) 🟡 | 25 (5×5) 🔴 | 20 (5×4) 🔴 | 25 (5×5) 🔴 | 12 (3×4) 🟡 | 25 (5×5) 🔴 | 20 (5×4) 🔴 |
| `infra-config` | 12 (4×3) 🟡 | 15 (5×3) 🟠 | 4 (2×2) 🟢 | N/A | N/A | 25 (5×5) 🔴 | 20 (5×4) 🔴 | 25 (5×5) 🔴 | 12 (3×4) 🟡 | 25 (5×5) 🔴 | 20 (5×4) 🔴 |
| `ml-research` | 6 (2×3) 🟢 | 15 (5×3) 🟠 | 4 (2×2) 🟢 | N/A | N/A | 15 (3×5) 🟠 | 12 (3×4) 🟡 | 15 (3×5) 🟠 | 8 (2×4) 🟡 | 20 (4×5) 🔴 | 20 (5×4) 🔴 |
| `branch-heads` | N/A | N/A | N/A | N/A | N/A | 15 (3×5) 🟠 | 16 (4×4) 🟠 | N/A | 8 (2×4) 🟡 | 20 (4×5) 🔴 | N/A |
| `issues-and-comments` | N/A | N/A | N/A | 3 (1×3) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `pull-requests-and-reviews` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×4) 🟡 | 20 (4×5) 🔴 | N/A |
| `org-external-copies` | N/A | 15 (5×3) 🟠 | 4 (2×2) 🟢 | N/A | N/A | 25 (5×5) 🔴 | 16 (4×4) 🟠 | N/A | N/A | N/A | 20 (5×4) 🔴 |
| `platform-user-directory` | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-catalog` | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-records` | 6 (2×3) 🟢 | 3 (1×3) 🟢 | 8 (4×2) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `commit-history` | N/A | N/A | 4 (2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `issue-records` | N/A | N/A | N/A | 3 (1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-contents` | N/A | 3 (1×3) 🟢 | N/A | N/A | N/A | 5 (1×5) 🟢 | 12 (3×4) 🟡 | 15 (3×5) 🟠 | N/A | 25 (5×5) 🔴 | N/A |
| `pull-request-records` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | search_repositories | get_file_contents | list_commits | get_issue | create_issue | create_or_update_file | push_files | delete_file | create_pull_request | merge_pull_request | fork_repository |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `public-website` | 2 | 1 | 1 | 1 | 1 | 4 | 3 | 4 | 2 | 4 | 4 |
| `internal-docs` | 2 | 2 | 2 | N/A | N/A | 3 | 3 | 1 | 2 | 4 | 5 |
| `backend-api` | 2 | 1 | 2 | N/A | N/A | 3 | 3 | 3 | 3 | 4 | 5 |
| `payments-service` | 2 | 5 | 2 | 1 | 2 | 5 | 5 | 5 | 3 | 5 | 5 |
| `infra-config` | 4 | 5 | 2 | N/A | N/A | 5 | 5 | 5 | 3 | 5 | 5 |
| `ml-research` | 2 | 5 | 2 | N/A | N/A | 3 | 3 | 3 | 2 | 4 | 5 |
| `branch-heads` | N/A | N/A | N/A | N/A | N/A | 3 | 4 | N/A | 2 | 4 | N/A |
| `issues-and-comments` | N/A | N/A | N/A | 1 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `pull-requests-and-reviews` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 4 | N/A |
| `org-external-copies` | N/A | 5 | 2 | N/A | N/A | 5 | 4 | N/A | N/A | N/A | 5 |
| `platform-user-directory` | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-catalog` | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-records` | 2 | 1 | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `commit-history` | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `issue-records` | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-contents` | N/A | 1 | N/A | N/A | N/A | 1 | 3 | 3 | N/A | 5 | N/A |
| `pull-request-records` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

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
