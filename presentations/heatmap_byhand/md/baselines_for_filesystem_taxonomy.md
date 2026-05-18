# Baselines for the Filesystem-MCP Risk-Ranking Taxonomy

The hand-built spreadsheet `risk_ranking_filesystemMCP.xlsx` scores every
`(Directory × Filetype × Tool)` cell on an ordinal **Low / Medium / High /
Critical** scale, with eight tool axes (`read_file`, `write_file`,
`edit_file`, `create_dir`, `list_dir`, `move_file`, `search`,
`get_file_info`), 12 filetypes (`.sys`, `.exe`, `.bash`, `.code`, `.sql`,
`.xlsx`, `.docx`, `.pdf`, `.csv`, `.md`, `.png`, `.txt`), and 8 directory
classes (Sensitive Docs, Security Evidence, Source Code, QA Test Plans,
Shared Project Dir, Eval Data, Onboarding, Public). This document collects
the prior-art baselines that justify each design choice and ground the
taxonomy in established literature.

The spreadsheet already names five standards as anchors —
**NIST SP 800-30, OWASP, CIS, MITRE/CVE, NIST SP 800-60**. Each section
below maps one taxonomy dimension to the published works that defined or
operationalised the same scoring shape.

---

## 1. The ordinal `Low / Medium / High / Critical` scale

The four-level qualitative scale is the dominant convention across both
government and industry vulnerability scoring. Any of the following can be
cited as the schema baseline:

- **NIST SP 800-30 Rev. 1 — *Guide for Conducting Risk Assessments***
  defines the canonical qualitative risk matrix where Risk = Likelihood ×
  Impact, with both axes on a 5-step *Very Low → Very High* scale that most
  practitioners collapse into Low/Medium/High/Critical. This is the
  taxonomy's foundational risk-formula reference.
- **FIPS 199 / NIST SP 800-60 Vol. 1+2 — *Security Categorization of
  Federal Information and Information Systems*** assigns every information
  type a `{Confidentiality, Integrity, Availability}` impact tuple drawn
  from `{Low, Moderate, High}`, then takes the high-water mark. This is the
  closest published analogue to scoring files-and-directories by
  sensitivity tier (Source Code vs Sensitive Docs vs Public). The
  spreadsheet's Directory ranking is essentially an SP-800-60-style
  categorisation table specialised to a corporate filesystem.
