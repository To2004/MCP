# NVD/CVE Database + CVSS v3.1

## Source
- **Paper:** From Description to Score: Can LLMs Quantify Vulnerabilities? — Jafarikhah et al.
- **Link:** https://nvd.nist.gov/
- **Year:** 2026

## Format & Size
- **Total samples:** 31,000+ CVEs from 2019-2024 with CVSS v3.1 base metric scores
- **Format:** Structured vulnerability records with textual descriptions and 8 categorical sub-metric scores plus a composite 0.0-10.0 severity score
- **Availability:** Fully public via NVD (National Vulnerability Database) — https://nvd.nist.gov/

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| CVE ID | String | CVE-2023-12345 | Yes | Unique vulnerability identifier |
| Description | Text | Free-text vulnerability description | Yes | Input for text-to-score models — directly analogous to MCP tool descriptions |
| Attack Vector (AV) | Categorical | Network, Adjacent, Local, Physical | Yes | How the attacker reaches the target |
| Attack Complexity (AC) | Categorical | Low, High | Yes | Conditions beyond attacker control |
| Privileges Required (PR) | Categorical | None, Low, High | Yes | Auth level needed to exploit |
| User Interaction (UI) | Categorical | None, Required | Yes | Whether a human must act |
| Scope (S) | Categorical | Unchanged, Changed | Yes | Whether exploit crosses trust boundaries |
| Confidentiality Impact (C) | Categorical | None, Low, High | Yes | Data exposure severity |
| Integrity Impact (I) | Categorical | None, Low, High | Yes | Data modification severity |
| Availability Impact (A) | Categorical | None, Low, High | Yes | Service disruption severity |
| CVSS Base Score | Float | 0.0-10.0 | Yes | Composite severity score |
| Severity Label | Categorical | None, Low, Medium, High, Critical | Yes | Derived from base score thresholds |

## Proposed Risk Dimensions

### Attack Surface (from AV + AC)
- **Feeding columns:** Attack Vector, Attack Complexity
- **Proposed scale:** 1-10 combining reachability and difficulty
- **Derivation:** AV maps to reachability: Network=8, Adjacent=6, Local=4, Physical=2. AC modifies it: Low complexity = no change, High complexity = subtract 2. So Network+Low=8, Network+High=6, Local+Low=4, Local+High=2. For MCP tools: network-accessible tools with simple invocation = high score. Tools requiring local access and complex setup = low score.

### Privilege Escalation Potential (from PR + UI + S)
- **Feeding columns:** Privileges Required, User Interaction, Scope
- **Proposed scale:** 1-10 combining access requirements and blast radius
- **Derivation:** PR: None=8, Low=5, High=2. UI: None=+2, Required=+0. S: Changed=+2, Unchanged=+0. Sum and normalize to 1-10. A tool requiring no privileges, no user interaction, and capable of crossing trust boundaries (Scope=Changed) scores 10. A tool needing high privileges and user confirmation with no scope change scores 2. For MCP: tools that agents can invoke autonomously without human approval and that affect external systems = highest scores.

### Impact Triad (from C + I + A)
- **Feeding columns:** Confidentiality Impact, Integrity Impact, Availability Impact
- **Proposed scale:** 1-10 composite, or three separate 1-10 sub-scores
- **Derivation:** Each impact metric: None=0, Low=3, High=7. Sum all three (0-21), normalize to 1-10. Alternatively, keep as three separate dimensions for finer granularity. For MCP risk scoring, these three dimensions transfer directly: a tool that can read sensitive data (C=High), modify state (I=High), and crash services (A=High) gets the maximum impact score. A read-only tool with no state modification = low score.

### Text-to-Score Feasibility (Meta-dimension)
- **Feeding columns:** CVE description → CVSS base score (the LLM evaluation results)
- **Proposed scale:** Not a risk score itself, but validates the approach
- **Derivation:** The Jafarikhah et al. paper tested 6 LLMs on predicting CVSS scores from text descriptions. GPT-5 achieved highest precision with two-shot prompting. This validates that LLMs CAN map textual descriptions to multi-dimensional severity scores — the exact approach needed for scoring MCP tool descriptions. The MAE across 8 metrics provides the expected error margin for an LLM-based MCP scorer.

## Data Quality Notes
- 31K+ CVEs is a large, well-established dataset with professional annotations by NVD analysts — gold-standard quality for vulnerability scoring.
- CVSS v3.1 is the current industry standard, but it was designed for static software vulnerabilities, not dynamic agent-tool interactions. Some metrics (e.g., Physical attack vector) may not apply to MCP.
- The text descriptions vary significantly in quality and detail — some are one-liners, others are multi-paragraph.
- The LLM evaluation results (GPT-5 as best performer, two-shot optimal) are specific to the models and prompting strategies tested. Results may differ for other models or fine-tuning approaches.
- A meta-classifier combining LLM outputs provided only marginal improvement over the best single model, suggesting diminishing returns from ensembling.
- CVSS does not capture temporal or environmental factors — only base metrics. MCP risk scoring will need additional dimensions beyond what CVSS provides.

## Usefulness Verdict
This is the **methodological foundation** for the entire MCP risk scoring approach. CVSS v3.1 is the most established multi-dimensional vulnerability scoring system in existence, and its 8 sub-metrics provide a proven template for decomposing "risk" into measurable axes. The direct transfer is: Attack Vector → tool accessibility, Privileges Required → agent permission level, Scope → blast radius across trust boundaries, and the CIA triad → impact on confidentiality, integrity, and availability.

The Jafarikhah et al. results are equally important: they demonstrate that LLMs can predict CVSS scores from text descriptions with reasonable accuracy, which validates the core technical approach of scoring MCP tools based on their textual descriptions and metadata. The 31K+ CVE dataset can serve as pre-training data for a scorer — teach it to map description → multi-dimensional score on CVEs, then fine-tune on MCP-specific data. The two-shot prompting finding is immediately practical for a lightweight MCP scorer that does not require fine-tuning.
