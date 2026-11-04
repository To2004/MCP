# Dynamic Layer Knowledge Base

This folder collects the evidence behind the dynamic layer: the per-caller behaviour multiplier
M in [0.7, 5] that turns a static risk score into R = R_static x M (design v4, see
[DIMENSION_FORMULAS.md](../DIMENSION_FORMULAS.md)). It was built on 2026-10-25 to answer an
external review before submission to an A* security or software-engineering venue. Throughout,
the MCP server is the protected asset and the calling agent is the threat.

## Files

| File | What it answers | Lines |
|------|-----------------|-------|
| [01-mcp-protocol.md](01-mcp-protocol.md) | What each MCP revision says about `initialize`, sessions, per-request `_meta` and caller identity; what revision 2026-07-28 breaks in the layer and the gateway | 411 |
| [02-mcp-runtime-security-literature.md](02-mcp-runtime-security-literature.md) | MCP runtime monitors, gateways, benchmarks and datasets (2024-2026); closest competitors; positioning; `refs.bib` problems | 405 |
| [03-ueba-insider-threat-and-datasets.md](03-ueba-insider-threat-and-datasets.md) | How commercial UEBA and the insider-threat literature build baselines; 12 public per-user datasets mapped to the 15 dimensions | 374 |
| [04-score-aggregation-and-calibration.md](04-score-aggregation-and-calibration.md) | Outlier-ensemble and p-value combination theory; what the max becomes on conformal p-values; a calibrated three-stage design | 701 |
| [05-system-map.md](05-system-map.md) | As-built map of the engine, gateway, binding and simulator from the code alone, with ten code-vs-doc differences | 504 |
| [06-threat-model-and-evasion.md](06-threat-model-and-evasion.md) | Adversary classes A0-A4, knowledge K0-K3, coverage per dimension, measured evasions, mitigations M1-M9, paste-ready section 3 | 482 |
| [07-evaluation-methodology.md](07-evaluation-methodology.md) | What S&P, USENIX Security, CCS, NDSS, ICSE and FSE expect; our v4 simulation read against it; a seven-part protocol | 641 |
| [review-assessment.md](review-assessment.md) | A verdict on each reviewer claim (C1-C12), issues the review missed (N1-N31), and gaps in this knowledge base (K1-K16) | see file |
| [improvement-options.md](improvement-options.md) | Candidate changes grouped (a)-(h), each with evidence, cost, risk and kind of work, then a recommended order | see file |
| [v5-design-spec.md](v5-design-spec.md) | The v5 design (revision 2): one pricing rule (commonness and the record rank), the agent-day bound, deployment, evaluation plan, paper plan, author decisions D1-D4 and the Review log of all four reviewers' findings | see file |
| [v5-implementation-plan.md](v5-implementation-plan.md) | Batches 0-7 in dependency order with exclusive file ownership, the external-evidence track X1-X3, and the schedule | see file |
| [context-brief-2026-10-29.md](context-brief-2026-10-29.md) | **Portable summary of the week of 22-29 Oct 2026**, written to be pasted into ChatGPT or Claude: project, MCP facts, the static and dynamic scores, every variable justified, timeline, tests, reviewer critique, ideas backlog, open decisions, glossary, references | see file |
| [dynamic-score-report.md](dynamic-score-report.md) | **2026-10-29, the dynamic score for the paper.** The idea, the six dimensions (Typical Footprint: Tool, Asset, Tool on asset; Typical Cadence: Calls this hour, Breadth, Time of day), each with why it matters and its ordinary look-alike; the formula in plain words; eight formulas compared; design checks; limits; a LaTeX draft in the static section's style | see file |
| [behaviour-formula-candidates.md](behaviour-formula-candidates.md) | **2026-10-29.** Six candidate formulas for M on the 6 agreed dimensions, with a simulation (125 checks × 3 seeds) and a literature check. Counting days, not calls, matters most; recommends F (rank on days, Tool on asset per asset) | see file |
| [static-and-dynamic-formulas.md](static-and-dynamic-formulas.md) | **Current design (2026-10-28).** Both scores side by side. Static, as in the paper draft: ToolImpact, AssetSensitivity, BlastRadius and ParameterRisk, combined by a 0.3/0.3/0.3/0.1 weighted sum; where the code differs; notes for the paper. Dynamic: the 8 general dimensions, the one formula, why it has this form, the guarantee, how the two combine, prototype checks (154/164), and decided and open choices | see file |
| [behaviour-multiplier-formula.md](behaviour-multiplier-formula.md) | **Proposal, revision 2 (2026-10-28).** M as one formula, ((A+1)/(2D+1))^γ: agent id only, 8 dimensions, no Red Flags or policy file. Its form comes from three stated requirements, with a conformal false-alarm bound, the price in power, threats, experiments E1-E7 and four judges' review. It would replace v5 spec §2.3-2.5 | see file |
| [v5-calibration.md](v5-calibration.md) | Record of revision 1's calibration (arm S5 on v4 scores) and the proposals it beat, with a table of what revision 2 supersedes | see file |
| [probes/README.md](probes/README.md) | Every probe script in `probes/`: what it measures, its inputs and which document uses it | see file |

