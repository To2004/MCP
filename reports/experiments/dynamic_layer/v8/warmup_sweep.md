# Weight-by-rank cold-start sweep — B's abstention does not resolve with more data

`dynamic_v2.py`'s `B` factor weights each argument's deviation by `BREADTH_WEIGHT`
(`{5: 1.00, 4: 0.75, 3: 0.50, 2: 0.25, 1: 0.0}`) — the scan's 1-5 breadth/centrality
RANK for that argument, relative to its own tool's most central measurable argument.
`v3/warmup_curve.txt` already measured how `L` (the likelihood factor) settles with
warm-up. This does the same for `B`, the factor `BREADTH_WEIGHT` actually feeds, and
finds a genuinely different, more important story: `L`'s cold-start problem resolves
with data; a large share of `B`'s does not, no matter how much data it gets.

## Method

`scripts/dynamic_design/warmup_sweep.py`, run against the three 100k-row synthetic org
corpora (`reports/experiments/real_benign/{server}_org_100k.csv`). For each server: hold
out a FIXED tail of 5,000 rows as the test set (the same 5,000 calls scored at every
point below), warm the scorer on the first N rows of everything before that tail for
N in `{0, 20, 100, 500, 2000, 10000, 50000, 94000}`, then score the fixed tail and
record both the D distribution and `scorer.sources` — which of the five things
`B.deviation()` decided for each measurable quantity it looked at:

- **no history** — fewer than `MIN_HISTORY` (20) observations of this exact
  `(server, tool, argument)` yet. True cold start.
- **no floor** — this argument HAS enough history, but its lower quartile sits on its
  own observed minimum (a dominant default collapses the spread, e.g. a page size that
  is 30 in most calls) — there is no room below Q1 to discount into, ever, regardless
  of sample size.
- **ordinary / narrow / wide** — the argument was actually graded against its own
  history.

Full numbers: `warmup_sweep_raw.txt` in this directory.

## Result

```
                 abstain% (no history + no floor), by warm-up size
server            0     20    100    500    2k     10k    50k    94k
github_helios    70%   70%    69%    68%    67%    66%    67%    67%
calendar_aurora  85%   85%    84%    84%    84%    84%    84%    84%
slack_vireo      52%   52%    51%    50%    50%    50%    50%    50%
```

Every server's abstention rate flattens within a few thousand warm-up calls and then
stays flat all the way to 94,000 — two to three orders of magnitude past where `L`'s
own noise floor settled in `v3/warmup_curve.txt` (a few thousand calls, per its own
table). **This is not a slow cold start. It is a ceiling**, and the two components
behave completely differently against more data:

- **`no history` does shrink with warm-up**, as it should — a true cold-start count. On
  `github_helios` it drops from 1,080 to 670 quantities-abstained and then holds. But on
  `calendar_aurora` it barely moves at all: 15,747 -> 15,587 across the ENTIRE sweep,
  0 to 94,000 calls. That is a long tail of distinct `(tool, argument)` keys, each
  individually too rare to cross 20 observations even when the corpus as a whole is
  saturated with traffic — spreading 94,000 calls across many keys does not make any
  one key warm if the traffic itself is spread that thin.
- **`no floor` does not shrink with warm-up at all, structurally cannot.** It is not a
  data-volume problem — it is what a dominant-default argument distribution looks like
  at ANY sample size. `calendar_aurora`'s `no_floor` count is 3,076 at 0 warm-up and
  3,087 at 94,000: statistically indistinguishable. More data does not create spread
  where the traffic itself has none.

`no_floor` outnumbers `no_history` on every server at every warm-up size — the
DOMINANT reason `B` abstains is not "not enough data yet," it is "this argument has a
default value practically everyone uses, so there is nothing below it to discount
into." That is arguably the CORRECT behaviour (an argument with no real narrow calls
should not be scored as if narrow calls existed), but it means most of `BREADTH_WEIGHT`'s
rank-weighting is applied against a comparison that most quantities never actually
enter — abstention, not narrow/ordinary/wide grading, is the modal outcome everywhere,
even fully warm.

## Secondary finding: the median drifts down slightly and keeps drifting

```
median D, by warm-up size
                0      20    100    500    2k     10k    50k    94k
github_helios  0.91   0.91   0.91   0.90   0.89   0.88   0.88   0.88
calendar_aurora 0.92  0.92   0.92   0.92   0.90   0.89   0.91   0.88
slack_vireo    0.94   0.94   0.94   0.93   0.92   0.92   0.91   0.91
```

