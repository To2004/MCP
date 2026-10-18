# Greedy focus selection (pick on seed 2, check on seed 1; years 1-2; <= 2 caller-days/day)

| step | dimension added | pick seed | gain | check seed | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | order: next-step rarity | 19% | +19% | 16% | 4% | 12% | 18% | 53% | 58% | 38% | 0% | 5% | 0% | 0% | 2% | 0% |
| 2 | size of each request | 36% | +17% | 32% | 17% | 70% | 26% | 58% | 60% | 43% | 0% | 7% | 0% | 0% | 12% | 90% |
| 3 | calls per hour | 43% | +6% | 38% | 34% | 77% | 26% | 66% | 60% | 46% | 0% | 43% | 0% | 0% | 13% | 90% |
| 4 | first touch of an asset (self) | 49% | +6% | 45% | 32% | 75% | 23% | 100% | 63% | 48% | 0% | 55% | 0% | 16% | 34% | 90% |
| 5 | items requested per day | 51% | +3% | 45% | 34% | 80% | 35% | 100% | 44% | 39% | 0% | 60% | 0% | 21% | 36% | 90% |
| 6 | new tool for this caller | 54% | +3% | 48% | 34% | 77% | 35% | 100% | 88% | 44% | 0% | 57% | 0% | 20% | 29% | 90% |
| 7 | learned day model | 56% | +2% | 50% | 49% | 80% | 37% | 100% | 90% | 44% | 0% | 60% | 3% | 20% | 32% | 90% |
| 8 | dormancy | 56% | +0% | 53% | 45% | 77% | 45% | 89% | 90% | 50% | 2% | 66% | 43% | 13% | 27% | 95% |
| 9 | consequence added up over the day | 58% | +2% | 55% | 49% | 77% | 45% | 89% | 90% | 50% | 2% | 66% | 43% | 19% | 34% | 95% |
