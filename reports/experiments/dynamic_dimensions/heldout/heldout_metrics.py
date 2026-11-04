"""Held-out metrics for the v5 dynamic layer (spec 6.1, 6.5; EV-18, EV-19, EV-24, EV-31).

Every function reads per-call or per-agent-day arrays taken from a score log and returns
numbers. Nothing here changes an engine. The units are the spec's (section 6.1):

- the **agent-day** for false alarms. The agent is the baseline key the engine kept history
  under: the signed-in agent, or the reported client and address without sign-in (spec 2.1,
  decision D5; never a person by default). The day is the engine's local-day key (B9: the
  caller's zone and a 04:00 rollover), never the UTC date, counted in **deployment days**
  (day 0 is the world's or the route's first day): :func:`local_day_keys` with ``base_day``,
  then :func:`group_agent_days`;
- the **gray episode** for detection. An episode is credited only when the call that set its
  agent-day's maximum belongs to it (EV-18): :func:`credited_episode_scores`;
- the **world** for replication. Every interval and test resamples or permutes whole worlds
  and nothing inside them (R2-8); the statistics live in :mod:`heldout_stats`.

Every window here counts deployment days: the route warm-up stratum is days 0-89 (EV-31), the
fit window 90-134 and the selection window 135-180 (``heldout_world_spec``), Hyp2's 30-day
periods start at day 90. Days that look like 1970-based keys are refused
(:func:`check_deployment_days`).

The primary endpoint (Hyp1) is :func:`credited_pauc`: the partial area under credited gray
recall against the benign agent-day rate, over [0, 3%]. Thresholds for matched-budget points
come from :func:`fit_threshold`, on unlabelled calibration agent-days (R2-3). The daily review
list (:func:`review_list`) takes L = max(1, round(active agents / 40)) agent-days by (s1, s2).
Also here: per-dimension spend with Holm and the tenure bands (Hyp2), harm before the first
alert (EV-19, :func:`harm_before_first_alert`) and the gate curve of R (EV-24,
:func:`gate_curve`).

The threshold fit, the list's exact tie expectation and the Wilson interval are copied from the
knowledge-base probe ``probes/calib_eval.py`` (copied, not imported).

Every number these functions give on a simulator world is a development-world or synthetic
number until it comes from a frozen held-out run.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from mcp_security.behaviour import clock

try:  # imported as part of the heldout package (tests, other harness modules)
    from . import heldout_stats as hs
except ImportError:  # run as a script: the sibling module is on sys.path
    import heldout_stats as hs  # type: ignore[no-redef]

# ── frozen evaluation constants (spec 6.1, 6.5) ──────────────────────────────────────────────
MAX_FPR = 0.03  # Hyp1: pAUC over benign agent-day rates in [0, 3%]
ALPHA_DEPLOYED = 0.01  # the deployed 1% line (CAL-5)
STATED_ALPHAS = (0.01, 0.025, 0.05)  # lines reported beside the deployed one
FLOOR_BUDGET = 0.0035  # beta: 0.30% first access + 0.05% copy (CAL-4)
X3_LINE = 3.0  # v4's line, kept for continuity (Hyp6)
PREVALENCES = (1e-3, 1e-4, 1e-5)  # PPV at these gray prevalences (R1-7)
TENURE_EDGES = (20, 45)  # Hyp2 bands: A < 20, 20 <= A < 45, A >= 45
TENURE_BANDS = ("A < 20", "20 <= A < 45", "A >= 45")
TENURE_WINDOW_DAYS = 89  # A counts the caller's active days in [t - 89, t - 1] (spec 2.3)
PERIOD_DAYS = 30  # Hyp2: 30-day periods
# Windows below are in deployment days (day 0 = the world's or the route's first day).
EVAL_FROM_DAY = 90  # warm days start here; days 0-89 are the route warm-up stratum (EV-31)
ROUTE_WARMUP_WINDOW = (0, EVAL_FROM_DAY - 1)
MAX_DEPLOYMENT_DAY = 3_650  # ten years; a 1970-based local-day key is larger after 1979
AGENTS_PER_LIST_SLOT = 40  # L = max(1, round(active agents / 40)): 4 at 150 agents
MIN_LIST_LENGTH = 1
RECALL_AT_LENGTHS = tuple(range(1, 17))  # recall@L for L = 1-16
KEY_DECIMALS = 9  # list keys are rounded like the simulator's (normal_org_sim.py:548)
FIT_TOLERANCE = 1e-9  # share <= alpha up to float noise
OFFSET_BUCKET_S = 900.0  # zone offsets are looked up once per 15 minutes
BUCKET_END_S = OFFSET_BUCKET_S - 1.0  # tz transitions fall on whole minutes
WRITE_WEIGHT = 2.0  # EV-24: an episode that wrote or deleted weighs twice its sensitivity
NO_ASSET = ""  # a call that touched no asset
HALF = 0.5


# ── local-day keys (B9) ──────────────────────────────────────────────────────────────────────
def _zone_offsets(ts: np.ndarray, zone_name: str) -> np.ndarray:
    """The zone's UTC offset (seconds) at each ``ts``, looked up once per 15-minute bucket; a
    bucket whose offset changes inside it is looked up per element."""
    bucket = np.floor(ts / OFFSET_BUCKET_S)
    starts, inverse = np.unique(bucket, return_inverse=True)
    starts = starts * OFFSET_BUCKET_S
    at_start = np.array([clock.local_seconds(float(s), zone_name) - s for s in starts])
    at_end = np.array(
        [
            clock.local_seconds(float(s + BUCKET_END_S), zone_name) - (s + BUCKET_END_S)
            for s in starts
        ]
    )
    offsets = at_start[inverse]
    for b in np.flatnonzero(at_start != at_end):
        rows = np.flatnonzero(inverse == b)
        offsets[rows] = [clock.local_seconds(float(t), zone_name) - t for t in ts[rows]]
    return offsets


def _local_seconds(ts: ArrayLike, zones: str | ArrayLike) -> np.ndarray:
    t = np.asarray(ts, dtype=np.float64)
    if t.ndim != 1:
        raise ValueError(f"ts must be one-dimensional, not shape {t.shape}")
    if isinstance(zones, str):
        return t + _zone_offsets(t, zones)
    z = np.asarray(zones)
    if z.shape != t.shape:
        raise ValueError(f"zones has shape {z.shape}, ts has {t.shape}")
    out = np.empty_like(t)
    for name in np.unique(z):
        rows = np.flatnonzero(z == name)
        out[rows] = t[rows] + _zone_offsets(t[rows], str(name))
    return out


def local_day_keys(
    ts: ArrayLike,
    zones: str | ArrayLike = clock.DEFAULT_ZONE,
    day_start_hour: float = clock.DAY_START_HOUR,
    *,
    base_day: int = 0,
) -> np.ndarray:
    """The engine's local-day key of each timestamp minus ``base_day``.

    The key equals :func:`clock.local_day` (done once per 15 minutes of offsets) and counts
    days from 1970-01-01. ``base_day`` is the key of deployment day 0, so that the result is
    the deployment day every window of this harness counts: ``normal_org_world.BASE_DAY`` for
    a simulator world, ``clock.local_day`` of the route's first call in the route zone for a
    gateway log. Pass absolute timestamps: zone offsets follow the rules of their own date.
    ``zones`` is one IANA zone or one per timestamp.
    """
    clock.check_day_start(day_start_hour)
    local = _local_seconds(ts, zones)
    keys = np.floor((local - day_start_hour * clock.HOUR_S) / clock.DAY_S).astype(np.int64)
    return keys - int(base_day)


def check_deployment_days(day: ArrayLike) -> None:
    """``ValueError`` when days look like 1970-based local-day keys, not deployment days.

    A deployment day stays within :data:`MAX_DEPLOYMENT_DAY` of day 0 (W6 runs 365 days); the
    key of any date after 1979 is larger. Windows and training days compared with such keys
    would silently select nothing.
    """
    d = np.asarray(day)
    if d.size and int(np.abs(d).max()) > MAX_DEPLOYMENT_DAY:
        raise ValueError(
            f"days reach {int(np.abs(d).max())}: these look like 1970-based local-day keys, "
            "but windows count deployment days; use local_day_keys(..., base_day=<the key of "
            "deployment day 0>)"
        )


def local_hours(ts: ArrayLike, zones: str | ArrayLike = clock.DEFAULT_ZONE) -> np.ndarray:
    """The wall-clock hour 0-23 of each timestamp (equal to :func:`clock.local_hour`)."""
    local = _local_seconds(ts, zones)
    return (np.mod(local, clock.DAY_S) // clock.HOUR_S).astype(np.int64)


# ── agent-days ───────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class AgentDays:
    """Calls grouped into agent-days, (agent, local day) with at least one call.

    ``order`` lists call indices by (agent, day, stream position); ``starts`` is where each
    agent-day begins in it; ``of_call`` maps each call (input order) to its agent-day.
    """

    order: np.ndarray
    starts: np.ndarray
    of_call: np.ndarray
    agent: np.ndarray  # per agent-day: the caller's label as given
    day: np.ndarray  # per agent-day: the local-day key

    @property
    def n_days(self) -> int:
        """Number of agent-days."""
        return len(self.starts)

    @property
    def n_calls(self) -> int:
        """Number of calls."""
        return len(self.order)

    @property
    def sorted_group(self) -> np.ndarray:
        """The agent-day of each position of ``order``."""
        return self.of_call[self.order]


def group_agent_days(agent: ArrayLike, day: ArrayLike, seq: ArrayLike | None = None) -> AgentDays:
    """Group calls into agent-days. ``seq`` is the stream order (input order when None)."""
    a = np.asarray(agent)
    d = np.asarray(day, dtype=np.int64)
    if a.ndim != 1 or a.shape != d.shape or len(a) == 0:
        raise ValueError("agent and day must be non-empty one-dimensional arrays of one length")
    s = np.arange(len(a)) if seq is None else np.asarray(seq)
    if s.shape != a.shape:
        raise ValueError(f"seq has shape {s.shape}, agent has {a.shape}")
    _, code = np.unique(a, return_inverse=True)
    order = np.lexsort((s, d, code))
    ca, cd = code[order], d[order]
    new = np.r_[True, (ca[1:] != ca[:-1]) | (cd[1:] != cd[:-1])]
    starts = np.flatnonzero(new)
    of_call = np.empty(len(a), dtype=np.int64)
    of_call[order] = np.cumsum(new) - 1
    return AgentDays(
        order=order, starts=starts, of_call=of_call, agent=a[order][starts], day=cd[starts]
    )


def past_window_start(days: AgentDays, window: int) -> np.ndarray:
    """Per agent-day i: the index of the same caller's first agent-day in [t_i - window,
    t_i - 1] (i itself when there is none), so agent-days lo..i-1 are its past days in the
    window. Needs the (agent, day) order that :func:`group_agent_days` gives."""
    if window < 0:
        raise ValueError(f"window must be non-negative, not {window}")
    _, agent = np.unique(days.agent, return_inverse=True)
    lowest = int(days.day.min()) if days.n_days else 0
    span = int(days.day.max()) - lowest + window + 2 if days.n_days else 1
    key = agent.astype(np.int64) * span + (days.day - lowest)
    if np.any(np.diff(key) <= 0):
        raise ValueError("agent-days must be sorted by (agent, day), as group_agent_days gives")
    first = np.searchsorted(agent, agent, side="left")
    return np.maximum(np.searchsorted(key, key - window, side="left"), first)


def active_days_before(days: AgentDays, window: int = TENURE_WINDOW_DAYS) -> np.ndarray:
    """Per agent-day: A, the same caller's active days in [t - window, t - 1] (the input of
    :func:`tenure_band`; 89 days by default, spec 2.3)."""
    return np.arange(days.n_days) - past_window_start(days, window)


def day_any(days: AgentDays, flags: ArrayLike) -> np.ndarray:
    """Per agent-day: whether any of its calls has the flag (``flags``: calls, or calls x k)."""
    f = np.asarray(flags, dtype=bool)
    if f.shape[0] != days.n_calls:
        raise ValueError(f"flags has {f.shape[0]} rows, expected {days.n_calls} calls")
    return np.logical_or.reduceat(f[days.order], days.starts, axis=0)


@dataclass(frozen=True)
class DayMax:
    """Each agent-day's largest score, its top call and the top call's secondary.

    The top call is the first call in stream order that reaches the maximum, as the
    simulator's day maximum (``normal_org_sim.py:430``); it carries the list's secondary key
    and decides credit (EV-18).
    """

    score: np.ndarray
    top: np.ndarray  # call index (input order)
    secondary: np.ndarray


def _scores(x: ArrayLike, n: int, what: str) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.shape != (n,):
        raise ValueError(f"{what} has shape {arr.shape}, expected ({n},)")
    return np.where(np.isnan(arr), -np.inf, arr)


def day_max(days: AgentDays, primary: ArrayLike, secondary: ArrayLike | None = None) -> DayMax:
    """Day maxima of a per-call score (NaN counts as -inf, a call that took no part)."""
    p = _scores(primary, days.n_calls, "primary")
    s = (
        np.zeros(days.n_calls)
        if secondary is None
        else _scores(secondary, days.n_calls, "secondary")
    )
    v = p[days.order]
    peak = np.maximum.reduceat(v, days.starts)
    at = v == peak[days.sorted_group]
    first = np.minimum.reduceat(np.where(at, np.arange(len(v)), len(v)), days.starts)
    top = days.order[first]
    return DayMax(score=peak, top=top, secondary=s[top])


# ── detection: credit and the partial AUC (Hyp1) ─────────────────────────────────────────────
def credited_episode_scores(
    day_score: ArrayLike, top_episode: ArrayLike, n_episodes: int
) -> np.ndarray:
    """Per episode: the largest score of the agent-days whose top call belongs to it, and -inf
    when no agent-day credits it (it ranks below every benign day). ``top_episode`` is -1 for a
    day whose top call is in no episode."""
    score = np.asarray(day_score, dtype=np.float64)
    ep = np.asarray(top_episode, dtype=np.int64)
    if score.shape != ep.shape:
        raise ValueError("day_score and top_episode must have one shape")
    out = np.full(n_episodes, -np.inf)
    credited = ep >= 0
    np.maximum.at(out, ep[credited], score[credited])
    return out


def partial_auc(
    negatives: ArrayLike,
    positives: ArrayLike,
    max_fpr: float = MAX_FPR,
    *,
    normalise: bool = True,
) -> float:
    """Area under the ROC curve over false-positive rates [0, max_fpr].

    Higher scores are stranger. Points are taken at every distinct score and joined by
    straight lines, so a tie between a positive and a negative is a diagonal step (with
    ``max_fpr = 1`` the area is the Mann-Whitney probability, ties counted one half).
    ``normalise`` divides by ``max_fpr``, so a perfect ranking gives 1 and a random one
    ``max_fpr / 2``.
    """
    neg = np.asarray(negatives, dtype=np.float64).ravel()
    pos = np.asarray(positives, dtype=np.float64).ravel()
    if len(neg) == 0 or len(pos) == 0:
        raise ValueError("partial_auc needs at least one negative and one positive")
    if np.isnan(neg).any() or np.isnan(pos).any():
        raise ValueError("scores must not be NaN (use -inf for 'never alerts')")
    if not 0 < max_fpr <= 1:
        raise ValueError(f"max_fpr must lie in (0, 1], not {max_fpr}")
    values = np.concatenate([neg, pos])
    is_pos = np.concatenate([np.zeros(len(neg), bool), np.ones(len(pos), bool)])
    order = np.argsort(-values, kind="stable")
    v, ip = values[order], is_pos[order]
    last = np.flatnonzero(np.r_[v[1:] != v[:-1], True])
    fpr = np.r_[0.0, np.cumsum(~ip)[last] / len(neg)]
    tpr = np.r_[0.0, np.cumsum(ip)[last] / len(pos)]
    x0, x1, y0, y1 = fpr[:-1], fpr[1:], tpr[:-1], tpr[1:]
    xc = np.minimum(x1, max_fpr)
    width = np.clip(xc - x0, 0.0, None)
    dx = x1 - x0
    frac = np.divide(xc - x0, dx, out=np.zeros_like(dx), where=dx > 0)
    yc = y0 + (y1 - y0) * np.clip(frac, 0.0, 1.0)
    area = float(np.sum(width * (y0 + yc) / 2))
    return area / max_fpr if normalise else area


def in_window(day: ArrayLike, window: tuple[int, int] | None) -> np.ndarray:
    """Mask of deployment days in the inclusive window (every day when None); days that look
    like 1970-based keys are refused (:func:`check_deployment_days`)."""
    d = np.asarray(day)
    if window is None:
        return np.ones(d.shape, dtype=bool)
    check_deployment_days(d)
    lo, hi = window
    return (d >= lo) & (d <= hi)


def episodes_present(days: AgentDays, episode: ArrayLike, mask: ArrayLike) -> np.ndarray:
    """Sorted ids of the episodes with at least one call on an agent-day in ``mask``."""
    ep = np.asarray(episode, dtype=np.int64)
    keep = np.asarray(mask, dtype=bool)[days.of_call] & (ep >= 0)
    return np.unique(ep[keep])


def credited_pauc(
    days: AgentDays,
    dm: DayMax,
    episode: ArrayLike,
    window: tuple[int, int] | None = None,
    max_fpr: float = MAX_FPR,
) -> float:
    """Hyp1 on one world: normalised pAUC of credited gray recall against the benign
    agent-day rate. Benign = every agent-day in the window with no gray call (ordinary and
    change); positives = the episodes with a call in the window."""
    ep = np.asarray(episode, dtype=np.int64)
    sel = in_window(days.day, window)
    gray = day_any(days, ep >= 0)
    n_ep = int(ep.max()) + 1 if (ep >= 0).any() else 0
    present = episodes_present(days, ep, sel)
    if len(present) == 0:
        raise ValueError("no gray episode in the window")
    top_ep = np.where(sel, ep[dm.top], -1)
    scores = credited_episode_scores(dm.score, top_ep, n_ep)[present]
    return partial_auc(dm.score[sel & ~gray], scores, max_fpr)


# ── matched-budget thresholds (copied from calib_eval.fit_threshold) ─────────────────────────
@dataclass(frozen=True)
class Threshold:
    """A fitted alert threshold: the smallest observed key whose share at or above it is at
    most alpha. Days tied at a key alert together; ``feasible`` is False when even the top key
    alone exceeds alpha (nothing alerts)."""

    alpha: float
    feasible: bool
    value: float | None
    secondary: float | None
    fit_rate: float
    next_rate: float | None  # the share one key lower
    ties: int
    days: int


def fit_threshold(scores: ArrayLike, alpha: float, secondary: ArrayLike | None = None) -> Threshold:
    """Fit a threshold on agent-day keys (score, then secondary, compared lexicographically).

    Pass the calibration pool's **unlabelled** agent-days (gray included, R2-3). -inf days
    (nothing scored) never alert but count in the denominator.
    """
    p = np.asarray(scores, dtype=np.float64)
    s = np.zeros_like(p) if secondary is None else np.asarray(secondary, dtype=np.float64)
    n = len(p)
    if n == 0:
        raise ValueError("no agent-days to fit on")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must lie in (0, 1), not {alpha}")
    keep = p > -np.inf
    order = np.lexsort((-s[keep], -p[keep]))
    ps, ss = p[keep][order], s[keep][order]
    if len(ps) == 0:
        return Threshold(alpha, False, None, None, 0.0, None, 0, n)
    g_start = np.flatnonzero(np.r_[True, (ps[1:] != ps[:-1]) | (ss[1:] != ss[:-1])])
    g_end = np.r_[g_start[1:], len(ps)]
    j = int((g_end <= alpha * n + FIT_TOLERANCE).sum()) - 1
    if j < 0:
        return Threshold(alpha, False, None, None, 0.0, float(g_end[0] / n), int(g_end[0]), n)
    return Threshold(
        alpha=alpha,
        feasible=True,
        value=float(ps[g_start[j]]),
        secondary=float(ss[g_start[j]]) if secondary is not None else None,
        fit_rate=float(g_end[j] / n),
        next_rate=float(g_end[j + 1] / n) if j + 1 < len(g_end) else None,
        ties=int(g_end[j] - g_start[j]),
        days=n,
    )


def at_or_above(
    scores: ArrayLike, threshold: Threshold, secondary: ArrayLike | None = None
) -> np.ndarray:
    """Keys at or above a fitted threshold (nothing when the fit was infeasible)."""
    p = np.asarray(scores, dtype=np.float64)
    if not threshold.feasible or threshold.value is None:
        return np.zeros(p.shape, dtype=bool)
    if threshold.secondary is None or secondary is None:
        return p >= threshold.value
    s = np.asarray(secondary, dtype=np.float64)
    return (p > threshold.value) | ((p == threshold.value) & (s >= threshold.secondary))


def credited_caught(day_alert: ArrayLike, top_episode: ArrayLike, n_episodes: int) -> np.ndarray:
    """Per episode: caught when an alerting agent-day's top call belongs to it (EV-18)."""
    alert = np.asarray(day_alert, dtype=bool)
    ep = np.asarray(top_episode, dtype=np.int64)
    caught = np.zeros(n_episodes, dtype=bool)
    hit = alert & (ep >= 0)
    caught[ep[hit]] = True
    return caught


