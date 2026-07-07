# Deterministic (clean) vs judged (old) bands

| server | cells | band agree | within-1 | det dist (l/m/h/c) | judged dist |
| --- | --- | --- | --- | --- | --- |
| calendar_cbg | 66 | 67% | 97% | 2/25/33/6 | 6/28/21/11 |
| fs_corp_filesystem | 210 | 57% | 100% | 37/82/82/9 | 52/56/71/31 |
| fs_fintech_fs | 322 | 53% | 97% | 37/102/161/22 | 54/95/104/69 |
| fs_law_firm_fs | 308 | 58% | 100% | 23/149/124/12 | 64/112/98/34 |
| fs_media_studio_fs | 294 | 47% | 96% | 104/102/84/4 | 49/125/86/34 |
| fs_medical_clinic_fs | 294 | 57% | 99% | 19/143/117/15 | 56/87/95/56 |
| github_cbg | 66 | 48% | 95% | 10/21/26/9 | 14/13/23/16 |
| slack_cbg | 80 | 36% | 98% | 22/30/27/1 | 27/28/19/6 |
| sqlite_cbg_sqlite | 35 | 46% | 91% | 0/14/21/0 | 6/13/11/5 |
| sqlite_devops_sqlite | 25 | 56% | 84% | 4/7/12/2 | 8/5/9/3 |

**Overall:** 910/1700 exact (54%), 1658/1700 within-one-band (98%). The deterministic floors shift more cells up (irreversibility/confidentiality) while dropping the non-reproducible LLM overrides.
