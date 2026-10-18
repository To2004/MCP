"""Simulate the proposed dynamic design on the real labelled calls, causally."""
import json, csv, math, re, collections, sys

ARM = "/home/ovadyat/MCP/reports/experiments/v7/five_level_v2_policy_v7_iso"
NAC = "/home/ovadyat/MCP/reports/experiments/v5/five_level_v2_policy_v5r_nacombo"
TH = {"medium": 17, "high": 50, "critical": 100}
WARMUP = 40           # on the APP's total volume, never on the per-tool count
FLOOR_LOW = 0.10

ART = {o: json.load(open(f"{ARM}/{o}.json"))
       for o in ("github_helios", "slack_vireo", "calendar_aurora")}

# roster: what counts as "us" in this deployment (design time, from the register)
ROSTER = {"To2004", "helios", "vireo", "aurora", "group.calendar.google.com",
          "group.v.calendar.google.com"}
IDENT = re.compile(r"[\w.+-]+@[\w.-]+\.\w+|^[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+$")

def band(s):
    return ("critical", 100.0) if s >= TH["critical"] else \
           ("high", 50.0) if s >= TH["high"] else \
           ("medium", 17.0) if s >= TH["medium"] else ("low", 0.0)

def cell(org, tool, asset):
    a = ART[org]
    v = a["cells"].get(asset, {}).get(tool)
    b = a["blast_radius"].get(f"{tool}|{asset}")
    return (v, b) if v is not None and b else (None, None)

def args_of(r):
    try: return json.loads(r["args"]) if r["args"] else {}
    except json.JSONDecodeError: return {}

def escalation(org, tool, a):
    """How much wider is THIS call than the typical one the scan priced? -> blast steps."""
    steps, why = 0, []
    for k, v in a.items():
        if isinstance(v, list) and len(v) >= 10:
            steps = max(steps, 2); why.append(f"{k}[{len(v)}]")
        elif isinstance(v, bool) and v and any(h in k.lower() for h in
                ("recursive", "force", "cascade", "all", "permanent")):
            steps = max(steps, 2); why.append(f"{k}=true")
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            if any(h in k.lower() for h in ("limit", "count", "max", "per_page")) and v >= 100:
                steps = max(steps, 1); why.append(f"{k}={v}")
    for e in ART[org].get("tool_input_ranking", {}).get(tool, {}).get("inputs", []):
        n, t = e.get("name"), e.get("critical_trigger")
        if not t or n not in a: continue
        m = re.search(r"(\d[\d,]*)", str(t))
        if not m: continue
        thr = float(m.group(1).replace(",", "")); val = a[n]
        if (isinstance(val, list) and len(val) >= thr) or \
           (isinstance(val, (int, float)) and not isinstance(val, bool) and val >= thr):
            steps = max(steps, 2); why.append(f"{n} crosses '{t}'")
    return steps, why

def egress(a):
    """Any identifier-shaped value that is not in our roster."""
    for k, v in a.items():
        vals = v if isinstance(v, list) else [v]
        for x in vals:
            if not isinstance(x, str) or not IDENT.match(x): continue
            if not any(tok in x for tok in ROSTER):
                return True, f"{k}={x}"
    return False, ""

def run(path, label, show):
    rows = sorted(csv.DictReader(open(path)), key=lambda r: int(r["index"]))
    hist = collections.defaultdict(collections.Counter)   # app -> tool counts (causal)
    tot = collections.Counter()
    out = []
    for r in rows:
        org, app, tool, asset = r["org"], r["persona"], r["tool"], r["asset"]
        if org not in ART: continue
        base, blast = cell(org, tool, asset)
        if base is None: continue
        b_name, b_lo = band(base)

        a = args_of(r)
        steps, why_e = escalation(org, tool, a)
        eg, why_g = egress(a)
        blast_new = 5 if eg else min(5, blast + steps)
        score = base / blast * blast_new

        n = tot[app]
        if n < WARMUP:
            L, why_l = 1.0, f"cold (app has {n} calls)"
        else:
            c = hist[app]; V = len(ART[org]["cells"][next(iter(ART[org]["cells"]))])
            p = (c[tool] + 1) / (n + V)
            ramp = min(max(-math.log2(p) / -math.log2(1 / (n + V)), 0), 1)
            L = FLOOR_LOW + (1 - FLOOR_LOW) * ramp
            why_l = f"{c[tool]}/{n} = {c[tool]/max(n,1):.1%} of this app's calls"
        floor = (b_lo / base) if b_lo else FLOOR_LOW
        L_eff = max(L, floor)
        final = score * L_eff

        out.append(dict(r=r, base=base, blast=blast, blast_new=blast_new, steps=steps,
                        why_e="; ".join(why_e), eg=eg, why_g=why_g, L=L, why_l=why_l,
                        floor=floor, final=final, band=b_name,
                        fband=band(final)[0], n=n))
        tot[app] += 1
        if band(final)[0] not in ("high", "critical"):    # only unflagged calls train
            hist[app][tool] += 1
    show(out, label)
    return out
