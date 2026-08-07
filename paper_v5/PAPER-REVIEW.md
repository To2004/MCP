# Paper review — story, clarity, and A*-venue readiness

Companion to `CITATION-AUDIT.md`. Produced 2026-08-03 by a multi-agent audit
(story-arc, clarity, hostile-reviewer) over all five sections, with the strongest
empirical claims re-verified by hand against the repository. Items marked
**[verified]** were re-checked directly; items marked *[agent-computed]* are
reproducible from artifacts already on disk but were not re-run here.

---

## 1. The structural problem: the paper proves its parts, never its product

§1 contribution 3 promises an evaluation *"used to measure whether the calculated
risk levels match organizational judgment."* No experiment does that.

- RQ1 measures **sensitivity** against the held-out table.
- RQ2 measures the **impact ladder** against an earlier internal LLM arm.
- RQ3 measures **session separation** on synthetic labels.
- RQ4 measures a **false-positive rate**.

`ρ(c)` — which §3 calls *"the object to design"* — is never compared to
organizational judgment, even though the oracle exists and everything after the
primitives is, by §4.1, deterministic. There are 1,048 scored (tool, resource)
cells (208+520+320) and an oracle sensitivity column, and they are never composed.

**Smallest fix, zero new experiments.** Substitute the organization's held-out
sensitivity into Eq. (2), band the result, and report band agreement between the
pipeline's `ρ` and that oracle-composed band across all 1,048 cells. Arithmetic
over existing artifacts: four lines of prose and a four-row table. It converts the
arc from "our inputs are right" to "our output is right," and it directly tests
whether the six one-tier sensitivity misses survive the multiply and the blast floor.

If the number is bad, the same-size fix points the other way: rewrite contribution 3
to promise per-factor agreement, and say composite validation is future work. What
is not defensible is the current state, where §1 promises the composite and §5
delivers four components.

---

## 2. Confirmed defects in the paper's description of its own system

### 2.1 §4.1 describes the wrong banding function **[verified]**

The paper says:

> Banding is not a raw threshold: it encodes explicit security floors — any
> irreversible operation is at least medium — derived by measuring where an LLM
> reviewer systematically disagreed with raw thresholds.

That is `band_label()` in `src/mcp_security/static_scoring/pipeline.py:413`, which
keys on an **impact scale of 1–3** (`impact == 3` = irreversible) and cuts at
`BAND_THRESHOLDS = {"medium": 8, "high": 24}` on a 60-point scale.

But Eq. (2) commits the paper to `score ∈ [1,125]` and Table 2 to a **five-tier**
ladder. That dispatches to `band_label_v5()` (line 506), whose own docstring says
the opposite:

> the band is a straight threshold on that number, nothing else … not because of
> any per-case rule
>
> severity enters the SCORE (via the primitives and the deterministic blast
> floors), never the band

So §4.1's most distinctive design claim about banding is **not a property of the
system that produced Section 5's numbers.**

Related: the paper never states the cut-points anywhere. `BAND_THRESHOLDS_V5 =
{"medium": 17, "high": 50, "critical": 100}` appears in no table, equation, or
prose — while RQ3's entire result is a sweep over two of them. That is a
reproducibility gap on a criterion AAMAS lists explicitly.

### 2.2 The band is fragile enough that enforcement drifts between identical runs **[verified]**

Over the uniform grid of all 125 (sensitivity, blast, impact) triples with the
shipped 17/50/100 cut-points, **72.8% of cells change enforcement band if any one
primitive moves by ±1** (48% for each primitive taken alone). On the actual
351-cell corpus the figure is *75.8%* *[agent-computed]*.

Read against §5's own disclosure — *"An earlier arm measured 23–35 cells per server
of pure run-to-run variance with the prompt held fixed"* — this implies roughly
**15–22 cells per server change enforcement band between two identical runs of the
same pipeline on the same inputs.**

§4.1 says: *"Determinism buys exactly one thing … band boundaries, twin
reconciliation and the floor do not drift between runs."* True, and beside the
point: the **decision** drifts, which is the only thing an operator cares about.
A framework whose §4.7 promise is *"The decision is auditable"* cannot have a fifth
of its table move on re-scan without saying so.

`scripts/formula_sensitivity.py` already computes this analysis and is not reported.

### 2.3 §3 forbids what §4.6 does

§3: *"Nor does the server observe intent … The score below is therefore a function
of those five alone, never of what the agent meant."*
§4.6 signal (3): *"LLM judge … classifies **intent**."*

