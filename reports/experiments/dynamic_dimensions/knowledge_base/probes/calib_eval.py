"""Shared evaluator for the v5 calibration arms, run on the vectors that dump_vectors.py saved.

An arm hands in one per-call score, ``primary`` (higher = stranger; one value per tool-call row
of the npz, in the npz row order; an M-like arm passes M), and optionally a ``secondary`` (the
review list's tie-breaker) and ``dstar`` (the index of the dimension that gave the call its
score). The evaluator turns these into agent-day scores the way the simulator's day maximum does
(``normal_org_sim.py:421-444``): an agent-day is every (agent, UTC day) with at least one message
on days 90 and later; its score is the largest score of its messages; its *top row* is the first
message in stream order that reaches that maximum (the simulator's strict ``M > rec[0]``,
``normal_org_sim.py:430``), and that row supplies the day's secondary and reason d*.
Non-call messages (``initialize``, ``tools/list``) are in the dump's ``msg_*`` side table. They
enter the day maximum only when the arm passes ``msg_primary`` (the v4 reference passes
``msg_M``, as the simulator does). They always count for the day's label, as in
``normal_org_sim.py:452-465``.

Day labels are the simulator's own (``normal_org_sim.py:507-509``). A day is gray if any of its
messages belongs to a gray episode, change if any carries a tag, and ordinary otherwise. Benign
means ordinary or change.

Every number from these worlds is a DEVELOPMENT-WORLD number (seeds 7, 11 and 21 and their
profiles were used to design v1-v4), never a test result. The metric definitions are in
``METRIC_DEFINITIONS`` below and in ``README.md`` next to this file.

Use from an arm::

    import sys; sys.path.insert(0, "reports/experiments/dynamic_dimensions/knowledge_base/probes")
    import calib_eval
    res = calib_eval.evaluate(npz, primary, secondary, dstar, name="my arm",
                              msg_primary=..., msg_secondary=..., msg_dstar=...)
    print(calib_eval.to_markdown([calib_eval.v4_reference(npz), res]))

CLI (prints the v4 reference and its check against ``<npz>.validation.json``)::

    python3 reports/experiments/dynamic_dimensions/knowledge_base/probes/calib_eval.py \
        /tmp/.../v5_vectors/smoke.npz [--json out.json] [--md out.md]
"""

from __future__ import annotations

import argparse
import functools
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# ── evaluation constants (frozen for every arm) ──────────────────────────────────────────────
EVAL_FROM_DAY = 90  # normal_org_sim.py:68; checked against the sidecar's constants
FIT_DAYS = (90, 134)  # thresholds are fitted on ordinary agent-days of these days
REPORT_FIRST_DAY = 135  # reported on days 135 to the last day (179, plus the UTC spill-over 180)
ALPHAS = (0.01, 0.025, 0.05)  # target ordinary agent-day alert rates in the fit window
LIST_SIZES = (4, 8)  # review list sizes per day (normal_org_sim.py:69)
LIST_DRAWS = 20  # random tie-breaking draws for the review list
LIST_SEED = 20261025  # one seed for every arm, so arms see the same draws (paired)
KEY_DECIMALS = 9  # the simulator rounds list keys to 9 decimals (normal_org_sim.py:548)
WILSON_Z = 1.959963984540054  # two-sided 95%
HISTORY_EDGES = (15, 45)  # bands A < 15, 15 <= A < 45, A >= 45 (A = his active days)
HISTORY_BANDS = ("A < 15", "15 <= A < 45", "A >= 45", "no tool call")
ORDINARY, CHANGE, GRAY = 0, 1, 2
CLASSES = ("ordinary", "change", "gray")
NO_REASON, MESSAGE_REASON = -1, -2  # d* when no dimension took part / a message the arm left out
CHECK_TOLERANCE = 1e-9  # same npz, same arithmetic: values must agree to float noise
ROUNDED_TOLERANCE = 6e-4  # the simulator rounds per-tag rates and causes to 3 decimals
V4_LIST = "M, then second score"  # the simulator's name for the (M, s2) list
V4_FIXED_LINE = ("x3", 3.0)  # v4's alert line (normal_org_sim.py:70)

METRIC_DEFINITIONS = """\
- Agent-day: an (agent, UTC day) with at least one message, days 90 and later. Its score is the
  maximum score of its messages; its top row is the first message (stream order) at that maximum.
- Day labels (the simulator's): gray if any message on the day is part of a gray episode, change
  if any carries a tag, else ordinary. Benign = ordinary + change.
- Top-call labelling (call-level variant): a non-gray day is change only when its top row is
  tagged, so a day touched by one tagged call that did not set its score stays ordinary.
- Per-call rates: share of ordinary (untagged, non-episode) tool calls, and of tagged tool calls,
  at or above the threshold. Day labels play no part.
- Alert: agent-day score >= threshold (equivalently, some message >= threshold).
- Fitted threshold: the smallest score value t taken by an ordinary fit-window (days 90-134)
  agent-day such that the share of those days with score >= t is at most alpha. No fractional
  alerting inside a tie: if the tie at t would cross alpha, t moves up to the next value. The
  achieved fit rate and the rate one value lower are both reported. If even the top value
  exceeds alpha, the fit is infeasible and nothing alerts.
- Tie-broken threshold (only when a secondary is given): the same rule on the key (primary,
  secondary), compared lexicographically. A day's key is the largest (primary, secondary) of its
  rows and its top row the first row at that key; a call alerts when its own key reaches the
  threshold key. This is deterministic, so it is not fractional alerting.
- Report window: days 135 to the last day (179, plus the UTC spill-over day 180 when present, as
  the simulator scores it). Fixed lines (v4 at x3) are also shown on days 90-180 for the check.
- Gray episode recall: an episode with at least one tool call in the window is caught when one
  of those calls is at or above the threshold (tool calls only, as normal_org_sim.py:437-439).
  Wilson 95% intervals.
- Share of gray calls at or above the threshold: pooled over calls, and the mean over episodes of
  each episode's share (the simulator's calls_x3).
- Precision: alerted gray agent-days / alerted agent-days (day precision), and alerted agent-days
  whose top row belongs to a gray episode / alerted agent-days (credited precision).
- Alerts per 1,000 agent-days: 1000 x alerted agent-days / agent-days in the window, split by
  the day label.
- Review list: every scored day (90-180), agent-days ranked by (day score, secondary of the top
  row), both rounded to 9 decimals; remaining ties at random (seed fixed, 20 draws averaged; the
  exact expectation is also given). Top k for k in {4, 8}. Credited (corrected) recall: an episode
  is caught when a listed agent-day's top row is one of its messages. Day-credited recall is the
  simulator's older rule (any listed agent-day that carries the episode). Random: k agent-days
  drawn uniformly per day, expected value, under the same credit rule; lift = recall / random.
  Fill: expected share of the k x days list slots taken by ordinary, change and gray days.
- Reasons for benign alerts: share of alerted benign agent-days by the top row's d*.
- Strata: people vs bots (role name contains "bot"), and history band by A on the day (his active
  days in the last 90, up to yesterday): A < 15, 15-44, >= 45. Episodes take the band of their
  first tool call in the window.
"""


