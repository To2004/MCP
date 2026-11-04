# Score aggregation and calibration: from the max of heuristic scores to Tippett on conformal p-values

This note reviews, from primary sources, how to combine per-dimension anomaly scores soundly. It
then works out what the dynamic layer's max becomes if each dimension's score is a conformal
p-value against the caller's own history. Threat model as everywhere in this repo: the MCP server
is the protected asset and the calling agent is the threat. Every guarantee below is about false
alarms on an *ordinary* agent. None of them says anything about detecting an adaptive one. Sources
were opened on 2026-10-25 (see [Sources](#sources)).

## Answers in brief

1. **Zimek et al. argue against the max, and the paper cites them in support of it.** They write
   that the max "has a tendency to overestimate the outlierness" and that "a single result that is
   far off ... will determine the ensemble result" (p. 18). They do allow two cases, and both fit
   this design: "multiview" outliers seen in different subspaces, and settings where "the cost of
   missing a single outlier is much higher than the cost for a high false alarm rate". Aggarwal &
   Sathe do support the max: it reduces bias when outliers are hidden in a few components, at the
   cost of variance on small training sets. The citations in the notes (line 149 and line 273)
   need rewording ([§2](#2-outlier-ensembles-what-the-two-cited-papers-say)).
2. **Both papers, and Kriegel et al., say a combination is only sound after normalisation.** The
   design's claim that "the scores share one scale" (property 6) rests on all scores using the
   same curve shape. That is not calibration. The simulation shows the gap: one red flag,
   oversized request, causes 71% of v4's false alarms. This is the failure Zimek et al. name.
3. **The rarity score is already almost calibrated.** Its `e = (N+1)/(A+1)` equals `λ̂ · p`,
   where `p` is a plug-in conformal p-value and `λ̂ = (n+1)/(A+1)` is his calls per active day
   ([§1.2](#12-the-rarity-score-is-a-calibrated-per-day-rate)). The excess score is a ratio to his
   mean, not a tail probability, so it is not calibrated. The red flags' values are constants.
4. **On conformal p-values, the max is Tippett's minimum p.** With per-dimension rates
   `q_d = λ̂_d p_d` and weights `w_d` that sum to 1, the call's evidence is
   `q = min_d q_d / w_d` (weighted Bonferroni). This holds under any dependence between
   dimensions. Šidák's form `1-(1-p_min)^K` is exact only when they are independent.
5. **Guarantees.** Per call, `P(q ≤ t) ≤ Σ_d w_d t / λ_d`. Per agent-day,
   `P(some call today has q ≤ t) ≤ t` (approximately, because `λ̂` is estimated). Keep the
   design's curve with `s = 1/(1+2q)`. Then `M` stays in (0.7, 5), ×1 still means "once every
   two days", ×3 means about once in 10.6 days, and the reason `d*` is `argmin_d q_d / w_d`.
6. **A 90-day history cannot back 15 equal-weight dimensions.** A conformal p-value is never below
   `1/(n+1)`, so no `q_d` can go below `1/(A+1)`. With `K = 15` and `A = 90`, Bonferroni caps `M`
   at ×2.24, so personal evidence alone can never reach ×3. The fix is a third stage: calibrate
   the combined statistic against his own past calls. This gives an exact per-agent-day guarantee
   under day-exchangeability, with `M` in (0.7, 4.67] at `A = 90`. It can run today on the logged
   `s1` ([§6.3](#63-stage-3-calibrate-the-combined-score-against-his-own-past)).
7. **The daily list cannot use BH on personal baselines alone.** A day-level p-value is at least
   `1/(A+1) = 0.011`, but BH's first threshold for 150 agents at FDR 0.1 is `0.00067`. Either
   calibrate the per-agent-normalised statistic on the whole organisation's agent-days, which
   brings the floor down to about 7·10⁻⁵, or keep a top-k list and report its estimated share of
   false discoveries (at least 33% for k = 5 from personal baselines).
8. **Exchangeability is the assumption that drift, the weekly cycle, overlapping windows and an
   agent shaping its own baseline all break.** Updating once a day keeps scoring free of leakage,
   but calls within a day share one calibration set. Barber et al. bound the coverage loss under
   drift, and decaying weights trade resolution for robustness.
9. **The max (min-p) is the most powerful combiner only for sparse signals**: one or two
   dimensions out of 15. For several medium signals (mass cleanup, scope creep, copy from a
   sensitive repository) the harmonic-mean p-value or the Cauchy combination is stronger. Both
   still credit most of the evidence to the smallest p-value ([§4](#4-combining-p-values)).

## 1. The current design in statistical terms

### 1.1 Three kinds of score under one max

| Kind | Dimensions | What `s` is | Calibrated? |
|---|---|---|---|
| Rarity score | tool, asset, network, client, hour of day | `c / (1 + 2e)`, with `e` the per-day rate of something this rare | almost: `e = λ̂ · p_split` (§1.2) |
| Excess score | call rate, write rate, breadth, repetition, session duration | `x / (x + 2)`, with `x = (today+u)/(usual+u)`, a ratio to his mean | no (§1.3) |
| Red flag | burst, sweep, oversized request, unsafe sequence, missing handshake | 0.9 or 0.7, habit-discounted | the limit is (org 99.5% quantile per agent-day); the value is not |

### 1.2 The rarity score is a calibrated per-day rate

For dimension `d`, let his history (90 days, up to yesterday) contain `n` calls over `A` active
days, with `n_w` calls on value `w`. The design's "rare calls" for the value `v` of this call is
`N = Σ_{w: n_w ≤ n_v} n_w`. Take as nonconformity "how rarely he uses this value"
(`S = -n_value`). Then the plug-in conformal p-value is the following. It is plug-in because the
counts come from the same history the call is compared with; the exact version is below.

```
p_split = (1 + N) / (n + 1)                           the share of his past at least this rare, add-one
e       = (N + 1) / (A + 1) = λ̂ · p_split,             λ̂ = (n + 1) / (A + 1)  calls per active day
```

So `e` is the **expected number of calls per day at least this rare**. Under the null, the
expected number of calls a day with `p ≤ t` is about `λ t`. The design's "times per day" therefore
already contains a per-day multiplicity correction across the day's calls. Its two `+1`s are the
add-one rule of conformal inference ("this call", "today").

**Exact (full-conformal) version.** For exact finite-sample validity, the counts must include the
test point (Laxhammar's CAD, Algorithm 4.2, line 2, recomputes every score with the test point in
the bag). With counts from the bag, value `v` has `n_v + 1` occurrences and

```
p_full = ( n_v + 1 + Σ_{w ≠ v, n_w ≤ n_v + 1} n_w ) / (n + 1)
       = p_split + ( Σ_{w: n_w = n_v + 1} n_w ) / (n + 1)        ≥ p_split
```

The design's numerator leaves out the values used exactly `n_v + 1` times. That makes it slightly
anti-conservative, which matters only for small counts. For a **never-used value** (`n_v = 0`):

```
p_full(new value) = (1 + f_1) / (n + 1),     f_1 = number of values he used exactly once in the window
```

The design uses `ν` ("new values he started after onboarding") in place of `f_1`. Both measure how
often his next call is something new. `f_1` is the one the exchangeability argument produces. It
also resembles the Good–Turing estimate of unseen mass (Good 1953; UNVERIFIED: only the citation
was checked, the paper was not opened).

Two departures from calibration are deliberate and should stay outside the statistic
([§6.4](#64-policy-overrides-stay-outside-the-statistic)): the ceilings `c = 0.9`, and the hour-of-day
score. The hour-of-day score uses a local density ("calls within one hour of this time"). It
does not use the cut rule, and weekends are blended with 4 pseudo-days.

### 1.3 The excess score is not calibrated

The excess score depends only on `today / usual`. The same ratio has very different tail
probabilities for different agents. Below, `X` is "calls in the last hour, seen at a call", with
his mean `μ = 100` (computed with scipy in this session; not saved in the repository):

| His hourly count distribution | `P(X ≥ 4μ)` (s = 0.67, ×1.7) | `P(X ≥ 10μ)` (s = 0.83, ×2.9) |
|---|---|---|
| Poisson (a steady bot) | 8·10⁻¹¹³ | ≈ 0 |
| lognormal, CV 0.5 | 0.0008 | < 10⁻⁵ |
| lognormal, CV 1.0 | 0.019 | 0.0007 |
| lognormal, CV 1.5 | 0.034 | 0.0039 |
| lognormal, CV 3.0 (a bursty person) | 0.047 | 0.011 |

The same ×2.9 is a once-in-a-lifetime event for the bot and a weekly event for the bursty
person. Under the max, the dimension with the heaviest benign tail takes the false-alarm budget.

### 1.4 The symptom in the simulation

v4 alerts (×3 or more) on 2.46% of ordinary agent-days. 71% of those are caused by oversized
request (DIMENSION_FORMULAS.md, "What still causes alerts"), so roughly 1.7% of ordinary
agent-days alert through that one flag. The learned limits aim for 0.5%. Three mechanisms are
consistent with this. None has been measured yet; they are inferences to check:

1. **Multiplicity across tools.** `policy.py` (`derive_policy`, `by_tool`) sets each tool's limit
   at the 99.5% quantile of the agent-days that used that tool. An agent-day that uses `m` tools
   faces `m` such tests, so its rate is up to `m × 0.5%`.
2. **Drift.** The limits are learned on the first 30 days and scored on the last 90.
3. **Heterogeneity.** The quantile is pooled across agents, so heavy writers exceed it more often.

This is Zimek et al.'s failure mode word for word: one detector whose scores are "far off" for
some objects "will determine the ensemble result". A calibrated combiner instead gives each
dimension a fixed share `w_d` of the false-alarm budget ([§6](#6-the-max-becomes-tippett-a-worked-design)).

## 2. Outlier ensembles: what the two cited papers say

### 2.1 Aggarwal & Sathe 2015 (SIGKDD Explorations 17(1):24–47)

Their argument is bias against variance. For detectors of different types, "it is assumed that
they are standardized" before combining (p. 35).

- On the two combiners (p. 35): "It has been suggested [23] that the averaging variant is better
  and that the maximum function overestimates the absolute scores [23] by picking out the larger
  errors." [23] is Zimek et al. Then: "one is often able to de-emphasize irrelevant or weak
  ensemble (poorly biased) components with the maximization function. Therefore, one is often
  able to reduce bias. However, the maximization function might increase variance, especially for
  small training data sets."
- Why the max helps (p. 35–36): "In many 'difficult' data sets, the outliers may be well hidden,
  as a result of which many ensemble components may give them inlier-like scores." Their toy
  example gives the outlier one unusual dimension out of `d`. Averaging makes the probability of a
  rank inversion tend to 0.5, while "the maximization function always discovers the correct
  relative score of the outlier point" (p. 36).
- Where it fails (p. 36): "if a training data set (or subsample) is very small, then the
  maximization function will not work very well because of its propensity of pick out the high
  variance in the scores." For this design, that is the onboarding period and short histories.
- What they propose (p. 37): "two schemes, both of which normalize to Z-scores before applying
  the combination". **AOM** averages maxima over buckets. **Thresh** sums scores above a threshold
  (`t = 0` on the Z-score); its effect is "to reward points for showing up as outliers in a given
  component, but not to penalize them too much for showing up as strong inliers". Red flags,
  which "take part only when raised", follow the same thresholded logic.

### 2.2 Zimek, Campello & Sander 2014 (SIGKDD Explorations 15(1):11–22)

The task asked for the exact wording on the maximum. These quotes are from the PDF at kdd.org, with
pages as printed:

- p. 18: "In our opinion, from the point of view of ensembles, using the maximum of scores has some
  decisive disadvantages whereas the average does seem to make more sense."
- p. 18: "The maximum as a combination function results in the upper bound of all individual
  scores and, hence, has a tendency to overestimate the outlierness. This also means that a single
  result that is far off, overestimating the scores for some objects, will determine the ensemble
  result (e.g., Figure 2(b))."
- p. 18: "Errors of each individual score vector for single objects are strongly emphasized, and an
  error of a single ensemble member assigning a high outlier score to some object cannot be
  compensated for, even if all other detectors would be correct."
- **First case they allow** (p. 18): "keeping the maximum scores from different outlier models, if
  these models are learned in different subspaces, could be an approach to the problem of
  “multiview” outliers that we mentioned in the introduction — and that is somehow orthogonal to
  the ensemble or consensus idea." The introduction (p. 12) says "different outliers in different
  subspaces could each be meaningfully reported."
- **Second case they allow** (p. 18): "If the cost of missing a single outlier is much higher than
  the cost for a high false alarm rate, using the maximum combination is certainly worth
  considering."
- On normalisation (p. 17): "normalization of scores is important, to avoid a bias of the decision
  to the individual result with the largest scale."
- Open question (p. 19): "Can scores actually be converted into “outlier probabilities” [23; 40]?
  How would the success of such a conversion be evaluated (the problem of “calibration”)?"

So the answer is yes, with one nuance. They say the max overestimates and is decided by one
member's error. They do not use the word "noisy"; they say a result that is "far off" and "an
error of a single ensemble member". The year is 2014 at Crossref and the ACM (online 2014-03-17).
The authors' own publication list and Aggarwal & Sathe give 2013.

### 2.3 What this means for the paper

The dynamic layer is not a consensus ensemble. Its 15 dimensions are different *views* (cadence,
footprint, protocol). Each is a valid reason on its own, and the server prefers a false alarm to a
missed misuse. Those are Zimek et al.'s two exceptions, so the max can be defended with their own
words, provided the scores are normalised. A paste-ready replacement for the sentence in the notes
(lines 145–150 and 271–273):

> We combine dimensions with the maximum. Outlier-ensemble work warns that the maximum
> overestimates outlierness and lets a single miscalibrated detector decide the result
> \cite{zimek2014ensembles}, but recommends it when outliers are visible in only a few views
> ("multiview" outliers) and when a missed outlier costs more than a false alarm
> \cite{zimek2014ensembles,aggarwal2015outlier}. Both conditions hold here. Because the maximum is
> only meaningful on comparable scores, we calibrate every dimension against the agent's own
> history before taking it (Section~X).

## 3. Normalising scores before combining: Kriegel et al. 2011

Kriegel, Kröger, Schubert & Zimek (SDM 2011, pp. 13–24) define what a combinable score must be,
in Section 3.1 of the preprint:

- *regular*: `S(o) ≥ 0`, `S(o) ≈ 0` for inliers, `S(o) ≫ 0` for outliers;
- *normal*: regular and in `[0, 1]`;
- *ranking-stable* transformation: `S(o1) ≤ S(o2) ⇒ T S(o1) ≤ T S(o2)`.

Their Gaussian scaling (Section 3.3.2) is

```
Norm_gauss(o) = max{ 0, erf( (S(o) − μ_S) / (σ_S √2) ) } = max{ 0, 2·cdf_gauss(o) − 1 }
```

The ensemble then averages the unified scores, `P(o) = (1/|OD|) Σ_i prob_i(S_i(o))` (Section
4.2). In their Table 5, the "mean unified score" has the best ROC AUC in five of the six
settings and the second best in the sixth.

Three consequences for the design:

1. **Unify first, then combine.** The order matters more than the choice of combiner.
2. **For a per-caller baseline, the natural unification is per agent and per dimension: his own
   empirical distribution of that statistic.** That is a conformal p-value, and it has every
   property above. As `1 − p` it is normal, it is ranking-stable (a rank transform), and it needs
   no distributional fit. Kriegel et al. fit a Gaussian or Gamma to the population of scores; with
   90 days per agent, the empirical rank is the safer choice.
3. **The design's exponent already has Kriegel's form.** `2s − 1` matches `2·cdf − 1`. With
   `s = 1 − p`, the multiplier would read `M = 5^(1 − 2p)`. §6 keeps the design's own curve
   `s = 1/(1 + 2q)` instead, because it keeps "0.5 = every other day".

## 4. Combining p-values

For `K` p-values `p_1 … p_K` of one call (one per dimension that takes part):

| Combiner | Statistic → combined p | Valid when | Source opened |
|---|---|---|---|
| Tippett | `p_min = min_d p_d` → `1 − (1 − p_min)^K` (Šidák form) | independent (`p_min ~ Beta(1, K)` under H0) | Heard & Rubin-Delanchy |
| Bonferroni | `min(1, K · p_min)` | any dependence | Vovk & Wang eq. (1) |
| Weighted Bonferroni | `min_d p_d / w_d`, `Σ w_d = 1` | any dependence (union bound) | elementary |
| Fisher | `−2 Σ log p_d ~ χ²_{2K}` | independent | Heard & Rubin-Delanchy; Bates Thm 1 (fails with a shared calibration set) |
| Stouffer | `Σ Φ⁻¹(p_d) ~ N(0, K)` | independent | Heard & Rubin-Delanchy |
| Harmonic mean (HMP) | `p̊ = 1 / Σ_d (w_d / p_d)` | approximately; "anticonservative, but only very slightly for small α" | Wilson 2019 |
| HMP, dependence-free | `e · ln K · p̊` | any dependence, `K > 2` | Vovk & Wang (their table) |
| Arithmetic mean | `2 · p̄` | any dependence | Vovk & Wang (Rüschendorf) |
| Cauchy (ACAT) | `T = Σ w_d tan((0.5 − p_d)π)`, `p = 1/2 − arctan(T)/π` | tail approximately Cauchy under any correlation, given pairwise bivariate normality (C.1) | Liu & Xie Thm 1 |

**When min-p, that is the max score, is the most powerful.**

- **Donoho & Jin 2004, Theorem 1.3.** In the sparse normal-means model with `n^(−β)` non-null
  tests, the maximum (= minimum p = "Bonferroni-based inference") reaches the optimal detection
  boundary only for very sparse signals: "ρ*(β) = ρ_Max(β), β ∈ [3/4, 1), so that M_n is
  effective in the range of very sparse alternatives, while ... M_n is inefficient if β < 3/4."
  This is asymptotic (`n → ∞`). With `K = 15` it is only a heuristic: one or two dimensions out of
  15 is the "sparse" case.
- **Liu & Xie 2020.** "the minimum p-value test has good power against sparse alternatives since it
  uses the smallest individual p-value to represent the overall significance". The Cauchy
  combination "is essentially dominated by a few of the smallest p-values" and also attains the
  boundary under strong sparsity.
- **Heard & Rubin-Delanchy 2018, Proposition 2.** Tippett is the uniformly most powerful test only
  under an alternative where one p-value is `Beta(a, n)` and the others are `U[p_i*, 1]`. They
  conclude: "Tippett’s method seems very difficult to justify in practice" as a likelihood-ratio
  test. Fisher suits positive-valued data that are larger under H1, and Stouffer suits roughly
  Gaussian data (their Table 1).
- **Vovk & Wang 2020.** "in the IID case, using the Bonferroni merging function is a safe option,
  at least asymptotically". But "if there is potentially substantial dependence among the
  p-values, then we should not use Bonferroni, and the harmonic mean might be a safer choice." The
  reason is power: under strong dependence Bonferroni stays valid but becomes too conservative.

**Worked example** (`K = 15`, ordinary dimensions at `p = 0.5`, equal weights; computed in this
session):

| Case | Bonferroni | Šidák | HMP | `e ln K` · HMP | Cauchy |
|---|---|---|---|---|---|
| one strong (0.001) | 0.015 | 0.015 | 0.015 | 0.107 | 0.015 |
| one medium (0.02) | 0.300 | 0.261 | 0.192 | 1.000 | 0.241 |
| two medium (0.02, 0.02) | 0.300 | 0.261 | 0.119 | 0.876 | 0.140 |
| three medium (0.03 ×3) | 0.450 | 0.367 | 0.121 | 0.891 | 0.141 |

For a single strong signal all the combiners agree, so the max loses nothing. For two or three
medium signals, HMP and Cauchy give 2–4× smaller p-values than Tippett. This is the "medium signals
don't add up" cost the design already names, and it fits the misuse kinds v4 catches least: mass
cleanup 24%, scope creep 30%, copy from a sensitive repository 48%. HMP and Cauchy belong in the
ablation's combiner arm next to `s1 + 0.3 s2 (1 − s1)`. The dependence-free HMP (`e ln K`) is far
too conservative at `K = 15` to be useful.

## 5. Conformal p-values from the agent's own history

### 5.1 Definition and guarantees

Orient scores so that larger means stranger. For a test unit with score `S` and calibration
scores `S_1 … S_n`:

```
p = (1 + #{i ≤ n : S_i ≥ S}) / (n + 1)
```

This is Bates et al.'s eq. (3), which counts `≤` on a score where small means outlier. It is also
Laxhammar's CAD, Algorithm 4.2, line 4.

- **Marginal validity**: if the test unit is exchangeable with the calibration units,
  `P(p ≤ t) ≤ t` for all `t` (Bates eq. 2; Laxhammar eq. 4.10, `Pr(Anom^ε = 1) ≤ ε`). Laxhammar
  reads this as a test, at level ε, of the null "the new example and the training set are IID".
  For this design that null is "this call is like his last 90 days".
- **Dependence**: p-values that share one calibration set are positively dependent (PRDS, Bates
  Thm 2), so BH still controls the FDR (Cor. 1). The same dependence "invalidates Fisher’s
  combination test" (Bates, Section 1.2 and Thm 1). So do not use Fisher across the calls of one
  day.
- **Conditional on his history**, the false-alarm rate at level `α` is
  `FPR(α; D) ~ Beta(ℓ, n + 1 − ℓ)` with `ℓ = ⌊(n + 1)α⌋` (Bates Prop. 1). Its spread grows like
  `(nα)^(−1/2)`:

| Calibration size `n` | α | Mean FPR | 90th percentile across agents | `P(FPR > 1.5α)` |
|---|---|---|---|---|
| 30 days | 0.05 | 0.032 | 0.074 | 0.10 |
| 90 days | 0.05 | 0.044 | 0.073 | 0.09 |
| 90 days | 0.10 | 0.099 | 0.140 | 0.06 |
| 900 calls | 0.01 | 0.010 | 0.014 | 0.08 |

  At the day level (`n = A = 90`), one agent in ten has a true false-alarm rate above 1.45 times
  the nominal 5%. Bates et al.'s calibration-conditional adjustment (Thm 4, with Simes or DKWM
  bounds) makes the rate hold with probability `1 − δ` for each agent, at a cost in power.
- **Offline against online** (Laxhammar, Section 4.3.2): with a fixed training set, "the empirical
  rate of detected anomalies for the offline CAD may be significantly higher than ε" because the
  alarm indicators are not independent. The online CAD, updated after every example, is
  well-calibrated: `lim sup rate ≤ ε` (eq. 4.14). Updating once a day sits in between. Within a
  day it is offline, so the guarantee should be stated per agent-day, not per number of calls.

### 5.2 One p-value per dimension

Each dimension needs a test **unit**, a **calibration set** of past units of the same kind, and a
rate `λ̂_d = (n_d + 1)/(A + 1)` of units per active day. Then `q_d = λ̂_d · p_d` is "how many units
a day are at least this strange".

| Dimension | Unit | Score `S` recorded per unit | `p_d` |
|---|---|---|---|
| Call rate, write rate, breadth, repetition | call | the windowed value at the call (for example calls in the 60 min before it) | `(1 + #{past calls with value ≥ now}) / (n + 1)` |
| Session duration | call | minutes since the session started | the same |
| Tool, asset, network, client | call (message, for network and client) | `−(his count of the value)` | `p_full` of §1.2; for a new value, `(1 + f_1)/(n + 1)` |
| Hour of day | call | `−(his calls within ±1 h of this time)`, cut rule | `(1 + #{past calls whose ±1 h density ≤ now}) / (n + 1)`, weekends computed apart |
| Burst, sweep, unsafe sequence | agent-day | raised or not | personal: `(k_f + 1)/(A + 1)`; org: `(1 + raised org agent-days)/(N_org + 1)` |
| Oversized request | agent-day, per tool | raised or not | org-calibrated (no habit discount, as now) |
| Missing handshake | session | session without `initialize` | `(1 + his such sessions)/(sessions + 1)` |

The engine already stores the mean of each windowed value (`DailyMean.mean_then_add`, one value
per past call). For the conformal version, store a log-binned histogram instead. Counting a whole
tied bin as `≥` keeps `p` conservative. The habit discount `0.9/(1 + 2k/(A+1))` is already
`0.9 / (1 + 2 q_f)` with a personal flag rate, which is the same shape as everything else.

## 6. The max becomes Tippett: a worked design

### 6.1 Stages 1 and 2: per-dimension rates, then weighted Bonferroni

```
Stage 1, each dimension d in D(c):  p_d(c) as in §5.2;   q_d(c) = λ̂_d · p_d(c)
Stage 2, the call:                  q(c)  = min_{d ∈ D(c)} q_d(c) / w_d          Σ_d w_d = 1
                                    d*(c) = argmin_d q_d(c) / w_d                 the reason
                                    q2(c) = second-smallest q_d(c) / w_d          the runner-up
The multiplier (the design's curve with s = 1/(1+2q)):
    M(c) = 5   ^ ((1 − 2q) / (1 + 2q))      when q ≤ 1/2
    M(c) = 0.7 ^ ((2q − 1) / (1 + 2q))      when q > 1/2         M ∈ (0.7, 5), M(1/2) = 1
```

**Guarantees.** These follow from the union bound and need no assumption about how dimensions
depend on each other. Let `U_d` be his units of dimension `d` today. Under H0, where each unit is
exchangeable with his history so that every `p_d(u)` is super-uniform:

```
per call:       P( q(c) ≤ t )                ≤ Σ_d w_d · t / λ_d
per agent-day:  P( ∃ c today: q(c) ≤ t )      ≤ Σ_d E|U_d| · w_d t / λ_d  ≈  t      (λ_d ≈ E|U_d|)
```

The "≈" is the price of estimating `λ_d` from his history. A day busier than usual has more
units, and call rate prices that separately. Read `M` as a per-day rate:

| `M` | `s` | `q`: an ordinary agent-day this strange happens about | `M` | `s` | `q` |
|---|---|---|---|---|---|
| ×1.0 | 0.50 | every 2 days | ×3.6 | 0.90 | once in 17.6 days |
| ×1.9 | 0.70 | once in 4.7 days | ×4.0 | 0.93 | once in 27 days |
| ×3.0 | 0.84 | once in 10.6 days | ×4.5 | 0.97 | once in 59 days |

So **the ×3 alert line bounds the per-agent-day false alarms at about 9.4%**. That is a
conservative bound; the realised rate is lower. To guarantee a rate `α_day`, put the line at
`M_alert = g(1/(1 + 2 α_day))`: ×4.29 for 2.5%, ×3.73 for 5%.

### 6.2 The resolution limit

A conformal p-value is at least `1/(n+1)`, so `q_d ≥ λ̂_d/(n_d + 1) = 1/(A + 1)`, and
`q ≥ min_d 1/((A + 1) w_d)`. With equal weights:

| Active days `A` | `K` dimensions | Smallest `q` | Largest `M` |
|---|---|---|---|
| 14 (onboarding) | 5 / 15 | 0.36 / 1.0 | ×1.31 / ×0.89 |
| 30 | 5 / 15 | 0.17 / 0.50 | ×2.24 / ×1.00 |
| 90 | 1 | 0.011 | ×4.66 |
| 90 | 5 / 15 | 0.056 / 0.17 | ×3.62 / ×2.24 |

**Ninety days of one agent's data cannot certify a 1-in-90-days event across 15 looks.** This is
a property of personal baselines, not of conformal inference. The current design avoids it only by
leaving out the factor `K`, which leaves its guarantee unstated. There are three ways out, and the
next section combines them:

- unequal weights, for example most weight on org-calibrated red flags, whose p-values have
  resolution `1/(N_org + 1)`;
- org-pooled calibration;
- calibrating the combined statistic itself, which replaces `K` by the effective number of
  independent dimensions in his own data.

### 6.3 Stage 3: calibrate the combined score against his own past

```
q3(c) = (1 + #{his past calls u, last 90 days up to yesterday : q(u) ≤ q(c)}) / (A + 1)
M(c)  = g( 1 / (1 + 2 · q3(c)) )                     g = the design's curve
```

`q3` is the design's rarity score applied to the whole call: how many times per day, over his last
90 days, he made a call at least this strange. For each call, `q(u)` is what the engine computed
live on day `u`, so the logs already hold it.

**Exact per-agent-day guarantee.** Let `Q_j` be the smallest `q` on past active day `j` and `Q_0`
today's. If his active days are exchangeable, `p_day = (1 + #{j ≥ 1 : Q_j ≤ Q_0})/(A + 1)` is
super-uniform. Each past day with `Q_j ≤ q(c)` has at least one call with `q(u) ≤ q(c)`, so
`q3(c) ≥ p_day(c)` for every call. Hence

```
P_H0( ∃ c today : q3(c) ≤ t )  ≤  P_H0( p_day(c*) ≤ t )  ≤  t
```

The proof needs nothing about the dimensions or the calls depending on one another. It is
conformal inference with "the day's strangest call" as the nonconformity score, at day
granularity. Its floor is `1/(A + 1)`, so `M ∈ (0.7, 4.67]` at `A = 90`, `(0.7, 4.11]` at 30 and
`(0.7, 3.42]` at 14. Familiar calls have `q3 ≫ 1` and keep the design's ×0.7 side.

**Use it now, with no change to stages 1 and 2.** Take `q(u) := −s1(u)`:
`q3(c) = (1 + #{past calls with s1 ≥ s1(c)})/(A + 1)`. This gives a stated false-alarm guarantee on
the logged `Verdict.score`. It is monotone in `s1` for each agent, so `d*` and `s2` do not change.
Across agents it acts as Kriegel-style unification: an agent whose `s1` is often high has his high
`s1` discounted. It does **not** fix the per-dimension budget (§1.4). That needs stages 1 and 2.

### 6.4 Policy overrides stay outside the statistic

Three mechanisms are policy decisions, not statistical ones. Keep them as explicit, logged
overrides around `M_stat` from §6.3, so the guarantee stays clean and the reason stays honest:

```
M_final = max( M_stat,  M_floor(σ),  M_flag_org )
```

- **First-access floor**: `M_floor` is ×3.6 for sensitivity 5 and ×2.6 for sensitivity 4. Its
  reason is "policy: first access".
- **Org-calibrated flags**: oversized request, and every flag with no habit discount, is priced on
  the organisation's rate, not his own. Stage 3 would otherwise habit-discount it, and the design
  rejects that: "each one is its own paste".
- **Org discount**: at stage 1, a value that 3 or more other agents adopted this week gets
  `q_d ≥ 0.5`.

### 6.5 What the design keeps and what it costs

- **Kept**: one named reason `d*` and a runner-up; `M` monotone and bounded whatever `K` is; ×1 at
  "every other day"; the warm-up (with `A = 0`, `q3 = 1`, so `M = ×0.89`, close to the design's
  ×1). Exact attribution also stays: removing a dimension changes `q` only where it was `d*`. The
  ablation must then recompute `q3` from the logged per-call `q_d`, which is cheap.
- **Cost**: a histogram per dimension instead of a mean; weights `w_d` to choose and justify;
  coarser resolution at the top of the scale, ×4.67 at most from 90 days; and an alert line that
  becomes a derived quantity from `α_day` instead of a fixed ×3.

## 7. The daily review list: false discoveries across agents

Each day, give each of the `m` agents the p-value `P_a = p_day(c*_a)` of its strangest call. BH at
level `α`: sort `P_(1) ≤ … ≤ P_(m)`, let `k̂ = max{i : P_(i) ≤ iα/m}`, and list those `k̂`
agent-days.

- **Validity**: BH controls the FDR for independent test statistics (BH 1995, abstract). It also
  does so under positive regression dependency (BY 2001, abstract). BY 2001 also gives "a simple
  conservative modification" for any other dependency; the constant `Σ_{i≤m} 1/i` is UNVERIFIED,
  as the full text was not opened. e-BH controls the FDR "for any dependence structure between the
  e-values" (Wang & Ramdas 2022, abstract). Across agents the histories are separate, but
  org-wide events (a release, a VPN change) make many agents strange on the same day. That
  dependence is positive, so BH is plausible but unproven.
- **Feasibility**: `P_a ≥ 1/(A + 1) = 0.011`, while BH's first threshold is `α/m = 0.00067`
  (`m = 150`, `α = 0.1`). BH needs `i ≥ m/((A+1)α) ≈ 17` agents at the floor before it can list
  anything. **From personal baselines alone, BH is powerless at this organisation size.**
- **Option A: pooled calibration.** Calibrate the per-agent-normalised day statistic `Q_a` (which
  is already per-day and per-agent) on all the organisation's agent-days:
  `P_a^org = (1 + #{(a', j) : Q_{a',j} ≤ Q_a}) / (m A + 1)`. The floor becomes `7.4·10⁻⁵` at
  `m = 150`, and BH works. The assumption is that agent-days are exchangeable across agents after
  normalisation. Weaken it by calibrating within strata (tenure band, activity band, bot or
  person), the "Mondrian" idea of Vovk et al. 2005 (UNVERIFIED: the book was not opened).
- **Option B: keep the fixed top-k list and state its quality.** Estimate the false-discovery
  share as `FDP̂(k) = m · t_k / k`, with `t_k` the k-th smallest `P_a` and nearly every agent-day
  null. From personal baselines, `t_k ≥ 1/91`, so `FDP̂ ≥ 0.33` for `k = 5` and 0.17 for `k = 10`
  at `m = 150`. This is an honest number to report next to the list's catch rate. It also says
  that the list's precision has to come from `R_static` and from org-calibrated flags.
- **Real-time alerts** (call by call, not a daily batch) are an online multiple-testing problem.
  Generalized alpha-investing controls online FDR "provided p-values corresponding to true nulls
  are independent from the other p-values" (Javanmard & Montanari 2018, abstract). Calls that
  share one calibration set violate that, which is one more reason to state guarantees per
  agent-day.
- **Why this matters**: Axelsson (2000, abstract) shows that with a low base rate of intrusions,
  "the false alarm rate is the limiting factor" of an intrusion detector.

## 8. Exchangeability, drift and daily learning

Every guarantee above assumes that today's unit is exchangeable with the calibration units. The
places where this breaks in the design:

1. **Learning once a day.** This is inductive (split) conformal at day granularity: today is
   scored only on days before it, so there is no leakage, which is good. Calls within a day share
   one calibration set, so their alarms are dependent (Bates Thm 2; Laxhammar on the offline CAD).
   The number of alarms in a day can exceed `α` times the number of calls even when each call is
   valid. State the guarantee per agent-day.
2. **Drift** (a role change, a new project, a team transfer). These are the design's "ordinary life
   changes", which alert on 2–45% of their days. Barber et al. 2023 bound the loss with fixed
   weights `w_i`, using any joint distribution:
   `coverage gap ≤ Σ_i w_i d_TV(Z, Z^i) / (1 + Σ_i w_i)`, where `Z^i` swaps the test point with
   point `i`. A 90-day window is the fixed weights "1 for the last 90 days, 0 before". The bound is
   large right after a role change. With decaying weights `w = ρ^age`, a drifting history weighs
   less (they suggest `w_i = ρ^(n+1−i)`). The floor then rises to `1/(1 + Σw)`: with `ρ = 0.97` a
   day, `Σw ≈ 30` and `M_max ≈ ×4.1` instead of ×4.67. Weights must be fixed in advance, not chosen
   from the data.
3. **The weekly cycle.** Weekend calls are not exchangeable with weekday calls. Calibrate them
   separately (stratified, "Mondrian"). The design's blend with 4 pseudo-days is a shrinkage that
   lowers variance but gives up exact validity.
4. **Overlapping windows.** "Calls in the last hour" at two consecutive calls are nearly equal. The
   effective calibration size is closer to the number of hours, or days, than the number of
   calls, so the spread in §5.1 is wider than `Beta(ℓ, n + 1 − ℓ)` with `n` = calls. Plan with
   `n ≈ A`.
5. **Short histories.** At `A = 14` the floor is `1/15`, so `M ≤ ×3.42`. Aggarwal & Sathe warn
   that the max picks out "high variance" on small training sets. That is consistent with v4's
   15% false-alarm rate on new hires' onboarding days.
6. **The agent controls its own baseline, which is the threat model itself.** Validity is a
   statement about the null and gives no power against an agent that drifts slowly ("boils the
   frog"). Its strange days enter the calibration set the next day, and within 90 days they look
   ordinary. Mitigations:
   - red flags with org-level limits learned once (the first 30 days) and never refit per agent;
   - a cap on how fast his baseline may move;
   - comparison with peers;
   - leaving alerted days out of calibration. This biases `p` downward and so raises false
     alarms; it is a trade-off to measure, not a free fix.
7. **Overrides.** The first-access floor and the org discount break calibration on purpose. Keep
   them outside the statistic (§6.4).

## 9. Empirical calibration checks for the simulator

All checks run on the ordinary agent-days of the scored 90 days in the five organisations.

1. **Uniformity of each dimension's p.** Plot `F̂_d(t)`, the share of ordinary units with
   `p_d ≤ t`, against `t`. The curve should satisfy `F̂_d(t) ≤ t + ε`. A DKW band is
   `ε = sqrt(ln(2/δ)/(2n))` (Massart 1990; the constant is UNVERIFIED: only the citation was
   checked). Use `n ≈ A`, not the number of calls (§8.4).
2. **Equal budget.** Compare the share of ordinary false alarms by `d*` with `w_d`. Today it is 71%
   oversized request against 1/15 under equal weights. This one number is the strongest
   calibration finding for the paper.
3. **One scale, tested.** For each dimension compute `P(s_d ≥ 0.84 on an ordinary agent-day)`,
   where 0.84 is the ×3 line. If property 6 held in the calibration sense, these would be about
   equal. Report the table, and QQ-plots of the upper tails.
4. **Is the stated rate real?** For `t ∈ {0.01, 0.025, 0.05, 0.1}`, plot the stated `t` against
   the observed share of ordinary agent-days with `min_c q3(c) ≤ t`. This is a reliability diagram
   for the guarantee. Summarise it with an ECE-style weighted gap (Guo et al. 2017, eq. 3).
5. **Per-agent spread.** Compare the histogram of per-agent false-alarm rates at level α with
   `Beta(ℓ, A + 1 − ℓ)`. A wider spread means the days are not exchangeable: drift, or the life
   changes.
6. **Effective number of dimensions.** `K_eff(t) = P(min_d p_d ≤ t) / t` on ordinary units shows
   how conservative Bonferroni is, and what stage 3 gains.
7. **Reliability of `M` against labels.** Bin calls by `M` and plot the share of gray-episode calls
   per bin. It should increase. `M` is not a probability, so ask for monotonicity, not the
   diagonal (Guo et al., Section 2).
8. **Ablation arms to add** to [Future work](../DIMENSION_FORMULAS.md#future-work-ablation-study):
   - Tippett with weighted Bonferroni (stages 1 and 2);
   - the calibrated max (stage 3 on today's `s1`);
   - stages 1 to 3 together;
   - HMP and Cauchy as combiners;
   - pooled and personal calibration for the daily list;
   - weights `ρ ∈ {1, 0.99, 0.97}`.

## 10. What to change in the design document and the paper

1. **DIMENSION_FORMULAS.md, property 8 and "Where the formulas come from"**, and **the notes,
   lines 145–150 and 271–273**: reword the citations as in §2.3. Zimek et al. support the max
   only for multiview outliers and when misses cost more than false alarms, and they require
   normalisation.
2. **Property 6, "well-founded because the scores share one scale"**: the shared curve makes the
   scores comparable in shape, not in false-alarm rate. Either soften it ("the same shape") or
   earn it with stage 1, which makes "0.5" mean the same per-day rate in every dimension.
3. **"This thing + everything rarer is an empirical p-value"**: make it exact. `e = λ̂ · p_split`,
   the expected number of calls a day at least this rare (§1.2).
4. **State a guarantee.** With stage 3 the paper can claim: "for an agent whose behaviour is
   exchangeable across days, the probability that an ordinary agent-day contains a call with
   `M ≥ g(1/(1+2α))` is at most α". Then report the simulation's realised rate against that
   bound (§9.4).
5. **Report the daily list's estimated false-discovery share** with its catch rate (§7, option B),
   or move to pooled calibration plus BH (option A).

## Sources

Opened on 2026-10-25. "Full text" means the paper itself was read. "Abstract" means the
publisher-deposited abstract at Crossref. "Metadata" means only the DOI record was checked, so any
claim about the content is UNVERIFIED.

| Source | Opened | Used for |
|---|---|---|
| Zimek, Campello, Sander 2014 | full text (kdd.org PDF V15-01-02) | §2.2 quotes, p. 12, 17–19 |
| Aggarwal, Sathe 2015 | full text (kdd.org issue PDF Article4) | §2.1 quotes, p. 35–37 |
| Kriegel, Kröger, Schubert, Zimek 2011 | full text (authors' preprint) | §3 definitions, formula, Table 5 |
| Bates, Candès, Lei, Romano, Sesia 2023 | full text (arXiv 2104.08279) | §5.1: eqs. (2)–(4), Thms 1, 2, 4, Prop. 1, Cor. 1 |
| Laxhammar 2014 (PhD thesis) | full text (DiVA, his.diva-portal.org) | CAD Alg. 4.2, eqs. 4.10–4.14 |
| Heard, Rubin-Delanchy 2018 | full text (arXiv 1707.06897) | §4 Prop. 2, Table 1, combiner definitions |
| Donoho, Jin 2004 | full text (arXiv math/0410072) | §4 Thm 1.3 |
| Liu, Xie 2020 | full text (arXiv 1808.09011) | §4 eq. (1), Thm 1, condition (C.1) |
| Vovk, Wang 2020 | full text (arXiv 1212.4966) | §4 merging constants and the rule of thumb |
| Wilson 2019 | full text (Europe PMC, PMC6347718) | §4 HMP validity statement |
| Barber, Candès, Ramdas, Tibshirani 2023 | full text (arXiv 2202.13415) | §8 eq. (3), Lemma 1, weights |
| Guo, Pleiss, Sun, Weinberger 2017 | full text (arXiv 1706.04599) | §9 reliability diagrams, ECE eq. (3) |
| Benjamini, Hochberg 1995 | abstract | §7 |
| Benjamini, Yekutieli 2001 | abstract | §7 (the `Σ 1/i` constant is UNVERIFIED) |
| Wang, Ramdas 2022 | abstract | §7 e-BH |
| Javanmard, Montanari 2018 | abstract | §7 online FDR |
| Axelsson 2000 | abstract | §7 base rate |
| Laxhammar, Falkman 2014 (TPAMI); 2015 (AMAI) | metadata; content through the thesis's own summary | §5.1 |
| Šidák 1967; Good 1953; Massart 1990; DeGroot, Fienberg 1983; Niculescu-Mizil, Caruana 2005; Vovk, Gammerman, Shafer 2005 | metadata only: content UNVERIFIED | named where they originate a tool |
| Tippett 1931; Fisher 1932; Stouffer et al. 1949; Arias-Castro et al. 2011 | not opened: UNVERIFIED, cited through Heard & Rubin-Delanchy, Liu & Xie and Vovk & Wang | attribution only |

Repository facts: `src/mcp_security/behaviour/policy.py` (`QUANTILE = 0.995`, per-tool limits
over agent-days), `memory.py` (`DailyCounts.per_day`, `DailyMean.mean_then_add`), `engine.py`
(`_more`, `multiplier`). The simulation numbers are from `DIMENSION_FORMULAS.md` (v4). The
arithmetic in §1.3, §4, §5.1 and §6 was computed with scipy 1.18 in this session's scratchpad. It
is not in the repository.

## References

- C. C. Aggarwal, S. Sathe. Theoretical foundations and algorithms for outlier ensembles. *ACM
  SIGKDD Explorations* 17(1):24–47, 2015. doi:10.1145/2830544.2830549.
- S. Axelsson. The base-rate fallacy and the difficulty of intrusion detection. *ACM TISSEC*
  3(3):186–205, 2000. doi:10.1145/357830.357849.
- R. F. Barber, E. J. Candès, A. Ramdas, R. J. Tibshirani. Conformal prediction beyond
  exchangeability. *Annals of Statistics* 51(2):816–845, 2023. doi:10.1214/23-AOS2276.
- S. Bates, E. Candès, L. Lei, Y. Romano, M. Sesia. Testing for outliers with conformal p-values.
  *Annals of Statistics* 51(1):149–178, 2023. doi:10.1214/22-AOS2244.
- Y. Benjamini, Y. Hochberg. Controlling the false discovery rate: a practical and powerful
  approach to multiple testing. *JRSS-B* 57(1):289–300, 1995. doi:10.1111/j.2517-6161.1995.tb02031.x.
- Y. Benjamini, D. Yekutieli. The control of the false discovery rate in multiple testing under
  dependency. *Annals of Statistics* 29(4):1165–1188, 2001. doi:10.1214/aos/1013699998.
- M. H. DeGroot, S. E. Fienberg. The comparison and evaluation of forecasters. *The Statistician*
  32(1/2):12–22, 1983. doi:10.2307/2987588 (metadata only).
- D. Donoho, J. Jin. Higher criticism for detecting sparse heterogeneous mixtures. *Annals of
  Statistics* 32(3):962–994, 2004. doi:10.1214/009053604000000265.
- I. J. Good. The population frequencies of species and the estimation of population parameters.
  *Biometrika* 40(3–4):237–264, 1953. doi:10.1093/biomet/40.3-4.237 (metadata only).
- C. Guo, G. Pleiss, Y. Sun, K. Q. Weinberger. On calibration of modern neural networks. *ICML*
  2017. arXiv:1706.04599.
- N. A. Heard, P. Rubin-Delanchy. Choosing between methods of combining p-values. *Biometrika*
  105(1):239–246, 2018. doi:10.1093/biomet/asx076.
- A. Javanmard, A. Montanari. Online rules for control of false discovery rate and false discovery
  exceedance. *Annals of Statistics* 46(2):526–554, 2018. doi:10.1214/17-AOS1559.
- H.-P. Kriegel, P. Kröger, E. Schubert, A. Zimek. Interpreting and unifying outlier scores. *Proc.
  SIAM SDM* 2011, pp. 13–24. doi:10.1137/1.9781611972818.2.
- R. Laxhammar. *Conformal Anomaly Detection: Detecting Abnormal Trajectories in Surveillance
  Applications*. PhD thesis, University of Skövde, 2014. ISBN 978-91-981474-2-1 (DiVA
  diva2:690997).
- R. Laxhammar, G. Falkman. Online learning and sequential anomaly detection in trajectories.
  *IEEE TPAMI* 36(6):1158–1173, 2014. doi:10.1109/TPAMI.2013.172 (metadata only).
- R. Laxhammar, G. Falkman. Inductive conformal anomaly detection for sequential detection of
  anomalous sub-trajectories. *Annals of Mathematics and Artificial Intelligence* 74(1–2):67–94,
  2015. doi:10.1007/s10472-013-9381-7 (metadata only).
- Y. Liu, J. Xie. Cauchy combination test: a powerful test with analytic p-value calculation under
  arbitrary dependency structures. *JASA* 115(529):393–402, 2020. doi:10.1080/01621459.2018.1554485.
- P. Massart. The tight constant in the Dvoretzky–Kiefer–Wolfowitz inequality. *Annals of
  Probability* 18(3):1269–1283, 1990. doi:10.1214/aop/1176990746 (metadata only).
- A. Niculescu-Mizil, R. Caruana. Predicting good probabilities with supervised learning. *ICML*
  2005, pp. 625–632. doi:10.1145/1102351.1102430 (metadata only).
- Z. Šidák. Rectangular confidence regions for the means of multivariate normal distributions.
  *JASA* 62(318):626–633, 1967. doi:10.1080/01621459.1967.10482935 (metadata only).
- V. Vovk, A. Gammerman, G. Shafer. *Algorithmic Learning in a Random World*. Springer, 2005.
  doi:10.1007/b106715 (metadata only).
- V. Vovk, R. Wang. Combining p-values via averaging. *Biometrika* 107(4):791–808, 2020.
  doi:10.1093/biomet/asaa027.
- R. Wang, A. Ramdas. False discovery rate control with e-values. *JRSS-B* 84(3):822–852, 2022.
  doi:10.1111/rssb.12489.
- D. J. Wilson. The harmonic mean p-value for combining dependent tests. *PNAS* 116(4):1195–1200,
  2019. doi:10.1073/pnas.1814092116.
- A. Zimek, R. J. G. B. Campello, J. Sander. Ensembles for unsupervised outlier detection:
  challenges and research questions. *ACM SIGKDD Explorations* 15(1):11–22, 2014.
  doi:10.1145/2594473.2594476.
