"""Static, pre-runtime MCP scan: understand a server's tools and assets.

This is the scanner the framework runs **before** an MCP server is live. It never
connects to a running server. It assembles the server's description from static
sources —

* **tools** from the server's own saved ``tools/list`` (:mod:`.tool_list`), and
* **assets** from the on-disk store the server fronts (a filesystem tree, a
  sqlite schema, the seeded slack channels) —

then hands that description to the LLM understanding stage
(:class:`mcp_security.static_scoring.pipeline.StaticScorer` in ``strict`` mode) to
derive every risk primitive. Nothing is hardcoded and no checked-in risk table is
read: if the model is unreachable the scan raises rather than guess.

The result is a *scan artifact* (``reports/scan/<server>.json``) with the same
shape as a static table — tool impact, asset sensitivity, per-pair blast radius,
the multiplied ``cells`` matrix and its ``bands``. The call ranker
(:mod:`mcp_security.call_scoring`) scores observed calls against this freshly
derived matrix, never against the evaluation ground truth.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from mcp_security.static_scoring import registry as reg
from mcp_security.static_scoring.pipeline import build_static_table
from mcp_security.static_scoring.registry import ServerRegistry

from .atomic_flags import enrich_scan
from .tool_list import load_tool_list

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCAN_DIR = REPO_ROOT / "reports" / "scan"
_DEMO = REPO_ROOT / "demo"

# Where each server kind's assets live on disk by default (the demo stores).
_DEFAULT_ROOTS = {
    "filesystem": _DEMO / "corp_filesystem",
    "sqlite": _DEMO / "cbg_sqlite" / "cbg.db",
}


@dataclass
class ScanResult:
    """A completed static scan of one server: its tools, assets and risk matrix."""

    server: str
    kind: str
    table: dict

    @property
    def n_tools(self) -> int:
        return len(self.table.get("tool_impact", {}))

    @property
    def n_assets(self) -> int:
        return len(self.table.get("asset_sensitivity", {}))


# Declarative-registry kinds: their assets are server-defined scopes (channels,
# calendars, repositories), not enumerated from a disk store, and their advertised
# tool set is declared from the server source rather than a saved tools/list.
_DECLARATIVE_REGISTRIES = {
    "slack": reg.load_slack_registry,
    "calendar": reg.load_calendar_registry,
    "github": reg.load_github_registry,
}


def build_registry(
    kind: str,
    *,
    root: Path | None = None,
    server: str | None = None,
    by_file: bool = False,
    tool_list: Path | None = None,
) -> ServerRegistry:
    """Assemble a :class:`ServerRegistry` from static sources (no live MCP).

    Disk-backed kinds (filesystem, sqlite) take their tools from the server's own
    saved ``tools/list`` and their assets from the on-disk store (``root``);
    ``by_file`` selects per-file (take2) filesystem assets. Declarative kinds
    (slack, calendar, github) take both their advertised tool set and their asset
    scopes from the registry, since those servers front no local disk store.
    """
    if kind in _DECLARATIVE_REGISTRIES:
        base = _DECLARATIVE_REGISTRIES[kind]()
        name = server or base.server
        return ServerRegistry(
            server=name, kind=kind, tools=base.tools, assets=base.assets, apps=base.apps
        )

    tools = load_tool_list(kind, path=tool_list)
    if kind == "filesystem":
        store = root or _DEFAULT_ROOTS["filesystem"]
        assets = (
            reg.filesystem_assets_by_file(store) if by_file else reg.filesystem_assets(store)
        )
        apps = reg.FS_DEFAULT_APPS
        name = server or f"fs:{store.name}"
    elif kind == "sqlite":
        store = root or _DEFAULT_ROOTS["sqlite"]
        assets = reg.sqlite_assets(store)
        apps = reg.SQLITE_DEFAULT_APPS
        name = server or f"sqlite:{store.parent.name}"
    else:
        raise ValueError(f"unsupported scan kind: {kind!r}")
    return ServerRegistry(server=name, kind=kind, tools=tools, assets=list(assets), apps=apps)


def scan_server(
    kind: str,
    *,
    root: Path | None = None,
    server: str | None = None,
    by_file: bool = False,
    tool_list: Path | None = None,
    use_llm: bool = True,
    version: str = "scan-0000-00-00",
) -> ScanResult:
    """Run a full static scan: assemble the registry, then derive risk with the LLM.

    ``use_llm`` defaults to True and the scan runs in strict (LLM-only) mode, so an
    unreachable model raises :class:`LLMUnavailableError` instead of falling back
    to a heuristic. ``use_llm=False`` is offered only for tests and offline smoke
    runs and uses the deterministic baseline (never shipped as a real scan).
    """
    registry = build_registry(
        kind, root=root, server=server, by_file=by_file, tool_list=tool_list
    )
    logger.info(
        "scanning %s (%s): %d tools, %d assets",
        registry.server,
        kind,
        len(registry.tools),
        len(registry.assets),
    )
    table = build_static_table(registry, use_llm=use_llm, strict=use_llm, version=version)
    # Honest provenance: a real scan is LLM-derived; --no-llm is only a smoke baseline.
    table["provenance"] = "llm-scan" if use_llm else "offline-baseline"
    # Record the registry kind verbatim. The LLM also infers a free-text `mcp_kind`
    # (e.g. "team messaging workspace"), but the call ranker dispatches its resolver
    # on this exact kind so it never depends on the inferred phrasing.
    table["server_kind"] = kind
    # Additive enrichment: flag every tool's atomic operation from the taxonomy
    # (always deterministic), and rank each tool's inputs by risk — with the LLM
    # when this is a real (LLM) scan, else the rule heuristic.
    enrich_scan(table, registry.tools, use_llm=use_llm)
    return ScanResult(server=registry.server, kind=kind, table=table)


def _safe_name(server: str) -> str:
    """A filesystem-safe stem for a server name (``fs:corp`` -> ``fs_corp``)."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in server)


def write_scan(result: ScanResult, out_dir: Path = DEFAULT_SCAN_DIR) -> Path:
    """Write the scan artifact to ``<out_dir>/<server>.json`` and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_safe_name(result.server)}.json"
    path.write_text(json.dumps(result.table, indent=2), encoding="utf-8")
    return path
