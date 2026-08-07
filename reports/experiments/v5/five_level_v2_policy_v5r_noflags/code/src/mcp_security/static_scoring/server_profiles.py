"""Hand-written organizational profiles for the scanned MCP servers.

The profiles live in ``docs/mcp-tools/server-profiles.md``: one ``### <name>``
section per server, each stating the owning company, the expected organizational
use of the server, the peak asset severity, and the CIA emphasis per asset. This
module is the single reader of that document — it parses the sections and hands
one server's profile text to the scoring pipeline as **org description**.

Why this exists: the stock scanner infers everything from the tool registry and
the asset ids alone (``inferred_profile``). The ``five_level_v2_desc`` experiment
instead gives the model the organization's own written description of the server
and drops the separately-scored asset-sensitivity primitive, on the hypothesis
that a written profile carries the severity/CIA judgement more faithfully than a
per-asset 1-5 number derived from a path or a table name.

The document is the source of truth; nothing here is hardcoded except the alias
map, which reconciles the short server names some scan drivers use (``fs:corp``)
with the fully-qualified names in the document (``fs:corp_filesystem``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROFILE_DOC = REPO_ROOT / "docs" / "mcp-tools" / "server-profiles.md"

# Section heading: "### fs_fintech_fs".
_SECTION_RE = re.compile(r"^### (?P<name>\S+)\s*$", re.MULTILINE)
# Fact line inside a section: "**Tier: XL** · `fs:fintech_fs` · 14 tools · ...".
_FACT_RE = re.compile(r"\*\*Tier:\s*(?P<tier>[A-Z]+)\*\*\s*·\s*`(?P<server>[^`]+)`")

# Scan drivers that use a shorter server name than the profile document.
_ALIASES = {
    "fs:corp": "fs:corp_filesystem",
    "sqlite:cbg": "sqlite:cbg_sqlite",
}

# Per-asset sensitivity table inside a profile section. Header row:
# "| Asset | Sens. | C | I | A | Why |" (case-insensitive on the two key cells).
_ASSET_TABLE_HEADER_RE = re.compile(r"^\|\s*Asset\s*\|\s*Sens\.?\s*\|", re.IGNORECASE)
# A data row's first two cells: "| `asset-id` | 4 | ...". The asset id is taken
# VERBATIM after stripping one surrounding backtick pair and whitespace — no other
# normalization, so path ids like `/`, `sensitive/` and `README.md` round-trip.
_ASSET_TABLE_ROW_RE = re.compile(r"^\|\s*`?(?P<asset>[^|`]+?)`?\s*\|\s*(?P<sens>[^|]+?)\s*\|")


class ProfileNotFoundError(KeyError):
    """Raised when a scan asks for an org profile the document does not define."""


class ProfileAssetTableError(ValueError):
    """Raised when a profile's per-asset sensitivity table is missing or malformed."""


def parse_asset_table(text: str) -> dict[str, int]:
    """Parse a profile section's ``| Asset | Sens. | ... |`` table(s).

    Returns ``{asset_id: sensitivity}`` with ids kept exactly as written (only a
    surrounding backtick pair and whitespace stripped). Multiple tables in one
    section are merged. Raises :class:`ProfileAssetTableError` when the section
    has no table, a row's Sens. cell is not an integer 1-5, or an asset id
    appears twice — the table is a scoring input, so silence is not an option.
    """
    sensitivities: dict[str, int] = {}
    in_table = False
    for line in text.splitlines():
        if _ASSET_TABLE_HEADER_RE.match(line):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.lstrip().startswith("|"):
            in_table = False  # table ended; a later table may start again
            continue
        if re.match(r"^\|[\s:|-]+\|?\s*$", line):
            continue  # the |---|---| separator row
        row = _ASSET_TABLE_ROW_RE.match(line)
        if row is None:
            raise ProfileAssetTableError(f"unparsable asset-table row: {line!r}")
        asset = row.group("asset").strip()
        sens_cell = row.group("sens").strip().strip("*")
        try:
            sens = int(sens_cell)
        except ValueError:
            raise ProfileAssetTableError(
                f"asset {asset!r}: Sens. cell {sens_cell!r} is not an integer"
            ) from None
        if not 1 <= sens <= 5:
            raise ProfileAssetTableError(f"asset {asset!r}: sensitivity {sens} outside 1-5")
        if asset in sensitivities:
            raise ProfileAssetTableError(f"duplicate asset row {asset!r}")
        sensitivities[asset] = sens
    if not sensitivities:
        raise ProfileAssetTableError(
            "profile section has no '| Asset | Sens. | ... |' table — profile-sensitivity "
            "modes require one row per registry asset"
        )
    return sensitivities


def missing_asset_rows(sensitivities: dict[str, int], asset_ids) -> list[str]:
    """Registry asset ids that have no row in the parsed profile table (sorted)."""
    return sorted(a for a in asset_ids if a not in sensitivities)


