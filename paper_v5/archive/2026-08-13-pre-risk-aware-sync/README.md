# paper_v5 — Policy-Grade Static Severity Scoring for MCP Servers

Standalone LaTeX project for the paper written around the **v5 experiment**
(`../reports/experiments/v5/`), in which the scanner is given only a server's
captured tool catalog and the organization's classification *policy* — no
per-asset sensitivity numbers — and must derive the severities the organization
would have assigned.

Formatted for **AAMAS 2027** — the 26th International Conference on Autonomous
Agents and Multiagent Systems, 3–7 May 2027, JW Marriott Hotel, Hanoi, Vietnam.
Submission deadline listed as *early October 2026 (TBC)*.

Self-contained: nothing here depends on `../paper/` or `../thesis/`.

## Status

Synced from Overleaf on **2026-08-11** (`paper_v5_overleaf (1).zip`, exported
2026-08-10). The Overleaf project is the source of truth, and it keeps the body
text **inline in `main.tex`** rather than in `sections/*.tex` — the local layout
now matches that. The pre-sync split-file lineage (2026-08-04) is preserved
under [`archive/`](archive/README.md).

| Part | State |
|---|---|
| Literature review (53 papers + 11 primary/industry/standards sources) | Done — [`literature-review.md`](literature-review.md), [`refs.bib`](refs.bib) |
| AAMAS 2027 rules | Done — [`AAMAS-2027-RULES.md`](AAMAS-2027-RULES.md) |
| Writing guide (length + narrative) | Done — [`WRITING-GUIDE.md`](WRITING-GUIDE.md) |
| Introduction guide (moves + 3 worked examples) | Done — [`INTRODUCTION-GUIDE.md`](INTRODUCTION-GUIDE.md) |
| §1 Introduction | **Written** — flat, no subsections |
| §2 Related Work | **Written** |
| §3 Problem Setting and Threat Model | **Written** |
| §4 The Framework | **Written** — 7 subsections (overview, sensitivity, impact ladder, hand-off, blast radius, dynamic layer, enforcement) |
| §5 Evaluation | **Not in Overleaf.** A 2026-08-04 draft survives at [`sections/05-evaluation.tex`](sections/05-evaluation.tex); it is not `\input` by `main.tex` |
| §6 Discussion, §7 Conclusion | Not started |

The title changed in this sync, from *From Organizational Policy to Runtime
Risk: Consequence-Aware Access Control for MCP Servers* to **Deriving
Design-Time Risk Severity for Model Context Protocol Servers from
Organizational Policy Alone**.

**Expected in the PDF:** seven `??` marks from `\ref{sec:eval}` — §5 does not
exist yet. Not a build error. One further `??` at §4.7 is a real inconsistency,
see *Open issues* below.

Current build: **7 pages** (5 of body, 2 of bibliography — `\nocite{*}` is on
while drafting). `\stub` is still defined in `main.tex` but no longer used.

## Open issues

