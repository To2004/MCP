"""Run MCPSafetyScanner (LLM-based) against testbed servers.

Reads the OpenAI API key from C:\\Users\\user\\Documents\\Keys\\chatgptkey.txt
(never hardcodes or prints the key).

Usage:
    python tests/testbed/run_safety_scanner.py --server filesystem
    python tests/testbed/run_safety_scanner.py --all
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SERVERS_DIR = Path(__file__).parent / "servers"
RESULTS_DIR = Path(__file__).parent / "results"
KEY_FILE = Path(r"C:\Users\user\Documents\Keys\chatgptkey.txt")


def read_api_key() -> str:
    """Read the OpenAI API key from the key file."""
    if not KEY_FILE.exists():
        raise FileNotFoundError(f"OpenAI key file not found: {KEY_FILE}")
    return KEY_FILE.read_text().strip()


def load_profile(name: str) -> dict[str, Any]:
    """Load a server profile by name."""
    path = SERVERS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Server profile not found: {path}")
    return json.loads(path.read_text())


def build_claude_desktop_config(profile: dict[str, Any]) -> dict[str, Any]:
    """Build a claude_desktop_config.json dict for MCPSafetyScanner."""
    cmd = profile.get("start_cmd", [])
    if not cmd:
        return {}
    return {
        "mcpServers": {
            profile["name"]: {
                "command": cmd[0],
                "args": cmd[1:],
            }
        }
    }


def run_scanner(server_name: str, api_key: str) -> Path | None:
    """Run MCPSafetyScanner against one server. Returns path to report or None on failure."""
    profile = load_profile(server_name)

    if profile.get("transport") == "http":
        print(f"[skip] {server_name}: HTTP transport not supported by MCPSafetyScanner")
        return None

    config = build_claude_desktop_config(profile)
    if not config:
        print(f"[skip] {server_name}: could not build config")
        return None

    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    report_path = RESULTS_DIR / f"scanner_{server_name}_{ts}.md"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir=RESULTS_DIR
    ) as f:
        json.dump(config, f)
        config_path = f.name

    env = {**os.environ, "OPENAI_API_KEY": api_key}
    try:
        result = subprocess.run(
            [sys.executable, "-m", "mcpSafetyScanner", "--config", config_path],
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        output = result.stdout + result.stderr
        report_path.write_text(
            f"# MCPSafetyScanner Report: {server_name}\n\n"
            f"_Scanned: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}_\n\n"
            + output
        )
        print(f"[done] {server_name} → {report_path.name}")
        return report_path
    except subprocess.TimeoutExpired:
        print(f"[timeout] {server_name}: scanner timed out after 300s")
        return None
    except FileNotFoundError:
        print("[error] mcpSafetyScanner not installed. Run: pip install mcpSafetyScanner")
        return None
    finally:
        Path(config_path).unlink(missing_ok=True)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run MCPSafetyScanner against testbed servers"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--server", help="Server name")
    group.add_argument("--all", action="store_true", help="Run against all vulnerable servers")
    args = parser.parse_args()

    api_key = read_api_key()

    if args.all:
        servers = []
        for path in sorted(SERVERS_DIR.glob("*.json")):
            profile = json.loads(path.read_text())
            if profile.get("tier") == "vulnerable":
                servers.append(path.stem)
    else:
        servers = [args.server]

    for server in servers:
        print(f"\n=== Scanning {server} ===")
        run_scanner(server, api_key)


if __name__ == "__main__":
    main()
