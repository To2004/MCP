"""Evaluate a scan's primitives with the independent judge (evaluation-only).

For each committed scan (``reports/scan/<stem>.json``) this re-derives every
primitive — tool_impact, asset_sensitivity, blast_radius — with the JUDGE_*
prompts (an independent, skeptical reviewer), and compares the judge's value to
the value the base-model scan produced. It answers two questions:

* **How good are the scores?** High agreement = the base model is confident and an
  independent pass concurs; the judge is redundant (which is why it's off).
* **Where to improve?** The disagreements — and their *direction* (does the judge
  systematically want higher or lower on a given primitive?) — point at the
  prompts/rules to tighten.

Needs the local LLM (run on a GPU node). Writes reports/evaluation/judge_agreement.md.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.scanner.scan import build_registry
from mcp_security.static_scoring import prompts

REPO = Path(__file__).resolve().parent.parent
SCAN_DIR = REPO / "reports" / "scan"

# scan stem -> how to rebuild its registry (offline, deterministic).
SERVERS: dict[str, dict] = {
    "fs_corp_filesystem":   {"kind": "filesystem", "root": "demo/corp_filesystem",   "server": "fs:corp_filesystem",   "by_file": True},
    "fs_fintech_fs":        {"kind": "filesystem", "root": "demo/fintech_fs",         "server": "fs:fintech_fs",        "by_file": True},
    "fs_law_firm_fs":       {"kind": "filesystem", "root": "demo/law_firm_fs",        "server": "fs:law_firm_fs",       "by_file": True},
    "fs_media_studio_fs":   {"kind": "filesystem", "root": "demo/media_studio_fs",    "server": "fs:media_studio_fs",   "by_file": True},
    "fs_medical_clinic_fs": {"kind": "filesystem", "root": "demo/medical_clinic_fs",  "server": "fs:medical_clinic_fs", "by_file": True},
    "sqlite_cbg_sqlite":    {"kind": "sqlite",     "root": "demo/cbg_sqlite/cbg.db",  "server": "sqlite:cbg_sqlite"},
    "sqlite_devops_sqlite": {"kind": "sqlite",     "root": "demo/devops_sqlite/devops.db", "server": "sqlite:devops_sqlite"},
    "github_cbg":           {"kind": "github",     "server": "github:cbg"},
    "slack_cbg":            {"kind": "slack",      "server": "slack:cbg"},
    "calendar_cbg":         {"kind": "calendar",   "server": "calendar:cbg"},
}

FIELD_RANGE = {"tool_impact": (1, 3), "sensitivity": (1, 5), "blast_radius": (1, 5)}


def _clamp(value: object, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _judge(field: str, key: str, item_json: dict, proposed_value: int, profile: dict) -> int | None:
    """Ask the judge to independently re-derive one primitive; None if unusable."""
    prompt = (
        prompts.JUDGE_SYSTEM.format(domain_profile=json.dumps(profile, indent=2))
        + "\n\n"
        + prompts.JUDGE_USER.format(
            field_name=field, item_key=key,
            item_json=json.dumps(item_json, indent=2),
            proposed_json=json.dumps({field: proposed_value}),
        )
    )
    resp = query_ollama(prompt)
    if not isinstance(resp, dict) or "judged_value" not in resp:
        return None
    low, high = FIELD_RANGE[field]
    return _clamp(resp.get("judged_value"), low, high, proposed_value)


def evaluate_server(stem: str, cfg: dict, blast_sample: int) -> dict:
    """Judge every impact/sensitivity primitive and (a sample of) blast cells."""
    scan = json.loads((SCAN_DIR / f"{stem}.json").read_text("utf-8"))
    profile = scan.get("inferred_profile", {})
    reg = build_registry(
        cfg["kind"], root=Path(cfg["root"]) if cfg.get("root") else None,
        server=cfg.get("server"), by_file=cfg.get("by_file", False),
    )
    tools = {t.name: t for t in reg.tools}
    assets = {a.asset_id: a for a in reg.assets}

    records: list[dict] = []  # {field, key, base, judged}

    for tool_name, base in scan.get("tool_impact", {}).items():
        if tool_name not in tools:
            continue
        j = _judge("tool_impact", tool_name, tools[tool_name].to_prompt_json(), base, profile)
        if j is not None:
            records.append({"field": "tool_impact", "key": tool_name, "base": base, "judged": j})

    for asset_id, base in scan.get("asset_sensitivity", {}).items():
        if asset_id not in assets:
            continue
        j = _judge("sensitivity", asset_id, assets[asset_id].to_prompt_json(), base, profile)
        if j is not None:
            records.append({"field": "sensitivity", "key": asset_id, "base": base, "judged": j})

    blast_items = list(scan.get("blast_radius", {}).items())
    # Deterministic, spread-out sample so a long run is bounded (index stride).
    if blast_sample and len(blast_items) > blast_sample:
        stride = max(1, len(blast_items) // blast_sample)
        blast_items = blast_items[::stride][:blast_sample]
    for key, base in blast_items:
        tool_name, _, asset_id = key.partition("|")
        if tool_name not in tools or asset_id not in assets:
            continue
        item = {"tool": tools[tool_name].to_prompt_json(), "asset": assets[asset_id].to_prompt_json()}
        j = _judge("blast_radius", key, item, base, profile)
        if j is not None:
            records.append({"field": "blast_radius", "key": key, "base": base, "judged": j})

    return {"stem": stem, "records": records}


def _agg(records: list[dict]) -> dict:
    by_field: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_field[r["field"]].append(r)
    out = {}
    for field, rs in by_field.items():
        n = len(rs)
        agree = sum(1 for r in rs if r["base"] == r["judged"])
        signed = sum(r["judged"] - r["base"] for r in rs)
        absdelta = sum(abs(r["judged"] - r["base"]) for r in rs)
        out[field] = {
            "n": n, "agree": agree,
            "agree_pct": round(100 * agree / n, 1) if n else 0.0,
            "mean_signed": round(signed / n, 2) if n else 0.0,
            "mean_abs": round(absdelta / n, 2) if n else 0.0,
        }
    return out


def build_report(results: list[dict]) -> str:
    all_records = [r for res in results for r in res["records"]]
    overall = _agg(all_records)
    lines = [
        "# Judge-agreement evaluation — how well an independent reviewer concurs "
        "with the scans",
        "",
        "The judge (evaluation-only) re-derives each primitive skeptically and is "
        "compared to the base-model scan. High agreement = confident, stable scores; "
        "a systematic signed gap on a primitive = a prompt/rule to tighten.",
        "",
        "## Overall (all servers)",
        "",
        "| primitive | n | agree | mean Δ (judge−base) | mean |Δ| |",
        "| --- | --- | --- | --- | --- |",
    ]
    for field in ("tool_impact", "sensitivity", "blast_radius"):
        m = overall.get(field)
        if not m:
            continue
        lines.append(
            f"| {field} | {m['n']} | {m['agree']}/{m['n']} ({m['agree_pct']}%) | "
            f"{m['mean_signed']:+} | {m['mean_abs']} |"
        )
    lines += ["", "## Per server", "",
              "| server | impact agree | sensitivity agree | blast agree |",
              "| --- | --- | --- | --- |"]
    for res in results:
        m = _agg(res["records"])
        def cell(f: str) -> str:
            x = m.get(f)
            return f"{x['agree']}/{x['n']} ({x['agree_pct']}%)" if x else "—"
        lines.append(f"| {res['stem']} | {cell('tool_impact')} | {cell('sensitivity')} | "
                     f"{cell('blast_radius')} |")

    # Biggest disagreements (improvement targets), by |Δ| then field.
    disagree = [r for r in all_records if r["base"] != r["judged"]]
    disagree.sort(key=lambda r: abs(r["judged"] - r["base"]), reverse=True)
    lines += ["", "## Largest disagreements (where to improve)", ""]
    if not disagree:
        lines.append("_None — the judge agreed on every primitive._")
    for r in disagree[:25]:
        lines.append(f"- `{r['field']}` **{r['key']}**: base {r['base']} → judge {r['judged']}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--servers", nargs="*", default=list(SERVERS),
                    help="scan stems to evaluate (default: all 10)")
    ap.add_argument("--blast-sample", type=int, default=30,
                    help="blast cells to judge per server (0 = all). Default 30.")
    ap.add_argument("--out", type=Path,
                    default=REPO / "reports" / "evaluation" / "judge_agreement.md")
    args = ap.parse_args()

    results = []
    for stem in args.servers:
        if stem not in SERVERS:
            print(f"[skip] unknown server: {stem}")
            continue
        print(f"[judge] {stem} ...", flush=True)
        results.append(evaluate_server(stem, SERVERS[stem], args.blast_sample))

    report = build_report(results)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n[wrote {args.out}]")


if __name__ == "__main__":
    main()
