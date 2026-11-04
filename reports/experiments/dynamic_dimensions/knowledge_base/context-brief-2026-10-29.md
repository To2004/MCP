# Context brief: risk scoring for MCP servers (week of 22-29 October 2026)

This is a self-contained summary of one week of design work on a risk-scoring framework for MCP
(Model Context Protocol) servers. It covers the static and dynamic scores, every decision and why,
the tests run, a reviewer-style critique, and a backlog of open ideas. It is written so that it can be
pasted into, or uploaded to, ChatGPT or Claude as background.

## 0. How to use this brief

Upload this file, or paste it, then start with something like:

> You are helping a security researcher who is writing an A*-venue paper (USENIX Security / CCS /
> S&P) on risk scoring for MCP servers. The attached brief is the current state of the design. MCP
> servers are the protected asset and AI agents are the threat; never reverse this. Keep answers
> MCP-specific. Point out where a claim is not yet supported by evidence.

**Rules of the project:**
- **Threat direction:** we defend servers *from* agents.
- **Scope:** only MCP-specific results for MCP-related questions.
- **Synthetic numbers:** all numbers below come from synthetic design checks. They are not paper
  results, and the real-data evaluation is still in the pipeline.

## 1. The project in one paragraph

A gateway sits in front of MCP servers and scores every tool call **before it executes**, so a server
can log, throttle, gate or deny risky calls. The score has two layers:

```text
Risk(call) = Risk_static(tool, asset, parameters) × M(call)
```

- **The static score** says how much damage this tool can do to this asset with these parameter
  values. It is fixed at design time from the tool catalog and the organisation's policy.
- **The dynamic multiplier M** says how unusual this call is *for the agent that makes it*. It is
  learned from that agent's own past.

## 2. Status and deadlines

- **Target venue:** USENIX Security 2027, cycle 2. Registration is due 19 Jan 2027, the paper 26 Jan
  2027, and the internal freeze is about 8 Dec 2026.
- **Due by 8 Nov 2026:**
  - X1: at least two scenario writers from outside the team, so the designers don't write their own
    test cases;
  - X3: lab users' consent and ethics approval for logged traffic.
- **The author has not started writing the evaluation.** Real-data evaluation is in the pipeline.
- **The paper's static section is drafted.** The dynamic section has a LaTeX draft (see §5.10).

## 3. MCP facts that shape the design

- **Latest spec: MCP 2026-07-28.**
  - There is no `initialize` handshake (replaced by `server/discover`) and no sessions
    (`Mcp-Session-Id` removed).
  - Every request carries `_meta` (protocol version, client capabilities, `clientInfo`) plus
    `MCP-Protocol-Version`, `Mcp-Method` and `Mcp-Name` headers.
  - "Input required" turns are a result followed by a retry with a new JSON-RPC id (MRTR).
  - Tasks are an extension, and authorization is optional.
- **Identity.** MCP has no standard agent-id field, and `clientInfo` is self-reported and must not
  drive security decisions.
  - The setting has **only an agent id**: no user ids, no sign-in, no IP address. One agent id may
    stand for a whole organisation.
  - **Assumption:** the operator issues the id, and a client cannot choose or forge it. Sybil
    identities are out of scope.
- **Consequences for the dynamic score:**
  - Session-based checks (session length, missing handshake) don't exist on new clients.
  - Retries must be folded into one logical call.
- **Code:** the gateway runs on the MCP Python SDK 2.x (`mcp>=2.3,<3`) and supports both the legacy
  and the 2026-07-28 protocol.

## 4. The static score

### 4.1 As written in the paper draft

The static score has four factors, each on a 1-5 ordinal scale:

| Factor | Defined for | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| ToolImpact(t) | each tool | no material effect | metadata | content access, or a limited change | major change, normally reversible | irreversible or consequential |
| AssetSensitivity(a) | each asset | public, negligible | routine internal | moderate impact | restricted, high impact | critical (credentials, regulated data, crown jewels) |
| BlastRadius(t, a) | each tool-and-asset pair | single object | bounded subset | broad subset | complete asset | systemic, fans out |
| ParameterRisk(t, input) | each risk-relevant input | minimal (e.g. $100) | low ($500) | moderate ($2,000) | high ($10,000) | critical ($50,000) |

```text
ParameterRisk(t) = max over the tool's risk-relevant inputs   (0 if it has none)
Risk_static = 0.3·ToolImpact + 0.3·AssetSensitivity + 0.3·BlastRadius + 0.1·ParameterRisk
```

| Example | Risk_static |
|---|---|
| Ping | 0.9 |
| Read one message in a routine channel | 1.8 |
| Write one file in an internal folder | 2.7 |
| Delete one CEO calendar event | 3.0 |
| `send_money` $100 / $50,000 | 3.4 / 3.8 |
| Drop the salaries table | 4.4 |

**How the factors are produced:**
- An LLM classifies the factors at design time, with fixed rules for obvious names such as
  `delete_file`.
- Asset sensitivity reuses the organisation's own labels where they exist.
- ParameterRisk thresholds come from the policy where it gives them; otherwise an LLM writes one
  rule per input. At run time each rule is only a lookup.

**Which asset a call is priced on:** the binding layer resolves it from the tool's arguments
against the policy register, deterministically, with no per-server code. When it can't, the call is
priced at the **worst** asset the tool can reach.

### 4.2 Known issues with the static part

1. **Code and paper differ.**
   - The gateway computes the cube root of ToolImpact × AssetSensitivity × BlastRadius (a geometric
     mean), and only logs ParameterRisk.
   - The paper uses the weighted sum above.
   - The ToolImpact wording also differs: the scanner prompt has 4 = full modification and 5 =
     destructive or executing.
2. **w_P = 0.1 is weak for the paper's own example:** $100 → 3.4 and $50,000 → 3.8.
3. **"0 when there is no risky parameter" ranks below "minimal".** The maximum is then 4.5.
   Suggested fix: divide the other weights by 0.9 when there is no parameter.
4. **ParameterRisk depends on the call's arguments,** so the equation should show the call. The
   asset index also disappears between the definition and the max.
5. **Adding ordinal levels treats them as equally spaced.** This is a known risk-matrix critique
   (Cox 2008), so report sensitivity to the weights.

## 5. The dynamic score: the current design ("J")

### 5.1 Idea

- **M = 1** for ordinary behaviour.
- **M rises towards 5** the less often this agent has done anything like it.
- **M is about 0.87** for its deepest habit.

M uses only what is known before the call runs: agent id, time, tool, and asset (from the binding
layer). Argument values belong to the static score, and outcomes never change the same call's score.

### 5.2 The six dimensions

All six compare the call with **the same agent's own past calls**.

| Group | Dimension | Asks | Rises: a real case | Stays calm |
|---|---|---|---|---|
| Typical Footprint | Tool | Which capability? | a comment bot calls `merge_pull_request` | a new tool used daily settles in about two weeks |
| | Asset | What is it working on? | a reporting agent first queries `salaries` | an explorer bot opens one more channel |
| | Tool on asset | A new action on something familiar? | `delete-event` on a calendar it only reads | a rarely used asset gives little evidence |
| Typical Cadence | Calls this hour | How fast? | 300 reads an hour, against a peak of 20 | a busy hour in the same doubling |
| | Breadth (distinct tool-asset pairs per hour) | How wide? | 25 repositories in an hour, against a usual 3 | a monthly report already in its history |
| | Time of day | When? | posting at 3 am from a 9-to-5 agent | a night-shift or always-on agent |

