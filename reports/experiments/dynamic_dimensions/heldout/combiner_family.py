"""EV-20: the matched-budget combiner family, recomputed offline from a score log.

Spec section 6.7 tests v5's weighted minimum of commonness against other ways to combine the
same per-dimension evidence. Each arm turns one call's evidence into one number (higher is
stranger); an agent-day takes its calls' maximum; every arm gets its own threshold, fitted on
the calibration pool's unlabelled agent-days at each alpha
(:func:`heldout_metrics.fit_threshold`), and applies it unchanged to the test pool. Arms are then
compared at matched false-alarm cost on credited recall and on the Hyp1 endpoint (Hyp4).

Per call the arms read (:class:`CallEvidence`):

- ``scores``: the raw per-dimension scores s_d (``Verdict.scores``), NaN where d took no part;
- ``rates``: the commonness q_d (``Verdict.rates``), NaN where none;
- per dimension its name, group and budget share w_d (NaN for a watch-only dimension).

Arms on scores: mean, noisy-OR, soft-OR (a = 0.1, 0.3, 0.5), top-2 mean, group-AOM, Thresh.
Arms on ranks: v5 (weighted Bonferroni: q = min_d q_d / w_d, s1 = 1 / (1 + 2 q)), Tippett,
harmonic mean and Cauchy, plus leave-one-dimension-out and leave-one-group-out ablations of v5
(shares fixed, never renormalised).

**Footprint enters the rank arms only as a rank** (spec 6.7). Under D3 (a) its q_d already is
one, with its budget share. Under D3 (b) it is watch-only for v5, but Tippett, harmonic mean and
Cauchy still take its rank, weighted by an equal split of the third it leaves unspent
(:attr:`CallEvidence.rank_weights`); only Missing handshake, watch-only under every D3, stays out.
A dimension with a score but no rate (v4 vectors) is rank-transformed first against a reference
sample (:func:`with_rank_fallback`, R2-11).

**No floors.** Floors sit outside the statistic and are the same for every arm, so every arm,
the ``v5`` arm included, is the statistic alone: the ``v5`` arm is s1 of q_stat, not the shipped
s1 = 1/(1 + 2 min(q_stat, q_floor)) that the Hyp1 endpoint scores. Hyp4
(:func:`hyp4_noninferiority`) therefore compares combiners, not the shipped engine.

Every number from a simulator world is a development-world or synthetic number until it comes
from a frozen held-out run.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from mcp_security.behaviour.engine import (
    READ_VOLUME,
    RED_FLAGS,
    TYPICAL_FOOTPRINT,
    WATCH_CAP,
    BehaviourConfig,
    budget_share,
    dimension_groups,
)

try:  # imported as part of the heldout package (tests, other harness modules)
    from . import heldout_metrics as hm
    from . import heldout_stats as hs
except ImportError:  # run as a script: the sibling modules are on sys.path
    import heldout_metrics as hm  # type: ignore[no-redef]
    import heldout_stats as hs  # type: ignore[no-redef]

# ── frozen constants ─────────────────────────────────────────────────────────────────────────
WATCH_FACTOR = 12.0  # CAL-3: a watch-only term's v_d = max(12 q_d, 2/15)
EDGE_OF_ORDINARY = 0.5  # s = 0.5 is ordinary; Thresh and noisy-OR count only the excess
SOFT_OR_WEIGHTS = (0.1, 0.3, 0.5)  # soft-OR: s1 + a s2 (1 - s1)
ALPHAS = hm.STATED_ALPHAS
ARM_V5 = "v5"
ARM_MEAN = "mean"
ARM_NOISY_OR = "noisy_or"
ARM_TOP2 = "top2_mean"
ARM_GROUP_AOM = "group_aom"
ARM_THRESH = "thresh"
ARM_TIPPETT = "tippett"
ARM_HARMONIC = "harmonic_mean"
ARM_CAUCHY = "cauchy"
SOFT_OR_PREFIX = "soft_or_"
LODO_PREFIX = "lodo:"  # leave one dimension out
LOGO_PREFIX = "logo:"  # leave one group out
TWO = 2  # the top-two arms read the two largest scores
RANK_FLOOR = 1e-300  # a rank is never 0 (add-one); guards log(0) in hand-made inputs


# ── evidence ─────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CallEvidence:
    """Per-call, per-dimension evidence from a score log (calls x dimensions)."""

    scores: np.ndarray  # s_d, NaN where d took no part
    rates: np.ndarray  # q_d, NaN where none
    names: tuple[str, ...]
    groups: tuple[str, ...]  # each dimension's group
    shares: np.ndarray  # w_d; NaN for a watch-only dimension

    def __post_init__(self) -> None:
        d = len(self.names)
        if self.scores.ndim != 2 or self.scores.shape[1] != d:
            raise ValueError(f"scores must be calls x {d}, not {self.scores.shape}")
        if self.rates.shape != self.scores.shape:
            raise ValueError("rates and scores must have one shape")
        if len(self.groups) != d or self.shares.shape != (d,):
            raise ValueError("names, groups and shares must give one entry per dimension")
        finite = self.rates[~np.isnan(self.rates)]
        if ((finite <= 0) | (finite > 1)).any():
            raise ValueError("a commonness q_d must lie in (0, 1]")

    @property
    def n_calls(self) -> int:
        """Number of calls."""
        return self.scores.shape[0]

    @property
    def rank_weights(self) -> np.ndarray:
        """Per dimension: its weight in the rank arms (Tippett, harmonic mean, Cauchy), NaN to
        leave it out (spec 6.7, R2-11).

        A dimension with a budget share keeps it. A Typical Footprint dimension without one
        (watch-only under D3 (b)) gets an equal split of the budget the shares leave unspent,
        which is Footprint's third, so Footprint enters as a rank under either D3 (1/12 each
        with v5's defaults). Every other dimension without a share (Missing handshake) stays
        out. ``ValueError`` when Footprint has no share and the shares leave no budget.
        """
        w = self.shares.astype(np.float64).copy()
        silent = np.isnan(w) & (np.array(self.groups) == TYPICAL_FOOTPRINT)
        if silent.any():
            unspent = 1.0 - float(np.nansum(w))
            if unspent <= 0:
                raise ValueError("Footprint is watch-only, but the shares leave it no budget")
            w[silent] = unspent / int(silent.sum())
        return w


def layout(config: BehaviourConfig) -> tuple[tuple[str, ...], tuple[str, ...], np.ndarray]:
    """The dimensions a config scores, their groups and budget shares (NaN: watch-only), in
    the design document's order. v5 defaults: 16 dimensions, 1/21 Cadence, 1/12 the rest.
    ``ValueError`` for a config without budget shares (v1-v4)."""
    if config.budget_shares is None:
        raise ValueError(f"design {config.design} has no budget shares (CAL-3)")
    names, groups, shares = [], [], []
    for group, dims in dimension_groups(config.design).items():
        for dim in dims:
            if dim == READ_VOLUME and not config.reply_volume:
                continue  # Read volume takes no part with its switch off (AI-8)
            share = budget_share(config, dim)
            names.append(dim)
            groups.append(group)
            shares.append(math.nan if share is None else share)
    return tuple(names), tuple(groups), np.array(shares)


def evidence_from_verdicts(
    scores: Sequence[Mapping[str, float]],
    rates: Sequence[Mapping[str, float]],
    names: Sequence[str],
    groups: Sequence[str],
    shares: ArrayLike,
) -> CallEvidence:
    """Build :class:`CallEvidence` from per-call dicts (``Verdict.scores``, ``Verdict.rates``);
    keys outside ``names`` (a design's other entries) are left out."""
    if len(scores) != len(rates):
        raise ValueError("scores and rates must give one dict per call")
    index = {name: i for i, name in enumerate(names)}
    s = np.full((len(scores), len(names)), np.nan)
    q = np.full_like(s, np.nan)
    for row, (sd, qd) in enumerate(zip(scores, rates, strict=True)):
        for name, value in sd.items():
            if name in index:
                s[row, index[name]] = value
        for name, value in qd.items():
            if name in index:
                q[row, index[name]] = value
    return CallEvidence(s, q, tuple(names), tuple(groups), np.asarray(shares, dtype=np.float64))


def rank_transform(values: ArrayLike, reference: ArrayLike) -> np.ndarray:
    """Add-one upper-tail rank of each value among a reference sample (higher = stranger):
    (1 + #{reference >= v}) / (n + 1), a conformal p-value under exchangeability."""
    ref = np.sort(np.asarray(reference, dtype=np.float64))
    ref = ref[~np.isnan(ref)]
    v = np.asarray(values, dtype=np.float64)
    at_least = len(ref) - np.searchsorted(ref, v, side="left")
    return (1 + at_least) / (len(ref) + 1)


def with_rank_fallback(evidence: CallEvidence, reference: Mapping[str, ArrayLike]) -> CallEvidence:
    """Fill a missing commonness from the score's rank in ``reference[dimension]`` wherever a
    dimension scored but carries no rate (Footprint under D3 (b), or v4 vectors). Pass the
    calibration pool's agent-day maxima of that dimension as the reference."""
    rates = evidence.rates.copy()
    for name, ref in reference.items():
        if name not in evidence.names:
            raise ValueError(f"unknown dimension {name!r}")
        col = evidence.names.index(name)
        rows = np.isnan(rates[:, col]) & ~np.isnan(evidence.scores[:, col])
        rates[rows, col] = rank_transform(evidence.scores[rows, col], ref)
    return CallEvidence(evidence.scores, rates, evidence.names, evidence.groups, evidence.shares)


def footprint_dimensions(evidence: CallEvidence) -> tuple[str, ...]:
    """The evidence's Typical Footprint dimensions (the ones R2-11 makes ranks)."""
    return tuple(
        n for n, g in zip(evidence.names, evidence.groups, strict=True) if g == TYPICAL_FOOTPRINT
    )


# ── the v5 statistic and its ablations ───────────────────────────────────────────────────────
def v5_statistic(
    evidence: CallEvidence,
    *,
    drop: Sequence[str] = (),
    watch_cap: float = WATCH_CAP,
    watch_factor: float = WATCH_FACTOR,
) -> np.ndarray:
    """q_stat per call (CAL-3): the minimum over the dimensions that took part of v_d, which is
    q_d / w_d for an alerting dimension and max(12 q_d, 2/15) for a watch-only one. Dimensions
    in ``drop`` are left out; shares are never renormalised. inf when nothing took part."""
    unknown = set(drop) - set(evidence.names)
    if unknown:
        raise ValueError(f"unknown dimensions {sorted(unknown)}")
    keep = np.array([n not in drop for n in evidence.names])
    if not keep.any():
        raise ValueError("every dimension was dropped")
    return _budget_rates(evidence, watch_cap, watch_factor)[:, keep].min(axis=1)


def _budget_rates(evidence: CallEvidence, watch_cap: float, watch_factor: float) -> np.ndarray:
    """Calls x dimensions: v_d (q_d / w_d, or the watch-only price), inf where d took no part."""
    q, w = evidence.rates, evidence.shares
    alerting = ~np.isnan(w)
    with np.errstate(invalid="ignore", divide="ignore"):
        v = np.where(
            alerting, q / np.where(alerting, w, 1.0), np.maximum(watch_factor * q, watch_cap)
        )
    return np.where(np.isnan(q), np.inf, v)


def _min_without_each(v: np.ndarray) -> np.ndarray:
    """Rows x columns: each row's minimum over every column but that one (from the smallest
    and second-smallest entry, so all leave-one-out minima cost one pass)."""
    rows = np.arange(v.shape[0])
    first = v.argmin(axis=1)
    rest = v.copy()
    rest[rows, first] = np.inf
    out = np.repeat(v[rows, first][:, None], v.shape[1], axis=1)
    out[rows, first] = rest.min(axis=1)
    return out


def s1_of(q: ArrayLike) -> np.ndarray:
    """s1 = 1 / (1 + 2 q); -inf where nothing took part (q = inf)."""
    q = np.asarray(q, dtype=np.float64)
    return np.where(np.isinf(q), -np.inf, 1.0 / (1.0 + 2.0 * np.where(np.isinf(q), 0.0, q)))


# ── arms on scores ───────────────────────────────────────────────────────────────────────────
def _taking_part(evidence: CallEvidence) -> tuple[np.ndarray, np.ndarray]:
    s = evidence.scores
    part = ~np.isnan(s)
    return np.where(part, s, 0.0), part


def _top_two(evidence: CallEvidence) -> tuple[np.ndarray, np.ndarray]:
    s = np.where(np.isnan(evidence.scores), -np.inf, evidence.scores)
    if s.shape[1] < TWO:
        return s[:, 0], np.full(s.shape[0], -np.inf)
    top = -np.sort(-s, axis=1)[:, :TWO]
    return top[:, 0], top[:, 1]


def mean_arm(evidence: CallEvidence) -> np.ndarray:
    """Mean of s_d over the dimensions that took part."""
    s, part = _taking_part(evidence)
    n = part.sum(axis=1)
    return np.where(n > 0, s.sum(axis=1) / np.maximum(n, 1), -np.inf)


def noisy_or_arm(evidence: CallEvidence) -> np.ndarray:
    """Noisy-OR on the excess over ordinary: 1 - prod_d (1 - max(0, 2 s_d - 1))."""
    s, part = _taking_part(evidence)
    excess = np.clip(2 * s - 1, 0.0, 1.0) * part
    out = 1.0 - np.prod(1.0 - excess, axis=1)
    return np.where(part.any(axis=1), out, -np.inf)


def soft_or_arm(evidence: CallEvidence, weight: float) -> np.ndarray:
    """Soft-OR of the two largest scores: s1 + a s2 (1 - s1), with s2 = 0 when only one."""
    s1, s2 = _top_two(evidence)
    s2 = np.where(np.isinf(s2), 0.0, s2)
    none = np.isinf(s1)
    s1 = np.where(none, 0.0, s1)
    return np.where(none, -np.inf, s1 + weight * s2 * (1 - s1))


def top2_mean_arm(evidence: CallEvidence) -> np.ndarray:
    """Mean of the two largest scores (the one score when only one took part)."""
    s1, s2 = _top_two(evidence)
    return np.where(np.isinf(s2), s1, (s1 + s2) / TWO)


def group_aom_arm(evidence: CallEvidence) -> np.ndarray:
    """Average of maxima: the largest score within each group, averaged over the groups that
    took part."""
    s = np.where(np.isnan(evidence.scores), -np.inf, evidence.scores)
    labels = np.array(evidence.groups)
    peaks = np.stack([s[:, labels == g].max(axis=1) for g in dict.fromkeys(evidence.groups)], 1)
    finite = np.isfinite(peaks)
    n = finite.sum(axis=1)
    total = np.where(finite, peaks, 0.0).sum(axis=1)
    return np.where(n > 0, total / np.maximum(n, 1), -np.inf)


def thresh_arm(evidence: CallEvidence) -> np.ndarray:
    """Thresh: the sum of the excess over ordinary, sum_d max(0, s_d - 0.5)."""
    s, part = _taking_part(evidence)
    out = (np.clip(s - EDGE_OF_ORDINARY, 0.0, None) * part).sum(axis=1)
    return np.where(part.any(axis=1), out, -np.inf)


# ── arms on ranks ────────────────────────────────────────────────────────────────────────────
def _rank_inputs(evidence: CallEvidence) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Ranks of the dimensions with a rank weight (:attr:`CallEvidence.rank_weights`), a
    taking-part mask and the weights, renormalised per call over the dimensions that took
    part."""
    weight = evidence.rank_weights
    ranked = ~np.isnan(weight)
    q = evidence.rates[:, ranked]
    part = ~np.isnan(q)
    w = np.where(part, weight[ranked], 0.0)
    total = w.sum(axis=1, keepdims=True)
    weights = np.divide(w, total, out=np.zeros_like(w), where=total > 0)
    return np.clip(np.where(part, q, 1.0), RANK_FLOOR, 1.0), part, weights


def tippett_arm(evidence: CallEvidence) -> np.ndarray:
    """Tippett: p = 1 - (1 - min_d q_d)^k over the k ranked dimensions that took part;
    the arm is -log p."""
    q, part, _ = _rank_inputs(evidence)
    k = part.sum(axis=1)
    q_min = np.where(part, q, 1.0).min(axis=1)
    below = q_min < 1.0  # q_min = 1 gives p = 1 (and log1p(-1) would be -inf)
    p = np.ones_like(q_min)
    p[below] = -np.expm1(k[below] * np.log1p(-q_min[below]))
    return np.where(k > 0, -np.log(np.maximum(p, RANK_FLOOR)), -np.inf)


def harmonic_mean_arm(evidence: CallEvidence) -> np.ndarray:
    """Weighted harmonic mean p (weights from the rank weights): 1 / sum_d (w_d / q_d);
    the arm is -log of it."""
    q, part, weights = _rank_inputs(evidence)
    inverse = (weights / q).sum(axis=1)
    return np.where(part.any(axis=1), np.log(np.maximum(inverse, RANK_FLOOR)), -np.inf)


def cauchy_arm(evidence: CallEvidence) -> np.ndarray:
    """Cauchy combination: T = sum_d w_d tan((0.5 - q_d) pi) over the d ranked dimensions that
    took part, weights from the rank weights; larger T is stranger (p = 1/2 - arctan(T) / pi).

    Each q_d is first capped at d/(d + 1), the mean of the largest of d uniform ranks. Under
    add-one commonness q_d = 1 is the usual value of an ordinary dimension (every past day was
    at least as strange), and uncapped it sends tan to -1.6e16, so the call would rank by how
    many dimensions sit at 1 instead of by its evidence. The term is computed as
    w_d / tan(pi q_d), the same value, which equals w_d / (pi q_d) to machine precision for a
    very small q_d.
    """
    q, part, weights = _rank_inputs(evidence)
    d = part.sum(axis=1, keepdims=True)
    capped = np.minimum(q, d / (d + 1))
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(part, weights / np.tan(math.pi * capped), 0.0)
    return np.where(part.any(axis=1), terms.sum(axis=1), -np.inf)


def arm_scores(evidence: CallEvidence, *, ablations: bool = True) -> dict[str, np.ndarray]:
    """Every arm's per-call score (higher = stranger, -inf: nothing took part). With
    ``ablations``, also v5 leaving one dimension out and one group out."""
    v = _budget_rates(evidence, WATCH_CAP, WATCH_FACTOR)
    out = {
        ARM_V5: s1_of(v.min(axis=1)),
        ARM_MEAN: mean_arm(evidence),
        ARM_NOISY_OR: noisy_or_arm(evidence),
        ARM_TOP2: top2_mean_arm(evidence),
        ARM_GROUP_AOM: group_aom_arm(evidence),
        ARM_THRESH: thresh_arm(evidence),
        ARM_TIPPETT: tippett_arm(evidence),
        ARM_HARMONIC: harmonic_mean_arm(evidence),
        ARM_CAUCHY: cauchy_arm(evidence),
    }
    for a in SOFT_OR_WEIGHTS:
        out[f"{SOFT_OR_PREFIX}{a:g}"] = soft_or_arm(evidence, a)
    if not ablations:
        return out
    if len(evidence.names) > 1:
        lodo = _min_without_each(v)
        for j, name in enumerate(evidence.names):
            out[f"{LODO_PREFIX}{name}"] = s1_of(lodo[:, j])
    groups = list(dict.fromkeys(evidence.groups))
    if len(groups) > 1:
        labels = np.array(evidence.groups)
        group_min = np.stack([v[:, labels == g].min(axis=1) for g in groups], axis=1)
        logo = _min_without_each(group_min)
        for j, group in enumerate(groups):
            out[f"{LOGO_PREFIX}{group}"] = s1_of(logo[:, j])
    return out


def red_flags_statistic(evidence: CallEvidence) -> np.ndarray:
    """v5's statistic over the Red Flags group only, as s1 (the "Red Flags only" baseline)."""
    others = [n for n, g in zip(evidence.names, evidence.groups, strict=True) if g != RED_FLAGS]
    return s1_of(v5_statistic(evidence, drop=others))


# ── matched budget ───────────────────────────────────────────────────────────────────────────
def fit_arms(
    day_scores: Mapping[str, ArrayLike], alphas: Sequence[float] = ALPHAS
) -> dict[str, dict[float, hm.Threshold]]:
    """Each arm's threshold at each alpha, fitted on the calibration pool's unlabelled
    agent-day maxima in the fit window (pooled over its worlds)."""
    return {
        arm: {a: hm.fit_threshold(scores, a) for a in alphas} for arm, scores in day_scores.items()
    }


@dataclass(frozen=True)
class ArmPoint:
    """One arm at one alpha on one world (or pooled worlds): counts for pooling."""

    arm: str
    alpha: float
    benign_days: int
    benign_alerts: int
    episodes: int
    caught: int

    @property
    def benign_rate(self) -> float:
        """Realised benign agent-day alert rate."""
        return self.benign_alerts / self.benign_days if self.benign_days else math.nan

    @property
    def recall(self) -> float:
        """Credited gray recall."""
        return self.caught / self.episodes if self.episodes else math.nan

    @property
    def transfer_ratio(self) -> float:
        """Realised over target rate (Hyp3)."""
        return hm.transfer_ratio(self.benign_rate, self.alpha)


def evaluate_arm(
    arm: str,
    threshold: hm.Threshold,
    days: hm.AgentDays,
    dm: hm.DayMax,
    episode: ArrayLike,
    window: tuple[int, int] | None = None,
) -> ArmPoint:
    """Apply a fitted threshold unchanged to one world's agent-days in the window."""
    ep = np.asarray(episode, dtype=np.int64)
    sel = hm.in_window(days.day, window)
    gray = hm.day_any(days, ep >= 0)
    alert = hm.at_or_above(dm.score, threshold) & sel
    present = hm.episodes_present(days, ep, sel)
    n_ep = int(ep.max()) + 1 if (ep >= 0).any() else 0
    caught = hm.credited_caught(alert, np.where(sel, ep[dm.top], -1), n_ep)
    benign = sel & ~gray
    return ArmPoint(
        arm=arm,
        alpha=threshold.alpha,
        benign_days=int(benign.sum()),
        benign_alerts=int((alert & benign).sum()),
        episodes=len(present),
        caught=int(caught[present].sum()),
    )


def pool_points(points: Sequence[ArmPoint]) -> ArmPoint:
    """Sum one arm's points over worlds."""
    if not points or len({(p.arm, p.alpha) for p in points}) != 1:
        raise ValueError("pool the points of one arm at one alpha")
    return ArmPoint(
        arm=points[0].arm,
        alpha=points[0].alpha,
        benign_days=sum(p.benign_days for p in points),
        benign_alerts=sum(p.benign_alerts for p in points),
        episodes=sum(p.episodes for p in points),
        caught=sum(p.caught for p in points),
    )


@dataclass(frozen=True)
class NonInferiority:
    """Hyp4 for one arm: the simultaneous one-sided upper bound of (arm - v5) on the Hyp1
    endpoint, and whether the null "arm - v5 >= delta_c" is rejected."""

    arm: str
    difference: float
    upper: float
    level: float
    rejected: bool


def hyp4_noninferiority(
    per_world: Mapping[str, ArrayLike],
    delta_c: float,
    *,
    reference: str = ARM_V5,
    level: float = hs.CONFIDENCE,
    b: int = hs.BOOTSTRAP_B,
    seed: int = hs.BOOTSTRAP_SEED,
) -> dict[str, NonInferiority]:
    """Hyp4: no combiner beats v5 by delta_c or more. ``per_world`` maps each arm to its
    per-world pAUC (same world order). Bounds are simultaneous over the m other arms
    (Bonferroni: each at 1 - (1 - level) / m) from one shared world-bootstrap matrix; an arm's
    null is rejected only when its bound, not its estimate, is below delta_c. The ``v5`` arm
    is the statistic without floors (module docstring), not the shipped s1."""
    if reference not in per_world:
        raise ValueError(f"the reference arm {reference!r} is missing")
    others = [a for a in per_world if a != reference]
    if not others:
        raise ValueError("no arm to compare with the reference")
    base = np.asarray(per_world[reference], dtype=np.float64)
    counts = hs.bootstrap_counts(len(base), b, seed)
    each = 1 - (1 - level) / len(others)
    out = {}
    for arm in others:
        interval = hs.paired_world_bootstrap(per_world[arm], base, level=each, counts=counts)
        out[arm] = NonInferiority(
            arm=arm,
            difference=interval.estimate,
            upper=interval.upper_one_sided,
            level=each,
            rejected=interval.upper_one_sided < delta_c,
        )
    return out
