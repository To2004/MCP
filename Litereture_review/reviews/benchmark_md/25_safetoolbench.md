# SafeToolBench

## Source
- **Paper:** SafeToolBench: Pioneering a Prospective Benchmark to Evaluating Tool Utilization Safety in LLMs (Xia et al., EMNLP 2025 Findings)
- **Link:** https://aclanthology.org/2025.findings-emnlp.958/
- **arXiv:** https://arxiv.org/abs/2509.07315
- **Year:** 2025

## Format & Size
- **Total samples:** 1,200 adversarial instructions — 600 single-app (SA) + 600 multi-app (MA), evenly split across 4 risk categories (300 each)
- **Format:** Structured JSON-like entries pairing natural-language user instructions with tool-call plans across 16 real-world application domains; each entry includes risk category label, API call sequences with parameters, and risk explanation
- **Availability:** arXiv / ACL Anthology (no public GitHub repository found as of March 2026)

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| User instruction | String (NL) | "Transfer all my savings to account X immediately" | Yes | Malicious or ambiguous natural-language request targeting one or more apps |
| App(s) | Categorical list | WeChat, Alipay, Bank, Uber, Google Drive, Taobao, etc. | Yes | 16 domains; SA uses 1 app, MA uses 2+ coordinated apps |
| API call sequence | Structured plan | `APP_name: [returned_args = api_name(#param1=value1, #param2=value2)]` | Partial | Tool-call plans with parameter bindings; 31-73 unique APIs across categories |
| Risk category | Categorical | Privacy Leak, Property Damage, Physical Injury, Bias & Offensiveness | Yes | 4 categories, 300 samples each (150 SA + 150 MA) |
| Risk explanation | String | Free-text justification of why the instruction is risky | Yes | Human-verified; useful as ground-truth rationale for risk scoring |
| Quality-control score | Integer (1-10) | 7, 8, 9, 10 | Yes | GPT-4o-assigned risk score; only samples scoring >= 7 retained after 3-annotator verification; ~30% of candidates discarded |
| Scenario type | Categorical | SA (single-app), MA (multi-app) | Yes | MA scenarios typically 10-20% easier to detect as risky |

## Proposed Risk Dimensions

### Agent Action Severity (v3 Dim 1)
- **Feeding columns:** Risk category, API call sequence, App(s)
- **Proposed scale:** 1-10
- **Derivation:** The 16 application domains provide natural severity calibration — Bank and Insurance API calls carry higher baseline severity than Weather or YouTube. The four risk categories (Privacy Leak, Property Damage, Physical Injury, Bias & Offensiveness) map directly to severity tiers: Physical Injury and Property Damage score 7-10, Privacy Leak scores 5-8, Bias & Offensiveness scores 3-6. The API call sequence reveals what operations are attempted (e.g., fund transfer vs. weather query), enabling fine-grained severity scoring within each domain. SafeToolBench's "Type of Operation" dimension (reversible vs. irreversible) from the SafeInstructTool framework directly feeds action severity assessment.

### Permission Overreach (v3 Dim 2)
- **Feeding columns:** API call sequence, App(s), User instruction, Scenario type
- **Proposed scale:** 1-10
- **Derivation:** Multi-app (MA) scenarios inherently involve cross-app permission escalation — an agent coordinating Alipay + WeChat is requesting broader access than single-app use. The "Alignment Between Instruction and Tool" dimension from SafeInstructTool detects mismatches where the agent requests tool access that does not match the stated task, a direct signal of permission overreach. The "Impact Scope of the Operation" dimension (individual vs. system-wide) maps to how far the requested permissions extend beyond minimum necessary access.

