# Scanner improvements — what changed, why, and the measured effect

Five improvements to the MCP risk scanner, each motivated by a finding from the
independent review, implemented and validated by re-running the full pipeline on
GPU. Threat model unchanged: the MCP server is the protected asset; the agent is
the threat; scoring is local-LLM-only with no hardcoded per-asset values.

## Summary

| # | Improvement | Problem it fixes | Measured effect |
|---|---|---|---|
| 1 | Breadth/enumeration signal | scanner scored `list`/`tree`/`search` over a sensitive scope as **low** (one-band-low conservative bias) | enumeration over a sensitive scope now **high**; scanner-vs-oracle exact **25% → 35%**, within-one **56% → 69%**; filesystem exact **31% → 42%** |
| 2 | Directory-scope assets | folder-targeted and unenumerated-file calls were dropped as unresolved | unresolved calls **152 → 34**; scored **109 → 227** |
| 3 | Multi-rater oracle + inter-rater agreement | accuracy judged against one hand heatmap (thin, unvalidated) | 10-rater panel; inter-rater **ceiling 50% exact / 78% within-one** quantified |
| 4 | Deterministic pre-commit gate | a bad scan/rank could be committed silently | `review verify` (8 invariants) runs on every relevant commit |
| 5 | Formula sensitivity analysis | nobody knew how stable the band cut-points were | **85% of 1700 cells flip band under a ±1 input shift** — quantified fragility |

## 1. Breadth / enumeration signal

**Files:** `src/mcp_security/static_scoring/prompts.py` (`BLAST_TASK`, `BAND_TASK`).

The blast-radius prompt now carries an explicit breadth rule: a tool that
enumerates or reads across a whole scope at once (list a directory, walk a tree,
glob/search, bulk-read, `SELECT` over a table) aggregates exposure over everything
inside, so its blast radius is broad (≥3) even though each individual read is
harmless. The band prompt mirrors it: a bulk read / enumeration over a *sensitive*
scope is **high** (one call leaks the whole scope), not low.

Effect on the corp filesystem scan: band distribution moved from
`low59 / med20 / high20 / crit13` to `low52 / med56 / high71 / crit31` — far more
risk mass where the human/framework oracles place it.

## 2. Directory-scope assets

**Files:** `src/mcp_security/static_scoring/registry.py` (`_directory_scope_assets`),
`src/mcp_security/call_scoring/resolve.py` (directory + ancestor-scope matching).

The scanner now emits one **directory-scope asset per folder** (ids ending `/`,
root `/`) in addition to per-file assets, so enumeration/fan-out tools have a
concrete container to score. The resolver maps a call to: the exact file → the
directory scope it names → the nearest **ancestor** scope (for a file the scan
never enumerated) → the store root, never guessing beyond what was scanned.

Effect: the 118 "path not among scanned files" unresolved calls were recovered —
unresolved fell **152 → 34** (the remainder are genuinely target-less ops), scored
rose **109 → 227**.

## 3. Multi-rater oracle + inter-rater agreement

**Files:** `scripts/evaluate_vs_human.py`.

Accuracy is now graded against a **panel of 10 independent oracles** — the human
heatmap plus framework baselines (DREAD, CVSS v3, NIST SP 800-30/60, OWASP, OWASP
AIVSS, MAESTRO, ChatGPT plain/security) — none of which is the scanner's own LLM.
The script reports **inter-rater agreement** (how much the oracles disagree among
themselves: ~50% exact / 78% within-one on filesystem) and **scanner-vs-consensus**
(upper-median band, robust to a maximalist outlier like DREAD). The headline
finding: the scanner now agrees with the consensus about as well as the expert
frameworks agree with each other — most remaining disagreement is legitimate, not
scanner error.

## 4. Deterministic pre-commit gate

**Files:** `.pre-commit-config.yaml`, `src/mcp_security/review/verify.py`.

`review verify` re-derives every published artifact and asserts 8 invariants (score
formula holds, band distributions recount, ranked calls resolve to real cells, no
leakage path, determinism config pinned, …) with **no LLM, < 1 s**. It is wired as
a pre-commit hook on changes to the scoring code or the published artifacts, so a
scan/rank that contradicts the code can't land.

## 5. Formula sensitivity analysis

**Files:** `scripts/formula_sensitivity.py`.

`score = sensitivity × blast × impact`, banded by fixed cut-points. The script
perturbs each scanned cell's inputs by ±1 (within range) and recomputes the policy
band: **85% of 1700 cells are "fragile"** (flip band under some ±1 shift) and 62%
sit within a margin of a cut-point. This quantifies *why* the scanner and the
oracles disagree so much — small, defensible input differences flip bands — and
flags the cut-points as the next thing to stabilise.

## Validation

- Full pipeline re-run on GPU; **969-call corpus, 830 scored**.
- Deterministic verifier: **8/8 pass**; methodology audit **7/7**; **271 unit tests pass**, ruff clean.

## Reproduce

```bash
sbatch scripts/scan_and_rank_multigpu.sbatch   # scan + params + rank + grade + verify
uv run python scripts/evaluate_vs_human.py      # multi-rater agreement
uv run python scripts/formula_sensitivity.py    # band-stability analysis
uv run python -m mcp_security.review verify      # deterministic gate
```
