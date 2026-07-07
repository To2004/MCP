"""Rank captured calls against the scanner's freshly derived risk matrices.

Each simulation session drove an agent against one demo MCP server, so every
session's ``calls.csv`` is scored against that server's **scan artifact**
(``reports/scan/<server>.json``) — the matrix the scanner derived from the tools
and assets, before the server ran. The result is one corpus of calls ranked from
highest to lowest risk.

The primary corpus is the filesystem simulation
(``logs/proxy/sessions/filesystem_sim/calls.csv``); other sessions are scored too
when their scan artifact is present. Nothing here reads the design-time ground
truth under ``reports/samples`` / ``reports/evaluation``.
"""

from __future__ import annotations

import csv
import logging
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .loader import load_calls
from .score import ScoredCall, score_call
from .tables import (
    STATUS_INVALID,
    STATUS_UNRESOLVED,
    StaticTable,
    load_param_rubrics,
    load_scans,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
PROXY_LOGS = REPO_ROOT / "logs" / "proxy"
DEFAULT_OUTPUT = REPO_ROOT / "reports" / "ranked_calls.csv"
DEFAULT_OUTPUT_MD = REPO_ROOT / "reports" / "ranked_calls.md"

# Each source ``calls.csv`` (relative to logs/proxy/) and the scan-artifact stem
# (``reports/scan/<stem>.json``) it is scored against. The filesystem simulation
# is the primary corpus; the rest are scored when their scan exists.
SOURCES: tuple[tuple[str, str], ...] = (
    ("sessions/filesystem_sim/calls.csv", "fs_corp_filesystem"),
    ("parsed/calls.csv", "fs_corp_filesystem"),
    ("sessions/medical_clinic_sim/calls.csv", "fs_medical_clinic_fs"),
    ("sessions/law_firm_sim/calls.csv", "fs_law_firm_fs"),
    ("sessions/media_studio_sim/calls.csv", "fs_media_studio_fs"),
    ("sessions/cbg_sqlite_sim/calls.csv", "sqlite_cbg_sqlite"),
    # Additional simulations across the big MCPs (scripts/make_simulations.py),
    # calendar weighted heaviest. Each is scored once its scan artifact exists.
    ("sessions/calendar_sim/calls.csv", "calendar_cbg"),
    ("sessions/github_sim/calls.csv", "github_cbg"),
    ("sessions/slack_sim/calls.csv", "slack_cbg"),
    ("sessions/fintech_sim/calls.csv", "fs_fintech_fs"),
    ("sessions/devops_sqlite_sim/calls.csv", "sqlite_devops_sqlite"),
)

_CSV_FIELDS = (
    "rank",
    "final_score",
    "score",
    "param_multiplier",
    "final_band",
    "band",
    "param_band",
    "param_top",
    "server",
    "tool",
    "asset",
    "sensitivity",
    "tool_impact",
    "persona",
    "category",
    "scorable",
    "reason",
    "source",
    "run_id",
    "index",
    "args_raw",
)


def _rank_key(call: ScoredCall) -> tuple[int, float, float]:
    """Sort key: scored calls first, then by the NUMBER (final_score).

    ``final_score`` = cell score amplified by parameter risk, so a bulk/large-
    magnitude call outranks an equal-cell call with a small parameter — by number,
    not by band. The raw cell ``score`` breaks ties. Bands never enter ranking.
    """
    scored = 1 if call.final_score is not None else 0
    return (scored, call.final_score or 0.0, call.score or 0.0)


def score_corpus(
    sources: tuple[tuple[str, str], ...] = SOURCES,
    scans: dict[str, StaticTable] | None = None,
    proxy_logs: Path = PROXY_LOGS,
    rubrics: dict[str, dict] | None = None,
) -> list[ScoredCall]:
    """Score every configured session against its scan and return calls by risk.

    ``rubrics`` maps a scan name to ``{tool_name: ToolRubric}``; when present, the
    parameter dimension amplifies each resolved call's score into ``final_score``
    (the value used for ranking). Calls come back ordered by ``final_score``.
    """
    scans = load_scans() if scans is None else scans
    rubrics = load_param_rubrics() if rubrics is None else rubrics
    if not scans:
        logger.warning("no scans available — nothing to score")
        return []
    scored: list[ScoredCall] = []
    for rel_path, scan_name in sources:
        path = proxy_logs / rel_path
        if not path.exists():
            logger.warning("source not found, skipping: %s", path)
            continue
        table = scans.get(scan_name)
        if table is None:
            logger.warning("scan %r not found, skipping %s", scan_name, rel_path)
            continue
        tool_rubrics = rubrics.get(scan_name, {})
        for call in load_calls(path, source=rel_path):
            scored.append(score_call(call, table, tool_rubrics.get(call.tool)))
    scored.sort(key=_rank_key, reverse=True)
    return scored


def write_ranked_csv(scored: list[ScoredCall], output: Path = DEFAULT_OUTPUT) -> Path:
    """Write the ranked calls to ``output`` and return its path."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for rank, call in enumerate(scored, start=1):
            row = asdict(call)
            row["rank"] = rank
            row["args_raw"] = call.args_raw.replace("\n", " ")[:300]
            writer.writerow({field: row.get(field, "") for field in _CSV_FIELDS})
    return output


def write_ranked_markdown(scored: list[ScoredCall], output: Path = DEFAULT_OUTPUT_MD) -> Path:
    """Write the ranked calls as a markdown report (summary + ranked table)."""
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Ranked MCP calls", "", "Each captured call scored against the scanner's "
             "risk matrix for its server (no design-time table read). Ranking is by "
             "**final_score** — the cell score amplified by the call's input-parameter "
             "risk (`score x param_multiplier`). Bands are shown for visualization only.",
             "", summarize(scored), "", "## Ranking", "",
             "| Rank | Final score | Cell score | Param x | Final band | Cell band | Param | "
             "Param risk | Server | Tool | Asset | Persona | Category | Reason |",
             "| ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | "
             "--- | --- |"]
    for rank, call in enumerate(scored, start=1):
        asset = call.asset or "—"
        fscore = "—" if call.final_score is None else f"{call.final_score:g}"
        cscore = "—" if call.score is None else f"{call.score:g}"
        lines.append(
            f"| {rank} | {fscore} | {cscore} | {call.param_multiplier:g}x | "
            f"{call.final_band} | {call.band} | {call.param_top or '—'} | "
            f"{call.param_band or '—'} | {call.server} | `{call.tool}` | `{asset}` | "
            f"{call.persona or '—'} | {call.category or '—'} | {call.reason} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def summarize(scored: list[ScoredCall]) -> str:
    """Build a short, honest summary: coverage first, then the scored ranking."""
    total = len(scored)
    by_server = Counter(s.server for s in scored)
    bands = Counter(s.band for s in scored)
    risk_bands = [b for b in ("critical", "high", "medium", "low") if bands[b]]
    resolved = sum(bands[b] for b in risk_bands)

    lines = [f"{total} calls across {len(by_server)} server(s).", ""]
    lines.append(f"Resolved to a scanned cell: {resolved}/{total}")
    lines += [f"  {band:>8}: {bands[band]}" for band in risk_bands]
    lines.append(f"  {STATUS_UNRESOLVED}: {bands.get(STATUS_UNRESOLVED, 0)} "
                 "(directory/enumeration ops, no-arg calls, or assets not in the scan)")
    lines.append(f"  {STATUS_INVALID}: {bands.get(STATUS_INVALID, 0)} (unknown tools)")
    escalated = sum(1 for s in scored if s.scorable and s.param_multiplier > 1.0)
    lines.append("")
    lines.append(f"Parameter risk amplified the score on {escalated} resolved call(s).")
    lines.append("")
    lines.append("Top 10 riskiest resolved calls (by final score):")
    ranked = [s for s in scored if s.scorable][:10]
    for rank, call in enumerate(ranked, start=1):
        mark = (f" (cell {call.score:g} x{call.param_multiplier:g} via {call.param_top})"
                if call.param_multiplier > 1.0 else "")
        lines.append(
            f"  {rank:>2}. [{call.final_score:g}] {call.server}/{call.tool}"
            f" -> {call.asset}  ({call.category or call.persona}){mark}  [{call.final_band}]"
        )
    return "\n".join(lines)
