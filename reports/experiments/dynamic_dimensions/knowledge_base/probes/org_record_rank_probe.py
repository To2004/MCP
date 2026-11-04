"""v5 revision-2 probe (DEVELOPMENT WORLD only): the organisation-level record rank.

Review finding R2-1 (v5-design-spec.md, "Review log") replaces the record price c_d / (A + 1) by
an add-one rank among ALL the organisation's agent-days on which the dimension took part:

    q_d = min( 1 / (A + 1),  (1 + #{org record-days on d in [t-89, t-1], strength >= his})
                              / (N_d + 1) )                                       on a record day

N_d counts the org agent-days in the window on which d took part. The min with the personal
1 / (A + 1) keeps a record at least as strange as a non-record day; with a 90-day window the
personal part can never reach a stated line (the cap condition), so validity rests only on the
org rank. Arms, all on arm S5's code path of calib_v5_synthesis.py (v4 score vectors, oracle
simulator inputs; NOT the v5 engine):

  S5   the rev-1 design, reproduced (record price c_d / (A + 1))
  O1   S5 with the org-level record rank on Cadence, Burst and Sweep
  O2   O1 + Unsafe sequence records (first raise in his window) org-ranked with tied strength,
       the four alerting Red Flags at 1/12 each, Missing handshake capped at q/w >= 2/15
       (watch-only). Footprint stays on e (its q/w >= 12/90, so it cannot alert: D3 (b)).
  O3   O2 + the surge guard (finding R3-4): on a day when the agent-days that set a record on d
       (or raise Oversized request) number at least max(5, 3 x the window's daily mean), those
       agent-days are also ranked among today's agent-days, q = max(q_window, q_today). Offline
       this uses the whole day; online it would use the day so far.

Reports per world: per-dimension spend against w_d * alpha (ordinary days 90-134 and 135-180,
all benign days 90-180), realised rate of the full statistic, gray recall at the stated lines
(episodes on days >= 135), oracle matched-benign points (labelled ROC points), and the path
activity check N_d + 1 >= 1 / (w_d alpha) with the record-day counts R_d.

    python3 org_record_rank_probe.py <npz> [<npz> ...] --out <json>
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
import calib_v5_synthesis as syn  # noqa: E402

S5 = syn.ARMS[5]
STATED = syn.STATED  # 1%, 2.5%, 5% and x3 (9.43%)
REPORT_FIRST_DAY = 135
RECORD_DIMS = tuple(pdm.CADENCE) + (10, 11)  # dims with a strength to rank by
SEQUENCE, HANDSHAKE = 13, 14
WATCH_CAP = 2 / 15  # q/w floor of a watch-only dimension (above every stated line)
W_O2 = np.array([1 / 18] * 6 + [1 / 12] * 4 + [1 / 12] * 4 + [1 / 15])
SURGE_MIN, SURGE_FACTOR = 5, 3.0  # surge: today's count >= max(5, 3 x window daily mean)


def dim_inputs(v: pdm.Vectors, d: int, rec: np.ndarray) -> tuple:
    """(strength, bins, took) of a record dimension."""
    if d in pdm.CADENCE:
        return v.s[:, d], (pdm.S_BINS, pdm.s_bin), np.isfinite(v.s[:, d])
    if d == SEQUENCE:  # no strength in the vectors: every record ties
        return np.zeros(len(rec)), (pdm.MAG_BINS, pdm.mag_bin), np.ones(len(rec), bool)
    m = np.nan_to_num(v.magnitude[d], nan=0.0)
    return m, (pdm.MAG_BINS, pdm.mag_bin), np.ones(len(rec), bool)


def surge_price(v, mask, strength, took, bins, q) -> tuple[np.ndarray, int]:
    """q = max(q, q_today) on the masked rows of surge days; also the surge-day count 90-180."""
    nb, fn = bins
    ref_day, ref_val = pdm.day_max_units(v.agent, v.day, strength, mask)
    all_day, _ = pdm.day_max_units(v.agent, v.day, np.zeros(len(mask)), took)
    per_day = np.bincount(ref_day, minlength=pdm.N_DAYS)
    n_today = np.bincount(all_day, minlength=pdm.N_DAYS)
    mean_win = pdm.window_units(ref_day, np.arange(pdm.N_DAYS)) / pdm.HISTORY_DAYS
    surge = per_day >= np.maximum(SURGE_MIN, SURGE_FACTOR * mean_win)
    h = np.bincount(ref_day * nb + fn(ref_val), minlength=pdm.N_DAYS * nb)
    tail = np.cumsum(h.reshape(pdm.N_DAYS, nb)[:, ::-1], axis=1)[:, ::-1]
    rows = np.flatnonzero(mask & surge[v.day])
    out = q.copy()
    q_today = tail[v.day[rows], fn(strength[rows])] / (n_today[v.day[rows]] + 1.0)
    out[rows] = np.maximum(q[rows], q_today)
    return out, int(surge[90:181].sum())


def org_rank(
    v: pdm.Vectors, rec: np.ndarray, strength: np.ndarray, took: np.ndarray, bins
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(q_org on record rows, R per row day, N per row day) with ties counted as >=."""
    q = np.full(len(rec), np.inf)
    ref_day, ref_val = pdm.day_max_units(v.agent, v.day, strength, rec)
    all_day, _ = pdm.day_max_units(v.agent, v.day, np.zeros(len(rec)), took)
    n_units = pdm.window_units(all_day, v.day)
    r_units = pdm.window_units(ref_day, v.day)
    if rec.any():
        nb, fn = bins
        ge = pdm.window_count(
            ref_day, fn(ref_val), v.day[rec], fn(strength[rec]), nb, at_least=True
        )
        q[rec] = (1.0 + ge) / (n_units[rec] + 1.0)
    return q, r_units, n_units