# ── the daily review list ────────────────────────────────────────────────────────────────────
def list_lengths(day: ArrayLike) -> np.ndarray:
    """Per agent-day: its day's list length L = max(1, round(active agents / 40)), rounding
    halves up (an agent-day is one active agent on that day)."""
    _, inverse, counts = np.unique(np.asarray(day), return_inverse=True, return_counts=True)
    lengths = np.floor(counts / AGENTS_PER_LIST_SLOT + HALF).astype(np.int64)
    return np.maximum(MIN_LIST_LENGTH, lengths)[inverse]


def _listed_probability(
    day: np.ndarray, pri: np.ndarray, sec: np.ndarray, k: np.ndarray
) -> np.ndarray:
    """P(listed) per agent-day when the list takes the top ``k`` (per agent-day: its day's L)
    by (pri, sec) and breaks the remaining ties at random (calib_eval._exact_topk)."""
    order = np.lexsort((-sec, -pri, day))
    d, p_, s_ = day[order], pri[order], sec[order]
    new_group = np.r_[True, (d[1:] != d[:-1]) | (p_[1:] != p_[:-1]) | (s_[1:] != s_[:-1])]
    g_start = np.flatnonzero(new_group)
    g_size = np.diff(np.r_[g_start, len(d)])
    above = g_start - np.searchsorted(d, d[g_start], side="left")
    slots = k[order][g_start]
    prob = np.empty(len(day))
    prob[order] = np.repeat(np.clip((slots - above) / g_size, 0.0, 1.0), g_size)
    return prob


