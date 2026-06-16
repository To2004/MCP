"""Sensitivity taxonomies and risk-band helpers shared across the framework.

This is the single source of truth for the security team's fixed sensitivity
rankings. Both ``local_llm/rank_with_llm.py`` (the fixed-taxonomy NIST ranker)
and ``mcp_security.scanner`` (the live asset scanner) import from here.

Each per-kind anchor is *optional*: when an asset is not covered by an anchor,
the ranker falls back to the local LLM. Anchors only encode the
high-confidence, security-team-blessed mappings.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Risk bands — ordered integer scale used for max()/comparison and labelling
# ---------------------------------------------------------------------------
BAND: dict[str, int] = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
IBAND: dict[int, str] = {4: "Critical", 3: "High", 2: "Medium", 1: "Low"}

RISK_LEVELS: tuple[str, ...] = ("Critical", "High", "Medium", "Low")


def band_of(level: str, default: str = "Medium") -> int:
    """Return the integer band for a risk level, tolerant of casing/whitespace."""
    return BAND.get(level.strip().capitalize(), BAND[default])


# ---------------------------------------------------------------------------
# Directory sensitivity — filesystem store, by logical area (security team)
# ---------------------------------------------------------------------------
DIR_SENSITIVITY: dict[str, str] = {
    "Sensitive Docs": "Critical",
    "Security Evidence": "Critical",
    "Source Code": "High",
    "Eval Data": "Medium",
    "Shared Proj Dir": "Medium",
    "QA Test Plans": "Medium",
    "Onboarding": "Low",
    "Public": "Low",
}

# ---------------------------------------------------------------------------
# Filetype sensitivity — filesystem store, by extension (the CBG table).
# Keys are bare extensions without the leading dot.
# ---------------------------------------------------------------------------
FILETYPE_SENSITIVITY: dict[str, str] = {
    "sys": "Critical",
    "exe": "Critical",
    "bash": "High",
    "code": "High",
    "sql": "High",
    "xlsx": "High",
    "docx": "High",
    "pdf": "Medium",
    "csv": "Medium",
    "md": "Low",
    "png": "Low",
    "txt": "Low",
}

# ---------------------------------------------------------------------------
# Slack channel anchor — only the unambiguous cases; the rest is LLM-ranked.
# Tags are produced by the slack enumerator (e.g. "private", "dm").
# ---------------------------------------------------------------------------
SLACK_CHANNEL_ANCHOR: dict[str, str] = {
    "dm": "High",
    "private": "High",
    "public": "Low",
}

# ---------------------------------------------------------------------------
# DB column anchor — a table is at least this sensitive if it has such a column.
# Tags are produced by the sqlite enumerator as "column:<name>".
# ---------------------------------------------------------------------------
DB_COLUMN_ANCHOR: dict[str, str] = {
    "ssn": "Critical",
    "password": "Critical",
    "secret": "Critical",
    "token": "Critical",
    "credit_card": "Critical",
    "card_number": "Critical",
    "email": "High",
    "phone": "High",
    "address": "High",
    "salary": "High",
    "dob": "High",
}
