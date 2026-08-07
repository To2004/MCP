"""Run the deterministic tool-impact rules over every MCP catalog in the repo.

No LLM, no GPU: `static_impact.classify` reads each tool's own declaration (name,
description, parameters, annotation hints) and returns a 1-5 tier plus the
evidence that set it. This script sweeps every catalog group and writes one
markdown report per group, plus a corpus-wide summary.

    uv run python scripts/static_impact_report.py
    uv run python scripts/static_impact_report.py --group finance

Groups:
  live       the five servers the v4 experiments scan (real captured catalogs)
  finance    five finance MCP servers
  reference  the official reference servers (git, postgres, redis, gdrive, ...)
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scan_pure_desc import TARGETS  # noqa: E402

from mcp_security.scanner.tool_list import load_tool_list  # noqa: E402
from mcp_security.static_scoring import static_impact  # noqa: E402

OUT_DIR = REPO_ROOT / "reports" / "experiments" / "v4" / "static_impact"
LADDER = {
    1: "no effect",
    2: "metadata",
    3: "content read",
    4: "reversible write",
    5: "irreversible",
}
# A tier the rules reached with no verb evidence at all is a DEFAULT, not a
# finding; the classifier reports that as low confidence.
LOW_CONFIDENCE = 0.5


def _groups() -> dict[str, list[tuple[str, Path, str]]]:
    """group -> [(server label, catalog path, loader kind)]."""
    finance = REPO_ROOT / "reports" / "scan_finance" / "tool_lists"
    reference = REPO_ROOT / "src" / "mcp_security" / "atomic_ops" / "data" / "tool_lists"
    return {
        "live": [(t.stem, t.catalog, t.kind) for t in TARGETS],
        "finance": [(p.stem, p, "generic") for p in sorted(finance.glob("*.json"))],
        "reference": [(p.stem, p, "generic") for p in sorted(reference.glob("*.json"))],
    }


def _classify(path: Path, kind: str) -> list:
    tools = load_tool_list(kind, path=path)
    verdicts = static_impact.classify_all(tools)
    return [(t, verdicts[t.name]) for t in tools]


def _tier_row(counts: collections.Counter) -> str:
    return " | ".join(str(counts.get(t, 0)) for t in range(1, 6))


def _summary_table(rows: list[tuple[str, collections.Counter, int, int]]) -> list[str]:
    out = [
        "| Server | Tools | t1 | t2 | t3 | t4 | t5 | state-changing | no verb evidence |",
        "|---|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for label, counts, changing, unknown in rows:
        total = sum(counts.values())
        out.append(
            f"| `{label}` | {total} | {_tier_row(counts)} | "
            f"**{changing}** | {unknown or '—'} |"
        )
    return out


def _server_section(label: str, results: list) -> list[str]:
    counts = collections.Counter(v.tool_impact for _, v in results)
    out = [
        "",
        f"### `{label}` — {len(results)} tools",
        "",
        "| Tool | Impact | Why | Flags |",
        "|---|:--:|---|---|",
    ]
    for tool, v in sorted(results, key=lambda r: (-r[1].tool_impact, r[0].name)):
        why = v.reasoning.replace("deterministic ladder: ", "").replace("|", "/")
        flags = ", ".join(f.split(":")[0] for f in v.capability_flags) or "—"
        bulk = " *(bulk)*" if v.is_bulk else ""
        low = " ⚠" if v.confidence <= LOW_CONFIDENCE else ""
        out.append(f"| `{tool.name}`{bulk} | **{v.tool_impact}**{low} | {why} | {flags} |")
    out += ["", f"Tier counts: {dict(sorted(counts.items()))}"]
    return out


def build(group: str) -> Path:
    rows, sections = [], []
    for label, path, kind in _groups()[group]:
        results = _classify(path, kind)
        counts = collections.Counter(v.tool_impact for _, v in results)
        changing = sum(1 for _, v in results if v.tool_impact >= 4)
        unknown = sum(1 for _, v in results if v.confidence <= LOW_CONFIDENCE)
        rows.append((label, counts, changing, unknown))
        sections += _server_section(label, results)

    total = sum(sum(c.values()) for _, c, _, _ in rows)
    corpus = collections.Counter()
    for _, c, _, _ in rows:
        corpus += c
    doc = [
        f"# Static tool impact — {group} MCP servers (no LLM)",
        "",
        f"{total} tools across {len(rows)} servers, classified by",
        "`src/mcp_security/static_scoring/static_impact.py` from each tool's own",
        "declaration only — name, description, parameters, annotation hints.",
        "**No model call.** Regenerate with",
        f"`uv run python scripts/static_impact_report.py --group {group}`.",
        "",
        "Ladder: **1** no effect · **2** metadata · **3** content read ·",
        "**4** reversible write · **5** irreversible.",
        "",
        "⚠ marks a tier reached with **no verb evidence** — a default, not a finding.",
        "",
        "## Summary",
        "",
        *_summary_table(rows),
        "",
        f"Corpus: {dict(sorted(corpus.items()))} — "
        f"{sum(v for k, v in corpus.items() if k >= 4)}/{total} state-changing "
        f"({sum(v for k, v in corpus.items() if k >= 4) / total:.0%}).",
        "",
        "## Per-server detail",
        *sections,
        "",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{group}.md"
    path.write_text("\n".join(doc), encoding="utf-8")
    print(f"[ok] {group}: {total} tools, {len(rows)} servers -> {path}")
    for label, counts, changing, unknown in rows:
        print(
            f"     {label:16s} {sum(counts.values()):4d} tools  "
            f"t1-5 {_tier_row(counts):18s}  changing {changing:3d}  no-evidence {unknown}"
        )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", default=None, choices=list(_groups()), help="default: all")
    args = parser.parse_args(argv)
    for group in [args.group] if args.group else _groups():
        build(group)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
