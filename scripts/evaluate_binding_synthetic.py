#!/usr/bin/env python3
"""Full ``tool x asset`` coverage: can the resolver name the asset a call touches?

The live corpus measures whatever the personas happened to do — a few register
cells get hundreds of calls, most get none. This harness fills the matrix: every
tool crossed with every asset the register says it reaches, ten generated calls
each, built from the vendor's own input schema.

**The key table is given, not discovered.** Discovery is measured separately by
``evaluate_binding.py``; here the id-to-asset mapping is handed over so a failure
is a failure of *resolution* and nothing else.

Reported per server, and per failing cell:

``recall``     the targeted asset is in the resolved set
``mean set``   how many assets were returned
``exact``      returned exactly the targeted asset and nothing else

Usage::

    uv run python scripts/evaluate_binding_synthetic.py
    uv run python scripts/evaluate_binding_synthetic.py --only slack_vireo --variants 20
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mcp_security.binding import AssetResolver, Level, discover  # noqa: E402
from mcp_security.binding.catalog import catalog_for  # noqa: E402
from mcp_security.binding.discovery import Binding, Discovery  # noqa: E402
from mcp_security.binding.identifiers import canonical_id, normalize_key  # noqa: E402
from mcp_security.binding.synthetic import generate  # noqa: E402
from mcp_security.static_scoring.server_policies import (  # noqa: E402
    parse_asset_register,
    policy_for,
)

CORPUS = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r_nacombo"
V8_DIR = REPO_ROOT / "reports" / "experiments" / "v8"
#: The three servers the method was developed against.
SERVERS = ("calendar_aurora", "github_helios", "slack_vireo")

#: Held-out servers: different kinds, never consulted while writing the rules.
#: Their catalogs and registers already existed in the repo; the only thing
#: supplied for them is the key table, which this harness assumes anyway.
HELD_OUT = ("sqlite_cbg_sqlite", "fs_corp_filesystem")

LEVELS = {
    Level.TOOL_ONLY: "L0 tool-only",
    Level.CATALOG: "L1 +keys",
    Level.OPERATION: "L2 +operation",
    Level.EGRESS: "L3 +egress",
}


def given_keys(server: str) -> tuple[str, dict[str, str]]:
    """The key table, taken as given: the container parameter and what its values mean.

    Derived once from the labelled corpus (the asset a human assigned to the
    calls carrying each identifier) and then treated as an input. This is the
    "assume you have the keys" premise: correct by construction, so any error
    below belongs to resolution rather than to discovery.
    """
    path = V8_DIR / "given_keys.json"
    entry = json.loads(path.read_text(encoding="utf-8")).get(server, {}) if path.exists() else {}
    return entry.get("container_key", ""), entry.get("ids", {})


def build_given_keys() -> dict[str, dict[str, str]]:
    """Recover the correct key table from the labelled corpus, once."""
    tables: dict[str, dict[str, str]] = {}
    for server in SERVERS:
        rows = parse_asset_register(policy_for(server).text)
        with (CORPUS / f"live_scale_{server}.csv").open(newline="", encoding="utf-8") as handle:
            calls = list(csv.DictReader(handle))
        found = discover(calls, rows)
        register_ids = {row.asset_id for row in rows}
        observed: dict[str, Counter[str]] = defaultdict(Counter)
        for call in calls:
            args = json.loads(call["args"] or "{}")
            for key, value in args.items():
                if normalize_key(key) not in found.container_keys:
                    continue
                for raw in value if isinstance(value, list) else [value]:
                    if isinstance(raw, (str, int)) and str(raw).strip():
                        observed[canonical_id(str(raw))][call["asset"]] += 1
        table: dict[str, str] = {}
        for container_id, labels in observed.items():
            modal = labels.most_common(1)[0][0]
            if modal in register_ids:
                table[modal] = container_id
            else:  # a corpus label spelled without the org prefix
                near = [r for r in register_ids if r.endswith(modal) or modal.endswith(r)]
                if near:
                    table[near[0]] = container_id
        tables[server] = {"container_key": found.container_keys[0], "ids": table}
    return tables


def resolver_with_given_keys(server: str, rows: list, *, keys_given: bool = True) -> AssetResolver:
    """A resolver whose catalog is the given key table rather than a discovered one.

    With ``keys_given=False`` the table is withheld entirely, which is the honest
    deployment condition: nobody hands a gate a mapping from an opaque handle to
    a policy asset. What survives is the register, the tool schemas, and whatever
    the arguments happen to spell out.
    """
    container_key, keys = given_keys(server)
    if not keys_given:
        keys = {}
    bindings = {
        canonical_id(container_id): Binding(
            canonical_id(container_id), asset_id, "given", "key table supplied", 1.0
        )
        for asset_id, container_id in keys.items()
    }
    discovery = Discovery(
        container_keys=(normalize_key(container_key),),
        listing_tools=(),
        org_domains=("org.example",),
        bindings=bindings,
    )
    artifact = json.loads((CORPUS / f"{server}.json").read_text(encoding="utf-8"))
    operations = {
        tool: list(entry.get("atomic_ops") or [])
        for tool, entry in (artifact.get("tool_atomic_ops") or {}).items()
    }
    return AssetResolver(rows, discovery, operations, catalog_for(server))


def evaluate(server: str, variants: int, *, keys_given: bool = True) -> dict:
    rows = parse_asset_register(policy_for(server).text)
    tools = catalog_for(server)
    container_key, keys = given_keys(server)
    # Calls are generated identically either way; only what the resolver is told
    # differs, so the two arms are comparable call for call.
    calls = generate(server, rows, tools, keys, container_key, variants=variants)
    if keys_given:
        resolver = resolver_with_given_keys(server, rows)
    else:
        # Stateless: no table, no observation, nothing retained. The resolver
        # gets this call, the register and the tool schemas — that is all.
        artifact = json.loads((CORPUS / f"{server}.json").read_text(encoding="utf-8"))
        operations = {
            tool: list(entry.get("atomic_ops") or [])
            for tool, entry in (artifact.get("tool_atomic_ops") or {}).items()
        }
        resolver = AssetResolver(rows, None, operations, catalog_for(server))

    per_level: dict[str, dict] = {}
    cells: dict[tuple[str, str], dict] = {}
    for level, label in LEVELS.items():
        hits = sizes = exact = 0
        for call in calls:
            resolved = resolver.resolve(call.tool, call.args, level)
            found = call.target_asset in resolved.asset_ids
            hits += found
            sizes += len(resolved.asset_ids)
            exact += found and len(resolved.asset_ids) == 1
            if level == Level.EGRESS:
                cell = cells.setdefault(
                    (call.tool, call.target_asset),
                    {"n": 0, "hit": 0, "size": [], "shape": call.shape},
                )
                cell["n"] += 1
                cell["hit"] += found
                cell["size"].append(len(resolved.asset_ids))
        n = max(len(calls), 1)
        per_level[label] = {
            "recall": hits / n,
            "mean_set": sizes / n,
            "exact": exact / n,
        }

    failing = [
        {
            "tool": tool,
            "asset": asset,
            "recall": cell["hit"] / cell["n"],
            "mean_set": statistics.mean(cell["size"]),
            "shape": cell["shape"],
        }
        for (tool, asset), cell in sorted(cells.items())
        if cell["hit"] < cell["n"]
    ]
    return {
        "server": server,
        "calls": len(calls),
        "cells": len(cells),
        "register_rows": len(rows),
        "tools_in_catalog": len(tools),
        "given_keys": 0 if not keys_given else len(keys),
        "levels": per_level,
        "failing_cells": sorted(failing, key=lambda c: (c["recall"], c["tool"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", action="append")
    parser.add_argument("--no-keys", action="store_true",
                        help="withhold the key table — bind only from what arguments spell out")
    parser.add_argument("--held-out", action="store_true",
                        help="run the servers the rules were never developed against")
    parser.add_argument("--variants", type=int, default=10)
    parser.add_argument("--rebuild-keys", action="store_true",
                        help="recover the given key table from the labelled corpus and save it")
    parser.add_argument("--json", type=Path, default=V8_DIR / "synthetic_results.json")
    options = parser.parse_args()

    V8_DIR.mkdir(parents=True, exist_ok=True)
    if options.rebuild_keys:
        path = V8_DIR / "given_keys.json"
        path.write_text(json.dumps(build_given_keys(), indent=2), encoding="utf-8")
        print(f"wrote {path}")

    chosen = options.only or (HELD_OUT if options.held_out else SERVERS)
    results = [evaluate(s, options.variants, keys_given=not options.no_keys) for s in chosen]
    for result in results:
        print(f"\n{'=' * 78}\n{result['server']}  —  {result['cells']} tool x asset cells, "
              f"{result['calls']} generated calls, {result['given_keys']} keys given\n{'=' * 78}")
        header = f"{'level':16s} {'recall':>8s} {'exact':>8s} {'mean set':>9s}"
        print(f"{header}\n{'-' * len(header)}")
        for label, row in result["levels"].items():
            print(f"{label:16s} {row['recall']:8.3f} {row['exact']:8.3f} {row['mean_set']:9.2f}")
        if result["failing_cells"]:
            print(f"\ncells the resolver cannot reach ({len(result['failing_cells'])}):")
            for cell in result["failing_cells"]:
                print(f"  {cell['tool']:28s} {cell['asset']:26s} recall={cell['recall']:.2f} "
                      f"set={cell['mean_set']:.1f}  [{cell['shape']}]")
        else:
            print("\nevery cell reachable")
    options.json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nwrote {options.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
