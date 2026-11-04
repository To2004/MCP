# UEBA, insider-threat detection and public per-user datasets for the dynamic layer

This note surveys user and entity behaviour analytics (UEBA) and insider-threat detection as far
as they bear on the dynamic layer's per-caller baselines. It covers how commercial UEBA scores and
aggregates signals, which academic work matters, and which **public datasets with per-user event
logs** could give the 15 dimensions a non-synthetic, held-out test. Every fact below was read on the
page in [Sources](#sources) on 2026-10-25, unless it is marked UNVERIFIED. Threat model as
everywhere in this repo: the MCP server is the protected asset and the calling agent is the threat.
In UEBA terms, the agent plays the "user", a tool plays the "action" or "API", and an asset plays
the "resource".

## Answers in brief

1. **There is no public dataset of real MCP traffic with per-caller identity.** The nearest
   things are an aggregate table of MCP client names and versions seen at `huggingface.co/mcp`
   [D28], and a 12-day MCP honeypot whose traffic was all registry indexers [D29]. A held-out test
   of the dynamic layer has to borrow a non-MCP log and map its fields onto the dimensions.
2. **The best non-synthetic candidates, in order:**
   - **CLUE-LDS** [D12]: real Nextcloud logs, 50.5 M events, over 5,000 users, 1,910 days, CC BY
     4.0. It has user roles and IP geolocation. It has no attacks; the authors inject account
     hijacking by swapping user ids, and ship the code.
   - **GH Archive** [D14]: real public GitHub events per actor and repository since 2011. This is
     the same domain as our simulator. It has no reads, no IP, no client and no labels.
   - **The LANL enterprise datasets** [D4, D5, D7]: real, CC0, 58 days to 9 months. Only the 2015
     set has labels: 749 red-team authentication events, nearly all from one source host [D10].
   - **The flaws.cloud CloudTrail logs** [D11]: real AWS API calls with user agent and source IP,
     but mostly attackers sharing leaked keys.
   - **The RBA login dataset** [D13]: 33 M logins with IP, ASN, user agent and 87 labelled account
     takeovers in the original data. Its feature values are synthesized from real data.
3. **CERT is synthetic, benign and malicious alike** [D1, D3]. So is OpTC's background activity
   [D10]. TWOS, RUU and Schonlau are real but short or tiny. Use them only to compare with
   published work, never as the non-synthetic test.
4. **No dataset tests missing handshake (#15) or oversized request (#13) well.** Since the MCP
   `2026-07-28` revision removes `initialize` and sessions ([01-mcp-protocol.md](01-mcp-protocol.md)),
   #15 and session duration (#5) need their own argument, not a borrowed dataset.
5. **Commercial UEBA agrees with v4 on most mechanisms.** Microsoft Sentinel, Exabeam, Okta and
   Entra all score "first time / uncommon for this user". They learn for days or until a model
   converges before they score. They price a first access to a critical asset high, and they
   discount what an entity does often.
6. **Commercial UEBA differs from v4 in two ways.**
   - **Peer groups.** All three big UEBA products compare a user with peers built from directory
     groups or clustering. v4 lets other agents only *lower* a score (the org discount).
   - **Accumulation.** Exabeam and Splunk risk-based alerting *sum* risk over a session or 24 hours.
     v4 takes the *max* per call and has no accumulation across calls.
   Both are reviewer questions; [section 6](#6-implications-for-the-dynamic-layer) proposes tests.

## 1. How commercial UEBA builds baselines and scores

| Product | Baseline against | Windows and warm-up | Per-signal output | Aggregation |
|---|---|---|---|---|
| Microsoft Sentinel UEBA [V1, V2] | user, peers, tenant ("concentric circles") | per insight: 10 days ("uncommonly by user"), 30, 90 or 180 days ("first time"); burst of operations: 7 days | booleans per action, app, browser, country, device, ISP, resource; `InvestigationPriority` 0–10 per event | entity-rarity score + time-series score → `InvestigationPriority`; a separate ML `AnomalyScore` 0–1 over many events |
| Splunk UBA [V3–V6] | entity, HR / OU / behavioural / device peer groups | sliding window for batch models; peer groups rebuilt daily | anomaly with base, min and max score; scoring rules "Analysis of Baseline / Peer Group / Transfer" | threat rules and kill-chain models stitch anomalies into threats; end of life 2027-01-31 |
| Splunk ES risk-based alerting [V7, V8] | none (rule hits) | — | risk score per risk object | sum per object over 24 h > 100; ≥ 3 ATT&CK tactics and ≥ 4 sources over 7 days |
| Exabeam Advanced Analytics [V9–V14] | user history, org- or ML-defined peer groups | typically 60–90 days of logs; a model-based rule fires only after 80% confidence ("convergence") | rule points = anchor score × anomaly factor | sum of rule points per session; ≥ 90 is "notable" |
| Elastic ML [V15, V16] | the entity's own past, or the population (`over` field) | at least 20 buckets | `rare`, `freq_rare`, `time_of_day`, `time_of_week` | anomaly score per bucket (not covered here) |
| Okta behaviour detection [V17] | the user's last N successful sign-ins | N = 50 for IP and ASN, 20 for city, device, geo-location, 15 state, 10 country | New IP / ASN / City / State / Country / Geo-location / Device; velocity > 805 km/h | feeds sign-on policy; "can't deny access … based on behavior conditions", only step up |
| Entra ID Protection [V18] | the user's past sign-ins | "learning mode", at least 5 days; back to learning after long inactivity | unfamiliar IP, ASN, location, device, browser, tenant IP subnet; anomalous token; mass access to sensitive files | risk level per detection |
| AWS GuardDuty [V19] | each IAM user identity | not stated | "which factors of the API request are unusual for the user identity": user, location, API | one finding per anomalous request or burst; repeated remote hosts become "expected behavior" |

### Details that map onto v4

- **"First time" is not "risky".** Sentinel says so outright: a user's first Azure operation gets a
  *high* `InvestigationPriority` "because it's a first-time event" but a *low* `AnomalyScore`
  "because occasional first-time Azure actions are common" [V2]. v4 prices a never-used tool "by
  how often he starts new tools" (#7). That is the same correction, inside one score.
- **Peers.** Sentinel ranks each user's top 20 peers by TF-IDF over security groups and mailing
  lists, so smaller groups weigh more [V2]. Splunk UBA's behavioural peer groups cluster login
  activity, AD events and access sources and destinations [V4]. Exabeam's peer groups are a team,
  department or location, or ML-chosen per activity [V13]. All three need directory or HR data
  that an MCP server does not have.
- **The organisation as a dampener.** Sentinel has `FirstTimeActionPerformedInTenant` and
  `…UncommonlyUsedInTenant` for every insight type [V1]. v4's org discount uses the same signal
  the other way round. Something new for him that three other agents also started this week is an
  org-wide change, and is capped at 0.5.
- **First access to a critical asset.** In Exabeam's documentation, "the first login to a critical
  system by a specific user" adds 40 points to the session, against a notable line of 90 [V11,
  V14]. Entra's "mass access to sensitive files" fires only if the count is uncommon *for the user*
  and the files may be sensitive [V18]. Both price sensitivity × novelty, as v4's first-access floor
  (#8) does.
- **Habit discount.** Exabeam's anomaly factor depends on "the shape of the user's histogram, how
  often a rule is triggered, and the size of the user's peer group" [V12]. GuardDuty stops
  reporting a remote host it keeps seeing: "its machine learning (ML) model will identify this as
  an expected behavior" [V19]. v4's habit discount and daily learning are the same idea.
- **Time as a cycle.** Exabeam's third model type is "numerical time-of-week": Sunday 23:00 sits
  next to Monday 00:00 [V10]. Elastic offers `time_of_day` and `time_of_week` per entity [V15].
  v4 blends weekend hours (#6); a cyclic week is the alternative.
- **Client granularity.** Sentinel keeps both `UserAgent` and `UserAgentFamily` [V1]. Okta treats
  a browser change as a new device [V17]. v4 drops the client version (#10), as the HF MCP client
  table does when it deduplicates names [D28].
- **Network granularity.** Okta and Entra use the IP, the ASN and geography; Entra also uses the
  tenant's IP subnet [V17, V18]. None documents a fixed /16. See [section 3](#3-academic-work-that-matters)
  (Freeman, Wiefling) for evidence on levels.
- **Raise, don't block.** Okta's behaviours can only step a sign-in up to MFA, never deny it [V17].
  That matches v4's rule that the multiplier raises risk and never blocks on its own.

## 2. Aggregation: sum over time against max per call

Exabeam adds rule points within a session and alerts at 90 [V9, V11]. Splunk ES adds risk scores
per object over 24 hours and alerts above 100. Its second default rule counts distinct ATT&CK
tactics (≥ 3) and sources (≥ 4) over 7 days [V7, V8]. Splunk's guide calls the latter "excellent
for finding 'low and slow' attacks" [V8]. Splunk UBA stitches anomalies into threats with
kill-chain rules [V3].

v4 combines dimensions *within one call* by max. That is defensible: the strongest sign sets `M`,
and a call's `M` must be computable before the call runs. But v4 has **no accumulation across a
caller's calls**, so a caller who stays just below ×3 on every call never stands out. The daily
review list and `s2` partly cover this.

The max has a known statistical cost. Tippett's method, the minimum of n p-values, has null
distribution Beta(1, n), and it is "more sensitive to the smallest p-value" than the other
combiners [D24]. v4's rarity score is an empirical p-value ("this thing + everything rarer"), so
`max s` behaves like Tippett. With independent dimensions, P(min p < α) = 1 − (1 − α)ⁿ ≈ nα, so the
ordinary false-alarm rate grows about linearly with the number of dimensions. Correlation between
dimensions makes it grow less. Heard and Rubin-Delanchy compare six combiners and say when each is
optimal [D24]: a citation for "why max" beyond fuzzy OR.

## 3. Academic work that matters

| Work | What it gives the dynamic layer |
|---|---|
| Shashanka, Shen, Wang 2016, IEEE BigData [D22] | Canonical UEBA system paper (Niara). SVD-based anomaly scores per user, IP and device against *historical* and *peer* baselines. On one Jenkins use case over 3 months: 64 events, 39 alerts with confidence > 60. |
| Freeman et al. 2016, NDSS [D23] | Per-user feature rarity for logins (IP, user agent, time of day). The score is a product over features of `p(A|x_k) · p(x_k) / p(x_k | u, L)`, under feature independence. Smoothing reserves mass for unseen values, with backoff IP → ISP → country and the same for user agents. This is the closest published analogue of v4's Typical Footprint. |
| Wiefling et al. 2022, ACM TOPS [D13] | Real-world risk-based authentication: 3.3 M users and 31.3 M logins over a year. Feature weights: IP address 0.6 / ASN 0.3 / country 0.1, and user agent 0.53 full string / 0.27 browser / 0.19 OS / 0.01 device type. About 8 logins blocked 99.5% of targeted attackers; 4–6 were enough for naive and VPN attackers. Median 2 logins per user. |
| Glasser and Lindauer 2013, IEEE S&P Workshops [D3] | How CERT was generated (DARPA ADAMS; host sensor logs of a large organisation over 500 days), and the authors' own discussion of the limits of synthetic realism. |
| Tuor et al. 2017, AAAI AICS workshop [D18] | Unsupervised per user-day scoring on CERT r6.2, weekdays only. Anomaly scores are decomposed into per-feature contributions, which is v4's reason `d*`. |
| Le, Zincir-Heywood, Heywood 2020, IEEE TNSM [D19] | Granularity: user-day, user-week, user-session. Up to 85% of insiders detected at 0.78% false-positive rate with limited labels (supervised RF). It is a reference point for "per agent-day" reporting. |
| Homoliak et al. 2019, ACM CSUR [D20] | Survey and taxonomy of insider threats, including an overview of public datasets. |
| Schonlau et al. 2001, Statistical Science [D16]; Ben Salem and Stolfo [D17]; Harilal et al. 2017 [D15] | The masquerade-detection line and its datasets (Schonlau, RUU, TWOS). Ben Salem and Stolfo's critique: simulated masquerades made of other users' commands reduce the task to "author identification". |
| Landauer et al. 2022, IEEE BigData workshop [D12] | Argues that "simulations are unable to adequately induce the dynamic and unstable nature of real user behavior", and releases CLUE-LDS. |
| Anjum et al. 2021, ACM SACMAT [D9]; Larroche 2026, ANUBIS '26 (arXiv) [D10] | Documentation and evaluation pitfalls of OpTC and LANL; see [section 5](#5-pitfalls-of-these-datasets). |
| Arp et al. 2022, USENIX Security [D21] | General pitfalls: sampling bias (P1), label inaccuracy (P2), inappropriate measures (P7), base-rate fallacy (P8). P8's example: 99% TP at 1% FP with a class ratio 1:100 gives 100 false positives per 99 true positives. |

## 4. Public datasets with per-user event logs

**Real** means the benign traffic came from real people or systems. Labels are listed exactly as
the publisher provides them.

| Dataset | Real? | Content | Size and span | Labels | Licence and access |
|---|---|---|---|---|---|
| **CLUE-LDS** [D12] | yes | Nextcloud (hBOX) events: `time`, `uid`, `uidType`, `type` (49 event types: logins, file accesses, link shares, config changes …), `params` (paths, groups), `isLocalIP`, `role`, `location` | 50,522,931 events; > 5,000 users; 2017-07-07 – 2022-09-29 (1,910 days); 635 MB zip, 14.9 GB JSON | none; account hijacking injected by swapping `uid`s (code in repo) | CC BY 4.0, Zenodo DOI 10.5281/zenodo.7119953 |
| **GH Archive** [D14] | yes | public GitHub events: `type`, `actor`, `repo`, `org`, `payload`, `created_at`; 16 event types in GitHub's list | hourly archives since 2011-02-12; BigQuery | none | free download and BigQuery; licence not stated on the page (UNVERIFIED) |
| **LANL Comprehensive Multi-Source Events (2015)** [D4] | yes | authentication (`time, src user@domain, dst user@domain, src computer, dst computer, auth type, logon type, orientation, success`), process start/stop, DNS, flows, red team | 1,648,275,307 events; 12,425 users; 17,684 computers; 58 days; ~12 GB compressed; 1-second resolution, undisclosed start | `redteam.txt`: compromise events taken from the auth data (749 per [D9]) | CC0-style waiver; email and use form; DOI 10.17021/1179829 |
| **LANL Unified Host and Network (2017)** [D5, D6] | yes | Windows events 4624/4625/4634/4647/4648/4672/4688/4689/4768/4769/4770/4774/4776/4800–4803 …, with `UserName`, `LogonID`, `LogonType`, `Source`, `Destination`, `ProcessName`, `ParentProcessName`; NetFlow v9 | ~90 days (flows 89); 5,546,990,084 events per [D9] | none ("no specific malicious activity" [D9]) | CC0; email and use form |
| **LANL User–Computer Authentication Associations (2014)** [D7] | yes | `time, user, computer` for successful authentications | 708,304,516 events; 11,362 users; 22,284 computers; 9 months | none | form; DOI 10.11578/1160076 |
| **flaws.cloud CloudTrail** [D11] | yes (mostly attackers) | default multi-region CloudTrail: `userIdentity`, `eventTime`, `eventSource`, `eventName`, `sourceIPAddress`, `userAgent`, `requestParameters`, `resources`, `readOnly` … | 1,939,207 events; 2017-02-12 – 2020-10-07; 9,402 IPs; 8,811 user agents; 1,242 APIs; ~240 MB | none; one legitimate user (the owner, mostly root); everything else is CTF players | free download; licence not stated in the post (UNVERIFIED) |
| **RBA login dataset** [D13] | **synthesized from real** | per login: user ID, timestamp, IP, country, region, city, ASN, user agent, browser, OS, device type, RTT, success, `is attack IP`, `is account takeover` | > 33 M logins; > 3.3 M users; original Feb 2020 – Feb 2021 | attack IP (FireHOL match); account takeover (87 successful logins in the original, found by incident response) | CC BY 4.0; GitHub, Zenodo 6782156; "feature values are plausible, but still totally artificial" |
| **DARPA OpTC** [D8, D9] | background synthetic [D10] | eCAR endpoint events (`principal`, `object`, `action`, `properties`) for 11 object types, plus Zeek | 17,433,324,390 events; 500 of 1,000 hosts; ~1 TB compressed; fall 2019 | red-team ground-truth PDF only; "no explicit, event-level labels" [D10] | public domain, Distribution A |
| **CERT Insider Threat Test Dataset** r1–r6.2 [D1, D3] | **no, fully synthetic** | logon, device (removable media), HTTP, email, file, user attributes, psychometrics | r6.2: 4,000 users, 516 days, 135,117,169 events, 5 scenarios [D18]; all releases 87.23 GB | `answers.tar.bz2`: scenarios and insider user ids | CC BY 4.0, DOI 10.1184/R1/12841247.v1 |
| **TWOS** [D15] | yes (gamified) | keystrokes, mouse, host monitor (process, file, registry), network pcap, SMTP, logon, personality survey | 24 users; 5 days (March 2017); 320 h active | 12 masquerader sessions × 90 min; 5 possible traitor sessions × 120 min | by e-mail request with a data sharing agreement |
| **RUU** [D17] | yes | Windows host sensor: process, registry, GUI window, DLL activity | 34 users; mean ~7 days each (1–19); > 10 GB | 14 masqueraders × 15 min (capture-the-flag) | "available for download" per the report; terms UNVERIFIED |
| **Schonlau masquerade data** [D16] | yes | UNIX command names only (no arguments, no timestamps) | 50 users × 15,000 commands, in 150 blocks of 100 | from block 51 on, some blocks replaced by commands of users outside the 50 | download at schonlau.net; terms UNVERIFIED |
| Not per-user, for completeness: DARPA TC Engagement 5 [D25]; OTRF Security Datasets [D26]; Splunk BOTS v3 [D27] | — | provenance graphs; short simulated attack recordings; a pre-indexed CTF Splunk index (CloudTrail, O365, AAD sign-in …) | — | — | public domain; MIT/GPL text conflicts on the repo page; CC0 |

### Mapping fields to the 15 dimensions

**yes** = the field exists as needed; **proxy** = an analogue with a stated caveat; **no** = not
evaluable. Numbering as in [DIMENSION_FORMULAS.md](../DIMENSION_FORMULAS.md#the-dimensions).

| # | Dimension | CLUE-LDS | GH Archive | LANL 2015 | LANL 2017 | LANL 2014 | flaws.cloud | RBA | CERT (synthetic) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Call rate | yes | proxy: public write events only | yes | yes | yes | yes | proxy: logins | yes |
| 2 | Write rate | proxy: split `type` into read and modify | yes: almost every event is a write | no | no | no | yes: `readOnly` | no | proxy: file copy, email send |
| 3 | Breadth | yes: `params.path` (or its top folder) | yes: `repo` | yes: destination computer | yes: `Destination` / `LogHost` | yes: computer | yes: `resources` ARN, bucket | no | yes: PC, URL, file |
| 4 | Repetition | yes | yes | yes | yes | yes | yes | proxy: repeated logins | yes |
| 5 | Session duration | proxy: time since `login_successful` | no | proxy: LogOn/LogOff pairs | yes: 4624 → 4634 by `LogonID` | no | proxy: `sessionContext.creationDate` | no | yes: logon/logoff |
| 6 | Hour of day | yes: UTC plus location timezone | yes: UTC, user timezone unknown | yes: relative clock (see below) | yes: relative | yes: relative | yes | yes | yes |
| 7 | Tool | yes: `type` | yes: `type` + `payload.action` | proxy: auth type × logon type; process name | yes: `EventID` × `LogonType`; `ProcessName` | no | yes: `eventSource:eventName` | no | yes: activity type |
| 8 | Asset | yes: `params.path` | yes: `repo` | yes: destination computer | yes | yes | yes | no | yes |
| 9 | Network | proxy: city or country, `isLocalIP`; no IP | no | proxy: source computer (internal host) | proxy: `Source` | no | proxy: exact IP only (anonymization breaks prefixes) | yes: IP, ASN, geo | proxy: PC |
| 10 | Client | no (not a first-level field; UNVERIFIED in `params`) | no | proxy: authentication package | proxy: `ProcessName` / `ParentProcessName` | no | yes: `userAgent` | yes: user agent, browser, OS | no |
| 11 | Burst | yes | yes | yes | yes | yes | yes | yes: login bursts | yes |
| 12 | Sweep | yes | yes | yes | yes | yes | yes | no | yes |
| 13 | Oversized request | no | proxy: `payload` text length (comments, issue bodies) | no: flow bytes are per host | no | no | proxy: length of `requestParameters` | no | proxy: email size |
| 14 | Unsafe sequence | proxy: read of a sensitive path, then a share of another path; sensitivity must be assigned | proxy: merge without a review event ("unreviewed merge") | no | no | no | proxy: recon → policy change; sensitivity must be assigned | no | proxy: job-site browsing → removable copy |
| 15 | Missing handshake | proxy: actions without a recent login (sync clients may break it) | no | no | proxy: 4688 under a `LogonID` with no 4624 seen | no | proxy: calls with long-term keys and no session | no | proxy: activity with no logon |
| — | Usable labels | none; hijack injection | none | 749 red-team events | none | none | none (most traffic is attackers) | attack IP, 87 ATO | synthetic answers |

Notes on the matrix:

- **Relative clocks are enough for hour of day.** LANL's times count from epoch 1 with the real
  start hidden [D4, D7]. v4 compares a call's hour with *his own* past hours, so a constant
  offset does not change the score. Only "2 a.m." loses its literal meaning. Weekend blending needs
  the weekday, which should be recoverable from the weekly cycle (not checked).
- **CLUE is the only real dataset with roles and a long span together.** That makes it the place
  to test a peer-group arm against the org discount (`role`: consulting, administration,
  management, sales, technical, external [D12]).
- **GH Archive matches the simulator's domain, but only its write side.** Reads (`get_file`,
  `list_issues`) are never public events. So call rate there is "visible actions per hour", and
  the write-vs-read separation cannot be tested.
- **flaws.cloud inverts the base rate.** The identities `backup`, `Level6` and the `flaws` role
  were used by thousands of players with leaked keys [D11]. That is the stolen-token case: one
  identity, many places and programs. It suits network and client rarity and burst (one IP tried
  to start EC2 instances "over half a million times"), but not false alarms.
- **RBA covers only Footprint dimensions 9 and 10 plus burst**, but with real labels and ASN. It is
  the one dataset that can test /16 against ASN against exact IP directly. Whether its synthesized
  IPs keep prefix structure is UNVERIFIED.

## 5. Pitfalls of these datasets

- **CERT is synthetic throughout**: "synthetic background data and data from synthetic malicious
  actors" [D1]. The answer key comes from the same generator, so a detector can learn the
  generator. Turcotte et al. single CERT out as "entirely synthetic" [D6]. Secondary sources even
  disagree on basic counts: one table gives r6.2 2,500 users, while Tuor et al. give 4,000 (see
  UNVERIFIED). Use CERT only to compare with published numbers.
- **LANL 2015 labels are one intrusion.**
  - The 749 events are authentications only [D4], all in the first 30 days [D10].
  - "Almost all of them come from the same source host (C17693)" [D10]. Detecting C17693 detects
    the red team.
  - Larroche shows that published results depend on excluded accounts, authentication packages
    and downsampled benign users. Downsampling "unrealistically decreases the false positive
    rate" [D10].
  - He recommends no train/test overlap and keeping the last 28 days, which have no red team,
    for false-positive estimates [D10].
  - Only 58 days: v4's 90-day window does not fit. Use 14–21 days and report the sensitivity.
- **LANL 2017 and 2014 have no labels** [D9]: benign baselines only.
- **OpTC is short and partly synthetic.**
  - Benign data runs 19–23 September and red-team data 23–25 September [D9]. Larroche counts
    "synthetic background activity spanning 9 days" [D10]; the two counts differ.
  - There are no event-level labels [D10], and the `actor_id` field has known errors [D9].
  - A per-caller 90-day baseline is impossible.
- **flaws.cloud anonymization swaps every IP for a random one**, keeping only the format, so
  "IPs that you would expect to be originating in AWS are going to look like they are coming from
  elsewhere" [D11]. /16 and ASN grouping are therefore meaningless; only exact-IP rarity survives
  (my inference from the method). S3 and Lambda object logging was off, so data reads are missing.
- **RBA dataset values are "totally artificial"** although the statistics follow the original
  [D13]. The original was deleted. Users are sparse (median 2 logins), which stresses the warm-up.
- **CLUE has no attacks.** Swapping two users' ids tests "does a stranger look like a stranger",
  the same reduction Ben Salem and Stolfo criticise in Schonlau [D17]. It does not test a real
  agent misusing its own access. Paths are pseudonymised consistently, so sensitivity must be
  assigned by a rule (by folder or role), and that rule must be fixed before scoring.
- **Masquerade data is short.** TWOS has 5 days, RUU about 7 days per user, and Schonlau has no
  timestamps [D15–D17]. None supports a 90-day baseline.
- **General pitfalls** [D21]: sampling bias (one organisation, one product), label inaccuracy
  (red-team subsets, uid swaps), and the base-rate fallacy. Report per agent-day false-alarm rates
  and precision at the ×3 line, not ROC alone.
- **Humans are not agents.** Every dataset here logs people or their scripts. An agent's hour
  profile, burstiness and repetition differ by design: no sleep, loops, pagination. A held-out run
  checks that the *mechanisms* behave on real, messy behaviour. It does not calibrate thresholds
  for agents.

## 6. Implications for the dynamic layer

1. **Freeze v4, then run it once on held-out data.** The tolerance, ceilings, floors and discounts
   were chosen on the simulator ([Open decisions](../DIMENSION_FORMULAS.md#open-decisions), item 5).
   A held-out claim requires fixing them before any real dataset is scored. Write the metrics
   down in advance: ordinary agent-days at ×3, and injected episodes caught at ×3 and on the
   review list.
2. **Primary held-out benchmark: CLUE-LDS.** Map `uid` → agent, `type` → tool, the path or its top
   folder → asset, and city or country → network. Use the authors' uid-swap code for hijack
   episodes. Report the 13 dimensions it supports, and state that client (#10) and oversized
   request (#13) cannot be evaluated there.
3. **Domain check: GH Archive.** Take real organisations' public events for 180 days and score the
   last 90. This tests Cadence, tool, asset and sweep on real GitHub actors, including the
   "unreviewed merge" branch of #14. It can also re-fit the simulator's per-agent distributions
   (calls per day, repositories per hour, hour profiles), which answers "settings come from the
   simulation".
4. **Footprint check: RBA plus flaws.cloud.**
   - Use RBA's 87 takeovers and attack IPs to compare /16 against ASN against exact IP for #9,
     and full user agent against browser family for #10.
   - Freeman's backoff and Wiefling's weights (IP 0.6, ASN 0.3, country 0.1) suggest adding ASN
     as a fallback level to the /16 [D13, D23].
   - Use flaws.cloud to show that network, client and burst fire on a shared stolen identity.
5. **Enterprise check: LANL 2015 / 2017 / 2014.** Score breadth, asset rarity, hour of day and
   call rate on 12k real users. Report the 2015 red team as a single-intrusion case study under
   Larroche's protocol: keep all accounts, no temporal overlap, and false positives counted over
   all 58 days [D10]. Use 2014's 9 months to test the 90-day window itself.
6. **Say plainly what no dataset tests.** Missing handshake (#15) and oversized request (#13) have
   no good public analogue. Under MCP `2026-07-28`, #15 and session duration (#5) may not apply at
   all ([01-mcp-protocol.md](01-mcp-protocol.md)). Their evidence must come from the repo's own
   gateway logs, and the paper should say so.
7. **Answer "why no peer groups" with data.** Sentinel, Splunk UBA and Exabeam all use peers
   [V2, V4, V13]. Add a peer arm to the [ablation](../DIMENSION_FORMULAS.md#future-work-ablation-study):
   rarity among the same `role`, on CLUE. Then report whether letting peers *raise* scores costs
   false alarms against the org discount, which can only lower them.
8. **Add an accumulation arm.** Vendors alert on sums over a session or 24 h [V7, V9]. Test a daily
   per-agent sum, or a count of calls above 0.5, as a *review-list* signal, leaving the per-call
   `M` unchanged. This closes the "low and slow" gap without touching the max.
9. **Report false alarms against the number of dimensions.** With max/Tippett, each added dimension
   adds roughly its own ordinary false-alarm rate (≈ nα when independent) [D24]. The
   leave-one-out ablation should plot this. It is the honest cost of 15 dimensions.
10. **Revisit the warm-up length.** Vendors wait days or until convergence: Entra ≥ 5 days, Exabeam
    80% confidence, Elastic ≥ 20 buckets, Okta the last 10–50 sign-ins [V12, V15, V17, V18].
    Wiefling found about 8 logins enough [D13]. v4's warm-up is the first day only. Compare a
    count-based warm-up (≥ N calls) in the ablation; CLUE and RBA have many sparse users to test
    it on.
11. **Cite the vendor parallels as support, not proof.** First-time pricing (Sentinel), first
    critical access (Exabeam, 40 of 90), habit learning (GuardDuty, Exabeam) and cyclic time
    (Exabeam, Elastic) all match v4 mechanisms. Vendors publish no false-alarm rates, so they show
    common practice, not effectiveness.

## UNVERIFIED and open points

- **CERT r4.2 counts.** 1,000 users, 70 insiders, 32.77 M events and three scenarios come only from
  secondary journal tables, which disagree with each other on r6.2's user count. They were not
  checked against the release README inside the archive. r6.2's 4,000 users, 516 days and 135 M
  events are from Tuor et al. [D18].
- **CERT file list.** The exact files per release (for example an LDAP / org-structure file) were
  not read; Tuor et al. report six categorical user attributes.
- **Licences not stated on the page read.** GH Archive, flaws.cloud, the Schonlau data and RUU.
  A Kaggle mirror of flaws.cloud says Apache 2.0, but that is the mirror's own label.
- **CLUE event types.** Only `login_successful` and `file_accessed` were seen verbatim. The split
  into read and modify types, and whether `params` carries a client, must be checked in the data.
- **Synthesized RBA IPs.** Whether they keep prefix-to-ASN consistency is unknown.
- **OpTC duration.** [D9]'s table gives 6 days (benign 19–23 September, red team 23–25
  September); [D10] gives 9 days of background; not resolved.
- **Bibliographic details not opened.** Kent 2015 (the chapter LANL asks users to cite) and
  Hagberg et al. 2014 were not opened. Bian et al. (IEEE TNSM 2021) was read only as a PDF excerpt
  (749 events in the first 30 days, 299 red-team hosts); its author list and DOI were not checked.
- **Gateway proxies.** No dataset gives an MCP client's `initialize` behaviour. The #15 proxies
  above are analogies, not tests.

Count, second pass: **12 per-user datasets** were profiled (CLUE, GH Archive, LANL 2015, 2017 and
2014, flaws.cloud, RBA, OpTC, CERT, TWOS, RUU, Schonlau). Three non-per-user datasets and two MCP
sources were also checked. **48 sources were opened** (29 D, 19 V). Four cited items were not
opened or only partly (Kent 2015, Hagberg et al. 2014, Bian et al. 2021, the CERT release
README), and the 8 bullets above remain UNVERIFIED.

## Sources

All accessed 2026-10-25.

**Datasets and papers**

- [D1] Lindauer, B. *Insider Threat Test Dataset*, CMU KiltHub, CC BY 4.0, doi:10.1184/R1/12841247.v1. <https://kilthub.cmu.edu/articles/dataset/Insider_Threat_Test_Dataset/12841247>
- [D2] SEI dataset page. <https://www.sei.cmu.edu/library/insider-threat-test-dataset/>
- [D3] Glasser, J., Lindauer, B. "Bridging the Gap: A Pragmatic Approach to Generating Insider Threat Data." IEEE S&P Workshops 2013. doi:10.1109/SPW.2013.37. <https://www.ieee-security.org/TC/SPW2013/papers/data/5017a098.pdf>
- [D4] LANL. *Comprehensive, Multi-Source Cyber-Security Events.* doi:10.17021/1179829. <https://csr.lanl.gov/data/cyber1/>
- [D5] LANL. *Unified Host and Network Data Set.* <https://csr.lanl.gov/data/2017/>
- [D6] Turcotte, M., Kent, A., Hash, C. "Unified Host and Network Data Set." In *Data Science for Cyber-Security*, 2018. arXiv:1708.07518. <https://arxiv.org/abs/1708.07518>
- [D7] LANL. *User-Computer Authentication Associations in Time.* doi:10.11578/1160076. <https://csr.lanl.gov/data/auth/>
- [D8] Five Directions. *OpTC-data* (README, `ecar.md`). <https://github.com/FiveDirections/OpTC-data>
- [D9] Anjum, M. M., Iqbal, S., Hamelin, B. "Analyzing the Usefulness of the DARPA OpTC Dataset in Cyber Threat Detection Research." ACM SACMAT 2021. doi:10.1145/3450569.3463573; arXiv:2103.03080. <https://arxiv.org/abs/2103.03080>
- [D10] Larroche, C. "On fair and realistic performance evaluations for graph-based lateral movement detectors." ANUBIS '26; arXiv:2607.29390. <https://arxiv.org/abs/2607.29390>
- [D11] Piper, S. "Public dataset of Cloudtrail logs from flaws.cloud." Summit Route, 2020-10-09. <https://summitroute.com/blog/2020/10/09/public_dataset_of_cloudtrail_logs_from_flaws_cloud/>
- [D12] Landauer, M., Skopik, F., Höld, G., Wurzenberger, M. *CLUE-LDS*, Zenodo, doi:10.5281/zenodo.7119953; code <https://github.com/ait-aecid/clue-lds>; paper "A User and Entity Behavior Analytics Log Data Set for Anomaly Detection in Cloud Computing," IEEE BigData 2022 (BDA4CID workshop), doi:10.1109/BigData55660.2022.10020672.
- [D13] Wiefling, S., Jørgensen, P. R., Thunem, S., Lo Iacono, L. "Pump Up Password Security! Evaluating and Enhancing Risk-Based Authentication on a Real-World Large-Scale Online Service." ACM TOPS 26(1), 2022, doi:10.1145/3546069; arXiv:2206.15139; dataset <https://github.com/das-group/rba-dataset>, Zenodo record 6782156.
- [D14] GH Archive. <https://www.gharchive.org/>; GitHub event types. <https://docs.github.com/en/rest/using-the-rest-api/github-event-types>
- [D15] Harilal, A. et al. "TWOS: A Dataset of Malicious Insider Threat Behavior Based on a Gamified Competition." MIST@CCS 2017, doi:10.1145/3139923.3139929; access <https://github.com/ivan-homoliak-sutd/twos>
- [D16] Schonlau, M. et al. "Computer Intrusion: Detecting Masquerades." *Statistical Science* 16(1):58–74, 2001. doi:10.1214/ss/998929476.
- [D17] Ben Salem, M., Stolfo, S. J. RUU dataset and "Data Collection and Analysis for Masquerade Attack Detection: Challenges and Lessons Learned," Columbia technical reports. <https://academiccommons.columbia.edu/doi/10.7916/D8ZS34BX/download>; <https://mice.cs.columbia.edu/getTechreport.php?format=pdf&techreportID=1453>
- [D18] Tuor, A. et al. "Deep Learning for Unsupervised Insider Threat Detection in Structured Cybersecurity Data Streams." AAAI AICS workshop 2017; arXiv:1710.00811.
- [D19] Le, D. C., Zincir-Heywood, N., Heywood, M. I. "Analyzing Data Granularity Levels for Insider Threat Detection Using Machine Learning." IEEE TNSM 17(1):30–44, 2020. doi:10.1109/TNSM.2020.2967721.
- [D20] Homoliak, I. et al. "Insight Into Insiders and IT: A Survey of Insider Threat Taxonomies, Analysis, Modeling, and Countermeasures." ACM CSUR 52(2), 2019. doi:10.1145/3303771.
- [D21] Arp, D. et al. "Dos and Don'ts of Machine Learning in Computer Security." USENIX Security 2022. <https://www.usenix.org/conference/usenixsecurity22/presentation/arp>
- [D22] Shashanka, M., Shen, M.-Y., Wang, J. "User and Entity Behavior Analytics for Enterprise Security." IEEE BigData 2016. doi:10.1109/BigData.2016.7840805.
- [D23] Freeman, D. M., Jain, S., Dürmuth, M., Biggio, B., Giacinto, G. "Who Are You? A Statistical Approach to Measuring User Authenticity." NDSS 2016. doi:10.14722/ndss.2016.23240.
- [D24] Heard, N. A., Rubin-Delanchy, P. "Choosing between methods of combining p-values." *Biometrika* 105(1):239–246, 2018. doi:10.1093/biomet/asx076.
- [D25] DARPA I2O. *Transparent Computing Engagement 5 Data Release.* <https://github.com/darpa-i2o/Transparent-Computing>
- [D26] OTRF. *Security Datasets.* <https://github.com/OTRF/Security-Datasets>
- [D27] Splunk. *Boss of the SOC v3 dataset.* <https://github.com/splunk/botsv3>
- [D28] *evalstate/mcp-clients* (MCP client names, versions, capabilities seen at huggingface.co/mcp). <https://huggingface.co/datasets/evalstate/mcp-clients>
- [D29] *workspace-tools-mcp* research honeypot (README findings only; no released traffic found). <https://github.com/brian-mitchell-sec/workspace-tools-mcp>

**Vendor documentation**

- [V1] Microsoft. *Microsoft Sentinel UEBA reference* (ms.date 2025-08-28). <https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference>
- [V2] Microsoft. *Advanced threat detection with UEBA in Microsoft Sentinel* (ms.date 2025-12-15). <https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics>
- [V3] Splunk. *Splunk UBA models overview* (5.4.5). <https://help.splunk.com/en/security-offerings/splunk-user-behavior-analytics/use-splunk-user-behavior-analytics/5.4.5/splunk-uba-models/splunk-uba-models-overview>
- [V4] Splunk. *Review Peer Groups in Splunk UBA* (5.4.5). <https://help.splunk.com/en/security-offerings/splunk-user-behavior-analytics/use-splunk-user-behavior-analytics/5.4.5/assess-security-posture/review-peer-groups-in-splunk-uba>
- [V5] Splunk. *Customize anomaly scoring rules* (5.4.5). <https://help.splunk.com/en/security-offerings/splunk-user-behavior-analytics/administer/5.4.5/customize-splunk-uba/customize-anomaly-scoring-rules>
- [V6] Splunk. *About Splunk User Behavior Analytics* (5.4.4; end of life 2027-01-31). <https://help.splunk.com/en/security-offerings/splunk-user-behavior-analytics/plan-and-scale/5.4.4/plan-and-scale-your-splunk-uba-deployment/about-splunk-user-behavior-analytics>
- [V7] Splunk. *Default risk incident rules in Splunk Enterprise Security* (7.3). <https://help.splunk.com/en/splunk-enterprise-security-7/risk-based-alerting/7.3/identify-threat/default-risk-incident-rules-in-splunk-enterprise-security>
- [V8] Splunk. *The Essential Guide to Risk-Based Alerting* (PDF). <https://www.splunk.com/en_us/pdfs/gated/ebooks/the-essential-guide-to-risk-based-alerting.pdf>
- [V9] Exabeam. *How Advanced Analytics Works.* <https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/understand-the-basics-of-advanced-analytics/how-advanced-analytics-works.html>
- [V10] Exabeam. *How Exabeam Models Work.* <https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/configure-rules/how-exabeam-models-work.html>
- [V11] Exabeam. *What Is an Exabeam Rule?* <https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/configure-rules/what-is-an-exabeam-rule-.html>
- [V12] Exabeam. *Get to Know a User Profile.* <https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153664-get-to-know-a-user-profile.html>
- [V13] Exabeam. *Configure Advanced Analytics* (i56). <https://docs.exabeam.com/en/advanced-analytics/i56/advanced-analytics-administration-guide/125371-configure-advanced-analytics.html>
- [V14] Exabeam. *Welcome to the Advanced Analytics Homepage* (i56). <https://docs.exabeam.com/en/advanced-analytics/i56/advanced-analytics-user-guide/113538-welcome-to-the-advanced-analytics-homepage.html>
- [V15] Elastic. *Time functions.* <https://www.elastic.co/docs/reference/machine-learning/ml-time-functions>
- [V16] Elastic. *Rare functions.* <https://www.elastic.co/docs/reference/machine-learning/ml-rare-functions>
- [V17] Okta. *About behavior detection.* <https://help.okta.com/oie/en-us/content/topics/security/behavior-detection/about-behavior-detection.htm>
- [V18] Microsoft. *What are risk detections? – Microsoft Entra ID Protection* (ms.date 2026-10-21). <https://learn.microsoft.com/en-us/entra/id-protection/concept-identity-protection-risks>
- [V19] AWS. *GuardDuty IAM finding types.* <https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-iam.html>
