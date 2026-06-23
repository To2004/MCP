"""Map the captured proxy sessions to their static tables and score them all.

Each simulation session ran an agent against one demo MCP server, so every
session's ``calls.csv`` is scored against that server's design-time table. The
result is one ranked corpus of normal/benign-and-misconfiguration calls,
ordered from highest to lowest risk.
"""

from __future__ import annotations

import csv
import logging
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .loader import load_calls
from .score import ScoredCall, score_call
from .tables import BAND_ORDER, StaticTable, load_tables

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
PROXY_LOGS = REPO_ROOT / "logs" / "proxy"
DEFAULT_OUTPUT = REPO_ROOT / "reports" / "ranked_calls.csv"

# Each source ``calls.csv`` (relative to logs/proxy/) and the static table it is
# scored against. The first entry is the consolidated filesystem capture that
# carries the VALID/BAD_TOOL/BAD_PARAMS/EDGE categories.
SOURCES: tuple[tuple[str, str], ...] = (
    ("parsed/calls.csv", "corp_filesystem"),
    ("sessions/medical_clinic_sim/calls.csv", "medical_clinic_fs"),
    ("sessions/law_firm_sim/calls.csv", "law_firm_fs"),
    ("sessions/media_studio_sim/calls.csv", "media_studio_fs"),
    ("sessions/cbg_sqlite_sim/calls.csv", "cbg_sqlite"),
)

_CSV_FIELDS = (
    "rank",
    "score",
    "band",
    "server",
    "tool",
    "asset",
    "sensitivity",
    "tool_impact",
    "category",
    "scorable",
    "reason",
    "source",
    "index",
    "args_raw",
)


def score_corpus(
    sources: tuple[tuple[str, str], ...] = SOURCES,
    tables: dict[str, StaticTable] | None = None,
    proxy_logs: Path = PROXY_LOGS,
) -> list[ScoredCall]:
    """Score every configured session and return the calls ranked by risk."""
    tables = tables or load_tables()
    scored: list[ScoredCall] = []
    for rel_path, table_name in sources:
        path = proxy_logs / rel_path
        if not path.exists():
            logger.warning("source not found, skipping: %s", path)
            continue
        table = tables.get(table_name)
        if table is None:
            logger.warning("table %r not found, skipping %s", table_name, rel_path)
            continue
        for call in load_calls(path, source=rel_path):
            scored.append(score_call(call, table))
    scored.sort(key=lambda s: (s.score if s.score is not None else -1.0), reverse=True)
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
            row.pop("args_raw", None)
            row["args_raw"] = call.args_raw.replace("\n", " ")[:300]
            writer.writerow({field: row.get(field, "") for field in _CSV_FIELDS})
    return output


def summarize(scored: list[ScoredCall]) -> str:
    """Build a short human-readable summary of the ranked corpus."""
    bands = Counter(s.band for s in scored)
    by_server = Counter(s.server for s in scored)
    unscorable = [s for s in scored if not s.scorable]
    ordered_bands = sorted(bands, key=lambda b: BAND_ORDER.get(b, -1), reverse=True)

    lines = [f"Scored {len(scored)} calls across {len(by_server)} servers.", ""]
    lines.append("By band:")
    lines += [f"  {band:>8}: {bands[band]}" for band in ordered_bands]
    lines.append("")
    lines.append("By server:")
    lines += [f"  {server}: {count}" for server, count in by_server.most_common()]
    lines.append("")
    lines.append(f"Unscorable (invalid/unknown tool): {len(unscorable)}")
    lines.append("")
    lines.append("Top 10 riskiest calls:")
    for rank, call in enumerate(scored[:10], start=1):
        score = "n/a" if call.score is None else f"{call.score:g}"
        asset = call.asset or "-"
        lines.append(
            f"  {rank:>2}. [{call.band:>8} {score:>4}] {call.server}/{call.tool}"
            f" -> {asset}  ({call.category})"
        )
    return "\n".join(lines)
