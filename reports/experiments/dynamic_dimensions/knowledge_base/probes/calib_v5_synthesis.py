"""v5 score calibration, synthesis arms (DEVELOPMENT WORLD only; not a test result).

The base is the "daily rates with budget shares" arm of calib_per_dim_conformal.py (its
RECOMMENDED ArmSpec: stages 1-2, group weights, record rank, no stage 3). This script adds the
grafts the v5 synthesis takes from the other proposals and measures them one at a time:

  S0  base, reproduced (first-access floor at its v4 value, oversized over v4's per-tool line)
  S1  S0 + the first-access floor as a policy rule priced at its rule rate (calib_personal_day)
  S2  S1 + oversized request graded over the pooled agent-day line (RF1)
  S3  S2 with the floor at fixed prices (s5 at q = 1%, s4 at v4) instead of the rule rate
  S4  S2 with Missing handshake removed (a proxy for the MCP 2026-07-28 era, no initialize)
  S5  S3 with Cadence counted in past days, not past calls ("day units")  <- CHOSEN v5
  S6  S3 with the record-rank reference split by tenure band (A < 45, A >= 45)
  S7  S3 with the record-rank reference built from established callers only (A >= 20)

Rule rate: beta(t) = (1 + agent-days in [t-89, t-1] that raised the rule) / (active agent-days
in the window + 1), rounded up to LADDER, never priced weaker than its v4 value.

Every arm goes through calib_eval.evaluate (via calib_per_dim_conformal.evaluate_arm). The
script also prints diagnostics: a matched-benign-rate comparison, each group's spend against its
third of the budget, a weekday/weekend split and the per-caller spread at the stated 5% line.
Run: python3 calib_v5_synthesis.py <npz> [<npz> ...] --out <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import calib_eval as ce  # noqa: E402  (sibling probe, path set above)
import calib_per_dim_conformal as pdm  # noqa: E402
import calib_personal_day as pday  # noqa: E402

N_DAYS, PAST = pdm.N_DAYS, pdm.HISTORY_DAYS
LADDER = pday.LADDER  # 0.25, 0.5, 1, 2.5, 5, 10, 20, 50, 100 %: frozen with this design
V4_Q = {"s5": 1 / 18, "s4": 1 / 8}  # v4 floor values 0.9 and 0.8 on the q scale, s = 1/(1+2q)
FIXED_Q = {"s5": 0.01, "s4": 1 / 8}
STATED = (0.01, 0.025, 0.05, pdm.q_from_multiplier(3.0))
MATCHED = (0.01, 0.02, 0.03)
OVERSIZED, HANDSHAKE = 12, 14
GROUPS = {"cadence": range(0, 6), "footprint": range(6, 10), "flags": range(10, 15)}
ESTABLISHED_A = 20  # B4/B5's established_days
BAND_EDGE = 45  # the evaluator's upper history-band edge (calib_eval.py:59)
RECORD_DIMS = {d: "s" for d in pdm.CADENCE} | {10: "mag", 11: "mag"}  # dims with a record rank
ARMS = (  # name, floor pricing, RF1 line, drop missing handshake, stage-1 variant
    ("S0 base (budget shares, Part B)", "v4", False, False, "base"),
    ("S1 + floor at rule rate", "ladder", False, False, "base"),
    ("S2 + oversized over RF1 line", "ladder", True, False, "base"),
    ("S3 = S2, floor at fixed prices", "fixed", True, False, "base"),
    ("S4 = S2, no missing handshake", "ladder", True, True, "base"),
    ("S5 = S3, Cadence in day units (CHOSEN)", "fixed", True, False, "days"),
    ("S6 = S3, record reference by tenure band", "fixed", True, False, "band"),
    ("S7 = S3, record reference established only", "fixed", True, False, "established"),
)


def record_rank_masked(v, ref_mask, query_mask, strength, n_bins, bins) -> np.ndarray:
    """pdm.record_rank with separate reference and query masks (add-one, ties count >=)."""
    out = np.ones(len(v.agent))
    if not query_mask.any() or not ref_mask.any():
        return out
    ref_day, ref_val = pdm.day_max_units(v.agent, v.day, strength, ref_mask)
    qd, qb = v.day[query_mask], bins(strength[query_mask])
    ge = pdm.window_count(ref_day, bins(ref_val), qd, qb, n_bins, at_least=True)
    out[query_mask] = (1.0 + ge) / (pdm.window_units(ref_day, qd) + 1.0)
    return out


def stage1_variant(v: pdm.Vectors, st1: pdm.Stage1, kind: str) -> np.ndarray:
    """q_rr for one stage-1 variant (records are the same set in every variant)."""
    q = st1.q_rr.copy()
    a1 = v.a.astype(np.float64) + 1.0
    if kind == "days":  # N_d = his past days whose day maximum is at least today's score
        for d in pdm.CADENCE:
            n = np.full(len(v.agent), -1, np.int64)
            for lo, hi in pdm.agent_slices(v.agent):
                sd = v.s[lo:hi, d]
                ok = np.flatnonzero(np.isfinite(sd))
                if len(ok) == 0:
                    continue
                ag, dy = v.agent[lo:hi][ok], v.day[lo:hi][ok]
                rd, rv = pdm.day_max_units(ag, dy, sd[ok], np.ones(len(ok), bool))
                b = pdm.s_bin(sd[ok])
                n[lo + ok] = pdm.window_count(rd, pdm.s_bin(rv), dy, b, pdm.S_BINS, at_least=True)
            plain = (n >= 0) & ~st1.record[:, d]
            q[plain, d] = (1.0 + n[plain]) / a1[plain]
        return q
    for d, how in RECORD_DIMS.items():
        rec = st1.record[:, d]
        strength = v.s[:, d] if how == "s" else v.magnitude[d]
        nb, bins = (pdm.S_BINS, pdm.s_bin) if how == "s" else (pdm.MAG_BINS, pdm.mag_bin)
        if kind == "band":
            rr = np.ones(len(v.agent))
            for band in (v.a < BAND_EDGE, v.a >= BAND_EDGE):
                m = rec & band
                rr[m] = record_rank_masked(v, m, m, strength, nb, bins)[m]
        else:  # established-only reference, every record queried against it
            rr = record_rank_masked(v, rec & (v.a >= ESTABLISHED_A), rec, strength, nb, bins)
        q[rec, d] = rr[rec] / a1[rec]
    return q


def rule_rate(v: pdm.Vectors, raised: np.ndarray) -> np.ndarray:
    """beta per day: (1 + raised agent-days on [t-89, t-1]) / (active agent-days + 1)."""
    act = np.bincount(np.unique(v.agent * N_DAYS + v.day) % N_DAYS, minlength=N_DAYS)
    rai = np.bincount(np.unique((v.agent * N_DAYS + v.day)[raised]) % N_DAYS, minlength=N_DAYS)
    ca, cr = np.r_[0, np.cumsum(act)], np.r_[0, np.cumsum(rai)]
    t = np.arange(N_DAYS)
    lo = np.maximum(0, t - PAST)
    return (1 + cr[t] - cr[lo]) / (ca[t] - ca[lo] + 1)


def floor_q(v: pdm.Vectors, pricing: str) -> tuple[np.ndarray, dict]:
    """q of the first-access rule per call (inf if not raised) and the daily prices."""
    masks = {"s5": v.floor > 0.85, "s4": (v.floor > 0.75) & (v.floor < 0.85)}
    q, prices = np.full(len(v.agent), np.inf), {}
    for name, m in masks.items():
        if pricing == "v4":
            price = np.full(N_DAYS, V4_Q[name])
        elif pricing == "fixed":
            price = np.full(N_DAYS, FIXED_Q[name])
        else:
            beta = rule_rate(v, m)
            step = LADDER[np.searchsorted(LADDER, beta - 1e-12, side="left")]
            price = np.minimum(step, V4_Q[name])
            prices[f"beta_{name}_days90_180"] = [float(beta[90:181].min()), float(beta[90:].max())]
        prices[f"price_{name}_days90_180"] = sorted({float(x) for x in price[90:181]})
        q[m] = price[v.day[m]]
    return q, prices


class _LineCatcher(np.ndarray):
    """An int array that remembers the right side of its last ``>``: pday.rf1_raised ends with
    ``size > line[tool]``, so this recovers the exact per-call RF1 line without copying it."""

    caught: np.ndarray | None = None

    def __gt__(self, other):  # noqa: D105
        _LineCatcher.caught = np.asarray(other)
        return np.asarray(self) > np.asarray(other)


def rf1_magnitude(npz: Path, v: pdm.Vectors) -> np.ndarray:
    """size / RF1 line where the call is over it (NaN otherwise), line from pday.rf1_raised."""
    with np.load(npz) as z:
        tool, op = z["tool"].astype(np.int64), z["op"]
        size = z["size"].astype(np.int64)
    over = pday.rf1_raised(v.agent, v.day, tool, size.view(_LineCatcher), op, v.meta["tools"])
    line = _LineCatcher.caught.astype(np.float64)
    if line.shape != size.shape:
        raise ValueError("could not recover the RF1 line")
    return np.where(over, size / np.maximum(line, 1.0), np.nan)


def run(v: pdm.Vectors, st1: pdm.Stage1, spec: tuple, rf1_q: np.ndarray, q_rr: dict) -> tuple:
    """One arm: budget shares, then the first-access rule as a min on q."""
    _, pricing, rf1, no_hs, variant = spec
    qd = q_rr[variant].copy()
    if rf1:
        qd[:, OVERSIZED] = rf1_q
    if no_hs:
        qd[:, HANDSHAKE] = np.inf
    w = pdm.WEIGHTS["group"]
    q, dstar, q2 = pdm.stage2(qd, w)
    mq, mdstar, mq2 = pdm.stage2(st1.msg_q, w)
    fq, prices = floor_q(v, pricing)
    use = fq < q
    p = np.where(use, fq, q)
    out = pdm.ArmOut(
        p, np.where(use, q, q2), np.where(use, pdm.FLOOR_REASON, dstar), mq, mq2, mdstar, q
    )
    return out, qd, fq, prices


def day_groups(npz: Path) -> tuple[ce.World, np.ndarray]:
    """The evaluator's agent-day grouping and the agent of every stacked row."""
    w = ce.load_world(npz)
    with np.load(npz) as z:
        agent_row = np.r_[z["agent"], z["msg_agent"]].astype(np.int64)
    return w, agent_row


