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


# ---------------------------------------------------------------------------
# Fixture builder — wipe and rebuild per-version sandbox state.
# ---------------------------------------------------------------------------

def wipe_and_recreate(version: str) -> None:
    """Reset sandbox + victim dir for one version to a clean baseline."""
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    script = f"""
        set -e
        rm -rf {sandbox!r} {victim!r} {sandbox}_evil {sandbox}_indirect
        mkdir -p {sandbox!r} {victim!r}
        printf '%s' {CANARY_FILE_CONTENT!r} > {victim!r}/passwd_canary
        echo 'hello from the sandbox' > {sandbox!r}/readme.txt
        mkdir -p {sandbox!r}/subdir
        echo 'nested file' > {sandbox!r}/subdir/nested.txt
    """
    wsl_bash(script)


def wipe_all() -> None:
    for v in SANDBOXES:
        wipe_and_recreate(v)


# ---------------------------------------------------------------------------
# Pure helpers — text cleaning, truncation, and hit classification.
# ---------------------------------------------------------------------------

_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ABS_PATH_RE = re.compile(r"(?:/[a-zA-Z0-9_.+-]+){2,}")
_SECRET_MARKERS = ("AWS_SECRET", "API_KEY", "PASSWORD=", "SECRET_KEY")


def clean_text(text: str) -> str:
    return _CTRL_RE.sub(lambda m: f"<0x{ord(m.group()):02x}>", text)


def truncate(text: str, limit: int = 600) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[...{len(text)} chars total]"


def _is_regression(pinned: str, latest: str) -> bool:
    """True if the two versions behaved meaningfully differently."""
    def is_block(text: str) -> bool:
        low = text.lower()
        return any(k in low for k in (
            "access denied", "outside allowed", "not allowed",
            "forbidden", "error:", "tool error",
        ))

    p_blocked = is_block(pinned)
    l_blocked = is_block(latest)
    if p_blocked != l_blocked:
        return True
    if not p_blocked and not l_blocked:
        p2 = re.sub(r"\s+", " ", pinned.strip().lower())
        l2 = re.sub(r"\s+", " ", latest.strip().lower())
        return p2 != l2
    return False


def classify_hit(
    input_path: Any,
    pinned: str,
    latest: str,
    pinned_elapsed_ms: int,
    latest_elapsed_ms: int,
) -> tuple[str, str, bool]:
    """Return (severity, reason, is_regression)."""
    regression = _is_regression(pinned, latest)
    combined = f"{pinned}\n{latest}"

    # CRITICAL — leaks dominate
    if CANARY in combined:
        return "CRITICAL", f"canary string '{CANARY}' leaked — real sandbox escape", regression
    if re.search(r"\broot:x:", combined):
        return "CRITICAL", "/etc/passwd marker 'root:x:' in response", regression
    if "BEGIN OPENSSH" in combined or "BEGIN RSA" in combined or "ssh-rsa " in combined:
        return "CRITICAL", "SSH key material in response", regression
    if any(m in combined for m in _SECRET_MARKERS):
        return "CRITICAL", "credential marker in response", regression

    # HIGH — crashes, timeouts, oversized
    if pinned_elapsed_ms >= REQUEST_TIMEOUT_SEC * 1000 or latest_elapsed_ms >= REQUEST_TIMEOUT_SEC * 1000:
        return "HIGH", "request timeout / hang (>= 15s)", regression
    if len(pinned) >= DOS_SIZE_THRESHOLD or len(latest) >= DOS_SIZE_THRESHOLD:
        mb = max(len(pinned), len(latest)) / (1024 * 1024)
        return "HIGH", f"oversized response ({mb:.1f} MB) — DoS candidate", regression
    if "Traceback" in combined or "UnhandledPromiseRejection" in combined or "\n    at Object." in combined:
        return "HIGH", "stack trace in response (unhandled error)", regression

    # MEDIUM — info leak
    input_str = str(input_path) if input_path is not None else ""
    for match in _ABS_PATH_RE.findall(combined):
        if not match or match in input_str:
            continue
        if "node_modules" in match:
            return "MEDIUM", f"internal path leaked: {match[:80]}", regression
        if match.startswith(("/home/", "/root/", "/Users/")):
            return "MEDIUM", f"host path leaked: {match[:80]}", regression

    if regression:
        return "LOW", "behavioral divergence between versions", True

    return "INFO", "no hit", False


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("attack_fs_chains.py — scaffold OK (no phases implemented yet)")


if __name__ == "__main__":
    main()
