# Review Assessment of the Dynamic Layer

This file rules on each claim in the external review of the dynamic layer (design v4, the
behaviour multiplier M in [0.7, 5] with R = R_static x M). It then lists the issues the review
missed and the gaps that remain in this knowledge base. Each claim was checked by two independent
checkers and then by a judge who re-opened the decisive sources; this file passes on their
verdicts and says plainly where the reviewer is right, where the reviewer overstates, and where
the reviewer understates.

## How to read this

- **Verdict**: true, partly true, false or unverifiable. **Confidence**: high, medium or low.
- **Severity** is the risk at an A* security or SE venue: critical (likely reject on its own),
  high (a likely reject point if left), medium (a clear weakness), low (wording).
- **Provenance**: "judge opened" means the judge re-opened the primary source on 2026-10-25.
  "Checker" means only a checker opened it. Code facts give file:line. A few code lines were also
  re-read by the author of this file (listed in [README.md](README.md)).
- The review text itself is not in the repository. Each claim below is paraphrased from the
  checkers' and judges' records.
- IDs: C1-C12 are reviewer claims, N1-N31 are issues the review missed, K1-K16 are
  knowledge-base gaps. Lower-case IDs (a1, b4, ...) are options in
  [improvement-options.md](improvement-options.md), which refers back to these IDs.

## Summary

| ID | Claim (paraphrased) | Verdict | Confidence | Severity |
|----|---------------------|---------|------------|----------|
| C1 | MCP 2026-07-28 removes `initialize` and sessions, so the session-based dimensions only work on legacy traffic | true | high | high |
| C2 | The layer is evaluated only on synthetic worlds that were also used to design it | true | high | critical |
| C3 | The "one shared scale" is not a calibration; scores are not comparable in benign tail rate | true | high | high |
| C4 | The max combiner is argued, not tested against an objective or against alternatives at equal budget | true | high | high |
| C5 | "Computed without reading arguments" is overstated; asset identity and resolution are unspecified | true | high | high |
| C6 | R = R_static x M and the (M, s2) review list serve different objectives, and this is not stated | true | high | high |
| C7 | The hand-set constants have no sensitivity analysis | true | high | high |
| C8 | There is no adversary model for the dynamic layer, and no definition of detectable misuse | true | high | high |
| C9 | Calling the rarity score an "empirical p-value" is wrong; it is a heuristic, not a calibration | true | high | low |
| C10 | The 0.9 ceiling moves the neutral point of tool, network and client to e = 0.4 | true | high | low |
| C11 | Zimek et al. 2014 warn that the max lets one noisy detector decide; citing them in support is misleading | true | high | medium |
| C12 | v4 cuts false alarms but lowers list catches slightly and misses over-fetching entirely; the draft suggests more | partly true | high | medium |

## Where the reviewer is right, and where not

The reviewer is right on eleven of twelve claims, and the twelfth is partly right. On five claims
the reviewer understates the problem:

- **C1**: the protocol change is not just a silent no-op. A bug (`engine.py:574`) makes the
  `requires_before` rule fire on every sessionless call (M = 3.62 on an ordinary merge), and the
  habit discount then trains it off for good.
- **C3**: per-dimension benign exceedance at 0.5 spans about 7,000x. A learned limit misses its
  own 0.5% target by a factor of 2.4-4.4.
- **C5**: free-text arguments can steer the asset (sensitivity 5 to 4). On the live route the
  worst-case driver is written into the behaviour history (N1).
- **C7**: the list leaves out the x3 alert line, which together with the upper bound 5 sets the one
  threshold s* = 0.8413. The 0.9 constants sit just above it.
- **C11**: Zimek et al. take a side. They write that the average "does seem to make more sense".

The reviewer overstates in five places:

- **C1**: the core of the layer, per-principal rarity, rate, breadth and the first-access floor,
  survives the protocol change. Legacy traffic is still live: dual-era servers are allowed, no
  end date is set, and all captured traffic is 2025-11-25.
- **C5**: the engine-level statement is narrowly true. Resolution is deterministic and model-free,
  and unresolved calls err high on R_static.
- **C7**: the review list is invariant to the bounds 0.7 and 5, and 0.7 never affects an alert.
- **C10**: the real split is not rarity against excess. It is kappa = 0.9 dimensions and small-mu
  excess scores against the rest. No result changes.
- **C12**: the paper draft reports no v4 results at all, so it cannot overclaim them. The list
  "loss" is noise and its sign depends on the list size.

What holds up, and is worth saying in a rebuttal:

- The baselines are per principal.
- M feeds nothing back into state, so ablations are cheap once per-call scores are logged.
- The temporal split inside each world (learn 30 days, evaluate from day 90) is sound.
- The observe-only gateway gives an adaptive caller no oracle to probe.
- The first-access floor flags first touches of sensitivity 4-5 assets, even by fresh identities.
- The rarity score is close to a conformal p-value.
- Several choices match commercial UEBA: new-thing pricing (Sentinel), first-access points
  (Exabeam), learning repeats (GuardDuty).
- No public MCP dataset with per-caller histories exists (02, 03), so the synthetic-first approach
  is defensible as a development stage, though not as the final evidence.

## C1: MCP revision 2026-07-28 and the session-based dimensions

**Claim.** The current MCP revision removes the `initialize` handshake and protocol sessions, so
missing handshake, session duration and the session-scoped checks only work on legacy traffic.

**Verdict.** True, high confidence. **Severity: high.**

**Decisive evidence.**

- The 2026-07-28 changelog (judge opened) lists as major changes "Remove protocol-level sessions
  and the Mcp-Session-Id header" (SEP-2567) and "Make MCP stateless: remove the
  initialize/notifications/initialized handshake" (SEP-2575). The versioning page (judge opened)
  says "There is no negotiation handshake" and defines Legacy as 2025-11-25 and earlier.
  `initialize` is removed, not deprecated (01 section 2).
- The impact is limited, not refuted. A server "MAY implement both behaviors", no end date for
  legacy revisions exists, and `runs/gateway/live/github.jsonl` has 346 matches for 2025-11-25
  and 0 for 2026-07-28. Even under legacy rules, a session id was optional ("MAY assign") and
  stdio never had one.
- Code: `engine.py:483` fires missing handshake only with a session. `engine.py:379,403-404`
  score session duration only with a session. `proxy.py:433` takes the session only from the
  header. Under modern traffic these never take part, and nothing reports that.
- Bug beyond the claim: `engine.py:574` reads
  `if needed and not (session and session.tools & needed): return True`. With no session this is
  True. A route with a hand-written `requires_before` (kept by `policy.py:107`), or a policy learned
  on legacy traffic, flags every ordinary merge: M = 3.62 on day 0, then about 0.90 once the habit
  discount builds. At that point a real unreviewed merge is invisible: a false alarm followed by a
  blind spot.
- The citation contradicts its source. `DYNAMIC-LAYER-V4-NOTES.md:161-162` cites `mcp2026spec`
  (an unversioned URL, accessed 2026-07-30) for "Every MCP session starts with an initialize
  handshake". On that date the URL led to the revision that removed it.
  `main-restructured.tex:600-618, 922-928` and `DIMENSION_FORMULAS.md:349` also assume sessions.
- SEP-2567 (checker opened) reports that session lifetime is set by the host app: "ChatGPT creates
  a fresh session for every individual tool call". So session duration partly measures the
  client, not the agent.

**Fix.**

- Make the layer era-aware; do not rebut the claim.
- Scope missing handshake and session duration to legacy Streamable HTTP with server-minted
  session ids.
- Cite versioned spec pages and SEP-2575/2567.
- Fix `engine.py:574`: a missing session means "not evaluable".
- Move sequence and duration checks to a per-principal "spell" (calls separated by an idle gap)
  and key all state by the verified principal.
- Add modern-era signals: a conformance flag, an era-downgrade flag, and protocol version plus a
  capabilities fingerprint as Footprint values.
- Simulate modern-era and mixed-era worlds and report results per era. See improvement options
  a1-a9.

**Sources.** [01](01-mcp-protocol.md) sections 2 and 4;
modelcontextprotocol.io/specification/2026-07-28/changelog and .../basic/versioning (judge
opened); modelcontextprotocol.io/seps/2567-sessionless-mcp and 2575-stateless-mcp (checkers);
`engine.py:379,403-404,483,570-579`; `policy.py:97-110`; `proxy.py:433`; `refs.bib:20-26`.

