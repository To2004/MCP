# Dynamic dimensions — seed 1, per-dimension budget 0.5%

## E1 — which dimension catches which strange usage (W=90, default references)

| dimension | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit | benign | alerts/day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rep.hier | 95% | 0% | 15% | 0% | 0% | 0% | 2% | 42% | 5% | 2% | 15% | 0% | 0.37% | 5.0 |
| rate.hier | 38% | 48% | 0% | 0% | 0% | 0% | 0% | 57% | 0% | 0% | 5% | 20% | 0.24% | 3.7 |
| reach.hier | 15% | 42% | 72% | 8% | 0% | 0% | 0% | 28% | 0% | 0% | 5% | 55% | 0.17% | 2.8 |
| breadth.hier | 0% | 0% | 0% | 68% | 2% | 0% | 0% | 10% | 0% | 2% | 12% | 0% | 0.20% | 2.7 |
| asset.hier | 0% | 2% | 0% | 95% | 0% | 0% | 0% | 18% | 20% | 35% | 62% | 0% | 0.27% | 3.6 |
| sensjump.self | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 1% | 0% | 0.00% | 0.0 |
| tool.hier | 0% | 0% | 0% | 5% | 92% | 2% | 0% | 0% | 0% | 0% | 0% | 15% | 0.00% | 0.1 |
| order_rule.policy | 0% | 0% | 0% | 0% | 85% | 100% | 0% | 2% | 0% | 0% | 0% | 0% | 0.00% | 0.1 |
| order_tr.hier | 52% | 25% | 90% | 88% | 98% | 100% | 2% | 25% | 0% | 68% | 19% | 15% | 0.42% | 5.8 |
| time_cal.hier | 40% | 25% | 40% | 20% | 32% | 48% | 62% | 42% | 30% | 30% | 15% | 55% | 0.45% | 5.7 |
| dormancy.hier | 5% | 5% | 10% | 0% | 5% | 5% | 5% | 2% | 80% | 0% | 5% | 60% | 0.04% | 0.6 |
| size.hier | 0% | 80% | 12% | 10% | 2% | 0% | 0% | 10% | 0% | 0% | 6% | 100% | 0.27% | 4.8 |

## E2 — compared with whom (W=90)

| dimension.reference | mean detect | ordinary FP | new_hire | role_change | team_transfer | new_repo | back_from_vacation | oncall_incident | legit_drift |
|---|---|---|---|---|---|---|---|---|---|
| rep.self | 14% | 0.37% | 0% | 0% | 1% | 1% | 0% | 1% | 0% |
| rep.peer | 14% | 0.39% | 0% | 0% | 1% | 0% | 0% | 1% | 1% |
| rep.org | 13% | 0.32% | 1% | 0% | 0% | 0% | 1% | 1% | 0% |
| rep.hier | 15% | 0.37% | 0% | 0% | 1% | 1% | 0% | 1% | 0% |
| rate.self | 14% | 0.25% | 0% | 0% | 0% | 0% | 0% | 4% | 0% |
| rate.peer | 14% | 0.22% | 0% | 0% | 0% | 0% | 0% | 2% | 0% |
| rate.org | 11% | 0.24% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| rate.hier | 14% | 0.24% | 0% | 0% | 0% | 0% | 0% | 3% | 0% |
| reach.self | 21% | 0.19% | 0% | 0% | 0% | 0% | 0% | 1% | 1% |
| reach.peer | 14% | 0.13% | 0% | 0% | 0% | 0% | 0% | 1% | 0% |
| reach.org | 7% | 0.14% | 0% | 0% | 0% | 0% | 0% | 1% | 0% |
| reach.hier | 19% | 0.17% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| breadth.self | 8% | 0.23% | 0% | 0% | 1% | 0% | 0% | 1% | 0% |
| breadth.peer | 7% | 0.14% | 0% | 0% | 0% | 0% | 0% | 1% | 0% |
| breadth.org | 4% | 0.08% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| breadth.hier | 8% | 0.19% | 0% | 0% | 1% | 0% | 0% | 0% | 0% |
| asset.self | 19% | 0.23% | 1% | 0% | 1% | 1% | 1% | 0% | 1% |
| asset.peer | 10% | 0.24% | 0% | 0% | 0% | 2% | 0% | 0% | 2% |
| asset.org | 9% | 0.01% | 0% | 0% | 0% | 6% | 0% | 0% | 0% |
| asset.hier | 19% | 0.22% | 1% | 0% | 1% | 1% | 1% | 0% | 1% |
| asset.anchor | 9% | 0.24% | 0% | 0% | 0% | 2% | 0% | 0% | 2% |
| tool.self | 16% | 0.01% | 1% | 1% | 0% | 0% | 0% | 0% | 0% |
| tool.peer | 10% | 0.00% | 0% | 0% | 0% | 0% | 0% | 3% | 0% |
| tool.org | 8% | 0.23% | 0% | 3% | 0% | 0% | 0% | 0% | 1% |
| tool.hier | 10% | 0.00% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| order_tr.self | 50% | 0.37% | 1% | 3% | 0% | 1% | 1% | 10% | 0% |
| order_tr.peer | 48% | 0.32% | 1% | 1% | 0% | 1% | 1% | 16% | 0% |
| order_tr.org | 27% | 0.34% | 1% | 5% | 1% | 0% | 1% | 14% | 0% |
| order_tr.hier | 48% | 0.37% | 0% | 2% | 0% | 1% | 1% | 12% | 0% |
| time.self | 28% | 0.47% | 0% | 1% | 0% | 1% | 0% | 2% | 0% |
| time.peer | 30% | 0.34% | 1% | 0% | 0% | 0% | 0% | 8% | 1% |
| time.org | 1% | 0.25% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| time.hier | 32% | 0.45% | 0% | 1% | 0% | 1% | 0% | 2% | 0% |
| dormancy.self | 10% | 0.04% | 0% | 0% | 0% | 0% | 2% | 0% | 0% |
| dormancy.peer | 15% | 0.03% | 0% | 0% | 0% | 0% | 2% | 0% | 0% |
| dormancy.org | 16% | 0.03% | 0% | 0% | 0% | 0% | 2% | 0% | 0% |
| dormancy.hier | 15% | 0.03% | 0% | 0% | 0% | 0% | 2% | 0% | 0% |
| size.self | 22% | 0.30% | 0% | 1% | 0% | 0% | 0% | 1% | 0% |
| size.peer | 18% | 0.20% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| size.org | 18% | 0.09% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| size.hier | 18% | 0.27% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |

## E3 — window length and anchoring

| score (window) | creep | habit | fanout | legit_drift FP | transfer FP | new_repo FP | ordinary FP |
|---|---|---|---|---|---|---|---|
| asset.hier (W=30) | 77% | 0% | 92% | 1% | 1% | 1% | 0.34% |
| asset.peer (W=30) | 45% | 5% | 85% | 1% | 1% | 1% | 0.25% |
| asset.anchor (W=30) | 37% | 10% | 78% | 2% | 0% | 1% | 0.25% |
| reach.self (W=30) | 9% | 65% | 12% | 0% | 0% | 0% | 0.25% |
| reach.peer (W=30) | 5% | 55% | 0% | 0% | 0% | 0% | 0.15% |
| reach.hier (W=30) | 4% | 65% | 5% | 0% | 0% | 0% | 0.21% |
| asset.hier (W=90) | 62% | 0% | 95% | 1% | 1% | 1% | 0.22% |
| asset.peer (W=90) | 17% | 5% | 85% | 2% | 0% | 2% | 0.24% |
| asset.anchor (W=90) | 19% | 5% | 75% | 2% | 0% | 2% | 0.24% |
| reach.self (W=90) | 4% | 60% | 12% | 1% | 0% | 0% | 0.19% |
| reach.peer (W=90) | 0% | 45% | 0% | 0% | 0% | 0% | 0.13% |
| reach.hier (W=90) | 5% | 55% | 8% | 0% | 0% | 0% | 0.17% |
| asset.hier (W=life) | 40% | 0% | 95% | 0% | 1% | 1% | 0.12% |
| asset.peer (W=life) | 16% | 5% | 82% | 0% | 0% | 3% | 0.22% |
| asset.anchor (W=life) | 15% | 5% | 70% | 0% | 0% | 3% | 0.22% |
| reach.self (W=life) | 2% | 50% | 5% | 0% | 0% | 0% | 0.15% |
| reach.peer (W=life) | 1% | 35% | 0% | 0% | 0% | 0% | 0.13% |
| reach.hier (W=life) | 2% | 55% | 2% | 0% | 0% | 0% | 0.14% |

## E3b — self-normalisation of a weekly habit (W=90)

| score | wk1 | wk2 | wk3 | wk5 | wk9 | wk13 |
|---|---|---|---|---|---|---|
| reach.self | 15% | 2% | 3% | 0% | 1% | 3% |
| reach.peer | 2% | 0% | 2% | 1% | 3% | 0% |
| reach.hier | 12% | 2% | 3% | 0% | 1% | 3% |
| size.self | 46% | 17% | 10% | 9% | 7% | 6% |
| size.peer | 44% | 32% | 34% | 28% | 22% | 25% |
| size.hier | 50% | 32% | 27% | 15% | 9% | 8% |

## E4/E5 — combined detector over time (total budget 1.0%, W=90)

