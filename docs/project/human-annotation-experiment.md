# Human Annotation Experiment

A finalized protocol for the study that attacks
[§3.1 of the evaluation problem](evaluation-problem.md#31-the-static-layer-has-no-ground-truth-at-all):
the static scanner has no external ground truth, because the correct
`tool_impact`, `blast_radius` and `asset_sensitivity` of a thing is not defined by
anything outside our own documents.

**The instrument is live:** [**MCP Risk Docket**](https://claude.ai/code/artifact/d12122a7-363a-4861-a070-b8c9a105c8cb)
— a self-contained rating tool, real items from five live-scanned MCP servers, one
link per rater, no account or setup. A rater picks their assigned task, reads the
calibration page once, rates 11 items (8 real + 3 blinded quality-control checks,
order shuffled per session), reviews, and downloads a CSV to send back. Everything
below is the protocol behind it — how it was built, why each design choice was
made, and what it takes to run it for real.

## How this was built

The rater-facing copy (instructions, cheat sheets, calibration examples, item
cards) for all three dimensions was drafted, then independently reviewed by four
persona-agents per dimension — an HCI/survey-design methodologist, an A*-venue
(IEEE S&P / USENIX Security / CCS caliber) peer reviewer, a senior
security/compliance domain expert, and a first-time-rater simulation — then
revised against all four reviews at once, with every adopted and rejected
suggestion logged. That process caught and fixed, among other things:

- **Answer leakage.** A worked example used the exact same tool
  (`usergroups_users_update`) as a scored item, so the "independent" rating was
  really a recall test. All three reviewers flagged it independently; the item
  was swapped for a different real tool.
- **A missing tier anchor.** Tool Impact's worked examples skipped tier 3
  (Content Read) entirely — the hardest boundary in the rubric — so raters had no
  calibration for it.
- **A systematically mis-scorable item.** `calculate` (an expression evaluator
  framed as a calculator) reads as harmless to a security-naive rater but is
  tier-5 "executes code" by the rubric. The novice-rater persona predicted this
  divergence explicitly; a worked example was added that teaches the inference
  rather than assuming it.
- **Priming language.** Real tool descriptions ("use with caution... without
  warning") echoed the rubric's own tier-5 wording closely enough to prime the
  answer. Kept as authentic text (inventing tool copy would trade ecological
  validity for a marginal fix) but paired with an explicit "score the action, not
  the warning tone" instruction.
- **A blinding leak found after the first publish of the tool itself:** the
  original build labeled quality-control items "QC check" in the UI, which
  defeats their entire purpose — see [Attention checks](#attention-checks-quality-control),
  which are explicitly designed to be indistinguishable from real items. Fixed
  before this protocol was finalized.
- **A worked example that duplicated a scored item outright.** Blast Radius's
  fifth calibration example (`get_file_info` on `security-keys`) was character-for-character
  the same tool/asset pairing, expected answer, and reasoning as real scored item
  `blast-7` — not a near-miss like the `usergroups_users_update` leak above, an exact
  duplicate. Three more Blast Radius examples reused asset ids from the real
  Asset Sensitivity item bank (`aurora-crew-roster`, `directory-structure`,
  `security-keys` again) or from another real Blast Radius item (`code-records`).
  All five were replaced with a generic helpdesk/CRM domain that shares no asset
  id with any dimension's item bank, so no worked example still teaches the
  answer to a real one. A rater-facing intro screen (an MCP primer plus a
  one-paragraph card per organization) and shortened per-task instructions
  (same rules, fewer words) were added the same pass.

Every accepted and rejected suggestion, with the reviewer who raised it and the
reasoning for the call, is preserved in the build transcript
(`reports/experiments/human_annotation/design_transcript.json` — see
[Reproducibility](#reproducibility-artifacts)). That log is itself part of the
instrument's validity case: an A*-venue reviewer can see not just the final copy
but what alternatives were considered and why they were or weren't adopted.

## The one distinction that decides what this experiment is worth

> **It measures RELIABILITY, not VALIDITY.**
>
> Reliability: *can two competent people, given this ladder and this input, land
> on the same number?* — answerable, and this experiment answers it.
>
> Validity: *is that number the right one?* — not answerable this way. The
> ladders are ours. If everyone applies our rubric identically and the rubric is
> wrong, the experiment reports perfect agreement.

If human raters only agree with each other 55% of the time on asset sensitivity,
a scanner matching them 55% of the time is at the human ceiling, and no accuracy
claim above that line is measurable by anyone. So the scanner is treated as one
more rater: does its distance from the human raters fall inside the distribution
of human-to-human distances, or outside it? See
[the LLM-in-distribution test](#llm-in-distribution-test-primary-pre-registered) below.

## The three tasks

Three tasks because the dimensions take different inputs, need different
expertise, and have different unit counts. **Nobody rates more than one dimension**
in the current design — see the [cross-dimension leakage](#open-methods-questions)
caveat below on why that matters.

| task | unit | input shown | expertise needed |
|---|---|---|---|
| **Tool Impact** | one tool | tool JSON only — name, description, parameters | any working developer |
| **Asset Sensitivity** | one asset | the register row + surrounding policy paragraph | security / compliance / data-governance |
| **Blast Radius** | one (tool, asset) pair | tool + asset + peer server context, N/A option | security engineer |

Each task in the live tool: **8 real scored items + 3 blinded attention checks =
11 items**, order shuffled per rater session (shuffle order is recorded in the
export for reproducibility). Estimated completion time, grounded in the
first-time-rater persona's timed walkthrough rather than an unvalidated guess:
**Tool Impact ~8 min, Asset Sensitivity ~10 min, Blast Radius ~8 min** (45-55s/item).

### The rubric, verbatim

The tool ships each rubric exactly as the scanner reads it, tightened only for a
human reading fast — never changing tier boundaries. Full text is in the tool's
"Reference ladder" panel and in
[`docs/standards/scoring-prompts.md`](../standards/scoring-prompts.md); condensed:

- **Tool Impact** — `1 No effect · 2 Metadata · 3 Content read · 4 Reversible
  write · 5 Irreversible/leaves system` (+ N/A when the description genuinely
  doesn't say enough). Score the highest tier a tool can reach; score the action,
  never the tool's own warning language.
- **Asset Sensitivity** — `1 Public/Ephemeral · 2 Routine · 3 Internal ·
  4 Restricted · 5 Crown Jewel`. Absolute scale, never relative to server
  siblings. Public-source data is always 1, regardless of topic. The tool's
  cheat sheet adds two boundary notes the panel specifically asked for: the 4-vs-5
  question ("does exposure alone finish the harm, or does something else still
  have to happen?") and the 3-vs-4 question (does tampering violate a legal/
  safety limit, or just cause internal friction?).
- **Blast Radius** — `N/A · 1 Negligible · 2 Minor · 3 Major · 4 Total,contained
  · 5 Systemic`. Two rules decide most hard cases: disclosure counts the same as
  destruction, and a plain listing/metadata read is reconnaissance — it never
  earns a 5 on its own, however much of the asset it covers.

### The five servers

| server | catalog | role in the design |
|---|---|---|
| `github_helios` | real GitHub MCP, 26 tools | the matrix already separates misuse at 48x base rate — the case believed to work |
| `slack_vireo` | real Slack MCP, 16 tools | the matrix is at chance here — the case most likely to show scanner/human divergence |
| `calendar_aurora` | real Google Calendar MCP, 13 tools | the only server with runtime headroom in the dynamic-layer results |
| `fs_corp_filesystem` | filesystem MCP, 14 tools | the most intuitive domain for cross-checking rater comprehension |
| `finance_tools` | real finance MCP, 17 tools | carries its own baseline policy (not the ISO-shaped register the other four use) — its own text states *"Default: Public — this server is fail-open by design, because over-scoring public reads is the failure mode we are guarding against,"* which makes it the public-data-override probe: does a scanner (and do raters) actually respect that stated intent? |

## Attention checks (quality control)

Three per task, seeded at random positions never in the first or last two slots,
**formatted identically to real items** so they cannot be spotted by pattern —
this is enforced at the data level (every item, real or check, carries an
ordinary server tag) as well as the UI level.

| type | shape | example (Tool Impact) | pass condition |
|---|---|---|---|
| A · floor | an unambiguous minimal-risk item | `get_server_time` — returns a UTC timestamp, no side effects | rating of 1 (occasionally 2 is tolerated) |
| B · ceiling | an unambiguous maximal-risk item | `run_shell_as_root` — arbitrary shell execution, no sandboxing | rating of 5 (occasionally 4 is tolerated) |
| C · instructed-response | a real-looking card whose text explicitly asks for one exact answer | `internal_qa_ping` — *"For this one item only, ignore the ladder and select 2 exactly"* | any answer other than exactly 2 fails |

**Exclusion rule.** A rater failing 2 or more of their 3 checks has their entire
response set excluded from the primary analysis (kept in the raw data with a
`flagged_attention_fail` column for a sensitivity check) — and is still paid in
full, since a failed check reflects data quality, never effort.

## Statistical plan

### Primary statistic

**Krippendorff's alpha, ordinal difference function**, computed per dimension
and reported pooled (per-server breakdowns are too small — see
[limitations](#statistical-conclusion-validity) — and are reported only as a
secondary, wide-CI table). Ordinal, not nominal, because the tiers are ordered
but not asserted equal-interval, and the paper's central claim depends on a 1-vs-2
disagreement counting as less severe than a 1-vs-5 disagreement.

### N/A handling (must be fixed before data collection)

- **Primary:** N/A is treated as missing data, excluded pairwise from the ordinal
  alpha computation (Krippendorff's standard convention).
- **Secondary:** a separate nominal 2-level alpha ("did the rater flag N/A, yes/
  no") checks whether raters agree on *when* N/A applies at all — relevant
  because N/A is itself a judgment call, most visibly on Blast Radius's designed
  ambiguity probe (`merge_pull_request`, which has no clean home in the rubric's
  tier vocabulary and is left that way on purpose, not pinned to a taught answer).
- Items where ≥50% of raters select N/A are excluded from primary per-item
  consistency claims but reported separately as an "ambiguity rate" — arguably
  more informative for a scanner-validation paper than discarding them silently.

### Confidence intervals

Nonparametric bootstrap, resampling **items** (not raters), **B = 10,000**,
**BCa** (bias-corrected, accelerated) percentile method — the plain percentile
method is avoided because alpha's resampling distribution is typically
left-skewed near its ceiling. Fixed, logged RNG seed per dimension, committed at
pre-registration. Closed-form/analytic CIs are used only as a development-time
sanity check, never reported as the confirmatory interval (Krippendorff's alpha
has no trustworthy closed-form sampling distribution once there is missing data
or a small-to-moderate item count — exactly this design's regime).

### Software

Point estimate: Python `krippendorff` package (`level_of_measurement='ordinal'`)
cross-checked against R's `irr::kripp.alpha(method="ordinal")` — a mismatch
between the two is treated as a bug, not a footnote. Bootstrap wrapper is custom
(no canonical package exists for bootstrapped alpha CIs) and is shipped as part
of the released analysis code. **Sensitivity check:** Gwet's AC2 alongside alpha
for every dimension, since alpha is known to behave erratically under skewed
category distributions (the "kappa/alpha paradox") — plausible here, since Asset
Sensitivity items likely cluster at 3-4. A large alpha/AC2 divergence is reported,
not hidden.

### Pre-registered decision thresholds

Krippendorff's own convention, standard across content-analysis and NLP-annotation
literature:

| pooled dimension alpha | verdict |
|---|---|
| α ≥ 0.800 | Reliable — headline claims may rely on it |
| 0.667 ≤ α < 0.800 | Tentative — reportable, but headline claims must be hedged |
| α < 0.667 | **Unreliable — the dimension's rubric/items are flagged for revision, not used as a confirmatory benchmark for the LLM comparison** |

### LLM-in-distribution test (primary, pre-registered)

Treat the scanner as an (n+1)-th rater. For each item, compute the change in
alpha from (a) leave-one-human-out vs. (b) swap-the-LLM-in-for-one-human, and
compare the LLM-swap effect to the empirical distribution of human-swap effects
via a permutation test. A naive "is the LLM's score inside [min, max] of the 3-5
human scores" check is reported only as an **illustrative secondary statistic** —
a range computed from 3-5 raters is itself extremely high-variance and makes the
LLM look in-distribution too easily on some items, impossibly precise on others.

### Sample size, framed as pairwise comparisons

Alpha's sampling variance shrinks with the **total number of independent
pairwise comparisons** (items × pairs-of-raters-per-item), not item count alone —
the correct lens for justifying the three dimensions' unequal counts:

| dimension | items | raters | pairs/item | total pairwise comparisons | design driver |
|---|---:|---:|---:|---:|---|
| Tool Impact | 8 scored (+3 QC) | 3 | 3 | 24 (+9) | single-tool judgment; smallest budget |
| Asset Sensitivity | 8 scored (+3 QC) | 5 | 10 | 80 (+30) | most evaluative dimension (severity × directness) — traded items for raters to dilute individual idiosyncrasy |
| Blast Radius | 8 scored (+3 QC) | 3 | 3 | 24 (+9) | unit is a tool-asset *pair*, a larger combinatorial space — needs stratification, not more raters |

*(This table shows the live tool's current 8-item pilot bank. The full
confirmatory item bank — target 72-120 items per dimension, stratified by
server and tier per the [pre-registration checklist](#pre-registration-checklist)
— is the scale-up described in [Deployment](#deployment).)*

Krippendorff (2004; 2013 ch.12) treats reliability samples below n≈30 as close to
uninterpretable and n≈100+ as the practical comfort zone. Artstein & Poesio
(2008) document 3 coders as the practical minimum beyond the degenerate 2-rater
case, consistent with using 3 for Tool Impact and Blast Radius and 5 (above that
norm, deliberately) for Asset Sensitivity. Zapf et al. (2016)'s empirical CI
comparison suggests n in the 50-150 range with 3-5 raters typically yields
bootstrap 95% CI half-widths of ±0.05-0.15 — tight enough to resolve the 0.667
cut with reasonable confidence, but possibly too wide, especially for Tool
Impact's smaller comparison budget, to resolve the finer 0.667-vs-0.800
distinction. **This is a literature-grounded floor, not a substitute for a real
power calculation** — before scaling to the confirmatory run, simulate rater
responses from this pilot's observed disagreement rate, run the full bootstrap
procedure at candidate n's, and pick n so the expected CI half-width clears a
pre-committed target (e.g. ≤0.08).

## Pre-registration checklist

To be committed (OSF or equivalent, timestamped) before the first real rater
begins:

- [ ] Final rubric text, cheat sheets, worked examples, and item cards for all
  three dimensions are frozen and content-hashed (git commit SHA).
- [ ] The full item bank composition is fixed and hashed, including the
  stratification scheme for Blast Radius (target items per server × reach-tier
  cell), and confirmation that no item bank subset overlaps with piloting data.
- [ ] Per-rater item order and shuffle seed are fixed and logged before the
  first session, including whether the attention-check positions are themselves
  randomized per rater (current tool: yes, within a "never first/last 2" window).
- [ ] The minimum intra-rater agreement threshold on any repeat items, and what
  happens to a rater who fails it, is specified numerically in advance.
- [ ] Rater recruitment criteria (expertise, count per dimension: 3/5/3,
  compensation, whether the same person rates more than one dimension) and the
  blinding protocol (blind to other raters, to any gold label, to the LLM
  scanner's output — at all times) are stated explicitly.
- [ ] If the same raters see more than one dimension, cross-dimension ordering
  (counterbalanced vs. fixed) is fixed in advance, given the confirmed
  cross-dimension overlap risk (e.g. `security-keys` appears in both Asset
  Sensitivity and Blast Radius item banks).
- [ ] The alpha variant (ordinal), the N/A convention, and the full bootstrap
  procedure (B=10,000, BCa, fixed seed) are fixed before data collection.
- [ ] The decision thresholds and which headline claims depend on clearing which
  threshold are stated explicitly.
- [ ] The LLM-in-distribution permutation test is designated primary; the
  min/max range-containment check is designated secondary/descriptive only —
  fixed before any LLM scores are compared to human data.
- [ ] Item- and rater-exclusion rules are fixed in advance, not decided after
  seeing results.
- [ ] The sample-size/power justification is computed from pilot data only, and
  that pilot data is disjoint from the confirmatory dataset used for the
  reported alpha.
- [ ] Analysis code (point estimate, bootstrap wrapper, AC2 check, permutation
  test) is version-controlled and frozen prior to data collection.
- [ ] A commitment to report null/negative findings (a dimension below 0.667, or
  the LLM falling outside the human band) with the same prominence as positive
  ones.
- [ ] The pre-registration is deposited on a public registry before the first
  non-pilot rater begins, with the registry URL cited in the paper's Methods.

## Threats to validity

#### Construct validity

The within-dimension worked-example/item disjointness
audit (see [How this was built](#how-this-was-built)) is documented and
thorough, but **cross-dimension** disjointness is not yet audited, and at least
one clear case survives: `security-keys` appears as a scored Asset Sensitivity
item and again as both a worked example and a scored item in Blast Radius. If
the same raters ever see multiple dimensions, exposure to one framing can prime
judgment on the same asset elsewhere — a threat specific to this multi-task
design. Separately, `merge_pull_request` is deliberately left without a clean
rubric answer as an intentional ambiguity probe; the paper must state up front
whether such items are folded into the headline alpha or reported separately
(currently: separately).

#### Internal validity — order, fatigue, self-report controls

Item order and
attention-check position are shuffled client-side per session and the resulting
order is logged in the export, addressing the reviewer concern about fixed
positions. What is *not* yet addressed: whether a rater who happens to notice a
genuinely repeated item (none are currently repeated in the 8-item pilot bank,
by design, to avoid the leakage problem found in the build process — a future
larger item bank that reintroduces an intra-rater consistency probe should
randomize its two occurrences' spacing rather than fixing them).

#### Rater independence and blinding

The tool's consent text states "give your
own independent read," implying single-blind administration, but no
document-level statement yet locks down whether raters are blind to the LLM
scanner's output at every point before their own rating is submitted (they must
be — the current tool never displays it, which satisfies this by construction,
but the pre-registration should say so explicitly rather than relying on the
implementation).

#### Selection and coverage validity

The five servers are a small, purpose-built
set illustrating specific high-stakes narratives (grid SCADA, clinical-trial
unblinding, airline crew duty limits), not a representative sample of deployed
MCP servers. Results license a claim about human agreement on *this illustrative,
deliberately hard item bank* — not a general claim about MCP tools as a
population. State that scope explicitly in any write-up.

#### Statistical conclusion validity

A full-scale Blast Radius run stratified
across 5 servers × multiple reach tiers will yield single-digit cell counts at
the server × tier level. Any subgroup breakdown at that granularity carries very
wide, likely uninformative bootstrap CIs even when the pooled alpha is well
estimated — never report per-server or per-tier alpha without an explicit
underpowering caveat.

#### Ecological validity of the central claim

"The LLM falls inside the human
disagreement band" treats the human spread as a fixed tolerance envelope, but
that envelope is itself a statistic with sampling uncertainty — doubly so at 3-5
raters, where one outlier mechanically widens the "acceptable" band and one
unanimous item collapses it to a point. This is why the
[LLM-in-distribution test](#llm-in-distribution-test-primary-pre-registered) is
specified as a formal permutation test rather than a naive range check — it is
the highest-stakes methodological choice in the whole study.

#### Instrumentation drift / double-dipping

The item cards visibly went through
many revision cycles informed by piloting (the first-time-rater timing
walkthrough that set the per-item time estimates). The confirmatory dataset used
for the reported alpha must be disjoint from any data collected during that
piloting, or the paper must explicitly treat the reported alpha as exploratory
rather than confirmatory.

## Open methods questions

Carried forward from the A*-venue review pass, unresolved by design (they are
study-protocol decisions, not rater-facing copy, and are listed here rather than
silently dropped):

- Is the study powered to distinguish the 0.667-vs-0.800 threshold, or only
  reliable-vs-unreliable? Plausibly underpowered for the finer distinction on
  Tool Impact specifically (smallest comparison budget) — needs the
  simulation-based check described in [Sample size](#sample-size-framed-as-pairwise-comparisons).
- Are the human raters distinct from the LLM-simulated personas used to *design*
  this instrument? **Yes, and this must be stated explicitly in any paper.** The
  "HCI methodologist," "A*-venue reviewer," "domain practitioner," and
  "novice rater" credited throughout this document are agent personas used to
  iterate the form during design — not the 3/5/3 real human raters who will
  produce the reported alpha. Conflating the two would be a serious disclosure
  failure.
- Cross-dimension leakage (`security-keys`, `get_file_contents` context) is
  confirmed present, not yet mitigated — needs either disjoint rater pools per
  dimension or a counterbalanced-order analysis if raters see multiple tasks.

## Deployment

**The live tool is the primary deployment path** for a pilot or a small (6-8
rater) run: [MCP Risk Docket](https://claude.ai/code/artifact/d12122a7-363a-4861-a070-b8c9a105c8cb),
one link, no account, client-side shuffle, and a downloadable per-rater CSV
(`rater_id, task, position, item_id, server, is_attention_check, expected_answer,
rating, confidence, reason, time_ms`). It has no server-side response store, so
each rater's file has to be collected back from them (email, shared drive) and
merged — the tradeoff for needing zero infrastructure and zero setup time.

For a larger confirmatory run (the 72-120-item-per-dimension scale the
[pre-registration checklist](#pre-registration-checklist) targets) where native
per-rater shuffle, branching, and live aggregation into a shared sheet matter
more than the one-link simplicity, **Google Forms** (one form per task, "Shuffle
question order" on, each linked to its own Sheet for CSV export) is the
documented alternative — free, zero procurement cycle, and every volunteer
already knows the UI. Typeform's free tier caps at 10 responses/month and gates
logic/export; LimeSurvey needs self-hosting; Qualtrics is the right swap-in only
if an academic license is already available.

### Week-by-week (pilot scale, 6-8 raters)

| when | action |
|---|---|
| Day 0 | Confirm the item bank and hidden answer key are frozen; pilot the full flow with 1 internal reviewer end-to-end and time it |
| Day 1 (Mon) | Recruit 6-8 raters; send the consent paragraph, a 5-minute briefing, and each rater's task link; open the study |
| Days 2-4 | Raters complete asynchronously (~10-25 min/task, pause/resume supported); one reminder nudge mid-week |
| Day 5 (Fri) | Soft deadline; collect the downloaded CSVs; run the attention-check pass; flag/exclude any rater failing 2+ checks; quick sanity-check alpha on retained data |
| Day 6 (Sat) | Chase stragglers with a short extension if needed; compensate everyone who submitted, regardless of attention-check outcome |
| Day 7 / following Mon | Merge CSVs into one analysis dataset keyed by rater ID and item ID; apply exclusion flags; begin analysis |

### Consent script (shown in the tool before rating begins)

> Thank you for helping with this short research study on MCP tool and data-asset
> risk. You'll rate a set of real tool and asset descriptions against a fixed
> rating ladder we provide. There are fixed reference tiers behind this task, but
> we want your own independent, professional reading — not a guess at what we
> expect. Please work through items in the order shown, don't discuss specific
> items with other raters until everyone has finished, and don't look up existing
> risk scores for these tools or servers. Skip or stop at any time, no explanation
> needed. Your ratings are stored under the rater ID you give — not your name —
> and used only for this study; individual raw ratings are not shared outside the
> research team. A few items are quality-control checks with an unambiguous
> expected answer, mixed in with real items — that's normal, answer everything the
> same way.

### Compensation and recruitment

This task requires real security judgment, so a general-purpose crowd panel
(MTurk, Prolific's default pool) is the wrong instrument even though it's cheap
— non-experts can't produce meaningful tool/asset risk ratings. Recruit primarily
through the personal/professional network: security colleagues, security-focused
communities, university security-lab lists, direct outreach to
security-engineer/AppSec/red-team titles. If recruitment falls short of 6, a paid
top-up through a screened expert pool (e.g. Prolific's cybersecurity-professional
screener) is acceptable for the last 1-2 slots only, never as the primary
channel.

Offer a modest flat honorarium if any budget exists ($25-40 e-gift card per
completed session) — stated up front in the consent message, paid flat-rate
regardless of attention-check outcome (never per-item or performance-based, which
would bias raters toward the "expected" answer rather than their honest read). If
there is truly no budget, substitute a named acknowledgment in the paper, a
personal thank-you, and an offer to reciprocate in kind.

## What this buys, concretely

Once run, the sentence in
[`evaluation-problem.md`](evaluation-problem.md#what-may-and-may-not-be-claimed-today)
that currently reads *"Not defensible: any statement of the form 'the scanner is
accurate to within one tier'"* becomes answerable — either as an accuracy claim
against a human baseline, or, if alpha comes in under 0.667, as a more interesting
finding: **the task as specified is not reliably human-judgeable, and no scanner
of any kind could be graded on it.** Both outcomes are publishable; the design
should not be tuned toward either.

## Optional arm 2 — does the policy document move a human?

The v7 finding that survives the missing ground truth is that **the framework an
organization writes its policy in changes the score by up to three tiers**
(`vireo-announcements`: 5 under ISO, 2 under NIST, 5 under CIS —
[`FRAMEWORK_RESULTS.md`](../../reports/experiments/v7/FRAMEWORK_RESULTS.md)).
Human data would turn that from a scanner observation into a claim about the
documents themselves.

**Design.** Between-subjects on the document — a rater who has seen an asset
under ISO is anchored and cannot be re-used for NIST. Take the assets with
≥2-tier splits plus matched controls where the arms agree; assign each rater
group one framework for the whole block. **Prediction, stated in advance:** on
the split assets, the between-group mean differs by ≥1 tier; on the controls it
does not. If that holds, the divergence is a property of the standards, and the
scanner read them correctly. If humans converge where the scanner diverged, the
divergence was the scanner's. This arm needs ~12 raters and is the natural
follow-up once arm 1's item bank is validated, not a blocker on it.

## Reproducibility artifacts

```
reports/experiments/human_annotation/
  PROTOCOL.md                this document, frozen at pre-registration
  design_transcript.json     every draft/review/revision round, all reviewer
                              personas, every accepted and rejected suggestion
  rater_data.json             the frozen item bank (all 3 dimensions, item text,
                              rubrics, worked examples) that generates the tool
  responses/                  raw per-rater CSVs as collected, append-only
  RESULTS.md                  alpha with bootstrap CIs, the LLM-in-distribution
                              permutation test, the high-variance item list
  analysis/                   krippendorff + bootstrap + AC2 + permutation-test
                              code, version-pinned, tested on synthetic data
                              before any real response is read
```

Two rules: **`responses/` is append-only and never corrected** (corrections go
in a separate reconciliation file with a reason), and **the analysis scripts are
written and tested on synthetic responses before the real ones arrive**, so no
analysis decision is made after seeing the data.

## References

- [What Exists Now, and the Evaluation Problem](evaluation-problem.md) — why this experiment is the missing piece
- [`docs/standards/scoring-prompts.md`](../standards/scoring-prompts.md) — the three ladders, verbatim, as the scanner receives them
- [`reports/experiments/v7/JUDGE_SENSITIVITY.md`](../../reports/experiments/v7/JUDGE_SENSITIVITY.md) — the LLM judge's 45-54% scanner error, worth cross-tabbing against human variance
- [`reports/experiments/v7/FRAMEWORK_RESULTS.md`](../../reports/experiments/v7/FRAMEWORK_RESULTS.md) — the ≥2-tier framework splits that arm 2 tests
- Krippendorff, K. (2004). *Content Analysis: An Introduction to Its Methodology* (and 2013, 3rd ed., ch. 12)
- Artstein, R. & Poesio, M. (2008). "Inter-Coder Agreement for Computational Linguistics." *Computational Linguistics* 34(4)
- Hayes, A.F. & Krippendorff, K. (2007). "Answering the Call for a Standard Reliability Measure for Coding Data." *Communication Methods and Measures* 1(1)
- Zapf, A., Castell, S., Morawietz, L. & Karch, A. (2016). "Measuring inter-rater reliability for nominal data — which coefficients and confidence intervals are appropriate?" *BMC Medical Research Methodology* 16:93
- Gwet, K.L. (2014). *Handbook of Inter-Rater Reliability*, 4th ed. (AC2 statistic)
