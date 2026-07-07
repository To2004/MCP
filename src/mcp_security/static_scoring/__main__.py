"""CLI: build static risk tables for MCP servers.

Examples
--------
Score one built-in registry or demo, offline::

    python -m mcp_security.static_scoring --kind filesystem --no-llm
    python -m mcp_security.static_scoring --kind cbg_sqlite --no-llm

Score *every* demo server into one combined results file::

    python -m mcp_security.static_scoring --all              # model-reviewed
    python -m mcp_security.static_scoring --all --no-llm     # deterministic

With the local model serving (e.g. on a GPU node) every primitive is the model's
own judgement; bands are the deterministic band_label. The judge cross-check does
not run in a scan (it is evaluation-only), so ``judge_ran`` is always false here.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path

from .pipeline import band_label, build_static_table
from .registry import (
    DEMO_SERVERS,
    DEMO_SERVERS_TAKE2,
    LOADERS,
    ServerRegistry,
    load_registry_from_json,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT_DIR = REPO_ROOT / "reports" / "samples"
COMBINED_OUT = DEFAULT_OUT_DIR / "all_static_tables.json"

_BAND_ORDER = ("low", "medium", "high", "critical")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--kind", choices=sorted(LOADERS), help="One built-in registry/demo")
    source.add_argument("--registry", type=Path, help="Path to a registry JSON file")
    source.add_argument("--all", action="store_true", help="Score every demo into one file")
    source.add_argument(
        "--combine",
        type=Path,
        nargs="+",
        metavar="PART.json",
        help="Merge per-server table JSONs (from parallel jobs) into one combined file",
    )
    source.add_argument(
        "--reband",
        type=Path,
        metavar="COMBINED.json",
        help="Recompute bands on an existing combined file with the current policy (no model)",
    )
    parser.add_argument("--out", type=Path, help="Output path (default under reports/samples/)")
    parser.add_argument("--no-llm", action="store_true", help="Deterministic only; skip the model")
    parser.add_argument(
        "--take2",
        action="store_true",
        help="take2: filesystem assets are per-file FULL PATHS, not file types",
    )
    return parser.parse_args(argv)


def _version(take2: bool = False) -> str:
    tag = "take2" if take2 else "take1"
    return f"static-{tag}-{datetime.date.today().isoformat()}"


def _score(registry: ServerRegistry, *, use_llm: bool, version: str) -> dict:
    logger.info(
        "Scoring %s (kind=%s): %d tools × %d assets%s",
        registry.server,
        registry.kind,
        len(registry.tools),
        len(registry.assets),
        "" if use_llm else " [offline]",
    )
    return build_static_table(registry, use_llm=use_llm, version=version)


def _worst_band(table: dict) -> str:
    """The single most severe band anywhere in a table's cell matrix."""
    worst = "low"
    for row in table["bands"].values():
        for band in row.values():
            if _BAND_ORDER.index(band) > _BAND_ORDER.index(worst):
                worst = band
    return worst


def _digest(name: str, table: dict) -> dict:
    """One compact per-server row for the combined file's index."""
    cs = table["crosscheck_summary"]
    crit = [
        f"{asset} · {tool}"
        for asset, row in table["bands"].items()
        for tool, band in row.items()
        if band == "critical"
    ]
    return {
        "name": name,
        "server": table["server"],
        "kind": table["mcp_kind"],
        "model_reviewed": table["model_reviewed"],
        "worst_band": _worst_band(table),
        "n_tools": len(table["tool_impact"]),
        "n_assets": len(table["asset_sensitivity"]),
        "critical_cells": crit,
        "judge_ran": cs.get("judge_ran", False),
        "overridden": cs.get("overridden", 0),
        "flagged_for_review": cs.get("flagged_for_review", 0),
    }


