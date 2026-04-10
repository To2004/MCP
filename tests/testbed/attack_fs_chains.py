"""Filesystem MCP — Attack Chains Campaign.

White-hat research engagement against the official filesystem MCP server,
using only read_file and list_directory. Runs 15 multi-step attack chains
against two versions side-by-side:
  v2025.3.28 — /tmp/fs_328 (pinned, vulnerable)
  v2025.7.29 — /tmp/fs_729 (latest, patched)

Outputs:
  tests/testbed/excel_reports/fs_attack_chains.xlsx
  tests/testbed/excel_reports/fs_attack_chains.raw.jsonl
  tests/testbed/excel_reports/fs_attack_chains.source_notes.md

Safety: all filesystem state lives under /tmp/mcp_attack_{328,729} and
/tmp/victim_{328,729}. Nothing is written outside /tmp. Escape detection
uses a canary string 'ATTACKER_CANARY_12345' — real host secrets are
never the success condition.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FS_328 = "/tmp/fs_328/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js"
FS_729 = "/tmp/fs_729/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js"

SANDBOX_328 = "/tmp/mcp_attack_328"
SANDBOX_729 = "/tmp/mcp_attack_729"
VICTIM_328 = "/tmp/victim_328"
VICTIM_729 = "/tmp/victim_729"

CANARY = "ATTACKER_CANARY_12345"
CANARY_FILE_CONTENT = f"root:x:0:0:canary:/root:/bin/bash\n{CANARY}\n"

REPORTS_DIR = Path(__file__).resolve().parent / "excel_reports"
XLSX_OUT = REPORTS_DIR / "fs_attack_chains.xlsx"
JSONL_OUT = REPORTS_DIR / "fs_attack_chains.raw.jsonl"
NOTES_OUT = REPORTS_DIR / "fs_attack_chains.source_notes.md"

REQUEST_TIMEOUT_SEC = 15
SERVER_INIT_TIMEOUT_SEC = 30
RACE_BUDGET_SEC = 30
MAX_RESPONSE_BYTES = 10 * 1024 * 1024   # 10 MB cap per response
DOS_SIZE_THRESHOLD = 5 * 1024 * 1024    # 5 MB flags as HIGH

SANDBOXES = {"328": SANDBOX_328, "729": SANDBOX_729}
VICTIMS = {"328": VICTIM_328, "729": VICTIM_729}
SERVERS = {"328": FS_328, "729": FS_729}


# ---------------------------------------------------------------------------
# WSL shell helpers — all fixture planting happens inside WSL because the
# servers run there and Windows can't create Unix symlinks / hardlinks / FIFOs.
# ---------------------------------------------------------------------------

def wsl_bash(script: str, check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a bash script inside WSL and return the CompletedProcess."""
    return subprocess.run(
        ["wsl", "bash", "-lc", script],
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
    )


def wsl_python(script: str, check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a python3 one-liner inside WSL. Use for operations that need raw
    bytes in filenames (null byte, non-UTF8) that bash cannot express."""
    return subprocess.run(
        ["wsl", "python3", "-c", script],
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
    )


def wsl_file_exists(path: str) -> bool:
    cp = wsl_bash(f"test -e {path!r} && echo yes || echo no", check=False)
    return cp.stdout.strip() == "yes"


def wsl_read_file(path: str) -> str:
    cp = wsl_bash(f"cat {path!r}", check=False)
    return cp.stdout


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("attack_fs_chains.py — scaffold OK (no phases implemented yet)")


if __name__ == "__main__":
    main()
