"""Tests for loading a server's tools from its own saved tools/list."""

from __future__ import annotations

import json

import pytest

from mcp_security.scanner.tool_list import load_tool_list, tool_list_path


def test_loads_filesystem_tools_with_schema():
    tools = load_tool_list("filesystem")
    names = {t.name for t in tools}
    assert {"read_text_file", "write_file", "read_multiple_files"} <= names
    # The input schema rides along and exposes real parameters.
    rmf = next(t for t in tools if t.name == "read_multiple_files")
    params = {p["name"] for p in rmf.parameters()}
    assert params  # e.g. {"paths"}
    # to_prompt_json surfaces the parameters to the LLM.
    assert "parameters" in rmf.to_prompt_json()


def test_annotations_come_from_tools_list():
    tools = {t.name: t for t in load_tool_list("filesystem")}
    assert tools["read_text_file"].read_only_hint is True


def test_missing_tool_list_raises():
    assert tool_list_path("nope").name == "nope.json"
    with pytest.raises(FileNotFoundError):
        load_tool_list("nope")


def test_explicit_path(tmp_path):
    path = tmp_path / "x.json"
    path.write_text(json.dumps({"server": "s", "kind": "k", "tools": [
        {"name": "t", "description": "d", "input_schema": {"properties": {"n": {"type": "number"}}},
         "annotations": {"read_only_hint": True}}]}), encoding="utf-8")
    tools = load_tool_list("k", path=path)
    assert tools[0].name == "t" and tools[0].read_only_hint is True
    assert tools[0].parameters()[0]["name"] == "n"
