"""Tests for tool_matcher."""

from mcp.types import Tool

from tests.testbed.harness.tool_matcher import describe_matches, match


def make_tool(name: str) -> Tool:
    """Create a minimal Tool for use in tests."""
    return Tool(name=name, description="", inputSchema={"type": "object", "properties": {}})


def test_match_by_keyword() -> None:
    """A tool whose name contains a keyword from match_rules is matched once."""
    tools = [make_tool("read_file"), make_tool("get_time")]
    templates = [
        {
            "id": "path_traversal",
            "category": "C2",
            "match_rules": {"tool_name_contains": ["read", "file"]},
        },
    ]
    result = match(tools, templates)
    # 'read_file' matches (contains 'read'); any() short-circuits, so one match per (tool, template).
    # 'get_time' does not contain 'read' or 'file'.
    assert len(result) == 1
    assert result[0][0].name == "read_file"
    assert result[0][1]["id"] == "path_traversal"


def test_wildcard_matches_all() -> None:
    """The '*' wildcard keyword causes the template to match every tool."""
    tools = [make_tool("echo"), make_tool("add"), make_tool("print")]
    templates = [
        {
            "id": "tool_poisoning",
            "category": "C6",
            "match_rules": {"tool_name_contains": ["*"]},
        },
    ]
    result = match(tools, templates)
    assert len(result) == 3


def test_no_match() -> None:
    """No matches are returned when no tool name contains the template keywords."""
    tools = [make_tool("get_time")]
    templates = [
        {
            "id": "command_injection",
            "category": "C1",
            "match_rules": {"tool_name_contains": ["exec", "shell"]},
        },
    ]
    assert match(tools, templates) == []


def test_describe_matches_empty() -> None:
    """describe_matches reports no matches when the list is empty."""
    assert "No tool" in describe_matches([])


def test_describe_matches_nonempty() -> None:
    """describe_matches lists each tool-template pair with id and category."""
    tools = [make_tool("read_file")]
    templates = [
        {
            "id": "path_traversal",
            "category": "C2",
            "match_rules": {"tool_name_contains": ["read"]},
        },
    ]
    result = match(tools, templates)
    summary = describe_matches(result)
    assert "1 matches" in summary
    assert "read_file" in summary
    assert "path_traversal" in summary
    assert "C2" in summary


def test_tool_matches_multiple_templates() -> None:
    """A tool can match more than one template if keywords overlap."""
    tools = [make_tool("exec_shell")]
    templates = [
        {
            "id": "command_injection",
            "category": "C1",
            "match_rules": {"tool_name_contains": ["exec"]},
        },
        {
            "id": "shell_escape",
            "category": "C3",
            "match_rules": {"tool_name_contains": ["shell"]},
        },
    ]
    result = match(tools, templates)
    assert len(result) == 2
    matched_ids = {t["id"] for _, t in result}
    assert matched_ids == {"command_injection", "shell_escape"}


def test_match_is_case_insensitive() -> None:
    """Keyword matching is case-insensitive."""
    tools = [make_tool("ReadFile")]
    templates = [
        {
            "id": "path_traversal",
            "category": "C2",
            "match_rules": {"tool_name_contains": ["read"]},
        },
    ]
    result = match(tools, templates)
    assert len(result) == 1


def test_keyword_case_insensitive() -> None:
    """Keywords in match_rules should be case-insensitive."""
    tools = [make_tool("read_file")]
    templates = [
        {
            "id": "path_traversal",
            "category": "C2",
            "match_rules": {"tool_name_contains": ["READ", "FILE"]},
        },
    ]
    result = match(tools, templates)
    assert len(result) == 1


def test_empty_tools_returns_empty() -> None:
    """An empty tool list produces no matches regardless of templates."""
    templates = [
        {
            "id": "command_injection",
            "category": "C1",
            "match_rules": {"tool_name_contains": ["exec"]},
        },
    ]
    assert match([], templates) == []


def test_empty_templates_returns_empty() -> None:
    """An empty template list produces no matches regardless of tools."""
    tools = [make_tool("exec_cmd")]
    assert match(tools, []) == []
