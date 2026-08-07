# Paper Brief — hand this to an LLM assistant

Self-contained context for helping write this paper, especially the
**Introduction** and **Related Work**. You have no other context, so everything
you need is below. Read §0 first — it will save you from three mistakes that
previous assistants made on this exact task.

---

## 0. Read this before you start

Three assistants have already reviewed this paper. All three made the same
class of error, and it cost real time:

1. **They hallucinated citation links.** One produced a "citation check" table in
   which *every single link* pointed at the wrong paper — "Caller Identity
   Confusion in MCP" linked to NIST SP 800-60, "MCP-in-SoS" linked to FIPS 199.
   **If you cannot verify a reference, say you cannot. Do not produce a URL.**
2. **They quoted superseded arXiv titles as corrections.** One insisted three
   bibliography titles were wrong; all three matched the *current* arXiv
   versions and the reviewer was reading v1 abstracts. **Check the version.**
3. **They reviewed a stale PDF** and reported placeholder artefacts (`[? ?]`,
   `§??`) that had already been fixed.

Also: **do not invent bibliography keys.** §6 lists every key that exists. If
an argument needs a source that is not in that list, say so explicitly rather
than inventing `smith2025something`.

---

## 1. What the work is, in one paragraph

The Model Context Protocol (MCP) lets AI agents invoke tools on a server that
owns real organizational resources — files, repositories, databases, message
archives. We built a system that lets **the server** decide how dangerous an
incoming call is, *before* executing it, and turn that into an access-control
decision. It computes a graded risk score at two times: **design time**, for
every (tool, resource) pairing the server exposes, and **request time**, using
the concrete arguments, the session context, and the agent's recent activity.
The distinguishing part is where the *resource sensitivity* number comes from:
it is **derived from the organization's own published classification policy**
(prose, no numbers in it), not assumed from a labelled inventory that no
organization will actually hand you.

**Threat framing (never reverse this):** the MCP server is the **protected
resource**; the agent is the **risk source**. The subject is **misuse through
legitimate access**, not intrusion. Harm needs no attacker.

---

## 2. The paper's argument, as a chain

Each link is one paragraph of the Introduction.

1. Agents act on real systems through MCP. MCP standardises *how* a call is
   made, not *how consequential* it is. The server holds the data and runs the
   side effects — the last place a damaging call can be stopped.
2. The field studies the reverse direction (malicious server → agent). We study
   agent → server. What those calls share is **misuse**: a legitimate
   capability exercised inappropriately, needing no malicious party. It starts
   with **human error** (loose task statement, over-broad delegation,
   over-provisioning) and continues on the **agent side** (hallucinated tool
   calls; proceeding despite recognised risk). Prompt injection and agentic
   misalignment are further routes to the same place, not the main subject.
   **Unit of analysis = the whole invocation:** tool, resource, arguments,
   context, history.
3. Conventional access control does not by itself *quantify* this. RBAC/ABAC
   answer "may this agent use this tool?", not "how dangerous is this
   invocation?" And appropriate and inappropriate calls arrive through the same
   authenticated channel.
4. Risk-adaptive access control is not new — it dates to 2007, was fused with
   ABAC in 2011, and **has recently been extended to agentic systems**. What it
   has not been given is an MCP-specific notion of what a call would cost.
   Several 2026 systems *do* produce graded outcomes, but the grade is a
   containment level, an action class, or a detector score — never a computed
   **consequence magnitude** for what the call would touch.
5. Three axes a conventional formulation misses: risk belongs to the
   **(tool, resource) pairing**, the **arguments** move the baseline, and the
   same call reads differently against different **histories**.
6. Our methodology: design-time baseline, request-time refinement, graded score
   against organizational thresholds → allow / review / deny.
7. Three contributions (§4 below).

**One-sentence through-line.** *Access control decides whether an agent MAY
act; we add a computed, graded consequence score so an MCP server can decide
HOW DANGEROUS this particular invocation is.*

---

## 3. What is genuinely novel — and what is NOT

This was established by a 37-paper sweep. Be precise here; the gap is narrow
and real, and overclaiming it is the fastest way to get rejected.

