# Citation audit — paper_v5

Audit date: 2026-08-03. Method: all 35 cited arXiv papers downloaded in full text and
searched; every `\cite` checked against the source; each flagged defect re-checked by an
independent adversarial verifier instructed to refute it. 123 (claim, citekey) pairs
checked, 59 raw findings, **19 survived** adversarial recheck. Every DOI and arXiv ID
below was confirmed live against CrossRef, the arXiv API, or Semantic Scholar.

Corpus cached at `~/.cache/citecheck/` (paper texts, standards, metadata).

---

## 1. Blocking — fix before submission

### 1.1 `huang2026caller` is WITHDRAWN

arXiv 2603.07473v2, updated 2026-07-21. The PDF now 404s. Authors' note:

> Withdrawal due to some flaws in experimental methodology and unresolved ethical issues
> in data collection. We need to redesign the experiments and obtain proper ethical
> clearance before resubmission.

Cited **3 times**, each time load-bearing:

| Location | Claim |
|---|---|
| `01-introduction.tex:73` | "servers hold authorization as persistent state instead of re-checking each call" |
| `02-related-work.tex:41` | "shows that a server cannot reliably distinguish the principal behind a call" |
| `03-threat-model.tex:63` | identity does not separate correct/mistaken/manipulated agents |

The withdrawn measurement *is* the claim being cited — the disowned methodology produced
exactly that finding. All three sites are single-key or rescued only by
`mellafe2026capability`, which does not study MCP servers (see §2.3).

`GROUND-TRUTH.md` §8 lists this as one of only two keys backing the design decision
*"Identity cannot separate good calls from bad."*

**Fix.** Remove the entry. Re-anchor on Zhou et al., *A First Measurement Study on
Authentication Security in Real-World Remote MCP Servers*, arXiv:2605.22333 (6 authors,
Fudan) — 7,973 live remote MCP servers, 40.55% expose tools with no authentication at all.
Verified present. For the confused-deputy half, cite Hardy, *The Confused Deputy*, ACM
SIGOPS OSR 22(4):36–38, 1988, `10.1145/54289.871709`.

### 1.2 The Related Work novelty claim contradicts a paper you already cite

`02-related-work.tex:95-97` closes:

> None scores the unit an access decision is actually taken over: the whole invocation,
> before it runs, with its resource, its arguments, and its calling history attached.

`zhang2026stars` (STARS) — **in your bib, cited in your own Introduction** — says:

> Our setting differs in prediction unit: we score a proposed skill invocation before
> execution

and its Introduction: *"we argue that the prediction unit should be the invocation rather
than the skill alone."* It defines a continuous score R(U,S,C) ∈ [0,1] over request, skill
and runtime context, computed before execution.

This is a self-contradiction inside the paper, and it lands on the central novelty claim.

**Fix.** The surviving distinction is the **input**, not the unit: STARS produces its score
holistically from a learned/LLM evaluator; yours decomposes into tool impact × resource
sensitivity × blast radius, with sensitivity derived from the organization's written
classification policy. Rewrite the closing sentence to claim the decomposition and the
policy derivation, not the unit.

---

## 2. Major — a reviewer will catch these

### 2.1 `yang2026agenttrust` is mischaracterised

`01-introduction.tex:91-94` groups it under outcomes that are "not magnitudes." AgentTrust's
own abstract:

> produces a structured verdict (allow, warn, block, review) before every [tool call]

"review" is your own intermediate outcome. The paragraph opens with the universal negative
*"No existing method estimates what a concrete MCP invocation would cost"* and has no hedge.

**Fix.** Same as §1.2 — draw the line on the input (holistic evaluator vs. decomposed,
policy-derived factors), not on the output shape.

### 2.2 `zhao2026parasites` misattributed

`02-related-work.tex:33-38` is a three-way distributive list with "a server" as subject of
all three verbs, ending "…or is planted in the ecosystem outright~\cite{zhao2026parasites}."
Zhao et al.'s own threat model does not support "planted server"; it is a large-scale census
of attacks on the MCP ecosystem. Single key on its clause, so no group-duty defence.

### 2.3 `mellafe2026capability` does not study MCP servers

Used in `02-related-work.tex` under the topic sentence *"The work that does look at the
server's own position."* Its own Limitations section:

> Public-source audit only. The Stripe remote MCP server internals were not audited. The
> framework findings are public-source client/framework defaults.

It audits LangChain/LangGraph, LlamaIndex and the Stripe Agent Toolkit — agent frameworks.
The word "principal" appears once, in a definition. It is also single-author, 7 pages,
unreviewed, no venue. With `huang2026caller` withdrawn, it becomes the sole support for the
identity claim.

