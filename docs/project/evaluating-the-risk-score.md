# Evaluating the Risk Score

The framework outputs a number and never blocks anything. So the evaluation question is
not "did we stop the bad call" — it is **"is the number right?"** This document is about
what that question can and cannot mean, and how comparable systems answer it.

The formula is not in question here. `cell × likelihood × escalation`, floored at the
band, stays as specified in [Dynamic Layer — The Calculation](dynamic-layer-formula.md).
What changes is how it is graded.

## First: what misuse is, and is not

Misuse is **not** a malformed call. `ticker="AAPL; cat /etc/passwd"` is an attack: it is
caught by input validation, it is obviously wrong to any reader, and detecting it proves
nothing about a risk score. Every call in a misuse corpus should pass schema validation
and look, in isolation, entirely ordinary.

Misuse is a **legitimate call that is riskier than the calls it should be compared to**:

| tool | ordinary use | misuse |
|---|---|---|
| `list-events` | reads the team calendar | reads the CEO's calendar |
| `get_file_contents` | reads one file in the repo it maintains | reads a file in a repo it has never touched |
| `get_historical_stock_prices` | one ticker, one month | five hundred tickers, ten years |

Nothing there is malformed, and nothing there is blocked. The only thing that separates
the right column from the left is **comparison with peers**. That is the whole problem
statement, and it dictates the evaluation.

## The 125 question

> We assigned this call 125. Is that true?

Strictly: **the question has no answer, because 125 is not a quantity.** The inputs are
ordinal judgements — asset sensitivity 1-5, blast radius 1-5, tool impact 1-5 — where the
labels are ordered but the *intervals between them are undefined*. Sensitivity 4 is more
than 3; it is not "one unit" more, and there is no basis for saying 4 is to 3 as 3 is to
2. Multiplying three such judgements produces a number whose ordering may be meaningful
but whose magnitude is not.

This is not a subtlety we invented. It is the central published criticism of CVSS, the
system this framework's shape is modelled on. Spring et al., *Time to Change the CVSS?*
(IEEE Security & Privacy 19(2), 2021), state that the scoring algorithm is justified
neither formally nor empirically, and that the equation combines ordinal measures in a
numerical way — and that using CVSS directly as a risk score is a mistake by its own
specification.

Three concrete consequences for this project:

1. **Never report mean absolute error or RMSE against a "true" score.** There is no true
   score to be wrong about. Report rank correlation instead.
2. **Never say a 125 call is "twice as risky" as a 60 call.** It ranks above it. That is
   the entire claim the arithmetic supports.
3. **The band is the honest output, and the number is an ordering key inside it.** This is
   already the design's instinct — the floor protects the band, not the number — and it
   should be stated as a measurement-theory position rather than an implementation detail.

The alternative some of the literature took is worth knowing: SSVC (Stakeholder-Specific
Vulnerability Categorization), from the same authors, replaces the number with a decision
tree whose outputs are action tiers — defer, scheduled, out-of-cycle, immediate — precisely
to avoid doing arithmetic on ordinals. Since this framework's output is also not
allow/deny, an action ladder ("log / sample for review / review now") may be a more
defensible surface than a 0-125 scale, with the score used only to order within a tier.

## What can actually be validated

Six properties, in rough order of how cheaply this project can establish them. Several are
already implemented for the static score and simply have no runtime counterpart yet.

| property | the question | status here |
|---|---|---|
| **reproducibility** | same input, same score? | `mcp_security.review verify` — done for static |
| **stability** | does ±1 on one ordinal input flip the band? | `scripts/formula_sensitivity.py` — done, and the answer is bad (~85% of cells flip) |
| **criterion validity** | does the ordering agree with independent frameworks? | `scripts/evaluate_vs_human.py` — panel of DREAD / CVSS v3 / NIST SP 800-30 / OWASP / MAESTRO; Spearman .74-.91 vs NIST, .72-.86 vs OWASP |
| **inter-rater reliability** | do independent raters even agree with *each other*? | partially — the panel exists, the agreement-between-oracles number should be reported alongside |
| **within-class discrimination** | inside one tool, does misuse out-rank ordinary use? | **missing** — this is the misuse question |
| **operating-point utility** | at a threshold, what does a reviewer get? | **missing** — coverage/efficiency table |

The fourth row deserves emphasis. Wunder et al., *Shedding Light on CVSS Scoring
Inconsistencies* (arXiv 2308.15259), found that independent experts scoring the *same*
vulnerability with the *same* rubric disagree substantially. That result is a floor on
what any agreement-with-experts evaluation can claim: if the oracles disagree with each
other by a given margin, agreeing with them more closely than that margin is not evidence
of correctness. **Always report oracle-vs-oracle agreement next to scorer-vs-oracle
agreement.** Without it, a Spearman of 0.8 is uninterpretable.

