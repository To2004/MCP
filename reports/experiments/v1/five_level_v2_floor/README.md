# Experiment `blast_floor` — sensitivity-coupled minimum blast

Floors: sensitivity 5 -> blast >= 4; sensitivity 4 -> blast >= 3. `plain` floors every scored cell; `gated` floors only mutating tools (impact >= 4). Baseline: `five_level_v2_fs`.

| server | variant | cells raised | low | medium | high | critical | na |
|---|---|---|---|---|---|---|---|
| calendar:real | plain | 39 | 5 | 5 | 57 | 9 | 132 |
| calendar:real | gated | 16 | 5 | 9 | 57 | 5 | 132 |
| slack:real | plain | 41 | 15 | 22 | 63 | 16 | 188 |
| slack:real | gated | 21 | 15 | 35 | 51 | 15 | 188 |
| fs:corp | plain | 64 | 14 | 40 | 108 | 25 | 121 |
| fs:corp | gated | 17 | 14 | 59 | 92 | 22 | 121 |
