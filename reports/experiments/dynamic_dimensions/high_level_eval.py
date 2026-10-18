"""High-level dimension search: the same tests as before, without looking inside any call.

Pools:
  A  tool, operation type, asset type (from the tool name), time, volume, sessions, protocol
     messages + client software family, user-agent family and /16 network range
  B  pool A without any client or network field
Reference: the exact-content result from eval2.json (reads asset names and argument names/values).

For each pool: greedy selection across the 9 scenarios at <= 2 and <= 4 flagged agent-days per day,
detection by kind and intensity, the best single dimension per kind, and false alarms on
legitimate change. Writes results/high_level.md and results/high_level.json.

Run:  python high_level_eval.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from ablation import greedy
from eval2 import Scenario

HERE = Path(__file__).parent
D = Path("/home/ovadyat/MCP/runs/dynamic_dimensions/w2")
NAMES = ["github_M", "calendar_M", "slack_M", "github_S", "calendar_L", "slack_churn", "github_bots",
         "calendar_M2", "slack_M2"]
TOOL_TIME = ["rate_1m", "rate_10m", "rate_1h", "calls_today", "sessions_1h", "burstiness_cv", "next_tool_self",
             "next_tool_trigram", "op_transition", "write_first", "session_length", "hour_of_week", "dormancy",
             "parallel_sessions", "inits_1h", "cancels_1h", "tool_mix_shift_week", "fano_1h", "gap_memory",
             "tool_entropy_1h", "cusum_calls", "list_to_call_delay", "non_call_share",
             "asset_type_new", "asset_type_new_org_rare", "asset_types_today", "tool_new_org_rare", "writes_today",
             "removes_today", "impact_sum_today", "distinct_tools_today", "tool_repeat_10m", "tool_repeat_in_session",
             "call_without_list", "call_without_init", "tool_recency_gap", "op_escalation_session", "read_to_write_fast",
             "session_tool_diversity", "session_duration", "write_share_today", "tool_periodicity",
             "peer_deviation_week", "tool_new_tool_peer_rare",
             "session_count_distance", "session_pattern_rarity", "peer_next_tool", "pair_gap_unusual", "tool_rate_1m"]
GENERAL_CLIENT = ["client_family_new", "ua_family_new", "network_range_new", "networks_in_session", "networks_1h",
                  "client_families_1h", "context_new_on_write", "shared_session_rule"]
POOLS = {"A: tool + time + volume + general client/network": TOOL_TIME + GENERAL_CLIENT,
         "B: tool + time + volume only": TOOL_TIME}


def by_kind(scens, cols, load):
    per, by_int = defaultdict(list), defaultdict(list)
    for s in scens:
        _, _, kinds, hit = s.detect([s.cols.index(c) for c in cols], load)
        for k, v in kinds.items():
            per[k].append(v)
        for k in np.unique(s.ep_kind):
            for i in (1, 2, 3):
                m = (s.ep_kind == k) & (s.ep_int == i) & s.after
                if m.any():
                    by_int[(k, i)].append(float(hit[m].mean()))
    return {k: float(np.mean(v)) for k, v in per.items()}, {f"{k}|{i}": float(np.mean(v)) for (k, i), v in by_int.items()}


def main():
    scens = [Scenario.load(D / f"{n}.compact.npz") for n in NAMES]
    missing = [c for c in TOOL_TIME + GENERAL_CLIENT if c not in scens[0].cols]
    assert not missing, f"missing columns: {missing}"
    ref = json.load(open(HERE / "results" / "eval2.json"))
    out = {"reference_exact": {L: ref["global"][L][-1][1] for L in ("2.0", "4.0")}}
    md = ["# High-level dimensions: no look inside any call\n",
          "Same 9 organisations, 21 kinds of strange usage and scoring as the exact-content search. The "
          "dimensions here never read tool inputs or the specific asset: only which tool, its operation, the "
          "asset TYPE implied by the tool, time, volume, sessions, and (pool A) a general client and network.\n"]
    for pool, cols in POOLS.items():
        res = {}
        md.append(f"## Pool {pool}\n")
        for load in (2.0, 4.0):
            chosen, m = greedy(scens, cols, load, 12)
            kinds, ints = by_kind(scens, chosen, load)
            res[str(load)] = {"detection": m, "chosen": chosen, "per_kind": kinds, "by_intensity": ints}
            md += [f"### At <= {load:g} flagged agent-days per day: {m:.0%} "
                   f"(exact-content reference {out['reference_exact'][str(load)]:.0%})\n",
                   "Chosen, in order: " + ", ".join(chosen) + "\n",
                   "| kind | mild | medium | strong |", "|---|---|---|---|"]
            for k in sorted(kinds):
                md.append(f"| {k} | " + " | ".join(f"{ints[f'{k}|{i}']:.0%}" if f"{k}|{i}" in ints else "–"
                                                   for i in (1, 2, 3)) + " |")
            md.append("")
        out[pool] = res
    # best single high-level dimension per kind, and false alarms
    single = {s.name: s.single_metrics for s in scens}
    kinds = sorted({k for s in single for k in single[s][TOOL_TIME[0]] if k != "benign" and not k.startswith("FP:")})
    md += ["## Best single high-level dimension per kind (top-0.2% events, mean over organisations)\n",
           "| kind | best | 2nd | 3rd |", "|---|---|---|---|"]
    for k in kinds:
        avg = sorted(((np.nanmean([single[s][d].get(k, np.nan) for s in single]), d)
                      for d in TOOL_TIME + GENERAL_CLIENT), reverse=True)
        md.append(f"| {k} | " + " | ".join(f"{d} {v:.0%}" for v, d in avg[:3] if v == v) + " |")
    tags = sorted({t for s in single for t in single[s][TOOL_TIME[0]] if t.startswith("FP:")})
    chosen_all = sorted({c for pool in POOLS for L in ("2.0", "4.0") for c in out[pool][L]["chosen"]})
    md += ["", "## False alarms of the chosen dimensions\n",
           "| dimension | benign messages flagged | worst legitimate change |", "|---|---|---|"]
    for d in chosen_all:
        b = np.nanmean([single[s][d]["benign"] for s in single])
        fp = sorted(((np.nanmean([single[s][d].get(t, np.nan) for s in single]), t[3:]) for t in tags),
                    key=lambda x: -x[0] if x[0] == x[0] else 0)[0]
        md.append(f"| {d} | {b:.2%} | {fp[1]} {fp[0]:.1%} |")
    (HERE / "results" / "high_level_v2.md").write_text("\n".join(md) + "\n")
    (HERE / "results" / "high_level_v2.json").write_text(json.dumps(out, indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    main()
