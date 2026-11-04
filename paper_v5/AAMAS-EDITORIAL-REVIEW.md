# AAMAS Editorial Review

A senior-editor pass on `paper_v5/main.tex`, structured as requested: research-story
reconstruction, AAMAS/notable-author writing-pattern research (web-verified), a
five-agent committee (Story Editor, Terminology Editor, Skeptical Reviewer,
Positioning Researcher, Story Architect), a synthesis that makes the committee argue
with itself, then section-by-section surgery. Nothing here has been applied to
`main.tex` — this is the diagnosis-and-plan pass, for you to triage before any
rewrite happens. Method note at the very end.

The framework's name in the compiled paper is **CARMA** (`\frameworkname`,
*Continuous Adaptive Risk Model for MCP Actions*) — used in the Introduction,
Methodology, and Implementation, but never in the Conclusion. That asymmetry
recurs as a finding below.

---

## 1. Executive diagnosis

Five problems are what stand between this draft and a strong AAMAS paper. None of
them require new experiments — all are fixable by rearranging, scoping, and naming
things the paper already has.

**A promise/delivery gap repeated in at least four places.** The Abstract
(line 105–106), the Introduction's methodology preview (line 251), Contribution
bullet 3 (261–263), and §6.3's cost/latency commitments all tell the reader the
Dynamic Scanner's runtime adaptation — including the headline "3,000 live
invocations across GitHub, Slack, and Calendar" — was *evaluated*. Section 7's own
second sentence concedes "Currently, we report only the results of the Static
Scanner," §6.2 admits accuracy against misuse traces is "left for subsequent
evaluation," and no cost or latency number appears anywhere in the compiled paper.
A reviewer who reads the Abstract's "3,000 live invocations" as evidence for the
dynamic layer will feel misled by the time they reach §6.2's two-sentence
disclaimer, three sections later.

**The paper's two genuinely novel, MCP-specific mechanisms are mis-filed as
engineering detail.** The evidence-precedence deterministic operation ladder
(bounds tool impact from MCP's self-reported annotations without letting them
alone promote a tool) and the config-free, traffic-derived argument-to-asset
resolver are both real, defensible, and specific to this problem — but neither is
named in the Contributions list, which instead foregrounds the domain-general
T·S·B product (the least original part of the design, read alone). A reviewer who
reads only Abstract + Contributions — the most common first pass — will underrate
the paper's actual novelty and reasonably conclude, as one committee member did,
that the core formula is incremental recombination.

**Concrete notational defects that read as carelessness.** The invocation tuple
`c`, used unglossed in the paper's two central dynamic-layer equations, is defined
only inside a commented-out, non-compiled block. `R_static(t,r)` at two locations
silently substitutes an undefined `r` for the `a` used everywhere else the pair is
written. And the stated bands High (50–99) and Critical (≥100) read as continuous
ranges, but full enumeration of the discrete 5×5×5 product shows only 30 achievable
scores — nothing lands in 81–99 or 101–124. Each is a one-sentence fix; together
they read, to a technical reviewer, as a formal apparatus that was drafted faster
than it was checked.

**A within-document contradiction about server trust.** Line 884 correctly frames
MCP tool annotations as "self-reported and imprecise" under the paper's own stated
benign-server assumption; two sentences later, line 910 calls the same annotations
"hints supplied by a possibly untrusted server" — importing adversarial-server
language the paper's own Threat Model explicitly excludes ("malicious MCP
servers… are outside the scope of this work," line 429). This is a local wording
bug, not a threat-model-direction problem, but it is exactly the kind of internal
inconsistency a careful reviewer checks a paper's claims against its own stated
assumptions for.

**Introduction pacing and a scattered running example.** The argument that MCP/agent
defenses answer a verdict rather than a graded consequence is made twice (lines
177–186, then again 223–236) with general access control sandwiched between, and
Related Work then re-argues most of the same ground a third time. Meanwhile the
paper's own best illustrative device — `write_file` against assets of varying
sensitivity — is scattered across four or five slightly different phrasings (lines
101, 240, 359, 409) instead of carried, as one example, from Introduction through
Methodology into a real, table-verified Results number.

---

## 2. The paper's real story

*"This paper is really about"* replacing the binary permit/deny verdict that
authorization gives an already-authorized MCP tool call with a graded, traceable,
pre-execution consequence estimate — computed per (tool, asset) pair from what an
organization already writes down about its own assets, not from a hand-built
inventory or an opaque model verdict.

The 5–8 sentence version a reader should retain a week later:

> AI agents connected to MCP servers now issue real, already-authorized tool calls
> against organizational files, repositories, channels, calendars, and databases,
> and the same call — `write_file`, `delete-event` — can be trivial or catastrophic
> purely depending on which asset it reaches and how much of that asset one call
> can touch. Existing defenses only answer whether a call is permitted (RBAC/ABAC,
> MCP-layer defenses) or grade something else entirely — a whole task, a server as
> a static artifact, a vulnerability class — none of them price the consequence of
> this specific, already-permitted call against this specific asset. CARMA closes
> that gap with a two-layer, server-side framework: a design-time Static Scanner
> multiplies three interpretable 1–5 factors — tool impact, organization-derived
> asset sensitivity, and blast radius — into a 1–125 score for every reachable
> (tool, asset) pair, with asset sensitivity read directly out of the
> organization's own prose classification policy rather than a hand-built numbered
> inventory. A request-time Dynamic Scanner then multiplies that static floor by a
> bounded, model-free runtime factor built from how much a concrete call deviates
> from the caller's own history, whether it works against the asset's stated CIA
> priority, and how novel the call or call sequence is — a factor that can only
> raise the score, never discount it, so unfamiliar behavior never quietly reads as
> safe. Two specifically MCP-grounded mechanisms carry the real technical weight: a
> deterministic operation ladder that bounds a tool's impact tier using the
> protocol's own self-reported annotations without ever letting them alone promote
> a tool to the top tier, and a zero-per-server-configuration resolver that
> discovers which call arguments name which organizational asset purely from
> observed traffic. Across 16 real deployments of 9 MCP catalogs, the static risk
> surface behaves the way the design intends — the same filesystem tool catalog
> produces a different top-risk asset under five different organizational policies,
> and public-data deployments produce zero High/Critical cells — but the dynamic
> layer, though fully specified and exercised on 3,000 live invocations, has so far
> been shown only to be fast and collectible, not yet accurate against real misuse,
> a boundary the Conclusion states honestly.

