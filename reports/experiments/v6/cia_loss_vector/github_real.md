# Scan — github:real · CIA-native score

_kind=github · scoring=cia_loss_vector · source=five_level_v2_v5 artifacts · score_max=125 · bands={'low': 30, 'medium': 95, 'high': 14, 'critical': 21, 'na': 360}_

`score = max(existing score, sensitivity floor, max over C/I/A of S x B_f x I_f)` — the same three factors as v5, computed **per security objective** and collapsed by the high-water mark. Sensitivity and coverage are the unchanged v5 numbers; the 1–5 action ladder is replaced by per-objective impact. Every cell carries the objective that drove it, and that objective selects the control.

## Scoring rules applied

- score = max(existing score, sensitivity floor, max over C/I/A of S x B_f x I_f), range 0-125
- **INVARIANT: a cell is never scored below its existing value.** CIA is evidence added to the framework's judgement, not a re-weighting of it — so nothing the existing scale prices correctly can move down
- sensitivity floor: an asset the org rates 5 never scores below 50, and one rated 4 never below 25 — a crown jewel is not a routine cell just because the verb is a listing. Mirrors the pipeline's existing gated blast floor, one factor over
- sensitivity is NOT split per objective. `C>I>A` says disclosure hurts most on this asset; it does not say integrity loss is a tier cheaper. The loss axis breaks ties between objectives and routes the control, nothing more
- per-objective impact replaces the 1-5 action ladder as a LOWER BOUND: a READ is I_C=5 (a total confidentiality loss) and I_I=0, while writes and deletes keep their existing tiers — so only under-priced reads move
- self-sufficient assets: for CONFIDENTIALITY only, and only for content-returning ops, one item is the whole loss so B_C is treated as 5
- escape (CVSS subsequent system): assets flagged hub/self-sufficient/population gain 25% on the driving objective at coverage >= 4, capped at the scale max
- the driving objective is kept and selects the control: C -> deny, I -> confirm, A -> throttle
- bands are the v5 thresholds on the score (low <17, medium 17-49, high 50-99, critical >=100), so the two arms are directly comparable

## Tool impact per objective

_How completely one call violates each objective; 0 means it cannot touch that objective at all. Replaces the single 1–5 impact number._

| tool | atomic ops | I_C | I_I | I_A |
| --- | --- | --- | --- | --- |
| `create_or_update_file` | CREATE, WRITE | 0 | 5 | 0 |
| `search_repositories` | SEARCH | 4 | 0 | 0 |
| `create_repository` | CREATE, WRITE | 4 | 4 | 0 |
| `get_file_contents` | READ | 5 | 3 | 0 |
| `push_files` | WRITE | 0 | 4 | 0 |
| `create_issue` | CREATE, WRITE | 4 | 4 | 0 |
| `create_pull_request` | CREATE, WRITE | 0 | 4 | 0 |
| `fork_repository` | CREATE | 0 | 4 | 0 |
| `create_branch` | CREATE, WRITE | 0 | 4 | 0 |
| `list_commits` | LIST | 2 | 2 | 0 |
| `list_issues` | LIST | 2 | 2 | 0 |
| `update_issue` | MODIFY | 4 | 4 | 0 |
| `add_issue_comment` | WRITE | 4 | 4 | 0 |
| `search_code` | SEARCH | 4 | 3 | 0 |
| `search_issues` | SEARCH | 4 | 3 | 0 |
| `search_users` | SEARCH | 4 | 0 | 0 |
| `get_issue` | READ | 5 | 0 | 0 |
| `get_pull_request` | READ | 5 | 3 | 0 |
| `list_pull_requests` | LIST | 2 | 2 | 0 |
| `create_pull_request_review` | CREATE, WRITE | 0 | 4 | 0 |
| `merge_pull_request` | WRITE | 0 | 5 | 0 |
| `get_pull_request_files` | READ | 5 | 3 | 0 |
| `get_pull_request_status` | METADATA | 2 | 2 | 0 |
| `update_pull_request_branch` | MODIFY | 0 | 4 | 0 |
| `get_pull_request_comments` | READ | 5 | 3 | 0 |
| `get_pull_request_reviews` | READ | 5 | 3 | 0 |

