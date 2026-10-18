"""Rank misuse against its neighbours, on the realistic-misuse corpora.

Goal is NOT enforcement. Nothing is blocked; the question is whether a misuse call
scores higher than the benign calls around it. So every metric here is a RANKING
metric.

Model under test:
    final = min(score_max, max( cell(tool,asset) x likelihood x escalation , floor ))
      likelihood  keyed (company, tool), catalog prior alpha=30, no cold start
      escalation  3 bins from the call history via Tukey fences (Q1-1.5*IQR,
                  Q3+1.5*IQR): below -> 0.9, between -> 1.0, above -> 1.3.
                  Applied only to MAGNITUDE arguments (array lengths, or numerics the
                  static scan gave a critical_trigger); never to identifiers such as
                  pull_number, where "larger" carries no meaning.
      floor       absolute band lower bound of the cell

Averaged over 10 corpus seeds because a realistic misuse rate leaves only ~15 misuse
calls per run.

    python3 scripts/dynamic_design/rank_eval.py
"""
import csv, json, math, random, collections, statistics

NAC = "reports/experiments/v5/five_level_v2_policy_v5r_nacombo"
ARM = "reports/experiments/v7/five_level_v2_policy_v7_iso"
STATIC = "reports/experiments/synthetic_static"
ORGS = ("github_helios", "slack_vireo", "calendar_aurora")
ALPHA, MISUSE_SHARE, MAX_EP, MIN_HIST = 30.0, 0.03, 3, 20
BIN_MULT = {"below": 0.9, "between": 1.0, "above": 1.3}   # bounded both ways
LOWER = {"low": 0.0, "medium": 17.0, "high": 50.0, "critical": 100.0}
SCORE_MAX = 125.0
csv.field_size_limit(10 ** 7)

def band(s):
    return "critical" if s >= 100 else "high" if s >= 50 else "medium" if s >= 17 else "low"

