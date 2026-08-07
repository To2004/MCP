# Citation Audit — Supplement for the new Related Work

Companion to [`CITATION-AUDIT.md`](CITATION-AUDIT.md) (2026-08-03), which is more
thorough than this and should be read first. This file covers only the **new
Related Work text supplied 2026-08-02** and the bib entries it introduced, which
post-date that audit and are therefore not in it.

**No prose was changed.** `refs.bib` gained six entries the new text cites that
were absent from the file on disk; without them the section does not compile.

---

## 1. Verified correct — every numeric claim in the new Related Work

Checked against primary sources. Quotes verbatim.

| Claim in your text | Evidence |
|---|---|
| "Li et al. analyze **2,562** MCP applications" | *"we systematically examine 2,562 real-world MCP applications spanning 23 functional categories"* — arXiv:2507.06250 |
| "measure their use of **file, network, system, and memory** APIs" | *"network and system resource APIs dominate usage patterns, affecting 1,438 and 1,237 servers respectively, while file and memory resources are less frequent but still significant"* |
| "MCP-in-SoS scans **222** server repositories" | *"we conduct a large-scale analysis of 222 GitHub repositories implementing MCP servers"* — arXiv:2603.10194 |
| "derives repository-level risk from the likelihood and severity **those catalogs assign**" | *"We rely on standardized metadata from the MITRE CAPEC and CWE databases."* Likelihood of Attack + Typical Severity from CAPEC; Likelihood of Exploit from CWE. **Your attribution to the catalogs is exactly right** — this is a precise sentence. |
| "a study of **196** evaluators" | 196 participants, main survey — arXiv:2308.15259, IEEE S&P 2024 |
| "**68%** assigned a different severity level to vulnerabilities they had scored before" | Follow-up survey, 59 participants, 68% gave different ratings |
| "Huang et al. combine static pattern matching with sandboxed execution" | *"static pattern matching … and dynamic sandboxed fuzzing and monitoring via Docker and eBPF"* |

---

## 2. Will break the build

### `mtguard2026` does not exist

`02-related-work.tex`, defenses paragraph:

```latex
...against safety policies~\cite{zhu2026igac,mtguard2026}.
```

The key in `refs.bib` is **`he2026mtguard`**. Renders as a bold `[?]`.

---

## 3. Duplicate entries introduced by the new text

Each prints **twice** in the bibliography under two numbers, because `\nocite{*}`
is still on.

| Work | Keys | Where used |
|---|---|---|
| Parasites in the Toolchain | `zhao2026parasites` / `zhao2025parasites` | Intro / Related Work |
| CVSS v4.0 specification | `first2023cvss4` / `first2023cvss` | uncited / Related Work |
| AIVSS | `owasp2025aivss` / `owasp2026aivss` | Intro / Related Work |

Note `zhao2025parasites`: the citekey says **2025**, the entry says **2026 IEEE
S&P**. The main audit §3 also notes a proceedings DOI now exists for this work.

### A version mismatch inside one of them

> "A study of 196 evaluators applying **CVSS v3.1** found differences between
> evaluators … `\cite{first2023cvss,wunder2024cvss}`"

`first2023cvss` is the **v4.0** specification. It is cited to support a sentence
about **v3.1** evaluator behaviour. Either cite the v3.1 spec or let
`wunder2024cvss` carry the sentence alone.

Separately: the Wunder abstract does not state which CVSS version was used. The
paper references the 2022 CWE Top 25, so v3.1 is plausible — **confirm in the
body before submission**.

---

## 4. Could not verify — check before submission

Not necessarily wrong; simply unconfirmed, and both paywalled.

- `ni2010fuzzy` — "fuzzy rules over subject and object security information"
- `shaikh2012dynamic` — "dynamically calculate trust and risk for each
  subject–object pair from the user's past behavior"
- `kandala2011radac` — "leave the concrete risk-calculation method outside their
  scope". A claim about what a paper *does not* do is the hardest kind to defend.
- `owireduashley2026severity` — "grades the harm of actions recorded **after
  execution**". If it grades proposed actions instead, the contrast with STARS
  collapses.
- `zhao2025parasites` DOI `10.1109/SP63933.2026.00154` — not resolved here.

---

## 5. Two places where the new text collides with the main audit

### 5.1 The STARS sentence

Your Related Work says STARS *"scores proposed skill invocations using the
request, capability, and runtime context before execution."* **That is accurate**
— and it is the same finding the main audit flags as blocking (§1.2): STARS
occupies your unit of analysis. Your Related Work states this correctly while
the closing novelty sentence elsewhere still claims the unit. Fixing one without
the other leaves the paper contradicting itself.

### 5.2 Parasites, again

The new Related Work groups it under *"attacks in which a malicious server, tool
description, or external input influences the agent."* Zhao et al.'s abstract:
*"**Unlike traditional prompt injection and tool poisoning attacks**, our attack
targets the interconnected toolchain itself, assembling multiple **legitimate**
tools into a coordinated workflow."*

"External input" makes the grouping defensible. But your Introduction now uses
the paper for harm arising with no single malicious call, so the two sections
characterise it differently. The main audit §2.2 flags a third, separate
misattribution of the same key.

### 5.3 AgentBound is absent from Related Work

`buhler2026agentbound` appears in the Introduction but nowhere in the new
Related Work, which has an **Access control** heading. It is peer-reviewed (FSE
2026) and its abstract claims to be *"the first access control framework for MCP
servers."* I verified from the PDF that its threat model is the reverse of
yours — *"an adversary … controlling one or multiple malicious MCP server(s)"*,
*"protecting the host system"*. That is your answer, but it needs to appear
where a reviewer looks for it.

---

## 6. Two errors of mine that the main audit caught