| combination | horizon | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit | benign | sessions/day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OR (budget split) | month 1 | – | – | 50% | – | – | – | – | 100% | – | 50% | – | 100% | 0.67% | 6.8 |
| OR (budget split) | year 1 | 68% | 67% | 88% | 92% | 100% | 100% | 5% | 65% | 80% | 72% | 38% | 100% | 0.32% | 3.6 |
| OR (budget split) | year 2 | 72% | 77% | 82% | 81% | 100% | 100% | 21% | 69% | 73% | 50% | 12% | 82% | 0.35% | 4.4 |
| SUM of bits | month 1 | – | – | 100% | – | – | – | – | 100% | – | 0% | – | 100% | 0.56% | 4.1 |
| SUM of bits | year 1 | 86% | 72% | 94% | 88% | 84% | 44% | 0% | 69% | 0% | 28% | 38% | 86% | 0.41% | 3.6 |
| SUM of bits | year 2 | 78% | 86% | 95% | 94% | 95% | 47% | 0% | 69% | 13% | 15% | 16% | 91% | 0.48% | 4.1 |
| MAX of ranks | month 1 | – | – | 100% | – | – | – | – | 0% | – | 50% | – | 100% | 1.12% | 10.8 |
| MAX of ranks | year 1 | 77% | 72% | 88% | 92% | 100% | 100% | 24% | 65% | 80% | 78% | 47% | 100% | 0.54% | 4.9 |
| MAX of ranks | year 2 | 78% | 77% | 95% | 81% | 100% | 100% | 26% | 77% | 80% | 55% | 14% | 73% | 0.64% | 6.1 |

## E5b — weighting strangeness by consequence (budget 1.0%, W=90)

| strangeness + lambda*log2(impact*sens) | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit | alerts on high-consequence calls | benign |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lambda=0.0 | 75% | 57% | 78% | 62% | 95% | 100% | 0% | 62% | 10% | 25% | 13% | 60% | 1% | 0.56% |
| lambda=0.5 | 80% | 52% | 72% | 60% | 95% | 100% | 2% | 65% | 5% | 25% | 15% | 60% | 2% | 0.58% |
| lambda=1.0 | 80% | 50% | 68% | 62% | 92% | 100% | 2% | 68% | 0% | 28% | 18% | 60% | 4% | 0.60% |

## E7 — the three plans at the same budget (1.0% of calls; P3: top 3% caller-days)

| plan | horizon | loop | pgwalk | overfetch | fanout | offrole | wfskip | offhrs | burst | dormant | sensesc | creep | habit | benign calls flagged | caller-days flagged / day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 rules + counters | month 1 | – | – | 50% | – | – | – | – | 0% | – | 0% | – | 50% | 1.00% | 4.2 |
| P1 rules + counters | year 1 | 82% | 44% | 81% | 21% | 100% | 100% | 5% | 65% | 60% | 6% | 29% | 86% | 0.56% | 3.1 |
| P1 rules + counters | year 2 | 78% | 73% | 73% | 19% | 100% | 100% | 5% | 54% | 7% | 0% | 9% | 82% | 0.55% | 3.5 |
| P2 all dimensions, hierarchy | month 1 | – | – | 100% | – | – | – | – | 0% | – | 50% | – | 100% | 1.12% | 4.8 |
| P2 all dimensions, hierarchy | year 1 | 77% | 72% | 88% | 92% | 100% | 100% | 24% | 65% | 80% | 78% | 47% | 100% | 0.54% | 3.7 |
| P2 all dimensions, hierarchy | year 2 | 78% | 77% | 95% | 81% | 100% | 100% | 26% | 77% | 80% | 55% | 14% | 73% | 0.64% | 4.7 |
| P3 caller-day risk (RBA) | month 1 | – | – | 50% | – | – | – | – | 0% | – | 0% | – | 0% | 8.04% | 0.5 |
| P3 caller-day risk (RBA) | year 1 | 32% | 39% | 25% | 92% | 26% | 52% | 0% | 65% | 20% | 6% | 50% | 57% | 7.65% | 0.7 |
| P3 caller-day risk (RBA) | year 2 | 39% | 59% | 36% | 56% | 52% | 47% | 5% | 38% | 7% | 15% | 24% | 45% | 8.20% | 0.8 |
| P3b caller-day risk, >=2 dimensions | month 1 | – | – | 50% | – | – | – | – | 0% | – | 0% | – | 0% | 8.04% | 0.5 |
| P3b caller-day risk, >=2 dimensions | year 1 | 32% | 39% | 25% | 92% | 26% | 52% | 0% | 65% | 20% | 6% | 50% | 57% | 7.65% | 0.7 |
| P3b caller-day risk, >=2 dimensions | year 2 | 39% | 59% | 36% | 56% | 52% | 47% | 5% | 38% | 7% | 15% | 24% | 45% | 8.20% | 0.8 |


## E6 — holiday calendar (time dimension, W=90)

| score | benign FP on holidays | benign FP other days | off_hours detect |
|---|---|---|---|
| time.hier | 0.82% | 0.45% | 57% |
| time_cal.hier | 0.83% | 0.44% | 62% |
