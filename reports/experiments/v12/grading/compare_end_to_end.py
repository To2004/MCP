"""Compare v12 runs end to end on the real labelled calls.

For each run with stage 2 output, re-score the live corpus with the current
evaluator (``scripts/evaluate_input_rules.py``) and tabulate, per server:

- how many inputs stage 1 kept and how many got a usable rule;
- separation of risky (MISUSE + MALICIOUS) from BENIGN calls, as an AUC, for
  the input rules and for the tool-only baseline;
- how many BENIGN calls scored 4 or 5, and 5 (false alarms where the dynamic layer acts),
  and how many risky calls scored 4 or 5 (caught at that threshold).

Usage::

    python3 reports/experiments/v12/grading/compare_end_to_end.py run4 run7 run9 run11

A v13 run is named by its folder (``reports/experiments/v13/run1``); its kept
inputs are the ones with a rule.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

V12 = Path(__file__).resolve().parents[1]
REPO = V12.parents[2]
SERVERS = ("github", "slack", "calendar")


def _folder(run: str) -> Path:
    return REPO / run if "/" in run else V12 / run


def _rules_summary(run_dir: Path, server: str) -> tuple[int, int, int]:
    data = json.loads((run_dir / f"{server}.json").read_text())
    kept = sum(a.get("important", False) for t in data["tools"] for a in t["arguments"])
    rules = sum("rule" in a for t in data["tools"] for a in t["arguments"])
    missing = sum(len(t.get("missing_rules", [])) for t in data["tools"])
    return kept, rules, missing


def main(runs: list[str]) -> None:
    for run in runs:
        subprocess.run([sys.executable, str(REPO / "scripts" / "evaluate_input_rules.py"),
                        "--run", str(_folder(run)), "--servers", *SERVERS],
                       check=True, capture_output=True, cwd=REPO)
    print(f"{'server':9} {'run':6} {'kept':>5} {'rules':>6} {'missing':>8} | "
          f"{'AUC rules':>9} {'AUC tool-only':>13} | {'benign at 4-5':>13} {'at 5':>5} | "
          f"{'risky at 4-5':>12}")
    for server in SERVERS:
        for run in runs:
            run_dir = _folder(run)
            ev = json.loads((run_dir / f"eval_{server}.json").read_text())
            s = ev["summary"]
            dist = s["distribution"]
            benign_high = sum(dist["BENIGN"].get(str(k), 0) for k in (4, 5))
            benign_top = dist["BENIGN"].get("5", 0)
            risky = sum(sum(dist[c].values()) for c in ("MISUSE", "MALICIOUS"))
            risky_high = sum(dist[c].get(str(k), 0) for c in ("MISUSE", "MALICIOUS") for k in (4, 5))
            kept, rules, missing = _rules_summary(run_dir, server)
            label = "/".join(run_dir.parts[-2:]) if "/" in run else run
            print(f"{server:9} {label:6} {kept:5} {rules:6} {missing:8} | "
                  f"{s['separation']['level']['RISKY_vs_BENIGN']:9.3f} "
                  f"{s['separation']['tool_only']['RISKY_vs_BENIGN']:13.3f} | "
                  f"{benign_high:6} of 500 {benign_top:5} | {risky_high:5} of {risky}")
        print()


if __name__ == "__main__":
    main(sys.argv[1:] or ["run4", "run7", "run9", "run11"])
