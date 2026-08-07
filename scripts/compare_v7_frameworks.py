"""Compare the v7 framework-native policy arms against the v5r ``nacombo`` baseline.

Four organizations — ``fs_corp_filesystem``, ``github_helios``, ``slack_vireo``,
``calendar_aurora`` — each publish four policy documents describing the same
deployment:

* ``nacombo``  the baseline register shape (``docs/mcp-tools/server-policies.md``)
* ``iso``      an ISO/IEC 27001:2022 A.5.9 inventory with A.8.3 authorization
* ``nist``     an SP 800-60 information-type register with AC-3 authorization
* ``cis``      a CIS Safeguard 3.2 inventory with 3.3 access control lists

Every other scanner input is held fixed: same tool catalogs, same impact ladder,
same blast rubric, same deterministic assembly. So a difference between arms is
attributable to the policy document and its matching sensitivity prompt.

**There is no held-out ground truth for these four servers.** The three
live-provisioned organizations have no section in ``server-profiles.md`` at all,
and ``fs_corp_filesystem``'s profile uses path-shaped asset ids
(``sensitive/security/private_key.pem``) that do not align with the policy
register's concept ids (``security-keys``). So this script does NOT report
accuracy. It reports two things that need no truth:

1. **Reference comparison** — how each arm moves relative to ``nacombo``, per
   asset and per cell, over the asset ids the two registers share.
2. **Cross-arm agreement** — whether three organizations describing the same
   deployment under three frameworks arrive at the same severities.

The arms diverge in register shape by design (ISO keeps the baseline's rows, NIST
splits by operation profile, CIS merges into coarse entries), so cell counts
differ and a whole-matrix diff would be meaningless. Every comparison here is
restricted to shared asset ids and reports the coverage it achieved.

Writes ``FRAMEWORK_RESULTS.md``, ``framework_results.json`` and
``framework_sensitivity.csv`` into ``reports/experiments/v7/``.

Run:  uv run python scripts/compare_v7_frameworks.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
V7_DIR = REPO_ROOT / "reports" / "experiments" / "v7"
BASELINE_DIR = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r_nacombo"

SERVERS = ("fs_corp_filesystem", "github_helios", "slack_vireo", "calendar_aurora")
ARMS = ("iso", "nist", "cis")
ARM_LABELS = {
    "nacombo": "baseline register (v5r nacombo)",
    "iso": "ISO/IEC 27001:2022 A.5.9 + A.8.3",
    "nist": "NIST FIPS 199 / SP 800-60 + AC-3",
    "cis": "CIS Controls v8.1 Control 3",
}
BANDS = ("low", "medium", "high", "critical", "na")


class MissingArtifactError(FileNotFoundError):
    """Raised when an arm has not been scanned yet.

    Reported by name rather than skipped: a comparison table silently missing an
    arm reads as "the arm agreed", which is the opposite of what it means.
    """


def load_arm(arm: str, server: str) -> dict:
    """One arm's scan artifact for one server."""
    path = (
        BASELINE_DIR / f"{server}.json"
        if arm == "nacombo"
        else V7_DIR / f"five_level_v2_policy_v7_{arm}" / f"{server}.json"
    )
    if not path.exists():
        raise MissingArtifactError(f"{arm}/{server}: no artifact at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def scored_cells(table: dict) -> dict[str, float]:
    """``{"tool|asset": score}`` for every cell the arm actually scored."""
    return {
        f"{tool}|{asset}": score
        for asset, row in table["cells"].items()
        for tool, score in row.items()
        if score is not None
    }


def arm_summary(table: dict) -> dict:
    """Distributional shape of one arm on one server — no ground truth needed."""
    sens = table["asset_sensitivity"]
    cells = scored_cells(table)
    total = sum(len(row) for row in table["cells"].values())
    impact_source = table.get("tool_impact_source", {})
    blast = [v for v in table["blast_radius"].values() if v is not None]
    return {
        "assets": len(table["asset_ids"]),
        "tools": len(table["tool_impact"]),
        "cells": total,
        "scored": len(cells),
        "na": total - len(cells),
        "na_rate": round((total - len(cells)) / total, 3) if total else 0.0,
        "mean_sensitivity": round(statistics.fmean(sens.values()), 2) if sens else 0.0,
        "mean_blast": round(statistics.fmean(blast), 2) if blast else 0.0,
        "mean_impact": (
            round(statistics.fmean(table["tool_impact"].values()), 2)
            if table["tool_impact"]
            else 0.0
        ),
        "mean_score": round(statistics.fmean(cells.values()), 1) if cells else 0.0,
        "max_score": max(cells.values()) if cells else 0,
        "bands": {b: table["band_distribution"].get(b, 0) for b in BANDS},
        "static_ladder_share": (
            round(
                sum(1 for v in impact_source.values() if v == "static_ladder") / len(impact_source),
                3,
            )
            if impact_source
            else 0.0
        ),
        "policy_doc": table.get("description_source", ""),
    }


def sensitivity_delta(reference: dict, arm: dict) -> dict:
    """Per-asset sensitivity comparison over the asset ids both registers carry.

    Reports coverage explicitly. A framework that renamed or merged an asset is
    not "wrong" — it is describing the same deployment differently — so the
    unshared ids are counted and named rather than quietly dropped.
    """
    ref_sens, arm_sens = reference["asset_sensitivity"], arm["asset_sensitivity"]
    shared = sorted(set(ref_sens) & set(arm_sens))
    diffs = [arm_sens[a] - ref_sens[a] for a in shared]
    return {
        "shared_assets": len(shared),
        "reference_only": sorted(set(ref_sens) - set(arm_sens)),
        "arm_only": sorted(set(arm_sens) - set(ref_sens)),
        "exact": (round(sum(1 for d in diffs if d == 0) / len(diffs), 3) if diffs else None),
        "within_one": (
            round(sum(1 for d in diffs if abs(d) <= 1) / len(diffs), 3) if diffs else None
        ),
        "mad": round(statistics.fmean(abs(d) for d in diffs), 3) if diffs else None,
        "bias": round(statistics.fmean(diffs), 3) if diffs else None,
        "per_asset": {a: (ref_sens[a], arm_sens[a]) for a in shared},
    }


def cell_delta(reference: dict, arm: dict) -> dict:
    """Per-cell score comparison over cells both arms scored on shared assets."""
    ref_cells, arm_cells = scored_cells(reference), scored_cells(arm)
    shared_assets = set(reference["asset_sensitivity"]) & set(arm["asset_sensitivity"])
    keys = [k for k in set(ref_cells) & set(arm_cells) if k.split("|", 1)[1] in shared_assets]
    diffs = [arm_cells[k] - ref_cells[k] for k in keys]
    ref_bands = reference["bands"]
    arm_bands = arm["bands"]
    flips = [
        (
            k,
            ref_bands[k.split("|", 1)[1]][k.split("|", 1)[0]],
            arm_bands[k.split("|", 1)[1]][k.split("|", 1)[0]],
        )
        for k in keys
        if ref_bands[k.split("|", 1)[1]][k.split("|", 1)[0]]
        != arm_bands[k.split("|", 1)[1]][k.split("|", 1)[0]]
    ]
    return {
        "comparable_cells": len(keys),
        "identical": sum(1 for d in diffs if d == 0),
        "agreement": round(sum(1 for d in diffs if d == 0) / len(diffs), 3) if diffs else None,
        "mean_abs_delta": round(statistics.fmean(abs(d) for d in diffs), 1) if diffs else None,
        "bias": round(statistics.fmean(diffs), 1) if diffs else None,
        "band_flips": len(flips),
        "band_flip_rate": round(len(flips) / len(keys), 3) if keys else None,
        "biggest_moves": sorted(
            (
                {
                    "cell": k,
                    "reference": ref_cells[k],
                    "arm": arm_cells[k],
                    "delta": arm_cells[k] - ref_cells[k],
                }
                for k in keys
            ),
            key=lambda r: -abs(r["delta"]),
        )[:5],
    }


def cross_arm_agreement(tables: dict[str, dict]) -> dict:
    """Do the three frameworks agree, on the assets all three carry?"""
    present = [a for a in ARMS if a in tables]
    if len(present) < 2:
        return {"shared_assets": 0, "unanimous": None, "spread": None, "disagreements": []}
    sens = [tables[a]["asset_sensitivity"] for a in present]
    shared = sorted(set.intersection(*(set(s) for s in sens)))
    rows = [(a, [s[a] for s in sens]) for a in shared]
    spreads = [max(v) - min(v) for _, v in rows]
    return {
        "arms": present,
        "shared_assets": len(shared),
        "unanimous": (
            round(sum(1 for s in spreads if s == 0) / len(spreads), 3) if spreads else None
        ),
        "within_one": (
            round(sum(1 for s in spreads if s <= 1) / len(spreads), 3) if spreads else None
        ),
        "mean_spread": round(statistics.fmean(spreads), 2) if spreads else None,
        "disagreements": [
            {"asset": a, **dict(zip(present, v)), "spread": max(v) - min(v)}
            for a, v in rows
            if max(v) - min(v) >= 2
        ],
    }


def _bands_cell(summary: dict) -> str:
    b = summary["bands"]
    return f"{b['low']}/{b['medium']}/{b['high']}/{b['critical']}"


def render_markdown(results: dict) -> str:
    """The comparison as a readable report."""
    out: list[str] = [
        "# v7 — the framework-native policy arms",
        "",
        "Four organizations, four policy documents each, one scanner. Everything",
        "except the policy document and its matching sensitivity prompt is held",
        "fixed: same tool catalogs, same deterministic impact ladder, same blast",
        "rubric, same assembly. A difference between arms is attributable to how",
        "the organization wrote its policy.",
        "",
        "| arm | document |",
        "|---|---|",
    ]
    out.extend(f"| `{arm}` | {label} |" for arm, label in ARM_LABELS.items())
    out += [
        "",
        "## No accuracy numbers here, and why",
        "",
        "None of these four servers has held-out numeric ground truth.",
        "`github_helios`, `slack_vireo` and `calendar_aurora` have no section in",
        "`server-profiles.md` at all, and `fs_corp_filesystem`'s profile uses",
        "path-shaped asset ids that do not align with the policy register's",
        "concept ids. So this report measures *movement* against the `nacombo`",
        "baseline and *agreement* between the frameworks — never correctness.",
        "",
        "## Register shape per arm",
        "",
        "The arms were written to diverge in shape on purpose: ISO keeps the",
        "baseline's rows and adds columns, NIST splits a row whose read and write",
        "categorize differently, CIS merges non-sensitive data into coarse entries",
        "as Safeguard 3.2 permits.",
        "",
        "| server | " + " | ".join(f"{a} assets" for a in ("nacombo", *ARMS)) + " |",
        "|---" * 5 + "|",
    ]
    for server in SERVERS:
        cells = [
            str(results["summaries"][server][a]["assets"])
            if a in results["summaries"][server]
            else "—"
            for a in ("nacombo", *ARMS)
        ]
        out.append(f"| `{server}` | " + " | ".join(cells) + " |")

    out += [
        "",
        "## Distributional shape",
        "",
        "| server | arm | assets | scored | N/A | mean sens | mean blast | "
        "mean impact | mean score | low/med/high/crit |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for server in SERVERS:
        for arm in ("nacombo", *ARMS):
            s = results["summaries"][server].get(arm)
            if not s:
                out.append(f"| `{server}` | `{arm}` | — | — | — | — | — | — | — | not scanned |")
                continue
            out.append(
                f"| `{server}` | `{arm}` | {s['assets']} | {s['scored']} | "
                f"{s['na_rate']:.0%} | {s['mean_sensitivity']} | {s['mean_blast']} | "
                f"{s['mean_impact']} | {s['mean_score']} | {_bands_cell(s)} |"
            )

    out += [
        "",
        "## Sensitivity vs the baseline, on shared asset ids",
        "",
        "`exact` and `within one` are agreement with `nacombo`, not accuracy.",
        "`coverage` is how many of the baseline's assets the arm's register",
        "still carries under the same id.",
        "",
        "| server | arm | shared | coverage | exact | within one | mean abs Δ | bias |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for server in SERVERS:
        base_assets = results["summaries"][server]["nacombo"]["assets"]
        for arm in ARMS:
            d = results["sensitivity"][server].get(arm)
            if not d:
                out.append(f"| `{server}` | `{arm}` | — | — | — | — | — | not scanned |")
                continue
            out.append(
                f"| `{server}` | `{arm}` | {d['shared_assets']} | "
                f"{d['shared_assets'] / base_assets:.0%} | {d['exact']:.0%} | "
                f"{d['within_one']:.0%} | {d['mad']} | {d['bias']:+.2f} |"
            )

    out += [
        "",
        "## Cell scores vs the baseline",
        "",
        "Restricted to cells both arms scored on an asset id they share.",
        "",
        "| server | arm | comparable cells | identical | mean abs Δ | bias | band flips |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for server in SERVERS:
        for arm in ARMS:
            d = results["cells"][server].get(arm)
            if not d or not d["comparable_cells"]:
                out.append(f"| `{server}` | `{arm}` | — | — | — | — | not scanned |")
                continue
            out.append(
                f"| `{server}` | `{arm}` | {d['comparable_cells']} | "
                f"{d['agreement']:.0%} | {d['mean_abs_delta']} | {d['bias']:+.1f} | "
                f"{d['band_flips']} ({d['band_flip_rate']:.0%}) |"
            )

    out += [
        "",
        "## Do the three frameworks agree with each other?",
        "",
        "The question this experiment exists to answer: three organizations",
        "describe the same deployment under three different standards. Do they",
        "arrive at the same severities?",
        "",
        "| server | shared assets | unanimous | within one | mean spread | ≥2-tier splits |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for server in SERVERS:
        a = results["cross_arm"][server]
        if not a["shared_assets"]:
            out.append(f"| `{server}` | — | — | — | — | not enough arms scanned |")
            continue
        out.append(
            f"| `{server}` | {a['shared_assets']} | {a['unanimous']:.0%} | "
            f"{a['within_one']:.0%} | {a['mean_spread']} | {len(a['disagreements'])} |"
        )

    splits = [
        (server, d) for server in SERVERS for d in results["cross_arm"][server]["disagreements"]
    ]
    if splits:
        out += [
            "",
            "### Where the frameworks split by two tiers or more",
            "",
            "| server | asset | " + " | ".join(ARMS) + " | spread |",
            "|---|---|" + "---|" * (len(ARMS) + 1),
        ]
        for server, d in splits:
            vals = " | ".join(str(d.get(a, "—")) for a in ARMS)
            out.append(f"| `{server}` | `{d['asset']}` | {vals} | {d['spread']} |")

    missing = results.get("missing", [])
    if missing:
        out += [
            "",
            "## Not scanned",
            "",
            "These artifacts were absent when the comparison ran, so every row",
            "above that would have used them is marked rather than omitted:",
            "",
        ]
        out.extend(f"- {m}" for m in missing)
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=V7_DIR)
    args = parser.parse_args(argv)

    results: dict = {
        "summaries": {},
        "sensitivity": {},
        "cells": {},
        "cross_arm": {},
        "missing": [],
    }
    for server in SERVERS:
        tables: dict[str, dict] = {}
        for arm in ("nacombo", *ARMS):
            try:
                tables[arm] = load_arm(arm, server)
            except MissingArtifactError as exc:
                results["missing"].append(str(exc))
        if "nacombo" not in tables:
            print(f"[FAIL] {server}: no baseline artifact; skipping")
            continue
        reference = tables["nacombo"]
        results["summaries"][server] = {a: arm_summary(t) for a, t in tables.items()}
        results["sensitivity"][server] = {
            a: sensitivity_delta(reference, t) for a, t in tables.items() if a != "nacombo"
        }
        results["cells"][server] = {
            a: cell_delta(reference, t) for a, t in tables.items() if a != "nacombo"
        }
        results["cross_arm"][server] = cross_arm_agreement(tables)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "framework_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    (args.out_dir / "FRAMEWORK_RESULTS.md").write_text(render_markdown(results), encoding="utf-8")

    with (args.out_dir / "framework_sensitivity.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["server", "asset", "nacombo", *ARMS])
        for server in SERVERS:
            summaries = results["summaries"].get(server, {})
            if "nacombo" not in summaries:
                continue
            base = load_arm("nacombo", server)["asset_sensitivity"]
            arm_sens = {}
            for arm in ARMS:
                try:
                    arm_sens[arm] = load_arm(arm, server)["asset_sensitivity"]
                except MissingArtifactError:
                    arm_sens[arm] = {}
            every_asset = sorted(set(base) | {a for s in arm_sens.values() for a in s})
            for asset in every_asset:
                writer.writerow(
                    [
                        server,
                        asset,
                        base.get(asset, ""),
                        *(arm_sens[arm].get(asset, "") for arm in ARMS),
                    ]
                )

    print(
        f"[v7] wrote FRAMEWORK_RESULTS.md, framework_results.json and "
        f"framework_sensitivity.csv to {args.out_dir}"
    )
    if results["missing"]:
        print(f"[v7] {len(results['missing'])} artifact(s) missing:")
        for m in results["missing"]:
            print(f"      {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
