"""Holistic, framework-grounded LLM review of a scan's risk heatmap.

Unlike the per-primitive judge (which re-scores one value in isolation), this
reads a whole matrix and asks an independent reviewer whether each cell is
COHERENT relative to its neighbours — the calibration question. It is:

* **LLM-only** — every verdict comes from the model; no hardcoded rule decides.
* **general** — the prompt states risk-assessment PRINCIPLES (NIST SP 800-30
  risk = impact x likelihood; FIPS-199 asset categorization), not domain rules,
  so it works for any MCP server.
* **leakage-free** — the reviewer sees only the scan's own matrix and inferred
  domain; it never reads the committed ground-truth tables.

Output: per-cell verdicts (ok / too_high / too_low) and, crucially, the
SYSTEMATIC PATTERNS across verdicts — which tool/asset kinds are consistently
over- or under-scored. Those patterns are the signal for improving the general
scoring guidelines (the proposer prompts), not for patching individual cells.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.static_scoring import prompts  # noqa: F401  (kept for parity/imports)

REPO = Path(__file__).resolve().parent.parent
SCAN_DIR = REPO / "reports" / "scan"

# The reviewer reads only a scan's own <stem>.json (no registry), so any scan
# stem present in reports/scan/ can be reviewed; this list is just the default set.
SERVERS: dict[str, dict] = {s: {} for s in (
    "fs_corp_filesystem", "fs_fintech_fs", "fs_law_firm_fs", "fs_media_studio_fs",
    "fs_medical_clinic_fs", "sqlite_cbg_sqlite", "sqlite_devops_sqlite",
    "github_cbg", "slack_cbg", "calendar_cbg",
)}

REVIEW_SYSTEM = """You are a security risk reviewer auditing a STATIC risk matrix for
an MCP server, grounded in standard practice: NIST SP 800-30 (risk = impact x
likelihood) and FIPS-199 asset categorization. You reason from PRINCIPLES, not
from any server-specific rule list.

The matrix scores each (asset, tool) cell as:
    score = asset_sensitivity(1-5) x blast_radius(1-5) x tool_impact(1-3)
- asset_sensitivity: value/confidentiality of the asset (5 = secrets/regulated/PII,
  1 = public).
- blast_radius: how far ONE call reaches (1 = one item, 5 = sweeps/destroys a whole
  scope). A single-item touch is small even on a valuable asset.
- tool_impact: 1 read-only, 2 recoverable write, 3 destructive/irreversible.

Your job is COHERENCE, not exact numbers. Given the row below (one asset, every
tool acting on it) and the cross-asset context for each tool, decide for each cell
whether its score is reasonable AND consistent with its neighbours:
- Across TOOLS on this asset, scores should rise with impact and reach.
- The SAME TOOL should score higher on more-sensitive assets, lower on less.
A cell is fine if it is in the right ballpark and correctly ordered vs peers; only
flag clear miscalibration. Output ONLY valid JSON, no prose, no fences."""

REVIEW_USER = """Inferred domain: {domain}

ASSET under review: "{asset}"  (sensitivity {sens})
Tools acting on it (impact, blast, score, atomic op):
{rows}

Cross-asset context (how each tool scores on OTHER assets, for calibration):
{context}

