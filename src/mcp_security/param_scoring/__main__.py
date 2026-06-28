"""CLI: derive per-tool parameter rubrics for a server and write the artifact.

    python -m mcp_security.param_scoring --kind filesystem --server fs:corp_filesystem
    python -m mcp_security.param_scoring --kind sqlite --server sqlite:cbg_sqlite

Tools come from the Excel catalog (same source as the scanner); the LLM derives
each tool's magnitude parameters and cutoffs from ``parameter-scoring.md``. Output:
``reports/scan/<server>_params.json`` (+ ``.md``). LLM-only — run on a GPU node.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from mcp_security.static_scoring.pipeline import LLMUnavailableError

from .derive import derive_rubrics

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAN_DIR = REPO_ROOT / "reports" / "scan"


def _to_markdown(server: str, rubrics: dict) -> str:
    lines = [f"# Parameter rubric — {server}", "",
             "LLM-derived per `docs/standards/parameter-scoring.md`. Each row is a "
             "magnitude-bearing input parameter and how its value bands.", ""]
    for tool, rub in rubrics.items():
        params = rub.parameters
        if not params:
            continue
        lines += [f"## `{tool}`", "", "| parameter | base | extract | cutoffs |",
                  "| --- | --- | --- | --- |"]
        for p in params:
            cut = " · ".join(f"≥{c.min:g}→{c.band}" for c in p.cutoffs) or (
                f"true→{p.when_true}" if p.when_true else "—")
            lines.append(f"| `{p.name}` | {p.base_rank} | {p.extract} | {cut} |")
        lines.append("")
    if all(not r.parameters for r in rubrics.values()):
        lines.append("_No magnitude-bearing parameters found for this server's tools._")
    return "\n".join(lines) + "\n"


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive input-parameter rubrics.")
    parser.add_argument("--kind", default="filesystem",
                        choices=["filesystem", "sqlite", "slack", "calendar", "github"])
    parser.add_argument("--server", required=True, help="server name (sets the artifact stem)")
    parser.add_argument("--tool-list", type=Path, help="explicit saved tools/list json")
    parser.add_argument("--scan-dir", type=Path, default=SCAN_DIR)
    parser.add_argument("--no-llm", action="store_true", help="offline: empty rubrics")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    # Source tools uniformly via the scanner's registry builder so declarative
    # kinds (calendar/github/slack) work too — their advertised tool set and input
    # schemas come from the registry, not a saved tools/list.
    from mcp_security.scanner.scan import build_registry

    tools = build_registry(args.kind, tool_list=args.tool_list).tools
    from .rubric import ToolRubric

    if args.no_llm:
        # Offline: emit empty rubrics so downstream is well-defined.
        rubrics: dict = {t.name: ToolRubric(t.name) for t in tools}
    else:
        # Non-strict: a tool whose rubric the model can't produce simply has no
        # magnitude parameters (an honest empty result, not a fabricated rubric) —
        # one bad tool must not abort the whole server's derivation.
        try:
            rubrics = derive_rubrics(tools, strict=False)
        except LLMUnavailableError as exc:
            print(f"parameter derivation aborted: {exc}", file=sys.stderr)
            return 2

    args.scan_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{_safe(args.server)}_params"
    payload = {"server": args.server, "kind": args.kind,
               "rubrics": {name: r.to_dict() for name, r in rubrics.items()}}
    (args.scan_dir / f"{stem}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (args.scan_dir / f"{stem}.md").write_text(_to_markdown(args.server, rubrics), encoding="utf-8")
    n_params = sum(len(r.parameters) for r in rubrics.values())
    print(f"Derived rubrics for {len(rubrics)} tools ({n_params} magnitude params) "
          f"-> {args.scan_dir / (stem + '.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
