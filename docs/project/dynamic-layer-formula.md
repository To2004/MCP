# Dynamic Layer — The Calculation

How one call's score is computed, factor by factor, with a worked example carried all
the way through. Specification only: no results, no evaluation.

## The formula

```
final = min( score_max , max( cell(tool, asset) × likelihood × escalation , floor ) )
```

Four ingredients, each answering a different question:

| factor | the question it answers | range | who decides it |
|---|---|---|---|
| `cell(tool, asset)` | how bad would this be, if it went wrong? | 1 … 125 | the scan, at design time |
| `likelihood` | how normal is this action for this company? | 0.10 … 1.00 | observed history |
| `escalation` | is this call unusually large or small here? | 0.9 / 1.0 / 1.3 | observed history |
| `floor` | how far may a discount ever pull it down? | the cell's band bottom | the scan's band |

The shape matters: **only the cell can make a score large.** Likelihood can only shrink
it, escalation nudges it slightly either way, and the floor stops the shrinking. Nothing
in the runtime can invent risk that the scan did not already price.

---

## 1 · `cell` — the base

A table lookup, nothing more. The scan has already computed, for every (tool, resource)
pairing the server exposes:

```
cell = asset_sensitivity × blast_radius × tool_impact        1 … 125
```

The runtime never recomputes this. It reads the number and moves on.

**Bands** partition that range, and are used again later for the floor:

```
low  0–16      medium  17–49      high  50–99      critical  100–125
```

---

## 2 · `likelihood` — how normal is this action for this company?

**The idea.** If a company's agents call a tool constantly, this call is more of the
same, and the score should relax. If they almost never call it, the call keeps its full
weight. The measure is **share of traffic**, not raw count — an agent making ten
thousand calls should not thereby earn trust on all of them.

**Keyed on `(company, tool)`.** Not the individual agent, because agents are often
one-shot and never accumulate history. Not the asset, because the asset is already in
the cell.

### The three inputs

| symbol | meaning |
|---|---|
| `n` | how many calls this company has made so far |
| `c` | how many of those used *this* tool |
| `prior[t]` | this tool's share of the catalog, from the synthetic static corpus |
| `α = 30` | how much weight the catalog prior carries |
| `V` | how many tools the server exposes |

### The arithmetic

```
p     = (c + α × prior[t]) / (n + α)          blended share of traffic
s     = −log₂(p)                              "bits of surprise"
s_max = −log₂( 1 / (V + n) )                  the most surprising thing possible
ramp  = clamp(s / s_max, 0, 1)                0 = utterly routine, 1 = maximally novel
L     = 0.10 + 0.90 × ramp                    mapped into [0.10, 1.00]
```

**Why the prior term.** Without `α × prior[t]`, a brand-new deployment has `n = 0` and
the formula is undefined — the cold-start hole. Mixing in the catalog share means every
tool has some support from the very first call. `α = 30` is deliberately weak: after a
few dozen real calls, observation dominates.

**Why the logarithm.** Traffic shares span orders of magnitude. A tool that is 1-in-10
of traffic, one that is 1-in-100, and one that is 1-in-1000 should be evenly spaced in
suspicion, not crushed together near zero. The log does that. One bit means "half the
traffic"; seven bits means "about one call in 130".

**Why divide by `s_max`.** Bits are unbounded, and the maximum possible surprise grows
as history grows. Dividing by it makes the output comparable across servers and across
time.

**Why the floor of 0.10.** Even a completely routine action is not risk-free. The most
the term can ever do is remove 90 % of the cell's value.

---

## 3 · `escalation` — is this call unusually large for this deployment?

**The idea.** The same tool can be a pinprick or a demolition depending on its
arguments. But what counts as "large" is a property of the deployment, not of the tool:
a `limit` of 30 is unremarkable on one server and unheard of on another. So the
deployment's own history sets the cut points.

**Two numbers, three bins — Tukey's fences:**

```
Q1, Q3 = the 25th and 75th percentile of values this company has passed
IQR    = Q3 − Q1

lower  = Q1 − 1.5 × IQR
upper  = Q3 + 1.5 × IQR

value > upper        → 1.3      bigger than normal here
lower ≤ value ≤ upper → 1.0      ordinary
value < lower        → 0.9      smaller than normal here
```

