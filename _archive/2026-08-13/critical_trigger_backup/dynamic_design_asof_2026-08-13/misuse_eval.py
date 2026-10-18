"""Benign vs MISUSE only. Malicious is excluded entirely — the static matrix already
separates it, and it is the class whose scripted repetition distorts frequency signals.

Compares two ways of counting history:
  raw      every call is an observation (what we had)
  episode  a (app, key) seen many times inside one hour counts ONCE
           -- a burst is one event, not sixty pieces of evidence

    python3 scripts/dynamic_design/misuse_eval.py
"""
import csv, json, math, collections

ARM = "reports/experiments/v7/five_level_v2_policy_v7_iso"
STATIC = "reports/experiments/synthetic_static"
NAC = "reports/experiments/v5/five_level_v2_policy_v5r_nacombo"
ORGS = ("github_helios", "slack_vireo", "calendar_aurora")
ALPHA = 30.0                      # weak catalog prior (10-100 was the good range)
csv.field_size_limit(10 ** 7)

def band(s):
    return "critical" if s >= 100 else "high" if s >= 50 else "medium" if s >= 17 else "low"

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

def prior_of(org, key):
    c = collections.Counter()
    for r in csv.DictReader(open(f"{STATIC}/{org}_static.csv")):
        c[r["tool"] if key == "tool" else (r["tool"], r["asset"])] += 1
    n = sum(c.values())
    return {k: v / n for k, v in c.items()}, len(c)

def hour(ts):                                   # 2026-07-16T00:41:00 -> 2026-07-16T00
    return ts[:13]

def run(org, key, mode):
    prior, support = prior_of(org, key)
    cells = json.load(open(f"{ARM}/{org}.json"))["cells"]
    rows = [r for r in sorted(csv.DictReader(open(f"{NAC}/live_scale_{org}.csv")),
                              key=lambda r: int(r["index"]))
            if r["category"] in ("BENIGN", "MISUSE")]        # malicious excluded
    obs = collections.defaultdict(collections.Counter)       # app -> key -> weight
    seen_ep = set()                                          # (app, key, hour)
    n_obs = collections.Counter()
    out = []
    for r in rows:
        base = cells.get(r["asset"], {}).get(r["tool"])
        if base is None: continue
        app = r["persona"]
        k = r["tool"] if key == "tool" else (r["tool"], r["asset"])
        c, n = obs[app], n_obs[app]
        p = (c[k] + ALPHA * prior.get(k, 1.0 / support)) / (n + ALPHA)
        smax = -math.log2(1.0 / (support + max(n, 1)))
        L = 0.10 + 0.90 * min(max(-math.log2(max(p, 1e-12)) / smax, 0.0), 1.0)
        out.append(dict(cat=r["category"], base=base, b=band(base), L=L))
        # --- update history
        if mode == "raw":
            obs[app][k] += 1; n_obs[app] += 1
        else:
            ep = (app, k, hour(r["timestamp"]))
            if ep not in seen_ep:
                seen_ep.add(ep); obs[app][k] += 1; n_obs[app] += 1
    return out

print("BENIGN vs MISUSE only (malicious excluded).  Catalog prior alpha=30.\n")
print(f"  {'server':17} {'key':12} {'counting':9} {'meanL BEN':>10} {'meanL MIS':>10} "
      f"{'AUC all':>8} {'AUC in medium':>14}")
for org in ORGS:
    for key in ("tool", "tool+asset"):
        for mode in ("raw", "episode"):
            o = run(org, key, mode)
            ben = [x["L"] for x in o if x["cat"] == "BENIGN"]
            mis = [x["L"] for x in o if x["cat"] == "MISUSE"]
            med = [x for x in o if x["b"] == "medium"]
            am = auc([x["L"] for x in med if x["cat"] == "MISUSE"],
                     [x["L"] for x in med if x["cat"] == "BENIGN"])
            print(f"  {org:17} {key:12} {mode:9} {sum(ben)/len(ben):10.3f} "
                  f"{sum(mis)/len(mis):10.3f} {auc(mis, ben):8.3f} "
                  f"{('%.3f' % am) if am == am else '—':>14}")
    print()

print("How repetitive is each class, raw calls vs distinct hourly episodes:")
print(f"  {'server':17} {'class':8} {'calls':>6} {'cells':>6} {'raw/cell':>9} {'episodes':>9} {'ep/cell':>8}")
for org in ORGS:
    rows = [r for r in csv.DictReader(open(f"{NAC}/live_scale_{org}.csv"))
            if r["category"] in ("BENIGN", "MISUSE")]
    for lab in ("BENIGN", "MISUSE"):
        s = [r for r in rows if r["category"] == lab]
        cells = {(r["tool"], r["asset"]) for r in s}
        eps = {(r["persona"], r["tool"], r["asset"], hour(r["timestamp"])) for r in s}
        print(f"  {org:17} {lab:8} {len(s):6} {len(cells):6} {len(s)/len(cells):9.1f} "
              f"{len(eps):9} {len(eps)/len(cells):8.1f}")