# ── the world: everything that does not depend on the arm ────────────────────────────────────
@dataclass(frozen=True)
class World:
    """Agent-days, labels and episodes of one dumped world, shared by every arm."""

    path: str
    meta: dict
    n_calls: int
    n_msgs: int
    last_day: int
    rows: np.ndarray  # stacked index ([calls; messages]) of every scored row, in stream order
    starts: np.ndarray  # first position in ``rows`` of each agent-day
    row_group: np.ndarray  # agent-day of each position in ``rows``
    row_episode: np.ndarray  # episode of each position in ``rows`` (-1 if none)
    row_tagged: np.ndarray  # True when that row carries a tag
    day: np.ndarray  # per agent-day
    label: np.ndarray  # per agent-day: ORDINARY, CHANGE or GRAY (simulator labelling)
    tags: np.ndarray  # per agent-day: OR of tag bits
    tagged_rows: np.ndarray  # per agent-day: number of tagged rows
    is_bot: np.ndarray  # per agent-day
    band: np.ndarray  # per agent-day: index into HISTORY_BANDS
    pair_day: np.ndarray  # (agent-day, episode) pairs: the day carries the episode
    pair_ep: np.ndarray
    call_day: np.ndarray  # per tool call
    call_kind: np.ndarray  # per tool call: label_kind (0 ordinary, 1 change, 2 gray)
    call_band: np.ndarray  # per tool call: index into HISTORY_BANDS
    gray_call: np.ndarray  # tool-call index of every gray call on scored days
    gray_ep: np.ndarray  # its episode
    ep_kind: np.ndarray  # per episode
    ep_is_bot: np.ndarray  # per episode


def _band(a: np.ndarray) -> np.ndarray:
    """History band index of an A array (-1 = no tool call)."""
    band = np.digitize(a, HISTORY_EDGES).astype(np.int8)
    band[a < 0] = len(HISTORY_BANDS) - 1
    return band


def _frozen(**arrays: np.ndarray) -> dict[str, np.ndarray]:
    for arr in arrays.values():
        arr.flags.writeable = False
    return arrays


def load_world(npz_path: str | Path) -> World:
    """Load the arm-independent part of a dumped world (cached per resolved path)."""
    return _load_world(str(Path(npz_path).resolve()))


@functools.lru_cache(maxsize=4)
def _load_world(resolved: str) -> World:
    path = Path(resolved)
    meta = json.loads(path.with_suffix(".json").read_text())
    if meta["constants"]["eval_from_day"] != EVAL_FROM_DAY:
        raise ValueError(f"{path}: eval_from_day {meta['constants']['eval_from_day']} != 90")
    call_cols = ("agent", "seq", "day", "label_kind", "tag_mask", "episode", "A")
    with np.load(path) as z:
        c = {k: z[k] for k in call_cols}
        m = {k: z[f"msg_{k}"] for k in call_cols[:-1]}
        ep_kind, ep_agent = z["ep_kind"], z["ep_agent"]
    n_calls, n_msgs = len(c["agent"]), len(m["agent"])
    stack = {k: np.concatenate([c[k], m[k]]).astype(np.int64) for k in call_cols[:-1]}
    stack_a = np.concatenate([c["A"].astype(np.int64), np.full(n_msgs, -1, dtype=np.int64)])
    scored = np.flatnonzero(stack["day"] >= EVAL_FROM_DAY)
    rows = scored[np.lexsort((stack["seq"][scored], stack["agent"][scored]))]
    key = stack["agent"][rows] * 1000 + stack["day"][rows]
    starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    if len(starts) != len(np.unique(key)):
        raise ValueError(f"{path}: an agent's days are not contiguous in stream order")
    lengths = np.diff(np.r_[starts, len(rows)])
    row_group = np.repeat(np.arange(len(starts)), lengths)
    row_episode = stack["episode"][rows]
    row_tagged = stack["tag_mask"][rows] != 0
    has_ep = np.maximum.reduceat((row_episode >= 0).astype(np.int8), starts).astype(bool)
    tags = np.bitwise_or.reduceat(stack["tag_mask"][rows], starts)
    label = np.where(has_ep, GRAY, np.where(tags != 0, CHANGE, ORDINARY)).astype(np.int8)
    bot_agent = {a["index"]: "bot" in a["role"] for a in meta["agents"]}  # normal_org_sim.py:506
    agent = stack["agent"][rows][starts]
    is_bot = np.array([bot_agent[int(a)] for a in agent], dtype=bool)
    day_a = np.maximum.reduceat(stack_a[rows], starts)  # A is constant within a day; -1: no call
    n_ep = len(meta["episodes"])
    pos = np.flatnonzero(row_episode >= 0)
    pairs = np.unique(row_group[pos] * max(1, n_ep) + row_episode[pos])
    gray_call = np.flatnonzero((c["episode"] >= 0) & (c["day"] >= EVAL_FROM_DAY))
    arrays = _frozen(
        rows=rows,
        starts=starts,
        row_group=row_group,
        row_episode=row_episode,
        row_tagged=row_tagged,
        day=stack["day"][rows][starts],
        label=label,
        tags=tags,
        tagged_rows=np.add.reduceat(row_tagged.astype(np.int32), starts),
        is_bot=is_bot,
        band=_band(day_a),
        pair_day=pairs // max(1, n_ep),
        pair_ep=pairs % max(1, n_ep),
        call_day=c["day"].astype(np.int64),
        call_kind=c["label_kind"].astype(np.int8),
        call_band=_band(c["A"].astype(np.int64)),
        gray_call=gray_call,
        gray_ep=c["episode"][gray_call].astype(np.int64),
        ep_kind=ep_kind.astype(np.int64),
        ep_is_bot=np.array([bot_agent[int(a)] for a in ep_agent], dtype=bool),
    )
    return World(
        path=str(path),
        meta=meta,
        n_calls=n_calls,
        n_msgs=n_msgs,
        last_day=int(stack["day"][rows].max()),
        **arrays,
    )


