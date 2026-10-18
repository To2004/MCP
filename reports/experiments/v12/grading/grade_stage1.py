"""Grade a v12 run's stage 1 against the reference verdicts in ``verdicts.json``.

Every input of the five catalogs carries one verdict: ``keep`` (important),
``drop`` (should not be kept), ``record-id`` (an id inside an already chosen
asset; should not be kept), ``borderline`` (either answer is defensible) or
``debatable``. They are one annotator's judgments under the extremes test, not
ground truth. filesystem and sqlite are held out: no prompt was tuned on them,
and their verdicts were written before any run on them was read.

A v13 run (one step, ``<server>.json`` rows with a ``status``) is graded the
same way: an input counts as kept when it got a rule. v13 drops on purpose any
input with fewer than five choices (a switch, a short list), so those are also
counted apart, and the totals are given with and without them.

Usage::

    python3 reports/experiments/v12/grading/grade_stage1.py run10
    python3 reports/experiments/v12/grading/grade_stage1.py reports/experiments/v13/run1
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V12 = HERE.parent
sys.path.insert(0, str(V12.parents[2] / "scripts"))

from input_feature_facts import facts_for  # noqa: E402
from mcp_catalogs import load_tools  # noqa: E402

SERVERS = ("github", "slack", "calendar", "filesystem", "sqlite")
HELD_OUT = {"filesystem", "sqlite"}
SHOULD_DROP = {"drop", "record-id"}
#: v13: an input with fewer choices than this cannot reach five levels.
FIVE_LEVELS = 5


def _run_file(run: str, server: str) -> Path:
    """A v12 run's importance file, or a v13 run's one-step file."""
    folder = Path(run) if "/" in run else V12 / run
    v12 = folder / f"{server}.importance.json"
    return v12 if v12.exists() else folder / f"{server}.json"


def _switches(server: str) -> set[str]:
    """``tool|path`` of every input with fewer than five choices (a boolean, a short enum),
    read from the catalog, so a v12 run is split the same way as a v13 one."""
    found = set()
    for tool in load_tools(server):
        for path, fact in facts_for(tool["input_schema"] or {}).items():
            n = len(fact["enum"]) if fact.get("enum") else (
                2 if "boolean" in (fact.get("type") or []) else None)
            if n is not None and n < FIVE_LEVELS:
                found.add(f"{tool['tool_name']}|{path}")
    return found


def _detail(row: dict) -> str:
    """What the run's answers were, for whichever stage 1 version wrote them."""
    if "status" in row:
        return f"status={row['status']}"
    if "gap" in row:
        return f"kind={row.get('kind')} rankable={row.get('rankable')} gap={row.get('gap')}"
    if "affects_asset" in row:
        return f"asset={row.get('affects_asset')} rank={row.get('rank')}"
    if "votes" in row:
        return "votes=" + "".join("Y" if x else ("n" if x is False else "?") for x in row["votes"])
    return ""


def grade(run: str) -> None:
    verdicts = json.loads((HERE / "verdicts.json").read_text())
    totals = {"tuned": collections.Counter(), "held_out": collections.Counter()}
    for server in SERVERS:
        path = _run_file(run, server)
        if not path.exists():
            continue
        rows = {f"{t['tool_name']}|{a['path']}": a
                for t in json.loads(path.read_text())["tools"] for a in t["arguments"]}
        switches = _switches(server) & set(rows)
        mine = verdicts[server]
        c = collections.Counter((mine.get(k, "unjudged"), a["important"]) for k, a in rows.items())
        kept = sum(a["important"] for a in rows.values())
        group = "held_out" if server in HELD_OUT else "tuned"
        totals[group].update({"keep_kept": c[("keep", True)], "keep_all": c[("keep", True)] + c[("keep", False)],
                              "noise_dropped": sum(c[(v, False)] for v in SHOULD_DROP),
                              "noise_all": sum(c[(v, b)] for v in SHOULD_DROP for b in (True, False)),
                              "inputs": len(rows), "kept": kept,
                              "keep_kept_ns": sum(1 for k, a in rows.items() if k not in switches
                                                  and mine.get(k) == "keep" and a["important"]),
                              "keep_all_ns": sum(1 for k in rows if k not in switches
                                                 and mine.get(k) == "keep"),
                              "keep_switches": sum(1 for k in switches if mine.get(k) == "keep")})
        tag = " (held out)" if server in HELD_OUT else ""
        print(f"\n===== {server}{tag}: {len(rows)} inputs, kept {kept}, dropped {len(rows) - kept}")
        for v in ("keep", "borderline", "record-id", "drop", "debatable", "unjudged"):
            if c[(v, True)] or c[(v, False)]:
                print(f"   my verdict {v:10}: run kept {c[(v, True)]:3}  run dropped {c[(v, False)]:3}")
        for label, want, got in (("IMPORTANT BUT DROPPED", {"keep"}, False),
                                 ("SHOULD-DROP OR RECORD-ID BUT KEPT", SHOULD_DROP, True)):
            misses = sorted(k for k, a in rows.items() if mine.get(k) in want
                            and a["important"] is got and not (got is False and k in switches))
            if misses:
                print(f"   {label}:")
                for k in misses:
                    print(f"     {k.replace('|', '.')} [{_detail(rows[k])}] {rows[k]['reason'][:90]}")
    for group, t in totals.items():
        if t["inputs"]:
            print(f"\nTOTAL {group}: {t['inputs']} inputs, kept {t['kept']} | important kept "
                  f"{t['keep_kept']}/{t['keep_all']} | should-drop dropped {t['noise_dropped']}/{t['noise_all']}")
            if t["keep_switches"]:
                print(f"   without the {t['keep_switches']} switches and short lists judged keep: "
                      f"important kept {t['keep_kept_ns']}/{t['keep_all_ns']}")


if __name__ == "__main__":
    grade(sys.argv[1] if len(sys.argv) > 1 else "run10")
