"""Tests for the static MCP server catalog."""

from mcp_security.atomic_ops.server_catalog import KNOWN_SERVERS


def test_known_servers_has_tier_a_four():
    names = {s.name for s in KNOWN_SERVERS}
    assert {"filesystem", "sqlite", "slack", "github"}.issubset(names)


def test_known_servers_have_readme_paths():
    for s in KNOWN_SERVERS:
        if s.tier == "A":
            assert s.readme_path is not None
            assert s.readme_path.exists(), f"missing readme: {s.readme_path}"


def test_known_servers_have_tool_list_paths_for_tier_a():
    for s in KNOWN_SERVERS:
        if s.tier == "A":
            assert s.tool_list_path is not None
            assert s.tool_list_path.exists(), f"missing tool list: {s.tool_list_path}"


def test_tool_list_json_has_expected_shape():
    fs = next(s for s in KNOWN_SERVERS if s.name == "filesystem")
    tools = fs.load_tool_list()
    assert isinstance(tools, list)
    assert len(tools) >= 10
    sample = tools[0]
    assert "name" in sample
    assert "description" in sample
    assert "inputSchema" in sample


def test_count_of_tier_b_servers():
    tier_b = [s for s in KNOWN_SERVERS if s.tier == "B"]
    assert len(tier_b) >= 6