## C2: Evaluation only on the design worlds

**Claim.** The dynamic layer is evaluated only on synthetic worlds that were also used to design
and tune it. There is no held-out or real data.

**Verdict.** True, high confidence. **Severity: critical.**

**Decisive evidence.**

- The project concedes it. `DIMENSION_FORMULAS_v3.md:631-635` says "v3's new detectors were
  designed after seeing what v2 missed, so their catch rates are optimistic".
  `DIMENSION_FORMULAS.md:4,650` say v4 was checked on the same five organisations.
- No world is held out. The seeds are 7, 11, 21, 31 and 41, exactly the worlds on which v1-v4
  were compared. 37 engine variants were scored on seed 7 (07 section 1.1). In v3, slow-loop
  detection went from 9% to 100% after detectors were written for v2's misses. This is test
  snooping (Arp et al. P3).
- The constants were tuned on the same worlds (`DIMENSION_FORMULAS.md:827-830`; Open decision 5).
  This is biased parameter selection (Arp P5).
- The "trustworthy" false-alarm drop is also in-sample: v4's network change targeted v3's own
  false alarms (`DIMENSION_FORMULAS.md:687`).
- Org changes fall on fixed days 110, 130 and 150 in every world (`normal_org_world.py:37`).
- The worlds are not reproducible. A salted `hash()` at `normal_org_world.py:525` gives different
  digests under PYTHONHASHSEED 1 and 2 (judge re-ran). The three simulator files are untracked in
  git.
- The paper misstates its data. `main-restructured.tex:1034-1037` says "invocation logs collected
  from the deployments", and :1091-1092 says "real MCP invocation traces". Yet :1141 reports only
  the static scanner. The "3,000 live invocations" (:105, :1358) are a generator-sampled benign
  mix, and the real_benign CSVs have no timestamps and 1-5 callers (N2).
- Arp et al. 2022 and Sommer & Paxson 2010 (judge opened) define these pitfalls and ask for
  ground truth "orthogonal (unrelated) to how the detector works".

**Fix.**

- Now, in the text: delete the real-trace claims; describe the 3,000 calls as feasibility only;
  label seeds 7-41 as development worlds; add a threats-to-validity paragraph (Arp P3/P5/P9,
  Sommer & Paxson).
- Then make the design reproducible and freeze it: stable hash, commit the files, tag, freeze the
  constants.
- Preregister the hypotheses and endpoints.
- Run at least 30 held-out worlds per family with randomised change days.
- Add independently authored scenarios and an adaptive red team.
- Run a shadow deployment.
- If this cannot be done before submission, present the dynamic layer as design plus feasibility
  with no efficacy numbers. That lowers the severity to high. See options g1-g11.

**Sources.** [07](07-evaluation-methodology.md) sections 1-3;
usenix.org/system/files/sec22-arp.pdf and oaklandsok.github.io/papers/sommer2010.pdf (judge
opened); the files above.

## C3: The shared scale is not a calibration

**Claim.** The design calls the max well-founded because the scores share one scale, but the
scores are not calibrated to comparable benign tail rates.

**Verdict.** True, high confidence. **Severity: high.**

**Decisive evidence.**

- The claim is made as a design property. `DIMENSION_FORMULAS.md:513-516` (property 6) says the
  max is "well-founded because the scores share one scale". Property 4 (:510) says a dimension can
  be added "without recalibrating the others or the alert line". The paste-ready LaTeX repeats this
  (`DYNAMIC-LAYER-V4-NOTES.md:21,113,142,229,276-277`).
- The comparability is by construction. There is one tolerance (2.0); the ceilings differ (0.9);
  the flags are constants off the curve (0.9, 0.7) (`engine.py:117-123`).
