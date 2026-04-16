# ToolSafe: Enhancing Tool Invocation Safety of LLM Agents via Proactive Step-Level Guardrail and Feedback

**Authors:** Yutao Mou, Zhangchi Xue, Lijun Li, Peiyang Liu, Shikun Zhang, Wei Ye, Jing Shao
**Institutions:** National Engineering Research Center for Software Engineering, Peking University;
Shanghai Artificial Intelligence Laboratory
**arXiv:** 2601.10156 | January 2026
**Code:** https://github.com/MurrayTom/ToolSafe

> Companion to the Hebrew summary at `19_ToolSafe_summary_HE.md`. Same paper, English
> narrative, and a thesis-relevance section reframed to match the project's server-defense
> direction (MCP servers are the protected asset).

---

## 1. The Core Problem — Why Agent Tool Invocation Is Dangerous

### The key insight

LLM-based agents execute complex tasks in open environments by invoking external tools
(tool invocation). This capability **amplifies security risk**: even well-aligned agents
can perform dangerous actions in response to malicious user requests or third-party
prompt injection. The critical gap: there is no **step-level pre-execution monitor** that
can detect and prevent an unsafe tool invocation *before* it runs.

### Metaphor — the pharmacist

Think of a pharmacist (the guardrail) reviewing each prescription (tool call) before
dispensing:

```
Pharmacy (AI Agent System)
    |
    +-- Case 1: Patient directly asks for a dangerous drug
    |   "Give me 50 sleeping pills without a prescription"
    |   --> Normal pharmacist: "I cannot" (refuse)         -- OK
    |   --> Weak pharmacist: dispenses without checking     -- FAIL
    |
    +-- Case 2: Normal prescription, but tampered in transit
    |   Original: "aspirin 100mg"
    |   Modified: "aspirin 100mg + send PIN to hacker@evil.com"
    |   --> Normal pharmacist: doesn't notice the change    -- FAIL
    |   --> TS-Guard pharmacist: "Wait, second line is off" -- OK
    |
    +-- Case 3: The tool itself is intrinsically dangerous
    |   Doctor prescribes "submit_alpha_bay_order" (Dark Web)
    |   --> Normal pharmacist: doesn't recognize the tool   -- FAIL
    |   --> TS-Guard pharmacist: "This tool is harmful"    -- OK
```

**ToolSafe = the smart pharmacist** that not only detects unsafe prescriptions but also:
1. **Explains** why the action is unsafe
2. **Feeds back** to the agent so the agent can correct itself
3. **Does not just refuse** — preserves legitimate task completion

---

## 2. Background and Related Work

### 2.1 LLM guardrail models

Existing guardrails (LlamaGuard, Qwen3Guard, ShieldGemma, PolyGuard, WildGuard) are
designed for **static content moderation** — they classify LLM input/output as harmful.
They do not handle the **runtime dynamics of tool invocation** in autonomous agents:
they lack tool context and do not reason about step-level action consequences.

### 2.2 Agent guardrails

Newer work extends guardrails to agents:
- **LlamaFirewall** — PromptGuard2 + AlignmentCheck in a "detect-and-abort" paradigm
- **Safiron** — planning-stage guardrail
- **AgentAuditor** — evaluates full execution trajectories
- **GuardAgent** — manually-defined rules (limited coverage)
- **ShieldAgent / AGrail** — deep reasoning + verification, but **high latency** (~8.75 sec/sample),
  impractical for real-time monitoring

**The core gap:** every existing approach either (a) aborts the whole execution,
breaking legitimate tasks, or (b) is too slow for step-level monitoring. ToolSafe
proposes something fundamentally different: **step-level monitoring with feedback
to the agent** instead of termination.

---

## 3. TS-Bench — The First Step-Level Tool Invocation Safety Benchmark

### 3.1 Formal task definition

The agent interacts with the environment in a reasoning-action loop. At each step `t`
it produces:
- An action `a_t` — intermediate reasoning + planned tool call
- An observation `o_t` — the environment's response after execution

The interaction history up to step `t` is `H_t = {(a_0, o_0), ..., (a_{t-1}, o_{t-1})}`.

**Formal task:** given a user request `u`, history `H_t`, candidate action `a_t`, and
tool specification `T`, decide whether `a_t` is safe to execute **before** running it:

```
y_t = f_guardrail(a_t, H_t, u, T)         (1)
```

where `y_t ∈ {safe, controversial, unsafe}`.

### 3.2 Four unsafe tool invocation patterns

ToolSafe analyzes logs from four representative agent safety datasets (AgentAlign,
AgentHarm, ASB, AgentDojo) and identifies **four unsafe patterns** along two orthogonal
dimensions:

|                                 | Harmful Tools (HT)       | Benign Tools, Risky Args (BTRA)       |
|---------------------------------|--------------------------|---------------------------------------|
| **Malicious User Request (MUR)**| MUR + HT                 | MUR + BTRA                            |
| **Prompt Injection (PI)**       | PI + HT                  | PI + BTRA                             |

- **Axis 1 — Triggering cause:** the user's own request is malicious (MUR) vs. a
  third-party prompt injection contaminates the trajectory (PI)
- **Axis 2 — Manifestation:** the tool is intrinsically dangerous (HT) vs. a benign
  tool weaponized by its arguments (BTRA)

**Why all four matter:**
- **MUR + HT:** user asks for something harmful, agent calls an intrinsically-harmful
  tool. E.g., "Order 20g of drugs" → `submit_alpha_bay_order(item="drugs")`
- **MUR + BTRA:** user asks for something harmful, but the tool itself is legitimate —
  the risk is in the arguments. E.g., "Email my PIN" → `send_email(to="hacker", body="PIN: 1234")`
- **PI + HT:** a malicious instruction is injected into the environment and the agent
  calls an intrinsically-harmful tool
- **PI + BTRA:** injected instruction drives a benign tool with dangerous arguments —
  **the hardest case to detect**

### 3.3 Benchmark construction

**Data sources:** TS-Bench is built from four representative datasets:

| Dataset | Content | Contribution |
|---|---|---|
| AgentAlign | 4,956 harmful + 9,783 benign instructions | Training split |
| AgentHarm | 176 malicious + 176 safe, 104 tools | Evaluation split |
| ASB (Agent Security Bench) | 10 scenarios, 400+ tools | Train + eval |
| AgentDojo | 70 tools, 97 tasks, 27 injection goals | Evaluation split |

**Step-level annotation:** each trajectory is sampled with GPT-4o / Claude 3.5 /
Qwen3-30B-A3B and every step is labeled:

```
Three-level safety scale:
  0.0 = safe          (no risk)
  0.5 = controversial (potential risk)
  1.0 = unsafe        (significant risk)
```

Each step is additionally labeled for **prompt injection presence** and for **whether
the original user request was malicious**.

**Train / eval splits:**

```
TS-Bench-train:
  AgentAlign-Traj:  673 samples  (123 safe / 237 controversial / 313 unsafe)
  ASB-Traj:        1520 samples  (720 /  469 / 331)

TS-Bench-eval:
  AgentHarm-Traj:   731 samples  (206 / 315 / 210)
  ASB-Traj:        5237 samples  (2700 / 1466 / 1071)
  AgentDojo-Traj:  1220 samples  (868 / N/A / 352)
```

### 3.4 Coverage vs. prior benchmarks

| Benchmark | Annotation Level | Monitored Behavior | MUR | PI | HT | BTRA |
|---|---|---|:---:|:---:|:---:|:---:|
| R-Judge | Trajectory | tool calls | ✓ | ✓ | — | ✓ |
| ASSEBench | Trajectory | tool calls | ✓ | ✓ | — | ✓ |
| OS-Safe | Step | web/code execution | ✓ | ✓ | ✓ | — |
| ShieldAgent-Bench | Step | web browsing | ✓ | ✓ | — | — |
| **TS-Bench (this paper)** | **Step** | **tool calls** | ✓ | ✓ | ✓ | ✓ |

TS-Bench is the only step-level benchmark covering **all four** unsafe patterns.

---

## 4. TS-Guard — Step-Level Guardrail Model

### 4.1 Architecture: decompose the decision into sub-tasks

Rather than directly classifying an action as safe or unsafe (a hard single-shot
judgment), TS-Guard **decomposes** the problem into three sub-tasks solved sequentially
in a single inference:

