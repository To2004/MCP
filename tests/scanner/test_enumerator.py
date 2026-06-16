"""Tests for per-kind asset enumeration."""

import sqlite3

from mcp_security.scanner.config_reader import spec_from_root
from mcp_security.scanner.enumerator import enumerate_assets
from mcp_security.scanner.safety import is_read_only


def test_filesystem_enumeration_by_extension(tmp_path):
    (tmp_path / "a.sql").write_text("x")
    (tmp_path / "b.sql").write_text("x")
    (tmp_path / "c.txt").write_text("x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "d.png").write_text("x")

    inv = enumerate_assets(spec_from_root(str(tmp_path)))
    by_name = {a.name: a for a in inv.assets}
    assert inv.kind == "filesystem"
    assert inv.source == "enumerated"
    assert by_name[".sql"].count == 2
    assert by_name[".txt"].count == 1
    assert by_name[".png"].count == 1


def test_filesystem_depth_cap(tmp_path):
    # Build a deep chain; with max_depth=1 only the top file is counted.
    from mcp_security.scanner.enumerator import _enumerate_filesystem

    (tmp_path / "top.txt").write_text("x")
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "buried.txt").write_text("x")

    inv = _enumerate_filesystem(spec_from_root(str(tmp_path)), max_depth=1)
    # Count files only (directory rows also carry a count = files directly inside).
    file_rows = [a for a in inv.assets if "directory" not in a.tags]
    assert sum(a.count for a in file_rows) == 1


def test_filesystem_emits_directories_ranked_by_contents(tmp_path):
    # Directories show up as assets and inherit the sensitivity of what they hold.
    (tmp_path / "readme.txt").write_text("x")
    sensitive = tmp_path / "sensitive"
    sensitive.mkdir()
    (sensitive / "dump.sql").write_text("x")  # .sql -> High

    inv = enumerate_assets(spec_from_root(str(tmp_path)))
    dirs = {a.name: a for a in inv.assets if "directory" in a.tags}
    # Both the root and the sub-directory are present.
    assert any(name.endswith("sensitive/") for name in dirs)
    sens = next(a for name, a in dirs.items() if name.endswith("sensitive/"))
    assert "ext:sql" in sens.tags  # ranked by its most sensitive file


def test_filesystem_by_file_lists_individual_files(tmp_path):
    from mcp_security.scanner.enumerator import _enumerate_filesystem

    (tmp_path / "a.sql").write_text("x")
    (tmp_path / "b.sql").write_text("x")

    inv = _enumerate_filesystem(spec_from_root(str(tmp_path)), by_file=True)
    file_rows = [a for a in inv.assets if "directory" not in a.tags]
    names = {a.name for a in file_rows}
    assert any(n.endswith("a.sql") for n in names)
    assert any(n.endswith("b.sql") for n in names)
    assert len(file_rows) == 2  # individual files, not one ".sql" bucket


def test_sqlite_enumeration_tags_pii_columns(tmp_path):
    db = tmp_path / "corp.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE customers (id INTEGER, email TEXT, name TEXT)")
    conn.execute("CREATE TABLE orders (id INTEGER, total REAL)")
    conn.execute("INSERT INTO customers VALUES (1, 'a@b.c', 'A')")
    conn.commit()
    conn.close()

    inv = enumerate_assets(spec_from_root(str(db), kind="sqlite"))
    by_name = {a.name: a for a in inv.assets}
    assert inv.kind == "sqlite"
    assert "customers" in by_name and "orders" in by_name
    assert "column:email" in by_name["customers"].tags
    assert by_name["orders"].tags == ()
    assert by_name["customers"].count == 1  # row count


def test_sqlite_missing_db_is_empty(tmp_path):
    inv = enumerate_assets(spec_from_root(str(tmp_path / "absent.db"), kind="sqlite"))
    assert inv.is_empty


def test_safety_gate_blocks_write_tools():
    # Read-only enumeration tools pass; write/delete tools are refused.
    assert is_read_only("list_directory", "List the contents of a directory")
    assert is_read_only("search_files", "Search for files matching a pattern")
    assert not is_read_only("write_file", "Write content to a file")
    assert not is_read_only("delete_file", "Delete a file")
    # Unclassified tools fail closed.
    assert not is_read_only("xyzzy", "does something unknown")
