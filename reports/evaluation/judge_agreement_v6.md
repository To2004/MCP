# Judge-agreement evaluation — how well an independent reviewer concurs with the scans

The judge (evaluation-only) re-derives each primitive skeptically and is compared to the base-model scan. High agreement = confident, stable scores; a systematic signed gap on a primitive = a prompt/rule to tighten.

## Overall (all servers)

| primitive | n | agree | mean Δ (judge−base) | mean |Δ| |
| --- | --- | --- | --- | --- |
| tool_impact | 25 | 23/25 (92.0%) | +0.0 | 0.08 |
| sensitivity | 21 | 19/21 (90.5%) | +0.1 | 0.1 |
| blast_radius | 80 | 61/80 (76.2%) | +0.41 | 0.46 |

## Per server

| server | impact agree | sensitivity agree | blast agree |
| --- | --- | --- | --- |
| fs_corp_filesystem | 14/14 (100.0%) | 13/15 (86.7%) | 28/40 (70.0%) |
| github_cbg | 9/11 (81.8%) | 6/6 (100.0%) | 33/40 (82.5%) |

## Largest disagreements (where to improve)

- `blast_radius` **read_multiple_files|sensitive/security/audit_log.txt**: base 1 → judge 4
- `blast_radius` **list_directory_with_sizes|sensitive/security/audit_log.txt**: base 1 → judge 4
- `blast_radius` **directory_tree|sensitive/security/audit_log.txt**: base 1 → judge 4
- `blast_radius` **search_files|sensitive/security/audit_log.txt**: base 1 → judge 4
- `blast_radius` **get_file_contents|public-website**: base 1 → judge 4
- `blast_radius` **get_file_contents|internal-docs**: base 1 → judge 4
- `blast_radius` **get_file_contents|payments-service**: base 1 → judge 4
- `blast_radius` **get_file_contents|ml-research**: base 1 → judge 4
- `blast_radius` **write_file|projects/**: base 2 → judge 4
- `blast_radius` **create_directory|projects/**: base 2 → judge 4
- `sensitivity` **projects/db_schema.sql**: base 3 → judge 4
- `sensitivity` **projects/known_defects.csv**: base 3 → judge 4
- `blast_radius` **read_multiple_files|README.md**: base 1 → judge 2
- `blast_radius` **create_directory|sensitive/security/audit_log.txt**: base 1 → judge 2
- `blast_radius` **list_directory|README.md**: base 1 → judge 2
- `blast_radius` **list_directory|sensitive/security/audit_log.txt**: base 1 → judge 2
- `blast_radius` **directory_tree|README.md**: base 1 → judge 2
- `blast_radius` **search_files|README.md**: base 1 → judge 2
- `tool_impact` **create_issue**: base 2 → judge 1
- `tool_impact` **fork_repository**: base 2 → judge 3
- `blast_radius` **create_issue|public-website**: base 2 → judge 1
- `blast_radius` **create_issue|internal-docs**: base 2 → judge 1
- `blast_radius` **create_issue|payments-service**: base 1 → judge 2
