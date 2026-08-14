# What the Dynamic Layer Can Claim, and How to Defend It

Written for a top-tier submission. [Evaluating the Dynamic Layer](evaluating-the-dynamic-layer.md)
gives the protocol; this gives the argument the protocol is meant to support, which claims
survive it, and what a reviewer will attack first.

## The claim to abandon

> *"Our dynamic layer detects misuse."*

This cannot be defended, for two independent reasons.

**No ground truth exists, and manufacturing it is circular.** Any misuse corpus authored
alongside the scorer encodes the same intuitions the scorer encodes, so the evaluation
recovers the generator rather than testing the system. Arp et al. list this under sampling
bias and inappropriate baselines; it is the single most common reason security-ML papers
are rejected.

**It is also false as currently stated.** The sensitivity sweep found **7 of 7** widening
classes invisible across three servers — page size to a million, calendar windows to a
century, fan-out to 5,000 targets, all scoring exactly `+0.0000`. A reviewer who runs the
artifact finds this in an hour. Better to publish it.

Trying to prove a claim this broad is what would sink the paper. The way through is not a
cleverer evaluation of the same claim — it is a set of narrower claims that the evidence
already supports.

## Five claims that survive

Each is stated with the experiment that establishes it and the attack it must withstand.

### C1 · A design-time score cannot separate what a deployment's own history separates

The static cell is constant for a given (tool, asset) pair by construction. Real traffic to
that same pair varies substantially in observed behaviour. Therefore any purely design-time
score assigns one number to calls that differ operationally.

*Establishes:* a gap exists. *Attack:* "so what?" — C1 is worthless alone and only matters
because C2 shows the gap carries signal. Present them together.

### C2 · Per-deployment rarity is learnable and separates administrative from routine work

`P(write scores above read)` = **0.90–0.98** across three independent real deployments,
with a gap of +0.16 to +0.21 against a stated noise floor of 0.007–0.018.

*Attack, and it is the dangerous one:* **a three-line frequency counter reproduces τ-b =
0.79 of the ranking.** A reviewer will say the layer is an expensive `Counter()`. The only
defence is to run that baseline yourself, report it prominently, and argue the residual
0.21 — or concede the point and reposition. Do not let a reviewer find it first.

