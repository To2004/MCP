"""Offline probe: replace session duration by a per-caller "spell" (calls ended by an idle gap).

Reads the per-call v4 score vectors that ``dump_vectors.py`` saved for one DEVELOPMENT WORLD
(seed 7, main profile) and, without re-running the engine, measures:

1. inter-call gaps per caller (bots and people apart), to choose the idle gap G;
2. a "spell duration" arm: minutes since the caller's current spell began, scored with the
   engine's excess formula ``(v + u) / (v + u + 2 (usual + u))``, u = 1 minute, usual = his
   call-weighted mean over days [d-89, d-1] (``memory.DailyMean`` with ``daily=True``);
3. the v4 multiplier with session duration swapped for spell duration (every other score as
   logged), as ordinary/change agent-day alert rates and gray-episode catches at x3;
4. the "merge with no review" step scoped to the spell, or to a fixed time window, instead of
   the session.

M feeds nothing back into the engine's state (``engine.py:281-299``), so swapping one
dimension's score offline gives exactly the multiplier the engine would give.

DEVELOPMENT WORLD: seed 7 was used to design v1-v4. No number printed here is a test result.

    python3 reports/experiments/dynamic_dimensions/knowledge_base/probes/spell_probe.py \
        --npz <scratchpad>/v5_vectors/main_seed7.npz --out <scratchpad>/v5_vectors/spell_probe.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

EVAL_FROM = 90  # normal_org_sim.py: EVAL_FROM
HISTORY_DAYS = 90
ALERT = 3.0
S_AT_ALERT = 0.5 * (1 + math.log(ALERT) / math.log(5.0))  # M = 5^(2s-1) = 3
TOLERANCE, MINUTE_UNIT = 2.0, 1.0
GAPS_MIN = (10, 20, 30, 60)
WINDOWS_MIN = (60, 24 * 60)
REVIEW_TOOLS = ("get_pull_request", "get_pull_request_reviews", "get_pull_request_status")
DIMS = (
    "calls_last_hour writes_last_hour assets_last_hour same_call_10m session_length time_of_day "
    "tool asset network client burst many_assets request_too_big sequence protocol_skip"
).split()


def multiplier(s: np.ndarray) -> np.ndarray:
    """engine.multiplier, vectorised; NaN (nothing took part) -> 1."""
    m = np.where(s >= 0.5, 5.0 ** (2 * s - 1), 0.7 ** (1 - 2 * s))
    return np.where(np.isnan(s), 1.0, m)


def spell_minutes(ts: np.ndarray, agent: np.ndarray, gap_s: float) -> np.ndarray:
    """Minutes since the caller's current spell began (rows sorted by agent, then ts)."""
    new_agent = np.r_[True, agent[1:] != agent[:-1]]
    gaps = np.r_[np.inf, np.diff(ts)]
    starts = new_agent | (gaps > gap_s)
    start_ts = pd.Series(np.where(starts, ts, np.nan)).ffill().to_numpy()
    return (ts - start_ts) / 60.0


def usual_up_to_yesterday(values: np.ndarray, agent: np.ndarray, day: np.ndarray) -> np.ndarray:
    """His call-weighted mean of ``values`` over days [d-89, d-1]; NaN with no history."""
    frame = pd.DataFrame({"a": agent, "d": day, "v": values})
    daily = frame.groupby(["a", "d"])["v"].agg(["sum", "count"])
    n_days = int(day.max()) + 1
    out = np.full(len(values), np.nan)
    for a, block in daily.groupby(level=0):
        sums = np.zeros(n_days + 1)
        counts = np.zeros(n_days + 1)
        days = block.index.get_level_values(1).to_numpy()
        sums[days + 1] = block["sum"].to_numpy()
        counts[days + 1] = block["count"].to_numpy()
        cs, cc = np.cumsum(sums), np.cumsum(counts)
        rows = np.flatnonzero(agent == a)
        d = day[rows]
        lo = np.maximum(d - HISTORY_DAYS + 1, 0)
        total = cs[d] - cs[lo]
        n = cc[d] - cc[lo]
        out[rows] = np.where(n > 0, total / np.maximum(n, 1), np.nan)
    return out


def excess(value: np.ndarray, usual: np.ndarray) -> np.ndarray:
    u = MINUTE_UNIT
    return (value + u) / (value + u + TOLERANCE * (usual + u))


def day_classes(df: pd.DataFrame) -> pd.Series:
    """Agent-day class as the simulator labels it: gray > change > ordinary."""
    worst = df.groupby(["agent", "day"])["label_kind"].max()
    return worst.map({0: "ordinary", 1: "change", 2: "gray"})


def alert_rates(df: pd.DataFrame, m_col: str, msg_day_max: pd.Series, classes: pd.Series) -> dict:
    day_max = df.groupby(["agent", "day"])[m_col].max()
    day_max = pd.concat([day_max, msg_day_max], axis=1).max(axis=1).reindex(classes.index)
    out = {}
    for name in ("ordinary", "change"):
        sel = classes == name
        out[f"{name}_agent_days"] = int(sel.sum())
        out[f"{name}_alert_rate_pct"] = round(100 * float((day_max[sel] >= ALERT).mean()), 3)
    return out