def _credit(prob: np.ndarray, top_episode: np.ndarray, n_episodes: int) -> np.ndarray:
    """P(caught) per episode: 1 - prod over the days credited to it of (1 - P(listed))."""
    miss = np.ones(n_episodes)
    credited = top_episode >= 0
    np.multiply.at(miss, top_episode[credited], 1.0 - prob[credited])
    return 1.0 - miss


@dataclass(frozen=True)
class ListResult:
    """Credited catch of a daily review list, its random-list expectation and the lift."""

    episodes: int
    slots: int
    caught: float  # expected credited catches
    recall: float
    random_recall: float
    lift: float | None
    per_episode: np.ndarray  # P(credited catch), every episode id
    random_per_episode: np.ndarray


def review_list(
    day: ArrayLike,
    score: ArrayLike,
    secondary: ArrayLike,
    top_episode: ArrayLike,
    episodes: ArrayLike,
    *,
    length: int | None = None,
) -> ListResult:
    """The daily review list (spec 2.4 step 5, EV-18): per day, the top L agent-days by (s1,
    then the s2 of the first call at that s1), remaining ties at random (exact expectation).

    ``day``, ``score``, ``secondary``, ``top_episode`` are per agent-day (pass only the days of
    the report window); ``episodes`` are the episode ids in scope. ``length`` fixes L for every
    day; None uses :func:`list_lengths`. Credit: a listed day catches the episode its top call
    belongs to. The random list draws L agent-days uniformly per day, under the same credit.
    """
    d = np.asarray(day, dtype=np.int64)
    ep = np.asarray(top_episode, dtype=np.int64)
    scope = np.asarray(episodes, dtype=np.int64)
    if len(scope) == 0:
        raise ValueError("no episode in scope")
    if length is not None and length < MIN_LIST_LENGTH:
        raise ValueError(f"length must be at least {MIN_LIST_LENGTH}, not {length}")
    k = np.full(len(d), length, dtype=np.int64) if length is not None else list_lengths(d)
    pri = np.round(_scores(score, len(d), "score"), KEY_DECIMALS)
    sec = np.round(_scores(secondary, len(d), "secondary"), KEY_DECIMALS)
    n_ep = int(max(scope.max(), ep.max(initial=-1))) + 1
    prob = _listed_probability(d, pri, sec, k)
    _, inverse, per_day = np.unique(d, return_inverse=True, return_counts=True)
    random_prob = np.minimum(1.0, k / per_day[inverse])
    caught, rand = _credit(prob, ep, n_ep), _credit(random_prob, ep, n_ep)
    recall, random_recall = float(caught[scope].mean()), float(rand[scope].mean())
    first_of_day = np.unique(d, return_index=True)[1]
    return ListResult(
        episodes=len(scope),
        slots=int(np.minimum(k[first_of_day], per_day).sum()),
        caught=float(caught[scope].sum()),
        recall=recall,
        random_recall=random_recall,
        lift=recall / random_recall if random_recall > 0 else None,
        per_episode=caught,
        random_per_episode=rand,
    )


