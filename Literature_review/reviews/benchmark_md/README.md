# Benchmark Analysis for Multi-Dimensional MCP Risk Scoring

Analysis of 74 benchmarks and datasets from the MCP security literature, evaluating which ones
can feed into a **multi-dimensional 1-10 risk scoring system** for MCP tool/agent access.

18 entries were selected as relevant. 56 were skipped. Each analysis file covers data structure,
proposed risk dimensions, quality notes, and a usefulness verdict.

This folder now also includes a small set of **internet-sourced emerging additions** verified on
**2026-03-30**. These are separated from the original 18 because they were added after the main
literature sweep and are not all mature enough to count as core benchmark evidence.

---

## Analyzed Benchmarks (18)

### Tier 1 — MCP-Specific, Directly Usable

| # | File | Benchmark | Source | Samples |
|---|------|-----------|--------|---------|
| 1 | [01_mcip_bench.md](01_mcip_bench.md) | MCIP-Bench | Jing et al., 2025 | 2,218 instances, 10 risk types |
| 2 | [02_mcip_guardian_training.md](02_mcip_guardian_training.md) | MCIP Guardian Training | Jing et al., 2025 | 13,830 instances, 11 categories |
| 3 | [03_mcp_attackbench.md](03_mcp_attackbench.md) | MCP-AttackBench | Xing et al., 2025 | 70,448 samples, 3 attack families |
| 4 | [04_mcptox.md](04_mcptox.md) | MCPTox Dataset | Wang et al., 2025 | 1,312-1,497 cases, 45 real servers |
| 5 | [05_mcpsecbench.md](05_mcpsecbench.md) | MCPSecBench Playground | Yang et al., 2025 | 17 types x 4 surfaces |
| 6 | [06_mcp_safetybench.md](06_mcp_safetybench.md) | MCP-SafetyBench | Zong et al., 2025 | 5 domains x 20 types x 13 models |
| 7 | [07_mcp_server_database.md](07_mcp_server_database.md) | MCP Server Database | Zhao et al., 2025 | 1,360 servers, 12,230 tools |
| 8 | [08_component_attack_poc.md](08_component_attack_poc.md) | Component-based Attack PoC | Zhao et al., 2025 | 132 servers, 12 categories |
| 9 | [09_mcp_server_dataset_67k.md](09_mcp_server_dataset_67k.md) | MCP Server Dataset (67K) | Li & Gao, 2025 | 67,057 servers, 44,499 tools |
| 10 | [10_mcp_itp_implicit_poisoning.md](10_mcp_itp_implicit_poisoning.md) | MCP-ITP Implicit Poisoning | Li et al., 2026 | 548 cases x 12 models |

### Tier 2 — Agent/Tool Security, Transferable to MCP

| # | File | Benchmark | Source | Samples |
|---|------|-----------|--------|---------|
| 11 | [11_nvd_cvss.md](11_nvd_cvss.md) | NVD/CVE + CVSS v3.1 | Jafarikhah et al., 2026 | 31,000+ CVEs, 8 base metrics |
| 12 | [12_r_judge.md](12_r_judge.md) | R-Judge Records | Yuan et al., 2024 | 569 records, 10 risk types |
| 13 | [13_agentdojo.md](13_agentdojo.md) | AgentDojo Task Suites | Debenedetti et al., 2024 | 97 tasks + 629 injections |
| 14 | [14_injecagent.md](14_injecagent.md) | InjecAgent Dataset | Zhan et al., 2024 | 1,054 test cases |
| 15 | [15_meta_tool_use_pi.md](15_meta_tool_use_pi.md) | Meta Tool-Use PI Benchmark | Chennabasappa et al., 2025 | 600 scenarios (300/300) |
| 16 | [16_asb.md](16_asb.md) | ASB (Agent Security Bench) | Zhang et al., 2025 | 6 attack prompt types |
| 17 | [17_miniscope.md](17_miniscope.md) | MiniScope Permissions | Zhu et al., 2025 | 10 apps, permission hierarchies |
| 18 | [18_indirect_pi_attack.md](18_indirect_pi_attack.md) | Indirect PI Attack Dataset | Rall et al., 2025 | 1,068 instances, 28 models |

---

## Internet-Sourced Emerging Additions (4)

These were added from primary web sources after the original review pass. They are useful, but they
should be treated as **supplementary evidence** rather than the backbone of the scoring system.