For every tool on this asset, return:
{{"cells": [{{"tool": <name>, "verdict": "ok"|"too_high"|"too_low",
  "reason": "<one clause; cite a neighbour when relevant>"}}],
  "row_note": "<one sentence on this row's overall calibration>"}}"""


def _load(stem: str) -> dict:
    return json.loads((SCAN_DIR / f"{stem}.json").read_text("utf-8"))


def _context_line(tool: str, scan: dict) -> str:
    """Compact 'this tool across assets' view: sens->score, for calibration."""
    pairs = []
    for asset, row in scan.get("cells", {}).items():
        if tool in row:
            pairs.append((scan["asset_sensitivity"].get(asset, "?"), row[tool]))
    pairs.sort()
    shown = ", ".join(f"sens{s}:{sc:g}" for s, sc in pairs[:8])
    return f"{tool}: {shown}"


def review_server(stem: str) -> dict:
    scan = _load(stem)
    domain = scan.get("inferred_profile", {}).get("mcp_kind", scan.get("mcp_kind", stem))
    impacts = scan.get("tool_impact", {})
    blast = scan.get("blast_radius", {})
    atomic = {t: v.get("primary_op", "") for t, v in scan.get("tool_atomic_ops", {}).items()}
    cells = scan.get("cells", {})
    sens = scan.get("asset_sensitivity", {})

    verdicts: list[dict] = []
    for asset, row in cells.items():
        rows = "\n".join(
            f"- {t}: impact {impacts.get(t, '?')}, blast {blast.get(f'{t}|{asset}', '?')}, "
            f"score {sc:g}, op {atomic.get(t, '?')}"
            for t, sc in row.items()
        )
        context = "\n".join(_context_line(t, scan) for t in row)
        prompt = REVIEW_SYSTEM + "\n\n" + REVIEW_USER.format(
            domain=domain, asset=asset, sens=sens.get(asset, "?"), rows=rows, context=context
        )
        resp = query_ollama(prompt)
        if not isinstance(resp, dict) or not isinstance(resp.get("cells"), list):
            continue
        for c in resp["cells"]:
            if isinstance(c, dict) and c.get("tool") in row:
                verdicts.append({
                    "asset": asset, "tool": c["tool"],
                    "verdict": c.get("verdict", "ok"),
                    "reason": str(c.get("reason", ""))[:160],
                    "score": row[c["tool"]],
                    "op": atomic.get(c["tool"], ""),
                })
    return {"stem": stem, "verdicts": verdicts}


def build_report(results: list[dict]) -> str:
    lines = [
        "# Heatmap coherence review — framework-grounded LLM judge (general, no leakage)",
        "",
        "An independent reviewer reads each cell WITH its neighbours and judges "
        "coherence (right ballpark + correct ordering), not exact numbers. The "
        "systematic patterns below are the guideline-improvement targets.",
        "",
    ]
    for res in results:
        v = res["verdicts"]
        n = len(v)
        counts = Counter(x["verdict"] for x in v)
        ok = counts.get("ok", 0)
        lines += [
            f"## {res['stem']}",
            "",
            f"- **{ok}/{n} cells coherent ({100 * ok / n:.0f}%)** · "
            f"too_high {counts.get('too_high', 0)} · too_low {counts.get('too_low', 0)}",
            "",
        ]
        # Systematic patterns: which atomic ops are most flagged, and direction.
        by_op: dict[str, Counter] = {}
        for x in v:
            if x["verdict"] != "ok":
                by_op.setdefault(x["op"], Counter())[x["verdict"]] += 1
        if by_op:
            lines.append("Miscalibration by operation (pattern → guideline signal):")
            for op, c in sorted(by_op.items(), key=lambda kv: -sum(kv[1].values())):
                lines.append(f"- `{op}`: too_high {c.get('too_high', 0)}, too_low {c.get('too_low', 0)}")
            lines.append("")
        flagged = [x for x in v if x["verdict"] != "ok"]
        flagged.sort(key=lambda x: x["verdict"])
        lines.append("Flagged cells:")
        for x in flagged[:30]:
            lines.append(f"- [{x['verdict']}] `{x['tool']}` × `{x['asset']}` "
                         f"(score {x['score']:g}) — {x['reason']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--servers", nargs="*", default=list(SERVERS))
    ap.add_argument("--out", type=Path, default=REPO / "reports" / "evaluation" / "heatmap_review.md")
    args = ap.parse_args()
    results = [review_server(s) for s in args.servers if s in SERVERS]
    report = build_report(results)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n[wrote {args.out}]")


if __name__ == "__main__":
    main()
