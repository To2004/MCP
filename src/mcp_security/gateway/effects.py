"""Typed effect fields: the few inputs the static scan keeps, logged as fields of their own.

The static scan's input importance (``<server>.importance.json``) labels each important
input of each tool with its effect: ``which`` (names the asset), ``how_much`` (an amount),
``who`` (recipients), ``when`` (a time), ``action`` (the operation's mode) or ``carried``
(content). The gateway reads a call's arguments through those labels only, so nothing here
is specific to one server. What it logs:

- ``which``: each asset-naming value, as given — the static layer prices assets by name;
- ``how_much``: each amount, as a number (a list counts as its length);
- ``who_count`` and ``who``: how many recipients, and their pseudonyms, never the values;
- ``when_span_days``: the span between the call's dates, or from the call to its one date;
- ``action``: each mode value;
- ``carried_bytes``: the size of the content, never the content.

With these, a log written without message bodies still feeds the dimensions the dynamic
layer selected (``reports/experiments/dynamic_dimensions/REPORT.md``, section 7).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from mcp_security.gateway.pseudonym import Pseudonymizer

WHICH, HOW_MUCH, WHO, WHEN, ACTION, CARRIED = (
    "which",
    "how_much",
    "who",
    "when",
    "action",
    "carried",
)
EFFECTS = (WHICH, HOW_MUCH, WHO, WHEN, ACTION, CARRIED)
MAX_VALUE_CHARS = 200  # a which/action value longer than this is cut, not dropped
MAX_RECIPIENTS = 100  # pseudonyms kept per call; who_count still counts them all
SECONDS_PER_DAY = 86_400
DIGEST_CHARS = 12
DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}")
DATE_KEYS = ("dateTime", "date")  # a calendar-style {"dateTime": ...} value


def top_level(path: str) -> str:
    """The argument an importance path starts at: ``reviewers[]`` or ``a.b`` -> its key."""
    return path.split("[")[0].split(".")[0]


@dataclass(frozen=True)
class EffectMap:
    """Tool -> top-level argument -> effect, from one importance file."""

    tools: dict[str, dict[str, str]]
    digest: str  # sha256 prefix of the file, so a log line can be traced to it

    @classmethod
    def load(cls, path: Path) -> EffectMap:
        """Read an importance file; only important inputs with a known effect are kept."""
        raw = path.read_bytes()
        tools: dict[str, dict[str, str]] = {}
        for tool in json.loads(raw)["tools"]:
            labels = tools.setdefault(tool["tool_name"], {})
            for argument in tool.get("arguments", []):
                effect = argument.get("effect")
                if argument.get("important") and effect in EFFECTS:
                    labels.setdefault(top_level(argument["path"]), effect)
        return cls(tools=tools, digest=hashlib.sha256(raw).hexdigest()[:DIGEST_CHARS])

    def extract(self, tool: str | None, args: object, ts: float, pseudonyms: Pseudonymizer) -> dict:
        """The typed fields of one call; empty when the tool has no labelled input in it."""
        labels = self.tools.get(tool or "")
        if not labels or not isinstance(args, dict):
            return {}
        out: dict = {}
        recipients: list[str] = []
        dates: list[float] = []
        carried = 0
        for key, effect in labels.items():
            value = args.get(key)
            if value is None:
                continue
            if effect in (WHICH, ACTION):
                out.setdefault(effect, {})[key] = _text(value)
            elif effect == HOW_MUCH and (amount := _amount(value)) is not None:
                out.setdefault(HOW_MUCH, {})[key] = amount
            elif effect == WHO:
                recipients += _recipients(value)
            elif effect == WHEN:
                dates += _dates(value)
            elif effect == CARRIED:
                carried += _size(value)
        if recipients:
            out["who_count"] = len(recipients)
            out[WHO] = [pseudonyms.of(r) for r in recipients[:MAX_RECIPIENTS]]
        if dates:
            span = max(dates) - min(dates) if len(dates) > 1 else abs(dates[0] - ts)
            out["when_span_days"] = round(span / SECONDS_PER_DAY, 3)
        if carried:
            out["carried_bytes"] = carried
        return out


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _text(value: object) -> str:
    return (value if isinstance(value, str) else _canonical(value))[:MAX_VALUE_CHARS]


def _amount(value: object) -> float | int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, (list, tuple)):
        return len(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return None


def _recipients(value: object) -> list[str]:
    if isinstance(value, bool):
        return []
    if isinstance(value, list):
        return [_text(item) for item in value if item is not None]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [_text(value)]


def _dates(value: object) -> list[float]:
    if isinstance(value, dict):
        value = next((value[k] for k in DATE_KEYS if isinstance(value.get(k), str)), None)
    if not isinstance(value, str) or not DATE_PREFIX.match(value):
        return []
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return []
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return [moment.timestamp()]


def _size(value: object) -> int:
    return len((value if isinstance(value, str) else _canonical(value)).encode())
