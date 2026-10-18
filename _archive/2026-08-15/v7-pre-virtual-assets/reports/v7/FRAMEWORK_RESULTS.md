# v7 — the framework-native policy arms

Four organizations, four policy documents each, one scanner. Everything
except the policy document and its matching sensitivity prompt is held
fixed: same tool catalogs, same deterministic impact ladder, same blast
rubric, same assembly. A difference between arms is attributable to how
the organization wrote its policy.

| arm | document |
|---|---|
| `nacombo` | baseline register (v5r nacombo) |
| `iso` | ISO/IEC 27001:2022 A.5.9 + A.8.3 |
| `nist` | NIST FIPS 199 / SP 800-60 + AC-3 |
| `cis` | CIS Controls v8.1 Control 3 |

## No accuracy numbers here, and why

None of these four servers has held-out numeric ground truth.
`github_helios`, `slack_vireo` and `calendar_aurora` have no section in
`server-profiles.md` at all, and `fs_corp_filesystem`'s profile uses
path-shaped asset ids that do not align with the policy register's
concept ids. So this report measures *movement* against the `nacombo`
baseline and *agreement* between the frameworks — never correctness.

## Register shape per arm

The arms were written to diverge in shape on purpose: ISO keeps the
baseline's rows and adds columns, NIST splits a row whose read and write
categorize differently, CIS merges non-sensitive data into coarse entries
as Safeguard 3.2 permits.

| server | nacombo assets | iso assets | nist assets | cis assets |
|---|---|---|---|---|
| `fs_corp_filesystem` | 16 | 16 | 18 | 9 |
| `github_helios` | 19 | 19 | 21 | 12 |
| `slack_vireo` | 15 | 15 | 17 | 10 |
| `calendar_aurora` | 17 | 17 | 19 | 10 |

## Distributional shape

| server | arm | assets | scored | N/A | mean sens | mean blast | mean impact | mean score | low/med/high/crit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `fs_corp_filesystem` | `nacombo` | 16 | 87 | 61% | 3.06 | 3.25 | 2.71 | 35.1 | 36/26/21/4 |
| `fs_corp_filesystem` | `iso` | 16 | 101 | 55% | 3.31 | 3.53 | 2.86 | 38.3 | 31/36/34/0 |
| `fs_corp_filesystem` | `nist` | 18 | 96 | 62% | 3.17 | 3.36 | 2.86 | 37.3 | 41/29/16/10 |
| `fs_corp_filesystem` | `cis` | 9 | 75 | 40% | 3.56 | 3.61 | 2.86 | 40.7 | 24/20/26/5 |
| `github_helios` | `nacombo` | 19 | 126 | 74% | 3.21 | 3.4 | 3.23 | 42.9 | 29/46/47/4 |
| `github_helios` | `iso` | 19 | 132 | 73% | 3.21 | 3.3 | 3.23 | 37.2 | 38/61/33/0 |
| `github_helios` | `nist` | 21 | 167 | 69% | 3.05 | 3.22 | 3.23 | 36.9 | 43/88/34/2 |
| `github_helios` | `cis` | 12 | 110 | 65% | 3.67 | 3.4 | 3.23 | 48.2 | 25/35/43/7 |
| `slack_vireo` | `nacombo` | 15 | 62 | 74% | 3.27 | 2.79 | 3.06 | 30.7 | 18/38/5/1 |
| `slack_vireo` | `iso` | 15 | 62 | 74% | 3.53 | 2.73 | 3.06 | 31.6 | 16/39/5/2 |
| `slack_vireo` | `nist` | 17 | 65 | 76% | 3.41 | 2.8 | 3.06 | 30.0 | 18/41/3/3 |
| `slack_vireo` | `cis` | 10 | 73 | 54% | 4.3 | 2.96 | 3.06 | 36.9 | 10/50/12/1 |
| `calendar_aurora` | `nacombo` | 17 | 71 | 68% | 3.12 | 3.28 | 3.0 | 44.5 | 14/33/18/6 |
| `calendar_aurora` | `iso` | 17 | 80 | 64% | 3.06 | 3.14 | 3.0 | 39.2 | 26/31/18/5 |
| `calendar_aurora` | `nist` | 19 | 89 | 64% | 3.16 | 2.98 | 3.0 | 39.5 | 24/44/13/8 |
| `calendar_aurora` | `cis` | 10 | 68 | 48% | 3.9 | 3.07 | 3.0 | 44.8 | 21/22/17/8 |

## Sensitivity vs the baseline, on shared asset ids

`exact` and `within one` are agreement with `nacombo`, not accuracy.
`coverage` is how many of the baseline's assets the arm's register
still carries under the same id.

