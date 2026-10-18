"""Score real labelled calls with a v12 run's input rules (no model on the path).

Every call in the live corpus (``v5/five_level_v2_policy_v5r_nacombo/
live_scale_<org>.csv``, about 1,000 real calls per organization, labelled by the
session they came from: BENIGN, MISUSE or MALICIOUS) is scored with
``mcp_security.input_rules.evaluate_call``: the highest level among the call's
important inputs.

Reported per server:

- the level distribution per category;
- separation: the probability a MISUSE or MALICIOUS call scores above a BENIGN
  one, ties counted half (an AUC; 0.5 is no separation);
- the same separation for a **tool-only** baseline that ignores the arguments
  and scores a call by the most sensitive asset its tool can reach, which is
  what a design-time view alone can say;
- which inputs set the level, and how often a value could not be resolved.

The category is a session label, not a per-call verdict: a misuse session also
makes ordinary-looking calls, so perfect separation is not expected.

Usage::

    uv run python scripts/evaluate_input_rules.py --run reports/experiments/v12/run4
"""

from __future__ import annotations

import argparse
import collections
from collections.abc import Sequence
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp_security.input_rules import evaluate_call  # noqa: E402
from policy_context import POLICY_SECTIONS  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r_nacombo"
ORG_IDS_DIR = REPO / "reports" / "live_run" / "orgs_2026-07-29"
#: id tables written when the orgs were provisioned: asset name -> {"id": ...}
ID_TABLES = ("slack_channels.json", "calendars.json")
CATEGORIES = ("BENIGN", "MISUSE", "MALICIOUS")
LEVEL_COLUMNS = (1, 2, 3, 4, 5, None)


def load_aliases() -> dict[str, str]:
    """Raw channel and calendar ids -> asset ids, from the provisioning records."""
    aliases: dict[str, str] = {}
    for name in ID_TABLES:
        for asset, record in json.loads((ORG_IDS_DIR / name).read_text()).items():
            if isinstance(record, dict) and record.get("id"):
                aliases[record["id"]] = asset
    return aliases


def load_rules(run_dir: Path, server: str) -> dict[str, tuple[list[dict], dict[str, int]]]:
    """Tool -> (its rule rows, its reachable assets with their scanned level)."""
    data = json.loads((run_dir / f"{server}.json").read_text())
    tools = {}
    for tool in data["tools"]:
        rows = [a for a in tool["arguments"] if isinstance(a.get("rule"), dict)]
        assets = {a["asset"]: a["scanned_level"]
                  for a in tool.get("policy_slice", {}).get("assets_this_tool_can_reach", [])
                  if isinstance(a.get("scanned_level"), int)}
        tools[tool["tool_name"]] = (rows, assets)
    return tools


def separation(high: Sequence[float], low: Sequence[float]) -> float | None:
    """P(a call from ``high`` scores above one from ``low``), ties counted half."""
    if not high or not low:
        return None
    above = ties = 0
    low_counts = collections.Counter(low)
    for h in high:
        for value, n in low_counts.items():
            if h > value:
                above += n
            elif h == value:
                ties += n
    return (above + 0.5 * ties) / (len(high) * len(low))


def has_corpus(server: str) -> bool:
    """True when the live labelled corpus has calls for ``server``'s organization."""
    return server in POLICY_SECTIONS and (
        CORPUS_DIR / f"live_scale_{POLICY_SECTIONS[server]}.csv").exists()


def score_server(run_dir: Path, server: str, aliases: dict[str, str],
                 org_domains: tuple[str, ...]) -> dict:
    """Score every corpus call for ``server`` and summarize."""
    rules = load_rules(run_dir, server)
    org = POLICY_SECTIONS[server]
    calls = list(csv.DictReader((CORPUS_DIR / f"live_scale_{org}.csv").open()))
    rows_out = []
    for call in calls:
        rows, assets = rules.get(call["tool"], ([], {}))
        args = json.loads(call["args"] or "{}")
        result = evaluate_call(rows, args, assets=assets, aliases=aliases,
                               org_domains=org_domains)
        rows_out.append({
            "index": call["index"], "category": call["category"], "tool": call["tool"],
            "labelled_asset": call["asset"], "level": result.level,
            "tool_only": max(assets.values()) if assets else None,
            "set_by": list(result.set_by),
            "unresolved": [lv.path for lv in result.inputs if lv.unresolved],
            "inputs": {lv.path: [lv.level, lv.matched] for lv in result.inputs},
        })
    return {"server": server, "org": org, "calls": rows_out, "summary": summarize(rows_out)}


