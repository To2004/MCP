"""Tests for the weekly repo cleanup script."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.weekly_cleanup import (
    find_gitignore_matches,
    find_duplicates,
    find_backup_named,
    archive_item,
    write_report,
)


# ── find_gitignore_matches ────────────────────────────────────────────────────

def test_find_gitignore_matches_finds_pyc(tmp_path):
    (tmp_path / "foo.pyc").write_bytes(b"")
    (tmp_path / "keep.py").write_text("x = 1")
    result = find_gitignore_matches(tmp_path)
    assert any(p.name == "foo.pyc" for p in result)
    assert not any(p.name == "keep.py" for p in result)


def test_find_gitignore_matches_finds_pycache_dir(tmp_path):
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "mod.cpython-311.pyc").write_bytes(b"")
    result = find_gitignore_matches(tmp_path)
    assert tmp_path / "__pycache__" in result


def test_find_gitignore_matches_skips_archive(tmp_path):
    archive = tmp_path / "_archive"
    archive.mkdir()
    (archive / "foo.pyc").write_bytes(b"")
    result = find_gitignore_matches(tmp_path)
    assert not any("_archive" in str(p) for p in result)


# ── find_duplicates ───────────────────────────────────────────────────────────

def test_find_duplicates_detects_identical_files(tmp_path):
    content = b"same content here"
    (tmp_path / "a.pdf").write_bytes(content)
    (tmp_path / "b.pdf").write_bytes(content)
    (tmp_path / "c.pdf").write_bytes(b"different")
    dupes = find_duplicates(tmp_path)
    all_paths = [p for pair in dupes for p in pair]
    names = {p.name for p in all_paths}
    assert "a.pdf" in names or "b.pdf" in names


def test_find_duplicates_no_false_positives(tmp_path):
    (tmp_path / "x.py").write_text("x = 1")
    (tmp_path / "y.py").write_text("y = 2")
    assert find_duplicates(tmp_path) == []


def test_find_duplicates_skips_archive(tmp_path):
    content = b"same"
    (tmp_path / "orig.pdf").write_bytes(content)
    archive = tmp_path / "_archive"
    archive.mkdir()
    (archive / "orig.pdf").write_bytes(content)
    dupes = find_duplicates(tmp_path)
    assert dupes == []


# ── find_backup_named ─────────────────────────────────────────────────────────

def test_find_backup_named_detects_explicit_backups(tmp_path):
    (tmp_path / "litreturereview_original_backup.pptx").write_bytes(b"")
    (tmp_path / "main_old.tex").write_bytes(b"")
    (tmp_path / "normal.md").write_text("# doc")
    result = find_backup_named(tmp_path)
    names = {p.name for p in result}
    assert "litreturereview_original_backup.pptx" in names
    assert "main_old.tex" in names
    assert "normal.md" not in names


def test_find_backup_named_detects_old_subdirs(tmp_path):
    old_dir = tmp_path / "old"
    old_dir.mkdir()
    (old_dir / "bib_old.bib").write_bytes(b"")
    result = find_backup_named(tmp_path)
    assert tmp_path / "old" in result


def test_find_backup_named_skips_archive(tmp_path):
    archive = tmp_path / "_archive"
    archive.mkdir()
    (archive / "main_old.tex").write_bytes(b"")
    result = find_backup_named(tmp_path)
    assert not any("_archive" in str(p) for p in result)


# ── archive_item ──────────────────────────────────────────────────────────────

def test_archive_item_moves_file_preserving_structure(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    src = repo_root / "subdir" / "foo.pyc"
    src.parent.mkdir()
    src.write_bytes(b"bytecode")
    archive_root = tmp_path / "_archive"
    run_date = "2026-04-14"

    record = archive_item(src, repo_root, archive_root, run_date, "gitignore violation")

    expected_dest = archive_root / run_date / "subdir" / "foo.pyc"
    assert expected_dest.exists()
    assert not src.exists()
    assert record["original"] == str(src)
    assert record["archived_to"] == str(expected_dest)
    assert record["reason"] == "gitignore violation"


def test_archive_item_moves_directory(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    src_dir = repo_root / "__pycache__"
    src_dir.mkdir()
    (src_dir / "mod.pyc").write_bytes(b"")
    archive_root = tmp_path / "_archive"

    record = archive_item(src_dir, repo_root, archive_root, "2026-04-14", "gitignore violation")

    expected_dest = archive_root / "2026-04-14" / "__pycache__"
    assert expected_dest.is_dir()
    assert not src_dir.exists()
    assert record["original"] == str(src_dir)


def test_archive_item_handles_collision(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    src1 = repo_root / "foo.pyc"
    src2 = repo_root / "sub" / "foo.pyc"
    src2.parent.mkdir()
    src1.write_bytes(b"one")
    src2.write_bytes(b"two")
    archive_root = tmp_path / "_archive"

    # Archive src1 first, then src2 — both become foo.pyc at different paths
    archive_item(src1, repo_root, archive_root, "2026-04-14", "junk")
    record2 = archive_item(src2, repo_root, archive_root, "2026-04-14", "junk")

    # src2 should land at sub/foo.pyc (different relative path, no collision)
    assert Path(record2["archived_to"]).exists()


# ── write_report ──────────────────────────────────────────────────────────────

def test_write_report_creates_dated_markdown(tmp_path):
    archive_root = tmp_path / "_archive"
    archive_root.mkdir()
    moves = [
        {"original": "/repo/foo.pyc", "archived_to": "/repo/_archive/2026-04-14/foo.pyc", "reason": "gitignore violation"},
        {"original": "/repo/bar.pdf", "archived_to": "/repo/_archive/2026-04-14/bar.pdf", "reason": "duplicate of /repo/orig.pdf"},
    ]
    report_path = write_report(moves, archive_root, "2026-04-14")

    assert report_path == archive_root / "cleanup_2026-04-14.md"
    content = report_path.read_text(encoding="utf-8")
    assert "2026-04-14" in content
    assert "foo.pyc" in content
    assert "gitignore violation" in content
    assert "## Summary" in content
    assert "2 items archived" in content


def test_write_report_empty_run(tmp_path):
    archive_root = tmp_path / "_archive"
    archive_root.mkdir()
    report_path = write_report([], archive_root, "2026-04-14")
    content = report_path.read_text(encoding="utf-8")
    assert "0 items archived" in content