def recall_at_lengths(
    day: ArrayLike,
    score: ArrayLike,
    secondary: ArrayLike,
    top_episode: ArrayLike,
    episodes: ArrayLike,
    lengths: Sequence[int] = RECALL_AT_LENGTHS,
) -> dict[int, float]:
    """Credited list recall at fixed list lengths (recall@L, L = 1-16 by default)."""
    return {
        n: review_list(day, score, secondary, top_episode, episodes, length=n).recall
        for n in lengths
    }


# ── quiet: per-dimension spend, strata, periods (Hyp2) ───────────────────────────────────────
def dimension_fired(
    rates: ArrayLike, shares: ArrayLike, alpha: float = ALPHA_DEPLOYED
) -> np.ndarray:
    """Per call and dimension: q_d / w_d <= alpha (the dimension spends at this line).
    ``rates`` is calls x dimensions (NaN: took no part); a NaN share (watch-only) never fires."""
    q = np.asarray(rates, dtype=np.float64)
    w = np.asarray(shares, dtype=np.float64)
    if q.ndim != 2 or q.shape[1] != len(w):
        raise ValueError(f"rates must be calls x {len(w)} dimensions, not {q.shape}")
    with np.errstate(invalid="ignore", divide="ignore"):
        return (q / w) <= alpha