### The defensible novelty

> No prior work derives a **consequence magnitude** for a concrete MCP
> invocation by combining **tool impact**, **blast radius**, and a **resource
> sensitivity obtained from the organization's own classification policy**.

The load-bearing part is the **resource axis**. Across all 37 candidates, every
competing system scores the **action** — its type, its arguments, its
conformance to a declared intent — and is structurally blind to **what the
action touches**. Nothing has both a tool-impact axis and a policy-derived
resource-sensitivity axis.

### What is NOT novel — do not claim these

| Claim | Why it fails |
|---|---|
| "Risk-adaptive access control has not been applied to agents" | **False.** `fleming2025tbac` is exactly that. |
| "Existing MCP defenses are binary / stop at allow-deny" | **False as of 2026.** `li2026conleash`, `yang2026agenttrust`, `hossain2026nexus` all produce graded outcomes. |
| "A static baseline refined at request time" as the novelty | `zhang2026stars` already publishes that architecture. |
| "Nobody inspects arguments" | `zhu2026igac` and `rahman2026rolestratified` do, server-side. Their tests are *containment or detection*, not graded severity — that is the real distinction. |
| CVSS/RFC grounding as novel | Others use the same anchors. It is methodological rigour, not novelty. |

### The three closest papers — must be cited and distinguished

| Key | What it does | Why we survive |
|---|---|---|
| `li2026conleash` | Closest in **setting**: authorizes MCP invocations, call-with-arguments as the unit, graded consent-lattice outcome, 984 real traces, user study | Client-side; we enforce at the server. No resource axis. |
| `zhang2026stars` | Closest in **architecture**: static prior + request-conditioned model fused into one calibrated score | Explicitly stops short of an enforcement decision. No resource axis. |
| `yang2026agenttrust` | Closest in **mechanism**: ships as an MCP server, four-way verdict plus ordinal risk level, normalizes obfuscated arguments, detects multi-step chains | Overlaps our dynamic layer only. No policy derivation. |

---

## 4. The three contributions

1. **A risk-analysis methodology** assessing the misuse risk of an MCP
   invocation from tool impact, resource sensitivity, blast radius, runtime
   arguments, execution context, and the agent's recent activity — deriving its
   sensitivity input from organizational policy rather than a labelled asset
   inventory.
2. **An enforcement framework** integrating the design-time and request-time
   assessments into a risk-based access-control decision for MCP servers.
3. **An evaluation setting** pairing tool catalogs captured from real vendor MCP
   servers with synthesized organizational policies, resource inventories, and
   invocation scenarios.

---

## 5. The system and its numbers

**Every number below is exact. Do not round, restate, or extrapolate.**

### Scoring model

```
score = resource_sensitivity (1-5)  x  blast_radius (1-5)  x  tool_impact (1-5)
      -> 1..125 -> deterministic assembly -> band in {low, medium, high, critical}
```

Inputs are exactly two documents: the captured tool catalog (`tools/list`) and
the organization's policy section. The per-asset sensitivity table is **held
out** and used only as ground truth.

### Tool impact — a deterministic five-tier ladder

| Tier | Operation |
|---|---|
| 1 | none — server talks about itself (ping, health, version) |
| 2 | metadata — names, ids, counts, timestamps, schema, listings |
| 3 | content read **or** limited write (append a line, set one field) |
| 4 | ordinary write — caller supplies what the item says |
| 5 | removal or execution — delete, purge, run code, move money |