- Measured on 7,086 ordinary agent-days (main organisation; judge opened checker 1's log): the
  share of days on which a dimension's daily max reaches 0.5 runs from 74.4% (repetition) to 0.01%
  (client, sweep), about 7,000x. At the x3 line, oversized request is at 1.92% and every excess
  dimension at 0.04% or less. Hour of day has a daily-max q99 of 0.094.
- `policy.py:53` promises that a learned flag fires on at most 0.5% of ordinary agent-days, yet
  oversized request fires on 1.92%. It causes 71% of x3 false alarms
  (`DIMENSION_FORMULAS.md:733-744`).
- The cited sources assume normalised inputs: Zimek et al. ("relies heavily on the scores ...
  being comparable"), Aggarwal & Sathe (Z-score normalisation before combining), and Kriegel et al.
  2011 (typical inlier values are not comparable) (judge opened all three).
- In the design's favour: M is checked on benign data overall (2.5-2.8% of ordinary agent-days at
  x3), three flag limits are learned from benign quantiles, and 0.5 has a real meaning in units.
  The scores are commensurate in unit, not in false-alarm rate.

**Fix.**

- Reword property 6 to "one shape and one s-to-M map, not one false-alarm rate". Drop "without
  recalibrating" from property 4.
- Log per-dimension daily maxima and publish a benign table per dimension.
- Test a calibrated max (per-dimension conformal p-values, weighted Bonferroni) as an ablation
  arm.
- Fix the oversized-request multiplicity.
- Either price red flags by their measured benign rate, or declare them policy overrides outside
  the scale. See options b1-b5 and b8.

**Sources.** [04](04-score-aggregation-and-calibration.md) sections 1-3 and 6; `engine.py:110-126`;
`policy.py:53`; `normal_org_sim.py:415-449`; doi:10.1145/2594473.2594476;
doi:10.1145/2830544.2830549; doi:10.1137/1.9781611972818.2.

## C4: The max is argued, not tested

**Claim.** The max combiner is presented as principled without a stated objective or a
comparison with alternatives at an equal false-alarm budget.

**Verdict.** True, high confidence. **Severity: high.**

**Decisive evidence.**

- `DIMENSION_FORMULAS.md:489,499` say "max as a design property" and "not a shortcut: it is what
  makes the rest of the design work". The notes say "Making the max a contribution" (:130). No
  objective, cost ratio or false-alarm target is stated.
- Qualification: the working doc lists the drawbacks (:527-537) and plans the ablation (:844).
- The toy table (:491-497) runs the average through the max's own alert line. The only tested
  alternative ("v3 + tie-break formula") was rejected at unequal false-alarm rates (6.2% against
  7.0%).
- The equal-budget result exists but is not cited. On the fixed daily list, the max ordered by s2
  catches 53.2% at top 4 and 65.8% at top 8, against 54.4% and 63.3% for soft-OR (one
  organisation, v3, about 79 episodes). This is a tie: the max costs nothing in detection, but it
  is not superior.
- `DIMENSION_FORMULAS.md:851-854` wrongly says the combiner arm needs a rerun. M feeds nothing back
  into state (`engine.py:297-299, 504-515`).
- Theory (judge opened): Birnbaum 1954 says no combination method is optimal in general. Heard &
  Rubin-Delanchy 2018 show that Tippett's min-p is optimal only for sparse alternatives and is
  "very difficult to justify in practice".
- Properties 3 and 4 fail against the design's own data. Under a max, the alarm set is a union, so
  the false-alarm rate can only stay level or rise as dimensions are added.
- The paper has three aggregators: the product L = D·A·N (~:848), the "most severe proposal"
  (~:955), and the max (notes only). `aggarwal2015outlier` and `zimek2014ensembles` are not in
  `refs.bib`.

**Fix.**

- Keep the max, but as a tested choice. State a Neyman-Pearson objective: maximise gray recall
  subject to ordinary false alarms <= alpha, with alpha in {1, 2.5, 5}%, and use the fixed list as
  the second operating point.
- Run a matched-budget combiner ablation with a preregistered non-inferiority rule.
- Reframe the max as the sparse-misuse (multiview) choice.
- Use one aggregator across the paper. See options c1-c6.

**Sources.** [04](04-score-aggregation-and-calibration.md) section 4;
[07](07-evaluation-methodology.md) section 3.4; kdd.org/exploration_files/V15-01-02-Zimek.pdf
(judge opened); doi:10.1080/01621459.1954.10483521 (abstract, judge opened); arXiv 1707.06897,
doi:10.1093/biomet/asx076 (judge opened); `results/normal_org_sim.md` lines 27 and 33.

## C5: "Without reading arguments" and asset identity

**Claim.** The statement that M is computed without reading the call's arguments is overstated,
and the design never says how the asset is identified.

**Verdict.** True, high confidence. **Severity: high.**

**Decisive evidence.**

- Narrowly true: the engine's `Message` (`engine.py:150-163`) has no arguments field.
- False at system level. `RouteScorer.score` (`framework.py:181-191`) calls `MatrixScorer.score`,
  which for multi-candidate tools walks every string argument at any depth, free text included,
  and matches it against register ids (`binding/scoring.py:89-166`). The engine receives
  `asset=cell.driver` (re-read: `framework.py:188-189`). Size is the byte length of the whole
  message (`wire_log.py:275,430`).
- Coverage on `github_remote.cells.json`: 49 tools. 11 have no cells (asset None), 3 have a sole
  candidate, and 35 need argument matching.
- Steering (judge probe): `get_file_contents(repo='website', path='README.md')` resolves to
  helios-scada-gateway (sensitivity 5, cell 75). With `path='docs/helios-public-site.md'` it
  resolves to repository-contents (sensitivity 4, cell 48). This contradicts
  `main-restructured.tex:897-898` and `binding/__init__.py:11-12` ("cannot be steered").
- Facets as identity: after 20 days on one public repository, `list_issues`, `search_code` and
  `push_files` on the same repository resolve to three facets and each scores M = 3.779 (false
  first-access floors).
- Collapse: 30 unregistered repositories all resolve to one driver, so breadth sees 1 asset and
  sweep cannot fire. A later real read of that driver gets no first-access floor.
- The paper describes a resolver (Discovery/AssetResolver, `main-restructured.tex:900-918`) that
  the live gateway does not run (`framework.py:127`).
- The v4 simulation uses oracle repository names (`normal_org_world.py:394-395`), so its results
  assume perfect resolution.
- Severity is high, not critical: the layer does not need a redesign. It becomes critical if a
  resolver-in-the-loop run moves the v4 numbers materially, and N1 suggests it will.

**Fix.**

- Reword to "M receives no argument values; it consumes the asset resolved by the static side's
  deterministic binding, plus the request size". Delete "cannot be steered".
- Specify asset identity as Step 0.
- Split the two roles of the asset: a container handle for behaviour, the worst-case driver for
  R_static.
- Restrict matching to identifier-typed inputs.
- Learn the sweep limit from the decision log.
- Add regression tests and a resolver-in-the-loop arm. See options d1-d9.

**Sources.** [05](05-system-map.md) section 2; `framework.py:1-24,127,165-217`;
`binding/scoring.py:89-166`; `engine.py:150-163,418-445,490-501`; `policy.py:155-188`;
`normal_org_world.py:388-398`; judge probe in the session scratchpad (`judge_c5/judge_probe.py`).

## C6: Two outputs, two objectives

**Claim.** The per-call risk R = R_static x M and the daily review list ranked by (M, s2) serve
different objectives. The review list is behavioural triage that ignores R_static, and the design
does not say so.

**Verdict.** True, high confidence. **Severity: high.**

**Decisive evidence.**

- The review key leaves out R_static (`DIMENSION_FORMULAS.md:450-455`), and the alert line is on M
  (:566-568). No threshold on R exists. Yet the notes claim "soundness of gating on R_dynamic"
  (:141), and the paper says R_dynamic feeds review and access control
  (`main-restructured.tex:972-976`).
- Not purely behavioural: the first-access floor puts sensitivity into M on purpose (:441,
  :566-568).
- An R-based key was tested and loses in all five organisations. At top 4: main 58.2% against
  36.7%, seed 11 47.6 against 32.8, heavy files 54.4 against 39.1, small 71.4 against 67.1, and at
  top 8 large 57.4 against 41.2.
- That does not show R is wrong. The gray label has no harm weight; the simulator's static score is
  a per-tool level in {2, 3, 4} that ignores the asset; and the agent-day R can come from a
  different call than the max-M representative.
- There are three R scales: the paper (1-125 bands, L in [1, 8]), the gateway (`risk` = cell x
  factor, and `dynamic_risk` = cell^(1/3) x M, re-read `framework.py:194-206`), and the simulator.
  Nothing ranks, alerts or gates on either gateway number.
- s2 mainly cuts ties at the cut (35.2% to 2.2% of the cut in a tie, main top 4). It does not
  raise catches.
- CVSS v4.0 (judge opened) separates intrinsic severity from contextual enrichment.

**Fix.**

- Name three outputs with their own objectives: per-call R (consequence ordering or gating), the
  daily list (most gray episodes per analyst budget), and the alert at M >= 3.
- Report the static x M arm with its caveats.
- Make the simulator's static score per (tool, asset), weight gray episodes by harm, and compare
  review keys.
- Use one R_static scale everywhere, and retire or rename the legacy `risk` field. See options e1-e7.

**Sources.** [05](05-system-map.md) section 6; `DIMENSION_FORMULAS.md:17,420-421,441,450-455,
552-568,845`; `framework.py:185-206,296-298`; `normal_org_sim.py:425-452,540-562`;
`results/normal_org_*.md` "v4 | top k" rows; first.org/cvss/v4.0/specification-document (judge
opened).

## C7: No sensitivity analysis

**Claim.** The tolerance, ceilings, flag values, floors, bounds, windows and discounts were set by
hand and never swept.

**Verdict.** True, high confidence. **Severity: high.**

**Decisive evidence.**

- No sweep exists. The 37 simulator variants are structural switches, and grep finds no override
  of any constant. `DIMENSION_FORMULAS.md:544` says "5 and 0.7 are chosen by design", and :836 says
  the ablation is "Not done yet".
- The doc overstates what was done: :827 says "checked by simulation" for constants tried once at
  most, mostly on v2/v3 engines.
- `MAX_MULTIPLIER` and `MIN_MULTIPLIER` are module constants, not config fields (re-read
  `engine.py:74-75`).
- The review leaves out the alert line (`ALERT = 3.0`, `normal_org_sim.py:70`). With the upper bound
  it sets s* = 0.5 + ln 3 / (2 ln 5) = 0.8413. The flag value 0.9 and the ceilings 0.9 sit 0.06
  above it, and the sensitivity-4 floor (0.8) can never alert alone. Small moves flip whole
  categories.
- Oversized request plus tool explain 81-94% of ordinary x3 agent-days across the five
  organisations. Oversized request alone exceeds its nominal 0.5% budget by 2.4-4.4x.
- The 90-day window cannot be swept upward: worlds are 180 days long and evaluation starts at day
  90.
- Overstated part: the list ranks by (round(M, 9), s2). M is strictly monotone in s1, so list
  metrics do not depend on 0.7 or 5, and 0.7 never touches an alert.
- Venue norm (judge opened): the ACM SIGSOFT Quantitative Simulation standard lists sensitivity
  analysis as Desirable and calibration description as Essential. Arp P5.

**Fix.**

- Split the "checked by simulation" list into definitional constants, constants set by hand and
  never swept, and constants tried once.
- Move the bounds into `BehaviourConfig`, and make ALERT a parameter.
- Log raw statistics so that most constants can be recomputed offline.
- State the analytic invariances.
- Run one-at-a-time tornado plots, a Morris screening and a small factorial on held-out worlds.
- Report the realised raise rate of each learned flag. See option g5.

**Sources.** [07](07-evaluation-methodology.md) section 3.5; `engine.py:74-78,111-143,184-188`;
`policy.py:23-25,53-56`; `normal_org_sim.py:68-70,145-218,545-550`;
raw.githubusercontent.com/acmsigsoft/EmpiricalStandards/master/docs/standards/QuantitativeSimulation.md
(judge opened); usenix.org/conference/usenixsecurity22/presentation/arp (judge opened).

## C8: No adversary model

**Claim.** The paper does not say what an adversary of the dynamic layer knows or controls, or
which misuse is detectable.

**Verdict.** True, high confidence. **Severity: high.**

**Decisive evidence.**

- Section 3 (`main-restructured.tex:416-429`) scopes misuse "regardless of whether the operation
  originates from benign error ... or malicious intent". It never says what an adversary knows or
  controls.
- The misuse taxonomy and the trust assumptions are commented out (:423-425, :432).
- The uncommented text has no "adversar", "evasi", "mimicr" or "sybil", and "attacker" appears
  once.
- The intro says misuse "needs no malicious agent" (:189-194), but section 3 puts malicious intent
  in scope.
- `main-restructured.tex:866-867` says the factors are "bounded below by 1, familiar behavior does
  not reduce the static risk" (re-read). v4 has M down to 0.7, so it rewards a caller who imitates
  its own history.
- `Message` has no argument content and no response size, so harm in content and over-fetching are
  undetectable by construction. This is not stated.
- All 10 gray kinds are non-adaptive (`normal_org_world.py:196-207`), so the 70.7% catch at x3
  holds only for oblivious misuse.
- Probes (06, checker 2): a fresh identity makes 2,400 writes at M = 1.00; a session split takes
  x3.62 to x0.95; a perfect mimic scores x0.89.
- Helps the paper: the gateway is observe-only (`proxy.py:1-16`), so it offers no probing oracle.
- The material for the fix already exists in 06.
- Primary sources (judge opened): Arp et al. arXiv 2010.09470; Wagner & Soto CCS 2002,
  doi:10.1145/586110.586145; Kloft & Laskov JMLR 13:3681-3724, 2012.

**Fix.**

- Add an "Adversary of the dynamic layer" paragraph: classes A0-A4, knowledge K0-K3, and
  capabilities.
- Un-comment and extend the trust assumptions: the gateway sees all traffic, verified identities,
  trusted static artefacts, observe-only, which MCP revision, and the shared upstream credential
  (N11).
- Add a table of detectable, detectable-at-a-cost and undetectable-by-construction misuse.
- Either scope the claim to "flags non-adaptive misuse and raises the cost of adaptive misuse",
  or run adaptive gray kinds.
- Fix the "bounded below by 1" sentence, or adopt M >= 1 for writes and R_static >= 4.
- Harden the cheapest evasions. See options f1-f12.

**Sources.** [06](06-threat-model-and-evasion.md); `main-restructured.tex:185-196,416-432,860-870,
1088-1100`; `engine.py:74-75,151-164,281-290`; `proxy.py:1-16`; arxiv.org/abs/2010.09470;
dl.acm.org/doi/10.1145/586110.586145; jmlr.org/papers/v13/kloft12b.html (all judge opened).

## C9: The "empirical p-value" label

**Claim.** "This thing + everything rarer" is called an empirical p-value, but the implemented
quantity is a heuristic per-day rate and must not be described as calibration.

**Verdict.** True, high confidence. **Severity: low.**

**Decisive evidence.**

- `DIMENSION_FORMULAS.md:823-824` uses the label.
- `memory.py:102` returns `(rare + 1) / (active_days + 1)`, a count per active day. The doc rejects
  the plain share at :271-275, and its own example has e = 12.8.
- Exactly, e = p_split x lambda_hat. Here p_split = (N+1)/(n+1) has the form of the marginal
  conformal p-value in Bates et al. 2023 (eq. 3; abstract judge opened, Ann. Statist.
  51(1):149-178, doi:10.1214/22-AOS2244), and lambda_hat is his calls per active day. It is only a
  plug-in, because the scores are fitted on the same history.
- The never-used branch (`memory.py:97-99`), hour of day (a local count) and the overrides have no
  tail reading at all.
- The mislabel is not in the paper draft yet, but it has spread to notes and to this knowledge base:
  `DYNAMIC-LAYER-V4-NOTES.md:101`, 04 :24 and :66 ("calibrated"), 03 :111 and 07 :408 (the "max ~
  Tippett" premise).

**Fix.** Wording only. Describe e as a plug-in conformal p-value times daily volume, the expected
number of his calls a day at least this rare. Claim no calibration. Correct notes 03, 04 and 07
(K5). Add a reliability plot only if calibration is ever claimed. See options b1 and h1-h6.

**Sources.** [05](05-system-map.md) section 5; [04](04-score-aggregation-and-calibration.md)
section 1.2; arxiv.org/abs/2104.08279 (judge opened); `memory.py:89-102`.

## C10: The ceiling moves the neutral point

**Claim.** With ceiling 0.9, tool, network and client reach s = 0.5 at e = 0.4, not at "every
other day" (e = 0.5), so the doc's shared midpoint is false for them.

**Verdict.** True, high confidence. **Severity: low.**

**Decisive evidence.**

- The ceiling scales the whole curve: `engine.py:356,414` compute `0.9 / (1 + 2e)`, so 0.5 falls at
  e = kappa - 1/2. At e = 0.5 the score is 0.45 (x0.965); at once in 10 days it is 0.75 (x2.24),
  not the table's 0.83 (x2.89, `DIMENSION_FORMULAS.md:397`). x3 needs once in 28.7 days, against
  once in 10.6 days at kappa = 1.
- The doc contradicts its own formula (:173 against :182, :395-397, :471, :460, :801). The notes
  repeat it (:21, :80, :111-114, :142, :246 "caps", :277).
- Wider than claimed: the excess score reaches 0.5 at today = 2mu + u, not 2mu. At mu = 1 it is
  0.429.
- Correction to the framing: asset and hour of day (kappa = 1) match the excess score at large mu.
  The outliers are the three kappa = 0.9 dimensions and the small-mu excess scores. The max is in
  effect a weighted max.
- Not broken: the s-to-M map is identical for all dimensions, and monotonicity, boundedness and the
  exact attribution do not depend on a shared native-unit midpoint. No result changes.

**Fix.** Define the shared scale on the s axis. State each family's 0.5 point in its own units.
Call kappa a weight that scales the curve, not a cap. Correct the table rows. Add unit tests that
pin each family's edge. An optional tau_d = 4 kappa_d - 2 arm, as a sensitivity row. See options b1, b2
and b7.

**Sources.** [05](05-system-map.md) section 4; `engine.py:117-122,184-188,356,414,420,425,589`;
`tests/behaviour/test_engine.py:114-115`.

## C11: Zimek et al. warn against the max

**Claim.** Zimek et al. 2014 warn that the max lets a single noisy detector decide the result, so
citing them as support for the max is misleading.

**Verdict.** True, high confidence. **Severity: medium.**

**Decisive evidence.**

- Zimek, Campello & Sander, SIGKDD Explorations 15(1), p. 18 (judge re-read the PDF text): the
  max "has a tendency to overestimate the outlierness ... a single result that is far off ...
  will determine the ensemble result". Also: "In our opinion ... using the maximum of scores has
  some decisive disadvantages whereas the average does seem to make more sense". The reviewer
  understates; this is a stated preference, not a neutral trade-off.
- Two exceptions, both on p. 18: (a) the max over models learned in different subspaces
  ("multiview" outliers), which they call "orthogonal to the ensemble or consensus idea"; (b) "If
  the cost of missing a single outlier is much higher than the cost for a high false alarm rate".
  Section 5.2 also assumes "normalized outlier scores".
- Our text cites them for the opposite: `DYNAMIC-LAYER-V4-NOTES.md:147-149, 271-273` ("averaging
  would dilute") and `DIMENSION_FORMULAS.md:523-526, 825-826`.
- The warned failure mode is in our results: one flag sets d* for 71% of ordinary x3 days.
- Exception (b) does not fit a design that rejects options over a 0.8-point false-alarm rise.
- Not in `main-restructured.tex` yet.

**Fix.**

- Recast the max as the multiview/subspace choice, and quote the warning.
- Credit the "one detector is not diluted" argument to Aggarwal & Sathe only, with their
  short-history variance caveat.
- Drop exception (b), unless it is scoped to the first-access floor.
- Meet the normalisation precondition (calibrated max), and measure each dimension's share of the
  false-alarm budget. See options c1, b4 and b5.

**Sources.** kdd.org/exploration_files/V15-01-02-Zimek.pdf (judge re-read the text);
doi:10.1145/2594473.2594476; [04](04-score-aggregation-and-calibration.md) section 2.

## C12: What v4 costs

**Claim.** v4 lowers false alarms but slightly lowers the daily list's catch rate and leaves
over-fetching completely undetected, while the draft suggests more than this.

**Verdict.** Partly true, high confidence. **Severity: medium.**

**Decisive evidence.**

- The numbers are right. Ordinary agent-days at x3 go from 3.01% to 2.46% in all five
  organisations. Catches at x3 stay at 70.7%. The (M, s2) list goes from 59.0% to 57.8%.
  Over-fetching is caught in 0 of 47 episodes.
- The framing is wrong. The draft reports no v4 results (`main-restructured.tex:1142`) and still
  describes the old L(c) (:867), so it cannot overclaim them. The real defect is that v4 and its
  costs are absent.
- The design doc already discloses all three costs ("What v4 costs"; Open decisions 1 and 4).
- The list loss is not robust. It appears only at top 4. The large organisation is 57.4 against
  57.4 at top 8, and main goes 68.4 to 70.9 at top 8. Under random ties v4 is better (main 50.2 to
  53.2). The 1.2-point mean is about 6 of 460 episodes. The mean also mixes k: top 4 throughout
  gives 55.8% to 53.6% (N4).
- Missed by the reviewer: under v4, s2's advantage over random ties shrinks from about +5.6 points
  to about +0.5.
- "Completely undetected" is true by construction for the argument-blind M: over-fetch calls have
  a fixed size and no page-size argument. The gateway's B x L factor raises perPage=100 only to
  x1.2. The abstract's "invocation-specific arguments" (:105) over-describes the evaluated
  multiplier.

**Fix.**

- Replace the L(c) text with v4.
- Lead with the paired false-alarm drop, with clustered intervals.
- Report list detection as "no measurable change", with all four rankings at both budgets.
- Declare over-fetching a scope limit of an argument-blind M, with 0/47 and its interval
  [0%, 7.6%].
- Scope the abstract.
- Run a budget sweep, and test over-fetching through the argument and response channels (option d9). See
  options e4 and h1-h6.

**Sources.** `DIMENSION_FORMULAS.md` "Simulation (v4)" and "What v4 costs";
`results/normal_org_sim.md:44-45,287-302`; `results/normal_org_git_large.md:121-136`;
`results/normal_org_git_heavy_files.md:121-136`; `normal_org_world.py:797-799`; `framework.py:1-20`.

## Issues the review missed

The gap hunters (simulated reviewers) reported 48 items. After merging duplicates, 31 remain.
Probe numbers come from the hunters' scripts in the session scratchpad (gap K11). Where an item
overlaps a claim, the overlap is noted, and the item is listed only for what it adds.

### Critical

**N1. The worst-case binding driver is written into the behaviour history on the live route.**

- *Evidence.* `framework.py:186-191` passes `asset=cell.driver`, the worst surviving candidate
  (`binding/scoring.py:110-121`). The engine then adds it to `st.assets`, `last_read` and
  `read_sensitive` (`engine.py:440-445`). Probes with the real RouteScorer on
  `github_remote.cells.json`:
  - A developer's first routine read scores x3.62 ("asset 0.90").
  - A routine "read a file, then file an issue" raises unsafe sequence (x3.62) on day 0. The habit
    discount then trains it off (0.45 on day 1, 0.34 by day 7).
  - 120 reads across 40 unregistered repositories count as one asset; only call rate catches them
    (x3.21).
  - 30 days of reads on an unregistered repository make the first real read of
    helios-scada-gateway score M = 0.888. A fresh user's same call scores x3.62. The floor is
    disarmed for the most sensitive asset.
- *Fix.* Give the engine the named container as a pseudonymised handle. When resolution fails,
  pass no asset, or `unresolved:<tool>:<hash>`, and never update history with a worst-case driver.
  Add a pipeline test. Extends C5 from "unspecified" to "measured failure".

**N2. The paper describes a different dynamic layer, reports no dynamic results, and the code
emits two dynamic numbers on scales that do not match.**

- *Evidence.*
  - `main-restructured.tex:846-868` describes L = D·A·N in [1, 8], "bounded below by 1".
    Lines 922-956 describe persona profiles and band composition.
  - :1142 reports only the static scanner.
  - The gateway logs both `risk` = cell x B·L and `dynamic_risk` = cell^(1/3) x M
    (`framework.py:194-206`, re-read).
  - On the paper's 1-125 bands, R_dynamic^3 = T·S·B·M^3, so M acts as a factor in [0.34, 125]. A
    Low cell of 8 with M = 5 maps to 1000, against Critical >= 100.
  - The real_benign corpora (1,000 rows; no timestamps; 1 or 5 callers) cannot exercise v4.
- *Fix.* Rewrite sections 4.3 and 5.3 around v4 with one notation table. Define
  R_static' = (T·S·B)^(1/3) and bands for R in [0.7, 25]. Retire or rename `risk`. Add a Dynamic
  Results section. Overlaps C2, C6 and C12; the scale arithmetic and the second output are new.

### High

**N3. The headline false-alarm rate leaves out labelled benign-change days.**

- *Evidence.* One tagged call moves the whole day into "change" (`normal_org_sim.py:507-513`).
  v4 alerts per day:
  - main: 2.10 ordinary + 3.09 change, against 0.57 gray
  - heavy files: 1.33 + 3.12, against 0.70
  - large: 3.93 + 5.04, against 1.53

  Precision at x3 is 9.9%, 13.6% and 14.6%. The headline 2.46% covers about 40% of benign alerts.
  Prevalence is set by design (about one episode a day per 150 agents). On the base-rate
  fallacy, see Axelsson, ACM TISSEC 2000, doi:10.1145/357830.357849 (gap hunter opened).
- *Fix.* Count every benign agent-day in the headline, broken down by tag. Report precision, alerts
  per 1,000 agents per day, and precision against assumed prevalence (Bayes). Do not label a whole
  day from one call.

**N4. The review-list metric credits coincidental alerts, has no chance floor, and mixes list
sizes.**

- *Evidence.*
  - An episode counts if its agent-day is listed, even when the listed call is unrelated
    (`normal_org_sim.py:430-436, 543, 556`).
  - A random list at k = 4 catches 6.5% overall, 25.9% of scope creep and 11.3% of Saturday
    batches.
  - The v4 table uses top 8 for the large organisation without saying so. Top 4 throughout gives
    55.8% to 53.6% (-2.1 points), and -4.7 for the large organisation.
  - k is fixed for organisations of 60 to 300 agents.
- *Fix.* Credit an episode only when d* comes from an episode call. Report the lift over random
  per kind and recall@k curves. Scale k with active agent-days.

**N5. Volume poisons the baseline.**

- *Evidence.*
  - Hour of day and Footprint count calls, not days. One 30-call night at 03:00 turns later 03:00
    calls from x4.94 into x0.95 for more than 50 days. 300 calls on a new asset make it x0.89 the
    next day.
  - The excess "usual" is call-weighted (size-biased). One 600-call hour raises it from 9.4 to
    51.8, so a later 12x hour drops from x3.11 to x1.12.
  - The tail sum: one day touching 30 public repositories once each turns a sensitivity-3 first
    access from x4.36 into x0.95.
  - Every call, alerted or rejected, is learned (`engine.py:436-457`).
  - The repo had already measured the "v2 + days" fix (x3.84 against x0.97) but kept call counts.
  - The learning window is gray-free by construction, so poisoned limits are never exercised.
  - Poisoning precedent: ANTIDOTE, IMC 2009, doi:10.1145/1644893.1644895 (gap hunter opened).
- *Fix.* Cap each day's contribution (log1p or min(count, c); counting days alone raised false
  alarms to 52.9%). Use a time-bucketed robust "usual". Hold back M >= 3 agent-days until reviewed.
  Add condition-then-exploit scenarios.

**N6. The habit discount is self-granted and loses the toxic-flow episodes.**

- *Evidence.*
  - Burst, sweep and sequence are discounted by the number of days each flag was raised, with no
    review (`engine.py:504-515`). The flag falls under x3 after 3-4 raised days.
  - This contradicts the red-flag definition, "the same for every agent"
    (`DIMENSION_FORMULAS.md:37`).
  - Cross-copy is caught 6/6 under v2, 1/6 with the discount alone, 2/6 under v4 (main) and 1/7
    (seed 11).
  - Cross-copy is the stand-in for the GitHub MCP toxic agent flow (Invariant Labs, 2025-05-26; gap
    hunter opened).
- *Fix.* Discount only flag-days an operator dismissed, or only repeats of the same signature
  (read asset to write asset). Never discount a sequence whose read is more sensitive than the
  write target. Report cross-copy with and without the discount.

**N7. The rarity score is not monotone where novelty begins.**

- *Evidence.* An unseen value uses nu_d, which is at least the number of singletons
  (`memory.py:95-102`). An asset used once scores s = 0.938 (x4.10), and a never-touched asset
  scores 0.718 (x2.01). The doc's own example shows the same (0.79 against 0.83). This breaks
  property 5 ("a stranger call never scores safer"). Only sensitivity 4-5 assets are protected,
  by the floor.
- *Fix.* Make N_d non-decreasing in n_d(v) by construction: min(nu_d, singleton mass), or a
  Good-Turing estimate. State it as a lemma and add a property-based test.

**N8. Callers control the identity key: day one is free and a new client_id is a new baseline.**

- *Evidence.*
  - The key is sha256(iss | client_id | sub) (re-read `oauth.py:110`).
  - MCP 2025-06-18 says clients and servers SHOULD support Dynamic Client Registration. 2025-11-25
    makes CIMD a SHOULD and DCR a MAY, and says CIMD "cannot prevent localhost URL impersonation"
    (gap hunters opened both).
  - Warm-up requires 5 calls AND past the first UTC day. A fresh identity makes 2,400 writes at
    M = 1.00 (06).
  - The simulator keeps one baseline per person and models a "client switch" inside one id, so the
    "client switch 45% at x3" result does not describe the gateway.
- *Fix.* Key Cadence and Footprint on (iss, sub), with client_id as a Footprint value. Start new
  identities from a role or org prior. Make IdP trust policy (CIMD allowlist, DCR rate limits) a
  stated assumption. Rerun the simulator with the gateway's identity function.

**N10. Dormant and sparse identities are scored as familiar.**

- *Evidence.*
  - After 60 active days and 120 days of silence, a return at 02:00 from a new /16, a new client, a
    new tool and a new asset scores M = 0.89 on all 31 calls. Network and client do not take part
    (`memory.py:43-54, 89-102`; `engine.py:354`).
  - An agent with 4 active days gets x1.99 where a 60-day agent gets x4.51.
  - Entra ID Protection: "A user can go back into learning mode after a long period of inactivity"
    (gap hunter opened). Vendors also wait longer before scoring (03).
- *Fix.* Add a days-since-last-active dimension. Shrink toward a role or org prior while A is small,
  or floor M at 1. Add dormant and sparse identities to the simulator.

**N11. The gateway forwards every caller with one shared upstream credential.**

- *Evidence.* `proxy.py:4,86,454-461` strip the agent's Authorization and inject one key
  (`GITHUB_TOKEN` in `routes.example.json`). Effective permissions are the union of all callers', so
  the layer, which never blocks, is the only access check. GitHub's audit log cannot corroborate
  attribution. MCP 2025-06-18 forbids passing the client's token through (gap hunter opened); the
  gateway does not pass it through, but it pools access.
- *Fix.* Use per-user upstream credentials (OAuth per user, or RFC 8693 token exchange; gap hunter
  opened RFC 8693), or state the privilege pooling in the threat model. Put the exchange id into
  the upstream request for audit joins.

**N12. `resources/read` and `prompts/get` bypass the dynamic layer.**

- *Evidence.* Only `tools/call` goes to `_decide` (`proxy.py:182-185`); other methods score only
  network and client (`engine.py:292-294`). The static scan covers only the 49 tools.
  github-mcp-server serves raw repository files through `repo://{owner}/{repo}/contents{/path*}`
  templates (gap hunter opened `pkg/github/repository_resource.go` at commit 926d0491).
- *Fix.* Score resource and prompt reads as calls: map URI templates to pseudo-tools and URI
  variables to assets, and scan them. Report the share of request methods that are scored.

**N13. All behaviour state lives in one process.**

- *Evidence.*
  - Engine state, sessions and SessionBook are in memory, and by default the state is saved only on
    a clean shutdown (`config.py:83-84`).
  - Behind N round-robin replicas, every cadence check and red flag becomes N times looser, and the
    first-access floor fires once per replica.
  - After a restart, a merge in a still-open reviewed session scores x3.62 (sequence plus missing
    handshake), because `SessionState.tools` is not saved.
  - A crash puts every caller back in warm-up.
  - With `state_every` > 0, `save_state` runs on the request path: 22.5 MB and 1.6 s for 300 agents
    with 90 days of history.
- *Fix.* Shard by caller key, or use a shared store. Persist open sessions with a TTL. Take
  incremental snapshots off the event loop. Evaluate N = 2 and N = 4 in the simulator.

**N14. Gray episodes carry the detector's own giveaways, and none is adaptive.**

- *Evidence.*
  - The shadow script is hard-coded to 01:00-03:00, a cloud /16, `python-requests` and no
    `initialize` (`normal_org_world.py:735-744`). The doc credits its 100% catch to the hour.
  - Without the client score (which the gateway would not have; N15), one script drops from x3.32
    to x2.84.
  - cross_copy always runs in one session, and bulk export hits 20-40 repositories in 1.5 h.
  - Mimicry precedent: Wagner & Soto (judge opened).
- *Fix.* Add an adaptive variant of each kind that stays within the victim's hours, /16, client and
  histogram and paces under the documented lines. Report the most an attacker gets through under
  x3. Extends C8 from definitions to measurement.

**N15. The simulator gives the engine inputs the gateway cannot derive, and the port check skips the
gateway pipeline.**

- *Evidence.* The simulator gives the engine:
  - oracle asset and sensitivity (`normal_org_sim.py:223-224`);
  - a client name on calls that never sent `initialize` (`normal_org_world.py:740-741`), whereas the
    gateway reads clientInfo only from `initialize` or `_meta` (`wire_log.py:145-153`);
  - comments labelled as writes;
  - a written merge-review rule, whereas a log-learned policy starts empty (`policy.py:203`);
  - a sweep limit, which is off for log-learned policies.

  `check_port` feeds simulator rows straight into the engine (`normal_org_sim.py:395-399`).
- *Fix.* Replay each world as JSON-RPC through `gateway/proxy.py` with OAuth tokens, the scan and
  the binding (extend `scripts/gateway_replay_corpus.py`). Report the same tables. Overlaps C5 and
  N1.

### Medium

**N9. The org discount trusts any three identities.**

- *Evidence.* `FirstUses.others` counts other identity keys in 7 days, first-day ones included
  (`memory.py:231-238`; `engine.py:546-556`). Three fresh identities drop a focused agent's first
  touch from x4.51 (or x4.37 in 06) to x1.00. A prompt injection in a widely read issue makes many
  agents start the same tool in the same week, and this looks like an org change.
- *Fix.* Count only distinct established subjects past onboarding, with a threshold relative to org
  size. Require an observable org event (a catalog digest change, which `proxy.py:383-397` already
  tracks, or an admin-declared migration). Never discount write, destructive or static >= 4 tools.

**N16. Sequence checks are scoped to one session on one route.**

- *Evidence.*
  - A session split takes x3.62 to x0.94-0.98.
  - `requires_before` checks the tool name only: a review on one PR then a merge on another raises
    nothing.
  - One global LRU of 50,000 sessions (`engine.py:597-608`) lets 1,001 junk session ids evict a
    victim's session (with the cap scaled to 1,000). The victim's next call then scores x1.90.
  - One engine per route (`proxy.py:136-147`) makes a read on the GitHub route and a post on the
    Slack route invisible, and each new route resets warm-up.
- *Fix.* Keep sensitive reads per caller across sessions and routes (1 h and 24 h windows). Tie
  `requires_before` to the same asset or PR. Add per-identity session quotas, and create a
  SessionState only after the server accepts the id. Add an outbound-capable attribute from the
  static scan.

**N17. Tool names do not match operations, and "merge with no review" checks no review.**

- *Evidence.* The remote GitHub server multiplexes operations behind a `method` argument (issue_read,
  issue_write, pull_request_read, ...; README opened by a gap hunter). So create, update and get
  collapse into one tool, with one read/write label. The review tools are all reads, and the
  engine never checks for the same PR or for an approval.
- *Fix.* Key the tool dimension on (tool, operation selector), and set read/write per (tool, method).
  Rename the flag, or require the same asset plus an approved review state.

**N18. Learned red-flag limits are the maximum of a small, unlabelled sample.**

- *Evidence.*
  - The quantile index is n - 1 when n < 200 (`policy.py:53,56,113-117`), so a tool with 50-199
    agent-days gets the largest request ever seen as its limit.
  - Burst is pooled over bots and people (learned 48/min against a default of 20).
  - Limits are fixed forever.
  - Rare or new tools fall back to the global loosest limit (for example, `create_release` after the
    day-130 release).
  - In 06's toy set (150 x 30, all agents active; K11), 23 inflated agent-days moved the burst limit
    from 13 to 200.
- *Fix.* Require 200 agent-days for a tool's own limit. Let each identity contribute one agent-day.
  Learn separate lines for bots and people. Fall back by operation class. Re-learn on catalog
  change.

**N19. The caller chooses which dimensions take part.**

- *Evidence.* Missing fields silently drop dimensions (`engine.py:349-350, 403-404, 418, 483, 578`).
  A sessionless call with no clientInfo is scored on 8 of 15. Under the max, fewer participants can
  only lower s1. P(s1 >= t) also grows with the number of dimensions, so "the alert line never
  moves" is false. This holds in the legacy era too.
- *Fix.* Fail closed: score a missing value as its own value, or flag it when he usually sends it.
  Report false alarms by the number of participating dimensions.

**N20. The proxy sees every response, but the layer ignores it.**

- *Evidence.* `proxy.py:211-228` parses every reply, but `Message.size` counts request bytes only.
  Over-fetching (0/47) and bulk-export volume are response-side quantities. So Open decision 4
  ("cannot be seen without reading an argument") is wrong for a gateway.
- *Fix.* Add response bytes and item counts as Cadence dimensions, plus a per-tool response-size
  flag. They feed the next call's M and the list.

**N21. The stated formulas do not match the code.**

- *Evidence.*
  - (a) The excess score is 0.5 at 2mu + u.
  - (b) mu is call-weighted.
  - (c) The 5-call warm-up was kept although listed as removed.
  - (d) Discounted flags still take part below 0.5.
  - (e) The weekend blend is applied to weekday calls.
  - (f) "Smooth, no cliffs" is wrong: dM/ds jumps from 0.71 to 3.22 at s = 0.5.
  - KB 05 adds: seed 11 learned a required step that the doc says was not found, and R_static is
    defined differently in the gateway and the simulator.
- *Fix.* Write the paper's equations from the code, or change the code. Add one test per stated
  property.

**N22. No uncertainty is reported, and the five organisations are not replications.**

- *Evidence.* Per-kind n is 3-7 in the main organisation (Clopper-Pearson lower bound 29% for 3/3).
  79 episodes give an SE of about 5.5 points at 58%. Agent-days cluster by agent. The worlds are
  one generator, one server (26 GitHub tools) and the same 10 kinds.
- *Fix.* Wilson or Clopper-Pearson intervals per kind. Cluster bootstrap. Paired McNemar for v3
  against v4. Report alert concentration. At least one non-GitHub world.

**N23. Time to detection and enforcement are not evaluated.**

- *Evidence.*
  - "Caught" means any one call reached x3 (`normal_org_sim.py:571`).
  - The share of an episode's calls at x3 is only 2% for scope creep and 8% for mass cleanup.
  - The paper says a verdict comes "before the invocation proceeds" (`main-restructured.tex:891-892`),
    yet the gateway never blocks, background mode scores after forwarding, and scorer exceptions
    fail open.
  - `score_us` excludes the state-save pause.
- *Fix.* Report harm before the first alert (calls, distinct assets, bytes). Report a hypothetical
  gate's benign block rate. Report end-to-end p50/p99 latency in inline mode with snapshots on.
  Limit the pre-execution claim to inline mode.

**N24. Some dimensions do not match the threat model, and misuse is injected only into human
identities.**

- *Evidence.* Network, client and missing handshake are justified by stolen credentials, while
  authentication bypass is out of scope (`main-restructured.tex:421,429`). Bots get no gray episodes
  except the misconfigured loop (`normal_org_world.py:804`).
- *Fix.* Add credential misuse to section 3 with its assumptions, or move those dimensions to an
  impersonation extension. Map each dimension to a threat clause. Inject episodes into bot
  identities.

**N25. Results cannot be traced to code.**

- *Evidence.*
  - The v2-v4 engine, `test_engine_designs.py`, the simulator and all v4 results are uncommitted.
  - Result JSONs carry no commit or config digest.
  - `--only` merges runs.
  - Scores are pickled to /tmp.
  - The port check covers only the main organisation.
  - The decision record lacks `Verdict.scores` and s2.
- *Fix.* Commit and tag. Store the SHA and config digest with each row, and refuse merges across
  versions. Log the score vector and s2.

**N26. The interpretability claim is untested, and v4 makes reasons less informative.**

- *Evidence.* The first-access floor is folded into "asset 0.90" (`engine.py:430-431`). Org and
  habit discounts carry no marker, and s2 is never shown (`framework.py:296-305`). The human study
  covers only static dimensions.
- *Fix.* Emit structured reasons (the mechanism, the raw counts, and s2). Run a small triage study,
  or drop the interpretability claim for the dynamic layer.

**N27. Day, hour and weekend are UTC.**

- *Evidence.* `engine.py:283,387-388` and `memory.py:17-19` use UTC. A UTC-6 workday spans two UTC
  days, which inflates A. At UTC+10, Monday morning is Sunday UTC. Warm-up length depends on the
  start time. No daylight saving is modelled.
- *Fix.* Use local time from an IdP claim or a learned modal offset, and roll the day over at 04:00
  local. Add APAC and daylight-saving agents.

**N28. Hosted agent platforms make the network dimension constant.**

- *Evidence.* Anthropic publishes 160.79.104.0/21 as its outbound range for MCP tool calls (gap
  hunters opened platform.claude.com/docs/en/api/ip-addresses). That range is inside one /16, so
  every hosted-connector user has the same network value. The simulator has no hosted egress.
- *Fix.* Mark registered platform egress ranges as shared and leave them out. Split the evaluation by
  hosting (local client, hosted connector, CI). Whether platforms supply origin attributes is
  UNVERIFIED.

### Low

**N29. Scalability beyond about 100 assets is untested.**

- *Evidence.* The tail sums run over all values on each call, and the agents dict is unbounded.
  Throughput (11,398 messages/s) was measured only on about 100 repositories.
- *Fix.* Fenwick tree over count buckets; LRU with cold state on disk; benchmark at 10^5 assets and
  10^4 identities.

**N30. Unparseable bodies are forwarded with no verdict.**

- *Evidence.* Invalid JSON becomes `{'unparsed': ...}` and is forwarded unscored
  (`http_wire.py:72-81`; `proxy.py:180-195`). Content-Encoding is not stripped.
- *Fix.* Fail closed (400), decode or reject non-identity encodings, forward the canonical message,
  and count unscored forwards.

**N31. Privacy and ethics of per-employee profiling are not discussed.**

- *Evidence.* State holds /16 networks, hour histograms and sensitive-read days. Logs keep raw
  addresses, `sub` and user agent (`wire_log.py:357-379`).
- *Fix.* Add a privacy and ethics subsection. Use keyed-hash pseudonyms for /16s, retention tied to
  90 days, and audited access to profiles.

## Knowledge-base gaps

From the completeness critic. README.md now closes part of K7 (the per-dimension era table) and
part of K16 (index, contradictions table, UNVERIFIED ledger).

- **K1 (critical).** 02 and 06 still say "M reads no arguments", and 06 has no evasion row for
  steering the binding with free text, which can lower a sensitivity-5 first access from x3.62 to
  x2.63 or below. Fix: use 05's wording; add evasion row 8b and mitigation M10 (identifier-typed
  matching; worst case on disagreement).
- **K2 (critical).** No note says which quantity drives which decision. R is never evaluated, and
  there are two R_static definitions. 02's novelty claim 2 ("a bounded multiplier on a static
  score") rests on this. Fix: define the outputs (option e1) and one R_static; rerun static x M with
  per-asset cells; restate the claim if R still loses.
- **K3 (high).** The notes contradict each other on offline ablation, and no log supports it (the
  pickle is gone; none of the 26 gateway and proxy logs has a `behaviour` field). Fix: see the
  README contradictions table; log the vectors persistently under `results/`.
- **K4 (high).** 04 section 2.3 claims both Zimek exceptions hold, against a false-alarm-first
  design. The notes say "the alert line never moves" (:140), which contradicts the multiplicity
  results. Fix: rest on multiview plus normalisation.
- **K5 (high).** 03 and 07 call the rarity score an empirical p-value, and 07's combiner hypothesis
  depends on it. Fix: e = lambda_hat x p. Within Footprint, Tippett on p = e/lambda_hat differs from
  max of e by the per-agent lambda_hat.
- **K6 (high).** 04 and 07 give incompatible calibration and combiner specifications (unit, Sidak
  against weighted Bonferroni, red flags), and 07's arm list misses arms from 02, 03, 04 and 06.
  Fix: make 07 section 3.4/3.6 the single preregistered family, with a Holm correction.
- **K7 (high).** There was no canonical era table. 02's Implication 4 overclaims that per-caller
  baselines need no session notion (the sequence checks do). Implication 8 cites the 2025-06-18
  lifecycle without scoping. 04 section 5.2 has no era caveat. 07's freeze checklist lacks the
  `requires_before` fix. Fix: README table; correct 02, 04 and 07; add a "modern era" leave-group-out
  arm.
- **K8 (high).** 01, 02 and 06 recommend different baseline keys and fallbacks. RFC 9068, 8693 and
  7662 were not opened for which claims exist. Fix: open them and pick one key and one documented
  unauthenticated fallback.
- **K9 (medium).** 01's revision table misdates "MUST NOT use sessions for authentication" (it is in
  2025-06-18). 06 cites a URL that redirects. No paste-ready BibTeX exists for the versioned spec
  revisions or SEP-2575/2567. Fix: cite GitHub tag paths; add the BibTeX.