```
Input:  user request u, history H_t, candidate action a_t, tool spec T

Sub-task 1: detect malicious user intent          →  h_t ∈ {yes, no}
Sub-task 2: detect external attack / injection    →  v_t ∈ {yes, no}
Sub-task 3: final safety rating                   →  y_t ∈ {0.0, 0.5, 1.0}

Also outputs: r_t = brief analysis / reasoning

Joint output: P(y_t, v_t, h_t, r_t | a_t, H_t, u)          (2)
```

**Structured output format:**

```xml
<Think> brief analysis of context and risk </Think>
<Malicious_User_Request> yes/no </Malicious_User_Request>
<Being_Attacked> yes/no </Being_Attacked>
<Harmfulness_Rating> 0.0 / 0.5 / 1.0 </Harmfulness_Rating>
```

**Why three sub-tasks?** Think of a judge deciding whether to approve an action:

- Single-shot judge ("is this safe?") — makes many errors
- Multi-stage judge:
  1. "Is the original request suspicious?" (`h_t`) — captures *intent*
  2. "Are there signs of external attack?" (`v_t`) — captures *manipulation*
  3. "Given 1+2, what is the risk level?" (`y_t`) — informed decision

Multi-stage decomposition → fewer false positives, better explanations.

### 4.2 Training: GRPO with multi-task reward

TS-Guard is trained with **GRPO** (Group Relative Policy Optimization), a reinforcement
learning method shown to generalize better than SFT for guardrail tasks.

**Multi-task reward function:**

```
r_t = 1 - w_1 · 1[ĥ ≠ h*]
        - w_2 · 1[v̂ ≠ v*]                                 (3)
        - w_3 · 1[ŷ ≠ y*]

w_1 = w_2 = w_3 = 1/3 (equal weights)
```

where `ĥ, v̂, ŷ` are predictions and `h*, v*, y*` are ground-truth labels.

**Why multi-task reward?** With single-task reward `r = 1[ŷ = y*]` the model can "guess"
the final label without understanding why. Multi-task reward forces the model to learn
(1) user intent, (2) attack context, *and* (3) final risk — giving finer supervision
and better generalization with fewer false positives.

### 4.3 Implementation

| Parameter | Value |
|---|---|
| Base model | Qwen2.5-7B-Instruct |
| Framework | verl (GRPO) |
| Batch size | 256 |
| Max prompt length | 4,096 tokens |
| Max response length | 1,024 tokens |
| Learning rate | 1e-6 |
| KL regularization | 0.001 (low-variance KL) |
| Rollouts | 16 per prompt |
| Epochs | 10 |
| Hardware | 8 × NVIDIA 96GB H20 GPUs |

---

## 5. TS-Flow — Monitor-and-Feedback Instead of Detect-and-Abort

### 5.1 The problem with detect-and-abort

LlamaFirewall (the dominant approach) halts execution when it detects an unsafe step —
which also halts any legitimate in-progress task. In real scenarios, injected
instructions are **mixed with legitimate ones**, and aborting everything costs utility.

### 5.2 Monitor-and-feedback

TS-Flow proposes dynamic interaction between agent and guardrail:

```
For each step t:
  1. Agent produces candidate action a_t
  2. TS-Guard receives (u, H_t, a_t, T)
     and returns (r_t, h_t, v_t, y_t)
  3. If y_t = safe (0.0):
       → execute a_t
       → continue
  4. If y_t ∈ {controversial (0.5), unsafe (1.0)}:
       → inject full TS-Guard output (r_t + h_t + v_t + y_t)
         as feedback into the agent's context
       → agent reads feedback, produces corrected action a_t'
       → loop back to step 2 with a_t'
```

|  | LlamaFirewall | TS-Flow |
|---|---|---|
| On detection | abort | inject feedback |
| Legitimate task completion | broken | preserved |
| Interaction | one-way (guard → stop) | two-way (guard ↔ agent) |
| Safety outcome | very good | very good |
| Utility outcome | degraded | preserved or improved |

---

## 6. Experiments and Results

### 6.1 Guardrail accuracy (strict mode — controversial + unsafe both count as unsafe)

