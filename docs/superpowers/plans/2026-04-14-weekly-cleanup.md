# Weekly Repo Cleanup Job Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python cleanup script + Windows Task Scheduler entry that runs every Saturday, archives junk/duplicate/backup files from the repo into `_archive/`, and writes a dated markdown report.

**Architecture:** A single standalone Python script (`scripts/weekly_cleanup.py`) with three responsibilities — find candidates, move them to `_archive/<date>/` preserving structure, and write a report. A one-time PowerShell script (`scripts/install_cleanup_task.ps1`) registers it with Windows Task Scheduler. No new dependencies beyond the stdlib.

**Tech Stack:** Python 3.11+ stdlib only (`pathlib`, `hashlib`, `shutil`, `re`, `datetime`), Windows Task Scheduler via `schtasks.exe` (called from PowerShell).

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `scripts/weekly_cleanup.py` | Create | Main cleanup script — finder + archiver + reporter |
| `scripts/install_cleanup_task.ps1` | Create | One-time Task Scheduler registration |
| `tests/test_weekly_cleanup.py` | Create | Unit tests for all cleanup logic |

**Never touch:** `.git/`, `.venv/`, `_archive/` itself, `.worktrees/`

---

## Archival Categories

The script archives three classes of files/dirs:

| Category | Examples | Label in report |
|----------|----------|----------------|
| **gitignore_match** | `__pycache__/`, `*.pyc`, `.playwright-mcp/`, `testbed_test.db` | `gitignore violation` |
| **duplicate** | Two files with identical SHA-256 | `duplicate of <other path>` |
| **backup_named** | `*_backup*`, `*_original*`, files in `old/` subdirs | `backup/old file` |

---

## Task 1: Project scaffold

**Files:**
- Create: `scripts/__init__.py` (empty, makes scripts importable in tests)
- Create: `tests/test_weekly_cleanup.py` (skeleton only)
- Create: `scripts/weekly_cleanup.py` (skeleton only)

- [ ] **Step 1: Create scripts package marker**

```bash
mkdir -p scripts
touch scripts/__init__.py
```

- [ ] **Step 2: Create skeleton test file**

`tests/test_weekly_cleanup.py`:

```python
"""Tests for the weekly repo cleanup script."""
import pytest
from pathlib import Path
```

- [ ] **Step 3: Create skeleton script**

`scripts/weekly_cleanup.py`:

```python
"""Weekly repo cleanup — archives junk, duplicates, and backup-named files."""
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = REPO_ROOT / "_archive"
SKIP_DIRS = {".git", ".venv", "_archive", ".worktrees", "node_modules", "scripts"}
```

- [ ] **Step 4: Commit scaffold**

```bash
git add scripts/__init__.py scripts/weekly_cleanup.py tests/test_weekly_cleanup.py
git commit -m "chore: scaffold weekly cleanup script and tests"
```

---

## Task 2: Implement and test `find_gitignore_matches`

**Files:**
- Modify: `tests/test_weekly_cleanup.py`
- Modify: `scripts/weekly_cleanup.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_weekly_cleanup.py`:

```python
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.weekly_cleanup import find_gitignore_matches

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
    # __pycache__ itself should be flagged, not its children separately
    assert tmp_path / "__pycache__" in result

def test_find_gitignore_matches_skips_archive(tmp_path):
    archive = tmp_path / "_archive"
    archive.mkdir()
    (archive / "foo.pyc").write_bytes(b"")
    result = find_gitignore_matches(tmp_path)
    assert not any("_archive" in str(p) for p in result)
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
uv run pytest tests/test_weekly_cleanup.py::test_find_gitignore_matches_finds_pyc -v
```

Expected: `ImportError` or `AttributeError` — function does not exist yet.

- [ ] **Step 3: Implement `find_gitignore_matches`**

Add to `scripts/weekly_cleanup.py`:

```python
import re

# Directories to skip entirely (never enter)
SKIP_DIRS = {".git", ".venv", "_archive", ".worktrees", "node_modules"}

# Junk dir names — archive the whole directory
JUNK_DIR_NAMES = {"__pycache__", ".pytest_cache", ".ruff_cache", ".playwright-mcp", ".mypy_cache"}

# Junk file suffixes
JUNK_SUFFIXES = {".pyc", ".pyo", ".tmp", ".potx"}

# Junk file name patterns (regex)
JUNK_NAME_RE = re.compile(r"^(~\$|\.DS_Store|Thumbs\.db)$")

# Junk exact filenames
JUNK_EXACT_NAMES = {"testbed_test.db"}


def find_gitignore_matches(root: Path) -> list[Path]:
    """Return files/dirs that match gitignore-style junk patterns.

    Returns top-level junk dirs (not their children) to avoid double-counting.
    Never descends into SKIP_DIRS or already-flagged dirs.
    """
    results: list[Path] = []

    def _walk(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return
        for entry in entries:
            if entry.name in SKIP_DIRS:
                continue
            if entry.is_dir():
                if entry.name in JUNK_DIR_NAMES:
                    results.append(entry)
                    # do NOT recurse into it
                else:
                    _walk(entry)
            else:
                if (
                    entry.suffix in JUNK_SUFFIXES
                    or JUNK_NAME_RE.match(entry.name)
                    or entry.name in JUNK_EXACT_NAMES
                ):
                    results.append(entry)

    _walk(root)
    return results
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_weekly_cleanup.py -k "gitignore" -v
```

Expected: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
git add scripts/weekly_cleanup.py tests/test_weekly_cleanup.py
git commit -m "feat(cleanup): implement find_gitignore_matches with tests"
```

---

## Task 3: Implement and test `find_duplicates`

**Files:**
- Modify: `tests/test_weekly_cleanup.py`
- Modify: `scripts/weekly_cleanup.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_weekly_cleanup.py`:

```python
from scripts.weekly_cleanup import find_duplicates

