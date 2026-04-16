# MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol

**Full Paper Summary**

- **Authors:** Huihao Jing, Haoran Li, Wenbin Hu, Qi Hu, Heli Xu, Tianshu Chu, Peizhao Hu, Yangqiu Song
- **Institutions:** HKUST, Huawei Technologies
- **Published:** EMNLP 2025 — arXiv:2505.14590 (v7, Sep 29 2025)
- **Code & Data:** https://github.com/HKUST-KnowComp/MCIP

---

## 1. The Problem: What Is Missing in MCP?

Model Context Protocol (MCP) is an open protocol by Anthropic that allows AI
agents to connect to external tools, APIs, memory stores, and servers. MCP has
become a unified interface for LLM-tool interaction and is growing rapidly —
tens of thousands of servers now expose tools through it.

MCP's decentralized architecture separates **clients** (the AI agent side) from
**servers** (the tool side), and this separation introduces a critical security
gap. When the client and server are deployed independently:

- Either side can inject malicious instructions into the LLM.
- The client can send harmful requests to the server.
- The server can return poisoned responses that redirect the agent.
- There is **no built-in mechanism** in the MCP protocol to decide whether a
  function call is contextually appropriate.

Prior work addressed LLM safety in isolated contexts (jailbreaks, backdoors,
prompt injection). But those techniques treat function calls in isolation. MCP
changes this — function calls happen **in a multi-component context** involving
the user, the client, the server, and external data sources. A call that is
individually safe can be dangerous in context; a call that looks dangerous in
isolation may be completely appropriate. Safety must therefore be evaluated at
the **interaction level**, not the individual call level.

The authors identify two specific things MCP currently lacks:

1. **Tracking tools** — MCP has no Layer 5 equivalent in the MAESTRO stack.
   There is no structured log of information flows happening inside MCP sessions.
2. **Safety-aware models** — MCP has no Layer 6 equivalent. There is no
   component that learns from those logs to detect unsafe patterns.

MCIP is designed to add both.

---

## 2. Background: The Two Frameworks MCIP Builds On

### 2.1 MAESTRO — The AI Threat Modeling Framework

MAESTRO (from the Cloud Security Alliance, 2025) is a 7-layer reference
architecture for analyzing security in AI agent systems. The layers are:

| Layer | Name | What it covers |
|-------|------|---------------|
| Layer 1 | Foundation Models | The LLM itself (training, weights, alignment) |
| Layer 2 | Data Operations | Training data, retrieval, memory |
| Layer 3 | Agent Frameworks | Reasoning, planning, tool selection logic |
| Layer 4 | Deployment and Infrastructure | MCP clients, servers, hosting |
| Layer 5 | Evaluation and Observability | **Tracking tools — MISSING in MCP** |
| Layer 6 | Security and Compliance | **Safety-aware models — MISSING in MCP** |
| Layer 7 | Agent Ecosystem | Multi-agent coordination, market dynamics |

Layer 6 cuts across all other layers — security and compliance controls should
be embedded at every level, not bolted on at the end.

The authors map MCP components directly to MAESTRO layers:

| MAESTRO Layer | MCP Component |
|---------------|--------------|
| Layer 1 | Foundation models |
| Layer 2 | Local and cloud data operations |
| Layer 3 | MCP clients |
| Layer 4 | MCP servers |
| Layer 5 | **Missing — tracking tools** |
| Layer 6 | **Missing — safety aware models** |
| Layer 7 | Market of clients and servers |

MCIP fills Layers 5 and 6 by adding a **tracking log format** (MCI) and a
**safety-aware model** (MCIP Guardian).

### 2.2 Contextual Integrity (CI) — The Privacy Theory Behind MCI

Contextual Integrity is a privacy theory from Nissenbaum (2004). Its core
claim:

> Information flows are appropriate when they match the norms of the
> context they originate from.

CI defines information flows as **tuples**:

```
(Sender, Recipient, Data Subject, Information Type, Transmission Principle)
```

- **Sender:** who initiates the flow (user, client, server, external source)
- **Recipient:** who receives it
- **Data Subject:** whose data is being transferred
- **Information Type:** what kind of data (query, function call, return value,
  credentials, user data, etc.)