| # | File | Resource | Type | Why it matters |
|---|------|----------|------|----------------|
| 19 | [19_mcpshield.md](19_mcpshield.md) | MCPShield | Defense benchmark | Recent arXiv benchmark framing 6 attack scenarios across 6 agentic LLMs; strong lifecycle-defense relevance |
| 20 | [20_dvmcp.md](20_dvmcp.md) | Damn Vulnerable MCP Server (DVMCP) | Practical benchmark / lab | 10 runnable attack challenges focused on MCP exploitation, including code execution and remote access |
| 21 | [21_audit_db.md](21_audit_db.md) | audit-db | Structured audit corpus | Community schema for reproducible MCP server audits with manifests, findings, and severity indexes |
| 22 | [22_vulnerability_db.md](22_vulnerability_db.md) | vulnerability-db | Vulnerability intelligence feed | OSV-style MCP advisory repository useful for deployment-time risk enrichment |

### How To Treat These Additions

- **MCPShield** is the strongest new academic addition.
- **DVMCP** is best for demos, smoke tests, and attack walkthroughs, not training.
- **audit-db** and **vulnerability-db** are best treated as future-facing structured evidence feeds.
- These additions do **not** overturn the original ranking that MCP-AttackBench, MCPSecBench, MCPTox,
  MCP Server Database, and MCP Server Dataset 67K are the main pillars of the scoring framework.

---

## Added from ToolSafe Reference Scan (4)

Added on **2026-04-14** after tracing the four agent-safety datasets cited by ToolSafe
(Mou et al., 2026, arXiv 2601.10156) as its basis for the 2-dimensional unsafe-tool-invocation
taxonomy (triggering cause × manifestation → MUR / PI / HT / BTRA). These are general-agent
benchmarks, not MCP-specific — treat as supporting methodology/training evidence, not as
core MCP coverage.

| # | File | Benchmark | Source | Samples |
|---|------|-----------|--------|---------|
| 23 | [23_agentharm.md](23_agentharm.md) | AgentHarm | Andriushchenko et al., 2024 | 110 tasks (440 with augmentations), 104 tools, 11 harm categories |
| 24 | [24_agent_safetybench.md](24_agent_safetybench.md) | Agent-SafetyBench | Zhang et al., 2024 | 2,000 test cases, 349 environments, 8 risk categories, 10 failure modes |
| 25 | [25_agentalign.md](25_agentalign.md) | AgentAlign | Zhang et al., 2025 | 4,956 harmful + 9,783 benign instructions with paired variants |
| 26 | [26_ts_bench.md](26_ts_bench.md) | TS-Bench (ToolSafe) | Mou et al., 2026 | ~7,188 labeled trajectories (AgentHarm-Traj 731, ASB-Traj 5,237, AgentDojo-Traj 1,220) |
| 27 | [27_assebench.md](27_assebench.md) | ASSEBench (AgentAuditor) | Luo et al., 2025 | 2,293 annotated records, 29 scenarios, 15 risk types, dual strict/lenient labels |
| 28 | [28_os_safe.md](28_os_safe.md) | OS-Safe (AGrail) | Luo et al., 2025 (ACL) | Step-level web/code execution annotations; task-specific vs. systemic risk split |
| 29 | [29_shieldagent_bench.md](29_shieldagent_bench.md) | ShieldAgent-Bench | Chen et al., 2025 | 960 instructions + 3,110 unsafe trajectories across 6 web environments, 7 risk categories |

### How To Treat These Additions