| server | arm | shared | coverage | exact | within one | mean abs Δ | bias |
|---|---|---:|---:|---:|---:|---:|---:|
| `fs_corp_filesystem` | `iso` | 16 | 100% | 44% | 94% | 0.625 | +0.25 |
| `fs_corp_filesystem` | `nist` | 16 | 100% | 62% | 100% | 0.375 | -0.12 |
| `fs_corp_filesystem` | `cis` | 5 | 31% | 60% | 100% | 0.4 | +0.00 |
| `github_helios` | `iso` | 19 | 100% | 42% | 95% | 0.632 | +0.00 |
| `github_helios` | `nist` | 19 | 100% | 47% | 95% | 0.579 | -0.37 |
| `github_helios` | `cis` | 7 | 37% | 57% | 100% | 0.429 | +0.14 |
| `slack_vireo` | `iso` | 15 | 100% | 47% | 87% | 0.8 | +0.27 |
| `slack_vireo` | `nist` | 15 | 100% | 40% | 93% | 0.667 | +0.00 |
| `slack_vireo` | `cis` | 6 | 40% | 67% | 67% | 1.0 | +1.00 |
| `calendar_aurora` | `iso` | 17 | 100% | 71% | 100% | 0.294 | -0.06 |
| `calendar_aurora` | `nist` | 17 | 100% | 53% | 94% | 0.529 | -0.18 |
| `calendar_aurora` | `cis` | 7 | 41% | 29% | 86% | 0.857 | +0.57 |

## Cell scores vs the baseline

Restricted to cells both arms scored on an asset id they share.

| server | arm | comparable cells | identical | mean abs Δ | bias | band flips |
|---|---|---:|---:|---:|---:|---:|
| `fs_corp_filesystem` | `iso` | 79 | 29% | 13.0 | +6.4 | 29 (37%) |
| `fs_corp_filesystem` | `nist` | 78 | 35% | 9.6 | -0.0 | 22 (28%) |
| `fs_corp_filesystem` | `cis` | 37 | 43% | 12.8 | +7.4 | 14 (38%) |
| `github_helios` | `iso` | 113 | 50% | 7.2 | -5.1 | 27 (24%) |
| `github_helios` | `nist` | 108 | 32% | 9.4 | -8.2 | 43 (40%) |
| `github_helios` | `cis` | 49 | 39% | 10.1 | +1.0 | 14 (29%) |
| `slack_vireo` | `iso` | 59 | 48% | 9.7 | +1.3 | 13 (22%) |
| `slack_vireo` | `nist` | 56 | 14% | 9.9 | -2.2 | 16 (29%) |
| `slack_vireo` | `cis` | 30 | 40% | 12.9 | +9.6 | 11 (37%) |
| `calendar_aurora` | `iso` | 70 | 61% | 5.8 | -1.9 | 9 (13%) |
| `calendar_aurora` | `nist` | 66 | 36% | 11.7 | -7.4 | 19 (29%) |
| `calendar_aurora` | `cis` | 41 | 27% | 12.9 | +7.1 | 15 (37%) |

## Do the three frameworks agree with each other?

The question this experiment exists to answer: three organizations
describe the same deployment under three different standards. Do they
arrive at the same severities?

| server | shared assets | unanimous | within one | mean spread | ≥2-tier splits |
|---|---:|---:|---:|---:|---:|
| `fs_corp_filesystem` | 5 | 20% | 60% | 1.2 | 2 |
| `github_helios` | 7 | 14% | 71% | 1.14 | 2 |
| `slack_vireo` | 6 | 0% | 67% | 1.67 | 2 |
| `calendar_aurora` | 7 | 14% | 71% | 1.14 | 2 |

### Where the frameworks split by two tiers or more

| server | asset | iso | nist | cis | spread |
|---|---|---|---|---|---|
| `fs_corp_filesystem` | `payroll-records` | 4 | 3 | 5 | 2 |
| `fs_corp_filesystem` | `project-material` | 4 | 3 | 2 | 2 |
| `github_helios` | `helios-ot-runbooks` | 3 | 3 | 5 | 2 |
| `github_helios` | `platform-user-directory` | 3 | 2 | 1 | 2 |
| `slack_vireo` | `vireo-announcements` | 5 | 2 | 5 | 3 |
| `slack_vireo` | `vireo-eng-platform` | 3 | 2 | 5 | 3 |
| `calendar_aurora` | `aurora-exec` | 4 | 3 | 5 | 2 |
| `calendar_aurora` | `aurora-maintenance` | 3 | 3 | 5 | 2 |
