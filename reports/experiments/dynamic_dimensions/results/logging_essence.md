# What logs record and what analytics use, across domains similar to an MCP gateway

A condensed research note for choosing the dynamic layer's focus. It covers what a log record contains in comparable systems and which behaviour signals are built from it. Only request-side signals matter here: the dynamic layer may not use server responses. Sources were read in October 2026; items the researcher could not confirm on a primary source are marked UNVERIFIED in the full research transcript.

## The universal record

Every system reviewed logs six request-side facts:

| Fact | What it is |
|---|---|
| Who | The principal, with its type and any delegation |
| Action | What was done, with a read/write class |
| Object | What it was done to |
| When | The time of the request |
| From where | Source address |
| Client | The client software |

Behaviour analytics also needs a session or credential handle (hashed) and a correlation id.

| Fact | CloudTrail | Kubernetes audit | GitHub / Slack / Workspace | pgaudit | EHR (ONC) | HTTP access logs |
|---|---|---|---|---|---|---|
| Who | userIdentity (type, invokedBy, onBehalfOf) | user, impersonatedUser | actor, actor_is_bot, isAgenticAction | user | user id | auth user |
| Action + class | eventName + readOnly | verb (get/list vs create/delete) | action, operation_type | CLASS (READ/WRITE/DDL/ROLE) | add / change / query / print | method + route |
| Object | resources[] | objectRef | repo / entity / resourceIds | OBJECT_NAME | patient + data category | path |
| When / from / client | eventTime, sourceIPAddress, userAgent | timestamps, sourceIPs, userAgent | created_at, ip (opt-in), user_agent | %t, %r, %a | NTP time | %t, %h, User-agent |
| Session / correlation | accessKeyId, requestID | auditID | token_id, request_id, session_id | %c, STATEMENT_ID | — | X-Request-Id |

## Bodies are the exception

No major system logs full request bodies by default. The reasons given are volume, cost and sensitive data. They cope in five ways:

- **Metadata levels.** Kubernetes logs `Metadata` for reads and secrets, and `Request`/`RequestResponse` only for writes (GKE practice).
- **Choosing classes of calls, not fields.** Examples: CloudTrail event selectors, pgaudit classes, GitHub opt-in API events.
- **Structured parameters instead of raw bodies.** Examples: CloudTrail `requestParameters`; Workspace `parameters` vs `sensitiveParameters`.
- **Shape and size instead of values.** Examples: EHR "medication list, not the medication"; database query "quiplets" (Kamra et al.); `http.request.body.size`.
- **Hashing identifiers.** OWASP recommends hashing session ids.

**What this means for us:** reading only the inputs the static scan keeps (`which`, `how_much`, `who`, `when`, `action`, `carried` length) is the CloudTrail/Workspace pattern. No system offers per-field selection inside a generic body. Field selection comes from the API's schema, which is what the static scan supplies.

## Signals that recur across domains (request-side)

| Signal | Where it appears | Typical reference and window |
|---|---|---|
| Frequency / velocity | CloudTrail Insights (per minute vs 7 days), GuardDuty S3 (24 h), payments (1/7/30 days), Defender for Cloud Apps (activity rate) | self |
| First-seen / novelty | Sentinel (first time for user, peers, tenant; 30–180 days), GuardDuty (rare / infrequent / frequent), Elastic rare_method_for_username, PSD2 new payee | self, then peers and population |
| Breadth (distinct objects) | CADS (EHR), Defender for Cloud Apps mass download, web traversal width | **needs a peer or population reference:** raw distinct-patient counts gave very high false positives (CADS) |
| Time of day / week | EHR after clinic hours, payments night/weekend (circular models), web night crawlers | self |
| Peer / role | Sentinel peers, CADS communities, Kamra role classifier, Boxwala same-department | role or learned group |
| Sequence / workflow | OWASP "out of order / bypass flow control", GuardDuty "series in proximity", "explained by a prior step" (more than 94% of EHR accesses, Fabbri & LeFevre) | session; less standardised |
| Dormancy / new account | Sentinel (dormant 180 days, new 30 days), Defender inactive accounts, Elastic dormant user active | self |

**Response-side and excluded:** error and failure rates, and returned volume (rows returned, bytes sent).

**Request-side substitutes:**
- count requests instead of rows returned;
- read the requested quantity or span from the arguments;
- spot loops and retries as repeated identical requests (Tan & Kumar's "Repeated" feature).

## Key sources

- AWS CloudTrail record contents and Insights; Amazon GuardDuty finding types.
- Kubernetes auditing (levels and stages); GKE audit policy.
- GitHub enterprise audit log; Slack Audit Logs API and anomalous events; Google Workspace Reports API.
- pgaudit; Kamra, Terzi & Bertino, *VLDB J.* (CERIAS TR 2007-73).
- Chen & Malin, CODASPY 2011 (CADS); Boxwala et al., JAMIA 2011; Fabbri & LeFevre, arXiv 1109.6880.
- NIST SP 800-92; OWASP Logging Cheat Sheet; OpenTelemetry semantic conventions; Elastic Common Schema; CEF.
- Microsoft Sentinel UEBA reference; Microsoft Defender for Cloud Apps anomaly detection.
- Fraud Detection Handbook (ULB/Worldline); PSD2 RTS 2018/389 (UK-retained text).
- Tan & Kumar, DMKD 2002; OWASP bot management and API6:2023.