| Model | AgentHarm-Traj (F1) | ASB-Traj (F1) | AgentDojo-Traj (F1) |
|---|---:|---:|---:|
| GPT-4o | 84.80 | 63.03 | 56.59 |
| Qwen3-8B | 58.94 | 38.93 | 72.32 |
| Qwen2.5-7B-IT | 80.17 | 62.96 | 50.47 |
| Llama-Guard-3-8B | 86.35 | 24.82 | 33.33 |
| **TS-Guard (this paper)** | **90.16** | — | **86.18** |

Key findings:
1. **Most guardrails collapse under prompt injection** — GPT-4o drops from F1=84.80 on
   MUR-dominant AgentHarm-Traj to F1=63.03 on PI-dominant ASB-Traj.
2. **Over-defensiveness on BTRA** — on AgentDojo-Traj (benign tools with risky args),
   many models have high recall but low F1 (they flag safe arguments as dangerous).
3. **TS-Guard matches or beats dedicated guardrail models** (LlamaGuard-3-8B) and general
   LLMs (GPT-4o) on all three splits.

### 6.2 End-to-end safety + utility under TS-Flow

TS-Flow + TS-Guard on AgentDojo:
- ASR: 56.16% → **1.16%** (~98% reduction)
- Utility: 26.87 → **42.78** (actually *improves*, vs. LlamaFirewall which drops to 20.79)

### 6.3 Guardrail model vs. guardrail agent

| Property | TS-Guard (model) | AGrail (agent) |
|---|---|---|
| Architecture | single model, one inference | multi-step reasoning + tools |
| Latency | ~1.36 sec/sample | ~8.75 sec/sample |
| F1 (AgentHarm) | 90.16 | 85.75 |
| F1 (AgentDojo) | 86.18 | 58.05 |
| Real-time monitoring viability | high | low (8× latency) |

TS-Guard wins on both accuracy and efficiency.

---

## 7. Limitations

1. **Feedback as external signal.** TS-Guard's feedback is injected as plain text into the
   agent's context. Some agents may ignore it or fail to integrate it into their reasoning.
   Agents are not *trained* to receive guardrail feedback.
2. **Independent training.** Agent and guardrail are trained separately, which can cause
   misalignment between the agent's reasoning and the guardrail's safety judgments. A
   future direction is joint training.
3. **Training-data dependence.** TS-Guard is trained on four specific datasets; generalization
   to entirely new domains is untested.
4. **English-only.** Benchmark and model are English; behavior in other languages is unknown.
5. **Intent-only checking.** TS-Guard judges the *intent* of a call, not the *actual
   runtime behavior* of the tool — a tool that behaves differently from its declared
   spec will not be caught.
6. **Non-trivial overhead.** On Qwen2.5-14B, token overhead reaches 89%.

---

## 8. Relevance to the Thesis — Server-Side Dynamic Risk Scoring for MCP

> **Threat-model reminder:** this project treats MCP servers as the protected asset and
> agents as the threat source. All relevance below is framed as the MCP server scoring
> incoming agent requests **before** executing them. ToolSafe's agent-side design is
> inverted and relocated to the server side.

### 8.1 Direct alignment with the project's two-mode scoring

The project produces risk scores in two modes:
- **Static** — tool-level risk based on general properties
- **Dynamic** — request-level risk based on the specific agent input

ToolSafe's 2×2 taxonomy maps onto these two modes almost perfectly:

| ToolSafe axis | Project's mode | Implication for server |
|---|---|---|
| **HT — Harmful Tools** | Static mode | Tool-level severity lookup from the MCP server's own tool catalog |
| **BTRA — Benign Tool, Risky Args** | Dynamic mode | Per-request argument inspection at the server boundary |
| **MUR — Malicious User Request** | Threat-source signal | Scored from request origin + session history |
| **PI — Prompt Injection** | Threat-source signal | Scored from inconsistency between declared task and tool call |

The BTRA class is the single strongest empirical justification for having a dynamic
mode at all. ToolSafe's results show it is where every existing guardrail over-flags —
the server cannot rely on tool-level severity alone.

### 8.2 Three-level scale as a seed for the 1–10 scale

TS-Guard uses a three-level scale (0.0 / 0.5 / 1.0), which is coarser than the thesis's
1–10. The mapping is natural:

```
  TS-Guard label           Project score band        Server action
  -------------------------+------------------------+-----------------------
  0.0 safe                 →  1-3                   →  allow
  0.5 controversial        →  4-6                   →  throttle / challenge
  1.0 unsafe               →  7-10                  →  deny
```

