"""Orchestrates rule application over a server's tools."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import readme_rules, toollist_rules
from .discovery import discover_server
from .rules_base import RuleHit
from .server_catalog import ServerEntry
from .taxonomy import AtomicOp, load_taxonomy

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TAXONOMY = (
    REPO_ROOT
    / "presentations"
    / "heatmap_byhand"
    / "csv"
    / "atomic_operations.csv"
)


@dataclass
class ClassifiedTool:
    """One tool's classification under one source (readme or toollist)."""

    server_name: str
    tool_name: str
    tool_description: str
    atomic_ops: set[str] = field(default_factory=set)
    rule_ids: list[str] = field(default_factory=list)
    max_severity: int = 0
    severity_label: str = ""
    source: str = ""
    notes: str = ""


@dataclass
class ServerClassification:
    """Both source classifications for one server."""

    server: ServerEntry
    readme_classifications: list[ClassifiedTool] = field(default_factory=list)
    toollist_classifications: list[ClassifiedTool] = field(default_factory=list)
    discovery_source: str = "readme_only"


def _extract_readme_tools(readme: str) -> list[tuple[str, str]]:
    """Pull (tool_name, short_description) pairs out of a README.

    Looks for level-3 headers shaped like ### `tool_name` (back-tick-quoted
    tool name), then captures the first paragraph after **What it does:** as
    the description.
    """
    if not readme:
        return []
    pairs: list[tuple[str, str]] = []
    header_re = re.compile(r"^###\s+`([^`]+)`", re.MULTILINE)
    headers = list(header_re.finditer(readme))
    for i, m in enumerate(headers):
        tool = m.group(1).strip()
        body_start = m.end()
        body_end = headers[i + 1].start() if i + 1 < len(headers) else len(readme)
        body = readme[body_start:body_end]
        desc_match = re.search(
            r"\*\*What it does:\*\*\s*(.+?)(?:\n\n|\Z)",
            body,
            re.DOTALL,
        )
        desc = ""
        if desc_match:
            desc = desc_match.group(1).strip().replace("\n", " ")
        pairs.append((tool, desc))
    return pairs


def _to_op_set_and_severities(
    hits: list[RuleHit], taxonomy: list[AtomicOp]
) -> tuple[set[str], int, str]:
    ops = {h.atomic_op for h in hits}
    severities = {op.name: (op.severity, op.severity_label) for op in taxonomy}
    if not ops:
        return ops, 0, ""
    pairs = [severities[o] for o in ops if o in severities]
    if not pairs:
        return ops, 0, ""
    max_sev, label = max(pairs, key=lambda p: p[0])
    return ops, max_sev, label


def classify_server(
    server: ServerEntry,
    taxonomy: list[AtomicOp] | None = None,
    prefer_live: bool = False,
) -> ServerClassification:
    """Classify every tool of a server from both README and tool-list sources."""
    if taxonomy is None:
        taxonomy = load_taxonomy(DEFAULT_TAXONOMY)
    readme_text = server.load_readme()
    disc = discover_server(server, prefer_live=prefer_live)

    readme_results: list[ClassifiedTool] = []
    readme_tools = _extract_readme_tools(readme_text)
    for name, desc in readme_tools:
        hits = readme_rules.classify_from_readme(name, desc, readme_text)
        ops_set, max_sev, label = _to_op_set_and_severities(hits, taxonomy)
        readme_results.append(
            ClassifiedTool(
                server_name=server.name,
                tool_name=name,
                tool_description=desc[:300],
                atomic_ops=ops_set,
                rule_ids=[h.rule_id for h in hits],
                max_severity=max_sev,
                severity_label=label,
                source="readme",
            )
        )

    toollist_results: list[ClassifiedTool] = []
    for entry in disc.tools:
        name = entry.get("name", "")
        desc = entry.get("description", "")
        schema = entry.get("inputSchema") or entry.get("input_schema") or {}
        hits = toollist_rules.classify_from_toollist(name, desc, schema)
        ops_set, max_sev, label = _to_op_set_and_severities(hits, taxonomy)
        toollist_results.append(
            ClassifiedTool(
                server_name=server.name,
                tool_name=name,
                tool_description=str(desc)[:300],
                atomic_ops=ops_set,
                rule_ids=[h.rule_id for h in hits],
                max_severity=max_sev,
                severity_label=label,
                source="toollist",
            )
        )

    return ServerClassification(
        server=server,
        readme_classifications=readme_results,
        toollist_classifications=toollist_results,
        discovery_source=disc.source,
    )