def _filled(rows: list[dict], key: str, category: str) -> list[int]:
    """Levels for one category; a call no rule touched counts as level 0."""
    return [r[key] or 0 for r in rows if r["category"] == category]


def summarize(rows: list[dict]) -> dict:
    """Distributions, separations and the inputs that drive the level."""
    dist = {c: collections.Counter(r["level"] for r in rows if r["category"] == c)
            for c in CATEGORIES}
    sep = {}
    for key in ("level", "tool_only"):
        benign = _filled(rows, key, "BENIGN")
        risky = _filled(rows, key, "MISUSE") + _filled(rows, key, "MALICIOUS")
        sep[key] = {"MISUSE_vs_BENIGN": separation(_filled(rows, key, "MISUSE"), benign),
                    "MALICIOUS_vs_BENIGN": separation(_filled(rows, key, "MALICIOUS"), benign),
                    "RISKY_vs_BENIGN": separation(risky, benign)}
    set_by = collections.Counter(f"{r['tool']}.{p}" for r in rows for p in r["set_by"])
    per_tool = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        per_tool[r["tool"]][r["category"]].append(r["level"] or 0)
    return {
        "calls": len(rows),
        "distribution": {c: {str(k): dist[c].get(k, 0) for k in LEVEL_COLUMNS} for c in CATEGORIES},
        "separation": sep,
        "no_rule_applied": sum(r["level"] is None for r in rows),
        "with_unresolved_input": sum(bool(r["unresolved"]) for r in rows),
        "top_set_by": set_by.most_common(12),
        "per_tool_mean": {t: {c: round(sum(v) / len(v), 2) for c, v in cats.items()}
                          for t, cats in sorted(per_tool.items())},
    }


def render(result: dict) -> str:
    """A short markdown report for one server."""
    s = result["summary"]
    lines = [f"# {result['server']} ({result['org']}): {s['calls']} real calls", ""]
    lines += ["| category | " + " | ".join(str(k) for k in LEVEL_COLUMNS[:-1]) + " | no rule |",
              "|---|" + "---|" * len(LEVEL_COLUMNS)]
    for c in CATEGORIES:
        d = s["distribution"][c]
        lines.append(f"| {c} | " + " | ".join(str(d[str(k)]) for k in LEVEL_COLUMNS) + " |")
    lines += ["", "| separation (AUC, 0.5 = none) | input rules | tool only |", "|---|---|---|"]
    for k in ("MISUSE_vs_BENIGN", "MALICIOUS_vs_BENIGN", "RISKY_vs_BENIGN"):
        a, b = s["separation"]["level"][k], s["separation"]["tool_only"][k]
        lines.append(f"| {k} | {a:.3f} | {b:.3f} |")
    lines += ["", f"No rule applied: {s['no_rule_applied']} calls. "
              f"With an unresolved input: {s['with_unresolved_input']} calls.", "",
              "Inputs that set the level most often:", ""]
    lines += [f"- `{name}`: {n}" for name, n in s["top_set_by"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", type=Path, required=True, help="a v12 run folder with stage 2 output")
    ap.add_argument("--servers", nargs="*", default=sorted(POLICY_SECTIONS))
    ap.add_argument("--org-domain", action="append", default=[],
                    help="an organization email domain treated as internal (repeatable)")
    args = ap.parse_args()
    aliases = load_aliases()
    for server in args.servers:
        if not (args.run / f"{server}.json").exists():
            print(f"{server}: no stage 2 output in {args.run}; skipped")
            continue
        if not has_corpus(server):
            print(f"{server}: no live labelled corpus; skipped")
            continue
        result = score_server(args.run, server, aliases, tuple(args.org_domain))
        (args.run / f"eval_{server}.json").write_text(json.dumps(result, indent=1))
        report = render(result)
        (args.run / f"eval_{server}.md").write_text(report)
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
