"""Design-phase probe (development world only): THREE-GROUP CALIBRATION, a v5 arm, offline.

The arm keeps v4's per-dimension scores s_d and turns each of the paper's three groups (Typical
Cadence, Typical Footprint, Red Flags) into one calibrated per-agent-day p-value, then combines
the three by weighted Bonferroni: 3 looks instead of 15.

    Group statistic, one of
      plain       S_G(c) = max of s_d(c) over the dimensions of G that take part (v4's max)
      normalised  T_G(c) = min over those dimensions of u_d(c), u_d = s_d's own tail share
                  (same calibration source as the group), ties broken by S_G
    p_G(c)  = calibrated tail share of the group statistic, against one of
              self      his own active days in [d-89, d-1] (the days behind A):
                        (1 + #{his past days j: Q_G(j) at least as strange}) / (A + 1)
              org       every active agent-day of the organisation in the same days:
                        (1 + #{pool agent-days at least as strange}) / (N + 1)
              role      the same, pooled within his role only (a "Mondrian" pool)
              self>org  his personal rank, then org-calibrated: the key (-p_self, statistic)
              self>role the same within his role
              both      max(p_self, p_role): valid when either assumption holds
              Q_G(j) is the day's strangest value on day j; days without G count as least strange.
    q(c)    = min_G p_G(c) / w_G,  sum of w_G = 1 (equal thirds by default)
    s(c)    = 1 / (1 + 2 q(c));   M_stat = 5 ^ max(0, 2 s - 1)   (v5: no discount below x1)
    M(c)    = max(M_stat, M_floor), M_floor = g(first-access floor): an explicit override
    reason  = the group with the smallest p_G / w_G, then the dimension that set its statistic
    runner-up (list tie-breaker) = the second-largest s among the three groups and the floor

Guarantee (per agent-day, stated): if today's day-level p of each look is super-uniform (his day
exchangeable with his own past days for "self"; with the pooled agent-days for "org" and "role"),
then P(M_stat today >= g(1 / (1 + 2 alpha))) <= sum_G w_G alpha = alpha, under any dependence
between the groups. The override adds its own, separately reported, rate.

Every number is from a burnt DEVELOPMENT WORLD (seeds 7, 11 and 21; the existing profiles). The
headline numbers come from the shared evaluator calib_eval.py only; the "supplementary" blocks
(one look at a time, per agent) are this script's own and say so. The variant is chosen by the
rule in select_looks(), which reads days 90-134 only; nothing is fitted on days 135-179.
Calibration sets are causal (up to yesterday), like the engine's own daily learning.

    python3 reports/experiments/dynamic_dimensions/knowledge_base/probes/calib_group_calibrated.py \\
        NPZ [NPZ ...] --out-dir DIR
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calib_eval as ce  # noqa: E402

# ── constants ────────────────────────────────────────────────────────────────────────────────
DIM_KEYS = (
    "calls_last_hour",
    "writes_last_hour",
    "assets_last_hour",
    "same_call_10m",
    "session_length",
    "time_of_day",
    "tool",
    "asset",
    "network",
    "client",
    "burst",
    "many_assets",
    "request_too_big",
    "sequence",
    "protocol_skip",
)
GROUPS = ("Typical Cadence", "Typical Footprint", "Red Flags")
GROUP_SHORT = ("Cadence", "Footprint", "Red Flags")
GROUP_DIMS = (tuple(range(0, 6)), tuple(range(6, 10)), tuple(range(10, 15)))
RED = 2
ASSET_DIM, NETWORK_DIM, CLIENT_DIM = 7, 8, 9
FLOOR_REASON = 15  # d* index of the first-access floor override
LOOKBACK_DAYS = 89  # A = his active days in [d-89, d-1]; load_rows() asserts it
EQUAL_WEIGHTS = (1 / 3, 1 / 3, 1 / 3)
STATED_ALPHAS = (0.01, 0.025, 0.05)
SOURCES = ("self", "org", "role", "self>org", "self>role", "both")  # simplest first
NORMALISABLE = ("self", "org", "role")
RED_SOURCES = ("org", "role")  # Red Flags are calibrated at organisation level only
SELECT_DAYS = (90, 134)  # the variant rule reads only these days (the evaluator's fit half)
SELECT_ALPHA = 0.05  # ... at this budget
SELECT_SLACK = 1.25  # a look is admissible when its realised rate <= slack x its share
# (-p, statistic) as one float. Exact for personal p (steps >= 1/(90*90) > 1e-4 >> LEX_EPS);
# approximate across days for org-pool p, whose values on different days can differ < 1e-6.
LEX_EPS = 1e-6
CHUNK = 50_000  # rows per block in personal_p (50k x 89 booleans)
MIN_AGENT_DAYS = 20  # per-agent supplementary rates need this many ordinary days
BINOMIAL_DRAWS = 2000
MAX_MULTIPLIER = 5.0


def curve_v5(s: np.ndarray) -> np.ndarray:
    """v5's curve: 5^max(0, 2s - 1) (PS8: M never below 1); 1 when s is NaN."""
    s = np.nan_to_num(np.asarray(s, dtype=np.float64), nan=0.0)
    return MAX_MULTIPLIER ** np.maximum(0.0, 2.0 * s - 1.0)