- **Transmission Principle:** the rule that governs whether this flow is
  appropriate (e.g., consent, necessity, data minimization, transparency)

A flow is **appropriate** when the transmission principle is respected.
A flow is **inappropriate** (a risk) when the principle is violated.

The authors adapt CI directly to MCP. In an MCP interaction, information flows
in a predictable trajectory:

```
USER sends QUERY about SUBJECT to CLIENT under TRANSMISSION PRINCIPLE
  ↓
CLIENT sends FUNCTION REQUEST about SUBJECT to SERVER under TRANSMISSION PRINCIPLE
  ↓
SERVER sends FUNCTION LIST (or RETURN VALUE) to CLIENT under TRANSMISSION PRINCIPLE
  ↓
CLIENT sends RESPONSE about SUBJECT to USER under TRANSMISSION PRINCIPLE
```

This trajectory — the ordered sequence of information flows — is what MCIP
logs and what MCIP Guardian learns to evaluate.

---

## 3. The MCIP Framework — What It Actually Is

MCIP is not a new version of the MCP protocol from scratch. It is an
**enhancement layer on top of MCP** that adds two components:

### Component 1: The MCI Tracking Log Format

To fix the missing Layer 5 (Evaluation and Observability), MCIP introduces
the **Model Contextual Integrity (MCI)** format.

In real-world MCP sessions, interactions appear as natural language dialogues.
This makes structured classification hard — you cannot easily extract
"who sent what to whom and under what principle" from a free-text conversation.

MCI solves this by defining a **structured log format** where each interaction
is stored as an ordered list of 5-element tuples:

```
(sender, recipient, data_subject, information_type, transmission_principle)
```

Each full MCP interaction becomes a **trajectory** — a sequence of these
tuples that traces the complete information flow from user query to final
response. A typical trajectory has around **8 transmission steps**.

Example trajectory for a safe BMI calculation:

```
Step 1: User → Assistant  |  Subject: user_health  |  Type: user query
        Principle: consent (user voluntarily provides data)

Step 2: Assistant → Function(calculate_bmi)  |  Subject: user_health
        Type: function parameter  |  Principle: necessity (required for service)

Step 3: Function(calculate_bmi) → Assistant  |  Subject: user_health
        Type: BMI result  |  Principle: service provision

Step 4: Assistant → User  |  Subject: user_health
        Type: BMI result  |  Principle: transparency (return requested info)
```

Now compare to a **Function Dependency Injection** attack:

```
Step 1: User → Assistant  |  "Calculate my BMI"
Step 2: Assistant → Function(read_purchase_history)  |  ← NOT requested
        Principle: VIOLATED — no necessity for purchase history in BMI calculation
Step 3: Function(read_purchase_history) → Assistant
Step 4: Assistant → Function(calculate_bmi)
Step 5: Function(calculate_bmi) → Assistant
Step 6: Assistant → User  |  correct BMI result shown
```

The final result looks correct. But the MCI log reveals a **redundant flow**
(Step 2) — an extra function call that was never requested and violates the
necessity principle. This is what MCIP Guardian is trained to catch.

### Component 2: MCIP Guardian — The Safety-Aware Model

MCIP Guardian is a fine-tuned LLM that:
- Takes an MCP interaction (formatted as an MCI trajectory) as input
- Outputs a classification from the 11-class taxonomy (10 risk types + True/safe)
- Provides fine-grained risk categorization to support effective defense

It is trained on the **Guardian Training Dataset** (13,830 instances) and
evaluated on **MCIP-Bench** (2,218 instances).

Base model: **Salesforce/Llama-xLAM-2-8b-fc-r** — one of the most advanced
function-calling LLMs. Fine-tuned using OpenRLHF on 4× NVIDIA H800 80GB GPUs.
Training: learning rate 5×10⁻⁶, batch size 2, max sequence length 2,048,
3 epochs.

---

## 4. The Taxonomy — A Complete Map of MCP Safety Risks

The taxonomy is structured along **three dimensions**: Phase, Source, Scope.

