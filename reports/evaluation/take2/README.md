# Evaluation ground truth

Rendered from `all_static_tables_take2.json` by `scripts/export_eval_tables.py`.

These design-time, judge-reviewed risk tables are the **reference the scanner is graded against** (see `scripts/evaluate_scanner.py`). They are **not** an input to the scanner and must not be used for training.

| Server | Kind | Worst band | Tools | Assets | Critical cells | Judge overrides |
| --- | --- | --- | --- | --- | --- | --- |
| [cbg_sqlite](cbg_sqlite.md) | SQL database | critical | 5 | 7 | api_keys · write_query | 6 |
| [corp_filesystem](corp_filesystem.md) | filesystem | critical | 14 | 8 | sensitive/security/private_key.pem · write_file, sensitive/security/private_key.pem · edit_file | 16 |
| [corp_sqlite](corp_sqlite.md) | SQL database | critical | 5 | 6 | api_keys · write_query | 8 |
| [law_firm_fs](law_firm_fs.md) | filesystem | high | 14 | 12 | — | 33 |
| [media_studio_fs](media_studio_fs.md) | filesystem | high | 14 | 13 | — | 39 |
| [medical_clinic_fs](medical_clinic_fs.md) | filesystem | critical | 14 | 13 | billing/invoices/inv_2026-05-20_alice_johnson.txt · write_file, billing/invoices/inv_2026-05-20_alice_johnson.txt · edit_file, billing/invoices/inv_2026-05-20_alice_johnson.txt · move_file, patients/alice_johnson/medical_history.txt · write_file, patients/alice_johnson/medical_history.txt · edit_file, patients/alice_johnson/medical_history.txt · move_file, patients/bob_martinez/medical_history.txt · write_file, patients/bob_martinez/medical_history.txt · edit_file, patients/bob_martinez/medical_history.txt · move_file | 37 |
| [slack](slack.md) | communication platform | high | 8 | 10 | — | 15 |

**Totals:** {'critical_cells': 13, 'judge_overrides': 154}