*Second attack:* rarity is not malice (Sommer and Paxson's semantic gap). In these orgs rare
and administrative coincide; `L` would score a rare read and a rare deletion identically.
State this as a scope limit in the abstract, not the discussion.

### C3 · The score states its own precision — this is the safest contribution

Almost nothing in the risk-scoring literature reports the resolution of its own output.
Spring et al. make exactly this complaint about CVSS: a score assembled from ordinal inputs
asserts more precision than it has. This work can report:

- **resolution** — p95 spread over byte-identical repeated calls, 0.007–0.018 warm
- **the warm-up curve** — 0.086 at 250 calls falling to 0.004 at 60,000
- **a usability threshold** — `L` is not trustworthy below ~`20 x tools_exposed` calls
- **a cold-start guarantee** — with no history the score is exactly 1.0, leaving the static
  cell untouched, rather than guessing

*Attack:* none serious. This is methodology, it is checkable, and it is reusable by others.

### C4 · The capability boundary is measured rather than asserted

Which deviation classes are detectable, which are not, and what evasion costs: 7/7 widening
classes invisible; normalising a rare tool costs ~882 cover calls, after which the tool
scores **below** 1.0 and the attacker is better placed than an ordinary caller.

*Attack:* "so your system does not work." *Reframe:* a defence whose limits are measured is
worth more than one whose limits are unmeasured, and the evasion cost is a number nobody
else in this space publishes.

### C5 · Zero per-deployment configuration

The comparable systems — AgentSpec (ICSE 2026), Conseca, PCAS — are **deterministic policy
enforcers requiring authored policy per deployment**. This layer requires none: it learns
the baseline from traffic. That is the real differentiator, and it is measurable as
configuration cost (rules authored, lines of policy, expert hours) alongside detection.

*Attack:* "a policy would catch the widening case you miss." True, and it should be said —
the honest positioning is complementary, not competitive.

## The related work that must be positioned against

A 2025–2026 cluster attacks a neighbouring problem, and a reviewer will know it. Getting
the distinction right matters more than any single experiment:

| work | approach | threat direction |
|---|---|---|
| **Progent** (2025) | privilege control over tool calls, policy-based | protects the **agent** from injection |
| **MiniScope** (2025) | least-privilege authorization for tool-calling agents | protects the **agent** |
| **AgentSpec** (ICSE 2026) | DSL of triggers/conditions/enforcement, deterministic | protects the **agent** |
| **Conseca**, **PCAS** | just-in-time contextual policy, Datalog reference monitor | protects the **agent** |
| *Evaluating Privilege Usage of Agents with Real-World Tools* (2026) | measurement of privilege use | measurement |
| *When Lower Privileges Suffice* (2026) | over-privileged tool **selection** | measurement |

Two things follow.

**The threat direction differs and must be stated in the first paragraph.** Nearly all of
this cluster treats the agent as the victim of a malicious server or injected content. This
project inverts that: the **server is the protected asset and the agent is the threat**. A
reviewer skimming will assume the common direction and judge the paper against the wrong
baselines unless the abstract forecloses it.

**The two 2026 measurement papers are the closest neighbours and the strongest threat.**
Over-privilege in tool selection is adjacent to `blast_radius` and `tool_breadth`. The
differentiator to argue is that they measure *privilege as granted*, statically, while this
measures *behaviour as exercised*, per deployment, with no policy authored. If that
distinction cannot be made crisply, the contribution shrinks to an incremental one.

## Adopt the field's two-axis norm

Agent-security work evaluates on **security and utility simultaneously**: Attack Success
Rate against task completion, because a defence that blocks everything scores perfectly on
one axis. Agent Security Bench established this framing.

This project already has the utility axis and has not been using it as one: the benign
corpora measure the **over-block rate**. A gate at a given threshold, run over 300,000
benign calls, yields a false-block rate directly. Report the pair — detection at a budget,
against benign work broken — never detection alone.

## The single highest-value thing to add

**A misuse set authored by people who have never seen the scorer.**

This breaks the circularity that no amount of statistics can fix, and it is the difference
between "we made up some bad calls" and a case-control study with externally defined cases.
The machinery already exists: the [human annotation experiment](human-annotation-experiment.md)
built a rating instrument with calibration, quality controls and shuffled presentation.
Reuse it with a different task:

> Here is a tool, its documentation, and five real calls an organisation made to it.
> Write three calls that a reviewer would consider *legitimate-looking but riskier than
> these*, and say in one line why.

Raters never see `B`, `L`, the rubric, or any score. Their calls become the **cases**; the
real calls they were shown become the matched **controls** — same tool, same asset, which is
what makes the comparison about the runtime rather than about the static matrix. Two raters
over twenty tools at three variants each is 120 cases, which is enough for a per-deviation
breakdown with intervals.

This also yields something the paper needs independently: a **deviation taxonomy grounded in
human judgement** rather than in what the author thought to test. The current sweep tests
seven deviations I chose, which is exactly the weakness a reviewer probes.

## Precedent: the paper these claims make is a real paper

The results are largely negative, and that is not a weakness at this venue tier. Three of
the most cited papers in security ML are negative or methodological:

- **Sommer and Paxson**, *Outside the Closed World* (IEEE S&P 2010) — "anomaly detection is
  harder than this field admits, here is why"
- **Pendlebury et al.**, *TESSERACT* (USENIX Security 2019) — "your evaluations are biased,
  here is the correct protocol"
- **Arp et al.**, *Dos and Don'ts of ML in Computer Security* (USENIX Security 2022) — "ten
  pitfalls, most papers commit several"

The honest shape of this work is closest to those: a first runtime risk layer for MCP, a
methodology for measuring what such a layer can see, real traffic corpora from live servers,
and measured limits. That is a contribution. *"Our score is correct"* is not, and no
evaluation can make it one.

## What a reviewer attacks, in order

| # | attack | status |
|---|---|---|
| 1 | "Your misuse set is your own invention" | **open** — fixed only by externally authored cases |
| 2 | "No baseline" | **have it**: rarity counter τ-b 0.79, write-flag 0.41 — must be reported |
| 3 | "Rarity is not malice" | **concede in the abstract**, scope it |
| 4 | "Three servers, all yours" | **open** — needs a held-out server never inspected |
| 5 | "Trivially evadable" | **have the number**: ~882 calls — publish it |
| 6 | "AUC at what base rate?" | **open** — report coverage/efficiency at 10⁻³, 10⁻⁴, 10⁻⁵ |
| 7 | "Utility cost?" | **have the data**: over-block rate over 300k benign calls, unreported |

Four of seven are already answered by work done. The two that matter most — externally
authored cases, and a genuinely held-out server — are the ones to spend the remaining time
on.

## References

- Sommer, Paxson, *Outside the Closed World*, [IEEE S&P 2010](https://www.icir.org/robin/papers/oakland10-ml.pdf)
- Arp et al., *Dos and Don'ts of Machine Learning in Computer Security*, [USENIX Sec 2022](https://arxiv.org/abs/2010.09470)
- Pendlebury et al., *TESSERACT*, [USENIX Sec 2019](https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury)
- Allodi, Massacci, *Comparing Vulnerability Severity and Exploits Using Case-Control Studies*, [ACM TISSEC 2014](https://dl.acm.org/doi/10.1145/2630069)
- Spring et al., *Time to Change the CVSS?*, [IEEE S&P Magazine 2021](https://ieeexplore.ieee.org/document/9382369)
- Wang, Poskitt, Sun, *AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents*, [ICSE 2026](https://cposkitt.github.io/files/publications/agentspec_llm_enforcement_icse26.pdf)
- Shi, He, Wang, Li, Wu, Guo, Song, *Progent: Securing AI Agents with Privilege Control*, [arXiv:2504.11703](https://arxiv.org/abs/2504.11703)
- Zhu, Tseng, Vernik, Huang, Patil, Fang, Popa, *MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents*, [arXiv:2512.11147](https://arxiv.org/abs/2512.11147)
- Zhang et al., *Evaluating Privilege Usage of Agents with Real-World Tools*, [arXiv:2603.28166](https://arxiv.org/abs/2603.28166)
- Yang et al., *When Lower Privileges Suffice: Investigating Over-Privileged Tool Selection in LLM Agents*, [arXiv:2606.20023](https://arxiv.org/abs/2606.20023)
- Project-internal: [Evaluating the Dynamic Layer](evaluating-the-dynamic-layer.md) · [Human Annotation Experiment](human-annotation-experiment.md) · [v3 results](../../reports/experiments/dynamic_layer/v3/README.md)