# The spec's six judgement flags (docs/standards/mcp-profile-spec.md) — the part
# of a Contents cell that enumeration cannot know.
PROFILE_FLAGS = (
    "self-sufficient",
    "population",
    "completeness-is-the-asset",
    "metadata-only",
    "hub",
    "public",
)


@dataclass(frozen=True)
class AssetRow:
    """One fully parsed row of a profile's asset table (spec v1 columns)."""

    asset_id: str
    sensitivity: int
    cia: dict[str, str]  # {"C": "H", "I": "M", "A": "L"} (empty when columns absent)
    contents: str  # the Contents cell verbatim (may be empty on 6-column tables)
    why: str
    flags: tuple[str, ...]  # spec flags found among the Contents tokens


def parse_asset_rows(text: str) -> list[AssetRow]:
    """Parse the asset table into full :class:`AssetRow` records.

    Column positions are taken from the header row, so both the 6-column
    (`Why` only) and the spec-v1 7-column (`Contents` + `Why`) layouts parse.
    This is the reader the tools+description-only scan uses to build its asset
    registry — the profile IS the asset inventory there, so every cell matters,
    not just Sens. Raises :class:`ProfileAssetTableError` on the same conditions
    as :func:`parse_asset_table`.
    """
    rows: list[AssetRow] = []
    seen: set[str] = set()
    columns: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if _ASSET_TABLE_HEADER_RE.match(stripped):
            columns = [
                c.strip().strip("*").rstrip(".").lower() for c in stripped.strip("|").split("|")
            ]
            continue
        if not columns:
            continue
        if not stripped.startswith("|"):
            columns = []
            continue
        if re.match(r"^\|[\s:|-]+\|?\s*$", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < len(columns):
            raise ProfileAssetTableError(
                f"row has {len(cells)} cells, header has {len(columns)}: {stripped!r}"
            )
        by_col = dict(zip(columns, cells))
        asset = by_col.get("asset", "").strip().strip("`").strip()
        try:
            sens = int(by_col.get("sens", "").strip().strip("*"))
        except ValueError:
            raise ProfileAssetTableError(
                f"asset {asset!r}: Sens. cell {by_col.get('sens')!r} is not an integer"
            ) from None
        if not 1 <= sens <= 5:
            raise ProfileAssetTableError(f"asset {asset!r}: sensitivity {sens} outside 1-5")
        if asset in seen:
            raise ProfileAssetTableError(f"duplicate asset row {asset!r}")
        seen.add(asset)
        contents = by_col.get("contents", "")
        tokens = {t.strip() for t in contents.split("·")}
        rows.append(
            AssetRow(
                asset_id=asset,
                sensitivity=sens,
                cia={
                    k.upper(): by_col[k].strip().strip("*") for k in ("c", "i", "a") if k in by_col
                },
                contents=contents,
                why=by_col.get("why", ""),
                flags=tuple(f for f in PROFILE_FLAGS if f in tokens),
            )
        )
    if not rows:
        raise ProfileAssetTableError(
            "profile section has no '| Asset | Sens. | ... |' table — profile-sensitivity "
            "modes require one row per registry asset"
        )
    return rows


def expected_use(text: str) -> str:
    """The profile's 'Expected organizational/agent use' paragraph, or ''.

    Feeds the behavioral-baseline stage as the app purpose in scans whose only
    inputs are the tool catalog and the profile.
    """
    match = re.search(
        r"\*\*Expected (?:organizational|agent) use\.?\*\*\s*(.+?)(?=\n\s*\n|\Z)",
        text,
        re.DOTALL,
    )
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def strip_profile_flags(text: str) -> str:
    """Remove the six judgement flags from every Contents cell (noflags scheme).

    The shape and facts stay; only the ``· <flag>`` tokens go. Measures how much
    the flags (hub, population, self-sufficient, …) carry versus the prose — e.g.
    whether the model still fires the hub/population tier-5 escapes without them.
    """
    pattern = re.compile(r"\s*·\s*(?:" + "|".join(re.escape(f) for f in PROFILE_FLAGS) + r")\b")
    return pattern.sub("", text)


def terse_profile(text: str) -> str:
    """The MINIMUM viable scheme: the fact line + a table of Asset · Sens · shape+flags.

    Drops the prose header, the C/I/A columns, the Why column, and the free-text
    facts inside Contents — keeping only each asset's id, its sensitivity, its
    shape token, and its flags. Tests whether the structured skeleton alone
    scores as well as the full written profile ("is less enough?").
    """
    fact_line = next((ln for ln in text.splitlines() if _FACT_RE.search(ln)), "")
    rows = parse_asset_rows(text)
    out = [fact_line, "", "| Asset | Sens. | Contents |", "|---|---|---|"]
    for row in rows:
        shape = row.contents.split("·")[0].strip() if row.contents else "item"
        cell = " · ".join([shape, *row.flags]) if row.flags else shape
        out.append(f"| `{row.asset_id}` | {row.sensitivity} | {cell} |")
    return "\n".join(out) + "\n"


def prose_profile_view(text: str) -> str:
    """The profile WITHOUT its markdown tables (the inverse of the struct view).

    Used by the ``five_level_v2_ult_imponly`` ablation: the tool-impact stage
    sees the org's prose (owner, purpose, expected use, CIA) but not the
    per-asset inventory — action-type judgement needs context, not the table.
    """
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("|"))


