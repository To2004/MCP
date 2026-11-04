# The behaviour multiplier M: one formula

> **Superseded in part (2026-10-29).** Its derivation, guarantee and judges' review still apply.
> Its dimension list and day-based form are replaced by [dynamic-score-report.md](dynamic-score-report.md).

This note defines the dynamic layer's behaviour multiplier M with one formula, and states every
choice behind it. It derives the formula's form from stated requirements and gives the false-alarm
bound with its conditions. It also lists the threats and experiments a paper needs. It is a
proposal to replace §2.3-2.5 of [v5-design-spec.md](v5-design-spec.md); it is not yet adopted.

- **Revision 2 (2026-10-28).** It follows a review by four independent judges (§13). Revision 1
  overclaimed uniqueness, the meaning of 5, the "unchosen" bottom and the guarantee; those points
  are corrected here.
- **Numbers.** Every number is printed by
  [probes/m_formula_numbers.py](probes/m_formula_numbers.py), except where a line says it comes from
  a judge's simulation. The numbers are exact arithmetic or synthetic Monte Carlo. **None is a
  result on a world or on real traffic** (§10).

## 1. The formula

The MCP server is the protected asset and the calling agent is the threat. M says how unusual a
call is **for the agent that makes it**, and multiplies the call's static risk.

```text
A   = the agent's active days in its window: its last H = 90 active days, so A ≤ 90
D   = how many of those days were at least as unusual as this call            (§2)

M   = ( (A + 1) / (2D + 1) ) ^ γ          γ = ln 5 / ln(H + 1) ≈ 0.357
R   = R_static × M                        R_static ∈ [1, 5], so R ∈ [0.78, 25]
```

**On one dimension:**

| What the agent is doing | (A+1)/(2D+1) | M |
|---|---|---|
| New agent, no history (A = 0) | 1 | ×1 |
| Something it does on half its days (D = 45) | 1 | ×1 |
| Less unusual than every past day (D = 90) | 0.50 | ×0.78 |
| Never in its last 90 active days (D = 0) | 91 | ×5 |

**On a whole call with 8 dimensions,** the same formula is used with D counted for the whole call.
A call that is new on one dimension and ordinary on the others then typically gets **×2.5, not ×5**.
An ordinary agent sets a new record on some dimension about one day in 12, so one record is worth
less than it is on one dimension alone (§5.3).

No parameter is fitted to data. The choices are listed in §4.

## 2. Inputs and what "at least as unusual" means

**Identity.** The only identity is an agent id.
- **Assumption:** the operator issues the id, and a client cannot choose or forge it. Sybil
  identities are out of scope (Douceur 2002).
- One id may stand for a whole organisation. Then "the agent's days" are the organisation's days,
  and the formula does not change.
- Calls without an id share one key.
- There is no sign-in, no network address and no user id.

**Dimensions.** There are eight, of two kinds.

| Kind | Dimension | More unusual means |
|---|---|---|
| Quantity | Call rate: calls in the last hour | more |
| Quantity | Write rate: writes in the last hour | more |
| Quantity | Breadth: distinct assets touched in the last hour | more |
| Quantity | Repetition: the same (tool, asset) call within 10 minutes | more |
| Quantity | Read volume: bytes returned in the last hour | more |
| Category | Tool | used on fewer of the window's days |
| Category | Asset | used on fewer of the window's days |
| Category | Hour of day | active at that hour on fewer of the window's days |

Removed from v5:
- Network and Client, because there is no address and no client name.
- Session duration, because an organisation-wide id rarely idles for 30 minutes.
- The five Red Flags, because they need limits or required steps from a policy file.

**One dimension.** A past day is represented by its peak on that dimension:
- for a quantity, its largest amount;
- for a category, its rarest category.

n_d is the number of past days whose peak on d was at least as unusual as this call. Ties count as
"at least as unusual".

**The whole call (the rarest-dimension rank).** In one sentence for the paper:

> Because every ordinary day looks rare on some dimension, we compare the call's rarest dimension,
> measured in days, with each past day's rarest dimension, not with that dimension's own history.

