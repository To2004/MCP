"""Option 2 (static-guided dimensions, risk added per caller-day) + Option 3 (learned token
model), each given half the analyst load, alerts merged. Compared at the same total load."""
from pathlib import Path
import numpy as np
import focus, learned
from evaluate import KINDS, SHORT, Run, table
from plans import EVENT_RANK, caller_days, ranks

D = Path("/home/ovadyat/MCP/runs/dynamic_dimensions")
TOTAL = 2.0


def option2_alerts(run, hz, load):
    """Caller-day keys (caller, day) alerted by option 2 at <= load, plus credited episodes."""
    inv, kday = caller_days(run)
    R = ranks(run, focus.FOCUS["A+B+C"])
    ev = R >= EVENT_RANK
    bits = np.where(ev, -np.log2(np.clip(1 - R, 1e-6, 1)), 0.0)
    best = np.zeros((inv.max() + 1, bits.shape[1]))
    np.maximum.at(best, inv, bits)
    S, Dn, top = best.sum(1), (best > 0).sum(1), best.max(1)
    lo, hi = hz
    nd = len(np.unique(run.day[(run.day >= lo) & (run.day < hi)]))
    inh = (kday >= lo) & (kday < hi)
    pick = None
    for T in (10, 14, 18, 24, 32, 45, 60, 80):
        for B in (12, 15, 99):
            cd = ((S >= T) & (Dn >= 2)) | (top >= B)
            if (cd & inh).sum() / nd <= load:
                cand = (cd & inh)
                if pick is None or cand.sum() > pick.sum():
                    pick = cand
    caught = set()
    hit = pick[inv] & ev.any(1)
    for e, (kind, d0, ix) in run.episodes.items():
        if lo <= d0 < hi and hit[ix].any():
            caught.add(e)
    keys = set(zip(run.caller[np.isin(inv, np.flatnonzero(pick))].astype(str), run.day[np.isin(inv, np.flatnonzero(pick))]))
    return keys, caught, nd


def option3_alerts(S, eps, hz, load):
    import numpy as np
    from collections import defaultdict
    by = defaultdict(list)
    for (c, d), s in S.items():
        by[c].append((d, s))
    z = {}
    for c, seq in by.items():
        seq.sort()
        for i, (d, s) in enumerate(seq):
            past = [x for _, x in seq[max(0, i - 30):i]]
            if len(past) < 5:
                continue
            med = float(np.median(past)); mad = float(np.median(np.abs(np.array(past) - med))) + 1.0
            z[(c, d)] = (s - med) / mad
    lo, hi = hz
    days = {d for (_, d) in S if lo <= d < hi}
    for thr in (3, 4, 5, 6, 8, 10, 13, 16, 20, 25, 32, 40, 50, 64, 90):
        al = {k for k, v in z.items() if v > thr and lo <= k[1] < hi}
        if len(al) / max(1, len(days)) <= load:
            return al, {e for k in al for e in eps.get(k, ())}
    return set(), set()


rows_md = ["# Option 2 + Option 3 together, same total load (<= 2 caller-days/day)\n"]
for g, (pairs, hz) in {"year 1": ([("1", "seed1"), ("2", "seed2")], (30, 365)),
                       "year 2": ([("1", "seed1"), ("2", "seed2")], (365, 10**6))}.items():
    res = {"option 2 alone": [], "option 3 alone": [], "option 2 + option 3 (half load each)": []}
    for sd, wname in pairs:
        run = Run(D / f"scores_s{sd}_w90.npz")
        S, eps, kinds = learned.score_world(Path(f"world_{wname}.csv.gz"))
        k2, c2, nd = option2_alerts(run, hz, TOTAL)
        k3, c3 = option3_alerts(S, eps, hz, TOTAL)
        k2h, c2h, _ = option2_alerts(run, hz, TOTAL / 2)
        k3h, c3h = option3_alerts(S, eps, hz, TOTAL / 2)
        total_eps = {e: kind for e, (kind, d0, ix) in run.episodes.items() if hz[0] <= d0 < hz[1]}
        for name, caught, keys in (("option 2 alone", c2, k2), ("option 3 alone", c3, k3),
                                   ("option 2 + option 3 (half load each)", c2h | c3h, k2h | {(str(c), d) for c, d in k3h})):
            det = {kd: np.mean([e in caught for e, kk in total_eps.items() if kk == kd]) for kd in KINDS}
            res[name].append((len(keys) / nd, det))
    rows = []
    for name, ps in res.items():
        det = {k: np.nanmean([p[1][k] for p in ps]) for k in KINDS}
        rows.append([name, f"{np.mean([p[0] for p in ps]):.1f}", f"{np.nanmean(list(det.values())):.0%}"]
                    + [f"{det[k]:.0%}" for k in KINDS])
    rows_md += [f"## {g}\n", table(rows, ["detector", "load", "mean detect"] + [SHORT[k] for k in KINDS]), ""]
    print(rows_md[-2], flush=True)
Path("results/hybrid.md").write_text("\n".join(rows_md) + "\n")
