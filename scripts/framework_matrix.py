"""Positioning matrix: this framework vs. the closest risk-scoring works.

Authored reference data (not computed) distilled from the cited papers, rendered to
``reports/evaluation/framework_matrix.{md,json}`` so the comparison is versioned and
regenerable. The axes are the ones that distinguish a per-invocation, server-side,
graduated MCP risk scorer from neighbouring approaches; the matrix shows that no prior
work occupies the same cell.

Run:  uv run python scripts/framework_matrix.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_MD = REPO_ROOT / "reports" / "evaluation" / "framework_matrix.md"
OUT_JSON = REPO_ROOT / "reports" / "evaluation" / "framework_matrix.json"

AXES = [
    "scores", "timing", "output", "ground_truth", "threat_direction",
    "per_call_granularity", "argument_aware", "public_dataset",
]

# Each row: name -> {axis: value}. Values kept short for a paper table.
MATRIX: dict[str, dict[str, str]] = {
    "McpRisk (ours)": {
        "scores": "MCP tool invocation risk per (tool, asset)",
        "timing": "static (design) + dynamic (request)",
        "output": "graduated band 1–4 / 0–60 score",
        "ground_truth": "external MCP attack benchmarks",
        "threat_direction": "server is victim (client→server)",
        "per_call_granularity": "yes — per (tool, asset, args)",
        "argument_aware": "partial (param magnitude; contextual LLM planned)",
        "public_dataset": "released",
    },
    "CVSS v3": {
        "scores": "software vulnerability severity",
        "timing": "static, once per vuln",
        "output": "0–10 score",
        "ground_truth": "NVD / analyst consensus",
        "threat_direction": "n/a (software)",
        "per_call_granularity": "no (per vuln)",
        "argument_aware": "no",
        "public_dataset": "yes (NVD)",
    },
    "AIVSS (OWASP)": {
        "scores": "agentic-AI vulnerability severity",
        "timing": "static",
        "output": "CVSS base × agentic factors → 0–10",
        "ground_truth": "expert rubric",
        "threat_direction": "agent system (generic)",
        "per_call_granularity": "no (per vuln / system)",
        "argument_aware": "no",
        "public_dataset": "rubric only",
    },
    "AgenTRIM": {
        "scores": "tool-driven agency risk (least-privilege)",
        "timing": "offline + runtime per step",
        "output": "allow/deny + risk",
        "ground_truth": "none public (AgentDojo task success)",
        "threat_direction": "agent tool misuse / injection",
        "per_call_granularity": "yes — per tool call",
        "argument_aware": "partial",
        "public_dataset": "no labeled set",
    },
    "AURA": {
        "scores": "agent autonomy risk",
        "timing": "design + runtime",
        "output": "gamma-based score",
        "ground_truth": "none (framework)",
        "threat_direction": "agent autonomy (generic)",
        "per_call_granularity": "per action",
        "argument_aware": "no",
        "public_dataset": "no",
    },
    "MCP-RiskCue": {
        "scores": "risk inferred from MCP server logs",
        "timing": "runtime (post-hoc on logs)",
        "output": "risk label/severity",
        "ground_truth": "synthetic logs + human labels",
        "threat_direction": "server-side telemetry",
        "per_call_granularity": "per log event",
        "argument_aware": "yes (reads logs)",
        "public_dataset": "limited",
    },
    "ASTRA": {
        "scores": "context-/steerability-adjusted risk",
        "timing": "design",
        "output": "ordinal risk tiers",
        "ground_truth": "none (framework)",
        "threat_direction": "application context (generic)",
        "per_call_granularity": "no",
        "argument_aware": "no",
        "public_dataset": "no",
    },
    "R-Judge": {
        "scores": "safety-risk awareness from agent traces",
        "timing": "runtime / post-hoc",
        "output": "binary safe / unsafe",
        "ground_truth": "569 human-labeled records",
        "threat_direction": "agent safety (mixed)",
        "per_call_granularity": "per trajectory step",
        "argument_aware": "yes (reads trace)",
        "public_dataset": "yes",
    },
    "Permission-risk (Entra)": {
        "scores": "OAuth permission/capability risk",
        "timing": "static, at grant time",
        "output": "ordinal risk score",
        "ground_truth": "expert consensus (769 perms)",
        "threat_direction": "capability grant",
        "per_call_granularity": "no (per permission)",
        "argument_aware": "no",
        "public_dataset": "yes",
    },
    "Description→Score": {
        "scores": "CVSS severity from CVE text",
        "timing": "static, once per vuln",
        "output": "CVSS base metrics",
        "ground_truth": "MITRE CVSS labels",
        "threat_direction": "n/a (software)",
        "per_call_granularity": "no (per vuln)",
        "argument_aware": "no",
        "public_dataset": "yes",
    },
}

# The cell only McpRisk occupies, stated plainly.
GAP = ("No prior work scores **graduated, per-(tool, asset) MCP invocation risk** in "
       "**both** a design-time and a request-time mode under the **server-as-victim** "
       "threat model and validates it on **external attack benchmarks**. Capability "
       "scorers (CVSS, AIVSS, permission-risk, Description→Score) are per-vulnerability "
       "and argument-blind; agent-safety detectors (R-Judge, AgenTRIM, AURA) are binary "
       "or allow/deny and mostly evaluated by task success, not graduated risk.")

AXIS_LABEL = {
    "scores": "Scores", "timing": "Timing", "output": "Output",
    "ground_truth": "Ground truth", "threat_direction": "Threat direction",
    "per_call_granularity": "Per-call", "argument_aware": "Arg-aware",
    "public_dataset": "Public data",
}


def render_md() -> str:
    cols = ["scores", "timing", "output", "ground_truth", "threat_direction",
            "per_call_granularity", "argument_aware"]
    head = "| Framework | " + " | ".join(AXIS_LABEL[c] for c in cols) + " |"
    sep = "| --- |" + " --- |" * len(cols)
    lines = ["# Positioning matrix: McpRisk vs. neighbouring risk-scoring works", "",
             "Distilled from the cited papers. Axes chosen to separate a per-invocation, "
             "server-side, graduated MCP risk scorer from neighbouring approaches.", "",
             head, sep]
    for name, row in MATRIX.items():
        bold = "**" if name.startswith("McpRisk") else ""
        lines.append(f"| {bold}{name}{bold} | "
                     + " | ".join(row[c] for c in cols) + " |")
    lines += ["", "## The unoccupied cell", "", GAP, ""]
    return "\n".join(lines)


def main() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(), encoding="utf-8")
    OUT_JSON.write_text(json.dumps({"axes": AXES, "matrix": MATRIX, "gap": GAP}, indent=2),
                        encoding="utf-8")
    print(render_md())
    print(f"\nWrote {OUT_MD.relative_to(REPO_ROOT)} and {OUT_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