**Fix.** Keep it only in `01-introduction.tex:73-74` (capability-gate vs. per-call
authorization is genuinely its contribution). Remove it from the server-position sentence.

### 2.4 `atlam2020riskbased` — wrong journal

Bib: *International Journal of Computer Network and Information Security* 12(5), 2020.
Actual: ***Future Internet*** 12(6):103, `10.3390/fi12060103`, 2020-06-11.

Confirmed three ways: CrossRef title+author match; the full IJCNIS 2020 record (30 items)
contains no Atlam paper and 12(5) holds five unrelated articles; Semantic Scholar agrees.
Cited 3 times.

```bibtex
@article{atlam2020riskbased,
  title   = {Risk-Based Access Control Model: A Systematic Literature Review},
  author  = {Atlam, Hany F. and Azad, Muhammad Ajmal and Alassafi, Madini O. and
             Alshdadi, Abdulrahman A. and Alenezi, Ahmed},
  journal = {Future Internet}, volume = {12}, number = {6}, pages = {103},
  year    = {2020}, doi = {10.3390/fi12060103}
}
```

### 2.5 `pynadath2002adjustable` — authors in the wrong order

JAIR version of record: **Scerri**, Pynadath, Tambe. The bib puts Pynadath first.

Confirmed via CrossRef, Semantic Scholar, OpenAlex (`author_position: first` = Paul Scerri),
the JAIR article page, DBLP, and the PDF title page itself. Origin of the error: DBLP's CoRR
mirror record (arXiv 1106.4573) lists Pynadath first, but that PDF is byte-identical and its
title page reads Scerri first.

This is your **only** AAMAS-community anchor, and the bib comment claims it was verified.

---

## 3. Venue and metadata corrections — all verified live

Five entries are cited as preprints but have been published:

| Key | Correct venue | DOI |
|---|---|---|
| `hasan2025firstglance` | ACM TOSEM 2026 | `10.1145/3814959` |
| `shi2025toolhijacker` | **NDSS 2026** | `10.14722/ndss.2026.230675` |
| `xing2025mcpguard` | Findings of ACL 2026, pp. 4877–4889 | `10.18653/v1/2026.findings-acl.240` |
| `yin2025reasoningtrap` | **ACL 2026 Main** | `10.18653/v1/2026.acl-long.376` |
| `bradatsch2024zerotrust` | IEEE TrustCom **2023**, pp. 1422–1429 | `10.1109/TrustCom60117.2023.00194` |
| `tang2025riskknowledge` | **COLM 2025** (camera-ready) | OpenReview `OeYdS51k8F` |

Note `bradatsch2024zerotrust`: the year in the citekey is also wrong (2023, not 2024).

Author-list defects:

- `hasan2025firstglance` — omits **Gopi Krishnan Rajbahadur** (4th author). v1/v2 had five
  authors; v3 (18 Jun 2025) added him. The bib pins no version, so it renders as a complete
  list and silently misattributes.
- `rahman2026rolestratified` — omits **Md Hasibul Amin** (5th of 7); paper is now at v2.
- `shi2025toolhijacker` — `and others` after 3 of 6 hides **Neil Zhenqiang Gong**.
- `zhu2025miniscope` — `and others` after 6 of 7 hides **Raluca Ada Popa**.
- `lynch2025misalignment` — `and others` after 6 of 8 hides Ethan Perez, Kevin Troy.
- `jing2025mcip` — author "Heli, Xu" is parsed family=Heli, given=Xu; should be Xu Heli.

Missing fields that ACM-Reference-Format will render as gaps (confirmed against the compiled
`main.pdf`):

- `spring2021time` — add `volume={19}, number={2}, pages={74--78}`. Currently renders as
  "IEEE Security & Privacy (2021)" with no locator.
- `cheng2007fuzzymls` — `pages={222--230}`
- `kandala2011radac` — `pages={236--241}`
- `buhler2026agentbound` — `pages={2141--2164}` (currently the placeholder "Article FSE096")
- `li2025privilege` — `pages={555--563}`, `doi={10.1109/MASS66014.2025.00090}`
- `jing2025mcip` — `pages={1177--1194}`, `doi={10.18653/v1/2025.emnlp-main.62}`
- `zhao2026parasites` — proceedings DOI now exists
- `cheimonidis2023dynamic` — add article number `324`

