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

| Part | State |
|---|---|
| Literature review (53 papers + 11 primary/industry/standards sources) | Done — [`literature-review.md`](literature-review.md), [`refs.bib`](refs.bib) |
| AAMAS 2027 rules | Done — [`AAMAS-2027-RULES.md`](AAMAS-2027-RULES.md) |
| Writing guide (length + narrative) | Done — [`WRITING-GUIDE.md`](WRITING-GUIDE.md) |
| Introduction guide (moves + 3 worked examples) | Done — [`INTRODUCTION-GUIDE.md`](INTRODUCTION-GUIDE.md) |
| **1.1 Vision and Scope** | **Written** — 273 words, 3 paragraphs, 6 citations |
| 1.2 The Gap in Existing Work | Stub (~250 words) |
| 1.3 Contributions | Stub (~200 words) — write LAST, from the evaluation |
| §2 onward | Not started (`\input` lines commented out in `main.tex`) |

**The Introduction uses numbered subsections** (1.1/1.2/1.3), following
arXiv:2603.26635 (AAMAS 2026). Five of the six sampled papers write it flat
instead — evidence table in `WRITING-GUIDE.md` §3, and the revert recipe is in
the comment block at the end of `sections/01-introduction.tex`.

**Expected in the PDF:** three `??` marks where the contributions list
references sections 3–5, which do not exist yet. They resolve automatically once
those sections carry their labels. Not a build error.

Stubs render in the PDF as grey `[To be written: …]` markers via the `\stub`
macro in `main.tex`, so nothing ships blank by accident. Delete the macro once
the skeleton is filled.

Current build: 3 pages (1 page of body, 2 of bibliography — `\nocite{*}` is on
while drafting).

## Layout

| Path | Contents |
|---|---|
| `main.tex` | acmart/sigconf preamble, AAMAS 2027 block, CCS concepts, title, section includes, bibliography |
| `sections/01-introduction.tex` | Section 1 — three subsections; 1.1 written, 1.2/1.3 stubbed |
| `refs.bib` | 64 BibTeX entries in thirteen strands, IDs verified against the arXiv API 2026-07-30 |
| `AAMAS-2027-RULES.md` | Every binding rule: length, format, anonymity, desk rejection, review criteria, Findings track, AI policy |
| `WRITING-GUIDE.md` | **Start here when writing.** The story through-line and reader-question chain, page/word budgets per section, what accepted AAMAS papers actually do, revision order |
| `INTRODUCTION-GUIDE.md` | The five moves an introduction must make, plus three worked examples dissected paragraph by paragraph (DSN 2026 MCP paper, AAMAS 2025, ACM SAC 2026) |
| `literature-review.md` | Per-paper relevance notes, strand rationale, local PDF paths, catalog corrections, gap statement |
| `paper_v5_overleaf.zip` | Upload-ready archive |

## Overleaf

Upload `paper_v5_overleaf.zip` via **New Project → Upload Project**. Then:

- Compiler: **pdfLaTeX**
- Main document: **main.tex**

`acmart.cls` and `ACM-Reference-Format.bst` ship with Overleaf's TeX Live;
BibTeX runs automatically. Re-zip after local edits with:

```bash
cd ~/MCP/paper_v5 && rm -f paper_v5_overleaf.zip && \
  zip -r paper_v5_overleaf.zip main.tex sections refs.bib
```

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

Section 1.1 cites only published literature. Experimental figures (56 assets,
100% within-one-tier, MAE 0.10–0.125, ladder answering 55/55 tools) come from
[`../reports/experiments/v5/README.md`](../reports/experiments/v5/README.md)
and its `EVALUATION.md`; they are **not** yet used in this draft and belong in
§1.3 and the evaluation section.

## Related

- Experiment: [`../reports/experiments/v5/`](../reports/experiments/v5/)
- Policy document under test: [`../docs/mcp-tools/server-policies.md`](../docs/mcp-tools/server-policies.md)
- Held-out ground truth: [`../docs/mcp-tools/server-profiles.md`](../docs/mcp-tools/server-profiles.md)
- Earlier write-ups (not modified): [`../paper/`](../paper/), [`../thesis/`](../thesis/)
- Local PDF corpus: [`../Literature_review/pdf/`](../Literature_review/pdf/)
- Slide decks the references were drawn from: [`../presentations/slides/`](../presentations/slides/)
