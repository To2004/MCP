# Did the scanner read each policy correctly?

Half of all v7 assets score differently from the `nacombo` baseline. That
number cannot by itself tell a *justified* difference (the framework
document genuinely says something else) from a *scanner error* (the
document says one thing and the scanner produced another).

This judge separates them. For every shared asset it re-derives the tier
from the policy text alone — shown one document and one asset, and told
neither scanner's number — then the verdict is arithmetic on four values:
what each policy IMPLIES and what each scan PRODUCED.

| verdict | meaning |
|---|---|
| `faithful` | scanner matches what its own policy implies |
| `justified` | faithful **and** the two documents genuinely differ |
| `agrees` | faithful, and both documents imply the same tier |
| `scanner_error` | **the failure that matters** — policy implies X, scanner said Y |

## Per arm

| arm | judged | faithful | **scanner error** | over | under | ≥2 tiers | mean signed error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `iso` | 67 | 55% | **45%** | 8 | 22 | 1 | -0.37 |
| `nist` | 67 | 46% | **54%** | 7 | 29 | 5 | -0.72 |
| `cis` | 25 | 80% | **20%** | 4 | 1 | 2 | +1.60 |

## Is a difference from the baseline explained by the documents?

`policy divergence` counts assets where the judge read the two documents as
implying *different* tiers — a difference that is supposed to happen.
`baseline unfaithful` counts assets where the **baseline** scanner, not the
v7 one, departed from its own policy.

| arm | policy divergence | justified | agrees | baseline unfaithful |
|---|---:|---:|---:|---:|
| `iso` | 20 | 12 | 25 | 11 |
| `nist` | 32 | 12 | 19 | 11 |
| `cis` | 9 | 6 | 14 | 4 |

## Every scanner error, worst first

`policy` is the tier the judge derived from that arm's own document;
`scan` is what the arm produced. The quote is the policy sentence the
judge relied on.

| arm | server | asset | policy | scan | Δ | class the policy assigns |
|---|---|---|---:|---:|---:|---|
| `iso` | `slack_vireo` | `vireo-announcements` | 1 | 5 | +4 | Public |
| `cis` | `slack_vireo` | `vireo-announcements` | 1 | 5 | +4 | Non-sensitive |
| `nist` | `fs_corp_filesystem` | `directory-structure` | 5 | 2 | -3 | confidentiality |
| `cis` | `slack_vireo` | `vireo-eng-platform` | 2 | 5 | +3 | Non-sensitive |
| `nist` | `fs_corp_filesystem` | `onboarding-material` | 4 | 2 | -2 | MODERATE |
| `nist` | `github_helios` | `helios-grid-infra-config` | 5 | 3 | -2 | D.2.2 Key Asset and Critical Infrastructure Protection |
| `nist` | `github_helios` | `helios-scada-gateway` | 5 | 3 | -2 | D.7.1 Energy Supply |
| `nist` | `calendar_aurora` | `account-directory` | 2 | 4 | +2 | LOW |
| `iso` | `fs_corp_filesystem` | `directory-records` | 3 | 4 | +1 | Internal |
| `iso` | `fs_corp_filesystem` | `file-contents` | 5 | 4 | -1 | Restricted |
| `iso` | `fs_corp_filesystem` | `file-directory` | 4 | 3 | -1 | Confidential |
| `iso` | `fs_corp_filesystem` | `media-records` | 3 | 4 | +1 | Internal |
| `iso` | `fs_corp_filesystem` | `project-material` | 3 | 4 | +1 | Internal |
| `iso` | `fs_corp_filesystem` | `security-keys` | 5 | 4 | -1 | Restricted |
| `iso` | `github_helios` | `branch-heads` | 5 | 4 | -1 | Restricted |
| `iso` | `github_helios` | `code-records` | 4 | 3 | -1 | Confidential |
| `iso` | `github_helios` | `helios-grid-infra-config` | 5 | 4 | -1 | Restricted |
| `iso` | `github_helios` | `helios-market-bidding-engine` | 4 | 3 | -1 | Confidential |
| `iso` | `github_helios` | `helios-ot-runbooks` | 4 | 3 | -1 | Confidential |
| `iso` | `github_helios` | `helios-scada-gateway` | 5 | 4 | -1 | Restricted |
| `iso` | `github_helios` | `issue-records` | 3 | 4 | +1 | Internal |
| `iso` | `github_helios` | `org-external-copies` | 4 | 3 | -1 | Confidential |
| `iso` | `github_helios` | `platform-user-directory` | 2 | 3 | +1 | Routine |
| `iso` | `github_helios` | `repository-contents` | 4 | 3 | -1 | Confidential |
| `iso` | `slack_vireo` | `agent-channel-membership` | 5 | 4 | -1 | Restricted |
| `iso` | `slack_vireo` | `message-reactions` | 5 | 4 | -1 | Modification |
| `iso` | `slack_vireo` | `usergroup-directory` | 2 | 3 | +1 | Routine |
| `iso` | `slack_vireo` | `usergroup-membership` | 5 | 4 | -1 | Restricted |
| `iso` | `slack_vireo` | `vireo-lab-informatics` | 4 | 3 | -1 | Confidential |
| `iso` | `slack_vireo` | `vireo-trial-ops` | 4 | 3 | -1 | Confidential |
| `iso` | `slack_vireo` | `vireo-unblinding` | 5 | 4 | -1 | Restricted |
| `iso` | `calendar_aurora` | `account-directory` | 5 | 4 | -1 | Restricted |
| `iso` | `calendar_aurora` | `aurora-exec` | 5 | 4 | -1 | Confidential |
| `iso` | `calendar_aurora` | `aurora-regulatory` | 4 | 3 | -1 | Confidential |
| `iso` | `calendar_aurora` | `connected-account-config` | 5 | 4 | -1 | Restricted |
| `iso` | `calendar_aurora` | `event-records` | 3 | 4 | +1 | Internal |
| `iso` | `calendar_aurora` | `outbound-invite-email` | 5 | 4 | -1 | Confidential |
| `nist` | `fs_corp_filesystem` | `media-records` | 3 | 4 | +1 | confidentiality |
| `nist` | `fs_corp_filesystem` | `payroll-records` | 4 | 3 | -1 | MODERATE |
| `nist` | `fs_corp_filesystem` | `product-source` | 4 | 3 | -1 | MODERATE |

### The three largest, with the policy's own words

**`iso` · `slack_vireo` · `vireo-announcements` — policy implies 1, scanner said 5**

> Company-wide broadcast channel; already seen by everyone, so only spoofing matters (owner: Corporate Communications; loss axis: modification (spoofing); organizationally sanctioned operations: conversations_history, conversations_replies)

Judge: The asset is described as a company-wide broadcast channel that has already been seen by everyone, implying no confidentiality left to lose.

**`cis` · `slack_vireo` · `vireo-announcements` — policy implies 1, scanner said 5**

> Company-wide broadcast channel; already seen by everyone, so only spoofing matters (data category: Non-sensitive; segment: public)

Judge: The policy explicitly states that the data in this channel has already been seen by everyone and is non-sensitive.

**`nist` · `fs_corp_filesystem` · `directory-structure` — policy implies 5, scanner said 2**

> Recursive tree of every name and path under the mount, no contents; the paths name teams and the security scope (information type: C.3.5.4 IT Infrastructure Maintenance; impact driver: confidentiality; organizationally sanctioned operations: none)

Judge: The asset 'directory-structure' exposes the layout of the entire mount, which names teams and the security scope, leading to severe or catastrophic adverse effects as defined by the policy.