@dataclass(frozen=True)
class SpendRow:
    """One dimension's realised spend against its budget share w_d alpha (Hyp2 theory
    check), with its Holm-adjusted overrun test."""

    dimension: str
    share: float | None
    nominal: float | None
    days: int
    fired: int
    spend: float
    wilson95: tuple[float, float]
    p_value: float | None
    adjusted_p: float | None
    overrun: bool


def per_dimension_spend(
    fired_days: ArrayLike,
    shares: ArrayLike,
    names: Sequence[str],
    alpha: float = ALPHA_DEPLOYED,
    *,
    world: ArrayLike | None = None,
    holm_alpha: float = hs.HOLM_ALPHA,
    b: int = hs.BOOTSTRAP_B,
    seed: int = hs.BOOTSTRAP_SEED,
) -> list[SpendRow]:
    """Per-dimension spend on benign warm agent-days, tested against w_d alpha with Holm over
    the alerting dimensions.

    ``fired_days`` is agent-days x dimensions (:func:`day_any` of :func:`dimension_fired`).
    The test of H0 "spend <= w_d alpha" is the world bootstrap when ``world`` names at least two
    worlds (worlds resampled whole), else the exact binomial tail.
    """
    f = np.asarray(fired_days, dtype=bool)
    w = np.asarray(shares, dtype=np.float64)
    if f.ndim != 2 or f.shape[1] != len(w) or len(names) != len(w):
        raise ValueError("fired_days, shares and names must agree on the dimensions")
    n = f.shape[0]
    if n == 0:
        raise ValueError("no agent-days")
    worlds = None
    if world is not None:
        _, worlds = np.unique(np.asarray(world), return_inverse=True)
        if len(worlds) != n:
            raise ValueError("world must give one world per agent-day")
    use_bootstrap = worlds is not None and worlds.max() + 1 >= hs.MIN_BOOTSTRAP_WORLDS
    counts = hs.bootstrap_counts(int(worlds.max()) + 1, b, seed) if use_bootstrap else None
    den = np.bincount(worlds) if use_bootstrap else None
    p_values: dict[int, float] = {}
    for i in np.flatnonzero(~np.isnan(w)):
        nominal = float(w[i] * alpha)
        k = int(f[:, i].sum())
        if use_bootstrap:
            num = np.bincount(worlds, weights=f[:, i].astype(np.float64), minlength=len(den))
            p_values[i] = hs.bootstrap_p_above(num, den, nominal, counts=counts)
        else:
            p_values[i] = hs.binomial_upper_tail(k, n, nominal)
    tested = sorted(p_values)
    result = hs.holm([p_values[i] for i in tested], holm_alpha) if tested else None
    adjusted = {i: float(result.adjusted[j]) for j, i in enumerate(tested)} if result else {}
    rows = []
    for i, name in enumerate(names):
        k = int(f[:, i].sum())
        share = None if np.isnan(w[i]) else float(w[i])
        rows.append(
            SpendRow(
                dimension=name,
                share=share,
                nominal=None if share is None else share * alpha,
                days=n,
                fired=k,
                spend=k / n,
                wilson95=hs.wilson(k, n),
                p_value=p_values.get(i),
                adjusted_p=adjusted.get(i),
                overrun=adjusted.get(i, 1.0) <= holm_alpha,
            )
        )
    return rows