def s_of_q(q: np.ndarray) -> np.ndarray:
    """The design's mapping from a per-agent-day rate q to a score: 1 / (1 + 2q)."""
    return 1.0 / (1.0 + 2.0 * np.asarray(q, dtype=np.float64))


def stated_line(alpha: float) -> float:
    """The M line whose stated per-agent-day false-alarm bound is alpha."""
    return float(curve_v5(s_of_q(alpha)))


def dstar_names(meta: dict) -> list[str]:
    """Reason names: the group, then the dimension (paper names), then the override."""
    names = [
        f"{GROUP_SHORT[GROUPS.index(d['group'])]}: {d['paper_name']}" for d in meta["dimensions"]
    ]
    return names + ["Override: first-access floor"]


# ── the world, as stacked rows (tool calls, then non-call messages: calib_eval's order) ─────
@dataclass(frozen=True)
class Rows:
    """Per stacked row: who, when, and the 15 scores (the floor taken out of the asset)."""

    n_calls: int
    n_agents: int
    n_days: int
    agent: np.ndarray
    day: np.ndarray
    role_of_agent: np.ndarray
    active: np.ndarray  # (agents, days): a tool call that day
    history: np.ndarray  # (agents, days): active days in [d-89, d-1] (= A)
    dims: np.ndarray  # (rows, 15) float32: s_d, the asset without the floor; NaN: no part
    asset_floored: np.ndarray  # (rows,) float32: v4's s_asset, the floor inside
    floor: np.ndarray  # (rows,): first-access floor value, NaN when it did not apply


def load_rows(npz: Path) -> Rows:
    """Read only the columns the arm needs and build the stacked rows."""
    with np.load(npz) as z:
        s = np.stack([z[f"s_{k}"] for k in DIM_KEYS], axis=1).astype(np.float32)
        floor = z["floor"].astype(np.float64)
        nofloor = z["asset_nofloor"]
        agent_c, day_c, role_c, a_c = (z[k].astype(np.int64) for k in ("agent", "day", "role", "A"))
        agent_m, day_m = z["msg_agent"].astype(np.int64), z["msg_day"].astype(np.int64)
        msg_net, msg_cli = z["msg_s_network"], z["msg_s_client"]
    n_calls, n_msgs = len(agent_c), len(agent_m)
    n_agents = int(max(agent_c.max(), agent_m.max())) + 1
    n_days = int(max(day_c.max(), day_m.max())) + 1
    role_of_agent = np.full(n_agents, -1, dtype=np.int64)
    role_of_agent[agent_c] = role_c
    active = np.zeros((n_agents, n_days), dtype=bool)
    active[agent_c, day_c] = True
    csum = np.concatenate([np.zeros((n_agents, 1), np.int64), np.cumsum(active, 1)], axis=1)
    d = np.arange(n_days)
    history = csum[:, d] - csum[:, np.maximum(d - LOOKBACK_DAYS, 0)]
    if not np.array_equal(history[agent_c, day_c], a_c):
        raise ValueError(f"{npz}: A is not 'active days in [d-89, d-1]'")
    asset_floored = s[:, ASSET_DIM].copy()
    applied = ~np.isnan(floor)
    s[applied, ASSET_DIM] = nofloor[applied]  # the floor leaves the statistic
    msg = np.full((n_msgs, len(DIM_KEYS)), np.nan, dtype=np.float32)
    msg[:, NETWORK_DIM], msg[:, CLIENT_DIM] = msg_net, msg_cli
    return Rows(
        n_calls=n_calls,
        n_agents=n_agents,
        n_days=n_days,
        agent=np.concatenate([agent_c, agent_m]),
        day=np.concatenate([day_c, day_m]),
        role_of_agent=role_of_agent,
        active=active,
        history=history,
        dims=np.concatenate([s, msg]),
        asset_floored=np.concatenate([asset_floored, np.full(n_msgs, np.nan, np.float32)]),
        floor=np.concatenate([floor, np.full(n_msgs, np.nan)]),
    )


