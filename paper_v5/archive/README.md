# archive/

Superseded drafts of the paper_v5 LaTeX project. Nothing here is compiled; keep
it for provenance and for text that was cut but may come back.

## 2026-08-13-pre-risk-aware-sync/

The state `~/MCP/paper_v5` held before the 2026-08-13 sync from the Overleaf
export `MCP_Risk_Assessment.zip`. That sync renamed the paper to *Risk-Aware
MCP: Risk Assessment for Model Context Protocol Invocations*, added Asaf
Shabtai as second author, added §3 Threat Model / §5 Evaluation / §6
Preliminary Results / §7 Conclusion, and added the three `figures/`
architecture PNGs.

| Path | Note |
|---|---|
| `main.tex` | Old title (*Deriving Design-Time Risk Severity … from Organizational Policy Alone*), single author, §1–§4 only, `\input{sections/05-evaluation}` at the end |
| `refs.bib` | 67 entries. **Only place `tukey1977eda` (Tukey's fences, the dynamic escalation bins) and `first2019cvss31` are defined** — both dropped in the 2026-08-13 export, which cites neither |
| `README.md` | Pre-sync project README, including the three open issues that sync resolved |
| `paper_v5_overleaf.zip` | Pre-sync upload bundle — `main.tex` + `refs.bib` only, no `figures/` |
| `sections/04-framework-outline.tex` | Framework outline; superseded by §4 Methodology inline |
| `sections/05-evaluation.tex` | The 2026-08-04 evaluation draft, the last file still `\input` by the old `main.tex`. Superseded by §5 Evaluation inline. Kept because the inline §5 is much shorter and this draft holds cut material |

With this sync the live project has **no `sections/` directory at all** — the
Overleaf source is one self-contained `main.tex`.

## 2026-08-04-pre-overleaf-sync/

The split-file lineage that `~/MCP/paper_v5` held before the 2026-08-11 sync
from the Overleaf export `paper_v5_overleaf (1).zip` (exported 2026-08-10).

| Path | Note |
|---|---|
| `main.tex` | Old title (*From Organizational Policy to Runtime Risk*), body pulled in via `\input{sections/…}` |
| `refs.bib` | Pre-sync bibliography; still contains `huang2026caller`, dropped in the Overleaf version |
| `README.md` | Pre-sync project README |
| `sections/01-introduction.tex` | Superseded by §1 inline in the live `main.tex` |
| `sections/02-related-work.tex` | Superseded by §2 inline |
| `sections/03-threat-model.tex` | Superseded by §3 inline. **Still the only place the decision equation `eq:decision` (the `allow`/`review`/`deny` gate on `θ_r ≤ θ_d`) is defined** — line 109. Nothing references it any more: the 2026-08-13 draft dropped the dangling `\ref` and takes the position that the framework reports a score rather than deciding allow/review/deny |
| `sections/04-framework.tex` | Superseded by §4 inline |

The 2026-08-04 evaluation draft was not archived here — it stayed live until
the next sync, and is now at
[`../2026-08-13-pre-risk-aware-sync/sections/05-evaluation.tex`](2026-08-13-pre-risk-aware-sync/sections/05-evaluation.tex).
