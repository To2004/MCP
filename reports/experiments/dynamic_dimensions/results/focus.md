# Three topics to focus on, at <= 2 alerted caller-days per day (no rules)

## month 1 of a new deployment

| focus | load | mean detect | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A volume, short time | 1.6 | 32% | 50% | 65% | 83% | 0% | 0% | 0% | 0% | 50% | – | 0% | 0% | 100% |
| B what is touched, vs peers | 1.8 | 15% | 0% | 0% | 0% | 100% | 0% | 0% | 0% | 0% | – | 50% | 17% | 0% |
| C order and time | – | unreachable | – | – | – | – | – | – | – | – | – | – | – | – |
| A+B | 1.9 | 35% | 50% | 55% | 83% | 67% | 0% | 0% | 0% | 25% | – | 0% | 8% | 100% |
| A+C | – | unreachable | – | – | – | – | – | – | – | – | – | – | – | – |
| B+C | – | unreachable | – | – | – | – | – | – | – | – | – | – | – | – |
| A+B+C | – | unreachable | – | – | – | – | – | – | – | – | – | – | – | – |

## year 1

| focus | load | mean detect | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A volume, short time | 1.4 | 30% | 68% | 84% | 58% | 2% | 0% | 0% | 0% | 53% | 0% | 6% | 7% | 88% |
| B what is touched, vs peers | 1.5 | 15% | 0% | 0% | 0% | 89% | 3% | 0% | 0% | 11% | 10% | 17% | 43% | 7% |
| C order and time | 1.6 | 53% | 39% | 27% | 61% | 68% | 98% | 75% | 21% | 5% | 90% | 74% | 11% | 61% |
| A+B | 1.4 | 32% | 54% | 75% | 49% | 70% | 0% | 0% | 0% | 48% | 0% | 6% | 22% | 59% |
| A+C | 1.1 | 43% | 52% | 51% | 46% | 42% | 98% | 25% | 7% | 31% | 80% | 34% | 3% | 44% |
| B+C | 1.8 | 50% | 30% | 21% | 55% | 87% | 98% | 57% | 12% | 9% | 90% | 66% | 26% | 54% |
| A+B+C | 1.4 | 46% | 52% | 51% | 46% | 70% | 98% | 25% | 7% | 33% | 80% | 34% | 11% | 44% |

## year 2

| focus | load | mean detect | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A volume, short time | 1.6 | 31% | 84% | 81% | 63% | 3% | 0% | 0% | 0% | 55% | 0% | 2% | 2% | 76% |
| B what is touched, vs peers | 1.5 | 11% | 0% | 0% | 0% | 85% | 0% | 0% | 0% | 12% | 0% | 15% | 10% | 5% |
| C order and time | 1.4 | 47% | 46% | 12% | 75% | 85% | 98% | 67% | 3% | 12% | 72% | 39% | 5% | 56% |
| A+B | 1.8 | 33% | 69% | 74% | 51% | 82% | 0% | 0% | 0% | 50% | 0% | 7% | 3% | 63% |
| A+C | 1.2 | 48% | 60% | 62% | 52% | 46% | 98% | 43% | 0% | 50% | 72% | 22% | 3% | 66% |
| B+C | 1.2 | 40% | 34% | 12% | 39% | 85% | 98% | 43% | 0% | 8% | 72% | 22% | 6% | 56% |
| A+B+C | 1.6 | 51% | 60% | 62% | 52% | 85% | 98% | 43% | 0% | 53% | 72% | 22% | 6% | 66% |