# ── the arm: agent-day keys and top rows ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class DayView:
    """Agent-day keys under one alert key, and the attributes of each day's top row.

    The plain view keys a day by its maximum primary alone (the simulator's day maximum); the
    tie-broken view keys it by the lexicographic maximum of (primary, secondary) over its rows.
    """

    p: np.ndarray  # per agent-day: maximum primary (-inf when no row was scored)
    s: np.ndarray  # per agent-day: secondary of the key (0 in the plain view)
    dstar: np.ndarray  # per agent-day: the top row's reason index
    episode: np.ndarray  # per agent-day: the top row's episode (-1 if none)
    tagged: np.ndarray  # per agent-day: the top row carries a tag
    top: np.ndarray  # per agent-day: stacked index of the top row


@dataclass(frozen=True)
class Arm:
    """One arm: per-call scores and its agent-day views."""

    call_p: np.ndarray  # per tool call: primary (NaN replaced by -inf)
    call_s: np.ndarray  # per tool call: secondary (0 when none was given)
    plain: DayView
    tie_broken: DayView | None  # only when a secondary was given
    list_secondary: np.ndarray  # per agent-day: secondary of the plain view's top row


def _vector(x, n: int, what: str, fill: float | None = None) -> np.ndarray:
    """A float64 copy of ``x`` of length ``n`` (``fill`` when x is None); NaN becomes -inf."""
    if x is None:
        if fill is None:
            raise ValueError(f"{what} is required")
        return np.full(n, fill, dtype=np.float64)
    arr = np.asarray(x, dtype=np.float64)
    if arr.shape != (n,):
        raise ValueError(f"{what} has shape {arr.shape}, expected ({n},)")
    return np.where(np.isnan(arr), -np.inf, arr)


def _index_vector(x, n: int, what: str, fill: int) -> np.ndarray:
    if x is None:
        return np.full(n, fill, dtype=np.int64)
    arr = np.asarray(x)
    if arr.shape != (n,) or not np.issubdtype(arr.dtype, np.integer):
        raise ValueError(f"{what} must be an integer array of shape ({n},)")
    return arr.astype(np.int64)


def _day_view(w: World, p: np.ndarray, s: np.ndarray, d: np.ndarray) -> DayView:
    """Lexicographic day maximum of (p, s); the top row is the first row (stream order) at it."""
    v, sv = p[w.rows], s[w.rows]
    pmax = np.maximum.reduceat(v, w.starts)
    at = v == pmax[w.row_group]
    smax = np.maximum.reduceat(np.where(at, sv, -np.inf), w.starts)
    best = at & (sv == smax[w.row_group])
    first = np.minimum.reduceat(np.where(best, np.arange(len(v)), len(v)), w.starts)
    top = w.rows[first]
    return DayView(
        p=pmax,
        s=smax,
        dstar=d[top],
        episode=w.row_episode[first],
        tagged=w.row_tagged[first],
        top=top,
    )


def build_arm(
    w: World,
    primary,
    secondary=None,
    dstar=None,
    msg_primary=None,
    msg_secondary=None,
    msg_dstar=None,
) -> Arm:
    """Stack an arm's call and message scores and build its agent-day views."""
    p_call = _vector(primary, w.n_calls, "primary")
    if not np.isfinite(p_call).any():
        raise ValueError("primary has no finite value")
    p = np.concatenate([p_call, _vector(msg_primary, w.n_msgs, "msg_primary", -np.inf)])
    s = np.concatenate(
        [
            _vector(secondary, w.n_calls, "secondary", 0.0),
            _vector(msg_secondary, w.n_msgs, "msg_secondary", 0.0),
        ]
    )
    d = np.concatenate(
        [
            _index_vector(dstar, w.n_calls, "dstar", NO_REASON),
            _index_vector(msg_dstar, w.n_msgs, "msg_dstar", MESSAGE_REASON),
        ]
    )
    plain = _day_view(w, p, np.zeros_like(p), d)
    return Arm(
        call_p=p_call,
        call_s=s[: w.n_calls],
        plain=plain,
        tie_broken=_day_view(w, p, s, d) if secondary is not None else None,
        list_secondary=s[plain.top],
    )


# ── thresholds and small statistics ──────────────────────────────────────────────────────────
def fit_threshold(p: np.ndarray, s: np.ndarray, alpha: float) -> dict:
    """Smallest observed key (t, u) with share(key >= (t, u)) <= alpha, keys compared
    lexicographically (pass s = 0 for a primary-only threshold). Days tied at a key alert
    together: no fractional alerting. Infeasible (the top key alone exceeds alpha): no alerts."""
    n = len(p)
    if n == 0:
        raise ValueError("no ordinary agent-days in the fit window")
    keep = p > -np.inf
    order = np.lexsort((-s[keep], -p[keep]))  # descending by p, then s
    ps, ss = p[keep][order], s[keep][order]
    if len(ps) == 0:
        return {
            "alpha": alpha,
            "feasible": False,
            "threshold": None,
            "threshold_secondary": None,
            "fit_rate": 0.0,
            "fit_rate_next_value": None,
            "ties_at_threshold": 0,
            "fit_days": n,
        }
    g_start = np.flatnonzero(np.r_[True, (ps[1:] != ps[:-1]) | (ss[1:] != ss[:-1])])
    g_end = np.r_[g_start[1:], len(ps)]  # days at or above group j = g_end[j]
    j = int((g_end <= alpha * n + 1e-9).sum()) - 1  # feasible groups form a prefix
    if j < 0:
        return {
            "alpha": alpha,
            "feasible": False,
            "threshold": None,
            "threshold_secondary": None,
            "fit_rate": 0.0,
            "fit_rate_next_value": float(g_end[0] / n),
            "ties_at_threshold": int(g_end[0]),
            "fit_days": n,
        }
    return {
        "alpha": alpha,
        "feasible": True,
        "threshold": float(ps[g_start[j]]),
        "threshold_secondary": float(ss[g_start[j]]),
        "fit_rate": float(g_end[j] / n),
        "fit_rate_next_value": float(g_end[j + 1] / n) if j + 1 < len(g_end) else None,
        "ties_at_threshold": int(g_end[j] - g_start[j]),
        "fit_days": n,
    }


def _hot(p: np.ndarray, s: np.ndarray, t: float | None, u: float) -> np.ndarray:
    """(p, s) >= (t, u) lexicographically; nothing alerts when t is None (infeasible fit)."""
    if t is None:
        return np.zeros(len(p), dtype=bool)
    return (p > t) | ((p == t) & (s >= u))


