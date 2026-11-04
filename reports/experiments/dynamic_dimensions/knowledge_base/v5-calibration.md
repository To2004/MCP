# v5 score calibration: daily rates with budget shares

This note fixes how design v5 turns the 15 dimension scores into the behaviour multiplier M, so
that a stated alert budget bounds false alarms on ordinary agent-days. It synthesises the four
Part B calibration proposals and the three judgments, and adds one probe run of the grafted design.
Every number is from the burnt worlds main_seed7, main_seed11 and heavy_files_seed21
(PYTHONHASHSEED=0) and is a **development world** number, never a test result.

## Status after review (revision 2, 2026-10-25)

This note is the record of arm S5, the **calibration stage on v4 scores**: v4 engine vectors with
oracle simulator inputs. None of its numbers is a v5 number or goes into the paper (R1-11,
R4-7). The four-reviewer pass changed the design. The current design is
[v5-design-spec.md](v5-design-spec.md) revision 2, which has the finding-by-finding Review log.
These parts of this note are superseded:

| Here | Superseded by (spec revision 2) | Finding |
|---|---|---|
| "daily rate" (§1, §9) | renamed **commonness**; one rule for every dimension, Footprint included unless D3 = (b) | R4-3, R1-9 |
| record price c_d / (A + 1) and assumption A2 (§1, §2) | the **record rank among all route agent-days**, q_d = min(1/(A_d + 1), r_d); one exchangeability assumption | R2-1 |
| `record_min_reference = 19` (§1, §5, §10) | derived path activity, N_d + 1 ≥ 1/(w_d α) | R1-4, R2-9, R4-12 |
| the guarantee 0.6α + r_floor(u) for "a warm agent-day" (§2) | a marginal bound, α + β (or (2/3)α + β if Footprint is watch-only), with declared floor budgets | R1-5, R2-1, R2-10 |
| the paper sentence (§2) | spec §2.6 | R4-5 |
| deployed line x3 (§1, Decision in brief) | the 1% line (x4.69); x3 is reported for continuity | R1-7 |
| "the existing once-a-day learning point" (§5) | there is none: `DailyCounts.expire` folds lazily per caller (memory.py:43-48, per R3); the route clock is CAL-7 | R3-3, R3-16 |
| Missing handshake per era (§1, §4) | legacy-only and watch-only | R3-4, R4-8 |
| H1 alert hold, F1 (§4, §8) | the record hold (a tune candidate); Footprint by the one rule | R1-8, R4-9 |
| ordinary days only in the bound check (§2) | all benign days (Hyp2); the per-dimension spend check | R2-3, R2-1 |

New probe evidence for revision 2 is in
[probes/org_record_rank_probe.py](probes/org_record_rank_probe.py) and
[probes/hour_surge_check.py](probes/hour_surge_check.py).

## Decision in brief

- **Chosen: "daily rates with budget shares"**, Part B's per-dimension arm, with four grafts. The
  whole design was run as arm **S5** of
  [calib_v5_synthesis.py](probes/calib_v5_synthesis.py). Two of the three judges picked the base
  arm, for detection and for continuity with the paper names.
  1. The first-access floor becomes a policy rule outside the statistic. Sensitivity 5 sits on the
     1% alert line and sensitivity 4 keeps its v4 value (from personal day calibration and RF8).
  2. Oversized request is graded over the red-flag area's pooled agent-day line (RF1).
  3. Typical Cadence is counted in past **days**, not past calls. This makes the bound an exact
     per-agent-day statement with no volume term, which judges 1 and 3 asked for.
  4. Reliability is reported per group, per weekday class and per caller.
- **Kept from v4:** the 15 dimensions in three groups; s1, s2 and d*; the curve g
  (engine.py:184-188); the x3 alert line, now read as a 9.43% budget; the habit discount, org
  discount and warm-up.
- **Headline (development world, report window days 135-180):**
  - At a fitted 1% (ties by s2), v5 alerts on 0.54 / 0.26 / 0.53% of ordinary agent-days. v4
    alerts on 1.11 / 0.80 / 1.45%. Gray caught is 69 against 70 of 130 episodes.
  - At a matched benign rate of 1%, v5 catches 80 of 130 against v4's 50.
  - The k = 4 review list catches 63.3 / 64.3 / 72.2% against 55.7 / 44.0 / 51.9%.
- **Guarantee (revision 1 form, superseded; see the status table):** per agent-day, at most
  0.6 alpha plus the alert floor's own rate, for any alpha < 13.3%. On ordinary days the realised rate at the stated lines is at most 0.35 of the
  stated alpha in days 90-134, and at most 0.17 of it in days 135-180.
- **Not fixed:**
  - overfetch: 1 of 18 caught (needs AI-8 response sizes);
  - off_hours_batch: 1 of 10 against v4's 6 of 10;
  - cross_copy: 4 of 13 against 6 of 13;
  - Typical Footprint cannot alert on its own (cap x2.54);
  - one rehearsal day habituates a Cadence dimension.
- Every choice was made on burnt worlds. The design must be frozen and preregistered before any
  held-out world (EV-15, EV-16).

## 1. The design, from s_d to M

### Notation

- Caller u, day t (the local day of B9). His window J is his active days in [t-89, t-1], and
  A = |J| (memory.py:79-87; B5 stretches the window).
- s_d(c) is the v5 engine's score for dimension d on call c. The calibration sits on top of
  whatever s_d the other v5 areas produce: AI-2, E4/E5, B1, B6 and the RF items.
- w_d is the budget share. g(s) = 5^(2s-1) for s >= 1/2 and 0.7^(1-2s) below (engine.py:184-188).

### Stage 1: a daily rate per dimension

**Daily rate** q_d: how often per active day, in his last 90 days, he did something at least this
strange, counting today once.

