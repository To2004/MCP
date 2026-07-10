# Heatmap coherence review — framework-grounded LLM judge (general, no leakage)

An independent reviewer reads each cell WITH its neighbours and judges coherence (right ballpark + correct ordering), not exact numbers. The systematic patterns below are the guideline-improvement targets.

## fs_corp_filesystem

- **183/210 cells coherent (87%)** · too_high 3 · too_low 24

Miscalibration by operation (pattern → guideline signal):
- `CREATE`: too_high 0, too_low 12
- `OVERWRITE`: too_high 1, too_low 8
- `MODIFY`: too_high 1, too_low 2
- `MOVE`: too_high 1, too_low 2

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
- [too_low] `write_file` × `sensitive/security/private_key.pem` (score 30) — Impact should be higher given the asset sensitivity; compare to move_file
- [too_low] `edit_file` × `sensitive/security/private_key.pem` (score 30) — Impact should be higher given the asset sensitivity; compare to move_file
- [too_low] `move_file` × `sensitive/security/private_key.pem` (score 30) — Impact should be higher given the asset sensitivity; compare to write_file
- [too_low] `create_directory` × `source_code/core.c` (score 8) — Should be higher given the sensitivity of the asset and blast radius
- [too_low] `write_file` × `/` (score 30) — Impact should be higher given the blast radius and asset sensitivity compared to edit_file
- [too_low] `create_directory` × `/` (score 20) — Impact should be higher given the blast radius and asset sensitivity compared to edit_file
- [too_low] `create_directory` × `sensitive/` (score 20) — Score should be higher given the asset sensitivity compared to other tools like write_file or edit_file
- [too_low] `write_file` × `projects/` (score 18) — Impact should be higher given the destructive nature, compared to edit_file on same asset
- [too_low] `create_directory` × `projects/` (score 12) — Impact should be higher given the blast radius, compared to read operations on same asset
- [too_low] `write_file` × `sensitive/security/` (score 30) — Impact should be higher given the destructive nature; compare to edit_file
- [too_low] `create_directory` × `sensitive/security/` (score 20) — Impact should be higher given the recoverable write nature; compare to edit_file
- [too_low] `write_file` × `onboarding/` (score 18) — Should be higher than 18 given the destructive impact; compare to edit_file on this asset.
- [too_low] `create_directory` × `onboarding/` (score 8) — Should be higher than 8 given the recoverable write impact; compare to read operations on this asset.
- [too_low] `write_file` × `sensitive/financials/` (score 24) — Impact should be higher given the blast radius and asset sensitivity compared to edit_file
- [too_low] `create_directory` × `sensitive/financials/` (score 16) — Impact should be higher given the blast radius and asset sensitivity compared to edit_file
- [too_low] `write_file` × `source_code/` (score 24) — Impact should be higher given the destructive nature; compare to edit_file on this asset
- [too_low] `create_directory` × `source_code/` (score 16) — Impact should be higher given the blast radius; compare to read operations on this asset

## github_cbg

- **56/66 cells coherent (85%)** · too_high 3 · too_low 7

Miscalibration by operation (pattern → guideline signal):
- `WRITE`: too_high 0, too_low 6
- `CREATE`: too_high 3, too_low 1

Flagged cells:
- [too_high] `fork_repository` × `internal-docs` (score 24) — Should be lower given the impact and blast radius, compared to create_or_update_file
- [too_high] `fork_repository` × `backend-api` (score 32) — Score is higher than expected based on cross-asset context
- [too_high] `fork_repository` × `infra-config` (score 30) — Score is higher than expected given the blast radius, should be similar to create_issue
- [too_low] `create_issue` × `public-website` (score 4) — Should be higher given its impact and blast radius, compared to create_or_update_file
- [too_low] `create_pull_request` × `public-website` (score 4) — Should be higher given its impact and blast radius, compared to create_or_update_file
- [too_low] `fork_repository` × `public-website` (score 4) — Should be higher given its impact and blast radius, compared to create_or_update_file
- [too_low] `create_issue` × `internal-docs` (score 12) — Should be higher given the impact and blast radius, compared to create_or_update_file
- [too_low] `create_pull_request` × `internal-docs` (score 12) — Should be higher given the impact and blast radius, compared to merge_pull_request
- [too_low] `create_pull_request` × `payments-service` (score 20) — Should be higher given the blast radius, similar to merge_pull_request
- [too_low] `create_pull_request` × `infra-config` (score 20) — Should be higher given the blast radius, similar to merge_pull_request
