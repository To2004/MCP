# Literature Review — v5 Paper

Curated reading set for the v5 (policy-grade) paper. **53 peer-reviewed /
preprint papers** plus **11 primary, standards, and industry sources**, grouped
into thirteen strands. Every entry here has a matching key in
[`refs.bib`](refs.bib); arXiv IDs, DOIs, and venues were resolved against the
arXiv API or the publisher record on 2026-07-30.

Strands **J–M** were added from the papers you cited in
`../presentations/slides/2026-05-06_lit-review-categories.pptx` and
`Weekly Sync Meeting 2026-04-06 (MCP).pptx`, plus the industry disclosures that
named several MCP attack classes before the first paper on them.

Local PDFs live under `../Literature_review/pdf/`; the `PDF` column gives the
path relative to that folder, or `—` when the paper is not in the local corpus.

## Contents

- [How this set was selected](#how-this-set-was-selected)
- [A. MCP protocol, ecosystem, and measurement](#a-mcp-protocol-ecosystem-and-measurement)
- [B. MCP threat taxonomies and systematizations](#b-mcp-threat-taxonomies-and-systematizations)
- [C. Attacks on and through MCP](#c-attacks-on-and-through-mcp)
- [D. MCP and agent defenses](#d-mcp-and-agent-defenses)
- [E. Risk scoring: classical systems and their AI adaptations](#e-risk-scoring-classical-systems-and-their-ai-adaptations)
- [F. Risk estimation for agents, design time and run time](#f-risk-estimation-for-agents-design-time-and-run-time)
- [G. Agent-safety benchmarks and injected-agent evidence](#g-agent-safety-benchmarks-and-injected-agent-evidence)
- [H. LLM-as-judge and LLM-driven security assessment](#h-llm-as-judge-and-llm-driven-security-assessment)
- [I. Security categorization standards](#i-security-categorization-standards)
- [J. Asset and data importance scoring](#j-asset-and-data-importance-scoring)
- [K. Permission, capability, and CVSS scoring by LLM](#k-permission-capability-and-cvss-scoring-by-llm)
- [L. Graded severity as an output shape, and runtime scoring](#l-graded-severity-as-an-output-shape-and-runtime-scoring)
- [M. Industry disclosures and vendor guidance](#m-industry-disclosures-and-vendor-guidance)
- [Corrections to the local catalog](#corrections-to-the-local-catalog)
- [Second tier — read, not cited](#second-tier--read-not-cited)
- [Where the gap is](#where-the-gap-is)

## How this set was selected

The paper's claim is narrow, so the reading set is built to attack it from four
sides rather than to survey MCP security in general:

1. **Is the threat model real?** — strands A and C establish that MCP servers
   hold consequential assets and that the agent side is routinely subverted.
2. **Do existing defenses already produce a graded number?** — strand D shows
   they collapse to allow/deny.
3. **Do existing scoring systems apply?** — strands E and F show they are
   either vulnerability-shaped, tool-only, or post-hoc.
4. **Is "derive severity from policy" a legitimate framing?** — strands H and I
   supply the precedent: LLMs reading configuration and producing security
   judgements, and the FIPS 199 / SP 800-60 classify-then-map procedure this
   work automates.

Strand B supplies the taxonomies used to position the threat model, and
strand G supplies the evidence that an injected agent is indistinguishable from
a legitimate one at the protocol boundary.

## A. MCP protocol, ecosystem, and measurement

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `anthropic2024mcp` | Introducing the Model Context Protocol | Anthropic, 2024 | Primary source for the protocol and its release date. | — |
| `mcp2026spec` | Model Context Protocol Specification | modelcontextprotocol.io, 2026 | Normative reference for `tools/list`, tool annotations, and the JSON-RPC surface the scanner consumes. | — |
| `hou2026mcp` | MCP: Landscape, Security Threats, and Future Research Directions | ACM TOSEM 2026, doi:10.1145/3796519 | The anchor survey; its lifecycle framing is where "attention concentrates on the server→agent direction" is documented. | `2_MCP_Protocol/surveys/Model_Context_Protocol_(MCP)_Landscape,...pdf` |
| `hasan2025firstglance` | MCP at First Glance: Security and Maintainability of MCP Servers | arXiv:2506.13538 | Source of the 1,899-server figure cited in §1.1; establishes ecosystem scale empirically rather than from registry marketing. | `2_MCP_Protocol/measurements/Model_Context_Protocol_(MCP)_at_First_Glance_...pdf` |
| `guo2025measurement` | A Measurement Study of Model Context Protocol Ecosystem | arXiv:2509.25292 | Independent ecosystem crawl; corroborates scale and distribution of server types. | `2_MCP_Protocol/measurements/A_Measurement_Study_of_Model_Context_Protocol_Ecosystem.pdf` |
| `li2026firstlook` | A First Look at the Security Issues in the MCP Ecosystem | DSN 2026, arXiv:2510.16558 | Peer-reviewed measurement of real security issues in deployed servers. | `2_MCP_Protocol/measurements/2025_first-look-mcp-ecosystem-security.pdf` |
| `li2025privilege` | We Urgently Need Privilege Management in MCP | IEEE MASS 2025 | **Load-bearing for the threat model.** Measures that servers expose far more API surface than any task needs — the privilege behind a call exceeds the privilege the call requires. | `2_MCP_Protocol/measurements/We_Urgently_Need_Privilege_Management_in_MCP_...pdf` |

## B. MCP threat taxonomies and systematizations

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `gaire2025sok` | SoK: Security and Safety in the MCP Ecosystem | arXiv:2512.08290 | Most recent systematization; use to show the agent→server cell is thin. | `1_MCP_Security/surveys/SoK_Security_and_Safety_in_the_Model_Context_Protocol_Ecosystem.pdf` |
| `shen2026mcp38` | MCP-38: A Comprehensive Threat Taxonomy for MCP Systems | arXiv:2603.18063 | 38-category taxonomy; the finest-grained map to position our threat model against. | `1_MCP_Security/surveys/MCP-38_...pdf` |
| `rostamzadeh2026mcpdpt` | MCP-DPT: Defense-Placement Taxonomy and Coverage Analysis | arXiv:2604.07551 | Classifies *where* defenses sit (client, proxy, server). Our contribution is server-side and design-time — a cell this taxonomy shows is sparse. | `1_MCP_Security/surveys/MCP-DPT_...pdf` |
| `zhao2026parasites` | Parasites in the Toolchain: Large-Scale Analysis of Attacks on the MCP Ecosystem | IEEE S&P 2026 | Top-tier venue, large-scale; the strongest citation for cross-tool/server→agent attacks being the field's centre of gravity. | `1_MCP_Security/attacks/Parasites_in_the_Toolchain_...pdf` |

## C. Attacks on and through MCP

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `radosevich2025mcpsafety` | MCP Safety Audit: LLMs with MCP Allow Major Security Exploits | arXiv:2504.03767 | The canonical "MCP is exploitable" citation; also the origin of MCPSafetyScanner, an audit-time comparison point. | `1_MCP_Security/attacks/MCP_Safety_Audit_...pdf` |
| `wang2025mcptox` | MCPTox: Benchmark for Tool Poisoning on Real-World MCP Servers | arXiv:2508.14925 | Tool poisoning measured on *real* servers, matching our use of real vendor catalogs. | `1_MCP_Security/attacks/MCPTox_...pdf` |
| `shi2025toolhijacker` | Prompt Injection Attack to Tool Selection in LLM Agents | arXiv:2504.19793 | Shows the agent's tool choice is attacker-controllable — the mechanism that makes a legitimate-looking call malicious. | `4_Prompt_Injection/attacks/Prompt_Injection_Attack_to_Tool_Selection_in_LLM_Agents_(ToolHijacker).pdf` |
| `yang2025mcpsecbench` | MCPSecBench: Systematic Security Benchmark and Playground | arXiv:2508.13220 | Benchmark already used in this project's external-benchmark evaluation; keeps the paper's evaluation lineage citable. | `1_MCP_Security/benchmarks/MCPSecBench_...pdf` |

## D. MCP and agent defenses

The argument this strand supports: **every one of these ends in a binary
verdict.** That is the gap the graduated score fills.

| Key | Work | Venue / ID | Output form | PDF |
|---|---|---|---|---|
| `xing2025mcpguard` | MCP-Guard: Multi-Stage Defense-in-Depth for MCP | arXiv:2508.10991 | Block / pass, inline proxy | `1_MCP_Security/defenses/MCP-Guard_...pdf` |
| `zhou2026mcpshield` | MCPShield: Security Cognition Layer for Adaptive Trust Calibration | arXiv:2602.14281 | Trust calibration → gate | `1_MCP_Security/defenses/MCPShield_...pdf` |
| `jing2025mcip` | MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol | EMNLP 2025 | 10-way label, not ordinal | `1_MCP_Security/defenses/MCIP_...pdf` |
| `bhatt2025etdi` | ETDI: Mitigating Tool Squatting and Rug Pull via OAuth-Enhanced Tool Definitions | CARS 2025, doi:10.1109/CARS67163.2025.11337310 | Policy allow/deny | `1_MCP_Security/defenses/ETDI_...pdf` |
| `shi2025progent` | Progent: Securing AI Agents with Privilege Control | arXiv:2504.11703 | Allow/deny, hand-authored policy | `3_Multi_Agent_Trust/frameworks/Progent_...pdf` |
| `zhu2025miniscope` | MiniScope: Least Privilege Framework for Authorizing Tool-Calling Agents | arXiv:2512.11147 | Scope grant/deny | `4_Prompt_Injection/defenses/MiniScope_...pdf` |
| `abaev2026agentguardian` | AgentGuardian: Learning Access Control Policies to Govern AI Agent Behavior | arXiv:2601.10440 | Learned allow/deny. Same group (BGU) — position carefully, this is the nearest in-house neighbour. | `1_MCP_Security/defenses/AgentGuardian_...pdf` |
| `buhler2026agentbound` | AgentBound: Securing Execution Boundaries of AI Agents | FSE 2026 | Boundary enforcement | — |

## E. Risk scoring: classical systems and their AI adaptations

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `spring2021time` | Time to Change the CVSS? | IEEE S&P Magazine 2021, doi:10.1109/MSEC.2020.3044475 | Authoritative critique of CVSS as a decision input. | — |
| `jacobs2021epss` | Exploit Prediction Scoring System (EPSS) | DTRAP 2021, doi:10.1145/3436242 | Precedent for replacing a hand-weighted formula with a calibrated, evaluated score. | — |
| `bahar2024validity` | On the Validity of Traditional Vulnerability Scoring Systems for Adversarial Attacks against LLMs | arXiv:2412.20087 | Direct evidence that CVSS/DREAD collapse toward a single value on AI threats — the over-block result this project reproduced. | — |
| `owasp2025aivss` | OWASP AI Vulnerability Scoring System | OWASP, 2025 | The main AI-specific scoring baseline; capability-only, hence argument-blind. | — |
| `jafarikhah2026description` | From Description to Score: Can LLMs Quantify Vulnerabilities? | ACM SAC 2026, arXiv:2512.06781 | **Closest methodological neighbour**: LLM reads text, emits an ordinal severity. Differs in that it scores CVEs from descriptions, not tool/asset pairs from policy. | `6_Risk_Scoring/scoring/From_Description_to_Score_...pdf` |
| `betser2026agentrim` | AgenTRIM: Tool Risk Mitigation for Agentic AI | arXiv:2601.12449 | Tool-level risk for agentic systems; no asset dimension, no organizational context. | `Scoring_curated/2026_AgenTRIM-tool-risk-mitigation-agentic-ai.pdf` |
| `kumar2026mcpinsos` | MCP-in-SoS: Risk Assessment Framework for Open-Source MCP Servers | arXiv:2603.10194 | The other MCP-specific risk-assessment framework; scores the *server implementation*, not the request. | `Scoring_curated/2026_MCP-in-SoS-risk-assessment-mcp-servers.pdf` |

## F. Risk estimation for agents, design time and run time

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `hazan2025astra` | ASTRA: Agentic Steerability and Risk Assessment Framework | arXiv:2511.18114 | Agent-level risk assessment; complements rather than competes (agent as subject, not server). | `6_Risk_Scoring/scoring/ASTRA_...pdf` |
| `fu2025riskcue` | Can LLM Infer Risk Information From MCP Server System Logs? | arXiv:2511.05867 | The MCP-RiskCue work. Same intuition — LLM infers risk for MCP — but **post-hoc from logs**, after execution. We score before. | `Scoring_curated/2025_MCP-RiskCue-llm-infer-risk-from-logs.pdf` |
| `fleming2025tbac` | Uncertainty-Aware, Risk-Adaptive Access Control using an LLM-Judged TBAC Model | arXiv:2510.11414 | Precedent for an LLM judgement driving a *graded*, risk-adaptive access decision. | — |
| `yuan2024rjudge` | R-Judge: Benchmarking Safety Risk Awareness for LLM Agents | Findings of EMNLP 2024 | The standard for "can a model judge agent risk at all"; also a candidate external oracle. | `6_Risk_Scoring/scoring/R-Judge_...pdf` |

## G. Agent-safety benchmarks and injected-agent evidence

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `zhan2024injecagent` | InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated LLM Agents | Findings of ACL 2024 | Evidence that an injected agent emits well-formed, authenticated calls. | `4_Prompt_Injection/attacks/InjecAgent_...pdf` |
| `debenedetti2024agentdojo` | AgentDojo: Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses | NeurIPS 2024 D&B | Same point, with a live environment; the standard citation pair. | `4_Prompt_Injection/benchmarks/AgentDojo_...pdf` |
| `ruan2024toolemu` | Identifying the Risks of LM Agents with an LM-Emulated Sandbox | ICLR 2024 | ToolEmu — the origin of LM-judged agent risk severity; explains why *graded* ground truth is scarce. | — |
| `anthropic2025misalignment` | Agentic Misalignment: How LLMs Could Be Insider Threats | Anthropic, 2025 | Covers the non-injection branch of the threat model: a goal-drifted agent, not a hijacked one. | — |

## H. LLM-as-judge and LLM-driven security assessment

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `zheng2023judging` | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | NeurIPS 2023 D&B | Methodological grounding, and the source of the position-bias/self-preference caveats our judge stage must answer. | — |
| `malul2024genkubesec` | GenKubeSec: LLM-Based Kubernetes Misconfiguration Detection, Localization, Reasoning, Remediation | arXiv:2405.19954 | Direct precedent: LLM reads declarative configuration, produces a security verdict with reasoning. Same group. | — |
| `cohen2025kubeguard` | KubeGuard: LLM-Assisted Kubernetes Hardening via Configuration Files and Runtime Logs | arXiv:2509.04191 | The static-plus-runtime pairing, one domain over. Useful template for framing the static/dynamic split. | — |

## I. Security categorization standards

**This strand is what makes the v5 framing defensible.** The paper's premise —
that an organization publishes a *policy*, not a numbered inventory — is not a
convenience assumption; it is how the standards say categorization works.

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `nist2004fips199` | Standards for Security Categorization of Federal Information and Information Systems | FIPS PUB 199, doi:10.6028/NIST.FIPS.199 | Defines the low/moderate/high impact levels **in prose**, per CIA objective. The classify-then-map procedure we automate. | — |
| `nist2008sp80060` | Guide for Mapping Types of Information and Information Systems to Security Categories | NIST SP 800-60 Vol. 1 Rev. 1, doi:10.6028/NIST.SP.800-60v1r1 | The companion mapping guide: information type → impact level. Exactly the derivation the scanner performs, done by hand. | — |
| `owasp2026agentictop10` | OWASP Top 10 for Agentic Applications | OWASP, 2026 | Industry framing for agentic risk; note that no category defines a per-request quantitative score for a server. | — |

## J. Asset and data importance scoring

**The strand your slide deck called Category 7 — and the one v5 is actually
about.** These score the *asset*, independently of any request. Every other
strand assumes that number; this is the small body of work that tries to
produce it. None of it is wired into an MCP scorer, which is the opening.

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `mckechnie2024sara` | SARA: A Collection of Sensitivity-Aware Relevance Assessments | SIGIR 2024, arXiv:2401.05144 | Learning-to-rank producing a *graded* sensitivity score per document, not a label. The closest prior art to deriving sensitivity rather than reading it off a table. | `Scoring_curated/2024_SARA-sensitivity-aware-relevance-assessments.pdf` |
| `gangupantulu2021crownjewels` | Crown Jewels Analysis using Reinforcement Learning with Attack Graphs | arXiv:2108.09358 | Automatically identifies which assets matter most in an estate. Different mechanism (attack graph, not policy text), same question. | `Scoring_curated/2021_CJA-RL-crown-jewels-reinforcement-learning-attack-graphs.pdf` |
| `aydin2025ciata` | CIA+TA Risk Assessment for AI Reasoning Vulnerabilities | arXiv:2508.15839 | Per-axis (C/I/A + Trust/Accountability) asset scores rather than one number — relevant to the policy register's CIA columns. | `Scoring_curated/2025_CIA-TA-risk-assessment-ai-reasoning-vulnerabilities.pdf` |
| `vyhmeister2025datavaluation` | A Framework for Data Valuation and Monetisation | arXiv:2512.07664 | Asset *value* as an axis distinct from asset *risk*; useful for the discussion of what the sensitivity scale is really measuring. | `Scoring_curated/2025_data-valuation-monetisation-framework.pdf` |

## K. Permission, capability, and CVSS scoring by LLM

The "LLM reads text, emits an ordinal" pattern, in the three domains where it
already has a track record. Together with `jafarikhah2026description` these
establish that the method is credible before we apply it to MCP.

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `huang2026auditing` | Auditing MCP Servers for Over-Privileged Tool Capabilities | arXiv:2603.21641 | `mcp-sec-audit`. Scores capability risk at registration from code + tool metadata — the nearest design-time MCP competitor. | `Scoring_curated/2026_auditing-mcp-servers-overprivileged-tools.pdf` |
| `marchiori2025cves` | Can LLMs Classify CVEs? Investigating LLM Capabilities in Computing CVSS Vectors | arXiv:2504.10713 | LLM vs embeddings for CVSS components; argues hybrid. Supports our rules-first-with-LLM-fallback design. | `Scoring_curated/2025_can-llms-classify-cves-cvss-vectors.pdf` |
| `mahara2025entra` | Detecting Malicious Entra OAuth Apps with LLM-Based Permission Risk Scoring | arXiv:2512.15781 | 769 Microsoft Graph scopes scored by 8 open-source LLMs. **The closest methodological template for scoring MCP tool permissions**, and precedent for using local models. | `Scoring_curated/2025_llm-permission-risk-scoring-entra-oauth.pdf` |
| `qiao2025orchestration` | Agent Tools Orchestration Leaks More: Dataset, Benchmark, and Mitigation | arXiv:2512.16310 | RLR and H-Score metrics; 90.24% average leakage across 8 models. Ready-made end-to-end evaluation metrics, and the mosaic-effect argument that per-call scoring alone is insufficient. | `Scoring_curated/2025_agent-tools-orchestration-leaks-more.pdf` |

## L. Graded severity as an output shape, and runtime scoring

| Key | Work | Venue / ID | Why it is here | PDF |
|---|---|---|---|---|
| `cao2024mad` | Are Anomaly Scores Telling the Whole Story? A Benchmark for Multilevel Anomaly Detection | arXiv:2411.14515 | **Cited in §1.1.** The evidence that graded severity beats binary for operator action — the general form of this paper's argument, in a domain where it has been measured. | `Scoring_curated/2024_multilevel-anomaly-detection-benchmark.pdf` |
| `aharon2024fewshot` | A Classification-by-Retrieval Framework for Few-Shot Anomaly Detection to Detect API Injection Attacks | arXiv:2405.11247 | Scoring when labelled attack data is scarce — exactly the MCP situation. | `Scoring_curated/2024_few-shot-api-attack-anomaly-detection.pdf` |
| `wang2025probguard` | ProbGuard: Probabilistic Runtime Monitoring for LLM Agent Safety | arXiv:2508.00500 | DTMC over agent behaviour, probability of reaching an unsafe state. The probabilistic alternative to our ordinal score. | `6_Risk_Scoring/scoring/ProbGuard_...pdf` |
| `mou2026toolsafe` | ToolSafe: Enhancing Tool Invocation Safety via Proactive Step-Level Guardrail and Feedback | arXiv:2601.10156 | Pre-execution judgement over interaction history; the closest runtime analogue, still gate-shaped. | `6_Risk_Scoring/detection/ToolSafe_...pdf` |
| `andriushchenko2025agentharm` | AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents | ICLR 2025, arXiv:2410.09024 | HarmScore / RefusalRate; candidate threshold-tuning set. | `Scoring_curated/2024_AgentHarm-llm-agent-harmfulness-benchmark.pdf` |
| `zhang2024agentsafetybench` | Agent-SafetyBench: Evaluating the Safety of LLM Agents | arXiv:2412.14470 | 349 environments, 2,000 cases, 8 risk categories — a taxonomy our bands should map onto. | `Scoring_curated/2024_Agent-SafetyBench-llm-agent-safety.pdf` |
| `bradatsch2024zerotrust` | Zero Trust Score-Based Network-Level Access Control in Enterprise Networks | arXiv:2402.08299 | 29 trust attributes → Subjective-Logic numeric score → authorization decision. The architectural umbrella: compute a number, then decide. | `Scoring_curated/2024_zero-trust-score-network-access-control.pdf` |
| `paulraj2025criticalinfra` | Autonomous AI-Based Cybersecurity Framework for Critical Infrastructure | arXiv:2507.07416 | Couples vulnerability severity with asset criticality into one dynamic impact score — the closest published system to our static × dynamic product. | `Scoring_curated/2025_securing-critical-infrastructure-ai-era-framework.pdf` |

## M. Industry disclosures and vendor guidance

Non-academic, but load-bearing: two of the MCP attack classes the academic
literature now studies were named in blog posts months before the first paper.
Cite them for priority, not for evidence.

| Key | Source | Why it is here |
|---|---|---|
| `invariant2025toolpoisoning` | Invariant Labs, *MCP Security Notification: Tool Poisoning Attacks* (Apr 2025) | **Cited in §1.1.** The disclosure that named tool poisoning. Every later academic treatment traces here. |
| `owasp2025mcptop10` | OWASP Top 10 for MCP (2025) | **Cited in §1.1.** MCP-specific practitioner catalogue; MCP03 is tool poisoning. |
| `anthropic2024agents` | Anthropic, *Building Effective Agents* (Dec 2024) | The vendor's own framing of what agents do with tools — useful for the threat-model section. |
| `microsoft2026securingagents` | Microsoft Security Blog, *Securing AI Agents: When AI Tools Move from Reading to Acting* (Jun 2026) | Enterprise framing of the read→act transition; evidence the server-side concern is being taken up in industry. |
| `anthropic2024mcp`, `mcp2026spec` | Anthropic / MCP spec | Protocol primary sources (strand A). |
| `anthropic2025misalignment` | Anthropic, *Agentic Misalignment* (2025) | The goal-drift branch of the threat model (strand G). |

## Corrections to the local catalog

While resolving IDs against the arXiv API I found several titles in
`../Literature_review/pdf/Scoring_curated/README.md` that do not match the
published record. `refs.bib` uses the **arXiv titles**; the local README should
be fixed to match:

| ID | Local README says | Actual arXiv title |
|---|---|---|
| 2508.00500 | ProGuard — Proactive Runtime Enforcement of LLM Agent Safety via Probabilistic Model Checking | **ProbGuard**: Probabilistic Runtime **Monitoring** for LLM Agent Safety |
| 2507.07416 | Securing Critical Infrastructure in the AI Era — Automated AI-Based Security Framework | **Autonomous AI-based Cybersecurity Framework for Critical Infrastructure: Real-Time Threat Mitigation** |
| 2405.11247 | Few-Shot API Attack Anomaly Detection in a Classification-by-Retrieval Framework | **A Classification-by-Retrieval Framework for Few-Shot Anomaly Detection to Detect API Injection Attacks** |
| 2401.05144 | SARA — Sensitivity-Aware Relevance Assessments | SARA: **A Collection of** Sensitivity-Aware Relevance Assessments |
| 2108.09358 | CJA-RL — Crown Jewels Analysis using Reinforcement Learning with Attack Graphs | Crown Jewels Analysis using Reinforcement Learning with Attack Graphs (no "CJA-RL" in the title) |

Also: the 2512.06781 PDF is filed locally as
`2025_from-description-to-score-llm-cvss.pdf` per the README, but the actual
file in `6_Risk_Scoring/scoring/` is `From_Description_to_Score_...pdf`. Only
one copy is needed.

Two entries in `../Literature_review/risk_scoring_frameworks_survey.md`
(`SafePred`, and several arXiv IDs cited without a local PDF) could not be
resolved and are **not** in `refs.bib`. Verify them before citing.

## Second tier — read, not cited

Present in the local corpus and relevant, but cut to keep the reference list at
conference length. Pull any of these in if a reviewer asks for coverage:

- `MCPGuard: Automatically Detecting Vulnerabilities in MCP Servers` — implementation-level scanning.
- `TRUSTDESC` (arXiv:2604.07536) — trusted description generation against tool poisoning.
- `SEAgent` (arXiv:2601.11893) — mandatory access control for privilege escalation in agent systems.
- `AgentSpec` — customizable runtime enforcement.
- `ToolSafe` (arXiv:2601.10156) — step-level tool-invocation guardrail.
- `TraceAegis`, `SentinelAgent` — behavioural/graph anomaly detection over agent traces.
- `Mind the GAP` (arXiv:2602.16943) — text safety does not transfer to tool-call safety.
- `NIST SP 800-207` — zero-trust architecture; background for per-request evaluation.
- `MCPThreatHive` (arXiv:2604.13849) — composite threat risk scoring; found during the July 2026 sweep, not yet read in full.
- `STARS` (arXiv:2604.10286) — request-conditioned continuous-risk scoring for skill invocation. **Closest new competitor found in the sweep; read before the related-work section is written.**
- `Trust No Tool / VISTA-Guard` (arXiv:2605.17453) — final-action risk scoring over trajectories.

## Where the gap is

Reduced to one paragraph, for use in §1.2 and the related-work section:

> MCP defenses emit binary verdicts (strand D). Classical and AI-specific
> scoring systems score vulnerabilities or capabilities, not invocations, and
> are argument- and asset-blind (strand E). The MCP-specific scoring work that
> exists scores the server implementation (`kumar2026mcpinsos`), the tool
> (`betser2026agentrim`), or the log record after the fact (`fu2025riskcue`).
> The one work that reads text and emits an ordinal severity
> (`jafarikhah2026description`) scores CVE descriptions, not (tool, asset)
> pairs. **Across all of it, asset sensitivity is assumed to be given.** No
> prior work derives the sensitivity scale from the artifact an organization
> actually publishes — a classification policy in the FIPS 199 / SP 800-60
> mould (strand I) — and then validates the derived numbers against a
> held-out organizational inventory.
