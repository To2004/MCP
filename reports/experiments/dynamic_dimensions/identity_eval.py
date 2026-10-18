"""Identity test, evaluation: how much detection depends on knowing WHO sends each call.

Same traffic, three identities (see identity_variants.py): one token per person, one token shared
by 10 people, and no stable identity (each session a stranger). For each, reports detection of the
cross-scenario set chosen with per-person identity, and of the best set re-chosen for that identity.

Run:  python identity_eval.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ablation import greedy
from eval2 import Scenario

HERE = Path(__file__).parent
BASE = Path("/home/ovadyat/MCP/runs/dynamic_dimensions/w2")
VAR = Path("/home/ovadyat/MCP/runs/dynamic_dimensions/w2id")
NAMES = ["calendar_M", "slack_M", "github_M"]


def main():
    res = json.load(open(HERE / "results" / "eval2.json"))
    chosen = {load: [c for c, _ in res["global"][load]] for load in ("2.0", "4.0")}
    out = {}
    for variant, path_of in (("one token per person", lambda n: BASE / f"{n}.compact.npz"),
                             ("one token shared by 10 people", lambda n: VAR / f"{n}__shared10.compact.npz"),
                             ("no stable identity (per session)", lambda n: VAR / f"{n}__session.compact.npz")):
        scens = [Scenario.load(path_of(n)) for n in NAMES if path_of(n).exists()]
        if not scens:
            continue
        row = {}
        for load in ("2.0", "4.0"):
            L = float(load)
            fixed = [[s.cols.index(c) for c in chosen[load]] for s in scens]
            dets = [s.detect(ix, L) for s, ix in zip(scens, fixed)]
            per_kind = {}
            for d in dets:
                for k, v in d[2].items():
                    per_kind.setdefault(k, []).append(v)
            best_set, best_m = greedy(scens, scens[0].cols, L, 10)
            row[load] = {"fixed set": float(np.mean([d[0] for d in dets])),
                         "re-chosen set": best_m, "re-chosen": best_set,
                         "per kind (fixed set)": {k: float(np.mean(v)) for k, v in per_kind.items()}}
        out[variant] = row
        print(f"{variant:<36} load 2: fixed {row['2.0']['fixed set']:.0%} best {row['2.0']['re-chosen set']:.0%} | "
              f"load 4: fixed {row['4.0']['fixed set']:.0%} best {row['4.0']['re-chosen set']:.0%}", flush=True)
    (HERE / "results" / "identity.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