**Left out on purpose:**
- argument values (that is static ParameterRisk);
- session length (better as a simple policy limit, and gone in MCP 2026-07-28);
- day of week (the author decided it is not part of the context);
- the old "Red Flags" group (burst, sweep, oversized request, unsafe sequence, missing handshake),
  because it needed hand-written limits;
- network and client (there is no IP address or client name).

### 5.3 The formula

**The one question:** *how many of this agent's past calls were at least this unusual?*

1. **For each dimension,** count the past calls at least as unusual on it:
   - Tool, Asset, Time of day: a value used just as rarely or more rarely;
   - Tool on asset: this tool's share among past calls on this asset;
   - Calls this hour, Breadth: an amount in the same doubling or higher.
2. **For the whole call,** compare its rarest dimension with each past call's rarest dimension; a
   tie goes to the next one. The count of past calls at least as unusual is k.
3. **Convert k to M:**

```text
M = ((n + 1) / (2k + 1))^γ ,     γ = ln 5 / ln(max(n, 1000) + 1)
n = the agent's past calls in its history window (90 days, as in the author's deck)
k = past calls at least as unusual as this one (0 … n)
Equivalent: share = (k + ½)/(n + 1), and M = (½ / share)^γ, a likelihood ratio against the agent's typical call
```

### 5.4 Every variable, justified

| Variable | Why it is there | How it generalizes across MCP servers |
|---|---|---|
| n | The amount of evidence. UEBA scores each entity against its own baseline (Sentinel 10-180 days, Exabeam 60-90 days). | A plain count of calls, which exists on every server |
| k | UEBA's "first time / uncommon for this user", as a number. It gives the habit discount for free. | Uses only tool name, asset and time |
| ½ (inside n+1 and 2k+1) | The mid-p correction (Lancaster 1961): no division by zero, a new agent gets ×1, and a behaviour seen in half the calls gets exactly ×1. | A statistical constant |
| 5 (the top) | The same span as the static 1-5 scale, so behaviour can move a call across the whole static range and no further. | The same everywhere |
| γ | "Never seen" lands exactly on ×5, and each halving of k is the same step (×1.17 at 1,000 calls, ×1.14 at 4,000, ×1.10 at 100,000). | Computed per agent from n, with no tuning |
| 1,000 | A warm-up, as in UEBA (Exabeam convergence, Entra 5 days, Elastic 20 buckets). Never seen gives ×1.18 after 1 call, ×1.75 after 10, ×2.93 after 100 and ×5 from 1,000. | One number, but quiet agents reach it late |
| Doublings (bins 1-3, 4-7, 8-15, …) | Relative to the agent's own level: a busier hour is not a record, twice the peak is. This is the implicit tolerance band. | Scale-free (20→40 is the same step as 2,000→4,000) |
| Rarest dimension first | With six dimensions, most calls are a little unusual somewhere. A plain maximum inflates ordinary calls; a sum hides single signals. | A rule on frequencies, not dimension names |

### 5.5 Worked examples (illustrative k; n = 4,000, so γ = 0.194)

| Call | k | M | Static | Risk |
|---|---|---|---|---|
| Routine read | 2,000 | ×1.00 | 1.8 | 1.8 |
| Monthly report (1 in 100 past calls as unusual) | 40 | ×2.13 | 2.7 | 5.8 |
| Delete on a calendar it only reads | 3 | ×3.43 | 3.0 | 10.3 |
| 3 am sweep of 25 repositories, nothing like it before | 0 | ×5.00 | 2.1 | 10.5 |
| Its deepest habit | 4,000 | ×0.87 | 2.7 | 2.4 |
| A new agent (n = 10) does something new | 0 | ×1.75 | 3.0 | 5.2 |

### 5.6 Settled rules (from the reviewers' minor points)

