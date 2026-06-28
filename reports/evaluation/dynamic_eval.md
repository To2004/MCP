# Dynamic evaluation: request-time risk vs. call intent

Scored calls: 261. Binary detection is computed on the **194** calls with a usable verdict (89 risky, 105 benign): a real band maps to its rank (low=1..critical=4), a forbidden-tool `invalid` maps to deny, `unresolved` abstentions and the access-control `MISUSE` class are excluded. Labels are the sessions' authored intent categories — a **weak** ground truth, so these numbers are diagnostic. We group ['BAD_PARAMS', 'BAD_TOOL', 'EDGE', 'MALICIOUS'] as risky and ['BENIGN', 'DISCOVERY', 'VALID'] as benign.

## Separation

- **AUC** (risk band vs. risky label): **0.64**
- at the deny threshold (band ≥ high): detection/TPR **67%**, false-positive rate on benign **59%**, precision 49%, recall 67%, F1 57%

## Graduated vs. a single binary threshold

A binary gate must commit to one cut; the table shows the error count (FP+FN) at each. The four-band gate instead routes the middle to log/escalate rather than forcing allow or deny.

| binary cut | TP | FP | TN | FN | FP+FN | TPR | FPR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ≥ medium | 87 | 97 | 8 | 2 | **99** | 98% | 92% |
| ≥ high | 60 | 62 | 43 | 29 | **91** | 67% | 59% |
| ≥ critical | 30 | 3 | 102 | 59 | **62** | 34% | 3% |

### Parameter escalation & static under-detection

- parameter escalation lifted the band on **11** calls; by category: {'VALID': 7, 'BENIGN': 1, 'MISUSE': 2, 'MALICIOUS': 1}
- scorable MALICIOUS calls still scored low/medium by the *static* cell: **27** — read-only exfiltration the inherent cell under-weights, the case a contextual request-time LLM scorer is designed to escalate.

### Coverage (what the static scorer can score)

| category | scorable | unresolved (abstain) | invalid (forbidden tool) |
| --- | --- | --- | --- |
| DISCOVERY | 10 | 2 | 0 |
| BENIGN | 43 | 3 | 0 |
| VALID | 52 | 2 | 0 |
| MISUSE | 48 | 3 | 0 |
| EDGE | 19 | 1 | 0 |
| BAD_PARAMS | 8 | 8 | 0 |
| BAD_TOOL | 0 | 0 | 15 |
| MALICIOUS | 47 | 0 | 0 |
| **all** | 227 | 19 | 15 |

Scorable coverage: **227/261 (87%)**. `unresolved` calls (enumeration / no-argument / unscanned target) are where the static scorer abstains — the gap a contextual LLM call scorer (future work) is meant to fill.

### Category × final band

| category | low | medium | high | critical | unresolved | invalid | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DISCOVERY | 2 | 3 | 5 | 0 | 2 | 0 | 12 |
| BENIGN | 3 | 24 | 16 | 0 | 3 | 0 | 46 |
| VALID | 3 | 8 | 38 | 3 | 2 | 0 | 54 |
| MISUSE | 1 | 10 | 32 | 5 | 3 | 0 | 51 |
| EDGE | 0 | 2 | 15 | 2 | 1 | 0 | 20 |
| BAD_PARAMS | 0 | 0 | 2 | 6 | 8 | 0 | 16 |
| BAD_TOOL | 0 | 0 | 0 | 0 | 0 | 15 | 15 |
| MALICIOUS | 2 | 25 | 13 | 7 | 0 | 0 | 47 |
