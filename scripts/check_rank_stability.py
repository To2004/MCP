"""Measure how much the breadth ranking depends on the order inputs were presented in.

Position bias in listwise LLM ranking is architectural — causal attention and positional
encodings couple a candidate's score to where it sat in the prompt — so a ranking is only
trustworthy to the extent it survives being asked again with the candidates shuffled.
The published mitigation is repetition over permutations with aggregation, which costs a
model call per repeat; this script measures the bias instead of paying to suppress it, so
the size of the problem is known before anyone decides whether to pay.

For each tool it asks twice, once with the inputs in schema order and once reversed, and
reports Kendall's tau between the two rankings. Tau of 1.0 means the presentation order
did not matter at all; 0.0 means the answer was independent of the tool's actual inputs.

    sbatch scripts/check_rank_stability.sbatch
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

from mcp_security.scanner import breadth
from mcp_security.static_scoring.registry import ToolSpec

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "reports" / "experiments" / "breadth_spec" / "rank_stability.json"
#: The servers the ranking is actually used on. Prompt wording was tuned against these,
#: which would disqualify them for a *coverage* claim — but this measures self-consistency
#: under reordering, and a prompt cannot be fitted to be position-invariant, so the
#: contamination that matters elsewhere does not apply here.
IN_USE = ("github_real", "slack_real", "calendar_real")
HELD_OUT = ("filesystem", "sqlite", "maverick", "openbb", "sec_edgar", "yahoo_finance",
            "finance_tools")


def kendall_tau(first: list[str], second: list[str]) -> float | None:
    """Rank correlation between two orderings of the same items, in ``[-1, 1]``."""
    if len(first) < 2:
        return None
    position = {name: index for index, name in enumerate(second)}
    concordant = discordant = 0
    for i in range(len(first)):
        for j in range(i + 1, len(first)):
            left = position[first[i]] - position[first[j]]
            concordant += left < 0
            discordant += left > 0
    total = concordant + discordant
    return (concordant - discordant) / total if total else None


def _order(tool: ToolSpec, model: str) -> list[str]:
    """The model's ranking of one tool's inputs, as a list of names."""
    entry = breadth.classify_tool_breadth(tool, use_llm=True, model=model)
    ranked = [i for i in entry["inputs"] if i.get("rank")]
    return [i["name"] for i in sorted(ranked, key=lambda i: i["rank"])]


def _reversed_schema(tool: ToolSpec) -> ToolSpec:
    """The same tool with its properties presented in the opposite order."""
    schema = dict(tool.input_schema or {})
    props = schema.get("properties") or {}
    schema["properties"] = dict(reversed(list(props.items())))
    return ToolSpec(name=tool.name, description=tool.description, input_schema=schema)


def load_catalog(path: Path) -> list[ToolSpec]:
    raw = json.loads(path.read_text())
    entries = raw["tools"] if isinstance(raw, dict) and "tools" in raw else raw
    return [ToolSpec(name=e["name"], description=e.get("description", "") or "",
                     input_schema=e.get("input_schema") or e.get("inputSchema") or {})
            for e in entries]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen2.5:32b")
    parser.add_argument("--held-out", action="store_true",
                        help="the catalogs not in use, to check the finding generalises")
    parser.add_argument("--per-catalog", type=int, default=8,
                        help="tools sampled per catalog (those with the most inputs)")
    args = parser.parse_args(argv)

    wanted = HELD_OUT if args.held_out else IN_USE
    catalogs = [p for p in
                sorted((REPO / "reports" / "tool_lists").glob("*.json"))
                + sorted((REPO / "reports" / "scan_finance" / "tool_lists").glob("*.json"))
                if any(p.stem.startswith(h) for h in wanted)]
    random.Random(20260814).shuffle(catalogs)

    results: list[dict] = []
    print(f"{'catalog':<18}{'tool':<28}{'inputs':>7}{'tau':>7}", flush=True)
    for path in catalogs:
        tools = sorted(load_catalog(path),
                       key=lambda t: -len((t.input_schema or {}).get("properties") or {}))
        for tool in [t for t in tools
                     if len((t.input_schema or {}).get("properties") or {}) >= 3][:args.per_catalog]:
            forward = _order(tool, args.model)
            backward = _order(_reversed_schema(tool), args.model)
            if not forward or set(forward) != set(backward):
                print(f"{path.stem:<18}{tool.name:<28}{'':>7}{'n/a':>7}", flush=True)
                continue
            tau = kendall_tau(forward, backward)
            if tau is None:
                print(f"{path.stem:<18}{tool.name:<28}{len(forward):>7}{'n/a':>7}", flush=True)
                continue
            results.append({"catalog": path.stem, "tool": tool.name,
                            "inputs": len(forward), "tau": tau,
                            "forward": forward, "backward": backward})
            print(f"{path.stem:<18}{tool.name:<28}{len(forward):>7}{tau:>7.2f}", flush=True)

    taus = [r["tau"] for r in results if r["tau"] is not None]
    summary = {
        "tools": len(results),
        "mean_tau": round(statistics.fmean(taus), 3) if taus else None,
        "median_tau": round(statistics.median(taus), 3) if taus else None,
        "identical": sum(1 for r in results if r["forward"] == r["backward"]),
        "results": results,
    }
    OUT.write_text(json.dumps(summary, indent=1))
    print(f"\n{len(results)} tools  mean tau {summary['mean_tau']}  "
          f"median {summary['median_tau']}  identical orderings {summary['identical']}",
          flush=True)
    print(f"written to {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
