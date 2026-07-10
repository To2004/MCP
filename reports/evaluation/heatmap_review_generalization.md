# Heatmap coherence review — framework-grounded LLM judge (general, no leakage)

An independent reviewer reads each cell WITH its neighbours and judges coherence (right ballpark + correct ordering), not exact numbers. The systematic patterns below are the guideline-improvement targets.

## sqlite_cbg_sqlite

- **29/35 cells coherent (83%)** · too_high 0 · too_low 6

Miscalibration by operation (pattern → guideline signal):
- `WRITE`: too_high 0, too_low 6

Flagged cells:
- [too_low] `insert_row` × `employees` (score 16) — should be higher given the blast radius and impact compared to write_query
- [too_low] `insert_row` × `projects` (score 12) — should be higher as it has the same blast radius and impact as write_query but scores lower
- [too_low] `insert_row` × `datasets` (score 12) — should be higher given the same blast radius as write_query but lower score
- [too_low] `insert_row` × `experiments` (score 12) — should be higher given the same blast radius as write_query but lower score
- [too_low] `insert_row` × `publications` (score 8) — should be higher than write_query due to blast radius difference
- [too_low] `insert_row` × `grants` (score 16) — should be higher than read_query due to write capability

## slack_cbg

- **63/80 cells coherent (79%)** · too_high 0 · too_low 17

Miscalibration by operation (pattern → guideline signal):
- `BROADCAST`: too_high 0, too_low 17

Flagged cells:
- [too_low] `slack_post_message` × `general` (score 6) — Should be higher than broadcast actions with recoverable write impact
- [too_low] `slack_post_message` × `announcements` (score 6) — Should be higher given its destructive impact, compare with slack_reply_to_thread and slack_add_reaction
- [too_low] `slack_post_message` × `random` (score 6) — Should be higher than 6 given its destructive impact and blast radius, considering cross-asset context
- [too_low] `slack_reply_to_thread` × `engineering` (score 8) — Should be higher than read-only operations given its recoverable write impact
- [too_low] `slack_add_reaction` × `engineering` (score 8) — Should be higher than read-only operations given its recoverable write impact
- [too_low] `slack_reply_to_thread` × `incident-response` (score 16) — Should be higher than read-only tools due to recoverable write impact; consider slack_post_message as a reference
- [too_low] `slack_add_reaction` × `incident-response` (score 16) — Should be higher than read-only tools due to recoverable write impact; consider slack_post_message as a reference
- [too_low] `slack_reply_to_thread` × `on-call` (score 16) — Should be higher than 16 given its blast radius and impact, similar to slack_post_message
- [too_low] `slack_add_reaction` × `on-call` (score 16) — Should be higher than 16 given its blast radius and impact, similar to slack_reply_to_thread
- [too_low] `slack_reply_to_thread` × `research-team` (score 16) — Should be higher than read-only operations given its recoverable write impact
- [too_low] `slack_add_reaction` × `research-team` (score 16) — Should be higher than read-only operations given its recoverable write impact
- [too_low] `slack_reply_to_thread` × `exec-private` (score 16) — Should be higher than read-only tools due to recoverable write impact; consider slack_post_message as a reference
- [too_low] `slack_add_reaction` × `exec-private` (score 16) — Should be higher than read-only tools due to recoverable write impact; consider slack_post_message as a reference
- [too_low] `slack_reply_to_thread` × `hr-internal` (score 16) — Should be higher than read-only operations given its recoverable write impact
- [too_low] `slack_add_reaction` × `hr-internal` (score 16) — Should be higher than read-only operations given its recoverable write impact
- [too_low] `slack_reply_to_thread` × `team-leads` (score 16) — Should be higher than 16 given its blast radius and impact, similar to slack_post_message
- [too_low] `slack_add_reaction` × `team-leads` (score 16) — Should be higher than 16 given its blast radius and impact, similar to slack_reply_to_thread

## fs_medical_clinic_fs

- **257/294 cells coherent (87%)** · too_high 3 · too_low 34

Miscalibration by operation (pattern → guideline signal):
- `CREATE`: too_high 0, too_low 14
- `READ`: too_high 0, too_low 6
- `LIST`: too_high 0, too_low 6
- `OVERWRITE`: too_high 0, too_low 5
- `MOVE`: too_high 2, too_low 1
- `SEARCH`: too_high 0, too_low 2
- `MODIFY`: too_high 1, too_low 0