| Group | Dimensions | Daily rate q_d | When it beats his whole window |
|---|---|---|---|
| Typical Cadence | Call rate, Write rate, Breadth, Repetition, Session duration, Hour of day | (1 + D_d) / (A + 1), where D_d = #{j in J : Q_d(j) >= s_d(c)} and Q_d(j) is his day maximum of s_d on day j (4096 bins; a tie counts as "at least") | record: q_d = c_d / (A + 1) |
| Typical Footprint | Tool, Asset (without the floor), Network, Client | e, v4's per-day rate (memory.py:89-101), recovered from s = kappa/(1 + 2e), with kappa = 0.9, or 1 for Asset. The org discount sets q_d >= 1/2. With B4, q_d >= 1/(A + 1) is kept after the role prior. | no record rank |
| Red Flags, habit | Burst, Sweep, Unsafe sequence | (1 + k_d) / (A + 1), where k_d is his raised days in J. This is the habit discount in add-one form (engine.py:504-515; rule_days at engine.py:233). | Burst and Sweep (k_d = 0): q_d = c_d / (A + 1), with strength = times over the limit. Unsafe sequence: c = 1. |
| Red Flags, org | Oversized request, Missing handshake | (1 + #{org agent-days in the window with rho >= rho(c)}) / (N_org + 1). For Oversized request, rho = size / RF1 line and it is raised when rho > 1. Missing handshake has rho = 1 when raised, in the legacy era only (E6). | not needed |

**Record rank** c_d: when a call is stranger than anything in his own 90 days, how it ranks among
the records the organisation's callers set on that dimension in the same 90 days.

- c_d = (1 + #{record-days on d in [t-89, t-1] with strength >= his}) / (R_d + 1).
- Each caller adds at most one record-day per dimension per day: his strongest.
- With fewer than 19 record-days in the reference, c_d = 1. The dimension then cannot alert:
  it fails quietly.

### Stage 2: budget shares

**Budget share** w_d: the part of the alert budget a dimension may spend. Each group gets a third,
split equally inside the group.

- q_stat(c) = min over d of q_d(c) / w_d, with w_d = 1/18 for each Cadence dimension, 1/12 for
  each Footprint dimension and 1/15 for each Red Flag. The shares sum to 1.
- d*_stat is the argmin and q2 is the second-smallest value.
- Shares are fixed. A dimension that cannot take part leaves its share unspent; Missing handshake
  in the MCP 2026-07-28 era is one. Shares are never renormalised, so dropping one dimension
  never moves another's line, and a leave-one-out ablation stays exact.

### Policy rules: alert floor and watch floor

These use the names from RF8. The first-access floor leaves the Asset score, which now enters
Stage 1 without it (today the floor is folded in at engine.py:430-431), and becomes its own rule:

- First access to a never-touched **sensitivity-5** asset: **alert floor**, q_floor = 0.01
  (x4.69). It alerts at every stated line.
- First access to a never-touched **sensitivity-4** asset: **watch floor**, q_floor = 1/8, v4's
  0.8 (x2.63). It never alerts on its own at x3 or any stricter line.
- q_final = min(q_stat, q_floor). When the floor wins, d* = "first-access floor" and q2 = q_stat,
  so the statistic becomes the runner-up.
- Any other alert floor the red-flag area adopts (RF6, copy out of sensitivity 5) enters the same
  way at q = 0.01. This is untested here.

### Output and alert line

- s1 = 1 / (1 + 2 q_final), s2 = 1 / (1 + 2 q2), M = g(s1) in [0.7, 5]. If PS8 is adopted,
  M = max(1, g(s1)); this changes no alert.
- **Alert budget** alpha: the share of ordinary agent-days allowed to alert.
- **Alert line** M_alpha = g(1 / (1 + 2 alpha)): q_final <= alpha exactly when M >= M_alpha. That
  gives x4.69 at 1%, x4.29 at 2.5% and x3.73 at 5%; x3 is alpha = 9.43%.
- The deployed alert stays M >= 3 (PS6), and the stated lines are reported beside it. An
  agent-day's M is the maximum over its calls.

### What can reach a line

Each row gives the smallest q/w at A = 89 and the largest M it allows.

| Path | Smallest q/w at A = 89 | Largest M | Reaches x3? |
|---|---|---|---|
| Cadence record, c_d down to 1/(R_d + 1) | about 0 | x5 | yes |
| Cadence, not a record (D_d >= 1) | 36/90 = 0.40 | x1.20 | no |
| Burst or Sweep record | about 0 | x5 | yes |
| Burst or Sweep, not a record | 30/90 = 0.33 | x1.38 | no |
| Unsafe sequence (c = 1) | 15/90 = 0.167 | x2.24 | no |
| Typical Footprint | 12/90 = 0.133 (0.8 at A = 14) | x2.54 (x0.92) | no |
| Oversized request (N_org about 6,000) | about 0.0025 | x4.9 | yes |
| Missing handshake (5-7% of agent-days, RF5) | about 0.9 | x0.9 | no |
| Alert floor / watch floor | 0.01 / 0.125 | x4.69 / x2.63 | yes / no |

So an alert comes from only three sources:

- a Cadence, Burst or Sweep record that also ranks high among the organisation's records;
- an oversized request that is rare across the organisation;
- the alert floor.

Typical Footprint and Unsafe sequence still order the review list (s2 and d*) and still feed
R = R_static x M below the line. They cannot alert alone. This is stated on purpose: in v4, Tool
and Asset novelty were the largest sources of benign alerts (Tool 28-44% of them at alpha 5%).

## 2. The guarantee

### Paper sentence

> Each dimension's score is turned into a daily rate: how often, in the caller's last 90 days, he
> was at least this strange. The call keeps the smallest rate divided by that dimension's budget
> share. On a day like his past days, the multiplier reaches the alert line for budget alpha with
> probability at most alpha, plus how often the first-access floor fires, however the dimensions
> depend on one another.

### Statement and proof sketch

**Proposition.** Take a warm agent-day (u, t) with A <= 89 and a level alpha < 2/15 (13.3%,
which includes x3's 9.43%). Then, under A1-A4 below:

P(M_day >= M_alpha) <= alpha (6/18 + 2/15) + alpha (1/15) + alpha (1/15) + r_floor(u) =
0.6 alpha + r_floor(u).

The terms are, in order:

- the Cadence, Burst and Sweep records (A1, A2);
- Oversized request (A3);
- Missing handshake, legacy era only (A3);
- the alert floor's realised rate (A4).

1. **Caps.** When q <= alpha < 2/15, only the paths marked "yes" in the table above can fire:
   every other path has q/w >= 2/15.
2. **Record path for d.** An alert through d needs two things: today's day maximum of d is a
   strict record over his A past day maxima, and c_d <= w_d alpha (A + 1).
   - Under A1, P(strict record) <= 1/(A + 1).
   - Under A2, P(c_d <= x | record) <= x for x <= 1. Here x <= (1/15)(2/15)(90) = 0.8.
   - So the term is at most w_d alpha.
3. **Organisation flags.** These use the add-one conformal rank of his agent-day maximum of rho
   among the organisation's agent-days. That gives at most w_d alpha, as an average over callers.
4. **Union bound** over dimensions. Nothing is assumed about how dimensions or calls depend on
   each other. The floor adds its own rate.

Every event above concerns a day maximum, so the statement is per agent-day with no volume term.

- The conformal step is Bates et al. 2023, eq. 3 and Prop. 1, as quoted in note 04 section 5.1.
  I did not open the paper, so this is UNVERIFIED by me.
- Part B's call-count form gives the same record sets, so the same alerts. Its sub-line ranks
  carry today's volume, so its bound held only in expectation (judges 1 and 3).

### Assumptions and scope

- **A1.** His day maxima of each record dimension, as scored at the time, are exchangeable over
  his A past active days and today. The scores are themselves learned daily from his history: v4
  baselines mature as A grows. So this is exchangeability of score values, not of raw behaviour,
  and the paper must not say "distribution-free".
- **A2.** Given a record, its strength is exchangeable with the records the organisation's callers
  set on that dimension in the window.
  - This is biased by tenure: a record at A = 89 is a maximum over 90 days, one at A = 15 a maximum
    over 16.
  - Splitting the reference by tenure (arm S6) did not help, so it stays a per-band diagnostic.
- **A3.** For the org-priced flags, his agent-day is exchangeable with the organisation's
  agent-days in the window. That term is an organisation average, not a per-caller bound.
- **A4.** The alert floor is policy, outside the statistic. Its cost is its realised rate, counted
  by RF5. On these worlds the floor's rule rate was 0.04-0.32% of the organisation's agent-days.
- **Not covered:**
  - change days, which are not exchangeable by definition;
  - adaptive callers;
  - a switch of protocol era (keep the pools per era, E3);
  - the weekly cycle: there is no weekend stratum, but the split is measured below;
  - per-call rates: R is per call, and all calls of one day share one bound.
- **Zimek et al. 2014** (quoted in note 04 section 2.2) prefer the average. They allow the max
  for "multiview" outliers, and when a miss costs much more than a false alarm. v5 normalises
  first, as their p. 17 asks: the max is over calibrated, share-weighted rates, with each
  dimension one view. The cost-asymmetry exception is used only for the alert floor (RF8, C11).

### Stated against realised (DEVELOPMENT WORLD, calibration stage on v4 scores, arm S5)

This table checks only ordinary days and group spend. Per-dimension spend overran its share at
x3: Repetition spent 0.728 / 0.845 / 0.632% against 0.524% (R2-1;
`org_record_rank_probe.py` reproduces it). Spec revision 2 §2.6 has the per-dimension check.

The evaluator's unfitted lines are cross-checked by the probe's spend diagnostic. Each cell is
main_seed7 / main_seed11 / heavy_files_seed21, as % of agent-days.

| Line | Bound 0.6 alpha | Ordinary, days 90-134 | Ordinary, days 135-180 | Change, days 90-180 | All benign, days 90-180 | Cadence spend, days 90-134 (share alpha/3) | Red Flags spend, days 90-134 (share alpha/3) | Footprint | Alert floor |
|---|---|---|---|---|---|---|---|---|---|
| 1% (x4.69) | 0.6 | 0.29 / 0.20 / 0.27 | 0.00 / 0.08 / 0.00 | 2.48 / 1.28 / 1.48 | 0.70 / 0.39 / 0.52 | 0.17 / 0.17 / 0.20 | 0.06 / 0.03 / 0.07 | 0 | 0.06 / 0 / 0 |
| 2.5% (x4.29) | 1.5 | 0.73 / 0.67 / 0.53 | 0.32 / 0.16 / 0.17 | 3.86 / 4.07 / 2.81 | 1.32 / 1.20 / 1.06 | 0.55 / 0.50 / 0.40 | 0.12 / 0.17 / 0.13 | 0 | 0.06 / 0 / 0 |
| 5% (x3.73) | 3.0 | 1.60 / 1.49 / 1.33 | 0.68 / 0.49 / 0.73 | 5.32 / 6.33 / 4.70 | 2.13 / 2.13 / 2.08 | 1.25 / 1.08 / 1.00 | 0.29 / 0.41 / 0.33 | 0 | 0.06 / 0 / 0 |
| x3 (9.43%) | 5.7 | 3.29 / 2.85 / 2.30 | 1.43 / 1.35 / 1.62 | 7.41 / 8.64 / 6.48 | 3.55 / 3.50 / 3.25 | 2.62 / 2.16 / 1.96 | 0.61 / 0.73 / 0.33 | 0 | 0.06 / 0 / 0 |

- **Ordinary days** are below 0.6 alpha at every line. **Every group** spends less than its third.
- **Change days** exceed the stated level at 1-2.5%. This is expected: they are outside A1.
- **Weekday / weekend**, ordinary days 90-180 at the 5% line: 0.88 / 1.53, 0.81 / 1.23 and
  1.11 / 0.82%. Weekends run hotter in the main worlds but stay below the stated level. There are
  2,433-2,691 weekend days per world.
- **Per caller** at the 5% line (140 / 141 / 138 callers with at least 30 ordinary days): median
  0%, 90th percentile 3.7 / 3.1 / 3.6%, maximum 7.1 / 5.9 / 7.1%. No caller is above 10%.

## 3. Small histories

- **Warm-up: unchanged.** Until his fifth tool call and the end of his first day, no history
  dimension takes part (engine.py:288-290). The rules still run (engine.py:427).
  - The alert floor applies from his first call.
  - Oversized request is priced against the organisation.
  - A Burst or Sweep at A = 0 is a record, ranked against the organisation's records.
- **A < 15.** Cadence alerts only through a record that ranks in the organisation's record tail.
  Footprint is capped at x0.92 at A = 14, so a newcomer's honest novelty gets the benefit of the
  doubt. The alert floor and Oversized request still protect the server.
- **Measured (development world, alpha 2.5%, ties by s2).**
  - Benign rate on A < 15 days: 2.33 / 0.00 / 0.00%, against v4's 9.30 / 2.78 / 27.50%. These
    are 43 / 36 / 40 days, so no interval supports a claim.
  - Newcomer rate at a matched benign rate of 2%: v5 2.3 / 0.0 / 0.0%; v4 7.0 / 2.8 / 10.0%; org
    calibration 14.0 / 16.7 / 10.0%.
  - The one A < 15 gray episode (main_seed11) is caught by both v4 and v5.
  - Band 15 <= A < 45: v5 benign 2.42 / 0.56 / 0.00% and gray 2/3, 2/5, 2/2. v4: 2/3, 3/5, 2/2,
    so v5 loses one episode.
- **Interfaces with other areas.**
  - With B4 (role prior), Footprint keeps q_d >= 1/(A + 1) after the prior. This preserves the
    cap and the guarantee. Running without the clamp is an ablation.
  - With B5 (minimum history), A counts the stretched window.
  - With RF11, k_d counts days only once the caller is established.
- **Not adopted:**
  - personal day calibration's newcomer pool: it needs a role label (Message has none,
    engine.py:151-164), and it judges a rotating Sybil leniently;
  - an organisation-wide pool: newcomers alerted on 10-17% of days.
- **Dormant return.** B5 keeps his window. His Cadence records rank against the organisation's
  records as usual.

## 4. Poisoning and drift

**His own history.**

- **Rehearsal.** One earlier day at least as strong on dimension d switches that dimension's
  record path off for the rest of the window (D_d = 1 gives q/w >= 0.4, x1.20).
  - The rehearsal day was itself a record, so it alerts if it ranks in the organisation's record
    tail. Rehearsing costs about one alert per dimension per 90 days.
  - Judge 2 estimated many alerts for v4, about 4 for personal day calibration and about 1 for this
    arm. That is an inference, UNVERIFIED by measurement.
  - Counting in days does not change this: the share division, not the unit, sets the 0.4.
- **Slow climb.** A slow climb never sets a strong record. scope_creep is still caught 7 times in
  14 at alpha 2.5%, the best of all arms, because Breadth and Session duration records still
  occur.
- **Option H1, alert hold** (default off; an arm). A day that alerted on d stays out of his D_d
  for 30 days, so repeating the act keeps alerting. The bound loosens by K_d/(A + 1) per
  dimension, the analogue of personal day calibration's G5.
- B6's daily cap applies to the Footprint counts unchanged.

**Organisation references** (the record-rank reference and the oversized pool).

- A few strong record-days can move a dimension's tail. Org calibration measured about 10
  agent-days for its 60-day pools. The record reference is smaller, so it is at least as exposed;
  its size is UNVERIFIED. Each identity already adds at most one record-day per dimension per
  day.
- **S7** (established callers only, A >= 20) was measured:
  - benign alerts change by -0.02 to -0.15 points at x3 and at the stated 5% line;
  - 0-2 fewer gray episodes are caught at the stated 5% line;
  - the fitted 5% point is unstable: 3.62 / 4.70 / 5.48% ordinary.
- **H2** (leave the top identity out, the RF1 trick) is not measured. Both are pre-freeze
  candidates.

**Floors.** Fixed prices give an attacker nothing to poison. Under rule-rate pricing (arm S2), one
identity raising a rule every day could push its price up a ladder step for everyone.

**Org discount.** Unchanged: RF7 applies inside Footprint.

**Drift.**

- At the 5% line, ordinary days run 1.33-1.60% in days 90-134 against 0.49-0.73% in days 135-180.
  This is the simulator ramp: every agent starts on day 0. Report the realised rate per 30-day
  period, as RF5 does, and evaluate on randomised calendars (EV-06).
- The window is a fixed 89 days. Barber et al. 2023's weighted conformal is untested.
- **Protocol era.** In the MCP 2026-07-28 era, Missing handshake's share is simply unspent; the
  task brief says SEP-2575 removes initialize (I did not open it). Arm S4 drops the dimension.
  Nothing changes at any unfitted line or at the fitted 1% and 2.5% points; the fitted 5%
  point moves by at most 0.11 points.

## 5. Engine state, config and selectability

**Selectability.**

- Add V5 to DESIGNS (engine.py:81). BehaviourConfig.design stays V4 (engine.py:114) until the
  freeze.
- Set `self.v4 = design in (V4, V5)` (engine.py:275), so v5 shares v4's scoring path.
- The calibration step runs after the scores dict (engine.py:294-299). The v1-v4 verdicts stay
  byte-identical, checked by a golden test.

**Inputs v5 must expose** as verdict fields, without changing v4's scores:

- the Asset score without the floor;
- the org-discounted score before its cap;
- the over-limit magnitudes: minute count / limit, distinct assets per hour / limit, and size /
  RF1 line.

**New state.** It lives in a new module, `behaviour/calibration.py`. Snapshot and restore add new
keys, read with `.get` as restore already does (engine.py:619-640).

- **Per caller:**
  - one ring of 89 day maxima, plus today's running maximum, for each of the 8 record dimensions
    (6 Cadence, Burst, Sweep); about 6 KB;
  - k_d from the existing rule_days (engine.py:233);
  - Footprint unchanged (memory.py:89-101).
- **Per route (organisation):**
  - for each record dimension, 89 daily sorted arrays of record-day strengths, one value per
    caller per day;
  - for Oversized request and Missing handshake, 89 daily arrays of agent-day maxima of rho, plus
    the count of active agent-days.
  - Revision 1 said both are folded at "the existing once-a-day learning point". There is no such
    point: per-caller structures fold lazily on the caller's next call (R3-3). Revision 2 adds a
    route clock with a fold sweep (spec CAL-7). The size estimate is about 1 MB for 150 callers.
- **Per call:** one binary search per dimension.
- **No role label is needed.**
- **Verdict (v5 only):**
  - `rate` (q_final), `rates` (q_d), `runner_up_rate` (q2);
  - `records` (the dimensions at a record);
  - `floors` (RF8);
  - the reason with its group.
  - The gateway logs `behaviour_rate`, so the realised-against-stated tables can be recomputed
    offline.

**Config fields:**

| Field | Default | Meaning |
|---|---|---|
| `design` | `"v4"` | `"v5"` selects this design; v1-v4 unchanged |
| `budget_shares` | (1/3, 1/3, 1/3) | per group, split equally inside the group |
| `record_rank` | True | the record rank on Cadence, Burst and Sweep |
| `record_min_reference` | 19 | below this many record-days, c_d = 1 |
| `cadence_units` | `"days"` | `"calls"` reproduces Part B (arms S0-S4) |
| `score_bins` | 4096 | ties count as "at least" |
| `alert_floor_rate` | 0.01 | q of a sensitivity-5 first access |
| `watch_floor_rate` | 0.125 | q of a sensitivity-4 first access (v4's 0.8) |
| `floor_pricing` | `"fixed"` | `"rule_rate"` = the frozen ladder (ablation S1, S2) |
| `alert_line` | 3.0 | RF8's field; the stated lines are derived from it |
| `record_reference` | `"all"` | `"established"` (S7) or `"band"` (S6) |
| `leave_top_identity_out` | False | H2 |
| `alert_hold_days` | None | H1 |

The window is the existing `history_days = 90` (engine.py:115): 89 past days plus today.

## 6. Evidence (DEVELOPMENT WORLD, shared evaluator)

Everything comes from `calib_eval.evaluate`. The v4 rows are `ce.v4_reference`; they equal the
Part B runs that checked against the validation files with 0 mismatches.

- The report window is days 135-180.
- Thresholds are fitted on ordinary agent-days of days 90-134.
- "tb" means ties broken by s2.
- Each cell is main_seed7 / main_seed11 / heavy_files_seed21, with 43 / 41 / 46 gray episodes.
- v5 is arm S5. The runner-up rows are copied from the Part B proposals.

### E1. Operating points

| Arm | Point | Ordinary % | Change % | All benign % | Gray caught | Credited precision % |
|---|---|---|---|---|---|---|
| v4 | alpha 1% tb | 1.11 / 0.80 / 1.45 | 4.07 / 3.93 / 5.83 | 1.77 / 1.41 / 2.53 | 21, 15, 34 | 19.6 / 18.1 / 22.1 |
| v4 | alpha 2.5% tb | 2.51 / 2.00 / 3.83 | 8.14 / 5.67 / 13.21 | 3.76 / 2.71 / 6.14 | 24, 19, 35 | 11.2 / 12.7 / 10.7 |
| v4 | alpha 5% tb | 6.54 / 6.13 / 6.91 | 14.68 / 16.58 / 16.55 | 8.35 / 8.14 / 9.28 | 25, 23, 38 | 5.6 / 5.0 / 8.1 |
| v4 | x3 | 2.76 / 2.80 / 1.98 | 8.90 / 9.27 / 8.23 | 4.12 / 4.05 / 3.52 | 24, 22, 35 | 10.4 / 9.7 / 16.8 |
| **v5** | alpha 1% tb | 0.54 / 0.26 / 0.53 | 0.85 / 0.65 / 0.77 | 0.61 / 0.34 / 0.59 | 20, 20, 29 | 33.3 / 52.8 / 49.1 |
| **v5** | alpha 2.5% tb | 1.05 / 1.01 / 1.71 | 1.52 / 1.53 / 2.14 | 1.16 / 1.11 / 1.81 | 26, 23, 33 | 25.0 / 25.3 / 25.4 |
| **v5** | alpha 5% tb | 3.84 / 4.08 / 4.28 | 4.73 / 5.13 / 6.52 | 4.04 / 4.28 / 4.83 | 28, 25, 35 | 9.7 / 8.5 / 12.9 |
| **v5** | stated 1% (x4.69) | 0.00 / 0.08 / 0.00 | 0.38 / 0.00 / 0.09 | 0.08 / 0.06 / 0.02 | 16, 16, 24 | 75.0 / 84.2 / 96.0 |
| **v5** | stated 5% (x3.73) | 0.68 / 0.49 / 0.73 | 1.04 / 1.09 / 1.37 | 0.76 / 0.61 / 0.89 | 24, 20, 32 | 33.3 / 39.2 / 43.2 |
| **v5** | x3 (9.43%) | 1.43 / 1.35 / 1.62 | 2.18 / 1.74 / 2.14 | 1.60 / 1.43 / 1.75 | 27, 23, 33 | 22.6 / 23.4 / 28.6 |
| Budget shares, base (S0) | alpha 1% tb | 0.54 / 0.23 / 0.50 | 0.76 / 0.65 / 0.86 | 0.59 / 0.31 / 0.59 | 16, 15, 20 | 28.3 / 40.0 / 39.6 |
| Budget shares, base (S0) | x3 | 1.41 / 1.32 / 1.65 | 2.27 / 1.96 / 2.23 | 1.60 / 1.45 / 1.79 | 27, 23, 33 | 22.6 / 21.1 / 28.1 |
| Personal day calibration | alpha 1% tb | 0.70 / 0.78 / 0.87 | 2.37 / 2.40 / 3.00 | 1.07 / 1.09 / 1.39 | 18, 13, 29 | 26.1 / 19.7 / 30.5 |
| Personal day calibration | alpha 2.5% tb | 2.03 / 1.48 / 1.87 | 6.63 / 4.36 / 6.60 | 3.05 / 2.03 / 3.04 | 20, 17, 33 | 12.0 / 13.7 / 18.6 |
| Personal day calibration | alpha 5% tb | 4.62 / 4.34 / 5.14 | 11.55 / 12.21 / 12.09 | 6.16 / 5.85 / 6.85 | 23, 22, 35 | 6.9 / 6.6 / 9.7 |
| Org calibration (pool frozen at day 134) | alpha 1% | 0.62 / 0.36 / 0.48 | - | 1.51 / 1.22 / 1.43 | 22, 16, 31 | 22.3 / 20.3 / 31.3 |
| Org calibration | alpha 2.5% | 1.43 / 1.27 / 1.79 | - | 2.75 / 2.37 / 3.27 | 25, 23, 35 | 14.0 / 15.3 / 18.4 |
| Org calibration | alpha 5% | 4.19 / 3.74 / 4.31 | - | 5.61 / 5.22 / 6.03 | 28, 24, 36 | 8.6 / 8.0 / 11.4 |
| Three-group calibration | alpha 1% | 0.19 / 0.16 / 0.06 | - | 0.40 / 0.36 / 0.23 | 4, 2, 3 | 17.4 / 10.5 / 21.4 |
| Three-group calibration | alpha 5% | 1.76 / 1.43 / 2.54 | - | 2.54 / 2.18 / 3.58 | 21, 17, 35 | 12.5 / 11.4 / 16.6 |

Pooled gray recall with Wilson 95% intervals (130 episodes; the pooling ignores world
clustering, which EV-18 adds):

| Point | v4 | v5 |
|---|---|---|
| alpha 1% tb | 70 [45, 62] | 69 [45, 61] |
| alpha 2.5% tb | 78 [51, 68] | 82 [55, 71] |
| alpha 5% tb | 86 [58, 74] | 88 [59, 75] |
| x3 | 81 [54, 70] | 83 [55, 72] |

### E2. Matched benign rate

The threshold is set after the fact on the report window's benign agent-days, using judge 2's
method. It is reproduced in `calib_v5_synthesis.matched` and gives the same v4 numbers.

| Arm | Gray at 1% benign | at 2% | at 3% | Change-day rate at 2% | Newcomer rate at 2% | Top 5% of callers' share of alerts at 2% |
|---|---|---|---|---|---|---|
| v4 | 19/13/18 = 50 [31, 47] | 21/17/28 = 66 [42, 59] | 24/21/35 = 80 [53, 69] | 4.4 / 4.8 / 4.7 | 7.0 / 2.8 / 10.0 | 24 / 38 / 31 |
| **v5** | 26/22/32 = **80** [53, 69] | 27/23/33 = **83** [55, 72] | 28/25/35 = **88** [59, 75] | 2.3 / 2.5 / 2.4 | 2.3 / 0.0 / 0.0 | 28 / 21 / 22 |
| Budget shares, base (S0) | 26/22/23 = 71 | 27/23/33 = 83 | 28/23/35 = 86 | 2.5 / 2.5 / 2.4 | 2.3 / 0.0 / 0.0 | 27 / 20 / 22 |
| Personal day calibration | 14/13/29 = 56 | 18/17/31 = 66 | 19/19/33 = 71 | 4.5 / 4.4 / 4.4 | 0 / 0 / 0 | 22 / 28 / 28 |
| Org calibration | 17/16/22 = 55 | 24/18/33 = 75 | 25/23/34 = 82 | 5.1 / 6.7 / 5.8 | 14.0 / 16.7 / 10.0 | 29 / 44 / 43 |
| Three-group calibration | 8/9/15 = 32 | 17/16/24 = 57 | 21/19/27 = 67 | 4.2 / 5.0 / 3.8 | 2.3 / 0 / 5.0 | 25 / 22 / 22 |

### E3. Gray recall by kind, pooled over the three worlds

| Kind | Episodes | v4, 1% tb | v5, 1% tb | v4, 2.5% tb | v5, 2.5% tb |
|---|---|---|---|---|---|
| big_paste | 14 | 11 | **14** | 13 | **14** |
| bulk_export | 18 | 18 | 17 | 18 | 18 |
| cross_copy | 13 | 5 | 4 | 6 | 4 |
| mass_cleanup | 8 | 0 | **5** | 0 | **5** |
| off_hours_batch | 10 | **6** | 0 | **6** | 1 |
| overfetch | 18 | 0 | 1 | 0 | 1 |
| scope_creep | 14 | 1 | 1 | 2 | **7** |
| sensitive_peek | 16 | 11 | **14** | 14 | 14 |
| shadow_script | 9 | **8** | 3 | 9 | 8 |
| slow_loop / bot_loop | 8 / 2 | 8 / 2 | 8 / 2 | 8 / 2 | 8 / 2 |

The base arm S0 caught sensitive_peek 0 times in 16 at 1% tb. The alert floor is what restores it.

### E4. Review list, strata and reasons

**Credited recall of the review list** (days 90-180, 20 draws):

| Arm | k = 4 | k = 8 |
|---|---|---|
| v4 | 55.7 / 44.0 / 51.9 | 63.3 / 58.3 / 69.6 |
| **v5** | **63.3 / 64.3 / 72.2** | **67.1 / 67.9 / 77.2** |
| S0 | 59.5 / 58.3 / 65.8 | 63.3 / 63.1 / 75.9 |
| Personal day calibration | 51.9 / 50.0 / 64.6 | 62.0 / 59.5 / 70.9 |
| Org calibration | 55.7 / 59.5 / 65.8 | 69.6 / 70.2 / 77.2 |
| Three-group calibration | 50.6 / 46.4 / 49.4 | 60.8 / 63.1 / 65.8 |

A random list scores 4.4 / 3.5 / 3.7% (k = 4) and 8.8 / 6.9 / 7.4% (k = 8).

**Benign alert rate by stratum** at alpha 2.5% tb (people / bots / A < 15 / 15-44 / A >= 45):

- v4: 3.25 / 5.82 / 9.30 / 3.23 / 3.73; 1.75 / 6.56 / 2.78 / 2.25 / 2.72; 5.82 / 7.42 / 27.50 /
  4.62 / 5.97.
- v5: 1.34 / 0.42 / 2.33 / 2.42 / 1.11; 1.02 / 1.48 / 0.00 / 0.56 / 1.14; 1.97 / 1.17 / 0.00 /
  0.00 / 1.85.

**Benign alerts by reason d*** at alpha 2.5% tb, % of benign alerts:

| World | v4 | v5 |
|---|---|---|
| main_seed7 | n = 179: Oversized request 50, Asset 23, Tool 13 | n = 55: Oversized request 35, Repetition 24, Write rate 13, Breadth 13 |
| main_seed11 | n = 129: Oversized request 75, Asset 22 | n = 53: Oversized request 34, Repetition 21, Write rate 17, Session duration 11 |
| heavy_files_seed21 | n = 291: Tool 36, Oversized request 24, Asset 19 | n = 86: Oversized request 26, Repetition 24, Write rate 15, Session duration 15 |

### E5. Arms measured in this synthesis

Probe: calib_v5_synthesis.py.

| Arm | 1% tb: ordinary %; gray | 5% tb: ordinary %; gray | Stated 1%: gray | Stated 5%: benign %; gray | x3: benign %; gray | List k = 4; k = 8 | Matched gray at 1 / 2 / 3% |
|---|---|---|---|---|---|---|---|
| v4 | 1.11 / 0.80 / 1.45; 21, 15, 34 | 6.54 / 6.13 / 6.91; 25, 23, 38 | - | - | 4.12 / 4.05 / 3.52; 24, 22, 35 | 55.7 / 44.0 / 51.9; 63.3 / 58.3 / 69.6 | 50 / 66 / 80 |
| S0 base (Part B, reproduced) | 0.54 / 0.23 / 0.50; 16, 15, 20 | 3.95 / 3.82 / 3.91; 28, 23, 35 | 10, 8, 14 | 0.78 / 0.63 / 0.91; 20, 15, 23 | 1.60 / 1.45 / 1.79; 27, 23, 33 | 59.5 / 58.3 / 65.8; 63.3 / 63.1 / 75.9 | 71 / 83 / 86 |
| S1 = S0 + floor at rule rate (ladder) | 0.54 / 0.23 / 0.50; 20, 20, 29 | 4.59 / 4.60 / 5.45; 27, 23, 33 | 16, 16, 24 | 0.82 / 0.63 / 0.91; 24, 20, 32 | 1.60 / 1.45 / 1.79; 27, 23, 33 | 64.6 / 65.5 / 72.2; 68.4 / 67.9 / 77.2 | 80 / 83 / 83 |
| S2 = S1 + RF1 line | 0.54 / 0.26 / 0.53; 20, 20, 29 | 4.65 / 4.93 / 6.04; 27, 23, 34 | 16, 16, 24 | 0.76 / 0.61 / 0.89; 24, 20, 32 | 1.60 / 1.43 / 1.75; 27, 23, 33 | 63.3 / 65.5 / 72.2; 68.4 / 67.9 / 75.9 | 80 / 83 / 83 |
| S3 = S2, floor at fixed prices | 0.54 / 0.26 / 0.53; 20, 20, 29 | 3.92 / 3.84 / 3.77; 28, 23, 35 | 16, 16, 24 | 0.76 / 0.61 / 0.89; 24, 20, 32 | 1.60 / 1.43 / 1.75; 27, 23, 33 | 62.0 / 63.1 / 70.9; 63.3 / 65.5 / 75.9 | 80 / 83 / 86 |
| S4 = S2, no Missing handshake | 0.54 / 0.26 / 0.53; 20, 20, 29 | 4.65 / 4.88 / 6.15; 27, 23, 34 | 16, 16, 24 | 0.76 / 0.61 / 0.89; 24, 20, 32 | 1.60 / 1.43 / 1.75; 27, 23, 33 | 63.3 / 65.5 / 72.2; 68.4 / 67.9 / 75.9 | 80 / 83 / 83 |
| **S5 = S3 + Cadence in days (v5)** | 0.54 / 0.26 / 0.53; 20, 20, 29 | 3.84 / 4.08 / 4.28; 28, 25, 35 | 16, 16, 24 | 0.76 / 0.61 / 0.89; 24, 20, 32 | 1.60 / 1.43 / 1.75; 27, 23, 33 | 63.3 / 64.3 / 72.2; 67.1 / 67.9 / 77.2 | 80 / 83 / 88 |
| S6 = S3, reference by tenure band | 0.62 / 0.47 / 0.78; 20, 20, 31 | 4.38 / 3.66 / 5.70; 29, 23, 34 | 14, 16, 24 | 0.69 / 0.63 / 0.84; 21, 20, 31 | 1.56 / 1.47 / 1.64; 27, 23, 33 | 62.0 / 63.1 / 69.6; 65.8 / 67.9 / 73.4 | 80 / 84 / 86 |
| S7 = S3, established-only reference | 0.62 / 0.31 / 0.59; 20, 20, 29 | 3.62 / 4.70 / 5.48; 27, 23, 35 | 15, 15, 24 | 0.69 / 0.59 / 0.86; 22, 20, 31 | 1.45 / 1.41 / 1.62; 26, 23, 33 | 60.8 / 63.1 / 70.9; 65.8 / 65.5 / 75.9 | 80 / 83 / 85 |

What the arms show:

- **The floor** (S0 to S1) is the largest single gain: +4 / +5 / +9 gray at a fitted 1%, at the
  same ordinary rate.
- **The RF1 line** (S1 to S2) changes little, because the org-priced grading already ranks by
  size.
- **Fixed against ladder prices** (S3 against S2):
  - fixed prices have fewer false alarms at a fitted 5% (3.77-3.92% against 4.65-6.04% ordinary);
  - they have fewer newcomer alerts at a matched 3% (2.3 / 8.3 / 5.0% against 14.0 / 16.7 /
    7.5%);
  - they lose 1.3-2.4 list points at k = 4.
- **Day units** (S3 to S5) leave every unfitted line identical, as the record argument predicts,
  and add 1.2-3.8 list points.

## 7. Why the other proposals lost, and the grafts taken

Judges' scores, out of 10:

| Proposal | Statistical rigour | Security value | Paper and engineering | Outcome |
|---|---|---|---|---|
| Daily rates with budget shares (per_dim_conformal_wbonf) | 5 | 7 (winner) | 8 (winner) | **base of v5** |
| Personal day calibration | 8 (winner) | 6 | 7 | runner-up; four grafts |
| Org calibration | 4 | 5 | 5 | lost |
| Three-group calibration | 6 | 3 | 4 | lost |

**Personal day calibration** has the tightest guarantee: one rank per day, with realised rates on
the diagonal from 1%. It lost for three reasons:

- Its detection at a matched budget is v4's: 56 / 66 / 71 against v5's 80 / 83 / 88. At the same
  fitted alpha it catches fewer gray episodes than v4.
- Its level ladder was picked after seeing the report window.
- Revision 1 also gave "pools keyed by role" and "7-8 new names" as reasons. They are dropped:
  v5 had planned a role field itself, and it adds names too (R4-11). Only measured reasons
  remain.

Rigour was its edge. v5 now covers the two rigour objections to the base arm: the record-path
proof and day units remove the volume term.

**Org calibration:**

- Its headline scored the report window with a pool frozen at day 134, which is not the
  deployable rule. The code is calib_org_normalised.py:47-49, as cited by judge 3; I did not
  re-read it.
- With a rolling pool, the stated bound was exceeded 1.34-1.9 times in days 90-134.
- Newcomers alert on 10-17% of days, and its false alarms are the most concentrated (the top 5%
  of callers hold 29-44% of alerts).
- Poisoning one dimension's tail takes about 10 agent-days.
- Revision 1's "it adds a 16th dimension" is dropped as a reason, since v5's D1 proposes one
  (R4-11).

**Three-group calibration:**

- It has the worst matched detection: 32 / 57 / 67.
- Its Red Flags look never fires at alpha <= 5% in the main worlds.
- Its 1.25x slack admitted a look that broke its own share.

**Grafts taken into v5:**

| Source | Graft | Status in v5 |
|---|---|---|
| Personal day calibration, RF8 | First-access floor outside the statistic, with its own reason; the statistic becomes the runner-up | adopted (S1); priced at fixed levels (S3), the ladder kept as an ablation |
| Personal day calibration | RF1 pooled-line re-implementation (`rf1_raised`, calib_personal_day.py:112-147; its sources are cited at lines 87-88) | adopted (S2), reused by calling `rf1_raised` |
| Personal day calibration, judge 3 | Reliability by day class and half, and the per-caller spread | adopted (section 2 table) |
| Personal day calibration | "Raising his own ceiling costs an alert" | adopted in section 4 |
| Judges 1 and 3 | A day-level bound with no conditional volume term; "exchangeable score values", not "distribution-free" | adopted (day units, A1 wording) |
| Judge 1 | Record pool split by tenure | measured (S6), not adopted, kept as a diagnostic |
| Judge 2 | Count habituation in days; report the rehearsal cost | adopted; the rehearsal cost goes to EV-25 |
| Judge 2, org calibration | Footprint novelty priced by its org rate | arm F1; it needs org value counts, which the vectors lack |
| Judges 2 and 3, org calibration | Leave the top identity out; established-only references | S7 measured; H2 is a pre-freeze candidate |
| Org calibration | Era split for Missing handshake | fixed shares, unspent in the modern era (S4: no effect) |
| Three-group calibration | Selection rule written first, on fit days only; each group's spend against its third | adopted for the pre-freeze candidates and the section 2 table |
| Judge 3 | Rename "v5-PDC" to "daily rates with budget shares"; floor at the strictest line | adopted |

Rejected grafts:

- the newcomer pool and record hold of personal day calibration (record hold returns as H1, an
  alert hold);
- Missing handshake as an alert floor: it fires on 5-7% of agent-days;
- stage 3, the personal or org day rank: it lost in Part B.

**Selection honesty.** Three choices in this synthesis were made on these development worlds:
fixed against ladder prices, day units, and leaving S6 and S7 out.

- Day units was argued before the run, as alert-neutral by construction. The run confirmed that.
- Fixed prices were argued from poisoning and from the ladder's post-hoc origin. The run also
  showed fewer false alarms at the fitted 5% point.

All three are frozen here.

## 8. Ablation arms this design implies

- **Measured now:** S0-S7 (E5).
- **Pre-freeze candidates.** These go in EV-16's candidate file. Each is decided on development
  worlds, days 90-134 only, by EV-16's rule: the fewest benign x3 alerts, list recall within 1
  point of v5's, and no gray kind with at least 20 episodes losing more than 10 points.
  - S7, established-only reference;
  - H1, 30-day alert hold;
  - H2, leave the top identity out in the record and oversized references;
  - F1, Footprint record rank by org value counts (needs the EV-03 score log);
  - RF6, the copy-out-of-sensitivity-5 alert floor;
  - B4 with and without the Footprint clamp.
- **Paper ablations** (held-out worlds; matched budgets with Holm, EV-20):
  - leave-one-dimension-out (15) and leave-one-group-out (3), exact because the shares are fixed;
  - record rank off;
  - floor at fixed prices, at v4 values and at the rule rate;
  - group against equal shares;
  - day against call units;
  - personal day calibration and org calibration as alternative calibrations;
  - the EV-20 combiner family (mean, soft-OR, top-2, Tippett, harmonic mean, Cauchy);
  - PS8.
- **Adaptive section** (EV-25): the rehearsal cost per arm, meaning the alerting days an adaptive
  caller pays before a new level stops alerting.

## 9. Names: what stays and what is new

- **Kept:**
  - Typical Cadence, Typical Footprint and Red Flags, with all 15 dimension names;
  - top score s1, runner-up s2, reason d*;
  - habit discount (now the flag's own daily rate);
  - org discount (a daily rate of at least 1/2);
  - first-access floor (an alert floor at sensitivity 5, a watch floor at sensitivity 4, the RF8
    names);
  - warm-up; M in [0.7, 5], or [1, 5] under PS8.
- **Same form:** s1 = 1/(1 + 2q) is v4's Footprint form s = 1/(1 + 2e) (memory.py:89-101), so the
  paper's "score to multiplier" table is unchanged. d* is now "the dimension whose rate, divided by
  its share, is smallest".

New names, one sentence each:

| Name | Definition |
|---|---|
| daily rate | How often per active day, in his last 90 days, he did something at least this strange, counting today once. |
| budget share | The part of the alert budget one dimension may spend: each group a third, split equally inside it. |
| record rank | When a call is stranger than anything in his own 90 days, how it ranks among the records the organisation's callers set in the same 90 days. |
| alert budget | The share of ordinary agent-days allowed to alert. |
| alert line | The multiplier that bounds (under the stated assumptions; it does not "guarantee") the share of agent-days that alert: x4.69 at 1%, x4.29 at 2.5%, x3.73 at 5%, and x3 at 9.43%. Revision 2 drops "alert budget" as a name and deploys the 1% line. |

The design's short name is "budget shares". In BehaviourConfig it is `design = "v5"`.

## 10. Open items

Revision 2 of the spec resolves or replaces every item below. The list is kept as the revision 1
record.

- **Freeze before held-out worlds:** the shares, the floor prices (0.01 and 1/8), the RF1
  constants, the bins, `record_min_reference = 19` and the day units. Hash them with EV-15.
- **Re-run on vectors from the final v5 engine** (EV-03). The other areas change s_d.
- **Kinds that stay weak:**
  - off_hours_batch: Hour of day ranks his logged score, so it discounts callers who sometimes
    work odd hours. Part B's hour-gap option failed its rule.
  - cross_copy: a rare tool falls to x1.8-2.1.
  - overfetch: needs AI-8.
- **"Established" is defined two ways.** B4 and B5 use 20 active days and 14 days. RF7 and RF11
  use 14 days and 5 calls. The record reference needs one definition.
- **Minimum organisation size.** Oversized request reaches the 1% line only when N_org + 1 >= 1,500
  agent-days in the window. Smaller routes fail quietly.

## Files and reproduction

- **Probe:**
  [probes/calib_v5_synthesis.py](probes/calib_v5_synthesis.py).
  - numpy only, one process, about 80 s per world for 8 arms; ruff clean.
  - It imports calib_per_dim_conformal.py (stages 1-2: lines 122-131, 134-156, 293-356, 418-465),
    calib_personal_day.py (`rf1_raised`, lines 86-147; `LADDER`, line 65) and calib_eval.py. The
    probe is 329 lines.
- **Run:** `python3 reports/experiments/dynamic_dimensions/knowledge_base/probes/calib_v5_synthesis.py <npz> ... --out <dir>`
- **Outputs, in this session's scratchpad (not the repo):**
  - `/tmp/claude-343913582/-home-ovadyat-MCP/d6821e4d-e280-4911-be08-63b780ec3aaa/scratchpad/v5syn/v5syn_<world>.json`
  - `/tmp/claude-343913582/-home-ovadyat-MCP/d6821e4d-e280-4911-be08-63b780ec3aaa/scratchpad/v5syn/tables.md`,
    formatted only by `fmt.py` in the same folder.
- **Part B and judge outputs:** the `pdc/`, `orgnorm/` and `gc_full/` folders and
  `judge2_matched.json` in the same scratchpad.

## References

- Knowledge base:
  - [04 score aggregation and calibration](04-score-aggregation-and-calibration.md): sections 2.2,
    5.1, 6.1-6.4 and 8;
  - [06 threat model and evasion](06-threat-model-and-evasion.md);
  - [07 evaluation methodology](07-evaluation-methodology.md);
  - [review-assessment](review-assessment.md): C3, C4, C9, C11;
  - [improvement-options](improvement-options.md): c1, c2;
  - [DIMENSION_FORMULAS.md](../DIMENSION_FORMULAS.md), section "Names".
- Part A areas: RF1, RF5, RF6, RF7, RF8, RF11; B1, B4, B5, B6, B9; E3-E6; AI-2, AI-8; PS6, PS8;
  EV-03, EV-06, EV-15, EV-16, EV-18, EV-20, EV-25.
- Code read for this note:
  - engine.py:74-81, 106, 111-118, 151-176, 184-188, 233, 275, 286-299, 427-437, 489, 504-515,
    611-640;
  - memory.py:17-19, 79-101;
  - calib_eval.py:50-52, 115-146.
- R. F. Barber, E. J. Candès, A. Ramdas, R. J. Tibshirani. Conformal prediction beyond
  exchangeability. *Annals of Statistics* 51(2):816-845, 2023. Via note 04; not opened by me.
- S. Bates, E. Candès, L. Lei, Y. Romano, M. Sesia. Testing for outliers with conformal p-values.
  *Annals of Statistics* 51(1):149-178, 2023. Via note 04 section 5.1; UNVERIFIED by me.
- H.-P. Kriegel, P. Kröger, E. Schubert, A. Zimek. Interpreting and unifying outlier scores.
  *SIAM SDM* 2011, 13-24. Via note 04.
- A. Zimek, R. J. G. B. Campello, J. Sander. Ensembles for unsupervised outlier detection.
  *ACM SIGKDD Explorations* 15(1):11-22, 2014. Quoted from note 04 section 2.2.
- Model Context Protocol specification 2026-07-28: SEP-2567 (sessions removed) and SEP-2575
  (initialize removed). These come from the task brief, which says they were re-verified on
  primary sources. I did not open them.