def tenure_band(active_days: ArrayLike) -> np.ndarray:
    """Hyp2 tenure band of each agent-day from A (the caller's active days in the window,
    :func:`active_days_before`): 0 for A < 20, 1 for 20 <= A < 45, 2 for A >= 45."""
    a = np.asarray(active_days)
    if (a < 0).any():
        raise ValueError("A must be non-negative")
    return np.digitize(a, TENURE_EDGES).astype(np.int64)


def period_index(
    day: ArrayLike, first_day: int = EVAL_FROM_DAY, length: int = PERIOD_DAYS
) -> np.ndarray:
    """The 30-day period of each deployment day counted from ``first_day`` (-1 before it)."""
    if length < 1:
        raise ValueError(f"length must be positive, not {length}")
    d = np.asarray(day, dtype=np.int64)
    check_deployment_days(d)
    out = (d - first_day) // length
    return np.where(d < first_day, -1, out)


@dataclass(frozen=True)
class GroupRate:
    """Alerts over agent-days in one group (a stratum, a world or a period)."""

    days: int
    alerts: int
    rate: float
    wilson95: tuple[float, float]


def rate_by_group(alerts: ArrayLike, group: ArrayLike) -> dict[object, GroupRate]:
    """Alert rate per group label, with Wilson intervals. Groups are any per-agent-day label:
    a stratum, a world, a 30-day period, a tenure band, or the identity strength the decision
    line logs (``user``, ``service`` or ``none``; DEP-8)."""
    a = np.asarray(alerts, dtype=bool)
    g = np.asarray(group)
    if a.shape != g.shape:
        raise ValueError("alerts and group must have one shape")
    out = {}
    for label in np.unique(g):
        m = g == label
        n, k = int(m.sum()), int(a[m].sum())
        key = label.item() if hasattr(label, "item") else label
        out[key] = GroupRate(days=n, alerts=k, rate=k / n, wilson95=hs.wilson(k, n))
    return out


