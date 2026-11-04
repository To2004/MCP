# Craft Review

Read-only prose-craft review of `paper_v5/main.tex` for the AAMAS 2027 draft. 37
findings across all six written sections. Fourteen agents did the work: two read
the project's own house-style guides and bibliography first, six reviewed one
section each against that standard, and six more independently re-checked every
cited paper before it was allowed to stay on this list. Nothing in `paper_v5/`
was edited.

**Tally:** 21 confirmed &middot; 9 unverified &middot; 5 needed no citation &middot; 2 fabricated (dropped).

- **Confirmed** — real paper, pattern checked and matches.
- **Unverified** — real paper, but the specific claim about it didn't hold up
  under an independent check. The writing suggestion may still be right; don't
  cite it that way.
- **No citation needed** — a mechanical fix (typo, dangling reference, internal
  consistency check) with no external example to attach.
- **Fabricated** — the citation was invented or inverted the source's actual
  claim. Dropped; noted here so the same citation doesn't get reintroduced later.

## Two of these aren't style nits

- **Implementation, line ~910** calls the MCP server itself "possibly
  untrusted" — the inverse of the project's own non-negotiable framing
  (servers are the protected asset, agents are the threat), and it
  contradicts this same section's "benign-server assumption" stated only 26
  lines earlier.
- **Implementation, lines 955–956** claims a verdict "cannot be steered by
  text an attacker writes," while the two mechanisms named one sentence
  earlier are, by construction, driven by that same text. Narrower claim
  needed.

## Abstract + Introduction (lines 96–108, 163–325)

