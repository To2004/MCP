# Search for graded-severity benchmarks (and why most don't fit)

We need external ground truth that grades each **action** on a **severity scale**
(none/low/medium/high/critical) over a **benign→misuse** range — the target of a
risk-*scoring* framework, comparable to CVSS/NIST. We searched widely; the key finding
is that **clean per-action severity ground truth is rare**: most agent-safety
benchmarks are binary (safe/unsafe), categorical (risk *type*, not level), or grade the
agent's *trajectory* at eval time rather than labelling each action. That scarcity is
itself part of the gap this framework addresses.

## Verdicts

| benchmark | graded severity? | per-action label? | public data? | usable here? | why |
| --- | --- | --- | --- | --- | --- |
| **AgentTrust** | ✅ none..critical | ✅ | ✅ AGPL-3.0 | **YES (used)** | exactly the target: 5-level severity per action, benign→misuse, 430 items |
| ToolEmu | partial (0–3 safety) | ❌ | ✅ | no | 0–3 score is computed on the agent's *trajectory* by an LM evaluator at eval time; `all_cases.json` has only risk *descriptions*, no per-case severity label |
| SafeToolBench | ❌ (risk *category*) | partial | ✅ | no | items carry a Risk *Category* (e.g. "Bias & Offensiveness") + a binary high/low split, not a graded severity level |
| SafeAgentBench | ❌ (safe/unsafe) | task-level | ✅ | no | embodied (AI2-THOR) safe/unsafe task planning, not graded per-action severity |
| Agent-SafetyBench | ❌ (failure modes) | trajectory | ✅ | no | 8 risk categories / 10 failure modes; safety classification, not a severity scale |
| R-Judge | ❌ (safe/unsafe) | per-step binary | ✅ | no | binary risk awareness from interaction records |
| PrivacyLens / ConfAIde / AgentSocialBench | partial (sensitivity) | trajectory | ✅ | no | graded *privacy* sensitivity / leak rate; privacy-only, trajectory-graded |
| HAICOSYSTEM / ToolSword | ❌ | dynamic | ✅ | no | LM-based dynamic risk over multi-turn interactions; no fixed per-action severity |
| SkyEye (AWS IAM) | ✅ L/M/H/Critical (~20k actions) | ✅ (permission) | ❌ | no (no public dataset) | a Black Hat tool; ~20k AWS actions graded, but no public dataset release found |
| CVE / CVSS (NVD, CIRCL, Kaggle) | ✅ (CVSS severity) | ✅ (vulnerability) | ✅ | future | canonical graded severity, but items are *software vulnerabilities*, not agent/tool *actions* — a different feature space (needs a CVE-text scorer); kept as a future direct CVSS check |
| Linux_Command_Classification (HF) | ❌ (intent) | ✅ | ✅ | no | commands labelled by intent/context, not severity |
| Qwen3Guard / WildGuard | ❌ (content safety) | response-level | ✅ | no | 3-tier content moderation, not tool-action severity |

## What we did with the finding

- **Used** the one clean fit, **AgentTrust** (external, 430 items across internal /
  real-world / obfuscated-bypass sets).
- Because per-action severity ground truth is scarce, we **authored** a complementary
  set (`external/mcp_severity/`, 66 scenarios across reversibility × sensitivity × scope
  × exfiltration, labelled from independent SOC-analyst intuition, *not* the framework's
  formula). It is **secondary** evidence — author-created — and is reported separately
  from the external headline.
- **CVE/CVSS** remains the natural next external source for a *direct* CVSS/NIST
  comparison, but on vulnerabilities rather than actions; it needs a text-based scorer
  and is left as a documented future extension.

## Sources

AgentTrust (arXiv:2605.04785, github.com/chenglin1112/AgentTrust) ·
ToolEmu (ICLR'24, github.com/ryoungj/ToolEmu) ·
SafeToolBench (EMNLP'25 Findings, github.com/BITHLP/SafeToolBench) ·
SafeAgentBench (arXiv:2412.13178) · Agent-SafetyBench (arXiv:2412.14470) ·
PrivacyLens (NeurIPS'24) · ToolEmu/HAICOSYSTEM/ToolSword surveys ·
SkyEye (arXiv:2507.21094) · CVSS/NVD, CIRCL/vulnerability-scores (HF).
