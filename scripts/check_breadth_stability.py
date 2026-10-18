"""Measure how much `kind`/`breadth` depend on the order inputs were presented in.

`check_rank_stability.py` found the old listwise `rank` question order-dependent (mean
Kendall's tau 0.538 under reversal, negative on the two largest tools) and the fix was to
stop asking for an ordering at all: `breadth` grades each input independently against a
fixed 1-5 rubric, never against its neighbours. That is a claim about what the RUBRIC asks
for, not about what the model actually does when it executes it — every input on a tool
still gets answered in one autoregressive reply, in list order, which is exactly the
mechanism that made `rank` position-dependent. This script runs the same forward/reversed
test `check_rank_stability.py` ran, on the same fields it did not check: `kind` and
`breadth`.

For each tool it asks twice, once with inputs in schema order and once reversed, and reports
per-parameter agreement: whether `kind` matches, whether `breadth` matches exactly, and by
how much `breadth` differs when it does not (a flip from 5 to 4 is a smaller failure than a
flip from 5 to 1).

    sbatch scripts/check_breadth_stability.sbatch
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
OUT = REPO / "reports" / "experiments" / "breadth_spec" / "breadth_stability.json"
# Same split `check_rank_stability.py` uses, for a direct comparison against its numbers.
IN_USE = ("github_real", "slack_real", "calendar_real")
HELD_OUT = ("filesystem", "sqlite", "maverick", "openbb", "sec_edgar", "yahoo_finance",
            "finance_tools")


def _entries(tool: ToolSpec, model: str) -> dict[str, dict]:
    """``{param_name: {"kind": ..., "breadth": ...}}`` for one tool."""
    out = breadth.classify_tool_breadth(tool, use_llm=True, model=model)
    return {i["name"]: {"kind": i["kind"], "breadth": i["breadth"]} for i in out["inputs"]}


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
    print(f"{'catalog':<18}{'tool':<28}{'inputs':>7}{'kind agree':>11}{'breadth agree':>14}",
          flush=True)
    for path in catalogs:
        tools = sorted(load_catalog(path),
                       key=lambda t: -len((t.input_schema or {}).get("properties") or {}))
        for tool in [t for t in tools
                     if len((t.input_schema or {}).get("properties") or {}) >= 3][:args.per_catalog]:
            forward = _entries(tool, args.model)
            backward = _entries(_reversed_schema(tool), args.model)
            names = sorted(set(forward) & set(backward))
            if not names or set(forward) != set(backward):
                print(f"{path.stem:<18}{tool.name:<28}{'':>7}{'n/a':>11}{'n/a':>14}", flush=True)
                continue

            kind_matches = sum(1 for n in names if forward[n]["kind"] == backward[n]["kind"])
            breadth_matches = sum(1 for n in names
                                  if forward[n]["breadth"] == backward[n]["breadth"])
            deltas = [abs(forward[n]["breadth"] - backward[n]["breadth"]) for n in names
                     if forward[n]["breadth"] != backward[n]["breadth"]]
            kind_rate = kind_matches / len(names)
            breadth_rate = breadth_matches / len(names)
            results.append({
                "catalog": path.stem, "tool": tool.name, "inputs": len(names),
                "kind_agree": round(kind_rate, 3), "breadth_agree": round(breadth_rate, 3),
                "breadth_deltas": deltas,
                "forward": {n: forward[n] for n in names},
                "backward": {n: backward[n] for n in names},
            })
            print(f"{path.stem:<18}{tool.name:<28}{len(names):>7}{kind_rate:>11.2f}"
                  f"{breadth_rate:>14.2f}", flush=True)

    kind_rates = [r["kind_agree"] for r in results]
    breadth_rates = [r["breadth_agree"] for r in results]
    all_deltas = [d for r in results for d in r["breadth_deltas"]]
    summary = {
        "tools": len(results),
        "mean_kind_agree": round(statistics.fmean(kind_rates), 3) if kind_rates else None,
        "mean_breadth_agree": round(statistics.fmean(breadth_rates), 3) if breadth_rates else None,
        "median_breadth_agree": round(statistics.median(breadth_rates), 3) if breadth_rates else None,
        "identical": sum(1 for r in results if r["breadth_agree"] == 1.0),
        "mean_breadth_delta_when_disagreeing": (
            round(statistics.fmean(all_deltas), 3) if all_deltas else None),
        "results": results,
    }
    OUT.write_text(json.dumps(summary, indent=1))
    print(f"\n{len(results)} tools  mean kind agree {summary['mean_kind_agree']}  "
          f"mean breadth agree {summary['mean_breadth_agree']}  "
          f"median {summary['median_breadth_agree']}  "
          f"identical {summary['identical']}  "
          f"mean |delta| when wrong {summary['mean_breadth_delta_when_disagreeing']}",
          flush=True)
    print(f"written to {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