**Why quartiles rather than mean and standard deviation.** Quartiles are rank-based, so
they assume no bell curve and are not dragged around by the very extreme values they
exist to find. One enormous call does not move Q1 or Q3.

**Why 1.5.** Tukey chose it so that, on well-behaved data, about **0.7 %** of values
fall outside the fences. The bin therefore fires rarely by construction — the score may
move, but not often and not by much.

**Which arguments qualify.** Only *quantities*: array lengths, and numerics the scan
gave a `critical_trigger`. Never identifiers — `pull_number` is a number, but PR #25 is
not "bigger" than PR #7, and binning it would manufacture risk from a meaningless order.

**Minimum history: 20 observations.** Below that there are no meaningful quartiles, and
the factor returns 1.0.

---

## 4 · `floor` — how far a discount may go

```
floor = the lower bound of the band the cell was in BEFORE anything moved it

cell 12  → low      → floor 0
cell 27  → medium   → floor 17
cell 60  → high     → floor 50
cell 110 → critical → floor 100
```

Two properties worth being explicit about:

- It is an **absolute score**, not a ratio, so escalation raising a call cannot also
  raise the floor beneath it.
- It is taken from the **pre-change** cell, so the band a call is protected in is the
  band the scan put it in.

The effect: the runtime may reorder calls *inside* a band, and may push a call *up* into
a higher one, but can never discount a call out of the band it started in.

---

## Worked example, with real numbers

A trial-coordinator agent at **vireo** calls `users_search` on the `user-directory`
resource with `{"query": "e", "limit": 19}`. The company has made 183 calls so far, 17
of them with this tool. The server exposes 16 tools.

**Step 1 — the cell.**

```
cell(users_search, user-directory) = 27          → medium band (17–49)
```

**Step 2 — likelihood.**

```
prior[users_search] = 0.01613                    (its share of the catalog corpus)

p     = (17 + 30 × 0.01613) / (183 + 30)
      = 17.484 / 213
      = 0.0821                                   ~8 % of this company's traffic

s     = −log₂(0.0821)   = 3.607 bits
s_max = −log₂(1 / 199)  = 7.637 bits
ramp  = 3.607 / 7.637   = 0.472
L     = 0.10 + 0.90 × 0.472 = 0.525
```

Reading: this tool is about 8 % of what vireo does — moderately common, so the call is
discounted to a little over half its cell value.

**Step 3 — escalation.**

```
limit = 19, and vireo's observed limits fall between the fences  → 1.0
```

**Step 4 — floor and final.**

```
floor = 17                                       (medium band's lower bound)

final = min(125, max(27 × 0.525 × 1.0, 17))
      = min(125, max(14.18, 17))
      = 17.00
```

**What happened.** The likelihood term wanted to pull the call from 27 down to 14.2 —
which would have dropped it out of medium into low. The floor stopped it at 17, the
bottom of its own band. The call is reported as **17, medium**.

This is the design working as intended: routine use is allowed to move a call *within*
its band, and is not allowed to argue it out of one.

---

## Constants, in one place

| constant | value | why |
|---|---|---|
| `score_max` | 125 | 5 × 5 × 5, the ceiling of the static formula |
| band thresholds | 17 / 50 / 100 | from the scan's `band_thresholds` |
| `α` (prior strength) | 30 | weak enough that real evidence dominates within a few dozen calls |
| likelihood floor | 0.10 | a routine action is still not risk-free |
| Tukey multiplier | 1.5 | ~0.7 % of well-behaved values fall outside |
| escalation bins | 0.9 / 1.0 / 1.3 | bounded both ways; the score may move, but not by much |
| minimum history for a bin | 20 | below this there are no meaningful quartiles |

## Order of operations

```
1. resolve the call to a (tool, resource) cell        → base score, and its band
2. look up the company's history                       → likelihood L ∈ [0.10, 1.00]
3. bin the call's magnitude arguments                  → escalation E ∈ {0.9, 1.0, 1.3}
4. multiply                                            → base × L × E
5. clamp below by the pre-change band's lower bound
6. clamp above by score_max
7. report the score and its band. Nothing is blocked.
```
