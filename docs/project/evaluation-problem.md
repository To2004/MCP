# What Exists Now, and the Evaluation Problem

A plain statement of the two layers that are built, what each one has been measured
at, and why neither number can currently be defended as *accuracy*. Written to be
read start to finish before any further evaluation work is planned.

The short version: **both layers exist and run; neither has ground truth.** The
static layer is graded against documents we wrote and an LLM judge we run. The
dynamic layer is graded against corpora we generate, whose labels come from the
generator. Every headline number so far is a measurement of self-consistency, not
of correctness.

## Part 1 — The static layer (design time)

### What it is

A scan of an MCP server produces one number per `(tool, asset)` pair, before any
traffic exists:

```
cell = asset_sensitivity × blast_radius × tool_impact          1 … 125
bands: low <17 · medium 17-49 · high 50-99 · critical ≥100
likelihood is pinned to 1.0 at scan time
```

| dimension | who decides it |
|---|---|
| `asset_sensitivity` | an LLM classifies each asset against the organization's **policy document** — the org supplies no numbers |
| `tool_impact` | a deterministic ladder (`static_impact.py`); the LLM only decides where the ladder abstains |
| `blast_radius` | an LLM rubric, plus deterministic fixups (bulk twins, alias twins, no roof) |

### Where it lives

`reports/experiments/v7/five_level_v2_policy_v7_iso/` — the current reference arm,
four servers, each with a `.json` (full scan), a `_matrix.csv` (one row per cell),
and a `.md` (human-readable matrix).

| server | tools | assets | cells | scored | N/A | low / med / high / crit |
|---|---:|---:|---:|---:|---:|---|
| `github_helios` | 26 | 19 | 494 | 132 | 73 % | 38 / 61 / 33 / 0 |
| `fs_corp_filesystem` | 14 | 16 | 224 | 101 | 55 % | 31 / 36 / 34 / 0 |
| `calendar_aurora` | 13 | 17 | 221 | 80 | 64 % | 26 / 31 / 18 / 5 |
| `slack_vireo` | 16 | 15 | 240 | 62 | 74 % | 16 / 39 / 5 / 2 |

`v7_iso` is one of four arms. The same four organizations were also scanned with
their policy written in NIST and CIS shapes, and against the earlier `nacombo`
baseline register. Everything except the policy document and its matching
sensitivity prompt is held fixed across arms.

### What it does *not* do

It never sees a call. It scores the pairing, not the request — so it cannot know
who is calling, how often, or with what arguments.

## Part 2 — The dynamic layer (call time)

### What it is

One multiplicative pass over the static cell, per call:

```
final = min( 125 , max( cell(tool, asset) × likelihood × escalation , floor ) )
```

| factor | question | range | source |
|---|---|---|---|
| `cell` | how bad if this went wrong? | 1 … 125 | the scan |
| `likelihood` | how normal is this action for this company? | 0.10 … 1.00 | observed history, keyed `(company, tool)` |
| `escalation` | is this call unusually large here? | 0.9 / 1.0 / 1.3 | Tukey fences over this deployment's argument history |
| `floor` | how far may a discount pull it down? | the pre-change band's lower bound | the scan's bands |

Design: [`dynamic-layer-design.md`](dynamic-layer-design.md). Arithmetic and a
worked example: [`dynamic-layer-formula.md`](dynamic-layer-formula.md). Results:
[`reports/experiments/dynamic_layer/RESULTS.md`](../../reports/experiments/dynamic_layer/RESULTS.md).

Two properties are structural and worth restating: **only the cell can make a score
large** (the runtime can shrink, nudge, and clamp, but never invent risk the scan
did not price), and **nothing is blocked** — the output is a ranking for a review
queue.

### Status per factor

| factor | status |
|---|---|
| `cell` | works — carries essentially all measured signal |
| `likelihood` | built, measured, **net negative on 3 of 3 servers** |
| `escalation` | built and correct, **never once fired** — no corpus varies call size |
| `floor` | works — and in the floor sweep it is the thing doing the detecting |

