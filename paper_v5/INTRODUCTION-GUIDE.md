# What Belongs in the Introduction

What an introduction has to do, what it must not do, and three worked examples
from real papers — dissected paragraph by paragraph so the moves are visible.

Companion documents: [`AAMAS-2027-RULES.md`](AAMAS-2027-RULES.md) for the
binding constraints, [`WRITING-GUIDE.md`](WRITING-GUIDE.md) for the whole-paper
budget and the narrative rules.

## Contents

- [1. The five moves](#1-the-five-moves)
- [2. What does not belong](#2-what-does-not-belong)
- [3. Example A — MCP at a top-tier venue](#3-example-a--mcp-at-a-top-tier-venue)
- [4. Example B — a strong AAMAS paper](#4-example-b--a-strong-aamas-paper)
- [5. Example C — the closest paper to our work](#5-example-c--the-closest-paper-to-our-work)
- [6. What the three have in common](#6-what-the-three-have-in-common)
- [7. What to steal from each](#7-what-to-steal-from-each)
- [8. How our 1.1 / 1.2 / 1.3 maps on](#8-how-our-11--12--13-maps-on)

## 1. The five moves

Every introduction worth reading makes the same five moves, in order. The
subsection boundaries are a packaging choice; the moves are not optional.

| # | Move | What it must establish | Failure mode |
|---|---|---|---|
| 1 | **Setting** | What exists, at what scale, and why it now matters. | Protocol history. Nobody cares when it was released, only what it now touches. |
| 2 | **Tension** | The thing that does not work, stated so a reader feels it. | Stated as a research gap ("little work has examined…") instead of as a problem someone has. |
| 3 | **Gap** | What existing work produces and why that is the wrong shape. | A literature list. The gap is not "few papers exist"; it is "the papers that exist output the wrong thing." |
| 4 | **Position** | Your specific, falsifiable claim. Named, not described. | Hedging. If a reviewer cannot disagree with it, it is not a position. |
| 5 | **Contributions** | 3–4 items, each mapping to a section and to a result. | Promising what the paper does not evaluate — narrative debt. |

Move 2 is the one most drafts skip. Setting straight into Gap reads as a
literature survey with a proposal attached. The tension is what makes a reader
want the gap resolved.

## 2. What does not belong

- **Method detail.** Name the approach; do not explain it. That is §4.
- **Results beyond one headline number per contribution.** Save them.
- **Definitions of standard terms.** If the venue knows what an agent is, do not
  define it.
- **A roadmap paragraph** — at AAMAS. Section titles do the job. (Note: this
  differs by venue; see Example C, which has one, because ACM SAC security
  papers conventionally do.)
- **Everything you read.** The introduction cites what the argument needs.
  Example A below carries 1,030 words on **six** citations.

## 3. Example A — MCP at a top-tier venue

> **A First Look at the Security Issues in the Model Context Protocol
> Ecosystem** — Xiaofan Li, Xing Gao.
> **DSN 2026** (IEEE/IFIP Int. Conf. on Dependable Systems and Networks).
> arXiv:[2510.16558](https://arxiv.org/abs/2510.16558) · bib key `li2026firstlook`

**~1,030 words · 6 paragraphs · 6 citations · no contributions list**

| ¶ | Words | Opens with | Move |
|---|--:|---|---|
| 1 | 220 | *"The Model Context Protocol (MCP) has recently emerged as a foundational standard for connecting large language models (LLMs) with external tools."* | **Setting.** Ends by naming the ecosystem concretely — hosts (Cursor, Windsurf, Claude Desktop), registries (mcp.so, Smithery), thousands of servers. |
| 2 | 130 | *"Unfortunately, this newly emerging MCP ecosystem also introduces new attack surfaces."* | **Tension + Gap in one.** Closes on the gap sentence: *"However, these studies focus primarily on the security vulnerabilities arising from malicious MCP servers."* |
| 3 | 180 | *"In this paper, we present the first cross-entity security study of the current MCP ecosystem."* | **Position**, declared early. |
| 4 | 200 | *"To examine these two stages, we adopt a hybrid methodology…"* | Methodology + first findings. |
| 5 | 170 | *"Our quantitative analysis shows that weakness at the registry-level allows adversarial or hijacked servers to enter hosts through normal discovery…"* | Findings + the tool they build. |
| 6 | 130 | *"To quantitatively analyze the security issues in MCP registries, we collect 67,057 MCP servers from four decentralized registries… and two centralized registries…"* | Scale + responsible disclosure. |

**What to notice.**

- **Six citations in a thousand words.** A top-tier introduction is not a
  literature review. The citations appear only where the gap sentence needs
  them.
- **The gap is one sentence**, at the end of ¶2, and it is a *directional*
  claim — prior work looks at malicious servers — not a volume claim.
- **"In this paper, we present the first…" lands in ¶3 of 6.** Position is
  declared at the 40% mark, not the 80% mark.
- **No contributions list.** It ends on disclosure instead. This works for a
  measurement paper where the findings *are* the contribution; it would not work
  for ours, which proposes a method.
- ¶1 spends 220 words on setting because MCP genuinely needed explaining in
  2025. **It needs less now** — a 2027 reviewer knows what MCP is.

> **Side note that matters for us:** this is the source of the "67,000 MCP
> servers" figure. It is 67,057 server *listings* collected across six
> registries — not distinct servers, and not a live count. Cite it precisely or
> use the more conservative "on the order of ten thousand" from
> `hasan2025firstglance`.

## 4. Example B — a strong AAMAS paper

> **A Scoresheet for Explainable AI** — AAMAS 2025.
> arXiv:[2502.09861](https://arxiv.org/abs/2502.09861)

**~895 words · 7 paragraphs · 16 citations · ends with contributions**

| ¶ | Words | Opens with | Move |
|---|--:|---|---|
| 1 | 200 | *"It is important for autonomous and intelligent systems to be explainable for a range of reasons."* | **Setting** — why explainability matters, legally and socially. |
| 2 | 150 | *"The importance of explainability has also been recognised by various standards."* | **Standards exist.** Names IEEE P7001 and others concretely. |
| 3 | 180 | *"However, this work does not provide adequate guidance for the development and evaluation of the explainability of systems."* | **Gap** — the standards are too coarse. Closes by quantifying it: *"Hoffman et al. assign each system only a single number (1–7)."* |
| 4 | 115 | *"Following IEEE P7001, we propose to provide this guidance in the form of a scoresheet."* | **Position** — names the artifact. |
| 5 | 65 | *"The scoresheet can be used in various ways with the most obvious being to evaluate the explainability of candidate systems."* | Usage — makes it concrete. |
| 6 | 45 | *"Explanations are used by different people for different purposes…"* | Design rationale, with a forward pointer to §2. |
| 7 | 140 | *"This paper makes a number of contributions."* | **Contributions** — "Firstly… Secondly… Thirdly…" |

**Why this is the one to imitate.** Its argument is structurally almost
identical to ours:

| Scoresheet for XAI | Our paper |
|---|---|
| Explainability matters | Agent access to real resources matters |
| **Standards already exist** (IEEE P7001) | **Standards already exist** (FIPS 199, SP 800-60) |
| But they give no actionable per-system guidance | But nobody automates the classify-then-map they prescribe |
| Propose a **scoresheet** | Propose a **derivation** |
| Show it is usable, generic, useful | Show it recovers the organization's own numbers |

The move worth stealing outright: **¶2 establishes that a standard exists
before ¶3 attacks its inadequacy.** That is far stronger than "no prior work
does X" — it says the field already agrees this should be done, and nobody has
made it operational. We have exactly the same card to play with FIPS 199.

Also note ¶5 and ¶6 are 65 and 45 words. **Short paragraphs are allowed.** A
paragraph that does one small job in two sentences is not a fragment.

## 5. Example C — the closest paper to our work

> **From Description to Score: Can LLMs Quantify Vulnerabilities?** —
> Jafarikhah, Thompson, Deans, Siadati, Liu. **ACM SAC 2026.**
> arXiv:[2512.06781](https://arxiv.org/abs/2512.06781) · bib key `jafarikhah2026description`

**~565 words · 5 paragraphs · 6 citations · contributions list + roadmap**

Chosen because it is the same *shape* of claim as ours: free text in, ordinal
severity out, produced by an LLM, validated against ground truth someone else
assigned.

| ¶ | Words | Opens with | Move |
|---|--:|---|---|
| 1 | 110 | *"Vulnerability management is a fundamental component of software security programs across organizations."* | **Setting** — grounded immediately in NVD volume. |
| 2 | 75 | *"This rapid growth has placed substantial strain on maintainers and threat intelligence providers."* | **Tension** — backlogs, subjective prioritization. |
| 3 | 105 | *"On the other hand, recent advances in GenAI have shown that LLMs possess capabilities that go well beyond natural language generation."* | **Position** — LLMs might do this. Ends on the payoff: automated scoring could clear the backlog. |
| 4 | 165 | *"Motivated by this question, the main contributions of this paper are as follows:"* | **Contributions** — two items. |
| 5 | 110 | *"The remainder of this paper is organized as follows."* | Roadmap. |

**What to notice.**

- **565 words.** A published ACM introduction can be this short. This is direct
  evidence that our 273-word §1.1 plus two more subsections is in range.
- **The tension is operational, not academic** — a backlog, real people
  overloaded. Ours is the same species: an inventory nobody will hand you.
- ¶3 does something we should copy: it does not claim LLMs *will* work. It
  claims they *might*, and makes the paper the test. That framing survives a
  skeptical reviewer far better than asserting the method works.
- The roadmap in ¶5 is a security-venue convention. **Do not copy it for
  AAMAS** — none of the five AAMAS papers sampled has one.

## 6. What the three have in common

| | A · DSN 2026 | B · AAMAS 2025 | C · SAC 2026 |
|---|---|---|---|
| Words | ~1,030 | ~895 | ~565 |
| Paragraphs | 6 | 7 | 5 |
| Citations | 6 | 16 | 6 |
| Contributions list | No | Yes | Yes |
| Roadmap paragraph | No | No | Yes |
| Position declared at | ¶3 of 6 | ¶4 of 7 | ¶3 of 5 |

**The invariants:**

1. **Position lands at 40–60% of the way in.** Never at the end.
2. **The gap is one or two sentences**, and it is about the *shape* of what
   prior work produces, not the *quantity* of it.
3. **Citation count is unrelated to quality.** 6, 16, 6. Two top venues used
   six. Cite for the argument, not for coverage.
4. **Something concrete appears early** — registry names, IEEE P7001, NVD
   volume. None open on abstractions.
5. **Word counts vary 2×** (565–1,030) with no relation to venue tier.

## 7. What to steal from each

- **From A (DSN):** the one-sentence directional gap — *"However, these studies
  focus primarily on…"*. We have the identical move available: prior MCP
  security studies the client side. Also: cite sparingly.
- **From B (AAMAS):** *establish that a standard already exists, then attack its
  inadequacy.* FIPS 199 and SP 800-60 prescribe classify-then-map; nobody
  automates it. This is a stronger opening than any novelty claim, and it is
  the single most valuable structural idea in this document.
- **From C (SAC):** frame the method as a *question the paper tests*, not a
  solution the paper announces. "Can severity be derived from policy alone?"
  beats "We derive severity from policy."

## 8. How our 1.1 / 1.2 / 1.3 maps on

| Our subsection | Moves it carries | Target | Status |
|---|---|--:|---|
| **1.1 Vision and Scope** | 1 Setting + 2 Tension, plus explicit scope boundaries | ~280 w | **Written** (273 w, 6 cites) |
| **1.2 The Gap in Existing Work** | 3 Gap + 4 Position | ~250 w | Stub |
| **1.3 Contributions** | 5 Contributions | ~200 w | Stub |

Total ~730 words — between Example C (565) and Example B (895).

**Checks against the examples, for when 1.2 gets written:**

- Position must appear inside 1.2, not be deferred to 1.3. All three examples
  declare it before the contributions.
- The gap must be one directional sentence, not a survey. With 64 references
  available, the temptation is to spend 250 words listing them. Do not — that
  is §2's job.
- Open 1.2 on the standards-exist move (B), not on "prior work has not…".
- Keep the whole Introduction under ~10 citations if possible. §1.1 uses 6.

## 9. Exemplars — sentences and paragraphs to match

Rules tell you what to avoid; examples give you something to hit. This section
is the target. Everything quoted from a published paper is verbatim and was
read directly; nothing here is reconstructed from memory.

### 9.1 How real papers open each move

One verified sentence per move, from the three dissected papers.

**Setting** — concrete, and dated to the moment:

> "The Model Context Protocol (MCP) has recently emerged as a foundational
> standard for connecting large language models (LLMs) with external tools."
> — DSN 2026

> "Vulnerability management is a fundamental component of software security
> programs across organizations." — ACM SAC 2026

**Tension** — one word turns the paragraph:

> "**Unfortunately**, this newly emerging MCP ecosystem also introduces new
> attack surfaces." — DSN 2026

> "This rapid growth has placed substantial strain on maintainers and threat
> intelligence providers." — ACM SAC 2026

**The gap** — one sentence, and it is *directional*, not about volume:

> "However, these studies focus primarily on the security vulnerabilities
> arising from malicious MCP servers." — DSN 2026, closing ¶2

> "However, this work does not provide adequate guidance for the development
> and evaluation of the explainability of systems." — AAMAS 2025, opening ¶3

Note what neither says: *"little work has examined…"*, *"to date, few papers…"*.
A volume claim invites a reviewer to name a counter-example. A directional claim
says prior work looked the *other way*, which is far harder to refute.

**Position** — declared early and flatly:

> "In this paper, we present the first cross-entity security study of the
> current MCP ecosystem." — DSN 2026, ¶3 of 6

> "Following IEEE P7001, we propose to provide this guidance in the form of a
> scoresheet." — AAMAS 2025, ¶4 of 7

**Contributions** — announced, never sidled into:

> "This paper makes a number of contributions. Firstly, we develop (and
> justify) a scoresheet for explainability… Secondly, we provide additional
> detailed guidance on *how* to complete the scoresheet… Thirdly, we
> demonstrate that the scoresheet is applicable to a range of systems."
> — AAMAS 2025

### 9.2 Two paragraphs from this paper, annotated

These are on-brand by construction. Match this register.

**Exemplar A — a gap paragraph that concedes before it claims.**

> The idea of including a calculated risk value in an access-control decision
> is not new. Quantified risk-adaptive access control was introduced in earlier
> work [9] and was later integrated into attribute-based access-control models
> [19]. Risk-based access control has been widely reviewed [3, 8], applied in
> systems where a numeric trust value affects access decisions [6], and
> recently extended to agentic systems [10].

Why it works:

- **It gives away the strongest counter-argument first.** A reviewer who knows
  `fleming2025tbac` was going to raise it; the paragraph raises it instead.
- **Chronological, so the reader feels the field closing in** — 2007, 2011,
  surveys, deployments, agents — which makes the next paragraph's "but not for
  MCP" land as a narrow, checkable residue rather than a sweeping claim.
- **Five citations, zero gloss.** No sentence explains what any individual
  paper did. That is correct here; explanation belongs in Related Work.
- One idea per sentence. No sentence carries two clauses of new information.

**Exemplar B — a definition paragraph that earns its term.**

> We focus on *misuse*, meaning the inappropriate use of a legitimate
> capability. Misuse does not require a malicious agent or a malicious server.
> It may begin with an operator who describes a task imprecisely, delegates a
> broader goal than intended, or grants the agent more permissions than the
> task requires. Existing studies suggest that MCP deployments are often
> over-provisioned [15, 21].

Why it works:

- **The term is defined in its first appearance**, in a subordinate clause, and
  never re-defined.
- **The second sentence removes the reader's likely assumption** (that this is
  an attacker story) before it can take hold.
- **The third sentence is concrete about a human**, not an abstraction —
  *describes a task imprecisely*, *delegates a broader goal*. A reader
  recognises themselves.
- **The evidence sentence is hedged to match its evidence**: "studies suggest",
  "often". Two citations do not establish a universal, and the sentence does
  not pretend they do.

### 9.3 Hedging calibration

The most common failure in a draft is a claim pitched one notch stronger than
its evidence. Match the register to what you actually have.

| You have | Write | Not |
|---|---|---|
| A systematic review | "most work" | — |
| Four representative citations | "much recent work" | "most work" |
| Two measurement studies | "studies suggest … are often" | "deployments are" |
| A verified absence after a deliberate search | "to the best of our knowledge, no prior work" | "no prior work" |
| A mechanism that could in principle be encoded | "does not by itself quantify" | "cannot express" |
| One measured comparison | "in our evaluation, X exceeded Y" | "X outperforms Y" |

## Sources

- arXiv:[2510.16558](https://arxiv.org/abs/2510.16558) — DSN 2026
- arXiv:[2502.09861](https://arxiv.org/abs/2502.09861) — AAMAS 2025
- arXiv:[2512.06781](https://arxiv.org/abs/2512.06781) — ACM SAC 2026

Quotations are single sentences reproduced for structural analysis; read the
full introductions at the links above.
