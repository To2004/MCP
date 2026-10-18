"""live_scale_* only. Two questions:
   A) under the floor, likelihood only reorders WITHIN a band — does it reorder well?
   B) what does moving the floor actually buy or cost?
"""
import json, csv, math, collections

ARM = "/home/ovadyat/MCP/reports/experiments/v7/five_level_v2_policy_v7_iso"
NAC = "/home/ovadyat/MCP/reports/experiments/v5/five_level_v2_policy_v5r_nacombo"
TH = {"medium": 17.0, "high": 50.0, "critical": 100.0}
ORDER = ["low", "medium", "high", "critical"]
LOWER = {"low": 0.0, "medium": 17.0, "high": 50.0, "critical": 100.0}
WARMUP, FLOOR_LOW = 40, 0.10
ART = {o: json.load(open(f"{ARM}/{o}.json")) for o in
       ("github_helios", "slack_vireo", "calendar_aurora")}

def band(s):
    return "critical" if s >= TH["critical"] else "high" if s >= TH["high"] \
        else "medium" if s >= TH["medium"] else "low"

def auc(pos, neg):
    b = sorted([(x, 1) for x in pos] + [(x, 0) for x in neg], key=lambda t: t[0])
    ranks, i = {}, 0
    while i < len(b):
        j = i
        while j + 1 < len(b) and b[j + 1][0] == b[i][0]: j += 1
        m = (i + j) / 2 + 1
        for k in range(i, j + 1): ranks[k] = m
        i = j + 1
    s = sum(ranks[k] for k, (_, l) in enumerate(b) if l == 1)
    n1, n0 = len(pos), len(neg)
    return (s - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else float("nan")

def score_stream(org):
    """One causal pass; returns per-call base score, band, and likelihood."""
    rows = sorted(csv.DictReader(open(f"{NAC}/live_scale_{org}.csv")),
                  key=lambda r: int(r["index"]))
    a = ART[org]; V = len(a["cells"][next(iter(a["cells"]))])
    hist = collections.defaultdict(collections.Counter); tot = collections.Counter()
    out = []
    for r in rows:
        base = a["cells"].get(r["asset"], {}).get(r["tool"])
        if base is None: continue
        app = r["persona"]; n = tot[app]
        if n < WARMUP:
            L = 1.0
        else:
            c = hist[app]
            p = (c[r["tool"]] + 1) / (n + V)
            ramp = min(max(-math.log2(p) / -math.log2(1 / (n + V)), 0.0), 1.0)
            L = FLOOR_LOW + (1 - FLOOR_LOW) * ramp
        out.append(dict(cat=r["category"], tool=r["tool"], asset=r["asset"], app=app,
                        base=base, band=band(base), L=L, n=n))
        tot[app] += 1
        hist[app][r["tool"]] += 1          # train on everything seen (no label peeking)
    return out

def floor_for(mode, b, base):
    if mode == "band":  return LOWER[b] / base
    if mode == "one":                                   # one band lower
        i = max(0, ORDER.index(b) - 1); return LOWER[ORDER[i]] / base
    if mode == "half":  return 0.5
    return FLOOR_LOW                                     # "none"

for org in ("github_helios", "slack_vireo", "calendar_aurora"):
    o = [x for x in score_stream(org) if x["n"] >= WARMUP]      # warm calls only
    print(f"\n{'='*88}\n{org}  ({len(o)} warm calls)\n{'='*88}")

    print("  A · does likelihood rank correctly INSIDE each static band?")
    print(f"    {'band':10} {'calls':>6} {'benign':>7} {'bad':>5} {'AUC(bad>benign)':>17}")
    for b in ORDER:
        sub = [x for x in o if x["band"] == b]
        if not sub: continue
        ben = [x["L"] for x in sub if x["cat"] == "BENIGN"]
        bad = [x["L"] for x in sub if x["cat"] != "BENIGN"]
        a_ = auc(bad, ben)
        print(f"    {b:10} {len(sub):6} {len(ben):7} {len(bad):5} "
              f"{('%.3f' % a_) if a_ == a_ else '—':>17}")

    print("\n  B · what moving the floor buys / costs  (flagged = final ≥ high)")
    print(f"    {'floor mode':22} {'BENIGN':>10} {'MISUSE':>10} {'MALICIOUS':>11}  demoted-out-of-band")
    tot = collections.Counter(x["cat"] for x in o)
    for mode, name in (("band", "band boundary (design)"), ("one", "one band lower"),
                       ("half", "fixed 0.5"), ("none", "none (0.1)")):
        fl = collections.Counter(); dem = 0
        for x in o:
            L = max(x["L"], floor_for(mode, x["band"], x["base"]))
            fb = band(x["base"] * L)
            if fb in ("high", "critical"): fl[x["cat"]] += 1
            if ORDER.index(fb) < ORDER.index(x["band"]): dem += 1
        cells = [f"{fl[c]:4}/{tot[c]:<4}={fl[c]/tot[c]:4.0%}" if tot[c] else "     —     "
                 for c in ("BENIGN", "MISUSE", "MALICIOUS")]
        print(f"    {name:22} {cells[0]:>10} {cells[1]:>10} {cells[2]:>11}  {dem:5}")
