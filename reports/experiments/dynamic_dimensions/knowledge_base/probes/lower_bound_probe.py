"""Lower-bound probe: what does M's floor of 0.7 do, and what would M >= 1 change?

Design-v5 question (improvement option f2, claim C8): keep v4's bottom of x0.7, set M >= 1 for
"consequential" calls only (writes, or a cell of static level 4 or more), or set M >= 1 for every
call. The probe reads the per-call vectors that ``dump_vectors.py`` saved (v4 engine, unchanged)
and recomputes each arm offline; M feeds nothing back into the engine's state, so this is exact.

Arms (``M`` is v4's multiplier; ``s2`` its runner-up; non-call messages enter the day maximum):

- ``v4``: M as shipped, bottom x0.7;
- ``floor on consequential``: max(M, 1) on writes and on calls whose asset has sensitivity >= 4
  (the simulator's static score is a per-tool level in {2, 3, 4}, with 4 = write, so
  "static level >= 4" per (tool, asset) cell is approximated by "write or sensitivity >= 4");
- ``floor on every call``: max(M, 1) on every message.

Reports, per world: the share of scored calls with M < 1 (all, writes, sensitivity >= 4, gray
episode calls), the mean M among them, whether any x3 alert changes (it cannot), how many days have
fewer than k agent-days with a day maximum above 1 (the only way a review list can change), and
the shared evaluator's metrics for each arm.

Every number is a DEVELOPMENT-WORLD number (seeds 7 and 11 were used to design v1-v4).

Run (numpy only):
    python3 reports/experiments/dynamic_dimensions/knowledge_base/probes/lower_bound_probe.py \
        <scratchpad>/v5_vectors/main_seed7.npz <scratchpad>/v5_vectors/main_seed11.npz
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calib_eval  # noqa: E402 — the shared evaluator lives next to this file

WRITE_OP = 1  # sidecar "operations": read 0, write 1, metadata 2
SENSITIVE = 4  # sensitivity at or above which a cell counts as consequential here
ALERT = 3.0
FLOOR = 1.0
LIST_SIZES = (4, 8)
#: the evaluator metrics this probe reports (prefixes of ``calib_eval.simulator_view`` keys)
KEPT_METRICS = ("ordinary_days_x3", "gray_caught_x3", "review.")


def arms(c: dict) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Each arm's per-call and per-message multiplier."""
    m, msg_m = c["M"].astype(np.float64), c["msg_M"].astype(np.float64)
    consequential = (c["op"] == WRITE_OP) | (c["sens"] >= SENSITIVE)
    return {
        "v4": (m, msg_m),
        "floor on consequential": (np.where(consequential, np.maximum(m, FLOOR), m), msg_m),
        "floor on every call": (np.maximum(m, FLOOR), np.maximum(msg_m, FLOOR)),
    }


def share_below(m: np.ndarray, mask: np.ndarray) -> dict:
    """Share of the masked calls with M < 1, and their mean M."""
    sel = m[mask]
    below = sel[sel < FLOOR]
    return {
        "calls": int(sel.size),
        "share_M_below_1": round(float(below.size / max(1, sel.size)), 4),
        "mean_M_when_below_1": round(float(below.mean()), 3) if below.size else None,
    }


def thin_days(c: dict, m: np.ndarray, msg_m: np.ndarray, scored_from: int) -> dict:
    """Days on which fewer than k agent-days have a day maximum above 1 (list could change)."""
    keys = np.concatenate([
        c["day"].astype(np.int64) * 100_000 + c["agent"],
        c["msg_day"].astype(np.int64) * 100_000 + c["msg_agent"],
    ])
    vals = np.concatenate([m, msg_m])
    keep = keys // 100_000 >= scored_from
    keys, vals = keys[keep], vals[keep]
    order = np.argsort(keys, kind="stable")
    keys, vals = keys[order], vals[order]
    starts = np.flatnonzero(np.r_[True, keys[1:] != keys[:-1]])
    day_max = np.maximum.reduceat(vals, starts)
    day_of = keys[starts] // 100_000
    out = {}
    for k in LIST_SIZES:
        above = np.bincount(day_of[day_max > FLOOR] - scored_from,
                            minlength=int(day_of.max() - scored_from + 1))
        out[f"days_with_fewer_than_{k}_above_1"] = int((above < k).sum())
    out["days"] = int(np.unique(day_of).size)
    return out


def probe(npz_path: Path) -> dict:
    """All measurements for one world."""
    c = dict(np.load(npz_path))
    scored = c["day"] >= calib_eval.EVAL_FROM_DAY
    v4 = c["M"].astype(np.float64)
    masks = {
        "all scored calls": scored,
        "writes": scored & (c["op"] == WRITE_OP),
        "sensitivity >= 4": scored & (c["sens"] >= SENSITIVE),
        "gray-episode calls": scored & (c["episode"] >= 0),
        "gray-episode writes": scored & (c["episode"] >= 0) & (c["op"] == WRITE_OP),
    }
    result = {"world": npz_path.stem, "caveat": "development world, not a test result"}
    result["below_1_under_v4"] = {name: share_below(v4, mask) for name, mask in masks.items()}
    result["arms"] = {}
    s2 = c["s2"].astype(np.float64)
    for name, (m, msg_m) in arms(c).items():
        changed_alerts = int(((m >= ALERT) != (v4 >= ALERT)).sum())
        res = calib_eval.evaluate(
            npz_path, m, s2, c["dstar"], name=name,
            msg_primary=msg_m, msg_secondary=c["msg_s2"], msg_dstar=c["msg_dstar"],
            fixed_lines={"x3": ALERT},
        )
        view = calib_eval.simulator_view(res)
        result["arms"][name] = {
            "alerts_changed_vs_v4": changed_alerts,
            "thin_list_days": thin_days(c, m, msg_m, calib_eval.EVAL_FROM_DAY),
            "evaluator": {k: v for k, v in view.items() if k.startswith(KEPT_METRICS)},
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("npz", nargs="+", type=Path)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    out = [probe(p) for p in args.npz]
    text = json.dumps(out, indent=1)
    print(text)
    if args.json:
        args.json.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