def day_min(w: ce.World, x_rows: np.ndarray) -> np.ndarray:
    """Per agent-day minimum of a stacked [calls; messages] array (inf when absent)."""
    return np.minimum.reduceat(x_rows[w.rows], w.starts)


def matched(w: ce.World, agent_row: np.ndarray, prim: np.ndarray, sec: np.ndarray) -> dict:
    """Post-hoc matched benign rate on the report window (diagnostic, judge-2 method)."""
    p = np.where(np.isnan(prim), -np.inf, prim)
    s = np.where(np.isnan(sec), -np.inf, sec)
    order = np.lexsort((s, p))
    new = np.r_[True, (p[order][1:] != p[order][:-1]) | (s[order][1:] != s[order][:-1])]
    r = np.empty(len(p), np.int64)
    r[order] = np.cumsum(new)
    r[~np.isfinite(p)] = 0
    dkey = np.maximum.reduceat(r[w.rows], w.starts)
    rep = w.day >= ce.REPORT_FIRST_DAY
    ben, ordy, chg = rep & (w.label != 2), rep & (w.label == 0), rep & (w.label == 1)
    sel = w.call_day[w.gray_call] >= ce.REPORT_FIRST_DAY
    gcalls, geps = w.gray_call[sel], w.gray_ep[sel]
    eps = np.unique(geps)
    agent_day = agent_row[w.rows[w.starts]]
    bk = np.sort(dkey[ben])[::-1]
    res = {}
    for rate in MATCHED:
        k = int(np.floor(rate * ben.sum()))
        hot = dkey >= (bk[k] + 1 if k < len(bk) else 1)
        caught = np.zeros(int(w.gray_ep.max()) + 1, bool)
        np.logical_or.at(caught, geps, r[gcalls] >= (bk[k] + 1 if k < len(bk) else 1))
        kinds: dict = {}
        for e in eps:
            name = w.meta["kinds"][int(w.ep_kind[e])]
            a, b = kinds.get(name, (0, 0))
            kinds[name] = (a + int(caught[e]), b + 1)
        cnt = np.bincount(agent_day[hot & ben], minlength=agent_row.max() + 1)
        callers = np.flatnonzero(np.bincount(agent_day[ben], minlength=agent_row.max() + 1))
        c = np.sort(cnt[callers])[::-1]
        top = max(1, int(np.ceil(0.05 * len(callers))))
        res[f"{rate:g}"] = {
            "benign": float((hot & ben).sum() / ben.sum()),
            "ordinary": float((hot & ordy).sum() / ordy.sum()),
            "change": float((hot & chg).sum() / chg.sum()),
            "newcomer": float(
                (hot & ben & (w.band == 0)).sum() / max(1, (ben & (w.band == 0)).sum())
            ),
            "gray": [int(caught[eps].sum()), len(eps)],
            "top5_share": float(c[:top].sum() / max(1, c.sum())),
            "kinds": kinds,
        }
    return res