def _assemble_combined(tables: dict[str, dict], version: str, out: Path) -> int:
    """Write the combined file from a {name: table} mapping and log a summary."""
    index = [_digest(name, table) for name, table in tables.items()]
    combined = {
        "version": version,
        "generated_servers": len(tables),
        "model_reviewed": all(t["model_reviewed"] for t in tables.values()),
        "index": index,
        "totals": {
            "critical_cells": sum(len(d["critical_cells"]) for d in index),
            "judge_overrides": sum(d["overridden"] for d in index),
        },
        "tables": tables,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")

    logger.info("=" * 70)
    logger.info("Wrote combined results → %s (%d servers)", out, len(tables))
    for d in index:
        logger.info(
            "  %-18s kind=%-22s worst=%-8s critical_cells=%-2d overrides=%d",
            d["name"],
            d["kind"],
            d["worst_band"],
            len(d["critical_cells"]),
            d["overridden"],
        )
    return 0


def _run_all(use_llm: bool, out: Path, *, take2: bool) -> int:
    version = _version(take2)
    servers = DEMO_SERVERS_TAKE2 if take2 else DEMO_SERVERS
    tables = {
        name: _score(loader(), use_llm=use_llm, version=version) for name, loader in servers.items()
    }
    return _assemble_combined(tables, version, out)


def _reband_table(table: dict) -> dict:
    """Recompute a single table's bands + distribution with the current policy.

    Pure post-processing on the stored scores — no model call — so a band-policy
    change can be applied to existing model-reviewed results without re-running.
    """
    sens = table["asset_sensitivity"]
    imp = table["tool_impact"]
    blast = table["blast_radius"]
    bands = {
        a: {tool: band_label(sens[a], blast[f"{tool}|{a}"], imp[tool]) for tool in row}
        for a, row in table["cells"].items()
    }
    table["bands"] = bands
    dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for row in bands.values():
        for b in row.values():
            dist[b] += 1
    table["band_distribution"] = dist
    return table


def _reband(path: Path, out: Path) -> int:
    """Re-band every table in a combined file and rewrite the index/totals."""
    c = json.loads(path.read_text(encoding="utf-8"))
    tables = {name: _reband_table(t) for name, t in c["tables"].items()}
    return _assemble_combined(tables, c.get("version", _version()), out)


def _combine_parts(parts: list[Path], out: Path) -> int:
    """Aggregate per-server table JSONs (from parallel GPU jobs) into one file.

    Each part is a single-server table whose filename stem is its demo name.
    No GPU needed — this just merges the fan-out results on the login node.
    """
    tables: dict[str, dict] = {}
    for path in sorted(parts):
        tables[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    if not tables:
        logger.error("No part files matched; nothing to combine.")
        return 1
    version = next(iter(tables.values())).get("version", _version())
    return _assemble_combined(tables, version, out)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse_args(argv)
    use_llm = not args.no_llm

    suffix = "_take2" if args.take2 else ""
    if args.all:
        default = COMBINED_OUT.with_name(f"all_static_tables{suffix}.json")
        return _run_all(use_llm, args.out or default, take2=args.take2)

    if args.combine:
        default = COMBINED_OUT.with_name(f"all_static_tables{suffix}.json")
        return _combine_parts(args.combine, args.out or default)

    if args.reband:
        return _reband(args.reband, args.out or args.reband)

    if args.kind:
        # take2 swaps in per-file filesystem loaders; sqlite/slack are unchanged.
        loader = (DEMO_SERVERS_TAKE2 if args.take2 else LOADERS).get(args.kind) or LOADERS[
            args.kind
        ]
        registry = loader()
        default_name = f"{args.kind}{suffix}_static_table.json"
    else:
        registry = load_registry_from_json(args.registry)
        default_name = f"{registry.kind}{suffix}_static_table.json"

    table = _score(registry, use_llm=use_llm, version=_version(args.take2))
    out_path = args.out or (DEFAULT_OUT_DIR / default_name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")

    cs = table["crosscheck_summary"]
    logger.info(
        "Wrote %s — model_reviewed=%s, judge_ran=%s, %d flagged / %d records",
        out_path,
        table["model_reviewed"],
        cs.get("judge_ran", False),
        cs.get("flagged_for_review", 0),
        cs.get("total_records", 0),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