Flagged cells:
- [too_high] `move_file` × `patients/alice_johnson/` (score 60) — Should be lower than 60 given the blast radius and impact compared to edit_file
- [too_high] `move_file` × `billing/` (score 48) — Should be lower than 48 given the blast radius; should match edit_file score
- [too_high] `edit_file` × `policies/` (score 48) — Score should be lower than move_file given the same blast radius and similar impact; move_file is 48
- [too_low] `read_multiple_files` × `patients/alice_johnson/intake_form.txt` (score 5) — Should be higher than 5 given its blast radius should logically exceed single item reads
- [too_low] `create_directory` × `patients/alice_johnson/intake_form.txt` (score 10) — Should be higher given the asset sensitivity of 5
- [too_low] `directory_tree` × `patients/alice_johnson/intake_form.txt` (score 5) — Should be higher given the blast radius should logically exceed single item reads
- [too_low] `read_multiple_files` × `patients/alice_johnson/medical_history.txt` (score 5) — Should be higher due to potential larger blast radius compared to single file reads
- [too_low] `create_directory` × `patients/alice_johnson/medical_history.txt` (score 10) — Should be higher due to potential larger blast radius compared to read operations
- [too_low] `directory_tree` × `patients/alice_johnson/medical_history.txt` (score 5) — Should be higher due to potential larger blast radius compared to single directory lists
- [too_low] `search_files` × `patients/alice_johnson/medical_history.txt` (score 5) — Should be higher due to potential larger blast radius compared to single file reads
- [too_low] `read_multiple_files` × `patients/alice_johnson/prescription.txt` (score 5) — Should be higher than 5 given its blast radius should logically exceed single item reads
- [too_low] `create_directory` × `patients/alice_johnson/prescription.txt` (score 10) — Should be higher given the asset sensitivity of 5
- [too_low] `directory_tree` × `patients/alice_johnson/prescription.txt` (score 5) — Should be higher given the blast radius should logically exceed single item lists
- [too_low] `read_multiple_files` × `patients/bob_martinez/intake_form.txt` (score 5) — Should be higher than 5 given its blast radius should logically exceed single item reads
- [too_low] `create_directory` × `patients/bob_martinez/intake_form.txt` (score 10) — Should be higher given the asset sensitivity and blast radius
- [too_low] `directory_tree` × `patients/bob_martinez/intake_form.txt` (score 5) — Should be higher given the potential blast radius of listing a directory tree
- [too_low] `read_multiple_files` × `patients/bob_martinez/medical_history.txt` (score 5) — Should be higher than 5 given the blast radius of multiple files, similar to write/edit/move actions
- [too_low] `create_directory` × `patients/bob_martinez/medical_history.txt` (score 10) — Should be higher than 10 given the asset sensitivity, similar to write/edit/move actions
- [too_low] `directory_tree` × `patients/bob_martinez/medical_history.txt` (score 5) — Should be higher than 5 given the blast radius, similar to read_multiple_files
- [too_low] `search_files` × `patients/bob_martinez/medical_history.txt` (score 5) — Should be higher than 5 given the blast radius, similar to read_multiple_files
- [too_low] `read_multiple_files` × `patients/bob_martinez/prescription.txt` (score 5) — Should be higher than 5 given its blast radius should logically exceed single item reads
- [too_low] `create_directory` × `patients/bob_martinez/prescription.txt` (score 10) — Should be higher given the asset sensitivity and blast radius
- [too_low] `directory_tree` × `patients/bob_martinez/prescription.txt` (score 5) — Should be higher given the blast radius likely exceeds single item lists
- [too_low] `create_directory` × `/` (score 12) — impact should be higher given its blast radius; should match edit_file/write_file scores
- [too_low] `write_file` × `patients/` (score 30) — Should be higher due to destructive impact, compare with edit_file and move_file
- [too_low] `create_directory` × `patients/` (score 20) — Should be higher due to recoverable write impact, compare with edit_file
- [too_low] `write_file` × `patients/alice_johnson/` (score 30) — Should be higher than 30 given the destructive impact and asset sensitivity
- [too_low] `create_directory` × `patients/alice_johnson/` (score 20) — Should be higher than 20 given the recoverable write impact and asset sensitivity
- [too_low] `write_file` × `patients/bob_martinez/` (score 30) — Should be higher than 30 given the impact and blast radius, compared to edit_file and move_file
- [too_low] `create_directory` × `patients/bob_martinez/` (score 20) — Should be higher than 20 given the impact and blast radius, compared to write_file and edit_file
