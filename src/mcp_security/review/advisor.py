"""Results advisor — reads the scores/results and proposes what to do next.

Unlike the judge (which audits soundness), the advisor reads the *outcomes* — the
scanner-vs-ground-truth agreement, the band distribution of each scan, and the
ranked-call coverage — and recommends concrete next steps: where accuracy is weak,
what coverage gaps to close, and which experiments would strengthen the claims.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAN_DIR = REPO_ROOT / "reports" / "scan"
ACCURACY = REPO_ROOT / "reports" / "evaluation" / "scanner_accuracy.md"
RANKED = REPO_ROOT / "reports" / "ranked_calls.csv"

ADVISOR_SYSTEM = """You are a research advisor for a security project. You are
given the measured results of an MCP risk scanner: how well its LLM-derived risk
matrices agree with reviewed ground truth, the band distribution of each scan, and
the coverage of a ranked corpus of captured tool calls. Give a focused, technical
assessment — not platitudes.

Output ONLY valid JSON, no prose, no fences:
{"strengths": [str], "weaknesses": [str],
 "next_steps": [{"action": str, "why": str, "priority": "high"|"medium"|"low"}],
 "risks_to_validity": [str]}"""

ADVISOR_USER = """RESULTS DIGEST:
{digest}

Return the assessment JSON."""


def _digest() -> str:
    """Build a compact text digest of the current results for the LLM."""
    parts: list[str] = []
    if ACCURACY.exists():
        parts.append("## Scanner accuracy (vs ground truth)\n" + ACCURACY.read_text("utf-8"))

    if SCAN_DIR.exists():
        lines = ["## Scans (band distributions)"]
        for path in sorted(SCAN_DIR.glob("*.json")):
            data = json.loads(path.read_text("utf-8"))
            lines.append(
                f"- {path.stem}: kind={data.get('mcp_kind')} "
                f"provenance={data.get('provenance')} bands={data.get('band_distribution')} "
                f"tools={len(data.get('tool_impact', {}))} assets={len(data.get('asset_sensitivity', {}))} "
                f"judge_overrides={data.get('crosscheck_summary', {}).get('overridden')}"
            )
        parts.append("\n".join(lines))

    if RANKED.exists():
        rows = list(csv.DictReader(RANKED.open(encoding="utf-8")))
        bands = Counter(r["band"] for r in rows)
        servers = Counter(r["server"] for r in rows)
        scorable = sum(1 for r in rows if r.get("scorable") == "True")
        parts.append(
            "## Ranked calls\n"
            f"- total={len(rows)} resolved_to_cell={scorable} bands={dict(bands)}\n"
            f"- per server={dict(servers)}"
        )
    return "\n\n".join(parts) if parts else "(no results found — run the scanner and ranker first)"


def advise() -> dict:
    """Ask the LLM for an assessment of the current results."""
    result = query_ollama(ADVISOR_SYSTEM + "\n\n" + ADVISOR_USER.format(digest=_digest()))
    if not isinstance(result, dict) or "next_steps" not in result:
        return {
            "strengths": [], "weaknesses": [],
            "next_steps": [{"action": "re-run with the local LLM available",
                            "why": "model gave no usable assessment", "priority": "high"}],
            "risks_to_validity": [],
        }
    return result


def to_markdown(assessment: dict) -> str:
    """Render the advisor's assessment as markdown."""
    lines = ["# Results advisor", "", "## Strengths"]
    lines += [f"- {s}" for s in assessment.get("strengths", [])] or ["- (none)"]
    lines += ["", "## Weaknesses"]
    lines += [f"- {w}" for w in assessment.get("weaknesses", [])] or ["- (none)"]
    lines += ["", "## Next steps (prioritised)"]
    steps = sorted(assessment.get("next_steps", []),
                   key=lambda s: {"high": 0, "medium": 1, "low": 2}.get(s.get("priority"), 3))
    for s in steps:
        lines.append(f"- **[{s.get('priority', '?')}] {s.get('action', '')}** — {s.get('why', '')}")
    lines += ["", "## Risks to validity"]
    lines += [f"- {r}" for r in assessment.get("risks_to_validity", [])] or ["- (none)"]
    lines.append("")
    return "\n".join(lines)