## The design to copy: case-control

The strongest evaluation available without outcome labels is the one Allodi and Massacci
used in *Comparing Vulnerability Severity and Exploits Using Case-Control Studies* (ACM
TISSEC, 2014) — a method borrowed from epidemiology. Cases are known-bad instances,
controls are matched instances that are not, and the question is whether the score
separates them **after matching**.

Matching is the part that matters here, and it is exactly the comparison-class idea:
controls must be drawn from the same tool, and ideally the same tool and asset, as the
cases. Otherwise the study measures the static matrix's opinion of which tools are
dangerous, which was never in doubt.

Their headline finding is also the cautionary tale this project should keep in view:
relying on high CVSS scores was found equivalent to picking vulnerabilities at random,
while a much simpler signal — whether an exploit existed — did far better. A carefully
constructed severity score can be internally coherent, reproducible, expert-endorsed, and
still fail to discriminate real outcomes. That is a failure mode the current evaluation
design cannot detect, because nothing in it compares matched cases and controls.

## What a results table should look like

Replace the current AUC/AP-led tables with two, reported together:

**Ordering quality, stratified by comparison class:**

| stratum | n cases | n controls | concordance | static-only control |
|---|---:|---:|---:|---:|
| per tool, averaged over tools | … | … | … | … |

Report the number of strata and the spread, not just the mean — most strata will be small,
and a mean over classes of three calls is fragile.

**Operating point, in reviewer terms:**

| threshold | calls flagged per 1,000 | coverage | efficiency | vs. base rate |
|---|---:|---:|---:|---:|

Coverage and efficiency are recall and precision under the names EPSS uses; the last
column is the multiple over random, which at a 1% misuse rate is the only figure that
conveys whether the score is doing anything.

The static-only control column is not optional. The question is never "is the score good"
but **"does the runtime term beat the matrix alone, inside a class where the matrix is
constant."**

## Keying: the application, not the agent

Any peer comparison needs a stable identity for "who is calling." The captures settle what
is available (see `logs/proxy/sessions/finance_yahoo/captured.jsonl`):

| identifier | stability | usable as a peer key? |
|---|---|---|
| `mcp-session-id` | one connection; gone on reconnect | no — groups a session, nothing longer |
| `clientInfo.name` | free text, defaults to the SDK's own name | no |
| `User-Agent` | the HTTP client library | no |
| **OAuth `client_id`** | the registered application, stable across sessions and restarts | **yes** |

The distinction matters more than it looks. An *agent* is ephemeral — instances are
created and destroyed per task, so a per-agent history is both thin and short-lived. The
*application* the agent belongs to persists, accumulates history, and is what an
organization actually grants permission to. Peer comparison should therefore be
application-versus-application, with sessions as the unit of aggregation inside an
application.

## References

- Spring, Hatleback, Householder, Manion, Shick, *Time to Change the CVSS?*, [IEEE Security & Privacy 19(2), 2021](https://ieeexplore.ieee.org/document/9382369) · [Towards Improving CVSS (SEI, 2018)](https://www.sei.cmu.edu/documents/574/2018_019_001_538372.pdf)
- Allodi, Massacci, *Comparing Vulnerability Severity and Exploits Using Case-Control Studies*, [ACM TISSEC, 2014](http://disi.unitn.it/~allodi/allodi-tissec-14.pdf)
- Wunder, Kurtz, Eichenmüller, Gassmann, Benenson, *Shedding Light on CVSS Scoring Inconsistencies*, [arXiv:2308.15259](https://arxiv.org/abs/2308.15259)
- Jacobs et al., *Exploit Prediction Scoring System (EPSS)*, [arXiv:1908.04856](https://arxiv.org/pdf/1908.04856) — coverage/efficiency reporting
- Axelsson, *The Base-Rate Fallacy and the Difficulty of Intrusion Detection*, [ACM TISSEC, 2000](https://dl.acm.org/doi/10.1145/357830.357849)
- [MARIA: Marginal Risk Assessment without Ground Truth in AI Systems](https://arxiv.org/abs/2510.27163) — compares a candidate system against the incumbent rather than against labels
- Project-internal: [Dynamic Layer — The Calculation](dynamic-layer-formula.md) · [External Benchmarks and Positioning](external-benchmarks-and-positioning.md) · [Results](../../reports/experiments/dynamic_layer/RESULTS.md)