def episode_catch(df: pd.DataFrame, m_col: str, kinds: list[str], ep_kind: np.ndarray) -> dict:
    gray = df[df.episode >= 0]
    caught = gray.groupby("episode")[m_col].max() >= ALERT
    by_kind: dict[str, list[int]] = {}
    for ep, hit in caught.items():
        kind = kinds[int(ep_kind[ep])]
        tally = by_kind.setdefault(kind, [0, 0])
        tally[0] += int(hit)
        tally[1] += 1
    total = [sum(v[0] for v in by_kind.values()), sum(v[1] for v in by_kind.values())]
    return {"all": total, **{k: by_kind[k] for k in sorted(by_kind)}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--npz", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    meta = json.loads(args.npz.with_suffix(".json").read_text())
    z = np.load(args.npz)
    cols = ["agent", "day", "ts", "label_kind", "episode", "warm", "is_bot", "tool", "M"]
    df = pd.DataFrame({c: z[c] for c in cols})
    for d in DIMS:
        df[f"s_{d}"] = z[f"s_{d}"].astype(np.float64)
    df["raw_sequence"] = z["raw_sequence"].astype(np.float64)
    df = df.sort_values(["agent", "ts"], kind="stable").reset_index(drop=True)
    agent, ts, day = df.agent.to_numpy(), df.ts.to_numpy(), df.day.to_numpy()
    tools = meta["tools"]

    # 1. inter-call gaps
    same = np.r_[False, agent[1:] == agent[:-1]]
    gaps_min = np.where(same, np.r_[np.nan, np.diff(ts)] / 60.0, np.nan)
    gap_report = {}
    for who, mask in (("bots", df.is_bot == 1), ("people", df.is_bot == 0)):
        g = gaps_min[mask.to_numpy() & ~np.isnan(gaps_min)]
        gap_report[who] = {
            "gaps": int(g.size),
            "quantiles_min": {
                q: round(float(np.quantile(g, q)), 2) for q in (0.5, 0.9, 0.95, 0.99)
            },
            "share_over_G_pct": {G: round(100 * float((g > G).mean()), 3) for G in GAPS_MIN},
        }

    # 3. v4 as logged, and v4 with session duration swapped for spell duration
    others = df[[f"s_{d}" for d in DIMS if d != "session_length"]].to_numpy()
    s_others = np.where(np.isnan(others).all(axis=1), np.nan, np.nanmax(
        np.where(np.isnan(others), -np.inf, others), axis=1))
    s_others = np.where(np.isinf(s_others), np.nan, s_others)
    df["M_v4_check"] = multiplier(np.fmax(s_others, df.s_session_length.to_numpy()))
    df["M_no_duration"] = multiplier(s_others)
    msg = pd.DataFrame({"agent": z["msg_agent"], "day": z["msg_day"], "M": z["msg_M"]})
    msg_day_max = msg.groupby(["agent", "day"])["M"].max()
    evald = df[df.day >= EVAL_FROM]
    classes = day_classes(evald)
    kinds, ep_kind = meta["kinds"], z["ep_kind"]
    warm = df.warm.to_numpy() == 1
    report = {
        "caveat": meta["caveat"],
        "world": meta["world"],
        "s_at_alert": round(S_AT_ALERT, 4),
        "gaps": gap_report,
        "max_abs_err_M_recomputed": float(np.max(np.abs(df.M_v4_check - df.M))),
        "v4_as_logged": alert_rates(evald, "M", msg_day_max, classes)
        | {"episodes_caught": episode_catch(evald, "M", kinds, ep_kind)},
        "v4_without_duration": alert_rates(evald, "M_no_duration", msg_day_max, classes)
        | {"episodes_caught": episode_catch(evald, "M_no_duration", kinds, ep_kind)},
    }
    sess = evald.s_session_length.to_numpy()
    report["session_duration_alone_over_x3"] = alert_rates(
        evald.assign(x=multiplier(sess)), "x", msg_day_max * 0, classes
    )
    arms = {}
    for G in GAPS_MIN:
        minutes = spell_minutes(ts, agent, G * 60.0)
        usual = usual_up_to_yesterday(minutes, agent, day)
        s_spell = np.where(warm & ~np.isnan(usual), excess(minutes, usual), np.nan)
        df[f"M_spell{G}"] = multiplier(np.fmax(s_others, s_spell))
        df[f"x_spell{G}"] = multiplier(s_spell)
        ev = df[df.day >= EVAL_FROM]
        arms[f"G={G}min"] = {
            "spell_alone_over_x3": alert_rates(ev, f"x_spell{G}", msg_day_max * 0, classes),
            "v4_with_spell": alert_rates(ev, f"M_spell{G}", msg_day_max, classes)
            | {"episodes_caught": episode_catch(ev, f"M_spell{G}", kinds, ep_kind)},
        }
    report["spell_arms"] = arms

    # 4. merge with no review, scoped to spell or time window
    merge, review = tools.index("merge_pull_request"), [tools.index(t) for t in REVIEW_TOOLS]
    is_merge = (df.tool == merge).to_numpy()
    is_review = np.isin(df.tool.to_numpy(), review)
    last_review = pd.Series(np.where(is_review, ts, np.nan)).groupby(agent).ffill().to_numpy()
    # last review strictly before this call (a merge is never a review, so ffill is safe)
    seq_rep = {"merges_eval": int((is_merge & (day >= EVAL_FROM)).sum())}
    v4_raw = df.raw_sequence.to_numpy()
    ev_merge = is_merge & (day >= EVAL_FROM)
    seq_rep["v4_sequence_raised_on_merges_pct"] = round(
        100 * float((~np.isnan(v4_raw[ev_merge])).mean()), 3
    )
    for G in GAPS_MIN:
        minutes = spell_minutes(ts, agent, G * 60.0)
        spell_start = ts - minutes * 60.0
        ok = last_review >= spell_start
        seq_rep[f"no_review_in_spell_G={G}min_pct"] = round(
            100 * float((~ok[ev_merge]).mean()), 3)
    for W in WINDOWS_MIN:
        ok = ts - last_review <= W * 60.0
        seq_rep[f"no_review_in_last_{W}min_pct"] = round(100 * float((~ok[ev_merge]).mean()), 3)
    report["merge_review"] = seq_rep

    args.out.write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
