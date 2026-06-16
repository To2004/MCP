"""Tests for per-kind enumeration THROUGH the MCP protocol (the server's tools).

These drive a fake in-memory session so no real server / network is needed; the
live path is exercised manually against ``uvx mcp-server-sqlite``.
"""

import json

import anyio

from mcp_security.scanner import enumerator as en
from mcp_security.scanner.config_reader import ConnectionSpec


class _Tool:
    def __init__(self, name, required=(), description=""):
        self.name = name
        self.description = description or name.replace("_", " ")
        self.inputSchema = {"type": "object", "required": list(required)}


class _ToolsResult:
    def __init__(self, tools):
        self.tools = tools


class _Content:
    def __init__(self, text):
        self.text = text


class _CallResult:
    def __init__(self, text):
        self.content = [_Content(text)]


class FakeSession:
    """Minimal stand-in for an MCP ClientSession used by the enumerators."""

    def __init__(self, tools, responder):
        self._tools = tools
        self._responder = responder

    async def list_tools(self):
        return _ToolsResult(self._tools)

    async def call_tool(self, name, args):
        return _CallResult(self._responder(name, args))


def test_mcp_sqlite_lists_tables_and_tags_pii_via_tools():
    tools = [
        _Tool("list_tables"),
        _Tool("describe_table", required=("table_name",)),
        _Tool("write_query", required=("query",)),  # must never be called
    ]

    def responder(name, args):
        assert name != "write_query", "enumeration must not call write tools"
        if name == "list_tables":
            # Python-repr (single quotes) — the real server emits this, not JSON.
            return "[{'name': 'customers'}, {'name': 'orders'}, {'name': 'sqlite_sequence'}]"
        if name == "describe_table":
            if args["table_name"] == "customers":
                return "[{'cid': 0, 'name': 'id'}, {'cid': 1, 'name': 'email'}]"
            return "[{'cid': 0, 'name': 'id'}]"
        return ""

    spec = ConnectionSpec(name="s", kind="sqlite", transport="stdio", command="x")
    inv = anyio.run(en._mcp_enumerate_sqlite, spec, FakeSession(tools, responder))

    by_name = {a.name: a for a in inv.assets}
    assert set(by_name) == {"customers", "orders"}  # sqlite_sequence skipped
    assert "column:email" in by_name["customers"].tags
    assert by_name["orders"].tags == ()
    assert inv.note == "via list_tables + describe_table"


def test_mcp_filesystem_walks_directory_tree_via_tools():
    tools = [
        _Tool("directory_tree", required=("path",)),
        _Tool("write_file", required=("path", "content")),  # must never be called
    ]
    tree = [
        {"name": "readme.md", "type": "file"},
        {
            "name": "sensitive",
            "type": "directory",
            "children": [{"name": "dump.sql", "type": "file"}],
        },
    ]

    def responder(name, args):
        assert name == "directory_tree"
        return json.dumps(tree)

    spec = ConnectionSpec(
        name="fs", kind="filesystem", transport="stdio", command="x", roots=("/srv/data",)
    )
    inv = anyio.run(en._mcp_enumerate_filesystem, spec, FakeSession(tools, responder))

    dirs = {a.name: a for a in inv.assets if "directory" in a.tags}
    files = {a.name for a in inv.assets if "directory" not in a.tags}
    # Directory shows up and inherits the sensitivity of the .sql beneath it.
    sens = next(a for name, a in dirs.items() if name.endswith("sensitive/"))
    assert "ext:sql" in sens.tags
    assert ".sql" in files and ".md" in files
    assert inv.note == "via directory_tree"


def test_mcp_sqlite_falls_back_when_no_list_tool():
    # A sqlite server exposing no read-only list tool yields an empty inventory,
    # so enumerate_assets can fall through to the next path.
    tools = [_Tool("write_query", required=("query",))]
    spec = ConnectionSpec(name="s", kind="sqlite", transport="stdio", command="x")
    inv = anyio.run(en._mcp_enumerate_sqlite, spec, FakeSession(tools, lambda n, a: ""))
    assert inv.is_empty
