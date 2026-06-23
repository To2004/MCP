"""Load captured tool calls from the proxy simulation logs into a common shape.

Two CSV schemas exist under ``logs/proxy/``:

* the consolidated ``parsed/calls.csv`` — columns ``tool``, ``args_json``,
  ``category`` in ``{VALID, BAD_TOOL, BAD_PARAMS, EDGE}``;
* the raw per-session ``calls.csv`` — columns ``tool``, ``args``, ``category``
  in ``{BENIGN, DISCOVERY, ...}`` plus ``persona``/``intent``.

Both are normalised into :class:`Call`. Captured responses can contain embedded
NUL bytes, so the reader strips them before CSV parsing.
"""

from __future__ import annotations

import csv
import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Call:
    """One captured tool call, normalised across both CSV schemas."""

    source: str
    index: str
    tool: str
    args: dict = field(default_factory=dict)
    category: str = ""
    status: str = ""
    persona: str = ""
    args_raw: str = ""


def _clean(path: Path) -> Iterator[str]:
    """Yield the file's lines with NUL bytes removed (captured responses have them)."""
    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        for line in handle:
            yield line.replace("\x00", "")


def _parse_args(raw: str) -> dict:
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def load_calls(path: Path, source: str | None = None) -> list[Call]:
    """Read one ``calls.csv`` (either schema) into a list of :class:`Call`."""
    label = source or path.parent.name
    rows = csv.DictReader(_clean(path))
    calls: list[Call] = []
    for row in rows:
        tool = (row.get("tool") or "").strip()
        if not tool:
            continue
        raw_args = row.get("args_json") if "args_json" in row else row.get("args")
        calls.append(
            Call(
                source=label,
                index=(row.get("index") or "").strip(),
                tool=tool,
                args=_parse_args(raw_args or ""),
                category=(row.get("category") or "").strip(),
                status=(row.get("status") or "").strip(),
                persona=(row.get("persona") or "").strip(),
                args_raw=(raw_args or "").strip(),
            )
        )
    logger.info("loaded %d calls from %s", len(calls), path)
    return calls
