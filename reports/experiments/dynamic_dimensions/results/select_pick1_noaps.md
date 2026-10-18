# Greedy focus selection (pick on seed 1, check on seed 2; years 1-2; <= 2 caller-days/day)

| step | dimension added | pick seed | gain | check seed | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | order: next-step rarity | 22% | +22% | 22% | 29% | 18% | 34% | 49% | 53% | 36% | 0% | 2% | 0% | 32% | 1% | 5% |
| 2 | hour of week | 35% | +13% | 37% | 42% | 36% | 58% | 60% | 64% | 70% | 3% | 18% | 17% | 50% | 4% | 20% |
| 3 | size of each request | 45% | +11% | 48% | 42% | 67% | 66% | 63% | 71% | 73% | 3% | 29% | 17% | 50% | 8% | 90% |
| 4 | calls per hour | 53% | +8% | 50% | 52% | 69% | 63% | 56% | 69% | 73% | 3% | 57% | 11% | 49% | 10% | 90% |
| 5 | dormancy | 58% | +5% | 58% | 55% | 72% | 66% | 65% | 71% | 76% | 12% | 55% | 82% | 52% | 8% | 80% |
| 6 | learned day model | 61% | +2% | 56% | 54% | 77% | 66% | 61% | 56% | 71% | 12% | 50% | 82% | 47% | 6% | 90% |
| 7 | asset foreign to the team | 61% | +1% | 62% | 58% | 77% | 66% | 96% | 61% | 71% | 15% | 54% | 82% | 57% | 12% | 90% |
| 8 | new tool for this caller | 64% | +2% | 61% | 55% | 77% | 63% | 89% | 95% | 74% | 15% | 54% | 54% | 54% | 12% | 90% |
| 9 | items requested per day | 64% | +0% | 62% | 53% | 77% | 79% | 83% | 98% | 61% | 15% | 63% | 54% | 43% | 15% | 100% |