| Rule | Why |
|---|---|
| Only calls that executed enter the history. Denied or failed calls are scored but never learned, and a retried call counts once. | In the probe-then-strike test, the real call still scores ×5 after 20 denied attempts. If the attempts were learned, it would score ×0.7-2.1. |
| Time of day uses the route's time zone and counts calls within one hour of this time, with no weekday. | It matches the author's deck ("calls within 1 hour of this time"). |
| Amounts of 1-3 share one bin. | So a third call in an hour is never a record. |
| M below 1 only reorders the review list; **blocking uses max(1, M)**. | UEBA also down-weights habit, but habit must never lower a block decision. |
| Every score shows its reason: the rarest dimension and its share. | Example: "write on a repo it only reads, ×3.41: Tool on asset, as unusual in 0.09% of past calls". |
| Statistics are reported as a mean ± 95% Student-t interval over 10 seeds. Development seeds are burnt. | So no number is tuned on the data it is reported on. |

### 5.7 Guarantee, and its assumption

If the agent's ordinary calls are exchangeable, a given call reaches ×5 with probability at most
1/(n+1). This is a conformal p-value (Bates et al. 2023). Calls are bursty and trending in practice,
so the bound is a design intuition until it is checked on real data. It holds per call, so busy agents
get more chances per day.

### 5.8 Grounding in UEBA (user and entity behaviour analytics)

| Our dimension | UEBA counterpart |
|---|---|
| Tool | Microsoft Sentinel's first-time / uncommon action insights; AWS GuardDuty's "API unusual for this identity" |
| Asset | Sentinel's per-resource insights; Exabeam's first access to a system; Elastic's `rare` |
| Tool on asset | GuardDuty: "which factors of the API request are unusual for the user identity" |
| Calls this hour | Sentinel's burst of operations; Exabeam's numerical models; Elastic counts per bucket |
| Breadth | Microsoft Entra's "mass access to sensitive files", only when uncommon for the user |
| Time of day | Exabeam's time-of-week model; Elastic `time_of_day` |

- **Kept from UEBA:**
  - a per-entity baseline;
  - first time as the strongest signal, but discounted for entities that often do first-time things;
  - a long history with a warm-up;
  - raise, don't block.
- **Changed:**
  - graded rarity instead of yes/no flags plus expert risk points;
  - no peer groups (an MCP gateway has no directory);
  - one score per call before it runs, instead of a session or 24-hour sum.

### 5.9 What is new beyond "UEBA on MCP logs" (claims to defend)

1. **Scored before execution,** per call, at the protocol boundary.
2. **One risk from two layers:** a policy-derived static model scaled by behaviour with a fixed span
   (×5 = the static scale). Risk = impact × likelihood follows NIST SP 800-30.
3. **Assets resolved from free-form tool arguments** against the policy register, with no
   per-server code, and shared by both layers.
4. **Identity-minimal:** an agent id only.
5. **Label-free and calibrated:** one formula, graded rarity, and a stated false-alarm bound.
6. **Agent-specific signal:** Tool on asset catches a hijacked agent that keeps its targets but
   changes its actions.

**Not claimed:**
- that per-entity rarity is new;
- that rank-based p-values are new;
- that M stops an attacker who mimics the agent.

### 5.10 Paper text that exists

- **A LaTeX "Dynamic Risk Assessment" subsection,** in the same style as the static section. Its
  bib keys still need adding: `bates2023conformal`, `sentinel_ueba`, `exabeam_models`,
  `freeman2016whoareyou`, plus NIST SP 800-30.
- **Replacement text for the author's deck (slides 28-30).** The deck's old formula,
  e^(Baseline − Likelihood), can only move between ×0.37 and ×2.7 and stays near ×1 on real data, so
  it must become a ratio.

## 6. How the design got here (timeline)

