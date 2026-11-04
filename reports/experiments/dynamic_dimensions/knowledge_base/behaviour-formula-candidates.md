# Behaviour multiplier: six candidate formulas compared

> **2026-10-29 update.** The author chose to count calls for now: candidate J in
> [dynamic-score-report.md](dynamic-score-report.md) §4, which also gives 10-seed intervals. This
> note's recommendation, F (days), is the planned improvement.

This note compares six formulas for the dynamic multiplier M on the six agreed dimensions. It
reports what a simulation and the literature say about each, and recommends one. All six score a
call against the same agent id's own history, and M multiplies the static score.

- **Date:** 2026-10-29.
- **Data:** every number comes from [probes/m_formula_candidates.py](probes/m_formula_candidates.py),
  except the rows marked "literature toy case". Synthetic data only: these are design checks, not
  paper results.

## The six dimensions

| Group | Dimension | More unusual means |
|---|---|---|
| Typical Footprint | Tool | used more rarely by this agent |
| | Asset | touched more rarely by this agent |
| | Tool on asset | this tool used more rarely on this asset |
| Typical Cadence | Calls this hour | more calls in the hour than usual (in doublings) |
| | Breadth | more distinct tool-and-asset pairs in the hour than usual (in doublings) |
| | Time of day | an hour the agent rarely works |

## The candidates

| | Candidate | In one line |
|---|---|---|
| A | The deck's dimension slides (v4) | an excess score for amounts and a "times per day" rarity score for categories; the strangest dimension wins; M = 5^(2s−1) or 0.7^(1−2s) |
| B | The deck's formal model, with one fix | per dimension, M = (Baseline / Likelihood)^γ with an add-one likelihood, counted on calls; the strangest dimension wins. The fix: a ratio instead of exp(Baseline − Likelihood) |
| C | Product of ratios (naive Bayes, as in risk-based login checks) | B's ratios multiplied over all dimensions |
| D | Rank on calls | how many of the agent's past calls were at least as unusual: M = ((H+1)/(2D+1))^γ |
| E | Rank on days | the same, but each past day counts once |
| F | E with Tool on asset per asset | E, with Tool on asset as "how often this tool, among the days this asset was used" |

## Results: 19 scenarios, 7 kinds of agent, 125 checks per seed

| Candidate | Stay quiet (53) | One unusual thing (44) | Several at once (14) | Expected to get through (14) | Total, seeds 101 / 202 / 303 |
|---|---|---|---|---|---|
| A deck slides (v4) | 43 | 23-26 | 0 | 14 | 80 / 80 / 83 |
| B deck model, fixed | 15-17 | 36-38 | 14 | 13-14 | 80 / 79 / 83 |
| C product of ratios | 8-10 | 27-30 | 14 | 13-14 | 64 / 63 / 68 |
| D rank on calls | 18-21 | 35-38 | 14 | 13-14 | 84 / 81 / 87 |
| E rank on days | 46-48 | 36-41 | 14 | 13-14 | 111 / 115 / 115 |
| **F days, Tool on asset per asset** | **48-50** | **40-44** | **14** | **13-14** | **117 / 120 / 122** |

## What matters most

1. **The unit: count days, not calls.** This is the biggest effect: D to E gains 27-34 checks.
   With calls as the unit:
   - ordinary days look unusual (median ×1.5-2.0, against ×0.9 for days);
   - a new tool used daily for two weeks still scores ×2.3-2.6;
   - one huge burst day teaches the agent that bursts are normal, so a later burst scores ×1.1;
   - in the literature toy case (1,000 calls a day), a tool used once every day scores ×2.4 on
     every use, against ×0.78 when counting days.
2. **Rank the whole call.** D, E and F reach ×5 when several things are unusual at once and stay
   calibrated. A can never reach ×5 (0 of 14), because its scores stay below 1. B and C rise
   on ordinary days: B takes the maximum of six uncorrected scores, and C counts nested
   dimensions twice (a new tool on a new asset is also a new pair).
3. **Tool on asset per asset.** From E to F, a known resource used with a new action goes from
   ×1.5-1.7 to ×5, and nothing else gets worse.

## What the literature says

- **Days, not events, is the standard unit for this question:**
  - Insider-threat work and enterprise log analysis use user-days, sessions or host-days: Le et
    al., IEEE TNSM 2020; Tuor et al., AICS 2017; Beehive, ACSAC 2013.
  - Elastic's rare functions model whether something happens in a time bucket at least once.
  - SRI's NIDES (Javitz and Valdes, 1994) notes that 1,000 audit records in a day "are not
    independent". It also treats the false-alarm rate per day as the one that matches analyst
    effort.
  - The analogy for the paper is document frequency in text retrieval: a word that appears once
    tends to repeat inside the same document, so inverse document frequency counts documents, not
    occurrences (Church and Gale 1995; Madsen et al., ICML 2005). Here a day plays the role of the
    document.