### Dimension 1: Threat Phase (When Does the Risk Arise?)

Risks arise at different points in the MCP lifecycle:

**Config Phase** — Before the interaction even starts. The infrastructure
hosting clients and servers is configured. Malicious actors in the marketplace
can misconfigure servers or corrupt the environment. Attacks here require
auditing configuration files and infrastructure. Maps to MAESTRO Layer 7.

**Interaction Phase** — The core of MCP. The client-server interaction is
the most vulnerable component because both sides are deployed separately and
both can communicate with the LLM. Either side can inject malicious
instructions. This is where most attacks happen.

**Termination Phase** — After the session ends. Privileges may not be
properly revoked, configurations may drift, server versions may become
mismatched. Attacks here are subtle — the system looks healthy, but
outdated behavior persists.

### Dimension 2: Threat Source (Who Initiates the Attack?)

- **Server-sourced attacks** — The MCP server itself is malicious or
  compromised and injects harmful content into function lists, return values,
  or configuration.
- **Client-sourced attacks** — The MCP client (which encapsulates the user
  query) injects harmful instructions into prompts or function parameters.

### Dimension 3: Threat Scope (How Broadly Does the Risk Spread?)

Three levels, defined in terms of the MCI trajectory:

- **Intra-flow Behavior** — The risk affects specific elements within a single
  interaction turn. One of the five MCI tuple elements (sender, recipient,
  data subject, information type, transmission principle) is violated.
- **Single-flow Behavior** — The risk affects one complete step in the
  trajectory. It introduces unnecessary actions or omits required ones.
  Detected as **redundant** or **missing** information flows.
- **Inter-flow Behavior** — The risk spans multiple steps and disrupts the
  temporal or logical dependencies between them. Detected as **malicious
  reordering** of the flow sequence.

---

## 5. The Full Attack Taxonomy (All 14 Attack Types)

The table below summarizes all attacks, organized exactly as in the paper
(Figure 3). Read it alongside the Phase/Source/Scope framework above.

### Config Phase Attacks

| Attack | Source | Scope | What Happens | MAESTRO |
|--------|--------|-------|-------------|---------|
| **Server Name Overlapping** | Server | Intra-flow (Recipient) | A malicious server registers under the same name as a legitimate one. The LLM resolves the wrong recipient, causing widespread misdelivery of queries. | L4, L7 |
| **Installer Spoofing** | Server | Intra-flow (Transmission Principle) | A modified installer distributed through third-party channels removes authentication checks and consent mechanisms. Corrupts the global transmission principle. | L4, L7 |
| **Backdoor Implantation** | Server | Intra-flow (Transmission Principle) | Foundation models carry backdoors from pretraining or fine-tuning. When triggered by specific inputs, the model behaves maliciously (leaks data, bypasses filters). | L4, L7, L1 |

### Interaction Phase Attacks