# ── calibration of any causal per-row key (higher = stranger, -inf = took no part) ──────────
def day_max(rows: Rows, key: np.ndarray) -> np.ndarray:
    """(agents, days) table of the day maximum of a per-row key (-inf: no finite key)."""
    tab = np.full((rows.n_agents, rows.n_days), -np.inf)
    ok = np.isfinite(key)
    np.maximum.at(tab, (rows.agent[ok], rows.day[ok]), key[ok])
    return tab


def _window(q_row: np.ndarray, act_row: np.ndarray) -> np.ndarray:
    """(days, 89) matrix: row d holds his day keys on active days d-1 ... d-89 (-inf if none)."""
    d = np.arange(len(q_row))[:, None] - 1 - np.arange(LOOKBACK_DAYS)[None, :]
    dc = np.maximum(d, 0)
    return np.where((d >= 0) & act_row[dc], q_row[dc], -np.inf)


def personal_p(rows: Rows, key: np.ndarray) -> np.ndarray:
    """Per row: (1 + #{his active days j in [d-89, d-1]: day max(j) >= key}) / (A + 1)."""
    tab = day_max(rows, key)
    p_row = np.ones(len(key))
    order = np.argsort(rows.agent, kind="stable")
    bounds = np.searchsorted(rows.agent[order], np.arange(rows.n_agents + 1))
    for a in range(rows.n_agents):
        win = _window(tab[a], rows.active[a])
        idx = order[bounds[a] : bounds[a + 1]]
        idx = idx[np.isfinite(key[idx])]
        days = rows.day[idx]
        for lo in range(0, len(idx), CHUNK):
            sl = slice(lo, lo + CHUNK)
            num = (win[days[sl]] >= key[idx[sl], None]).sum(axis=1)
            p_row[idx[sl]] = (1 + num) / (rows.history[a, days[sl]] + 1)
    return p_row


def org_p(rows: Rows, key: np.ndarray, stratum: np.ndarray) -> np.ndarray:
    """Per row: (1 + #{pool agent-days whose day max >= key}) / (N + 1); the pool is every active
    agent-day of his stratum in [d-89, d-1]."""
    tab = day_max(rows, key)
    p_row = np.ones(len(key))
    row_stratum = stratum[rows.agent]
    ok = np.isfinite(key)
    for g in np.unique(stratum):
        members = stratum == g
        t_g, a_g = tab[members], rows.active[members]
        idx = np.flatnonzero(ok & (row_stratum == g))
        idx = idx[np.argsort(rows.day[idx], kind="stable")]
        cuts = np.searchsorted(rows.day[idx], np.arange(rows.n_days + 1))
        for d in range(rows.n_days):
            part = idx[cuts[d] : cuts[d + 1]]
            if len(part) == 0:
                continue
            lo = max(0, d - LOOKBACK_DAYS)
            pool = np.sort(t_g[:, lo:d][a_g[:, lo:d]])
            num = len(pool) - np.searchsorted(pool, key[part], side="left")
            p_row[part] = (1 + num) / (len(pool) + 1)
    return p_row


@dataclass(frozen=True)
class Look:
    """One group's calibrated look: its source and whether it normalises within the group."""

    source: str
    normalised: bool = False

    @property
    def label(self) -> str:
        return f"{self.source}{'+norm' if self.normalised else ''}"