`mcp2026spec` has two problems: the citekey says 2026 while the year field says 2025, and
the cited revision (2025-06-18) is stale — **2025-11-25** and **2026-07-28** now exist. The
four hints and the "clients **MUST** consider tool annotations to be untrusted unless they
come from trusted servers" warning are unchanged in the current revision, so the claim holds;
only the pointer needs updating.

---

## 4. Uncited claims that need support

- `05-evaluation.tex:237` — "against a design target of 1--2\%" is the yardstick that turns
  0.8% into the RQ4 headline, but the target has no provenance: not derived in §4, not
  attributed to an operator requirement, not cited. If it is your own target, say so and say
  it was fixed before the experiment.
- `05-evaluation.tex:41-44` — "we know of no external benchmark that supplies it" is a survey
  claim with zero support, and it justifies RQ3 having no external comparison. Bound it
  explicitly and name the near misses (ToolEmu, MAD-Bench, the action-graded severity scale)
  and why each grades a different object.

---

## 5. Verified correct — stop worrying about these

- **CVSS v4.0 quotes are verbatim.** Table 8: VI:H *"There is a total loss of integrity"*;
  VI:L *"the amount of modification is limited."* The tier 3/4 grounding is solid.
- **RFC 5789** — *"used to apply partial modifications to a resource"* supports the PATCH
  characterisation.
- **`hasan2025firstglance` "1,899 open-source servers"** — exact match.
- **`fleming2025tbac`** — abstract explicitly weighs target-resource risk against *"the LLM's
  own model uncertainty in its decision-making."* Characterised accurately.
- **`hou2026mcp`** — TOSEM DOI `10.1145/3796519` confirmed, published 2026-02-16.
- **All Section 5 numbers match `GROUND-TRUTH.md` verbatim** — 56 resources, six misses,
  55/55 tools, 51/55 agreement, the blast-radius table, the score sums, both dynamic
  thresholds, and every RQ4 figure. Nothing rounded or drifted.
- **`sandhu1996rbac`, `nist2004fips199`, `nist2008sp80060`, `dusseault2010patch`,
  `fielding2022http`** — all correct.

---

## 6. Novelty threats — work that already does part of what you claim

Every entry verified to exist. Citation counts from Semantic Scholar.

| Work | Cites | Overlap | Your distinction |
|---|--:|---|---|
| **ToolEmu** — Ruan et al., ICLR 2024, arXiv:2309.15817 | **464** | LM-based safety evaluator that *quantifies severity* of risks realized by agent tool use across 36 high-stakes toolkits | Post-hoc, emulated, no resource-sensitivity input, no policy derivation |
| **CaMeL** — Debenedetti et al., arXiv:2503.18813 | 199 | Canonical capability-based agent defense | Capabilities on values, not a consequence magnitude |
| **AgentSpec** — ICSE 2026, arXiv:2503.18666 | 148 | Runtime enforcement DSL with a "require human approval" action | Rule-to-verdict; the escalation line is fixed by which predicate fires |
| **ShieldAgent** — Chen et al., ICML, arXiv:2503.22738 | 119 | Extracts *verifiable rules from policy documents*, enforces over trajectories | Deontic rules (what is forbidden), not resource valuations |
| **IsolateGPT** — NDSS 2025, arXiv:2403.04960 | 115 | Execution isolation + permission mediation | Isolation, not pricing |
| **Conseca** — HotOS 2025, arXiv:2501.17070 | 52 | Just-in-time contextual policy per purpose | States your premise; still produces policy, not magnitude |
| `zhang2026stars` (already cited) | — | Scores the invocation before execution — **your exact unit** | Decomposition + policy-derived sensitivity |
| `owireduashley2026severity` (**in your bib, never cited**) | — | Seven-level ordinal harm rubric for tool-call trajectories | Retrospective grading of what an action *did*, vs. pricing what it *would* do |
| `almandalawi2025policyaware` (**in your bib, barely used**) | — | Six-stage pipeline whose stage 3 is literally "Data classification. Resolve sensitivity labels" | Takes a catalog/labels/lineage as input — it does *not* do without an inventory; returns {Approve, Deny, Conditional} |
| Agent Control Protocol — arXiv:2603.18829 | 2 | Deterministic static risk scoring driving allow/review/deny | Scores a request *type*, not a (tool, resource) pair |
| A Theory of Least Autonomy — arXiv:2607.09744 | 0 | Defines a compositional **"blast radius"** over an enterprise action hierarchy | Terminology collision — must cite and distinguish |

**ToolEmu is the most serious omission.** 464 citations, ICLR, and it is the best-known
prior attempt to put a graded severity number on an agent's tool action. Its absence from a
paper arguing that nobody grades agent-action severity is the first thing a reviewer will
notice.

