# Research Proposal

M.Sc. research proposal on the MCP Security risk-scoring framework (`McpRisk`),
written in the official Ben-Gurion University thesis template (1.5 line spacing;
switch `\onehalfspacing` to `\doublespacing` in `main.tex` for the final thesis).

- **Title:** Defending MCP Servers from Agents: A Static and Dynamic
  Risk-Scoring Framework for the Model Context Protocol
- **Author:** Tomer Ovadya
- **Supervisor:** Prof. Asaf Shabtai
- **Institution:** Ben-Gurion University of the Negev, Department of Computer
  Science

## Building

Requires a LaTeX distribution (MiKTeX or TeX Live) with `latexmk`. The document
uses `babel` with Hebrew for the mandatory bilingual cover/abstract pages.

```bash
latexmk -pdf main.tex     # produces main.pdf
latexmk -c                # clean auxiliary files
```

## Layout

| Path | Contents |
|------|----------|
| `main.tex` | Master file: preamble, title/author metadata, chapter includes |
| `Main_pages/` | Cover, title, and abstract pages (English + Hebrew) |
| `content/introduction/` | Chapter 1 — Introduction (motivation, problem, objectives) |
| `content/related_work/` | Chapter 2 — Background and Related Work (five strands) |
| `content/framework/` | Chapter 3 — Proposed Approach: the McpRisk Framework |
| `content/experiments/` | Chapter 4 — Preliminary Results |
| `content/discussion_and_conclusions/` | Chapter 5 — Research Plan and Expected Contributions |
| `content/appendixs/` | (unused; retained for reference) |
| `bibliography/thesis.bib` | 40 verified references (arXiv IDs / DOIs checked) |

## Notes

- This is a **research proposal**: it presents the proposed approach and
  preliminary results, then a research plan (work packages, timeline, expected
  contributions) for the remaining work. It uses 1.5 line spacing; the body
  (Chapters 1–5) is ~24 pages, ~44 pages total including front matter, the
  bilingual Hebrew pages, and the bibliography.
- All experimental numbers are drawn from the framework's own evaluation reports
  under `../reports/`. All 40 citations are real, verified works — sourced from
  the local Zotero library, recent arXiv releases, snowball sampling of anchor
  papers' references, and confirmed Anthropic/OWASP primary sources.
