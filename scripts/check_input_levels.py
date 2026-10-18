"""Two quick checks of a v13 run's input rules, so a run can be judged without
reading every rule.

1. **Scenarios** (``reports/experiments/v13/scenarios.json``): hand-written pairs,
   the same call with one input moved from harmless to risky. A pair passes
   when the risky call scores above the harmless one (and at least
   ``risky_at_least`` when given). Each pair says why it is risky: the policy
   line it rests on (``policy``), common knowledge (``simple``), or neither
   (``out_of_scope``: listed, not counted, since no rule can know it).
2. **Real calls**: on the labelled live corpus, the inputs whose value alone
   tells risky sessions from harmless ones (a leave-one-out separation per
   value). Each is shown with its status in the run and how well its rule
   separates the same calls. A dropped input here is a missed one; a rule far
   below its input's separation has the wrong levels. The labels are per
   session, not per call, and most corpus values never vary, so this screens
   rather than grades.

Writes ``<run>/checks.md`` and prints it.

Usage::

    uv run python scripts/check_input_levels.py --run reports/experiments/v13/run11
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluate_input_rules import (  # noqa: E402
    CORPUS_DIR,
    has_corpus,
    load_aliases,
    load_rules,
    score_server,
    separation,
)
from mcp_security.input_rules import evaluate_call  # noqa: E402
from policy_context import POLICY_SECTIONS  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SCENARIOS = REPO / "reports" / "experiments" / "v13" / "scenarios.json"
COUNTED = ("policy", "simple")
#: An input is screened when it appears in at least this many real calls...
MIN_CALLS = 15
#: ...and its value alone separates risky from harmless sessions at least this well.
SIGNAL_AUC = 0.75


def scenario_results(run_dir: Path, scenarios: list[dict]) -> list[dict]:
    """Each scenario with the two levels the run's rules give and whether it passed."""
    rules: dict[str, dict] = {}
    out = []
    for s in scenarios:
        server = s["server"]
        if server not in rules:
            path = run_dir / f"{server}.json"
            rules[server] = load_rules(run_dir, server) if path.exists() else {}
        rows, assets = rules[server].get(s["tool"], ([], {}))
        low = evaluate_call(rows, s["harmless"], assets=assets)
        high = evaluate_call(rows, s["risky"], assets=assets)
        a, b = low.level or 0, high.level or 0
        ok = b > a and b >= s.get("risky_at_least", 0)
        out.append({**s, "harmless_level": low.level, "risky_level": high.level,
                    "set_by": list(high.set_by), "passed": ok})
    return out


def flatten(args: dict) -> dict[str, str]:
    """Input path -> the value as JSON text; list items of objects as ``key[].sub``."""
    flat = {}
    for key, value in args.items():
        flat[key] = json.dumps(value, sort_keys=True)
        for item in value if isinstance(value, list) else []:
            for sub, sub_value in item.items() if isinstance(item, dict) else []:
                flat.setdefault(f"{key}[].{sub}", json.dumps(sub_value, sort_keys=True))
    return flat


def value_signal(values: list[str], risky: list[bool]) -> float | None:
    """How well the value alone tells risky from harmless: each call is scored by
    the risky share of the other calls with the same value (leave-one-out, one
    pseudo-call at the overall share), then separated as an AUC."""
    prior = sum(risky) / len(risky)
    by_value: dict[str, list[bool]] = collections.defaultdict(list)
    for v, y in zip(values, risky):
        by_value[v].append(y)
    scores = [(sum(by_value[v]) - y + prior) / len(by_value[v]) for v, y in zip(values, risky)]
    high = [s for s, y in zip(scores, risky) if y]
    low = [s for s, y in zip(scores, risky) if not y]
    return separation(high, low)


def real_call_screen(run_dir: Path, server: str, aliases: dict[str, str]) -> list[dict]:
    """The inputs of ``server``'s real calls whose value carries the risk signal."""
    scored = score_server(run_dir, server, aliases, ())
    data = json.loads((run_dir / f"{server}.json").read_text())
    status = {(t["tool_name"], a["path"]): a.get("status", "rule" if a.get("rule") else "null")
              for t in data["tools"] for a in t["arguments"]}
    calls = {c["index"]: c for c in scored["calls"]}
    per_input: dict[tuple[str, str], list] = collections.defaultdict(list)
    corpus = CORPUS_DIR / f"live_scale_{POLICY_SECTIONS[server]}.csv"
    with corpus.open() as fh:
        for row in csv.DictReader(fh):
            levels = calls[row["index"]]["inputs"]
            for path, value in flatten(json.loads(row["args"] or "{}")).items():
                level = levels.get(path, [None])[0]
                per_input[(row["tool"], path)].append((value, row["category"] != "BENIGN", level))
    found = []
    for (tool, path), obs in sorted(per_input.items()):
        values, risky, levels = map(list, zip(*obs))
        if len(obs) < MIN_CALLS or all(risky) or not any(risky):
            continue
        signal = value_signal(values, risky)
        if signal is None or signal < SIGNAL_AUC:
            continue
        st = status.get((tool, path), status.get((tool, path.replace("[]", "")), "not in catalog"))
        rule_auc = separation([lv or 0 for lv, y in zip(levels, risky) if y],
                              [lv or 0 for lv, y in zip(levels, risky) if not y])
        found.append({"server": server, "input": f"{tool}.{path}", "calls": len(obs),
                      "status": st, "value_signal": signal,
                      "rule_signal": rule_auc if st == "rule" else None})
    return found


def render(run_dir: Path, results: list[dict], screen: list[dict]) -> str:
    """The checks as markdown."""
    counted = [r for r in results if r["basis"] in COUNTED]
    lines = [f"# Input-level checks: {run_dir.name}", "",
             "Generated by `scripts/check_input_levels.py`.", "", "## Scenarios", ""]
    for basis in COUNTED:
        part = [r for r in counted if r["basis"] == basis]
        lines.append(f"- {basis}: {sum(r['passed'] for r in part)} of {len(part)} pass")
    lines += ["", "| | server | tool | change | levels | basis | why |", "|---|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda r: (r["basis"] == "out_of_scope", r["passed"])):
        mark = "–" if r["basis"] == "out_of_scope" else ("pass" if r["passed"] else "**FAIL**")
        lines.append(f"| {mark} | {r['server']} | `{r['tool']}` | {r['change']} | "
                     f"{r['harmless_level']} → {r['risky_level']} | {r['basis']} | {r['why']} |")
    lines += ["", "## Real calls: inputs whose value carries the risk", "",
              f"Inputs in at least {MIN_CALLS} calls whose value alone separates risky from "
              f"harmless sessions with an AUC of {SIGNAL_AUC} or more.", "",
              "| server | input | calls | status | value alone | rule |", "|---|---|---|---|---|---|"]
    for s in screen:
        rule = f"{s['rule_signal']:.2f}" if s["rule_signal"] is not None else "–"
        lines.append(f"| {s['server']} | `{s['input']}` | {s['calls']} | {s['status']} | "
                     f"{s['value_signal']:.2f} | {rule} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--run", type=Path, required=True, help="a v13 run folder")
    ap.add_argument("--scenarios", type=Path, default=SCENARIOS)
    args = ap.parse_args()
    scenarios = json.loads(args.scenarios.read_text())["scenarios"]
    results = scenario_results(args.run, scenarios)
    aliases = load_aliases()
    screen = [s for server in POLICY_SECTIONS if (args.run / f"{server}.json").exists()
              and has_corpus(server) for s in real_call_screen(args.run, server, aliases)]
    report = render(args.run, results, screen)
    (args.run / "checks.md").write_text(report)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