- **CVSS v3.1 / v4.0 — *Common Vulnerability Scoring System*** uses the
  same four severity bands (Low / Medium / High / Critical) over a 0–10
  numeric base. Cite as the bridge between the qualitative bands and any
  future numeric calibration. The curated paper *From Description to
  Score* (Jafarikhah et al., SAC '26, `2025_from-description-to-score-llm-
  cvss.pdf`) shows LLMs can recover CVSS bands from free text — the same
  technique can be turned on tool-call records.
- **OWASP Risk Rating Methodology** uses Likelihood × Impact on a 0–9
  numeric scale collapsing to the same four bands. Most industry checklists
  ultimately reduce to this.
- **DREAD (Microsoft)** — Damage, Reproducibility, Exploitability, Affected
  users, Discoverability, each rated 1–10 then averaged. Historical
  baseline showing the multi-factor ordinal approach predates LLMs.
- **MAESTRO / ATFAA** (Narajala et al., arXiv 2504.19956, 2508.10043) — uses
  `R = P × I × E` (Likelihood × Impact × Exploitability), all ordinal.
  Closest *agentic* adaptation of the classic NIST formula and the one
  most-cited in MCP-defence papers.
- **OWASP AIVSS v0.5** (Huang, Bargury et al., 2025) — extends CVSS with 10
  Agentic AI Risk Amplification Factors. Provides the rigorous
  mathematical foundation for graded *agentic* risk scoring; the "Tool
  Use" AARF directly motivates the Tool axis of the taxonomy.
- **Multilevel Anomaly Detection (MAD) benchmark** (Cat 4 in
  `Scoring_curated`, arXiv 2411.14515) — empirically demonstrates that
  graded severity scoring outperforms binary safe/unsafe across many
  tasks. **TraceSafe-Bench** (arXiv 2604.07223) reaches the same finding
  for multi-step tool-call trajectories. Both papers are direct evidence
  that the L/M/H/C choice over binary is sound.

> **Bottom line:** the L/M/H/C scale is not arbitrary — it is the
> intersection of the NIST 800-30/FIPS-199 governmental scheme, CVSS
> bands, and the empirically-validated graded-vs-binary preference shown
> in MAD and TraceSafe-Bench.

---

## 2. The Directory axis — asset/sensitivity context

This axis maps directly onto the **asset / data importance scoring**
literature (Category 7 in `Literature_review/pdf/Scoring_curated`).

- **NIST SP 800-60 Vol. 2 — *Appendices***. Provides reference impact
  levels for ~100 information types (financial records, audit logs,
  source code, public-affairs material, etc.). The spreadsheet's eight
  directory classes are a corporate-flavoured remapping of this
  catalogue: *Sensitive Docs* = SP-800-60 §C.3 (Financial Management) +
  §D (PII); *Security Evidence* = §C.3.5 (Security Management);
  *Source Code* = §C.3.4 (Information Management); *Onboarding/Public* =
  the lowest impact categories. Cite SP-800-60 as the *taxonomy authority*
  for the directory ranking.
- **FIPS 199** — formal definition of *Low / Moderate / High* impact and
  the high-water-mark aggregation rule. Justifies promoting a folder's
  rating whenever it contains a file at higher sensitivity.
- **SARA — Sensitivity-Aware Relevance Assessments** (arXiv 2401.05144,
  `2024_SARA-sensitivity-aware-relevance-assessments.pdf`). Trains
  SVM/LR sensitivity classifiers on TF-IDF features and a
  *Learning-to-Rank* approach producing a numeric sensitivity score per
  document. Direct ML method for the filesystem-MCP use case — score every
  file by sensitivity rather than rely on filename.
- **CJA-RL — Crown Jewels Analysis with Reinforcement Learning on Attack
  Graphs** (arXiv 2108.09358,
  `2021_CJA-RL-crown-jewels-reinforcement-learning-attack-graphs.pdf`).
  Identifies the highest-criticality nodes ("crown jewels") in a network
  by training an RL agent on its attack graph. Analogue for marking the
  *Sensitive Docs / Security Evidence* directories as crown-jewel assets.
- **CIA + TA Risk Assessment for AI Reasoning** (arXiv 2508.15839,
  `2025_CIA-TA-risk-assessment-ai-reasoning-vulnerabilities.pdf`).
  Extends the classic CIA triad with Trust/Accountability and produces
  per-asset risk scores along all four axes. Direct schema candidate if
  the taxonomy ever needs richer per-asset output than a single tier.
- **Securing Critical Infrastructure in the AI Era** (arXiv 2507.07416,
  `2025_securing-critical-infrastructure-ai-era-framework.pdf`). Computes
  a *dynamic impact score per vulnerability* combining CVSS severity,
  **asset criticality**, exploit activity, dependency-graph position, and
  environmental exposure. The closest existing system to the
  static × dynamic product the framework should ultimately compute.
- **Data Valuation and Monetisation Framework** (arXiv 2512.07664,
  `2025_data-valuation-monetisation-framework.pdf`). General data-asset
  valuation framework; cite for the *value* axis that complements
  *sensitivity* (a budget file is both sensitive and high-value).
- **DLP-IGBCA classification** (`2023_dlp-classification-igbca.pdf`) and
  **Contextual Sensitive Data Detection**
  (`2025_contextual-sensitive-data-detection.pdf`). Two ML methods for
  classifying file content as sensitive — directly relevant for any
  future automation of the directory categorisation.

---

## 3. The Filetype axis — extension-based sensitivity / blast radius

This axis is shorter on academic baselines because it is largely an
engineering convention. The strongest anchors:

- **NIST SP 800-83 — Guide to Malware Incident Prevention and Handling**
  documents the relative malware risk of `.exe`, `.sys`, `.bash`, and
  macro-enabled Office formats. Justifies the spreadsheet's *Critical*
  rating for `.sys`/`.exe` and *High* for `.bash`/`.docx`/`.xlsx`.
- **MITRE ATT&CK T1059 (Command and Scripting Interpreter)** and
  **T1204 (User Execution)** enumerate the executable/script
  filetypes used in real intrusions. Cite as the empirical evidence for
  ranking `.bash`/`.exe`/`.code` above passive formats.
- **CIS Critical Security Controls v8 — Control 9 (Email and Web Browser
  Protections)** lists block-on-sight file extensions in policy form. The
  enterprise-procurement baseline for the same intuition.
- **OWASP File Upload Cheat Sheet** ranks file types by upload risk; the
  same hierarchy maps onto the spreadsheet's *Filetypes* ranking.
- **DLP-IGBCA classification** (above) — practical ML baseline for
  treating extension as one feature in a sensitivity score rather than as
  ground truth.

> The spreadsheet's filetype reasoning column ("Affects the kernel level",
> "Can run commands", "external links … macro-enabled variants") is
> exactly the language used by SP-800-83 §3 and ATT&CK T1204. Cite both.

---

## 4. The Tool axis — action / capability risk

This axis maps onto **permission and tool-invocation risk scoring**
(Category 3 in `Scoring_curated`) and the MCP-native scoring work
(Category 1).

- **MCP-in-SoS — Risk Assessment for Open-Source MCP Servers** (arXiv
  2603.10194, `2026_MCP-in-SoS-risk-assessment-mcp-servers.pdf`). Closest
  existing system to the static side of the framework: static analysis →
  CWE/CAPEC metadata → normalize → per-finding **Risk Index** + repo-level
  score. Validates the per-tool ordinal-score approach the spreadsheet
  uses for `read_file`/`write_file`/…
- **Auditing MCP Servers for Over-Privileged Tool Capabilities** (arXiv
  2603.21641, `2026_auditing-mcp-servers-overprivileged-tools.pdf`).
  `mcp-sec-audit` scores capability-based deployment risk by analysing
  implementation code + tool metadata; outputs hardening guidance.
  Direct analogue for scoring tool *permissions* at registration.
- **Detecting Malicious Entra OAuth Apps with LLM-Based Permission Risk
  Scoring** (arXiv 2512.15781,
  `2025_llm-permission-risk-scoring-entra-oauth.pdf`). Releases a public
  dataset of risk scores for all 769 Microsoft Graph scopes, generated by
  8 LLMs with reasoning. Direct methodological template for static
  scoring of MCP tool permissions — change "Graph scope" to "MCP tool".
- **AgenTRIM — Tool Risk Mitigation for Agentic AI** (arXiv 2601.12449,
  `2026_AgenTRIM-tool-risk-mitigation-agentic-ai.pdf`). Runtime
  orchestrator that combines deterministic controls + LLM reasoning to
  score tool exposure on a per-query basis. Direct match for the dynamic
  twin of the spreadsheet (the static side is what's in the xlsx today).
- **Agent Tools Orchestration Leaks More** (arXiv 2512.16310,
  `2025_agent-tools-orchestration-leaks-more.pdf`). Introduces
  **Risk Leakage Rate (RLR)** and **H-Score** for tool orchestration.
  Reports 90.24 % average RLR across 8 models. Ready-made evaluation
  metrics for grading the spreadsheet end-to-end.
- **MCP-Guard** (Xing et al., arXiv 2508.10991). Three-stage cascaded
  proxy (regex → E5 detector → LLM arbiter) on MCP request payloads, F1
  95.4 %. The xlsx's role is precisely the *severity dial* that
  MCP-Guard's own roadmap lists as future work.
- **Progent** (Shi et al., arXiv 2504.11703). Per-call JSON-policy proxy,
  drops prompt-injection ASR 41.2 → 2.2 % on AgentDojo. Provides the
  policy-enforcement context the score will eventually drive.
- **MCP-RiskCue** (arXiv 2511.05867,
  `2025_MCP-RiskCue-llm-infer-risk-from-logs.pdf`). Tests whether LLMs
  can infer risk from MCP server *logs* — the runtime twin of the
  spreadsheet.
- **Repello AI Blast Radius model** — four measurable dimensions: data
  access, executable actions, downstream system exposure, and persistence
  mechanisms. The spreadsheet implicitly encodes the first two; cite for
  the explicit blast-radius rationale that `write_file` outranks
  `read_file`.
- **Anthropic Trustworthy Agents Framework** — graduated permissions
  (always allow / needs approval / block) per tool action. Production
  precedent for ordinal per-tool gating.

---

## 5. The matrix shape — why `Directory × Filetype × Tool` is the right cube

Three published precedents support a multi-axis matrix rather than a
single score:

- **NIST SP 800-30 Tables I-2/I-3** — present qualitative risk as a
  *matrix* of Likelihood × Impact rather than a scalar.
- **OWASP Risk Rating Matrix** — the same Likelihood × Impact 4×4 grid.
- **Securing Critical Infrastructure in the AI Era** (arXiv 2507.07416) —
  computes risk as *vulnerability score × asset criticality × exposure*,
  i.e. the **static × asset × dynamic** product. The xlsx covers the
  static × asset half today; this paper supplies the conceptual frame
  for adding the dynamic third dimension later.
- **Microsoft AGT (Agent Governance Toolkit)** — 0-1000 trust score with
  5 behavioural tiers and decay. Production-tested precedent for an
  ordinal-yet-continuous score (the natural extension of the xlsx).

> The exact cube `(Asset × File × Action)` does not appear in any single
> prior paper — that is the spreadsheet's contribution. What is reused is
> each *individual face* of the cube: SP-800-60 for the asset face,
> SP-800-83/ATT&CK for the file face, and AIVSS/MCP-in-SoS for the
> action face.

---

## 6. Suggested citation block for the thesis

Drop-in BibTeX/Markdown anchors covering every justification needed for
the xlsx, grouped by section above:

| Use to justify | Cite |
|---|---|
| Ordinal L/M/H/C scale | NIST SP 800-30 Rev. 1; FIPS 199; CVSS v3.1; OWASP Risk Rating |
| Graded > binary | MAD (arXiv 2411.14515); TraceSafe-Bench (arXiv 2604.07223) |
| Directory categorisation | NIST SP 800-60 Vol. 1+2; FIPS 199; SARA (arXiv 2401.05144); CJA-RL (arXiv 2108.09358) |
| Asset × vuln product | Securing Critical Infrastructure (arXiv 2507.07416); CIA+TA (arXiv 2508.15839) |
| Filetype risk | NIST SP 800-83; MITRE ATT&CK T1059/T1204; CIS Control 9 |
| Tool permission risk (MCP-specific) | MCP-in-SoS (arXiv 2603.10194); Auditing MCP Servers (arXiv 2603.21641); MCP-Guard (arXiv 2508.10991); Progent (arXiv 2504.11703) |
| Tool permission risk (general) | OWASP AIVSS v0.5; MAESTRO/ATFAA (arXiv 2504.19956); Entra OAuth scoring (arXiv 2512.15781); AgenTRIM (arXiv 2601.12449) |
| Evaluation metrics | Risk Leakage Rate / H-Score (arXiv 2512.16310); AgentHarm (arXiv 2410.09024); Agent-SafetyBench (arXiv 2412.14470) |
| Architectural pattern | NIST SP 800-207 (Zero Trust); MS Agent Governance Toolkit; Repello AI Blast Radius |

---

## 7. Gaps worth acknowledging in the write-up

- **No prior work scores filesystem MCP tools specifically.** The closest
  systems (MCP-in-SoS, mcp-sec-audit) score *MCP server repositories* or
  *individual tools in isolation*, not the cell `(asset class × extension
  × tool)`. Frame the xlsx as the *first hand-curated Filesystem-MCP
  reference matrix*.
- **The xlsx is currently 100 % static.** The dynamic counterparts
  (AgenTRIM, MCP-RiskCue, ToolSafe, ProGuard) live in separate papers; the
  framework's next step is to multiply the static cell value by a
  runtime-derived modifier — exactly the static × dynamic product
  `Securing Critical Infrastructure` operationalises.
- **No published taxonomy lists the same 8 directory classes.** The
  closest list is NIST SP-800-60 Vol. 2's information-type catalogue.
  Document the mapping explicitly so the choice is reproducible.

---

## References (verbatim file locations)

All cited papers live in the repository under
`C:\Users\user\Documents\GitHub\MCP\Literature_review\pdf\`:

- `Scoring_curated/2026_MCP-in-SoS-risk-assessment-mcp-servers.pdf`
- `Scoring_curated/2026_auditing-mcp-servers-overprivileged-tools.pdf`
- `Scoring_curated/2025_MCP-RiskCue-llm-infer-risk-from-logs.pdf`
- `Scoring_curated/2025_from-description-to-score-llm-cvss.pdf`
- `Scoring_curated/2025_llm-permission-risk-scoring-entra-oauth.pdf`
- `Scoring_curated/2026_AgenTRIM-tool-risk-mitigation-agentic-ai.pdf`
- `Scoring_curated/2025_agent-tools-orchestration-leaks-more.pdf`
- `Scoring_curated/2024_multilevel-anomaly-detection-benchmark.pdf`
- `Scoring_curated/2024_SARA-sensitivity-aware-relevance-assessments.pdf`
- `Scoring_curated/2021_CJA-RL-crown-jewels-reinforcement-learning-attack-graphs.pdf`
- `Scoring_curated/2025_CIA-TA-risk-assessment-ai-reasoning-vulnerabilities.pdf`
- `Scoring_curated/2025_securing-critical-infrastructure-ai-era-framework.pdf`
- `Scoring_curated/2025_data-valuation-monetisation-framework.pdf`
- `6_Risk_Scoring/detection/2023_dlp-classification-igbca.pdf`
- `6_Risk_Scoring/detection/2025_contextual-sensitive-data-detection.pdf`
- `7_Not_Academic/2020_NIST_SP_800-207_zero-trust-architecture.pdf`

Companion repo documents:

- `Literature_review/risk_scoring_frameworks_survey.md` — full survey of
  the agentic-risk-scoring landscape (40+ papers).
- `Literature_review/related_work_gap_matrix.md` — gap analysis defending
  the *first dynamic, ordinal, agent-aware risk scorer for the A→S
  direction of MCP* claim.
- `Literature_review/mcp_server_attack_taxonomy_v2_agent_boundary.md` —
  attack taxonomy the xlsx scores against.