## How to use it

1. Start with [review-assessment.md](review-assessment.md). It gives each reviewer claim a verdict
   and severity, and cites the evidence in notes 01-07 and the code.
2. Choose work from [improvement-options.md](improvement-options.md). Its last section gives the
   recommended order: text fixes first, then small code fixes and logging, then design changes,
   then a frozen held-out evaluation.
3. Go to the numbered notes for the detailed evidence. Each one has its own sources and its own
   UNVERIFIED list.
4. Before pasting LaTeX from a note into the paper, check the "Contradictions resolved" table
   below and the knowledge-base gaps (K1-K16) in the review assessment. Several notes still carry
   statements that later checks overturned.
5. Spec facts are as of 2026-10-25. The MCP revision marked Current on that date is 2026-07-28.

Provenance in these files is stated as "opened by" (who in this workflow opened the primary
source). The numbered notes, the claim checkers, the judges and the gap hunters each opened their
own sources. The two synthesis files (review-assessment and improvement-options) pass on that
status without re-opening external pages. The author of the synthesis files re-read these code
lines: `engine.py:574`, `engine.py:74-75`, `framework.py:184-207`, `oauth.py:110`,
`normal_org_world.py:525`, `policy.py:53,56`, `main-restructured.tex:864-868` and
`paper_v5/README.md:13-15`.

Probe scripts behind many measured numbers (M = 3.62 on a sessionless merge, the evasion probes
E1-E13, the binding probes) live only in the session scratchpad and are not in the repository.
This is gap K11.

## Contradictions resolved

The notes were written in parallel, and in places they disagree. Use the statement in the right
column.

| Topic | Where the notes disagree | Statement to use |
|-------|--------------------------|------------------|
| Is the rarity score an empirical p-value? | 03 section 2 and 07 section 3.4 say yes; 04 section 1.2 heading says "calibrated" | No. e = (N+1)/(A+1) = lambda_hat x p_split: a plug-in conformal p-value times his calls per active day. It is the expected number of his calls a day at least this rare, and it can exceed 1. It is a per-day rate, not a p-value, and it is not calibrated (05 section 5; claim C9). |
| Does M read arguments? | 02 and 06 say M is argument-free | M receives no argument values. Its asset comes from the binding, which matches every string argument against register ids when a tool has two or more candidates. Its size input includes the arguments (05 section 2; C5). |
| Can the ablation and combiner arms run offline? | `DIMENSION_FORMULAS.md:851-854` and 02 say a rerun is needed; 07 section 3.4 and 04 section 6.3 say offline | M feeds nothing back into state, so every arm can be recomputed offline from logged per-call score vectors. Nothing logs those vectors today (the simulator pickle in /tmp is gone, and no gateway log has a `behaviour` field), so one instrumented rerun is needed first. |
| Calibration unit and combiner form | 07 says per call with Sidak; 04 says per agent-day with weighted Bonferroni | Compute p-values per call, but state guarantees and report results per agent-day. Use weighted Bonferroni (valid under any dependence); report Sidak only as a sensitivity check. Calibrate oversized request and missing handshake at org level. |
| Baseline key | 01 says (issuer, subject, client_id); 06 says pool by `sub` | Use a user-level baseline on (iss, sub), with client_id as a Footprint value of that user. This is pending a check of RFC 9068, 8693 and 7662 for which claims a gateway can rely on (K8). |
| Zimek et al.'s "missing costs more" exception | 04 section 2.3 says both exceptions hold | Only the multiview/subspace exception fits. The design treats false alarms as a first-class cost, so the cost-asymmetry exception does not apply unless it is stated and scoped (for example, to the first-access floor) (C11, K4). |
| Date of "MUST NOT use sessions for authentication" | 01 dates it to 2025-11-25 | It is already in the 2025-06-18 revision (re-checked by the completeness critic on the GitHub tag) (K9). |
| CLUE-LDS coverage | 03 says 13 of 15 dimensions | 8 direct plus 5 by proxy, by 03's own matrix (K13). |
| Warm-up | 03 section 6.10 says first day only | At least 5 tool calls AND past the first UTC day (`engine.py:288-290`). |

## Per-dimension status

One row per v4 dimension. "Legacy" means MCP 2025-11-25 and earlier; "modern" means 2026-07-28.
"Asset from arguments" means the dimension depends on the binding's argument matching.