Precisely:
1. A call's profile is its n_d values sorted from smallest (most unusual) to largest.
2. Each past day has a profile, computed in the same way against the other days.
3. D is the number of past days whose profile is at least as unusual. Profiles are compared on the
   rarest entry first, then the next one (lexicographic order).

For the exact guarantee, all counts are recomputed leaving the day itself out, over the same A + 1
days, today included (§5.2). That costs about 91 × 8 ranks per call.

## 3. Why this form

Write f = (D + ½)/(A + 1) for the call's smoothed frequency: how often the agent does something
at least this unusual. Then (A + 1)/(2D + 1) = 1/(2f).

**Assumption (0).** M depends on the history only through f, and is non-increasing in f.

- **(i) Ordinary is neutral.** A behaviour seen on half the agent's days (D = A/2) gives M = 1, for
  every A including A = 0. This fixes the ½ in f: it is the only offset with this property, and it
  is the mid-p correction (Lancaster 1961).
- **(ii) Scale invariance.** Making a behaviour c times rarer multiplies M by a factor that depends
  only on c. On (0, 1), the monotone solutions are powers, M = κ · f^(−γ) (a Pexider form of
  Cauchy's equation; Aczél 1966).
  - The same power family turns p-values into evidence in the e-value literature (Shafer et al.
    2011; Vovk and Wang 2021).
  - In words, log M is affine in the surprisal log(1/f), and each halving of the frequency
    multiplies M by 2^γ, which is ×1.28 at H = 90.
  - M is anchored at the median, not the mean, so it is not an e-value: its mean on ordinary days
    is about 1.2.
- **(iii) Behaviour and the static score weigh equally.** The top is chosen so that M spans the
  same range as R_static on a log scale, ln 5. In log R = log R_static + log M, neither layer can
  outweigh the other. The most unusual thing a full window can show (A = H, D = 0) therefore gives
  M = 5.

(ii) gives M = κ f^(−γ). (i) gives κ = 2^(−γ). (iii) gives (H + 1)^γ = 5, so γ = ln 5 / ln(H + 1).

**Uniqueness.** Under (0), the formula is the only monotone, scale-invariant function of f that
meets (i)-(iii). On the finite set of frequencies that 90 days can produce, other monotone functions
also meet (i)-(iii), but they differ from this one by less than 2 × 10⁻⁴.

**The bottom follows from the ½.** With offset τ in f = (D + τ)/(A + 1), the bottom is
(τ(H + 1)/(H + τ))^γ:

| Offset τ | Bottom of M | Neutral at the median, (i)? |
|---|---|---|
| 1 (plain conformal p) | ×1.00 | no: the median gets ×1.28 |
| **½ (mid-p)** | **×0.78** | **yes** |
| 0.365 | ×0.70 | no |

A bottom of exactly 0.7 is possible, but it costs requirement (i).

## 4. Every choice, and what it changes

| Choice | Value | Kind | What it changes |
|---|---|---|---|
| Window H | the last 90 active days | design parameter | γ, the per-halving step, the bottom (sweep below) |
| Offset in f | ½ | fixed by (i) | the bottom (§3) |
| Top | 5 | fixed by (iii) | γ only; see below |
| γ | 0.357 | derived | — |
| Bottom | 0.78 | derived | — |
| Windows inside dimensions | 1 hour, 10 minutes | design parameters | what counts as one amount |
| Unit of history | one active day | design parameter | the unit of the guarantee (§5.1) |
| Dimension set | the 8 in §2 | design parameter | power (§5.3) |
| Combiner | rarest-dimension rank | design choice | calibration and power (§5.2-5.3) |

**The H sweep.**

| H (active days) | γ | Bottom | Per halving | Once before (D = 1) |
|---|---|---|---|---|
| 30 | 0.469 | 0.73 | ×1.38 | ×2.99 |
| 60 | 0.392 | 0.76 | ×1.31 | ×3.25 |
| **90** | **0.357** | **0.78** | **×1.28** | **×3.38** |
| 180 | 0.310 | 0.81 | ×1.24 | ×3.56 |
| 365 | 0.273 | 0.83 | ×1.21 | ×3.71 |

**What the top changes.** Changing the top changes only γ, and M′ = M^(γ′/γ). So:
- the order of calls by M is the same for any top, for every A;
- the order by R = R_static × M is not. The top sets how far behaviour can reorder calls whose
  static scores differ, so the paper needs a sweep over tops 3-10 (E3, §10).

**"Why 5 and not 4.9999?"** Five makes behaviour span the same log-range as the static score
(iii), so neither layer dominates the other. A different top weights one layer more than the
other. Whether that changes results is an empirical question, and E3 answers it. Do not argue that
5 is "the ratio of the static scale's ends": R_static is built from ordinal levels, so that ratio
has no meaning (Cox 2008).

## 5. What it guarantees

### 5.1 One dimension

**Assumption.** The agent's active days are exchangeable: no trend and no cycle the window does not
absorb.

Then (D + 1)/(A + 1) is a conformal p-value (Bates et al. 2023; Laxhammar 2014, Alg. 4.2), and f is
smaller by ½/(A + 1). M ≥ x holds exactly when f ≤ t_x, where t_x = ½ (H + 1)^(−log₅ x). So:

```text
P(M ≥ x on an agent-day) ≤ ⌊(A + 1) t_x + ½⌋ / (A + 1) ≤ t_x + ½ / (A + 1)
```

| Level (A = H = 90) | Simple bound | Sharp bound | Exact without ties |
|---|---|---|---|
| M ≥ 2 | 7.7% | 7.7% | 7.7% |
| M ≥ 3 | 2.8% | 2.2% | 2.2% |
| M = 5 | 1.1% | 1.1% | 1.1% (= 1/91) |

What the bound means:
- **Per agent-day, covering every call of that day.** A call is never more unusual than its day's
  peak so far, so its D is at least the day's D.
- **Conditional on A.** When A < H, M = 5 cannot be reached.
- **Marginal over histories.** "1.1% of days" holds in expectation, not for every particular
  history.
- **Ties make it conservative.** Ties count as "at least as unusual".

### 5.2 The whole call

With every count recomputed leaving the day out over the same A + 1 days, the rarest-dimension rank
is a fixed function of each day and the set of the other days. Under the assumption in §5.1,
(D + 1)/(A + 1) is then a conformal p-value **for any number of dimensions K**. This holds with two
limits:
- **Partial days.** Today's data are incomplete until the day ends. That keeps the guarantee
  conservative for quantities. For categories it is unproven, because later values can move past
  days' ranks either way.
- **The cheaper version** fixes profiles when each day closes. It has no finite-sample guarantee. A
  judge's simulation found it within Monte Carlo error of nominal on iid days.

The table compares the two combiners on ordinary days, for K = 8 and 8,000 agent-days per row.
"Correlation" is between dimensions, through a common day effect.

| Combiner | Correlation | Median M | P(M ≥ 3) | P(M = 5) |
|---|---|---|---|---|
| M of the most unusual dimension | 0 | ×1.90 | 16.2% | 8.4% |
| M of the most unusual dimension | 0.25 | ×1.69 | 14.1% | 7.6% |
| **Rarest-dimension rank** | 0 | **×1.00** | **2.4%** | **1.2%** |
| **Rarest-dimension rank** | 0.25 | **×0.99** | **2.1%** | **1.0%** |

With the simple maximum:
- a typical ordinary call gets about ×1.7-1.9;
- an ordinary agent reaches ×5 on about one day in 12-13;
- the union bound is 8 × 1.1% = 8.8%.

The rank replaces a K-dependent correction such as Bonferroni with recalibration against the
agent's own days.

### 5.3 The price: one strong signal is worth less

The rank keeps false alarms at about 1/91 of days, and the cost is power. Here is a call that is
new on one dimension and ordinary on all the others:

| Dimensions K | Median M | P(M = 5) |
|---|---|---|
| 1 | ×5.00 | 100% |
| 4 | ×3.38 | 27% |
| 8 | ×2.50 | 16% |

The trade-off is forced. Records on some dimension come on about 8.4% of ordinary days (the
maximum row of §5.2), so they cannot all score ×5 while ×5 stays at 1.1% of days. Reaching ×5 needs a call more unusual than
every day in the window, for example new on two dimensions at once.

The ties among one-record calls are broken by the next-rarest dimension. Two otherwise identical
first-time calls can therefore differ, for instance by their hour of day.

### 5.4 Many agents

With N agent ids, about N/91 agent-days reach ×5 each day by chance. A daily review list across
agents needs false-discovery control, such as Benjamini-Hochberg across ids.

## 6. Guideline values

These are **per dimension**, for an agent with a full window (H = 90). For the whole call, see §5.3.

| Behaviour for this agent, on one dimension | M |
|---|---|
| Less unusual than every past day | ×0.78 |
| About every other active day | ×1.00 |
| About once a week | ×1.54 |
| About once in 10 days | ×1.75 |
| About once a month | ×2.50 |
| Once in 90 active days | ×3.38 |
| Never in 90 active days | ×5.00 |

**New agents ramp up with evidence.** Something never seen before scores:

| Active days of history | 0 | 1 | 3 | 10 | 30 | 60 | 90 |
|---|---|---|---|---|---|---|---|
| M | ×1.00 | ×1.28 | ×1.64 | ×2.35 | ×3.40 | ×4.34 | ×5.00 |

The discount also grows with evidence: ×0.87 after 1 day, ×0.79 after 10 and ×0.78 after 90.
There is no warm-up rule. The same ramp also makes a fresh id the cheapest evasion (§9).

## 7. Paper text

Equation:

```latex
M \;=\; \left(\frac{A+1}{2D+1}\right)^{\gamma}, \qquad \gamma \;=\; \frac{\ln 5}{\ln (H+1)}
```

Paragraph:

> **Behaviour multiplier.** Let A be the agent's active days in its last H = 90. On one dimension,
> a past day is at least as unusual as the call if its peak amount was at least as large, or its
> rarest tool, asset or hour at least as rare. Every ordinary day looks rare on some dimension, so
> we compare the call's rarest dimension with each past day's rarest; D counts the past days that
> are at least as unusual. Then R = R_static · M with M = ((A+1)/(2D+1))^γ and γ = ln 5 / ln(H+1).
> Given the mid-p frequency (D+½)/(A+1), this is the only monotone, scale-invariant formula where
> (i) behaviour seen on half the days gives M = 1, (ii) halving the frequency multiplies M by a
> fixed factor (×1.28), and (iii) M spans the same log-range as the static score. The bottom,
> ≈0.78, follows. If an agent's days are exchangeable, the chance that any of its calls on a given
> day reaches M = 5 is at most 1/(H+1) ≈ 1.1% [Bates et al. 2023].

Introduction, two sentences:

> A static score says how dangerous a tool is, not that an agent is suddenly acting out of
> character. We add one behaviour multiplier with no fitted weights: it compares each call with the
> agent's own last 90 active days, keeps habits near ×1, and lifts a call the agent has never made
> towards ×5, while an agent with stable habits reaches ×5 on at most about 1% of its days.

## 8. Questions a reviewer will ask

- **Why 5?** It gives behaviour the same log-range as the static score (iii). The order by M alone
  does not depend on it; the order by R does, and E3 sweeps it (§4).
- **Why a power of the frequency?** It is the only scale-invariant monotone form (ii), and it is
  the same family as the standard p-to-e calibrators. Behaviour that is half as frequent always
  costs the same step, ×1.28.
- **Why not a learned model?** There are no labels for agent misuse, and histories are short.
  Nothing is fitted. The parameters are conventions (§4), and the false-alarm rate is bounded in
  advance (§5).
- **What is new?** Not the statistics. First-time and uncommon-for-this-user flags are standard in
  commercial UEBA. Freeman et al. (NDSS 2016) score per-user feature rarity, and Laxhammar (2014)
  gives conformal anomaly detection. The contribution is an MCP-side layer that:
  - needs only an agent id and no arguments;
  - composes with the static score;
  - states its false-alarm bound;
  - is evaluated on MCP agent traffic (§10).
- **Does it depend on H?** Yes; H is the main design parameter (§4).

## 9. Threats and limitations

- **Exchangeability fails in practice:**
  - **Weekly cycles.** In one judge's simulation, a weekend shift of one standard deviation put
    P(M = 5) at 3.2% of weekend days and 0.25% of weekdays, while the all-day average stayed near
    1.1%.
  - **Steady growth.** An agent whose volume grows sets a record every day, so it sits at ×5 daily.

  Both have to be measured (E1).
- **The discount rewards mimicry.** An agent inside its habit gets M down to 0.78, so a habitual
  write on a top-risk tool falls from 5 to 3.9 and could pass a gate. Recommended: a gate uses
  max(1, M), so the discount reorders the review list but never lowers a block decision.
- **Fresh ids are the cheapest evasion.** A new id reaches only ×1.28 after one day and ×2.35 after
  ten (§6). With only an agent id there is no prior from other agents. The rate of new ids per day is a
  separate signal, outside M.
- **Adaptive pacing.** The formula and the agent's own history are known to the attacker. They can
  stay just under their past daily peaks. The hourly windows also let them spread an action over
  24 hours, and there is no daily-total dimension.
- **Poisoning has a cost but works.** To make a behaviour ordinary (×1), an adversary must show it
  on about 45 of 90 active days. Before that, the first repetitions still score high.
- **A new tool on the server.** Every agent that adopts it sets a record on Tool at the same time.
  Without a cross-agent comparison this is not discounted.
- **An organisation-wide id dilutes both kinds of dimension.** Quantities become organisation
  totals. The organisation's union of tools, assets and hours is broad, so if it touches a new asset
  every day, a new asset is not unusual.
- **Coarse top.** At A = 90 the largest values are ×5, ×3.38 and ×2.82 (D = 0, 1, 2).

## 10. Experiments the paper needs

None of these has been run. Until they are, the paper must not say the layer "is evaluated".

| # | Experiment | Answers |
|---|---|---|
| E1 | Ordinary-traffic false alarms against the bound, split by weekday/weekend, growing agents and organisation-wide ids, with the spread across agents | does the bound hold on real days |
| E2 | Detection and precision@k of R against v5, the most-unusual-dimension maximum, a Fisher (sum of log frequencies) combiner, UEBA-style first-time flags and Freeman et al.'s score | is it useful |
| E3 | Sweeps of the top (3-10), H, the offset ½ vs 1, and the combiner | do the choices matter |
| E4 | Gate crossings caused by the discount, with and without max(1, M) | the mimicry hole |
| E5 | Adaptive attacks: mimicry, pacing, poisoning cost, id rotation, dormancy, a newly shipped tool | robustness |
| E6 | Dilution against organisation size, for organisation-wide ids | the shared-id setting |
| E7 | The cheap combiner against the exact one, on real days | is the cheap version valid |

## 11. What this replaces in the v5 spec

| v5 revision 2 | This proposal |
|---|---|
| Commonness plus the record rank against the route's agent-days | the agent's own days only |
| Budget shares (1/21, 1/12) and watch-only terms | the rarest-dimension rank; no weights |
| Alert and watch floors, floor budget, demotion, route warm-up | removed; sensitivity stays in R_static |
| Surge guard, org discount, habit rules | removed |
| Red Flags and the behaviour policy file | removed |
| s1 = 1/(1+2q), M = 5^(2s1−1), M ∈ [1, 5] (D2) | one formula; M ∈ [0.78, 5] (D2 reversed) |
| Key: sign-in, else client name + address (D5) | an operator-issued agent id only |

Read volume stays (D1). D3 is moot, because every dimension is treated alike.

## 12. Open decisions for the author

1. **Combiner.**
   - The rarest-dimension rank: calibrated, but one record is worth about ×2.5.
   - The most-unusual-dimension maximum: one record gives ×5, but ordinary calls sit near ×1.9 and
     ×5 comes on about 8% of ordinary days.

   Recommended: the rank, with E2 comparing both.
2. **Bottom.** ×0.78 with mid-p (keeps (i)), or no discount with τ = 1 (M ∈ [1, 5], which was D2).
3. **Gate rule.** max(1, M) for gating (recommended, §9).
4. **H** = the last 90 active days.
5. **Session duration.** Recommended: drop it.
6. **Fewer dimensions** raise power (§5.3). Whether all eight earn their place is part of E2.

## 13. Judges' review (revision 1)

Four independent judges read revision 1. Their reports are summarised here; their scratch scripts
are in the session scratchpad, not the repository.

| Judge | Verdict on revision 1 | Main findings | Changed in revision 2 |
|---|---|---|---|
| A* security PC member | weak reject | Uniqueness assumed its answer. "5 = ratio of the scale's ends" is meaningless on an ordinal scale. One record gets ×2.5 at the call level, not ×5. The discount is a gate hole. Identity provenance was unstated. Nothing was evaluated. | §3 reframed; 5 justified as equal log-range (iii); §5.3 added; gate rule; identity assumption; §10 experiments; threats extended |
| Statistician | correct with fixes | Uniqueness needs assumption (0) and fails on the finite lattice (by < 2×10⁻⁴). The ½ is a choice (the τ table). The bound is per agent-day by dominance, conditional on A, marginal, and has a sharper form. The rank is valid for any K under the stated conditions, but power is diluted. Citations confirmed with DOIs. | §3, §5.1, §5.2, §5.3, §5.4, references |
| Reproducer | 58 of 60 numbers match | H = 60 bottom 0.76, not 0.77. Bound at M ≥ 3 is 2.8%, not 2.9%. "Shared weight 0.5" is a correlation of 0.25. | all three fixed; probe relabelled |
| Paper editor | clarity 3/5 | Whole-call D was unclear. "Applied twice" misleads. Notation clashes (p, R1-R3, K/k, m/M, D/D_d). Jargon. The §7 paragraph was too long. | renamed to rarest-dimension rank; f and n_d; (i)-(iii); quantity/category; new §7 paragraph and intro sentences |

## 14. Reproduce

```bash
python3 -I reports/experiments/dynamic_dimensions/knowledge_base/probes/m_formula_numbers.py
```

It takes about two minutes and prints the numbers in §1, §3-§6.

## References

- J. Aczél. *Lectures on Functional Equations and Their Applications*. Mathematics in Science and
  Engineering, vol. 19. Academic Press, New York, 1966. Metadata confirmed (CiNii); the page for
  the Pexider equation is UNVERIFIED.
- S. Bates, E. Candès, L. Lei, Y. Romano, M. Sesia. Testing for outliers with conformal p-values.
  *Annals of Statistics* 51(1):149-178, 2023. doi:10.1214/22-AOS2244.
- L. A. Cox Jr. What's wrong with risk matrices? *Risk Analysis* 28(2):497-512, 2008.
  doi:10.1111/j.1539-6924.2008.01030.x.
- J. R. Douceur. The Sybil attack. IPTPS 2002. Cited through note 06.
- D. M. Freeman, S. Jain, M. Dürmuth, B. Biggio, G. Giacinto. Who are you? A statistical approach
  to measuring user authenticity. NDSS 2016. doi:10.14722/ndss.2016.23240.
- H. O. Lancaster. Significance tests in discrete distributions. *Journal of the American
  Statistical Association* 56(294):223-234, 1961. doi:10.1080/01621459.1961.10482105.
- R. Laxhammar. *Conformal Anomaly Detection: Detecting Abnormal Trajectories in Surveillance
  Applications*. PhD thesis, University of Skövde, 2014. Alg. 4.2 was read for note 04.
- G. Shafer, A. Shen, N. Vereshchagin, V. Vovk. Test martingales, Bayes factors and p-values.
  *Statistical Science* 26(1):84-101, 2011. doi:10.1214/10-STS347.
- V. Vovk, R. Wang. E-values: calibration, combination and applications. *Annals of Statistics*
  49(3):1736-1754, 2021. doi:10.1214/20-AOS2020.
