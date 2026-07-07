# Judge-agreement evaluation — how well an independent reviewer concurs with the scans

The judge (evaluation-only) re-derives each primitive skeptically and is compared to the base-model scan. High agreement = confident, stable scores; a systematic signed gap on a primitive = a prompt/rule to tighten.

## Overall (all servers)

| primitive | n | agree | mean Δ (judge−base) | mean |Δ| |
| --- | --- | --- | --- | --- |
| tool_impact | 25 | 23/25 (92.0%) | +0.0 | 0.08 |
| sensitivity | 21 | 19/21 (90.5%) | +0.1 | 0.1 |
| blast_radius | 80 | 54/80 (67.5%) | +0.14 | 0.36 |

## Per server

| server | impact agree | sensitivity agree | blast agree |
| --- | --- | --- | --- |
| fs_corp_filesystem | 14/14 (100.0%) | 13/15 (86.7%) | 25/40 (62.5%) |
| github_cbg | 9/11 (81.8%) | 6/6 (100.0%) | 29/40 (72.5%) |

## Largest disagreements (where to improve)

- `blast_radius` **read_file|projects/**: base 4 → judge 1
- `blast_radius` **read_media_file|projects/**: base 4 → judge 2
- `sensitivity` **projects/db_schema.sql**: base 3 → judge 4
- `sensitivity` **projects/known_defects.csv**: base 3 → judge 4
- `blast_radius` **read_multiple_files|README.md**: base 1 → judge 2
- `blast_radius` **read_multiple_files|sensitive/security/audit_log.txt**: base 1 → judge 2
- `blast_radius` **write_file|projects/**: base 3 → judge 4
- `blast_radius` **edit_file|projects/**: base 3 → judge 4
- `blast_radius` **create_directory|sensitive/security/audit_log.txt**: base 1 → judge 2
- `blast_radius` **create_directory|projects/**: base 2 → judge 3
- `blast_radius` **list_directory|sensitive/security/audit_log.txt**: base 1 → judge 2
- `blast_radius` **list_directory_with_sizes|README.md**: base 1 → judge 2
- `blast_radius` **list_directory_with_sizes|sensitive/security/audit_log.txt**: base 1 → judge 2
- `blast_radius` **directory_tree|sensitive/security/audit_log.txt**: base 1 → judge 2
- `blast_radius` **move_file|projects/**: base 4 → judge 5
- `blast_radius` **search_files|README.md**: base 1 → judge 2
- `blast_radius` **search_files|sensitive/security/audit_log.txt**: base 1 → judge 2
- `tool_impact` **create_issue**: base 2 → judge 1
- `tool_impact` **fork_repository**: base 2 → judge 3
- `blast_radius` **get_file_contents|payments-service**: base 1 → judge 2
- `blast_radius` **get_file_contents|infra-config**: base 2 → judge 1
- `blast_radius` **get_file_contents|ml-research**: base 1 → judge 2
- `blast_radius` **get_issue|infra-config**: base 2 → judge 3
- `blast_radius` **create_issue|public-website**: base 2 → judge 1
- `blast_radius` **create_issue|internal-docs**: base 2 → judge 1