**The central tension:** authorization (RBAC/ABAC, and MCP's own annotation hints)
already tells an organization whether a call is allowed; the paper's whole argument
rests on the claim that "allowed" and "consequential" are orthogonal, and that
nothing upstream grades the latter. The wrinkle is that risk-adaptive access
control already conceded this exact point roughly two decades ago (Cheng 2007,
Kandala 2011) — so the paper has to hold two things at once without contradicting
itself: grading a permitted request is not a new idea, but nobody has built the
MCP-specific, per-invocation, organization-policy-grounded version of it. The
paper's credibility depends on stating the gap at that narrower, defensible scope
rather than the sweeping "no existing method" framing it currently uses.

**The key insight:** risk is not a property of the tool, the server, or the agent —
it is a property of the (tool, asset) relationship, and it decomposes cleanly into
three independently traceable, design-time-knowable questions (what can this
operation do; how much does the organization say this asset is worth, read from
policy prose; how much of it can one call reach), plus a fourth, request-time-only
question that is allowed only to escalate that baseline, never discount it, because
absence of behavioral history is not evidence of safety.

**The running example** (the committee's unanimous pick, replacing four or five
scattered variants currently in the draft): `write_file` applied to a
scratch/temporary file versus applied to an organization's credentials/secrets
store — already backed by a real, table-verified number (`write_file` ×
`security-keys` in `fs_corp_filesystem`, T=5·S=5·B=4=100), with the same tool's
top-risk target shifting to `card-vault`, `patient-charts`, `matter-files`, or
`unreleased-imagery` depending on which of five organizations' policies is in
force.

**The research gap, one sentence:** No existing method computes, before execution,
a graded consequence score for a concrete MCP invocation at the granularity of the
specific (tool, asset) pair it touches — RBAC/ABAC and MCP-layer defenses return a
verdict with no magnitude; risk-adaptive access control and its one agent-facing
instance (Fleming et al.'s TBAC) compute risk per task, not per call;
server-/tool-auditing frameworks score the artifact independently of which assets
a deployment actually holds; vulnerability-scoring systems grade a vulnerability
class, not an authorized operational call — and none of them derives that
consequence from an organization's own classification-policy prose rather than a
bespoke, hand-labeled inventory.

**The contribution, one sentence:** CARMA is a two-layer, server-side framework
that scores every reachable (tool, asset) pair of an MCP deployment at design time
as the product of an operation's impact, the target asset's organization-derived
sensitivity, and the invocation's blast radius — using a deterministic
evidence-precedence ladder that bounds, but is never solely promoted by, the
protocol's own self-reported tool annotations, and a config-free resolver that
discovers which call arguments name which organizational asset purely from
observed traffic — and then adapts that baseline at request time with a bounded,
model-free multiplier that can only escalate the static floor, never discount it.

**The takeaway, for a reviewer describing the paper to a colleague:** this is a
decomposition paper, not a verdict paper — its contribution is showing that MCP
invocation risk splits cleanly into three legible, differently-timed axes, derived
from policy an organization already writes rather than an inventory it must build,
with the honest caveat that the static half is empirically validated across real
deployments while the dynamic half is so far shown only to be feasible, not yet
accurate against independently verified misuse.

**Soul-clarity gate: passed.** Every committee member, once checked directly
against `main.tex`, converges on the same core claim and the same concrete, fixable
list of problems. None of these is a case where the paper doesn't know what it's
about — they're cases where the text hasn't yet been arranged to say it as cleanly
as the underlying idea supports.

---

## 3. What the reader should feel

The first paragraph should not open on the amorphous, widely-shared intuition that
"agents now act, so this is risky" — it should open on one concrete invocation (a
file-write reaching a secrets store versus a scratch file) that makes the reader
feel the specific gap before any terminology arrives. From there, understanding
should sharpen in three steps: first, that "permitted" and "consequential" are
orthogonal, which authorization alone cannot express; second, that consequence
itself decomposes into three legible, independently traceable axes — what an
operation can technically do, how sensitive the specific asset is per the
organization's own stated policy, and how much of that asset one call reaches —
rather than being one opaque number; third, that this decomposition is computed at
two different times because the evidence for it becomes available at two different
times, with the runtime half constrained to only ever escalate a baseline, never
discount it. By the contribution sentence, "risk assessment for MCP invocations"
should no longer read as a generic security phrase but as a specific, falsifiable
commitment: decomposable, traceable to organization-authored policy text, and
honest about which half of that commitment — static — is empirically validated
versus which half — dynamic — is so far only shown to be feasible.

---

## 4. AAMAS writing patterns discovered

Structural and narrative techniques found by directly fetching real AAMAS papers
(2023–2026) and closely adjacent agent-safety/security venues, verified rather than
paraphrased from search snippets. (Terminology-specific patterns — how the field
actually uses individual words like *risk*, *policy*, *capability* — are folded
into the terminology audit in §5 instead of repeated here.)

**Two-stage opener: an unremarkable everyday scenario first, then a named real
incident to raise the stakes — before any formal terminology.**
> "In the digital era, we are surrounded by online services that require various
> aspects of data usage… Users are unlikely to trust these digital service
> providers due to concerns about privacy breaches exemplified in the Cambridge
> Analytica scandal…"
— Xu, Dennis & Mustafa, AAMAS 2024. The first sentence costs the reader nothing;
only after that low-friction entry does the paper reach for an already-famous
incident to convert an abstract risk into something the reviewer already believes
is serious.

**Scale-first opener: state the problem's breadth as the literal first sentence.**
> "Online systems are used by billions of users who interact with each other,
> share data about themselves and also other people."
— Ogunniye & Kökciyan, AAMAS 2023. A magnitude claim, not a narrative — tells the
reviewer in one clause the paper is not about an edge case, and reaches its gap
statement by the end of the same paragraph.

**Concrete illustrative example as the literal opening sentence, before any
formalism.**
> "Imagine that you are a security guard monitoring a camera feed, and you witness
> a person approaching a locked door."
— Zhang, Kemp & Lipovetzky, AAMAS 2024 Best Paper. Puts the reader inside the exact
judgment task the paper formalizes later, using a scenario they already have
working intuitions about.

**Hold formal apparatus until after the motivating narrative and the problem
statement are both already on the page.**
> "In this paper, we address the trustworthiness issues in agents for privacy
> protection… We use a cognitive agent programmed in the Beliefs-Desires-Intentions
> (BDI) paradigm…"
— Xu, Dennis & Mustafa, AAMAS 2024. BDI — the paper's central formalism — is not
named until after a full paragraph of motivation and an explicit problem sentence.
The formalism arrives as a tool for an already-stated problem, not furniture the
reader must inventory first.

**Ground an abstract protocol in one concrete worked trace immediately after
defining it, before arguing anything is missing.**
> "Figure 1 illustrates the client-server workflow in a typical MCP interaction.
> When a user requests current market trends and prices, the host forwards the
> query to the client, and the client communicates with the server via the MCP
> Protocol…"
— Jing et al. (MCIP), EMNLP 2025. Shows the reader exactly how the system is
supposed to work, step by step, before saying what's unguarded — the gap that
follows has a concrete target to attach to.

**The single contrastive connective ("However, …") as the whole hinge between an
uncontested prior-work sentence and the paper's stated limitation.** Verified
recurring verbatim across MCIP, Progent, and ToolEmu. One word carries the entire
argumentative turn from "here is what the field agrees is true" to "here is what
that agreement does not cover" — its absence is often what makes an introduction
read as a survey rather than a paper with a claim.

**State the gap as a named comparison against specific prior systems, not a
generic "existing work is insufficient."**
> "Though implemented with different settings, both ToolEmu and AgentMonitor
> utilized LLMs as safety monitors to identify the risky actions of LLM agents.
> However, judging whether agent actions are safe in the context of multi-turn
> interactions… remains unclear…"
— Yuan et al. (R-Judge), Findings of EMNLP 2024. Naming specific systems and
stating precisely what neither establishes is far harder to dispute than an
unnamed "prior work has limitations," and does double duty as related-work
coverage inside the introduction itself.

**Enumerate the reasons a problem is hard as explicitly named sub-challenges
(First/Second/Finally) before presenting the solution.**
> "Securing AI agents is challenging for several reasons. First, agent behavior is
> inherently non-deterministic… Second… Finally…"
— Shi et al. (Progent), 2025. Lets the solution section map back onto each item
one at a time — easier for a reviewer to check for completeness, and signals the
authors understood the problem's structure before proposing to solve it. **This
paper currently has no equivalent paragraph** — see §6 and §10 below; it is the
single missing beat identified across the whole committee.

**A "first" novelty claim scoped narrowly to the specific target, paired
immediately with an admission that the general class already exists.**
> "We propose ToolHijacker, the first prompt injection attack to tool selection in
> LLM agents." — elsewhere conceding prior injection attacks exist but are
> "suboptimal in tool selection."
— Shi et al. (ToolHijacker), 2025. Scoped narrowly enough to survive a reviewer
mentally searching for counterexamples.

**"To (the best of) our knowledge" attached to a narrow, checkable sub-claim, never
the paper's overall contribution.**
> "To our knowledge, this is the first benchmark dataset curated to assess risk
> awareness of LLMs for agent safety." (R-Judge) / "To the best of our knowledge,
> however, there has been little work on the impact of solvability in
> goal-recognition scenarios." (AAMAS 2024 Best Paper — note "little," not "no.")
Both hedges protect a claim narrow enough to plausibly be true, rather than an
unfalsifiable sweeping one. **This is the exact fix needed for main.tex line
223–224** — see the Related Work and Introduction entries in §8 and §11.

**Quantify a method's own failure rate inside the paper's own words, rather than
gesturing at "limitations."**
> "…this defense fails… when the tools required to solve the task are also
> sufficient to carry out the attack (this is true for 17% of our test cases)."
— Debenedetti et al. (AgentDojo), NeurIPS 2024. A number survives scrutiny; "has
some limitations" invites the exact question a number answers pre-emptively.

**Separate an evaluation's two axes so success on one is never mistaken for
success on both.**
> "the helpfulness score measures how well the LM agent fulfills the user
> instruction… while the safety score assesses the potential risks…"
— Ruan et al. (ToolEmu), ICLR 2024. Directly transferable to this paper's own
static-feasibility-vs-dynamic-accuracy split — see the Evaluation/Results fixes
below.

**Splitting a threat model into orthogonal origins — attacker-caused vs.
no-attacker — instead of one undifferentiated "risk" bucket.**
> "Intended Attacks: the outer attackers attempt to manipulate the agents… Unintended
> Risks: … agents may cause safety issues even if there are no malicious attacks."
— Yuan et al. (R-Judge). A taxonomy move directly transferable to any paper (this
one included) that needs to separate an adversarial threat model from an
accidental-misuse one within the same framework.

**Contributions as prose with ordinal adverbs, reading as a connected argument
rather than a bulleted checklist.**
> "Our work makes several kinds of contributions. First, we carry out a
> comprehensive behavioral experiment… Second, we expand upon the planning
> model… Third, we introduce a human-like goal recognition algorithm…"
— Zhang, Kemp & Lipovetzky, AAMAS 2024 Best Paper. In a page-limited venue, a
bulleted list can read as padding; ordinal prose keeps the same checkable
structure — one distinct deliverable per sentence — while reading as one argument.

**A paragraph can be a single sentence when its only job is to point at a
figure.** Confirmed as a genuine, standalone paragraph (not a fragment) in the same
AAMAS 2024 Best Paper — evidence that in an 8-page format, paragraphs are keyed to
one move, not a minimum length.

**Two admired opening sentences, traced to their real source.** Both of the
sentences you flagged as models —
*"Over the past year, the Model Context Protocol (MCP) [1], [2] has rapidly
emerged as a cornerstone for connecting large language models to the real
world…"* and
*"The Model Context Protocol (MCP) is an open, JSON-RPC-based communication
standard introduced by Anthropic in late 2024 [1]."* —
are **verbatim (first) and near-verbatim (second, "standard" vs. "protocol")**
from the same paper: **Li et al., "We Urgently Need Privilege Management in MCP: A
Measurement of API Usage in MCP Ecosystems," IEEE MASS 2025 (arXiv:2507.06250)** —
already cited in this project's own bibliography as `li2025privilege`. The two
sentences are two different techniques in the same paper, not one continuous
quote: the first is a three-beat *stakes → mechanism → pivot* Introduction opener;
the second is from a dedicated **"MCP in a Nutshell" background subsection**,
holding the Introduction's rhetorical framing separate from the protocol's precise,
citable technical definition. Notably, `li2025privilege`'s own opener uses exactly
the inflated register (*"cornerstone," "rapidly emerged," "fueled a wave of
innovation"*) this paper's terminology audit (§5) confirms `main.tex` correctly
avoids — worth knowing precisely because it means the risk of drifting toward that
register on a future editing pass is real, not hypothetical.

---

## 5. Terminology audit

Every term below was checked directly against `main.tex` occurrence counts and, for
comparison, against real papers already in this project's own corpus (fetched, not
assumed). Positive findings (terms already used correctly and consistently) are
included too, since the task called for auditing every important recurring
concept — and because they're the model to imitate for the weaker rows.

| Term | Current usage | Problem | Recommended | Evidence |
|---|---|---|---|---|
| **invocation / request / call / operation** | Four nouns (77/23/54/58 occurrences) used interchangeably for the same scored event, often in adjacent sentences. The one passage that gave each a distinct referent is commented out. | MCP's own spec treats "request" (the JSON-RPC message) and "invocation" (the act of sending it) as distinct; "operation" is the server-side effect. Implementation *does* use "request" narrowly and correctly, inconsistent with the rest of the paper. | Pick "invocation" as canonical (already the title's word); reserve "request" for the literal message, "operation" for the server-side effect. | STARS (arXiv:2604.10286) deliberately uses both "request" and "invocation" in one sentence to mark different referents; MCP spec: "clients send a `tools/call` request… to invoke a tool." |
| **action** | Appears live only twice outside citations/quotes: in CARMA's own name expansion ("…for MCP *Actions*") and "MCP-related actions." A third sense means the enforcement response. | The acronym promises "Actions" but the body almost entirely avoids the word for the scored object. | Either rename the expansion to match the paper's actual noun ("…for MCP Invocations"), or explicitly gloss "action" as synonymous with "invocation" once, early. | Owiredu-Ashley (arXiv:2607.07474), ToolEmu, R-Judge all default to "action" (RL/decision-theory lineage) — the word is defensible, just inconsistent with this paper's own body-text choice. |
| **impact** (Tool Impact `T(t)` vs. FIPS impact) | "Impact" literally names `T(t)` (defined as asset-*independent*), while the same word, via the FIPS 199/SP 800-60 citations, is separately used for how `S(a)` is derived — the opposite, asset-*dependent* quantity. | A reader who follows the FIPS citation attaches "impact" to asset-side consequence first, then meets a same-named, asset-independent factor. | Rename `T(t)` (e.g. "operation severity" / "operation class"); reserve "impact" for the FIPS-grounded asset-side quantity. | Verified directly: main.tex l.589–590 (T(t) asset-independent) vs. l.635–637, l.249 ("impact categories" for S(a)). |
| **risk vs. severity vs. consequence** | "Risk" dominant (142×) for the paper's own output; "severity" only ever describes *other* papers' scores, never this paper's, even though the file's own top-of-file comment calls the project "severity scoring." | `R_static = T·S·B` has no likelihood term — by the field's own convention, that's severity, not risk. | Name the static score "severity" (or state once, explicitly, that "risk" is used as a synonym for severity with no independent likelihood estimate). | Cao et al. (arXiv:2411.14515) consistently names the pure consequence axis "severity"; MCP-in-SoS (already cited, l.348) explicitly derives risk from likelihood *and* severity as separate terms. |
| **policy** | 23 occurrences, two senses never disambiguated: (1) an org's prose classification document; (2) an enforcement/authorization ruleset. | The paper's own contribution partly depends on this distinction (it disclaims providing enforcement while grounding itself in a classification document) — conflating the words risks a reviewer conflating the concepts. | Always qualify: "classification policy" (sense 1, already majority usage) vs. "enforcement/authorization policy" (sense 2). | Progent (arXiv:2504.11703): "a security policy consisting of symbolic rules" — the opposite sense, already coexisting unresolved in this paper's own reference set. |
| **capability** | 19 occurrences, loose generic-English synonym for "tool"/"permission," never MCP's own normative sense. | MCP's spec reserves "capability" for a declared, top-level protocol feature object (e.g. `{"tools": {...}}`), not an individual tool. | Replace generic uses with "tool" or "permission"; reserve "capability" for the protocol object if ever discussed. | MCP spec: "Servers that support tools MUST declare the `tools` capability" — a feature-flag object, not a tool. |
| **blast radius** | Defined once, then used unmarked 15× as settled jargon, including inside the formal S=5 tier definition. | Not native AAMAS/academic terminology — practitioner/industry glossary origin. | Mark it explicitly on first use ("we borrow the practitioner term…"), following the field's own precedent, rather than a full synonym swap (unnecessary — the term is genuinely the clearest available). | Shi et al., "SoK: Trust-Authorization Mismatch" (arXiv:2512.06914, already cited): "We adopt the concept of 'blast radius' to characterize…" — explicitly flagged even in a terminology-systematization paper. |
| **crown jewels** | Used once, unmarked, inside the formal S=5 definition. | Same borrowing-discipline gap as blast radius, at the one place precision matters most (a load-bearing category boundary). | Drop (redundant with "credentials, regulated data") or mark as illustrative, not part of the formal definition. | Same SoK precedent as above. |
| **exposure** (in "Novelty and Exposure") | Named as half the third dynamic factor, but the implementation text only ever explains novelty. "Exposure" is never independently defined anywhere. | A reviewer cannot answer "what does exposure add beyond novelty?" from the paper's own text. | Rename to "Novelty (N)" alone, or add one sentence defining exposure's independent contribution. | No settled term-of-art for "exposure" found in the adjacent literature — the burden is on this paper to define it locally, which it currently doesn't. |
| **misuse** | Defined to fold in "compromised behavior" and "malicious intent" alongside benign error/delegation — but Related Work separately excludes server-to-agent attacks. | Field convention treats misuse/attack as opposites: misuse needs no adversary; a compromised agent is the target of an *attack*, not an instance of misuse. | Narrow to the field-standard sense (authorized, uncompromised actor, harmful outcome); flag compromised-agent scenarios as a boundary case rather than folding them in. | AgentHarm (arXiv:2410.09024): "misuse" is the term-of-art specifically for harm from an already-authorized actor, no adversary required. |
| **framework / methodology / method** | "Framework" 42×; Contributions list uses three near-synonyms across its own three bullets ("risk-analysis methodology," "risk-assessment framework," "evaluation methodology"); §6 reverts to "method" as an unplanned fourth variant. | "Framework" titles six-plus unrelated systems in this paper's own bibliography — risks reading as content-free. | Keep "methodology" strictly for the abstract method (Contribution 1), "framework"/"system" for the concrete implementation (Contribution 2); drop "method" as a free variant. | This project's own refs.bib, read directly: six-plus "…Framework" titles for systems sharing almost nothing else. |
| **runtime vs. request-time** | Glossed three ways for one instant: "At runtime" (Abstract, Threat Model, §7, Fig. 1 caption), "At request time" (Introduction's parallel sentence), "request-time evidence" (§4.2's own topic sentence). | Silent vocabulary swap within one short passage; the reader has to infer the three phrases denote the same instant. | Standardize on "runtime" (more frequent, pairs naturally with "design time"); state explicitly if "request-time" is meant to name something narrower. | The nearest self-described competitor, Huang et al. (arXiv:2603.21641): "static pattern matching… and dynamic sandboxed fuzzing" — static/dynamic as primary, design-time/runtime as gloss. |
| **context** | Always qualified ("execution context," "runtime context," "organizational context") — no problem in practice. | MCP's own name claims the bare word "context" for a different concept (the informational payload given to a model). | No change required; optionally one clause noting the two senses are unrelated. | MCIP (EMNLP 2025) invokes Nissenbaum's "contextual integrity" — a *third*, unrelated sense of "context" in this exact citation neighborhood. |
| **asset (vs. resource)** | "Asset" used exclusively (146×); "resource" never appears. | None — positive finding. | Keep as-is; optionally note the deliberate avoidance of MCP's own "Resource" primitive. | MCP spec: "Resource" is a distinct, URI-addressable protocol primitive, separate from "Tool" — this paper avoided a real collision. |
| **authentication / authorization / access control** | Correctly and consistently distinguished throughout. | None — positive finding, this paper's cleanest terminology usage. | Use as the model for the weaker rows above. | Matches Shi et al.'s SoK paper's own precise authentication/authorization split exactly. |
| **mechanism** | Used sparingly (3×), each time naming one specific, singular component — never a filler synonym for "method." | None — positive finding. | Model for the framework/methodology discipline above. | Progent: "This deterministic update mechanism…"; SoK: "Trust as a mediating mechanism…" — same narrow, single-component usage. |
| **static / dynamic** | Primary, consistent adjective pair (62/43 occurrences), no synonym drift. | None — positive finding, the paper's most disciplined terminology choice. | No change; matches the field's own self-description convention exactly. | Huang et al.'s own self-description: "static pattern matching… and dynamic sandboxed fuzzing." |
| **architecture** | Never appears in body prose — only in figure filenames/labels. | Missed opportunity, not an error: a genuine structural claim (two differently-timed pipelines feeding one score) exists but is invisible to the reader. | Use explicitly and sparingly in the Figure 1 caption or §4 Overview if a structural claim is intended. | MCIP: "Its decentralized architecture, which separates clients and servers, poses unique challenges…" — precise use for an actual topology claim. |
| **protocol / tool** | Used consistently in normative MCP senses throughout (9×/139×). | None — positive finding, no collision or drift found anywhere. | Model for tightening the invocation/request/call cluster and "capability." | MCP spec's own normative vocabulary, reused correctly. |
| **unsafe / undesirable / harmful / anomalous action** | Only "harmful" appears, once. | None — positive finding; these four adjectives are *not* a settled four-way taxonomy across the literature (each sub-community defaults to a different one). | If a future revision needs more than one severity adjective, define the chosen set explicitly rather than importing all four as if already agreed. | Cao et al. defaults to "anomalous"/"severity"; AgentHarm defaults to "harmful"/"misuse" — neither treats the four as interchangeable. |
| **Inflated/journalistic language** ("cornerstone," "rapidly emerged," "powerful," "unprecedented," "dangerous," "intelligent"…) | None appear in an inflated sense anywhere. "Critical" appears only as the literal S=4/S=5 band name; "fundamental" only as a transition adverb. | None — clean, verified-absent finding, worth stating explicitly since the risk of drift is real (see §4's traced-source finding above). | Keep this discipline through future revisions, especially the Introduction's opening sentences. | The admired opening example (§4) is itself a verbatim instance of exactly this register — already in this paper's own bibliography. |
| **Generic AI-writing filler** ("plays a crucial role," "presents unique challenges," "to bridge this gap," "a comprehensive framework," "it is worth noting") | None of these five stock phrases appear anywhere. | None — clean, verified-absent finding. | Maintain in future drafting/polishing passes, where filler is most often introduced. | Cross-checked against `CRAFT-REVIEW.md`'s independent 37-finding pass, which didn't flag this category either — a genuinely independent clean result. |

---

## 6. Introduction surgery

Paragraph-by-paragraph, read start to finish including the Abstract as paragraph
zero. For each: the question in the reader's mind before it, the question it
answers, the question it *should* create, and whether the next paragraph actually
answers that.

**Abstract (99–106).** *Before:* what is this paper about? *Answers:* the
asset-consequence problem plus a two-stage-framework preview and evaluation scale.
*Should create:* you told me 3,000 live invocations exercised the Dynamic
Scanner — does the paper report its accuracy, or only that it ran? **Broken:**
Intro P1 doesn't pick up this thread at all — it restarts from a generic "AI agents
act" framing — and the specific question the Abstract plants is never resolved
until Results says, negatively, "we report only the results of the Static
Scanner." Scope the Abstract's claim to match what §7 delivers, or don't make it.

**P1 (166–175).** *Answers:* the specific defect in MCP's own design — annotations
describe the tool, not the asset a call reaches. *Should create:* what exists today
to catch this, and why isn't it enough? **Broken:** the next paragraph opens on the
*opposite* threat direction (malicious servers/tools harming agents) before
reaching on-topic material — a detour the reader has to wait through. This is also
where the concrete opener (public doc vs. regulated asset, currently exiled to a
comment and restated abstractly eight paragraphs later) should have appeared.

**P2 (177–186).** *Answers:* the nearest MCP-specific literature diagnoses
vulnerabilities/violations, not per-asset consequence. *Should create:* "our work
provides this estimate" — show me how, now. **Broken:** this is the first of three
places the paper asserts its own contribution before presenting it (again at P6's
"no existing method…", again at P7's "our approach instead computes…"). Each
restatement of "no one does X, we do X" without yet showing X dilutes the eventual
reveal, which doesn't land until P8 — five more paragraphs of negative-space
literature later.

**P3 (189–198).** *Answers:* defines misuse cause-agnostically, states the paper's
consequence-over-intent stance, and — in passing — previews the five-input
decomposition (tool, asset, arguments, context, history) without naming it yet.
*Should create:* access control already exists precisely to gate whether a caller
may act — why doesn't it solve this? **Not broken** — P3→P4 is one of the paper's
cleanest joints.

**P4 (202–209).** *Answers:* the sharp verdict-vs-magnitude distinction — AC
answers "may it?", never "how dangerous is it?" *Should create:* has anyone already
tried bolting a risk value onto an access-control decision? **Not broken** — P4→P5
is the paper's other clean joint.

**P5 (212–220).** *Answers:* yes, on both counts — RAdAC generally, Fleming/TBAC
for agents specifically — but neither is MCP-specific or per-invocation. *Should
create:* precisely what does Fleming still miss for MCP, and are there OTHER
MCP/agent-specific systems that also fall short? **Broken:** P6 answers a broader
question than the one P5 provoked — instead of tightly closing the Fleming gap, it
re-opens the MCP/agent-defenses literature already covered in P2 (Progent,
MiniScope, AgenTrim, ConLeash, IGAC, AgentTrust, STARS, NEXUS), material that
belongs adjacent to P2's MTGuard discussion. This is the exact
MCP-defenses→general-AC→MCP-defenses-again interleaving diagnosed in §1.

**P6 (223–236).** *Answers:* no — the full spread of MCP/agent-specific runtime
defenses also stops at a permit/suspicious/block verdict. *Should create:* setting
access-control-shaped defenses aside — is there a severity-scoring tradition (like
CVSS) that might already solve this? **Not broken locally** (P7 pivots correctly)
but this paragraph's *content* is the redundant half of the P2/P6 split — see
Example Rewrite E in §11.

**P7 (237).** *Answers:* no — CVSS/AIVSS grade a vulnerability class, not a
concrete call's consequence to a specific asset. *Should create:* I've now seen six
paragraphs of negative results across three literatures. Show me, concretely, what
you compute. **Not broken locally** — P8 delivers. But structurally, by this point
the reader has held an abstract complaint for ~650 words and three restated
versions of "our work does X" without ever seeing X.

**P8 (240–245).** *Answers:* names the three static factors via one intuitive
example (`read_file` on a public document vs. regulated data), plus gestures at the
dynamic adjustment. *Should create:* what do you call this, and what's it for?
**Not broken** — clean joint into P9. Minor note: this is the paper's best
illustrative example, but it's introduced only in passing rather than being the
*same* example carried from paragraph 1 through Methodology into the real Table 2
number.

**P9 (247).** *Answers:* names CARMA and its one-line purpose. *Should create:*
mechanically, how do the two stages work and combine? **Not broken** — P10
delivers exactly this.

**P10 (249).** *Answers:* the formula-in-words for both stages, and the novel
sensitivity source (policy prose, not a manual inventory). *Should create:* has
this actually been built and run against real servers and policies — and will
*both* stages be evaluated? **Not broken locally** — P11 addresses it directly, but
P11's *answer* is where the paper's largest structural problem is seeded.

**P11 (251).** *Answers:* claims yes — both the static risk surface AND the
runtime adaptation are examined. **Broken — this is the seed of the paper's single
largest promise/delivery gap.** "Examines… the runtime adaptation of these scores"
directly promises evaluated dynamic-layer results that Section 7 does not deliver.
No paragraph anywhere in the Introduction, Related Work, or Methodology flags that
the dynamic half is feasibility-only — the reader discovers this unassisted, ~900
words into Results.

**P12 / Contributions (253–263).** *Answers:* three bullets, formally closing the
Introduction. **Broken, two compounding failures:** (a) bullet 2 says only
"produces interpretable risk scores" — the two mechanisms that actually defend the
paper against an "incremental recombination" reading (the evidence-precedence
ladder, the traffic-derived resolver) are never named here, only in Implementation,
several sections later; (b) bullet 3 doubles down on "controlled evaluation of…
the dynamic adaptation," reinforcing rather than scoping P11's overclaim. The
Introduction closes with its two most consequential open questions — "what's
really novel?" and "will the dynamic layer's accuracy actually be reported?" —
both left hanging.

**Cross-paragraph synthesis.** Roughly two-thirds of the joints (P3→P4, P4→P5,
P6→P7, P8→P9→P10) are causally tight and should be preserved as-is — each reader
question genuinely forces the next paragraph. Four defects break the rest, in
priority order: **(1) promise/delivery** — scope the claim at first mention, not
900 words later (highest-severity, single-sentence fix); **(2) pacing** — the
concrete example belongs in paragraph 1, not paragraph 8, cutting six paragraphs
of negative-space review to three or four (highest-leverage rewrite); **(3)
structure** — merge the two non-adjacent MCP-defenses passes; **(4) novelty
visibility** — name both real mechanisms in Contributions, not just Implementation.

---

## 7. Remaining sections

More compact than the Introduction pass, same categories (STORY / TERMINOLOGY /
LOGIC / TECHNICAL_PRECISION / CLAIM / CITATION / REDUNDANCY / ORDER / TRANSITION /
REVIEWER_CONFUSION).

### Related Work (lines 326–412)

**Purpose:** triangulate against every adjacent literature that could plausibly
already solve this, state precisely why each doesn't, fold in FIPS/NIST as
borrowed methodology (not a competitor), and close with one compound, defensible
gap statement.

**Current story:** correctly scoped but structurally sprawling — nine to ten
paragraphs against the author's own commented-out four-strand plan, ~789 words
against its own 600–700 budget.

**Problems:** *(REDUNDANCY)* three passages restate arguments and citations
already made in the Introduction almost verbatim (RBAC/ABAC+RAdAC+Fleming;
CVSS/AIVSS; IGAC's description). *(REDUNDANCY)* MCP-in-SoS is independently
described in two non-adjacent paragraphs. *(REDUNDANCY)* the same
"trivial-vs-critical asset" example recurs twice within 50 lines, with different
nouns. *(ORDER)* server-weakness/audit citations are split across two non-adjacent
paragraphs with the tool-poisoning contrast sandwiched between. *(STORY)* ConLeash
sits in its own orphan paragraph despite belonging with the Defenses paragraph —
the Introduction already groups it there. *(TRANSITION)* the FIPS/NIST paragraph
interrupts the risk-scoring strand without marking its different rhetorical
function (methodology borrowed from, not work distinguished against). *(LOGIC)* Ni
et al. and Shaikh et al. get no stated limitation, unlike Kandala et al. in the
same paragraph. *(LOGIC)* the central tension (RAdAC already conceded
risk-grading; only the MCP-specific per-invocation version is missing) is never
stated explicitly. *(STORY)* the closing sentence resolves only the last strand,
not the compound four-strand gap the paper's contribution needs. *(TECHNICAL_
PRECISION)* "an agent sends a call that may harm the MCP server" (336–337) can be
misread as an attack *on* the server — contradicting the fixed threat model.
*(TERMINOLOGY)* "capabilities and weaknesses of MCP servers" collides with MCP's
normative term. *(REVIEWER_CONFUSION)* AgentTrust and NEXUS are cited in the
Introduction's defenses list but never individually elaborated here, unlike every
other citation in that list. *(CLAIM)* "our work instead scores each MCP
invocation using its runtime details" states the Dynamic Scanner's contribution in
the same unqualified present tense as the Static Scanner's, reinforcing the
paper's largest promise/delivery gap.

**Structural changes:** MOVE the server-audit citations to join Li/Huang/MCP-in-SoS
in one place; MOVE ConLeash into the Defenses paragraph; MOVE FIPS/NIST to close
the risk-scoring strand (or relocate to Methodology, where it's actually used).
DELETE ConLeash's private gap sentence once merged; DELETE the redundant second
MCP-in-SoS description; DELETE one of the two near-duplicate illustrative
examples. MERGE the RBAC/ABAC+RAdAC+Fleming discussion with the Introduction's
near-identical version (full detail stays here, Introduction trims to a gesture);
same for CVSS/AIVSS and IGAC. ADD one bridging sentence stating the central
tension directly; ADD individual treatment of AgentTrust/NEXUS or drop them from
the Introduction's list; ADD a compound four-strand closing gap statement. SHORTEN
the risk-adaptive-AC paragraph and the section overall toward its own planned
budget. EXPAND the Fleming limitation sentence slightly and the final paragraph
into the compound synthesis.

**Sentence changes** *(sample; full set in the source data)*: "we study the
opposite direction: an agent sends a call that may harm the MCP server" →
"…an already-authorized call that may harm the organizational assets and services
the server manages, not the server itself" *(direct evidence: fixed threat model)*.
The closing sentence rewritten as a compound four-part gap statement spanning all
four strands *(direct evidence: story synthesis's research-gap sentence)*.

### Threat Model (lines 416–429)

**Purpose:** state, once and precisely, who/what is protected, what hazard is
assessed, the one precondition the paper's central argument depends on (scored
calls have already passed authorization), and what evidence exists at which of the
two operating times.

**Current story:** a dangling reference ("this evidence," line 427, whose
antecedent is commented out), a benign-server assumption that never actually calls
the *server itself* protected, and — critically — nearly every substantive
assumption the rest of the paper depends on already exists, drafted, in
commented-out LaTeX immediately below the compiled paragraphs.

**Problems:** *(LOGIC)* the dangling "this evidence" reference. *(CLAIM)* the
section never states, anywhere compiled, that the framework only scores
already-permitted invocations — the `perm(c)=1` precondition the paper's entire
"permitted ≠ consequential" argument depends on sits only in a commented-out
block. *(STORY)* the section largely re-derives, less precisely, what the
Introduction already says at greater length — undercutting the reason for a
separate formal pass. *(REDUNDANCY)* the misuse-definition paragraph makes the
same "still valid despite being harmful" point twice in one paragraph.
*(TERMINOLOGY)* the topic sentence itself — "misuse of legitimate MCP
capabilities" — collides with MCP's normative "capability." *(TERMINOLOGY)*
"operation" used 14×/"invocation" 0×, despite invocation being the paper's
canonical term elsewhere, with "operation" doing two different jobs in adjacent
sentences of the very section meant to fix this vocabulary. *(CLAIM)* the server
is called "benign" but never explicitly named "protected" — a precision gap
against the paper's own non-negotiable threat-model direction. *(TRANSITION)* the
section ends on a backward-looking exclusion list rather than the
evidence-timing paragraph that would flow directly into Methodology. *(STORY)* a
commented-out misuse taxonomy (operation/asset/scope/parameter/behavioral) maps
almost one-to-one onto the T/S/B and D/A/N factors introduced later — cut, so
those factors arrive in Methodology unmotivated by the threat side. *(LOGIC)* the
explicit "we do not infer intent" disclaimer — exactly the fixed threat model's
own framing — is commented out and never compiled.

**Structural changes:** MOVE the design-time/runtime paragraph after the
out-of-scope paragraph, so the section ends on a forward pointer into Methodology
instead of a disclaimer. DELETE the redundant "in contrast to attacks that
compromise the server" clause (fully superseded by the dedicated out-of-scope
sentence two lines later). MERGE the two "still valid despite harmful" sentences.
ADD the `perm(c)=1` precondition explicitly (see Example Rewrite A, §11); ADD an
antecedent for "this evidence"; ADD a condensed version of the misuse-vector
taxonomy; ADD the intent-disclaimer sentence. EXPAND the benign-server sentence
into an explicit protected-party statement naming the server; EXPAND the topic
sentence to swap "capabilities" for "tools" or "invocations."

### Methodology

**Purpose:** formally deliver the contribution precisely enough that a reviewer
trusts the Results numbers, understands the static/dynamic split as architectural
rather than convenient, and can see — ideally through the paper's own running
example — that the three-axis decomposition is the load-bearing idea.

**Current story:** legible as a formula specification, but reads as existing to
define equations rather than to prove the paper's central claim. Never
instantiates the running example, never surfaces either of the two genuinely
novel mechanisms even in passing, and depends on a symbol (`c`) that is never
actually defined in the compiled text.

**Problems:** *(LOGIC)* the invocation tuple `c` — used unglossed in the two
central dynamic-layer equations and again at lines 757, 782 — is defined only in
a commented-out subsection. *(TECHNICAL_PRECISION)* `R_static(t,r)` at two
locations vs. `R_static(t,a)` in Eq. 1 and everywhere else — `r` is never defined.
*(TECHNICAL_PRECISION)* the stated bands overstate the resolution a discrete
5×5×5 product can actually deliver (nothing populates 81–99 or 101–124).
*(STORY)* the two defensible novel mechanisms are invisible here even
conceptually — Tool Impact never mentions the evidence-precedence rule; Novelty
and Exposure never signals the order-sensitive sequence evidence lives inside it.
*(TERMINOLOGY)* "Novelty and Exposure" defines only novelty. *(TERMINOLOGY)*
"request-time evidence" is an unglossed third temporal variant against seven
uses of "runtime" in the same section. *(TERMINOLOGY)* "capability" used three
times as a loose synonym, including in the sentence stating what `R_static`
formally represents. *(CLAIM)* `R_static` is called a "risk score" throughout with
no statement that it's a pure consequence/severity magnitude with no likelihood
term. *(STORY)* the static/dynamic split's justification gives equal narrative
weight to an epistemic reason (information timing) and a practical one
(computational cost) without stating which is the actual architectural claim.
*(STORY)* the paper's clearest illustrative device never appears in Methodology —
T, S, B, and Eq. 1 are defined only through abstract bulleted tiers. *(REVIEWER_
CONFUSION)* asset resolution is presented as an already-solved input step, with
no signal it's one of the paper's fully novel mechanisms. *(CLAIM)* "bounded
below by 1" is asserted with no explanation, within Methodology itself, of what
makes it true by construction. *(TECHNICAL_PRECISION)* the choice of
multiplicative aggregation over alternatives (sum, weighted sum, max) is never
justified, despite being the central formula and, per the committee, the least
MCP-specific design element.

**Structural changes:** MOVE the numeric band cutoffs out of Risk Output into
Evaluation/Results, next to the score distribution they describe; MOVE a
two-sentence conceptual preview of the evidence-precedence rule forward from
Implementation into §4.2.1. MERGE the remaining Risk Output content into a short
closing paragraph of Dynamic Risk Adaptation once bands relocate. ADD the missing
formal definition of `c` (see Example Rewrite B, §11); ADD one worked instantiation
of the running example immediately after Eq. 1, tied to the Table 2 number; ADD a
forward-pointer at the asset-resolution clause; ADD one sentence resolving the
risk-vs-severity ambiguity; ADD one clause disambiguating "Exposure." SHORTEN the
Overview's dual-justification paragraph so cost reads as secondary. EXPAND
Tool Impact by one to two sentences naming the evidence-precedence treatment;
EXPAND Novelty and Exposure to name the sequence signal explicitly.

### Implementation (lines 815–1032)

**Purpose:** make the two-layer design concrete and credible — show where each
factor's evidence comes from, what's deterministic vs. model-derived, and what's
architecturally forbidden from the invocation path; land the two genuinely novel
mechanisms as the promised payoff.

**Current story:** careful, concrete systems-engineering prose, in a
well-justified fixed order (capture → static → dynamic), and it does contain the
paper's two most genuinely novel mechanisms — but never signals they're the
mechanisms carrying the paper's real novelty, because Contributions never named
them either.

**Problems:** *(LOGIC — flagged CONFIRMED elsewhere as a correctness issue, not
just style)* line ~910's "possibly untrusted server" directly contradicts the
fixed threat model and this same subsection's own correct framing 26 lines
earlier. *(LOGIC)* the Composition paragraph says runtime factors are "realized
over discrete reporting bands rather than as continuous multipliers," but
Methodology's Eq. 3–4 define `L(c)` as a literal continuous product — Implementation
never states how the discrete rule relates to the continuous formula it's
supposedly "realizing," so the paper's formal apparatus and the actually-built
system read as two different objects. *(CITATION)* two of the section's most
concrete empirical findings — the removed reviewer stage altering "~46% of
bands," and the access-anomaly escalator "firing on between half and two-thirds
of all cells" — are bare, unsourced numbers with no sample size or pointer to a
supporting table anywhere. *(CLAIM)* "a given tool catalog yields a byte-identical
risk matrix on re-scan" is asserted with more confidence than §6.3 (the
subsection built to validate exactly this kind of claim) anywhere substantiates —
reproducibility is never measured or reported. *(TERMINOLOGY)* "Novelty and
Exposure" again grounds only novelty. *(TERMINOLOGY)* "call" used roughly twice as
often as "invocation" for the identical referent, concentrated in the Dynamic
Layer subsection, despite "invocation" being the section's own title-level term.
*(STORY)* the calendar-event illustration (976–978) is unconnected to the running
example — it makes a genuinely distinct point (one call, multiple register rows)
that `write_file` alone can't show, so the fix is to anchor it to the running
example, not drop it. *(REVIEWER_CONFUSION)* Implementation sends readers to
equations whose notation is inconsistent/undefined in Methodology — out of this
section's scope to fix, but it undercuts legibility of what Implementation
actively points to.

**Structural changes:** MERGE the calendar-event illustration into the running
example rather than leaving it free-floating. ADD a sample-size/corpus pointer to
both ablation numbers; ADD one reconciling sentence for the continuous-vs-discrete
composition mismatch; ADD one sentence defining "exposure" or drop it from the
name; ADD a framing clause marking both mechanisms as the paper's central novelty
(primary fix belongs upstream, in Contributions). EXPAND the determinism claim
with a pointer to where it's verified, or hedge to "is designed to yield."

### Evaluation (lines 1033–1152)

**Purpose:** set the reader's expectations honestly and precisely for what
Results will show — every promise here should be either fully cashed out in
Results or explicitly, consistently scoped as future work.

**Current story:** names three evaluation properties (consistent ordering,
systematic factor-response, appropriate runtime adaptation) but never returns to
confirm or deny each by name; corpus-scale numbers live in the wrong subsection
(Static Assessment, not Evaluation Settings); Dynamic Assessment is honest about
its own narrow scope but the Abstract's headline "3,000 invocations" figure never
appears inside Evaluation at all; Additional Properties promises cost/latency in
the same unhedged register used for delivered claims, with no hedge warning the
reader the promise goes unmet.

**Problems:** *(CLAIM)* "adapts appropriately to runtime behavioral context"
(line ~1042) is directly self-contradicted 75 lines later by §6.3's own
"left for subsequent evaluation" — a self-contradiction *within one section*,
maximally visible to a straight-through reader. *(CLAIM)* §6.4's unhedged
"we measure" language for Computational Cost and Runtime Latency — neither figure
appears anywhere in the compiled paper, and unlike §6.3, no hedge warns the
reader. *(REDUNDANCY)* the opening "no existing benchmark…" paragraph restates,
with the identical three citations, an argument already made in more detail in
Related Work — its third appearance in the paper. *(REVIEWER_CONFUSION)* the
paper's own headline number (3,000 invocations, GitHub/Slack/Calendar) is never
stated anywhere inside Evaluation itself — only in the Abstract/Conclusion
bookends, sharpened by contrast with §6.2, which *does* give the equivalent
static-corpus numbers in full. *(TERMINOLOGY)* "the proposed method"/"the proposed
methodology" name the same referent as "framework" (the section's own dominant
term) within six lines of each other. *(TERMINOLOGY)* "risk estimation" appears
only in this section; "risk assessment" is used everywhere else for the identical
concept. *(TRANSITION)* the three named evaluation properties are never mapped to
the subsections that test them. *(ORDER)* corpus-scale numbers sit in §6.2
("Static Assessment") rather than §6.1 ("Evaluation Settings," which describes
the corpus but gives no numbers).

**Structural changes:** MOVE the corpus-scale numbers into §6.1. MERGE
Computational Cost into §6.2 and Runtime Latency into §6.3, rather than a
disconnected §6.4 catch-all. ADD a connective sentence mapping each named
criterion to its testing subsection; ADD the invocation count and deployment
identities to §6.1 or §6.3 so Evaluation grounds its own headline claim; ADD an
explicit hedge to §6.4 matching §6.3's honesty pattern. SHORTEN the redundant
"no existing benchmark" paragraph to a single pointer back to Related Work.
EXPAND §6.3 with the same scale specificity §6.2 already has.

### Preliminary Results (lines 1159–1345)

**Purpose:** deliver the empirical payoff and close the promises made upstream —
substantiate the static risk surface, report the Dynamic Scanner evidence and
operational numbers §6.3 commits to, and make the traceability claim visible in
practice.

**Current story:** a self-consistent, arithmetically clean static-surface
report — but it never reports a single Dynamic Scanner number, and the paper's
own "3,000 live invocations" fact first appears not here but in the Conclusion, a
section later than a reader would look for it.

**Problems:** *(STORY)* no Dynamic Scanner results, cost, or latency numbers
anywhere, despite four separate upstream promises setting up exactly this
expectation. *(ORDER)* the 3,000-invocation fact appears for the first time in the
Conclusion, not in Results. *(TRANSITION)* the section's opening sentence
("Currently, we report only…") is a bare scope-narrowing statement with no
itemization of what's deferred or where the resolution lives. *(REVIEWER_
CONFUSION)* the closing per-parameter blast-radius-grading paragraph introduces
new methodology never connected back to the one-sentence `B(t,a)` definition in
Methodology. *(CLAIM)* "operationally useful because semantic inference is
concentrated…" asserts a cost benefit with no cost number behind it — exactly the
measurement §6.3 promises and never delivers. *(STORY)* the paper's strongest
proof point (the same tool scoring very differently by asset) is only
half-realized — Table 3 reports only the maximum-scoring `write_file` pair per
organization, never a matched low-scoring instance from the same deployment, so
the full within-tool contrast the Introduction primes the reader to expect never
actually appears. *(TECHNICAL_PRECISION)* Table 3's header reads "S·B·T" against
Eq. 1's canonical "T·S·B" order, unexplained. *(CLAIM)* two of Table 3's four
maximum-score rows rest on a tool-impact assignment with an unaddressed
face-validity question (`conversations_leave` — "leaving a Slack channel" —
scored at the top tier alongside `delete-event` and `write_query`, with no
explanation). *(LOGIC)* the SQL-vs-OpenBB reachability-rate claim varies both
tool count and catalog domain at once, so the asserted single cause isn't
actually isolated by the comparison given. *(TECHNICAL_PRECISION)* "24% of the
scored surface and 7.7% of the complete matrix" gives two valid, differently-
scoped percentages with no stated preference. *(TERMINOLOGY)* "our framework" /
"the framework classifies" overstate what this section actually measured (one of
two layers) — should be scoped to "the Static Scanner."