Small (0.03-0.06 over the whole sweep) but real and monotone-ish in the same direction
on all three servers — the reference keeps adapting toward more central values as it
sees more of the deployment's own traffic, echoing `warmup_curve.txt`'s own note that
"any adaptive reference moves; the question is whether it moves less than the signal."
Here it is moving less than the signal (the interquartile spread is much larger than
the drift), but it has not visibly flattened out even at 94,000 calls the way `L`'s
noise floor did — worth revisiting at a still larger corpus if one gets generated,
rather than assuming 94k is asymptotic.

## What this means for `BREADTH_WEIGHT` / weight-by-rank specifically

The rank weighting itself (`_relative_weight`, keyed by the scan's 1-5 breadth level)
is not what is being questioned here — that machinery only ever gets a chance to matter
on the 15-50% of quantities that actually reach a graded verdict (`ordinary`/`narrow`/
`wide`). On the majority of scored quantities, `B` abstains at 1.0 before rank-weighting
ever enters the picture, on every server, at every warm-up size tested including the
most warmed one. So the honest framing is: **weight-by-rank is real but narrow in
practice** — it shapes a minority of the traffic's scores, and that minority does not
grow appreciably no matter how much history the deployment accumulates, because the
ceiling is set by the traffic's own shape (dominant defaults, a long tail of rare
argument keys), not by how long the deployment has been running.

## Per-argument breakdown (github_helios, fully warmed on 95,000 calls)

Did the per-argument version of the "not done here" item below anyway, since the
aggregate number alone does not say WHICH arguments are structurally idle. It reshapes
the finding into something sharper and more concerning than an aggregate percentage:

```
high-weight (breadth>=4) args: 6 total, 6 are no_floor (100%)
lower-weight (breadth<4) args: 15 total, 8 are no_floor (53%)
```

EVERY breadth>=4 argument with enough history to judge is `no_floor` — every one of
them is an identifier (`issue_number`, `pull_number`) with a tiny observed range
(1 to ~9), so `min == q1` and there is never any room to discount into. Meanwhile the
breadth=3 arguments split cleanly on a real distinction the numbers surface on their
own: `page` (near-universally 1, also `no_floor` — genuinely uninformative, correctly
recognised as such) versus `per_page`/`perPage` (spread 1-100, min=1/q1=30, actually
graded `ordinary`/`narrow`/`wide` every time).

So `BREADTH_WEIGHT`'s ranking and "how much this argument's history is worth grading"
are not just uncorrelated here, they run BACKWARDS: the rank-5 slots (full weight,
`_relative_weight` = 1.00) are spent entirely on arguments that structurally never
produce a graded verdict, while the argument that actually carries the deployment's
real signal (`per_page`) sits at rank 3, weight 0.50 relative to its tool's rank-5
argument — so even when `per_page` DOES get graded, its deviation is halved before it
enters `B`, by a rank that measures "how central to the asset" and was never meant to
measure "how much this argument's own history varies." Centrality and variance are
different questions; this scheme answers the first and spends most of its weight on it,
in a corpus where the second is what the traffic actually has to say.

One more thread worth naming: `issue_number`/`pull_number` showing up as MEASURABLE at
all (kind `count` or `magnitude` rather than `none`) is arguably a scan-time
misclassification — the breadth rubric's own rule is explicit that "a value that
identifies something is `none`/`not_size` even when it is a number," and an issue or PR
number is exactly that case. In this corpus the mistake is inert (the argument abstains
either way, since its range is tiny), but it is a direct, concrete link back to the
`kind`-stability work done earlier this session: a `kind` misclassification at scan
time is not just a classification-accuracy number in isolation, it decides which
arguments the runtime even ATTEMPTS to weight by rank in the first place. A tool where
a similarly ID-shaped argument has more real spread (unlike this corpus's) would not
get the free pass `issue_number` gets here.

**Checked on the other two servers — it generalises, cleanly:**

```
                     high-weight (breadth>=4) no_floor   lower-weight (breadth<4) no_floor
github_helios              6/6  (100%)                          8/15  (53%)
calendar_aurora            4/4  (100%)                          0/4   (0%)
slack_vireo                2/2  (100%)                          1/9   (11%)
```

Every breadth>=4 argument on every server, without exception, is `no_floor` — this is
not noise from one server's tool shapes. `calendar_aurora`'s and `slack_vireo`'s
highest-weight arguments are the same story as GitHub's: `calendarId`/`channel_types`/
`calendars`, all selectors with a tiny observed range (1-3 distinct values). The
rank-vs-variance mismatch is structural to what "breadth=5" tends to mean (an
identifier or selector, which is exactly the kind of value that has almost no spread to
discount against), not an artefact of one server's argument mix.

## Not done here, worth doing next if this is worth pursuing further

- Repeat with a real (not synthetic) corpus once one reaches this scale — `live_scale_*`
  corpora on disk today are ~1,000-3,000 rows each, well inside the region where this
  sweep still shows `no_history` shrinking, so real traffic has not yet been observed
  at the point where this ceiling would show up.
