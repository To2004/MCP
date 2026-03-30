# MiniScope Synthetic Permission Dataset

## Source
- **Paper:** MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents (Zhu et al., 2025)
- **Link:** https://arxiv.org/abs/2512.11147
- **Year:** 2025

## Format & Size
- **Total samples:** Variable per application — single-method requests per API method + 200 multi-method requests per app + 2 multi-app suites (171 and 465 methods)
- **Format:** Synthetic API call scenarios with permission scope annotations across 10 real-world applications
- **Availability:** Paper and supplementary materials (https://arxiv.org/abs/2512.11147)

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Application | Categorical (10 apps) | Gmail, Google Calendar, Slack, Dropbox, etc. | Yes | Real-world applications with known API structures |
| API method | String | Gmail: 79 methods, Calendar: 37, Slack: 247, Dropbox: 120 | Yes | Actual API method identifiers from real services |
| Permission scope | Categorical per app | Gmail: 10 scopes, Calendar: 17, Slack: 84, Dropbox: 13 | Yes | Ground-truth minimum scopes per method |
| Request type | Categorical | Single-method, multi-method, multi-app | Yes | Increasing complexity levels |
| Multi-method request count | Integer | 200 per app | Yes | Standardized across apps for consistent evaluation |
| Multi-app suite | Structured | Suite 1: 171 methods, Suite 2: 465 methods | Yes | Cross-application permission resolution scenarios |
| Mismatch rate | Float (%) | Over-privilege or under-privilege detection rate | Yes | Key metric — measures how far from least-privilege |
| Latency overhead | Float (%) | 1-6% overhead | Yes | Practical deployment cost |
| Baseline method | Categorical | Vanilla, PerMethod, LLMScope, MiniScope | Yes | 4 baselines including 3 comparison methods |

## Proposed Risk Dimensions

### Permission Scope Risk
- **Feeding columns:** Permission scope per method, mismatch rate
- **Proposed scale:** 1-10 where exact least-privilege match = 1, minor over-privilege (1 extra scope) = 3-4, moderate over-privilege (2-3 extra scopes) = 5-6, severe over-privilege (broad/admin scopes granted unnecessarily) = 8-10
- **Derivation:** For each API call, compare the scopes actually granted against the minimum scopes required (ground truth from MiniScope's annotations). The risk score is a function of the excess: count the number of unnecessary scopes granted and weight each by its sensitivity. A Gmail "readonly" excess scope is less dangerous than a "full access" excess scope. The mismatch rate from MiniScope's evaluation provides the aggregate measure; per-call scoring breaks it down. MiniScope achieved the lowest mismatch rates across baselines, so its outputs serve as the "ideal" calibration target.

### Application Complexity Risk
- **Feeding columns:** API method count per app, scope count per app
- **Proposed scale:** 1-10 based on the combinatorial complexity of the application's permission model
- **Derivation:** More methods and more scopes = more opportunities for over-privilege. Gmail (79 methods / 10 scopes) has a 7.9 method-to-scope ratio — many methods share scopes, so permission assignment is relatively straightforward (score 3-4). Slack (247 methods / 84 scopes) has a 2.9 ratio with far more scopes — the permission landscape is complex and error-prone (score 7-8). Dropbox (120 methods / 13 scopes) has a 9.2 ratio — many methods per scope means coarse-grained permissions with high over-privilege risk (score 6-7). The risk formula: `base_score = log2(methods) + log2(scopes)`, normalized to 1-10.

### Over-Privilege Detection
- **Feeding columns:** Mismatch rate per baseline method (Vanilla, PerMethod, LLMScope, MiniScope)
- **Proposed scale:** 1-10 where 0% mismatch = 1 and increasing mismatch percentages map linearly to higher scores
- **Derivation:** The mismatch rate directly measures how far a permission assignment deviates from least-privilege. Under the Vanilla baseline (no scope restriction), every call gets full access — score 10. Under MiniScope (optimized), mismatch is minimized — score 1-2. At runtime, measure the gap between the scopes a tool request actually needs and the scopes it was granted. Each percentage point of over-privilege adds to the risk score. This dimension answers: "how much more access does this agent have than it actually needs right now?"

### Runtime Overhead Feasibility
- **Feeding columns:** Latency overhead (1-6%)
- **Proposed scale:** Not a risk score per se, but a feasibility gate — 1-6% overhead confirms that dynamic permission checking is practical for production deployment
- **Derivation:** The 1-6% latency overhead measured by MiniScope demonstrates that least-privilege enforcement does not impose prohibitive costs. This is relevant for the risk scoring system's architecture: if dynamic scope checking adds less than 6% latency, it can be integrated as a real-time risk dimension rather than a batch-processed post-hoc score. Any risk dimension that requires scope comparison at inference time is validated as feasible by this measurement.

## Data Quality Notes
- The dataset is synthetic — API method lists and scope mappings are drawn from real applications, but the actual requests are generated, not collected from real user interactions. This means the permission mappings are accurate but the request patterns may not reflect real-world usage distributions.
- The 10 applications vary enormously in complexity: Slack has 247 methods while Google Calendar has 37. Comparisons across apps need to be normalized by application complexity.
- The 200 multi-method requests per app are standardized in count but may vary in complexity — it is not clear whether "multi-method" means 2 methods or 10 in the same request.
- The two multi-app suites (171 and 465 methods) cover cross-application scenarios, which are rare in other benchmarks. This is valuable because real enterprise agents often call tools across multiple services in a single workflow.
- The latency overhead numbers (1-6%) are measured under specific conditions — hardware, model size, and network conditions will affect these in practice.
- The Vanilla, PerMethod, LLMScope baselines provide comparison points but are specific to MiniScope's evaluation setup. Translating mismatch rates to other frameworks may require re-measurement.

## Usefulness Verdict
MiniScope provides something no other benchmark in the survey offers: a ground-truth mapping from API methods to minimum required permission scopes across 10 real-world applications. This is directly useful for building a "permission scope risk" dimension in a 1-10 scorer. Most security benchmarks focus on whether an attack succeeds; MiniScope focuses on whether the agent has more access than it needs, which is the precondition that makes attacks possible in the first place. Over-privileged access is not an attack — it is a risk posture.

For practical deployment, the per-app method and scope counts provide a concrete complexity metric that can be computed for any new MCP server without running any experiments. Count the methods, count the scopes, compute the ratio, and you have a baseline complexity risk score. The 1-6% latency overhead validates that real-time scope checking is feasible, which means the permission scope risk dimension can be computed dynamically at request time rather than statically at deployment time. This aligns perfectly with the thesis goal of dynamic (not just static) risk scoring.