Recording these because both came from work I did in this project and both were
stated with more confidence than they deserved.

**`pynadath2002adjustable` author order.** I added this entry and wrote in the
bib comment that it was verified. I checked the title, volume and page range —
**not** the author order. The JAIR version of record is **Scerri, Pynadath,
Tambe**; the arXiv/DBLP mirror lists Pynadath first, and I copied the mirror.
This is your only AAMAS-community anchor, so the error sits on the citation
doing the most positioning work.

**`huang2026caller` is withdrawn.** I verified this key twice — title, authors,
arXiv ID — and never checked whether the paper was still live. It was withdrawn
2026-07-21 for *"flaws in experimental methodology and unresolved ethical issues
in data collection."* I cited it in the Introduction for the persistent-authorization
claim. Verifying that a paper exists is not the same as verifying it still stands.

---

## 6b. Limitation claims — what you say each paper *fails* to do

These are the riskiest sentences in a Related Work section: a reviewer who wrote
the cited paper will check them first. Verified against each abstract.

### WRONG — `betser2026agentrim`

> "AgenTRIM assigns risk levels to tools and applies stronger checks to riskier
> ones."

The abstract supports neither half. It says nothing about assigning risk levels
to tools, and nothing about differentiated checks. What it says:

> "Offline, AgenTRIM **reconstructs and verifies the agent's tool interface**
> from code and execution traces. At runtime, it **enforces per-step
> least-privilege tool access through adaptive filtering and status-aware
> validation of tool calls**."

Two problems. The mechanism is misdescribed — it is least-privilege enforcement
with adaptive filtering, not risk-level assignment. And it is *understated*:
"status-aware validation of tool calls" means AgenTRIM validates **calls at
runtime**, not tools. Your sentence makes it sound tool-level, which is the
weaker claim, and a reviewer will read that as either careless or convenient.

**Suggested replacement:** *"AgenTRIM reconstructs a tool interface offline and
enforces per-step least-privilege access at runtime through adaptive filtering
and status-aware validation of tool calls~\cite{betser2026agentrim}."* That is
accurate and still lands in your grouping, because least-privilege enforcement
is not a consequence magnitude.

### CONTESTABLE — `li2026conleash`

> "ConLeash checks whether an MCP call stays within an approved consent
> boundary. However, it does not estimate the risk or possible impact of a call
> that is already allowed."

The abstract describes *"a **risk lattice** to auto-permit safe calls within
known boundaries while escalating risks."* It does position calls on a risk
structure. Saying it "does not estimate the risk" invites a one-line refutation.

**The defensible version** — which you already use correctly in the Introduction:
the lattice ranks **distance from a consent boundary**, not **consequence
magnitude over the resource reached**. Say that instead of "does not estimate
the risk."

### CORRECT — `owireduashley2026severity`

> "Owiredu-Ashley instead grades the harm of actions recorded after execution."

Verbatim support: *"our contribution is a reusable, trace-grounded severity
instrument applied to the **actual actions recorded in existing red-team
logs**."* Exactly right.

One observation you may want to act on: it is an **evaluation rubric**, not a
defense. It grades trajectories in red-team logs to replace binary
attack-success rate; it never intervenes. Grouping it with STARS, AgenTRIM and
MCP-in-SoS as systems that "answer different risk questions" is defensible, but
it is not a competitor to your enforcement framework at all. It may serve you
better in the **evaluation** section as related severity-grading methodology.

### DEFENSIBLE — the three-way artifact claim

> "All three assess the server as an artifact, independently of the resources a
> given installation holds."

Holds for `kumar2026mcpinsos` (repositories) and `li2025privilege` (API-usage
measurement). Slightly loose for `huang2026auditing`, which runs **dynamic
sandboxed fuzzing** — that is execution, not static artifact analysis. The
substance survives (it still assesses the server, not a deployment's resources),
but "as an artifact" is the wrong word for a tool that executes the server.

### Already flagged in the main audit, restated because they are limitation claims

- **`zhang2026stars`** — your Related Work describes it correctly ("before
  execution"), which is precisely why it contradicts the novelty sentence
  elsewhere. See main audit §1.2.
- **`yang2026agenttrust`** — has a `review` verdict *and* an ordinal risk level,
  so "not magnitudes" is false. See main audit §2.1.

---

## 6c. Papers to add or reconsider

**Add — the most conspicuous omission.** ToolEmu (Ruan et al., ICLR 2024,
arXiv:2309.15817, ~464 citations) is the best-known prior attempt to attach a
graded severity number to an agent's tool action. A Related Work section arguing
that nobody grades agent-action severity, which does not cite it, is the first
thing a reviewer checks. Your distinction is real — it is post-hoc, emulated, and
has no resource-sensitivity input — but it has to be stated.

**Reconsider placement.** `owireduashley2026severity` is a measurement
instrument, not a defense (above).

**Already in your bib, never cited** — `li2025accesscontrol`, `shi2025sok`,
`almandalawi2025policyaware`. The last is notable: its stage 3 is literally
"Data classification. Resolve sensitivity labels", which is adjacent to your
central move. Engaging with it and showing it takes labels *as input* rather
than deriving them strengthens your claim; leaving it uncited in the bibliography
looks like an oversight.

---

## 7. What I did not do

- Did not edit either section's prose.
- Did not fix `mtguard2026`, the three duplicate pairs, or the v3.1/v4.0 mismatch.
- Did not add AgentBound to Related Work.
- Did not resolve the paywalled sources.

`refs.bib` changed only by addition: `zhao2025parasites`, `ni2010fuzzy`,
`shaikh2012dynamic`, `wunder2024cvss`, `first2023cvss`, `owasp2026aivss` — the
six entries your text cites that the file lacked.
