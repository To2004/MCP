"""Re-assemble the v4 static arm from its own artifacts — no LLM call.

Tool impact in the static arm is deterministic (``static_impact.classify``), so a
rule change makes the stored artifacts stale even though nothing about the model
stages changed. This script re-runs the pipeline with the LLM stages replaced by
the values the original scan already recorded — verbatim blast (``blast_radius_raw``),
the inferred profile and the baselines — while impact is recomputed from the
current rules and every deterministic assembly pass (bulk twins, alias twins,
floors, roofs, bands) runs again on top.

The result is exactly what a re-scan would produce if the model answered
identically, which for a temperature-0 run it does. Artifacts are overwritten in
place and the previous impacts are reported as a diff.

    uv run python scripts/reassemble_static_arm.py                 # dry run
    uv run python scripts/reassemble_static_arm.py --write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scan_pure_desc import (  # noqa: E402
    SCHEMES,
    TARGETS,
    build_pure_registry,
    uncovered_tools,
)

from mcp_security.scanner.atomic_flags import enrich_scan  # noqa: E402
from mcp_security.scanner.render import matrix_csv, scan_to_markdown  # noqa: E402
from mcp_security.scanner.tool_list import load_tool_list  # noqa: E402
from mcp_security.static_scoring import pipeline as P  # noqa: E402
from mcp_security.static_scoring.server_profiles import profile_for  # noqa: E402

ARM = REPO_ROOT / "reports" / "experiments" / "v4" / "five_level_v2_pure_v4static"
IMPACT_MODE = "five_level_v2_v4_static"

# Fields the model produced that this re-assembly cannot regenerate: carried
# across verbatim so the refreshed artifact keeps its original provenance.
_CARRY = ("provenance", "blast_escape", "tool_profiles", "desc_scheme", "registry_source")


def _patch_llm_stages(old: dict) -> None:
    """Replace every model-backed stage with the values this scan already recorded."""
    P.StaticScorer.infer_domain = lambda self: dict(old["inferred_profile"])
    P.StaticScorer.build_baselines = lambda self: dict(old["baselines"])

    def _blast(self, sensitivity):  # noqa: ARG001 -- signature must match
        # blast_radius_raw is the model's verbatim answer, BEFORE any
        # deterministic pass; the pipeline re-applies those passes itself.
        self._blast_escape = old.get("blast_escape", {})
        return dict(old["blast_radius_raw"])

    P.StaticScorer.score_blast = _blast


def reassemble(stem: str, *, write: bool) -> tuple[int, list[str]]:
    """Rebuild one server's artifacts; returns (changed impacts, diff lines)."""
    old = json.loads((ARM / f"{stem}.json").read_text(encoding="utf-8"))
    target = next(t for t in TARGETS if t.stem == stem)
    scheme = old.get("desc_scheme", "full")

    raw = profile_for(target.server)
    profile = replace(raw, text=SCHEMES[scheme](raw.text))
    tools = load_tool_list(target.kind, path=target.catalog)
    registry = build_pure_registry(profile, tools, target.kind)

    _patch_llm_stages(old)
    table = P.build_static_table(
        registry,
        use_llm=False,
        strict=False,
        version=old["version"],
        impact_mode=IMPACT_MODE,
    )
    for key in _CARRY:
        if key in old:
            table[key] = old[key]
    table["server_kind"] = target.kind
    table["catalog_sha256"] = hashlib.sha256(target.catalog.read_bytes()).hexdigest()
    table["uncovered_tools"] = uncovered_tools(table)
    table["reassembled_from"] = {
        "note": "impact recomputed from current static rules; LLM stages replayed "
        "from the original scan's blast_radius_raw",
        "original_version": old["version"],
    }
    enrich_scan(table, registry.tools, use_llm=False)

    diff = [
        f"{name}: {old['tool_impact_raw'][name]} -> {new}"
        for name, new in table["tool_impact_raw"].items()
        if old["tool_impact_raw"].get(name) != new
    ]
    if write:
        (ARM / f"{stem}.json").write_text(json.dumps(table, indent=2), encoding="utf-8")
        (ARM / f"{stem}.md").write_text(
            scan_to_markdown(target.server, target.kind, table), encoding="utf-8"
        )
        (ARM / f"{stem}_matrix.csv").write_text(matrix_csv(table), encoding="utf-8")

    print(
        f"[{'write' if write else 'dry'}] {stem:22s} "
        f"impacts changed {len(diff):2d} | bands {old['band_distribution']} -> "
        f"{table['band_distribution']}"
    )
    for line in diff:
        print(f"      {line}")
    return len(diff), diff


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="overwrite the arm's artifacts")
    parser.add_argument("--only", default=None, help="comma-separated stems")
    args = parser.parse_args(argv)

    wanted = {s.strip() for s in args.only.split(",")} if args.only else None
    stems = [t.stem for t in TARGETS if (wanted is None or t.stem in wanted)]
    for stem in stems:
        if not (ARM / f"{stem}.json").exists():
            print(f"[skip] {stem}: no artifact in {ARM}")
            continue
        reassemble(stem, write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