It is optional and unrun, but the design violates the threat model's own boundary
and neither section acknowledges the other.

---

## 3. RQ3 is circular — worse than the paper's own disclosure admits **[verified]**

The paper concedes the labels are *"a property of the generator, not an independent
annotation."* The actual coupling is tighter than that. In
`scripts/make_dynamic_testbed.py`:

```python
sensitivity: dict[str, int] = raw.get("asset_sensitivity", {})   # line 239
crown = [a for a, s in concrete.items() if s >= 4]               # line 246
```

`raw` is the scan artifact — **the scorer's own output file.** "Adversarial" is
defined as destructive tools applied to assets *the scanner rated ≥ 4*. The static
scorer multiplies sensitivity by impact; the generator partitions on sensitivity
and impact. The reported 56% / 91% static recall therefore measures how faithfully
the banding threshold reproduces the generator's partition rule. Any monotone
function of the same two variables scores similarly.

The dynamic half repeats this one level up: the generator's adversarial classes are
documented as *"reads a crown jewel then exfiltrates it"* and *"mass crown reads,
exfil, destructive ops"* — naming, in comments, the exact detectors of §4.6 signals
(1) and (2). The +25 points of recall is a rule catching sessions written to be
caught by that rule.

This also explains the one result the paper reports and cannot account for: misuse
was constructed as a legitimate persona making one wrong-target call inside normal
work — i.e. deliberately shaped to defeat baseline-deviation and read-then-write.
The flat 24% → 24% is a fact about the generator, not about accidental insiders.

**RQ3 as constructed cannot support its heading.** Either rebuild the labels
independently of the scan, or evaluate on an external corpus (AgentDojo, InjecAgent)
and report where the graded score ranks trajectories those benchmarks already label.
The "no external benchmark supplies graded severity" defence is about *graded* ground
truth; it does not excuse the absence of a comparison on the binary task they do supply.

---

## 4. No baseline anywhere

Not one number in §5 is compared against an alternative method. RQ1 has no
competitor; RQ2 compares the ladder against *the authors' own earlier LLM arm*;
RQ3 compares the system against a piece of itself; RQ4 compares nothing.

Baselines that could be built quickly, in ascending order of awkwardness at absence:

1. **Monolithic-LLM.** Same model, same two documents, one band asked directly.
   This tests the paper's *central* design claim — §2's *"decomposed into named
   factors … rather than delegated whole to a judge"* — and the plumbing already
   exists from the v4 arm.
2. **MCP-annotation baseline.** §1 spends a paragraph arguing the four hints are
   inadequate; §5 concedes none of the three catalogs declares any. The paper
   attacks a baseline on a corpus where it is undefined.
3. **Established methods.** DREAD, CVSS v3 base, NIST SP 800-30, OWASP, AIVSS.
4. **Formula ablations.** `max(s,b,i)`, `s+b+i`, `s×i`, `s` alone. §4.1's
   *"Multiplying rather than averaging keeps a low factor influential"* is a
   plausibility argument a single table would settle.

Two of these already exist on disk and were not reported: `formula_sensitivity.py`
(the ±1 analysis) and `evaluate_vs_human.py`, which grades against *"a PANEL of
independent oracles"* — hand-authored heatmap plus DREAD, CVSS v3, NIST SP 800-30/60,
OWASP/AIVSS, MAESTRO — and reports inter-rater agreement as *"the irreducible
'legitimate disagreement' ceiling."*

---

## 5. RQ1's headline is weaker than the paper presents it

- **A bag-of-words baseline reaches 91% within-one** (69.6% exact) against the
  paper's 100% / 89.3% *[agent-computed, ~20-line matcher, no tuning]*. A constant
  always-3 predictor reaches 83.9% within-one. The exact-agreement gap (89% vs 70%)
  is the real effect and the number worth defending; the within-one headline the
  paper made load-bearing is nine points above word overlap.
- **The label distribution is never reported** ({1:7, 2:11, 3:11, 4:25, 5:2} —
  45% of resources share one label), so a reader cannot compute those baselines.
- **The Slack register contains a duplicate** **[verified]**:
  `usergroup-membership` and `user-group-membership`, both rated 4.
  `server-profiles.md:402` says *"Same access-control asset (generated naming
  variant — keep equal to the row above)."* That is a free correct answer in the
  denominator of n=56.
- **The policy handed to the scorer names the class for nearly every register row.**
  GitHub's Routine row reads *"Repository catalog, branch names, commit listings,
  issue listings and search hit lists"*; the register rows are `repository-catalog`,
  `branch-directory`, `commit-list`, `issue-catalog`. *"It states no severity number
  anywhere"* is literally true and materially misleading — it states the **class**,
  and class→number is a fixed monotone ladder the framework owns.
