"""Turn eval2.json into results/dimension_search.md."""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
res = json.load(open(sys.argv[1] if len(sys.argv) > 1 else HERE / "results" / "eval2.json"))
single, per, glob = res["single"], res["per_scenario"], res["global"]
scen = list(single)
kinds = sorted({k for s in scen for k in next(iter(single[s].values())) if k != "benign" and not k.startswith("FP:")})
md = ["# Dimension search: 60 dimensions, 21 kinds of strange usage, 9 scenarios\n"]
for load in [k for k in glob if k.replace(".", "").isdigit()]:
    md += [f"## One set for all scenarios, at <= {load} alerted agent-days per day\n",
           "| step | dimension added | mean detection over 9 scenarios |", "|---|---|---|"]
    md += [f"| {i + 1} | {c} | {m:.0%} |" for i, (c, m) in enumerate(glob[load])]
    bi = glob.get(f"{load}_by_intensity", {})
    if bi:
        md += ["", "Detection of the final set by kind and intensity (mild / medium / strong):", "",
               "| kind | mild | medium | strong |", "|---|---|---|---|"]
        for k in kinds:
            md.append(f"| {k} | " + " | ".join(f"{bi[f'{k}|{i}']:.0%}" if f"{k}|{i}" in bi else "–" for i in (1, 2, 3)) + " |")
    md.append("")
top = defaultdict(list)
for s, trail in per.items():
    for i, (c, _) in enumerate(trail):
        top[c].append(i + 1)
md += ["## Picked inside each scenario (greedy top 10)\n", "| dimension | scenarios (of 9) | mean position |", "|---|---|---|"]
for c, pos in sorted(top.items(), key=lambda kv: (-len(kv[1]), np.mean(kv[1]))):
    md.append(f"| {c} | {len(pos)} | {np.mean(pos):.1f} |")
md += ["", "## Best single dimension per kind (top-0.2% events; mean over scenarios where the kind exists)\n",
       "| kind | best | 2nd | 3rd |", "|---|---|---|---|"]
dims = list(single[scen[0]])
for k in kinds:
    avg = []
    for d in dims:
        v = [single[s][d].get(k) for s in scen if single[s][d].get(k) == single[s][d].get(k) and single[s][d].get(k) is not None]
        if v:
            avg.append((np.mean(v), d))
    avg.sort(reverse=True)
    md.append(f"| {k} | " + " | ".join(f"{d} {m:.0%}" for m, d in avg[:3]) + " |")
md += ["", "## False alarms on legitimate change (share of those messages flagged, mean over scenarios)\n"]
tags = sorted({k for s in scen for k in single[s][dims[0]] if k.startswith("FP:")})
md += ["| dimension | benign | " + " | ".join(t[3:] for t in tags) + " |", "|---" * (len(tags) + 2) + "|"]
for d in dims:
    row = [np.nanmean([single[s][d]["benign"] for s in scen])] + [np.nanmean([single[s][d].get(t, np.nan) for s in scen]) for t in tags]
    md.append(f"| {d} | " + " | ".join(f"{x:.2%}" for x in row) + " |")
(HERE / "results" / "dimension_search.md").write_text("\n".join(md) + "\n")
print("\n".join(md[:60]))