| # | Dimension | Group | Legacy | Modern | Asset from arguments | Main known weakness (see review-assessment) |
|---|-----------|-------|--------|--------|----------------------|----------------------------------------------|
| 1 | Call rate | Cadence | yes | yes | no | call-weighted "usual" (N5); replicas split counts (N13) |
| 2 | Write rate | Cadence | yes | yes | no | read/write decided per tool name, not per method (N17) |
| 3 | Breadth | Cadence | yes | yes | yes | collapses to one worst-case driver on unresolved calls (N1) |
| 4 | Repetition | Cadence | yes | yes | yes | distinct unregistered repositories look like repetition (N1) |
| 5 | Session duration | Cadence | only with server-minted session ids | never takes part | no | measures the host app, not the agent (SEP-2567); restarts reset it (C1, N13) |
| 6 | Hour of day | Cadence | yes | yes | no | counts calls not days, so one night poisons it (N5); UTC (N27) |
| 7 | Tool | Footprint | yes | yes | no | a never-seen tool can score below a tool seen once (N7); multiplexed tool names (N17) |
| 8 | Asset | Footprint | yes | yes | yes | worst-case driver and facets as identity; free-text steering (C5, N1) |
| 9 | Network | Footprint | yes | yes | no | hosted connectors share one /16 (N28) |
| 10 | Client | Footprint | from `initialize` clientInfo | clientInfo optional, self-reported | no | free to spoof; a new client_id is a new identity (N8) |
| 11 | Burst | Red Flags | yes | yes | no | learned limit pooled over bots and people (N18); habit discount (N6) |
| 12 | Sweep | Red Flags | yes | yes | yes | cannot be learned from a gateway log; collapse (C5, N1) |
| 13 | Oversized request | Red Flags | yes | yes | no (size includes arguments) | fires on 1.92% of ordinary agent-days against a 0.5% target (C3, N18) |
| 14 | Unsafe sequence | Red Flags | session-scoped | `requires_before` fires on every call (bug); read-then-write never fires | yes | session split, any-PR review, habit discount loses cross-copy (C1, N6, N16) |
| 15 | Missing handshake | Red Flags | Streamable HTTP with session ids only | never | no | restarts and session eviction cause false alarms; the caller can choose stateless (C1, N13, N16) |

## UNVERIFIED ledger

Items that no one in this workflow could confirm on a primary page. Do not cite them as fact.

- 02: the Kai Security primary post (only a secondary summary was opened); the CrossMCP-Bench
  NeurIPS venue (dataset card only); the ADR GitHub repository; the MDPI Electronics 15(13):2829
  DOI; the MCPTox AAAI DOI, MSB at ICLR 2026 and Parasites at S&P 2026 (arXiv comments only).
- 03 and 07: the Tuor et al. 2017 venue (03 states it as fact, 07 marks it UNVERIFIED); Kent 2015
  (the LANL citation), Hagberg 2014 and Bian 2021 (not opened); the GH Archive licence.
- 04: the Benjamini-Yekutieli sum-of-1/i constant, the Massart DKW constant, Good 1953, and Vovk
  2005 (Mondrian conformal).
- The design and notes call the max "the standard disjunction of fuzzy logic" with no citation
  (Zadeh 1965 was not opened). Zimek et al.'s year is 2014 per the DOI, but 2013 in some author
  lists.
- Aggarwal & Sathe 2015: opened in full by the 04 author and the completeness critic (quotes on
  pp. 35-37 check out); one judge's re-fetch failed. Treat it as verified, with that note.
- C8: Anderson 1980's masquerader/misfeasor taxonomy (the scanned NIST PDF has no text layer);
  Salem et al. 2008 (listed as opened in 06, not re-opened by the judge); the verbatim wording of
  Arp et al. pitfall P10.
- C6: the Splunk ES risk-based-alerting example (the fetch returned only navigation).
- C3: checker 2's per-dimension figures (its output files were empty).
- C2: whether a GH Archive replay through the GitHub MCP tool mapping is feasible.
- K8: which claims (`sub`, `client_id`, `act`) a gateway can rely on (RFC 9068, 8693 and 7662 not
  opened for this question).
- K13: AIDev (arXiv 2602.09185) and "Fingerprinting AI Coding Agents on GitHub" (arXiv
  2601.17406), reported by the completeness critic and not opened by the synthesis author.
- N28 and N30: whether hosted agent platforms supply origin attributes; whether a given upstream
  server decodes compressed request bodies.

## References

- [DIMENSION_FORMULAS.md](../DIMENSION_FORMULAS.md): design v4.
- [DYNAMIC-LAYER-V4-NOTES.md](../../../../paper_v5/DYNAMIC-LAYER-V4-NOTES.md): paper notes and
  paste-ready LaTeX.
- [main-restructured.tex](../../../../paper_v5/main-restructured.tex): paper draft.
- Engine: `src/mcp_security/behaviour/` (engine.py, memory.py, policy.py). Gateway:
  `src/mcp_security/gateway/` (proxy.py, framework.py, oauth.py, wire_log.py). Binding:
  `src/mcp_security/binding/`.
- Simulator: `normal_org_world.py`, `normal_org_engines.py`, `normal_org_sim.py` in the parent
  folder; results in `../results/normal_org_*.md`.
