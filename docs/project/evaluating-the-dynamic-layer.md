# Evaluating the Dynamic Layer

[Evaluating the Risk Score](evaluating-the-risk-score.md) argues what a *risk score* can be
validated against at all. This is narrower and executable: what to measure for the
**runtime** layer specifically, in what order, and what each measurement can and cannot
support. The static layer's problem is that no ground truth exists. The runtime layer's
problem is different and more tractable — deviation from a deployment's own history is
observable, so the honest questions are how precisely it is measured, what it is blind to,
and whether it adds anything over the static score alone.

Every number quoted below is from
[`reports/experiments/dynamic_layer/v3/`](../../reports/experiments/dynamic_layer/v3/).

## The one thing that makes this hard

`D = B x L` measures **rarity and narrowness**, not malice. That gap is the subject of
Sommer and Paxson's *Outside the Closed World* (IEEE S&P 2010): machine learning finds
*similarity*, not *novelty*, and the leap from "anomalous" to "malicious" is a semantic gap
that must be measured rather than assumed. Every experiment below exists to measure some
part of that gap instead of asserting it away.

The measured version of the gap in this project: `L` separated writes from reads at
P = 0.90–0.98 across three servers, but only because in these orgs rare and administrative
happen to coincide. `L` never sees arguments and never sees what a tool does, so it would
score a rare read and a rare deletion identically.

## E0 · Invariants — cheap, and they catch real defects

Properties that must hold regardless of data, asserted as unit tests. These are not
"evaluation" in the results-table sense, but every defect found in the dynamic layer so far
was found here or by E1, not by a metric.

| invariant | why | status |
|---|---|---|
| empty deployment scores exactly 1.0 | no evidence must leave the static cell untouched | passing |
| `L` is held back until a distribution exists | it claimed "0.79x the median" on nine calls | fixed, passing |
| an argument that cannot be narrow is excluded | one such argument pinned `B` to 1.0 for a whole tool | fixed, passing |
| identical input, identical output within one epoch | otherwise nothing else is measurable | **fails by design — see E1** |
| widening an argument never *lowers* the score | monotonicity | **untested** |

## E1 · Resolution — measure the noise floor before anything else

Byte-identical calls scored at different points in the stream should score identically and
do not, because the baseline adapts. The **p95 spread over repeated identical calls** is
the layer's resolution limit: no ranking, gap or improvement smaller than it means
anything, and every other result must be reported against it.

Use a p95, never a maximum — a maximum over N groups grows with N and made a 100,000-call
corpus look 17x noisier than a 1,000-call one purely for having more groups.

Measured: **0.007–0.018 at 50,000 warm calls, 0.033–0.145 at 500.** The floor is a function
of warm-up length (0.086 at 250 warm calls falling to 0.004 at 60,000), not of the formula.
The practical rule that follows is that `L` is not trustworthy below roughly
`20 x tools_exposed` calls.

This is the measurement-theory point Spring et al. make about CVSS in *Time to Change the
CVSS?* — a score built from ordinal inputs states more precision than it has. Publishing
the floor alongside the score is the correction.

## E2 · Discrimination — matched case-control, never a raw comparison

The design is Allodi and Massacci's (*Comparing Vulnerability Severity and Exploits Using
Case-Control Studies*, ACM TISSEC 2014), and **matching is the whole point**. A case and its
control must share tool and asset, so that only the runtime's contribution varies. Comparing
across tools measures the static matrix's opinion of which tools are dangerous, which was
never in question.

```
for each benign call c in a held-out window:
    build c' = the same call, one deviation applied
    record whether D(c') > D(c)
report P(D(c') > D(c)) with a confidence interval, per deviation type
```

The deviation taxonomy must be defined **independently of the scorer** — otherwise the
evaluation rediscovers its own generator. A defensible starting set, each naming a distinct
way a legitimate-looking call can be riskier than its peers:

1. **argument widening** — `per_page` 30 → 1000
2. **window widening** — a 7-day range → 365 days
3. **fan-out** — one calendar → every calendar the token can reach
4. **rare-tool use** — a tool this deployment has never called
5. **volume** — the same ordinary call, 1000x in a minute
6. **enumeration** — ordinary calls whose *arguments* sweep the id space

Report per type. A single pooled number hides that the layer is excellent at (4) and blind
to (1).

## E3 · Sensitivity — the minimum detectable deviation