- **One annotator.** Ground truth and the policy prose were written by the same
  people against the same spec. No second rater, no κ, no α. The paper's own
  uncited neighbour (`owireduashley2026severity`) reports Krippendorff's α = 0.91.
- **No confidence intervals.** n=56 with 6 errors gives a Wilson 95% CI of roughly
  78–95% on exact agreement; §5 reports "88–90%" on n=16 and n=20 with no interval.

---

## 6. Venue fit — the objection most likely to sink it

Across all five sections, these strings appear **zero** times: *multiagent,
multi-agent, coordination, negotiation, norm, institution, collective, emergent,
equilibrium*. "Autonomy" appears once, in the single sentence citing
`pynadath2002adjustable` — which is not in Related Work, and whose author order is
wrong (see `CITATION-AUDIT.md` §2.5).

Reference venue profile of the 49 cited works:

| Venue class | Count |
|---|---:|
| arXiv preprint, no venue | **26** |
| Peer-reviewed CS venues (S&P, EMNLP, ACL, TOSEM, PACMSE, ARES, MASS, KSE) | 9 |
| Standards and specs | 9 |
| Other journals | 4 |
| **JAIR / AAMAS / AAAI / IJCAI / JAAMAS** | **1** |

The CCS block makes it official: the 500-weight concept is *Security and
privacy~Distributed systems security*, with *Intelligent agents* at 300.

And the model is single-agent by construction — one server, one agent, one call.
`x` and `h` are one connection's and one agent's history. A reviewer will ask what
breaks if you replace "agent" with "client," and the answer is nothing.

**The AAMAS thread also never pays off.** §1 promises *"the score makes that
threshold computable"*; §4.7 retires it — *"The intermediate review outcome …
is not evaluated here"*; §5 operates a binary flag. The paper spends three sections
arguing a graded score beats a binary verdict, then evaluates a binary flag.

**Route to an AAMAS paper** (next cycle, not this deadline):

1. Make the **transfer-of-control decision** the contribution, not the score.
   Eq. (1) already has three outcomes. Measure the operator: at each θ_r, how many
   calls reach a human, what fraction were worth escalating, and the cost asymmetry
   between a missed escalation and a wasted one. That is a policy over autonomy
   levels, and AAMAS reviewers know how to referee it.
2. Make it genuinely multi-agent — which your testbed already supports and does not
   exploit: several personas share one server and one resource pool, each with its
   own `h`, and one agent's score depends on what others have already done to that
   resource. Cumulative blast across concurrent agents, contention on crown-jewel
   resources, one agent's escalation moving another's threshold. Or delegation
   chains, which is where "the server cannot see the principal" gets interesting.
3. Re-cite for the venue: adjustable autonomy, mixed-initiative interaction,
   transfer-of-control strategies, electronic institutions, norm enforcement,
   organizational models of MAS. Aim for 10–15 such citations, not one.
4. Flip the CCS block so *Computing methodologies~Intelligent agents* leads.

**If the target stays a security venue** (CCS / USENIX / ACSAC / NDSS), objection 6
evaporates entirely and the paper is much closer to submittable — the remaining work
is baselines, the RQ3 rebuild, and the §4.1 correction.

---

## 7. Submission-blocking administrivia

- **The abstract is a placeholder.** `main.pdf` p.1 reads *"[To be written:
  abstract — write last …]"*. AAMAS requires abstract registration a week before the
  paper deadline and prohibits placeholders.
- **`\nocite{*}` is still in `main.tex:143`**, so four never-cited entries appear in
  the reference list: `almandalawi2025policyaware`, `li2025accesscontrol`,
  `owireduashley2026severity`, `shi2025sok`. Three of these are the most dangerous
  papers in the file (see `CITATION-AUDIT.md` §6).
- **No Discussion, no Conclusion** — sections 06 and 07 are commented out. The body
  ends on *"beyond catalog capture, the vendor servers themselves were not driven
  live."* A reviewer reads that as an unfinished submission.
- **No figure.** Five tables of percentages, four equations across two sections
  describing one dataflow (Eq. 2 → Eq. 3 → Eq. 4 → Eq. 1). §4.6's *"Two compositions
  coexist, entering at different points"* is a sentence a diagram makes trivial.
- **Limitations are misplaced** — they sit between RQ4 and Table 5, so the reader
  hits "19–22% of cells move" before the table it refers to.
