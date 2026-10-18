# Dynamic Context Catalog

Every kind of runtime context a gateway in front of one MCP server can use **without reading
the tool's input values** — inputs belong to the static layer. Nine big contexts, each split
into small contexts with what it means, an example, how it is judged, what the literature
says, and whether the current logs can test it.

Companion to [Dynamic Layer Blind Spots](dynamic-layer-blind-spots.md) (what the current
runtime sees) and [The Dynamic Layer, Explained](dynamic-layer-explained.md) (how it works
today).

## Ground rules

**Position.** The defender is a gateway in front of one MCP server. It sees the calls made to
this server, the transport and session metadata, its own responses, and the server clock. It
never sees the user's task, the agent's reasoning, the model's internals, or calls the agent
makes to other servers.

**Inputs are out.** No context below reads a tool argument's value. Anything derived from
inputs is the static layer's job ([input typing](../standards/input-typing.md)).

**Legend** used on every small context:

| Field | Values |
|---|---|
| Judged by | **Rule** — compared to what the org wrote in its policy. **Learned** — compared to past traffic, which an attacker can shape. **Static** — read from the static layer's result for this call (an open design decision, see [Session](#5-session-context--how-the-calls-fit-together)). |
| Evidence | **Evaluated** — a paper measured it. **Proposed** — a paper suggests it without measuring. **None** — no paper found. |
| Logs | Whether the real, labeled corpora can test it today. |

## The big contexts at a glance

