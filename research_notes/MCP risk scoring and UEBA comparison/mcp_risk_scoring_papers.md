# Academic works that compute MCP risk scores (2024 – November 2026)

These notes list every academic or preprint work I could verify that produces a risk score, grade, rank or risk level for MCP servers, tools, parameters, calls or sessions. For each work they record the threat direction, the scoring method, the inputs, the evaluation and the limitations, and compare it with our framework. Here the MCP server is the protected asset and the calling agent is the threat. A static layer scores tools from policy-derived asset sensitivity and 1–5 levels per input. A dynamic layer scores each call as cell × likelihood × escalation, with a floor, times a behaviour multiplier of x0.7–5. It runs behind an observe-only gateway with a tamper-evident log. Every paper was checked against its arXiv abstract page or ACL Anthology PDF on 2026-11-04. Formula details come from the full HTML or PDF.

## 1. Which works produce an MCP risk score, grade, rank or level? (citation, date, venue, code)

### Takeaway

The second pass verified **30 in-scope works**. **21 (Tier A)** compute a numeric score or an ordinal risk level. **9 (Tier B)** give a categorical risk class, grade, rank or threshold decision without a numeric score. All date from **April 2025 – November 2026**. I found no MCP risk-scoring work from 2024 (MCP launched November 2024). Only four have a peer-reviewed venue: IEEE S&P 2026, EMNLP 2025, ACL 2026 Industry and the journal JISA. The rest are arXiv preprints.

### Cited Findings

#### Tier A: numeric score or ordinal risk level (21)

