"""Personal day calibration: a v5 arm computed offline on the saved v4 vectors (design phase).

The arm keeps v4's per-dimension scores, s1, d* and s2. It changes only what M is read from:

- **day rank** ``p``: ``(1 + his past active days whose strangest call was at least as strange
  as this call) / (A + 1)``, over his active days in the 90-day history, up to yesterday (``A``
  is the dump's column, memory.py:79-82). The statistic leaves out the policy overrides below.
- ``M_stat = g(1 - p)`` with the engine's curve g (engine.py:184-188): x1 at p = 1/2, x0.7 at
  p = 1 (every past day was at least this strange), towards x5 as p goes to 0.
- **newcomer pool** (A < 15): his day is ranked against the newcomer days (A < 15) of his role
  in the last 180 days, not against his own few days. Fallback: people or bots, then everyone;
  a pool needs at least 19 days, otherwise M_stat = 1.
- **record day** (A >= 15): a day stranger than all his own days gets
  ``p = p_role / (A + 1)``, where ``p_role`` ranks it against the record days of his role in the
  last 90 days (same fallback). This removes the floor 1/(A + 1).
- **policy overrides**, outside the statistic: the first-access floor (sensitivity 5 and 4)
  and oversized request (its line is learned on the organisation). Missing handshake stays in
  the statistic: it already fires only for a caller whose client normally initializes.
  ``M = max(M_stat, M_rule)``. Two pricings of M_rule: ``v4``, its v4 value (x3.62, x2.63,
  x3.62); ``org``, its organisation rate ``beta`` (agent-days that raised it over active
  agent-days, last 89 days up to yesterday), never below the v4 value:
  ``M_rule = g(1 - min(beta, 1 - v4 value))``; ``ladder``, the same with beta rounded up to the
  next step of LADDER (0.25, 0.5, 1, 2.5, 5, 10, 20, 50, 100%), so the level does not drift.
- oversized line: ``v4`` (the logged per-tool limits) or ``rf1``, the red-flag area's pooled
  agent-day line (one 0.5% budget, top identity left out), learned on days 0-29 only.
- optional **record hold**: a record day stays out of his own days for 30 days (it still counts
  in A). This is the poisoning guard; it loosens the guarantee by K/(A + 1), K = held days.

M feeds nothing back into engine state, so every value is computed from logged columns. No
constant is fitted on days 135-179; the per-caller ranks are causal (up to yesterday) and use no
labels. The proposal is the ARMS row marked PROPOSAL; the other rows are ablations. Its ladder,
and keeping missing handshake in the statistic, were chosen after a first look at these
development worlds, so both must be frozen before any held-out world. Headline numbers come from the shared evaluator (calib_eval.py) only. Every number is a
DEVELOPMENT-WORLD number.

Run::

    python3 reports/experiments/dynamic_dimensions/knowledge_base/probes/calib_personal_day.py \\
        <npz> [<npz> ...] --out <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calib_eval as ce  # noqa: E402  (sibling module, path set just above)

# ── constants, fixed before any run (04 section 6.3; the evaluator's A bands) ────────────────
PAST_DAYS = 89  # the engine's 90-day history minus today: A counts days t-89 .. t-1
NEWCOMER_A = 15  # A < 15: ranked against the role's newcomer days
NEWCOMER_KEEP = 180  # newcomer days stay in the pool this long
RECORD_KEEP = 90  # record days stay in the pool this long
MIN_POOL = 19  # a pool needs this many days, so its floor 1/(N + 1) is at most 5%
HOLD_DAYS = 30  # record hold: a record day stays out of his own days this long
EVAL_FROM = ce.EVAL_FROM_DAY
STATED = (0.0025, 0.005, 0.01, 0.025, 0.05, 0.10, 0.20)
#: rule-rate ladder: an organisation rate is rounded up to the next step (no daily drift)
LADDER = np.array([0.0025, 0.005, 0.01, 0.025, 0.05, 0.10, 0.20, 0.50, 1.0])
MIN_M, MAX_M, EDGE = 0.7, 5.0, 0.5
NEG = -np.inf
POLICY_FLAGS = ("request_too_big",)  # an organisation-learned line: a policy override
#: override name -> (v4 value, reason index in DSTAR_NAMES)
OVERRIDES = {
    "first_access_5": (0.9, 15),
    "first_access_4": (0.8, 15),
    "request_too_big": (0.9, 12),
}
FIRST_ACCESS = "First-access floor (policy)"


def g(s: np.ndarray | float) -> np.ndarray:
    """The engine's curve (engine.py:184-188): [0, 1] -> [0.7, 5], exactly 1 at 0.5."""
    s = np.asarray(s, dtype=np.float64)
    return np.where(s >= EDGE, MAX_M ** (2 * s - 1), MIN_M ** (1 - 2 * s))