def spend(w: ce.World, agent_row: np.ndarray, qd: np.ndarray, fq: np.ndarray, out) -> dict:
    """Realised share of ordinary agent-days per group / rule / weekday class (diagnostic)."""
    n_msg = len(out.msg_p)
    wgt = pdm.WEIGHTS["group"]
    ordy = w.label == 0
    halves = {"90-134": ordy & (w.day < 135), "135-180": ordy & (w.day >= 135)}
    weekend = (w.day + 3) % 7 >= 5  # epoch day 0 is a Thursday (memory.py:17-19)
    final = day_min(w, np.r_[out.p_final, out.msg_p])
    res: dict = {}
    for t in STATED:
        key = f"{100 * t:.3g}%"
        row = {h: float((final[m] <= t).mean()) for h, m in halves.items()}
        for name, dims in GROUPS.items():
            g = np.min(qd[:, list(dims)] / wgt[list(dims)], axis=1)
            gd = day_min(w, np.r_[g, np.full(n_msg, np.inf)])
            row[f"{name} (share {100 * t / 3:.3g}%)"] = {
                h: float((gd[m] <= t).mean()) for h, m in halves.items()
            }
        fd = day_min(w, np.r_[fq, np.full(n_msg, np.inf)])
        row["first-access rule"] = {h: float((fd[m] <= t).mean()) for h, m in halves.items()}
        allm = ordy & (w.day >= 90)
        row["weekday / weekend"] = [
            float((final[allm & ~weekend] <= t).mean()),
            float((final[allm & weekend] <= t).mean()),
            int((allm & weekend).sum()),
        ]
        res[key] = row
    agent_day = agent_row[w.rows[w.starts]]
    m = ordy & (w.day >= 90)
    hits = np.bincount(agent_day[m & (final <= 0.05)], minlength=agent_row.max() + 1)
    days = np.bincount(agent_day[m], minlength=agent_row.max() + 1)
    big = days >= 30
    per = hits[big] / days[big]
    res["per_caller_5pct"] = {
        "callers": int(big.sum()),
        "median": float(np.median(per)),
        "p90": float(np.quantile(per, 0.9)),
        "max": float(per.max()),
        "share_above_10pct": float((per > 0.10).mean()),
    }
    return res


