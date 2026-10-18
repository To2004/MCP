# External Benchmarks and Where This Work Sits

Every number this project has produced so far comes from corpora we generated ourselves.
That is the single largest weakness in the evidence base, and it is fixable: public
benchmarks in our threat direction exist. This document explains what they are, what the
closest published systems do differently, and exactly what would have to be built to use
each one.

## Direction discipline — read this first

The framework defends **MCP servers from the agents that call them**. An agent issues a
tool call; the server decides how worried to be. Most of the 2025-26 agent-security
literature runs the *opposite* way — a poisoned web page or a malicious tool attacks the
*agent*, and the defense protects the agent.

| | agent is the **threat** (ours) | agent is the **victim** (not ours) |
|---|---|---|
| what goes wrong | the agent asks for something it shouldn't | the agent is tricked into asking |
| who is protected | the server and its data | the agent and its user |
| examples | R-Judge, AgentHarm, Agent-SafetyBench, FORTIS | MSB, AgentDojo, Progent, CaMeL, dual-graph provenance |

The second column is out of scope by
[the project's own rule](../../CLAUDE.md) and should not be cited as a baseline we
compete with. It is fair to cite as related work we deliberately do not address.

An important consequence: **a defense in our direction can only use what arrives at the
server.** It never sees the agent's prompt, reasoning, or retrieved content. Any signal
requiring agent-side visibility — taint tracking, provenance graphs, intent parsing — is
unavailable to us by construction, not by choice.

## Three ways to build the decision, and which one we are

**The rulebook.** Enumerate what each caller may do; refuse everything else. Provable and
cheap at runtime, but somebody must author rules per server, and a rulebook cannot express
"allowed, but strange."

**The judge that reads the transcript.** Hand an LLM the record of what the agent did and
ask whether anything in it was unsafe. Needs no per-server authoring, but costs a model
call per judgement and inherits the model's blind spots.

**The risk score.** Refuse nothing. Attach a number to every call so a human reviews the
worrying ones first. No LLM at runtime, ranks everything, and degrades gracefully — but it
never *decides*, so it can only be judged on ordering quality.

We are the third. That matters for what we may claim: **we should not claim better
detection than a rulebook, and we should not benchmark against attack-blocking success
rates.** The claim available to us is prioritisation quality under a realistic (rare)
misuse rate.

## R-Judge — the closest published work to ours

[R-Judge](https://arxiv.org/abs/2401.10019) (Findings of EMNLP 2024,
[code](https://github.com/Lordog/R-Judge)) asks an LLM to read an agent's interaction
record and judge whether it was safe. Its **unit of analysis is identical to ours** — a
record of agent tool calls, scored after the fact, in the agent-as-threat direction.

**Composition.** 569 multi-turn agent interaction records, 27 risk scenarios, 5
application categories, 10 risk types. Every record is hand-labelled, and each carries a
human-written description of the risk, not just a binary flag.

**Record shape.** Each record has:

| field | contents |
|---|---|
| `id` | unique identifier |
| `contents` | the multi-turn transcript — user instruction, agent actions, and environment observations tagged `[ENVIRONMENT]` |
| `label` | binary safety judgement, 0 or 1 |
| `reference` | human-annotated description of what the risk actually was |
| `scenario` | the application scenario |
| `attack_type` | the risk category |

**Two evaluation settings.** *Safety judgment* scores the binary label with **F1, recall
and specificity**. *Risk identification* is open-ended: the model writes an analysis and
GPT-4 grades it against the human `reference`.

**The result that makes this interesting.** The best model tested, GPT-4o, reaches
**74.42% F1**. Most of the 11 models evaluated do not meaningfully beat random. The
authors also report that fine-tuning on safety judgement helps substantially while
prompting strategies do not.

**Why that number is an opportunity.** A frontier LLM reading a full transcript — with the
user's instruction, the agent's reasoning, and every environment response — reaches 74%
F1. Our layer sees strictly less (no instruction, no reasoning, no responses), uses no
model at runtime, and costs a table lookup plus arithmetic. If it lands anywhere near that
number, the interesting claim is not accuracy — it is **accuracy per unit of cost and
per unit of visibility**. If it lands far below, that is a real, publishable calibration
of what the call stream alone can support.

### What it would take to run our scorer on R-Judge

This is the honest engineering cost, not a one-liner:

1. **Extract the tool calls.** Parse `contents` into an ordered call list per record —
   tool name plus arguments. Environment turns are discarded (we would not see them).
2. **Get a severity matrix for R-Judge's tools.** Our score starts at `cell(tool, asset)`,
   which requires a scan. R-Judge's tools are not MCP servers we have scanned. Either run
   the scanner over synthesised catalogs for its 5 application categories, or fall back to
   the tool-impact ladder alone and accept a weaker base.
3. **Resolve assets.** Our `cell` needs a resource, and R-Judge records may not name one
   cleanly. Expect the binding layer's error rate to dominate here; measure it separately
   rather than folding it into the headline.
4. **Aggregate to a record-level score.** R-Judge labels whole records; we score calls.
   Max over the record is the conservative choice and matches the aggregation the
   [risk-adaptive TBAC work](https://arxiv.org/abs/2510.11414) recommends.
5. **Threshold and report F1/recall/specificity** — the same three metrics, so the
   comparison is direct.

Steps 2 and 3 are where this can fail honestly, and both should be reported.

## EPSS — the evaluation frame we should be using

[EPSS](https://arxiv.org/pdf/1908.04856) (Jacobs et al., also in ACM DTRAP) predicts
whether a vulnerability will be exploited in the wild. Its structure is the same as ours:

| EPSS / CVSS | ours |
|---|---|
| CVSS base score — how bad if exploited | `cell(tool, asset)` — how bad if this call is misuse |
| EPSS probability — how likely to be exploited | `likelihood` — how normal this action is here |
| remediation threshold | band threshold |
| level of effort — how many CVEs you must patch | how many calls a human must review |

The key borrowing is not the model. It is **the vocabulary and the reporting format.**

**Coverage** = TP / (TP + FN) — of everything that was genuinely bad, what share did we
flag? This is recall.

**Efficiency** = TP / (TP + FP) — of everything we flagged, what share was genuinely bad?
This is precision.

**Effort** = how much work the strategy costs, expressed as the number of items flagged
per thousand.

Renaming precision and recall this way is not cosmetic — it forces the report into the
shape a practitioner actually decides with. The canonical EPSS illustration: patching
everything at CVSS ≥ 8.8 means remediating **253 of every 1,000 published CVEs to reach
about 51% coverage, for roughly 5% efficiency**. Nineteen wasted patches for every real
one. Stated that way, the tradeoff is arguable; stated as "AUC 0.86" it is not.

### What to change in our reporting

Our current tables lead with AUC and AP. Both are threshold-free, and a threshold-free
metric cannot answer "how much human review does this buy me." Replace, or at minimum
supplement, with an operating-point table per server:

| threshold | effort (calls flagged per 1,000) | coverage | efficiency |
|---|---|---|---|
| band ≥ high | … | … | … |
| band ≥ critical | … | … | … |
| top-20 by score | … | … | … |

Three further disciplines worth adopting from the same literature:

- **Report against the base rate, always.** At 1% misuse, efficiency of 0.02 is twice
  random and effectively nothing; 0.48 is 48× random. The multiple is the honest figure.
- **Cite [Axelsson](https://dl.acm.org/doi/10.1145/357830.357849)** (TISSEC 2000) for why
  a rare positive class makes false alarms — not detection — the binding constraint. Our
  design doc argues this from first principles; it is a 26-year-old known result.
- **Hold out data and publish the held-out numbers.** EPSS v3 published precision and
  recall against held-out test data, and that transparency is a large part of why it was
  adopted.

## AgentHarm, Agent-SafetyBench, FORTIS — and the one trick that makes them usable

All three evaluate **whether an agent behaves badly**. None of them evaluates a
server-side scorer. That sounds disqualifying, and it is not, because of one observation:

> When these benchmarks run an agent, the agent emits tool calls. Those calls are exactly
> our input. The benchmark's own label tells us whether the episode was harmful.

So the recipe is the same for all three: **run the benchmark, capture the tool-call trace,
throw away everything else, score the trace with our layer, and evaluate the score against
the benchmark's label.** We are not competing with the agents — we are harvesting labelled
traffic that somebody else built and validated.

### AgentHarm

[AgentHarm](https://arxiv.org/abs/2410.09024): **110 explicitly malicious agent tasks**
(440 with augmentations) across **11 harm categories** including fraud, cybercrime and
harassment. The defining property is that the agent is asked to do harm *directly* — this
is misuse at the user's request, not injection.

**Use it for:** the malicious end of the spectrum, where labels are unambiguous. If our
score does not separate AgentHarm traces from benign traces of the same tools, the layer
does not work, and we would know that cheaply. Treat this as a floor test, not a
headline: real misuse is subtler than deliberate harm.

### Agent-SafetyBench

[Agent-SafetyBench](https://arxiv.org/abs/2412.14470) (code:
[thu-coai/Agent-SafetyBench](https://github.com/thu-coai/Agent-SafetyBench)): **349
interaction environments, 2,000 test cases, 8 risk categories, 10 failure modes**, each
case annotated with its anticipated failure mode, every sample manually reviewed at least
twice. Sixteen agents were evaluated and **none scored above 60% on safety**.

**Use it for:** the volume and the failure-mode annotations. This is the largest labelled
set in our direction, and because each case carries *which* failure mode was expected, it
supports a much more useful result than one aggregate number — a per-failure-mode
breakdown of where a static severity matrix suffices and where it is blind. That table is
a paper section on its own, and it directly attacks the open question of whether the
runtime terms earn their place.

### FORTIS

[FORTIS](https://arxiv.org/pdf/2605.09163) (code:
[lili0415/FORTIS-Benchmark](https://github.com/lili0415/FORTIS-Benchmark)) benchmarks
**over-privilege in agent skills** — whether an agent accomplishes its objective using
only the privilege the task required, or reaches for more. Permissions are represented as
scopes attached to skill definitions, so tasks come with a notion of minimum-necessary
privilege.

**Use it for:** validating the *permission dimension* — the factor the current formula
does not have. Over-privilege is very nearly a definition of misuse in our threat model:
the caller is authorised, so nothing is technically violated, yet it is reaching beyond
what its job needs. FORTIS supplies labelled examples of exactly that, with the
minimum-necessary baseline already annotated, which is the hard part to construct
ourselves.

### Choosing between them

| benchmark | venue | size | label | what it costs us to use | best used for |
|---|---|---|---|---|---|
| R-Judge | **EMNLP Findings 2024** | 569 records | binary safe/unsafe + risk text | tool extraction + a severity matrix for its tools | head-to-head vs a published F1 |
| AgentHarm | **ICLR 2025** | 110 / 440 tasks | harmful by construction | run agents, capture traces | floor test — does the score separate at all |
| Agent-SafetyBench | arXiv (no venue confirmed) | 2,000 cases | unsafe + failure mode | run agents, capture traces | per-failure-mode breakdown; largest volume |
| FORTIS | arXiv | not yet counted | over-privilege vs minimum | map skills/scopes to our tools | evidence for the permission dimension |

### Which evaluation style gets accepted where

Worth being deliberate about, because the two communities reward different tables.

**ML venues (ICLR, EMNLP) accept benchmark papers judged by binary outcome metrics** —
attack success rate, F1, safety score. AgentHarm (ICLR 2025) and Agent Security Bench
(ICLR 2025) report attack success; R-Judge (EMNLP Findings 2024) reports F1, recall and
specificity. None of them reports a ranking metric.

**Security venues accept prioritisation evaluated as ranking.** EPSS is published in ACM
DTRAP and is judged entirely on coverage/efficiency at an operating point; Axelsson's
base-rate analysis is ACM TISSEC. This is the literature where "we did not block anything,
we ordered the queue" is a recognised contribution rather than a missing experiment.

Our layer produces an ordering, so the second frame fits and the first does not. The
practical implication is that **a threshold plus F1 should still be reported** — it is the
only way to sit in the same table as R-Judge — but the headline should be the
operating-point table, and the claim should be triage quality, not detection.

Cheapest first: **R-Judge** (static records, no agent execution needed) before anything
requiring an agent harness.

## Where this sits in OWASP's vocabulary

Worth naming precisely, because it settles two recurring questions at once.

**We are not an API1 (BOLA) control.** [Broken Object Level Authorization](https://salt.security/blog/owasp-api-security-top-10-explained)
has topped the OWASP API list since 2019 and accounts for roughly 40% of API attacks. It
is the risk that an API accepts an object ID without checking the caller owns it —
exactly the `get-event(eventId=...)` question. Detecting it requires ownership context and
testing under more than one identity at once; the state of the art
([AuthProbe](https://arxiv.org/abs/2607.20574), [Barabanov et al.](https://arxiv.org/abs/2201.10833))
is specification-driven and multi-identity. We have neither ownership nor identity, so
this is out of scope by construction rather than by omission.

**We are an [API4:2023 — Unrestricted Resource Consumption](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/) signal.**
OWASP renamed that entry from "Lack of Resources & Rate Limiting" specifically to stress
the root cause rather than the symptom, and the root cause is a call consuming more than
it should. That is what the breadth factor measures, and it gives the work a named
category to sit in.

The one BOLA-adjacent thing that *is* available without ownership is **enumeration** —
the discovery phase, separate from the exploitation phase. Cloudflare's API Shield flags
it on "drastic differences in the number of unique elements requested by different user
sessions", which is object cardinality per session: breadth again, but across calls
rather than within one.

**And the non-role-based frontier is intent, not attributes.** The 2026 line of work —
[Intent-Governed Tool Authorization](https://arxiv.org/html/2606.22916v2),
[SkillScope](https://arxiv.org/pdf/2605.05868), [aiAuthZ](https://arxiv.org/pdf/2607.05518),
[Do Coding Agents Understand Least-Privilege Authorization?](https://arxiv.org/abs/2605.14859)
— moves from *who are you* to *what did you come here to do*. IGAC's "intent-tool
mismatch" (a call that is "statically authorized yet not authorized by the user's current
expressed intent") is this project's definition of misuse in someone else's words. The
difference is vantage point: those systems sit agent-side and can read intent; this one
sits server-side and cannot. That makes them related work to distinguish from, not an
approach to adopt — and the server-side position is the one that survives a compromised
agent.

## What none of them give us

Stating the gap plainly, so no adaptation layer gets mistaken for a result:

- **No scanned severity matrix.** Every benchmark supplies traces, none supplies a
  `(tool, asset)` matrix. Our base score has to be built for their tools, and that build
  is a confound to report, not hide.
- **No organizational policy.** Asset sensitivity in this framework comes from an org's
  policy register. Benchmark environments have no such register, so that input has to be
  synthesised or neutralised.
- **No MCP transport detail.** These are agent-framework traces, not MCP wire traffic, so
  nothing in them exercises caller identity, scopes, or sessions.
- **Not a rare base rate.** Benchmarks are roughly balanced by construction; production
  misuse is not. Any number taken from them must be re-reported at a realistic rate before
  it means anything operationally.

## References

- [R-Judge: Benchmarking Safety Risk Awareness for LLM Agents](https://arxiv.org/abs/2401.10019) — Findings of EMNLP 2024 · [code](https://github.com/Lordog/R-Judge) · [paper](https://aclanthology.org/2024.findings-emnlp.79.pdf)
- [AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents](https://arxiv.org/abs/2410.09024)
- [Agent-SafetyBench: Evaluating the Safety of LLM Agents](https://arxiv.org/abs/2412.14470) · [code](https://github.com/thu-coai/Agent-SafetyBench)
- [FORTIS: Benchmarking Over-Privilege in Agent Skills](https://arxiv.org/pdf/2605.09163) · [code](https://github.com/lili0415/FORTIS-Benchmark)
- [Exploit Prediction Scoring System (EPSS)](https://arxiv.org/pdf/1908.04856) — Jacobs et al.; also ACM DTRAP [10.1145/3436242](https://dl.acm.org/doi/10.1145/3436242)
- [The Base-Rate Fallacy and the Difficulty of Intrusion Detection](https://dl.acm.org/doi/10.1145/357830.357849) — Axelsson, TISSEC 2000
- [Uncertainty-Aware, Risk-Adaptive Access Control for Agentic Systems](https://arxiv.org/abs/2510.11414)
- [A Fraud-Detection-Inspired Framework for LLM Agents Security](https://arxiv.org/html/2605.01143)
- [Role-Stratified Conformal Risk Control for LLM Tool Calls](https://arxiv.org/abs/2607.24343)
- Out-of-direction, for related work only: [MSB](https://arxiv.org/abs/2510.15994), [Progent](https://arxiv.org/abs/2504.11703), [dual-graph provenance](https://arxiv.org/pdf/2605.26497), [MCP-DPT](https://arxiv.org/abs/2604.07551)
