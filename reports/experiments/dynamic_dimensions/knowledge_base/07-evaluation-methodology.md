# Evaluating the dynamic layer: what A* venues expect, and a protocol for the paper

This note fixes, from sources opened on 2026-10-25, what security venues (IEEE S&P, USENIX Security,
CCS, NDSS) and software-engineering venues (ICSE, FSE) expect from the evaluation of an anomaly- or
behaviour-based detection layer, reads the current simulation of the dynamic layer (design v4)
against those expectations, and writes a concrete evaluation protocol. Threat model as everywhere in
this repo: the MCP server and the assets behind it are the protected asset, the calling agent is the
threat; the paper's threat model counts misuse "regardless of whether the operation originates from
benign error, excessive delegation, compromised behavior, or malicious intent" (`main-restructured.tex`
§Threat Model), so both gray misuse and an adaptive agent are in scope.

## Answers in brief

1. **The current numbers are design-set numbers.** All five simulated organisations (seeds 7, 11,
   21, 31, 41) were used while v2, v3 and v4 were designed: 37 engine variants were scored on the main
   organisation alone. That is *test snooping* and *biased parameter selection* in Arp et al.'s terms
   (P3, P5). The design doc already admits it ("catch rates optimistic"). The headline numbers must
   come from worlds and scenarios that were never looked at.
2. **Seeds alone are not enough.** The generator, its gray kinds and the detector share one author,
   and the org-wide changes always fall on days 110, 130 and 150. New seeds test overfitting to a
   seed, not to the generator. Scenarios written by people who never saw the detector (Sommer &
   Paxson: ground truth "via a mechanism orthogonal (unrelated) to how the detector works"), and a
   real-traffic replay, are what close that gap.
3. **The measures are already of the kind reviewers want.** Ordinary agent-days at ×3 and a daily
   review list of fixed size are an operational, budget-based framing, as in Ho et al. (USENIX Sec
   2017, a budget of 10 alerts a day set by the site's security team) and Tuor et al. (a daily budget
   of user-days). What is missing: precision and the base rate, low-FPR curves, confidence intervals,
   external baselines and an adaptive adversary.
4. **The base rate is designer-chosen.** In the main organisation about 1 new gray episode starts per
   day for 150 agents, and gray agent-days are only 10–15% of the agent-days at ×3 (5 worlds, v4).
   With a realistic, lower prevalence, precision at ×3 drops in proportion (Axelsson 2000). The
   protocol reports precision as a function of an assumed prevalence, not at the simulator's.
5. **Current intervals are wide.** Main organisation, v4: 50 of 79 gray episodes caught at ×3, 63%,
   Wilson 95% CI [52%, 73%]. Per kind, e.g. scope creep 12/40 → [18%, 45%]. "One mass cleanup lost,
   one scope creep gained" between v3 and v4 is inside the noise. The paper must not claim it.
6. **Combiners can be compared offline, at equal budget.** The engine's state never depends on `M`,
   so max, mean, noisy-OR, `s1 + 0.3·s2·(1 − s1)`, Tippett and Fisher can all be recomputed from the
   logged per-call score vectors. The design doc says the combiner arm needs a rerun; it does not.
7. **Several constants are not free.** Within the dynamic layer, `M = 5^(2·s1 − 1)` is monotone in
   `s1`, so the review list is unchanged by the bounds 0.7 and 5. At a fixed ×3 line, the upper bound
   only moves the line in score space (`s1 ≥ 0.841` at 5). The bounds matter for gating and for
   `R = R_static × M`, and that is where their sensitivity must be measured.
8. **Statistics.** Make the world (organisation × seed) the unit of replication, with ≥ 30 held-out
   worlds per family. Compare designs paired by world (Wilcoxon signed-rank, Holm correction, effect
   sizes). Give per-kind rates with Wilson intervals, and pooled rates with a cluster bootstrap.
9. **Venue mechanics.** USENIX Security '26 requires an "Ethical Considerations" appendix and an
   "Open Science" appendix, with artifacts available at submission on a persistent host such as Zenodo
   (GitHub is not accepted). The ACM SIGSOFT Simulation standard lists "overfitting the simulation
   model to reproduce a reference behavior" and "a single run" as antipatterns.

## 1. What the venues expect

### 1.1 Arp et al. 2022, the ten pitfalls, mapped to our setup

Arp et al. (USENIX Security 2022, Distinguished Paper) studied 30 papers from CCS, S&P, USENIX
Security and NDSS. The share of papers with each pitfall is from their Section 2.