| Date | Step |
|---|---|
| Before | **v4, the version in the author's deck.** Three groups: Typical Cadence, Typical Footprint and Red Flags. It used an excess score for amounts, a "times per day" rarity score for categories, and "the strangest dimension wins", with M = 5^(2s−1) above s = 0.5 and 0.7^(1−2s) below. A behaviour policy file held limits and required steps. |
| 25-26 Oct | **An external A* review** led to a knowledge base and **v5 revision 2**: commonness plus a record rank against the organisation, budget shares, alert and watch floors, a surge guard, 16 dimensions, M in [1, 5]. Decisions D1-D4: Read volume as a 16th dimension, M ≥ 1, Footprint may alert, USENIX '27 cycle 2. |
| 27 Oct | **D5:** history is kept per agent, never per user. MCP 2026-07-28 was analysed, and the code was ported to SDK 2.x. |
| 28 Oct | The author asked for **"one simple formula", without policy or Red Flags**, explainable to an A* venue. The day-based formula M = ((A+1)/(2D+1))^γ was proposed. Four simulated judges reviewed it; the security judge gave a weak reject, and the fixes were applied. Dimension sets of 8 and then 12 were tried; file-specific dimensions (Step, Area) were dropped as overfitting; 8 general dimensions were tested on 5 server shapes and 2 generic agents. |
| 29 Oct | **Back to the deck's version, keeping only Typical Footprint and Typical Cadence.** Six dimensions were agreed (Session length dropped, no day of week). Eleven candidate formulas (A-K) were compared, with a literature check. The author chose **counting calls, not days, for now** (formula J). The UEBA grounding, a reviewer-style critique, the settled minor rules, the defence of the claims and a 23-slide technical deck followed. |

## 7. Tests run (synthetic design checks)

**Setup:**
- 20 general scenarios on 7 kinds of synthetic agent: GitHub, Slack, Calendar, SQLite and
  Filesystem shapes with their real tool names, one always-on agent, and one with very uneven volume.
- 90 days of history each, and 132 checks per seed.
- Expectations were fixed before running.
- Results are the mean ± 95% interval over 10 development seeds.

| Candidate | Quiet (53) | One unusual thing (51) | Several at once (14) | Total (132) |
|---|---|---|---|---|
| A: deck v4 scores | 42.0 | 31.9 | 0 | 87.9 ± 1.9 |
| B: deck model as a ratio, on calls | 15.3 | 43.8 | 14 | 86.9 ± 1.1 |
| C: product of ratios (naive Bayes) | 10.0 | 34.0 | 14 | 71.8 ± 0.9 |
| D: rank on calls | 20.9 | 43.5 | 14 | 92.2 ± 1.8 |
| E: rank on days | 47.9 | 46.6 | 14 | 122.4 ± 1.6 |
| G: strangest dimension (max) | 40.2 | 50.8 | 14 | 118.8 ± 1.6 |
| H: total surprise (sum, ranked) | 52.1 | 34.1 | 12.8 | 112.9 ± 1.3 |
| **J: calls + settled rules (current)** | **21.9** | **43.6** | **14** | **93.3 ± 1.7** |
| K: days + settled rules (planned) | 49.8 | 50.5 | 14 | 128.1 ± 1.3 |

**Lessons, in order of size:**
1. **Counting days instead of calls gains about 35 checks.** Calls are not independent evidence
   (NIDES, SRI 1994), and insider-threat work counts per user-day.
2. **The combiner sets false alarms against detection.** The maximum catches the most but flags
   ordinary days; the sum is quietest but misses single signals; rarest-first does both.
3. **Tool on asset counted per asset** gains about 6 checks.
4. **The deck's e^(B−L) must become a ratio,** whichever formula is chosen.

**Known misses of the current design:**
- ordinary days come out at about ×1.4-1.9 instead of ×1;
- a new tool used daily is still about ×2.5 after two weeks;
- one huge burst day teaches the agent that bursts are normal.

All three are costs of counting calls.

## 8. Reviewer-style critique (to answer in the paper)

**Major:**
1. There is no real-data evaluation yet; the synthetic scenarios are written by the designers.
2. The security claim must name its target (for example a prompt-injected or hijacked agent acting
   out of character) and admit mimicry, pacing and fresh ids.
