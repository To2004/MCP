# Evaluation ground truth

Rendered from `all_static_tables.json` by `scripts/export_eval_tables.py`.

These design-time, judge-reviewed risk tables are the **reference the scanner is graded against** (see `scripts/evaluate_scanner.py`). They are **not** an input to the scanner and must not be used for training.

| Server | Kind | Worst band | Tools | Assets | Critical cells | Judge overrides |
| --- | --- | --- | --- | --- | --- | --- |
| [cbg_sqlite](cbg_sqlite.md) | SQL database | critical | 5 | 7 | api_keys · write_query | 6 |
| [corp_filesystem](corp_filesystem.md) | filesystem | critical | 14 | 7 | .pem · write_file, .pem · edit_file, .pem · move_file | 10 |
| [corp_sqlite](corp_sqlite.md) | SQL database | critical | 5 | 6 | api_keys · write_query | 8 |
| [law_firm_fs](law_firm_fs.md) | filesystem | high | 14 | 3 | — | 5 |
| [media_studio_fs](media_studio_fs.md) | filesystem | high | 14 | 3 | — | 3 |
| [medical_clinic_fs](medical_clinic_fs.md) | filesystem | high | 14 | 4 | — | 5 |
| [slack](slack.md) | communication platform | high | 8 | 10 | — | 15 |

**Totals:** {'critical_cells': 5, 'judge_overrides': 52}
