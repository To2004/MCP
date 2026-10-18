"""Render derived input typings as one compact table per server.

Numeric-ish inputs show their low / medium / high ranges; inputs that pick one
thing out of a large set are ticked in the **policy** column, which is what the
dynamic layer looks up at run time. Everything else is left blank on purpose.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
V10 = REPO / "reports" / "experiments" / "v10"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_catalogs import SERVERS  # noqa: E402


def _run_dir() -> Path:
    """The run to summarise: the one named on the command line, else the latest."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    runs = sorted((d for d in V10.glob("run*") if d.name[3:].isdigit()),
                  key=lambda d: int(d.name[3:]))
    if not runs:
        raise SystemExit(f"no run directories under {V10}")
    return runs[-1]


DIR = _run_dir()


CLASSES = ("RANGE", "POLICY", "IGNORE", "UNKNOWN")


def _bands(a: dict) -> str:
    """The three ranges, with where their boundaries came from."""
    bands = [str(a.get(k, "")).strip() for k in ("low", "medium", "high")]
    if not any(bands):
        return f"— ({a.get('bounds_source') or 'unstated'})"
    unit = a.get("unit") or ""
    return (" · ".join(f"{name} {value or '—'}"
                       for name, value in zip(("L", "M", "H"), bands))
            + (f" {unit}" if unit else "")
            + f" ({a.get('bounds_source') or 'unstated'})")


def main() -> int:
    lines = ["# Tool Arguments: how each value is evaluated at run time", "",
             f"Run `{DIR.name}` — prompt in `prompt-AS-RUN.md` beside this file.",
             "Qwen2.5:32b, greedy, seed 0.", "",
             "`RANGE` values are compared by magnitude; `POLICY` values are resolved",
             "against the organisation's policy; `IGNORE` values this component does not",
             "evaluate; `UNKNOWN` means the definition did not say enough.", ""]
    grand = Counter()
    for server in SERVERS:
        path = DIR / f"{server}.json"
        if not path.exists():
            continue
        blob = json.loads(path.read_text())
        counts: Counter[str] = Counter()
        rows = []
        for tool in sorted(blob["tools"], key=lambda t: t["tool_name"]):
            for a in tool.get("arguments", []):
                cls = str(a.get("classification", "UNKNOWN")).upper()
                counts[cls] += 1
                grand[cls] += 1
                sub = a.get("subtype") or ""
                items = a.get("items") or {}
                item = f"items: {items.get('classification')}" if items else ""
                rows.append(
                    f"| `{tool['tool_name']}` | `{a.get('path')}` | **{cls}**"
                    f"{' / ' + sub if sub else ''} | {_bands(a) if cls == 'RANGE' else '—'} "
                    f"| {a.get('policy_concept') or item or '—'} "
                    f"| {a.get('confidence', '')} | {a.get('reason', '')} |")
        lines += [f"## {server}", "",
                  f"Full explanation, tool by tool: [`{server}.md`]({server}.md)", "",
                  "| tool | argument | class | low / medium / high | policy concept / items | conf | why |",
                  "|---|---|---|---|---|---|---|", *rows, "",
                  " · ".join(f"**{c}** {counts[c]}" for c in CLASSES)
                  + f" · {sum(t['declared_arguments'] for t in blob['tools'])} declared"
                  + f" · {len(blob['no_declared_schema'])} tool(s) declare none"
                  + f" · failed: {', '.join(blob['failed']) if blob['failed'] else 'none'}.", ""]
    lines += ["## All three servers", "",
              " · ".join(f"**{c}** {grand[c]}" for c in CLASSES) + ".", ""]
    out = DIR / "INPUT_TYPES.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