3. The paper ships the weaker unit, calls, against its own evidence for days.
4. The exchangeability assumption behind the bound is likely broken on real traffic.
5. Novelty must be argued as in §5.9.
6. There is no decision rule yet: no review or block thresholds, no analyst workload, no
   false-discovery control across agents.

**Moderate:**
- the constants (5, 1,000, 90 days, the windows) need justification and a sweep;
- there is no ablation of the dimensions;
- the rarest-first rule is unusual and its cost per call is unmeasured;
- the identity assumption carries everything;
- legitimate change (new tools, role change, growth, weekly rhythm) needs measuring;
- static and dynamic may overlap (Breadth against BlastRadius);
- baselines are missing;
- systems costs are unmeasured.

**Minor:** resolved in §5.6.

## 9. Ideas backlog (everything not yet done)

**Dynamic formula:**
- Count days or time buckets instead of calls (K). This is the largest measured gain, and it fixes
  quiet agents, busy agents and burst poisoning.
- If staying with calls, cap how many calls one hour can add to the history.
- A cross-agent discount for fleet-wide change: a server ships a new tool, or three or more agents
  start the same thing in a week.
- A daily accumulation score for the review list (Exabeam / Splunk style) to catch low-and-slow
  agents.
- Benjamini-Hochberg false-discovery control across agents for the daily list.
- Track the rate of new agent ids as a separate fleet signal (fresh-id evasion).
- Conformal test martingales to detect drift or poisoning.
- An e-value framing, a calibrator anchored at the mean rather than the median, as an alternative
  justification.
- Full-conformal recomputation against the cheaper, fixed-profile version, with latency measured.

**Possible dimensions (not adopted):**
- Read volume: bytes returned, seen one call late. It would cover data copied out.
- Tool rate: calls of one tool per hour.
- Step: tool order on an asset, such as a write without the usual read. Dropped as overfit to files;
  a known gap.
- Request size: now covered by static ParameterRisk.

**Static:**
- Align code and paper.
- Renormalise the weights when there is no parameter.
- Reconsider w_P.
- Fix the notation.
- Align the ToolImpact 4/5 wording.
- Run a weight-sensitivity analysis.

**Evaluation:**
- **Real data.** Candidate datasets: GH Archive (cadence), CLUE-LDS (Nextcloud logs), LANL, the
  flaws.cloud CloudTrail logs, and a risk-based-authentication login dataset.
- **Outside scenario writers (X1)** and a frozen, preregistered protocol.
- **Baselines:** the static score alone, Exabeam-style points, Freeman's login risk model, an
  isolation forest or autoencoder, and published MCP runtime monitors.
- **Ablation and sweeps:** ablation per dimension; sweeps of 5, 1,000, 90 days, the doublings and the
  ±1 hour window.
- **Operating point:** review the top k agent-days by Risk and block above X, with the analyst
  workload stated.
- **Systems:** latency and memory per call, state across gateway replicas, and folding of retries.

**Paper:**
- Add the bib entries.
- Use the dynamic LaTeX draft.
- Put the replacement deck text into the WP2 deliverable.
- Write the claims and non-claims (§5.9) into the introduction.

## 10. Open decisions for the author

1. **Unit of counting:** calls (current) or days (planned, better on every test).
2. **Static combination:** the weighted sum (paper) or the geometric mean (code), plus the value of
   w_P and the "no parameter" rule.
3. **Read volume:** whether to add it for data-exfiltration coverage.
4. **Extra layers:** whether to add the daily accumulation and the cross-agent discount.
5. **Quiet agents:** how to handle very low-volume agents (with calls, they cannot reach ×5).

## 11. Glossary