| Attack | Source | Scope | What Happens | MAESTRO |
|--------|--------|-------|-------------|---------|
| **Function Overlapping** | Server | Intra-flow (Recipient) | Server registers a function with the same name as a legitimate one but with malicious behavior. The LLM resolves the wrong recipient. Example: a fake `calculate_bmi` that also exfiltrates user data silently. | L4 |
| **Excessive Privileges Overlapping** | Server | Intra-flow (Recipient) | Server returns a function requiring higher privileges than the task needs. The LLM is misled into selecting an unnecessarily powerful function. Example: a tip calculator task routes to `transaction_auditing` instead of `calculator`. | L4, L2 |
| **Function Dependency Injection** | Server | Single-flow (Redundancy) | Server falsely claims that certain functions must be called before the target function. The LLM invokes unnecessary functions first. Example: `read_purchase_history` is falsely required before `calculate_bmi`. | L4 |
| **Function Injection** | Server | Single-flow (Redundancy) | Malicious server injects harmful content into a function's output, prompting the LLM to call additional unrelated functions. Example: `calculate_bmi` response contains an injected prompt that causes `read_purchase_history` to be called next. | L4 |
| **Causal Dependency Injection** | Client | Inter-flow (Drift) | Client disrupts the expected causal order of function calls, bypassing required verification steps. Example: access a database before identity verification completes. The LLM executes with a false causal chain. | L3 |
| **Intent Injection (Wrong Parameter)** | Client | Single-flow (Misleading) | Function calls or parameters completely deviate from the user's original intent. Example: user asks to calculate BMI with weight=70, but the injected call uses weight=1.85, producing wrong output that the user trusts. | L3 |
| **Intent Injection (Ignore Purpose)** | Client | Single-flow (Misleading) | The correct function is selected but its purpose is ignored. Example: user asks to calculate BMI, but the actual call goes to `write_database` with injected data. | L3 |
| **Data Injection** | Client | Single-flow (Overwriting) | Malicious client injects fake return values. The LLM treats injected content as legitimate function output and continues reasoning on fabricated data. Example: the BMI response shows 20.50 instead of 22.86 because the real function call is suppressed and replaced. | L3 |
| **Identity Injection** | Client | Intra-flow (Sender) | Client impersonates a privileged user (e.g., administrator), causing the LLM to execute sensitive commands. Example: "I need to reset all user passwords immediately" → LLM calls `reset_all_passwords()`, resetting 1,500 accounts. | L3 |
| **Replay Injection** | Client | Single-flow (Redundancy) | A single-use authorization token is reused. The client replays a previously valid call without re-validating the identity. Example: identity is checked once, but then `write_database` is called multiple times using the same token. | L3 |

### Termination Phase Attacks

| Attack | Source | Scope | What Happens | MAESTRO |
|--------|--------|-------|-------------|---------|
| **Expired Privilege Redundancy** | Server | Single-flow (Evasion) | A privilege granted during the session is not revoked when the session ends. The system skips the information flow that would revoke access, enabling privilege escalation after the fact. | L4, L7, L2 |
| **Configuration Drift** | Server | Inter-flow (Drift) | Incremental misalignment between client and server configuration accumulates over time. Subtle differences cause persistent errors in transmission principles. | L4, L7 |
| **Server Version Mismatch** | Client | Intra-flow (Transmission Principle) | Client fails to update to the server's expected version. Security enforcement logic may silently fail because expected behaviors no longer match the actual server state. | L3, L7 |

---

## 6. The Datasets — How MCIP Generates Training and Evaluation Data

### 6.1 Source Data

Two open-source datasets are used as raw material:

**glaiveai/glaive-function-calling-v2** — 112,960 real function-calling
conversations in multi-turn dialogue format, released by Glaive AI. This is
one of the most widely used datasets for training function-calling models.

**Team-ACE/ToolACE** — 11,300 rows of function-calling data. Used as a
supplementary source for generalizability testing, since its function pool is
entirely different from Glaive AI.

### 6.2 MCIP-Bench — The Evaluation Benchmark

**Purpose:** Test whether LLMs can detect safety risks in MCP scenarios.

**Construction process:**
1. Sample 200 real conversations from `glaive-function-calling-v2` as "gold"
   (safe) instances.
2. Extract all function call bodies and return values to build a **function
   pool of 10,633 function call pairs**.
3. For each of the 10 risk categories, synthesize **risk-specific variations**
   of the gold instances by injecting attacks. For categories requiring
   high-privilege functions (Identity Injection, Excessive Privileges
   Overlapping), use DeepSeek-R1 to generate alternative function bodies that
   require elevated access.
4. Use DeepSeek-R1 to assist with labeling and to verify correctness.
5. Add supplementary instances from ToolACE to test generalizability.

**Final size:**

| Label | From Glaive AI | From ToolACE | Total |
|-------|---------------|-------------|-------|
| True (safe) | 188 | 214 | 402 |
| Identity Injection | 183 | — | 183 |
| Function Overlapping | 126 | 83 | 209 |
| Function Injection | 111 | 149 | 260 |
| Data Injection | 109 | 84 | 193 |
| Excessive Privileges Overlapping | 108 | — | 108 |
| Function Dependency Injection | 106 | 150 | 256 |
| Replay Injection | 95 | 150 | 245 |
| Wrong Parameter Intent Injection | 71 | 74 | 145 |
| Ignore Purpose Intent Injection | 60 | 56 | 116 |
| Causal Dependency Injection | 35 | 66 | 101 |
| **Total** | **1,192** | **1,026** | **2,218** |

