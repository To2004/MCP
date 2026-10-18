"""Does the breadth spec cover the arguments that real traffic actually sends?

Two different failures hide behind the word "coverage", and this script separates them:

1. **Name coverage** — is every ``(tool, argument)`` seen on the wire present in the
   spec at all? A missing name means the runtime is blind to that argument, silently.
2. **Extraction coverage** — of the arguments the spec calls a quantity, how many
   actually yield a number? A parameter classified as a quantity but never parsed is
   worse than one classified ``none``: it looks covered on paper and contributes
   nothing at runtime.

Both passes are reported side by side (schema-derived and LLM), because they disagree
in interesting places and the union is what the runtime would actually use.

    python3 scripts/dynamic_design/check_breadth_coverage.py --corpus real
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path("/home/ovadyat/MCP")
sys.path.insert(0, str(REPO / "scripts" / "dynamic_design"))

from dynamic_v2 import parse_quantity  # noqa: E402

SPEC_DIR = REPO / "reports" / "experiments" / "breadth_spec"
CORPORA = {
    "real": (REPO / "reports" / "experiments" / "real_warmup", "{org}_real.csv"),
    "scale": (REPO / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r_nacombo",
              "live_scale_{org}.csv"),
}
ORGS = {"github_helios": "github", "slack_vireo": "slack", "calendar_aurora": "calendar"}

csv.field_size_limit(10 ** 7)


def load_spec(server: str, source: str) -> dict[str, dict]:
    """``{tool: {arg: entry}}`` from either the schema pass or the LLM pass."""
    if source == "llm":
        path = SPEC_DIR / f"{server}_llm.json"
        if not path.exists():
            return {}
        data = json.loads(path.read_text())
        return {tool: (block["llm"] or {}) for tool, block in data["tools"].items()}
    data = json.loads((SPEC_DIR / f"{server}.json").read_text())
    return {tool: {e["name"]: e for e in entries} for tool, entries in data["tools"].items()}


def audit(server: str, rows: list[dict], source: str) -> dict:
    spec = load_spec(server, source)
    seen: Counter = Counter()
    missing: Counter = Counter()
    classified = extracted = 0
    dropped: Counter = Counter()

    for row in rows:
        try:
            args = json.loads(row.get("args") or "{}")
        except json.JSONDecodeError:
            continue
        if not isinstance(args, dict):
            continue
        by_arg = spec.get(row["tool"])
        for name, value in args.items():
            seen[(row["tool"], name)] += 1
            if by_arg is None or name not in by_arg:
                missing[(row["tool"], name)] += 1
                continue
            entry = by_arg[name]
            if entry.get("kind", "none") == "none":
                continue
            classified += 1
            if parse_quantity(value, entry["kind"], entry.get("parse")) is None:
                dropped[(entry["kind"], row["tool"], name)] += 1
            else:
                extracted += 1

    return {"instances": sum(seen.values()), "distinct": len(seen),
            "missing_instances": sum(missing.values()), "missing_distinct": len(missing),
            "missing_names": sorted(f"{t}.{a}" for t, a in missing),
            "classified": classified, "extracted": extracted,
            "dropped": dropped.most_common(6)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", choices=sorted(CORPORA), default="real")
    args = parser.parse_args(argv)
    base, pattern = CORPORA[args.corpus]

    print(f"corpus: {args.corpus}  ({base})\n")
    header = f"{'server':<10}{'source':<8}{'arg instances':>14}{'distinct':>10}" \
             f"{'name gap':>10}{'classified':>12}{'extracted':>11}{'extract %':>11}"
    print(header)
    results: dict[tuple[str, str], dict] = {}
    for org, server in ORGS.items():
        path = base / pattern.format(org=org)
        if not path.exists():
            print(f"{server:<10}(missing {path.name})")
            continue
        rows = list(csv.DictReader(path.open()))
        for source in ("schema", "llm"):
            result = audit(server, rows, source)
            results[(server, source)] = result
            rate = result["extracted"] / max(result["classified"], 1)
            print(f"{server:<10}{source:<8}{result['instances']:>14}{result['distinct']:>10}"
                  f"{result['missing_distinct']:>10}{result['classified']:>12}"
                  f"{result['extracted']:>11}{rate:>10.0%}")

    print("\narguments seen on the wire but absent from the spec:")
    any_missing = False
    for (server, source), result in results.items():
        if result["missing_names"]:
            any_missing = True
            print(f"  {server}/{source}: {result['missing_names'][:6]}")
    if not any_missing:
        print("  none — every argument real traffic sent is present in both specs")

    print("\nclassified as a quantity but not extractable (the silent gap):")
    for (server, source), result in results.items():
        for (kind, tool, name), count in result["dropped"]:
            print(f"  {server}/{source:<7}{kind:<10}{tool}.{name:<22}{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
