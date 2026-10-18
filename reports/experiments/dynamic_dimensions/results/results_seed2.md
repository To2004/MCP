# Dynamic dimensions — seed 2, per-dimension budget 0.5%

## E1 — which dimension catches which strange usage (W=90, default references)

| dimension | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit | benign | alerts/day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rep.hier | 98% | 0% | 18% | 0% | 0% | 0% | 2% | 57% | 0% | 5% | 11% | 0% | 0.35% | 5.0 |
| rate.hier | 30% | 35% | 0% | 2% | 0% | 0% | 0% | 55% | 0% | 0% | 2% | 35% | 0.27% | 4.0 |
| reach.hier | 15% | 50% | 75% | 0% | 0% | 0% | 2% | 25% | 0% | 0% | 3% | 85% | 0.17% | 2.9 |
| breadth.hier | 0% | 0% | 2% | 60% | 0% | 0% | 0% | 8% | 0% | 0% | 7% | 0% | 0.19% | 2.7 |
| asset.hier | 0% | 0% | 0% | 98% | 0% | 0% | 0% | 20% | 0% | 42% | 67% | 0% | 0.25% | 3.5 |
| sensjump.self | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 2% | 0% | 0% | 0.00% | 0.0 |
| tool.hier | 0% | 2% | 2% | 2% | 95% | 5% | 2% | 0% | 0% | 2% | 0% | 20% | 0.00% | 0.1 |
| order_rule.policy | 0% | 0% | 0% | 0% | 78% | 100% | 0% | 5% | 5% | 0% | 0% | 0% | 0.01% | 0.2 |
| order_tr.hier | 72% | 42% | 70% | 85% | 98% | 100% | 0% | 30% | 0% | 72% | 15% | 15% | 0.42% | 6.0 |
| time_cal.hier | 35% | 30% | 50% | 30% | 28% | 48% | 55% | 48% | 25% | 38% | 13% | 65% | 0.46% | 6.1 |
| dormancy.hier | 5% | 2% | 0% | 5% | 0% | 0% | 10% | 5% | 80% | 2% | 3% | 40% | 0.04% | 0.6 |
| size.hier | 2% | 95% | 38% | 5% | 5% | 0% | 0% | 8% | 0% | 5% | 11% | 90% | 0.28% | 5.0 |

## E2 — compared with whom (W=90)

| dimension.reference | mean detect | ordinary FP | new_hire | role_change | team_transfer | new_repo | back_from_vacation | oncall_incident | legit_drift |
|---|---|---|---|---|---|---|---|---|---|
| rep.self | 16% | 0.35% | 0% | 0% | 0% | 1% | 0% | 2% | 0% |
| rep.peer | 16% | 0.36% | 0% | 0% | 0% | 1% | 0% | 2% | 0% |
| rep.org | 14% | 0.27% | 1% | 1% | 1% | 0% | 1% | 0% | 0% |
| rep.hier | 16% | 0.34% | 0% | 0% | 0% | 1% | 0% | 2% | 0% |
| rate.self | 13% | 0.26% | 0% | 0% | 0% | 0% | 0% | 5% | 0% |
| rate.peer | 13% | 0.23% | 0% | 1% | 0% | 0% | 0% | 2% | 0% |
| rate.org | 9% | 0.26% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| rate.hier | 13% | 0.26% | 0% | 0% | 0% | 0% | 0% | 4% | 0% |
| reach.self | 23% | 0.19% | 0% | 0% | 0% | 0% | 0% | 2% | 0% |
| reach.peer | 16% | 0.14% | 0% | 0% | 0% | 0% | 1% | 1% | 0% |
| reach.org | 8% | 0.13% | 0% | 0% | 0% | 0% | 0% | 1% | 0% |
| reach.hier | 21% | 0.16% | 0% | 0% | 0% | 0% | 0% | 1% | 0% |
| breadth.self | 8% | 0.21% | 0% | 0% | 1% | 0% | 0% | 1% | 1% |
| breadth.peer | 6% | 0.17% | 0% | 1% | 0% | 0% | 0% | 0% | 1% |
| breadth.org | 3% | 0.13% | 0% | 0% | 0% | 0% | 0% | 0% | 1% |
| breadth.hier | 6% | 0.19% | 0% | 0% | 0% | 0% | 0% | 0% | 1% |
| asset.self | 19% | 0.22% | 2% | 0% | 1% | 1% | 1% | 0% | 0% |
| asset.peer | 10% | 0.23% | 0% | 0% | 0% | 2% | 0% | 0% | 3% |
| asset.org | 9% | 0.01% | 0% | 0% | 0% | 4% | 0% | 0% | 2% |
| asset.hier | 19% | 0.21% | 1% | 0% | 1% | 1% | 1% | 0% | 0% |
| asset.anchor | 8% | 0.23% | 0% | 0% | 0% | 2% | 0% | 0% | 4% |
| tool.self | 17% | 0.01% | 1% | 1% | 0% | 0% | 0% | 1% | 0% |
| tool.peer | 11% | 0.00% | 0% | 0% | 0% | 0% | 0% | 6% | 0% |
| tool.org | 7% | 0.32% | 0% | 4% | 0% | 0% | 1% | 0% | 0% |
| tool.hier | 11% | 0.00% | 0% | 0% | 0% | 0% | 0% | 1% | 0% |
| order_tr.self | 52% | 0.37% | 0% | 3% | 1% | 1% | 1% | 13% | 0% |
| order_tr.peer | 51% | 0.33% | 1% | 1% | 1% | 1% | 1% | 17% | 0% |
| order_tr.org | 26% | 0.38% | 1% | 2% | 1% | 0% | 1% | 15% | 0% |
| order_tr.hier | 50% | 0.37% | 0% | 2% | 1% | 1% | 1% | 14% | 0% |
| time.self | 30% | 0.48% | 0% | 1% | 0% | 1% | 0% | 2% | 0% |
| time.peer | 32% | 0.32% | 1% | 3% | 1% | 1% | 1% | 7% | 0% |
| time.org | 1% | 0.25% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| time.hier | 36% | 0.46% | 0% | 0% | 1% | 1% | 0% | 2% | 0% |
| dormancy.self | 9% | 0.04% | 0% | 0% | 0% | 0% | 2% | 0% | 0% |
| dormancy.peer | 13% | 0.03% | 0% | 0% | 0% | 0% | 2% | 0% | 0% |
| dormancy.org | 13% | 0.03% | 0% | 0% | 0% | 0% | 2% | 0% | 0% |
| dormancy.hier | 13% | 0.03% | 0% | 0% | 0% | 0% | 2% | 0% | 0% |
| size.self | 24% | 0.31% | 0% | 1% | 0% | 0% | 0% | 1% | 0% |
| size.peer | 20% | 0.22% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| size.org | 19% | 0.14% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| size.hier | 22% | 0.28% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |

## E3 — window length and anchoring

| score (window) | creep | habit | fanout | legit_drift FP | transfer FP | new_repo FP | ordinary FP |
|---|---|---|---|---|---|---|---|
| asset.hier (W=30) | 75% | 0% | 98% | 0% | 1% | 1% | 0.36% |
| asset.peer (W=30) | 35% | 0% | 85% | 5% | 0% | 1% | 0.25% |
| asset.anchor (W=30) | 35% | 0% | 72% | 5% | 1% | 1% | 0.26% |
| reach.self (W=30) | 5% | 90% | 8% | 0% | 1% | 0% | 0.23% |
| reach.peer (W=30) | 0% | 65% | 0% | 0% | 0% | 0% | 0.14% |
| reach.hier (W=30) | 2% | 75% | 0% | 0% | 0% | 0% | 0.18% |
| asset.hier (W=90) | 67% | 0% | 98% | 0% | 1% | 1% | 0.21% |
| asset.peer (W=90) | 14% | 0% | 90% | 3% | 0% | 2% | 0.23% |
| asset.anchor (W=90) | 15% | 0% | 75% | 4% | 0% | 2% | 0.23% |
| reach.self (W=90) | 5% | 85% | 5% | 0% | 0% | 0% | 0.19% |
| reach.peer (W=90) | 0% | 70% | 0% | 0% | 0% | 0% | 0.14% |
| reach.hier (W=90) | 3% | 85% | 0% | 0% | 0% | 0% | 0.16% |
| asset.hier (W=life) | 38% | 0% | 95% | 0% | 0% | 1% | 0.11% |
| asset.peer (W=life) | 12% | 0% | 90% | 2% | 0% | 2% | 0.22% |
| asset.anchor (W=life) | 11% | 0% | 75% | 2% | 0% | 2% | 0.21% |
| reach.self (W=life) | 3% | 80% | 2% | 0% | 0% | 0% | 0.16% |
| reach.peer (W=life) | 0% | 70% | 0% | 0% | 0% | 0% | 0.13% |
| reach.hier (W=life) | 2% | 75% | 0% | 0% | 0% | 0% | 0.15% |

## E3b — self-normalisation of a weekly habit (W=90)

| score | wk1 | wk2 | wk3 | wk5 | wk9 | wk13 |
|---|---|---|---|---|---|---|
| reach.self | 14% | 8% | 1% | 1% | 0% | 0% |
| reach.peer | 14% | 7% | 2% | 0% | 0% | 4% |
| reach.hier | 12% | 5% | 0% | 0% | 0% | 0% |
| size.self | 36% | 17% | 11% | 8% | 7% | 9% |
| size.peer | 35% | 35% | 33% | 30% | 20% | 19% |
| size.hier | 34% | 31% | 25% | 15% | 8% | 9% |

## E4/E5 — combined detector over time (total budget 1.0%, W=90)