Each instance is a **multi-turn function-calling dialogue averaging 6 turns**.
The ToolACE subset is used specifically to measure generalizability — the
model is never trained on ToolACE-style functions.

**Evaluation tasks on MCIP-Bench:**

- **Safety Awareness** — binary classification: is this interaction safe or
  unsafe? Measured by accuracy and macro F1.
- **Risk Resistance** — 11-class classification: which specific attack type is
  present? Measured by weighted recall across all 11 classes.

### 6.3 MCIP Guardian Training Data

**Purpose:** Train a model to classify MCP risks using the MCI structured format.

**Construction process:**
1. Sample 2,000 rows from `glaive-function-calling-v2` as raw training data.
2. Use DeepSeek-R1 to **annotate each dialogue in MCI format** — extracting
   the 5-tuple (sender, recipient, data_subject, information_type,
   transmission_principle) for each step and assembling the full trajectory.
3. Apply the same synthesis strategy as MCIP-Bench to create risk-specific
   variants across all 10 attack categories.

**Final size:**

| Label | Training Count |
|-------|---------------|
| True (safe) | 1,791 |
| Identity Injection | 1,749 |
| Function Overlapping | 1,395 |
| Function Injection | 1,382 |
| Data Injection | 1,361 |
| Excessive Privileges Overlapping | 1,401 |
| Function Dependency Injection | 1,372 |
| Replay Injection | 1,371 |
| Wrong Parameter Intent Injection | 664 |
| Ignore Purpose Intent Injection | 718 |
| Causal Dependency Injection | 626 |
| **Total** | **13,830** |

Each training instance contains around **8 transmission steps** formatted
as an ordered MCI trajectory. The three smallest classes (Wrong Parameter:
664, Ignore Purpose: 718, Causal Dependency: 626) are underrepresented —
roughly 2–3× fewer samples than the top classes. This is a known limitation.

---

## 7. Evaluation Metrics

MCIP is evaluated on three metrics:

**Safety Metrics (on MCIP-Bench):**

- **Safety Awareness** — Accuracy and Macro F1 on the binary safe/unsafe
  classification task. Tests whether the model can detect that a risk exists.
- **Risk Resistance** — Accuracy and Macro F1 on the 11-class risk
  identification task. Tests whether the model can identify what kind of
  risk it is.
  - A separate **ToolACE Risk Resistance** score measures generalizability on
    unseen function types (ToolACE subset of MCIP-Bench).

**Utility Metric:**

- **BFCL overall accuracy** — Berkeley Function Calling Leaderboard v3
  accuracy. Measures whether safety fine-tuning degrades the model's ability
  to correctly handle normal, benign function calls. This is the safety-utility
  trade-off measure.

---

## 8. Experimental Results — What the Numbers Say

Models tested: xLAM-2-70b-fc-r, xLAM-2-32b-fc-r, xLAM-2-32b-fc-r (base),
ToolACE-2-8B, Qwen2.5-72B-Instruct, Qwen2.5-32B-Instruct, DeepSeek-R1, and
**MCIP Guardian (their model)**.

Full results (Table 2 from the paper):

| Model | BFCL Acc (%) | Risk Resistance Acc (%) | Risk Resistance Ma-F1 | ToolACE Risk Resistance Acc (%) | ToolACE Risk Resistance Ma-F1 | Safety Awareness Acc (%) | Safety Awareness Ma-F1 |
|-------|-------------|------------------------|----------------------|-------------------------------|------------------------------|--------------------------|----------------------|
| xLAM-2-70b-fc-r | **78.45** | 17.14 | 9.91 | 20.29 | 6.90 | 22.69 | 22.57 |
| xLAM-2-32b-fc-r | 76.43 | 30.12 | 25.32 | 34.80 | 20.63 | 37.25 | 36.94 |
| xLAM-2-32b-fc-r (Base) | 72.04 | 13.35 | 8.84 | 14.42 | 7.61 | 57.43 | 49.18 |
| ToolACE-2-8B | 68.71 | 5.00 | 3.76 | 17.21 | 13.56 | 62.38 | 24.56 |
| Qwen2.5-72B-Instruct | 60.76 | 40.77 | 33.74 | **47.08** | **34.23** | 55.45 | 52.20 |
| Qwen2.5-32B-Instruct | 58.93 | 35.74 | 28.21 | 39.38 | 26.12 | 50.08 | 47.92 |
| DeepSeek-R1 | 56.89 | 42.28 | 35.18 | 49.42 | 33.45 | 55.45 | 60.50 |
| **MCIP Guardian (Ours)** | 65.79 | **54.16** | **42.03** | **42.03** | **37.19** | **75.73** | **69.91** |