- **Event counting works when events are sparse,** as in logins: Freeman et al., NDSS 2016 count
  logins, and a user has a median of 2 (Wiefling et al., ACM TOPS 2022). Agent calls are dense.
- **Product of ratios:** Freeman et al. state that the independence assumption "does not hold in
  practice". Naive Bayes ranks well but gives poor probabilities (Domingos and Pazzani 1997).
- **Maximum:** false alarms grow with the number of dimensions (Heard and Rubin-Delanchy,
  Biometrika 2018).
- **Rank:** it stays valid under any dependence between dimensions (Bates et al., Annals of
  Statistics 2023; Laxhammar 2014).
- **Baseline / Likelihood** is a recognised form: density relative to a reference measure
  (Steinwart, Hush and Scovel, JMLR 2005). The add-one likelihood is standard (Jurafsky and
  Martin, SLP3 §3.6.1). **No precedent was found for exp(Baseline − Likelihood).** It always stays
  between ×0.37 and ×2.7, and near ×1 once a dimension has 20 or more values, so the deck's
  formula needs the ratio fix whichever candidate is chosen.

## Recommendation: F

```text
A = the agent's active days in the last 90
D = how many of those days were at least as unusual as this call
    (compare the call's most unusual dimension first, then the next)
M = ((A + 1) / (2D + 1))^γ ,   γ = ln 5 / ln(91)
```

The paper sentence: *for each call we ask on how many of this agent's past days it did something
at least this unusual. Never in 90 days gives ×5; half of its days gives ×1.*

A day is not a dimension. It is the unit we count in, as a document is in inverse document
frequency.

**Where F still misses** (5-8 of 125 per seed):
- **A low-volume agent** (the SQLite one) scores ×3.38 on a busy day and on three extra calls,
  because a few extra calls are already a doubling. The open fix is to ignore doublings below
  about 4 calls.
- **An agent with very uneven volume** hides bursts inside its own wild days. That is correct for
  it.
- **Borderline single cases:** one explorer case at ×2.0, and one ordinary day in ten at ×3.

**What a reviewer will attack:**
- the coarse top (×5, ×3.38, ×2.82);
- dilution as dimensions are added;
- weekly cycles and drift;
- partial days;
- a fresh id reaches only ×1.28 after one day.

## References

Status of each source:
- read in full: Freeman et al. NDSS 2016; Beehive ACSAC 2013; NIDES (SRI 1994); Elastic ML
  documentation; Steinwart et al. JMLR 2005; Jurafsky and Martin SLP3; Madsen et al. ICML 2005;
- abstract only: Church and Gale 1995; Domingos and Pazzani 1997; Kloft and Laskov JMLR 2012;
- checked earlier in note 03 or note 04: all the others.

- S. Bates, E. Candès, L. Lei, Y. Romano, M. Sesia. Testing for outliers with conformal p-values.
  *Annals of Statistics* 51(1), 2023.
- K. W. Church, W. A. Gale. Poisson mixtures. *Natural Language Engineering* 1(2), 1995.
- P. Domingos, M. Pazzani. On the optimality of the simple Bayesian classifier under zero-one loss.
  *Machine Learning* 29, 1997.
- D. M. Freeman, S. Jain, M. Dürmuth, B. Biggio, G. Giacinto. Who are you? A statistical approach
  to measuring user authenticity. NDSS 2016.
- N. A. Heard, P. Rubin-Delanchy. Choosing between methods of combining p-values. *Biometrika*
  105(1), 2018.
- H. S. Javitz, A. Valdes. The NIDES statistical component: description and justification. SRI
  International, 1994.
- D. Jurafsky, J. H. Martin. *Speech and Language Processing*, 3rd ed. draft, §3.6.1.
- R. Laxhammar. *Conformal Anomaly Detection*. PhD thesis, University of Skövde, 2014.
- D. C. Le, N. Zincir-Heywood, M. I. Heywood. Analyzing data granularity levels for insider threat
  detection using machine learning. *IEEE TNSM* 17(1), 2020.
- R. E. Madsen, D. Kauchak, C. Elkan. Modeling word burstiness using the Dirichlet distribution.
  ICML 2005.
- I. Steinwart, D. Hush, C. Scovel. A classification framework for anomaly detection. *JMLR* 6,
  2005.
- A. Tuor, S. Kaplan, B. Hutchinson, N. Nichols, S. Robinson. Deep learning for unsupervised
  insider threat detection in structured cybersecurity data streams. AICS 2017.
- S. Wiefling, M. Dürmuth, L. Lo Iacono. What's in score for website users: a data-driven long-term
  study on risk-based authentication characteristics. *ACM TOPS*, 2022.
- T.-F. Yen et al. Beehive: large-scale log analysis for detecting suspicious activity in
  enterprise networks. ACSAC 2013.
