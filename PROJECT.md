# MCP Security — Project Explainer

Self-contained description of this repository and the research in it, written
for someone (or some assistant) with **no prior context**. Nothing here assumes
you have seen the code, the papers, or any earlier conversation.

Repository root: `~/MCP`

---

## 1. What this project is

**The one-line version.** An MCP server exposes tools that touch real
organizational resources. This project computes, *before a call executes*, how
much damage it could do — and turns that number into an access-control
decision.

### Background: what MCP is

The Model Context Protocol (MCP) is the standard way AI agents reach external
capabilities. An MCP **server** advertises a catalog of **tools** (`read_file`,
`create_or_update_file`, `conversations_history`, …) through a `tools/list`
discovery call. An MCP **client**, driven by an LLM agent, picks a tool and
invokes it over JSON-RPC. The server executes it against real resources: files,
git repositories, databases, message archives.

### The problem

MCP standardises **how** a call is made. It says nothing about **how dangerous**
the call is. A server receiving `create_or_update_file` has no protocol-level
way to know whether the target is a public README or the repository holding
infrastructure secrets — and no way to tell a correct agent from a mistaken or
manipulated one, since all present the same identity, token, and interface.

### The threat model — this is inverted from most of the literature

> **The MCP server is the protected resource. The agent is the risk source.**

Most MCP security research runs the other way: how a *malicious server* harms
the *agent* that trusts it (tool poisoning, rug pulls). This project studies
**agent → server**. Never reverse this when writing about the work.

The subject is **misuse through legitimate access**, not intrusion. Harm needs
no attacker:

- **Human error** — an operator states a task loosely, delegates too broadly,
  or provisions an agent with far more capability than the work needs.
- **Agent failure** — the model hallucinates a tool call, or proceeds with an
  action whose risk it can itself articulate.
- **Manipulation** — prompt injection or goal drift, a further route to the
  same place rather than the main subject.

All of these produce the same thing at the server: a well-formed, correctly
authorised call whose consequence exceeds what anyone intended.

---

## 2. How the scoring works

### The unit of analysis

Not the tool. The **whole invocation**: a tool, the resource it touches, the
arguments it carries, and the context and history it arrives in.

### The static (design-time) score

Computed once per server, for every (tool, resource) pairing it exposes:

```
score = resource_sensitivity (1-5)  x  blast_radius (1-5)  x  tool_impact (1-5)
      -> 1..125
      -> deterministic assembly (bulk twins, alias twins, gated floors)
      -> band in {low, medium, high, critical}
```

Bands are not raw thresholds. `band_label()` encodes explicit security floors —
for example, any irreversible operation is at least *medium* regardless of the
product. The floors were derived by measuring where an LLM reviewer
systematically disagreed with raw thresholds.

**The three primitives:**

| Primitive | Question it answers | How it is produced |
|---|---|---|
| **Tool impact** (1–5) | Is this a read, a write, or a removal? | A deterministic rule ladder; an LLM only where the rules abstain |
| **Resource sensitivity** (1–5) | How bad if this resource is lost? | LLM: classify the resource against the org's policy, then map the policy's consequence language onto 1–5 |
| **Blast radius** (1–5) | Who and what is different afterwards? | LLM, per (tool, resource) pair |

### The tool-impact ladder

One question decides the tier — what *operation* is this?

| Tier | Operation |
|---|---|
| 1 | none — the server talks about itself (ping, health, version, whoami) |
| 2 | metadata — names, ids, counts, sizes, timestamps, schema, listings |
| 3 | content read **or** limited write (append a line, add a comment, set one named field) |
| 4 | ordinary write — the caller supplies what the item says |
| 5 | removal or execution — delete, purge, truncate; run code; move money |

281 vocabulary patterns, plus 119 ambiguous single words, 10 generic read verbs
and 9 parameter detectors.

