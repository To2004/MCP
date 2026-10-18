# Greedy focus selection (pick on seed 2, check on seed 1; years 1-2; <= 2 caller-days/day)

| step | dimension added | pick seed | gain | check seed | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | order: next-step rarity | 22% | +22% | 22% | 15% | 5% | 36% | 54% | 59% | 45% | 0% | 4% | 0% | 35% | 0% | 9% |
| 2 | hour of week | 37% | +15% | 35% | 30% | 16% | 64% | 56% | 74% | 74% | 8% | 17% | 23% | 35% | 10% | 9% |
| 3 | size of each request | 48% | +11% | 45% | 30% | 65% | 64% | 58% | 77% | 74% | 8% | 19% | 23% | 35% | 16% | 75% |
| 4 | dormancy | 53% | +5% | 51% | 30% | 73% | 68% | 61% | 79% | 74% | 10% | 15% | 70% | 35% | 10% | 88% |
| 5 | items requested per day | 59% | +6% | 58% | 45% | 80% | 86% | 69% | 79% | 77% | 10% | 27% | 70% | 35% | 15% | 100% |
| 6 | assets per day | 62% | +3% | 60% | 45% | 80% | 86% | 78% | 82% | 77% | 13% | 33% | 70% | 40% | 21% | 100% |
| 7 | new tool for this caller | 65% | +3% | 62% | 45% | 80% | 86% | 78% | 100% | 81% | 13% | 33% | 70% | 40% | 21% | 100% |
| 8 | learned day model | 66% | +1% | 63% | 52% | 78% | 84% | 78% | 100% | 71% | 15% | 48% | 67% | 37% | 23% | 100% |
| 9 | weekly scope drift (re-anchored) | 67% | +0% | 64% | 52% | 80% | 84% | 82% | 100% | 71% | 15% | 50% | 67% | 42% | 30% | 100% |
