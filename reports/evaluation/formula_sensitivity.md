# Formula sensitivity (band cut-point robustness)

`score = sensitivity × blast × impact`, banded by fixed cut-points (medium ≥ 8, high ≥ 24) plus crown-jewel rules. Each scanned cell's inputs are perturbed by ±1 (one at a time, within range); a cell is **fragile** if any such perturbation flips its band, **boundary** if its score is within 4 of a cut-point.

**Overall:** 1700 cells · stable 248/1700 (15%) · fragile 1452/1700 (85%) · boundary 1052/1700 (62%)

| Scan | cells | stable | fragile | boundary |
| --- | --- | --- | --- | --- |
| calendar_cbg | 66 | 2/66 (3%) | 64/66 (97%) | 43/66 (65%) |
| fs_corp_filesystem | 210 | 47/210 (22%) | 163/210 (78%) | 118/210 (56%) |
| fs_fintech_fs | 322 | 27/322 (8%) | 295/322 (92%) | 207/322 (64%) |
| fs_law_firm_fs | 308 | 27/308 (9%) | 281/308 (91%) | 218/308 (71%) |
| fs_media_studio_fs | 294 | 82/294 (28%) | 212/294 (72%) | 173/294 (59%) |
| fs_medical_clinic_fs | 294 | 33/294 (11%) | 261/294 (89%) | 184/294 (63%) |
| github_cbg | 66 | 10/66 (15%) | 56/66 (85%) | 31/66 (47%) |
| slack_cbg | 80 | 13/80 (16%) | 67/80 (84%) | 43/80 (54%) |
| sqlite_cbg_sqlite | 35 | 2/35 (6%) | 33/35 (94%) | 22/35 (63%) |
| sqlite_devops_sqlite | 25 | 5/25 (20%) | 20/25 (80%) | 13/25 (52%) |

## Most fragile cells (band flips under a ±1 input change)

| cell | band | score | flips to |
| --- | --- | --- | --- |
| `access_contacts × personal` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `access_contacts × team` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × /` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × billing/` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × cases/CASE-2026-001/` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × cases/CASE-2026-002/` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × clients/acme_corp/` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × clients/blue_whale_inc/` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × clients/citybank/` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × clients/neon_brand/` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × payments/` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × sensitive/financials/payslips_q1.csv` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_directory × sensitive/security/audit_log.txt` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_issue × ml-research` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `create_issue × payments-service` | medium | 8 | blast-1→low, impact+1→high, impact-1→low, sensitivity-1→low |
| `edit_file × shoots/SHOOT-2026-A/photo_001.jpg` | medium | 9 | blast-1→low, impact-1→low, sensitivity+1→high, sensitivity-1→low |
| `edit_file × shoots/SHOOT-2026-A/photo_002.jpg` | medium | 9 | blast-1→low, impact-1→low, sensitivity+1→high, sensitivity-1→low |
| `create_directory × marketing/` | medium | 8 | blast-1→low, impact-1→low, sensitivity-1→low |
| `create_directory × onboarding/` | medium | 8 | blast-1→low, impact-1→low, sensitivity-1→low |
| `create_directory × patients/alice_johnson/medical_history.txt` | low | 0 | blast+1→medium, impact+1→high, impact-1→medium |
| `create_directory × patients/alice_johnson/prescription.txt` | low | 0 | blast+1→medium, impact+1→high, impact-1→medium |
| `create_directory × patients/bob_martinez/prescription.txt` | low | 0 | blast+1→medium, impact+1→high, impact-1→medium |
| `create_directory × payments/card_vault/pan_tokens.csv` | low | 0 | blast+1→medium, impact+1→high, impact-1→medium |
| `create_directory × security/audit/` | low | 6 | blast+1→medium, impact+1→medium, sensitivity+1→medium |
| `create_directory × shoots/SHOOT-2026-B/` | medium | 18 | blast+1→high, impact+1→high, sensitivity+1→high |
