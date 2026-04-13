"""
Run the full MCP attack campaign in one command.

Usage:
    python tests/testbed/run_all.py                    # attack mode, all servers
    python tests/testbed/run_all.py --mode eval        # also run scorer
    python tests/testbed/run_all.py --trials 3         # repeat each payload 3x
    python tests/testbed/run_all.py --no-scenarios     # skip multi-step scenarios
    python tests/testbed/run_all.py --no-disable       # keep unreachable server profiles

After the run this script:
  1. Saves all results to tests/testbed/results/campaign_<timestamp>.json
  2. Moves unreachable server profiles to tests/testbed/servers/disabled/
  3. Writes a markdown report to tests/testbed/results/report_<timestamp>.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from tests.testbed.harness.attack_runner import run_server  # noqa: E402
from tests.testbed.harness.scenario_runner import run_server_scenarios  # noqa: E402
from tests.testbed.harness.server_manager import load_profile  # noqa: E402
from tests.testbed.generate_report import generate  # noqa: E402

TESTBED = Path(__file__).parent
SERVERS_DIR = TESTBED / "servers"
DISABLED_DIR = SERVERS_DIR / "disabled"
RESULTS_DIR = TESTBED / "results"
SANDBOX_DIR = TESTBED / "sandbox"


def _clean_sandbox() -> None:
    """Delete all contents of the testbed sandbox, keeping the directory itself."""
    if not SANDBOX_DIR.exists():
        return
    for item in SANDBOX_DIR.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def _server_names() -> list[str]:
    """Return all active server profile stems, sorted."""
    return [p.stem for p in sorted(SERVERS_DIR.glob("*.json"))]


def _requires_api_key(name: str) -> bool:
    """Return True if this server profile requires an external API key."""
    try:
        profile = load_profile(name)
        return bool(profile.get("requires_api_key", False))
    except Exception:
        return False


async def _attack_one(name: str, mode: str, trials: int) -> list[dict[str, Any]]:
    """Run all attack templates against one server. Returns [] on connection failure."""
    try:
        return await run_server(name, mode, trials, template_filter=None)
    except Exception as exc:
        print(f"    [ERROR] {exc!s:.120}")
        return []


async def _scenarios_one(name: str, mode: str) -> list[dict[str, Any]]:
    """Run multi-step scenarios against one server. Returns [] on failure."""
    try:
        return await run_server_scenarios(name, mode)
    except Exception as exc:
        print(f"    [SCENARIO ERROR] {exc!s:.120}")
        return []


def _disable(name: str) -> None:
    """Move a server profile to servers/disabled/ so it is excluded from future runs."""
    DISABLED_DIR.mkdir(exist_ok=True)
    src = SERVERS_DIR / f"{name}.json"
    dst = DISABLED_DIR / f"{name}.json"
    if src.exists():
        shutil.move(str(src), str(dst))


def _asr(results: list[dict[str, Any]]) -> str:
    mal = [r for r in results if r.get("payload_type") == "malicious"]
    dmg = [r for r in mal if r.get("damage_detected")]
    return f"{len(dmg)}/{len(mal)} ({len(dmg)/len(mal)*100:.1f}%)" if mal else "N/A"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run full MCP attack campaign against all server profiles."
    )
    parser.add_argument("--mode", choices=["attack", "eval"], default="attack",
                        help="attack = payloads only; eval = payloads + scorer (default: attack)")
    parser.add_argument("--trials", type=int, default=1,
                        help="Repeat each payload N times (default: 1)")
    parser.add_argument("--no-scenarios", action="store_true",
                        help="Skip multi-step scenario runner")
    parser.add_argument("--no-disable", action="store_true",
                        help="Keep unreachable server profiles (don't move to disabled/)")
    args = parser.parse_args()

    servers = _server_names()
    ts_start = datetime.now(UTC)
    print(f"\n{'='*64}")
    print(f"  MCP ATTACK CAMPAIGN — {ts_start.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Servers: {len(servers)} | Mode: {args.mode} | Trials: {args.trials}")
    print(f"{'='*64}")

    all_results: list[dict[str, Any]] = []
    unreachable: list[str] = []    # failed to connect, not API-key related
    api_key_skip: list[str] = []   # skipped because requires_api_key and no results

    for name in servers:
        needs_key = _requires_api_key(name)
        key_note = " [needs API key]" if needs_key else ""
        print(f"\n>>> {name}{key_note}")

        # Attack templates
        results = asyncio.run(_attack_one(name, args.mode, args.trials))

        if not results:
            if needs_key:
                api_key_skip.append(name)
                print(f"    -> 0 results (API key not set — expected, keeping profile)")
            else:
                unreachable.append(name)
                print(f"    -> 0 results (unreachable — will disable)")
        else:
            print(f"    -> templates: {_asr(results)} damage | {len(results)} total results")
            all_results.extend(results)

            # Multi-step scenarios
            if not args.no_scenarios:
                sc = asyncio.run(_scenarios_one(name, args.mode))
                if sc:
                    sc_dmg = sum(1 for r in sc if r.get("damage_detected"))
                    print(f"    -> scenarios: {sc_dmg}/{len(sc)} damage")
                    all_results.extend(sc)

    # ── Save combined results ────────────────────────────────────────────────
    RESULTS_DIR.mkdir(exist_ok=True)
    ts_file = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    out_json = RESULTS_DIR / f"campaign_{ts_file}.json"
    out_json.write_text(json.dumps(all_results, indent=2), encoding="utf-8")

    # ── Disable unreachable servers ──────────────────────────────────────────
    if unreachable and not args.no_disable:
        for name in unreachable:
            _disable(name)

    # ── Generate markdown report ─────────────────────────────────────────────
    report_path = generate()

    # ── Final summary ────────────────────────────────────────────────────────
    elapsed = (datetime.now(UTC) - ts_start).seconds
    mal_all = [r for r in all_results if r.get("payload_type") == "malicious"]
    dmg_all = [r for r in mal_all if r.get("damage_detected")]
    ben_all = [r for r in all_results if r.get("payload_type") == "benign"]
    servers_reached = len(servers) - len(unreachable) - len(api_key_skip)

    print(f"\n{'='*64}")
    print(f"  CAMPAIGN COMPLETE  ({elapsed}s)")
    print(f"{'='*64}")
    print(f"  Servers reached  : {servers_reached}/{len(servers)}")
    print(f"  API key skipped  : {len(api_key_skip)}")
    if unreachable:
        print(f"  Disabled         : {len(unreachable)} — {', '.join(unreachable)}")
    print(f"  Total results    : {len(all_results)}")
    print(f"  Malicious tested : {len(mal_all)}")
    print(f"  Benign tested    : {len(ben_all)}")
    print(f"  Overall ASR      : {_asr(all_results)}")
    print(f"  Results JSON     : {out_json}")
    print(f"  Report           : {report_path}")
    print(f"{'='*64}\n")

    _clean_sandbox()
    print("  Sandbox cleaned.")


if __name__ == "__main__":
    main()