### The headline measurement (misuse at 1 % of calls, 30 seeds)

| server | scoring | AUC | **AP** | AP sd |
|---|---|---:|---:|---:|
| `github_helios` | static cell only | 0.862 | **0.485** | ±0.342 |
| | × likelihood | 0.865 | 0.478 | ±0.339 |
| `slack_vireo` | static cell only | 0.713 | **0.021** | ±0.005 |
| | × likelihood | 0.655 | 0.018 | ±0.005 |
| `calendar_aurora` | static cell only | 0.868 | **0.602** | ±0.297 |
| | × likelihood | 0.737 | 0.203 | ±0.224 |
| — | random baseline | 0.500 | 0.010 | — |

Read as: on two servers the **static matrix alone** reaches 48× and 60× the base
rate, and the runtime term subtracts from it. On the third the matrix is at chance
and nothing rescues it.

## Part 3 — The evaluation problem

Four distinct problems get called "the evaluation problem". They have different
causes and different fixes, so they are separated here.

### 3.1 The static layer has no ground truth at all

Stated in the v7 report itself: *"None of these four servers has held-out numeric
ground truth."* Three of the four have no section in `server-profiles.md`; the
fourth uses path-shaped asset ids that do not align with the register's concept
ids. So the v7 tables measure **movement** against a baseline and **agreement**
between arms — never correctness.

Two findings make that gap concrete rather than theoretical:

**The frameworks disagree with each other.** Three organizations describing the
same deployment under ISO, NIST and CIS:

| server | shared assets | unanimous | within one tier | ≥2-tier splits |
|---|---:|---:|---:|---:|
| `fs_corp_filesystem` | 5 | 20 % | 60 % | 2 |
| `github_helios` | 7 | 14 % | 71 % | 2 |
| `slack_vireo` | 6 | **0 %** | 67 % | 2 |
| `calendar_aurora` | 7 | 14 % | 71 % | 2 |

`vireo-announcements` scores 5 under ISO, 2 under NIST, 5 under CIS. If the input
document determines the answer, three faithful readings should not spread three
tiers apart. Either the documents genuinely disagree — in which case there is no
single correct number to be graded against — or the scanner is misreading them.

**The judge cannot settle it, because the judge is us.** `JUDGE_SENSITIVITY.md`
re-derives each tier from the policy text alone and reports **45 % scanner error on
ISO, 54 % on NIST, 20 % on CIS**. That is either a serious defect or a noisy
second opinion, and there is no way to tell from inside the system: the policy was
written by us, the scanner is an LLM, and the judge is the same LLM shown less
context. The worst case in the table (`vireo-announcements`, policy implies 1,
scan produced 5) is a four-tier miss on an asset the policy explicitly classes
Public — which suggests the judge is at least sometimes right, and therefore that
the 45 % is not pure noise.

> **The static problem is not "our accuracy is unknown". It is that the object we
> would grade against — a correct sensitivity tier for an asset — is not defined
> by anything outside our own documents.**

### 3.2 The dynamic layer's corpora decided its results

Every dynamic number to date comes from corpora generated by
`scripts/dynamic_design/make_realistic_misuse.py` and its predecessors. Nine
defects have been found in them, and the first three inverted the sign of the
result:

| # | defect | effect |
|---|---|---|
| 1 | misuse repeated 20-42× on the same cell | made misuse the agent's *dominant habit* — any frequency signal must call it routine |
| 2 | attacks more repetitive than benign (github 19.2 vs 7.9 repeats/cell) | inverted every novelty signal |
| 3 | misuse/malicious 25-33 % of every stream | "unusual" stops meaning anything |
| 4 | **corpus and scan disagree on asset names** (`announcements` vs `vireo-announcements`) | **45 % of Slack calls silently dropped**, incl. 133 misuse |
| 5 | attack assets disjoint from benign in 6 of 9 apps | the asset *is* the label; asset-aware signals score ~1.0 for the wrong reason |
| 6 | agents one-shot (0 of 91 span >1 day) | per-agent history cannot accumulate |
| 7 | no magnitude variation in arguments | escalation untestable — still open |
| 8 | `live_scale_all.csv` is a concatenation of the per-org files | double counting |
| 9 | corpora blocked by org | a chronological split trains and tests on disjoint apps |