**What the numbers reveal:**

### Finding 1: LLMs are dangerously bad at detecting MCP risks

Even the best baseline (DeepSeek-R1) achieves only 42.28% on Risk Resistance
and 55.45% on Safety Awareness. Qwen2.5-32B achieves only 50.08% on Safety
Awareness — barely above random chance. The specialized function-calling model
xLAM-2-70b achieves only 17.14% Risk Resistance despite having 78.45% BFCL
utility. LLMs are not naturally safe in MCP contexts.

### Finding 2: Function-calling LLMs are specifically worse at safety

The xLAM series, despite being the most capable at function calling, performs
among the worst at safety. xLAM-2-70b reaches 17.14% Risk Resistance — less
than a third of what DeepSeek-R1 achieves. The reason: function-calling
training optimizes for executing functions correctly, not for questioning
whether they should be called. These models tend to **over-approve** function
executions, treating everything as a legitimate request.

### Finding 3: General reasoning ability matters more than function-calling for safety

DeepSeek-R1 and Qwen2.5-72B-Instruct, despite weaker function-calling
performance (lower BFCL), significantly outperform xLAM models on safety
metrics. Strong general reasoning and contextual understanding enables better
safety judgment than specialized tool-use training alone.

### Finding 4: The safety-utility trade-off is real but manageable

MCIP Guardian achieves 54.16% Risk Resistance (the best of any model) but its
BFCL drops to 65.79% — lower than xLAM-2-70b's 78.45%. There is a genuine
trade-off: fine-tuning for safety reduces utility. However, MCIP Guardian
achieves a more **balanced** position: safety awareness 75.73% (highest) while
maintaining reasonable utility (65.79%). The ablation confirms this: safety
metrics improve steadily across 3 epochs while BFCL drops moderately at first
then stabilizes.

### Finding 5: MCIP Guardian improves over the best baseline by a large margin

Against DeepSeek-R1 (best baseline):
- Risk Resistance: 42.28% → **54.16%** (+11.88 pp absolute)
- Safety Awareness: 55.45% → **75.73%** (+20.28 pp absolute)
- Macro F1 (Safety): 60.50% → **69.91%** (+9.41 pp)

These are substantial improvements. The authors report 40.81% and 18.3%
improvements on two safety metrics, plus 27.22% improvement on a
generalization test.

---

## 9. The Attack-Defense Lifecycle MCIP Enables

MCIP frames MCP security as a complete attack-defense cycle:

```
ATTACK PATH:
  Malicious MCP clients  }
  Malicious MCP servers  } → attack foundation models
                           → operate through unintended/unauthorized operations

DEFENSE PATH:
  Safety models → learn from tracking files (MCI logs)
               → defend against real-time attack behaviors
```

This cycle has two sides:
- The **attack side** uses both clients and servers to exploit the foundation
  model's tendency to follow instructions, regardless of whether those
  instructions are contextually appropriate.
- The **defense side** uses the MCI-structured logs as training signal to teach
  models to recognize when instructions violate contextual norms.

MCIP supports both halves — the tracking log provides the attack signal,
and the Guardian model provides the defense response.

---

## 10. Key Insights from the Ablation Study

The authors conduct ablation experiments to understand *why* models fail.

**Why do function-calling LLMs fail at safety?**

