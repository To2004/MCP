"""EV-22: outside baselines, scored per agent-day at the same budget as v5 (spec 6.7).

Each baseline returns one score per agent-day (higher = stranger). Like every combiner arm, it
then gets its own threshold, fitted on the calibration pool's unlabelled agent-days at the same
alpha (:func:`heldout_metrics.fit_threshold`), and is compared at the same list length L.

Baselines (spec 6.7 and Part A EV-22; the competitor descriptions are note 02's, lines 49-51):

- **static only**: the day's largest R_static (list only);
- **Red Flags only**: v5's statistic over the Red Flags group, offline;
- **per-agent max |z|** over agent-day counts (calls, writes, distinct assets, distinct tools,
  new values, night calls), against the caller's own earlier days; sd floored at 1;
- **Isolation Forest** per world, trained only on days 0-89, with (n_estimators,
  max_samples) from :data:`IFOREST_GRID`, chosen on the calibration pool by
  :func:`choose_iforest_grid`; numpy only;
- **role peer group**: median / MAD of the role's training days;
- **MCP Guardian-style**: the most calls in any one minute (a fixed per-identity rate limit);
- **AegisMCP-style**: org-wide rarity of (tool, sensitivity, network type) on earlier days;
- **Praetor-style**: a per-agent allowlist of (tool, asset) edges and 3-call contexts learned
  on days 0-29, ranked by unseen items per agent-day;
- **personal-day calibration** and **org calibration**: simplified ports of the probe arms
  ``calib_personal_day.py`` and ``calib_org_normalised.py`` (see each function).

v1-v4 come straight from their score logs and need no code here.

Days are deployment days (day 0 = the world's first day; ``heldout_metrics.local_day_keys`` with
``base_day``): the training and learning windows above count from it, and 1970-based day keys
are refused.

Every number from a simulator world is a development-world or synthetic number until it comes
from a frozen held-out run.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import ArrayLike

try:  # imported as part of the heldout package (tests, other harness modules)
    from . import combiner_family as cf
    from . import heldout_metrics as hm
except ImportError:  # run as a script: the sibling modules are on sys.path
    import combiner_family as cf  # type: ignore[no-redef]
    import heldout_metrics as hm  # type: ignore[no-redef]

# ── frozen constants ─────────────────────────────────────────────────────────────────────────
FEATURES = ("calls", "writes", "distinct_assets", "distinct_tools", "new_values", "night_calls")
NIGHT_HOURS = frozenset({22, 23, 0, 1, 2, 3, 4, 5})  # local wall-clock hours
HISTORY_DAYS = 90  # per-agent z: the caller's earlier days in the last 90
SD_FLOOR = 1.0  # Part A: sd floored at 1
MAD_SCALE = 1.4826  # MAD to sd under normality
TRAIN_LAST_DAY = hm.EVAL_FROM_DAY - 1  # Isolation Forest and peers train on days 0-89
PRAETOR_LEARN = (0, 29)  # Praetor-style allowlists are learned on days 0-29
CONTEXT_CALLS = 3  # Praetor-style call context length
RATE_WINDOW_S = 60.0  # Guardian-style: calls per minute
IFOREST_GRID = ((100, 256), (100, 1024), (300, 256), (300, 1024))  # (n_estimators, max_samples)
IFOREST_SEED = 20_261_028
EULER_GAMMA = 0.5772156649015329
PERSONAL_PAST_DAYS = 89  # personal-day calibration: days t-89 .. t-1
ORG_POOL_DAYS = 60  # org calibration: the last 60 days before the scored day
MISSING = ""  # a missing categorical value (no asset, no network)


@dataclass(frozen=True)
class CallTable:
    """Per-call columns the baselines read (one row per scored call, input order)."""

    agent: np.ndarray
    day: np.ndarray  # local-day key
    ts: np.ndarray
    hour: np.ndarray  # local wall-clock hour
    tool: np.ndarray
    asset: np.ndarray  # "" when the call touched none
    is_write: np.ndarray
    network: np.ndarray
    client: np.ndarray
    sensitivity: np.ndarray  # 0 when unknown
    r_static: np.ndarray
    seq: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.int64))

    def __post_init__(self) -> None:
        n = len(self.agent)
        cols = (self.day, self.ts, self.hour, self.tool, self.asset, self.is_write)
        cols += (self.network, self.client, self.sensitivity, self.r_static)
        if n == 0 or any(len(c) != n for c in cols):
            raise ValueError("every column must give one value per call")
        if len(self.seq) not in (0, n):
            raise ValueError("seq must be empty or give one value per call")

    def agent_days(self) -> hm.AgentDays:
        """The calls' agent-days (stream order = ``seq``, else ``ts``)."""
        return hm.group_agent_days(self.agent, self.day, self.seq if len(self.seq) else self.ts)


