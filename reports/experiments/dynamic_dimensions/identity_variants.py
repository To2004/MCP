"""Identity test: the same traffic seen with three kinds of caller identity.

  per_person  one agent token per person (what the worlds already have)
  shared10    people share agent tokens, 10 per token (e.g. one company assistant acting for many
              users); bots keep their own token; the gateway sees only the shared token
  session     no stable identity at all: every session looks like a new caller

The output CSVs keep every column (labels included) and only rewrite `agent`, so dims2/dims3 and
eval2 can score them unchanged.

Run:  python identity_variants.py w2/calendar_M.csv.gz   (writes w2/calendar_M__shared10.csv.gz, __session)
"""
from __future__ import annotations

import csv
import gzip
import sys
from pathlib import Path

csv.field_size_limit(10**9)
SHARE = 10


def main(path: Path):
    with gzip.open(path, "rt") as fh:
        rows = list(csv.DictReader(fh))
    people = sorted({r["agent"] for r in rows if "bot" not in r["role"]})
    group = {p: f"shared-{i // SHARE:03d}" for i, p in enumerate(people)}
    for tag, key in (("shared10", lambda r: group.get(r["agent"], r["agent"])), ("session", lambda r: r["session"])):
        out = path.with_name(path.name.replace(".csv.gz", f"__{tag}.csv.gz"))
        with gzip.open(out, "wt", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            for r in rows:
                w.writerow({**r, "agent": key(r)})
        print(f"{out.name}: {len({key(r) for r in rows})} identities (was {len({r['agent'] for r in rows})})")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(Path(p))