| # | Big context | Question it answers | Strongest evidence |
|---|---|---|---|
| 1 | [Subject](#1-subject-context--who-is-calling) | Who is calling, and what may they do? | Evaluated: per-caller scope enforcement |
| 2 | [Action](#2-action-context--what-kind-of-call) | What kind of call is this, at tool level? | Rule-based, from the policy |
| 3 | [Time](#3-time-context--when) | When is it happening, and how fast? | Proposed only |
| 4 | [Environment](#4-environment-context--under-what-conditions) | Under what conditions? | Proposed only |
| 5 | [Session](#5-session-context--how-the-calls-fit-together) | How do this caller's calls fit together? | Weak alone (AUROC 0.64) |
| 6 | [Outcome](#6-outcome-context--what-the-server-returned) | What did the server send back? | Never tested apart from inputs |
| 7 | [Protocol](#7-protocol-context--how-the-client-speaks-mcp) | How does the client speak MCP? | Evaluated: unlisted-tool re-check |
| 8 | [Population](#8-population-context--compared-with-everyone-else) | How does this compare with everyone else? | Learned, so poisonable |
| 9 | [Policy](#9-policy-context--the-yardstick) | What did the org say is normal? | The yardstick, not a signal |

In access-control terms (NIST SP 800-162), 1 is the *subject*, 2 the *action*, 3 and 4 the
*environment*; the *resource* (which asset) comes from the static layer. 5–8 add what ABAC
does not have: history.

## 1. Subject context — who is calling

**Verified identity.** Who the credential belongs to (OAuth subject, token owner), as checked
by the server — not what the client says about itself.
- Example: the `slack_vireo` token belongs to a study-operations assistant.
- Rule · Evaluated as part of scope enforcement (2605.18414, 2609.14780) · Logs: no (only 17
  finance calls carry an `X-Agent-Id` header).

**Granted scope.** Which tools and assets this identity may use. Out-of-scope calls are
blocked before any scoring.
- Example: a scheduling agent on `calendar_aurora` has no reason to call `manage-accounts`.
- Rule · Evaluated: per-caller tool filtering in a proxy cut unauthorized calls to 0%, against
  4–37% when the allowlist sat only in the prompt (2605.18414) · Logs: no.

**On whose behalf.** The human the agent acts for, when the token carries delegation. Lets the
human's role apply, not just the agent's.
- Rule · None for MCP · Logs: no.

**Client software.** The `clientInfo` name and version from `initialize`. Self-reported, so it
can be faked; useful only for consistency (see [Protocol](#7-protocol-context--how-the-client-speaks-mcp)).
- Rule · None · Logs: constant harness names only.

**Caller age.** Time since this identity was first seen. A brand-new identity going straight
to sensitive tools is different from an old one.
- Rule · Proposed (novelty with expiry, 2510.19462) · Logs: no.

**Caller record.** Past denials and flags for this identity.
- Rule · Proposed ("repeated auth failures", 2511.20920) · Logs: no.

**Shared credential.** Many agents or sessions behind one identity, which makes every other
subject context weak.
- Evaluated as a measurement: many MCP servers cannot tell callers apart (2603.07473) and many
  remote servers have no authentication at all (2605.22333) · Logs: no.

> Use identity for **rules**, not for learned per-caller baselines. Per-caller conditioning
> collapsed misuse AUC from 0.53 to 0.30 on the synthetic testbed
> (`reports/dynamic_eval/embedding/EMBEDDING_LIKELIHOOD.md`).

## 2. Action context — what kind of call

**Tool name.** Which tool was called. Always available.
- Rule or Learned · Logs: yes.

**Tool class.** Read, write, delete, send or admin — taken from the tool's definition (the
static atomic-operation label), not from the call's inputs.
- Static (tool level) · Logs: yes.

**Tool's policy status.** Allowed, never, or needs approval. The policy already has these:
`conversations_join`, `create_repository` and `merge_pull_request` are "never" in
[server-policies-abstract.md](../mcp-tools/server-policies-abstract.md).
- Rule · Evaluated indirectly (tool-level enforcement, 2605.18414) · Logs: yes.

**Tool rarity.** How unusual this tool is for this org — the current runtime's `L`.
- Learned · Own result: lowered ranking quality on 2 of 3 servers
  (`reports/experiments/dynamic_layer/RESULTS.md`), and about 882 cover calls make a rare tool
  look normal ([Evaluating the Dynamic Layer](evaluating-the-dynamic-layer.md)) · Logs: yes.

**Decoy tool.** A tool no legitimate workflow ever calls; any call is a tripwire.
- Rule · Evaluated: 0 false alarms in 485 benign runs, but caught only 26–37% of all attack
  attempts (2605.11026, agent tool calls, not MCP-specific) · Logs: no.

**Static result for this call.** The asset the call was bound to, its cell score, and the v12
policy checks. Not a raw input, but computed from inputs — see the open decision under
[Session](#5-session-context--how-the-calls-fit-together).
- Static · The asset binding is wrong on 46% of live calls
  ([Dynamic Layer Design](dynamic-layer-design.md)) · Logs: human asset labels exist.

## 3. Time context — when

The server clock records time, so an agent cannot fake it the way it can shape an input.

**Time of day, day of week, holidays.** Agent activity outside the org's working hours.
- Rule (proposed policy line *Normal hours*) · Proposed (2504.08623, 2511.20920) · Logs: no —
  every timestamp in the labeled corpora is made up.

**Allowed windows.** Writes to specific assets only inside approved windows — a change to the
`github_helios` perimeter repositories outside change control, for instance.
- Rule (proposed policy line *Allowed windows*) · None · Logs: no.

**Rate per window.** Calls per minute or hour for one caller.
- Rule (a cap) · Proposed and stress-tested only (2504.12757) · Logs: no.

**Gap between calls.** A burst far faster than the normal workflow.
- Rule or Learned · Proposed (2607.19432). Calibrate by **call count, not seconds**:
  wall-clock thresholds have no useful regime at agent speed (2606.19386) · Logs: no.

**Session duration.** One session running far longer than any task needs.
- Rule (Block 4: "a handful of calls per request") · Proposed (2510.19462, 2607.19432) ·
  Logs: no.

**Time between related calls.** A write or send soon after a sensitive read.
- Rule, over tool classes · Evaluated on synthetic agent data as "turns from sensitive read to
  external send" (2605.01143) · Logs: computable, but sessions leak the label.

**Slow drift over days.** An attacker who stays below every threshold by going slowly. Only
rules hold here; a learned baseline is exactly what slow drift poisons.
- Rule · The behave-then-defect pattern is shown in 2608.23763 (for a malicious server; the
  mechanism carries over) · Logs: no.

> MCP traffic timing does not stand out at the network level — it looks like ordinary machine
> polling (2609.19091). That is a statement about network intrusion detection, not about
> time as a policy rule.

## 4. Environment context — under what conditions

**Transport and origin.** Local stdio or remote HTTP; the source network.
- Rule · Proposed (IP and location in 2504.08623) · Logs: every call comes from 127.0.0.1.

**Deployment.** Which instance the call reached — production or test.
- Rule · None · Logs: no.

**Org state.** An incident, audit period or change freeze the org has declared, which
tightens every other rule while it lasts.
- Rule · None · Logs: no.

**Server state.** Load and remaining quota; a bulk call costs more near a limit.
- Rule · None for agent risk · Logs: no.

## 5. Session context — how the calls fit together

> **Open decision.** Contexts marked *Static* read the static layer's per-call result. They
> never read inputs directly, but they depend on them. Allowing them is what makes rules like
> "several channels in a row" (`slack_vireo`, Table 4) checkable.

**Order of tools.** The sequence of tool names.
- Learned · Weak alone: metadata plus session structure reaches AUROC 0.64 on unseen tasks
  (2605.11053); a sequence-only detector was withdrawn by its own authors (2606.30566, agent
  memory, not MCP); works for narrow fixed workflows (2604.26274, agent tool calls, which also
  reads inputs) · Logs: every session holds a single label, so any session feature separates
  the classes by construction.

**Class pattern.** Read, then list, then write — escalation over tool classes.
- Rule · Evaluated on synthetic agent data (2605.01143) · Logs: label leak (as above).

**Session size.** Number of calls and distinct tools, against Block 4's normal workflow.
- Rule · Evaluated only inside a fused detector (session DAG statistics, 2510.19462) ·
  Logs: label leak.

**Repetition.** The same tool again and again — enumeration, paging through everything.
- Rule or Learned · Proposed · Logs: label leak.

**Cumulative static risk.** The highest or total cell score so far in the session.
- Static · Evaluated on synthetic agent data as cumulative tool risk (2605.01143) ·
  Logs: computable from asset labels.

**Distinct assets touched.** How many different assets one session reaches.
- Static · None · Logs: computable from asset labels.

## 6. Outcome context — what the server returned

The current runtime never looks at the response
([Blind Spots §2](dynamic-layer-blind-spots.md#2--the-response-is-never-looked-at)).

**Error or denial.** The call failed or was refused.
- Rule · Proposed · Logs: only 2 of 3,000 live calls failed — too few to test.

**Retry after denial.** Trying again, or trying a neighbour, after a refusal — probing.
- Rule · Denied calls modelled as graph nodes (2604.04035). Keep refusals generic: agents
  infer that they are being watched from blocking feedback (2603.16928), and denial messages
  can leak protected information (2604.04035) · Logs: no.

**Empty or not-found results.** Guessing identifiers that do not exist.
- Rule or Learned · None · Logs: status only.

**Response size and record count.** How much the server sent back.
- Rule or Learned · Never tested apart from inputs: 2605.11053 combines argument and response
  embeddings · Logs: live responses are cut at 280 characters; full sizes only in about 300
  demo-server calls.

**Response sensitivity.** Whether what the server is about to return contains data the
caller should not get. This reads output content — a value, though not an input; deciding
whether that is allowed is part of the design.
- Rule · Proposed as DLP (2511.20920) · Logs: cut at 280 characters.

**Latency.** Unusually heavy calls.
- Learned · None · Logs: demo-server captures only.

## 7. Protocol context — how the client speaks MCP

**Handshake.** Protocol version, capabilities and `clientInfo` at `initialize`.
- Rule · None · Logs: demo-server captures only.

**Handshake changes.** A different `clientInfo` for the same identity, or mid-stream.
- Rule · None · Logs: no.

**Tool discovery.** How often the caller re-lists tools with `tools/list`.
- Rule or Learned · None · Logs: demo-server captures only.

**Unlisted tool calls.** A call to a tool this caller was never shown — an injected or
hallucinated tool name.
- Rule · Evaluated: the proxy in 2605.18414 re-checks every `tools/call` against the caller's
  filtered list · Logs: `BAD_TOOL` cases exist only as robustness tests in the wire logs.

**Other primitives.** Use of resources, prompts and notifications.
- None · Logs: no.

## 8. Population context — compared with everyone else

All of these are learned, so all of them can be shaped by an attacker who generates enough
ordinary-looking traffic first.

**Org-wide tool frequency.** How common this tool is across all callers of this org.
- Learned · Own result: pooling by org beat per-agent baselines early on (AUC 0.492 → 0.723 in
  the first 50 calls, [Dynamic Layer Design](dynamic-layer-design.md)) · Logs: yes.

**Peer group.** How callers with the same role usually behave.
- Learned · None for MCP · Logs: personas are authored, never sent on the wire.

**Pattern rarity across tenants.** How rare this sequence of tool types is across everyone.
- Learned · Evaluated in an emulated smart home (Count-Min rarity, 2510.19462) · Logs: no.

**Cross-session patterns.** Problems visible only across many sessions, not inside one.
- Learned · Abstract-level only (2604.11806) · Logs: no.

## 9. Policy context — the yardstick

Not an observation. This is what the observations are compared to. The rules above come from
the [policy template](../standards/policy.md):

| Policy part | Feeds |
|---|---|
| Block 0 — org context | which outcomes matter, and to whom |
| Table 2 — asset register | the static result (asset weight) |
| Table 3 — value rules | static only: these read inputs |
| Block 4 — normal workflow | session size, repetition, rate |
| Table 4 — tool-level rows ("call count: never") | tool's policy status |
| *Proposed:* Normal hours, Allowed windows | time rules |
| *Proposed:* Callers — agent roles and the tools each may use | granted scope |

The two proposed time lines would carry the same `stated` / `draft` marking as Table 4. The
template has no subject section yet; granted scope needs one before it can be a rule.

## Context you cannot use

| Context | Why not | Example papers |
|---|---|---|
| The user's task or intent | The server never sees it | 2412.16682, 2502.05174, 2505.14590 |
| The agent's reasoning or transcript | Not visible to the server | 2505.03574, 2605.17380 |
| Model internals | Not visible to the server | 2508.20412 |
| Calls to other servers | Only this server's calls are visible | 2607.19432, 2609.23498 |
| Tool input values | Excluded by design — the static layer's job | — |
| Data flow / taint tracking | Works by spotting values that reappear in later inputs | 2503.18813, 2505.23643, 2605.11360 |

The cost of excluding inputs is real: on unseen tasks, metadata alone stops at AUROC 0.64,
while content features (inputs plus responses) exceed 0.89 (2605.11053). The dynamic layer
can only stay input-free if the static layer carries the content.

## What the current logs can test

| Big context | Testable on real labeled logs today? |
|---|---|
| Subject | No — no identity on the wire |
| Action | Yes — tool name, class, policy status, rarity |
| Time | No — timestamps are invented |
| Environment | No |
| Session | No — each `run_id` holds one label |
| Outcome | No — 2 errors in 3,000 calls, responses cut at 280 characters |
| Protocol | No — not captured for the live servers |
| Population | Partly — tool frequency only |

What would change that: run the live corpus through the mitm proxy, which already records
real timestamps, session ids, headers, full responses and protocol events
(`logs/proxy/scripts/run_mitm_finance.py`), with several callers identified by header and
benign and misuse calls mixed inside the same sessions. Do not synthesize timing: the
generator would decide the answer.

## Where to start

1. **Subject and scope rules** — the only input-free context with a strong MCP evaluation.
2. **Tool policy status** — already written in Table 4.
3. **Time and session rules from the policy** — unevaluated, but input-free, unforgeable by
   the agent, and easy to explain.
4. **Learned contexts** (rarity, sequence, population) — a small multiplier at most; all are
   poisonable.

## References

Read depth varies: numbers quoted from method sections came through a summarizer and should
be checked against the PDF before citing. All arXiv IDs were re-fetched and their titles
match.

- NIST SP 800-162 — *Guide to Attribute Based Access Control (ABAC) Definition and Considerations*.
- [2412.16682](https://arxiv.org/abs/2412.16682) — The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection in LLM Agents.
- [2502.05174](https://arxiv.org/abs/2502.05174) — MELON: Provable Defense Against Indirect Prompt Injection Attacks in AI Agents.
- [2503.18813](https://arxiv.org/abs/2503.18813) — Defeating Prompt Injections by Design.
- [2504.08623](https://arxiv.org/abs/2504.08623) — Enterprise-Grade Security for the Model Context Protocol (MCP): Frameworks and Mitigation Strategies.
- [2504.12757](https://arxiv.org/abs/2504.12757) — MCP Guardian: A Security-First Layer for Safeguarding MCP-Based AI System.
- [2505.03574](https://arxiv.org/abs/2505.03574) — LlamaFirewall: An open source guardrail system for building secure AI agents.
- [2505.14590](https://arxiv.org/abs/2505.14590) — MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol.
- [2505.23643](https://arxiv.org/abs/2505.23643) — Securing AI Agents with Information-Flow Control.
- [2508.20412](https://arxiv.org/abs/2508.20412) — MindGuard: Intrinsic Decision Inspection for Securing LLM Agents Against Metadata Poisoning.
- [2510.19462](https://arxiv.org/abs/2510.19462) — AegisMCP: Online Graph Intrusion Detection for Tool-Augmented LLMs on Edge Devices.
- [2511.20920](https://arxiv.org/abs/2511.20920) — Securing the Model Context Protocol (MCP): Risks, Controls, and Governance.
- [2603.07473](https://arxiv.org/abs/2603.07473) — Give Them an Inch and They Will Take a Mile: Understanding and Measuring Caller Identity Confusion in MCP-Based AI Systems.
- [2603.16928](https://arxiv.org/abs/2603.16928) — Noticing the Watcher: LLM Agents Can Infer CoT Monitoring from Blocking Feedback.
- [2604.04035](https://arxiv.org/abs/2604.04035) — Causality Laundering: Denial-Feedback Leakage in Tool-Calling LLM Agents.
- [2604.11806](https://arxiv.org/abs/2604.11806) — Detecting Safety Violations Across Many Agent Traces.
- [2604.26274](https://arxiv.org/abs/2604.26274) — Enforcing Benign Trajectories: A Behavioral Firewall for Structured-Workflow AI Agents.
- [2605.01143](https://arxiv.org/abs/2605.01143) — A Low-Latency Fraud Detection Layer for Detecting Adversarial Interaction Patterns in LLM-Powered Agents.
- [2605.11026](https://arxiv.org/abs/2605.11026) — AgentShield: Deception-based Compromise Detection for Tool-using LLM Agents.
- [2605.11053](https://arxiv.org/abs/2605.11053) — Content-Aware Attack Detection in LLM Agent Tool-Call Traffic: An Empirical Study of Features, Architectures, and Evaluation Protocols.
- [2605.11360](https://arxiv.org/abs/2605.11360) — Options, Not Clicks: Lattice Refinement for Consent-Driven MCP Authorization.
- [2605.17380](https://arxiv.org/abs/2605.17380) — ADR: An Agentic Detection System for Enterprise Agentic AI Security.
- [2605.18414](https://arxiv.org/abs/2605.18414) — Prompts Don't Protect: Architectural Enforcement via MCP Proxy for LLM Tool Access Control.
- [2605.22333](https://arxiv.org/abs/2605.22333) — A First Measurement Study on Authentication Security in Real-World Remote MCP Servers.
- [2606.19386](https://arxiv.org/abs/2606.19386) — Bistable by Construction: Wall-Clock-Calibrated State Monitors Have No Moment-Detection Regime at Agent Cadence.
- [2606.30566](https://arxiv.org/abs/2606.30566) — Retrieval Observability Bounds on Provenance Detection for Agent Memory Poisoning: Measured Coverage and a Falsified Standalone Detector.
- [2607.19432](https://arxiv.org/abs/2607.19432) — ChainWatch: A Kill Chain-Aligned Sequential Detection Framework for Multi-Step Attacks in MCP-Based AI Agent Systems.
- [2608.23763](https://arxiv.org/abs/2608.23763) — TrustShiftProbe: Characterizing, Benchmarking, and Defending Staged Trust Attacks on MCP Servers.
- [2609.14780](https://arxiv.org/abs/2609.14780) — The Stochastic Deputy: Structural Tenant Isolation for Tool-Using LLM Agents.
- [2609.19091](https://arxiv.org/abs/2609.19091) — When Agents Look Like Beacons: NIDS Evasion by Model Context Protocol Traffic.
- [2609.23498](https://arxiv.org/abs/2609.23498) — Runtime Authorization Consistency Checking for MCP-based Agentic Workflows.