| combination | horizon | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit | benign | sessions/day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OR (budget split) | month 1 | 100% | 100% | 100% | – | – | 100% | 0% | – | – | 0% | – | – | 0.62% | 6.5 |
| OR (budget split) | year 1 | 82% | 84% | 79% | 87% | 96% | 100% | 10% | 59% | 100% | 82% | 17% | 100% | 0.31% | 3.6 |
| OR (budget split) | year 2 | 95% | 80% | 89% | 100% | 100% | 100% | 17% | 64% | 64% | 62% | 9% | 80% | 0.35% | 4.7 |
| SUM of bits | month 1 | 100% | 0% | 100% | – | – | 100% | 0% | – | – | 0% | – | – | 0.41% | 3.7 |
| SUM of bits | year 1 | 76% | 68% | 79% | 74% | 70% | 50% | 0% | 62% | 11% | 29% | 19% | 90% | 0.42% | 3.6 |
| SUM of bits | year 2 | 82% | 80% | 95% | 76% | 94% | 30% | 0% | 82% | 0% | 24% | 16% | 100% | 0.48% | 4.7 |
| MAX of ranks | month 1 | 100% | 100% | 100% | – | – | 100% | 0% | – | – | 0% | – | – | 1.10% | 10.9 |
| MAX of ranks | year 1 | 82% | 84% | 79% | 91% | 96% | 94% | 24% | 52% | 100% | 82% | 21% | 100% | 0.51% | 4.4 |
| MAX of ranks | year 2 | 95% | 80% | 89% | 100% | 100% | 100% | 11% | 64% | 64% | 67% | 16% | 80% | 0.56% | 5.9 |

## E5b — weighting strangeness by consequence (budget 1.0%, W=90)

| strangeness + lambda*log2(impact*sens) | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit | alerts on high-consequence calls | benign |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lambda=0.0 | 95% | 65% | 82% | 70% | 88% | 95% | 5% | 68% | 15% | 15% | 9% | 75% | 2% | 0.52% |
| lambda=0.5 | 95% | 55% | 78% | 68% | 92% | 98% | 2% | 70% | 10% | 25% | 9% | 70% | 3% | 0.54% |
| lambda=1.0 | 92% | 52% | 75% | 62% | 90% | 100% | 2% | 72% | 5% | 28% | 9% | 65% | 4% | 0.56% |

## E7 — the three plans at the same budget (1.0% of calls; P3: top 3% caller-days)

| plan | horizon | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit | benign calls flagged | caller-days flagged / day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 rules + counters | month 1 | 100% | 0% | 100% | – | – | 100% | 0% | – | – | 0% | – | – | 0.77% | 4.0 |
| P1 rules + counters | year 1 | 94% | 63% | 74% | 13% | 96% | 94% | 24% | 72% | 33% | 24% | 14% | 90% | 0.56% | 3.1 |
| P1 rules + counters | year 2 | 100% | 70% | 84% | 12% | 100% | 100% | 6% | 73% | 27% | 5% | 6% | 90% | 0.57% | 3.6 |
| P2 all dimensions, hierarchy | month 1 | 100% | 100% | 100% | – | – | 100% | 0% | – | – | 0% | – | – | 1.10% | 4.7 |
| P2 all dimensions, hierarchy | year 1 | 82% | 84% | 79% | 91% | 96% | 94% | 24% | 52% | 100% | 82% | 21% | 100% | 0.51% | 3.4 |
| P2 all dimensions, hierarchy | year 2 | 95% | 80% | 89% | 100% | 100% | 100% | 11% | 64% | 64% | 67% | 16% | 80% | 0.56% | 4.5 |
| P3 caller-day risk (RBA) | month 1 | 0% | 0% | 0% | – | – | 0% | 0% | – | – | 0% | – | – | 4.00% | 0.2 |
| P3 caller-day risk (RBA) | year 1 | 41% | 37% | 53% | 48% | 39% | 17% | 0% | 55% | 0% | 0% | 29% | 60% | 7.64% | 0.7 |
| P3 caller-day risk (RBA) | year 2 | 50% | 55% | 53% | 59% | 65% | 35% | 0% | 64% | 0% | 19% | 16% | 70% | 7.58% | 0.9 |
| P3b caller-day risk, >=2 dimensions | month 1 | 0% | 0% | 0% | – | – | 0% | 0% | – | – | 0% | – | – | 4.00% | 0.2 |
| P3b caller-day risk, >=2 dimensions | year 1 | 41% | 37% | 53% | 48% | 39% | 17% | 0% | 55% | 0% | 0% | 29% | 60% | 7.64% | 0.7 |
| P3b caller-day risk, >=2 dimensions | year 2 | 50% | 55% | 53% | 59% | 65% | 35% | 0% | 64% | 0% | 19% | 16% | 70% | 7.58% | 0.9 |


## E6 — holiday calendar (time dimension, W=90)

| score | benign FP on holidays | benign FP other days | off_hours detect |
|---|---|---|---|
| time.hier | 0.78% | 0.46% | 52% |
| time_cal.hier | 1.16% | 0.45% | 55% |
