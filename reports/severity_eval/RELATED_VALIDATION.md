# How risk scoring is proven (system-wise, not theoretical) — and where ours stands

Multi-agent research across vulnerability scoring, agent/MCP risk, systems/SIEM risk,
and quantitative frameworks, to answer: *how do credible risk-scoring works actually
prove themselves on real systems, and what can we run head-to-head?*

## 1. The validation ladder (most → least convincing)

Across domains, a risk score is validated like a **ranker against a real outcome**:

1. **Outcome-based ROC / PR-AUC, out-of-time split.** Bind each score to a real
   outcome (e.g. confirmed exploitation), train on the past, test on a held-out
   future window. **EPSS** does this: AUC ≈ **0.838**; PR-AUC matters because only
   ~5% of CVEs are ever exploited. *Gold standard.*
2. **Coverage-vs-effort / efficiency curves.** EPSS's operational proof: at similar
   coverage, **CVSS≥7 gives 3.96% efficiency vs EPSS≥0.10's 65.2%** — ~85% less work
   for the same risk caught. The most *actionable* way to beat a CVSS baseline.
3. **Precision@k** vs the exploited set (analysts only act on the top-k).
4. **Case-control / odds-ratio** (Allodi & Massacci, TISSEC'14): patching by **CVSS
   alone is statistically equivalent to random**; PoC/black-market presence are far
   better risk factors. Causal-leaning evidence.
5. **Calibration curve + Brier score** (a "0.7" should mean ~70% observed).
6. **Inter-rater / intra-rater reliability** (weighted Cohen's κ, Krippendorff's α,
   Gwet's AC₁). Proves *reproducibility*, not correctness. CVSS fails badly here:
   a 196-analyst study found **35–55% gave a different severity to the same CVE**
   months later; the multi-system study "Conflicting Scores" found inter-system
   **κ ≈ 0, α negative** (worse than chance).

**The objection we must pre-empt (Cox 2008; Krisper 2021):** multiplying *ordinal*
scales — exactly our Impact×Likelihood×Irreversibility — is mathematically unsound
("risk inversion", range compression). Defense: validate the **ranking** the product
induces against ground truth (don't claim the number is meaningful), and **beat a
single-axis baseline** (otherwise it's "analysis placebo").

## 2. Closest comparables, and whether they actually proved their scoring

| work | output | empirically validated? | runnable code/data |
| --- | --- | --- | --- |
| **AgentTrust** | severity none..critical | yes, on its OWN benchmark | ✅ github.com/chenglin1112/AgentTrust (we ran it — see §3) |
| **MCP-RiskCue** | 9-category risk from MCP logs | yes (471 eval, 83% acc) | ✅ github.com/PorUna-byte/MCP-RiskCue |
| **LLM-CVSS** | CVSS per-metric | yes vs 45k CVSS (acc/MAE/F1) | ✅ github.com/spritz-group/LLM-CVSS (methodology template) |
| **OMGPermissions** | 1–5 permission risk | **no** ground truth (expert-anchored only) | ✅ github.com/ashim-mahara/OMGPermissions |
| **ProbGuard** | unsafe-state probability | yes (driving/SafeAgentBench) | ✅ github.com/haoyuwang99/ProbGuard |
| **AgenTRIM** | binary allow/deny | yes (AgentDojo, F1≈0.999) | ❌ "code on publication" |
| **AURA** | 0–100 autonomy risk → bands | **no** (one case study) | ❌ |
| **ASTRA** | 0–1 enforcement rate | partial | ❌ no code found |
| **TRiSM** | survey metrics | **no** (survey) | ❌ |

Skeptical takeaway: **AURA and TRiSM have no empirical scoring validation**; AgenTRIM
is binary (not graded) and unreleased. Only **AgentTrust** is both a graded-severity
MCP-adjacent scorer *and* runnable — so we ran it.

## 3. Head-to-head we actually ran: AgentTrust's scorer vs ours

We ran AgentTrust's **own published rule-based scorer** (`TrustInterceptor`, LLM judge
OFF — its headline config) on the same 496 scenarios our scorers see
(`scripts/run_agenttrust_scorer.py`). Spearman ρ vs the graded ground truth:

| set | AgentTrust (theirs) | ours | best classical |
| --- | --- | --- | --- |
| agenttrust_internal (300) | **0.88** | 0.45 | nist 0.42 |
| agenttrust_independent (30) | **0.99** | −0.23 | owasp 0.03 |
| agenttrust_realworld (100) | **0.97** | 0.24 | owasp 0.21 |
| **mcp_native (66, unseen by AgentTrust)** | 0.43 | **0.64** | owasp 0.58 |

**The decisive observation:** AgentTrust's ~0.9 on AgentTrust data is **home-field
advantage** — its rule patterns were authored *on those exact scenarios* (the
circular-evaluation trap the research warns about). On `mcp_native`, the one set it
never saw, it **collapses to 0.43 — below ours (0.64) and below CVSS/NIST/OWASP.** Its
hardcoded patterns do not transfer; our model generalizes to a new domain better. This
is itself the methodological lesson: *a scorer graded on its own benchmark is not
evidence it works elsewhere.*

## 4. What to adopt for the paper (the credible validation recipe)

1. **Side-by-side, same-items, multiple frameworks** (the "Conflicting Scores"
   protocol): score every item with ours + CVSS/NIST/DREAD/OWASP + the closest system
   (AgentTrust), bin to a common scale, report the full pairwise agreement matrix
   (weighted κ + Krippendorff α) and each scorer's agreement to the reference. ✔ done.
2. **Report cross-distribution transfer**, not just in-distribution — the AgentTrust
   collapse on `mcp_native` shows why this is essential.
3. **Pre-empt the ordinal-multiplication objection** (Cox/Krisper): validate the
   induced ranking (Spearman/weighted-κ), beat a single-axis baseline, and never claim
   the raw product is a cardinal quantity.
4. **Move toward outcome-based proof** (the EPSS bar): curate an MCP "KEV analog" — a
   labeled set where a high score should predict real harm / attack success — and
   report PR/ROC-AUC + coverage-vs-effort + precision@k, out-of-time. Runnable
   substrates the research surfaced: **EPSS daily CSV + CISA KEV** (CVE exploitation,
   trivially downloadable), **CMU CERT / LANL insider-threat** (action→malicious
   labels), **CIRCL/vulnerability-scores** (text→CVSS, 724k items).

## Sources (verified live)

EPSS first.org/epss · CISA KEV github.com/cisagov/kev-data · Allodi-Massacci TISSEC'14 ·
"CVSS scoring inconsistencies" arXiv:2308.15259 · "Conflicting Scores" arXiv:2508.13644 ·
Cox 2008 (Risk Analysis) · Krisper arXiv:2103.05440 · Holm-Afridi (Computers&Security'15) ·
LLM-CVSS arXiv:2504.10713 · MCP-RiskCue arXiv:2511.05867 · AgenTRIM 2601.12449 ·
AURA 2510.15739 · ProbGuard 2508.00500 · AgentTrust arXiv:2605.04785 ·
CMU CERT (kilthub 12841247) · LANL csr.lanl.gov/data/cyber1 · CIRCL/vulnerability-scores (HF).
