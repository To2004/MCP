# Dynamic Layer Improvement Options

This file lists the candidate changes to the dynamic layer (design v4, M in [0.7, 5],
R = R_static x M) that follow from the review assessment and notes 01-07. Each option says what to
change, why (with a pointer to the evidence), what it costs, what it risks for current behaviour,
and whether it needs code, a simulation run, or only text. The last section gives a recommended
order of work.

## How to read this

- **Evidence IDs**: C1-C12 (reviewer claims), N1-N31 (issues the review missed) and K1-K16
  (knowledge-base gaps) are defined in [review-assessment.md](review-assessment.md). Numbered
  notes are [01](01-mcp-protocol.md) to [07](07-evaluation-methodology.md).
- **Cost**: small = under a day, no rerun; medium = a few days or one simulator rerun; large =
  weeks, new data, or other people.
- **Risk** is to current behaviour or current results. "None" means text only. "High" means alert
  sets or headline numbers will change.
- **Needs**: text, code (engine, gateway or binding, with tests), or simulation (a run of
  `normal_org_sim.py` or a new world family).
- Per the project's rule on design versions, every option that changes behaviour should ship as a
  selectable v5 path (`BehaviourConfig.design`), with v4 kept runnable and its doc saved as
  `DIMENSION_FORMULAS_v4.md`.

## (a) Protocol compatibility

**a1. Treat a missing session as "not evaluable" in `requires_before`.**

- *Change.* At `engine.py:574`, return False (or fall back to the per-principal spell of a3) when
  the session is None. Do not flag a violation. Add a regression test: a sessionless merge after
  `pull_request_read`, with a hand-written `requires_before`, must give M of about 1.
- *Why.* C1. Today every sessionless call to a guarded tool scores M = 3.62 on day 0, then the
  habit discount trains the rule off, leaving a blind spot.
- *Cost* small. *Risk* low: it changes only calls without a session id; legacy sessioned traffic is
  unchanged. *Needs* code.

**a2. Classify each request's protocol era and log it.**

- *Change.* Derive legacy or modern from the transport, `_meta` protocolVersion and the
  MCP-Protocol-Version header. Put it in the decision record and in `Message`.
- *Why.* C1; 01 section 4. Without it, no result can be reported per era. All captured traffic is
  2025-11-25.
- *Cost* small. *Risk* none (logging only). *Needs* code.

**a3. Replace "session" with a per-principal "spell" for sequence and duration checks.**

- *Change.* A spell is a run of one principal's calls ended by an idle gap G, with G calibrated on
  the org's own inter-call gaps. Use it for `requires_before`, read-then-write and session
  duration. Learn required steps over spells in `policy.py`. Keep server-minted sessions as an
  optional legacy refinement.
- *Why.* C1 (modern traffic has no session). SEP-2567 notes that session lifetime is set by the
  host app. N16: the session is a scope the caller chooses.
- *Cost* medium. *Risk* medium: sequence and duration results change in the legacy era too.
  *Needs* code and simulation.

**a4. Add modern-era successors to "missing handshake".**

- *Change.* A conformance red flag for: required `_meta` keys missing, Mcp-Method, Mcp-Name or
  MCP-Protocol-Version headers that disagree with the body, or legacy artefacts on a modern
  request. An era-downgrade flag for a principal who normally speaks modern. Protocol version and a
  capabilities fingerprint as Footprint rarity values. Self-reported fields may only raise M,
  because the spec says clientInfo SHOULD NOT drive security decisions.
- *Why.* C1; 01 "Proposed version-scoped replacements".
- *Cost* medium. *Risk* low: these are new dimensions, and under a max they add false-alarm mass,
  so they must be measured (N19). *Needs* code and simulation.

**a5. Add gateway-level protocol checks.**

- *Change.* Compare the MCP-Protocol-Version header with `_meta`, and stop silently preferring the
  header. Flag missing required headers. For modern traffic, flag a state handle minted for one
  principal and presented by another. Keep SessionBook and `session_agent_mismatch` for legacy.
- *Why.* C1; 01 section 4: the gateway never compares the two version sources and never checks
  `Mcp-Param-*`.
- *Cost* medium. *Risk* low. *Needs* code.

**a6. Score `resources/read` and `prompts/get`.**

- *Change.* Map each resource URI template to a pseudo-tool (for example
  `resource:repository_content`) and its URI variables to an asset. Scan them statically. Feed them
  to Cadence, Footprint and Red Flags. In 2026-07-28 traffic the Mcp-Name header carries the URI.
  Report the share of request methods that are scored.
- *Why.* N12: github-mcp-server serves raw repository files as resources, and these bypass the
  layer today.
- *Cost* medium to large (the static scan needs extending). *Risk* medium: new calls enter
  baselines and limits. *Needs* code, a scan, and simulation.

**a7. Fail closed on bodies the gateway cannot parse.**

- *Change.* Return 400 for bodies that do not parse into a JSON-RPC object with a string method.
  Decode or reject a non-identity Content-Encoding. Forward the canonical re-serialised message.
  Count unscored forwards.
- *Why.* N30.
- *Cost* small. *Risk* low to medium: some odd but legitimate traffic may be rejected. *Needs* code.

**a8. Build modern-era and mixed-era simulator worlds.**

- *Change.* A world variant with no session ids, `_meta` on every request and some clients without
  clientInfo, and a variant that migrates mid-run. Remove the protocol-impossible "stateless bot
  that keeps session ids". Report false alarms and catches per era.
- *Why.* C1. All v4 results are legacy-era results.
- *Cost* medium. *Risk* none to v4 (new worlds). *Needs* simulation.

**a9. Make legacy session state robust.**

- *Change.* Persist open sessions (start, initialized, tools, `read_sensitive`) with a TTL across
  restarts. Add per-identity session quotas, and evict within the same caller first. Create a
  SessionState only after the server has assigned or accepted the id.
- *Why.* N13: x3.62 after a restart inside a reviewed session. N16: 1,001 junk ids evict a
  victim's session.
- *Cost* small to medium. *Risk* low. *Needs* code.

## (b) Score calibration and the shared scale

**b1. Reword the scale claim.**

- *Change.* "Every score maps to M through the same function, so s = 0.5 means x1 for every
  dimension. Each family reaches 0.5 at its own point: the excess score at 2mu + u; rarity at
  e = kappa - 1/2 (every other day for asset and hour, once in 2.5 days for tool, network and
  client)." Call kappa a weight that scales the curve, not a cap. Say the scores are commensurate
  in unit, not in false-alarm rate. Red flags, the floor and the org-discount cap are set values,
  not points on the curve.
