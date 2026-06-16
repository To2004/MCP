"""Rank an asset inventory into the ``Rank | Name | Risk Level | Reasoning`` table.

The scanner *finds* assets deterministically; this module *understands* them.
Understanding is generic — it works for any MCP server, including kinds never
seen before, because it reasons from the server's own self-description rather
than from a hardcoded per-kind table.

1. **Local LLM (understanding agent)** — every asset is rated and given a
   one-line reason by the local model. The prompt is kind-agnostic and includes
   the server's ``context`` (its tool/resource descriptions, captured at
   enumeration), so the model can judge what a novel server's assets expose.
2. **Anchors as a floor/fallback** — the security team's fixed sensitivity maps
   (``FILETYPE_SENSITIVITY``, the PII/channel anchors) act as deterministic
   hints the model sees, a raise-only floor it cannot silently undercut, and the
   offline rating when ``use_llm=False`` or Ollama is down (then unanchored
   assets get a templated reason and are flagged ``unranked``).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.sensitivity import (
    BAND,
    DB_COLUMN_ANCHOR,
    FILETYPE_SENSITIVITY,
    RISK_LEVELS,
    SLACK_CHANNEL_ANCHOR,
    band_of,
)

from .enumerator import AssetGroup, AssetInventory

logger = logging.getLogger(__name__)

# Optional per-kind anchor hints shown to the model. These are only hints now —
# an unknown kind simply gets none and is still understood from server context.
_KIND_ANCHOR_HINT: dict[str, dict[str, str]] = {
    "filesystem": FILETYPE_SENSITIVITY,
    "sqlite": DB_COLUMN_ANCHOR,
    "slack": SLACK_CHANNEL_ANCHOR,
}


def _filetype_anchor(asset: AssetGroup) -> str | None:
    """Map a bare extension name (``.sql``) to a band."""
    return FILETYPE_SENSITIVITY.get(asset.name.lstrip(".").lower())


def _slack_anchor(asset: AssetGroup) -> str | None:
    for tag in asset.tags:
        if tag in SLACK_CHANNEL_ANCHOR:
            return SLACK_CHANNEL_ANCHOR[tag]
    return None


def _sqlite_anchor(asset: AssetGroup) -> str | None:
    """A table is at least as sensitive as its most sensitive PII column."""
    best: str | None = None
    for tag in asset.tags:
        if tag.startswith("column:"):
            col = tag.split(":", 1)[1]
            for key, level in DB_COLUMN_ANCHOR.items():
                if key in col and (best is None or BAND[level] > BAND[best]):
                    best = level
    return best


# Kind-specific anchor resolvers. Adding a kind = adding one entry here.
ANCHOR_RESOLVERS: dict[str, Callable[[AssetGroup], str | None]] = {
    "filesystem": _filetype_anchor,
    "slack": _slack_anchor,
    "sqlite": _sqlite_anchor,
}


def _generic_extension_anchor(asset: AssetGroup) -> str | None:
    """Kind-agnostic fallback: any asset whose name/tags reveal a known filetype.

    Lets a resource called ``report.pdf`` (from *any* server) be anchored by the
    shared filetype taxonomy, without per-kind code.
    """
    suffix = Path(asset.name).suffix.lstrip(".").lower()
    if suffix and suffix in FILETYPE_SENSITIVITY:
        return FILETYPE_SENSITIVITY[suffix]
    for tag in asset.tags:
        if tag.startswith("ext:"):
            ext = tag.split(":", 1)[1]
            if ext in FILETYPE_SENSITIVITY:
                return FILETYPE_SENSITIVITY[ext]
    return None


class RankedAsset:
    """One ranked row. Plain class so it formats cleanly and stays comparable."""

    def __init__(
        self,
        name: str,
        risk_level: str,
        reasoning: str,
        count: int = 1,
        source: str = "enumerated",
        rank: int = 0,
    ) -> None:
        self.rank = rank
        self.name = name
        self.risk_level = risk_level
        self.reasoning = reasoning
        self.count = count
        self.source = source

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"RankedAsset(rank={self.rank}, name={self.name!r}, risk={self.risk_level!r})"


# ---------------------------------------------------------------------------
# Anchor resolution
# ---------------------------------------------------------------------------
def _anchor_for(inv_kind: str, asset: AssetGroup) -> str | None:
    """Return a band if any anchor applies: kind-specific first, then generic.

    Generic enough that a server kind with no registered resolver is still
    anchored whenever an asset name/tag reveals a known filetype; otherwise it
    falls through to the LLM.
    """
    resolver = ANCHOR_RESOLVERS.get(inv_kind)
    band = resolver(asset) if resolver else None
    if band is None:
        band = _generic_extension_anchor(asset)
    return band


# ---------------------------------------------------------------------------
# LLM ranking for the unanchored remainder
# ---------------------------------------------------------------------------
def _build_prompt(kind: str, assets: list[AssetGroup], context: str = "") -> str:
    """Kind-agnostic understanding prompt.

    Works for any server: the model judges each asset's data-exposure risk from
    its name/tags plus the server's own ``context`` (what its tools expose), so a
    kind with no hardcoded anchor is still understood rather than guessed.
    """
    anchor = _KIND_ANCHOR_HINT.get(kind, {})
    payload = [{"name": a.name, "tags": list(a.tags)} for a in assets]
    ctx_block = (
        f"What this MCP server exposes (from its own tool/resource descriptions):\n{context}\n"
        if context.strip()
        else ""
    )
    anchor_block = (
        f"Reference anchors (name -> band), use as hints: {json.dumps(anchor)}\n" if anchor else ""
    )
    return (
        "You assess data-exposure risk for assets an MCP server can read. The server "
        "is the protected asset; the agent making requests is the threat.\n"
        f"Server kind: {kind}.\n"
        f"{ctx_block}"
        f"Risk bands: {', '.join(RISK_LEVELS)}.\n"
        f"{anchor_block}"
        "For EVERY item below assign a risk_level (one of the bands) and a reasoning of at "
        "most 15 words, judging by how sensitive the data it exposes is. Reply with JSON "
        "only, no prose.\n"
        f"Items: {json.dumps(payload)}\n"
        'Return exactly: {"rows":[{"name":"<name>","risk_level":"<band>",'
        '"reasoning":"<text>"}]}'
    )


def _llm_rank(kind: str, assets: list[AssetGroup], context: str = "") -> dict[str, dict]:
    """Ask the local LLM to rank the given assets. Returns name -> {risk, reason}."""
    if not assets:
        return {}
    response = query_ollama(_build_prompt(kind, assets, context))
    if not response:
        return {}
    out: dict[str, dict] = {}
    for row in response.get("rows", []):
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        level = str(row.get("risk_level", "")).strip().capitalize()
        if name and level in BAND:
            out[name] = {"risk": level, "reason": str(row.get("reasoning", "")).strip()}
    return out


def _templated_reason(kind: str, asset: AssetGroup) -> str:
    if asset.tags:
        return f"unranked ({kind}); tags: {', '.join(asset.tags)}"
    return f"unranked ({kind} asset); no anchor, LLM unavailable"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def rank_inventory(inv: AssetInventory, use_llm: bool = True) -> list[RankedAsset]:
    """Rank every asset in the inventory, anchors first then the local LLM."""
    anchored: list[RankedAsset] = []
    remainder: list[AssetGroup] = []

    for asset in inv.assets:
        band = _anchor_for(inv.kind, asset)
        if band is not None:
            anchored.append(
                RankedAsset(
                    name=asset.name,
                    risk_level=band,
                    reasoning="",  # filled below (seeded from anchor)
                    count=asset.count,
                    source=inv.source,
                )
            )
        else:
            remainder.append(asset)

    llm_results = _llm_rank(inv.kind, remainder, inv.context) if use_llm else {}

    # Anchored rows: the LLM may RAISE the band (never silently downgrade) and
    # phrase the reasoning. Absent the LLM, keep the anchor band + a template.
    anchored_llm = (
        _llm_rank(
            inv.kind,
            [AssetGroup(name=a.name, count=a.count, tags=()) for a in anchored],
            inv.context,
        )
        if use_llm and anchored
        else {}
    )
    for row in anchored:
        hit = anchored_llm.get(row.name)
        if hit and BAND[hit["risk"]] > BAND[row.risk_level]:
            row.risk_level = hit["risk"]  # raise only
        row.reasoning = (
            (hit or {}).get("reason") or f"{row.risk_level} per sensitivity taxonomy"
        )

    ranked: list[RankedAsset] = list(anchored)
    for asset in remainder:
        hit = llm_results.get(asset.name)
        if hit:
            ranked.append(
                RankedAsset(
                    name=asset.name,
                    risk_level=hit["risk"],
                    reasoning=hit["reason"] or "ranked by local LLM",
                    count=asset.count,
                    source=inv.source,
                )
            )
        else:
            ranked.append(
                RankedAsset(
                    name=asset.name,
                    risk_level="Medium",
                    reasoning=_templated_reason(inv.kind, asset),
                    count=asset.count,
                    source="theorised" if inv.source != "enumerated" else inv.source,
                )
            )

    ranked.sort(key=lambda r: (-band_of(r.risk_level), -r.count, r.name))
    for i, row in enumerate(ranked, start=1):
        row.rank = i
    return ranked