| Term | Meaning |
|---|---|
| MCP | Model Context Protocol: how AI agents call tools on servers |
| Gateway | the proxy in front of MCP servers that logs and scores every call |
| Agent id | the operator-issued identity of the calling agent; the only identity available |
| Binding layer | deterministic resolution of the asset a call names, from its arguments, against the policy register |
| Policy register | the organisation's list of assets with their sensitivity |
| Container | the asset level that binding returns: repository, channel, calendar, table or folder |
| M | the behaviour multiplier, about 0.87 to 5 |
| n, k | the agent's past calls, and how many were at least as unusual as this call |
| Mid-p | counting the current observation as half (Lancaster 1961) |
| Conformal p-value | a rank of a new observation among past ones; valid when they are exchangeable |
| UEBA | user and entity behaviour analytics (Sentinel, Exabeam, Splunk UBA, Elastic, GuardDuty) |
| Rarest-first | ranking a call by its most unusual dimension, with ties broken by the next |
| MRTR | MCP's input-required result-and-retry flow |

## 12. Key references

The numbers and statements above lean on these sources. During the week each one was opened,
checked against its publisher metadata, or taken from the project's verified notes. NIST SP 800-30
was cited from memory and not opened again.

- S. Bates, E. Candès, L. Lei, Y. Romano, M. Sesia. Testing for outliers with conformal p-values.
  *Annals of Statistics* 51(1):149-178, 2023.
- H. O. Lancaster. Significance tests in discrete distributions. *JASA* 56(294):223-234, 1961.
- D. M. Freeman et al. Who are you? A statistical approach to measuring user authenticity. NDSS
  2016.
- S. Wiefling, M. Dürmuth, L. Lo Iacono. Risk-based authentication characteristics (long-term
  study). *ACM TOPS*, 2022.
- H. S. Javitz, A. Valdes. The NIDES statistical component. SRI International, 1994.
- D. C. Le, N. Zincir-Heywood, M. I. Heywood. Data granularity levels for insider threat detection.
  *IEEE TNSM* 17(1), 2020.
- T.-F. Yen et al. Beehive: large-scale log analysis for detecting suspicious activity in enterprise
  networks. ACSAC 2013.
- I. Steinwart, D. Hush, C. Scovel. A classification framework for anomaly detection. *JMLR* 6, 2005.
- N. A. Heard, P. Rubin-Delanchy. Choosing between methods of combining p-values. *Biometrika*
  105(1), 2018.
- V. Vovk, R. Wang. E-values: calibration, combination and applications. *Annals of Statistics*
  49(3), 2021.
- L. A. Cox Jr. What's wrong with risk matrices? *Risk Analysis* 28(2), 2008.
- NIST SP 800-30 Rev. 1, *Guide for Conducting Risk Assessments*, 2012.
- Vendor documentation: Microsoft Sentinel UEBA reference; Exabeam Advanced Analytics (models,
  rules); Elastic ML time functions; Okta behavior detection; Microsoft Entra ID Protection risk
  detections; AWS GuardDuty IAM finding types.

## 13. Repository pointers (for the author)

| File | What it holds |
|---|---|
| `reports/experiments/dynamic_dimensions/knowledge_base/dynamic-score-report.md` | The reference report for the dynamic score, with the LaTeX draft |
| `reports/experiments/dynamic_dimensions/knowledge_base/behaviour-formula-candidates.md` | The comparison of candidates and the literature check |
| `reports/experiments/dynamic_dimensions/knowledge_base/static-and-dynamic-formulas.md` | The static score and the earlier dynamic design |
| `reports/experiments/dynamic_dimensions/knowledge_base/03-ueba-insider-threat-and-datasets.md` | The verified UEBA sources and candidate datasets |
| `reports/experiments/dynamic_dimensions/knowledge_base/probes/m_formula_candidates.py` | The test. Run `--seeds 101,…,110` for intervals and `--explain` for reasons |
| Slide deck "Dynamic Risk Score: Formula and Justification" (claude.ai artifact, 23 slides) | The deck version of this brief |
