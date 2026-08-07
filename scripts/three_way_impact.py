"""Compare the three independent tool-impact methods over the same catalogs.

    A  LLM         the model reads the tool JSON and answers the 1-5 ladder
    B  static      `static_scoring.static_impact` — tiered verb patterns over prose
    C  atomic      `atomic_scanner` — parse to atomic operations, take the max

The three share no machinery: A is a language model, B matches tier patterns in
the description, C tokenises the name into verb+object and looks up an operation
taxonomy. Where all three land on the same tier, that tier is about as close to
ground truth as this framework gets without human labelling. Where they split,
the split localises the problem — and which pair agrees says which signal the
disagreement lives in.

    uv run python scripts/three_way_impact.py
    uv run python scripts/three_way_impact.py --group finance

Writes reports/experiments/v4/five_level_v2_pure_v4_toolscanner/.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scan_pure_desc import TARGETS  # noqa: E402

from mcp_security.atomic_scanner import classify_all as atomic_all  # noqa: E402
from mcp_security.scanner.tool_list import load_tool_list  # noqa: E402
from mcp_security.static_scoring import static_impact  # noqa: E402

OUT_DIR = REPO_ROOT / "reports" / "experiments" / "v4" / "five_level_v2_pure_v4_toolscanner"
LLM_ARM = REPO_ROOT / "reports" / "experiments" / "v4" / "five_level_v2_pure_v4"
FINANCE = REPO_ROOT / "reports" / "scan_finance" / "tool_lists"
REFERENCE = REPO_ROOT / "src" / "mcp_security" / "atomic_ops" / "data" / "tool_lists"


def _catalogs(group: str) -> list[tuple[str, Path, str]]:
    if group == "live":
        return [(t.stem, t.catalog, t.kind) for t in TARGETS]
    root = FINANCE if group == "finance" else REFERENCE
    return [(p.stem, p, "generic") for p in sorted(root.glob("*.json"))]


def _llm_impacts(stem: str) -> dict[str, int]:
    """The LLM arm's per-tool impact, when a scan exists for this server."""
    path = LLM_ARM / f"{stem}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("tool_impact_raw", {})


def collect(group: str) -> list[dict]:
    """One record per tool: the three verdicts plus the atomic operation set."""
    rows: list[dict] = []
    for stem, path, kind in _catalogs(group):
        tools = load_tool_list(kind, path=path)
        statics = static_impact.classify_all(tools)
        atomics = atomic_all(tools)
        llm = _llm_impacts(stem)
        for tool in tools:
            atomic = atomics[tool.name]
            rows.append(
                {
                    "server": stem,
                    "tool": tool.name,
                    "llm": llm.get(tool.name),
                    "static": statics[tool.name].tool_impact,
                    "atomic": atomic.tool_impact,
                    "ops": sorted(atomic.operations),
                    "max_op": atomic.max_op,
                    "atomic_source": atomic.source,
                    "static_why": statics[tool.name].reasoning.replace(
                        "deterministic ladder: ", ""
                    ),
                }
            )
    return rows


def _pair_agreement(rows: list[dict], left: str, right: str) -> tuple[int, int, float]:
    both = [r for r in rows if r[left] is not None and r[right] is not None]
    same = sum(1 for r in both if r[left] == r[right])
    within1 = sum(1 for r in both if abs(r[left] - r[right]) <= 1)
    return same, len(both), (within1 / len(both) if both else 0.0)


def _consensus(row: dict) -> tuple[int | None, str]:
    """Majority tier across the available methods, and how strong it was."""
    votes = [row[k] for k in ("llm", "static", "atomic") if row[k] is not None]
    if not votes:
        return None, "none"
    counts = collections.Counter(votes)
    tier, n = counts.most_common(1)[0]
    if len(votes) == 3:
        return tier, {3: "unanimous", 2: "majority", 1: "three-way split"}[n]
    return (tier, "agreed") if n == 2 else (max(votes), "split (2 methods)")


def report(group: str, rows: list[dict]) -> Path:
    methods = [m for m in ("llm", "static", "atomic") if any(r[m] is not None for r in rows)]
    lines = [
        f"# Three-way tool impact — {group} ({len(rows)} tools)",
        "",
        "Three independent methods over the same catalogs:",
        "",
        "| | method | signal it reads |",
        "|---|---|---|",
        "| **A** | LLM | the model reads the tool JSON and answers the ladder |",
        "| **B** | static | tiered verb patterns over name + description prose |",
        "| **C** | atomic | name tokenised to verb+object, mapped to an operation "
        "taxonomy, tier = max |",
        "",
        "They share no pattern table, so agreement is corroboration rather than a "
        "shared blind spot.",
        "",
        "## Pairwise agreement",
        "",
        "| pair | exact | of | % | within ±1 |",
        "|---|--:|--:|--:|--:|",
    ]
    for left, right in (("llm", "static"), ("llm", "atomic"), ("static", "atomic")):
        if left not in methods or right not in methods:
            continue
        same, total, within = _pair_agreement(rows, left, right)
        lines.append(
            f"| {left} vs {right} | {same} | {total} | {same / total:.0%} | {within:.0%} |"
        )

    strength = collections.Counter(_consensus(r)[1] for r in rows)
    lines += [
        "",
        "## Consensus",
        "",
        f"{dict(strength)}",
        "",
        "## Where the methods disagree",
        "",
        "| server | tool | LLM | static | atomic | max op | atomic ops |",
        "|---|---|:--:|:--:|:--:|---|---|",
    ]
    disagreements = [
        r for r in rows if len({r[m] for m in methods if r[m] is not None}) > 1
    ]
    for r in sorted(disagreements, key=lambda r: (r["server"], r["tool"])):
        llm = r["llm"] if r["llm"] is not None else "—"
        lines.append(
            f"| {r['server']} | `{r['tool']}` | {llm} | {r['static']} | {r['atomic']} | "
            f"`{r['max_op']}` | {', '.join(r['ops'])} |"
        )

    lines += [
        "",
        f"{len(disagreements)} of {len(rows)} tools have a disagreement "
        f"({len(disagreements) / len(rows):.0%}).",
        "",
        "## Atomic operation census",
        "",
        "| operation | tools | tier |",
        "|---|--:|--:|",
    ]
    from mcp_security.atomic_scanner import ladder_tier

    census = collections.Counter(op for r in rows for op in r["ops"])
    for op, n in census.most_common():
        lines.append(f"| `{op}` | {n} | {ladder_tier(op)} |")
    lines.append("")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{group}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    (OUT_DIR / f"{group}.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", default=None, choices=["live", "finance", "reference"])
    args = parser.parse_args(argv)
    for group in [args.group] if args.group else ["live", "finance", "reference"]:
        rows = collect(group)
        path = report(group, rows)
        methods = [m for m in ("llm", "static", "atomic") if any(r[m] is not None for r in rows)]
        summary = []
        for left, right in (("llm", "static"), ("llm", "atomic"), ("static", "atomic")):
            if left in methods and right in methods:
                same, total, within = _pair_agreement(rows, left, right)
                summary.append(f"{left[:3]}/{right[:3]} {same}/{total}={same / total:.0%}")
        print(f"[ok] {group:10s} {len(rows):3d} tools  " + "  ".join(summary) + f"  -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
