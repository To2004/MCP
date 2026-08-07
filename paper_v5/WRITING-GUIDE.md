# AAMAS 2027 Writing Guide

House rules for this paper: the conference's hard constraints, the length
budget they imply, and the structural conventions actually observed in accepted
AAMAS papers. Written 2026-07-30 after sampling six papers (five AAMAS, one
MCP) and reading the AAMAS 2027 submission instructions.

## Contents

- [0. The paper is a story](#0-the-paper-is-a-story)
- [1. Hard constraints](#1-hard-constraints)
- [2. The page budget](#2-the-page-budget)
- [3. What accepted AAMAS papers actually do](#3-what-accepted-aamas-papers-actually-do)
- [4. The Introduction](#4-the-introduction)
- [5. Word budget per section](#5-word-budget-per-section)
- [6. Citation density](#6-citation-density)
- [7. Things that eat pages](#7-things-that-eat-pages)
- [8. Pre-submission checklist](#8-pre-submission-checklist)

## 0. The paper is a story

Everything below this section is arithmetic — page counts, word budgets,
citation density. This section is the part that decides whether the paper gets
read. **A reviewer who loses the thread stops reasoning and starts scoring.**
The job of every paragraph is to keep them in the story.

### The through-line

One sentence. Everything in the paper either advances it or gets cut. Ours:

> *Design-time risk severity for an MCP server can be derived from the
> classification policy an organization actually publishes, instead of the
> per-asset inventory it never will.*

Test any paragraph against it. A paragraph on MCP's protocol history, or on
prompt-injection taxonomy, or on how good the LLM is — none of those advance
that sentence. They are interesting. They are not the story.

### The reader's question at every moment

A story works when the reader always has exactly one open question, and the
next paragraph answers it while opening the next. Write the questions out and
check the chain holds:

| After reading… | The reader is asking… | Answered by |
|---|---|---|
| ¶1 Setting | "So agents can touch real assets. And?" | ¶2 |
| ¶2 Inversion | "Fine — can't the server just check who's calling?" | ¶2's own last sentence: no, identity doesn't separate them |
| ¶2 end | "Then something must already score this. What?" | ¶3 |
| ¶3 Gap | "OK, they're all binary. So build a graded score. What's hard?" | ¶4 |
| ¶4 Missing input | "…so does deriving it from policy actually work?" | ¶5 contributions, then §5 |

If you cannot name the question a paragraph answers, the paragraph is
decoration. If two consecutive paragraphs answer the same question, merge them.
If a paragraph answers a question nobody asked yet, move it later.

### Tension and release

Every section should open with a difficulty and close with its resolution.
A paper that only reports ("we did X, then Y, then Z") reads as a lab notebook.
A paper that sets up a problem and pays it off reads as a result.

Ours has three natural tensions. Use them, and pay each one off explicitly:

1. **The inventory does not exist.** Set up in the Introduction, paid off by
   the classify-then-map derivation.
2. **Can prose really produce a number?** Set up in the framework, paid off by
   the 100% within-one-tier result.
3. **What if the model is just guessing?** Set up implicitly by the reviewer,
   paid off by the deterministic ladder answering 55/55 tools with no LLM call
   — the strongest and least expected beat in the paper. **Do not bury this.**

### Narrative debt

Any promise you make and do not keep is debt, and reviewers collect it. If the
Introduction says "we show the framework generalizes", §5 must contain
generalization. If it says "two-mode, static and dynamic", and the paper only
evaluates static, that is debt — either evaluate it or stop promising it.

Cheapest way to stay solvent: write the contributions list **last**, from what
the evaluation actually shows.

### Do not hide the failures — spend them

Where the derivation drifts (the six adjacent-tier misses) and where a stage
stays noisy (blast radius, 19–22% of cells moving) are not embarrassments to
minimise. They are the most credible passages in the paper, and AAMAS lists
*soundness* and *reproducibility* among its criteria. A paper that explains why
`account-directory` scored 5 against the organization's 4 — because the policy
register puts it next to a Restricted row — has demonstrated it understands its
own system. Narratively, an honest failure buys the reader's trust for the
claims around it.

### Concrete beats abstract, every time

"A destructive tool with irreversible impact" is abstract. `delete_file` on
`private_key.pem` is a story. One worked example, introduced early and returned
to in the framework and the evaluation, does more for comprehension than three
paragraphs of definition — and it costs fewer words. Pick one running example
and keep it.

### Sentence-level habits that keep people reading

- **One idea per sentence.** Two ideas joined by a semicolon is two sentences.
- **Front-load the point.** The claim goes first, the qualification second.
  "The ladder answered every tool; the LLM fallback never fired" beats "Although
  the design permits an LLM fallback, it was found that in practice…"
- **Cut throat-clearing.** "It is important to note that", "In this section we
  will", "As mentioned previously" — all deletable, all free words.
- **Prefer verbs to nominalizations.** "We derive" beats "The derivation is
  performed".
- **Never make the reader hold two unexplained terms at once.** Introduce
  *blast radius* or *impact ladder* one at a time, each with its example.
- **End sections on the sentence you want remembered**, not on a caveat.

### The revision pass

When the draft is over length — it will be — do this in order, not
proportionally:

1. Delete anything that does not advance the through-line sentence.
2. Delete every paragraph whose reader-question you cannot name.
3. Merge paragraphs answering the same question.
4. Convert per-paper Related Work sentences into grouped citations.
5. Only then, tighten sentences.

Steps 1–4 recover pages. Step 5 recovers lines. Most people start at 5, run out
of will, and ship a padded paper at exactly 8 pages.

## 1. Hard constraints

From the [AAMAS 2027 submission instructions](https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/instructions/):

| Rule | Value |
|---|---|
| Main-track page limit | **8 pages**, "with any number of additional pages containing bibliographic references" |
| References | **Do not count** toward the 8 |
| Review | **Double-blind** — "papers must be prepared for double-blind reviewing" |
| LaTeX | **Mandatory** |
| Style files | "Authors should not modify the style files or any of the layout parameters" |
| Typesetting tricks | Explicitly warned against: avoid "excessive use of typesetting tricks to make everything fit into 8 pages" |
| Abstract registration | One week before the paper deadline, **100–300 words**, plain text |
| OpenReview accounts | Every author, two weeks before abstract registration |
| Supplementary | Optional, single ZIP, ≤25 MB, reviewers not required to read it, must preserve anonymity |
| Deadline | Early Oct 2026 (TBC) |

Two consequences worth internalizing:

1. **8 pages is the whole paper.** Not 8 + appendix. Anything that does not fit
   goes to supplementary material that reviewers are explicitly told they need
   not read — so nothing load-bearing can live there.
2. **The "no typesetting tricks" line is enforceable.** Shrinking `\baselineskip`,
   negative `\vspace` before sections, or `\small` on body text are the standard
   desk-reject triggers. Cut words instead.

## 2. The page budget

Eight pages in `acmart` two-column ≈ **6,500–7,500 words** of body text, before
figures and tables. Each half-column figure costs roughly 150–200 words of
space; a full-width figure costs 400–500.

Working allocation for this paper:

| Section | Pages | Words |
|---|---|---|
| Abstract + title block | 0.3 | 180–250 |
| 1 Introduction | **0.75–1.0** | **650–900** |
| 2 Related Work | 0.75 | 600–700 |
| 3 Threat model + problem setup | 0.75 | 600–700 |
| 4 Framework | 2.0 | 1,400–1,700 |
| 5 Evaluation | 2.25 | 1,600–1,900 |
| 6 Discussion + limitations | 0.75 | 600–700 |
| 7 Conclusion | 0.25 | 150–250 |
| **Total** | **~8** | **~6,000–6,800** |

## 3. What accepted AAMAS papers actually do

Six papers sampled, chosen for topical proximity (agent safety, LLM agents,
MCP security) and recency:

| Paper | Venue | Intro subsections? | Intro length | Ends with contributions? |
|---|---|---|---|---|
| Deception and Communication in Autonomous MAS (2603.26635) | AAMAS 2026 | **Yes** — 1.1 Tensions in Theory, 1.2 Deception in Among Us, 1.3 Findings in Brief | ~1,300 w, 8 para | Yes |
| Learning Symbolic Task Decompositions (2502.13376) | AAMAS 2025 main | No — bold run-in headings (*Motivating example*, *Our Contributions*) | ~2,300 w, 13 para | Yes, numbered list of 3 |
| PREFINE (2605.21225) | AAMAS 2026 full | No | ~1,300 w, 6–7 para | Yes, 3 bullets |
| Beyond Self-Interest (2603.13890) | AAMAS 2026 oral | No | **~675 w, 5 para** | Yes, 3 items |
| A Scoresheet for Explainable AI (2502.09861) | AAMAS 2025 | No | ~1,300 w, 4 para | Yes, "Firstly… Secondly… Thirdly…" |
| MCP-in-SoS (2603.10194) | — (MCP baseline) | No | ~1,300 w, 8–9 para | Yes, 5 bullets |

**Findings.**

- **Five of six use no numbered subsections in the Introduction.** The flat
  Introduction is the AAMAS norm. Structure comes from bold run-in headings
  (`\textbf{Motivating example.}`) or from paragraph order alone.
- **Six of six end the Introduction with an explicit contributions list.** This
  is not optional. It is how AAMAS reviewers locate the claim.
- Typical Introduction is **650–1,400 words**. The tightest sampled (675 words,
  5 paragraphs) was an *oral* — brevity is not penalised.
- Nobody writes a "paper organization / roadmap" paragraph. Section titles do
  that job. Cut it.
- Section 2 is Related Work in four of six; two defer it until after the method.

### Decision for this paper

**Use a flat `\section{Introduction}` with no numbered subsections**, ending in
a contributions list. That is what five of six do, and it is the cheaper option
under an 8-page limit — subsection headings cost vertical space and invite the
padding that fills them.

If you want the numbered variant anyway, `2603.26635` is the precedent, and the
switch is mechanical: promote the four bold run-in headings to `\subsection`.
`main.tex` and `sections/01-introduction.tex` are written so this is a one-step
change; the commented block at the bottom of the intro file shows it.

## 4. The Introduction

**Target: 650–900 words, 5 paragraphs, ≤1 page, ending in contributions.**

The recipe below is distilled from the six sampled papers. Each paragraph does
exactly one job; if a paragraph does two, split it or cut one.

| ¶ | Job | Words | Test it must pass |
|---|---|---|---|
| 1 | **Setting.** What the technology is, at what scale, and why it now touches things that matter. | 90–130 | A reader outside MCP knows what an MCP server is by the end of it. |
| 2 | **Inversion.** The threat model, stated as a reversal of what the field assumes. | 110–150 | The words "protected asset" and "threat source" appear and are assigned. |
| 3 | **Gap.** What existing work produces and why it is the wrong shape. | 130–180 | Names ≥3 concrete competitor classes, not "prior work". |
| 4 | **The specific missing input.** The narrow, falsifiable thing this paper supplies. | 150–200 | A reviewer could disagree with it. Vague framing fails here. |
| 5 | **Contributions.** Numbered or bulleted, 3–4 items, each one a claim you evaluate. | 150–220 | Every item maps to a section, and to a number in the results. |

**Rules of thumb.**

- One idea per sentence. AAMAS reviewers read fast.
- The gap paragraph is where papers bloat. Cite in groups
  (`\cite{a,b,c}`), never one-per-clause with a sentence of gloss each.
- Do not explain the method in the Introduction. Name it and move on.
- Do not preview the numbers except in the contributions list, and there only
  as one figure each.
- No roadmap paragraph.

**What went wrong in the first draft of this paper.** §1.1 alone was 967 words
across 5 paragraphs with 32 `\cite` commands — and §1.2–1.4 were still to come,
which would have put the Introduction near 2,500 words, ~2 of 8 pages. The
whole Introduction must be what §1.1 alone was.

## 5. Word budget per section

- **Related Work** (600–700): three or four thematic paragraphs, not a list.
  Each paragraph ends with the sentence that says why that strand does not
  solve the problem. With 64 references and 700 words, most citations appear
  in groups without individual discussion — that is correct and expected.
- **Threat model** (600–700): one figure plus prose. The figure earns its space
  only if it removes 150+ words.
- **Framework** (1,400–1,700): the largest prose section. Formulas are cheap
  vertically; prose about formulas is not.
- **Evaluation** (1,600–1,900): tables dominate. Budget ~400 words of setup,
  then let each table carry a 100–150 word reading.
- **Discussion/limitations** (600–700): AAMAS reviewers reward explicit
  limitations. The two known calibration gaps belong here, stated plainly.
- **Conclusion** (150–250): three sentences and a forward pointer. Never a
  summary of every section.

## 6. Citation density

- Introduction: **15–22** `\cite` commands total. More than that and the prose
  is carrying the survey's job.
- Related Work: 35–45. This is where the 64 entries earn their keep.
- Method/Evaluation: sparse — cite only baselines, metrics, and datasets.
- Group aggressively: `\cite{a,b,c,d}` after a claim beats four separate
  sentences each introducing one paper.

## 7. Things that eat pages

| Habit | Cost | Fix |
|---|---|---|
| Roadmap paragraph | 80–120 words | Delete. Section titles do it. |
| Restating the contribution in §3 and §4 | 150–250 words | State once, in the Introduction. |
| Explaining a formula in prose after displaying it | 100+ words each | Display it, define the symbols, stop. |
| Per-paper sentences in Related Work | 400+ words | Group by strand; one gap sentence per strand. |
| Figures that repeat a table | 150–500 words of space | Pick one. |
| Wide tables forced with `\resizebox` | Illegible + reads as a trick | Cut columns. |
| `\subsection` inside the Introduction | ~25 words of space each, plus the padding they invite | Bold run-in headings. |

## 8. Pre-submission checklist

- [ ] Body ≤ 8 pages; references start on page 9 or later
- [ ] `\documentclass[sigconf, anonymous, review]{acmart}` and
      `\settopmatter{printfolios=true}` for the double-blind submission
- [ ] No self-identifying text: acknowledgements removed, repo URLs anonymised,
      "our previous work" phrased in the third person
- [ ] Abstract 100–300 words, registered one week before the paper deadline
- [ ] All authors have OpenReview accounts (two weeks before abstract deadline)
- [ ] `\nocite{*}` **removed** from `main.tex` — it is a drafting aid only
- [ ] `\stub` macro and all its uses removed
- [ ] No modified layout parameters, no `\vspace` hacks, no `\small` body text
- [ ] Every contribution in the Introduction maps to a section and a result
- [ ] Limitations stated explicitly, not buried
- [ ] Supplementary (if any) is a single ZIP ≤25 MB, anonymised, and nothing
      load-bearing lives in it

## Sources

- [AAMAS 2027 submission instructions](https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/instructions/)
- [AAMAS 2027 conference site](https://warwick.ac.uk/fac/sci/dcs/aamas2027/)
- Papers sampled: arXiv [2603.26635](https://arxiv.org/abs/2603.26635),
  [2502.13376](https://arxiv.org/abs/2502.13376),
  [2605.21225](https://arxiv.org/abs/2605.21225),
  [2603.13890](https://arxiv.org/abs/2603.13890),
  [2502.09861](https://arxiv.org/abs/2502.09861),
  [2603.10194](https://arxiv.org/abs/2603.10194)
