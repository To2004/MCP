# Asset Ranking — rubric-scored by local LLM (Qwen2.5)

Scored per `docs/standards/asset-ranking-guidelines.md` (FIPS 199 · MITRE ATT&CK · OWASP · kill-chain).

## sqlite-mcp  _(kind=sqlite)_

| Asset class | Risk Level | Sensitivity | Reasoning |
|---|---|---|---|
| `api_keys` | Critical | 5 | T1552 + OWASP non-compliance; FIPS H/H/H |
| `employees` | High | 4 | T1213 + OWASP PII non-compliance; FIPS H/M/L |
| `customers` | Medium | 3 | T1005 Data from Local System; contains email |
| `orders` | Low | 2 | FIPS M/M/L; generic transaction data |
| `insights` | Minimal | 1 | FIPS L/L/L; business insights, no PII or sensitive data |

## filesystem:corp_filesystem  _(kind=filesystem)_

| Asset class | Risk Level | Sensitivity | Reasoning |
|---|---|---|---|
| `.pem` | Critical | 5 | T1552 Unsecured Credentials; key material |
| `corp_filesystem/sensitive/security/` | Critical | 5 | FIPS H/H/H; T1213 Data from Info Repositories; critical security data |
| `.c` | High | 4 | T1195 Supply Chain Compromise; source code |
| `.csv` | High | 4 | T1530 Data from Cloud Storage; potential PII or financial data |
| `corp_filesystem/sensitive/` | High | 4 | T1530 Data from Cloud Storage; sensitive content |
| `corp_filesystem/sensitive/financials/` | High | 4 | T1530 Data from Cloud Storage; financial records |
| `corp_filesystem/source_code/` | High | 4 | T1195 Supply Chain Compromise; OWASP financial impact |
| `.sql` | Medium | 3 | T1005 Data from Local System; potential for schema/data extraction |
| `corp_filesystem/projects/` | Medium | 3 | FIPS Moderate on Confidentiality and Integrity; project data |
| `.md` | Low | 2 | FIPS Low across CIA; documentation-focused |
| `.txt` | Low | 2 | FIPS Low across CIA; no Technique target |
| `corp_filesystem/onboarding/` | Low | 2 | FIPS Low on Confidentiality and Integrity; documentation-focused |
| `.png` | Minimal | 1 | FIPS Low across CIA; media files |
| `corp_filesystem/` | Minimal | 1 | FIPS Low across CIA; no Technique target |