class Calibrator:
    """Computes and caches each look's p and reason per stacked row, on one world."""

    def __init__(self, rows: Rows) -> None:
        self.rows = rows
        self.cache: dict[tuple, tuple[np.ndarray, np.ndarray]] = {}
        self.single = np.zeros(rows.n_agents, dtype=np.int64)

    def group_scores(self, g: int, floored: bool) -> np.ndarray:
        """(rows, k) float64 scores of group g's dimensions (NaN: took no part)."""
        cols = self.rows.dims[:, list(GROUP_DIMS[g])].astype(np.float64)
        if floored and g == 1:
            cols[:, GROUP_DIMS[1].index(ASSET_DIM)] = self.rows.asset_floored
        return cols

    def calibrate(self, key: np.ndarray, source: str) -> np.ndarray:
        """The calibrated p of a causal per-row key under one source."""
        if source == "self":
            return personal_p(self.rows, key)
        if source in ("org", "role"):
            strat = self.single if source == "org" else self.rows.role_of_agent
            return org_p(self.rows, key, strat)
        if source in ("self>org", "self>role"):
            p_self = personal_p(self.rows, key)
            key2 = np.where(np.isfinite(key), -p_self + LEX_EPS * key, -np.inf)
            return self.calibrate(key2, source.split(">")[1])
        if source == "both":
            return np.maximum(personal_p(self.rows, key), self.calibrate(key, "role"))
        raise ValueError(f"unknown source {source!r}")

    def look(self, g: int, look: Look, floored: bool = False) -> tuple[np.ndarray, np.ndarray]:
        """(p, reason) of group g under one look; reason = the dimension index, -1 if none."""
        k = (g, look, floored)
        if k in self.cache:
            return self.cache[k]
        cols = self.group_scores(g, floored)
        filled = np.where(np.isnan(cols), -np.inf, cols)
        top = filled.max(axis=1)
        dims = np.asarray(GROUP_DIMS[g])
        if not look.normalised:
            key, arg = top, np.argmax(filled, axis=1)
        else:
            if look.source not in NORMALISABLE:
                raise ValueError(f"normalised looks take {NORMALISABLE}, not {look.source!r}")
            u = np.stack([self.calibrate(filled[:, j], look.source) for j in range(len(dims))], 1)
            u = np.where(np.isfinite(filled), u, np.inf)
            arg = np.argmin(u, axis=1)
            t = u[np.arange(len(u)), arg]
            key = np.where(
                np.isfinite(t), -t + LEX_EPS * np.where(np.isfinite(top), top, 0), -np.inf
            )
        p = self.calibrate(key, look.source)
        reason = np.where(np.isfinite(top), dims[arg], -1)
        self.cache[k] = (p, reason)
        return p, reason


# ── the arm ──────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ArmSpec:
    """One three-group-calibration arm."""

    name: str
    looks: tuple[Look, Look, Look]  # (Cadence, Footprint, Red Flags)
    weights: tuple[float, float, float] = EQUAL_WEIGHTS
    floor_inside: bool = False  # v4 placement: the floor inside Footprint, no override


@dataclass(frozen=True)
class ArmOutput:
    """Per stacked row: M, the runner-up, the reason, q and each look's p."""

    m: np.ndarray
    secondary: np.ndarray
    dstar: np.ndarray
    q: np.ndarray
    p: np.ndarray  # (rows, 3), 1 where the group took no part


def run_arm(cal: Calibrator, spec: ArmSpec) -> ArmOutput:
    """Combine the three calibrated looks by weighted Bonferroni, then apply the override."""
    if abs(sum(spec.weights) - 1.0) > 1e-9:
        raise ValueError(f"weights must sum to 1: {spec.weights}")
    rows = cal.rows
    looks = [cal.look(g, spec.looks[g], spec.floor_inside) for g in range(3)]
    p = np.stack([x[0] for x in looks], axis=1)
    reasons = np.stack([x[1] for x in looks], axis=1)
    took_part = reasons >= 0
    qg = np.where(took_part, p / np.asarray(spec.weights)[None, :], np.inf)
    best = np.argmin(qg, axis=1)
    r = np.arange(len(best))
    q = qg[r, best]
    finite = np.isfinite(q)
    s_groups = np.where(took_part, s_of_q(np.where(took_part, qg, 1.0)), 0.0)
    m_stat = curve_v5(np.where(finite, s_of_q(np.where(finite, q, 1.0)), 0.0))
    dstar = np.where(finite, reasons[r, best], ce.NO_REASON)
    floor_s = np.zeros(len(q)) if spec.floor_inside else np.nan_to_num(rows.floor, nan=0.0)
    m_floor = np.where(floor_s > 0, curve_v5(floor_s), 1.0)
    m = np.maximum(m_stat, m_floor)
    dstar = np.where(m_floor > m_stat, FLOOR_REASON, dstar)
    cand = np.sort(np.concatenate([s_groups, floor_s[:, None]], axis=1), axis=1)
    return ArmOutput(m=m, secondary=cand[:, -2], dstar=dstar.astype(np.int64), q=q, p=p)


def evaluate_arm(npz: Path, rows: Rows, out: ArmOutput, name: str) -> dict:
    """The shared evaluator on one arm, with the stated lines as unfitted fixed lines."""
    n = rows.n_calls
    lines = {"x3": 3.0} | {f"stated {100 * a:g}%": stated_line(a) for a in STATED_ALPHAS}
    return ce.evaluate(
        npz,
        out.m[:n],
        out.secondary[:n],
        out.dstar[:n],
        name=name,
        msg_primary=out.m[n:],
        msg_secondary=out.secondary[n:],
        msg_dstar=out.dstar[n:],
        dstar_names=dstar_names(ce.load_world(npz).meta),
        fixed_lines=lines,
    )


