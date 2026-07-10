# Heatmap coherence review — framework-grounded LLM judge (general, no leakage)

An independent reviewer reads each cell WITH its neighbours and judges coherence (right ballpark + correct ordering), not exact numbers. The systematic patterns below are the guideline-improvement targets.

## fs_corp_filesystem

- **171/210 cells coherent (81%)** · too_high 7 · too_low 32

Miscalibration by operation (pattern → guideline signal):
- `METADATA`: too_high 0, too_low 9
- `MOVE`: too_high 5, too_low 3
- `MODIFY`: too_high 2, too_low 6
- `OVERWRITE`: too_high 0, too_low 7
- `CREATE`: too_high 0, too_low 5
- `LIST`: too_high 0, too_low 2

Flagged cells:
- [too_high] `move_file` × `sensitive/` (score 60) — Score is too high compared to edit_file, despite similar impact and blast radius
- [too_high] `edit_file` × `projects/` (score 27) — Score is higher than expected given the blast radius and impact; should be lower, similar to 'create_directory'
- [too_high] `move_file` × `projects/` (score 36) — Score is higher than expected given the blast radius; should be lower, similar to 'write_file'
- [too_high] `move_file` × `sensitive/security/` (score 60) — Score is higher than expected given its blast radius and impact, should be lower than write_file
- [too_high] `move_file` × `onboarding/` (score 24) — impact is too high compared to similar write operations on this asset
- [too_high] `edit_file` × `source_code/` (score 36) — Score should be lower, consistent with write_file and move_file impacts
- [too_high] `move_file` × `source_code/` (score 48) — Score should be lower, consistent with write_file impact but higher blast radius
- [too_low] `write_file` × `README.md` (score 6) — Impact should be higher given the destructive nature; compare to edit_file.
- [too_low] `create_directory` × `README.md` (score 2) — Impact should be higher given the blast radius; compare to edit_file.
- [too_low] `move_file` × `README.md` (score 6) — Impact should be higher given the blast radius; compare to edit_file.
- [too_low] `get_file_info` × `README.md` (score 1) — Impact should be higher given the blast radius; compare to edit_file.
- [too_low] `create_directory` × `onboarding/org_chart.png` (score 4) — Should be higher given the cross-asset context and impact level
- [too_low] `move_file` × `onboarding/org_chart.png` (score 12) — Should be higher given the cross-asset context and impact level
- [too_low] `get_file_info` × `onboarding/org_chart.png` (score 2) — Should be higher given the cross-asset context for similar impact level
- [too_low] `edit_file` × `projects/db_schema.sql` (score 18) — should be higher than 18 given its impact and blast radius, similar to move_file
- [too_low] `get_file_info` × `projects/db_schema.sql` (score 3) — should be higher than 3 given its impact and blast radius, similar to list_directory_with_sizes
- [too_low] `edit_file` × `projects/known_defects.csv` (score 18) — should be higher than write_file due to potential for more complex changes; should match move_file score of 18
- [too_low] `get_file_info` × `projects/known_defects.csv` (score 3) — should be higher due to potential for revealing sensitive metadata; should match list_directory score of 3
- [too_low] `create_directory` × `sensitive/security/audit_log.txt` (score 8) — Should be higher given the sensitivity of the asset and blast radius
- [too_low] `get_file_info` × `sensitive/security/audit_log.txt` (score 4) — Should be higher given the sensitivity of the asset and blast radius
- [too_low] `write_file` × `sensitive/security/private_key.pem` (score 30) — Impact should be higher given the asset sensitivity; compare to move_file
- [too_low] `edit_file` × `sensitive/security/private_key.pem` (score 30) — Impact should be higher given the asset sensitivity; compare to move_file
- [too_low] `move_file` × `sensitive/security/private_key.pem` (score 30) — Impact should be higher given the asset sensitivity; compare to write_file
- [too_low] `write_file` × `/` (score 30) — Should be higher than 30 given its impact and blast radius, similar to move_file on this asset
- [too_low] `edit_file` × `/` (score 30) — Should be higher than 30 given its impact and blast radius, similar to move_file on this asset
- [too_low] `get_file_info` × `/` (score 20) — Should be higher than 20 given its blast radius, similar to list_directory on this asset
- [too_low] `write_file` × `sensitive/` (score 30) — Should be higher given the destructive impact; compare with edit_file on this asset
- [too_low] `create_directory` × `sensitive/` (score 20) — Should be higher given the recoverable write impact; compare with read_multiple_files on this asset
- [too_low] `list_allowed_directories` × `sensitive/` (score 10) — Should be higher given the asset sensitivity; compare with read_file on this asset
- [too_low] `get_file_info` × `projects/` (score 6) — Score is lower than expected given the blast radius; should be higher, similar to 'read_file'