def build_arms(v: pdm.Vectors, st1: pdm.Stage1, q_days: np.ndarray) -> tuple[dict, dict]:
    """Stage-1 matrices and weights of S5, O1 and O2, plus the path-activity counts."""
    a1 = v.a.astype(np.float64) + 1.0
    o1 = q_days.copy()
    seq_q = np.zeros(0)
    activity: dict = {}
    for d in RECORD_DIMS + (SEQUENCE,):
        rec = st1.record[:, d]
        strength, bins, took = dim_inputs(v, d, rec)
        q_org, r_units, n_units = org_rank(v, rec, strength, took, bins)
        days = (v.day >= 90) & (v.day <= 180)
        activity[d] = {
            "N_min": int(n_units[days].min()),
            "N_median": int(np.median(n_units[days])),
            "R_min": int(r_units[days].min()),
            "R_median": int(np.median(r_units[days])),
        }
        if d in RECORD_DIMS:
            o1[rec, d] = np.minimum(1.0 / a1[rec], q_org[rec])
        else:
            seq_q = np.minimum(1.0 / a1[rec], q_org[rec])
    o2 = o1.copy()
    o2[st1.record[:, SEQUENCE], SEQUENCE] = seq_q
    o2[:, HANDSHAKE] = np.maximum(o2[:, HANDSHAKE], WATCH_CAP * W_O2[HANDSHAKE])
    o3 = o2.copy()
    for d in RECORD_DIMS + (SEQUENCE,):
        rec = st1.record[:, d]
        strength, bins, took = dim_inputs(v, d, rec)
        o3[:, d], activity[d]["surge_days_90_180"] = surge_price(
            v, rec, strength, took, bins, o3[:, d]
        )
    w5 = pdm.WEIGHTS["group"]
    arms = {"S5": (q_days, w5), "O1": (o1, w5), "O2": (o2, W_O2), "O3": (o3, W_O2)}
    return arms, activity


def run_arm(v, st1, qd: np.ndarray, w: np.ndarray, rf1_q: np.ndarray, surge: bool):
    """Budget shares, then the fixed-price first-access floor as a min on q (S5's floor)."""
    qd = qd.copy()
    qd[:, syn.OVERSIZED] = rf1_q  # S5's pooled-line grading (RF1)
    if surge:
        raised = np.isfinite(rf1_q)
        m = np.nan_to_num(v.magnitude[syn.OVERSIZED], nan=0.0)
        bins = (pdm.MAG_BINS, pdm.mag_bin)
        qd[:, syn.OVERSIZED], _ = surge_price(
            v, raised, m, np.ones(len(raised), bool), bins, qd[:, syn.OVERSIZED]
        )
    q, dstar, q2 = pdm.stage2(qd, w)
    mq, mdstar, mq2 = pdm.stage2(st1.msg_q, w)
    fq, _ = syn.floor_q(v, "fixed")
    use = fq < q
    out = pdm.ArmOut(
        np.where(use, fq, q),
        np.where(use, q, q2),
        np.where(use, pdm.FLOOR_REASON, dstar),
        mq,
        mq2,
        mdstar,
        q,
    )
    return out, qd