## Asset sensitivity per objective

_Unchanged from the v5 scan and NOT split per objective — a loss-axis ranking is not a magnitude. The axis breaks ties between objectives and routes the control._

| asset | sensitivity | loss axis | flags |
| --- | --- | --- | --- |
| `infra-config` | 4 | I>A>C | hub |
| `payments-service` | 4 | I>C>A | hub |
| `backend-api` | 4 | I>C>A | hub |
| `ml-research` | 4 | C>I>A | — |
| `internal-docs` | 3 | C>I>A | — |
| `public-website` | 1 | I>C>A | public |
| `repository-contents` | 4 | C>I>A | — |
| `code-records` | 4 | C>I>A | population |
| `branch-heads` | 4 | I>A>C | hub |
| `pull-requests-and-reviews` | 4 | I>C>A | hub |
| `pull-request-records` | 4 | I>C>A | hub |
| `issues-and-comments` | 3 | C>I>A | — |
| `issue-records` | 3 | I>C>A | — |
| `org-external-copies` | 4 | C>I>A | population |
| `repository-records` | 3 | I>C>A | hub |
| `repository-catalog` | 3 | C>I>A | metadata-only |
| `branch-directory` | 2 | C>I>A | metadata-only |
| `commit-list` | 2 | C>I>A | metadata-only |
| `issue-catalog` | 2 | C>I>A | metadata-only |
| `platform-user-directory` | 1 | C>I>A | public |

## Risk matrix (score · driver)

_Each cell shows `score (driver: S×B×I)`; range 0–125, peak here 125. Colour is by score on the v5 thresholds: 🟢 <17 · 🟡 17–49 · 🟠 50–99 · 🔴 ≥100._