def share_of_groups_above(alerts: ArrayLike, group: ArrayLike, bound: float) -> float:
    """The share of groups (worlds, 30-day periods) whose alert rate exceeds the bound,
    reported beside the pooled rate (spec 2.6, R2-8)."""
    rates = rate_by_group(alerts, group)
    if not rates:
        raise ValueError("no group")
    return sum(r.rate > bound for r in rates.values()) / len(rates)


def quiet_check(
    alerts_per_world: ArrayLike,
    days_per_world: ArrayLike,
    alpha: float = ALPHA_DEPLOYED,
    beta: float = FLOOR_BUDGET,
    *,
    b: int = hs.BOOTSTRAP_B,
    seed: int = hs.BOOTSTRAP_SEED,
    level: float = hs.CONFIDENCE,
) -> tuple[hs.Interval, bool]:
    """Hyp2 per family: the pooled benign rate's one-sided upper world-bootstrap bound, and
    whether it is at most alpha + beta."""
    interval = hs.world_bootstrap(alerts_per_world, days_per_world, b=b, seed=seed, level=level)
    return interval, interval.upper_one_sided <= alpha + beta


# ── transfer and precision ───────────────────────────────────────────────────────────────────
def transfer_ratio(realised: float, target: float) -> float:
    """Realised over target alert rate of a threshold fitted on the calibration pool (Hyp3)."""
    if target <= 0:
        raise ValueError(f"target must be positive, not {target}")
    return realised / target


def ppv(recall: float, false_alarm_rate: float, prevalence: float) -> float:
    """Positive predictive value at a gray prevalence: r pi / (r pi + f (1 - pi))."""
    if not 0 < prevalence < 1:
        raise ValueError(f"prevalence must lie in (0, 1), not {prevalence}")
    hit = recall * prevalence
    total = hit + false_alarm_rate * (1 - prevalence)
    return hit / total if total > 0 else math.nan


def ppv_by_prevalence(
    recall: float, false_alarm_rate: float, prevalences: Sequence[float] = PREVALENCES
) -> Mapping[float, float]:
    """PPV at each prevalence (spec 6.5: 10^-3 to 10^-5)."""
    return {p: ppv(recall, false_alarm_rate, p) for p in prevalences}


# ── harm before the first alert (EV-19) ──────────────────────────────────────────────────────
@dataclass(frozen=True)
class Harm:
    """EV-19, per episode id: what the episode had delivered before its first alerting call.

    For an episode that never alerts, the counts cover all its calls (the most harm it did
    with no alert). Episodes without calls have zero counts and ``caught`` False.
    """

    caught: np.ndarray  # some call of the episode alerted
    first_alert: np.ndarray  # call index (input order) of its first alerting call, -1 if none
    delay_s: np.ndarray  # seconds from its first call to its first alert, NaN if none
    calls: np.ndarray  # its calls before the first alert
    assets: np.ndarray  # distinct touched assets of those calls
    request_bytes: np.ndarray
    reply_bytes: np.ndarray


def _per_call(values: ArrayLike | None, n: int, what: str, fill: object) -> np.ndarray:
    if values is None:
        return np.full(n, fill)
    out = np.asarray(values)
    if out.shape != (n,):
        raise ValueError(f"{what} has shape {out.shape}, expected ({n},)")
    return out