The damage is not hypothetical. Defects 1-3 produced a misuse AUC of 0.24 / 0.41 /
0.74 — a measurement of how the generator was written. Defect 4 produced a Slack
result of AP 0.107 → 0.244 that was reported as *the one server where the
likelihood term earned its place*; with every call scored, Slack sits at 0.047 and
the term is negative there too.

> **Every dynamic result so far has been overturned at least once by a corpus bug,
> not by a change to the design.** That is the strongest available evidence that
> the corpus, not the signal, is what is being measured.

### 3.3 Even a clean corpus is too small to decide anything

At a realistic 1 % misuse rate there are 4-5 positives per run. AP's standard
deviation is ±0.30 on the two servers that work — nearly the size of the mean. One
call landing at rank 3 rather than rank 30 swings an entire run, and GitHub and
Calendar are not distinguishable from each other.

More seeds do not fix it: the generator can only draw from 5-12 distinct misuse
cells per server, so the independent sampling is capped by the catalog, not by the
seed count.

And the metric choice matters more than it should. Slack's AUC of 0.713 sounds
usable; its AP of 0.021 is twice the base rate — nothing. **AP is the one to read**,
because ROC's x-axis is a false-positive *rate* and fifteen false alarms against
500 benign calls barely move it.

### 3.4 There is no external benchmark that fits without a build

Public benchmarks in our threat direction exist — R-Judge, AgentHarm,
Agent-SafetyBench, FORTIS — and
[`external-benchmarks-and-positioning.md`](external-benchmarks-and-positioning.md)
works through each. None of them can be run against this system as-is, for one
structural reason:

> **Our score starts at `cell(tool, asset)`. No benchmark ships a severity matrix,
> an asset register, or an organizational policy. Those are exactly the inputs
> whose correctness is in question (§3.1), so we would have to build them for the
> benchmark's tools — and the build becomes a confound in the result.**

Two further mismatches: benchmark traces are agent-framework records, not MCP wire
traffic, so nothing in them exercises caller identity; and they are roughly
balanced by construction, while production misuse is rare, so any number taken from
them has to be re-reported at a realistic base rate before it means anything.

### 3.5 A separate, smaller problem: the caller is not identifiable

The whole runtime design keys on a caller. Searching every captured log and corpus
for what MCP actually carries:

| field | what it identifies |
|---|---|
| `clientInfo` (from `initialize`) | 12 distinct values, **all naming the SDK or our harness — never the agent** |
| `mcp-session-id` | the connection, per-session |
| `run_id` | our harness's own grouping, not from the protocol |
| IP | `127.0.0.1`, 1,718 times |

The protocol has a field for agent identity and in practice it carries
`{"name": "mcp", "version": "0.1.0"}`. This is why the likelihood term is keyed
`(company, tool)` rather than per-agent — and it means no per-agent runtime signal
is measurable at all until clients are required to set a meaningful
`clientInfo.name`.

### The shape of the problem, in one picture

```
        we write the policy document
                  ↓
        an LLM reads it → asset sensitivity  ─┐
        a ladder + LLM  → tool impact         ├→  the static matrix
        an LLM rubric   → blast radius       ─┘        ↓
                                                       ↓
        we write the corpus generator                  ↓
                  ↓                                    ↓
        it emits calls AND their labels  ───────────→ scored
                                                       ↓
        we compute AUC / AP against those labels  ←────┘
                  ↓
        we grade the static matrix with an LLM judge
        that reads the policy document we wrote
```

