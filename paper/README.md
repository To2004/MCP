# Paper

Conference-style write-up of the MCP risk-scoring framework.

- `main.tex` — the paper source (IEEE `conference` two-column format, ~5 pages).
- `refs.bib` — BibTeX references (copied from `Literature_review/latex/bib.bib`); every citation resolves here.
- `main.pdf` — compiled output.

## Build

Compiled with [Tectonic](https://tectonic-typesetting.github.io/) (self-contained LaTeX engine, fetches packages on first run):

```bash
tectonic main.tex
```

`bibtex`/`biber` runs automatically; no separate pass is needed.

## Structure

Threat model (server as protected asset) → related work (binary-defense gap) →
`Impact × Likelihood × Irreversibility` risk model → static + dynamic two-mode
design → evaluation against held-out design-time tables and an independent human
oracle (93% tool-impact agreement; 89% within-one-band vs. the oracle).