**Structural changes:** MOVE the 3,000-invocation sentence from the Conclusion
into Results, as the opening of a new Dynamic Assessment Results subsection.
MERGE the per-parameter grading paragraph into the discussion following Table 3,
tied explicitly back to `B(t,a)`. ADD a short Dynamic Feasibility Results
subsection (see Example Rewrite F, §11); ADD the promised cost/latency numbers or
an explicit sentence stating they're not yet reported; ADD one bridging sentence
at the very start of §7 itemizing exactly what's covered vs. deferred; ADD a
matched low-scoring `write_file` exemplar from the same deployment as a
high-scoring row, completing the contrast; ADD one clause explaining the evidence
behind `conversations_leave`'s top-tier score. SHORTEN or hedge the SQL-vs-OpenBB
causal claim.

### Conclusion (lines 1356–1391)

**Purpose:** restate the central tension so an Abstract+Conclusion-only reader
still gets the paper's core argument; recap the architecture surfacing the real
novel mechanisms, not just T·S·B; select and interpret the strongest evidence
rather than re-tabulate it; honestly reconcile the promise/delivery gap; end on a
confident, specific statement of what's demonstrated.

**Current story:** opens correctly on the central tension, but never names CARMA
even though the macro is used five times earlier in the paper. Recaps the
architecture using only the domain-general T·S·B formula and the operation
ladder — omitting the traffic-derived resolver and the runtime layer's
bounded-below-by-1 guarantee, its most distinctive design property. The results
paragraph re-tabulates aggregate percentages already given in Results almost
verbatim, without selecting the paper's own strongest, most specific finding (the
`write_file` cross-organization shift plus the public-data zero-High/Critical
result) — exactly the illustrative claim the Introduction sets up. Ends entirely
on an unreinforced hedge.

