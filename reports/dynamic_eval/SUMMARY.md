# Dynamic scoring — benign vs adversarial discrimination

Self-generated discrimination test (no external benchmark exists for this
task). Labels come from the synthetic testbed by construction; each session
is scored **static-only** and **static⊗dynamic**, so the delta is exactly
what the dynamic signal (baseline + sequence) adds. `recall` = fraction of
adversarial sessions flagged; `fall-out` = fraction of benign sessions
flagged (lower is better).

A session's score is its riskiest call's band. Results are shown at two
flag thresholds: **high** and **critical**. Static over-flags ordinary reads
to *high*, so benign fall-out is high there; the read-then-exfil **sequence**
signal reaches *critical*, where benign sessions rarely land — that is where
the dynamic signal creates clean separation.

Session mean band-rank (low=1 … critical=4): adversarial 3.47→3.81 (static→combined), misuse 2.84→2.92, benign 2.41→2.41. Misuse (accidental-insider mistakes) is expected to land between benign and adversarial — it touches assets but carries no attack sequence.

## Overall — flag threshold: high

| scorer | recall (adversarial) | flagged (misuse) | fall-out (benign) |
| --- | --- | --- | --- |
| static | 91% | 63% | 49% |
| combined | 100% | 71% | 49% |

Adversarial sessions caught **only** by the dynamic signal (static < high ≤ combined): 8 of 88.

## Overall — flag threshold: critical

| scorer | recall (adversarial) | flagged (misuse) | fall-out (benign) |
| --- | --- | --- | --- |
| static | 56% | 24% | 9% |
| combined | 81% | 24% | 9% |

Adversarial sessions caught **only** by the dynamic signal (static < critical ≤ combined): 22 of 88.

## Per server (critical threshold)

| server | n benign | n adv | static recall | combined recall | benign fall-out | dynamic-only catches |
| --- | --- | --- | --- | --- | --- | --- |
| calendar_cbg | 498 | 20 | 50% | 90% | 24% | 8 |
| fs_corp_filesystem | 97 | 4 | 75% | 100% | 0% | 1 |
| fs_fintech_fs | 100 | 4 | 50% | 100% | 0% | 2 |
| fs_law_firm_fs | 88 | 4 | 25% | 100% | 9% | 3 |
| fs_media_studio_fs | 97 | 4 | 50% | 100% | 25% | 2 |
| fs_medical_clinic_fs | 95 | 4 | 100% | 100% | 20% | 0 |
| github_cbg | 481 | 20 | 55% | 80% | 5% | 5 |
| slack_cbg | 487 | 20 | 55% | 55% | 0% | 0 |
| sqlite_cbg_sqlite | 87 | 4 | 25% | 50% | 0% | 1 |
| sqlite_devops_sqlite | 86 | 4 | 100% | 100% | 0% | 0 |
