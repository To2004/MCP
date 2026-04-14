"""Weekly repo cleanup — archives junk, duplicates, and backup-named files."""
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = REPO_ROOT / "_archive"
SKIP_DIRS = {".git", ".venv", "_archive", ".worktrees", "node_modules"}
