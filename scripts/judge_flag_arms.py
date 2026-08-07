"""LLM-as-judge over the cells where the flag arms disagree.

Protocol, following ``scripts/judge_blast_experiments.py``: the judge is
**anchor-free**. It never sees either arm's answer and is not asked to pick
between them — it re-derives blast radius itself, and both arms are then graded
against it. That removes position bias and the pull of an anchor, which an A/B
preference judge has no defence against.

**The information the judge gets, and why.** Both arms are approximations of the
same thing: what the organization disclosed about the asset. `keyflags` saw the
description plus three flags; `noflags` saw the description alone. The judge sees
the organization's **complete register row** — description, flags and CIA — plus
the tool declaration and the propagation rubric.

That is deliberately a superset of both arms, so neither is handed its own input
as the yardstick. It is not neutral in the strict sense: an arm whose information
is closer to the judge's has a structural advantage, and `keyflags` is closer. So
read a `keyflags` win as weak evidence and a `noflags` win as strong evidence.

The judge is NOT shown the asset's sensitivity, because sensitivity anchoring is
one of the things under test — the scoring arms were told it, and their blast
correlates with it at +0.57 to +0.69.

Only the cells where the arms actually differ are judged; the rest are identical
by construction and would just pad the agreement rate.

Run on a GPU node:  python scripts/judge_flag_arms.py
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.scanner.tool_list import load_tool_list
from mcp_security.static_scoring import prompts
from mcp_security.static_scoring.server_policies import parse_asset_register, policy_for

REPO_ROOT = Path(__file__).resolve().parents[1]
V5 = REPO_ROOT / "reports" / "experiments" / "v5"
ARMS = {
    "keyflags": V5 / "five_level_v2_policy_v5r_keyflags",
    "noflags": V5 / "five_level_v2_policy_v5r_noflags",
}
# stem -> (server kind, captured catalog) — the judge needs the tool's own
# declaration, which lives in the catalog, not in the scan artifact.
SERVERS = {
    "calendar_aurora": ("calendar", "calendar_real.json"),
    "github_helios": ("github", "github_real.json"),
    "slack_vireo": ("slack", "slack_real.json"),
}
TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"

JUDGE_TASK = (
    prompts.BLAST_TASK_V5R
    + """

You are an INDEPENDENT reviewer. You have not been shown anyone else's answer and
there is no answer to agree with. Judge the pair on its own merits."""
)

JUDGE_USER = """Tool:
{tool_json}

Asset, exactly as the organization's register describes it:
  id: {asset_id}
  description: {description}
  structural flags: {flags}
  loss axis: {cia}
  tools the register says reach it: {tools}

Return JSON: {{"asset_id": str, "affects_asset": bool, "coverage_reasoning": str,
"blast_radius": "1-5 or null", "confidence": 0.0-1.0}}"""


def load(arm: Path, stem: str) -> dict:
    return json.loads((arm / f"{stem}.json").read_text(encoding="utf-8"))


def differing_cells(stem: str) -> list[tuple[str, int | None, int | None]]:
    a = load(ARMS["keyflags"], stem)["blast_radius"]
    b = load(ARMS["noflags"], stem)["blast_radius"]
    return [(k, a[k], b.get(k)) for k in a if a[k] != b.get(k)]


def judge_cell(tool_json: dict, row) -> dict | None:
    prompt = (
        JUDGE_TASK
        + "\n\n"
        + JUDGE_USER.format(
            tool_json=json.dumps(tool_json),
            asset_id=row.asset_id,
            description=row.description,
            flags=", ".join(row.flags) or "none",
            cia=row.cia or "unstated",
            tools=", ".join(row.tools) or "none",
        )
    )
    result = query_ollama(prompt)
    return result if isinstance(result, dict) else None


def grade(arm_value: int | None, judged: int | None) -> dict:
    """One cell's agreement with the judge. N/A is its own category, not a zero."""
    if judged is None or arm_value is None:
        return {
            "comparable": False,
            "exact": arm_value == judged,
            "abs_err": None,
            "signed": None,
        }
    return {
        "comparable": True,
        "exact": arm_value == judged,
        "abs_err": abs(arm_value - judged),
        "signed": arm_value - judged,
    }


def summarize(rows: list[dict], arm: str) -> dict:
    graded = [r for r in rows if r[f"{arm}_comparable"]]
    n = len(graded)
    if not n:
        return {"n": 0}
    errs = [r[f"{arm}_abs_err"] for r in graded]
    signed = [r[f"{arm}_signed"] for r in graded]
    return {
        "n": n,
        "exact": round(sum(1 for r in rows if r[f"{arm}_exact"]) / len(rows), 3),
        "within_1": round(sum(1 for e in errs if e <= 1) / n, 3),
        "mae": round(sum(errs) / n, 3),
        "bias": round(sum(signed) / n, 3),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=V5)
    parser.add_argument("--limit", type=int, default=None, help="judge only the first N cells")
    parser.add_argument("--no-llm", action="store_true", help="plumbing smoke test")
    args = parser.parse_args(argv)

    rows: list[dict] = []
    for stem, (kind, catalog) in SERVERS.items():
        key_table = load(ARMS["keyflags"], stem)
        register = {r.asset_id: r for r in parse_asset_register(policy_for(key_table["server"]).text)}
        tools = {
            t.name: t.to_prompt_json()
            for t in load_tool_list(kind, path=TOOL_LISTS / catalog)
        }
        cells = differing_cells(stem)
        if args.limit:
            cells = cells[: args.limit]
        print(f"[{stem}] judging {len(cells)} differing cells")
        for key, key_val, no_val in cells:
            tool, asset = key.split("|", 1)
            row = register.get(asset)
            if row is None:
                continue
            tool_json = tools.get(tool) or {"tool_name": tool}
            verdict = None if args.no_llm else judge_cell(tool_json, row)
            judged = None
            if verdict is not None:
                raw = verdict.get("blast_radius")
                if verdict.get("affects_asset") is not False and raw not in (None, "null"):
                    judged = max(1, min(5, int(raw)))
            gk, gn = grade(key_val, judged), grade(no_val, judged)
            rows.append(
                {
                    "server": stem,
                    "cell": key,
                    "asset": asset,
                    "register_flags": ",".join(row.flags),
                    "keyflags": key_val,
                    "noflags": no_val,
                    "judge": judged,
                    "judge_reasoning": (verdict or {}).get("coverage_reasoning", ""),
                    **{f"keyflags_{k}": v for k, v in gk.items()},
                    **{f"noflags_{k}": v for k, v in gn.items()},
                }
            )

    if not rows:
        print("[FAIL] nothing judged")
        return 1

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    (args.out_dir / "flag_arms_judged.csv").write_text(buf.getvalue(), encoding="utf-8")

    summary = {arm: summarize(rows, arm) for arm in ("keyflags", "noflags")}
    flagged = [r for r in rows if r["register_flags"]]
    summary["on_flagged_assets_only"] = {
        arm: summarize(flagged, arm) for arm in ("keyflags", "noflags")
    } if flagged else {}
    (args.out_dir / "flag_arms_judged.json").write_text(
        json.dumps({"summary": summary, "n_cells": len(rows)}, indent=2), encoding="utf-8"
    )
    print(f"\njudged {len(rows)} cells")
    for arm in ("keyflags", "noflags"):
        s = summary[arm]
        if s.get("n"):
            print(
                f"  {arm:<9} exact {s['exact'] * 100:.0f}%  within-1 {s['within_1'] * 100:.0f}%  "
                f"MAE {s['mae']}  bias {s['bias']:+.2f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