- **K10 (high).** The held-out protocol (07 section 3.1) ignores the simulator's non-determinism, the
  untracked files and the sim-versus-gateway gaps. Fix: a pre-freeze list (option g1).
- **K11 (medium).** Probe and repro scripts behind key numbers live only in the scratchpad. 06's E8
  used a toy set (13/min, against the main world's learned 48/min). Fix: copy them to
  `knowledge_base/probes/` with a README; rerun E8 on the main world's days 0-29.
- **K12 (medium).** 07 uses USENIX Security '26 rules, a past cycle. `paper_v5/README.md:13-15`
  (re-read) targets AAMAS 2027 with a deadline "early October 2026 (TBC)", which has passed as of
  2026-10-25, and an 8-page body. Fix: confirm the venue with the author; open its current CFP;
  decide what fits in the body.
- **K13 (medium).** Dataset gaps:
  - FragBench is missing from 03.
  - CLUE coverage is 8 direct plus 5 by proxy, not "13 of 15".
  - GH Archive cannot test unsafe sequence per caller.
  - AIDev and the Ghaleb fingerprinting paper are not in the knowledge base (UNVERIFIED here).
  - The GH Archive licence is open.
  - The first real-data check should be oversized-request false alarms on real GH Archive body sizes.
- **K14 (medium).** Unverified citations remain open across files (see the README ledger).
  `zimek2014ensembles` and `aggarwal2015outlier` are not in `refs.bib`.
- **K15 (medium).** v4 overhead is unmeasured. The existing `score_us` (148 values, median 188 µs,
  p99 306 µs) predates the behaviour layer. Real AI-agent cadence (loops, pagination, retries) is
  never characterised. Fix: measure; fit agent profiles from MCP-Bench trajectories.
- **K16 (low).** The README was missing (now added). There was no claims ledger. The human-study
  method is not covered. 03's warm-up sentence is wrong. Six notes exceed 400 lines.

## References

Primary sources, with who opened them in this workflow.

- Arp, D. et al. "Dos and Don'ts of Machine Learning in Computer Security." USENIX Security 2022.
  usenix.org/system/files/sec22-arp.pdf; arXiv 2010.09470. Judge opened.
- Axelsson, S. "The Base-Rate Fallacy and the Difficulty of Intrusion Detection." ACM TISSEC 2000,
  doi:10.1145/357830.357849. Gap hunter opened.
- Bates, S. et al. "Testing for Outliers with Conformal p-values." Ann. Statist. 51(1):149-178, 2023,
  doi:10.1214/22-AOS2244; arXiv 2104.08279. Judge opened the abstract; checkers read eq. 3.
- Birnbaum (1954). JASA 49(267):559-574, doi:10.1080/01621459.1954.10483521. Judge opened the
  abstract; the full title was not recorded in this workflow.
- Heard, N. and Rubin-Delanchy, P. "Choosing between methods of combining p-values." Biometrika
  105(1):239-246, 2018, doi:10.1093/biomet/asx076; arXiv 1707.06897. Judge opened.
- Kloft, M. and Laskov, P. "Security Analysis of Online Centroid Anomaly Detection." JMLR
  13:3681-3724, 2012. jmlr.org/papers/v13/kloft12b.html. Judge opened.
- Kriegel, H.-P. et al. "Interpreting and Unifying Outlier Scores." SIAM SDM 2011,
  doi:10.1137/1.9781611972818.2. Judge opened.
- Aggarwal, C. and Sathe, S. "Theoretical Foundations and Algorithms for Outlier Ensembles." SIGKDD
  Explorations 17(1), 2015, doi:10.1145/2830544.2830549. Opened by the 04 author and the critic;
  one judge's re-fetch failed.
- Rubinstein et al. "ANTIDOTE: understanding and defending against poisoning of anomaly
  detectors." IMC 2009, doi:10.1145/1644893.1644895. Gap hunter opened; title as in 06.
- Sommer, R. and Paxson, V. "Outside the Closed World." IEEE S&P 2010.
  oaklandsok.github.io/papers/sommer2010.pdf. Judge opened.
- Wagner, D. and Soto, P. "Mimicry Attacks on Host-Based Intrusion Detection Systems." CCS 2002,
  doi:10.1145/586110.586145. Judge opened.
- Zimek, A., Campello, R. and Sander, J. "Ensembles for Unsupervised Outlier Detection." SIGKDD
  Explorations 15(1), doi:10.1145/2594473.2594476. kdd.org/exploration_files/V15-01-02-Zimek.pdf.
  Judge opened.
- ACM SIGSOFT Empirical Standards, Simulation (Quantitative).
  raw.githubusercontent.com/acmsigsoft/EmpiricalStandards/master/docs/standards/QuantitativeSimulation.md.
  Judge opened.
- CVSS v4.0 specification. first.org/cvss/v4.0/specification-document. Judge opened.
- MCP specification 2026-07-28: changelog and basic/versioning. Judge opened. SEP-2567 and
  SEP-2575: checkers opened. 2025-06-18 basic/authorization and 2025-11-25 authorization: gap
  hunters opened.
- Invariant Labs, "GitHub MCP Exploited", 2025-05-26. Gap hunter opened.
- github/github-mcp-server `pkg/github/repository_resource.go` at commit 926d0491, and its README.
  Gap hunters opened.
- Anthropic IP addresses page, platform.claude.com/docs/en/api/ip-addresses. Gap hunters opened.
- Microsoft Entra ID Protection risk concepts,
  learn.microsoft.com/en-us/entra/id-protection/concept-identity-protection-risks. Gap hunter opened.
- RFC 8693 (OAuth 2.0 Token Exchange). Gap hunter opened.
- UNVERIFIED: the Splunk ES risk-based-alerting example; Anderson 1980's taxonomy; Arp P10's
  verbatim wording.
- Knowledge-base notes: [01](01-mcp-protocol.md), [02](02-mcp-runtime-security-literature.md),
  [03](03-ueba-insider-threat-and-datasets.md), [04](04-score-aggregation-and-calibration.md),
  [05](05-system-map.md), [06](06-threat-model-and-evasion.md),
  [07](07-evaluation-methodology.md).
