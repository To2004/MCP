# Blast-roof experiment — calendar:real

Roofs CAP blast for low-consequence cells (mirror of the floors). Applied offline to the shipped floored blast; only impact<=3 cells are ever capped (never a write/delete), and assets flagged hub/population/self-sufficient are exempt from the read cap. Bands are the pure `band_label_v5` of the resulting score.

| ruleset | rule | cells capped | low | medium | high | critical |
|---|---|---|---|---|---|---|
| none | — | 0 | 19 | 45 | 8 | 2 |
| conservative | read_cap=4, sens_caps={1: 4} | 0 | 19 | 45 | 8 | 2 |
| user | read_cap=4, sens_caps={1: 3}, combined_cap=(5, 2, 3) | 7 | 19 | 45 | 8 | 2 |
| aggressive | read_cap=4, sens_caps={1: 3, 2: 3}, combined_cap=(2, 2, 2) | 4 | 19 | 45 | 8 | 2 |

## user — capped cells

| asset | tool | sens | impact | blast | -> | band before | band after |
|---|---|:-:|:-:|:-:|:-:|---|---|
| `calendar-records` | `list-calendars` | 3 | 2 | 4→3 | | medium | medium |
| `account-directory` | `list-calendars` | 4 | 2 | 4→3 | | medium | medium |
| `holidays` | `list-events` | 1 | 3 | 4→3 | | low | low |
| `color-catalog` | `list-colors` | 1 | 2 | 4→3 | | low | low |
| `executive` | `get-freebusy` | 4 | 2 | 4→3 | | medium | medium |
| `free-busy-availability` | `get-freebusy` | 3 | 2 | 4→3 | | medium | medium |
| `calendar-directory` | `get-freebusy` | 2 | 2 | 4→3 | | low | low |

## aggressive — capped cells

| asset | tool | sens | impact | blast | -> | band before | band after |
|---|---|:-:|:-:|:-:|:-:|---|---|
| `holidays` | `list-events` | 1 | 3 | 4→3 | | low | low |
| `color-catalog` | `list-colors` | 1 | 2 | 4→2 | | low | low |
| `holidays` | `get-freebusy` | 1 | 2 | 3→2 | | low | low |
| `calendar-directory` | `get-freebusy` | 2 | 2 | 4→2 | | low | low |