Recall curves (Figure 6) show that function-calling models (xLAM, ToolACE)
have very low recall on "Unsafe" — they classify almost everything as safe.
This is a **missing alignment signal**: function-calling training teaches models
*how* to call functions, not *whether* they should be called in a given context.
A model optimized for calling accuracy has no training signal that would cause
it to say "this call is contextually wrong."

**Does the safety training hurt utility?**

Figure 7 shows the training curve for MCIP Guardian over 3 epochs:
- BFCL utility drops initially, then stabilizes.
- Safety metrics (Risk Resistance, Safety Awareness) improve steadily.
- The trade-off is real but not catastrophic — the final model retains
  competitive utility while gaining substantially in safety.

**Conclusion:** Targeted contextual alignment — training specifically on
contextual integrity violations — is more effective at improving MCP safety
than simply scaling model size or improving function-calling capability.

---

## 11. How the Prompt Templates Work

The paper uses three prompt templates in its data pipeline (Table 5):

**High Privilege Function Generation** (for training data augmentation):
Used to generate alternative function calls that require higher privileges
while maintaining semantic similarity to the original. This creates realistic
Excessive Privileges Overlapping and Identity Injection examples. The generated
functions must: require higher privilege, maintain similar core functionality,
preserve high semantic similarity to the original.

**MCI Annotation** (for training data formatting):
Used to instruct DeepSeek-R1 to extract the 5-element MCI tuples from raw
conversation data. The model is asked to identify every user enquiry and
output the corresponding information flows as structured JSON. Format:
`{enquiry: xxx, information flow: [sender:xxx, recipient:xxx, data subject:xxx,
transmission principle:xxx, information type:xxx]}`.

**Evaluation** (for MCIP-Bench testing):
Given a list of vulnerability definitions and an input chat, the model
must choose the most appropriate attack label (A–K) and provide a rationale.
This is a multiple-choice format that enables standardized evaluation.

---

## 12. Limitations the Authors Acknowledge

**1. No simulation of specific adversarial attack strategies.**
The taxonomy accounts for potential risks from malicious sources and plausible
threat goals, but does not explicitly capture the full diversity of concrete
attack techniques — no prompt injection variants, no malicious payload
construction exercises.

**2. Absolute performance is still low.**
54.16% on Risk Resistance leaves substantial room for improvement. The model
can detect risks much better than baselines, but nearly half of risky
interactions still slip through. Future work should explore fine-grained
supervision or targeted training strategies.

**3. Long-tail class performance.**
The three smallest classes (Wrong Parameter, Ignore Purpose, Causal Dependency)
are both underrepresented in training data and hardest to detect. Causal
dependency injection is particularly hard to model because the attack
spans multiple turns and requires understanding temporal ordering.

**4. Synthesized data only.**
Neither MCIP-Bench nor the Guardian training set comes from real-world MCP
deployments. The authors rely on synthesized variations of real function-calling
dialogues, but real attacks in production will be noisier, more ambiguous, and
more varied than controlled synthesis can capture.

**5. No integration with adaptive threat modeling.**
The current approach uses a fixed taxonomy. Attackers adapt. Dynamic adversarial
training — where new attack patterns are discovered and folded into training —
is listed as future work.

---

## 13. What MCIP Contributes vs. What It Does Not Do

### What It Contributes

- **First systematic safety analysis of MCP** from a contextual integrity
  perspective.
- **A formal taxonomy** of 14 attack types across 3 phases, 2 threat sources,
  and 3 threat scopes — all grounded in the MAESTRO framework.
- **MCIP-Bench** — the first benchmark for evaluating LLM safety in MCP
  function-calling contexts. 2,218 instances, 11 classes.
- **Guardian Training Data** — 13,830 structured MCI-format training instances
  for teaching risk recognition.
- **MCIP Guardian** — a fine-tuned model that achieves substantially better
  safety performance than any general-purpose or function-calling LLM baseline.
- **Empirical evidence** that function-calling training makes models *less*
  safe in MCP contexts, not more.

### What It Does Not Do

- It does **not produce severity scores**. Every risky interaction is labeled
  with a category, but there is no 1–10 magnitude telling the server how
  dangerous this specific instance is.
