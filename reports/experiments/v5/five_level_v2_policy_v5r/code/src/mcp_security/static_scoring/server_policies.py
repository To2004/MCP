"""Readers for the organization's POLICY document (``docs/mcp-tools/server-policies.md``).

The realistic-disclosure counterpart to :mod:`.server_profiles`. A profile hands
the scanner a per-asset ``Sens.`` number; a policy deliberately does not. What it
hands over instead is:

* a **data-classification table** — class · adverse-impact definition · examples,
  with no numbers anywhere;
* an **asset register** — ``| Asset | Description | Tools | Flags | CIA |`` — the
  facts the org can share (what exists, what touches it, which structural
  properties it has, where the loss axis lies);
* **recognition rules** with a fail-closed default class.

The scanner classifies each register row against the table and maps the class's
adverse-impact language onto its own 1-5 rubric, so the sensitivity primitive is
*derived* rather than supplied. See ``docs/standards/mcp-policy-spec.md``.

The ``Flags`` column is the one structural judgement a policy still carries:
``hub`` / ``population`` / ``self-sufficient`` are the escape routes the v4/v5
blast rubric requires an organization to sanction before a tier-5 award, and the
blast roof exempts flagged assets from its read cap. A flag states what an asset
IS (other systems authenticate against it; it holds a whole population), not how
much it is worth — so it stays policy-grade.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .server_profiles import PROFILE_FLAGS, ProfileAssetTableError, ServerProfile, profile_for

REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_DOC = REPO_ROOT / "docs" / "mcp-tools" / "server-policies.md"

# The register's header: "| Asset | Description | Tools | Flags | CIA |". The
# second column is Description, never Sens. — that is what stops the profile
# parser from mistaking a policy for an inventory.
_REGISTER_HEADER_RE = re.compile(r"^\|\s*Asset\s*\|\s*Description\s*\|", re.IGNORECASE)
_SEPARATOR_ROW_RE = re.compile(r"^\|[\s:|-]+\|?\s*$")
# A backticked identifier inside a Tools or Flags cell.
_TICKED_RE = re.compile(r"`([^`]+)`")
# Cells an author leaves empty: an em dash, a hyphen, "none", or nothing.
_EMPTY_CELL_RE = re.compile(r"^\s*(?:[-—–]|none|n/?a)?\s*$", re.IGNORECASE)

# The structural flags a register row may carry. Same vocabulary as the profile
# spec's judgement flags, so downstream code (blast roof, tier-5 escapes) reads
# one set of names whichever document supplied them.
POLICY_FLAGS = PROFILE_FLAGS


class PolicyRegisterError(ValueError):
    """Raised when a policy section's asset register is missing or malformed.

    The register is a scoring input — it supplies the asset inventory and the
    tool×asset homing — so a silent parse is not an option.
    """


class PolicyNumbersError(ValueError):
    """Raised when a policy section carries a sensitivity number after all.

    A policy that states its own 1-5 is no longer measuring what the experiment
    measures (can the scanner *derive* sensitivity?), so the scan refuses it.
    """


@dataclass(frozen=True)
class PolicyAssetRow:
    """One parsed row of a policy section's asset register."""

    asset_id: str
    description: str
    tools: tuple[str, ...]
    flags: tuple[str, ...]
    cia: str


def _split_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _ticked(cell: str) -> tuple[str, ...]:
    """Backticked identifiers in a cell, in order; ``()`` for an empty cell."""
    if _EMPTY_CELL_RE.match(cell):
        return ()
    found = _TICKED_RE.findall(cell)
    if found:
        return tuple(item.strip() for item in found)
    # Tolerate an un-ticked comma list so a hand-edited row still parses.
    return tuple(item.strip() for item in cell.split(",") if item.strip())


