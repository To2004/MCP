# Dynamic Layer v2 — Idea and Implementation

Design notes for the runtime factor computed in
[`../reports/experiments/dynamic_layer/v2/`](../reports/experiments/dynamic_layer/v2/README.md).
This is intended to eventually **replace** the persona-based design currently
written into `main.tex` §4.3 (Dynamic Risk Adaptation) and §5.3 (Dynamic
Layer) — the deviation/anomaly/novelty ($D$, $A$, $N$) factors built from
per-persona behavioral profiles. That migration has not happened yet: the
paper still describes and implements $D/A/N$, unchanged. This file exists so
the idea and implementation are written down before that rewrite, without
touching the submission text in the meantime. It intentionally reports no
results — the last section of the source README is explicit that nothing
here has been evaluated against labeled misuse, only run on benign traffic.

## The idea

v1 folded runtime evidence into one blended multiplier. v2's premise is that
blending throws away information: a call can be unusual for a deployment in
two genuinely different ways, and conflating them into a single number makes
neither one legible or checkable on its own. v2 keeps them apart as two
independent factors over the same static cell, each answering a different
question and each cheap to justify in isolation.

The first factor, breadth, asks whether *this call's arguments* are narrower
than the worst case the static scan already priced. The scan's blast-radius
rating is deliberately the ceiling — "the reach of one call, or one call
misused" — so a call at the wide end is exactly what was already priced, and
only a demonstrably narrower one earns a discount. This is why breadth can
only move the score down, never up: letting it escalate would double-count
reach the static scan already accounted for. The mechanism is a per-parameter
grade (does a larger value mean more data reached, and how much), collapsed
across a tool's arguments by taking the most conservative one — a call wide
in any single dimension is not a narrow call, so one wide argument cancels
the discount regardless of how narrow the others are.

The second factor, likelihood, asks whether *this tool* is usual for this
deployment, and is allowed to move the score in either direction around a
neutral point of even usage across the tools the server exposes. Rarity
raises the score; commonness is deliberately given a smaller effect than
rarity, on purpose — an earlier symmetric version, where being common
discounted a call as much as being rare escalated one, measured net-negative
on all three test servers, because "this tool gets called a lot" is not
actually evidence that a given call is safe.

## The implementation

Both factors are computed with no model call and no network access on the
invocation path, preserving the same constraint the persona-based design in
§5.3 already commits to. The work that needs a model happens once, offline,
at scan time: every tool parameter is classified for what kind of quantity it
carries and how much stored data it alone can reach, and that classification
is cached as an artifact the runtime only reads. The likelihood factor needs
no model at all — it is a running count of calls per tool against the
deployment's own call history, smoothed with a small pseudocount so a
never-before-seen tool doesn't produce an undefined ratio. Because neither
factor touches a model or the network at request time, the combined
computation is fast enough to sit directly in front of the invocation: the
source README measures tens of microseconds per call and tens of thousands
of calls per second on the three test servers, which is a performance
characteristic of the implementation, not a claim about detection accuracy.

## What would need to change in the paper

Migrating `main.tex` to this design, if and when that happens, means
replacing §4.3's $D(c) \cdot A(c) \cdot N(c)$ formulation and §5.3's
persona-profile machinery (baseline deviation, access-anomaly qualifier,
sequence detection) with the breadth/likelihood formulation above. The two
designs are not compatible extensions of each other — v2 has no persona
state, no cross-call sequence signal, and no access-anomaly qualifier — so
this is a replacement of the section's content, not an additive edit. Do not
merge the two without deciding which one the paper is actually claiming.
