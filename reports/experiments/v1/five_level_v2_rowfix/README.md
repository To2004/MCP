# Experiment `rowfix` — per-asset row-consistency repair

Baseline: `five_level_v2_fs`. One LLM audit per asset row; only inconsistent cells' blast repaired (guardrailed, minimum-change).

| server | rows audited | rows failed | cells repaired | low | medium | high | critical | na |
|---|---|---|---|---|---|---|---|---|
| calendar:real | 16 | 0 | 8 | 4 | 15 | 52 | 5 | 132 |
| slack:real | 19 | 0 | 26 | 8 | 45 | 51 | 12 | 188 |
| fs:corp | 22 | 0 | 26 | 14 | 67 | 82 | 24 | 121 |