**Problems:** *(STORY)* CARMA never named in the Conclusion. *(STORY)* the
empirical paragraph omits the paper's single strongest finding in favor of
generic aggregate stats. *(REDUNDANCY)* the numbers paragraph near-verbatim
repeats Preliminary Results with no new synthesis. *(CLAIM)* the asset-sensitivity
sentence drops the explicit "…rather than a fully labeled asset inventory"
contrast Contribution 1 states as the paper's specific novelty claim. *(STORY)*
the architecture summary names only the domain-general formula and the operation
ladder, never the traffic-derived resolver — an Abstract+Conclusion-only reader
meets only half the paper's real novelty. *(LOGIC)* the bounded-below-by-1
escalation-only guarantee — the property most directly resolving the paper's own
central tension — is never stated in the section most likely to be read alone as
the paper's summary. *(ORDER)* the decomposability paragraph (a design claim)
sits between the empirical paragraph and limitations, rather than grouped with
the earlier architecture summary it belongs with. *(REVIEWER_CONFUSION)*
"the corresponding baseline" lacks a clean local antecedent on a skim-first read.
*(TERMINOLOGY)* "provisioned" appears nowhere else in the document, for a claim
the Abstract already states with concrete, checkable deployment names.
*(STORY)* the section ends entirely on a hedge, with no closing sentence
reaffirming what's actually demonstrated.

