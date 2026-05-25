"""Tests for the tool-list rule classifier."""

from mcp_security.atomic_ops.toollist_rules import classify_from_toollist


def ops(hits):
    return {h.atomic_op for h in hits}


def test_read_prefix():
    hits = classify_from_toollist("read_text_file", "Returns text", {})
    assert "READ" in ops(hits)


def test_get_prefix_for_content():
    hits = classify_from_toollist("get_file_contents", "Returns file content", {})
    assert "READ" in ops(hits)


def test_get_prefix_for_metadata_is_not_read():
    hits = classify_from_toollist("get_file_info", "Returns file metadata", {})
    assert "METADATA" in ops(hits)
    assert "READ" not in ops(hits)


def test_list_prefix():
    hits = classify_from_toollist("list_directory", "Lists dir contents", {})
    assert "LIST" in ops(hits)


def test_search_prefix():
    hits = classify_from_toollist("search_files", "Finds matching paths", {})
    assert "SEARCH" in ops(hits)


def test_write_file_is_overwrite_and_write():
    hits = classify_from_toollist(
        "write_file",
        "Creates a new file or completely overwrites an existing one.",
        {},
    )
    op_set = ops(hits)
    assert "OVERWRITE" in op_set
    assert "WRITE" in op_set


def test_delete_prefix():
    hits = classify_from_toollist("delete_file", "Deletes a file", {})
    assert "DELETE" in ops(hits)


def test_move_prefix():
    hits = classify_from_toollist("move_file", "Moves a file", {})
    assert "MOVE" in ops(hits)


def test_create_directory():
    hits = classify_from_toollist("create_directory", "Creates a dir", {})
    assert "CREATE" in ops(hits)


def test_post_message():
    hits = classify_from_toollist(
        "slack_post_message", "Posts a message to a channel", {}
    )
    assert "BROADCAST" in ops(hits)


def test_query_with_freeform_sql_schema_tags_worst_case():
    schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }
    hits = classify_from_toollist(
        "write_query", "Executes any non-SELECT SQL statement", schema
    )
    op_set = ops(hits)
    assert "EXECUTE" in op_set
    assert "DELETE" in op_set
    assert "SCHEMA_MODIFY" in op_set
    assert "WRITE" in op_set


def test_read_query_is_read_only():
    schema = {"type": "object", "properties": {"query": {"type": "string"}}}
    hits = classify_from_toollist(
        "read_query", "Executes a SQL SELECT statement", schema
    )
    op_set = ops(hits)
    assert "READ" in op_set
    assert "DELETE" not in op_set
    assert "SCHEMA_MODIFY" not in op_set


def test_describe_table_is_metadata():
    hits = classify_from_toollist(
        "describe_table", "Returns the CREATE TABLE DDL", {}
    )
    assert "METADATA" in ops(hits)


def test_create_table_is_schema_modify():
    hits = classify_from_toollist(
        "create_table", "Executes a CREATE TABLE DDL", {}
    )
    assert "SCHEMA_MODIFY" in ops(hits)


def test_edit_file_is_modify():
    hits = classify_from_toollist(
        "edit_file", "Applies find-and-replace operations", {}
    )
    assert "MODIFY" in ops(hits)


def test_unknown_tool_returns_empty():
    hits = classify_from_toollist("frobulate", "frobulates the framistat", {})
    assert hits == []


def test_no_destructive_for_pure_read():
    hits = classify_from_toollist("read_text_file", "Reads a file", {})
    destructive = {"DELETE", "OVERWRITE", "EXECUTE", "SCHEMA_MODIFY"}
    assert ops(hits).isdisjoint(destructive)
