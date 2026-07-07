# Judge-agreement evaluation — how well an independent reviewer concurs with the scans

The judge (evaluation-only) re-derives each primitive skeptically and is compared to the base-model scan. High agreement = confident, stable scores; a systematic signed gap on a primitive = a prompt/rule to tighten.

## Overall (all servers)

| primitive | n | agree | mean Δ (judge−base) | mean |Δ| |
| --- | --- | --- | --- | --- |
| tool_impact | 110 | 98/110 (89.1%) | +0.09 | 0.11 |
| sensitivity | 136 | 29/136 (21.3%) | +0.32 | 0.84 |
| blast_radius | 295 | 80/295 (27.1%) | -0.47 | 1.1 |

## Per server

| server | impact agree | sensitivity agree | blast agree |
| --- | --- | --- | --- |
| fs_corp_filesystem | 14/14 (100.0%) | 3/15 (20.0%) | 10/30 (33.3%) |
| fs_fintech_fs | 13/14 (92.9%) | 7/23 (30.4%) | 11/30 (36.7%) |
| fs_law_firm_fs | 13/14 (92.9%) | 2/22 (9.1%) | 8/30 (26.7%) |
| fs_media_studio_fs | 13/14 (92.9%) | 2/21 (9.5%) | 17/30 (56.7%) |
| fs_medical_clinic_fs | 13/14 (92.9%) | 4/21 (19.0%) | 16/30 (53.3%) |
| sqlite_cbg_sqlite | 4/5 (80.0%) | 2/7 (28.6%) | 0/30 (0.0%) |
| sqlite_devops_sqlite | 4/5 (80.0%) | 2/5 (40.0%) | 3/25 (12.0%) |
| github_cbg | 9/11 (81.8%) | 5/6 (83.3%) | 8/30 (26.7%) |
| slack_cbg | 5/8 (62.5%) | 1/10 (10.0%) | 4/30 (13.3%) |
| calendar_cbg | 10/11 (90.9%) | 1/6 (16.7%) | 3/30 (10.0%) |

## Largest disagreements (where to improve)

- `blast_radius` **read_text_file|shoots/SHOOT-2026-A/**: base 4 → judge 1
- `sensitivity` **source_code/core.c**: base 4 → judge 2
- `sensitivity` **source_code/**: base 4 → judge 2
- `blast_radius` **read_file|source_code/**: base 4 → judge 2
- `blast_radius` **read_text_file|sensitive/financials/**: base 4 → judge 2
- `blast_radius` **read_media_file|onboarding/**: base 4 → judge 2
- `blast_radius` **read_multiple_files|sensitive/financials/payslips_q1.csv**: base 4 → judge 2
- `blast_radius` **read_multiple_files|sensitive/security/**: base 4 → judge 2
- `blast_radius` **list_directory|source_code/**: base 4 → judge 2
- `blast_radius` **list_directory_with_sizes|sensitive/financials/**: base 4 → judge 2
- `blast_radius` **directory_tree|sensitive/security/audit_log.txt**: base 4 → judge 2
- `blast_radius` **directory_tree|onboarding/**: base 4 → judge 2
- `blast_radius` **get_file_info|sensitive/**: base 4 → judge 2
- `blast_radius` **list_allowed_directories|/**: base 4 → judge 2
- `blast_radius` **read_file|payments/settlements/**: base 4 → judge 2
- `blast_radius` **read_text_file|customers/cust_0002/**: base 4 → judge 2
- `blast_radius` **read_media_file|customers/cust_0001/**: base 4 → judge 2
- `blast_radius` **read_multiple_files|security/audit/**: base 4 → judge 2
- `blast_radius` **list_directory|payments/card_vault/**: base 4 → judge 2
- `blast_radius` **list_directory_with_sizes|security/secrets/**: base 4 → judge 2
- `blast_radius` **directory_tree|security/**: base 4 → judge 2
- `blast_radius` **search_files|customers/cust_0002/**: base 4 → judge 2
- `blast_radius` **get_file_info|customers/cust_0001/**: base 4 → judge 2
- `blast_radius` **read_file|clients/blue_whale_inc/**: base 4 → judge 2
- `blast_radius` **read_text_file|clients/**: base 4 → judge 2
