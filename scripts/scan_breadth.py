"""Run the scanner's breadth pass over every saved tool catalog, with the model.

``tool_breadth`` says which of a tool's inputs decide how *much* a call covers. The
schema settles what it states as structure; everything else needs meaning, which is what
the local model supplies. Slack declares all 63 of its inputs as plain strings, so
without the model pass that server resolves nothing at all — this is a required scan
step, not an optional enrichment.

Writes one file per catalog to ``reports/experiments/breadth_spec/<server>_scan.json``.
Existing scan artifacts are left untouched; merging is a separate, explicit step.

    sbatch scripts/scan_breadth.sbatch
    uv run python scripts/scan_breadth.py --catalog reports/tool_lists/slack_real.json
"""

from __future__ import annotations

import argparse
import collections
import json
import time
from pathlib import Path

from mcp_security.scanner.breadth import classify_breadth
from mcp_security.static_scoring.registry import ToolSpec

REPO = Path(__file__).resolve().parents[1]
#: The three servers the runtime is built and evaluated against. The other catalogs on
#: disk are useful for checking the classifier generalises, but scanning them every time
#: costs GPU minutes for tools nothing consumes.
IN_USE = ("github_real", "slack_real", "calendar_real")
CATALOGS = [REPO / "reports" / "tool_lists" / f"{stem}.json" for stem in IN_USE]
ALL_CATALOGS = sorted((REPO / "reports" / "tool_lists").glob("*.json")) + sorted(
    (REPO / "reports" / "scan_finance" / "tool_lists").glob("*.json")
)
OUT = REPO / "reports" / "experiments" / "breadth_spec"


def load_tools(path: Path) -> list[ToolSpec]:
    """Every tool in a saved catalog, as the scanner's registry sees it."""
    raw = json.loads(path.read_text())
    entries = raw["tools"] if isinstance(raw, dict) and "tools" in raw else raw
    return [
        ToolSpec(
            name=entry["name"],
            description=entry.get("description", "") or "",
            input_schema=entry.get("input_schema") or entry.get("inputSchema") or {},
        )
        for entry in entries
    ]


def run_catalog(path: Path, *, use_llm: bool, model: str | None) -> dict:
    tools = load_tools(path)
    started = time.monotonic()
    breadth = classify_breadth(tools, use_llm=use_llm, model=model)
    elapsed = time.monotonic() - started

    kinds: collections.Counter = collections.Counter()
    sources: collections.Counter = collections.Counter()
    for entry in breadth.values():
        for item in entry["inputs"]:
            kinds[item["kind"]] += 1
            sources[item["source"]] += 1
    return {
        "server": path.stem,
        "model": model if use_llm else None,
        "tools": breadth,
        "kinds": dict(kinds),
        "sources": dict(sources),
        "seconds": round(elapsed, 1),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, action="append",
                        help="one catalog to scan (repeatable); default is all saved catalogs")
    parser.add_argument("--model", default="qwen2.5:32b")
    parser.add_argument("--all", action="store_true",
                        help="every catalog on disk, not just the three servers in use")
    parser.add_argument("--no-llm", action="store_true",
                        help="structure only — leaves everything the schema cannot state unresolved")
    args = parser.parse_args(argv)

    OUT.mkdir(parents=True, exist_ok=True)
    catalogs = args.catalog or (ALL_CATALOGS if args.all else CATALOGS)
    header = f"{'catalog':<24}{'tools':>6}{'inputs':>8}{'resolved':>10}{'unresolved':>12}{'sec':>7}"
    print(header, flush=True)
    unclassified_total = 0
    for path in catalogs:
        result = run_catalog(path, use_llm=not args.no_llm, model=args.model)
        total = sum(result["kinds"].values())
        # Count provenance, not kind: an input nobody classified now reads `none`, so
        # counting kinds would report a total model failure as a clean sheet.
        unclassified = result["sources"].get("unclassified", 0)
        unclassified_total += unclassified
        print(f"{path.stem:<24}{len(result['tools']):>6}{total:>8}"
              f"{total - unclassified:>10}{unclassified:>12}{result['seconds']:>7.0f}", flush=True)
        (OUT / f"{path.stem}_scan.json").write_text(json.dumps(result, indent=1))

    print(f"\nwritten to {OUT}/", flush=True)
    if not args.no_llm and unclassified_total:
        print(f"FAILED: {unclassified_total} inputs unclassified — the model did not answer "
              f"for them. A scan that silently skips the model is worse than no scan.",
              flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