# ── selection rule (days 90-134 only) and supplementary reliability ─────────────────────────
def look_stats(w: ce.World, p: np.ndarray, share: float, days: tuple[int, int]) -> dict:
    """One look at one budget share on a day range: ordinary agent-day rate, gray caught."""
    lo, hi = days
    p_day = np.minimum.reduceat(p[w.rows], w.starts)
    ordinary = (w.day >= lo) & (w.day <= hi) & (w.label == ce.ORDINARY)
    in_days = (w.call_day[w.gray_call] >= lo) & (w.call_day[w.gray_call] <= hi)
    gray, ep = w.gray_call[in_days], w.gray_ep[in_days]
    return {
        "ordinary_days": int(ordinary.sum()),
        "realised": float((p_day[ordinary] <= share).mean()),
        "share": share,
        "episodes": int(len(np.unique(ep))),
        "caught": int(len(np.unique(ep[p[gray] <= share]))),
    }


def candidate_looks(g: int) -> list[Look]:
    """Every look the rule may choose for group g, simplest first."""
    plain = [Look(s) for s in (RED_SOURCES if g == RED else SOURCES)]
    norm = [Look(s, True) for s in (RED_SOURCES if g == RED else NORMALISABLE)]
    return plain + norm


def select_looks(stats: dict) -> tuple[Look, Look, Look]:
    """Fixed before any report-window number was read. Per group, among the looks whose
    realised rate on ordinary agent-days of days 90-134 is at most SELECT_SLACK x its budget
    share (1/3 of 5%) in every world, take the one that catches the most gray episodes on days
    90-134 (summed over worlds); ties go to the simpler look (candidate_looks order)."""
    chosen = []
    for g in range(3):
        best, best_key = None, None
        for i, look in enumerate(candidate_looks(g)):
            per = [stats[world][g][look.label] for world in stats]
            if any(x["realised"] > SELECT_SLACK * x["share"] for x in per):
                continue
            key = (sum(x["caught"] for x in per), -i)
            if best_key is None or key > best_key:
                best, best_key = look, key
        chosen.append(best or candidate_looks(g)[0])
    return tuple(chosen)


def per_agent_reliability(w: ce.World, rows: Rows, m: np.ndarray, alpha: float) -> dict:
    """Supplementary: per agent, ordinary agent-days (report window) at the stated line,
    against a binomial reference at exactly alpha."""
    line = stated_line(alpha)
    day_m = np.maximum.reduceat(m[w.rows], w.starts)
    agent = rows.agent[w.rows[w.starts]]
    sel = (w.day >= ce.REPORT_FIRST_DAY) & (w.label == ce.ORDINARY)
    n = np.bincount(agent[sel], minlength=rows.n_agents)
    k = np.bincount(agent[sel], weights=(day_m[sel] >= line), minlength=rows.n_agents)
    keep = n >= MIN_AGENT_DAYS
    rate = k[keep] / n[keep]
    rng = np.random.default_rng(ce.LIST_SEED)
    sim = rng.binomial(np.tile(n[keep], (BINOMIAL_DRAWS, 1)), alpha) / n[keep][None, :]
    return {
        "alpha": alpha,
        "line": line,
        "agents": int(keep.sum()),
        "share_over_2alpha": float((rate > 2 * alpha).mean()) if keep.any() else None,
        "binomial_share_over_2alpha": float((sim > 2 * alpha).mean()),
        "max_rate": float(rate.max()) if keep.any() else None,
    }


def look_reliability(w: ce.World, out: ArmOutput, spec: ArmSpec) -> list[dict]:
    """Supplementary: each look on its own, report window, ordinary agent-days."""
    res = []
    for g in range(3):
        for a in STATED_ALPHAS:
            share = spec.weights[g] * a
            st = look_stats(w, out.p[:, g], share, (ce.REPORT_FIRST_DAY, w.last_day))
            res.append({"group": GROUPS[g], "alpha": a} | st)
    return res


# ── main ─────────────────────────────────────────────────────────────────────────────────────
def arm_specs(selected: tuple[Look, Look, Look]) -> list[ArmSpec]:
    """The arms evaluated on every world: the selected one first, then the variants."""
    sel = " / ".join(x.label for x in selected)
    org, norg = Look("org"), Look("org", True)
    specs = [
        ArmSpec(f"GC selected ({sel})", selected),
        ArmSpec("GC literal self / self / org", (Look("self"), Look("self"), org)),
        ArmSpec("GC literal org / org / org", (org, org, org)),
        ArmSpec("GC literal role / role / org", (Look("role"), Look("role"), org)),
        ArmSpec("GC literal both / both / org", (Look("both"), Look("both"), org)),
        ArmSpec("GC self>role / self>role / org", (Look("self>role"), Look("self>role"), org)),
        ArmSpec("GC normalised org / org / org", (norg, norg, norg)),
        ArmSpec(f"GC selected, w = 1/4, 1/4, 1/2 ({sel})", selected, (0.25, 0.25, 0.5)),
        ArmSpec(f"GC selected, floor inside ({sel})", selected, floor_inside=True),
    ]
    seen, uniq = set(), []
    for s in specs:
        k = (s.looks, s.weights, s.floor_inside)
        if k not in seen:
            seen.add(k)
            uniq.append(s)
    return uniq


