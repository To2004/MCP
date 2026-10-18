"""Score the real live_scale calls with the synthetic static corpus as the prior.

Three corrections over the earlier runs:
  1. the FLOOR is absolute — the band lower bound of the cell BEFORE any change,
     not a ratio applied to the already-escalated score;
  2. EGRESS strength is a parameter, not assumed to be "go to max";
  3. the likelihood prior comes from the 100k static coverage corpus, so no call is
     cold. Prior strength alpha is swept: alpha=0 is the old cold-start behaviour,
     large alpha means the uniform catalog prior dominates.

    python3 scripts/dynamic_design/warm_eval.py
"""
import csv, json, math, collections

ARM = "reports/experiments/v7/five_level_v2_policy_v7_iso"
STATIC = "reports/experiments/synthetic_static"
NAC = "reports/experiments/v5/five_level_v2_policy_v5r_nacombo"
ORGS = ("github_helios", "slack_vireo", "calendar_aurora")
LOWER = {"low": 0.0, "medium": 17.0, "high": 50.0, "critical": 100.0}
ORDER = ["low", "medium", "high", "critical"]
SCORE_MAX = 125.0
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

def static_prior(org, key):
    """Uniform distribution over the scored cells, from the synthetic corpus."""
    c = collections.Counter()
    for r in csv.DictReader(open(f"{STATIC}/{org}_static.csv")):
        c[r["tool"] if key == "tool" else (r["tool"], r["asset"])] += 1
    n = sum(c.values())
    return {k: v / n for k, v in c.items()}, len(c)

def evaluate(org, key, alpha, egress_steps):
    prior, support = static_prior(org, key)
    art = json.load(open(f"{ARM}/{org}.json"))
    cells, blast = art["cells"], art["blast_radius"]
    rows = sorted(csv.DictReader(open(f"{NAC}/live_scale_{org}.csv")),
                  key=lambda r: int(r["index"]))
    hist = collections.defaultdict(collections.Counter); tot = collections.Counter()
    out = []
    for r in rows:
        base = cells.get(r["asset"], {}).get(r["tool"])
        b0 = blast.get(f"{r['tool']}|{r['asset']}")
        if base is None or not b0: continue
        app = r["persona"]; k = r["tool"] if key == "tool" else (r["tool"], r["asset"])
        n = tot[app]; c = hist[app]
        # Dirichlet-style blend of observed history with the static prior
        p = (c[k] + alpha * prior.get(k, 1.0 / support)) / (n + alpha) if (n + alpha) else 1.0 / support
        p = max(p, 1e-12)
        smax = -math.log2(1.0 / (support if alpha else max(n, 1) + support))
        L = 0.10 + 0.90 * min(max(-math.log2(p) / smax, 0.0), 1.0)

        b_static = band(base)
        moved = min(5, b0 + egress_steps) if egress_steps else b0
        score = base / b0 * moved
        final = min(SCORE_MAX, max(score * L, LOWER[b_static]))   # ABSOLUTE floor
        out.append(dict(cat=r["category"], base=base, b_static=b_static, L=L,
                        final=final, fband=band(final)))
        tot[app] += 1; hist[app][k] += 1
    return out

print("Likelihood prior = 100k synthetic static corpus (uniform over scored cells).")
print("Floor = absolute band lower bound of the PRE-CHANGE cell.  Egress off here.\n")
for org in ORGS:
    print(f"{'='*92}\n{org}\n{'='*92}")
    for key in ("tool", "tool+asset"):
        print(f"  key=(app,{key})")
        print(f"    {'alpha':>8} {'meanL BENIGN':>13} {'meanL BAD':>10} "
              f"{'AUC in medium':>14} {'AUC in low':>11} {'malicious flagged':>18}")
        for alpha in (0, 10, 100, 1000, 100000):
            o = evaluate(org, key, alpha, 0)
            ben = [x["L"] for x in o if x["cat"] == "BENIGN"]
            bad = [x["L"] for x in o if x["cat"] != "BENIGN"]
            def a_in(b):
                s = [x for x in o if x["b_static"] == b]
                return auc([x["L"] for x in s if x["cat"] != "BENIGN"],
                           [x["L"] for x in s if x["cat"] == "BENIGN"])
            nm = sum(1 for x in o if x["cat"] == "MALICIOUS")
            fm = sum(1 for x in o if x["cat"] == "MALICIOUS" and x["fband"] in ("high", "critical"))
            am, al = a_in("medium"), a_in("low")
            print(f"    {alpha:>8} {sum(ben)/len(ben):13.3f} {sum(bad)/len(bad):10.3f} "
                  f"{('%.3f'%am) if am==am else '—':>14} {('%.3f'%al) if al==al else '—':>11} "
                  f"{fm:6}/{nm:<4}={fm/max(nm,1):4.0%}")
    print()

print(f"{'='*92}\nEGRESS STRENGTH — how far should an external target move blast?\n{'='*92}")
print(f"  {'org':18} {'egress':>10} {'BENIGN flagged':>15} {'MISUSE':>9} {'MALICIOUS':>11}")
for org in ORGS:
    for steps, name in ((0, "off"), (1, "+1"), (2, "+2"), (9, "to max")):
        o = evaluate(org, "tool+asset", 1000, steps)
        t = collections.Counter(x["cat"] for x in o)
        f = collections.Counter(x["cat"] for x in o if x["fband"] in ("high", "critical"))
        cells = [f"{f[c]/t[c]:4.0%}" if t[c] else "  — " for c in ("BENIGN", "MISUSE", "MALICIOUS")]
        print(f"  {org:18} {name:>10} {cells[0]:>15} {cells[1]:>9} {cells[2]:>11}")