For each deviation type, sweep its magnitude and find where `ΔD` first exceeds the E1 noise
floor. This is the anomaly-injection method used where labels do not exist: inject a
controlled deviation, sweep its size, and report the smallest one still detected.

**This is the experiment that matters most here, and it already has a decisive result.**
One real benign call, warmed on 50,000 calls, widening one argument and holding everything
else fixed:

| `per_page` | `D` | `B` | Δ vs ordinary |
|---:|---:|---:|---:|
| 1 | 0.7716 | 0.8500 | |
| 10 | 0.8138 | 0.8966 | |
| **30** (Q1) | **0.9077** | 1.0000 | — |
| 100 | 0.9077 | 1.0000 | +0.0000 |
| 1,000 | 0.9077 | 1.0000 | −0.0000 |
| 1,000,000 | 0.9076 | 1.0000 | **−0.0001** |

A call requesting **a million records scores the same as one requesting thirty** — a
difference 90x *below* the noise floor. The minimum detectable widening is not large, it is
**infinite**: `B` is gated at Q1 and discount-only, so nothing above the ordinary range is
visible, and `L` cannot help because the tool is common.

This is not a bug; it follows from the deliberate decision that `blast_static` already
prices the worst a single call can do, so the runtime may only discount. But it means the
layer's answer to *"an agent just asked for a million records"* is *"that is ordinary"*, and
that has to be stated as a scope limit rather than discovered by a reader.

The experiment is worth running precisely because it converts a design rationale into a
measured blind spot.

## E4 · Operating point — coverage, efficiency and effort, at a real base rate

Never report AUC alone. A gate has a budget, so report the EPSS triple (Jacobs et al.,
*Exploit Prediction Scoring System*, DTRAP 2021):

- **effort** — fraction of calls flagged
- **coverage** — fraction of misuse caught
- **efficiency** — fraction of flags that are misuse

Sweep effort from 0.01% to 5% and plot coverage and efficiency against it. Then apply
Axelsson's base-rate correction (*The Base-Rate Fallacy and the Difficulty of Intrusion
Detection*, ACM TISSEC 2000): at a misuse rate of 1 in 10⁴ calls, a 1% flag rate has an
efficiency ceiling of 1% even with perfect recall. State the assumed base rate explicitly
and report efficiency at several — 10⁻³, 10⁻⁴, 10⁻⁵ — because the conclusion changes.

Insider-threat work uses the same framing under a different name, **CR@k** (cumulative
recall at an investigation budget of k) and Precision@k, and prefers PR-AUC to ROC-AUC
under class imbalance. This project's threat model *is* insider threat — a legitimate
agent making an over-broad call — so those are the right borrowed metrics.

## E5 · Ablation — does the runtime earn its complexity?