def _codes(values: ArrayLike) -> tuple[np.ndarray, int]:
    _, code = np.unique(np.asarray(values), return_inverse=True)
    return code.astype(np.int64), int(code.max()) + 1


def _triple_codes(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """One integer code per distinct (a, b, c) row."""
    ca, _ = _codes(a)
    cb, nb = _codes(b)
    cc, nc = _codes(c)
    return (ca * nb + cb) * nc + cc


def _distinct_per_day(days: hm.AgentDays, key: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """Per agent-day: the number of distinct ``key`` values among its calls where ``keep``."""
    pairs = np.unique(np.stack([days.of_call[keep], key[keep]], axis=1), axis=0)
    if len(pairs) == 0:
        return np.zeros(days.n_days)
    return np.bincount(pairs[:, 0], minlength=days.n_days).astype(np.float64)


def _new_values(days: hm.AgentDays, calls: CallTable) -> np.ndarray:
    """Per agent-day: distinct (kind, value) pairs the caller used for the first time that day,
    over tool, asset, network and client."""
    agent, n_agents = _codes(calls.agent)
    total = np.zeros(days.n_days)
    day = np.asarray(calls.day, dtype=np.int64)
    for column in (calls.tool, calls.asset, calls.network, calls.client):
        col = np.asarray(column)
        value, n_values = _codes(col)
        key = agent * n_values + value
        uniq, inverse = np.unique(key, return_inverse=True)
        first = np.full(len(uniq), np.iinfo(np.int64).max)
        np.minimum.at(first, inverse, day)
        keep = (day == first[inverse]) & (col != MISSING)
        total += _distinct_per_day(days, key, keep)
    return total


def agent_day_features(days: hm.AgentDays, calls: CallTable) -> np.ndarray:
    """Agent-days x :data:`FEATURES`: calls, writes, distinct assets, distinct tools, new
    values and night calls."""
    n = days.n_days
    tool, _ = _codes(calls.tool)
    asset, _ = _codes(calls.asset)
    has_asset = np.asarray(calls.asset) != MISSING
    night = np.isin(np.asarray(calls.hour), list(NIGHT_HOURS))
    return np.stack(
        [
            np.bincount(days.of_call, minlength=n),
            np.bincount(days.of_call, weights=np.asarray(calls.is_write, float), minlength=n),
            _distinct_per_day(days, asset, has_asset),
            _distinct_per_day(days, tool, np.ones(len(tool), bool)),
            _new_values(days, calls),
            np.bincount(days.of_call, weights=night.astype(float), minlength=n),
        ],
        axis=1,
    ).astype(np.float64)


# ── simple baselines ─────────────────────────────────────────────────────────────────────────
def static_only(days: hm.AgentDays, r_static: ArrayLike) -> np.ndarray:
    """The day's largest R_static (list-only baseline)."""
    return hm.day_max(days, r_static).score


def red_flags_only(days: hm.AgentDays, evidence: cf.CallEvidence) -> np.ndarray:
    """The day's largest Red Flags s1, v5's statistic over that group alone (offline)."""
    return hm.day_max(days, cf.red_flags_statistic(evidence)).score


def guardian_rate(days: hm.AgentDays, ts: ArrayLike, window_s: float = RATE_WINDOW_S) -> np.ndarray:
    """MCP Guardian-style: the most calls the agent made in any ``window_s`` seconds of the
    day (a fixed per-identity calls-per-minute limit ranks days by this)."""
    t = np.asarray(ts, dtype=np.float64)[days.order]
    group = days.sorted_group
    base = t[days.starts][group]
    span = 2 * (t - base).max(initial=0.0) + 2 * window_s
    key = group * span + (t - base)
    order = np.lexsort((key,))
    key = key[order]
    end = np.searchsorted(key, key + window_s, side="left")
    counts = end - np.arange(len(key))
    out = np.zeros(days.n_days)
    np.maximum.at(out, group[order], counts)
    return out


def aegis_rarity(
    days: hm.AgentDays, tool: ArrayLike, sensitivity: ArrayLike, network_type: ArrayLike
) -> np.ndarray:
    """AegisMCP-style org-wide rarity: per call, -log((1 + earlier org calls with the same
    (tool, sensitivity, network type)) / (1 + earlier org calls)), on days before the call's;
    the agent-day takes its largest."""
    parts = [np.asarray(c).astype(str) for c in (tool, sensitivity, network_type)]
    if any(p.shape != (days.n_calls,) for p in parts):
        raise ValueError("tool, sensitivity and network_type must give one value per call")
    code = _triple_codes(*parts)
    day = days.day[days.of_call]
    day_code, n_days = _codes(day)
    per_day = np.bincount(day_code, minlength=n_days)
    before = np.r_[0, np.cumsum(per_day)[:-1]]  # org calls on earlier days
    pair = code * n_days + day_code
    uniq, inverse, counts = np.unique(pair, return_inverse=True, return_counts=True)
    owner = uniq // n_days
    run_start = np.r_[True, owner[1:] != owner[:-1]]
    cum = np.cumsum(counts)
    offset = np.maximum.accumulate(np.where(run_start, cum - counts, 0))
    earlier = (cum - counts - offset)[inverse]  # same triple on earlier days
    rarity = -np.log((1 + earlier) / (1 + before[day_code]))
    return hm.day_max(days, rarity).score


def praetor_unseen(
    days: hm.AgentDays,
    agent: ArrayLike,
    tool: ArrayLike,
    asset: ArrayLike,
    learn: tuple[int, int] = PRAETOR_LEARN,
) -> np.ndarray:
    """Praetor-style: per agent, an allowlist of (tool, asset) edges and of 3-call tool
    contexts learned on the ``learn`` days; an agent-day scores its distinct unseen edges plus
    its distinct unseen contexts. Contexts follow the agent's stream order."""
    a, _ = _codes(agent)
    t, n_tools = _codes(tool)
    s, n_assets = _codes(asset)
    day = days.day[days.of_call]
    learned = hm.in_window(day, learn)
    edge = (a * n_tools + t) * n_assets + s
    unseen_edge = ~np.isin(edge, edge[learned])
    total = _distinct_per_day(days, edge, unseen_edge)
    order = days.order
    ao, to = a[order], t[order]
    full = np.zeros(len(order), dtype=bool)
    full[CONTEXT_CALLS - 1 :] = ao[CONTEXT_CALLS - 1 :] == ao[: len(ao) - CONTEXT_CALLS + 1]
    context = np.zeros(len(order), dtype=np.int64)
    for lag in range(CONTEXT_CALLS):
        shifted = np.r_[np.zeros(lag, dtype=np.int64), to[: len(to) - lag]]
        context = context * n_tools + shifted
    context = context * (int(a.max()) + 1) + ao
    ctx = np.empty(len(order), dtype=np.int64)
    ctx[order] = context
    has = np.empty(len(order), dtype=bool)
    has[order] = full
    unseen_ctx = has & ~np.isin(ctx, ctx[has & learned])
    return total + _distinct_per_day(days, ctx, unseen_ctx)


# ── per-agent and peer z ─────────────────────────────────────────────────────────────────────
def per_agent_max_z(
    days: hm.AgentDays,
    features: ArrayLike,
    *,
    history_days: int = HISTORY_DAYS,
    sd_floor: float = SD_FLOOR,
) -> np.ndarray:
    """Per agent-day: max over features of |x - mean| / max(sd, sd_floor), mean and sd over
    the same caller's agent-days in [t - history_days, t - 1] (causal). 0 with no history."""
    x = np.asarray(features, dtype=np.float64)
    if x.shape[0] != days.n_days:
        raise ValueError("features must give one row per agent-day")
    lo = hm.past_window_start(days, history_days)
    i = np.arange(days.n_days)
    n = (i - lo).astype(np.float64)[:, None]
    cs = np.vstack([np.zeros(x.shape[1]), np.cumsum(x, axis=0)])
    cs2 = np.vstack([np.zeros(x.shape[1]), np.cumsum(x * x, axis=0)])
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = (cs[i] - cs[lo]) / n
        var = np.clip((cs2[i] - cs2[lo]) / n - mean**2, 0.0, None)
        z = np.abs(x - mean) / np.maximum(np.sqrt(var), sd_floor)
    return np.where(n[:, 0] > 0, z.max(axis=1), 0.0)


def role_peer_group(
    days: hm.AgentDays,
    features: ArrayLike,
    role: ArrayLike,
    *,
    train_last_day: int = TRAIN_LAST_DAY,
    sd_floor: float = SD_FLOOR,
) -> np.ndarray:
    """Per agent-day: max over features of |x - median| / max(1.4826 MAD, sd_floor), against
    the role's agent-days up to ``train_last_day`` (every role's when the role has none)."""
    x = np.asarray(features, dtype=np.float64)
    r = np.asarray(role)
    if x.shape[0] != days.n_days or r.shape != (days.n_days,):
        raise ValueError("features and role must give one entry per agent-day")
    hm.check_deployment_days(days.day)
    train = days.day <= train_last_day
    if not train.any():
        raise ValueError(f"no agent-day on or before day {train_last_day} to train on")
    out = np.empty(days.n_days)
    for label in np.unique(r):
        rows = r == label
        ref = x[train & rows] if (train & rows).any() else x[train]
        med = np.median(ref, axis=0)
        mad = np.median(np.abs(ref - med), axis=0)
        z = np.abs(x[rows] - med) / np.maximum(MAD_SCALE * mad, sd_floor)
        out[rows] = z.max(axis=1)
    return out


# ── Isolation Forest (numpy) ─────────────────────────────────────────────────────────────────
def average_path(n: ArrayLike) -> np.ndarray:
    """c(n), the mean path length of an unsuccessful BST search: 2 H(n - 1) - 2 (n - 1) / n,
    1 for n = 2 and 0 below (Liu et al. 2008)."""
    m = np.asarray(n, dtype=np.float64)
    safe = np.maximum(m, 2.0)
    harmonic = np.log(safe - 1.0) + EULER_GAMMA
    out = 2.0 * harmonic - 2.0 * (safe - 1.0) / safe
    return np.where(m > 2, out, np.where(m == 2, 1.0, 0.0))


@dataclass(frozen=True)
class _Tree:
    feature: np.ndarray  # -1 at a leaf
    split: np.ndarray
    left: np.ndarray
    right: np.ndarray
    size: np.ndarray  # rows reaching a leaf
    depth: np.ndarray


def _grow(x: np.ndarray, rng: np.random.Generator, limit: int) -> _Tree:
    feature, split, left, right, size, depth = [], [], [], [], [], []
    stack = [(np.arange(len(x)), 0, -1, False)]
    while stack:
        rows, level, parent, is_right = stack.pop()
        node = len(feature)
        if parent >= 0:
            (right if is_right else left)[parent] = node
        sub = x[rows]
        lo, hi = sub.min(axis=0), sub.max(axis=0)
        usable = np.flatnonzero(hi > lo)
        feature.append(-1)
        split.append(0.0)
        left.append(-1)
        right.append(-1)
        size.append(len(rows))
        depth.append(level)
        if level >= limit or len(rows) <= 1 or len(usable) == 0:
            continue
        f = int(rng.choice(usable))
        cut = float(rng.uniform(lo[f], hi[f]))
        feature[node], split[node] = f, cut
        goes_left = sub[:, f] < cut
        stack.append((rows[~goes_left], level + 1, node, True))
        stack.append((rows[goes_left], level + 1, node, False))
    return _Tree(*(np.array(v) for v in (feature, split, left, right, size, depth)))


def _path_length(tree: _Tree, x: np.ndarray) -> np.ndarray:
    node = np.zeros(len(x), dtype=np.int64)
    while True:
        inner = tree.feature[node] >= 0
        if not inner.any():
            break
        rows = np.flatnonzero(inner)
        f = tree.feature[node[rows]]
        goes_left = x[rows, f] < tree.split[node[rows]]
        node[rows] = np.where(goes_left, tree.left[node[rows]], tree.right[node[rows]])
    return tree.depth[node] + average_path(tree.size[node])


class IsolationForest:
    """Liu, Ting and Zhou's Isolation Forest in numpy: random axis-parallel splits on
    subsamples of ``max_samples`` rows, depth limit ceil(log2 psi); the anomaly score is
    2^(-E[h(x)] / c(psi)), higher = stranger."""

    def __init__(
        self, n_estimators: int = 100, max_samples: int = 256, seed: int = IFOREST_SEED
    ) -> None:
        if n_estimators < 1 or max_samples < 2:
            raise ValueError("need n_estimators >= 1 and max_samples >= 2")
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.seed = seed
        self.trees: list[_Tree] = []
        self.psi = 0

    def fit(self, x: ArrayLike) -> IsolationForest:
        """Grow the trees on the training rows ``x`` (rows x features)."""
        data = np.asarray(x, dtype=np.float64)
        if data.ndim != 2 or len(data) < 2:
            raise ValueError("fit needs at least two training rows")
        rng = np.random.default_rng(self.seed)
        self.psi = min(self.max_samples, len(data))
        limit = math.ceil(math.log2(self.psi))
        self.trees = [
            _grow(data[rng.choice(len(data), self.psi, replace=False)], rng, limit)
            for _ in range(self.n_estimators)
        ]
        return self

    def score(self, x: ArrayLike) -> np.ndarray:
        """Anomaly score in (0, 1] per row; ``RuntimeError`` before :meth:`fit`."""
        if not self.trees:
            raise RuntimeError("fit the forest first")
        data = np.asarray(x, dtype=np.float64)
        mean_path = np.mean([_path_length(t, data) for t in self.trees], axis=0)
        return 2.0 ** (-mean_path / average_path(self.psi))


def isolation_forest(
    days: hm.AgentDays,
    features: ArrayLike,
    *,
    n_estimators: int = IFOREST_GRID[0][0],
    max_samples: int = IFOREST_GRID[0][1],
    train_last_day: int = TRAIN_LAST_DAY,
    seed: int = IFOREST_SEED,
) -> np.ndarray:
    """Per agent-day Isolation Forest score for one world, trained only on its agent-days up
    to ``train_last_day`` (no scored day enters training)."""
    x = np.asarray(features, dtype=np.float64)
    if x.shape[0] != days.n_days:
        raise ValueError("features must give one row per agent-day")
    hm.check_deployment_days(days.day)
    train = days.day <= train_last_day
    forest = IsolationForest(n_estimators, max_samples, seed).fit(x[train])
    return forest.score(x)


def choose_iforest_grid(objective: Mapping[tuple[int, int], float]) -> tuple[int, int]:
    """EV-22's choice of (n_estimators, max_samples): the :data:`IFOREST_GRID` point with the
    highest objective on the **calibration pool**, ties to the cheaper point (fewer trees,
    then fewer samples).

    The objective is the baseline's mean per-world credited pAUC on the calibration pool's
    report window (``heldout_metrics.credited_pauc``). Using the calibration pool's labels to
    tune a competitor gives it its best setting, which can only make v5's comparison harder;
    its thresholds stay fitted on unlabelled agent-days (R2-3), and the test pool is never
    used. ``ValueError`` unless every grid point, and nothing else, has a finite objective.
    """
    if set(objective) != set(IFOREST_GRID):
        raise ValueError(f"give an objective for exactly the grid points {IFOREST_GRID}")
    values = {point: float(v) for point, v in objective.items()}
    if not all(math.isfinite(v) for v in values.values()):
        raise ValueError("every grid point needs a finite objective")
    return min(IFOREST_GRID, key=lambda point: (-values[point], point))


# ── simplified ports of the probe calibrations ───────────────────────────────────────────────
def personal_day_calibration(
    days: hm.AgentDays, day_score: ArrayLike, *, past_days: int = PERSONAL_PAST_DAYS
) -> np.ndarray:
    """Personal day rank: p = (1 + the caller's past agent-days in [t - past_days, t - 1]
    whose maximum was at least today's) / (A + 1); the baseline is -log p. Simplified from
    ``calib_personal_day.py``: no newcomer pool, no record ranking, no policy overrides."""
    s = np.asarray(day_score, dtype=np.float64)
    if s.shape != (days.n_days,):
        raise ValueError("day_score must give one value per agent-day")
    agent, _ = _codes(days.agent)
    out = np.empty(days.n_days)
    bounds = np.r_[np.flatnonzero(np.r_[True, agent[1:] != agent[:-1]]), days.n_days]
    for lo, hi in zip(bounds[:-1], bounds[1:], strict=True):
        d, v = days.day[lo:hi], s[lo:hi]
        past = (d[None, :] < d[:, None]) & (d[None, :] >= d[:, None] - past_days)
        a = past.sum(axis=1)
        at_least = (past & (v[None, :] >= v[:, None])).sum(axis=1)
        out[lo:hi] = -np.log((1 + at_least) / (1 + a))
    return out


def org_calibration(
    days: hm.AgentDays, evidence: cf.CallEvidence, *, pool_days: int = ORG_POOL_DAYS
) -> np.ndarray:
    """Org-normalised max: per dimension, the rank of the day's maximum s_d among the
    organisation's agent-day maxima of the last ``pool_days`` days (where d took part); q =
    min_d rank_d / w_d over alerting dimensions; the baseline is s1 = 1 / (1 + 2 q).
    Simplified from ``calib_org_normalised.py``: a rolling pool, no freeze at day 134 (the
    harness's fit and report windows keep test days out of fitting)."""
    alerting = np.flatnonzero(~np.isnan(evidence.shares))
    q = np.full(days.n_days, np.inf)
    unique_days = np.unique(days.day)
    for col in alerting:
        peak = hm.day_max(days, evidence.scores[:, col]).score
        took_part = np.isfinite(peak)
        for t in unique_days:
            today = (days.day == t) & took_part
            if not today.any():
                continue
            pool = took_part & (days.day < t) & (days.day >= t - pool_days)
            rank = cf.rank_transform(peak[today], peak[pool])
            q[today] = np.minimum(q[today], rank / evidence.shares[col])
    return cf.s1_of(q)


def baseline_names() -> Sequence[str]:
    """The baselines this module scores, in table order."""
    return (
        "static_only",
        "red_flags_only",
        "per_agent_max_z",
        "isolation_forest",
        "role_peer_group",
        "guardian_rate",
        "aegis_rarity",
        "praetor_unseen",
        "personal_day_calibration",
        "org_calibration",
    )
