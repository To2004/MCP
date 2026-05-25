"""Tests for the discovery module."""

from mcp_security.atomic_ops.discovery import (
    DiscoveryResult,
    discover_server,
)
from mcp_security.atomic_ops.server_catalog import ServerEntry, get_server


def test_discovery_falls_back_to_cached_tool_list():
    server = get_server("filesystem")
    result = discover_server(server, prefer_live=False)
    assert isinstance(result, DiscoveryResult)
    assert result.source in {"cached", "live"}
    assert len(result.tools) > 0


def test_discovery_uses_readme_only_when_no_tool_list():
    # Synthetic server with neither readme_path nor tool_list_path
    server = ServerEntry(
        name="orphan",
        package="example/orphan",
        tier="B",
        install_hint="n/a",
    )
    result = discover_server(server, prefer_live=False)
    assert result.readme_only
    assert result.tools == []


def test_discovery_returns_tools_as_dicts():
    server = get_server("sqlite")
    result = discover_server(server, prefer_live=False)
    assert all("name" in t and "description" in t for t in result.tools)