**The 3/4 boundary is externally grounded**, which matters because it is the
line most likely to be challenged. Two independent published standards draw it
in the same place: RFC 5789 (`PATCH`, partial modification) versus RFC 9110
(`PUT`, complete replacement); and CVSS v4.0 integrity `VI:L` ("the amount of
modification is limited") versus `VI:H` ("a total loss of integrity").

Breadth is deliberately **absent** from this ladder — how many items a call
reaches is coverage, and blast radius scores that. A bulk variant and its
singular describe the same *operation*.

### The rules-to-model hand-off

The classifier reports a confidence: **0.35** when no tier verb matched at all,
**0.8** when a verb fired, **0.95** when a verb fired *and* an MCP annotation
corroborated it. The LLM is consulted only when confidence falls below **0.5** —
the case where the rules do not know, as opposed to where they disagree.

### The dynamic (request-time) layer

Static answers *"how bad if this happens"*. Dynamic answers *"how abnormal is
this call, from this agent, in this session, given its actual arguments"*.
Four signals, cheap to expensive:

| # | Signal | LLM? | What it does |
|---|---|---|---|
| 0 | Embedding likelihood | no | Hashing vectorizer over tool + argument tokens, TruncatedSVD, novelty = mean distance to the 5 nearest historical calls, calibrated against the history's own quantiles |
| 1 | Behavioural baseline | no | Deviation from this agent's own history: unseen tool, first touch of a sensitive resource, burst above normal rate |
| 2 | Session sequence risk | no | Cumulative sensitivity in a session; flags sensitive-read → external-write within a window |
| 3 | LLM judge | yes, optional | Decodes obfuscated arguments (base64, hex, shell expansion) and classifies intent |

Two compositions coexist. Band signals (baseline / sequence / judge) fuse via
`escalate()` and can only **raise** risk above the static floor. The embedding
likelihood instead multiplies: `final_risk = static_score x likelihood`, with
likelihood in `[0.1, 1.0]`. The 0.1 floor bounds the discount — a
scanned-critical cell keeps a tenth of its risk even when the call looks
demonstrably normal, and a call with no benign history behind it keeps full
static risk.

Cost: fit under 0.5 s per server, scoring about 0.05 ms per call.

---

## 3. The distinguishing idea — policy, not inventory

This is the part that makes the work publishable, and it is easy to miss.

Every severity model needs to know how sensitive a resource is. Prior work —
including this project's own earlier versions — supplies that with a **labelled
asset inventory**: a table giving each resource a number on a fixed scale.

That table is convenient and, in practice, fictional. A per-resource
sensitivity register is itself among the most sensitive documents an
organization holds, it is stale within weeks of being written, and it is not
what a security function actually publishes.

What a security function publishes is a **classification policy**: named
classes, each described by the adverse impact its compromise would cause, plus
recognition rules for assigning resources to classes. **No numbers anywhere.**
This is the structure FIPS 199 and NIST SP 800-60 prescribe.

So the scanner is given only two documents:

1. the captured tool catalog (`tools/list`), and
2. the organization's **policy** section.

and it must *derive* the sensitivity scale by classify-then-map: locate the
resource in the policy's asset register, apply the recognition rules, map the
matched class's consequence language onto 1–5. The organization states
consequences in its own vocabulary; the rubric owns the scale.

The per-resource sensitivity table is **held out entirely** and used afterwards
only as ground truth.

> Two documents in this repo are easy to confuse:
> - `docs/mcp-tools/server-profiles.md` — the **inventory**. Has a per-asset
>   `Sens.` 1–5 column. **Held out**; ground truth only.
> - `docs/mcp-tools/server-policies.md` — the **policy**. Classification table,
>   asset register, recognition rules. **No 1–5 anywhere.** This is the input.

---

## 4. Repository layout

```
~/MCP/
├── src/mcp_security/        the framework  (~14,200 lines, 59 files)
├── tests/                   49 test files
├── scripts/                 ~100 experiment, evaluation and SLURM scripts
├── docs/                    documentation (see below)
├── demo/                    9 simulated organizations (filesystems, sqlite DBs)
├── reports/                 all experimental output
├── Literature_review/       132 papers, organized and annotated
├── presentations/           slide decks, posters
├── paper_v5/                the AAMAS 2027 paper being written
├── thesis/                  BGU M.Sc. research proposal (LaTeX)
└── paper/                   an earlier IEEE-format write-up (superseded)
```

### `src/mcp_security/` — the framework

| Package | Lines | What it does |
|---|--:|---|
| `static_scoring/` | 7,502 | The LLM pipeline: domain inference → impact, sensitivity, blast → multiply → assemble → band. Also `static_impact.py`, the deterministic ladder |
| `atomic_ops/` | 1,729 | Tool-catalog classifier; tags atomic operations, emits the sensitivity/heatmap workbooks |
| `scanner/` | 1,431 | Assembles a server's description — tools from `tools/list`, resources from the store — and drives the LLM stage |
| `review/` | 1,069 | Verify / judge / advise pipeline over produced scans |
| `dynamic/` | 1,004 | The four request-time signals plus `combine.py` |
| `call_scoring/` | 894 | Resolves an observed call's arguments to a scanned resource, looks up its band |
| `param_scoring/` | 455 | Per-tool input rubrics: which arguments carry magnitude, and how a value escalates a band |
| `llm/` | 116 | Ollama client (local model, no cloud fallback) |

### `docs/`

- `docs/project/overview.md` — framework overview
- `docs/project/architecture.md` + `.png` / `.svg` — architecture diagrams
- `docs/project/dynamic-scoring-design.md` — the design of the request-time layer
- `docs/standards/mcp-policy-spec.md` — the schema a policy document must follow
- `docs/mcp-tools/server-policies.md` — the policies (scanner input)
- `docs/mcp-tools/server-profiles.md` — the inventories (held-out ground truth)

### `reports/`

- `reports/experiments/v1..v6/` — the six experiment generations (§5)
- `reports/dynamic_eval/` — discrimination test, embedding likelihood, real-traffic validation
- `reports/severity_eval/` — comparison against external severity benchmarks
- `reports/scan/` — raw per-server scan output

---

## 5. The research story — six generations

This sequence is the intellectual history of the project. Each generation asked
one question and answered it.

| Gen | Question | Inputs the scanner got | Sensitivity from |
|---|---|---|---|
| **v1** | Which scoring rubric? | tool catalog + demo store | LLM inference |
| **v2** | Does the org's written profile beat inference? | + org profile, then profile only | org profile table |
| **v3** | Which deterministic rules, and how much description context? | tool catalog + profile | org profile table |
| **v4** | Can prompts be standards-grounded? Is tool impact rule-derivable? | tool catalog + profile | org profile table |
| **v5** | Can the scanner **derive** severities from a policy that states no numbers? | tool catalog + **policy** | LLM classify → map |
| **v6** | Can CIA change the *shape* of the matrix rather than its scale? | v5 artifacts, re-priced offline | per-facet split of v5 |

The through-line: each generation removed something the organization had to
hand over. v2 replaced the model's guess with the org's table. v5 removed the
table itself. **v5 is the current best configuration**; v6 is exploratory and
not wired into the scan path.

---

## 6. What has been measured

**All figures are exact. Do not round or extrapolate.**

### Static — does policy text alone recover the org's severities?

Three real vendor servers: **56 resources, 55 tools**.

| Server | Resources | Tools | MAE | Exact | Within 1 tier |
|---|--:|--:|--:|--:|--:|
| calendar | 16 | 13 | 0.125 | 88% | 100% |
| github | 20 | 26 | 0.10 | 90% | 100% |
| slack | 20 | 16 | 0.10 | 90% | 100% |

**50 of 56 exact; nothing off by more than one tier** — against a document that
states no number anywhere. The six misses are all adjacent-tier and defensible.

### Tool impact — the rules needed no model

**55 of 55 tools decided by the deterministic ladder, zero LLM calls**, 93%
agreement (51/55) with the previous generation's LLM, every disagreement one
tier.

> **Important caveat that must always accompany this result:** the LLM fallback
> never fired because all three vendor catalogs declare no MCP annotations, so
> every confidence was either 0.8 or 0.35 — nothing landed near the 0.5
> threshold. The hybrid hand-off is covered by **unit tests only** on this
> corpus.

### Dynamic — does the request-time signal add discrimination?

Ten servers, synthetic sessions labelled benign / misuse / adversarial by
construction. Each session scored static-only and static⊗dynamic.

At flag threshold **critical**:

| Scorer | Recall (adversarial) | Fall-out (benign) |
|---|--:|--:|
| static | 56% | 9% |
| combined | **81%** | **9%** |

**+25 points of recall at unchanged false-positive cost.** 22 of 88 adversarial
sessions are caught *only* by the dynamic signal. At threshold *high*: 91% →
100% recall, fall-out 49% for both.

### Real-traffic validation

A live `mcp-server-git` driven over stdio against a real repository (223
commits): **400 real tool calls**, 399 succeeded, 12 tools, 106 distinct call
signatures. Fit on the first 70% chronologically, scored the held-out 30%.
**Benign false-positive rate 0.8%**; mean held-out likelihood 0.107. The
quantile-anchored calibration, tuned on synthetic data, transferred with **no
adjustment**.

### What is real vs synthesized

- **Real:** the tool catalogs, captured from live vendor MCP servers. The git
  corpus above.
- **Synthesized:** the organizational policies, the resource registers, the
  invocation scenarios.
- Correct term: an **evaluation setting**, never a benchmark.

---

## 7. What has NOT been measured

State these as limitations; never claim them as results.

- **Scalability versus manual assessment.** No measurement exists.
- **The LLM judge** (`dynamic/judge.py`) is wired but was not run in the
  reported evaluation — it needs a GPU job.
- **The rules→LLM hand-off** never fired on this corpus.
- **External benchmark comparison** for the dynamic task — none exists; graded
  per-action severity ground truth for this problem barely exists at all.
- **Cross-organization generalization.** One policy document, three servers.
- **Live third-party servers.** The vendor tool catalogs are real captures, but
  the GitHub / Slack / Calendar tokens are expired, so those servers were not
  driven live.

---

## 8. Running it

Python project managed with `uv`. The LLM stages use a **local** model
(qwen2.5:32b via Ollama) — there is no cloud fallback by design; if the model
is unreachable the pipeline raises rather than guessing.

```bash
uv sync                                              # install
uv run pytest                                        # 49 test files
uv run ruff check .                                  # lint

# scan a server (static, design time)
uv run python -m mcp_security.scanner --kind github

# the v5 configuration, on the cluster
sbatch scripts/scan_v5.sbatch <stem>

# score one captured session (static + dynamic)
uv run python -m mcp_security.dynamic --session <calls.csv> --server <stem>

# evaluate v5 against the held-out organizational table
uv run python scripts/evaluate_policy_v5.py
```

Scans run on a SLURM cluster with GPU nodes; a scan of one server takes roughly
45 minutes.

---

## 9. Vocabulary

Use these terms consistently; the project's documents do.

| Term | Meaning here |
|---|---|
| **Invocation** | One tool call: tool + resource + arguments + context + history. The unit of analysis |
| **Resource** (or asset) | A thing the server owns and a tool can touch — a repository, a channel, a calendar, a file class |
| **Tool impact** | Reversibility/severity of the *operation*, 1–5. Independent of what it touches |
| **Resource sensitivity** | Criticality if the resource is exposed, corrupted or destroyed, 1–5 |
| **Blast radius** | How far one call reaches — coverage, 1–5 |
| **Band** | The categorical output: low / medium / high / critical |
| **Static / design-time** | Scored once per server from the catalog and policy, before anything runs |
| **Dynamic / request-time** | Scored per call from arguments, context and history |
| **Misuse** | A legitimate capability exercised inappropriately. The subject of the work |
| **Profile** | The held-out inventory with per-resource numbers. Ground truth, never an input |
| **Policy** | The classification document with no numbers. The actual input |

---

## 10. Current state

`paper_v5/` holds an AAMAS 2027 short paper being written from the v5 results,
positioning the work as **risk-based access control for MCP servers**: access
control decides whether an agent *may* act; this adds a computed, graded
consequence score so the server can decide *how dangerous* this particular
invocation is.

For paper-specific context — the argument, the citation set, what is and is not
novel against the 2026 literature — see `paper_v5/BRIEF.md`. For the exact
numbers any text may state, see `paper_v5/GROUND-TRUTH.md`.