| asset \ tool | create_or_update_file | search_repositories | create_repository | get_file_contents | push_files | create_issue | create_pull_request | fork_repository | create_branch | list_commits | list_issues | update_issue | add_issue_comment | search_code | search_issues | search_users | get_issue | get_pull_request | list_pull_requests | create_pull_request_review | merge_pull_request | get_pull_request_files | get_pull_request_status | update_pull_request_branch | get_pull_request_comments | get_pull_request_reviews |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `infra-config` | 60 (I: 4×3×5) 🟠 | N/A | N/A | 25 (C: 4×1×5) 🟡 | 100 (I: 4×5×4) 🔴 | N/A | 48 (I: 4×3×4) 🟡 | 100 (I: 4×5×4) 🔴 | 48 (I: 4×3×4) 🟡 | 0 | N/A | N/A | N/A | 48 (C: 4×3×4) 🟡 | N/A | N/A | N/A | 25 (C: 4×1×5) 🟡 | 0 | 48 (I: 4×3×4) 🟡 | 125 (I: 4×5×5) 🔴 | 25 (C: 4×1×5) 🟡 | 0 | 80 (I: 4×4×4) 🟠 | N/A | 25 (C: 4×1×5) 🟡 |
| `payments-service` | 60 (I: 4×3×5) 🟠 | N/A | N/A | 25 (C: 4×1×5) 🟡 | 100 (I: 4×5×4) 🔴 | N/A | 80 (I: 4×4×4) 🟠 | 100 (I: 4×5×4) 🔴 | 48 (I: 4×3×4) 🟡 | 0 | 0 | N/A | N/A | 48 (C: 4×3×4) 🟡 | 32 (C: 4×2×4) 🟡 | N/A | N/A | 25 (C: 4×1×5) 🟡 | 0 | 48 (I: 4×3×4) 🟡 | 125 (I: 4×5×5) 🔴 | 25 (C: 4×1×5) 🟡 | 0 | 48 (I: 4×3×4) 🟡 | 25 (C: 4×1×5) 🟡 | 25 (C: 4×1×5) 🟡 |
| `backend-api` | 60 (I: 4×3×5) 🟠 | N/A | N/A | 25 (C: 4×1×5) 🟡 | 100 (I: 4×5×4) 🔴 | N/A | 48 (I: 4×3×4) 🟡 | 100 (I: 4×5×4) 🔴 | 100 (I: 4×5×4) 🔴 | 0 | 0 | N/A | N/A | 48 (C: 4×3×4) 🟡 | N/A | N/A | N/A | 25 (C: 4×1×5) 🟡 | 0 | 48 (I: 4×3×4) 🟡 | 125 (I: 4×5×5) 🔴 | 40 (C: 4×2×5) 🟡 | 0 | 48 (I: 4×3×4) 🟡 | 40 (C: 4×2×5) 🟡 | 25 (C: 4×1×5) 🟡 |
| `ml-research` | 60 (C: 4×3×5) 🟠 | N/A | N/A | 25 (C: 4×1×5) 🟡 | 48 (C: 4×3×4) 🟡 | N/A | 48 (C: 4×3×4) 🟡 | 80 (C: 4×5×4) 🟠 | N/A | 0 | 0 | N/A | N/A | 48 (C: 4×3×4) 🟡 | 32 (C: 4×2×4) 🟡 | N/A | N/A | N/A | 0 | 48 (C: 4×3×4) 🟡 | N/A | 25 (C: 4×1×5) 🟡 | N/A | 48 (C: 4×3×4) 🟡 | N/A | N/A |
| `internal-docs` | 45 (C: 3×3×5) 🟡 | N/A | N/A | 15 (C: 3×1×5) 🟢 | 36 (C: 3×3×4) 🟡 | 24 (C: 3×2×4) 🟡 | 24 (C: 3×2×4) 🟡 | N/A | 24 (C: 3×2×4) 🟡 | 12 (C: 3×2×2) 🟢 | 6 (C: 3×1×2) 🟢 | N/A | N/A | 36 (C: 3×3×4) 🟡 | 24 (C: 3×2×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `public-website` | 15 (I: 1×3×5) 🟢 | N/A | N/A | 5 (C: 1×1×5) 🟢 | 16 (I: 1×4×4) 🟢 | 8 (I: 1×2×4) 🟢 | 8 (I: 1×2×4) 🟢 | 16 (I: 1×4×4) 🟢 | 8 (I: 1×2×4) 🟢 | 6 (I: 1×3×2) 🟢 | 2 (I: 1×1×2) 🟢 | N/A | N/A | 8 (C: 1×2×4) 🟢 | N/A | N/A | N/A | 5 (C: 1×1×5) 🟢 | 6 (I: 1×3×2) 🟢 | 8 (I: 1×2×4) 🟢 | 20 (I: 1×4×5) 🟡 | 5 (C: 1×1×5) 🟢 | 2 (I: 1×1×2) 🟢 | 16 (I: 1×4×4) 🟢 | 5 (C: 1×1×5) 🟢 | 5 (C: 1×1×5) 🟢 |
| `repository-contents` | 60 (C: 4×3×5) 🟠 | N/A | N/A | 80 (C: 4×4×5) 🟠 | 64 (C: 4×4×4) 🟠 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 48 (C: 4×3×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 40 (C: 4×2×5) 🟡 | N/A | 64 (C: 4×4×4) 🟠 | N/A | N/A |
| `code-records` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 100 (C: 4×5×4) 🔴 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `branch-heads` | 125 (I: 4×5×5) 🔴 | N/A | N/A | N/A | 100 (I: 4×5×4) 🔴 | N/A | 48 (I: 4×3×4) 🟡 | N/A | 100 (I: 4×5×4) 🔴 | 0 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 125 (I: 4×5×5) 🔴 | N/A | N/A | 100 (I: 4×5×4) 🔴 | N/A | N/A |
| `pull-requests-and-reviews` | N/A | N/A | N/A | N/A | N/A | N/A | 48 (I: 4×3×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | 48 (C: 4×3×4) 🟡 | 48 (C: 4×3×4) 🟡 | N/A | N/A | 25 (C: 4×1×5) 🟡 | 0 | 48 (I: 4×3×4) 🟡 | 125 (I: 4×5×5) 🔴 | 25 (C: 4×1×5) 🟡 | 0 | 48 (I: 4×3×4) 🟡 | 25 (C: 4×1×5) 🟡 | 25 (C: 4×1×5) 🟡 |
| `pull-request-records` | 60 (I: 4×3×5) 🟠 | N/A | N/A | N/A | N/A | N/A | 80 (I: 4×4×4) 🟠 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 25 (C: 4×1×5) 🟡 | 0 | 48 (I: 4×3×4) 🟡 | 125 (I: 4×5×5) 🔴 | 25 (C: 4×1×5) 🟡 | 0 | 48 (I: 4×3×4) 🟡 | 25 (C: 4×1×5) 🟡 | 25 (C: 4×1×5) 🟡 |
| `issues-and-comments` | N/A | N/A | N/A | N/A | N/A | 24 (C: 3×2×4) 🟡 | N/A | N/A | N/A | N/A | 18 (C: 3×3×2) 🟡 | 24 (C: 3×2×4) 🟡 | 24 (C: 3×2×4) 🟡 | N/A | 36 (C: 3×3×4) 🟡 | N/A | 15 (C: 3×1×5) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 15 (C: 3×1×5) 🟢 | N/A |
| `issue-records` | N/A | N/A | N/A | N/A | N/A | 24 (I: 3×2×4) 🟡 | N/A | N/A | N/A | N/A | 12 (I: 3×2×2) 🟢 | 24 (I: 3×2×4) 🟡 | 24 (I: 3×2×4) 🟡 | N/A | 36 (C: 3×3×4) 🟡 | N/A | 15 (C: 3×1×5) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `org-external-copies` | N/A | 100 (C: 4×5×4) 🔴 | 100 (C: 4×5×4) 🔴 | N/A | N/A | N/A | N/A | 100 (C: 4×5×4) 🔴 | N/A | N/A | N/A | N/A | N/A | 48 (C: 4×3×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-records` | 45 (I: 3×3×5) 🟡 | N/A | 24 (I: 3×2×4) 🟡 | N/A | N/A | N/A | N/A | 75 (I: 3×5×4) 🟠 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-catalog` | N/A | 36 (C: 3×3×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `branch-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 24 (C: 2×3×4) 🟡 | 8 (C: 2×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `commit-list` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (C: 2×4×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `issue-catalog` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 12 (C: 2×3×2) 🟢 | N/A | N/A | N/A | 24 (C: 2×3×4) 🟡 | N/A | 10 (C: 2×1×5) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `platform-user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 12 (C: 1×3×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Per-objective scores

_The vector behind each cell, before the high-water mark. A zero means the tool cannot violate that objective at all. Top 25 by score._

| asset | tool | score_C | score_I | score_A | → score | driver |
| --- | --- | --- | --- | --- | --- | --- |
| `infra-config` | `merge_pull_request` | 0 | 125 | 0 | **125** | I |
| `payments-service` | `merge_pull_request` | 0 | 125 | 0 | **125** | I |
| `backend-api` | `merge_pull_request` | 0 | 125 | 0 | **125** | I |
| `branch-heads` | `create_or_update_file` | 0 | 125 | 0 | **125** | I |
| `branch-heads` | `merge_pull_request` | 0 | 125 | 0 | **125** | I |
| `pull-requests-and-reviews` | `merge_pull_request` | 0 | 125 | 0 | **125** | I |
| `pull-request-records` | `merge_pull_request` | 0 | 125 | 0 | **125** | I |
| `infra-config` | `push_files` | 0 | 100 | 0 | **100** | I |
| `infra-config` | `fork_repository` | 0 | 100 | 0 | **100** | I |
| `payments-service` | `push_files` | 0 | 100 | 0 | **100** | I |
| `payments-service` | `fork_repository` | 0 | 100 | 0 | **100** | I |
| `backend-api` | `push_files` | 0 | 100 | 0 | **100** | I |
| `backend-api` | `fork_repository` | 0 | 100 | 0 | **100** | I |
| `backend-api` | `create_branch` | 0 | 100 | 0 | **100** | I |
| `code-records` | `search_code` | 100 | 0 | 0 | **100** | C |
| `branch-heads` | `push_files` | 0 | 100 | 0 | **100** | I |
| `branch-heads` | `create_branch` | 0 | 100 | 0 | **100** | I |
| `branch-heads` | `update_pull_request_branch` | 0 | 100 | 0 | **100** | I |
| `org-external-copies` | `search_repositories` | 100 | 0 | 0 | **100** | C |
| `org-external-copies` | `create_repository` | 100 | 80 | 0 | **100** | C |
| `org-external-copies` | `fork_repository` | 100 | 80 | 0 | **100** | C |
| `infra-config` | `update_pull_request_branch` | 0 | 80 | 0 | **80** | I |
| `payments-service` | `create_pull_request` | 0 | 80 | 0 | **80** | I |
| `ml-research` | `fork_repository` | 80 | 80 | 0 | **80** | C |
| `repository-contents` | `get_file_contents` | 80 | 0 | 0 | **80** | C |

## Blast radius (coverage · 1–5)

_Unchanged from the v5 scan: what fraction of the asset ONE call reaches. Used as B in the score, per objective._

| asset \ tool | create_or_update_file | search_repositories | create_repository | get_file_contents | push_files | create_issue | create_pull_request | fork_repository | create_branch | list_commits | list_issues | update_issue | add_issue_comment | search_code | search_issues | search_users | get_issue | get_pull_request | list_pull_requests | create_pull_request_review | merge_pull_request | get_pull_request_files | get_pull_request_status | update_pull_request_branch | get_pull_request_comments | get_pull_request_reviews |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `infra-config` | 3 | N/A | N/A | 1 | 5 | N/A | 3 | 5 | 3 | 3 | N/A | N/A | N/A | 3 | N/A | N/A | N/A | 1 | 2 | 3 | 5 | 1 | 1 | 4 | N/A | 1 |
| `payments-service` | 3 | N/A | N/A | 1 | 5 | N/A | 4 | 5 | 3 | 3 | 2 | N/A | N/A | 3 | 2 | N/A | N/A | 1 | 2 | 3 | 5 | 1 | 1 | 3 | 1 | 1 |
| `backend-api` | 3 | N/A | N/A | 1 | 5 | N/A | 3 | 5 | 5 | 3 | 2 | N/A | N/A | 3 | N/A | N/A | N/A | 1 | 2 | 3 | 5 | 2 | 1 | 3 | 2 | 1 |
| `ml-research` | 3 | N/A | N/A | 1 | 3 | N/A | 3 | 5 | N/A | 3 | 2 | N/A | N/A | 3 | 2 | N/A | N/A | N/A | 2 | 3 | N/A | 1 | N/A | 3 | N/A | N/A |
| `internal-docs` | 3 | N/A | N/A | 1 | 3 | 2 | 2 | N/A | 2 | 2 | 1 | N/A | N/A | 3 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `public-website` | 3 | N/A | N/A | 1 | 4 | 2 | 2 | 4 | 2 | 3 | 1 | N/A | N/A | 2 | N/A | N/A | N/A | 1 | 3 | 2 | 4 | 1 | 1 | 4 | 1 | 1 |
| `repository-contents` | 3 | N/A | N/A | 4 | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | 4 | N/A | N/A |
| `code-records` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `branch-heads` | 5 | N/A | N/A | N/A | 5 | N/A | 3 | N/A | 5 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | N/A | N/A | 5 | N/A | N/A |
| `pull-requests-and-reviews` | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 3 | N/A | N/A | 1 | 2 | 3 | 5 | 1 | 1 | 3 | 1 | 1 |
| `pull-request-records` | 3 | N/A | N/A | N/A | N/A | N/A | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 3 | 3 | 5 | 1 | 1 | 3 | 1 | 1 |
| `issues-and-comments` | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | 3 | 2 | 2 | N/A | 3 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A |
| `issue-records` | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | 2 | 2 | 2 | N/A | 3 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `org-external-copies` | N/A | 5 | 5 | N/A | N/A | N/A | N/A | 5 | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-records` | 3 | N/A | 2 | N/A | N/A | N/A | N/A | 5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `repository-catalog` | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `branch-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `commit-list` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `issue-catalog` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | 3 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `platform-user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Controls implied

_The driving objective selects the control, which a bare number cannot do. Cells scoring ≥ 50._

| control | cells | why |
| --- | --- | --- |
| **require human confirmation** | 25 | recoverable only if a restore path exists |
| **deny** | 10 | disclosure cannot be undone, so approval buys nothing |

## Biggest changes from the v5 product (98 of 160 cells moved)

| asset | tool | driver | v5 | v6 | Δ | workings |
| --- | --- | --- | --- | --- | --- | --- |
| `org-external-copies` | `search_repositories` | C | 40.0 | **100** 🔴 | +60 | 4×5×4 |
| `code-records` | `search_code` | C | 60.0 | **100** 🔴 | +40 | 4×5×4 |
| `repository-contents` | `get_file_contents` | C | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `infra-config` | `merge_pull_request` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `payments-service` | `merge_pull_request` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `backend-api` | `merge_pull_request` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `branch-heads` | `create_or_update_file` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `branch-heads` | `merge_pull_request` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `pull-requests-and-reviews` | `merge_pull_request` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `pull-request-records` | `merge_pull_request` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `infra-config` | `push_files` | I | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `infra-config` | `fork_repository` | I | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `payments-service` | `push_files` | I | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `payments-service` | `fork_repository` | I | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `backend-api` | `push_files` | I | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `backend-api` | `fork_repository` | I | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `backend-api` | `create_branch` | I | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `branch-heads` | `push_files` | I | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `branch-heads` | `create_branch` | I | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `branch-heads` | `update_pull_request_branch` | I | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `org-external-copies` | `create_repository` | C | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `org-external-copies` | `fork_repository` | C | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `repository-catalog` | `search_repositories` | C | 18.0 | **36** 🟡 | +18 | 3×3×4 |
| `infra-config` | `get_pull_request_status` | — | 8.0 | **25** 🟡 | +17 | existing score |
| `payments-service` | `get_pull_request_status` | — | 8.0 | **25** 🟡 | +17 | existing score |
| `backend-api` | `get_pull_request_status` | — | 8.0 | **25** 🟡 | +17 | existing score |
| `pull-requests-and-reviews` | `get_pull_request_status` | — | 8.0 | **25** 🟡 | +17 | existing score |
| `pull-request-records` | `get_pull_request_status` | — | 8.0 | **25** 🟡 | +17 | existing score |
| `infra-config` | `update_pull_request_branch` | I | 64.0 | **80** 🟠 | +16 | 4×4×4 |
| `payments-service` | `create_pull_request` | I | 64.0 | **80** 🟠 | +16 | 4×4×4 |

_Top 30 by absolute change; 98 moved in total._
