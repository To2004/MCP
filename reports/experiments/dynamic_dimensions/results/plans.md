# The three plans at equal analyst load

Load = alerted caller-days per day. Detection = share of strange-usage episodes caught, averaged over seeds. Policy-rule hits always alert.

## month 1 (new deployment)

| plan | load target | load | mean detect | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 guardrails + counters | <= 1 | – | unreachable | – | – | – | – | – | – | – | – | – | – | – | – |
| P1 guardrails + counters | <= 2 | 1.5 | 38% | 67% | 45% | 0% | 0% | 83% | 100% | 0% | 25% | – | 0% | 0% | 100% |
| P1 guardrails + counters | <= 4 | 3.0 | 51% | 67% | 65% | 67% | 0% | 83% | 100% | 0% | 75% | – | 0% | 8% | 100% |
| P2 per-call baselines | <= 1 | – | unreachable | – | – | – | – | – | – | – | – | – | – | – | – |
| P2 per-call baselines | <= 2 | – | unreachable | – | – | – | – | – | – | – | – | – | – | – | – |
| P2 per-call baselines | <= 4 | 3.5 | 57% | 67% | 45% | 100% | 67% | 83% | 100% | 0% | 25% | – | 42% | 0% | 100% |
| P3 risk events -> caller-day | <= 1 | 0.9 | 30% | 17% | 35% | 0% | 67% | 83% | 100% | 0% | 25% | – | 0% | 8% | 0% |
| P3 risk events -> caller-day | <= 2 | 1.8 | 56% | 67% | 45% | 67% | 100% | 83% | 100% | 0% | 50% | – | 0% | 8% | 100% |
| P3 risk events -> caller-day | <= 4 | 3.3 | 66% | 100% | 55% | 83% | 100% | 83% | 100% | 0% | 50% | – | 42% | 17% | 100% |

## months 2-2.5 (new deployment)

| plan | load target | load | mean detect | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 guardrails + counters | <= 1 | 0.9 | 24% | 20% | 17% | 17% | 0% | 80% | 100% | 0% | 17% | 0% | 0% | 0% | 42% |
| P1 guardrails + counters | <= 2 | 1.9 | 38% | 40% | 58% | 44% | 0% | 80% | 100% | 0% | 50% | 0% | 0% | 0% | 83% |
| P1 guardrails + counters | <= 4 | 2.8 | 47% | 60% | 92% | 66% | 0% | 80% | 100% | 0% | 58% | 0% | 0% | 3% | 100% |
| P2 per-call baselines | <= 1 | 1.0 | 30% | 20% | 33% | 29% | 20% | 80% | 100% | 0% | 0% | 0% | 0% | 0% | 75% |
| P2 per-call baselines | <= 2 | 1.8 | 39% | 20% | 58% | 51% | 45% | 80% | 100% | 0% | 8% | 0% | 20% | 0% | 83% |
| P2 per-call baselines | <= 4 | 3.5 | 57% | 50% | 92% | 73% | 94% | 90% | 100% | 0% | 42% | 0% | 55% | 4% | 83% |
| P3 risk events -> caller-day | <= 1 | 0.8 | 36% | 40% | 42% | 17% | 74% | 80% | 100% | 0% | 17% | 0% | 0% | 0% | 58% |
| P3 risk events -> caller-day | <= 2 | 2.0 | 59% | 80% | 67% | 63% | 100% | 90% | 100% | 12% | 50% | 0% | 57% | 7% | 83% |
| P3 risk events -> caller-day | <= 4 | 3.5 | 65% | 90% | 75% | 83% | 100% | 90% | 100% | 25% | 58% | 0% | 67% | 7% | 83% |

## year 1 (after month 1)

| plan | load target | load | mean detect | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 guardrails + counters | <= 1 | 0.7 | 31% | 36% | 37% | 34% | 6% | 88% | 100% | 7% | 23% | 6% | 3% | 4% | 25% |
| P1 guardrails + counters | <= 2 | 1.8 | 51% | 57% | 67% | 60% | 15% | 96% | 100% | 10% | 50% | 41% | 12% | 11% | 88% |
| P1 guardrails + counters | <= 4 | 3.5 | 62% | 78% | 97% | 77% | 19% | 98% | 100% | 14% | 67% | 47% | 15% | 28% | 100% |
| P2 per-call baselines | <= 1 | 0.6 | 38% | 24% | 37% | 20% | 36% | 88% | 100% | 0% | 24% | 74% | 23% | 1% | 22% |
| P2 per-call baselines | <= 2 | 1.4 | 51% | 52% | 51% | 46% | 57% | 98% | 100% | 7% | 36% | 80% | 34% | 6% | 44% |
| P2 per-call baselines | <= 4 | 3.9 | 80% | 88% | 86% | 83% | 94% | 98% | 100% | 26% | 66% | 90% | 86% | 40% | 100% |
| P3 risk events -> caller-day | <= 1 | 0.8 | 49% | 54% | 49% | 43% | 66% | 93% | 100% | 2% | 49% | 52% | 26% | 7% | 51% |
| P3 risk events -> caller-day | <= 2 | 1.5 | 63% | 75% | 67% | 77% | 81% | 98% | 100% | 5% | 60% | 58% | 29% | 19% | 88% |
| P3 risk events -> caller-day | <= 4 | 3.6 | 79% | 90% | 78% | 89% | 98% | 98% | 100% | 21% | 78% | 80% | 74% | 45% | 100% |

## year 2

| plan | load target | load | mean detect | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 guardrails + counters | <= 1 | 0.5 | 27% | 21% | 31% | 9% | 3% | 100% | 100% | 0% | 17% | 5% | 0% | 1% | 34% |
| P1 guardrails + counters | <= 2 | 1.9 | 47% | 74% | 72% | 56% | 9% | 100% | 100% | 3% | 50% | 17% | 2% | 3% | 76% |
| P1 guardrails + counters | <= 4 | 2.8 | 52% | 84% | 83% | 74% | 15% | 100% | 100% | 3% | 59% | 17% | 2% | 6% | 86% |
| P2 per-call baselines | <= 1 | 0.7 | 37% | 24% | 41% | 28% | 30% | 100% | 100% | 0% | 13% | 61% | 10% | 1% | 43% |
| P2 per-call baselines | <= 2 | 1.6 | 54% | 60% | 62% | 52% | 58% | 100% | 100% | 0% | 53% | 72% | 22% | 4% | 66% |
| P2 per-call baselines | <= 4 | 2.9 | 65% | 74% | 76% | 83% | 91% | 100% | 100% | 3% | 57% | 72% | 44% | 6% | 76% |
| P3 risk events -> caller-day | <= 1 | 0.8 | 49% | 39% | 55% | 59% | 67% | 100% | 100% | 0% | 38% | 33% | 10% | 7% | 85% |
| P3 risk events -> caller-day | <= 2 | 2.0 | 66% | 69% | 74% | 80% | 79% | 100% | 100% | 6% | 66% | 71% | 36% | 14% | 95% |
| P3 risk events -> caller-day | <= 4 | 3.7 | 77% | 92% | 78% | 92% | 100% | 100% | 100% | 16% | 75% | 72% | 66% | 29% | 100% |

