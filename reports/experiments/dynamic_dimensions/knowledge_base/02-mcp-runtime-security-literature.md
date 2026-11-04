# MCP runtime security, 2024–2026: what exists and where the dynamic layer stands

This note surveys MCP-specific runtime security work (gateways and proxies, runtime monitors and
anomaly detectors, benchmarks, taxonomies and public traffic) and compares each piece with the
dynamic layer, the per-caller behaviour multiplier `M ∈ [0.7, 5]` of
[`DIMENSION_FORMULAS.md`](../DIMENSION_FORMULAS.md) (v4). Every work below was checked on a primary
source opened on 2026-10-25 (arXiv API metadata plus the abstract or HTML page, a venue page, a
spec page, or the project's own repository or dataset card); anything not opened is marked
**UNVERIFIED**. Threat model as everywhere in this repo: the MCP server is the protected asset,
the calling agent is the threat.

## Scope, method and legend

- **In scope:** MCP-specific work only (project rule). Agent tool-call monitors are included only
  when they sit at the MCP boundary or are evaluated on MCP. Non-MCP agent guards that the paper
  already cites (AgentGuardian, AgentTrust, NEXUS, STARS, Progent, MiniScope) were screened by
  abstract and left out because their abstracts report no MCP evaluation.
- **Search:** arXiv / Semantic Scholar (research tool), Exa and web search, 2024 to 2026-10-25.
  Metadata (authors, dates, journal refs, DOIs) comes from the arXiv API, not from search
  snippets.
- **Direction** of each work:
  - **A→S**: the agent or caller is the threat; the server, its data or its host is protected
    (our direction).
  - **S→A**: a malicious server, tool or injected content is the threat; the agent or its user is
    protected.
  - **Mixed**: both.
- **Per-caller baseline** means: the work compares a call with *the same caller's own past*. A
  model trained on all traffic, a fixed threshold, or a per-session state is not one.

## The dynamic layer in four lines, for comparison

1. Each call is scored against the **same agent's last 90 days**, on 15 dimensions in three
   groups: Typical Cadence and Typical Footprint (graded, per agent), Red Flags (yes/no, one line
   for every agent).
2. Scores are closed-form (excess and rarity, both `x / (x + 2)`), use **no arguments** except
   request size, and the **strongest score alone** sets `M`, with its dimension as the reason.
3. `M` multiplies a static capability score, `R = R_static × M ∈ [0.7, 25]`. It never blocks
   on its own; other agents can only lower a score (org discount).
4. Evaluation so far: five simulated GitHub organisations (60–300 agents, 180 days, last 90
   scored), mostly ordinary traffic with labelled life and org changes and 460 gray episodes;
   2.46% of ordinary agent-days reach ×3 on average, 70.7% of gray episodes are caught at ×3.

## Runtime monitors, gateways and guards in our direction (A→S or mixed)

Ordered by how close they are to the dynamic layer. Citations are in [References](#references).

| # | Work | Dir. | Where it sits | What it detects | Per-caller baseline? | Evaluation | How the dynamic layer differs |
|---|---|---|---|---|---|---|---|
| [1] | **MCP Guardian** (Kumar et al., arXiv 2504.12757, 2025) | Mixed | Middleware overriding the MCP `invoke_tool` method | Invalid API tokens; per-token request rate over a fixed limit (example: 5 requests per minute → HTTP 429); regex WAF on arguments (`rm -rf`, SQL injection, sensitive paths); logs each call with user/agent, tool, parameters | **No.** Fixed per-token threshold. The authors list per-agent identities and quotas, when several LLMs share one Guardian, as a limitation for future work | One weather MCP server on a VM; scenario tests (destructive command blocked, 100 rapid calls cut at 5); +3–4 ms median latency (10–15%). No false-positive rate on benign traffic | Rate is graded against the agent's own usual, not one number for all; the layer scores instead of blocking; false alarms are measured per agent-day over 90 days |
| [2] | **AegisMCP** (Zhan, Al Sadi, Li, Haddadi, arXiv 2510.19462, 2025) | A→S | Protocol-level instrumentation of the MCP control plane in smart homes (NEBULA schema), streaming heterogeneous temporal graph | Attack sessions: instruction-driven escalation, chain-of-tool exfiltration, malicious server registration, persistence | **No.** Its novelty cue is a TTL rarity over (source type, event type, destination type) triples plus unseen destinations, not per-agent history; a self-supervised model learns "normal" per home | Emulated smart-home testbed plus a physical bench, synthesised 24–48 h of activity, 10% attack prevalence: AUROC 0.985, AP 0.947, 55.7% recall at 2% FPR; beats XGBoost, GRU, GCN, R-GCN, random forest and rules. Artefact release is stated both as done (abstract) and as "upon publication" (body) | Closed-form per-agent scores instead of a learned graph model; per-call `M` with a named reason instead of a session alarm; false alarms over 90 days of ordinary traffic instead of 1–2 days at a fixed attack prevalence |
| [3] | **Praetor** (Dang, arXiv 2604.26274, 2026). Boundary case: framed on the MCP dispatch layer but **not evaluated on MCP data** | A→S | Stateful gateway sidecar at the tool-call boundary | Any call with no edge in a parameterised DFA compiled offline from verified benign telemetry (tool sequences, 3-call context, parameter bounds); such a call is blocked | **Yes, per deployment**: the automaton is compiled from the telemetry of the agent it protects. Binary allow/block | Agent Security Bench (5 attack families, 1,000 attempts per family per scenario) and ToolBench benign traces (400 train / 100 test): 5.6% macro ASR, 2.0% benign task failure, 2.2 ms per call. After a 20% tool refresh the stale profile fails 24% of benign tasks until 350 sequences are human-approved | The closest idea (learn normal from the agent's own traffic), but an allowlist: anything unseen is blocked. The layer grades how unusual a new thing is *for this agent* (habit and org discounts, rolling 90 days), and adds time, rate, network and client |
| [4] | **Content-aware attack detection in MCP tool-call traffic** (Zavrak, arXiv 2605.11053, 2026; v1 was titled "MCPShield") | Mixed | Passive, post-session monitor of the full tool-call stream (names, arguments, responses); proposed beside MCP gateways | Attacked sessions (tool input or output manipulation, jailbreak, indirect injection) | **No.** Supervised classifiers (GNNs, MLP, tree ensembles) over session graphs | RAS-Eval (605 benign / 3,797 attacked sessions, MCP format), ATBench (502 / 497), and a combined set with 832 benign `mcpbench` sessions. **Metadata-only features plateau near AUROC 0.64**; SBERT content embeddings reach 0.975 (tree ensembles). Random splits inflate AUROC by up to 26 points over task-disjoint splits | Online per call, unsupervised per caller, argument-free. Their metadata-only result is the most direct challenge to an argument-free design; see [Implications](#implications-for-the-dynamic-layer) |
| [5] | **ADR** (C. Li, Hu, Xu, et al., MLSys 2026 Industry Track, arXiv 2605.17380) | Mixed | Endpoint sensor on employee machines: prompts, agent reasoning, MCP tool calls, environment | Credential exposure, exfiltration and multi-stage injection chains, via a two-tier LLM detector (triage, then reasoning with source code, threat intelligence and policy lookups) | **No** per-user or per-agent history is described; "normal versus suspicious" comes from the policy store and threat repository | Deployed at Uber over ten months (7,200+ hosts, 10,000+ sessions per day); ADR-Bench (302 tasks: 42 malicious, 260 benign, 133 MCP servers, 17 techniques; partly adapted from RAS-Eval and MCP-Artifact, benign tasks generated with GPT-4): 0 false positives, 67% of attacks detected | Needs prompts and reasoning from the host; the layer sees only what reaches the server. LLM per event versus closed-form arithmetic per call. Both put precision first |
| [6] | **FragBench** (Mehta, Selvanayagam, et al., arXiv 2605.11029, 2026) | A→S | Offline user-level detector over executed MCP sessions (24 FastMCP servers in a sandbox) | Malicious goals split into benign-looking fragments sent in separate sessions | **Partly.** Events are linked per user across sessions, but the detector is a supervised campaign classifier, not "normal for this user" | 24 campaigns from public incident reports; event-level F1 0.88–0.96 (GCN best); per the dataset card, 15,055 malicious and 5,440 benign sessions, CC-BY-4.0, with a gated tier | The only MCP work found that aggregates per caller *across sessions*. Unsupervised and graded in our case; their data is a candidate external test (below) |
| [7] | **ChainWatch** (Narayan, Jyoti, Singh, arXiv 2607.19432, 2026) | Mostly S→A (client and host trusted, servers adversarial) | Transparent proxy between client and servers | Multi-step kill-chain progression: HMM over a 20-dimensional per-call feature vector, five session rules | No | **None empirical**: the paper calls itself a design specification and traces five literature scenarios | Not comparable on numbers; opposite trust direction |
| [8] | **Governed MCP** (Son, arXiv 2604.16870, 2026) | A→S | Kernel-resident gateway in a research OS; six layers: schema, trust tier, token bucket, regex pre-filter, logit-based safety classifier, constitutional policy; Blake3 audit chain | Dangerous tool calls | **No.** Token bucket with fixed per-agent, per-tool limits | Author-written Custom-101 (37 dangerous / 64 benign MCP prompts): F1 0.789, 9 of 64 benign blocked (about 14%); Custom-260 (OS actions). Inference dominates latency (65 ms per call on a 7B model, per the abstract) | Semantic classification of each call versus behaviour against the caller's past; fixed limits versus per-agent usual |
| [9] | **Runtime Policy Enforcement for MCP-Based LLM Agents** (Wang, Zhu, Li, *Electronics* 15(13):2829, MDPI, 2026) | A→S | Policy enforcement point at the tool-call boundary; SHA-256 hash-chained JSONL audit log | Path traversal, user-guided exfiltration, cross-server taint, high-risk tools, **high-frequency tool abuse** (per-tool rate caps), with cross-step source-integrity and sensitivity labels | **No.** Five declarative rules with fixed caps | 30-task controlled dataset, 1,050 runs: ASR 40% → 5%; 30% task-level false positives from capability-token denials, 0/30 rule false positives; a preliminary run on a real MCP stdio filesystem server; ~60 µs P50 per call | Deterministic allow/deny; close to our Red Flags (rate caps ≈ burst, labels ≈ unsafe sequence) but with no graded per-agent part. Hash-chained logs are common ground, not a novelty for us |
| [10] | **RAC: Runtime Authorization Consistency Checking** (Zhang, Lee, Zhuang, Peng, arXiv 2609.23498, 2026) | A→S | Controller-side pre-commit guard | "Authorization drift": a workflow whose steps are each allowed but which together exceed the session's authorization | **No.** State is the session's accepted lineage | TraceBench (1,248 workflows): no missed blocks versus 509 of 1,008 for the best Static+History baseline; 92.8% block recall on LLM-generated plans; real MCP filesystem replay stops 9 unsafe continuations; sub-ms p99 | Authorization logic within one session versus behaviour across 90 days; complementary to our unsafe-sequence flag |
| [11] | **HCP** (T. Liu, arXiv 2606.29073, 2026) | A→S | Reference runtime for MCP-style execution | Violations of eight invariants, including principal binding, scoped capability invocation, deny-path audit and explicit protocol state | No | 10 benchmark cases: naive baseline permits all, a mitigation baseline 6, HCP blocks 10 | A protocol redesign versus a drop-in gateway score on the current protocol |
| [13] | **MCP-Guard** (Xing et al., arXiv 2508.10991, 2025) | Mostly S→A (prompt injection, exfiltration in LLM–tool interactions) | Three-stage pipeline: static scan, fine-tuned E5 detector, LLM arbitrator | Adversarial prompts and tool content | No | MCP-AttackBench (70,448 samples, GPT-4 augmented); 96.01% accuracy for the E5 model | Content classification; the layer reads no arguments |
| [14] | **MTGuard** (He, Xie, Y. Li, Ji, arXiv 2607.25297, 2026) | Mixed | Separate guard agent; eBPF-monitored Docker sandbox; pre-, in- and post-execution checks | Harmful tool use, including host-side execution hijacking | No | Browser-automation and financial-analysis scenarios from MCP-SafetyBench: 48.3% of unsafe calls detected versus 8.3% for baselines, 3.7% FPR, ~10 s extra latency | Execution-level evidence on the host versus protocol-level behaviour at the server |

**CrossMCP-Bench's IFG-Guard** [12], a deterministic information-flow guard released with the
benchmark, reports 92.0% detection and 0.0% FPR on 134 scenarios; it is listed with the datasets
below.

## Work in the opposite direction (S→A), kept for contrast

These protect the agent or its host from a malicious server or tool. They are not competitors,
but reviewers may cite them as "MCP runtime anomaly detection".

| # | Work | What it detects, and how | Note for us |
|---|---|---|---|
| [15] | MindGuard (Z. Wang et al., arXiv 2508.20412, 2025; v3 retitled "Intrinsic Decision Inspection for Securing LLM Agents Against Metadata Poisoning") | Tool-poisoning decisions, from attention-based decision dependence graphs; 94–99% average precision | Needs model internals |
| [16] | MCPShield (Zhou et al., arXiv 2602.14281, 2026) | Untrusted servers, by agent-side probing, isolated execution and periodic reasoning over the agent's history of each server; 76 malicious servers, 95.3% defense rate | Learns a baseline **of the server**, not of the caller |
| [17] | TrustShiftProbe / SHIELD (Rostamzadeh et al., arXiv 2608.23763, 2026) | Servers that behave well, then defect; SHIELD audits server payloads against **behavioural baselines learned during clean trust windows**; ASR 69.5% → 42.7% | The only MCP work found that learns a temporal behavioural baseline and scores drift, but for servers |
| [18] | Connor (Huang et al., arXiv 2604.01905, 2026) | Malicious servers, by tool behaviour deviating from its declared function intent; 114 PoC servers, F1 94.6% | |
| [19] | MCP-RiskCue (Fu, Zhang, Wang, arXiv 2511.05867, 2025) | LLMs judging risk in synthetic server system logs (1,800 logs, 243 servers); GRPO-trained Llama-3.1-8B reaches 83% accuracy | The paper's `refs.bib` files it under "risk scoring aimed at MCP"; its direction is S→A |
| [20] | SecMCP (Shi et al., arXiv 2508.06418, 2025) | Conversation drift in the agent's latent activations; average AUROC 0.98 | Needs model internals |
| [21] | MCP-SandboxScan / SandScope (Tan et al., arXiv 2601.01241, 2026) | Source-to-sink witnesses when executing MCP tools under WASI or stdio | Audit, not runtime gating |
| [22] | Yamasaki, Toda, Mori (IEICE Tech. Rep. ICSS2025-139, 2026) | Malicious servers: proxy-recorded tool requests correlated with OS audit logs; P 1.00, R 0.81 on 21 scenarios | |
| [23] | AgentBound (Bühler et al., FSE 2026, doi:10.1145/3808103) | Contains MCP servers with declarative, Android-style permissions | Host protected from the server |

## Benchmarks, taxonomies and datasets

The last column asks the question that matters for the dynamic layer: does the data carry a
stable caller identity across sessions and days, so that a per-caller baseline can be learned?

| # | Name | Direction covered | Content | Real or synthetic | Per-caller, multi-day history? |
|---|---|---|---|---|---|
| [24] | MCPSecBench (Yang et al., arXiv 2508.13220) | Mixed | 17 attack types on 4 surfaces (client, protocol, server, host). Caller-side: prompt injection, tool misuse via "Confused AI", slash-command overlap, sandbox escape | Playground on Claude, OpenAI and Cursor hosts | No |
| [25] | MSB (D. Zhang et al., ICLR 2026, arXiv 2510.15994) | S→A | 12 attacks, 2,000 instances, 405 tools, metric NRP | Real tools via MCP | No |
| [26] | MCP-SafetyBench (Zong et al., arXiv 2512.15163) | Mostly S→A | 20 attack types: 11 server-side, 4 host-side, 5 user-side; the user-side harms fall on the user's environment | Real MCP servers, 5 domains | No |
| [27] | MCPTox (Z. Wang et al., AAAI, doi:10.1609/aaai.v40i42.40895 per arXiv) | S→A | Tool poisoning: 45 servers, 353 tools, 1,348 cases | Real servers | No |
| [13] | MCP-AttackBench | S→A | 70,448 text samples | GPT-4 augmented | No |
| [28] | MCIP benchmark (Jing et al., EMNLP 2025, doi:10.18653/v1/2025.emnlp-main.62) | Mixed | Taxonomy of unsafe MCP behaviours, benchmark and training data | Construction not checked | No |
| [29] | RAS-Eval (Fu, Yuan, Wang, arXiv 2506.15253) | Mixed (11 CWE categories, e.g. command and SQL injection) | 80 test cases, 3,802 attack tasks; JSON, LangGraph and MCP tool formats | Real and simulated execution | No |
| [5] | ADR-Bench | Mixed | 302 tasks (42 / 260), 133 MCP servers, 17 techniques; repository `github.com/uber/ADR` named in the paper (**not opened**) | Mixed; emulated execution | No |
| [12] | CrossMCP-Bench (Anonymous; the card names NeurIPS 2026 Datasets & Benchmarks, venue **UNVERIFIED**) | A→S | 134 core scenarios (75 attack, 59 benign) plus 53 independent benign; labels conditioned on an authorization context; DR and FPR; LLM guards have 8.5–28.8% FPR | Fully synthetic. The card states: "no production MCP corpus with ground-truth labels exists" | No |
| [30] | MCPHunt (H. Li et al., arXiv 2604.27819) | A→S (non-adversarial credential propagation across servers) | 3,615 traces, 5 models, 147 tasks; policy-violating propagation 11.5–41.3%; CC BY 4.0 on Hugging Face | Controlled | No |
| [6] | FragBench | A→S | 24 campaigns, fragments spread over sessions, benign cover sessions | Sandboxed execution of LLM-rewritten fragments | **Per-user linkage across sessions**; time span not stated in what we read |
| [19] | MCP-RiskCue | S→A | 1,800 server logs, 2,421 training chats, 471 evaluation queries | LLM-generated | No |
| [31] | GatewayBench (Zheng, Chen, H. Li, B. Li, arXiv 2610.23449) | Mostly S→A | 524 tasks; 11,118 real tools from 251 servers; 7 gateways (agentcore, agentgateway, litellm, lunar, enkrypt, strata, bifrost); TSR and ASR | Real tools, task episodes | No |
| [32] | `cx-cmu/agent_trajectories`, `mcpbench` split | Benign | 899 MCP-Bench trajectories, 5 models × 4 passes, run under a "distraction" condition | Real model runs | No |
| [33] | "Labels Are Not Endpoints" (Ahmed, Abbas, arXiv 2608.12880) | Method | Audit of an MCP security campaign: treatment metadata leaked into the attack-success label; 58 labels corrected to benign | — | — |

**Taxonomies that name the caller as a threat.** Hou et al. [34] list *malicious users* among
four attacker types. Errico, Ngiam and Sojan [35] name "agents who become unintentional
adversaries by over-stepping their role", and in §III-D propose, as a control, behavioural
baselines per user and role (typical tools, sequences, data volumes, access times) with alerts on
after-hours activity and volume spikes; neither the abstract nor that section reports an
implementation or an evaluation. MCP-38 [36] (38 categories mapped to
STRIDE and both OWASP lists) and MCP-DPT [37] (defense placement; gaps at host orchestration,
transport and supply chain) are protocol-wide. MCP Safety Audit [38] shows LLMs coerced into
using MCP tools to compromise the developer's own system. Song et al. [39], Zhao et al. [40] and
the S&P 2026 Parasites study [41] (12,230 tools across 1,360 servers) are S→A.

## What real MCP traffic looks like: honeypots

Public evidence on agents attacking MCP servers in the wild is thin, which supports evaluating
on ordinary traffic with gray risk rather than on attacks.

- **GreyNoise** [42] (blog, 2025-11-05): every MCP honeypot was found within days, but "no
  MCP-specific payload or exploitation attempts appeared".
- **workspace-tools-mcp** [43] (GitHub write-up, 12 days, 2026-06-17 to 06-29): a server listed
  in the official registry drew 1,081 `initialize` handshakes from 688 IPs, all indexers or
  scanners; an identical unlisted server drew none; one tool call in total (from an audit tool),
  zero prompt-injection compliances, zero canary triggers.
- **honeymcp** [44]: an open-source sensor that records `clientInfo`, `Mcp-Session-Id` and the
  claimed protocol version per request; it publishes no traffic statistics in the README read.
- **Kai Security honeypot**: 135 tool calls, one to a bait `get_aws_credentials` with
  `role="admin"`. Known only from a secondary summary [45]; the primary post was not opened:
  **UNVERIFIED**.

None of these is peer reviewed, and none releases a labelled per-caller corpus.

## Industry and standards that baseline agents

A reviewer may say "this is UEBA for agents". These are the sources that say it first.

- **IETF draft-sharif-aeba-00** [46] (Agent Event Behaviour Analysis; R. Sharif; Independent
  Submission, Informational, not IETF-endorsed; 2026-04-15, expiry 2026-10-17; a later revision
  was not checked). It defines per-agent baselines over a **24-hour** and a **90-day** window,
  peer groups, and a per-event deviation score in [0, 1] as a *weighted composite* whose weights
  are implementation-defined. It mentions MCP only by reference (OWASP MCP Top 10, an MCPS
  draft). No evaluation.
- **Exabeam Agent Behavior Analytics** [47] (vendor): behavioural baselines for agents, including
  MCP activity; the white paper says baselines mature in roughly 14 days. No public evaluation.
- **observability-mcp "Inspect"** [48] (open-source MCP gateway): learns a per-principal profile
  from observed calls (AppArmor-style observe → dry-run → enforce); flags calls outside accepted
  rules, such as a new tool; stores argument shapes, not payloads. Binary rules, no evaluation.
- **MCPKernel** [49] and **agentsentinel** [50] (open source): per-agent z-scores (2.5σ and 3σ)
  on session counts, tools, servers and call rate; agentsentinel adds a weighted Trust Score. No
  evaluation.
- **OpenTelemetry GenAI conventions for MCP** [51] (status: Development): the client-span table
  read lists `mcp.method.name`, `gen_ai.tool.name`, `mcp.session.id` and `mcp.resource.uri`, but
  no caller-identity attribute.
- **The MCP specification.** Authorization is OPTIONAL, and stdio implementations SHOULD NOT use
  it [53]: a per-caller baseline needs an identity that MCP itself does not guarantee. In revision
  2025-06-18 initialization MUST be the first interaction [52]; revision 2026-07-28 removes the
  `initialize` handshake and protocol-level sessions (SEP-2575, SEP-2567) [54]. The consequences
  for missing handshake and session duration are worked out in
  [`01-mcp-protocol.md`](01-mcp-protocol.md).

## Closest competitors a reviewer will name

1. **MCP Guardian [1]**, the MCP gateway with per-token rate limits and logging. Show a
   fixed-threshold arm (one rate limit for every token) on the simulated organisations.
2. **AegisMCP [2]**, the closest learned MCP anomaly detector. Show a global-rarity arm (rarity
   of a value across all traffic, not per agent).
3. **Praetor [3]** and **observability-mcp Inspect [48]**, "learn normal, block the rest". Show a
   per-agent allowlist arm (anything never seen raises `M` to the top) and report it on onboarding,
   role change and server-release days.
4. **Zavrak [4]**, metadata-only detection is weak. Answer in the threats to validity: their
   attacks are content-level injections inside single sessions with no caller history; the layer
   targets behavioural misuse by authenticated callers over time, and multiplies a static score
   that already prices capability. Do not claim the layer detects injection.
5. **ADR [5]**, production MCP detection at scale. Complementary: it needs prompts and
   reasoning on the host; the layer needs only what reaches the server.
6. **FragBench [6]**, per-user aggregation across sessions. Use as external data (below).
7. **The UEBA framing ([35] §III-D, [46], [47]).** Concede the idea; claim the mechanism and the
   evaluation (next section).
8. **Rule and authorization guards** ([8]–[11], [12]): complementary. Red Flags are the rule part
   of the layer; the graded groups exist because fixed lines flag ordinary life (new hires, role
   changes, releases).

## Positioning

We found 23 MCP runtime systems: the 22 rows of the two tables above plus CrossMCP-Bench's
IFG-Guard (Praetor is MCP-framed but not MCP-evaluated). Eleven of them protect the agent or its
host from a malicious server or injected content, and so do most MCP attack benchmarks (MSB,
MCPTox, most of MCP-SafetyBench). The systems that share our direction, protecting the server and
its data from the caller, do one of three things. They apply
fixed thresholds and rules per token or session (MCP Guardian, Governed MCP, the MDPI policy
enforcement point, RAC, CrossMCP-Bench's IFG-Guard). They classify sessions with a model trained
on labelled attacks (Zavrak; FragBench Defense; AegisMCP, whose novelty cue is global). Or they
reason over prompts and agent reasoning with an LLM (ADR). Praetor learns a per-deployment
envelope but blocks whatever falls outside it and is not evaluated on MCP data. None of the
academic systems we found grades each call against the same caller's own multi-week history. That
idea appears only as a governance recommendation without an evaluation (Errico et al., §III-D),
an individual IETF draft (AEBA), and vendor or open-source tools with no published evaluation.

What is new in the dynamic layer, stated so that it holds against these works:

1. **Per-caller, argument-free scores over MCP-native dimensions** (tool, asset, client from
   `clientInfo`, /16 network, handshake), computed in closed form from the caller's last 90 days.
2. **A bounded multiplier on a static capability score**, not a separate alarm: familiar
   behaviour lowers risk by at most 30%, strange behaviour raises it at most five-fold.
3. **One saturating shape and a max combiner**, so every score carries one named reason, adding a
   dimension cannot dilute a strange one or move the alert line, and AEBA-style weighted composites
   are avoided.
4. **Safety valves that can only lower a score** (habit discount, org discount): other agents
   never raise one.
5. **An evaluation on mostly ordinary traffic** that reports false alarms per agent-day under
   labelled life and org changes. The MCP evaluations we found measure detection per task or
   session, on benign sets from tens to about five thousand sessions, none with per-caller
   histories over weeks.

What we should **not** claim: the first MCP gateway; the first to baseline agent behaviour; the
first to detect misuse from metadata; the first tamper-evident log (Praetor, Governed MCP and the
MDPI enforcement point all hash-chain theirs). And our evidence is simulated: no public MCP dataset
we found carries per-caller histories spanning days.

## Implications for the dynamic layer

1. **Add competitor arms to the planned ablation** ([Future work](../DIMENSION_FORMULAS.md#future-work-ablation-study)):
   a fixed per-token rate limit ([1], [8]); global rarity instead of per-agent rarity ([2]); a
   per-agent allowlist ([3], [48]); per-agent z-scores ([49], [50]); a weighted mean instead of
   the max ([46]). Per the design doc, only the leave-one-out arms can reuse logged
   `Verdict.scores`; these arms change the scores or the combiner, so they need a rerun of
   `normal_org_sim.py`. Report false alarms per ordinary agent-day and gray episodes caught at ×3,
   as now.
2. **Answer the metadata-only result of [4]** in the paper's threats to validity (competitor 4
   above). If space allows, add one content-free comparison: their metadata-only AUROC of about
   0.64 is for injection sessions, a different target.
3. **External data.** FragBench [6] is the only public MCP corpus found that links sessions per
   user; check whether its timestamps span days before using it for Typical Cadence, and use it at
   least for cross-session breadth and unsafe sequence. CrossMCP-Bench [12] and MCPHunt [30] can
   test the unsafe-sequence flag only (single sessions, no history). The honeypots [42], [43]
   justify the gray-risk framing: almost no real attack traffic reaches MCP servers today.
4. **Protocol drift.** Missing handshake and session duration rely on `initialize` and sessions,
   which revision 2026-07-28 removes [54]. Competitors that key their state on a session
   (ChainWatch, RAC, AegisMCP's session DAGs, Zavrak, Praetor) need another session notion too; a
   per-caller baseline keyed on the OAuth subject does not. See
   [`01-mcp-protocol.md`](01-mcp-protocol.md).
5. **State the identity assumption.** Authorization is optional in MCP [53] and absent on stdio;
   the layer needs a caller identity (the gateway's OAuth sign-in or headers). Say what happens
   without one (fall back to client, network, session) or scope the claim to authenticated HTTP.
6. **Report gateway overhead per call.** Competitors do: MCP Guardian +3–4 ms, Praetor 2.2 ms,
   the MDPI enforcement point ~60 µs P50, RAC sub-ms p99.
7. **Labels.** Following [33], say that gray-episode labels come from the simulator by
   construction and are never derived from the scorer's output.
8. **Cite as motivation:** Errico et al. §III-D [35] for per-user behavioural baselines at MCP
   gateways, Hou et al. [34] for malicious users, the 2025-06-18 lifecycle [52] for the handshake.

## Notes on `paper_v5/refs.bib` (spotted, not changed)

- Duplicate keys: `betser2026agentrim`, `owireduashley2026severity`, `zhang2026stars`. Parasites
  appears twice under two keys (`zhao2026parasites`, `zhao2025parasites`).
- `zhu2025miniscope`: arXiv v2 is titled "MiniScope: Authorizing Agents with Least-Privilege
  Permissions"; author order on arXiv is Zhu, Huang, Tseng, Vernik, Patil, Fang, Popa.
- `betser2026agentrim`: arXiv order is Betser, Giloni, Bose, Padakandla, Picardi, Erez,
  Vainshtein; the arXiv comment says "EMNLP 2026 Findings".
- `rahman2026rolestratified`: arXiv v2 adds Md Hasibul Amin between Tasnia and Ahona.
- `fu2025riskcue`: S→A (malicious servers), although filed under "risk scoring aimed at MCP".

## References

All accessed 2026-10-25. arXiv metadata from `export.arxiv.org/api`.

1. S. Kumar, A. Girdhar, R. Patil, D. Tripathi. "MCP Guardian: A Security-First Layer for
   Safeguarding MCP-Based AI System." arXiv:2504.12757, 2025.
   <https://arxiv.org/abs/2504.12757>. An eight-author version is listed at
   doi:10.5121/csit.2025.150908 (CS & IT, vol. 15).
2. Z. Zhan, A. Al Sadi, K. Li, H. Haddadi. "AegisMCP: Online Graph Intrusion Detection for
   Tool-Augmented LLMs on Edge Devices." arXiv:2510.19462, 2025. <https://arxiv.org/abs/2510.19462>
3. H. Dang. "Enforcing Benign Trajectories: A Behavioral Firewall for Structured-Workflow AI
   Agents." arXiv:2604.26274, 2026. <https://arxiv.org/abs/2604.26274>
4. S. Zavrak. "Content-Aware Attack Detection in LLM Agent Tool-Call Traffic: An Empirical Study
   of Features, Architectures, and Evaluation Protocols." arXiv:2605.11053, 2026.
   <https://arxiv.org/abs/2605.11053>
5. C. Li, P. Hu, J. Xu, B. Ozbas, O. Liu, C. Van, M. Li, W. Zhou, M. Alizadeh, P. Zhang,
   K. Sriramadhesikan, M. Zhang. "ADR: An Agentic Detection System for Enterprise Agentic AI
   Security." MLSys 2026 (Industry Track); arXiv:2605.17380. <https://arxiv.org/abs/2605.17380>
6. A. Mehta, N. Selvanayagam, C. Lam, H. Li, P.-N. Nguyen, R. Lee, O. McGoffin, M. Luong,
   A. Collé, J. Johnson, D. Williams-King, L. Le. "FragBench: Cross-Session Attacks Hidden in
   Benign-Looking Fragments." arXiv:2605.11029, 2026. <https://arxiv.org/abs/2605.11029>; data
   <https://huggingface.co/datasets/LidaSafety/fragbench>
7. O. Narayan, R. Jyoti, R. Singh. "ChainWatch: A Kill Chain-Aligned Sequential Detection
   Framework for Multi-Step Attacks in MCP-Based AI Agent Systems." arXiv:2607.19432, 2026.
   <https://arxiv.org/abs/2607.19432>
8. D. Son. "Governed MCP: Kernel-Level Tool Governance for AI Agents via Logit-Based Safety
   Primitives." arXiv:2604.16870, 2026. <https://arxiv.org/abs/2604.16870>
9. S. Wang, S. Zhu, R. Li. "Runtime Policy Enforcement for MCP-Based LLM Agents." *Electronics*
   15(13):2829, MDPI, 2026. <https://www.mdpi.com/2079-9292/15/13/2829> (DOI not checked)
10. A. Zhang, X. Lee, Z. Zhuang, B. Peng. "Runtime Authorization Consistency Checking for
    MCP-based Agentic Workflows." arXiv:2609.23498, 2026. <https://arxiv.org/abs/2609.23498>
11. T. Liu. "From Tool Connection to Execution Control: Benchmarking Security Invariants in
    MCP-Style Agent Runtimes." arXiv:2606.29073, 2026. <https://arxiv.org/abs/2606.29073>
12. Anonymous. "CrossMCP-Bench: Authorization-Conditioned Evaluation of Runtime Security Guards
    for Tool-Calling Agents." Dataset card, 2026. <https://huggingface.co/datasets/MLZoo/CrossMCP-Bench>
    (venue claim **UNVERIFIED**)
13. W. Xing, Z. Qi, Y. Qin, Y. Li, C. Chang, J. Yu, C. Lin, Z. Xie, M. Han. "MCP-Guard: A
    Multi-Stage Defense-in-Depth Framework for Securing Model Context Protocol in Agentic AI."
    arXiv:2508.10991, 2025. <https://arxiv.org/abs/2508.10991>
14. P. He, Y. Xie, Y. Li, S. Ji. "Hybrid Analysis for Secure MCP Tool Use in LLM Agents."
    arXiv:2607.25297, 2026. <https://arxiv.org/abs/2607.25297>
15. Z. Wang, H. Du, G. Shi, J. Zhang, H. Cheng, Y. Yao, K. Guo, X.-Y. Li. "MindGuard: Intrinsic
    Decision Inspection for Securing LLM Agents Against Metadata Poisoning." arXiv:2508.20412,
    2025. <https://arxiv.org/abs/2508.20412>
16. Z. Zhou, Y. Zhang, H. Cai, M. Aloqaily, O. Bouachir, L. Pang, P. Mehrotra, K. Wang, Q. Wen.
    "MCPShield: A Security Cognition Layer for Adaptive Trust Calibration in Model Context
    Protocol Agents." arXiv:2602.14281, 2026. <https://arxiv.org/abs/2602.14281>
17. M. Rostamzadeh, S. Narula, M. Ghasemigol, D. Takabi. "TrustShiftProbe: Characterizing,
    Benchmarking, and Defending Staged Trust Attacks on MCP Servers." arXiv:2608.23763, 2026.
    <https://arxiv.org/abs/2608.23763>
18. Y. Huang, Z. Zhao, B. Chen, S. Wu, Z. Zhou, Y. Cao, X. Hu, X. Peng. "From Component
    Manipulation to System Compromise: Understanding and Detecting Malicious MCP Servers."
    arXiv:2604.01905, 2026. <https://arxiv.org/abs/2604.01905>
19. J. Fu, Y. Zhang, Y. Wang. "Can LLM Infer Risk Information From MCP Server System Logs?"
    arXiv:2511.05867, 2025. <https://arxiv.org/abs/2511.05867>
20. H. Shi, H. Yao, S. Shao, S. Jiao, Z. Peng, Z. Qin, C. Wang. "Quantifying Conversation Drift
    in MCP via Latent Polytope." arXiv:2508.06418, 2025. <https://arxiv.org/abs/2508.06418>
21. Z. Tan, R. Hao, J. Singer, Y. Tang, C. Anagnostopoulos. "MCP-SandboxScan: WASM-based Secure
    Execution and Runtime Analysis for MCP Tools." arXiv:2601.01241, 2026.
    <https://arxiv.org/abs/2601.01241>
22. S. Yamasaki, T. Toda, T. Mori. "Detecting Malicious MCP Servers by Correlating LLM-Agent
    Tool-Calling Logs with OS Audit Logs." IEICE Tech. Rep. 125(381), ICSS2025-139, pp. 402–409,
    2026. <https://ken.ieice.org/ken/paper/20260304gcsW/eng/>
23. C. Bühler, M. Biagiola, L. Di Grazia, G. Salvaneschi. "AgentBound: Securing Execution
    Boundaries of AI Agents." FSE 2026, doi:10.1145/3808103; arXiv:2510.21236.
24. Y. Yang, C. Gao, D. Wu, Y. Chen, Y. Li, S. Wang. "MCPSecBench: A Systematic Security
    Benchmark and Playground for Testing Model Context Protocols." arXiv:2508.13220, 2025.
    <https://arxiv.org/abs/2508.13220>
25. D. Zhang, Z. Li, X. Luo, X. Liu, P. Li, W. Xu. "MCP Security Bench (MSB): Benchmarking
    Attacks Against Model Context Protocol in LLM Agents." ICLR 2026 (per arXiv comment);
    arXiv:2510.15994. <https://arxiv.org/abs/2510.15994>
26. X. Zong, Z. Shen, L. Wang, Y. Lan, C. Yang. "MCP-SafetyBench: A Benchmark for Safety
    Evaluation of Large Language Models with Real-World MCP Servers." arXiv:2512.15163, 2025.
    <https://arxiv.org/abs/2512.15163>
27. Z. Wang, Y. Gao, Y. Wang, S. Liu, H. Sun, H. Cheng, G. Shi, H. Du, X. Li. "MCPTox: A
    Benchmark for Tool Poisoning Attack on Real-World MCP Servers." doi:10.1609/aaai.v40i42.40895
    (per arXiv); arXiv:2508.14925. <https://arxiv.org/abs/2508.14925>
28. H. Jing, H. Li, W. Hu, Q. Hu, X. Heli, T. Chu, P. Hu, Y. Song. "MCIP: Protecting MCP Safety
    via Model Contextual Integrity Protocol." EMNLP 2025, pp. 1177–1194,
    doi:10.18653/v1/2025.emnlp-main.62. <https://aclanthology.org/2025.emnlp-main.62/>
29. Y. Fu, X. Yuan, D. Wang. "RAS-Eval: A Comprehensive Benchmark for Security Evaluation of LLM
    Agents in Real-World Environments." arXiv:2506.15253, 2025. <https://arxiv.org/abs/2506.15253>
30. H. Li, T. Sun, Y. Wang, Q. Zhang. "MCPHunt: An Evaluation Framework for Cross-Boundary Data
    Propagation in Multi-Server MCP Agents." arXiv:2604.27819, 2026.
    <https://arxiv.org/abs/2604.27819>; data
    <https://huggingface.co/datasets/lihaonan0716/mcphunt-agent-traces>
31. Y. Zheng, Z. Chen, H. Li, B. Li. "GatewayBench: Unified Capability and Security Evaluation
    Platform for MCP Gateways." arXiv:2610.23449, 2026. <https://arxiv.org/abs/2610.23449>
32. `cx-cmu/agent_trajectories` (Hugging Face dataset card, `mcpbench` split).
    <https://huggingface.co/datasets/cx-cmu/agent_trajectories>
33. R. M. Ahmed, S. Abbas. "Labels Are Not Endpoints: Treatment Leakage and Construct Validity in
    MCP Agent Security Evaluation." arXiv:2608.12880, 2026. <https://arxiv.org/abs/2608.12880>
34. X. Hou, Y. Zhao, S. Wang, H. Wang. "Model Context Protocol (MCP): Landscape, Security
    Threats, and Future Research Directions." arXiv:2503.23278, 2025.
    <https://arxiv.org/abs/2503.23278>
35. H. Errico, J. Ngiam, S. Sojan. "Securing the Model Context Protocol (MCP): Risks, Controls,
    and Governance." arXiv:2511.20920, 2025. <https://arxiv.org/abs/2511.20920> (§III-D in the
    HTML version)
36. Y. T. Shen, K. Toyoda, A. Leung. "MCP-38: A Comprehensive Threat Taxonomy for Model Context
    Protocol Systems (v1.0)." arXiv:2603.18063, 2026. <https://arxiv.org/abs/2603.18063>
37. M. Rostamzadeh, S. Narula, N. Birhan, M. Ghasemigol, D. Takabi. "MCP-DPT: A
    Defense-Placement Taxonomy and Coverage Analysis for Model Context Protocol Security."
    arXiv:2604.07551, 2026. <https://arxiv.org/abs/2604.07551>
38. B. Radosevich, J. Halloran. "MCP Safety Audit: LLMs with the Model Context Protocol Allow
    Major Security Exploits." arXiv:2504.03767, 2025. <https://arxiv.org/abs/2504.03767>
39. H. Song, Y. Shen, W. Luo, L. Guo, T. Chen, J. Wang, B. Li, X. Zhang, J. Chen. "Beyond the
    Protocol: Unveiling Attack Vectors in the Model Context Protocol (MCP) Ecosystem."
    arXiv:2506.02040, 2025. <https://arxiv.org/abs/2506.02040>
40. W. Zhao, J. Liu, B. Ruan, S. Li, Z. Liang. "When MCP Servers Attack: Taxonomy, Feasibility,
    and Mitigation." arXiv:2509.24272, 2025. <https://arxiv.org/abs/2509.24272>
41. S. Zhao, Q. Hou, Z. Zhan, Y. Wang, Y. Xie, Y. Guo, L. Chen, S. Li, Z. Xue. "Parasites in
    the Toolchain: A Large-Scale Analysis of Attacks on the MCP Ecosystem." IEEE S&P 2026 (per
    arXiv comment); arXiv:2509.06572. <https://arxiv.org/abs/2509.06572>
42. N. Stone. "What GreyNoise Learned from Deploying MCP Honeypots." GreyNoise blog, 2025-11-05.
    <https://www.greynoise.io/blog/deploying-mcp-honeypots>
43. brian-mitchell-sec. "Does anyone come scanning? An internet-facing MCP honeypot, A/B by
    discoverability." FINDINGS.md, 2026.
    <https://github.com/brian-mitchell-sec/workspace-tools-mcp/blob/main/FINDINGS.md>
44. kosiorkosa47. honeymcp (README). <https://github.com/kosiorkosa47/honeymcp>
45. al-ice.ai Editorial. "Kai Security AI: Honeypot MCP server logs AI agent probing," 2026-02-23
    (secondary summary; primary post **UNVERIFIED**).
    <https://al-ice.ai/posts/2026/02/kai-honeypot-mcp-server-agent-probing/>
46. R. Sharif. "Agent Event Behaviour Analysis (AEBA)." Internet-Draft draft-sharif-aeba-00,
    Independent Submission, 2026-04-15. <https://datatracker.ietf.org/doc/html/draft-sharif-aeba-00>
47. Exabeam. "Agent Behavior Analytics" (product page and white paper).
    <https://www.exabeam.com/capabilities/agent-behavior-analytics/>
48. observability-mcp. "Inspect: observe, learn, and enforce agent behavior" (documentation).
    <https://thotischner.github.io/observability-mcp/inspect/>
49. MCPKernel. "Behavioral Fingerprinting" (documentation).
    <https://piyushptiwari1.github.io/mcpkernel/trust/behavioral/>
50. jaydenaung. agentsentinel (README). <https://github.com/jaydenaung/agentsentinel>
51. OpenTelemetry. "Semantic conventions for MCP" (GenAI repository, status Development).
    <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/mcp.md>
52. Model Context Protocol specification 2025-06-18, "Lifecycle."
    <https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle>
53. Model Context Protocol specification 2025-06-18, "Authorization."
    <https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization>
54. Model Context Protocol specification 2026-07-28, "Key Changes."
    <https://modelcontextprotocol.io/specification/2026-07-28/changelog>