# ── compact report: formatting only, every number read from the shared evaluator's dicts ────
REPORT_KINDS_FIRST = ("cross_copy", "overfetch", "bulk_export", "scope_creep")


def _op(res: dict, label: str) -> dict:
    return next(p for p in res["operating_points"] if p["label"] == label)


def _pc(x, digits: int = 2) -> str:
    return "-" if x is None else f"{100 * x:.{digits}f}%"


def _rec(block: dict) -> str:
    lo, hi = block["wilson95"]
    if block["episodes"] == 0:
        return "0/0"
    return f"{block['caught']}/{block['episodes']} [{100 * lo:.0f}, {100 * hi:.0f}]"


def _pooled(blocks: list[dict]) -> str:
    k, n = sum(b["caught"] for b in blocks), sum(b["episodes"] for b in blocks)
    lo, hi = ce.wilson(k, n)
    return f"{k}/{n} [{100 * lo:.0f}, {100 * hi:.0f}]" if n else "0/0"


def _tbl(header: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return out + ["| " + " | ".join(r) + " |" for r in rows]


def _group_of_reason(name: str, dim_group: dict[str, str]) -> str:
    if ": " in name:
        head = name.split(": ")[0]
        return "Override" if head == "Override" else head
    return GROUP_SHORT[GROUPS.index(dim_group[name])] if name in dim_group else name


def report(out_dir: Path) -> str:
    """Compact markdown of the selected arm (and variants) next to v4, per world."""
    summary = json.loads((out_dir / "group_calib_summary.json").read_text())
    worlds = {
        w: json.loads((out_dir / f"group_calib_{w}.json").read_text()) for w in summary["worlds"]
    }
    lines = [
        "All numbers: DEVELOPMENT WORLD (burnt seeds 7, 11, 21), report window days 135-180 "
        "unless marked. Source: calib_eval.evaluate (shared evaluator).",
        f"Selected looks (rule on days 90-134): {' / '.join(summary['selection']['selected'])}.",
        "",
    ]
    hd = ["World", "Arm", "Point", "Threshold", "Fit", "Ordinary", "Change", "All benign"]
    hd += ["Gray recall [Wilson]", "Credited prec.", "Alerts/1000"]
    rows = []
    v4_pts = (
        "alpha 1%, ties by secondary",
        "alpha 2.5%, ties by secondary",
        "alpha 5%",
        "x3 fixed",
    )
    arm_pts = ("alpha 1%", "alpha 2.5%", "alpha 5%", "x3 fixed")
    arm_pts += tuple(f"stated {a}% fixed" for a in ("1", "2.5", "5"))
    for w, d in worlds.items():
        v4, sel = d["results"][0], d["results"][1]
        for res, pts in ((v4, v4_pts), (sel, arm_pts)):
            for lab in pts:
                p = _op(res, lab)
                m = p["metrics"]
                t = p["threshold"]
                rows.append(
                    [
                        w,
                        "v4" if res is v4 else "GC selected",
                        lab,
                        "infeasible" if t is None else f"{t:.3f}",
                        _pc(p["fit"]["fit_rate"]),
                        _pc(m["by_day_label"]["ordinary"]["rate"]),
                        _pc(m["by_day_label"]["change"]["rate"]),
                        _pc(m["by_day_label"]["benign"]["rate"]),
                        _rec(m["gray"]["overall"]),
                        _pc(m["precision"]["credited"], 1),
                        f"{m['alerts_per_1000_agent_days']['all']:.1f}",
                    ]
                )
    lines += ["### Operating points", ""] + _tbl(hd, rows) + [""]
    # review list
    rows = []
    for w, d in worlds.items():
        for res in d["results"]:
            cells = [w, res["name"]]
            for lst in res["review_list"]:
                c = lst["credited"]["all"]
                cells.append(
                    f"{_pc(c['recall'], 1)} (rand {_pc(c['random'], 1)}, x{c['lift']:.2f})"
                )
            rows.append(cells)
    lines += ["### Review list, credited recall (days 90-180)", ""]
    lines += _tbl(["World", "Arm", "k = 4", "k = 8"], rows) + [""]
    # per kind
    kinds = list(worlds[next(iter(worlds))]["results"][0]["review_list"][0]["credited"].keys())
    kinds = [k for k in kinds if k != "all"]
    kinds = [k for k in REPORT_KINDS_FIRST if k in kinds] + [
        k for k in kinds if k not in REPORT_KINDS_FIRST
    ]
    rows = []
    for kind in kinds:
        cells = [kind]
        for which, lab in ((0, "alpha 5%"), (1, "alpha 5%"), (0, "x3 fixed"), (1, "x3 fixed")):
            blocks = [
                _op(d["results"][which], lab)["metrics"]["gray"]["by_kind"][kind]
                for d in worlds.values()
            ]
            cells.append(" + ".join(f"{b['caught']}/{b['episodes']}" for b in blocks))
            cells[-1] += f" = {_pooled(blocks)}"
        for which in (0, 1):
            num = den = 0.0
            for d in worlds.values():
                c = d["results"][which]["review_list"][1]["credited"].get(kind)
                if c:
                    num, den = num + c["recall"] * c["episodes"], den + c["episodes"]
            cells.append(_pc(num / den if den else None, 0))
        rows.append(cells)
    hd = ["Kind", "v4 alpha 5%", "GC alpha 5%", "v4 x3", "GC x3", "v4 list@8", "GC list@8"]
    lines += ["### Gray recall by kind (worlds 7 + 11 + 21 = pooled [Wilson])", ""]
    lines += _tbl(hd, rows) + [""]
    # reasons for benign alerts
    meta_dims = ce.load_world(worlds[next(iter(worlds))]["results"][0]["npz"]).meta["dimensions"]
    dim_group = {x["paper_name"]: x["group"] for x in meta_dims}
    rows = []
    for w, d in worlds.items():
        for which in (0, 1):
            res = d["results"][which]
            for lab in ("alpha 5%", "x3 fixed"):
                r = _op(res, lab)["metrics"]["benign_alert_reasons"]["benign"]
                groups: dict[str, float] = {}
                for name, sh in r["share"].items():
                    gname = _group_of_reason(name, dim_group)
                    groups[gname] = groups.get(gname, 0.0) + sh
                top = sorted(r["share"].items(), key=lambda x: -x[1])[:4]
                rows.append(
                    [
                        w,
                        "v4" if which == 0 else "GC",
                        lab,
                        str(r["alerts"]),
                        ", ".join(f"{g} {100 * s:.0f}%" for g, s in sorted(groups.items())),
                        ", ".join(f"{n} {100 * s:.0f}%" for n, s in top),
                    ]
                )
    lines += ["### Benign alerts by reason d* (report window)", ""]
    lines += _tbl(["World", "Arm", "Point", "Alerts", "By group", "Top d*"], rows) + [""]
    # strata
    rows = []
    for w, d in worlds.items():
        for which in (0, 1):
            st = _op(d["results"][which], "alpha 5%")["metrics"]["strata"]
            cells = [w, "v4" if which == 0 else "GC"]
            for grp, name in (("is_bot", "people"), ("is_bot", "bots")) + tuple(
                ("history", b) for b in ce.HISTORY_BANDS[:3]
            ):
                s = st[grp][name]
                cells.append(
                    f"{_pc(s['ordinary']['rate'])} ({s['ordinary']['days']}); {_rec(s['gray'])}"
                )
            rows.append(cells)
    hd = ["World", "Arm", "People", "Bots"] + list(ce.HISTORY_BANDS[:3])
    lines += ["### Strata at alpha 5%: ordinary rate (days); gray caught", ""]
    lines += _tbl(hd, rows) + [""]
    # reliability
    rows = []
    for w, d in worlds.items():
        sel = d["results"][1]
        for a in ("1", "2.5", "5"):
            rep = _op(sel, f"stated {a}% fixed")["metrics"]["by_day_label"]
            allw = _op(sel, f"stated {a}% fixed, days 90-{sel['counts']['last_day']}")
            allw = allw["metrics"]["by_day_label"]
            rows.append(
                [
                    w,
                    f"{a}%",
                    f"{_op(sel, f'stated {a}% fixed')['threshold']:.3f}",
                    _pc(rep["ordinary"]["rate"]),
                    _pc(allw["ordinary"]["rate"]),
                    _pc(rep["change"]["rate"]),
                    _pc(rep["benign"]["rate"]),
                ]
            )
    hd = ["World", "Stated alpha", "Line M", "Ordinary 135-180", "Ordinary 90-180"]
    hd += ["Change 135-180", "All benign 135-180"]
    lines += ["### Stated versus realised (GC selected, unfitted stated lines)", ""]
    lines += _tbl(hd, rows) + [""]
    rows = []
    for w, d in worlds.items():
        sup = d["supplementary"][d["results"][1]["name"]]
        for x in sup["looks"]:
            rows.append(
                [w, x["group"], f"{100 * x['alpha']:g}%", _pc(x["share"], 3), _pc(x["realised"], 3)]
            )
        for x in sup["per_agent"]:
            rows.append(
                [
                    w,
                    "per agent (n >= 20 ordinary days)",
                    f"{100 * x['alpha']:g}%",
                    f"> 2 alpha: binomial {_pc(x['binomial_share_over_2alpha'], 1)}",
                    f"observed {_pc(x['share_over_2alpha'], 1)} of {x['agents']}, max "
                    f"{_pc(x['max_rate'], 1)}",
                ]
            )
    lines += ["### Supplementary (this script's code): each look alone, and per agent", ""]
    lines += _tbl(["World", "Look", "alpha", "Budget share", "Realised ordinary"], rows) + [""]
    # variants
    rows = []
    for w, d in worlds.items():
        for res in d["results"]:
            a5, a1 = _op(res, "alpha 5%")["metrics"], _op(res, "alpha 1%")["metrics"]
            stated = [p for p in res["operating_points"] if p["label"] == "stated 5% fixed"]
            lst = [x["credited"]["all"]["recall"] for x in res["review_list"]]
            rows.append(
                [
                    w,
                    res["name"],
                    _pc(a5["by_day_label"]["ordinary"]["rate"]),
                    _pc(a5["by_day_label"]["benign"]["rate"]),
                    _rec(a5["gray"]["overall"]),
                    _rec(a1["gray"]["overall"]),
                    " / ".join(_pc(x, 1) for x in lst),
                    _pc(stated[0]["metrics"]["by_day_label"]["ordinary"]["rate"])
                    if stated
                    else "-",
                ]
            )
    hd = ["World", "Arm", "a5 ordinary", "a5 benign", "a5 gray", "a1 gray", "list@4/@8"]
    hd += ["stated 5%: ordinary"]
    lines += ["### Variants (alpha = fitted on days 90-134 ordinary, primary only)", ""]
    lines += _tbl(hd, rows)
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("npz", type=Path, nargs="*")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--report-only", action="store_true", help="render the saved results")
    args = ap.parse_args()
    if args.report_only:
        print(report(args.out_dir))
        return
    args.out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    stats: dict = {}
    for npz in args.npz:  # pass 1: the selection statistics, days 90-134 only
        cal, w = Calibrator(load_rows(npz)), ce.load_world(npz)
        stats[npz.stem] = {}
        for g in range(3):
            share = EQUAL_WEIGHTS[g] * SELECT_ALPHA
            stats[npz.stem][g] = {
                lk.label: look_stats(w, cal.look(g, lk)[0], share, SELECT_DAYS)
                for lk in candidate_looks(g)
            }
        del cal
        print(f"selection stats {npz.stem} ({time.time() - t0:.0f} s)", flush=True)
    selected = select_looks(stats)
    print("selected:", [x.label for x in selected], flush=True)
    summary = {
        "selection": {
            "rule": select_looks.__doc__,
            "selected": [x.label for x in selected],
            "stats": stats,
        },
        "stated_lines": {f"{a:g}": stated_line(a) for a in STATED_ALPHAS},
        "worlds": {},
    }
    for npz in args.npz:  # pass 2: every arm through the shared evaluator
        world, rows, w = npz.stem, load_rows(npz), ce.load_world(npz)
        cal = Calibrator(rows)
        results = [ce.v4_reference(npz, check=True)]
        supp = {}
        for spec in arm_specs(selected):
            out = run_arm(cal, spec)
            results.append(evaluate_arm(npz, rows, out, spec.name))
            supp[spec.name] = {
                "looks": look_reliability(w, out, spec),
                "per_agent": [per_agent_reliability(w, rows, out.m, a) for a in STATED_ALPHAS],
                "override_rows": int((out.dstar == FLOOR_REASON).sum()),
            }
            print(f"  {world} {spec.name} ({time.time() - t0:.0f} s)", flush=True)
        payload = {"results": results, "supplementary": supp}
        (args.out_dir / f"group_calib_{world}.json").write_text(
            json.dumps(ce._jsonable(payload), indent=1)
        )
        (args.out_dir / f"group_calib_{world}.md").write_text(ce.to_markdown(results))
        summary["worlds"][world] = {"v4_check_mismatches": results[0]["check"].get("mismatches")}
        cal.cache.clear()
    (args.out_dir / "group_calib_summary.json").write_text(
        json.dumps(ce._jsonable(summary), indent=1)
    )
    print(f"done ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
