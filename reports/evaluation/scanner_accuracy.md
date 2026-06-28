# Scanner accuracy

Scans in `reports/scan` vs ground truth `reports/evaluation/raw/all_static_tables.json`. Higher agreement = the scanner reproduces the reviewed judgement without ever reading it.

| Server | Band agreement | Tool-impact agreement | Asset-sensitivity agreement |
| --- | --- | --- | --- |
| calendar_cbg | _no ground truth_ | — | — |
| calendar_cbg_params | _no ground truth_ | — | — |
| corp_filesystem | — | 14/14 (100%) | — |
| fs_corp_filesystem_params | _no ground truth_ | — | — |
| fs_fintech_fs | _no ground truth_ | — | — |
| fs_fintech_fs_params | _no ground truth_ | — | — |
| law_firm_fs | — | 13/14 (93%) | — |
| fs_law_firm_fs_params | _no ground truth_ | — | — |
| media_studio_fs | — | 14/14 (100%) | — |
| fs_media_studio_fs_params | _no ground truth_ | — | — |
| medical_clinic_fs | — | 13/14 (93%) | — |
| fs_medical_clinic_fs_params | _no ground truth_ | — | — |
| github_cbg | _no ground truth_ | — | — |
| github_cbg_params | _no ground truth_ | — | — |
| slack_cbg | _no ground truth_ | — | — |
| slack_cbg_params | _no ground truth_ | — | — |
| cbg_sqlite | 12/35 (34%) | 5/5 (100%) | 5/7 (71%) |
| sqlite_cbg_sqlite_params | _no ground truth_ | — | — |
| sqlite_devops_sqlite | _no ground truth_ | — | — |
| sqlite_devops_sqlite_params | _no ground truth_ | — | — |
| **overall** | **12/35 (34%)** | **59/61 (97%)** | **5/7 (71%)** |
