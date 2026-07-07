"""Independent methodology judge — audits the pipeline for scientific soundness.

The judge checks one claim at a time. Each claim names the source files that are
its evidence; the LLM is shown only those, asked to decide independently, and must
return a structured verdict (pass / concern / fail) with the specific evidence it
relied on. This keeps every judgement inside the local model's context and makes
the audit reproducible and inspectable, rather than a single opaque "looks fine".

The judge is deliberately skeptical: its job is to find data leakage, hardcoded
scores, mistakes, and threats to validity — not to bless the work.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama

from .evidence import bundle
from .verify import RANKED_CSV, SCAN_DIR, run_verification, to_markdown as verify_to_markdown

JUDGE_SYSTEM = """You are an independent, skeptical scientific reviewer auditing a
security research pipeline. The pipeline statically scans an MCP server's tools
(from an Excel catalog) and assets (from disk), then uses a local LLM to derive
risk scores, and finally ranks captured tool calls by those scores. A separate set
of design-time "ground truth" tables is meant to be used ONLY to grade the scanner,
never as an input to it.

You verify ONE claim about this pipeline. You are shown the relevant source files
as evidence. Decide INDEPENDENTLY whether the claim holds, citing the specific code
that justifies your verdict. Be concrete; quote identifiers/paths. Do not assume
good faith — look for the failure mode the claim is guarding against.

Output ONLY valid JSON, no prose, no fences:
{"verdict": "pass" | "concern" | "fail",
 "severity": "none" | "low" | "medium" | "high",
 "evidence": "specific code/paths you relied on",
 "reasoning": "why the claim does or does not hold",
 "recommendation": "what to change, or empty if pass"}"""

JUDGE_USER = """CLAIM TO VERIFY:
{claim}

WHAT WOULD VIOLATE IT:
{violation}

EVIDENCE (source files):
{evidence}

Return the verdict JSON."""


@dataclass(frozen=True)
class Claim:
    """One auditable property of the pipeline and the files that evidence it."""

    key: str
    claim: str
    violation: str
    files: tuple[str, ...]


# The scientific properties the design depends on. Each is checked in isolation.
CLAIMS: tuple[Claim, ...] = (
    Claim(
        "no_data_leakage",
        "The scanner never reads the design-time ground-truth tables "
        "(reports/samples/* or reports/evaluation/*); they only grade it.",
        "Any code path where the scanner/understanding stage opens, imports, or "
        "otherwise consumes the committed tables would be leakage.",
        ("src/mcp_security/scanner/scan.py",
         "src/mcp_security/scanner/tool_list.py",
         "src/mcp_security/static_scoring/pipeline.py"),
    ),
    Claim(
        "tools_from_server_tools_list",
        "The scanner's tools come from the server's own saved tools/list "
        "(reports/tool_lists/<kind>.json), not a hand-authored catalog, and carry "
        "no pre-assigned risk label.",
        "Inventing a tool set in the scanner, or reading a human risk tier as the "
        "tool's score, would mean the tools are not the server's own advertised set.",
        ("src/mcp_security/scanner/tool_list.py",),
    ),
    Claim(
        "llm_only_no_fabrication",
        "The scanner runs the scorer in strict mode (scan_server calls "
        "build_static_table with strict=use_llm), and in strict mode every "
        "primitive — domain, tool_impact, sensitivity, blast_radius, band, "
        "baseline — routes a missing model answer through _strict_fail, which "
        "raises LLMUnavailableError instead of substituting a heuristic.",
        "A fallback/default/heuristic score used when strict=True, or a strict "
        "primitive that does not call _strict_fail on a missing model answer.",
        ("src/mcp_security/static_scoring/pipeline.py",
         "src/mcp_security/scanner/scan.py"),
    ),
    Claim(
        "scoring_uses_scan_not_tables",
        "The call ranker scores observed calls against the scanner's fresh scan "
        "artifacts (reports/scan/), not the committed tables.",
        "load_* pointing the ranker at reports/samples or reports/evaluation.",
        ("src/mcp_security/call_scoring/tables.py",
         "src/mcp_security/call_scoring/corpus.py"),
    ),
    Claim(
        "no_unjustified_hardcoded_scores",
        "Risk MAGNITUDES (tool_impact, asset_sensitivity, blast_radius) are "
        "LLM-derived; in strict mode (the scanner's mode) each _strict_fails rather "
        "than falling back to a heuristic. Bands are a deterministic, documented "
        "function of those primitives (band_label, with published security floors) "
        "and the score formula (sensitivity*blast*impact) — reproducible by design, "
        "not a fabricated per-cell number.",
        "A hardcoded MAGNITUDE (sensitivity/impact/blast) used as the result of a "
        "strict scan — e.g. a fallback primitive reached when strict=True, or a "
        "fixed per-asset/per-tool risk magnitude injected into the scoring path.",
        ("src/mcp_security/static_scoring/pipeline.py",),
    ),
    Claim(
        "deterministic_scoring",
        "Scoring is reproducible: the model is queried greedily with a fixed seed.",
        "Sampling temperature > 0 or no fixed seed, making scores vary run to run.",
        ("src/mcp_security/llm/ollama_client.py",),
    ),
    Claim(
        "honest_unresolved_handling",
        "Calls that do not resolve to a scanned cell are reported as unresolved/"
        "invalid statuses, never given a fabricated score or band.",
        "A default score/band assigned to a call whose asset or tool is unknown.",
        ("src/mcp_security/call_scoring/score.py",
         "src/mcp_security/call_scoring/resolve.py"),
    ),
)


def _judge_one(claim: Claim) -> dict:
    """Ask the LLM to independently verify one claim; return a verdict dict."""
    prompt = JUDGE_SYSTEM + "\n\n" + JUDGE_USER.format(
        claim=claim.claim,
        violation=claim.violation,
        evidence=bundle(list(claim.files)),
    )
    result = query_ollama(prompt)
    if not isinstance(result, dict) or "verdict" not in result:
        return {
            "verdict": "error",
            "severity": "unknown",
            "evidence": "",
            "reasoning": "model gave no usable verdict (is Ollama running?)",
            "recommendation": "re-run the judge with the local LLM available",
        }
    return result


def run_audit(claims: tuple[Claim, ...] = CLAIMS) -> list[dict]:
    """Run every claim through the judge; return a verdict record per claim."""
    records: list[dict] = []
    for claim in claims:
        verdict = _judge_one(claim)
        records.append({"key": claim.key, "claim": claim.claim, **verdict})
    return records


RESULT_SYSTEM = """You are a skeptical scientific reviewer giving a single graded
verdict on the RESULTS of an MCP risk-scoring pipeline (not its code). You are
given: (1) the deterministic self-consistency checks that already passed/failed,
(2) the scanner's agreement with an independent human heatmap oracle, (3) the band
distribution of each scan, and (4) the ranked captured-call corpus.