- It does **not enable graduated responses**. The output is a category label.
  The server can block or allow, but cannot throttle, monitor, or respond
  proportionally.
- It does **not handle low-level protocol exploits** well. MCPSecBench showed
  that MCIP Guardian is less than 30% effective against protocol-level attacks
  (real CVEs, sandbox escapes, DNS rebinding).
- It does **not use real-world deployment data**. The training and evaluation
  are entirely on synthesized data.
- It does **not log or reason about multi-session patterns**. Each interaction
  is treated independently — cross-session accumulation risks are outside scope.

---

## 14. Connection to Your Thesis

The gap MCIP leaves is exactly the gap your thesis fills:

| MCIP | Your Thesis |
|------|-------------|
| Detects the **type** of risk (which of 10 categories) | Produces a **severity score** (1–10) for each request |
| Binary label: safe or unsafe | Graduated output: allow / log / escalate / deny |
| MCI trajectory as a sequence of 5-tuples | Dynamic scoring combining static tool properties + request context + session history |
| MCIP Guardian as a classifier | Multi-stage scorer: static metadata → contextual enrichment → LLM judgment |
| Synthesized benchmark (2,218 instances) | Real testbed: 32 servers, 25 attack templates, live execution |
| Evaluated on MCIP-Bench | Evaluated on ASR, TPR/FPR at multiple score thresholds |

MCIP's 10 risk categories map directly to severity tiers in your framework:

| MCIP Category | Suggested Score Range | Reasoning |
|---------------|-----------------------|-----------|
| Identity Injection | 9–10 | Full agent compromise, executes commands as admin |
| Function Injection | 8–10 | Unauthorized tools added to agent's capability space |
| Data Injection | 7–9 | Reasoning corrupted by fabricated return values |
| Excessive Privileges Overlapping | 6–8 | Principle of least privilege violated |
| Replay Injection | 6–8 | Authorization trust model broken across time |
| Causal Dependency Injection | 5–7 | Control flow manipulated across multiple steps |
| Function Overlapping | 4–6 | Wrong tool selected, depends on agent's choice |
| Function Dependency Injection | 4–6 | Unnecessary calls added, redundant flows |
| Wrong Parameter Intent Injection | 3–5 | Correct tool, wrong parameters |
| Ignore Purpose Intent Injection | 3–5 | Tool misused but damage is bounded |
| True (safe) | 1–2 | Contextually appropriate information flow |

You can also directly use MCIP's datasets:
- **MCIP-Bench** as one of your evaluation benchmarks (your scorer's output
  should correlate with MCIP's risk labels — riskier categories should score
  higher).
- **Guardian Training Data** (13,830 MCI-format instances) as a training
  signal for your dynamic scoring component.

---

## 15. Quick Reference Card

| Item | Value |
|------|-------|
| Paper | arXiv:2505.14590 (EMNLP 2025) |
| Authors | Jing, Li, Hu, Hu, Xu, Chu, Hu, Song (HKUST + Huawei) |
| Code & Data | https://github.com/HKUST-KnowComp/MCIP |
| Core Theory | Contextual Integrity (Nissenbaum 2004) |
| Threat Framework | MAESTRO (CSA 2025) |
| Fills MAESTRO Layers | 5 (tracking) and 6 (safety model) |
| Attack Phases | Config, Interaction, Termination |
| Attack Types | 14 total (3 Config + 8 Interaction + 3 Termination) |
| Eval Benchmark | MCIP-Bench: 2,218 instances, 11 classes |
| Training Data | Guardian Dataset: 13,830 instances, 11 classes |
| Base Model | Salesforce/Llama-xLAM-2-8b-fc-r |
| Best Risk Resistance | 54.16% (MCIP Guardian) vs 42.28% (DeepSeek-R1 baseline) |
| Best Safety Awareness | 75.73% (MCIP Guardian) vs 60.76% (Qwen2.5-72B baseline) |
| Safety improvement | +40.81% and +18.3% on two safety metrics vs baselines |
| Key finding | Function-calling LLMs are *less* safe than general LLMs in MCP |
| Key gap left open | No severity graduation, no graduated response, no real-world data |