### Agent Compromise Indicator (v3 Dim 5)
- **Feeding columns:** User instruction, Risk explanation, Quality-control score, Risk category
- **Proposed scale:** 1-10
- **Derivation:** SafeToolBench's adversarial instructions simulate scenarios where the agent is being steered toward unsafe tool use — exactly the pattern a compromised agent would exhibit. The "Harmfulness of the Instruction" and "Urgency of the Instruction" dimensions from SafeInstructTool detect manipulation signals (malicious intent, artificial time pressure) that indicate hostile influence on the agent. The quality-control score (7-10 range for retained samples) provides a pre-computed severity baseline: higher-scored instructions represent more convincing adversarial steering, correlating with higher compromise likelihood. The "Data Sensitivity" dimension flags when the agent is being directed to access or exfiltrate sensitive information, a hallmark of compromised-agent behavior.

## Data Quality Notes
- No public GitHub repository has been released as of March 2026; data availability is limited to what is described in the paper and ACL Anthology supplementary materials. This significantly limits immediate reuse for training or automated pipeline integration.
- The benchmark was constructed using GPT-4o for instruction generation, API creation, and tool-call planning, with ~5% of tool plans requiring manual correction. This means the adversarial instructions may reflect GPT-4o's biases rather than real-world attacker patterns.
- The quality threshold (risk score >= 7, ~30% discard rate, 3-annotator verification) is rigorous and suggests high-quality retained samples, but the 1-10 quality score is conflated with risk severity — a "low quality" sample might actually represent a subtle, hard-to-detect attack that is more dangerous in practice.
- The 16 domains are heavily oriented toward Chinese consumer apps (WeChat, Alipay, Meituan, Taobao, CatEye) alongside global services (Google Calendar, Google Drive, YouTube, Uber). Domain transfer to enterprise MCP server contexts (databases, CI/CD pipelines, cloud infrastructure) would require mapping.
- SafeInstructTool's nine dimensions use a 0-3 point scale per dimension with a composite formula S = U + max(T_im + C_im), which would need to be rescaled to MCP-RSS's 1-10 scoring system.

## Usefulness Verdict
SafeToolBench's defining contribution to MCP-RSS is its **prospective** (pre-execution) safety evaluation paradigm. Unlike retrospective benchmarks that assess harm after tool execution, SafeToolBench evaluates whether an LLM can identify risky instructions *before* any tool is called. This directly mirrors MCP-RSS's proxy architecture, where the risk scoring engine sits between the agent and the MCP server and must score requests before forwarding them. The GPT-4o baseline achieving 83% safety score on identifying risky instructions provides a concrete performance target — MCP-RSS's scoring engine should aim to match or exceed this detection rate on equivalent threat categories. The gap (17% miss rate) also quantifies the residual risk that MCP-RSS must account for through defense-in-depth mechanisms.

The SafeInstructTool framework's nine dimensions across three perspectives (User Instruction, Tool Itself, Joint Instruction-Tool) provide a complementary decomposition to MCP-RSS's v3 server-defense dimensions. Several SafeInstructTool dimensions map cleanly: "Type of Operation" and "Impact Scope" feed Agent Action Severity (Dim 1), "Alignment Between Instruction and Tool" feeds Permission Overreach (Dim 2), and "Data Sensitivity" plus "Key Sensitivity" feed Data Exfiltration Risk (Dim 3). The composite scoring formula S = U + max(T_im + C_im) demonstrates one approach to aggregating multi-dimensional risk into a single score, which MCP-RSS can study as a reference design even if the final formula differs.

The primary limitation for MCP-RSS integration is the consumer-app orientation of the 16 domains. MCP servers typically expose infrastructure tools (database queries, file system operations, API orchestration), not mobile-app workflows. However, the risk *categories* (Privacy Leak, Property Damage, Physical Injury, Bias & Offensiveness) and the underlying safety *dimensions* (data sensitivity, operation reversibility, impact scope) are domain-agnostic and transfer directly. SafeToolBench is best used as a conceptual alignment validator — confirming that MCP-RSS's scoring approach is consistent with the only published prospective tool-safety benchmark — rather than as a direct training data source.
