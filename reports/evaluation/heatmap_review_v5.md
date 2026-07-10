# Heatmap coherence review — framework-grounded LLM judge (general, no leakage)

An independent reviewer reads each cell WITH its neighbours and judges coherence (right ballpark + correct ordering), not exact numbers. The systematic patterns below are the guideline-improvement targets.

## fs_corp_filesystem

- **187/210 cells coherent (89%)** · too_high 3 · too_low 20

Miscalibration by operation (pattern → guideline signal):
- `CREATE`: too_high 0, too_low 13
- `OVERWRITE`: too_high 1, too_low 5
- `MODIFY`: too_high 1, too_low 1
- `MOVE`: too_high 1, too_low 1

Flagged cells:
- [too_high] `write_file` × `README.md` (score 6) — Score should be 3 given the asset sensitivity and blast radius.
- [too_high] `edit_file` × `README.md` (score 6) — Score should be 3 given the asset sensitivity and blast radius.
- [too_high] `move_file` × `README.md` (score 6) — Score should be 3 given the asset sensitivity and blast radius.
- [too_low] `write_file` × `onboarding/org_chart.png` (score 12) — Score should be higher given the impact and blast radius, compared to edit_file on this asset
- [too_low] `create_directory` × `onboarding/org_chart.png` (score 4) — Score should be higher given the impact and blast radius, compared to write_file on this asset
- [too_low] `move_file` × `onboarding/org_chart.png` (score 12) — Score should be higher given the impact and blast radius, compared to edit_file on this asset
- [too_low] `edit_file` × `projects/db_schema.sql` (score 18) — should be higher than create_directory due to higher impact and blast radius
- [too_low] `create_directory` × `projects/known_defects.csv` (score 6) — should be higher given the blast radius of 1 and impact of 2, compared to read operations
- [too_low] `create_directory` × `sensitive/financials/payslips_q1.csv` (score 8) — Should be higher given the sensitivity of the asset, similar to write operations
- [too_low] `create_directory` × `sensitive/security/audit_log.txt` (score 8) — should be higher given the impact of creating a directory in a sensitive area
- [too_low] `create_directory` × `sensitive/security/private_key.pem` (score 10) — Should be higher due to the asset's high sensitivity compared to other create actions on less sensitive assets
- [too_low] `create_directory` × `source_code/core.c` (score 8) — Should be higher given the sensitivity of the asset and blast radius
- [too_low] `write_file` × `/` (score 45) — Impact should be higher given the blast radius and asset sensitivity compared to edit_file
- [too_low] `create_directory` × `/` (score 20) — Impact should be higher given the asset sensitivity compared to other write operations like edit_file
- [too_low] `create_directory` × `sensitive/` (score 20) — Score should be higher given the asset sensitivity compared to other tools like write_file or edit_file
- [too_low] `write_file` × `projects/` (score 18) — Impact should be higher given the destructive nature, compared to edit_file on same asset
- [too_low] `create_directory` × `projects/` (score 12) — Impact should be higher given the blast radius, compared to read operations on same asset
- [too_low] `create_directory` × `sensitive/security/` (score 20) — Score should be higher given the asset sensitivity compared to other write operations
- [too_low] `write_file` × `onboarding/` (score 18) — Should be higher than 18 given the destructive impact; compare to edit_file on this asset.
- [too_low] `create_directory` × `onboarding/` (score 8) — Should be higher than 8 given the recoverable write impact; compare to read operations on this asset.
- [too_low] `create_directory` × `sensitive/financials/` (score 16) — Score should be higher given the blast radius and asset sensitivity; inconsistent with write/edit operations on this asset
- [too_low] `write_file` × `source_code/` (score 36) — Should be higher than 36 given the impact and blast radius, consistent with edit_file on this asset
- [too_low] `create_directory` × `source_code/` (score 16) — Should be higher than 16 given the impact, consistent with read operations on this asset

## github_cbg

- **50/66 cells coherent (76%)** · too_high 7 · too_low 9

Miscalibration by operation (pattern → guideline signal):
- `WRITE`: too_high 3, too_low 8
- `DELETE`: too_high 3, too_low 1
- `CREATE`: too_high 1, too_low 0

Flagged cells:
- [too_high] `fork_repository` × `public-website` (score 8) — Should be lower than push_files due to smaller blast radius
- [too_high] `create_issue` × `internal-docs` (score 12) — Score is higher than expected based on cross-asset context
- [too_high] `delete_file` × `internal-docs` (score 18) — Score is higher than expected based on cross-asset context
- [too_high] `merge_pull_request` × `internal-docs` (score 27) — Score is higher than expected based on cross-asset context
- [too_high] `delete_file` × `backend-api` (score 24) — Score is anomalously high compared to other assets with similar impact and blast radius
- [too_high] `delete_file` × `ml-research` (score 60) — Score is higher than expected based on cross-asset context, should be 24
- [too_high] `merge_pull_request` × `ml-research` (score 60) — Score is higher than expected based on cross-asset context, should be 36
- [too_low] `create_issue` × `public-website` (score 4) — Should be higher than get_file_contents due to write impact, but lower than create_or_update_file
- [too_low] `delete_file` × `public-website` (score 6) — Should be higher than create_or_update_file due to destructive impact
- [too_low] `push_files` × `backend-api` (score 36) — Should be higher based on blast radius and cross-asset context
- [too_low] `merge_pull_request` × `backend-api` (score 36) — Should be higher based on blast radius and cross-asset context
- [too_low] `create_or_update_file` × `payments-service` (score 30) — Should be higher given the cross-asset context of similar sensitivity
- [too_low] `push_files` × `payments-service` (score 45) — Should be higher given the cross-asset context of similar sensitivity
- [too_low] `merge_pull_request` × `payments-service` (score 45) — Should be higher given the cross-asset context of similar sensitivity
- [too_low] `create_or_update_file` × `infra-config` (score 45) — Should be higher given the tool's impact on more sensitive assets
- [too_low] `create_pull_request` × `infra-config` (score 20) — Should be higher given the tool's impact on more sensitive assets