def structured_profile_view(text: str) -> str:
    """The profile reduced to its STRUCTURED parts: fact line, tables, CIA line.

    Used by the ``five_level_v2_ult_struct`` ablation: the model sees only the
    machine-checkable statements (tier fact line, the per-asset ``| Asset |
    Sens. |`` table rows, and the "In general: C > I > A" ordering), with all
    free prose removed. The asset table survives the transformation, so
    :func:`parse_asset_table` works unchanged on the result.
    """
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if (
            _FACT_RE.search(stripped)
            or stripped.startswith("|")
            or stripped.startswith("**In general")
            or stripped.startswith("**CIA in general")
        ):
            kept.append(stripped)
    return "\n".join(kept)


@dataclass(frozen=True)
class ServerProfile:
    """One server's written organizational profile."""

    name: str  # section name, e.g. "fs_fintech_fs"
    server: str  # server id declared in the section, e.g. "fs:fintech_fs"
    tier: str  # length tier: XS / S / M / L / XL
    text: str  # the section body, verbatim (this is what the model reads)

    @property
    def word_count(self) -> int:
        """Prose word count — the tier experiment's dose variable.

        Markdown table lines are excluded: the per-asset sensitivity table is a
        structured scoring input (added for the profile-sensitivity modes), not
        part of the written-description dose the XS-XL tiers vary.
        """
        prose = "\n".join(
            line for line in self.text.splitlines() if not line.lstrip().startswith("|")
        )
        return len(re.findall(r"[A-Za-z0-9_./*`'-]+", prose))

    @property
    def asset_sensitivity(self) -> dict[str, int]:
        """The org's own per-asset 1-5 sensitivities, parsed from the section's table.

        Raises :class:`ProfileAssetTableError` if the section carries no table —
        only the profile-sensitivity scan modes require one.
        """
        return parse_asset_table(self.text)


@lru_cache(maxsize=1)
def load_profiles(doc: Path | None = None) -> dict[str, ServerProfile]:
    """Parse the profile document into ``{name -> ServerProfile}``.

    Sections without the ``**Tier:** · `server-id``` fact line are skipped: they
    are prose sections of the document (the index, the group intros), not server
    profiles. Cached, since the document is read once per process.
    """
    path = doc or PROFILE_DOC
    if not path.exists():
        raise FileNotFoundError(f"no server-profile document at {path}")
    text = path.read_text(encoding="utf-8")

    profiles: dict[str, ServerProfile] = {}
    matches = list(_SECTION_RE.finditer(text))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        # A trailing "## <group>" heading belongs to the next group, not this section.
        body = re.split(r"\n## ", body)[0].strip()
        fact = _FACT_RE.search(body)
        if fact is None:
            continue
        name = match.group("name")
        profiles[name] = ServerProfile(
            name=name, server=fact.group("server"), tier=fact.group("tier"), text=body
        )
    return profiles


def profile_for(server: str, *, doc: Path | None = None) -> ServerProfile:
    """Return the profile for ``server``, looked up by server id or section name.

    ``server`` may be the server id the scan uses (``fs:fintech_fs``), one of the
    short aliases (``fs:corp``), or the document's section name
    (``fs_fintech_fs``). Raises :class:`ProfileNotFoundError` rather than
    returning an empty description — a desc-mode scan that silently ran without
    its description would look like a normal scan in the artifact.
    """
    profiles = load_profiles(doc)
    wanted = _ALIASES.get(server, server)
    if wanted in profiles:
        return profiles[wanted]
    for profile in profiles.values():
        if profile.server == wanted:
            return profile
    raise ProfileNotFoundError(
        f"no organizational profile for {server!r} in {doc or PROFILE_DOC}; "
        f"known: {sorted(p.server for p in profiles.values())}"
    )


def main(argv: list[str] | None = None) -> int:
    """List the parsed profiles (``python -m mcp_security.static_scoring.server_profiles``)."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default=None, help="print one profile's full text")
    args = parser.parse_args(argv)

    if args.server:
        profile = profile_for(args.server)
        print(
            f"# {profile.name} ({profile.server}) tier={profile.tier} words={profile.word_count}\n"
        )
        print(profile.text)
        try:
            table = profile.asset_sensitivity
        except ProfileAssetTableError as exc:
            print(f"\n[asset table] none parsed: {exc}")
        else:
            print(f"\n[asset table] {len(table)} rows:")
            for asset, sens in table.items():
                print(f"  {sens}  {asset}")
        return 0
    profiles = load_profiles()
    print(f"{len(profiles)} profiles in {PROFILE_DOC}")
    for profile in profiles.values():
        print(
            f"  {profile.name:24s} {profile.server:24s} tier={profile.tier:2s} "
            f"words={profile.word_count}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
