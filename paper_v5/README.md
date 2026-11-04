# paper_v5 — Risk-Aware MCP

Standalone LaTeX project for the paper built on the **v5 experiment**
(`../reports/experiments/v5/`), extended into a full two-stage framework: a
design-time **Static Scanner** that builds a tool--asset risk surface from a
server's captured tool catalog plus the organization's classification *policy*,
and a runtime **Dynamic Scanner** that adapts each baseline using
invocation-specific and historical evidence.

Current title: **Risk-Aware MCP: Risk Assessment for Model Context Protocol
Invocations** (Tomer Ovadya, Asaf Shabtai — BGU, SISE).

Formatted for **AAMAS 2027** — the 26th International Conference on Autonomous
Agents and Multiagent Systems, 3–7 May 2027, JW Marriott Hotel, Hanoi, Vietnam.
Submission deadline listed as *early October 2026 (TBC)*.

Self-contained: nothing here depends on `../paper/` or `../thesis/`.

## Status

Synced from Overleaf on **2026-08-13** from the export
`MCP_Risk_Assessment.zip`. The Overleaf project is the source of truth, and it
keeps the body text **inline in `main.tex`** — there is no longer a `sections/`
directory. The pre-sync lineage is preserved under
[`archive/`](archive/README.md).

This sync is a large one: the paper went from four written sections with seven
dangling `\ref{sec:eval}` marks to a complete draft with figures, tables, and
results.

| Part | State |
|---|---|
| §1 Introduction | **Written** — flat, no subsections |
| §2 Related Work | **Written** |
| §3 Threat Model | **Written** |
| §4 Methodology | **Written** — overview, static risk assessment (impact / sensitivity / blast radius / score), dynamic risk adaptation, risk output |
| §5 Implementation | **Written 2026-08-13** — invocation logging (JSON-RPC capture over stdio *and* HTTP), static layer, dynamic layer. See below |
| §6 Evaluation | **Written** — settings, static assessment, dynamic assessment, additional properties |
| §7 Preliminary Results | **Written** — static results only; see *Open issues* |
| §8 Conclusion | **Written** |
| Figures | **3 architecture figures** in [`figures/`](figures/) |
| Literature review (53 papers + 11 primary/industry/standards sources) | Done — [`literature-review.md`](literature-review.md), [`refs.bib`](refs.bib) |
| AAMAS 2027 rules | Done — [`AAMAS-2027-RULES.md`](AAMAS-2027-RULES.md) |
| Writing guide (length + narrative) | Done — [`WRITING-GUIDE.md`](WRITING-GUIDE.md) |
| Introduction guide (moves + 3 worked examples) | Done — [`INTRODUCTION-GUIDE.md`](INTRODUCTION-GUIDE.md) |

The title changed again in this sync, from *Deriving Design-Time Risk Severity
for Model Context Protocol Servers from Organizational Policy Alone* to
**Risk-Aware MCP: Risk Assessment for Model Context Protocol Invocations**.
Asaf Shabtai was added as second author.

### §5 Implementation

Added 2026-08-13. Sits between the Methodology and the Evaluation: §4 stays a
description of the model, §5 carries the engineering. Three subsections, in
this order deliberately —

1. **Invocation Logging** (`sec:impl-logging`) — both layers are downstream of
   one capture. We record at the **JSON-RPC message layer, not at a
   transport**, which is what makes a single implementation cover *local*
   (stdio subprocess) and *web-hosted* (HTTP+SSE / streamable HTTP) MCP servers
   alike, with no server cooperation and no agent modification. Covers the two
   collection paths, the catalog/calls/sessions tables they normalize into, the
   two different shapes MCP servers use to report errors, and the structural
   anomalies the parser flags.
2. **Static Layer** (`sec:impl-static`) — reachability/N-A, the deterministic
   operation ladder and its evidence precedence (annotations *bound* a tier,
   verbs decide within the bound, parameters describe but do not decide), the
   classify-then-map derivation of sensitivity from policy, deterministic
   banding, and why the old LLM judge stage was removed from the scan path.
3. **Dynamic Layer** (`sec:impl-dynamic`) — the no-model-on-the-call-path
   constraint, zero-per-server-config asset resolution, and the three runtime
   factors mapped to their implementations.

Source of the description: `../src/mcp_security/` (`static_scoring/`,
`binding/`, `dynamic/`) and `../logs/proxy/` (`analysis/mitm_capture.py`,
`analysis/parse_wire.py`, `orgs_2026-07-29/mcp_live.py`).

**One deliberate divergence, stated in the text.** §4.3 defines the runtime
factors as continuous multipliers, $L(c)=D\,A\,N$ with each factor in $[1,2]$.
The implementation realizes them over the four discrete reporting bands: each
signal proposes a band, the verdict is the most severe proposal. §5.3 says so
explicitly and argues the property that matters — bounded below, so familiar
behavior can never drop a call under its static floor — is preserved. If a
reviewer would rather see one formalism, §4.3 is the half to change.

### Build

Clean: **zero undefined references and zero undefined citations**.

**11 pages**: **~9 of body** (§8 Conclusion opens on p.9) plus 2 of references.