Arp et al. (*Dos and Don'ts of Machine Learning in Computer Security*, USENIX Security 2022)
list "inappropriate baseline" among ten pitfalls. Without this experiment no claim about the
dynamic layer is supportable, because the static cell alone might do as well.

Score the same evaluation set under each of:

```
cell only                     the static baseline
cell x L                      rarity only
cell x B                      narrowness only
cell x B x L                  the full layer
```

and against two deliberately trivial baselines: **"flag every write"** and **"flag the k
rarest tools"**. If a three-line heuristic matches the layer, that is the result, and it is
worth knowing before more is built on top. Given that `L` fires on 95–98% of calls and `B`
on 6–14%, with `B`'s median exactly 1.000 on every tool of every server, the honest prior is
that `cell x L` will account for nearly all of the layer's behaviour.

## E6 · Generalisation — hold out servers and respect time

Two constraints from Pendlebury et al. (*TESSERACT*, USENIX Security 2019):

- **Temporal.** Warm on earlier calls, score on strictly later ones — never shuffle. The
  current harness already does this (warm on the first half, score the second).
- **Spatial.** The evaluation set's class ratios must match deployment. The current write
  rate of ~10–15% is a *choice made by the generator*, not a measured fact about any real
  deployment, and it should be stated as an assumption whenever a write/read result is
  quoted.

Add a **held-out server**: develop and tune on GitHub and Slack, then evaluate on Calendar
without having looked at it. The breadth rubric was already rewritten once for being
overfitted to the three development servers, so this is a live risk, not a hypothetical one.

## E7 · Robustness — the attack any adaptive baseline invites

Absent from the benign corpora and from most of the literature: `B` and `L` both learn from
traffic the adversary controls. An agent that knows the scheme can **poison its own
baseline** — issue wide calls until Q1 rises, after which the wide call it wanted all along
is "ordinary"; or spread calls evenly until no tool is rare.

Measure the cost: how many calls does it take to move Q1 for an argument by 2x, or to move a
tool from `L = 1.28` to `L = 1.0`? The answer is bounded by `MAX_HISTORY = 4000` and by the
smoothing constant, so it is computable and should be published. A defence whose evasion
cost is 200 calls should not be described as a defence.

## Results — E5, E3 and E7, run on all three servers

`scripts/dynamic_design/evaluate_dynamic.py`, on the three 100,000-call corpora, warmed on
50,000. Raw output in [`reports/experiments/dynamic_layer/v3/eval_<server>.txt`](../../reports/experiments/dynamic_layer/v3/).

### E5 · Ablation — `L` carries the ranking, `B` is not decorative, rarity alone gets most of it

Kendall **tau-b** with the tied-pair fraction beside it. The first version of this used
concordant-versus-discordant only, which is Goodman–Kruskal gamma, and reported +0.97 for
`B` — a variable that is constant on 93% of calls. Reporting ties alongside makes that
visible rather than flattering.

Measured before and after `B` was made two-sided, since that change was made in response
to E3 and its cost belongs here:

| | github | slack | calendar |
|---|---:|---:|---:|
| `D` vs **"rank by tool rarity"** — discount-only | +0.789 | +0.784 | +0.810 |
| `D` vs **"rank by tool rarity"** — two-sided | **+0.729** | **+0.694** | **+0.666** |
| `D` vs `L` alone — is `B` decorative? | +0.851 | +0.693 | +0.595 |
| `D` vs **"flag every write"** | +0.424 | +0.436 | +0.409 |
| `B` moved on — discount-only | 6.7% | 16.6% | 14.2% |
| `B` moved on — two-sided | **11.8%** | **24.2%** | **22.2%** |

Readings a results table has to state plainly:

- **`B` is not decorative**, and became substantially less so. It now fires on 12–24% of
  calls rather than 7–17%, and dropping it moves 15–40% of pairwise orderings.
- **The frequency-counter critique weakened but did not disappear.** A three-line
  `Counter()` still reproduces 0.67–0.73 of the ordering, down from 0.78–0.81. That
  remains the number to beat and must be reported.
- **"Flag every write" does not match the layer** (+0.41), so it is at least not that.

### E3 · Sensitivity — this is what made `B` two-sided

Seven deviation sweeps across three servers, each a real call with one argument widened and
everything else held fixed, scored against a copy of the model so the probe cannot teach it
the value being probed:

| server | deviation | swept | discount-only `B` | two-sided `B` |
|---|---|---|---|---|
| github | page size | 30 → 1,000,000 | never | **1,000** |
| github | page depth | 1 → 100,000 | never | **10** |
| github | batch fan-out | 1 → 5,000 files | never | **50** |
| slack | history limit | 100 → 1,000,000 | never | **500** |
| slack | channel sweep | 50 → 200,000 | never | **200** |
| calendar | time window | 7 days → 100 years | never | **+3 months** |
| calendar | calendar fan-out | 1 → 5,000 calendars | never | **5** |

Under the original discount-only `B`, every delta was exactly **+0.0000** — not small,
zero — on all seven. `B` was gated at Q1 and capped at 1.0, so nothing above the ordinary
range was visible, and `L` could not compensate because the tool was common. **0 of 7.**

That followed from the rule that `blast_static` already prices the worst a single call can
do, so the runtime may only discount. The rule conflates two different facts:
`blast_radius` is judged at design time from a schema and prices what the tool **could**
reach, while what a deployment actually asks for is knowable only at runtime. A call
exceeding observed practice is new information, not reach counted twice.

`B` now moves both ways — `B_MIN` 0.70 at the narrowest value ever seen, 1.0 through the
ordinary band, `B_MAX` 1.30 beyond the 90th percentile. **7 of 7 detected**, each at the
first step past ordinary.

Two implementation notes, both found by re-running E1 after the change and both instances
of the same failure mode:

- The escalation edge must be **one continuous rule**. A first version used Q3 when the
  interquartile range was positive and a fallback anchor when it was degenerate; real
  traffic oscillates across that boundary, `per_page=100` flipped between "ordinary" and
  "wide", and the noise floor went from 0.009 to **0.130**. A single percentile cannot flip.
- The anchor must not be an **extreme-value statistic**. Anchoring on the maximum observed
  value is unstable because scoring a call inserts its own value into the history, so one
  outlier redefines the scale.

### E7 · Poisoning — the only real signal costs ~1,000 calls to switch off

`L` is fed by traffic the adversary controls. Taking the rarest GitHub tool,
`fork_repository`, and issuing cover calls before the one that matters:

| cover calls | `L` | |
|---:|---:|---|
| 0 | 1.2614 | escalated |
| 500 | 1.0932 | escalated |
| **1,000** | **0.9739** | **discounted — better than an average call** |
| 2,000 | 0.9158 | discounted |

The cost of hiding a rare tool is roughly the median tool's volume — **882 calls here**.
Worse than merely evading: past that point the tool scores *below* 1.0, so an attacker who
warms up is better placed than an ordinary caller, because the design treats commonness as
evidence. That asymmetry was chosen deliberately (`L_MIN` 0.85 against `L_MAX` 1.30) and
this is the bill for it.

`B` can be owned outright in `MAX_HISTORY` = 4,000 calls, at which point the attacker's own
values define the quartiles. It buys nothing only because `B` cannot escalate anyway.

### The cost of the fix, stated honestly

Making `B` two-sided is not free, and E1 is where the bill arrives:

| | discount-only | two-sided |
|---|---|---|
| widening detected | 0 / 7 | **7 / 7** |
| noise floor, github | 0.009 | 0.021 |
| noise floor, slack | 0.018 | **0.084** |
| noise floor, calendar | 0.007 | 0.007 |
| write/read gap | +0.207 / +0.199 / +0.163 | unchanged |
| P(write above read) | 0.977 / 0.935 / 0.902 | 0.946 / 0.914 / 0.883 |

Every server still clears its floor, but Slack's margin narrows to 2.4x where GitHub's is
10x and Calendar's 23x. The residual is a discrete-mass effect: `max_channels=200` sits
directly on the 90th percentile, so it flips as the boundary crosses it. Any neutral band
on a discrete distribution has this property; it is bounded, not eliminated.

**P(write above read) falling is expected and arguably desirable.** Wide *reads* can now
escalate too, so writes are no longer the only thing that rises. A layer that scored high
only on writes was a write detector.

### E8 · Negative controls — replace a component with noise and see if anything changes

A component that can be replaced by noise without changing the result was not
contributing. The breadth rubric is the most expensive component in the pipeline — a GPU
scan per server, three rubric rewrites — so it is the one worth controlling. It weights
`B`, so it is controlled against `B`'s own job (detecting a widened argument), not against
the write/read separation, which `L` drives and breadth cannot affect.

Every measurable argument on each server is widened to 100x its 90th percentile:

| | args | detected | median Δ |
|---|---:|---:|---:|
| **github** scan labels | 21 | 81% | **+0.348** |
| github randomised | 21 | 81% | +0.277 |
| github constant (no rubric) | 21 | 86% | +0.348 |
| **slack** scan labels | 10 | 100% | **+0.287** |
| slack randomised | 10 | 80% | +0.287 |
| slack constant | 10 | 100% | +0.287 |
| **calendar** scan labels | 4 | 100% | **+0.266** |
| calendar randomised | 4 | **25%** | **+0.000** |
| calendar constant | 4 | 100% | +0.266 |

Two conclusions, one of which cost a design change to reach.

**The labels are not noise.** Randomising them degrades every server — Calendar collapses
from 100% detection to 25%. So the rubric carries real information about which arguments
matter.

**But it is indistinguishable from a constant.** "Every argument is equally central"
matches the scan labels exactly on all three servers. The rubric is better than being
wrong and no better than not asking. On this metric its value is unproven, and it is the
most expensive thing in the pipeline.

#### The control also found a defect

Run before the fix, the scan labels scored **+0.227 on GitHub against +0.348 for a
constant** — the rubric was *costing* a third of the signal. The cause was the relative
weighting's denominator:

```
w = BREADTH_WEIGHT[this argument] / BREADTH_WEIGHT[most central argument on the tool]
```

The most central argument is breadth 5 on **17 of 17 GitHub tools and 9 of 9 Calendar
tools**, because every tool names its asset — and that argument is always an identifier
with no readable quantity. The most central *measurable* argument is breadth 3 on most
tools. So the ratio was a constant `0.50/1.00` almost everywhere: not a discriminating
weight, a flat halving of every signal the runtime can read, divided by a reference that
can never itself contribute.

The denominator now ranges over measurable arguments only, which is what restored
+0.348. This is exactly the class of defect a negative control exists to find: the
component was not broken, its *reference frame* was, and no benign-corpus metric would
have shown it.

## Still to run

| | status |
|---|---|
| E2 matched case-control, per deviation type | needs a misuse set; widening types will read 0.500 until E3 is addressed |
| E4 coverage / efficiency at a stated base rate | needs E2 |
| E6 held-out server | discipline, not compute |
| E0 monotonicity invariant | one test |

## What not to do

- **Do not report a single AUC on a balanced set.** Spatial bias plus the base-rate fallacy
  make it meaningless for a gate.
- **Do not generate benign and misuse from the same script.** The evaluation would recover
  the generator's own decision boundary. Deviations must be defined as transformations of
  *real* calls, which is why E2 mutates a held-out benign call rather than sampling a new one.
- **Do not tune on the evaluation servers.** Rewriting the breadth rubric after seeing which
  inputs it misclassified is data snooping; it happened once and was caught.
- **Do not quote MCP attack benchmarks as if they tested this.** MCP Security Bench (2025),
  MCP-Guard (2025) and *Beyond the Protocol* (2025) target prompt injection, tool poisoning
  and rug pulls — a **malicious server attacking an agent**, the opposite direction from this
  project's threat model, where the server is the protected asset. They are useful as
  related work and as a source of adversarial traffic, never as a validation set.

## References

- Sommer, Paxson, *Outside the Closed World: On Using Machine Learning for Network Intrusion Detection*, [IEEE S&P 2010](https://www.icir.org/robin/papers/oakland10-ml.pdf)
- Arp, Quiring, Pendlebury, Warnecke, Pierazzi, Wressnegger, Cavallaro, Rieck, *Dos and Don'ts of Machine Learning in Computer Security*, [USENIX Security 2022 · arXiv:2010.09470](https://arxiv.org/abs/2010.09470)
- Pendlebury, Pierazzi, Jordaney, Kinder, Cavallaro, *TESSERACT: Eliminating Experimental Bias in Malware Classification across Space and Time*, [USENIX Security 2019](https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury) · [arXiv:1807.07838](https://arxiv.org/abs/1807.07838)
- Allodi, Massacci, *Comparing Vulnerability Severity and Exploits Using Case-Control Studies*, [ACM TISSEC 2014](https://dl.acm.org/doi/10.1145/2630069)
- Jacobs, Romanosky, Adjerid, Baker, *Exploit Prediction Scoring System (EPSS)*, [DTRAP 2021](https://dl.acm.org/doi/10.1145/3436242) · [arXiv:1908.04856](https://arxiv.org/pdf/1908.04856)
- Axelsson, *The Base-Rate Fallacy and the Difficulty of Intrusion Detection*, [ACM TISSEC 2000](https://dl.acm.org/doi/10.1145/357830.357849)
- Spring, Hatleback, Householder, Manion, Shick, *Time to Change the CVSS?*, [IEEE Security & Privacy 19(2), 2021](https://ieeexplore.ieee.org/document/9382369)
- Zhang, Li, Luo, Liu, Li, Xu, *MCP Security Bench (MSB): Benchmarking Attacks Against Model Context Protocol in LLM Agents*, [2025](https://www.semanticscholar.org/paper/bb33f9e07e661b52a6fade948f71d5a0e0bbc773) — opposite threat direction; related work only
- Xing et al., *MCP-Guard: A Multi-Stage Defense-in-Depth Framework for Securing Model Context Protocol in Agentic AI*, [2025](https://www.semanticscholar.org/paper/8951ab8938bcc4f92e29a6a9f20ae16878090367)
- Song et al., *Beyond the Protocol: Unveiling Attack Vectors in the Model Context Protocol Ecosystem*, [2025](https://www.semanticscholar.org/paper/ef65bc91d689a7419b493f91989f101a5fdab62e)
- Project-internal: [Evaluating the Risk Score](evaluating-the-risk-score.md) · [Dynamic Layer Formula v2](dynamic-layer-formula-v2.md) · [Dynamic Layer Blind Spots](dynamic-layer-blind-spots.md) · [v3 results](../../reports/experiments/dynamic_layer/v3/README.md)