281 vocabulary patterns. The **3/4 boundary is externally grounded**: RFC 5789
`PATCH` (partial modification) vs RFC 9110 `PUT` (complete replacement), and
CVSS v4.0 `VI:L` ("amount of modification is limited") vs `VI:H` ("total loss
of integrity"). Breadth is deliberately absent — blast radius scores coverage.

### Dynamic layer — four signals

Embedding likelihood (no LLM), behavioural baseline (no LLM), session sequence
risk (no LLM), LLM judge (optional). Band signals **escalate only**. The
embedding likelihood multiplies: `final_risk = static_score x likelihood`,
likelihood in `[0.1, 1.0]`. Fit < 0.5 s per server; scoring ~0.05 ms per call.

### RESULT 1 — policy text alone recovers the organization's severities

Three real vendor servers, **56 resources, 55 tools**.

| Server | Resources | Tools | MAE | Exact | Within 1 |
|---|--:|--:|--:|--:|--:|
| calendar | 16 | 13 | 0.125 | 88% | 100% |
| github | 20 | 26 | 0.10 | 90% | 100% |
| slack | 20 | 16 | 0.10 | 90% | 100% |

**50 of 56 exact; no resource off by more than one tier** — from a document
that states no number anywhere. The six misses are all adjacent-tier and all
defensible (e.g. `infra-config` scored 4 vs the org's 5).

### RESULT 2 — the rules needed no model

**55/55 tools decided by the deterministic ladder, 0 LLM calls**, 51/55 (93%)
agreement with the previous arm's LLM, every disagreement one tier.

> **Mandatory honesty constraint.** The LLM fallback never fired because all
> three vendor catalogs declare no MCP annotations, so every confidence was
> either 0.8 or 0.35 — nothing landed near the 0.5 threshold. The hybrid
> hand-off is **covered by unit tests only** on this corpus. This must be
> stated, not glossed.

### RESULT 3 — the dynamic signal adds discrimination

At flag threshold **critical**:

| Scorer | Recall (adversarial) | Fall-out (benign) |
|---|--:|--:|
| static | 56% | 9% |
| combined | **81%** | **9%** |

**+25 points of recall at unchanged false-positive cost.** 22 of 88 adversarial
sessions are caught *only* by the dynamic signal. At threshold *high*: static
91% → combined 100%, fall-out 49% both.

### RESULT 4 — calibration transfers to real traffic

Live `mcp-server-git` over stdio against a real repository (223 commits):
**400 real tool calls**, 399 OK, 12 tools, 106 distinct call signatures. Fit on
the first 70% chronologically, scored the held-out 30%. **Benign false-positive
rate 0.8%**; mean held-out likelihood 0.107. The quantile-anchored ramp, tuned
on synthetic data, **transferred with no adjustment**.

### What is real vs synthesized

- **Real:** the tool catalogs, captured from live vendor servers. The git corpus.
- **Synthesized:** organizational policies, asset registers, invocation
  scenarios.
- Call it an **evaluation setting**, never a benchmark.

---

## 6. Every citation key that exists

**Use only these.** Anything else must be flagged as missing, not invented.

### MCP protocol and ecosystem
`anthropic2024mcp` · `mcp2026spec` · `hasan2025firstglance` (1,899 servers analysed) · `hou2026mcp` (survey)

### The direction the field studies (server harms agent)
`invariant2025toolpoisoning` · `shi2025toolhijacker` · `zhao2026parasites`

### Server exposure; identity is not enough
`li2025privilege` (over-privilege, measured) · `huang2026auditing` · `huang2026caller` (caller identity confusion in MCP) · `mellafe2026capability` (capability gates ≠ authorization)

### Misuse without an attacker
`yin2025reasoningtrap` (reasoning amplifies tool hallucination) · `tang2025riskknowledge` (agents act against risk they can articulate) · `zhan2024injecagent` (indirect prompt injection) · `lynch2025misalignment` (agentic misalignment — **not** injection; keep separate)

### MCP / agent defenses
`xing2025mcpguard` · `jing2025mcip` · `shi2025progent` · `zhu2025miniscope` · `abaev2026agentguardian`

### Access control and its risk-based branch — the family we join
`sandhu1996rbac` · `hu2014abac` (NIST SP 800-162) · `cheng2007fuzzymls` (**founding quantified risk-adaptive AC**) · `kandala2011radac` (ABAC + risk) · `atlam2020riskbased` (survey) · `cheimonidis2023dynamic` · `bradatsch2024zerotrust` · `fleming2025tbac` (**risk-adaptive AC for agentic systems — the closest AC prior work**)

### Why classical scoring does not transfer
`spring2021time` · `bahar2024validity` · `owasp2025aivss` (AI-specific — do **not** call it "classical static software scoring") · `cao2024mad` (graded beats binary, measured)

### Risk scoring aimed at MCP and agents
`kumar2026mcpinsos` (server implementations) · `betser2026agentrim` (offline + runtime tool-call validation — **not** "the tool alone") · `fu2025riskcue` (logs, post hoc)

### 2026 concurrent work on graded agent/MCP authorization
`li2026conleash` · `zhang2026stars` · `yang2026agenttrust` · `hossain2026nexus` · `almandalawi2025policyaware` · `zhu2026igac` · `owireduashley2026severity` · `li2025accesscontrol` · `shi2025sok` · `rahman2026rolestratified`

### Standards
`nist2004fips199` · `nist2008sp80060` (classify-then-map sensitivity) · `dusseault2010patch` (RFC 5789) · `fielding2022http` (RFC 9110) · `first2023cvss4`

---

## 7. Claims that must NEVER appear

- **Scalability versus manual assessment.** Never measured. No "faster than
  human review", no "cheaper", no "does not scale by hand" as a *result*.
- **That the rules→LLM hand-off was exercised.** It never fired.
- **That the LLM judge was evaluated.** It is wired but was not run.
- **External benchmark comparison for the dynamic task.** None exists.
- **Cross-organization generalization.** One policy document, three servers.
- **Any reversal of the threat direction.** Server protected, agent risk source.

---

## 8. Venue constraints (AAMAS 2027)

- **8 pages of body.** References free; appendices free but **may not carry
  core content** — the paper must be self-contained.
- **Double-blind.** Cite our own prior work in the third person.
- LaTeX mandatory, ACM `acmart` / `sigconf`. Do not modify layout parameters;
  "excessive typesetting tricks" are a desk-reject category. **Cut words instead.**
- Abstract 100–300 words, registered one week before the paper deadline.
- Deadline: early October 2026 (TBC). Conference 3–7 May 2027, Hanoi.
- **"Out of scope" is a desk-reject category.** AAMAS is an agents conference,
  not a security conference. Frame as *agent governance*, not vulnerability
  management.

**Length budgets:** Introduction 650–900 words (currently ~1,030 — needs
cutting); Related Work 600–700; Threat model 600–700; Framework 1,400–1,700;
Evaluation 1,600–1,900.

---

## 9. What I want help with

### Related Work (600–700 words, four strands)

Not a paper list. Four paragraphs, each ending in the sentence that says why
that strand does not solve the problem. Group citations aggressively — with ~50
keys and 700 words, most appear in groups without individual discussion, and
that is correct.

1. **MCP security** — the field studies the server harming the agent.
2. **Defenses for MCP and tool-using agents** — several now produce graded
   outcomes, but the grade is a containment level, an action class, or a
   detector score, never a consequence magnitude over a (tool, resource) pair.
3. **Access control and its risk-based branch** — *the key strand.* RBAC/ABAC
   decide permission; risk-adaptive AC adds a computed risk value; it now
   reaches agentic systems. What it lacks is an MCP-specific consequence model.
   This is where our contribution is placed.
4. **Risk scoring for MCP and agents** — scores the server implementation, the
   tool call at runtime, or the log after the fact.

### Introduction

Currently ~1,030 words against a 650–900 budget. I need it **compressed without
losing precision**. Known redundancy: the ecosystem-scale sentence in ¶1, and
the `$1,000,000 vs $1,000` example, which now partly duplicates "a well-formed,
authorised call whose consequence exceeds what the operator intended."

**Do not soften the gap claim while cutting.** It took several iterations to get
it factually correct against the 2026 literature, and the precise version is in
§3 above.

---

## 10. Style rules

- One idea per sentence. One message per paragraph, stated in its first sentence.
- Front-load the claim; qualification second.
- Terminology must be stable: **resource** (not "asset"), **invocation** (not
  "call"/"request"/"action" interchangeably), **misuse** as the organizing concept.
- No roadmap paragraph — AAMAS papers do not use them.
- Avoid absolutes unless backed: prefer "much recent work" to "most work",
  "does not by itself quantify" to "cannot express".
- Every factual sentence rests on a number from §5, a key from §6, or an
  explicit statement that it is our own design choice.