Judge whether the results are trustworthy and meaningful. Reward honest handling of
unresolved calls and meaningful parameter escalation; penalise distributions that
look degenerate (everything one band), agreement that is no better than chance, or
any deterministic check that failed.

Output ONLY valid JSON, no prose, no fences:
{"verdict": "pass" | "concern" | "fail",
 "result_quality": "strong" | "adequate" | "weak",
 "evidence": "the specific numbers you relied on",
 "reasoning": "why the results are or are not trustworthy",
 "top_improvements": [str]}"""

RESULT_USER = """RESULTS DIGEST:
{digest}

Return the verdict JSON."""


def _results_digest() -> str:
    """Compact digest of the measured outcomes for the results judge."""
    parts: list[str] = []
    checks = run_verification()
    parts.append(verify_to_markdown(checks))

    human = Path(__file__).resolve().parents[3] / "reports/evaluation/scanner_vs_human.md"
    if human.exists():
        parts.append(human.read_text("utf-8"))

    if SCAN_DIR.exists():
        lines = ["## Band distributions"]
        for path in sorted(SCAN_DIR.glob("*.json")):
            if path.stem.endswith("_params"):
                continue
            d = json.loads(path.read_text("utf-8"))
            lines.append(f"- {path.stem}: {d.get('band_distribution')} "
                         f"(model_reviewed={d.get('model_reviewed')})")
        parts.append("\n".join(lines))

    if RANKED_CSV.exists():
        rows = list(csv.DictReader(RANKED_CSV.open(encoding="utf-8")))
        scored = [r for r in rows if r["scorable"] == "True"]
        escalated = sum(1 for r in scored if r["param_band"] and r["final_band"] != r["band"])
        bands = Counter(r["final_band"] for r in scored)
        parts.append(f"## Ranked corpus\n- total={len(rows)} scored={len(scored)} "
                     f"param_escalated={escalated}\n- scored final bands={dict(bands)}")
    return "\n\n".join(parts)


def judge_results() -> dict:
    """Ask the LLM for one graded verdict on the trustworthiness of the results."""
    result = query_ollama(RESULT_SYSTEM + "\n\n" + RESULT_USER.format(digest=_results_digest()))
    if not isinstance(result, dict) or "verdict" not in result:
        return {"verdict": "error", "result_quality": "unknown", "evidence": "",
                "reasoning": "model gave no usable verdict (is Ollama running?)",
                "top_improvements": ["re-run the results judge with the local LLM available"]}
    return result


def results_to_markdown(verdict: dict) -> str:
    """Render the results-quality verdict as markdown."""
    lines = [
        f"# Results-quality verdict — {verdict.get('verdict', '?')} "
        f"(quality: {verdict.get('result_quality', '?')})",
        "",
        f"*Reasoning:* {verdict.get('reasoning', '')}",
        "",
        f"*Evidence:* {verdict.get('evidence', '')}",
        "",
        "## Top improvements",
    ]
    lines += [f"- {i}" for i in verdict.get("top_improvements", [])] or ["- (none)"]
    lines.append("")
    return "\n".join(lines)


_MARK = {"pass": "✅", "concern": "⚠️", "fail": "❌", "error": "❓"}


def to_markdown(records: list[dict]) -> str:
    """Render the audit verdicts as a markdown report."""
    counts: dict[str, int] = {}
    for r in records:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    lines = [
        "# Methodology audit (independent LLM judge)",
        "",
        "Each claim was verified in isolation by the local LLM, shown only the "
        "relevant source. Verdicts: ✅ pass · ⚠️ concern · ❌ fail · ❓ no answer.",
        "",
        "**Summary:** " + ", ".join(f"{_MARK.get(k, k)} {v}" for k, v in sorted(counts.items())),
        "",
    ]
    for r in records:
        lines += [
            f"## {_MARK.get(r['verdict'], '')} {r['key']} — {r['verdict']} "
            f"(severity: {r.get('severity', '?')})",
            "",
            f"*Claim:* {r['claim']}",
            "",
            f"*Reasoning:* {r.get('reasoning', '')}",
            "",
            f"*Evidence:* {r.get('evidence', '')}",
        ]
        if r.get("recommendation"):
            lines += ["", f"*Recommendation:* {r['recommendation']}"]
        lines.append("")
    return "\n".join(lines)
