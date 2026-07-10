# Heatmap coherence review — framework-grounded LLM judge (general, no leakage)

An independent reviewer reads each cell WITH its neighbours and judges coherence (right ballpark + correct ordering), not exact numbers. The systematic patterns below are the guideline-improvement targets.

## github_cbg

- **47/66 cells coherent (71%)** · too_high 6 · too_low 13

Miscalibration by operation (pattern → guideline signal):
- `WRITE`: too_high 2, too_low 9
- `CREATE`: too_high 2, too_low 2
- `READ`: too_high 1, too_low 2
- `DELETE`: too_high 1, too_low 0

Flagged cells:
- [too_high] `fork_repository` × `public-website` (score 8) — Score is too high for this sensitivity level, given the tool's impact
- [too_high] `fork_repository` × `internal-docs` (score 24) — Should be lower given the blast radius, similar to create_issue
- [too_high] `delete_file` × `payments-service` (score 30) — Score is too high compared to similar tools on this asset
- [too_high] `get_file_contents` × `infra-config` (score 10) — Score should be lower, consistent with other assets of similar sensitivity
- [too_high] `create_issue` × `ml-research` (score 16) — Score should be lower, consistent with impact 2 and blast 2 on less sensitive assets
- [too_high] `create_pull_request` × `ml-research` (score 16) — Score should be lower, consistent with impact 2 and blast 2 on less sensitive assets
- [too_low] `create_issue` × `public-website` (score 4) — Score should be higher given the write impact; compare with create_or_update_file
- [too_low] `create_pull_request` × `public-website` (score 4) — Score should be higher given the write impact; compare with merge_pull_request
- [too_low] `create_issue` × `internal-docs` (score 12) — Should be higher given the write impact, similar to create_or_update_file
- [too_low] `create_pull_request` × `internal-docs` (score 12) — Should be higher given the write impact, similar to merge_pull_request
- [too_low] `create_issue` × `backend-api` (score 8) — Should be higher given the impact and consistency across assets
- [too_low] `create_pull_request` × `backend-api` (score 16) — Should be higher given the impact and consistency across assets
- [too_low] `get_file_contents` × `payments-service` (score 5) — Should be higher given the asset sensitivity compared to cross-asset context
- [too_low] `get_issue` × `payments-service` (score 5) — Should be higher given the asset sensitivity compared to cross-asset context
- [too_low] `create_or_update_file` × `payments-service` (score 30) — Should be higher given the asset sensitivity compared to cross-asset context
- [too_low] `fork_repository` × `payments-service` (score 40) — Should be higher given the asset sensitivity compared to cross-asset context
- [too_low] `create_issue` × `infra-config` (score 10) — Score should be higher, consistent with other assets of similar sensitivity
- [too_low] `create_pull_request` × `infra-config` (score 30) — Score should be higher, consistent with other assets of similar sensitivity
- [too_low] `fork_repository` × `ml-research` (score 32) — Score should be higher, consistent with impact 2 and blast 4 on more sensitive assets
