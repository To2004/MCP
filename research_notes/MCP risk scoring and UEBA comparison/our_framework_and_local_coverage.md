# Our MCP Risk-Scoring Framework: Feature Profile and Local Literature Coverage

These are local-only research notes, built from the repository at `/home/ovadyat/MCP` on 2026-11-04 with no web research. Every claim is tied to a local file. Links point to absolute local paths. "Current" means one of two things, and the notes say which each time: what the **code and gateway run today**, or what the **latest design decision** is (author decisions recorded in the design knowledge base and project memory, some not yet in code). The repo holds many design generations that contradict each other. Mapping them is a large part of these notes.

## 1. Threat direction and scope: what is protected, who is the threat, what is out of scope?

### Takeaway
The MCP server, and the organisational assets reachable through its tools, is the protected asset. The calling AI agent is the threat source. The paper frames the threat as **misuse of legitimate MCP capabilities**, whatever the intent (error, excessive delegation, compromise or malice). Malicious servers, tool poisoning, auth bypass, implementation CVEs, policy manipulation and server-to-agent attacks are all out of scope. The latest dynamic-layer framing goes further: it assumes almost all traffic is ordinary and the risky calls are "gray", not attacks.

### Cited Findings
- "The server is always the victim; the agent is always the threat." All attacks flow client → server. Malicious-server → agent (tool poisoning) is out of scope, except when a poisoned agent then becomes a threat *to the server* — [docs/project/overview.md](/home/ovadyat/MCP/docs/project/overview.md)
- The project's rules forbid reversing the direction and require MCP-only results for MCP questions — [CLAUDE.md](/home/ovadyat/MCP/CLAUDE.md)
- The paper's threat model assumes the MCP server and its advertised tools are benign. The protected environment is "the organizational assets and services reachable through these tools". The focus is "misuse of legitimate MCP capabilities … regardless of whether the operation originates from benign error, excessive delegation, compromised behavior, or malicious intent". Explicitly out of scope: "malicious MCP servers, tool poisoning, authentication bypass, implementation vulnerabilities, manipulation of organizational policies, and server-to-agent attacks" — [paper_v5/main.tex §3 Threat Model](/home/ovadyat/MCP/paper_v5/main.tex)
- The paper deliberately separates assessment from enforcement: "the framework estimates the risk … the organization determines what action, if any, should follow" — [paper_v5/main.tex §4.4 Risk Output](/home/ovadyat/MCP/paper_v5/main.tex)
- Out of scope by construction: OWASP API1 (BOLA). Ownership checks need ownership context and several identities, which the framework does not have. The framework positions itself as an **OWASP API4:2023 Unrestricted Resource Consumption** signal (breadth) — [docs/project/external-benchmarks-and-positioning.md](/home/ovadyat/MCP/docs/project/external-benchmarks-and-positioning.md)
- A server-side defence "can only use what arrives at the server". It never sees the agent's prompt, reasoning or retrieved content, so taint tracking, provenance graphs and intent parsing are unavailable "by construction" — [docs/project/external-benchmarks-and-positioning.md](/home/ovadyat/MCP/docs/project/external-benchmarks-and-positioning.md)
- Dynamic-layer evaluation framing (author decision, repeated 2026-10-20 and 2026-10-28): "we are not working with attacker all calls in theory should be normal". The risky calls are gray: bulk export, odd hours, first look at a sensitive asset. Do not add adaptive-attacker, mimicry, poisoning or evasion framing — [memory: dynamic-layer-eval-framing.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/dynamic-layer-eval-framing.md)
- Dynamic test scenarios cover only behaviour that is unusual for this agent id compared with its own past. Out of scope for them: anything the static layer prices (tool impact, asset sensitivity, toxic flows), failed, denied or retried calls, and protocol checks — [memory: dynamic-scenarios-scope.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/dynamic-scenarios-scope.md)
- Identity assumption: the operator issues the agent id and a client cannot choose or forge it. **Sybil identities are out of scope** — [knowledge_base/context-brief-2026-10-29.md §3](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md)
- Claims the design record says the paper should *not* make: that per-entity rarity is new, that rank-based p-values are new, or "that M stops an attacker who mimics the agent" — [context-brief-2026-10-29.md §5.9](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md)

### Inferences
- The threat framing moved over time. Early docs speak of "malicious or compromised AI agents" and attacks ([overview.md](/home/ovadyat/MCP/docs/project/overview.md)). The paper now speaks of intent-agnostic misuse, and the dynamic layer is now framed around gray, non-malicious deviation. A comparison report should quote the paper's "misuse of legitimate capabilities" definition as the current one.
- Two in-scope gaps the repo admits are worth noting because UEBA systems cover them: no peer-group comparison (no directory available), and no cross-call accumulation in the current behaviour design (Section 2).

### Gaps
- The overview says the framework "is **not anomaly detection**" ([overview.md](/home/ovadyat/MCP/docs/project/overview.md)). The behaviour multiplier is, in effect, per-agent anomaly scoring against the agent's own history. The repo does not reconcile these two statements. The overview predates the behaviour layer and also says "Early development — package skeleton", so it is stale.

## 2. What exactly is scored, when, on what scale and with what formula, and which generation is current?

### Takeaway
There are three scoring objects. (a) A **design-time static cell** per (tool, asset): sensitivity × blast radius × impact, each 1-5, product 1-125, four bands. (b) A **per-call static input level** per tool input (v13, 1-5, a design-time lookup table applied at runtime). (c) A **runtime adjustment** with two parallel mechanisms: a per-deployment argument/tool-frequency factor `B × L`, and a per-agent **behaviour multiplier M**. In code, M is still design v4 (×0.7-5). The latest author decisions replace it with a rank-on-calls formula on four dimensions, which is not yet in the engine. The paper draft in `paper_v5/main.tex` describes yet another runtime formula (`L = D·A·N`, about [1, 8]), and the repo flags this as a deliberate divergence from the implementation.

### Cited Findings

#### Feature profile (for line-by-line comparison)

| Axis | Our framework (current code / latest design) | Source |
|---|---|---|
| Protected asset | MCP server and the org assets reachable through its tools | [main.tex §3](/home/ovadyat/MCP/paper_v5/main.tex) |
| Threat source | Calling AI agent (misuse of legitimate capabilities, any intent) | [main.tex §3](/home/ovadyat/MCP/paper_v5/main.tex) |
| Vantage point | Server-side gateway at the MCP JSON-RPC layer; sees only what reaches the server | [external-benchmarks-and-positioning.md](/home/ovadyat/MCP/docs/project/external-benchmarks-and-positioning.md) |
| Units scored | (tool, asset) cell at design time; tool input (1-5 rule) at design time; each `tools/call` at runtime; per-agent behaviour vs own history | [GROUND-TRUTH.md §1](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md), [v13 README](/home/ovadyat/MCP/reports/experiments/v13/README.md), [gateway/framework.py](/home/ovadyat/MCP/src/mcp_security/gateway/framework.py) |
| Not scored | Server implementation; sessions (MCP 2026-07-28 has none); whole runs; response content; peer groups | [context-brief §3, §5.2](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md), [dynamic-layer-blind-spots.md](/home/ovadyat/MCP/docs/project/dynamic-layer-blind-spots.md) |
| Timing | Static: once per server catalog (design time). Runtime: inline, **before forwarding**, per call | [gateway/proxy.py](/home/ovadyat/MCP/src/mcp_security/gateway/proxy.py) |
| Output | Graded number plus a reason string; static bands low <17, medium 17-49, high 50-99, critical ≥100 on 1-125; behaviour `dynamic_risk` = static level (1-5) × M, range 0.7-25 | [main.tex §4.4](/home/ovadyat/MCP/paper_v5/main.tex), [behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md) |
| Decision | None: observe-only, never blocks; enforcement left to the organisation (target modes observe / shadow / enforce not built) | [gateway-architecture.md](/home/ovadyat/MCP/docs/project/gateway-architecture.md) |
| Static formula | `sens × blast × impact` (1-125) plus deterministic assembly and banding | [GROUND-TRUTH.md §1](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md) |
| Runtime formula (code) | `R = min(125, cell × B × L)`, B ∈ [0.70, 1.30], L ∈ [0.85, 1.30]; and separately `dynamic_risk = cell^(1/3) × M`, M ∈ [0.7, 5] (v4) | [dynamic-layer-explained.md](/home/ovadyat/MCP/docs/project/dynamic-layer-explained.md), [framework.py L283-295](/home/ovadyat/MCP/src/mcp_security/gateway/framework.py) |
| Runtime formula (latest design) | `Risk = Risk_static × M`, M = ((n+1)/(2k+1))^γ, γ = ln5/ln(max(n,1000)+1); 4 behaviour dims on calls (2026-11-01) | [memory: dynamic-layer-v5-decisions.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/dynamic-layer-v5-decisions.md) |
| Baseline | Per agent id, own last 90 days (behaviour); per deployment/connection (B, L) | [behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md), [gate_runtime.py](/home/ovadyat/MCP/scripts/dynamic_design/gate_runtime.py) |
| Identity | Agent id only (latest decision; no user id, sign-in or IP); gateway can derive `gateway.agent_id` from OAuth | [memory: identity-agent-not-user.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/identity-agent-not-user.md), [gateway/README.md](/home/ovadyat/MCP/src/mcp_security/gateway/README.md) |
| Model on call path | None; all runtime logic is closed-form or lookup | [v8 README](/home/ovadyat/MCP/reports/experiments/v8/README.md) |
| Training labels | None (label-free); thresholds learned from ordinary traffic | [behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md) |
| Peer groups | No; other agents can only *lower* a score (org discount, v4) | [DIMENSION_FORMULAS.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md) |
| Aggregation over time | None per agent-day or session in the current designs (max/rank per call only) | [03-ueba-insider-threat-and-datasets.md §2](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/03-ueba-insider-threat-and-datasets.md) |
| Tamper evidence | Per-file SHA-256 hash chain in `gateway-log/3` | [gateway/log_file.py](/home/ovadyat/MCP/src/mcp_security/gateway/log_file.py) |