def harm_before_first_alert(
    episode: ArrayLike,
    ts: ArrayLike,
    alert: ArrayLike,
    *,
    asset: ArrayLike | None = None,
    request_bytes: ArrayLike | None = None,
    reply_bytes: ArrayLike | None = None,
    seq: ArrayLike | None = None,
    n_episodes: int | None = None,
) -> Harm:
    """EV-19 per episode: its first alerting call, and the calls, distinct touched assets and
    request and reply bytes of its calls strictly before that one, in stream order (``ts``,
    then ``seq``).

    Per call: ``episode`` (-1 outside every episode), ``alert`` (the call reached the line:
    q <= alpha at the deployed line, or M >= x3 for v4), ``asset`` ("" for none). Bytes are
    ARG-1's request and reply bytes; absent arrays count as 0.
    """
    ep = np.asarray(episode, dtype=np.int64)
    n = len(ep)
    t = _per_call(ts, n, "ts", 0.0).astype(np.float64)
    hit = _per_call(alert, n, "alert", False).astype(bool)
    touched = _per_call(asset, n, "asset", NO_ASSET).astype(str)
    sent = _per_call(request_bytes, n, "request_bytes", 0.0).astype(np.float64)
    got = _per_call(reply_bytes, n, "reply_bytes", 0.0).astype(np.float64)
    order_in = np.arange(n) if seq is None else _per_call(seq, n, "seq", 0)
    n_ep = int(ep.max(initial=-1)) + 1 if n_episodes is None else n_episodes
    if n_ep < int(ep.max(initial=-1)) + 1:
        raise ValueError(f"n_episodes = {n_ep} is below the largest episode id + 1")
    order = np.lexsort((order_in, t, ep))
    rows = order[ep[order] >= 0]
    out_first = np.full(n_ep, -1, dtype=np.int64)
    delay = np.full(n_ep, np.nan)
    if len(rows) == 0:
        zeros = np.zeros(n_ep)
        return Harm(np.zeros(n_ep, bool), out_first, delay, zeros, zeros, zeros, zeros)
    e = ep[rows]
    starts = np.flatnonzero(np.r_[True, e[1:] != e[:-1]])
    group = np.cumsum(np.r_[True, e[1:] != e[:-1]]) - 1
    pos = np.arange(len(rows))
    first_pos = np.minimum.reduceat(np.where(hit[rows], pos, len(rows)), starts)
    caught_group = first_pos < len(rows)
    before = pos < first_pos[group]
    ids = e[starts]
    out_first[ids[caught_group]] = rows[first_pos[caught_group]]
    delay[ids[caught_group]] = t[rows[first_pos[caught_group]]] - t[rows[starts[caught_group]]]
    kept = rows[before]
    has_asset = touched[kept] != NO_ASSET
    _, asset_code = np.unique(touched[kept], return_inverse=True)
    pairs = np.unique(np.stack([ep[kept][has_asset], asset_code[has_asset]], axis=1), axis=0)
    caught = np.zeros(n_ep, dtype=bool)
    caught[ids[caught_group]] = True
    return Harm(
        caught=caught,
        first_alert=out_first,
        delay_s=delay,
        calls=np.bincount(ep[kept], minlength=n_ep).astype(np.float64),
        assets=np.bincount(pairs[:, 0], minlength=n_ep).astype(np.float64),
        request_bytes=np.bincount(ep[kept], weights=sent[kept], minlength=n_ep),
        reply_bytes=np.bincount(ep[kept], weights=got[kept], minlength=n_ep),
    )


# ── the gate curve of R (EV-24) ──────────────────────────────────────────────────────────────
def consequence_weight(max_sensitivity: ArrayLike, wrote: ArrayLike) -> np.ndarray:
    """EV-24's weight of a gray episode: the highest sensitivity it touched, doubled when it
    wrote or deleted (Part A EV-24)."""
    s = np.asarray(max_sensitivity, dtype=np.float64)
    w = np.asarray(wrote, dtype=bool)
    if s.shape != w.shape or (s < 0).any():
        raise ValueError("max_sensitivity (non-negative) and wrote must have one shape")
    return s * np.where(w, WRITE_WEIGHT, 1.0)


@dataclass(frozen=True)
class GateCurve:
    """EV-24: a gate that blocks every call with R at or above a threshold, at each distinct
    threshold (descending). Benign calls are the calls of benign agent-days."""

    threshold: np.ndarray
    benign_call_rate: np.ndarray  # share of benign calls blocked
    benign_day_rate: np.ndarray  # share of benign agent-days with a blocked call
    recall: np.ndarray  # harm-weighted share of gray episodes with a blocked call


def _share_at_or_above(values: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
    ordered = np.sort(values)
    return (len(ordered) - np.searchsorted(ordered, thresholds, side="left")) / len(ordered)


def gate_curve(
    days: AgentDays,
    risk: ArrayLike,
    episode: ArrayLike,
    weights: ArrayLike | None = None,
) -> GateCurve:
    """EV-24 (spec 2.8): benign block rate against harm-weighted gray recall for a gate on
    the per-call risk R = R_static x M.

    An episode counts as stopped at a threshold when one of its calls is blocked; its weight
    is ``weights[episode id]`` (:func:`consequence_weight`; 1 when None). NaN risk never
    blocks. Pass the calls of one report window.
    """
    r = _scores(risk, days.n_calls, "risk")
    ep = np.asarray(episode, dtype=np.int64)
    if ep.shape != (days.n_calls,):
        raise ValueError(f"episode has shape {ep.shape}, expected ({days.n_calls},)")
    gray_day = day_any(days, ep >= 0)
    benign_call = ~gray_day[days.of_call]
    present = np.unique(ep[ep >= 0])
    if len(present) == 0 or not benign_call.any():
        raise ValueError("the gate curve needs benign calls and at least one episode")
    peak = np.full(int(present.max()) + 1, -np.inf)
    np.maximum.at(peak, ep[ep >= 0], r[ep >= 0])
    w = np.ones(len(peak)) if weights is None else np.asarray(weights, dtype=np.float64)
    if w.ndim != 1 or len(w) < len(peak) or (w < 0).any():
        raise ValueError("weights must give a non-negative weight per episode id")
    ep_peak, ep_weight = peak[present], w[present]
    if ep_weight.sum() <= 0:
        raise ValueError("the episodes' weights sum to zero")
    day_peak = day_max(days, r).score[~gray_day]
    values = np.concatenate([r[benign_call], ep_peak])
    thresholds = np.unique(values[np.isfinite(values)])[::-1]
    by_peak = np.argsort(ep_peak)
    cum = np.r_[0.0, np.cumsum(ep_weight[by_peak])]
    below = np.searchsorted(ep_peak[by_peak], thresholds, side="left")
    return GateCurve(
        threshold=thresholds,
        benign_call_rate=_share_at_or_above(r[benign_call], thresholds),
        benign_day_rate=_share_at_or_above(day_peak, thresholds),
        recall=(cum[-1] - cum[below]) / cum[-1],
    )