def run_world(npz: Path) -> dict:
    """All arms on one world: evaluator results plus diagnostics."""
    t0 = time.time()
    pdm.hour_gap_rate = lambda v, a1: np.full(len(v.agent), np.inf)  # option not used here
    v = pdm.load_vectors(npz)
    st1 = pdm.stage1(v)
    mag = rf1_magnitude(npz, v)
    v.magnitude[OVERSIZED] = mag
    rf1_q = pdm.org_flag_rate(v, OVERSIZED)
    w, agent_row = day_groups(npz)
    res = {"world": npz.stem, "results": [ce.v4_reference(npz, check=False)], "diag": {}}
    with np.load(npz) as z:
        v4 = (z["M"], z["s2"], z["msg_M"], z["msg_s2"])
    res["diag"]["v4"] = {"matched": matched(w, agent_row, np.r_[v4[0], v4[2]], np.r_[v4[1], v4[3]])}
    res["diag"]["rf1_raised_share_of_calls"] = float(np.isfinite(mag).mean())
    q_rr = {"base": st1.q_rr}
    for kind in ("days", "band", "established"):
        q_rr[kind] = stage1_variant(v, st1, kind)
    for spec in ARMS:
        out, qd, fq, prices = run(v, st1, spec, rf1_q, q_rr)
        res["results"].append(pdm.evaluate_arm(npz, v, out, spec[0]))
        prim = pdm.neglog(np.r_[out.p_final, out.msg_p])
        sec = pdm.neglog(np.r_[out.q2, out.msg_q2])
        res["diag"][spec[0]] = {
            "matched": matched(w, agent_row, prim, sec),
            "spend": spend(w, agent_row, qd, fq, out),
            "prices": prices,
        }
        print(f"{npz.stem}: {spec[0]} at {time.time() - t0:.0f}s", flush=True)
    return res


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("npz", nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for npz in args.npz:
        res = run_world(npz)
        (args.out / f"v5syn_{npz.stem}.json").write_text(json.dumps(res, default=ce._jsonable))


if __name__ == "__main__":
    main()
