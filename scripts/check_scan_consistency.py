"""Deterministic consistency checks over scan artifacts — no LLM, no ground truth.

Encodes invariants a correct scan must satisfy regardless of domain. Violations
are not automatically "wrong" — they are *review targets*: cells where the model's
judgement conflicts with the scoring rules' own logic. Run after any scan to get
an improvement worklist.

Invariants:
  I1  read-only tool (impact 1) must not have blast 5 on a SINGLE-ITEM asset —
      blast 5 for reads is legitimate only via the fan-out clause (container
      sweep of a dangerous class, 4 + 1 escalation).
  I2  metadata-only tool (info/stat/describe/list-names) blast <= 3 on any asset.
  I3  single-item asset (not a container/scope) blast <= 2 for read tools —
      the fan-out belongs to the container's cell.
  I4  dangerous-asset escalation is monotone: for the same tool, blast on a
      sensitivity-5 asset >= blast on a sensitivity<=2 asset of the same shape
      (container vs item), minus 1 tolerance.
  I5  cells formula holds: score == sensitivity * blast * impact (tolerance 1e-6).

Usage:
    python scripts/check_scan_consistency.py [--scan-dir reports/scan] [stems...]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Tool-name hints for metadata-only operations (reveal structure, not contents).
_METADATA_HINTS = (
    "get_file_info", "describe", "list_allowed", "freebusy", "get_me",
    "list_tables", "get_user_profile", "colors",
)
_READ_HINTS = ("read", "get", "list", "search", "describe", "tree", "info", "fetch", "download")


def _is_metadata(tool: str) -> bool:
    t = tool.lower()
    return any(h in t for h in _METADATA_HINTS)


def _is_readish(tool: str, impact: int) -> bool:
    return impact == 1 or any(h in tool.lower() for h in _READ_HINTS)


def _is_container(asset: str) -> bool:
    """A scope/container asset: a directory path, root, or a bare collection name."""
    return asset.endswith("/") or asset == "/" or ("." not in asset.rsplit("/", 1)[-1])


def check_scan(path: Path) -> list[dict]:
    d = json.loads(path.read_text("utf-8"))
    impacts: dict[str, int] = d.get("tool_impact", {})
    sens: dict[str, int] = d.get("asset_sensitivity", {})
    blast: dict[str, int] = d.get("blast_radius", {})
    cells: dict[str, dict[str, float]] = d.get("cells", {})
    findings: list[dict] = []

    def flag(inv: str, key: str, detail: str) -> None:
        findings.append({"scan": path.stem, "invariant": inv, "cell": key, "detail": detail})

    for key, b in blast.items():
        tool, _, asset = key.partition("|")
        imp = impacts.get(tool)
        if imp is None or asset not in sens:
            continue
        # I1: read blast 5 is only the container fan-out escalation, never an item.
        if imp == 1 and b == 5 and not _is_container(asset):
            flag("I1", key, "impact 1 (read-only) with blast 5 on a single item")
        # I2: metadata ops reveal structure, not contents.
        if _is_metadata(tool) and b > 3:
            flag("I2", key, f"metadata-only tool with blast {b}")
        # I3: single-item assets cannot be swept by reads.
        if not _is_container(asset) and _is_readish(tool, imp) and b > 2:
            flag("I3", key, f"read of a single-item asset with blast {b}")

    # I4: dangerous-asset escalation monotonicity per tool (same asset shape).
    for tool in impacts:
        for shape, pick in (("container", True), ("item", False)):
            hi = [blast[f"{tool}|{a}"] for a, s in sens.items()
                  if s == 5 and _is_container(a) == pick and f"{tool}|{a}" in blast]
            lo = [blast[f"{tool}|{a}"] for a, s in sens.items()
                  if s <= 2 and _is_container(a) == pick and f"{tool}|{a}" in blast]
            if hi and lo and max(hi) + 1 < max(lo):
                flag("I4", f"{tool}|<{shape}>",
                     f"max blast on sens-5 {shape}s ({max(hi)}) < max on sens<=2 ({max(lo)})")

    # I5: formula integrity.
    for asset, row in cells.items():
        for tool, score in row.items():
            key = f"{tool}|{asset}"
            if tool in impacts and asset in sens and key in blast:
                expect = sens[asset] * blast[key] * impacts[tool]
                if abs(score - expect) > 1e-6:
                    flag("I5", key, f"score {score} != s*b*i {expect}")
    return findings


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stems", nargs="*", help="scan stems (default: all non-params scans)")
    ap.add_argument("--scan-dir", type=Path, default=REPO / "reports" / "scan")
    args = ap.parse_args()

    paths = (
        [args.scan_dir / f"{s}.json" for s in args.stems]
        if args.stems
        else [p for p in sorted(args.scan_dir.glob("*.json")) if not p.stem.endswith("_params")]
    )
    all_findings: list[dict] = []
    for p in paths:
        if p.exists():
            all_findings.extend(check_scan(p))

    by_inv: dict[str, int] = {}
    for f in all_findings:
        by_inv[f["invariant"]] = by_inv.get(f["invariant"], 0) + 1
    print(f"{len(all_findings)} findings across {len(paths)} scans — {by_inv or 'CLEAN'}")
    for f in all_findings[:40]:
        print(f"  [{f['invariant']}] {f['scan']}: {f['cell']} — {f['detail']}")
    if len(all_findings) > 40:
        print(f"  ... and {len(all_findings) - 40} more")


if __name__ == "__main__":
    main()
