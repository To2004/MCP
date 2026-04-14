"""Weekly repo cleanup — archives junk, duplicates, and backup-named files."""
import re
import hashlib
import shutil
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = REPO_ROOT / "_archive"

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


# Matches files with backup/old indicators in the stem.
# Deliberately excludes _v\d+ because this repo uses version numbers
# in active research document names (e.g. mcp_server_attacks_v3.md).
BACKUP_STEM_RE = re.compile(
    r"(_backup|_original_backup|_old)$",
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
        # skip if already moved (junk pass may have moved parent)
        if not item.exists():
            continue
        record = archive_item(item, REPO_ROOT, archive_root, run_date, "backup/old file")
        moves.append(record)
        print(f"  archived: {item}")

    # 3. Duplicates (run after moving junk so hashes reflect actual state)
    dupes = find_duplicates(REPO_ROOT)
    print(f"[cleanup] Found {len(dupes)} duplicate pairs")
    for keep, dup in dupes:
        if not dup.exists():
            continue
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