def wilson(k: int, n: int, z: float = WILSON_Z) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials (NaN, NaN when n = 0)."""
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def _rate(k: int, n: int) -> float | None:
    return k / n if n else None


def _recall(caught: np.ndarray, mask: np.ndarray) -> dict:
    k, n = int(caught[mask].sum()), int(mask.sum())
    return {"episodes": n, "caught": k, "recall": _rate(k, n), "wilson95": wilson(k, n)}


# ── one operating point ──────────────────────────────────────────────────────────────────────
def _window(w: World, which: str) -> tuple[int, int]:
    return {
        "fit": FIT_DAYS,
        "report": (REPORT_FIRST_DAY, w.last_day),
        "scored": (EVAL_FROM_DAY, w.last_day),
    }[which]


def _reasons(dstar: np.ndarray, names: list[str]) -> dict:
    vals, counts = np.unique(dstar, return_counts=True)
    total = int(counts.sum())

    def name(i: int) -> str:
        if i == NO_REASON:
            return "none"
        if i == MESSAGE_REASON:
            return "non-call message (no reason given)"
        return names[i] if 0 <= i < len(names) else f"dimension {i}"

    order = np.argsort(-counts, kind="stable")
    return {"alerts": total, "share": {name(int(vals[i])): float(counts[i] / total) for i in order}}


def _class_rates(sel: np.ndarray, hot: np.ndarray, label: np.ndarray) -> dict:
    out = {}
    for i, cls in enumerate(CLASSES):
        n, k = int((sel & (label == i)).sum()), int((sel & hot & (label == i)).sum())
        out[cls] = {"days": n, "alerts": k, "rate": _rate(k, n)}
    benign = sel & (label != GRAY)
    nb, kb = int(benign.sum()), int((benign & hot).sum())
    out["benign"] = {"days": nb, "alerts": kb, "rate": _rate(kb, nb)}
    return out


def operating_point(
    w: World,
    view: DayView,
    hot_day: np.ndarray,
    hot_call: np.ndarray,
    call_p: np.ndarray,
    window: str,
    names: list[str],
) -> dict:
    """Every threshold metric at one alert decision (per agent-day and per call), on a window."""
    lo, hi = _window(w, window)
    sel = (w.day >= lo) & (w.day <= hi)
    hot = hot_day
    out: dict = {"window": [lo, hi], "by_day_label": _class_rates(sel, hot, w.label)}
    benign = sel & (w.label != GRAY)
    tc = _class_rates(benign, hot, np.where(view.tagged, CHANGE, ORDINARY))
    out["by_top_call_label"] = {"ordinary": tc["ordinary"], "change": tc["change"]}
    in_win = (w.call_day >= lo) & (w.call_day <= hi)
    calls = {}
    for cls, m in (
        ("ordinary", in_win & (w.call_kind == ORDINARY)),
        ("change", in_win & (w.call_kind == CHANGE)),
        ("benign", in_win & (w.call_kind != GRAY)),
    ):
        calls[cls] = {"calls": int(m.sum()), "rate": _rate(int(hot_call[m].sum()), int(m.sum()))}
    out["per_call"] = calls
    change = sel & (w.label == CHANGE)
    out["change_by_tag"] = {}
    for i, tag in enumerate(w.meta["tags"]):
        m = change & ((w.tags >> i) & 1).astype(bool)
        out["change_by_tag"][tag] = {
            "days": int(m.sum()),
            "rate": _rate(int((m & hot).sum()), int(m.sum())),
        }
    out["change_days_with_one_tagged_row"] = int((change & (w.tagged_rows == 1)).sum())
    alerted = sel & hot
    n_alert, n_days = int(alerted.sum()), int(sel.sum())
    n_cal_days = len(np.unique(w.day[sel]))
    out["precision"] = {
        "day": _rate(int((alerted & (w.label == GRAY)).sum()), n_alert),
        "credited": _rate(int((alerted & (view.episode >= 0)).sum()), n_alert),
    }
    out["alerts_per_1000_agent_days"] = {
        cls: 1000 * int((alerted & (w.label == i)).sum()) / max(1, n_days)
        for i, cls in enumerate(CLASSES)
    } | {"all": 1000 * n_alert / max(1, n_days)}
    out["alerts_per_day"] = {
        cls: int((alerted & (w.label == i)).sum()) / max(1, n_cal_days)
        for i, cls in enumerate(CLASSES)
    }
    gray, ep_present, ep_caught, ep_band = _gray(w, hot_call, call_p, lo, hi)
    out["gray"] = gray
    out["benign_alert_reasons"] = {
        cls: _reasons(view.dstar[alerted & (w.label == i)], names)
        for i, cls in ((ORDINARY, "ordinary"), (CHANGE, "change"))
    } | {"benign": _reasons(view.dstar[alerted & (w.label != GRAY)], names)}
    out["strata"] = _strata(w, sel, hot, ep_present, ep_caught, ep_band)
    return out


def _gray(w: World, hot_call: np.ndarray, call_p: np.ndarray, lo: int, hi: int) -> tuple:
    n_ep = len(w.meta["episodes"])
    keep = (w.call_day[w.gray_call] >= lo) & (w.call_day[w.gray_call] <= hi)
    gc, ep = w.gray_call[keep], w.gray_ep[keep]
    best = np.full(n_ep, -np.inf)
    np.maximum.at(best, ep, call_p[gc])
    n_calls = np.bincount(ep, minlength=n_ep)
    n_above = np.bincount(ep, weights=hot_call[gc].astype(np.float64), minlength=n_ep)
    present = n_calls > 0
    caught = n_above > 0
    first = np.full(n_ep, np.iinfo(np.int64).max)
    np.minimum.at(first, ep, gc)  # rows are in stream order: the smallest index is the first call
    band = np.full(n_ep, len(HISTORY_BANDS) - 1, dtype=np.int8)
    band[present] = w.call_band[first[present]]

    def block(mask: np.ndarray) -> dict:
        m = mask & present
        res = _recall(caught, m)
        res["calls"] = int(n_calls[m].sum())
        res["calls_at_or_above"] = int(n_above[m].sum())
        res["call_share"] = _rate(res["calls_at_or_above"], res["calls"])
        res["call_share_episode_mean"] = (
            float(np.mean(n_above[m] / n_calls[m])) if m.any() else None
        )
        res["median_max_primary"] = float(np.median(best[m])) if m.any() else None
        return res

    out = {
        "overall": block(np.ones(n_ep, dtype=bool)),
        "by_kind": {kind: block(w.ep_kind == i) for i, kind in enumerate(w.meta["kinds"])},
    }
    return out, present, caught, band


def _strata(w: World, sel, hot, ep_present, ep_caught, ep_band) -> dict:
    def row(day_mask: np.ndarray, ep_mask: np.ndarray) -> dict:
        rates = _class_rates(sel & day_mask, hot, w.label)
        return {
            "ordinary": rates["ordinary"],
            "change": rates["change"],
            "benign": rates["benign"],
            "gray": _recall(ep_caught, ep_present & ep_mask),
        }

    return {
        "is_bot": {
            "people": row(~w.is_bot, ~w.ep_is_bot),
            "bots": row(w.is_bot, w.ep_is_bot),
        },
        "history": {name: row(w.band == i, ep_band == i) for i, name in enumerate(HISTORY_BANDS)},
    }


# ── the fixed review list ────────────────────────────────────────────────────────────────────
def _caught_from_p(p: np.ndarray, pair_day: np.ndarray, pair_ep: np.ndarray, n_ep: int):
    miss = np.ones(n_ep)
    np.multiply.at(miss, pair_ep, 1.0 - p[pair_day])
    return 1.0 - miss


def _exact_topk(day: np.ndarray, pri: np.ndarray, sec: np.ndarray, k: int):
    """P(listed) per agent-day when the remaining ties are broken at random, as
    normal_org_sim.py:468-495, and the share of days whose cut falls inside a tie."""
    order = np.lexsort((-sec, -pri, day))
    d, p_, s_ = day[order], pri[order], sec[order]
    new_group = np.r_[True, (d[1:] != d[:-1]) | (p_[1:] != p_[:-1]) | (s_[1:] != s_[:-1])]
    g_start = np.flatnonzero(new_group)
    g_size = np.diff(np.r_[g_start, len(d)])
    above = g_start - np.searchsorted(d, d[g_start], side="left")
    prob = np.empty(len(day))
    prob[order] = np.repeat(np.clip((k - above) / g_size, 0.0, 1.0), g_size)
    cut = (above < k) & (above + g_size > k)
    return prob, len(np.unique(d[g_start][cut])) / max(1, len(np.unique(day)))


def review_list(w: World, arm: Arm, k: int, draws: int, seed: int) -> dict:
    """Recall@k of the daily review list over every scored day (days 90 to the last)."""
    n_ep = len(w.meta["episodes"])
    pri = np.round(arm.plain.p, KEY_DECIMALS)
    sec = np.round(arm.list_secondary, KEY_DECIMALS)
    credited = np.flatnonzero(arm.plain.episode >= 0)
    credit = {
        "credited": (credited, arm.plain.episode[credited]),
        "day_credited": (w.pair_day, w.pair_ep),
    }
    universe = np.zeros(n_ep, dtype=bool)
    universe[w.pair_ep] = True
    masks = {"all": universe} | {
        kind: universe & (w.ep_kind == i) for i, kind in enumerate(w.meta["kinds"])
    }
    exact_p, cut_share = _exact_topk(w.day, pri, sec, k)
    random_p = np.minimum(1.0, k / np.bincount(w.day)[w.day])
    rng = np.random.default_rng(seed)
    hits = {rule: np.zeros((draws, n_ep), dtype=bool) for rule in credit}
    for i in range(draws):
        order = np.lexsort((rng.random(len(w.day)), -sec, -pri, w.day))
        rank = np.empty(len(order), dtype=np.int64)
        rank[order] = np.arange(len(order))
        listed = (rank - np.searchsorted(w.day[order], w.day, side="left")) < k
        for rule, (pd_, pe) in credit.items():
            np.logical_or.at(hits[rule][i], pe, listed[pd_])
    out: dict = {"k": k, "draws": draws, "seed": seed, "days_cut_in_a_tie": cut_share}
    for rule, (pd_, pe) in credit.items():
        exact = _caught_from_p(exact_p, pd_, pe, n_ep)
        rand = _caught_from_p(random_p, pd_, pe, n_ep)
        block = {}
        for name, m in masks.items():
            if not m.any():
                continue
            per_draw = hits[rule][:, m].mean(axis=1)
            rec, rnd = float(per_draw.mean()), float(rand[m].mean())
            block[name] = {
                "episodes": int(m.sum()),
                "recall": rec,
                "recall_sd_over_draws": float(per_draw.std(ddof=1)) if draws > 1 else 0.0,
                "recall_exact": float(exact[m].mean()),
                "random": rnd,
                "lift": rec / rnd if rnd > 0 else None,
                "lift_points": rec - rnd,
            }
        out[rule] = block
    slots = k * len(np.unique(w.day))  # the simulator's fill: share of the k x days slots
    out["fill"] = {cls: float(exact_p[w.label == i].sum() / slots) for i, cls in enumerate(CLASSES)}
    return out


# ── public API ───────────────────────────────────────────────────────────────────────────────
def _point(
    w: World,
    arm: Arm,
    label: str,
    kind: str,
    view: DayView,
    fit: dict,
    window: str,
    names: list[str],
) -> dict:
    t, u = fit["threshold"], fit.get("threshold_secondary") or 0.0
    call_s = arm.call_s if view is arm.tie_broken else np.zeros_like(arm.call_p)
    return {
        "label": label,
        "kind": kind,
        "key": "primary, then secondary" if view is arm.tie_broken else "primary",
        "threshold": t,
        "threshold_secondary": fit.get("threshold_secondary"),
        "fit": fit,
        "metrics": operating_point(
            w,
            view,
            _hot(view.p, view.s, t, u),
            _hot(arm.call_p, call_s, t, u),
            arm.call_p,
            window,
            names,
        ),
    }


def evaluate(
    npz_path: str | Path,
    primary,
    secondary=None,
    dstar=None,
    name: str = "arm",
    *,
    msg_primary=None,
    msg_secondary=None,
    msg_dstar=None,
    dstar_names: list[str] | None = None,
    fixed_lines: dict[str, float] | None = None,
    alphas: tuple[float, ...] = ALPHAS,
    list_sizes: tuple[int, ...] = LIST_SIZES,
    draws: int = LIST_DRAWS,
    seed: int = LIST_SEED,
) -> dict:
    """Evaluate one arm on one dumped world.

    ``primary``, ``secondary`` and ``dstar`` are aligned with the npz tool-call rows; the
    ``msg_*`` arguments with its non-call message rows (left out of the day maximum when
    ``msg_primary`` is None). ``dstar_names`` names the dstar indices (default: the sidecar's
    15 paper names). ``fixed_lines`` adds unfitted primary thresholds, reported on the report
    window and on every scored day. Every alpha gets a primary-only threshold and, when a
    secondary is given, a (primary, secondary) one. Returns a JSON-serialisable dict.
    """
    if not all(0 < a < 1 for a in alphas):
        raise ValueError(f"alphas must lie in (0, 1): {alphas}")
    w = load_world(npz_path)
    arm = build_arm(w, primary, secondary, dstar, msg_primary, msg_secondary, msg_dstar)
    names = dstar_names or [d["paper_name"] for d in w.meta["dimensions"]]
    lo, hi = FIT_DAYS
    fit_days = (w.day >= lo) & (w.day <= hi) & (w.label == ORDINARY)
    points = []
    for alpha in alphas:
        tag = f"alpha {100 * alpha:g}%"
        views = [(tag, arm.plain)]
        if arm.tie_broken is not None:
            views.append((f"{tag}, ties by secondary", arm.tie_broken))
        for label, view in views:
            fit = fit_threshold(view.p[fit_days], view.s[fit_days], alpha)
            points.append(_point(w, arm, label, "fitted", view, fit, "report", names))
    for line, t in (fixed_lines or {}).items():
        fit = {
            "threshold": t,
            "threshold_secondary": None,
            "fit_days": int(fit_days.sum()),
            "fit_rate": float((arm.plain.p[fit_days] >= t).mean()),
        }
        for window in ("report", "scored"):
            suffix = f", days {EVAL_FROM_DAY}-{w.last_day}" if window == "scored" else ""
            points.append(
                _point(w, arm, f"{line} fixed{suffix}", "fixed", arm.plain, fit, window, names)
            )
    notes = []
    if msg_primary is None:
        notes.append(
            "non-call messages are left out of the day maximum (msg_primary is None); "
            "they still label the day"
        )
    return {
        "name": name,
        "npz": w.path,
        "world": w.meta["world"],
        "caveat": w.meta["caveat"],
        "messages_in_day_max": msg_primary is not None,
        "notes": notes,
        "counts": {
            "tool_calls": w.n_calls,
            "non_call_messages": w.n_msgs,
            "agent_days_scored": len(w.day),
            "fit_ordinary_agent_days": int(fit_days.sum()),
            "last_day": w.last_day,
            "episodes": len(w.meta["episodes"]),
        },
        "operating_points": points,
        "review_list": [review_list(w, arm, k, draws, seed) for k in list_sizes],
    }


def v4_reference(npz_path: str | Path, check: bool = True) -> dict:
    """The v4 reference: primary = M, secondary = s2, d* = dstar, messages as the simulator."""
    path = Path(npz_path)
    with np.load(path) as z:
        cols = {k: z[k] for k in ("M", "s2", "dstar", "msg_M", "msg_s2", "msg_dstar")}
    res = evaluate(
        path,
        cols["M"],
        cols["s2"],
        cols["dstar"],
        name="v4 (M, then s2)",
        msg_primary=cols["msg_M"],
        msg_secondary=cols["msg_s2"],
        msg_dstar=cols["msg_dstar"],
        fixed_lines=dict([V4_FIXED_LINE]),
    )
    if check:
        res["check"] = check_v4(res)
    return res


# ── the check of v4 at x3 against dump_vectors.py's validation file ──────────────────────────
def simulator_view(res: dict) -> dict[str, float]:
    """Our v4-at-x3 numbers on days 90-180, under the keys of ``normal_org_sim.analyse``."""
    pt = next(
        p
        for p in res["operating_points"]
        if p["kind"] == "fixed" and p["metrics"]["window"][0] == EVAL_FROM_DAY
    )
    m = pt["metrics"]
    w = load_world(res["npz"])
    key_of = {d["paper_name"]: d["key"] for d in w.meta["dimensions"]}
    out = {
        "agent_days": len(w.day),
        "ordinary_days_x3": m["by_day_label"]["ordinary"]["rate"],
        "ordinary_days_x3_people": m["strata"]["is_bot"]["people"]["ordinary"]["rate"],
        "ordinary_days_x3_bots": m["strata"]["is_bot"]["bots"]["ordinary"]["rate"],
        "ordinary_calls_x3": m["per_call"]["ordinary"]["rate"],
        "gray_episodes": m["gray"]["overall"]["episodes"],
        "gray_caught_x3": m["gray"]["overall"]["recall"],
    }
    for cls, v in m["alerts_per_day"].items():
        out[f"alerts_per_day.{cls}"] = v
    for kind, g in m["gray"]["by_kind"].items():
        if g["episodes"]:
            out[f"gray.{kind}.episodes"] = g["episodes"]
            out[f"gray.{kind}.caught_x3"] = g["recall"]
            out[f"gray.{kind}.median_max_M"] = g["median_max_primary"]
            out[f"gray.{kind}.calls_x3"] = g["call_share_episode_mean"]
    for tag, t in m["change_by_tag"].items():
        if t["days"]:
            out[f"changes_x3.{tag}.days"] = t["days"]
            out[f"changes_x3.{tag}.x3"] = round(t["rate"], 3)
    causes = m["benign_alert_reasons"]["ordinary"]["share"]
    for paper, share in list(causes.items())[:8]:
        out[f"ordinary_x3_causes.{key_of.get(paper, paper)}"] = round(share, 3)
    for lst in res["review_list"]:
        prefix = f"review.top {lst['k']} | {V4_LIST}"
        out[f"{prefix}.gray_caught"] = lst["day_credited"]["all"]["recall_exact"]
        out[f"{prefix}.days_cut_in_a_tie"] = lst["days_cut_in_a_tie"]
        for cls, v in lst["fill"].items():
            out[f"{prefix}.fill.{cls}"] = v
    return out


def _flat(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(_flat(v, f"{prefix}{k}."))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[f"{prefix}{k}"] = v
    return out


def check_v4(res: dict) -> dict:
    """Compare v4 at x3 (days 90-180) with ``<npz>.validation.json`` from dump_vectors.py."""
    vpath = Path(res["npz"]).with_suffix(".validation.json")
    if not vpath.exists():
        return {"validation_file": str(vpath), "status": "missing"}
    report = json.loads(vpath.read_text())
    saved: dict = {}
    if "rebuilt" in report:  # a world without a saved results file (smoke)
        ref = _flat(report["rebuilt"]["all messages"])
    else:  # a full world: rebuilt values for VALIDATED_KEYS, and the saved results file
        ref = {r["metric"]: r["all messages"] for r in report["metrics"]}
        saved = {r["metric"]: r["saved"] for r in report["metrics"]}
        for r in report.get("gray_by_kind", []):
            ref[f"gray.{r['kind']}.caught_x3"] = r["rebuilt"]
            saved[f"gray.{r['kind']}.caught_x3"] = r["saved"]
        for c, v in report.get("causes_rebuilt", {}).items():
            ref[f"ordinary_x3_causes.{c}"] = v
        for c, v in report.get("causes_saved", {}).items():
            saved[f"ordinary_x3_causes.{c}"] = v
    ours = simulator_view(res)
    rows = []
    for key in sorted(set(ref) | set(ours)):
        if key not in ours or key not in ref:
            continue
        rounded = key.startswith(("changes_x3.", "ordinary_x3_causes."))
        tol = ROUNDED_TOLERANCE if rounded else CHECK_TOLERANCE
        diff = ours[key] - ref[key]
        rows.append(
            {
                "metric": key,
                "validation": ref[key],
                "ours": ours[key],
                "diff": diff,
                "saved_results": saved.get(key),
                "match": abs(diff) <= tol,
            }
        )
    only_ref = sorted(k for k in ref if k not in ours)
    only_ours = sorted(k for k in ours if k not in ref)
    return {
        "validation_file": str(vpath),
        "compared": len(rows),
        "mismatches": [r["metric"] for r in rows if not r["match"]],
        "rows": rows,
        "not_compared_validation_only": only_ref,
        "not_compared_ours_only": only_ours,
    }


# ── markdown ─────────────────────────────────────────────────────────────────────────────────
def _pct(x, digits: int = 2) -> str:
    return (
        "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.{digits}f}%"
    )


def _num(x, digits: int = 3) -> str:
    if x is None:
        return "-"
    if isinstance(x, float) and math.isinf(x):
        return "+inf" if x > 0 else "-inf"
    return f"{x:.{digits}f}"


def _threshold(p: dict) -> str:
    if p["threshold"] is None:
        return "none (infeasible)"
    if p["threshold_secondary"] is None or p["key"] == "primary":
        return _num(p["threshold"])
    return f"({_num(p['threshold'])}, {_num(p['threshold_secondary'])})"


def _ci(r: dict) -> str:
    if not r["episodes"]:
        return "-"
    lo, hi = r["wilson95"]
    return f"{r['caught']}/{r['episodes']} = {_pct(r['recall'], 1)} [{_pct(lo, 0)}, {_pct(hi, 0)}]"


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out


def _arm_markdown(res: dict) -> list[str]:
    c = res["counts"]
    pts = res["operating_points"]
    rep = next((p for p in pts if p["metrics"]["window"][0] == REPORT_FIRST_DAY), pts[0])
    lab = rep["metrics"]["by_day_label"]
    lines = [
        f"## {res['name']} on {res['world']} (development world)",
        "",
        f"{res['caveat']}",
        "",
        f"Tool calls {c['tool_calls']:,}; non-call messages {c['non_call_messages']:,} "
        f"({'in' if res['messages_in_day_max'] else 'left out of'} the day maximum). "
        f"Scored agent-days {c['agent_days_scored']:,} (days 90-{c['last_day']}); ordinary "
        f"agent-days in the fit window (90-134) {c['fit_ordinary_agent_days']:,}. Report window "
        f"(days 135-{c['last_day']}): {lab['ordinary']['days']:,} ordinary, "
        f"{lab['change']['days']:,} change, {lab['gray']['days']:,} gray agent-days; "
        f"{rep['metrics']['gray']['overall']['episodes']} gray episodes. "
        f"{rep['metrics']['change_days_with_one_tagged_row']:,} of the change agent-days carry "
        "a single tagged message.",
        "",
    ]
    lines += [f"Note: {n}." for n in res["notes"]] + ([""] if res["notes"] else [])
    lines += ["### Operating points", ""]
    rows = []
    for p in pts:
        m, f = p["metrics"], p["fit"]
        d, t, pc = m["by_day_label"], m["by_top_call_label"], m["per_call"]
        a = m["alerts_per_1000_agent_days"]
        rows.append(
            [
                p["label"],
                f"{m['window'][0]}-{m['window'][1]}",
                _threshold(p),
                f"{_pct(f['fit_rate'])} ({_pct(f.get('fit_rate_next_value'))})",
                str(f.get("ties_at_threshold", "-")),
                _pct(d["ordinary"]["rate"]),
                _pct(d["change"]["rate"]),
                _pct(d["benign"]["rate"]),
                f"{_pct(t['ordinary']['rate'])} / {_pct(t['change']['rate'])}",
                f"{_pct(pc['ordinary']['rate'], 3)} / {_pct(pc['change']['rate'], 3)}",
                _ci(m["gray"]["overall"]),
                _pct(m["gray"]["overall"]["call_share"], 1),
                f"{_pct(m['precision']['day'], 1)} / {_pct(m['precision']['credited'], 1)}",
                f"{a['all']:.1f} ({a['ordinary']:.1f} / {a['change']:.1f} / {a['gray']:.1f})",
            ]
        )
    lines += _table(
        [
            "Point",
            "Days",
            "Threshold",
            "Fit rate (one value lower)",
            "Ties at t",
            "Ordinary",
            "Change",
            "All benign",
            "Top-call ordinary / change",
            "Ordinary / change calls",
            "Gray recall [Wilson 95%]",
            "Gray calls >= t",
            "Precision day / credited",
            "Alerts per 1,000 agent-days (ord / chg / gray)",
        ],
        rows,
    )
    kinds = [k for k, g in rep["metrics"]["gray"]["by_kind"].items() if g["episodes"]]
    lines += ["", "### Gray episodes by kind", ""]
    rows = []
    for p in pts:
        g = p["metrics"]["gray"]["by_kind"]
        rows.append(
            [p["label"]]
            + [
                f"{_ci(g[k])}; calls {_pct(g[k]['call_share'], 0)}" if g[k]["episodes"] else "-"
                for k in kinds
            ]
        )
    lines += _table(["Point"] + kinds, rows)
    lines += ["", f"### Review list (days 90-{c['last_day']}, every day)", ""]
    rows = []
    for lst in res["review_list"]:
        cr, dc = lst["credited"]["all"], lst["day_credited"]["all"]
        rows.append(
            [
                str(lst["k"]),
                f"{_pct(cr['recall'], 1)} (sd {_pct(cr['recall_sd_over_draws'], 1)})",
                _pct(cr["recall_exact"], 1),
                _pct(cr["random"], 1),
                "-" if cr["lift"] is None else f"{cr['lift']:.2f}x",
                _pct(dc["recall"], 1),
                _pct(dc["recall_exact"], 1),
                _pct(dc["random"], 1),
                _pct(lst["days_cut_in_a_tie"], 1),
                " / ".join(_pct(lst["fill"][x], 0) for x in CLASSES),
            ]
        )
    lines += _table(
        [
            "k",
            f"Credited recall ({res['review_list'][0]['draws']} draws)",
            "Credited, exact",
            "Random, same credit",
            "Lift",
            "Day-credited (old rule)",
            "Day-credited, exact",
            "Random, day credit",
            "Days cut in a tie",
            "Fill ord / chg / gray",
        ],
        rows,
    )
    lines += ["", "Credited recall by kind (random in brackets, then lift):", ""]
    rows = []
    for lst in res["review_list"]:
        cr = lst["credited"]
        rows.append(
            [str(lst["k"])]
            + [
                f"{_pct(cr[k]['recall'], 0)} ({_pct(cr[k]['random'], 0)}, "
                f"{'-' if cr[k]['lift'] is None else format(cr[k]['lift'], '.1f') + 'x'})"
                if k in cr
                else "-"
                for k in kinds
            ]
        )
    lines += _table(["k"] + kinds, rows)
    lines += ["", "### Reasons for benign alerts (d* of the top row)", ""]
    rows = []
    for p in pts:
        r = p["metrics"]["benign_alert_reasons"]
        cells = []
        for cls in ("ordinary", "change"):
            top3 = list(r[cls]["share"].items())[:3]
            shares = ", ".join(f"{k} {_pct(v, 0)}" for k, v in top3)
            cells.append(f"n={r[cls]['alerts']}" + (f": {shares}" if shares else ""))
        rows.append([p["label"]] + cells)
    lines += _table(["Point", "Ordinary agent-days", "Change agent-days"], rows)
    lines += ["", "### Strata (report window; history band = A, his active days)", ""]
    rows = []
    for p in pts:
        if p["metrics"]["window"][0] != REPORT_FIRST_DAY:
            continue
        st = p["metrics"]["strata"]
        for group in ("is_bot", "history"):
            for sname, s in st[group].items():
                if not (s["ordinary"]["days"] or s["change"]["days"] or s["gray"]["episodes"]):
                    continue
                rows.append(
                    [
                        p["label"],
                        sname,
                        f"{s['ordinary']['days']:,}",
                        _pct(s["ordinary"]["rate"]),
                        f"{s['change']['days']:,}",
                        _pct(s["change"]["rate"]),
                        _pct(s["benign"]["rate"]),
                        _ci(s["gray"]),
                    ]
                )
    lines += _table(
        [
            "Point",
            "Stratum",
            "Ordinary days",
            "Ordinary rate",
            "Change days",
            "Change rate",
            "All benign",
            "Gray recall",
        ],
        rows,
    )
    if "check" in res:
        lines += ["", *_check_markdown(res["check"])]
    return lines


def _check_markdown(chk: dict) -> list[str]:
    lines = [f"### v4 at x3 (days 90-180) against `{Path(chk['validation_file']).name}`", ""]
    if chk.get("status") == "missing":
        return lines + ["Validation file missing; no check."]
    lines.append(
        f"{chk['compared']} values compared; mismatches: {', '.join(chk['mismatches']) or 'none'}."
    )
    lines.append("")
    has_saved = any(r["saved_results"] is not None for r in chk["rows"])
    header = ["Metric", "Validation (analyse on this npz)", "Ours", "Diff", "Match"]
    rows = []
    for r in chk["rows"]:
        row = [
            r["metric"].replace("|", "\\|"),  # simulator list names contain a pipe
            _num(r["validation"], 6),
            _num(r["ours"], 6),
            f"{r['diff']:.1e}",
            "yes" if r["match"] else "NO",
        ]
        if has_saved:
            row.insert(2, _num(r["saved_results"], 6))
        rows.append(row)
    if has_saved:
        header.insert(2, "Saved results/*.json")
    lines += _table(header, rows)
    lines += [
        "",
        f"Not compared (validation only): {len(chk['not_compared_validation_only'])} "
        "keys (the simulator's other rankings, its x2 line, the median tie size at the cut).",
    ]
    return lines


def _comparison(results: list[dict]) -> list[str]:
    lines = ["## Arms side by side (report window, development world)", ""]
    rows = []
    for res in results:
        lists = {lst["k"]: lst["credited"]["all"] for lst in res["review_list"]}
        for p in res["operating_points"]:
            m = p["metrics"]
            if m["window"][0] != REPORT_FIRST_DAY:
                continue
            rows.append(
                [
                    res["name"],
                    p["label"],
                    _pct(p["fit"]["fit_rate"]),
                    _pct(m["by_day_label"]["ordinary"]["rate"]),
                    _pct(m["by_day_label"]["benign"]["rate"]),
                    _ci(m["gray"]["overall"]),
                    _pct(m["precision"]["credited"], 1),
                    f"{m['alerts_per_1000_agent_days']['all']:.1f}",
                    " / ".join(_pct(lists[k]["recall"], 1) for k in sorted(lists)),
                ]
            )
    ks = "/".join(str(lst["k"]) for lst in results[0]["review_list"])
    return lines + _table(
        [
            "Arm",
            "Point",
            "Fit rate",
            "Ordinary",
            "All benign",
            "Gray recall",
            "Credited precision",
            "Alerts per 1,000",
            f"List recall @{ks}",
        ],
        rows,
    )


def to_markdown(results: dict | list[dict]) -> str:
    """Markdown tables for one result or several (several: a side-by-side table first)."""
    items = [results] if isinstance(results, dict) else list(results)
    lines: list[str] = []
    if len(items) > 1:
        lines += _comparison(items) + [""]
    for res in items:
        lines += _arm_markdown(res) + [""]
    return "\n".join(lines)


def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, float) and (math.isinf(x) or math.isnan(x)):
        return None if math.isnan(x) else ("inf" if x > 0 else "-inf")
    if isinstance(x, np.generic):
        return _jsonable(x.item())
    return x


def main() -> None:
    ap = argparse.ArgumentParser(description="Print the v4 reference of a dumped world.")
    ap.add_argument("npz", type=Path, help="an npz written by dump_vectors.py")
    ap.add_argument("--json", type=Path, help="also save the result dict as JSON")
    ap.add_argument("--md", type=Path, help="also save the markdown")
    ap.add_argument("--no-check", action="store_true", help="skip the validation-file check")
    args = ap.parse_args()
    res = v4_reference(args.npz, check=not args.no_check)
    md = to_markdown(res)
    print(md)
    print("\nMetric definitions:\n" + METRIC_DEFINITIONS)
    if args.json:
        args.json.write_text(json.dumps(_jsonable(res), indent=1))
    if args.md:
        args.md.write_text(md + "\n\n## Metric definitions\n\n" + METRIC_DEFINITIONS)
    if res.get("check", {}).get("mismatches"):
        raise SystemExit(f"v4 check failed: {res['check']['mismatches']}")


if __name__ == "__main__":
    main()