| Pitfall (share of 30 papers) | What it means | Our setup today | Fix in this protocol |
|---|---|---|---|
| P1 Sampling bias (60%) | data does not represent the true distribution | one generator, written by the designers; one server (GitHub); gray kinds and their rate chosen by us | §3.1 new profiles, §3.2 independent scenarios, §3.3 real traffic; "construct different estimates of the true distribution and analyze them individually" (Arp) |
| P2 Label inaccuracy (10%) | labels wrong or unstable | labels exact by construction, but the *construct* is open: is a back-from-vacation day a false alarm? is "gray" worth a review? | count change days as false alarms in the primary endpoint and break them out (§3.7); human study (`human_study/`); two independent labellers for new scenarios |
| P3 Data snooping (57%) | test data used before final evaluation: "preparatory work to identify useful features, parameters, and learning algorithms" | 37 variants on the main world, 15–17 on each of the others; v3/v4 detectors designed after seeing v2's misses; the human-study cards come from seed 7. Temporal snooping is avoided *inside* a world (history up to yesterday, limits from days 0–29) | §3.1 freeze, burn the used seeds, preregister; "test data should be split early … and stored separately until the final evaluation" (Arp) |
| P4 Spurious correlations (20%) | detector keys on artifacts | possible generator artifacts: fixed org-change days 110/130/150, gray window days 95–172, the personal script always at 1–3 a.m., fixed paste ranges | randomise schedules (§3.1), intensity sweeps and new kinds (§3.2), check that the reason `d*` matches the risk the scenario author named |
| P5 Biased parameter selection (10%) | thresholds or constants tuned on the test set | tolerance 2, units, ceilings 0.9, the 5 and 0.7, flag values, floors, 14 onboarding days, 4 weekend pseudo-days, org discount 3/7: "checked by simulation" on the same five worlds | freeze them (§3.1); sensitivity analysis is descriptive, not tuning (§3.5) |
| P6 Inappropriate baseline (20%) | no or weak baselines | only our own v1–v3 | §3.6: static only, Red Flags only, per-agent z-score, Isolation Forest, peer group; tuned fairly |
| P7 Inappropriate measures (33%) | measures that ignore imbalance and a low FP budget | operational measures already (×3 rate, daily list) | add precision at budget, recall@budget curves, bounded AUC, per-100-agents-per-day units (§3.7) |
| P8 Base-rate fallacy (10%) | imbalance ignored when interpreting | gray prevalence set by `GRAY_KINDS` weights; not discussed | Bayes precision at assumed prevalence (§1.3, §3.7) |
| P9 Lab-only evaluation (47%) | only lab setting | the dynamic evaluation is all simulation. The paper's §Evaluation Settings says the dynamic evaluation uses "invocation logs collected from the deployments" (line ~1040), which does not match | §3.3 GH Archive replay and a shadow deployment of the gateway; fix the paper text |
| P10 Inappropriate threat model (17%) | adversarial ML ignored | the agent is the threat, yet no adaptive agent is evaluated; the safety valves (habit discount, org discount) can be gamed | §3.2 white-box tier: "an evaluation of adversarial aspects is not an add-on but rather a mandatory component" (Arp) |

Arp's recommendations that apply directly:
- Simple and non-learning baselines (P6).
- Precision–recall and "curves only up to tractable false-positive rates", with bounded AUC (P8).
- Discussing "false positives in relation to the base rate of the negative class, which enables the
  reader to get an understanding of the workload" (P8).
- "Temporal and spatial relations of the data should be considered" (P9).
- An adaptive, white-box adversary (P10).

### 1.2 Sommer & Paxson 2010, "Outside the Closed World"

IEEE S&P 2010, pp. 305–316. The five challenges and what each asks of us:

| Challenge (their §III) | For the dynamic layer |
|---|---|
| Outlier detection under a closed-world assumption | the layer finds the *strange for him*, not the malicious. Say so, and evaluate gray misuse and benign look-alikes, not only attacks |
| High cost of errors: "limiting false positives must be a top priority" | lead with the false-alarm budget (already the design's framing) |
| Semantic gap: "What does it mean?" | the reason `d*` is the answer. Measure it: does `d*` name the risk the scenario author meant? (human study, §3.2) |
| Diversity of traffic | several organisations, profiles and servers; never one world |
| Difficulties with evaluation: data, and "Mind the Gap" | simulation "will often lack any plausible degree of realism or relevance" for novel attacks. Hence §3.2–§3.3 |

Their evaluation recommendations (§IV-D), which reviewers still quote:
- Answer "What can it detect, and why? What can it not detect, and why not? How reliably does it
  operate? Where does it break?" They call failing to do so "the #1 reason that conference
  submissions on anomaly detection fail".
- "One always needs multiple datasets": train and test on different data, and use data "from
  multiple sources" to show the system adapts to different environments.
- "Researchers need to manually examine false positives", using a random sample if there are too
  many. Also inspect true positives and true negatives.
- Collect ground truth orthogonally to the detector. "A final compromise is to inject a set of
  attacks deemed representative", which is what we do now.
- "Mediated trace access": bring the experiment to the data, so a partner organisation can run the
  frozen engine on its own logs and return aggregates.
- "The most convincing real-world test … is to solicit feedback from operators who run the system."

### 1.3 Axelsson 2000, the base-rate fallacy

ACM TISSEC 3(3):186–205; an earlier version appeared at CCS 1999, pp. 1–7.
- The false-alarm rate, not detection, "is the limiting factor for the performance of an intrusion
  detection system".
- "One should measure the false alarm rate in relation to how many intrusions one would expect to
  detect". In his scenario this required fewer than 1/100,000 false alarms per event.
- He also stresses the choice of unit; he used 10 audit records.

Applied to v4, from `results/normal_org_*.json`:

| World | Active agent-days scored | Ordinary agent-days at ×3 | ×3 agent-days per day: ordinary · change · gray | Gray share of ×3 agent-days |
|---|---|---|---|---|
| Main (seed 7) | 9,537 | 2.68% | 2.10 · 3.09 · 0.57 | 9.9% |
| Second seed (11) | 9,453 | 2.83% | 2.26 · 3.19 · 0.64 | 10.5% |
| Heavy files (21) | 9,419 | 1.83% | 1.33 · 3.12 · 0.70 | 13.6% |
| Small (31) | 4,033 | 2.51% | 0.70 · 1.74 · 0.30 | 10.8% |
| Large (41) | 18,630 | 2.46% | 3.93 · 5.04 · 1.53 | 14.5% |

- **Benign triggers outnumber the rest.** Labelled life and org changes (the "change" column) are the
  largest share of ×3 agent-days. Alahmadi et al. call this kind of alarm a *benign trigger*: "true
  alarms, explained by legitimate behavior". Researchers must "make such distinctions between types
  of FP", so report them separately.
- **Precision moves with prevalence.** About 79 episodes start in 77 days among 150 agents (gray
  window days 95–172). Precision at a fixed operating point is
  `π·TPR / (π·TPR + (1 − π)·FPR)`, so a real organisation with a tenth of that prevalence would see
  roughly a tenth of the gray share. Report this curve over π.
- **The unit matters.** Ordinary *calls* at ×3 are 0.1%, but they cluster in about 2 agent-days a
  day. State the unit (agent-day) and keep the call-level number for gating.

### 1.4 Fixed false-alarm budgets: the precedents

| Source | How the budget is set and used |
|---|---|
| Ho et al., USENIX Sec 2017 | a daily budget of 10 alerts, "specified … as a very tolerable number" by the site's security team (LBNL), split across sub-detectors. Baselines are compared (1) at the same budget and (2) by the budget they would need to catch the same attacks. Classical baselines were given their best hyperparameters. The realised daily load is checked: 80% of 100 random days had ≤ 10 alerts |
| Tuor et al., 2017 (arXiv 1710.00811) | rank user-days. A fixed daily budget "cannot be carried over from one day to the next". Cumulative recall CR-k (sum of recall at budgets 25, 50, …, k). Chronological development/test split, about 85/15 |
| Alahmadi et al., USENIX Sec 2022 | SOC analysts on false positives. Benign triggers dominate. Five alarm properties: Reliable, Explainable, Analytical, Contextual, Transferable |
| Hassan et al. (NoDoze), NDSS 2019 | "threat alert fatigue": more alerts than analysts can investigate. The evaluation reports the false-alarm reduction and the analyst hours saved |

Our daily review list (top 4 of 150 agents, top 8 of 300) is already a budget of about 2.7 per 100
agents per day. The protocol keeps it, sweeps it, and adds the Ho et al. "budget needed to match"
comparison.

### 1.5 Low false-positive curves

- ROC curves "may obscure experimental results" under imbalance; PR curves change with the class
  ratio and ROC curves do not (Arp P7–P8; Saito & Rehmsmeier 2015).
- For the low-FPR region use the partial area under the ROC curve over an a-priori FPR range
  (McClish 1989), Arp's "bounded AUC". Here that range is 0–5% of non-gray agent-days, the region
  around the budget.

### 1.6 Statistics, preregistration and SE-venue norms

| Source | Rule we adopt |
|---|---|
| Arcuri & Briand, ICSE 2011 | randomised runs must be repeated. "At least n = 1,000 times" per problem instance where feasible, else justify. Use Mann–Whitney U (or Fisher's exact test for success counts), "report all the obtained p-values", and always give standardised effect sizes (Vargha–Delaney Â12) with confidence intervals |
| Demšar, JMLR 2006 | across several datasets (here: worlds), the Wilcoxon signed-ranks test for two methods, and Friedman with post-hoc tests for more |
| ACM SIGSOFT Empirical Standards, Simulation (Quantitative) | *essential*: describe the model, its calibration data, its verification and validation, and the "number of runs per scenario". *Desirable*: "reports sensitivity analysis for input parameters". *Antipatterns*: overfitting the model to reproduce a reference behaviour; a single run. *Invalid criticism*: rejecting generated data "when no appropriate primary data is available" |
| Brown, Cai & DasGupta 2001 | no Wald intervals for proportions. Use Wilson or Jeffreys for n ≤ 40 and Agresti–Coull for larger n |
| Field & Welsh 2007 | a cluster bootstrap (resample whole clusters) gives consistent variance estimates under both clustered-data models they study. Clusters here: agents within a world, and worlds |
| Holm 1979 | a sequentially rejective multiple test, for the families of ablation and combiner comparisons |
| Nosek et al., PNAS 2018 | preregistration separates prediction from postdiction, including "when the data are preexisting" |
| Kapoor & Narayanan, Patterns 2023 | leakage found in 294 papers across 17 fields, sorted into eight types, and caught with "model info sheets". Fill one in for the simulator |
| Glasser & Lindauer, IEEE SPW 2013 (CERT data authors) | synthetic insider data served integration and "confirmatory hypothesis testing", but "exploratory uses of this synthetic data are not fruitful" |
| Engelen et al., IEEE SPW 2021 | the CICIDS2017 benchmark had generation and labelling errors: "more than 20 percent" of traces were reconstructed or relabelled. Validate a generator, don't trust it |

### 1.7 Adaptive adversary, and space and time

- Wagner & Soto (CCS 2002): *mimicry*, where an attacker cloaks the attack so that it looks normal
  to an anomaly IDS.
- Carlini et al. (arXiv 1902.06705): defences must be tested against adaptive attacks. Most defences
  that were not "are quickly shown to be incorrect".
- Pendlebury et al. (TESSERACT, USENIX Sec 2019): *spatial* bias (test distribution unlike
  deployment) and *temporal* bias (impossible time splits). Both apply when the test worlds have
  another gray prevalence, or when history and test days mix.

## 2. Our setup today, read against these expectations

- **Worlds.** `normal_org_world.py`: 180 days, days 0–89 history, days 90–179 scored. Profiles `main`
  (seeds 7, 11), `heavy_files` (21), `more_pastes` (31 with 60 agents, 41 with 300). Earlier
  experiments in this folder used seeds 1, 2, 11 and 12 (`world.py`). Seeds burnt so far:
  **{1, 2, 7, 11, 12, 21, 31, 41}**.
- **Fixed schedule.** `VPN_CHANGE_DAY, ROLLOUT_DAY, MIGRATION_DAY = 110, 130, 150`;
  `CRUNCH_DAYS = range(120, 124)`; `GRAY_FROM, GRAY_TO = 95, 172`. A designer who knows these days can
  tune for them. Life events (vacations, switches, transfers) are random per agent.
- **Gray kinds.** 10 weighted kinds in `GRAY_KINDS`, plus a misconfigured bot loop. 460 episodes over
  the five worlds; the detectors of v3 were built "after seeing what v2 missed".
- **Learned limits** come from days 0–29 of each world (`policy.py`, quantile 0.995), as in a
  deployment, so there is no temporal leakage there.
- **Port check.** The shipped engine equals the simulation engine on every message
  (`--check-port`). This is good *verification* evidence in the Simulation standard's sense; it is
  not *validation*.
- **Intervals today**, Wilson 95%, which ignore clustering and are too narrow:

| Quantity | Value | 95% CI |
|---|---|---|
| Main, v4, gray caught at ×3 | 50/79 = 63% | [52%, 73%] |
| All five, v4, gray caught at ×3 | 325/460 = 70.7% | [66.3%, 74.6%] |
| Scope creep / mass cleanup / copy from sensitive, v4 | 12/40 · 8/34 · 20/42 | [18, 45] · [12, 40] · [33, 62] % |
| Over-fetching, v4 | 0/47 | [0%, 7.6%] |
| Main, ordinary agent-days at ×3, v3 → v4 | ≈305 → 256 of 9,537 | [2.9, 3.6] → [2.4, 3.0] % |

- **What the paper needs.** The v3 → v4 false-alarm drop is the more trustworthy result: it is paired
  on the same worlds and was not the selection target. It still needs held-out worlds before it is a
  claim. The paper's §Dynamic Assessment (line ~1088) is the place for this protocol, and
  §Evaluation Settings (line ~1040) must stop saying the dynamic evaluation uses deployment logs
  until §3.3 exists.

## 3. The protocol

### 3.0 The evidence ladder

Each level removes one source of optimism. Report every level that was run, side by side; the gap
between level 0 and the others is itself a result.

| Level | Data | Removes | Status |
|---|---|---|---|
| 0 Design worlds | seeds 7, 11, 21, 31, 41 | nothing (optimistic) | done |
| 1 Held-out seeds | same 3 profiles, new seeds | overfitting to a seed | to do (§3.1) |
| 2 Held-out families | new profiles, sizes, schedules, a 365-day horizon, other servers | overfitting to a profile, the fixed calendar, the time window, GitHub | to do (§3.1) |
| 3 Independent scenarios | gray and benign episodes written by people who never saw the detector; a white-box red team | generator/detector circularity; adaptive agents | to do (§3.2) |
| 4 Real background | GH Archive replay; LANL as a secondary check | the realism gap of synthetic ordinary life | to do (§3.3) |
| 5 Shadow deployment | the observe-only gateway on real MCP traffic, with operator feedback | lab-only | to do (§3.3) |

### 3.1 Freeze the design, preregister held-out worlds

**Freeze.**
- Tag one commit (e.g. `dyn-v4-frozen`) and record the SHA-256 of `engine.py`, `memory.py`,
  `policy.py`, `normal_org_world.py`, `normal_org_engines.py`, `normal_org_sim.py` and
  `DIMENSION_FORMULAS.md`.
- Frozen with it: the `BehaviourConfig` defaults, `MAX_MULTIPLIER`/`MIN_MULTIPLIER`, `ALERT = 3.0`,
  the list budget (top 4 per 150 agents), and the learned-limit procedure (30 days, q = 0.995).

**Preregister** before generating any held-out world: on OSF (Nosek et al.), or as a timestamped
Zenodo record.
- The hypotheses and primary endpoints.
- The seed derivation, the profile priors and the analysis script, committed and runnable.
- The decision rules, and what counts as a deviation.

**Seeds that cannot be cherry-picked.** Derive the test seeds *after* freezing, from the frozen
commit's hash: the first 30 values of `SHA-256(commit ‖ "test" ‖ i) mod 2^31` per family, skipping
burnt seeds. Derive a separate *calibration* pool (`‖ "calib"`, 10 per family) for:
- the between-world SD pilot;
- threshold matching of combiners and baselines (§3.4, §3.6);
- Morris screening (§3.5).

The test pool is scored once.

**Families**, each with ≥ 30 test worlds:
- **F1:** the three existing profiles at 150 agents.
- **F2:** new profiles. Draw each `Profile` field and the role mix from preregistered ranges (e.g.
  `file_write_kb` 1–16, role mix from a Dirichlet around the current one), and the size from
  {50, 100, 200, 400, 800}.
- **F3:** F1 with the org-wide change days and the gray window randomised per world.
- **F4:** 365-day worlds, scored on days 90–364, for drift (TESSERACT's temporal axis).
- **F5:** another server (Slack or Calendar tools with their static levels). `world2.py` already has
  multi-server worlds; port its tools to the `normal_org_world` generator.

**Endpoints**, examples to be fixed before freezing:
- **E1 (quiet):** ordinary agent-days at ×3, mean over worlds. Upper 95% bound ≤ 3.0% in each family;
  change days counted as false alarms, then broken out.
- **E2 (useful):** gray-episode recall on the daily list at 2.7 per 100 agents. Lower 95% bound
  reported, *on level-3 scenarios*.
- **Secondary:**
  - change days at ×3 by kind;
  - recall by kind;
  - share of an episode's calls at ×3 (for gating);
  - median days to first detection, for slow episodes;
  - realised daily load (Ho et al.'s check).

**After the run.** If a held-out result prompts a design change, it is v5. Report v4's held-out
numbers as they are, and give v5 new held-out worlds.

### 3.2 Independently constructed scenarios

**Black-box authors.** 3–5 people (security practitioners or students) who have not seen
`DIMENSION_FORMULAS*`, the engine or any result.
- *They get:* the threat model (server protected, agent the threat), the GitHub MCP tool catalogue
  with static levels and operations, the organisation (teams, repositories and their sensitivity,
  roles, clients), and a template. The template asks for: who; when; how many calls; which tools and
  assets; how long; and a label ("should a reviewer look at this agent today?", plus severity 1–3
  and *the one thing that makes it risky*).
- *They write:* at least 30 risky gray scenarios and at least 30 *benign look-alikes* (ordinary
  life the generator lacks: a reorg, a hackathon weekend, an audit export, a new bot). The
  look-alikes test E1, not only E2.
- *Labels:* a second author labels every scenario blind. Report agreement (Cohen's κ). Two
  dissenting labels exclude a scenario, by a rule fixed in advance.
- *Implementation:* a neutral implementer compiles the scenarios into episode code for
  `normal_org_world.py`. Hash it before the first scoring run; the detector's authors see only
  aggregate results.
- *Injection:* inject them into F1–F3 test worlds and into real backgrounds (§3.3), with
  preregistered rates and a sweep of intensity (e.g. 0.5×, 1×, 2× the author's numbers).

**White-box red team.** People who *do* get the formulas and the shipped engine (Kerckhoffs; Arp
P10; Carlini et al.).
- *Goals:* read three sensitivity-5 repositories; export 40 repositories; paste 200 KB. Each goal
  must be reached within 30 days without a ×3 agent-day, or without a place on the daily list.
- *Report:* the success rate, and the cost (days of preparation, extra calls).
- *Required attack classes:*
  - mimicry (Wagner & Soto);
  - baseline widening within tolerance 2 and the 90-day window
    (`scripts/dynamic_design/evaluate_dynamic.py --only poisoning` does this for the Gen-2 layer;
    port it to v4);
  - training the habit discount (raise a flag a little on many days);
  - org-discount laundering: 3 colluding identities start the same new tool, network or client
    within 7 days, which caps each other's score at 0.5. The first-access floor is not discounted,
    so check it holds;
  - splitting across sessions and identities.

**Explanation.** For every caught scenario, check whether `d*` (or `s2`) is the dimension the author
named. Reasons that are wrong but still catch the scenario are Arp's P4 in miniature. The
human-study cards (`human_study/`) measure the same thing with people. Redraw them from a test world;
seed 7 is burnt.

**External sets in other domains.** The CERT Insider Threat Test Dataset (r1–r6.x, synthetic, with
an answer key) and the LANL red-team events were authored by others. They can act as
independent-author checks only after mapping to agent-days. Coordinate with the UEBA-datasets entry
of this knowledge base for fields and licences.

**LLM-authored scenarios** (a model with no access to the repo) are cheap extra volume. They are not
independent of the designers' assumptions; report them apart.

### 3.3 Real traffic: a public replay and a shadow deployment

**GH Archive** (primary). It records the public GitHub timeline, with "15+ event types" in hourly
archives since 2011-02-12, also on BigQuery. Each event carries `actor`, `repo`, `org`, `created_at`
and a type-specific `payload`.

*Selection rule (preregistered):* for example, the 20 public organisations with the most distinct
active actors in one fixed 270-day window. That gives 90 days of history and 180 scored. Exclude
organisations the authors belong to.

| Event type | MCP tool (GitHub server) | Operation | Size for "oversized request" |
|---|---|---|---|
| `PushEvent` | `push_files` | write | commit count |
| `CreateEvent` (branch / repository) | `create_branch` / `create_repository` | write | |
| `IssuesEvent` opened / edited, closed | `create_issue` / `update_issue` | write | issue body length |
| `IssueCommentEvent` | `add_issue_comment` | write | comment body length |
| `PullRequestEvent` opened / merged | `create_pull_request` / `merge_pull_request` | write | PR body length |
| `PullRequestReviewEvent` | `create_pull_request_review` | write | review body length |
| `ForkEvent` | `fork_repository` | write | |

*Dimensions that run:* call rate, write rate, breadth, repetition, hour of day, tool, asset, burst,
sweep, and oversized request.

*Dimensions that cannot run:* network, client, session duration and missing handshake (the last
two never take part under MCP `2026-07-28` traffic either; see `01-mcp-protocol.md`), unsafe
sequence (no reads), and the first-access floor (no sensitivity; leave it off rather than invent
labels).

*What it measures:*
- The false-alarm *load* on real human and bot cadences: vacations, releases, newcomers, bots. It is
  an upper bound, because the data is unlabelled.
- The causes `d*`.
- A blind manual review of a random sample of ~100 alerted actor-days by two raters, sorted as
  benign trigger / unexplained / worth a look (Sommer & Paxson; Alahmadi et al.).
- Injecting the §3.2 scenarios into these real backgrounds gives recall on real ordinary life.

*Caveats:*
- Public events only, so each actor is seen partially.
- Humans act through the web UI and git as well as APIs, so this is a cadence proxy for agents.

*Ethics:* the data is public, but this is per-person behavioural profiling. Pseudonymise actors,
report aggregates only, and cover it in the Ethical Considerations appendix.

**LANL "Comprehensive, Multi-Source Cyber-Security Events"** (secondary). This is real, de-identified
data: 58 days, 12,425 users, about 1.65 billion events, with labelled red-team events. 58 days is
shorter than the 90-day window, so run it as a *declared* sensitivity arm (window 30 days, days
31–58 scored), never as the primary.

**Shadow deployment** (MCP-specific, the strongest evidence). Put
`uv run python -m mcp_security.gateway.proxy` in observe-only mode in front of a real GitHub MCP
server, used by the lab's own agents with consent.
- Run it for at least 120 days: 90 of history, then 30 or more scored.
- Each week an operator reviews the top-k list and marks each item useful, benign trigger or noise.
  This is the "feedback from operators" Sommer & Paxson ask for.
- Through mediated access, a partner organisation can run the frozen engine and return the
  endpoint aggregates only.

### 3.4 Combiners at an equal false-alarm budget

**Why offline works.** `BehaviourEngine.observe` returns the full `scores` dict for `D(c)`, and no
state update reads `M`: habit days, first uses and history all depend on raw events. So every
combiner is a function of the logged score vectors and needs no rerun. Log `Verdict.scores` for
every call of the test worlds once.

| Arm | Per-call statistic | Note |
|---|---|---|
| max (v4) | `s1` | the frozen design |
| mean | mean of `s_d` over `D(c)` | dilution |
| noisy-OR | `1 − ∏(1 − s_d)` | the `s_d` are not probabilities. Ordinary scores of about 0.33 saturate it (10 of them give 0.98), so also run it on `max(0, 2·s_d − 1)` |
| top-2 blend | `s1 + 0.3·s2·(1 − s1)` | tested before, on the design worlds |
| Tippett | `1 − (1 − min p_d)^{|D(c)|}` | Šidák-adjusted min-p. Most sensitive to the smallest p (Heard & Rubin-Delanchy) |
| Fisher | `−2 Σ log p_d`, ranked by χ²(2·|D(c)|) | independence is violated (a loop raises call rate, repetition and burst together), so use it as a ranking statistic, not a test |

**p-values without labels.**
- *Cadence and Footprint:* the conformal p-value `p_d = (1 + #{c′ : s_d(c′) ≥ s_d(c)}) / (n + 1)`
  over the agent's own calls in his window, up to yesterday. Use all past calls, as a deployment
  would; filtering by label would be selective snooping. Bates et al. prove such p-values are
  marginally valid but can never fall below `1/(n + 1)`. So calibrate per call, not per agent-day (a
  90-day window gives ≥ 1/91), and add a pooled-peers variant for agents with little history.
- *Red Flags:* `p_f = (1 + k_f)/(A + 1)` when raised. This is the habit discount's own frequency.

**What it tests.** The rarity score is already an empirical p-value ("this thing + everything
rarer"). So max ≈ Tippett *within* Footprint, and the arms differ mainly *across* groups. That
tests the design's claim that all scores share one scale with 0.5 at the edge of ordinary.

**Equal budget, two ways.**
- **List budget:** the top-k agent-days per day, k ∈ {1, 2, 4, 8, 16} per 150 agents. It is equal
  by construction. Report recall@k with CR-k (Tuor et al.).
- **Threshold budget, for gating:** pick each arm's threshold on the calibration pool so that 2.5%
  (also 1% and 5%) of non-gray agent-days alert, freeze it, and apply it to the test pool. Report
  the *realised* rate (does the calibration transfer? Arp P5), recall, and Ho et al.'s "budget
  needed to match max's recall".

**Statistics.**
- Paired by world: Wilcoxon signed-rank on per-world differences from max, with Holm correction over
  the 5 comparisons.
- Report the median difference with a bootstrap CI, and Â12.
- Break the result down by kind. Mass cleanup (medium signals that add up) is where sums should win.
  Single-signal kinds (peek, new client) are where max should win.
- *Example decision rule:* keep max unless an arm beats it by more than 3 points of E2 at equal
  budget (Holm-adjusted p < 0.05) without losing the one-reason explanation.

### 3.5 Sensitivity of the constants

**First, what the formula fixes analytically.** The ×3 line is `s1 ≥ 0.5 + ln 3 / (2 ln 5) = 0.841`.

| Constant | What ×3 means at the default | Consequence for the analysis |
|---|---|---|
| Tolerance τ = 2 | excess: `(x + u)/(μ + u) ≥ 5.30·τ` = 10.6 × his usual. Rarity with c = 1 (asset, hour): rarer than once in 10.6 days; with c = 0.9 (tool, network, client): once in 28.7 days. A flag at 0.9 stays at ×3 or more while raised on ≤ 3.5% of his active days (the habit discount also uses τ) | τ moves all graded scores but not the flag values, so it interacts with them. That is why the analysis must be global, not one factor at a time (Saltelli et al.) |
| Ceilings 0.9 | a never-seen tool, network or client tops out at ×3.62 | discontinuous near 0.841: at a ceiling ≤ 0.84 they never alert alone. Sweep {0.80, 0.84, 0.86, 0.90, 0.95, 1.0} |
| Upper bound 5 | `M` is monotone in `s1`, so the review list is unchanged by it. At a fixed ×3 the line moves: B = 4 → `s1 ≥ 0.896`, B = 8 → 0.764, B = 3 → only `s1` = 1 | not a detection parameter of the list. Measure it on gating and on `R = R_static × M` (main world, top 4: ranking by static × M caught 36.7% of gray episodes vs 58.2% for (M, s2)) |
| Lower bound 0.7 | touches only `s1` < 0.5, never an alert | measure it only on the ordering of R among ordinary calls |
| Missing handshake 0.7, first-access floor 0.8 | ×1.9 and ×2.63: neither alerts alone, by design | state it, no sweep needed |

**Then the experiment.** It is descriptive robustness, not tuning (§3.1).

| Factor | Default | Range | Offline from a raw log? |
|---|---|---|---|
| tolerance τ | 2 | 1, 1.5, 2, 3, 4 | yes, if `(x+u)/(μ+u)`, `e_d` and `k_f` are logged per call |
| ceilings (tool, network, client) | 0.9 | 0.80–1.0 as above | yes (`e_d` logged) |
| bounds | 0.7 / 5 | 0.5–1.0 / 4–10, at a fixed ×3 and at a fixed `s1` line | yes |
| flag value / floor values | 0.9 / 0.9, 0.8 | 0.8–1.0 / ±0.1 | yes |
| history window | 90 days | 30, 60, 90, 120, 180 (needs longer worlds: N_DAYS = window + 180) | no, rerun |
| limit quantile | 0.995 (0.5%) | 0.99, 0.995, 0.998, 0.999 | yes, if raw size, busiest minute and busiest hour are logged; recompute habit days in sequence |
| org discount | 3 agents / 7 days | {2, 3, 5, 8} × {3, 7, 14, 30}, and a size-scaled variant (a share of agents) | yes, if first-use events are logged |
| onboarding, weekend blend, warm-up | 14 days, 4 pseudo-days, first day | 0–28, 0–8, {none, 5 calls, first day} | no, rerun |

**Method.**
1. On the calibration pool, run Morris elementary-effects screening (Morris 1991: randomised
   one-factor-at-a-time trajectories, runs proportional to the number of factors k; e.g. r = 20
   trajectories × (k + 1) runs). Rank factors by μ* (influence) and σ (non-linearity or
   interaction).
2. For the 2–3 most influential factors, run a full factorial on test worlds, plus tornado plots
   for the rest.
3. Report each endpoint (E1, E2, change days at ×3) over the whole box, and the fraction of the box
   where the preregistered claims still hold.

Logging the raw statistics once (a small change to the simulation engine, not yet made) makes all
but the window, onboarding, weekend and warm-up offline, and the global analysis cheap.

### 3.6 Ablation and baselines

**Ablation.** Run the arms planned in `DIMENSION_FORMULAS.md` (Future work) as planned, with three
changes:
- run them on the test pool, not the design worlds;
- report per-world paired differences from v4 with Holm correction over the family of 15 + 3 + …
  arms;
- recompute the dimension, group and combiner arms offline (§3.4); only the safety valves and the
  warm-up need reruns.

Add the open decision on the review list (first-access floor counted twice in `s2`) as one more
arm, preregistered.

**Baselines (Arp P6).** Tune each on the calibration pool with its best hyperparameters, as Ho et
al. did. Compare at equal budget.

| Baseline | Why |
|---|---|
| static only (`M` ≡ 1) | what the dynamic layer adds |
| Red Flags only | the "non-learning approach" check |
| per-agent max-\|z\| on agent-day counts (calls, writes, distinct assets, distinct tools, new values) | the textbook per-user baseline |
| Isolation Forest on per-agent-day feature vectors, trained on history days only | the strongest baseline in Tuor et al. |
| peer-group (role) reference | the folder's earlier peer references (`detectors.py`) |
| v1, v2, v3 | our own path; on held-out worlds this re-tests "18% fewer false alarms" |

### 3.7 Reporting, with intervals over worlds

**Unit of replication.** The world. Run ≥ 30 test worlds per family, justified against Arcuri &
Briand's 1,000-run guideline by measured cost. Use the calibration-pool SD to check the CI
half-width before running: e.g. ±0.2 points on E1 and ±3 points on E2.

**Intervals.**
- Per-world endpoints: mean and a 95% percentile bootstrap over worlds.
- Pooled episode rates: a cluster bootstrap with the world as cluster (Field & Welsh).
- Per kind: Wilson or Jeffreys, since n is often ≤ 40 (Brown et al.).
- Inside one world, resample agents, not agent-days. Habits make an agent's alerts correlated.

**Comparisons.**
- Wilcoxon signed-rank paired by world (Demšar), with Holm correction within each family of tests.
- Report all p-values, Â12, and the median paired difference with its CI.
- Equivalence claims ("the same episodes are caught") need a margin fixed in advance, with the 90%
  CI inside it.

**Tables and figures.**
1. Design worlds vs each held-out family vs independent scenarios vs real background, side by side,
   for E1, E2 and change days.
2. Recall@budget curves with CI bands, and the pAUC over 0–5% of non-gray agent-days.
3. Precision at the budget as a function of assumed prevalence π: Bayes from the TPR and FPR, so
   no rerun.
4. False-alarm causes `d*`, and change days by kind (benign triggers).
5. Per-kind recall with CIs, including the kinds the layer cannot see: over-fetching 0/47 needs an
   argument the layer does not read. That is Sommer & Paxson's "what can it not detect, and why
   not?".
6. Red-team success and cost.
7. Sensitivity box and ablation tables.
8. Run counts, seeds, runtime, and the shipped-engine port check.

**Artifacts and appendices.**
- The frozen code, generator, seed derivation, scenario specifications, logged score vectors and
  analysis scripts go on Zenodo. The Ethical Considerations appendix covers the human study, GH
  Archive profiling and red-team scope; the Open Science appendix lists every artifact (USENIX
  Security '26).
- Fill in a Kapoor & Narayanan model info sheet for the simulator.
- Describe verification (the port check) and validation (levels 3–5) separately, as the Simulation
  standard asks.

## 4. Order of work and cost

1. **Log once.** Add per-call raw statistics and score vectors to the simulation engine's output.
   Without this, §3.4–§3.6 each need many reruns.
2. **Freeze and preregister** (§3.1). Derive the calibration and test seeds.
3. **Calibration pool.** Measure the between-world SD, match combiner and baseline thresholds, run
   the Morris screen. Get the per-run cost from a timing run of
   `normal_org_sim.py --only "v4" --seed <calib>` first; the README's "about 10 minutes on 8 cores"
   is for a default run, not a per-engine cost.
4. **In parallel.** Recruit scenario authors (§3.2); build the GH Archive mapping (§3.3); set up the
   shadow gateway, which needs 120 or more days.
5. **Test pool, once.** Then independent scenarios, the real background, the red team.
6. **Write up** with the ladder table first.

## 5. UNVERIFIED and open points

- Fisher (1934) and Tippett (1931): cited as attributed by Heard & Rubin-Delanchy (2018); the
  originals were not opened. The same holds for Vargha–Delaney Â12 (through Arcuri & Briand),
  Wilcoxon and Friedman (through Demšar), and Sobol' indices (through Saltelli et al.).
- The origin of the noisy-OR combination is not cited; only its formula is used.
- Tuor et al.: venue UNVERIFIED (the author PDF is named `aics17`; arXiv lists no venue). Cite the
  arXiv record.
- The LANL dataset's companion paper (Kent, 2015) and its DOI were not opened; cite the dataset page.
- Page numbers not seen and therefore omitted: Holm 1979, McClish 1989, Nosek et al. 2018, Saltelli
  et al. 2019 (volume), Kapoor & Narayanan 2023 (volume). The DOIs were opened.
- NoDoze's abstract (NDSS page) gives an 86% false-alarm reduction, the body text 84%. Neither is
  used here.
- Aggarwal & Sathe 2015 and Zimek et al. 2014 (the max combiner's citations in
  `DIMENSION_FORMULAS.md`) were not re-verified for this note.
- Open:
  - whether AI-agent accounts in GH Archive can be identified reliably (not checked);
  - the exact preregistered thresholds for E1 and E2 (to be set by the authors before freezing);
  - whether to port the generator to Slack or Calendar first (F5).

## Sources

All accessed 2026-10-25.

- D. Arp et al., "Dos and Don'ts of Machine Learning in Computer Security," USENIX Security 2022,
  pp. 3971–3988. Page: https://www.usenix.org/conference/usenixsecurity22/presentation/arp ; PDF read:
  https://www.usenix.org/system/files/sec22-arp.pdf ; arXiv 2010.09470.
- R. Sommer, V. Paxson, "Outside the Closed World: On Using Machine Learning for Network Intrusion
  Detection," IEEE S&P 2010, pp. 305–316, doi:10.1109/SP.2010.25. PDF read:
  https://oaklandsok.github.io/papers/sommer2010.pdf
- S. Axelsson, "The Base-Rate Fallacy and the Difficulty of Intrusion Detection," ACM TISSEC
  3(3):186–205, 2000, doi:10.1145/357830.357849 (earlier version: CCS 1999, pp. 1–7).
- G. Ho, A. Sharma, M. Javed, V. Paxson, D. Wagner, "Detecting Credential Spearphishing in Enterprise
  Settings," USENIX Security 2017, pp. 469–485. PDF read:
  https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-ho.pdf
- A. Tuor, S. Kaplan, B. Hutchinson, N. Nichols, S. Robinson, "Deep Learning for Unsupervised Insider
  Threat Detection in Structured Cybersecurity Data Streams," arXiv:1710.00811, 2017.
  https://arxiv.org/abs/1710.00811
- B. A. Alahmadi, L. Axon, I. Martinovic, "99% False Positives: A Qualitative Study of SOC Analysts'
  Perspectives on Security Alarms," USENIX Security 2022, pp. 2783–2800.
  https://www.usenix.org/conference/usenixsecurity22/presentation/alahmadi
- W. U. Hassan et al., "NoDoze: Combatting Threat Alert Fatigue with Automated Provenance Triage,"
  NDSS 2019, doi:10.14722/ndss.2019.23349.
- F. Pendlebury, F. Pierazzi, R. Jordaney, J. Kinder, L. Cavallaro, "TESSERACT: Eliminating
  Experimental Bias in Malware Classification across Space and Time," USENIX Security 2019,
  pp. 729–746. https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury
- D. Wagner, P. Soto, "Mimicry Attacks on Host-Based Intrusion Detection Systems," CCS 2002,
  pp. 255–264, doi:10.1145/586110.586145.
- N. Carlini et al., "On Evaluating Adversarial Robustness," arXiv:1902.06705, 2019.
- A. Arcuri, L. Briand, "A Practical Guide for Using Statistical Tests to Assess Randomized
  Algorithms in Software Engineering," ICSE 2011, pp. 1–10, doi:10.1145/1985793.1985795.
- J. Demšar, "Statistical Comparisons of Classifiers over Multiple Data Sets," JMLR 7:1–30, 2006.
  http://www.jmlr.org/papers/v7/demsar06a.html
- P. Ralph et al., "Empirical Standards for Software Engineering Research," arXiv:2010.03525; the
  Simulation (Quantitative) standard:
  https://github.com/acmsigsoft/EmpiricalStandards/blob/master/docs/standards/QuantitativeSimulation.md
- N. A. Heard, P. Rubin-Delanchy, "Choosing between methods of combining p-values," Biometrika
  105(1):239–246, 2018, doi:10.1093/biomet/asx076.
- S. Bates, E. Candès, L. Lei, Y. Romano, M. Sesia, "Testing for outliers with conformal p-values,"
  Ann. Statist. 51(1):149–178, 2023, doi:10.1214/22-AOS2244.
- T. Saito, M. Rehmsmeier, "The Precision-Recall Plot Is More Informative than the ROC Plot When
  Evaluating Binary Classifiers on Imbalanced Datasets," PLoS ONE 10(3):e0118432, 2015,
  doi:10.1371/journal.pone.0118432.
- D. K. McClish, "Analyzing a Portion of the ROC Curve," Medical Decision Making, 1989,
  doi:10.1177/0272989X8900900307.
- A. Saltelli et al., "Why so many published sensitivity analyses are false," Environmental Modelling
  & Software, 2019, doi:10.1016/j.envsoft.2019.01.012.
- M. D. Morris, "Factorial Sampling Plans for Preliminary Computational Experiments," Technometrics
  33(2), 1991, doi:10.1080/00401706.1991.10484804.
- B. A. Nosek, C. R. Ebersole, A. C. DeHaven, D. T. Mellor, "The preregistration revolution," PNAS,
  2018, doi:10.1073/pnas.1708274114.
- S. Kapoor, A. Narayanan, "Leakage and the reproducibility crisis in machine-learning-based
  science," Patterns, 2023, doi:10.1016/j.patter.2023.100804.
- L. D. Brown, T. T. Cai, A. DasGupta, "Interval Estimation for a Binomial Proportion," Statist. Sci.
  16(2):101–133, 2001, doi:10.1214/ss/1009213286.
- C. A. Field, A. H. Welsh, "Bootstrapping clustered data," JRSS-B 69:369–390, 2007,
  doi:10.1111/j.1467-9868.2007.00593.x.
- S. Holm, "A Simple Sequentially Rejective Multiple Test Procedure," Scand. J. Statist., 1979,
  doi:10.2307/4615733.
- J. Glasser, B. Lindauer, "Bridging the Gap: A Pragmatic Approach to Generating Insider Threat
  Data," IEEE Security and Privacy Workshops 2013. PDF read:
  https://www.ieee-security.org/TC/SPW2013/papers/data/5017a098.pdf ; dataset:
  doi:10.1184/R1/12841247.
- G. Engelen, V. Rimmer, W. Joosen, "Troubleshooting an Intrusion Detection Dataset: the CICIDS2017
  Case Study," IEEE SPW 2021, doi:10.1109/SPW53761.2021.00009.
- LANL, "Comprehensive, Multi-Source Cyber-Security Events": https://csr.lanl.gov/data/cyber1/
- GH Archive: https://www.gharchive.org/ ; GitHub event types:
  https://docs.github.com/en/rest/using-the-rest-api/github-event-types
- USENIX Security '26 Call for Papers (Ethical Considerations and Open Science appendices):
  https://www.usenix.org/conference/usenixsecurity26/call-for-papers ; Call for Artifacts:
  https://www.usenix.org/conference/usenixsecurity26/call-for-artifacts
- Repo: `DIMENSION_FORMULAS.md` (v4), `DIMENSION_FORMULAS_v3.md` (Simulation v3, "Honest limits"),
  `normal_org_world.py`, `normal_org_sim.py`, `results/normal_org_*.{md,json}`, `human_study/README.md`,
  `src/mcp_security/behaviour/engine.py`, `policy.py`, `scripts/dynamic_design/evaluate_dynamic.py`,
  `paper_v5/main-restructured.tex`, `paper_v5/DYNAMIC-LAYER-V4-NOTES.md`.