- **TS-Bench (#26)** is the most directly relevant to the project: its 2×2 taxonomy
  (MUR/PI × HT/BTRA) and three-way safety label (safe/controversial/unsafe) map cleanly
  onto the project's static vs. dynamic modes and gate/throttle/deny tiering.
- **Agent-SafetyBench (#24)** is the most directly usable of the three raw datasets —
  its 8 risk categories and 10 failure modes feed the v3 Agent Action Severity and Agent
  Compromise Indicator dimensions.
- **AgentAlign (#25)** is the training-data asset (~15K instructions) with paired
  benign/harmful variants; use for sequence-aware classifier fine-tuning.
- **AgentHarm (#23)** was previously marked "skipped" as binary-only; re-included here
  as a deny-always floor for calibration and as the raw source behind ToolSafe's
  `AgentHarm-Traj` annotated split.
- **ASSEBench (#27)** provides **dual strict/lenient labels** — the clearest signal
  for calibrating the gate/throttle/deny middle band.
- **OS-Safe (#28)** is the OS-primitive step-level complement to TS-Bench; strong for
  MCP servers exposing filesystem or shell tools, weak on BTRA coverage.
- **ShieldAgent-Bench (#29)** is the **policy-grounded** benchmark — every unsafe
  label traces to a verifiable policy rule, making it the best source for training
  explainable deny decisions and setting efficiency targets (ShieldAgent's 90.1%
  recall, 64.7% fewer API queries, 58.2% lower latency).

### Coverage Matrix Across the ToolSafe-Referenced Benchmarks

Per the 2×2 taxonomy (triggering cause × manifestation) from the ToolSafe paper
(Mou et al., 2026):

| Benchmark | Annotation Level | Monitored Behavior | MUR | PI | HT | BTRA |
|---|---|---|:---:|:---:|:---:|:---:|
| R-Judge (#12) | Trajectory | tool calls | ✓ | ✓ | — | ✓ |
| ASSEBench (#27) | Trajectory | tool calls | ✓ | ✓ | — | ✓ |
| OS-Safe (#28) | Step | web / code execution | ✓ | ✓ | ✓ | — |
| ShieldAgent-Bench (#29) | Step | web browsing | ✓ | ✓ | — | — |
| TS-Bench (#26) | Step | tool calls | ✓ | ✓ | ✓ | ✓ |

**Only TS-Bench covers all four patterns at step granularity.** For full coverage the
project should combine TS-Bench (training + 2×2 completeness) with ShieldAgent-Bench
(policy grounding) and OS-Safe (OS-primitive severity for filesystem/shell MCP tools).

---

## Skipped Benchmarks & Datasets (52)

| Category | Entries | Reason |
|----------|---------|--------|
| **Redundant with included** | ProtoAMP, AttestMCP, MCLIB, MCPShield Eval Suite, MCPSafetyScanner, MCP Attack Benchmark (Beyond Protocol) | Attack data or defense evaluation already captured by the datasets they draw from |
| **Binary-only output** | AgentHarm, HarmBench, JailbreakBench, BIPIA | Measure attack success as yes/no — no multi-dimensional structure for graduated scoring |
| **Utility benchmarks** | BFCL-v3, WebArena, AgentBench, HELM | Measure task completion and model capability, not risk — useful for evaluating utility cost of risk scoring but not as risk data sources |
| **Too general / tangential** | ShareGPT, WildChat, glaive-function-calling-v2, ToolACE, ToolBench, MetaTool, CyberSecEval3, AlpacaFarm, CIAQA, CrAIBench, Anthropic Red-Teaming | General LLM data or niche domains without structured risk labels transferable to MCP scoring |
| **Ecosystem stats only** | MCP Server Registry (1,899 repos), MCP Empirical (1,899 repos), MCP API Usage (2,117 repos), MCP Ecosystem (8,401 projects), Top-296 MCP Servers | Ecosystem census data — useful for context but lack risk labels or scoring structure |
| **Too small / qualitative** | Malicious MCP (4 servers), Damn Vulnerable MCP (10 servers), Log-To-Leak, MCPSafetyScanner Test, MCP-ITP test scenarios | Useful for smoke testing but too small or qualitative for training/calibrating a risk scorer |
| **Covered by included** | RAS-Eval, EICU-AC, Mind2Web-SC, AgentDojo defense variants | Risk structures already captured by more complete included entries |
| **Non-MCP scoring frameworks** | DecodingTrust, TrustLLM, Trust Paradox, Synthetic PI, ToolSword, SafeToolBench | General LLM trustworthiness or tool-safety frameworks not specific to MCP — methodology insights absorbed into v3 dimensions |

---

## Unified Risk Dimensions Across All Benchmarks

### Original 11 Benchmark-Derived Dimensions

These are the risk dimensions that the analyzed data **actually supports** — derived from what's in the
benchmarks, not forced onto them.

| Dimension | Proposed Scale | Description | Primary Data Sources | How to Derive |
|-----------|---------------|-------------|---------------------|---------------|
| **Attack Surface** | 1-10 | Which layer is targeted (client/protocol/server/host) | MCPSecBench (#5), MCP-SafetyBench (#6) | Map 4 surfaces to severity tiers: protocol=10, server=7, client=5, host=4 (based on ASR) |
| **Attack Severity** | 1-10 | How dangerous the attack is if successful | NVD/CVSS (#11), MCP-AttackBench (#3) | Adapt CVSS base score methodology; map 3 attack families to severity bands |
| **Risk Type** | Categorical → 1-10 | Which of 10 MCP-specific risk categories applies | MCIP-Bench (#1), R-Judge (#12) | 10 risk types each mapped to severity weight based on potential impact |
| **Tool Toxicity** | 1-10 | How poisoned/manipulated a tool description is | MCPTox (#4), MCP-ITP (#10) | Combine paradigm difficulty (explicit=3, implicit-func=6, implicit-param=8) with detection rate |
| **Data Exposure** | 1-10 | Risk of data leakage through tool access | MCP Server Database (#7), InjecAgent (#14) | EIT/PAT/NAT classification weighted by exploit chain probability (27.2% of servers expose combos) |
| **Trust Calibration** | 1-10 | Agent capability vs actual trustworthiness gap | MCP-SafetyBench (#6), R-Judge (#12) | Behavioral drift across multi-turn interactions; higher capability = higher scrutiny needed |
| **Trustworthiness** | 1-10 | Multi-dimensional agent/model trustworthiness | MCP-SafetyBench (#6), ASB (#16) | Composite of safety sub-dimensions derived from MCP-specific evaluation |
| **Protocol Amplification** | 1-10 | How much MCP architecture amplifies attack success | MCPSecBench (#5), Component PoC (#8) | Scale +23-41% amplification factor; protocol features present = higher score |
| **Permission Scope** | 1-10 | Over-privilege level of requested permissions | MiniScope (#17), MCP Server Dataset 67K (#9) | Ratio of requested permissions to minimum needed; 17 avg permissions/server as baseline |
| **Injection Resilience** | 1-10 | Resistance to prompt injection variations | AgentDojo (#13), Indirect PI (#18) | Inverse of ASR across variation types; 12 obfuscation techniques as coverage check |
| **Input Manipulation** | 1-10 | Sophistication of prompt-level attacks | ASB (#16), Meta Tool-Use PI (#15) | 6 attack types + 7 injection techniques scored by evasion sophistication |

### Current v3 Server-Defense Dimensions (refined from the 11 above)

The original 11 were refined through three iterations (11→8→7→6) to align with the project's
server-defense framing: **"protects MCP servers from malicious or risky agent behavior."**
Every dimension must answer: **"How does this agent threaten MY server?"**

| # | Dimension | Scale | Server's Question | Absorbs | Grade |
|---|-----------|-------|------------------|---------|-------|
| 1 | **Agent Action Severity** | 1-10 | How dangerous is this request to my resources? | Attack Type + Severity + Surface + Protocol Amp | A |
| 2 | **Permission Overreach** | 1-10 | Is the agent requesting more access than needed? | Permission Scope | B+ |
| 3 | **Data Exfiltration Risk** | 1-10 | How much of my sensitive data is at risk? | Data Exposure (session-aware) | A |
| 4 | **Cross-Tool Escalation** | 1-10 | Is this session showing escalating threat patterns? | Trust Calibration temporal data | B+ |
| 5 | **Agent Compromise Indicator** | 1-10 | Is this agent acting under hostile influence? | Tool Toxicity + Injection Resilience + Input Manipulation (**reframed**) | A |
| 6 | **Resource Consumption Risk** | 1-10 | Is this agent abusing my server resources? | NEW (rule-based) | D |
| Mod | **Agent Trust Modifier** | 0.7-1.4× | How much should I trust this agent? | Trustworthiness + Trust Calibration | A |

Full specification: [`dimension_refinement_v3_server_defense.md`](../dimension_refinement_v3_server_defense.md)

---

## How to Use This Analysis

1. **Use the v3 dimensions** — The table above shows both the original 11 and the refined 6+1.
   Use the v3 set for implementation — every dimension is server-defense aligned.

2. **Get training data** — MCIP Guardian (#2, 13,830 samples) and MCP-AttackBench (#3, 70,448 samples)
   are the largest labeled datasets for training the Agent Action Severity classifier.

3. **Adopt scoring methodology** — CVSS v3.1 (#11) is the proven multi-dimensional scoring template.
   Adapt its formula for MCP-specific dimensions.

4. **Evaluate your scorer** — AgentDojo (#13), MCPSecBench (#5), and MCPTox (#4) are the standard
   evaluation benchmarks. Include them for credibility.

5. **Calibrate base rates** — MCP Server Dataset 67K (#9) and MCP Server Database (#7) provide
   ecosystem-scale statistics for setting risk priors.

---

## File Structure

Each analysis file follows this template:
1. **Source** — paper, authors, link, year
2. **Format & Size** — sample count, format, availability
3. **Data Structure** — field-by-field breakdown with types, examples, usability
4. **Proposed Risk Dimensions** — how the data maps to 1-10 scoring with derivation logic
5. **Data Quality Notes** — limitations, missing values, caveats
6. **Usefulness Verdict** — practical assessment for multi-dimensional risk scoring

## Related Files

- [../benchmarks_review.md](../benchmarks_review.md) — Full 24-benchmark literature review
- [../datasets_review.md](../datasets_review.md) — Full 50-dataset literature review
- [../paper_summaries/](../paper_summaries/) — Detailed paper summaries (Hebrew)
- [../client_server_attack_dimension_framework.md](../client_server_attack_dimension_framework.md) — Client→Server Attack Dimension Framework (6 dims + modifier derived from 12 attack benchmarks)
- [../dimension_refinement_v3_server_defense.md](../dimension_refinement_v3_server_defense.md) — Server-Defense Dimension Refinement v3 (6 dims + modifier)
- [../benchmark_dimension_set_server_attack.md](../benchmark_dimension_set_server_attack.md) — Benchmark-Backed Server-Attack Dimension Set (5 dims + modifier)
- [../benchmark_refinement_server_attack_columns.md](../benchmark_refinement_server_attack_columns.md) — Server-Attack Signal Extraction (column-level detail from 7 core benchmarks)