**lines 170–171 — Confirmed.** Two consecutive sentences restate the identical
claim (an agent's decision landing on organizational assets), only reworded.
*Fix:* delete one, let the MCP sentence follow directly.
*Grounding:* Jafarikhah et al., "From Description to Score" (ACM SAC 2026,
arXiv:2512.06781) — verified ~526 words, no adjacent sentence pair restates a
prior claim.

**lines 99, 189, 217, 225, 231, 233, 237 — Confirmed.** Seven "X, Y, or Z"
triads across ~1,500 words — every enumerable claim stretched to exactly three
items. *Fix:* vary the count per instance instead of defaulting to three.
*Grounding:* Li & Gao, "A First Look at the Security Issues in the MCP
Ecosystem" (DSN 2026, arXiv:2510.16558) — verified 6 citations across ~853
words, gap stated as one directional sentence, not a list. (Also the source of
the "67,000 MCP servers" figure — it's 67,057 registry *listings*, not
distinct servers; cite precisely if used.)

**11 paragraphs, ~1,110 words — Confirmed.** House budget is 650–900 words in
5 paragraphs; this draft runs roughly double the paragraph count. *Fix:* the
four gap-elaboration paragraphs (access control / RAdAC history / "no existing
method" / CVSS-AIVSS) answer the same reader question and can collapse into
1–2 paragraphs with grouped citations. *Grounding:* Jafarikhah et al. — its
full introduction is ~526 words in 4 paragraphs, the project's own
length-calibration anchor.

**lines 247–249 — Fabricated citation.** The framework-naming paragraph
explains both scanners' mechanisms at §4 level of detail instead of naming and
moving on, pushing the Position statement to ~80% through the Introduction
instead of the 40–60% window. *Fix:* cut to one type-level sentence, move
mechanism detail to §4 — this house rule is independently documented, it just
doesn't need the citation below. *Grounding claimed:* "A Scoresheet for
Explainable AI" (Winikoff et al., AAMAS 2025, arXiv:2502.09861) at "paragraph 3
of 6 (~40%)." **Verifier found this false** — the real paper's Introduction has
7 paragraphs, and its actual Position sentence is paragraph 4 of 7 (~57%), not
3 of 6. Number was invented.

**line 105 — Confirmed.** One sentence reports two structurally different
evaluations (static risk surface; 3,000 live invocations) joined by "together
with." *Fix:* split into two sentences, one per evaluation. *Grounding:*
Winikoff et al. — verifier located an actual 65-word paragraph plus others in
the 43–47-word range, confirming the paper favors short single-idea units.

**lines 99, 189, 237 — No citation needed.** Doubled punctuation ("For
example,:"), a stray space orphaning a period after a `\cite`, a two-item list
missing its conjunction. *Fix:* proofread directly.

## Related Work (lines 326–415)

**lines 386–388 — Confirmed.** The "196 evaluators / 68% re-scored
differently" claim cites `first2023cvss` (the CVSS v4.0 *specification*, not a
study) jointly with `wunder2024cvss` (the actual user study). *Fix:* cite
`wunder2024cvss` alone for the empirical claims. *Grounding:* verified directly
against this project's own `INTRODUCTION-GUIDE.md`, which already flags this
exact failure mode for the "67,000 servers" figure — same bug, different
sentence.

**lines 368–376 — Unverified.** Four sentences in a row, each "Author et al.
does X~\cite{}" — the per-paper list the house style forbids — with no closing
gap sentence. *Fix:* compress to 1–2 sentences with grouped citations, add the
missing gap sentence. *Grounding checked:* the cited AAMAS 2025 paragraphs are
real but are usage asides, not the paper's actual claim-and-gap paragraph —
wrong example, though the underlying rule is independently documented in
`WRITING-GUIDE.md`.

**lines 359, 362, 399–401 — No citation needed.** "System A does X, while/
whereas System B does Y" opens four different sentences across three
paragraphs. *Fix:* vary the connective and sentence shape in at least two of
the four.

**line 359 — Unverified.** One sentence joins three ideas via "but" and a
semicolon. *Fix:* split at the semicolon. *Grounding checked:* the DSN 2026
paper's citation sparsity is real, but the guide never actually ties it to
sentence-splicing discipline for this paper.

**line ~406 — No citation needed.** "Together, These methods…" — mid-sentence
capitalization typo in the section's load-bearing closing sentence. *Fix:*
lowercase "these."

**lines 353–357 — Unverified.** ConLeash gets its own single-citation
paragraph, followed by four stray blank lines (an editing artifact). *Fix:*
fold into the preceding paragraph, delete the stray lines. *Grounding
checked:* the cited AAMAS 2025 short paragraphs are real but contain no
citation at all — the "isolated citation vs. claim-plus-gap" distinction isn't
actually in that source.

## Threat Model + Conclusion (lines 416–525, 1348–1386)

**line ~427 — No citation needed.** "This evidence" has no antecedent — its
introducing sentence appears to have been commented out. *Fix:* restore a
trimmed clause or rewrite standalone.

**line 1351 — Unverified.** The Conclusion's opening sentence — highest-
visibility in the paper — is a semicolon-joined double claim. *Fix:* split it.
*Grounding checked:* claimed the DSN 2026 paper delivers its gap statement in
one short sentence; the verifier found it's actually a two-sentence compound
passage. Split-it advice stands regardless.

**lines 1364–1371 — Confirmed.** Four number clusters in the Conclusion's
results paragraph with zero interpretive framing. *Fix:* add one interpretive
sentence after the numbers. *Grounding:* Wunder et al., "Shedding Light on
CVSS Scoring Inconsistencies" (IEEE S&P 2024) — confirmed its headline 68%
statistic is always paired with the interpretive claim it supports.

**lines 1379–1383 — Confirmed.** The paper's final paragraph ends on a generic
hedge ("important directions for further evaluation"). *Fix:* keep the
limitation, follow with one concrete sentence restating the demonstrated
contribution. *Grounding:* Winikoff et al. — verifier located the near-exact
closing text in §6.1: a specific, technical, named open problem, not
boilerplate.

**line 421 — Unverified.** Sentences 3 and 5 of the misuse-definition
paragraph both restate that misuse is a syntactically valid operation. *Fix:*
merge into one sentence. *Grounding checked:* claimed ~565 words with zero
repeated claims for the ACM SAC 2026 paper; independent estimate put it at
~650–700 words with at least one claim repeated. Doesn't hold.

**line 419 — Fabricated citation (bonus catch).** Names "organizational assets
and services," not the MCP server itself, as the protected party — one step
removed from the project's own non-negotiable rule. *Fix:* make the
server-as-protected-party framing explicit; no external paper needed, it's the
project's own rule. *Grounding claimed:* "AgentBound" (ACM FSE 2026,
arXiv:2510.21236) naming "the agent" as the constrained actor. **Verifier
found no such quote in the paper — and worse, AgentBound's actual threat model
is the inverse**: it explicitly targets MCP servers as the enforcement point,
treating the server as the untrusted party. Would have gotten the comparison
exactly backwards. Dropped.

## Methodology (lines 526–814)

**lines 579–580, 632–634, 761–763 — Confirmed.** Three unattributed passive
constructions in a row obscure which parts are deterministic engineering
versus model-derived judgment. *Fix:* give each sentence an explicit actor
("the scanner represents," "we interpret and map," "the Dynamic Scanner
adds"). *Grounding:* Winikoff et al. — verifier fetched the HTML directly:
consistent first-person active voice throughout.

**lines 725, 730, 734 — Confirmed.** All three runtime-factor definitions open
with the identical "This factor captures how…" template; one repeats
"unusual" twice in one clause. *Fix:* vary each opening, drop the doubled
adjective. *Grounding:* CVSS v4.0 Specification (already cited) — spot-checked,
every base metric gets a distinct, metric-specific opening.

**lines 757–759 — Confirmed.** "Because the runtime factors are bounded
below by 1, familiar behavior does not reduce…, while unusual…can increase…"
buries the claim behind a subordinate clause, then stacks a second claim with
"while." *Fix:* front-load and split. *Grounding:* Winikoff et al. — verifier
located a near-exact claim-first sentence in the source.

**lines 793–795 — Unverified.** The section's closing sentence semicolon-joins
two independent claims. *Fix:* split at the semicolon. *Grounding checked:*
the paper does use some short single-claim paragraphs, but the specific
"65 and 45 words" figures couldn't be relocated in the actual text.

**lines 537–543 — Confirmed.** The Overview's paragraph-2 topic sentence names
only one of the two justifications the paragraph actually argues (information
timing; the closer pivots to computational cost with no signal). *Fix:* split
into two paragraphs, or rewrite the topic sentence to scope both. *Grounding:*
Winikoff et al. — consistent with the paper's confirmed style of topic
sentences stating the paragraph's complete claim.

**lines 737–744 — Confirmed.** "Approximately" hedges Eq. 3's bound twice,
scoped neither way. *Fix:* state the bound precisely, hard or soft.
*Grounding:* CVSS v4.0 Specification — every metric range stated as a closed
exact interval, never hedged.

## Implementation (lines 815–1032)

**line ~910 — Confirmed. [correctness, not style]** Calls the MCP server
itself "a possibly untrusted server," contradicting both the project's
threat-model rule and this section's own "benign-server assumption" stated 26
lines earlier. *Fix:* replace "untrusted" with language that stays inside the
benign-server assumption — "self-reported hints, not verified capability
facts." *Grounding:* Hou et al., "MCP: Landscape, Security Threats, and Future
Research Directions" (ACM TOSEM 2026, already cited) — confirmed this survey
treats "agent attacks server" and "server attacks agent" as two distinct,
separately-tracked categories in the field. This isn't a phrasing choice, it's
a category error.

**lines 863–871 — Unverified.** Three consecutive sentences reuse an identical
"table holds one row per X — [field list] — input to Y layer" template; ~19
em-dashes across the section. *Fix:* break the parallelism, convert half the
em-dash pairs to plain sentences. *Grounding checked:* claimed the AAMAS 2025
paper avoids em-dash asides; independent inspection found roughly a dozen in
just its first two sections. Doesn't hold as a comparison; the repetition
observation stands on its own.

**lines 934–940 — Confirmed.** Narrates implementation history chronologically
and drops into passive voice at the pivot sentence, right after two sentences
of active "we." *Fix:* lead with the decision and the number, keep "we" as the
actor throughout. *Grounding:* Winikoff et al. — opens with a direct position
statement ahead of elaboration.

**line 958 — Unverified.** "A tool is not one action; it is one action per
container it can address, and the argument chooses" — a semicolon-joined
clause and an and-joined clause in the same sentence. *Fix:* split into two.
*Grounding checked:* claimed short single-clause sentences for the ACM SAC
2026 paper; its actual abstract uses multi-clause compound sentences.
Contradicts the characterization.

**lines 976–978 — No citation needed.** Introduces a second concrete
illustration (calendar-event update) alongside the paper's established
running example (`delete_file` on `private_key.pem`). *Fix:* re-express the
same point using the existing running example. Internal house-style check, no
external comparison needed.

**lines 1016–1019 — Unverified.** One sentence carries three distinct claims
joined by a semicolon and an "and." *Fix:* split by claim. *Grounding
checked:* the AAMAS 2025 paper cited a third time for "short single-claim
sentences" — again contradicted by independent inspection.

**lines 955–956 — Confirmed. [correctness, not style]** "A verdict
therefore…cannot be steered by text an attacker writes into an argument" is
unscoped; the two mechanisms named one sentence earlier (pattern matching,
weighted token overlap) are, by construction, driven by that literal text.
*Fix:* scope the claim to what's actually ruled out — no natural-language
instruction-following channel, not text-influence in general. *Grounding:*
Shi et al., "Prompt Injection Attack to Tool Selection in LLM Agents" (NDSS
2026, arXiv:2504.19793, already cited) — confirmed ToolHijacker redirects
tool-selection specifically through the model's semantic reading of a tool
description, exactly the channel a deterministic matcher lacks.

## Evaluation + Preliminary Results (lines 1033–1347)

**line ~1040 — Confirmed.** "Server-level risk, tool-level risk, and
request-level safety" is a padded triad; "and therefore" fuses two claims into
one long sentence. *Fix:* trim the list, split the sentence. *Grounding:*
Li & Gao (DSN 2026) — its gap-vs-prior-work statement is one directional
clause, not an enumerated list.

**line ~1042 — Confirmed.** Three predicate clauses stacked with "and"
compress what elsewhere becomes four separate RQs into one sentence. *Fix:*
give each claim its own sentence, matched to where it's tested. *Grounding:*
Jafarikhah et al. — frames its central claim as one direct testable question.

**lines ~1097–1098, ~1104–1105 — Confirmed.** "Was captured," "was derived" —
two passive constructions interrupting an otherwise active-voice paragraph.
*Fix:* "we captured," "we derived." *Grounding:* Li et al., "We Urgently Need
Privilege Management in MCP" (IEEE MASS 2025, already cited) — states its
methodology in active voice throughout.

**line ~1128–1129 — Confirmed.** "Because the Static Scanner uses LLM-based
analysis…, we measure…" buries the claim behind the justification clause.
*Fix:* front-load the claim. *Grounding:* Hasan et al., "MCP at First Glance"
(arXiv:2506.13538, already cited) — leads its methodology framing with the
claim itself.

**lines ~1245–1247 — Confirmed.** Asserts the 84%-deterministic split is
"operationally useful" with no cost/latency number behind it, in a section
otherwise careful to lead with numbers. *Fix:* cut the sentence, or replace
with a quantified claim once §5.3's promised cost figures exist. *Grounding:*
Spring et al., "Time to Change the CVSS?" (IEEE S&P 2021, already cited) — the
canonical argument that unquantified "useful for decision-support" claims are
exactly what reviewers target.

**lines ~1036–1038 — Confirmed.** The section's opening sentence fuses two
separate evaluation questions via "and." *Fix:* split into two sentences.
*Grounding:* Winikoff et al. — short, single-claim declarative paragraphs, not
compound "and"-joined sentences.

## Already tracked elsewhere

Not re-litigated here: `PAPER-REVIEW.md` already carries the substantive
issues — the §4.1/Eq. 2 banding-function mismatch, the RQ3 circularity in the
misuse testbed, missing baselines across all four RQs, the AAMAS venue-fit
risk, and the abstract's overclaims relative to §7. One note there is now
stale: it lists "no Conclusion section (commented out)" — the current draft
has one, at lines 1348–1386, reviewed above.

**Method:** 14 Claude Sonnet 5 subagents, 166 tool calls, ~895k tokens. Two
oriented on the project's own guides and bibliography; six reviewed one
section each; six independently re-fetched and checked every cited paper
before its finding was kept. Read-only throughout.
