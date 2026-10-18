"""Evaluate the dimension pool across scenarios: alone, greedily within each scenario, and as
one set chosen to work across ALL scenarios at once.

Label-free throughout: each dimension's score is ranked against the previous 30 days of all
messages; a risk event is rank >= EVENT_RANK; events add up per agent-day; an agent-day alerts
when >= 2 dimensions agree above T bits, or one event is above B bits. (T, B) is swept and
detection is read at <= LOAD alerted agent-days per day, after the first month.

Run:  python eval2.py --scores-dir ../../../runs/dynamic_dimensions/w2 --scenarios github_M calendar_M ...
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

CAL_DAYS, EVENT_RANK, SINGLE_RANK, MIN_RAW = 30, 0.995, 0.998, 1e-6
GRID = [(T, B) for T in (8, 10, 12, 14, 18, 24, 32, 45, 60, 80) for B in (11, 13, 15, 99)]
LEGIT = ["new_hire", "back_from_vacation", "client_upgrade", "redeploy", "new_network", "team_transfer", "role_change", "night_work"]


COMPACT = ("cd", "kday", "ep_kind", "ep_int", "ep_day", "ep_ev", "ep_single", "ep_cds", "ep_ptr", "after")


class Scenario:
    @classmethod
    def load(cls, path: Path):
        """A prepared (compact) scenario: everything detect() needs, nothing per message."""
        z = np.load(path, allow_pickle=True)
        s = cls.__new__(cls)
        s.name, s.cols = path.stem.replace(".compact", ""), list(z["cols"])
        for k in COMPACT:
            setattr(s, k, z[k])
        s.n_eval_days = int(z["n_eval_days"])
        s.single_metrics = json.loads(str(z["single"]))
        return s

    def save(self, path: Path):
        np.savez_compressed(path, cols=np.array(self.cols), n_eval_days=self.n_eval_days,
                            single=json.dumps(self.single(), default=float),
                            **{k: getattr(self, k) for k in COMPACT})

    def __init__(self, path: Path):
        z = np.load(path)
        self.name = path.stem
        self.S = z["scores"]
        self.cols = list(z["cols"])
        for suffix in ("_x", "_h", "_p", "_q"):                           # extra feature batches, same rows
            extra = path.with_name(path.stem + suffix + ".npz")
            if extra.exists():
                x = np.load(extra)
                assert x["scores"].shape[0] == self.S.shape[0], "feature batches are not aligned"
                self.S = np.concatenate([self.S, x["scores"]], 1)
                self.cols += list(x["cols"])
        self.day = (z["ts"].astype(float) // 86400).astype(int)
        self.agent = z["agent"].astype(str)
        self.strange, self.legit = z["strange"].astype(str), z["legit"].astype(str)
        self.episode, self.intensity = z["episode"].astype(str), z["intensity"].astype(int)
        self.benign = self.strange == ""
        self.ndays = self.day.max() + 1
        self.day_idx = [np.flatnonzero(self.day == d) for d in range(self.ndays)]
        self.R = self._ranks()
        keys = np.char.add(np.char.add(self.agent, "|"), self.day.astype(str))
        _, self.inv = np.unique(keys, return_inverse=True)
        nk = self.inv.max() + 1
        self.kday = np.zeros(nk, int)
        self.kday[self.inv] = self.day
        ev = self.R >= EVENT_RANK
        bits = np.where(ev, -np.log2(np.clip(1 - self.R, 1e-6, 1)), 0.0).astype(np.float32)
        self.cd = np.zeros((nk, len(self.cols)), np.float32)
        np.maximum.at(self.cd, self.inv, bits)
        eps = defaultdict(list)
        for i in np.flatnonzero(~self.benign):
            eps[self.episode[i]].append(i)
        self.ep_names = list(eps)
        self.ep_kind = np.array([self.strange[eps[e][0]] for e in self.ep_names])
        self.ep_int = np.array([self.intensity[eps[e][0]] for e in self.ep_names])
        self.ep_day = np.array([self.day[eps[e][0]] for e in self.ep_names])
        self.ep_ev = np.zeros((len(self.ep_names), len(self.cols)), bool)
        self.ep_single = np.zeros_like(self.ep_ev)
        cds, ptr = [], [0]
        for j, e in enumerate(self.ep_names):
            ix = np.array(eps[e])
            self.ep_ev[j] = ev[ix].any(0)
            self.ep_single[j] = (self.R[ix] >= SINGLE_RANK).any(0)
            u = np.unique(self.inv[ix])
            cds.extend(u)
            ptr.append(len(cds))
        self.ep_cds, self.ep_ptr = np.array(cds), np.array(ptr)
        self.after = self.ep_day >= CAL_DAYS
        self.n_eval_days = max(1, self.ndays - CAL_DAYS)

    def _ranks(self):
        R = np.zeros(self.S.shape, np.float32)
        for d in range(1, self.ndays):
            past = np.concatenate(self.day_idx[max(0, d - CAL_DAYS):d])
            idx = self.day_idx[d]
            if not len(past) or not len(idx):
                continue
            P = np.sort(self.S[past], axis=0)
            for j in range(self.S.shape[1]):
                x = self.S[idx, j]
                R[idx, j] = np.searchsorted(P[:, j], x, side="left") / len(past) * (x > MIN_RAW)
        return R

    def detect(self, cols, load):
        """Best detection (mean over kinds) at <= load alerted agent-days/day, after month 1."""
        C = self.cd[:, cols]
        S, D, top = C.sum(1), (C > 0).sum(1), C.max(1)
        credit = self.ep_ev[:, cols].any(1)
        in_eval = self.kday >= CAL_DAYS
        best = None
        for T, B in GRID:
            al = ((S >= T) & (D >= 2)) | (top >= B)
            ld = (al & in_eval).sum() / self.n_eval_days
            if ld > load:
                continue
            hit = np.logical_or.reduceat(al[self.ep_cds], self.ep_ptr[:-1]) & credit & self.after
            per = {k: hit[(self.ep_kind == k) & self.after].mean() for k in np.unique(self.ep_kind[self.after])}
            m = float(np.mean(list(per.values())))
            if best is None or m > best[0]:
                best = (m, ld, per, hit)
        return best or (0.0, 0.0, {}, np.zeros(len(self.ep_names), bool))

    def single(self):
        """Each dimension alone: share of episodes with a top-0.2% event, per kind; benign rate."""
        out = {}
        for j, c in enumerate(self.cols):
            ev = self.R[:, j] >= SINGLE_RANK
            row = {"benign": float(ev[self.benign].mean())}
            for k in np.unique(self.ep_kind):
                m = (self.ep_kind == k) & self.after
                row[k] = float(self.ep_single[m, j].mean()) if m.any() else float("nan")
            for tag in LEGIT:
                mm = self.benign & (self.legit == tag)
                row["FP:" + tag] = float(ev[mm].mean()) if mm.any() else float("nan")
            out[c] = row
        return out


def greedy(scens, load, steps, pool):
    chosen, trail = [], []
    for _ in range(steps):
        best = None
        for c in pool:
            if c in chosen:
                continue
            idx = [[s.cols.index(x) for x in chosen + [c]] for s in scens]
            m = float(np.mean([s.detect(ix, load)[0] for s, ix in zip(scens, idx)]))
            if best is None or m > best[1]:
                best = (c, m)
        chosen.append(best[0])
        trail.append(best)
        print(f"  + {best[0]:<24} {best[1]:.1%}", flush=True)
    return trail


def prep(npz: Path, out: Path):
    s = Scenario(npz)
    s.save(out)
    print(f"prepared {npz.stem}: {len(s.ep_names)} episodes", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep", type=Path, help="prepare one scenario's .npz into a compact file and exit")
    ap.add_argument("--scores-dir", type=Path, required=True)
    ap.add_argument("--scenarios", nargs="*", default=[])
    ap.add_argument("--load", type=float, default=2.0)
    ap.add_argument("--steps", type=int, default=14)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results" / "eval2.json")
    a = ap.parse_args()
    if a.prep:
        prep(a.prep, a.prep.with_suffix(".compact.npz"))
        return
    scens = [Scenario.load(a.scores_dir / f"{n}.compact.npz") for n in a.scenarios]
    pool = scens[0].cols
    res = {"single": {s.name: s.single_metrics for s in scens}, "per_scenario": {}, "global": {}}
    for s in scens:
        print(f"greedy within {s.name}", flush=True)
        res["per_scenario"][s.name] = greedy([s], a.load, 10, pool)
    for load in (a.load, 2 * a.load):
        print(f"global greedy, load <= {load}", flush=True)
        trail = greedy(scens, load, a.steps, pool)
        res["global"][str(load)] = trail
        final = [scens[0].cols.index(c) for c, _ in trail]
        res["global"][f"{load}_per_kind"] = {s.name: {k: float(v) for k, v in s.detect(
            [s.cols.index(c) for c, _ in trail], load)[2].items()} for s in scens}
        res["global"][f"{load}_curve"] = [(c, m) for c, m in trail]
        by_int = defaultdict(list)                      # kind x intensity for the chosen set
        for s in scens:
            hit = s.detect([s.cols.index(c) for c, _ in trail], load)[3]
            for k in np.unique(s.ep_kind):
                for i in (1, 2, 3):
                    m = (s.ep_kind == k) & (s.ep_int == i) & s.after
                    if m.any():
                        by_int[f"{k}|{i}"].append(float(hit[m].mean()))
        res["global"][f"{load}_by_intensity"] = {k: float(np.mean(v)) for k, v in by_int.items()}
    a.out.write_text(json.dumps(res, indent=1, default=float))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