def _clean(v: np.ndarray) -> np.ndarray:
    return np.where(np.isnan(v), NEG, v.astype(np.float64))


# ── loading: the statistic, the overrides and the agent-day grids ────────────────────────────
#: the red-flag area's pooled oversized line (RF1), re-implemented from pooled_line_rates.py:29-56
#: and red_flag_arms.py:52-67, 135-148: learned on days 0-29 only, never refitted
RF1_LEARN_DAYS, RF1_ALPHA, RF1_REF_Q, RF1_MIN_REF, KB = 30, 0.005, 0.99, 100, 1_000
CONTENT_TOOLS = frozenset(
    {
        "create_issue",
        "add_issue_comment",
        "create_pull_request_review",
        "create_pull_request",
        "create_release",
        "create_or_update_file",
        "push_files",
    }
)


def _order_stat(vals: np.ndarray, q: float) -> float | None:
    """Split-conformal order statistic: the ceil(q (n + 1))-th smallest value (red_flag_arms:139)."""
    vals = np.sort(vals)
    k = int(np.ceil(q * (len(vals) + 1)))
    return None if k > len(vals) else float(vals[k - 1])


def rf1_raised(agent, day, tool, size, op, tool_names) -> np.ndarray:
    """Calls over the pooled agent-day line: one 0.5% budget per agent-day, top identity left out."""
    learn = day < RF1_LEARN_DAYS
    n_tools = len(tool_names)
    key = (agent[learn] * 1000 + day[learn]) * n_tools + tool[learn]
    uk, inv = np.unique(key, return_inverse=True)
    biggest = np.zeros(len(uk))
    np.maximum.at(biggest, inv, size[learn])
    ad, t_of = uk // n_tools, uk % n_tools
    ref = {}
    for t in range(n_tools):
        v = np.sort(biggest[t_of == t])
        if len(v) >= RF1_MIN_REF:
            ref[t] = v[min(len(v) - 1, int(np.ceil(RF1_REF_Q * (len(v) + 1))) - 1)]
    tool_op = {int(t): int(np.bincount(op[tool == t]).argmax()) for t in np.unique(tool)}

    def cls(t: int) -> tuple[int, bool]:
        return tool_op.get(t, 1), tool_names[t] in CONTENT_TOOLS

    by: dict = {}
    for t, r in ref.items():
        by.setdefault(cls(t), []).append(r)
    cmed = {c: sorted(v)[len(v) // 2] for c, v in by.items()}
    top = max(ref.values())
    reff = np.array([ref.get(t) or cmed.get(cls(t)) or top for t in range(n_tools)], float)
    ua, ainv = np.unique(ad, return_inverse=True)
    ratio = np.zeros(len(ua))
    np.maximum.at(ratio, ainv, biggest / reff[t_of])
    k = _order_stat(ratio, 1 - RF1_ALPHA)
    who = ua // 1000
    tail = np.bincount(who[ratio > k]) if (ratio > k).any() else None
    if tail is not None:
        k = _order_stat(ratio[who != tail.argmax()], 1 - RF1_ALPHA)
    line = np.ceil(k * reff / KB) * KB
    return size > line[tool]


def load(npz: Path, naive: bool, line: str = "v4") -> dict:
    """Per-call statistic (s1 without the overrides), override flags and agent-day grids.

    ``naive``: the statistic is v4's own s1 (overrides inside), the 04 section 6.3 baseline."""
    meta = json.loads(npz.with_suffix(".json").read_text())
    keys = [d["key"] for d in meta["dimensions"]]
    with np.load(npz) as z:
        c = {k: z[k] for k in ("agent", "day", "A", "s1", "dstar", "s2", "floor", "role")}
        c |= {k: z[k] for k in ("size", "size_limit", "tool", "op")}
        c |= {k: z[k] for k in ("raw_request_too_big", "s_asset")}
        m = {k: z[f"msg_{k}"] for k in ("agent", "day", "s1", "dstar", "s2")}
        if naive:
            s, d = _clean(c["s1"]), c["dstar"].astype(np.int64)
        else:
            s, d = np.full(len(c["agent"]), NEG), np.full(len(c["agent"]), -1, np.int64)
            for i, k in enumerate(keys):
                if k in POLICY_FLAGS:
                    continue
                v = _clean(z["asset_nofloor"] if k == "asset" else z[f"s_{k}"])
                better = v > s
                s, d = np.where(better, v, s), np.where(better, i, d)
            # keep v4's d* (its dict order breaks ties) wherever v4's s1 is the statistic
            same = (_clean(c["s1"]) == s) & (c["dstar"] != 12)
            same &= (c["dstar"] != 7) | np.isnan(c["floor"]) | (c["s_asset"] == z["asset_nofloor"])
            d = np.where(same, c["dstar"], d)
    n_agents, n_days = len(meta["agents"]), int(max(c["day"].max(), m["day"].max())) + 1
    ag, dy = c["agent"].astype(np.int64), c["day"].astype(np.int64)
    active = np.zeros((n_agents, n_days), bool)
    active[ag, dy] = True
    q = np.full(n_agents * n_days, NEG)
    np.maximum.at(q, ag * n_days + dy, s)
    s_msg = _clean(m["s1"])
    np.maximum.at(q, m["agent"].astype(np.int64) * n_days + m["day"], s_msg)
    cs = np.concatenate([np.zeros((n_agents, 1), np.int64), np.cumsum(active, 1)], 1)
    t = np.arange(n_days)
    a_grid = cs[:, t] - cs[:, np.maximum(0, t - PAST_DAYS)]
    if not np.array_equal(a_grid[ag, dy], c["A"]):
        raise ValueError("A grid disagrees with the dump's A column")
    fl = c["floor"]
    raised = {
        "first_access_5": fl > 0.85,
        "first_access_4": (fl > 0.75) & (fl < 0.85),
        "request_too_big": ~np.isnan(c["raw_request_too_big"]),
    }
    if not np.array_equal(raised["request_too_big"], c["size"] > c["size_limit"]):
        raise ValueError("v4's oversized flag is not size > size_limit")
    if line == "rf1":
        raised["request_too_big"] = rf1_raised(
            ag, dy, c["tool"].astype(np.int64), c["size"].astype(np.int64), c["op"], meta["tools"]
        )
    roles = [r["role"] for r in meta["agents"]]
    role_names = meta["roles"]
    return {
        "meta": meta,
        "n_agents": n_agents,
        "n_days": n_days,
        "agent": ag,
        "day": dy,
        "A": c["A"].astype(np.int64),
        "s": s,
        "dstar": d,
        "s2": c["s2"].astype(np.float64),
        "raised": {} if naive else raised,
        "msg_agent": m["agent"].astype(np.int64),
        "msg_day": m["day"].astype(np.int64),
        "msg_s": s_msg,
        "msg_dstar": m["dstar"].astype(np.int64),
        "msg_s2": m["s2"].astype(np.float64),
        "active": active,
        "Q": q.reshape(n_agents, n_days),
        "A_grid": a_grid,
        "role": np.array([role_names.index(r) for r in roles]),
        "is_bot": np.array(["bot" in r for r in roles]),
    }


# ── pools (Mondrian strata: role, then people or bots, then everyone) ────────────────────────
def _resolve(values: np.ndarray, role: np.ndarray, is_bot: np.ndarray, n_roles: int) -> list:
    """Sorted pool per role, falling back to the agent's class, then to everyone."""
    org = np.sort(values)
    cls = {b: np.sort(values[is_bot == b]) for b in (False, True)}
    out = []
    for r in range(n_roles):
        mine = np.sort(values[role == r])
        bot = bool(is_bot[role == r][0]) if (role == r).any() else False
        pick = next((x for x in (mine, cls[bot], org) if len(x) >= MIN_POOL), None)
        out.append(pick)
    return out


def _pool_p(pool: np.ndarray, x: np.ndarray) -> np.ndarray:
    n = len(pool)
    return (1 + n - np.searchsorted(pool, x, side="left")) / (n + 1)


def day_loop(w: dict, hold: bool, naive: bool) -> dict:
    """Walk the days in order: day ranks, records, holds, pools and each day's sorted window."""
    q, active, a_grid = w["Q"], w["active"], w["A_grid"]
    n_agents, n_days = w["n_agents"], w["n_days"]
    n_roles = len(w["meta"]["roles"])
    agent_role = w["role"]
    held = np.zeros_like(active)
    record = np.zeros_like(active)
    p_day = np.ones((n_agents, n_days))
    windows = np.full((n_days - EVAL_FROM, n_agents, PAST_DAYS), NEG)
    rec_pools, new_pools = [], []
    for t in range(n_days):
        lo = max(0, t - PAST_DAYS)
        days = np.arange(lo, t)
        live = held[:, lo:t] & (t - days <= HOLD_DAYS)[None, :]
        win = np.where(active[:, lo:t] & ~live, q[:, lo:t], NEG)
        x, a = q[:, t], a_grid[:, t]
        count = (win >= x[:, None]).sum(1)
        rlo = max(0, t - RECORD_KEEP)
        rmask = record[:, rlo:t] & (a_grid[:, rlo:t] >= NEWCOMER_A)
        rrole = np.repeat(agent_role[:, None], t - rlo, 1)
        rbot = np.repeat(w["is_bot"][:, None], t - rlo, 1)
        rec = _resolve(q[:, rlo:t][rmask], rrole[rmask], rbot[rmask], n_roles)
        nlo = max(0, t - NEWCOMER_KEEP)
        nmask = active[:, nlo:t] & (a_grid[:, nlo:t] < NEWCOMER_A)
        nrole = np.repeat(agent_role[:, None], t - nlo, 1)
        nbot = np.repeat(w["is_bot"][:, None], t - nlo, 1)
        new = _resolve(q[:, nlo:t][nmask], nrole[nmask], nbot[nmask], n_roles)
        p, is_rec = _p_values(x, a, count, agent_role, rec, new, naive)
        p_day[:, t] = p
        record[:, t] = is_rec & active[:, t]
        if hold:
            held[:, t] = record[:, t]
        if t >= EVAL_FROM:
            k = t - lo
            windows[t - EVAL_FROM, :, PAST_DAYS - k :] = np.sort(win, 1)
            rec_pools.append(rec)
            new_pools.append(new)
    return {
        "p_day": p_day,
        "record": record,
        "held": held,
        "windows": windows,
        "rec_pools": rec_pools,
        "new_pools": new_pools,
    }


def _p_values(x, a, count, role, rec, new, naive) -> tuple[np.ndarray, np.ndarray]:
    """Day rank for values x of callers with A = a and ``count`` past days at least as strange.

    rec, new: per-role sorted pools (or None). Returns (p, is_record); p = 0.5 (M = 1) when
    nothing took part or a newcomer has no pool."""
    finite = np.isfinite(x)
    p = (1 + count) / (a + 1)
    is_rec = finite & (count == 0) & (a >= NEWCOMER_A)
    if naive:
        return np.where(finite, p, 0.5), is_rec
    newcomer = finite & (a < NEWCOMER_A)
    for r in np.unique(role[is_rec | newcomer]):
        sel = is_rec & (role == r)
        if sel.any() and rec[r] is not None:
            p[sel] = _pool_p(rec[r], x[sel]) / (a[sel] + 1)
        sel = newcomer & (role == r)
        if sel.any():
            p[sel] = 0.5 if new[r] is None else _pool_p(new[r], x[sel])
    return np.where(finite, p, 0.5), is_rec


def row_p(w: dict, loop: dict, x, agent, day, a) -> np.ndarray:
    """Day rank of every scored row (day >= 90); NaN for the others."""
    out = np.full(len(x), np.nan)
    idx = np.flatnonzero(day >= EVAL_FROM)
    for start in range(0, len(idx), 400_000):
        sl = idx[start : start + 400_000]
        win = loop["windows"][day[sl] - EVAL_FROM, agent[sl]]
        count = (win >= x[sl, None]).sum(1)
        role = w["role"][agent[sl]]
        p = np.empty(len(sl))
        for t in np.unique(day[sl]):
            m = day[sl] == t
            i = t - EVAL_FROM
            p[m], _ = _p_values(
                x[sl][m],
                a[sl][m],
                count[m],
                role[m],
                loop["rec_pools"][i],
                loop["new_pools"][i],
                loop["naive"],
            )
        out[sl] = p
    return out


def org_rates(w: dict) -> dict[str, np.ndarray]:
    """beta per override and day: (1 + raised agent-days) / (active agent-days + 1), t-89..t-1."""
    n_days, out = w["n_days"], {}
    t = np.arange(n_days)
    lo = np.maximum(0, t - PAST_DAYS)
    act = np.concatenate([[0], np.cumsum(w["active"].sum(0))])
    for name, mask in w["raised"].items():
        grid = np.zeros((w["n_agents"], n_days), bool)
        grid[w["agent"][mask], w["day"][mask]] = True
        cum = np.concatenate([[0], np.cumsum(grid.sum(0))])
        out[name] = (1 + cum[t] - cum[lo]) / (act[t] - act[lo] + 1)
        w.setdefault("raised_grid", {})[name] = grid
    return out


# ── the arm ──────────────────────────────────────────────────────────────────────────────────
def build(
    npz: Path, hold: bool = False, naive: bool = False, pricing: str = "org", line: str = "v4"
) -> dict:
    """Primary, secondary and d* per call and per message, plus the day-level ranks."""
    w = load(npz, naive, line)
    loop = day_loop(w, hold, naive) | {"naive": naive}
    p = row_p(w, loop, w["s"], w["agent"], w["day"], w["A"])
    msg_a = w["A_grid"][w["msg_agent"], w["msg_day"]]
    p_msg = row_p(w, loop, w["msg_s"], w["msg_agent"], w["msg_day"], msg_a)
    m_stat, m_msg = g(1 - p), g(1 - p_msg)
    primary, dstar = m_stat.copy(), w["dstar"].copy()
    beta = org_rates(w)
    p_rule = {}
    for name, mask in w["raised"].items():
        v4_value, reason = OVERRIDES[name]
        fixed = np.full(w["n_days"], 1 - v4_value)
        rate = beta[name]
        if pricing == "ladder":
            rate = LADDER[np.searchsorted(LADDER, rate - 1e-12, side="left")]
        p_rule[name] = fixed if pricing == "v4" else np.minimum(rate, fixed)
        m_rule = np.where(mask, g(1 - p_rule[name][w["day"]]), -np.inf)
        win = m_rule > primary
        primary, dstar = np.where(win, m_rule, primary), np.where(win, reason, dstar)
    scored = w["day"] >= EVAL_FROM
    primary[~scored] = np.nan
    m_msg[w["msg_day"] < EVAL_FROM] = np.nan
    return {
        "w": w,
        "loop": loop,
        "beta": beta,
        "p_rule": p_rule,
        "primary": primary,
        "secondary": w["s2"],
        "dstar": dstar,
        "msg_primary": m_msg,
        "msg_secondary": w["msg_s2"],
        "msg_dstar": w["msg_dstar"],
        "p_call": p,
    }


# ── the guarantee check: stated alpha against realised (diagnostic, not a headline) ──────────
def reliability(npz: Path, arm: dict) -> dict:
    """Share of agent-days with day rank <= t, by evaluator day label, A band and class."""
    wd = ce.load_world(npz)
    w, loop = arm["w"], arm["loop"]
    stack_agent = np.concatenate([w["agent"], w["msg_agent"]])
    agent = stack_agent[wd.rows[wd.starts]]
    day = wd.day.astype(np.int64)
    p_stat = loop["p_day"][agent, day]
    p_final = p_stat.copy()
    for name, grid in w.get("raised_grid", {}).items():
        on = grid[agent, day]
        p_final = np.where(on, np.minimum(p_final, arm["p_rule"][name][day]), p_final)
    held_cum = np.concatenate(
        [np.zeros((w["n_agents"], 1), np.int64), np.cumsum(loop["held"], 1)], 1
    )
    held_now = held_cum[agent, day] - held_cum[agent, np.maximum(0, day - HOLD_DAYS)]
    a_day = w["A_grid"][agent, day]
    bands = {
        "all": np.ones(len(day), bool),
        "A < 15": a_day < NEWCOMER_A,
        "15 <= A < 45": (a_day >= 15) & (a_day < 45),
        "A >= 45": a_day >= 45,
        "people": ~wd.is_bot,
        "bots": wd.is_bot,
    }
    halves = {"days 90-134": day <= 134, "days 135-180": day >= 135}
    out: dict = {"stated": list(STATED), "rows": []}
    for label_name, lab in (("ordinary", 0), ("change", 1), ("benign", -1)):
        lab_mask = wd.label != 2 if lab < 0 else wd.label == lab
        for which, p in (("statistic", p_stat), ("final", p_final)):
            for bname, bmask in bands.items():
                for hname, hmask in ({"days 90-180": np.ones(len(day), bool)} | halves).items():
                    if hname != "days 90-180" and (bname != "all" or which != "statistic"):
                        continue
                    sel = lab_mask & bmask & hmask
                    if not sel.any():
                        continue
                    out["rows"].append(
                        {
                            "label": label_name,
                            "p": which,
                            "stratum": bname,
                            "window": hname,
                            "days": int(sel.sum()),
                            "realised": [float((p[sel] <= t).mean()) for t in STATED],
                        }
                    )
    ordinary = wd.label == 0
    rates = []
    for a in np.unique(agent[ordinary]):
        sel = ordinary & (agent == a)
        if sel.sum() >= 30:
            rates.append(float((p_stat[sel] <= 0.05).mean()))
    rates = np.array(rates)
    est = ordinary & (a_day >= NEWCOMER_A)
    out["per_agent_at_5pct"] = {
        "agents": len(rates),
        "median": float(np.median(rates)),
        "p90": float(np.quantile(rates, 0.9)),
        "max": float(rates.max()),
        "share_above_7.5pct": float((rates > 0.075).mean()),
    }
    floor = 1 / (a_day + 1)
    out["record_days"] = {
        "ordinary_established_days": int(est.sum()),
        "share_records": float(loop["record"][agent[est], day[est]].mean()),
        "mean_floor_1_over_A_plus_1": float(floor[est].mean()),
    }
    out["held_days_per_agent_day"] = {
        "mean": float(held_now[ordinary].mean()),
        "max": float(held_now[ordinary].max()) if ordinary.any() else 0.0,
        "mean_K_over_A_plus_1": float((held_now[est] / (a_day[est] + 1)).mean()),
    }
    out["beta_mean_days_90_180"] = {k: float(v[EVAL_FROM:].mean()) for k, v in arm["beta"].items()}
    newcomer = a_day < NEWCOMER_A
    out["newcomers"] = {
        "agent_days": int(newcomer.sum()),
        "ordinary": int((newcomer & ordinary).sum()),
        "M_stat_quantiles_ordinary": [
            float(x) for x in np.quantile(g(1 - p_stat[newcomer & ordinary]), [0.1, 0.5, 0.9])
        ]
        if (newcomer & ordinary).any()
        else None,
    }
    return out


def _reliability_md(rel: dict) -> list[str]:
    head = "| Day label | p | Stratum | Window | Days | " + " | ".join(
        f"t={100 * t:g}%" for t in rel["stated"]
    )
    lines = [head + " |", "|" + "---|" * (5 + len(rel["stated"]))]
    for r in rel["rows"]:
        vals = " | ".join(f"{100 * v:.2f}%" for v in r["realised"])
        lines.append(
            f"| {r['label']} | {r['p']} | {r['stratum']} | {r['window']} | {r['days']} | {vals} |"
        )
    lines += ["", f"Per-agent rate at t = 5% (statistic, ordinary): {rel['per_agent_at_5pct']}"]
    lines += [f"Record days: {rel['record_days']}", f"Held days: {rel['held_days_per_agent_day']}"]
    lines += [f"Override org rates (mean beta): {rel['beta_mean_days_90_180']}"]
    lines += [f"Newcomers: {rel['newcomers']}"]
    return lines


# ── a compact summary of the evaluator's own results ─────────────────────────────────────────
KINDS = ("cross_copy", "overfetch", "bulk_export", "scope_creep")


def summary_rows(res: dict) -> list[list[str]]:
    """One row per report-window operating point, read from the evaluator's dict."""
    lists = {lst["k"]: lst["credited"] for lst in res["review_list"]}
    rows = []
    for pt in res["operating_points"]:
        m = pt["metrics"]
        if m["window"][0] != ce.REPORT_FIRST_DAY:
            continue
        lab, gray = m["by_day_label"], m["gray"]

        def kind(k: str, gray=gray) -> str:
            b = gray["by_kind"].get(k)
            return f"{b['caught']}/{b['episodes']}" if b else "-"

        reasons = m["benign_alert_reasons"]["benign"]["share"]
        top = ", ".join(f"{k} {100 * v:.0f}%" for k, v in list(reasons.items())[:3])
        st = m["strata"]
        rows.append(
            [
                res["name"],
                pt["label"],
                ce._pct(pt["fit"]["fit_rate"]),
                ce._pct(lab["ordinary"]["rate"]),
                ce._pct(lab["change"]["rate"]),
                f"{gray['overall']['caught']}/{gray['overall']['episodes']}",
                " ".join(kind(k) for k in KINDS),
                ce._pct(st["is_bot"]["people"]["ordinary"]["rate"]),
                ce._pct(st["is_bot"]["bots"]["ordinary"]["rate"]),
                ce._pct(st["history"]["A < 15"]["benign"]["rate"]),
                top or "-",
            ]
        )
    rows.append(
        [
            res["name"],
            "review list k=4 / 8 (credited)",
            "",
            "",
            "",
            " / ".join(ce._pct(lists[k]["all"]["recall"], 1) for k in sorted(lists)),
            " ".join(
                "/".join(ce._pct(lists[k].get(x, {}).get("recall"), 0) for k in sorted(lists))
                for x in KINDS
            ),
            "",
            "",
            "",
            "",
        ]
    )
    return rows


SUMMARY_HEAD = [
    "Arm",
    "Point",
    "Fit rate",
    "Ordinary",
    "Change",
    "Gray caught",
    "cross_copy overfetch bulk_export scope_creep",
    "People ord.",
    "Bots ord.",
    "A<15 benign",
    "Benign alerts by d* (top 3)",
]


ARMS = (
    ("day calibration, rules at v4 values", False, False, "v4", "v4"),
    ("day calibration, rules at org rate", False, False, "org", "v4"),
    ("day calibration, org rate, pooled oversized line", False, False, "org", "rf1"),
    ("PROPOSAL: day calibration, rule ladder, pooled line", False, False, "ladder", "rf1"),
    ("proposal + record hold", True, False, "ladder", "rf1"),
    ("naive day calibration (v4 s1)", False, True, "v4", "v4"),
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("npz", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    names = None
    for npz in args.npz:
        t0 = time.time()
        meta = json.loads(npz.with_suffix(".json").read_text())
        names = [d["paper_name"] for d in meta["dimensions"]] + [FIRST_ACCESS]
        stated_lines = {f"stated {100 * a:g}%": float(g(1 - a)) for a in (0.01, 0.025, 0.05)}
        results = [ce.v4_reference(npz, check=True)]
        rels = {}
        for label, hold, naive, pricing, line in ARMS:
            arm = build(npz, hold=hold, naive=naive, pricing=pricing, line=line)
            res = ce.evaluate(
                npz,
                arm["primary"],
                arm["secondary"],
                arm["dstar"],
                name=label,
                msg_primary=arm["msg_primary"],
                msg_secondary=arm["msg_secondary"],
                msg_dstar=arm["msg_dstar"],
                dstar_names=names,
                fixed_lines=stated_lines | {"x3": 3.0},
            )
            results.append(res)
            rels[label] = reliability(npz, arm)
            del arm
        world = meta["world"]
        md = [f"# Personal day calibration: {world} (DEVELOPMENT WORLD)", ""]
        md += ce._table(SUMMARY_HEAD, [r for res in results for r in summary_rows(res)])
        for label, rel in rels.items():
            md += ["", f"## Stated against realised: {label}", ""] + _reliability_md(rel)
        md += ["", ce.to_markdown(results)]
        (args.out / f"{world}.pdc.md").write_text("\n".join(md))
        payload = {"results": results, "reliability": rels}
        (args.out / f"{world}.pdc.json").write_text(json.dumps(ce._jsonable(payload)))
        print(
            f"{world}: {time.time() - t0:.0f} s, mismatches {results[0]['check'].get('mismatches')}"
        )


if __name__ == "__main__":
    main()