Nothing in that loop enters from outside. Every arrow is one of our own artifacts,
so the loop can be made perfectly self-consistent while being wrong end to end.

## What may and may not be claimed today

**Defensible now:**

- The static matrix ranks generated misuse at 48-60× the base rate on two of three
  servers — *on corpora we generated*.
- The likelihood term does not currently earn its place: negative on 3 of 3.
- The band floor is doing the detecting in the floor sweep; loosening it makes
  results strictly worse.
- The framework an organization writes its policy in **changes the score**, by up
  to three tiers on the same asset. This one is a real finding and does not depend
  on ground truth, because it is a statement about *variance between inputs*, not
  about correctness.

**Not defensible now:**

- Any statement of the form "the scanner is accurate to within one tier".
- Any per-server comparison of dynamic AP (variance ±0.30 swamps the differences).
- Any claim that `escalation` works or does not work — it has never fired.
- Any comparison against published detection numbers (R-Judge's 74 % F1 and the
  like), because our input pipeline for those benchmarks does not exist yet.

## What would break the circle

Ordered by cost, cheapest first. Each one injects something we did not author.

1. **Fix defect 4 at source** and re-run. Asset-name reconciliation between corpus
   and scan is a bug fix, not research, and it silently distorted 45 % of one
   server's calls. Until it is fixed at source, every corpus-based number carries
   an asterisk. *Cheap, and it blocks everything downstream.*
2. **Report at an operating point, not threshold-free.** Replace the AUC/AP lead
   with EPSS-style **coverage / efficiency / effort** per band threshold. This does
   not add ground truth, but it makes the existing numbers answer the question a
   practitioner asks ("how much review does this buy me"), and it makes the
   base-rate multiple impossible to hide.
3. **Get one external asset register.** The static problem is entirely about where
   sensitivity tiers come from. A single real organization's classification policy
   — or a published one — with tiers we did not assign turns §3.1 from "undefined"
   into "measurable on one server".
4. **Run R-Judge.** Cheapest of the external benchmarks because it needs no agent
   harness — static records only. The honest cost is steps 2-3 of the recipe in
   `external-benchmarks-and-positioning.md`: a severity matrix for its tools, and
   asset resolution whose error rate must be reported separately rather than folded
   into the headline.
5. **Generate traffic where call sizes actually vary**, so `escalation` can be
   measured for the first time.
6. **Require `clientInfo.name`** in the harness and any live deployment, so that a
   per-agent signal becomes measurable at all.

## Open questions, unresolved

- Does the likelihood term belong in the formula at all? It is negative on three of
  three servers, and the calendar regression has a stated cause (its misuse uses
  the tools the company runs hourly) that will recur on any deployment of that
  shape.
- Why is the Slack matrix near chance where the other two are 48-60× base rate?
  That is a static-arm finding, and no runtime signal can repair it.
- Is the judge's 45-54 % "scanner error" a real defect or a second opinion? It
  cannot be answered without an external register (item 3 above).
- What is the correct sensitivity of an asset, and who says so? Everything in §3.1
  reduces to this.

## References

- [Dynamic Layer — Design](dynamic-layer-design.md) · [Dynamic Layer — The Calculation](dynamic-layer-formula.md)
- [`reports/experiments/dynamic_layer/RESULTS.md`](../../reports/experiments/dynamic_layer/RESULTS.md) — the measured dynamic results and the corpus defect table
- [`reports/experiments/v7/README.md`](../../reports/experiments/v7/README.md) · [`FRAMEWORK_RESULTS.md`](../../reports/experiments/v7/FRAMEWORK_RESULTS.md) · [`JUDGE_SENSITIVITY.md`](../../reports/experiments/v7/JUDGE_SENSITIVITY.md)
- [External Benchmarks and Where This Work Sits](external-benchmarks-and-positioning.md)
- [Dynamic Scoring Design](dynamic-scoring-design.md) — superseded generation, kept for its reasoning
