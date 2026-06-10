"""Regenerate mcp_tools_atomic_ops.xlsx from the current classifier rules.

Usage (from repo root):
    uv run python presentations/atomic_op_classification/regen_xlsx.py
    uv run python presentations/atomic_op_classification/regen_xlsx.py --live
    uv run python presentations/atomic_op_classification/regen_xlsx.py --server filesystem
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    cmd = [sys.executable, "-m", "mcp_security.atomic_ops.build_heatmap"] + sys.argv[1:]
    return subprocess.run(cmd, cwd=str(ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
