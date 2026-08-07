"""The advertised tool catalog: what each tool is called, does, and accepts.

Captured from each server's own ``tools/list`` response, so the descriptions and
input schemas here are the vendor's, not ours. Two things the binding layer needs
that the policy register does not carry:

* **the description** — ``manage-accounts`` documents its own modes ("Actions:
  'list' (show accounts), 'add' (authenticate new account)"), which is what
  separates two register assets that share a tool;
* **the input schema** — which parameters exist, which are required, and what
  shape their values take, which is what lets a synthetic call be well-formed
  rather than invented.

Nothing here is server-specific: a catalog is loaded by path and parsed by shape.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"

#: Catalog stem per server stem. Several organizations share one vendor surface —
#: Aurora Airways and the reference calendar deployment advertise the same 13
#: tools — so the mapping is many-to-one by design.
SERVER_CATALOGS = {
    "calendar_aurora": "calendar_real",
    "calendar_real": "calendar_real",
    "github_helios": "github_real",
    "github_real": "github_real",
    "slack_vireo": "slack_real",
    "slack_real": "slack_real",
    "sqlite_cbg_sqlite": "sqlite",
    "fs_corp_filesystem": "filesystem",
    "fs_fintech_fs": "filesystem",
    "fs_law_firm_fs": "filesystem",
    "fs_medical_clinic_fs": "filesystem",
    "fs_media_studio_fs": "filesystem",
}

#: A description that enumerates its own modes, e.g. "Actions: 'list' (show
#: accounts), 'add' (authenticate new account), 'remove' (remove account)".
_MODE_RE = re.compile(r"'([a-z][a-z_-]{1,24})'\s*\(([^)]{3,60})\)")


@dataclass(frozen=True)
class ToolSpec:
    """One advertised tool: its name, its own description, its input schema."""

    name: str
    description: str
    schema: dict

    @property
    def properties(self) -> dict[str, dict]:
        return dict(self.schema.get("properties") or {})

    @property
    def required(self) -> tuple[str, ...]:
        return tuple(self.schema.get("required") or ())

    def modes(self) -> dict[str, str]:
        """Modes the tool documents for itself, as ``value -> what it does``.

        A tool whose description spells out its own operations tells you which
        register asset a call means when the tool alone cannot: ``action='list'``
        reads the account directory, ``action='add'`` rewrites what every other
        tool can reach. Empty when the description documents no modes.
        """
        return {value: meaning.strip() for value, meaning in _MODE_RE.findall(self.description)}

    def mode_parameter(self) -> str | None:
        """The parameter carrying those modes, when the schema declares one.

        Preference order: a parameter whose schema enumerates exactly the
        documented modes, then one whose own description names them. ``None``
        when the tool documents modes but no parameter obviously carries them.
        """
        documented = set(self.modes())
        if not documented:
            return None
        for name, spec in self.properties.items():
            values = {str(v) for v in (spec.get("enum") or ())}
            if values & documented:
                return name
            text = str(spec.get("description") or "")
            if sum(mode in text for mode in documented) >= 2:
                return name
        return None


def load_catalog(path: Path) -> dict[str, ToolSpec]:
    """Every tool a captured ``tools/list`` advertises, keyed by name."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    tools = payload.get("tools", payload) if isinstance(payload, dict) else payload
    specs: dict[str, ToolSpec] = {}
    for tool in tools:
        name = tool.get("name")
        if not name:
            continue
        specs[name] = ToolSpec(
            name=name,
            description=tool.get("description") or "",
            schema=tool.get("input_schema") or tool.get("inputSchema") or {},
        )
    return specs


def catalog_for(server: str, *, tool_lists: Path | None = None) -> dict[str, ToolSpec]:
    """The advertised catalog for a server stem.

    Raises :class:`KeyError` for a server with no known catalog rather than
    returning an empty one — a silently empty catalog would look like a tool
    surface with no parameters, which is exactly the wrong default.
    """
    stem = SERVER_CATALOGS[server]
    return load_catalog((tool_lists or TOOL_LISTS) / f"{stem}.json")


__all__ = ["SERVER_CATALOGS", "TOOL_LISTS", "ToolSpec", "catalog_for", "load_catalog"]