def parse_asset_register(text: str) -> list[PolicyAssetRow]:
    """Parse a policy section's ``| Asset | Description | Tools | Flags | CIA |`` table.

    Column positions come from the header row, so a register with or without the
    optional ``Flags`` and ``CIA`` columns parses. Raises
    :class:`PolicyRegisterError` when the section has no register, a row is
    short, or an asset id repeats.
    """
    rows: list[PolicyAssetRow] = []
    seen: set[str] = set()
    columns: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if _REGISTER_HEADER_RE.match(stripped):
            columns = [cell.strip().strip("*").rstrip(".").lower() for cell in _split_cells(line)]
            continue
        if not columns:
            continue
        if not stripped.startswith("|"):
            columns = []  # register ended; a later one may start again
            continue
        if _SEPARATOR_ROW_RE.match(stripped):
            continue
        cells = _split_cells(line)
        if len(cells) < len(columns):
            raise PolicyRegisterError(
                f"register row has {len(cells)} cells, header has {len(columns)}: {stripped!r}"
            )
        by_col = dict(zip(columns, cells))
        asset = by_col.get("asset", "").strip().strip("`").strip()
        if not asset:
            raise PolicyRegisterError(f"register row has no asset id: {stripped!r}")
        if asset in seen:
            raise PolicyRegisterError(f"duplicate register row {asset!r}")
        seen.add(asset)
        flags = tuple(flag for flag in _ticked(by_col.get("flags", "")) if flag in POLICY_FLAGS)
        unknown = [
            flag
            for flag in _ticked(by_col.get("flags", ""))
            if flag not in POLICY_FLAGS and not _EMPTY_CELL_RE.match(flag)
        ]
        if unknown:
            raise PolicyRegisterError(
                f"asset {asset!r}: unknown flag(s) {unknown}; choose from {list(POLICY_FLAGS)}"
            )
        rows.append(
            PolicyAssetRow(
                asset_id=asset,
                description=by_col.get("description", "").strip(),
                tools=_ticked(by_col.get("tools", "")),
                flags=flags,
                cia=by_col.get("cia", "").strip(),
            )
        )
    if not rows:
        raise PolicyRegisterError(
            "policy section has no '| Asset | Description | Tools | ... |' register — "
            "policy-sensitivity modes build their asset inventory from it (spec P1+)"
        )
    return rows


def assert_no_sensitivity_numbers(text: str, *, server: str) -> None:
    """Refuse a policy section that leaked a per-asset sensitivity number.

    The whole point of the policy arm is that the org supplies consequences and
    the scanner supplies the scale, so an ``| Asset | Sens. |`` table here would
    silently turn the experiment back into the inventory-grade one.
    """
    for line in text.splitlines():
        if re.match(r"^\|\s*Asset\s*\|\s*Sens\.?\s*\|", line.strip(), re.IGNORECASE):
            raise PolicyNumbersError(
                f"{server}: policy section contains an '| Asset | Sens. |' table. A policy "
                "states adverse impact, never a 1-5 — move that table to "
                "docs/mcp-tools/server-profiles.md."
            )


def policy_for(server: str, *, doc: Path | None = None) -> ServerProfile:
    """The policy section for ``server``, validated to carry no sensitivity numbers."""
    policy = profile_for(server, doc=doc or POLICY_DOC)
    assert_no_sensitivity_numbers(policy.text, server=server)
    return policy


def unmapped_tools(rows: list[PolicyAssetRow], tool_names) -> list[str]:
    """Advertised tools that appear in no register row's Tools cell (sorted).

    Spec conformance P2 requires total coverage; the driver reports the gap
    rather than failing, because a tool that genuinely touches no organizational
    asset (a clock, a colour palette) is a legitimate answer the section states
    in prose.
    """
    mapped = {tool for row in rows for tool in row.tools}
    return sorted(set(tool_names) - mapped)


def unknown_register_tools(rows: list[PolicyAssetRow], tool_names) -> list[str]:
    """Tools named in the register that the server does not actually advertise."""
    advertised = set(tool_names)
    return sorted({tool for row in rows for tool in row.tools} - advertised)


__all__ = [
    "POLICY_DOC",
    "POLICY_FLAGS",
    "PolicyAssetRow",
    "PolicyNumbersError",
    "PolicyRegisterError",
    "ProfileAssetTableError",
    "assert_no_sensitivity_numbers",
    "parse_asset_register",
    "policy_for",
    "unknown_register_tools",
    "unmapped_tools",
]