def test_find_duplicates_detects_identical_files(tmp_path):
    content = b"same content here"
    (tmp_path / "a.pdf").write_bytes(content)
    (tmp_path / "b.pdf").write_bytes(content)
    (tmp_path / "c.pdf").write_bytes(b"different")
    dupes = find_duplicates(tmp_path)
    # Should return pairs; one of a.pdf or b.pdf appears as duplicate
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
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
uv run pytest tests/test_weekly_cleanup.py::test_find_duplicates_detects_identical_files -v
```

Expected: `ImportError` — function not defined yet.

- [ ] **Step 3: Implement `find_duplicates`**

Add to `scripts/weekly_cleanup.py`:

```python
import hashlib


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(root: Path) -> list[tuple[Path, Path]]:
    """Return (keep, archive) pairs for duplicate files.

    For each group of identical files (by SHA-256), keeps the one
    whose path is shortest (closest to root), archives the rest.
    Never compares files inside SKIP_DIRS or _archive/.
    """
    seen: dict[str, Path] = {}   # hash -> first (keep) path
    duplicates: list[tuple[Path, Path]] = []

    def _walk(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return
        for entry in entries:
            if entry.name in SKIP_DIRS:
                continue
            if entry.is_dir():
                _walk(entry)
            elif entry.is_file():
                try:
                    digest = _sha256(entry)
                except OSError:
                    continue
                if digest in seen:
                    duplicates.append((seen[digest], entry))
                else:
                    seen[digest] = entry

    _walk(root)
    return duplicates
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_weekly_cleanup.py -k "duplicate" -v
```

Expected: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
git add scripts/weekly_cleanup.py tests/test_weekly_cleanup.py
git commit -m "feat(cleanup): implement find_duplicates with SHA-256 dedup"
```

---

## Task 4: Implement and test `find_backup_named`

**Files:**
- Modify: `tests/test_weekly_cleanup.py`
- Modify: `scripts/weekly_cleanup.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_weekly_cleanup.py`:

```python
from scripts.weekly_cleanup import find_backup_named

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
    # The whole old/ dir should be flagged
    assert tmp_path / "old" in result

def test_find_backup_named_skips_archive(tmp_path):
    archive = tmp_path / "_archive"
    archive.mkdir()
    (archive / "main_old.tex").write_bytes(b"")
    result = find_backup_named(tmp_path)
    assert not any("_archive" in str(p) for p in result)
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
uv run pytest tests/test_weekly_cleanup.py::test_find_backup_named_detects_explicit_backups -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `find_backup_named`**

Add to `scripts/weekly_cleanup.py`:

```python
# Matches files with backup/old indicators in the stem
BACKUP_STEM_RE = re.compile(
    r"(_backup|_original|_old|_v\d+)$",
    re.IGNORECASE,
)

# Directory names that signal old/backup content
BACKUP_DIR_NAMES = {"old", "backup", "archive_old"}


def find_backup_named(root: Path) -> list[Path]:
    """Return files/dirs whose names indicate they are backups or old versions.

    Flags entire directories named 'old', 'backup', etc., rather than
    recursing into them.
    """
    results: list[Path] = []

    def _walk(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return
        for entry in entries:
            if entry.name in SKIP_DIRS:
                continue
            if entry.is_dir():
                if entry.name.lower() in BACKUP_DIR_NAMES:
                    results.append(entry)
                    # do NOT recurse
                else:
                    _walk(entry)
            else:
                stem = entry.stem
                if BACKUP_STEM_RE.search(stem):
                    results.append(entry)

    _walk(root)
    return results
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_weekly_cleanup.py -k "backup_named" -v
```

Expected: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
git add scripts/weekly_cleanup.py tests/test_weekly_cleanup.py
git commit -m "feat(cleanup): implement find_backup_named with tests"
```

---

## Task 5: Implement and test `archive_item`

**Files:**
- Modify: `tests/test_weekly_cleanup.py`
- Modify: `scripts/weekly_cleanup.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_weekly_cleanup.py`:

```python
from scripts.weekly_cleanup import archive_item

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
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
uv run pytest tests/test_weekly_cleanup.py::test_archive_item_moves_file_preserving_structure -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `archive_item`**

Add to `scripts/weekly_cleanup.py`:

```python
import shutil


def archive_item(
    src: Path,
    repo_root: Path,
    archive_root: Path,
    run_date: str,
    reason: str,
) -> dict:
    """Move src into archive_root/run_date/, preserving path relative to repo_root.

    Returns a dict with original, archived_to, and reason keys.
    """
    rel = src.relative_to(repo_root)
    dest = archive_root / run_date / rel
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        # Avoid collision: append a counter suffix
        counter = 1
        while dest.exists():
            dest = dest.with_name(f"{dest.stem}_{counter}{dest.suffix}")
            counter += 1

    shutil.move(str(src), str(dest))
    return {"original": str(src), "archived_to": str(dest), "reason": reason}
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_weekly_cleanup.py -k "archive_item" -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add scripts/weekly_cleanup.py tests/test_weekly_cleanup.py
git commit -m "feat(cleanup): implement archive_item with structure preservation"
```

---

## Task 6: Implement and test `write_report`

**Files:**
- Modify: `tests/test_weekly_cleanup.py`
- Modify: `scripts/weekly_cleanup.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_weekly_cleanup.py`:

```python
from scripts.weekly_cleanup import write_report

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
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
uv run pytest tests/test_weekly_cleanup.py::test_write_report_creates_dated_markdown -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `write_report`**

Add to `scripts/weekly_cleanup.py`:

```python
def write_report(moves: list[dict], archive_root: Path, run_date: str) -> Path:
    """Write a markdown report of the cleanup run to archive_root/cleanup_<date>.md.

    Returns the path to the written report file.
    """
    report_path = archive_root / f"cleanup_{run_date}.md"
    lines: list[str] = [
        f"# Cleanup Report — {run_date}",
        "",
        "## Summary",
        "",
        f"**{len(moves)} items archived** on {run_date}.",
        "",
    ]

    if moves:
        lines += [
            "## Archived Items",
            "",
            "| # | Original Path | Archived To | Reason |",
            "|---|--------------|-------------|--------|",
        ]
        for i, m in enumerate(moves, 1):
            lines.append(f"| {i} | `{m['original']}` | `{m['archived_to']}` | {m['reason']} |")
        lines.append("")
    else:
        lines += ["Nothing was archived this run.", ""]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_weekly_cleanup.py -k "write_report" -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add scripts/weekly_cleanup.py tests/test_weekly_cleanup.py
git commit -m "feat(cleanup): implement write_report with markdown table output"
```

---

## Task 7: Wire up the `main()` entry point

**Files:**
- Modify: `scripts/weekly_cleanup.py`

- [ ] **Step 1: Add `main()` to the script**

Add at the bottom of `scripts/weekly_cleanup.py`:

```python
def main() -> None:
    """Run the full cleanup pipeline."""
    run_date = date.today().isoformat()
    archive_root = ARCHIVE_ROOT
    archive_root.mkdir(exist_ok=True)

    print(f"[cleanup] Starting run for {run_date}")
    print(f"[cleanup] Repo root: {REPO_ROOT}")

    moves: list[dict] = []

    # 1. Gitignore-matching junk
    junk = find_gitignore_matches(REPO_ROOT)
    print(f"[cleanup] Found {len(junk)} gitignore matches")
    for item in junk:
        record = archive_item(item, REPO_ROOT, archive_root, run_date, "gitignore violation")
        moves.append(record)
        print(f"  archived: {item}")

    # 2. Backup-named files and dirs
    backups = find_backup_named(REPO_ROOT)
    print(f"[cleanup] Found {len(backups)} backup-named items")
    for item in backups:
        record = archive_item(item, REPO_ROOT, archive_root, run_date, "backup/old file")
        moves.append(record)
        print(f"  archived: {item}")

    # 3. Duplicates (run after moving junk so hashes reflect actual state)
    dupes = find_duplicates(REPO_ROOT)
    print(f"[cleanup] Found {len(dupes)} duplicate pairs")
    for keep, dup in dupes:
        reason = f"duplicate of {keep.relative_to(REPO_ROOT)}"
        record = archive_item(dup, REPO_ROOT, archive_root, run_date, reason)
        moves.append(record)
        print(f"  archived duplicate: {dup}  (keeping {keep})")

    # 4. Write report
    report_path = write_report(moves, archive_root, run_date)
    print(f"[cleanup] Report written to {report_path}")
    print(f"[cleanup] Done — {len(moves)} items archived.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full test suite to verify nothing broke**

```bash
uv run pytest tests/test_weekly_cleanup.py -v
```

Expected: All tests PASS.

- [ ] **Step 3: Do a manual dry-run (print only, no archive)**

Temporarily call each finder and print counts without calling `archive_item`:

```bash
uv run python -c "
from pathlib import Path
import sys; sys.path.insert(0, '.')
from scripts.weekly_cleanup import REPO_ROOT, find_gitignore_matches, find_backup_named, find_duplicates
print('Junk:', len(find_gitignore_matches(REPO_ROOT)))
print('Backup-named:', len(find_backup_named(REPO_ROOT)))
print('Duplicates:', len(find_duplicates(REPO_ROOT)))
"
```

Review the output. If any counts look unexpectedly high (>50), investigate before proceeding.

- [ ] **Step 4: Commit**

```bash
git add scripts/weekly_cleanup.py
git commit -m "feat(cleanup): add main() entry point wiring all finders together"
```

---

## Task 8: Create the Windows Task Scheduler installer

**Files:**
- Create: `scripts/install_cleanup_task.ps1`

- [ ] **Step 1: Write the PowerShell installer**

`scripts/install_cleanup_task.ps1`:

```powershell
# install_cleanup_task.ps1
# Run once (as the current user) to register the weekly Saturday cleanup job.
# No admin rights required — the task runs as the current user.

$ErrorActionPreference = "Stop"

$repoRoot  = Split-Path -Parent $PSScriptRoot
$python    = Join-Path $repoRoot ".venv\Scripts\python.exe"
$script    = Join-Path $repoRoot "scripts\weekly_cleanup.py"
$taskName  = "MCP_WeeklyCleanup"
$logFile   = Join-Path $repoRoot "_archive\task_scheduler.log"

# Validate python exists
if (-not (Test-Path $python)) {
    Write-Error "Python not found at $python. Run 'uv sync' first."
    exit 1
}

# Build the action
$action = New-ScheduledTaskAction `
    -Execute $python `
    -Argument $script `
    -WorkingDirectory $repoRoot

# Build the trigger: every Saturday at 09:00
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday -At "09:00"

# Settings: run even on battery, don't stop if on battery
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries

# Register (or update if already exists)
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Limited `
    -Force | Out-Null

Write-Host "Task '$taskName' registered successfully."
Write-Host "It will run every Saturday at 09:00."
Write-Host "To run it immediately: Start-ScheduledTask -TaskName '$taskName'"
Write-Host "To remove it:          Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
```

- [ ] **Step 2: Run the installer**

In a PowerShell terminal (not bash):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
.\scripts\install_cleanup_task.ps1
```

Expected output:
```
Task 'MCP_WeeklyCleanup' registered successfully.
It will run every Saturday at 09:00.
```

- [ ] **Step 3: Verify the task is registered**

```powershell
Get-ScheduledTask -TaskName "MCP_WeeklyCleanup" | Select-Object TaskName, State
```

Expected: `TaskName: MCP_WeeklyCleanup, State: Ready`

- [ ] **Step 4: Commit**

```bash
git add scripts/install_cleanup_task.ps1
git commit -m "feat(cleanup): add PowerShell Task Scheduler installer for Saturday runs"
```

---

## Task 9: Run cleanup once and verify

**Files:** No code changes — just validation.

- [ ] **Step 1: Run the script manually**

```bash
uv run python scripts/weekly_cleanup.py
```

Review the console output. Check that moved files make sense.

- [ ] **Step 2: Verify the archive folder was created**

```bash
ls _archive/
```

Expected: A dated folder (e.g., `2026-04-14/`) and `cleanup_2026-04-14.md`.

- [ ] **Step 3: Review the report**

```bash
cat "_archive/cleanup_$(date +%Y-%m-%d).md"
```

Confirm the table looks correct and every moved item is listed.

- [ ] **Step 4: Run the full test suite one final time**

```bash
uv run pytest tests/test_weekly_cleanup.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Final commit**

```bash
git add _archive/
git commit -m "chore: first cleanup run — archive report included"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Covered by |
|-------------|-----------|
| Recurse all subfolders | `_walk()` in all three finders |
| Archive duplicates | Task 3 (`find_duplicates`) |
| Archive temp/gitignore junk | Task 2 (`find_gitignore_matches`) |
| Archive backup-named files | Task 4 (`find_backup_named`) |
| Move, never delete | `shutil.move()` in Task 5 |
| Preserve folder structure in archive | `rel = src.relative_to(repo_root)` in Task 5 |
| Dated markdown report in `_archive/` | Task 6 (`write_report`) |
| Touch committed files too | Yes — no git-status filtering |
| Never touch `_archive/` itself | `SKIP_DIRS` includes `_archive` |
| Run every Saturday | Task 8 (Task Scheduler trigger) |
| Saturday at a sensible time | 09:00 AM |

**Placeholder scan:** None found. All steps include actual code.

**Type consistency:** `archive_item` returns `dict` throughout. `find_*` functions all return `list[Path]`. `write_report` takes `list[dict]` — consistent with `archive_item` output.
