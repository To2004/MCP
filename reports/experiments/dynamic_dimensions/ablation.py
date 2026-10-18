"""Which log fields does the dynamic layer really need? Field ablation over the 9 prepared scenarios.

Each dimension is mapped to the log fields it reads. For each field set, the cross-scenario greedy
selection is rerun using only the dimensions that field set allows, and detection is reported at
<= 2 and <= 4 alerted agent-days per day.

Field groups:
  ENV     agent id, session id, timestamp, MCP method, tool name (+ the static scan's tool operation)
  WIRE    client address, client name/version, user agent
  KEYS    the names of the arguments a call passes (no values)
  BYTES   request size in bytes
  HASH    a hash of the full arguments (equality only: "same call again")
  VALUES  the values of the inputs the static scan keeps (which / how_much / who / when / action)

Run:  python ablation.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from eval2 import Scenario

D = Path("/home/ovadyat/MCP/runs/dynamic_dimensions/w2")
NAMES = ["github_M", "calendar_M", "slack_M", "github_S", "calendar_L", "slack_churn", "github_bots",
         "calendar_M2", "slack_M2"]
NEEDS = {
    "identical_10m": {"HASH"}, "identical_in_session": {"HASH"}, "retry_after_cancel": {"HASH"},
    "reach_today": {"VALUES"}, "how_much_value": {"VALUES"}, "when_span": {"VALUES"}, "who_count": {"VALUES"},
    "who_new": {"VALUES"}, "distinct_who_day": {"VALUES"}, "action_value_new": {"VALUES"},
    "arg_keys_new": {"KEYS"}, "request_bytes": {"BYTES"},
    "address_new": {"WIRE"}, "addresses_1h": {"WIRE"}, "client_new": {"WIRE"}, "user_agent_new": {"WIRE"},
    "addresses_in_session": {"WIRE"}, "non_dominant_client": {"WIRE"}, "client_context": {"WIRE"},
}
for d in ("which_new", "which_new_peer_rare", "which_new_org_rare", "which_per_session", "which_per_day",
          "sens_above_own_max", "tool_asset_pair_new", "asset_entropy_1h", "unpopular_share_day",
          "new_edges_today", "cusum_new_edges", "low_revisit", "monotone_run", "scope_shift_week"):
    NEEDS[d] = {"VALUES"}
SETS = {
    "everything": {"ENV", "WIRE", "KEYS", "BYTES", "HASH", "VALUES"},
    "no wire fields": {"ENV", "KEYS", "BYTES", "HASH", "VALUES"},
    "no argument values (keys + bytes + hash only)": {"ENV", "WIRE", "KEYS", "BYTES", "HASH"},
    "envelope + wire only": {"ENV", "WIRE"},
    "envelope only": {"ENV"},
}


def greedy(scens, pool, load, steps):
    chosen, best_m = [], 0.0
    for _ in range(steps):
        cand = None
        for c in pool:
            if c in chosen:
                continue
            m = float(np.mean([s.detect([s.cols.index(x) for x in chosen + [c]], load)[0] for s in scens]))
            if cand is None or m > cand[1]:
                cand = (c, m)
        if cand is None or cand[1] <= best_m + 0.002:
            break
        chosen.append(cand[0])
        best_m = cand[1]
    return chosen, best_m


def main():
    scens = [Scenario.load(D / f"{n}.compact.npz") for n in NAMES]
    cols = scens[0].cols
    out = {}
    for name, fields in SETS.items():
        pool = [c for c in cols if NEEDS.get(c, {"ENV"}) <= fields]
        row = {"dimensions available": len(pool)}
        for load in (2.0, 4.0):
            chosen, m = greedy(scens, pool, load, 10)
            row[f"load {load:g}"] = {"detection": m, "chosen": chosen}
        out[name] = row
        print(f"{name:<48} {len(pool):>3} dims | load 2: {row['load 2']['detection']:.0%} | "
              f"load 4: {row['load 4']['detection']:.0%}", flush=True)
    Path(__file__).with_name("results").joinpath("ablation.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
