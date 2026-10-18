"""Render derived input typings as a per-server markdown table.

Reads ``reports/input_types/<server>*.json`` (shards merge) and writes
``reports/input_types/INPUT_TYPES.md``: one row per parameter with the fields
the model chose to fill, plus coverage counts.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIR = REPO / "reports" / "input_types"
SERVERS = ("github", "slack", "calendar")


def _cell(value: object) -> str:
    if value in (None, "", [], {}):
        return "—"
    if isinstance(value, dict):
        return "; ".join(f"{k}: {v}" for k, v in value.items() if v not in (None, "", []))
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(f"{item.get('at', '?')}→{item.get('means', '')}")
            else:
                parts.append(str(item))
        return " · ".join(parts)
    return str(value)


def _load(server: str) -> tuple[list[dict], list[str]]:
    tools, failed = [], []
    for path in sorted(DIR.glob(f"{server}*.json")):
        blob = json.loads(path.read_text())
        tools.extend(blob.get("tools", []))
        failed.extend(blob.get("failed", []))
    return tools, failed


def main() -> int:
    lines = ["# Derived Tool Input Types", "",
             "Produced by `scripts/derive_input_types.py` from",
             "`docs/standards/input-typing.md` (Qwen2.5:32b, greedy, seed 0).", ""]
    for server in SERVERS:
        tools, failed = _load(server)
        if not tools and not failed:
            continue
        kinds: Counter[str] = Counter()
        n_params = 0
        lines += [f"## {server}", ""]
        lines += ["| tool | parameter | kind | population | limits / measures | edges | stability | prose | ev |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for tool in sorted(tools, key=lambda t: t.get("tool_name", "")):
            for p in tool.get("parameters", []):
                n_params += 1
                kinds[str(p.get("kind", "?"))] += 1
                size = _cell(p.get("limits")) if p.get("limits") else _cell(
                    " ".join(x for x in [str(p.get("measures") or ""), str(p.get("unit") or "")] if x).strip())
                lines.append(
                    f"| `{tool.get('tool_name')}` | `{p.get('name')}` | {_cell(p.get('kind'))} "
                    f"| {_cell(p.get('population'))} | {size} | {_cell(p.get('edges'))} "
                    f"| {_cell(p.get('stability'))} | {'yes' if p.get('prose') else '—'} "
                    f"| {_cell(p.get('evidence'))} |")
        declared = sum(t.get("declared_parameters", 0) for t in tools)
        lines += ["", f"{len(tools)} tool(s) typed, {n_params} parameter(s) described "
                      f"against {declared} declared.",
                  f"Failed: {', '.join(failed) if failed else 'none'}.", "",
                  "Kinds the model chose: "
                  + ", ".join(f"`{k}` ×{v}" for k, v in kinds.most_common()) + ".", ""]
    out = DIR / "INPUT_TYPES.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
