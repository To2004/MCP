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
| `github_helios` | 19 | 9 | 9 | 9 |
| `slack_vireo` | 15 | 10 | 10 | 10 |
| `calendar_aurora` | 17 | 11 | 11 | 11 |

## Distributional shape

| server | arm | assets | scored | N/A | mean sens | mean blast | mean impact | mean score | low/med/high/crit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `fs_corp_filesystem` | `nacombo` | 16 | 87 | 61% | 3.06 | 3.25 | 2.71 | 35.1 | 36/26/21/4 |
| `fs_corp_filesystem` | `iso` | 16 | 101 | 55% | 3.31 | 3.53 | 2.86 | 38.3 | 31/36/34/0 |
| `fs_corp_filesystem` | `nist` | 18 | 96 | 62% | 3.17 | 3.36 | 2.86 | 37.3 | 41/29/16/10 |
| `fs_corp_filesystem` | `cis` | 9 | 75 | 40% | 3.56 | 3.61 | 2.86 | 40.7 | 24/20/26/5 |
| `github_helios` | `nacombo` | 19 | 126 | 74% | 3.21 | 3.4 | 3.23 | 42.9 | 29/46/47/4 |
| `github_helios` | `iso` | 9 | 93 | 60% | 3.56 | 3.13 | 3.23 | 38.7 | 16/56/19/2 |
| `github_helios` | `nist` | 9 | 90 | 62% | 3.33 | 3.18 | 3.23 | 37.5 | 17/56/17/0 |
| `github_helios` | `cis` | 9 | 91 | 61% | 3.44 | 2.99 | 3.23 | 37.3 | 28/36/27/0 |
| `slack_vireo` | `nacombo` | 15 | 62 | 74% | 3.27 | 2.79 | 3.06 | 30.7 | 18/38/5/1 |
| `slack_vireo` | `iso` | 10 | 49 | 69% | 3.4 | 2.98 | 3.06 | 31.4 | 16/25/6/2 |
| `slack_vireo` | `nist` | 10 | 47 | 71% | 3.2 | 2.72 | 3.06 | 27.0 | 17/27/2/1 |
| `slack_vireo` | `cis` | 10 | 49 | 69% | 3.5 | 2.69 | 3.06 | 30.1 | 20/22/6/1 |
| `calendar_aurora` | `nacombo` | 17 | 71 | 68% | 3.12 | 3.28 | 3.0 | 44.5 | 14/33/18/6 |
| `calendar_aurora` | `iso` | 11 | 52 | 64% | 3.27 | 3.25 | 3.0 | 43.5 | 16/16/15/5 |
| `calendar_aurora` | `nist` | 11 | 50 | 65% | 3.18 | 3.16 | 3.0 | 41.6 | 12/23/11/4 |
| `calendar_aurora` | `cis` | 11 | 50 | 65% | 3.27 | 3.28 | 3.0 | 49.0 | 14/14/14/8 |

## Sensitivity vs the baseline, on shared asset ids

`exact` and `within one` are agreement with `nacombo`, not accuracy.
`coverage` is how many of the baseline's assets the arm's register
still carries under the same id.

| server | arm | shared | coverage | exact | within one | mean abs Δ | bias |
|---|---|---:|---:|---:|---:|---:|---:|
| `fs_corp_filesystem` | `iso` | 16 | 100% | 44% | 94% | 0.625 | +0.25 |
| `fs_corp_filesystem` | `nist` | 16 | 100% | 62% | 100% | 0.375 | -0.12 |
| `fs_corp_filesystem` | `cis` | 5 | 31% | 60% | 100% | 0.4 | +0.00 |
| `github_helios` | `iso` | 0 | 0% | — | — | — | no shared asset ids (different taxonomy) |
| `github_helios` | `nist` | 0 | 0% | — | — | — | no shared asset ids (different taxonomy) |
| `github_helios` | `cis` | 0 | 0% | — | — | — | no shared asset ids (different taxonomy) |
| `slack_vireo` | `iso` | 0 | 0% | — | — | — | no shared asset ids (different taxonomy) |
| `slack_vireo` | `nist` | 0 | 0% | — | — | — | no shared asset ids (different taxonomy) |
| `slack_vireo` | `cis` | 0 | 0% | — | — | — | no shared asset ids (different taxonomy) |
| `calendar_aurora` | `iso` | 0 | 0% | — | — | — | no shared asset ids (different taxonomy) |
| `calendar_aurora` | `nist` | 0 | 0% | — | — | — | no shared asset ids (different taxonomy) |
| `calendar_aurora` | `cis` | 0 | 0% | — | — | — | no shared asset ids (different taxonomy) |

## Cell scores vs the baseline

Restricted to cells both arms scored on an asset id they share.

| server | arm | comparable cells | identical | mean abs Δ | bias | band flips |
|---|---|---:|---:|---:|---:|---:|
| `fs_corp_filesystem` | `iso` | 79 | 29% | 13.0 | +6.4 | 29 (37%) |
| `fs_corp_filesystem` | `nist` | 78 | 35% | 9.6 | -0.0 | 22 (28%) |
| `fs_corp_filesystem` | `cis` | 37 | 43% | 12.8 | +7.4 | 14 (38%) |
| `github_helios` | `iso` | 0 | — | — | — | no shared asset ids (different taxonomy) |
| `github_helios` | `nist` | 0 | — | — | — | no shared asset ids (different taxonomy) |
| `github_helios` | `cis` | 0 | — | — | — | no shared asset ids (different taxonomy) |
| `slack_vireo` | `iso` | 0 | — | — | — | no shared asset ids (different taxonomy) |
| `slack_vireo` | `nist` | 0 | — | — | — | no shared asset ids (different taxonomy) |
| `slack_vireo` | `cis` | 0 | — | — | — | no shared asset ids (different taxonomy) |
| `calendar_aurora` | `iso` | 0 | — | — | — | no shared asset ids (different taxonomy) |
| `calendar_aurora` | `nist` | 0 | — | — | — | no shared asset ids (different taxonomy) |
| `calendar_aurora` | `cis` | 0 | — | — | — | no shared asset ids (different taxonomy) |

## Do the three frameworks agree with each other?

The question this experiment exists to answer: three organizations
describe the same deployment under three different standards. Do they
arrive at the same severities?

| server | shared assets | unanimous | within one | mean spread | ≥2-tier splits |
|---|---:|---:|---:|---:|---:|
| `fs_corp_filesystem` | 5 | 20% | 60% | 1.2 | 2 |
| `github_helios` | 9 | 33% | 78% | 0.89 | 2 |
| `slack_vireo` | 10 | 40% | 100% | 0.6 | 0 |
| `calendar_aurora` | 11 | 9% | 91% | 1.0 | 1 |

### Where the frameworks split by two tiers or more

| server | asset | iso | nist | cis | spread |
|---|---|---|---|---|---|
| `fs_corp_filesystem` | `payroll-records` | 4 | 3 | 5 | 2 |
| `fs_corp_filesystem` | `project-material` | 4 | 3 | 2 | 2 |
| `github_helios` | `ot-estate-description-information` | 4 | 3 | 5 | 2 |
| `github_helios` | `platform-account-directory-information` | 3 | 1 | 1 | 2 |
| `calendar_aurora` | `operational-commitment-information` | 3 | 5 | 5 | 2 |
