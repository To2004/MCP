"""Shared helpers for the simulator tests: where the simulator lives and how to run it in a
fresh interpreter with a chosen ``PYTHONHASHSEED`` (the hash seed is fixed at start-up, so a
determinism test needs its own process)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_DIR / "reports" / "experiments" / "dynamic_dimensions"
SUBPROCESS_TIMEOUT_S = 300


def ensure_sim_on_path() -> None:
    """Make ``import normal_org_world`` work, appending (never shadowing other modules)."""
    if str(SIM_DIR) not in sys.path:
        sys.path.append(str(SIM_DIR))


def run_python(code: str, hash_seed: str) -> str:
    """Run ``code`` in a new interpreter with ``PYTHONHASHSEED=hash_seed`` and the simulator
    folder importable; return its stripped stdout. Arguments go as a list (no shell)."""
    prelude = f"import sys\nsys.path.insert(0, {str(SIM_DIR)!r})\n"
    env = {**os.environ, "PYTHONHASHSEED": hash_seed}
    result = subprocess.run(
        [sys.executable, "-c", prelude + code],
        env=env,
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        check=True,
        timeout=SUBPROCESS_TIMEOUT_S,
    )
    return result.stdout.strip()
