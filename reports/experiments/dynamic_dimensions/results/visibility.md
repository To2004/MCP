# Reading nothing vs reading only static-kept inputs (risk added per caller-day, <= 2 caller-days/day)

## month 1

| what the layer reads | mean detect | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| envelope only (who/when/tool/order, no inputs) | 24% | 50% | 35% | 0% | 33% | 100% | 0% | 0% | 25% | – | 17% | 0% | 0% |
| static-guided (envelope + kept inputs by effect) | 44% | 67% | 45% | 67% | 100% | 17% | 17% | 0% | 50% | – | 25% | 0% | 100% |

## year 1

| what the layer reads | mean detect | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| envelope only (who/when/tool/order, no inputs) | 54% | 51% | 56% | 55% | 55% | 98% | 73% | 10% | 56% | 80% | 49% | 10% | 51% |
| static-guided (envelope + kept inputs by effect) | 61% | 69% | 60% | 70% | 98% | 98% | 34% | 10% | 55% | 80% | 46% | 35% | 83% |

## year 2

| what the layer reads | mean detect | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| envelope only (who/when/tool/order, no inputs) | 59% | 62% | 45% | 75% | 76% | 100% | 86% | 11% | 62% | 72% | 41% | 10% | 66% |
| static-guided (envelope + kept inputs by effect) | 58% | 62% | 67% | 65% | 88% | 98% | 52% | 3% | 62% | 75% | 32% | 14% | 81% |

