# Commercial UEBA risk scoring, and behaviour analytics for AI agents and MCP

State as of 2026-11-04. Part A covers how commercial UEBA products document their scoring. Part B covers work that baselines the behaviour of AI agents over time and flags or scores deviations. The reference point throughout is our framework: the MCP server is the protected asset and agents are the threat. A gateway scores each call (static tool risk x runtime factors) and multiplies it by a bounded behaviour multiplier (x0.7-5). The multiplier comes from that agent's own past behaviour, keyed by agent id only, over about 90 active days, plus a learned per-agent policy of limits per tool and required steps.

Source-quality legend: **[DOC]** official product documentation; **[PR]** vendor press release or marketing (claims, not verified behaviour); **[PAPER]** arXiv preprint, verified to exist through the arXiv API on 2026-11-04 (none of the arXiv works below lists a peer-reviewed venue); **[SNIPPET]** detail taken from a search-engine excerpt of the source and not read in full.

## A. Documented scoring mechanics of commercial UEBA products

### Takeaway

Every major product follows the same pattern. Detections or anomalies each carry a score, and the scores are summed or near-summed per entity over a fixed window (a session, 24 h, 7 d or 30 d). The total is then compared against a threshold or normalised across the population. Only Exabeam documents a per-rule multiplicative factor that is learned from the entity's own history (anchor score x anomaly factor). Context multipliers (Splunk risk factors, Elastic asset-criticality weights 0.5-2, Google closed-alert coefficient) are set by admins, not learned. No vendor documents a bounded behaviour multiplier that can go below 1 for familiar behaviour, as our x0.7 floor does.

### Cited Findings

