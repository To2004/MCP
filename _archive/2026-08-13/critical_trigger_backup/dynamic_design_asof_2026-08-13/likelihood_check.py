"""Usage-share likelihood, split per app chronologically (the corpus is org-blocked)."""
import json, csv, math, collections

ARM = "/home/ovadyat/MCP/reports/experiments/v7/five_level_v2_policy_v7_iso"
NAC = "/home/ovadyat/MCP/reports/experiments/v5/five_level_v2_policy_v5r_nacombo"
FLOOR, WARMUP = 0.10, 40

calls = sorted(csv.DictReader(open(f"{NAC}/live_scale_all.csv")), key=lambda r: int(r["index"]))
V = {}
for org in {r["org"] for r in calls}:
    d = json.load(open(f"{ARM}/{org}.json"))
    V[org] = len(d["cells"][next(iter(d["cells"]))])          # catalog size

by_app = collections.defaultdict(list)
for r in calls: by_app[r["persona"]].append(r)

def auc(pos, neg):                                            # midrank, tie-safe
    both = sorted([(x, 1) for x in pos] + [(x, 0) for x in neg], key=lambda t: t[0])
    ranks, i = {}, 0
    while i < len(both):
        j = i
        while j + 1 < len(both) and both[j + 1][0] == both[i][0]: j += 1
        mid = (i + j) / 2 + 1
        for k in range(i, j + 1): ranks[k] = mid
        i = j + 1
    s = sum(ranks[k] for k, (_, l) in enumerate(both) if l == 1)
    n1, n0 = len(pos), len(neg)
    return (s - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else float("nan")

for gran in ("tool", "tool+asset"):
    out = collections.defaultdict(list)
    trained = tested = 0
    for app, rows in by_app.items():
        split = int(len(rows) * 0.70)
        c = collections.Counter()
        for r in rows[:split]:
            if r["category"] == "BENIGN":
                c[r["tool"] if gran == "tool" else (r["tool"], r["asset"])] += 1
        n = sum(c.values()); trained += n
        vocab = V[rows[0]["org"]] * (1 if gran == "tool" else 8)
        s_max = -math.log2(1 / (n + vocab)) if n else 1.0
        for r in rows[split:]:
            tested += 1
            if n < WARMUP: out[r["category"]].append(1.0); continue
            key = r["tool"] if gran == "tool" else (r["tool"], r["asset"])
            p = (c[key] + 1) / (n + vocab)
            ramp = min(max(-math.log2(p) / s_max, 0.0), 1.0)
            out[r["category"]].append(FLOOR + (1 - FLOOR) * ramp)

    print(f"\n{'='*70}\nGRANULARITY: (app, {gran})   trained {trained} benign / tested {tested}\n{'='*70}")
    print(f"  {'label':11} {'n':>5} {'mean L':>8} {'median':>8} {'p10':>7} {'p90':>7}")
    for lab in ("BENIGN", "MISUSE", "MALICIOUS"):
        v = sorted(out[lab])
        if not v: continue
        print(f"  {lab:11} {len(v):5} {sum(v)/len(v):8.3f} {v[len(v)//2]:8.3f} "
              f"{v[int(len(v)*.1)]:7.3f} {v[int(len(v)*.9)]:7.3f}")
    print(f"  AUC malicious vs benign : {auc(out['MALICIOUS'], out['BENIGN']):.3f}")
    print(f"  AUC misuse    vs benign : {auc(out['MISUSE'],    out['BENIGN']):.3f}")