⚠️ **This now exceeds the AAMAS limit.** 8 body pages are allowed, references
free — so the body is roughly one page over. §5 Implementation accounts for
~1.5 pages of that; the draft was at ~7 body pages before it. Something has to
give before submission: trim §5, trim elsewhere, or move part of §5 to an
appendix (AAMAS allows unlimited appendix pages, but nothing load-bearing may
live there).

Also fixed in this pass: a stray markdown fence (```` ```latex ````) at the top
of §4.3 that was typesetting as literal `‘‘‘latex` in the PDF.

Overfull `\hbox` warnings remain, the widest in the §7 results tables.
Cosmetic, but visible in the PDF.

### Reported numbers

| Quantity | Value |
|---|---|
| Deployments scanned | 16, from 9 distinct MCP tool catalogs |
| Tools | 262 total (151 distinct) |
| Registered assets | 221 |
| Candidate tool--asset cells | 3,615 |
| Scored / not-applicable | 1,182 (33%) / 2,433 (67%) |
| Bands over the scored surface | 444 Low, 458 Medium, 242 High, 38 Critical |
| High+Critical share | ~24% of scored, 7.7% of the full matrix |
| Deterministic impact assignment | 127 of 151 distinct tools (84%); 24 needed semantic analysis |
| Live invocations collected | 3,000 across GitHub, Slack, and Calendar |

## Open issues

1. **Over the page limit** — see *Build* above. This is the blocking one.
2. **The dynamic layer is claimed but not reported.** The abstract and §8
   both state that 3,000 live invocations were collected across GitHub, Slack,
   and Calendar, but §7 opens with "Currently, we report only the results of
   the Static Scanner." §6.3 defers the real dynamic assessment to "subsequent
   evaluation." A reviewer will read the abstract as promising runtime results
   the paper does not deliver — either report something from the 3,000
   invocations or soften the abstract.
3. **§6.4 promises two measurements that §7 never reports.** *Computational
   Cost* (LLM cost to build a server's matrix) and *Runtime Latency*
   (per-invocation scoring overhead) are both set up as evaluation criteria
   and then never answered. §5.3 now states that both layers record per-stage
   timings, which is where those numbers would come from.
4. **Overfull hboxes in the §7 tables** — see *Build* above.

The three open issues from the previous sync are all **resolved**: §5 exists,
`\ref{eq:decision}` is gone, and the terminology is now uniform on "asset"
(105 uses, zero "resource" / "the register").

## Layout

| Path | Contents |
|---|---|
| `main.tex` | Everything: acmart/sigconf preamble, AAMAS 2027 block, CCS concepts, title, **§1–§7 inline**, bibliography |
| `figures/` | Three PNG architecture figures: overall methodology, Static Scanner, Dynamic Scanner |
| `refs.bib` | 65 BibTeX entries; 40 cited. IDs verified against the arXiv API 2026-07-30 |
| `archive/` | Pre-sync lineage — see [`archive/README.md`](archive/README.md) |
| `MCP_Risk_Assessment.zip` | The 2026-08-13 Overleaf export this folder was synced from |
| `paper_v5_overleaf.zip` | Upload-ready archive, regenerated 2026-08-13 (now includes `figures/`) |
| `AAMAS-2027-RULES.md` | Every binding rule: length, format, anonymity, desk rejection, review criteria, Findings track, AI policy |
| `WRITING-GUIDE.md` | **Start here when writing.** The story through-line and reader-question chain, page/word budgets per section, what accepted AAMAS papers actually do, revision order |
| `INTRODUCTION-GUIDE.md` | The five moves an introduction must make, plus three worked examples dissected paragraph by paragraph (DSN 2026 MCP paper, AAMAS 2025, ACM SAC 2026) |
| `literature-review.md` | Per-paper relevance notes, strand rationale, local PDF paths, catalog corrections, gap statement |
| `GROUND-TRUTH.md` | Held-out severities the static arm is measured against |
| `DYNAMIC-LAYER-V4-NOTES.md` | How to write the dynamic layer (behaviour multiplier, design v4) into §4.3: the names to use (three groups: Typical Cadence, Typical Footprint, Red Flags; fifteen dimensions; the mechanisms), $s_1$/$s_2$ and the full formula, how to argue the max, the missing-handshake paragraph, paste-ready LaTeX with a dimensions table, and two verified BibTeX entries. `main.tex` not touched |

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
  zip -r paper_v5_overleaf.zip main.tex refs.bib figures
```

The `figures/` directory is now load-bearing — a bundle without it will not
compile.

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

§1–§4 cite only published literature. The experimental figures in §6 come from
the scan corpus under
[`../reports/experiments/v5/`](../reports/experiments/v5/); the 3,000 live
invocations come from the provisioned GitHub, Slack, and Calendar deployments.

## Related

- Experiment: [`../reports/experiments/v5/`](../reports/experiments/v5/)
- Policy document under test: [`../docs/mcp-tools/server-policies.md`](../docs/mcp-tools/server-policies.md)
- Held-out ground truth: [`../docs/mcp-tools/server-profiles.md`](../docs/mcp-tools/server-profiles.md)
- Earlier write-ups (not modified): [`../paper/`](../paper/), [`../thesis/`](../thesis/)
- Local PDF corpus: [`../Literature_review/pdf/`](../Literature_review/pdf/)
- Slide decks the references were drawn from: [`../presentations/slides/`](../presentations/slides/)