def auc(pos, neg):
    b = sorted([(x, 1) for x in pos] + [(x, 0) for x in neg], key=lambda t: t[0])
    r, i = {}, 0
    while i < len(b):
        j = i
        while j + 1 < len(b) and b[j + 1][0] == b[i][0]: j += 1
        m = (i + j) / 2 + 1
        for k in range(i, j + 1): r[k] = m
        i = j + 1
    s = sum(r[k] for k, (_, l) in enumerate(b) if l == 1)
    n1, n0 = len(pos), len(neg)
    return (s - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else float("nan")

def fences(vals):
    """Two cut points from the observed history — Tukey, so no normality assumed."""
    v = sorted(vals)
    q1 = statistics.quantiles(v, n=4)[0] if len(v) >= 4 else v[0]
    q3 = statistics.quantiles(v, n=4)[2] if len(v) >= 4 else v[-1]
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr

def magnitudes(art, tool, args):
    """(name, value) for arguments that are QUANTITIES, not identifiers."""
    trig = {i["name"] for i in art.get("tool_input_ranking", {}).get(tool, {}).get("inputs", [])
            if i.get("critical_trigger")}
    out = []
    for k, v in args.items():
        if isinstance(v, list): out.append((k + "[]", len(v)))
        elif isinstance(v, (int, float)) and not isinstance(v, bool) and k in trig:
            out.append((k, float(v)))
    return out

def corpus(org, seed):
    rows = sorted(csv.DictReader(open(f"{NAC}/live_scale_{org}.csv")), key=lambda r: int(r["index"]))
    benign = [r for r in rows if r["category"] == "BENIGN"]
    misuse = [r for r in rows if r["category"] == "MISUSE"]
    rng = random.Random(seed)
    by_cell = collections.OrderedDict()
    for r in misuse: by_cell.setdefault((r["persona"], r["tool"], r["asset"]), []).append(r)
    cells = list(by_cell); rng.shuffle(cells)
    target, eps, used = int(len(benign) * MISUSE_SHARE / (1 - MISUSE_SHARE)), [], 0
    for c in cells:
        if used >= target: break
        n = min(rng.randint(1, MAX_EP), target - used, len(by_cell[c]))
        eps.append(by_cell[c][:n]); used += n
    slots = sorted(rng.sample(range(len(benign)), len(eps)))
    out, cur = [], 0
    for s, ep in zip(slots, eps):
        out.extend(benign[cur:s]); out.extend(ep); cur = s
    out.extend(benign[cur:])
    return out

def resolve_asset(cells, org, asset):
    """The corpora sometimes drop the org prefix the scan uses (`announcements` for
    `vireo-announcements`). Try the literal name, then the prefixed one."""
    if asset in cells: return asset
    pre = org.split("_")[1]
    return f"{pre}-{asset}" if f"{pre}-{asset}" in cells else asset


def score(org, rows, use_escalation):
    art = json.load(open(f"{ARM}/{org}.json")); cells = art["cells"]
    pc = collections.Counter()
    for r in csv.DictReader(open(f"{STATIC}/{org}_static.csv")): pc[r["tool"]] += 1
    tot = sum(pc.values()); prior = {k: v / tot for k, v in pc.items()}; sup = len(pc)

    hist = collections.defaultdict(collections.Counter); n_obs = collections.Counter()
    mags = collections.defaultdict(list)          # (company, tool, arg) -> values seen
    esc_bins = collections.Counter()
    out = []
    for r in rows:
        asset = resolve_asset(cells, org, r["asset"])
        base = cells.get(asset, {}).get(r["tool"])
        if base is None: continue
        company = r["persona"].split("@")[-1]
        n = n_obs[company]
        p = (hist[company][r["tool"]] + ALPHA * prior.get(r["tool"], 1 / sup)) / (n + ALPHA)
        L = 0.10 + 0.90 * min(max(-math.log2(max(p, 1e-12)) / -math.log2(1 / (sup + max(n, 1))), 0), 1)

        try: args = json.loads(r["args"]) if r["args"] else {}
        except json.JSONDecodeError: args = {}
        esc = 1.0
        if use_escalation:
            for name, val in magnitudes(art, r["tool"], args):
                seen = mags[(company, r["tool"], name)]
                if len(seen) >= MIN_HIST:
                    lo, hi = fences(seen)
                    b = "above" if val > hi else "below" if val < lo else "between"
                    esc = max(esc, BIN_MULT[b]) if b == "above" else min(esc, BIN_MULT[b])
                    esc_bins[b] += 1
                seen.append(val)

        b0 = band(base)
        final = min(SCORE_MAX, max(base * L * esc, LOWER[b0]))
        out.append(dict(cat=r["category"], base=base, b=b0, L=L, esc=esc, final=final))
        hist[company][r["tool"]] += 1; n_obs[company] += 1
    return out, esc_bins

print("Realistic misuse (~3 %, episodes of 1-3, no cell reused). Ranking only — nothing")
print("is blocked. likelihood keyed (company, tool). 10 corpus seeds, mean [min-max].\n")
print(f"  {'server':17} {'escalation':11} {'AUC misuse>benign':>19} {'AUC within band':>17} "
      f"{'misuse mean %ile':>17}")
for org in ORGS:
    for use_esc in (False, True):
        A, W, P = [], [], []
        for seed in range(10):
            o, bins = score(org, corpus(org, 20260812 + seed), use_esc)
            mis = [x["final"] for x in o if x["cat"] == "MISUSE"]
            ben = [x["final"] for x in o if x["cat"] == "BENIGN"]
            A.append(auc(mis, ben))
            ws = [auc([x["final"] for x in o if x["b"] == b and x["cat"] == "MISUSE"],
                      [x["final"] for x in o if x["b"] == b and x["cat"] == "BENIGN"])
                  for b in ("low", "medium", "high", "critical")]
            ws = [w for w in ws if w == w]
            if ws: W.append(sum(ws) / len(ws))
            allv = sorted(x["final"] for x in o)
            P.append(sum(allv.index(m) / len(allv) for m in mis) / len(mis) * 100)
        w = f"{sum(W)/len(W):.3f}" if W else "—"
        print(f"  {org:17} {'on' if use_esc else 'off':11} "
              f"{sum(A)/len(A):8.3f} [{min(A):.2f}-{max(A):.2f}] {w:>17} "
              f"{sum(P)/len(P):16.0f}%")
    print()
