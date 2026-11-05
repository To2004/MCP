# Few MCP risk scorers defend servers from agents

This report compares our MCP risk-scoring framework with the 30 academic works and 55 industry products, tools and standards that the research notes verified. It also summarises 132 broader MCP security papers by threat direction and maps UEBA practice onto our behaviour multiplier. Works absent from the repo's existing coverage (KB02, KB03, KB04, KB06, KB07, the context brief, `paper_v5/refs.bib`, `refs-full.bib`, the paper's literature review and the older comparison documents) are tagged **[NEW]** in the tables and the reference list.

## The short answer: the combination is new, the parts are not

No verified academic paper or documented product computes what our framework computes: **one graded score per call at a server-side gateway**. That score multiplies a static (tool, asset) price, whose sensitivity comes from the organisation's own classification policy, by a **bounded factor learned from the same agent's own multi-week history**.

Every ingredient of that score exists somewhere else. **MCP-in-SoS** is the only academic MCP scorer that both outputs a number and shares our threat direction, but it scores code weaknesses statically, from generic CWE/CAPEC metadata ([arXiv:2603.10194](https://arxiv.org/abs/2603.10194)). **ConLeash**, **AgentTrust** and **Governed MCP** score each call at runtime with the agent as the threat, but they do so on the client or host, with lattices, rules or classifiers, and keep no long per-agent history ([arXiv:2605.11360](https://arxiv.org/abs/2605.11360), [arXiv:2605.04785](https://arxiv.org/abs/2605.04785), [arXiv:2604.16870](https://arxiv.org/abs/2604.16870)). **Harness** scores an organisation's own MCP tools as likelihood × impact with hand-set sensitivity labels ([Harness docs](https://developer.harness.io/ai-security/mcp-risk-score)). Per-entity behaviour baselines are almost 40 years old (Denning 1987, IDES/NIDES), and they now ship for AI agents in Microsoft Entra and Exabeam ([Entra agents](https://learn.microsoft.com/en-us/entra/id-protection/concept-risky-agents), [Exabeam white paper](https://www.exabeam.com/wp-content/uploads/WHITEPAPER-Agent-Behavior-Analytics-Securing-the-Autonomous-Enterprise.pdf)).

The defensible novelty claims are therefore narrow. They are asset sensitivity derived from a written classification policy and checked against a held-out inventory, a per-call composition of a static price with an argument-free bounded per-agent multiplier (including a **discount below ×1 that no paper or vendor documents**), and evaluation on mostly ordinary traffic. The same literature names our weak points. Eight MCP scanners average **45.53% precision** ([arXiv:2607.11086](https://arxiv.org/abs/2607.11086)), and our scanner matches an oracle panel exactly only 35% of the time. The max combiner is weaker than averaging on CERT, the ×0.7 discount is a poisoning surface, and fresh identities, Sybils and cold start all defeat history-based scoring. Per-call scoring is also blind to content and flow, which is why the whole framework scored a run-level **AUC of about 0.5** on MCPHunt, the only outside labelled dataset. Before any comparison is published, our own framework needs one fixed definition, because today it exists in four inconsistent versions.

## Our framework exists in four versions that disagree

A comparison needs a fixed target, and the repo does not have one. The paper draft, the GROUND-TRUTH specification, the running gateway and the latest author decision (2026-11-01, which lives only in project memory and a probe script) each define the runtime differently ([our_framework notes §2](/home/ovadyat/MCP/research_notes/MCP%20risk%20scoring%20and%20UEBA%20comparison/our_framework_and_local_coverage.md)). The shorthand in circulation is itself inconsistent: the scoring notes describe the dynamic layer as "cell × likelihood × escalation, with a floor, times a behaviour multiplier of x0.7–5", a phrase that merges the Gen 2 paper specification with behaviour design v4. This report treats the **latest design** as "ours", and uses the **as-built gateway** wherever a measured number is needed.

| Element | Paper draft (`main.tex`) | Code and gateway today | Latest design (2026-10-29 / 11-01) | What must be reconciled |
|---|---|---|---|---|
| Static price | sensitivity × blast radius × impact, each 1–5, product 1–125, four bands | Same cell. The behaviour path converts it to a 1–5 level by cube root (`cell ** (1/3)`) | A USENIX design record proposes a weighted sum, 0.3·Impact + 0.3·Sensitivity + 0.3·Blast + 0.1·ParameterRisk (open decision #2) | Three combination rules |
| Per-input level | Absent (v13 came later) | v13 lookup table, 1–5, logged beside the risk; how it combines is "not decided" | ParameterRisk = max over inputs, weight 0.1 | Undecided |
| Runtime factor | L = D·A·N, about [1, 8]; R_dynamic = R_static × L, "bounded below by 1" | R = min(125, cell × B × L), B ∈ [0.70, 1.30], L ∈ [0.85, 1.30]; per deployment, no caller identity | Replaced by the behaviour multiplier | The paper and the code describe different mechanisms |
| Behaviour multiplier | None | Design v4: 15 dimensions; M = 5^(2S−1) or 0.7^(1−2S); "the strangest dimension decides"; ×0.7–5; warm-up of 5 calls | M = ((n+1)/(2k+1))^γ, γ = ln5/ln(max(n,1000)+1), on four call-counted dimensions, plus burst and tool-order rules; blocking uses max(1, M) | Whether familiar behaviour may lower a score |
| Identity | Not specified | v4 also reads the /16 network and client family. The gateway derives `agent_id` per issuer, app and user from OAuth, and labels callers `anonymous` without OAuth | Agent id only; a missing id means all calls share one key | v4 inputs break the latest decision |
| Framing | Intent-agnostic "misuse of legitimate capabilities" | — | Mostly ordinary traffic with gray risk | `overview.md` still says the framework "is not anomaly detection" (stale) |

Sources for the table: [main.tex §3, §4.3–4.4](/home/ovadyat/MCP/paper_v5/main.tex), [GROUND-TRUTH.md](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md), [gateway/framework.py](/home/ovadyat/MCP/src/mcp_security/gateway/framework.py), [behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md), [dynamic-layer-explained.md](/home/ovadyat/MCP/docs/project/dynamic-layer-explained.md), [context-brief-2026-10-29.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md), [memory: dynamic-layer-v5-decisions.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/dynamic-layer-v5-decisions.md), [gateway/README.md](/home/ovadyat/MCP/src/mcp_security/gateway/README.md).

**The discount is the most important disagreement for this comparison**, because the literature treats it as the main attack surface. The paper says the dynamic factor never lowers the static risk. The v4 engine lowers it by up to 30% (×0.7), and in the shipped engine a perfect mimic earns ×0.89 ([KB06](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/06-threat-model-and-evasion.md)). The latest design keeps a reported discount (about ×0.87 for the deepest habit, with a lower bound of ×0.78) but enforces on max(1, M).

Two further disagreements will draw reviewer attention. First, v4's session duration, missing-handshake and unsafe-sequence dimensions have nothing to key on under MCP revision 2026-07-28, which removes `initialize` and sessions; the latest design already drops session length ([KB06](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/06-threat-model-and-evasion.md)). Second, `main.tex` no longer cites the withdrawn caller-identity paper (arXiv 2603.07473), but the paper is still in `refs-full.bib`, and GROUND-TRUTH.md §8 still maps the claim "identity cannot separate good calls from bad" to it ([CITATION-AUDIT.md §1.1](/home/ovadyat/MCP/paper_v5/CITATION-AUDIT.md), [GROUND-TRUTH.md](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)).

## Thirty academic MCP scorers exist, and only one shares our direction

**The second pass verified 30 works that put a risk score, grade, rank or level on MCP servers, tools, parameters, calls or sessions:** 21 numeric (Tier A) and 9 categorical (Tier B). All date from **April 2025 to November 2026**. None is from 2024, since MCP launched in November 2024, and **16 of the 21 numeric scorers are from 2026**. Only four have a peer-reviewed venue: Parasites (IEEE S&P 2026), MCIP (EMNLP 2025), ShieldMCP (ACL 2026 Industry) and the Anbiaee et al. threat model (*JISA*) ([arXiv:2509.06572](https://arxiv.org/abs/2509.06572), [arXiv:2505.14590](https://arxiv.org/abs/2505.14590), [ACL 2026.acl-industry.58](https://aclanthology.org/2026.acl-industry.58/), [doi:10.1016/j.jisa.2026.104645](https://doi.org/10.1016/j.jisa.2026.104645)).

**The server-protecting direction is almost unoccupied.** The 21 numeric scorers split as follows:

| Direction | Count | Works |
|---|---|---|
| Fully ours (server protected from callers) | 2 | MCP-in-SoS; the Corvus scanner ([arXiv:2608.00150](https://arxiv.org/abs/2608.00150)) |
| Partly ours | 2 | Governed MCP (protects the host from the calling agent); FlowGuard, which is mixed ([arXiv:2607.14754](https://arxiv.org/abs/2607.14754)) |
| Agent as threat, but defending the user's resources on the client | 3 | AgentTrust; ConLeash; Tu and Tu's least-privilege training ([arXiv:2608.18351](https://arxiv.org/abs/2608.18351)) |
| Inverse (agent protected from servers) | 7 | — |
| Both directions, or protocol level | 7 | — |

MCP-in-SoS states our threat model in so many words: "we treat the client as an untrusted requester … We treat the MCP server as the security boundary". It computes Likelihood = LA·LE·MI and Impact = TS·CC per finding from CAPEC/CWE metadata, rolls the findings up to a repository score R_rms·log10(N_r+1), and min–max scales that score to 0–100 in five 20-point bands. Across **222 Python repositories** it rates **47.6% High and 18.3% Very High**. Its authors note that it covers Python only and that CAPEC estimates "may diverge from realized risk in MCP deployments" ([arXiv:2603.10194](https://arxiv.org/abs/2603.10194)).

**Static scorers belong to the same likelihood × impact family as our cell, so the form of our static layer is not new.** Anbiaee et al. use a 3 × 3 NIST SP 800-30 grid, and Huang et al. sum five DREAD ratings to a score out of 50 ([arXiv:2603.22489](https://arxiv.org/abs/2603.22489)). MCPThreatHive computes R = 0.35·L + 0.30·S + 0.20·I + 0.15·D and then applies **MCP-specific multipliers** (×1.20 semantic, ×1.15 parasitic chaining, ×1.10 low observability) capped at 10; these multipliers are the closest academic analogue to an escalation factor ([arXiv:2604.13849](https://arxiv.org/abs/2604.13849)). The registry census weights eight threat classes {0, 1, 3, 5} ([arXiv:2609.14119](https://arxiv.org/abs/2609.14119)), and MCPZoo sorts tools into three capability levels ([arXiv:2607.11086](https://arxiv.org/abs/2607.11086)). **None reads an organisation's security policy.** The notes searched MCP abstracts for "policy", "privilege", "permission" and "access control". They found no paper that derives impact or sensitivity from a classification scheme or from ISO, NIST or CIS controls.

**Runtime scorers gate calls; they do not price them against history.** ConLeash is the closest per-call model. It lifts each call into a four-dimension lattice (input scope, output sink, data sensitivity, effects), and Datalog subsumption returns ALLOW, ASK or BLOCK; on **984 traces from 13 real servers** it auto-permits **98.3%** of benign calls and catches **99.4%** of escalations at 8.2 ms per step ([arXiv:2605.11360](https://arxiv.org/abs/2605.11360)). Governed MCP is the closest on caller trust and audit, with four agent trust tiers from "prior trust evolution", fixed token buckets, a ProbeLogits safety gate and a **Blake3 hash-chained audit log**, though it reports latency only (11.3 µs for the non-inference layers, 332–556 ms for the gate) ([arXiv:2604.16870](https://arxiv.org/abs/2604.16870)). MCPShield is the mirror image of our dynamic layer: it baselines the *server's* behaviour after B invocations and rejects the server on drift ([arXiv:2602.14281](https://arxiv.org/abs/2602.14281)). AEGIS **[NEW]** is the only work that scores **quantity parameters** (volumetric, timebound), enforcing per-parameter thresholds through OPA in the ContextForge gateway ([arXiv:2608.20481](https://arxiv.org/abs/2608.20481)). ChainWatch's HMM transitions are "design choices pending Baum-Welch estimation", with no quantitative evaluation ([arXiv:2607.19432](https://arxiv.org/abs/2607.19432)). AegisMCP's AUROC of 0.985 comes only from synthetic smart-home runs, and its novelty signal is global rather than per agent ([arXiv:2510.19462](https://arxiv.org/abs/2510.19462)).

**No academic work multiplies a static and a dynamic term into one value.** ShieldMCP and MCPShield have registration-time and runtime stages, but each stage gates on its own threshold. **None is evaluated on real production MCP traffic with caller identity.** ConLeash's 50 real sessions come closest.

## Industry grades servers before install and gates calls without a number

The industry catalogue holds **55 entries**: 35 products and projects, 6 standards and 14 small open-source graders. **Only 17 publish a formula.** Supply-chain scanners grade a server before install, identity-aware gateways allow or deny each call, and registries attach grades to listings.

**Most protect the agent from servers, the opposite of our direction.** Cisco's scanner targets "malicious MCP tools" ([GitHub](https://github.com/cisco-ai-defense/mcp-scanner/)), and Docker's gateway limits what "a malicious or compromised MCP server can read" ([security.md](https://github.com/docker/mcp-gateway/blob/main/docs/security.md)). Snyk Agent Scan gives each server a 0–1000 score at four levels (100, 300, 600, 1000), and Evo alerts at 600 or above, but the analysis API behind the score is undocumented ([risks.md](https://github.com/snyk/agent-scan/blob/HEAD/docs/risks.md), [Snyk docs](https://docs.snyk.io/agent-security/evo-by-snyk/agentic-development-security-ads/agent-supply-chain-security)).

**Only Harness, Akto and Wallarm score the organisation's own MCP tools as assets.** Harness is the closest documented analogue to our static cell. Its lookup table maps likelihood (internet exposure, authentication strength, open High or Critical issues) and impact ("Sensitivity of Response Data" and organisation-set labels) to a 0–10 score, with unpublished defaults ([Harness docs](https://developer.harness.io/ai-security/mcp-risk-score)). Akto adds capped points (severity, +1 if discovered in the last 30 days, +1 for sensitive data, +1 for public exposure, maximum 5) ([Akto docs](https://ai-security-docs.akto.io/akto-argus-agentic-ai-security-for-homegrown-ai/agentic-ai-discovery/concepts/risk-score)), and Wallarm takes the maximum factor weight on a 1–10 scale ([Wallarm docs](https://docs.wallarm.com/api-discovery/risk-score/)). In all three, sensitivity comes from hand-set labels or detected sensitive data, never from a policy document.

**Runtime gateways in our direction decide; they do not score.** Pomerium, agentgateway, Kong, AWS AgentCore Policy, Azure API Management and Cloudflare portals return allow or deny from CEL, Cedar, ACL or rate-limit rules, and the identity they key on is usually the **end user**, such as Pomerium's email or a JWT `sub` ([Pomerium](https://www.pomerium.com/docs/capabilities/mcp), [agentgateway](https://agentgateway.dev/docs/kubernetes/latest/documentation/mcp/tool-access/)). Golf Firewall's monitor mode attaches "threat scores" to events but publishes no method ([Golf docs](https://docs.golf.dev/golf-firewall)). Per-agent baselines appear only in small projects, namely HarrisonCN's per-client EWMA burst detection ([PR #87](https://github.com/HarrisonCN/mcp-gateway/pull/87)) and TrueFoundry's off-path z-score quarantine ([TrueFoundry](https://www.truefoundry.com/blog/claude-code-enterprise-mcp-gateway)); mTrust and Noma make similar claims that could not be verified. **No major gateway documents a hash-chained log.** Integrity is left to the SIEM, and only AxioRank claims a "tamper-evident audit log" ([mcpaudit](https://github.com/AxioRank/mcpaudit)).

**No standard defines an MCP scoring formula.** The OWASP MCP Top 10 is in beta and lists categories only, including MCP08 "Lack of Audit and Telemetry" ([OWASP](https://owasp.org/www-project-mcp-top-10/)). CoSAI lists about 40 threats without scores ([CoSAI PDF](https://www.coalitionforsecureai.org/wp-content/uploads/2026/03/model-context-protocol-security-1.pdf)), and MAESTRO has no numeric scoring. The MCP Security Best Practices page uses MUST/SHOULD rules ([MCP spec](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)), and NIST's agent overlays (COSAiS) are still in development ([NIST NCCoE slides](https://www.nccoe.nist.gov/sites/default/files/2026-05/Cyber-AI-Profile-Working-Session-Extending-Tech-Content-Slides-Slido.pdf)). The closest standards-level statement of our threat is **OWASP Agentic ASI02 "Tool Misuse"**: agents misusing tools they are allowed to use, with harm "in sequences of actions rather than in any single API call". The notes saw it only through secondary sources ([HUMAN summary](https://www.humansecurity.com/learn/blog/owasp-top-10-agentic-applications/)).

## Side by side, every close system lacks at least two of our pieces

The table puts the closest academic systems first, then industry. "A→S" means the server or the organisation's data is protected and the agent is the threat; "S→A" is the inverse.

| System | Direction | Unit scored | Static / runtime | Scale and formula | Org-policy context | Per-agent baseline | Identity | Deployment | Audit integrity | Evaluation |
|---|---|---|---|---|---|---|---|---|---|---|
| **Ours, as built** | A→S | (tool, asset) cell; input level; each call; agent vs own history | Both | Cell 1–125; gate cell × B × L; dynamic_risk = cell^(1/3) × M, M ∈ [0.7, 5], max over 15 dimensions | Sensitivity derived by an LLM from the org's classification policy | Yes, 90 days per agent (v4) | OAuth-derived agent id; v4 also network and client | Observe-only HTTP gateway, about 40 µs per call | SHA-256 hash chain per file | Static 50/56 exact vs held-out table; MCPHunt AUC about 0.5 |
| **Ours, latest design** | A→S | Each call | Both | Risk_static × M; M a mid-p rank on 4 call-counted dimensions, plus burst and tool-order rules; enforce on max(1, M) | Same | Yes, rank p-value vs own 90-day calls | Agent id only | Same | Same | 4 of 9 Pinecrest scenarios pass |
| MCP-in-SoS ([2603.10194](https://arxiv.org/abs/2603.10194)) | A→S | CWE finding, then repository | Static (code) | CAPEC/CWE L × I; RMS·log10, scaled 0–100, 5 bands | No (generic CAPEC) | No | None | Offline scan | n/a | 222 Python repos |
| ConLeash ([2605.11360](https://arxiv.org/abs/2605.11360)) | Agent as threat (client) | Each call | Runtime | Point in a 4-dimension lattice, then ALLOW/ASK/BLOCK | User consent rules plus invariants | User decisions become rules | User | Client middleware, 8.2 ms | Not stated | 984 traces, 13 real servers |
| Governed MCP ([2604.16870](https://arxiv.org/abs/2604.16870)) | Agent as threat (host) | Call and calling agent | Runtime | 6 layers; safety-score gate (s > 0); fixed token buckets | "Constitutional policy" | Trust tier from history | 4 agent tiers | Kernel gateway, enforcing | Blake3 audit chain | Latency only |
| AgentTrust ([2605.04785](https://arxiv.org/abs/2605.04785)) | Agent as threat (host) | Call and session | Runtime | 5-level lattice plus verdict; rules plus LLM judge | Ruleset | Session chains only | Session | Host interceptor; ships an MCP server | Not stated | 300 scenarios: 95.0% verdict, 73.7% risk level |
| AEGIS [NEW] ([2608.20481](https://arxiv.org/abs/2608.20481)) | A→S | Quantity parameter | Thresholds set offline, checked per call | Allow/deny at the highest stable value | Admin thresholds | No | None | OPA in a gateway | Not stated | 56 servers, 937 tools |
| MCPShield ([2602.14281](https://arxiv.org/abs/2602.14281)) | S→A | Server | Before, during and after calls | Deny ratio over LLM-judged mock calls; drift delta | No | Baselines the **server** | n/a | Agent-side layer | Not stated | 76 malicious servers; defence rate 10.05% → 95.30% |
| AegisMCP ([2510.19462](https://arxiv.org/abs/2510.19462)) | Both | Graph edge, session | Runtime | Fused GraphSAGE, DAG and TTL-novelty scores; FPR-capped thresholds | No | Global novelty only | Session | Smart-home IDS | Not stated | Synthetic; AUROC 0.985 |
| ShieldMCP [NEW] ([ACL](https://aclanthology.org/2026.acl-industry.58/)) | S→A | Description, call, response | Registration and runtime | Classifier threshold τ = 0.72; session-graph alert | No | No | None | Proxy | Not stated | Tool-poisoning ASR 74% → under 9% |
| Harness [NEW] ([docs](https://developer.harness.io/ai-security/mcp-risk-score)) | A→S (own tools) | Each tool | Static (discovery) | Likelihood × impact lookup, 0–10 | Hand-set labels plus response-data sensitivity | No | n/a | SaaS posture | Not documented | None published |
| Snyk Agent Scan ([risks.md](https://github.com/snyk/agent-scan/blob/HEAD/docs/risks.md)) | Mostly S→A | Server, skill | Static | 0–1000, 4 levels | Generic "private data" category | No | n/a | CLI or fleet scan | n/a | None published |
| Wallarm [NEW] / Akto [NEW] | A→S (own endpoints) | Endpoint or MCP primitive | Static | Max weight 1–10 / additive, capped at 5 | Sensitive-data detection | No | n/a | API discovery | n/a | None |
| Pomerium [NEW], agentgateway, Kong [NEW], AgentCore | A→S | Each call | Runtime | Allow/deny, no score | RBAC/ABAC on token claims | No | End user, JWT `sub` | Enforcing proxy | SIEM export, no chain | None |
| TrueFoundry [NEW], HarrisonCN [NEW] | A→S | Client traffic | Runtime, off the call path | z-score / EWMA, then quarantine | No | Yes; windows undocumented | Client or developer | Gateway | Not documented | None |

Two columns make us distinctive: **org-policy context**, and a **per-agent baseline applied to a per-call price**. On **evaluation**, several systems are stronger. ConLeash, ShieldMCP and MCPShield report benign-utility cost on real servers. Our strongest number compares the scanner with a held-out table written by the same authors, and our only external test (MCPHunt) separated risky from benign runs at chance level.

## What is new, what is not, and where the literature says we are weak

### Novelty holds for the composition and the policy input only

| Piece of our framework | Verdict | Prior work that already does it |
|---|---|---|
| Server as the protected asset, agent as the threat | Not new on its own; rare in scoring | MCP-in-SoS; Corvus [NEW]; AEGIS [NEW]; MCP-FSD [NEW] ([2610.22301](https://arxiv.org/abs/2610.22301)); Hou et al. "malicious users" ([2503.23278](https://arxiv.org/abs/2503.23278)); Errico et al. "agents who … over-step their role" ([2511.20920](https://arxiv.org/abs/2511.20920)); OWASP ASI02 |
| Static product of 1–5 factors (likelihood × impact) | Not new | CVSS, DREAD, NIST SP 800-30; MCP-in-SoS; Anbiaee et al.; MCPThreatHive; Harness [NEW] |
| Tool impact ladder (none up to delete/execute) | Not new | MCPZoo three levels [NEW]; Parasites EIT/PAT/NAT; Snyk "destructive capabilities"; destructive-tool class ([2611.02527](https://arxiv.org/abs/2611.02527)) [NEW] |
| **Sensitivity derived from the org's written classification policy and checked against a held-out inventory** | **New** (no MCP paper or product found) | Nearest: Harness labels [NEW]; ConLeash data-sensitivity dimension; Akto/Wallarm sensitive-data detection [NEW] |
| Per-input 1–5 levels from design-time rules | Partly new | ConLeash lattice; FlowGuard parameter risk vectors [NEW]; AEGIS volumetric/timebound thresholds [NEW]; ChainWatch "parameter sensitivity"; AgentCore Cedar argument conditions |
| **One graded per-call score = static price × behaviour factor** | **New as a composition** | ShieldMCP and MCPShield: staged thresholds, not products; gateways return allow/deny; Golf's "threat scores" are unpublished [NEW] |
| Per-agent baseline over weeks | Not new as an idea | UEBA since IDES/NIDES; Errico §III-D3 (proposal, no evaluation); IETF AEBA draft (KB02); Exabeam ABA; Entra ID Protection for agents [NEW]; MI9 [NEW]; HarrisonCN, TrueFoundry [NEW] |
| **Bounded multiplier that can go below ×1 on a per-call price** | **Looks new**, and is also the main poisoning surface | Exabeam's anchor × anomaly factor and its risk-reducing events are the nearest (KB03); Splunk and Elastic multipliers are admin-set; NIST SP 800-207 "contextual, score-based" trust algorithms |
| Rank / mid-p / conformal p-value for M | Not new (the repo's design record says so) | Lancaster mid-p; conformal p-values (KB04); Ho et al. directed anomaly scoring (KB07) |
| Max combiner over dimensions | Not new, and contested | Wallarm max [NEW]; Google SecOps max + 0.2 × rest [NEW]; Le and Zincir-Heywood 2021, where MAX does worse [NEW] |
| Learned per-agent policy (tool limits, required steps) | Not new | Praetor DFA from benign telemetry (KB02); TraceAegis; Invariant flow rules; AgentCap prerequisites [NEW] ([2611.00729](https://arxiv.org/abs/2611.00729)) |
| Observe-only gateway | Not new | Golf monitor mode [NEW]; observability-mcp "Inspect" (KB02) |
| Hash-chained audit log | Not new (table stakes) | Governed MCP Blake3; MDPI *Electronics* SHA-256 chain (KB02); CapSeal [NEW] ([2604.16762](https://arxiv.org/abs/2604.16762)); mcp-attested [NEW] ([2605.24248](https://arxiv.org/abs/2605.24248)) |
| No model on the call path | Sets us apart from LLM-judge guards, but not new | Canopii and mcptrustchecker avoid LLMs [NEW]; contrast MCP-Guard, AgentTrust, Governed MCP |
| Evaluation on mostly ordinary traffic with gray risk | New as a framing for MCP | ConsentBench is closest; most runtime work reports attack success on attack-only suites |

The repo's own latest positioning (KB02) already lists most of the "not new" items. The new evidence in this pass changes three things. **Entra ID Protection for agents** documents per-agent behaviour detections in production, including "unfamiliar resource access" and "sign-in spike" ([Microsoft Learn](https://learn.microsoft.com/en-us/entra/id-protection/concept-risky-agents)). **MI9** publishes per-goal agent baselines with a conservative cold start ([arXiv:2508.03858](https://arxiv.org/abs/2508.03858)). **Harness** documents tool-level likelihood × impact with organisation labels. The paper can no longer imply that per-agent baselining, or org-context sensitivity in general, is unexplored. It can still claim the *policy-derived, validated* sensitivity and the *per-call bounded multiplier*.

### Seven weaknesses the literature exposes

| Weakness | Our own evidence | What the literature shows | State in the latest design |
|---|---|---|---|
| **Scanner precision** | Oracle panel: 35% exact, 69% within one band; the raters themselves agree only 42–50% exact. Blast radius moves 19–22% of cells between arms. A v13 prompt change shifts AUC by up to 0.1 ([scanner_vs_human.md](/home/ovadyat/MCP/reports/evaluation/scanner_vs_human.md), [GROUND-TRUTH.md](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)) | 8 MCP scanners: 96.89% of servers flagged, **average precision 45.53%**, worst 10.40% ([2607.11086](https://arxiv.org/abs/2607.11086)). Registry census: pooled pattern precision **0.56**, with Wilson CIs per class ([2609.14119](https://arxiv.org/abs/2609.14119)) | Human annotation study designed but not run |
| **Max combiner** | v4: "the strangest dimension decides". The latest J4s proposal uses a Šidák combination (a calibrated min-p, still max-type) | On CERT, **MAX is among the weaker combiners**; AVG and VOTE do better ([doi:10.1109/TNSM.2021.3071928](https://doi.org/10.1109/TNSM.2021.3071928)). Every p-value combiner is optimal only against some alternative ([doi:10.1093/biomet/asx076](https://doi.org/10.1093/biomet/asx076)) | Ablation listed as a TODO |
| **Boiling-frog poisoning of the discount** | A perfect mimic earns ×0.89. 23 inflated agent-days move the learned burst limit from 13 to 200 calls a minute. Design J admits that "one burst day teaches that bursts are normal" ([KB06](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/06-threat-model-and-evasion.md), [context brief §7](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md)) | Slow poisoning raises false negatives with "far less chaff" ([doi:10.1145/1644893.1644895](https://doi.org/10.1145/1644893.1644895)). The attacker's gain is bounded only "if external constraints are properly used" ([Kloft & Laskov](https://www.jmlr.org/papers/volume13/kloft12b/kloft12b.pdf)). Isolation Forest and LODA resist poisoning; autoencoders and LOF do not ([Le & Zincir-Heywood 2021](https://web.cs.dal.ca/~lcd/pubs/TNSM2021.pdf)) | Enforcing on max(1, M) plus fixed burst rules partly answer this; the reported score still discounts |
| **Fresh identities and Sybils** | A fresh identity's first day is free (2,400 writes at M = 1.00). Three Sybils switch on the org discount for a fourth identity (×4.37 → ×1.00) (KB06). Sybils are declared out of scope | Stateful defences need requests to be grouped, and **fresh, indistinguishable identities defeat them**, a formal result ([2608.17445](https://arxiv.org/abs/2608.17445)). A distributed attack across accounts was caught only **a fifth as often** ([2605.31593](https://arxiv.org/abs/2605.31593)). Exabeam calls ephemeral agents "a known gap" | The agent id is assumed operator-issued and unforgeable |
| **Cold start** | v4 warm-up: M = 1 for the first 5 calls. Under J, an agent with fewer than 1,000 past calls cannot reach ×5. Pinecrest scenarios S9 and S10 fail for lack of a cold start | NIDES would not wait "one or more years" ([NIDES](https://csl.sri.com/papers/2sri/2sri.pdf)). Ho et al. used a 6-month burn-in. **Entra runs a separate "early life malicious activity" detection alongside its learning mode.** MI9 uses conservative thresholds that tighten as confidence grows | v4's first-access floor (sensitivity 4–5) is the only guard |
| **Per-call blindness to content and flow** | MCPHunt run-level AUC: 0.501 static, 0.506 gate, 0.497 dynamic. Spearman correlation with an independent judge: 0.061–0.099. 50 `write_file` calls that copy secrets were under-scored ([mcphunt README](/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/README.md)) | IFG-Guard reaches 92.0% detection at 0% FPR using information-flow tracking (KB02). RAC catches authorization drift that a static-plus-history baseline misses 509 of 1,008 times ([2609.23498](https://arxiv.org/abs/2609.23498)). UEBA products **sum risk over a session or 24 h** | No accumulation per agent-day; this is an open item |
| **Adaptive insiders and mimicry** | The design record forbids claiming that M stops a mimic | In a pre-registered study, adaptive operational security produced **no detectable shift in the mole's UEBA rank** ([2605.07472](https://arxiv.org/abs/2605.07472)). Mimicry against sequence detectors has been known since 2002 (KB06) | Out of scope by the author's framing decision |

Two weaknesses sit outside the scoring maths.

**Per-agent baselines depend on identity that MCP does not guarantee.** In a measurement of 7,973 remote servers, **40.55%** expose tools without authentication. **All 119 testable OAuth servers** have at least one flaw, and **96.6%** have dynamic-client-registration flaws ([arXiv:2605.22333](https://arxiv.org/abs/2605.22333)). No study measures how often one credential is shared across many agents. That is the attribution failure that matters most when an agent id "may stand for the whole org".

**An agent id that blends several humans widens the baseline**, which makes mimicry easier. The upside is a lower privacy cost than employee UEBA. NIST SP 800-53 AC-2(12) warns that account monitoring "may reveal previously unknown information about the behavior of individuals" ([doi:10.6028/NIST.SP.800-53r5](https://doi.org/10.6028/NIST.SP.800-53r5)).

## Most MCP security research protects the agent, not the server

**The broader MCP security notes count 132 unique works.** None is from 2024. The A→S work is young, mostly from March to November 2026, and concentrated in authorization and gateway defences.

| Primary direction | Works |
|---|---|
| A→S (server protected from the agent) | 34 |
| S→A (agent protected from the server) | 50 |
| Both, or neutral | 47 |
| Unknown | 1 |

| Group (count) | Direction mix | Key works | What it means for us |
|---|---|---|---|
| Surveys and taxonomies (17) | Mostly S→A | Hou et al. name "malicious users". Errico et al. propose per-user/role baselines but evaluate none. Krakauer et al. [NEW] ([2611.02611](https://arxiv.org/abs/2611.02611)) find confused-deputy risk "cannot be completely mitigated" inside a server. MCPSHIELD ([2604.05969](https://arxiv.org/abs/2604.05969)): no single defence covers more than 34% of threats. Surapani et al. [NEW] ([2609.15906](https://arxiv.org/abs/2609.15906)) | No taxonomy is organised around "legitimate agent misusing legitimate tools". Krakauer's ceiling argues for a gateway layer |
| Benchmarks (19) | Mostly S→A | MCPTox, MSB and MCP-SafetyBench are S→A. Usable A→S pieces: MCPHunt (11.5–41.3% policy-violating propagation), FragBench (per-user linkage), RAC TraceBench (1,248 workflows), HCP's 10 invariants. COPEX [NEW] ([2610.04378](https://arxiv.org/abs/2610.04378)) | No benchmark has per-agent, multi-day histories |
| Evaluation-method papers | Neutral | "Labels Are Not Endpoints" corrected 58 attack labels ([2608.12880](https://arxiv.org/abs/2608.12880)). The CASCADE audit [NEW] ([2604.17125](https://arxiv.org/abs/2604.17125)) shows the headline FPR depends on how allow/review/block collapse to binary | State the labelling rule; never derive labels from the scorer |
| Ecosystem measurements (25) | Mixed | Capability laundering in **16.4%** of 4,806 triaged servers [NEW] ([2610.22301](https://arxiv.org/abs/2610.22301)). **40.6% silent drift** [NEW]. Scanners under 50% precise [NEW]. **91.8% of 414** audited servers lack OAuth [NEW] ([2608.00150](https://arxiv.org/abs/2608.00150)). MCP traffic resembles C2 beaconing [NEW] ([2609.19091](https://arxiv.org/abs/2609.19091)) | Price the actual capability, not the declared one. Re-scan when the tool list changes. Report the sample with any authentication figure |
| A→S defences (25 entries: 20 A→S, 5 both) | A→S | Prompts Don't Protect ([2605.18414](https://arxiv.org/abs/2605.18414)): unauthorized tools are selected in 48–68% of cases and 96% under role-escalation prompts, and ABAC filtering brings this to 0%. Zero-trust SDK study [NEW] ([2609.22573](https://arxiv.org/abs/2609.22573)): checks inside the tool body leak 21.1%. Stochastic Deputy [NEW] ([2609.14780](https://arxiv.org/abs/2609.14780)): 26 of 26 out-of-scope attempts served. Also RAC, SecureMCP [NEW], AgentCap [NEW], Mandato [NEW], KedgeFlow [NEW] | All enforce deterministically outside the model, where our gateway sits. **None grades a call against the same agent's own multi-week history** |
| S→A defences and detectors | S→A | MCP-Guard, MindGuard, SecMCP, MCPShield, ETDI, AgentBound, MTGuard, mcp-attested [NEW] | Cite for contrast only |
| Identity and authentication (9) | A→S | Zhou et al. [NEW] (the authentication measurement above). Kumar et al. [NEW]: enterprise gateway with RFC 8693 token exchange ([2608.10760](https://arxiv.org/abs/2608.10760)). AIP [NEW]: capability tokens, 600 of 600 attacks rejected ([2603.24775](https://arxiv.org/abs/2603.24775)). Delegation Without Trust [NEW] ([2609.00267](https://arxiv.org/abs/2609.00267)). Caller identity confusion (**withdrawn**, [2603.07473](https://arxiv.org/abs/2603.07473)) | Our baseline needs gateway-established identity; cite these works as the layer we build on |
| Attacks (18) | Overwhelmingly S→A | Parasites; Trivial Trojans [NEW] ([2507.19880](https://arxiv.org/abs/2507.19880)); Log-To-Leak [NEW] ([2610.36108](https://arxiv.org/abs/2610.36108)) | These attacks chain **legitimate** tools into exfiltration, which the victim server sees as unusual caller behaviour |

Direction labels and counts come from the MCP security notes, which resolved every arXiv ID against the arXiv API on 2026-11-04.

**The strongest argument the literature gives us links the two directions.** Many S→A attacks, including Parasites, Trivial Trojans and Log-To-Leak, hijack an agent into calling legitimate tools in unusual combinations or volumes. At the victim server, that shows up as a caller deviating from its own past. A server-side behaviour layer can therefore see the effect of an injection it never sees directly. **The temporal dimension in A→S work is thin.** RAC tracks lineage within one session, ChainWatch uses a session HMM, AegisMCP uses global novelty, MCP Guardian and Governed MCP use fixed rate limits, and TrustShiftProbe baselines servers rather than callers ([arXiv:2608.23763](https://arxiv.org/abs/2608.23763)).

Several names collide, so the paper should cite them by ID: MCPShield ([2602.14281](https://arxiv.org/abs/2602.14281)) versus MCPSHIELD ([2604.05969](https://arxiv.org/abs/2604.05969)); MCP-Guard ([2508.10991](https://arxiv.org/abs/2508.10991)) versus MCPGuard ([2510.23673](https://arxiv.org/abs/2510.23673)); MCPSec ([2609.10854](https://arxiv.org/abs/2609.10854)), MCP-SEC ([2509.06572](https://arxiv.org/abs/2509.06572)) and SecMCP ([2508.06418](https://arxiv.org/abs/2508.06418)); AEGIS ([2608.20481](https://arxiv.org/abs/2608.20481)) versus AegisMCP ([2510.19462](https://arxiv.org/abs/2510.19462)); and the MCPZoo dataset ([2512.15144](https://arxiv.org/abs/2512.15144)) versus the extended MCPZoo study ([2607.11086](https://arxiv.org/abs/2607.11086)).

## UEBA already solved per-entity baselining; agents change the keying

### Academic UEBA gives us the method and its known failure modes

Gartner named "User Behavior Analytics" in an August 2014 Market Guide. It added the "E" in 2015 because "other entities besides users are often profiled"; both definitions are known only through vendor quotes ([Dataconomy](https://dataconomy.com/2016/08/03/iot-security/)). The method is far older. Denning's 1987 model of subjects acting on objects is the root ([doi:10.1109/TSE.1987.232894](https://doi.org/10.1109/TSE.1987.232894)). SRI's IDES "adaptively learns what is normal for subjects", and its subjects include "individual users, groups, remote hosts and the overall system" ([IDES final report](https://csl.sri.com/papers/9sri/9sri.pdf)). **Treating an AI agent id as a UEBA entity is therefore a direct extension, not a new concept.**

**Baselines.** IDES aged profiles daily by 0.9862 (a 50-day half-life) and kept separate weekday and weekend profiles ([IDES enhanced prototype](https://www.csl.sri.com/papers/1sri/1sri.pdf)). NIDES aged most measures by audit records rather than by the clock, to keep "profile continuity over nights and weekends", which is the idea behind our "90 active days" ([NIDES](https://csl.sri.com/papers/2sri/2sri.pdf)). Peer groups separate one entity's change from an organisation-wide change: Eldardiry et al. flag changes "dissimilar to their peers' behavioral changes" ([doi:10.1109/SPW.2013.14](https://doi.org/10.1109/SPW.2013.14)), and Turcotte et al. learn overlapping peer groups for users whose own history is sparse ([doi:10.1109/ISI.2016.7745472](https://doi.org/10.1109/ISI.2016.7745472)). Machine identities need their own baselines most of all. In GitHub Enterprise audit logs, a global-only baseline produced **64 alerts dominated by noisy service accounts**, against 26 for per-user plus global ([doi:10.1109/SecDev66745.2025.00021](https://doi.org/10.1109/SecDev66745.2025.00021)).

**Scoring and aggregation.** NIDES mapped each measure's percentiles onto a half-normal, combined them as T² (a mean of squares), and alerted only when the alert level changed, which is a precedent for hysteresis. Tuor et al. standardised −log P scores with an EWMA and decomposed them per feature for explanation ([arXiv:1710.00811](https://arxiv.org/abs/1710.00811)). Ho et al. ranked events by directed anomaly scoring under a budget of **10 alerts a day**, after a **6-month burn-in** ([USENIX Sec 2017](https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-ho.pdf)). Goldberg et al. found that "repeated appearance near the top" of ranked lists over time beat single-day anomaly scores ([doi:10.1109/HICSS.2016.344](https://doi.org/10.1109/HICSS.2016.344)).

**Evaluation.** CERT is fully synthetic, with an anomaly rate around 10⁻⁵ per user-day, and "there is no standard benchmark for the CERT problem" ([arXiv:2007.06985](https://arxiv.org/abs/2007.06985)). LANL's 58-day, 1.65-billion-event dataset is real, machine-to-machine and red-team-labelled, which makes it the closer analogue to gateway traffic ([LANL](https://csr.lanl.gov/data/cyber1/)).

**An open gap we could fill.** The notes found **no paper that formally analyses a bounded multiplicative behaviour modifier on a static per-request risk**: its monotonicity, a bound on the attacker's discount, or how it interacts with a floor. NIST SP 800-207's "contextual, score-based" trust algorithm is the nearest standards concept ([doi:10.6028/NIST.SP.800-207](https://doi.org/10.6028/NIST.SP.800-207)).

### Commercial UEBA sums per entity; only Exabeam learns a multiplier

| Product | Entity and window | Per-event score | Aggregation | Multipliers | Bound |
|---|---|---|---|---|---|
| Exabeam Advanced Analytics (KB03) | User or asset session (24 h); 60–90-day initial baseline | **Anchor score × anomaly factor**, learned from the user's histogram, rule frequency and peer-group size; some events reduce risk | Sum per session; incident at 90 | Learned | Trend chart 0–100 |
| Splunk ES risk-based alerting (KB03) | Risk object; 24 h, 3 d, 7 d | Impact × confidence (e.g. 80 × 70 gives 56) | **Sum > 100 per 24 h**; 7-day tactic rule (≥3 tactics, ≥4 sources) for "low and slow" | Admin "risk factors", e.g. ×1.5 | "No upper limit" |
| Microsoft Sentinel UEBA (KB03) | User, host, IP, app; lookback set per activity | InvestigationPriority 0–10; AnomalyScore 0–1 | Top anomalies over 30 d | Peer group: top 20 peers by TF-IDF | 0–10 / 0–1 |
| Elastic entity risk scoring [NEW] | Host, user, service; 30 d of alerts, hourly | Alert risk score | Weighted so that higher scores count more | Admin asset criticality 0.5–2; privileged ×2 | 0–100, five levels |
| Google SecOps Risk Analytics [NEW] | Entity; 24 h or 7 d | Finding risk score | **max + 0.2 × sum of the rest** | Admin TTL modifiers | Normalised 1–1000; riskDelta capped at 200% |
| Entra ID Protection, workload identities [NEW] | Service principal; **2–60-day** learning | Detection (unfamiliar IP, resource, user agent) | Risk level | — | Low / Medium / High |

Sources: [Exabeam](https://docs.exabeam.com/en/advanced-analytics/i56/advanced-analytics-user-guide/113551-get-to-know-a-user-profile.html), [Splunk](https://help.splunk.com/en/splunk-enterprise-security-7/risk-based-alerting/7.3/introduction/how-risk-based-alerting-works-in-splunk-enterprise-security), [Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics), [Elastic](https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-risk-scoring), [Google SecOps](https://docs.cloud.google.com/chronicle/docs/detection/risk-analytics-overview), [Entra workload identities](https://learn.microsoft.com/en-us/entra/id-protection/concept-workload-identity-risk).

Securonix, CrowdStrike and Palo Alto do not publish their internals. A search snippet says Palo Alto's SaaS user risk halves every 30 days ([PA docs](https://docs.paloaltonetworks.com/saas-security/behavior-threats/user-risk-scoring)).

Our multiplier is closest to Exabeam's **per-event** anchor × anomaly factor, not to any vendor's **per-entity** total. The paper should say this plainly: vendors rank entities for analysts, while we price calls. **No vendor documents a behaviour multiplier with explicit bounds that goes below 1**, so our ×0.7 has no direct industry precedent.

### UEBA for AI agents is shipping, but rarely documented

**Industry.** Only two vendors document how their agent baselines work. **Microsoft Entra ID Protection for agents [NEW]** runs a learning mode that suppresses behavioural alerts for agents without enough history, while "a separate detection runs in parallel" for early-life malicious behaviour. Its eight detections include "sign-in spike" and "unfamiliar resource access"; risk in on-behalf-of flows goes to the **user**, and detections are kept for 90 days ([Microsoft Learn](https://learn.microsoft.com/en-us/entra/id-protection/concept-risky-agents)). **Exabeam Agent Behavior Analytics (KB02)** forms baselines "over roughly 14 days", with some rules needing 7, 14 or 28 days, and counts MCP integrations as Tier 2. Its white paper admits that short-lived agents "never reach baseline maturity", calling this "a known gap … innate to any detection model based on historical baselining" ([Exabeam white paper](https://www.exabeam.com/wp-content/uploads/WHITEPAPER-Agent-Behavior-Analytics-Securing-the-Autonomous-Enterprise.pdf)). Securonix AEBA, Zenity, Noma and Lasso Intent Deputy [all NEW] claim agent baselines without publishing how they work ([Securonix](https://www.securonix.com/products/ueba/), [Noma](https://www.helpnetsecurity.com/2026/06/02/noma-brings-visibility-and-access-governance-to-ai-agents-and-mcp-servers/)). CrowdStrike, Silverfort, Teleport, Palo Alto and Oasis focus on agent identity and authorization at MCP gateways, not on behaviour.

**Academic.** Among the 38 verified papers, **MI9 [NEW]** is the closest analogue. It keeps **goal-conditioned** baselines, tests drift with Jensen-Shannon divergence and Mann-Whitney U, treats drift as "risk factors rather than direct violations", and starts with conservative cold-start thresholds, but its only evaluation is on 1,033 Gemini-generated scenarios (99.81% detection) ([arXiv:2508.03858](https://arxiv.org/abs/2508.03858)). **Praetor (KB02)** compiles benign telemetry into a gateway DFA and reaches 5.6% macro attack success on Agent Security Bench at 2.2 ms per call, yet shows **18% evasion by synonym substitution on continuous parameters** ([arXiv:2604.26274](https://arxiv.org/abs/2604.26274)). Server-side fingerprinting **[NEW]** can identify which agent or model is calling, with 97.2% F1 over 33,580 GitHub pull requests ([arXiv:2601.17406](https://arxiv.org/abs/2601.17406)) and the MARK classifier for web agents ([arXiv:2606.20910](https://arxiv.org/abs/2606.20910)); this could cross-check a self-declared agent id. **Only 6 of the 38 papers are MCP-specific, and none keeps a long per-agent history.**

### Mapping UEBA practice onto our design choices

| Our choice (latest design) | UEBA practice | Implication |
|---|---|---|
| Key on agent id only; it may stand for the whole org | Key on the human where one exists (Entra sends OBO risk to the user; Exabeam profiles "users and their AI agents"). Per-identity baselines matter more for machines (GitHub audit-log study) | Defensible, but state it as a deliberate departure |
| Self-baseline only; v4 org discount when ≥3 other agents start the same new thing | Sentinel, Exabeam and Securonix add peer groups; Eldardiry; Turcotte | Add peers over **agents** (same route or tool set), counting only established agents |
| 90 active days, hard window | IDES/NIDES half-lives of 30–50 days; Exabeam 60–90 d; Entra 2–60 d; Exabeam ABA about 14 d | Counting active days is a NIDES idea; consider exponential ageing instead of a hard cut-off |
| Time of day ±1 h; days of the other kind count 1/16 | IDES separate weekday/weekend profiles; Elastic `time_of_day` | Consistent with practice |
| Rank / mid-p per dimension | NIDES percentile mapping; Kriegel [0,1] calibration; Ho ranking | Standard; not a novelty claim |
| Max or Šidák across dimensions | NIDES mean of squares; Tuor sum of −log; Google max + 0.2 × rest | Ablate max vs Šidák vs mean vs Fisher |
| No accumulation across calls | Exabeam session sum; Splunk 24 h sum and 7-day tactic rule; Goldberg repeated top-k | Add a per-agent-day accumulated signal beside M |
| Discount to about ×0.78–0.87 (v4: ×0.7) | Only Exabeam's risk-reducing events come close | Never discount below the static price when enforcing; grant a discount only after maturity |
| Warm-up; quiet agents cannot reach ×5 | Entra parallel early-life detection; Exabeam maturity gate; MI9 conservative thresholds | Add an early-life check that does not depend on history |
| A reason string on every score | Tuor per-feature decomposition; REACT alarm properties ([Alahmadi](https://www.usenix.org/system/files/sec22-alahmadi.pdf)) | Consistent with practice |
| Agent-day rates at ×3; AP | Tuor CR-k; Le's investigation budget (60% of insiders at a 0.1% budget); Ho alerts per day | Report recall at a fixed review budget |

## Recommendations: narrow the claim, borrow UEBA's guard rails, test on outside data

These recommendations respect the author's standing decisions: identity is the agent id only; evaluation uses mostly ordinary traffic with gray risk; dynamic scenarios compare an agent only with its own past; and earlier designs stay selectable. Adversarial weaknesses therefore become stated limitations, not new evaluation tracks.

| # | Area | Recommendation | Evidence |
|---|---|---|---|
| 1 | Positioning | Structure related work as four labelled strands. (a) MCP risk scoring: MCP-in-SoS as the only same-direction numeric scorer; ConLeash, AgentTrust and Governed MCP as client/host runtime scorers; MCPShield, MCP-Guard and ShieldMCP as inverse. (b) A→S authorization and identity: Prompts Don't Protect, RAC, AIP, Kumar et al., Zhou et al. (c) UEBA: IDES/NIDES, Exabeam, Entra agents, NIST SP 800-207. (d) Agent behaviour monitors: MI9, Praetor, AegisMCP. State plainly that most MCP security work is S→A, so reviewers do not expect MCPTox or MSB numbers | Sections above |
| 2 | Positioning | Claim only the composition, the validated policy-derived sensitivity, the bounded per-call multiplier and the ordinary-traffic evaluation. Cite Errico §III-D3, the IETF AEBA draft, Exabeam ABA and Entra agents as prior statements of agent baselining. Do not claim the first gateway, first baseline, first tamper-evident log, new rank p-values, or resistance to mimicry | Novelty table |
| 3 | Citation hygiene | Remove `huang2026caller` from `refs-full.bib` and GROUND-TRUTH.md §8; the audit proposes Zhou et al. ([2605.22333](https://arxiv.org/abs/2605.22333)) as the replacement. Check arXiv 2606.28679: `refs.bib` gives it to Mellafe's "Capability Gates Are Not Authorization", while `gateway-architecture.md` and these notes call it ScopeGate. Cite every colliding name by ID | [CITATION-AUDIT.md](/home/ovadyat/MCP/paper_v5/CITATION-AUDIT.md), [refs.bib](/home/ovadyat/MCP/paper_v5/refs.bib) |
| 4 | Consistency | Pick one runtime definition (the D·A·N text, B × L, Gen 2 or v4/J) and make the paper, GROUND-TRUTH and the gateway agree. Fix the floor statement in particular. Either remove network and client from v4 or explain why they stay | Four-version table |
| 5 | Datasets | **MCPHunt**: keep it, and report AUC ≈ 0.5 as evidence of the per-call blind spot. **FragBench**: the only MCP benchmark with per-user linkage across sessions. **RAC TraceBench** and **HCP's 10 invariants**: test the burst and tool-order rules. **ConsentBench**: false positives per call on real servers | [2604.27819](https://arxiv.org/abs/2604.27819), [2605.11029](https://arxiv.org/abs/2605.11029), [2609.23498](https://arxiv.org/abs/2609.23498), [2606.29073](https://arxiv.org/abs/2606.29073), [2605.11360](https://arxiv.org/abs/2605.11360) |
| 6 | Datasets | For per-entity behaviour, where no MCP equivalent exists, use **CLUE-LDS** (real cloud data, more than 5,000 users over 5 years), **LANL** (real machine-to-machine traffic), and **GH Archive** and flaws.cloud CloudTrail (machine identities; KB03). Use CERT only as a sanity check | [Landauer 2022](https://doi.org/10.1109/BigData55660.2022.10020672), [LANL](https://csr.lanl.gov/data/cyber1/), [Jordan & Chen](https://doi.org/10.1109/SecDev66745.2025.00021) |
| 7 | Metrics | Report recall at a fixed review budget (CR-k, alerts per day), AP at realistic base rates, and per-class precision of the static scanner with Wilson intervals. Run the human annotation study | [Tuor](https://arxiv.org/abs/1710.00811), [Ho](https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-ho.pdf), [2609.14119](https://arxiv.org/abs/2609.14119) |
| 8 | Design | Make the discount safe. Enforce on max(static, static × M). Grant M < 1 only after a maturity threshold. Cap the discount an agent can gain per window. Use robust statistics (trimmed quantiles) for learned limits. Keep v4 selectable | Kloft & Laskov; Rubinstein; Le 2021; KB06 M1 |
| 9 | Design | Add an early-life check that does not depend on history: route-level priors, the first-access floor kept for more than one day, and the rate of new agent ids as a fleet signal | Entra early-life detection; Exabeam gap; KB06 M4; context brief |
| 10 | Design | Add peer context over agents (same route or tool set), counting only established, independent agents, so an org-wide rollout does not read as a rise for every agent | Eldardiry; Turcotte; KB06 M2 |
| 11 | Design | Add a per-agent-day accumulated score beside the per-call M, with NIDES-style hysteresis. Ablate max vs Šidák vs mean | Splunk, Exabeam, Google; Goldberg; Le 2021 |
| 12 | Design | Wire the v13 level-5 hard rules (credential words) into the gate, as `gateway-architecture.md` already plans, and test them on MCPHunt's secret-carrying calls. State that flow-level exfiltration needs information-flow tracking we do not have | MCPHunt README; IFG-Guard (KB02) |

## Conclusion

The comparison changes what the paper should claim. The repo's earlier positioning treated per-agent baselining at MCP servers as something only proposed (Errico) or sold without evidence. That is no longer accurate. Microsoft now documents agent-level behaviour detections with a learning mode and a separate early-life detector, and Exabeam documents agent baselines that cover MCP. Our defensible novelty therefore moves away from "baselining agents" and onto two things nobody else has: a **severity prior derived from the organisation's own policy**, and a **bounded, argument-free behaviour factor applied to a per-call price**.

The bounded factor is also where the literature is most sceptical. Its discount below ×1 is undocumented elsewhere, and it is exactly the surface that boiling-frog and fresh-identity results attack. It is defensible only with three guards: enforcement never goes below the static price, discounts are earned only after maturity, and an early-life check that ignores history covers new identities. Without those guards it inherits UEBA's best-known failures without UEBA's peer groups and accumulation. The largest remaining gap is evidence, not design. No public dataset combines MCP traffic, multi-day per-agent history and independent labels, so outside UEBA datasets and the A→S MCP benchmarks are the only external checks available until one exists.

## References

Tags: **[NEW]** means absent from the repo's existing coverage. Otherwise, the file that already covers the work is given in parentheses: KB02, KB03, KB04, KB06, KB07, CB (context brief), refs.bib, refs-full.bib, LR (paper literature review), CMP (Compass comparison), ANN (annotated bibliography), GAP (gap matrix), GW (gateway architecture). Coverage was checked by arXiv ID, DOI and name search over those files on 2026-11-04.

### MCP risk scoring, academic (30)

- Kumar et al., MCP-in-SoS, 2026, [arXiv:2603.10194](https://arxiv.org/abs/2603.10194) (refs.bib, LR, CMP)
- Shen, Toyoda, Leung, MCPThreatHive, 2026, [arXiv:2604.13849](https://arxiv.org/abs/2604.13849) (LR)
- C. Huang et al., MCP threat modeling with STRIDE + DREAD, 2026, [arXiv:2603.22489](https://arxiv.org/abs/2603.22489) **[NEW]**
- Anbiaee et al., threat modeling for MCP, A2A, Agora, ANP, *JISA* 2026, [arXiv:2602.11327](https://arxiv.org/abs/2602.11327) (CMP)
- Huang, Huang, Fard, mcp-sec-audit, 2026, [arXiv:2603.21641](https://arxiv.org/abs/2603.21641) (refs.bib)
- Kraishan, Same Name, Different Server (silent-drift census), 2026, [arXiv:2609.14119](https://arxiv.org/abs/2609.14119) **[NEW]**
- Chen et al., Rethinking MCP Security (MCPZoo study), 2026, [arXiv:2607.11086](https://arxiv.org/abs/2607.11086) **[NEW]**; Wu et al., MCPZoo dataset, 2025, [arXiv:2512.15144](https://arxiv.org/abs/2512.15144) **[NEW]**
- An et al., FlowGuard, 2026, [arXiv:2607.14754](https://arxiv.org/abs/2607.14754) **[NEW]**
- Padilla, Exposed by Design / Corvus, 2026, [arXiv:2608.00150](https://arxiv.org/abs/2608.00150) **[NEW]**
- Zhou et al., MCPShield (security cognition layer), 2026, [arXiv:2602.14281](https://arxiv.org/abs/2602.14281) (KB02, refs-full.bib)
- Xing et al., MCP-Guard, 2025, [arXiv:2508.10991](https://arxiv.org/abs/2508.10991) (KB02, refs.bib)
- Yergattikar, ShieldMCP, ACL 2026 Industry, [2026.acl-industry.58](https://aclanthology.org/2026.acl-industry.58/) **[NEW]**
- C. Yang, AgentTrust, 2026, [arXiv:2605.04785](https://arxiv.org/abs/2605.04785) (refs.bib)
- Y. Li et al., ConLeash ("Options, Not Clicks"), 2026, [arXiv:2605.11360](https://arxiv.org/abs/2605.11360) (refs.bib)
- Narajala, Huang, Habler, zero-trust tool registry, 2025, [arXiv:2504.19951](https://arxiv.org/abs/2504.19951) **[NEW]**
- Son, Governed MCP, 2026, [arXiv:2604.16870](https://arxiv.org/abs/2604.16870) (KB02)
- Narayan et al., ChainWatch, 2026, [arXiv:2607.19432](https://arxiv.org/abs/2607.19432) (KB02)
- Zhan et al., AegisMCP, 2025, [arXiv:2510.19462](https://arxiv.org/abs/2510.19462) (KB02)
- Shi et al., SecMCP, 2025, [arXiv:2508.06418](https://arxiv.org/abs/2508.06418) (KB02)
- Tu, Tu, Task-conditioned least privilege, 2026, [arXiv:2608.18351](https://arxiv.org/abs/2608.18351) **[NEW]**
- Jamshidi et al., Semantic Attacks on Tool-Augmented LLMs, 2025, [arXiv:2512.06556](https://arxiv.org/abs/2512.06556) **[NEW]**
- Jing et al., MCIP, EMNLP 2025, [arXiv:2505.14590](https://arxiv.org/abs/2505.14590) (ANN, mcip-summary)
- Zhao et al., Parasites in the Toolchain, IEEE S&P 2026, [arXiv:2509.06572](https://arxiv.org/abs/2509.06572) (KB02, refs.bib)
- Fu et al., MCP-RiskCue, 2025, [arXiv:2511.05867](https://arxiv.org/abs/2511.05867) (KB02, refs.bib)
- Z. Li et al., We Urgently Need Privilege Management in MCP, 2025, [arXiv:2507.06250](https://arxiv.org/abs/2507.06250) (refs.bib)
- Z. Li et al., description–code inconsistency, 2026, [arXiv:2602.03580](https://arxiv.org/abs/2602.03580) **[NEW]**
- Priya, Taylor, Araujo, AEGIS (cross-domain resource abuse), 2026, [arXiv:2608.20481](https://arxiv.org/abs/2608.20481) **[NEW]**
- Z. Huang et al., My Credentials, Please (MCP-FSD), 2026, [arXiv:2610.22301](https://arxiv.org/abs/2610.22301) **[NEW]**
- Yao et al., When Neither Side Confirms, 2026, [arXiv:2611.02527](https://arxiv.org/abs/2611.02527) **[NEW]**
- Z. Wang et al., MindGuard, 2025, [arXiv:2508.20412](https://arxiv.org/abs/2508.20412) (KB02)

### MCP industry systems and standards

- Harness MCP Risk Score, [docs](https://developer.harness.io/ai-security/mcp-risk-score) **[NEW]**
- Akto risk score, [docs](https://ai-security-docs.akto.io/akto-argus-agentic-ai-security-for-homegrown-ai/agentic-ai-discovery/concepts/risk-score) **[NEW]**
- Wallarm endpoint and MCP primitive risk score, [docs](https://docs.wallarm.com/api-discovery/risk-score/) **[NEW]**
- Snyk Agent Scan, [risks.md](https://github.com/snyk/agent-scan/blob/HEAD/docs/risks.md) (GAP); Snyk Evo Agent Supply Chain Security, [docs](https://docs.snyk.io/agent-security/evo-by-snyk/agentic-development-security-ads/agent-supply-chain-security) **[NEW]**
- Cisco AI Defense MCP Scanner, [GitHub](https://github.com/cisco-ai-defense/mcp-scanner/) (GAP)
- Docker MCP Gateway, [security.md](https://github.com/docker/mcp-gateway/blob/main/docs/security.md) **[NEW]**
- Pomerium MCP, [docs](https://www.pomerium.com/docs/capabilities/mcp) **[NEW]**; agentgateway, [docs](https://agentgateway.dev/docs/kubernetes/latest/documentation/mcp/tool-access/) (GW); Kong AI MCP Proxy, [docs](https://developer.konghq.com/plugins/ai-mcp-proxy/) **[NEW]**; AWS AgentCore Policy, [docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-getting-started.html) (GW)
- Golf Firewall, [docs](https://docs.golf.dev/golf-firewall) **[NEW]**
- HarrisonCN mcp-gateway v6.6.0, [PR #87](https://github.com/HarrisonCN/mcp-gateway/pull/87) **[NEW]**; TrueFoundry MCP gateway, [blog](https://www.truefoundry.com/blog/claude-code-enterprise-mcp-gateway) **[NEW]**
- AxioRank mcpaudit, [GitHub](https://github.com/AxioRank/mcpaudit) **[NEW]**
- OWASP MCP Top 10, [OWASP](https://owasp.org/www-project-mcp-top-10/) (KB02, refs.bib); OWASP Top 10 for Agentic Applications, secondary [summary](https://www.humansecurity.com/learn/blog/owasp-top-10-agentic-applications/) (refs-full.bib)
- CoSAI, Model Context Protocol Security, 2026, [PDF](https://www.coalitionforsecureai.org/wp-content/uploads/2026/03/model-context-protocol-security-1.pdf) **[NEW]**
- MCP Security Best Practices, [spec](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices) (spec revisions in KB02, GW)
- NIST NCCoE COSAiS working session, 2026, [slides](https://www.nccoe.nist.gov/sites/default/files/2026-05/Cyber-AI-Profile-Working-Session-Extending-Tech-Content-Slides-Slido.pdf) **[NEW]**

### Broader MCP security

- Hou et al., MCP Landscape, 2025, [arXiv:2503.23278](https://arxiv.org/abs/2503.23278) (KB02, refs.bib)
- Errico, Ngiam, Sojan, Securing MCP, 2025, [arXiv:2511.20920](https://arxiv.org/abs/2511.20920) (KB02, GW)
- Krakauer et al., Where Does MCP Security End?, 2026, [arXiv:2611.02611](https://arxiv.org/abs/2611.02611) **[NEW]**
- Acharya, Gupta, formal framework "MCPSHIELD", 2026, [arXiv:2604.05969](https://arxiv.org/abs/2604.05969) (CMP)
- Wang et al., MCPGuard (survey), 2025, [arXiv:2510.23673](https://arxiv.org/abs/2510.23673) **[NEW]**
- Surapani et al., Authorization Architectures for Tool-Using AI Agents, 2026, [arXiv:2609.15906](https://arxiv.org/abs/2609.15906) **[NEW]**
- Li et al., MCPHunt, 2026, [arXiv:2604.27819](https://arxiv.org/abs/2604.27819) (KB02)
- Mehta et al., FragBench, 2026, [arXiv:2605.11029](https://arxiv.org/abs/2605.11029) (KB02)
- Birhan et al., COPEX, 2026, [arXiv:2610.04378](https://arxiv.org/abs/2610.04378) **[NEW]**
- T. Liu, HCP security invariants, 2026, [arXiv:2606.29073](https://arxiv.org/abs/2606.29073) (KB02)
- Ahmed, Abbas, Labels Are Not Endpoints, 2026, [arXiv:2608.12880](https://arxiv.org/abs/2608.12880) (KB02)
- Abasıkeleş Turgut et al., CASCADE record-level audit, 2026, [arXiv:2604.17125](https://arxiv.org/abs/2604.17125) **[NEW]**
- Rostamzadeh et al., TrustShiftProbe, 2026, [arXiv:2608.23763](https://arxiv.org/abs/2608.23763) (KB02)
- Zhang et al., RAC, 2026, [arXiv:2609.23498](https://arxiv.org/abs/2609.23498) (KB02)
- Sohail, When Agents Look Like Beacons, 2026, [arXiv:2609.19091](https://arxiv.org/abs/2609.19091) **[NEW]**
- Uppala, Prompts Don't Protect, 2026, [arXiv:2605.18414](https://arxiv.org/abs/2605.18414) (refs-full.bib)
- Li et al., Zero-Trust Authorization and Discovery for Enterprise MCP, 2026, [arXiv:2609.22573](https://arxiv.org/abs/2609.22573) **[NEW]**
- Baig et al., The Stochastic Deputy, 2026, [arXiv:2609.14780](https://arxiv.org/abs/2609.14780) **[NEW]**
- Kim et al., SecureMCP, 2026, [arXiv:2605.05260](https://arxiv.org/abs/2605.05260) **[NEW]**
- Kabbinamakki Suresh et al., AgentCap, 2026, [arXiv:2611.00729](https://arxiv.org/abs/2611.00729) **[NEW]**
- Mandato, 2026, [arXiv:2608.14074](https://arxiv.org/abs/2608.14074) **[NEW]**; KedgeFlow, 2026, [arXiv:2610.14810](https://arxiv.org/abs/2610.14810) **[NEW]**
- CapSeal, 2026, [arXiv:2604.16762](https://arxiv.org/abs/2604.16762) **[NEW]**; Metere, mcp-attested, 2026, [arXiv:2605.24248](https://arxiv.org/abs/2605.24248) **[NEW]**
- Zhou et al., Authentication Security in Real-World Remote MCP Servers, 2026, [arXiv:2605.22333](https://arxiv.org/abs/2605.22333) **[NEW]** (named in CITATION-AUDIT.md as a replacement citation)
- Kumar et al., A Gateway Architecture for Enterprise MCP Authentication, 2026, [arXiv:2608.10760](https://arxiv.org/abs/2608.10760) **[NEW]**
- Prakash, AIP, 2026, [arXiv:2603.24775](https://arxiv.org/abs/2603.24775) **[NEW]**
- Dantuluri, Sundi, Delegation Without Trust, 2026, [arXiv:2609.00267](https://arxiv.org/abs/2609.00267) **[NEW]**
- Y. Huang et al., caller identity confusion in MCP, 2026, [arXiv:2603.07473](https://arxiv.org/abs/2603.07473) (refs-full.bib) — **WITHDRAWN by its authors; do not cite**
- Croce, Trivial Trojans, 2025, [arXiv:2507.19880](https://arxiv.org/abs/2507.19880) **[NEW]**
- Hu et al., Log-To-Leak, 2026, [arXiv:2610.36108](https://arxiv.org/abs/2610.36108) **[NEW]**
- Dang, Praetor, 2026, [arXiv:2604.26274](https://arxiv.org/abs/2604.26274) (KB02)
- Name-collision references: MCPSec no-box analysis, [arXiv:2609.10854](https://arxiv.org/abs/2609.10854) **[NEW]**

### UEBA, academic and standards

- Denning, An Intrusion-Detection Model, IEEE TSE 1987, [doi:10.1109/TSE.1987.232894](https://doi.org/10.1109/TSE.1987.232894) **[NEW]**
- Lunt et al., IDES final report, SRI 1992, [PDF](https://csl.sri.com/papers/9sri/9sri.pdf) **[NEW]**; IDES enhanced prototype, SRI, [PDF](https://www.csl.sri.com/papers/1sri/1sri.pdf) **[NEW]**
- Javitz, Valdes, NIDES statistical component, SRI 1994, [PDF](https://csl.sri.com/papers/2sri/2sri.pdf) (CB)
- Eldardiry et al., IEEE SPW 2013, [doi:10.1109/SPW.2013.14](https://doi.org/10.1109/SPW.2013.14) **[NEW]**
- Turcotte et al., learned peer groups, IEEE ISI 2016, [doi:10.1109/ISI.2016.7745472](https://doi.org/10.1109/ISI.2016.7745472) **[NEW]**
- Jordan, Chen, Enterprise GitHub UEBA, IEEE SecDev 2025, [doi:10.1109/SecDev66745.2025.00021](https://doi.org/10.1109/SecDev66745.2025.00021) **[NEW]**
- Tuor et al., AAAI-17 workshop, [arXiv:1710.00811](https://arxiv.org/abs/1710.00811) (KB03, KB07)
- Le, Zincir-Heywood, unsupervised ensembles, IEEE TNSM 2021, [doi:10.1109/TNSM.2021.3071928](https://doi.org/10.1109/TNSM.2021.3071928) **[NEW]**
- Heard, Rubin-Delanchy, p-value combiners, Biometrika 2018, [doi:10.1093/biomet/asx076](https://doi.org/10.1093/biomet/asx076) (KB04)
- Goldberg et al., HICSS 2016, [doi:10.1109/HICSS.2016.344](https://doi.org/10.1109/HICSS.2016.344) **[NEW]**
- Ho et al., credential spearphishing / DAS, USENIX Security 2017, [PDF](https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-ho.pdf) (KB03, KB07)
- Garchery, Granitzer, ADSAGE, 2020, [arXiv:2007.06985](https://arxiv.org/abs/2007.06985) **[NEW]**
- Kent, LANL multi-source events, [LANL](https://csr.lanl.gov/data/cyber1/) (KB03)
- Landauer et al., real cloud UEBA dataset (CLUE-LDS), IEEE BigData 2022, [doi:10.1109/BigData55660.2022.10020672](https://doi.org/10.1109/BigData55660.2022.10020672) (KB03)
- Rubinstein et al., boiling frog, ACM IMC 2009, [doi:10.1145/1644893.1644895](https://doi.org/10.1145/1644893.1644895) (KB06)
- Kloft, Laskov, JMLR 2012, [PDF](https://www.jmlr.org/papers/volume13/kloft12b/kloft12b.pdf) (KB06)
- Alahmadi, Axon, Martinovic, USENIX Security 2022, [PDF](https://www.usenix.org/system/files/sec22-alahmadi.pdf) (KB07)
- NIST SP 800-207, [doi:10.6028/NIST.SP.800-207](https://doi.org/10.6028/NIST.SP.800-207) (GW, LR)
- NIST SP 800-53 Rev. 5, AC-2(12), [doi:10.6028/NIST.SP.800-53r5](https://doi.org/10.6028/NIST.SP.800-53r5) **[NEW]**
- Gartner UBA/UEBA history via Litan quote, [Dataconomy](https://dataconomy.com/2016/08/03/iot-security/) **[NEW]** (secondary source)

### UEBA, commercial, and behaviour analytics for AI agents

- Exabeam Advanced Analytics, [docs](https://docs.exabeam.com/en/advanced-analytics/i56/advanced-analytics-user-guide/113551-get-to-know-a-user-profile.html) (KB03)
- Splunk ES risk-based alerting, [docs](https://help.splunk.com/en/splunk-enterprise-security-7/risk-based-alerting/7.3/introduction/how-risk-based-alerting-works-in-splunk-enterprise-security) (KB03)
- Microsoft Sentinel UEBA, [docs](https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics) (KB03)
- Elastic entity risk scoring, [docs](https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-risk-scoring) **[NEW]** (Elastic ML anomaly jobs are in KB03)
- Google SecOps Risk Analytics, [docs](https://docs.cloud.google.com/chronicle/docs/detection/risk-analytics-overview) **[NEW]**
- Microsoft Entra ID Protection, workload identities, [docs](https://learn.microsoft.com/en-us/entra/id-protection/concept-workload-identity-risk) **[NEW]**
- Microsoft Entra ID Protection for agents, [docs](https://learn.microsoft.com/en-us/entra/id-protection/concept-risky-agents) **[NEW]**
- Exabeam Agent Behavior Analytics white paper, [PDF](https://www.exabeam.com/wp-content/uploads/WHITEPAPER-Agent-Behavior-Analytics-Securing-the-Autonomous-Enterprise.pdf) (KB02)
- Securonix UEBA/AEBA, [page](https://www.securonix.com/products/ueba/) **[NEW]**
- Palo Alto SaaS Security user risk scoring, [docs](https://docs.paloaltonetworks.com/saas-security/behavior-threats/user-risk-scoring) **[NEW]** (search snippet only)
- Noma Security MCP governance, [Help Net Security](https://www.helpnetsecurity.com/2026/06/02/noma-brings-visibility-and-access-governance-to-ai-agents-and-mcp-servers/) **[NEW]**
- MI9, 2025, [arXiv:2508.03858](https://arxiv.org/abs/2508.03858) **[NEW]**
- Decomposition Attacks Across Unlinkable Identities, 2026, [arXiv:2608.17445](https://arxiv.org/abs/2608.17445) **[NEW]**
- Stateful Online Monitoring Catches Distributed Agent Attacks, 2026, [arXiv:2605.31593](https://arxiv.org/abs/2605.31593) **[NEW]**
- HBEE, 2026, [arXiv:2605.07472](https://arxiv.org/abs/2605.07472) **[NEW]**
- Fingerprinting AI Coding Agents on GitHub, 2026, [arXiv:2601.17406](https://arxiv.org/abs/2601.17406) **[NEW]**
- MARK, "Whose Agent Are You?", 2026, [arXiv:2606.20910](https://arxiv.org/abs/2606.20910) **[NEW]**

### Local repository sources

- [paper_v5/main.tex](/home/ovadyat/MCP/paper_v5/main.tex), [paper_v5/GROUND-TRUTH.md](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md), [paper_v5/CITATION-AUDIT.md](/home/ovadyat/MCP/paper_v5/CITATION-AUDIT.md), [paper_v5/refs.bib](/home/ovadyat/MCP/paper_v5/refs.bib), [paper_v5/refs-full.bib](/home/ovadyat/MCP/paper_v5/refs-full.bib)
- [src/mcp_security/gateway/framework.py](/home/ovadyat/MCP/src/mcp_security/gateway/framework.py), [src/mcp_security/gateway/README.md](/home/ovadyat/MCP/src/mcp_security/gateway/README.md), [src/mcp_security/behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md)
- [docs/project/dynamic-layer-explained.md](/home/ovadyat/MCP/docs/project/dynamic-layer-explained.md), [docs/project/gateway-architecture.md](/home/ovadyat/MCP/docs/project/gateway-architecture.md), [reports/evaluation/scanner_vs_human.md](/home/ovadyat/MCP/reports/evaluation/scanner_vs_human.md), [reports/experiments/gateway/mcphunt/README.md](/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/README.md)
- [KB02](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/02-mcp-runtime-security-literature.md), [KB03](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/03-ueba-insider-threat-and-datasets.md), [KB06](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/06-threat-model-and-evasion.md), [context brief](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md)
- Project memory: [dynamic-layer-v5-decisions.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/dynamic-layer-v5-decisions.md)
