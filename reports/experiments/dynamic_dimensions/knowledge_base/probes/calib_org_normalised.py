"""v5 arm "org calibration": an org-normalised max over the logged per-dimension scores.

Each dimension keeps its personal score s_d (excess, rarity, red flag, first-access floor), so
personal baselines stay inside s_d. What changes is the scale on which the max is taken
(Kriegel et al. 2011's "unify, then combine"): every s_d is replaced by its **org rate**, the
share of the organisation's recent agent-days whose strongest score in that dimension reached
at least s_d (add-one, so it is a conformal p-value at agent-day level). Each dimension may
spend its **budget share** w_d of the false-alarm budget (weighted Bonferroni):

    r_d(c) = (1 + #{pool agent-days j : S_d,j >= s_d(c)}) / (N + 1)     org rate
    q(c)   = min_d r_d(c) / w_d                                        d* = argmin, q2 = runner-up
    s1     = 1 / (1 + 2 q),  s2 = 1 / (1 + 2 q2)                        the rarity curve
    M      = g(s1)  (the v4 curve: 5^(2 s1 - 1) above 0.5, 0.7^(1 - 2 s1) below)
    alert line for an alert budget alpha:  M_alpha = g(1 / (1 + 2 alpha))

Org-level guarantee: if today's agent-days are exchangeable with the pool's, the expected share
of agent-days at or above M_alpha is at most alpha (union bound over the dimensions plus the
conformal add-one rule). It is marginal over agents, not per agent.

The arm is computed OFFLINE from the vectors that dump_vectors.py saved. M feeds nothing back
into engine state, so the logged s_d, floor and raw flag columns are enough. Pools never use days
135-179 (the evaluator's test half): rolling pools are frozen at day 134. Every number is a
DEVELOPMENT-WORLD number. Headline metrics come only from calib_eval.evaluate; the
diagnostics below (per-dimension reliability, per-agent spread, resolution, tail ownership) are
this script's own and are labelled as diagnostics.

Run (one process, numpy only; about 100 s and 1.9 GB for the three full worlds):

    python3 reports/experiments/dynamic_dimensions/knowledge_base/probes/calib_org_normalised.py \
        <world.npz> [<world.npz> ...] --json out.json --md out.md
    (re-render only: --json out.json --md out.md --from-json)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calib_eval as ce  # noqa: E402  (the shared evaluator lives next to this file)

# ── frozen design constants ──────────────────────────────────────────────────────────────────
TEST_FIRST_DAY = ce.REPORT_FIRST_DAY  # 135: no pool may contain a day at or after this one
FREEZE_DAY = TEST_FIRST_DAY - 1  # rolling pools stop growing at day 134
ROLLING_DAYS = 60  # pool = the last 60 days before the scored day
FIXED_POOL = (30, 89)  # the task's "history days" pool
STATED_ALPHAS = (0.01, 0.025, 0.05)  # alert budgets with a stated line M_alpha
S_STAR_X3 = (1 + np.log(3) / np.log(5)) / 2  # s with g(s) = 3
ALPHA_X3 = (1 / S_STAR_X3 - 1) / 2  # the alert budget the v4 x3 line states (about 9.43%)
TOP, BOTTOM = 5.0, 0.7  # the v4 curve's ends
RULE_VALUE = 0.9  # red-flag value before the habit discount (DIMENSION_FORMULAS.md, Red flags)
DIM_NAMES = [
    "Call rate", "Write rate", "Breadth", "Repetition", "Session duration", "Hour of day",
    "Tool", "Asset", "Network", "Client",
    "Burst", "Sweep", "Oversized request", "Unsafe sequence", "Missing handshake",
    "First access",
]  # fmt: skip
CADENCE_KEYS = [
    "calls_last_hour", "writes_last_hour", "assets_last_hour", "same_call_10m",
    "session_length", "time_of_day",
]  # fmt: skip
POLICY_ITEMS = (10, 11, 12, 13, 14, 15)  # red flags and the first access
FIRST_ACCESS = 15
MSG_DIMS = {8: "msg_s_network", 9: "msg_s_client"}  # the only scores non-call messages carry
ORG_CAPPED = {8: 0, 9: 1, 6: 2, 7: 3}  # dimension -> org_mask bit (sidecar ORG_KINDS)
ORDINARY_SCORE = 0.5  # the org discount's cap: "counts at most as ordinary" (x1)


@dataclass(frozen=True)
class ArmSpec:
    """One variant of org calibration; the default is the headline arm."""

    name: str
    pool: str = "rolling"  # "rolling" (last 60 days, frozen at 134) or "fixed" (days 30-89)
    graded_flags: bool = True  # burst, sweep, oversized scored by how far over the limit
    flags_half: bool = False  # red flags + first access share half the budget
    by_class: bool = False  # separate pools for people and machine identities
    floor_override: bool = False  # first access outside the statistic: M = max(M_stat, g(floor))
    benign_oracle: bool = False  # pool = benign-labelled agent-days only (needs labels)
    leave_top_out: bool = False  # per dimension, drop the identity owning most of the x3 tail
    note: str = ""


ARMS = [
    ArmSpec("org calibration", note="headline: label-free pool, last 60 days, frozen at 134"),
    ArmSpec("org, pool days 30-89", pool="fixed", note="the task's fixed history pool"),
    ArmSpec("org, flags half budget", flags_half=True, note="6 policy items share 50%"),
    ArmSpec("org, pool per class", by_class=True, note="people and machines pooled apart"),
    ArmSpec("org + first-access policy floor", floor_override=True, note="RF8 placement"),
    ArmSpec("org, benign-labelled pool", benign_oracle=True, note="oracle: labels in the pool"),
    ArmSpec("org, top identity left out", leave_top_out=True, note="RF2-style poisoning guard"),
    ArmSpec("org, flags as logged", graded_flags=False, note="flags enter by 0.9/0.7 + habit"),
]


def multiplier(s: np.ndarray) -> np.ndarray:
    """The v4 curve g: 5^(2s-1) for s >= 0.5, 0.7^(1-2s) below (DIMENSION_FORMULAS.md, Step 2)."""
    return np.where(s >= 0.5, TOP ** (2 * s - 1), BOTTOM ** (1 - 2 * s))


def stated_line(alpha: float) -> float:
    """M_alpha = g(1 / (1 + 2 alpha)): the line whose org-level false-alarm bound is alpha."""
    return float(multiplier(np.array(1 / (1 + 2 * alpha))))


# ── the world: calls, messages and agent-days ────────────────────────────────────────────────
@dataclass
class World:
    path: Path
    meta: dict
    call_day: np.ndarray
    call_ad: np.ndarray  # agent-day index of every tool call
    msg_day: np.ndarray
    msg_ad: np.ndarray
    ad_day: np.ndarray
    ad_agent: np.ndarray
    ad_bot: np.ndarray
    ad_label: np.ndarray  # 0 ordinary, 1 change, 2 gray (simulator's day label)
    ad_band: np.ndarray  # history band of the day (ce.HISTORY_BANDS)
    x_call: list[np.ndarray]  # per dimension: the input to its org rate (-inf: no part)
    x_msg: dict[int, np.ndarray]
    floor: np.ndarray  # first-access floor value per call (NaN when none)
    capped: dict[int, np.ndarray]  # per org-discounted dimension: calls the discount capped
    msg_capped: dict[int, np.ndarray]  # messages on an agent-day whose calls were capped
    day_max: list[np.ndarray] = field(default_factory=list)  # per dimension, per agent-day


def _f64(z, key: str) -> np.ndarray:
    a = z[key].astype(np.float64)
    a[np.isnan(a)] = -np.inf
    return a


def _flag_inputs(z, meta: dict, graded: bool) -> list[np.ndarray]:
    """Burst, sweep, oversized, sequence, handshake. Graded: how far over the limit, times the
    habit factor (logged s_f / 0.9), so org calibration can price the size of an overrun."""
    keys = ["burst", "many_assets", "request_too_big", "sequence", "protocol_skip"]
    logged = [_f64(z, f"s_{k}") for k in keys]
    if not graded:
        return logged
    pol = meta["policy_learned_for_v4"]

    def over(count: np.ndarray, limit, s_f: np.ndarray) -> np.ndarray:
        raised = np.isfinite(s_f)
        habit = np.where(raised, s_f, 0.0) / RULE_VALUE  # the habit discount's factor
        return np.where(raised, count / limit * habit, -np.inf)

    burst = over(z["minute_calls"], pol["burst_per_minute"], logged[0])
    sweep = over(z["hour_assets"], pol["many_assets_per_hour"], logged[1])
    size = over(z["size"], z["size_limit"], logged[2])  # no habit discount: s_f is 0.9
    return [burst, sweep, size, logged[3], logged[4]]


def load(path: Path, graded: bool) -> World:
    """Load the columns this arm needs and index agent-days as calib_eval does (agent, UTC day)."""
    meta = json.loads(path.with_suffix(".json").read_text())
    with np.load(path) as z:
        c_agent, c_day = z["agent"].astype(np.int64), z["day"].astype(np.int64)
        m_agent, m_day = z["msg_agent"].astype(np.int64), z["msg_day"].astype(np.int64)
        kinds = np.concatenate([z["label_kind"], z["msg_label_kind"]]).astype(np.int8)
        a_col = np.concatenate([z["A"].astype(np.int64), np.full(len(m_agent), -1)])
        x = [_f64(z, f"s_{k}") for k in CADENCE_KEYS]
        x += [_f64(z, "s_tool"), _f64(z, "asset_nofloor"), _f64(z, "s_network")]
        x += [_f64(z, "s_client")] + _flag_inputs(z, meta, graded) + [_f64(z, "floor")]
        x_msg = {d: _f64(z, col) for d, col in MSG_DIMS.items()}
        floor = z["floor"].astype(np.float64)
        org_mask = z["org_mask"].astype(np.int64)
    capped = {d: ((org_mask >> bit) & 1).astype(bool) for d, bit in ORG_CAPPED.items()}
    for d, m in capped.items():
        x[d][m] = -np.inf  # an org-discounted score is ordinary by rule: it stays out of the pool
    keys = np.concatenate([c_agent * 1000 + c_day, m_agent * 1000 + m_day])
    uk, inv = np.unique(keys, return_inverse=True)
    n_ad, n_c = len(uk), len(c_agent)
    label = np.zeros(n_ad, np.int8)
    np.maximum.at(label, inv, kinds)
    day_a = np.full(n_ad, -1, np.int64)
    np.maximum.at(day_a, inv, a_col)
    band = np.digitize(day_a, ce.HISTORY_EDGES).astype(np.int8)
    band[day_a < 0] = len(ce.HISTORY_BANDS) - 1
    bot = np.array(["bot" in a["role"] for a in meta["agents"]])  # normal_org_sim.py:506
    w = World(
        path=path,
        meta=meta,
        call_day=c_day,
        call_ad=inv[:n_c],
        msg_day=m_day,
        msg_ad=inv[n_c:],
        ad_day=uk % 1000,
        ad_agent=uk // 1000,
        ad_bot=bot[uk // 1000],
        ad_label=label,
        ad_band=band,
        x_call=x,
        x_msg=x_msg,
        floor=floor,
        capped=capped,
        msg_capped={},
    )
    for d in x_msg:  # messages carry no org_mask: inherit it from the agent-day's calls
        day_capped = np.zeros(n_ad, bool)
        day_capped[w.call_ad[capped[d]]] = True
        w.msg_capped[d] = day_capped[w.msg_ad]
        x_msg[d][w.msg_capped[d]] = -np.inf
    for d, xd in enumerate(x):
        s = np.full(n_ad, -np.inf)
        np.maximum.at(s, w.call_ad, xd)
        if d in x_msg:
            np.maximum.at(s, w.msg_ad, x_msg[d])
        w.day_max.append(s)
    return w


# ── org rates ────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Curve:
    """Org exceedance curve of one dimension: sorted finite pool maxima and the pool size."""

    vals: np.ndarray
    n_pool: int

    def rate(self, x: np.ndarray) -> np.ndarray:
        """(1 + #{pool days >= x}) / (N + 1); +inf where the dimension took no part."""
        ge = len(self.vals) - np.searchsorted(self.vals, x, side="left")
        return np.where(np.isfinite(x), (1.0 + ge) / (self.n_pool + 1.0), np.inf)


def _curve(w: World, d: int, pool: np.ndarray, spec: ArmSpec, share: float) -> Curve:
    s = w.day_max[d][pool]
    if spec.leave_top_out:
        fin = np.isfinite(s)
        m = max(1, int(np.ceil(share * ALPHA_X3 * len(s))))  # the x3 tail of this dimension
        if fin.sum() >= m:
            agents = w.ad_agent[pool]
            tail = np.argsort(-np.where(fin, s, -np.inf), kind="stable")[:m]
            top = np.bincount(agents[tail]).argmax()
            s = s[agents != top]
    return Curve(np.sort(s[np.isfinite(s)]), len(s))


def _pool_days(spec: ArmSpec, day: int) -> tuple[int, int]:
    if spec.pool == "fixed":
        return FIXED_POOL
    last = min(day - 1, FREEZE_DAY)
    return last - ROLLING_DAYS + 1, last


def shares(spec: ArmSpec, dims: list[int]) -> np.ndarray:
    """Budget shares w_d over the calibrated dimensions; they sum to 1."""
    w = np.zeros(len(DIM_NAMES))
    if spec.flags_half:
        flags = [d for d in dims if d in POLICY_ITEMS]
        rest = [d for d in dims if d not in POLICY_ITEMS]
        w[flags], w[rest] = 0.5 / len(flags), 0.5 / len(rest)
    else:
        w[dims] = 1.0 / len(dims)
    return w


@dataclass
class ArmScores:
    call_M: np.ndarray
    call_s2: np.ndarray
    call_dstar: np.ndarray
    msg_M: np.ndarray
    msg_s2: np.ndarray
    msg_dstar: np.ndarray
    day_q: np.ndarray  # per agent-day: min q (the union statistic)
    day_qd: list[np.ndarray]  # per dimension, per agent-day: min r_d (NaN-free, +inf = no part)
    w: np.ndarray
    pools: dict  # diagnostics: pool sizes per group


def score_arm(w: World, spec: ArmSpec) -> ArmScores:
    """Per-call M, runner-up and reason for one arm; days before 90 stay unscored (NaN)."""
    dims = [d for d in range(len(DIM_NAMES)) if not (spec.floor_override and d == FIRST_ACCESS)]
    wd = shares(spec, dims)
    n_c, n_m, n_ad = len(w.call_day), len(w.msg_day), len(w.ad_day)
    rows = {"call": (w.call_day, w.call_ad), "msg": (w.msg_day, w.msg_ad)}
    best = {k: [np.full(len(v[0]), np.inf) for _ in range(2)] for k, v in rows.items()}
    arg = {k: np.full(len(v[0]), -1, np.int64) for k, v in rows.items()}
    day_qd = []
    pool_ok = np.ones(n_ad, bool) if not spec.benign_oracle else w.ad_label < ce.GRAY
    classes = [w.ad_bot, ~w.ad_bot] if spec.by_class else [np.ones(n_ad, bool)]
    windows = sorted({_pool_days(spec, t) for t in range(ce.EVAL_FROM_DAY, w.ad_day.max() + 1)})
    lut = np.full(w.ad_day.max() + 1, -1)
    for t in range(ce.EVAL_FROM_DAY, len(lut)):
        lut[t] = windows.index(_pool_days(spec, t))
    slices = {}  # per kind: rows sorted by pool window, and each window's slice
    for kind, (day, _) in rows.items():
        gid = lut[day]
        order = np.argsort(gid, kind="stable")
        edges = np.searchsorted(gid[order], np.arange(len(windows) + 1), side="left")
        slices[kind] = (order, edges)
    pools: dict = {}
    for d in dims:
        q = {"call": np.full(n_c, np.inf), "msg": np.full(n_m, np.inf)}
        for g, (lo, hi) in enumerate(windows):
            in_window = (w.ad_day >= lo) & (w.ad_day <= hi) & pool_ok
            for ci, cls in enumerate(classes):
                curve = _curve(w, d, in_window & cls, spec, wd[d])
                pools[(lo, hi, ci)] = curve.n_pool
                for kind, (_, ad) in rows.items():
                    if kind == "msg" and d not in w.x_msg:
                        continue
                    x = w.x_call[d] if kind == "call" else w.x_msg[d]
                    order, edges = slices[kind]
                    sel = order[edges[g] : edges[g + 1]]
                    sel = sel[cls[ad[sel]]]
                    q[kind][sel] = curve.rate(x[sel])
        if d in w.capped:  # the org discount survives calibration: org score exactly 0.5
            q["call"][w.capped[d]] = ORDINARY_SCORE * wd[d]
            if d in w.msg_capped:
                q["msg"][w.msg_capped[d]] = ORDINARY_SCORE * wd[d]
        dq = np.full(n_ad, np.inf)
        for kind, (_, ad) in rows.items():
            np.minimum.at(dq, ad, q[kind])
            z = q[kind] / wd[d]
            b1, b2 = best[kind]
            new1 = z < b1
            b2[:] = np.where(new1, b1, np.minimum(b2, z))
            arg[kind] = np.where(new1, d, arg[kind])
            b1[:] = np.where(new1, z, b1)
        day_qd.append(dq)
    out = {}
    for kind, (day, _) in rows.items():
        b1, b2 = best[kind]
        none = ~np.isfinite(b1)
        s1 = 1 / (1 + 2 * b1)
        m = np.where(none, 1.0, multiplier(s1))
        s2 = np.where(np.isfinite(b2), 1 / (1 + 2 * b2), 0.0)
        dstar = np.where(none, ce.NO_REASON, arg[kind])
        if spec.floor_override and kind == "call":
            fl = np.where(np.isnan(w.floor), -np.inf, w.floor)
            m_floor = np.where(np.isfinite(fl), multiplier(np.maximum(fl, 0.0)), -np.inf)
            wins = m_floor > m
            s2 = np.where(wins, np.where(none, 0.0, s1), s2)
            m, dstar = np.where(wins, m_floor, m), np.where(wins, FIRST_ACCESS, dstar)
        unscored = day < ce.EVAL_FROM_DAY
        out[kind] = (np.where(unscored, np.nan, m), s2, dstar.astype(np.int64))
    day_q = np.full(n_ad, np.inf)
    np.minimum.at(day_q, w.call_ad, best["call"][0])
    np.minimum.at(day_q, w.msg_ad, best["msg"][0])
    return ArmScores(*out["call"], *out["msg"], day_q, day_qd, wd, pools)


# ── diagnostics (this script's own; not headline numbers) ────────────────────────────────────
def diagnostics(w: World, spec: ArmSpec, sc: ArmScores) -> dict:
    """Stated-versus-realised reliability per dimension and in union, per-agent spread,
    resolution and tail ownership, on the test half (days 135-180) and the fit half (90-134)."""
    halves = {
        "test 135-180": w.ad_day >= TEST_FIRST_DAY,
        "fit 90-134": (w.ad_day >= ce.EVAL_FROM_DAY) & (w.ad_day <= FREEZE_DAY),
    }
    budgets = {f"{100 * a:g}%": a for a in STATED_ALPHAS} | {
        f"x3 ({100 * ALPHA_X3:.2f}%)": ALPHA_X3
    }
    out: dict = {"union": {}, "per_dimension": {}, "per_agent": {}}
    for hname, h in halves.items():
        labels = {
            "all": h,
            "benign": h & (w.ad_label != ce.GRAY),
            "ordinary": h & (w.ad_label == ce.ORDINARY),
            "change": h & (w.ad_label == ce.CHANGE),
            "gray": h & (w.ad_label == ce.GRAY),
        }
        for cname, cm in labels.items():
            out["union"][f"{hname}, {cname}"] = {
                b: float((sc.day_q[cm] <= a).mean()) for b, a in budgets.items()
            } | {"days": int(cm.sum())}
        rows = {}
        for d in range(len(DIM_NAMES)):
            if sc.w[d] == 0:
                continue
            rows[DIM_NAMES[d]] = {
                b: {"stated": sc.w[d] * a}
                | {
                    f"realised {c}": float((sc.day_qd[d][labels[c]] <= sc.w[d] * a).mean())
                    for c in ("all", "ordinary", "change")
                }
                for b, a in budgets.items()
            }
        out["per_dimension"][hname] = rows
    test = halves["test 135-180"]
    line = 0.025
    for cname, cm in (("people", ~w.ad_bot), ("machines", w.ad_bot)):
        sel = test & cm
        n = np.bincount(w.ad_agent[sel], minlength=len(w.meta["agents"]))
        k = np.bincount(w.ad_agent[sel & (sc.day_q <= line)], minlength=len(n))
        has = n >= 10
        r = k[has] / n[has]
        out["per_agent"][cname] = {
            "agents": int(has.sum()),
            "alert budget": line,
            "share of agents above 2x budget": float((r > 2 * line).mean()) if has.any() else None,
            "share of agents with 0 alerts": float((r == 0).mean()) if has.any() else None,
            "max agent rate": float(r.max()) if has.any() else None,
            "top 5% of agents hold share of alerts": _top_share(k[has]),
        }
    sizes = sorted(set(sc.pools.values()))
    out["resolution"] = {
        "pool agent-days (min, max)": [sizes[0], sizes[-1]],
        "largest M at the smallest pool": float(
            multiplier(np.array(1 / (1 + 2 / ((sizes[0] + 1) * sc.w[sc.w > 0].max()))))
        ),
        "smallest q at the smallest pool, equal shares": 1
        / ((sizes[0] + 1) * sc.w[sc.w > 0].max()),
    }
    return out


def _top_share(k: np.ndarray) -> float | None:
    if k.sum() == 0:
        return None
    top = np.sort(k)[::-1][: max(1, int(np.ceil(0.05 * len(k))))]
    return float(top.sum() / k.sum())


def tail_ownership(w: World, alpha: float = ALPHA_X3) -> dict:
    """Pool days 75-134: per dimension, the share of its x3 tail (top w_d * alpha of agent-days,
    equal shares) held by the single identity with most days in it. A share near 1 means one
    identity sets the curve (self-granted habit at org level; poisoning surface)."""
    pool = (w.ad_day >= FREEZE_DAY - ROLLING_DAYS + 1) & (w.ad_day <= FREEZE_DAY)
    share = 1 / len(DIM_NAMES)
    out = {}
    for d, name in enumerate(DIM_NAMES):
        s = w.day_max[d][pool]
        m = max(1, int(np.ceil(share * alpha * len(s))))
        tail = np.argsort(-s, kind="stable")[:m]
        tail = tail[np.isfinite(s[tail])]
        if len(tail) == 0:
            out[name] = None
            continue
        counts = np.bincount(w.ad_agent[pool][tail])
        out[name] = {"tail_days": len(tail), "top_identity_share": float(counts.max() / len(tail))}
    return out


# ── the run ──────────────────────────────────────────────────────────────────────────────────
def evaluate_arm(w: World, spec: ArmSpec, sc: ArmScores) -> dict:
    """The shared evaluator, with the stated lines as fixed lines."""
    lines = {f"stated {100 * a:g}% (M {stated_line(a):.3f})": stated_line(a) for a in STATED_ALPHAS}
    lines["x3 (stated 9.43%)"] = 3.0
    names = DIM_NAMES[:FIRST_ACCESS] + ["First access (policy floor)" if spec.floor_override else
                                        "First access"]  # fmt: skip
    return ce.evaluate(
        w.path,
        sc.call_M,
        sc.call_s2,
        sc.call_dstar,
        name=spec.name,
        msg_primary=sc.msg_M,
        msg_secondary=sc.msg_s2,
        msg_dstar=sc.msg_dstar,
        dstar_names=names,
        fixed_lines=lines,
    )


def run(paths: list[Path], arm_names: list[str] | None) -> dict:
    """Every arm on every world, next to the v4 reference."""
    out: dict = {"worlds": {}}
    specs = [a for a in ARMS if not arm_names or a.name in arm_names]
    for path in paths:
        res: dict = {"v4": ce.v4_reference(path, check=True), "arms": {}, "diagnostics": {}}
        cache: dict[bool, World] = {}
        for spec in specs:
            if spec.graded_flags not in cache:
                cache = {spec.graded_flags: load(path, spec.graded_flags)}
            w = cache[spec.graded_flags]
            sc = score_arm(w, spec)
            res["arms"][spec.name] = evaluate_arm(w, spec, sc)
            res["diagnostics"][spec.name] = diagnostics(w, spec, sc) | {"note": spec.note}
            if spec.name == ARMS[0].name:
                res["tail_ownership"] = tail_ownership(w)
            print(f"{path.stem}: {spec.name} done", flush=True)
        out["worlds"][path.stem] = res
    return out


# ── markdown: formatting of the evaluator's own result dicts (no metric is computed here) ───
DEV = "DEVELOPMENT WORLD"
KINDS_SHOWN = ("cross_copy", "overfetch", "bulk_export", "scope_creep")


def _pct(x, d: int = 2) -> str:
    return "-" if x is None else f"{100 * x:.{d}f}%"


def _rec(g: dict) -> str:
    lo, hi = g["wilson95"]
    return f"{g['caught']}/{g['episodes']} [{100 * lo:.0f}, {100 * hi:.0f}]"


def _points(res: dict, labels: list[str]) -> dict:
    return {p["label"]: p for p in res["operating_points"] if p["label"] in labels}


def _v4_label(res: dict, alpha: str) -> str:
    """v4's primary-only fit is infeasible when its 3.62 tie crosses alpha: use ties by s2."""
    pts = _points(res, [f"alpha {alpha}", f"alpha {alpha}, ties by secondary"])
    plain = pts.get(f"alpha {alpha}")
    feasible = plain is not None and plain["fit"].get("feasible", plain["threshold"] is not None)
    return f"alpha {alpha}" if feasible else f"alpha {alpha}, ties by secondary"


def _row(name: str, label: str, p: dict, lists: dict) -> list[str]:
    m = p["metrics"]
    return [
        name,
        label,
        "-" if p["threshold"] is None else f"{p['threshold']:.3f}",
        _pct(p["fit"]["fit_rate"]),
        _pct(m["by_day_label"]["ordinary"]["rate"]),
        _pct(m["by_day_label"]["benign"]["rate"]),
        _pct(m["alerts_per_1000_agent_days"]["all"] / 1000),
        _rec(m["gray"]["overall"]),
        _pct(m["precision"]["credited"], 1),
        " / ".join(_pct(lists[k]["recall"], 1) for k in sorted(lists)),
    ]


HEAD = ["Arm", "Point", "t", "Fit", "Ordinary", "Benign", "All days", "Gray recall [W95]",
        "Cred. prec.", "List @4 / @8"]  # fmt: skip


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return out + ["| " + " | ".join(r) + " |" for r in rows]


def summarise(res: dict, headline: str = ARMS[0].name) -> str:
    """Compact tables per world: headline vs v4, ablations, kinds, reasons, strata, reliability."""
    lines: list[str] = []
    alphas = [f"{100 * a:g}%" for a in STATED_ALPHAS]
    for world, r in res["worlds"].items():
        v4, arms, diag = r["v4"], r["arms"], r["diagnostics"]
        lists = {
            n: {x["k"]: x["credited"]["all"] for x in a["review_list"]} for n, a in arms.items()
        }
        v4_lists = {x["k"]: x["credited"]["all"] for x in v4["review_list"]}
        lines += [f"### {world} ({DEV}; report window days 135-180)", ""]
        rows = []
        for a in alphas:
            for lab in (f"alpha {a}", f"alpha {a}, ties by secondary"):
                rows.append(_row("v4", lab, _points(v4, [lab])[lab], v4_lists))
            lab = f"alpha {a}"
            rows.append(_row(headline, lab, _points(arms[headline], [lab])[lab], lists[headline]))
        rows.append(_row("v4", "x3 fixed", _points(v4, ["x3 fixed"])["x3 fixed"], v4_lists))
        for p in arms[headline]["operating_points"]:
            if p["kind"] == "fixed" and p["metrics"]["window"][0] == ce.REPORT_FIRST_DAY:
                rows.append(_row(headline, p["label"], p, lists[headline]))
        lines += _table(HEAD, rows) + [""]
        lines += [f"Ablations at the fitted alpha 2.5% point and the stated 2.5% line ({DEV}):", ""]
        rows = []
        for n, a in arms.items():
            for p in a["operating_points"]:
                if p["label"] == "alpha 2.5%" or (
                    p["label"].startswith("stated 2.5%") and p["metrics"]["window"][0] == 135
                ):
                    rows.append(_row(n, p["label"].split(" (")[0], p, lists[n]))
        lines += _table(HEAD, rows) + [""]
        lines += [f"Gray recall by kind, Wilson 95% ({DEV}; report window):", ""]
        kinds = list(v4["operating_points"][0]["metrics"]["gray"]["by_kind"])
        rows = []
        for a in alphas:
            for name, rr, lab in (
                ("v4", v4, f"alpha {a}"),
                ("v4", v4, f"alpha {a}, ties by secondary"),
                (headline, arms[headline], f"alpha {a}"),
            ):
                g = _points(rr, [lab])[lab]["metrics"]["gray"]["by_kind"]
                rows.append([name, lab] + [_rec(g[k]) if g[k]["episodes"] else "-" for k in kinds])
        lines += _table(["Arm", "Point"] + kinds, rows) + [""]
        lines += [f"Credited list recall by kind, k = 4 / 8 ({DEV}; days 90-180):", ""]
        rows = []
        for name, rr in (("v4", v4), (headline, arms[headline])):
            cells = []
            for k in kinds:
                v = [x["credited"].get(k) for x in rr["review_list"]]
                cells.append(" / ".join(_pct(b["recall"], 0) if b else "-" for b in v))
            rows.append([name] + cells)
        lines += _table(["Arm"] + kinds, rows) + [""]
        lines += [f"Share of benign alerts by reason d*, alpha 2.5% ({DEV}; report window):", ""]
        rows = []
        for name, rr, lab in (
            ("v4", v4, _v4_label(v4, "2.5%")),
            ("v4", v4, "x3 fixed"),
            (headline, arms[headline], "alpha 2.5%"),
            (headline, arms[headline], f"stated 2.5% (M {stated_line(0.025):.3f}) fixed"),
        ):
            br = _points(rr, [lab])[lab]["metrics"]["benign_alert_reasons"]["benign"]
            top = ", ".join(f"{k} {100 * v:.0f}%" for k, v in list(br["share"].items())[:6])
            rows.append([name, lab.split(" (")[0], str(br["alerts"]), top])
        lines += _table(["Arm", "Point", "Benign alerts", "Share by d*"], rows) + [""]
        lines += [f"Strata, alpha 2.5% ({DEV}; report window; benign rate, gray caught):", ""]
        rows = []
        for name, rr, lab in (
            ("v4", v4, _v4_label(v4, "2.5%")),
            (headline, arms[headline], "alpha 2.5%"),
        ):
            st = _points(rr, [lab])[lab]["metrics"]["strata"]
            for grp in ("is_bot", "history"):
                for sname, v in st[grp].items():
                    if v["benign"]["days"] == 0:
                        continue
                    g = v["gray"]
                    gtxt = f"{g['caught']}/{g['episodes']}" if g["episodes"] else "-"
                    rows.append([name, sname, str(v["ordinary"]["days"]),
                                 _pct(v["ordinary"]["rate"]), _pct(v["benign"]["rate"]), gtxt])  # fmt: skip
        lines += _table(["Arm", "Stratum", "Ord. days", "Ordinary", "Benign", "Gray"], rows)
        lines += ["", f"Stated vs realised, union over dimensions (diagnostic; {DEV}):", ""]
        rows = []
        for n in arms:
            for half, v in diag[n]["union"].items():
                rows.append([n, half] + [_pct(v[b]) for b in list(v)[:-1]] + [str(v["days"])])
        b = list(next(iter(diag[headline]["union"].values())))[:-1]
        lines += _table(["Arm", "Half, days"] + [f"stated {x}" for x in b] + ["n"], rows) + [""]
        lines += [f"Per dimension, stated w_d x 2.5% vs realised on all agent-days ({DEV}):", ""]
        rows = []
        for n in (headline, "org, pool days 30-89"):
            for half in ("fit 90-134", "test 135-180"):
                if n not in diag:
                    continue
                pdim = diag[n]["per_dimension"][half]
                rows.append([f"{n}, {half}"] + [_pct(v["2.5%"]["realised all"], 3)
                                                 for v in pdim.values()])  # fmt: skip
        stated = [_pct(v["2.5%"]["stated"], 3) for v in diag[headline]["per_dimension"][
            "test 135-180"].values()]  # fmt: skip
        names = list(diag[headline]["per_dimension"]["test 135-180"])
        lines += _table(["Arm"] + names, [["stated"] + stated] + rows) + [""]
        lines += [f"Per-agent spread at the stated 2.5% line, test half ({DEV}):", ""]
        rows = [[n, c] + [str(round(x, 3)) if isinstance(x, float) else str(x) for x in v.values()]
                for n in arms for c, v in diag[n]["per_agent"].items()]  # fmt: skip
        hdr = list(next(iter(diag[headline]["per_agent"].values())))
        lines += _table(["Arm", "Class"] + hdr, rows)
        lines += ["", f"Resolution: {diag[headline]['resolution']}", ""]
        own = r.get("tail_ownership", {})
        lines += [
            "Top identity's share of each dimension's x3 tail, pool days 75-134: "
            + ", ".join(f"{k} {v['top_identity_share']:.2f}" for k, v in own.items() if v),
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("npz", type=Path, nargs="*", help="worlds written by dump_vectors.py")
    ap.add_argument("--arms", nargs="*", help="arm names to run (default: all)")
    ap.add_argument("--json", type=Path, required=True, help="where to save (or read) results")
    ap.add_argument("--md", type=Path, help="also write the summary tables")
    ap.add_argument("--from-json", action="store_true", help="only re-render --json as --md")
    args = ap.parse_args()
    if args.from_json:
        res = json.loads(args.json.read_text())
    else:
        if not args.npz:
            ap.error("give at least one npz, or --from-json")
        res = ce._jsonable(run(args.npz, args.arms))
        args.json.write_text(json.dumps(res, indent=1))
    if args.md:
        args.md.write_text(summarise(res))


if __name__ == "__main__":
    main()
