"""Tests for the classifier orchestrator."""

from mcp_security.atomic_ops.classifier import classify_server
from mcp_security.atomic_ops.server_catalog import ServerEntry, get_server


def test_classify_sqlite_server_returns_readme_and_toollist_classifications():
    server = get_server("sqlite")
    result = classify_server(server)
    assert len(result.readme_classifications) > 0
    assert len(result.toollist_classifications) > 0


def test_classify_sqlite_write_query_tagged_worst_case_from_toollist():
    server = get_server("sqlite")
    result = classify_server(server)
    write_q = next(
        c for c in result.toollist_classifications if c.tool_name == "write_query"
    )
    assert {"EXECUTE", "DELETE", "SCHEMA_MODIFY", "WRITE"}.issubset(write_q.atomic_ops)


def test_classify_filesystem_write_file_tagged_overwrite():
    server = get_server("filesystem")
    result = classify_server(server)
    wf = next(
        c for c in result.toollist_classifications if c.tool_name == "write_file"
    )
    assert "OVERWRITE" in wf.atomic_ops


def test_max_severity_correct():
    server = get_server("sqlite")
    result = classify_server(server)
    write_q = next(
        c for c in result.toollist_classifications if c.tool_name == "write_query"
    )
    assert write_q.max_severity == 5


def test_classification_includes_rule_ids():
    server = get_server("sqlite")
    result = classify_server(server)
    write_q = next(
        c for c in result.toollist_classifications if c.tool_name == "write_query"
    )
    assert len(write_q.rule_ids) > 0


def test_classify_orphan_server_is_readme_only():
    server = ServerEntry(
        name="orphan",
        package="example/orphan",
        tier="B",
        install_hint="n/a",
    )
    result = classify_server(server)
    assert len(result.toollist_classifications) == 0
    assert len(result.readme_classifications) == 0
    assert result.discovery_source == "readme_only"