**Structural changes:** MOVE the decomposability paragraph to directly follow the
architecture paragraph. MERGE the `write_file` cross-organization and public-data
findings into the numbers paragraph, replacing generic aggregate stats. ADD
CARMA's name to the opening or closing sentence; ADD the traffic-derived resolver
alongside the operation ladder; ADD the bounded-below-by-1 guarantee explicitly;
ADD a closing sentence reaffirming the demonstrated contribution after the
limitations paragraph. SHORTEN the remaining generic stats to one supporting
clause once the specific finding is folded in. EXPAND the asset-sensitivity
sentence to restore the inventory contrast.

---

## 8. Citation and positioning issues

Every major claim in the Introduction and Related Work was checked against its
citation by directly fetching the source (not inferred from title/venue). 14
claims audited; two need a fix, one is a bibliography hygiene issue, the rest hold
up — including several genuinely well-executed citation patterns worth preserving.

**Needs a fix — citation doesn't support the claim:**

- *"An agent may select an available but inappropriate tool"* (line 192–193,
  cited to Yin et al., "The Reasoning Trap," arXiv:2510.22977). **Verified via
  WebFetch: this paper is about tool *hallucination*** — inventing a call to a
  nonexistent tool, under two specifically constructed conditions (no correct tool
  available; only distractors present) — a different failure mode from
  misselecting among genuinely valid, real options. Reword to match what the
  paper actually shows ("an agent may fabricate a plausible but nonexistent tool
  call…"), or find a citation about wrong-selection-among-valid-options — none
  currently exists in the corpus, so narrow the prose rather than inventing one.

- *"The public server ecosystem is growing quickly"* (line 170, cited to Hou et
  al., ACM TOSEM 2026). **Verified: this is a threat-taxonomy survey with no
  growth-rate figures**, and neither of the two ecosystem-measurement papers
  already in the corpus (`li2026firstlook`: 67,057 registry listings;
  `guo2025measurement`: 8,401 valid projects from a 14-day crawl) demonstrates a
  growth *rate* — both are single-snapshot counts. Either soften to a scale claim
  backed by one of those two existing citations, or drop the growth framing.

**Bibliography hygiene (not a rendering bug yet, but fragile):**

- `refs.bib` contains duplicate `@entry` blocks under the same or near-identical
  keys for `zhao2025parasites`/`zhao2026parasites` (identical paper, two keys —
  only one is actually cited), and separate duplicate blocks for
  `betser2026agentrim`, `owireduashley2026severity`, and `zhang2026stars`. BibTeX
  silently picks one; deduplicate before the camera-ready pass.

**Cosmetic:**

- *"ConLeash"* should be *"Conleash"* (one capital C) to match the source paper's
  own spelling.
- *"AgenTRIM assigns risk levels"* (plural) — confirmed via full text: it's
  actually a binary low/high partition, not an ordinal scale. Optionally change
  to "a binary risk label" if AAMAS reviewers who know this paper would expect
  more granularity than stated.

**Confirmed accurate, including the paper's central novelty claim:** every
"closest competitor" candidate — STARS, AgenTRIM, MTGuard, IGAC, AgentTrust/NEXUS,
MCP-in-SoS, and two additional candidates found during this pass but not yet in
the corpus (Trust No Tool/VISTA-Guard, MCPThreatHive) — was individually
re-verified against its actual text. The novelty claim ("no existing method
estimates the consequence of a concrete MCP invocation from the sensitivity and
scope of the asset it affects") **holds up against everything checkable.** One
open item: **`MCPThreatHive` (arXiv:2604.13849)** is flagged in your own
`literature-review.md` as "found during the July 2026 sweep, not yet read in
full" — its abstract alone doesn't resolve whether its "composite risk scoring
model" operates at server-, threat-pattern-, or invocation-level. Read it before
submission; if per-invocation, add it to the differentiation paragraph, if not,
cite it as reinforcing evidence.

The 196-evaluators/68% CVSS-inconsistency claim (line 386–388) was independently
re-confirmed accurate on both figures — this is the same citation-misattachment
issue (`first2023cvss`, the *specification*, cited jointly with `wunder2024cvss`,
the actual *study*) already caught by `CRAFT-REVIEW.md`; not re-filed as new, just
independently corroborated.

**A citation pattern worth preserving as a model, not fixing:** the three-item
citation cluster at lines 334–336 (`invariant2025toolpoisoning`,
`shi2025toolhijacker`, `zhao2025parasites` for "a malicious server, tool
description, or external input") is a clean 1:1:1 mapping — each citation
genuinely earns its place against a distinct clause of the sentence, unlike the
padded triads `CRAFT-REVIEW.md` flagged elsewhere in this same paper. Also
well-executed: Fleming et al. positioned explicitly as the single nearest prior
work with a precisely stated granularity gap ("risk computed for the whole task,
not updated for each call") — this is the right way to state a distinction, and
the model for the compound gap statement recommended for Related Work's closer.

---

## 9. Top 10 changes, ranked

| # | Change | Priority | Scope |
|---|---|---|---|
| 1 | Scope every claim that the Dynamic Scanner's runtime adaptation was "evaluated" down to what §7 actually delivers (feasibility only); move the 3,000-invocation figure and deployments into a new "Dynamic Feasibility Results" subsection, stated at first mention rather than discovered in the Conclusion. | **CRITICAL** | whole paper |
| 2 | Promote the evidence-precedence operation ladder and the traffic-derived resolver from Implementation asides into the Contributions list (rewrite bullet 2), with a one-sentence preview at first mention in Methodology. | **CRITICAL** | section |
| 3 | Narrow the stated research gap from the sweeping "no existing method…" claim to the precise, defensible scope (pre-execution, per-(tool,asset), policy-derived, not inventory-derived); apply the same narrowing to Related Work's closer as a compound four-part statement. | **CRITICAL** | section |
| 4 | State explicitly, once, in Threat Model, that the framework only scores invocations that have already passed existing authentication/authorization checks (the `perm(c)=1` precondition, currently trapped in a comment). | **CRITICAL** | paragraph |
| 5 | Fix two notational defects in Methodology's central equations: define the invocation tuple `c` in compiled text; correct `R_static(t,r)` to `R_static(t,a)`. | HIGH | paragraph |
| 6 | Restructure the Introduction to eliminate the MCP-defenses→general-AC→MCP-defenses-again interleaving: merge the two non-adjacent defenses passes into one. | HIGH | section |
| 7 | Consolidate the four to five scattered file-operation illustrations into one running example (`write_file` scratch file vs. credentials store), carried from Introduction through Methodology into the Table 2/3 result. | HIGH | whole paper |
| 8 | Rewrite the Conclusion: name CARMA; replace re-tabulated generic stats with the strongest specific finding; add the resolver mechanism and the bounded-below-by-1 guarantee; end on a confident restatement, not a bare hedge. | HIGH | section |
| 9 | Fix the internal contradiction in Implementation's annotation-trust framing ("self-reported and imprecise" vs. "possibly untrusted server," two sentences apart, contradicting the fixed threat model). | HIGH | sentence |
| 10 | State the reporting bands' actual discreteness explicitly — the 5×5×5 product cannot populate large stretches of the stated High/Critical ranges (verified by full enumeration). | MEDIUM | paragraph |

---

## 10. Proposed new Introduction architecture

Not necessarily a full rewrite — a proposed paragraph sequence, each with its
purpose and exactly how it creates the need for the next.

**P1 — The same call, two consequences (cold open).** Replace the generic "AI
agents now act" opening with the paper's own strongest concrete contrast:
`write_file` against a scratch file versus against a credentials store — same
tool, wildly different consequence. In the same breath, state compactly that the
server is assumed benign and the call is already authenticated and authorized:
the risk is that "authorized" and "consequential" are orthogonal, not a malicious
server or a policy violation. *Creates:* the security-literate reader's immediate
reflex — "isn't grading how dangerous an authorized request is exactly what
access control already does?"

**P2 — Zoom out: access control already grades risk, and the paper concedes
this.** One consolidated paragraph (not interleaved with MCP-specific material):
RBAC/ABAC decide permit/deny, not magnitude; risk-adaptive access control already
established, two decades ago, that a computed risk value can condition an
authorization decision — grading a permitted request is explicitly *not* this
paper's idea. Close by narrowing to Fleming et al./TBAC: scores a whole task, not
a call. *Creates:* if grading has already reached agents once, has it reached MCP
specifically?

**P3 — Zoom in: MCP- and agent-specific defenses, consolidated, ending on the
narrowly-scoped gap.** One single, non-repeated pass over MCP's own annotation
vocabulary and the full defense literature (MTGuard, IGAC, Progent, MiniScope,
AgenTrim, ConLeash, AgentGuardian, AgentTrust, STARS, NEXUS) — restrict, audit, or
verdict a call, never a graded asset-specific consequence. Close with CVSS/AIVSS
in the same bucket (grade a vulnerability class, not an authorized call), then
the gap at defensible scope. *Creates:* "why hasn't anyone done this — what
actually makes it hard?"

**P4 — Why this is hard** *(new paragraph — currently absent).* Three named
obstacles, each foreshadowing one design decision in P5: (a) asset sensitivity
has no numeric source — organizations write prose policy, not a labeled field, so
deriving it is an interpretation problem; (b) blast radius depends on each tool's
own argument semantics and self-reported, imprecise (not adversarial) annotations,
so no fixed configuration can supply it; (c) whatever runs at request time must
return a verdict before the call proceeds, deterministically, without a model,
and must never let absence of history read as "safe." *Creates:* an explicit
checklist — "show me the design that resolves (a), (b), and (c)."

**P5 — The insight and approach: naming CARMA, every choice traced to P4.**
Sensitivity read from policy prose (resolves a); tool impact bounded by the
evidence-precedence ladder, blast radius resolved by the traffic-derived resolver
(resolves b) — name both mechanisms here, not only in Implementation; a bounded,
floor-1, model-free runtime multiplier that can only escalate (resolves c).
Redeem the P1 example here with its actual number — `write_file` × `security-keys`
= 100 in Table 2. *Creates:* "has this actually been run for real, on both
layers?"

**P6 — What was actually evaluated, scoped precisely at first mention.** Replace
the current overclaiming line with: the static layer is evaluated for accuracy
and behavior across 16 real deployments; the dynamic layer is fully specified
with the same rigor and exercised on 3,000 live invocations to establish
feasibility — explicitly not accuracy against real misuse, named here as future
work rather than left for the reader to discover at line 1162. This single
paragraph is the fix for the paper's largest promise/delivery gap. *Creates:* the
natural closing move — itemize the contribution.

**P7 — Contributions, with both MCP-specific mechanisms given explicit billing.**
(1) the three-factor, policy-derived decomposition; (2) the evidence-precedence
ladder and the traffic-derived resolver, named explicitly rather than left to
Implementation; (3) the two-layer framework with an escalation-only runtime
adjustment; (4) an evaluation methodology with the static layer validated and the
dynamic layer's feasibility demonstrated — scoped identically to P6, not walked
back. *Hands off* to Related Work (citation-depth on what P2–P3 covered at
shape-level) with the reader already knowing the gap, the difficulty, the
mechanism, and the evaluation's honest boundary.

---

## 11. Example rewrites

Illustrative only — `main.tex` was **not** modified for any of these. Each was
independently, adversarially fact-checked by a second pass against the actual
compiled file and every cited external source; verdicts are reported honestly,
including the one that didn't hold up.

### A. Threat Model — state the `perm(c)=1` precondition — ⚠ verdict: **grounding overstated**

**Current** (line 421): *"Our threat model focuses on misuse of legitimate MCP
capabilities. Misuse occurs when an MCP operation creates potentially harmful
consequences for organizational assets or services, regardless of whether the
operation originates from benign error, excessive delegation, compromised
behavior, or malicious intent. The operation may still be syntactically valid and
supported by the exposed tool…"*

**Proposed:** *"…We consider only invocations that have already passed the
deployment's existing authentication and authorization checks: for an invocation
$c$, we restrict attention to the case in which the deployment's own
access-control decision already satisfies $\mathrm{perm}(c)=1$, and our framework
neither performs, weakens, nor second-guesses that decision. Misuse occurs when
such an already-permitted MCP operation nevertheless creates potentially harmful
consequences… The operation is syntactically valid, supported by the exposed
tool, and authorized under $\mathrm{perm}(c)=1$ — yet permitted is not the same
as safe…"*

**Why:** takes a precondition the authors already derived correctly — it's sitting
word-for-word in a commented-out block (lines 496–501) — and moves it from dead
comment into the section reviewers check foundational claims against.

**Verifier's finding:** the mechanical part checks out completely (the
`perm(c)=1` text really is drafted, verbatim, in the commented block; the
notation collides with nothing live). **But the rewrite's central justification is
false and should be dropped**: it argues "a reviewer who reads only this
sentence has no textual basis to know the paper excludes authorization bypass
from its own scope" and that this distinction is "currently unstated… anywhere
the compiler reaches." That's contradicted by the paper itself — the **Conclusion
already states this almost exactly**: *"Authorization answers whether an MCP
invocation is permitted; it does not express how consequential that permitted
invocation may be"* (lines 1359–1360), and "authorization"/"authorized" appears
live at eight other locations. **The edit is still worth making** (compiling a
formal precondition where the paper's central argument depends on one is good
practice regardless), but justify it as *making an implicit precondition
explicit and formal*, not as *filling a total absence* — the concept already
exists in prose elsewhere in the paper.

### B. Methodology — define the invocation tuple, fix `r`→`a` — ✅ **Confirmed**

**Current:** the invocation tuple `c` is used unglossed at Eq. 2/3 and lines 757,
782; its only definition sits in a commented block pointing at a label
(`\ref{sec:threat}`) that no longer exists (the Threat Model section was renamed
to `\label{threatmodel}`). `R_static(t,r)` appears at lines 716, 751 against
`R_static(t,a)` everywhere else.

**Proposed:** port the tuple definition into live text as a proper labeled
equation — *"For each request reaching the framework, we represent the
information available for assessment as the invocation tuple $c = \langle
i,t,a,x,h\rangle$, where $i$ identifies the calling agent…"* — repointing the
cross-reference at the label that actually compiles, and correct both `r`
instances to `a`.

**Verifier's finding:** every claim checked out exactly — the stale
`\ref{sec:threat}` label, the five unglossed downstream uses of `c`, `r`'s total
absence from the compiled document, Eq. 1 as the paper's actual first live
equation. No collision risk from introducing a live `\label{eq:invocation}`. One
labeling loose end worth knowing: after this fix, the new tuple equation becomes
the paper's literal "Eq. 1," displacing the static-risk equation — cosmetic, not
a correctness issue.

### C. Contributions + Methodology — name the two real mechanisms — ✅ **Confirmed**

**Current** (Contributions bullet 2): *"We develop a framework that implements
the proposed methodology through complementary Static and Dynamic Scanners and
produces interpretable risk scores."*

**Proposed:** *"**Two MCP-specific scoring mechanisms.** We develop a
risk-assessment framework built on two mechanisms novel to the MCP setting.
First, an evidence-precedence deterministic operation ladder classifies tool
impact from MCP's self-reported `tools/list` annotations while treating them as
hints rather than ground truth… Second, a config-free, traffic-derived resolver
recovers which call arguments name which organizational assets by observing live
invocation traffic, requiring no per-server configuration…"* — plus a one-sentence
forward pointer at each mechanism's first mention in Methodology (§4.2.1, §4.3).

**Verifier's finding:** every quoted passage and reused phrase verified verbatim
against `main.tex`; all four external papers (SoK, Progent, InjecAgent, ToolEmu)
confirmed real with their claimed patterns present. Two small overstatements in
the *justification* text, not the rewrite itself, worth knowing: it claims
Contributions bullets 1 and 3 "already open with 'We introduce'/'We develop'" as
if showing variety — false, bullets 1 *and* 3 both open with "We introduce"; it's
bullet 2 (the one being replaced) that says "We develop." And the claim that SoK
and Progent use "mechanism" *exclusively* in the reserved sense is overstated —
both also use it generically elsewhere. Neither issue affects the rewrite's
substance.

### D. Introduction + Related Work — narrow the gap claim to a defensible scope — ✅ **Confirmed**

**Current** (line 223–224): *"To our knowledge, no existing method estimates the
consequence of a concrete MCP invocation from the sensitivity and scope of the
asset it affects."*

**Proposed:** *"To our knowledge, no existing method computes a pre-execution
consequence score for a concrete MCP invocation, scoped to the specific
tool–asset pair it exercises and derived from the organization's own
classification policy rather than from a fully labeled asset inventory."* Plus a
compound four-part closer for Related Work, giving each of the four surveyed
strands (verdict-only defenses; task-level RAdAC; artifact-level auditing;
vulnerability-class scoring) its own clause and citation cluster before the final
"our work fills this compound gap" sentence.

**Verifier's finding:** confirmed both quoted passages verbatim, confirmed the
narrower wording is not invented — it reuses phrasing the paper *already*
commits to at line 256 ("derived from organizational policy rather than
requiring a fully labeled asset inventory"). This is the strongest of the six
rewrites: it makes three separate parts of the paper (Introduction, Contributions,
Related Work) state the identical, already-established, defensible claim instead
of three different-strength versions of it.

### E. Introduction — consolidate the two MCP-defenses passes — ⚠ verdict: **core diagnosis solid, one detail wrong**

**Current:** two non-adjacent paragraphs (177–186 and 223–235) cover largely the
same defense literature, with general access control sandwiched between, each
ending on a near-identical closing sentence.

**Proposed:** one consolidated paragraph — *"MCP and agent security research
studies both directions of risk. One line studies how malicious servers, poisoned
tool descriptions, or crafted external inputs can harm the agents that use
them… A second line treats the agent itself as the source of risk and intervenes
along the call: at runtime, MTGuard inspects…"* — merging every citation from
both original paragraphs into one, ending on a single gap-closing sentence.

**Verifier's finding:** every quoted passage, citation grouping, and the
downstream "third pass" in Related Work re-covering the identical citation set
were confirmed verbatim. **One corroborating detail doesn't hold up**: the
rewrite's evidence section claims the paper's own inline planning comments
"independently label" lines 177–186 and 223–235 as "P2" and "P6" respectively —
checked directly, the comment's own description of P6 ("method — our
methodology") doesn't match 223–235's actual content (other people's defenses
failing, not "our methodology"); by content it maps closer to P4. The redundancy
itself is real and independently verifiable without that detail — drop the
"the file's own comments confirm this" claim, keep the fix.

### F. Abstract / Introduction / Contributions / §6–7 / Conclusion — close the promise/delivery gap — ✅ **Confirmed**

The largest of the six rewrites, spanning seven locations. Rescopes "evaluate"
away from the Dynamic Scanner's *accuracy* (never shown) toward its *feasibility*
(genuinely shown) everywhere the stronger claim currently appears, and adds a new
§7.2 "Dynamic Feasibility Results" subsection — inserted at first mention rather
than discovered in the Conclusion — reporting the 3,000-invocation collection,
full scoring coverage, deterministic reproducibility (no model on the invocation
path), and stating plainly what this does *not* establish: *"we cannot yet report
precision, recall, or agreement with human judgment on this trace."*

**Verifier's finding:** confirmed every quoted passage verbatim across all seven
locations, confirmed via grep that no cost/latency figure exists anywhere in the
compiled paper outside the bare promise, confirmed §6.2's and §7's own
self-admissions are already there for the four overclaiming locations to
contradict. One explicit, honest note the rewrite itself flags: the `[X ms]`
latency placeholders in the new §7.2 are illustrative only — no real measurement
exists to report, and none should be fabricated; those values, if this section is
ever actually added, must come from the timing instrumentation Implementation
already describes (line 1025) but never surfaces.

---

## Method

19 Claude Sonnet 5 subagents, ~2.95M tokens, 501 tool calls. Story reconstruction
(1) → three parallel web-research crews on AAMAS/notable-author writing patterns
(3) → the five-agent committee, Story/Terminology/Skeptic/Positioning in parallel
then Architect reading all four (5) → synthesis with a soul-clarity gate (1) →
Introduction paragraph-by-paragraph analysis (1) → seven section reviews (7) →
top-10 ranking and new-Introduction-architecture in parallel (2) → six example
rewrites, each independently adversarially verified (12, draft+verify pairs) →
this assembly pass. The soul-clarity gate passed on the first attempt — every
committee member converged on the same core claim once checked directly against
`main.tex`. Nothing in `paper_v5/` was edited.