---

## 7. Recommended additions

**Must add**

| Work | Venue | ID | Where |
|---|---|---|---|
| Ruan et al., ToolEmu | ICLR 2024 | arXiv:2309.15817 | Related Work §"Risk scoring" |
| Hardy, The Confused Deputy | SIGOPS OSR 1988 | `10.1145/54289.871709` | Intro P4, Threat Model |
| Zhou et al., Authentication Security in Remote MCP Servers | preprint | arXiv:2605.22333 | replaces `huang2026caller` ×3 |
| Li & Gao, A First Look at Security Issues in the MCP Ecosystem | **DSN 2026** | `10.1109/DSN69566.2026.00046` | Intro P1 — 67,057 servers, 35× `hasan2025firstglance`, peer-reviewed |
| Wang et al., MCPTox | **AAAI 2026** | `10.1609/aaai.v40i42.40895` | Intro P2, RW P1 — peer-reviewed tool poisoning, replaces reliance on a vendor blog |
| Ni et al., Risk-based access control on fuzzy inferences | ASIACCS 2010 | `10.1145/1755688.1755719` | RW — canonical quantified-risk AC between Cheng 2007 and Kandala 2011 |
| Khambhammettu et al., Risk assessment in access control systems | Comp. & Sec. 2013 | `10.1016/j.cose.2013.03.010` | RW + §4 — the precedent for decomposing AC risk into **object sensitivity** × subject trustworthiness |
| Rose et al., Zero Trust Architecture | NIST SP 800-207 | `10.6028/NIST.SP.800-207` | Intro P5, RW — normative anchor before `bradatsch2024zerotrust` |

**Should add**

- Chen & Crampton, *Risk-Aware Role-Based Access Control*, STM 2011,
  `10.1007/978-3-642-29963-6_11` — formalizes exactly your allow / allow-with-obligation /
  deny risk-band mechanism. Cite at Eq. (1).
- Molloy et al., *Risk-based security decisions under uncertainty*, CODASPY 2012,
  `10.1145/2133601.2133622` — the peer-reviewed treatment of how to set θ_r and θ_d.
- Baracaldo & Joshi, *An adaptive risk management and access control framework to mitigate
  insider threats*, Comp. & Sec. 2013, `10.1016/j.cose.2013.08.001` — risk-adaptive AC for
  principals who are legitimately entitled but acting harmfully. That is your misuse premise,
  with a 2013 precedent.
- El Helou et al., *Hybrid Inspection and Task-Based Access Control in Zero-Trust Agentic
  AI*, arXiv:2605.02682 — the 2026 empirical successor to `fleming2025tbac`, same
  organisation. Omitting it beside your self-declared nearest work is conspicuous.
- Li et al., *ADR*, MLSys 2026 Industry Track, arXiv:2605.17380 — deployed at Uber, 7,200+
  hosts, 10 months. The strongest available evidence that the enforcement-verdict family is
  what industry actually runs.
- South et al., *Authenticated Delegation and Authorized AI Agents*, arXiv:2501.09674 —
  standard reference for the delegation half of "authentication says who is calling."

**Cite the four entries already sitting unused in your bib**: `owireduashley2026severity`,
`li2025accesscontrol`, `shi2025sok`, `almandalawi2025policyaware`. A reviewer who greps the
bibliography will find them and ask why a paper claiming this gap never engaged with them.
`shi2025sok` in particular is a systematization of exactly the Intro P4 framing.

---

## 8. Weak sources carrying load

These are unreviewed single- or low-author preprints supporting load-bearing claims:

| Key | Problem |
|---|---|
| `mellafe2026capability` | 1 author, 7pp, no venue, artifact on a throwaway GitHub org. Cited 3×. |
| `yang2026agenttrust` | 1 author, 31pp, self-labelled preprint, no institutional co-authors |
| `fleming2025tbac` | Named as *the nearest work*; 3-author Cisco preprint, v1 only, never published |
| `huang2026auditing` | 5pp preprint cited 4× as if it were an ecosystem measurement |
| `invariant2025toolpoisoning` | Vendor blog as primary anchor for tool poisoning in two sections |
| `abaev2026agentguardian` | Unreviewed preprint, same institution as the authors, cited 3× |

None of these is disqualifying alone. Together they mean the Related Work rests largely on
unrefereed material, which at an A* venue invites the question of whether the gap is real or
just under-searched. The peer-reviewed additions in §7 fix this cheaply.