- *Why.* C3, C10.
- *Cost* small. *Risk* none. *Needs* text (see h2 and h3).

**b2. Pin each family's edge in tests.**

- *Change.* Unit tests: the excess score is 0.5 at 2mu + u for small and large mu; rarity is 0.5 at
  e = kappa - 1/2 for kappa = 0.9 and 1.
- *Why.* C10. Today only `multiplier(0.5) == 1.0` is tested.
- *Cost* small. *Risk* none. *Needs* code (tests).

**b3. Publish a benign table per dimension.**

- *Change.* In `normal_org_sim.py score_shard`, keep each dimension's daily max and per-call s_d,
  saved under `results/`, not /tmp. Report P(daily max >= 0.5), P(>= 0.841), q50/q90/q99/q99.9 and
  each dimension's share of x3 false alarms, against an equal 1/15 budget, for all five
  organisations. Checker 1's `c3_scale_check.py` is a prototype.
- *Why.* C3: benign exceedance at 0.5 spans about 7,000x across dimensions.
- *Cost* small to medium (one instrumented rerun). *Risk* none. *Needs* simulation.

**b4. Test a calibrated max as an ablation arm.**

- *Change.* Turn each dimension into a conformal p-value against the caller's own history and
  combine with weighted Bonferroni (q = min_d lambda_d p_d / w_d). Then add stage 3: calibrate the
  combined score against his own past calls, q3 = (1 + #{past calls with q <= q(c)})/(A+1).
  Stage 3 gives an exact per-agent-day false-alarm bound under day-exchangeability, and keeps M in
  (0.7, 4.67] at A = 90.
- *Why.* C3, C11 (Zimek's normalisation precondition); 04 section 6. Without stage 3, honest
  multiplicity correction caps M at x2.24 with 90 days and 15 dimensions.
- *Cost* medium. *Risk* high if adopted: the alert set changes. As an arm, none. *Needs*
  simulation first, code only if adopted. Caveats from 04 section 8 apply: daily learning, drift,
  the weekly cycle, and an agent shaping his own baseline all break exchangeability.

**b5. Fix the learned red-flag limits.**

- *Change.*
  - Learn the 99.5% quantile of each agent-day's maximum size-to-limit ratio across tools, or
    split the 0.5% budget across tools.
  - Require 200 agent-days before a tool gets its own limit.
  - Let each identity contribute one agent-day.
  - Learn separate lines for bots and people.
  - Fall back by operation class (the median write limit for an unseen write tool), never the
    global maximum.
  - Re-learn when the catalog digest changes, with capped growth.
  - Report each flag's realised raise rate against its nominal 0.5%.
- *Why.* C3, C7, N18. Oversized request fires on 1.92% of ordinary agent-days against a 0.5%
  target and causes 71% of x3 false alarms. With n < 200 the quantile is the sample maximum.
- *Cost* medium. *Risk* medium: it lowers the main false-alarm source but may move catches of big
  paste. *Needs* code and simulation.

**b6. Make the rarity score monotone at novelty.**

- *Change.* Set N_d(unseen) = min(nu_d, the mass of values used once), or use one Good-Turing-style
  unseen-mass estimate. State it as a lemma, and add a property-based test that s_d is
  non-increasing as n_d(v) goes 0, 1, 2, ... over random histories.
- *Why.* N7: a never-touched asset scores x2.01 while an asset used once scores x4.10. This breaks
  property 5.
- *Cost* small. *Risk* medium: novelty scores rise for agents who started many values that later
  became frequent, so false alarms may rise. *Needs* code and simulation.

**b7. Optional exact-midpoint arm.**

- *Change.* tau_d = 4 kappa_d - 2 (1.6 for kappa = 0.9), and the excess form
  (x + tau u)/((x + tau u) + tau (mu + u)), so that 0.5 falls exactly at "every other day" and
  "twice the usual". Do not use min(kappa, 1/(1+2e)), which flattens the graded top.
- *Why.* C10, if the native-unit claim is to hold exactly.
- *Cost* small. *Risk* none (a sensitivity row next to "ceilings 0.9 -> 1"). *Needs* simulation.

**b8. Place red flags and the first-access floor explicitly.**

- *Change.* Either declare them policy overrides outside the calibrated statistic (04 section 6.4),
  or price each by its measured benign rate instead of 0.9 and 0.7.
- *Why.* C3, C7: 0.9 sits 0.06 above the x3 threshold s* = 0.8413, so every flag alerts alone and
  flag-driven catches hold by construction.
- *Cost* small (text) or medium (pricing). *Risk* none or medium. *Needs* text, or simulation.

**b9. Handle small and stale histories.**

- *Change.* Add a "days since last active" dimension, scored as rarity against his own gaps. While
  A < A_min (for example 10), floor M at 1 or shrink e toward a role or org prior (hierarchical
  pooling). Re-enter learning after long inactivity.
- *Why.* N10: a dormant account returning from a new network, client, tool and asset at 02:00
  scores M = 0.89. Vendors wait longer before scoring (Entra at least 5 days, Exabeam until 80%
  model confidence, Elastic at least 20 buckets; 03).
- *Cost* medium. *Risk* medium. *Needs* code and simulation (dormant and sparse identities).

**b10. Compute day, hour and weekend in local time.**

- *Change.* Use a time zone from an IdP claim or a learned modal offset. Roll the day over at 04:00
  local. Make the weekend configurable. Add APAC and daylight-saving agents to the simulator, and
  report false alarms by time-zone group.
- *Why.* N27: a UTC-6 workday spans two UTC days, which inflates A; warm-up length depends on the
  start time.
- *Cost* medium. *Risk* medium (hour and weekend scores change). *Needs* code and simulation.

## (c) Aggregation

**c1. Rewrite "Why the strangest wins".**

- *Change.*
  - Reframe the max as the multiview/subspace choice aimed at sparse misuse, where one dimension
    is far off.
  - Quote Zimek et al. as they read: they prefer the average, warn that a single far-off detector
    decides the result, and allow the max over separate subspaces.
  - Cite Birnbaum 1954 (no method optimal in general) and Heard & Rubin-Delanchy 2018 (when min-p
    is optimal).
  - Delete "not a shortcut: it is what makes the rest of the design work".
  - Property 3: "inflates false alarms less than a sum", and show the 71% share.
  - Property 4: "a bounded M does not fix the false-alarm rate; each added dimension adds about its
    own rate".
  - Property 6: rest it on the common s-to-M map.
  - Give each combiner its own threshold in the toy table, or drop the table.
- *Why.* C4, C11, K4.
- *Cost* small. *Risk* none. *Needs* text.

**c2. Run a matched-budget combiner ablation.**

- *Change.*
  - Arms: max (v4); mean; noisy-OR; soft-OR s1 + a s2 (1 - s1) with a in {0.1, 0.3, 0.5}; top-2
    mean; group-AOM (max within group, mean across); Thresh (sum of excess over 0.5); Tippett,
    weighted Bonferroni, HMP and Cauchy on calibrated p (b4); stage 3 (b4); accumulation (c5).
  - Give each arm its own threshold, fitted to the same alpha in {1, 2.5, 5}% on days 90-134, and
    test on days 135-179. Also report at fixed list sizes k in {4, 8}.
  - Report recall against false alarms, partial AUC up to 5%, and paired bootstrap intervals over
    agents.
  - Preregister the rule: keep the max if it is within a stated non-inferiority margin of the best
    arm at each alpha.
- *Why.* C4. The only equal-budget evidence is a tie (53.2 against 54.4 at top 4; 65.8 against
  63.3 at top 8; one organisation, v3).
- *Cost* medium. *Risk* none unless the max loses. *Needs* simulation (one instrumented rerun, then
  offline).

**c3. Correct the "needs a rerun" statement and log what offline arms need.**

- *Change.* M feeds nothing back into state (`engine.py:297-299, 504-515`), so combiner, dimension
  and group arms are offline-computable from per-call score vectors (plus e_d, ratios, k_f and
  first-use events). Nothing logs these today, so make one instrumented rerun the first step.
  Correct `DIMENSION_FORMULAS.md:851-854`.
- *Why.* C4, K3.
- *Cost* small. *Risk* none. *Needs* text and code (logging).

**c4. Fail closed when a dimension cannot take part.**

- *Change.* Score a missing client, network or session as its own value ("none") by rarity, or raise
  a flag when he normally sends it. Report benign false alarms by the number of participating
  dimensions.
- *Why.* N19: a sessionless call with no clientInfo is scored on 8 of 15 dimensions, and under a max
  fewer participants can only lower s1, so the caller chooses which evidence counts.
- *Cost* medium. *Risk* medium (more participants means more false-alarm mass). *Needs* code and
  simulation.

**c5. Add an accumulation arm.**

- *Change.* A daily or 24-hour sum of per-call risk, or a count of calls above 0.5, in the style of
  Exabeam (session sum >= 90) and Splunk RBA (24-hour sum > 100). Compare it with the per-call max
  on slow multi-day episodes.
- *Why.* 03 section 2: vendors add risk across events, while v4 never accumulates. Scope creep is
  caught on only 2% of its calls at x3.
- *Cost* small as an arm. *Risk* none. *Needs* simulation.

**c6. Use one aggregator in the paper.**

- *Change.* Replace the product L = D·A·N (`main-restructured.tex` ~:848) and the "most severe
  proposal" rule (~:955) with M = g(s1), or evaluate them as arms.
- *Why.* C4, N2.
- *Cost* small. *Risk* none. *Needs* text.

## (d) Asset identity and the "no arguments" claim

**d1. Reword the claim.**

- *Change.* "M receives no argument values. It consumes the call's asset as resolved by the static
  side's deterministic, model-free binding, that asset's scanned sensitivity, read or write from
  the tool's impact level, client and network from the transport, and the request size in bytes
  (which includes the arguments)." Delete "cannot be steered by text an attacker writes into an
  argument", or qualify it: "a decoy cannot lower the driver once the true container is named, but
  free-text strings can change which asset is resolved".
- *Why.* C5, K1.
- *Cost* small. *Risk* none. *Needs* text (paper, notes, docstrings, notes 02 and 06).

**d2. Specify asset identity as Step 0, and make the paper match the code.**

- *Change.* Describe the rule that actually runs:
  - one candidate: no arguments are read;
  - otherwise: every string is matched by name coverage >= 0.8, partial siblings are excluded and
    facets are kept, and the worst survivor drives;
  - no match: the worst of all candidates (basis "unresolved");
  - no cells: asset None.

  Either replace the Discovery/AssetResolver text (`main-restructured.tex:900-918`) with this rule,
  or wire AssetResolver and Discovery into RouteScorer and evaluate that. Restore the commented
  assumption at :432. State the limitation for the 11 of 49 tools with no cells.
- *Why.* C5.
- *Cost* small (text) or large (wiring the resolver in). *Risk* none or high. *Needs* text, or code
  and simulation.

**d3. Split the two roles of the asset.**

- *Change.* R_static keeps the worst-case register driver, for safety. The behaviour engine gets a
  separate identity key: the concrete container handle from the matched identifier argument
  (pseudonymised), or `unresolved:<tool>:<hash of the raw container value>`. Use that key for
  breadth, repetition, asset rarity, sweep, unsafe sequence and the first-access floor. Add
  `basis` and `worst_case` to `Message`. For unresolved calls, never write the worst-case driver
  into `assets`, `last_read` or `read_sensitive`; emit a separate "unresolved target" signal.
- *Why.* N1 (critical) and C5:
  - false x3.62 on a developer's first routine read;
  - a false sequence on read-then-issue, which then habituates;
  - 40 repositories count as one asset;
  - the first-access floor for helios-scada-gateway is disarmed (M = 0.888 against x3.62 for a
    fresh user);
  - facet ids score the same public repository as three new sensitive assets.
- *Cost* medium. *Risk* high on the live route (many alerts change), none on the current simulator
  (it already passes oracle names). *Needs* code, tests and simulation (d8).

**d4. Match only identifier-typed inputs.**

- *Change.* Restrict binding matches to schema-declared or breadth-classified container keys
  (owner, repo, path keys), not free text such as body or content. When the container key itself is
  unresolved, keep the worst case whatever the other strings say.
- *Why.* C5, K1: `path='docs/helios-public-site.md'` moves the driver from sensitivity 5 to 4.
- *Cost* small to medium. *Risk* low: some calls become unresolved, which errs high on R_static.
  *Needs* code.

**d5. Key the tool dimension on (tool, operation).**

- *Change.* Where the breadth spec marks an enum operation argument (`method`), key Footprint on
  (tool, method), and set read or write per (tool, method). Rename "merge with no review", or
  require the same asset plus an approved review state read from the response.
- *Why.* N17: the remote GitHub server multiplexes create, update and get behind one tool name.
- *Cost* medium. *Risk* medium. *Needs* code, a scan, and simulation on the remote catalog.

**d6. Learn the sweep limit and asset fields from the gateway log.**

- *Change.* Make `messages_from_log` join each request with its `gateway.decision` record and read
  asset, sensitivity and operation from it. Correct `policy.py:15-16` and Open decision 3.
- *Why.* C5: the sweep limit can never be learned from a log today.
- *Cost* small. *Risk* low. *Needs* code.

**d7. Add regression tests for the binding failures.**

- *Change.* Tests for: the decoy-path steering case; 30 unregistered repositories collapsing to one
  id; the same public repository read through `list_issues`, `search_code` and `push_files`
  raising false floors and a false sequence; an unresolved read masking the later first-access
  floor of the real SCADA read.
- *Why.* C5, N1.
- *Cost* small. *Risk* none (the tests document current failures until d3 and d4 land). *Needs*
  code.

**d8. Evaluate with the resolver in the loop.**

- *Change.* Either generate concrete tool arguments per simulated call and resolve them with the
  live MatrixScorer against a register shaped like the real scan (facets, a few named repositories,
  unregistered ones), or replay each world as JSON-RPC through `gateway/proxy.py` with OAuth tokens
  and the scan (extend `scripts/gateway_replay_corpus.py`). Report: resolution accuracy; the false
  floors and false sequences added; the breadth and sweep collapse; and the change in false alarms
  and catches against the oracle-asset numbers, with and without d3 and d4.
- *Why.* C5, N1, N15. Every v4 result assumes perfect repository-level resolution.
- *Cost* medium to large. *Risk* high for the headline numbers, which is the point. *Needs*
  simulation.

**d9. Use the response channel.**

- *Change.* Add response bytes and returned items, per call and per hour, as Cadence excess
  dimensions, plus a per-tool response-size red flag learned like the request limit. These arrive
  after the call has run, so they feed the next call's M and the daily list. Say so in the paper.
- *Why.* N20, C12: over-fetching is caught 0 of 47 times. Open decision 4 says this needs an
  argument, but the proxy already parses every reply.
- *Cost* medium. *Risk* low (new dimensions; measure their false-alarm mass). *Needs* code and
  simulation (the simulator must emit response sizes).

## (e) Ranking objective

**e1. Name three outputs and their objectives.**

- *Change.* Add "Outputs and their objectives" after Step 3:
  - (A) per-call R = R_static x M, which orders or gates calls by expected consequence;
  - (B) the daily review list ranked by (M, s2), which finds the most gray episodes per analyst
    budget and deliberately leaves out R_static;
  - (C) the per-call alert at M >= 3.

  State that M is "behaviour plus first-access sensitivity" on purpose, and that s2 is a tie-breaker
  (it cuts ties at the list's cut from 35.2% to 2.2%), not a catch-rate gain.
- *Why.* C6, K2.
- *Cost* small. *Risk* none. *Needs* text.

**e2. Use one R_static scale everywhere.**

- *Change.* Define R_static' = (T·S·B)^(1/3) in the paper, the gateway and the simulator, and give
  bands for R in [0.7, 25]. Retire or rename the gateway's legacy `risk` = cell x B·L field
  (`framework.py:200`), so that `dynamic_risk` is the one framework output.
- *Why.* N2, C6. On the paper's 1-125 bands, M would act as a factor up to 125.
- *Cost* small to medium. *Risk* medium for any consumer of the `risk` field. *Needs* code and
  text.

**e3. Test R on its own terms.**

- *Change.* Make the simulator's static score depend on the (tool, asset) cell. Weight gray episodes
  by consequence (the highest sensitivity touched, x2 for writes or deletes). Compare review keys at
  a fixed budget: (M, s2); (R, s2) with the agent-day represented by its max-R call; and M >= 3 first,
  then R. Add per-call precision@k for R against M.
- *Why.* C6. The only R-like arm used a per-tool static score and an unweighted label, and lost by
  4-22 points in every organisation.
- *Cost* medium. *Risk* none (new arms). If R still loses on harm-weighted recall, demote R to a
  reporting score and change 02's novelty claim 2. *Needs* simulation.

**e4. Fix the review-list metric.**

- *Change.* Credit an episode only when the listed agent-day's top call (d*) is one of its calls.
  Report the lift over a random ranking per kind. Set k as a share of active agent-days (weekday and
  weekend separately). Report recall@k curves for k = 1 to 16, and days to first listing for
  multi-day episodes. Recompute the v3-to-v4 deltas with one k throughout.
- *Why.* N4: a random list catches 25.9% of scope creep at k = 4; the large organisation is
  reported at top 8 without saying so; top 4 throughout gives 55.8% to 53.6%.
- *Cost* small to medium. *Risk* high for reported list numbers. *Needs* simulation (analysis).

**e5. Report harm before the first alert.**

- *Change.* Per episode, report the time to the first x3 call and the calls, distinct assets and
  bytes delivered before it. For a hypothetical gate, report the ordinary-call block rate per
  agent-day, separately for people and bots.
- *Why.* N23: only 2% of scope-creep calls and 8% of mass-cleanup calls reach x3.
- *Cost* small. *Risk* none. *Needs* simulation (analysis).

**e6. Log what the list and the ablation need.**

- *Change.* Put `Verdict.scores` (or at least s1, s2 and their dimension names), the era (a2) and
  the resolution basis into the gateway decision line. Either implement agent-day ranking in
  `gateway/score.py`, or label the review list as an evaluation construct.
- *Why.* C6, K3, N25: no gateway log can rebuild the (M, s2) list or the planned ablation.
- *Cost* small. *Risk* none (log size grows). *Needs* code.

**e7. Make reasons informative, then test them.**

- *Change.* Emit structured reasons: the mechanism (rarity, floor, org-discounted,
  habit-discounted), the raw counts behind e or x/mu, and s2 with its dimension. Then run a small
  analyst triage study with and without reasons, measuring time and accuracy, or drop the
  interpretability claim for the dynamic layer.
- *Why.* N26: "asset 0.90" reads the same for a first sensitive access and for a rare asset.
- *Cost* small (code), large (study). *Risk* none. *Needs* code, and people for the study.

## (f) Threat model

**f1. Write the dynamic layer's adversary model.**

- *Change.* In section 3:
  - Classes A0 (non-adaptive misuse), A1 (masquerader with a stolen token), A2 (hijacked or
    injected agent in its user's session), A3 (traitor) and A4 (Sybil).
  - Knowledge levels K0-K3.
  - What the caller controls: pacing, origin, identities, session splitting, protocol revision,
    presence during the learning window.
  - Un-comment and extend the trust assumptions: the gateway sees all traffic and its log is intact;
    identities are verified by an org IdP; static artefacts are trusted; the gateway is observe-only,
    so it gives no oracle; which MCP revision is assumed; the shared upstream credential (f9).
  - A table of detectable, detectable-at-a-cost and undetectable-by-construction misuse.
  - Reconcile the intro's "needs no malicious agent" with "malicious intent" in scope.
  - Scope the 70.7% figure to non-adaptive misuse.

  Base it on 06's paste-ready text, after applying K1.
- *Why.* C8.
- *Cost* small. *Risk* none. *Needs* text.

**f2. Settle the lower bound.**

- *Change.* Either say that familiar behaviour is discounted to 0.7, or enforce M >= 1 for writes and
  for R_static >= 4. The second also removes the incentive to mimic.
- *Why.* C8: "bounded below by 1" (`main-restructured.tex:866-867`) is false for v4. Probe E13: a
  perfect mimic earns x0.89.
- *Cost* small. *Risk* low (it changes only sub-x1 calls, and never an alert). *Needs* text, or
  code and simulation.

**f3. Key baselines by user, not by client registration.**

- *Change.* Key Cadence and Footprint on (iss, sub), with client_id as a Footprint value of that
  user. A new client_id for a known user is then a Footprint event, not a fresh baseline. Start new
  identities from a role or org prior instead of M = 1. Make IdP trust policy (a CIMD domain
  allowlist, DCR rate limits) a stated assumption. First open RFC 9068, 8693 and 7662 to confirm
  which claims a gateway can rely on (K8), and document a fallback for unauthenticated routes.
- *Why.* N8: a fresh identity makes 2,400 writes at M = 1.00, and the simulator's "client switch"
  cannot happen in the gateway.
- *Cost* medium. *Risk* medium (baselines merge). *Needs* code and simulation.

**f4. Harden the org discount.**

- *Change.* Count only distinct established subjects (past onboarding), with a threshold relative to
  org size. Require an observable org event: a catalog digest change (already tracked) or an
  admin-declared migration. Never discount write, destructive or static >= 4 tools.
- *Why.* N9: three first-day identities drop a first sensitive touch from x4.51 to x1.00, and a
  shared prompt injection looks like an org change.
- *Cost* small to medium. *Risk* medium: org-change false alarms may rise, so measure on the days
  110, 130 and 150 events. *Needs* code and simulation.

**f5. Resist volume poisoning.**

- *Change.* Cap each value's contribution per day (log1p(count) or min(count, c)); count distinct
  days in the hour-of-day numerator. Use a time-bucketed robust "usual" (the median or 90th
  percentile of hourly counts over active hours). Hold back agent-days with M >= 3 from the
  baseline until reviewed or until a cooling period ends; this makes property 7's exact ablation
  approximate. Put gray traffic into the learning window in simulation.
- *Why.* N5: one 30-call night buys 50+ days of familiarity at 03:00. One 600-call hour turns a
  later 12x hour from x3.11 into x1.12. Counting days alone ("v2 + days") raised false alarms to
  52.9%, so evaluate intermediate caps.
- *Cost* medium. *Risk* high (false alarms may rise). *Needs* code and simulation.

**f6. Reform the habit discount.**

- *Change.* Discount only flag-days an operator dismissed (add a feedback field to the decision
  log), or only repeats of the same signature (read asset to write asset). Floor the discount (for
  example at 0.75). Never discount unsafe sequence when the asset read is more sensitive than the
  write target. Move graded flags out of "Red Flags", or redefine the group. Report cross-copy with
  and without the discount.
- *Why.* N6: cross-copy, the stand-in for the documented GitHub MCP toxic flow, goes from 6/6 to
  1/6 under the discount alone.
- *Cost* medium. *Risk* medium (false alarms from habitual copiers return). *Needs* code and
  simulation.

**f7. Widen the scope of sequence state.**

- *Change.* Keep sensitive reads per caller across sessions and routes, with 1-hour and 24-hour
  TTLs, in a gateway-level store. Give each tool an outbound-capable attribute from the static
  scan, and raise unsafe sequence on "sensitive read on route A, then outbound write on route B".
  Tie `requires_before` to the same asset or PR. Share origin baselines across a user's routes.
- *Why.* N16: a session split drops x3.62 to x0.94; one engine per route hides cross-server
  exfiltration.
- *Cost* medium. *Risk* medium. *Needs* code and simulation (split-copy scenarios).

**f8. Handle shared egress.**

- *Change.* Mark registered platform egress ranges (for example Anthropic's published MCP outbound
  range) as shared in the route config, and leave the network dimension out for them. Split the
  evaluation by hosting: local client, hosted connector, CI.
- *Why.* N28: all hosted-connector callers share one /16.
- *Cost* small. *Risk* low. *Needs* code and config, plus a simulator population of hosted agents.

**f9. Stop pooling privileges, or say so.**

- *Change.* Use per-user upstream credentials (per-user OAuth to the upstream, or RFC 8693 token
  exchange with an `act` claim). Otherwise, state in the threat model that the gateway is a
  privilege-pooling intermediary and that M is measured over pooled permissions. Put the gateway
  exchange id into upstream requests, so audit logs can be joined for validation.
- *Why.* N11.
- *Cost* large (code) or small (text). *Risk* high (code) or none (text). *Needs* code or text.

**f10. Map each dimension to a threat clause.**

- *Change.* Network, client and missing handshake are justified by credential theft, which section
  3 puts out of scope. Either add credential misuse to section 3 with its assumptions, or move those
  three to an "impersonation extension". Inject gray episodes into bot identities too.
- *Why.* N24.
- *Cost* small (text), medium (bot episodes). *Risk* none. *Needs* text and simulation.

**f11. Add adaptive gray kinds as a robustness section.**

- *Change.* Kinds: paced export, an aware thief (victim's hours, /16 and clientInfo, sends
  `initialize`), split copy, injected flow, fresh identity, Sybil discount, limit poisoning,
  condition then exploit, dormant return. For each, report the most calls, assets and bytes per day
  it gets through under x3, and the alerts it absorbs while conditioning. Keep this secondary to the
  ordinary-traffic evaluation, which leads with false alarms per the project's evaluation framing.
- *Why.* C8, N14, Arp P10. Every current gray kind is non-adaptive and carries giveaways the caller
  controls.
- *Cost* medium. *Risk* none (new results). *Needs* simulation.

**f12. Add privacy and ethics.**

- *Change.* A subsection on per-employee profiling. Pseudonymise /16 networks with a keyed hash. Tie
  log and state retention to the 90-day window. Restrict and audit access to profiles. Consider
  coarser hour bins.
- *Why.* N31. Top security venues expect an ethics discussion.
- *Cost* small. *Risk* none (text) or low (pseudonymisation). *Needs* text, optionally code.

## (g) Evaluation protocol

**g1. Fix the simulator before any new numbers.**

- *Change.*
  - Replace `hash()` at `normal_org_world.py:525` with a stable hash, and add a determinism test (the
    same digest across PYTHONHASHSEED values).
  - Commit `normal_org_world.py`, `normal_org_engines.py`, `normal_org_sim.py`, the v2-v4 engine and
    its tests.
  - Store the git SHA, config and policy digests and the seed in every result's meta, and refuse
    `--only` merges across versions.
  - Align the simulator with the gateway: no client on calls without `initialize`, write labels from
    `tool_impact`, no written `requires_before` unless learned, the same handling of non-call
    verdicts.
  - Apply a1.
  - Rerun the port check on all five worlds.
- *Why.* C2, K10, N15, N25.
- *Cost* small to medium. *Risk* medium: v4 numbers will move slightly once the oracle client is
  removed (one shadow script drops below x3). *Needs* code and simulation.

**g2. Freeze and preregister.**

- *Change.* Tag the frozen design (for example `dyn-v5-frozen`) with SHA-256 hashes of the engine,
  memory, policy and simulator files. Freeze every constant, including ALERT, the list budget and
  the limit-learning procedure. Preregister hypotheses, primary endpoints (benign agent-days at x3;
  gray catch rate per kind) and decision rules on OSF or Zenodo. Include one family of arms (c2,
  b4, c5, e3) with a Holm correction.
- *Why.* C2, C7, K6.
- *Cost* small. *Risk* none. *Needs* process.

**g3. Run held-out worlds.**

- *Change.*
  - Derive seeds after the freeze, excluding the burnt set {1, 2, 7, 11, 12, 21, 31, 41}.
  - At least 30 worlds per family.
  - Randomise the org-change days (now fixed at 110, 130 and 150) and the gray window.
  - Draw size and profile from preregistered ranges.
  - Use a longer horizon (N_DAYS >= window + 90) so the history window can be swept.
  - Add Slack or Calendar catalogs and an LLM-agent cadence profile fitted from MCP-Bench
    trajectories (K15).
  - Score the test pool once; any later change is a new version that needs fresh worlds.
- *Why.* C2 (critical), C7, N22.
- *Cost* medium to large (compute). *Risk* high for the headline numbers. *Needs* simulation.

**g4. Report honest metrics with uncertainty.**

- *Change.*
  - Count every benign agent-day (ordinary plus labelled change) in the false-alarm headline, with
    a per-tag breakdown.
  - Report precision at x3 and on the list, alerts per 1,000 agents per day, and precision against
    assumed prevalence (1e-2 to 1e-5 per agent-day).
  - Give Wilson or Clopper-Pearson intervals per kind and cluster-bootstrap intervals (agent within
    world, world as cluster).
  - Compare versions with paired tests: McNemar on episodes, paired bootstrap on agent-days.
  - Report alert concentration on the top 5% of agents.
  - Stratify by era, hosting, history length A, time zone and number of participating dimensions.
- *Why.* N3 (precision at x3 is 9.9-14.6%), N22, N4, C12.
- *Cost* small. *Risk* high for the headline framing. *Needs* simulation (analysis).

**g5. Run the sensitivity analysis.**

- *Change.*
  - Move `MAX_MULTIPLIER` and `MIN_MULTIPLIER` into `BehaviourConfig`, and make ALERT a parameter.
  - Log raw statistics so that ceilings, flags, floors, the scoring tolerance, the quantile and the
    alert line can be recomputed offline. The history window, onboarding, discounts and weekend
    pseudo-days need reruns.
  - State the analytic facts: s* = 0.5 + ln A / (2 ln B) = 0.8413; the (M, s2) list does not depend
    on 0.7 or 5; 0.7 never affects an alert; every flag or ceiling above s* alerts alone.
  - Then run one-at-a-time tornado plots, Morris screening, and a factorial on the 2-3 most
    influential factors, over the grids in C7's fix (for example ceilings {0.80, 0.84, 0.86, 0.90,
    0.95, 1.0} to cross s*).
  - Report the fraction of the parameter box in which each headline claim still holds.
- *Why.* C7; ACM SIGSOFT simulation standard; Arp P5.
- *Cost* medium. *Risk* none. *Needs* code and simulation.

**g6. Add outside baselines.**

- *Change.* Static only; red flags only; a per-agent z-score; Isolation Forest; an MCP
  Guardian-style fixed per-token rate limit; an AegisMCP-style global rarity; a Praetor-style
  per-deployment allowlist. All at the same false-alarm budget.
- *Why.* C2, Arp P6; 02 "Closest competitors". Today the only baselines are our own v1-v3.
- *Cost* medium. *Risk* none. *Needs* simulation.

**g7. Use independently built scenarios and a red team.**

- *Change.* At least 30 gray scenarios and 30 benign look-alikes, written by people who never saw the
  design doc or the engine, from a threat-model specification. A second person labels them blind
  (report Cohen's kappa). A white-box adaptive red team on top (f11).
- *Why.* C2 (Sommer & Paxson: ground truth independent of the detector).
- *Cost* large (people). *Risk* none. *Needs* people and simulation.

**g8. Climb the real-data ladder.**

- *Change.* In order:
  1. Oversized-request false alarms on real GH Archive body sizes per tool, with the 30-day learned
     limit. This is the cheapest real check, and it targets the main false-alarm source.
  2. CLUE-LDS (real Nextcloud logs, more than 5,000 users over 1,910 days; 8 dimensions direct and 5
     by proxy; ships hijack-injection code).
  3. The RBA login set, for network granularity (/16 against ASN against IP).
  4. flaws.cloud CloudTrail, for stolen-identity rarity.
  5. A shadow deployment of the observe-only gateway on organic traffic, with an operator reviewing
     sampled alerts.

  Check the GH Archive terms first (licence UNVERIFIED). Use LANL only with Larroche 2026's caveats.
- *Why.* C2; 03; 07 section 3.3. No public MCP dataset with per-caller histories exists.
- *Cost* medium (GH Archive) to large (shadow deployment). *Risk* none. *Needs* data and
  simulation.

**g9. Measure overhead and deployment behaviour.**

- *Change.* End-to-end p50, p99 and p99.9 added latency at the proxy, in inline mode, with snapshots
  on, with and without the behaviour layer. Memory per agent. Snapshot time against the number of
  agents. Move snapshots off the event loop (incremental per-day deltas). Shard state by caller key
  for replicas, and evaluate N = 2 and N = 4 by splitting each caller's stream. Measure detection
  recovery after a restart. Fenwick-tree tail sums, benchmarked at 10^5 assets.
- *Why.* N13, N23, N29, K15. Competitors report 60 µs to 4 ms per call. The existing `score_us`
  predates the layer.
- *Cost* medium. *Risk* low. *Needs* code and measurement.

**g10. Redraw the human-study cards from a held-out world.**

- *Change.* Draw the cards from a held-out world, not seed 7. Document the design, sample size and
  agreement (K16).
- *Why.* C2, 07.
- *Cost* small to medium. *Risk* none. *Needs* simulation and people.

**g11. Confirm the venue and the page budget.**

- *Change.* Confirm the target with the author. `paper_v5/README.md` says AAMAS 2027 (8 body pages,
  deadline "early October 2026 (TBC)", which has passed as of 2026-10-25); the brief says a
  security or SE A* venue. Open that venue's current CFP and artifact rules (07 uses USENIX
  Security '26, a past cycle). Decide which ladder levels and tables go in the body and which in an
  appendix.
- *Why.* K12.
- *Cost* small. *Risk* none. *Needs* a decision.

## (h) Wording fixes in the doc and the paper

These are recommendations; none of these files was changed by this workflow. Line numbers are as
of 2026-10-25.

**h1. Paper (`paper_v5/main-restructured.tex`).**

- :105 and :1358. Scope "invocation-specific arguments": "the behaviour multiplier reads no argument
  values; it uses the asset the static binding resolves and the request size". Describe the "3,000
  live invocations" as "a generator-sampled benign call mix against real servers, used for
  feasibility and latency" (C2, C12).
- :189-194 against :416-429. Reconcile "needs no malicious agent" with malicious intent in scope, and
  add f1's adversary paragraph (C8).
- :423-425 and :432. Un-comment the taxonomy and the trust assumptions, and extend them (C5, C8).
- :600-618. Version-scope the sessions table: "In MCP revisions up to 2025-11-25 a session starts
  with an initialize handshake; revision 2026-07-28 removes both (SEP-2575, SEP-2567)" (C1).
- :832-871. Replace L = D·A·N in [1, 8] with v4, M = g(s1) in [0.7, 5]. Replace :866-867 ("bounded
  below by 1 ...") with "familiar behaviour lowers the static risk by at most 30%, and unusual
  behaviour raises it up to five times", or with f2's M >= 1 rule (C8, N2).
- :891-892. "In inline mode the gateway scores a call before forwarding it; the evaluated gateway is
  observe-only and never blocks" (N23).
- :897-898. Replace "cannot be steered" with d1's qualified sentence (C5).
- :900-918. Describe the resolver that runs (d2), or wire it in.
- :922-928. Remove "session sizes" from the profile, or scope it to legacy traffic (C1).
- :953-958. One aggregator (c6).
- :972-976. Risk Output: "R_dynamic ranks calls by expected consequence; the daily review list ranks
  agent-days by (M, s2) under a fixed review budget; the alert line is M >= 3" (C6).
- :978-984. Bands for R in [0.7, 25] on the cube-root scale (e2).
- :1034-1037 and :1091-1092. Delete "invocation logs collected from the deployments" and "real MCP
  invocation traces". Say "simulated organisations: development worlds (optimistic) and held-out
  worlds" (C2).
- :1141-1142. Add a Dynamic Results section, or state "design and feasibility only" (C2, N2).
- Add a threats-to-validity paragraph (Arp P3, P5, P9, P10; Sommer & Paxson) and a privacy and
  ethics subsection (f12).

**h2. Paper notes (`paper_v5/DYNAMIC-LAYER-V4-NOTES.md`).**

- :18-19 and :205. d1 wording (C5).
- :21, :80, :111-114, :142, :276-277. Replace "one scale" with "one s-to-M map, with 0.5 = x1 for
  every dimension". Rename \paragraph{One scale.} to \paragraph{One shape.}. :237: drop "exactly".
  :246: "caps" becomes "scales" (C3, C10).
- :101. Replace "(the share of his past at least this rare)" with "(his past calls on v and on every
  value he used at most as often; N_d/n would be the share)" (C9).
- :130. Replace "Making the max a contribution" with "The max as a tested choice" (C4).
- :140. Replace "the alert line never moves" with "M stays bounded; each added dimension adds about
  its own ordinary false-alarm rate" (C4, N19).
- :141. Replace "soundness of gating on R_dynamic" with "monotone alerting on M; R monotone in M"
  (C6).
- :145-151 and :271-278. c1's Zimek wording (C11).
- :161-162. Version-scope the handshake, and replace `mcp2026spec` (C1).
- :182-184. Replace "the false-alarm drop is the trustworthy number" with "development-world
  results; the network change targeted v3's in-sample false alarms" (C2).

**h3. Design doc (`DIMENSION_FORMULAS.md`).**

- :14. Replace "ordinary calls stay at or below x1" with a measured statement (C3).
- :147 and :460. Replace "exactly" with "at 2·usual + u". :173/:182 and :801: add the kappa caveat.
  :395-397: split the rarity rows by kappa (kappa = 0.9: once a day 0.30/x0.87; every other day
  0.45/x0.97; once in 2.5 days 0.50/x1.00; once in 10 days 0.75/x2.24). :471: tool 0.50 becomes 0.45
  (C10).
- :335. Replace "it no longer takes part" with "it stays in the scores at 0.45 and can be s1 or s2"
  (N21).
- :349. Version-scope "must start with the initialize handshake" (C1).
- :489-537. Rewrite as in c1. :511-512 (property 5) holds only after b6 (N7).
- :542. Replace "smooth, no cliffs" with "continuous, with a kink at s = 0.5 (slope 0.71 below, 3.22
  above)" (N21).
- :619. Replace "5-call warm-up removed" with "warm-up: at least 5 tool calls and past the first UTC
  day" (N21).
- :629-631. Report the realised raise rates of learned limits (b5).
- :659-668. State k per organisation, and use top 4 throughout (N4).
- :687. Label the network-driven drop as in-sample (C2).
- :823-824. C9's wording: "the tail set of a plug-in conformal p-value; e = p x (n+1)/(A+1), a
  per-day rate, not a probability; s = c/(1+2e) is a heuristic grading of it".
- :827-830. Split "checked by simulation" three ways (C7).
- :851-854. The combiner arm is offline once per-call vectors are logged (c3).
- :868 (Open decision 3). The decision record does carry the asset (d6). :871 (Open decision 4):
  response-side signals (d9).
- New sections: "Step 0: asset identity" (d2), "Outputs and their objectives" (e1), "Threat model"
  (f1), "Protocol era" (a2, a3).

**h4. Code docstrings and docs.**

- `framework.py:14-15` and `engine.py:152`: d1 wording.
- `binding/__init__.py:11-12`: remove "cannot be moved by anything an attacker writes into an
  argument".
- `policy.py:15-16`: correct the statement about learning sweep from logs (d6).
- `docs/project/gateway-architecture.md`: the spec says clientInfo SHOULD NOT drive security
  decisions; it is not a "must not" (01).
- Per the docs-sync rule, update `docs/` and `CLAUDE.md` when any code option changes commands or
  architecture.

**h5. Bibliography (`paper_v5/refs.bib`).**

- Replace `mcp2026spec` (unversioned, accessed 2026-07-30) with versioned entries for 2025-06-18,
  2025-11-25 and 2026-07-28, plus SEP-2567 and SEP-2575 (K9).
- Add the sources the fixes cite:
  - Zimek et al. 2014 (doi:10.1145/2594473.2594476);
  - Aggarwal & Sathe 2015 (doi:10.1145/2830544.2830549);
  - Kriegel et al. 2011 (doi:10.1137/1.9781611972818.2);
  - Birnbaum 1954 (doi:10.1080/01621459.1954.10483521);
  - Heard & Rubin-Delanchy 2018 (doi:10.1093/biomet/asx076);
  - Bates et al. 2023 (doi:10.1214/22-AOS2244);
  - Arp et al. 2022;
  - Sommer & Paxson 2010;
  - Wagner & Soto 2002 (doi:10.1145/586110.586145);
  - Kloft & Laskov 2012;
  - Axelsson 2000 (doi:10.1145/357830.357849).
- Fix what 02 found: the duplicate keys `betser2026agentrim`, `owireduashley2026severity` and
  `zhang2026stars`; Parasites under two keys; the MiniScope retitle; the AgenTRIM author order; the
  missing author in `rahman2026rolestratified`; `fu2025riskcue` filed under MCP risk scoring
  although it is server-to-agent.
- Do not cite Anderson 1980 for a masquerader taxonomy, or the "fuzzy-logic disjunction", until each
  is verified (README ledger).

**h6. Knowledge-base notes (K1-K16).**

- 02 and 06: d1 wording; add evasion row 8b and mitigation M10 to 06 (K1).
- 02: Implication 4 (session notion) and Implication 8 (the lifecycle citation) (K7); novelty claim 2
  after e3 (K2).
- 03 :111 and section 6.9, and 07 :408 and section 3.4: e = lambda_hat x p, not a p-value (K5). 04
  :24 and :66: rename the "calibrated" heading (C9).
- 04 section 2.3: rest on multiview plus normalisation (K4).
- 07 sections 3.1, 3.4 and 3.6: the pre-freeze list (g1) and one arm family (K6, K10). 07 section 9:
  the venue (K12).
- 01: date the session-authentication rule to 2025-06-18 and record the observed redirects (K9).
- 03: the warm-up sentence, the CLUE count, a FragBench row (K13).
- 06 E8: label it a toy set and rerun it on the main world (K11). Copy the probe scripts into
  `knowledge_base/probes/` with a README.

## Recommended sequence

The order puts the cheapest removal of reject points first, keeps v4 runnable throughout, and
produces no headline number before the design is frozen.

1. **Decide scope (a day).** g11: confirm the venue and page budget. Then decide whether the dynamic
   layer goes in with efficacy numbers or as design plus feasibility. If the deadline does not allow
   steps 5-6, take the second path. That lowers C2 from critical to high.
2. **Text only (2-4 days, no behaviour risk).** h1-h6, f1, f2 (wording), f10, f12, e1, d1, d2 (text),
   b1, c1, c6, and a threats-to-validity paragraph. This alone answers C5, C6, C8, C9, C10 and C11 as
   wording, fixes C12's framing, and removes N2's contradictions in the text.
3. **Small code that does not change v4 alerts on legacy traffic (a few days).** a1 (the one
   deliberate behaviour fix), a2, c3 and e6 (log per-call score vectors, era, basis and s2), b2,
   d7, g1 (determinism, commits, provenance, sim-gateway alignment), the constants into config
   (g5's prerequisite), d6 and a7.
4. **Design changes as a selectable v5, in order of evidence strength.**
   1. d3 and d4 (asset identity; critical N1).
   2. f3 and f4 (identity key and org discount).
   3. b6 (monotonicity).
   4. f5 and f6 (poisoning, habit discount).
   5. b5 (learned limits; the main false-alarm source).
   6. f7 and a3 (sequence scope, spells).
   7. b9 (small and stale histories).
   8. a4, a5 and a9 (modern-era signals, session robustness).
   9. d5, d9 and a6 (tool granularity, responses, resources).
   10. b10 and f8 (time zones, shared egress).

   Each goes behind `BehaviourConfig.design`, with v4 kept as it is.
5. **Development-world experiments, on burnt seeds only.**
   - b3, the benign table per dimension.
   - c2 with b4 and c5, the matched-budget combiner family.
   - e3 and e4, the review keys and the corrected list metric.
   - d8, resolver in the loop.
   - a8, modern and mixed era.
   - f11, adaptive kinds, as a secondary section.

   Choose the v5 configuration by a rule written down before the runs.
6. **Freeze and held-out evaluation.** g2, then g3, g4, g5 and g6. Then g10.
7. **External validity, as time allows.** g8 (the GH Archive oversized-request check first), g9, g7,
   then the shadow deployment.

Things not to do:

- Do not rebut C1.
- Do not claim calibration for the current scores.
- Do not present 59.0% to 57.8% as either a loss or a gain.
- Do not report any number from seeds {1, 2, 7, 11, 12, 21, 31, 41} as a test result.

## References

- [review-assessment.md](review-assessment.md): verdicts C1-C12, issues N1-N31, gaps K1-K16, and the
  primary sources with who opened them.
- [README.md](README.md): index, contradictions resolved, per-dimension status, UNVERIFIED ledger.
- Notes: [01](01-mcp-protocol.md), [02](02-mcp-runtime-security-literature.md),
  [03](03-ueba-insider-threat-and-datasets.md), [04](04-score-aggregation-and-calibration.md),
  [05](05-system-map.md), [06](06-threat-model-and-evasion.md),
  [07](07-evaluation-methodology.md).
- Design: [DIMENSION_FORMULAS.md](../DIMENSION_FORMULAS.md). Paper:
  [main-restructured.tex](../../../../paper_v5/main-restructured.tex),
  [DYNAMIC-LAYER-V4-NOTES.md](../../../../paper_v5/DYNAMIC-LAYER-V4-NOTES.md).
