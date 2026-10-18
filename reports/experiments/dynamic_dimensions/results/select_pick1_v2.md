# Greedy focus selection (pick on seed 1, check on seed 2; years 1-2; <= 2 caller-days/day)

| step | dimension added | pick seed | gain | check seed | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | order: next-step rarity | 16% | +16% | 19% | 10% | 20% | 22% | 62% | 58% | 48% | 0% | 5% | 0% | 8% | 0% | 0% |
| 2 | size of each request | 32% | +16% | 36% | 22% | 78% | 29% | 69% | 63% | 53% | 0% | 17% | 0% | 8% | 5% | 94% |
| 3 | first touch of an asset (self) | 40% | +8% | 42% | 22% | 73% | 29% | 100% | 68% | 53% | 0% | 22% | 6% | 25% | 16% | 89% |
| 4 | calls per hour | 45% | +5% | 49% | 32% | 78% | 29% | 100% | 68% | 56% | 0% | 67% | 6% | 25% | 22% | 100% |
| 5 | new tool for this caller | 48% | +3% | 51% | 32% | 78% | 29% | 100% | 95% | 56% | 0% | 67% | 6% | 28% | 23% | 100% |
| 6 | dormancy | 50% | +2% | 52% | 29% | 78% | 28% | 100% | 93% | 36% | 0% | 65% | 57% | 25% | 23% | 95% |
| 7 | learned day model | 51% | +1% | 54% | 31% | 78% | 29% | 100% | 95% | 36% | 0% | 72% | 57% | 28% | 30% | 95% |
| 8 | assets per day | 53% | +3% | 55% | 31% | 78% | 29% | 100% | 95% | 36% | 0% | 72% | 57% | 28% | 35% | 95% |
| 9 | items requested per day | 56% | +2% | 57% | 34% | 81% | 43% | 98% | 95% | 50% | 0% | 73% | 57% | 18% | 35% | 95% |
