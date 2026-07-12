"""Static scan of the captured finance MCP tool catalogs (deterministic, no LLM).

Consumes the tool lists captured live through the MITM proxy
(``reports/scan_finance/tool_lists/<kind>.json``) and runs the project's
deterministic static-analysis layer over each:

* **atomic-op classification** — what each tool fundamentally *does*
  (READ/SEARCH/CREATE/MODIFY/DELETE/…) and how severe that verb is, from the
  atomic-op taxonomy (:mod:`mcp_security.scanner.atomic_flags`).
* **input-risk ranking** — which of each tool's parameters most amplifies risk
  (free-form query, bulk list, scope-widening flag, magnitude, …).

No LLM and no per-kind asset registry are required, so this runs anywhere (no
GPU). Writes ``reports/scan_finance/<kind>.json`` (full detail) and
``reports/scan_finance/<kind>.md`` (operator-readable summary).

Run:  uv run python scripts/scan_finance.py
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp_security.scanner.atomic_flags import classify_tools_atomic, rank_tool_inputs
from mcp_security.scanner.tool_list import load_tool_list

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIR = REPO_ROOT / "reports" / "scan_finance"
TOOL_LIST_DIR = SCAN_DIR / "tool_lists"


def scan_kind(kind: str) -> dict:
    """Build the static-scan table for one finance server kind."""
    tool_list_path = TOOL_LIST_DIR / f"{kind}.json"
    meta = json.loads(tool_list_path.read_text(encoding="utf-8"))
    tools = load_tool_list(kind, path=tool_list_path)

    atomic = classify_tools_atomic(tools)
    rankings = rank_tool_inputs(tools, use_llm=False)  # deterministic rules

    rows = []
    for tool in tools:
        flag = atomic[tool.name]
        inputs = rankings[tool.name]["inputs"]
        top_input = inputs[0] if inputs else None
        rows.append(
            {
                "tool": tool.name,
                "description": (tool.description or "").strip().replace("\n", " ")[:160],
                "primary_op": flag["primary_op"],
                "atomic_ops": flag["atomic_ops"],
                "severity": flag["severity"],
                "severity_label": flag["severity_label"],
                "op_source": flag["source"],
                "n_params": len(inputs),
                "top_input": top_input,
                "self_read_only_hint": tool.read_only_hint,
                "input_ranking": inputs,
            }
        )
    # Highest verb-severity first, then most parameters (larger attack surface).
    rows.sort(key=lambda r: (r["severity"], r["n_params"]), reverse=True)

    sev_hist: dict[str, int] = {}
    for r in rows:
        sev_hist[r["severity_label"] or "UNKNOWN"] = sev_hist.get(r["severity_label"] or "UNKNOWN", 0) + 1

    return {
        "server": meta.get("server", kind),
        "kind": kind,
        "provenance": "static-deterministic",
        "source": meta.get("source", ""),
        "n_tools": len(rows),
        "severity_histogram": sev_hist,
        "tools": rows,
    }


def to_markdown(table: dict) -> str:
    lines = [
        f"# Static scan — {table['server']} (`{table['kind']}`)",
        "",
        f"Source: {table['source']}",
        "",
        f"Method: deterministic static analysis (atomic-op taxonomy + input-risk rules), "
        f"no LLM. {table['n_tools']} tools.",
        "",
        "## Severity distribution (by primary atomic op)",
        "",
        "| Severity | Tools |",
        "| --- | --- |",
    ]
    for label, count in sorted(table["severity_histogram"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {label} | {count} |")
    lines += [
        "",
        "## Tools ranked by verb severity",
        "",
        "| # | Tool | Primary op | Sev | Top input-risk param | Params |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for i, r in enumerate(table["tools"], 1):
        ti = r["top_input"]
        ti_str = (
            f"`{ti['name']}` (r{ti['risk']}: {ti['reason'][:48]})" if ti else "—"
        )
        lines.append(
            f"| {i} | `{r['tool']}` | {r['primary_op']} ({r['severity_label']}) "
            f"| {r['severity']} | {ti_str} | {r['n_params']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not TOOL_LIST_DIR.exists():
        print(f"no captured finance tool lists at {TOOL_LIST_DIR} — "
              "run run_mitm_finance.py then save_finance_tool_lists.py first")
        return 1
    kinds = sorted(p.stem for p in TOOL_LIST_DIR.glob("*.json"))
    if not kinds:
        print(f"no *.json tool lists in {TOOL_LIST_DIR}")
        return 1

    for kind in kinds:
        table = scan_kind(kind)
        (SCAN_DIR / f"{kind}.json").write_text(
            json.dumps(table, indent=2), encoding="utf-8"
        )
        (SCAN_DIR / f"{kind}.md").write_text(to_markdown(table), encoding="utf-8")
        top = table["tools"][0] if table["tools"] else None
        top_str = f"top: {top['tool']} ({top['severity_label']})" if top else "no tools"
        print(f"{kind}: {table['n_tools']} tools scanned, {top_str} -> "
              f"reports/scan_finance/{kind}.json + .md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
