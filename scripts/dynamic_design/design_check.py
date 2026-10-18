"""Check the two design rules against real artifacts + the labelled live corpus.

A) the band-floor rule: floor(cell) = band_lower_bound(cell) / cell_score
B) usage-share likelihood: surprisal of (app, tool) under the app's own distribution
"""
import json, csv, glob, math, collections

ARM = "/home/ovadyat/MCP/reports/experiments/v7/five_level_v2_policy_v7_iso"
NAC = "/home/ovadyat/MCP/reports/experiments/v5/five_level_v2_policy_v5r_nacombo"

# ---------- A. how much room does the band-floor rule actually leave? ----------
def band_of(score, th):
    if score >= th.get("critical", 1e9): return "critical", th["critical"]
    if score >= th["high"]:              return "high", th["high"]
    if score >= th["medium"]:            return "medium", th["medium"]
    return "low", 0.0

print("=" * 78)
print("A · BAND-FLOOR RULE — floor = band_lower_bound / cell_score")
print("=" * 78)
rows = collections.defaultdict(list)
for f in sorted(glob.glob(f"{ARM}/*.json")):
    d = json.load(open(f)); th = d["band_thresholds"]; smax = d["score_max"]
    for a, row in d["cells"].items():
        for t, v in row.items():
            if v is None: continue
            b, lo = band_of(v, th)
            floor = (lo / v) if lo else 0.10          # low band: global floor
            rows[b].append((v, floor))
print(f"  thresholds {json.load(open(f))['band_thresholds']}  score_max {smax}\n")
print(f"  {'band':9} {'cells':>6} {'floor min':>10} {'floor max':>10} {'floor mean':>11} {'headroom':>9}")
for b in ("low", "medium", "high", "critical"):
    v = rows[b]
    if not v: continue
    fl = [x[1] for x in v]
    print(f"  {b:9} {len(v):6} {min(fl):10.2f} {max(fl):10.2f} {sum(fl)/len(fl):11.2f} "
          f"{1-sum(fl)/len(fl):9.0%}")
frozen = sum(1 for b in rows for s, f in rows[b] if f >= 0.995)
tot = sum(len(v) for v in rows.values())
print(f"\n  cells with NO room at all (sitting on their band boundary): {frozen}/{tot} = {frozen/tot:.0%}")

# ---------- B. usage-share likelihood on the labelled corpus ----------
print("\n" + "=" * 78)
print("B · USAGE-SHARE LIKELIHOOD — surprisal of (app, tool) under the app's own mix")
print("=" * 78)
calls = list(csv.DictReader(open(f"{NAC}/live_scale_all.csv")))
calls.sort(key=lambda r: int(r["index"]))
catalog = {}
for org in {r["org"] for r in calls}:
    p = f"{ARM}/{org}.json"
    try: catalog[org] = len(json.load(open(p))["cells"][list(json.load(open(p))["cells"])[0]])
    except Exception: catalog[org] = 20

split = int(len(calls) * 0.70)
train = [r for r in calls[:split] if r["category"] == "BENIGN"]   # benign head only
counts = collections.defaultdict(collections.Counter)
for r in train: counts[r["persona"]][r["tool"]] += 1

FLOOR = 0.10
def likelihood(persona, tool, org):
    c = counts[persona]; n = sum(c.values()); V = catalog.get(org, 20)
    if n < 50: return 1.0                                   # warm-up: decline to vouch
    p = (c[tool] + 1) / (n + V)                             # add-one smoothing
    s = -math.log2(p)
    s_max = -math.log2(1 / (n + V))                         # an unseen tool
    ramp = min(max(s / s_max, 0.0), 1.0)
    return FLOOR + (1 - FLOOR) * ramp

test = calls[split:]
by = collections.defaultdict(list)
for r in test: by[r["category"]].append(likelihood(r["persona"], r["tool"], r["org"]))
print(f"  trained on {len(train)} benign calls; tested on {len(test)}\n")
print(f"  {'label':11} {'n':>5} {'mean L':>8} {'median':>8} {'p90':>7}")
for lab in ("BENIGN", "MISUSE", "MALICIOUS"):
    v = sorted(by[lab])
    if not v: continue
    print(f"  {lab:11} {len(v):5} {sum(v)/len(v):8.3f} {v[len(v)//2]:8.3f} {v[int(len(v)*.9)]:7.3f}")

def auc(pos, neg):
    both = sorted([(x, 1) for x in pos] + [(x, 0) for x in neg])
    r = 0; n1 = len(pos); n0 = len(neg); rank = 0
    for i, (_, lab) in enumerate(both, 1):
        if lab == 1: rank += i
    return (rank - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else 0.0
print(f"\n  AUC malicious vs benign : {auc(by['MALICIOUS'], by['BENIGN']):.3f}")
print(f"  AUC misuse    vs benign : {auc(by['MISUSE'],    by['BENIGN']):.3f}")

# ---------- C. what the two rules do together ----------
print("\n" + "=" * 78)
print("C · COMBINED — can the band floor still bind after likelihood?")
print("=" * 78)
d = json.load(open(f"{ARM}/github_helios.json")); th = d["band_thresholds"]
for cell in (12, 25, 48, 60, 96, 100, 125):
    b, lo = band_of(cell, th)
    fl = (lo / cell) if lo else 0.10
    print(f"  cell {cell:4}  band {b:9} floor {fl:.2f}  -> may fall to {cell*fl:6.1f} "
          f"(still {band_of(cell*fl, th)[0]})")