**Exabeam Advanced Analytics / New-Scale Analytics** [DOC]
- How a session is scored: the risk engine "treats each session as a container and assigns risk scores to the events that are flagged as anomalous. As the sum of event risk scores reach a threshold (a default value of 90), incidents are automatically generated" — [Exabeam docs, How Advanced Analytics Works (undated, accessed 2026-11-04)](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/understand-the-basics-of-advanced-analytics/how-advanced-analytics-works.html)
- Notable users and assets are those whose session score "met or exceeded the configured threshold (default is 90)". The list shows only each user's highest-scoring session, over a selectable window of 1 day to 3 months — [Exabeam docs, Advanced Analytics homepage (undated)](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153651-welcome-to-the-advanced-analytics-homepage.html)
- Per-event formula: the total risk score is "the anchor score multiplied by the anomaly factor". The anchor score is fixed per rule. The anomaly factor "measures the degree to which the action was anomalous for the user ... calculated in part by the shape of the user's histogram, how often a rule is triggered, and the size of the user's peer group." Fact-based rules carry no model confidence. Some events reduce risk; for example, an account lockout of the user's own workstation shows a down arrow. The risk-trend chart is drawn on a 0-100 scale. A session is "all user activity, starting from the time they log in until the time they log out, in a 24 hour period" — [Exabeam docs, Get to Know a User Profile (i56, undated)](https://docs.exabeam.com/en/advanced-analytics/i56/advanced-analytics-user-guide/113551-get-to-know-a-user-profile.html)
- Risk transfer between sessions: risk from sequences and daily feeds (for example, a malicious web domain) is transferred to the session. If the activity happened outside an open session, it goes to the user's *next* session — [same page](https://docs.exabeam.com/en/advanced-analytics/i56/advanced-analytics-user-guide/113551-get-to-know-a-user-profile.html)
- Baseline length: a deployment "begins by examining typically 60-90 days of an organization's logs" before it starts scoring sessions — [Exabeam docs, Configure Advanced Analytics (i56)](https://docs.exabeam.com/en/advanced-analytics/i56/advanced-analytics-administration-guide/125371-configure-advanced-analytics.html)
- Down-weighting of common anomalies: Exabeam uses "Bayesian statistics to further highlight unusual anomalies and de-emphasize those that occur more commonly", sets reference scores by security exposure, and compares across users to normalise behaviour — [Exabeam Smart Timelines white paper (undated)](https://www.exabeam.com/wp-content/uploads/EXA_WP_Smart-Timelines-1.pdf). Rule scores in a session are summed and "adjusted based on historical data and trends if Histogram shaping and Bayesian scoring are enabled" — [Exabeam blog, 2020-07-15](https://www.exabeam.com/blog/siem-trends/exabeam-advanced-analytics-tips-targeted-search-and-tuning-rules/)

**Splunk Enterprise Security, Risk-Based Alerting (RBA)** [DOC]
- Building blocks: risk rules write risk events to a risk index. Each event carries a risk object (system, user or other), a risk score and an optional threat object. "The aggregated risk score of an asset or identity is the sum of all the risk scores for risk events in the risk index that apply to the specific asset or identity over a period of time." Risk factors "add or multiply risk scores", for example multiplying by 1.5 for a privileged administrator — [Splunk ES 7.3 docs, How RBA works (updated 2025-07-14)](https://help.splunk.com/en/splunk-enterprise-security-7/risk-based-alerting/7.3/introduction/how-risk-based-alerting-works-in-splunk-enterprise-security)
- Default risk incident rules:
  - "Risk Threshold Exceeded For Object Over 24 Hour Period": `risk_score_sum > 100`.
  - "ATT&CK Tactic Threshold Exceeded For Object Over Previous 7 days": `tactic_count >= 3 AND source_count >= 4`, described as the model for catching "low and slow" attacks.
  - Example alerts also include "Events from multiple sourcetypes over 3 days".
  - Sources: [Splunk Guide to RBA (PDF, undated)](https://www.splunk.com/en_us/pdfs/gated/ebooks/the-splunk-guide-to-risk-based-alerting.pdf); [Splunk ES 8.5 docs (updated 2026-06-16)](https://help.splunk.com/en/splunk-enterprise-security-8/user-guide/8.5/mission-control/analyze-risk-with-risk-based-alerting-in-splunk-enterprise-security)
- Severity bands on the 24-hour sum: <=100 low; 100-250 medium; 250-500 high; >500 critical. The SPL is `stats sum(calculated_risk_score) as risk_score_sum ... by risk_object | where risk_score_sum > 100` — [Splunk ES 7.3, Generate risk notables (updated 2025-07-14)](https://help.splunk.com/en/splunk-enterprise-security-7/risk-based-alerting/7.3/scenario-1-ram-isolates-threats-using-risk-based-alerting/generate-risk-notables-using-risk-incident-rules)
- Score scale:
  - Each risk event's score combines impact and confidence; for example, impact 80 and confidence 70 give 56.
  - Shipped searches assign scores of 20-100 (20 info, 40 low, 60 medium, 80 high, 100 critical).
  - "Splunk Enterprise Security does not define an upper limit for the total risk score of an identity or asset."
  - Source: [Splunk ES 7.1 docs, How risk scores work](https://docs.splunk.com/Documentation/ES/7.1.0/RBA/Analyzerisk)
- ES 8.x "finding-based detections" can group findings by "Cumulative entity risk" with an "is greater than" threshold. A score of 0 keeps an event as context without raising risk — [Splunk ES 8.6 docs, risk modifiers (updated 2026-07-20)](https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.6/risk-based-alerting/assign-risk-using-risk-modifiers-in-splunk-enterprise-security)

**Microsoft Sentinel UEBA** [DOC]
- What is profiled: UEBA builds "dynamic behavioral profiles for users, hosts, IP addresses, applications, and other entities". It scores deviation from the entity's own history, from its peer group and from organisation-wide patterns — [Microsoft Learn, UEBA in Sentinel (accessed 2026-11-04)](https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics)
- Two documented scores:
  - `InvestigationPriority`, 0-10, near real time, per event. It combines an Entity Anomaly Score (rarity of user, device or country) with a Time Series Score (spikes over time).
  - `AnomalyScore`, 0-1, batch, per behaviour, from an ML detector trained on the workspace's telemetry.
  - The two can disagree. Microsoft's example is a first-time Azure operation, which gets high priority but a low anomaly score.
  - Source: [same page](https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics)
- Peer groups and display windows: `UserPeerAnalytics` ranks each user's top 20 peers by security-group and mailing-list membership using TF-IDF, so smaller groups weigh more. User pages show the "top three anomalies from the past 30 days" — [same page](https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics)
- Lookback: "User activities are analyzed against a baseline that is dynamically compiled each time it's used. Each activity has its own defined lookback period" — [Microsoft Learn, UEBA reference](https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference)
- Non-human identities as inputs: UEBA sources include `AADServicePrincipalSignInLogs` and `AADManagedIdentitySignInLogs` (both preview), plus AWS, GCP and Okta. The Sentinel experience in the Azure portal is retired after 2027-03-31 — [UEBA reference](https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference)

**Microsoft Entra ID Protection (users, workload identities)** [DOC]
- Sign-in and user risk detections are labelled real-time or offline, for example atypical travel, unfamiliar sign-in properties and anomalous token. The atypical-travel detection "uses adaptive learning to learn a new user's sign-in behavior" — [Microsoft Learn, What are risk detections](https://learn.microsoft.com/en-us/entra/id-protection/concept-identity-protection-risks)
- Workload identities (service principals): the "Suspicious Sign-ins" detection "learns the baselines sign-in behavior for workload identities ... takes between 2 and 60 days". It then fires on unfamiliar IP/ASN, target resource, user agent, hosting change, country or credential type. "Anomalous service principal activity" baselines administrative behaviour; "Suspicious API Traffic" flags abnormal Graph traffic or directory enumeration. Managed identities are out of scope — [Microsoft Learn, Securing workload identities](https://learn.microsoft.com/en-us/entra/id-protection/concept-workload-identity-risk)

**Elastic Security entity risk scoring** [DOC]
- What is scored and when: hosts, users and services, from the last 30 days of alerts by default, recalculated hourly. Only entities in the entity store are scored. Alert risk scores are aggregated so that "alerts with higher risk scores contribute more" — [Elastic docs, Entity risk scoring (current, accessed 2026-11-04)](https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-risk-scoring)
- Modifiers:
  - Asset-criticality weights: low 0.5, medium 1, high 1.5, extreme 2.
  - Privileged-user weight: 2.
  - Watchlist membership is applied "using a Bayesian update model".
  - Final score is 0-100, with levels <20 unknown, 20-40 low, 40-70 moderate, 70-90 high, >90 critical.
  - Resolution groups pool all members' alerts and take the highest criticality.
  - Source: [same page](https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-risk-scoring)

**Google Security Operations (Chronicle) Risk Analytics** [DOC]
- Formula: base entity risk = (maximum finding risk score) + weighting x (sum of the remaining findings' scores). The default weighting is 0.2, adjustable 0-1: 0 gives max-only, 1 gives a plain sum.
  - Normalised score: min-max scaled across all entities to 1-1000; entities with zero risk are excluded.
  - Defaults: detection risk score 15 (range 0-1000); closed-alert coefficient 1 (range 0-1).
  - Google also applies "risk score modification with TTL" multipliers.
  - Source: [Google SecOps docs, Risk Analytics overview (accessed 2026-11-04)](https://docs.cloud.google.com/chronicle/docs/detection/risk-analytics-overview)
- Windows and deltas: risk windows are, for example, 24 hours or 7 days. `riskDelta` is the percentage change from the previous window, capped at 200%. The raw score is unbounded and the normalised score lies in 0-1000 — [Google SecOps API, entityRiskScores.query](https://docs.cloud.google.com/chronicle/docs/reference/rest/v1alpha/projects.locations.instances.entityRiskScores/query); [EntityRisk type](https://docs.cloud.google.com/chronicle/docs/reference/rest/Shared.Types/EntityRisk). `lastResetTime` supports "UEBA risk score reset based deduplication" for risk-based meta rules — [EntityRisk type](https://docs.cloud.google.com/chronicle/docs/reference/rest/Shared.Types/EntityRisk)

**Securonix** (scoring mechanics not found in public docs)
- Securonix's public UEBA/AEBA product page promises a "prioritized risk narrative" and detection of "deviations from individual or peer-group patterns". It gives no formula, decay or threshold — [Securonix UEBA page (2026)](https://www.securonix.com/products/ueba/)
- The method Securonix has patented combines an entity's inherent risk with a composite threat risk score, built from combinations of threat indicators along a kill chain — [US 9,800,605 B2, "Risk scoring for threat assessment", assignee Securonix](https://patents.google.com/patent/US9800605) [SNIPPET]

**CrowdStrike Falcon Identity Protection** (internals not publicly documented)
- A partner integration documents the score as 0-1 (1 = maximum risk) and converts it as |1 - score| x 1000 — [Netskope docs, CrowdStrike Identity Protection plugin](https://docs.netskope.com/en/crowdstrike-falcon-identity-protection-plugin-for-user-risk-exchange.html) [SNIPPET]. CrowdStrike describes its Zero Trust Risk Score as a dynamic score from "the activities and the behavior of a user or computer account" — [CrowdStrike white paper page (undated)](https://www.crowdstrike.com/en-us/resources/white-papers/falcon-zero-trust-risk-score/) [SNIPPET]

**Palo Alto Networks SaaS Security (one documented decay example)**
- In Palo Alto's Behavior Threats user risk scoring, an incident's influence "reduces by approximately half every 30 days". Policy weights run 1-10 — [Palo Alto docs, User Risk Scoring](https://docs.paloaltonetworks.com/saas-security/behavior-threats/user-risk-scoring) [SNIPPET]

### Inferences

- **Aggregation shape.** Splunk uses a plain sum over 24 h with no upper limit. Exabeam sums per session against a threshold of 90. Google uses max + 0.2 x the rest, which saturates more slowly than a sum. Elastic uses a weighted aggregate mapped to 0-100. Our framework multiplies a per-call score by a bounded behaviour factor rather than accumulating additive risk per entity. It is therefore closer to Exabeam's *per-event* anchor x anomaly-factor than to any vendor's *per-entity* total. A paper should say the two differ: we price each call, while UEBA ranks entities for analyst triage.
- **Learned versus configured multipliers.** Exabeam's anomaly factor is the only documented multiplier learned from the entity's own history (histogram shape, rule-trigger frequency, peer-group size). Splunk risk factors, Elastic criticality and privileged-user weights, and Google's closed-alert coefficient are all admin-set. Exabeam's Bayesian de-emphasis of common anomalies and its risk-reducing events are the nearest precedent for our x0.7 reward of familiar behaviour. No vendor documents a below-1 behaviour multiplier with explicit bounds.
- **Windows.**
  - Splunk: 24 h, 3 d, 7 d.
  - Google: 24 h or 7 d.
  - Elastic: 30 d of alerts.
  - Sentinel: per-activity lookback, top anomalies over 30 d.
  - Exabeam: 60-90 d initial baseline.
  - Entra workload identities: 2-60 d learning.
  - Our 90 active days sits at the long end, close to Exabeam's initial baseline. Using *active* days rather than calendar days is not documented by any vendor (see Gaps).
- **Peer groups.** Sentinel (TF-IDF top 20), Exabeam (peer-group size inside the anomaly factor) and Securonix use peer groups. Our framework, keyed by agent id only, has none. That is a defensible simplification, but reviewers who know UEBA will ask about it.

### Gaps

- Sentinel's per-activity lookback lengths (the "Baseline" column of the UEBA reference table) were cut off in the fetched page and are not reported here.
- Elastic's exact weighting function for "higher scores contribute more" is not on the current page. I did not verify the Riemann-zeta weighting that older Elastic versions documented.
- Splunk UBA (the separate ML product with 0-10 anomaly and threat scores) was not researched. I found no current official documentation in the time available.
- Securonix and CrowdStrike do not publish their scoring internals. The patent and partner documents are indirect evidence only.
- No vendor documents scoring over *active* days, or bounds on a behaviour multiplier.

## B1. Academic work that baselines AI-agent behaviour over time (papers first)

### Takeaway

The literature splits into six families:

1. Learned behaviour models from benign traces, enforced at runtime: TraceAegis, Praetor, AgentGuard, ProbGuard, TriCEGAR.
2. Drift and statistical-process-control monitors over per-agent or per-goal baselines: MI9, Agent Drift, AMDM.
3. Reputation and trust scores that update with each agent's history, mostly in multi-agent LLM systems.
4. Stateful or cumulative monitors across turns or accounts.
5. Server-side behavioural fingerprinting of agents.
6. MCP-specific detectors, which mostly score sessions or graph windows rather than an agent's long history.

**None of the verified works combines all three of our ingredients**: a per-call static x runtime price, a bounded multiplier learned from one agent's long history, and keying by agent id only. The closest single pieces are MI9 (per-goal baselines, JSD/Mann-Whitney drift, conservative cold-start thresholds, graduated containment), Praetor (gateway-enforced automaton of permitted tool sequences and parameter bounds learned from benign telemetry) and AegisMCP (MCP-specific streaming graph detector with time-to-live novelty).

### Cited Findings

#### Per-work dimension table

Abbreviations: B = behaviour, S = session, MAS = multi-agent system.

| # | Work (date, ID) | Entity baselined | History keyed by | What is scored | Bounding / aggregation | Cold start | Evaluation | MCP? |
|---|---|---|---|---|---|---|---|---|
| 1 | **MI9** runtime governance (2025-08-05, v4 2025-11-18; [2508.03858](https://arxiv.org/abs/2508.03858)) | Agent behaviour *per goal*: frequency distributions of event types, tool usage, sequence traits | Agent objective (goal); pooling across agents not stated | Jensen-Shannon divergence (discrete sequences) + Mann-Whitney U (continuous metrics) under sliding-window SPC with variance-based adaptive thresholds; FSM conformance; Agency-Risk Index ARI in [0,1], 4 tiers | Drift feeds a risk-tier-weighted escalation controller over 4 containment levels (monitor, planning intervention, tool restriction, execution isolation) | Transfer from similar objectives; otherwise conservative thresholds that tighten as confidence grows | 1,033 synthetic scenarios (Gemini-generated, Gemini-judged); detection 99.81%, FPR 0.0121%; not validated on live traces | No |
| 2 | **Agent Drift / Agent Stability Index** (2026-01-07; [2601.04170](https://arxiv.org/abs/2601.04170)) | Multi-agent workflow behaviour, 12 dimensions incl. tool-usage patterns | Workflow | ASI composite; [SNIPPET] first 20 interactions as baseline; chi-squared on tool-invocation frequencies over sliding windows; Levenshtein distance on tool sequences | Composite index | Early-window baseline | Simulation and theory only | No |
| 3 | **AMDM**, Adaptive Monitoring of agentic AI (2025-08-28, v3; [2509.00115](https://arxiv.org/abs/2509.00115)) | System-level metric axes | Monitored system | Per-axis EWMA thresholds + joint Mahalanobis distance | Normalised multi-axis | Not stated | Goal-drift detection latency 12.3 s to 5.6 s; FPR 4.5% to 0.9% vs static thresholds | No |
| 4 | **AAGATE** governance platform (2025-10-29; [2510.25863](https://arxiv.org/abs/2510.25863)) | "Per-agent behavioral fingerprints with anomalyScore" | Agent | Isolation Forest + Markov chains; feeds an SSVC-style decision tree (track, alert, quarantine); AIVSS vectors | Thresholds unspecified | Not stated | None reported | No |
| 5 | **AgentGuard** (2025-09-28; [2509.23864](https://arxiv.org/abs/2509.23864)) | Agent I/O abstracted into events | Agent under observation | Online-learned MDP + probabilistic model checking ("Dynamic Probabilistic Assurance") | Probabilities of properties | Online learning | Framework paper | No |
| 6 | **TriCEGAR** (2026-01-30; [2601.22997](https://arxiv.org/abs/2601.22997)) | Agent lifecycle events | Agent | Learns AgentGuard's state abstraction from traces (predicate trees, counterexample refinement) | Same as above | Removes hand-made abstraction | Framework implementation | No |
| 7 | **ProbGuard** (2025-08-01, v4 2026-08-03; [2508.00500](https://arxiv.org/abs/2508.00500)) | Symbolic agent states | Task/domain | DTMC learned from traces; intervene when P(safe) is below a user threshold | Probability in [0,1] | Needs traces | Robotics and web-agent domains | No |
| 8 | **TraceAegis** (2025-10-13; [2510.11203](https://arxiv.org/abs/2510.11203)) | Stable "execution units" + behavioural rules from benign traces | Agent application/scenario | Violations of hierarchical order and semantic-consistency constraints | Rule violation | Needs benign traces per scenario | TraceAegis-Bench: 2 scenarios x (1,300 benign + 300 abnormal) | Uses agent traces; [SNIPPET] gateway logs from MCP-based agents |
| 9 | **Praetor**, "Enforcing Benign Trajectories" (2026-04-29; [2604.26274](https://arxiv.org/abs/2604.26274)) | Verified benign tool-call telemetry compiled into a parameterised DFA (permitted sequences, contexts, parameter bounds) | Deployment/workflow | Gateway O(1) state-transition lookup per call | Allow/deny | Needs verified benign telemetry | Agent Security Bench: 5.6% macro ASR (2.2% in structured workflows vs 12.8% for Aegis); 2.2 ms/call; 2.0% benign task failure; 18% evasion via synonym substitution on continuous parameters | Gateway-based, protocol-agnostic |
| 10 | **AegisMCP** (2025-10-22, v2; [2510.19462](https://arxiv.org/abs/2510.19462)) | Streaming heterogeneous temporal graph over agents, MCP servers, tools, devices, remotes, sessions | Graph triples (src_type, etype, dst_type) + session DAG | Binary TTL novelty (triple unseen for longer than Δ) + edge, DAG, attribute and structure scores, linearly fused | Dual thresholds with hysteresis (none, observe, high); escalators (install, then egress to a new domain) | Self-supervised pretraining on benign windows; runtime warm-up not described | Synthetic 24-48 h smart-home runs; AUROC 0.985, AP 0.947, 55.7% recall at 2% FPR; 0.69 ms P95/window | **Yes**; threat = misled agent acting via MCP |
| 11 | **Content-aware attack detection in MCP tool-call traffic** (2026-05-11, v3; [2605.11053](https://arxiv.org/abs/2605.11053)) | One agent session as a graph (calls as nodes, sequential and data-flow edges) | Session | GNN/XGBoost session classification with argument/response embeddings | Session label | Supervised | RAS-Eval, ATBench | **Yes**; session-level, no long history |
| 12 | **ADR**, Uber (2026-05-17; [2605.17380](https://arxiv.org/abs/2605.17380)) | Per-session telemetry (prompts, reasoning, MCP calls, environment) | Session/endpoint; no cross-session baseline | Two-tier LLM triage + reasoning agent | Per-event decision | n/a | >10 months in production, 7,200 hosts, >10k sessions/day; ADR-Bench F1 0.800 at zero FPs | **Yes**; mostly external-manipulation threat model |
| 13 | **Detecting Silent Failures in Multi-Agentic Trajectories** (2025-11-06; [2511.04032](https://arxiv.org/abs/2511.04032)) | Trajectories | Trajectory | XGBoost (supervised) and SVDD (semi-supervised) anomaly detection | Per-trajectory | n/a | 4,275 + 894 trajectories; accuracy up to 98% and 96% | No |
| 14 | **SentinelAgent** (2025-05-30; [2505.24201](https://arxiv.org/abs/2505.24201)) | Dynamic execution graphs of MAS interactions | Run | Node, edge and path anomalies + LLM oversight agent | Per-run | n/a | Case studies | No |
| 15 | **Agent-ToM** (2026-05-22; [2605.24216](https://arxiv.org/abs/2605.24216)) | "Task-consistent behavioral baselines" per trajectory; persistent "semantic guardrail memory" across episodes | Task; memory shared across episodes | LLM theory-of-mind deviation judgement | Per-trajectory | Memory distilled at training time | SHADE-Arena, CUA-SHADE-Arena | No |
| 16 | **A-Trust** (2025-06-03, v2 2026-04-14; [2506.02546](https://arxiv.org/abs/2506.02546)) | Messages from each agent; per-agent trust records | Agent (in an MAS) | Attention-based trust over 6 dimensions | Trust record | [SNIPPET] detection starts only after 20 queries | [SNIPPET] 100% agent detection for considered attacks | No |
| 17 | **Credibility scoring** (2025-05-30; [2505.24239](https://arxiv.org/abs/2505.24239)) | Agent contributions | Agent | Credibility in [0,1], "learned gradually based on the past contributions" | Weighted aggregation of outputs | Gradual | Multiple tasks, incl. adversary-majority | No |
| 18 | **DRF** (2025-09-06; [2509.05764](https://arxiv.org/abs/2509.05764)) | Agent honesty and capability | Agent | Reputation from an interactive rating network + UCB selection; [SNIPPET] per-round score with decay | Reputation | UCB exploration | Reasoning and code tasks | No |
| 19 | **DART** (2026-09-01; [2609.05529](https://arxiv.org/abs/2609.05529)) | Post-execution behavioural evidence | Agent (blockchain-anchored) | Historical reputation in task allocation | Reputation + quarantine | n/a | [SNIPPET] 150 rounds, 22 agents (3 malicious from round 30); persistent adversary quarantined at round 32 | No |
| 20 | **SGTO-MAS** (2026-06-06; [2606.07940](https://arxiv.org/abs/2606.07940)) | Agent trust | Agent | [SNIPPET] per-round trust = blend of previous value + compliance score - cumulative risk penalty | Blended | [SNIPPET] correction for few observed interactions | 500 runs | No |
| 21 | **Node-contribution backpropagation** (2025-10-22, v2 2026-05-26; [2510.19420](https://arxiv.org/abs/2510.19420)) | Each agent's contribution to the final decision (signed DAG) | Agent | Backpropagated contribution; [SNIPPET] averaged over rounds; outliers flagged | Isolation of agents | n/a | Dynamic MAS settings | No |
| 22 | **Zero-Trust Identity Framework for Agentic AI** (2025-05-25; [2505.19301](https://arxiv.org/abs/2505.19301)) | Agent DID | Agent DID | [SNIPPET] dynamic trust score from policy violations, anomalies, credential validity, peer feedback; a lower score restricts capabilities | Score gates session authority | n/a | Framework only | No (agent IAM) |
| 23 | **Fortifying the Agentic Web**, zero-trust architecture (2025-08-17, v3; [2508.12259](https://arxiv.org/abs/2508.12259)) | Agent identity (DID/VC) + behavioural attestation | Agent | Trust-Adaptive Runtime Environments; [SNIPPET] trust from historical behaviour and peer assessment | Environment tightens as trust falls | n/a | Formal analysis | No |
| 24 | **ZTPM** for agentic cyber-physical systems (2026-05-25; [2605.25653](https://arxiv.org/abs/2605.25653)) | Robot-control agents | Agent | 25 policy primitives with Physical Impact Tiers; [SNIPPET] trust updated from interaction history, anomaly signals and time decay | Policy | n/a | 60 traces | No |
| 25 | **Sequential monitors for decomposition attacks** (2025-06-12; [2506.10949](https://arxiv.org/abs/2506.10949)) | Conversation/agent sequence | Conversation | Cumulative intent over sub-tasks | Within-session accumulation | n/a | Largest decomposition dataset; 87% ASR on GPT-4o undefended | No |
| 26 | **Stateful Online Monitoring Catches Distributed Agent Attacks** (2026-05-29; [2605.31593](https://arxiv.org/abs/2605.31593)) | Weak suspiciousness signals across *many accounts'* transcripts | Clusters across accounts (not one identity) | Real-time clustering, rare escalation to an LLM | Cross-account aggregation | n/a | Distributed attack evades a standard monitor (caught a fifth as often as prior attacks) | No |
| 27 | **Decomposition Attacks Across Unlinkable Identities** (2026-08-18, v2; [2608.17445](https://arxiv.org/abs/2608.17445)) | Groups of requests | Whatever grouping signal exists | Proves the security-utility trade-off depends on how requests are grouped | — | Fresh, indistinguishable identities defeat stateful defences | Theory + experiments | No |
| 28 | **DeepContext** (2026-02-18; [2602.16935](https://arxiv.org/abs/2602.16935)) | Turn-embedding sequence | Conversation | RNN hidden state over turns (intent drift) | Within-conversation | n/a | Crescendo / ActorAttack | No |
| 29 | **Representation transitions in multi-turn agents** (2026-09-30; [2610.00400](https://arxiv.org/abs/2610.00400)) | Agent's internal representations | Trajectory | Accumulated drift along a denoised safety direction | Cumulative | Benign traffic anchored at zero | MT-AgentRisk etc.; needs model internals | No |
| 30 | **MARK**, "Whose Agent Are You?" (2026-06-18; [2606.20910](https://arxiv.org/abs/2606.20910)) | Web agents seen by a *server* | Fingerprint (TLS, HTTP, browser behaviour) | Agent vs human vs crawler attribution | Classifier | n/a | Live instrumented domain | No (web), server-side |
| 31 | **FP-Agent** (2026-05-02; [2605.01247](https://arxiv.org/abs/2605.01247)) | 7 browsing agents + humans | Browser and behavioural fingerprint | Distinguishability | Classifier | n/a | Honey website, 3 tasks | No, server-side |
| 32 | **Known By Their Actions** (2026-05-14; [2605.14786](https://arxiv.org/abs/2605.14786)) | Agent action and timing traces | Passive JS tracker | Identifies the underlying LLM | Classifier | n/a | 14 LLMs, up to 96% F1 | No, server-side |
| 33 | **Trace** (2026-05-02; [2605.01186](https://arxiv.org/abs/2605.01186)) | Terminal command sequences of attack agents | Session | Attributes the model family | Classifier | n/a | 7 LLM families | No |
| 34 | **Fingerprinting AI Coding Agents on GitHub** (2026-01-24; [2601.17406](https://arxiv.org/abs/2601.17406)) | PR behaviour of 5 coding agents | Account/PR | 41 features, multi-class identification | Classifier | n/a | 33,580 PRs, 97.2% F1 | No |
| 35 | **HBEE** (2026-05-08; [2605.07472](https://arxiv.org/abs/2605.07472)) | Per-agent UEBA rank in a multi-agent LLM insider simulation | Agent | Tests whether an adaptive LLM insider leaves behavioural residue | — | — | Pre-registered, 95 valid runs; adaptive OPSEC caused no detectable shift in UEBA rank; the peer-suspicion signal inverted | No |
| 36 | **Simplified and Secure MCP Gateways** (2025-04-28; [2504.19997](https://arxiv.org/abs/2504.19997)) | Gateway traffic | — | [SNIPPET] rate limiting + intrusion detection + logging | — | — | Reference architecture | **Yes**, server-protecting gateway |
| 37 | **MCP Guardian** (2025-04-17, v2; [2504.12757](https://arxiv.org/abs/2504.12757)) | MCP traffic | — | Auth, rate limiting, WAF, logging; [SNIPPET] real-time anomaly detection left as future work | — | — | Scenarios | **Yes** |
| 38 | **Securing MCP: Risks, Controls, Governance** (2025-11-25; [2511.20920](https://arxiv.org/abs/2511.20920)) | Recommends baselining tool sequences and data volumes per user and role, plus per-user and per-tool limits | User/role (recommended) | — | — | — | Position paper; names "agents who become unintentional adversaries by over-stepping their role" | **Yes** |

#### Notes on key works

- **MI9** is the closest academic analogue to our dynamic layer. Its baselines are *goal-conditioned* "because the same agent may behave differently under different goals". It adopts new baselines only "when goal changes match consistent behavioral patterns", and drift signals act as "risk factors rather than direct violations". This matches our use of behaviour as a multiplier rather than a gate — [MI9 v3 HTML](https://arxiv.org/html/2508.03858v3)
- **Praetor** is the closest analogue to our learned per-agent policy (limits per tool, required steps). It compiles benign telemetry into permitted tool sequences, sequential contexts and parameter bounds, and enforces them at a gateway. Its reported weakness is continuous parameter bounds, which show 18% evasion by synonym substitution — [arXiv 2604.26274](https://arxiv.org/abs/2604.26274)
- **AegisMCP** is the most MCP-specific behaviour detector found. It is the only one that models MCP servers, tools, agents and sessions as a temporal graph with novelty over time. It is consistent with our threat direction, since the adversary induces an agent to make legitimate tool calls — [AegisMCP v2 HTML](https://arxiv.org/html/2510.19462v2)
- **Keying risk.** Work 27 proves that stateful defences only work if requests can be grouped, and that "fresh, indistinguishable groups" defeat them. Work 26 shows real attackers split work across accounts. Both bear directly on keying history by agent id only — [2608.17445](https://arxiv.org/abs/2608.17445); [2605.31593](https://arxiv.org/abs/2605.31593)
- **Evasion.** HBEE's pre-registered result is that adaptive OPSEC "produces no detectable shift in the mole's UEBA rank". This is a caution that per-agent behavioural baselines can be operated "below the radar" — [2605.07472](https://arxiv.org/abs/2605.07472)

#### Excluded on scope

These were checked and set aside:
- *ProbeID* ([2610.33633](https://arxiv.org/pdf/2610.33633)) and *MTGuard*, Hybrid Analysis for Secure MCP Tool Use ([2607.25297](https://arxiv.org/html/2607.25297)): agent- or tool-side verification against malicious or drifting servers, which is the inverse threat direction. Not re-verified through the arXiv API.
- *AegisUI* ([2603.05031](https://arxiv.org/abs/2603.05031)): single-payload UI anomaly detection with no per-agent history.

### Inferences

- **Cold start.** The few works that address it use three tactics: conservative thresholds that tighten with confidence (MI9), a minimum observation count (A-Trust, 20 queries) and correction for few observations (SGTO-MAS, snippet only). Our framework should justify its x0.7-5 range at low history counts against these. In particular, it must not grant the x0.7 discount to a brand-new agent id, given works 26 and 27.
- **Bounding.** Bounded scores are common ([0,1] trust or credibility, ARI in [0,1], P(safe)). However, no paper bounds a *multiplier on a per-call risk price* in the way our framework does. That combination appears to be novel among verified works; this is an inference, not proven absence.
- **Evaluation norms.** Most works evaluate on synthetic traces (MI9, AegisMCP, Agent Drift, DART) or attack benchmarks (Praetor/ASB, ADR-Bench, SHADE-Arena). Only ADR reports production deployment, and ADR is session-level. This matches our memory note that dynamic-layer evaluation on ordinary traffic with gray risk is underserved.
- **MCP-specific behaviour-over-time work is thin.** Of 38 papers, 6 are MCP-specific (works 10, 11, 12, 36, 37, 38). Only AegisMCP keeps temporal novelty state, and none keeps a long per-agent history.

### Gaps

- I did not read in full A-Trust, DRF, DART, SGTO-MAS, the zero-trust papers (works 22-24), Agent Drift's baseline details or the MCP gateway papers. Their [SNIPPET] details need checking against the full text before citation.
- No peer-reviewed venue was confirmed for any of the 38 works; arXiv comment fields were not checked for each.
- I did not find a paper that explicitly applies commercial-style UEBA (per-entity risk accumulation with peer groups) to MCP traffic keyed by agent identity.

## B2. Industry: UEBA, ITDR and NHI security extended to AI agents and MCP

### Takeaway

As of November 2026, two vendors *document* per-agent behavioural baselines with concrete mechanics:
- **Microsoft Entra ID Protection for agents**: learning mode, eight named detections, risk levels feeding Conditional Access, 90-day retention.
- **Exabeam Agent Behavior Analytics**: white paper giving baseline maturity of about 14 days, with per-rule 7/14/28-day requirements and an admitted gap for short-lived agents.

Securonix, Zenity, Noma and Lasso *claim* agent behavioural baselines or drift detection in marketing, without published mechanics. CrowdStrike, Silverfort, Teleport, Oasis, Palo Alto and Okta focus on agent identity, authorisation and audit at MCP or agent gateways rather than learned behaviour. Noma, Zenity, Lasso, Silverfort, Teleport, Palo Alto and CrowdStrike explicitly cover MCP.

### Cited Findings

**Microsoft Entra ID Protection for agents** [DOC] (page ms.date 2026-06-17)
- Learning mode and early-life detection: "Learning Mode automatically suppresses behavioral alerts for agents that lack sufficient activity history, preventing false positives during onboarding and after periods of inactivity. A separate detection runs in parallel to ensure genuinely malicious early-life behavior is still caught" — [Microsoft Learn, ID Protection for Agents](https://learn.microsoft.com/en-us/entra/id-protection/concept-risky-agents)
- Detections (all currently offline):
  - Confirmed compromised.
  - Early life malicious activity: "Newly created agent immediately exhibited multiple suspicious behavior patterns".
  - Entra directory reconnaissance.
  - Failed access attempt.
  - Microsoft Entra threat intelligence.
  - Sign-in spike: "higher number of sign-ins compared to its usual sign-in frequency".
  - Suspicious credential usage.
  - Unfamiliar resource access: "resources that it doesn't usually access".
  - Source: [same page](https://learn.microsoft.com/en-us/entra/id-protection/concept-risky-agents)
- Keying: "In on-behalf-of (OBO) flows ... risky activity is attributed to the **user** rather than the agent"; detections apply to autonomous agent activity unless noted. Confirming compromise sets risk to High and triggers Conditional Access "configured to block access on High Agent Risk". Detections are retained up to 90 days. Licensing is moving to a Microsoft Agent 365 licence — [same page](https://learn.microsoft.com/en-us/entra/id-protection/concept-risky-agents)

**Exabeam Agent Behavior Analytics (ABA)** [PR] + vendor white paper
- Launch: announced 2026-01-06 as an extension of UEBA to "AI agent behavior analytics, unified timeline-driven investigation of AI activity, and posture visibility". It built on a September 2025 Google Agentspace / Gemini Enterprise integration. No MCP mention — [Exabeam press release, 2026-01-06](https://www.exabeam.com/press-releases/exabeam-introduces-first-connected-system-for-ai-agent-behavior-analytics-and-ai-security-posture-insight/)
- Expansion on 2026-04-01: added ChatGPT and Copilot. It builds "dynamic behavior profiles for users and their AI agents" over request volumes, token usage, tool invocations, web sessions and outbound activity, and flags deviations "such as sudden spikes in API calls or token consumption" — [Help Net Security, 2026-04-01](https://www.helpnetsecurity.com/2026/04/01/exabeam-expands-aba-to-detect-ai-agent-threats-across-chatgpt-copilot-and-gemini/)
- White paper (© 2026; references Q1 2026):
  - Three tiers: Tier 1 conversational (ChatGPT, Gemini, Copilot); Tier 2 integrated harnesses "such as Claude Code, Model Context Protocol (MCP) integrations"; Tier 3 digital workers modelled as users.
  - Baseline maturity: "In most cases, baselines are established over roughly 14 days of activity ... Others require extended observation periods, such as 7, 14, or 28 days"; maturity-dependent detections "do not trigger" before then.
  - Short-lived agents "never reach baseline maturity". Exabeam calls this "a known gap for ephemeral agents ... innate to any detection model based on historical baselining".
  - Linking multiple credentials to one agent "remains an area of active research and development".
  - Source: [Exabeam white paper, Agent Behavior Analytics: Securing the Autonomous Enterprise](https://www.exabeam.com/wp-content/uploads/WHITEPAPER-Agent-Behavior-Analytics-Securing-the-Autonomous-Enterprise.pdf)

**Securonix Agent and Entity Behavior Analytics (AEBA) / Advanced Behavioral Analytics (ABA)** [PR]
- AEBA "extends traditional UEBA to monitor AI agents, autonomous workflows, and non-human identities". Its signals are agent actions, API calls, tool usage, permissions, sensitive-data interactions, "abnormal prompt behavior", rare access, volume spikes and unexpected sequences. It covers "deviations from individual or peer-group patterns". No MCP mention and no scoring formula — [Securonix UEBA/AEBA page (2026)](https://www.securonix.com/products/ueba/)
- Press coverage around October 2026 describes ABA (AEBA + UEBA) detecting "when an enterprise AI agent uses an unexpected tool, accesses data beyond its intended purpose or deviates from its established operating patterns" — [Cybersecurity Insiders](https://www.cybersecurity-insiders.com/securonix-launches-advanced-behavioral-analytics-to-detect-human-and-ai-driven-threats/) [SNIPPET]; [CRN Asia, 2026](https://www.crnasia.com/india/news/2026/securonix-extends-behavioural-analytics-to-detect-threats-from-ai-agents) [SNIPPET]

**Zenity AI Detection & Response (AIDR)** [PR], MCP mentioned
- Zenity claims a "stateful threat engine [that] tracks agent execution continuously across sessions, building a behavioral baseline". It claims step-level tracking (messages, RAG, tool invocations), mapping to OWASP LLM and MITRE ATLAS, and governance of "MCP servers and tools" — [Zenity AIDR page](https://zenity.io/platform/ai-security-platform/aidr) [SNIPPET]. The Zenity docs pages I fetched rendered only navigation, so I could not confirm these claims in the docs — [Zenity docs, AI Detection & Response](https://docs.zenity.io/UserGuide/ZenityUG_AI-Detection_Response.html)

**Noma Security** [PR], MCP-specific (2026-06-02)
- Noma's platform "monitors the skills, MCP servers, and tools agents actually use, establishes a baseline for agent behavior, and detects ... agents drifting from their intent or established behavior". "Contextual Policies" correlate prompts, tool calls, responses, data access and identity "over time". Per-tool allow/block can be scoped by tool, agent type, user, team or environment — [Help Net Security, 2026-06-02](https://www.helpnetsecurity.com/2026/06/02/noma-brings-visibility-and-access-governance-to-ai-agents-and-mcp-servers/)

**Lasso Security** [PR], MCP-specific
- Lasso released an open-source MCP Gateway (2025-04-17), a proxy and orchestrator with configurable request and response guardrails — [Business Wire, 2025-04-17](https://www.businesswire.com/news/home/20250417840621/en)
- Intent Deputy (2026-02-17) claims "behavioral baselines" and "intent alignment" ("Is this action aligned with the agent's authorized purpose?"), plus 99.83% detection at under 50 ms. These figures are vendor claims with no independent validation found — [Business Wire, 2026-02-17](https://www.businesswire.com/news/home/20260217250467/en/Lasso-Security-Introduces-Intent-Deputy-Pioneering-Intent-Security-as-the-New-Standard-for-Securing-AI-Agents)

**Astrix Security (NHI ITDR)** [PR]
- Astrix claims "AI-based threat engines detect abuse of NHIs based on anomaly indicators such as unusual IP, user agent, and activity". It says ITDR should score each NHI on permissions, scopes, third-party vendors, rotation policy and behaviour — [Astrix glossary, ITDR](https://astrix.security/glossary/what-is-identity-threat-detection-and-response/) [SNIPPET]
- Trade press reports that Astrix uses anomaly detection and fingerprinting to set fine-grained permissions for AI agents — [BankInfoSecurity](https://www.bankinfosecurity.com/astrixs-45m-series-b-targets-non-human-identity-security-a-27006) [SNIPPET]

**Oasis Security, Agentic Access Management (AAM)** [PR]
- Oasis describes AAM as "intent-aware, policy-driven identity infrastructure" with "precise, time-bound access". It is intent-based just-in-time access rather than behavioural baselining — [Oasis blog, Introducing AAM](https://www.oasis.security/blog/introducing-oasis-agentic-access-management) [SNIPPET]; [Oasis AAM page](https://oasis.security/agentic-access-management) [SNIPPET]. Oasis raised a $120M Series B in March 2026 — [FinTech Global, 2026-03-20](https://fintech.global/2026/03/20/oasis-security-lands-120m-to-govern-enterprise-ai-agents/) [SNIPPET]

**CrowdStrike, Continuous Identity for AI Agents** [PR] (2026-06-15)
- Announced SPIFFE-based verifiable agent identities, an Agentic IdP that ties each agent to the humans and workloads behind it, risk-aware authorisation extended to agents, and Falcon Guardian agent inventory. An AI Gateway covering MCP traffic is planned — [CrowdStrike press release, 2026-06-15](https://www.crowdstrike.com/en-us/press-releases/crowdstrike-unveils-continuous-identity-for-ai-agents/) [SNIPPET]

**Silverfort AI Agent Security** [PR], MCP-specific
- An inline MCP gateway "between agents and the MCP servers they access" evaluates every tool call against policies and tethers each agent to a human identity via the IdP. It is policy-based, with no documented behavioural model — [Silverfort solution brief, 2025-06](https://www.silverfort.com/wp-content/uploads/2025/06/Silverfort_AI-Agent_SolutionBrief.pdf) [SNIPPET]; [Google Agent Gateway partner page](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agw-partners) [SNIPPET]

**Teleport** [DOC/PR], MCP-specific
- Teleport's MCP integration is default-deny (newly appearing tools are blocked until allowed), with RBAC/ABAC, just-in-time access and short-lived X.509 workload identity for agents. It mentions "behavior analysis" but documents no anomaly model — [Teleport Agentic Identity Framework docs](https://goteleport.com/docs/agentic-identity-framework) [SNIPPET]; [Teleport blog](https://goteleport.com/blog/secure-ai-agents-zero-code-mcp/) [SNIPPET]

**Palo Alto Networks, Secure AI Agents** [PR], MCP-specific (May 2026)
- An agent identity broker acts as the authorisation server for remote MCP servers. It keeps audit trails of which MCP server and tools each agent used, holds new MCP servers as "disabled" until an admin approves them, and maintains an MCP inventory — [Palo Alto Networks blog](https://www.paloaltonetworks.com/blog/identity-security/secure-ai-agents-controls-visibility-mcp-data-access/) [SNIPPET]

**Okta** [PR]
- Identity Threat Protection re-evaluates *user* risk continuously within sessions (Shared Signals Framework, Universal Logout). I found no documentation that it baselines agent behaviour. Okta for AI Agents is framed as discovery, registration and access standardisation — [Okta ITP product page](https://www.okta.com/products/identity-threat-protection/) [SNIPPET]

**MCP gateway vendors with anomaly claims** [PR, low confidence]
- TrueFoundry describes z-score anomaly checks on gateway audit metrics, with a configurable threshold that triggers quarantine, evaluated off the request path — [TrueFoundry blog](https://www.truefoundry.com/blog/claude-code-enterprise-mcp-gateway) [SNIPPET]
- mTrust claims "per-agent behavioral baselines" and sequence mining — [mTrust site](https://www.modeltrust.io/) [SNIPPET]

### Inferences

- **Keying contrast.** Microsoft attributes OBO-flow risk to the *user*, and Exabeam profiles "users and their AI agents". Both key on human identity where it exists. Our agent-id-only keying is the opposite choice. It can be defended by our identity constraint (agents may stand for a whole org), but it should be stated as a deliberate departure.
- **Cold-start precedent.** Entra's learning mode with a parallel early-life-malicious detector, and Exabeam's 14-day maturity gate with a stated ephemeral-agent gap, are the best citable industry precedents. Both show the field accepts that baselines need weeks and that new identities need a separate non-baseline check. Our 90-active-day history is longer than either.
- **MCP-specific behavioural signals in industry.** Named signals are MCP servers and tools actually used (Noma), newly appearing tools (Teleport default-deny), which MCP server and tool was invoked (Palo Alto audit), and tool invocation sequences (Exabeam Tier 2). None documents a numeric behaviour score per agent per MCP server.

### Gaps

- **Token Security:** searches returned no primary material on behavioural signals (no result).
- I found nothing on Splunk/Cisco applying UEBA or RBA to AI agents.
- I found no documentation that Microsoft Sentinel UEBA has an agent-specific entity type. It does ingest service principal and managed identity sign-ins in preview.
- Zenity, Noma, Lasso, Astrix, Securonix and CrowdStrike publish no scoring mechanics, windows, bounds or evaluation data. All their claims are marketing-level.
- No independent evaluation of any vendor's agent-behaviour detection was found.

### Second-pass count (verified 2026-11-04)

- **Part A: 9 products.** Exabeam Advanced Analytics; Splunk ES RBA; Microsoft Sentinel UEBA; Microsoft Entra ID Protection (users and workload identities); Elastic entity risk scoring; Google SecOps Risk Analytics; Securonix (partial, patent only); CrowdStrike Falcon Identity Protection (partial); Palo Alto SaaS Security user risk (decay example only). The first 6 are documented in detail; the last 3 are partial. Splunk UBA was not covered.
- **Part B1: 38 papers in the table**, all confirmed on arXiv (API lookup or arXiv abstract fetch).
  - Core per-agent or per-goal behaviour-over-time baselines or learned behaviour models: works 1-10, 15.
  - Trust and reputation with history: works 16-24.
  - Stateful or cumulative monitors: works 25-29.
  - Fingerprinting: works 30-34.
  - Evasion study: work 35.
  - Other trajectory or session detectors: works 11-14.
  - MCP gateway or governance papers: works 36-38.
  - MCP-specific works: 6 (10, 11, 12, 36, 37, 38).
  - A further 3 were excluded on scope: ProbeID, MTGuard, AegisUI.
- **Part B2: 15 industry offerings.** Microsoft Entra ID Protection for agents; Exabeam ABA; Securonix AEBA/ABA; Zenity AIDR; Noma; Lasso (MCP Gateway + Intent Deputy); Astrix; Oasis AAM; CrowdStrike Continuous Identity; Silverfort; Teleport; Palo Alto Secure AI Agents; Okta; TrueFoundry; mTrust.
  - MCP-specific (8): Noma, Lasso, Silverfort, Teleport, Palo Alto, CrowdStrike (planned gateway), TrueFoundry, mTrust. Zenity and Exabeam mention MCP.
  - Documented, not marketing: 2 (Microsoft; Exabeam's white paper).
  - Not found: 1 (Token Security).