1. **`\ref{eq:decision}` is dangling.** §4.7 Enforcement opens with
   "Enforcement instantiates Eq.~\ref{eq:decision}", but the rewritten §3 no
   longer defines that equation — the `allow`/`review`/`deny` gate on
   thresholds `θ_r ≤ θ_d` was dropped. The new §3 also states the opposite
   position ("our work reports this score but does not decide whether a call
   should be allowed, reviewed, or blocked"), so §3 and §4.7 now disagree.
   Either restore the equation in §3 (it is intact at
   `archive/2026-08-04-pre-overleaf-sync/sections/03-threat-model.tex`, line
   109) or rewrite §4.7 to stop claiming an enforcement decision.
2. **`asset` vs `resource` terminology.** The paper standardized on
   "resource" / "the register", but three sentences still say "asset":
   `main.tex` lines 261 ("fully labeled asset inventory"), 420 and 423 ("owns
   the connected assets", "maps it to the relevant asset"). One sweep would
   make it uniform. `sections/05-evaluation.tex` has one more.
3. **Evaluation section.** §5 is referenced seven times and does not exist in
   the Overleaf project.

## Layout

| Path | Contents |
|---|---|
| `main.tex` | Everything: acmart/sigconf preamble, AAMAS 2027 block, CCS concepts, title, **§1–§4 inline**, bibliography |
| `sections/05-evaluation.tex` | 2026-08-04 evaluation draft, **not** `\input` by `main.tex` and not in Overleaf |
| `refs.bib` | 62 BibTeX entries; 46 cited, 17 unused. IDs verified against the arXiv API 2026-07-30 |
| `archive/` | Pre-sync lineage — see [`archive/README.md`](archive/README.md) |
| `AAMAS-2027-RULES.md` | Every binding rule: length, format, anonymity, desk rejection, review criteria, Findings track, AI policy |
| `WRITING-GUIDE.md` | **Start here when writing.** The story through-line and reader-question chain, page/word budgets per section, what accepted AAMAS papers actually do, revision order |
| `INTRODUCTION-GUIDE.md` | The five moves an introduction must make, plus three worked examples dissected paragraph by paragraph (DSN 2026 MCP paper, AAMAS 2025, ACM SAC 2026) |
| `literature-review.md` | Per-paper relevance notes, strand rationale, local PDF paths, catalog corrections, gap statement |
| `paper_v5_overleaf.zip` | Upload-ready archive, regenerated 2026-08-11 from the synced files |

## Overleaf

The Overleaf project is the source of truth. Export from it with **Menu →
Download → Source**, then re-sync this folder from the zip rather than editing
both sides.

To seed a new project, upload `paper_v5_overleaf.zip` via **New Project →
Upload Project**. Then:

- Compiler: **pdfLaTeX**
- Main document: **main.tex**

`acmart.cls` and `ACM-Reference-Format.bst` ship with Overleaf's TeX Live;
BibTeX runs automatically. Re-zip after local edits with:

```bash
cd ~/MCP/paper_v5 && rm -f paper_v5_overleaf.zip && \
  zip -r paper_v5_overleaf.zip main.tex refs.bib
```

Uploading a re-zipped bundle **overwrites** the Overleaf project. Pull the
Overleaf source down first if it has moved on.

## Two AAMAS template gotchas

**1. `\setcopyright{ifaamas}` does not work with stock `acmart`.** The AAMAS
template prescribes it, but `ifaamas` only exists in the patched `acmart.cls`
that IFAAMAS ships inside the official AAMAS bundle. Against stock acmart it
fails with `Package xkeyval Error: value 'ifaamas' is not allowed`. This draft
uses `\setcopyright{rightsretained}`; when you drop the official bundle's
`acmart.cls` into this folder, swap the two commented lines in `main.tex`.

**2. Do not add `\usepackage{amssymb}`.** acmart's Libertine math setup already
defines `\Bbbk`, so loading amssymb on top errors out with
`Command \Bbbk already defined`. acmart already provides amsmath, booktabs,
graphicx, and xcolor.

## Submission vs camera-ready

AAMAS main-track review is double-blind. `main.tex` carries a commented
`\documentclass[sigconf, anonymous, review]{acmart}` line plus
`\settopmatter{printfolios=true}` — swap to those for submission. **Confirm the
page limit and anonymity policy against the AAMAS 2027 submission instructions
when they are published**; they were not yet up as of 2026-07-30.

## Local build

```bash
~/bin/tectonic main.tex     # or: latexmk -pdf main.tex
```

## Where the references came from

Three sources, merged and de-duplicated:

- The local corpus under `../Literature_review/pdf/` (132 PDFs), especially the
  curated `Scoring_curated/` set.
- The papers cited in `../presentations/slides/` — the 14-paper, 6-category
  scoring review in `2026-05-06_lit-review-categories.pptx` and the taxonomy
  slides in `Weekly Sync Meeting 2026-04-06 (MCP).pptx`.
- A July 2026 web sweep for work published after the corpus was assembled, plus
  the industry disclosures (Invariant Labs, OWASP MCP Top 10, Anthropic,
  Microsoft) that named several MCP attack classes first.

Every arXiv ID, DOI, and venue was re-resolved against the arXiv API on
2026-07-30. Five title errors found in the local catalog are listed under
*Corrections to the local catalog* in `literature-review.md`.

## Sources for the numbers

§1–§4 cite only published literature. Experimental figures (56 assets,
100% within-one-tier, MAE 0.10–0.125, ladder answering 55/55 tools) come from
[`../reports/experiments/v5/README.md`](../reports/experiments/v5/README.md)
and its `EVALUATION.md`; they are **not** yet used in `main.tex` and belong in
the contributions paragraph of §1 and in §5.

## Related

- Experiment: [`../reports/experiments/v5/`](../reports/experiments/v5/)
- Policy document under test: [`../docs/mcp-tools/server-policies.md`](../docs/mcp-tools/server-policies.md)
- Held-out ground truth: [`../docs/mcp-tools/server-profiles.md`](../docs/mcp-tools/server-profiles.md)
- Earlier write-ups (not modified): [`../paper/`](../paper/), [`../thesis/`](../thesis/)
- Local PDF corpus: [`../Literature_review/pdf/`](../Literature_review/pdf/)
- Slide decks the references were drawn from: [`../presentations/slides/`](../presentations/slides/)
