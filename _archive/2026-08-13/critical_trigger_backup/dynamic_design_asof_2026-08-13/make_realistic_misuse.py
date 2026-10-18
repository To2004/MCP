"""Rebuild the live_scale corpora with a realistic misuse rate and shape.

The shipped corpora make misuse 25 % of every stream and repeat the same off-limits
cell 20-40 times. That is not misuse: misuse is an agent occasionally straying outside
its purpose, not adopting a new habit. Any frequency-based signal must call a dominant
habit routine, so the corpus makes itself unmeasurable.

Real-world anchor: organisations report ~13.5 negligent-insider incidents per year, and
53-55 % of insider incidents are negligent rather than malicious (Ponemon / Exabeam
2025-26 roundups). Against thousands of agent calls per day the true per-call rate is
far below 0.1 % — too rare to measure — so this generator deliberately OVERSAMPLES to
MISUSE_SHARE and records that it did.

Shape rules, which matter more than the rate:
  * each misuse episode is 1-3 consecutive calls, not a block of sixty;
  * each episode uses a DISTINCT (tool, asset) cell — an agent that strays does not
    keep returning to the same wrong place;
  * episodes are spread through the benign stream, not concatenated at one end.

    python3 scripts/dynamic_design/make_realistic_misuse.py
"""
import csv, random, collections, os

NAC = "reports/experiments/v5/five_level_v2_policy_v5r_nacombo"
OUT = "reports/experiments/realistic_misuse"
ORGS = ("github_helios", "slack_vireo", "calendar_aurora")
MISUSE_SHARE = 0.03          # oversampled; see module docstring
MAX_EPISODE = 3              # consecutive calls in one straying episode
SEED = 20260812
csv.field_size_limit(10 ** 7)

def build(org):
    rows = sorted(csv.DictReader(open(f"{NAC}/live_scale_{org}.csv")),
                  key=lambda r: int(r["index"]))
    benign = [r for r in rows if r["category"] == "BENIGN"]
    misuse = [r for r in rows if r["category"] == "MISUSE"]

    rng = random.Random(SEED)
    # one representative call per distinct misuse cell, so no cell is ever revisited
    by_cell = collections.OrderedDict()
    for r in misuse:
        by_cell.setdefault((r["persona"], r["tool"], r["asset"]), []).append(r)
    cells = list(by_cell)
    rng.shuffle(cells)

    target = int(len(benign) * MISUSE_SHARE / (1 - MISUSE_SHARE))
    episodes, used = [], 0
    for cell in cells:
        if used >= target: break
        n = min(rng.randint(1, MAX_EPISODE), target - used, len(by_cell[cell]))
        episodes.append(by_cell[cell][:n]); used += n

    # spread the episodes through the benign stream
    slots = sorted(rng.sample(range(len(benign)), len(episodes)))
    out, cursor = [], 0
    for slot, ep in zip(slots, episodes):
        out.extend(benign[cursor:slot]); out.extend(ep); cursor = slot
    out.extend(benign[cursor:])

    path = f"{OUT}/{org}_misuse.csv"
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for i, r in enumerate(out, 1):
            r = dict(r); r["index"] = i
            w.writerow(r)
    n_mis = sum(1 for r in out if r["category"] == "MISUSE")
    cells_used = len({(r["tool"], r["asset"]) for r in out if r["category"] == "MISUSE"})
    print(f"{org:18} {len(out):5} calls  misuse {n_mis:3} ({n_mis/len(out):.1%}) "
          f"in {len(episodes)} episodes over {cells_used} distinct cells "
          f"({n_mis/max(cells_used,1):.1f} calls per cell)  -> {path}")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(f"target misuse share {MISUSE_SHARE:.0%} (oversampled; real-world per-call "
          f"rate is <0.1%), episodes of 1-{MAX_EPISODE} calls, no cell reused\n")
    for org in ORGS:
        build(org)