- **The system has no name outside §4.** `\textsc{McpRisk}` appears four times, all
  in §4. Title, abstract, intro and evaluation never name the thing.

---

## 8. What the abstract must say, given only what the body proves

Include: MCP servers as protected party and agents as risk source; the graded
per-invocation score (sensitivity × blast × impact, 1–5 each) replacing a binary
verdict; sensitivity derived from policy prose with no per-resource ratings,
validated at 50/56 exact and 56/56 within one tier against a held-out organizational
table over three real vendor catalogs (55 tools); a deterministic impact ladder that
decided all 55 tools with zero model calls at 93% agreement with the LLM arm; a
request-time layer raising adversarial recall 56%→81% at fixed 9% benign fall-out;
0.8% false positives on 400 real `mcp-server-git` calls.

Do **not** claim: end-to-end risk accuracy, evaluation of the review tier,
judge-free scoring, cross-organization generality, or insider-misuse detection.

---

## 9. Language — the highest-value rewrites

Full list (20 vague phrases, 12 overlong sentences, 13 over-claims, with
replacements written out) is in `~/.cache/citecheck/out/narr1.md`. The ones that
matter most, because each is a claim rather than a style point:

| Line | Now | Change to |
|---|---|---|
| `01:88` | "No existing method estimates what a concrete MCP invocation would cost." | "We are not aware of a method that estimates…" |
| `02:95` | "None scores the unit…" | "None **of these** scores the unit…" (scope to the enumerated works) |
| `01:98` | "none prices the resource the call reaches" | "none **of them** scores the resource…" |
| `05:59` | "RQ1: policy text recovers the organization's severities." | "RQ1: policy text recovers the organization's ratings to within one tier, and exactly in 50 of 56 cases." |
| `05:66` | "it lands on it or immediately beside it, **everywhere**" | drop "everywhere"; add "This is one policy document, so it establishes the reading on this organization, not across organizations." |
| `05:228` | "RQ4: the calibration transfers to real traffic." | "RQ4: the calibration held on one real-traffic corpus." |
| `05:241` | "all three scored high" | add "Three hand-designed cases are an illustration of the separation, not a measurement of detection rate." |
| `05:133` | "the tool axis **can be** decided without a model call" | "**On these three catalogs** the tool axis **was** decided without a model call… We have no evidence about catalogs on which the rules abstain." |
| `03:118` | "a single flag threshold, **swept across bands**" | "a single flag threshold… at two settings, *high* and *critical*" (two points is not a sweep) |
| `04:74` | "§5 **quantifies** [run-to-run variance] for blast radius" | "§5 reports how far blast cells move **between two scoring arms**, and quotes a run-to-run band measured on an earlier version" |
| `01:121` | "evaluate it on tool catalogs captured from real vendor MCP servers, paired with organizational policies…" | say **synthesized** here as contribution 3 does eleven lines later, and mention that RQ3 runs on written-for-this-study profiles and RQ4 on a real git trace |
| `01:136` | "affect the score **as intended**" | state the intended direction and magnitude, or cut |

Also: §1 defines *misuse* broadly ("the inappropriate use of a legitimate
capability", including injected chains), and §5:167 silently narrows it to
"accidental-insider behaviour" — the one class where the contribution is flat
(24% → 24%). Two definitions, one word; a reader will not notice the swap, and a
reviewer who does will treat it as evasion.

---

## 10. Priority order

**Before any submission**

1. Remove the withdrawn `huang2026caller`; re-anchor the identity claim (`CITATION-AUDIT.md` §1.1).
2. Rewrite the novelty claim against `zhang2026stars` / `yang2026agenttrust` (§1.2, §2.1).
3. Fix §4.1's banding description and state the 17/50/100 cut-points.
4. Write the abstract; remove `\nocite{*}`; add Discussion and Conclusion.
5. Apply the §9 scope-narrowing rewrites and the bib corrections.

**Makes it competitive**

6. Add the composite ρ-vs-oracle table (§1 here) — one table, no new experiments.
7. Add RQ1 baselines (majority-class, lookup, monolithic-LLM) and the label histogram.
8. Report the ±1 band-stability table from `formula_sensitivity.py`.
9. Cite ToolEmu and the four dangling bib entries; add the peer-reviewed anchors
   from `CITATION-AUDIT.md` §7.

**Not fixable this cycle**

10. RQ3's label circularity — rebuild with independent labels or move to an
    external corpus.
11. A second organization's policy and a second annotator.
12. Venue re-scope to AAMAS (§6), if AAMAS is the target rather than a security venue.