def summarise(w: ce.World, agent_row, out, qd: np.ndarray, wts: np.ndarray, names) -> dict:
    """Spend per dimension, realised rate, gray recall at stated lines, oracle matched points."""
    n_msg = len(out.msg_p)
    ordy, ben = w.label == 0, w.label != 2
    masks = {
        "ord 90-134": ordy & (w.day >= 90) & (w.day < 135),
        "ord 135-180": ordy & (w.day >= 135),
        "benign 90-180": ben & (w.day >= 90),
    }
    final = syn.day_min(w, np.r_[out.p_final, out.msg_p])
    sel = w.call_day[w.gray_call] >= REPORT_FIRST_DAY
    gcalls, geps = w.gray_call[sel], w.gray_ep[sel]
    eps = np.unique(geps)
    res: dict = {"lines": {}, "spend": {}}
    for t in STATED:
        key = f"{100 * t:.3g}%"
        caught = np.zeros(int(w.gray_ep.max()) + 1, bool)
        np.logical_or.at(caught, geps, out.p_final[gcalls] <= t)
        kinds: dict = {}
        for e in eps:
            k = w.meta["kinds"][int(w.ep_kind[e])]
            a, b = kinds.get(k, (0, 0))
            kinds[k] = (a + int(caught[e]), b + 1)
        res["lines"][key] = {
            h: round(100 * float((final[m] <= t).mean()), 3) for h, m in masks.items()
        }
        res["lines"][key]["gray"] = [int(caught[eps].sum()), len(eps)]
        res["lines"][key]["kinds"] = kinds
        sp = {}
        for d in range(pdm.N_DIMS):
            dd = syn.day_min(w, np.r_[qd[:, d] / wts[d], np.full(n_msg, np.inf)])
            sp[names[d]] = {"share": round(100 * t * wts[d], 3)} | {
                h: round(100 * float((dd[m] <= t).mean()), 3) for h, m in masks.items()
            }
        res["spend"][key] = sp
    prim = pdm.neglog(np.r_[out.p_final, out.msg_p])
    sec = pdm.neglog(np.r_[out.q2, out.msg_q2])
    res["oracle_matched_ROC_points"] = {
        k: {"benign": round(100 * x["benign"], 3), "gray": x["gray"]}
        for k, x in syn.matched(w, agent_row, prim, sec).items()
    }
    return res


def run_world(npz: Path) -> dict:
    """All four arms on one world."""
    t0 = time.time()
    pdm.hour_gap_rate = lambda v, a1: np.full(len(v.agent), np.inf)  # option not used here
    v = pdm.load_vectors(npz)
    st1 = pdm.stage1(v)
    v.magnitude[syn.OVERSIZED] = syn.rf1_magnitude(npz, v)
    rf1_q = pdm.org_flag_rate(v, syn.OVERSIZED)
    q_days = syn.stage1_variant(v, st1, "days")
    w, agent_row = syn.day_groups(npz)
    names = [d["paper_name"] for d in v.meta["dimensions"]]
    arms, activity = build_arms(v, st1, q_days)
    res = {
        "world": npz.stem,
        "caveat": "DEVELOPMENT WORLD; v4 score vectors, arm S5 code path",
        "activity": {names[d]: a for d, a in activity.items()},
        "arms": {},
    }
    for name, (qd, wts) in arms.items():
        out, qd2 = run_arm(v, st1, qd, wts, rf1_q, surge=name == "O3")
        res["arms"][name] = summarise(w, agent_row, out, qd2, wts, names)
        print(f"{npz.stem}: {name} at {time.time() - t0:.0f}s", flush=True)
    return res


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("npz", nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.write_text(json.dumps([run_world(p) for p in args.npz], default=ce._jsonable))


if __name__ == "__main__":
    main()