#### Static layer: the generations and which is current
- **Core static formula (current in the paper and the code):** `score = asset_sensitivity × blast_radius × tool_impact`, range 1..125. Then a deterministic assembly (bulk twins, alias twins, gated blast floor) and `band_label()` → {low, medium, high, critical}. Bands encode security floors, for example "any irreversible operation is at least medium". The v5r mode removes the blast roof — [paper_v5/GROUND-TRUTH.md §1](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- The deterministic impact ladder has five tiers: 1 none (ping, health), 2 metadata, 3 content read or limited write (PATCH-like, CVSS VI:L), 4 ordinary write (PUT-like, CVSS VI:H), 5 removal or execution (delete, execute code, move money). Its vocabulary is 281 patterns plus 119 ambiguous words, 10 generic read verbs and 9 parameter detectors. Breadth is deliberately *not* on the ladder; blast radius scores coverage — [GROUND-TRUTH.md §1](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- **v5 / v5r (current static scan for the paper):** sensitivity is derived from the organisation's classification policy. The impact ladder runs first, with an LLM fallback. v5r adds rewritten prompts and an operation-type impact ladder. The v5r `nacombo` arm "is the baseline the paper cites" — [reports/experiments/v9/README.md](/home/ovadyat/MCP/reports/experiments/v9/README.md), [CLAUDE.md command table](/home/ovadyat/MCP/CLAUDE.md)
- **v6 CIA loss vectors (offline variant, not the main path):** `score_f = S × B_f × I_f` for each objective f ∈ {C, I, A} the call can violate, then `score = max(existing score, score_C, score_I, score_A)`. Invariant: never below the existing cell. Sensitivity is not split per objective. It runs offline with no model. An earlier "CIA as a facet selector" re-pricing is marked superseded — [scripts/cia_risk_rescore.py docstring](/home/ovadyat/MCP/scripts/cia_risk_rescore.py), [CLAUDE.md](/home/ovadyat/MCP/CLAUDE.md)
- **v7 (experiment):** policies written in the shape of three security frameworks (ISO, NIST, CIS) for four orgs (fs_corp_filesystem, github_helios / NERC CIP, slack_vireo / ICH-GCP, calendar_aurora / aviation), compared against `nacombo` — [reports/experiments/v7/README.md](/home/ovadyat/MCP/reports/experiments/v7/README.md). The v7 ISO matrices are the static input for the dynamic-layer results — [reports/experiments/dynamic_layer/RESULTS.md](/home/ovadyat/MCP/reports/experiments/dynamic_layer/RESULTS.md)
- **v8 binding (current runtime component):** resolves at runtime which asset a call touches, with "no model may run" and "nothing may be configured per server" (dictionary lookup, regex, IDF-weighted token overlap). Severity is "the worst severity among every asset it could be touching", so recall 1.0 makes under-scoring impossible — [reports/experiments/v8/README.md](/home/ovadyat/MCP/reports/experiments/v8/README.md). The gateway uses it as `binding.scoring.MatrixScorer` — [gateway/framework.py](/home/ovadyat/MCP/src/mcp_security/gateway/framework.py)
- **v10 / v11 / v12 (superseded or deprioritized):** v10 input typing is "deprioritized"; v11's stacked-feature ledger was "too complicated to explain"; v12's two stages are "Superseded by v13" — [v10](/home/ovadyat/MCP/reports/experiments/v10/README.md), [v11](/home/ovadyat/MCP/reports/experiments/v11/README.md), [v12 README](/home/ovadyat/MCP/reports/experiments/v12/README.md)
- **v13 per-input levels (current; run21 frozen):** one prompt per tool, run at design time, asks per input for "a rule that turns the value into a level, reaching every level from 1 to 5, or answer none". The rules form a lookup table, and "no model runs on a call". Rule kinds: `ranges`, `register`, `keywords`, `values`, `domain`. Level 3 is the neutral "ordinary call" — [v13 README](/home/ovadyat/MCP/reports/experiments/v13/README.md), [v12 README](/home/ovadyat/MCP/reports/experiments/v12/README.md). In the gateway, the input level is "reported beside the risk (how the two combine is not decided)" — [gateway/framework.py](/home/ovadyat/MCP/src/mcp_security/gateway/framework.py)
- **Conflicting static combination formulas (open decision):** the newer USENIX-targeted design record states a *weighted sum*: `Risk_static = 0.3·ToolImpact + 0.3·AssetSensitivity + 0.3·BlastRadius + 0.1·ParameterRisk`, with ParameterRisk = max over risk-relevant inputs (0 if none). The gateway instead computes the cube root of the product (geometric mean) and only logs ParameterRisk. Listed as open decision #2 — [context-brief-2026-10-29.md §4.1-4.2, §10](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md). Confirmed in code: `static_level = cell.severity ** (1 / 3)` and `dynamic_risk = static_level * verdict.multiplier` — [gateway/framework.py L283-295](/home/ovadyat/MCP/src/mcp_security/gateway/framework.py). The AAMAS draft `main.tex` uses the 1-125 product — [GROUND-TRUTH.md §1](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)

#### Runtime layer, part 1: per-deployment argument and frequency factors (three generations)
- **Gen 1 (superseded):** a four-signal layer (embedding likelihood, behavioural-baseline and session-sequence band signals, an optional LLM judge). It was "dropped … and no longer claimed in the paper" — [GROUND-TRUTH.md §2, §4](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- **Gen 2, "cell × likelihood × escalation, floored" (measured; the GROUND-TRUTH paper spec):** `rho(c) = min(125, max(cell(t,r) × lik(c) × esc(c), floor(t,r)))`. Here lik ∈ [0.10, 1.00] is surprisal of the tool's share of deployment traffic: `p = (k_t + 30·prior[t])/(n + 30)`, `lik = 0.10 + 0.90·clamp(log2(1/p)/log2(n+V), 0, 1)`. esc ∈ {0.9, 1.0, 1.3} is a Tukey bin over argument history (≥20 observations). floor ∈ {0, 17, 50, 100} is the pre-change band's lower bound, so the runtime "never demotes out of a band". Likelihood is keyed (deployment, tool), not per agent, because "no agent in the corpora spans more than a single day, median 32 calls" — [GROUND-TRUTH.md §2](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md); run via `scripts/dynamic_design/rank_eval.py` — [CLAUDE.md](/home/ovadyat/MCP/CLAUDE.md)
- **dynamic_v2, B × L (in the gateway today):** `R(c) = min(125, cell(tool, asset) × B(c) × L(c))`. B ∈ [0.70, 1.30] grades argument quantities against their own history: escalate above p90 to B_MAX at 2.5 × p90; discount below Q1; weighted by design-time `breadth` (5:1.00, 4:0.75, 3:0.50, 2:0.25, 1:0.0); combined by max. L ∈ [0.85, 1.30] is tool rarity against the median tool, shrunk by confidence = total/(total + 20 × tools_exposed). Constants: MIN_HISTORY 20, MAX_HISTORY 4000, L_ALPHA 30. "B never looks at how often a tool is called and L never looks at argument values" — [docs/project/dynamic-layer-explained.md](/home/ovadyat/MCP/docs/project/dynamic-layer-explained.md). The gateway runs it as "the runtime factor B × L: gate_runtime.GateScorer" — [gateway/framework.py](/home/ovadyat/MCP/src/mcp_security/gateway/framework.py)
- B × L carries "No state across calls. No session, no clock, no rate" and "No caller identity. The score is per deployment". Per-identity conditioning "collapsed misuse AUC from 0.53 to 0.30" — [dynamic-layer-explained.md §6](/home/ovadyat/MCP/docs/project/dynamic-layer-explained.md)
- **The AAMAS paper text diverges from both.** `main.tex` §4.3 defines `L(c) = D(c)·A(c)·N(c)` (Baseline Deviation, Access Anomaly, Novelty and Exposure), each about [1, 2], so L is about [1, 8], with `R_dynamic = R_static × L`, "bounded below by 1" — [paper_v5/main.tex §4.3](/home/ovadyat/MCP/paper_v5/main.tex). The paper README calls this "One deliberate divergence, stated in the text" — [paper_v5/README.md](/home/ovadyat/MCP/paper_v5/README.md)

#### Runtime layer, part 2: the per-agent behaviour multiplier M
- **Design v4 (the engine and gateway default today):** "how strange is this call, for this agent, compared with his own last 90 days?" It gives a multiplier between ×0.7 and ×5 and "never reads a tool's arguments". `dynamic_risk` = static level (1-5) × multiplier, range 0.7-25 — [src/mcp_security/behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md). "design v4 by default, v1-v3 with `design` in the route's behaviour policy" — [gateway/framework.py](/home/ovadyat/MCP/src/mcp_security/gateway/framework.py)
  - v4 has 15 dimensions in three groups. **Typical Cadence:** call rate, write rate, breadth, repetition, session duration, hour of day. **Typical Footprint:** tool, asset, network (/16), client. **Red Flags:** burst, sweep, oversized request, unsafe sequence, missing handshake — [DIMENSION_FORMULAS.md (v4)](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md)
  - Excess score for counts: `s = (v+u)/(v+u+2(avg+u))`. Rarity score: `e = (calls on things at most this common + 1)/(active days + 1)`, `s = c/(1+2e)`, c = 0.9 for tools. A raised Red Flag scores 0.9 (×3.6); protocol skip scores 0.7 (×1.9). "The strangest dimension decides": `M = 5^(2S−1)` when S ≥ 0.5, `0.7^(1−2S)` below. For the first 5 tool calls M = 1 (warm-up) — [behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md)
  - Org discount: something new for him that 3 or more other agents also started this week counts at most 0.5. First-access floor: a never-touched asset of sensitivity 5 scores at least 0.9, of sensitivity 4 at least 0.8. A habit discount also applies — [DIMENSION_FORMULAS.md Names table](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md)
  - The learned **behaviour policy**: "Each limit is set so the rule fires on at most 0.5% of ordinary agent-days. A tool requires another when that one came earlier in 99.5% of its sessions (seen in at least 50 sessions)." CLI: `python -m mcp_security.behaviour.policy --log … --days 30` — [behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md)
- **Design v5 (interfaces only in code):** it adds Read volume as a 16th dimension. "So far it has its interfaces only"; with every v5 switch off it equals v4 — [behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md). Decision D2 (M ∈ [1, 5]) was later superseded — [memory: dynamic-layer-v5-decisions.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/dynamic-layer-v5-decisions.md)
- **2026-10-28 "one simple formula" (superseded, kept selectable):** `M = ((A+1)/(2D+1))^γ`, `γ = ln5/ln(H+1)`, 8 general dimensions, H = last 90 active days; no Red Flags or policy — [memory: dynamic-layer-v5-decisions.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/dynamic-layer-v5-decisions.md)
- **2026-10-29 design "J" (prototype, "not yet in the engine"):** six dimensions (Tool, Asset, Tool on asset, Calls this hour, Breadth, Time of day), counting **calls**. `M = ((n+1)/(2k+1))^γ`, `γ = ln5/ln(max(n,1000)+1)`; n = the agent's past calls in a 90-day window; k = past calls at least as unusual. Equivalently `share = (k+½)/(n+1)`, `M = (½/share)^γ`, a mid-p (Lancaster 1961) rank / conformal p-value. M is about 0.87 for the deepest habit (0.78 lower bound in the report) and reaches 5 for "never seen". Settled rules: only executed calls enter history; Time of day ±1 h in the route's time zone; amounts 1-3 share one bin; **blocking uses max(1, M)**; every score shows its reason. Guarantee: under exchangeability, P(×5) ≤ 1/(n+1) — [context-brief-2026-10-29.md §5](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md), [dynamic-score-report.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/dynamic-score-report.md)
- **2026-11-01 (the latest author decision, design stage only):** "the dynamic score has only four behaviour dimensions, all counted on **calls**: Calls this hour, Time of day, Tool rarity and Asset rarity. Breadth, Tool on asset and Session length are out." Policy rules come back for **burst** (calls per minute) and **suspicious tool order** (a required step is missing). A smooth-k proposal "J4s" is "not yet confirmed": Sidak combination `share = 1 − (1 − s)^4`, `M = (½/share)^γ`. Weekend handling: calls on the other kind of day count 1/16. Result: 4 of 9 Pinecrest scenarios pass. Still failing: S2, S6, S7 (because calls are counted) and S9, S10 (no cold start) — [memory: dynamic-layer-v5-decisions.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/dynamic-layer-v5-decisions.md)
- Open items in the latest design: unit of counting (calls now, days planned, "better on every test"); static combination (sum vs geometric mean); Read volume; daily accumulation and a cross-agent discount; quiet agents "cannot reach ×5" — [context-brief §10](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md)

### Inferences
- For a comparison table, report **two columns** for our framework: "as built" (static 1-125 cell + v8 binding + v13 input levels + B × L + behaviour v4 ×0.7-5, observe-only) and "as designed for the next paper" (`Risk_static × M`, M a per-agent rank p-value on four call-counted dimensions plus two policy rules). Citing a single formula would be wrong for one of the two.
- The repo's own measurements (Section 6) argue against the per-deployment frequency term in both Gen 2 and dynamic_v2. That probably explains why the design focus moved to the per-agent behaviour multiplier.
- The behaviour multiplier is UEBA-style per-entity rarity scoring, applied per call before execution and multiplied onto a static capability score. The repo itself concedes the UEBA idea and claims only the mechanism, the evaluation and the MCP-specific placement.

### Gaps
- No single doc states "this is the current end-to-end formula". The latest decisions (2026-11-01) live only in project memory and a probe script (`probes/m_formula_pinecrest.py`), not in a design doc or the engine.
- How the v13 input level combines with the cell is "not decided" in code. The weighted-sum design gives ParameterRisk a 0.1 weight, but no doc shows that this is implemented.

## 3. What inputs does scoring use?

### Takeaway
At design time: the captured tool catalog (`tools/list`) and the organisation's classification policy with its asset register (optionally written in ISO, NIST or CIS shape). An LLM turns these into per-tool impact, per-asset sensitivity, per-(tool, asset) blast radius, per-input breadth/kind labels, and per-input 1-5 rules. At runtime: the call's tool name and arguments (for binding, the input rules and B), deployment-level tool counts (L), and the agent id, timestamp, tool and resolved asset for the behaviour multiplier. The latest decision limits identity to **an agent id only**.

### Cited Findings
- Static inputs are "exactly two documents: the captured tool catalog (`tools/list`) and the organization's policy section". The per-asset sensitivity table in `server-profiles.md` is held out and used only as ground truth — [GROUND-TRUTH.md §1](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- Pipeline stages: 0 domain inference (LLM, once per server); 1 tool impact (rules first, LLM on abstention); 2 asset sensitivity (LLM classify→map against the policy); 3 blast radius (LLM, per (tool, asset)); then deterministic assembly and banding — [GROUND-TRUTH.md §1](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- Policy frameworks: v7 republishes each org's policy in ISO (A.5.9 owner, A.8.3 authorisation set), NIST (FIPS 199 axes) and CIS shapes; the scanner, catalogs, ladder and blast rubric are identical across arms — [v7 README](/home/ovadyat/MCP/reports/experiments/v7/README.md). The policy format is validated against a spec (`scripts/check_policies.py`) — [CLAUDE.md](/home/ovadyat/MCP/CLAUDE.md)
- Design-time `tool_breadth` per input: `kind` ∈ {count, magnitude, range, none} and `breadth` 1-5 ("how central is this input to the asset the call acts on") — [dynamic-layer-explained.md §2](/home/ovadyat/MCP/docs/project/dynamic-layer-explained.md)
- v13 rule tables use the policy's whole asset register (`register` rules), credential words at level 5 for text, a fixed email ladder for address inputs, and window lengths for `timeMin`/`timeMax` — [v13 README](/home/ovadyat/MCP/reports/experiments/v13/README.md)
- Binding resolves the asset from free-form arguments against the policy register, deterministically and with no per-server code. When it cannot, the call is priced at the **worst** asset the tool can reach — [context-brief §4.1](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md), [v8 README](/home/ovadyat/MCP/reports/experiments/v8/README.md)
- Behaviour inputs (latest design): "agent id, time, tool, and asset (from the binding layer)". "Argument values belong to the static score, and outcomes never change the same call's score" — [context-brief §5.1](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md). v4 in code also uses the /16 network, the client family, `initialize` presence and request size — [behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md)
- **Identity decision:** "we are not doing sign in or ip we have only agent id that we can think it is like the all org." The key is the agent id only; "If the agent id is missing, all calls share one key"; no Network or Client dimensions — [memory: identity-agent-not-user.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/identity-agent-not-user.md). By contrast, the gateway *can* derive `gateway.agent_id` "one per issuer, app and user" from an OAuth token, and without OAuth every caller is `anonymous` — [gateway/README.md](/home/ovadyat/MCP/src/mcp_security/gateway/README.md)
- History window: 90 days per agent in v4 ("90 days of memory per agent kept per day (bounded)") — [behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md). In the latest formula, n is "the agent's past calls in its history window (90 days, as in the author's deck)" — [context-brief §5.3](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md)
- MCP 2026-07-28 facts the design relies on: no `initialize` handshake, no sessions (`Mcp-Session-Id` removed); `clientInfo` is self-reported "and must not drive security decisions"; MCP has no standard agent-id field — [context-brief §3](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md), [gateway-architecture.md](/home/ovadyat/MCP/docs/project/gateway-architecture.md)

### Inferences
- Compared with UEBA products, the input set is deliberately thin: no HR or directory data (so no peer groups), no IP, ASN or geo (under the latest decision), no device or browser. The input that is distinctive to our framework is an **organisational classification policy** that drives a design-time severity prior. The repo's literature review says no prior work derives sensitivity from such a policy ([literature-review.md "Where the gap is"](/home/ovadyat/MCP/paper_v5/literature-review.md)).

### Gaps
- The v4 engine still consumes network and client, against the later identity decision. The repo does not say whether those inputs will be removed from v4 or only from the new formula.

## 4. Where is an LLM used, and where is the logic deterministic?

### Takeaway
LLMs run only at **design time**: domain inference, asset sensitivity, blast radius, impact fallback, breadth/kind classification and v13 rule writing. On the **call path everything is deterministic**: binding by lookup, regex and IDF token overlap; input rules by lookup; B × L and M in closed form. The runtime LLM judge was dropped from the scan path and the paper.

### Cited Findings
- Stages 0, 2 and 3 are LLM. Stage 1 impact is "rules first, LLM only on abstention", with rule confidence 0.35 / 0.8 / 0.95 and the model consulted when confidence < 0.5. Assembly and banding are deterministic — [GROUND-TRUTH.md §1](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- On the v5 corpus, 55/55 tools were decided by the rules with 0 LLM calls; the fallback "is covered by unit tests only on this corpus". On the v5r `nacombo` corpus the ladder decided 127 of 151 distinct tools (84%) and the model 24 (16%) — [GROUND-TRUTH.md §3, §9](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- Scanner model: `qwen2.5:32b`. The MCPHunt judge uses `gemma3:27b`, a different family. Each scan runs on one RTX 4090, about 14 minutes per server — [reports/experiments/gateway/mcphunt/README.md](/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/README.md). v13 notes "qwen2.5 32B" behaviour under prompt changes — [v13 README](/home/ovadyat/MCP/reports/experiments/v13/README.md)
- Binding: "No model may run … Every mechanism is deterministic Python — dictionary lookup, regex, IDF-weighted token overlap … cannot be steered by text an attacker places in an argument" — [v8 README](/home/ovadyat/MCP/reports/experiments/v8/README.md)
- v13: "The rules are a lookup table for the dynamic layer: no model runs on a call" — [v13 README](/home/ovadyat/MCP/reports/experiments/v13/README.md)
- The paper's §5 Implementation states a "no-model-on-the-call-path constraint" and explains "why the old LLM judge stage was removed from the scan path" — [paper_v5/README.md](/home/ovadyat/MCP/paper_v5/README.md). The LLM judge (`dynamic/judge.py`) "is wired but was not run" — [GROUND-TRUTH.md §7](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- LLM reliability problems the repo itself reports:
  - The listwise `rank` field was dropped because Kendall's τ under input reversal averaged 0.538 and went negative on large tools (−0.37, −0.47). Its replacement `breadth` agrees with itself only 62.5% of the time under reversal (`kind`: 94.7%) — [dynamic-layer-explained.md §2](/home/ovadyat/MCP/docs/project/dynamic-layer-explained.md)
  - Blast radius is "the noisy stage": 19-22% of cells moved between arms; v4 measured 23-35 cells per server of run-to-run variance — [GROUND-TRUTH.md §3](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
  - In v13, "Any prompt change moves the greedy answers by several scenarios and up to 0.1 AUC" — [v13 README](/home/ovadyat/MCP/reports/experiments/v13/README.md)

### Inferences
- This split (LLM offline to build a severity prior, closed-form online) sets the framework apart from LLM-judge runtime guards (ToolSafe, MCP-Guard's arbitrator, ADR, Governed MCP), which the repo's comparison docs already list. The price is that design-time LLM noise is frozen into the matrix.

### Gaps
- No measured end-to-end cost or latency for a full design-time scan across all servers, beyond "about 14 minutes each" for the MCPHunt servers.

## 5. Deployment: gateway design, log format, tamper evidence, observe-only versus enforce

### Takeaway
An observe-only HTTP proxy (`mcp_security.gateway.proxy`) forwards every message byte for byte and scores every `tools/call` inline before forwarding. It never blocks. It writes `gateway-log/3` JSONL per route, with OpenTelemetry MCP field names, HMAC pseudonyms and a per-file SHA-256 hash chain. It can act as an OAuth 2.1 resource server. Enforcement modes and decision rules (allow / alert / review / deny) are designed in the NIST 800-207 PEP/PDP/PIP/PAP shape but not built.

### Cited Findings
- "Observe-only MCP gateway: forward every message to an external server, record it, change nothing … every `tools/call` is scored by the whole framework (static cell, runtime factor, input level) *before* it is forwarded, and the verdict is logged; nothing is ever blocked." Unscanned tool lists are saved for a static scan. `score.py` re-scores a saved log offline — [gateway/proxy.py docstring](/home/ovadyat/MCP/src/mcp_security/gateway/proxy.py)
- Live and offline scoring match: "Same object, same order, same numbers. Every result carries the digests of the artifacts it came from" — [gateway/framework.py docstring](/home/ovadyat/MCP/src/mcp_security/gateway/framework.py)
- Hash chain: "Every line carries `gateway.prev_sha256` … editing, inserting or deleting a line in the middle breaks the chain". It cannot detect lines cut from the start or end of a file, or a whole rewrite, so copies must go to storage the gateway cannot rewrite; one process per log directory — [gateway/log_file.py docstring](/home/ovadyat/MCP/src/mcp_security/gateway/log_file.py)
- `gateway-log/3` fields: identity (`user.id` = token `sub`, `gateway.app`, `gateway.agent`, `gateway.agent_id`, `gateway.auth`, issuer, scopes, token id, `act`, self-reported `gateway.client`, `client.address`); order (`mcp.session.id` as a pseudonym, `gateway.seq`, trace ids); content (`gen_ai.tool.name`, `gateway.arg_keys`, `gateway.args_hash`, `gateway.effects`, message bytes, header mismatch); notices (`auth_failed` with reasons, `session_agent_mismatch`, `catalog_not_scanned`, …) — [gateway/README.md](/home/ovadyat/MCP/src/mcp_security/gateway/README.md), [gateway/wire_log.py docstring](/home/ovadyat/MCP/src/mcp_security/gateway/wire_log.py)
- Pseudonyms: keyed HMAC for session ids, arguments and recipients. Without a key they are plain SHA-256, "guessable for low-entropy values" — [gateway/README.md](/home/ovadyat/MCP/src/mcp_security/gateway/README.md)
- OAuth: the gateway checks the provider's JWT access tokens, serves RFC 9728 metadata, checks the RFC 8707 audience, and "The token is never sent upstream" — [gateway/README.md](/home/ovadyat/MCP/src/mcp_security/gateway/README.md), [gateway-architecture.md](/home/ovadyat/MCP/docs/project/gateway-architecture.md)
- NIST role mapping: the PEP is observe-only "No modes (observe / shadow / enforce)"; the PDP "computes the risk; nothing turns it into an outcome"; dynamic PIP state is "Lost on restart; shared by all callers"; there is no versioned policy bundle (PAP); audit is the JSONL plus hash chain, "chain not anchored off the host". Target: hard rules (input-rule level 5, unscanned tool) always win, plus score thresholds on `cell × B × L` — [docs/project/gateway-architecture.md](/home/ovadyat/MCP/docs/project/gateway-architecture.md)
- Measured capacity: ~40 µs median scoring per call, not growing with callers (to 100k) or history; ~600 calls/s per process with httpx, ~1,500 with aiohttp; 8 aiohttp processes ~9,000 calls/s with inline scoring; a separate log-reading scorer decides within ~3 ms at ~14,000 calls/s but cannot block — [gateway-architecture.md](/home/ovadyat/MCP/docs/project/gateway-architecture.md)
- Behaviour engine state survives restarts with `snapshot`/`restore` — [behaviour/README.md](/home/ovadyat/MCP/src/mcp_security/behaviour/README.md)

### Inferences
- The repo's own positioning says hash-chained logs are "common ground, not a novelty for us" (Praetor, Governed MCP and the MDPI enforcement point all hash-chain theirs) — [02-mcp-runtime-security-literature.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/02-mcp-runtime-security-literature.md). A comparison should treat tamper-evident logging as table stakes.

### Gaps
- Stages 2-3 (identity provider choice, TLS exposure, Postgres, shadow/enforce) are planned only. No enforcement-mode measurement exists.

## 6. Evaluation: datasets, metrics, headline results, blind spots and limitations

### Takeaway
Most evidence is **self-generated**. Real catalogs, synthesised policies, asset registers and invocation scenarios form "an evaluation setting, not a benchmark". The strongest result is the static scan: policy-derived sensitivity matches held-out org numbers, 50/56 exact and 100% within one tier. The dynamic results are mixed to negative. The per-deployment likelihood term hurt ranking on all three servers. On the one outside labelled dataset (MCPHunt) the whole framework did not separate risky from benign runs (AUC about 0.5). The behaviour multiplier has been tested only on simulated organisations and designer-written scenarios.

### Cited Findings
**Settings and datasets**
- Real: tool catalogs captured from live vendor MCP servers (calendar 13 tools, github 26, slack 16) and a real git corpus. Synthesized: the policies, asset registers and invocation scenarios (`make_dynamic_testbed.py`, `make_insider_testbed.py`). "Say this precisely. It is an **evaluation setting**, not a benchmark" — [GROUND-TRUTH.md §6](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- Insider testbed: legitimate insiders with mixed records and no external attackers; 2 orgs; ~100 calls per persona; sessions shuffled; "Identity therefore carries no label signal by construction" — [scripts/make_insider_testbed.py docstring](/home/ovadyat/MCP/scripts/make_insider_testbed.py)
- v5r corpus: 16 deployments over 9 catalogs, 262 tools, 221 assets, 3,615 cells, of which 1,182 scored (444 low / 458 medium / 242 high / 38 critical). Live traffic: 3,000 calls (1,000 each for github_helios, slack_vireo, calendar_aurora; 50/25/25 benign / misuse / malicious), with labels "assigned by the generator … not an independent annotation". "§9 has no oracle" — [GROUND-TRUTH.md §7, §9](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- Org-traffic corpora: role-weighted personas (e.g. GitHub ci_bot 52%, developer 26%, …, admin 1%); 1,000 live calls per server (GitHub writes executed in a scratch repo; Slack and Calendar writes recorded, not executed) plus 100,000 synthetic calls per server — [reports/experiments/dynamic_layer/v3/README.md](/home/ovadyat/MCP/reports/experiments/dynamic_layer/v3/README.md)
- MCPHunt (outside traffic): 62,337 recorded tool calls by five models over 147 tasks and eight real MCP servers, labelled risky / benign / hard negative at run level; 61,926 calls scored — [gateway/mcphunt/README.md](/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/README.md)

**Static results**
- v5 vs held-out org table: 3 servers, 56 assets, 55 tools; MAE 0.10-0.125; exact 88-90%; within one tier 100%; 50/56 exact; the six misses are all adjacent-tier — [GROUND-TRUTH.md §3](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- Oracle panel (10 raters: human, ChatGPT ×2, CVSS v3, DREAD, MAESTRO/ATFAA, NIST SP 800-30, NIST SP 800-60, OWASP AIVSS, OWASP risk rating): scanner vs consensus exact 25/71 (35%), within one band 49/71 (69%). The raters' own agreement is 50% / 78% (filesystem) and 42% / 75% (sqlite). The file does not say which scanner generation was graded — [reports/evaluation/scanner_vs_human.md](/home/ovadyat/MCP/reports/evaluation/scanner_vs_human.md), [scripts/evaluate_vs_human.py](/home/ovadyat/MCP/scripts/evaluate_vs_human.py)
- Human inter-rater study (Krippendorff's ordinal alpha with bootstrap CIs, Gwet's AC2 check): protocol and instrument built; "`responses/` … created once the study actually runs" — **no results yet** — [reports/experiments/human_annotation/README.md](/home/ovadyat/MCP/reports/experiments/human_annotation/README.md), [docs/project/human-annotation-experiment.md](/home/ovadyat/MCP/docs/project/human-annotation-experiment.md)
- v13 input levels (run21): AUC github 0.669, slack 0.913, calendar 0.953 against tool-only baselines of 0.623 / 0.653 / 0.647; 30/35 policy scenario pairs and 14/14 common-knowledge pairs — [v13 README](/home/ovadyat/MCP/reports/experiments/v13/README.md)
- v8 binding: reading the arguments halves mean over-scoring (+0.88 → +0.44 severity levels) and raises "exactly right" (github 37% → 62%, slack 46% → 73%, calendar 24% → 32%). github_helios under-scores on 18% of calls where register coverage is incomplete (recall 0.630): "register completeness a *safety* property" — [v8 README](/home/ovadyat/MCP/reports/experiments/v8/README.md)

**Dynamic results**
- Gen 1 (superseded composition, "Do not quote these numbers for the current dynamic layer"): at the critical threshold, recall 56% → 81% at unchanged 9% benign fall-out; real git traffic (400 calls) benign FPR 0.8% — [GROUND-TRUTH.md §4-5](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- Gen 2 (cell × likelihood × escalation) at a 1% misuse rate, 30 seeds: static cell alone AP github 0.485, calendar 0.602, slack 0.021 (random 0.010). × likelihood: 0.478, 0.203, 0.018. "**The likelihood term is negative on all three servers.** It has not earned its place." Escalation "Never fired". The run lists 9 corpus defects, for example 45% of Slack calls dropped by asset-name mismatch, and agents one-shot (median 32 calls) — [reports/experiments/dynamic_layer/RESULTS.md](/home/ovadyat/MCP/reports/experiments/dynamic_layer/RESULTS.md)
- dynamic_v2 (B × L): noise floor p95 0.007-0.084 when warm. Only 4 of 44 measurable Calendar inputs reach MIN_HISTORY, because the generator never fills write-tool arguments. "Every one of these [constants] was chosen while looking at the three development servers. That is data snooping" — [dynamic-layer-explained.md §3.7, §4](/home/ovadyat/MCP/docs/project/dynamic-layer-explained.md)
- Behaviour v4 simulation: 5 simulated GitHub orgs (60-300 agents, 180 days, last 90 scored), 460 gray episodes. Mean ordinary agent-days at ×3 fell 3.01% → 2.46% (v3 → v4); gray episodes caught at ×3: 70.7%; ordinary *calls* at ×3: 0.1% — [DIMENSION_FORMULAS.md §Simulation](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md), [02-mcp-runtime-security-literature.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/02-mcp-runtime-security-literature.md)
- Formula candidates (20 scenarios, 7 synthetic agent kinds, 132 checks per seed, 10 development seeds): J (calls, current) 93.3 ± 1.7; K (days, planned) 128.1 ± 1.3; deck v4 87.9 ± 1.9. Known misses of J: ordinary days at about ×1.4-1.9 instead of ×1; a new tool used daily is still about ×2.5 after two weeks; one burst day teaches that bursts are normal — [context-brief §7](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md). The latest four-dimension design passes 4 of 9 Pinecrest scenarios — [memory: dynamic-layer-v5-decisions.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/dynamic-layer-v5-decisions.md)
- MCPHunt, spread clock, run-level ROC AUC (risky vs benign / vs hard negative / unsafe vs safe / secret-carrying calls): static cell 0.501 / 0.486 / 0.579 / 0.477; gate risk (cell × B × L) 0.506 / 0.488 / 0.547 / 0.476; dynamic risk (static level × behaviour) 0.497 / 0.495 / 0.581 / 0.504. The real-clock 0.732 / 0.808 "is an artefact" of warm-up timing — [gateway/mcphunt/README.md](/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/README.md)
- MCPHunt vs an independent judge (gemma3:27b, 600 calls): Spearman 0.061 (cell) and 0.099 (dynamic risk); at level 4+, precision 0.385 and recall 0.668. Per route, git 0.892 and sqlite 0.765, but shell −0.225 and fetch −0.501. 50 under-scored `write_file` calls copy secrets into `notes/`: "The static side prices where a write lands, not what it carries" — [gateway/mcphunt/README.md](/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/README.md)

**Blind spots and limitations the repo states**
- B × L: no state across calls; no caller identity; no ownership check; "Rarity is not malice"; "A common tool used wrongly is the structural blind spot"; adapts, so it is not time-invariant; "It learns from traffic the adversary controls. Normalising a rare tool costs ~882 cover calls" — [dynamic-layer-explained.md §6](/home/ovadyat/MCP/docs/project/dynamic-layer-explained.md)
- The absent bound scores lower than a large one; the response is never looked at — [docs/project/dynamic-layer-blind-spots.md](/home/ovadyat/MCP/docs/project/dynamic-layer-blind-spots.md)
- Reviewer-style critique of the latest design: no real-data evaluation; designer-written scenarios; ships calls against its own evidence for days; exchangeability likely broken; no decision rule, analyst workload or false-discovery control; no ablation; Breadth may overlap BlastRadius; baselines missing — [context-brief §8](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md). The ablation study is still to do — [memory: dynamic-layer-ablation-todo.md](/home/ovadyat/.claude/projects/-home-ovadyat-MCP/memory/dynamic-layer-ablation-todo.md)
- Not measured: scalability vs manual assessment; the LLM judge; an external benchmark for the dynamic task ("none exists"); cross-organisation generalisation (one policy document for all deployments) — [GROUND-TRUTH.md §7](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- "There is no public dataset of real MCP traffic with per-caller identity" — [03-ueba-insider-threat-and-datasets.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/03-ueba-insider-threat-and-datasets.md)
- Planned evaluation metrics: EPSS-style coverage (recall), efficiency (precision) and effort (items flagged per 1,000); report AP over AUC at realistic base rates; claim triage quality, not detection — [external-benchmarks-and-positioning.md](/home/ovadyat/MCP/docs/project/external-benchmarks-and-positioning.md), [RESULTS.md](/home/ovadyat/MCP/reports/experiments/dynamic_layer/RESULTS.md)

### Inferences
- The only external-label test (MCPHunt) shows that per-call scoring cannot see content-level or flow-level risk (secrets copied into an innocuous location). The comparison report should list content inspection and information-flow tracking as capabilities our framework lacks and some competitors have (MCP-Guard, CrossMCP-Bench's IFG-Guard, RAC).
- The headline static numbers come from a single synthesised policy per org, written by the authors. Their external validity rests on the human study, which has not been run.

### Gaps
- No behaviour-multiplier result on real multi-day per-agent traffic exists. The repo names candidate datasets (CLUE-LDS, GH Archive, LANL, flaws.cloud CloudTrail, the RBA login dataset, FragBench) but none has been run.
- The oracle-panel file does not say which scanner version it graded, so its 35% / 69% numbers cannot be assigned to v5r with confidence.

## 7. Which external works does the repo already cite or summarise, and which comparisons has it already drawn?

### Takeaway
The repo already covers a large literature: about **200 distinct external works** across the files below. That includes 62 unique keys in `paper_v5/refs.bib` (65 entries, 3 duplicated) and 92 in `refs-full.bib`. Coverage is densest on MCP security (attacks, defences, benchmarks), risk scoring (CVSS, EPSS, AIVSS, MAESTRO), access control and standards (NIST, RAdAC), and UEBA (8 vendor products, about 12 academic UEBA/insider papers, 12+ public datasets). Several prior comparison documents exist, so a new report should treat these items as **already known**.

### Cited Findings

#### Existing comparison and positioning documents (already drawn)

| Document | What it compares | Status note |
|---|---|---|
| [docs/project/risk-scoring-taxonomy-comparison.md](/home/ovadyat/MCP/docs/project/risk-scoring-taxonomy-comparison.md) | 10 approaches (ToolSafe, MCPShield, MCP-Guard, R-Judge, MAESTRO, TRiSM, From Description to Score, Graph of Effort, OWASP AIVSS, the DRA review) on threat direction, scoring mode, formula, agent-awareness, MCP-specificity and output | Older; describes "session context" and formula "TBD" |
| [docs/project/external-benchmarks-and-positioning.md](/home/ovadyat/MCP/docs/project/external-benchmarks-and-positioning.md) | Direction discipline; rulebook vs judge vs risk score; R-Judge as closest; EPSS reporting frame; AgentHarm, Agent-SafetyBench, FORTIS; OWASP API1/API4; intent-based authZ (IGAC, SkillScope, aiAuthZ) | Current framing for evaluation |
| [docs/project/compass_survey_comparison.md](/home/ovadyat/MCP/docs/project/compass_survey_comparison.md) | The "Compass" survey (40+ works, April 2026, at [Literature_review/risk_scoring_frameworks_survey.md](/home/ovadyat/MCP/Literature_review/risk_scoring_frameworks_survey.md)) vs "MCP-RSS"; 30 net-new works; a formula landscape table | Older "MCP-RSS 1-10 ordinal" framing |
| [docs/project/mcip-summary.md](/home/ovadyat/MCP/docs/project/mcip-summary.md), [mcip-paper-full-summary.md](/home/ovadyat/MCP/docs/project/mcip-paper-full-summary.md) | MCIP (Jing et al., EMNLP 2025): contextual integrity, 10 risk categories, MCIP-Bench 2,218 instances, a guardian training set of 13,830 | Summary |
| [docs/project/annotated-bibliography-mcp-security.md](/home/ovadyat/MCP/docs/project/annotated-bibliography-mcp-security.md) | 30 papers in 7 categories (MCP security, agent safety benchmarks, vulnerability scoring, API risk, DRA, zero trust, prompt injection) | Annotated list |
| [Literature_review/related_work_gap_matrix.md](/home/ovadyat/MCP/Literature_review/related_work_gap_matrix.md) | A direction matrix (A→S, S→A, S→S, U→A, Ext→A, CVE) over industry frameworks, practitioner tools and academic defences, plus axes (timing, output type, agent-aware, policy-free) | Older "first dynamic, ordinal, agent-aware" claim |
| [knowledge_base/02-mcp-runtime-security-literature.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/02-mcp-runtime-security-literature.md) | 23 MCP runtime systems with direction, per-caller baseline yes/no, evaluation, and how the behaviour layer differs; benchmarks; honeypots; industry agent-baselining; "closest competitors a reviewer will name" | **Most recent and most rigorous** (verified 2026-10-25) |
| [knowledge_base/03-ueba-insider-threat-and-datasets.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/03-ueba-insider-threat-and-datasets.md) | 8 UEBA products (baseline, windows, per-signal output, aggregation), mapped onto v4; academic UEBA; per-user datasets | **Most recent UEBA comparison** (verified 2026-10-25) |
| [context-brief-2026-10-29.md §5.8](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md) | Each latest dimension mapped to a UEBA counterpart (Sentinel, GuardDuty, Exabeam, Elastic, Entra); kept vs changed | Latest |
| [docs/project/gateway-architecture.md](/home/ovadyat/MCP/docs/project/gateway-architecture.md) | Gateways and policy plumbing (OPA, Cerbos, AWS AgentCore Policy, IBM ContextForge, agentgateway, Langfuse, Helicone, Phoenix); NIST 800-207 roles | Current |
| [paper_v5/literature-review.md](/home/ovadyat/MCP/paper_v5/literature-review.md) | 53 papers and 11 primary sources in strands A-M, with a "Where the gap is" paragraph | For the AAMAS v5 paper |
| [Literature_review/mcp_server_cve_catalog.md](/home/ovadyat/MCP/Literature_review/mcp_server_cve_catalog.md), [mcp_server_attack_taxonomy_v2_agent_boundary.md](/home/ovadyat/MCP/Literature_review/mcp_server_attack_taxonomy_v2_agent_boundary.md) | 42 agent→server MCP CVEs (cutoff 2026-04-23); an agent→server attack taxonomy | Evidence inventory |

#### Conclusions already drawn in those documents
- The repo's latest positioning: "None of the academic systems we found grades each call against the same caller's own multi-week history." That idea appears only as a governance recommendation (Errico et al. §III-D), an individual IETF draft (AEBA), and vendor or open-source tools with no published evaluation. Claimed as new: per-caller argument-free scores on MCP-native dimensions; a bounded multiplier on a static score; one saturating shape with a max combiner; lowering-only safety valves; evaluation on mostly ordinary traffic per agent-day. **Not** to claim: first MCP gateway, first to baseline agent behaviour, first to detect misuse from metadata, first tamper-evident log — [02-mcp-runtime-security-literature.md §Positioning](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/02-mcp-runtime-security-literature.md)
- Commercial UEBA "agrees with v4 on most mechanisms" (first-time or uncommon for the user, warm-up, high price on first access to a critical asset, discounting habit). It differs in **peer groups** and **accumulation** (Exabeam/Splunk sum over a session or 24 h; v4 takes the max per call) — [03-ueba §Answers in brief](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/03-ueba-insider-threat-and-datasets.md)
- Kept from UEBA: a per-entity baseline, first time as the strongest signal but discounted, a long history with warm-up, raise-don't-block. Changed: graded rarity instead of flags plus points; no peer groups; one score per call before it runs — [context-brief §5.8](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md)
- Static gap claim: "Across all of it, asset sensitivity is assumed to be given. No prior work derives the sensitivity scale from … a classification policy in the FIPS 199 / SP 800-60 mould … and then validates the derived numbers against a held-out organizational inventory" — [paper_v5/literature-review.md](/home/ovadyat/MCP/paper_v5/literature-review.md)
- Gateway claim: "None of the gateways combines a design-time tool × asset matrix with learned per-caller behaviour" — [gateway-architecture.md](/home/ovadyat/MCP/docs/project/gateway-architecture.md)

#### Inventory of external works (name, year, one line, local file)
Abbreviations for files: **KB02** = [02-mcp-runtime-security-literature.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/02-mcp-runtime-security-literature.md); **KB03** = [03-ueba-insider-threat-and-datasets.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/03-ueba-insider-threat-and-datasets.md); **KB04/06/07** = [04-score-aggregation-and-calibration.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/04-score-aggregation-and-calibration.md) / [06-threat-model-and-evasion.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/06-threat-model-and-evasion.md) / [07-evaluation-methodology.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/07-evaluation-methodology.md); **CB** = [context-brief-2026-10-29.md](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/context-brief-2026-10-29.md); **BIB** = [paper_v5/refs.bib](/home/ovadyat/MCP/paper_v5/refs.bib) / [refs-full.bib](/home/ovadyat/MCP/paper_v5/refs-full.bib); **LR** = [paper_v5/literature-review.md](/home/ovadyat/MCP/paper_v5/literature-review.md); **TAX** = [risk-scoring-taxonomy-comparison.md](/home/ovadyat/MCP/docs/project/risk-scoring-taxonomy-comparison.md); **EXT** = [external-benchmarks-and-positioning.md](/home/ovadyat/MCP/docs/project/external-benchmarks-and-positioning.md); **CMP** = [compass_survey_comparison.md](/home/ovadyat/MCP/docs/project/compass_survey_comparison.md); **ANN** = [annotated-bibliography-mcp-security.md](/home/ovadyat/MCP/docs/project/annotated-bibliography-mcp-security.md); **GAP** = [related_work_gap_matrix.md](/home/ovadyat/MCP/Literature_review/related_work_gap_matrix.md); **GW** = [gateway-architecture.md](/home/ovadyat/MCP/docs/project/gateway-architecture.md).

**A. MCP runtime monitors, gateways and guards in our direction or mixed (14)** — all KB02 unless noted
- MCP Guardian (Kumar et al., 2025, arXiv 2504.12757): middleware with per-token fixed rate limits, a regex WAF and logging; no per-caller baseline (also GAP, GW)
- AegisMCP (Zhan et al., 2025, 2510.19462): smart-home MCP control-plane graph IDS; AUROC 0.985; global rarity, not per agent
- Praetor (Dang, 2026, 2604.26274): gateway sidecar with a DFA compiled from benign telemetry; blocks unseen edges; per deployment; not evaluated on MCP
- Content-aware attack detection in MCP tool-call traffic (Zavrak, 2026, 2605.11053): supervised session classifiers; metadata-only features plateau near AUROC 0.64
- ADR (C. Li et al., MLSys 2026, 2605.17380): endpoint LLM detector at Uber, 7,200+ hosts; ADR-Bench
- FragBench (Mehta et al., 2026, 2605.11029): cross-session fragment attacks with per-user linkage; event F1 0.88-0.96
- ChainWatch (Narayan et al., 2026, 2607.19432): HMM kill-chain proxy; design spec only; mostly S→A
- Governed MCP (Son, 2026, 2604.16870): kernel gateway with token buckets, a logit safety classifier and a Blake3 audit chain
- Runtime Policy Enforcement for MCP-Based LLM Agents (Wang, Zhu, Li, *Electronics* 2026): PEP with fixed caps and a SHA-256 hash-chained JSONL log
- RAC (Zhang et al., 2026, 2609.23498): session authorisation-drift checking; TraceBench
- HCP (T. Liu, 2026, 2606.29073): reference runtime with 8 security invariants
- CrossMCP-Bench / IFG-Guard (anonymous, 2026, HF dataset): authorisation-conditioned guard benchmark; IFG-Guard 92.0% detection, 0% FPR
- MCP-Guard (Xing et al., 2025, 2508.10991): static scan + E5 detector + LLM arbitrator; MCP-AttackBench (also TAX, ANN, GAP, BIB)
- MTGuard (He et al., 2026, 2607.25297): eBPF sandbox guard agent (also BIB `he2026mtguard`)

**B. MCP works in the opposite direction (S→A), for contrast (11)** — KB02 unless noted
- MindGuard (Wang et al., 2025, 2508.20412): tool-poisoning detection from attention graphs (also GAP)
- MCPShield (Zhou et al., 2026, 2602.14281): agent-side probing of untrusted servers (also TAX, CMP, BIB)
- MCPShield Formal (2026, 2604.05969): 7-category / 23-vector taxonomy from 177k tools (CMP)
- TrustShiftProbe / SHIELD (Rostamzadeh et al., 2026, 2608.23763): temporal baselines of *servers*
- Connor (Huang et al., 2026, 2604.01905): malicious-server detection by intent deviation
- MCP-RiskCue (Fu et al., 2025, 2511.05867): LLM risk inference from server logs (also BIB, LR)
- SecMCP (Shi et al., 2025, 2508.06418): conversation drift in latent space
- MCP-SandboxScan (Tan et al., 2026, 2601.01241): WASM execution analysis
- Yamasaki, Toda, Mori (IEICE 2026): tool logs correlated with OS audit logs
- AgentBound (Bühler et al., FSE 2026): Android-style permissions for MCP servers (also BIB, GW)
- ETDI (Bhatt et al., 2025, 2506.01333): OAuth-enhanced tool definitions against squatting and rug pulls (BIB, GAP, GW)

**C. MCP benchmarks and datasets (13)**
- MCPSecBench (Yang et al., 2025, 2508.13220): 17 attack types on 4 surfaces (KB02, ANN, BIB)
- MSB (D. Zhang et al., ICLR 2026, 2510.15994): 12 attacks, 2,000 instances, S→A (KB02, EXT)
- MCP-SafetyBench (Zong et al., 2025, 2512.15163): 20 attack types on real servers (KB02)
- MCPTox (Wang et al., AAAI, 2508.14925): tool poisoning, 1,348 cases (KB02, BIB)
- MCIP / MCIP-Bench (Jing et al., EMNLP 2025, 2505.14590): contextual-integrity taxonomy and guardian (mcip-summary.md, KB02, GAP, BIB)
- RAS-Eval (Fu, Yuan, Wang, 2025, 2506.15253): 80 test cases, 3,802 attack tasks, MCP format (KB02)
- MCPHunt (H. Li et al., 2026, 2604.27819): 3,615 traces of cross-boundary credential propagation; **used as outside test data** (KB02, [gateway/mcphunt/README.md](/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/README.md))
- GatewayBench (Zheng et al., 2026, 2610.23449): 7 MCP gateways compared on TSR and ASR (KB02)
- cx-cmu/agent_trajectories `mcpbench` split: 899 benign MCP-Bench trajectories (KB02)
- "Labels Are Not Endpoints" (Ahmed, Abbas, 2026, 2608.12880): treatment leakage in MCP security labels (KB02)
- ADR-Bench (2026): 302 tasks (KB02)
- DVMCP (Damn Vulnerable MCP server): 10-challenge lab (GAP)
- TraceSafe-Bench (2026, 2604.07223): granular beats binary across 13 LLMs (CMP)

**D. MCP taxonomies, measurement and ecosystem studies (≈17)**
- Hou et al., MCP Landscape (2025, 2503.23278): names malicious users among attacker types (KB02, ANN, BIB)
- Errico, Ngiam, Sojan, Securing MCP (2025, 2511.20920): §III-D proposes per-user/role behavioural baselines at MCP gateways; no implementation (KB02, GW)
- MCP-38 (Shen et al., 2026, 2603.18063): 38-category threat taxonomy (KB02, BIB)
- MCP-DPT (Rostamzadeh et al., 2026, 2604.07551): defence-placement taxonomy (KB02, ANN, EXT, BIB)
- MCP Safety Audit / MCPSafetyScanner (Radosevich, Halloran, 2025, 2504.03767) (KB02, ANN, GAP, BIB)
- Song et al., Beyond the Protocol (2025, 2506.02040); Zhao et al., When MCP Servers Attack (2025, 2509.24272) (KB02)
- Parasites in the Toolchain (Zhao et al., IEEE S&P 2026, 2509.06572): 12,230 tools over 1,360 servers (KB02, BIB)
- Hasan et al., MCP at First Glance (2025, 2506.13538); Guo et al., Measurement Study (2025); X. Li & Gao, First Look (2026); Z. Li et al., Privilege Management in MCP (2025); Gaire et al., SoK (2025) (BIB, ANN)
- Huang et al., Caller Identity Confusion in MCP (2026): "identity cannot separate good calls from bad" (BIB, cited in [GROUND-TRUTH.md §8](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md))
- Mellafe Zuvic, Capability Gates Are Not Authorization (2026) (BIB)
- Huang et al., Auditing MCP Servers for Over-Privileged Tool Capabilities (2026) (BIB)
- Xiong et al., Butterfly Effects in Toolchains (2025) (BIB)
- Invariant Labs, Tool Poisoning notification (2025) and GitHub MCP exploit (BIB, KB06)
- OWASP Top 10 for MCP (2025) (BIB)
- MCP specification revisions 2025-06-18, 2025-11-25, 2026-07-28 (KB02, KB06, GW)

**E. Agent-safety benchmarks and agent-risk work (≈12)**
- R-Judge (Yuan et al., EMNLP Findings 2024, 2401.10019): 569 records, 10 risk types; "closest published work" in unit of analysis (EXT, TAX, ANN, LR)
- AgentHarm (Andriushchenko et al., ICLR 2025, 2410.09024): 110/440 malicious tasks (EXT, ANN, BIB)
- Agent-SafetyBench (Zhang et al., 2024, 2412.14470): 349 environments, 2,000 cases (EXT, BIB)
- FORTIS (2026, 2605.09163): over-privilege in agent skills (EXT)
- ToolEmu (Ruan et al., ICLR 2024); InjecAgent (Zhan et al., ACL Findings 2024); AgentDojo (Debenedetti et al., NeurIPS 2024); ASB (ICLR 2025) (ANN, LR, BIB)
- Agentic Misalignment (Lynch et al., 2025); A Sober Look at Agentic Misalignment (Ye et al., 2026) (BIB)
- ASTRA (Hazan et al., 2025, 2511.18114): agent-level risk assessment (LR, CMP)
- Tang et al., LM Agents May Fail to Act on Their Own Risk Knowledge (2025); Yin et al., Reasoning Trap (2025); Xu et al., tool hallucination (2024) (BIB)

**F. Agent guards and authorisation (≈25)** — mostly BIB and LR unless noted
- ToolSafe (Mou et al., 2026, 2601.10156): step-level guardrail; BTRA pattern (TAX, LR)
- GuardAgent (Xiang et al., 2024, 2406.09187) (ANN, GAP)
- Progent (Shi et al., 2025, 2504.11703): privilege-control DSL (GAP, EXT)
- MiniScope (Zhu et al., 2025, 2512.11147): least-privilege tool authorisation (GAP)
- AgentGuardian (Abaev et al., 2026): learned access-control policies
- PAuth (Sharma et al., 2026); Conleash (Li et al., 2026); STARS (Zhang et al., 2026); AgentTrust (Yang, 2026); NEXUS (Hossain, 2026); IGAC (Zhu & Wang, 2026); SkillScope; aiAuthZ; "Do Coding Agents Understand Least-Privilege Authorization?" (EXT)
- Fleming et al., LLM-judged TBAC risk-adaptive access control (2025, 2510.11414) (LR, EXT)
- ProbGuard (Wang et al., 2025, 2508.00500): DTMC runtime monitoring (LR)
- Rahman & Rahman, Role-Stratified Conformal Risk Control for LLM Tool Calls (2026, 2607.24343) (BIB, EXT)
- Uppala, MCP proxy enforcement (2026); Uchibeke, deterministic pre-action authorisation (2026); Tallam, five-plane runtime governance (2026) (BIB)
- AgenTRIM (Betser et al., 2026, 2601.12449): tool-level risk filtering (LR, CMP)
- SEAgent (2601.11893), AgentSpec (2503.18666, ICSE 2026), AgentSentinel (2509.07764), TrustBench (2603.09157) (CMP)
- A Fraud-Detection-Inspired Framework for LLM Agents Security (2026, 2605.01143) (EXT)
- Li et al., Vision for Access Control in LLM Agent Systems (2025); Shi et al., SoK Trust-Authorization Mismatch (2025) (BIB)
- Out-of-direction, cited only for contrast: CaMeL, dual-graph provenance (2605.26497), LlamaFirewall / NeMo Guardrails (EXT, GAP)

**G. Risk-scoring frameworks and severity scales (≈30)**
- CVSS v4.0 (FIRST, 2023); Spring & Hatleback, Time to Change the CVSS? (IEEE S&P Mag. 2021); Wunder et al., CVSS inconsistencies (2024) (BIB, LR)
- EPSS (Jacobs et al., DTRAP 2021, 1908.04856): the reporting frame of coverage, efficiency and effort (EXT, ANN, LR)
- Bahar et al., Validity of CVSS/DREAD for LLM attacks (2024, 2412.20087) (ANN, LR)
- OWASP AIVSS (2025; v0.5) and Huang et al., AIVSS for Agentic AI (2026) (TAX, ANN, BIB, CMP)
- From Description to Score (Jafarikhah et al., ACM SAC 2026, 2512.06781): "closest methodological neighbour" (LR, TAX, GAP)
- MCP-in-SoS (Kumar et al., 2026, 2603.10194): risk of the *server implementation*; A→S threat model; static (LR, CMP)
- MAESTRO / ATFAA (2025, 2508.10043): R = P × I × E (TAX, ANN, CMP; also an oracle-panel rater)
- TRiSM for Agentic AI (Raza et al., 2025, 2506.04133) (TAX, GAP)
- Graph of Effort (2025, 2503.16392) (TAX, ANN)
- Cheimonidis & Rantos, Dynamic Risk Assessment SLR (2023): 50 models (TAX, ANN, BIB)
- From the Compass survey (CMP): CORTEX (2508.19281), AgentGuard MDP (2509.23864), AURA (2510.15739), GaaS (2508.18765), Guardrails as Infrastructure (2603.18059), TOP-R mosaic effect (2512.16310), Trinity Defense (2602.09947), KRI framework (2603.12450), NVIDIA ARP (2511.21990), Quantitative Security Benchmarking MAS (2507.21146), ConfusedPilot (2408.04870), Permission Risk Scoring (2512.15781), SafePred; industry: Microsoft AGT (0-1000 trust score), Traceable AI (0-10 likelihood × impact), CSA Agentic Trust Framework, FINOS AIR-OP-028, Repello blast radius, Adversa MCP Top 25, Databricks DASF v3.0
- Owiredu-Ashley, Action-Graded Severity Scale for Tool-Using Agents (2026) (BIB)
- Cao et al., Multilevel Anomaly Detection benchmark (2024, 2411.14515): "graded beats binary" (LR, BIB)
- Aharon et al., few-shot API injection detection (2024) (LR)
- Bradatsch et al., Zero Trust score-based network access control (2024); Paulraj et al., critical-infrastructure framework (2025) (LR)
- Cox Jr., What's wrong with risk matrices? (Risk Analysis 2008) (CB)
- Marchiori et al., Can LLMs classify CVEs? (2025); Mahara, Entra OAuth app permission risk scoring (2025) (BIB)
- Asset importance: McKechnie & McDonald, SARA (2024); Gangupantulu et al., Crown Jewels Analysis (2021); Aydin, CIA+TA (2025); Vyhmeister et al., data valuation (2025); Engelberg et al., AI Native Asset Intelligence (2026); Yan et al., SALP-CG (2026); Al Mandalawi et al., policy-aware GenAI (2025) (BIB)

**H. Access control, zero trust and standards (≈25)**
- NIST SP 800-207 Zero Trust; NIST SP 800-162 / Hu et al. ABAC (2014); NIST SP 800-30 Rev. 1 (2012); FIPS 199 (2004); SP 800-60 (2008) (GW, CB, BIB)
- Sandhu et al., RBAC (1996); Cheng et al., Fuzzy MLS (2007); Kandala, Sandhu, Bhamidipati, RAdAC (ARES 2011); Ni et al., fuzzy risk-based AC (2010); Shaikh et al., dynamic risk-based decisions (2012); Atlam & Azad, risk-based AC SLR (2020) (BIB, GW)
- Anderson, Computer Security Threat Monitoring and Surveillance (1980); Pynadath & Tambe, adjustable autonomy (2002) (BIB)
- RFC 5789 (PATCH), RFC 9110 (HTTP semantics): the impact 3/4 boundary; RFC 9728, RFC 8707, OAuth 2.1; RFC 9449 DPoP (GROUND-TRUTH, GW, KB06)
- OWASP API Top 10 (API1 BOLA, API4 resource consumption); OWASP LLM Top 10 incl. LLM06 Excessive Agency; OWASP Agentic Top 10 (2026); MITRE ATLAS (EXT, GAP, BIB)
- Zero-trust agent works: Caging the Agents (2603.17419); Zero-Trust Identity Framework for Agentic AI (2505.19301); Zero-Trust multi-LLM survey (2508.19870) (ANN, CMP)
- OpenTelemetry GenAI MCP semantic conventions (KB02; the basis of the log field names)
- Industry disclosures: Anthropic MCP intro (2024) and Building Effective Agents (2024); Microsoft Securing AI Agents (2026) (BIB)

**I. UEBA products, agent-behaviour analytics and academic UEBA / insider threat (≈30)**
- Vendors (KB03 [V1-V19], CB §5.8): Microsoft Sentinel UEBA (InvestigationPriority 0-10; 10/30/90/180-day insights); Splunk UBA (peer groups; end of life 2027-01-31); Splunk ES risk-based alerting (sum > 100 per 24 h); Exabeam Advanced Analytics (60-90 days, 80% convergence, rule points, notable at 90); Elastic ML (`rare`, `time_of_day`, ≥20 buckets); Okta behaviour detection (last N sign-ins; step-up only, never deny); Microsoft Entra ID Protection (≥5-day learning; mass access to sensitive files); AWS GuardDuty IAM anomaly findings
- Agent-specific baselining (KB02): IETF draft-sharif-aeba-00, Agent Event Behaviour Analysis (2026; 24-hour and 90-day windows, peer groups, weighted composite in [0, 1], no evaluation); Exabeam Agent Behavior Analytics (baselines in about 14 days, including MCP); observability-mcp "Inspect" (observe → dry-run → enforce); MCPKernel and agentsentinel (per-agent z-scores at 2.5σ and 3σ; Trust Score)
- Academic UEBA and insider threat (KB03, CB, KB06/07): Shashanka, Shen, Wang (IEEE BigData 2016, Niara UEBA); Freeman et al., Who Are You? (NDSS 2016; per-user login feature rarity, the "closest published analogue" of Typical Footprint); Wiefling et al. (ACM TOPS 2022; RBA on 3.3 M users); Glasser & Lindauer (S&P Workshops 2013, CERT); Tuor et al. (AAAI AICS 2017); Le, Zincir-Heywood, Heywood (IEEE TNSM 2020; user-day granularity); Homoliak et al. (ACM CSUR 2019); Schonlau et al. (Statistical Science 2001); Ben Salem & Stolfo (RUU; masquerade survey); Harilal et al. (TWOS, 2017); Landauer et al. (CLUE-LDS, IEEE BigData 2022); Anjum et al. (SACMAT 2021, OpTC); Larroche (ANUBIS 2026); Javitz & Valdes (NIDES, SRI 1994); Yen et al., Beehive (ACSAC 2013); Steinwart, Hush, Scovel (JMLR 2005); Ho et al., credential spearphishing (USENIX Sec 2017)

**J. Public datasets with per-user logs, and MCP traffic evidence (≈20)** — KB03, KB02
- CLUE-LDS (Nextcloud, 50.5 M events, 1,910 days); GH Archive; LANL 2014, 2015 and 2017; flaws.cloud CloudTrail; the RBA login dataset (33 M logins); DARPA OpTC; CERT r1-r6.2 (fully synthetic); TWOS; RUU; Schonlau; DARPA TC E5; OTRF Security Datasets; Splunk BOTS v3; evalstate/mcp-clients (HF MCP client table)
- MCP honeypots: GreyNoise MCP honeypots (2025; "no MCP-specific payload"); workspace-tools-mcp (12 days, 1,081 handshakes, 1 tool call); honeymcp; Kai Security honeypot (**UNVERIFIED**, secondary source)

**K. Score aggregation, calibration and evaluation methodology (≈35)** — KB04, KB07, CB
- Conformal and p-values: Bates et al., conformal p-values (Ann. Stat. 2023); Vovk, Gammerman, Shafer (2005); Barber et al.; Laxhammar (conformal anomaly detection); Lancaster mid-p (JASA 1961); Heard & Rubin-Delanchy (Biometrika 2018); Vovk & Wang (2020, 2021 e-values); Wang & Ramdas (e-value FDR 2022); Benjamini-Hochberg; Benjamini-Yekutieli; Javanmard-Montanari (online FDR); Šidák; Tippett (via Heard); Wilson harmonic-mean p; Liu & Xie Cauchy combination; Donoho & Jin higher criticism; Good-Turing; DKW / Massart
- Outlier ensembles and calibration: Aggarwal & Sathe; Kriegel et al.; Zimek et al.; Guo et al. (ICML 2017); Niculescu-Mizil & Caruana; DeGroot & Fienberg
- Evaluation pitfalls: Arp et al., Dos and Don'ts (USENIX Sec 2022); Sommer & Paxson (S&P 2010); Axelsson base-rate fallacy (TISSEC 2000); Alahmadi et al., 99% false positives (SOC); Hassan et al., NoDoze; Pendlebury et al., TESSERACT; Carlini et al., adversarial robustness; Arcuri & Briand; Demšar; Saito & Rehmsmeier (PR vs ROC); McClish (partial ROC); Saltelli; Morris; Nosek (preregistration); Kapoor & Narayanan (leakage); Brown-Cai-DasGupta; Field & Welsh; Holm; Engelen et al. (CICIDS2017); Ralph et al. (empirical standards)
- Human annotation: Krippendorff (2004/2013), Gwet's AC2 ([human-annotation-experiment.md](/home/ovadyat/MCP/docs/project/human-annotation-experiment.md)); Zheng et al., LLM-as-a-Judge (2023) (BIB)

**L. Evasion and adversarial ML (≈12)** — KB06
- Wagner & Soto, mimicry attacks (CCS 2002); Rubinstein et al. (boiling frog, IMC 2009); Kloft & Laskov (JMLR); Barreno et al. (can ML be secure?); Chan-Tin et al. (frog-boiling attack); Ben Salem, Hershkop, Stolfo (insider survey); Douceur, Sybil attack (IPTPS 2002); Greshake et al., indirect prompt injection (2023); Shi et al., ToolHijacker (2025); InjecAgent; System-level IFC defence (2409.19091); FATH (2410.21492) (KB06, ANN)

**M. Gateway and policy plumbing (≈15)** — GW, EXT
- OPA bundles and decision logs; Cerbos; AWS AgentCore Policy (Cedar); IBM ContextForge; agentgateway; Langfuse; Helicone; Arize Phoenix; the Azure event-sourcing pattern; Lasso MCP Gateway; Invariant `mcp-scan` / Snyk `agent-scan`; Cisco mcp-scanner; MCP-Shield (riseandignite); MCP Guard (General-Analysis); eqtylab mcp-guardian; Cloudflare API Shield (enumeration by unique-element counts); AuthProbe (2607.20574); Barabanov et al. (2201.10833); SMCP (2602.01129); ScopeGate (2606.28679)

#### Count check
- Second pass: `paper_v5/refs.bib` holds **65 entries / 62 unique keys** (duplicates: `betser2026agentrim`, `owireduashley2026severity`, `zhang2026stars`). `refs-full.bib` holds **92 unique entries**. Both counts differ from GROUND-TRUTH's stated "40" and "77", which are stale — [paper_v5/refs.bib](/home/ovadyat/MCP/paper_v5/refs.bib), [paper_v5/refs-full.bib](/home/ovadyat/MCP/paper_v5/refs-full.bib), [GROUND-TRUTH.md §8](/home/ovadyat/MCP/paper_v5/GROUND-TRUTH.md)
- The annotated bibliography lists 30 papers; the AAMAS literature review 53 papers + 11 sources; the Compass comparison 30 "net-new" works; KB02 54 references; KB03 29 dataset/paper and 19 vendor sources — [ANN](/home/ovadyat/MCP/docs/project/annotated-bibliography-mcp-security.md), [LR](/home/ovadyat/MCP/paper_v5/literature-review.md), [CMP](/home/ovadyat/MCP/docs/project/compass_survey_comparison.md), [KB02](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/02-mcp-runtime-security-literature.md), [KB03](/home/ovadyat/MCP/reports/experiments/dynamic_dimensions/knowledge_base/03-ueba-insider-threat-and-datasets.md)

### Inferences
- With overlaps removed, the inventory above names about **200 distinct external works**. This is an estimate from the category counts (≈14 + 11 + 13 + 17 + 12 + 25 + 30 + 25 + 30 + 20 + 35 + 12 + 15 ≈ 260, minus about 60 that recur across categories). A new MCP-risk-scoring or UEBA comparison should flag as "new" only works absent from KB02, KB03 and the two bib files. Works likely to be genuinely new: any MCP runtime system published after 2026-10-25 (KB02's verification date), and UEBA products not in KB03 (for example CrowdStrike, Securonix, Varonis, Google SecOps; none appears in these files).
- The older comparison docs (TAX, CMP, GAP) describe an earlier "MCP-RSS, ordinal 1-10, session-context" framework. Their comparison rows for "our project" are stale and should not be reused without updating to the current profile in Section 2.

### Gaps
- The `Literature_review/excels/` spreadsheets and `pdf/` subfolders were not opened, so the paper catalog there may hold more works not listed above.
- KB04, KB06 and KB07 reference lists were read only at the first-author/title level; their one-line relevance notes were not extracted.
- Kai Security's honeypot and CrossMCP-Bench's venue are marked UNVERIFIED in the repo itself.