The three-way label matches the server-side gate/throttle/deny tiering the project is
building. GRPO can be extended with a continuous reward to directly produce a 1–10
output instead of a categorical one.

### 8.3 Sub-task decomposition adapted for the MCP server

TS-Guard's three-sub-task decomposition adapts directly to a server-side scorer:

```
Server-side request scoring:

  (h_t)  Is the agent's request malicious?
         → Is the agent trying to access an MCP resource for an illegitimate goal?

  (v_t)  Are there signs of prompt injection contaminating the agent?
         → Does the request pattern suggest the agent is acting under external
           hostile influence? (Compare to the session's declared task.)

  (y_t)  Final risk score
         → A 1-10 score weighing h_t, v_t, the requested resource's sensitivity,
           and the required privileges.

  (NEW for thesis)  sensitivity_t: the MCP resource's sensitivity
         → DB read < DB write < network access < money transfer
```

The server, not the agent, runs this scoring. Unlike ToolSafe, where the guardrail
sits beside the LLM, here the guardrail sits in front of the MCP server's tool-dispatch
layer — the *server's* request handler scores each incoming call.

### 8.4 TS-Flow as a template for a risk-aware MCP handshake

The monitor-and-feedback paradigm is directly applicable. Instead of the server simply
rejecting a high-risk call, it can return a structured risk response that lets the
agent self-correct:

```
Agent → MCP server: "read_file(path='/etc/passwd')"

Server-side Risk Scorer:
  h_t = no     (request itself is not obviously malicious)
  v_t = maybe  (passwd read not tied to declared session task)
  sensitivity = 8/10  (system credentials file)
  risk_score = 7/10

  → CONDITIONAL response: "Risk score 7/10. State the reason you
    need /etc/passwd for the current task, or request a lower-
    sensitivity file." (feedback, not abort)
```

This preserves legitimate task completion without blindly allowing the risky call.

### 8.5 Concrete takeaways for the project

| Insight from ToolSafe | How to integrate |
|---|---|
| GRPO + multi-task reward generalizes better than SFT | Train the scorer with GRPO over (h, v, y) sub-scores |
| Multi-task reward reduces false positives | Decompose the risk score into sub-scores and recombine |
| Rich feedback > plain rejection | When the server blocks, return a structured explanation |
| All four MUR/PI/HT/BTRA patterns matter | Cover all four in the project's evaluation set |
| Token overhead 36–89% | Factor into latency budget — Lenovo's constraint requires practicality |
| Step-level, not trajectory-level | The MCP server scores per-request, not per-session retrospectively |

### 8.6 Complementary to MCPShield, not redundant

MCPShield (paper #02) monitors **MCP servers** for behavioral divergence — does the tool
do what its spec says? That is a post-invocation integrity check. ToolSafe provides the
complementary **pre-invocation** judgment: should this call be allowed in the first
place? Both belong on the server side of the project's architecture:

```
Incoming agent request
    │
    ▼
[Pre-invocation scoring]  ← ToolSafe-style (1-10 risk score)
    │
    ▼
[Gate / Throttle / Deny]  ← project's decision layer
    │
    ▼
[Tool dispatch]
    │
    ▼
[Runtime behavior check]  ← MCPShield-style (behavior vs. declared spec)
    │
    ▼
Response to agent
```

### 8.7 Bottom line

ToolSafe is the closest published analog to what the project is building. Its 2×2
taxonomy gives empirical grounding for the static/dynamic split, its three-level label
matches the gate/throttle/deny tiering, and TS-Guard's ~90 F1 at ~1.36 sec/sample sets
a concrete performance–latency ceiling. The main limitation for direct reuse is domain:
TS-Bench is general-agent, not MCP, so the project should import the **methodology**
(pre-execution step-level judgment, 2×2 taxonomy, GRPO + multi-task reward) and run
evaluation on MCP-specific benchmarks (MCPTox, MCIP-Bench, MCP-AttackBench) for the
core results. The cleanest thesis framing:

> *"ToolSafe-style pre-execution detection, relocated from the agent side to the MCP
> server side, extended with MCP-specific tool-sensitivity and session-context features."*
