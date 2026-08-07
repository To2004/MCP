"""Compare the flag-ablation arms: does the register's `Flags` column earn its place?

Three arms, identical inputs, differing only in what the register is allowed to
assert about an asset:

* ``five_level_v2_policy_v5r``          — every flag reaches the model
* ``five_level_v2_policy_v5r_keyflags`` — only `hub` / `population` / `self-sufficient`
* ``five_level_v2_policy_v5r_noflags``  — no flag at all; tier 5 must be argued
  from the asset's own description

Same tools, same asset ids, same rubric, same assembly. So a blast difference is
attributable to the flags, and the question the report answers is narrow: **did
removing a flag change a number, and did it change it on the assets that carried
one?**

What it measures per server pair:

1. **Tier-5 survival** — how many cells reached blast 5 in each arm, and whether
   the ones that vanished were on flagged assets (the flag was load-bearing) or
   on unflagged ones (the model was inventing a route anyway).
2. **Cells moved** — the raw blast diff, split by whether the asset carried a flag.
   Movement on an *unflagged* asset is noise, not an effect of the ablation.
3. **Sensitivity drift** — flags are visible to the sensitivity stage too (they
   ride in the asset's tags), so removing them can move sensitivity as well. If it
   does, the flags were double-counting.
4. **Σ score** per arm.

Writes ``FLAG_ABLATION.md`` and ``flag_ablation.json`` next to the arms.

Run:  uv run python scripts/compare_flag_arms.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
V5 = REPO_ROOT / "reports" / "experiments" / "v5"
ARMS = {
    "all flags": V5 / "five_level_v2_policy_v5r",
    "key flags": V5 / "five_level_v2_policy_v5r_keyflags",
    "no flags": V5 / "five_level_v2_policy_v5r_noflags",
}
SERVERS = ("calendar_aurora", "github_helios", "slack_vireo")
KEY_FLAGS = frozenset({"hub", "population", "self-sufficient"})


def load(arm: Path, stem: str) -> dict | None:
    path = arm / f"{stem}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def score_sum(table: dict) -> float:
    return round(
        sum(v for row in table["cells"].values() for v in row.values() if v is not None), 1
    )


def flagged_assets(table: dict) -> set[str]:
    """Assets the REGISTER declares a key flag for — the same set in every arm.

    Read from the policy document, not from the artifact: the baseline v5r run
    predates the ``register_flags_declared`` field, and taking the empty dict at
    face value would classify every cell as unflagged and silently void the whole
    comparison.
    """
    declared = table.get("register_flags_declared")
    if not declared:
        import sys

        sys.path.insert(0, str(REPO_ROOT / "src"))
        from mcp_security.static_scoring.server_policies import (
            parse_asset_register,
            policy_for,
        )

        rows = parse_asset_register(policy_for(table["server"]).text)
        declared = {row.asset_id: list(row.flags) for row in rows if row.flags}
    return {a for a, flags in declared.items() if set(flags) & KEY_FLAGS}


def per_server(stem: str) -> dict | None:
    tables = {name: load(path, stem) for name, path in ARMS.items()}
    if any(t is None for t in tables.values()):
        return None
    baseline = tables["all flags"]
    flagged = flagged_assets(baseline)
    result = {"server": stem, "flagged_assets": sorted(flagged), "arms": {}}

    for name, table in tables.items():
        blast = table["blast_radius"]
        fives = [k for k, v in blast.items() if v == 5]
        result["arms"][name] = {
            "flag_policy": table.get("asset_flag_policy"),
            "score_sum": score_sum(table),
            "bands": table["band_distribution"],
            "blast_5_cells": len(fives),
            "blast_5_on_flagged": sum(1 for k in fives if k.split("|", 1)[1] in flagged),
            "blast_5_on_unflagged": sum(1 for k in fives if k.split("|", 1)[1] not in flagged),
            "sensitivity": table.get("asset_sensitivity", {}),
        }

    # Cell-level diffs against the all-flags arm.
    for name, table in tables.items():
        if name == "all flags":
            continue
        base_blast, arm_blast = baseline["blast_radius"], table["blast_radius"]
        moved_flagged, moved_unflagged = [], []
        for key, before in base_blast.items():
            after = arm_blast.get(key)
            if before == after:
                continue
            asset = key.split("|", 1)[1]
            entry = {"cell": key, "all_flags": before, "this_arm": after}
            (moved_flagged if asset in flagged else moved_unflagged).append(entry)
        sens_moved = {
            a: {"all_flags": s, "this_arm": table["asset_sensitivity"].get(a)}
            for a, s in baseline.get("asset_sensitivity", {}).items()
            if table.get("asset_sensitivity", {}).get(a) != s
        }
        result["arms"][name]["diff_vs_all_flags"] = {
            "moved_on_flagged_assets": moved_flagged,
            "moved_on_unflagged_assets": moved_unflagged,
            "sensitivity_moved": sens_moved,
        }
    return result


def _table(rows: list[list[str]], header: list[str]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def render(results: list[dict]) -> str:
    out = [
        "# Does the register's `Flags` column earn its place?",
        "",
        "Three arms, identical inputs, differing only in what the register may assert",
        "about an asset. Same tools, same asset ids, same rubric, same assembly — so a",
        "difference here is the flags and nothing else.",
        "",
        "| arm | flags the model sees |",
        "|---|---|",
        "| `five_level_v2_policy_v5r` | every flag the register carries |",
        "| `..._keyflags` | only `hub` / `population` / `self-sufficient` |",
        "| `..._noflags` | none — tier 5 argued from the asset's description |",
        "",
        "Generated by `scripts/compare_flag_arms.py` — do not hand-edit.",
        "",
        "## Totals",
        "",
        _table(
            [
                [
                    r["server"],
                    name,
                    f"{a['score_sum']:g}",
                    a["blast_5_cells"],
                    a["blast_5_on_flagged"],
                    a["blast_5_on_unflagged"],
                ]
                for r in results
                for name, a in r["arms"].items()
            ],
            ["server", "arm", "Σ score", "blast-5 cells", "…on flagged assets", "…on unflagged"],
        ),
        "",
        "A blast 5 **on an unflagged asset** is the number to watch in the flagged arms:",
        "the rubric told the model a 5 needs a register-sanctioned route, so such a cell",
        "means it awarded one anyway.",
        "",
    ]
    for r in results:
        out += [
            f"## {r['server']}",
            "",
            f"Assets the register flags: {', '.join(f'`{a}`' for a in r['flagged_assets']) or '*none*'}",
            "",
        ]
        for name, arm in r["arms"].items():
            if name == "all flags":
                continue
            diff = arm["diff_vs_all_flags"]
            on_flagged = diff["moved_on_flagged_assets"]
            on_unflagged = diff["moved_on_unflagged_assets"]
            out += [
                f"### {name} vs all flags",
                "",
                f"- blast moved on **{len(on_flagged)}** cells of flagged assets "
                f"(the ablation's actual effect)",
                f"- blast moved on **{len(on_unflagged)}** cells of unflagged assets "
                f"(this stage's own run-to-run variance)",
                f"- sensitivity moved on **{len(diff['sensitivity_moved'])}** assets"
                + (
                    " — flags were reaching the sensitivity stage too"
                    if diff["sensitivity_moved"]
                    else ""
                ),
                "",
            ]
            if on_flagged:
                out += [
                    _table(
                        [
                            [f"`{d['cell']}`", d["all_flags"], d["this_arm"]]
                            for d in sorted(on_flagged, key=lambda d: str(d["cell"]))
                        ],
                        ["cell", "all flags", name],
                    ),
                    "",
                ]
            if diff["sensitivity_moved"]:
                out += [
                    _table(
                        [
                            [f"`{a}`", v["all_flags"], v["this_arm"]]
                            for a, v in sorted(diff["sensitivity_moved"].items())
                        ],
                        ["asset", "all flags", name],
                    ),
                    "",
                ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=V5)
    args = parser.parse_args(argv)

    results = [r for stem in SERVERS if (r := per_server(stem)) is not None]
    if not results:
        print("[FAIL] no server has all three arms scanned yet")
        return 1
    (args.out_dir / "FLAG_ABLATION.md").write_text(render(results), encoding="utf-8")
    payload = [
        {
            **r,
            "arms": {
                n: {k: v for k, v in a.items() if k != "sensitivity"} for n, a in r["arms"].items()
            },
        }
        for r in results
    ]
    (args.out_dir / "flag_ablation.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for r in results:
        line = " | ".join(
            f"{n}: Σ{a['score_sum']:g} 5s={a['blast_5_cells']}" for n, a in r["arms"].items()
        )
        print(f"[ok] {r['server']}: {line}")
    print(f"\nwrote FLAG_ABLATION.md and flag_ablation.json to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