| # | Work (authors, date) | Venue / status | Unit scored | Code / data |
|---|---|---|---|---|
| A1 | **MCP-in-SoS**: Kumar, Guirao Aguilera, Srikanteswara, Misra, Tayeen (2026-03-10) — [arXiv:2603.10194](https://arxiv.org/abs/2603.10194) | preprint | CWE weakness and repository (server) | Release of pipeline, Joern queries and metadata promised in "Open Science" section — [Source](https://arxiv.org/html/2603.10194) |
| A2 | **MCPThreatHive**: Shen, Toyoda, Leung (2026-04-15) — [arXiv:2604.13849](https://arxiv.org/abs/2604.13849) | DEF CON SG 2026 Demo Labs white paper | threat-intel item / MCP-38 threat class | [github.com/VulcanLab/MCPThreatHive](https://arxiv.org/html/2604.13849) |
| A3 | **MCP threat modeling with STRIDE + DREAD**: C. Huang, X. Huang, Tran, Fard (2026-03-23) — [arXiv:2603.22489](https://arxiv.org/abs/2603.22489) | preprint | threat (57 threats, 5 components) | not stated |
| A4 | **Security threat modeling for MCP, A2A, Agora, ANP**: Anbiaee, Rabbani, Mirani, Piya, Opushnyev, Ghorbani, Dadkhah (2026-02-11) — [arXiv:2602.11327](https://arxiv.org/abs/2602.11327) | *J. Information Security and Applications* 2026, Art. 104645 | protocol-level risk × lifecycle phase | not stated |
| A5 | **mcp-sec-audit** ("Auditing MCP Servers for Over-Privileged Tool Capabilities"): C. Huang, X. Huang, Fard (2026-03-23) — [arXiv:2603.21641](https://arxiv.org/abs/2603.21641) | preprint (tool paper) | server / tool capabilities | [github.com/nyit-vancouver/mcp-sec-audit](https://arxiv.org/html/2603.21641) |
| A6 | **Same Name, Different Server** (registry census): Kraishan (2026-09-12) — [arXiv:2609.14119](https://arxiv.org/abs/2609.14119) | preprint | server severity score | anonymized artifact released — [Source](https://arxiv.org/abs/2609.14119) |
| A7 | **Rethinking MCP Security / MCPZoo**: P. Chen, An, Wu, Wan, Hong, J. Chen, Pan, Dai, M. Yang (2026-07-13) — [arXiv:2607.11086](https://arxiv.org/abs/2607.11086) | preprint (extends [arXiv:2512.15144](https://arxiv.org/abs/2512.15144)) | tool capability risk level; evaluates scanners' server risk flags | public query interface — [Source](https://arxiv.org/abs/2607.11086) |
| A8 | **FlowGuard**: An, P. Chen, Hong, Y. Chen, Wu (2026-07-16) — [arXiv:2607.14754](https://arxiv.org/abs/2607.14754) | preprint | parameter risk score/vector, then findings | not stated |
| A9 | **Exposed by Design / Corvus**: Padilla (2026-07-31) — [arXiv:2608.00150](https://arxiv.org/abs/2608.00150) | preprint | internet-facing server priority score; finding confidence & severity | Corvus released open source — [Source](https://arxiv.org/abs/2608.00150) |
| A10 | **MCPShield** (security cognition layer): Z. Zhou, Y. Zhang, Cai, Aloqaily, Bouachir, Pang, Mehrotra, K. Wang et al. (2026-02-15) — [arXiv:2602.14281](https://arxiv.org/abs/2602.14281) | preprint | server deny score; drift judgment | not stated |
| A11 | **MCP-Guard**: Xing, Qi, Qin, Li, Chang, Yu, Lin, Xie et al. (2025-08-14) — [arXiv:2508.10991](https://arxiv.org/abs/2508.10991) | preprint | per-request malicious probability | MCP-AttackBench (70,448 samples) introduced — [Source](https://arxiv.org/abs/2508.10991) |
| A12 | **ShieldMCP** ("Securing the Tool Layer"): Yergattikar (2026) — [ACL Anthology 2026.acl-industry.58](https://aclanthology.org/2026.acl-industry.58/) | ACL 2026 Industry Track, pp. 865–871 | tool-description score; call/response alerts | open-source proxy per related talk (not verified) |
| A13 | **AgentTrust**: C. Yang (2026-05-06) — [arXiv:2605.04785](https://arxiv.org/abs/2605.04785) | preprint | per-call risk level + verdict | [github.com/chenglin1112/AgentTrust](https://arxiv.org/html/2605.04785) (AGPL-3.0; ships an MCP server) |
| A14 | **ConLeash** ("Options, Not Clicks: Lattice Refinement for Consent-Driven MCP Authorization"): Y. Li, Y. Chen, P. Wang, Khabra, Shezan, Feng, Tian (2026-05-12) — [arXiv:2605.11360](https://arxiv.org/abs/2605.11360) | preprint | per-call point in a risk lattice | ConsentBench (984 traces) — [Source](https://arxiv.org/abs/2605.11360) |
| A15 | **Zero-trust tool registry vs tool squatting**: Narajala, K. Huang, Habler (2025-04-28) — [arXiv:2504.19951](https://arxiv.org/abs/2504.19951) | preprint | per-tool dynamic trust score | not stated |
| A16 | **Governed MCP**: D. Son (2026-04-18) — [arXiv:2604.16870](https://arxiv.org/abs/2604.16870) | preprint (companion to ProbeLogits [arXiv:2604.11943](https://arxiv.org/abs/2604.11943)) | per-call safety score + calling-agent trust tier | not stated |
| A17 | **ChainWatch**: Narayan, Jyoti, Singh (2026-07-20) — [arXiv:2607.19432](https://arxiv.org/abs/2607.19432) | preprint | per-call features → session kill-chain stage → alert | not stated |
| A18 | **AegisMCP**: Zhan, Al Sadi, Li, Haddadi (2025-10-22) — [arXiv:2510.19462](https://arxiv.org/abs/2510.19462) | preprint | per-edge and per-session graph scores | not stated |
| A19 | **SecMCP** ("Quantifying Conversation Drift in MCP via Latent Polytope"): H. Shi, Yao, Shao, Jiao, Peng, Qin, C. Wang (2025-08-08) — [arXiv:2508.06418](https://arxiv.org/abs/2508.06418) | preprint | per-query drift distance | not stated |
| A20 | **Task-Conditioned Least-Privilege Learning for Terminal and MCP Agents**: A. Tu, M. Tu (2026-08-18) — [arXiv:2608.18351](https://arxiv.org/abs/2608.18351) | submitted to IEEE | per-action six-dimension audit; trajectory excess-privilege value | not stated |
| A21 | **Semantic Attacks on Tool-Augmented LLMs** (descriptor-level manipulation): Jamshidi, Dakhel, Nafi, Khomh (2025-12-06) — [arXiv:2512.06556](https://arxiv.org/abs/2512.06556) | preprint | system-level aggregate risk score (evaluation metric) | not stated |

#### Tier B: categorical risk class, grade, rank or threshold decision (9)

| # | Work (authors, date) | Venue / status | Output | Code / data |
|---|---|---|---|---|
| B1 | **MCIP**: Jing, H. Li, W. Hu, Q. Hu, Xu, Chu, P. Hu, Song (2025-05-20) — [arXiv:2505.14590](https://arxiv.org/abs/2505.14590) | EMNLP 2025 | unsafe or safe + fine-grained risk category for an MCP interaction | [github.com/HKUST-KnowComp/MCIP](https://arxiv.org/html/2505.14590) |
| B2 | **Parasites in the Toolchain (MCP-UPD / MCP-SEC)**: Zhao, Hou, Zhan, Y. Wang, Xie, Guo, L. Chen, S. Li et al. (2025-09-08) — [arXiv:2509.06572](https://arxiv.org/abs/2509.06572) | IEEE S&P 2026 | tool risk-capability class (EIT/PAT/NAT); high-risk server list | not stated |
| B3 | **MCP-RiskCue** ("Can LLM Infer Risk Information From MCP Server System Logs?"): Fu, Y. Zhang, Y. Wang (2025-11-08) — [arXiv:2511.05867](https://arxiv.org/abs/2511.05867) | preprint | log → one of 9 risk categories | [github.com/PorUna-byte/MCP-RiskCue](https://arxiv.org/abs/2511.05867) |
| B4 | **We Urgently Need Privilege Management in MCP**: Z. Li, K. Li, Ma, Xu, Y. Zhang, Cheng (2025-07-05) — [arXiv:2507.06250](https://arxiv.org/abs/2507.06250) | preprint | resource-access taxonomy; high-risk API usage per server | not stated |
| B5 | **Don't believe everything you read** (description–code inconsistency): Z. Li, Ma, Dai, Xu, Y. Zhang, Yan, K. Li (2026-02-03) — [arXiv:2602.03580](https://arxiv.org/abs/2602.03580) | preprint | 4-level consistency grade (Full / Mostly / Partial / Rare match) | not stated |
| B6 | **AEGIS: Preventing Cross-Domain Resource Abuse in MCP**: Priya, Taylor, Araujo (2026-08-20) — [arXiv:2608.20481](https://arxiv.org/abs/2608.20481) | preprint | per-parameter threshold policy (allow/deny) from a tool ontology | not stated |
| B7 | **My Credentials, Please** (MCP-FSD, filesystem capability laundering): Z. Huang, Tang, Guan, Sun, He (2026-10-15) — [arXiv:2610.22301](https://arxiv.org/abs/2610.22301) | preprint | per-server/tool capability-gap class (L1–L3) | not stated |
| B8 | **When Neither Side Confirms** (destructive tool approval): Yao, Z. Yang, Z. Wang, Zhou, Ye (2026-11-02) — [arXiv:2611.02527](https://arxiv.org/abs/2611.02527) | preprint | destructive / non-destructive tool class; approval coverage | not stated |
| B9 | **MindGuard**: Z. Wang, Du, Shi, J. Zhang, Cheng, Yao, Guo, X.-Y. Li (2025-08-28) — [arXiv:2508.20412](https://arxiv.org/abs/2508.20412) | preprint | per-call poisoning flag from attention-graph edge weights | not stated |

#### Seen, out of scope for me (no risk score, attack/benchmark only, or not MCP-specific)

- *MCP scanners/detectors with binary or finding-list output, no risk score:* MCPInspect / "A First Look at the Security Issues in the MCP Ecosystem" (DSN 2026, title changed from "Toward Understanding…") [2510.16558](https://arxiv.org/abs/2510.16558); MCPSec no-box analysis [2609.10854](https://arxiv.org/abs/2609.10854); DCIChecker [2606.04769](https://arxiv.org/abs/2606.04769); MCPPrivacyDetector [2606.21338](https://arxiv.org/abs/2606.21338); MCP-BiFlow [2605.07836](https://arxiv.org/abs/2605.07836); VIPER-MCP [2605.21392](https://arxiv.org/abs/2605.21392); Connor [2604.01905](https://arxiv.org/abs/2604.01905); ML detection of MCP attacks [2604.10534](https://arxiv.org/abs/2604.10534); MCP Safety Audit / McpSafetyScanner [2504.03767](https://arxiv.org/abs/2504.03767); MCP at First Glance [2506.13538](https://arxiv.org/abs/2506.13538); MCP Pitfall Lab / MCP-BOM [2604.21477](https://arxiv.org/abs/2604.21477); SpellSmith [2607.07461](https://arxiv.org/abs/2607.07461); SandScope / MCP-SandboxScan [2601.01241](https://arxiv.org/abs/2601.01241); MICRYSCOPE crypto misuse [2512.03775](https://arxiv.org/abs/2512.03775); AgentBound permission manifests (FSE 2026) [2510.21236](https://arxiv.org/abs/2510.21236); Agent Audit [2603.22853](https://arxiv.org/abs/2603.22853); MCPGuard survey [2510.23673](https://arxiv.org/abs/2510.23673); MCP-SecLint (DTU Orbit PDF, ACM DOI 10.1145/3806007.3810961; venue not verified) [PDF](https://backend.orbit.dtu.dk/ws/portalfiles/portal/452703195/3806007.3810961.pdf).
- *MCP attacks / benchmarks:* MCPTox [2508.14925](https://arxiv.org/abs/2508.14925); MSB (ICLR 2026) [2510.15994](https://arxiv.org/abs/2510.15994); MCPSecBench [2508.13220](https://arxiv.org/abs/2508.13220); MCPXKIT/MCPLIB (TDSC) [2508.12538](https://arxiv.org/abs/2508.12538); Beyond the Protocol [2506.02040](https://arxiv.org/abs/2506.02040); When MCP Servers Attack [2509.24272](https://arxiv.org/abs/2509.24272); MCP-ITP [2601.07395](https://arxiv.org/abs/2601.07395); ShareLock [2606.27027](https://arxiv.org/abs/2606.27027); A2M [2609.26761](https://arxiv.org/abs/2609.26761); function hijacking [2604.20994](https://arxiv.org/abs/2604.20994); MCP-TDP "When the Manual Lies" [2605.24069](https://arxiv.org/abs/2605.24069); COPEX [2610.04378](https://arxiv.org/abs/2610.04378); implicit trust in tool-calling pipelines [2609.18217](https://arxiv.org/abs/2609.18217); TrustShiftProbe [2608.23763](https://arxiv.org/abs/2608.23763); Breaking the Protocol / MCPBench [2601.17549](https://arxiv.org/abs/2601.17549); clause-compliance abuse [2603.10163](https://arxiv.org/abs/2603.10163); MCP tool poisoning cross-framework (AISec '26) [2611.03555](https://arxiv.org/abs/2611.03555); MCP Safety Training [2505.23634](https://arxiv.org/abs/2505.23634); RAG-Pref (CAMLIS 2026) [2605.11217](https://arxiv.org/abs/2605.11217); GatewayBench [2610.23449](https://arxiv.org/abs/2610.23449); BARBICAN gateway attribution [2610.33198](https://arxiv.org/abs/2610.33198).
- *MCP measurement, taxonomy, governance, authorization (no score):* MCP-38 taxonomy [2603.18063](https://arxiv.org/abs/2603.18063); MCP-DPT [2604.07551](https://arxiv.org/abs/2604.07551); OWASP MCP Top 10 three-tier mapping [2611.02611](https://arxiv.org/abs/2611.02611); formal framework (also named "MCPSHIELD") [2604.05969](https://arxiv.org/abs/2604.05969); Hou et al. landscape [2503.23278](https://arxiv.org/abs/2503.23278); MCP measurement study [2509.25292](https://arxiv.org/abs/2509.25292); remote-MCP auth measurement [2605.22333](https://arxiv.org/abs/2605.22333); registry drift [2608.00997](https://arxiv.org/abs/2608.00997); random registry draw [2609.10962](https://arxiv.org/abs/2609.10962); remote MCP centralization [2609.19100](https://arxiv.org/abs/2609.19100); Errico et al. governance [2511.20920](https://arxiv.org/abs/2511.20920); enterprise-grade MCP security [2504.08623](https://arxiv.org/abs/2504.08623); MCP Guardian [2504.12757](https://arxiv.org/abs/2504.12757); ETDI [2506.01333](https://arxiv.org/abs/2506.01333); SMCP [2602.01129](https://arxiv.org/abs/2602.01129); MCP gateways [2504.19997](https://arxiv.org/abs/2504.19997); zero-trust authorization for enterprise MCP [2609.22573](https://arxiv.org/abs/2609.22573); ABAC MCP proxy (EMNLP 2026 Industry) [2605.18414](https://arxiv.org/abs/2605.18414); runtime authorization consistency (RAC) [2609.23498](https://arxiv.org/abs/2609.23498); ACLE-MCP [2609.02690](https://arxiv.org/abs/2609.02690); manifest signing [2601.23132](https://arxiv.org/abs/2601.23132); decode-time provenance binding [2610.31974](https://arxiv.org/abs/2610.31974); ProbeID [2610.33633](https://arxiv.org/abs/2610.33633); caller identity confusion (withdrawn by authors) [2603.07473](https://arxiv.org/abs/2603.07473); semantic gateway [2604.25555](https://arxiv.org/abs/2604.25555); Resilient Write (its "risk score" predicts content-filter rejection, not security) [2604.10842](https://arxiv.org/abs/2604.10842).
- *Risk scoring that is not MCP-specific (general agents/tool calls; MCP mentioned at most in passing or as one dataset):* AURA [2510.15739](https://arxiv.org/abs/2510.15739); STARS [2604.10286](https://arxiv.org/abs/2604.10286); NEXUS [2607.19356](https://arxiv.org/abs/2607.19356); IGAC [2606.22916](https://arxiv.org/abs/2606.22916); role-stratified conformal risk control [2607.24343](https://arxiv.org/abs/2607.24343); action-graded severity scale [2607.07474](https://arxiv.org/abs/2607.07474); LLM-judged TBAC [2510.11414](https://arxiv.org/abs/2510.11414); AgenTRIM [2601.12449](https://arxiv.org/abs/2601.12449); AIRGuard [2605.28914](https://arxiv.org/abs/2605.28914); APPA [2607.24625](https://arxiv.org/abs/2607.24625); KedgeFlow [2610.14810](https://arxiv.org/abs/2610.14810); GRAD (graph-level risk score; one "MCP" dataset, AUROC 77.59%) [2610.22828](https://arxiv.org/abs/2610.22828); MiniScope [2512.11147](https://arxiv.org/abs/2512.11147); AgentGuardian [2601.10440](https://arxiv.org/abs/2601.10440).

### Inferences

- MCP risk scoring is mostly a 2026 phenomenon. 16 of the 21 Tier A works date from 2026. Only 5 are from 2025: A11, A15, A18, A19 and A21.
- Several names collide and the report should cite arXiv IDs: "MCPShield" ([2602.14281](https://arxiv.org/abs/2602.14281) vs [2604.05969](https://arxiv.org/abs/2604.05969)), "MCP-Guard" vs "MCPGuard" ([2508.10991](https://arxiv.org/abs/2508.10991) vs [2510.23673](https://arxiv.org/abs/2510.23673)), and "MCPSec" / "MCP-SEC" / "SecMCP" ([2609.10854](https://arxiv.org/abs/2609.10854), [2509.06572](https://arxiv.org/abs/2509.06572), [2508.06418](https://arxiv.org/abs/2508.06418)). "AEGIS" ([2608.20481](https://arxiv.org/abs/2608.20481)) and "AegisMCP" ([2510.19462](https://arxiv.org/abs/2510.19462)) are also different works.

### Gaps

- Semantic Scholar, the arXiv export API and Exa all rate-limited me (HTTP 429) during the session. Coverage of ACM DL, IEEE Xplore, USENIX and NDSS proceedings that are not on arXiv relies on general web search, so a non-arXiv venue paper could have been missed. ShieldMCP was the only one found.
- I could not confirm code releases for MCPShield, MCP-Guard, ConLeash, ChainWatch, AegisMCP or Governed MCP from the pages I read.
- Industry MCP risk scores are excluded as non-academic but match our design closely. Examples: Harness's MCP Tool risk score (likelihood × impact lookup, with response-data sensitivity and labels as impact contributors) — [Harness docs](https://developer.harness.io/ai-security-use-ai-security-ai-firewall-policies/use-ai-security/mcp-risk-score); MCPpedia's 0–100 trust score — [MCPpedia](https://mcppedia.com/methodology); MCPSafe's AIVSS-based letter grade — [MCPSafe](https://mcpsafe.io/methodology). Their methods are vendor-documented and not peer-reviewed.

## 2. Threat direction: do they protect the server from agents (ours), the agent from servers, or both?

### Takeaway

Few works share our direction. **MCP-in-SoS (A1)** is the only one that both computes a numeric server risk score and states our threat model: the client/agent is the untrusted requester and the MCP server is the security boundary. Corvus (A9), AEGIS (B6), MCP-FSD (B7) and Governed MCP (A16) also defend the server or host from callers, but their outputs are scanner priorities, thresholds or tiers. Most runtime per-call risk scorers either protect the agent from malicious servers (MCPShield, MCP-Guard, ShieldMCP, SecMCP, MindGuard) or protect the user's resources from the user's own agent on the client side (AgentTrust, ConLeash, A20, B8).

### Cited Findings

**(i) Server or its data protected FROM agents/callers (our direction)**

- A1 MCP-in-SoS: "we treat the client as an untrusted requester and focus on weaknesses in the MCP server implementation… We treat the MCP server as the security boundary". The adversary's goal is "to misuse an agent to exploit server-side tools and vulnerabilities to exfiltrate sensitive information" — [Source](https://arxiv.org/html/2603.10194)
- A9 Corvus: dynamic testing of 414 internet-facing servers as an external caller would. 91.8% lack OAuth, and 687 tool instances expose shell execution without access controls — [Source](https://arxiv.org/abs/2608.00150)
- B6 AEGIS: "Attackers or malicious agents can exploit certain modalities of these MCP tools to degrade the overall quality of service", for example "an excessively large search radius or very long videos, overloading backend systems". Threat model is OWASP Agentic "Resource Overload (T4)" — [Source](https://arxiv.org/html/2608.20481)
- B7 MCP-FSD: "attacker-steered arguments cause a tool to access sensitive host files outside its declared contract and deployment scope" — [Source](https://arxiv.org/abs/2610.22301)
- A16 Governed MCP: treats tool calls as "the agent's syscalls". A community-uploaded "Classic" agent "cannot invoke system_shell_exec regardless of arguments", so the host is protected from the calling agent — [Source](https://arxiv.org/html/2604.16870)
- A8 FlowGuard is a "server-side security scanner" run "under the operator's authority". It probes servers for command injection and file-system access triggered by tool parameters (server weakness exploitable by callers), and also scans metadata and returned content (agent-side risk) — [Source](https://arxiv.org/html/2607.14754)

**(ii) Agent as the threat, defended on the client/host side (user resources, not the MCP server)**

- A14 ConLeash: threat is "implicit privilege escalation, where an agent leverages validly granted permissions to perform actions that exceed the user's intended risk boundary" (effect and scope escalation) — [Source](https://arxiv.org/html/2605.11360)
- A13 AgentTrust: intercepts the agent's own tool calls (file, shell, HTTP, DB) before execution to stop "accidental deletion, credential exposure, or data exfiltration" — [Source](https://arxiv.org/abs/2605.04785)
- A20: targets "excess-authority errors" where agents exercise "authority that the user did not grant or the task does not need" — [Source](https://arxiv.org/abs/2608.18351)
- B8: injected deletions executed in 479 of 960 runs. Measures whether destructive tools get human approval — [Source](https://arxiv.org/abs/2611.02527)

**(iii) Agent/user protected FROM malicious or compromised servers (inverse direction)**

- A10 MCPShield: "agents implicitly trust tools exposed by potentially untrusted MCP servers" — [Source](https://arxiv.org/abs/2602.14281)
- A12 ShieldMCP: "adversaries can now compromise AI agents not through the user prompt, but through the tools the agent trusts" — [Source](https://aclanthology.org/2026.acl-industry.58/)
- A3 DREAD paper: "We assume an adversary who deploys or compromises an MCP server, embeds malicious instructions within tool descriptions" — [Source](https://arxiv.org/html/2603.22489)
- A15 zero-trust registry: defends against "tool squatting", the deceptive registration of tools — [Source](https://arxiv.org/abs/2504.19951)
- A11 MCP-Guard (prompt injection, data exfiltration in LLM–tool interactions) — [Source](https://arxiv.org/abs/2508.10991); A19 SecMCP (adversarial external content hijacking the conversation) — [Source](https://arxiv.org/abs/2508.06418); A21 descriptor poisoning/shadowing/rug pull — [Source](https://arxiv.org/abs/2512.06556); B9 MindGuard (tool poisoning) — [Source](https://arxiv.org/abs/2508.20412); B3 MCP-RiskCue ("when the MCP server is compromised or untrustworthy") — [Source](https://arxiv.org/abs/2511.05867); B2 Parasites (private data exfiltrated via injected external data) — [Source](https://arxiv.org/abs/2509.06572); B5 description–code mismatch misleading agents — [Source](https://arxiv.org/abs/2602.03580)

**(iv) Both directions or protocol-level**

- A2 MCPThreatHive (all 38 MCP-38 threat classes) — [Source](https://arxiv.org/abs/2604.13849); A4 protocol risks (four protocols) — [Source](https://arxiv.org/abs/2602.11327); B1 MCIP (taxonomy spans user, client, server sources) — [Source](https://arxiv.org/html/2505.14590)
- A6 census: high-severity mass is dominated by unauthenticated network exposure (server side, 9.57% of servers) alongside tool poisoning (agent side) — [Source](https://arxiv.org/abs/2609.14119)
- A7 MCPZoo and A5 mcp-sec-audit rate risky capabilities of servers (command execution, file write, outbound transfer). These are dangerous whether the caller is malicious or the server is — [Source](https://arxiv.org/html/2607.11086); [Source](https://arxiv.org/abs/2603.21641)
- A17 ChainWatch covers "direct sequential attacks, indirect prompt injection chains, and hybrid multi-stage attacks" — [Source](https://arxiv.org/abs/2607.19432). A18 AegisMCP covers "instruction-driven escalation, chain-of-tool exfiltration, malicious MCP server registration, and persistence" — [Source](https://arxiv.org/abs/2510.19462)

### Inferences

- Of the 21 Tier A works, 2 fully share our direction (A1, A9) and 2 partly do (A16 host-side, A8 mixed). 3 address agent-as-threat on the client (A13, A14, A20). 7 are inverse (A3, A10, A11, A12, A15, A19, A21) and 7 cover both directions or the protocol level (A2, A4, A5, A6, A7, A17, A18). The claim "MCP risk scoring that defends servers FROM agents" is therefore almost unoccupied for per-call scoring. Only MCP-in-SoS (static, code-level) shares both the direction and a numeric server score.
- The client-side agent-as-threat works (ConLeash, AgentTrust) are the closest runtime analogues to our dynamic layer. They protect the user's resources rather than a server operator's assets.

### Gaps

- None of the 30 works models a malicious or compromised *caller identity* at an MCP server the way ours does: an agent id with its own history, possibly standing for the whole org. Governed MCP's agent trust tiers (A16) are the nearest. The withdrawn caller-identity paper ([2603.07473](https://arxiv.org/abs/2603.07473)) addressed caller confusion but was pulled by its authors for methodology and ethics issues.

## 3. What is scored, when, on what scale, and with what formula or model?

### Takeaway

Static scores are mostly weighted sums or likelihood × impact products over code findings, threat intel or capability rules: MCP-in-SoS, MCPThreatHive, the census, mcp-sec-audit, DREAD, NIST 800-30. Runtime scores are classifier probabilities with thresholds (MCP-Guard, ShieldMCP, Governed MCP), ordinal risk levels with verdicts (AgentTrust), lattice containment (ConLeash), LLM-judged deny ratios (MCPShield) or session/sequence models (ChainWatch HMM, AegisMCP graph). Only ConLeash and FlowGuard score individual *inputs/parameters*. ChainWatch adds one per-call "parameter sensitivity" feature. Only AEGIS scores *quantity* parameters.

### Cited Findings

**A1 MCP-in-SoS (static, design/pre-deployment; weakness → server)**
- Each finding maps CWE ↔ CAPEC. Likelihood(w) = LA·LE·MI (CAPEC likelihood of attack × CWE likelihood of exploit × count of modes of introduction). Impact(w) = TS·CC (CAPEC typical severity × count of common consequences). R(w) = Likelihood × Impact. Categorical metadata becomes integers. Missing LE is imputed from LA and the reverse — [Source](https://arxiv.org/html/2603.10194)
- Repository score: R_exp = Σ f_r(c)·w(c). R_rms = sqrt(Σ f·w² / Σ f). R_overall = R_rms·log10(N_r+1). Then ln and min–max scaling to 0–100. Bands are Very Low / Low / Medium / High / Very High in fixed 20-point intervals — [Source](https://arxiv.org/html/2603.10194)
- Example CWE scores: R(CWE-732) = 100.0; CWE-441 = 5.0; CWE-862 (Missing Authorization) = 33.3. Analyzers: CodeQL, Joern (CWE Top-25 queries) and, on a subset, the Cisco AI Defense MCP Scanner — [Source](https://arxiv.org/html/2603.10194)

**A2 MCPThreatHive (static, continuous intel; threat item)**
- R = 0.35·L_norm + 0.30·S + 0.20·I + 0.15·D. L_norm = L/7 (7-level impact severity). S = empirical attack success rate. I = persistence/scope (transient 0.5, session 0.75, long-term 1.0). D = exploitation ease (insider-only 0.33, moderate 0.66, trivial 1.0) — [Source](https://arxiv.org/pdf/2604.13849)
- MCP multipliers: semantic/inference-time ×1.20, parasitic chaining ×1.15, low runtime observability ×1.10. R_final = min(10, R·P·10). Critical ≥ 9.0, High 7–9, Medium 4–7, Low < 4. Weights are organization-configurable. Factors are LLM-assigned with chain-of-thought and schema constraints. Worked example: MCP-19 direct prompt injection scores R = 0.855, then ×1.20 → 10.0 (Critical) — [Source](https://arxiv.org/pdf/2604.13849)

**A3 STRIDE + DREAD (design time; threat)**
- 57 threats across Host+Client, LLM, Server, External Data Stores and Authorization Server. Overall DREAD score is the sum of 5 ratings: Low 1–10, Medium 11–24, High 25–39, Critical 40–50. Tool poisoning scores 46.5/50 (Critical) — [Source](https://arxiv.org/html/2603.22489)

**A4 Agent-protocol threat model (design time; protocol risk)**
- NIST SP 800-30 qualitative assessment. L and I on a 3-level scale. R = L × I with Low for R ∈ {1,2} and High for R ∈ {6,9} (Medium = {3,4} by elimination). Twelve protocol-level risks are assessed across creation, operation and update phases — [Source](https://arxiv.org/html/2602.11327)

**A5 mcp-sec-audit (pre-deployment; server/tool capability)**
- A TOML rulebook defines "capability families, high-risk indicators (keywords/regex), and severity weights". The total risk score is "a weighted sum of capability confidences" mapped to low/medium/high/critical. Static Python AST/regex runs with optional Docker sandbox fuzzing plus eBPF monitoring — [Source](https://arxiv.org/html/2603.21641)
- Example output: a filesystem server "flagged as MEDIUM risk (score: 29.0)" — [Source](https://arxiv.org/html/2603.21641)

**A6 Same Name, Different Server (static census; server)**
- S_i = Σ_c w_c·1[k_{i,c} > 0], with w_c ∈ {0,1,3,5} (informational, low, medium, high) over 8 threat classes and 31 syntactic patterns. Patterns run on recovered tool definitions, handler source code and package manifests. Prevalence is corrected by each class's measured precision — [Source](https://arxiv.org/html/2609.14119)

**A7 MCPZoo / Rethinking MCP Security (static; tool capability)**
- Tools fall into seven capability groups and "three risk levels". High covers command and script execution, local file modification and outbound data transfer. High-risk tools are 37.66% of capabilities and Medium-risk 56.02% — [Source](https://arxiv.org/html/2607.11086)

**A8 FlowGuard (pre-invocation triage; parameter)**
- A risk knowledge base scores parameter patterns (command-like, file-like, prompt-bearing). The score draws on "CVE-derived parameter names, Fluffy's parameter to sink observations, and the OWASP Top 25 Parameters list". Each parameter becomes a "risk vector", and strong scores route to fast-path probes. Execution risks are then confirmed by runtime evidence — [Source](https://arxiv.org/html/2607.14754)

**A9 Corvus (pre-scan prioritisation + findings; server)**
- Per-server priority_score in [0,100] "encoding risk severity", from tool name/description signals, capability flags and anonymous-server status. Per-finding confidence in [0,100]: 85–100 confirmed code execution, 71–84 strong behavioural evidence, 40–70 moderate timing side-channel, 1–39 lexical only. Findings ≥ 40 go to SARIF and ≥ 70 to manual triage. Severity is CRITICAL/HIGH/MEDIUM/LOW with "a suggested CVSS 3.1 vector" — [Source](https://arxiv.org/html/2608.00150)

**A10 MCPShield (pre-, during and post-invocation; server)**
- S_deny(T) = (1/N) Σ_{T_i} Σ_k 𝟙[s(d_i, C^p_{i,k}) = deny], over LLM-judged metadata-guided mock invocations. Above a threshold the server is rejected. Defaults: pre_mock_count = 4, pre_deny_ratio = 0.5 — [Source](https://arxiv.org/html/2602.14281)
- After a baseline of B invocations, reasoning runs every K invocations and contrasts the baseline with a recent window to form a "drift delta". The server is rejected above a threshold. Defaults: post_baseline = 5, post_k = 3, post_threshold = 4 — [Source](https://arxiv.org/html/2602.14281)

**A11 MCP-Guard (runtime; request)**
- Stage I is static pattern scanning. Stage II is a fine-tuned multilingual E5 that outputs P(y|x). Stage III is an LLM arbiter. D(x) = Block if LLM = Unsafe, Pass if Safe, and 𝟙[P(y|x) > T_u] if Uncertain, with T_u = 0.45 — [Source](https://arxiv.org/html/2508.10991)

**A12 ShieldMCP (registration time + runtime; description, call, response, session)**
- A distilled 3B-based classifier, trained on 8,400 benign and 3,200 adversarial descriptions, "scores whether a tool description contains embedded action directives". Descriptions "scoring above threshold τd = 0.72 are quarantined". Description hashes catch rug pulls. Parameters are sanitized against the schema. A token-level instruction classifier checks responses. A session dependency graph raises "a high-severity alert" when an unpredicted tool call follows a tool response — [Source](https://aclanthology.org/2026.acl-industry.58.pdf)

**A13 AgentTrust (runtime; call + session)**
- Risk lattice R = {none, low, medium, high, critical} and verdicts {allow, warn, block, review}. The trust evaluator F(History, a) → (verdict, risk, …) chains a shell deobfuscator, rule engine, SafeFix (37 rules), RiskChain (7 multi-step chains) and a cache-aware LLM-as-Judge — [Source](https://arxiv.org/html/2605.04785)

**A14 ConLeash (runtime, client-side; call)**
- Each invocation is lifted into a "consent boundary" over four dimensions: input scope, output sink, data sensitivity and effects. These sit as "a point in this lattice" built from location, taint and effect sub-lattices (power-set lattices for taint/effects). Datalog subsumption decides ALLOW, ASK (escalate) or BLOCK. Invariant violations are non-overridable. User decisions are generalised into reusable rules — [Source](https://arxiv.org/html/2605.11360)

**A15 Zero-trust registry (registration + continuous; tool)**
- A dynamic "Trust Score" per tool from "version currency, the existence and severity (CVSS) of known vulnerabilities in its dependencies (determined through SBOMs and CVE databases), the vendor's patching history, indications of ongoing exploits". Access policies enforce, for example, "minimum_tool_trust_score": 75 — [Source](https://arxiv.org/html/2504.19951)

**A16 Governed MCP (runtime; call + calling agent)**
- A 6-layer kernel gateway: schema validation, trust tier, rate limit, adversarial pre-filter, ProbeLogits semantic gate and constitutional policy, with a Blake3-hashed audit chain. Four agent trust tiers (System, AiNative, AiEnhanced, Classic) come from "origin, signature, and prior trust evolution", and tools declare a minimum tier. ProbeLogits gives a real-valued safety score s, and the gateway thresholds at s > 0 — [Source](https://arxiv.org/html/2604.16870)

**A17 ChainWatch (runtime; session)**
- Per call, a 20-dimensional vector: tool category one-hot (READ/WRITE/EXECUTE/NETWORK/CONFIGURE); Parameter Sensitivity, a weighted sum over credentials, paths, URLs and encoded data; 4 data-flow bits; 3 temporal features; 7 output flags. An HMM infers six kill-chain stages. Rules fire on a sliding window k = 10 with step threshold m = 5. Transition values are "design choices pending Baum-Welch estimation" — [Source](https://arxiv.org/html/2607.19432)

**A18 AegisMCP (runtime; edge + session)**
- MCP activity is a streaming heterogeneous temporal graph. The model fuses a GraphSAGE per-edge behaviour score, a session-DAG score (chain length, branching, install/permission proximity, rare paths) and novelty/attribute cues, with "FPR-cap thresholds (observe/high)" — [Source](https://arxiv.org/html/2510.19462)

**A19 SecMCP (runtime; query)**
- Measures the layer-wise distance of LLM activations from a benign reference set and flags the query when it exceeds threshold τ — [Source](https://arxiv.org/html/2508.06418)

**A20 Task-conditioned least privilege (training time; action/trajectory)**
- Each action is audited before execution and from observed effects "along six dimensions of risk". Deterministic verifiers score completion, evidence, exact state, prohibited attempts and safe success. "Excess privilege values" are measured against task-specific sufficient-authority envelopes and optimised in post-training — [Source](https://arxiv.org/abs/2608.18351)

**A21 Descriptor-level manipulation (evaluation; system)**
- R_sys = w1·ρ + w2·ι + w3·S̄_harm with equal weights. ρ is the success rate on malicious-tool episodes, ι the unsafe-invocation rate, and S̄_harm the normalised harm from leakage severity and intent deviation, each 0–3 — [Source](https://arxiv.org/html/2512.06556)

**Tier B (categorical)**
- B1 MCIP: the MCIP Guardian decides "whether unsafe factors exist" and gives "fine-grained risk categorization". The taxonomy covers Stage (Config, Termination, Interaction), Source, Scope, Type and MAESTRO layer. Flows use contextual-integrity attributes (sender, recipient, data subject, information type, transmission principle) — [Source](https://arxiv.org/html/2505.14590)
- B2 Parasites: an LLM capability analysis plus dynamic verification labels tools as External Ingestion (EIT), Privacy Access (PAT) or Network Access (NAT), and identifies "high-risk servers that concentrate multiple dangerous capabilities" — [Source](https://arxiv.org/html/2509.06572)
- B3 MCP-RiskCue: 9 risk types grouped into 4 high-level categories aligned to confidentiality, integrity and availability. An LLM classifies system logs embedded in tool return values — [Source](https://arxiv.org/html/2511.05867)
- B4 Privilege management: static API-usage analysis builds "a detailed taxonomy of MCP resource access" and quantifies security-relevant API usage per server — [Source](https://arxiv.org/abs/2507.06250)
- B5 DCI measurement: servers graded Full / Mostly / Partial / Rare match between description and code — [Source](https://ar5iv.labs.arxiv.org/html/2602.03580)
- B6 AEGIS: an LLM-built tool ontology covers modality, operation (transform/retrieve/delete) and parameter type (volumetric, timebound, qualitative), with normalized parameter names such as num_records, radius and max_depth. Thresholds are "the highest value that maintains stable operation" under an acceptable tool-call error rate, enforced with OPA in the ContextForge gateway — [Source](https://arxiv.org/html/2608.20481)
- B7 MCP-FSD: L1 server-category screening, L2 per-tool contract analysis that infers least-privilege boundaries, and L3 bypassable path-validation checks — [Source](https://arxiv.org/abs/2610.22301)
- B8: a rule-based extractor plus LLM adjudication marks tools as destructive (269 adjudicated destructive) — [Source](https://arxiv.org/html/2611.02527)
- B9 MindGuard: builds a Decision Dependence Graph from attention and flags a call when non-source context edges exceed γ or user-query influence falls below α — [Source](https://arxiv.org/html/2508.20412)

### Inferences

- No work combines a static per-tool score with a runtime per-call score into one value as ours does. ShieldMCP and MCPShield have registration-time and runtime stages, but they gate on separate thresholds instead of multiplying static and dynamic terms.
- Likelihood × impact appears only in static/threat-level works: A1, A4, and A2 implicitly. Ours applies likelihood at call time, so A1's CWE-CAPEC "Likelihood × Impact" is the nearest academic anchor for the static layer's form, and A2's MCP multipliers are the nearest analogue to an "escalation" factor.
- ConLeash's four-dimension lattice (input scope, output sink, data sensitivity, effects) is the closest published analogue to our per-input 1–5 levels plus asset sensitivity. AEGIS's volumetric/timebound/qualitative parameter classes are the closest analogue to our breadth/quantity inputs.

### Gaps

- Exact weights in mcp-sec-audit's rulebook and its band thresholds are in the repo, not the paper — [Source](https://arxiv.org/html/2603.21641). AgentTrust's mapping from rules to risk levels is rule-specific. ChainWatch's HMM parameters are not estimated.

## 4. What inputs does each work use?

### Takeaway

Most scorers use tool metadata, source code or LLM-visible text. Very few use deployment context. None derives asset sensitivity from an organisation's written security policy. Data sensitivity appears only as a lattice dimension (ConLeash) or a leakage label. Caller identity/history appears only as Governed MCP's agent trust tier and the zero-trust registry's agent principals in access policy.

### Cited Findings

| Work | Tool metadata | Source code / manifests | Runtime traffic / traces | User/org policy | Data sensitivity | Caller identity / history | Source |
|---|---|---|---|---|---|---|---|
| A1 MCP-in-SoS | — | yes (CodeQL, Joern) + MITRE CWE/CAPEC metadata | no | no | no (generic CAPEC severity) | no | [html](https://arxiv.org/html/2603.10194) |
| A2 MCPThreatHive | threat reports | CVE/NVD, GitHub advisories | no | configurable weights | no | no | [pdf](https://arxiv.org/pdf/2604.13849) |
| A3 DREAD | architecture | — | client tests | no | no | no | [html](https://arxiv.org/html/2603.22489) |
| A4 protocols | protocol specs | — | MCP resolver case study | no | no | no | [html](https://arxiv.org/html/2602.11327) |
| A5 mcp-sec-audit | yes | Python source; TOML rules | Docker + eBPF under fuzzing | no | no | no | [html](https://arxiv.org/html/2603.21641) |
| A6 census | recovered tool definitions | handler source, manifests; version history | no | no | no | no | [html](https://arxiv.org/html/2609.14119) |
| A7 MCPZoo | tool capabilities | repos made runnable | runtime servers for scanners | no | no | no | [html](https://arxiv.org/html/2607.11086) |
| A8 FlowGuard | descriptions, schemas, parameter names | CVE-derived parameter names | probe responses | no | no | no | [html](https://arxiv.org/html/2607.14754) |
| A9 Corvus | tool names/descriptions, capability flags | — | live probing, timing | no | no | anonymous-server status | [html](https://arxiv.org/html/2608.00150) |
| A10 MCPShield | metadata | — | mock calls, kernel traces, invocation history | no | no | server history (not caller) | [html](https://arxiv.org/html/2602.14281) |
| A11 MCP-Guard | payload text | — | request text | no | no | no | [html](https://arxiv.org/html/2508.10991) |
| A12 ShieldMCP | descriptions + hashes | — | parameters vs schema, responses, session graph | no | no | no | [pdf](https://aclanthology.org/2026.acl-industry.58.pdf) |
| A13 AgentTrust | tool name | — | params, raw payload, session id, timestamp | ruleset | credential exposure rules | session history | [html](https://arxiv.org/html/2605.04785) |
| A14 ConLeash | tool | — | call arguments, cross-step taint | user consent rules + invariants | yes (lattice dimension) | user decisions | [html](https://arxiv.org/html/2605.11360) |
| A15 registry | registration metadata | SBOM, CVEs/CVSS, patch history | no | admin policy (min trust score, rate limits, agent roles) | no | agent principals in policy | [html](https://arxiv.org/html/2504.19951) |
| A16 Governed MCP | schema, required tier | — | every call | "constitutional policy" | no | agent trust tier ("prior trust evolution"), rate limit | [html](https://arxiv.org/html/2604.16870) |
| A17 ChainWatch | tool category | — | parameters, data flow, timing, outputs, session | no | parameter sensitivity weights | session | [html](https://arxiv.org/html/2607.19432) |
| A18 AegisMCP | — | — | install/invoke/net_out events, bytes, destinations | no | no | session, novelty state | [html](https://arxiv.org/html/2510.19462) |
| A19 SecMCP | — | — | model activations | no | no | benign reference set | [html](https://arxiv.org/html/2508.06418) |
| B6 AEGIS | tool schemas → ontology | — | call parameters | admin thresholds | no | no | [html](https://arxiv.org/html/2608.20481) |

### Inferences

- Our framework's distinctive inputs are policy-derived asset sensitivity, per-agent history and breadth inputs. These are absent from almost all academic MCP scorers. The nearest neighbours are ConLeash (data-sensitivity dimension, user-defined invariants), Governed MCP (caller tier from trust evolution), the zero-trust registry (admin policy with min trust score and agent roles) and AEGIS (quantity parameters).
- Harness, a vendor, does use "Sensitivity of Response Data" and labels as impact contributors in an MCP tool likelihood × impact score — [Harness docs](https://developer.harness.io/ai-security-use-ai-security-ai-firewall-policies/use-ai-security/mcp-risk-score). This suggests industry is closer to our input model than academia.

### Gaps

- I did not find any MCP paper that reads an organisation's security policy, data-classification scheme or ISO/NIST/CIS controls to set tool impact. This is a gap in the literature, not in my search terms. I searched "policy", "privilege", "permission" and "access control" in MCP abstracts.

## 5. Evaluation: datasets, sizes, metrics, headline numbers

### Takeaway

Static/ecosystem scorers are evaluated on large crawls (222 to 113,927 servers), usually by prevalence and sometimes by precision on hand-labelled samples. Runtime scorers are evaluated on attack benchmarks (ASR, F1, AUROC). Only a few report false-positive or benign-utility cost on ordinary traffic: ConLeash, ShieldMCP, MCPShield, AgentTrust and MCP-Guard. One study (A7) shows existing scanners' risk flags are below 50% precise.

### Cited Findings

- A1 MCP-in-SoS: 222 Python repos. 191 (86.0%) have ≥ 1 mapped weakness, with 15,962 findings over 51 CWE classes. 47.6% of scored repos are High, 18.3% Very High, 23.6% Medium, 9.9% Low and 0.5% Very Low. Protocol-surface weaknesses are 56.9% of findings and 57.1% of risk-weighted exposure. 87% of repos with Tool weaknesses also have Protocol weaknesses — [Source](https://arxiv.org/html/2603.10194)
- A2 MCPThreatHive: "demonstrates classification fidelity on a single known incident". The authors say a formal precision/recall evaluation is needed — [Source](https://arxiv.org/pdf/2604.13849)
- A3 DREAD: 57 threats scored, and seven major MCP clients tested against tool poisoning. "Significant security issues with most tested clients" — [Source](https://arxiv.org/abs/2603.22489)
- A5 mcp-sec-audit: MCPTox (45 real servers) gives 663 capability instances "with 100% detection rate". On the vulnerable-server lab, static detection was 2/2 on Python and 0/7 on JavaScript servers — [Source](https://arxiv.org/html/2603.21641)
- A6 census: 21,643 servers and 72,606 versions, with 14,353 servers' source scanned. 414 hand-labelled findings give pooled precision 0.56. 15.21% of servers have ≥ 1 finding and 11.14% a high-severity one (~7.6% after precision correction). 51.1% of multi-version servers changed their advertised surface and 40.6% did so silently. Silent drift has OR 2.96 [2.56, 3.42] for a high-severity finding. Popularity OR is 0.78 per log-star — [Source](https://arxiv.org/abs/2609.14119)
- A7 MCPZoo: 64,611 unique servers (113,927 total), with 37,288 supporting dynamic analysis. Eight scanners were run: Snyk Agent-Scan, Tencent A.I.G, Cisco MCP-Scanner, Ant Group MCPScan, MCPSafetyScanner, Lasso mcp-gateway, nova-proximity and mcp-armor. 96.89% of servers are flagged risky by ≥ 1 scanner. Average precision is 45.53% (worst 10.40%), and pairwise Jaccard agreement is low — [Source](https://arxiv.org/html/2607.11086)
- A8 FlowGuard: 1,880 executable cases in five categories. F1 is 0.879 for command injection and 0.942 for file-system access. It is up to 2.23× faster than dynamic scanners and produced 523 findings across 326 real servers — [Source](https://arxiv.org/abs/2607.14754)
- A9 Corvus: 640 confirmed production servers, 414 audited dynamically, 68 reportable vulnerabilities (SQLi, SSRF to cloud metadata, template injection, path traversal). 41.6% of servers vanished within three days — [Source](https://arxiv.org/abs/2608.00150)
- A10 MCPShield: 76 malicious servers, six attack methods, six LLM backbones. Average defense rate rises from 10.05% undefended to 95.30%, with low deny rates on benign servers over 5 runs. Probing costs about 10–100× the server's baseline tokens — [Source](https://arxiv.org/html/2602.14281)
- A11 MCP-Guard: MCP-AttackBench has 70,448 samples. Stage II reaches 96.01% accuracy (F1 95.06%). The pipeline F1 is 89.1% with 51% latency reduction (455.9 ms average), peak F1 95.4%, and average F1 97.21% on external benchmarks with DeepSeek-chat — [Source](https://arxiv.org/html/2508.10991)
- A12 ShieldMCP: 40 MCP servers (25 benign), 5 LLM backends, 487 attack cases and 200 benign tasks. Tool-poisoning ASR falls from 74% to < 9% and IPI ASR from 47% to < 6%. Benign completion is 96.8% vs 98.5% undefended. Median added latency is 118 ms (P95 247 ms), and expert alert review agreed 46/50 — [Source](https://aclanthology.org/2026.acl-industry.58.pdf)
- A13 AgentTrust: 300 scenarios (six risk categories × 50), with 95.0% verdict accuracy and 73.7% risk-level accuracy. On 630 independent adversarial scenarios it reaches 96.7% verdict accuracy (patched ruleset, not zero-shot) and ~93% on shell-obfuscated payloads — [Source](https://arxiv.org/abs/2605.04785)
- A14 ConLeash: ConsentBench has 984 traces from 13 real MCP servers over 11 task categories. It auto-permits 98.3% of benign calls, catches 99.4% of escalations and reaches 98.2% step accuracy (F1 98.7%) at 8.2 ms per step. It detects 95.5% of boundary crossings on 50 real sessions, and 15/16 users preferred it — [Source](https://arxiv.org/html/2605.11360)
- A15 zero-trust registry: architecture and policy examples only. No empirical evaluation — [Source](https://arxiv.org/html/2504.19951)
- A16 Governed MCP: the five non-inference layers plus audit cost 11.3 µs per call. The ProbeLogits gate costs 332–556 ms on Qwen2.5-7B, Llama-3-8B and Mistral-7B, 2.4–3.4× faster than Llama Guard 3 — [Source](https://arxiv.org/abs/2604.16870)
- A17 ChainWatch: "We demonstrate the approach using five representative attack scenarios", with no quantitative benchmark — [Source](https://arxiv.org/abs/2607.19432)
- A18 AegisMCP: emulated smart-home testbed plus physical bench. Sub-second inference and alerting on Intel N150, outperforming traffic-only and sequence baselines — [Source](https://arxiv.org/abs/2510.19462)
- A19 SecMCP: Llama3, Vicuna and Mistral on MS MARCO, HotpotQA and FinQA. AUROC > 0.915 in all cases, average 0.98 — [Source](https://arxiv.org/html/2508.06418)
- A20: Qwen3.5-4B trained on 1,500 tasks. Safe success is 98.48% vs 64.36% (2,896 episodes, 500 held-out tasks), and excess-authority errors fall from 4.56% to 0.79% — [Source](https://arxiv.org/abs/2608.18351)
- B1 MCIP: improvements of 40.81% and 18.3% on two safety metrics and 27.22% on an additional benchmark — [Source](https://arxiv.org/html/2505.14590)
- B2 Parasites: 12,230 tools from 1,360 servers. 5,666 were flagged potentially risky and 1,062 (8.7%) confirmed exploitable (487 EIT, 406 PAT, 190 NAT). Capability analysis has 85.5% precision and 98.0% recall; dynamic verification has 95.1% precision and 98.8% recall — [Source](https://arxiv.org/html/2509.06572)
- B3 MCP-RiskCue: 1,800 synthetic logs from 10 LLMs, 243 dummy servers, 2,421 training and 471 evaluation queries. GRPO-trained Llama-3.1-8B reaches 83% accuracy (+9 pp over the best remote model) — [Source](https://arxiv.org/abs/2511.05867)
- B4: 2,562 MCP applications in 23 categories. Network APIs appear in 1,438 servers and system APIs in 1,237 — [Source](https://arxiv.org/abs/2507.06250)
- B5: 10,240 servers in 36 categories. About 13% show substantial description–code mismatch — [Source](https://arxiv.org/abs/2602.03580)
- B6 AEGIS: 56 servers and 937 tools (869 text). Ontology identification exceeds 84% accuracy — [Source](https://arxiv.org/html/2608.20481)
- B7 MCP-FSD: 21,097 servers from nine registries. 787 of 4,806 triaged servers (16.4%) have filesystem capability despite non-filesystem classification. 150 cases were confirmed vulnerable, leading to 13 advisories including two CVEs in Anthropic's Git MCP server — [Source](https://arxiv.org/abs/2610.22301)
- B8: in a 1,000-repo registry sample, an estimated 90% (95% CI 82–95) of destructive tools lack server-side confirmation. 32 of 41 hosts have no default approval step. 60.7% of host–tool pairs have no enforced approval — [Source](https://arxiv.org/abs/2611.02527)
- B9 MindGuard: evaluated on MCPTox. Average precision > 97.6% with near-perfect attribution accuracy — [Source](https://arxiv.org/abs/2508.20412)

### Inferences

- A7's finding that MCP scanner alerts are under 50% precise, and A6's pooled pattern precision of 0.56, are directly relevant to defending our LLM static scanner. Any MCP risk score should be validated against hand labels, as A6 does with per-class Wilson CIs.
- Only ConLeash's ConsentBench and AgentTrust's benign/warn buckets resemble our "mostly ordinary traffic with grey risk" evaluation framing. Most runtime work reports ASR on attack-only suites.

### Gaps

- None of the runtime scorers is evaluated on real production MCP traffic logs with caller identity. ConLeash's 50 "real-world agent sessions" is the closest.

## 6. Stated limitations, and how each differs from our framework

### Takeaway

The common limitations are language coverage (Python-only static analysis), reliance on generic metadata (CAPEC, keyword rules), LLM hallucination, adaptive attackers and attack-only evaluation. Relative to us, every work lacks at least two of: server-protecting direction, org-policy-derived impact, per-input levels, runtime per-call scoring, a per-caller behaviour baseline, and a passive gateway with a tamper-evident log.

### Cited Findings

- A1 MCP-in-SoS: "restricted to Python MCP servers", and "our risk scoring relies on CAPEC's likelihood and severity metadata; these estimates may diverge from realized risk in MCP deployments" — [Source](https://arxiv.org/html/2603.10194)
- A2 MCPThreatHive: hallucinated risk levels, token-budget sensitivity, domain shift and false positives on aggressive-sounding pentest tools. Outputs "should be reviewed by a qualified analyst" — [Source](https://arxiv.org/pdf/2604.13849)
- A5 mcp-sec-audit: "Pattern-based detection is inherently susceptible to false positives… and false negatives". JavaScript/TypeScript parsing is limited — [Source](https://arxiv.org/html/2603.21641)
- A6 census: precision varies by class, "narrow syntactic signatures score high; use-dependent classes score low". The registry does not version tool definitions, so tool-behaviour drift is invisible — [Source](https://arxiv.org/html/2609.14119)
- A10 MCPShield: "security cognition depends on the behavior of the underlying agent backbone". Remote settings and adaptive adversaries are future work — [Source](https://arxiv.org/html/2602.14281)
- A12 ShieldMCP: English-only classifier, cross-call correlation "scales quadratically", adaptive attacks, three expert evaluators and a single hardware configuration — [Source](https://aclanthology.org/2026.acl-industry.58.pdf)
- A13 AgentTrust: "Static analysis ceiling… cannot, even in principle, reason about runtime data flow". Deobfuscation is "incomplete by design" — [Source](https://arxiv.org/html/2605.04785)
- A15 registry: "Doesn't protect against tool vulnerabilities or fully trusted compromised agents" — [Source](https://arxiv.org/html/2504.19951)
- A17 ChainWatch: HMM transition values are unestimated design choices, and the paper notes that rule R2 "could generate" false alerts when calibrating thresholds — [Source](https://arxiv.org/html/2607.19432)
- A7 MCPZoo: current scanners "are not yet reliable enough to support ecosystem-level security claims" — [Source](https://arxiv.org/html/2607.11086)

### Inferences

How each Tier A work differs from ours (S = static per-tool score, R = runtime per-call score, P = org-policy-derived sensitivity, I = per-input levels, B = per-caller behaviour baseline, G = observe-only gateway + tamper-evident log):

| Work | Direction | S | R | P | I | B | G | Key difference from ours |
|---|---|---|---|---|---|---|---|---|
| A1 MCP-in-SoS | ours | yes (code) | no | no | no | no | no | Scores code weaknesses from generic CWE/CAPEC metadata, min–max relative to its corpus. No tool semantics, policy or runtime |
| A2 MCPThreatHive | both | threat-level | no | weights only | no | no | no | Scores abstract threat classes, not a deployment's tools or calls |
| A3 DREAD / A4 NIST | inverse / protocol | threat-level | no | no | no | no | no | Expert ordinal scoring of threats or protocols |
| A5 mcp-sec-audit | mixed | yes (capability) | no | no | no | no | no | Keyword/capability weights, no asset context |
| A6 census | both | yes (server) | no | no | no | no | no | Per-class weights {0,1,3,5}; ecosystem census |
| A7 MCPZoo | both | 3 capability levels | no | no | no | no | no | Coarse capability tiers; main result is scanner unreliability |
| A8 FlowGuard | mixed | parameter risk (triage) | probing | no | parameter-level | no | no | Parameter scores steer a scanner, not production gating |
| A9 Corvus | ours | server priority | probing | no | no | no | no | External scanner, CVSS-suggested findings |
| A10 MCPShield | inverse | probe deny score | yes | no | no | server drift | no | Baselines the server's behaviour for the agent; we baseline the agent for the server |
| A11 MCP-Guard / A12 ShieldMCP / A19 SecMCP / B9 MindGuard | inverse | partly | yes | no | no | no / ref set | ShieldMCP is a proxy | Injection/poisoning detectors, not misuse-risk scorers |
| A13 AgentTrust | agent-as-threat (host) | no | 5-level | no | no | session chains | MCP server form | Rules + LLM judge on a single host; no server-asset model |
| A14 ConLeash | agent-as-threat (client) | no | lattice | user rules | yes (4 dims) | user decisions | no | Closest per-call model; client consent, no numeric score, no server operator |
| A15 registry | inverse | trust score | no | admin min-score | no | no | registry | Supply-chain trust of tools, not call risk |
| A16 Governed MCP | agent-as-threat (host) | tier per tool | yes | constitutional | no | caller tier | Blake3 audit chain | Closest on caller trust + tamper-evident audit, but enforcing (not observe-only) and kernel-bound |
| A17 ChainWatch / A18 AegisMCP | both | no | session | no | parameter sensitivity (A17) | session/novelty | no | Session anomaly models, not per-agent long-term baselines |
| A20 least-privilege | agent-as-threat | no | per-action (training) | task envelopes | no | no | no | Score is a training signal, not a deployment gate |
| A21 descriptor attacks | inverse | no | eval metric | no | no | no | no | System-level evaluation metric only |

- Positioning claim the evidence supports: no verified academic MCP work combines (a) the server-as-asset direction, (b) static tool risk from org security policy, (c) per-call runtime scoring with escalation and a floor, and (d) a per-agent behaviour multiplier learned from history in an observe-only gateway. The closest pieces exist separately: A1 (direction plus static likelihood × impact), A14 (per-input lattice), B6 (quantity parameters), A16 (caller tier plus hash-chained audit) and A10 (behaviour baseline, inverse direction).

### Gaps

- I did not read every Tier B paper's limitations section in full. The Tier B differences above rest on abstracts and the scoring sections only.
- Whether ShieldMCP's open-source proxy (mentioned in a related talk listing) is public could not be verified.
