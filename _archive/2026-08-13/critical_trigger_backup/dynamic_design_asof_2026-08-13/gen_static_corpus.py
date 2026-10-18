"""Generate a STATIC coverage corpus: 100k calls per MCP touching every scored cell.

Purpose: give the runtime layer a baseline that is not cold, without using any real
traffic. The corpus is deterministic and uniform over the scored (tool, asset) cells
of the scan — it encodes what the server *can* do, not what anyone actually did.
Uniform on purpose: it is a maximum-entropy prior, so it adds support without
asserting that any pairing is normal.

    python3 scripts/dynamic_design/gen_static_corpus.py [N]

Writes reports/experiments/synthetic_static/<org>_static.csv (default N=100000).
"""
import csv, json, sys, os

ARM = "reports/experiments/v7/five_level_v2_policy_v7_iso"
OUT = "reports/experiments/synthetic_static"
ORGS = {
    "github_helios":  ["Grid Ops Agent@helios", "CI Bot@helios", "Analyst Agent@helios"],
    "slack_vireo":    ["Trial Coordinator@vireo", "PV Assistant@vireo", "Eng Bot@vireo"],
    "calendar_aurora": ["Workplace Services Agent@aurora", "Exec Assistant@aurora",
                        "Scheduler Bot@aurora"],
}

def main(n_total=100_000):
    os.makedirs(OUT, exist_ok=True)
    for org, apps in ORGS.items():
        d = json.load(open(f"{ARM}/{org}.json"))
        cells = d["cells"]
        pairs = [(a, t) for a in cells for t, v in cells[a].items() if v is not None]
        pairs.sort()                                   # deterministic order
        path = f"{OUT}/{org}_static.csv"
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["index", "org", "persona", "category", "asset", "tool",
                        "status", "args", "source"])
            for i in range(n_total):
                asset, tool = pairs[i % len(pairs)]     # round-robin: uniform coverage
                app = apps[i % len(apps)]               # spread evenly over the apps
                w.writerow([i + 1, org, app, "STATIC", asset, tool, "OK", "{}",
                            "synthetic_static"])
        per_cell = n_total // len(pairs)
        print(f"{org:18} {n_total:7} calls over {len(pairs):4} scored cells "
              f"({per_cell} per cell), {len(apps)} apps -> {path}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100_000)
