# Heatmap coherence review — framework-grounded LLM judge (general, no leakage)

An independent reviewer reads each cell WITH its neighbours and judges coherence (right ballpark + correct ordering), not exact numbers. The systematic patterns below are the guideline-improvement targets.

## fs_corp_filesystem

- **178/210 cells coherent (85%)** · too_high 8 · too_low 24

Miscalibration by operation (pattern → guideline signal):
- `CREATE`: too_high 0, too_low 10
- `MOVE`: too_high 8, too_low 1
- `OVERWRITE`: too_high 0, too_low 7
- `MODIFY`: too_high 0, too_low 5
- `SEARCH`: too_high 0, too_low 1

Flagged cells:
- [too_high] `move_file` × `onboarding/org_chart.png` (score 12) — Score is higher than expected given the blast radius and impact, compared to write_file
- [too_high] `move_file` × `projects/known_defects.csv` (score 18) — impact and blast radius are too high compared to edit/write operations on same asset
- [too_high] `move_file` × `/` (score 45) — Should be lower than write_file given its blast radius
- [too_high] `move_file` × `sensitive/` (score 60) — Score is too high compared to write/edit operations which have similar impact but lower blast radius
- [too_high] `move_file` × `sensitive/security/` (score 60) — Score is too high compared to write/edit operations, which are also destructive but have a smaller blast radius
- [too_high] `move_file` × `onboarding/` (score 18) — Should be lower given the blast radius; should match write/edit scores.
- [too_high] `move_file` × `sensitive/financials/` (score 36) — Should be lower than write/edit due to recoverable impact
- [too_high] `move_file` × `source_code/` (score 36) — Should be lower than write/edit due to recoverable nature despite higher blast radius
- [too_low] `write_file` × `README.md` (score 6) — Should be higher than 6 given the destructive impact; should match edit_file score.
- [too_low] `create_directory` × `README.md` (score 2) — Should be higher than 2 given the recoverable write impact; should match list_directory score for consistency.
- [too_low] `move_file` × `README.md` (score 6) — Should be higher than 6 given the destructive impact; should match write_file score for consistency.
- [too_low] `create_directory` × `onboarding/org_chart.png` (score 4) — Should be higher given the blast radius and impact, compared to other tools like move_file
- [too_low] `create_directory` × `projects/db_schema.sql` (score 6) — should be higher given the asset sensitivity and impact
- [too_low] `create_directory` × `projects/known_defects.csv` (score 6) — should be higher given the impact and blast radius, compared to write operations on same asset
- [too_low] `create_directory` × `sensitive/financials/payslips_q1.csv` (score 8) — Should be higher given the sensitivity of the asset, similar to write operations
- [too_low] `create_directory` × `sensitive/security/audit_log.txt` (score 8) — Should be higher given the sensitivity of the asset and blast radius
- [too_low] `create_directory` × `sensitive/security/private_key.pem` (score 10) — Should be higher given the asset sensitivity, compare with read_multiple_files
- [too_low] `search_files` × `sensitive/security/private_key.pem` (score 10) — Should be higher given the blast radius, compare with read_multiple_files
- [too_low] `create_directory` × `source_code/core.c` (score 8) — should be higher given the sensitivity of the asset, similar to write operations
- [too_low] `write_file` × `/` (score 30) — Should be higher than create_directory given its impact
- [too_low] `edit_file` × `/` (score 30) — Should be higher than create_directory given its impact
- [too_low] `write_file` × `sensitive/` (score 30) — Should be higher than create_directory due to irreversible impact
- [too_low] `edit_file` × `sensitive/` (score 30) — Should be higher than create_directory due to irreversible impact
- [too_low] `create_directory` × `projects/` (score 12) — Should be higher due to its recoverable write impact compared to read operations
- [too_low] `write_file` × `sensitive/security/` (score 30) — Should be higher than create_directory due to irreversible impact
- [too_low] `edit_file` × `sensitive/security/` (score 30) — Should be higher than create_directory due to irreversible impact
- [too_low] `write_file` × `onboarding/` (score 12) — Should be higher than 12 given the destructive impact; should match edit_file score.
- [too_low] `create_directory` × `onboarding/` (score 8) — Should be higher given the blast radius; should match read operations on this asset.
- [too_low] `write_file` × `sensitive/financials/` (score 24) — Should be higher than create_directory due to irreversible impact
- [too_low] `edit_file` × `sensitive/financials/` (score 24) — Should be higher than create_directory due to irreversible impact

## github_cbg

- **52/66 cells coherent (79%)** · too_high 4 · too_low 10

Miscalibration by operation (pattern → guideline signal):
- `WRITE`: too_high 2, too_low 6
- `CREATE`: too_high 2, too_low 4

Flagged cells:
- [too_high] `fork_repository` × `internal-docs` (score 24) — Should be lower given the impact and blast radius, compared to create_or_update_file
- [too_high] `create_issue` × `payments-service` (score 20) — Score is higher than expected based on cross-asset context
- [too_high] `create_pull_request` × `payments-service` (score 20) — Score is higher than expected based on cross-asset context
- [too_high] `fork_repository` × `infra-config` (score 40) — Score is too high compared to similar tools with the same impact
- [too_low] `create_issue` × `public-website` (score 4) — Should be higher than get_file_contents due to write impact, but lower than create_or_update_file
- [too_low] `create_pull_request` × `public-website` (score 4) — Should be higher than get_file_contents due to write impact, but lower than create_or_update_file
- [too_low] `fork_repository` × `public-website` (score 4) — Should be higher given its impact on other assets
- [too_low] `create_issue` × `internal-docs` (score 12) — Should be higher given the impact and blast radius, compared to create_or_update_file
- [too_low] `create_pull_request` × `internal-docs` (score 12) — Should be higher given the impact and blast radius, compared to merge_pull_request
- [too_low] `fork_repository` × `backend-api` (score 16) — Score should be higher given the blast radius and asset sensitivity
- [too_low] `fork_repository` × `payments-service` (score 20) — Score is lower than expected based on cross-asset context
- [too_low] `create_issue` × `infra-config` (score 10) — Score should be higher given the impact and consistency across assets
- [too_low] `create_pull_request` × `infra-config` (score 20) — Score should be higher given the impact and consistency across assets
- [too_low] `fork_repository` × `ml-research` (score 16) — Score is lower than expected given the blast radius
